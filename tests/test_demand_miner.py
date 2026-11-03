"""Tests for Demand Miner — stdlib unittest (also runs under pytest)."""
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import demand_miner as dm  # noqa: E402

KEYWORDS = ["website", "web design", "site"]


def mention(text, **kw):
    m = {"source": "forum", "text": text, "url": "https://example.com/x",
         "author": "Tester", "engagement": 0, "date": "2026-11-03"}
    m.update(kw)
    return m


class ImportAndHelp(unittest.TestCase):
    def test_module_imports_and_has_version(self):
        self.assertTrue(dm.VERSION)
        spec = importlib.util.find_spec("demand_miner")
        self.assertIsNotNone(spec)

    def test_help_runs(self):
        r = subprocess.run([sys.executable, str(ROOT / "src" / "demand_miner.py"), "--help"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("--keywords", r.stdout)
        self.assertIn("Demand Miner", r.stdout)


class Scoring(unittest.TestCase):
    def test_off_niche_is_not_scored(self):
        self.assertIsNone(dm.score_mention("Looking for a plumber, any recommendations?", KEYWORDS))

    def test_strong_buyer_scores_high(self):
        r = dm.score_mention(
            "Looking for someone to build a website for my business — how much does it cost?",
            KEYWORDS)
        self.assertFalse(r["seller"])
        self.assertGreaterEqual(r["score"], 7)  # looking for 3 + how much 3 + my business 1 (+? if present)

    def test_seller_is_flagged(self):
        r = dm.score_mention(
            "We offer website design — DM me, our agency can help. Book a call!", KEYWORDS)
        self.assertTrue(r["seller"])

    def test_agency_seo_bait_is_flagged(self):
        r = dm.score_mention(
            "In this guide, our team explains website costs. Contact us for a free consultation.",
            KEYWORDS)
        self.assertTrue(r["seller"])

    def test_location_hint(self):
        self.assertEqual(dm.location_hint("Need a website designer near Kelowna please"), "Kelowna")
        self.assertEqual(dm.location_hint("Need a website designer please"), "")


class MineOnSample(unittest.TestCase):
    def test_bundled_sample_corpus(self):
        raw = json.loads((ROOT / "data" / "sample.json").read_text())
        result = dm.mine(raw["mentions"], KEYWORDS)
        self.assertEqual(result["scanned"], 5)
        self.assertEqual(result["sellers_filtered"], 1)
        self.assertEqual(result["off_niche"], 1)
        self.assertEqual(result["below_threshold"], 1)
        self.assertEqual(len(result["leads"]), 2)
        # ranked highest-first, every lead carries evidence + source
        self.assertGreaterEqual(result["leads"][0]["score"], result["leads"][1]["score"])
        for lead in result["leads"]:
            self.assertTrue(lead["quote"])
            self.assertTrue(lead["url"].startswith("https://"))
            self.assertTrue(lead["signals"])

    def test_cli_end_to_end_and_csv(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            csv_path = str(Path(td) / "leads.csv")
            r = subprocess.run([sys.executable, str(ROOT / "src" / "demand_miner.py"),
                                str(ROOT / "data" / "sample.json"),
                                "--keywords", "website,web design,site", "--csv", csv_path],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("LEADS: 2", r.stdout)
            self.assertIn("1 sellers filtered", r.stdout)
            rows = Path(csv_path).read_text().strip().splitlines()
            self.assertEqual(len(rows), 3)  # header + 2 leads


if __name__ == "__main__":
    unittest.main()
