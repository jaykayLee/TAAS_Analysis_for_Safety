"""
패널 아티팩트 게시 계획 — 온라인 패널(library/panel_online.html)과 데이터 파일을 Artifact 도구 한도(한 번에 255개)에 맞게 나눔

    python ops/publish_plan.py      → ops/_publish_1.json, ops/_publish_2.json … (각각 Artifact 도구의 files 값)

게시 순서 (ops/AUTO_UPDATE.md 4단계):
  1) Artifact read  url=<artifact_url>
  2) Artifact publish url=<artifact_url> file_path=library/panel_online.html files=<_publish_1.json 내용>   (capabilities 는 넘기지 않음)
  3) Artifact publish url=<artifact_url> file_path=library/panel_online.html files=<_publish_2.json 내용>   (같은 페이지, 나머지 파일 추가)
파일 경로는 저장소 최상위 기준입니다. 이전 게시에 있던 파일은 그대로 남고 같은 경로는 교체됩니다.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "library"
PER = 240


def main():
    if not (LIB / "panel_online.html").exists():
        raise SystemExit("library/panel_online.html 이 없습니다. python build.py 를 먼저 실행하세요.")
    files = {}
    for name in ["index.json", "build_info.js", "build_info.json"]:
        files[name] = f"library/{name}"
    for p in sorted((LIB / "panel").glob("p*.json.gz")):
        files[f"panel/{p.name}"] = {"from": f"library/panel/{p.name}", "contentType": "application/gzip"}
    items = list(files.items())
    out = []
    for i in range(0, len(items), PER):
        part = dict(items[i:i + PER])
        f = ROOT / "ops" / f"_publish_{len(out) + 1}.json"
        f.write_text(json.dumps(part, ensure_ascii=False, indent=0), encoding="utf-8")
        out.append({"file": f.relative_to(ROOT).as_posix(), "files": len(part)})
    total = sum((LIB / (v if isinstance(v, str) else v["from"])[len("library/"):]).stat().st_size for v in files.values())
    print(json.dumps({"page": "library/panel_online.html", "batches": out, "total_files": len(files), "total_MB": round(total / 1e6, 1)}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
