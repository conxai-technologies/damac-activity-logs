# DAMAC snagging pilot

Four pages, one masthead, tabbed together. Each is a real file with its own
URL, so any of them can be linked to on its own.

**https://conxai-technologies.github.io/damac-activity-logs/**

| Tab | Page | Built from |
| --- | --- | --- |
| Pilot time and motion Lagoons – Ibiza (default) | `index.html` | `data/qaqc-time-motion.xlsx` via `build_time_motion.py` |
| Pilot time and motion Hills – Gems | `time-motion-gems.html` | the same workbook, same script |
| Review Stats | `review-stats.html` | `data/review-stats.json` via `build_review.py` |
| Archived activities | `activity-logs.html` | `data/activity-logs.csv` via `build.py` |

Deep links: `…/#Ibiza-T241` on Lagoons – Ibiza, `…/activity-logs.html#BL515` on
archived activities, `…/review-stats.html` for the review stats. The archived
activity log used to be the site root, so `index.html` forwards any hash it
does not know (`…/#BL515`) to `activity-logs.html`.

## Pilot time and motion

Minutes logged on site per activity, for each unit in the *QAQC Time + motion*
workbook, one page per project: **Lagoons – Ibiza** (T240–T245) and
**Hills – Gems** (E511B). Each unit is its own tab in the workbook, and lands on
the page whose project its tab name starts with (`SITES` in
`build_time_motion.py`). `Gems-E511B_old` is an earlier take of Gems-E511B and
is skipped.

Each fill colour in the workbook is a different person, and the page keeps one
colour per person: MEP inspector (MEP general), MEP specialist (above ceiling),
QA inspector (QA functional), and capture (iGUIDE or Matterport).

- **Recorded time by unit** — each unit's minutes, split by person (on a page
  with more than one unit).
- **One card per unit** — every activity with its logged clock times, its
  minutes, and a timeline of the day. MEP general and QA functional open as a
  dropdown onto their sub-tasks (roof, yard; inside cupboard, tile tapping,
  roof) plus **Other functional**: the activity's minutes less its timed
  sub-tasks.
- **Tests** on every unit: the flood test was already conducted by the
  contractor, with its results incorporated during QA and MEP snagging; the
  static / spray test is pending, for a later stage of snagging.

A blank row is shown as **Activity pending**; 0 minutes or "not recorded
seperately" as **Not recorded separately**. The workbook's minutes are used
as-is, and where they disagree with the row's own clock times by more than
2 minutes (`ROUNDING`) the page flags it; smaller differences are rounding.

## Archived activities

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

Every page is generated. `build.py` builds archived activities and then calls
`build_review.py` and `build_time_motion.py`, so one command refreshes the
site. Time and motion reads the workbook directly (cell fills included), which
needs `openpyxl`:

```sh
pip install openpyxl
cp "…/Damac snagging schedules - Activity logs.csv" data/activity-logs.csv
cp "…/QAQC_TIme+motion.xlsx" data/qaqc-time-motion.xlsx
python3 build.py
git commit -am "Refresh" && git push
```

`theme.py` holds the design tokens, the masthead and the tab bar — the chrome
every page wears. Add a page by appending it to `theme.PAGES` and giving it a
build script.

Nothing is inferred on any page. `build.py` normalises the sheet's mixed
date formats and duration strings; `build_review.py` recomputes every total and
percentage the deck prints from the villa rows beside it; `build_time_motion.py`
checks each row's minutes against its clock times and the workbook's own totals
block. Every way a mismatch is flagged on the page rather than corrected, `N/A`
renders as `—`, and `tbc` stays `tbc`.

A new fill colour in the workbook stops `build_time_motion.py` with the cell to
look at; map it to a person in `PEOPLE` at the top of the script.
