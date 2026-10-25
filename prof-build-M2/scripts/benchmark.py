"""Real data benchmark; startup and full HTML exports excluded from interaction target."""
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import platform
import resource
import statistics
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from IPython.utils.capture import capture_output
from src.contracts import *
from src.load_data import load_data,load_preparation_metadata
from src.load_relevance import load_relevance
from src.calculate_summaries import calculate_summaries
from src.filter_data import filter_quotes
from src.present_results import present_results
from src.export_briefing import export_briefing

out=Path('artifacts'); out.mkdir(exist_ok=True)
start=time.perf_counter()
p='data/rpw_usa_clean.csv.gz'
meta=load_preparation_metadata(p+'.validation.json',p)
q=load_data(p,meta)
startup=time.perf_counter()-start
rel=load_relevance('inputs/community_relevance.csv',set(q.destination_code))
available=tuple(sorted(q.period.unique(),key=period_key))
report={'platform':platform.platform(),'python':platform.python_version(),'processor':platform.processor(),'cpu_model':next((l.split(':',1)[1].strip() for l in Path('/proc/cpuinfo').read_text().splitlines() if l.startswith('model name')),'unknown'),'logical_cpus':__import__('os').cpu_count(),'system_memory_kib':Path('/proc/meminfo').read_text().splitlines()[0],'startup_seconds':startup,'dataframe_bytes':int(q.memory_usage(deep=True).sum()),'rows':len(q),'selections':{}}
for name,ps,ds in [('default',[available[-1]],['MEX']),('all',[],[])]:
    timings=[]; breakdown=[]
    rp,rd=resolve_choices(q,ps,ds)
    for i in range(5):
        start=time.perf_counter()
        f=filter_quotes(q,rp,[d.destination_code for d in rd]); a=time.perf_counter()
        results=calculate_summaries(f,200,rel,ScoringWeights(),ps,ds,rp,rd,meta,available_periods=available); b=time.perf_counter()
        with capture_output(): present_results(results)
        end=time.perf_counter()
        timings.append(end-start); breakdown.append({'filter':a-start,'calculate':b-a,'render':end-b})
    start=time.perf_counter(); html=export_briefing(results); export_time=time.perf_counter()-start
    report['selections'][name]={'seconds':timings,'median_seconds':statistics.median(timings),'breakdown':breakdown,'matching_rows':len(f),'export_seconds':export_time,'export_path':str(html),'export_bytes':html.stat().st_size}
    print(name,report['selections'][name],flush=True)
report['peak_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
(out/'benchmark.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
