from pathlib import Path
import uuid
import pandas as pd
from .contracts import validate_results
from .rendering import STYLE, body_sections, header_html

def export_briefing(results, output_dir: str='exports') -> Path:
    validate_results(results)
    stamp=pd.Timestamp.now(tz='UTC')
    sections=body_sections(results)
    sections[0]=header_html(results,stamp.isoformat())
    html='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>RemitRight LA briefing</title><style>'+STYLE+'</style></head><body><main>'+''.join(sections)+'</main></body></html>'
    out=Path(output_dir); out.mkdir(parents=True,exist_ok=True)
    path=out/f'remitright_briefing_{stamp.strftime("%Y%m%d_%H%M%S")}_{uuid.uuid4().hex[:12]}.html'
    with path.open('x',encoding='utf-8') as f: f.write(html)
    return path
