# DAMAC snagging pilot

Six tabs, one masthead. Each page is a real file with its own URL, so any of
them can be linked to on its own.

**https://conxai-technologies.github.io/damac-activity-logs/**

| Tab | Page | Built from |
| --- | --- | --- |
| Review Stats (default) | `index.html` | `data/review-timelines.json` via `build_review_timelines.py` |
| Pilot time and motion Lagoons – Ibiza | `time-motion-ibiza.html` | `data/qaqc-time-motion.xlsx` via `build_time_motion.py` |
| Pilot time and motion Hills – Gems | `time-motion-gems.html` | the same workbook, same script |
| Performance review | `performance-review.html`, and `performance-review-t240.html` etc. per unit | `data/performance-review.json` and `assets/performance-review/` via `build_performance_review.py` |
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

## Performance review

Performance analysis of AI on visual snags for Lagoons – Ibiza T240, T242, T243
and T245: each unit's onsite (manual) snags beside the AI snags on the ConXAI
dashboard. The tab lands on an overview with one row per unit; each unit has its
own page, reached with the unit buttons in the masthead.

- **Manual snags** — the target visual snags within the area the scan captured:
  the visual issue types except Ironmongery / aluminium scratches, stains and
  Shadow gap, roof excluded, in rooms the scan covered. Each has a match level
  (certain, likely, no match), and **recall** counts those captured by AI with
  a useful description (correct repair work, trade and location).
- **AI snags** — the unit's AI snags on the dashboard, roof excluded, material
  and non-material. Each is matched to an onsite snag (of any type), deleted on
  the QA/QC board, or an **additional true positive**: not covered by onsite
  and not deleted. Material means not tagged non-material on the dashboard.
- **Consolidated snag list** — every manual snag with its photos and the AI
  snag matched to it (dashboard snag ID, photo with the box drawn, description),
  then the AI-only snags, tagged deleted and material or non-material. Where the
  AI detection is not a separate snag on the dashboard, the detection itself is
  shown, marked *Snag merged with another*.

`data/performance-review.json` and the photos are exported from the snag-match
workspace (`plumbline_eval/export_performance_review.py`): manual snags and AI
snags from the 21 Oct 2026 dashboard export, match levels and recall from the
plumbline evaluation runs, the dashboard snag shown from snag-match's matching
rule (or the one the evaluation linked, when that is its own dashboard snag and
snag-match picked a different one), and deletions from the QA/QC change export
of 28 Oct 2026. Each photo is a single 640 px copy, used for the thumbnail and
the enlarged view alike, with the AI snag's boxes drawn over it on the page.

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

- **Review summary** — every AI-generated material snag is deleted, changed
  (its description or type was edited, or it was switched to non-material) or
  has no change. Priority and trade changes are counted separately, so a snag
  whose only change was its priority or trade counts as no change.
- **Performance improvements** — a bar chart of each field's share of
  material snags, and the shares accepted unchanged and deleted, on the archived
  page's Malta villas (Q844, Q845, Q545: the August version, read from
  `data/review-stats.json`) above the Ibiza units captured with Matterport
  (T240, T242, T243, T245: the September version). Each row's percentage
  improvement is the September share's fall below the August share (its rise,
  for accepted unchanged) as a percentage of the August share; a field resting
  on 10 or fewer snags a side shows — for not enough data. The two cover
  different units, so it compares shares, not counts.
- **All changes** — every material snag in one of four groups, with priority
  and trade counted: accepted as is; minor adjustment (a priority change, or a
  description adjustment of 1–4 words, and nothing else); major adjustment (any
  other change, or a combination of changes, such as a priority change with a
  1–4 word description adjustment); deleted.

The rest sit under **Change details**:

- **Deletions, Priority changes, Trade changes** — each as a share of the
  unit's material snags, with a bar.
- **Changes by category** — material → non-material, type update, and large
  (5 or more words) or small (1–4 words) description updates. A snag gets one
  description category, the highest of type > large > small.
- **Changes by field** — the archived page's table on its rules: priority,
  description (type included), trade, location and photo, with a kept snag
  changed if any of them was edited. The review team edited no location or
  photo (the change history's location edits are all automated updates), and a
  switch to non-material is not an edit to any of the five fields.
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
`build_review.py`, `build_time_motion.py`, `build_review_timelines.py` and
`build_performance_review.py`, so one command refreshes the site. Time and motion reads the workbook directly (cell fills included), which
needs `openpyxl`:

```sh
pip install openpyxl
cp "…/Damac snagging schedules - Activity logs.csv" data/activity-logs.csv
cp "…/QAQC_TIme+motion.xlsx" data/qaqc-time-motion.xlsx
# new units: add a line to data/time-motion-units.csv (unit,floor_area_sqm,bedrooms)
# review stats: replace data/review-timelines.json with a new snapshot
# performance review: re-run the snag-match export into this repo
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
