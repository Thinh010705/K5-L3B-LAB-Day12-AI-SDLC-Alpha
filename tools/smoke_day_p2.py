#!/usr/bin/env python3
"""Short integration smoke for P2 Day -> Shop using proposed v1.1 manifest.

It deliberately does not modify game.contract.json. NOT full P2 acceptance.
"""
import argparse
import json
from pathlib import Path

from chonoi.contract import load_contract
from chonoi.day import run_day


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', default='docs/contracts/game.contract.v1_1.proposed.json')
    parser.add_argument('--out', default='docs/proof/phase-2/smoke-day-cycle.jsonl')
    args = parser.parse_args()
    config = load_contract(args.manifest)
    assert config['contract_version'] == '1.1'
    scenario = {
        'day': {'money': 200, 'earned': 200},
        'gather': {'hold': ['ca_loc', 'bong_sung', 'bong_sung'], 'random_fish': False},
        'quan': {'time_left_ticks': 1, 'random_customers': False},
    }
    frames = [
        {'tick': 0, 'interact': True},
        {'tick': 1, 'interact': False},
        {'tick': 2, 'buy': 'oxygen', 'shop_done': True},
        {'tick': 3, 'interact': True, 'shop_done': False},
        {'tick': 4, 'interact': False},
        {'tick': 5, 'shop_done': True},
    ]
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    run_day(config['tuning'], scenario, 42, frames, 12, path, 1, days=2)
    rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
    names = [r['name'] for r in rows if r['type'] == 'event']
    end = rows[-1]
    assert names.count('day_start') == 2, names
    assert names.count('gather_end') == 2, names
    assert names.count('quan_end') == 2, names
    assert names.count('shop_end') == 2, names
    assert names.count('bought') == 1, names
    assert end['reason'] == 'days_complete' and end['days_completed'] == 2, end
    second_day = next(r for r in rows if r['type'] == 'snapshot' and r['day'] == 2)
    assert second_day['active_upgrades'] == {'oxygen': 1}, second_day
    assert second_day['player']['oxygen_max_ticks'] == 2700, second_day
    assert end['earned'] == 200 and end['money'] == 0, end
    print(f"PASS: Day/Shop 2 days, purchase next-day activation, inventory handoff, {path}")
    print("NOTE: Does NOT cover moving fish, monsters, UI, or full v1.1 acceptance")


if __name__ == '__main__':
    main()
