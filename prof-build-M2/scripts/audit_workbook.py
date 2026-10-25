"""Independent streaming audit: no preparation/calculation imports."""
import collections
import hashlib
import json
from pathlib import Path
import re
import sys
import openpyxl

path=Path(sys.argv[1])
w=openpyxl.load_workbook(path,read_only=True,data_only=True)
ws=w['Dataset (from Q2 2016)']
rows=ws.iter_rows(values_only=True)
head=next(rows)[:42]
columns=[re.sub('[^a-z0-9]+','_',str(c).lower().replace('%','pct')).strip('_') for c in head]
counts=collections.Counter(); ids=set(); repeated=[]; periods=set(); dest=set(); providers=set(); access=collections.Counter(); currencies=[collections.Counter(),collections.Counter()]; dates=[]
source_names=collections.defaultdict(set)
for rownum,values in enumerate(rows,2):
    r=dict(zip(columns,values[:42]))
    if not any(v is not None for v in r.values()): continue
    counts['modern_rows']+=1
    ident=str(r['id'])
    if ident in ids: repeated.append([rownum,ident])
    ids.add(ident)
    source_names[str(r['source_code'])].add(str(r['source_name']))
    if r['source_code']!='USA': continue
    counts['usa_rows']+=1
    period=str(r['period']).strip(); periods.add(period)
    dest.add(str(r['destination_code']).strip()); providers.add(' '.join(str(r['firm']).split()))
    counts['transparent_'+str(r['transparent']).lower().strip()]+=1
    if r['cc1_total_cost_pct'] in (None,''): counts['missing_cc1_total_cost']+=1
    if period=='2025_3Q' and r['destination_code']=='MEX': counts['mex_latest_reference']+=1
    access[str(r['access_point'])]+=1
    for i in range(2): currencies[i][str(r[f'cc{i+1}_lcu_code'])]+=1
    dates.append(str(r['date']))
w.close()
out=dict(counts=counts,distinct_ids=len(ids),repeated_ids=repeated,periods=sorted(periods),destinations=sorted(dest),providers=sorted(providers),access_counts=access,currencies=currencies,source_name_variants={k:sorted(v) for k,v in source_names.items() if len(v)>1},source_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
Path('data/raw').mkdir(parents=True,exist_ok=True)
Path('data/raw/independent_audit.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
if out['source_sha256']=='02e7ec01e461d027e4c805413839e3378f58366d2660cfeadfff140db288cf82':
    Path('data/reference_membership.json').write_text(json.dumps({k:out[k] for k in ['periods','destinations','providers']},indent=2)+'\n')
