"""Hand-calculated checks for switching the dashboard's transfer basket."""
import pandas as pd
import pytest

from src.contracts import RELEVANCE
from src.dashboard_presentation import COST_MODE, default_weights
from src.dashboard_workflow import DashboardSession


def test_transfer_amount_recalculates_costs_and_scores(quotes, prep):
    # The existing fixture has two Mexico and two India quotes in this quarter.
    data = quotes.loc[quotes.period.eq('2024_1Q')].copy(deep=True)
    data['transparent'] = 'yes'
    data['cc1_total_cost_pct'] = [2., 4., 8., 10.]
    data['cc2_total_cost_pct'] = [12., 16., 4., 6.]
    relevance = pd.DataFrame(columns=RELEVANCE)
    session = DashboardSession(data, prep)

    # Each tuple is (median cost, normalized cost, priority score), by hand.
    expected = {
        200: {'MEX': (3., 0., 0.), 'IND': (9., 1., 2 / 3)},
        500: {'MEX': (14., 1., 2 / 3), 'IND': (5., 0., 0.)},
    }
    for amount, countries in expected.items():
        result = session.analyze(
            ['2024_1Q'], ['MEX', 'IND'], amount,
            default_weights(COST_MODE), relevance, scoring_mode=COST_MODE,
        )
        rows = result.corridor_summary.set_index('destination_code')
        assert set(rows.index) == {'MEX', 'IND'}
        for code, (median, normalized, score) in countries.items():
            assert rows.loc[code, 'median_total_cost'] == median
            assert rows.loc[code, 'cost_normalized'] == normalized
            assert rows.loc[code, 'campaign_priority_score'] == pytest.approx(score)

"""Excluded countries and quarters must not change selected dashboard results."""
import pandas as pd
import pytest

from src.contracts import RELEVANCE
from src.dashboard_presentation import COST_MODE, default_weights
from src.dashboard_workflow import DashboardSession


def test_display_filters_and_shared_reference_use_their_respective_scopes(quotes, prep):
    costs_by_country_quarter = {
        ('MEX', 'Mexico', '2024_1Q'): [2., 6.],
        ('IND', 'India', '2024_1Q'): [10.],
        ('MEX', 'Mexico', '2024_2Q'): [100.],
        ('IND', 'India', '2024_2Q'): [200.],
        ('PHL', 'Philippines', '2024_1Q'): [-50.],
    }
    records = []
    for (code, name, quarter), costs in costs_by_country_quarter.items():
        for cost in costs:
            # Reuse the fixture's prepared-row structure, not its cost values.
            row = quotes.iloc[0].copy(deep=True)
            row['id'] = str(len(records))
            row['destination_code'] = code
            row['destination_name'] = name
            row['period'] = quarter
            row['period_start'] = pd.Timestamp(
                '2024-01-01' if quarter == '2024_1Q' else '2024-04-01'
            )
            row['date'] = row['period_start']
            row['corridor'] = 'USA' + code
            row['corridor_label'] = 'United States to ' + name
            row['transparent'] = 'yes'
            row['cc1_total_cost_pct'] = cost
            records.append(row)
    data = pd.DataFrame(records).reset_index(drop=True)
    changed = data.copy(deep=True)
    excluded_costs = {
        ('MEX', '2024_2Q'): 1000.,
        ('IND', '2024_2Q'): 2000.,
        ('PHL', '2024_1Q'): -500.,
    }
    for (code, quarter), cost in excluded_costs.items():
        mask = changed.destination_code.eq(code) & changed.period.eq(quarter)
        changed.loc[mask, 'cc1_total_cost_pct'] = cost

    relevance = pd.DataFrame(columns=RELEVANCE)
    # The reference includes the hidden Philippines corridor in Q1,
    # but excludes both Q2 quotes. Displayed medians and counts stay fixed.
    for dataset, low in ((data, -50.), (changed, -500.)):
        mexico_normalized = (4. - low) / (10. - low)
        expected = {'MEX': (4., 2, mexico_normalized, mexico_normalized * 2 / 3),
                    'IND': (10., 1, 1., 2 / 3)}
        result = DashboardSession(dataset, prep).analyze(
            ['2024_1Q'], ['MEX', 'IND'], 200,
            default_weights(COST_MODE), relevance, scoring_mode=COST_MODE,
        )
        reference = result.metadata.cost_reference
        assert reference.valid_corridors == 3
        assert reference.minimum_pct == low
        assert reference.maximum_pct == 10.
        rows = result.corridor_summary.set_index('destination_code')
        assert set(rows.index) == {'MEX', 'IND'}
        assert len(rows) == 2
        for code, (median, count, normalized, score) in expected.items():
            assert rows.loc[code, 'median_total_cost'] == median
            assert rows.loc[code, 'observations'] == count
            assert rows.loc[code, 'cost_normalized'] == normalized
            assert rows.loc[code, 'campaign_priority_score'] == pytest.approx(score)

