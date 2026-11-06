"""Checks for the agreed scoring modes, presentation semantics and exact exports."""
from dataclasses import replace
import math
import re

import numpy as np
import pandas as pd
import pytest

from src.contracts import RELEVANCE, ScoringWeights
from src.dashboard_workflow import DashboardSession
from src.dashboard_presentation import (
    COMMUNITY_MODE, COST_MODE, default_weights, validate_mode_weights, current_warnings,
    score_contributions, comparison_table, period_grid, trend_figure, cost_axis_range,
    recent_provider_rows, small_sample_messages, channel_period_details,
)
from src.rendering import body_sections, make_figures
from tests.test_dashboard import real_data, app_for, assert_clean


def analyze(quotes, prep, mode=COST_MODE, weights=None, relevance=None, periods=None, destinations=None):
    return DashboardSession(quotes, prep).analyze(
        periods or [], destinations or [], 200, default_weights(mode) if weights is None else weights,
        pd.DataFrame(columns=RELEVANCE) if relevance is None else relevance, scoring_mode=mode,
    )


def test_two_component_weights_and_hand_calculated_scores(quotes, prep):
    weights = default_weights(COST_MODE)
    assert weights == ScoringWeights(2 / 3, 1 / 3, 0)
    assert weights.cost + weights.transparency == 1
    result = analyze(quotes, prep)
    # Fixture medians: Mexico 6 and India 4. Both disclosure shares are 0.
    rows = result.corridor_summary.set_index('destination_code')
    assert rows.loc['MEX', 'campaign_priority_score'] == pytest.approx(2 / 3)
    assert rows.loc['IND', 'campaign_priority_score'] == 0
    assert rows.relevance_normalized.isna().all()
    assert rows.campaign_priority_score.notna().all()
    contributions = score_contributions(result)
    assert set(contributions.Component) == {'Relative cost', 'Non-transparent quote share'}
    for country, group in contributions.groupby('Country'):
        score = result.corridor_summary.set_index('receiving_country').loc[country, 'campaign_priority_score']
        assert group.Contribution.sum() == pytest.approx(score)


def test_partial_evidence_descriptive_in_both_modes(quotes, prep):
    rel = pd.DataFrame([['MEX', 4, 'test evidence', '', '2024-01-01']], columns=RELEVANCE)
    campaign = analyze(quotes, prep, COMMUNITY_MODE, relevance=rel)
    assert campaign.corridor_summary.campaign_priority_score.isna().all()
    assert any('evidence source' in message for message in current_warnings(campaign))
    cost = analyze(quotes, prep, relevance=rel)
    assert cost.corridor_summary.campaign_priority_score.notna().all()
    assert cost.metadata.validated_relevance_snapshot == campaign.metadata.validated_relevance_snapshot
    assert cost.corridor_summary.set_index('destination_code').loc['MEX', 'relevance_rationale'] == 'test evidence'
    assert not any('score unavailable' in message for message in current_warnings(cost))


@pytest.mark.parametrize('weights', [ScoringWeights(.7, .35, 0), ScoringWeights(-.1, 1.1, 0), ScoringWeights(float('nan'), 1, 0), ScoringWeights(.5, .25, .25)])
def test_two_component_invalid_weights(weights):
    with pytest.raises(ValueError):
        validate_mode_weights(COST_MODE, weights)


def test_invalid_evidence_not_silently_applied(quotes, prep):
    rel = pd.DataFrame([['MEX', 9, 'invalid', 'test', '2024-01-01']], columns=RELEVANCE)
    with pytest.raises(ValueError, match='relevance_rating'):
        analyze(quotes, prep, relevance=rel)


def test_mode_is_part_of_export_guard_even_with_same_weights(quotes, prep, tmp_path):
    session = DashboardSession(quotes, prep)
    args = ([], [], 200, ScoringWeights(.5, .5, 0), pd.DataFrame(columns=RELEVANCE))
    session.analyze(*args, scoring_mode=COMMUNITY_MODE)
    assert session.matches(*args, scoring_mode=COMMUNITY_MODE)
    assert not session.matches(*args, scoring_mode=COST_MODE)
    with pytest.raises(ValueError, match='Export blocked'):
        session.export(*args, output_dir=tmp_path, scoring_mode=COST_MODE)
    session.analyze(*args, scoring_mode=COST_MODE)
    path = session.export(*args, output_dir=tmp_path, scoring_mode=COST_MODE)
    html = path.read_text(encoding='utf-8')
    assert 'Cost &amp; disclosure' in html
    assert 'Community relevance is excluded' in html
    assert 'Applied community evidence snapshot' in html
    assert 'Showing 6 of 6 service rows' in html
    assert 'data:image/png;base64,' in html
    assert not re.search(r'<(?:script|link)\b|src="https?://', html)


def test_precise_defaults_and_evidence_in_export(quotes, prep, tmp_path):
    session = DashboardSession(quotes, prep)
    rel = pd.DataFrame([['MEX', 4, '<unsafe text>', 'fixture only', '2024-01-01']], columns=RELEVANCE)
    args = ([], [], 200, default_weights(COST_MODE), rel)
    result = session.analyze(*args, scoring_mode=COST_MODE)
    html = session.export(*args, output_dir=tmp_path, scoring_mode=COST_MODE).read_text(encoding='utf-8')
    assert repr(2 / 3) in html and repr(1 / 3) in html
    assert '&lt;unsafe text&gt;' in html and '<unsafe text>' not in html
    assert result.metadata.weights.relevance == 0
    # A table-only search must not affect the export or the analytical table.
    assert recent_provider_rows(result, query='no such provider').empty
    assert 'Showing 6 of 6 service rows' in html
    assert len(result.provider_details) == 6


def test_conditional_cost_warning_and_zero_weight_missing_component(quotes, prep):
    result = analyze(quotes, prep)
    assert not any('Relative cost unavailable' in x for x in current_warnings(result))
    assert 'Relative cost unavailable' not in ''.join(body_sections(result))
    single = analyze(quotes, prep, destinations=['MEX'])
    assert not any('Relative cost unavailable' in x for x in current_warnings(single))
    assert single.corridor_summary.cost_normalized.iloc[0] == 1
    assert single.corridor_summary.campaign_priority_score.notna().all()
    zero = analyze(quotes, prep, destinations=['MEX'], weights=ScoringWeights(0, 1, 0))
    assert zero.corridor_summary.cost_normalized.iloc[0] == 1
    assert zero.corridor_summary.campaign_priority_score.iloc[0] == 0
    part = score_contributions(zero).query("Component == 'Relative cost'").iloc[0]
    assert part['Component value'] == 1 and part.Contribution == 0
    equal = quotes.copy()
    equal.cc1_total_cost_pct = 6.
    result = analyze(equal, prep)
    assert result.corridor_summary.cost_normalized.eq(0).all()
    assert result.corridor_summary.median_total_cost.eq(6).all()


def test_grid_classifies_all_three_gap_types(quotes, prep):
    q = quotes.copy()
    mex_q2 = q.destination_code.eq('MEX') & q.period.eq('2024_2Q')
    q.loc[mex_q2, 'period'] = '2024_3Q'
    q.loc[mex_q2, 'period_start'] = pd.Timestamp('2024-07-01')
    result = analyze(q, prep, periods=['2024_1Q', '2024_3Q'])
    grid = period_grid(result).set_index(['Code', 'Period'])
    assert grid.loc[('MEX', '2024_2Q'), 'Cost status'] == 'Not selected'
    assert grid.loc[('IND', '2024_3Q'), 'Cost status'] == 'No data'
    absent_globally = replace(result, metadata=replace(result.metadata, available_periods=('2024_1Q', '2024_3Q')))
    assert period_grid(absent_globally).query("Period == '2024_2Q'")['Cost status'].eq('No survey data').all()
    fig = trend_figure(result)
    assert fig.data[0].connectgaps is False
    assert fig.data[0].y[1] is None
    # The valid IND Q2 quote has missing cost but a known zero disclosure share.
    full = period_grid(analyze(q, prep)).set_index(['Code', 'Period'])
    assert full.loc[('IND', '2024_2Q'), 'Cost status'] == 'No data'
    assert full.loc[('IND', '2024_2Q'), 'Disclosure share'] == 0


def test_chart_negative_values_and_single_points(quotes, prep):
    q = quotes.copy()
    q.loc[q.destination_code.eq('MEX'), 'cc1_total_cost_pct'] = -2.
    result = analyze(q, prep, periods=['2024_1Q'])
    fig = trend_figure(result)
    assert 'USD 200' in fig.layout.title.text and 'Mexico' in fig.layout.title.text
    assert fig.layout.yaxis.range[0] < -2 and fig.layout.yaxis.range[1] >= 0
    assert len(fig.data[0].y) == 1 and 'markers' in fig.data[0].mode
    assert 'Eligible quotes' in fig.data[0].hovertemplate
    assert cost_axis_range([-2, -1])[1] >= 0
    assert cost_axis_range([4, 5], 'Focus on variation')[0] > 0
    static = make_figures(result)[0]
    assert static.axes[0].get_ylim()[0] < -2
    assert '%' in static.axes[1].yaxis.get_major_formatter()(0.5)


def test_disclosure_percentages_from_underlying_fraction(quotes, prep):
    q = quotes.copy()
    q.loc[0, 'transparent'] = 'no'
    result = analyze(q, prep)
    row = comparison_table(result).set_index('Receiving country').loc['Mexico']
    assert row['Flagged / total quotes (%)'] == '1 / 3 (33.333333%)'
    fig = trend_figure(result, 'disclosure')
    trace = next(t for t in fig.data if t.name == 'Mexico')
    assert list(trace.y) == [.5, 0]
    assert fig.layout.yaxis.tickformat == '.0%'
    assert trace.connectgaps is False
    q.transparent = 'no'
    result = analyze(q, prep)
    assert result.corridor_summary.non_transparent_quote_share.eq(1).all()
    q.transparent = 'yes'
    assert analyze(q, prep).corridor_summary.non_transparent_quote_share.eq(0).all()


def test_real_mexico_armenia_and_dynamic_channel_sample(real_data):
    quotes, prep, rel = real_data
    result = analyze(quotes, prep, relevance=rel, destinations=['MEX', 'ARM'])
    # Independently read CSV fields rather than copying app outputs.
    raw = pd.read_csv('data/rpw_usa_clean.csv.gz', dtype=str, keep_default_na=False)
    medians = {}
    for code in ['MEX', 'ARM']:
        rows = raw.loc[raw.source_code.eq('USA') & raw.destination_code.eq(code)]
        eligible = pd.to_numeric(rows.loc[rows.transparent.eq('yes'), 'cc1_total_cost_pct'].replace('', np.nan))
        median = eligible.median()
        medians[code] = median
        actual = result.corridor_summary.set_index('destination_code').loc[code]
        assert actual.median_total_cost == median
        assert actual.total_quotes == len(rows)
        assert actual.non_transparent_quotes == rows.transparent.eq('no').sum()
    mex = result.corridor_summary.set_index('destination_code').loc['MEX']
    assert mex.total_quotes == 1329 and mex.non_transparent_quotes == 1
    all_costs = pd.to_numeric(raw.loc[raw.transparent.eq('yes'), 'cc1_total_cost_pct'].replace('', np.nan))
    reference_medians = raw.loc[raw.transparent.eq('yes')].assign(cost=all_costs).groupby('destination_code').cost.median().dropna()
    expected = (medians['MEX'] - reference_medians.min()) / (reference_medians.max() - reference_medians.min())
    assert mex.cost_normalized == pytest.approx(expected)
    assert mex.campaign_priority_score == pytest.approx(2 / 3 * expected + 1 / 3 * (1 / 1329))
    assert result.corridor_summary.campaign_priority_score.notna().all()
    assert not any('Relative cost unavailable' in x for x in current_warnings(result))
    assert any('Mexico - Mixed: 5 eligible' in x for x in small_sample_messages(result))
    latest = analyze(quotes, prep, relevance=rel, periods=['2025_3Q'], destinations=['MEX'])
    assert not any('Mexico - Mixed: 5 eligible' in x for x in small_sample_messages(latest))
    grid = period_grid(result)
    assert grid.query("Period == '2025_2Q'")['Cost status'].eq('No survey data').all()
    spike = grid.query("Code == 'MEX' and Period == '2017_1Q'").iloc[0]
    assert spike['Disclosure share'] == 1 / 26
    details, rows = channel_period_details(result, 'Mexico', 'Mixed')
    assert len(rows) == 5 and details.eligible_quotes.sum() == 5
    ordered = recent_provider_rows(result)
    visible_quarter = recent_provider_rows(result, query='2025 Q3')
    assert not visible_quarter.empty
    assert visible_quarter.reporting_period.eq('2025_3Q').all()
    assert set(visible_quarter.service_id) == set(result.provider_details.loc[result.provider_details.reporting_period.eq('2025_3Q'), 'service_id'])
    assert len(ordered) == len(result.provider_details)
    assert ordered.reporting_period.iloc[0] == result.provider_details.reporting_period.max()
    assert ordered.collection_date.iloc[0] == ordered.loc[ordered.reporting_period.eq(ordered.reporting_period.iloc[0]), 'collection_date'].max()


def test_ui_modes_defaults_stale_exports_and_template(quotes, prep):
    app = app_for(quotes, prep)
    assert app.selectbox(key='scoring_mode').value == COST_MODE
    app.selectbox(key='scoring_mode').select(COMMUNITY_MODE).run()
    assert any(button.key == 'evidence_template' for button in app.download_button)
    app.multiselect(key='destinations').set_value(['MEX', 'IND'])
    app.multiselect(key='periods').set_value([])
    app.button(key='update').click().run()
    assert_clean(app)
    assert app.session_state['analysis_session'].last_successful_results.corridor_summary.campaign_priority_score.isna().all()
    app.selectbox(key='scoring_mode').select(COST_MODE).run()
    assert_clean(app)
    assert app.number_input(key='cost_weight').value == 2 / 3
    assert app.number_input(key='transparency_weight').value == 1 / 3
    assert app.button(key='export').disabled
    app.button(key='update').click().run()
    assert_clean(app)
    result = app.session_state['analysis_session'].last_successful_results
    assert result.metadata.scoring_mode == COST_MODE
    assert result.metadata.weights == default_weights(COST_MODE)
    assert result.corridor_summary.campaign_priority_score.notna().all()
    assert not any('Relative cost unavailable' in x.value for x in app.info)
    app.selectbox(key='scoring_mode').select(COMMUNITY_MODE).run()
    assert app.number_input(key='cost_weight').value == .5
    assert app.number_input(key='relevance_weight').value == .25
    assert app.button(key='export').disabled
    app.radio(key='evidence_source').set_value('No community evidence').run()
    assert app.button(key='update').disabled
    app.button(key='load_evidence').click().run()
    assert_clean(app)
    assert not app.button(key='update').disabled
    assert app.session_state['relevance'].empty
