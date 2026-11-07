# Local MVP change-request implementation

Implemented on `feature/mvp-change-requests`, based on the Streamlit dashboard branch and merged with the latest main-branch test additions. This branch is being published for deployment; no public deployment has been verified. The original `one-shot-prompt.md`, prepared data and community CSV are unchanged. Community evidence remains optional and is never fabricated.

## Implemented behavior

| Request | Result |
| --- | --- |
| CR-01 | Staff discussion checklist for stable Internet, secure device/connection and service requirements; no personal answers stored. |
| CR-02 | Counter-only minus Internet-only median difference in percentage points and USD-equivalent dollars, with direction, counts and unavailable handling. |
| CR-03 | Cost & disclosure is the dashboard startup default (2/3 cost, 1/3 disclosure). Community campaign priority remains selectable. |
| CR-04 | Cost bounds use all USA-origin corridors for the selected periods and basket. Country display filters do not change the reference. Scope, bounds and data fingerprint are disclosed. |
| CR-05 | Latest four calendar quarters shortcut applies the shared period selection and updates results. Manual selection remains available. Missing surveys remain gaps; no backfilling. Notebook choices include the same optional preset. |
| CR-06 | Quarterly coverage reports eligible/total quotes, coverage percentage, non-transparent exclusions and transparent missing costs. Missing surveys are distinct from zero matching quotes. |
| CR-07 | Plain-language findings, missing community inputs and evidence-gathering next steps precede technical details. Full tables remain available. |
| CR-08 | Per-corridor/currency minimum, maximum, median, eligible count and zero-fee count, plus currency-separated box plots. |
| CR-09 | Provider-only numeric range filters and ascending/descending sorting for cost, fee and FX margin, with a choice to retain unknown values. Service IDs, channel, date and disclosure status remain visible. |
| CR-10 | Per-service USD fee, FX-margin dollars, component-derived total, published total and difference. No guessed conversion for non-USD fees; unknown components remain unavailable. |

The briefing improvements are shared with the notebook and offline HTML export. Provider view filters do not remove evidence from the complete export. Old notebook outputs were cleared so earlier scores do not appear beside the updated calculation source.

## Checkable real-data cases

- USA to Mexico, 2025 Q3, USD 200: median 4.485% from 46 eligible quotes.
- Internet-only 4.01% versus Counter-only 4.60%: difference 0.59 percentage points, or USD 1.18 on the selected USD-200 basket. This compares groups, not guaranteed individual savings.
- USA to Mexico, 2025 Q1, USD 500: 45 eligible costs / 46 quotes = 97.8261% coverage, zero non-transparent exclusions and one missing transparent cost.
- Mexico 2025 Q3 USD-200 visible fees: median USD 5.695, range USD 0–35, two zero-fee quotes, 46 eligible fees.
- MoneyGram service `1212255489`: USD 2.99 fee + USD 2.20 FX-margin equivalent = USD 5.19 component-derived total. Published 2.60% implies USD 5.20; the USD -0.01 difference stays visible.
- Calendar preset: 2024 Q4–2025 Q3, using Q4/Q1/Q3 survey observations and preserving the absent Q2 gap.

## Shared-normalization impact assessment

For 2025 Q3 and USD 200, the full USA reference has corridor medians from 2.47% to 8.875%. Mexico's normalized cost is `(4.485 - 2.47) / (8.875 - 2.47)`, approximately 0.314598, whether Mexico alone, Mexico plus Philippines or all destinations are displayed. Its cost/disclosure score is approximately 0.209732 when its non-transparent share is zero.

Previously, a Mexico–Philippines display used 3.96%–4.485% bounds, making Mexico's normalized cost 1 and the Philippines' 0. The shared reference gives approximately 0.314598 and 0.232631 respectively. With both disclosure shares zero, Mexico still ranks above the Philippines in the cost/disclosure mode, but the score gap narrows. A single displayed country can now have a score when the full reference has enough valid medians. Synthetic tests verify stable bounds and scores when only displayed countries change.

The normalization change can alter rankings when cost competes with disclosure or documented community relevance. It is not merely a display adjustment, and old/new scores should not be mixed. No actual community-informed ranking is asserted without community evidence. Periods, basket, weights, evidence and data releases can still change scores legitimately.

## Verification

- Original dashboard suite, main-branch test additions and local Module 10 tests are retained.
- The full-run total includes the two Module 10 tests in `tests/test_kanishk_channel_costs.py`, included in the deployment branch alongside the 15 request-specific acceptance checks.
- Fifteen request-specific acceptance checks passed, including real-data cases, missing/reversed channel comparisons, CSV input immutability, complete exports and a Streamlit shortcut/filter workflow.
- Final regression run after summary-layout polish: **112 passed in 92.14s**. The summary uses readable country panels instead of a horizontally scrolling table.
- A local browser verified the Cost & disclosure default and the shortcut's three observed quarters/138 Mexico quotes. This is local evidence, not a live-host screenshot for the MVP validation.
- Hosted Linux execution and public access still require an authorized deployment and remain untested here.

## Run locally

From `~/dso576/project-dashboard/prof-build-M2`:

```bash
uv sync --locked
uv run streamlit run streamlit_app.py --server.address 127.0.0.1 --browser.gatherUsageStats false
```

Run tests with `uv run pytest -q` from the same folder. Check the root README for the branch and current deployment status.
