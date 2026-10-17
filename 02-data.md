# Data loading and cleaning

## Design

Use Python with `pandas`, `openpyxl` and `matplotlib`. Manage the environment with `uv`.

The data workflow has two pieces:

| Piece | Receives | Returns | Must not do |
|---|---|---|---|
| `prepare_data.py` | World Bank Excel workbook | Cleaned compressed CSV | Display views or respond to user controls |
| `load_data.py` | Cleaned CSV path | Validated pandas DataFrame | Reopen or clean the Excel workbook |

Each view receives the loaded DataFrame and typed settings. A view returns either a table or a Matplotlib figure without opening files or changing another view.

## A. Prepare the data — `src/prepare_data.py`

### Source

Use the workbook downloaded by the sibling `dataset_wb-remittance-prices` repository.

Download it once:

```bash
cd ../dataset_wb-remittance-prices
uv run python download_data.py
```

The preparation script reads only the modern data sheet:

```python
pd.read_excel(
    workbook_path,
    sheet_name="Dataset (from Q2 2016)",
    usecols="A:AP",
    dtype=str,
)
```

Reading `A:AP` excludes five undocumented columns beyond the published 42-column schema.

One row represents one provider’s remittance service in one corridor during one survey period. A provider can have multiple rows because its services may use different payment instruments, access points, speeds or pickup methods.

### Rows

Keep only rows where `source_code` equals `USA`. The prepared data should contain 29,542 U.S.-origin quotes from `2016_2Q` through `2025_3Q`.

Do not use `Dataset (up to Q1 2016)`. It has an older structure, while the project vision uses recent periods from the modern sheet.

Do not remove rows based only on repeated firm or corridor values. Check and report repeated IDs and exact duplicate rows before writing the output.

### Columns and types

Convert column names to lowercase snake case. Examples include:

- `payment instrument` → `payment_instrument`
- `access point` → `access_point`
- `speed actual` → `speed_actual`
- `cc1 total cost %` → `cc1_total_cost_pct`
- `receiving network coverage` → `receiving_network_coverage`
- `pickup location` → `pickup_location`
- `pickup method` → `pickup_method`
- `Standard Note` → `standard_note`

Apply these types:

- Keep `id`, country codes, currency codes and `corridor` as strings.
- Convert amounts, fees, exchange rates, FX margins and total-cost percentages to numbers.
- Convert `date` to a date, handling both text dates and Excel date cells.
- Keep `period` as text.
- Add `period_start`, using the first day of the quarter so periods sort correctly.
- Preserve missing numeric values as missing rather than replacing them with zero.

### Text and labels

Strip leading and trailing spaces and collapse repeated internal spaces in text columns.

Normalize `transparent` to lowercase `yes` or `no`. Stop with a clear error if another nonblank value appears.

Preserve provider capitalization after whitespace cleaning.

Replace `..` with a missing value in country classification columns.

Keep the published `corridor` value. Add `corridor_label` from the country names, such as:

```text
United States to Mexico
```

### Costs and transparency

Use `cc1_total_cost_pct` as the cost of sending the $200-equivalent amount. Keep `cc2_total_cost_pct` for the $500-equivalent amount.

Keep reported cost values unchanged. Print their minimum and maximum and the number below zero so unusual values can be reviewed rather than silently removed.

Keep non-transparent quotes in the prepared data. When `transparent` is `no`, a zero FX margin means the margin was not disclosed, not that it was free.

Views must calculate median costs using only rows where `transparent` equals `yes`. They must count non-transparent quotes separately.

### Output

Write the prepared data as UTF-8 to:

```text
data/rpw_usa_clean.csv.gz
```

Write to a temporary file first and rename it only after validation succeeds. Add generated data files to `.gitignore`. Running the script again with the same workbook must produce the same result.

The preparation function has this contract:

```python
def prepare_data(input_path: str, output_path: str) -> None:
    """Prepare modern U.S.-origin remittance quotes and write a compressed CSV."""
```

## B. Load the data — `src/load_data.py`

Load the complete prepared dataset once when the tool starts:

```python
def load_data(path: str) -> pd.DataFrame:
    """Load and validate all prepared U.S.-origin remittance quotes."""
```

Parse `date` and `period_start` as dates and verify the required columns and allowed transparency values.

Loading all 29,542 prepared rows into pandas is appropriate for a laptop and allows user interactions to run against data already in memory. Views must not reload the CSV or Excel workbook.

For later cloud deployment, run the same preparation step during deployment and load the compressed CSV once when the application starts.

## C. Typed settings and view contracts

Keep shared settings in Python code rather than a TOML file:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    cost_column: str = "cc1_total_cost_pct"
    recent_periods: int = 4
    cost_threshold: float = 5.0
    transparent_value: str = "yes"
```

A view follows this contract:

```python
from matplotlib.figure import Figure


def build_view(
    data: pd.DataFrame,
    settings: Settings,
) -> pd.DataFrame | Figure:
    """Return one table or figure without opening files or changing the screen."""
```

User choices such as destination, sorting method and selected corridor are passed to the appropriate view rather than stored as hidden global state.

## Build order and checks

Build and verify the data pieces in this order:

1. Download the workbook.
2. Build and run `prepare_data.py`.
3. Compare its output with the expected counts.
4. Build `load_data.py`.
5. Load the prepared file and check its columns and types.
6. Pass a small DataFrame to each view before connecting it to the interface.

Run the preparation script from the project root:

```bash
uv run python src/prepare_data.py
```

The preparation piece is done when it reports:

| Check | Expected result |
|---|---:|
| Rows | 29,542 |
| Available periods | 37 |
| First period | `2016_2Q` |
| Last period | `2025_3Q` |
| Corridors | 42 |
| Cleaned provider names | 88 |
| Missing `cc1_total_cost_pct` | 0 |
| Transparent quotes | 29,520 |
| Non-transparent quotes | 22 |
| Repeated IDs | 0 |
| Exact duplicate rows | 0 |

The latest four available periods must be:

```text
2024_3Q
2024_4Q
2025_1Q
2025_3Q
```

The code must select the latest four available values rather than assuming every calendar quarter exists.
