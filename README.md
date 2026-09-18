# DAMAC snagging pilot

Two pages, one masthead, tabbed together. Each is a real file with its own
URL, so either can be linked to on its own.

**https://conxai-technologies.github.io/damac-activity-logs/**

| Tab | Page | Built from |
| --- | --- | --- |
| Activity logs | `index.html` | `data/activity-logs.csv` via `build.py` |
| Review Stats | `review-stats.html` | `data/review-stats.json` via `build_review.py` |

Deep links: `…/#BL515` on the activity log, `…/review-stats.html` for the
review stats.

## Activity logs

Time and effort logged for each unit, organised one card per unit.

- **Programme at a glance** — which days each unit was worked on.
- **One card per unit** (Q845, Q844, Q545, BL109, BL515, C625F, K148) with the
  four phases: manual QA snagging, manual MEP snagging, capture, processing.
- **Full log, side by side** — the source sheet, normalised, for cross-unit comparison.

Filter to a single unit with the chips at the top; the selection deep-links.

Each unit carries its floor area, taken from the unit's own header cell in the
sheet's first row (`BL515 (200.3 sq. m)`), beside the unit name and under the
column head in the full log.

## Review Stats

What DAMAC's review did to the AI-generated snag list, over five villas
(Q844, Q545, Q845, BL515, BL109 — C625F and K148 are not in this report).
Every material snag has exactly one outcome: deleted, changed, or accepted
exactly as issued.

- **Scope** — material snags per villa, and the one denominator every
  percentage on the page uses.
- **What the review did with each villa's snags** — the three outcomes as a
  split bar, villa by villa.
- **Deletions** — snags removed from the board, as a share of material snags.
- **Changes by field** — what each field records, then priority, description,
  trade, location and photo edits on the snags that were kept.
- **Example comment changes** — four worked examples, each with the capture
  photo the snag was boxed on, AI output beside the reviewer's edit.

Tables and wording come from the **DAMAC QA/QC Revision Report** of
18 Sep 2026. Its analysis sections ("What the numbers show" onward) are
deliberately not carried here.

The example photos are exported from *Damac Snagging Updates 18-09-2026.pptx*
([Drive](https://drive.google.com/file/d/1QWzWHVtEkQrwiJl2kG6Zl1-rIxIXqffR/view))
into `assets/review/`. That deck's own tables disagree with the report on three
fields — Description, Location and Photo — and the report's figures are the
ones the page shows.

## Rebuilding

Both pages are generated. `build.py` builds the activity log and then calls
`build_review.py`, so one command refreshes the site:

```sh
cp "…/Damac snagging schedules - Activity logs.csv" data/activity-logs.csv
python3 build.py
git commit -am "Refresh" && git push
```

`theme.py` holds the design tokens, the masthead and the tab bar — the chrome
both pages wear. Add a page by appending it to `theme.PAGES` and giving it a
build script.

Nothing is inferred on either page. `build.py` normalises the sheet's mixed
date formats and duration strings; `build_review.py` recomputes every total and
percentage the deck prints from the villa rows beside it. Either way a mismatch
is flagged on the page rather than corrected, `N/A` renders as `—`, and `tbc`
stays `tbc`.
