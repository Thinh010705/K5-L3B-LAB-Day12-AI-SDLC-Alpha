"""Test lát CLI --days, chưa khẳng định Day runtime đã chạy."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DayCliP2Tests(unittest.TestCase):
    def invoke(self, mode="day", *, days=None):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.jsonl"
            argv = [
                sys.executable,
                "-m",
                "chonoi.headless",
                "--mode",
                mode,
                "--seed",
                "1",
                "--ticks",
                "0",
                "--out",
                str(out),
            ]
            if days is not None:
                argv += ["--days", str(days)]
            p = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True)
            return p, out.exists()

    def test_help_declares_days(self):
        p = subprocess.run(
            [sys.executable, "-m", "chonoi.headless", "--help"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("--days", p.stdout)

    def test_invalid_days_zero(self):
        p, created = self.invoke(days=0)
        self.assertEqual(p.returncode, 2)
        self.assertIn("--days phải thuộc", p.stderr)
        self.assertFalse(created)

    def test_invalid_days_six(self):
        p, created = self.invoke(days=6)
        self.assertEqual(p.returncode, 2)
        self.assertFalse(created)

    def test_days_not_allowed_in_gather(self):
        p, created = self.invoke(mode="gather", days=1)
        self.assertEqual(p.returncode, 2)
        self.assertIn("--days chỉ dùng", p.stderr)
        self.assertFalse(created)

    def test_days_not_allowed_in_quan(self):
        p, created = self.invoke(mode="quan", days=1)
        self.assertEqual(p.returncode, 2)
        self.assertFalse(created)

    def test_day_requires_contract_v11(self):
        p, created = self.invoke(days=1)
        self.assertEqual(p.returncode, 2)
        self.assertNotIn("unrecognized arguments", p.stderr)
        self.assertIn("yêu cầu contract_version 1.1", p.stderr)
        self.assertFalse(created)

    def test_gather_v10_still_runs(self):
        p, created = self.invoke(mode="gather")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertTrue(created)


if __name__ == "__main__":
    unittest.main()
