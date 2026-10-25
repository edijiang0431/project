"""Read-only startup and validation of prepared artifacts; never opens Excel."""
from dataclasses import fields
from pathlib import Path
import hashlib
import json
import re
import pandas as pd
import numpy as np
from .contracts import *

def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1024*1024), b''):
            h.update(b)
    return h.hexdigest()

def report_for(path):
    return Path(str(path)+'.validation.json')

def transaction_dirs(path):
    p = Path(path)
    return sorted(p.parent.glob('.'+p.name+'.txn-*'))

def pair_metadata(report_path, data_path, intended_name=None):
    p = Path(data_path)
    obj = json.loads(Path(report_path).read_text(encoding='utf-8'))
    names = {f.name for f in fields(PreparationMetadata)}
    if not isinstance(obj, dict) or set(obj) != names:
        raise ValueError('Malformed report schema; expected PreparationMetadata fields')
    if type(obj['report_schema_version']) is not int or obj['report_schema_version'] != 1:
        raise ValueError('Unsupported report_schema_version')
    for k in ['source_filename','source_sha256','prepared_filename','prepared_sha256','prepared_at_utc']:
        if not isinstance(obj[k], str) or not obj[k]:
            raise ValueError('Invalid report field '+k)
    for k in ['source_sha256','prepared_sha256']:
        if not re.fullmatch('[0-9a-f]{64}', obj[k]):
            raise ValueError('Invalid fingerprint '+k)
    for k in ['validation_summary','change_summary','preparation_warnings']:
        if not isinstance(obj[k], list) or any(not isinstance(s,str) for s in obj[k]):
            raise ValueError('Invalid report field '+k)
        obj[k] = tuple(obj[k])
    stamp = pd.Timestamp(obj['prepared_at_utc'])
    if pd.isna(stamp) or stamp.tzinfo is None or stamp.utcoffset().total_seconds() != 0:
        raise ValueError('Preparation timestamp must be UTC')
    obj['prepared_at_utc'] = stamp
    if obj['prepared_filename'] != (intended_name or p.name) or obj['prepared_sha256'] != sha256(p):
        raise ValueError('Prepared filename/fingerprint mismatch')
    return PreparationMetadata(**obj)

def recovery_error(path, problem):
    p = Path(path).resolve()
    messages = [f'Prepared pair is not ready: {problem}. Startup is read-only. Regenerate using uv run python src/prepare_data.py --input <explicit-workbook> --output {p}']
    for d in transaction_dirs(p):
        try:
            manifest = json.loads((d/'transaction.json').read_text())
            if manifest['output'] != str(p):
                continue
            pair_metadata(d/'backup'/report_for(p).name, d/'backup'/p.name, p.name)
            read_prepared(d/'backup'/p.name)
            messages += [f'Valid backup pair: {d}', f'uv run python src/prepare_data.py --check-recovery {d} --output {p}', f'uv run python src/prepare_data.py --recover {d} --output {p}']
        except (ValueError, OSError, KeyError, TypeError):
            messages.append(f'No internally valid backup pair in {d}; preserve for diagnosis')
    return ValueError('\n'.join(messages))

def load_preparation_metadata(report_path: str, prepared_data_path: str) -> PreparationMetadata:
    try:
        if transaction_dirs(prepared_data_path):
            raise ValueError('Incomplete transaction exists')
        return pair_metadata(report_path, prepared_data_path)
    except (ValueError, OSError, KeyError, TypeError) as e:
        raise recovery_error(prepared_data_path, e) from e

def read_prepared(path):
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    if list(df.columns) != PREPARED:
        raise ValueError(f'Prepared schema/order invalid; missing {set(PREPARED)-set(df)}, unexpected {set(df)-set(PREPARED)}')
    for c in NUMERIC:
        raw = df[c].mask(df[c].eq(''))
        df[c] = pd.to_numeric(raw, errors='raise').astype(float)
        if np.isinf(df[c]).any() or (raw.notna() & df[c].isna()).any():
            raise ValueError(f'Invalid/nonfinite numeric {c}')
    for c in ['date','period_start']:
        df[c] = pd.to_datetime(df[c].replace('', None), format='%Y-%m-%d', errors='raise')
    for c in set(PREPARED)-set(NUMERIC)-{'date','period_start'}:
        df[c] = df[c].replace('', pd.NA).astype('string')
    validate_choices(df)
    for c in ['id','firm','source_name']:
        if df[c].isna().any() or df[c].str.strip().eq('').any():
            raise ValueError('Missing required '+c)
    if df.id.duplicated().any():
        raise ValueError('Duplicate verified id')
    if not df.transparent.isin(['yes','no']).all():
        raise ValueError('Invalid transparency')
    for code, name in [('source_code','source_name'),('destination_code','destination_name')]:
        if df.groupby(code)[name].nunique().gt(1).any():
            raise ValueError('Conflicting country code/name '+code)
    expected = df.period.map(period_start)
    if not df.period_start.eq(expected).all():
        raise ValueError('period_start disagrees with reporting period')
    return df

def load_data(path: str, metadata: PreparationMetadata | None = None) -> pd.DataFrame:
    try:
        if metadata is None:
            metadata = load_preparation_metadata(str(report_for(path)),path)
        if transaction_dirs(path) or metadata.prepared_filename != Path(path).name or metadata.prepared_sha256 != sha256(path):
            raise ValueError('Incomplete transaction or fingerprint mismatch')
        return read_prepared(path)
    except (ValueError, OSError, TypeError) as e:
        raise recovery_error(path,e) from e
