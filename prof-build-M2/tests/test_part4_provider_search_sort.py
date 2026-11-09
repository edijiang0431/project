from types import SimpleNamespace
import pandas as pd
from src.dashboard_presentation import recent_provider_rows


def test_provider_search_treats_special_characters_as_literal_text():
    names = ["A.B", "AxB", "Cash+", "Cashhh", "Pay(One)", "PayOne"]
    details = pd.DataFrame({
        "provider": names,
        "service_id": [f"service-{i}" for i in range(6)],
        "receiving_country": ["Mexico"] * 6,
        "reporting_period": ["2024_1Q"] * 6,
        "collection_date": pd.to_datetime(["2024-01-20"] * 6),
    })
    before = details.copy(deep=True)
    results = SimpleNamespace(provider_details=details)
    for query, expected in [("A.B", ["A.B"]), ("Cash+", ["Cash+"]),
                            ("Pay(One)", ["Pay(One)"])]:
        actual = recent_provider_rows(results, query=query)
        assert actual.provider.tolist() == expected
    pd.testing.assert_frame_equal(details, before)

def test_provider_numeric_sorting_both_directions_missing_last():
    details = pd.DataFrame({
        "provider": ["A", "B", "C", "D"],
        "service_id": ["a", "b", "c", "d"],
        "reporting_period": ["2024_1Q"] * 4,
        "collection_date": pd.to_datetime(["2024-01-20"] * 4),
        "total_cost_pct": [2.0, 10.0, 5.0, float("nan")],
        "transfer_fee": [10.0, 3.0, 7.0, float("nan")],
        "exchange_rate_margin": [1.5, 0.5, 2.0, float("nan")],
    })
    before = details.copy(deep=True)
    results = SimpleNamespace(provider_details=details)
    expected_orders = {
        "Total cost (%)": (["A", "C", "B", "D"], ["B", "C", "A", "D"]),
        "Transfer fee": (["B", "C", "A", "D"], ["A", "C", "B", "D"]),
        "FX margin (%)": (["B", "A", "C", "D"], ["C", "A", "B", "D"]),
    }
    for field, (ascending_order, descending_order) in expected_orders.items():
        for ascending, expected in [(True, ascending_order), (False, descending_order)]:
            actual = recent_provider_rows(results, sort=field, ascending=ascending)
            assert actual.provider.tolist() == expected
    pd.testing.assert_frame_equal(details, before)
