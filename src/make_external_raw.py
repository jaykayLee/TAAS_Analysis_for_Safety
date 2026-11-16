"""
외부 자료 CSV(data/source/external) → 라이브러리 원본 형식(data/raw/external/taas_raw_external.json.gz)

    python src/make_external_raw.py

9003 어린이보호구역 지정 현황 (경찰청, e-나라지표 1616): 수치 지정개소[개소] · 지정대상개소[개소] · 지정률[%]
"""
import csv, gzip, json, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "source" / "external"
OUT = ROOT / "data" / "raw" / "external" / "taas_raw_external.json.gz"


def school_zones():
    rows = list(csv.DictReader(open(SRC / "어린이보호구역_지정현황.csv", encoding="utf-8")))
    years = [r["연도"] for r in rows]
    meas = [("지정개소[개소]", "지정개소"), ("지정대상개소[개소]", "지정대상개소"), ("지정률[%]", "지정률")]
    data = [[r[k] for r in rows] for _, k in meas]
    rec = {"key": "9003|all", "pid": "9003", "label": f"{years[0]}-{years[-1]}", "vc": "", "lab": ["구분", "구분"], "colDims": ["연도"],
           "rows": [["전국", m] for m, _ in meas], "cols": [[y] for y in years], "data": data, "pages": 1, "nodata": False,
           "meaAll": 3, "meaOn": 3, "meaMissing": [], "dimAll": True, "dimMissing": [], "v8": True, "ts": int(time.time() * 1000), "source": "경찰청",
           "msg": ["주) 출처: 경찰청 「어린이보호구역 정기보고」 — e-나라지표 1616 어린이보호구역 지정현황 (2025-11-28 갱신분)",
                   "주) 2009~2024년. 지정대상개소·지정률은 2021년까지만 공표. 2008년 이전·2025년은 미공표(필요 시 CSV 에 추가)"]}
    meta = {"pid": "9003", "subjectId": "0", "menuId": "9003", "name": "어린이보호구역 지정 현황", "root": "외부자료(경찰청 등)",
            "path": ["외부자료(경찰청 등)", "교통안전 인프라", "어린이보호구역 지정 현황"], "trend": "N",
            "dateInfo": {"minYear": years[0], "maxYear": years[-1], "dimAttrId": 0}, "dims": [],
            "source_url": "https://www.index.go.kr/unity/potal/main/EachDtlPageDetail.do?idx_cd=1616"}
    return meta, rec


def main():
    metas, recs = [], []
    for f in (school_zones,):
        m, r = f(); metas.append(m); recs.append(r)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(OUT, "wt", encoding="utf-8") as g:
        json.dump({"exported": time.strftime("%Y-%m-%dT%H:%M:%S"), "source": "외부 자료", "meta": metas, "recs": recs}, g, ensure_ascii=False)
    print(f"{OUT.relative_to(ROOT)}: 장표 {len(recs)}개")


if __name__ == "__main__":
    main()
