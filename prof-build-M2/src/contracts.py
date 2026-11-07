"""Explicit, immutable value contracts; DataFrame consumers must not mutate tables."""
from dataclasses import dataclass
import math
import re
import pandas as pd

PUBLISHED = '''id period source_code source_name source_region source_income source_lending source_g8g20 destination_code destination_name destination_region destination_income destination_lending destination_g8g20 firm firm_type payment_instrument access_point speed_actual cc1_lcu_amount cc1_denomination_amount cc1_lcu_code cc1_lcu_fee cc1_lcu_fx_rate cc1_fx_margin cc1_total_cost_pct cc2_lcu_amount cc2_denomination_amount cc2_lcu_code cc2_lcu_fee cc2_lcu_fx_rate cc2_fx_margin cc2_total_cost_pct inter_lcu_bank_fx transparent standard_note note2 receiving_network_coverage pickup_location pickup_method date corridor'''.split()
PREPARED = PUBLISHED + ['period_start', 'corridor_label']
NUMERIC = [c for c in PUBLISHED if (c.startswith(('cc1_', 'cc2_')) and not c.endswith('_code')) or c == 'inter_lcu_bank_fx']
IDENTITY = ['source_code', 'destination_code', 'sending_country', 'receiving_country']
MEASURES = ['median_total_cost', 'observations', 'total_quotes', 'non_transparent_quotes', 'non_transparent_quote_share']
RELEVANCE = ['destination_code', 'relevance_rating', 'rationale', 'evidence_source', 'evidence_date']
CHANNELS = ['Internet-only', 'Counter-only', 'Mixed', 'Other/unknown']
SCHEMAS = {
 'corridor_summary': IDENTITY + MEASURES + ['relevance_rating', 'relevance_rationale', 'relevance_evidence_source', 'relevance_evidence_date', 'cost_normalized', 'transparency_normalized', 'relevance_normalized', 'cost_weight', 'transparency_weight', 'relevance_weight', 'campaign_priority_score', 'unscored_reasons'],
 'period_summary': IDENTITY + ['reporting_period', 'period_start'] + MEASURES,
 'channel_summary': IDENTITY + ['channel_category'] + MEASURES,
 'provider_details': IDENTITY + ['service_id', 'provider', 'reporting_period', 'collection_date', 'access_point', 'channel_category', 'transparent', 'transfer_amount_usd', 'transfer_fee', 'fee_currency', 'exchange_rate_margin', 'total_cost_pct'],
 'fee_summary': IDENTITY + ['fee_currency', 'median_transfer_fee', 'fee_observations'],
 'fx_margin_summary': IDENTITY + ['fee_currency', 'median_exchange_margin', 'fx_margin_observations'],
}
@dataclass(frozen=True)
class ScoringWeights:
    cost: float = .50
    transparency: float = .25
    relevance: float = .25
@dataclass(frozen=True)
class PreparationMetadata:
    report_schema_version: int
    source_filename: str
    source_sha256: str
    prepared_filename: str
    prepared_sha256: str
    prepared_at_utc: pd.Timestamp
    validation_summary: tuple[str, ...]
    change_summary: tuple[str, ...]
    preparation_warnings: tuple[str, ...]
@dataclass(frozen=True)
class ResolvedDestination:
    destination_code: str
    destination_name: str
@dataclass(frozen=True)
class RelevanceInputSnapshot:
    destination_code: str
    relevance_rating: float | None
    relevance_rationale: str | None
    relevance_evidence_source: str | None
    relevance_evidence_date: pd.Timestamp | None
@dataclass(frozen=True)
class CostReference:
    scope: str
    periods: tuple[str, ...]
    transfer_amount_usd: int
    valid_corridors: int
    minimum_pct: float | None
    maximum_pct: float | None

@dataclass(frozen=True)
class AnalysisMetadata:
    requested_periods: tuple[str, ...]
    requested_destination_codes: tuple[str, ...]
    resolved_periods: tuple[str, ...]
    resolved_destinations: tuple[ResolvedDestination, ...]
    transfer_amount_usd: int
    weights: ScoringWeights
    validated_relevance_snapshot: tuple[RelevanceInputSnapshot, ...]
    matching_row_count: int
    collection_date_min: pd.Timestamp | None
    collection_date_max: pd.Timestamp | None
    preparation: PreparationMetadata
    runtime_validation_warnings: tuple[str, ...]
    available_periods: tuple[str, ...] = ()
    scoring_mode: str = 'Community campaign priority'
    cost_reference: CostReference | None = None
    calendar_window: tuple[str, ...] = ()
@dataclass(frozen=True)
class AnalysisResults:
    corridor_summary: pd.DataFrame
    period_summary: pd.DataFrame
    channel_summary: pd.DataFrame
    provider_details: pd.DataFrame
    fee_summary: pd.DataFrame
    fx_margin_summary: pd.DataFrame
    metadata: AnalysisMetadata

def require_columns(df, columns):
    missing = [c for c in columns if c not in df]
    if missing:
        raise ValueError('Missing columns: ' + ', '.join(missing))

def period_key(p):
    if not isinstance(p, str) or not re.fullmatch(r'\d{4}_[1-4]Q', p):
        raise ValueError(f'Invalid period {p!r}; expected YYYY_nQ')
    return int(p[:4]) * 4 + int(p[5]) - 1

def period_start(p):
    period_key(p)
    return pd.Timestamp(int(p[:4]), (int(p[5])-1)*3+1, 1)

def validate_amount_weights(amount, weights):
    if isinstance(amount, bool) or not isinstance(amount, int) or amount not in (200, 500):
        raise ValueError('Choose exactly one integer transfer amount: USD 200 or 500')
    if not isinstance(weights, ScoringWeights):
        raise ValueError('weights must be ScoringWeights')
    vals = [weights.cost, weights.transparency, weights.relevance]
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0 for v in vals) or not math.isclose(sum(vals), 1, rel_tol=0, abs_tol=1e-9):
        raise ValueError('Weights must be finite, nonnegative and sum to 1 within 1e-9')

def validate_choices(df):
    require_columns(df, ['source_code','period','destination_code','destination_name'])
    if df.empty:
        raise ValueError('Prepared data is empty; regenerate data with src/prepare_data.py')
    for c in ['source_code','period','destination_code','destination_name']:
        if df[c].isna().any() or df[c].astype(str).str.strip().eq('').any():
            raise ValueError(f'Missing/blank {c}; regenerate prepared data')
    if not df.source_code.eq('USA').all():
        raise ValueError('Prepared data must contain USA origins only')
    for p in df.period.unique():
        period_key(p)
    if df.groupby('destination_code').destination_name.nunique().gt(1).any():
        raise ValueError('Conflicting destination names')

def canonical_selection(values, label):
    if not isinstance(values, (list, tuple)) or any(not isinstance(v, str) or not v.strip() for v in values):
        raise ValueError(f'{label} must be a list of nonblank strings')
    return tuple(sorted(set(values)))

def resolve_choices(df, periods, destinations):
    validate_choices(df)
    ps = canonical_selection(periods, 'periods')
    ds = canonical_selection(destinations, 'destinations')
    badp = sorted(set(ps)-set(df.period))
    badd = sorted(set(ds)-set(df.destination_code))
    if badp or badd:
        raise ValueError(f'Invalid periods: {badp}; invalid destinations: {badd}. Valid periods: {sorted(df.period.unique(), reverse=True)}; valid destinations: {sorted(df.destination_code.unique())}')
    mapping = df[['destination_code','destination_name']].drop_duplicates().sort_values(['destination_name','destination_code'], kind='stable')
    return (sorted(ps or df.period.unique(), key=period_key),
            [ResolvedDestination(r.destination_code,r.destination_name) for r in mapping.itertuples() if not ds or r.destination_code in ds])

NUM_RESULT = set(MEASURES + ['relevance_rating','cost_normalized','transparency_normalized','relevance_normalized','cost_weight','transparency_weight','relevance_weight','campaign_priority_score','transfer_amount_usd','transfer_fee','exchange_rate_margin','total_cost_pct','median_transfer_fee','fee_observations','median_exchange_margin','fx_margin_observations'])
COUNTS = {'observations','total_quotes','non_transparent_quotes','fee_observations','fx_margin_observations','transfer_amount_usd'}
DATES = {'period_start','collection_date','relevance_evidence_date'}
def result_table(name, records=()):
    df = records.loc[:, SCHEMAS[name]].copy() if isinstance(records, pd.DataFrame) else pd.DataFrame(records, columns=SCHEMAS[name])
    for c in df:
        if c in NUM_RESULT:
            df[c] = pd.to_numeric(df[c]).astype('int64' if c in COUNTS else 'float64')
        elif c in DATES:
            df[c] = pd.to_datetime(df[c])
        elif c != 'unscored_reasons':
            df[c] = df[c].astype('string')
    return df

def validate_results(results):
    problems = []
    for name, columns in SCHEMAS.items():
        missing = [c for c in columns if c not in getattr(results, name)]
        if missing:
            problems.append(name + ': ' + ', '.join(missing))
    if problems:
        raise ValueError('Missing columns: ' + '; '.join(problems))
