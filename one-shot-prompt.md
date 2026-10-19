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
| Prepare Data | `src/prepare_data.py`, startup `src/load_data.py` | Workbook → validated compressed CSV plus preparation report → in-memory prepared table plus preparation metadata. |
| Filter Data | `src/filter_data.py` | Prepared table + period/destination lists → unchanged-schema matching copy. |
| Calculate Summaries | `src/calculate_summaries.py` | Matching quotes + explicit current inputs → `AnalysisResults`. |
| Present Results | `src/present_results.py` | Result bundle → notebook tables, warnings and figures. |
| Export Briefing | `src/export_briefing.py` | Same bundle → unique standalone HTML path on explicit request. |

Shared types/schema validation live in `src/contracts.py`; relevance loading in `src/load_relevance.py`; orchestration in `analysis.ipynb`. Shared rendering helpers may draw/format existing results, never calculate measures. No function mutates caller tables/lists, reads hidden notebook globals or relies on another component's internals. Do not introduce generic Settings/build_view contracts or cost-threshold filtering.

This specification supersedes the amount-filter description in `01-design.md`: Filter Data selects periods/destinations only; Calculate Summaries owns the single run-level transfer amount (§6). Do not modify the source design document.

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

Generated files: compressed CSV, its validation/change report, transaction/recovery directories and `exports/*.html`; ignore generated data, transaction artifacts, exports and notebook checkpoints in Git. Keep relevance separate; supply only a header template, never fictional researcher entries. Outputs stay local. Future cloud plan: validated preparation at deployment, CSV loaded once per process, user-isolated settings/results, web tables/charts and HTML download around unchanged calculation contracts. No live API, database or interactive plotting backend is needed.

## 3. Prepare and load

```python
def prepare_data(input_path: str, output_path: str) -> None: ...
def load_data(path: str) -> pd.DataFrame: ...
def load_preparation_metadata(
    report_path: str, prepared_data_path: str
) -> PreparationMetadata: ...
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

Write the compressed CSV canonically so identical prepared tables produce identical bytes and SHA-256 values within the pinned environment. Preserve retained source-worksheet row order. Write columns in the exact published order listed above followed by `period_start,corridor_label`; write no index. Serialize UTF-8 CSV with `\n` line endings and a final line ending, RFC-style minimal quoting/doubled quote escaping, empty fields for missing values, dates as ISO `YYYY-MM-DD` and finite numeric values with round-trip-stable `%.17g` formatting. Do not allow locale or platform defaults to alter the bytes. Compress those canonical CSV bytes with gzip level 9, `mtime=0` and an empty original-filename header so execution time and temporary/final paths do not affect the output.

Write the deterministic CSV and its report as one transaction. The report path is `<output_path>.validation.json` (for example, `data/rpw_usa_clean.csv.gz.validation.json`). Report schema version 1 records source filename/SHA-256, prepared filename/SHA-256, UTC preparation timestamp, validation summary, baseline-change summary and preparation warnings. The timestamp exists only in the report; identical prepared tables produce identical compressed bytes and prepared SHA-256.

Stage and validate both artifacts, including their filename/fingerprint relationship, before replacement. Retain the prior valid pair in one uniquely identified transaction directory until both new final files validate. Any replacement/final-validation failure restores and revalidates the prior pair; a first-run failure leaves no ready pair. Cleanup touches only transaction-created paths. A pair is ready only when both final files exist and the report matches the CSV.

Startup is read-only. Missing/malformed/mismatched final files or an incomplete transaction stop loading without changing final or recovery files. Identify every internally valid backup pair by transaction directory, never combine pairs or choose among them, and provide these exact commands with actual paths:

```bash
uv run python src/prepare_data.py --check-recovery <transaction-directory> --output <output-path>
uv run python src/prepare_data.py --recover <transaction-directory> --output <output-path>
```

`--check-recovery` validates the chosen pair, report schema, fingerprints and intended final paths without writes. `--recover` is a separate explicit action that requires a passing check, installs only that pair transactionally and revalidates the result. Preserve recovery artifacts until success; startup invokes neither action.

At notebook startup, validate the final CSV/report pair before exposing either artifact to analysis. `load_preparation_metadata` reads the JSON report once, validates its schema/types and verifies that its prepared filename and SHA-256 match the CSV before returning `PreparationMetadata`. `load_data` parses the verified CSV once, preserves string IDs/codes, parses date/period_start and validates schema/types, USA-only rows, unique key, period-start agreement, country-name consistency and yes/no flags. A missing, malformed or mismatched final pair produces the read-only recovery error above; never reconstruct the report, repeat preparation or alter files during startup. Neither loader reopens or cleans Excel. Pass the loaded preparation metadata unchanged through the current analysis result bundle.

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

Startup loads the prepared table, displays available choices, loads relevance and renders the initial analysis. The notebook accepts exactly one transfer amount per analysis run. Defaults: latest available quarter, MEX, USD 200, default weights. Mexico is illustrative, not a recommendation. Never silently substitute if MEX is unavailable: show validation error/options. No four-period default and no automatic restore of previous sessions; saved notebook cells may retain written values.

```python
available_periods = sorted(quotes["period"].unique(), reverse=True)
periods = [available_periods[0]]
destination_codes = ["MEX"]
transfer_amount_usd = 200
```

Before choices, reject empty prepared data, missing/blank required source_code/period/destination_code/destination_name, non-USA rows, invalid period format and conflicting destination names. Display periods newest first as 2025 Q3, destinations alphabetically with codes. Allow multiple choices; an empty requested list means all values available for that dimension in the full prepared table. Do not assume calendar continuity (reference lacks 2025_2Q).

Before filtering, preserve the user's lists as `requested_periods` and `requested_destination_codes`, then create explicit `resolved_periods` and typed `resolved_destinations` from the full prepared choices and its validated one-to-one destination code/name mapping. Each resolved destination contains both `destination_code` and `destination_name`. For an empty request, use every available value; for a nonempty request, use exactly the validated selected values. Order resolved periods chronologically by year and quarter for chart axes, never by collection date, and order resolved destinations alphabetically by validated destination name then code. Do not add calendar quarters or destinations absent from the full prepared table. Pass the codes from the resolved destinations to filtering and pass both requested selections and resolved entries to calculation for metadata; presentation and export must not recover them from filtered rows, prepared data or notebook globals.

```python
def filter_quotes(quotes: pd.DataFrame, periods: list[str],
                  destination_codes: list[str]) -> pd.DataFrame: ...
```

Filter requires only source_code, period, destination_code; validate those fields and nonempty prepared input. Validate all requested values against full input before filtering and name every invalid selection. OR within each dimension, AND dimensions. Valid destinations absent in a chosen period yield a valid empty result.

Return `quotes.loc[mask].copy()` with a row-aligned mask, original column/row order and every input column. Never mutate inputs, read files, aggregate, rank, deduplicate, fill or filter by amount/weights/relevance. Preserve all missing costs/transparency states. Selection/contract errors clear prior displays and prevent stale export without replacing the stored last-successful result bundle or its input snapshot; preparation errors direct regeneration, and selection errors show valid options.

### Separate relevance CSV

UTF-8 `inputs/community_relevance.csv`:

```csv
destination_code,relevance_rating,rationale,evidence_source,evidence_date
```

```python
def load_relevance(path: str, valid_destination_codes: set[str]) -> pd.DataFrame: ...
```

Validate against full prepared destinations, not just selection. At most one row per destination. Supplied ratings are finite numeric 0–5; dates are actual calendar dates in strict YYYY-MM-DD. Duplicate/unknown codes, blank supplied destination identity, invalid ratings and invalid nonblank dates raise clear row/field errors. Validate supplied nonblank values even if another field is incomplete.

Missing file/header-only file means no documented relevance. A destination with no relevance entry, or an entry with blank rating/rationale/source/date, has an unavailable relevance component with an explanation; it is unscored only when relevance has positive weight, and descriptive analyses continue in either case. Complete rating 0 is valid; missing is never 0. Preserve partial evidence separately; label all relevance researcher judgment with rationale/source/date. Never invent entries or infer community relevance from quote counts: the dataset has no customer/population/firm-market-share weights.

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
class PreparationMetadata:
    report_schema_version: int
    source_filename: str
    source_sha256: str
    prepared_filename: str
    prepared_sha256: str
    prepared_at_utc: pd.Timestamp
    validation_summary: tuple[str, ...]
    change_summary: tuple[str, ...]
    preparation_warnings: tuple[str, ...]

@dataclass(frozen=True)
class ResolvedDestination:
    destination_code: str
    destination_name: str

@dataclass(frozen=True)
class RelevanceInputSnapshot:
    destination_code: str
    relevance_rating: float | None
    relevance_rationale: str | None
    relevance_evidence_source: str | None
    relevance_evidence_date: pd.Timestamp | None

@dataclass(frozen=True)
class AnalysisMetadata:
    requested_periods: tuple[str, ...]  # empty means the user requested all available
    requested_destination_codes: tuple[str, ...]  # same empty-list meaning
    resolved_periods: tuple[str, ...]  # explicit, available and chronological
    resolved_destinations: tuple[ResolvedDestination, ...]  # explicit and available
    transfer_amount_usd: int
    weights: ScoringWeights
    validated_relevance_snapshot: tuple[RelevanceInputSnapshot, ...]
    matching_row_count: int
    collection_date_min: pd.Timestamp | None
    collection_date_max: pd.Timestamp | None
    preparation: PreparationMetadata
    runtime_validation_warnings: tuple[str, ...]

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
    requested_periods: list[str], requested_destination_codes: list[str],
    resolved_periods: list[str],
    resolved_destinations: list[ResolvedDestination],
    preparation: PreparationMetadata,
    runtime_validation_warnings: tuple[str, ...] = (),
) -> AnalysisResults: ...

def present_results(
    results: AnalysisResults, provider_preview_rows: int = 100
) -> None: ...

def export_briefing(results: AnalysisResults, output_dir: str = "exports") -> Path: ...
```

Calculation accepts prepared names, internally mapping source_name→sending_country, destination_name→receiving_country and period→reporting_period. Group by country codes, retaining validated labels. Notebook passes the requested and resolved selections, current amount/weights, separate validated relevance and the once-loaded `PreparationMetadata`; calculation validates that filtered rows use only resolved values and agree with every matching resolved code/name entry. It records immutable value copies of requested selections, amount, weights and the validated relevance rows in metadata; canonicalize the relevance snapshot by destination code, represent every missing relevance field as `None`, and never retain caller lists or the relevance DataFrame. Together with `metadata.preparation.prepared_filename` and `prepared_sha256`, these fields are the independent successful-analysis input snapshot and cannot change if mutable notebook inputs are later edited. Do not reread or rebuild preparation information. Resolved values may legitimately have no matching filtered row. Keep `PreparationMetadata.preparation_warnings` separate from `runtime_validation_warnings`; append current access-point and analysis warnings only to the latter. Never use hidden DataFrame attributes.

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

Counts are nonnegative integers; 6.0 means 6%, shares/normalized scores 0–1. Missing numbers stay NaN/pandas NA; dates NaT; optional date bounds None; missing text nullable strings. `unscored_reasons` is a tuple, empty when every positive-weight component is available. Preserve partial relevance documentation; incomplete relevance is ineligible when relevance has positive weight but may remain missing when its weight is zero. Never store display labels in numeric fields.

All six tables retain complete schemas/types when empty. Zero matching quotes → six empty tables, matching count 0, no date bounds; preserve the resolved selections in metadata but do not invent absent corridor/period rows or zero shares. Nonempty groups with no eligible costs remain with missing median/count 0 and actual transparency. Fee/margin groups with no eligible metric retain missing median/count 0; unknown-currency groups remain separate/labeled unknown, never USD. Date bounds use nonmissing matching dates; both None if unavailable. Keep missing individual dates missing.

## 6. Calculation definitions

Validate required columns/types, amount and weights before aggregation. Empty filtered input is valid, unlike empty prepared input. Reject malformed/nonfinite supplied numeric values rather than treating them as missing or zero. Calculation opens no files and creates no charts.

### Amount, costs, transparency and currency

| Amount | Total cost % | Fee | FX margin % | Currency |
|---|---|---|---|---|
| USD 200 | cc1_total_cost_pct | cc1_lcu_fee | cc1_fx_margin | cc1_lcu_code |
| USD 500 | cc2_total_cost_pct | cc2_lcu_fee | cc2_fx_margin | cc2_lcu_code |

Calculate Summaries validates the notebook's single current amount and uses the corresponding row in this mapping consistently for total costs, fees, FX margins and currencies in all six result tables. Reject other amounts. Never mix cc1 and cc2 fields within a run or scale USD-200 costs to approximate USD-500 costs. Changing amount leaves row membership and transparency measures unchanged.

An eligible total-cost observation has transparent=yes and a nonmissing selected numeric cost. Corridor, corridor-period and corridor-channel medians/counts use exactly those eligible observations. Corridor medians pool all eligible quotes across selected periods, never median quarterly medians. Explain that periods with more eligible quotes contribute more observations; quote volume is not customer/market-share weighting. No persistence score.

For each group, total_quotes counts all matching rows; non_transparent_quotes counts flag=no; share is their quotient. Include missing-cost rows in denominator. Zero matching quotes → missing share; a nonempty all-transparent group has true share 0. Corridor share enters scoring; period shares support historical charts.

For fee and margin independently, use transparent rows with that specific metric nonmissing, reporting its own count; do not require valid total cost. Group by actual selected-amount currency and never pool currencies. Verify before labeling: all 29,542 audited U.S. quotes have USD in both currency fields, but preserve any other currency without conversion. Margins use documented percent units. Never imply median fee + median FX margin equals median total cost: units/observation sets differ and medians are not additive.

Provider details map id→service_id, firm→provider, date→collection_date, plus selected metric fields. Retain every matching quote. Calculate Summaries constructs `provider_details` with one stable ascending sort by prepared columns `destination_name`, `destination_code`, chronological `period`, `firm` and opaque string `id`, in that precedence. Parse period order by year/quarter rather than collection date or incidental string position; use a stable sorting algorithm so complete ties retain filtered input order. Then map the prepared names to result-contract names. Filter Data still preserves its input row order. Presentation takes the first `N` provider rows without sorting again, and export consumes the complete table in exactly the same order.

Mask non-transparent margin/total cost as missing in this result copy only; display “Unknown—non-transparent” regardless of raw zero/other values. Preserve reported fee with actual currency even for non-transparent quotes. Transparent missing metrics display “Unknown—missing value”; a missing fee is always unknown, never 0. Visible non-transparent fees do not enter transparent-only fee aggregates.

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
                  # only when at least two are valid and the range is nonzero
transparency_normalized = non_transparent_quote_share
relevance_normalized = complete_documented_relevance_rating / 5

weighted_component(weight, value) = 0 if weight == 0
                                    = unavailable if weight > 0 and value is missing
                                    = weight * value otherwise
campaign_priority_score = sum(the three weighted components)
```

Cost min/max includes all selected valid-cost corridors, even without relevance. Relative cost normalization requires at least two selected corridors with valid median costs. If fewer than two have valid medians, set `cost_normalized` missing for every corridor; do not treat the sole valid median as zero. No valid medians likewise means no normalized costs. If at least two corridors have valid medians and all those medians are equal, assign `cost_normalized = 0` to every corridor with a valid median; this means there is no relative cost difference within the current selection, not that actual cost is zero. Corridors with missing medians remain missing. Preserve each available raw median, including negative medians, for descriptive tables and trends.

Default weights 0.50 cost, 0.25 transparency, 0.25 relevance. Allow researcher changes, requiring every weight to be finite and nonnegative and the total to equal 1 within absolute tolerance 1e-9. Reject invalid weights without auto-normalizing.

For scoring eligibility, require a valid component value only when its weight is greater than zero. A zero-weight component contributes exactly zero and may be missing; implement this explicitly rather than relying on `0 * NaN`. If any positive-weight component is missing, leave the final score missing and list each such component as an unscored reason. In particular, when cost has positive weight and fewer than two selected corridors have valid median costs, leave the composite score unscored even for a corridor with an available raw median. When at least two valid medians are equal, their normalized zeros are valid component values, so scoring continues with the original weights and no redistribution. When cost has zero weight, unavailable relative cost is nonblocking under the same zero-weight rule as other components. Never redistribute weights. Keep missing zero-weight raw/normalized values missing so displays and exports do not imply evidence exists.

Explain in notebook/export that normalization is relative to the selected comparison set, so scores may change when selected corridors change. Also explain that positive-weight components are required, while a missing zero-weight component contributes zero without weight redistribution. Show raw cost/share/relevance, normalized component scores, weights, final score and documented rationale/source/date (documentation can be an adjacent keyed table); keep unavailable zero-weight components visibly missing.

Sort scored corridors by full-precision score descending, then use destination name and destination code, both ascending, as explicit tie-breakers. Place every unscored corridor after every scored corridor, ordered by destination name then code ascending. Use stable sorting throughout. For positive-weight components only, list every applicable exact reason: `Missing median cost`, `Relative cost unavailable: at least two selected corridors with valid median costs are required`, `Missing transparency share`, `Missing documented community relevance`. Use the relative-cost reason for a corridor with a raw median when the selected comparison set has fewer than two valid medians; use `Missing median cost` for a corridor lacking its own median. Incomplete documentation counts as missing relevance. A missing zero-weight component is not an unscored reason. Do not rank rounded values. Consumers preserve supplied ranking and never rerank by median cost.

Construct all remaining summaries with stable ascending sorts. Order `period_summary` by destination name, destination code and chronological reporting period. Order `channel_summary` by destination name/code and then the fixed category order Internet-only, Counter-only, Mixed, Other/unknown. Order `fee_summary` and `fx_margin_summary` by destination name/code, then known `fee_currency` codes alphabetically with unknown currency last. Apply currency ordering only to these two tables, where currency is part of the defined grain; never introduce currency grouping into corridor, period or channel percentage summaries merely for sorting. `provider_details` retains its separately defined stable order.

## 7. Presentation and briefing

Render from the same current AnalysisResults, without recomputing, regrouping, reranking, filling or analytically filtering. The only permitted row slice is the disclosed notebook provider preview; it does not change the result bundle:

1. Purpose; requested periods/destinations (empty requested lists display as “All available”) and their explicit resolved values; amount/weights/matching count; actual collection-date range; source/prepared fingerprints, preparation timestamp, validation/change summaries and preparation warnings from `metadata.preparation`; and separate runtime validation warnings. Distinguish survey quarters, collection dates, preparation timestamp and export timestamp.
2. Priority ranking with raw measures/counts, relevance documentation, normalized components, weights, score and unscored reasons. Display the §6 explanations for insufficient cost comparisons, equal-cost relative zeros and unavailable zero-weight components; always retain actual medians and missing values.
3. Currency-specific fee and margin tables with explicit units and their own counts.
4. Selected-period median-cost and non-transparent-share charts, one labeled series per resolved destination. Use metadata.resolved_periods as the selected analytical periods and metadata.resolved_destinations as the selected series universe. Label each series with its validated destination name and code, including destinations with no matching rows. Place periods at their actual calendar-quarter positions on a shared time axis. Between the earliest and latest resolved periods, show intervening quarters only as rendering positions; label globally unavailable quarters "No survey data" and available but unselected quarters "Not selected." These positions never enter resolved_periods, period_summary, calculations or exports of analytical tables. For each series, mark available values and break the line whenever an intervening quarter is unavailable, unselected or has no usable value for that measure. Selected quarters without usable values show a gap or "No data," never zero. Do not smooth, interpolate or zero-fill. One point implies no direction. Apply the same rendering rule in the notebook and HTML briefing.
5. Channel evidence with all observed categories; retain the four-category legend, identify absent categories as no observations without fabricated medians. No causal/customer-weighted claims.
6. Service-level provider evidence with agreed unknown labels. In the notebook, show a configurable preview of the first `provider_preview_rows` rows in the table's defined order, defaulting to 100, and label it `Showing X of Y service rows`. Explain beside the preview that the HTML export contains the complete table. Previewing is presentation-only: never slice or replace `results.provider_details`, and never let the preview limit calculations, summaries, counts, charts or export rows. The HTML export includes all `Y` matching service rows in the same defined order without aggregation or truncation.
7. Limitations: historical sampled quotes, changing survey composition, quote counts not customers/market shares, pooled-quarter weighting, selection-relative normalization, documented subjective relevance, and checking current prices/community relevance before publishing. Do not claim improvement or automatically recommend a corridor without supporting evidence; staff decide.

Use pandas/IPython display and static Matplotlib. Leave minor styling/wording to the builder. Validate `provider_preview_rows` as a positive integer; `X` is `min(provider_preview_rows, Y)`. Clear prior displays and close/replace figures on reruns and errors. Metadata matching_row_count=0 displays `No matching quotes` with current settings/warnings; omit empty tables/charts and report `Showing 0 of 0 service rows` only where the provider section is rendered. Quotes without eligible costs retain transparency/provider evidence and an explicit cost-unavailable explanation. Never leave stale results exportable.

Notebook orchestration stores an `AnalysisResults` bundle only after a successful run and retains that last-successful bundle and its immutable input snapshot independently of the mutable input variables. Before export, orchestration validates and canonicalizes the current executed requested period/destination values, transfer amount, weights and relevance inputs under the same contracts used for analysis, represents every missing relevance field as `None`, and combines them with the once-loaded prepared filename/SHA-256. Compare only these defined input-snapshot fields with their counterparts in `last_successful_results.metadata`, not `AnalysisMetadata` as a whole. Block export before calling `export_briefing` and create no file if no successful bundle exists, current inputs are invalid or the snapshots differ; explain that the researcher must rerun the analysis successfully. If they match, call `export_briefing` with only the stored result bundle. This guard reads the current in-memory executed values but no files: it does not reread the workbook or relevance input, repeat preparation or recalculate results. Calculation and export never read notebook globals. Editing an input cell changes nothing until that cell is executed, so state this beside the export control. Exclude presentation-only settings such as `provider_preview_rows` from the snapshot; changing them does not invalidate otherwise matching results.

Export validates schemas (a `ValueError` names every missing column), writes UTF-8 standalone HTML only on explicit request, creates `exports/` if needed and returns its actual Path/link. Use unique collision-safe names such as `remitright_briefing_20261016_183400.html`; never overwrite. Escape dynamic text, embed and close base64 PNG figures, and use no external assets, network requests, automatic sharing or added reporting engine. Match notebook settings, evidence, charts, warnings and order, with the complete provider table required above. Empty/partial results remain useful and the HTML opens offline and prints readably to PDF.

## 8. Build order and acceptance checks

Build environment/contracts, preparation/loading and diagnostics first; test filtering alone; add relevance validation/calculation with fixtures; then presentation/export and notebook wiring. Each piece passes its checks before integration. Supply README commands and actionable errors. Run tests and a notebook smoke run, inspect representative HTML offline and print preview. Record real results/discrepancies; do not claim tests passed without executing them.

### Preparation/loading

Independently compare current-release references with raw modern-sheet counts. Check ID uniqueness across all periods, currencies, types, 37 quarters and absent 2025_2Q. Independently count USA/MEX 2025_3Q (baseline 46). New-release reports show changed counts/coverage and dynamic latest default.

Checks:

- Exact repeated rows and repeated verified keys fail with counts, keys, source rows and context; different IDs with identical details survive and failures preserve old output.
- Malformed supplied numeric/date values fail with column/rows/examples; genuine missing, negative and zero values survive; native/text dates agree; blank/unknown transparency fails.
- Two preparations with different times and paths have identical canonical CSV content, compressed bytes and SHA-256 but may have different report timestamps. Check column/source-row order, UTF-8, `\n` plus final newline, missing/date/numeric serialization and gzip metadata.
- Loader rejects corrupt schema/types/period starts and reads no Excel. Metadata loading rejects missing/malformed reports, unsupported versions and filename/fingerprint mismatch; startup parses the verified CSV once, reads the report once and performs no preparation.
- Simulated replacement/final-validation failures restore an exact, loadable prior pair; first-run failure leaves none ready. An interruption after one replacement produces a read-only error with valid backup pairs and exact commands, chooses none and changes no recovery/final files. Check read-only `--check-recovery`, transactional `--recover`, reported failures and transaction-scoped cleanup.

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

Also reject empty prepared data, missing/blank required values, malformed periods, non-USA rows and conflicting destination names, naming all invalid selections. Preserve B, missing-cost rows, schema/order and caller inputs. USD 200/500 yield identical filtered rows. Check requested/resolved metadata, validated destination name/code pairs, and this gap case: a globally available period with no quotes for the selected destination remains in chronological `resolved_periods` and renders as a gap/“No data,” without a summary row or zero. The reference initial view is 2025_3Q, MEX, USD 200; a later period replaces it dynamically.

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

- Distinct cc1/cc2 costs/fees/margins/currencies switch together and consistently across all result tables; unsupported or multiple amounts fail. Independent missing metrics give their own counts; non-USD labels preserved, mixed currencies never pooled.
- Four quotes/two no flags/one missing cost give non-transparent count 2/share 0.5 independent of amount. Two all-non-transparent quotes give total 2/share 1, missing cost/score, observations 0, retained details. Nonempty all-yes gives share 0. Empty filtered input gives six complete empty schemas, matching count 0, no date bounds.
- Quarter costs [1,1,1] and [9] give pooled median 1, not 5; quarterly medians remain 1/9.
- Medians 4/6/8 normalize 0/0.5/1; share 0.2 stays 0.2; relevance 3→0.6; missing raw medians stay missing; valid-cost corridors without relevance remain in min/max. With fewer than two valid medians, test positive and zero cost weights and the exact reason. Equal valid medians 6/6 normalize 0/0 while actual 6% remains displayed; a missing median remains unavailable.
- Components (0.8,0.2,0.6) with defaults score 0.60. Reject negative/nonfinite weights and totals outside 1e-9. For each component, missing with positive weight prevents a score and gives its reason; missing with zero weight contributes zero, remains visibly missing and permits scoring without redistribution.
- Missing relevance file/entries/blank documentation do not block descriptive results; documented 0 is valid. Duplicate/unknown codes, rating 6/nonnumeric rating and impossible/malformed dates fail. Partial evidence remains visible, with the relevance component unavailable and the corridor unscored only when relevance has positive weight.
- Equal scores sort destination name then code; unscored last with all reasons; higher score can outrank higher cost.
- Internet→Internet-only; Agent→Counter-only; Internet,Agent→Mixed; Call Center→Other/unknown without unexpected-token warning. Internet,Unexpected→Other/unknown with warning; blank/missing access warns. Distinct affected counts, no double-counting; baseline category counts match §6.
- Same provider's distinct services stay separate. `provider_details` uses the specified destination-name/code, chronological-period, prepared `firm` and opaque-string `id` stable order; complete ties retain filtered input order. Filter output order remains unchanged, and notebook preview/export do not rerank. Non-transparent zero margin/reported cost display required unknown status while fee/currency stays visible. Transparent missing metrics stay missing. No caller mutation.
- Shuffled fixtures verify every stable table order: corridor score/tie/unscored order; period destination/chronology order; fixed channel-category order; fee/FX destination and known-currency alphabetical order with unknown last; and provider order. Currency sorting appears only in fee/FX tables and never changes the grain of percentage-only summaries.

### Presentation/export/integration

Checks:

- Initial latest/Mexico/USD-200/default-weight view shows missing relevance when `inputs/community_relevance.csv` is absent, insufficient cost comparison, and available raw cost/trend/transparency evidence, plus all active settings/dates.
- Two-period chart: India Q1 4%, Q2 gap; Mexico Q1 5%, Q2 8%; transparency points equal shares. Globally available but destination-empty periods remain gaps/“No data.” Single points imply no direction; empty results retain resolved country name/code.
- Calendar-gap fixtures: Q1 and Q3 have valid observations, while Q2 is globally unavailable: show actual quarter spacing, label Q2 "No survey data" and draw no connecting segment across it. If Q2 is globally available but unselected, label it "Not selected" and likewise break the line. Apply this per measure and in both notebook and HTML; rendering positions never add resolved periods, analytical rows or change costs, counts or scores.
- Consumers neither recompute nor reorder; missing required columns are all named. Notebook/export match ranking, values, units, documentation, preparation metadata and separately labeled runtime warnings; missing never becomes zero.
- For `Y>100`, default preview is the first 100 rows and says `Showing 100 of Y service rows`; custom valid sizes change only the slice/`X`. For `Y<100` and `Y=0`, show the actual count. Invalid sizes fail. Export contains exactly all `Y = metadata.matching_row_count` rows in the same order; previewing changes no result or other output.
- Before any successful analysis, export is blocked and creates no file.
- After a successful USD-200 run, execute an input-cell change to USD 500 and run only export: it is blocked, creates no file and instructs the researcher to rerun analysis.
- After successfully rerunning analysis at USD 500, export succeeds and both its settings and results use USD 500.
- Executed changes to weights or validated relevance inputs likewise block export until a successful rerun; mutating their notebook objects does not alter the stored snapshot. Invalid current inputs also block export without a file.
- After a successful analysis with missing or partial relevance, unchanged inputs still permit export because both snapshots represent the same missing fields as `None`.
- Changing only `provider_preview_rows` does not block export or alter the complete exported provider table.
- Error reruns clear stale displays/exports without replacing the last-successful bundle or snapshot; consumers leave the bundle unchanged. Same-second exports are distinct. HTML escapes researcher text, embeds permitted charts with no external images, works offline/print, and exports useful current settings when empty.

After loading the prepared U.S. data once, benchmark two selections: the default latest-quarter/Mexico/USD-200 view and all available periods/destinations at USD 200. For each selection, run filter, calculation and notebook rendering five times without rereading files, with the default 100-row provider preview enabled. Target a median end-to-end response time of at most 2 seconds for each selection on the test laptop; do not assume the preview alone guarantees the target. Record the laptop specifications, prepared DataFrame memory use, each timing and the median. Report startup loading and explicit full-row HTML export times separately; the 2-second target excludes both. If the target is missed, report the bottleneck and improve the responsible piece while preserving the calculation contracts and complete evidence. Retain full exported evidence rather than silently truncating for speed. Pass numerical/data checks before styling polish.
