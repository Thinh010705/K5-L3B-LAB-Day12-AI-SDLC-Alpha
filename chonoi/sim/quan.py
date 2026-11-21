"""Buổi tối — Mở Quán. KHUNG: đi lại, chặn biên, đồng hồ, kho nạp từ file/scenario.

Nhóm viết tiếp (PRD-0 mục F, Quán):
  TODO(nhóm, lát 3): khách đến theo lịch, chọn món nấu được, giữ chỗ nguyên liệu, kiên nhẫn,
                     bỏ đi (customer_left), no_dish, vòng đời khách.
  TODO(nhóm, lát 4): interact tại bếp/bàn (cook_started, dish_ready, dish_picked, served),
                     ăn xong trả tiền (paid), boa, uy tín, hết ca (quan_end).
"""

from ..ids import sort_by_id
from .ramp import ramp_velocity

TICK = 60.0


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None):
        t = tuning["quan"]
        self.t = t
        self.menu = tuning["menu"]
        self.rng = streams
        self.ids = ids
        p = scenario.get("player", {})
        self.pos = list(p.get("pos", t["start_pos"]))
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        # kho: --inventory HOẶC scenario.stock (cả hai -> cli đã báo mã 2)
        self.stock = dict(inventory if inventory is not None else scenario.get("stock", {}))
        self.hand = scenario.get("hand")
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * 60)))
        self.reputation = scenario.get("reputation", t["reputation_initial"])
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"),
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        # Khách dựng sẵn từ scenario (customers[]) và suy ra giữ chỗ (reserved).
        self.customers = []
        pat_ticks = int(round(t.get("patience_s", 60) * TICK))
        for c in scenario.get("customers", []):
            cust = dict(c)
            dish_id = cust.get("dish_id") or cust.get("dish")
            if dish_id and "reserved" not in cust:
                recipe = self.menu.get(dish_id, {}).get("recipe", {})
                cust["reserved"] = dict(recipe)
            elif "reserved" not in cust:
                cust["reserved"] = {}
            if "state" not in cust:
                cust["state"] = "waiting"
            if dish_id:
                if "dish_id" not in cust:
                    cust["dish_id"] = dish_id
                if "dish" not in cust:
                    cust["dish"] = dish_id
            if cust.get("state") == "eating":
                if "eat_ticks_left" not in cust:
                    cust["eat_ticks_left"] = int(round(t.get("eat_s", 10) * TICK))
                if "tipped" not in cust:
                    cust["tipped"] = cust.get("tip", 0) > 0
            else:
                if "patience_ticks_left" not in cust:
                    cust["patience_ticks_left"] = pat_ticks
            self.customers.append(cust)

        for e in self.customers:
            ids.reserve(e["id"])
        for s in self.stoves:
            ids.reserve(s["id"])
        for tb in self.tables:
            ids.reserve(tb["id"])
        self.money = 0
        self.earned = 0
        self.shift_earned = 0
        self.done = False
        self.reason = None

    def _total_reserved(self) -> dict:
        res = {}
        for c in self.customers:
            for k, v in c.get("reserved", {}).items():
                res[k] = res.get(k, 0) + v
        return res

    @staticmethod
    def _merge(defaults, updates):
        by_id = {d["id"]: dict(d) for d in defaults}
        for u in updates:
            if u["id"] not in by_id:
                from ..errors import BadInput
                raise BadInput(f"id bếp/bàn không tồn tại: {u['id']}")
            by_id[u["id"]].update(u)
        return sort_by_id(list(by_id.values()))

    def snapshot(self) -> dict:
        occupied = {c["table_id"]: c["id"] for c in self.customers}
        return {
            "player": {"pos": self.pos},
            "stock": {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0},
            "hand": self.hand,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                       for s in self.stoves],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])} for tb in self.tables],
            "customers": sort_by_id(self.customers),
        }

    def step(self, inp):
        events = []
        self.time_left_ticks = max(0, self.time_left_ticks - 1)

        # 1. Bếp nấu: đếm ngược cook_ticks_left
        for s in sort_by_id(self.stoves):
            if s.get("state") == "cooking":
                if s.get("cook_ticks_left", 0) > 0:
                    s["cook_ticks_left"] -= 1
                    if s["cook_ticks_left"] == 0:
                        s["state"] = "ready"
                        s["ready_ticks"] = 0
                        events.append(("dish_ready", {"stove_id": s["id"], "dish": s["dish"]}))
            elif s.get("state") == "ready":
                s["ready_ticks"] = s.get("ready_ticks", 0) + 1

        # 2. Khách đang ăn: đếm ngược eat_ticks_left
        remaining_customers = []
        for c in sort_by_id(self.customers):
            if c.get("state") == "eating":
                if c.get("eat_ticks_left", 0) > 0:
                    c["eat_ticks_left"] -= 1
                if c.get("eat_ticks_left", 0) == 0:
                    dish_id = c.get("dish_id") or c.get("dish")
                    dish_info = self.menu.get(dish_id, {})
                    price = c.get("price", dish_info.get("price", 0))

                    if "tip" in c:
                        tip = c["tip"]
                    elif c.get("tipped", False):
                        tip = int(round(price * self.t.get("tip_rate", 0.2)))
                    else:
                        tip = 0

                    paid_amount = price + tip
                    self.money += paid_amount
                    self.earned += paid_amount
                    self.shift_earned += paid_amount

                    if tip > 0:
                        rep_max = float(self.t.get("reputation_max", 5.0))
                        rep_delta = float(self.t.get("tip_reputation", 0.2))
                        self.reputation = min(rep_max, self.reputation + rep_delta)

                    events.append(("paid", {"customer_id": c["id"], "table_id": c["table_id"],
                                            "dish": dish_id, "price": price, "tip": tip}))
                    continue
            remaining_customers.append(c)
        self.customers = remaining_customers

        # 3. Di chuyển
        self._move(inp)

        # 4. Hết giờ
        if self.time_left_ticks <= 0:
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
        return events

    def _move(self, inp):
        speed = self.t["walk_speed"]
        mx, mz = inp.move
        self.vel = ramp_velocity(self, (mx * speed, mz * speed), int(self.t.get("ramp_max_ticks", 6)))
        b = self.t["bounds"]
        for i, axis in enumerate(("x", "z")):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i], self.vel[i] = lo, max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i], self.vel[i] = hi, min(0.0, self.vel[i])
