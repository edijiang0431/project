from pathlib import Path
from statistics import median

import pandas as pd
import pytest

from src.calculate_summaries import calculate_summaries
from src.contracts import RELEVANCE, ScoringWeights, period_key, resolve_choices
from src.filter_data import filter_quotes
from src.load_data import load_data, load_preparation_metadata, report_for
from tests.test_calculation import run


def test_real_mexico_latest_quarter_independent_crosscheck():
    path = Path(__file__).resolve().parents[1] / 'data/rpw_usa_clean.csv.gz'
    raw = pd.read_csv(path, dtype=str, keep_default_na=False)
    latest = max(raw['period'], key=period_key)
    records = [r for r in raw.to_dict('records')
               if r['source_code'] == 'USA' and r['destination_code'] == 'MEX'
               and r['period'] == latest]
    assert records, 'The latest quarter must contain Mexico quotes for this check'
    prep = load_preparation_metadata(report_for(path), path)
    quotes = load_data(path, prep)
    periods, destinations = resolve_choices(quotes, [latest], ['MEX'])
    selected = filter_quotes(quotes, [latest], ['MEX'])
    for amount, column in [(200, 'cc1_total_cost_pct'), (500, 'cc2_total_cost_pct')]:
        costs = [float(r[column]) for r in records
                 if r['transparent'] == 'yes' and r[column] != '']
        assert costs, 'This cross-check requires eligible costs'
        opaque = sum(r['transparent'] == 'no' for r in records)
        result = calculate_summaries(
            selected, amount, pd.DataFrame(columns=RELEVANCE), ScoringWeights(),
            [latest], ['MEX'], periods, destinations, prep)
        assert len(result.corridor_summary) == 1
        row = result.corridor_summary.iloc[0]
        assert row.destination_code == 'MEX'
        assert row.total_quotes == len(records)
        assert row.observations == len(costs)
        assert row.median_total_cost == pytest.approx(median(costs))
        assert row.non_transparent_quotes == opaque
        assert row.non_transparent_quote_share == pytest.approx(opaque / len(records))
        assert set(result.provider_details.service_id) == {r['id'] for r in records}

def test_negative_costs_remain_in_medians_and_normalization(quotes, prep):
    q = quotes.copy(deep=True)
    q.loc[q.destination_code == 'MEX', 'cc1_total_cost_pct'] = [-6., -4., -2.]
    q.loc[q.destination_code == 'IND', 'cc1_total_cost_pct'] = [-3., -1., 1.]
    third = q.iloc[:1].copy()
    third['id'] = 'negative-edge-phl'
    third['destination_code'] = 'PHL'
    third['destination_name'] = 'Philippines'
    third['corridor'] = 'USAPHL'
    third['corridor_label'] = 'United States to Philippines'
    third['cc1_total_cost_pct'] = 2.
    q = pd.concat([q, third], ignore_index=True)
    result = run(q, prep, weights=ScoringWeights(1, 0, 0))
    rows = result.corridor_summary.set_index('destination_code')
    assert rows.index.is_unique and set(rows.index) == {'MEX', 'IND', 'PHL'}
    for code, expected_median, expected_count, expected_normalized in [
        ('MEX', -4., 3, 0.), ('IND', -1., 3, .5), ('PHL', 2., 1, 1.)
    ]:
        assert rows.loc[code, 'median_total_cost'] == expected_median
        assert rows.loc[code, 'observations'] == expected_count
        assert rows.loc[code, 'cost_normalized'] == pytest.approx(expected_normalized)
        assert rows.loc[code, 'campaign_priority_score'] == pytest.approx(expected_normalized)
    assert (result.provider_details.total_cost_pct < 0).sum() == 5
