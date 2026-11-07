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

The complete prepared subset loads at startup. Raw workbook downloads and the separate dataset repository are not needed on the host. The community CSV is header-only until staff supply documented evidence; descriptive analysis and Cost & disclosure do not require those ratings.

Credit: Remittance Prices Worldwide, World Bank Group, CC BY 4.0. Adaptation includes whitespace normalization, typed fields, USA filtering and derived summaries.

## Streamlit Community Cloud settings

- Repository: `edijiang0431/project`.
- Branch: `feature/mvp-change-requests`.
- Main file: `prof-build-M2/streamlit_app.py`.
- Python: 3.14.
- Dependencies: the host recognizes `prof-build-M2/uv.lock` beside the entrypoint. Root `requirements.txt` is exported from that same frozen lockfile for reproducibility and course packaging.
- Viewing access must allow anyone with the link without signing in; the repository can remain private.

See [implementation notes](MVP_CHANGE_REQUESTS.md), [change requests](change-requests.md) and [detailed app instructions](prof-build-M2/README.md).
