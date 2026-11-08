"""Export Elena's case and render review PNGs; does not modify app or images."""
from pathlib import Path
import hashlib
import html
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT.parent / 'tmp/pdfs/packages'
sys.path.insert(0, str(TOOLS))
import mistune
import pypdfium2 as pdfium
from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Image,
    Table, TableStyle, PageBreak, NextPageTemplate, KeepTogether,
)

CASES = ROOT / 'cases/elena'
WORK = ROOT.parent / 'tmp/pdfs/elena-finalization'
WORK.mkdir(parents=True, exist_ok=True)
SOURCE = CASES / 'elena-remittance-trends.md'
FINAL = CASES / 'elena-remittance-trends-final.md'
PDF = CASES / 'elena-remittance-trends.pdf'

def final_text():
    text = SOURCE.read_text(encoding='utf-8')
    professor = (ROOT.parent / '11-prove-mw/my-case.md').read_text(encoding='utf-8')
    title = text.splitlines()[0]
    text = title + '\n\n' + text[text.index('## 1.'):]
    text = re.sub(r'<!--[\s\S]*?-->', '', text)
    for quote in re.findall(r'(?m)(?:^>.*(?:\n|$))+', professor):
        text = text.replace(quote, '')
    bottom = ('**Publication recommendation.** Use the app to inspect and check a qualified '
              'description of historical USA-Mexico USD 200 quotes. Publish the three observed '
              'medians with the missing Q2 interval and service-comparability limitation; '
              'do not turn the lower endpoint into a consumer-savings, affordability or policy-effect claim.')
    text = text.replace(title, title + '\n\n' + bottom, 1)
    # Put the numerical summary with the selection rationale before full-page
    # evidence figures, avoiding a mostly empty introductory page.
    data_start = text.index('**What they see:**')
    data_end = text.index('## 4.', data_start)
    data = text[data_start:data_end]
    text = text[:data_start] + text[data_end:]
    image_start = text.index('![Public dashboard saved analysis')
    text = text[:image_start] + data + '\n' + text[image_start:]
    # The working case retains the full code excerpt. The memo retains the
    # median and key formulas; complete runnable definitions remain linked.
    code = re.search(r'```python\n([\s\S]*?)\n```', text).group(1)
    import ast
    tree = ast.parse(code)
    selected = [ast.get_source_segment(code, node) for node in tree.body
                if isinstance(node, ast.FunctionDef) and node.name in
                {'median', 'normalized', 'signature'}]
    compact = '\n\n'.join(selected)
    compact = '\n'.join(line for line in compact.splitlines()
                        if not line.lstrip().startswith('#'))
    text = text.replace('```python\n' + code + '\n```',
                        '```python\n' + compact + '\n```')
    for char in ('\u2011', '\u2013', '\u2014'):
        text = text.replace(char, '-')
    return re.sub(r'\n{3,}', '\n\n', text).strip() + '\n'

for name, file in [('Body','calibri.ttf'),('Body-Bold','calibrib.ttf'),
                   ('Body-Italic','calibrii.ttf'),('Body-BoldItalic','calibriz.ttf'),
                   ('Mono','consola.ttf')]:
    pdfmetrics.registerFont(TTFont(name, 'C:/Windows/Fonts/' + file))
pdfmetrics.registerFontFamily('Body',normal='Body',bold='Body-Bold',italic='Body-Italic',boldItalic='Body-BoldItalic')

STYLES = {
    'body': ParagraphStyle('body',fontName='Body',fontSize=10.5,leading=14,spaceAfter=8,splitLongWords=True),
    'h1': ParagraphStyle('h1',fontName='Body-Bold',fontSize=20,leading=24,spaceAfter=15,keepWithNext=True),
    'h2': ParagraphStyle('h2',fontName='Body-Bold',fontSize=15,leading=19,spaceBefore=13,spaceAfter=9,keepWithNext=True),
    'h3': ParagraphStyle('h3',fontName='Body-Bold',fontSize=12,leading=15,spaceBefore=9,spaceAfter=7,keepWithNext=True),
    'quote': ParagraphStyle('quote',fontName='Body',fontSize=10.3,leading=14,leftIndent=12,borderColor=colors.HexColor('#9aabba'),borderWidth=0.7,borderPadding=8,spaceBefore=5,spaceAfter=12),
    'code': ParagraphStyle('code',fontName='Mono',fontSize=7.8,leading=10,backColor=colors.HexColor('#f1f4f7'),borderPadding=7,spaceBefore=5,spaceAfter=10,wordWrap='CJK'),
    'cell': ParagraphStyle('cell',fontName='Body',fontSize=8.5,leading=11,spaceAfter=0),
    'headcell': ParagraphStyle('headcell',fontName='Body-Bold',fontSize=8.5,leading=11,spaceAfter=0),
    'caption': ParagraphStyle('caption',fontName='Body',fontSize=9.5,leading=12,spaceBefore=7,spaceAfter=0),
    'figuretitle': ParagraphStyle('figuretitle',fontName='Body-Bold',fontSize=12,leading=15,spaceAfter=6),
}

def inline(tokens):
    result = ''
    for t in tokens:
        typ = t['type']
        if typ == 'text': result += html.escape(t.get('raw',''))
        elif typ in ('softbreak','linebreak'): result += '<br/>' if typ == 'linebreak' else ' '
        elif typ == 'strong': result += '<b>' + inline(t['children']) + '</b>'
        elif typ == 'emphasis': result += '<i>' + inline(t['children']) + '</i>'
        elif typ == 'codespan': result += '<font name="Mono" size="8.4">' + html.escape(t['raw']) + '</font>'
        elif typ == 'link': result += '<link href="' + html.escape(t['attrs']['url'],quote=True) + '" color="#145787">' + inline(t['children']) + '</link>'
        elif typ == 'inline_html': result += html.escape(t.get('raw',''))
        else: result += inline(t.get('children',[]))
    return result

def para(token, style='body'):
    return Paragraph(inline(token.get('children',[])), STYLES[style])

def blocks(tokens, style='body'):
    result=[]
    for t in tokens:
        typ=t['type']
        if typ in ('blank_line','block_html'): continue
        if typ in ('paragraph','block_text'):
            paragraph=para(t,style)
            if inline(t.get('children',[])).startswith('<b>Reproducible independent check.'):
                result.append(KeepTogether([paragraph]))
            else:
                result.append(paragraph)
        elif typ=='heading': result.append(para(t,'h'+str(min(t['attrs']['level'],3))))
        elif typ=='block_quote': result.extend(blocks(t['children'],'quote'))
        elif typ=='list':
            for item in t['children']:
                for child in item['children']:
                    if child['type'] in ('paragraph','block_text'):
                        result.append(Paragraph(inline(child['children']),STYLES['body'],bulletText='\u2022'))
                    else: result.extend(blocks([child],style))
        elif typ=='block_code':
            raw=t['raw'].rstrip('\n')
            if t.get('attrs',{}).get('info')=='markdown' and raw.startswith('### CR-'):
                result.extend(blocks(mistune.create_markdown(renderer='ast',plugins=['table'])(raw)))
            else:
                result.append(KeepTogether([Paragraph('<br/>'.join(html.escape(line).replace(' ','&#160;') or '&#160;' for line in raw.splitlines()),STYLES['code'])]))
        elif typ=='table':
            rows=[]
            for group in t['children']:
                if group['type']=='table_head': rows.append([Paragraph(inline(c['children']),STYLES['headcell']) for c in group['children']])
                elif group['type']=='table_body':
                    rows.extend([[Paragraph(inline(c['children']),STYLES['cell']) for c in row['children']] for row in group['children']])
            width=516
            widths=([78,73,89,94,94,88] if len(rows[0])==6 else [122,112,282])
            table=Table(rows,colWidths=widths,repeatRows=1,hAlign='LEFT')
            table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e9f0f5')),('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#becbd5')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
            result.extend([table,Spacer(1,11)])
        else: raise ValueError('Unhandled Markdown block: '+typ)
    return result

def footer(canvas,doc):
    canvas.saveState();w,h=canvas._pagesize
    canvas.setFont('Body',8);canvas.setFillColor(colors.HexColor('#526373'))
    canvas.drawString(36,18,'Elena | Historical remittance-cost evidence')
    canvas.drawRightString(w-36,18,str(doc.page));canvas.restoreState()

def build():
    final=final_text()
    # Regenerate this task's export derivative; retain the professor's original
    # instructions and complete calculations in the separate working Markdown.
    FINAL.write_text(final,encoding='utf-8')
    tokens=mistune.create_markdown(renderer='ast',plugins=['table'])(final)
    portrait=letter;wide=landscape(letter)
    doc=BaseDocTemplate(str(PDF),pagesize=portrait,title='Elena - Historical remittance-cost claims',author='Nicharee Ratanajaratkul (Prae)',leftMargin=48,rightMargin=48,topMargin=40,bottomMargin=36)
    doc.addPageTemplates([
        PageTemplate(id='Text',frames=[Frame(48,36,516,716,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)],pagesize=portrait,onPage=footer),
        PageTemplate(id='Figure',frames=[Frame(24,30,744,558,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)],pagesize=wide,onPage=footer),
    ])
    story=[];mode='Text';i=0;figures=0
    while i<len(tokens):
        t=tokens[i]
        image=t['type']=='paragraph' and len(t.get('children',[]))==1 and t['children'][0]['type']=='image'
        if image:
            j=i+1
            while j<len(tokens) and tokens[j]['type']=='blank_line':j+=1
            caption=tokens[j]
            if caption['type']!='paragraph':raise ValueError('Missing image caption')
            figures+=1;story.extend([NextPageTemplate('Figure'),PageBreak()]);mode='Figure'
            cap=para(caption,'caption');_,capheight=cap.wrap(744,550)
            img=Image(str(CASES/t['children'][0]['attrs']['url']))
            maxheight=558-21-capheight-10
            ratio=min(744/img.imageWidth,maxheight/img.imageHeight)
            img.drawWidth=img.imageWidth*ratio;img.drawHeight=img.imageHeight*ratio
            story.extend([Paragraph('Live dashboard evidence - Figure '+str(figures),STYLES['figuretitle']),img,cap])
            i=j+1;continue
        if t['type']!='blank_line' and mode=='Figure':
            story.extend([NextPageTemplate('Text'),PageBreak()]);mode='Text'
        if t['type']=='heading' and t['attrs']['level']==2:
            heading=inline(t.get('children',[]))
            if heading.startswith(('3.', '5.')):
                story.append(PageBreak())
        story.extend(blocks([t]));i+=1
    if figures!=6:raise ValueError('Expected six unmodified screenshots')
    doc.build(story)
    reader=PdfReader(str(PDF));links=[]
    for page in reader.pages:
        for ann in page.get('/Annots',[]):
            a=ann.get_object().get('/A',{})
            if a.get('/URI'):links.append(str(a['/URI']))
    renderdir=WORK/'pages';renderdir.mkdir(exist_ok=True)
    rendered=pdfium.PdfDocument(str(PDF))
    for n,page in enumerate(rendered):
        page.render(scale=1.5).to_pil().save(renderdir/f'page-{n+1:02}.png')
    text='\n'.join(page.extract_text() or '' for page in reader.pages)
    (WORK/'extracted-text.txt').write_text(text,encoding='utf-8')
    manifest={'pages':len(reader.pages),'embedded_images':sum(len(page.images) for page in reader.pages),'external_source_links':sorted(set(u for u in links if u.startswith('https://'))),'all_links':links,'pdf':str(PDF),'rendered_pages':str(renderdir)}
    (WORK/'pdf-checks.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps(manifest,indent=2))

if __name__=='__main__':build()
