# Export Briefing

## 1. Job

Create a shareable briefing for a CHIRLA campaign researcher from the **current** RemitRight LA analysis. The briefing records the researcher's selections, corridor cost ranking, observation counts, and cost-over-time chart so staff can discuss which remittance corridor merits further outreach research.

This component only formats and saves existing results. It does not read raw quotes, filter data, calculate statistics, rank corridors, or recommend a campaign target automatically. Run it only when the researcher explicitly requests an export.

## 2. Inputs and Contract

Receive the two DataFrames returned by `calculate_summaries(filtered_data)` and the notebook's current selections:

```python
def export_briefing(
    corridor_summary: pd.DataFrame,
    period_summary: pd.DataFrame,
    periods: list[str],
    destination_codes: list[str],
    transfer_amount_usd: int,
    output_dir: str = "exports",
) -> pathlib.Path:
    """Write one self-contained HTML briefing and return its path."""
```

**Corridor summary:** required columns `sending_country`, `receiving_country`, `median_total_cost`, `observations`; optional columns `median_transfer_fee`, `median_exchange_margin`. Rows are already ordered by descending median cost, then alphabetically by corridor.

**Period summary:** required columns `sending_country`, `receiving_country`, `reporting_period`, `median_total_cost`, `observations`. Rows are already ordered chronologically within each corridor.

These columns and definitions come from `04-calculate.md`; the export must not change them. The notebook explicitly passes the same `periods`, `destination_codes`, and `transfer_amount_usd` used for the current analysis. Do not read notebook globals or retrieve selections from a previous run. The selected transfer amount must be USD 200 or USD 500, as specified in `03-filter.md`.

An empty selection list means **all available** periods or destinations, not none. Display that selection as "All available" instead of suggesting that nothing was selected. The export receives no scoring weights, collection dates, provider identifiers, or channel summaries under the current contract; do not invent those fields or report unsupported results.

## 3. Briefing Content

Write one standalone HTML document with these sections, in this order:

1. **Title and context:** "RemitRight LA — CHIRLA Remittance Cost Briefing," an export timestamp, and the purpose: support a review of U.S.-origin remittance corridor costs for possible outreach.
2. **Analysis settings:** selected reporting period(s), destination code(s), and transfer amount in USD. Use readable quarter labels (for example, `2025_3Q` becomes `2025 Q3`). Clearly distinguish the export timestamp from the reporting periods; never call it the quote collection date.
3. **Corridor ranking:** a table showing sending country, receiving country, median total cost (%), and valid observation count in the supplied order. Add median visible transfer fee and median exchange-rate margin only when their optional columns are present. Show missing metric values as "Unknown," not zero.
4. **Total-cost trend:** one labeled Matplotlib line per corridor with reporting period on the x-axis and median total cost (%) on the y-axis. Use a shared chronological period axis and plot a marker for every available corridor-period observation. For a corridor with only one observed period, show one point without claiming an increasing or decreasing trend. Embed the image in the HTML so the report opens without separate chart files.
5. **Interpretation and limitations:** explain that a larger median total cost indicates a more expensive observed set of quotes, but does not alone establish the best campaign target; observation counts show how much evidence supports each median. State that the data represents historical survey quotes, not current guaranteed provider prices, and that staff should check current prices and community relevance before publishing or choosing outreach priorities.

Use a concise, neutral narrative. Do not generate an unsupported claim that costs or transparency improved, or that any provider has undisclosed margins. Do not name a "recommended" corridor unless an upstream recommendation and its rationale are added to the agreed contract.

## 4. Missing and Empty Results

- Validate the four required corridor fields and five required period fields before writing. Raise `ValueError` listing missing columns; do not guess their equivalents or silently repair data.
- If both summaries are empty, export the settings and a clear "No summary results available for the current selection" message; omit the ranking table and trend chart. Do not include stale results from a prior selection.
- If just one summary is empty, omit only its corresponding table or chart and explain that those results are unavailable.
- Missing optional columns are omitted; present optional columns with missing cells display "Unknown." Never substitute 0.
- Keep the original DataFrames and selection lists unchanged. Do not reorder, recalculate, fill, or drop their rows.
- If the same export filename already exists, generate a unique filename rather than silently overwriting it.
- The current summary contract does not distinguish zero matching quotes from matching quotes with no valid total-cost observations. Use the neutral no-summary message rather than asserting "No matching quotes."

## 5. Technical Design

Implement `export_briefing` in `src/export_briefing.py`. Use pandas only to read and format the small aggregate tables, Matplotlib to make the same type of static trend figure described in `05-present.md`, and the Python standard library (`pathlib`, `datetime`, `io`, `base64`, `html`) to write the standalone HTML file. Escape dynamic text inserted into HTML. Render the chart to an in-memory buffer, embed it as base64, and close its Matplotlib figure after use.

Create `exports/` if needed, and save a uniquely named file such as `remitright_briefing_20261016_183400.html`. Return the actual `Path`; the notebook shows the saved location or a clickable file link. Only export when the user runs the export cell or calls the function, not on every filter change. The function must never initiate a download or publish personal data; all outputs stay local unless the researcher chooses to share them.

No additional reporting engine or network access is required. The HTML file remains readable offline and can be printed to PDF in a browser. For a future cloud version, reuse the same explicit inputs and render the HTML server-side or offer it as a download; never recompute analytical measures in the export layer.

## 6. Checks

Use the synthetic calculation outputs in `04-calculate.md`, also used by `05-present.md`:

| Corridor | Median total cost | Valid observations |
|---|---:|---:|
| United States → Mexico | 6.0% | 3 |
| United States → India | 4.0% | 2 |

The exported table must retain that order. The embedded chart must show India at `2024 Q1 = 4.0%`, Mexico at `2024 Q1 = 5.0%`, and Mexico at `2024 Q2 = 8.0%`. Use selections `periods=["2024_1Q", "2024_2Q"]`, `destination_codes=["MEX", "IND"]`, and `transfer_amount_usd=200`; the briefing must display all three correctly.

Also verify:

- The returned path exists and contains a valid standalone HTML document with a nonempty embedded chart image, without referring to an external image path.
- The ranking numbers, observation counts, period labels, and chart points match the supplied DataFrames and the notebook display.
- A one-period selection shows chart markers without inventing a trend direction.
- Missing optional columns disappear; missing optional values appear as "Unknown."
- Empty summary inputs create a current, useful no-results briefing without stale tables or figures.
- Missing required columns raise a `ValueError` naming each missing column; invalid transfer amounts are rejected.
- Two exports made with the same selections produce distinct files without overwriting one another.
- Calling the function does not change either input DataFrame or either selection list.

## 7. Build Order and Done When

1. Implement input validation and the explicit `export_briefing(...)` interface.
2. Create the local HTML report with title, timestamp, selections, and ranking table.
3. Generate and embed the static trend chart from `period_summary`.
4. Add interpretation, data limitations, and empty-result behavior.
5. Run the synthetic checks above, open the file offline, and verify that browser printing produces a readable report.
6. Connect the notebook's export action to the function using the same calculation outputs already passed to `present_results`.

**Done when:** One explicit export action creates a self-contained, readable briefing of the current selections, with the exact supplied figures and chart, correct missing-data handling, no fabricated measures, and an existing returned file path. The export must work independently of the display function and without re-running preparation, filtering, or calculation.

## 8. Connection to Other Components

**Filter Data (`03-filter.md`)** owns the current period and destination selections; the notebook additionally holds the transfer amount. **Calculate Summaries (`04-calculate.md`)** supplies the two validated summary DataFrames. **Present Results (`05-present.md`)** displays these results in the notebook. **Export Briefing (`06-export.md`)** writes the same results to a reusable report only on demand.

Before integration, the team must reconcile the upstream naming mismatch noted in `05-present.md`: Filter Data uses `period` and destination-code/name fields, while Calculate Summaries specifies `reporting_period`, `sending_country`, and `receiving_country`. Export consumes the Calculate Summaries contract and must not work around that mismatch by guessing. Additional transparency, channel, relevance, or weighted-scoring sections require explicit upstream outputs before they can appear in the briefing.
