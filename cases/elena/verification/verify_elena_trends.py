"""Reconstructed independent verification of Elena's historical quote evidence.

Reconstructs the earlier in-memory investigation; it is not an archived original.
Uses only Python's standard library and reads pinned Git blobs without checkout.
Does not import application helpers, change files, or validate the Excel source.
Run from cases/elena/: python verification/verify_elena_trends.py
"""

import csv
import gzip
import hashlib
import io
from pathlib import Path
import subprocess
from decimal import Decimal


COMMIT = '208b0375b0816cb4ea05c17f303a6096ddd3024d'
DATA_PATH = 'prof-build-M2/data/rpw_usa_clean.csv.gz'
EXPECTED_SHA256 = 'fe8d6f2921450494ca27ff9503e50e1d24f53934af1bc4bddb02566bac205910'
PERIODS = ('2024_4Q', '2025_1Q', '2025_3Q')
FIELDS = (
    'firm', 'payment_instrument', 'access_point', 'pickup_method',
    'cc1_lcu_code', 'cc1_lcu_amount', 'cc1_denomination_amount',
)
STRICT_FIELDS = FIELDS + (
    'firm_type', 'pickup_location', 'speed_actual', 'receiving_network_coverage',
)


def eligible(row):
    return row['transparent'].strip().casefold() == 'yes' and bool(row['cc1_total_cost_pct'].strip())


def median(rows):
    values = sorted(Decimal(row['cc1_total_cost_pct']) for row in rows if eligible(row))
    n = len(values)
    return (values[(n - 1) // 2] + values[n // 2]) / 2 if n else None


def normalized(value):
    # Apply to each of the seven fields, as in the earlier investigation.
    # Preserve spelling/punctuation otherwise; do not invent provider aliases.
    tokens = (' '.join(token.casefold().split()) for token in value.split(','))
    return '|'.join(sorted(tokens))


def signature(row, fields=FIELDS):
    return tuple(normalized(row[field]) for field in fields)


def profiles(rows, fields=FIELDS):
    groups = {}
    for row in rows:
        key = signature(row, fields)
        if key in groups:
            raise ValueError('Ambiguous duplicate profile; do not guess a match: ' + str(key))
        groups[key] = row
    return groups


def shown(value):
    return 'Unavailable' if value is None else format(value, '.3f')


def main():
    repo = Path(__file__).resolve().parents[3]
    blob = subprocess.check_output(['git', 'show', COMMIT + ':' + DATA_PATH], cwd=repo)
    digest = hashlib.sha256(blob).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError('Unexpected prepared data fingerprint: ' + digest)
    all_rows = list(csv.DictReader(io.StringIO(gzip.decompress(blob).decode('utf-8-sig'))))
    rows = [row for row in all_rows if row['source_code'] == 'USA' and row['destination_code'] == 'MEX']
    if len({row['id'] for row in rows}) != len(rows):
        raise ValueError('Duplicate Mexico quote IDs')
    selected = {period: [row for row in rows if row['period'] == period] for period in PERIODS}
    for quarter in selected.values():
        for row in quarter:
            if row['cc1_lcu_code'] != 'USD' or Decimal(row['cc1_lcu_amount']) != 200 or Decimal(row['cc1_denomination_amount']) != 200:
                raise ValueError('Selected quote does not represent the specified USD 200 basket')

    print('RECONSTRUCTED CHECK; no application calculation helpers; prepared data only')
    print('Commit:', COMMIT)
    print('Prepared SHA-256:', digest)
    print('Mexico records in full available history:', len(rows))
    print('\nQUARTERS: total eligible nontransparent transparent_missing median_pct')
    for period in ('2024_4Q', '2025_1Q', '2025_2Q', '2025_3Q'):
        quarter = [row for row in rows if row['period'] == period]
        nontransparent = sum(row['transparent'].strip().casefold() != 'yes' for row in quarter)
        missing = sum(row['transparent'].strip().casefold() == 'yes' and not row['cc1_total_cost_pct'].strip() for row in quarter)
        print(period, len(quarter), sum(eligible(row) for row in quarter), nontransparent, missing, shown(median(quarter)))
    print('2025_2Q rows in complete committed USA data:', sum(row['period'] == '2025_2Q' for row in all_rows))
    # These windows have no exclusions, so profiles of eligible rows equal profiles
    # of all recorded rows. Check this instead of silently changing the population.
    if not all(eligible(row) for quarter in selected.values() for row in quarter):
        raise ValueError('Selected samples now have exclusions; revisit profile-population definition')

    print('\nBASIC MATCH FIELDS:', ', '.join(FIELDS))
    print('Normalization: casefold, collapse whitespace, split comma lists, sort tokens, join with |; no numeric recoding')
    maps = {period: profiles(selected[period]) for period in PERIODS}
    print('Distinct profiles:', ', '.join(period + '=' + str(len(maps[period])) for period in PERIODS))
    for first, second in zip(PERIODS, PERIODS[1:]):
        common = set(maps[first]) & set(maps[second])
        print('Pair matches:', first, second, len(common))
    common = set.intersection(*(set(mapping) for mapping in maps.values()))
    print('Basic profiles common to all three:', len(common))
    print('COMMON BASIC MEDIANS: period profiles median_pct')
    for period in PERIODS:
        print(period, len(common), shown(median([maps[period][key] for key in sorted(common)])))
    print('Unmatched Q1 profiles:', len(set(maps['2025_1Q']) - set(maps['2025_3Q'])))
    print('Unmatched Q3 profiles:', len(set(maps['2025_3Q']) - set(maps['2025_1Q'])))
    for label, difference, period in (
        ('Q1-only profile', set(maps['2025_1Q']) - set(maps['2025_3Q']), '2025_1Q'),
        ('Q3-only profile', set(maps['2025_3Q']) - set(maps['2025_1Q']), '2025_3Q'),
    ):
        for key in sorted(difference):
            print(label + ':', maps[period][key]['id'], ' / '.join(key))

    # Reproduce the earlier stricter-rule sensitivity check without treating its
    # selected subset as a validated fixed-product panel.
    strict = {period: profiles(selected[period], STRICT_FIELDS) for period in PERIODS}
    strict_common = set.intersection(*(set(mapping) for mapping in strict.values()))
    print('\nSTRICT FIELDS:', ', '.join(STRICT_FIELDS))
    print('Strict profiles common to all three:', len(strict_common))
    for period in PERIODS:
        print('Strict median:', period, shown(median([strict[period][key] for key in sorted(strict_common)])))

    print('\nFULL AVAILABLE HISTORY: period total eligible median_pct')
    history = {}
    for period in sorted({row['period'] for row in rows}):
        quarter = [row for row in rows if row['period'] == period]
        history[period] = median(quarter)
        print(period, len(quarter), sum(eligible(row) for row in quarter), shown(history[period]))
    end = history['2025_3Q']
    print('\nSTART SENSITIVITY: start median_pct endpoint_minus_start_percentage_points')
    for period in ('2023_4Q', '2024_1Q', '2024_3Q', '2024_4Q'):
        print(period, shown(history[period]), shown(end - history[period]))
    print('\nCaution: profile matches are not established product identities; this is not a causal decomposition.')


if __name__ == '__main__':
    main()
