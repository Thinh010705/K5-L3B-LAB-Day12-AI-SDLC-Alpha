"""Versioned file handoff checks for the Phase 3 integration boundary."""

import json
import os
import tempfile
import unittest
from pathlib import Path

from chonoi.errors import BadInput
from chonoi.inventory import KINDS_P2, read_inventory, write_inventory
from chonoi.freshness import validate_instances


class PhysicalInventoryTests(unittest.TestCase):
    def test_v12_round_trip_preserves_identity_freshness_and_id_order(self):
        items = [
            {"id": "I10", "kind": "ca_loc", "fresh": 29.999999999999996},
            {"id": "I2", "kind": "ca_linh", "fresh": 30.000000000000004},
            {"id": "I1", "kind": "ca_linh", "fresh": 0},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "stock.json"
            write_inventory(str(path), items, contract_version="1.2")
            self.assertEqual(read_inventory(str(path), contract_version="1.2"),
                             [items[2], items[1], items[0]])
            self.assertEqual(json.loads(path.read_text()),
                             {"items": [items[2], items[1], items[0]]})
            self.assertEqual(list(Path(tmp).iterdir()), [path])

    def test_v12_rejects_count_schema_and_invalid_instances(self):
        valid = {"id": "I1", "kind": "ca_linh", "fresh": 100}
        invalid = [
            {}, {"ca_linh": 1}, [valid, valid],
            [{**valid, "id": ""}], [{**valid, "kind": "unknown"}],
            [{**valid, "fresh": -0.01}], [{**valid, "fresh": 100.01}],
            [{**valid, "fresh": True}], [{**valid, "fresh": float("nan")}],
            [{**valid, "fresh": float("inf")}], [{**valid, "extra": 1}],
        ]
        for value in invalid:
            with self.subTest(value=value):
                with self.assertRaises(BadInput):
                    validate_instances(value, KINDS_P2)

    def test_v12_invalid_file_leaves_existing_target_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, target = Path(tmp) / "bad.json", Path(tmp) / "target.json"
            target.write_text("sentinel\n")
            for data in ({"items": {"ca_linh": 1}},
                         {"items": [{"id": "I1", "kind": "ca_linh", "fresh": 101}]},
                         {"items": [], "extra": 1}):
                source.write_text(json.dumps(data))
                with self.assertRaises(BadInput):
                    read_inventory(str(source), contract_version="1.2")
                self.assertEqual(target.read_text(), "sentinel\n")
            with self.assertRaises(BadInput):
                write_inventory(str(target), {"ca_linh": 1}, contract_version="1.2")
            self.assertEqual(target.read_text(), "sentinel\n")
            self.assertFalse(any(name.startswith(".inv-") for name in os.listdir(tmp)))

    def test_legacy_file_requires_legacy_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "stock.json"
            write_inventory(str(path), {"ca_linh": 2}, contract_version="1.1")
            self.assertEqual(read_inventory(str(path), contract_version="1.1"), {"ca_linh": 2})
            with self.assertRaises(BadInput):
                read_inventory(str(path), contract_version="1.2")


if __name__ == "__main__":
    unittest.main()
