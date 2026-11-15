"""
TAAS(OBIP25 / Octagon BI) 응답 파서와 조회 파라미터 도구 — 외부 패키지 없이 표준 라이브러리만 사용.

OctagonProxyServlet 응답(XML)에는 표가 HTML 조각으로 들어 있다.
  LABELSESSION  행 머리글 이름(시도, 시군구, 구분 …)
  COLSESSION    열 머리글(여러 단, colspan)
  ROWSESSION    행 머리글(여러 단, rowspan, 숨김 칸 style='display:none')
  DATASESSION   값
  PAGE/TOTALPAGE, CURRENTPAGE, DATAINFO/ROWCOUNT …
브라우저 수집기(runner_v9.js)와 똑같은 규칙으로 행렬을 펼친다.
"""
from __future__ import annotations

import html
import re
from html.parser import HTMLParser

TRANSIENT = re.compile(r"cube가 존재하지|Exception|Connection reset|timed out|timeout|DB오류|DB접속", re.I)


# ---------------------------------------------------------------- XML 조각 꺼내기
def tag(xml: str, name: str) -> str:
    """<NAME ...>내용</NAME> 의 내용 (CDATA 벗김). 없으면 ''."""
    m = re.search(rf"<{name}\b[^>]*>(.*?)</{name}>", xml, re.S)
    if not m:
        return ""
    s = m.group(1).strip()
    parts = re.findall(r"<!\[CDATA\[(.*?)\]\]>", s, re.S)
    return "".join(parts) if parts else html.unescape(s)


def page_info(xml: str) -> dict:
    num = lambda n: int(tag(xml, n) or 0)
    return {"total": num("TOTALPAGE"), "current": num("CURRENTPAGE"), "x": num("TOTALPAGEX"), "y": num("TOTALPAGEY"),
            "rowcount": num("ROWCOUNT"), "colcount": num("COLCOUNT"), "message": tag(xml, "MESSAGE").strip()}


# ---------------------------------------------------------------- HTML 표 → 칸 목록
class _Table(HTMLParser):
    """첫 번째 <table> 의 행/칸을 (속성, 텍스트) 로 모은다. <br> 은 줄바꿈."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows, self._row, self._cell, self._depth, self._done = [], None, None, 0, False

    def handle_starttag(self, t, attrs):
        if self._done:
            return
        t = t.lower()
        if t == "table":
            self._depth += 1
        elif t == "tr" and self._depth == 1:
            self._row = []
            self.rows.append(self._row)
        elif t in ("td", "th") and self._depth == 1 and self._row is not None:
            self._cell = [{k.lower(): (v or "") for k, v in attrs}, []]
            self._row.append(self._cell)
        elif t == "br" and self._cell is not None:
            self._cell[1].append("\n")

    def handle_startendtag(self, t, attrs):
        if t.lower() == "br" and self._cell is not None:
            self._cell[1].append("\n")
        else:
            self.handle_starttag(t, attrs)

    def handle_endtag(self, t):
        t = t.lower()
        if t == "table":
            self._depth -= 1
            if self._depth == 0:
                self._done = True
        elif t in ("td", "th"):
            self._cell = None

    def handle_data(self, d):
        if self._cell is not None and not self._done:
            self._cell[1].append(d)


def cell_text(parts) -> str:
    s = "".join(parts)
    s = re.sub(r"[ \t\r ]+", " ", s)
    s = re.sub(r" *\n *", "\n", s)
    return s.strip()


def table_cells(fragment: str):
    p = _Table()
    p.feed(fragment or "")
    p.close()
    return p.rows


def hidden(attrs) -> bool:
    return "display:none" in re.sub(r"\s", "", attrs.get("style", "")).lower()


def expand(fragment: str):
    """rowspan/colspan 펼친 행렬 (숨김 칸 제외)."""
    M: list[list] = []
    for ri, tr in enumerate(table_cells(fragment)):
        while len(M) <= ri:
            M.append([])
        ci = 0
        for attrs, parts in tr:
            if hidden(attrs):
                continue
            row = M[ri]
            while ci < len(row) and row[ci] is not None:
                ci += 1
            rs = int(attrs.get("rowspan") or 1) or 1
            cs = int(attrs.get("colspan") or 1) or 1
            v = cell_text(parts)
            for a in range(rs):
                while len(M) <= ri + a:
                    M.append([])
                r = M[ri + a]
                for b in range(cs):
                    while len(r) <= ci + b:
                        r.append(None)
                    r[ci + b] = v
            ci += cs
    return [[("" if v is None else v) for v in r] for r in M]


def parse(xml: str) -> dict:
    lab = (expand(tag(xml, "LABELSESSION")) or [[]])[0]
    R = expand(tag(xml, "ROWSESSION"))
    C = expand(tag(xml, "COLSESSION"))
    D = [[cell_text(p) for _, p in tr] for tr in table_cells(tag(xml, "DATASESSION"))]
    nc = max([len(r) for r in C] or [0])
    cols = [[(r[j] if j < len(r) else "") for r in C] for j in range(nc)]
    mea = [cell_text(p) for tr in table_cells(tag(xml, "ROWSESSION")) for a, p in tr if "rowMeaTitle" in a.get("class", "")]
    mea += [cell_text(p) for tr in table_cells(tag(xml, "COLSESSION")) for a, p in tr
            if "colMeaTitle" in a.get("class", "") or a.get("type") == "16"]
    return {"lab": lab, "rows": R, "cols": cols, "data": D, "meaT": mea}


def merge_page(p: dict, q: dict) -> dict:
    """다음 페이지를 붙임. 열 구성이 다르면(열 블록 페이지 등) 열 머리글 기준으로 맞춤, 빈 칸은 ''."""
    key = lambda c: "\u0001".join(c)
    if len(q["cols"]) == len(p["cols"]) and all(key(a) == key(b) for a, b in zip(q["cols"], p["cols"])):
        p["rows"] += q["rows"]
        p["data"] += q["data"]
        return p
    idx = {key(c): i for i, c in enumerate(p["cols"])}
    for c in q["cols"]:
        if key(c) not in idx:
            idx[key(c)] = len(p["cols"])
            p["cols"].append(c)
            for r in p["data"]:
                r.append("")
    n = len(p["cols"])
    pos = [idx[key(c)] for c in q["cols"]]
    for r, d in zip(q["rows"], q["data"]):
        row = [""] * n
        for j, v in enumerate(d):
            row[pos[j]] = v
        p["rows"].append(r)
        p["data"].append(row)
    p["colRealigned"] = p.get("colRealigned", 0) + 1
    return p


# ---------------------------------------------------------------- 조회 파라미터
def list_ids(param: str, name: str) -> list[str]:
    m = re.search(rf':{name}="([^"]*)"', param)
    return [x for x in (m.group(1).split(":") if m else []) if x]


def all_on(param: str) -> str:
    """꺼진 항목 표시(*)를 지워 행·열 축과 수치항목을 모두 켬."""
    def fix(m):
        return f':{m.group(1)}="' + m.group(2).replace("*", "") + '"'
    return re.sub(r':(row_list|col_list|mea_list)="([^"]*)"', fix, param)


def set_off(param: str, item_id: str) -> str:
    """한 항목만 끔 (예비 경로: 그 항목 때문에 서버 오류가 날 때)."""
    def fix(m):
        ids = [("*" + x.lstrip("*")) if x.lstrip("*") == item_id else x for x in m.group(2).split(":")]
        return f':{m.group(1)}="' + ":".join(ids) + '"'
    return re.sub(r':(row_list|col_list|mea_list)="([^"]*)"', fix, param)


def set_range(param: str, vc: str) -> str | None:
    """vc 'D1443=202501~202512;' → :vcondition 안 같은 차원의 [from] [to] 교체. vc 가 없으면 그대로."""
    if not vc:
        return param
    m = re.fullmatch(r"D(\d+)=(\d+)~(\d+);", vc)
    if not m:
        return None
    rx = re.compile(rf'(D{m.group(1)}@\|@[^#"]*#OTE!\[)[^\]]*(\]!# #OTE!\[)[^\]]*(\]!#)')
    if not rx.search(param):
        return None
    return rx.sub(lambda z: f"{z.group(1)}{m.group(2)}{z.group(2)}{m.group(3)}{z.group(3)}", param, count=1)


def set_page(param: str, n: int) -> str:
    return re.sub(r':pagenum="\d+"', f':pagenum="{n}"', param)
