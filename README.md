# DAMAC snagging pilot

Five pages, one masthead, tabbed together. Each is a real file with its own
URL, so any of them can be linked to on its own.

**https://conxai-technologies.github.io/damac-activity-logs/**

| Tab | Page | Built from |
| --- | --- | --- |
| Review Stats (default) | `index.html` | `data/review-timelines.json` via `build_review_timelines.py` |
| Pilot time and motion Lagoons – Ibiza | `time-motion-ibiza.html` | `data/qaqc-time-motion.xlsx` via `build_time_motion.py` |
| Pilot time and motion Hills – Gems | `time-motion-gems.html` | the same workbook, same script |
| Archived Review Stats | `review-stats.html` | `data/review-stats.json` via `build_review.py` |
| Archived activities | `activity-logs.html` | `data/activity-logs.csv` via `build.py` |

Deep links: `…/time-motion-ibiza.html#Ibiza-T241` on Lagoons – Ibiza,
`…/activity-logs.html#BL515` on archived activities, `…/review-stats.html` for
the archived review stats. The site root used to be Lagoons – Ibiza time and
motion, and before that the archived activity log, so `index.html` forwards any
hash to wherever it lives now: a time and motion unit (`…/#Ibiza-T241`) to its
time and motion page, anything else (`…/#BL515`) to `activity-logs.html`.

## Pilot time and motion

Minutes logged on site per activity, for each unit in the *QAQC Time + motion*
workbook, one page per project: **Lagoons – Ibiza** (T240–T245) and
**Hills – Gems** (E511B). Each unit is its own tab in the workbook, and lands on
the page whose project its tab name starts with (`SITES` in
`build_time_motion.py`). `Gems-E511B_old` is an earlier take of Gems-E511B and
is skipped.

Two corrections from the pilot team are applied at build time, so the workbook
stays as logged: Ibiza T244 is hidden (`HIDDEN`), and T242's capture is the
Matterport survey logged on T244's tab rather than the iGUIDE row on its own
(`CAPTURE_FROM`). The check against each tab's own totals block runs on the
tab as logged, before either correction.

Each fill colour in the workbook is a different person, and the page keeps one
colour per person: MEP inspector (MEP general), MEP specialist (above ceiling),
QA inspector (QA functional), and capture (iGUIDE or Matterport).

- **Recorded time by unit** — each unit's minutes, split by person (on a page
  with more than one unit). A **Total time / Per 100 m²** switch redraws it
  normalised to floor area, so units of different sizes compare.
- **Unit details** — floor area and bedrooms beside each unit's name, and its
  recorded time per 100 m², from `data/time-motion-units.csv` (the workbook
  does not carry them). A unit missing from that file simply shows no details;
  a name in it that is not a workbook tab stops the build.
- **One card per unit** — every activity with its logged clock times, its
  minutes, and a timeline of the day. MEP general and QA functional open as a
  dropdown onto their sub-tasks (roof, yard; inside cupboard, tile tapping,
  roof) plus **Other functional**: the activity's minutes less its timed
  sub-tasks.
- **Tests** (`TESTS`), which the workbook does not carry: the flood test
  (30 min, every unit, no start and end time logged) was conducted by the
  contractor and verified by functional QA, and stays out of the unit totals;
  the static test (20 min, every unit, no times logged) is conducted by
  functional QA; the drain check is conducted by the MEP team on T240–T243 and T245,
  its minutes (man-hours) taken from the start and end logged on site. The
  static test and drain check are added as sub-tasks to QA functional and MEP
  general, and count towards that person's time and the unit's recorded time;
  the drain check is drawn on the unit's timeline with MEP general.

A blank MEP specialist row is shown as 30 minutes, marked *Start and end time
not logged*, and counts towards the unit's MEP and recorded time (`UNTIMED`);
the check against the workbook's own totals block leaves it out. Any other
blank row is shown as **Activity pending**; 0 minutes or "not recorded
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

The landing page. What the review team (MM and HA, shown by their initials) did to
the AI-generated snags on Lagoons – Ibiza T240, T241, T242, T243, T245 and
Hills – Gems E511B, read from each snag's change history in QA/QC. It is laid out
like the archived review stats and shares its page rules (`PAGE_CSS` in
`build_review.py`), with the review's own change categories.

- **Outcomes** — every AI-generated material snag is deleted, changed (its
  description or type was edited, or it was switched to non-material) or has
  no change. Priority and trade changes are counted separately, so a snag whose
  only change was its priority or trade counts as no change.
- **Deletions, Priority changes, Trade changes** — each as a share of the
  unit's material snags, with a bar.
- **Changes by category** — material → non-material, type update, and large
  (5 or more words) or small (1–4 words) description updates. A snag gets one
  description category, the highest of type > large > small.
- **Changes by person** and four **example changes**.

`data/review-timelines.json` is a snapshot of the QA/QC change history
exported on 28 Oct 2026 (each snag's issued state, its state that day and every
save in between): one row per snag (unit, snag, status, kind, generated by AI)
and one row per categorised change. Each change is the net change of one field,
from its issued value to its final value, so edits that were later undone are
not in it, and it is credited to whoever made the final save. A person changing
a field and changing it back within a minute is not an edit, and nor is a
description that differs only in spacing. The export does not carry whether a
snag is material or non-material, so each snag's kind, and the review's
switches to non-material, are as read from QA/QC on 22 Oct 2026. Snags added by
hand are in the file but not counted. Unit names and capture methods are in its `units` list; the
four worked examples are picked in its `examples` list.

## Archived Review Stats

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
`build_review.py`, `build_time_motion.py` and `build_review_timelines.py`, so
one command refreshes the site. Time and motion reads the workbook directly (cell fills included), which
needs `openpyxl`:

```sh
pip install openpyxl
cp "…/Damac snagging schedules - Activity logs.csv" data/activity-logs.csv
cp "…/QAQC_TIme+motion.xlsx" data/qaqc-time-motion.xlsx
# new units: add a line to data/time-motion-units.csv (unit,floor_area_sqm,bedrooms)
# review stats: replace data/review-timelines.json with a new snapshot
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
