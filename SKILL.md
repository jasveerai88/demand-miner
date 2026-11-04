---
name: demand-miner
description: Rank buyer intent in captured public mentions, filtering out sellers, with an evidence quote per lead. Use when turning a local JSON corpus of public posts/comments into a lead sheet for a niche — mining only, never outreach.
---

# Demand Miner — agent skill

## Purpose

Reads a local JSON corpus of public mentions (posts/comments the user
captured) and scores **buying intent** with transparent, fixed rules:
strong-intent phrases, price questions, pain with a current provider, and
business ownership. Sellers — including agencies answering buyer questions
as SEO bait — are filtered out. Every surviving lead carries its evidence
quote and source URL.

## When to use / not use

Use when:
- Mining a corpus of public mentions for buyers in a niche defined by
  comma-separated keywords (e.g. `website,"web design",site`).
- Producing a ranked lead sheet or a leads CSV from captured data.

Do NOT use when:
- Scraping or fetching posts — the tool is offline and mines only what it
  is handed. Capturing mentions is a separate step.
- Contacting anyone — the tool never reaches out. Outreach is a separate,
  approved act.
- The corpus is AI-summarised text — summaries are an unsupported input
  (they distort the verbatim signals the scorer relies on); use raw text.

## Commands

```bash
# Human-readable lead sheet
python3 src/demand_miner.py data/sample.json --keywords website,"web design",site

# Machine-readable output for agents (one JSON object on stdout)
python3 src/demand_miner.py data/sample.json --keywords website,"web design",site --json

# Also write the leads CSV; tune the lead bar (default min score 4)
python3 src/demand_miner.py captures.json --keywords website,site --min-score 6 --csv leads.csv --json
```

Corpus shape: `{"mentions": [{"source", "text", "url", "author",
"engagement", "date"}]}` (a bare list of mentions also works).

## Output JSON schema (`--json`)

Top level:
- `tool` — `"demand-miner"`
- `version` — tool version string
- `keywords` — the niche keywords used (list of strings)
- `min_score` — the lead bar applied
- `scanned` — mentions in the corpus
- `sellers_filtered` — mentions classified as sellers
- `off_niche` — mentions with no whole-word keyword match
- `below_threshold` — on-niche, non-seller mentions under the lead bar
- `skipped_malformed` — mentions skipped (not an object, no usable text,
  or non-numeric `engagement`); malformed mentions never abort a run
- `leads_count` — number of leads
- `leads` — ranked highest score first; each lead:
  - `score` — intent score (signal points + engagement bonus)
  - `author`, `source`, `location` (hint extracted from the text, may be `""`)
  - `quote` — the evidence text (whitespace-collapsed, max 160 chars)
  - `url` — source link
  - `signals` — list of matched signal phrases
- `warnings` — list of strings (e.g. the skipped-malformed notice)

On error, stdout is a single object: `{"error": "<message>"}` and the exit
code is unchanged. Never a traceback.

## Exit codes

- `0` — lead sheet produced (possibly with zero leads).
- `1` — error: file not found, malformed JSON, structural problem with the
  corpus (the message says what the file must look like), or no usable
  keywords.

## Limits & honesty rules the agent must respect

- **A lead is a scored mention, not a verified buyer.** The seller filter
  is a heuristic and misfires both ways — a genuine buyer writing "dm me
  with your rates" is filtered as a seller; a seller avoiding every listed
  phrase slips through. Always read the `quote` before treating a lead as
  real, and say the list is machine-mined, not hand-verified.
- **Matching is whole-word only.** Keyword `website` does not match
  "websites"; `web design` does not match "web designer". Include each
  form you care about as its own keyword, or accept the narrower yield.
- **Scoring is fixed rules, not a model.** Buyers who phrase intent in
  unlisted ways score low or are missed. Do not inflate a lead's score or
  present the ranking as a quality guarantee.
- **Precision over yield.** This tool's proven property is precision on
  verbatim raw-text corpora. Do not feed it AI summaries and do not relax
  `--min-score` silently to manufacture more leads.
- Mining only: the tool stores nothing except a CSV you explicitly ask
  for, and sends nothing anywhere.
