"""Phase 2 shop: synchronous tick-based upgrades, independent of UI."""
from __future__ import annotations


class Shop:
    def __init__(self, tuning, money, upgrades, stock=None):
        self.t = tuning["shop"]
        self.money = money
        self.upgrades = dict(upgrades)
        self.stock = dict(stock or {})
        self.time_left_ticks = self.t["max_ticks"]
        self.done = False
        self.reason = None

    def step(self, inp):
        if self.done:
            return []
        self.time_left_ticks -= 1
        events = []
        # The one-shot buy command precedes shop_done, including the last tick.
        if inp.buy is not None:
            kind = inp.buy
            levels = self.t["upgrades"].get(kind)
            if levels is None:
                events.append(("buy_failed", {"action": kind, "reason": "unknown"}))
            else:
                current = self.upgrades.get(kind, 0)
                if current >= len(levels):
                    events.append(("buy_failed", {"action": kind, "reason": "max_level"}))
                else:
                    next_level = levels[current]
                    price = next_level["price"]
                    if self.money < price:
                        events.append(("buy_failed", {"action": kind, "reason": "funds"}))
                    else:
                        self.money -= price
                        self.upgrades[kind] = next_level["level"]
                        events.append(("bought", {"upgrade": kind, "level": next_level["level"],
                                                  "price": price, "money": self.money}))
        if inp.pressed("shop_done"):
            self.done, self.reason = True, "done"
        elif self.time_left_ticks <= 0:
            self.done, self.reason = True, "time"
        if self.done:
            events.append(("shop_end", {"reason": self.reason}))
        return events

    def snapshot(self):
        return {"stock": {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0}}
