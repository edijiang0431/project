"""Recompute the live-export median without importing app calculation code."""
import csv
from decimal import Decimal
from pathlib import Path
from statistics import median

path = Path(__file__).resolve().parents[1] / 'evidence' / 'ana-provider-export.csv'
with path.open(encoding='utf-8-sig', newline='') as stream:
    reader = csv.DictReader(stream)
    columns = reader.fieldnames
    rows = list(reader)
costs = [Decimal(row['Total cost (%)']) for row in rows
         if row['Disclosure status'] == 'Transparent' and row['Total cost (%)'].strip()]
print('Rows:', len(rows))
print('Countries:', ', '.join(sorted({r['Receiving country'] for r in rows})))
print('Periods:', ', '.join(sorted({r['Reporting period'] for r in rows})))
print('Eligible transparent costs:', len(costs))
print('Median total cost (%):', median(costs))
print('Collection dates:', min(r['Collection date'] for r in rows), 'to', max(r['Collection date'] for r in rows))
print('Columns:', ', '.join(columns))
print('Scope: verifies exported rows, not raw-workbook preparation or a current transaction price.')
