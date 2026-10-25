"""Strict one-time workbook preparation with deterministic data and recoverable pair commit."""
import argparse
from dataclasses import asdict
import gzip
import io
import json
import os
from pathlib import Path
import re
import shutil
import sys
import uuid
import numpy as np
import pandas as pd
if __package__ in (None, ''):
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.contracts import *
from src.load_data import sha256, report_for, pair_metadata, read_prepared, transaction_dirs

BASELINE_SHA = '02e7ec01e461d027e4c805413839e3378f58366d2660cfeadfff140db288cf82'

def supplied_error(df, column, mask, reason):
    if mask.any():
        records = [{'source_row': int(i)+2, 'value': str(df.at[i,column])} for i in df.index[mask][:20]]
        raise ValueError(f'{column}: {reason}; affected rows {int(mask.sum())}; source worksheet rows/examples: {records}')

def clean_modern(raw):
    df = raw.copy()
    df.columns = [re.sub(r'[^a-z0-9]+','_',str(c).lower().replace('%','pct')).strip('_') for c in df.columns]
    if list(df.columns) != PUBLISHED:
        raise ValueError(f'Published schema violation; missing {sorted(set(PUBLISHED)-set(df))}; unexpected {sorted(set(df)-set(PUBLISHED))}; expected exact published order')
    for c in df:
        df[c] = df[c].map(lambda v: None if pd.isna(v) or str(v).strip()=='' else re.sub(r'\s+',' ',str(v).strip()))
    for c in ['id','period','firm','source_code','source_name','destination_code','destination_name']:
        supplied_error(df,c,df[c].isna(),'required identity is blank')
    for c in ['source_region','source_income','source_lending','source_g8g20','destination_region','destination_income','destination_lending','destination_g8g20']:
        # '..' is a documented not-applicable classification, preserved verbatim.
        pass
    for c in NUMERIC:
        values = pd.to_numeric(df[c], errors='coerce')
        supplied_error(df,c,df[c].notna() & (values.isna() | ~np.isfinite(values)), 'malformed/nonfinite supplied number')
        df[c] = values.astype(float)
    rawdate = df.date.copy()
    dates = pd.to_datetime(rawdate, format='mixed', dayfirst=True, errors='coerce')
    supplied_error(df,'date',rawdate.notna() & dates.isna(),'invalid supplied date')
    df.date = dates
    supplied_error(df,'period',~df.period.str.fullmatch(r'\d{4}_[1-4]Q',na=False),'expected YYYY_nQ')
    df['period_start'] = df.period.map(period_start)
    df.transparent = df.transparent.str.lower()
    supplied_error(df,'transparent',~df.transparent.isin(['yes','no']),'expected yes/no')
    exact = df[PUBLISHED].duplicated(keep=False)
    repeated = df.id.duplicated(keep=False)
    if exact.any() or repeated.any():
        mask = exact | repeated
        context = df.loc[mask,['id','period','corridor','firm']].copy()
        context['source_row'] = context.index + 2
        raise ValueError(f'Duplicate quote keys / exact rows: affected={int(mask.sum())}, excess_keys={int(df.id.duplicated().sum())}, exact_excess={int(df[PUBLISHED].duplicated().sum())}; {context.to_dict("records")}')
    df['corridor_label'] = df.source_name + ' to ' + df.destination_name
    return df

def canonical_bytes(df):
    text = df[PREPARED].to_csv(index=False,lineterminator='\n',na_rep='',date_format='%Y-%m-%d',float_format='%.17g')
    b = io.BytesIO()
    with gzip.GzipFile(filename='',mode='wb',fileobj=b,compresslevel=9,mtime=0) as f:
        f.write(text.encode('utf-8'))
    return b.getvalue()

def validate_pair(data, report, name):
    meta = pair_metadata(report, data, name)
    read_prepared(data)
    return meta

def install_pair(data_bytes, report_bytes, output):
    output = Path(output).resolve()
    output.parent.mkdir(parents=True,exist_ok=True)
    if transaction_dirs(output):
        raise ValueError('Incomplete transaction exists. Use explicit --check-recovery / --recover first.')
    txn = output.parent / ('.'+output.name+'.txn-'+uuid.uuid4().hex)
    txn.mkdir()
    (txn/'transaction.json').write_text(json.dumps({'output':str(output)}))
    stage, backup = txn/'stage', txn/'backup'
    stage.mkdir(); backup.mkdir()
    staged_data, staged_report = stage/output.name, stage/report_for(output).name
    had_pair = False
    final_touched = False
    try:
        staged_data.write_bytes(data_bytes)
        staged_report.write_bytes(report_bytes)
        validate_pair(staged_data,staged_report,output.name)
        if output.exists() or report_for(output).exists():
            validate_pair(output,report_for(output),output.name)
            shutil.copy2(output,backup/output.name)
            shutil.copy2(report_for(output),backup/report_for(output).name)
            validate_pair(backup/output.name,backup/report_for(output).name,output.name)
            had_pair = True
        final_touched = True
        os.replace(staged_data, output)
        os.replace(staged_report, report_for(output))
        validate_pair(output,report_for(output),output.name)
    except Exception:
        if had_pair:
            # Copy backups, preserving them if restoration itself is interrupted.
            shutil.copy2(backup/output.name,output)
            shutil.copy2(backup/report_for(output).name,report_for(output))
            validate_pair(output,report_for(output),output.name)
        elif final_touched:
            # Any first-run commit failure leaves no ready pair, even when a
            # one-shot validation error would disappear on a second attempt.
            output.unlink(missing_ok=True)
            report_for(output).unlink(missing_ok=True)
        shutil.rmtree(txn)
        raise
    shutil.rmtree(txn)

def prepare_data(input_path: str, output_path: str) -> None:
    source = Path(input_path)
    if not source.exists():
        raise ValueError(f'Workbook not found: {source}. Download with dataset repository download_data.py, then pass its actual filename explicitly using --input.')
    raw = pd.read_excel(source,sheet_name='Dataset (from Q2 2016)',usecols='A:AP',dtype=str,keep_default_na=False)
    full = clean_modern(raw)
    full_rows, full_ids = len(full), full.id.nunique()
    df = full.loc[full.source_code.eq('USA')].copy()
    del raw, full
    validate_choices(df)
    for c,n in [('source_code','source_name'),('destination_code','destination_name')]:
        if df.groupby(c)[n].nunique().gt(1).any():
            raise ValueError(f'Conflicting country code/name in prepared USA data: {c}')
    stats = {'modern_rows':full_rows,'modern_distinct_ids':full_ids,'usa_rows':len(df),'periods':df.period.nunique(),'corridors':df.destination_code.nunique(),'providers':df.firm.nunique(),'missing_cc1_total_cost':int(df.cc1_total_cost_pct.isna().sum()),'transparent':int(df.transparent.eq('yes').sum()),'non_transparent':int(df.transparent.eq('no').sum()),'mex_latest_reference':int((df.destination_code.eq('MEX') & df.period.eq('2025_3Q')).sum())}
    baseline = dict(modern_rows=204469,modern_distinct_ids=204469,usa_rows=29542,periods=37,corridors=42,providers=88,missing_cc1_total_cost=0,transparent=29520,non_transparent=22,mex_latest_reference=46)
    source_sha = sha256(source)
    changes = [f'{k}: reference={baseline[k]}, current={v}, delta={v-baseline[k]}' for k,v in stats.items()]
    changes.append(f'Source SHA-256 matches reference: {source_sha == BASELINE_SHA}; reference={BASELINE_SHA}; current={source_sha}')
    membership = {'periods': sorted(df.period.unique()),'destinations':sorted(df.destination_code.unique()),'providers': sorted(df.firm.unique())}
    reference_file = Path(__file__).resolve().parents[1]/'data/reference_membership.json'
    if reference_file.exists():
        reference = json.loads(reference_file.read_text())
        for k, values in membership.items():
            changes.append(f'{k} added={sorted(set(values)-set(reference[k]))}; removed={sorted(set(reference[k])-set(values))}')
    else:
        changes.append('Exact reference membership comparison unavailable; baseline membership not yet preserved.')
    if source_sha == BASELINE_SHA and stats != baseline:
        raise ValueError('Same-release baseline discrepancy: '+str(stats))
    summaries = [f'{k}={v}' for k,v in stats.items()]
    summaries += ['periods='+','.join(membership['periods']), 'country/currency/schema/unique ID checks passed; all modern IDs audited before USA selection']
    summaries += [f'{c} currencies={sorted(df[c].dropna().unique())}' for c in ['cc1_lcu_code','cc2_lcu_code']]
    for c in ['cc1_total_cost_pct','cc2_total_cost_pct']:
        msg = f'{c}: min={df[c].min()}, max={df[c].max()}, negative_count={int(df[c].lt(0).sum())}'
        print(msg); summaries.append(msg)
    print(json.dumps(stats,indent=2))
    content = canonical_bytes(df)
    import hashlib
    report = dict(report_schema_version=1,source_filename=source.name,source_sha256=source_sha,prepared_filename=Path(output_path).name,prepared_sha256=hashlib.sha256(content).hexdigest(),prepared_at_utc=pd.Timestamp.now(tz='UTC').isoformat(),validation_summary=summaries,change_summary=changes,preparation_warnings=['Historical sampled quotes; not guaranteed live prices.'])
    install_pair(content,(json.dumps(report,indent=2,ensure_ascii=False)+'\n').encode(),output_path)
    print(f'Ready: {Path(output_path).resolve()} and {report_for(output_path)}')

def check_recovery(directory, output):
    d,p = Path(directory).resolve(),Path(output).resolve()
    manifest = json.loads((d/'transaction.json').read_text())
    if d.parent != p.parent or not d.name.startswith('.'+p.name+'.txn-') or manifest != {'output':str(p)}:
        raise ValueError('Recovery pair is not intended for this output path')
    validate_pair(d/'backup'/p.name,d/'backup'/report_for(p).name,p.name)
    return d/'backup'/p.name, d/'backup'/report_for(p).name

def recover(directory,output):
    a,b = check_recovery(directory,output)
    p=Path(output).resolve()
    # Keep the selected recovery directory intact until the installed pair validates.
    recovery_stage = Path(directory)/'recovery-install'
    recovery_stage.mkdir(exist_ok=False)
    try:
        shutil.copy2(a,recovery_stage/p.name)
        shutil.copy2(b,recovery_stage/report_for(p).name)
        os.replace(recovery_stage/p.name,p)
        os.replace(recovery_stage/report_for(p).name,report_for(p))
        validate_pair(p,report_for(p),p.name)
    except Exception:
        shutil.rmtree(recovery_stage)
        raise
    shutil.rmtree(Path(directory))

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',default='../dataset_wb-remittance-prices/data/rpw_dataset_2011_2025_q3.xlsx')
    parser.add_argument('--output',default='data/rpw_usa_clean.csv.gz')
    group=parser.add_mutually_exclusive_group()
    group.add_argument('--check-recovery'); group.add_argument('--recover')
    args=parser.parse_args()
    try:
        if args.check_recovery:
            print('Valid backup pair:',check_recovery(args.check_recovery,args.output))
        elif args.recover:
            recover(args.recover,args.output); print('Recovery succeeded')
        else:
            prepare_data(args.input,args.output)
    except (ValueError,OSError) as e:
        parser.exit(1,str(e)+'\n')
