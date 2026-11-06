"""Local RemitRight LA dashboard; no notebook or Jupyter kernel required."""
from hashlib import sha256
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st

from src.contracts import CHANNELS, RELEVANCE, ScoringWeights, period_key
from src.dashboard_workflow import DashboardSession
from src.dashboard_presentation import (
    COMMUNITY_MODE, COST_MODE, MODES, POOLING, DIRECTION, default_weights,
    comparison_table, current_warnings, score_contributions, small_sample_messages,
    period_grid, trend_figure, recent_provider_rows, channel_period_details, quarter_label,
)
from src.load_data import load_data, load_preparation_metadata
from src.load_relevance import load_relevance, validate_relevance
from src.rendering import LIMITATIONS, ACCESS_CHECKLIST
from src.evidence_summaries import channel_cost_comparison

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data' / 'rpw_usa_clean.csv.gz'
EVIDENCE = ROOT / 'inputs' / 'community_relevance.csv'


def table(data, provider=False):
    """Display copies only; preserve numerical results and exported data."""
    out = data.copy(deep=True).astype(object)
    if provider:
        for col in ('exchange_rate_margin', 'total_cost_pct'):
            out.loc[out.transparent.eq('no'), col] = 'Unknown: non-transparent'
        out['fee_currency'] = out.fee_currency.where(out.fee_currency.notna(), 'Unknown currency')
        out['access_point'] = out.access_point.where(out.access_point.notna(), 'Unknown: missing value')
    if 'unscored_reasons' in out:
        out['unscored_reasons'] = out.unscored_reasons.map(lambda x: '; '.join(x) or 'None')
    out = out.where(out.notna(), 'Unavailable')
    # Arrow columns need one type. Preserve numeric columns when complete;
    # format only columns containing explanatory text on this display copy.
    for col in out:
        if out[col].map(lambda value: isinstance(value, str)).any():
            out[col] = out[col].map(lambda value: f'{value:.6g}' if isinstance(value, float) else str(value))
    labels = {
        'median_total_cost': 'Median total cost (%)',
        'cost_normalized': 'Relative cost (0 to 1)',
        'non_transparent_quote_share': 'Non-transparent quote share (0 to 1)',
        'observations': 'Eligible cost quotes',
        'total_quotes': 'Total quotes',
        'campaign_priority_score': 'Campaign priority score',
        'median_transfer_fee': 'Median transfer fee (currency units)',
        'median_exchange_margin': 'Median FX margin (%)',
        'total_cost_pct': 'Total cost (%)',
        'exchange_rate_margin': 'FX margin (%)',
        'transfer_fee': 'Transfer fee (currency units)',
    }
    out = out.rename(columns={c: labels.get(c, c.replace('_', ' ').capitalize()) for c in out})
    st.dataframe(out, hide_index=True, width='stretch')


def evidence_controls(session):
    with st.sidebar.expander('Community evidence', expanded=False):
        st.caption('Use the project CSV or upload a CSV. Loading does not overwrite files. Ratings are researcher judgments, never inferred.')
        st.download_button('Download community CSV template', ','.join(RELEVANCE) + '\n', file_name='community_relevance_template.csv', mime='text/csv', key='evidence_template', on_click='ignore')
        st.caption('Required columns: destination_code, relevance_rating, rationale, evidence_source, evidence_date. Ratings: 0 to 5; dates: YYYY-MM-DD.')
        source = st.radio('Evidence source', ['Project CSV', 'Upload CSV', 'No community evidence'], key='evidence_source')
        upload = st.file_uploader('Community evidence CSV', type=['csv'], key='evidence_upload') if source == 'Upload CSV' else None
        try:
            if source == 'Project CSV':
                exists = EVIDENCE.exists()
                raw = EVIDENCE.read_bytes() if exists else b''
                token = (source, sha256(raw).hexdigest() if exists else 'missing')
                if not exists:
                    st.caption('The optional project CSV is absent. Continuing with no community evidence, matching the notebook.')
            elif source == 'No community evidence':
                raw = (','.join(RELEVANCE) + '\n').encode('utf-8')
                token = (source, sha256(raw).hexdigest())
            else:
                raw = upload.getvalue() if upload else None
                token = (source, sha256(raw).hexdigest()) if raw is not None else None
        except OSError as exc:
            raw, token = None, None
            st.error(f'Cannot read community evidence: {exc}')
        if raw and source == 'Upload CSV':
            try:
                preview = pd.read_csv(BytesIO(raw), dtype=str, keep_default_na=False)
                st.caption(f'Chosen upload: {upload.name}. Preview only; not applied until loaded and analysis updated. Showing up to 10 of {len(preview)} rows.')
                if preview.empty:
                    st.info('This CSV has a header but no evidence rows. No ratings will be inferred; community relevance remains unavailable.')
                else:
                    st.dataframe(preview.head(10), hide_index=True)
            except (ValueError, UnicodeError) as exc:
                st.error(f'CSV preview could not be read: {exc}')
        if 'relevance' not in st.session_state:
            st.session_state.relevance = pd.DataFrame(columns=['destination_code', 'relevance_rating', 'rationale', 'evidence_source', 'evidence_date'])
            st.session_state.evidence_token = None
            st.session_state.evidence_error = None
            # Match notebook startup: load the project CSV once, even when header-only.
            if source == 'Project CSV' and raw is not None:
                try:
                    st.session_state.relevance = load_relevance(EVIDENCE, set(session.quotes.destination_code))
                    st.session_state.evidence_token = token
                except (ValueError, OSError) as exc:
                    st.session_state.evidence_error = str(exc)
        if st.button('Load community evidence', key='load_evidence'):
            st.session_state.pop('export_artifact', None)
            try:
                if raw is None:
                    raise ValueError('Choose a CSV file first.')
                rel = (load_relevance(EVIDENCE, set(session.quotes.destination_code)) if source == 'Project CSV'
                       else validate_relevance(pd.read_csv(BytesIO(raw), dtype=str, keep_default_na=False), set(session.quotes.destination_code)))
                st.session_state.relevance = rel
                st.session_state.evidence_token = token
                st.session_state.evidence_error = None
            except (ValueError, OSError, UnicodeError) as exc:
                st.session_state.evidence_token = None
                st.session_state.evidence_error = str(exc)
        ready = token is not None and token == st.session_state.evidence_token
        if st.session_state.evidence_error:
            st.error(st.session_state.evidence_error)
        if not ready:
            st.warning('Load the selected community evidence before updating or exporting.')
        else:
            st.caption(f'{len(st.session_state.relevance)} evidence rows loaded. Use Load community evidence after editing the CSV.')
    if ready:
        st.sidebar.caption(f'Loaded evidence: {source}, {len(st.session_state.relevance)} rows. Applied to results only after Update analysis.')
    else:
        st.sidebar.caption('Evidence pending or invalid. Load a valid CSV, or choose No community evidence and load that explicit choice.')
    return ready


def raw_table(data):
    if data.empty:
        st.info('No rows for this view. No values have been substituted for missing evidence.')
        return
    out = data.copy()
    for col in out:
        if pd.api.types.is_datetime64_any_dtype(out[col]):
            out[col] = out[col].dt.strftime('%Y-%m-%d').where(out[col].notna(), 'Unavailable')
        if col == 'unscored_reasons':
            out[col] = out[col].map(lambda values: '; '.join(values) or 'None')
    st.caption('Underlying precision is retained. Missing cells are unavailable, not zero. Tables can be sorted by clicking a column heading.')
    st.dataframe(out, hide_index=True, width='stretch')


def period_summary_text(results):
    m = results.metadata
    if not m.resolved_periods:
        return 'No selected survey quarters'
    first, last = map(quarter_label, (m.resolved_periods[0], m.resolved_periods[-1]))
    observed = results.period_summary.reporting_period.nunique()
    return f'{first} to {last} | {len(m.resolved_periods)} selected survey quarters; {observed} observed with matching quotes'


def provider_table(rows):
    if rows.empty:
        st.info('No historical sampled quotes match this view-only search or drill-down. The saved analysis is unchanged.')
        return
    out = rows.copy()
    out['reporting_period'] = out.reporting_period.map(quarter_label)
    out['collection_date'] = out.collection_date.dt.strftime('%Y-%m-%d')
    out['disclosure_status'] = out.transparent.map({'yes': 'Transparent', 'no': 'Flagged non-transparent'})
    visible = ['provider', 'receiving_country', 'reporting_period', 'collection_date', 'channel_category', 'total_cost_pct', 'disclosure_status', 'transfer_fee', 'fee_currency', 'exchange_rate_margin']
    # Formatting helper preserves original eligibility and labels undisclosed cost/margin.
    display = out[visible + ['transparent', 'access_point']].copy()
    for col in ['total_cost_pct', 'exchange_rate_margin']:
        display[col] = display[col].astype(object)
        display.loc[display.transparent.eq('no'), col] = 'Unknown: non-transparent'
    table(display.drop(columns=['transparent', 'access_point']))
    with st.expander('Technical identifiers and exact provider values'):
        raw_table(rows)


def show_results(results):
    m = results.metadata
    st.subheader('Saved analysis')
    names = [d.destination_name for d in m.resolved_destinations]
    country_summary = ', '.join(names) if len(names) <= 3 else f'{len(names)} receiving countries'
    st.write(f'USA to {country_summary} | USD {m.transfer_amount_usd} | {period_summary_text(results)}')
    weight_text = f'cost {m.weights.cost:.12g}, disclosure {m.weights.transparency:.12g}'
    if m.scoring_mode == COMMUNITY_MODE:
        weight_text += f', community {m.weights.relevance:.12g}'
    st.write(f'Executed mode: **{m.scoring_mode}**. Applicable weights: {weight_text}.')
    counts = st.columns(3)
    counts[0].metric('Matching quotes', m.matching_row_count)
    counts[1].metric('Eligible cost quotes', int(results.corridor_summary.observations.sum()))
    counts[2].metric('Non-transparent quotes', int(results.corridor_summary.non_transparent_quotes.sum()))
    st.caption('Historical sampled services, not customers, transaction volumes, or market shares. Non-transparent and missing costs are excluded from cost medians, not from disclosure denominators.')
    if m.matching_row_count == 0:
        st.info('No matching quotes for these receiving countries and periods. Choose another selection and Update analysis; no cost or score is available.')
    else:
        summary, trends, channels, fees, providers = st.tabs(['Corridor comparison', 'Survey quarters', 'Channels', 'Fees and FX margins', 'Provider evidence'])
        with summary:
            st.caption('Pooled actual costs and counts come first. Missing scores do not erase descriptive price evidence.')
            st.dataframe(comparison_table(results), hide_index=True, width='stretch')
            if results.corridor_summary.campaign_priority_score.isna().any():
                st.info('Some scores are unavailable. See Scoring status and the input guidance below; missing components remain unavailable.')
            for message in current_warnings(results):
                st.info(message)
            absent = [d.destination_name for d in m.resolved_destinations if d.destination_code not in set(results.corridor_summary.destination_code)]
            if absent:
                st.info('No matching quotes in the selected periods for: ' + ', '.join(absent))
            st.caption(DIRECTION)
            with st.expander('Score components, contributions and exact calculated fields'):
                st.write('Contribution = applicable weight times component. A missing zero-weight component contributes zero but its component value stays unavailable. Positive-weight missing components leave the total score unavailable.')
                st.write('Relative cost uses all available USA-origin corridors for the selected periods and basket, before displayed-country filtering. At least two valid reference medians are required. Equal medians normalize to zero; actual costs are unchanged.')
                st.write(vars(m.cost_reference) if m.cost_reference is not None else 'Reference metadata unavailable.')
                raw_table(score_contributions(results))
                raw_table(results.corridor_summary)
        with trends:
            st.caption(POOLING)
            scale = st.radio('Cost chart scale', ['Start at zero', 'Focus on variation'], horizontal=True, key='cost_scale')
            st.caption('Scale changes only this chart. Focus on variation uses a tighter axis and can magnify apparent changes. All quarterly points remain. Offline charts use the zero-inclusive scale.')
            grid = period_grid(results)
            if grid['Median total cost (%)'].lt(0).any():
                st.info('Valid negative costs are present. The zero-inclusive scale extends below zero so these observations are not clipped.')
            st.plotly_chart(trend_figure(results, 'cost', scale), width='stretch', key='cost_trend')
            st.caption('Hover for country, quarter, actual median cost percentage and eligible quote count. One observed point does not establish a trend.')
            st.subheader('Disclosure trend')
            st.caption('Flagged quotes / all matching quotes, displayed as a percentage. A zero means no sampled quote was flagged; it is not proof about every service in the market.')
            st.plotly_chart(trend_figure(results, 'disclosure'), width='stretch', key='disclosure_trend')
            st.caption('Gaps are never filled with zero or interpolated. No survey data = absent globally; Not selected = available but excluded; No data = no usable value for this destination and metric.')
            with st.expander('Quarter-by-quarter values and gap classifications'):
                display = grid.copy()
                display['Non-transparent share (%)'] = 100 * display.pop('Disclosure share')
                table(display.drop(columns=['Code', 'Period']))
                raw_table(results.period_summary)
        with channels:
            st.caption('Internet-only, Counter-only, Mixed and Other/unknown remain separate. These are different sampled services and periods; comparisons do not show that switching causes savings or identify a best channel.')
            with st.expander('Internet-access discussion checklist'):
                st.caption('Discuss with the sender before encouraging a switch. These are questions, not inferred personal facts; this app stores no answers.')
                for question in ACCESS_CHECKLIST:
                    st.markdown('- ' + question)
            columns = ['receiving_country', 'channel_category', 'median_total_cost', 'observations', 'total_quotes', 'non_transparent_quotes', 'non_transparent_quote_share']
            channel_display = results.channel_summary[columns].copy()
            channel_display['non_transparent_quote_share'] *= 100
            channel_display = channel_display.rename(columns={'non_transparent_quote_share': 'Non-transparent quotes (%)'})
            table(channel_display)
            st.subheader('Channel median difference in dollars')
            st.caption('Counter-only minus Internet-only, in percentage points and USD-equivalent dollars for the selected basket. Positive means counter services have the higher median; this is not guaranteed individual savings.')
            table(channel_cost_comparison(results))
            for message in small_sample_messages(results):
                st.warning(message)
            with st.expander('Channel period and provider details (view-only drill-down)'):
                st.caption('These controls affect only this evidence view, not the saved analysis, score or complete HTML export.')
                country = st.selectbox('Channel receiving country', sorted(results.channel_summary.receiving_country.unique()), key='channel_country')
                channel = st.selectbox('Channel category', CHANNELS, key='channel_category')
                details, rows = channel_period_details(results, country, channel)
                if rows.empty:
                    st.info('No observations for this channel and receiving country in the saved selection. No median is fabricated.')
                else:
                    details['reporting_period'] = details.reporting_period.map(quarter_label)
                    table(details)
                    provider_table(rows)
        with fees:
            st.caption('Transfer fees are in the stated fee currency; exchange-rate margins are percentages. Each has its own eligible observation count. Separately calculated medians cannot simply be added to reproduce median total cost, even after converting units.')
            table(results.fee_summary)
            table(results.fx_margin_summary)
        with providers:
            st.caption(f'Historical sampled quotes: all {m.matching_row_count} matching service rows are accessible. Initial order: most recent selected quarter, collection date, then provider/country/service ID. Search and sort affect only this table; complete exports retain all matching rows.')
            query = st.text_input('Search provider evidence', placeholder='Provider, receiving country, quarter or service ID', key='provider_search')
            sort = st.selectbox('Provider table ordering', ['Most recent selected records', 'Total cost (%)', 'Transfer fee', 'FX margin (%)', 'Provider'], key='provider_sort')
            ascending = st.checkbox('Ascending order for the selected field', key='provider_ascending')
            rows = recent_provider_rows(results, query, sort, ascending)
            st.caption(f'Showing {len(rows)} of {m.matching_row_count} matching quotes. Missing costs are unavailable, not free. Row order is not a recommendation.')
            provider_table(rows)
    with st.expander('Complete executed settings'):
        st.write({'Origin': 'USA', 'Scoring mode': m.scoring_mode,
                  'Requested destinations': list(m.requested_destination_codes) or 'All available',
                  'Resolved destinations': [f'{d.destination_name} ({d.destination_code})' for d in m.resolved_destinations],
                  'Requested periods': list(m.requested_periods) or 'All available', 'Resolved periods': list(m.resolved_periods),
                  'Transfer basket (USD)': m.transfer_amount_usd,
                  'Exact weights': {'cost': repr(m.weights.cost), 'disclosure': repr(m.weights.transparency), 'community': repr(m.weights.relevance)},
                  'Actual collection date range': f'{m.collection_date_min} to {m.collection_date_max}' if m.collection_date_min is not None else 'Unavailable'})
    with st.expander('Community evidence applied to displayed results'):
        st.caption('This is the executed evidence snapshot. A newly chosen upload or loaded CSV is not applied until Update analysis succeeds.')
        if m.validated_relevance_snapshot:
            raw_table(pd.DataFrame([vars(r) for r in m.validated_relevance_snapshot]))
        else:
            st.info('No community evidence was applied. Descriptive costs and disclosure remain available; a positive community weight requires complete documented evidence for a composite score.')
        if m.scoring_mode == COST_MODE:
            st.write('Any evidence shown here is descriptive only. Community relevance is excluded from this score.')
    with st.expander('Methodology and score interpretation'):
        st.write(POOLING)
        st.write(DIRECTION)
        st.write('Cost normalization uses a shared reference of all available USA-origin corridors for the selected periods and basket. Country display filters do not change the bounds; periods, basket and data version can. Disclosure is the fraction flagged non-transparent. Community relevance uses the documented 0-5 input divided by 5; no ratings are inferred.')
        st.write({'Cost reference': vars(m.cost_reference) if m.cost_reference is not None else None, 'Data version (prepared SHA-256)': m.preparation.prepared_sha256})
    with st.expander('Historical-data limitations and attribution'):
        st.write(LIMITATIONS)
        st.write('Remittance Prices Worldwide, World Bank Group | CC BY 4.0. Adaptation: cleaned USA quotes and derived summaries.')
    with st.expander('Detailed preparation provenance and validation'):
        p = m.preparation
        st.write({'Source workbook': p.source_filename, 'Source SHA-256': p.source_sha256, 'Prepared file': p.prepared_filename, 'Prepared SHA-256': p.prepared_sha256, 'Prepared at (UTC)': str(p.prepared_at_utc)})
        for label, items in [('Validation', p.validation_summary), ('Reference comparison', p.change_summary), ('Preparation warnings', p.preparation_warnings), ('Runtime warnings', m.runtime_validation_warnings)]:
            st.write(label)
            for item in items:
                st.write(item)
            if not items:
                st.caption('None.')


def reset_mode_weights():
    weights = default_weights(st.session_state.scoring_mode)
    st.session_state.cost_weight = weights.cost
    st.session_state.transparency_weight = weights.transparency
    st.session_state.relevance_weight = weights.relevance
    st.session_state.pop('export_artifact', None)


def main():
    st.set_page_config(page_title='RemitRight LA', page_icon=':material/currency_exchange:', layout='wide')
    st.title('RemitRight LA')
    st.write('Historical U.S. remittance evidence for staff-selected outreach research. Mexico is illustrative, not a recommendation.')
    st.caption('Historical sampled quotes, not live prices. Check current prices and community relevance before publishing.')
    if 'analysis_session' not in st.session_state:
        try:
            with st.spinner('Validating and loading prepared data...'):
                prep = load_preparation_metadata(str(DATA) + '.validation.json', DATA)
                st.session_state.analysis_session = DashboardSession(load_data(DATA, prep), prep)
        except (ValueError, OSError) as exc:
            st.error(str(exc))
            st.stop()
    session = st.session_state.analysis_session
    names = session.quotes[['destination_code', 'destination_name']].drop_duplicates().set_index('destination_code').destination_name.to_dict()
    periods = sorted(session.quotes.period.unique(), key=period_key, reverse=True)
    with st.sidebar:
        st.header('Selected controls')
        st.caption('Destinations are receiving countries. Origin is USA. An empty list means all available countries.')
        destinations = st.multiselect('Destinations', sorted(names, key=lambda c: (names[c], c)), default=['MEX'], format_func=lambda c: f'{names[c]} ({c})', key='destinations')
        st.caption('Choose survey quarters. Empty means all available quarters; missing survey quarters remain gaps.')
        selected_periods = st.multiselect('Survey periods', periods, default=[periods[0]], format_func=quarter_label, key='periods')
        st.caption('USD 200 or 500 selects the transfer-cost basket; it does not filter by provider fees.')
        amount = st.selectbox('Transfer amount (USD)', [200, 500], key='amount')
        mode = st.selectbox('Scoring mode', MODES, index=MODES.index(COST_MODE), key='scoring_mode', on_change=reset_mode_weights)
        action = st.container()
        st.caption('Update applies these selections. Saved-result settings remain unchanged until a successful update.')
        st.caption('Weights express relative importance in the selected score, not fees charged to the sender. Switching modes restores that mode\'s defaults.')
        defaults = default_weights(mode)
        with st.expander('Advanced scoring settings'):
            st.write('Each weight must be 0 to 1 and applicable weights must sum to 1 (tolerance 1e-9). Inputs are never silently normalized. Default cost/disclosure weights in the two-component mode are exactly 2/3 and 1/3.')
            cost = st.number_input('Cost weight', min_value=0.0, max_value=1.0, value=defaults.cost, step=0.01, format='%.12f', key='cost_weight')
            disclosure = st.number_input('Disclosure weight', min_value=0.0, max_value=1.0, value=defaults.transparency, step=0.01, format='%.12f', key='transparency_weight')
            relevance = st.number_input('Community relevance weight', min_value=0.0, max_value=1.0, value=defaults.relevance, step=0.01, format='%.12f', key='relevance_weight') if mode == COMMUNITY_MODE else 0.0
            st.caption(f'Applicable weight sum: {cost + disclosure + relevance:.12g}. No redistribution.')
        st.write(f'Selected mode: **{mode}**')
        st.caption(f'Applicable weights: cost {cost:.12g}; disclosure {disclosure:.12g}' + (f'; community {relevance:.12g}' if mode == COMMUNITY_MODE else '; community excluded'))
        if mode == COST_MODE:
            st.caption('No community evidence is required for this score. Optional valid evidence remains available separately.')
        st.caption('Community CSV: download the header-only template below, fill its five existing fields, upload and Load, then Update. No ratings are inferred.')
    evidence_ready = evidence_controls(session)
    args = (selected_periods, destinations, amount, ScoringWeights(cost, disclosure, relevance), st.session_state.relevance)
    with action:
        submitted = st.button('Update analysis', type='primary', key='update', disabled=not evidence_ready)
    if submitted:
        st.session_state.pop('export_artifact', None)
        try:
            with st.spinner('Updating analysis...'):
                session.analyze(*args, scoring_mode=mode)
        except (ValueError, TypeError) as exc:
            st.error(f'Analysis could not be updated: {exc}. Correct the settings and Update analysis. Export is blocked.')
    current = evidence_ready and session.matches(*args, scoring_mode=mode)
    if session.last_successful_results is not None and session.current_run_valid:
        if not current:
            st.warning('Selected controls or evidence differ from the displayed results. Update analysis to apply them; export is blocked until the results match.')
        show_results(session.last_successful_results)
    else:
        st.info('Choose settings, then click Update analysis to display results.')
    st.subheader('Offline HTML briefing')
    st.caption('Create and download the exact saved analysis, with mode, weights, applied evidence, complete provider rows and embedded static charts. View-only search, sort and chart scale do not change the export.')
    if st.button('Create HTML briefing', key='export', disabled=not current):
        try:
            path = session.export(*args, output_dir=ROOT / 'exports', scoring_mode=mode)
            st.session_state.export_artifact = (path.name, path.read_bytes())
            st.success(f'Briefing created locally: {path.name}')
        except (ValueError, OSError) as exc:
            st.session_state.pop('export_artifact', None)
            st.error(str(exc))
    if current and 'export_artifact' in st.session_state:
        name, content = st.session_state.export_artifact
        st.download_button('Download HTML briefing', content, file_name=name, mime='text/html', key='download', on_click='ignore')


if __name__ == '__main__':
    main()
