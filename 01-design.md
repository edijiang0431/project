## 3. Divide the Work

We divided the project into five components, with each team member responsible for one part. Each component has a clear job, input, output, and Markdown file.

**Piece 1: Prepare Data**
- File: `02-prepare.md`
- Owner: Kanishk
- Job: Load and clean the raw remittance dataset, convert cost columns to numeric values, and produce a prepared quote table.
- Runs: Once during data preparation.

**Piece 2: Filter Data**
- File: `03-filter.md`
- Owner: Nicharee
- Job: Filter the prepared data based on the researcher's selected countries, reporting periods, and transfer amount.
- Runs: Whenever the researcher changes the filters.

**Piece 3: Calculate Summaries**
- File: `04-calculate.md`
- Owner: Edison
- Job: Use Python and pandas to calculate median total costs, observation counts, and corridor-level and period-level summaries.
- Runs: Whenever the filtered data changes.

**Piece 4: Present Results**
- File: `05-present.md`
- Owner: 
- Job: Display corridor rankings, summary tables, and cost trends in the notebook.
- Runs: When the tool starts and whenever results change.

**Piece 5: Export Briefing**
- File: `06-export.md`
- Owner: 
- Job: Generate a briefing containing the selected settings, summary statistics, charts, and explanations.
- Runs: When the researcher requests an export.

Each team member writes and tests their assigned component independently. The components communicate through clearly defined inputs and outputs, allowing them to be combined into the final one-shot prompt.
