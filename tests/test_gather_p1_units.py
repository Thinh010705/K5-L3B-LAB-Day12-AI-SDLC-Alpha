"""Unit test luật Gather Phase 1 (chonoi/sim/gather.py) — QA.

Nguồn ca kiểm thử: checklist QA Gather P1 (O1–O9, G1–G7, C1–C9, E1–E5), PRD-0, Test Contract v1.0 C–G.
Dựng qua runner.Session + LiveInputs; scenario là nội dung khối gather (không bọc "gather").
Input bước k -> event tick k+1. Cạnh nhấn false -> true mới tạo hành động.
Mọi thông số đọc từ game.contract.json; các số trong docstring chỉ minh họa theo preset hiện tại.

Chạy: PYTHONPATH=tests:. python3 -m unittest tests.test_gather_p1_units -v
"""

import copy
import math
import unittest
from pathlib import Path

from chonoi.contract import load_contract
from chonoi.inputs import LiveInputs
from chonoi.runner import Session

# Regression lịch sử P1/P2: dùng manifest P2 đã khóa; fixture kho đếm của
# các ca này không còn hợp lệ với giao diện công khai v1.2.
TUNING = load_contract(Path(__file__).resolve().parents[1] /
                       "docs/contracts/game.contract.v1_1.proposed.json")["tuning"]
G = TUNING["gather"]
TICK = TUNING["tick_hz"]
OXY_MAX = int(round(G["oxygen_max_s"] * TICK))
REFILL = G["oxygen_refill_per_tick"]
CHOKE = G["choke_interval_ticks"]
CAP = G["hold_capacity"]
REGROW = int(round(G["regrow_s"] * TICK))
CATCH_CD = int(round(G["catch_cooldown_s"] * TICK))
SURF = G["surface_depth"]
IR = G["interact_radius"]
CR = G["catch_radius"]
DOCK = G["dock_pos"]
DR = G["dock_radius"]

FAR_SURFACE = [20, 0]       # xa bến, ở mặt nước
FAR_UNDER = [20, 5]         # xa bến, dưới nước


def scenario(pos=FAR_UNDER, hold=None, nodes=None, fish=None, **player):
    """Fixture cô lập: xa bến, vận tốc 0, không nút, không cá (trừ khi truyền vào)."""
    p = {"pos": list(pos), "vel": [0, 0]}
    p.update(player)
    sc = {"player": p, "nodes": nodes or [], "fish": fish or [], "random_fish": False}
    if hold is not None:
        sc["hold"] = list(hold)
    return sc


def node(id_, pos, kind="bong_sung", regrow_ticks=0):
    return {"id": id_, "kind": kind, "pos": list(pos), "regrow_ticks": regrow_ticks}


def fish(id_, pos, kind="ca_loc"):
    return {"id": id_, "kind": kind, "pos": list(pos)}


class Driver:
    """Bọc Session + LiveInputs. step() trả danh sách (name, data) của bước đó."""

    def __init__(self, sc, time_left_ticks=None):
        sc = copy.deepcopy(sc)
        if time_left_ticks is not None:
            sc["time_left_ticks"] = time_left_ticks
        self.sess = Session("gather", TUNING, sc, seed=1)
        self.li = LiveInputs()
        self.rows = []

    @property
    def sim(self):
        return self.sess.sim

    def step(self, move=(0, 0), interact=None, catch=None, tap=()):
        """interact/catch: đặt trạng thái giữ phím; tap: bấm-nhả giữa hai tick (vẫn tạo cạnh lên)."""
        btn = {k: v for k, v in (("interact", interact), ("catch", catch)) if v is not None}
        self.li.set(move=list(move), **btn)
        for b in tap:
            self.li.set(**{b: True})
            self.li.set(**{b: False})
        rows = self.sess.step(self.li.advance())
        self.rows.extend(rows)
        return [(r["name"], r["data"]) for r in rows]

    def release(self):
        return self.step(interact=False, catch=False)

    def snap(self):
        return self.sess.snapshot()


def names(evs):
    return [n for n, _ in evs]


def find(evs, name):
    hits = [d for n, d in evs if n == name]
    return hits


# ---------------------------------------------------------------------------
# 2. Oxy, lặn/nổi, ngạt
# ---------------------------------------------------------------------------
class Oxygen(unittest.TestCase):
    def test_O1_surface_refills(self):
        d = Driver(scenario(pos=[20, SURF], oxygen_ticks=10))
        evs = d.step()
        s = d.snap()["player"]
        self.assertEqual(s["oxygen_ticks"], 10 + REFILL)
        self.assertTrue(s["at_surface"])
        self.assertEqual(s["hp"], G["hp_max"])
        self.assertEqual(evs, [])

    def test_O2_refill_clamped_to_max(self):
        d = Driver(scenario(pos=[20, SURF], oxygen_ticks=OXY_MAX - 1))
        for _ in range(5):
            d.step()
            self.assertEqual(d.snap()["player"]["oxygen_ticks"], OXY_MAX)
        self.assertEqual(d.snap()["player"]["oxygen_max_ticks"], OXY_MAX)

    def test_O3_underwater_drains_one(self):
        d = Driver(scenario(pos=[20, 1], oxygen_ticks=10))
        evs = d.step()
        s = d.snap()["player"]
        self.assertEqual(s["oxygen_ticks"], 9)
        self.assertFalse(s["at_surface"])
        self.assertEqual(s["hp"], G["hp_max"])
        self.assertNotIn("oxygen_empty", names(evs))

    def test_O4_dive_crossing_threshold(self):
        d = Driver(scenario(pos=[20, SURF], oxygen_ticks=10))
        evs = d.step(move=(0, 1))
        pos = d.snap()["player"]["pos"]
        self.assertGreater(pos[1], SURF)
        self.assertEqual(find(evs, "dive"), [{"pos": pos}])
        self.assertEqual(d.snap()["player"]["oxygen_ticks"], 9)
        for _ in range(10):
            self.assertNotIn("dive", names(d.step(move=(0, 1))))

    def test_O5_surface_rescues_from_choke(self):
        d = Driver(scenario(pos=[20, SURF + 0.001], vel=[0, -G["swim_speed"]], oxygen_ticks=0,
                            zero_oxy_ticks=CHOKE - 1, hp=1))
        evs = d.step(move=(0, -1))
        s = d.snap()["player"]
        self.assertLessEqual(s["pos"][1], SURF)
        self.assertEqual(find(evs, "surface"), [{"pos": s["pos"]}])
        self.assertEqual(s["oxygen_ticks"], REFILL)
        self.assertEqual(s["zero_oxy_ticks"], 0)
        self.assertEqual(s["hp"], 1)
        self.assertNotIn("choke", names(evs))
        self.assertNotIn("faint", names(evs))
        self.assertFalse(d.sess.done)
        for _ in range(5):
            self.assertNotIn("surface", names(d.step()))

    def test_O6_oxygen_empty_once(self):
        d = Driver(scenario(oxygen_ticks=1, zero_oxy_ticks=0))
        evs = d.step()
        self.assertEqual(find(evs, "oxygen_empty"), [{"oxygen_ticks": 0}])
        self.assertEqual(d.snap()["player"]["zero_oxy_ticks"], 1)
        evs = d.step()
        self.assertEqual(d.snap()["player"]["oxygen_ticks"], 0)
        self.assertNotIn("oxygen_empty", names(evs))

    def test_O7_choke_cycle_exact(self):
        hp0 = min(3, G["hp_max"])
        d = Driver(scenario(oxygen_ticks=1, hp=hp0))
        all_evs = d.step()          # bước 1: cạn oxy, bộ đếm = 1
        for _ in range(CHOKE - 2):  # tới hết bước CHOKE-1
            all_evs += d.step()
        self.assertNotIn("choke", names(all_evs))
        self.assertEqual(d.snap()["player"]["hp"], hp0)
        self.assertEqual(d.snap()["player"]["zero_oxy_ticks"], CHOKE - 1)
        evs = d.step()              # bước CHOKE
        self.assertEqual(find(evs, "choke"), [{"hp": hp0 - 1}])
        self.assertEqual(d.snap()["player"]["zero_oxy_ticks"], 0)
        more = []
        for _ in range(CHOKE):
            more += d.step()
        self.assertEqual(find(more, "choke"), [{"hp": hp0 - 2}])
        self.assertEqual(d.snap()["player"]["hp"], hp0 - 2)

    def test_O8_faint_loses_hold(self):
        d = Driver(scenario(oxygen_ticks=0, zero_oxy_ticks=CHOKE - 1, hp=1,
                            hold=["ca_loc", "bong_sung", "ca_linh"]))
        evs = d.step()
        self.assertEqual(names(evs), ["choke", "faint", "gather_end"])
        self.assertEqual(evs[0][1], {"hp": 0})
        self.assertEqual(evs[1][1], {"cause": "choke", "lost": ["ca_linh", "bong_sung", "ca_loc"], "hp": 0})
        self.assertEqual(evs[2][1], {"reason": "fainted", "inventory": {"items": {}}})
        self.assertEqual(d.snap()["hold"], [])
        self.assertEqual(d.sess.end_row()["reason"], "fainted")

    def test_O9_faint_has_priority(self):
        # Trong bến, dưới nước, bước cuối của ca, nhấn cả interact + catch với cá trong tầm.
        pos = [DOCK[0], 1]
        d = Driver(scenario(pos=pos, oxygen_ticks=0, zero_oxy_ticks=CHOKE - 1, hp=1,
                            fish=[fish("F1", [pos[0] + 1, 1])]), time_left_ticks=1)
        evs = d.step(interact=True, catch=True)
        self.assertEqual(names(evs), ["choke", "faint", "gather_end"])
        self.assertEqual(evs[-1][1]["reason"], "fainted")
        self.assertNotIn("fish_caught", names(evs))
        self.assertEqual(d.sess.end_row()["reason"], "fainted")


# ---------------------------------------------------------------------------
# 3. Hái và giỏ
# ---------------------------------------------------------------------------
class Gathering(unittest.TestCase):
    def test_G1_gather_at_exact_radius(self):
        d = Driver(scenario(pos=FAR_SURFACE, hold=["ca_loc"],
                            nodes=[node("N1", [FAR_SURFACE[0] + IR, 0])]))
        evs = d.step(interact=True)
        self.assertEqual(find(evs, "gather"), [{"node_id": "N1", "kind": "bong_sung", "amount": G["node_yield"]}])
        s = d.snap()
        self.assertEqual(s["hold"], ["ca_loc"] + ["bong_sung"] * G["node_yield"])
        self.assertEqual(s["nodes"][0]["regrow_ticks"], REGROW)
        self.assertFalse(s["nodes"][0]["ready"])

    def test_G2_no_gather_when_out_of_range_not_ready_or_underwater(self):
        cases = {
            "ngoài bán kính": (FAR_SURFACE, node("N1", [FAR_SURFACE[0] + IR + 0.01, 0]), 0),
            "chưa ready": (FAR_SURFACE, node("N1", [FAR_SURFACE[0] + 1, 0], regrow_ticks=50), 49),
            "dưới nước": ([20, SURF + 0.1], node("N1", [20, 0]), 0),
        }
        for label, (pos, n, timer_after) in cases.items():
            with self.subTest(label):
                d = Driver(scenario(pos=pos, nodes=[n], oxygen_ticks=100))
                evs = d.step(interact=True)
                self.assertNotIn("gather", names(evs))
                self.assertNotIn("hold_full", names(evs))
                self.assertEqual(d.snap()["hold"], [])
                self.assertEqual(d.snap()["nodes"][0]["regrow_ticks"], timer_after)

    def test_G3_tie_break_by_numeric_id_and_nearest_wins(self):
        x = FAR_SURFACE[0]
        with self.subTest("bằng khoảng cách -> ID số nhỏ"):
            d = Driver(scenario(pos=FAR_SURFACE, nodes=[node("N10", [x - 1, 0]), node("N2", [x + 1, 0])]))
            self.assertEqual(find(d.step(interact=True), "gather")[0]["node_id"], "N2")
        with self.subTest("gần hơn thắng ID nhỏ"):
            d = Driver(scenario(pos=FAR_SURFACE, nodes=[node("N1", [x + IR, 0]), node("N5", [x + 0.5, 0])]))
            self.assertEqual(find(d.step(interact=True), "gather")[0]["node_id"], "N5")

    def test_G4_hold_full_on_gather(self):
        full = ["ca_loc"] * CAP
        d = Driver(scenario(pos=FAR_SURFACE, hold=full, nodes=[node("N1", [FAR_SURFACE[0] + 1, 0])]))
        evs = d.step(interact=True)
        self.assertEqual(find(evs, "hold_full"),
                         [{"action": "gather", "node_id": "N1", "required": G["node_yield"], "free": 0}])
        self.assertNotIn("gather", names(evs))
        s = d.snap()
        self.assertTrue(s["nodes"][0]["ready"])
        self.assertEqual(s["hold"], full)

    def test_G5_fill_last_slot(self):
        if G["node_yield"] != 1:
            self.skipTest("ca này viết cho node_yield = 1")
        old = ["ca_loc", "ca_linh", "bong_dien_dien"] * CAP
        old = old[:CAP - 1]
        d = Driver(scenario(pos=FAR_SURFACE, hold=old, nodes=[node("N1", [FAR_SURFACE[0] + 1, 0])]))
        evs = d.step(interact=True)
        self.assertEqual(len(find(evs, "gather")), 1)
        s = d.snap()
        self.assertEqual(s["hold_count"], CAP)
        self.assertEqual(s["hold"], old + ["bong_sung"])

    def test_G6_regrown_same_step_then_gather(self):
        with self.subTest("hồi rồi hái cùng bước"):
            d = Driver(scenario(pos=FAR_SURFACE, nodes=[node("N1", [FAR_SURFACE[0] + 1, 0], regrow_ticks=1)]))
            evs = d.step(interact=True)
            self.assertEqual(names(evs), ["node_regrown", "gather"])
            self.assertEqual(evs[0][1], {"node_id": "N1"})
        with self.subTest("nhiều nút hồi: theo sort_by_id"):
            far = [node("N10", [80, 0], regrow_ticks=1), node("N2", [60, 0], regrow_ticks=1),
                   node("N1", [70, 0], regrow_ticks=1)]
            d = Driver(scenario(pos=FAR_SURFACE, nodes=far))
            evs = d.step()
            self.assertEqual([x["node_id"] for x in find(evs, "node_regrown")], ["N1", "N2", "N10"])

    def test_G7_holding_interact_does_not_repeat(self):
        x = FAR_SURFACE[0]
        d = Driver(scenario(pos=FAR_SURFACE, nodes=[node("N1", [x + 0.5, 0]), node("N2", [x + 1, 0])]))
        evs = d.step(interact=True)
        self.assertEqual(find(evs, "gather")[0]["node_id"], "N1")
        for _ in range(10):  # vẫn giữ phím; N2 còn ready trong tầm nhưng không có cạnh mới
            self.assertNotIn("gather", names(d.step(interact=True)))
        d.release()
        self.assertEqual(find(d.step(interact=True), "gather")[0]["node_id"], "N2")


# ---------------------------------------------------------------------------
# 4. Bắt cá
# ---------------------------------------------------------------------------
class Catching(unittest.TestCase):
    def test_C1_catch_ca_loc(self):
        d = Driver(scenario(fish=[fish("F1", [FAR_UNDER[0] + CR, FAR_UNDER[1]])]))
        evs = d.step(catch=True)
        self.assertEqual(find(evs, "fish_caught"),
                         [{"fish_id": "F1", "kind": "ca_loc", "yield": G["fish_yield"]["ca_loc"]}])
        s = d.snap()
        self.assertEqual(s["hold"], ["ca_loc"] * G["fish_yield"]["ca_loc"])
        self.assertEqual(s["fish"], [])
        self.assertEqual(s["player"]["catch_cd_ticks"], CATCH_CD)

    def test_C2_catch_ca_linh_yield_appended(self):
        y = G["fish_yield"]["ca_linh"]
        d = Driver(scenario(hold=["bong_sung"], fish=[fish("F1", [21, 5], "ca_linh")]))
        evs = d.step(catch=True)
        self.assertEqual(find(evs, "fish_caught"), [{"fish_id": "F1", "kind": "ca_linh", "yield": y}])
        self.assertEqual(d.snap()["hold"], ["bong_sung"] + ["ca_linh"] * y)

    def test_C3_hold_full_nearest_school_only(self):
        y = G["fish_yield"]["ca_linh"]
        free = y - 1
        hold = ["bong_sung"] * (CAP - free)
        d = Driver(scenario(hold=hold, fish=[fish("F1", [20.5, 5], "ca_linh"), fish("F2", [20 + CR, 5], "ca_loc")]))
        evs = d.step(catch=True)
        self.assertEqual(names(evs), ["hold_full"])
        self.assertEqual(evs[0][1], {"action": "catch", "fish_id": "F1", "required": y, "free": free})
        s = d.snap()
        self.assertEqual([f["id"] for f in s["fish"]], ["F1", "F2"])
        self.assertEqual(s["hold"], hold)
        self.assertEqual(s["player"]["catch_cd_ticks"], 0)

    def test_C4_no_fish_in_range(self):
        d = Driver(scenario(fish=[fish("F1", [20 + CR + 1, 5])]))
        evs = d.step(catch=True)
        self.assertEqual(evs, [])
        self.assertEqual(d.snap()["player"]["catch_cd_ticks"], 0)

    def test_C5_catch_ignored_at_surface(self):
        d = Driver(scenario(pos=[20, SURF], fish=[fish("F1", [20, SURF + 1])]))
        evs = d.step(catch=True)
        self.assertNotIn("fish_caught", names(evs))
        self.assertNotIn("hold_full", names(evs))
        self.assertEqual(len(d.snap()["fish"]), 1)

    def test_C6_cooldown_blocks_then_allows(self):
        d = Driver(scenario(catch_cd_ticks=2, fish=[fish("F1", [21, 5])]))
        evs = d.step(catch=True)
        self.assertNotIn("fish_caught", names(evs))
        self.assertEqual(d.snap()["player"]["catch_cd_ticks"], 1)
        d.li.set(catch=False)
        evs = d.step(catch=True)  # đầu bước timer=1 -> giảm về 0 -> bắt được
        self.assertEqual(len(find(evs, "fish_caught")), 1)

    def test_C7_cooldown_boundary_t_plus_L(self):
        sc = scenario(fish=[fish("F1", [21, 5]), fish("F2", [21, 5])])
        with self.subTest("bấm-nhả mỗi tick"):
            d = Driver(sc)
            d.step(tap=("catch",))
            caught = [r for r in d.rows if r["name"] == "fish_caught"]
            t = caught[0]["tick"]
            while d.sess.tick < t + CATCH_CD:
                d.step(tap=("catch",))
            caught = [r for r in d.rows if r["name"] == "fish_caught"]
            self.assertEqual([r["tick"] for r in caught], [t, t + CATCH_CD])
            self.assertEqual([r["data"]["fish_id"] for r in caught], ["F1", "F2"])
        with self.subTest("giữ phím qua mốc không bắt lại"):
            d = Driver(sc)
            for _ in range(CATCH_CD * 3):
                d.step(catch=True)
            self.assertEqual(len([r for r in d.rows if r["name"] == "fish_caught"]), 1)

    def test_C8_tie_break_and_exact_radius(self):
        with self.subTest("F10 và F2 cùng khoảng cách -> F2"):
            d = Driver(scenario(fish=[fish("F10", [18, 5]), fish("F2", [22, 5])]))
            self.assertEqual(find(d.step(catch=True), "fish_caught")[0]["fish_id"], "F2")
        with self.subTest("đúng mép bán kính -> bắt"):
            d = Driver(scenario(fish=[fish("F1", [20 + CR, 5])]))
            self.assertEqual(len(find(d.step(catch=True), "fish_caught")), 1)
        with self.subTest("ngoài mép -> không bắt"):
            d = Driver(scenario(fish=[fish("F1", [20 + CR + 0.01, 5])]))
            self.assertEqual(d.step(catch=True), [])

    def test_C9_interact_and_catch_same_tick(self):
        with self.subTest("trong bến, dưới nước: docked, không bắt cá"):
            pos = [DOCK[0], 1]
            d = Driver(scenario(pos=pos, fish=[fish("F1", [pos[0] + 1, 1])]))
            evs = d.step(interact=True, catch=True)
            self.assertEqual(names(evs), ["gather_end"])
            self.assertEqual(evs[0][1]["reason"], "docked")
            self.assertEqual(len(d.snap()["fish"]), 1)
        with self.subTest("ngoài bến: interact bỏ qua, catch vẫn xử lý"):
            d = Driver(scenario(fish=[fish("F1", [21, 5])]))
            evs = d.step(interact=True, catch=True)
            self.assertEqual(names(evs), ["fish_caught"])
            self.assertFalse(d.sess.done)


# ---------------------------------------------------------------------------
# 5. Kết thúc và kho
# ---------------------------------------------------------------------------
class Ending(unittest.TestCase):
    def test_E1_dock_at_exact_radius_beats_gather(self):
        pos = [DOCK[0] + DR, 0]
        d = Driver(scenario(pos=pos, hold=["ca_loc", "bong_sung"], nodes=[node("N1", [pos[0] + 1, 0])]))
        evs = d.step(interact=True)
        self.assertEqual(names(evs), ["gather_end"])
        self.assertEqual(evs[0][1], {"reason": "docked", "inventory": {"items": {"bong_sung": 1, "ca_loc": 1}}})
        self.assertEqual(d.snap()["hold"], ["ca_loc", "bong_sung"])
        self.assertEqual(d.sess.end_row()["reason"], "docked")

    def test_E2_last_tick_action_before_time_end(self):
        with self.subTest("bắt cá ở bước cuối"):
            d = Driver(scenario(fish=[fish("F1", [21, 5])]), time_left_ticks=1)
            evs = d.step(catch=True)
            self.assertEqual(names(evs), ["fish_caught", "gather_end"])
            self.assertEqual(evs[1][1], {"reason": "time",
                                         "inventory": {"items": {"ca_loc": G["fish_yield"]["ca_loc"]}}})
        with self.subTest("hái ở bước cuối"):
            d = Driver(scenario(pos=FAR_SURFACE, nodes=[node("N1", [21, 0])]), time_left_ticks=1)
            evs = d.step(interact=True)
            self.assertEqual(names(evs), ["gather", "gather_end"])
            self.assertEqual(evs[1][1], {"reason": "time",
                                         "inventory": {"items": {"bong_sung": G["node_yield"]}}})

    def test_E3_last_tick_dock_is_docked(self):
        d = Driver(scenario(pos=DOCK), time_left_ticks=1)
        evs = d.step(interact=True)
        self.assertEqual(names(evs), ["gather_end"])
        self.assertEqual(evs[0][1]["reason"], "docked")

    def test_E4_time_out_underwater_keeps_hold(self):
        d = Driver(scenario(hold=["ca_linh", "ca_loc"], oxygen_ticks=100), time_left_ticks=1)
        evs = d.step()
        self.assertEqual(evs, [("gather_end", {"reason": "time",
                                               "inventory": {"items": {"ca_linh": 1, "ca_loc": 1}}})])
        self.assertEqual(d.snap()["hold"], ["ca_linh", "ca_loc"])
        self.assertEqual(d.snap()["player"]["hp"], G["hp_max"])

    def test_E5_step_after_done_is_noop(self):
        d = Driver(scenario(pos=DOCK, fish=[fish("F1", [DOCK[0], 1])]))
        d.step(interact=True)
        self.assertTrue(d.sess.done)
        before = copy.deepcopy(d.sim.snapshot())
        tl = d.sim.time_left_ticks
        d.release()
        evs = d.step(move=(1, 1), interact=True, catch=True)
        self.assertEqual(evs, [])
        self.assertEqual(d.sim.snapshot(), before)
        self.assertEqual(d.sim.time_left_ticks, tl)


class Sanity(unittest.TestCase):
    def test_fixture_constants_from_contract(self):
        # bảo đảm fixture không mâu thuẫn với contract (nếu contract đổi, ca vẫn có ý nghĩa)
        self.assertGreater(FAR_UNDER[1], SURF)
        self.assertLessEqual(FAR_SURFACE[1], SURF)
        self.assertGreater(math.dist(FAR_UNDER, DOCK), DR + IR + CR)
        self.assertGreaterEqual(G["fish_yield"]["ca_linh"], 2)  # C3 cần free >= 1
        self.assertGreater(CATCH_CD, 1)


if __name__ == "__main__":
    unittest.main()
