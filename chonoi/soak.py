"""Soak headless runner (Phase 4 Test Contract v1.3).

Lệnh: python3 -m chonoi.soak --seed 7 --days 10 --out soak.json
Chạy N ngày trong một tiến trình headless duy nhất: gather -> quan -> shop.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import tempfile
import time

from .contract import load_contract
from .day import DaySession
from .errors import BadInput
from .inputs import InputState


class _SoakParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        sys.stderr.write(f"lỗi: {message}\n")
        sys.exit(2)


def _int(name):
    def conv(s):
        try:
            return int(s)
        except ValueError:
            raise argparse.ArgumentTypeError(f"{name} phải là số nguyên")
    return conv


class SoakBot:
    """Bot tất định điều khiển Út Sen xuyên suốt các pha của vòng Ngày."""

    def __init__(self):
        self.tick = 0

    def get_input(self, sess: DaySession) -> InputState:
        phase = sess.phase
        edges = set()
        move = (0.0, 0.0)

        if phase == "gather":
            # Út Sen cập bến ở dock_pos [2, 0] để kết thúc lặn gọn gàng
            # Bến dock ở vị trí dock_pos [2, 0], interact_radius = 3.0
            dock_pos = sess.tuning.get("gather", {}).get("dock_pos", [2.0, 0.0])
            player_pos = sess.sim.pos if sess.sim else [2.0, 0.0]
            dist_to_dock = math.dist(player_pos, dock_pos)
            if dist_to_dock <= 2.5:
                # Tại bến -> cập bến
                edges.add("interact")
            else:
                # Hướng về bến
                dx = dock_pos[0] - player_pos[0]
                dy = dock_pos[1] - player_pos[1]
                mag = math.hypot(dx, dy)
                if mag > 0:
                    move = (dx / mag, dy / mag)

        elif phase == "quan":
            # Trong quán: tương tác nấu / phục vụ nếu ở gần bếp hoặc bàn
            # Cho thời gian ca quán chạy đều đặn
            if sess.phase_tick % 60 == 0:
                edges.add("interact")

        elif phase == "shop":
            # Trong shop: hoàn tất shop để chuyển sang ngày mới
            edges.add("shop_done")

        self.tick += 1
        return InputState(move=move, held=set(), edges=edges)


def run_soak(seed: int, days: int, out_path: str) -> dict:
    t_start = time.time()
    contract = load_contract()
    tuning = contract["tuning"]
    mult = tuning.get("score", {}).get("reputation_multiplier", 100)

    scenario = {}
    sess = DaySession(tuning, scenario, seed, days=days, allow_soak=True)
    bot = SoakBot()
    results = []

    last_day_recorded = 0
    crashes = 0

    try:
        max_total_ticks = days * 30000  # Giới hạn an toàn tránh vòng lặp vô hạn
        while not sess.done and sess.tick < max_total_ticks:
            prev_phase = sess.phase
            prev_day = sess.day

            inp = bot.get_input(sess)
            sess.step(inp)

            # Ghi nhận kết quả khi Shop đóng (chuyển ngày hoặc kết thúc)
            if prev_phase == "shop" and (sess.phase != "shop" or sess.done):
                if prev_day > last_day_recorded:
                    results.append({
                        "day": prev_day,
                        "earned": sess.earned,
                        "reputation": sess.reputation,
                        "score": sess.earned + mult * math.floor(sess.reputation),
                    })
                    last_day_recorded = prev_day

    except Exception as e:
        sys.stderr.write(f"Soak crash: {e}\n")
        crashes = 1

    duration_s = round(time.time() - t_start, 2)
    output = {
        "days": days,
        "days_completed": sess.days_completed,
        "crashes": crashes,
        "results": results,
        "duration_s": duration_s,
    }

    # Ghi file nguyên tử qua file tạm
    out_dir = os.path.dirname(os.path.abspath(out_path))
    os.makedirs(out_dir, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".soak-", suffix=".tmp", dir=out_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp, out_path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise

    return output


def main(argv=None) -> int:
    p = _SoakParser(prog="chonoi.soak")
    p.add_argument("--seed", required=True, type=_int("seed"))
    p.add_argument("--days", required=True, type=_int("days"))
    p.add_argument("--out", required=True)
    a = p.parse_args(argv)

    try:
        if a.days < 1:
            raise BadInput("--days phải >= 1")
    except BadInput as e:
        sys.stderr.write(f"đầu vào sai: {e}\n")
        return 2

    try:
        run_soak(a.seed, a.days, a.out)
    except BadInput as e:
        sys.stderr.write(f"đầu vào sai: {e}\n")
        return 2
    except OSError as e:
        sys.stderr.write(f"lỗi ghi: {e}\n")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

