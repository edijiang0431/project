# RemitRight LA

A local notebook for CHIRLA researchers preparing a “know what you really pay” campaign briefing. Compare historical U.S. remittance corridors, inspect fees and undisclosed margins, document community relevance, and export the exact analysis as standalone offline HTML. Staff choose priorities; the tool makes no automatic recommendation.

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
