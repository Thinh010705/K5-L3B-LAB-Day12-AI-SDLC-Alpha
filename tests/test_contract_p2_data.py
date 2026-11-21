"""Offline v1.1 MANIFEST tests; do not import chonoi or change P1 runtime.

These tests test the proposed data only, not functionality of mode day.
"""
import copy
import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
CHECKER = ROOT / 'tools' / 'check_contract_p2.py'
SPEC = importlib.util.spec_from_file_location('p2_contract_auditor', CHECKER)
AUDITOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDITOR)
MANIFEST = ROOT / 'docs' / 'contracts' / 'game.contract.v1_1.proposed.json'


class Phase2ManifestData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not MANIFEST.is_file():
            raise AssertionError('Missing proposed manifest: ' + str(MANIFEST))
        cls.valid = json.loads(MANIFEST.read_text(encoding='utf-8'))

    def test_proposed_manifest_matches_ticket02(self):
        self.assertEqual([], AUDITOR.audit(self.valid))

    def test_detects_wrong_contract_version(self):
        broken = copy.deepcopy(self.valid)
        broken['contract_version'] = '1.0'
        self.assertTrue(any('contract_version' in x for x in AUDITOR.audit(broken)))

    def test_detects_wrong_fish_yield(self):
        broken = copy.deepcopy(self.valid)
        broken['tuning']['gather']['fish_yield']['ca_keo'] = 1
        self.assertTrue(any('fish_yield' in x for x in AUDITOR.audit(broken)))

    def test_detects_wrong_new_node_kind(self):
        broken = copy.deepcopy(self.valid)
        broken['tuning']['gather']['nodes'][4]['kind'] = 'bong_sung'
        self.assertTrue(any('nodes' in x for x in AUDITOR.audit(broken)))

    def test_detects_wrong_d4_ingredient_plan(self):
        broken = copy.deepcopy(self.valid)
        broken['tuning']['day_plan'][3]['ingredients']['ca_loc'] = 3
        self.assertTrue(any('day_plan[3].ingredients' in x for x in AUDITOR.audit(broken)))

    def test_detects_wrong_shop_upgrade_price(self):
        broken = copy.deepcopy(self.valid)
        broken['tuning']['shop']['upgrades']['oxygen'][0]['price'] = 199
        self.assertTrue(any('shop.upgrades' in x for x in AUDITOR.audit(broken)))

    def test_detects_wrong_menu_recipe(self):
        broken = copy.deepcopy(self.valid)
        broken['tuning']['menu']['lau_mam']['recipe']['ca_keo'] = 2
        self.assertTrue(any('menu.lau_mam' in x for x in AUDITOR.audit(broken)))

    def test_detects_missing_monster_spawn(self):
        broken = copy.deepcopy(self.valid)
        broken['tuning']['gather']['monsters']['spawns'].pop()
        self.assertTrue(any('monsters' in x for x in AUDITOR.audit(broken)))


if __name__ == '__main__':
    unittest.main()
