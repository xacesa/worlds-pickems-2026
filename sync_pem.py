#!/usr/bin/env python3
"""Liest öffentliche PEM.LOL-Worlds-2026-Daten konservativ aus.
Zwischenstände geben keine Punkte. Bei unbekanntem Seitenlayout Abbruch.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

URL = "https://pem.lol/worlds/2026/pickems"
HEADINGS = [
    "Highest Presence",
    "Highest Win Rate (5+ Games)",
    "Most Deaths / Game (5+ Games)",
    "Highest KDA",
    "Avg Damage / Game",
    "Highest Kill Participation",
    "Peyz vs Gumayusi: Most Kills",
    "Faker: 700 Worlds Kills?",
    "Will Teemo be picked?",
    "Unique Champions",
    "Games Under / Over 32:00",
    "15 Kills in a Game?",
    "450 CS in a Game?",
    "Finals MVP Role",
    "Regions in Knockouts",
    "LCS team in Knockouts?",
    "Higher Placement: HLE or T1",
    "Shortest Game Win",
]

def sections(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "svg", "noscript"]):
        tag.decompose()
    lines = [s.strip() for s in soup.get_text("\n", strip=True).splitlines() if s.strip()]
    positions = {}
    for pos, item in enumerate(lines):
        if item in HEADINGS:
            positions.setdefault(HEADINGS.index(item) + 1, pos)
    if len(positions) < 16 or any(i not in positions for i in (1, 2, 4, 8, 9, 12, 13, 14, 16, 18)):
        raise RuntimeError(f"PEM.LOL layout changed: {len(positions)} / 18 sections found")
    ordered = sorted((pos, qid) for qid, pos in positions.items())
    return {qid: lines[pos+1 : ordered[idx+1][0] if idx+1 < len(ordered) else len(lines)]
            for idx, (pos, qid) in enumerate(ordered)}

def first_number(lines, pattern):
    for idx, value in enumerate(lines[:18]):
        # Ignore the rank "1" before the top statistic on PEM.LOL.
        if idx == 0 and value == "1" and len(lines) > 1 and re.fullmatch(pattern, lines[1]):
            continue
        if re.fullmatch(pattern, value):
            return float(value.replace(",", "."))
    return None

def top_name(lines, fmt):
    patterns = {
        "percent": r"\d+(?:[.,]\d+)?%",
        "decimal": r"\d+[.]\d+",
        "damage": r"\d{1,3}(?:,\d{3})+|\d{4,6}",
    }
    for i, token in enumerate(lines[:14]):
        if re.fullmatch(patterns[fmt], token):
            for candidate in lines[i+1:i+6]:
                if re.fullmatch(r"\d+/\d+|\d+|[Nn]/[Aa]|-", candidate):
                    continue
                if re.search("[A-Za-zÀ-ÿ]", candidate) and len(candidate) < 75:
                    return candidate, token
    return None

def yes_no(lines):
    for word in lines[:14]:
        if word.lower() in ("yes", "no"):
            return "Ja" if word.lower() == "yes" else "Nein"
    return None

def parse(html):
    s = sections(html)
    live = {}
    def put(q, value, detail="", **more):
        if value is not None and str(value).strip():
            live[str(q)] = {"value": str(value), "detail": detail, **more}
    for q in (1, 2, 3, 4, 5, 6):
        fmt = "percent" if q in (1, 2, 6) else "damage" if q == 5 else "decimal"
        pair = top_name(s.get(q, []), fmt)
        if pair:
            put(q, pair[0], pair[1])

    duel = s.get(7, [])
    if any("tied" in v.lower() for v in duel[:9]):
        put(7, "Gleichstand", "Peyz und Gumayusi gleichauf")
    else:
        for team in ("Peyz", "Gumayusi"):
            if team in duel[:10]:
                put(7, team)
                break

    faker = first_number(s.get(8, []), r"\d{2,4}")
    if faker is not None:
        put(8, f"{faker:g}", "Fakers WM-Karriere-Kills", numeric=faker)
    put(9, yes_no(s.get(9, [])))
    champs = first_number(s.get(10, []), r"\d+")
    if champs is not None:
        put(10, f"{champs:g}", "bisher ausgewählte Champions", numeric=champs)

    times = s.get(11, [])
    stats = {}
    for i, entry in enumerate(times):
        label = ("Nach" if "Over (After)" in entry else "Vor" if "Under (Before)" in entry else None)
        if label:
            choices = (times[i-1:i] + times[i+1:i+2]) if label == "Nach" else (times[i+1:i+2] + times[i-1:i])
            match = next((v for v in choices if re.fullmatch(r"\d+", v)), None)
            if match is not None:
                stats[label] = int(match)
    if len(stats) == 2:
        leader = "Vor" if stats["Vor"] > stats["Nach"] else "Nach" if stats["Nach"] > stats["Vor"] else "Gleichstand"
        put(11, leader, f"Vor {stats['Vor']} · Nach {stats['Nach']}", before=stats["Vor"], after=stats["Nach"])

    for q, desc in ((12, "meiste Kills in einem Spiel"), (13, "meiste CS in einem Spiel")):
        number = first_number(s.get(q, []), r"\d+")
        if number is not None:
            put(q, f"{number:g}", desc, numeric=number)

    role_map = {"Mid": "Mid Lane", "Mid Lane": "Mid Lane", "ADC": "ADC",
                "AD Carry": "ADC", "Bot": "ADC", "Top": "Top",
                "Jungle": "Jungle", "Support": "Support"}
    for value in s.get(14, [])[:12]:
        if value in role_map:
            put(14, role_map[value])
            break
        if value.upper() == "TBD":
            put(14, "Noch offen")
            break
    regions = first_number(s.get(15, []), r"\d+")
    if regions is not None:
        put(15, f"{regions:g}", "Regionen in der K.-o.-Phase", numeric=regions)
    put(16, yes_no(s.get(16, [])))

    placement = s.get(17, [])
    if any("tied" in x.lower() for x in placement[:8]):
        put(17, "Beide noch dabei", "Noch keine Entscheidung")
    elif "T1" in placement[:12]:
        put(17, "T1")
    elif "HLE" in placement[:12] or "Hanwha Life Esports" in placement[:12]:
        put(17, "Hanwha Life Esports")

    shortest = s.get(18, [])
    duration = next((x for x in shortest[:12] if re.fullmatch(r"\d{1,2}:\d{2}", x)), None)
    if duration:
        pos = shortest.index(duration)
        matchup = next((x for x in shortest[pos+1:pos+7] if "vs" in x.lower()), None)
        if matchup and matchup.strip().lower().endswith("vs"):
            i = shortest.index(matchup)
            if i + 1 < len(shortest):
                matchup += " " + shortest[i+1]
        put(18, matchup or "Kürzestes Spiel", duration)

    if len(live) < 14:
        raise RuntimeError(f"Only {len(live)} metrics found, refusing partial scrape")
    return live

def final_answers(live):
    out = {}
    # Nur monotone Ereignisse jetzt verbindlich werten
    for q, limit in ((8, 700), (12, 15), (13, 450)):
        val = live.get(str(q), {}).get("numeric")
        if isinstance(val, (int, float)) and val >= limit:
            out[str(q)] = "Ja"
    for q in (9, 16):
        if live.get(str(q), {}).get("value") == "Ja":
            out[str(q)] = "Ja"

    # Die übrigen Antworten erst NACH dem Turnier und bei hinreichenden Signalen.
    completed = (dt.datetime.now(dt.timezone.utc).date() >= dt.date(2026, 11, 15)
                 and live.get("14", {}).get("value") not in (None, "Noch offen")
                 and live.get("15", {}).get("numeric", 0) >= 2
                 and live.get("17", {}).get("value") not in (None, "Beide noch dabei"))
    if not completed:
        return out

    for q in (1, 2, 3, 4, 5, 6, 7, 14, 15, 17):
        value = live.get(str(q), {}).get("value")
        if value and value not in ("Gleichstand", "Noch offen"):
            out[str(q)] = value
    for q in (8, 9, 16):
        out.setdefault(str(q), "Nein")
    count = live.get("10", {}).get("numeric")
    if isinstance(count, (int, float)) and 0 < count < 1000:
        bucket = int(count) // 5 * 5
        out["10"] = f"{bucket}–{bucket+4}"
    before = live.get("11", {}).get("before")
    after = live.get("11", {}).get("after")
    if isinstance(before, int) and isinstance(after, int) and before != after:
        out["11"] = "Vor" if before > after else "Nach"
    for q, threshold in ((12, 15), (13, 450)):
        if str(q) not in out and isinstance(live.get(str(q), {}).get("numeric"), (int, float)):
            out[str(q)] = "Nein"
    # Gewinner des kürzesten Spiels ist aus der PEM-Paarung nicht eindeutig.
    return out

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--html", type=Path)
    args = parser.parse_args()
    if args.html:
        html = args.html.read_text(encoding="utf-8")
    else:
        response = requests.get(URL, timeout=30, headers={"User-Agent": "Mozilla/5.0 (compatible; PickemFanTracker/1.0)"})
        response.raise_for_status()
        if len(response.content) > 5_000_000:
            raise RuntimeError("Response too large")
        html = response.text
    live = parse(html)
    path = Path(__file__).with_name("results.json")
    old = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    final = {k: v for k, v in old.get("results", {}).items() if k.isdigit() and 1 <= int(k) <= 18 and isinstance(v, str)}
    proposed = final_answers(live)
    conflicts = {k: (final[k], v) for k, v in proposed.items() if k in final and final[k] != v}
    if conflicts:
        raise RuntimeError(f"Conflicting final answers; review manually: {conflicts}")
    final.update(proposed)
    data = {"format": "worlds-2026-results", "version": 1,
            "updatedAt": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "sourceUrl": URL, "results": final, "live": live}
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Updated {len(live)} live stats, {len(final)} confirmed results")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"SYNC ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
