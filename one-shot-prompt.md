# Build RemitRight LA

Build a local notebook decision-support tool using only this prompt, the dataset repository below and the public internet. No original component files are required. Do not invent researcher inputs, evidence, prices or community characteristics.

## 1. Vision and design

The user is a campaign researcher at the Coalition for Humane Immigrant Rights (CHIRLA), choosing a U.S.-to-destination corridor for its next “know what you really pay” outreach campaign. Staff review priorities annually and when survey data changes. Replace separate spreadsheet, corridor-page and community-evidence reviews with one reproducible briefing. The tool supports staff judgment; it does not automatically select a target. An IFAD adaptation is possible later; build the CHIRLA workflow now.

Use cases:

- Select periods, destinations and USD 200/500; compare costs and explainable scores to shortlist communities.
- Inspect provider fees, unknown margins and non-transparent shares to choose an evidence-based campaign message.
- Compare Internet-only and Counter-only quotes, retaining Mixed and Other/unknown; inspect quarter-specific cost and transparency charts for persistence.
- Supply documented community-relevance judgments and adjust weights; inspect component scores and unscored reasons before deciding priorities.
- Export the exact current analysis as an offline HTML briefing.

Staff care about time, quality, freshness, privacy and explainability. Use no personal member records. Show collection dates and survey periods; explain that quotes are historical, not guaranteed live prices, and require current-price/community checks before publishing. Relevance is researcher judgment, never inferred population or customer usage.

| Principle | Reason |
|---|---|
| Prepare once, load once per session | Avoid repeated workbook parsing during interactions. |
| Explicit inputs and typed results | Eliminate hidden state and mismatched report settings. |
| Calculation owns measures | Notebook and export agree and can evolve independently. |
| Preserve units, missing values and quote records | Avoid false zero costs, currency mixing and accidental deduplication. |
| Separate relevance from quotes | Preserve provenance and visible researcher judgment. |
| Build/test pieces independently | Localize failures; each piece fits one agent session. |

| Piece | Files | Input → output |
|---|---|---|
| Prepare Data | `src/prepare_data.py`, startup `src/load_data.py` | Workbook → validated compressed CSV → in-memory prepared table. |
| Filter Data | `src/filter_data.py` | Prepared table + period/destination lists → unchanged-schema matching copy. |
| Calculate Summaries | `src/calculate_summaries.py` | Matching quotes + explicit current inputs → `AnalysisResults`. |
| Present Results | `src/present_results.py` | Result bundle → notebook tables, warnings and figures. |
| Export Briefing | `src/export_briefing.py` | Same bundle → unique standalone HTML path on explicit request. |

Shared types/schema validation live in `src/contracts.py`; relevance loading in `src/load_relevance.py`; orchestration in `analysis.ipynb`. Shared rendering helpers may draw/format existing results, never calculate measures. No function mutates caller tables/lists, reads hidden notebook globals or relies on another component's internals. Do not introduce generic Settings/build_view contracts or cost-threshold filtering.

## 2. Data, environment and execution

Dataset repository: `https://github.com/USC-DSO-576-PS/dataset_wb-remittance-prices.git`, cloned as sibling `../dataset_wb-remittance-prices`. Read its README, data overview and workbook Legend; do not modify that repository. Credit “Remittance Prices Worldwide, World Bank Group” under its CC BY 4.0 terms.

Use Python 3.11+, pandas for filtering/grouping/medians, openpyxl for Excel, Matplotlib for static charts, IPython for display and JupyterLab/ipykernel for execution. Manage a project-local uv environment with declared dependencies/lockfile, independent of the course parent environment; use pytest for meaningful synthetic checks. SQL is unnecessary: the U.S. subset is approximately 30,000 rows; an all-string 42-column measurement used about 17.934 MiB (prepared types may differ). Keep the prepared U.S. table and current summaries in memory, discard the full workbook after preparation, load CSV once per session, and recalculate/reuse one bundle on changed inputs.

Provide these README commands after uv installation:

```bash
uv sync
uv run python ../dataset_wb-remittance-prices/download_data.py
uv run python src/prepare_data.py --input ../dataset_wb-remittance-prices/data/rpw_dataset_2011_2025_q3.xlsx --output data/rpw_usa_clean.csv.gz
uv run pytest
uv run jupyter lab analysis.ipynb
```

Clone the dataset URL as a sibling first if absent. Its downloader writes beside itself and may fetch a newer filename: print its actual path and substitute it explicitly in `--input`; never silently choose among workbooks. If download fails, follow the dataset repository's browser instructions. Preparation with no CLI arguments uses the baseline input path above and output `data/rpw_usa_clean.csv.gz`; missing files give actionable errors.

Generated files: compressed CSV, validation/change report beside it, and `exports/*.html`; ignore generated data, exports and notebook checkpoints in Git. Keep relevance separate; supply only a header template, never fictional researcher entries. Outputs stay local. Future cloud plan: validated preparation at deployment, CSV loaded once per process, user-isolated settings/results, web tables/charts and HTML download around unchanged calculation contracts. No live API, database or interactive plotting backend is needed.

## 3. Prepare and load

```python
def prepare_data(input_path: str, output_path: str) -> None: ...
def load_data(path: str) -> pd.DataFrame: ...
```

Read only `Dataset (from Q2 2016)`, `usecols="A:AP"`, initially `dtype=str`: 42 published columns. Do not combine the differently structured older sheet; ignore undocumented columns beyond AP. One row is a provider's service in one corridor during one survey round. Multiple services from the same provider/corridor/period are legitimate. Retain only USA-origin rows in prepared output.

Normalize headings to lowercase snake case and `%`→`pct`. Exact published prepared columns before additions:

```text
id, period, source_code, source_name, source_region, source_income,
source_lending, source_g8g20, destination_code, destination_name,
destination_region, destination_income, destination_lending,
destination_g8g20, firm, firm_type, payment_instrument, access_point,
speed_actual, cc1_lcu_amount, cc1_denomination_amount, cc1_lcu_code,
cc1_lcu_fee, cc1_lcu_fx_rate, cc1_fx_margin, cc1_total_cost_pct,
cc2_lcu_amount, cc2_denomination_amount, cc2_lcu_code, cc2_lcu_fee,
cc2_lcu_fx_rate, cc2_fx_margin, cc2_total_cost_pct, inter_lcu_bank_fx,
transparent, standard_note, note2, receiving_network_coverage,
pickup_location, pickup_method, date, corridor
```

Keep IDs/codes/corridor as strings; convert amount, denomination-amount, fee, exchange-rate, margin and total-cost fields (including `inter_lcu_bank_fx`) to numeric. Parse `date` from valid native Excel or text dates. Require period `YYYY_nQ`, n=1–4, and derive `period_start` as that quarter's first day. Reporting quarter comes from period, not collection date. Strip text outer whitespace/collapse repeated internal spaces; preserve provider capitalization. Apply documented missing conventions only to their documented fields (`..` in classifications); do not let broad NA parsing erase valid country codes. Preserve published corridor and add `corridor_label`, e.g. United States to Mexico.

Hard rules:

- Validate published schema; reject violations with missing/unexpected fields. Require nonblank quote identity, period, provider and country codes/names; validate country code-to-name consistency in prepared data.
- Normalize transparency to lowercase yes/no; reject blanks, missing and other values without silently dropping rows.
- For every relevant numeric/date field, preserve documented missing values, but reject nonblank unparseable supplied values. Errors name column, source worksheet rows and example values. Never silently coerce malformed values to NaN/0. Retain source-row references during cleaning; nonfinite numbers are not usable observations.
- Keep valid reported costs unchanged, including negatives. Print min/max and negative-value counts for both cost columns; never trim or introduce cost thresholds.
- Verify quote-key semantics and uniqueness across all modern periods before selecting the key. In the audited release, Legend calls id “id number applied to each service”; all 204,469 rows have distinct IDs. Use opaque string `id` for this release. Only if later documentation establishes legitimate reuse, use its verified composite key; never append period to hide unexplained duplicates. Ambiguity requires team review.
- Stop for exact duplicate rows including ID or duplicate verified quote keys. Report affected/excess-row counts, keys, source rows, periods, corridors and providers. Never automatically drop or silently retain confirmed duplicates. Different valid IDs with otherwise identical service details remain separate.
- Retain non-transparent and missing-cost quotes. A non-transparent zero margin means undisclosed, not free. Access-point warnings (§6) do not stop analysis.

Write UTF-8 compressed CSV via a temporary file, validating before atomic rename. Failure must preserve prior valid output. Same workbook gives identical table content/diagnostics except labeled execution timestamps. Record source filename/fingerprint; save validation/change report beside CSV, show it at notebook startup, and explicitly pass its change/warning summary to report metadata.

`load_data` reads CSV once, preserves string IDs/codes, parses date/period_start and validates schema/types, USA-only rows, unique key, period-start agreement, country-name consistency and yes/no flags. It never reopens/cleans Excel; errors direct regeneration rather than repair.

### Release-specific regression baseline

| Check | Reference `rpw_dataset_2011_2025_q3.xlsx` |
|---|---:|
| Full modern rows / distinct IDs | 204,469 / 204,469 |
| U.S. rows | 29,542 |
| Periods; first / last | 37; `2016_2Q` / `2025_3Q` |
| Corridors / cleaned providers | 42 / 88 |
| Missing cc1 total costs | 0 |
| Transparent / non-transparent | 29,520 / 22 |
| Repeated IDs / exact duplicate rows | 0 / 0 |
| Latest four available, diagnostic only | `2024_3Q`, `2024_4Q`, `2025_1Q`, `2025_3Q` |
| USA/MEX `2025_3Q` quotes | 46 |

Direct audit verified full ID uniqueness, U.S. row count, fee currencies and access values (§6); independently verify remaining component-supplied baselines during build. Investigate same-release discrepancies rather than rewriting references to fit implementation.

New releases may change rows, periods, destinations and providers. Show a visible comparison of counts/coverage to this retained baseline; such changes are not permanent hard-count violations. For exact added/removed sets, derive/preserve membership from the reference workbook when available; otherwise disclose that comparison limitation. Hard schema, parsing, duplicate and transparency rules still apply. Latest-period default is always dynamic.

## 4. Researcher choices, startup and filtering

Startup loads the prepared table, displays available choices, loads relevance and renders the initial analysis. Defaults: latest available quarter, MEX, USD 200, default weights. Mexico is illustrative, not a recommendation. Never silently substitute if MEX is unavailable: show validation error/options. No four-period default and no automatic restore of previous sessions; saved notebook cells may retain written values.

```python
available_periods = sorted(quotes["period"].unique(), reverse=True)
periods = [available_periods[0]]
destination_codes = ["MEX"]
transfer_amount_usd = 200
```

Before choices, reject empty prepared data, missing/blank required source_code/period/destination_code/destination_name, non-USA rows, invalid period format and conflicting destination names. Display periods newest first as 2025 Q3, destinations alphabetically with codes. Allow multiple choices; an empty list means all available for that dimension. Do not assume calendar continuity (reference lacks 2025_2Q).

```python
def filter_quotes(quotes: pd.DataFrame, periods: list[str],
                  destination_codes: list[str]) -> pd.DataFrame: ...
```

Filter requires only source_code, period, destination_code; validate those fields and nonempty prepared input. Validate all requested values against full input before filtering and name every invalid selection. OR within each dimension, AND dimensions. Valid destinations absent in a chosen period yield a valid empty result.

Return `quotes.loc[mask].copy()` with a row-aligned mask, original column/row order and every input column. Never mutate inputs, read files, aggregate, rank, deduplicate, fill or filter by amount/weights/relevance. Preserve all missing costs/transparency states. Pass amount and weights to calculation. Selection/contract errors stop the run and clear/invalidate prior results; no stale export. Preparation errors direct regeneration; selection errors direct choosing displayed options.

### Separate relevance CSV

UTF-8 `inputs/community_relevance.csv`:

```csv
destination_code,relevance_rating,rationale,evidence_source,evidence_date
```

```python
def load_relevance(path: str, valid_destination_codes: set[str]) -> pd.DataFrame: ...
```

Validate against full prepared destinations, not just selection. At most one row per destination. Supplied ratings are finite numeric 0–5; dates are actual calendar dates in strict YYYY-MM-DD. Duplicate/unknown codes, blank supplied destination identity, invalid ratings and invalid nonblank dates raise clear row/field errors. Validate supplied nonblank values even if another field is incomplete.

Missing file/header-only file means no documented relevance. Missing destination or blank rating/rationale/source/date leaves it unscored with explanation but descriptive analyses continue. Complete rating 0 is valid; missing is never 0. Preserve partial evidence separately; label all relevance researcher judgment with rationale/source/date. Never invent entries or infer community relevance from quote counts: the dataset has no customer/population/firm-market-share weights.

## 5. Shared result contract

Use typed dataclasses in contracts.py; frozen wrappers do not freeze DataFrames, so consumers must leave contained tables unchanged.

```python
from dataclasses import dataclass
from pathlib import Path
import pandas as pd

@dataclass(frozen=True)
class ScoringWeights:
    cost: float = 0.50
    transparency: float = 0.25
    relevance: float = 0.25

@dataclass(frozen=True)
class AnalysisMetadata:
    selected_periods: tuple[str, ...]  # empty = all available
    selected_destination_codes: tuple[str, ...]  # empty = all available
    transfer_amount_usd: int
    weights: ScoringWeights
    matching_row_count: int
    collection_date_min: pd.Timestamp | None
    collection_date_max: pd.Timestamp | None
    validation_flags: tuple[str, ...]

@dataclass(frozen=True)
class AnalysisResults:
    corridor_summary: pd.DataFrame
    period_summary: pd.DataFrame
    channel_summary: pd.DataFrame
    provider_details: pd.DataFrame
    fee_summary: pd.DataFrame
    fx_margin_summary: pd.DataFrame
    metadata: AnalysisMetadata

def calculate_summaries(
    filtered_data: pd.DataFrame, transfer_amount_usd: int,
    relevance_inputs: pd.DataFrame, weights: ScoringWeights,
    periods: list[str], destination_codes: list[str],
    validation_flags: tuple[str, ...] = (),
) -> AnalysisResults: ...

def present_results(results: AnalysisResults) -> None: ...

def export_briefing(results: AnalysisResults, output_dir: str = "exports") -> Path: ...
```

Calculation accepts prepared names, internally mapping source_name→sending_country, destination_name→receiving_country and period→reporting_period. Group by country codes, retaining validated labels. Notebook passes exact filter selections, current amount/weights and separate validated relevance; calculation snapshots metadata. Pass preparation/change warnings explicitly and append current warnings, never use hidden DataFrame attributes.

Schema abbreviations expand to exact columns:

- Identity: `source_code,destination_code,sending_country,receiving_country` (strings).
- Measures: `median_total_cost` (numeric percent), `observations` (integer valid-cost count), `total_quotes`, `non_transparent_quotes` (integers), `non_transparent_quote_share` (0–1).

| Table | Grain and columns |
|---|---|
| corridor_summary | Matching corridor: Identity + Measures + `relevance_rating,relevance_rationale,relevance_evidence_source,relevance_evidence_date,cost_normalized,transparency_normalized,relevance_normalized,cost_weight,transparency_weight,relevance_weight,campaign_priority_score,unscored_reasons`. |
| period_summary | Matching corridor-period: Identity + `reporting_period,period_start` + Measures. |
| channel_summary | Matching corridor/category: Identity + `channel_category` + Measures. |
| provider_details | Matching quote: Identity + `service_id,provider,reporting_period,collection_date,access_point,channel_category,transparent,transfer_amount_usd,transfer_fee,fee_currency,exchange_rate_margin,total_cost_pct`. |
| fee_summary | Matching corridor/observed selected-amount currency: Identity + `fee_currency,median_transfer_fee,fee_observations`. |
| fx_margin_summary | Matching corridor/observed selected-amount currency: Identity + `fee_currency,median_exchange_margin,fx_margin_observations`; margins are percentages, currency a grouping label. |

Counts are nonnegative integers; 6.0 means 6%, shares/normalized scores 0–1. Missing numbers stay NaN/pandas NA; dates NaT; optional date bounds None; missing text nullable strings. unscored_reasons is a tuple, empty when scored. Preserve partial relevance documentation but leave incomplete relevance ineligible. Never store display labels in numeric fields.

All six tables retain complete schemas/types when empty. Zero matching quotes → six empty tables, matching count 0, no date bounds; do not invent absent corridor/period rows or zero shares. Nonempty groups with no eligible costs remain with missing median/count 0 and actual transparency. Fee/margin groups with no eligible metric retain missing median/count 0; unknown-currency groups remain separate/labeled unknown, never USD. Date bounds use nonmissing matching dates; both None if unavailable. Keep missing individual dates missing.

## 6. Calculation definitions

Validate required columns/types, amount and weights before aggregation. Empty filtered input is valid, unlike empty prepared input. Reject malformed/nonfinite supplied numeric values rather than treating them as missing or zero. Calculation opens no files and creates no charts.

### Amount, costs, transparency and currency

| Amount | Total cost % | Fee | FX margin % | Currency |
|---|---|---|---|---|
| USD 200 | cc1_total_cost_pct | cc1_lcu_fee | cc1_fx_margin | cc1_lcu_code |
| USD 500 | cc2_total_cost_pct | cc2_lcu_fee | cc2_fx_margin | cc2_lcu_code |

Reject other amounts. Never scale USD-200 costs to approximate USD-500 costs. Changing amount leaves row membership/transparency measures unchanged.

An eligible total-cost observation has transparent=yes and a nonmissing selected numeric cost. Corridor, corridor-period and corridor-channel medians/counts use exactly those eligible observations. Corridor medians pool all eligible quotes across selected periods, never median quarterly medians. Explain that periods with more eligible quotes contribute more observations; quote volume is not customer/market-share weighting. No persistence score.

For each group, total_quotes counts all matching rows; non_transparent_quotes counts flag=no; share is their quotient. Include missing-cost rows in denominator. Zero matching quotes → missing share; a nonempty all-transparent group has true share 0. Corridor share enters scoring; period shares support historical charts.

For fee and margin independently, use transparent rows with that specific metric nonmissing, reporting its own count; do not require valid total cost. Group by actual selected-amount currency and never pool currencies. Verify before labeling: all 29,542 audited U.S. quotes have USD in both currency fields, but preserve any other currency without conversion. Margins use documented percent units. Never imply median fee + median FX margin equals median total cost: units/observation sets differ and medians are not additive.

Provider details map id→service_id, firm→provider, date→collection_date, plus selected metric fields. Retain every matching quote. Mask non-transparent margin/total cost as missing in this result copy only; display “Unknown—non-transparent” regardless of raw zero/other values. Preserve reported fee with actual currency even for non-transparent quotes. Transparent missing metrics display “Unknown—missing value”; a missing fee is always unknown, never 0. Visible non-transparent fees do not enter transparent-only fee aggregates.

### Channels

Split access_point on commas; trim/collapse whitespace, compare case-insensitively against verified source vocabulary, preserve original prepared text in details. Do not invent aliases. Counter tokens: Agent, Bank branch, Post Office branch. Internet is the Internet token. Call Center is a recognized other token; verify any additional documented vocabulary against actual source before accepting it.

| Category | Rule |
|---|---|
| Internet-only | Internet present, no counter token. |
| Counter-only | Counter token present, no Internet. |
| Mixed | Internet plus a counter token. |
| Other/unknown | Neither, missing/blank access, or ANY unexpected token. |

Unexpected tokens override recognized tokens for the entire quote. Warn without stopping analysis; flags name each unexpected token and distinct affected-quote count. Repeated token within a quote counts once; multiple unknown tokens can each count that quote in warnings, but summaries count it once. Missing/blank access gets a separate warning/count. These quotes remain eligible for corridor cost/transparency and belong to neither main channel comparison group. Show all observed categories; main comparison is side-by-side Internet-only versus Counter-only median costs/counts, without double-counting Mixed/Other.

Directly audited U.S. access values/counts: Agent 9,390; Bank branch,Call Center 296; Internet 18,207; Bank branch,Internet 123; Agent,Call Center 163; Bank branch 451; Agent,Internet 547; Agent,Call Center,Internet 26; Call Center 339. Baseline category counts: Internet-only 18,207; Counter-only 10,300; Mixed 696; Other/unknown 339; sum 29,542. These are release-specific checks, not fixed future counts.

### Explainable scoring and ranking

Exactly three components, all higher=greater campaign priority: pooled median cost, non-transparent quote share, documented relevance. Provider/channel/trend evidence contributes no additional scoring component.

```text
valid_costs = all nonmissing selected corridor medians
cost_normalized = (median_total_cost - min(valid_costs)) / (max(valid_costs) - min(valid_costs))
transparency_normalized = non_transparent_quote_share
relevance_normalized = complete_documented_relevance_rating / 5
campaign_priority_score = cost_weight * cost_normalized
                        + transparency_weight * transparency_normalized
                        + relevance_weight * relevance_normalized
```

Cost min/max includes all selected valid-cost corridors, even without relevance. If valid medians are all equal (including one corridor), their normalized costs are 0; missing remains missing. No valid medians means no normalized costs. Preserve negative medians.

Default weights 0.50 cost, 0.25 transparency, 0.25 relevance. Allow researcher changes, requiring finite nonnegative values summing to 1 (only floating-point tolerance 1e-9). Reject invalid weights without auto-normalizing. Require all three components even with a zero component weight; missing component means missing final score, never fill/redistribute.

Explain in notebook/export that normalization is relative to the selected comparison set, so scores may change when selected corridors change. Show raw cost/share/relevance, normalized component scores, weights, final score and documented rationale/source/date (documentation can be an adjacent keyed table).

Sort scored corridors by full-precision score descending, then destination name/code alphabetically. Unscored follow all scored, alphabetically by the same keys. List every applicable exact reason: `Missing median cost`, `Missing transparency share`, `Missing documented community relevance`. Incomplete documentation counts as missing relevance. Do not rank rounded values. Period rows sort by corridor and chronological quarter. Consumers preserve supplied ranking, never rerank by median cost.

## 7. Presentation and briefing

Render from the same current AnalysisResults, without recomputing, regrouping, reranking, filling or filtering:

1. Purpose; selected periods/destinations (empty lists = “All available”); amount/weights/matching count; actual collection-date range; preparation change summary and validation flags. Distinguish survey quarters, collection dates and export timestamp.
2. Priority ranking with median cost/valid count, transparency count/denominator/share, researcher relevance, normalized components/weights/final score/unscored reasons, and supporting relevance documentation.
3. Currency-specific fee and margin tables with explicit units and their own counts.
4. Selected-period median-cost and non-transparent-share charts, one labeled series per corridor. Shared chronological period axis, available points marked, missing/no-quote corridor-periods left as gaps; do not connect across gaps. No smoothing/interpolation/zero fill. One point implies no direction. Axis alignment is rendering, not analytical aggregation.
5. Channel evidence with all observed categories; retain the four-category legend, identify absent categories as no observations without fabricated medians. No causal/customer-weighted claims.
6. Complete service-level provider table with agreed unknown labels. Do not aggregate services or silently truncate exported evidence.
7. Limitations: historical sampled quotes, changing survey composition, quote counts not customers/market shares, pooled-quarter weighting, selection-relative normalization, documented subjective relevance, and checking current prices/community relevance before publishing. Do not claim improvement or automatically recommend a corridor without supporting evidence; staff decide.

Use pandas/IPython display and static Matplotlib. Leave minor styling/wording to the builder. Clear prior displays and close/replace figures on reruns and errors. Metadata matching_row_count=0 displays `No matching quotes` with current settings/warnings; omit empty tables/charts. Quotes without eligible costs retain transparency/provider evidence and an explicit cost-unavailable explanation. Never leave stale results exportable.

Export validates schemas (ValueError lists every missing column), writes UTF-8 standalone HTML only on explicit cell/function action, creates exports/ if needed and returns actual Path/local link. Unique filename, e.g. remitright_briefing_20261016_183400.html, including collisions in one second; never overwrite. Use pathlib/datetime/io/base64/html; escape dynamic text, embed PNGs as base64, close figures. Include the same settings, evidence, charts, warnings and order as notebook. No external assets, network request, automatic sharing or additional reporting engine. Empty/partially missing results still export a useful current briefing. HTML opens offline and prints readably to PDF in a browser.

## 8. Build order and acceptance checks

Build environment/contracts, preparation/loading and diagnostics first; test filtering alone; add relevance validation/calculation with fixtures; then presentation/export and notebook wiring. Each piece passes its checks before integration. Supply README commands and actionable errors. Run tests and a notebook smoke run, inspect representative HTML offline and print preview. Record real results/discrepancies; do not claim tests passed without executing them.

### Preparation/loading

Independently compare current-release references with raw modern-sheet counts. Check ID uniqueness across all periods, currencies, types, 37 quarters and absent 2025_2Q. Independently count USA/MEX 2025_3Q (baseline 46). New-release reports show changed counts/coverage and dynamic latest default.

Fixtures: exact repeated row fails; repeated verified key with otherwise different fields fails; different valid IDs with identical details survive. Error includes duplicate counts/keys/source rows and leaves old output intact. Malformed numeric/impossible date fails with column/rows/examples; genuine missing stays missing; valid negative and true zero survive; native/text dates agree. Blank/unknown transparency fails. Same workbook yields identical table content. Loader rejects corrupt schema/types/period starts, reads no Excel.

### Filtering

All rows have USA and consistent destination names:

| Row | Period | Destination | Transparent |
|---|---|---|---|
| A | 2025_1Q | MEX | yes |
| B | 2025_3Q | PHL | no |
| C | 2024_4Q | MEX | yes |
| D | 2025_3Q | IND | yes |

| Period list | Destination list | Expected |
|---|---|---|
| [2025_3Q] | [MEX,PHL] | B |
| [2025_3Q] | [] | B,D |
| [] | [MEX] | A,C |
| [] | [] | A,B,C,D |
| [2025_1Q,2025_3Q] | [MEX,PHL] | A,B |
| [2025_1Q] | [PHL] | Empty, original schema |

Reject empty prepared data, missing/blank required values, malformed period, non-USA rows and conflicting destination names at their owning boundary. Name all invalid selections. Preserve B and missing-cost rows, all input columns/order and unchanged input frames/lists. Amount change does not change rows. Reference initial latest quarter is 2025_3Q, MEX, USD 200; a later available quarter dynamically replaces the initial period.

### Calculation/relevance

Transparent USA, USD-200 fixture with consistent IDs/labels and all required fields:

| Destination | Period | Cost % |
|---|---|---:|
| MEX | 2024_1Q | 4 |
| MEX | 2024_1Q | 6 |
| MEX | 2024_2Q | 8 |
| IND | 2024_1Q | 3 |
| IND | 2024_1Q | 5 |
| IND | 2024_2Q | missing |

Expected corridor cost/count: Mexico 6%/3, India 4%/2. Period rows: India Q1 4%/2; India Q2 missing/0, retained with total 1/share 0; Mexico Q1 5%/2; Mexico Q2 8%/1. Retention supersedes the original missing-group omission. Without relevance both remain unscored, India before Mexico alphabetically. With complete synthetic test-only relevance 3 for each and all quotes transparent, normalized costs Mexico 1/India 0 give scores 0.65/0.15, Mexico first. Never prefill researcher inputs with these fixture ratings.

Also test:

- Distinct cc1/cc2 costs/fees/margins switch correctly; unsupported amount fails. Independent missing metrics give their own counts; non-USD labels preserved, mixed currencies never pooled.
- Four quotes/two no flags/one missing cost give non-transparent count 2/share 0.5 independent of amount. Two all-non-transparent quotes give total 2/share 1, missing cost/score, observations 0, retained details. Nonempty all-yes gives share 0. Empty filtered input gives six complete empty schemas, matching count 0, no date bounds.
- Quarter costs [1,1,1] and [9] give pooled median 1, not 5; quarterly medians remain 1/9.
- Medians 4/6/8 normalize 0/0.5/1; equal 6/6 normalize 0/0; missing stays missing. Share 0.2 remains 0.2, relevance 3→0.6. Include valid-cost corridors lacking relevance in min/max.
- Components (0.8,0.2,0.6) with default weights give 0.60. Valid adjusted weights use exact formula; negative/nonfinite/non-unit weights fail. Missing component leaves score missing even if its weight is zero, no redistribution.
- Missing relevance file/entries/blank documentation do not block descriptive results; documented 0 is valid. Duplicate/unknown codes, rating 6/nonnumeric rating and impossible/malformed dates fail. Partial evidence remains visible but unscored.
- Equal scores sort destination name then code; unscored last with all reasons; higher score can outrank higher cost.
- Internet→Internet-only; Agent→Counter-only; Internet,Agent→Mixed; Call Center→Other/unknown without unexpected-token warning. Internet,Unexpected→Other/unknown with warning; blank/missing access warns. Distinct affected counts, no double-counting; baseline category counts match §6.
- Same provider's distinct services stay separate. Non-transparent zero margin/reported cost display required unknown status while fee/currency stays visible. Transparent missing metrics stay missing. No caller mutation.

### Presentation/export/integration

Verify initial latest-period/Mexico/USD-200/default-weight view with explicit missing-relevance status when no CSV exists. Show every promised feature, active settings and dates. Two-period fixture cost chart: India Q1 4%, Q2 gap; Mexico Q1 5%, Q2 8%. Transparency points match shares. Single-period charts show markers without directional claims. Consumers do not rerank/regroup shuffled inputs. Missing required columns raise errors naming each one.

Notebook/report match ranking, numbers, counts, units, documentation, warnings and service rows; missing values never become zero. Empty/error reruns clear old output; no stale exports. Consumers work independently without invoking preparation/filter/calculation and leave bundle unchanged. Same-selection/same-second exports have distinct paths. HTML exists, escapes researcher text, embeds nonempty charts where data permits, has no external images, opens offline and prints readably. Empty result exports current settings/no-matching message.

After loading the prepared U.S. data once, benchmark two selections: the default latest-quarter/Mexico/USD-200 view and all available periods/destinations at USD 200. For each selection, run filter, calculation and notebook rendering five times without rereading files. Target a median end-to-end response time of at most 2 seconds for each selection on the test laptop. Record the laptop specifications, prepared DataFrame memory use, each timing and the median. Report startup loading and explicit HTML export times separately; the 2-second target excludes both. If the target is missed, report the bottleneck and improve the responsible piece while preserving the calculation contracts and complete evidence. Retain full exported evidence rather than silently truncating for speed. Pass numerical/data checks before styling polish.

## 9. Completion review

Review all eight equally weighted criteria before handoff: (1) specific user/decision/concrete uses; (2) every use has inputs/views; (3) principles/pipeline precede precise rules; (4) compact definitions without conflicting duplicates; (5) independent pieces/contracts; (6) laptop-sized single-load workflow/cloud plan; (7) verified fields and explicit quality/edge checks; (8) standalone access/setup/defaults/build order/numerical acceptance tests. Walk through with only this prompt and dataset repository; report remaining guesses. Specification review alone does not validate the future implementation.
