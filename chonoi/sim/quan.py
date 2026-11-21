"""Buổi tối — Mở Quán. KHUNG: đi lại, chặn biên, đồng hồ, kho nạp từ file/scenario.

Nhóm viết tiếp (PRD-0 mục F, Quán):
  TODO(nhóm, lát 3): khách đến theo lịch, chọn món nấu được, giữ chỗ nguyên liệu, kiên nhẫn,
                     bỏ đi (customer_left), no_dish, vòng đời khách.
  TODO(nhóm, lát 4): interact tại bếp/bàn (cook_started, dish_ready, dish_picked, served),
                     ăn xong trả tiền (paid), boa, uy tín, hết ca (quan_end).
"""

import math

from ..ids import id_key, sort_by_id
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
            if "order_tick" not in cust:
                cust["order_tick"] = 0
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
        self.tick = 0
        self.random_customers = scenario.get("random_customers", True)
        self.money = 0
        self.earned = 0
        self.shift_earned = 0
        self.done = False
        self.reason = None

    def _can_cook(self, dish_id: str, stock: dict) -> bool:
        recipe = self.menu.get(dish_id, {}).get("recipe", {})
        return all(stock.get(ing, 0) >= qty for ing, qty in recipe.items())

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
        self.tick += 1

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

        # 2. Khách đang ăn (eat_ticks_left) & Khách đang chờ (patience_ticks_left)
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
                        tip = math.floor(price * self.t.get("tip_rate", 0.2))
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
            elif c.get("state") == "waiting":
                if c.get("patience_ticks_left", 0) > 0:
                    c["patience_ticks_left"] -= 1
                if c.get("patience_ticks_left", 0) == 0:
                    rep_min = float(self.t.get("reputation_min", 0.0))
                    rep_delta = float(self.t.get("left_reputation_delta", -0.5))
                    self.reputation = max(rep_min, self.reputation + rep_delta)
                    events.append(("customer_left", {"customer_id": c["id"], "table_id": c["table_id"],
                                                     "reason": "impatient"}))
                    continue
            remaining_customers.append(c)
        self.customers = remaining_customers

        # 3. Khách mới đến theo lịch
        if self.random_customers:
            first_tick = self.t.get("first_customer_tick", 120)
            interval_ticks = int(round(self.t.get("customer_interval_s", 15) * TICK))
            if self.tick >= first_tick and (self.tick - first_tick) % interval_ticks == 0:
                occupied_tables = {c["table_id"] for c in self.customers}
                available_tables = [tb for tb in sort_by_id(self.tables) if tb["id"] not in occupied_tables]
                if available_tables:
                    tot_reserved = self._total_reserved()
                    available_stock = {k: self.stock.get(k, 0) - tot_reserved.get(k, 0) for k in self.stock}
                    cookable = [d for d in sorted(self.menu.keys()) if self._can_cook(d, available_stock)]
                    if not cookable:
                        events.append(("no_dish", {}))
                    else:
                        table = available_tables[0]
                        cid = self.ids.new("C")
                        if len(cookable) == 1:
                            chosen_dish = cookable[0]
                        else:
                            chosen_dish = self.rng.get("customer").choice(cookable)
                        recipe = self.menu[chosen_dish]["recipe"]
                        pat_ticks = int(round(self.t.get("patience_s", 60) * TICK))
                        new_cust = {
                            "id": cid, "table_id": table["id"],
                            "dish_id": chosen_dish, "dish": chosen_dish,
                            "state": "waiting", "patience_ticks_left": pat_ticks,
                            "reserved": dict(recipe),
                            "order_tick": self.tick
                        }
                        self.customers.append(new_cust)

        # 4. Di chuyển
        self._move(inp)

        # 5. Tương tác (interact)
        if inp.pressed("interact"):
            radius = self.t.get("interact_radius", 1.5)
            candidates = []
            for s in self.stoves:
                d = math.dist(self.pos, s["pos"])
                if d <= radius:
                    candidates.append((d, 0, id_key(s["id"]), "stove", s))
            for tb in self.tables:
                d = math.dist(self.pos, tb["pos"])
                if d <= radius:
                    candidates.append((d, 1, id_key(tb["id"]), "table", tb))

            candidates.sort(key=lambda x: (x[0], x[1], x[2]))
            if candidates:
                cand = candidates[0]
                ctype, obj = cand[3], cand[4]
                if ctype == "stove":
                    self._interact_stove(obj, events)
                elif ctype == "table":
                    self._interact_table(obj, events)

        # 6. Hết giờ
        if self.time_left_ticks <= 0:
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
        return events

    def _interact_stove(self, s: dict, events: list):
        # 1. Bếp đã chín và tay trống -> bưng đĩa
        if s.get("state") == "ready" and self.hand is None:
            dish = s["dish"]
            self.hand = dish
            s["state"] = "idle"
            s["dish"] = None
            s["cook_ticks_left"] = 0
            s["ready_ticks"] = 0
            events.append(("dish_picked", {"stove_id": s["id"], "dish": dish}))
            return

        # 2. Bếp rảnh và tay trống -> nấu món cho khách đang chờ
        if s.get("state") == "idle" and self.hand is None:
            already_prep = [st["dish"] for st in self.stoves if st.get("dish") and st.get("state") in ("cooking", "ready")]
            if self.hand:
                already_prep.append(self.hand)
            prep_copy = list(already_prep)

            waiting_sorted = sorted(
                [c for c in self.customers if c.get("state") == "waiting"],
                key=lambda c: (c.get("order_tick", 0), id_key(c.get("table_id", "")))
            )

            target_customer = None
            for c in waiting_sorted:
                d_id = c.get("dish_id") or c.get("dish")
                if d_id in prep_copy:
                    prep_copy.remove(d_id)
                else:
                    target_customer = c
                    break

            if target_customer is not None:
                dish_to_cook = target_customer.get("dish_id") or target_customer.get("dish")
                recipe = self.menu[dish_to_cook]["recipe"]
                if all(self.stock.get(ing, 0) >= qty for ing, qty in recipe.items()):
                    for ing, qty in recipe.items():
                        self.stock[ing] -= qty
                        if self.stock[ing] == 0:
                            del self.stock[ing]
                    target_customer["reserved"] = {}
                    s["state"] = "cooking"
                    s["dish"] = dish_to_cook
                    s["order_id"] = target_customer["id"]
                    s["cook_ticks_left"] = int(round(self.menu[dish_to_cook]["cook_s"] * TICK))
                    s["ready_ticks"] = 0
                    events.append(("cook_started", {"stove_id": s["id"], "dish": dish_to_cook}))

    def _interact_table(self, tb: dict, events: list):
        if self.hand is not None:
            c = next((cust for cust in self.customers if cust.get("table_id") == tb["id"]), None)
            if c is not None and c.get("state") == "waiting":
                dish_needed = c.get("dish_id") or c.get("dish")
                if dish_needed == self.hand:
                    dish_served = self.hand
                    self.hand = None
                    c["state"] = "eating"
                    c["eat_ticks_left"] = int(round(self.t.get("eat_s", 10) * TICK))
                    pat_max = int(round(self.t.get("patience_s", 60) * TICK))
                    c["tipped"] = (c.get("patience_ticks_left", 0) / pat_max) >= self.t.get("tip_min_patience_ratio", 0.5)
                    c["reserved"] = {}
                    events.append(("served", {"customer_id": c["id"], "table_id": tb["id"], "dish": dish_served}))

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
