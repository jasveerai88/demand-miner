# Changelog

All notable changes to Demand Miner are documented here.

## v0.2.0 — 2026-11-03

- First public release (MIT, Python 3 stdlib only, local-first).
- Renamed from demand-miner-lite before first publish (owner decision 2026-11-03).
- Seller filter redesigned after v0.1 failed its pre-registered accuracy test on real data (2026-11-01): agency/guide SEO-bait voice is now filtered; on the verbatim raw-text corpus every surviving lead (2 of 2) was a hand-verified real buyer.
- Includes `data/sample.json` and a test suite covering import, `--help`, scoring, seller filtering, and an end-to-end sample run.
- Sponsors is LIVE: https://github.com/sponsors/jasveerai88

## v0.1.0 — 2026-11-03

- Internal first version: buying-intent scoring + basic seller filter. Failed its own accuracy test (agencies beat the seller filter 3-to-2) — kept here for honesty; superseded by v0.2.0 above.
