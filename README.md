# RemitRight LA

An interactive Streamlit dashboard for CHIRLA campaign researchers comparing historical U.S.-origin remittance services. It helps staff assess quoted costs, pricing non-disclosure and supporting evidence when considering a “know what you really pay” outreach campaign. Staff decide priorities; the dashboard does not recommend a provider or infer community needs.

## Dashboard and deployment status

The complete tested version is on `feature/mvp-change-requests`, with entrypoint `prof-build-M2/streamlit_app.py`. Cost & disclosure is the default; documented community-informed scoring is optional. No community ratings are invented.

The code is ready for Streamlit Community Cloud, but no public dashboard URL has been verified yet. Deployment is waiting for an authorized Streamlit sign-in and repository access. The live link must be added here after deployment, then verified without signing in. The team demo-video link and root `validation.pdf` are also required for the final MVP submission and are not supplied by this deployment preparation.

## Run on a laptop

Use Python 3.14 to match the tested environment. From the repository root:

```bash
cd prof-build-M2
uv sync --locked
uv run streamlit run streamlit_app.py --server.address 127.0.0.1 --browser.gatherUsageStats false
```

Open the local URL shown by Streamlit. No Jupyter server or notebook execution is required. Run `uv run pytest -q` from the same build folder to execute the tests.

## Data scope

The app reads the committed prepared CSV and validation report under `prof-build-M2/data/`: 29,542 modern U.S.-origin service quotes across 37 available survey periods and 42 destination corridors. The source is the World Bank Remittance Prices Worldwide Q3 2025 release. The older sheet and non-U.S. origins are excluded. Results therefore describe these U.S.-origin surveyed services; they are not global estimates, customer counts or live prices.

The complete prepared subset loads at startup. Raw workbook downloads and the separate dataset repository are not needed on the host. The researcher-rating CSV remains header-only until staff supply documented evidence. An optional, separate ACS community-size proxy is now bundled; descriptive analysis and Cost & disclosure do not require either source.

### Optional ACS community-size evidence

In **Community evidence**, choose **ACS community-size proxy**, click **Load community evidence**, select **Community campaign priority**, then **Update analysis**. Cost & disclosure remains the default. Nothing is downloaded during dashboard startup.

The source is the Census Bureau's [2020–2024 ACS 5-year Table B05006 for Los Angeles County](https://data.census.gov/table/ACSDT5Y2024.B05006?g=050XX00US06037). The app shows country-of-birth estimates, 90% margins of error, the county denominator and exact matched categories. This is potential audience-size evidence, not actual remittance participation, CHIRLA membership or assessed campaign need. It does not establish that ACS is the best evidence for every campaign decision.

The transparent scoring rule is `rating = 5 × country-born population estimate / all county foreign-born residents`. Existing scoring divides the rating by 5, recovering the population share. The fixed county denominator avoids changes when countries are filtered. This linear rule is a project design choice, not a Census rating; it does not propagate uncertainty into composite scores. Missing matches stay unavailable. China uses the separately published category excluding Hong Kong and Taiwan. South Sudan has no separate category and is not replaced by Sudan. Period/geographic differences from national quarterly remittance prices remain limitations.

Preparation is separate from loading: from `prof-build-M2`, run `uv run python -m src.prepare_acs` to rebuild deterministically from the saved official source row and labels. Add `--refresh` to download them again. The source row, retrieval date and official URLs are saved in `inputs/acs_b05006_la_source.json`; derived evidence is `inputs/acs_b05006_la.csv`. The official summary file is streamed only until the county row is found, avoiding the Census API's key requirement. The applied evidence snapshot carries the source, survey period, estimates, margins of error and formula into exports.

Credit: Remittance Prices Worldwide, World Bank Group, CC BY 4.0. Adaptation includes whitespace normalization, typed fields, USA filtering and derived summaries.

## Streamlit Community Cloud settings

- Repository: `edijiang0431/project`.
- Branch: `feature/mvp-change-requests`.
- Main file: `prof-build-M2/streamlit_app.py`.
- Python: 3.14.
- Dependencies: the host recognizes `prof-build-M2/uv.lock` beside the entrypoint. Root `requirements.txt` is exported from that same frozen lockfile for reproducibility and course packaging.
- Viewing access must allow anyone with the link without signing in; the repository can remain private.

See [implementation notes](MVP_CHANGE_REQUESTS.md), [change requests](change-requests.md) and [detailed app instructions](prof-build-M2/README.md).
