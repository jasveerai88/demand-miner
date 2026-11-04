#!/usr/bin/env python3
"""
Demand Miner v0.3.0 — turn captured public mentions into ranked buyer leads.

The free answer to ₹8,500+/mo lead tools: you bring mentions captured from
public posts/comments (social search, comment exports, forum threads); the
miner scores BUYING INTENT with transparent rules, filters out sellers and
spam, and prints a lead sheet where every lead carries its evidence quote
and source URL. No scraping, no logins, no outreach — mining only.
Local, offline, Python 3 stdlib only. Spend: none.

Usage:
  python3 demand_miner.py CORPUS.json --keywords website,"web design",site [--min-score 4] [--csv leads.csv] [--json]
With --json, one JSON object is printed instead of the lead sheet
(same counts, same leads, same exit codes; errors become {"error": ...}).
Corpus: {"mentions":[{"source","text","url","author","engagement","date"}]}
Exit codes: 0 ok, 1 error.
"""
import argparse, csv, json, re, sys
from pathlib import Path

VERSION = "0.3.0"
TOOL = "demand-miner"

STRONG = ["looking for", "need someone", "need a ", "need an ", "hire", "hiring",
          "want to hire", "any recommendations", "recommend a", "recommend someone",
          "who can", "can anyone", "help me find", "in search of", "seeking",
          "looking to hire", "need help with"]
PRICE = ["how much", "what does it cost", "cost of", "price for", "quote",
         "budget", "rates for", "charge for"]
PAIN = ["frustrated", "fired my", "terrible experience", "not happy with",
        "ripped off", "scammed", "ghosted", "doesn't work", "does not work",
        "my current designer", "my current developer", "my current agency"]
OWNER = ["my business", "my shop", "my store", "my clinic", "our company",
         "my restaurant", "my salon", "my practice", "my company"]
SELLER = ["i offer", "we offer", "dm me", "hire me", "my services",
          "i can help you", "check out my", "i build websites",
          "we build websites", "our agency", "book a call", "link in bio",
          # v0.2 (redesign after the 2026-11-01 falsifier FAIL): agency/guide
          # voice — sellers answering buyer questions as SEO bait
          "our pricing", "get in touch", "in this article", "in this guide",
          "this guide tells", "our web designer", "our designers", "our team",
          "contact us", "free consultation", "our services", "brand audit",
          # summary-style seller markers (AI summaries of ads)
          "promotional", "advertisement", "advertising", "is offering"]

STOPLOC = {"The", "A", "An", "My", "Our", "This", "That", "It", "I"}


def _keyword_patterns(keywords):
    """Compile word-boundary-aware patterns for the niche keywords.

    A keyword only matches as a whole word (or whole phrase, for
    multi-word keywords): ``site`` must NOT match inside "opposite",
    "parasite" or "sitemap". Boundaries are enforced at both ends with
    (?<!\\w) / (?!\\w) around the escaped keyword, case-insensitively
    (the text is lowercased before matching and keywords are lowered
    here too).
    """
    pats = []
    for k in keywords or []:
        if not isinstance(k, str):
            continue
        k = k.strip().lower()
        if k:
            pats.append(re.compile(r"(?<!\w)" + re.escape(k) + r"(?!\w)"))
    return pats


def score_mention(text, keywords):
    t = " " + text.lower().strip() + " "
    if not any(p.search(t) for p in _keyword_patterns(keywords)):
        return None  # off-niche: not scored at all
    seller = any(s in t for s in SELLER)
    score, hits = 0, []
    for group, pts in ((STRONG, 3), (PRICE, 3), (PAIN, 2), (OWNER, 1)):
        for phrase in group:
            if phrase in t:
                score += pts
                hits.append(phrase.strip())
    if text.strip().endswith("?") or "?" in text:
        score += 1
        hits.append("question")
    eng = 0
    return {"score": score, "seller": seller, "hits": hits}


def location_hint(text):
    m = re.search(r"\b(?:in|near|around)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", text)
    if m and m.group(1).split()[0] not in STOPLOC:
        return m.group(1)
    return ""


def _parse_engagement(value):
    """Return engagement as an int, or raise ValueError if unusable.

    Missing/None/empty-string engagement counts as 0 (as before).
    A non-numeric value ("abc", a list, a dict, a bool) raises, and the
    caller treats the whole mention as malformed and skips it — that
    policy is documented in the README ("How malformed mentions are
    handled").
    """
    if value is None:
        return 0
    if isinstance(value, bool):
        raise ValueError("engagement is not a number")
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return 0
        return int(float(s))  # raises ValueError on "abc" etc.
    raise ValueError("engagement is not a number")


def mine(mentions, keywords, min_score=4):
    """Mine mentions into leads, tolerating malformed mentions.

    Per-mention tolerance: a mention that is not a dict, has no usable
    text, or carries a non-numeric engagement value is SKIPPED and
    counted in ``skipped_malformed`` — it never aborts the run, and the
    count is printed in the report. Valid mentions always process.
    """
    leads, sellers, below, off_niche, skipped = [], 0, 0, 0, 0
    if mentions is None:
        mentions = []
    for m in mentions:
        if not isinstance(m, dict):
            skipped += 1
            continue
        try:
            raw_text = m.get("text", "")
            if not isinstance(raw_text, str):
                skipped += 1
                continue
            text = raw_text.strip()
            if not text:
                skipped += 1
                continue
            r = score_mention(text, keywords)
            if r is None:
                off_niche += 1
                continue
            if r["seller"]:
                sellers += 1
                continue
            try:
                eng = _parse_engagement(m.get("engagement"))
            except (ValueError, TypeError):
                skipped += 1
                continue
            bonus = 2 if eng >= 100 else (1 if eng >= 10 else 0)
            total = r["score"] + bonus
            if total < min_score:
                below += 1
                continue
            leads.append({
                "score": total, "author": m.get("author", ""), "source": m.get("source", ""),
                "location": location_hint(text), "quote": re.sub(r"\s+", " ", text)[:160],
                "url": m.get("url", ""), "signals": ", ".join(sorted(set(r["hits"]))),
            })
        except Exception:
            # Safety net: no single mention may abort the whole run.
            skipped += 1
            continue
    leads.sort(key=lambda x: -x["score"])
    return {"leads": leads, "sellers_filtered": sellers, "below_threshold": below,
            "off_niche": off_niche, "scanned": len(mentions),
            "skipped_malformed": skipped}


def render(result, keywords):
    L = [f"DEMAND MINER v{VERSION} — niche: {', '.join(keywords)}",
         f"Scanned {result['scanned']} mentions · {result['sellers_filtered']} sellers filtered · "
         f"{result['off_niche']} off-niche · {result['below_threshold']} below the lead bar"]
    if result.get("skipped_malformed"):
        L.append(f"Skipped {result['skipped_malformed']} malformed mentions "
                 f"(not an object, no usable text, or non-numeric engagement — see README)")
    L += [f"LEADS: {len(result['leads'])}", ""]
    for i, lead in enumerate(result["leads"], 1):
        L.append(f"{i}. [score {lead['score']}] {lead['author'] or 'unknown author'} · {lead['source']}"
                 + (f" · near {lead['location']}" if lead["location"] else ""))
        L.append(f"   \"{lead['quote']}\"")
        L.append(f"   signals: {lead['signals']} · {lead['url']}")
    L += ["", "Every lead carries its evidence quote + source. Outreach is a separate, approved act — this sheet only mines."]
    return "\n".join(L)


def render_json(result, keywords, min_score):
    """The same lead sheet as render(), as one JSON object for agents."""
    warnings = []
    if result.get("skipped_malformed"):
        warnings.append(
            f"Skipped {result['skipped_malformed']} malformed mentions "
            f"(not an object, no usable text, or non-numeric engagement — see README)")
    leads = []
    for lead in result["leads"]:
        leads.append({
            "score": lead["score"], "author": lead["author"], "source": lead["source"],
            "location": lead["location"], "quote": lead["quote"], "url": lead["url"],
            "signals": [s for s in (p.strip() for p in lead["signals"].split(",")) if s],
        })
    return json.dumps({
        "tool": TOOL, "version": VERSION, "keywords": keywords, "min_score": min_score,
        "scanned": result["scanned"], "sellers_filtered": result["sellers_filtered"],
        "off_niche": result["off_niche"], "below_threshold": result["below_threshold"],
        "skipped_malformed": result["skipped_malformed"],
        "leads_count": len(leads), "leads": leads, "warnings": warnings,
    }, indent=2)


def extract_mentions(raw):
    """Pull the mentions list out of the parsed JSON.
    Structural problems get an error that says what to fix. (Per-mention
    problems are different: mine() skips and counts those — see README.)"""
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        if "mentions" not in raw:
            raise ValueError('corpus file has no "mentions" list — the top level must look like '
                             '{"mentions": [ ...one object per mention... ]} '
                             "(or pass a bare list of mentions)")
        mentions = raw["mentions"]
        if not isinstance(mentions, list):
            raise ValueError(f'"mentions" must be a list of mention objects, got {type(mentions).__name__} — '
                             'the top level must look like {"mentions": [ ...one object per mention... ]}')
        return mentions
    raise ValueError('corpus file must be a JSON object with a "mentions" list (or a bare list of mentions)')


def _fail(message, as_json):
    if as_json:
        print(json.dumps({"error": message}))
    else:
        print(f"ERROR: {message}")
    return 1


def main():
    ap = argparse.ArgumentParser(description="Demand Miner — ranked buyer leads from public mentions")
    ap.add_argument("corpus")
    ap.add_argument("--keywords", required=True, help="comma-separated niche keywords")
    ap.add_argument("--min-score", type=int, default=4)
    ap.add_argument("--csv", help="also write leads to this CSV path")
    ap.add_argument("--json", action="store_true",
                    help="print one JSON object instead of the lead sheet")
    a = ap.parse_args()
    keywords = [k.strip().lower() for k in a.keywords.split(",") if k.strip()]
    if not keywords:
        return _fail("no usable keywords — pass at least one keyword via --keywords "
                     "(e.g. --keywords website,\"web design\")", a.json)
    path = Path(a.corpus)
    if not path.exists():
        return _fail(f"file not found: {path}", a.json)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        mentions = extract_mentions(raw)
        result = mine(mentions, keywords, a.min_score)

        def write_csv():
            with open(a.csv, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=["score", "author", "source", "location", "quote", "url", "signals"])
                w.writeheader()
                w.writerows(result["leads"])

        if a.json:
            # CSV first, so a write failure still yields exactly one
            # JSON object on stdout (the error), never two.
            if a.csv:
                write_csv()
            print(render_json(result, keywords, a.min_score))
        else:
            print(render(result, keywords))
            if a.csv:
                write_csv()
    except Exception as e:
        return _fail(str(e), a.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
