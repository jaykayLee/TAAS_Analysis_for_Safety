"""
통계청(KOSIS) 인구총조사 연령별 인구 2개 파일 → TAAS 라이브러리 원본 형식(json.gz)

  python make_pop_raw.py pop_2005_2010.xlsx pop_2015_2025.xlsx out.json.gz

만드는 장표 (라이브러리에 함께 들어가 패널에서 TAAS 장표와 같이 분석)
  9001 연령구분별 인구 (어린이·일반·노인)   축: 시도 × 연령구분(전체/어린이/일반/노인)
        수치: 인구[명] · 남자[명] · 여자[명] · 구성비[%] · 인구_연간보간[명]
  9002 연령별 인구 (5세 단위)               축: 시도 × 연령(5세)   수치: 인구 · 남자 · 여자

연령 구분 (TAAS 기준과 맞춤)
  어린이 = 12세 이하  ← 0~4세 + 5~9세 + 10~14세 × 3/5  (10~14세 안 균등 분포 가정, 추정)
  노인   = 65세 이상  ← 통계표의 '65세이상' (정확)
  일반   = 전체 − 어린이 − 노인 (13~64세, 연령미상 포함)
주의
  2005·2010년: 인구총조사(내국인, 외국인 제외) / 2015~2025년: 총인구(외국인 포함) → 2010→2015 사이 기준 차이
  인구_연간보간: 2006~2009, 2011~2014년을 앞뒤 실측 연도로 직선 보간 (상관분석의 점 개수 확보용, 실측 아님)
"""
import gzip, json, re, sys, time
import openpyxl

SIDO = {"전국": "전국", "서울특별시": "서울", "부산광역시": "부산", "대구광역시": "대구", "인천광역시": "인천", "광주광역시": "광주",
        "대전광역시": "대전", "울산광역시": "울산", "세종특별자치시": "세종", "경기도": "경기", "강원도": "강원", "강원특별자치도": "강원",
        "충청북도": "충북", "충청남도": "충남", "전라북도": "전북", "전북특별자치도": "전북", "전라남도": "전남", "경상북도": "경북",
        "경상남도": "경남", "제주도": "제주", "제주특별자치도": "제주"}
SIDO_ORDER = ["전국", "서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종", "경기", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주"]
BANDS = ["0~4세", "5~9세", "10~14세", "15~19세", "20~24세", "25~29세", "30~34세", "35~39세", "40~44세", "45~49세", "50~54세", "55~59세",
         "60~64세", "65~69세", "70~74세", "75~79세", "80~84세", "85~89세", "90~94세", "95~99세", "100세이상", "85세이상", "연령미상"]
GROUPS = ["전체", "어린이 0~12세", "일반 13~64세", "노인 65세 이상"]


def norm_age(a):
    a = str(a or "").strip().replace(" ", "").replace("-", "~")
    return {"계": "합계", "합계": "합계", "65세이상": "65세이상", "15세미만": "15세미만", "15~64세": "15~64세"}.get(a, a)


def num(v):
    if v is None or v in ("-", "X", ""):
        return None
    return float(v)


def read(path):
    """→ {(year, 시도, 연령): (총, 남, 여)} , meta"""
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb["데이터"]; rows = list(ws.iter_rows(values_only=True))
    years = []; y = None
    for j, c in enumerate(rows[0]):
        if j < 2: continue
        if c: y = int(str(c)[:4])
        years.append(y)
    out = {}; reg = None
    for r in rows[2:]:
        if r[0]: reg = SIDO.get(str(r[0]).strip(), str(r[0]).strip())
        age = norm_age(r[1])
        for k in range(0, len(years), 3):
            yr = years[k]; t, m, f = (num(r[2 + k + i]) if 2 + k + i < len(r) else None for i in range(3))
            out[(yr, reg, age)] = (t, m, f)
    meta = {str(r[0]).strip("○ ").strip(): r[1] for r in wb["메타정보"].iter_rows(values_only=True) if r[0]}
    notes = [str(r[1]).strip() for r in wb["메타정보"].iter_rows(values_only=True) if r[1] and str(r[1]).strip().startswith(("주", "-"))]
    return out, meta, notes


def main(f1, f2, out):
    A, m1, n1 = read(f1); B, m2, n2 = read(f2)
    D = {**A, **B}
    years = sorted({k[0] for k in D})
    regs = [r for r in SIDO_ORDER if any(k[1] == r for k in D)]
    # 연령구분 계산
    G = {}
    for yr in years:
        for rg in regs:
            def g(a, i): v = D.get((yr, rg, a)); return v[i] if v else None
            for i in range(3):
                tot = g("합계", i)
                if tot is None: continue
                b0, b5, b10 = g("0~4세", i), g("5~9세", i), g("10~14세", i)
                child = None if None in (b0, b5, b10) else b0 + b5 + b10 * 0.6
                old = g("65세이상", i)
                if old is None:
                    parts = [g(a, i) for a in ["65~69세", "70~74세", "75~79세", "80~84세", "85세이상"]]
                    old = None if None in parts else sum(parts)
                mid = None if None in (child, old) else tot - child - old
                for gname, v in zip(GROUPS, (tot, child, mid, old)):
                    G.setdefault((yr, rg, gname), [None, None, None])[i] = v
    # 연간 보간 (총인구만)
    allyears = list(range(years[0], years[-1] + 1))
    def interp(rg, gname):
        pts = {yr: G[(yr, rg, gname)][0] for yr in years if (yr, rg, gname) in G and G[(yr, rg, gname)][0] is not None}
        res = {}
        ks = sorted(pts)
        for yr in allyears:
            if yr in pts: res[yr] = pts[yr]; continue
            lo = max([k for k in ks if k < yr], default=None); hi = min([k for k in ks if k > yr], default=None)
            if lo is not None and hi is not None:
                res[yr] = pts[lo] + (pts[hi] - pts[lo]) * (yr - lo) / (hi - lo)
        return res

    fmt = lambda v: "" if v is None else (f"{v:,.0f}" if abs(v) >= 100 or float(v).is_integer() else f"{v:.2f}")
    ts = int(time.time() * 1000)
    # 9001
    cols = [[str(y)] for y in allyears]
    rows, data = [], []
    for rg in regs:
        for gname in GROUPS:
            ip = interp(rg, gname)
            for mi, mname in enumerate(["인구[명]", "남자[명]", "여자[명]", "구성비[%]", "인구_연간보간[명]"]):
                rows.append([rg, gname, mname]); line = []
                for yr in allyears:
                    v = None; cur = G.get((yr, rg, gname))
                    if mi < 3: v = cur[mi] if cur else None
                    elif mi == 3:
                        tot = G.get((yr, rg, "전체"))
                        v = (cur[0] / tot[0] * 100) if cur and tot and cur[0] is not None and tot[0] else None
                    else: v = ip.get(yr)
                    line.append(fmt(v))
                data.append(line)
    note_common = ["주) 출처: 통계청 KOSIS 「인구총조사」 — 2005·2010년 " + str(m1.get("통계표명", "")) + "(외국인 제외), 2015~2025년 " + str(m2.get("통계표명", "")) + "(외국인 포함)",
                   "주) 2010년→2015년 사이에 외국인 포함 여부가 바뀌어 인구 수준이 한 번 뜁니다. 추세 비교는 2015년 이후 또는 구성비로 보세요."]
    rec1 = {"key": "9001|2005-2025", "pid": "9001", "label": "2005-2025", "vc": "", "lab": ["시도", "연령구분", "구분"], "colDims": ["연도"],
            "rows": rows, "cols": cols, "data": data, "pages": 1, "nodata": False, "meaAll": 5, "meaOn": 5, "meaMissing": [], "dimAll": True, "dimMissing": [],
            "v8": True, "ts": ts, "source": "KOSIS",
            "msg": note_common + ["주) 어린이(12세 이하)는 0~4세+5~9세+10~14세×3/5로 추정(10~14세 안 균등 분포 가정). 노인은 65세 이상 실측, 일반은 전체−어린이−노인.",
                                  "주) 인구_연간보간: 2006~2009·2011~2014년은 앞뒤 실측 연도의 직선 보간값(실측 아님, 상관분석 점 개수 확보용)."]}
    # 9002 (5세 단위 실측)
    rows2, data2 = [], []
    for rg in regs:
        for age in ["합계"] + BANDS:
            if not any((yr, rg, age) in D for yr in years): continue
            for mi, mname in enumerate(["인구[명]", "남자[명]", "여자[명]"]):
                rows2.append([rg, age, mname]); data2.append([fmt(D[(yr, rg, age)][mi]) if (yr, rg, age) in D and D[(yr, rg, age)][mi] is not None else "" for yr in allyears])
    rec2 = {**{k: rec1[k] for k in ("vc", "pages", "nodata", "meaMissing", "dimAll", "dimMissing", "v8", "ts", "source")}, "key": "9002|2005-2025", "pid": "9002", "label": "2005-2025",
            "lab": ["시도", "연령", "구분"], "colDims": ["연도"], "rows": rows2, "cols": cols, "data": data2, "meaAll": 3, "meaOn": 3, "msg": note_common + ["주) 2005·2010년은 85세이상, 2015년부터는 100세이상까지 5세 단위로 공표."]}
    path = ["인구(통계청 KOSIS)", "연령별 인구"]
    meta = [{"pid": "9001", "subjectId": "0", "menuId": "9001", "name": "연령구분별 인구 (어린이·일반·노인)", "path": path + ["연령구분별 인구 (어린이·일반·노인)"], "root": path[0], "trend": "N",
             "dateInfo": {"minYear": str(allyears[0]), "maxYear": str(allyears[-1]), "dimAttrId": 0}, "dims": [], "source_url": m2.get("통계표URL")},
            {"pid": "9002", "subjectId": "0", "menuId": "9002", "name": "연령별 인구 (5세 단위)", "path": path + ["연령별 인구 (5세 단위)"], "root": path[0], "trend": "N",
             "dateInfo": {"minYear": str(allyears[0]), "maxYear": str(allyears[-1]), "dimAttrId": 0}, "dims": [], "source_url": m2.get("통계표URL")}]
    with gzip.open(out, "wt", encoding="utf-8") as f:
        json.dump({"exported": time.strftime("%Y-%m-%dT%H:%M:%S"), "source": "KOSIS 인구총조사", "files": [f1, f2], "meta": meta, "recs": [rec1, rec2]}, f, ensure_ascii=False)
    # 확인용 출력
    for yr in years:
        t = G[(yr, "전국", "전체")][0]; c = G[(yr, "전국", "어린이 0~12세")][0]; o = G[(yr, "전국", "노인 65세 이상")][0]
        print(yr, f"전체 {t:,.0f}  어린이 {c:,.0f} ({c/t*100:.1f}%)  노인 {o:,.0f} ({o/t*100:.1f}%)")
    print("rows", len(rows), len(rows2), "regions", regs)


if __name__ == "__main__":
    main(*sys.argv[1:4])
