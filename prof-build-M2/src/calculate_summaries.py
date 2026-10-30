"""All analytical measures live here. Pure calculation; no files or figures."""
import numpy as np
import pandas as pd
from .contracts import *
from .load_relevance import validate_relevance, relevance_snapshot

RELATIVE_REASON = 'Relative cost unavailable: at least two selected corridors with valid median costs are required'

def classify_channel(value):
    if pd.isna(value) or not str(value).strip():
        return 'Other/unknown', ('Missing/blank access point',)
    tokens = { ' '.join(t.split()).casefold() for t in str(value).split(',') }
    counter = {'agent','bank branch','post office branch'}
    unknown = tokens - counter - {'internet','call center'}
    if unknown:
        return 'Other/unknown',tuple(sorted(unknown))
    internet, at_counter = 'internet' in tokens, bool(tokens & counter)
    return ('Mixed' if internet and at_counter else 'Internet-only' if internet else 'Counter-only' if at_counter else 'Other/unknown'), ()

def measure_groups(df, extra):
    keys=IDENTITY+extra
    out = df.groupby(keys,sort=False,dropna=False,observed=True).agg(
        median_total_cost=('_eligible_cost','median'), observations=('_eligible_cost','count'),
        total_quotes=('id','size'), non_transparent_quotes=('_no','sum')).reset_index()
    out['non_transparent_quote_share']=out.non_transparent_quotes/out.total_quotes
    return out

def input_snapshot(requested_periods,requested_destination_codes,amount,weights,relevance,preparation,scoring_mode='Community campaign priority'):
    validate_amount_weights(amount,weights)
    return (canonical_selection(requested_periods,'periods'),canonical_selection(requested_destination_codes,'destinations'),amount,weights,relevance_snapshot(relevance),preparation.prepared_filename,preparation.prepared_sha256,scoring_mode)

def metadata_snapshot(m):
    return (canonical_selection(m.requested_periods,'periods'),canonical_selection(m.requested_destination_codes,'destinations'),m.transfer_amount_usd,m.weights,m.validated_relevance_snapshot,m.preparation.prepared_filename,m.preparation.prepared_sha256,m.scoring_mode)

def calculate_summaries(filtered_data: pd.DataFrame, transfer_amount_usd: int,
    relevance_inputs: pd.DataFrame, weights: ScoringWeights,
    requested_periods: list[str], requested_destination_codes: list[str],
    resolved_periods: list[str], resolved_destinations: list[ResolvedDestination],
    preparation: PreparationMetadata, runtime_validation_warnings: tuple[str,...]=(),
    available_periods: tuple[str,...]=()) -> AnalysisResults:
    validate_amount_weights(transfer_amount_usd,weights)
    require_columns(filtered_data,PREPARED)
    canonical_selection(requested_periods,'periods'); canonical_selection(requested_destination_codes,'destinations')
    ps=tuple(sorted(set(resolved_periods),key=period_key))
    if len(ps)!=len(resolved_periods):
        raise ValueError('Duplicate resolved periods')
    mapping={d.destination_code:d.destination_name for d in resolved_destinations}
    if len(mapping)!=len(resolved_destinations):
        raise ValueError('Duplicate resolved destinations')
    for d in resolved_destinations:
        if not isinstance(d,ResolvedDestination) or not d.destination_code or not d.destination_name:
            raise ValueError('Invalid resolved destination')
    if requested_periods and set(requested_periods)!=set(ps):
        raise ValueError('Requested/resolved periods disagree')
    if requested_destination_codes and set(requested_destination_codes)!=set(mapping):
        raise ValueError('Requested/resolved destinations disagree')
    df=filtered_data.copy(deep=True)
    if not df.empty:
        validate_choices(df)
    for c in ['id','firm','source_name']:
        if df[c].isna().any() or df[c].astype(str).str.strip().eq('').any():
            raise ValueError('Missing/blank '+c)
    if df.id.duplicated().any():
        raise ValueError('Duplicate service id')
    if not df.transparent.isin(['yes','no']).all():
        raise ValueError('Invalid transparency')
    if not df.period.isin(ps).all() or not df.destination_code.isin(mapping).all() or not df.destination_name.eq(df.destination_code.map(mapping)).all():
        raise ValueError('Filtered rows disagree with resolved selections / destination labels')
    for c in NUMERIC:
        if not pd.api.types.is_numeric_dtype(df[c]):
            raise ValueError(f'{c}: prepared numeric dtype required')
        if np.isinf(df[c]).any():
            raise ValueError(c+': nonfinite value')
    for c in ['date','period_start']:
        if not pd.api.types.is_datetime64_any_dtype(df[c]):
            raise ValueError(c+': prepared datetime dtype required')
    if not df.empty and not df.period_start.eq(df.period.map(period_start)).all():
        raise ValueError('period_start disagreement')
    rel=validate_relevance(relevance_inputs,set(relevance_inputs.destination_code.dropna())|set(mapping))
    warnings=list(runtime_validation_warnings)
    access_map={}
    token_counts={}
    for value,count in df.access_point.fillna('').value_counts(dropna=False).items():
        category,tokens=classify_channel(value)
        access_map[value]=category
        for token in tokens:
            token_counts[token]=token_counts.get(token,0)+int(count)
    for token,count in sorted(token_counts.items()):
        warnings.append(f'Access point {token!r}: {count} distinct affected quotes')
    bounds=[None if df.date.empty or df.date.isna().all() else v for v in [df.date.min(),df.date.max()]]
    meta=AnalysisMetadata(tuple(requested_periods),tuple(requested_destination_codes),ps,tuple(resolved_destinations),transfer_amount_usd,ScoringWeights(weights.cost,weights.transparency,weights.relevance),relevance_snapshot(rel),len(df),*bounds,preparation,tuple(warnings),tuple(available_periods or ps))
    if df.empty:
        return AnalysisResults(**{k:result_table(k) for k in SCHEMAS},metadata=meta)
    prefix='cc1' if transfer_amount_usd==200 else 'cc2'
    df=df.rename(columns={'source_name':'sending_country','destination_name':'receiving_country'})
    df['channel_category']=df.access_point.fillna('').map(access_map)
    df['_eligible_cost']=df[prefix+'_total_cost_pct'].where(df.transparent.eq('yes'))
    df['_fee']=df[prefix+'_lcu_fee'].where(df.transparent.eq('yes'))
    df['_margin']=df[prefix+'_fx_margin'].where(df.transparent.eq('yes'))
    df['_no']=df.transparent.eq('no').astype(int)
    df['fee_currency']=df[prefix+'_lcu_code'].replace('',pd.NA)
    df['reporting_period']=df.period
    cor=measure_groups(df,[])
    cor=cor.merge(rel.rename(columns={'rationale':'relevance_rationale','evidence_source':'relevance_evidence_source','evidence_date':'relevance_evidence_date'}),on='destination_code',how='left',validate='many_to_one')
    valid=cor.median_total_cost.dropna()
    cor['cost_normalized']=np.nan
    if len(valid)>=2:
        cor['cost_normalized']=(cor.median_total_cost-valid.min())/(valid.max()-valid.min()) if valid.max()!=valid.min() else cor.median_total_cost.where(cor.median_total_cost.isna(),0.0)
    cor['transparency_normalized']=cor.non_transparent_quote_share
    complete=cor[['relevance_rating','relevance_rationale','relevance_evidence_source','relevance_evidence_date']].notna().all(axis=1)
    cor['relevance_normalized']=(cor.relevance_rating/5).where(complete)
    for component in ['cost','transparency','relevance']:
        cor[component+'_weight']=getattr(weights,component)
    scores=[]; reasons=[]
    for r in cor.itertuples():
        why=[]; score=0.
        for component,missing_reason in [('cost','Missing median cost' if pd.isna(r.median_total_cost) else RELATIVE_REASON),('transparency','Missing transparency share'),('relevance','Missing documented community relevance')]:
            w=getattr(weights,component); v=getattr(r,component+'_normalized')
            if w==0: continue
            if pd.isna(v): why.append(missing_reason)
            else: score+=w*v
        scores.append(np.nan if why else score); reasons.append(tuple(why))
    cor['campaign_priority_score']=scores; cor['unscored_reasons']=reasons
    cor=cor.sort_values(['campaign_priority_score','receiving_country','destination_code'],ascending=[False,True,True],na_position='last',kind='stable')
    period=measure_groups(df,['reporting_period','period_start']).sort_values(['receiving_country','destination_code','period_start'],kind='stable')
    channel=measure_groups(df,['channel_category'])
    channel['_order']=channel.channel_category.map({v:i for i,v in enumerate(CHANNELS)})
    channel=channel.sort_values(['receiving_country','destination_code','_order'],kind='stable')
    fee=df.groupby(IDENTITY+['fee_currency'],dropna=False,sort=False).agg(median_transfer_fee=('_fee','median'),fee_observations=('_fee','count')).reset_index().sort_values(['receiving_country','destination_code','fee_currency'],na_position='last',kind='stable')
    fx=df.groupby(IDENTITY+['fee_currency'],dropna=False,sort=False).agg(median_exchange_margin=('_margin','median'),fx_margin_observations=('_margin','count')).reset_index().sort_values(['receiving_country','destination_code','fee_currency'],na_position='last',kind='stable')
    details=df.sort_values(['receiving_country','destination_code','period_start','firm','id'],kind='stable').copy()
    details['service_id']=details.id
    details['provider']=details.firm
    details['collection_date']=details.date
    details['transfer_amount_usd']=transfer_amount_usd
    details['transfer_fee']=details[prefix+'_lcu_fee']
    details['exchange_rate_margin']=details['_margin']
    details['total_cost_pct']=details['_eligible_cost']
    return AnalysisResults(**{name:result_table(name,table) for name,table in [('corridor_summary',cor),('period_summary',period),('channel_summary',channel),('provider_details',details),('fee_summary',fee),('fx_margin_summary',fx)]},metadata=meta)
