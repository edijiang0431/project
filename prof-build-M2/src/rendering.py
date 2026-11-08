"""Shared formatting and static figures. No analytical aggregation or ranking."""
import base64
from html import escape
from io import BytesIO
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .contracts import *
from .dashboard_presentation import (COMMUNITY_MODE, COST_MODE, POOLING, DIRECTION, comparison_table, current_warnings, score_contributions, small_sample_messages, cost_axis_range)
from .evidence_summaries import channel_cost_comparison, cost_coverage, key_findings, fee_distribution, service_cost_breakdown

EXPLANATION = '''Scores support staff judgment; staff decide priorities. Relative cost uses all available USA-origin corridors for the selected periods and basket, before filtering displayed countries. Changing only displayed countries does not change that reference. Bounds may change with periods, basket or data version. At least two valid reference medians are required. Equal medians normalize to zero, not zero actual cost. Positive-weight components are required; a missing zero-weight component contributes zero without redistribution. Community evidence is a documented researcher rating or an optional ACS population-share proxy. The latter is not remittance participation or community need; its source, survey period, point estimates and margins of error appear in the applied evidence snapshot.'''
LIMITATIONS = '''Historical sampled quotes are not guaranteed live prices. Survey composition changes. Quote counts are not customers or market shares. Pooled-quarter medians use every eligible quote, so quarters with more eligible quotes contribute more observations; this is not customer weighting. No persistence score or causal channel claim is made. Shared-reference normalization still depends on periods, basket and data version. Community relevance is subjective documented judgment. Check current prices and community relevance before publishing. Median fees and FX margins have different units and observation sets and cannot simply be added. One chart point implies no direction. Missing costs remain unavailable; non-transparent costs/margins are unknown, even when reported as zero.'''
STYLE = '''body{font:15px/1.5 system-ui,sans-serif;color:#182d36;background:#f4f5f0;margin:0}main{max-width:1380px;margin:auto;padding:32px}h1{font-size:38px;margin-bottom:0;color:#174e49}h2{margin-top:34px;border-top:2px solid #cadbd5;padding-top:18px}h3{color:#174e49}p{max-width:1050px}.eyebrow{letter-spacing:.12em;text-transform:uppercase;color:#63756e;font-size:12px}.notice{border-left:4px solid #b07134;background:#fff8eb;padding:14px}table{border-collapse:collapse;width:100%;font-size:12px;background:white}th,td{border-bottom:1px solid #dde3df;padding:8px;text-align:left;vertical-align:top}th{background:#e1ece7;position:sticky;top:0}td{max-width:350px;overflow-wrap:anywhere}.table-wrap{overflow:auto;max-height:650px}img{width:100%;max-width:1200px}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#e7ece6;padding:16px;font-size:12px}a{color:#17665d}@page{size:landscape;margin:10mm}@media print{body{background:white;font-size:10px}main{padding:0}h1{font-size:26px}.table-wrap{overflow:visible;max-height:none}th{position:static}table{font-size:7px;table-layout:fixed}th,td{padding:4px;overflow-wrap:anywhere;word-break:normal}img{max-height:470px;object-fit:contain}h2,h3{break-after:avoid}tr{break-inside:avoid}pre{font-size:8px}}'''

ACCESS_CHECKLIST = (
    'Does the sender have a reliable Internet connection for completing and confirming the transfer?',
    'Can the sender use a trusted device and a secure connection, and protect login details?',
    'Can the sender meet the chosen service\'s payment, identification and recipient-access requirements?',
)

def access_checklist_html():
    return '<h3>Internet-access discussion checklist</h3><p>Ask the sender before encouraging a channel switch. These are community-validation questions, not facts inferred from price quotes; record no personal answers in this app.</p><ul>' + ''.join('<li>' + escape(item) + '</li>' for item in ACCESS_CHECKLIST) + '</ul>'

def quarter_label(p):
    return f'{p[:4]} Q{p[5]}'

def timeline(results):
    m=results.metadata
    if not m.resolved_periods:
        return [],[]
    window = m.calendar_window or m.resolved_periods
    positions=list(range(period_key(window[0]),period_key(window[-1])+1))
    periods=[f'{n//4:04}_{n%4+1}Q' for n in positions]
    labels=[]
    for p in periods:
        label=quarter_label(p)
        if p not in m.available_periods: label+='\nNo survey data'
        elif p not in m.resolved_periods: label+='\nNot selected'
        labels.append(label)
    return periods,labels

def make_figures(results):
    validate_results(results)
    m=results.metadata
    if m.matching_row_count==0:
        return []
    periods,labels=timeline(results)
    fig,axes=plt.subplots(2,1,figsize=(12,7.6),sharex=True,layout='constrained')
    # Direct lookup of existing results only; missing render positions break lines.
    lookup={(r.destination_code,r.reporting_period):r for r in results.period_summary.itertuples()}
    for d in m.resolved_destinations:
        for ax,field in zip(axes,['median_total_cost','non_transparent_quote_share']):
            y=[getattr(lookup[(d.destination_code,p)],field) if (d.destination_code,p) in lookup and p in m.resolved_periods else np.nan for p in periods]
            ax.plot(range(len(periods)),y,marker='o',markersize=3,linewidth=1.3,label=f'{d.destination_name} ({d.destination_code})')
    axes[0].set_ylabel('Median total cost (%)')
    axes[1].set_ylabel('Non-transparent quote share (0–1)')
    from matplotlib.ticker import PercentFormatter
    axes[1].yaxis.set_major_formatter(PercentFormatter(xmax=1))
    axes[1].set_ylabel('Non-transparent quote share (%)')
    axes[1].set_ylim(-.03,1.03)
    bounds = cost_axis_range(results.period_summary.median_total_cost)
    if bounds is not None:
        axes[0].set_ylim(*bounds)
    for ax in axes:
        ax.grid(alpha=.2)
        ax.spines[['top','right']].set_visible(False)
    axes[0].set_title('Selected survey quarters • gaps are not zero • one point implies no direction',loc='left')
    names = ', '.join(d.destination_name for d in m.resolved_destinations) if len(m.resolved_destinations) <= 3 else f'{len(m.resolved_destinations)} receiving countries'
    axes[0].set_title(f'Quarterly median total cost (%) | {names} | USD {m.transfer_amount_usd}', loc='left', fontsize=10)
    axes[1].set_title('Non-transparent quote share (%) | missing periods remain gaps', loc='left', fontsize=10)
    step = max(1, int(np.ceil(len(periods) / 10)))
    ticks = sorted(set(range(0, len(periods), step)) | {len(periods)-1})
    axes[1].set_xticks(ticks,[labels[i] for i in ticks],rotation=45,ha='right',fontsize=8)
    handles,labs=axes[0].get_legend_handles_labels()
    fig.legend(handles,labs,loc='outside right upper',fontsize=7,ncol=1 if len(labs)<15 else 2)
    fig.set_facecolor('#f4f5f0')
    return [fig]

def fee_distribution_figures(results):
    rows = results.provider_details
    rows = rows.loc[rows.transparent.eq('yes') & rows.transfer_fee.notna()]
    figures = []
    for currency, group in rows.groupby('fee_currency', dropna=False, sort=True):
        countries, samples = [], []
        for name, country_rows in group.groupby('receiving_country', sort=True):
            countries.append(name)
            samples.append(country_rows.transfer_fee.to_numpy())
        fig, axis = plt.subplots(figsize=(9, max(2.4, .3 * len(countries) + 1.5)), layout='constrained')
        axis.boxplot(samples, orientation='horizontal', tick_labels=countries, showfliers=True)
        label = 'Unknown currency' if pd.isna(currency) else str(currency)
        axis.set_xlabel(f'Visible transfer fee ({label})')
        axis.set_title(f'Fee distribution | selected USD {results.metadata.transfer_amount_usd} basket | transparent nonmissing quotes')
        axis.grid(axis='x', alpha=.2)
        figures.append(fig)
    return figures


def figure_html(fig, alt='Selected-period median cost and non-transparent quote share; missing quarters break lines'):
    try:
        b=BytesIO(); fig.savefig(b,format='png',dpi=105)
        return '<img alt="' + escape(alt, quote=True) + '" src="data:image/png;base64,'+base64.b64encode(b.getvalue()).decode()+'">'
    finally:
        plt.close(fig)

def formatted_table(df, provider=False, exact=False):
    out=df.copy(deep=True)
    if provider:
        for c in ['exchange_rate_margin','total_cost_pct']:
            out[c]=out[c].astype(object)
            out.loc[out.transparent.eq('no'),c]='Unknown—non-transparent'
        for c in ['transfer_fee','exchange_rate_margin','total_cost_pct']:
            out[c]=out[c].map(lambda x:'Unknown—missing value' if pd.isna(x) else x)
        out['fee_currency']=out.fee_currency.fillna('Unknown currency')
        out['access_point']=out.access_point.fillna('Unknown—missing value')
    if 'fee_currency' in out:
        out['fee_currency']=out.fee_currency.fillna('Unknown currency')
    for c in out:
        if pd.api.types.is_datetime64_any_dtype(out[c]):
            out[c] = out[c].dt.strftime('%Y-%m-%d')
    # pandas escape=True protects all researcher/provider/source text.
    return '<div class="table-wrap">'+out.to_html(index=False,escape=True,na_rep='Unavailable',float_format=lambda v:format(v, '.17g' if exact else '.6g'))+'</div>'

def header_html(results,export_time=None):
    m=results.metadata
    requested_periods=', '.join(quarter_label(p) for p in m.requested_periods) or 'All available'
    requested_destinations=', '.join(m.requested_destination_codes) or 'All available'
    settings=[('Requested survey quarters',requested_periods),('Resolved survey quarters',', '.join(quarter_label(p) for p in m.resolved_periods)),('Requested destinations',requested_destinations),('Resolved destinations',', '.join(f'{d.destination_name} ({d.destination_code})' for d in m.resolved_destinations)),('Transfer amount',f'USD {m.transfer_amount_usd}'),('Weights',f'Cost {m.weights.cost:g} · Non-transparent share {m.weights.transparency:g} · Community relevance {m.weights.relevance:g}'),('Matching service rows',str(m.matching_row_count)),('Actual collection dates',f'{m.collection_date_min} to {m.collection_date_max}')]
    settings.insert(0, ('Scoring mode', m.scoring_mode))
    if m.calendar_window:
        settings.append(('Requested calendar window', quarter_label(m.calendar_window[0]) + ' to ' + quarter_label(m.calendar_window[-1]) + '; missing surveys remain gaps, no older-quarter backfill'))
    if m.cost_reference is not None:
        ref = m.cost_reference
        settings.append(('Cost normalization reference', f'{ref.scope}; {ref.valid_corridors} valid corridor medians; bounds {ref.minimum_pct} to {ref.maximum_pct} percent; selected USD {ref.transfer_amount_usd} basket'))
    settings.append(('Exact applicable weights', f'Cost {m.weights.cost!r}; disclosure {m.weights.transparency!r}' + (f'; community {m.weights.relevance!r}' if m.scoring_mode == COMMUNITY_MODE else '; community excluded (weight 0)')))
    if export_time is not None: settings.append(('Export timestamp (UTC)',str(export_time)))
    table='<table>'+''.join('<tr><th>'+escape(k)+'</th><td>'+escape(v)+'</td></tr>' for k,v in settings)+'</table>'
    p=m.preparation
    provenance=f'Source: {p.source_filename}\nSource SHA-256: {p.source_sha256}\nPrepared: {p.prepared_filename}\nPrepared SHA-256: {p.prepared_sha256}\nPreparation timestamp (UTC): {p.prepared_at_utc}'
    def bullet_list(items):
        return '<ul>'+''.join('<li>'+escape(x)+'</li>' for x in items)+'</ul>' if items else '<p>None.</p>'
    diagnostics='<details open><summary>Preparation provenance and validation</summary><pre>'+escape(provenance)+'</pre><h3>Preparation validation summary</h3>'+bullet_list(p.validation_summary)+'<h3>Comparison with retained reference baseline</h3>'+bullet_list(p.change_summary)+'<h3>Preparation warnings</h3>'+bullet_list(p.preparation_warnings)+'</details><h3>Runtime validation warnings</h3>'+bullet_list(m.runtime_validation_warnings)
    return '<p class="eyebrow">CHIRLA • Campaign research • Local briefing</p><h1>RemitRight LA</h1><p>Know what you really pay. Compare historical U.S. remittance evidence to support a staff-selected outreach shortlist. Mexico is illustrative, not a recommendation.</p><p class="notice">Historical quotes. Check current prices and community relevance before publishing. No personal member records are used.</p><h2>Current analysis & provenance</h2><p>Survey quarters, actual collection dates, preparation timestamp and export timestamp are distinct. Community evidence may be a researcher rating or an ACS community-size proxy; consult its rationale and source.</p>'+table+diagnostics

def body_sections(results,preview=None):
    validate_results(results)
    m=results.metadata
    sections=[header_html(results)]
    sections.append('<h2>Key findings and evidence readiness</h2><p>Descriptive price evidence can be useful even when community-informed prioritization is incomplete. No community evidence is inferred.</p>' + formatted_table(key_findings(results)))
    sections.append('<h2>Executed scoring mode</h2><p>'+escape(m.scoring_mode)+'</p><p>'+escape(DIRECTION)+'</p><p>'+escape(POOLING)+'</p>')
    if m.calendar_window:
        for destination in m.resolved_destinations:
            usable = results.period_summary.loc[results.period_summary.destination_code.eq(destination.destination_code), 'median_total_cost'].notna().sum()
            if usable < 2:
                sections.append('<p class="notice">' + escape(destination.destination_name) + ': fewer than two usable time points in the requested calendar window; no trend conclusion.</p>')
    if m.scoring_mode == COST_MODE:
        sections.append('<p>Community relevance is excluded from this score. Any supplied community evidence remains descriptive only. Relative cost uses the shared USA-corridor reference for the selected periods and basket.</p>')
    evidence = pd.DataFrame([vars(r) for r in m.validated_relevance_snapshot])
    sections.append('<details><summary>Applied community evidence snapshot</summary>' + (formatted_table(evidence, exact=True) if not evidence.empty else '<p>No community evidence was applied. Missing evidence is not inferred.</p>') + '</details>')
    sections.extend('<p class="notice">'+escape(message)+'</p>' for message in current_warnings(results))
    if m.matching_row_count==0:
        return sections+['<h2>No matching quotes</h2><p>Showing 0 of 0 service rows</p><h2>Limitations & attribution</h2><p>'+escape(LIMITATIONS)+'</p><p>Remittance Prices Worldwide, World Bank Group · CC BY 4.0. Adaptation: cleaned USA quotes and derived summaries.</p>']
    sections += ['<h2>Corridor comparison</h2><p>'+escape(EXPLANATION)+'</p>',formatted_table(comparison_table(results)), '<details><summary>Exact score components and calculated fields</summary>'+formatted_table(score_contributions(results), exact=True)+formatted_table(results.corridor_summary, exact=True)+'</details>','<h2>Fees & exchange-rate margins</h2><p>Fees: actual currency units. FX margins: percent, grouped separately by currency. Each metric has its own eligible observation count.</p>',formatted_table(results.fee_summary),formatted_table(results.fx_margin_summary),'<h2>Quarter-specific evidence</h2><p>Selected quarters with no usable value show gaps (No data). Rendering positions do not add analytical rows.</p>']
    sections += [figure_html(f) for f in make_figures(results)]
    sections += ['<h3>Usable-cost coverage for the selected basket</h3><p>Eligible costs / total matching quotes. Transparent missing costs are distinct from non-transparent exclusions. Missing surveys and zero-quote selections have unavailable coverage.</p>', formatted_table(cost_coverage(results))]
    sections += ['<h3>Visible-fee distribution</h3><p>Transparent nonmissing fees only, separated by actual fee currency. Zero visible fee does not mean zero total remittance cost. Service quotes are not customer weights. Box plots show the median, quartiles, whiskers and outlying quotes.</p>', formatted_table(fee_distribution(results))]
    sections += [figure_html(fig, 'Visible transfer-fee distribution separated by currency') for fig in fee_distribution_figures(results)]
    sections.extend('<p class="notice">'+escape(message)+'</p>' for message in small_sample_messages(results))
    observed={(r.destination_code,r.channel_category) for r in results.channel_summary.itertuples()}
    absent=''.join('<li>'+escape(f'{d.destination_name} ({d.destination_code}): {category} — no observations')+'</li>' for d in m.resolved_destinations for category in CHANNELS if (d.destination_code,category) not in observed)
    sections += [formatted_table(results.period_summary, exact=True),'<h2>Channel evidence</h2><p>Compare Internet-only and Counter-only side by side in the table. Mixed and Other/unknown remain separate. Four-category legend: '+', '.join(CHANNELS)+'. No median is fabricated for absent categories. Quotes are not customer-weighted and differences are not causal.</p>'+('<ul>'+absent+'</ul>' if absent else '<p>All four categories have observations for each resolved destination.</p>'), access_checklist_html(), formatted_table(results.channel_summary, exact=True),'<h2>Service-level provider evidence</h2>']
    sections.insert(-1, '<h3>Channel median difference in dollars</h3><p>Counter-only minus Internet-only, for the selected USD-equivalent basket. Positive means counter services have the higher median. Different historical quote groups are not guaranteed individual savings.</p>' + formatted_table(channel_cost_comparison(results)))
    n=m.matching_row_count if preview is None else min(preview,m.matching_row_count)
    details = service_cost_breakdown(results.provider_details)
    sections += [f'<p>Showing {n} of {m.matching_row_count} service rows. The HTML export contains the complete table. Unknown—non-transparent means the rate was undisclosed, not free.</p>', '<p>Service dollar breakdown: margin percentage times the selected USD-equivalent basket / 100, plus the fee only when its currency is USD. Component-derived and published totals remain separate; source rounding can explain small differences. Unknown or non-USD fee components are not converted or filled with zero.</p>', formatted_table(details if preview is None else details.iloc[:preview],provider=True,exact=True),'<h2>Limitations & attribution</h2><p>'+escape(LIMITATIONS)+'</p><p>Remittance Prices Worldwide, World Bank Group · <a href="https://datacatalog.worldbank.org/search/dataset/0037898/Remittance-Prices-Worldwide">Source</a> · <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>. Adaptation: cleaned USA quotes and derived summaries. Outputs stay local.</p>']
    return sections
