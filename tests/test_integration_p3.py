"""Cross-phase checks using the v1.2 runtime before switching the manifest."""

from copy import deepcopy
import json
import tempfile
import unittest
from pathlib import Path

from chonoi.contract import load_contract
from chonoi.day import DaySession
from chonoi.errors import BadInput
from chonoi.inputs import InputPlayer
from chonoi.inventory import read_inventory
from chonoi.runner import Session
from chonoi.scenario_day import load_day_scenario
from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


def v12_tuning():
    tuning = deepcopy(load_contract()["tuning"])
    tuning["_contract_version"] = "1.2"
    return tuning


def fixture(fresh=100):
    return {"hold": [{"id": "I1", "kind": "ca_linh", "fresh": fresh}],
            "random_fish": False, "monsters": []}


class Phase3Integration(unittest.TestCase):
    def test_day_rejects_over_capacity_hold_before_output(self):
        tuning = v12_tuning()
        hold = [{"id": f"I{i}", "kind": "ca_linh", "fresh": 100}
                for i in range(1, tuning["gather"]["hold_capacity"] + 2)]
        with Workdir() as work:
            path = write_json(work.path("day.json"), {"gather": {"hold": hold}})
            with self.assertRaises(BadInput):
                load_day_scenario(path, tuning, 1)

    def test_headless_file_handoff_and_count_file_rejected(self):
        with Workdir() as work:
            scenario = write_json(work.path("gather.json"), {"gather": fixture()})
            inputs = write_json(work.path("inputs.json"), frames({"tick": 0, "interact": True}))
            inventory, gather_out, quan_out = (work.path(name) for name in
                                               ("stock.json", "gather.jsonl", "quan.jsonl"))
            code, error = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1",
                                       "--scenario", scenario, "--inputs", inputs,
                                       "--inventory-out", inventory, "--out", gather_out)
            self.assertEqual(code, 0, error)
            saved = json.loads(Path(inventory).read_text())
            self.assertEqual(saved, events(read_jsonl(gather_out), "gather_end")[0]
                             ["data"]["inventory"])
            code, error = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                       "--inventory", inventory, "--out", quan_out)
            self.assertEqual(code, 0, error)
            self.assertEqual(snapshots(read_jsonl(quan_out))[0]["stock"], saved["items"])

            old = write_json(work.path("count.json"), {"items": {"ca_linh": 1}})
            rejected = work.path("rejected.jsonl")
            code, _ = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                    "--inventory", old, "--out", rejected)
            self.assertEqual(code, 2)
            self.assertFalse(Path(rejected).exists())

    def test_threshold_30_spoils_on_first_gather_tick(self):
        session = Session("gather", v12_tuning(), fixture(30), 1,
                          contract_version="1.2")
        events = session.step(InputPlayer([]).advance(0))
        spoiled = [row for row in events if row["name"] == "spoiled"]
        self.assertEqual(spoiled, [{"type": "event", "tick": 1,
                                    "phase": "gather", "name": "spoiled",
                                    "data": {"item_id": "I1", "kind": "ca_linh",
                                             "location": "hold"}}])
        self.assertLess(session.snapshot()["hold"][0]["fresh"], 30)

    def test_file_handoff_keeps_gather_decay_and_identity(self):
        tuning = v12_tuning()
        session = Session("gather", tuning, fixture(), 1,
                          contract_version="1.2")
        events = session.step(InputPlayer([{"tick": 0, "interact": True}]).advance(0))
        self.assertTrue(session.done)
        item = events[-1]["data"]["inventory"]["items"][0]
        self.assertEqual(item["id"], "I1")
        self.assertEqual(item["kind"], "ca_linh")
        self.assertLess(item["fresh"], 100)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "stock.json"
            session.write_inventory_if_done(str(path))
            saved = json.loads(path.read_text())
            self.assertEqual(saved, {"items": [item]})
            stock = read_inventory(str(path), contract_version="1.2")
            quan = Session("quan", tuning, {"random_customers": False}, 1,
                           inventory=stock, contract_version="1.2")
            self.assertEqual(quan.snapshot()["stock"], [item])

    def test_day_handoff_does_not_decay_quan_on_transition_tick(self):
        tuning = v12_tuning()
        day = DaySession(tuning, {"gather": fixture(),
                                  "quan": {"random_customers": False}}, 1)
        events = day.step(InputPlayer([{"tick": 0, "interact": True}]).advance(0))
        ending = next(row for row in events if row["name"] == "gather_end")
        self.assertEqual(day.phase, "quan")
        self.assertEqual(day.snapshot()["stock"], ending["data"]["inventory"]["items"])
        self.assertEqual(day.phase_tick, 0)
        day.step(InputPlayer([]).advance(1))
        self.assertLess(day.snapshot()["stock"][0]["fresh"],
                        ending["data"]["inventory"]["items"][0]["fresh"])


if __name__ == "__main__":
    unittest.main()
