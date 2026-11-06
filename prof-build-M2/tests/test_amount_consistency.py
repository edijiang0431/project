import numpy as np
import pandas as pd
import pytest

from src.calculate_summaries import calculate_summaries
from src.contracts import (
    NUMERIC,
    PREPARED,
    RELEVANCE,
    PreparationMetadata,
    ScoringWeights,
    period_start,
    resolve_choices,
)


def _amount_quotes():
    prices = [
        ("service-a", "Provider A", 2.0, 1.0, 2.0, 10.0, 3.0, 5.0),
        ("service-b", "Provider B", 6.0, 2.0, 5.0, 20.0, 5.0, 9.0),
    ]
    records = []
    for service_id, provider, fee_200, margin_200, cost_200, fee_500, margin_500, cost_500 in prices:
        row = {column: None for column in PREPARED}
        row.update(
            id=service_id,
            period="2025_3Q",
            source_code="USA",
            source_name="United States",
            destination_code="MEX",
            destination_name="Mexico",
            firm=provider,
            access_point="Internet",
            transparent="yes",
            date=pd.Timestamp("2025-08-15"),
            period_start=period_start("2025_3Q"),
            corridor="USAMEX",
            corridor_label="United States to Mexico",
        )
        for column in NUMERIC:
            row[column] = np.nan
        row.update(
            cc1_lcu_amount=200.0,
            cc1_lcu_fee=fee_200,
            cc1_fx_margin=margin_200,
            cc1_total_cost_pct=cost_200,
            cc1_lcu_code="USD",
            cc2_lcu_amount=500.0,
            cc2_lcu_fee=fee_500,
            cc2_fx_margin=margin_500,
            cc2_total_cost_pct=cost_500,
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


def _analyze(quotes, amount):
    periods, destinations = resolve_choices(quotes, ["2025_3Q"], ["MEX"])
    return calculate_summaries(
        quotes,
        amount,
        pd.DataFrame(columns=RELEVANCE),
        ScoringWeights(),
        ["2025_3Q"],
        ["MEX"],
        periods,
        destinations,
        _preparation_metadata(),
        available_periods=tuple(periods),
    )


def test_amount_selection_is_consistent_across_result_tables():
    quotes = _amount_quotes()
    result_200 = _analyze(quotes, 200)
    result_500 = _analyze(quotes, 500)

    for table_name in ("corridor_summary", "period_summary", "channel_summary"):
        table_200 = getattr(result_200, table_name)
        table_500 = getattr(result_500, table_name)
        assert len(table_200) == len(table_500) == 1
        assert table_200.iloc[0].median_total_cost == pytest.approx(3.5)
        assert table_500.iloc[0].median_total_cost == pytest.approx(7.0)
        assert table_200.iloc[0].total_quotes == table_500.iloc[0].total_quotes == 2
        assert table_200.iloc[0].non_transparent_quotes == table_500.iloc[0].non_transparent_quotes == 0
        assert table_200.iloc[0].non_transparent_quote_share == pytest.approx(0.0)
        assert table_500.iloc[0].non_transparent_quote_share == pytest.approx(0.0)

    assert result_200.channel_summary.iloc[0].channel_category == "Internet-only"
    assert result_500.channel_summary.iloc[0].channel_category == "Internet-only"

    expected_provider_values = {
        200: {
            "service-a": (2.0, 2.0, 1.0),
            "service-b": (5.0, 6.0, 2.0),
        },
        500: {
            "service-a": (5.0, 10.0, 3.0),
            "service-b": (9.0, 20.0, 5.0),
        },
    }
    for amount, result in ((200, result_200), (500, result_500)):
        details = result.provider_details.set_index("service_id")
        assert set(details.index) == {"service-a", "service-b"}
        assert details.transfer_amount_usd.eq(amount).all()
        assert details.fee_currency.eq("USD").all()
        for service_id, expected in expected_provider_values[amount].items():
            actual = details.loc[service_id]
            assert actual.total_cost_pct == pytest.approx(expected[0])
            assert actual.transfer_fee == pytest.approx(expected[1])
            assert actual.exchange_rate_margin == pytest.approx(expected[2])

    for result, expected_fee, expected_margin in (
        (result_200, 4.0, 1.5),
        (result_500, 15.0, 4.0),
    ):
        assert len(result.fee_summary) == len(result.fx_margin_summary) == 1
        assert result.fee_summary.iloc[0].median_transfer_fee == pytest.approx(expected_fee)
        assert result.fee_summary.iloc[0].fee_observations == 2
        assert result.fx_margin_summary.iloc[0].median_exchange_margin == pytest.approx(expected_margin)
        assert result.fx_margin_summary.iloc[0].fx_margin_observations == 2

    assert result_200.metadata.matching_row_count == result_500.metadata.matching_row_count == 2
