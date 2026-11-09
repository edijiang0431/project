"""Render validation.md as an incomplete review PDF. Never alters cases or the final PDF."""
from pathlib import Path
import sys,re,html,json
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'tmp/pdfs/packages'))
import mistune
import pypdfium2 as pdfium
from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter,landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate,PageTemplate,Frame,Paragraph,Spacer,Table,TableStyle,Image,PageBreak,NextPageTemplate

WORK=ROOT.parent/'tmp/pdfs/combined-validation'
WORK.mkdir(parents=True,exist_ok=True)
for name,file in [('Body','calibri.ttf'),('Body-Bold','calibrib.ttf'),('Body-Italic','calibrii.ttf'),('Body-BoldItalic','calibriz.ttf'),('Mono','consola.ttf')]:
    pdfmetrics.registerFont(TTFont(name,'C:/Windows/Fonts/'+file))
pdfmetrics.registerFontFamily('Body',normal='Body',bold='Body-Bold',italic='Body-Italic',boldItalic='Body-BoldItalic')
STYLES={
 'body':ParagraphStyle('body',fontName='Body',fontSize=10.5,leading=14.3,spaceAfter=8),
 'h1':ParagraphStyle('h1',fontName='Body-Bold',fontSize=18,leading=23,spaceBefore=12,spaceAfter=12,keepWithNext=True),
 'h2':ParagraphStyle('h2',fontName='Body-Bold',fontSize=15,leading=19,spaceBefore=12,spaceAfter=9,keepWithNext=True),
 'h3':ParagraphStyle('h3',fontName='Body-Bold',fontSize=12,leading=16,spaceBefore=10,spaceAfter=7,keepWithNext=True),
 'h4':ParagraphStyle('h4',fontName='Body-Bold',fontSize=11,leading=14,spaceBefore=8,spaceAfter=7,keepWithNext=True),
 'quote':ParagraphStyle('quote',fontName='Body',fontSize=10.5,leading=14.3,leftIndent=12,spaceAfter=9),
 'code':ParagraphStyle('code',fontName='Mono',fontSize=8,leading=10.5,backColor=colors.HexColor('#f0f3f6'),borderPadding=6,spaceBefore=6,spaceAfter=10,wordWrap='CJK'),
 'cell':ParagraphStyle('cell',fontName='Body',fontSize=9,leading=12),
 'headcell':ParagraphStyle('headcell',fontName='Body-Bold',fontSize=9,leading=12),
 'caption':ParagraphStyle('caption',fontName='Body',fontSize=10,leading=13,spaceAfter=5),
}
def inline(tokens):
    result=''
    for t in tokens:
        typ=t['type']
        if typ=='text':result+=html.escape(t.get('raw',''))
        elif typ in ['softbreak','linebreak']:result+=' '
        elif typ=='strong':result+='<b>'+inline(t['children'])+'</b>'
        elif typ=='emphasis':result+='<i>'+inline(t['children'])+'</i>'
        elif typ=='codespan':result+='<font name="Mono" size="8.4">'+html.escape(t['raw'])+'</font>'
        elif typ=='link':result+='<link href="'+html.escape(t['attrs']['url'],quote=True)+'" color="#145787">'+inline(t['children'])+'</link>'
        elif typ=='inline_html':result+=html.escape(t.get('raw',''))
        else:result+=inline(t.get('children',[]))
    return result
def paragraph(token,style='body'):return Paragraph(inline(token.get('children',[])),STYLES[style])
parser=mistune.create_markdown(renderer='ast',plugins=['table','url'])
def blocks(tokens,style='body'):
    out=[]
    for t in tokens:
        typ=t['type']
        if typ in ['blank_line','block_html']:continue
        if typ in ['paragraph','block_text']:out.append(paragraph(t,style))
        elif typ=='heading':out.append(paragraph(t,'h'+str(min(t['attrs']['level'],4))))
        elif typ=='block_quote':out.extend(blocks(t['children'],'quote'))
        elif typ=='list':
            for item in t['children']:
                for c in item['children']:
                    if c['type'] in ['paragraph','block_text']:out.append(Paragraph(inline(c['children']),STYLES[style],bulletText='\u2022'))
                    else:out.extend(blocks([c],style))
        elif typ=='block_code':
            raw=t['raw'].rstrip('\n')
            if t.get('attrs',{}).get('info')=='markdown' and raw.startswith('### CR-'):out.extend(blocks(parser(raw)))
            else:out.append(Paragraph('<br/>'.join(html.escape(x).replace(' ','&#160;') or '&#160;' for x in raw.splitlines()),STYLES['code']))
        elif typ=='table':
            rows=[]
            for group in t['children']:
                if group['type']=='table_head':rows.append([paragraph(c,'headcell') for c in group['children']])
                else:
                    for row in group['children']:rows.append([paragraph(c,'cell') for c in row['children']])
            n=len(rows[0]);widths={3:[160,140,232],4:[205,125,101,101],6:[75,73,95,100,95,94]}.get(n,[532/n]*n)
            table=Table(rows,colWidths=widths,repeatRows=1,hAlign='LEFT')
            table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e6eef4')),('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#bdcbd6')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
            out.extend([table,Spacer(1,10)])
        elif typ=='thematic_break':out.append(Spacer(1,10))
        else:raise ValueError('Unsupported Markdown token '+typ)
    return out
def decorate(canvas,doc):
    w,h=canvas._pagesize;canvas.saveState()
    canvas.setFont('Body-Bold',8);canvas.setFillColor(colors.HexColor('#8a3d18'))
    canvas.drawString(30,h-20,'INCOMPLETE TEAM REVIEW DRAFT | Sections 3 and 4 pending')
    canvas.setFont('Body',8);canvas.setFillColor(colors.HexColor('#526373'))
    canvas.drawString(30,17,'RemitRight LA | Validation draft');canvas.drawRightString(w-30,17,str(doc.page));canvas.restoreState()
def build():
    text=(ROOT/'validation.md').read_text(encoding='utf8')
    tokens=parser(text);story=[];mode='Text';i=0;figures=0;active_case='';pending_intro=None
    doc=BaseDocTemplate(str(ROOT/'validation-draft.pdf'),pagesize=letter,title='INCOMPLETE TEAM REVIEW DRAFT - RemitRight LA validation',author='RemitRight LA team')
    doc.addPageTemplates([PageTemplate(id='Text',frames=[Frame(40,36,532,716,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)],pagesize=letter,onPage=decorate),PageTemplate(id='Figure',frames=[Frame(24,32,744,540,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)],pagesize=landscape(letter),onPage=decorate)])
    while i<len(tokens):
        t=tokens[i]
        image=t['type']=='paragraph' and len(t.get('children',[]))==1 and t['children'][0]['type']=='image'
        if image:
            path=t['children'][0]['attrs']['url']
            if re.search(r'jiayi-source-page-[56]-visible-1\.png$',path):
                # Keep the original address-bar excerpt with its app-view excerpt.
                j=i+1
                while tokens[j]['type']=='blank_line':j+=1
                caption_token=tokens[j];k=j+1
                while tokens[k]['type']=='blank_line':k+=1
                second=tokens[k]
                second_path=second['children'][0]['attrs']['url']
                assert second_path==path.replace('visible-1.png','visible-2.png')
                end=k+1
                while tokens[end]['type']=='blank_line':end+=1
                assert tokens[end]['type']=='paragraph'
                cap=paragraph(caption_token,'caption');cap_height=cap.wrap(744,540)[1]
                bar=Image(str(ROOT/path));view=Image(str(ROOT/second_path))
                r=min(744/bar.imageWidth,32/bar.imageHeight)
                bar.drawWidth=bar.imageWidth*r;bar.drawHeight=bar.imageHeight*r
                r=min(744/view.imageWidth,(540-bar.drawHeight-cap_height-20)/view.imageHeight)
                view.drawWidth=view.imageWidth*r;view.drawHeight=view.imageHeight*r
                story.extend([NextPageTemplate('Figure'),PageBreak(),bar,Spacer(1,6),view,Spacer(1,8),cap])
                mode='Figure';figures+=2;i=end+1;continue
            figures+=1
            story.extend([NextPageTemplate('Figure'),PageBreak()]);mode='Figure'
            j=i+1
            while j<len(tokens) and tokens[j]['type']=='blank_line':j+=1
            caption=None
            if j<len(tokens) and tokens[j]['type']=='paragraph' and tokens[j].get('children') and tokens[j]['children'][0]['type']=='emphasis':
                caption=paragraph(tokens[j],'caption')
            cap_height=caption.wrap(744,540)[1] if caption else 0
            intro_height=pending_intro.wrap(744,540)[1]+10 if pending_intro else 0
            picture=Image(str(ROOT/path));maxheight=540-cap_height-intro_height-12
            ratio=min(744/picture.imageWidth,maxheight/picture.imageHeight)
            picture.drawWidth=picture.imageWidth*ratio;picture.drawHeight=picture.imageHeight*ratio
            if pending_intro:story.extend([pending_intro,Spacer(1,10)]);pending_intro=None
            story.append(picture)
            if caption:story.extend([Spacer(1,8),caption])
            i=(j+1) if caption else i+1;continue
        if t['type']=='paragraph' and inline(t.get('children',[])).startswith('<b>Provider evidence,'):
            j=i+1
            while j<len(tokens) and tokens[j]['type']=='blank_line':j+=1
            if j<len(tokens) and tokens[j]['type']=='paragraph' and tokens[j].get('children') and tokens[j]['children'][0]['type']=='image':
                pending_intro=paragraph(t,'caption');i=j;continue
        if t['type']!='blank_line' and mode=='Figure':story.extend([NextPageTemplate('Text'),PageBreak()]);mode='Text'
        if t['type']=='heading':
            title=inline(t.get('children',[]))
            if t['attrs']['level']==2 and re.match(r'2\.[1-5] ',title):active_case=title[:3]
            if t['attrs']['level']==1 and re.match(r'[234]\. ',title) and not isinstance(story[-1],PageBreak):story.append(PageBreak())
            elif t['attrs']['level']==2 and re.match(r'2\.[2-5] ',title):story.append(PageBreak())
            elif active_case=='2.1' and title.startswith('5. The verdict') and not isinstance(story[-1],PageBreak):story.append(PageBreak())
        story.extend(blocks([t]));i+=1
    doc.build(story)
    pdf=PdfReader(str(ROOT/'validation-draft.pdf'))
    rendered=pdfium.PdfDocument(str(ROOT/'validation-draft.pdf'))
    pages=WORK/'pages';pages.mkdir(exist_ok=True)
    for n,page in enumerate(rendered):page.render(scale=1.4).to_pil().save(pages/f'page-{n+1:02}.png')
    report={'pages':len(pdf.pages),'figures':figures,'page_text':[p.extract_text() or '' for p in pdf.pages],'image_pages':[(n+1,len(p.images)) for n,p in enumerate(pdf.pages) if len(p.images)]}
    (WORK/'render-report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print('Rendered',len(pdf.pages),'pages with',figures,'evidence images. Review PNGs:',pages)
if __name__=='__main__':build()
