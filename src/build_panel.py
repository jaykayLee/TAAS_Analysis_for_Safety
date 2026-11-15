"""
패널 HTML 생성
usage: python build_panel.py <library_dir> <template.html> [sample_out.html]
 - <library_dir>/panel.html : 라이브러리 폴더에서 더블클릭으로 여는 패널 (index.js, panel_js/ 사용)
 - sample_out.html          : 예시 장표를 내장한 단독 패널 (아티팩트 게시용)
"""
import gzip, json, re, sys
from pathlib import Path

SAMPLE_PIDS = [7019, 7300, 1, 9001, 9002, 7196, 7240, 7092, 7066, 7051, 7160, 7110, 7097, 7089, 7269, 7210, 7030, 7086, 4]


def main(lib, tpl, sample_out=None):
    lib = Path(lib); html = Path(tpl).read_text(encoding="utf-8")
    (lib / "panel.html").write_text(html.replace("/*__SAMPLE__*/", ""), encoding="utf-8")
    idx = json.loads((lib / "index.json").read_text(encoding="utf-8"))
    # 차량기술 카드 장표명 점검
    names = {p["name"] for p in idx["patterns"]}
    tech = re.findall(r"\{t:'[^']+',std:.*?name:'([^']+)'", html)
    missing = [t for t in tech if t not in names and not any(t.replace(" ", "") in n.replace(" ", "") for n in names)]
    if sample_out:
        files = {}
        for pid in SAMPLE_PIDS:
            f = lib / "panel" / f"p{pid}.json.gz"
            if f.exists():
                files[pid] = json.loads(gzip.open(f, "rt", encoding="utf-8").read())
        sidx = dict(idx); sidx["patterns"] = idx["patterns"]  # 목록은 전체, 데이터는 일부
        sidx["n_facts"] = sum(len(o["v"]) for o in files.values())
        sample = "window.TAAS_SAMPLE=" + json.dumps({"index": sidx, "files": files}, ensure_ascii=False, separators=(",", ":")) + ";"
        Path(sample_out).write_text(html.replace("/*__SAMPLE__*/", sample).replace('<script src="index.js" onerror="void 0"></script>', ""), encoding="utf-8")
    return {"tech_cards": len(tech), "tech_missing": missing, "sample_bytes": Path(sample_out).stat().st_size if sample_out else 0}


if __name__ == "__main__":
    print(main(*sys.argv[1:]))
