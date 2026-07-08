# Manufacturing Report Dashboard Refinement Plan

## Goal

Make the dashboard more polished, easier to interpret, and more useful for senior management reviewing the outcome of a manufacturing run.

The main improvement opportunity is not adding more charts. The opportunity is making the result of the selected batch easier to understand quickly:

- Did the batch meet specification?
- Is the batch within historical expectations?
- Are there any points outside the +/-3SD range?
- What should leadership pay attention to?

## Recommended Refinements

### 1. Add an Executive Status Strip

Add a compact status strip near the top of the report that summarizes the selected batch.

Example:

```text
Run Status: In Spec | Within Historical Range | No 3SD Excursions
```

Possible status fields:

- Specification status
- Historical range status
- 3SD excursion status
- Overall run status

Why this helps:

Senior management can understand the result quickly without inspecting every chart.

### 2. Add a Manufacturing Run Summary

Add a short summary section for the selected batch.

Suggested fields:

- Construct
- Project
- Batch of interest
- Date of manufacture
- Dose level
- QC-4 result
- QC-5 result
- Viability result
- Specification flags
- Outside +/-3SD flags

Why this helps:

This turns the dashboard into a clearer report. The reader sees the most important facts before digging into the visual details.

### 3. Add Selected-Batch Chart Callouts

For each chart, add a small summary under the chart title.

Example:

```text
Selected batch: 35.0% | Historical avg: 41.0% | Spec: 10.0%
```

Why this helps:

The user does not need to hover over the chart or estimate values from the axis to understand the selected batch result.

### 4. Fix Sticky Filter Overlap

The sticky filter bar can visually crowd or overlap chart headers while scrolling.

Recommended improvement:

- Add more top spacing around chart sections.
- Add scroll margin to major sections.
- Confirm QC-4 and QC-5 titles remain visible when scrolling.

Why this helps:

The report will feel cleaner and more deliberate during normal use.

### 5. Improve Chart Header Layout

Refine how chart titles and dropdown controls are positioned.

Recommended improvement:

- Keep chart titles visually dominant.
- Keep dropdown controls grouped and right aligned.
- Use consistent spacing across line charts and flow charts.
- Slightly reduce dropdown visual weight if needed.

Why this helps:

The viewer can scan the report more easily and the charts feel more polished.

### 6. Strengthen Reference Line Styling

Make average, SD, and specification lines more visually distinct.

Recommended convention:

- Historical average: black dotted line
- SD limits: gray dotted line
- Specification: light red dotted line
- Selected batch: CU Gold
- Flagged selected batch: red

Why this helps:

Each line type has a different meaning. The styling should make those differences obvious.

### 7. Clean Up Footer Source Text

Replace the full local file path in the footer with a cleaner source note.

Current style to avoid:

```text
C:\Users\sladeand\Desktop\...
```

Suggested replacement:

```text
Source: Codex Manufacturing Data.xlsx | Generated: 08JUL26 10:25
```

Why this helps:

The report will look more professional when shared or exported.

### 8. Clarify Historical Baseline Meaning

Consider whether the dashboard should more clearly explain that historical averages and SD ranges exclude the selected batch.

Possible approaches:

- Keep the current KPI wording but improve nearby explanatory text.
- Add a tooltip or small note near SD controls.
- Add a short methodology note near the footer.

Why this helps:

This prevents confusion about how the historical average and SD ranges are calculated.

### 9. Review Date Formatting

The current `DDMMMYY` format is compact and useful for operational audiences.

Possible options:

- `11JUN26`
- `11 Jun 2026`
- `June 11, 2026`

Recommendation:

Keep `11JUN26` if the primary audience is technical or operational. Consider `11 Jun 2026` if the report will be circulated broadly to leadership.

### 10. Improve Print/PDF Output

The report has a Print/PDF button, so the printed version should feel polished.

Recommended improvement:

- Prevent chart cards from splitting across pages.
- Disable sticky filter behavior in print mode.
- Keep chart legends with their charts.
- Keep alert bubbles with their charts.
- Ensure the logo and title print cleanly.

Why this helps:

The exported version should look intentional, not like a browser screenshot.

## Suggested Implementation Order

1. Clean up footer source text.
2. Fix sticky filter overlap.
3. Add executive status strip.
4. Add manufacturing run summary.
5. Add selected-batch chart callouts.
6. Refine chart header layout.
7. Strengthen reference line styling.
8. Clarify historical baseline meaning.
9. Review date formatting.
10. Improve Print/PDF output.

## Definition of Done

The dashboard should allow a senior manager to answer these questions within 30 seconds:

- What batch am I looking at?
- Did the batch meet specification?
- Is the batch outside historical expectations?
- Are there any exceptions that require attention?
- What are the most important QC-4, QC-5, viability, and concentration results?

