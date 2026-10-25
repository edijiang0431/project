import pandas as pd
import pytest
from src.filter_data import filter_quotes
from src.contracts import resolve_choices

@pytest.fixture
def quotes():
    return pd.DataFrame(dict(source_code=['USA']*4,period=['2025_1Q','2025_3Q','2024_4Q','2025_3Q'],destination_code=['MEX','PHL','MEX','IND'],destination_name=['Mexico','Philippines','Mexico','India'],transparent=['yes','no','yes','yes'],cost=[None,2,3,4]),index=list('ABCD'))
@pytest.mark.parametrize('ps,ds,want', [(['2025_3Q'],['MEX','PHL'],'B'),(['2025_3Q'],[],'BD'),([],['MEX'],'AC'),([],[],'ABCD'),(['2025_1Q','2025_3Q'],['MEX','PHL'],'AB'),(['2025_1Q'],['PHL'],'')])
def test_filter(quotes,ps,ds,want):
    before=quotes.copy(deep=True)
    out=filter_quotes(quotes,ps,ds)
    assert ''.join(out.index)==want
    assert list(out)==list(quotes)
    pd.testing.assert_frame_equal(before,quotes)
def test_invalid(quotes):
    with pytest.raises(ValueError,match='BAD.*XXX'):
        filter_quotes(quotes,['BAD'],['XXX'])
    for c in ['source_code','period','destination_code']:
        bad=quotes.copy(); bad.loc['A',c]=''
        with pytest.raises(ValueError): filter_quotes(bad,[],[])
def test_resolution(quotes):
    ps,ds=resolve_choices(quotes,[],[])
    assert ps==['2024_4Q','2025_1Q','2025_3Q']
    assert [d.destination_code for d in ds]==['IND','MEX','PHL']
    bad=quotes.copy(); bad.loc['A','destination_name']='Wrong'
    with pytest.raises(ValueError,match='Conflicting'): resolve_choices(bad,[],[])
