"""Check real ACS provenance, missing countries and explicit application to scores."""
import json
from pathlib import Path

import pandas as pd
import pytest

from src.acs_evidence import ACS_SOURCE, acs_relevance, community_size_rating
from src.dashboard_presentation import COMMUNITY_MODE, COST_MODE, default_weights
from src.dashboard_workflow import DashboardSession
from src.prepare_acs import prepare, number
from tests.test_dashboard import app_for, assert_clean

ROOT = Path(__file__).resolve().parents[1]


def details():
    return pd.read_csv(ROOT / 'inputs' / 'acs_b05006_la.csv')


def test_population_share_uses_all_county_foreign_born_residents():
    d = details()
    rel = acs_relevance(d, set(d.destination_code))
    mexico = rel.set_index('destination_code').loc['MEX']
    # Independently read official Census variable values in the saved source row.
    snapshot = json.loads((ROOT / 'inputs' / 'acs_b05006_la_source.json').read_text())
    row = snapshot['row']
    assert row['GEO_ID'] == '0500000US06037'
    assert mexico.relevance_rating / 5 == pytest.approx(int(row['B05006_E160']) / int(row['B05006_E001']))
    filtered = acs_relevance(d[d.destination_code.eq('MEX')], {'MEX'})
    assert filtered.iloc[0].relevance_rating == mexico.relevance_rating
    assert 'MOE +/-9233' in mexico.rationale
    assert '2020–2024' in mexico.rationale
    assert 'B05006_160E' in mexico.evidence_source


def test_country_mapping_and_unavailable_are_not_fabricated():
    d = details()
    by_code = d.set_index('destination_code')
    assert by_code.loc['CHN', 'acs_category'] == 'China, excluding Hong Kong and Taiwan'
    assert by_code.loc['EGY', 'acs_category'] == 'Egypt'
    assert by_code.loc['CPV', 'acs_category'] == 'Cabo Verde'
    assert by_code.loc['SSD', 'match_status'] == 'Unavailable'
    assert pd.isna(by_code.loc['SSD', 'population_estimate'])
    rel = acs_relevance(d, set(d.destination_code))
    assert 'SSD' not in set(rel.destination_code)
    assert len(rel) == 41
    assert number('-666666666') is None
    assert number('0') == 0


@pytest.mark.parametrize('estimate,total', [(-1, 100), (101, 100), (0, 0), (float('nan'), 100)])
def test_invalid_populations_rejected(estimate, total):
    with pytest.raises(ValueError):
        community_size_rating(estimate, total)


def test_preparation_reproduces_saved_evidence():
    snapshot = json.loads((ROOT / 'inputs' / 'acs_b05006_la_source.json').read_text())
    d = details()
    rebuilt = prepare(snapshot, d[['destination_code', 'destination_name']])
    pd.testing.assert_frame_equal(rebuilt.fillna(''), d.fillna(''), check_dtype=False)


def test_acs_does_not_change_cost_mode(quotes, prep):
    rel = acs_relevance(details(), set(quotes.destination_code))
    session = DashboardSession(quotes, prep)
    args = ([], [], 200, default_weights(COST_MODE))
    without = session.analyze(*args, rel.iloc[:0], scoring_mode=COST_MODE)
    with_acs = session.analyze(*args, rel, scoring_mode=COST_MODE)
    pd.testing.assert_series_equal(without.corridor_summary.campaign_priority_score, with_acs.corridor_summary.campaign_priority_score)


def test_ui_requires_load_then_update_and_exports_provenance(quotes, prep, tmp_path):
    app = app_for(quotes, prep)
    assert app.selectbox(key='scoring_mode').value == COST_MODE
    app.selectbox(key='scoring_mode').select(COMMUNITY_MODE).run()
    app.multiselect(key='periods').set_value([]).run()
    app.radio(key='evidence_source').set_value(ACS_SOURCE).run()
    assert app.button(key='update').disabled
    app.button(key='load_evidence').click().run()
    assert not app.button(key='update').disabled
    app.button(key='update').click().run()
    assert_clean(app)
    session = app.session_state['analysis_session']
    result = session.last_successful_results
    assert result.corridor_summary.campaign_priority_score.notna().all()
    assert result.corridor_summary.iloc[0].relevance_normalized == pytest.approx(1141433 / 3279681)
    args = ([], ['MEX'], 200, default_weights(COMMUNITY_MODE), app.session_state['relevance'])
    html = session.export(*args, scoring_mode=COMMUNITY_MODE, output_dir=tmp_path).read_text()
    assert 'ACS community-size proxy' in html
    assert 'MOE +/-9233' in html
    assert '2020–2024' in html
    assert 'data.census.gov' in html
