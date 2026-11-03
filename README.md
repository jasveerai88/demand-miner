# Demand Miner

**Find the buyers hiding in public posts — free, offline, on your own machine.**

Lead tools charge ₹8,500+/mo to watch public posts for buying intent. This miner does the scoring part for free: feed it public mentions you captured (comments, forum posts, community threads) and it ranks real buyer intent, filters out the sellers — including agencies answering buyer questions as SEO bait — and prints a lead sheet where every lead carries its evidence quote and source link.

## Run it
```
python3 src/demand_miner.py your-captures.json --keywords website,"web design",site --csv leads.csv
```

## Measured, not marketed
First version of this tool FAILED its own pre-registered accuracy test on real data (agencies beat its seller filter 3-to-2) — the failure and the fix are published in its lab notes. The current version re-ran the same data: on the verbatim raw-text corpus, every surviving lead (2 of 2) was a hand-verified real buyer; AI-summary captures stay unclean and are not a supported input. Yield depends on your captures; the miner's job is precision, and that part is proven.

## Why it's free
I build free, local-first tools for small creators and businesses from measured failure data. Sponsors keep them free and fund the next ones — GitHub Sponsors is LIVE: **[github.com/sponsors/jasveerai88](https://github.com/sponsors/jasveerai88)**.

MIT licensed. Python 3 stdlib only. Mining only — who you contact is your call.

## Real example

Run on the bundled sample corpus (`data/sample.json` — 5 mentions: 2 buyers, 1 seller, 1 off-niche, 1 casual mention):

```
$ python3 src/demand_miner.py data/sample.json --keywords website,"web design",site
DEMAND MINER v0.2.0 — niche: website, web design, site
Scanned 5 mentions · 1 sellers filtered · 1 off-niche · 1 below the lead bar
LEADS: 2

1. [score 13] Harpreet · community · near Kelowna
   "I need help with my website — my current designer ghosted me and I am frustrated. Need someone reliable near Kelowna?"
   signals: frustrated, ghosted, my current designer, need help with, need someone, question · https://example.com/post/2
2. [score 12] Maya · forum
   "Looking for someone to build a website for my business — how much does it cost? Any recommendations?"
   signals: any recommendations, how much, looking for, my business, question · https://example.com/post/1

Every lead carries its evidence quote + source. Outreach is a separate, approved act — this sheet only mines.
```

The seller (an agency pitching its own services) is filtered out, and both surviving leads carry their evidence quote and source link.

## Privacy
- What it touches: only the corpus JSON file you pass on the command line.
- What it stores: nothing, unless you pass `--csv` — then it writes that one CSV where you told it to.
- What it sends: nothing. No scraping, no logins, no network, no tracking.
- Mining only: the tool never contacts anyone.
- Delete the tool folder and everything is gone.

## Tests
```
python3 -m unittest discover -s tests -v
```
(Stdlib only — no dependencies. The tests also run under pytest.)
