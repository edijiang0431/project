import pandas as pd
from .contracts import require_columns, canonical_selection, period_key

def filter_quotes(quotes: pd.DataFrame, periods: list[str], destination_codes: list[str]) -> pd.DataFrame:
    require_columns(quotes, ['source_code','period','destination_code'])
    if quotes.empty:
        raise ValueError('Prepared data is empty')
    for c in ['source_code','period','destination_code']:
        if quotes[c].isna().any() or quotes[c].astype(str).str.strip().eq('').any():
            raise ValueError(f'Missing/blank {c}')
    if not quotes.source_code.eq('USA').all():
        raise ValueError('Only USA source rows are valid')
    if 'destination_name' in quotes:
        if quotes.destination_name.isna().any() or quotes.destination_name.astype(str).str.strip().eq('').any():
            raise ValueError('Missing/blank destination_name')
        if quotes.groupby('destination_code').destination_name.nunique().gt(1).any():
            raise ValueError('Conflicting destination names')
    for p in quotes.period.unique():
        period_key(p)
    ps = canonical_selection(periods, 'periods')
    ds = canonical_selection(destination_codes, 'destination_codes')
    bp, bd = sorted(set(ps)-set(quotes.period)), sorted(set(ds)-set(quotes.destination_code))
    if bp or bd:
        raise ValueError(f'Invalid periods: {bp}; invalid destinations: {bd}. Valid periods: {sorted(quotes.period.unique())}; valid destinations: {sorted(quotes.destination_code.unique())}')
    mask = pd.Series(True, index=quotes.index)
    if ps:
        mask &= quotes.period.isin(ps)
    if ds:
        mask &= quotes.destination_code.isin(ds)
    return quotes.loc[mask].copy()
