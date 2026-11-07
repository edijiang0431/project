"""Pure, non-mutating evidence calculations shared by all report views."""
import numpy as np
import pandas as pd


def channel_cost_comparison(results):
    records = []
    for destination in results.metadata.resolved_destinations:
        rows = results.channel_summary.loc[results.channel_summary.destination_code.eq(destination.destination_code)].set_index('channel_category')
        def value(category, column):
            return rows.loc[category, column] if category in rows.index else np.nan
        internet = value('Internet-only', 'median_total_cost')
        counter = value('Counter-only', 'median_total_cost')
        delta = counter - internet
        direction = ('Unavailable' if pd.isna(delta) else 'Counter-only higher' if delta > 0 else 'Internet-only higher' if delta < 0 else 'Equal medians')
        records.append(dict(destination_code=destination.destination_code, receiving_country=destination.destination_name,
            internet_median_pct=internet, counter_median_pct=counter,
            internet_eligible_quotes=value('Internet-only', 'observations'), counter_eligible_quotes=value('Counter-only', 'observations'),
            counter_minus_internet_percentage_points=delta,
            counter_minus_internet_usd=delta * results.metadata.transfer_amount_usd / 100,
            direction=direction))
    return pd.DataFrame(records, columns=['destination_code','receiving_country','internet_median_pct','counter_median_pct',
        'internet_eligible_quotes','counter_eligible_quotes','counter_minus_internet_percentage_points','counter_minus_internet_usd','direction'])


def cost_coverage(results):
    meta = results.metadata
    lookup = {(row.destination_code, row.reporting_period): row for row in results.period_summary.itertuples()}
    records = []
    for destination in meta.resolved_destinations:
        for period in meta.calendar_window or meta.resolved_periods:
            row = lookup.get((destination.destination_code, period))
            if period not in meta.available_periods:
                status = 'No survey data'
            elif period not in meta.resolved_periods:
                status = 'Not selected'
            elif row is None:
                status = 'No matching quotes'
            else:
                status = 'Observed' if row.observations else 'No usable cost'
            total = row.total_quotes if row is not None else (0 if status == 'No matching quotes' else np.nan)
            eligible = row.observations if row is not None else (0 if total == 0 else np.nan)
            nontransparent = row.non_transparent_quotes if row is not None else (0 if total == 0 else np.nan)
            records.append(dict(receiving_country=destination.destination_name, reporting_period=period,
                eligible_cost_quotes=eligible, total_quotes=total,
                coverage_pct=eligible / total * 100 if pd.notna(total) and total > 0 else np.nan,
                non_transparent_exclusions=nontransparent,
                transparent_missing_cost_quotes=total - nontransparent - eligible,
                status=status))
    return pd.DataFrame(records, columns=['receiving_country','reporting_period','eligible_cost_quotes','total_quotes','coverage_pct','non_transparent_exclusions','transparent_missing_cost_quotes','status'])


def key_findings(results):
    records = []
    for destination in results.metadata.resolved_destinations:
        rows = results.corridor_summary.loc[results.corridor_summary.destination_code.eq(destination.destination_code)]
        if rows.empty:
            records.append({'Country': destination.destination_name, 'Price evidence': 'No matching quotes.', 'Community evidence': 'Not assessed.', 'Next step': 'Choose another period or collect additional price evidence.'})
            continue
        row = rows.iloc[0]
        price = ('No usable total cost.' if pd.isna(row.median_total_cost) else f'Median quoted cost {row.median_total_cost:.3f}% for USD {results.metadata.transfer_amount_usd}; {row.observations} eligible costs from {row.total_quotes} quotes.')
        price += f' {row.non_transparent_quotes} quotes did not disclose the exchange rate.'
        fields = [('relevance_rating','rating'), ('relevance_rationale','rationale'), ('relevance_evidence_source','evidence source'), ('relevance_evidence_date','evidence date')]
        missing = [label for field, label in fields if pd.isna(row[field])]
        evidence = 'Missing: ' + ', '.join(missing) + '.' if missing else 'Documented rating, rationale, source and date supplied; researcher judgment.'
        required = results.metadata.weights.relevance > 0
        next_step = 'Check current provider prices and discuss suitability with the community.'
        if missing:
            next_step += ' Gather and document ' + ', '.join(missing) + (' before community-informed prioritization.' if required else ' only if community-informed prioritization is needed; these inputs are optional for Cost & disclosure.')
        records.append({'Country': destination.destination_name, 'Price evidence': price, 'Community evidence': evidence, 'Next step': next_step})
    return pd.DataFrame(records, columns=['Country','Price evidence','Community evidence','Next step'])


def fee_distribution(results):
    records = []
    details = results.provider_details
    for row in results.fee_summary.itertuples():
        currency_mask = details.fee_currency.isna() if pd.isna(row.fee_currency) else details.fee_currency.eq(row.fee_currency)
        eligible = details.loc[details.destination_code.eq(row.destination_code) & currency_mask & details.transparent.eq('yes'), 'transfer_fee'].dropna()
        records.append(dict(receiving_country=row.receiving_country, fee_currency=row.fee_currency,
            median_transfer_fee=row.median_transfer_fee, eligible_fee_quotes=len(eligible),
            minimum_transfer_fee=eligible.min() if len(eligible) else np.nan,
            maximum_transfer_fee=eligible.max() if len(eligible) else np.nan,
            zero_fee_quotes=int(eligible.eq(0).sum())))
    return pd.DataFrame(records, columns=['receiving_country','fee_currency','median_transfer_fee','eligible_fee_quotes','minimum_transfer_fee','maximum_transfer_fee','zero_fee_quotes'])


def filter_service_rows(rows, filters=None, keep_unavailable=True):
    out = rows.copy(deep=True)
    allowed = {'total_cost_pct', 'transfer_fee', 'exchange_rate_margin'}
    for field, bounds in (filters or {}).items():
        if field not in allowed or len(bounds) != 2:
            raise ValueError('Invalid provider-table filter')
        low, high = bounds
        if any(value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not np.isfinite(value)) for value in bounds):
            raise ValueError('Provider bounds must be finite numbers or blank')
        if low is not None and high is not None and low > high:
            raise ValueError('Provider minimum cannot exceed maximum')
        if low is None and high is None:
            continue
        mask = out[field].notna()
        if low is not None:
            mask &= out[field].ge(low)
        if high is not None:
            mask &= out[field].le(high)
        if keep_unavailable:
            mask |= out[field].isna()
        out = out.loc[mask].copy()
    return out


def service_cost_breakdown(rows):
    out = rows.copy(deep=True)
    known = out.transparent.eq('yes')
    usd = out.fee_currency.eq('USD').fillna(False)
    out['transfer_fee_usd'] = out.transfer_fee.where(known & usd)
    out['fx_margin_usd'] = (out.exchange_rate_margin * out.transfer_amount_usd / 100).where(known)
    out['component_total_usd'] = out.transfer_fee_usd + out.fx_margin_usd
    out['published_total_usd'] = (out.total_cost_pct * out.transfer_amount_usd / 100).where(known)
    out['component_minus_published_usd'] = out.component_total_usd - out.published_total_usd
    out['breakdown_status'] = 'Available'
    out.loc[out.component_total_usd.isna(), 'breakdown_status'] = 'Unavailable: missing fee or FX margin'
    out.loc[~usd, 'breakdown_status'] = 'Unavailable: fee currency not USD; no conversion assumed'
    out.loc[~known, 'breakdown_status'] = 'Unknown: exchange rate undisclosed'
    return out
