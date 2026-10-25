"""Verify independent audit against prepared data and the retained count baseline."""
from pathlib import Path
import json
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.load_data import *
from src.calculate_summaries import classify_channel
p='data/rpw_usa_clean.csv.gz'
m=load_preparation_metadata(p+'.validation.json',p)
q=load_data(p,m)
audit=json.loads(Path('data/raw/independent_audit.json').read_text())
assert audit['counts']['modern_rows']==audit['distinct_ids']==204469
assert not audit['repeated_ids']
assert audit['counts']['usa_rows']==len(q)==29542
assert audit['periods']==sorted(q.period.unique()) and len(audit['periods'])==37
assert '2025_2Q' not in audit['periods']
assert q.destination_code.nunique()==42 and q.firm.nunique()==88
assert audit['providers']==sorted(q.firm.unique())
assert audit['counts']['mex_latest_reference']==46
assert q.transparent.value_counts().to_dict()=={'yes':29520,'no':22}
assert q.cc1_total_cost_pct.isna().sum()==0
assert q.cc1_lcu_code.eq('USD').all() and q.cc2_lcu_code.eq('USD').all()
assert q.access_point.value_counts().to_dict()==audit['access_counts']
channels=q.access_point.map(lambda v:classify_channel(v)[0]).value_counts().to_dict()
assert channels=={'Internet-only':18207,'Counter-only':10300,'Mixed':696,'Other/unknown':339}
assert str(q.date.min().date())=='2016-05-09' and str(q.date.max().date())=='2025-09-10'
print('Independent audit agrees with all retained count/coverage/currency/channel baselines.')
print('Channels:',channels)
print('Collection dates:',q.date.min(),q.date.max())
print('Non-USA source-name variants (prepared USA mapping remains consistent):',audit['source_name_variants'])
print('Source checksum:',audit['source_sha256'],'(differs from stored dataset-repo reference; exact reference sets unavailable)')
