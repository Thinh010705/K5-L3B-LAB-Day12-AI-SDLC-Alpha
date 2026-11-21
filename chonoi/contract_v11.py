"""Validate Test Contract v1.1 (TICKET-02), independent of v1.0 validator.

This checks schema and cross-field invariants, NOT the simulator's behavior.
The canonical fixed numbers are additionally checked by tools/check_contract_p2.py.
"""
from __future__ import annotations
import math
from .errors import BadInput

FISH = frozenset(('ca_linh', 'ca_loc', 'ca_keo'))
PLANTS = frozenset(('bong_dien_dien', 'bong_sung', 'keo_neo'))
DISHES = frozenset((
    'ca_loc_nuong_trui', 'goi_bong_sung', 'lau_ca_linh_dien_dien',
    'canh_chua_ca_loc', 'ca_keo_nuong', 'lau_mam',
))


def _fail(path, message):
    raise BadInput(f'{path}: {message}')


def _object(value, path):
    if not isinstance(value, dict):
        _fail(path, 'phải là object')
    return value


def _array(value, path, *, min_items=0, max_items=None):
    if not isinstance(value, list):
        _fail(path, 'phải là mảng')
    if len(value) < min_items or (max_items is not None and len(value) > max_items):
        _fail(path, f'số phần tử không hợp lệ: {len(value)}')
    return value


def _real(value, path, *, low=None, high=None, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        _fail(path, 'phải là số hữu hạn, không phải boolean')
    if positive and value <= 0:
        _fail(path, 'phải lớn hơn 0')
    if low is not None and value < low or high is not None and value > high:
        _fail(path, f'nằm ngoài dải [{low}, {high}]')
    return value


def _integer(value, path, *, low=None, high=None):
    if type(value) is not int:
        _fail(path, 'phải là số nguyên, không phải boolean')
    if low is not None and value < low or high is not None and value > high:
        _fail(path, f'nằm ngoài dải [{low}, {high}]')
    return value


def _pair(value, path, *, low=None, high=None, strict=False):
    p = _array(value, path, min_items=2, max_items=2)
    a, b = (_real(x, f'{path}[{i}]') for i, x in enumerate(p))
    if (a >= b if strict else a > b):
        _fail(path, 'phải tăng dần')
    if low is not None and a < low or high is not None and b > high:
        _fail(path, 'nằm ngoài phạm vi cho phép')
    return a, b


def _position(value, path, bounds):
    p = _array(value, path, min_items=2, max_items=2)
    for i, (key, component) in enumerate(zip(bounds, p)):
        lo, hi = bounds[key]
        _real(component, f'{path}[{i}]', low=lo, high=hi)
    return p


def _bounds(value, path, keys):
    obj = _object(value, path)
    if set(obj) != set(keys):
        _fail(path, f'phải có chính xác khóa {keys}')
    return {k: _pair(obj[k], f'{path}.{k}', low=0, strict=True) for k in keys}


def _positive_counts(value, path, allowed):
    obj = _object(value, path)
    if not obj or set(obj) - set(allowed):
        _fail(path, 'chứa id không hợp lệ hoặc rỗng')
    for k, v in obj.items():
        _integer(v, f'{path}.{k}', low=1)
    return obj


def _stations(value, path, bounds, prefix, expected_count):
    entries = _array(value, path, min_items=expected_count, max_items=expected_count)
    seen = set()
    for obj in entries:
        obj = _object(obj, path + '[]')
        ident = obj.get('id')
        if not isinstance(ident, str) or not ident or ident in seen or not ident.startswith(prefix):
            _fail(path, 'id không hợp lệ hoặc trùng')
        seen.add(ident)
        _position(obj.get('pos'), f'{path}.{ident}.pos', bounds)


def _gather(g):
    path = 'tuning.gather'
    _real(g.get('duration_s'), path + '.duration_s', low=60, high=600)
    b = _bounds(g.get('bounds'), path + '.bounds', ('x', 'd'))
    for field in ('dock_pos', 'start_pos'):
        _position(g.get(field), path + '.' + field, b)
    for field in ('dock_radius', 'interact_radius', 'catch_radius'):
        _real(g.get(field), path + '.' + field, positive=True)
    for field in ('swim_speed', 'oxygen_max_s', 'regrow_s', 'catch_cooldown_s'):
        _real(g.get(field), path + '.' + field, positive=True)
    for field in ('start_heading_deg', 'surface_depth'):
        _real(g.get(field), path + '.' + field)
    for field in ('ramp_max_ticks', 'hold_capacity', 'hp_max', 'oxygen_refill_per_tick',
                  'choke_interval_ticks', 'node_yield'):
        _integer(g.get(field), path + '.' + field, low=0 if field == 'ramp_max_ticks' else 1)
    if g['surface_depth'] < b['d'][0] or g['surface_depth'] > b['d'][1]:
        _fail(path + '.surface_depth', 'ngoài vùng nước')

    fy = _object(g.get('fish_yield'), path + '.fish_yield')
    if set(fy) != FISH:
        _fail(path + '.fish_yield', 'phải có đúng ca_linh, ca_loc, ca_keo')
    for kind, amount in fy.items():
        _integer(amount, path + '.fish_yield.' + kind, low=1, high=g['hold_capacity'])

    nodes = _array(g.get('nodes'), path + '.nodes', min_items=6, max_items=6)
    seen = set()
    kinds = set()
    for n in nodes:
        n = _object(n, path + '.nodes[]')
        ident, kind = n.get('id'), n.get('kind')
        if not isinstance(ident, str) or not ident or ident in seen:
            _fail(path + '.nodes', 'id không hợp lệ hoặc trùng')
        seen.add(ident)
        if kind not in PLANTS:
            _fail(f'{path}.nodes.{ident}.kind', 'loại cây không hợp lệ')
        kinds.add(kind)
        pos = _position(n.get('pos'), f'{path}.nodes.{ident}.pos', b)
        if pos[1] != 0:
            _fail(f'{path}.nodes.{ident}.pos', 'nút hái phải ở d=0')
    if kinds != PLANTS:
        _fail(path + '.nodes', 'thiếu một loại cây')

    _integer(g.get('fish_initial'), path + '.fish_initial', low=1)
    _integer(g.get('fish_max'), path + '.fish_max', low=g['fish_initial'])
    for key in ('fish_turn_ticks', 'fish_spawn_ticks'):
        _integer(g.get(key), path + '.' + key, low=1)
    for key in ('fish_speed', 'fish_spawn_clearance'):
        _real(g.get(key), path + '.' + key, positive=True)
    xmin, xmax = _pair(g.get('fish_x'), path + '.fish_x', low=b['x'][0], high=b['x'][1], strict=True)

    depths = _object(g.get('fish_depths'), path + '.fish_depths')
    spawn_depths = _object(g.get('fish_spawn_depths'), path + '.fish_spawn_depths')
    weights = _object(g.get('fish_weights'), path + '.fish_weights')
    if set(depths) != FISH or set(spawn_depths) != FISH or set(weights) != FISH:
        _fail(path, 'fish_depths / fish_spawn_depths / fish_weights phải có 3 loài')
    for kind in FISH:
        lo, hi = _pair(depths[kind], f'{path}.fish_depths.{kind}', low=b['d'][0], high=b['d'][1], strict=True)
        values = _array(spawn_depths[kind], f'{path}.fish_spawn_depths.{kind}', min_items=1)
        for index, v in enumerate(values):
            _real(v, f'{path}.fish_spawn_depths.{kind}[{index}]', low=lo, high=hi)
        if len(set(values)) != len(values):
            _fail(f'{path}.fish_spawn_depths.{kind}', 'độ sâu trùng')
        _real(weights[kind], f'{path}.fish_weights.{kind}', low=0, high=1)
    if abs(sum(weights.values()) - 1) > 1e-9:
        _fail(path + '.fish_weights', 'tổng trọng số phải bằng 1')
    spawn_x = _array(g.get('fish_spawn_x'), path + '.fish_spawn_x', min_items=1)
    for i, x in enumerate(spawn_x):
        _real(x, f'{path}.fish_spawn_x[{i}]', low=xmin, high=xmax)
    if len(set(spawn_x)) != len(spawn_x):
        _fail(path + '.fish_spawn_x', 'tọa độ trùng')

    monsters = _object(g.get('monsters'), path + '.monsters')
    _integer(monsters.get('invuln_ticks'), path + '.monsters.invuln_ticks', low=1)
    _real(monsters.get('loss_ratio'), path + '.monsters.loss_ratio', low=0, high=1)
    species = _object(monsters.get('species'), path + '.monsters.species')
    if 'ca_sau' not in species:
        _fail(path + '.monsters.species', 'thiếu ca_sau')
    depth_by_species = {}
    for kind, conf in species.items():
        conf = _object(conf, f'{path}.monsters.species.{kind}')
        depth_by_species[kind] = _pair(conf.get('depths'), f'{path}.monsters.species.{kind}.depths',
                                       low=b['d'][0], high=b['d'][1], strict=True)
        for key in ('patrol_speed', 'chase_speed', 'detect_radius', 'exit_radius',
                    'hit_radius', 'recoil_dist'):
            _real(conf.get(key), f'{path}.monsters.species.{kind}.{key}', positive=True)
        _integer(conf.get('recoil_ticks'), f'{path}.monsters.species.{kind}.recoil_ticks', low=1)
        if conf['exit_radius'] <= conf['detect_radius']:
            _fail(f'{path}.monsters.species.{kind}', 'exit_radius phải lớn hơn detect_radius')
    spawns = _array(monsters.get('spawns'), path + '.monsters.spawns', min_items=1)
    seen = set()
    for spawn in spawns:
        spawn = _object(spawn, path + '.monsters.spawns[]')
        ident, kind = spawn.get('id'), spawn.get('kind')
        if not isinstance(ident, str) or not ident or ident in seen:
            _fail(path + '.monsters.spawns', 'id không hợp lệ hoặc trùng')
        seen.add(ident)
        if kind not in species:
            _fail(path + '.monsters.spawns.' + ident, 'loài chưa khai báo')
        _integer(spawn.get('from_day'), f'{path}.monsters.spawns.{ident}.from_day', low=1, high=5)
        for field in ('pos',):
            pos = _position(spawn.get(field), f'{path}.monsters.spawns.{ident}.{field}', b)
            low, high = depth_by_species[kind]
            if not low <= pos[1] <= high:
                _fail(f'{path}.monsters.spawns.{ident}.{field}', 'độ sâu ngoài dải của loài')
        wps = _array(spawn.get('waypoints'), f'{path}.monsters.spawns.{ident}.waypoints', min_items=2, max_items=2)
        for j, wp in enumerate(wps):
            pos = _position(wp, f'{path}.monsters.spawns.{ident}.waypoints[{j}]', b)
            low, high = depth_by_species[kind]
            if not low <= pos[1] <= high:
                _fail(f'{path}.monsters.spawns.{ident}.waypoints[{j}]', 'độ sâu ngoài dải của loài')


def _quan(q):
    path = 'tuning.quan'
    _real(q.get('duration_s'), path + '.duration_s', low=60, high=600)
    b = _bounds(q.get('bounds'), path + '.bounds', ('x', 'z'))
    _position(q.get('start_pos'), path + '.start_pos', b)
    for name in ('walk_speed', 'interact_radius', 'patience_s', 'eat_s',
                 'customer_interval_s', 'tip_rate', 'tip_min_patience_ratio', 'tip_reputation'):
        _real(q.get(name), f'{path}.{name}', positive=True)
    for name in ('left_reputation_delta', 'reputation_initial', 'reputation_min', 'reputation_max'):
        _real(q.get(name), f'{path}.{name}')
    for name in ('ramp_max_ticks', 'first_customer_tick', 'carry_limit'):
        _integer(q.get(name), f'{path}.{name}', low=0 if name == 'ramp_max_ticks' else 1)
    _stations(q.get('stoves'), path + '.stoves', b, 'B', 2)
    _stations(q.get('tables'), path + '.tables', b, 'T', 4)
    if q['reputation_min'] > q['reputation_initial'] or q['reputation_initial'] > q['reputation_max']:
        _fail(path + '.reputation_initial', 'uy tín ban đầu ngoài giới hạn')
    if not 0 < q['tip_min_patience_ratio'] <= 1:
        _fail(path + '.tip_min_patience_ratio', 'phải thuộc (0,1]')
    if q['left_reputation_delta'] >= 0:
        _fail(path + '.left_reputation_delta', 'phải âm')
    if q.get('burn_s') is not None:
        _real(q['burn_s'], path + '.burn_s', positive=True)  # optional burn extension


def _menu(menu):
    path = 'tuning.menu'
    if set(menu) != DISHES:
        _fail(path, 'phải có đúng 6 id món chuẩn')
    for dish_id, dish in menu.items():
        dish = _object(dish, f'{path}.{dish_id}')
        _real(dish.get('cook_s'), f'{path}.{dish_id}.cook_s', positive=True)
        _integer(dish.get('price'), f'{path}.{dish_id}.price', low=1)
        _positive_counts(dish.get('recipe'), f'{path}.{dish_id}.recipe', FISH | PLANTS)


def _day_plan(plans, menu):
    path = 'tuning.day_plan'
    rows = _array(plans, path, min_items=5, max_items=5)
    for day, row in enumerate(rows, 1):
        row = _object(row, f'{path}[{day - 1}]')
        if row.get('day') != day or type(row.get('day')) is not int:
            _fail(f'{path}[{day - 1}].day', 'số ngày phải là 1..5 theo thứ tự')
        dishes = _positive_counts(row.get('dishes'), f'{path}[{day - 1}].dishes', menu)
        ingredients = _positive_counts(row.get('ingredients'), f'{path}[{day - 1}].ingredients', FISH | PLANTS)
        calculated = {}
        for dish_id, portions in dishes.items():
            for kind, count in menu[dish_id]['recipe'].items():
                calculated[kind] = calculated.get(kind, 0) + count * portions
        if ingredients != calculated:
            _fail(f'{path}[{day - 1}].ingredients', f'không bằng tổng công thức × số suất: {calculated}')


def _shop(shop):
    path = 'tuning.shop'
    _integer(shop.get('max_ticks'), path + '.max_ticks', low=1)
    upgrades = _object(shop.get('upgrades'), path + '.upgrades')
    if not {'oxygen', 'hp'} <= set(upgrades):
        _fail(path + '.upgrades', 'thiếu oxygen hoặc hp')
    for kind, levels in upgrades.items():
        rows = _array(levels, f'{path}.upgrades.{kind}', min_items=1)
        for idx, row in enumerate(rows, 1):
            row = _object(row, f'{path}.upgrades.{kind}[{idx - 1}]')
            if row.get('level') != idx or type(row.get('level')) is not int:
                _fail(f'{path}.upgrades.{kind}[{idx - 1}].level', 'cấp phải liên tiếp 1,2,...')
            _integer(row.get('price'), f'{path}.upgrades.{kind}[{idx - 1}].price', low=1)
            # Extension upgrades may have a different level-specific schema.
            if kind == 'oxygen':
                _real(row.get('oxygen_max_s'), f'{path}.upgrades.oxygen[{idx - 1}].oxygen_max_s', positive=True)
            elif kind == 'hp':
                _integer(row.get('hp_max'), f'{path}.upgrades.hp[{idx - 1}].hp_max', low=1)


def validate_contract_v11(contract):
    """Raise BadInput for invalid v1.1 core schema and cross-field invariants."""
    c = _object(contract, 'root')
    if c.get('contract_version') != '1.1':
        _fail('contract_version', 'phải là chuỗi "1.1"')
    cmd = c.get('headless_cmd')
    if not isinstance(cmd, str) or not cmd.strip():
        _fail('headless_cmd', 'phải là chuỗi khác rỗng')
    t = _object(c.get('tuning'), 'tuning')
    if t.get('tick_hz') != 60 or type(t.get('tick_hz')) is not int:
        _fail('tuning.tick_hz', 'phải bằng số nguyên 60')
    g = _object(t.get('gather'), 'tuning.gather')
    q = _object(t.get('quan'), 'tuning.quan')
    menu = _object(t.get('menu'), 'tuning.menu')
    _gather(g)
    _quan(q)
    _menu(menu)
    _day_plan(t.get('day_plan'), menu)
    _shop(_object(t.get('shop'), 'tuning.shop'))
    score = _object(t.get('score'), 'tuning.score')
    _real(score.get('reputation_multiplier'), 'tuning.score.reputation_multiplier', positive=True)
