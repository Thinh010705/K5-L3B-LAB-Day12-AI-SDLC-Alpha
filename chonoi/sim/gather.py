"""Buổi sáng — Lặn & Hái (`gather`). KHUNG: bơi, chặn mép, đồng hồ, cập bến, xuất kho.

Mặt cắt dòng sông nhìn NGANG: vị trí `[x, d]` (x sang phải, `d` độ sâu hướng xuống, d = 0 là mặt nước).
`move = [x, d]`: thành phần thứ hai DƯƠNG = bơi xuống. Hướng mặt là góc từ +x, dương = xuống.

Đã làm sẵn để smoke test chạy được: bơi + tăng/giảm tốc, chặn mép (d không âm), đồng hồ và hết giờ,
cập bến (`interact` trong vùng bến -> `gather_end` reason `docked`), xuất kho, snapshot đầy đủ trường gather.

Nhóm viết tiếp (đúng thứ tự một bước trong PRD mục 13.8, "Gather"):
  TODO(nhóm, lát 1): bơi + oxy + biên + giỏ
      - oxy: dưới nước (d > surface_depth) trừ 1 tick/tick, mặt nước hồi oxygen_refill_per_tick, kẹp [0, max]
      - ngạt: oxy = 0 và đang dưới nước -> đếm zero_oxy_ticks, đủ choke_interval_ticks thì -1 Máu (choke)
      - Máu về 0 -> ngất (faint, gather_end reason `fainted`, mất toàn bộ giỏ, kho rỗng)
      - sự kiện dive / surface / oxygen_empty / choke / faint
      - giỏ: thứ tự nhặt (LIFO), sức chứa hold_capacity
  TODO(nhóm, lát 2): hái + bắt cá + cập bến + kho
      - hái nút ở mặt nước (gather, hold_full), nút mọc lại (node_regrown đã có phần đếm ngược)
      - bắt đàn cá bằng `catch` (fish_caught, hold_full, hồi chiêu catch_cd_ticks, chỉ khi dưới nước)
      - cập bến xét TRƯỚC hái (đã có); ghi kho đúng một lần do runner lo
Các tính năng của phase sau chưa nằm trong khung này.
"""

import math

from ..errors import BadInput
from ..freshness import Freshness
from ..ids import sort_by_id
from ..inventory import hold_to_items
from .ramp import ramp_velocity

TICK = 60.0
AXES = ("x", "d")


class GatherSim:
    mode = "gather"
    phase = "gather"

    def __init__(self, tuning, scenario, streams, ids, *, day=1, active_upgrades=None):
        from ..scenario import _validate_gather, validate_monsters

        _validate_gather(scenario, tuning, active_upgrades=active_upgrades)
        t = tuning["gather"]
        self.t = t
        self.contract_version = tuning.get("_contract_version", "1.0")
        self.freshness = Freshness(tuning["freshness"], tuning["tick_hz"]) if self.contract_version == "1.2" else None
        self.rng = streams
        self.ids = ids
        if isinstance(day, bool) or not isinstance(day, int) or not 1 <= day <= 5:
            raise BadInput("Gather day phải trong [1,5]")
        self.day = day
        self.oxygen_max, self.hp_max = player_limits(tuning, active_upgrades)
        self.phase_tick = 0
        self.moving_fish = "fish_speed" in t and scenario.get("random_fish", True)
        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        self.heading = float(p.get("heading_deg", t["start_heading_deg"]))
        self.oxygen_ticks = p.get("oxygen_ticks", self.oxygen_max)
        self.hp = p.get("hp", self.hp_max)
        if not 0 <= self.oxygen_ticks <= self.oxygen_max or not 1 <= self.hp <= self.hp_max:
            raise BadInput("Oxy/Máu fixture vượt mức đang có hiệu lực")
        self.zero_oxy_ticks = p.get("zero_oxy_ticks", 0)
        self.invuln_ticks = p.get("invuln_ticks", 0)
        self.catch_cd_ticks = p.get("catch_cd_ticks", 0)
        self.hold = list(scenario.get("hold", []))  # thứ tự nhặt, cuối mảng là mới nhất
        if self.freshness is not None:
            self.hold = [dict(item) for item in self.hold]
            for item in self.hold:
                ids.reserve(item["id"])
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * TICK)))
        # nút và đàn cá: scenario THAY THẾ danh sách mặc định; random_fish=false tắt cá mặc định
        src_nodes = scenario["nodes"] if "nodes" in scenario else t["nodes"]
        self.nodes = [{"id": n["id"], "kind": n["kind"], "pos": [float(c) for c in n["pos"]],
                       "regrow_ticks": n.get("regrow_ticks", 0)} for n in src_nodes]
        if "fish" in scenario:
            src_fish = scenario["fish"]
        elif scenario.get("random_fish", True):
            src_fish = [] if isinstance(t["fish_initial"], int) else t["fish_initial"]
        else:
            src_fish = []
        # P1: cá đứng yên. P2: cá bơi/sinh khi có fish_speed và random_fish=true.
        self.fish = [{"id": f["id"], "kind": f["kind"], "pos": [float(c) for c in f["pos"]],
                      "heading_deg": f.get("heading_deg", 0)} for f in src_fish]
        for fish, source in zip(self.fish, src_fish):
            fish["age_ticks"] = source.get("age_ticks", 0)
        for coll in (self.nodes, self.fish):
            for e in coll:
                ids.reserve(e["id"])
        if "fish" not in scenario and self.moving_fish and isinstance(t["fish_initial"], int):
            for _ in range(t["fish_initial"]):
                self._spawn_fish(initial=True)
        config = t.get("monsters", {})
        sources = scenario.get("monsters", [m for m in config.get("spawns", []) if m["from_day"] <= day])
        validate_monsters(sources, t, spawns="monsters" not in scenario)
        self.monsters = [{"id": m["id"], "kind": m["kind"], "pos": list(m["pos"]),
                          "waypoints": [list(w) for w in m["waypoints"]],
                          "target_idx": m.get("target_idx", 1), "state": m.get("state", "patrol"),
                          "state_ticks_left": m.get("state_ticks_left", 0),
                          "recoil_dir": list(m["recoil_dir"]) if m.get("recoil_dir") is not None else None}
                         for m in sources]
        for monster in self.monsters:
            ids.reserve(monster["id"])
        self.money = 0
        self.earned = 0
        self.reputation = tuning["quan"]["reputation_initial"]
        self.done = False
        self.reason = None

    # --- giao diện cho runner -------------------------------------------------
    def inventory_items(self):
        return hold_to_items(self.hold, contract_version=self.contract_version)

    def snapshot(self) -> dict:
        return {
            "player": {"pos": self.pos, "vel": self.vel, "heading_deg": self.heading,
                       "oxygen_ticks": self.oxygen_ticks, "oxygen_max_ticks": self.oxygen_max,
                       "hp": self.hp, "hp_max": self.hp_max, "zero_oxy_ticks": self.zero_oxy_ticks,
                       "invuln_ticks": self.invuln_ticks, "catch_cd_ticks": self.catch_cd_ticks,
                       "at_surface": self._at_surface()},
            "hold": self.hold, "hold_count": len(self.hold),
            "monsters": [{**m, "pos": list(m["pos"]),
                          "waypoints": [list(w) for w in m["waypoints"]],
                          "recoil_dir": list(m["recoil_dir"]) if m["recoil_dir"] is not None else None}
                         for m in sort_by_id(self.monsters)],
            "hold_capacity": self.t["hold_capacity"],
            "nodes": [{"id": n["id"], "pos": n["pos"], "kind": n["kind"],
                       "ready": n["regrow_ticks"] == 0, "regrow_ticks": n["regrow_ticks"]}
                      for n in sort_by_id(self.nodes)],
            "fish": [{"id": f["id"], "pos": f["pos"], "kind": f["kind"], "heading_deg": f["heading_deg"],
                      **({"age_ticks": f["age_ticks"]} if "fish_speed" in self.t else {})}
                     for f in sort_by_id(self.fish)],
        }

    # --- một bước ---------------------------------------------------------------
    def step(self, inp):
        events = []
        if self.done:
            return events
        self.phase_tick += 1
        # 1. đồng hồ và hàng có sẵn: giảm bộ đếm, nút mọc lại
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.invuln_ticks = max(0, self.invuln_ticks - 1)
        self.catch_cd_ticks = max(0, self.catch_cd_ticks - 1)
        for n in sort_by_id(self.nodes):
            if n["regrow_ticks"] > 0:
                n["regrow_ticks"] -= 1
                if n["regrow_ticks"] == 0:
                    events.append(("node_regrown", {"node_id": n["id"]}))
        # Chỉ hàng có sẵn đầu bước hao tươi; hàng vừa nhặt chờ bước kế.
        if self.freshness is not None:
            events.extend(self.freshness.decay_hold(self.hold))
        # 2. bơi + chặn mép
        was_at_surface = self._at_surface()
        self._move(inp)
        # TODO(nhóm, lát 1): so phân vùng đầu/cuối bước -> dive / surface (data: pos).
        at_surface = self._at_surface()
        if was_at_surface != at_surface:
            name = "surface" if at_surface else "dive"
            events.append((name, {"pos": list(self.pos)}))
        # TODO(nhóm, lát 1): oxy theo d CUỐI bước (mặt nước hồi, dưới nước trừ), oxygen_empty khi từ dương
        #   xuống 0, đếm ngạt, choke (-1 Máu). Máu 0 -> faint + gather_end("fainted") với giỏ rỗng, return.
        if at_surface:
            self.oxygen_ticks = min(self.oxygen_max,
                                    self.oxygen_ticks + self.t["oxygen_refill_per_tick"])
            self.zero_oxy_ticks = 0
        else:
            previous_oxygen = self.oxygen_ticks
            self.oxygen_ticks = max(0, self.oxygen_ticks - 1)
            if previous_oxygen > 0 and self.oxygen_ticks == 0:
                events.append(("oxygen_empty", {"oxygen_ticks": 0}))
            if self.oxygen_ticks == 0:
                self.zero_oxy_ticks += 1
                if self.zero_oxy_ticks >= self.t["choke_interval_ticks"]:
                    self.zero_oxy_ticks = 0
                    self.hp -= 1
                    events.append(("choke", {"hp": self.hp}))
                    if self.hp == 0:
                        lost = self._drop_hold(len(self.hold))
                        events.append(("faint", {"cause": "choke", "lost": lost, "hp": 0}))
                        self._finish("fainted", events)
                        return events
            else:
                self.zero_oxy_ticks = 0
        # Quái di chuyển sau oxy/ngạt và trước tương tác, bắt cá.
        self._step_monsters(events)
        if self.done:
            return events
        # 3. interact: bến trước, rồi hái
        if inp.pressed("interact"):
            if self._in_dock():
                self._finish("docked", events)
                return events
            # TODO(nhóm, lát 2): chỉ khi ở mặt nước: hái nút `ready` gần nhất trong interact_radius
            #   (id nhỏ khi bằng nhau): gather / hold_full; đặt regrow_ticks cho nút.
            if at_surface:
                ready_nodes = [n for n in self.nodes if n["regrow_ticks"] == 0]
                node = self._nearest(ready_nodes, self.t["interact_radius"])
                if node is not None:
                    amount = self.t["node_yield"]
                    free = self.t["hold_capacity"] - len(self.hold)
                    if free < amount:
                        events.append(("hold_full", {"action": "gather", "node_id": node["id"],
                                                     "required": amount, "free": free}))
                    else:
                        self._add_hold(node["kind"], amount)
                        node["regrow_ticks"] = int(round(self.t["regrow_s"] * TICK))
                        events.append(("gather", {"node_id": node["id"], "kind": node["kind"],
                                                 "amount": amount}))
        # 4. bắt cá
        if inp.pressed("catch"):
            pass  # TODO(nhóm, lát 2): chỉ khi catch_cd_ticks == 0 và dưới nước: fish_caught / hold_full.
            if self.catch_cd_ticks == 0 and not at_surface:
                fish = self._nearest(self.fish, self.t["catch_radius"])
                if fish is not None:
                    amount = self.t["fish_yield"][fish["kind"]]
                    free = self.t["hold_capacity"] - len(self.hold)
                    if free < amount:
                        events.append(("hold_full", {"action": "catch", "fish_id": fish["id"],
                                                     "required": amount, "free": free}))
                    else:
                        self._add_hold(fish["kind"], amount)
                        self.fish.remove(fish)
                        self.catch_cd_ticks = int(round(self.t["catch_cooldown_s"] * TICK))
                        events.append(("fish_caught", {"fish_id": fish["id"], "kind": fish["kind"],
                                                      "yield": amount}))
        # 5. hết giờ
        if self.time_left_ticks <= 0:
            self._finish("time", events)
        if not self.done and self.moving_fish:
            self._move_fish()
            if self.phase_tick % self.t["fish_spawn_ticks"] == 0:
                fish = self._spawn_fish()
                if fish is not None:
                    events.append(("fish_spawned", {"id": fish["id"], "kind": fish["kind"],
                                                    "pos": list(fish["pos"])}))
        return events

    # --- tiện ích ---------------------------------------------------------------
    def _add_hold(self, kind, amount):
        if self.freshness is None:
            self.hold.extend([kind] * amount)
        else:
            for _ in range(amount):
                self.hold.append({"id": self.ids.new("I"), "kind": kind,
                                  "fresh": self.freshness.config["initial"]})

    def _drop_hold(self, count):
        lost = [self.hold.pop() for _ in range(count)]
        if self.freshness is not None:
            self.freshness.forget(lost)
        return lost

    def _step_monsters(self, events):
        candidates = []
        config = self.t.get("monsters", {})
        for monster in sort_by_id(self.monsters):
            species = config["species"][monster["kind"]]
            if monster["state"] == "recoil":
                # Toàn bộ bước cuối recoil cũng không phát hiện hay gây hit.
                distance = species["recoil_dist"] / TICK
                for axis in range(2):
                    monster["pos"][axis] += monster["recoil_dir"][axis] * distance
                self._clamp_monster(monster, species)
                monster["state_ticks_left"] -= 1
                if monster["state_ticks_left"] == 0:
                    monster["state"] = "patrol"
                    monster["recoil_dir"] = None
                continue
            distance = math.dist(self.pos, monster["pos"])
            player_in_depth = self.pos[1] >= species["depths"][0]
            if monster["state"] == "chase":
                if not player_in_depth or distance > species["exit_radius"]:
                    monster["state"] = "patrol"
            elif player_in_depth and distance <= species["detect_radius"]:
                monster["state"] = "chase"
            if monster["state"] == "chase":
                target, speed = self.pos, species["chase_speed"]
            else:
                target = monster["waypoints"][monster["target_idx"]]
                speed = species["patrol_speed"]
            remaining = math.dist(monster["pos"], target)
            if remaining <= speed / TICK:
                monster["pos"] = list(target)
                if monster["state"] == "patrol":
                    monster["target_idx"] = 1 - monster["target_idx"]
            elif remaining > 0:
                monster["pos"] = [p + (goal - p) * speed / TICK / remaining
                                  for p, goal in zip(monster["pos"], target)]
            self._clamp_monster(monster, species)
            if player_in_depth and math.dist(self.pos, monster["pos"]) <= species["hit_radius"]:
                candidates.append(monster)
        if self.invuln_ticks or not candidates:
            return
        monster = min(candidates, key=lambda m: math.dist(self.pos, m["pos"]))
        species = config["species"][monster["kind"]]
        lost = self._drop_hold(math.floor(len(self.hold) * config["loss_ratio"]))
        self.hp -= 1
        self.invuln_ticks = config["invuln_ticks"]
        events.append(("monster_hit", {"monster_id": monster["id"], "hp": self.hp,
                                        "lost": lost, "pos": list(self.pos)}))
        direction = [m - p for m, p in zip(monster["pos"], self.pos)]
        length = math.hypot(*direction)
        monster["recoil_dir"] = [c / length for c in direction] if length else [1.0, 0.0]
        monster["state"] = "recoil"
        monster["state_ticks_left"] = species["recoil_ticks"]
        if self.hp == 0:
            lost = self._drop_hold(len(self.hold))
            events.append(("faint", {"cause": "monster", "lost": lost, "hp": 0}))
            self._finish("fainted", events)

    def _clamp_monster(self, monster, species):
        for axis, (lo, hi) in enumerate((self.t["bounds"]["x"], species["depths"])):
            monster["pos"][axis] = max(lo, min(hi, monster["pos"][axis]))

    def _spawn_fish(self, initial=False):
        if len(self.fish) >= self.t["fish_max"]:
            return None
        candidates = {}
        for kind in sorted(self.t["fish_weights"]):
            points = []
            for x in self.t["fish_spawn_x"]:
                for depth in self.t["fish_spawn_depths"][kind]:
                    pos = [x, depth]
                    if all((pos != fish["pos"] if initial else
                            math.dist(pos, fish["pos"]) > self.t["fish_spawn_clearance"])
                           for fish in self.fish):
                        points.append(pos)
            if points:
                candidates[kind] = points
        if not candidates:
            return None
        rng = self.rng.get("fish_spawn")
        kinds = list(candidates)
        kind = rng.choices(kinds, weights=[self.t["fish_weights"][k] for k in kinds])[0]
        fish = {"id": self.ids.new("F"), "kind": kind,
                "pos": list(rng.choice(candidates[kind])),
                "heading_deg": self.rng.get("fish_heading").uniform(0.0, 360.0), "age_ticks": 0}
        self.fish.append(fish)
        return fish

    def _move_fish(self):
        for fish in sort_by_id(self.fish):
            fish["age_ticks"] += 1
            if fish["age_ticks"] % self.t["fish_turn_ticks"] == 0:
                fish["heading_deg"] = self.rng.get("fish_heading").uniform(0.0, 360.0)
            angle = math.radians(fish["heading_deg"])
            direction = [math.cos(angle), math.sin(angle)]
            bounds = [self.t["fish_x"], self.t["fish_depths"][fish["kind"]]]
            for axis, (lo, hi) in enumerate(bounds):
                pos = fish["pos"][axis] + direction[axis] * self.t["fish_speed"] / TICK
                # Phản xạ cả quãng đường thừa; chạm đúng mép cũng quay hướng.
                while pos < lo or pos > hi:
                    if pos < lo:
                        pos = 2 * lo - pos
                    else:
                        pos = 2 * hi - pos
                    direction[axis] *= -1
                if (pos == lo and direction[axis] < 0) or (pos == hi and direction[axis] > 0):
                    direction[axis] *= -1
                fish["pos"][axis] = pos
            fish["heading_deg"] = math.degrees(math.atan2(direction[1], direction[0])) % 360

    def _nearest(self, entities, radius):
        nearest = None
        best_distance = math.inf
        for entity in sort_by_id(entities):
            distance = math.dist(self.pos, entity["pos"])
            if distance <= radius and distance < best_distance:
                nearest = entity
                best_distance = distance
        return nearest

    def _at_surface(self) -> bool:
        return self.pos[1] <= self.t["surface_depth"]

    def _in_dock(self) -> bool:
        return math.dist(self.pos, self.t["dock_pos"]) <= self.t["dock_radius"]

    def _finish(self, reason, events):
        self.done = True
        self.reason = reason
        events.append(("gather_end", {"reason": reason, "inventory": {"items": self.inventory_items()}}))

    def _move(self, inp):
        speed = self.t["swim_speed"]
        mx, md = inp.move
        self.vel = ramp_velocity(self, (mx * speed, md * speed), int(self.t["ramp_max_ticks"]))
        if (mx, md) != (0.0, 0.0):
            self.heading = math.degrees(math.atan2(md, mx)) % 360
        b = self.t["bounds"]
        for i, axis in enumerate(AXES):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i] = lo
                self.vel[i] = max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i] = hi
                self.vel[i] = min(0.0, self.vel[i])


def player_limits(tuning, active_upgrades=None):
    """Day truyền cấp ĐANG ÁP DỤNG; mua trong Shop không sửa sim đang chạy."""
    levels = {} if active_upgrades is None else active_upgrades
    if not isinstance(levels, dict):
        raise BadInput("active_upgrades phải là object")
    oxygen_s, hp = tuning["gather"]["oxygen_max_s"], tuning["gather"]["hp_max"]
    for kind in ("oxygen", "hp"):
        level = levels.get(kind, 0)
        if isinstance(level, bool) or not isinstance(level, int) or level < 0:
            raise BadInput(f"active_upgrades.{kind} phải là cấp nguyên không âm")
        if not level:
            continue
        choices = tuning.get("shop", {}).get("upgrades", {}).get(kind, [])
        upgrade = next((row for row in choices if row["level"] == level), None)
        if upgrade is None:
            raise BadInput(f"active_upgrades.{kind}: cấp không tồn tại")
        if kind == "oxygen":
            oxygen_s = upgrade["oxygen_max_s"]
        else:
            hp = upgrade["hp_max"]
    return int(round(oxygen_s * TICK)), hp
