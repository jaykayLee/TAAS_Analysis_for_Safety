"""
라이브러리(parquet) → 특정 연도 엑셀 (장표별 시트 + 목차)
usage: python build_excel.py <library_dir> <year> <out.xlsx>
"""
import json, sys
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.cell import WriteOnlyCell
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

FONT = "맑은 고딕"
F_BASE = Font(name=FONT, size=10)
F_BOLD = Font(name=FONT, size=10, bold=True)
F_TITLE = Font(name=FONT, size=13, bold=True)
F_NOTE = Font(name=FONT, size=9, color="555555")
F_LINK = Font(name=FONT, size=10, color="1D5FAE", underline="single")
FILL_HEAD = PatternFill("solid", fgColor="E3EDF9")
FILL_ROWH = PatternFill("solid", fgColor="F4F6F8")
FILL_TOT = PatternFill("solid", fgColor="FFF6D6")
THIN = Side(style="thin", color="C9D1DA")
B_ALL = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
TOTALS = {"합계", "계", "전국", "전체", "소계"}
MAX_DIMS = 8


def ordered_unique(s):
    return list(dict.fromkeys(s))


def cell(ws, v, font=F_BASE, fill=None, fmt=None, align=None, border=B_ALL):
    c = WriteOnlyCell(ws, value=v)
    c.font = font
    if fill: c.fill = fill
    if fmt: c.number_format = fmt
    if align: c.alignment = align
    if border: c.border = border
    return c


def sheet_name(i, name, used):
    base = f"{i:03d}_" + "".join(ch for ch in name if ch not in '[]:*?/\\')
    base = base[:31]
    n, k = base, 2
    while n in used:
        suf = f"~{k}"; n = base[:31 - len(suf)] + suf; k += 1
    used.add(n)
    return n


def build(lib, year, out, edition=None):
    lib = Path(lib)
    facts = pd.read_parquet(lib / "parquet" / "facts.parquet")
    pats = pd.read_parquet(lib / "parquet" / "patterns.parquet")
    fy = facts[facts.year == year]
    wb = Workbook(write_only=True)
    toc = wb.create_sheet("목차")
    toc.column_dimensions["A"].width = 6
    for col, w in zip("BCDEFGH", (20, 46, 36, 14, 10, 50, 18)):
        toc.column_dimensions[col].width = w
    toc_rows, used = [], {"목차"}
    order = pats.sort_values(["root", "path"], key=lambda s: s if s.name != "root" else s.map({"교통여건": 0}).fillna(1))
    i = 0
    for _, p in order.iterrows():
        g = fy[fy.pid == p.pid]
        if g.empty:
            toc_rows.append((None, p, "2025년 값 없음", 0)); continue
        i += 1
        sn = sheet_name(i, p["name"], used)
        dn = json.loads(p.dim_names); rl = json.loads(p.row_levels)
        n_row = len(rl) - (1 if p.year_axis == "row" else 0) - (1 if p.has_measure else 0)
        rdims = [f"d{k+1}" for k in range(n_row)]
        cdims = [f"d{k+1}" for k in range(n_row, len(dn))]
        rnames = dn[:n_row] + (["구분"] if p.has_measure else [])
        cnames = dn[n_row:]
        g = g.copy(); g["measure"] = g.measure.fillna("값")
        rkeys = rdims + (["measure"] if p.has_measure else [])
        if not rkeys:
            g["_r"] = str(year); rkeys = ["_r"]; rnames = ["연도"]
        if not cdims:
            g["_c"] = str(year); cdims = ["_c"]; cnames = ["연도"]
        # 원래 출현 순서 유지
        rorder = ordered_unique(map(tuple, g[rkeys].fillna("").values))
        corder = ordered_unique(map(tuple, g[cdims].fillna("").values))
        val = {(tuple(r), tuple(c)): v for r, c, v in zip(g[rkeys].fillna("").values, g[cdims].fillna("").values, g.value)}

        ws = wb.create_sheet(sn)
        nrh = len(rkeys)
        for k in range(nrh):
            ws.column_dimensions[get_column_letter(k + 1)].width = 16 if k < nrh - 1 else 18
        for k in range(len(corder)):
            ws.column_dimensions[get_column_letter(nrh + k + 1)].width = 13
        ws.freeze_panes = f"{get_column_letter(nrh+1)}{4+len(cnames)+1}"
        ws.append([cell(ws, f"{p['name']} ({year}년)", F_TITLE, border=None)])
        ws.append([cell(ws, p.path, F_NOTE, border=None)])
        note = p.notes or ""
        ws.append([cell(ws, ("주석: " + note + "  |  " if note else "") + "출처: 한국도로교통공단 TAAS 교통사고분석시스템 (수치항목 6종 모두 활성화 기준)", F_NOTE, border=None)])
        ws.append([])
        # 열 머리글 (여러 단)
        for lvl, nm in enumerate(cnames):
            last = lvl == len(cnames) - 1
            # 마지막 머리글 줄: 행 축 이름 / 그 위 줄: 오른쪽 끝에 열 축 이름
            row = [cell(ws, rnames[k] if last else (f"{nm} ▶" if k == nrh - 1 else None), F_BOLD, FILL_HEAD,
                        align=Alignment(horizontal="center" if last else "right", vertical="center")) for k in range(nrh)]
            if last:
                row[nrh - 1] = cell(ws, f"{rnames[-1]}  /  {nm} ▶", F_BOLD, FILL_HEAD, align=Alignment(horizontal="center"))
            for c in corder:
                v = c[lvl]
                row.append(cell(ws, v, F_BOLD, FILL_TOT if v in TOTALS else FILL_HEAD,
                                align=Alignment(horizontal="center", vertical="center", wrap_text=True)))
            ws.append(row)
        # 본문
        for r in rorder:
            is_tot = any(x in TOTALS for x in r[:-1]) if p.has_measure else any(x in TOTALS for x in r)
            row = [cell(ws, x, F_BOLD if is_tot else F_BASE, FILL_TOT if is_tot else FILL_ROWH) for x in r]
            for c in corder:
                v = val.get((r, c))
                fmt = "#,##0" if v is None or float(v).is_integer() else "#,##0.0##"
                row.append(cell(ws, None if v is None else (int(v) if float(v).is_integer() else float(v)),
                                F_BOLD if is_tot else F_BASE, FILL_TOT if is_tot else None, fmt))
            ws.append(row)
        toc_rows.append((sn, p, None, len(rorder) * len(corder)))

    toc.append([cell(toc, f"TAAS 교통사고 상세통계 {year}년 — 목차", F_TITLE, border=None)])
    toc.append([cell(toc, "모든 장표는 수치항목 6종(사고건수·사망자수·부상자수·중상자수·경상자수·부상신고자수)을 모두 켠 상태로 수집했습니다. 조건설정(시도·도로종류 등) 필터는 적용하지 않은 전체 값입니다.", F_NOTE, border=None)])
    if edition:
        toc.append([cell(toc, edition, Font(name=FONT, size=10, bold=True, color="B45309"), border=None)])
    toc.append([])
    hdr = ["No", "분류", "장표명", "시트", "셀 수", "연도축", "주석", "원본"]
    toc.append([cell(toc, h, F_BOLD, FILL_HEAD, align=Alignment(horizontal="center")) for h in hdr])
    k = 0
    for sn, p, miss, ncell in toc_rows:
        k += 1
        parts = p.path.split(" > ")
        cat = " › ".join(parts[:-1][:2])
        sh = cell(toc, sn or miss, F_LINK if sn else F_NOTE)
        if sn:
            sh.hyperlink = f"#'{sn}'!A1"
        src = cell(toc, "TAAS", F_LINK); src.hyperlink = p.source_url
        toc.append([cell(toc, k), cell(toc, cat), cell(toc, p["name"]), sh, cell(toc, ncell, fmt="#,##0"),
                    cell(toc, {"row": "행", "col": "열"}.get(p.year_axis, "-")), cell(toc, p.notes or "", F_NOTE), src])
    toc.freeze_panes = "A6" if edition else "A5"
    wb.save(out)
    return {"sheets": i, "toc_rows": len(toc_rows)}


if __name__ == "__main__":
    print(build(sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None))
