import numpy as np
import pandas as pd
import pytest

from src.contracts import (
    NUMERIC,
    PREPARED,
    RELEVANCE,
    PreparationMetadata,
    ScoringWeights,
    period_start,
)
from src.notebook_workflow import NotebookSession


def _selection_quotes():
    cases = [
        ("mex-current-a", "Provider A", "2025_3Q", "MEX", "Mexico", 2.0, "2025-08-10"),
        ("mex-current-b", "Provider B", "2025_3Q", "MEX", "Mexico", 4.0, "2025-08-11"),
        ("ind-current", "Provider C", "2025_3Q", "IND", "India", 100.0, "2025-08-12"),
        ("mex-old", "Provider D", "2025_1Q", "MEX", "Mexico", 80.0, "2025-02-10"),
    ]
    records = []
    for service_id, provider, period, code, name, cost, date in cases:
        row = {column: None for column in PREPARED}
        row.update(
            id=service_id,
            period=period,
            source_code="USA",
            source_name="United States",
            destination_code=code,
            destination_name=name,
            firm=provider,
            access_point="Internet",
            transparent="yes",
            date=pd.Timestamp(date),
            period_start=period_start(period),
            corridor="USA" + code,
            corridor_label="United States to " + name,
        )
        for column in NUMERIC:
            row[column] = np.nan
        row.update(
            cc1_lcu_amount=200.0,
            cc1_lcu_fee=cost,
            cc1_fx_margin=cost / 2,
            cc1_total_cost_pct=cost,
            cc1_lcu_code="USD",
            cc2_lcu_amount=500.0,
            cc2_lcu_fee=cost * 2.5,
            cc2_fx_margin=cost / 2,
            cc2_total_cost_pct=cost,
            cc2_lcu_code="USD",
        )
        records.append(row)
    quotes = pd.DataFrame(records)
    for column in NUMERIC:
        quotes[column] = pd.to_numeric(quotes[column]).astype(float)
    return quotes


def _preparation_metadata():
    return PreparationMetadata(
        1,
        "fixture.xlsx",
        "0" * 64,
        "fixture.csv.gz",
        "1" * 64,
        pd.Timestamp("2026-01-01", tz="UTC"),
        ("fixture",),
        (),
        (),
    )


def test_notebook_session_applies_period_and_destination_filters():
    quotes = _selection_quotes()
    session = NotebookSession(quotes, _preparation_metadata())

    results = session.analyze(
        ["2025_3Q"],
        ["MEX"],
        200,
        ScoringWeights(),
        pd.DataFrame(columns=RELEVANCE),
        provider_preview_rows=10,
    )

    assert results.metadata.matching_row_count == 2

    details = results.provider_details.set_index("service_id")
    assert set(details.index) == {"mex-current-a", "mex-current-b"}
    assert len(details) == 2
    assert set(details.destination_code) == {"MEX"}
    assert set(details.reporting_period) == {"2025_3Q"}
    assert details.total_cost_pct.to_dict() == pytest.approx(
        {"mex-current-a": 2.0, "mex-current-b": 4.0}
    )

    for table_name in (
        "corridor_summary",
        "period_summary",
        "channel_summary",
        "provider_details",
        "fee_summary",
        "fx_margin_summary",
    ):
        assert set(getattr(results, table_name).destination_code) == {"MEX"}

    assert set(results.period_summary.reporting_period) == {"2025_3Q"}

    for table_name in ("corridor_summary", "period_summary", "channel_summary"):
        table = getattr(results, table_name)
        assert len(table) == 1
        assert table.iloc[0].median_total_cost == pytest.approx(3.0)
        assert table.iloc[0].observations == 2
        assert table.iloc[0].total_quotes == 2

    assert results.channel_summary.iloc[0].channel_category == "Internet-only"
