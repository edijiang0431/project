# Review of Ana's individual case

## Five template requirements

1. **Person and decision:** Specific illustrative CHIRLA researcher, a workshop-planning decision, timing and consequences. The file does not claim a real interview or an actual CHIRLA remittance workshop.
2. **Situation and alternatives:** Three free primary sources, with linked titles and short supporting quotations. Alternatives include the underlying World Bank data, current quotes and participant conversations. Sources support the setting and comparison process; no current provider quotes or participant interviews were collected for this case.
3. **Live use:** Public URL, origin, country, basket, quarter, mode and navigation recorded. Two actual live screenshots show selections, channel counts and medians, and the access checklist. Cropped versions only arrange original pixels; original captures remain alongside them.
4. **Interpretation:** All four questions answered. The case distinguishes quotes from customers, groups from individual transfers, historical data from current prices, and comparison from causation. It ties absent participant information to the workshop decision. The independent calculation agrees with the displayed values.
5. **Verdict:** Preserves Kanishk's decisions: one section of a broader workshop; both misleading claims rejected; existing comparison and checklist sufficient for that limited use with current quotes and participant conversations. The case supports adequacy for this bounded task, not universal optimality. No new change request is invented.

## MVP criteria 6 and 7

- **Criterion 6, realistic cases:** This individual case is specific, source-supported and demonstrated on the public app. Its boundary case is whether a historical channel comparison is enough to choose a workshop's main topic; the answer is no. It does not claim to cover all of the team's user types. That broader coverage must come from teammates' separate cases in the team's validation PDF.
- **Criterion 7, interpretation:** The price measure, observation unit, excluded groups, absent local/personal circumstances, misleading readings and decision limits are explicit and supported by screenshots, sources and a separate calculation. No individual savings, sender counts or causal effects are claimed.

## PDF and evidence checks

- Four PDF pages rendered and visually inspected: no clipped text or overlapping sections. The first three pages contain the memo; the fourth contains the complete executable calculation and actual output.
- Both screenshot figures appear and their medians, counts and access questions are readable. Every channel-table column is retained in two panels, with channel identifiers repeated. The checklist figure excludes the unrelated partly visible table below it.
- Source and live-app hyperlinks are embedded in the PDF.
- The final memo contains all five numbered sections and no pending-answer placeholders.
- `check_ana_channels.py` ran in the team's uv environment: 29 Internet quotes at 4.010%, 15 Counter quotes at 4.600%, two Other/unknown at 4.730%, overall median 4.485%, difference $1.18. Printed result: `Comparison with live medians and counts: MATCH`.
- The check re-aggregates prepared data with a separate method. It does not independently verify workbook cleaning, the survey's sampling, today's prices or participant circumstances.

## What was left out of the final memo

The working record remains intact. The final version omits preparation instructions, completion checklists, conversational wording and repeated narrative. The appendix now includes the complete executable code and actual output; only the script's introductory docstring and blank lines are omitted for space. All imports, calculations, output statements and checks are retained. Optional ACS scoring is not used for this channel-comparison decision.

## Submission-audit gaps resolved

- The independent code and its actual output are embedded in the PDF, not merely referenced as separate files.
- Part 4 explicitly identifies Module 11 Kind 1: one row per what.
- The rightmost table columns are visible in the replacement screenshot panels; no values or screenshot text were redrawn.
- The five-part structure, three linked sources and the student's limited-use verdict remain intact. All local content/format gaps identified in the audit are resolved. The case claim remains based on the student's confirmation of the team's agreement; neither that email nor the team's combined validation document was independently verified.

## Delivery status

The individual PDF and Markdown are saved locally. No case files have been committed or pushed, no messages have been sent and no Brightspace submission has been made. The student should open the PDF before uploading it. The team must also include the final case in Section 2 of its validation PDF.
