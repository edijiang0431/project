"""Independent check: standard-library CSV reading and Decimal medians.

Run from prof-build-M2: uv run python ../project-dashboard/check_ana_channels.py
Reads prepared quotes; does not import dashboard calculation functions or check Excel cleaning.
"""
import csv
from decimal import Decimal
import gzip
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
groups = {name: [] for name in ('Internet-only', 'Counter-only', 'Mixed', 'Other/unknown')}
counts = dict.fromkeys(groups, 0)
excluded = 0


def middle(values):
    ordered = sorted(values)
    n = len(ordered)
    return ordered[n // 2] if n % 2 else (ordered[n // 2 - 1] + ordered[n // 2]) / 2


with gzip.open(ROOT / 'prof-build-M2/data/rpw_usa_clean.csv.gz', 'rt', newline='') as source:
    for row in csv.DictReader(source):
        if (row['source_code'], row['destination_code'], row['period']) != ('USA', 'MEX', '2025_3Q'):
            continue
        words = {part.strip().lower() for part in row['access_point'].split(',') if part.strip()}
        known = {'internet', 'agent', 'bank branch', 'post office branch', 'call center'}
        online = 'internet' in words
        counter = bool(words & {'agent', 'bank branch', 'post office branch'})
        channel = ('Other/unknown' if not words or words - known else
                   'Mixed' if online and counter else 'Internet-only' if online else
                   'Counter-only' if counter else 'Other/unknown')
        counts[channel] += 1
        value = row['cc1_total_cost_pct'].strip()
        if row['transparent'].strip().lower() != 'yes' or not value:
            excluded += 1
            continue
        cost = Decimal(value)
        if not cost.is_finite():
            raise ValueError('Nonfinite cost')
        groups[channel].append(cost)

print('USA to Mexico | USD 200 | Q3 2025')
print('Channel | total quotes | eligible costs | median cost (%)')
for channel, values in groups.items():
    median = f'{middle(values):.3f}' if values else 'Unavailable'
    print(f'{channel} | {counts[channel]} | {len(values)} | {median}')
delta = middle(groups['Counter-only']) - middle(groups['Internet-only'])
print(f'Counter minus Internet: {delta:.3f} percentage points')
print(f'Dollar equivalent: ${delta * Decimal(200) / 100:.2f}')
print(f'All-quote median: {middle([cost for values in groups.values() for cost in values]):.3f}%')
print(f'Excluded non-transparent or missing costs: {excluded}')
assert len(groups['Internet-only']) == 29
assert len(groups['Counter-only']) == 15
# Match the displayed precision; the prepared CSV retains floating-point tails.
assert middle(groups['Internet-only']).quantize(Decimal('.001')) == Decimal('4.010')
assert middle(groups['Counter-only']).quantize(Decimal('.001')) == Decimal('4.600')
assert delta.quantize(Decimal('.001')) == Decimal('0.590')
print('Comparison with live medians and counts: MATCH')
