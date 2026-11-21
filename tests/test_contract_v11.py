"""Test versioned loading and v1.1 data validation without activating v1.1 runtime."""
from __future__ import annotations
import copy
import json
import os
import tempfile
import unittest
from pathlib import Path

from chonoi.contract import load_contract
from chonoi.errors import BadInput

PROPOSED = Path(__file__).resolve().parents[1] / 'docs/contracts/game.contract.v1_1.proposed.json'


class ContractVersion11(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = json.loads(PROPOSED.read_text(encoding='utf-8'))

    def load(self, data):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'manifest.json'
            path.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
            return load_contract(path)

    def bad(self, mutate, message):
        data = copy.deepcopy(self.source)
        mutate(data)
        with self.assertRaisesRegex(BadInput, message):
            self.load(data)

    def test_v11_proposed_is_loadable(self):
        self.assertEqual(self.load(self.source)['contract_version'], '1.1')

    def test_v10_validation_is_still_available(self):
        fixture = (
            Path(__file__).resolve().parent
            / "fixtures/game.contract.v1_0.json"
        )
        loaded = load_contract(fixture)
        self.assertEqual(loaded["contract_version"], "1.0")

    def test_default_manifest_is_loadable(self):
        loaded = load_contract()
        self.assertIn(str(loaded['contract_version']), ('1.0', '1.1', '1.2', '1.3'))

    def test_unknown_version_is_rejected(self):
        self.bad(lambda d: d.update(contract_version='9.9'), 'contract_version')

    def test_keo_neo_wrong_kind_is_rejected(self):
        self.bad(lambda d: d['tuning']['gather']['nodes'][4].update(kind='unknown'), 'nodes')

    def test_fish_initial_boolean_is_rejected(self):
        self.bad(lambda d: d['tuning']['gather'].update(fish_initial=True), 'fish_initial')

    def test_spawn_depth_out_of_species_bounds_is_rejected(self):
        self.bad(lambda d: d['tuning']['gather']['fish_spawn_depths'].update(ca_keo=[10, 27]), 'fish_spawn_depths')

    def test_monster_duplicate_id_is_rejected(self):
        self.bad(lambda d: d['tuning']['gather']['monsters']['spawns'][1].update(id='M1'), 'monsters.spawns')

    def test_day_plan_ingredient_mismatch_is_rejected(self):
        self.bad(lambda d: d['tuning']['day_plan'][0]['ingredients'].update(ca_loc=4), 'day_plan')

    def test_shop_negative_price_is_rejected(self):
        self.bad(lambda d: d['tuning']['shop']['upgrades']['hp'][0].update(price=-1), 'price')

    def test_wrong_menu_recipe_id_is_rejected(self):
        self.bad(lambda d: d['tuning']['menu']['lau_mam']['recipe'].update(not_an_ingredient=1), 'recipe')

    def test_v13_loaded_successfully(self):
        c = load_contract()
        self.assertEqual(c["contract_version"], "1.3")
        self.assertTrue(c.get("bench_cmd"))
        self.assertTrue(c.get("soak_cmd"))

    def test_v13_missing_bench_cmd_is_rejected(self):
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json", encoding="utf-8") as f:
            c = copy.deepcopy(self.source)
            c["contract_version"] = "1.3"
            c["soak_cmd"] = "python3 -m chonoi.soak"
            json.dump(c, f)
            name = f.name
        try:
            with self.assertRaises(BadInput):
                load_contract(name)
        finally:
            os.unlink(name)

    def test_v13_missing_soak_cmd_is_rejected(self):
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json", encoding="utf-8") as f:
            c = copy.deepcopy(self.source)
            c["contract_version"] = "1.3"
            c["bench_cmd"] = "python3 -m chonoi.bench"
            json.dump(c, f)
            name = f.name
        try:
            with self.assertRaises(BadInput):
                load_contract(name)
        finally:
            os.unlink(name)


if __name__ == '__main__':
    unittest.main()
