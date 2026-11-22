"""R1: retain each historical quote's recipient payout in results, table and export."""
from html.parser import HTMLParser

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from src.contracts import RELEVANCE, ScoringWeights
from src.dashboard_presentation import COST_MODE, recent_provider_rows
from src.dashboard_workflow import DashboardSession
from src.export_briefing import export_briefing
from tests.test_dashboard import APP, real_data


class Tables(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.tables, self.rows, self.row, self.cell = [], None, None, None
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        if tag == 'table':
            self.rows = []
        elif tag == 'tr':
            self.row = []
        elif tag in ('th', 'td'):
            self.cell = []

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if tag in ('th', 'td'):
            self.row.append(''.join(self.cell).strip())
            self.cell = None
        elif tag == 'tr':
            self.rows.append(self.row)
        elif tag == 'table':
            self.tables.append(self.rows)
            self.rows = None


def analyze(quotes, prep, periods, destinations, amount):
    return DashboardSession(quotes, prep).analyze(
        periods, destinations, amount, ScoringWeights(2/3, 1/3, 0),
        pd.DataFrame(columns=RELEVANCE), scoring_mode=COST_MODE)


@pytest.mark.parametrize('destination,amount', [('MEX', 200), ('MEX', 500), ('LBR', 200)])
def test_results_preserve_each_source_payout_method(real_data, destination, amount):
    quotes, prep, _ = real_data
    result = analyze(quotes, prep, ['2025_3Q'], [destination], amount)
    assert 'pickup_method' in result.provider_details, 'Recipient payout method is dropped from quote results'
    source = quotes.loc[quotes.period.eq('2025_3Q') & quotes.destination_code.eq(destination)]
    expected = source.set_index('id').pickup_method.sort_index()
    actual = result.provider_details.set_index('service_id').pickup_method.sort_index()
    pd.testing.assert_series_equal(actual, expected, check_names=False)
    if destination == 'MEX':
        assert actual.value_counts().to_dict() == {'Cash': 31, 'Bank account': 14, 'Own/partner Bank account': 1}


def test_missing_or_unusual_payout_is_not_inferred_from_sender_channel(quotes, prep):
    quotes = quotes.copy(deep=True)
    quotes['pickup_method'] = ['Cash', 'Bank account', pd.NA, 'Mobile wallet',
                               'Own/partner Bank account', 'Other <recorded>']
    quotes.loc[1, 'transparent'] = 'no'
    before = quotes.copy(deep=True)
    result = analyze(quotes, prep, [], [], 200)
    assert 'pickup_method' in result.provider_details, 'Missing payout contract'
    actual = result.provider_details.set_index('service_id')
    assert actual.loc['0', 'channel_category'] == 'Internet-only'
    assert actual.loc['0', 'pickup_method'] == 'Cash'
    assert actual.loc['1', 'pickup_method'] == 'Bank account'
    assert pd.isna(actual.loc['1', 'total_cost_pct'])
    assert pd.isna(actual.loc['2', 'pickup_method'])
    assert actual.loc['3', 'pickup_method'] == 'Mobile wallet'
    assert actual.loc['4', 'pickup_method'] == 'Own/partner Bank account'
    assert actual.loc['5', 'pickup_method'] == 'Other <recorded>'
    pd.testing.assert_frame_equal(quotes, before)


def test_complete_briefing_keeps_all_payouts_after_view_only_search(real_data, tmp_path):
    quotes, prep, _ = real_data
    result = analyze(quotes, prep, ['2025_3Q'], ['MEX'], 200)
    shown = recent_provider_rows(result, query='MoneyGram')
    assert 0 < len(shown) < 46
    text = export_briefing(result, tmp_path).read_text(encoding='utf-8')
    tables = [t for t in Tables(text).tables if t and 'Recipient payout method' in t[0]]
    assert tables, 'Complete export has no recipient payout column'
    header, *rows = tables[-1]
    exported = {r[header.index('service_id')]: r[header.index('Recipient payout method')] for r in rows}
    expected = result.provider_details.set_index('service_id').pickup_method.to_dict()
    assert len(rows) == 46
    assert exported == expected


def test_briefing_escapes_payout_text_and_preserves_missing(quotes, prep, tmp_path):
    quotes = quotes.copy(deep=True)
    quotes['pickup_method'] = ['Cash', 'Bank account', pd.NA, 'Mobile wallet',
                               'Own/partner Bank account', '<script>unsafe</script>']
    result = analyze(quotes, prep, [], [], 200)
    text = export_briefing(result, tmp_path).read_text(encoding='utf-8')
    tables = [t for t in Tables(text).tables if t and 'Recipient payout method' in t[0]]
    assert tables, 'Briefing omits payout information'
    header, *rows = tables[-1]
    cells = {r[header.index('service_id')]: r[header.index('Recipient payout method')] for r in rows}
    assert cells['2'] == 'Unavailable'
    assert cells['5'] == '<script>unsafe</script>'
    assert '<script>unsafe</script>' not in text


def test_dashboard_shows_payout_beside_each_matching_quote():
    app = AppTest.from_file(str(APP), default_timeout=90).run()
    app.button(key='update').click().run()
    assert not app.exception
    tables = [item.value for item in app.dataframe
              if 'Recipient payout method' in item.value.columns and len(item.value) == 46]
    assert tables, 'Provider evidence has no payout column beside the 46 Mexico quotes'
    expected = {'Cash': 31, 'Bank account': 14, 'Own/partner Bank account': 1}
    assert tables[-1]['Recipient payout method'].value_counts().to_dict() == expected
    result = app.session_state['analysis_session'].last_successful_results
    assert result.corridor_summary.iloc[0].median_total_cost == pytest.approx(4.485)
