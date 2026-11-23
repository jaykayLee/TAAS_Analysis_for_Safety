"""
부처별 외부 라이브러리 원본 만들기 — 원자료(03_References/02_Statistics/files/<lib>, 연표는 04 LIB-POLICY) → 04_Libraries/<분류>/LIB-<LIB>/<lib>.json.gz (위치: _source/taas_paths.py) (TAAS 원본과 같은 형식)

    python _source/src/make_ext_raw.py                 모든 부처
    python _source/src/make_ext_raw.py mois molit      고른 부처만
    python _source/src/make_ext_raw.py --import <dump.txt>   브라우저 수집기(KC.dump) 결과 → <원자료>/kosis/<key>.csv.gz 로 나눠 저장

부처(lib)와 장표 번호
  kostat  통계청(국가데이터처)   9001·9002  인구총조사 연령별 인구 (03_References/02_Statistics/files/kostat/*.xlsx → make_pop_raw)
  mois    행정안전부             9101·9102  주민등록인구 5세별 · 연령구분별(어린이·일반·노인)
  molit   국토교통부             9201~9205  자동차 등록대수 · 이륜차 신고대수 · 도로 연장 · 평균 일교통량 · 자동차 주행거리
  police  경찰청                 9003, 9301~9308  어린이보호구역 · 운전면허 소지자(면허종별·성별·연령대별·시도별) · 면허 자진반납 · 무인단속카메라 · 음주운전 단속 · 교통법규 위반 단속
                                 (9305~9308 은 공공데이터포털 파일: 03_References/02_Statistics/files/police/datagokr)
  policy  제도 시행 연표          9901  교통안전 제도 시행(연도 더미) + events.json(패널의 개입 연도 빠른 선택·그래프 표시)

수집 자료(KOSIS) 형식: <원자료>/kosis/<key>.csv.gz — 열 PRD_DE, C1_NM…C4_NM, ITM_NM, UNIT_NM, DT
(OpenAPI 의 긴 형식과 같음. 수집기: _source/collector/browser/kosis_collect.js, 목록: _source/ops/ext_sources.json)
수집 자료가 없는 장표는 건너뜁니다(장표 목록에도 넣지 않음).
"""
import collections, csv, gzip, io, json, re, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import taas_paths as TP  # noqa: E402 — 부처별 원자료·원천 위치(표준 구조)
ROOT = TP.ROOT
CAT = json.loads(TP.EXT_SOURCES.read_text(encoding="utf-8"))
Y0, Y1 = 2005, 2025

SIDO_ORDER = ["전국", "서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종", "경기", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주"]
SIDO = {"전국": "전국", "총계": "전국", "합계": "전국", "계": "전국", "총합계": "전국",
        "서울특별시": "서울", "부산광역시": "부산", "대구광역시": "대구", "인천광역시": "인천", "광주광역시": "광주", "대전광역시": "대전",
        "울산광역시": "울산", "세종특별자치시": "세종", "경기도": "경기", "강원도": "강원", "강원특별자치도": "강원", "충청북도": "충북",
        "충청남도": "충남", "전라북도": "전북", "전북특별자치도": "전북", "전라남도": "전남", "경상북도": "경북", "경상남도": "경남",
        "제주도": "제주", "제주특별자치도": "제주", "경기남부": "경기", "경기북부": "경기"}
SIDO.update({s: s for s in SIDO_ORDER})
DROP_SIDO = re.compile(r"전남광주")  # 2026년 통합 이전 자료에는 없음(광주·전남으로 따로 있음)


def sido(n):
    n = (n or "").strip()
    if DROP_SIDO.search(n):
        return None
    return SIDO.get(n, SIDO.get(n.replace(" ", ""), None))


def num(v):
    v = (v if v is not None else "").strip().replace(",", "")
    if v in ("", "-", "X", "x", "…", "...", "nan"):
        return None
    try:
        return float(v)
    except ValueError:
        return None


def fmt(v):
    if v is None:
        return ""
    if float(v).is_integer():
        return f"{int(v):,}"
    return f"{v:,.2f}".rstrip("0").rstrip(".")


def load(lib, key):
    """수집 자료 → [{year, C1..C4(이름), item, unit, v}] (없으면 None)"""
    f = TP.ext_src(lib) / "kosis" / f"{key}.csv.gz"
    if not f.exists():
        return None
    out = []
    with gzip.open(f, "rt", encoding="utf-8") as g:
        for r in csv.DictReader(g):
            p = r.get("PRD_DE", "")
            if len(p) < 4 or not p[:4].isdigit():
                continue
            out.append({"year": int(p[:4]), "C1": r.get("C1_NM", "").strip(), "C2": r.get("C2_NM", "").strip(),
                        "C3": r.get("C3_NM", "").strip(), "C4": r.get("C4_NM", "").strip(),
                        "item": re.sub(r"<br>", " ", r.get("ITM_NM", "")).strip(), "unit": r.get("UNIT_NM", "").strip(), "v": num(r.get("DT"))})
    return out


def meta_of(lib):
    return CAT["libs"][lib]


class Table:
    """장표 하나: 축(dims) × 수치(measure) × 연도 → TAAS 원본 레코드"""

    def __init__(self, pid, name, lib, category, dims, notes=(), source_url=""):
        self.pid, self.name, self.lib, self.category, self.dims = str(pid), name, lib, category, list(dims)
        self.notes, self.source_url = list(notes), source_url
        self.cells = {}  # (dims..., measure) -> {year: value}

    def put(self, dims, measure, year, v, add=False):
        if v is None or year is None or not (Y0 <= year <= Y1):
            return
        k = tuple(dims) + (measure,)
        d = self.cells.setdefault(k, {})
        d[year] = (d.get(year) or 0) + v if add else v

    def get(self, dims, measure, year):
        return self.cells.get(tuple(dims) + (measure,), {}).get(year)

    def rec(self, order=None):
        if not self.cells:
            return None, None
        years = sorted({y for d in self.cells.values() for y in d})
        keys = list(self.cells)
        if order:
            keys.sort(key=order)
        rows = [list(k) for k in keys]
        data = [[fmt(self.cells[k].get(y)) for y in years] for k in keys]
        root = f"{meta_of(self.lib)['name']} 자료"
        rec = {"key": f"{self.pid}|all", "pid": self.pid, "label": f"{years[0]}-{years[-1]}", "vc": "", "lab": self.dims + ["구분"], "colDims": ["연도"],
               "rows": rows, "cols": [[str(y)] for y in years], "data": data, "pages": 1, "nodata": False, "meaAll": 0, "meaOn": 0, "meaMissing": [],
               "dimAll": True, "dimMissing": [], "v8": True, "ts": int(time.time() * 1000), "source": self.lib, "msg": [f"주) {n}" for n in self.notes]}
        meta = {"pid": self.pid, "subjectId": "0", "menuId": self.pid, "name": self.name, "root": root, "lib": self.lib,
                "path": [root, self.category, self.name], "trend": "N", "dateInfo": {"minYear": str(years[0]), "maxYear": str(years[-1]), "dimAttrId": 0},
                "dims": [], "source_url": self.source_url}
        return meta, rec


def sido_order(k):
    return (SIDO_ORDER.index(k[0]) if k[0] in SIDO_ORDER else 99,) + tuple(str(x) for x in k[1:])


def add_national(t, ndim_after=1, measure_filter=None):
    """시도만 있고 전국이 없는 장표 → 전국 = 시도 합 (첫 축이 시도)"""
    have = {k for k in t.cells if k[0] == "전국"}
    new = {}
    for k, d in t.cells.items():
        if k[0] == "전국" or (measure_filter and not measure_filter(k[-1])):
            continue
        nk = ("전국",) + k[1:]
        if nk in have:
            continue
        for y, v in d.items():
            new.setdefault(nk, {})[y] = new.get(nk, {}).get(y, 0) + v
    t.cells.update(new)
    return bool(new)


KOSIS_URL = "https://kosis.kr/statHtml/statHtml.do?orgId={o}&tblId={t}"


def kurl(lib, key):
    j = next((x for x in meta_of(lib)["kosis"] if x["key"] == key), None)
    return KOSIS_URL.format(o=j["orgId"], t=j["tblId"]) if j else ""


# ---------------- 행정안전부 ----------------
def age_band(a):
    """'0 - 4세' → '0~4세', '100+' → '100세이상', '85+' → '85세이상', '계' → '계'"""
    a = (a or "").replace(" ", "")
    if a in ("계", "합계", "총계"):
        return "계"
    m = re.match(r"^(\d+)-(\d+)세?$", a)
    if m:
        return f"{m.group(1)}~{m.group(2)}세"
    m = re.match(r"^(\d+)\+$|^(\d+)세이상$", a)
    if m:
        return f"{m.group(1) or m.group(2)}세이상"
    return a


BANDS = [f"{a}~{a + 4}세" for a in range(0, 85, 5)]


def lib_mois():
    out = []
    A, B = load("mois", "pop5_2005"), load("mois", "pop5_2011")
    if not (A or B):
        return out
    MEAS = {"인구": "인구[명]", "총인구수": "인구[명]", "남": "남자[명]", "남자인구수": "남자[명]", "여": "여자[명]", "여자인구수": "여자[명]"}
    raw = {}  # (year, sido, band, measure) -> v
    for r in (A or []) + (B or []):
        s = sido(r["C1"]); m = MEAS.get(r["item"])
        if not s or not m or r["v"] is None:
            continue
        raw[(r["year"], s, age_band(r["C2"]), m)] = r["v"]
    t1 = Table(9101, "주민등록인구 (5세 단위)", "mois", "인구", ["시도", "연령"],
               ["출처: 행정안전부 「주민등록인구현황」 — KOSIS 행정구역(읍면동)별/5세별 주민등록인구 (2005~2010: DT_1B04005, 2011~: DT_1B04005N), 각 연도 12월 31일 기준",
                "주민등록 인구(내국인). 2010년 10월부터 거주불명자, 2015년 1월부터 재외국민 포함 — 연도 사이 기준 차이 주의. 외국인 제외",
                "85세 이상은 한 구간(85세이상)으로 합침. 인구총조사(9001·9002, 통계청)와 기준이 달라 값이 다름"],
               KOSIS_URL.format(o="101", t="DT_1B04005N"))
    years = sorted({k[0] for k in raw}); regs = sorted({k[1] for k in raw}, key=lambda s: SIDO_ORDER.index(s) if s in SIDO_ORDER else 99)
    for y in years:
        for s in regs:
            for m in ("인구[명]", "남자[명]", "여자[명]"):
                g = lambda b: raw.get((y, s, b, m))
                tot = g("계")
                t1.put([s, "계"], m, y, tot)
                for b in BANDS:
                    t1.put([s, b], m, y, g(b))
                old = g("85세이상")
                if old is None:
                    parts = [v for (yy, ss, bb, mm), v in raw.items() if yy == y and ss == s and mm == m and re.match(r"^(8[5-9]|9\d|1\d\d)~", bb)]
                    hun = g("100세이상")
                    old = (sum(parts) + (hun or 0)) if parts else None
                t1.put([s, "85세이상"], m, y, old)
    out.append(t1.rec(lambda k: (SIDO_ORDER.index(k[0]) if k[0] in SIDO_ORDER else 99, 0 if k[1] == "계" else (BANDS + ["85세이상"]).index(k[1]) + 1, k[2])))
    # 9102 연령구분 (9001 과 같은 정의)
    G = ["전체", "어린이 0~12세", "일반 13~64세", "노인 65세 이상"]
    t2 = Table(9102, "연령구분별 주민등록인구 (어린이·일반·노인)", "mois", "인구", ["시도", "연령구분"],
               ["출처: 행정안전부 「주민등록인구현황」 (9101 과 같은 자료, 12월 31일 기준) — 2005~2025년 매년 실측",
                "어린이 = 12세 이하 ← 0~4세 + 5~9세 + 10~14세 × 3/5 (10~14세 안 균등 분포 가정, 추정) · 노인 = 65세 이상(정확) · 일반 = 전체 − 어린이 − 노인 — 9001(인구총조사)과 같은 정의",
                "인구총조사(9001)의 빈 연도(2006~2009, 2011~2014)를 보간 대신 이 실측 계열로 채울 수 있음(패널 비율 환산의 분모로 선택)"],
               KOSIS_URL.format(o="101", t="DT_1B04005N"))
    for y in years:
        for s in regs:
            for m in ("인구[명]", "남자[명]", "여자[명]"):
                g = lambda b: t1.get([s, b], m, y)
                tot = g("계")
                if tot is None:
                    continue
                b0, b5, b10 = g("0~4세"), g("5~9세"), g("10~14세")
                child = None if None in (b0, b5, b10) else b0 + b5 + b10 * 0.6
                olds = [g(b) for b in ["65~69세", "70~74세", "75~79세", "80~84세", "85세이상"]]
                old = None if None in olds else sum(olds)
                mid = None if None in (child, old) else tot - child - old
                for gname, v in zip(G, (tot, child, mid, old)):
                    t2.put([s, gname], m, y, v)
                    if m == "인구[명]" and v is not None:
                        t2.put([s, gname], "구성비[%]", y, round(v / tot * 100, 2))
    out.append(t2.rec(lambda k: (SIDO_ORDER.index(k[0]) if k[0] in SIDO_ORDER else 99, G.index(k[1]), k[2])))
    return out


# ---------------- 국토교통부 ----------------
CAR = ["계", "승용", "승합", "화물", "특수"]
USE = ["계", "관용", "자가용", "영업용"]


def lib_molit():
    out = []
    # 9201 자동차 등록대수
    A, E = load("molit", "car_sido"), load("molit", "car_e")
    if A or E:
        t = Table(9201, "자동차 등록대수 (시도·차종·용도)", "molit", "자동차", ["시도", "차종", "용도"],
                  ["출처: 국토교통부 「자동차등록현황보고」 — KOSIS 자동차등록대수현황 시도별(DT_MLTM_5498), 각 연도 12월 말 기준 (2011~)",
                   "2005~2010년은 시도별 합계만: KOSIS e-지방지표 「1인당 자동차 등록대수」의 자동차등록대수(DT_1YL20731) — 차종·용도 = 계",
                   "이륜자동차 제외(9202). 전국 = 시도 합(2011~)"],
                  kurl("molit", "car_sido"))
        for r in A or []:
            s = sido(r["C1"]); car = "계" if r["C3"] in ("총계", "계") else r["C3"]; use = "계" if r["item"] in ("계", "총계") else r["item"]
            if s and r["v"] is not None and r["year"] >= 2011:
                t.put([s, car, use], "등록대수[대]", r["year"], r["v"])
        add_national(t)
        for r in E or []:
            if "자동차등록대수" in r["item"].replace(" ", "") and r["year"] < 2011:
                s = sido(r["C1"])
                if s:
                    t.put([s, "계", "계"], "등록대수[대]", r["year"], r["v"])
        out.append(t.rec(lambda k: (SIDO_ORDER.index(k[0]) if k[0] in SIDO_ORDER else 99, CAR.index(k[1]) if k[1] in CAR else 9, USE.index(k[2]) if k[2] in USE else 9)))
    # 9202 이륜차
    A, B = load("molit", "moto_2005"), load("molit", "moto_sido")
    if A or B:
        t = Table(9202, "이륜자동차 신고대수 (시도·규모·용도)", "molit", "자동차", ["시도", "규모·배기량", "용도"],
                  ["출처: 국토교통부 「자동차등록현황보고」 — 이륜차신고현황 연도별(DT_MLTM_2042, 2005~2012, 배기량별 전국)·시도별(DT_MLTM_5559, 2013~, 규모별, 12월 말)",
                   "구분이 두 시기에 다름: 2012년까지 배기량(50cc미만·50cc이상·100cc초과·260cc초과), 2013년부터 규모(경형·소형·중형·대형). 시기를 잇는 비교는 '계'만",
                   "50cc 미만 이륜차 사용신고 의무화(2012) 전후로 신고대수 기준이 다름 — 정책 연표 moped_registration 참고"],
                  kurl("molit", "moto_sido"))
        for r in A or []:
            use = "계" if r["C2"] in ("계", "") else r["C2"]; k = "계" if r["item"] in ("소계", "계") else r["item"]
            t.put(["전국", k, use], "신고대수[대]", r["year"], r["v"])
        for r in B or []:
            s = sido(r["C1"]); use = "계" if r["C3"] in ("계", "") else r["C3"]; k = "계" if r["item"] in ("소계", "계") else r["item"]
            if s and r["year"] >= 2013:
                t.put([s, k, use], "신고대수[대]", r["year"], r["v"])
        nat = {k for k, d in t.cells.items() if k[0] == "전국" and any(y >= 2013 for y in d)}
        if not nat:
            sub = Table(0, "", "molit", "", [])
            sub.cells = {k: {y: v for y, v in d.items() if y >= 2013} for k, d in t.cells.items() if k[0] != "전국"}
            add_national(sub)
            for k, d in sub.cells.items():
                if k[0] == "전국":
                    for y, v in d.items():
                        t.put(list(k[:-1]), k[-1], y, v)
        out.append(t.rec(sido_order))
    # 9203 도로 연장
    A = load("molit", "road_sido")
    if A:
        t = Table(9203, "도로 연장 (시도·도로종류)", "molit", "도로", ["시도", "도로종류"],
                  ["출처: 국토교통부 「도로현황」 — KOSIS 시·도별 도로현황(DT_MLTM_962), 각 연도 12월 31일 기준", "연장 단위는 원표 그대로(m 또는 km — 수치항목 이름에 표시)"],
                  kurl("molit", "road_sido"))
        for r in A:
            s = sido(r["C1"])
            if not s or r["v"] is None:
                continue
            rt = "계" if r["C2"] in ("전체", "계", "총계", "") else r["C2"]
            unit = f"[{r['unit']}]" if r["unit"] else ""
            t.put([s, rt], f"{r['item']}{unit}", r["year"], r["v"])
        out.append(t.rec(sido_order))
    # 9204 평균 일교통량
    A = load("molit", "aadt")
    if A:
        t = Table(9204, "평균 일교통량 (도로종류·차종)", "molit", "교통량", ["도로종류", "차종"],
                  ["출처: 국토교통부 「도로교통량조사」 — KOSIS 도로종류별 차종별 평균일교통량과 구성비(DT_MLTM_1240)", "평균 일교통량(AADT, 대/일)은 상시·수시 조사지점 평균 — 지점 구성이 해마다 조금씩 다름"],
                  kurl("molit", "aadt"))
        for r in A:
            unit = f"[{r['unit']}]" if r["unit"] else ""
            t.put([r["C1"], r["C2"] or "계"], f"{r['item']}{unit}", r["year"], r["v"])
        out.append(t.rec())
    # 9205 주행거리
    A = load("molit", "vkt_sido")
    if A:
        t = Table(9205, "자동차 주행거리 (시도·용도·차종)", "molit", "교통량", ["시도", "용도", "차종"],
                  ["출처: 한국교통안전공단 「자동차주행거리통계」 — KOSIS 용도별 차종별 시군구별 자동차주행거리(DT_426001_N004), 2012~",
                   "2025년부터 산출 방식이 원측정값으로 바뀜(2024년까지 가중 추정치) — 2024→2025 단절 주의",
                   "사고율 분모로 쓸 때: 연간 주행거리(대·km)로 나누면 '주행거리당 사고' (패널 비율 환산에서 배율 1억)"],
                  kurl("molit", "vkt_sido"))
        for r in A:
            s = sido(r["C1"])
            if not s:
                continue
            unit = f"[{r['unit']}]" if r["unit"] else ""
            t.put([s, "계" if r["C2"] in ("전체", "계") else r["C2"], "계" if r["C3"] in ("합계", "계") else r["C3"]], f"{r['item']}{unit}", r["year"], r["v"])
        out.append(t.rec(sido_order))
    return out


# ---------------- 경찰청 ----------------
def school_zones():
    rows = list(csv.DictReader(open(TP.ext_src("police") / "어린이보호구역_지정현황.csv", encoding="utf-8")))
    t = Table(9003, "어린이보호구역 지정 현황", "police", "교통안전 인프라", ["구분"],
              ["출처: 경찰청 「어린이보호구역 정기보고」 — e-나라지표 1616 어린이보호구역 지정현황 (2025-11-28 갱신분)",
               "2009~2024년. 지정대상개소·지정률은 2021년까지만 공표. 2008년 이전·2025년은 미공표(필요 시 CSV 에 추가)"],
              "https://www.index.go.kr/unity/potal/main/EachDtlPageDetail.do?idx_cd=1616")
    for r in rows:
        y = int(r["연도"])
        for m, k in (("지정개소[개소]", "지정개소"), ("지정대상개소[개소]", "지정대상개소"), ("지정률[%]", "지정률")):
            t.put(["전국"], m, y, num(r[k]))
    return t.rec(lambda k: ["지정개소[개소]", "지정대상개소[개소]", "지정률[%]"].index(k[-1]))


def age_group(a):
    a = a.replace(" ", "")
    if a in ("계", "합계", "총계"):
        return None
    m = re.match(r"^(\d+)", a)
    return int(m.group(1)) if m else None


AGE_BANDS = [("16~19세", 16, 19), ("20~29세", 20, 29), ("30~39세", 30, 39), ("40~49세", 40, 49), ("50~59세", 50, 59), ("60~64세", 60, 64),
             ("65~69세", 65, 69), ("70~74세", 70, 74), ("75세 이상", 75, 200)]


def lib_police():
    out = [school_zones()]
    LIC = "운전면허 소지자"
    A = load("police", "lic_type")
    if A:
        t = Table(9301, f"{LIC} (면허종별)", "police", "운전면허", ["면허종별"],
                  ["출처: 경찰청 「운전면허소지자현황」 — KOSIS 운전면허소지자현황(면허종별, TX_13201_A000), 연말 기준", "한 사람이 여러 종별을 가지면 종별마다 셈 — '총계'는 사람 수"],
                  kurl("police", "lic_type"))
        for r in A:
            k = "총계" if r["C1"] in ("총계", "계") else r["C1"]
            t.put([k], "소지자[명]", r["year"], r["v"])
        out.append(t.rec())
    A, B = load("police", "lic_sex_2005"), load("police", "lic_sex")
    G = TP.ext_src("police") / "datagokr" / "운전면허소지자_성별_15048417.csv"
    if A or B or G.exists():
        t = Table(9302, f"{LIC} (성별)", "police", "운전면허", ["성별"],
                  ["출처: 경찰청 「운전면허소지자현황」 — KOSIS 성별(TX_13201_A001, ~2018) · 성별(DT_13201_A004, 2019~); KOSIS 자료가 없는 연도는 공공데이터포털 「운전면허소지자 성별 현황」(15048417, 2005~2021)",
                   "보유율(%)은 2018년까지 KOSIS 표에 있는 값"], kurl("police", "lic_sex"))
        if G.exists():  # 공공데이터포털 값을 먼저 넣고 KOSIS 값이 있으면 덮어씀
            for r in rows_csv(G):
                y = int(r["연도"]); m_, f_ = num(r["남"]), num(r["여"])
                t.put(["남자"], "소지자[명]", y, m_); t.put(["여자"], "소지자[명]", y, f_)
                t.put(["계"], "소지자[명]", y, (m_ or 0) + (f_ or 0))
        for r in A or []:
            if r["C1"] == "보유율":
                t.put(["계"], "보유율[%]", r["year"], r["v"])
            else:
                t.put(["계" if r["C1"] in ("계", "총계") else r["C1"]], "소지자[명]", r["year"], r["v"])
        for r in B or []:
            if r["year"] >= 2019 and r["C1"] in ("총계", "계", ""):
                t.put(["계" if r["C2"] in ("계", "총계") else r["C2"]], "소지자[명]", r["year"], r["v"])
        out.append(t.rec(lambda k: (["계", "남자", "여자"].index(k[0]) if k[0] in ("계", "남자", "여자") else 9, k[-1])))
    A = load("police", "lic_age")
    if A:
        t = Table(9303, f"{LIC} (연령대별)", "police", "운전면허", ["연령대"],
                  ["출처: 경찰청 「운전면허소지자현황」 — KOSIS 연령대별(DT_13201_A002, 1세 단위 → 연령대로 합침), 2019~",
                   "고령 운전자 분석: '65세 이상'·'75세 이상'을 노인 인구(9001·9102)로 나누면 고령 면허 보유율"], kurl("police", "lic_age"))
        for r in A:
            name = r["C1"] if r["C1"] else r["C2"]
            if r["C2"] and r["C2"] not in ("총계", "계"):
                continue
            if name in ("계", "총계", "A00"):
                t.put(["계"], "소지자[명]", r["year"], r["v"]); continue
            a = age_group(name)
            if a is None:
                continue
            for b, lo, hi in AGE_BANDS:
                if lo <= a <= hi:
                    t.put([b], "소지자[명]", r["year"], r["v"], add=True)
            if a >= 65:
                t.put(["65세 이상(합)"], "소지자[명]", r["year"], r["v"], add=True)
        order = ["계"] + [b for b, _, _ in AGE_BANDS] + ["65세 이상(합)"]
        out.append(t.rec(lambda k: order.index(k[0]) if k[0] in order else 99))
    A = load("police", "lic_region")
    if A:
        t = Table(9304, f"{LIC} (시도별)", "police", "운전면허", ["시도"],
                  ["출처: 경찰청 「운전면허소지자현황」 — KOSIS 지역별(DT_13201_A005), 2019~ · 경기 = 경기남부 + 경기북부(지방경찰청 기준)"], kurl("police", "lic_region"))
        for r in A:
            if r["C1"] not in ("총계", "계", ""):
                continue
            s = sido(r["C2"])
            if s:
                t.put([s], "소지자[명]", r["year"], r["v"], add=r["C2"] in ("경기남부", "경기북부"))
        out.append(t.rec(sido_order))
    out += police_datagokr()
    return out


DG = TP.ext_src("police") / "datagokr"
DG_URL = "https://www.data.go.kr/data/{}/fileData.do"


def rows_csv(f):
    return list(csv.DictReader(l for l in open(f, encoding="utf-8") if not l.startswith("#")))


def police_datagokr():
    """공공데이터포털 파일데이터(경찰청) → 9305~9308"""
    out = []
    f = DG / "고령운전자_자진반납_15065567.csv"
    if f.exists():
        t = Table(9305, "운전면허 자진반납 (시도·고령)", "police", "운전면허", ["시도", "반납자"],
                  ["출처: 경찰청 「시도 경찰청별 고령운전자 자진반납 현황」(공공데이터포털 15065567, 2025-12-31 기준) — 2015~2025",
                   "시도 = 시도경찰청 기준(경기 = 경기남부 + 경기북부, 경기북부·세종은 개청 전 0). 전국 = 시도 합",
                   "고령 = 65세 이상. 2019년 급증은 지자체 반납 지원금(교통카드 등) 확대 시기와 겹침 — 정책 연표 elderly_licence 참고",
                   "고령 운전면허 소지자(9303 '65세 이상(합)')로 나누면 반납률"], DG_URL.format(15065567))
        for r in rows_csv(f):
            s = sido(r["지방청"])
            if not s:
                continue
            for k, v in r.items():
                m = re.match(r"^(\d{4}) (65세 이상|전체)$", k or "")
                if m:
                    t.put([s, "65세 이상" if m.group(2) != "전체" else "전체"], "반납자[명]", int(m.group(1)), num(v), add=True)
        add_national(t)
        for k, d in list(t.cells.items()):
            if k[1] == "전체":
                o = t.cells.get((k[0], "65세 이상", k[2]), {})
                for y, v in d.items():
                    if v and o.get(y) is not None:
                        t.put([k[0], "65세 이상"], "고령 비중[%]", y, round(o[y] / v * 100, 2))
        out.append(t.rec(lambda k: (SIDO_ORDER.index(k[0]) if k[0] in SIDO_ORDER else 99, k[1] != "전체", k[2])))
    f = DG / "무인교통단속카메라_설치연도별_15028200.csv"
    if f.exists():
        R = rows_csv(f)
        t = Table(9306, "무인교통단속카메라 설치 대수 (시도·연도)", "police", "교통안전 인프라", ["시도", "카메라 구분"],
                  ["출처: 공공데이터포털 「전국무인교통단속카메라표준데이터」(15028200, 경찰청·지자체, 데이터기준일자 2026-10-20) — 고정식 44,650대를 설치연도로 집계",
                   "'지금 남아 있는' 카메라를 설치연도로 센 값: 철거·교체된 카메라는 빠지므로 과거 누적 대수는 실제보다 작을 수 있음. 설치연도 미상 4,644대는 연도별 값에서 제외",
                   "카메라 구분: 전체 / 어린이보호구역(보호구역구분 코드 2 — 제한속도 30km/h 가 대부분이라 어린이보호구역으로 추정, 표준 정의서 미확인) / 단속구분 코드 1·2·4(뜻 미확인: 1 은 구간단속 길이가 있는 경우가 많아 과속 계열로 보임)",
                   "수치: 신규 설치[대] = 그 해 설치, 누적[대] = 그 해까지 설치(현존 기준). 2026년(일부)은 제외"], "https://www.data.go.kr/data/15028200/standard.do")
        new = collections.defaultdict(float)
        for r in R:
            s = sido(r["시도명"]); y = r["설치연도"]
            if not s or not y.isdigit() or not (Y0 - 30 <= int(y) <= Y1):
                continue
            y = int(y); n = float(r["대수"])
            keys = ["전체"]
            if r["보호구역구분코드"] == "2":
                keys.append("어린이보호구역(추정)")
            if r["단속구분코드"] in ("1", "2", "4"):
                keys.append(f"단속구분 코드 {r['단속구분코드']}")
            for g in (s, "전국"):
                for k in keys:
                    new[(g, k, y)] += n
        groups = {(g, k) for g, k, _ in new}
        for g, k in groups:
            cum = sum(v for (gg, kk, y), v in new.items() if gg == g and kk == k and y < Y0)
            for y in range(Y0, Y1 + 1):
                v = new.get((g, k, y), 0.0); cum += v
                t.put([g, k], "신규 설치[대]", y, v)
                t.put([g, k], "누적[대]", y, cum)
        order = ["전체", "어린이보호구역(추정)", "단속구분 코드 1", "단속구분 코드 2", "단속구분 코드 4"]
        out.append(t.rec(lambda k: (SIDO_ORDER.index(k[0]) if k[0] in SIDO_ORDER else 99, order.index(k[1]) if k[1] in order else 9, k[2])))
    f = DG / "음주운전_재범횟수별_단속_15043113.csv"
    if f.exists():
        t = Table(9307, "음주운전 단속 (재범 횟수별)", "police", "단속", ["위반 횟수"],
                  ["출처: 경찰청 「연도별 음주운전 재범자 단속 실적 현황」(공공데이터포털 15043113, 2025-12-31 기준) — 2010~2025 전국",
                   "계 = 1회~7회 이상 합 = 그 해 음주운전 단속 건수. 1회 = 처음 적발, 2회 이상 = 재범",
                   "제2 윤창호법(2019-06, 단속기준 0.03%) 이후에도 단속 건수가 줄어든 점 주의 — 단속 건수는 단속 활동량(코로나19 시기 일제검문 축소 등)에 좌우됨"], DG_URL.format(15043113))
        for r in rows_csv(f):
            y = int(r["년도"]); tot = 0; re_ = 0
            for k, v in r.items():
                if k == "년도":
                    continue
                v = num(v); t.put([k], "단속[건]", y, v); tot += v or 0
                if k != "1회":
                    re_ += v or 0
            t.put(["계"], "단속[건]", y, tot); t.put(["재범(2회 이상)"], "단속[건]", y, re_)
            t.put(["재범(2회 이상)"], "재범 비중[%]", y, round(re_ / tot * 100, 2) if tot else None)
        order = ["계", "1회", "재범(2회 이상)", "2회", "3회", "4회", "5회", "6회", "7회이상"]
        out.append(t.rec(lambda k: (order.index(k[0]) if k[0] in order else 99, k[1])))
    f = DG / "교통단속_위반유형별_3051800.csv"
    if f.exists():
        t = Table(9308, "교통법규 위반 단속 (위반 유형별)", "police", "단속", ["위반 유형"],
                  ["출처: 경찰청 「교통 단속 현황」(공공데이터포털 3051800, 2018-12-31 기준) — 2014~2018 전국 (이후 연도는 공개 파일 없음)",
                   "과속 단속에는 무인 단속카메라 적발이 포함됨 — 9306(카메라 설치)과 함께 보기"], DG_URL.format(3051800))
        for r in rows_csv(f):
            y = int(r["구분"]); tot = 0
            for k, v in r.items():
                if k == "구분":
                    continue
                v = num(v); t.put([k], "단속[건]", y, v); tot += v or 0
            t.put(["계"], "단속[건]", y, tot)
        out.append(t.rec(lambda k: (k[0] != "계", k[0])))
    return out


# ---------------- 제도 연표 ----------------
def lib_policy():
    rows = list(csv.DictReader(open(TP.ext_src("policy") / "정책_연표.csv", encoding="utf-8")))
    t = Table(9901, "교통안전 제도 시행 (연도 더미)", "policy", "제도 시행 연표", ["분류", "제도"],
              ["출처: 국가법령정보센터·정책브리핑·경찰청 보도자료로 확인한 시행일 — 04_Libraries/01_Standard_Law/LIB-POLICY/정책_연표.csv (항목별 근거·확인 상태 포함)",
               "값 = 1(그 해에 시행 중) / 0. 연간 자료의 개입 첫해(ITS연도): 시행일이 7월 이후면 다음 해",
               "다중회귀(OLS)의 설명변수나 중단 시계열의 개입 연도로 사용. 2019·2020~2021·2023년은 제도가 몰려 있어 효과를 따로 떼기 어려움",
               "확인 상태가 '미확인'인 제도(시행일 없음)와 외생 사건(코로나19 등 — 기간 더미로 넣을 것)은 넣지 않음"], "https://www.law.go.kr")
    events = []
    for r in rows:
        its = int(r["ITS연도"]) if r["ITS연도"].isdigit() else None
        events.append({"id": r["id"], "cat": r["분류"], "name": r["제도명"], "date": r["시행일"], "year": int(r["시행연도"]) if r["시행연도"].isdigit() else None,
                       "its": its, "target": [x.strip() for x in r["영향대상"].split(";") if x.strip()], "basis": r["근거"], "desc": r["내용"],
                       "status": r["확인상태"], "url": r["확인출처URL"].split(" ; ")[0], "note": r["비고"]})
        if its is None or r["분류"] == "외생":  # 외생 사건(코로나19 등)은 기간 더미가 맞으므로 OLS 의 '더미 연도'(예: 2020-2022)로 넣음
            continue
        nm = r["제도명"] if len(r["제도명"]) <= 40 else r["제도명"][:39] + "…"
        for y in range(Y0, Y1 + 1):
            t.put([r["분류"], f"{nm} ({r['시행일'][:7]})"], "시행[0/1]", y, 1.0 if y >= its else 0.0)
    cats = ["음주", "속도", "어린이", "보행자", "고령", "이륜PM", "안전띠", "사업용", "기타", "외생"]
    meta, rec = t.rec(lambda k: (cats.index(k[0]) if k[0] in cats else 99, k[1]))
    (TP.ext_raw("policy")).mkdir(parents=True, exist_ok=True)
    (TP.ext_raw("policy") / "events.json").write_text(json.dumps({"source": TP.rel(TP.ext_src("policy") / "정책_연표.csv"), "events": events}, ensure_ascii=False, indent=1), encoding="utf-8")
    return [(meta, rec)]


def lib_kostat():
    import make_pop_raw
    src = sorted((TP.ext_src("kostat")).glob("*.xlsx"))
    old = [p for p in src if "2005" in p.name and "2010" in p.name]
    new = [p for p in src if "2015" in p.name]
    if not old or not new:
        print("  kostat: 03_References/02_Statistics/files/kostat 에 2005_2010, 2015_2025 원본 엑셀이 없어 건너뜀")
        return None
    tmp = TP.ext_raw("kostat") / "_tmp.json.gz"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    make_pop_raw.main(str(old[0]), str(new[0]), str(tmp))
    j = json.load(gzip.open(tmp, "rt", encoding="utf-8")); tmp.unlink()
    for m in j["meta"]:
        m["lib"] = "kostat"; m["root"] = "통계청(국가데이터처) 자료"; m["path"] = [m["root"]] + m["path"][1:]
    return [(m, r) for m, r in zip(j["meta"], j["recs"])]


LIBS = {"kostat": lib_kostat, "mois": lib_mois, "molit": lib_molit, "police": lib_police, "policy": lib_policy}


def write(lib, pairs):
    pairs = [(m, r) for m, r in (pairs or []) if m]
    d = TP.ext_raw(lib); d.mkdir(parents=True, exist_ok=True)
    f = d / f"{lib}.json.gz"
    if not pairs:
        print(f"  {lib}: 수집 자료 없음 — 원본을 만들지 않음")
        return None
    body = {"exported": time.strftime("%Y-%m-%dT%H:%M:%S"), "source": meta_of(lib)["name"], "lib": lib,
            "meta": [m for m, _ in pairs], "recs": [r for _, r in pairs]}
    # 내용이 같으면 파일을 다시 쓰지 않음(빌드가 '원본 변화 없음'으로 건너뛰게)
    norm = lambda b: json.dumps({**b, "exported": "", "recs": [{**r, "ts": 0} for r in b["recs"]]}, ensure_ascii=False, sort_keys=True)
    if f.exists():
        try:
            old = json.load(gzip.open(f, "rt", encoding="utf-8"))
            if norm(old) == norm(body):
                print(f"  {lib}: 변화 없음 ({len(pairs)}개 장표)")
                return f
        except Exception:
            pass
    with gzip.GzipFile(f, "wb", mtime=0) as g:
        g.write(json.dumps(body, ensure_ascii=False).encode("utf-8"))
    print(f"  {lib}: {f.relative_to(ROOT) if f.is_relative_to(ROOT) else f} — 장표 {len(pairs)}개 ({', '.join(m['pid'] for m, _ in pairs)})")
    return f


def import_dump(path):
    """KC.dump() 가 돌려준 문자열(도구 결과 파일 포함) → <원자료>/kosis/<key>.csv.gz"""
    txt = Path(path).read_text(encoding="utf-8")
    if txt.lstrip().startswith("["):  # 도구 결과 파일: [{type,text}]
        txt = "".join(x.get("text", "") for x in json.loads(txt))
        try:
            txt = json.loads(txt.split("\n\n(captured")[0])
        except Exception:
            pass
    m = re.search(r"<<KC>>(.*?)<<KC>>", txt, re.S)
    if not m:
        sys.exit("수집 결과 표식(<<KC>>)을 찾지 못했습니다.")
    obj = json.loads(m.group(1))
    cols = ["PRD_DE", "C1_NM", "C2_NM", "C3_NM", "C4_NM", "ITM_NM", "UNIT_NM", "DT"]
    for key, v in obj.items():
        lib, k = key.split("/", 1)
        d = TP.ext_src(lib) / "kosis"; d.mkdir(parents=True, exist_ok=True)
        buf = io.StringIO(); w = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore"); w.writeheader()
        for r in v["recs"]:
            w.writerow({c: r.get(c, "") for c in cols})
        with gzip.GzipFile(d / f"{k}.csv.gz", "wb", mtime=0) as g:
            g.write(buf.getvalue().encode("utf-8"))
        (d / f"{k}.meta.json").write_text(json.dumps(v.get("meta") or {}, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  {key}: {len(v['recs'])}행 → {d / (k + '.csv.gz')}")


def main(argv):
    sys.path.insert(0, str(TP.SRC / "src"))
    if argv[:1] == ["--import"]:
        for p in argv[1:]:
            import_dump(p)
        return
    libs = argv or list(LIBS)
    for lib in libs:
        write(lib, LIBS[lib]())


if __name__ == "__main__":
    main(sys.argv[1:])
