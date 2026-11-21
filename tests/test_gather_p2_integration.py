"""Integration Gather Phase 2 qua CLI headless (cá bơi + quái, determinism, inventory).

Gọi `chonoi.headless.main(argv)` trong tiến trình: cùng đường đi với CLI.
Scenario cho CLI phải bọc {"gather": {...}}.
Kiểm: gather --inventory-out có ca_keo -> quan --inventory đọc được;
cùng seed byte-identical với cá bơi + quái; docs/proof/phase-2/integration.*.

Chạy: PYTHONPATH=tests;. python -m unittest tests.test_gather_p2_integration -v
"""

import contextlib
import io
import json
import os
import unittest

from chonoi.contract import load_contract
from chonoi.headless import main as headless_main

from helpers import Workdir, events, frames, read_jsonl, snapshots, write_json

TUNING = load_contract()["tuning"]
G = TUNING["gather"]
DOCK = G["dock_pos"]
TICK = TUNING["tick_hz"]


def run(*argv):
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        code = headless_main([str(a) for a in argv])
    return code, err.getvalue()


class IntegrationP2(unittest.TestCase):
    """Integration P2: cá bơi, quái, nâng cấp, inventory."""

    def test_IP1_fish_swim_determinism_byte_identical(self):
        """Cùng seed, cùng input: JSONL byte-identical. Cá bơi + quái."""
        with Workdir() as w:
            # Scenario với random_fish=true (cá bơi) + quái mặc định
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [20, 5], "vel": [0, 0]},
                "nodes": [], "random_fish": True,
            }})
            # Không input -> chỉ đứng yên
            outs = []
            for i in range(2):
                code, err = run("--mode", "gather", "--seed", 42, "--ticks", 400,
                                "--scenario", sc, "--out", w.path(f"g{i}.jsonl"),
                                "--snapshot-every", 50)
                self.assertEqual(code, 0, err)
                with open(w.path(f"g{i}.jsonl"), "rb") as f:
                    outs.append(f.read())
            self.assertEqual(outs[0], outs[1], "Cùng seed phải byte-identical")

    def test_IP2_fish_swim_snapshot_contains_moving_fish(self):
        """Snapshot sau vài trăm tick phải cho thấy cá di chuyển (pos khác tick 0)."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [2, 0], "vel": [0, 0]},
                "nodes": [], "random_fish": True,
            }})
            code, err = run("--mode", "gather", "--seed", 7, "--ticks", 300,
                            "--scenario", sc, "--out", w.path("g.jsonl"),
                            "--snapshot-every", 100)
            self.assertEqual(code, 0, err)
            snaps = snapshots(read_jsonl(w.path("g.jsonl")))
            self.assertGreaterEqual(len(snaps), 2)
            fish_t0 = {f["id"]: f["pos"] for f in snaps[0]["fish"]}
            fish_last = {f["id"]: f["pos"] for f in snaps[-1]["fish"]}
            # Ít nhất 1 con cá có vị trí khác (gần như chắc chắn với 300 ticks)
            moved = any(fish_t0.get(fid) != fish_last.get(fid) for fid in fish_t0
                        if fid in fish_last)
            self.assertTrue(moved, "Phải có ít nhất 1 con cá di chuyển sau 300 ticks")

    def test_IP3_gather_with_ca_keo_inventory_to_quan(self):
        """gather --inventory-out có ca_keo -> quan --inventory đọc được."""
        with Workdir() as w:
            # Đặt cá kèo gần bến để bắt rồi cập bến
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [DOCK[0], 1], "vel": [0, 0]},
                "hold": ["keo_neo"],
                "nodes": [], "random_fish": False,
                "fish": [{"id": "F1", "kind": "ca_keo", "pos": [DOCK[0] + 1, 1]}],
            }})
            inp = write_json(w.path("in.json"),
                             frames({"tick": 0, "catch": True}, {"tick": 2, "interact": True}))
            inv = w.path("inv.json")
            code, err = run("--mode", "gather", "--seed", 1, "--ticks", 100,
                            "--scenario", sc, "--inputs", inp,
                            "--out", w.path("g.jsonl"), "--inventory-out", inv)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("g.jsonl"))
            end = events(rows, "gather_end")
            self.assertEqual(len(end), 1)
            self.assertEqual(end[0]["data"]["reason"], "docked")
            # Kho phải có ca_keo
            with open(inv, encoding="utf-8") as f:
                inv_data = json.load(f)
            self.assertIn("ca_keo", inv_data["items"])
            self.assertEqual(inv_data["items"]["ca_keo"], G["fish_yield"]["ca_keo"])
            # Keo_neo cũng phải có
            self.assertIn("keo_neo", inv_data["items"])
            # Chạy quan với inventory
            code, err = run("--mode", "quan", "--seed", 1, "--ticks", 0,
                            "--inventory", inv, "--out", w.path("q.jsonl"))
            self.assertEqual(code, 0, err)
            stock = snapshots(read_jsonl(w.path("q.jsonl")))[0]["stock"]
            self.assertEqual(stock.get("ca_keo", 0), G["fish_yield"]["ca_keo"])

    def test_IP4_monsters_appear_in_snapshot(self):
        """Snapshot gather mặc định phải có monsters."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [2, 0], "vel": [0, 0]},
                "nodes": [], "random_fish": True,
            }})
            code, err = run("--mode", "gather", "--seed", 1, "--ticks", 10,
                            "--scenario", sc, "--out", w.path("g.jsonl"),
                            "--snapshot-every", 5)
            self.assertEqual(code, 0, err)
            snaps = snapshots(read_jsonl(w.path("g.jsonl")))
            self.assertGreaterEqual(len(snaps), 1)
            self.assertIn("monsters", snaps[0])
            # Day 1 -> chỉ M1
            monster_ids = [m["id"] for m in snaps[0]["monsters"]]
            self.assertIn("M1", monster_ids)

    def test_IP5_different_seed_different_fish(self):
        """Seed khác -> cá spawn khác."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [2, 0], "vel": [0, 0]},
                "nodes": [], "random_fish": True,
            }})
            outputs = {}
            for seed in (1, 99):
                code, err = run("--mode", "gather", "--seed", seed, "--ticks", 10,
                                "--scenario", sc, "--out", w.path(f"g{seed}.jsonl"),
                                "--snapshot-every", 5)
                self.assertEqual(code, 0, err)
                snaps = snapshots(read_jsonl(w.path(f"g{seed}.jsonl")))
                outputs[seed] = [(f["id"], f["kind"], f["pos"]) for f in snaps[0]["fish"]]
            self.assertNotEqual(outputs[1], outputs[99],
                                "Seed khác phải cho cá spawn khác")


class ScenarioValidationCLI(unittest.TestCase):
    """Scenario không hợp lệ -> mã thoát 2."""

    def test_SP1_monster_bad_kind_exit_2(self):
        """Quái loài lạ -> mã 2."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [20, 5]},
                "nodes": [], "random_fish": False,
                "monsters": [{"id": "M1", "kind": "rong_bien", "pos": [60, 20],
                              "waypoints": [[60, 20], [64, 20]]}],
            }})
            code, err = run("--mode", "gather", "--seed", 1, "--ticks", 10,
                            "--scenario", sc, "--out", w.path("g.jsonl"))
            self.assertEqual(code, 2)

    def test_SP2_monster_recoil_no_timer_exit_2(self):
        """monster recoil, timer=0 -> mã 2."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [20, 5]},
                "nodes": [], "random_fish": False,
                "monsters": [{"id": "M1", "kind": "ca_sau", "pos": [60, 20],
                              "waypoints": [[60, 20], [64, 20]],
                              "state": "recoil", "state_ticks_left": 0,
                              "recoil_dir": [1.0, 0.0]}],
            }})
            code, err = run("--mode", "gather", "--seed", 1, "--ticks", 10,
                            "--scenario", sc, "--out", w.path("g.jsonl"))
            self.assertEqual(code, 2)

    def test_SP3_fish_negative_age_exit_2(self):
        """fish age_ticks âm -> mã 2."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [20, 5]},
                "nodes": [], "random_fish": True,
                "fish": [{"id": "F1", "kind": "ca_loc", "pos": [50, 15],
                          "age_ticks": -1}],
            }})
            code, err = run("--mode", "gather", "--seed", 1, "--ticks", 10,
                            "--scenario", sc, "--out", w.path("g.jsonl"))
            self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
