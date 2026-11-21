"""Integration Gather Phase 1 qua CLI headless (I1–I5 trong checklist QA Gather P1).

Gọi `chonoi.headless.main(argv)` trong tiến trình: cùng đường đi với CLI (đọc scenario/inputs, kiểm hợp lệ,
ghi JSONL và file kho) nhưng không phụ thuộc lệnh `python3` của máy (trên Windows có thể là stub WindowsApps).
Scenario cho CLI phải bọc {"gather": {...}}.
"""

import contextlib
import io
import json
import os
import unittest
from pathlib import Path

from helpers import Workdir, events, frames, read_jsonl, snapshots, write_json

from chonoi.contract import load_contract
from chonoi.headless import main as headless_main

G = load_contract()["tuning"]["gather"]
DOCK = G["dock_pos"]


def run(*argv):
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        code = headless_main([str(a) for a in argv])
    return code, err.getvalue()


def catch_then_dock(w):
    """Giỏ sẵn 1 bông súng; dưới nước trong vùng bến: bắt đàn cá linh F1 (tick 0) rồi cập bến (tick 2)."""
    sc = write_json(
        w.path("sc.json"),
        {
            "gather": {
                "player": {"pos": [DOCK[0], 1], "vel": [0, 0]},
                "hold": ["bong_sung"],
                "nodes": [],
                "random_fish": False,
                "fish": [{"id": "F1", "kind": "ca_linh", "pos": [DOCK[0] + 1, 1]}],
            }
        },
    )
    inp = write_json(
        w.path("in.json"),
        frames({"tick": 0, "catch": True}, {"tick": 2, "interact": True}),
    )
    return sc, inp


class Inventory(unittest.TestCase):
    def test_I1_inventory_out_matches_gather_end_and_loads_into_quan(self):
        with Workdir() as w:
            sc, inp = catch_then_dock(w)
            inv = w.path("inv.json")
            code, err = run(
                "--mode",
                "gather",
                "--seed",
                1,
                "--ticks",
                100,
                "--scenario",
                sc,
                "--inputs",
                inp,
                "--out",
                w.path("g.jsonl"),
                "--inventory-out",
                inv,
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("g.jsonl"))
            end = events(rows, "gather_end")
            self.assertEqual(len(end), 1)
            self.assertEqual(end[0]["data"]["reason"], "docked")
            expected = {"bong_sung": 1, "ca_linh": G["fish_yield"]["ca_linh"]}
            self.assertEqual(end[0]["data"]["inventory"], {"items": expected})
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), end[0]["data"]["inventory"])
            code, err = run(
                "--mode",
                "quan",
                "--seed",
                1,
                "--ticks",
                0,
                "--inventory",
                inv,
                "--out",
                w.path("q.jsonl"),
            )
            self.assertEqual(code, 0, err)
            stock = snapshots(read_jsonl(w.path("q.jsonl")))[0]["stock"]
            self.assertEqual({k: v for k, v in stock.items() if v}, expected)

    def test_I2_faint_overwrites_inventory_with_empty(self):
        with Workdir() as w:
            inv = write_json(w.path("inv.json"), {"items": {"ca_loc": 5}})
            sc = write_json(
                w.path("sc.json"),
                {
                    "gather": {
                        "player": {
                            "pos": [20, 5],
                            "oxygen_ticks": 0,
                            "zero_oxy_ticks": 59,
                            "hp": 1,
                        },
                        "hold": ["ca_loc", "ca_linh"],
                        "nodes": [],
                        "random_fish": False,
                    }
                },
            )
            code, err = run(
                "--mode",
                "gather",
                "--seed",
                1,
                "--ticks",
                100,
                "--scenario",
                sc,
                "--out",
                w.path("g.jsonl"),
                "--inventory-out",
                inv,
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("g.jsonl"))
            self.assertEqual(events(rows, "gather_end")[0]["data"]["reason"], "fainted")
            self.assertEqual(rows[-1]["reason"], "fainted")
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": {}})

    def test_I3_tick_limit_does_not_write_inventory(self):
        with Workdir() as w:
            sc = write_json(
                w.path("sc.json"),
                {
                    "gather": {
                        "player": {"pos": [20, 0]},
                        "hold": ["ca_loc"],
                        "nodes": [],
                        "random_fish": False,
                    }
                },
            )
            new_inv = w.path("new.json")
            code, err = run(
                "--mode",
                "gather",
                "--seed",
                1,
                "--ticks",
                5,
                "--scenario",
                sc,
                "--out",
                w.path("a.jsonl"),
                "--inventory-out",
                new_inv,
            )
            self.assertEqual(code, 0, err)
            self.assertEqual(read_jsonl(w.path("a.jsonl"))[-1]["reason"], "tick_limit")
            self.assertFalse(os.path.exists(new_inv))
            old_inv = write_json(w.path("old.json"), {"items": {"ca_linh": 9}})
            with open(old_inv, "rb") as f:
                before = f.read()
            code, err = run(
                "--mode",
                "gather",
                "--seed",
                1,
                "--ticks",
                5,
                "--scenario",
                sc,
                "--out",
                w.path("b.jsonl"),
                "--inventory-out",
                old_inv,
            )
            self.assertEqual(code, 0, err)
            with open(old_inv, "rb") as f:
                self.assertEqual(f.read(), before)


class Determinism(unittest.TestCase):
    def test_I4_same_inputs_byte_identical(self):
        with Workdir() as w:
            sc, inp = catch_then_dock(w)
            outs = []
            for i in range(2):
                code, err = run(
                    "--mode",
                    "gather",
                    "--seed",
                    7,
                    "--ticks",
                    100,
                    "--scenario",
                    sc,
                    "--inputs",
                    inp,
                    "--out",
                    w.path(f"g{i}.jsonl"),
                    "--inventory-out",
                    w.path(f"inv{i}.json"),
                )
                self.assertEqual(code, 0, err)
                with (
                    open(w.path(f"g{i}.jsonl"), "rb") as f1,
                    open(w.path(f"inv{i}.json"), "rb") as f2,
                ):
                    outs.append((f1.read(), f2.read()))
            self.assertEqual(outs[0], outs[1])

    def test_I5_default_six_static_schools(self):
        fixture = Path(__file__).resolve().parent / "fixtures/game.contract.v1_0.json"

        from chonoi.contract import load_contract
        from chonoi.inputs import InputState
        from chonoi.runner import Session

        contract = load_contract(fixture)
        tuning = contract["tuning"]

        session = Session("gather", tuning, {}, 1)
        expected = [
            (f["id"], f["kind"], [float(c) for c in f["pos"]])
            for f in tuning["gather"]["fish_initial"]
        ]

        self.assertEqual(len(expected), 6)

        for _ in range(300):
            got = [(f["id"], f["kind"], f["pos"]) for f in session.snapshot()["fish"]]
            self.assertEqual(got, expected)
            session.step(InputState(move=[0, 0], held={}, edges=set()))


if __name__ == "__main__":
    unittest.main()
