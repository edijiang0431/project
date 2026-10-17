# Present Results

## 1. Job

Display the calculation outputs in the analysis notebook so a CHIRLA campaign researcher can compare selected remittance corridors and inspect total-cost trends.

This component presents existing results only. It does not filter quotes, calculate measures or scores, infer missing values, or export a briefing.

## 2. Inputs

The component receives the two pandas DataFrames returned by `calculate_summaries(filtered_data)`.

**Input 1: Corridor Summary**

| Column | Required | Definition |
|---|---:|---|
| `sending_country` | Yes | Sending country |
| `receiving_country` | Yes | Receiving country |
| `median_total_cost` | Yes | Median total cost (%) |
| `observations` | Yes | Number of valid total-cost observations |
| `median_transfer_fee` | No | Median visible transfer fee |
| `median_exchange_margin` | No | Median exchange-rate margin |

Rows arrive ranked by `median_total_cost` descending, with alphabetical corridor tie-breaks.

**Input 2: Period Summary**

| Column | Required | Definition |
|---|---:|---|
| `sending_country` | Yes | Sending country |
| `receiving_country` | Yes | Receiving country |
| `reporting_period` | Yes | Reporting period |
| `median_total_cost` | Yes | Median total cost (%) |
| `observations` | Yes | Number of valid total-cost observations |

Rows arrive sorted by corridor and reporting period in chronological order.

Presentation validates the required columns before rendering and raises a `ValueError` listing missing columns. It does not repair, regroup, rerank, or mutate either input.

## 3. Notebook Views

Render these views in order whenever the calculation outputs change:

1. **Corridor ranking table.** Show sending country, receiving country, median total cost, and valid observation count in the calculation-provided order. Show `median_transfer_fee` and `median_exchange_margin` only when the respective column exists; preserve missing values as unknown rather than displaying zero.
2. **Total-cost trend chart.** Plot `reporting_period` on the horizontal axis and `median_total_cost` on the vertical axis, with one labeled line per sending-country and receiving-country pair. Preserve the calculation-provided chronological order. A corridor with one period appears as a single point; do not imply a trend direction from it. Build one shared x-axis from the reporting periods in chronological year-quarter order, and show a marker for every available corridor-period, including corridors with only one period.

Use readable country labels and percentage labels for percentage measures. Include observation counts in the table so the researcher can judge how much evidence supports each median. Keep styling and exact wording simple and accessible.

The initial notebook view uses the summaries produced from the Filter Data component's initial selections: latest available period, Mexico (`MEX`), and USD 200. Because that selection includes only one period, the chart initially shows one point, not a trend. The researcher must select multiple periods to see change over time. This component does not own or silently change those selections.

## 4. Empty and Missing Results

- If both summary inputs are empty, clear any prior output and display a single no-results message; do not leave stale tables or charts visible.
- If the corridor summary is empty, do not render a ranking table.
- If the period summary is empty, do not render an empty chart.
- If an optional corridor metric is absent, omit its column. If it is present but missing for a row, display it as unknown, never as zero.
- Do not drop a corridor merely because an optional fee or margin is missing.

The agreed inputs do not distinguish an empty filtered selection from a nonempty filtered table with no valid total-cost observations. Therefore this component cannot reliably promise the exact message `No matching quotes`; it can only report that no summary results are available unless the upstream contract adds a filtered-row count or status.

## 5. Contract Gaps Against the Vision

Do not build the following promised views from the current calculation outputs because their required fields or measures are not provided:

| Vision promise | Missing agreed output |
|---|---|
| Provider table flagging unknown margins or non-transparent services | Provider/service identifier and a transparent-or-margin-missing measure |
| Transparency trend | Period-level transparency measure and denominator |
| Internet-versus-counter comparison | Service-channel field and channel-level summary |
| Relevance and weighted scoring with explainable rankings | Relevance measure, scoring weights, component scores, and final score |
| Collection-date display | Collection date or date range |
| Display of active transfer amount and complete filter settings | Selection metadata is not passed with the two summaries |

These are upstream contract gaps, not presentation defaults. Add the necessary agreed calculation outputs before adding the corresponding views.

There is also a naming mismatch between components: Filter Data specifies `period` and destination-code/name fields, while Calculate Summaries proposes `reporting_period`, `sending_country`, and `receiving_country`. Presentation consumes the Calculate Summaries names above; the team must reconcile the filter-to-calculation interface upstream.

## 6. Technical Design

Expose a notebook-facing function:

```python
def present_results(
    corridor_summary: pd.DataFrame,
    period_summary: pd.DataFrame,
) -> None:
    """Validate and render the current summary table and trend chart."""
```

Use pandas for table selection and display, and Matplotlib (`matplotlib.pyplot`) for the chart. Matplotlib is used because this is a static chart that can render directly in the notebook; no interactive plotting backend is needed. Keep both DataFrames in memory because they are already aggregated and small. Close or replace the previous figure when rerun so repeated filter changes do not accumulate stale charts or consume unnecessary memory. The project environment must include `matplotlib`; use the standard static notebook display.

For a later cloud version, pass the same summary records to a web table and chart component. Keep calculation definitions upstream so changing the interface does not change the measures.

## 7. Checks

Use the sample outputs in `04-calculate.md`.

**Expected ranking table order**

1. United States → Mexico: median total cost 6.0%, 3 observations.
2. United States → India: median total cost 4.0%, 2 observations.

**Expected chart points**

- United States → India: 2024 Q1 = 4.0%.
- United States → Mexico: 2024 Q1 = 5.0%, then 2024 Q2 = 8.0%.

Also verify:

- Optional fee and exchange-margin columns appear only when supplied, and missing cells are not shown as zero.
- Shuffling the input is not silently reranked or regrouped by presentation.
- Missing required columns raise a `ValueError` naming every missing column.
- Empty inputs remove prior displays and show no table or chart.
- A one-period corridor is displayed as one point without a claimed direction.
- Calling the function leaves both input DataFrames unchanged.

## 8. Done When

- The notebook shows the corridor ranking and total-cost trend described above whenever fresh summaries are supplied.
- The sample table order, chart points, and observation counts match the expected values.
- Empty and partial optional data render without stale results, fabricated zeros, or unsupported views.
- Every displayed value can be traced directly to one of the two agreed calculation outputs.
