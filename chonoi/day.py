"""Headless Test Contract v1.1 day orchestration atop GatherSim and QuanSim.

The Day Controller owns lifecycle, economy, shop and pause. Fish movement, monsters
and UI rendering remain the responsibility of Gather/UI modules and are not
implemented here. Do not treat Day smoke tests as full Phase 2 acceptance.
"""
from __future__ import annotations

from copy import deepcopy
import math

from .errors import BadInput
from .ids import IdAllocator
from .inputs import InputPlayer, BUTTONS_V11_CORE
from .jsonl import JsonlWriter
from .rng import Streams
from .shop import Shop
from .sim.gather import GatherSim
from .sim.quan import QuanSim


def _plan(tuning, day, overrides):
    plan_list = tuning["day_plan"]
    planned = deepcopy(plan_list[(day - 1) % len(plan_list)])
    planned["day"] = day
    raw = next((p for p in overrides if p["day"] == day), None)
    if raw is not None:
        planned["dishes"] = deepcopy(raw["dishes"])
    recipe_map = tuning["menu"]
    required = {}
    for dish_id, count in planned["dishes"].items():
        for kind, amount in recipe_map[dish_id]["recipe"].items():
            required[kind] = required.get(kind, 0) + count * amount
    planned["ingredients"] = required
    return planned


def _legacy_fish_fixture(gather_tuning, streams):
    """Compatibility shim for the uploaded P1 GatherSim which still wants a list.

    Not a substitute for Phase 2 fish movement/spawning, which Gather owner must
    implement separately. Deterministic 8 unique starting locations only.
    """
    count = gather_tuning["fish_initial"]
    if isinstance(count, list):
        return deepcopy(count)
    spots = [(kind, x, d)
             for kind in sorted(gather_tuning["fish_spawn_depths"])
             for x in gather_tuning["fish_spawn_x"]
             for d in gather_tuning["fish_spawn_depths"][kind]]
    rng = streams.get("initial_fish")
    # 36 kind/position pairs but only 30 geometric positions. Never place two
    # initial schools at the same x/depth even when kinds differ.
    rng.shuffle(spots)
    samples, taken = [], set()
    for kind, x, d in spots:
        if (x, d) not in taken:
            samples.append((kind, x, d))
            taken.add((x, d))
        if len(samples) == count:
            break
    return [{"id": f"F{i}", "kind": kind, "pos": [x, d],
             "heading_deg": rng.randrange(360)}
            for i, (kind, x, d) in enumerate(samples, 1)]


class DaySession:
    mode = "day"

    def __init__(self, tuning, scenario, seed, days=1, allow_soak=False):
        max_days = 20 if allow_soak or (isinstance(days, int) and days > 5) else 5
        if type(days) is not int or not 1 <= days <= max_days:
            raise BadInput(f"--days phải là số nguyên từ 1 đến {max_days}")
        if "day_plan" not in tuning or "shop" not in tuning:
            raise BadInput("day yêu cầu tuning.day_plan và tuning.shop v1.1")
        self.tuning, self.scenario, self.seed = tuning, scenario, seed
        self.days = days
        self.tick = self.sim_tick = self.phase_tick = 0
        self.day = 1
        self.days_completed = 0
        self.done = self.paused = False
        state = scenario.get("day", {})
        self.money = state.get("money", 0)
        self.earned = state.get("earned", 0)
        self.reputation = state.get("reputation", tuning["quan"]["reputation_initial"])
        self.upgrades = dict(state.get("upgrades", {}))
        self.active_upgrades = {}
        self.ids = IdAllocator()  # Không tái dùng ID cá thể đã dùng/bỏ ở pha/ngày trước.
        self._overrides = state.get("day_plan", [])
        self.phase = "gather"
        self.shop = None
        self._start_gather()
        self.initial_events = [self._event("day_start", {}),
                               self._event("day_plan", {"dishes": dict(self.day_plan["dishes"]),
                                                        "ingredients": dict(self.day_plan["ingredients"])}),
                               self._event("phase_start", {})]

    def _event(self, name, data, phase=None, day=None):
        return {"type": "event", "tick": self.tick, "phase": phase or self.phase,
                "day": day or self.day, "name": name, "data": data}

    def _start_gather(self):
        self.phase = "gather"
        self.phase_tick = 0
        self.active_upgrades = dict(self.upgrades)
        self.day_plan = _plan(self.tuning, self.day, self._overrides)
        day_tuning = deepcopy(self.tuning)
        self._day_tuning = day_tuning
        sc = deepcopy(self.scenario.get("gather", {}))
        if day_tuning.get("_contract_version") == "1.2" and self.day > 1:
            for item in sc.get("hold", []):
                item["id"] = self.ids.new("I")
        streams = Streams(f"{self.seed}:day:{self.day}:gather")
        gather_day = ((self.day - 1) % 5) + 1
        self.sim = GatherSim(day_tuning, sc, streams, self.ids,
                             day=gather_day, active_upgrades=self.active_upgrades)
        self.shop = None

    def _start_quan(self):
        self.phase = "quan"
        self.phase_tick = 0
        sc = deepcopy(self.scenario.get("quan", {}))
        sc["day_plan"] = self.day_plan
        inventory = self.sim.inventory_items()
        streams = Streams(f"{self.seed}:day:{self.day}:quan")
        self.sim = QuanSim(self.tuning, sc, streams, self.ids, inventory=inventory)
        self.sim.money = self.money
        self.sim.earned = self.earned
        self.sim.reputation = self.reputation

    def _start_shop(self):
        self.phase = "shop"
        self.phase_tick = 0
        self.money = self.sim.money
        self.earned = self.sim.earned
        self.reputation = self.sim.reputation
        self.shop = Shop(self.tuning, self.money, self.upgrades, self.sim.stock)
        self.sim = None

    def _end_shop(self):
        self.money = self.shop.money
        self.upgrades = dict(self.shop.upgrades)
        self.days_completed += 1
        if self.days_completed >= self.days:
            self.done = True
        else:
            self.day += 1
            self._start_gather()

    def snapshot(self):
        state = "finished" if self.done else "paused" if self.paused else "playing"
        snap = {"type": "snapshot", "tick": self.tick, "sim_tick": self.sim_tick,
                "mode": "day", "phase": self.phase, "phase_tick": self.phase_tick,
                "state": state, "day": self.day, "day_plan": deepcopy(self.day_plan),
                "upgrades": dict(self.upgrades), "active_upgrades": dict(self.active_upgrades),
                "money": self.money, "earned": self.earned, "reputation": self.reputation,
                "score": self.earned + self.tuning["score"]["reputation_multiplier"] * math.floor(self.reputation)}
        if self.phase == "shop":
            snap["time_left_ticks"] = self.shop.time_left_ticks
            snap.update(self.shop.snapshot())
        else:
            if self.phase == "quan":
                self.money, self.earned, self.reputation = self.sim.money, self.sim.earned, self.sim.reputation
                snap.update({"money": self.money, "earned": self.earned, "reputation": self.reputation,
                             "score": self.earned + self.tuning["score"]["reputation_multiplier"] * math.floor(self.reputation)})
            snap["time_left_ticks"] = self.sim.time_left_ticks
            snap.update(self.sim.snapshot())
        return snap

    def step(self, inp):
        if self.done:
            return []
        self.tick += 1
        if inp.pressed("pause"):
            self.paused = not self.paused
            events = [self._event("paused" if self.paused else "resumed", {})]
            if self.paused:
                return events
        else:
            events = []
        if self.paused:
            return events
        self.sim_tick += 1
        self.phase_tick += 1
        phase_at_start = self.phase
        if self.phase == "shop":
            for name, data in self.shop.step(inp):
                events.append(self._event(name, data, phase=phase_at_start))
            self.money = self.shop.money
            self.upgrades = dict(self.shop.upgrades)
            if self.shop.done:
                self._end_shop()
                if not self.done:
                    events.extend([self._event("day_start", {}),
                                   self._event("day_plan", {"dishes": dict(self.day_plan["dishes"]),
                                                            "ingredients": dict(self.day_plan["ingredients"])}),
                                   self._event("phase_start", {})])
        else:
            for name, data in self.sim.step(inp):
                events.append(self._event(name, data, phase=phase_at_start))
            if self.phase == "quan":
                self.money = self.sim.money
                self.earned = self.sim.earned
                self.reputation = self.sim.reputation
            if self.sim.done:
                if self.phase == "gather":
                    self._start_quan()
                else:
                    self._start_shop()
                events.append(self._event("phase_start", {}))
        return events

    def end_row(self):
        return {"type": "end", "ticks": self.tick, "sim_tick": self.sim_tick,
                "mode": "day", "state": "finished" if self.done else "playing",
                "reason": "days_complete" if self.done else "tick_limit",
                "money": self.money, "earned": self.earned, "reputation": self.reputation,
                "score": self.earned + self.tuning["score"]["reputation_multiplier"] * math.floor(self.reputation),
                "days_completed": self.days_completed}


def run_day(tuning, scenario, seed, frames, ticks, out_path, snapshot_every, days=1):
    # Create all dynamic state before opening the output file.
    sess = DaySession(tuning, scenario, seed, days)
    player = InputPlayer(frames, buttons=BUTTONS_V11_CORE)
    w = JsonlWriter(out_path)
    try:
        for row in sess.initial_events:
            w.write(row)
        w.write(sess.snapshot())
        last_snapped = 0
        while sess.tick < ticks and not sess.done:
            for row in sess.step(player.advance(sess.tick)):
                w.write(row)
            if sess.tick % snapshot_every == 0 or sess.done:
                w.write(sess.snapshot())
                last_snapped = sess.tick
        if last_snapped != sess.tick:
            w.write(sess.snapshot())
        w.write(sess.end_row())
    finally:
        w.close()
    return sess
