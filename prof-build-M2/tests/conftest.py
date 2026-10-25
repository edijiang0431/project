import pandas as pd
import pytest
from src.contracts import *

@pytest.fixture
def prep():
    return PreparationMetadata(1,'fixture.xlsx','0'*64,'fixture.csv.gz','1'*64,pd.Timestamp('2026-01-01',tz='UTC'),('fixture',),(),())
@pytest.fixture
def quotes():
    records=[]
    for i,(code,name,period,cost) in enumerate([('MEX','Mexico','2024_1Q',4),('MEX','Mexico','2024_1Q',6),('MEX','Mexico','2024_2Q',8),('IND','India','2024_1Q',3),('IND','India','2024_1Q',5),('IND','India','2024_2Q',None)]):
        r={c:None for c in PREPARED}
        r.update(id=str(i),period=period,source_code='USA',source_name='United States',destination_code=code,destination_name=name,firm='Provider',access_point='Internet',transparent='yes',date=pd.Timestamp('2024-01-20'),period_start=period_start(period),corridor='USA'+code,corridor_label='United States to '+name)
        for c in NUMERIC: r[c]=float('nan')
        r.update(cc1_total_cost_pct=cost,cc1_lcu_fee=2.,cc1_fx_margin=1.,cc1_lcu_code='USD',cc2_total_cost_pct=10. if cost is not None else None,cc2_lcu_fee=7.,cc2_fx_margin=3.,cc2_lcu_code='EUR')
        records.append(r)
    df=pd.DataFrame(records)
    for c in NUMERIC: df[c]=pd.to_numeric(df[c]).astype(float)
    return df
