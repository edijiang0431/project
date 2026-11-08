"""Prepare the optional Census evidence once. Dashboard startup never downloads data.

Run from prof-build-M2: uv run python -m src.prepare_acs
Use --refresh to re-download the official source row and variable definitions.
"""
import argparse
import csv
from datetime import datetime, timezone
import io
import json
from pathlib import Path
from urllib.request import urlopen

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_URL = 'https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/data/5YRData/acsdt5y2024-b05006.dat'
VARIABLES_URL = 'https://api.census.gov/data/2024/acs/acs5/groups/B05006.json'
SNAPSHOT = ROOT / 'inputs' / 'acs_b05006_la_source.json'
OUTPUT = ROOT / 'inputs' / 'acs_b05006_la.csv'


def download_snapshot():
    with urlopen(VARIABLES_URL, timeout=60) as response:
        variables = json.load(response)['variables']
    with urlopen(DATA_URL, timeout=60) as response:
        reader = csv.DictReader(io.TextIOWrapper(response, encoding='utf-8-sig'), delimiter='|')
        row = next((r for r in reader if r['GEO_ID'] == '0500000US06037'), None)
    if row is None:
        raise ValueError('Los Angeles County was not found in the official summary file')
    return dict(data_url=DATA_URL, variables_url=VARIABLES_URL,
                retrieved_date=datetime.now(timezone.utc).date().isoformat(), row=row,
                labels={k: v['label'] for k, v in variables.items() if k.startswith('B05006_') and k.endswith('E')})


def number(value):
    # Census negative sentinel codes mean unavailable, never negative populations.
    try:
        n = float(value)
        return n if n >= 0 else None
    except (TypeError, ValueError):
        return None


def prepare(snapshot, countries):
    row = snapshot['row']
    if row['GEO_ID'] != '0500000US06037':
        raise ValueError('Expected Los Angeles County, California')
    aliases = {'CPV': 'Cabo Verde', 'CHN': 'China, excluding Hong Kong and Taiwan',
               'EGY': 'Egypt', 'YEM': 'Yemen'}
    labels = {label.split('!!')[-1].rstrip(':'): key for key, label in snapshot['labels'].items()}
    records = []
    for country in countries.itertuples(index=False):
        category = aliases.get(country.destination_code, country.destination_name)
        # Do not substitute Sudan or a regional aggregate for South Sudan.
        key = labels.get(category) if country.destination_code != 'SSD' else None
        suffix = key.split('_')[1][:-1] if key else None
        estimate = number(row.get(f'B05006_E{suffix}')) if key else None
        moe = number(row.get(f'B05006_M{suffix}')) if key else None
        records.append(dict(destination_code=country.destination_code, destination_name=country.destination_name,
                            acs_category=category if key else '', acs_variable=key or '',
                            population_estimate=estimate, margin_of_error=moe,
                            county_foreign_born_total=number(row['B05006_E001']),
                            county_total_margin_of_error=number(row['B05006_M001']),
                            geography='Los Angeles County, California', survey_period='2020–2024',
                            retrieved_date=snapshot['retrieved_date'],
                            match_status='Matched' if estimate is not None and moe is not None else 'Unavailable'))
    return pd.DataFrame(records)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--refresh', action='store_true')
    args = parser.parse_args()
    if args.refresh or not SNAPSHOT.exists():
        snapshot = download_snapshot()
        temp = SNAPSHOT.with_suffix('.json.tmp')
        temp.write_text(json.dumps(snapshot, indent=2) + '\n')
        temp.replace(SNAPSHOT)
    snapshot = json.loads(SNAPSHOT.read_text())
    countries = pd.read_csv(ROOT / 'data' / 'rpw_usa_clean.csv.gz', usecols=['destination_code', 'destination_name']).drop_duplicates().sort_values('destination_code')
    details = prepare(snapshot, countries)
    temp = OUTPUT.with_suffix('.csv.tmp')
    details.to_csv(temp, index=False)
    temp.replace(OUTPUT)
    print(details[['destination_code', 'population_estimate', 'margin_of_error', 'match_status']].to_string(index=False))
    print(f'Prepared {OUTPUT.name}; {details.match_status.eq("Matched").sum()} matched of {len(details)} corridors')


if __name__ == '__main__':
    main()
