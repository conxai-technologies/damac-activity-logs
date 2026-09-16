# DAMAC snagging pilot — activity log

Time and effort logged for each unit in the DAMAC × CONXAI snagging pilot,
organised one card per unit.

**https://conxai-technologies.github.io/damac-activity-logs/**

## Layout

- **Programme at a glance** — which days each unit was worked on.
- **One card per unit** (Q845, Q844, Q545, BL109, BL515, C625F, K148) with the
  four phases: manual QA snagging, manual MEP snagging, capture, processing.
- **Full log, side by side** — the source sheet, normalised, for cross-unit comparison.

Filter to a single unit with the chips at the top; the selection deep-links
(`…/#BL515`).

Each unit carries its floor area, taken from the unit's own header cell in the
sheet's first row (`BL515 (200.3 sq. m)`), beside the unit name and under the
column head in the full log.

## Rebuilding

`index.html` is generated. After updating the sheet:

```sh
cp "…/Damac snagging schedules - Activity logs.csv" data/activity-logs.csv
python3 build.py
git commit -am "Refresh activity log" && git push
```

`build.py` normalises the sheet's mixed date formats and duration strings, and
cross-checks each stated duration and manhours figure against the times recorded
beside it — a mismatch is flagged on the page rather than corrected. Nothing is
inferred: `N/A` renders as `—` and `tbc` stays `tbc`.
