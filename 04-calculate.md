# Calculate Summaries

## 1. Job

Calculate summary statistics from filtered remittance quotes to help a CHIRLA campaign researcher compare U.S.-origin remittance corridors and identify where transfer costs are highest.

This component focuses only on calculations. Data preparation, filtering, visualization, and exporting are handled by other components.

## 2. Inputs

The component receives a filtered pandas DataFrame from the Filter Data component.

Required fields:

| Field | Description |
| sending_country | Country where the transfer originates |
| receiving_country | Country receiving the transfer |
| reporting_period | Reporting quarter or period |
| total_cost_pct | Total transfer cost as a percentage |
| transfer_fee | Transfer fee, if available |
| exchange_rate_margin | Exchange-rate margin, if available |

The input should already contain only records matching the researcher's selected countries, reporting periods, and transfer amount.

Cost fields must be numeric. Missing values should be represented as NaN.

The field names above are the proposed interface for this component and must match the output of Filter Data.

## 3. Outputs

The component produces two pandas DataFrames.

**Output 1: Corridor Summary**

One row per sending-country and receiving-country pair.

| Column | Definition |
|---|---|
| sending_country | Sending country |
| receiving_country | Receiving country |
| median_total_cost | Median total cost (%) |
| observations | Number of valid total-cost observations |
| median_transfer_fee | Median transfer fee, if available |
| median_exchange_margin | Median exchange-rate margin, if available |

Sort by median_total_cost in descending order. Break ties alphabetically by sending_country and receiving_country.

**Output 2: Period Summary**

One row per corridor and reporting period.

| Column | Definition |
|---|---|
| sending_country | Sending country |
| receiving_country | Receiving country |
| reporting_period | Reporting period |
| median_total_cost | Median total cost (%) |
| observations | Number of valid total-cost observations |

Sort by sending_country, receiving_country, and reporting_period in chronological order.

Both outputs are passed to Present Results and Export Briefing.

## 4. Definitions and Choices

**Median total cost:** Calculate the median of valid total_cost_pct values within each group. Median is preferred over mean because it is less affected by unusually expensive quotes.

**Observation count:** Count only records with valid total_cost_pct values.

**Grouping:** Corridor Summary groups by sending_country and receiving_country. Period Summary additionally groups by reporting_period.

**Missing values:** Exclude missing or nonnumeric total costs from calculations. Do not replace missing costs with zero.

**Duplicate records:** Do not automatically remove repeated quotes. The Prepare Data component is responsible for identifying and handling duplicates.

**Optional metrics:** Calculate median transfer fees and exchange-rate margins only when their columns are available and numeric. Do not substitute zero for unavailable metrics.

**Empty inputs:** Return empty DataFrames with the expected output columns if no valid observations remain.

**Sorting:** Rank corridors by median total cost from highest to lowest. Sort reporting periods chronologically rather than alphabetically.

**Responsibility boundaries:** This component does not load raw data, change filters, generate charts, or export reports.

## 5. Technical Design

This component uses Python and pandas to calculate summary statistics from the filtered remittance data.

- **Python:** Handles calculation logic and connects the component with other notebook functions.
- **pandas:** Uses groupby(), agg(), median(), count(), and sort_values() for summary calculations.
- **Data storage:** Receives a filtered pandas DataFrame and returns two summary DataFrames. Intermediate calculations remain in memory.
- **Performance:** Recalculates summaries when filtered inputs change. Results can be reused by the visualization and briefing components.
- **Validation:** Uses small sample DataFrames with known expected results to check calculations.

The component should expose a reusable function:

`calculate_summaries(filtered_data)`

The function returns:

`corridor_summary, period_summary`

This allows other components to use the results without repeating calculations.

For local use, pandas is sufficient for the expected workflow. If the application later moves to the cloud, the same calculation logic can be reused behind an application service, subject to performance testing with the actual dataset.

## 6. Data Quality and Edge Cases

The component should handle the following cases:

1. Missing total-cost values are excluded from medians and observation counts.
2. Empty filtered datasets return valid empty outputs without errors.
3. Groups containing only missing total-cost values are excluded from reported summaries.
4. Unexpected nonnumeric cost values are flagged or rejected rather than silently treated as zero.
5. Reporting periods are ordered chronologically.
6. Optional fee or margin columns do not prevent the core cost summaries from being calculated.
7. Repeated records are handled according to the agreed upstream data-cleaning rules.

## 7. Checks

Use the following small sample to verify the calculations.

**Sample Input**

| Sending | Receiving | Period | Total Cost (%) |
|---|---|---|---|
| United States | Mexico | 2024 Q1 | 4.0 |
| United States | Mexico | 2024 Q1 | 6.0 |
| United States | Mexico | 2024 Q2 | 8.0 |
| United States | India | 2024 Q1 | 3.0 |
| United States | India | 2024 Q1 | 5.0 |
| United States | India | 2024 Q2 | Missing |

**Expected Corridor Summary**

| Corridor | Median Cost (%) | Observations |
|---|---|---|
| United States → Mexico | 6.0 | 3 |
| United States → India | 4.0 | 2 |

**Expected Period Summary**

| Corridor | Period | Median Cost (%) | Observations |
|---|---|---|---|
| United States → India | 2024 Q1 | 4.0 | 2 |
| United States → Mexico | 2024 Q1 | 5.0 | 2 |
| United States → Mexico | 2024 Q2 | 8.0 | 1 |

**Done When:**

- Median calculations match the expected values.
- Observation counts exclude missing costs.
- Corridor and period grouping produces the correct rows.
- Corridor rankings use descending median total cost.
- Reporting periods appear in chronological order.
- Empty inputs return correctly structured DataFrames.
- The function can be called independently without loading files or creating charts.

## 8. Connection to Other Components

**Previous Component: Filter Data**

Provides a pandas DataFrame containing quotes matching the researcher's selected filters.

**Current Component: Calculate Summaries**

Receives the filtered data, calculates summary statistics, and returns two DataFrames.

**Next Component: Present Results**

Uses the summary tables to create corridor comparisons, rankings, and cost-trend charts.

**Next Component: Export Briefing**

Uses the same summary tables to prepare a briefing for the campaign researcher.

This separation allows the calculation logic to be developed, tested, and updated without changing the visualization or export components.

## 9. Build Order

1. Confirm the required input columns and data types with the Filter Data component.
2. Implement the calculate_summaries() function using pandas.
3. Calculate corridor-level median costs and observation counts.
4. Calculate period-level median costs and observation counts.
5. Add optional fee and exchange-rate margin summaries if supported by the prepared data.
6. Apply sorting and missing-value rules.
7. Test the function using the sample input and expected outputs.
8. Confirm that Present Results and Export Briefing can consume the returned DataFrames.
