# Changelog

All notable changes to Demand Miner are documented here.

## v0.2.2 — 2026-11-03

Mini-fix release from the delta re-audit:

- **Structural corpus errors are human-readable.** A corpus file missing the top-level `"mentions"` key previously failed with the terse `ERROR: 'mentions'` (a raw KeyError). A missing key, a `"mentions"` that isn't a list, or a top level that isn't an object/list now says what the file must look like — same error style as Payout Tracker. Per-mention problems are unchanged: still skipped and counted, never fatal.
- **Test hermeticity pinned.** The suite never writes into the pack's own tree (a stray `data/leads.csv` caused a transient failure when suites ran in parallel during the re-audit); all outputs go to temp dirs, and a regression test now proves a relative `--csv` lands in the caller's working directory, not the pack. The tool's normal CLI output behaviour is unchanged.
- Regression tests added; suite is now 22 tests.

## v0.2.1 — 2026-11-03

Bug-fix release from the adversarial QA audit (owner's bug-free production gate):

- **Keyword matching is now word-boundary-aware.** Keywords previously matched as raw substrings, so `site` fired inside "opposite", "parasite" and "sitemap" and produced false leads. Keywords (including multi-word phrases) now match only as whole words/phrases, case-insensitively. README sample run re-verified: same 2 leads, same scores (13 and 12), CSV identical.
- **Empty keywords are now a clean error.** `--keywords ""` (or only separators) previously printed a plausible `LEADS: 0` report; it now prints `ERROR:` and exits non-zero.
- **Malformed mentions no longer abort the run.** A mention that is not a JSON object, has no usable text, or carries a non-numeric `engagement` value is skipped and counted, and the report prints a `Skipped N malformed mentions` line when any occur. Valid mentions still process.
- README gained a "Known limits" section: the seller filter is a heuristic and can misfire (e.g. a genuine buyer writing "dm me with your rates" is filtered as a seller), and word-boundary matching means inflections like "websites" need their own keyword.
- Regression tests added for all three fixes (17 tests total, all passing).

## v0.2.0 — 2026-11-03

- First public release (MIT, Python 3 stdlib only, local-first).
- Renamed from demand-miner-lite before first publish (owner decision 2026-11-03).
- Seller filter redesigned after v0.1 failed its pre-registered accuracy test on real data (2026-11-01): agency/guide SEO-bait voice is now filtered; on the verbatim raw-text corpus every surviving lead (2 of 2) was a hand-verified real buyer.
- Includes `data/sample.json` and a test suite covering import, `--help`, scoring, seller filtering, and an end-to-end sample run.
- Sponsors is LIVE: https://github.com/sponsors/jasveerai88

## v0.1.0 — 2026-11-03

- Internal first version: buying-intent scoring + basic seller filter. Failed its own accuracy test (agencies beat the seller filter 3-to-2) — kept here for honesty; superseded by v0.2.0 above.
