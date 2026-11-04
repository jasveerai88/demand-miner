# Demand Miner

**Find the buyers hiding in public posts — free, offline, on your own machine.**

Lead tools charge ₹8,500+/mo to watch public posts for buying intent. This miner does the scoring part for free: feed it public mentions you captured (comments, forum posts, community threads) and it ranks real buyer intent, filters out the sellers — including agencies answering buyer questions as SEO bait — and prints a lead sheet where every lead carries its evidence quote and source link.

## Run it
```
python3 src/demand_miner.py your-captures.json --keywords website,"web design",site --csv leads.csv
```

## Use with AI agents

Add `--json` to print one JSON object (same counts, same ranked leads, same exit codes; errors come back as `{"error": ...}`):

```
python3 src/demand_miner.py your-captures.json --keywords website,"web design",site --json
```

Agents: read [SKILL.md](SKILL.md) first — commands, the full JSON schema, exit codes, and the honesty rules (a lead is a scored mention, not a verified buyer).

## Measured, not marketed
First version of this tool FAILED its own pre-registered accuracy test on real data (agencies beat its seller filter 3-to-2) — the failure and the fix are published in its lab notes. The current version re-ran the same data: on the verbatim raw-text corpus, every surviving lead (2 of 2) was a hand-verified real buyer; AI-summary captures stay unclean and are not a supported input. Yield depends on your captures; the miner's job is precision, and that part is proven.

## Why it's free
I build free, local-first tools for small creators and businesses from measured failure data. Sponsors keep them free and fund the next ones — GitHub Sponsors is LIVE: **[github.com/sponsors/jasveerai88](https://github.com/sponsors/jasveerai88)**.

MIT licensed. Python 3 stdlib only. Mining only — who you contact is your call.

## Real example

Run on the bundled sample corpus (`data/sample.json` — 5 mentions: 2 buyers, 1 seller, 1 off-niche, 1 casual mention):

```
$ python3 src/demand_miner.py data/sample.json --keywords website,"web design",site
DEMAND MINER v0.3.0 — niche: website, web design, site
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

## How matching and malformed mentions work

- **Keyword matching is word-boundary-aware.** A keyword only matches as a whole word (or whole phrase, for multi-word keywords like `web design`): `site` does **not** match inside "opposite", "parasite" or "sitemap". Matching is case-insensitive.
- **How malformed mentions are handled:** a mention that is not a JSON object, has no usable text, or carries a non-numeric `engagement` value (e.g. `"abc"` or a list) is **skipped and counted** — it never aborts the run. When any are skipped, the report prints a visible `Skipped N malformed mentions` line; valid mentions in the same file still process normally. Missing/empty `engagement` counts as 0.
- **No keywords, no run:** `--keywords ""` (or only commas/spaces) is an error with a non-zero exit code — the tool never prints a plausible-looking `LEADS: 0` report for an empty niche.

## Known limits

- **The seller filter is a heuristic and can misfire — in both directions.** It matches seller phrases like "dm me", "we offer" and "book a call". A genuine buyer who writes something like "dm me with your rates" will be filtered out as a seller, and a seller who avoids every listed phrase will slip through as a lead. Always read the evidence quote before treating a lead (or a filtered mention) as settled.
- **Word-boundary matching means inflections don't match:** keyword `website` does not match "websites", and `web design` does not match "web designer". List each form you care about as its own keyword.
- **Scoring is transparent rules, not a model.** The signal phrases and points are fixed lists in the source; a buyer who phrases intent in an unlisted way scores low or is missed. Yield depends on the quality of the mentions you feed it.

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
