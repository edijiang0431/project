# Data loading and cleaning

## A. Prepare the data — `src/prepare_data.py`

Use the World Bank Remittance Prices Worldwide workbook `rpw_dataset_2011_2025_q3.xlsx`. The PDF report provides context but is not a source of data rows.

### Select the relevant data

Read these workbook sheets:

- `Dataset (from Q2 2016)`: the modern quote data.
- `Countries`: country codes and descriptive fields.
- `Legend`: definitions of the published columns.

Keep only rows where `source_code` equals `USA`. This produces 29,542 U.S.-origin quotes covering 37 available periods from `2016_2Q` through `2025_3Q`.

Do not include `Dataset (up to Q1 2016)`. Its structure differs from the modern sheet, and the project vision only uses recent periods.

### Standardize the columns

Convert column names to lowercase snake case. For example:

- `payment instrument` → `payment_instrument`
- `access point` → `access_point`
- `speed actual` → `speed_actual`
- `cc1 total cost %` → `cc1_total_cost_pct`
- `receiving network coverage` → `receiving_network_coverage`
- `pickup location` → `pickup_location`
- `pickup method` → `pickup_method`
- `Standard Note` → `standard_note`

Drop the five undocumented columns named `Unnamed: 42` through `Unnamed: 46`. They are not defined in the workbook’s legend.

Keep the documented published columns because they may provide useful details about providers, costs, transfer methods and destinations.

### Types

- Treat `id`, country codes, currency codes and `corridor` as strings.
- Convert amounts, fees, exchange rates, FX margins and total-cost percentages to numbers.
- Convert `date` to a date. Handle both text dates and Excel date cells.
- Keep `period` as text and add a sortable `period_start` date based on its year and quarter.
- Leave missing numeric values blank rather than replacing them with zero.

### Text cleaning

Strip leading and trailing spaces and collapse repeated internal spaces in all text columns.

Normalize `transparent` to lowercase `yes` or `no`. Stop and report the problem if another nonblank value appears.

Preserve provider capitalization after whitespace cleaning because company names may use intentional capitalization.

Replace the workbook’s `..` placeholder with a missing value in country classification columns.

### Corridors and countries

Keep the published `corridor` value rather than rebuilding it from the country codes.

Add a readable `corridor_label` using the source and destination names:

```text
United States → Mexico
```

Use the `Countries` sheet to check destination codes, names, regions, income groups, lending categories and G8/G20 membership. Report unmatched codes without silently deleting their quote rows.

### Costs and transparency

Keep the published costs for both transfer amounts:

- `cc1_total_cost_pct`: cost of sending the first amount, normally the $200-equivalent basket.
- `cc2_total_cost_pct`: cost of sending the second amount, normally the $500-equivalent basket.

Do not silently cap or remove negative or unusually high costs. Print their counts for review.

Keep non-transparent quotes in the cleaned data. A zero FX margin where `transparent` is `no` means that the margin is unknown, not necessarily zero.

Views that calculate median costs must use only rows where `transparent` equals `yes`. Non-transparent quotes must be counted and reported separately.

### Output and checks

Write the prepared data to:

```text
data/rpw_usa_clean.csv.gz
```

Before writing it, print:

- Input and output row counts.
- Columns found in the source sheet.
- First and last periods.
- Number of periods, corridors and firms.
- Missing values in the cost columns.
- Counts of `yes` and `no` in `transparent`.
- Repeated IDs and exact duplicate rows.
- Unmatched country codes.
- Counts of negative or unusually high costs.

The current workbook should produce:

- 29,542 rows.
- 37 available periods.
- 42 U.S.-origin corridors.
- 88 provider names.
- No repeated IDs or exact duplicate rows.
- No missing values in `cc1_total_cost_pct`.
- 29,520 transparent quotes and 22 non-transparent quotes.

Write to a temporary filename first and rename it only after all checks pass. Running the script again with the same workbook must produce the same cleaned file.

## B. Load the data — `src/load_data.py`

This piece has one job: load the prepared file and return a pandas DataFrame.

Its contract is:

```python
def load_data(path: str) -> pd.DataFrame:
    """Load and validate all prepared U.S.-origin remittance quotes."""
```

When the tool starts, call `load_data` once and load all 29,542 prepared rows into pandas. Parse `date` and `period_start` as dates and verify that the required columns exist.

Views must never open the Excel workbook or cleaned file themselves. Each view receives the loaded DataFrame and the typed settings it needs.

On each user action, the tool filters or summarizes the DataFrame already in memory. It does not reload or clean the workbook.

## C. Settings and view contracts

Keep settings in Python code rather than a TOML file. Use a typed settings object containing:

- Cost column: `cc1_total_cost_pct`
- Number of recent available periods: `4`
- Cost threshold: `5.0`
- Transparency column: `transparent`

The latest four available periods in the current data are:

```text
2024_3Q
2024_4Q
2025_1Q
2025_3Q
```

Do not assume that every calendar quarter exists.

Each view must have a clear contract similar to:

```python
def build_view(
    data: pd.DataFrame,
    settings: Settings,
) -> pd.DataFrame | matplotlib.figure.Figure:
    """Return a table or figure without reading files or changing the screen."""
```

The preparation script cleans and limits the source data once. The loader loads the complete prepared dataset once at startup. Each view receives the DataFrame, calculates one result and returns a table or Matplotlib figure.
