"""Alpha / Integrator: additional black-box integration checks for contract v1.0.

Run from the repository root:
    PYTHONPATH=tests:. python3 -m unittest discover -s tests -p 'test_integration_alpha.py' -v

Use the team's configured headless_cmd (via existing tests/helpers.py), not internal sim APIs.
No network or third-party dependencies are required.
"""

import json
import os
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


class AlphaIntegrationContract(unittest.TestCase):
    @staticmethod
    def _fixture(w):
        scenario = write_json(
            w.path('gather_scenario.json'),
            {'gather': {'hold': ['ca_loc', 'bong_sung', 'bong_sung', 'ca_linh']}},
        )
        inputs = write_json(
            w.path('gather_inputs.json'),
            frames({'tick': 0, 'interact': True}),
        )
        return scenario, inputs

    def test_round_trip_inventory_event_and_quan_snapshot(self):
        """Gather dock → gather_end → inventory JSON → Quan tick-0 stock."""
        with Workdir() as w:
            scenario, inputs = self._fixture(w)
            inv, g_out, q_out = (w.path(x) for x in ('inventory.json', 'g.jsonl', 'q.jsonl'))
            code, stderr = run_headless('--mode', 'gather', '--seed', '11', '--ticks', '1',
                                         '--scenario', scenario, '--inputs', inputs,
                                         '--inventory-out', inv, '--out', g_out)
            self.assertEqual(code, 0, stderr)
            self.assertTrue(os.path.isfile(inv))
            with open(inv, encoding='utf-8') as f:
                saved = json.load(f)
            expected = {'items': {'bong_sung': 2, 'ca_linh': 1, 'ca_loc': 1}}
            self.assertEqual(saved, expected)
            g_rows = read_jsonl(g_out)
            self.assertEqual(g_rows[0]['type'], 'snapshot')
            self.assertEqual(g_rows[0]['tick'], 0)
            ending = events(g_rows, 'gather_end')
            self.assertEqual(len(ending), 1)
            self.assertEqual(ending[0]['data']['reason'], 'docked')
            self.assertEqual(ending[0]['data']['inventory'], saved)
            self.assertEqual(g_rows[-1]['type'], 'end')
            self.assertEqual(g_rows[-1]['reason'], 'docked')

            code, stderr = run_headless('--mode', 'quan', '--seed', '11', '--ticks', '0',
                                         '--inventory', inv, '--out', q_out)
            self.assertEqual(code, 0, stderr)
            q_rows = read_jsonl(q_out)
            self.assertEqual(q_rows[0]['type'], 'snapshot')
            self.assertEqual(snapshots(q_rows)[0]['stock'], expected['items'])
            self.assertEqual(q_rows[-1]['type'], 'end')

    def test_tick_limit_does_not_create_or_overwrite_inventory(self):
        """--ticks limit alone must NOT trigger inventory write."""
        with Workdir() as w:
            absent_path = w.path('absent.json')
            code, stderr = run_headless('--mode', 'gather', '--seed', '11', '--ticks', '0',
                                         '--inventory-out', absent_path, '--out', w.path('g0.jsonl'))
            self.assertEqual(code, 0, stderr)
            self.assertFalse(os.path.exists(absent_path))

            path = w.path('existing.json')
            sentinel = b'ORIGINAL_DATA_MUST_REMAIN_UNCHANGED\n'
            with open(path, 'wb') as f:
                f.write(sentinel)
            code, stderr = run_headless('--mode', 'gather', '--seed', '11', '--ticks', '2',
                                         '--inventory-out', path, '--out', w.path('g2.jsonl'))
            self.assertEqual(code, 0, stderr)
            with open(path, 'rb') as f:
                self.assertEqual(f.read(), sentinel)

    def test_invalid_inventory_fails_before_output_is_written(self):
        """Extra keys, unknown IDs, negatives, boolean and non-integer counts are invalid."""
        invalid = [
            {'items': {'ca_loc': -1}},
            {'items': {'ca_loc': True}},
            {'items': {'ca_loc': 1.5}},
            {'items': {'unknown_fish': 1}},
            {'items': {'ca_loc': 1}, 'version': 1},
            {'stock': {'ca_loc': 1}},
        ]
        for index, value in enumerate(invalid):
            with self.subTest(case=index), Workdir() as w:
                inv = write_json(w.path('invalid.json'), value)
                out = w.path('quan.jsonl')
                code, _ = run_headless('--mode', 'quan', '--seed', '11', '--ticks', '0',
                                       '--inventory', inv, '--out', out)
                self.assertEqual(code, 2, value)
                self.assertFalse(os.path.exists(out), value)

    def test_stock_conflict_and_wrong_mode_flags_rejected(self):
        with Workdir() as w:
            inv = write_json(w.path('inv.json'), {'items': {'ca_loc': 1}})
            scenario = write_json(w.path('quan_scenario.json'), {'quan': {'stock': {'ca_linh': 2}}})
            cases = [
                ('--mode', 'quan', '--seed', '11', '--ticks', '0', '--inventory', inv,
                 '--scenario', scenario),
                ('--mode', 'gather', '--seed', '11', '--ticks', '0', '--inventory', inv),
                ('--mode', 'quan', '--seed', '11', '--ticks', '0', '--inventory-out', w.path('out.json')),
            ]
            for index, args in enumerate(cases):
                with self.subTest(case=index):
                    target = w.path(f'bad_{index}.jsonl')
                    code, _ = run_headless(*args, '--out', target)
                    self.assertEqual(code, 2)
                    self.assertFalse(os.path.exists(target))

    def test_same_seed_same_input_byte_identical_round_trip(self):
        """Both outputs, including serialized inventory, should be byte-stable."""
        with Workdir() as w:
            scenario, inputs = self._fixture(w)
            records = []
            for index in (1, 2):
                inv, g_out, q_out = (w.path(f'{index}_{x}') for x in ('inv.json', 'g.jsonl', 'q.jsonl'))
                code, stderr = run_headless('--mode', 'gather', '--seed', '99', '--ticks', '1',
                                             '--scenario', scenario, '--inputs', inputs,
                                             '--inventory-out', inv, '--out', g_out)
                self.assertEqual(code, 0, stderr)
                code, stderr = run_headless('--mode', 'quan', '--seed', '99', '--ticks', '4',
                                             '--inventory', inv, '--out', q_out)
                self.assertEqual(code, 0, stderr)
                record = []
                for path in (inv, g_out, q_out):
                    with open(path, 'rb') as f:
                        record.append(f.read())
                records.append(record)
            self.assertEqual(records[0], records[1])

    def test_recipes_and_default_gather_kinds_are_compatible(self):
        """Cross-module static compatibility check, without modifying game rules."""
        from chonoi.inventory import KINDS_P1
        with open('game.contract.json', encoding='utf-8') as f:
            config = json.load(f)
        tuning = config['tuning']
        available = set(KINDS_P1)
        self.assertTrue(available)
        for node in tuning['gather']['nodes']:
            self.assertIn(node['kind'], available)
        for fish in tuning['gather']['fish_initial']:
            self.assertIn(fish['kind'], available)
        for dish, detail in tuning['menu'].items():
            self.assertTrue(detail['recipe'], dish)
            for ingredient, count in detail['recipe'].items():
                self.assertIn(ingredient, available, dish)
                self.assertIs(type(count), int, dish)
                self.assertGreater(count, 0, dish)


if __name__ == '__main__':
    unittest.main()
