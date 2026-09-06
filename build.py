#!/usr/bin/env python3
"""Render data/activity-logs.csv into a static index.html, organised by unit.

The CSV is a matrix: activity phases down the rows, units across the columns.
This flips it so each unit gets its own card, and keeps the original matrix at
the bottom for cross-unit comparison. Values are normalised (dates, durations)
but never invented: anything the sheet leaves as N/A or tbc stays that way.
"""

import csv
import html
import re
from collections import Counter
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).parent
CSV_PATH = ROOT / "data" / "activity-logs.csv"
OUT_PATH = ROOT / "index.html"
GENERATED = date.today()

# ---------------------------------------------------------------- parsing ---

NULLS = {"", "n/a", "na", "-"}
PENDING = {"tbc", "tba"}


def is_null(v):
    return v.strip().lower() in NULLS


def is_pending(v):
    return v.strip().lower() in PENDING


DMY = re.compile(r"^(\d{1,2})[/-](\d{1,2})[/-](\d{4})(?:\s+(\d{1,2}):(\d{2})(?::(\d{2}))?)?$")
DMONY = re.compile(r"^(\d{1,2})-([A-Za-z]{3})-(\d{2,4})$")
MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun",
     "jul", "aug", "sep", "oct", "nov", "dec"], start=1)}


def parse_dt(v):
    """Return (datetime, has_time, ambiguous) or None.

    The sheet mixes D/M/Y and M/D/Y. Where one component is >12 the order is
    forced; where both are <=12 the reading is flagged ambiguous and resolved
    later against the month the rest of the dataset agrees on.
    """
    v = v.strip()
    m = DMONY.match(v)
    if m:
        d, mon, y = int(m.group(1)), MONTHS.get(m.group(2).lower()), int(m.group(3))
        if mon is None:
            return None
        y += 2000 if y < 100 else 0
        return datetime(y, mon, d), False, False
    m = DMY.match(v)
    if not m:
        return None
    a, b, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
    hh = int(m.group(4)) if m.group(4) else 0
    mm = int(m.group(5)) if m.group(5) else 0
    has_time = m.group(4) is not None
    if a > 12 and b <= 12:            # day first
        day, mon, amb = a, b, False
    elif b > 12 and a <= 12:          # month first
        day, mon, amb = b, a, False
    elif a <= 12 and b <= 12:
        day, mon, amb = a, b, True    # provisional day-first, revisited below
    else:
        return None
    try:
        return datetime(y, mon, day, hh, mm), has_time, amb
    except ValueError:
        return None


DUR_TOKEN = re.compile(r"(\d+)\s*(d|h|min|m)?", re.I)


def parse_dur(v):
    """Minutes from strings like '0d 2h 22m', '3h 28min', '59m', '2h 30', '0'."""
    v = v.strip()
    if is_null(v) or is_pending(v):
        return None
    tokens = [(int(n), (u or "").lower()) for n, u in DUR_TOKEN.findall(v) if n != ""]
    if not tokens:
        return None
    total, prev = 0, None
    for n, unit in tokens:
        if not unit:
            # bare number: minutes if it trails an hours token, else minutes
            unit = "m" if prev in ("h", None) else prev
        if unit == "d":
            total += n * 1440
        elif unit == "h":
            total += n * 60
        else:
            total += n
        prev = unit
    return total


def fmt_dur(mins):
    """Hours and minutes only -- never days, which are ambiguous for effort."""
    if mins is None:
        return None
    h, m = divmod(mins, 60)
    return f"{h}h {m:02d}m" if h else f"{m}m"


def fmt_dt(dt, has_time):
    s = dt.strftime("%a %-d %b %Y")
    return f"{s} &middot; {dt.strftime('%H:%M')}" if has_time else s


def fmt_day(dt):
    return dt.strftime("%-d %b")


def fmt_dt_short(dt, has_time):
    """Compact form for the wide comparison table: '15 Aug 09:55'."""
    s = dt.strftime("%-d %b")
    return f"{s} {dt.strftime('%H:%M')}" if has_time else s


# ------------------------------------------------------------------ model ---

def read_matrix():
    rows = list(csv.reader(CSV_PATH.open(newline="", encoding="utf-8-sig")))
    header = rows[0]
    units, cols = [], []
    for i, cell in enumerate(header[2:], start=2):
        name = re.sub(r"\s*\(.*\)\s*$", "", cell).strip()
        if not name or name.lower().startswith("note"):
            continue
        units.append(name)
        cols.append(i)

    blocks, order, current = {}, [], None
    for row in rows[1:]:
        row = row + [""] * (len(header) - len(row))
        if not any(c.strip() for c in row):
            continue
        if row[0].strip():
            current = row[0].strip()
            blocks.setdefault(current, [])
            order.append(current)
        metric = row[1].strip()
        if not metric or current is None:
            continue
        blocks[current].append((metric, {u: row[c] for u, c in zip(units, cols)}))
    return units, [b for i, b in enumerate(order) if b not in order[:i]], blocks


def resolve_dates(units, block_order, blocks):
    """Two passes: learn the dominant month from unambiguous dates, then use it
    to settle the D/M vs M/D readings the sheet leaves ambiguous."""
    votes = Counter()
    for name in block_order:
        for _metric, vals in blocks[name]:
            for v in vals.values():
                p = parse_dt(v)
                if p and not p[2]:
                    votes[(p[0].year, p[0].month)] += 1
    dominant = votes.most_common(1)[0][0] if votes else None

    def resolve(v):
        p = parse_dt(v)
        if not p:
            return None
        dt, has_time, amb = p
        if amb and dominant:
            flipped = dt.replace(month=dt.day, day=dt.month) if dt.day <= 12 else dt
            if (dt.year, dt.month) != dominant and (flipped.year, flipped.month) == dominant:
                dt = flipped
        return dt, has_time
    return resolve


PHASES = [
    # csv block name,            display,                 slug,  start,                end,                   duration,               people,           effort,        break
    ("MANUAL QA SNAGGING",  "Manual QA snagging", "qa",   "Start - Manual QA",  "End -  Manual QA",  "Duration - Manual QA", "Number of QA", "Manhours", "break"),
    ("MANUAL MEP SNAGGING", "Manual MEP snagging", "mep", "Start - MEP QA",     "End -  MEP QA",     "Duration - MEP QA",    "Number of QA", "Manhours", None),
    ("CAPTURE",             "Capture",            "cap",  "Start - Capture",    "End - Capture",     None,                   None,             "Manhours", None),
    ("PROCESSING",          "Processing",         "proc", "Start - Processsing", "End - Processing", None,                   None,             "Processing time", None),
]


def build_units(units, block_order, blocks, resolve):
    lut = {}
    for name in block_order:
        for metric, vals in blocks[name]:
            lut[(name, metric.strip())] = vals

    def get(block, metric, unit):
        if metric is None:
            return ""
        return lut.get((block, metric.strip()), {}).get(unit, "")

    out = {}
    for unit in units:
        phases = []
        for block, label, slug, k_start, k_end, k_dur, k_people, k_effort, k_break in PHASES:
            raw = {
                "platform": get(block, "Platform", unit).strip(),
                "start": get(block, k_start, unit).strip(),
                "end": get(block, k_end, unit).strip(),
                "duration": get(block, k_dur, unit).strip(),
                "people": get(block, k_people, unit).strip(),
                "effort": get(block, k_effort, unit).strip(),
                "break": get(block, k_break, unit).strip() if k_break else "",
            }
            start, end = resolve(raw["start"]), resolve(raw["end"])
            dur = parse_dur(raw["duration"])
            brk = parse_dur(raw["break"]) if raw["break"] else None
            eff = parse_dur(raw["effort"])
            people = int(raw["people"]) if raw["people"].isdigit() else None

            # cross-check what the sheet states against what its own times imply
            flags = []
            if start and end and dur is not None:
                implied = int((end[0] - start[0]).total_seconds() // 60) - (brk or 0)
                if implied != dur:
                    flags.append(("duration", f"Start to end less break is {fmt_dur(implied)}; "
                                              f"the sheet records {fmt_dur(dur)}."))
            if dur is not None and people and eff is not None and dur * people != eff:
                flags.append(("effort", f"{fmt_dur(dur)} across {people} inspector"
                                        f"{'s' if people > 1 else ''} is {fmt_dur(dur * people)}; "
                                        f"the sheet records {fmt_dur(eff)}."))

            pending = any(is_pending(v) for v in (raw["start"], raw["end"], raw["effort"]))
            recorded = bool(start or end or dur is not None or eff is not None)
            phases.append({
                "label": label, "slug": slug, "block": block,
                "platform": raw["platform"], "start": start, "end": end,
                "duration": dur, "break": brk, "people": people, "effort": eff,
                "effort_label": "Processing time" if slug == "proc" else "Manhours",
                "flags": dict(flags), "pending": pending, "recorded": recorded,
                "raw": raw,
            })
        out[unit] = phases
    return out


# ----------------------------------------------------------------- render ---

PHASE_COLOR = {"qa": "var(--c-qa)", "mep": "var(--c-mep)",
               "cap": "var(--c-cap)", "proc": "var(--c-proc)"}


def esc(s):
    return html.escape(str(s), quote=True)


def platform_pill(p):
    if not p or is_null(p):
        return ""
    cls = "pf-conxai" if p.strip().lower() == "conxai" else "pf-onsite"
    return f'<span class="pill {cls}">{esc(p.strip())}</span>'


def flag(phase, key):
    if key not in phase["flags"]:
        return ""
    return (f'<span class="warn" tabindex="0" role="note" '
            f'aria-label="{esc(phase["flags"][key])}" '
            f'data-tip="{esc(phase["flags"][key])}">!</span>')


def dd(value, extra=""):
    return f'<dd{extra}>{value}</dd>'


def render_phase(p):
    head = (f'<header><h4>{esc(p["label"])}</h4>{platform_pill(p["platform"])}</header>')
    if not p["recorded"]:
        note = "Scheduled, not yet run" if p["pending"] else "Not recorded"
        sub = ""
        if p["platform"] and not is_null(p["platform"]):
            sub = f'<span class="sub">Planned platform: {esc(p["platform"])}</span>'
        return (f'<section class="phase ph-{p["slug"]} is-empty">{head}'
                f'<p class="none">{note}{sub}</p></section>')

    rows = []
    if p["start"]:
        rows.append(("Start", fmt_dt(*p["start"]), ""))
    if p["end"]:
        rows.append(("End", fmt_dt(*p["end"]), ""))
    if p["break"] is not None:
        rows.append(("Break", fmt_dur(p["break"]) if p["break"] else "None", ""))
    if p["duration"] is not None:
        rows.append(("Duration" + flag(p, "duration"), fmt_dur(p["duration"]), ' class="num"'))
    if p["people"] is not None:
        word = "inspector" if p["people"] == 1 else "inspectors"
        rows.append(("Inspectors", f'{p["people"]} <span class="unit-word">{word}</span>', ""))
    if p["effort"] is not None:
        rows.append((p["effort_label"] + flag(p, "effort"),
                     fmt_dur(p["effort"]), ' class="num strong"'))

    body = "".join(f'<div><dt>{k}</dt>{dd(v, extra)}</div>' for k, v, extra in rows)
    return f'<section class="phase ph-{p["slug"]}">{head}<dl>{body}</dl></section>'


def unit_summary(phases):
    by = {p["slug"]: p for p in phases}
    qa, mep, cap, proc = by["qa"], by["mep"], by["cap"], by["proc"]
    manual = [x for x in (qa["effort"], mep["effort"]) if x is not None]
    tiles = []

    if manual:
        bits = []
        if qa["effort"] is not None:
            bits.append(f'QA {fmt_dur(qa["effort"])}')
        if mep["effort"] is not None:
            bits.append(f'MEP {fmt_dur(mep["effort"])}')
        else:
            bits.append("MEP not recorded")
        tiles.append(("Manual manhours", fmt_dur(sum(manual)), " + ".join(bits)))
    else:
        tiles.append(("Manual manhours", "&mdash;", "No manual snagging recorded"))

    if cap["effort"] is not None:
        when = fmt_day(cap["start"][0]) if cap["start"] else ""
        if cap["start"] and cap["end"] and cap["start"][0] != cap["end"][0]:
            when = f'{fmt_day(cap["start"][0])} &ndash; {fmt_day(cap["end"][0])}'
        tiles.append(("Capture manhours", fmt_dur(cap["effort"]), when or "&mdash;"))
    else:
        tiles.append(("Capture manhours", "tbc" if cap["pending"] else "&mdash;", "Not yet captured"))

    if proc["effort"] is not None:
        when = fmt_day(proc["start"][0]) if proc["start"] else ""
        tiles.append(("Processing time", fmt_dur(proc["effort"]), when or "&mdash;"))
    else:
        tiles.append(("Processing time", "tbc" if proc["pending"] else "&mdash;", "Not yet processed"))

    return tiles


def unit_subline(phases):
    by = {p["slug"]: p for p in phases}
    bits = []
    for slug, name in (("qa", "QA"), ("mep", "MEP")):
        p = by[slug]
        pf = p["platform"].strip()
        if p["recorded"] and pf and not is_null(pf):
            bits.append(f'{name} <b>onsite</b>' if pf.lower() == "onsite"
                        else f'{name} on <b>{esc(pf)}</b>')
    cap = by["cap"]
    if cap["start"]:
        rng = fmt_day(cap["start"][0])
        if cap["end"] and cap["end"][0] != cap["start"][0]:
            rng = f'{fmt_day(cap["start"][0])}&ndash;{fmt_day(cap["end"][0])}'
        bits.append(f"captured {rng}")
    elif cap["pending"]:
        bits.append("capture tbc")
    return " &middot; ".join(bits) or "No activity recorded"


def render_calendar(units, unit_phases):
    """A day strip per unit: which phases touched which day."""
    days = sorted({d.date()
                   for phases in unit_phases.values()
                   for p in phases
                   for ends in (p["start"], p["end"]) if ends
                   for d in (ends[0],)})
    if not days:
        return ""
    all_days = []
    cur = days[0]
    while cur <= days[-1]:
        all_days.append(cur)
        cur = date.fromordinal(cur.toordinal() + 1)

    head = "".join(
        f'<div class="cal-d{" wknd" if d.weekday() >= 5 else ""}">'
        f'<span class="dow">{d.strftime("%a")[0]}</span>'
        f'<span class="dnum">{d.day}</span></div>' for d in all_days)

    rows = []
    for u in units:
        cells = []
        for d in all_days:
            chips = []
            for p in unit_phases[u]:
                touched = False
                if p["start"] and p["end"]:
                    touched = p["start"][0].date() <= d <= p["end"][0].date()
                elif p["start"]:
                    touched = p["start"][0].date() == d
                if touched:
                    chips.append(f'<i class="c-{p["slug"]}" title="{esc(u)} &mdash; '
                                 f'{esc(p["label"])}"></i>')
            cls = "cal-c" + (" wknd" if d.weekday() >= 5 else "") + (" on" if chips else "")
            cells.append(f'<div class="{cls}">{"".join(chips)}</div>')
        rows.append(f'<div class="cal-row" data-unit="{esc(u)}">'
                    f'<a class="cal-u mono" href="#u-{esc(u)}">{esc(u)}</a>'
                    f'<div class="cal-cells">{"".join(cells)}</div></div>')

    legend = "".join(f'<span><i class="c-{s}"></i>{n}</span>' for s, n in
                     (("qa", "Manual QA"), ("mep", "Manual MEP"),
                      ("cap", "Capture"), ("proc", "Processing")))
    month = all_days[0].strftime("%B %Y")
    return f"""
<section class="card cal-card" aria-labelledby="cal-h">
  <div class="card-head">
    <h2 id="cal-h">Programme at a glance</h2>
    <p class="card-sub">Every day each unit was worked on, {esc(month)}.</p>
  </div>
  <div class="cal-legend">{legend}</div>
  <div class="cal-scroll">
    <div class="cal">
      <div class="cal-row cal-head"><div class="cal-u"></div><div class="cal-cells">{head}</div></div>
      {"".join(rows)}
    </div>
  </div>
</section>"""


def render_matrix(units, block_order, blocks, resolve):
    thead = "".join(f'<th scope="col" class="mono">{esc(u)}</th>' for u in units)
    body = []
    for name in block_order:
        body.append(f'<tr class="grp"><th scope="rowgroup" colspan="{len(units) + 1}">'
                    f'{esc(name.title())}</th></tr>')
        for metric, vals in blocks[name]:
            cells = []
            for u in units:
                raw = vals[u].strip()
                if is_null(raw):
                    cells.append('<td class="na">&mdash;</td>')
                    continue
                if is_pending(raw):
                    cells.append('<td class="na">tbc</td>')
                    continue
                dt = resolve(raw)
                if dt:
                    cells.append(f'<td class="num">{fmt_dt_short(*dt)}</td>')
                    continue
                mins = parse_dur(raw)
                if mins is not None and re.search(r"[dhm]", raw, re.I):
                    cells.append(f'<td class="num">{esc(fmt_dur(mins))}</td>')
                elif raw == "0":
                    cells.append('<td class="num">None</td>')
                else:
                    cells.append(f"<td>{esc(raw)}</td>")
            label = re.sub(r"\s+", " ", metric).strip().replace("Processsing", "Processing")
            label = label[:1].upper() + label[1:]
            body.append(f'<tr><th scope="row">{esc(label)}</th>{"".join(cells)}</tr>')
    return f"""
<section class="card" aria-labelledby="mx-h">
  <div class="card-head">
    <h2 id="mx-h">Full log, side by side</h2>
    <p class="card-sub">The source sheet, normalised. Every row every unit was measured on.</p>
  </div>
  <div class="mxwrap">
    <table class="mx">
      <thead><tr><th scope="col" class="corner">Metric</th>{thead}</tr></thead>
      <tbody>{"".join(body)}</tbody>
    </table>
  </div>
</section>"""


def render(units, block_order, blocks, resolve, unit_phases):
    chips = "".join(
        f'<button class="chip mono" role="tab" aria-selected="false" data-f="{esc(u)}">{esc(u)}</button>'
        for u in units)

    cards = []
    for u in units:
        phases = unit_phases[u]
        tiles = "".join(
            f'<div class="tile"><span class="k">{k}</span>'
            f'<span class="v mono">{v}</span><span class="s">{s}</span></div>'
            for k, v, s in unit_summary(phases))
        panels = "".join(render_phase(p) for p in phases)
        cards.append(f"""
<article class="card unit-card" id="u-{esc(u)}" data-unit="{esc(u)}">
  <div class="uhead">
    <div class="uname">
      <h3 class="mono">{esc(u)}</h3>
      <p class="usub">{unit_subline(phases)}</p>
    </div>
    <div class="tiles">{tiles}</div>
  </div>
  <div class="phases">{panels}</div>
</article>""")

    # portfolio totals
    manual = sum(p["effort"] for ph in unit_phases.values() for p in ph
                 if p["slug"] in ("qa", "mep") and p["effort"] is not None)
    capture = sum(p["effort"] for ph in unit_phases.values() for p in ph
                  if p["slug"] == "cap" and p["effort"] is not None)
    processing = sum(p["effort"] for ph in unit_phases.values() for p in ph
                     if p["slug"] == "proc" and p["effort"] is not None)
    all_dates = [d[0] for ph in unit_phases.values() for p in ph
                 for d in (p["start"], p["end"]) if d]
    span = (f'{fmt_day(min(all_dates))} &ndash; {fmt_day(max(all_dates))} '
            f'{max(all_dates).year}') if all_dates else "&mdash;"

    strip = "".join(f'<div><span class="k">{k}</span><span class="v mono">{v}</span>'
                    f'<span class="s">{s}</span></div>' for k, v, s in [
        ("Units", str(len(units)), "in the pilot"),
        ("Window", f'<span class="sm">{span}</span>', "first to last logged activity"),
        ("Manual manhours", fmt_dur(manual), "QA and MEP snagging, all units"),
        ("Capture manhours", fmt_dur(capture), "onsite photo capture"),
        ("Processing time", fmt_dur(processing), "elapsed, not manned"),
    ])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>DAMAC snagging pilot &mdash; activity log</title>
<meta name="description" content="Time and effort logged for each unit in the DAMAC x CONXAI snagging pilot.">
<style>
:root{{
  --page:#eef0ee; --surface:#ffffff; --panel:#f7f8f7;
  --ink:#14171a; --ink2:#4d545c; --muted:#858d95;
  --line:#dcdfdc; --line2:#eaece9;
  --c-qa:#8a5cc4; --c-mep:#2f6ea8; --c-cap:#2f6f4f; --c-proc:#c98a1e;
  --warn:#a2373f;
}}
*{{box-sizing:border-box}}
html{{-webkit-text-size-adjust:100%;scroll-behavior:smooth}}
body{{margin:0;background:var(--page);color:var(--ink);
  font:15px/1.55 ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}}
.mono{{font-family:ui-monospace,SFMono-Regular,Menlo,"Roboto Mono",monospace}}
.wrap{{max-width:1240px;margin:0 auto;padding:34px 22px 90px}}

.top{{padding-bottom:18px;border-bottom:2px solid var(--ink);margin-bottom:22px}}
.top-inner{{display:flex;flex-wrap:wrap;gap:20px;align-items:flex-start;justify-content:space-between}}
.eyebrow{{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);
  font-weight:700;margin:0 0 7px}}
h1{{font-size:34px;line-height:1.05;margin:0;letter-spacing:-.02em;font-weight:680}}
.subline{{color:var(--ink2);font-size:13.5px;margin:9px 0 0;max-width:60ch}}
.provenance{{text-align:right;font-size:12px;color:var(--muted);line-height:1.75;flex:none}}
.provenance b{{color:var(--ink2);font-weight:600}}
.wordmark{{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-weight:700;
  letter-spacing:.16em;font-size:13px;color:var(--ink);margin:0 0 10px}}

.strip{{display:grid;grid-template-columns:repeat(auto-fit,minmax(168px,1fr));gap:1px;
  background:var(--line);border:1px solid var(--line);border-radius:12px;overflow:hidden;
  margin-bottom:26px}}
.strip>div{{background:var(--surface);padding:14px 16px}}
.strip .k,.tile .k{{display:block;font-size:10.5px;text-transform:uppercase;letter-spacing:.07em;
  color:var(--muted);font-weight:650;line-height:1.35}}
.tile .k{{min-height:2.7em}}
.strip .v{{display:block;font-size:21px;font-weight:700;letter-spacing:-.02em;margin-top:4px}}
.strip .v .sm{{font-size:14.5px;letter-spacing:-.01em;white-space:nowrap}}
.strip .s{{display:block;font-size:11.6px;color:var(--ink2);margin-top:3px}}

.filters{{display:flex;flex-wrap:wrap;gap:9px;align-items:center;margin-bottom:20px;
  position:sticky;top:0;z-index:5;background:var(--page);padding:10px 0 11px}}
.filters::after{{content:"";position:absolute;left:0;right:0;bottom:0;height:1px;background:var(--line)}}
.flabel{{font-size:11px;letter-spacing:.07em;text-transform:uppercase;color:var(--muted);font-weight:650}}
.chips{{display:flex;flex-wrap:wrap;gap:0;border:1px solid var(--line);border-radius:8px;
  overflow:hidden;background:var(--surface)}}
.chip{{font:inherit;font-size:12.5px;padding:8px 13px;border:none;background:none;cursor:pointer;
  color:var(--ink2);border-right:1px solid var(--line)}}
.chip:last-child{{border-right:none}}
.chip:hover{{background:var(--panel);color:var(--ink)}}
.chip[aria-selected="true"]{{background:var(--ink);color:#fff;font-weight:600}}
.chip:focus-visible{{outline:2px solid #1b6fc4;outline-offset:-2px}}
.showing{{font-size:12.5px;color:var(--muted);margin-left:auto}}

.card{{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:20px;
  margin-bottom:20px}}
.card-head{{margin-bottom:14px}}
h2{{font-size:17px;margin:0;letter-spacing:-.01em;font-weight:670}}
.card-sub{{color:var(--ink2);font-size:12.8px;margin:5px 0 0}}

.uhead{{display:flex;flex-wrap:wrap;gap:18px;align-items:flex-start;justify-content:space-between;
  padding-bottom:16px;border-bottom:1px solid var(--line);margin-bottom:16px}}
.uname h3{{font-size:26px;margin:0;font-weight:700;letter-spacing:-.02em}}
.usub{{color:var(--ink2);font-size:12.8px;margin:5px 0 0}}
.usub b{{color:var(--ink);font-weight:600}}
.tiles{{display:grid;grid-template-columns:repeat(3,minmax(124px,1fr));gap:9px;flex:0 1 470px}}
.tile{{background:var(--panel);border:1px solid var(--line2);border-radius:9px;padding:10px 12px}}
.tile .v{{display:block;font-size:19px;font-weight:700;letter-spacing:-.02em;margin-top:3px}}
.tile .s{{display:block;font-size:11.2px;color:var(--ink2);margin-top:3px;line-height:1.45}}

.phases{{display:grid;grid-template-columns:repeat(auto-fit,minmax(232px,1fr));gap:12px}}
.phase{{border:1px solid var(--line2);border-radius:10px;padding:0 13px 12px;
  border-top:3px solid var(--line);background:var(--surface)}}
.ph-qa{{border-top-color:var(--c-qa)}} .ph-mep{{border-top-color:var(--c-mep)}}
.ph-cap{{border-top-color:var(--c-cap)}} .ph-proc{{border-top-color:var(--c-proc)}}
.phase.is-empty{{background:var(--panel);border-top-color:var(--line)}}
.phase header{{display:flex;align-items:baseline;justify-content:space-between;gap:8px;
  padding:12px 0 9px;border-bottom:1px solid var(--line2);margin-bottom:9px}}
.phase h4{{font-size:12.5px;margin:0;font-weight:670;letter-spacing:-.005em}}
.pill{{font-size:10px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;
  padding:2px 7px;border-radius:5px;flex:none}}
.pf-onsite{{background:#eef1f4;color:#41525f;border:1px solid #dbe2e8}}
.pf-conxai{{background:#14171a;color:#fff}}
.phase dl{{margin:0;display:flex;flex-direction:column}}
.phase dl>div{{display:flex;gap:10px;align-items:baseline;justify-content:space-between;
  padding:5px 0;border-top:1px solid #f2f3f2}}
.phase dl>div:first-child{{border-top:none}}
.phase dt{{font-size:11.8px;color:var(--muted);flex:none}}
.phase dd{{margin:0;font-size:12.6px;text-align:right;color:var(--ink2)}}
.phase dd.num{{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--ink)}}
.phase dd.strong{{font-weight:700}}
.unit-word{{color:var(--muted);font-size:11.5px}}
.phase .none{{margin:2px 0 4px;font-size:12.6px;color:var(--muted)}}
.phase .none .sub{{display:block;font-size:11.5px;margin-top:4px}}

.warn{{display:inline-flex;align-items:center;justify-content:center;width:14px;height:14px;
  margin-left:5px;border-radius:50%;background:var(--warn);color:#fff;font-size:9.5px;
  font-weight:800;vertical-align:middle;cursor:help;position:relative}}
.warn:not([data-tip]){{cursor:default}}
.warn[data-tip]:hover::after,.warn[data-tip]:focus::after{{content:attr(data-tip);position:absolute;bottom:calc(100% + 7px);
  left:50%;transform:translateX(-50%);width:max-content;max-width:250px;text-align:left;
  background:var(--ink);color:#fff;font-size:11.5px;font-weight:400;line-height:1.45;
  padding:8px 10px;border-radius:7px;z-index:20;pointer-events:none}}

.cal-legend{{display:flex;flex-wrap:wrap;gap:14px;font-size:12px;color:var(--ink2);margin-bottom:12px}}
.cal-legend span{{display:flex;align-items:center;gap:6px}}
.cal-legend i,.cal-c i{{display:block;border-radius:2px}}
.cal-legend i{{width:11px;height:11px}}
.c-qa{{background:var(--c-qa)}} .c-mep{{background:var(--c-mep)}}
.c-cap{{background:var(--c-cap)}} .c-proc{{background:var(--c-proc)}}
.cal-scroll{{overflow-x:auto}}
.cal{{min-width:520px}}
.cal-row{{display:flex;align-items:stretch;gap:10px}}
.cal-u{{flex:0 0 76px;font-size:12.5px;font-weight:700;color:var(--ink);text-decoration:none;
  display:flex;align-items:center}}
.cal-u:hover{{text-decoration:underline}}
.cal-cells{{display:grid;grid-auto-flow:column;grid-auto-columns:minmax(28px,1fr);gap:3px;flex:1}}
.cal-head .cal-d{{text-align:center;padding-bottom:6px}}
.cal-d .dow{{display:block;font-size:9.5px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted)}}
.cal-d .dnum{{display:block;font-family:ui-monospace,monospace;font-size:12px;color:var(--ink2);font-weight:600}}
.cal-d.wknd .dnum,.cal-d.wknd .dow{{color:#b3b9be}}
.cal-c{{height:26px;border-radius:5px;background:var(--panel);border:1px solid var(--line2);
  display:flex;gap:2px;align-items:stretch;padding:3px;margin-bottom:5px}}
.cal-c.wknd{{background:#f0f1ef}}
.cal-c i{{flex:1;min-width:4px}}
.cal-row[hidden]{{display:none}}

.mxwrap{{overflow-x:auto;border:1px solid var(--line);border-radius:10px}}
table.mx{{width:100%;border-collapse:collapse;font-size:12.6px}}
.mx th,.mx td{{padding:8px 10px;text-align:left;border-bottom:1px solid var(--line2);white-space:nowrap}}
.mx thead th{{position:sticky;top:0;background:var(--panel);font-size:11px;letter-spacing:.05em;
  text-transform:uppercase;color:var(--ink2);font-weight:700;border-bottom:1px solid var(--line);z-index:2}}
.mx tbody th{{font-weight:500;color:var(--ink2);position:sticky;left:0;background:var(--surface);z-index:1}}
.mx .corner{{position:sticky;left:0;background:var(--panel);z-index:3}}
.mx tr.grp th{{background:var(--panel);font-size:11px;letter-spacing:.06em;text-transform:uppercase;
  font-weight:700;color:var(--ink);position:sticky;left:0}}
.mx td.num{{font-family:ui-monospace,SFMono-Regular,Menlo,monospace}}
.mx td.na{{color:var(--muted)}}
.mx tbody tr:hover td{{background:#fafbfa}}

.notes{{margin-top:26px;font-size:12.4px;color:var(--ink2);line-height:1.75}}
.notes h2{{font-size:13px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);
  margin:0 0 8px;font-weight:700}}
.notes ul{{margin:0;padding-left:18px}}
.notes li{{margin-bottom:6px}}
.foot{{margin-top:22px;padding-top:14px;border-top:1px solid var(--line);
  font-size:11.8px;color:var(--muted);line-height:1.7}}
.foot a{{color:var(--ink2)}}

@media (max-width:720px){{
  .wrap{{padding:24px 15px 70px}}
  h1{{font-size:27px}}
  .provenance{{text-align:left}}
  .tiles{{grid-template-columns:repeat(3,minmax(96px,1fr));flex:1 1 100%}}
  .filters{{position:static}}
}}
@media print{{
  body{{background:#fff}} .filters{{display:none}} .card{{break-inside:avoid}}
}}
</style>
</head>
<body>
<div class="wrap">

<header class="top">
  <div class="top-inner">
    <div>
      <p class="eyebrow">DAMAC &times; CONXAI snagging pilot</p>
      <h1>Activity log</h1>
      <p class="subline">What each unit cost in time &mdash; manual QA and MEP snagging onsite,
      against photo capture and CONXAI processing. One card per unit.</p>
    </div>
    <div class="provenance">
      <p class="wordmark">CONXAI</p>
      Source <b>Damac snagging schedules &mdash; Activity logs</b><br>
      Units <b>{len(units)}</b> &middot; Generated <b>{GENERATED:%d %b %Y}</b><br>
      Times as recorded onsite (GST)
    </div>
  </div>
</header>

<div class="strip">{strip}</div>

<div class="filters" role="tablist" aria-label="Filter by unit">
  <span class="flabel">Unit</span>
  <div class="chips">
    <button class="chip" role="tab" aria-selected="true" data-f="all">All</button>
    {chips}
  </div>
  <span class="showing" id="showing">Showing all {len(units)} units</span>
</div>

{render_calendar(units, unit_phases)}

{"".join(cards)}

{render_matrix(units, block_order, blocks, resolve)}

<div class="notes">
  <h2>Reading the log</h2>
  <ul>
    <li><b>Duration</b> is start to end less any recorded break. <b>Manhours</b> is that duration
      multiplied by the number of inspectors on site.</li>
    <li><b>Processing time</b> is elapsed pipeline time, not manned effort, so it is kept out of
      the manhours totals.</li>
    <li>A <span class="warn">!</span> marks a figure that does not agree with
      the times recorded beside it. Hover it for the arithmetic. Values are shown exactly as the
      sheet records them &mdash; nothing has been corrected.</li>
    <li>&mdash; means the sheet records N/A; <b>tbc</b> means the work is scheduled but not yet done.</li>
  </ul>
</div>

<p class="foot">
  Generated from <span class="mono">data/activity-logs.csv</span> by
  <span class="mono">build.py</span> &middot; {GENERATED:%d %b %Y}.
  Re-run the script after updating the sheet to refresh this page.
</p>

</div>
<script>
(function(){{
  var chips = Array.prototype.slice.call(document.querySelectorAll('.chip'));
  var cards = Array.prototype.slice.call(document.querySelectorAll('.unit-card'));
  var rows  = Array.prototype.slice.call(document.querySelectorAll('.cal-row[data-unit]'));
  var out   = document.getElementById('showing');
  var total = cards.length;

  function apply(f, push){{
    chips.forEach(function(c){{ c.setAttribute('aria-selected', String(c.dataset.f === f)); }});
    cards.forEach(function(c){{ c.hidden = !(f === 'all' || c.dataset.unit === f); }});
    rows.forEach(function(r){{ r.hidden = !(f === 'all' || r.dataset.unit === f); }});
    out.textContent = f === 'all' ? 'Showing all ' + total + ' units' : 'Showing ' + f + ' only';
    if (push) {{
      history.replaceState(null, '', f === 'all' ? location.pathname : '#' + f);
    }}
  }}

  chips.forEach(function(c){{
    c.addEventListener('click', function(){{ apply(c.dataset.f, true); }});
  }});

  var known = chips.map(function(c){{ return c.dataset.f; }});
  var hash = decodeURIComponent(location.hash.replace(/^#(u-)?/, ''));
  apply(known.indexOf(hash) > -1 ? hash : 'all', false);
}})();
</script>
</body>
</html>
"""


def main():
    units, block_order, blocks = read_matrix()
    resolve = resolve_dates(units, block_order, blocks)
    unit_phases = build_units(units, block_order, blocks, resolve)
    OUT_PATH.write_text(render(units, block_order, blocks, resolve, unit_phases),
                        encoding="utf-8")
    print(f"wrote {OUT_PATH} ({OUT_PATH.stat().st_size:,} bytes) "
          f"for {len(units)} units: {', '.join(units)}")


if __name__ == "__main__":
    main()
