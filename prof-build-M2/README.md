# RemitRight LA

A local notebook for CHIRLA researchers preparing a “know what you really pay” campaign briefing. Compare historical U.S. remittance corridors, inspect fees and undisclosed margins, document community relevance, and export the exact analysis as standalone offline HTML. Staff choose priorities; the tool makes no automatic recommendation.

## Local dashboard (no Jupyter required)

Windows PowerShell, one command per line:

```powershell
cd C:\Users\nr_pr\dso576\project-dashboard\prof-build-M2
uv sync --locked
uv run streamlit run streamlit_app.py --server.address 127.0.0.1 --browser.gatherUsageStats false
```

On macOS/Linux, first change into the build folder:

```bash
cd /path/to/project-dashboard/prof-build-M2
uv sync --locked
uv run streamlit run streamlit_app.py --server.address 127.0.0.1 --browser.gatherUsageStats false
```

Open the printed local URL (normally http://127.0.0.1:8501). Stop with Ctrl+C.
No Jupyter server, notebook execution, kernel, live API or raw-workbook preparation
is needed. The validated committed data loads once per browser session; start a
new session after rebuilding it. The notebook remains available through the
instructions below and retains its original three-component calculations.

### Select, then update

The sidebar identifies destinations as receiving countries; origin is USA.
Empty country or period lists mean all available values. USD 200/500 selects
the transfer-cost basket. Defaults remain Mexico, latest available quarter,
USD 200, **Community campaign priority** and weights 0.50/0.25/0.25.
Click **Update analysis** beside the main selections to apply them. The compact
saved-results summary always describes the executed analysis, not pending
controls. Complete requested/resolved selections, exact weights and collection
dates remain available in **Complete executed settings** and HTML exports.
A failed update clears the results display and blocks export.

### Explicit scoring modes

- **Community campaign priority** (startup default): unchanged normalized cost,
  non-transparent quote share and documented community relevance. Defaults are
  0.50/0.25/0.25. Incomplete evidence leaves the score unavailable when community
  weight is positive; descriptive evidence remains visible.
- **Cost & disclosure** (explicit choice): existing normalized cost and existing
  non-transparent quote share, with exact floating-point defaults `2/3`, `1/3`,
  and zero community weight. Community evidence is not required or included in
  this score; any supplied valid evidence remains available separately.

Applicable weights appear outside **Advanced scoring settings**. Weights express
relative importance in the selected score, not sender fees. Each must be between
0 and 1 and their sum must equal 1 within absolute tolerance `1e-9`. Arbitrary
inputs are never normalized or redistributed. Switching modes explicitly restores
that mode's defaults. Exact weights are stored independently of display rounding.

Higher scores reflect higher relative sampled costs and/or more quotes flagged
non-transparent; community mode also includes documented relevance. This is not
an automatic campaign or provider recommendation. The expanded component table
shows each value, weight and contribution. Missing positive-weight components
leave the score unavailable. A zero-weight missing component contributes zero
while its component value remains unavailable.

Relative cost continues to use the **selected comparison set**, selected periods
and basket. Fewer than two valid corridor medians leave it unavailable. Equal
valid medians normalize to zero, not zero actual cost. CR-04/shared normalization
is not implemented. Warnings describe current results; general methodology is
kept separately in named expandable sections.

### Community evidence

Open **Community evidence** and download its header-only CSV template. It has
`destination_code,relevance_rating,rationale,evidence_source,evidence_date`.
Use the existing 0-5 rating field and strict YYYY-MM-DD dates; no new rating rubric
or inferred rating is supplied. Use the project CSV, upload a CSV, or explicitly
choose **No community evidence**. Click **Load community evidence**, then
**Update analysis**. Uploaded previews are not applied evidence. Loading status
is visible outside the expander; the executed evidence snapshot is shown with
saved results. Uploads remain in memory and never replace the project CSV.

The header-only default (or an absent optional project file) preserves unavailable
relevance. Partial valid evidence is descriptive even when it cannot support a
score. Invalid files show validation errors and are never applied; correct/load
them or explicitly load the no-evidence choice to continue. Mode never changes
automatically when evidence is missing.

### Read results and inspect evidence

The main comparison prioritizes country names, actual median total cost, eligible
cost counts, flagged/total counts and percentages, score and availability. Expanded
views retain exact underlying numeric values and technical fields. Unknown and
unavailable values remain distinct from genuine zeros.

Corridor medians pool eligible quotes across selected quarters. Quarterly charts
calculate each quarter separately; the pooled median is not the average of
quarterly medians. Quarters with more eligible quotes contribute more observations.
Counts are sampled quotes, not customers, transaction volumes or market-share
weights.

The cost chart identifies countries and basket. Hover provides country, quarter,
actual cost percentage and eligible quote count. **Start at zero** is initial;
**Focus on variation** affects only the chart view. Negative costs remain visible
below zero. Quarterly points are retained with fewer tick labels; a single
observation stays a point, not evidence of a trend. The disclosure trend remains
available with a percentage axis; it has not been hidden or replaced.

Gaps distinguish **No survey data** (absent globally), **Not selected** (available
but excluded) and destination/metric-specific **No data**. They remain gaps,
never interpolated or filled with zero. Expanded quarterly details show their
classifications. A zero disclosure share means no sampled quote was flagged,
not proof that the entire market was transparent.

Channels retain Internet-only, Counter-only, Mixed and Other/unknown. Eligible
counts accompany medians; positive samples of five or fewer eligible cost quotes
receive a small-sample warning calculated from current results. The expandable
channel country/category drill-down affects only that evidence view and includes
quarter counts/medians and provider records. Different services and periods are
not a causal switching experiment or a best-channel recommendation.

Fees state currency explicitly; FX margins are percentages. Each retains its own
observation count. Separately calculated medians cannot simply be added to
reproduce median total cost, even after unit conversion.

Provider evidence starts with the most recent selected quarter and collection
date, then provider/country/service ID. Literal search and selectable field/direction
sorting affect only that table. All matching rows remain accessible; there is no
silent truncation or change to analytical eligibility. Technical identifiers and
exact values are expandable. Dates omit unnecessary midnight timestamps.

### Offline briefing and verification

Click **Create HTML briefing**, then **Download HTML briefing**. The existing
exporter writes a unique local file under `exports/`. It includes executed mode,
exact weights, selections, applied evidence, score status, explanations, complete
provider rows and embedded static charts. Static cost charts use a zero-inclusive
scale; disclosure axes show percentages. No external chart resources or internet
connection are required to open the file. View-only search, sort, drill-down and
interactive scale choices do not alter the complete analysis export.

Changing mode, applicable weights, selections or applied evidence blocks stale
exports/downloads until results match. Invalid inputs or failed updates also block
export. Already downloaded files are static and are not updated by later analyses.

```powershell
uv run pytest -q
uv run pytest -q tests/test_dashboard.py tests/test_dashboard_improvements.py
uv run python scripts/smoke_notebook.py
```

Checks cover controls, exact mode defaults, evidence upload/validation, conditional
warnings, contributions, gap types, negative-cost scales, small channel samples,
empty results and stale-export protection. Historical-data compatibility checks
compare every result table/metadata with the original notebook workflow: Mexico
2025 Q3 USD 200 median 4.485%; MEX + PHL Mexico normalized cost 1; all destinations
approximately 0.314598. An independent CSV cross-check also covers MEX + ARM with
all available periods. These fixed historical checks are not requirements for
future data releases. Automated tests do not establish visual usability.

Deferred: the proposed disclosure-trend replacement, CR-04/shared reference,
a new relevance-rating rubric, and other teammates' requests. No hosting,
deployment, external community data or automatic recommendations are included.

## Start from a fresh clone

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then run these commands from the cloned repository. No environment activation is needed.

macOS (zsh):

```zsh
uv run pytest
uv run jupyter lab analysis.ipynb
```

Windows (PowerShell):

```powershell
uv run pytest
uv run jupyter lab analysis.ipynb
```

JupyterLab prints a local browser URL; open `analysis.ipynb` there and stop the server with Ctrl+C when finished.

The committed condensed USA data and validated preparation report are ready for startup. Launching via `uv run` uses this project's Python kernel. Run cells in order. Startup validates the pair and parses CSV once; interactions use the in-memory table. No live API is called. Default: latest available survey quarter, Mexico (MEX), USD 200 and weights 0.50/0.25/0.25. Mexico is illustrative, not a recommendation.

Edit and **execute** the researcher choices cell, then rerun analysis. Empty selection lists mean all available values; there is no cost threshold. Choose exactly one of USD 200 or 500. The two price baskets switch together. No previous session settings are restored. Change `provider_preview_rows` to control the notebook-only preview (default 100); exported HTML always includes every matching service row.

`inputs/community_relevance.csv` contains only a header. Supply your own destination code, 0–5 rating, rationale, evidence source and strict YYYY-MM-DD evidence date. Explicitly rerun the relevance load line after edits. Missing/partial entries keep the relevance component unavailable; descriptive evidence remains useful. No community characteristics are inferred or prefilled.

To export, set `export_requested = True` in the export cell and execute it. It refuses invalid or changed executed inputs until analysis succeeds again, and shows the resulting local file link. Each UTF-8 HTML is unique, contains embedded charts and all provider rows, opens offline and can print to PDF. Never share before checking current prices and community relevance. Editing a cell without executing it does not change notebook state.

## Rebuild the data

The dataset repository is read-only. Clone it as a sibling if absent:

```bash
git clone https://github.com/USC-DSO-576-PS/dataset_wb-remittance-prices.git ../dataset_wb-remittance-prices
uv run python ../dataset_wb-remittance-prices/download_data.py
uv run python src/prepare_data.py --input ../dataset_wb-remittance-prices/data/rpw_dataset_2011_2025_q3.xlsx --output data/rpw_usa_clean.csv.gz
uv run pytest
uv run jupyter lab analysis.ipynb
```

The downloader writes beside itself and prints the actual downloaded filename; explicitly substitute a newer path in `--input`. Never silently select a workbook. If download fails, follow the dataset repository's browser instructions. Keep any app-local raw workbook downloads in git-ignored `data/raw/`. This build used the supplied nested clone `./dataset_wb-remittance-prices/` for documentation and the official catalog's complete-workbook link, saving to `data/raw/rpw_dataset_2011_2025_q3.xlsx`. It did not modify the dataset repo.

With no CLI arguments preparation uses the sibling baseline path above. It reads only `Dataset (from Q2 2016)`, A:AP, initially as strings, audits all modern service IDs, and retains USA records. Undocumented columns and the older sheet are excluded. Empty fields stay missing; the classification marker `..` remains the documented “not applicable” value. All supplied malformed numerics/dates and invalid transparency flags fail with worksheet row references. Negative costs remain. No deduplication, imputation, trimming or thresholds are applied.

Preparation writes deterministic gzip CSV and `<output>.validation.json` transactionally. The report contains fingerprints, validation and retained-baseline comparisons. Preparation supports an optional `data/reference_membership.json` for exact reference added/removed comparisons. The available workbook has the reference filename and matches all count checks, but its SHA-256 differs from the dataset repository’s reference checksum. No checksum-verified reference workbook was available, so this build discloses the limitation rather than claiming exact reference membership comparisons. New-release differences are visible, not permanent count restrictions. Schema/parsing/duplicate rules remain strict.

Startup is read-only: incomplete transactions, corrupt/missing artifacts or mismatched fingerprints stop loading. It lists valid backup pairs and exact commands, such as:

```bash
uv run python src/prepare_data.py --check-recovery <transaction-directory> --output <output-path>
uv run python src/prepare_data.py --recover <transaction-directory> --output <output-path>
```

First check the specific pair, then explicitly recover it. Neither startup nor preparation chooses between recovery directories. Preserve recovery artifacts until successful recovery. Missing source workbooks require an explicit download/preparation command, never automatic startup preparation.

## Implementation and validation

Python 3.11+; isolated uv environment and lockfile. pandas calculations, openpyxl preparation, static Matplotlib, IPython display and JupyterLab. Contracts are in `src/contracts.py`; preparation/loading, filtering, relevance/calculation, presentation and export are separate modules. `analysis.ipynb` orchestrates them through `NotebookSession`. No component reads notebook globals or mutates caller tables. One explicit additional metadata field, `available_periods`, carries the globally available quarter universe so rendering can distinguish “No survey data” from “Not selected” without guessing from filtered quotes.

The optional standalone `scripts/benchmark.py` uses Linux `/proc` and `resource` diagnostics; the app and tests do not import it.

Run `uv run python scripts/audit_workbook.py <explicit-workbook>` for independent streaming baseline diagnostics (raw audit output stays in `data/raw/`; exact reference membership is saved only if the reference checksum matches). Run `uv run python scripts/benchmark.py` for five in-memory default/all-selection timings, startup, full export and memory measurements. `uv run python scripts/smoke_notebook.py` executes the notebook into ignored `artifacts/`. Results and limitations are recorded in `BUILD_REPORT.md`.

Historical sampled quotes are not guaranteed live prices. Quarter medians pool eligible quotes; quote counts are not customers/market shares. Cost normalization depends on the selected comparison set and needs at least two valid corridor medians; equal medians normalize to zero while actual costs remain visible. Positive-weight components are required. Missing zero-weight components contribute zero without redistribution. Relevance is documented subjective researcher judgment. Channel differences are descriptive, not causal; a single time point implies no direction.

Data: **Remittance Prices Worldwide, World Bank Group**, [official catalog](https://datacatalog.worldbank.org/search/dataset/0037898/Remittance-Prices-Worldwide), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Adaptation: whitespace normalization, typed fields, USA subset and derived analysis. No personal member data. Everything stays local.

A future cloud version could prepare validated data at deployment, load once per process and isolate each user's settings/results, with web tables and HTML downloads around unchanged calculation contracts. No cloud deployment is part of this build.
