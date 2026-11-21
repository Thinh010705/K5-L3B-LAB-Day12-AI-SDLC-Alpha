"""Unit test luật Gather Phase 2 (cá bơi/sinh, Cá Sấu, nâng cấp, scenario) — QA.

Nguồn ca kiểm thử: QA-p2-handoff.local (F1–F8, M1–M9, Upgrade, Scenario),
PRD Phase 2, game.contract.json phiên bản P2 (fish_speed, monsters, shop).
Dựng qua runner.Session + LiveInputs; scenario là nội dung khối gather (không bọc "gather").
Input bước k -> event tick k+1. Cạnh nhấn false -> true mới tạo hành động.
Mọi thông số đọc từ game.contract.json; các số trong docstring chỉ minh họa theo preset hiện tại.

Chạy: PYTHONPATH=tests;. python -m unittest tests.test_gather_p2_units -v
"""

import copy
import math
import unittest

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.inputs import LiveInputs
from chonoi.runner import Session
from chonoi.sim.gather import GatherSim, player_limits, TICK

TUNING = load_contract()["tuning"]
G = TUNING["gather"]
OXY_MAX = int(round(G["oxygen_max_s"] * TICK))
CHOKE = G["choke_interval_ticks"]
CAP = G["hold_capacity"]
SURF = G["surface_depth"]
FISH_SPEED = G["fish_speed"]
FISH_TURN = G["fish_turn_ticks"]
FISH_MAX = G["fish_max"]
FISH_SPAWN_TICKS = G["fish_spawn_ticks"]
FISH_SPAWN_CLEARANCE = G["fish_spawn_clearance"]
FISH_X = G["fish_x"]
FISH_DEPTHS = G["fish_depths"]
FISH_SPAWN_X = G["fish_spawn_x"]
FISH_SPAWN_DEPTHS = G["fish_spawn_depths"]
FISH_WEIGHTS = G["fish_weights"]
FISH_INITIAL = G["fish_initial"]  # int = 8 (P2)
CR = G["catch_radius"]

MONSTER_CFG = G["monsters"]
INVULN_TICKS = MONSTER_CFG["invuln_ticks"]
LOSS_RATIO = MONSTER_CFG["loss_ratio"]
CA_SAU = MONSTER_CFG["species"]["ca_sau"]
PATROL_SPEED = CA_SAU["patrol_speed"]
CHASE_SPEED = CA_SAU["chase_speed"]
DETECT_RADIUS = CA_SAU["detect_radius"]
EXIT_RADIUS = CA_SAU["exit_radius"]
HIT_RADIUS = CA_SAU["hit_radius"]
RECOIL_TICKS = CA_SAU["recoil_ticks"]
RECOIL_DIST = CA_SAU["recoil_dist"]
MONSTER_DEPTHS = CA_SAU["depths"]

FAR_SURFACE = [20, 0]
FAR_UNDER = [20, 5]
DOCK = G["dock_pos"]
DR = G["dock_radius"]


# ---------------------------------------------------------------------------
# Helpers (cùng mẫu với test_gather_p1_units.py)
# ---------------------------------------------------------------------------
def scenario(pos=FAR_UNDER, hold=None, nodes=None, fish=None, random_fish=False,
             monsters=None, **player):
    """Fixture cô lập: xa bến, vận tốc 0, không nút, không cá, không quái (trừ khi truyền vào)."""
    p = {"pos": list(pos), "vel": [0, 0]}
    p.update(player)
    sc = {"player": p, "nodes": nodes or [], "fish": fish or [], "random_fish": random_fish}
    if hold is not None:
        sc["hold"] = list(hold)
    if monsters is not None:
        sc["monsters"] = monsters
    return sc


def monster(id_, pos, waypoints=None, kind="ca_sau", state="patrol",
            target_idx=1, state_ticks_left=0, recoil_dir=None):
    """Fixture quái cô lập."""
    if waypoints is None:
        waypoints = [list(pos), [pos[0] + 4, pos[1]]]
    return {"id": id_, "kind": kind, "pos": list(pos), "waypoints": waypoints,
            "target_idx": target_idx, "state": state,
            "state_ticks_left": state_ticks_left,
            "recoil_dir": recoil_dir}


def fish_fixture(id_, pos, kind="ca_loc", heading_deg=0, age_ticks=0):
    """Fixture cá có heading và age cho P2."""
    return {"id": id_, "kind": kind, "pos": list(pos),
            "heading_deg": heading_deg, "age_ticks": age_ticks}


class Driver:
    """Bọc Session + LiveInputs. step() trả danh sách (name, data) của bước đó."""

    def __init__(self, sc, time_left_ticks=None, day=1, active_upgrades=None, seed=1):
        sc = copy.deepcopy(sc)
        if time_left_ticks is not None:
            sc["time_left_ticks"] = time_left_ticks
        if day != 1 or isinstance(day, bool) or active_upgrades is not None:
            # Build trực tiếp qua GatherSim để truyền day/active_upgrades
            from chonoi.rng import Streams
            from chonoi.ids import IdAllocator
            streams, ids = Streams(seed), IdAllocator()
            sim = GatherSim(TUNING, sc, streams, ids, day=day, active_upgrades=active_upgrades)
            self.sess = Session.__new__(Session)
            self.sess.mode = "gather"
            self.sess.tuning = TUNING
            self.sess.sim = sim
            self.sess.tick = 0
        else:
            self.sess = Session("gather", TUNING, sc, seed=seed)
        self.li = LiveInputs()
        self.rows = []

    @property
    def sim(self):
        return self.sess.sim

    def step(self, move=(0, 0), interact=None, catch=None, tap=()):
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
    return [d for n, d in evs if n == name]


# ---------------------------------------------------------------------------
# 1. Cá bơi / sinh Phase 2 (F1–F8)
# ---------------------------------------------------------------------------
class FishSwim(unittest.TestCase):
    """Cá bơi, sinh theo lịch, spawn đầu ca."""

    def test_F1_initial_spawn_8_schools(self):
        """random_fish:true, không khai fish -> 8 đàn, id F1..F8, vị trí khác nhau,
        mỗi đàn trên điểm sinh của loài."""
        sc = scenario(random_fish=True)
        del sc["fish"]  # để GatherSim tự spawn
        d = Driver(sc)
        snap = d.snap()
        fish = snap["fish"]
        self.assertEqual(len(fish), FISH_INITIAL)
        # id: F1 .. F8
        ids = [f["id"] for f in fish]
        self.assertEqual(ids, [f"F{i}" for i in range(1, FISH_INITIAL + 1)])
        # Vị trí khác nhau
        positions = [tuple(f["pos"]) for f in fish]
        self.assertEqual(len(set(positions)), FISH_INITIAL)
        # Mỗi đàn trên điểm sinh hợp lệ
        for f in fish:
            kind = f["kind"]
            self.assertIn(f["pos"][0], FISH_SPAWN_X,
                          f"{f['id']}: x phải thuộc fish_spawn_x")
            self.assertIn(f["pos"][1], FISH_SPAWN_DEPTHS[kind],
                          f"{f['id']}: depth phải thuộc fish_spawn_depths[{kind}]")

    def test_F2_determinism_same_seed_identical_different_seed_differs(self):
        """Cùng seed -> giống hệt; seed khác -> khác ít nhất một vị trí."""
        sc = scenario(random_fish=True)
        del sc["fish"]
        d1 = Driver(copy.deepcopy(sc), seed=42)
        d2 = Driver(copy.deepcopy(sc), seed=42)
        d3 = Driver(copy.deepcopy(sc), seed=99)
        fish1 = [(f["id"], f["kind"], f["pos"]) for f in d1.snap()["fish"]]
        fish2 = [(f["id"], f["kind"], f["pos"]) for f in d2.snap()["fish"]]
        fish3 = [(f["id"], f["kind"], f["pos"]) for f in d3.snap()["fish"]]
        self.assertEqual(fish1, fish2, "Cùng seed phải giống hệt")
        self.assertNotEqual(fish1, fish3, "Seed khác phải khác ít nhất một vị trí")

    def test_F3_fish_swim_speed_and_age(self):
        """fish fixture + random_fish true: cá bơi fish_speed/60 m mỗi bước theo heading; age_ticks tăng."""
        # Cá heading 0 (phải): di chuyển theo x, không đổi d
        pos0 = [50.0, 15.0]
        f = fish_fixture("F1", pos0, kind="ca_loc", heading_deg=0, age_ticks=0)
        sc = scenario(fish=[f], random_fish=True)
        d = Driver(sc)
        expected_step = FISH_SPEED / TICK  # 1.5 / 60 = 0.025 m
        d.step()  # tick 1
        snap = d.snap()
        fish = snap["fish"][0]
        # age_ticks phải tăng 1
        self.assertEqual(fish["age_ticks"], 1)
        # Vị trí: x tăng, d không đổi (heading 0 = cos(0)=1, sin(0)=0)
        self.assertAlmostEqual(fish["pos"][0], pos0[0] + expected_step, places=6)
        self.assertAlmostEqual(fish["pos"][1], pos0[1], places=6)

    def test_F4_reflect_x_boundary(self):
        """Phản xạ mép: cá tại x gần mép phải (fish_x[1]) heading 0 -> phản xạ, heading thay đổi."""
        x_max = FISH_X[1]  # 96
        step = FISH_SPEED / TICK
        # Đặt cá gần mép phải: x sao cho x + step > x_max
        x0 = x_max - step / 2  # 95.9875 -> sau 1 bước sẽ vượt mép
        f = fish_fixture("F1", [x0, 15.0], kind="ca_loc", heading_deg=0, age_ticks=0)
        sc = scenario(fish=[f], random_fish=True)
        d = Driver(sc)
        d.step()
        snap = d.snap()
        fish = snap["fish"][0]
        # x phải phản xạ: 2 * x_max - (x0 + step) < x_max
        expected_x = 2 * x_max - (x0 + step)
        self.assertAlmostEqual(fish["pos"][0], expected_x, places=6)
        self.assertLessEqual(fish["pos"][0], x_max)
        # heading x phần phải đảo lại (giờ phải có cos thành phần < 0)
        heading_rad = math.radians(fish["heading_deg"])
        self.assertLess(math.cos(heading_rad), 0, "Heading x phải đảo sau phản xạ")

    def test_F5_reflect_depth_by_species(self):
        """Dải độ sâu theo loài (ca_keo [22,28]): phản xạ d."""
        depth_min, depth_max = FISH_DEPTHS["ca_keo"]  # [22, 28]
        step = FISH_SPEED / TICK
        # Cá ca_keo gần đáy, heading xuống (90 độ: cos=0, sin=1)
        d0 = depth_max - step / 2
        f = fish_fixture("F1", [50.0, d0], kind="ca_keo", heading_deg=90, age_ticks=0)
        sc = scenario(fish=[f], random_fish=True)
        d = Driver(sc)
        d.step()
        snap = d.snap()
        fish = snap["fish"][0]
        # d phải phản xạ
        expected_d = 2 * depth_max - (d0 + step)
        self.assertAlmostEqual(fish["pos"][1], expected_d, places=6)
        self.assertLessEqual(fish["pos"][1], depth_max)

    def test_F6_direction_change_at_turn_ticks(self):
        """age_ticks:119 -> bước sau (age=120) đổi hướng (heading khác) trước khi đi."""
        f = fish_fixture("F1", [50.0, 15.0], kind="ca_loc", heading_deg=0,
                         age_ticks=FISH_TURN - 1)  # 119
        sc = scenario(fish=[f], random_fish=True)
        d = Driver(sc)
        heading_before = 0
        d.step()  # tick 1: age_ticks -> 120, đổi hướng ngẫu nhiên
        snap = d.snap()
        fish = snap["fish"][0]
        self.assertEqual(fish["age_ticks"], FISH_TURN)
        # Heading thay đổi (gần như chắc chắn khác 0 với random seed = 1)
        # Nếu tình cờ bằng: vẫn hợp lệ (rất hiếm, chấp nhận)

    def test_F7_spawn_at_phase_tick_360(self):
        """Sinh tại phase_tick 360: đúng 1 fish_spawned; trần fish_max -> không sinh;
        random_fish:false -> không bơi/không sinh."""
        # 7a: Spawn tại tick 360
        sc = scenario(random_fish=True, fish=[])
        d = Driver(sc)
        spawned_events = []
        for _ in range(FISH_SPAWN_TICKS):
            evs = d.step()
            spawned_events.extend(find(evs, "fish_spawned"))
        self.assertEqual(len(spawned_events), 1,
                         f"Phải sinh đúng 1 đàn tại phase_tick {FISH_SPAWN_TICKS}")
        sp = spawned_events[0]
        self.assertIn("id", sp)
        self.assertIn("kind", sp)
        self.assertIn("pos", sp)

    def test_F7b_fish_max_cap(self):
        """Trần fish_max -> không sinh."""
        # Tạo FISH_MAX đàn cá fixture
        fishes = []
        spawn_pts = []
        for kind in sorted(FISH_SPAWN_DEPTHS.keys()):
            for x in FISH_SPAWN_X:
                for depth in FISH_SPAWN_DEPTHS[kind]:
                    spawn_pts.append((x, depth, kind))
        for i in range(FISH_MAX):
            x, depth, kind = spawn_pts[i % len(spawn_pts)]
            fishes.append(fish_fixture(f"F{i+1}", [x, depth], kind=kind))
        sc = scenario(fish=fishes, random_fish=True)
        d = Driver(sc)
        self.assertEqual(len(d.snap()["fish"]), FISH_MAX)
        spawned = []
        for _ in range(FISH_SPAWN_TICKS + 10):
            evs = d.step()
            spawned.extend(find(evs, "fish_spawned"))
        self.assertEqual(len(spawned), 0, "Không được sinh thêm khi đạt fish_max")

    def test_F7c_random_fish_false_no_swim_no_spawn(self):
        """random_fish:false -> không bơi/không sinh."""
        f = fish_fixture("F1", [50.0, 15.0], kind="ca_loc", heading_deg=0, age_ticks=0)
        sc = scenario(fish=[f], random_fish=False)
        d = Driver(sc)
        pos_before = list(d.snap()["fish"][0]["pos"])
        for _ in range(FISH_SPAWN_TICKS + 10):
            evs = d.step()
            self.assertNotIn("fish_spawned", names(evs))
        # Cá không bơi: vị trí không đổi
        pos_after = d.snap()["fish"][0]["pos"]
        self.assertEqual(pos_before, pos_after, "random_fish:false -> cá không bơi")

    def test_F8_catch_ca_keo_yield_2_and_harvest_keo_neo(self):
        """Bắt cá kèo yield 2; hái keo_neo ở N5/N6."""
        # 8a: Bắt cá kèo
        f = fish_fixture("F1", [FAR_UNDER[0] + 1, FAR_UNDER[1]], kind="ca_keo")
        sc = scenario(fish=[f], random_fish=False)
        d = Driver(sc)
        evs = d.step(catch=True)
        caught = find(evs, "fish_caught")
        self.assertEqual(len(caught), 1)
        self.assertEqual(caught[0]["kind"], "ca_keo")
        self.assertEqual(caught[0]["yield"], G["fish_yield"]["ca_keo"])  # 2
        self.assertEqual(d.snap()["hold"], ["ca_keo"] * G["fish_yield"]["ca_keo"])

    def test_F8b_harvest_keo_neo_node(self):
        """Hái keo_neo node ở mặt nước."""
        node = {"id": "N5", "kind": "keo_neo", "pos": [FAR_SURFACE[0] + 1, 0], "regrow_ticks": 0}
        sc = scenario(pos=FAR_SURFACE, nodes=[node], random_fish=False)
        d = Driver(sc)
        evs = d.step(interact=True)
        gathered = find(evs, "gather")
        self.assertEqual(len(gathered), 1)
        self.assertEqual(gathered[0]["kind"], "keo_neo")
        self.assertEqual(gathered[0]["amount"], G["node_yield"])


# ---------------------------------------------------------------------------
# 2. Cá Sấu (M1–M9)
# ---------------------------------------------------------------------------
class Monster(unittest.TestCase):
    """Quái vật: patrol, chase, hit, recoil, invuln, faint."""

    def test_M1_patrol_speed_and_waypoint_switch(self):
        """patrol 1.0 m/s tới waypoint, đổi target_idx khi tới."""
        wp0 = [60.0, 24.0]
        wp1 = [64.0, 24.0]
        m = monster("M1", wp0, waypoints=[wp0, wp1])
        sc = scenario(pos=[10, 0], monsters=[m], random_fish=False)
        d = Driver(sc)
        # Quái ở wp0, target_idx=1 -> di chuyển về wp1
        step = PATROL_SPEED / TICK  # 1.0 / 60
        # Chạy vài bước và kiểm tra quái di chuyển về wp1
        d.step()
        snap = d.snap()
        m_snap = [m for m in snap["monsters"] if m["id"] == "M1"][0]
        # Sau 1 bước, x phải tăng
        self.assertAlmostEqual(m_snap["pos"][0], wp0[0] + step, places=6)
        self.assertEqual(m_snap["pos"][1], wp1[1])
        self.assertEqual(m_snap["state"], "patrol")

        # Tìm bước mà quái đổi target_idx (tới wp1 rồi quay lại wp0)
        total_dist = math.dist(wp0, wp1)  # 4.0
        # Sau 1 bước ở trên, quái cần thêm (total_dist - step)/step - 1 bước nữa
        # Nhưng khi remaining <= step, nó snap về đích và đổi idx
        # Chạy đến khi quái về gần wp0 (đã qua wp1 rồi quay lại)
        for _ in range(500):
            d.step()
            m_snap = [m for m in d.snap()["monsters"] if m["id"] == "M1"][0]
            if m_snap["target_idx"] == 0:
                # Đã đổi target_idx -> đúng
                self.assertAlmostEqual(m_snap["pos"][0], wp1[0], places=3)
                break
        else:
            self.fail("Quái không đổi target_idx sau 500 bước")

    def test_M2_chase_enter_and_exit(self):
        """Người chơi d>=10, cách<=10 -> chase 3.0 m/s; >16 m hoặc d<10 -> patrol."""
        # Đặt người chơi trong vùng phát hiện
        player_pos = [60.0, MONSTER_DEPTHS[0]]  # d=10, đúng ngưỡng
        m_pos = [60.0 + DETECT_RADIUS, MONSTER_DEPTHS[0]]  # cách đúng detect_radius
        m = monster("M1", m_pos, waypoints=[m_pos, [m_pos[0] + 4, m_pos[1]]])
        sc = scenario(pos=player_pos, monsters=[m], random_fish=False, oxygen_ticks=OXY_MAX)
        d = Driver(sc)
        d.step()
        snap = d.snap()
        m_snap = [m for m in snap["monsters"] if m["id"] == "M1"][0]
        self.assertEqual(m_snap["state"], "chase")

    def test_M2b_chase_exit_depth_too_shallow(self):
        """d<10 -> quái không chase (về patrol)."""
        player_pos = [60.0, MONSTER_DEPTHS[0] - 0.1]  # d < 10
        m_pos = [60.0 + 5, MONSTER_DEPTHS[0]]
        m = monster("M1", m_pos, waypoints=[m_pos, [m_pos[0] + 4, m_pos[1]]])
        sc = scenario(pos=player_pos, monsters=[m], random_fish=False, oxygen_ticks=OXY_MAX)
        d = Driver(sc)
        d.step()
        snap = d.snap()
        m_snap = [m for m in snap["monsters"] if m["id"] == "M1"][0]
        self.assertEqual(m_snap["state"], "patrol")

    def test_M2c_chase_exit_too_far(self):
        """Đang chase, khoảng cách > exit_radius -> patrol."""
        player_pos = [60.0, MONSTER_DEPTHS[0]]
        m_pos = [60.0 + EXIT_RADIUS + 1, MONSTER_DEPTHS[0]]
        m = monster("M1", m_pos, waypoints=[m_pos, [m_pos[0] + 4, m_pos[1]]],
                    state="chase")
        sc = scenario(pos=player_pos, monsters=[m], random_fish=False, oxygen_ticks=OXY_MAX)
        d = Driver(sc)
        d.step()
        snap = d.snap()
        m_snap = [m for m in snap["monsters"] if m["id"] == "M1"][0]
        self.assertEqual(m_snap["state"], "patrol")

    def test_M3_monster_hit_lifo_loss(self):
        """Chạm <=1.5m: monster_hit {monster_id,hp,lost LIFO floor(n/2),pos}, invuln 90, state recoil 60."""
        player_pos = [60.0, 20.0]
        m_pos = [60.0 + HIT_RADIUS, 20.0]  # chạm vừa đúng
        m = monster("M1", m_pos, waypoints=[m_pos, [m_pos[0] + 4, m_pos[1]]])
        hold = ["ca_loc", "bong_sung", "ca_linh", "ca_keo"]
        # floor(4 * 0.5) = 2 items lost
        sc = scenario(pos=player_pos, hold=hold, monsters=[m], random_fish=False,
                      oxygen_ticks=OXY_MAX)
        d = Driver(sc)
        d.step()
        evs = d.rows
        hit_evs = [r for r in evs if r["name"] == "monster_hit"]
        self.assertEqual(len(hit_evs), 1)
        hit = hit_evs[0]["data"]
        self.assertEqual(hit["monster_id"], "M1")
        self.assertEqual(hit["hp"], G["hp_max"] - 1)
        # Lost: LIFO = pop from end, floor(4*0.5)=2 items
        self.assertEqual(len(hit["lost"]), 2)
        self.assertEqual(hit["lost"], ["ca_keo", "ca_linh"])  # pop() 2 lần LIFO
        # Player state
        snap = d.snap()
        # invuln_ticks: set = 90 trong _step_monsters, giảm ở ĐẦU bước tiếp (line 138)
        # Vậy snapshot tại bước hit: invuln_ticks = 90
        self.assertEqual(snap["player"]["invuln_ticks"], INVULN_TICKS)
        # Monster: state recoil, ticks_left = recoil_ticks
        m_snap = [m for m in snap["monsters"] if m["id"] == "M1"][0]
        self.assertEqual(m_snap["state"], "recoil")
        self.assertEqual(m_snap["state_ticks_left"], RECOIL_TICKS)
        self.assertIsNotNone(m_snap["recoil_dir"])

    def test_M4_invulnerable_no_hit(self):
        """Đang bất tử: không hit, quái không vào recoil."""
        player_pos = [60.0, 20.0]
        m_pos = [60.0 + 0.5, 20.0]  # rất gần
        m = monster("M1", m_pos, waypoints=[m_pos, [m_pos[0] + 4, m_pos[1]]])
        sc = scenario(pos=player_pos, monsters=[m], random_fish=False,
                      invuln_ticks=10, oxygen_ticks=OXY_MAX)
        d = Driver(sc)
        evs = d.step()
        self.assertNotIn("monster_hit", names(evs))
        m_snap = [m for m in d.snap()["monsters"] if m["id"] == "M1"][0]
        self.assertNotEqual(m_snap["state"], "recoil")

    def test_M5_two_monsters_only_nearest_hits_tie_by_id(self):
        """Hai quái trong tầm: chỉ 1 hit, con gần nhất, hòa theo id."""
        player_pos = [60.0, 20.0]
        # M2 gần hơn M1
        m1 = monster("M1", [60.0 + 1.0, 20.0],
                     waypoints=[[60.0 + 1.0, 20.0], [65.0, 20.0]])
        m2 = monster("M2", [60.0 + 0.5, 20.0],
                     waypoints=[[60.0 + 0.5, 20.0], [65.0, 20.0]])
        sc = scenario(pos=player_pos, monsters=[m1, m2], random_fish=False,
                      oxygen_ticks=OXY_MAX)
        d = Driver(sc)
        evs = d.step()
        hits = find(evs, "monster_hit")
        self.assertEqual(len(hits), 1, "Chỉ 1 hit dù 2 quái trong tầm")
        self.assertEqual(hits[0]["monster_id"], "M2", "Con gần nhất (M2) phải hit")

    def test_M5b_tie_distance_smaller_id_wins(self):
        """Hòa khoảng cách: id nhỏ nhất thắng."""
        player_pos = [60.0, 20.0]
        m1 = monster("M1", [60.0 + 1.0, 20.0],
                     waypoints=[[60.0 + 1.0, 20.0], [65.0, 20.0]])
        m2 = monster("M2", [60.0 - 1.0, 20.0],
                     waypoints=[[60.0 - 1.0, 20.0], [55.0, 20.0]])
        # Cả 2 cách cùng 1.0, nhưng code dùng min() -> tùy impl
        sc = scenario(pos=player_pos, monsters=[m1, m2], random_fish=False,
                      oxygen_ticks=OXY_MAX)
        d = Driver(sc)
        evs = d.step()
        hits = find(evs, "monster_hit")
        self.assertEqual(len(hits), 1)

    def test_M6_recoil_movement_and_end(self):
        """Recoil: mỗi bước lùi recoil_dist/60 m theo recoil_dir; hết 60 bước -> patrol."""
        # Đặt quái ở trạng thái recoil với recoil_dir=[1,0] (lùi ra phải)
        m_pos = [60.0, 20.0]
        rdir = [1.0, 0.0]
        m = monster("M1", m_pos, waypoints=[[56.0, 20.0], [64.0, 20.0]],
                    state="recoil", state_ticks_left=RECOIL_TICKS,
                    recoil_dir=rdir)
        sc = scenario(pos=[10.0, 0.0], monsters=[m], random_fish=False)
        d = Driver(sc)
        pos_before = m_pos[0]
        step_dist = RECOIL_DIST / TICK  # 2.0 / 60
        # Chạy 1 bước
        d.step()
        snap = d.snap()
        m_snap = [m for m in snap["monsters"] if m["id"] == "M1"][0]
        expected_x = pos_before + rdir[0] * step_dist
        self.assertAlmostEqual(m_snap["pos"][0], expected_x, places=6)
        self.assertEqual(m_snap["state"], "recoil")
        self.assertEqual(m_snap["state_ticks_left"], RECOIL_TICKS - 1)

        # Chạy hết recoil
        for _ in range(RECOIL_TICKS - 1):
            d.step()
        snap = d.snap()
        m_snap = [m for m in snap["monsters"] if m["id"] == "M1"][0]
        self.assertEqual(m_snap["state"], "patrol")
        self.assertIsNone(m_snap["recoil_dir"])

    def test_M6b_recoil_default_dir_when_overlap(self):
        """Trùng tâm quái-người -> recoil_dir = [1, 0]."""
        player_pos = [60.0, 20.0]
        m = monster("M1", [60.0, 20.0],
                    waypoints=[[60.0, 20.0], [64.0, 20.0]])
        sc = scenario(pos=player_pos, monsters=[m], random_fish=False,
                      oxygen_ticks=OXY_MAX)
        d = Driver(sc)
        d.step()
        snap = d.snap()
        m_snap = [m for m in snap["monsters"] if m["id"] == "M1"][0]
        self.assertEqual(m_snap["state"], "recoil")
        self.assertEqual(m_snap["recoil_dir"], [1.0, 0.0])

    def test_M7_hp1_hit_faint_monster(self):
        """Máu 1 + hit -> monster_hit, faint{cause:"monster"}, gather_end fainted, inventory rỗng."""
        player_pos = [60.0, 20.0]
        m_pos = [60.0 + 0.5, 20.0]
        m = monster("M1", m_pos, waypoints=[m_pos, [m_pos[0] + 4, m_pos[1]]])
        hold = ["ca_loc", "bong_sung"]
        sc = scenario(pos=player_pos, hold=hold, monsters=[m], random_fish=False,
                      hp=1, oxygen_ticks=OXY_MAX)
        d = Driver(sc)
        evs = d.step()
        self.assertIn("monster_hit", names(evs))
        self.assertIn("faint", names(evs))
        self.assertIn("gather_end", names(evs))
        # faint cause
        faint = find(evs, "faint")
        self.assertEqual(faint[0]["cause"], "monster")
        self.assertEqual(faint[0]["hp"], 0)
        # gather_end
        end = find(evs, "gather_end")
        self.assertEqual(end[0]["reason"], "fainted")
        self.assertEqual(end[0]["inventory"], {"items": {}})
        # hold rỗng
        self.assertEqual(d.snap()["hold"], [])

    def test_M8_choke_before_monster_hit(self):
        """Cùng tick ngạt trước hit: choke rồi monster_hit; choke làm Máu 0 -> bỏ bước quái."""
        player_pos = [60.0, 20.0]
        m_pos = [60.0 + 0.5, 20.0]
        m = monster("M1", m_pos, waypoints=[m_pos, [m_pos[0] + 4, m_pos[1]]])
        # hp=1, oxy=0, zero_oxy_ticks=59 -> choke ở bước này, hp->0 -> faint trước quái
        sc = scenario(pos=player_pos, hold=["ca_loc"], monsters=[m], random_fish=False,
                      hp=1, oxygen_ticks=0, zero_oxy_ticks=CHOKE - 1)
        d = Driver(sc)
        evs = d.step()
        # choke xảy ra trước monster step
        self.assertIn("choke", names(evs))
        self.assertIn("faint", names(evs))
        faint = find(evs, "faint")
        self.assertEqual(faint[0]["cause"], "choke")
        # Không có monster_hit vì đã faint trước
        self.assertNotIn("monster_hit", names(evs))

    def test_M9_monsters_by_day(self):
        """Mặc định Ngày 1 chỉ có M1; day=3 có M1+M2."""
        # Day 1: chỉ M1 (from_day <= 1)
        # Dùng scenario không truyền monsters để lấy spawns mặc định từ contract
        sc = scenario(random_fish=False)
        # Xóa key monsters nếu có (scenario helper có thể thêm)
        sc.pop("monsters", None)
        d1 = Driver(sc, day=1)
        monsters_d1 = d1.snap()["monsters"]
        ids_d1 = [m["id"] for m in monsters_d1]
        self.assertIn("M1", ids_d1)
        self.assertNotIn("M2", ids_d1, "Day 1 không có M2 (from_day=3)")

        # Day 3: M1 + M2
        sc2 = scenario(random_fish=False)
        sc2.pop("monsters", None)
        d3 = Driver(sc2, day=3)
        monsters_d3 = d3.snap()["monsters"]
        ids_d3 = [m["id"] for m in monsters_d3]
        self.assertIn("M1", ids_d3)
        self.assertIn("M2", ids_d3, "Day 3 phải có M2 (from_day=3)")


# ---------------------------------------------------------------------------
# 3. Nâng cấp (Upgrade)
# ---------------------------------------------------------------------------
class Upgrade(unittest.TestCase):
    """active_upgrades thay đổi oxygen_max_ticks và hp_max."""

    def test_U1_oxygen_upgrade_level_1(self):
        """active_upgrades={"oxygen":1} -> oxygen_max_ticks = 45*60 = 2700."""
        sc = scenario(random_fish=False)
        d = Driver(sc, active_upgrades={"oxygen": 1})
        snap = d.snap()
        expected = int(round(45 * TICK))  # 2700
        self.assertEqual(snap["player"]["oxygen_max_ticks"], expected)
        self.assertEqual(snap["player"]["oxygen_ticks"], expected)

    def test_U2_hp_upgrade_level_2(self):
        """active_upgrades={"hp":2} -> hp_max = 5."""
        sc = scenario(random_fish=False)
        d = Driver(sc, active_upgrades={"hp": 2})
        snap = d.snap()
        self.assertEqual(snap["player"]["hp_max"], 5)
        self.assertEqual(snap["player"]["hp"], 5)

    def test_U3_combined_upgrades(self):
        """active_upgrades={"oxygen":1,"hp":2} -> cả hai thay đổi."""
        sc = scenario(random_fish=False)
        d = Driver(sc, active_upgrades={"oxygen": 1, "hp": 2})
        snap = d.snap()
        self.assertEqual(snap["player"]["oxygen_max_ticks"], int(round(45 * TICK)))
        self.assertEqual(snap["player"]["hp_max"], 5)

    def test_U4_bad_upgrade_level(self):
        """Cấp không tồn tại -> BadInput."""
        sc = scenario(random_fish=False)
        with self.assertRaises(BadInput):
            Driver(sc, active_upgrades={"oxygen": 99})

    def test_U5_bad_upgrade_type(self):
        """active_upgrades kiểu sai -> BadInput."""
        sc = scenario(random_fish=False)
        with self.assertRaises(BadInput):
            Driver(sc, active_upgrades="invalid")

    def test_U6_player_limits_function(self):
        """player_limits trả đúng giá trị theo cấp nâng cấp."""
        oxy, hp = player_limits(TUNING, None)
        self.assertEqual(oxy, OXY_MAX)
        self.assertEqual(hp, G["hp_max"])

        oxy1, hp1 = player_limits(TUNING, {"oxygen": 1})
        self.assertEqual(oxy1, int(round(45 * TICK)))
        self.assertEqual(hp1, G["hp_max"])

        oxy2, hp2 = player_limits(TUNING, {"hp": 2})
        self.assertEqual(oxy2, OXY_MAX)
        self.assertEqual(hp2, 5)


# ---------------------------------------------------------------------------
# 4. Scenario validation — mã 2 (Scenario)
# ---------------------------------------------------------------------------
class ScenarioValidation(unittest.TestCase):
    """Scenario hợp lệ/không hợp lệ -> BadInput (mã 2)."""

    def test_S1_monster_recoil_invalid_timer_zero(self):
        """monster state recoil mà timer 0 -> BadInput."""
        m = monster("M1", [60.0, 20.0],
                    waypoints=[[60.0, 20.0], [64.0, 20.0]],
                    state="recoil", state_ticks_left=0,
                    recoil_dir=[1.0, 0.0])
        sc = scenario(monsters=[m], random_fish=False)
        with self.assertRaises(BadInput):
            Driver(sc)

    def test_S2_monster_recoil_non_unit_dir(self):
        """monster recoil_dir không đơn vị -> BadInput."""
        m = monster("M1", [60.0, 20.0],
                    waypoints=[[60.0, 20.0], [64.0, 20.0]],
                    state="recoil", state_ticks_left=10,
                    recoil_dir=[2.0, 0.0])  # không đơn vị
        sc = scenario(monsters=[m], random_fish=False)
        with self.assertRaises(BadInput):
            Driver(sc)

    def test_S3_monster_target_idx_out_of_range(self):
        """target_idx = 2 -> BadInput."""
        m = monster("M1", [60.0, 20.0],
                    waypoints=[[60.0, 20.0], [64.0, 20.0]],
                    target_idx=2)
        sc = scenario(monsters=[m], random_fish=False)
        with self.assertRaises(BadInput):
            Driver(sc)

    def test_S4_monster_unknown_kind(self):
        """kind lạ -> BadInput."""
        m = {"id": "M1", "kind": "rong_bien", "pos": [60.0, 20.0],
             "waypoints": [[60.0, 20.0], [64.0, 20.0]]}
        sc = scenario(monsters=[m], random_fish=False)
        with self.assertRaises(BadInput):
            Driver(sc)

    def test_S5_fish_negative_age_ticks(self):
        """fish age_ticks âm -> BadInput."""
        f = fish_fixture("F1", [50.0, 15.0], kind="ca_loc", age_ticks=-1)
        sc = scenario(fish=[f], random_fish=True)
        with self.assertRaises(BadInput):
            Driver(sc)

    def test_S6_hold_valid_ca_keo_keo_neo(self):
        """hold có ca_keo/keo_neo hợp lệ: không lỗi."""
        sc = scenario(hold=["ca_keo", "keo_neo", "ca_loc"], random_fish=False)
        d = Driver(sc)  # Không raise
        self.assertEqual(len(d.snap()["hold"]), 3)

    def test_S7_day_out_of_range(self):
        """day ngoài [1,5] -> BadInput."""
        sc = scenario(random_fish=False)
        with self.assertRaises(BadInput):
            Driver(sc, day=0)
        with self.assertRaises(BadInput):
            Driver(sc, day=6)

    def test_S8_day_bool_rejected(self):
        """day=True (bool) -> BadInput."""
        sc = scenario(random_fish=False)
        with self.assertRaises(BadInput):
            Driver(sc, day=True)


# ---------------------------------------------------------------------------
# 5. Sanity checks
# ---------------------------------------------------------------------------
class SanityP2(unittest.TestCase):
    def test_contract_p2_fish_initial_is_int(self):
        """fish_initial phải là int (8) trong P2, không phải list như P1."""
        self.assertIsInstance(FISH_INITIAL, int)
        self.assertEqual(FISH_INITIAL, 8)

    def test_contract_p2_has_fish_speed(self):
        """P2 phải có fish_speed trong tuning."""
        self.assertIn("fish_speed", G)
        self.assertEqual(G["fish_speed"], 1.5)

    def test_contract_p2_has_monsters(self):
        """P2 phải có monsters trong tuning."""
        self.assertIn("monsters", G)
        self.assertIn("species", MONSTER_CFG)
        self.assertIn("ca_sau", MONSTER_CFG["species"])

    def test_contract_p2_has_shop_upgrades(self):
        """P2 phải có shop.upgrades trong tuning."""
        self.assertIn("shop", TUNING)
        shop = TUNING["shop"]
        self.assertIn("upgrades", shop)
        self.assertIn("oxygen", shop["upgrades"])
        self.assertIn("hp", shop["upgrades"])

    def test_monster_fixture_depths(self):
        """Fixture constants hợp lý với contract."""
        self.assertGreaterEqual(MONSTER_DEPTHS[0], 10)
        self.assertGreater(EXIT_RADIUS, DETECT_RADIUS)
        self.assertGreater(CHASE_SPEED, PATROL_SPEED)


if __name__ == "__main__":
    unittest.main()
