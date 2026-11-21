#!/usr/bin/env python3
"""Independent DATA-ONLY check of TICKET-02 core manifest (Test Contract v1.1).

Does not import chonoi, change game.contract.json, or assert runtime support.
Run: python3 tools/check_contract_p2.py
     python3 tools/check_contract_p2.py --manifest path/to/manifest.json
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path

DEFAULT = Path('docs/contracts/game.contract.v1_1.proposed.json')
MENU = {
    'ca_loc_nuong_trui': ({'ca_loc': 1}, 6, 60),
    'goi_bong_sung': ({'bong_sung': 2}, 4, 40),
    'lau_ca_linh_dien_dien': ({'ca_linh': 3, 'bong_dien_dien': 1}, 10, 120),
    'canh_chua_ca_loc': ({'ca_loc': 1, 'bong_dien_dien': 1}, 8, 90),
    'ca_keo_nuong': ({'ca_keo': 2}, 6, 70),
    'lau_mam': ({'ca_linh': 2, 'ca_keo': 1, 'keo_neo': 1, 'bong_dien_dien': 1}, 12, 200),
}
PLANS = [
    {'ca_loc_nuong_trui': 3, 'goi_bong_sung': 3},
    {'ca_loc_nuong_trui': 2, 'lau_ca_linh_dien_dien': 2},
    {'goi_bong_sung': 2, 'canh_chua_ca_loc': 2, 'ca_keo_nuong': 2},
    {'lau_mam': 1, 'ca_loc_nuong_trui': 2, 'goi_bong_sung': 1},
    {'lau_mam': 1, 'lau_ca_linh_dien_dien': 1, 'ca_loc_nuong_trui': 1},
]


def calculate_ingredients(dishes):
    result = {}
    for dish, servings in dishes.items():
        for kind, quantity in MENU[dish][0].items():
            result[kind] = result.get(kind, 0) + quantity * servings
    return result


def audit(manifest):
    """Return errors; empty list means the manifest DATA matches core TICKET-02."""
    errors = []

    def check(path, value, expected):
        # Distinguish booleans from numeric values; tolerate int/float numerically.
        equal = value == expected and not (isinstance(value, bool) != isinstance(expected, bool))
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            equal = False
        if not equal:
            errors.append(f'{path}: expected {expected!r}; got {value!r}')

    def require_map(parent, name, prefix):
        value = parent.get(name) if isinstance(parent, dict) else None
        if not isinstance(value, dict):
            errors.append(f'{prefix}{name}: expected object')
            return {}
        return value

    if not isinstance(manifest, dict):
        return ['root: expected JSON object']
    check('contract_version', manifest.get('contract_version'), '1.1')
    if not isinstance(manifest.get('headless_cmd'), str) or not manifest['headless_cmd'].strip():
        errors.append('headless_cmd: nonempty string required')
    tuning = require_map(manifest, 'tuning', '')
    check('tuning.tick_hz', tuning.get('tick_hz'), 60)
    g = require_map(tuning, 'gather', 'tuning.')
    q = require_map(tuning, 'quan', 'tuning.')
    menu = require_map(tuning, 'menu', 'tuning.')
    score = require_map(tuning, 'score', 'tuning.')

    gathering = {
        'duration_s': 180,
        'bounds': {'x': [0, 100], 'd': [0, 30]},
        'dock_pos': [2, 0], 'dock_radius': 3,
        'start_pos': [2, 0], 'start_heading_deg': 0,
        'swim_speed': 4.0, 'ramp_max_ticks': 6,
        'surface_depth': 0.5, 'oxygen_max_s': 30,
        'oxygen_refill_per_tick': 6, 'choke_interval_ticks': 60,
        'hp_max': 3, 'hold_capacity': 12,
        'interact_radius': 2.0, 'node_yield': 1,
        'regrow_s': 20, 'catch_radius': 2.0, 'catch_cooldown_s': 0.5,
        'fish_yield': {'ca_linh': 3, 'ca_loc': 1, 'ca_keo': 2},
        'nodes': [
            {'id': 'N1', 'kind': 'bong_dien_dien', 'pos': [12, 0]},
            {'id': 'N2', 'kind': 'bong_dien_dien', 'pos': [28, 0]},
            {'id': 'N3', 'kind': 'bong_sung', 'pos': [44, 0]},
            {'id': 'N4', 'kind': 'bong_sung', 'pos': [60, 0]},
            {'id': 'N5', 'kind': 'keo_neo', 'pos': [76, 0]},
            {'id': 'N6', 'kind': 'keo_neo', 'pos': [90, 0]},
        ],
        'fish_initial': 8, 'fish_speed': 1.5,
        'fish_turn_ticks': 120, 'fish_max': 12,
        'fish_spawn_ticks': 360, 'fish_spawn_clearance': 1.0,
        'fish_x': [4, 96],
        'fish_depths': {'ca_linh': [3, 12], 'ca_loc': [8, 20], 'ca_keo': [22, 28]},
        'fish_spawn_x': [15, 30, 45, 60, 75, 90],
        'fish_spawn_depths': {'ca_linh': [5, 10], 'ca_loc': [10, 16], 'ca_keo': [24, 27]},
        'fish_weights': {'ca_linh': 0.4, 'ca_loc': 0.3, 'ca_keo': 0.3},
        'monsters': {
            'species': {'ca_sau': {
                'patrol_speed': 1.0, 'chase_speed': 3.0,
                'detect_radius': 10.0, 'exit_radius': 16.0,
                'depths': [10, 30], 'hit_radius': 1.5,
                'recoil_ticks': 60, 'recoil_dist': 2.0,
            }},
            'spawns': [
                {'id': 'M1', 'kind': 'ca_sau', 'pos': [60, 24],
                 'waypoints': [[60, 24], [64, 24]], 'from_day': 1},
                {'id': 'M2', 'kind': 'ca_sau', 'pos': [85, 18],
                 'waypoints': [[85, 18], [89, 18]], 'from_day': 3},
            ],
            'invuln_ticks': 90, 'loss_ratio': 0.5,
        },
    }
    for name, expected in gathering.items():
        check('tuning.gather.' + name, g.get(name), expected)

    restaurant = {
        'duration_s': 180, 'bounds': {'x': [0, 16], 'z': [0, 10]},
        'start_pos': [8, 5], 'walk_speed': 4.0,
        'ramp_max_ticks': 6, 'interact_radius': 1.5,
        'stoves': [{'id': 'B1', 'pos': [2, 8]}, {'id': 'B2', 'pos': [5, 8]}],
        'tables': [
            {'id': 'T1', 'pos': [9, 2]}, {'id': 'T2', 'pos': [13, 2]},
            {'id': 'T3', 'pos': [9, 6]}, {'id': 'T4', 'pos': [13, 6]},
        ],
        'first_customer_tick': 120, 'customer_interval_s': 15,
        'patience_s': 60, 'eat_s': 10, 'burn_s': None, 'carry_limit': 1,
        'tip_rate': 0.2, 'tip_min_patience_ratio': 0.5,
        'tip_reputation': 0.2, 'left_reputation_delta': -0.5,
        'reputation_initial': 3.0, 'reputation_min': 0.0, 'reputation_max': 5.0,
    }
    for name, expected in restaurant.items():
        check('tuning.quan.' + name, q.get(name), expected)
    check('tuning.score.reputation_multiplier', score.get('reputation_multiplier'), 100)
    check('tuning.menu.ids', set(menu), set(MENU))
    for dish, (recipe, cook_s, price) in MENU.items():
        check(f'tuning.menu.{dish}', menu.get(dish), {'recipe': recipe, 'cook_s': cook_s, 'price': price})

    plans = tuning.get('day_plan')
    if not isinstance(plans, list) or len(plans) != 5:
        errors.append('tuning.day_plan: expected 5 entries D1-D5')
    else:
        for i, expected_dishes in enumerate(PLANS, 1):
            p = plans[i - 1]
            if not isinstance(p, dict):
                errors.append(f'tuning.day_plan[{i - 1}]: expected object')
                continue
            check(f'tuning.day_plan[{i - 1}].day', p.get('day'), i)
            check(f'tuning.day_plan[{i - 1}].dishes', p.get('dishes'), expected_dishes)
            check(f'tuning.day_plan[{i - 1}].ingredients', p.get('ingredients'), calculate_ingredients(expected_dishes))
    shop = require_map(tuning, 'shop', 'tuning.')
    check('tuning.shop.max_ticks', shop.get('max_ticks'), 600)
    upgrades = require_map(shop, 'upgrades', 'tuning.shop.')
    check('tuning.shop.upgrades', upgrades, {
        'oxygen': [
            {'level': 1, 'price': 200, 'oxygen_max_s': 45},
            {'level': 2, 'price': 400, 'oxygen_max_s': 60},
        ],
        'hp': [
            {'level': 1, 'price': 250, 'hp_max': 4},
            {'level': 2, 'price': 500, 'hp_max': 5},
        ],
    })
    return errors


def main():
    parser = argparse.ArgumentParser(description='Audit TICKET-02 v1.1 core manifest data only')
    parser.add_argument('--manifest', type=Path, default=DEFAULT)
    args = parser.parse_args()
    try:
        with args.manifest.open(encoding='utf-8') as fp:
            data = json.load(fp)
    except (OSError, ValueError) as exc:
        parser.error(f'could not load manifest: {exc}')
    issues = audit(data)
    if issues:
        print(f'FAIL: {len(issues)} mismatch(es) against TICKET-02:')
        for issue in issues:
            print(' - ' + issue)
        return 1
    print('PASS: TICKET-02 v1.1 core manifest data checked')
    print('6 nodes | 3 fish species | 2 stoves | 4 tables | 6 dishes | 5 plans | 2 upgrades')
    print('NOTE: Does NOT prove CLI/simulation/UI support v1.1. Check runtime separately.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
