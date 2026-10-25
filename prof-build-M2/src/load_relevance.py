from pathlib import Path
import re
import numpy as np
import pandas as pd
from .contracts import RELEVANCE, require_columns, RelevanceInputSnapshot

def validate_relevance(data, valid_destination_codes):
    require_columns(data, RELEVANCE)
    df = data[RELEVANCE].copy()
    for c in RELEVANCE:
        if c != 'evidence_date':
            df[c] = pd.Series([None if pd.isna(x) or str(x).strip()=='' else str(x).strip() for x in df[c]], index=df.index, dtype=object)
        else:
            df[c] = df[c].astype(object)
    errors = []
    if df.destination_code.duplicated().any():
        errors.append('Duplicate destination_code: ' + str(df.loc[df.destination_code.duplicated(False),'destination_code'].tolist()))
    for i, r in zip(df.index, df.itertuples(index=False)):
        row = i + 2 if isinstance(i, int) else i
        if r.destination_code is None or r.destination_code not in valid_destination_codes:
            errors.append(f'row {row} destination_code: unknown/blank {r.destination_code!r}')
        if r.relevance_rating is not None:
            try:
                v = float(r.relevance_rating)
                if not np.isfinite(v) or not 0 <= v <= 5:
                    raise ValueError()
                df.at[i,'relevance_rating'] = v
            except (ValueError, TypeError):
                errors.append(f'row {row} relevance_rating: expected finite 0–5, got {r.relevance_rating!r}')
        v = r.evidence_date
        if pd.isna(v) or str(v).strip() == '':
            df.at[i,'evidence_date'] = None
        else:
            try:
                s = v.strftime('%Y-%m-%d') if isinstance(v, pd.Timestamp) else str(v)
                if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', s):
                    raise ValueError()
                df.at[i,'evidence_date'] = pd.Timestamp(s)
            except (ValueError, TypeError):
                errors.append(f'row {row} evidence_date: invalid YYYY-MM-DD {v!r}')
    if errors:
        raise ValueError('; '.join(errors))
    df.relevance_rating = pd.to_numeric(df.relevance_rating).astype(float)
    df.evidence_date = pd.to_datetime(df.evidence_date)
    return df

def load_relevance(path: str, valid_destination_codes: set[str]) -> pd.DataFrame:
    p = Path(path)
    df = pd.read_csv(p, dtype=str, keep_default_na=False) if p.exists() else pd.DataFrame(columns=RELEVANCE)
    return validate_relevance(df, valid_destination_codes)

def relevance_snapshot(df):
    return tuple(RelevanceInputSnapshot(str(r.destination_code), *[None if pd.isna(v) else v for v in (r.relevance_rating,r.rationale,r.evidence_source,r.evidence_date)]) for r in df.sort_values('destination_code', kind='stable').itertuples())
