# R4.1 case screenshot refresh

Baseline: d3d737b, origin/feature/mvp-change-requests. No app changes authorized.
Criteria: each case figure must visibly identify its origin/destination scope, selected survey quarters, transfer basket and scoring mode. Browser-address excerpts paired with a full app view on one PDF page are treated as one figure, not a separate result screenshot.

| Case / PDF pages | Before inspection | Action |
|---|---|---|
| 2.1 Elena, pp. 6–11, Figures 1–6 | All retain the sidebar: Mexico, selected quarters, USD 200 and Cost & disclosure. | Keep all. |
| 2.2 CHIRLA Ana, pp. 16–17, Figures 1–2 | Cropped panels show Mexico, 2025 Q3 and USD 200, but omit scoring mode. | Recapture both with sidebar. |
| 2.3 cash-pickup Ana, p. 21 overview | Full view includes Mexico, 2025 Q3, USD 200, mode and saved settings. | Keep. |
| 2.3 cash-pickup Ana, pp. 22–23 provider views | Table-only crops do not show transfer basket or scoring mode. Right-hand view also omits destination and period. | Recapture both with sidebar. |
| 2.4 Lea, p. 27 Figure 1 | Settings excerpt shows Philippines, 2025 Q3, USD 500, but omits mode. | Recapture with sidebar. |
| 2.4 Lea, pp. 28–29 Figures 2–3 | Result-only crops show country and basket but no quarter/mode. Figure 1's USD 500 does not establish Figure 2's USD 200. | Recapture each executed amount with sidebar. |
| 2.5 IFAD Ana, p. 33 Figure 1 settings | Full sidebar and saved settings present. | Keep. |
| 2.5 IFAD Ana, p. 34 Figure 1 guidance excerpt | Result text only; no destination scope/quarter controls. | Recapture with sidebar using all countries. |
| 2.5 IFAD Ana, p. 35 Figure 2 ranking | Table-only crop lacks quarter/basket/mode. | Recapture with sidebar using all countries. |
| 2.5 IFAD Ana, pp. 36–37 Figures 3–4 | Both full app views retain sidebar; address-bar strips are paired with them on the same PDF page. | Keep both figures, including their address strips. |

Inspected: 21 referenced case image assets, displayed on 19 figure pages in the 47-page validation.pdf. Replaced: 9 figure views on 9 pages, using 8 distinct new screenshots. Lea Figures 1 and 3 reuse the identical USD 500 viewport from the same successful run. Existing standalone case PDFs and their source screenshots remain historical originals. Only the team validation report needs updated screenshots.

## Capture record and review

Captured from the public URL in README.md, https://project-c2b8ykvnwmkqm8o59iqymy.streamlit.app/, on November 22, 2026. The app initially displayed its sleep screen; clicking its wake button restored the app. Chrome captured each viewport directly at 1600 × 1000. The images were not composited, annotated or edited. Every refreshed figure visibly includes USA-origin context, destination selection, 2025 Q3, transfer basket and Cost & disclosure mode in the actual sidebar. An empty Destinations field means all available countries, as the sidebar states; the saved all-country run confirms 42 countries.

Clicked Update analysis after changing analytical inputs and checked the saved result before taking each capture. Existing default cost/disclosure weights were retained. Provider-table search was empty, ordering was Most recent selected records, ascending was unchecked, and numeric filters were unused. The left and horizontally scrolled right captures use the same table/run. View changes and scrolling did not change analysis settings.

| Replacement view | Capture time (PST) | Screenshot |
|---|---|---|
| case-2.2-figure-1 | 2026-11-22 11:03:42 | [case-2.2-figure-1.png](screenshots/r41/case-2.2-figure-1.png) |
| case-2.2-figure-2 | 2026-11-22 11:04:20 | [case-2.2-figure-2.png](screenshots/r41/case-2.2-figure-2.png) |
| case-2.3-provider-left | 2026-11-22 11:04:40 | [case-2.3-provider-left.png](screenshots/r41/case-2.3-provider-left.png) |
| case-2.3-provider-right | 2026-11-22 11:04:43 | [case-2.3-provider-right.png](screenshots/r41/case-2.3-provider-right.png) |
| case-2.4-figure-2 | 2026-11-22 11:05:36 | [case-2.4-figure-2.png](screenshots/r41/case-2.4-figure-2.png) |
| case-2.4-figure-1 | 2026-11-22 11:05:42 | [case-2.4-figure-1.png](screenshots/r41/case-2.4-figure-1.png) |
| case-2.4-figure-3 | 2026-11-22 11:05:42 | [case-2.4-figure-1.png](screenshots/r41/case-2.4-figure-1.png) |
| case-2.5-figure-1-guidance | 2026-11-22 11:06:19 | [case-2.5-figure-1-guidance.png](screenshots/r41/case-2.5-figure-1-guidance.png) |
| case-2.5-figure-2 | 2026-11-22 11:06:42 | [case-2.5-figure-2.png](screenshots/r41/case-2.5-figure-2.png) |

Visible results checked against the existing cases:

- Lea USD 200: Philippines, 2025 Q3; 3.960%, 58 eligible costs from 58 quotes, zero nondisclosure flags.
- Lea USD 500: same country/quarter/mode; 2.860%, 57 eligible costs from 58 quotes, zero nondisclosure flags.
- Mexico: 4.485%, 46 eligible costs from 46 quotes. Channel rows retain 4.01% / 29 Internet-only, 4.60% / 15 Counter-only, 4.73% / 2 Other/unknown. Provider screenshots retain the original row ordering and show the corresponding cost components.
- IFAD all-country view: 1,010 matching and eligible quotes, zero non-transparent quotes. The highest rows retain Afghanistan 8.875% / 6, Cuba 7.750% / 4, Bangladesh 7.525% / 24, Guyana 7.350% / 21 and Armenia 6.950% / 16. Afghanistan guidance remains 8.875% / 6.
- Live Detailed preparation provenance displayed the same prepared-data SHA-256 as the repository: `fe8d6f2921450494ca27ff9503e50e1d24f53934af1bc4bddb02566bac205910`. This identifies the prepared data, not the deployed code commit.

## Scope and verification

Updated validation.md references/captions and validation.pdf only where the screenshot refresh required it. Retained original standalone case PDFs and all original image files. Corrected screenshot descriptions that would otherwise incorrectly describe the new captures as two-panel composites or part of the original historical run. The application's code, data, case conclusions and numerical analysis were not changed.

The existing build_validation_draft.py produces an incomplete draft and depends on Windows fonts. To keep the report change limited, updated the figure regions of the existing final PDF and their captions, plus the screenshot-provenance paragraph on page 18 and the caption on page 33. Preserved page sizes, page count, original headers, footers and all external link targets. Used Calibri from the installed Microsoft Word fonts for replacement text.

Verification command used for the document checks in this session:

```text
/tmp/m2-r41-tools/bin/python /tmp/m2-r41-inspection/verify_report.py
```

Results: the PDF remains 47 pages; 36 untouched pages render pixel-identically to the baseline; all 9 replacement figure pages embed their exact unaltered screenshot pixels; all 23 Markdown image references resolve; refreshed captions match the PDF text; the 49 existing external link targets are preserved; original files under prof-build-M2/, cases/ and validation-draft-assets/ are unchanged. All 11 updated PDF pages were rendered and visually reviewed for readable controls/results, captions and overlap.

```text
git diff --check -- validation.md
```

Output: none (exit 0). Full git diff --check treated this PDF as text and reported whitespace inside valid binary PDF streams; the whitespace check therefore applies to Markdown, while the PDF is checked by opening/rendering and comparing its pages and embedded images.

No application regression suite, original-workbook reanalysis, current-price verification or deployment change was performed. This is a screenshot/report repair. Student review is pending; no commit or push has been made.

## Follow-up: caption accuracy and executed settings

The student reported that page 28's Philippines / 2025 Q3 / USD 200 and result match its caption. Other student review remains unrecorded.

Page 35's caption now says: “This screenshot shows the top portion of the corridor table, including the five highest-cost corridors and additional rows; it is not the complete 42-country table.” This matches a view containing rows below Armenia. Only this caption was changed in the PDF for this follow-up. Its screenshot is unchanged, and all other 46 PDF pages render pixel-identically to the pre-follow-up version.

Execution evidence was rechecked against the original temporary browser jobs, their completion records, the saved body-text snapshots written by the same capture calls, and the actual screenshot sidebars. The manually supplied selection descriptions in capture-records.json were not treated as independent proof of execution.

| Refreshed pages | Visible controls and saved-result metadata | Evidence of execution |
|---|---|---|
| 16, 17, 22, 23 | USA → Mexico; 2025 Q3; USD 200; Cost & disclosure | Job 004 clicked Update analysis and completed. Every corresponding capture-time body snapshot retains the same Saved analysis and Executed mode. Only tabs, checklist expansion and scrolling changed afterward. |
| 28 | USA → Philippines; 2025 Q3; USD 200; Cost & disclosure | Job 011 changed the destination, clicked Update analysis, checked its saved header and 3.960% / 58 result, then captured. |
| 27, 29 | USA → Philippines; 2025 Q3; USD 500; Cost & disclosure | Job 011 then selected 500, clicked Update analysis again, checked the saved header and 2.860% / 57 result, then captured. Figure 3 reuses that same captured image. |
| 34, 35 | USA → all 42 receiving countries; 2025 Q3; USD 200; Cost & disclosure | Job 012 cleared Philippines, selected 200, clicked Update analysis and completed. Capture snapshots confirm the all-country saved header and mode. Only expander/tab/scroll actions separate guidance and ranking captures; job 013 confirms the ranking run's 1010 / 1010 / 0 counts. |

All nine refreshed views' saved body snapshots contain neither the pending-controls warning nor an analysis-error message. The screenshot helper waited for execution to finish before saving. Job 006's later checklist-wording assertion failed after its first channel screenshot was already captured; job 008 successfully captured the corrected checklist view. This failed attempt is retained, not treated as an extra Update or discarded from the record.

The evidence confirms the executed selections for the refreshed views; control visibility alone was not the basis. These are saved browser-session records, not a new live replay or an independent audit of all numerical calculations.

**Unconfirmed execution history:** original retained figure pages 6–11 (Elena), 21 (cash-pickup overview), 33 (IFAD original settings), and 36–37 (IFAD fees/channels) were not recaptured in this work. Their capture-time Update actions are unavailable in this session. Visible controls on those old screenshots do not by themselves establish that Update was clicked or that the saved result matched; their execution history has not been independently confirmed.

Temporary evidence locations: /tmp/m2-r41-inspection/jobs/, capture-records.json and the per-capture *.png.txt snapshots. The follow-up checker produced followup-execution-check.json with extracted saved headers and hashes of the inspected snapshots/current screenshot files. Those hashes were computed during this follow-up, not at original capture time.

## Caption recheck: provider header and ranking punctuation

Page 23's right-scrolled table still clips the leftmost column heading. Its Markdown and PDF caption explicitly says: “The leftmost column header is truncated. Check the complete export to verify that column; do not infer its meaning from the clipped header.” The screenshot and its underlying values were not changed. The caption does not infer which column the incomplete header represents.

Page 35's caption opening now reads “Highest corridor medians in the public run. Same executed settings as Figure 1.” Both pages were rendered and visually checked again: caption text is readable and consistent with the screenshots; no caption overlap was found. The remaining clipping in the provider screenshot is disclosed, not repaired. All other 45 PDF pages render pixel-identically to the pre-correction PDF; the screenshot/header regions on both edited pages are also pixel-identical. Page count remains 47. No application code, data or screenshot assets changed.
