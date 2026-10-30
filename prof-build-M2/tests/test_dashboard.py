"""Dashboard behavior, export guards, and real-data notebook parity."""
from dataclasses import replace
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from src.contracts import RELEVANCE, SCHEMAS, ScoringWeights
from src.dashboard_workflow import DashboardSession
from src.load_data import load_data, load_preparation_metadata
from src.load_relevance import load_relevance
from src.notebook_workflow import NotebookSession

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / 'streamlit_app.py'


@pytest.fixture(scope='module')
def real_data():
    path = ROOT / 'data' / 'rpw_usa_clean.csv.gz'
    prep = load_preparation_metadata(str(path) + '.validation.json', path)
    quotes = load_data(path, prep)
    relevance = load_relevance(ROOT / 'inputs' / 'community_relevance.csv', set(quotes.destination_code))
    return quotes, prep, relevance


@pytest.mark.parametrize('destinations,expected_normalized', [(['MEX'], None), (['MEX', 'PHL'], 1.0), ([], 0.314598)])
def test_real_notebook_dashboard_parity(real_data, monkeypatch, destinations, expected_normalized):
    quotes, prep, relevance = real_data
    # Bypass only notebook display; exercise its unchanged orchestration.
    monkeypatch.setattr('src.notebook_workflow.present_results', lambda *args: None)
    args = (['2025_3Q'], destinations, 200, ScoringWeights(), relevance)
    notebook = NotebookSession(quotes, prep).analyze(*args)
    dashboard = DashboardSession(quotes, prep).analyze(*args)
    for name in SCHEMAS:
        pd.testing.assert_frame_equal(getattr(dashboard, name), getattr(notebook, name))
    assert dashboard.metadata == notebook.metadata
    mexico = dashboard.corridor_summary.set_index('destination_code').loc['MEX']
    assert mexico.median_total_cost == pytest.approx(4.485)
    if expected_normalized is None:
        assert pd.isna(mexico.cost_normalized)
    else:
        assert mexico.cost_normalized == pytest.approx(expected_normalized, abs=5e-7)


@pytest.mark.parametrize('change', ['period', 'destination', 'amount', 'weights', 'evidence', 'fingerprint'])
def test_export_rejects_changed_inputs(quotes, prep, tmp_path, change):
    session = DashboardSession(quotes, prep)
    rel = pd.DataFrame(columns=RELEVANCE)
    args = [[], [], 200, ScoringWeights(), rel]
    session.analyze(*args)
    if change == 'period':
        args[0] = ['2024_1Q']
    elif change == 'destination':
        args[1] = ['MEX']
    elif change == 'amount':
        args[2] = 500
    elif change == 'weights':
        args[3] = ScoringWeights(0.5, 0.5, 0)
    elif change == 'evidence':
        args[4] = pd.DataFrame([['MEX', 4, 'Documented', 'Research', '2024-01-01']], columns=RELEVANCE)
    else:
        session.preparation = replace(prep, prepared_sha256='2' * 64)
    assert not session.matches(*args)
    with pytest.raises(ValueError, match='Export blocked'):
        session.export(*args, output_dir=tmp_path)
    assert not list(tmp_path.iterdir())


def test_failed_update_and_unrun_session_cannot_export(quotes, prep, tmp_path):
    session = DashboardSession(quotes, prep)
    args = ([], [], 200, ScoringWeights(), pd.DataFrame(columns=RELEVANCE))
    with pytest.raises(ValueError, match='Export blocked'):
        session.export(*args, output_dir=tmp_path)
    session.analyze(*args)
    with pytest.raises(ValueError, match='sum to 1'):
        session.analyze([], [], 200, ScoringWeights(1, 1, 1), args[-1])
    with pytest.raises(ValueError, match='Export blocked'):
        session.export(*args, output_dir=tmp_path)
    assert not list(tmp_path.iterdir())


def app_for(quotes, prep):
    app = AppTest.from_file(str(APP), default_timeout=60)
    app.session_state['analysis_session'] = DashboardSession(quotes, prep)
    return app.run()


def assert_clean(app):
    assert not app.exception, [x.message for x in app.exception]


def test_ui_requires_update_and_blocks_stale_export(quotes, prep, tmp_path, monkeypatch):
    from src.export_briefing import export_briefing
    monkeypatch.setattr('src.dashboard_workflow.export_briefing', lambda result, output_dir: export_briefing(result, tmp_path))
    app = app_for(quotes, prep)
    assert_clean(app)
    assert app.button(key='export').disabled
    app.button(key='update').click().run()
    assert_clean(app)
    assert not app.button(key='export').disabled
    assert any('Some scores are unavailable' in item.value for item in app.info)
    assert any('at least two selected corridors' in str(value) for item in app.dataframe for value in item.value.to_numpy().flat)
    app.button(key='export').click().run()
    assert_clean(app)
    assert any(button.key == 'download' for button in app.download_button)
    html = next(tmp_path.glob('*.html')).read_text(encoding='utf-8')
    assert 'Showing 1 of 1 service rows' in html
    assert 'USD 200' in html
    app.selectbox(key='amount').select(500).run()
    assert app.button(key='export').disabled
    assert not any(button.key == 'download' for button in app.download_button)
    assert any('differ from the displayed results' in x.value for x in app.warning)
    assert app.session_state['analysis_session'].last_successful_results.metadata.transfer_amount_usd == 200
    app.button(key='update').click().run()
    assert not app.button(key='export').disabled
    assert not any(button.key == 'download' for button in app.download_button)
    app.button(key='export').click().run()
    assert 'USD 500' in app.session_state['export_artifact'][1].decode('utf-8')
    app.number_input(key='cost_weight').set_value(1.0).run()
    assert app.button(key='export').disabled
    app.button(key='update').click().run()
    assert_clean(app)
    assert any('sum to 1' in x.value for x in app.error)
    assert app.button(key='export').disabled
    assert len(app.metric) == 0


def test_ui_empty_lists_mean_all_and_no_matching_quotes(quotes, prep):
    app = app_for(quotes, prep)
    app.multiselect(key='destinations').set_value([])
    app.multiselect(key='periods').set_value([])
    app.button(key='update').click().run()
    assert_clean(app)
    assert app.session_state['analysis_session'].last_successful_results.metadata.matching_row_count == len(quotes)
    # A globally valid destination and quarter with no intersecting records.
    q = quotes.loc[~(quotes.destination_code.eq('IND') & quotes.period.eq('2024_2Q'))].copy()
    app = app_for(q, prep)
    app.multiselect(key='destinations').set_value(['IND'])
    app.multiselect(key='periods').set_value(['2024_2Q'])
    app.button(key='update').click().run()
    assert_clean(app)
    assert any('No matching quotes' in x.value for x in app.info)
    assert app.metric[0].value == '0'


def test_ui_evidence_load_replace_and_reject(quotes, prep):
    app = app_for(quotes, prep)
    app.multiselect(key='destinations').set_value(['MEX', 'IND'])
    app.multiselect(key='periods').set_value(['2024_1Q'])
    app.button(key='update').click().run()
    app.radio(key='evidence_source').set_value('Upload CSV').run()
    assert app.button(key='update').disabled
    assert app.button(key='export').disabled
    raw = b'destination_code,relevance_rating,rationale,evidence_source,evidence_date\nMEX,4,Documented,Research,2024-01-01\n'
    app.file_uploader(key='evidence_upload').set_value(('evidence.csv', raw, 'text/csv')).run()
    assert app.button(key='update').disabled
    app.button(key='load_evidence').click().run()
    assert_clean(app)
    assert not app.button(key='update').disabled
    assert app.button(key='export').disabled
    app.button(key='update').click().run()
    assert_clean(app)
    result = app.session_state['analysis_session'].last_successful_results
    assert result.metadata.validated_relevance_snapshot[0].relevance_rating == 4
    assert pd.notna(result.corridor_summary.set_index('destination_code').loc['MEX', 'campaign_priority_score'])
    app.file_uploader(key='evidence_upload').set_value(('bad.csv', raw.replace(b'MEX,4,', b'MEX,9,'), 'text/csv')).run()
    assert app.button(key='export').disabled
    app.button(key='load_evidence').click().run()
    assert_clean(app)
    assert any('relevance_rating' in x.value for x in app.error)
    assert app.button(key='update').disabled
    assert app.button(key='export').disabled


def test_ui_real_requested_examples(real_data):
    app = AppTest.from_file(str(APP), default_timeout=60).run()
    assert_clean(app)
    assert app.multiselect(key='destinations').value == ['MEX']
    assert app.selectbox(key='amount').value == 200
    assert app.multiselect(key='periods').value == ['2025_3Q']
    for destinations, expected in [(['MEX'], None), (['MEX', 'PHL'], 1.0), ([], 0.314598)]:
        app.multiselect(key='destinations').set_value(destinations)
        app.button(key='update').click().run()
        assert_clean(app)
        row = app.session_state['analysis_session'].last_successful_results.corridor_summary.set_index('destination_code').loc['MEX']
        assert row.median_total_cost == pytest.approx(4.485)
        if expected is None:
            assert pd.isna(row.cost_normalized)
        else:
            assert row.cost_normalized == pytest.approx(expected, abs=5e-7)
