from dataclasses import replace
import re
import numpy as np
import pandas as pd
import pytest
from src.contracts import *
from src.calculate_summaries import calculate_summaries
from src.rendering import timeline,make_figures,body_sections
from src.export_briefing import export_briefing
from src.notebook_workflow import NotebookSession
from tests.test_calculation import run,documented

def test_preview_export_complete_and_escaping(quotes,prep,tmp_path):
    rel=documented(); rel.loc[0,'rationale']='<script>alert(1)</script>'
    a=run(quotes,prep,rel)
    original=a.provider_details.copy(deep=True)
    html=''.join(body_sections(a,2))
    assert 'Showing 2 of 6 service rows' in html
    assert '&lt;script&gt;' in html and '<script>' not in html
    one=export_briefing(a,tmp_path); two=export_briefing(a,tmp_path)
    assert one!=two and one.exists() and two.exists()
    text=one.read_text()
    assert 'Showing 6 of 6 service rows' in text
    assert 'data:image/png;base64,' in text
    assert not re.search(r'<(?:script|link)\b|src="https?://',text)
    pd.testing.assert_frame_equal(original,a.provider_details)
    bad=replace(a,fee_summary=a.fee_summary.drop(columns=['fee_currency','fee_observations']))
    with pytest.raises(ValueError,match='fee_currency, fee_observations'): export_briefing(bad,tmp_path)

def test_chart_calendar_gaps(quotes,prep):
    q=quotes.copy(); q.loc[q.period.eq('2024_2Q'),'period']='2024_3Q'; q.period_start=q.period.map(period_start)
    ps,ds=resolve_choices(q,[],[])
    a=calculate_summaries(q,200,pd.DataFrame(columns=RELEVANCE),ScoringWeights(),[],[],ps,ds,prep,available_periods=tuple(ps))
    periods,labels=timeline(a)
    assert periods==['2024_1Q','2024_2Q','2024_3Q']
    assert 'No survey data' in labels[1]
    figs=make_figures(a)
    assert np.isnan(figs[0].axes[0].lines[0].get_ydata()[1])
    b=replace(a,metadata=replace(a.metadata,available_periods=('2024_1Q','2024_2Q','2024_3Q')))
    assert 'Not selected' in timeline(b)[1][1]
    assert a.metadata.resolved_periods==('2024_1Q','2024_3Q')

def test_guard_and_mutation(quotes,prep,tmp_path):
    s=NotebookSession(quotes,prep)
    rel=documented(); w=ScoringWeights()
    args=([],[],200,w,rel)
    with pytest.raises(ValueError,match='Rerun'): s.export(*args,output_dir=tmp_path)
    s.analyze(*args,provider_preview_rows=1)
    original=s.last_successful_results
    with pytest.raises(ValueError,match='Rerun'): s.export([],[],500,w,rel,output_dir=tmp_path)
    assert not list(tmp_path.iterdir())
    rel.loc[0,'relevance_rating']=5
    assert original.metadata.validated_relevance_snapshot[1].relevance_rating==3
    with pytest.raises(ValueError): s.export(*args,output_dir=tmp_path)
    s.analyze([],[],500,w,rel,provider_preview_rows=2)
    assert s.export([],[],500,w,rel,output_dir=tmp_path).exists()
    successful=s.last_successful_results
    with pytest.raises(ValueError): s.analyze(['BAD'],[],500,w,rel)
    assert s.last_successful_results is successful
    with pytest.raises(ValueError): s.export([],[],500,w,rel,output_dir=tmp_path)

def test_missing_relevance_guard(quotes,prep,tmp_path):
    s=NotebookSession(quotes,prep)
    rel=pd.DataFrame([['MEX',None,'partial',None,None]],columns=RELEVANCE)
    s.analyze([],[],200,ScoringWeights(),rel)
    assert s.export([],[],200,ScoringWeights(),rel,tmp_path).exists()

@pytest.mark.parametrize('size',[0,-1,True,1.5])
def test_bad_preview(quotes,prep,size):
    from src.present_results import present_results
    with pytest.raises(ValueError,match='positive integer'): present_results(run(quotes,prep),size)

def test_large_preview_and_changes_do_not_limit_export(quotes,prep,tmp_path):
    q=pd.concat([quotes]*20,ignore_index=True); q['id']=[str(i) for i in range(len(q))]
    a=run(q,prep)
    default=''.join(body_sections(a,100)); custom=''.join(body_sections(a,3))
    assert 'Showing 100 of 120 service rows' in default
    assert 'Showing 3 of 120 service rows' in custom
    assert len(a.provider_details)==120
    assert 'Showing 120 of 120 service rows' in export_briefing(a,tmp_path).read_text()

def test_selected_destination_empty_quarter_and_empty_result(quotes,prep,tmp_path):
    q=quotes.copy(); q.loc[q.destination_code.eq('IND'),'period']='2024_3Q';q.period_start=q.period.map(period_start)
    ps,ds=resolve_choices(q,['2024_1Q','2024_3Q'],['MEX'])
    f=q[q.destination_code.eq('MEX') & q.period.isin(ps)].copy()
    a=calculate_summaries(f,200,pd.DataFrame(columns=RELEVANCE),ScoringWeights(),ps,['MEX'],ps,ds,prep,available_periods=('2024_1Q','2024_2Q','2024_3Q'))
    assert a.metadata.resolved_periods==('2024_1Q','2024_3Q') and len(a.period_summary)==1
    fig=make_figures(a)[0]
    assert np.isnan(fig.axes[0].lines[0].get_ydata()[2])
    empty=calculate_summaries(f.iloc[:0],200,pd.DataFrame(columns=RELEVANCE),ScoringWeights(),ps,['MEX'],ps,ds,prep)
    html=export_briefing(empty,tmp_path).read_text()
    assert 'No matching quotes' in html and 'Showing 0 of 0 service rows' in html and 'Mexico (MEX)' in html
    assert '<img' not in html
