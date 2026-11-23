"""
라이브러리 검증 — 자동 갱신 뒤 반드시 통과해야 하는 기준 (DuckDB 로 Parquet 을 바로 읽어 메모리를 적게 씀)

    python _source/ops/verify.py [라이브러리 폴더] [--expect-year 2026]

1) 연도별 전국 사고건수: 축이 모두 합계인 '사고[건]' 값이 같은 장표 수 (2025년 134개, 어린이·노인 등 부분 장표는 원래 다름)
2) 부상 = 중상 + 경상 + 부상신고 (셋이 모두 있는 행)
3) 기준값: 2025 전국 사고 193,889건 (확정치로 바뀌면 경고만)
4) --expect-year: 그 연도 자료가 있는 장표 수
종료 코드 0 = 통과, 1 = 실패
"""
import argparse, json, sys
from pathlib import Path

import duckdb

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import taas_paths as TP  # noqa: E402
ROOT = TP.ROOT
BASE_2025 = 193_889
TOT = "('합계','계','전국','전체','소계','')"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("library", nargs="?", default=str(TP.LIB_OUT))
    ap.add_argument("--expect-year", type=int)
    a = ap.parse_args()
    lib = Path(a.library)
    fp = str(lib / "parquet" / "facts.parquet").replace("'", "''")
    idx = json.loads((lib / "index.json").read_text(encoding="utf-8"))
    c = duckdb.connect()
    c.execute("SET memory_limit='2GB'")
    F = f"read_parquet('{fp}')"
    fail, warn, info = [], [], {"year_min": idx["year_min"], "year_max": idx["year_max"], "n_facts": idx["n_facts"]}

    alltot = " AND ".join(f"coalesce(d{i},'') IN {TOT}" for i in range(1, 9))
    rows = c.execute(f"""
      WITH t AS (SELECT year, pid, max(value) v FROM {F} WHERE measure='사고[건]' AND pid<9000 AND {alltot} GROUP BY 1,2),
           m AS (SELECT year, mode(v) mv FROM t GROUP BY 1)
      SELECT t.year, m.mv, sum(CASE WHEN t.v=m.mv THEN 1 ELSE 0 END), sum(CASE WHEN t.v<>m.mv THEN 1 ELSE 0 END)
      FROM t JOIN m USING(year) GROUP BY 1,2 ORDER BY 1""").fetchall()
    nat = {int(y): {"total": int(v), "tables": int(n), "differ": int(d)} for y, v, n, d in rows}
    info["national"] = {y: nat[y] for y in sorted(nat)[-3:]}
    if 2025 in nat and nat[2025]["total"] != BASE_2025:
        warn.append(f"2025 전국 사고건수 {nat[2025]['total']:,}건 (기준 {BASE_2025:,}) — 확정치 반영 여부 확인")

    keys = "pid, year, " + ", ".join(f"d{i}" for i in range(1, 9))
    n, bad = c.execute(f"""
      WITH p AS (SELECT {keys},
          max(CASE WHEN measure='부상[명]' THEN value END) a, max(CASE WHEN measure='중상자[명]' THEN value END) b,
          max(CASE WHEN measure='경상자[명]' THEN value END) cc, max(CASE WHEN measure='부상신고자[명]' THEN value END) d
        FROM {F} WHERE measure IN ('부상[명]','중상자[명]','경상자[명]','부상신고자[명]') GROUP BY ALL)
      SELECT count(*), sum(CASE WHEN abs(a-b-cc-d)>0.5 THEN 1 ELSE 0 END) FROM p WHERE a IS NOT NULL AND b IS NOT NULL AND cc IS NOT NULL AND d IS NOT NULL""").fetchone()
    info["injury_rows_checked"], info["injury_mismatch"] = int(n), int(bad or 0)
    if bad:
        fail.append(f"부상 = 중상+경상+부상신고 불일치 {int(bad)}행")

    if a.expect_year:
        y = a.expect_year
        k = c.execute(f"SELECT count(DISTINCT pid) FROM {F} WHERE year={y} AND pid<9000").fetchone()[0]
        info[f"tables_with_{y}"] = int(k)
        if not k:
            fail.append(f"{y}년 자료가 있는 장표가 없습니다")
        elif y not in nat or nat[y]["tables"] < 100:  # 2025: 134개 장표가 같은 전국 합계 (어린이·노인 등 부분 장표는 원래 다름)
            warn.append(f"{y}년 전국 사고건수가 같은 장표가 {nat.get(y, {}).get('tables', 0)}개뿐 (2025년 기준 134개)")

    print(json.dumps({"ok": not fail, "fail": fail, "warn": warn, "info": info}, ensure_ascii=False, indent=1))
    sys.exit(0 if not fail else 1)


if __name__ == "__main__":
    main()
