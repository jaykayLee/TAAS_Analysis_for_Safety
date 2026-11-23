# -*- coding: utf-8 -*-
"""Excel 공용 서식(머리글·셀·표) — 읽기용 워크북 생성기들이 함께 쓴다."""
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
FONT = "Malgun Gothic"; NAVY = "1F3864"; GREY = "F2F4F7"
thin = Side(style="thin", color="D4DAE2"); BOX = Border(left=thin, right=thin, top=thin, bottom=thin)
def title(ws, text, sub, span):
    ws["A1"] = text; ws["A1"].font = Font(name=FONT, bold=True, size=13, color=NAVY); ws.merge_cells(f"A1:{get_column_letter(span)}1")
    ws["A2"] = sub; ws["A2"].font = Font(name=FONT, size=9, italic=True, color="5A6678"); ws.merge_cells(f"A2:{get_column_letter(span)}2")
def table(ws, head, rows, widths, r0=4, center=(), height=None, wrap=True):
    for i, h in enumerate(head, 1):
        c = ws.cell(row=r0, column=i, value=h); c.font = Font(name=FONT, bold=True, color="FFFFFF", size=10)
        c.fill = PatternFill("solid", fgColor=NAVY); c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True); c.border = BOX
    r = r0 + 1
    for row in rows:
        for i, v in enumerate(row, 1):
            c = ws.cell(row=r, column=i, value=v); c.font = Font(name=FONT, size=9); c.border = BOX
            c.alignment = Alignment(horizontal="center" if i in center else "left", vertical="top", wrap_text=wrap)
            if (r - r0) % 2 == 0: c.fill = PatternFill("solid", fgColor=GREY)
        if height: ws.row_dimensions[r].height = height
        r += 1
    for i, w in enumerate(widths, 1): ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = ws.cell(row=r0 + 1, column=1); ws.auto_filter.ref = f"A{r0}:{get_column_letter(len(head))}{max(r - 1, r0)}"
    return r
def finish(wb):
    for w in wb.worksheets:
        w.sheet_view.zoomScale = 90; w.page_setup.orientation = "landscape"; w.page_setup.paperSize = w.PAPERSIZE_A4
        w.sheet_properties.pageSetUpPr.fitToPage = True; w.page_setup.fitToWidth = 1; w.page_setup.fitToHeight = 0
