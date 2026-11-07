"""Acceptance checks for the team's Module 9 change requests."""
import pandas as pd
import pytest
from dataclasses import replace

from src.contracts import RELEVANCE, ScoringWeights
from src.dashboard_presentation import COST_MODE
from src.dashboard_workflow import DashboardSession
from src.rendering import access_checklist_html
from src.evidence_summaries import channel_cost_comparison, cost_coverage, key_findings, fee_distribution, service_cost_breakdown, filter_service_rows
from tests.test_dashboard import real_data
from src.period_presets import latest_four_calendar_quarters
from streamlit.testing.v1 import AppTest
from tests.test_dashboard import APP
from src.export_briefing import export_briefing


def test_cr01_access_checklist():
    text = access_checklist_html()
    assert 'reliable Internet' in text and 'secure connection' in text
    assert 'not facts inferred' in text and 'no personal answers' in text


@pytest.mark.parametrize('counter,expected,direction', [(4.6,1.18,'Counter-only higher'), (3.42,-1.18,'Internet-only higher'), (4.01,0,'Equal medians'), (float('nan'),None,'Unavailable')])
def test_cr02_channel_dollar_difference(quotes, prep, counter, expected, direction):
    result = DashboardSession(quotes, prep).analyze([], ['MEX'], 200, ScoringWeights(), pd.DataFrame(columns=RELEVANCE))
    channels = pd.DataFrame([['MEX','Internet-only',4.01,29], ['MEX','Counter-only',counter,15]], columns=['destination_code','channel_category','median_total_cost','observations'])
    result = replace(result, channel_summary=channels)
    row = channel_cost_comparison(result).iloc[0]
    assert row.direction == direction
    if expected is None:
        assert pd.isna(row.counter_minus_internet_usd)
    else:
        assert row.counter_minus_internet_usd == pytest.approx(expected)
    assert row.internet_eligible_quotes == 29 and row.counter_eligible_quotes == 15
    channels.drop(index=1, inplace=True)
    assert pd.isna(channel_cost_comparison(result).iloc[0].counter_minus_internet_usd)


def test_cr04_shared_reference_is_display_selection_invariant(quotes, prep):
    session = DashboardSession(quotes, prep)
    args = ([], 200, ScoringWeights(2/3,1/3,0), pd.DataFrame(columns=RELEVANCE))
    one = session.analyze(args[0], ['MEX'], *args[1:], scoring_mode=COST_MODE)
    both = session.analyze(args[0], [], *args[1:], scoring_mode=COST_MODE)
    assert one.metadata.cost_reference == both.metadata.cost_reference
    assert one.metadata.cost_reference.valid_corridors == 2
    assert one.metadata.cost_reference.minimum_pct == 4
    assert one.metadata.cost_reference.maximum_pct == 6
    a = one.corridor_summary.set_index('destination_code').loc['MEX']
    b = both.corridor_summary.set_index('destination_code').loc['MEX']
    assert a.cost_normalized == b.cost_normalized == 1
    assert a.campaign_priority_score == pytest.approx(b.campaign_priority_score)


def test_cr05_calendar_window_has_no_backfill():
    selected, window = latest_four_calendar_quarters(['2024_3Q','2024_4Q','2025_1Q','2025_3Q'])
    assert selected == ['2024_4Q','2025_1Q','2025_3Q']
    assert window == ('2024_4Q','2025_1Q','2025_2Q','2025_3Q')


def test_cr06_cost_coverage_and_missing_surveys(real_data):
    quotes, prep, relevance = real_data
    result = DashboardSession(quotes, prep).analyze(['2025_1Q'], ['MEX'], 500, ScoringWeights(), relevance)
    row = cost_coverage(result).iloc[0]
    assert row.eligible_cost_quotes == 45 and row.total_quotes == 46
    assert row.coverage_pct == pytest.approx(45/46*100)
    assert row.non_transparent_exclusions == 0 and row.transparent_missing_cost_quotes == 1
    selected, window = latest_four_calendar_quarters(quotes.period.unique())
    result = DashboardSession(quotes, prep).analyze(selected, ['MEX'], 500, ScoringWeights(), relevance, calendar_window=window)
    gap = cost_coverage(result).set_index('reporting_period').loc['2025_2Q']
    assert gap.status == 'No survey data' and pd.isna(gap.coverage_pct)


def test_cr07_plain_language_findings_keep_missing_evidence_explicit(quotes, prep):
    result = DashboardSession(quotes, prep).analyze([], ['MEX'], 200, ScoringWeights(), pd.DataFrame(columns=RELEVANCE))
    row = key_findings(result).iloc[0]
    assert '6.000%' in row['Price evidence']
    assert 'rating, rationale, evidence source, evidence date' in row['Community evidence']
    assert 'Gather and document' in row['Next step']
    assert '<NA>' not in row.to_string() and 'NaT' not in row.to_string()


def test_cr08_fee_distribution_preserves_zeros_and_currency(real_data):
    quotes, prep, relevance = real_data
    result = DashboardSession(quotes, prep).analyze(['2025_3Q'], ['MEX'], 200, ScoringWeights(), relevance)
    row = fee_distribution(result).iloc[0]
    assert row.fee_currency == 'USD'
    assert row.median_transfer_fee == pytest.approx(5.695)
    assert row.minimum_transfer_fee == 0 and row.maximum_transfer_fee == 35
    assert row.zero_fee_quotes == 2 and row.eligible_fee_quotes == 46


def test_cr09_provider_filters_are_view_only(quotes, prep):
    result = DashboardSession(quotes, prep).analyze([], [], 200, ScoringWeights(), pd.DataFrame(columns=RELEVANCE))
    before = result.provider_details.copy(deep=True)
    rows = filter_service_rows(before, {'total_cost_pct': (4, 6)}, keep_unavailable=False)
    assert rows.total_cost_pct.between(4,6).all() and len(rows) == 3
    assert len(filter_service_rows(before, {'total_cost_pct': (4, 6)}, keep_unavailable=True)) == 4
    with pytest.raises(ValueError, match='minimum'):
        filter_service_rows(before, {'transfer_fee': (10, 1)})
    pd.testing.assert_frame_equal(result.provider_details, before)


def test_cr10_service_components_preserve_published_cost(real_data):
    quotes, prep, relevance = real_data
    result = DashboardSession(quotes, prep).analyze(['2025_3Q'], ['MEX'], 200, ScoringWeights(), relevance)
    details = service_cost_breakdown(result.provider_details).set_index('service_id')
    row = details.loc['1212255489']
    assert row.transfer_fee_usd == pytest.approx(2.99)
    assert row.fx_margin_usd == pytest.approx(2.20)
    assert row.component_total_usd == pytest.approx(5.19)
    assert row.total_cost_pct == pytest.approx(2.60)
    assert row.published_total_usd == pytest.approx(5.20)
    assert row.component_minus_published_usd == pytest.approx(-0.01)
    raw = result.provider_details.iloc[:3].copy()
    raw['transparent'] = ['no','yes','yes']
    raw['fee_currency'] = ['USD','EUR','USD']
    raw['transfer_fee'] = [0,5,float('nan')]
    check = service_cost_breakdown(raw)
    assert check.component_total_usd.isna().all()
    assert check.iloc[0].breakdown_status.startswith('Unknown')


def test_calendar_shortcut_updates_dashboard_and_manual_selection_clears_it():
    app = AppTest.from_file(str(APP), default_timeout=120).run()
    assert not app.exception
    assert app.selectbox(key='scoring_mode').value == COST_MODE
    app.button(key='latest_four').click().run()
    assert not app.exception
    result = app.session_state['analysis_session'].last_successful_results
    assert result.metadata.resolved_periods == ('2024_4Q','2025_1Q','2025_3Q')
    assert result.metadata.calendar_window == ('2024_4Q','2025_1Q','2025_2Q','2025_3Q')
    assert not app.button(key='export').disabled
    app.number_input(key='provider_min_total_cost_pct').set_value(4.5).run()
    assert not app.exception
    assert app.session_state['analysis_session'].last_successful_results.metadata == result.metadata
    assert not app.button(key='export').disabled
    app.multiselect(key='periods').set_value(['2025_3Q']).run()
    assert app.session_state['calendar_window'] == ()
    assert app.button(key='export').disabled


def test_new_evidence_sections_export_and_dont_mutate_input(real_data, tmp_path):
    quotes, prep, relevance = real_data
    before = quotes.copy(deep=True)
    session = DashboardSession(quotes, prep)
    selected, window = latest_four_calendar_quarters(quotes.period.unique())
    weights = ScoringWeights(2/3,1/3,0)
    result = session.analyze(selected, ['MEX'], 200, weights, relevance, scoring_mode=COST_MODE, calendar_window=window)
    with pytest.raises(ValueError, match='Export blocked'):
        session.export(selected, ['MEX'], 200, weights, relevance, tmp_path, scoring_mode=COST_MODE)
    path = session.export(selected, ['MEX'], 200, weights, relevance, tmp_path, scoring_mode=COST_MODE, calendar_window=window)
    html = path.read_text()
    for text in ['Key findings and evidence readiness', 'Internet-access discussion checklist', 'Usable-cost coverage', 'Visible-fee distribution', 'Channel median difference in dollars', 'component_total_usd', 'Requested calendar window', prep.prepared_sha256]:
        assert text in html
    assert html.index('Key findings and evidence readiness') < html.index('<h2>Corridor comparison')
    assert result.provider_details.service_id.nunique() == result.metadata.matching_row_count
    pd.testing.assert_frame_equal(quotes, before)


def test_coverage_no_quotes_and_fee_distribution_excludes_unknown(quotes, prep):
    result = DashboardSession(quotes, prep).analyze(['2024_2Q'], ['IND'], 200, ScoringWeights(), pd.DataFrame(columns=RELEVANCE))
    coverage = cost_coverage(result).iloc[0]
    assert coverage.eligible_cost_quotes == 0 and coverage.transparent_missing_cost_quotes == 1
    empty = replace(result, period_summary=result.period_summary.iloc[:0])
    assert pd.isna(cost_coverage(empty).iloc[0].coverage_pct)
    q = quotes.copy()
    q['cc1_lcu_fee'] = [0., 100., float('nan'), 5., 7., 9.]
    q.loc[1, 'transparent'] = 'no'
    q['cc1_lcu_code'] = ['USD','USD','USD','EUR','EUR','EUR']
    result = DashboardSession(q, prep).analyze([], [], 200, ScoringWeights(), pd.DataFrame(columns=RELEVANCE))
    stats = fee_distribution(result).set_index('fee_currency')
    assert stats.loc['USD','eligible_fee_quotes'] == 1 and stats.loc['USD','zero_fee_quotes'] == 1
    assert stats.loc['USD','maximum_transfer_fee'] == 0
    assert stats.loc['EUR','minimum_transfer_fee'] == 5 and stats.loc['EUR','maximum_transfer_fee'] == 9
