#!/usr/bin/env python3
"""TICKET-02: generate a proposed Test Contract v1.1 manifest from v1.0.

Default is non-destructive: writes docs/contracts/game.contract.v1_1.proposed.json.
Only --apply writes game.contract.json (with a P1 backup).
"""
import argparse
import json
import shutil
from copy import deepcopy
from pathlib import Path

DISHES = {
    'ca_loc_nuong_trui': {'recipe': {'ca_loc': 1}, 'cook_s': 6, 'price': 60},
    'goi_bong_sung': {'recipe': {'bong_sung': 2}, 'cook_s': 4, 'price': 40},
    'lau_ca_linh_dien_dien': {'recipe': {'ca_linh': 3, 'bong_dien_dien': 1}, 'cook_s': 10, 'price': 120},
    'canh_chua_ca_loc': {'recipe': {'ca_loc': 1, 'bong_dien_dien': 1}, 'cook_s': 8, 'price': 90},
    'ca_keo_nuong': {'recipe': {'ca_keo': 2}, 'cook_s': 6, 'price': 70},
    'lau_mam': {'recipe': {'ca_linh': 2, 'ca_keo': 1, 'keo_neo': 1, 'bong_dien_dien': 1}, 'cook_s': 12, 'price': 200},
}

PLANS = [
    {'ca_loc_nuong_trui': 3, 'goi_bong_sung': 3},
    {'ca_loc_nuong_trui': 2, 'lau_ca_linh_dien_dien': 2},
    {'goi_bong_sung': 2, 'canh_chua_ca_loc': 2, 'ca_keo_nuong': 2},
    {'lau_mam': 1, 'ca_loc_nuong_trui': 2, 'goi_bong_sung': 1},
    {'lau_mam': 1, 'lau_ca_linh_dien_dien': 1, 'ca_loc_nuong_trui': 1},
]


def ingredients_for(dishes):
    out = {}
    for dish_id, portions in dishes.items():
        for kind, amount in DISHES[dish_id]['recipe'].items():
            out[kind] = out.get(kind, 0) + amount * portions
    return out


def upgrade_manifest(config):
    if not isinstance(config, dict) or not isinstance(config.get('tuning'), dict):
        raise ValueError('Manifest needs root object and tuning object.')
    if str(config.get('contract_version')) not in ('1.0', '1.1'):
        raise ValueError('Expected contract_version 1.0 or 1.1. Refusing unrelated manifest.')

    data = deepcopy(config)
    tuning = data['tuning']
    for section in ('gather', 'quan', 'menu', 'score'):
        if not isinstance(tuning.get(section), dict):
            raise ValueError(f'tuning.{section} must exist and be an object')

    data['contract_version'] = '1.1'
    tuning['tick_hz'] = 60

    gather = tuning['gather']
    gather.update({
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
            'species': {
                'ca_sau': {
                    'patrol_speed': 1.0, 'chase_speed': 3.0,
                    'detect_radius': 10.0, 'exit_radius': 16.0,
                    'depths': [10, 30], 'hit_radius': 1.5,
                    'recoil_ticks': 60, 'recoil_dist': 2.0,
                },
            },
            'spawns': [
                {'id': 'M1', 'kind': 'ca_sau', 'pos': [60, 24],
                 'waypoints': [[60, 24], [64, 24]], 'from_day': 1},
                {'id': 'M2', 'kind': 'ca_sau', 'pos': [85, 18],
                 'waypoints': [[85, 18], [89, 18]], 'from_day': 3},
            ],
            'invuln_ticks': 90, 'loss_ratio': 0.5,
        },
    })

    quan = tuning['quan']
    quan.update({
        'duration_s': 180,
        'bounds': {'x': [0, 16], 'z': [0, 10]},
        'start_pos': [8, 5], 'walk_speed': 4.0,
        'ramp_max_ticks': 6, 'interact_radius': 1.5,
        'stoves': [
            {'id': 'B1', 'pos': [2, 8]}, {'id': 'B2', 'pos': [5, 8]},
        ],
        'tables': [
            {'id': 'T1', 'pos': [9, 2]}, {'id': 'T2', 'pos': [13, 2]},
            {'id': 'T3', 'pos': [9, 6]}, {'id': 'T4', 'pos': [13, 6]},
        ],
        'first_customer_tick': 120, 'customer_interval_s': 15,
        'patience_s': 60, 'eat_s': 10, 'burn_s': None,
        'carry_limit': 1, 'tip_rate': 0.2,
        'tip_min_patience_ratio': 0.5, 'tip_reputation': 0.2,
        'left_reputation_delta': -0.5,
        'reputation_initial': 3.0, 'reputation_min': 0.0, 'reputation_max': 5.0,
    })

    tuning['menu'] = deepcopy(DISHES)
    tuning['score']['reputation_multiplier'] = 100
    tuning['day_plan'] = [
        {'day': day, 'dishes': deepcopy(dishes), 'ingredients': ingredients_for(dishes)}
        for day, dishes in enumerate(PLANS, start=1)
    ]
    tuning['shop'] = {
        'max_ticks': 600,
        'upgrades': {
            'oxygen': [
                {'level': 1, 'price': 200, 'oxygen_max_s': 45},
                {'level': 2, 'price': 400, 'oxygen_max_s': 60},
            ],
            'hp': [
                {'level': 1, 'price': 250, 'hp_max': 4},
                {'level': 2, 'price': 500, 'hp_max': 5},
            ],
        },
    }
    return data


def verify(out):
    t = out['tuning']
    assert out['contract_version'] == '1.1'
    assert len(t['gather']['nodes']) == 6
    assert set(t['gather']['fish_yield']) == {'ca_linh', 'ca_loc', 'ca_keo'}
    assert len(t['quan']['stoves']) == 2 and len(t['quan']['tables']) == 4
    assert len(t['menu']) == 6 and len(t['day_plan']) == 5
    assert all(p['ingredients'] == ingredients_for(p['dishes']) for p in t['day_plan'])
    assert t['day_plan'][3]['ingredients'] == {
        'ca_linh': 2, 'ca_keo': 1, 'keo_neo': 1,
        'bong_dien_dien': 1, 'ca_loc': 2, 'bong_sung': 2,
    }
    assert t['day_plan'][4]['ingredients'] == {
        'ca_linh': 5, 'ca_keo': 1, 'keo_neo': 1,
        'bong_dien_dien': 2, 'ca_loc': 1,
    }
    assert len(t['shop']['upgrades']) == 2


def main():
    ap = argparse.ArgumentParser(description='Generate TICKET-02 manifest from v1.0.')
    ap.add_argument('--manifest', type=Path, default=Path('game.contract.json'))
    ap.add_argument('--output', type=Path, default=Path('docs/contracts/game.contract.v1_1.proposed.json'))
    ap.add_argument('--apply', action='store_true', help='Replace manifest (backup made first).')
    args = ap.parse_args()

    source = args.manifest
    data = json.loads(source.read_text(encoding='utf-8'))
    upgraded = upgrade_manifest(data)
    verify(upgraded)
    output = source if args.apply else args.output
    if args.apply:
        backup = source.with_name(source.name + '.phase1.bak')
        if backup.exists():
            raise FileExistsError(f'Refusing to overwrite backup: {backup}')
        shutil.copy2(source, backup)
        print(f'Backup: {backup}')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(upgraded, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Created: {output}')
    print('Version: 1.1; 6 nodes; 3 fish species; 6 dishes; 2 stoves; 4 tables; 5 day plans; 2 upgrades.')
    print('Note: This script updates only the manifest. CLI, simulation, UI, and tests still need v1.1 implementation.')

if __name__ == '__main__':
    main()
