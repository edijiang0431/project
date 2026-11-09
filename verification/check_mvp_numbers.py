"""Independent expected values from CSV/Decimal; compare with the app separately.

From prof-build-M2: uv run python ../verification/check_mvp_numbers.py
Does not alter data. Writes the comparison ledger and summary beside this script.
Application imports below supply OBSERVED values only, never the independent answer.
"""
import csv
from collections import Counter, defaultdict
from decimal import Decimal
import gzip
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / 'prof-build-M2'
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(APP))

import pandas as pd
from src.contracts import RELEVANCE
from src.load_data import load_data, load_preparation_metadata
from src.dashboard_workflow import DashboardSession
from src.dashboard_presentation import COST_MODE, COMMUNITY_MODE, default_weights
from src.acs_evidence import acs_relevance
from src.evidence_summaries import channel_cost_comparison, cost_coverage, fee_distribution, service_cost_breakdown
from src.period_presets import latest_four_calendar_quarters

DATA = APP / 'data/rpw_usa_clean.csv.gz'
with gzip.open(DATA, 'rt', encoding='utf-8-sig', newline='') as stream:
    records = list(csv.DictReader(stream))
digest = hashlib.sha256(DATA.read_bytes()).hexdigest()
prep = load_preparation_metadata(str(DATA) + '.validation.json', DATA)
quotes = load_data(DATA, prep)
empty = pd.DataFrame(columns=RELEVANCE)
ledger = []


def number(value):
    if value is None or str(value).strip() == '':
        return None
    result = Decimal(str(value))
    if result.is_nan():
        return None
    if not result.is_finite():
        raise ValueError('Unexpected infinite source value')
    return result


def median(values):
    values = sorted(v for v in values if v is not None)
    n = len(values)
    return (values[(n - 1) // 2] + values[n // 2]) / 2 if n else None


def channel(row):
    tokens = {' '.join(t.split()).casefold() for t in row['access_point'].split(',') if t.strip()}
    counters = {'agent', 'bank branch', 'post office branch'}
    if not tokens or tokens - counters - {'internet', 'call center'}:
        return 'Other/unknown'
    if 'internet' in tokens:
        return 'Mixed' if tokens & counters else 'Internet-only'
    return 'Counter-only' if tokens & counters else 'Other/unknown'


def groups(rows, key):
    out = defaultdict(list)
    for row in rows:
        out[key(row)].append(row)
    return out


def measures(rows, prefix):
    values = [number(r[prefix + '_total_cost_pct']) for r in rows if r['transparent'] == 'yes']
    eligible = sum(v is not None for v in values)
    flagged = sum(r['transparent'] == 'no' for r in rows)
    return dict(median_total_cost=median(values), observations=eligible, total_quotes=len(rows),
                non_transparent_quotes=flagged,
                non_transparent_quote_share=Decimal(flagged) / len(rows) if rows else None)


def check(selection, metric, expected, actual):
    missing = actual is None or (not isinstance(actual, str) and pd.isna(actual))
    if expected is None:
        passed = bool(missing)
    elif isinstance(expected, str):
        passed = not missing and expected == actual
    elif missing:
        passed = False
    elif isinstance(expected, int):
        passed = Decimal(str(actual)) == expected
    else:
        passed = abs(Decimal(str(actual)) - expected) <= Decimal('0.000000001')
    ledger.append(dict(selection=selection, metric=metric,
                       independent='Unavailable' if expected is None else str(expected),
                       app='Unavailable' if missing else str(actual), result='PASS' if passed else 'FAIL'))


def analyze(periods, amount=200, destinations=None, mode=COST_MODE, evidence=None, window=()):
    return DashboardSession(quotes, prep).analyze(
        periods, destinations or [], amount, default_weights(mode),
        empty if evidence is None else evidence, scoring_mode=mode, calendar_window=window)


def validate_result(result, rows, amount, tag, population_shares=None):
    prefix = 'cc1' if amount == 200 else 'cc2'
    check(tag, 'matching_quote_count', len(rows), result.metadata.matching_row_count)
    for name, table, key, columns in [
        ('corridor', result.corridor_summary, lambda r: r['destination_code'], ['destination_code']),
        ('quarter', result.period_summary, lambda r: (r['destination_code'], r['period']), ['destination_code', 'reporting_period']),
        ('channel', result.channel_summary, lambda r: (r['destination_code'], channel(r)), ['destination_code', 'channel_category']),
    ]:
        expected = groups(rows, key)
        check(tag, name + '.group_count', len(expected), len(table))
        for item in table.to_dict('records'):
            group_key = item[columns[0]] if len(columns) == 1 else tuple(item[c] for c in columns)
            for field, value in measures(expected[group_key], prefix).items():
                check(tag, f'{name}.{group_key}.{field}', value, item[field])

    reference_rows = [r for r in records if r['source_code'] == 'USA' and r['period'] in result.metadata.resolved_periods]
    reference = {key: measures(value, prefix)['median_total_cost'] for key, value in groups(reference_rows, lambda r: r['destination_code']).items()}
    valid = [v for v in reference.values() if v is not None]
    low, high = min(valid), max(valid)
    check(tag, 'reference.corridors', len(valid), result.metadata.cost_reference.valid_corridors)
    check(tag, 'reference.minimum_pct', low, result.metadata.cost_reference.minimum_pct)
    check(tag, 'reference.maximum_pct', high, result.metadata.cost_reference.maximum_pct)
    cost_mode = result.metadata.scoring_mode == COST_MODE
    for field, expected in [('cost', Decimal(2) / 3 if cost_mode else Decimal('.5')),
                            ('transparency', Decimal(1) / 3 if cost_mode else Decimal('.25')),
                            ('relevance', Decimal(0) if cost_mode else Decimal('.25'))]:
        check(tag, 'weight.' + field, expected, getattr(result.metadata.weights, field))
    for item in result.corridor_summary.to_dict('records'):
        mid = reference[item['destination_code']]
        norm = None if mid is None or len(valid) < 2 else (Decimal(0) if low == high else (mid - low) / (high - low))
        check(tag, item['destination_code'] + '.cost_normalized', norm, item['cost_normalized'])
        disclosure = measures([r for r in rows if r['destination_code'] == item['destination_code']], prefix)['non_transparent_quote_share']
        share = (population_shares or {}).get(item['destination_code'])
        score = None if norm is None else ((Decimal(2) * norm + disclosure) / 3 if cost_mode
                 else None if share is None else Decimal('.5') * norm + Decimal('.25') * disclosure + Decimal('.25') * share)
        if not cost_mode:
            check(tag, item['destination_code'] + '.community_normalized', share, item['relevance_normalized'])
        check(tag, item['destination_code'] + '.score', score, item['campaign_priority_score'])

    keyed = groups(rows, lambda r: (r['destination_code'], r[prefix + '_lcu_code'] or None))
    for table, raw_field, output_field, count_field in [
        (result.fee_summary, '_lcu_fee', 'median_transfer_fee', 'fee_observations'),
        (result.fx_margin_summary, '_fx_margin', 'median_exchange_margin', 'fx_margin_observations')]:
        for item in table.to_dict('records'):
            currency = None if pd.isna(item['fee_currency']) else item['fee_currency']
            subset = keyed[(item['destination_code'], currency)]
            values = [number(r[prefix + raw_field]) for r in subset if r['transparent'] == 'yes']
            check(tag, f'{item["destination_code"]}.{currency}.{output_field}', median(values), item[output_field])
            check(tag, f'{item["destination_code"]}.{currency}.{count_field}', sum(v is not None for v in values), item[count_field])
    for item in fee_distribution(result).to_dict('records'):
        code = next(r['destination_code'] for r in rows if r['destination_name'] == item['receiving_country'])
        subset = keyed[(code, item['fee_currency'])]
        fees = [number(r[prefix + '_lcu_fee']) for r in subset if r['transparent'] == 'yes']
        fees = [v for v in fees if v is not None]
        for field, value in [('minimum_transfer_fee', min(fees) if fees else None), ('maximum_transfer_fee', max(fees) if fees else None), ('zero_fee_quotes', sum(v == 0 for v in fees))]:
            check(tag, code + '.' + field, value, item[field])

    by_id = {r['id']: r for r in rows}
    check(tag, 'provider_rows', len(by_id), len(result.provider_details))
    for item in service_cost_breakdown(result.provider_details).to_dict('records'):
        raw = by_id[item['service_id']]
        disclosed = raw['transparent'] == 'yes'
        fee = number(raw[prefix + '_lcu_fee']) if disclosed and raw[prefix + '_lcu_code'] == 'USD' else None
        margin = number(raw[prefix + '_fx_margin']) if disclosed else None
        fx = margin * amount / 100 if margin is not None else None
        published = number(raw[prefix + '_total_cost_pct']) if disclosed else None
        published = published * amount / 100 if published is not None else None
        components = fee + fx if fee is not None and fx is not None else None
        for field, value in [('transfer_fee_usd', fee), ('fx_margin_usd', fx), ('component_total_usd', components), ('published_total_usd', published), ('component_minus_published_usd', components - published if components is not None and published is not None else None)]:
            check(tag, raw['id'] + '.' + field, value, item[field])


period = '2025_3Q'
latest_rows = [r for r in records if r['source_code'] == 'USA' and r['period'] == period]
latest200 = analyze([period])
latest500 = analyze([period], amount=500)
validate_result(latest200, latest_rows, 200, 'All USA corridors | Q3 2025 | USD 200 | Cost & disclosure')
validate_result(latest500, latest_rows, 500, 'All USA corridors | Q3 2025 | USD 500 | Cost & disclosure')
no_evidence = analyze([period], mode=COMMUNITY_MODE)
for item in no_evidence.corridor_summary.to_dict('records'):
    check('No community evidence', item['destination_code'] + '.score', None, item['campaign_priority_score'])

# Independently rebuild ACS expected inputs from the saved OFFICIAL source row and labels.
snapshot = json.loads((APP / 'inputs/acs_b05006_la_source.json').read_text())
raw_acs = snapshot['row']
check('ACS source', 'Los Angeles geography', '0500000US06037', raw_acs['GEO_ID'])
total = Decimal(raw_acs['B05006_E001'])
labels = {label.split('!!')[-1].rstrip(':'): key for key, label in snapshot['labels'].items()}
aliases = {'CPV': 'Cabo Verde', 'CHN': 'China, excluding Hong Kong and Taiwan', 'EGY': 'Egypt', 'YEM': 'Yemen'}
shares = {}
with (APP / 'inputs/acs_b05006_la.csv').open() as stream:
    for item in csv.DictReader(stream):
        code = item['destination_code']
        variable = labels.get(aliases.get(code, item['destination_name'])) if code != 'SSD' else None
        check('ACS mapping', code + '.variable', variable or '', item['acs_variable'])
        if not variable:
            check('ACS mapping', code + '.estimate', None, number(item['population_estimate']))
            continue
        suffix = variable.split('_')[1][:-1]
        population, moe = Decimal(raw_acs['B05006_E' + suffix]), Decimal(raw_acs['B05006_M' + suffix])
        if population < 0 or moe < 0:
            continue
        check('ACS values', code + '.population', population, number(item['population_estimate']))
        check('ACS values', code + '.90_percent_MOE', moe, number(item['margin_of_error']))
        check('ACS values', code + '.county_total', total, number(item['county_foreign_born_total']))
        shares[code] = population / total
evidence = acs_relevance(pd.read_csv(APP / 'inputs/acs_b05006_la.csv'), set(quotes.destination_code))
with_acs = analyze([period], mode=COMMUNITY_MODE, evidence=evidence)
validate_result(with_acs, latest_rows, 200, 'All USA corridors | Q3 2025 | USD 200 | Community + ACS', shares)
filtered = analyze([period], destinations=['MEX'], mode=COMMUNITY_MODE, evidence=evidence)
check('Display-filter invariance', 'Mexico community score', Decimal(str(with_acs.corridor_summary.set_index('destination_code').loc['MEX', 'campaign_priority_score'])), filtered.corridor_summary.iloc[0].campaign_priority_score)

# Independently construct the latest four calendar quarters (do not backfill Q2).
available = {r['period'] for r in records}
last = max(int(p[:4]) * 4 + int(p[5]) - 1 for p in available)
window = tuple(f'{n // 4:04}_{n % 4 + 1}Q' for n in range(last - 3, last + 1))
selected = [p for p in window if p in available]
actual_periods, actual_window = latest_four_calendar_quarters(available)
check('Calendar preset', 'requested window', ','.join(window), ','.join(actual_window))
check('Calendar preset', 'observed selections', ','.join(selected), ','.join(actual_periods))
trend = analyze(selected, destinations=['MEX'], window=window)
trend_rows = [r for r in records if r['destination_code'] == 'MEX' and r['period'] in selected]
validate_result(trend, trend_rows, 200, 'Mexico | latest four calendar quarters | USD 200')
for item in cost_coverage(trend).to_dict('records'):
    rows = [r for r in trend_rows if r['period'] == item['reporting_period']]
    expected = measures(rows, 'cc1')
    missing = item['reporting_period'] not in available
    check('Calendar coverage', item['reporting_period'] + '.status', 'No survey data' if missing else 'Observed', item['status'])
    check('Calendar coverage', item['reporting_period'] + '.eligible', None if missing else expected['observations'], item['eligible_cost_quotes'])
    check('Calendar coverage', item['reporting_period'] + '.coverage_pct', None if not rows else Decimal(100) * expected['observations'] / len(rows), item['coverage_pct'])

# A historical selection with a real non-transparency exclusion, unlike latest Q3.
old = analyze(['2017_1Q'], destinations=['MEX'])
old_rows = [r for r in records if r['destination_code'] == 'MEX' and r['period'] == '2017_1Q']
validate_result(old, old_rows, 200, 'Mexico | Q1 2017 | USD 200 | exclusion check')

# Supporting case analyses below are not claimed as built-in dashboard metrics.
phl = [r for r in latest_rows if r['destination_code'] == 'PHL']
paired = [r for r in phl if r['transparent'] == 'yes' and number(r['cc1_total_cost_pct']) is not None and number(r['cc2_total_cost_pct']) is not None]
deltas = [(number(r['cc1_total_cost_pct']) - number(r['cc2_total_cost_pct'])) * 10 for r in paired]
paired_summary = dict(pairs=len(paired), favors_two=sum(d > Decimal('1e-9') for d in deltas), ties=sum(abs(d) <= Decimal('1e-9') for d in deltas), favors_five=sum(d < -Decimal('1e-9') for d in deltas), median_difference_usd=str(median(deltas)))
for field, case_value in [('pairs', 57), ('favors_two', 50), ('ties', 6), ('favors_five', 1)]:
    check('Lea case: supporting paired analysis', field, paired_summary[field], case_value)
check('Lea case: supporting paired analysis', 'median_difference_usd', median(deltas), Decimal('13.10'))
fields = ['firm', 'payment_instrument', 'access_point', 'pickup_method', 'cc1_lcu_code', 'cc1_lcu_amount', 'cc1_denomination_amount']
def profile(row):
    return tuple('|'.join(sorted(' '.join(v.casefold().split()) for v in row[f].split(','))) for f in fields)
profiles = {}
for p in selected:
    rows = [r for r in trend_rows if r['period'] == p]
    mapping = {profile(r): r for r in rows}
    if len(mapping) != len(rows):
        raise ValueError('Ambiguous service profiles; cannot silently match')
    profiles[p] = mapping
common = set.intersection(*(set(value) for value in profiles.values()))
common_medians = {p: str(measures([mapping[k] for k in common], 'cc1')['median_total_cost']) for p, mapping in profiles.items()}
check('Elena case: supporting profile analysis', 'common_basic_profiles', len(common), 43)
for p, case_value in [('2024_4Q', '4.610'), ('2025_1Q', '4.700'), ('2025_3Q', '4.600')]:
    check('Elena case: supporting profile analysis', p + '.common_profile_median', Decimal(common_medians[p]), Decimal(case_value))

# Check the preserved cash-pickup case live export as a separate data artifact.
with (ROOT / 'cases/ana-cash-pickup/evidence/ana-provider-export.csv').open() as stream:
    exported = list(csv.DictReader(stream))
mex_rows = [r for r in latest_rows if r['destination_code'] == 'MEX']
check('Preserved live provider export', 'rows', len(mex_rows), len(exported))
check('Preserved live provider export', 'median_cost_pct', measures(mex_rows, 'cc1')['median_total_cost'], median(number(r['Total cost (%)']) for r in exported if r['Disclosure status'] == 'Transparent'))

def records_json(frame):
    return json.loads(frame.to_json(orient='records', date_format='iso', double_precision=12))
summary = dict(code_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(), prepared_sha256=digest,
               rows=len(records), distinct_ids=len({r['id'] for r in records}), periods=len(available), corridors=len({r['destination_code'] for r in records}),
               latest_rows=len(latest_rows), matched_acs_countries=len(shares),
               comparisons=len(ledger), failures=sum(r['result'] == 'FAIL' for r in ledger),
               latest_200_corridors=records_json(latest200.corridor_summary), latest_500_corridors=records_json(latest500.corridor_summary),
               mexico_channels=records_json(latest200.channel_summary[latest200.channel_summary.destination_code.eq('MEX')]),
               latest_200_fees=records_json(fee_distribution(latest200)), latest_200_fx=records_json(latest200.fx_margin_summary),
               acs_mexico_share=str(shares['MEX']), acs_mexico_score=float(filtered.corridor_summary.iloc[0].campaign_priority_score),
               calendar_window=window, observed_periods=selected, mexico_quarters=records_json(trend.period_summary),
               mexico_2017=records_json(old.corridor_summary), philippines_paired=paired_summary,
               common_basic_profiles=len(common), common_profile_medians=common_medians)
OUT.mkdir(exist_ok=True)
with (OUT / 'mvp-number-comparisons.csv').open('w', newline='') as stream:
    writer = csv.DictWriter(stream, fieldnames=list(ledger[0]))
    writer.writeheader()
    writer.writerows(ledger)
(OUT / 'mvp-number-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
lines = [f'Code commit: {summary["code_commit"]}', f'Prepared SHA-256: {digest}',
         f'Prepared rows / unique IDs / periods / corridors: {len(records)} / {summary["distinct_ids"]} / {len(available)} / {summary["corridors"]}',
         f'Latest-quarter quotes: {len(latest_rows)}', f'Numeric and state comparisons: {len(ledger)}; failures: {summary["failures"]}',
         f'ACS matched countries: {len(shares)}; Mexico population share: {shares["MEX"]:.9%}; community score: {summary["acs_mexico_score"]:.9f}',
         f'Philippines paired: {paired_summary}', f'Common Mexico basic profiles: {len(common)}; medians: {common_medians}',
         'Scope: independent expectations use the prepared CSV and saved official ACS source; not a new workbook extraction, live-price check or evaluation of campaign suitability.']
text = '\n'.join(lines) + '\n'
(OUT / 'mvp-number-output.txt').write_text(text)
print(text)
failures = [r for r in ledger if r['result'] == 'FAIL']
if failures:
    for row in failures[:15]:
        print(row)
    raise SystemExit(1)
