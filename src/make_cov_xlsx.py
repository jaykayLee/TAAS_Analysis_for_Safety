import json, duckdb
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

import sys
LIB = sys.argv[1] if len(sys.argv) > 1 else str(__import__("pathlib").Path(__file__).resolve().parents[1] / "library")
OUT = sys.argv[2] if len(sys.argv) > 2 else "TAAS_수집현황.xlsx"
FN = "맑은 고딕"
F = Font(name=FN, size=10); FB = Font(name=FN, size=10, bold=True)
FT = Font(name=FN, size=15, bold=True, color="0B2545"); FS = Font(name=FN, size=9, color="5A6472")
FH = Font(name=FN, size=10, bold=True, color="FFFFFF"); FL = Font(name=FN, size=10, color="1D5FAE", underline="single")
HEAD = PatternFill("solid", fgColor="0B2545"); BAND = PatternFill("solid", fgColor="F3F6FA")
OK = PatternFill("solid", fgColor="E6F4EA"); WARN = PatternFill("solid", fgColor="FFF4D6"); BAD = PatternFill("solid", fgColor="FDE7E7")
TH = Side(style="thin", color="D5DBE3"); BOX = Border(left=TH, right=TH, top=TH, bottom=TH)
C = Alignment(horizontal="center", vertical="center"); L = Alignment(horizontal="left", vertical="center", wrap_text=True)

idx = json.load(open(f"{LIB}/index.json")); cov = json.load(open(f"{LIB}/coverage.json"))
P = {str(p["pid"]): p for p in idx["patterns"]}
con = duckdb.connect(); FQ = f"'{LIB}/parquet/facts.parquet'"
TOT = "('합계','계','전국','전체','소계')"
cond = " AND ".join(f"(d{i} IS NULL OR d{i} IN {TOT})" for i in range(1, 9))
nat = {y: (v, n) for y, v, n in con.execute(f"""with t as (select year, value, count(distinct pid) n from {FQ}
  where measure='사고[건]' and {cond} and value is not null group by 1,2)
  select year, arg_max(value,n), max(n) from t group by 1""").fetchall()}
k = "pid,year," + ",".join(f"coalesce(d{i},'')" for i in range(1, 9))
ident = {y: (n, b) for y, n, b in con.execute(f"""with w as (select pid, year, {",".join(f"coalesce(d{i},'') d{i}" for i in range(1,9))},
  max(case when measure='부상[명]' then value end) b, max(case when measure='중상자[명]' then value end) s,
  max(case when measure='경상자[명]' then value end) l, max(case when measure='부상신고자[명]' then value end) r
  from {FQ} group by all)
  select year, count(*), sum(case when abs(b-(s+l+r))>0.5 then 1 else 0 end) from w
  where b is not null and s is not null and l is not null and r is not null group by 1""").fetchall()}
cells = dict(con.execute(f"select year, count(*) from {FQ} group by 1").fetchall())
pats_y = dict(con.execute(f"select year, count(distinct pid) from {FQ} group by 1").fetchall())

wb = Workbook()

def header(ws, row, names, widths):
    for j, (n, w) in enumerate(zip(names, widths), 1):
        c = ws.cell(row=row, column=j, value=n); c.font = FH; c.fill = HEAD; c.alignment = C; c.border = BOX
        ws.column_dimensions[get_column_letter(j)].width = w

# ---------- 장표별 현황
ws = wb.active; ws.title = "장표별 현황"
cols = ["장표번호", "대분류", "중분류", "장표명", "값 시작연도", "값 끝연도", "셀 수", "수집 구간 수", "빈 구간 수", "빈 구간", "일부 항목 누락", "축 미적용", "패널 제한", "상태", "주석", "TAAS"]
ws["A1"] = "장표별 수집 현황"; ws["A1"].font = FT
ws["A2"] = "TAAS 교통사고 상세통계 338개 장표 · 모든 행·열 축과 수치항목 6종을 켠 상태로 2005~2025년 수집 · 빈 구간 = TAAS 서버가 빈 표/오류를 돌려준 구간"; ws["A2"].font = FS
header(ws, 4, cols, [9, 16, 30, 40, 10, 10, 12, 10, 9, 30, 22, 14, 10, 12, 50, 8])
r = 5
for pid in sorted(P, key=int):
    p = P[pid]; c = cov.get(pid, {}); ch = c.get("chunks", {})
    empt = [k for k, v in ch.items() if v["status"] == "empty"]
    part = [f"{k}: {', '.join(v.get('missing', []))}" for k, v in ch.items() if v["status"] == "partial_measures"]
    dmis = [f"{k}: {', '.join(v.get('dim_missing', []))}" for k, v in ch.items() if v.get("dim_missing")]
    path = p["path"].split(" > ")
    notes = p["notes"] or ""
    vals = [int(pid), path[0], " › ".join(path[1:-1]), p["name"], p["year_min"], p["year_max"], p["n_facts"], len(ch), None,
            ", ".join(empt), "; ".join(part), "; ".join(dmis), "예" if p.get("panel_partial") else "", None, notes, "열기"]
    for j, v in enumerate(vals, 1):
        x = ws.cell(row=r, column=j, value=v); x.font = F; x.border = BOX
        x.alignment = C if j in (1, 5, 6, 8, 9, 13, 14, 16) else L
    ws.cell(row=r, column=7).number_format = "#,##0"; ws.cell(row=r, column=7).alignment = Alignment(horizontal="right", vertical="center")
    ws.cell(row=r, column=9, value=f'=IF(J{r}="",0,LEN(J{r})-LEN(SUBSTITUTE(J{r},",",""))+1)')
    ws.cell(row=r, column=14, value=f'=IF(G{r}=0,"값 없음",IF(OR(I{r}>0,K{r}<>"",L{r}<>""),"일부 빔","완전"))')
    ws.cell(row=r, column=16).hyperlink = p["source_url"]; ws.cell(row=r, column=16).font = FL
    r += 1
last = r - 1
tab = Table(displayName="장표현황", ref=f"A4:{get_column_letter(len(cols))}{last}")
tab.tableStyleInfo = TableStyleInfo(name="TableStyleLight1", showRowStripes=True)
ws.add_table(tab); ws.freeze_panes = "E5"
from openpyxl.formatting.rule import FormulaRule
ws.conditional_formatting.add(f"N5:N{last}", FormulaRule(formula=[f'N5="완전"'], fill=OK))
ws.conditional_formatting.add(f"N5:N{last}", FormulaRule(formula=[f'N5="일부 빔"'], fill=WARN))
ws.conditional_formatting.add(f"N5:N{last}", FormulaRule(formula=[f'N5="값 없음"'], fill=BAD))

# ---------- 빈 구간 상세
we = wb.create_sheet("빈 구간 상세")
we["A1"] = "값이 없는 구간"; we["A1"].font = FT
we["A2"] = "TAAS 서버가 '-' 만 있는 빈 표, 또는 '조회된 데이터가 없습니다'(SQL오류 등)를 돌려준 구간. 과속(2021~), 마약·약물(2024~)처럼 통계가 나중에 생긴 경우가 대부분"; we["A2"].font = FS
header(we, 4, ["장표번호", "장표명", "구간", "구분", "서버 메시지/내용"], [9, 46, 12, 16, 60])
r = 5
for pid in sorted(cov, key=int):
    for kk, v in cov[pid].get("chunks", {}).items():
        if v["status"] in ("empty", "partial_measures") or v.get("dim_missing"):
            kind = "빈 표" if v["status"] == "empty" else ("수치항목 일부 누락" if v["status"] == "partial_measures" else "축 미적용")
            msg = v.get("msg") or ", ".join(v.get("missing", []) or v.get("dim_missing", []))
            for j, x in enumerate([int(pid), P[pid]["name"], kk, kind, msg or "(빈 표: 모든 칸 '-')"], 1):
                c = we.cell(row=r, column=j, value=x); c.font = F; c.border = BOX; c.alignment = C if j in (1, 3) else L
            r += 1
t2 = Table(displayName="빈구간", ref=f"A4:E{r-1}"); t2.tableStyleInfo = TableStyleInfo(name="TableStyleLight1", showRowStripes=True)
we.add_table(t2); we.freeze_panes = "A5"

# ---------- 연도별 검증
wv = wb.create_sheet("연도별 검증")
wv["A1"] = "연도별 검증"; wv["A1"].font = FT
wv["A2"] = "전국 사고건수: 모든 축이 합계인 칸의 '사고[건]' 중 가장 많은 장표가 공통으로 낸 값 · 부상 항등식: 부상자 = 중상자 + 경상자 + 부상신고자"; wv["A2"].font = FS
header(wv, 4, ["연도", "값이 있는 장표 수", "셀 수", "전국 사고건수", "같은 값을 낸 장표 수", "항등식 검사 칸 수", "항등식 불일치", "판정"], [8, 16, 14, 15, 18, 17, 14, 10])
r = 5
for y in sorted(cells):
    if y is None: continue
    v, n = nat.get(y, (None, None)); a, b = ident.get(y, (0, 0))
    row = [str(int(y)), pats_y[y], cells[y], v, n, a, b, None]
    for j, x in enumerate(row, 1):
        c = wv.cell(row=r, column=j, value=x); c.font = F; c.border = BOX; c.alignment = C
        if j in (2, 3, 4, 5, 6, 7): c.number_format = "#,##0"
    wv.cell(row=r, column=8, value=f'=IF(G{r}=0,"통과","확인")')
    r += 1
lv = r - 1
for j, f in [(2, None), (3, f"=SUM(C5:C{lv})"), (6, f"=SUM(F5:F{lv})"), (7, f"=SUM(G5:G{lv})")]:
    if f:
        c = wv.cell(row=r, column=j, value=f); c.font = FB; c.number_format = "#,##0"; c.border = BOX; c.alignment = C
wv.cell(row=r, column=1, value="합계").font = FB
wv.conditional_formatting.add(f"H5:H{lv}", FormulaRule(formula=['H5="통과"'], fill=OK))
wv.freeze_panes = "A5"

# ---------- 요약 (맨 앞)
s = wb.create_sheet("요약", 0)
s.column_dimensions["A"].width = 30; s.column_dimensions["B"].width = 22; s.column_dimensions["C"].width = 60
s["A1"] = "TAAS 교통사고 상세통계 라이브러리 — 수집 현황 (2005~2025)"; s["A1"].font = FT
s["A2"] = f"생성 {idx['built_at']} · 출처 한국도로교통공단 TAAS 교통사고분석시스템 > 교통사고 상세통계"; s["A2"].font = FS
rows = [
    ("장표 수", "=COUNTA('장표별 현황'!A5:A{0})".format(last), "TAAS 상세통계 메뉴의 전체 장표"),
    ("값이 있는 장표", "=COUNTIF('장표별 현황'!G5:G{0},\">0\")".format(last), ""),
    ("완전 수집 장표", "=COUNTIF('장표별 현황'!N5:N{0},\"완전\")".format(last), "모든 구간에 값이 있음"),
    ("일부 구간이 빈 장표", "=COUNTIF('장표별 현황'!N5:N{0},\"일부 빔\")".format(last), "대부분 통계가 나중에 생긴 경우 ('빈 구간 상세' 참고)"),
    ("값이 전혀 없는 장표", "=COUNTIF('장표별 현황'!N5:N{0},\"값 없음\")".format(last), "7079, 7165 — 서버 SQL 오류"),
    ("전체 셀(값) 수", "=SUM('장표별 현황'!G5:G{0})".format(last), "장표 1칸 = 1행 (Parquet facts)"),
    ("수집 구간(작업) 수", "=SUM('장표별 현황'!H5:H{0})".format(last), "비회원 조회 한도에 맞춰 5년(일별 장표는 1년) 단위"),
    ("빈 구간 수", "=SUM('장표별 현황'!I5:I{0})".format(last), ""),
    ("부상 항등식 불일치 칸", f"='연도별 검증'!G{lv+1}", "부상자 = 중상자 + 경상자 + 부상신고자, 전 연도"),
    ("패널 제한 장표", "=COUNTIF('장표별 현황'!M5:M{0},\"예\")".format(last), "7120 시도 시군구별·일별 — 패널엔 2024~2025만, 전체는 Parquet"),
]
header(s, 4, ["항목", "값", "설명"], [30, 22, 60])
for i, (a, b, c) in enumerate(rows, 5):
    for j, x in enumerate((a, b, c), 1):
        cc = s.cell(row=i, column=j, value=x); cc.font = FB if j == 1 else F; cc.border = BOX
        cc.alignment = L if j != 2 else Alignment(horizontal="right", vertical="center")
    s.cell(row=i, column=2).number_format = "#,##0"
n = 5 + len(rows) + 1
notes = ["수집 방식: 장표마다 행·열 축과 수치항목 6종(사고·사망·부상·중상·경상·부상신고)을 모두 켠 상태로 조회 (v8 클릭 방식과 v9 직접 조회 결과가 칸 단위로 일치함을 확인)",
         "이름이 같은 다른 행(2008~2014 '창원시' 통합 전·후 등)은 ' (2)'를 붙여 둘 다 보존",
         "7020 사고유형별·월별 2025: 경상자수만 서버 오류로 제외",
         "시트: 장표별 현황(필터·정렬 가능) / 빈 구간 상세 / 연도별 검증"]
s.cell(row=n, column=1, value="참고").font = FB
for i, t in enumerate(notes, n + 1):
    c = s.cell(row=i, column=1, value="• " + t); c.font = F
s.sheet_view.showGridLines = False
for w in (ws, we, wv): w.sheet_view.zoomScale = 90
wb.save(OUT); print(OUT, last - 4, "patterns")
