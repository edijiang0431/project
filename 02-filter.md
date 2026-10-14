# Filters and analysis selections — `src/filter_data.py`

The analysis notebook holds all user selections in one clearly labeled input section. Its startup step loads the prepared modern U.S.-origin quote table once per session. The notebook constructs the available choices and initial selections, then passes them to this pure pandas function imported from `src/filter_data.py` whenever the researcher changes the inputs and reruns the analysis cells:

```python
def filter_quotes(
    quotes: pd.DataFrame,
    periods: list[str],
    destination_codes: list[str],
) -> pd.DataFrame:
    """Return matching quotes without changing the inputs."""
```

The function returns a separate DataFrame with every input column in its original order and matching rows in their original relative order. It does not read files or notebook globals, group, aggregate, rank, deduplicate, fill missing values, or change its DataFrame or list inputs.

## Initial notebook selections

After validating the prepared-table contract described below, construct the initial selections:

```python
available_periods = sorted(
    quotes["period"].dropna().unique(),
    reverse=True,
)
if not available_periods:
    raise ValueError("The prepared table contains no available periods")

latest_available_period = available_periods[0]
periods = [latest_available_period]  # currently "2025_3Q"
destination_codes = ["MEX"]         # Mexico
transfer_amount_usd = 200
```

Start with the latest available quarter for a recent comparison, Mexico as a concrete initial corridor, and USD 200 as the initial transfer amount. These are starting selections, not a recommendation that Mexico is the highest-priority corridor. Researchers can change them before running the analysis.

- Build period choices from the distinct `period` values in the full prepared table, display them as readable labels such as `2025 Q3`, and order them newest first by year and quarter.
- Build destination choices from distinct (`destination_code`, `destination_name`) pairs in the full prepared table. Display names with codes, such as Mexico (`MEX`), and order them alphabetically by name.
- Allow multiple periods and destinations. An empty period or destination list means all available values for that selection.
- Allow selection of exactly one of two transfer amounts: USD 200 or USD 500, with USD 200 selected initially.
- Do not automatically save or restore selections between sessions. Saved notebook cells may retain their written values.

The notebook passes `transfer_amount_usd` directly to the calculation piece. It does not affect which rows pass this filter. The calculation piece validates the amount and owns the mapping to the corresponding `cc1` or `cc2` fields. All comparisons in a run use that same selected amount. Scoring weights also pass directly to the calculation piece and do not filter quote rows.

## Filtering and validation

Use pandas because the notebook already holds the prepared U.S.-origin table in memory. Preliminary measurement of the 29,542 U.S.-origin rows with all 42 named columns loaded as strings used approximately 17.934 MiB, supporting this in-memory approach. The final prepared table's memory use may differ.

### Prepared-table contract

Data preparation owns producing the prepared table. Validate its contract before constructing choices or filtering:

- The notebook's choice setup requires `source_code`, `period`, `destination_code`, and `destination_name`. The `filter_quotes` function requires only the three fields it reads: `source_code`, `period`, and `destination_code`.
- Both notebook choice setup and `filter_quotes` reject an empty prepared input with a `ValueError`. This is distinct from valid selections producing an empty filtered result, which is returned normally.
- Check required columns before accessing them. Raise a `ValueError` listing any missing column names.
- Required values must not be null, empty strings, or whitespace-only strings.
- Periods must match `YYYY_nQ`, where `YYYY` is a four-digit year and `n` is 1–4. Reverse string sorting is chronological for this validated format.
- Every row must have `source_code == "USA"`.
- Notebook choice setup also checks that each destination code maps to exactly one display name.

Raise a `ValueError` identifying any input-contract violation. Neither notebook choice setup nor `filter_quotes` repairs the prepared data.

### Selection rules

- Validate periods and destination codes against the full prepared input before applying either filter. Raise a `ValueError` naming every invalid selection; do not ignore it or substitute a default.
- Use `period` rather than deriving quarters from `date`.
- Within each selection, keep rows matching any selected value. Combine the period and destination conditions with AND.
- An empty period or destination list applies no restriction for that selection.
- Treat a valid destination with no quotes in a selected period as a valid empty result, not an invalid destination.
- Preserve transparent and non-transparent quotes, including rows with missing cost or FX-margin values. The calculation piece applies eligibility rules separately for each measure.
- Initialize a row-aligned mask that keeps every row, then apply each nonempty selection. Return `quotes.loc[mask].copy()` so an empty result retains the input columns and no-selection inputs still produce a separate DataFrame.

The presentation piece displays `No matching quotes` for an empty filtered result and must not display results from an earlier selection. Validation errors stop the analysis run and are displayed by the notebook. A preparation-contract error directs the team to fix preparation and regenerate the table; an invalid-selection error directs the researcher to choose from the displayed options and rerun.

Data preparation owns reading and cleaning the raw workbook and saving the prepared table. Startup loading owns reading that prepared table once per session. Filtering never reads files; calculation owns summaries and scores; presentation owns tables, charts, and messages; export owns writing the briefing. Detailed preparation and loading rules belong in their responsible piece.

## Why this design

Filtering in memory avoids repeated file reads each time notebook inputs change. A pure filtering function can be built and checked with a tiny table, while keeping calculation, presentation, and export rules independently changeable.

## Done when

Use this synthetic table. Every row has `source_code = "USA"` and a corresponding destination name.

| Row | `period` | `destination_code` | `transparent` |
|---|---|---|---|
| A | `2025_1Q` | `MEX` | yes |
| B | `2025_3Q` | `PHL` | no |
| C | `2024_4Q` | `MEX` | yes |
| D | `2025_3Q` | `IND` | yes |

| Selected periods | Selected destinations | Expected rows |
|---|---|---|
| `["2025_3Q"]` | `["MEX", "PHL"]` | B |
| `["2025_3Q"]` | `[]` | B, D |
| `[]` | `["MEX"]` | A, C |
| `[]` | `[]` | A, B, C, D |
| `["2025_1Q", "2025_3Q"]` | `["MEX", "PHL"]` | A, B |
| `["2025_1Q"]` | `["PHL"]` | Empty DataFrame with the input columns |

Also verify:

- The current prepared data resolves the initial selections to `2025_3Q`, `MEX`, and USD 200; the initial period updates automatically if a later period is added.
- For `2025_3Q` and `MEX`, compare the filtered count with an independent pandas count on the same prepared input. The current raw modern worksheet has 46 matching U.S.-origin quotes; explain any difference caused by documented preparation rules.
- Period choices appear newest first, destination choices appear alphabetically, and the notebook initially displays Mexico (`MEX`).
- An unavailable period or unknown destination code raises a `ValueError` naming the invalid selection. In the current data, `2025_2Q` is unavailable.
- Both notebook choice setup and `filter_quotes` reject an empty prepared table, missing required column, blank required value, malformed period, or non-U.S. input with a `ValueError` naming the input-contract problem.
- Notebook choice setup rejects conflicting destination-name mappings.
- Row B remains available for transparency analysis, and matching rows with missing cost values are retained.
- Changing USD 200 to USD 500 leaves the filtered rows unchanged and causes the calculation piece to recalculate with the new amount. An unsupported amount is rejected by the calculation piece.
- The input DataFrame and selection lists remain unchanged, and the output preserves the input columns and relative row order.