import csv
from decimal import Decimal
import gzip
from pathlib import Path
from statistics import median

import pandas as pd
import pytest

from src.contracts import RELEVANCE, ScoringWeights
from src.dashboard_workflow import DashboardSession
from src.load_data import load_data, load_preparation_metadata


def test_internet_median_excludes_nontransparent_and_other_channels(quotes, prep):
    # Six services in one corridor and quarter, with distinct quote IDs.
    data = pd.concat([quotes.iloc[[0]].copy() for _ in range(6)], ignore_index=True)
    data["id"] = [f"channel-{i}" for i in range(6)]
    data["access_point"] = ["Internet", "Internet", "Internet", "Agent", "Internet,Agent", "Call Center"]
    data["transparent"] = ["yes", "yes", "no", "yes", "yes", "yes"]
    data["cc1_total_cost_pct"] = [2.0, 4.0, 0.0, 6.0, 10.0, 8.0]

    result = DashboardSession(data, prep).analyze(
        [], ["MEX"], 200, ScoringWeights(), pd.DataFrame(columns=RELEVANCE)
    )
    channels = result.channel_summary.set_index("channel_category")
    internet = channels.loc["Internet-only"]

    # By hand: median([2, 4]) = 3; undisclosed 0 is not an eligible cost.
    assert internet["median_total_cost"] == pytest.approx(3.0)
    assert internet["observations"] == 2
    assert internet["total_quotes"] == 3


def test_real_mexico_channel_medians_and_counts_match_independent_csv():
    path = Path(__file__).resolve().parents[1] / "data/rpw_usa_clean.csv.gz"
    with gzip.open(path, "rt", encoding="utf-8-sig", newline="") as source:
        raw_rows = list(csv.DictReader(source))
    latest = max(
        (row["period"] for row in raw_rows if row["source_code"] == "USA"),
        key=lambda value: (int(value[:4]), int(value[5])),
    )
    selected = [
        row for row in raw_rows
        if row["source_code"] == "USA"
        and row["destination_code"] == "MEX"
        and row["period"] == latest
    ]
    assert selected, f"No Mexico quotes in latest available quarter {latest}"

    # Independent CSV loop: do not call the app's classifier or aggregation.
    expected = {}
    counter_tokens = {"agent", "bank branch", "post office branch"}
    recognized = counter_tokens | {"internet", "call center"}
    for row in selected:
        tokens = {" ".join(token.split()).casefold() for token in row["access_point"].split(",")}
        if not tokens <= recognized:
            category = "Other/unknown"
        elif "internet" in tokens and tokens & counter_tokens:
            category = "Mixed"
        elif "internet" in tokens:
            category = "Internet-only"
        elif tokens & counter_tokens:
            category = "Counter-only"
        else:
            category = "Other/unknown"
        eligible = expected.setdefault(category, [])
        value = row["cc1_total_cost_pct"].strip()
        if row["transparent"].strip().lower() == "yes" and value:
            cost = Decimal(value)
            assert cost.is_finite(), f"Nonfinite cost in quote {row['id']}"
            eligible.append(cost)

    preparation = load_preparation_metadata(str(path) + ".validation.json", path)
    quotes = load_data(path, preparation)
    result = DashboardSession(quotes, preparation).analyze(
        [latest], ["MEX"], 200, ScoringWeights(), pd.DataFrame(columns=RELEVANCE)
    )
    actual = result.channel_summary.set_index("channel_category")
    assert set(actual.index) == set(expected)
    for category, costs in expected.items():
        assert actual.loc[category, "observations"] == len(costs), category
        if costs:
            assert actual.loc[category, "median_total_cost"] == pytest.approx(float(median(costs))), category
        else:
            assert pd.isna(actual.loc[category, "median_total_cost"]), category
