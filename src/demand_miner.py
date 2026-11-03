#!/usr/bin/env python3
"""
Demand Miner v0.2 — turn captured public mentions into ranked buyer leads.

The free answer to ₹8,500+/mo lead tools: you bring mentions captured from
public posts/comments (social search, comment exports, forum threads); the
miner scores BUYING INTENT with transparent rules, filters out sellers and
spam, and prints a lead sheet where every lead carries its evidence quote
and source URL. No scraping, no logins, no outreach — mining only.
Local, offline, Python 3 stdlib only. Spend: none.

Usage:
  python3 demand_miner.py CORPUS.json --keywords website,"web design",site [--min-score 4] [--csv leads.csv]
Corpus: {"mentions":[{"source","text","url","author","engagement","date"}]}
Exit codes: 0 ok, 1 error.
"""
import argparse, csv, json, re, sys
from pathlib import Path

VERSION = "0.2.0"

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


def score_mention(text, keywords):
    t = " " + text.lower().strip() + " "
    if not any(k in t for k in keywords):
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


def mine(mentions, keywords, min_score=4):
    leads, sellers, below, off_niche = [], 0, 0, 0
    for m in mentions:
        text = str(m.get("text", "")).strip()
        if not text:
            continue
        r = score_mention(text, keywords)
        if r is None:
            off_niche += 1
            continue
        if r["seller"]:
            sellers += 1
            continue
        eng = int(m.get("engagement") or 0)
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
    leads.sort(key=lambda x: -x["score"])
    return {"leads": leads, "sellers_filtered": sellers, "below_threshold": below,
            "off_niche": off_niche, "scanned": len(mentions)}


def render(result, keywords):
    L = [f"DEMAND MINER v{VERSION} — niche: {', '.join(keywords)}",
         f"Scanned {result['scanned']} mentions · {result['sellers_filtered']} sellers filtered · "
         f"{result['off_niche']} off-niche · {result['below_threshold']} below the lead bar",
         f"LEADS: {len(result['leads'])}", ""]
    for i, lead in enumerate(result["leads"], 1):
        L.append(f"{i}. [score {lead['score']}] {lead['author'] or 'unknown author'} · {lead['source']}"
                 + (f" · near {lead['location']}" if lead["location"] else ""))
        L.append(f"   \"{lead['quote']}\"")
        L.append(f"   signals: {lead['signals']} · {lead['url']}")
    L += ["", "Every lead carries its evidence quote + source. Outreach is a separate, approved act — this sheet only mines."]
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description="Demand Miner — ranked buyer leads from public mentions")
    ap.add_argument("corpus")
    ap.add_argument("--keywords", required=True, help="comma-separated niche keywords")
    ap.add_argument("--min-score", type=int, default=4)
    ap.add_argument("--csv", help="also write leads to this CSV path")
    a = ap.parse_args()
    path = Path(a.corpus)
    if not path.exists():
        print(f"ERROR: file not found: {path}")
        return 1
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        mentions = raw["mentions"] if isinstance(raw, dict) else raw
        keywords = [k.strip().lower() for k in a.keywords.split(",") if k.strip()]
        result = mine(mentions, keywords, a.min_score)
        print(render(result, keywords))
        if a.csv:
            with open(a.csv, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=["score", "author", "source", "location", "quote", "url", "signals"])
                w.writeheader()
                w.writerows(result["leads"])
    except Exception as e:
        print(f"ERROR: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
