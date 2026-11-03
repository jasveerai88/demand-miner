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


class WordBoundaryMatching(unittest.TestCase):
    """Regression (v0.2.1, D1): keywords matched as raw substrings, so
    `site` fired inside "opposite" / "parasite" / "sitemap"."""

    def test_keyword_inside_other_word_is_off_niche(self):
        for text in ("Looking for the opposite of a boring design, any recommendations?",
                     "Need someone to remove a parasite problem, who can help?",
                     "Can anyone fix my sitemap file, need help with it?"):
            self.assertIsNone(dm.score_mention(text, ["site"]), text)

    def test_standalone_keyword_still_matches_case_insensitively(self):
        r = dm.score_mention("Looking for someone to build my SITE, any recommendations?", ["site"])
        self.assertIsNotNone(r)

    def test_multiword_phrase_needs_boundaries_at_both_ends(self):
        self.assertIsNotNone(dm.score_mention(
            "Looking for web design help for my business", ["web design"]))
        # "web design" must not match inside "web designer"
        self.assertIsNone(dm.score_mention(
            "I am a web designer portfolio showcase", ["web design"]))

    def test_mine_does_not_turn_substring_mentions_into_leads(self):
        mentions = [mention("Looking for help, the opposite of my current site, "
                            "my current designer ghosted me, I am frustrated?",
                            engagement=200)]
        result = dm.mine(mentions, ["website", "web design"])
        # 'site' is not a keyword here and 'website' is absent as a word:
        # the mention must be off-niche, not a lead.
        self.assertEqual(result["off_niche"], 1)
        self.assertEqual(result["leads"], [])


class EmptyKeywords(unittest.TestCase):
    """Regression (v0.2.1, D2): --keywords "" printed a plausible LEADS: 0."""

    def _run(self, keywords_arg):
        return subprocess.run(
            [sys.executable, str(ROOT / "src" / "demand_miner.py"),
             str(ROOT / "data" / "sample.json"), "--keywords", keywords_arg],
            capture_output=True, text=True)

    def test_empty_keywords_is_a_clean_error(self):
        for arg in ("", "   ", ",,,", " , , "):
            r = self._run(arg)
            self.assertNotEqual(r.returncode, 0, arg)
            self.assertIn("ERROR:", r.stdout, arg)
            self.assertNotIn("LEADS:", r.stdout, arg)


class MalformedMentions(unittest.TestCase):
    """Regression (v0.2.1, D3): one malformed mention aborted the run.
    Policy: malformed mentions are SKIPPED and counted (see README)."""

    GOOD = "Looking for someone to build a website for my business — how much does it cost? Any recommendations?"

    def test_malformed_mentions_are_skipped_not_fatal(self):
        mentions = [
            mention(self.GOOD, engagement=25),
            mention(self.GOOD, engagement="abc"),        # non-numeric engagement
            mention(self.GOOD, engagement=[1, 2, 3]),    # engagement as a list
            "this mention is not a dict at all",         # non-dict entry
            42,                                          # non-dict entry
        ]
        result = dm.mine(mentions, KEYWORDS)
        self.assertEqual(result["skipped_malformed"], 4)
        self.assertEqual(len(result["leads"]), 1)  # the valid mention still leads

    def test_render_shows_skipped_line_only_when_nonzero(self):
        bad = dm.mine([mention(self.GOOD), "junk"], KEYWORDS)
        self.assertIn("Skipped 1 malformed mentions", dm.render(bad, KEYWORDS))
        clean = dm.mine([mention(self.GOOD)], KEYWORDS)
        self.assertNotIn("malformed", dm.render(clean, KEYWORDS))

    def test_cli_survives_malformed_corpus(self):
        import tempfile
        corpus = {"mentions": [
            dict(mention(self.GOOD, engagement=25)),
            dict(mention(self.GOOD, engagement="abc")),
            "not-a-dict",
        ]}
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "corpus.json"
            p.write_text(json.dumps(corpus))
            r = subprocess.run([sys.executable, str(ROOT / "src" / "demand_miner.py"),
                                str(p), "--keywords", "website,web design,site"],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("LEADS: 1", r.stdout)
            self.assertIn("Skipped 2 malformed mentions", r.stdout)


class StructuralErrors(unittest.TestCase):
    """Regression (v0.2.2): a corpus missing the top-level "mentions" key
    produced the terse `ERROR: 'mentions'` (a raw KeyError). Structural
    problems now say what the file must look like — same style as
    payout-tracker's extract(). Per-mention problems stay skip-and-count
    (see MalformedMentions); only the container shape is an error."""

    def _run(self, text):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "corpus.json"
            p.write_text(text)
            return subprocess.run([sys.executable, str(ROOT / "src" / "demand_miner.py"),
                                   str(p), "--keywords", "website"],
                                  capture_output=True, text=True)

    def test_missing_mentions_key(self):
        with self.assertRaises(ValueError) as ctx:
            dm.extract_mentions({"posts": []})
        self.assertIn('"mentions"', str(ctx.exception))
        r = self._run('{"posts": []}')
        self.assertEqual(r.returncode, 1)
        self.assertIn("ERROR:", r.stdout)
        self.assertIn('has no "mentions" list', r.stdout)
        self.assertNotIn("ERROR: 'mentions'", r.stdout)

    def test_mentions_not_a_list(self):
        for bad in ('{"mentions": "nope"}', '{"mentions": {"a": 1}}', '{"mentions": 5}'):
            r = self._run(bad)
            self.assertEqual(r.returncode, 1, bad)
            self.assertIn('"mentions" must be a list', r.stdout, bad)

    def test_top_level_not_object_or_list(self):
        r = self._run('"just a string"')
        self.assertEqual(r.returncode, 1)
        self.assertIn('must be a JSON object with a "mentions" list', r.stdout)

    def test_bare_list_still_accepted(self):
        self.assertEqual(dm.extract_mentions([{"text": "x"}]), [{"text": "x"}])
        r = self._run(json.dumps([mention(MalformedMentions.GOOD)]))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("LEADS: 1", r.stdout)


class TestHermeticity(unittest.TestCase):
    """Regression (v0.2.2): the suite must never write into the pack's own
    tree — two suites running in parallel collided over a stray
    data/leads.csv during the delta re-audit. All file outputs go to
    temp dirs; a relative --csv resolves against the caller's CWD."""

    def test_relative_csv_lands_in_caller_cwd_not_the_pack(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            r = subprocess.run([sys.executable, str(ROOT / "src" / "demand_miner.py"),
                                str(ROOT / "data" / "sample.json"),
                                "--keywords", "website,web design,site",
                                "--csv", "leads.csv"],
                               capture_output=True, text=True, cwd=td)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertTrue((Path(td) / "leads.csv").exists())
        self.assertFalse((ROOT / "data" / "leads.csv").exists())
        self.assertFalse((ROOT / "leads.csv").exists())


if __name__ == "__main__":
    unittest.main()
