"""
자동 갱신 상태 점검 — 저장소 원본의 최신 연도와 커밋을 JSON 으로 출력

    python ops/status.py              → {"raw_max_year": 2025, "raw_files": [...], "head": "...", ...}
    python ops/status.py --latest 2026  → TAAS 최신 연도를 넣으면 "need_collect": true/false 와 수집 대상 연도
"""
import argparse, gzip, json, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def raw_years():
    ys, files = set(), []
    for p in sorted((ROOT / "data" / "raw" / "taas").glob("*.json.gz")):
        files.append(p.name)
        with gzip.open(p, "rt", encoding="utf-8") as f:
            j = json.load(f)
        for r in j["recs"]:
            a, _, b = r["label"].partition("-")
            if a.isdigit() and r.get("rows"):
                ys.add(int(b or a))
    return ys, files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--latest", type=int, help="TAAS 에 공개된 최신 연도 (TAASU.check() 의 latest)")
    a = ap.parse_args()
    ys, files = raw_years()
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    out = {"raw_max_year": max(ys) if ys else None, "raw_years": sorted(ys), "raw_files": files, "head": head}
    if a.latest:
        out["need_collect"] = a.latest > (out["raw_max_year"] or 0)
        out["collect_years"] = list(range((out["raw_max_year"] or a.latest - 1) + 1, a.latest + 1)) if out["need_collect"] else []
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
