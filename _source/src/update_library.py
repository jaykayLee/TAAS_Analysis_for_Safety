"""
TAAS 라이브러리에 새 연도 수집분 통합

    python update_library.py taas_library taas_raw_2026.json.gz

1) 새 파일을 점검합니다 (장표 수, 연도, 빈 장표, 일부 항목 누락)
2) 라이브러리의 raw/ 에 보관된 기존 수집분 + 새 파일로 라이브러리를 다시 조립합니다
   - 같은 장표·구간이 겹치면 더 늦게 수집한 것을 사용 (예: 2025년 확정치 재수집)
   - 연도마다 축 이름이 달라도 이름 기준으로 맞춤, coverage.json 재계산
3) 기존 폴더는 taas_library.bak_<시각> 으로 남기고 새 폴더로 교체합니다
"""
import gzip, json, shutil, sys, time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_library import build  # noqa: E402

KEEP = ["panel.html", "taas.py", "README.md", "build_library.py", "update_library.py", "taas_collector.js"]


def inspect(path):
    j = json.load(gzip.open(path, "rt", encoding="utf-8"))
    recs = j["recs"]
    years = Counter()
    for r in recs:
        a, _, b = r["label"].partition("-")
        if a.isdigit():
            for y in range(int(a), int(b or a) + 1):
                years[y] += 1
    return {"file": Path(path).name, "exported": j.get("exported"), "records": len(recs),
            "patterns": len({r["pid"] for r in recs}), "years": dict(sorted(years.items())),
            "empty": sum(1 for r in recs if not r["rows"]),
            "partial_measures": sum(1 for r in recs if r.get("meaMissing"))}


def main(lib, *new_files):
    lib = Path(lib).resolve()
    if not (lib / "raw").is_dir():
        sys.exit(f"{lib}/raw 폴더가 없습니다. 이 라이브러리는 원본 보관 이전 버전이라 전체 수집 파일로 다시 만들어야 합니다.")
    before = json.loads((lib / "index.json").read_text(encoding="utf-8"))
    print("기존 라이브러리:", before["year_min"], "~", before["year_max"], f"셀 {before['n_facts']:,}")
    for f in new_files:
        print("새 수집 파일:", json.dumps(inspect(f), ensure_ascii=False))

    old_raws = sorted((lib / "raw").glob("*.json.gz"))
    tmp = lib.with_name(lib.name + ".new")
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir()
    (tmp / "raw").mkdir()
    for f in old_raws:
        shutil.copy2(f, tmp / "raw" / f.name)
    for f in new_files:
        dst = tmp / "raw" / Path(f).name
        if dst.exists():  # 같은 이름이면 덮지 않고 시각을 붙여 보관
            dst = dst.with_name(dst.name.replace(".json.gz", time.strftime("_%Y%m%d%H%M%S.json.gz")))
        shutil.copy2(f, dst)
    raws = sorted((tmp / "raw").glob("*.json.gz"), key=lambda p: p.stat().st_mtime)
    res = build([str(p) for p in raws], tmp)
    for k in KEEP:
        if (lib / k).exists():
            shutil.copy2(lib / k, tmp / k)

    bak = lib.with_name(lib.name + time.strftime(".bak_%Y%m%d_%H%M%S"))
    lib.rename(bak)
    tmp.rename(lib)
    print("통합 완료:", res["year_min"], "~", res["year_max"], f"셀 {res['facts']:,}", f"(이전 폴더: {bak.name})")
    if res["n_issues"]:
        print("확인 필요:", res["n_issues"], "건 — coverage.json 참고")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    main(sys.argv[1], *sys.argv[2:])
