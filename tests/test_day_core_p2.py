"""Integration tests for Day Controller/Shop (NOT Gather fish/monster acceptance)."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from chonoi.contract import load_contract
from chonoi.day import DaySession, run_day
from chonoi.errors import BadInput
from chonoi.headless import main as cli_main
from chonoi.inputs import BUTTONS_V11_CORE, InputPlayer, load_frames
from chonoi.shop import Shop
from chonoi.scenario_day import load_day_scenario

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "docs/contracts/game.contract.v1_1.proposed.json"


def inp(frames, tick):
    return InputPlayer(frames, buttons=BUTTONS_V11_CORE).advance(tick)


class DayCoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_contract(str(MANIFEST))
        cls.tuning = cls.config["tuning"]

    def scenario(self, money=0):
        return {"gather": {"hold": ["ca_loc", "bong_sung", "bong_sung"], "random_fish": False},
                "quan": {"time_left_ticks": 1, "random_customers": False},
                "day": {"money": money, "earned": money}}

    def make(self, days=1, money=0):
        return DaySession(self.tuning, self.scenario(money), 17, days)

    def test_day_initial_events_and_snapshot(self):
        s = self.make()
        self.assertEqual([e["name"] for e in s.initial_events],
                         ["day_start", "day_plan", "phase_start"])
        self.assertEqual([e["tick"] for e in s.initial_events], [0, 0, 0])
        snap = s.snapshot()
        self.assertEqual((snap["phase"], snap["day"], snap["phase_tick"]), ("gather", 1, 0))
        self.assertEqual(snap["day_plan"]["ingredients"], {"ca_loc": 3, "bong_sung": 6})

    def test_default_eight_unique_initial_fish(self):
        s = DaySession(self.tuning, {}, 19)
        positions = [tuple(f["pos"]) for f in s.sim.fish]
        self.assertEqual(len(positions), 8)
        self.assertEqual(len(set(positions)), 8)

    def test_gather_inventory_transfer_to_quan(self):
        s = self.make()
        ev = s.step(inp([{"tick": 0, "interact": True}], 0))
        self.assertEqual([e["name"] for e in ev], ["gather_end", "phase_start"])
        self.assertEqual([e["phase"] for e in ev], ["gather", "quan"])
        self.assertEqual(ev[0]["data"]["inventory"], {"items": {"bong_sung": 2, "ca_loc": 1}})
        self.assertEqual(s.snapshot()["stock"], {"ca_loc": 1, "bong_sung": 2})
        self.assertEqual(s.snapshot()["phase_tick"], 0)

    def test_shop_purchase_and_day_completion(self):
        s = self.make(money=200)
        player = InputPlayer([{"tick": 0, "interact": True}, {"tick": 2, "buy": "oxygen"},
                              {"tick": 3, "shop_done": True}], buttons=BUTTONS_V11_CORE)
        s.step(player.advance(0))
        events = s.step(player.advance(1))
        self.assertEqual([e["name"] for e in events], ["quan_end", "phase_start"])
        self.assertEqual(s.phase, "shop")
        ev = s.step(player.advance(2))
        self.assertEqual(ev[0]["name"], "bought")
        self.assertEqual((s.money, s.earned, s.upgrades["oxygen"]), (0, 200, 1))
        self.assertEqual(s.active_upgrades, {})
        ev = s.step(player.advance(3))
        self.assertEqual(ev[-1]["name"], "shop_end")
        self.assertTrue(s.done)
        self.assertEqual(s.end_row()["days_completed"], 1)
        self.assertEqual(s.end_row()["reason"], "days_complete")

    def test_buy_and_shop_done_same_tick(self):
        s = self.make(money=200)
        p = InputPlayer([{"tick": 0, "interact": True},
                         {"tick": 2, "buy": "oxygen", "shop_done": True}],
                        buttons=BUTTONS_V11_CORE)
        for i in range(2):
            s.step(p.advance(i))
        events = s.step(p.advance(2))
        self.assertEqual([e["name"] for e in events], ["bought", "shop_end"])
        self.assertEqual(events[-1]["data"], {"reason": "done"})
        self.assertTrue(s.done)

    def test_upgrade_effect_begins_next_day(self):
        s = self.make(days=2, money=200)
        p = InputPlayer([{"tick": 0, "interact": True},
                         {"tick": 2, "buy": "oxygen", "shop_done": True}],
                        buttons=BUTTONS_V11_CORE)
        for i in range(3):
            ev = s.step(p.advance(i))
        self.assertEqual(s.day, 2)
        self.assertEqual([e["name"] for e in ev], ["bought", "shop_end", "day_start", "day_plan", "phase_start"])
        self.assertEqual(s.upgrades["oxygen"], 1)
        self.assertEqual(s.active_upgrades["oxygen"], 1)
        self.assertEqual(s.sim.oxygen_max, 2700)
        self.assertEqual(s.days_completed, 1)
        self.assertFalse(s.done)
        self.assertEqual(s.day_plan["ingredients"], {"ca_loc": 2, "ca_linh": 6, "bong_dien_dien": 2})

    def test_shop_failures_unknown_funds_max(self):
        t = self.tuning
        shop = Shop(t, 0, {})
        p = InputPlayer([{"tick": 0, "buy": "unknown"}, {"tick": 1, "buy": "hp"}],
                        buttons=BUTTONS_V11_CORE)
        self.assertEqual(shop.step(p.advance(0))[0][1]["reason"], "unknown")
        self.assertEqual(shop.step(p.advance(1))[0][1]["reason"], "funds")
        maxed = Shop(t, 800, {"hp": 2})
        x = InputPlayer([{"tick": 0, "buy": "hp"}], buttons=BUTTONS_V11_CORE)
        self.assertEqual(maxed.step(x.advance(0))[0][1]["reason"], "max_level")

    def test_shop_timeout_is_600_active_ticks(self):
        s = self.make()
        p = InputPlayer([{"tick": 0, "interact": True}], buttons=BUTTONS_V11_CORE)
        s.step(p.advance(0))
        s.step(p.advance(1))
        self.assertEqual(s.phase, "shop")
        for i in range(2, 601):
            s.step(p.advance(i))
        self.assertFalse(s.done)
        self.assertEqual(s.shop.time_left_ticks, 1)
        ev = s.step(p.advance(601))
        self.assertTrue(s.done)
        self.assertEqual(ev[-1]["data"], {"reason": "time"})

    def test_pause_freezes_sim_and_phase_timers(self):
        s = self.make()
        p = InputPlayer([{"tick": 0, "pause": True},
                         {"tick": 1, "pause": False},
                         {"tick": 2, "pause": True}], buttons=BUTTONS_V11_CORE)
        t0 = s.sim.time_left_ticks
        self.assertEqual(s.step(p.advance(0))[0]["name"], "paused")
        self.assertEqual((s.tick, s.sim_tick, s.phase_tick), (1, 0, 0))
        self.assertEqual(s.snapshot()["state"], "paused")
        self.assertEqual(s.step(p.advance(1)), [])
        self.assertEqual(s.sim.time_left_ticks, t0)
        ev = s.step(p.advance(2))
        self.assertEqual(ev[0]["name"], "resumed")
        self.assertEqual((s.tick, s.sim_tick, s.phase_tick), (3, 1, 1))
        self.assertEqual(s.sim.time_left_ticks, t0 - 1)

    def test_one_shot_buy_not_inherited(self):
        p = InputPlayer([{"tick": 0, "buy": "hp"}], buttons=BUTTONS_V11_CORE)
        self.assertEqual(p.advance(0).buy, "hp")
        self.assertIsNone(p.advance(1).buy)

    def test_two_runs_exact_same_jsonl_bytes(self):
        scenario = self.scenario(money=200)
        frames = [{"tick": 0, "interact": True}, {"tick": 2, "buy": "oxygen", "shop_done": True}]
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / "a.jsonl", Path(tmp) / "b.jsonl"
            run_day(self.tuning, scenario, 23, frames, 10, a, 1)
            run_day(self.tuning, scenario, 23, frames, 10, b, 1)
            self.assertEqual(a.read_bytes(), b.read_bytes())
            rows = [json.loads(x) for x in a.read_text().splitlines()]
            self.assertEqual(rows[-1]["reason"], "days_complete")

    def test_day_scenario_invalid_before_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            sc = Path(tmp) / "bad.json"
            for data in [{"day": {"money": 201, "earned": 200}},
                         {"quan": {"stock": {"ca_loc": 1}}},
                         {"gather": {"hold": ["wrong"]}},
                         {"day": {"day_plan": [{"day": 1, "dishes": {"ca_loc_nuong_trui": 1},
                                                "ingredients": {"ca_loc": 2}}]}}]:
                sc.write_text(json.dumps(data))
                with self.assertRaises(BadInput):
                    load_day_scenario(sc, self.tuning, 1)

    def test_cli_day_with_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "day.jsonl"
            fixture = Path(tmp) / "fixture.json"
            fixture.write_text(json.dumps(self.scenario()))
            with patch("chonoi.headless.load_contract", return_value=self.config):
                self.assertEqual(cli_main(["--mode", "day", "--days", "1", "--seed", "1",
                                           "--ticks", "1", "--scenario", str(fixture),
                                           "--out", str(target)]), 0)
            self.assertTrue(target.exists())


if __name__ == "__main__":
    unittest.main()
