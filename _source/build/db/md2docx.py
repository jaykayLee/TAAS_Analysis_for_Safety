# -*- coding: utf-8 -*-
"""md → Word(읽기용). pandoc(build/pdf/reference.docx 스타일) 변환 후 python-docx로 표·글꼴·용지를 다듬는다.
md가 원문이고 Word는 같은 내용의 열람판이다(수정은 md의 원천 → 재생성). 사용: python build/db/md2docx.py <in.md> <out.docx>"""
import sys, os, subprocess, re
from docx import Document
from docx.shared import Pt, RGBColor, Mm
from docx.enum.section import WD_ORIENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); import paths as PA
src, dst = sys.argv[1], sys.argv[2]
src = src if os.path.isabs(src) else os.path.join(PA.ROOT, src); dst = dst if os.path.isabs(dst) else PA.out(dst)
txt = open(src, encoding="utf-8").read()
txt = re.sub(r"<!--.*?-->", "", txt, flags=re.S)
tmp = os.path.join(PA.WORK, "_md2docx.md"); open(tmp, "w", encoding="utf-8").write(txt)
subprocess.run(["pandoc", tmp, "-f", "gfm", "-t", "docx", "--reference-doc", os.path.join(PA.BUILD, "pdf", "reference.docx"), "-o", dst], check=True)
d = Document(dst)
FONT = "Malgun Gothic"; NAVY = "1F3864"
def setfont(run, size=None, color=None, bold=None):
    run.font.name = FONT; rpr = run._element.get_or_add_rPr(); rf = rpr.find(qn("w:rFonts"))
    if rf is None: rf = OxmlElement("w:rFonts"); rpr.append(rf)
    for k in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"): rf.set(qn(k), FONT)
    if size: run.font.size = Pt(size)
    if color: run.font.color.rgb = RGBColor.from_string(color)
    if bold is not None: run.font.bold = bold
for st in d.styles:
    try:
        if st.font is not None:
            st.font.name = FONT; rpr = st.element.get_or_add_rPr(); rf = rpr.find(qn("w:rFonts"))
            if rf is None: rf = OxmlElement("w:rFonts"); rpr.append(rf)
            for k in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"): rf.set(qn(k), FONT)
    except Exception: pass
for lvl, (sz, col) in {1: (17, NAVY), 2: (13, NAVY), 3: (11, "2E5496")}.items():
    try: s = d.styles[f"Heading {lvl}"]; s.font.size = Pt(sz); s.font.color.rgb = RGBColor.from_string(col); s.font.bold = True
    except KeyError: pass
try: d.styles["Normal"].font.size = Pt(10)
except KeyError: pass
maxcols = max([len(t.columns) for t in d.tables] or [0])
for sec in d.sections:
    sec.page_width, sec.page_height = (Mm(297), Mm(210)) if maxcols > 8 else (Mm(210), Mm(297))
    sec.orientation = WD_ORIENT.LANDSCAPE if maxcols > 8 else WD_ORIENT.PORTRAIT
    for m in ("left_margin", "right_margin"): setattr(sec, m, Mm(14))
    sec.top_margin = sec.bottom_margin = Mm(15)
def border(tbl):
    tblPr = tbl._tbl.tblPr; b = OxmlElement("w:tblBorders")
    for e in ("top", "left", "bottom", "right", "insideH", "insideV"):
        x = OxmlElement(f"w:{e}"); x.set(qn("w:val"), "single"); x.set(qn("w:sz"), "4"); x.set(qn("w:color"), "C9D3E3"); b.append(x)
    tblPr.append(b)
    w = OxmlElement("w:tblW"); w.set(qn("w:w"), "5000"); w.set(qn("w:type"), "pct"); old = tblPr.find(qn("w:tblW"))
    if old is not None: tblPr.remove(old)
    tblPr.append(w)
def shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr(); s = OxmlElement("w:shd"); s.set(qn("w:val"), "clear"); s.set(qn("w:color"), "auto"); s.set(qn("w:fill"), fill); tcPr.append(s)
for t in d.tables:
    border(t); n = len(t.columns); size = 9 if n <= 5 else (8 if n <= 9 else 7)
    for i, row in enumerate(t.rows):
        if i == 0:
            trPr = row._tr.get_or_add_trPr(); h = OxmlElement("w:tblHeader"); h.set(qn("w:val"), "true"); trPr.append(h)
        for c in row.cells:
            if i == 0: shade(c, NAVY)
            elif i % 2 == 0: shade(c, "F2F4F7")
            for p in c.paragraphs:
                p.paragraph_format.space_after = Pt(1); p.paragraph_format.space_before = Pt(1)
                for r in p.runs: setfont(r, size, "FFFFFF" if i == 0 else None, True if i == 0 else None)
for p in d.paragraphs:
    for r in p.runs: setfont(r)
d.core_properties.title = os.path.splitext(os.path.basename(dst))[0]; d.core_properties.author = "J.K. Lee"
d.save(dst); print("saved", PA.rel(dst), f"(표 {len(d.tables)}개, {'가로' if maxcols > 8 else '세로'})")
