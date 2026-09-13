# Role 5: Technical Path

## Download results

The existing `dataset_wb-remittance-prices` repository was used without cloning it again. Following Section 4, Route B was run from that repository:

```powershell
uv run python download_data.py
```

The script reached World Bank Data Catalog record `0037898` and downloaded both required files: **2 downloaded, 0 skipped, 0 failed**, with exit code 0. Both files returned `checksum ok`, matching the repository's expected release. The workbook download took 5.8 seconds and the PDF 0.8 seconds.

Files remain in `C:\Users\ediso\dso576\dataset_wb-remittance-prices\data`. Downloaded data must not be committed; Section 4 states that this repository's `.gitignore` excludes `data/`.

## File formats and sizes

| Filename | Format | Actual size | Approximate size |
|---|---|---:|---:|
| `rpw_dataset_2011_2025_q3.xlsx` | Excel workbook | 50,762,620 bytes | 48.4 MiB |
| `RPW_main_report_and_annex_Q325.pdf` | PDF report | 3,213,221 bytes | 3.1 MiB |

Combined size is 53,975,841 bytes, approximately 51.5 MiB. The script labels these binary-based sizes as MB.

## Opening/verification results

The workbook opened successfully with pandas and the openpyxl engine. The initial verification used pandas 3.0.5 and openpyxl 3.1.5. All six sheet names were accessible:

- `Terms of Use`
- `Methodology`
- `Legend`
- `Countries`
- `Dataset (up to Q1 2016)`
- `Dataset (from Q2 2016)`

Both main data sheets were read fully with `dtype=str` and Section 4's column ranges. Dimensions exclude the header row.

| Sheet | Read settings | Rows | Columns | Unique period values |
|---|---|---:|---:|---:|
| `Dataset (from Q2 2016)` | `usecols="A:AP"` | 204,469 | 42 | 37 |
| `Dataset (up to Q1 2016)` | `usecols="A:AO"` | 49,491 | 41 | 17 |
| `Countries` | `skiprows=1` | 215 | 6 | Not checked |

The modern sheet's median `cc1 total cost %` was **5.04**, calculated using `pd.to_numeric(..., errors="coerce")` followed by `.median()`. These results match Section 4.

The `Countries` sheet, also read with `dtype=str`, contains these columns:

- `ISO 3166-1 alpha-3 country code`
- `Country name`
- `Region`
- `Income Group`
- `Lending category`
- `G8/G20`

The PDF opened successfully with pypdf. It contains exactly **32 pages, including the cover**, is not encrypted, and yielded extractable text on all 32 pages. A subsequent visual inspection of the cover confirmed that it says "Issue 54, September 2025." The remaining pages were checked programmatically, not visually.

Both downloaded files had identical SHA-256 hashes before and after opening verification. The workbook hash also remained unchanged after the additional Section 4 calculations. No downloaded files were modified or converted to CSV.

## Problems or blockers

- Initial download and verification commands encountered a sandbox permission error accessing uv's cache. The same commands succeeded with approved elevated access. This was a local permission issue, not a World Bank download failure.
- No HTTP errors, timeouts, checksum failures, or Excel/PDF reader warnings occurred in the successful runs. No remaining blocker prevented reading the files.
- Full Excel reads were slow, consistent with Section 4. No formal performance benchmark was recorded.
- Programmatically extracted first-page PDF text includes "Issue 49, March 2024." The visible cover says "Issue 54, September 2025," matching the expected Q3 2025 report. The older extracted text therefore appears to be stale underlying PDF text, not evidence that the wrong report was downloaded. The downloaded PDF checksum matched the expected file.
- Section 4 warns that the modern sheet has five additional unlabeled columns outside `A:AP`. Verification used the documented range. It also advises explicit numeric conversion because some numbers are stored as text.

## Relevant technical options

These are preliminary investigation candidates from the assignment, not validated product selections. No external product research or final architecture decision is included.

| Option | Question to investigate |
|---|---|
| CSV | Can UTF-8 copies of each data sheet provide sufficient speed and reproducibility? Section 4 recommends this next step. |
| Parquet | Would a derived Parquet version improve read time, storage size, or type handling compared with CSV? |
| PostgreSQL | Does the intended workload require shared SQL access, joins, controlled updates, or concurrent use that justifies database setup? |
| Supabase | If PostgreSQL is warranted, would Supabase fit the team's hosting and access requirements? Confirm capabilities and constraints before adopting it. |
| Streamlit | Would a small interactive interface help the intended audience explore the verified data? Establish the audience and required interactions first. |
| Google Cloud/Gemini | Is there a concrete cloud or language-model task that supports the project question? Check usefulness, costs, access, and output verification before considering use. |

## Technical considerations for the two audiences

### Audience A — IFAD program officer

The verified remittance-price data can support corridor-level cost analysis using pandas and flat files, with Streamlit as a possible later interface for interactive comparisons. Open technical question: Which corridor-level cost measures and filters would best support IFAD program prioritization?

### Audience B — CHIRLA campaign researcher

The remittance data can identify high-cost U.S.-origin corridors, but auxiliary data would be needed to connect those corridors to specific immigrant communities. Census/ACS country-of-birth data would only be a proxy and does not show actual remittance behavior. Open technical question: What auxiliary data could validate the corridor-to-community links relevant to CHIRLA?

## Flat files vs PostgreSQL

The two main sheets contain **253,960 data rows** in total. Row count alone does not establish a need for PostgreSQL. Before deciding, the team should check:

- Representative filters, aggregations, and joins; measure runtime and memory on available machines.
- Whether work involves read-only analysis or shared updates, and how many people need simultaneous access.
- Schema differences between the 42-column modern sheet and 41-column legacy sheet, candidate keys, missing values, and numeric conversion rules.
- How quarterly releases would be acquired, versioned, validated, and compared without changing original downloads.
- Whether database maintenance, access management, and backup requirements are justified by the planned use.

A small comparison using derived files is a reasonable next experiment, consistent with Section 4's CSV guidance. It is not a final storage decision.

## Course tools/packages that may help

Tools directly used or described in Section 4 are:

- **Python standard library and `download_data.py`:** catalog lookup and downloading; SHA-256 checks support file integrity verification.
- **uv:** runs Python with the packages needed for a verification session.
- **pandas and openpyxl:** read Excel sheets, apply explicit column ranges, convert selected numeric fields, and calculate verification statistics.
- **pypdf:** used in this verification to open the report and extract page text; it is not specified by Section 4.

Further package choices for Parquet, database access, interfaces, or Gemini should follow the selected experiment and confirmed course requirements. No additional packages were installed to prepare this report.

## Recommended next investigation

1. PDF cover verification is complete: the visible cover confirms Issue 54, September 2025, matching the expected Q3 2025 report.
2. Agree on a question and a small set of representative queries for each of the two audiences.
3. In a separately authorized step, create UTF-8 CSV derivatives as Section 4 describes, retaining the original workbook. Compare row counts and verification statistics, then measure read time and memory. Consider Parquet as a separate comparison if useful.
4. Review schema compatibility, data types, and refresh requirements before testing PostgreSQL or related services.

No cloud accounts, deployments, model training, or Git/GitHub operations were performed for this report. Recommendations remain preliminary.
