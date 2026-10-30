#!/usr/bin/env python3
"""Render data/performance-review.json into the Performance review pages.

Performance analysis of AI on visual snags, for Lagoons - Ibiza T240, T242, T243
and T245: each unit's onsite (manual) snags beside the AI snags on the ConXAI
dashboard. performance-review.html is the tab's landing page, one row per unit;
each unit has its own page, performance-review-<unit>.html.

The JSON is a snapshot exported from the snag-match workspace
(plumbline_eval/export_performance_review.py). It holds, per unit:

- manual: the target visual snags within the area the scan captured, each with
  its match level (certain, likely, none), whether it counts towards recall,
  and the AI snag shown beside it (or, when the AI detection is not a separate
  snag on the dashboard, the detection itself, marked as merged);
- ai_matched: the dashboard AI snags matched to an onsite snag of any type;
- ai_only: the dashboard AI snags no onsite snag covers, deleted or not, and
  material or non-material.

Photos are in assets/performance-review/<unit>/, one 640 px copy each, used for
the thumbnail and the enlarged view alike. A dashboard photo can show several
AI snags, so it is stored without boxes and each AI snag's boxes are drawn over
it on the page. Every count on the pages is recomputed here from those rows.
"""

import json
from collections import Counter
from datetime import date
from pathlib import Path

import build_time_motion
import theme
from theme import GENERATED, esc

ROOT = Path(__file__).parent
DATA_PATH = ROOT / "data" / "performance-review.json"
SLUG = "perf"
TITLE = "Performance analysis of AI on visual snags"

LEVEL = {"certain": ("Certain match", "lv-certain"), "likely": ("Likely match", "lv-likely"),
         "none": ("No match", "lv-none")}
ORDER = {"certain": 0, "likely": 1, "none": 2}
PRIO = {"high": "p-high", "medium": "p-med", "low": "p-low"}
MAX_PICS = 6


def unit_file(unit):
    return f"performance-review-{unit.lower()}.html"


def pct(n, d):
    return f"{100 * n / d:.0f}%" if d else "—"


# ------------------------------------------------------------- arithmetic ---

def tally(u):
    m = u["manual"]
    lv = Counter(r["level"] for r in m)
    deleted = [a for a in u["ai_only"] if a["deleted"]]
    added = [a for a in u["ai_only"] if not a["deleted"]]
    return {
        "manual": len(m), "certain": lv["certain"], "likely": lv["likely"], "none": lv["none"],
        "covered": lv["certain"] + lv["likely"], "recall": sum(r["recall"] for r in m),
        "ai": len(u["ai_matched"]) + len(u["ai_only"]), "matched": len(u["ai_matched"]),
        "matched_deleted": sum(a["deleted"] for a in u["ai_matched"]), "deleted": len(deleted),
        "added": len(added), "added_material": sum(a["material"] for a in added),
        "added_nonmat": sum(not a["material"] for a in added),
    }


# ----------------------------------------------------------------- pieces ---

def unit_nav(current, units):
    links = [("All units", "performance-review.html", current is None)] + [
        (u, unit_file(u), u == current) for u in units]
    return ('<nav class="unitnav" aria-label="Select unit">' + "".join(
        f'<a href="{f}"' + (' aria-current="page"' if cur else "") + f">{esc(label)}</a>"
        for label, f, cur in links) + "</nav>")


def bar(title, total, parts):
    """parts: (label, n, css class); a part of 0 stays in the key but not the bar."""
    seg = "".join(f'<i class="{c}" style="flex:{n}" title="{esc(lb)}: {n}"><b>{n}</b></i>' for lb, n, c in parts if n)
    key = "".join(f'<span><i class="sw {c}"></i> {esc(lb)} <b>{n}</b></span>' for lb, n, c in parts)
    return (f'<div class="bar"><div class="bh"><span class="bt">{esc(title)}</span><span class="bn">{total}</span></div>'
            f'<div class="seg" role="img" aria-label="{esc(title)}">{seg}</div><div class="key">{key}</div></div>')


def box_spans(boxes):
    """An AI snag's boxes (fractions of the photo) drawn over its dashboard photo."""
    return "".join(f'<span class="bx" style="left:{x:.2%};top:{y:.2%};width:{w:.2%};height:{h:.2%}"></span>'
                   for x, y, w, h in boxes)


def thumbs(items):
    """items: (photo, label, tag) or, for a dashboard photo, (photo, label, tag, the snag's boxes)."""
    out = [f'<button class="th" data-full="{esc(p)}" data-name="{esc(label)}"'
           + (f' data-boxes="{esc(json.dumps(bx[0]))}"' if bx and bx[0] else "") + ' aria-label="Open photo">'
           f'<img loading="lazy" src="{esc(p)}" alt="">{box_spans(bx[0] if bx else [])}<span class="src {tag.lower()}">{tag}</span></button>'
           for p, label, tag, *bx in items if p][:MAX_PICS]
    return f'<span class="pic-list">{"".join(out)}</span>' if out else ""


def ai_desc(a, flags=""):
    sev = f'<span class="sev">&middot; {esc(a["severity"])}</span>' if a["severity"] else ""
    return (f'<div class="one"><span class="aid" title="Snag ID on the ConXAI dashboard">#{a["id"]}</span>{flags}'
            f'<p class="d"><b>{esc(a["element"])}</b> &mdash; {esc(a["text"])}{sev}</p></div>')


def ai_pics(a):
    return [(g["src"], f'#{a["id"]} {a["element"] or "AI snag"}', "A", g["boxes"]) for g in a["images"]]


def kind_tag(a):
    return ('<span class="nm mt" title="Not tagged non-material on the dashboard">Material</span>' if a["material"]
            else '<span class="nm" title="Tagged non-material on the dashboard">Non-material</span>')


def manual_row(r):
    name, cls = LEVEL[r["level"]]
    prio = PRIO.get(r["priority"].lower(), "")
    ai = r["ai"]
    if ai is None:
        pics, desc = "", '<p class="d meta">no AI match</p>'
    elif ai["merged"]:
        pics = thumbs([(d["image"], d["text"] or "AI detection", "A") for d in ai["detections"]])
        desc = '<span class="mrg">Snag merged with another</span>' + "".join(
            '<div class="one"><span class="aid none" title="Not a separate snag on the dashboard">no separate dashboard ID</span>'
            f'<p class="d">{esc(d["text"])}</p></div>' for d in ai["detections"][:4])
    else:
        pics = thumbs([p for a in ai["snags"] for p in ai_pics(a)])
        desc = "".join(ai_desc(a) for a in ai["snags"])
    photos = [(p, f'Onsite {r["onsite_id"]} photo {k + 1}', "M") for k, p in enumerate(r["photos"])]
    return (f'<tr class="r-manual" data-st="manual" data-trade="{esc(r["trade"])}" data-room="{esc(r["room"].upper())}" '
            f'data-prio="{prio}" data-level="{r["level"]}">'
            f'<td class="c-snag"><span class="badge b-man">Manual</span><span class="lv {cls}">{name}</span>'
            f'<p class="t">{esc(r["title"])}</p><p class="meta">{esc(r["room"])} <span class="sep">/</span> '
            f'<span class="mono">Onsite {esc(r["onsite_id"])}</span></p></td>'
            f'<td class="c-trade">{esc(r["trade"])}</td><td class="c-pic">{thumbs(photos)}</td>'
            f'<td class="c-man"><div class="sig"><span class="det yes" title="Logged on the walk">&#10003;</span>'
            f'<span class="dot {prio}"></span><span class="plab">{esc(r["priority"])}</span></div>'
            f'<p class="d">{esc(r["details"])}</p></td><td class="c-ai-pic">{pics}</td><td class="c-ai-desc">{desc}</td></tr>')


def ai_row(a):
    flags = ('<span class="del" title="Deleted on the QA/QC board">Deleted</span>' if a["deleted"] else "") + kind_tag(a)
    return (f'<tr class="r-ai-only" data-st="ai" data-trade="{esc(a["trade"])}" data-room="{esc(a["room"].upper())}" '
            f'data-prio="{PRIO.get(a["severity"].lower(), "")}" data-level="{"deleted" if a["deleted"] else "additional"}">'
            f'<td class="c-snag"><span class="badge b-ai">AI only</span><p class="meta">{esc(a["room"])}</p></td>'
            f'<td class="c-trade">{esc(a["trade"])}</td><td class="c-pic"></td><td class="c-man"></td>'
            f'<td class="c-ai-pic">{thumbs(ai_pics(a))}</td><td class="c-ai-desc">{ai_desc(a, flags)}</td></tr>')


def render_stats(t, qaqc):
    return f"""<section>
<h2>Snag Coverage and Stats</h2>
<div class="card statgrid">
<ul class="stats">
  <li><span class="n">{t["manual"]}</span><span class="lb">manually-logged snags<span class="qual">Target visual snags within the area captured</span></span></li>
  <li><span class="n">{t["ai"]}</span><span class="lb">AI-logged snags<span class="qual">AI snags on the ConXAI dashboard (roof excluded)</span></span></li>
  <li><span class="n">{t["added"]}</span><span class="lb">snags detected by AI, but not by Manual<span class="qual">additional true positive AI snags:
    not covered by onsite and not deleted &middot; <b>{t["added_material"]}</b> tagged <span class="nm mt">material</span>,
    <b>{t["added_nonmat"]}</b> tagged <span class="nm">non-material</span> &middot; another <b>{t["deleted"]}</b> were deleted on the board</span></span></li>
  <li><span class="n">{t["none"]}</span><span class="lb">snags detected by Manual, but not by AI</span></li>
  <li><span class="n">{t["covered"]}</span><span class="lb">snags detected by both Manual and AI<span class="qual"><b>{t["certain"]}</b> certain match &middot;
    <b>{t["likely"]}</b> likely match</span></span></li>
</ul>
<div class="bars">
{bar("Manual snags", f'<b>{t["manual"]}</b> total &middot; <b>{t["covered"]}</b> covered by AI',
     [("Covered by AI", t["covered"], "s-both"), ("Not covered by AI", t["none"], "s-notcov")])}
{bar("AI snags", f'<b>{t["ai"]}</b> total &middot; <b>{t["added"]}</b> additional true positives '
     f'(<b>{t["added_material"]}</b> material, <b>{t["added_nonmat"]}</b> non-material)',
     [("Matched to manual", t["matched"], "s-both"), ("Deleted", t["deleted"], "s-del"),
      ("Additional true positives, material", t["added_material"], "s-add"),
      ("Additional true positives, non-material", t["added_nonmat"], "s-add-nm")])}
<div class="mini"><div><span class="k">Recall</span><span class="v">{pct(t["recall"], t["manual"])}</span>
<span class="s">{t["recall"]} of {t["manual"]} in-scope manual snags</span></div></div>
<p class="statnote">Recall is measured over the <b>{t["manual"]}</b> in-scope manual snags (the target visual snags within
the area the scan captured). AI snags matched to manual include matches to onsite snags of every type""" + (
        f', and <b>{t["matched_deleted"]}</b> matched snags that were also deleted on the board' if t["matched_deleted"] else "") + f"""; Deleted
counts only AI snags no onsite snag covers. Deletions as on the QA/QC board on {date.fromisoformat(qaqc):%d %b %Y}.</p>
</div>
</div>
</section>"""


GLOSSARY = """<section>
<h2>Glossary</h2>
<div class="card"><ul class="gloss">
  <li><b>Recall</b> &mdash; the percentage of in-scope manually logged snags captured by AI with a useful description, defining
    the correct repair work, correct trade and location.</li>
  <li><b>Certain match</b> &mdash; the AI snag fully describes the onsite snag. <b>Likely match</b> &mdash; the AI snag partly
    describes it. <b>No match</b> &mdash; no AI snag covers it.</li>
  <li><b>Snag merged with another</b> &mdash; the AI detected the onsite snag, but the detection is not a separate snag on the
    dashboard: it sits with another AI snag. The AI detection is shown, without a dashboard snag ID.</li>
  <li><b>AI only</b> &mdash; AI snags on the dashboard that no onsite snag covers. <b>Deleted</b> ones were deleted on the QA/QC
    board; the rest are additional true positive AI snags. <b>Material</b> / <b>Non-material</b> &mdash; the snag's tag on the
    dashboard; snags not tagged non-material count as material.</li>
</ul></div>
</section>"""


def render_table(u):
    rows = ([(r["room"].upper(), 0, ORDER[r["level"]], r["onsite_id"], manual_row(r)) for r in u["manual"]]
            + [(a["room"].upper(), 1, a["deleted"], a["id"], ai_row(a)) for a in u["ai_only"]])
    rows.sort(key=lambda r: r[:4])
    trades = sorted({r["trade"] for r in u["manual"]} | {a["trade"] for a in u["ai_only"]} - {""})
    rooms = sorted({r["room"].upper() for r in u["manual"]} | {a["room"].upper() for a in u["ai_only"]} - {""})
    lv = Counter(r["level"] for r in u["manual"])
    levels = [(k, LEVEL[k][0]) for k in ORDER if lv[k]] + [("deleted", "AI only &middot; deleted"),
                                                          ("additional", "AI only &middot; not deleted")]
    opts = lambda vals: "".join(f"<option>{esc(v)}</option>" for v in vals)  # noqa: E731
    return f"""<section>
<h2>Consolidated Snag List <span class="h2sub">(AI + Manual)</span></h2>
<div class="controls">
  <div class="chips" role="group" aria-label="Filter by source"><button class="chip" data-f="all" aria-pressed="true">All</button><button
    class="chip" data-f="manual" aria-pressed="false">Manual snags</button><button class="chip" data-f="ai" aria-pressed="false">AI only</button></div>
  <input type="search" id="q" placeholder="Search description, room, trade, ID" aria-label="Search">
  <select id="trade" aria-label="Trade"><option value="">All trades</option>{opts(trades)}</select>
  <select id="room" aria-label="Room"><option value="">All rooms</option>{opts(rooms)}</select>
  <select id="prio" aria-label="Priority"><option value="">Any priority</option><option value="p-high">High</option><option
    value="p-med">Medium</option><option value="p-low">Low</option></select>
  <select id="level" aria-label="Match level"><option value="">All match levels</option>{"".join(f'<option value="{k}">{n}</option>' for k, n in levels)}</select>
  <label class="tog"><input type="checkbox" id="clamp" checked> Compact rows</label>
  <span class="count" id="count"></span>
</div>
<div class="tablewrap"><table>
<colgroup><col class="w-snag"><col class="w-trade"><col class="w-pic"><col class="w-man"><col class="w-ai-pic"><col class="w-ai-desc"></colgroup>
<thead><tr><th>Snag<span class="h2l">Room &middot; id</span></th><th>Trade</th><th>Picture</th>
<th>Manual<span class="h2l">Logged &middot; Priority &middot; Description</span></th><th>AI Pictures</th>
<th>AI description<span class="h2l">Snag ID &middot; description</span></th></tr></thead>
<tbody id="tb">
{chr(10).join(r[4] for r in rows)}
</tbody></table>
<p class="empty" id="empty" hidden>No snags match these filters.</p></div>
</section>
<dialog id="lb"><div class="lbbar"><span class="lbname" id="lbname"></span><button type="button" id="lbzoom">View actual size</button><button
  type="button" id="lbx" aria-label="Close">&times;</button></div><div class="lbview"><div class="lbw" id="lbw"><img id="lbi" alt="Snag photo"></div></div></dialog>"""


def foot():
    return f"""<p class="foot">
  Generated from <span class="mono">data/performance-review.json</span> by
  <span class="mono">build_performance_review.py</span> &middot; {GENERATED:%d %b %Y}.
</p>"""


def page(title_html, title_text, nav, body, script=""):
    masthead = theme.masthead(SLUG, title_html, TITLE, nav)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>DAMAC snagging pilot &mdash; {esc(title_text)}</title>
<meta name="description" content="{TITLE}: onsite snags beside the AI snags on the ConXAI dashboard.">
<style>
{theme.CHROME_CSS}

{PAGE_CSS}
</style>
</head>
<body>
<div class="wrap">

{masthead}

{body}

{foot()}

</div>{script}
</body>
</html>
"""


def render_unit(u, units, qaqc):
    body = render_stats(tally(u), qaqc) + "\n\n" + GLOSSARY + "\n\n" + render_table(u)
    return page(f'Unit <span class="mono">{esc(u["unit"])}</span>', f'performance review {u["unit"]}',
                unit_nav(u["unit"], units), body, f"\n<script>{JS}</script>")


def render_index(data):
    units = [u["unit"] for u in data["units"]]
    ts = {u["unit"]: tally(u) for u in data["units"]}
    tot = {k: sum(t[k] for t in ts.values()) for k in next(iter(ts.values()))}
    strip = "".join(f'<div><span class="k">{k}</span><span class="v mono">{v}</span><span class="s">{s}</span></div>' for k, v, s in [
        ("Units", str(len(units)), ", ".join(units)),
        ("Manual snags", str(tot["manual"]), "target visual snags within the area captured"),
        ("Covered by AI", str(tot["covered"]), f'{pct(tot["covered"], tot["manual"])} of manual snags'),
        ("Recall", pct(tot["recall"], tot["manual"]), f'{tot["recall"]} of {tot["manual"]}'),
        ("AI snags", str(tot["ai"]), "on the ConXAI dashboard (roof excluded)"),
        ("Additional true positives", str(tot["added"]), f'{tot["added_material"]} material, {tot["added_nonmat"]} non-material'),
    ])
    rows = "".join(
        f'<tr><td class="rl"><b><a href="{unit_file(u)}">{esc(u)}</a></b></td><td class="num">{t["manual"]}</td>'
        f'<td class="num">{t["covered"]}</td><td class="num">{pct(t["recall"], t["manual"])}<span class="sub">{t["recall"]} of {t["manual"]}</span></td>'
        f'<td class="num">{t["ai"]}</td><td class="num">{t["matched"]}</td><td class="num">{t["deleted"]}</td>'
        f'<td class="num">{t["added"]}<span class="sub">{t["added_material"]} material &middot; {t["added_nonmat"]} non-material</span></td></tr>'
        for u, t in ts.items())
    body = f"""<div class="strip">{strip}</div>

<section class="card">
<div class="card-head"><h2>By unit</h2><p class="card-sub">Open a unit for its snag-by-snag list.</p></div>
<div class="tablescroll"><table class="cmp"><thead><tr><th>Unit</th><th>Manual snags</th><th>Covered by AI</th><th>Recall</th>
<th>AI snags</th><th>Matched to manual</th><th>Deleted</th><th>Additional true positives</th></tr></thead>
<tbody>{rows}</tbody></table></div>
</section>

{GLOSSARY}"""
    return page("Performance review", "performance review", unit_nav(None, units), body)


# ------------------------------------------------------------------ style ---

# The snag list's own rules; the chrome (tokens, masthead, tabs, cards, footer) is theme.CHROME_CSS.
PAGE_CSS = """
:root{--high:#d03b3b;--med:#ef8f2c;--low:#3b82d0;--yes:#17914a;--no:#cf3232;
  --both:#2f6f4f;--man:#8a5cc4;--ai:#2f6ea8;--focus:#1b6fc4}
.wrap{max-width:1900px}
.top h1 .mono{font-weight:700}
.top .subline{font-size:17px;font-weight:500}
.unitnav{display:flex;flex-wrap:wrap;gap:6px;justify-content:flex-end;margin-top:6px}
.unitnav a{font-size:13px;font-weight:650;text-decoration:none;color:var(--ink2);border:1px solid var(--line);
  background:var(--surface);border-radius:999px;padding:5px 13px;line-height:1.4}
.unitnav a:hover{border-color:var(--ink2);color:var(--ink)}
.unitnav a[aria-current="page"]{background:var(--ink);border-color:var(--ink);color:#fff}
section{margin-bottom:26px}
section>h2{margin:0 0 14px}
.h2sub{font-weight:500;color:var(--muted)}
.card>.gloss{margin:0}

.statgrid{display:grid;gap:18px;grid-template-columns:minmax(0,1.35fr) minmax(0,1fr);align-items:start}
ul.stats{list-style:none;margin:0;padding:0;display:flex;flex-direction:column}
ul.stats li{display:flex;gap:14px;align-items:baseline;padding:9px 0;border-top:1px solid var(--line2)}
ul.stats li:first-child{border-top:none;padding-top:0}
.n{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:23px;font-weight:700;
  letter-spacing:-.02em;min-width:58px;text-align:right;flex:none}
.lb{font-size:13.5px;color:var(--ink2)}
.qual{display:block;color:var(--muted);font-size:12.2px;margin-top:3px;line-height:1.5}
.qual b{color:var(--ink2)}
.bars{display:flex;flex-direction:column;gap:18px}
.bar .bh{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:baseline;gap:4px 12px;margin-bottom:7px}
.bar .bt{font-size:12px;text-transform:uppercase;letter-spacing:.07em;font-weight:700;color:var(--ink2)}
.bar .bn{font-size:13px;color:var(--ink2)}
.bar .bn b{color:var(--ink);font-family:ui-monospace,monospace}
.seg{display:flex;height:34px;border-radius:7px;overflow:hidden;gap:2px;margin:0 0 8px}
.seg i{display:flex;align-items:center;justify-content:center;color:#fff;font-style:normal;font-size:12px;min-width:26px}
.seg b{font-family:ui-monospace,monospace;font-weight:700}
.key{display:flex;flex-wrap:wrap;gap:12px;font-size:12.2px;color:var(--ink2)}
.key span{display:flex;align-items:center;gap:6px}
.sw{width:11px;height:11px;border-radius:3px;flex:none}
.s-both{background:var(--both)}.s-notcov{background:var(--man)}.s-del{background:#8d949b}.s-add{background:var(--ai)}
.s-add-nm{background:repeating-linear-gradient(135deg,#6f9ccb 0 6px,#5a8bbf 6px 12px)}
.mini>div{background:var(--panel);border:1px solid var(--line2);border-radius:9px;padding:11px 13px}
.mini .k,.mini .v,.mini .s{display:block}
.mini .k{font-size:10.5px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);font-weight:650}
.mini .v{font-family:ui-monospace,monospace;font-size:21px;font-weight:700;letter-spacing:-.02em;margin-top:3px}
.mini .s{font-size:11.5px;color:var(--ink2)}
.statnote{font-size:11.8px;color:var(--muted);line-height:1.5;margin:0}
.statnote b{color:var(--ink2);font-weight:600}

.gloss{list-style:none;margin:0;padding:0}
.gloss li{padding:11px 0;border-top:1px solid var(--line2);font-size:13.2px;color:var(--ink2);line-height:1.55}
.gloss li:first-child{border-top:none;padding-top:0}
.gloss b{color:var(--ink);font-weight:650}

.controls{display:flex;flex-wrap:wrap;gap:9px;align-items:center;margin-bottom:12px}
button,input,select{font:inherit}
input[type=search],select{font-size:13px;padding:8px 11px;border:1px solid var(--line);
  border-radius:8px;background:var(--surface);color:var(--ink)}
input[type=search]{min-width:230px;flex:1 1 230px}
.chips{display:flex;border:1px solid var(--line);border-radius:8px;overflow:hidden;background:var(--surface)}
.chip{font:inherit;font-size:12.5px;padding:8px 13px;border:none;background:none;cursor:pointer;
  color:var(--ink2);border-right:1px solid var(--line)}
.chip:last-child{border-right:none}
.chip[aria-pressed="true"]{background:var(--ink);color:#fff;font-weight:600}
.count{font-size:12.5px;color:var(--muted);margin-left:auto}
label.tog{display:flex;align-items:center;gap:7px;font-size:12.5px;color:var(--ink2);cursor:pointer}

.tablewrap{background:var(--surface);border:1px solid var(--line);border-radius:12px;overflow:auto}
.tablewrap table{width:100%;border-collapse:collapse;table-layout:fixed}
.tablewrap thead th{position:sticky;top:0;z-index:3;background:var(--panel);text-align:left;
  font-size:11.5px;letter-spacing:.05em;text-transform:uppercase;color:var(--ink2);font-weight:700;
  padding:12px 13px;border-bottom:1px solid var(--line)}
thead th .h2l{display:block;font-size:11px;text-transform:none;letter-spacing:0;color:var(--muted);font-weight:500;margin-top:3px}
col.w-snag{width:16%} col.w-trade{width:6%} col.w-pic{width:10%} col.w-man{width:16%} col.w-ai-pic{width:10%} col.w-ai-desc{width:17%}
#tb td{padding:13px;border-bottom:1px solid var(--line2);vertical-align:top;font-size:13.2px}
#tb tr:last-child td{border-bottom:none}
#tb tr:hover{background:#fafbfa}
#tb tr td:first-child{border-left:4px solid transparent}
#tb tr{content-visibility:auto;contain-intrinsic-size:auto 170px}
#tb tr.r-manual td:first-child{border-left-color:var(--man)}
#tb tr.r-ai-only td{background:#fbfbfe}
#tb tr.r-ai-only td:first-child{border-left-color:var(--ai)}
.c-man,.c-ai-pic{border-left:1px solid var(--line2)}
.badge{display:inline-block;font-size:10.5px;font-weight:700;letter-spacing:.05em;
  text-transform:uppercase;padding:2px 7px;border-radius:5px;color:#fff;margin-bottom:6px}
.b-man{background:var(--man)} .b-ai{background:var(--ai)}
.lv{display:inline-block;font-size:10.5px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;
  padding:2px 7px;border-radius:5px;margin:0 0 6px 4px}
.lv-certain{background:#e5f5e9;color:#1c7c3a}.lv-likely{background:#fdf3dc;color:#93690a}.lv-none{background:#fbe4e4;color:#b3261e}
.c-snag .t{margin:0;font-weight:600;line-height:1.35}
.c-snag .meta{margin:4px 0 0;font-size:11.8px;color:var(--muted)}
.c-snag .sep{opacity:.5;padding:0 2px}
.c-trade{color:var(--ink2)}
.pic-list{display:grid;grid-template-columns:repeat(2,72px);gap:5px;align-content:flex-start}
.th{position:relative;display:inline-block;width:72px;height:72px;padding:0;margin:0;
  border:1px solid var(--line);border-radius:7px;overflow:hidden;background:var(--panel);cursor:zoom-in}
.th img{width:100%;height:100%;object-fit:cover;display:block}
.bx{position:absolute;box-sizing:border-box;border:1.5px solid #e61e1e;pointer-events:none}
.th .src{position:absolute;left:0;bottom:0;font-size:8.5px;font-weight:700;line-height:1;
  padding:2px 3px;color:#fff;border-radius:0 5px 0 0}
.src.m{background:rgba(20,23,26,.8)} .src.a{background:var(--ai)}
.sig{display:flex;align-items:center;gap:7px;margin-bottom:6px}
.det{font-size:14px;font-weight:800;line-height:1;width:19px;height:19px;border-radius:50%;
  display:flex;align-items:center;justify-content:center;color:#fff;flex:none}
.det.yes{background:var(--yes)}
.dot{width:12px;height:12px;border-radius:50%;flex:none}
.p-high{background:var(--high)} .p-med{background:var(--med)} .p-low{background:var(--low)}
.plab{font-size:11.5px;color:var(--ink2);font-weight:600}
.c-man .d{margin:0;line-height:1.45}
.c-ai-desc .d{font-size:12.8px;color:var(--ink2);margin:0 0 6px}
.d.meta{color:var(--muted)}
body.clamp .c-man .d,body.clamp .c-ai-desc .d{display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.c-ai-desc .one+.one{margin-top:9px;padding-top:9px;border-top:1px dashed var(--line2)}
.c-ai-desc .sev{font-size:11.5px;color:var(--muted);margin-left:2px}
.aid{display:inline-block;font-family:ui-monospace,Menlo,monospace;font-size:11px;font-weight:700;padding:1px 7px;
  border-radius:5px;background:#e8eef6;color:#244f7a;margin:0 6px 4px 0}
.aid.none{background:#f1f2f3;color:var(--muted);font-weight:600;font-family:inherit}
.del,.nm{display:inline-block;font-size:10.5px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;padding:2px 7px;
  border-radius:5px;margin:0 6px 4px 0}
.del{background:#fbe4e4;color:#b3261e}
.nm{background:#f0e9fb;color:#5c34a0}
.nm.mt{background:#dff2ef;color:#13665e}
.mrg{display:inline-block;font-size:10.5px;font-weight:700;padding:2px 7px;border-radius:5px;background:#fdf3dc;color:#93690a;margin-bottom:6px}
.empty{padding:44px;text-align:center;color:var(--muted);font-size:14px}

dialog#lb{border:none;padding:0;background:#111417;width:94vw;height:94vh;max-width:94vw;
  max-height:94vh;border-radius:10px;overflow:hidden;color:#fff}
dialog#lb::backdrop{background:rgba(8,10,12,.86)}
.lbbar{height:48px;display:flex;align-items:center;gap:8px;padding:7px 9px 7px 13px;
  background:#20252a;border-bottom:1px solid #353b41}
.lbbar .lbname{font-size:12px;color:#c7ccd0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-right:auto}
dialog#lb button{background:#fff;border:none;border-radius:7px;padding:6px 10px;font-size:12.5px;cursor:pointer;white-space:nowrap}
.lbview{width:100%;height:calc(94vh - 48px);overflow:auto;display:grid;place-items:center;padding:16px}
dialog#lb img{max-width:100%;max-height:calc(94vh - 80px);display:block;cursor:zoom-in}
dialog#lb img.actual{max-width:none;max-height:none;cursor:zoom-out}
.lbw{position:relative}.lbw.actual{width:max-content}.lbw .bx{border-width:3px}
:focus-visible{outline:2px solid var(--focus);outline-offset:2px}

.tablescroll{overflow-x:auto}
.cmp{width:100%;border-collapse:collapse;font-size:13px}
.cmp thead th{background:var(--panel);font-size:10.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);
  font-weight:700;padding:8px 10px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap}
.cmp thead th:first-child{text-align:left}
.cmp tbody td{padding:9px 10px;border-bottom:1px solid var(--line2);vertical-align:top}
.cmp tbody tr:last-child td{border-bottom:none}
.cmp td.num{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-weight:700;text-align:right;white-space:nowrap}
.cmp td.num .sub{font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
  display:block;font-size:11px;color:var(--muted);font-weight:400;margin-top:2px}
.cmp .rl a{color:var(--ink)}

@media (min-width:1361px){.tablewrap table{min-width:1320px}}
@media (max-width:1360px){
  .statgrid{grid-template-columns:1fr}
  .tablewrap table,.tablewrap thead,#tb,#tb tr,#tb td{display:block;width:100%}
  .tablewrap thead{display:none}
  #tb tr{border-bottom:1px solid var(--line);padding:6px 0}
  #tb td{border-bottom:none;padding:8px 13px}
  .c-man,.c-ai-pic{border-left:none}
  .c-man:not(:empty)::before,.c-ai-pic:not(:empty)::before,.c-ai-desc::before{display:block;font-size:10px;letter-spacing:.08em;
    color:var(--muted);font-weight:700;margin-bottom:5px}
  .c-man:not(:empty)::before{content:"MANUAL"}
  .c-ai-pic:not(:empty)::before{content:"AI PICTURES"}
  .c-ai-desc::before{content:"AI DESCRIPTION"}
}
@media (max-width:720px){.unitnav{justify-content:flex-start}}
@media print{.controls{display:none} #tb tr{content-visibility:visible;break-inside:avoid}}"""

# Filters (source chips, search, trade, room, priority, match level), compact rows, and the photo viewer.
JS = """
(function(){
  var tb=document.getElementById('tb'),rows=[].slice.call(tb.rows);
  var q=document.getElementById('q'),trade=document.getElementById('trade'),room=document.getElementById('room'),
      prio=document.getElementById('prio'),level=document.getElementById('level'),
      cnt=document.getElementById('count'),empty=document.getElementById('empty');
  rows.forEach(function(r){r._t=r.textContent.toLowerCase();});
  var src='all';
  function apply(){var s=q.value.trim().toLowerCase(),t=trade.value,rm=room.value,p=prio.value,lv=level.value,n=0;
    rows.forEach(function(r){var ok=(src==='all'||r.dataset.st===src)&&(!t||r.dataset.trade===t)&&(!rm||r.dataset.room===rm)
      &&(!p||r.dataset.prio===p)&&(!lv||r.dataset.level===lv)&&(!s||r._t.indexOf(s)>-1);
      r.hidden=!ok;if(ok)n++;});
    cnt.textContent=n+' of '+rows.length+' entries';empty.hidden=n>0;}
  [q,trade,room,prio,level].forEach(function(el){el.addEventListener('input',apply);el.addEventListener('change',apply);});
  [].forEach.call(document.querySelectorAll('.chip'),function(c){c.addEventListener('click',function(){src=c.dataset.f;
    [].forEach.call(document.querySelectorAll('.chip'),function(o){o.setAttribute('aria-pressed',o===c?'true':'false');});apply();});});
  apply();
  var cl=document.getElementById('clamp');function setClamp(){document.body.classList.toggle('clamp',cl.checked);}
  cl.addEventListener('change',setClamp);setClamp();
  var lb=document.getElementById('lb'),lbi=document.getElementById('lbi'),zoom=document.getElementById('lbzoom');
  var lbw=document.getElementById('lbw');
  function setActual(on){lbi.classList.toggle('actual',on);lbw.classList.toggle('actual',on);zoom.textContent=on?'Fit to screen':'View actual size';}
  tb.addEventListener('click',function(ev){var b=ev.target.closest('.th');if(!b)return;setActual(false);
    [].forEach.call(lbw.querySelectorAll('.bx'),function(x){x.remove();});
    JSON.parse(b.dataset.boxes||'[]').forEach(function(r){var x=document.createElement('span');x.className='bx';
      x.style.left=r[0]*100+'%';x.style.top=r[1]*100+'%';x.style.width=r[2]*100+'%';x.style.height=r[3]*100+'%';lbw.appendChild(x);});
    lbi.src=b.dataset.full;document.getElementById('lbname').textContent=b.dataset.name||'Snag photo';lb.showModal();});
  zoom.addEventListener('click',function(){setActual(!lbi.classList.contains('actual'));});
  lbi.addEventListener('click',function(){setActual(!lbi.classList.contains('actual'));});
  document.getElementById('lbx').addEventListener('click',function(){lb.close();});
  lb.addEventListener('close',function(){lbi.removeAttribute('src');setActual(false);});
  lb.addEventListener('click',function(ev){if(ev.target===lb)lb.close();});
})();
"""


def main():
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    units = [u["unit"] for u in data["units"]]
    missing = [p for u in data["units"] for r in u["manual"] + u["ai_only"]
               for p in r.get("photos", []) + [g["src"] for g in r.get("images", [])]
               + [g["src"] for a in ((r.get("ai") or {}).get("snags") or []) for g in a["images"]]
               + [d["image"] for d in ((r.get("ai") or {}).get("detections") or []) if d["image"]]
               if not (ROOT / p).is_file()]
    assert not missing, f"{len(missing)} photos missing, e.g. {missing[0]}"
    out = ROOT / build_time_motion.page_file(SLUG)
    out.write_text(render_index(data), encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size:,} bytes)")
    for u in data["units"]:
        f = ROOT / unit_file(u["unit"])
        f.write_text(render_unit(u, units, data["qaqc_export"]), encoding="utf-8")
        print(f"wrote {f} ({f.stat().st_size:,} bytes): {len(u['manual'])} manual snags, {len(u['ai_only'])} AI only")


if __name__ == "__main__":
    main()
