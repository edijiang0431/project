"""R2.1: cautions belong beside pooled medians and individual cost points."""
from types import SimpleNamespace

import pandas as pd
import pytest

from src import dashboard_presentation as presentation
from tests.test_dashboard import app_for, assert_clean
from tests.test_dashboard_improvements import analyze


@pytest.mark.parametrize('scope', ['ranking', 'trend'])
@pytest.mark.parametrize('count', [0, 1, 5, 6])
def test_cost_caution_boundaries(scope, count):
    row = dict(receiving_country='Cuba', observations=count, total_quotes=7,
               reporting_period='2025_3Q')
    results = SimpleNamespace(corridor_summary=pd.DataFrame([row]),
                              period_summary=pd.DataFrame([row]))
    if scope == 'ranking':
        messages = presentation.cost_sample_messages(results, 'ranking')
    else:
        small, zero = getattr(presentation, 'quarterly_cost_sample_groups', lambda *args: ([], []))(results)
        messages = small + zero
    if count == 6:
        assert messages == []
    else:
        assert len(messages) == 1
        assert 'Cuba' in messages[0]
        if scope == 'trend':
            assert '2025 Q3' in messages[0]
        if count == 0:
            if scope == 'ranking':
                assert 'No eligible cost quotes' in messages[0]
                assert 'no median is available' in messages[0]
            else:
                assert small == []
                assert zero == ['Cuba: 2025 Q3 (0)']
            assert 'Small sample' not in messages[0]
        else:
            if scope == 'ranking':
                assert 'Small sample' in messages[0]
                assert f'{count} eligible cost quotes' in messages[0]
            else:
                assert small == [f'Cuba: 2025 Q3 ({count})']
                assert zero == []


def test_pooled_count_does_not_hide_small_quarters(quotes, prep):
    # Six pooled eligible Mexico quotes, but three in each quarter.
    rows = []
    for period in ['2024_1Q', '2024_2Q']:
        base = quotes.loc[quotes.destination_code.eq('MEX') & quotes.period.eq(period)].iloc[0]
        for i in range(3):
            row = base.copy()
            row['id'] = f'{period}-{i}'
            rows.append(row)
    result = analyze(pd.DataFrame(rows), prep)
    before = result.corridor_summary.copy(deep=True)
    messages = getattr(presentation, 'cost_sample_messages', lambda *args: [])
    assert messages(result, 'ranking') == []
    quarterly, zero = getattr(presentation, 'quarterly_cost_sample_groups', lambda *args: ([], []))(result)
    assert quarterly == ['Mexico: 2024 Q1 (3), 2024 Q2 (3)']
    assert zero == []
    pd.testing.assert_frame_equal(result.corridor_summary, before)


def test_visible_lists_beside_table_and_cost_chart(quotes, prep):
    app = app_for(quotes, prep)
    app.multiselect(key='destinations').set_value([])
    app.multiselect(key='periods').set_value([])
    app.button(key='update').click().run()
    assert_clean(app)
    comparison, quarters = app.tabs[0], app.tabs[1]
    ranking_text = '\n'.join(item.value for item in comparison.warning)
    trend_text = '\n'.join(item.value for item in quarters.warning)
    assert 'Mexico: 3 eligible cost quotes' in ranking_text
    assert 'India: 2 eligible cost quotes' in ranking_text
    assert 'Mexico: 2024 Q1 (2), 2024 Q2 (1)' in trend_text
    assert 'India: 2024 Q1 (2)' in trend_text
    assert trend_text.count('Treat quarterly medians based on 1–5 eligible cost quotes cautiously') == 1
    assert 'India: 2024 Q2 (0)' not in trend_text
    zero_text = '\n'.join(item.value for item in quarters.info)
    assert 'No eligible cost quotes; no median is available' in zero_text
    assert 'India: 2024 Q2 (0)' in zero_text
    assert any('1–5 eligible cost quotes' in item.value for item in comparison.caption)
    assert sum(item.value.count('Numbers in parentheses are eligible cost quote counts.') for item in quarters.caption) == 1
    result = app.session_state['analysis_session'].last_successful_results
    expected = analyze(quotes, prep)
    pd.testing.assert_frame_equal(result.corridor_summary, expected.corridor_summary)
    pd.testing.assert_frame_equal(result.period_summary, expected.period_summary)
    assert all(trace.mode == 'lines+markers' for trace in presentation.trend_figure(result).data)


def test_grouping_keeps_every_quarter_and_count_in_time_order():
    rows = []
    expected = []
    # More quarters than a compact list might otherwise truncate; input is reversed.
    for year in range(2016, 2026):
        for quarter in range(1, 5):
            count = 1 + (year + quarter) % 5
            rows.append(dict(receiving_country='Cuba', reporting_period=f'{year}_{quarter}Q', observations=count))
            expected.append(f'{year} Q{quarter} ({count})')
    rows += [dict(receiving_country='Mexico', reporting_period='2025_3Q', observations=5),
             dict(receiving_country='Cuba', reporting_period='2026_1Q', observations=6),
             dict(receiving_country='Cuba', reporting_period='2026_2Q', observations=0)]
    results = SimpleNamespace(period_summary=pd.DataFrame(rows[::-1]))
    before = results.period_summary.copy(deep=True)
    small, zero = getattr(presentation, 'quarterly_cost_sample_groups', lambda *args: ([], []))(results)
    assert small == ['Cuba: ' + ', '.join(expected), 'Mexico: 2025 Q3 (5)']
    assert zero == ['Cuba: 2026 Q2 (0)']
    pd.testing.assert_frame_equal(results.period_summary, before)
