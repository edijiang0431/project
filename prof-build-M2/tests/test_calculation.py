from dataclasses import replace
import numpy as np
import pandas as pd
import pytest
from src.contracts import *
from src.calculate_summaries import calculate_summaries, classify_channel, RELATIVE_REASON
from src.load_relevance import validate_relevance, load_relevance

def run(q,prep,rel=None,weights=ScoringWeights(),amount=200):
    ps,ds=resolve_choices(q,[],[])
    return calculate_summaries(q,amount,pd.DataFrame(columns=RELEVANCE) if rel is None else rel,weights,[],[],ps,ds,prep,available_periods=tuple(ps))
def documented():
    return pd.DataFrame([['MEX',3,'test only','synthetic fixture','2024-01-01'],['IND',3,'test only','synthetic fixture','2024-01-01']],columns=RELEVANCE)
def test_fixture(quotes,prep):
    before=quotes.copy(deep=True)
    a=run(quotes,prep)
    assert a.corridor_summary.destination_code.tolist()==['IND','MEX']
    assert a.corridor_summary.median_total_cost.tolist()==[4,6]
    assert a.corridor_summary.observations.tolist()==[2,3]
    p=a.period_summary.iloc[1]
    assert p.observations==0 and p.total_quotes==1 and pd.isna(p.median_total_cost) and p.non_transparent_quote_share==0
    b=run(quotes,prep,documented())
    assert b.corridor_summary.destination_code.tolist()==['MEX','IND']
    assert b.corridor_summary.campaign_priority_score.tolist()==[.65,.15]
    pd.testing.assert_frame_equal(before,quotes)
def test_amount_currency_counts(quotes,prep):
    quotes.loc[0,'cc1_lcu_fee']=np.nan
    quotes.loc[1,'transparent']='no'
    a,b=run(quotes,prep),run(quotes,prep,amount=500)
    assert len(a.provider_details)==len(b.provider_details)==6
    assert a.fee_summary.fee_currency.unique().tolist()==['USD']
    assert b.fee_summary.fee_currency.unique().tolist()==['EUR']
    assert set(b.provider_details.transfer_fee)=={7}
    assert a.fee_summary.fee_observations.sum()==4
    assert a.fx_margin_summary.fx_margin_observations.sum()==5
    r=a.provider_details.loc[a.provider_details.service_id.eq('1')].iloc[0]
    assert pd.isna(r.total_cost_pct) and pd.isna(r.exchange_rate_margin) and r.transfer_fee==2
    pd.testing.assert_series_equal(a.corridor_summary.non_transparent_quote_share,b.corridor_summary.non_transparent_quote_share)
def test_empty_nontransparent(quotes,prep):
    quotes.transparent='no'
    a=run(quotes,prep)
    assert a.corridor_summary.observations.sum()==0
    assert a.corridor_summary.non_transparent_quote_share.eq(1).all()
    ps,ds=resolve_choices(quotes,[],[])
    b=calculate_summaries(quotes.iloc[:0],200,pd.DataFrame(columns=RELEVANCE),ScoringWeights(),[],[],ps,ds,prep)
    for k,cols in SCHEMAS.items():
        assert getattr(b,k).empty and list(getattr(b,k))==cols
    assert b.metadata.collection_date_min is None
def test_scoring_rules(quotes,prep):
    q=quotes[quotes.destination_code.eq('MEX')].copy()
    a=run(q,prep)
    assert RELATIVE_REASON in a.corridor_summary.iloc[0].unscored_reasons
    b=run(q,prep,weights=ScoringWeights(0,1,0))
    assert b.corridor_summary.campaign_priority_score.iloc[0]==0
    assert pd.isna(b.corridor_summary.cost_normalized.iloc[0])
    quotes.cc1_total_cost_pct=6
    c=run(quotes,prep,documented())
    assert c.corridor_summary.cost_normalized.eq(0).all()
    assert c.corridor_summary.median_total_cost.eq(6).all()
    assert c.corridor_summary.destination_code.tolist()==['IND','MEX']
@pytest.mark.parametrize('w',[ScoringWeights(-1,1,1),ScoringWeights(np.nan,0,1),ScoringWeights(.5,.5,.5)])
def test_bad_weights(quotes,prep,w):
    with pytest.raises(ValueError): run(quotes,prep,weights=w)
@pytest.mark.parametrize('amount',[100,[200,500],200.,True])
def test_bad_amount(quotes,prep,amount):
    with pytest.raises(ValueError): run(quotes,prep,amount=amount)
@pytest.mark.parametrize('access,expected',[('Internet','Internet-only'),('Agent','Counter-only'),('Internet,Agent','Mixed'),('Call Center','Other/unknown'),('Internet,Unexpected','Other/unknown'),('', 'Other/unknown')])
def test_channels(access,expected):
    assert classify_channel(access)[0]==expected
def test_access_warnings(quotes,prep):
    quotes.access_point=['Internet,Unexpected,Unexpected','Internet,Unexpected','',None,'Call Center','Agent']
    a=run(quotes,prep)
    assert any("'unexpected': 2 distinct" in x for x in a.metadata.runtime_validation_warnings)
    assert any('Missing/blank access point' in x and '2 distinct' in x for x in a.metadata.runtime_validation_warnings)
    assert a.channel_summary.total_quotes.sum()==6
def test_relevance(tmp_path):
    assert load_relevance(tmp_path/'missing',{'MEX'}).empty
    r=pd.DataFrame([['MEX',0,'why','source','2024-02-29']],columns=RELEVANCE)
    assert validate_relevance(r,{'MEX'}).relevance_rating.iloc[0]==0
    for col,value in [('destination_code','BAD'),('relevance_rating','6'),('relevance_rating','nan'),('evidence_date','2024-02-30'),('evidence_date','1/1/2024')]:
        bad=r.copy(); bad[col]=value
        with pytest.raises(ValueError,match=col): validate_relevance(bad,{'MEX'})
    with pytest.raises(ValueError,match='Duplicate'): validate_relevance(pd.concat([r,r]),{'MEX'})
def test_pooled_and_order(quotes,prep):
    quotes=quotes.sample(frac=1,random_state=4)
    quotes.loc[quotes.destination_code.eq('MEX'),'cc1_total_cost_pct']=[1,1,9]
    a=run(quotes,prep)
    assert a.corridor_summary.loc[a.corridor_summary.destination_code.eq('MEX'),'median_total_cost'].iloc[0]==1
    assert a.provider_details.service_id.tolist()==['3','4','5','0','1','2']

def test_partial_zero_relevance_and_all_reasons(quotes,prep):
    rel=documented(); rel.loc[0,'evidence_source']=''
    a=run(quotes,prep,rel)
    mex=a.corridor_summary.loc[a.corridor_summary.destination_code.eq('MEX')].iloc[0]
    assert pd.isna(mex.campaign_priority_score) and mex.relevance_rationale=='test only'
    b=run(quotes,prep,rel,ScoringWeights(.5,.5,0))
    assert b.corridor_summary.campaign_priority_score.notna().all()
    assert pd.isna(b.corridor_summary.loc[b.corridor_summary.destination_code.eq('MEX'),'relevance_normalized'].iloc[0])
    quotes.cc1_total_cost_pct=np.nan
    c=run(quotes,prep)
    assert c.corridor_summary.unscored_reasons.iloc[0]==('Missing median cost','Missing documented community relevance')

def test_currency_order_and_provider_opaque_ids(quotes,prep):
    quotes['cc1_lcu_code']=['ZZZ',None,'AAA','ZZZ','AAA',None]
    quotes['id']=['9','10','2','a','b','c']
    a=run(quotes.sample(frac=1,random_state=10),prep)
    assert a.provider_details.service_id.tolist()==['a','b','c','10','9','2']
    for table in [a.fee_summary,a.fx_margin_summary]:
        assert table.fee_currency.iloc[:2].tolist()==['AAA','ZZZ']
        assert pd.isna(table.fee_currency.iloc[2])
    assert 'fee_currency' not in a.corridor_summary and len(a.corridor_summary)==2

def test_three_corridor_normalization_and_transparency(quotes,prep):
    third=quotes.iloc[:2].copy()
    third['id']=['third-a','third-b'];third['destination_code']='PHL';third['destination_name']='Philippines';third['cc1_total_cost_pct']=8.
    q=pd.concat([quotes,third],ignore_index=True)
    q.loc[0,'transparent']='no'; q.loc[1,'transparent']='no'
    a=run(q,prep)
    # The remaining Mexico quote is 8; India is 4; Philippines 8.
    vals=a.corridor_summary.set_index('destination_code')
    assert vals.loc['MEX','non_transparent_quote_share']==2/3
    assert vals.loc['MEX','cost_normalized']==1 and vals.loc['IND','cost_normalized']==0
    q.loc[q.destination_code.eq('MEX'),'transparent']='yes'
    b=run(q,prep).corridor_summary.set_index('destination_code')
    assert b.cost_normalized.to_dict()=={'IND':0.,'MEX':.5,'PHL':1.}
    assert b.relevance_normalized.isna().all()  # costs without relevance still set min/max
