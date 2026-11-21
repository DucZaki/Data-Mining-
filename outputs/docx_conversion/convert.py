from pathlib import Path
import re, subprocess
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
root=Path.cwd(); src=root/'docs/giai_thich_do_an_va_bao_ve.md'
doc=Document(); sec=doc.sections[0]; sec.page_width=Cm(21); sec.page_height=Cm(29.7)
sec.top_margin=sec.bottom_margin=Cm(2); sec.left_margin=sec.right_margin=Cm(2)
for name in ['Normal','Title','Heading 1','Heading 2','Heading 3']:
 s=doc.styles[name]; s.font.name='Arial'; s.font.color.rgb=RGBColor(0,0,0)
doc.styles['Normal'].font.size=Pt(10)
doc.styles['Normal'].paragraph_format.space_after=Pt(6)
def inline(p,text):
 text=re.sub(r'\[([^\]]+)\]\(#[^)]+\)',r'\1',text)
 text=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',r'\1 (\2)',text)
 for chunk in re.split(r'(\*\*.*?\*\*|`[^`]+`)',text):
  r=p.add_run(chunk[2:-2] if chunk.startswith('**') else chunk[1:-1] if chunk.startswith('`') else chunk)
  if chunk.startswith('**'): r.bold=True
  if chunk.startswith('`'): r.font.name='Consolas'; r.font.size=Pt(9)
lines=src.read_text(encoding='utf-8').splitlines(); i=0; code=False
while i<len(lines):
 line=lines[i]; i+=1
 if line.startswith('```'): code=not code; continue
 if not line.strip(): continue
 if code:
  p=doc.add_paragraph(); r=p.add_run(line); r.font.name='Consolas'; r.font.size=Pt(8); continue
 if line.startswith('|'):
  rows=[line]
  while i<len(lines) and lines[i].startswith('|'): rows.append(lines[i]); i+=1
  rows=[r for r in rows if not re.match(r'^\|[\s:|\-]+$',r)]
  vals=[[c.strip() for c in r.strip('|').split('|')] for r in rows]
  t=doc.add_table(rows=0,cols=len(vals[0])); t.style='Table Grid'
  for ri,valsrow in enumerate(vals):
   cells=t.add_row().cells
   for c,v in zip(cells,valsrow):
    inline(c.paragraphs[0],v)
    for r in c.paragraphs[0].runs: r.font.size=Pt(8); r.bold=ri==0 or r.bold
    if ri==0:
     sh=OxmlElement('w:shd'); sh.set(qn('w:fill'),'E8EDF2'); c._tc.get_or_add_tcPr().append(sh)
   if ri==0:
    repeat=OxmlElement('w:tblHeader'); t.rows[ri]._tr.get_or_add_trPr().append(repeat)
  doc.add_paragraph(); continue
 m=re.match(r'!\[([^]]*)\]\(([^)]+)\)',line)
 if m:
  path=src.parent/m[2]
  if not path.exists():
   path.parent.mkdir(exist_ok=True)
   path.write_bytes(subprocess.check_output(['git','show','c4283d2:docs/'+m[2]]))
  doc.add_picture(str(path),width=Cm(16.5)); doc.add_paragraph(m[1],style='Caption'); continue
 m=re.match(r'^(#{1,4})\s+(.*)',line)
 if m:
  p=doc.add_paragraph(style='Title' if len(m[1])==1 else 'Heading '+str(len(m[1])-1)); inline(p,m[2]); continue
 m=re.match(r'^(-|\d+\.)\s+(.*)',line)
 p=doc.add_paragraph(style='List Bullet' if m and m[1]=='-' else 'List Number' if m else 'Normal'); inline(p,m[2] if m else line)
out=src.with_suffix('.docx'); doc.save(out); print(out)
