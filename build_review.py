#!/usr/bin/env python3
"""Render data/review-stats.json into review-stats.html.

The figures and wording come from the DAMAC QA/QC Revision Report: for each of
five villas, how many AI-generated snags the review deleted, how many it
changed, and how many it accepted exactly as issued. The worked examples and
their photos come from the deck the report summarises.

As on the activity log, nothing is corrected. Every total, percentage and
outcome split the report prints is recomputed here from the villa rows beside
it, and a figure that does not agree is flagged on the page rather than
quietly fixed.
"""

import json
from pathlib import Path

import theme
from theme import GENERATED, esc

ROOT = Path(__file__).parent
DATA_PATH = ROOT / "data" / "review-stats.json"
OUT_PATH = ROOT / "review-stats.html"


# ------------------------------------------------------------- arithmetic ---

def num(n):
    return f"{n:,}"


def pct(x):
    return f"{x:.1f}%"


def untouched(v):
    """Accepted exactly as issued: what is left once deleted and changed come off."""
    return v["snags"] - v["deleted"] - v["changed"]


def check(data):
    """Recompute what the report asserts. Returns {key: tooltip} for mismatches."""
    villas, total = data["villas"], data["total"]
    keys = [f["key"] for f in data["fields"]]
    flags = {}

    def cmp(key, stated, computed, what, fmt=num):
        if abs(stated - computed) > 0.05:
            flags[key] = f"Report says {fmt(stated)}; {what} comes to {fmt(computed)}."

    # the totals row against the five villas
    for col in ("snags", "deleted", "changed"):
        cmp(f"total-{col}", total[col], sum(v[col] for v in villas),
            "the five villas add up to")
    for k in keys:
        cmp(f"total-{k}", total["field_changes"][k][0],
            sum(v["field_changes"][k][0] for v in villas), "the five villas add up to")

    stated_untouched = next(o["total"] for o in data["outcomes"] if o["key"] == "untouched")
    cmp("total-untouched", stated_untouched, sum(untouched(v) for v in villas),
        "the five villas add up to")

    for v in villas + [total]:
        u = v["unit"]
        # every percentage is a share of that villa's material snags
        cmp(f"{u}-pctdel", v["pct_deleted"], 100 * v["deleted"] / v["snags"],
            f'{num(v["deleted"])} of {num(v["snags"])}', pct)
        cmp(f"{u}-pctchg", v["pct_changed"], 100 * v["changed"] / v["snags"],
            f'{num(v["changed"])} of {num(v["snags"])}', pct)
        for k in keys:
            n, p = v["field_changes"][k]
            if p is not None:
                cmp(f"{u}-{k}", p, 100 * n / v["snags"],
                    f'{num(n)} of {num(v["snags"])}', pct)
        # the three outcomes have to account for every material snag
        if untouched(v) < 0:
            flags[f"{u}-outcome"] = (
                f'{num(v["deleted"])} deleted and {num(v["changed"])} changed exceed '
                f'{u}\'s {num(v["snags"])} material snags.')
        # a field edit belongs to a changed snag, so the fields cannot fall short
        edits = sum(v["field_changes"][k][0] for k in keys)
        if edits < v["changed"]:
            flags[f"{u}-fields"] = (
                f'{num(v["changed"])} snags changed, but the five fields account for '
                f"only {num(edits)} edits between them.")
    return flags


def flag(flags, key):
    tip = flags.get(key)
    return f'<span class="warn" tabindex="0" data-tip="{esc(tip)}">!</span>' if tip else ""


# --------------------------------------------------------------- rendering ---

def render_scope(data, flags):
    """The report's scope: what is counted, and over what."""
    rows = "".join(f"""
      <tr><th class="mono">{esc(v["unit"])}</th>
        <td class="num">{num(v["snags"])}</td></tr>""" for v in data["villas"])
    t = data["total"]

    return f"""
<article class="card">
  <div class="card-head">
    <h2>Scope</h2>
    <p class="card-sub">{esc(data["scope"])}</p>
  </div>
  <div class="scope-cols">
    <div class="tblwrap narrow">
      <table class="dt">
        <thead><tr><th>Villa</th><th class="num">Material snags</th></tr></thead>
        <tbody>{rows}</tbody>
        <tfoot><tr><th class="mono">Total</th>
          <td class="num">{num(t["snags"])}{flag(flags, "total-snags")}</td></tr></tfoot>
      </table>
    </div>
    <div class="prose">
      <p class="lede">{esc(data["scope_note"])}</p>
      <h3>{esc(data["terms"]["heading"])}</h3>
      <p>{esc(data["terms"]["body"])}</p>
      <h3>{esc(data["denominator"]["heading"])}</h3>
      <p>{data["denominator"]["body"]}</p>
      <p class="eq mono">{" + ".join(
          f'{num(o["total"])} {esc(o["key"])}' for o in data["outcomes"])}
        = {num(t["snags"])}</p>
    </div>
  </div>
</article>"""


def render_outcomes(data, flags):
    """Every material snag lands in exactly one of three outcomes.

    Bar length is the villa's snag count, so villas stay comparable; the split
    is what the review did with them.
    """
    villas = data["villas"]
    peak = max(v["snags"] for v in villas)
    labels = {o["key"]: o["label"] for o in data["outcomes"]}

    rows = []
    for v in villas:
        parts = [("deleted", v["deleted"]), ("changed", v["changed"]),
                 ("untouched", untouched(v))]
        segs = "".join(
            f'<i class="seg {k}" style="flex:{n}" title="{esc(v["unit"])}: {num(n)} '
            f'{esc(labels[k].lower())} ({100 * n / v["snags"]:.1f}%)"></i>'
            for k, n in parts if n > 0)
        rows.append(f"""
    <div class="srow">
      <a class="sunit mono" href="index.html#{esc(v["unit"])}"
         title="Open {esc(v["unit"])} in the activity log">{esc(v["unit"])}</a>
      <div class="strack">
        <div class="sbar" style="width:{100 * v["snags"] / peak:.3f}%">{segs}</div>
        <span class="slab mono">{num(v["snags"])}</span>
      </div>
      <div class="sout">
        <span class="o deleted mono">{num(v["deleted"])}</span>
        <span class="o changed mono">{num(v["changed"])}</span>
        <span class="o untouched mono">{num(untouched(v))}{flag(flags, v["unit"] + "-outcome")}</span>
      </div>
    </div>""")

    legend = "".join(f'<span><i class="sw {o["key"]}"></i>{esc(o["label"])} '
                     f'<b class="mono">{num(o["total"])}</b></span>'
                     for o in data["outcomes"])

    return f"""
<article class="card">
  <div class="card-head">
    <h2>What the review did with each villa's snags</h2>
    <p class="card-sub">Bar length is the villa's material snag count, split into the three
    outcomes. Villa names link through to the activity log.</p>
  </div>
  <div class="legend">{legend}</div>
  <div class="chart">{"".join(rows)}</div>
</article>"""


def render_deletions(data, flags):
    rows = "".join(f"""
      <tr><th class="mono">{esc(v["unit"])}</th>
        <td class="num">{num(v["snags"])}</td>
        <td class="num">{num(v["deleted"])}</td>
        <td class="num">{pct(v["pct_deleted"])}{flag(flags, v["unit"] + "-pctdel")}</td></tr>"""
        for v in data["villas"])
    t = data["total"]

    return f"""
<article class="card">
  <div class="card-head">
    <h2>Deletions</h2>
    <p class="card-sub">{esc(data["deletions_note"])}</p>
  </div>
  <div class="tblwrap">
    <table class="dt">
      <thead><tr><th>Villa</th><th class="num">Material</th><th class="num">Deleted</th>
        <th class="num">% deleted</th></tr></thead>
      <tbody>{rows}</tbody>
      <tfoot><tr><th class="mono">Total</th>
        <td class="num">{num(t["snags"])}</td>
        <td class="num">{num(t["deleted"])}{flag(flags, "total-deleted")}</td>
        <td class="num">{pct(t["pct_deleted"])}{flag(flags, "total-pctdel")}</td></tr></tfoot>
    </table>
  </div>
  <p class="after">{esc(data["deletions_range"])}</p>
</article>"""


def render_changes(data, flags):
    fields = data["fields"]

    def cell(v, f):
        n, p = v["field_changes"][f["key"]]
        sub = f'<span class="sub">{p:.1f}%</span>' if p is not None else ""
        return f'<td class="num">{num(n)}{sub}{flag(flags, v["unit"] + "-" + f["key"])}</td>'

    def row(v, foot=False):
        u = v["unit"]
        return f"""
      <tr><th class="mono">{esc(u)}</th>
        <td class="num">{num(v["snags"])}</td>
        {"".join(cell(v, f) for f in fields)}
        <td class="num">{num(v["changed"])}{flag(flags, "total-changed" if foot else u + "-fields")}</td>
        <td class="meter">
          <span class="mtrack"><i style="width:{v["pct_changed"]:.2f}%"
            title="{esc(u)}: {num(v["changed"])} of {num(v["snags"])} snags changed"></i></span>
          <span class="mval mono">{pct(v["pct_changed"])}{flag(flags, u + "-pctchg")}</span>
        </td></tr>"""

    defs = "".join(f"""
      <tr><th>{esc(f["label"])}</th><td class="wrap">{esc(f["records"])}</td></tr>"""
        for f in fields)
    heads = "".join(f'<th class="num">{esc(f["label"])}</th>' for f in fields)

    return f"""
<article class="card">
  <div class="card-head">
    <h2>Changes by field</h2>
    <p class="card-sub">{esc(data["fields_intro"])}</p>
  </div>
  <div class="tblwrap narrow">
    <table class="dt">
      <thead><tr><th>Field</th><th>What it records</th></tr></thead>
      <tbody>{defs}</tbody>
    </table>
  </div>
  <p class="between">{esc(data["fields_note"])}</p>
  <div class="tblwrap">
    <table class="dt">
      <thead><tr><th>Villa</th><th class="num">Material</th>{heads}
        <th class="num">Changed</th><th class="num wide">% snags changed</th></tr></thead>
      <tbody>{"".join(row(v) for v in data["villas"])}</tbody>
      <tfoot>{row(data["total"], foot=True)}</tfoot>
    </table>
  </div>
  <p class="after">{esc(data["fields_caveat"])}</p>
</article>"""


def render_examples(data):
    """The deck's worked examples: AI output beside the reviewer's edit."""
    order = ["location", "trade", "type", "description"]
    labels = {"location": "Location", "trade": "Trade", "type": "Type",
              "description": "Description"}
    cards = []
    for ex in data["examples"]:
        diff = [k for k in order if ex["ai"][k] != ex["manual"][k]]

        def side(which, cls, title):
            src = ex[which]
            rows = "".join(
                f'<div class="ex-f{" is-diff" if k in diff else ""}">'
                f'<dt>{labels[k]}</dt><dd>{esc(src[k])}</dd></div>' for k in order)
            return (f'<div class="ex-side {cls}"><h4>{title}</h4>'
                    f'<dl class="ex-dl">{rows}</dl></div>')

        changed = ", ".join(labels[k].lower() for k in diff) or "nothing"
        cards.append(f"""
<article class="card ex">
  <div class="ex-head">
    <h3 class="mono">{esc(ex["unit"])} &middot; #{esc(ex["snag"])}</h3>
    <span class="ex-tag">{esc(changed)} edited</span>
  </div>
  <div class="ex-body">
    <a class="ex-photo" href="{esc(ex["image"])}" target="_blank" rel="noopener"
       title="Open the full photo">
      <img src="{esc(ex["image"])}" loading="lazy" decoding="async"
           alt="Snag {esc(ex["snag"])} in {esc(ex["unit"])}, boxed on the capture photo">
    </a>
    <div class="ex-cols">{side("ai", "is-ai", "AI output")}{side("manual", "is-man", "Manual edit")}</div>
  </div>
</article>""")

    return f"""
<div class="card-head sec-head">
  <h2>Example comment changes</h2>
  <p class="card-sub">Four snags walked through in the deck this report summarises, each on the
  photo it was raised against. The edited field is marked on both sides.</p>
</div>
<div class="exgrid">{"".join(cards)}</div>"""


def render(data, flags):
    villas, t = data["villas"], data["total"]
    outcomes = {o["key"]: o for o in data["outcomes"]}
    share = {k: 100 * o["total"] / t["snags"] for k, o in outcomes.items()}

    strip = "".join(f'<div><span class="k">{k}</span><span class="v mono">{v}</span>'
                    f'<span class="s">{s}</span></div>' for k, v, s in [
        ("Villas reviewed", str(len(villas)), "in this report"),
        ("Material snags", num(t["snags"]), "every figure counts over these"),
        ("Deleted", num(outcomes["deleted"]["total"]),
         f'{pct(share["deleted"])}, removed from the board'),
        ("Changed", num(outcomes["changed"]["total"]),
         f'{pct(share["changed"])}, kept but edited'),
        ("Accepted as issued", num(outcomes["untouched"]["total"]),
         f'{pct(share["untouched"])}, untouched'),
    ])

    masthead = theme.masthead(
        "review", "Review Stats",
        esc(data["lead"]),
        f"Source <b>{esc(data['source']['doc'])}</b><br>"
        f"Villas <b>{len(villas)}</b> &middot; Report dated "
        f"<b>{esc(data['source']['dated'])}</b><br>"
        f"Generated <b>{GENERATED:%d %b %Y}</b>")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>DAMAC snagging pilot &mdash; review stats</title>
<meta name="description" content="What DAMAC's review deleted, changed and accepted across five villas.">
<style>
{theme.CHROME_CSS}

/* ---------------------------------------------- the review stats page --- */
.sec-head{{margin:30px 0 14px}}
.after{{margin:12px 0 0;font-size:12.6px;color:var(--ink2)}}
.between{{margin:16px 0 12px;font-size:12.6px;color:var(--ink2);max-width:82ch}}

.scope-cols{{display:grid;grid-template-columns:minmax(220px,300px) 1fr;gap:24px;align-items:start}}
.prose{{font-size:12.9px;color:var(--ink2);line-height:1.65;max-width:72ch}}
.prose p{{margin:0 0 11px}}
.prose h3{{font-size:11px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);
  font-weight:700;margin:16px 0 5px}}
.prose .lede{{color:var(--ink);font-weight:600}}
.prose b{{color:var(--ink);font-weight:650}}
.eq{{display:inline-block;font-size:12.2px;color:var(--ink);background:var(--panel);
  border:1px solid var(--line2);border-radius:7px;padding:7px 11px;margin-top:2px}}

.legend{{display:flex;flex-wrap:wrap;gap:18px;font-size:12px;color:var(--ink2);margin-bottom:14px}}
.legend span{{display:flex;align-items:center;gap:6px}}
.legend b{{color:var(--ink);font-weight:700}}
.sw{{display:block;width:11px;height:11px;border-radius:2px}}
.sw.deleted,.seg.deleted{{background:var(--c-del)}}
.sw.changed,.seg.changed{{background:var(--c-chg)}}
.sw.untouched,.seg.untouched{{background:var(--c-count)}}

.chart{{margin-bottom:2px}}
.srow{{display:flex;align-items:center;gap:12px;padding:5px 0}}
.sunit{{flex:0 0 64px;font-size:12.5px;font-weight:700;color:var(--ink);text-decoration:none}}
.sunit:hover{{text-decoration:underline}}
.strack{{flex:1;display:flex;align-items:center;gap:9px;min-width:0}}
.sbar{{display:flex;gap:2px;height:18px;min-width:2px}}
.seg{{display:block;min-width:3px}}
.seg:first-child{{border-radius:4px 0 0 4px}}
.seg:last-child{{border-radius:0 4px 4px 0}}
.slab{{font-size:12px;color:var(--ink2);font-weight:600;flex:none}}
.sout{{flex:0 0 172px;display:flex;justify-content:flex-end;gap:12px;font-size:12.5px;
  font-weight:700}}
.sout .o{{min-width:44px;text-align:right}}
.o.deleted{{color:var(--c-del)}} .o.changed{{color:var(--c-chg)}} .o.untouched{{color:var(--c-count)}}

.tblwrap{{overflow-x:auto;border:1px solid var(--line);border-radius:10px}}
.tblwrap.narrow{{max-width:560px}}
table.dt{{width:100%;border-collapse:collapse;font-size:12.6px}}
.dt th,.dt td{{padding:9px 11px;text-align:left;border-bottom:1px solid var(--line2);
  white-space:nowrap;vertical-align:top}}
.dt td.wrap{{white-space:normal}}
.dt thead th{{background:var(--panel);font-size:11px;letter-spacing:.05em;text-transform:uppercase;
  color:var(--ink2);font-weight:700;border-bottom:1px solid var(--line)}}
.dt th.num,.dt td.num,.dt td.meter{{text-align:right}}
.dt td.num{{font-family:ui-monospace,SFMono-Regular,Menlo,monospace}}
.dt tbody th{{font-weight:600;color:var(--ink)}}
.dt tbody tr:hover td{{background:#fafbfa}}
.dt tfoot th,.dt tfoot td{{background:var(--panel);font-weight:700;border-bottom:none;
  border-top:1px solid var(--line)}}
.dt .sub{{display:block;font-size:10.8px;font-weight:500;color:var(--muted);
  font-family:ui-sans-serif,system-ui,sans-serif}}
.dt th.wide{{min-width:132px}}

.meter{{min-width:132px}}
.mtrack{{display:block;height:8px;border-radius:4px;background:var(--surface);
  border:1px solid var(--line2);overflow:hidden;margin-bottom:4px}}
.dt tfoot .mtrack{{background:var(--surface)}}
.mtrack i{{display:block;height:100%;background:var(--c-chg);border-radius:4px;min-width:2px}}
.mval{{font-size:12.6px;font-weight:700}}

.exgrid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(430px,1fr));gap:20px}}
.card.ex{{margin-bottom:0;padding:16px}}
.ex-head{{display:flex;align-items:baseline;justify-content:space-between;gap:10px;
  padding-bottom:10px;border-bottom:1px solid var(--line);margin-bottom:13px}}
.ex-head h3{{font-size:16px;margin:0;font-weight:700;letter-spacing:-.01em}}
.ex-tag{{font-size:10.5px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;
  color:var(--c-chg);background:#fdf5e6;border:1px solid #f0e0bd;border-radius:5px;
  padding:2px 7px;flex:none}}
.ex-photo{{display:block;border-radius:8px;overflow:hidden;border:1px solid var(--line2);
  margin-bottom:13px;background:var(--panel)}}
.ex-photo img{{display:block;width:100%;height:330px;object-fit:contain}}
.ex-cols{{display:grid;grid-template-columns:1fr 1fr;gap:10px}}
.ex-side{{border:1px solid var(--line2);border-radius:9px;padding:0 11px 10px;
  border-top:3px solid var(--line);background:var(--panel)}}
.ex-side.is-ai{{border-top-color:var(--c-count)}}
.ex-side.is-man{{border-top-color:var(--c-chg);background:var(--surface)}}
.ex-side h4{{font-size:11px;margin:0;padding:10px 0 8px;font-weight:700;letter-spacing:.06em;
  text-transform:uppercase;color:var(--ink2);border-bottom:1px solid var(--line2)}}
.ex-dl{{margin:0}}
.ex-f{{padding:7px 0;border-top:1px solid #f2f3f2}}
.ex-f:first-child{{border-top:none}}
.ex-f dt{{font-size:10.5px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);
  font-weight:650}}
.ex-f dd{{margin:2px 0 0;font-size:12.4px;color:var(--ink2);line-height:1.45;white-space:normal}}
.ex-f.is-diff{{margin:0 -11px;padding:7px 8px 7px 11px;border-left:3px solid var(--c-chg);
  background:#fdf7ec}}
.ex-f.is-diff dd{{color:var(--ink);font-weight:600}}

@media (max-width:900px){{
  .scope-cols{{grid-template-columns:1fr}}
  .tblwrap.narrow{{max-width:none}}
}}
@media (max-width:720px){{
  .srow{{flex-wrap:wrap;gap:8px}}
  .sunit{{flex:0 0 auto}}
  .sout{{flex:0 0 auto;justify-content:flex-start}}
  .exgrid{{grid-template-columns:1fr}}
  .ex-cols{{grid-template-columns:1fr}}
}}
</style>
</head>
<body>
<div class="wrap">

{masthead}

<div class="strip">{strip}</div>

{render_scope(data, flags)}

{render_outcomes(data, flags)}

{render_deletions(data, flags)}

{render_changes(data, flags)}

{render_examples(data)}

</div>
</body>
</html>
"""


def main():
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    flags = check(data)
    OUT_PATH.write_text(render(data, flags), encoding="utf-8")
    print(f"wrote {OUT_PATH} ({OUT_PATH.stat().st_size:,} bytes) "
          f"for {len(data['villas'])} villas"
          + (f"; flagged {len(flags)}: {', '.join(sorted(flags))}" if flags else "; no mismatches"))


if __name__ == "__main__":
    main()
