import gzip
import hashlib
import json
from pathlib import Path
import shutil
from unittest.mock import patch
import pandas as pd
import pytest
from src.contracts import PUBLISHED,PREPARED
from src.prepare_data import clean_modern,canonical_bytes,install_pair,check_recovery,recover
from src.load_data import *

def raw(q):
    df=q[PUBLISHED].copy()
    for c in df: df[c]=df[c].map(lambda v:'' if pd.isna(v) else str(v))
    return df

def artifacts(q,path):
    data=canonical_bytes(q)
    report=dict(report_schema_version=1,source_filename='fixture.xlsx',source_sha256='0'*64,prepared_filename=Path(path).name,prepared_sha256=hashlib.sha256(data).hexdigest(),prepared_at_utc=pd.Timestamp.now(tz='UTC').isoformat(),validation_summary=['fixture'],change_summary=[],preparation_warnings=[])
    return data,json.dumps(report).encode()

def test_clean_and_canonical(quotes,tmp_path):
    r=raw(quotes); r.loc[0,'cc1_total_cost_pct']='-4'; r.loc[1,'date']='20/Jan/2024'
    q=clean_modern(r)
    assert q.cc1_total_cost_pct.iloc[0]==-4
    assert q.date.iloc[0]==q.date.iloc[1]
    assert canonical_bytes(q)==canonical_bytes(q.copy())
    b=canonical_bytes(q)
    assert b[4:8]==b'\0'*4 and b[3]==0
    csv=gzip.decompress(b)
    assert b'\r\n' not in csv and csv.endswith(b'\n')
    assert csv.decode().splitlines()[0].split(',')==PREPARED
    p=tmp_path/'out.csv.gz'
    install_pair(*artifacts(q,p),p)
    m=load_preparation_metadata(report_for(p),p)
    got=load_data(p,m)
    assert got.id.tolist()==q.id.tolist()
    assert got.cc1_total_cost_pct.iloc[0]==-4

@pytest.mark.parametrize('col,val',[('cc1_total_cost_pct','bad'),('cc2_lcu_fee','inf'),('date','31/Feb/2024'),('transparent',''),('transparent','maybe')])
def test_malformed(quotes,col,val):
    r=raw(quotes); r.loc[0,col]=val
    with pytest.raises(ValueError,match=col+'.*source worksheet rows'): clean_modern(r)

def test_duplicates(quotes):
    r=raw(quotes)
    with pytest.raises(ValueError,match='affected=2.*source_row'):
        clean_modern(pd.concat([r,r.iloc[:1]],ignore_index=True))
    r.loc[1,'id']=r.loc[0,'id']
    with pytest.raises(ValueError,match='Duplicate quote'): clean_modern(r)
    r=raw(quotes); r.loc[1]=r.loc[0]; r.loc[1,'id']='unique'
    assert len(clean_modern(r))==6

def test_mismatched_and_readonly(quotes,tmp_path):
    p=tmp_path/'out.csv.gz'; install_pair(*artifacts(quotes,p),p)
    before={x.name:x.read_bytes() for x in tmp_path.iterdir()}
    p.write_bytes(p.read_bytes()+b'broken')
    state={x.name:x.read_bytes() for x in tmp_path.iterdir()}
    with pytest.raises(ValueError,match='read-only'): load_preparation_metadata(report_for(p),p)
    assert state=={x.name:x.read_bytes() for x in tmp_path.iterdir()}

@pytest.mark.parametrize('first_run',[False,True])
@pytest.mark.parametrize('failure_at',[1,2])
def test_replacement_rollback(quotes,tmp_path,first_run,failure_at):
    import src.prepare_data as module
    p=tmp_path/'out.csv.gz'
    if not first_run: install_pair(*artifacts(quotes,p),p)
    old=[p.read_bytes(),report_for(p).read_bytes()] if not first_run else None
    q=quotes.copy(); q.cc1_total_cost_pct=12
    original=module.os.replace; count=0
    def fail(a,b):
        nonlocal count
        count+=1
        if count==failure_at: raise OSError('simulated replacement failure')
        return original(a,b)
    with patch.object(module.os,'replace',fail):
        with pytest.raises(OSError,match='simulated'): install_pair(*artifacts(q,p),p)
    if first_run: assert not p.exists() and not report_for(p).exists()
    else:
        assert old==[p.read_bytes(),report_for(p).read_bytes()]
        load_data(p)
    assert not transaction_dirs(p)

def test_recovery(quotes,tmp_path):
    p=tmp_path/'out.csv.gz'; install_pair(*artifacts(quotes,p),p)
    txn=tmp_path/('.'+p.name+'.txn-test'); (txn/'backup').mkdir(parents=True)
    (txn/'transaction.json').write_text(json.dumps({'output':str(p.resolve())}))
    shutil.copy2(p,txn/'backup'/p.name); shutil.copy2(report_for(p),txn/'backup'/report_for(p).name)
    p.write_bytes(b'partial replacement')
    before={str(x):x.read_bytes() for x in tmp_path.rglob('*') if x.is_file()}
    with pytest.raises(ValueError,match='--check-recovery.*txn-test'):
        load_preparation_metadata(report_for(p),p)
    check_recovery(txn,p)
    assert before=={str(x):x.read_bytes() for x in tmp_path.rglob('*') if x.is_file()}
    recover(txn,p)
    assert not txn.exists()
    assert len(load_data(p))==6

def test_bad_schema_and_period(quotes,tmp_path):
    p=tmp_path/'out.csv.gz'
    q=quotes.copy(); q.loc[0,'period_start']=pd.Timestamp('2000-01-01')
    with pytest.raises(ValueError,match='period_start'): install_pair(*artifacts(q,p),p)
    assert not p.exists()

@pytest.mark.parametrize('first_run',[False,True])
def test_final_validation_failure_restores(quotes,tmp_path,first_run):
    import src.prepare_data as module
    p=tmp_path/'out.csv.gz'
    if not first_run: install_pair(*artifacts(quotes,p),p)
    old=(p.read_bytes(),report_for(p).read_bytes()) if not first_run else None
    q=quotes.copy(); q.cc1_total_cost_pct=10
    original=module.validate_pair; failed=False
    def validate(data,report,name):
        nonlocal failed
        # During final validation the installed content differs from the prior pair.
        if Path(data)==p.resolve() and not failed and Path(data).read_bytes()==canonical_bytes(q):
            failed=True
            raise ValueError('simulated final validation failure')
        return original(data,report,name)
    with patch.object(module,'validate_pair',validate):
        with pytest.raises(ValueError,match='simulated final'): install_pair(*artifacts(q,p),p)
    if first_run:
        assert not p.exists() and not report_for(p).exists()
    else:
        assert (p.read_bytes(),report_for(p).read_bytes())==old
        load_data(p)

@pytest.mark.parametrize('field,value',[('report_schema_version',2),('prepared_filename','other.csv.gz'),('prepared_sha256','0'*64),('validation_summary','bad'),('prepared_at_utc','2026-01-01')])
def test_report_validation(quotes,tmp_path,field,value):
    p=tmp_path/'out.csv.gz'; install_pair(*artifacts(quotes,p),p)
    obj=json.loads(report_for(p).read_text()); obj[field]=value
    report_for(p).write_text(json.dumps(obj))
    with pytest.raises(ValueError,match='read-only'): load_preparation_metadata(report_for(p),p)

def test_load_once_no_excel(quotes,tmp_path):
    p=tmp_path/'out.csv.gz'; install_pair(*artifacts(quotes,p),p)
    with patch('pandas.read_excel',side_effect=AssertionError('Excel must not open')):
        with patch('src.load_data.json.loads',wraps=json.loads) as j:
            with patch('src.load_data.pd.read_csv',wraps=pd.read_csv) as c:
                m=load_preparation_metadata(report_for(p),p)
                load_data(p,m)
                assert j.call_count==c.call_count==1

def test_distinct_times_paths_same_bytes(quotes,tmp_path):
    a,b=tmp_path/'a.csv.gz',tmp_path/'b.csv.gz'
    install_pair(*artifacts(quotes,a),a)
    install_pair(*artifacts(quotes,b),b)
    assert a.read_bytes()==b.read_bytes()
    assert sha256(a)==sha256(b)
    assert json.loads(report_for(a).read_text())['prepared_filename']!=json.loads(report_for(b).read_text())['prepared_filename']
