"""Strict pre-output validation for v1.1 day-mode scenario.

This module validates day orchestration fixtures. Detailed new monster/fish
fixture semantics must also be validated by the corresponding Gather module.
"""
from __future__ import annotations

import json
import math
from .errors import BadInput
from .scenario import _validate_quan, _validate_gather, _check_ids
from .freshness import validate_instances

ALL_KINDS = frozenset(("ca_loc", "ca_linh", "ca_keo", "bong_dien_dien", "bong_sung", "keo_neo"))
GATHER_KEYS = frozenset(("player", "hold", "nodes", "fish", "random_fish", "time_left_ticks",
                         "monsters", "random_ho", "ca_ho"))
GATHER_PLAYER = frozenset(("pos", "vel", "heading_deg", "hp", "oxygen_ticks", "zero_oxy_ticks",
                           "invuln_ticks", "catch_cd_ticks", "attack_cd_ticks"))
QUAN_KEYS = frozenset(("player", "hand", "stoves", "tables", "customers", "random_customers",
                        "time_left_ticks"))
DAY_KEYS = frozenset(("money", "earned", "reputation", "upgrades", "day_plan"))


def _int(v, label, lo=0, hi=None):
    if type(v) is not int or v < lo or (hi is not None and v > hi):
        raise BadInput(f"{label} phải là số nguyên trong [{lo}, {hi or '∞'}]")


def _number(v, label):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
        raise BadInput(f"{label} phải là số hữu hạn")


def _pos(pos, bounds, label):
    if not isinstance(pos, list) or len(pos) != 2:
        raise BadInput(f"{label} phải là [x, độ sâu/z]")
    for val, key in zip(pos, bounds):
        _number(val, label)
        if not bounds[key][0] <= val <= bounds[key][1]:
            raise BadInput(f"{label} ngoài biên {key}")


def _time(block, duration, label):
    if "time_left_ticks" in block:
        _int(block["time_left_ticks"], label + ".time_left_ticks", 1, round(duration * 60))


def load_day_scenario(path, tuning, days):
    if path is None:
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được scenario: {e}")
    if not isinstance(data, dict) or set(data) - {"gather", "quan", "day"}:
        raise BadInput("scenario day chỉ có các khối gather, quan và day")
    for key, value in data.items():
        if not isinstance(value, dict):
            raise BadInput(f"scenario.{key} phải là object")
    g = data.get("gather", {})
    q = data.get("quan", {})
    d = data.get("day", {})
    if set(g) - GATHER_KEYS:
        raise BadInput("scenario.gather có trường không hỗ trợ")
    if set(q) - QUAN_KEYS:
        raise BadInput("scenario.quan không được có stock/reputation hoặc trường lạ")
    if set(d) - DAY_KEYS:
        raise BadInput("scenario.day có trường lạ")
    _time(g, tuning["gather"]["duration_s"], "gather")
    _time(q, tuning["quan"]["duration_s"], "quan")
    if "random_fish" in g and type(g["random_fish"]) is not bool:
        raise BadInput("gather.random_fish phải là boolean")
    if "hold" in g:
        if tuning.get("_contract_version") == "1.2":
            validate_instances(g["hold"], ALL_KINDS)
        elif (not isinstance(g["hold"], list) or len(g["hold"]) > tuning["gather"]["hold_capacity"]
                or any(type(k) is not str or k not in ALL_KINDS for k in g["hold"])):
            raise BadInput("gather.hold phải là danh sách nguyên liệu hợp lệ trong sức chứa")
    for key in ("fish", "nodes", "monsters"):
        if key in g:
            _check_ids("gather." + key, g[key])
    if "fish" in g:
        for f in g["fish"]:
            if f.get("kind") not in {"ca_loc", "ca_linh", "ca_keo"}:
                raise BadInput("gather.fish.kind không hợp lệ")
            _pos(f.get("pos"), tuning["gather"]["bounds"], "gather.fish.pos")
            if f["pos"][1] <= tuning["gather"]["surface_depth"]:
                raise BadInput("gather.fish phải ở dưới nước")
            if "age_ticks" in f:
                _int(f["age_ticks"], "gather.fish.age_ticks")
    if "nodes" in g:
        for n in g["nodes"]:
            if n.get("kind") not in {"bong_dien_dien", "bong_sung", "keo_neo"}:
                raise BadInput("gather.nodes.kind không hợp lệ")
            _pos(n.get("pos"), tuning["gather"]["bounds"], "gather.nodes.pos")
            if n["pos"][1] != 0:
                raise BadInput("gather.nodes.pos phải ở mặt nước")
            if "regrow_ticks" in n:
                _int(n["regrow_ticks"], "gather.nodes.regrow_ticks")
    if "player" in g:
        p = g["player"]
        if not isinstance(p, dict) or set(p) - GATHER_PLAYER:
            raise BadInput("gather.player có trường lạ")
        if "pos" in p:
            _pos(p["pos"], tuning["gather"]["bounds"], "gather.player.pos")
        if "vel" in p:
            if not isinstance(p["vel"], list) or len(p["vel"]) != 2:
                raise BadInput("gather.player.vel phải là mảng [x, d]")
            for val in p["vel"]:
                _number(val, "gather.player.vel")
        if "heading_deg" in p:
            _number(p["heading_deg"], "gather.player.heading_deg")
        for key in ("hp", "oxygen_ticks", "zero_oxy_ticks", "invuln_ticks", "catch_cd_ticks", "attack_cd_ticks"):
            if key in p:
                _int(p[key], "gather.player." + key)
    if "random_customers" in q and type(q["random_customers"]) is not bool:
        raise BadInput("quan.random_customers phải là boolean")
    # Validate existing Quan fixture constraints without stock and reputation, as in day.
    _validate_quan(q, tuning)
    for key in ("money", "earned"):
        if key in d:
            _int(d[key], "day." + key)
    money, earned = d.get("money", 0), d.get("earned", 0)
    if money > earned:
        raise BadInput("day.money không được lớn hơn day.earned")
    if "reputation" in d:
        _number(d["reputation"], "day.reputation")
        if not tuning["quan"]["reputation_min"] <= d["reputation"] <= tuning["quan"]["reputation_max"]:
            raise BadInput("day.reputation ngoài miền")
    if "upgrades" in d:
        if not isinstance(d["upgrades"], dict):
            raise BadInput("day.upgrades phải là object")
        for kind, level in d["upgrades"].items():
            if kind not in tuning["shop"]["upgrades"]:
                raise BadInput("day.upgrades có id không hỗ trợ")
            _int(level, "day.upgrades." + kind, 0, len(tuning["shop"]["upgrades"][kind]))
    if "day_plan" in d:
        plan = d["day_plan"]
        if not isinstance(plan, list) or not plan or len(plan) > days:
            raise BadInput("day.day_plan phải là mảng 1..--days mục")
        seen = set()
        for row in plan:
            if not isinstance(row, dict) or set(row) - {"day", "dishes", "ingredients"}:
                raise BadInput("day.day_plan[] có trường lạ")
            num = row.get("day")
            _int(num, "day.day_plan.day", 1, days)
            if num in seen:
                raise BadInput("day.day_plan trùng ngày")
            seen.add(num)
            dishes = row.get("dishes")
            if not isinstance(dishes, dict) or not dishes:
                raise BadInput("day.day_plan.dishes không hợp lệ")
            ingredients = {}
            for dish, count in dishes.items():
                if dish not in tuning["menu"]:
                    raise BadInput("day.day_plan có dish id không hợp lệ")
                _int(count, "day.day_plan.dishes." + dish, 1)
                for kind, amount in tuning["menu"][dish]["recipe"].items():
                    ingredients[kind] = ingredients.get(kind, 0) + count * amount
            if "ingredients" in row and row["ingredients"] != ingredients:
                raise BadInput("day.day_plan.ingredients không khớp công thức")
    _validate_gather(g, tuning, active_upgrades=d.get("upgrades", {}))
    return data
