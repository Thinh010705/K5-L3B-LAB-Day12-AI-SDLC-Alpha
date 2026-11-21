"""Buổi tối — Mở Quán. KHUNG: đi lại, chặn biên, đồng hồ, kho nạp từ file/scenario.

Nhóm viết tiếp (PRD-0 mục F, Quán):
  TODO(nhóm, lát 3): khách đến theo lịch, chọn món nấu được, giữ chỗ nguyên liệu, kiên nhẫn,
                     bỏ đi (customer_left), no_dish, vòng đời khách.
  TODO(nhóm, lát 4): interact tại bếp/bàn (cook_started, dish_ready, dish_picked, served),
                     ăn xong trả tiền (paid), boa, uy tín, hết ca (quan_end).
"""

import math

from ..errors import BadInput
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
        # Cấu hình độ tươi (freshness) Contract v1.2
        freshness_cfg = self.t.get("freshness") or tuning.get("freshness") or {}
        self.fresh_initial = float(freshness_cfg.get("initial", 100.0))
        self.quan_decay_per_s = float(freshness_cfg.get("quan_decay_per_s", 0.25))
        self.gather_decay_per_s = float(freshness_cfg.get("gather_decay_per_s", 0.5))
        self.spoiled_below = float(freshness_cfg.get("spoiled_below", 30.0))

        # Phân biệt kho cá thể (v1.2) và kho đếm (v1.0/v1.1)
        raw_inv = inventory if inventory is not None else scenario.get("stock")
        is_items = False
        if isinstance(raw_inv, list):
            is_items = True
        elif isinstance(raw_inv, dict) and "items" in raw_inv and isinstance(raw_inv["items"], list):
            is_items = True
            raw_inv = raw_inv["items"]
        elif scenario.get("contract_version") == "1.2" or "freshness" in self.t or "freshness" in tuning:
            is_items = True
            if raw_inv is None:
                raw_inv = []
            elif isinstance(raw_inv, dict) and "items" not in raw_inv and not raw_inv:
                raw_inv = []

        self.is_item_mode = is_items
        if self.is_item_mode:
            if raw_inv is None:
                raw_inv = []
            if not isinstance(raw_inv, list):
                raise BadInput("kho cá thể phải là danh sách items")
            self.stock = []
            seen_ids = set()
            for it in raw_inv:
                if not isinstance(it, dict) or "id" not in it or "kind" not in it or "fresh" not in it:
                    raise BadInput(f"item kho không hợp lệ: {it}")
                iid = str(it["id"])
                if not iid or iid in seen_ids:
                    raise BadInput(f"id item trùng hoặc rỗng: {iid}")
                seen_ids.add(iid)
                fresh = float(it["fresh"])
                if math.isnan(fresh) or math.isinf(fresh) or fresh < 0.0 or fresh > 100.0:
                    raise BadInput(f"độ tươi ngoài miền [0, 100]: {fresh}")
                self.stock.append({
                    "id": iid,
                    "kind": str(it["kind"]),
                    "fresh": fresh,
                })
                self.ids.reserve(iid)
            self.spoiled_items = {it["id"] for it in self.stock if it["fresh"] < self.spoiled_below}
        else:
            self.stock = dict(inventory if inventory is not None else scenario.get("stock", {}))
            self.spoiled_items = set()

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
        raw_customers = scenario.get("customers", [])

        if self.is_item_mode:
            used_item_ids = set()
            stock_by_id = {it["id"]: it for it in self.stock}
            for c in raw_customers:
                cust = dict(c)
                dish_id = cust.get("dish_id") or cust.get("dish")
                if dish_id:
                    cust["dish_id"] = dish_id
                    cust["dish"] = dish_id
                if "order_tick" not in cust:
                    cust["order_tick"] = 0
                if "state" not in cust:
                    cust["state"] = "waiting"
                if cust.get("state") == "eating":
                    if "eat_ticks_left" not in cust:
                        cust["eat_ticks_left"] = int(round(t.get("eat_s", 10) * TICK))
                    if "tipped" not in cust:
                        cust["tipped"] = cust.get("tip", 0) > 0
                    cust["reserved"] = cust.get("reserved", [])
                else:
                    if "patience_ticks_left" not in cust:
                        cust["patience_ticks_left"] = pat_ticks
                self.customers.append(cust)

            waiting_custs = [c for c in self.customers if c.get("state") == "waiting"]
            # Kiểm tra reserved có sẵn
            for c in waiting_custs:
                if "reserved" in c and c["reserved"] is not None:
                    res_ids = c["reserved"]
                    if not isinstance(res_ids, list):
                        raise BadInput(f"reserved phải là danh sách id cá thể: {res_ids}")
                    dish_id = c.get("dish_id")
                    recipe = self.menu.get(dish_id, {}).get("recipe", {})
                    res_kinds = {}
                    for iid in res_ids:
                        if iid not in stock_by_id:
                            raise BadInput(f"reserved id không tồn tại trong kho: {iid}")
                        if iid in used_item_ids:
                            raise BadInput(f"reserved id bị dùng chung: {iid}")
                        it = stock_by_id[iid]
                        if it["fresh"] < self.spoiled_below:
                            raise BadInput(f"reserved id đã bị ươn: {iid}")
                        used_item_ids.add(iid)
                        res_kinds[it["kind"]] = res_kinds.get(it["kind"], 0) + 1
                    if res_kinds != recipe:
                        raise BadInput(f"reserved không khớp công thức của {dish_id}")

            # Khách waiting chưa có reserved -> tự cấp theo (order_tick, id_key(table_id))
            unreserved = [c for c in waiting_custs if "reserved" not in c or c["reserved"] is None]
            unreserved.sort(key=lambda c: (c.get("order_tick", 0), id_key(c.get("table_id", ""))))
            for c in unreserved:
                dish_id = c.get("dish_id")
                recipe = self.menu.get(dish_id, {}).get("recipe", {})
                allocated = []
                for ing, qty in recipe.items():
                    candidates = [
                        it for it in self.stock
                        if it["kind"] == ing and it["fresh"] >= self.spoiled_below and it["id"] not in used_item_ids and it["id"] not in allocated
                    ]
                    candidates.sort(key=lambda it: (-it["fresh"], id_key(it["id"])))
                    if len(candidates) < qty:
                        raise BadInput(f"Không đủ nguyên liệu khả dụng để cấp reserved cho {dish_id}")
                    for it in candidates[:qty]:
                        allocated.append(it["id"])
                        used_item_ids.add(it["id"])
                c["reserved"] = allocated
        else:
            for c in raw_customers:
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
        # Kế hoạch ngày (nếu có): lọc danh sách món cho phép
        day_plan = scenario.get("day_plan")
        if isinstance(day_plan, dict) and "dishes" in day_plan:
            self.allowed_dishes = list(day_plan["dishes"].keys())
        elif isinstance(scenario.get("plan_dishes"), list) and scenario["plan_dishes"]:
            self.allowed_dishes = list(scenario["plan_dishes"])
        else:
            self.allowed_dishes = list(self.menu.keys())
        self.money = 0
        self.earned = 0
        self.shift_earned = 0
        self.done = False
        self.reason = None

    def _available_stock_counts(self) -> dict:
        """Đếm số lượng khả dụng theo kind (chưa giữ và chưa ươn)."""
        if self.is_item_mode:
            reserved_ids = set()
            for c in self.customers:
                for iid in c.get("reserved", []):
                    reserved_ids.add(iid)
            avail = {}
            for it in self.stock:
                if it["id"] not in reserved_ids and it["fresh"] >= self.spoiled_below:
                    avail[it["kind"]] = avail.get(it["kind"], 0) + 1
            return avail
        else:
            tot = self._total_reserved()
            return {k: self.stock.get(k, 0) - tot.get(k, 0) for k in self.stock}

    def _can_cook(self, dish_id: str, available=None) -> bool:
        if available is None:
            available = self._available_stock_counts()
        recipe = self.menu.get(dish_id, {}).get("recipe", {})
        return all(available.get(ing, 0) >= qty for ing, qty in recipe.items())

    def _total_reserved(self):
        if self.is_item_mode:
            res = set()
            for c in self.customers:
                for iid in c.get("reserved", []):
                    res.add(iid)
            return res
        else:
            res = {}
            for c in self.customers:
                for k, v in c.get("reserved", {}).items():
                    res[k] = res.get(k, 0) + v
            return res

    def _reserve_items_for_dish(self, dish_id: str):
        """Chọn các cá thể khả dụng tươi nhất cho món, hòa theo id."""
        if not self.is_item_mode:
            return dict(self.menu.get(dish_id, {}).get("recipe", {}))
        recipe = self.menu.get(dish_id, {}).get("recipe", {})
        reserved_ids = set()
        for c in self.customers:
            for iid in c.get("reserved", []):
                reserved_ids.add(iid)

        allocated = []
        for ing, qty in recipe.items():
            candidates = [
                it for it in self.stock
                if it["kind"] == ing and it["fresh"] >= self.spoiled_below and it["id"] not in reserved_ids and it["id"] not in allocated
            ]
            candidates.sort(key=lambda it: (-it["fresh"], id_key(it["id"])))
            if len(candidates) < qty:
                return []
            for it in candidates[:qty]:
                allocated.append(it["id"])
        return allocated

    @staticmethod
    def _merge(defaults, updates):
        by_id = {d["id"]: dict(d) for d in defaults}
        for u in updates:
            if u["id"] not in by_id:
                raise BadInput(f"id bếp/bàn không tồn tại: {u['id']}")
            by_id[u["id"]].update(u)
        return sort_by_id(list(by_id.values()))

    def snapshot(self) -> dict:
        occupied = {c["table_id"]: c["id"] for c in self.customers}
        if self.is_item_mode:
            stock_snap = sort_by_id([dict(it) for it in self.stock])
        else:
            stock_snap = {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0}
        return {
            "player": {"pos": self.pos},
            "stock": stock_snap,
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

        # 1. Hao tươi kho thô & xử lý ươn (Phase 3 Contract v1.2)
        if self.is_item_mode:
            decay = self.quan_decay_per_s / TICK
            newly_spoiled = []
            for it in self.stock:
                old_f = it["fresh"]
                new_f = max(0.0, old_f - decay)
                it["fresh"] = new_f
                if old_f >= self.spoiled_below and new_f < self.spoiled_below and it["id"] not in self.spoiled_items:
                    newly_spoiled.append(it)
                    self.spoiled_items.add(it["id"])

            # Phát hết spoiled theo id
            newly_spoiled.sort(key=lambda it: id_key(it["id"]))
            for it in newly_spoiled:
                events.append(("spoiled", {"item_id": it["id"], "kind": it["kind"], "location": "stock"}))

            # Xử lý giữ chỗ bị ươn:
            # Nếu phần giữ có cá thể vừa ươn, nhả toàn bộ phần giữ của đơn và thử giữ lại đúng một lần.
            # Xử lý các đơn bị ảnh hưởng theo order_tick rồi id bàn. Không đủ thì đơn thường chuyển unfulfillable.
            affected = []
            for c in self.customers:
                if c.get("state") == "waiting" and c.get("reserved"):
                    if any(iid in self.spoiled_items for iid in c["reserved"]):
                        affected.append(c)

            if affected:
                for c in affected:
                    c["reserved"] = []
                affected.sort(key=lambda c: (c.get("order_tick", 0), id_key(c.get("table_id", ""))))
                for c in affected:
                    dish_id = c.get("dish_id") or c.get("dish")
                    new_res = self._reserve_items_for_dish(dish_id)
                    if new_res:
                        c["reserved"] = new_res
                    else:
                        c["reserved"] = []
                        c["unfulfillable"] = True

        # 2. Bếp nấu: đếm ngược cook_ticks_left và kiểm tra cháy món (nếu bật burn_s)
        burn_s = self.t.get("burn_s")
        burn_ticks = int(round(burn_s * TICK)) if burn_s is not None else None

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
                if burn_ticks is not None and s["ready_ticks"] > burn_ticks:
                    burnt_dish = s["dish"]
                    order_id = s.get("order_id")
                    s["state"] = "idle"
                    s["dish"] = None
                    s["cook_ticks_left"] = 0
                    s["ready_ticks"] = 0
                    if "order_id" in s:
                        del s["order_id"]

                    order_status = "none"
                    if order_id:
                        c = next((cust for cust in self.customers if cust.get("id") == order_id and cust.get("state") == "waiting"), None)
                        if c is not None:
                            c["reserved"] = [] if self.is_item_mode else {}
                            if self.is_item_mode:
                                new_res = self._reserve_items_for_dish(burnt_dish)
                                if new_res:
                                    c["reserved"] = new_res
                                    order_status = "reserved"
                                else:
                                    c["reserved"] = []
                                    c["unfulfillable"] = True
                                    order_status = "unfulfillable"
                            else:
                                avail = self._available_stock_counts()
                                if self._can_cook(burnt_dish, avail):
                                    recipe = self.menu[burnt_dish]["recipe"]
                                    c["reserved"] = dict(recipe)
                                    order_status = "reserved"
                                else:
                                    c["reserved"] = {}
                                    c["unfulfillable"] = True
                                    order_status = "unfulfillable"

                    events.append(("dish_burnt", {"stove_id": s["id"], "order_id": order_id,
                                                  "dish_id": burnt_dish, "order_status": order_status}))

        # 3. Di chuyển
        self._move(inp)

        # 4. Tương tác (interact)
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

        # 5. Khách đang ăn (eat_ticks_left) & Khách đang chờ (patience_ticks_left)
        remaining_customers = []
        for c in sort_by_id(self.customers):
            if c.get("state") == "eating":
                if c.get("eat_ticks_left", 0) > 0:
                    c["eat_ticks_left"] -= 1
                if c.get("eat_ticks_left", 0) == 0:
                    dish_id = c.get("dish_id") or c.get("dish")
                    dish_info = self.menu.get(dish_id, {})
                    price = c.get("base_price", c.get("price", dish_info.get("price", 0)))

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

        # 6. Hết giờ (Đóng ca chuẩn Phase 2)
        if self.time_left_ticks <= 0:
            self.done = True
            self.reason = "time"
            # Khách còn ăn trả ngay
            for c in sort_by_id(self.customers):
                if c.get("state") == "eating":
                    dish_id = c.get("dish_id") or c.get("dish")
                    dish_info = self.menu.get(dish_id, {})
                    price = c.get("base_price", c.get("price", dish_info.get("price", 0)))

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

            # Khách còn chờ rời mà không trừ uy tín. Dọn món và phần giữ của đơn.
            self.customers = []
            self.hand = None
            for s in self.stoves:
                s["state"] = "idle"
                s["dish"] = None
                s["cook_ticks_left"] = 0
                s["ready_ticks"] = 0
                if "order_id" in s:
                    del s["order_id"]

            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
            return events

        # 7. Khách mới đến theo lịch (nếu còn giờ)
        if self.random_customers:
            first_tick = self.t.get("first_customer_tick", 120)
            interval_ticks = int(round(self.t.get("customer_interval_s", 15) * TICK))
            if self.tick >= first_tick and (self.tick - first_tick) % interval_ticks == 0:
                occupied_tables = {c["table_id"] for c in self.customers}
                available_tables = [tb for tb in sort_by_id(self.tables) if tb["id"] not in occupied_tables]
                if available_tables:
                    available_stock = self._available_stock_counts()
                    allowed = sorted([d for d in self.allowed_dishes if d in self.menu]) or sorted(self.menu.keys())
                    cookable = [d for d in allowed if self._can_cook(d, available_stock)]
                    if not cookable:
                        events.append(("no_dish", {}))
                    else:
                        table = available_tables[0]
                        cid = self.ids.new("C")
                        if len(cookable) == 1:
                            chosen_dish = cookable[0]
                        else:
                            chosen_dish = self.rng.get("customer").choice(cookable)
                        pat_ticks = int(round(self.t.get("patience_s", 60) * TICK))
                        if self.is_item_mode:
                            res = self._reserve_items_for_dish(chosen_dish)
                        else:
                            recipe = self.menu[chosen_dish]["recipe"]
                            res = dict(recipe)
                        new_cust = {
                            "id": cid, "table_id": table["id"],
                            "dish_id": chosen_dish, "dish": chosen_dish,
                            "state": "waiting", "patience_ticks_left": pat_ticks,
                            "reserved": res,
                            "order_tick": self.tick
                        }
                        self.customers.append(new_cust)

        return events

    def _interact_stove(self, s: dict, events: list):
        # 1. Bếp đã chín và tay trống -> bưng đĩa
        if s.get("state") == "ready" and self.hand is None:
            dish = s["dish"]
            self.hand = dish
            self.hand_base_price = s.get("base_price", self.menu.get(dish, {}).get("price", 0))
            self.hand_order_id = s.get("order_id")
            s["state"] = "idle"
            s["dish"] = None
            s["cook_ticks_left"] = 0
            s["ready_ticks"] = 0
            if "order_id" in s:
                del s["order_id"]
            if "base_price" in s:
                del s["base_price"]
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

                if self.is_item_mode:
                    res_ids = set(target_customer.get("reserved", []))
                    used_items = [it for it in self.stock if it["id"] in res_ids]
                    used_counts = {}
                    for it in used_items:
                        used_counts[it["kind"]] = used_counts.get(it["kind"], 0) + 1

                    if used_counts == recipe:
                        # Tiêu đúng các id đang giữ
                        self.stock = [it for it in self.stock if it["id"] not in res_ids]
                        target_customer["reserved"] = []

                        # Chốt base_price = floor(giá niêm yết × trung bình fresh / 100)
                        avg_fresh = sum(it["fresh"] for it in used_items) / len(used_items) if used_items else 100.0
                        base_price = math.floor(self.menu[dish_to_cook]["price"] * avg_fresh / 100.0)
                        target_customer["base_price"] = base_price

                        s["state"] = "cooking"
                        s["dish"] = dish_to_cook
                        s["order_id"] = target_customer["id"]
                        s["base_price"] = base_price
                        s["cook_ticks_left"] = int(round(self.menu[dish_to_cook]["cook_s"] * TICK))
                        s["ready_ticks"] = 0

                        # cook_started.data.items là mảng cá thể sắp theo kind rồi id
                        used_sorted = sorted([dict(it) for it in used_items], key=lambda it: (it["kind"], id_key(it["id"])))
                        events.append(("cook_started", {
                            "stove_id": s["id"],
                            "dish": dish_to_cook,
                            "items": used_sorted
                        }))
                else:
                    if all(self.stock.get(ing, 0) >= qty for ing, qty in recipe.items()):
                        for ing, qty in recipe.items():
                            self.stock[ing] -= qty
                            if self.stock[ing] == 0:
                                del self.stock[ing]
                        target_customer["reserved"] = {}
                        base_price = self.menu[dish_to_cook]["price"]
                        target_customer["base_price"] = base_price

                        s["state"] = "cooking"
                        s["dish"] = dish_to_cook
                        s["order_id"] = target_customer["id"]
                        s["base_price"] = base_price
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
                    if hasattr(self, "hand_base_price"):
                        c["base_price"] = self.hand_base_price
                        del self.hand_base_price
                    elif "base_price" not in c:
                        c["base_price"] = self.menu.get(dish_served, {}).get("price", 0)

                    c["eat_ticks_left"] = int(round(self.t.get("eat_s", 10) * TICK))
                    pat_max = int(round(self.t.get("patience_s", 60) * TICK))
                    c["tipped"] = (c.get("patience_ticks_left", 0) / pat_max) >= self.t.get("tip_min_patience_ratio", 0.5)
                    c["reserved"] = [] if self.is_item_mode else {}
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
