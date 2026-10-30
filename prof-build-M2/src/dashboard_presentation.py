"""Presentation-only views of executed results; never changes analytical tables."""
import math
import numpy as np
import pandas as pd
from .contracts import ScoringWeights, validate_amount_weights, period_key

COMMUNITY_MODE = 'Community campaign priority'
COST_MODE = 'Cost & disclosure'
MODES = (COMMUNITY_MODE, COST_MODE)
POOLING = ('Corridor summaries pool eligible quotes across selected quarters. Quarterly charts calculate each quarter separately. '
           'A pooled median is not the average of quarterly medians: quarters with more eligible quotes contribute more observations. '
           'Quote counts are not customers, transaction volumes, or market-share weights.')
DIRECTION = 'Higher scores reflect higher relative sampled costs and/or more quotes flagged non-transparent; community mode also includes documented relevance. Scores do not automatically recommend a campaign or provider.'


def default_weights(mode):
    if mode not in MODES:
        raise ValueError('Choose a valid scoring mode')
    return ScoringWeights(2 / 3, 1 / 3, 0) if mode == COST_MODE else ScoringWeights()


def validate_mode_weights(mode, weights):
    if mode not in MODES:
        raise ValueError('Choose a valid scoring mode')
    validate_amount_weights(200, weights)
    if any(v > 1 for v in (weights.cost, weights.transparency, weights.relevance)):
        raise ValueError('Each weight must be between 0 and 1')
    if mode == COST_MODE and weights.relevance != 0:
        raise ValueError('Cost & disclosure excludes community relevance; its weight must be zero')


def quarter_label(p):
    return f'{p[:4]} Q{p[5]}'


def pretty(value, decimals=3, suffix=''):
    return 'Unavailable' if pd.isna(value) else f'{value:.{decimals}f}{suffix}'


def disclosure_text(no, total, share):
    return f'{int(no)} / {int(total)} ({100 * share:.6f}%)' if total > 0 and pd.notna(share) else 'Unavailable'


def comparison_table(results):
    df = results.corridor_summary
    return pd.DataFrame({
        'Receiving country': df.receiving_country,
        'Median total cost (%)': df.median_total_cost.map(lambda v: pretty(v, 3)),
        'Eligible cost quotes': df.observations,
        'Flagged / total quotes (%)': [disclosure_text(r.non_transparent_quotes, r.total_quotes, r.non_transparent_quote_share) for r in df.itertuples()],
        'Score': df.campaign_priority_score.map(lambda v: pretty(v, 6)),
        'Scoring status': df.unscored_reasons.map(lambda reasons: '; '.join(reasons) if reasons else 'Available'),
    }).reset_index(drop=True)


def score_contributions(results):
    components = [('cost', 'Relative cost'), ('transparency', 'Non-transparent quote share')]
    if results.metadata.scoring_mode == COMMUNITY_MODE:
        components.append(('relevance', 'Documented community relevance'))
    records = []
    for row in results.corridor_summary.itertuples():
        for component, label in components:
            value = getattr(row, component + '_normalized')
            weight = getattr(results.metadata.weights, component)
            records.append({'Country': row.receiving_country, 'Component': label, 'Component value': value, 'Weight': weight,
                            'Contribution': 0.0 if weight == 0 else weight * value})
    return pd.DataFrame(records, columns=['Country', 'Component', 'Component value', 'Weight', 'Contribution'])


def current_warnings(results):
    df = results.corridor_summary
    messages = []
    if df.empty:
        return ['No matching quotes. Choose another destination or survey period, then Update analysis.']
    if df.median_total_cost.notna().sum() < 2:
        messages.append('Relative cost unavailable: at least two selected corridors with valid median costs are required. Add a receiving country or change periods. A positive cost weight leaves the score unavailable; a zero cost weight contributes zero without filling the missing component.')
    for row in df.itertuples():
        if pd.isna(row.median_total_cost):
            messages.append(f'{row.receiving_country}: no eligible total costs for this basket. Try another period or basket; missing costs are not zero.')
        if 'Missing documented community relevance' in row.unscored_reasons:
            fields = [('relevance_rating', 'rating'), ('relevance_rationale', 'rationale'), ('relevance_evidence_source', 'evidence source'), ('relevance_evidence_date', 'evidence date')]
            missing = ', '.join(label for attr, label in fields if pd.isna(getattr(row, attr)))
            messages.append(f'{row.receiving_country}: score unavailable. Complete the community {missing}, load the CSV and Update analysis. Descriptive evidence remains visible. You may explicitly choose Cost & disclosure for a score without community relevance; the app will not switch modes for you.')
    return messages


def small_sample_messages(results, threshold=5):
    return [f'Small sample: {r.receiving_country} - {r.channel_category}: {r.observations} eligible cost quotes out of {r.total_quotes} matching quotes. Treat this median cautiously.'
            for r in results.channel_summary.itertuples() if 0 < r.observations <= threshold]


def period_grid(results):
    """Calendar positions for display only, including explicitly classified gaps."""
    m = results.metadata
    if not m.resolved_periods:
        return pd.DataFrame()
    lookup = {(r.destination_code, r.reporting_period): r for r in results.period_summary.itertuples()}
    records = []
    for destination in m.resolved_destinations:
        for n in range(period_key(m.resolved_periods[0]), period_key(m.resolved_periods[-1]) + 1):
            p = f'{n // 4:04}_{n % 4 + 1}Q'
            row = lookup.get((destination.destination_code, p))
            common = 'No survey data' if p not in m.available_periods else 'Not selected' if p not in m.resolved_periods else None
            cost_status = common or ('No data' if row is None or pd.isna(row.median_total_cost) else 'Observed')
            disclosure_status = common or ('No data' if row is None or pd.isna(row.non_transparent_quote_share) else 'Observed')
            records.append({'Country': destination.destination_name, 'Code': destination.destination_code, 'Quarter': quarter_label(p), 'Period': p,
                            'Median total cost (%)': row.median_total_cost if row is not None and cost_status == 'Observed' else np.nan,
                            'Eligible cost quotes': int(row.observations) if row is not None else 0,
                            'Total quotes': int(row.total_quotes) if row is not None else 0,
                            'Flagged quotes': int(row.non_transparent_quotes) if row is not None else 0,
                            'Disclosure share': row.non_transparent_quote_share if row is not None and disclosure_status == 'Observed' else np.nan,
                            'Cost status': cost_status, 'Disclosure status': disclosure_status})
    return pd.DataFrame(records)


def cost_axis_range(values, scale='Start at zero'):
    finite = [float(v) for v in values if pd.notna(v) and math.isfinite(v)]
    if not finite:
        return None
    low, high = min(finite), max(finite)
    if scale == 'Start at zero':
        low, high = min(0, low), max(0, high)
    pad = (high - low or max(abs(high), 1)) * .08
    return [low - pad if low < 0 or scale != 'Start at zero' else 0, high + pad]


def trend_figure(results, metric='cost', scale='Start at zero'):
    import plotly.graph_objects as go
    grid = period_grid(results)
    fig = go.Figure()
    if grid.empty:
        return fig
    field = 'Median total cost (%)' if metric == 'cost' else 'Disclosure share'
    for destination in results.metadata.resolved_destinations:
        rows = grid.loc[grid.Code.eq(destination.destination_code)]
        y = [None if pd.isna(v) else float(v) for v in rows[field]]
        hover = ('%{customdata[0]}<br>%{customdata[1]}<br>Median total cost: %{y:.3f}%<br>Eligible quotes: %{customdata[2]}<extra></extra>' if metric == 'cost'
                 else '%{customdata[0]}<br>%{customdata[1]}<br>Non-transparent: %{customdata[4]} / %{customdata[3]}<br>Share: %{y:.6%}<extra></extra>')
        fig.add_trace(go.Scatter(x=list(range(len(rows))), y=y, name=destination.destination_name, mode='lines+markers', connectgaps=False,
                                 customdata=rows[['Country', 'Quarter', 'Eligible cost quotes', 'Total quotes', 'Flagged quotes']].to_numpy(), hovertemplate=hover))
    names = ', '.join(d.destination_name for d in results.metadata.resolved_destinations)
    if len(results.metadata.resolved_destinations) > 3:
        names = f'{len(results.metadata.resolved_destinations)} receiving countries (legend identifies each)'
    title = 'Quarterly median total cost (%)' if metric == 'cost' else 'Quarterly non-transparent quote share (%)'
    labels = grid.loc[grid.Code.eq(results.metadata.resolved_destinations[0].destination_code), 'Quarter'].tolist()
    step = max(1, math.ceil(len(labels) / 10))
    ticks = sorted(set(range(0, len(labels), step)) | {len(labels) - 1})
    fig.update_layout(title={'text': f'{title}<br>{names} | USD {results.metadata.transfer_amount_usd}', 'font': {'size': 17}},
                      xaxis={'tickmode': 'array', 'tickvals': ticks, 'ticktext': [labels[i] for i in ticks], 'title': 'Survey quarter'},
                      yaxis={'title': title, 'range': cost_axis_range(grid[field], scale) if metric == 'cost' else [0, 1], 'tickformat': '.3f' if metric == 'cost' else '.0%'},
                      height=440, margin={'t': 90, 'b': 60}, hovermode='closest', legend={'orientation': 'h', 'y': -0.25})
    return fig


def recent_provider_rows(results, query='', sort='Most recent selected records', ascending=False):
    df = results.provider_details.copy()
    if query.strip():
        mask = pd.Series(False, index=df.index)
        for col in ['provider', 'receiving_country', 'service_id', 'reporting_period']:
            mask |= df[col].astype(str).str.contains(query.strip(), case=False, regex=False, na=False)
        mask |= df.reporting_period.map(quarter_label).str.contains(query.strip(), case=False, regex=False, na=False)
        df = df.loc[mask].copy()
    fields = {'Total cost (%)': 'total_cost_pct', 'Transfer fee': 'transfer_fee', 'FX margin (%)': 'exchange_rate_margin', 'Provider': 'provider'}
    if sort in fields:
        return df.sort_values([fields[sort], 'reporting_period', 'collection_date', 'service_id'], ascending=[ascending, False, False, True], na_position='last', kind='stable')
    return df.sort_values(['reporting_period', 'collection_date', 'provider', 'receiving_country', 'service_id'], ascending=[False, False, True, True, True], na_position='last', kind='stable')


def channel_period_details(results, country, channel):
    rows = results.provider_details
    rows = rows.loc[rows.receiving_country.eq(country) & rows.channel_category.eq(channel)].copy()
    details = rows.groupby('reporting_period', sort=True).agg(eligible_quotes=('total_cost_pct', 'count'), matching_quotes=('service_id', 'size'), median_total_cost_pct=('total_cost_pct', 'median')).reset_index()
    return details, rows
