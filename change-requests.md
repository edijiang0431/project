# Change requests

Our team's log of what we found and what should change, kept in the top folder of our team repo
from Module 9 to Module 13. Pull before you edit it and push soon after.

- For each finding, copy the request template below to the end of this file, give it the next
  number and fill in every field.
- Never delete a request. When it is built, set its status to `built` with the commit; when the
  team decides against it, `declined` with the reason.
- When this file gets long, ask Codex to move the built and declined requests into a dated file
  in `change-requests-archive/` (for example `change-requests-archive/2026-11-02.md`) and leave
  only the open ones here. Numbers continue; never reuse one.

Request template:

```markdown
### CR-NN: short title

- **From:** name, YYYY-MM-DD
- **Part:** the feature, number or function
- **Evidence:** what you did and saw: the input, what you expected, what the tool gave
- **Change:** what should change, in a sentence or two
- **Priority:** high, medium or low
- **Status:** open
```

A filled request (from the class lottery app):

```markdown
### CR-01: chance above 100% with two slots

- **From:** Ana, 2026-10-21
- **Part:** `odds` (the chance of selection by wage level)
- **Evidence:** one person at Level I and one at Level IV, two slots. Both must be selected,
  so each chance is 1. `odds` gave 0.4 and 1.6.
- **Change:** select each person at most once (without replacement), so no chance passes 1.
- **Priority:** high
- **Status:** open
```

## Requests

<!-- Add new requests below this comment, at the end of the file, newest last. -->

### CR-01: Add an Internet-access checklist before encouraging a channel switch

- **From:** Kanishk (kanishk1203), 2026-10-23
- **Part:** Channel comparison and campaign briefing
- **Evidence:** For USA to Mexico, Q3 2025 and USD 200, the notebook shows Internet-only median cost 4.01% from 29 quotes and Counter-only 4.60% from 15 quotes. This supports exploring Internet services, but the briefing offers no structured check of whether a sender has stable, secure Internet access. Price quotes do not establish individual access or suitability.
- **Change:** Include an Internet-access checklist in the notebook briefing and offline export for CHIRLA staff to discuss with senders before encouraging a switch. Ask about connection reliability and secure access; present answers as community validation, never infer them from quote data.
- **Priority:** medium
- **Status:** open

### CR-02: Calculate the dollar equivalent of the channel median-cost difference

- **From:** Kanishk (kanishk1203), 2026-10-23
- **Part:** Channel comparison calculation and briefing
- **Evidence:** For USA to Mexico, Q3 2025 and USD 200, Internet-only and Counter-only median costs are 4.01% and 4.60%. The briefing shows percentage medians but does not calculate their difference in dollars. The 0.59-percentage-point difference is equivalent to $1.18 on $200. My independent overall-median calculation also agrees with the app at 4.485% from 46 quotes; this request concerns interpretation, not a demonstrated calculation error.
- **Change:** Calculate `(Counter-only median cost % - Internet-only median cost %) / 100 * selected transfer amount` for each selected corridor and display the dollar difference, its direction, the percentage-point difference and both eligible quote counts in the notebook and export. Show unavailable when either median is missing and describe the result as a historical group comparison, not guaranteed individual savings. Verify $1.18 for this selection and handle equal or reversed medians.
- **Priority:** medium
- **Status:** open

### CR-03: Add a cost-and-transparency comparison mode

- **From:** Nicharee Ratanajaratkul (Prae), 2026-10-25
- **Part:** Part 1 — Priority ranking
- **Evidence:** With MEX and PHL selected for 2025 Q3 and USD 200 using default weights, median costs were 4.485% and 3.96% and both non-transparent shares were zero, but composite scores remained unavailable because documented community relevance was missing.
- **Change:** Add an explicitly selectable cost-and-transparency comparison mode with weights of two-thirds normalized cost and one-third non-transparent share, showing measures, contributions, and weights. Keep community evidence separate and missing values unavailable, retain the community-informed mode, and explain that this score does not assess community relevance or automatically select a campaign target.
- **Priority:** high
- **Status:** open

### CR-04: Use a shared reference for cost normalization

- **From:** Nicharee Ratanajaratkul (Prae), 2026-10-25
- **Part:** Parts 1–2 — Priority ranking and Mexico’s normalized cost
- **Evidence:** For 2025 Q3 and USD 200, Mexico's median remained 4.485% from 46 eligible quotes, but its normalized score changed from 1 for MEX–PHL to 0.314598 across 42 valid-cost corridors. Independent checks matched both displayed scores at six decimal places. Bounds changed from 3.96%–4.485% to 2.47%–8.875%. This follows the current formula rather than showing a calculation error.
- **Change:** Calculate normalization bounds from all available USA-origin corridors with valid eligible medians for the selected periods and transfer amount before filtering displayed countries. Show reference scope, bounds, data version, and actual median costs; explain when scores can change and assess the effect on composite rankings before adoption.
- **Priority:** medium
- **Status:** open

### CR-05: Add a latest-four-calendar-quarters shortcut for trend analysis

- **From:** Yuqian Chen (YuqianC0724), 2026-10-25
- **Part:** Part 1 — Quarter-specific evidence and notebook period selection
- **Evidence:** The default selection is MEX, 2025 Q3, USD 200. Running the existing analysis and rendering functions produces one cost point at 4.485% and one non-transparent-share point at 0; this cannot show whether a problem persists. Manually selecting multiple quarters produces a usable comparison. The current renderer already preserves 2025 Q2 as “No survey data” and breaks the line, and distinguishes an available but unselected quarter as “Not selected.” The missing convenience is selecting a recent calendar window without constructing the period list manually.
- **Change:** Add an executable “Latest four calendar quarters” preset anchored to the latest available survey quarter. Apply it to the shared analysis period selection and rerun analysis so charts and summary tables remain consistent; visibly state the requested calendar window and available survey quarters used. For this dataset, the window must be 2024 Q4–2025 Q3, using Q4, Q1 and Q3 observations while retaining the Q2 gap, with no backfilling from older quarters. Preserve manual selection and show a clear message if the window contains fewer than two usable time points.
- **Priority:** medium
- **Status:** open

### CR-06: Show usable-cost coverage alongside quarterly trend points

- **From:** Yuqian Chen (YuqianC0724), 2026-10-25
- **Part:** Part 2 — Quarter-specific median-cost evidence in notebook and HTML briefing
- **Evidence:** For USA → MEX, 2025 Q1, USD 500, a CSV loop with decimal sorting independently gives a median of 2.77%, matching the app. There are 46 matching quotes and zero non-transparent quotes, but one transparent quote has a missing USD 500 cost, leaving only 45 eligible costs. The chart shows cost and non-transparent share; counts are available in the table below, but usable-cost coverage and the missing-cost distinction are not presented alongside the chart. A zero non-transparent share therefore does not establish complete cost coverage. This is an interpretation improvement, not a demonstrated median-calculation error.
- **Change:** In the notebook and offline export, add a compact coverage summary next to the cost chart for each corridor and selected quarter: eligible cost observations / total quotes, coverage percentage, non-transparent exclusions, and transparent quotes with missing selected-amount costs. For this case show 45/46 (97.8%), zero non-transparent exclusions and one missing transparent cost. Calculate counts for the selected transfer amount, keep missing costs unavailable, and show unavailable coverage rather than dividing by zero when there are no quotes. Keep missing-survey gaps distinct from observed quarters with incomplete costs.
- **Priority:** medium
- **Status:** open
