"""Chrome shared by every page of the site: tokens, masthead, tabs, footer.

Both build.py (Activity logs) and build_review.py (Review Stats) render their
own body from their own data, but the frame around it lives here so the two
pages cannot drift apart.
"""

import html
from datetime import date

GENERATED = date.today()

# The pages of the site, in tab order: (slug, label, file).
PAGES = [
    ("activity", "Activity logs", "index.html"),
    ("review", "Review Stats", "review-stats.html"),
]


def esc(s):
    return html.escape(str(s), quote=True)


def nav(active):
    """The tab bar. Every page is a real file, so each tab is a plain link."""
    tabs = "".join(
        f'<a class="tab" href="{f}"'
        + (' aria-current="page"' if slug == active else "")
        + f">{esc(label)}</a>"
        for slug, label, f in PAGES)
    return f'<nav class="tabs" aria-label="Sections">{tabs}</nav>'


def masthead(active, title, subline, provenance):
    return f"""<header class="top">
  <div class="brand-row">
    <div class="brand-logos" aria-label="Project and technology logos">
      <img src="assets/damac.png" alt="DAMAC">
    </div>
    <img class="conxai-logo" src="assets/conxai.png" alt="Conxai">
  </div>
  <div class="top-inner">
    <div>
      <p class="eyebrow">DAMAC &times; CONXAI snagging pilot</p>
      <h1>{title}</h1>
      <p class="subline">{subline}</p>
    </div>
    <div class="provenance">{provenance}</div>
  </div>
  {nav(active)}
</header>"""


# Design tokens and the chrome every page wears. Page-specific rules stay in
# the page's own build script.
CHROME_CSS = """
:root{
  --page:#eef0ee; --surface:#ffffff; --panel:#f7f8f7;
  --ink:#14171a; --ink2:#4d545c; --muted:#858d95;
  --line:#dcdfdc; --line2:#eaece9;
  --c-qa:#8a5cc4; --c-mep:#2f6ea8; --c-cap:#2f6f4f; --c-proc:#c98a1e;
  --warn:#a2373f;
  /* chart hues, validated as a categorical set against the light surface */
  --c-count:#2f6ea8; --c-del:#a2373f; --c-chg:#a8720f;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%;scroll-behavior:smooth}
body{margin:0;background:var(--page);color:var(--ink);
  font:15px/1.55 ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.mono{font-family:ui-monospace,SFMono-Regular,Menlo,"Roboto Mono",monospace}
.wrap{max-width:1240px;margin:0 auto;padding:34px 22px 90px}

.top{padding-bottom:0;border-bottom:2px solid var(--ink);margin-bottom:22px}
.brand-row{display:flex;align-items:center;justify-content:space-between;gap:16px;margin-bottom:18px}
.brand-logos{display:flex;justify-content:flex-end;align-items:center;gap:18px}
.brand-logos img{display:block;width:auto;max-width:260px;height:auto;max-height:40px;object-fit:contain}
.brand-logos img[alt="DAMAC"]{max-height:16px}
.conxai-logo{display:block;width:auto;max-width:190px;height:auto;max-height:52px;object-fit:contain}
.top-inner{display:flex;flex-wrap:wrap;gap:20px;align-items:flex-start;justify-content:space-between}
.eyebrow{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);
  font-weight:700;margin:0 0 7px}
h1{font-size:34px;line-height:1.05;margin:0;letter-spacing:-.02em;font-weight:680}
.subline{color:var(--ink2);font-size:13.5px;margin:9px 0 0;max-width:60ch}
.provenance{text-align:right;font-size:12px;color:var(--muted);line-height:1.75;flex:none}
.provenance b{color:var(--ink2);font-weight:600}

.tabs{display:flex;gap:2px;margin:18px 0 -2px}
.tab{display:block;padding:9px 16px 10px;font-size:13.5px;font-weight:600;color:var(--ink2);
  text-decoration:none;border:1px solid transparent;border-bottom:none;border-radius:8px 8px 0 0;
  position:relative;top:2px}
.tab:hover{color:var(--ink);background:rgba(255,255,255,.6)}
.tab[aria-current="page"]{background:var(--surface);color:var(--ink);border-color:var(--ink);
  border-bottom:2px solid var(--surface)}
.tab:focus-visible{outline:2px solid #1b6fc4;outline-offset:-2px}

.strip{display:grid;grid-template-columns:repeat(auto-fit,minmax(168px,1fr));gap:1px;
  background:var(--line);border:1px solid var(--line);border-radius:12px;overflow:hidden;
  margin-bottom:26px}
.strip>div{background:var(--surface);padding:14px 16px}
.strip .k{display:block;font-size:10.5px;text-transform:uppercase;letter-spacing:.07em;
  color:var(--muted);font-weight:650;line-height:1.35}
.strip .v{display:block;font-size:21px;font-weight:700;letter-spacing:-.02em;margin-top:4px}
.strip .v .sm{font-size:14.5px;letter-spacing:-.01em;white-space:nowrap}
.strip .s{display:block;font-size:11.6px;color:var(--ink2);margin-top:3px}

.card{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:20px;
  margin-bottom:20px}
.card-head{margin-bottom:14px}
h2{font-size:17px;margin:0;letter-spacing:-.01em;font-weight:670}
.card-sub{color:var(--ink2);font-size:12.8px;margin:5px 0 0}

.warn{display:inline-flex;align-items:center;justify-content:center;width:14px;height:14px;
  margin-left:5px;border-radius:50%;background:var(--warn);color:#fff;font-size:9.5px;
  font-weight:800;vertical-align:middle;cursor:help;position:relative}
.warn:not([data-tip]){cursor:default}
.warn[data-tip]:hover::after,.warn[data-tip]:focus::after{content:attr(data-tip);position:absolute;bottom:calc(100% + 7px);
  left:50%;transform:translateX(-50%);width:max-content;max-width:250px;text-align:left;
  background:var(--ink);color:#fff;font-size:11.5px;font-weight:400;line-height:1.45;
  padding:8px 10px;border-radius:7px;z-index:20;pointer-events:none}

.notes{margin-top:26px;font-size:12.4px;color:var(--ink2);line-height:1.75}
.notes h2{font-size:13px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);
  margin:0 0 8px;font-weight:700}
.notes ul{margin:0;padding-left:18px}
.notes li{margin-bottom:6px}
.foot{margin-top:22px;padding-top:14px;border-top:1px solid var(--line);
  font-size:11.8px;color:var(--muted);line-height:1.7}
.foot a{color:var(--ink2)}

@media (max-width:720px){
  .wrap{padding:24px 15px 70px}
  h1{font-size:27px}
  .provenance{text-align:left}
  .brand-logos img[alt="DAMAC"]{max-height:14px}
  .conxai-logo{max-width:140px}
  .tabs{margin-top:14px}
  .tab{padding:8px 12px 9px;font-size:12.5px}
}
@media print{
  body{background:#fff} .tabs{display:none} .card{break-inside:avoid}
}"""
