"""Acceptance checks for the team's Module 9 change requests."""
import pandas as pd
import pytest
from dataclasses import replace

from src.contracts import RELEVANCE, ScoringWeights
from src.dashboard_presentation import COST_MODE
from src.dashboard_workflow import DashboardSession
from src.rendering import access_checklist_html
from src.evidence_summaries import channel_cost_comparison


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
