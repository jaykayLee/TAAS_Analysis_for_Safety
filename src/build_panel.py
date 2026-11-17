"""
패널 HTML 생성
usage: python build_panel.py <library_dir> <template.html> [sample_out.html]
 - <library_dir>/panel.html : 라이브러리 폴더에서 더블클릭으로 여는 패널 (index.js, panel_js/ 사용)
 - sample_out.html          : 예시 장표를 내장한 단독 패널 (아티팩트 게시용)
"""
import base64, gzip, json, re, sys
from pathlib import Path

SAMPLE_PIDS = [7019, 7300, 1, 9001, 9002, 7196, 7240, 7092, 7066, 7051, 7160, 7110, 7097, 7089, 7269, 7210, 7030, 7086, 4, 9102, 9201, 9301, 9901]


def panel_files(lib):
    """TAAS(panel/) + 부처 라이브러리(ext/<부처>/panel/)의 장표 파일 {pid: path}"""
    out = {}
    for f in list((lib / "panel").glob("p*.json.gz")) + list((lib / "ext").glob("*/panel/p*.json.gz")):
        out[int(f.name.split(".")[0][1:])] = f
    return out


def auto_config(tpl):
    """ops/auto_update.json + Claude 앱 프롬프트 → 패널의 window.TAAS_AUTO (갱신 버튼·프롬프트용)"""
    ops = Path(tpl).resolve().parent.parent / "ops"
    f = ops / "auto_update.json"
    if not f.exists():
        return ""
    cfg = json.loads(f.read_text(encoding="utf-8"))
    pr = ops / "APP_PROMPT.md"
    if pr.exists():
        cfg["app_prompt"] = pr.read_text(encoding="utf-8").replace("{artifact_url}", cfg.get("artifact_url", "")).strip()
    pe = ops / "APP_PROMPT_EXT.md"
    if pe.exists():
        cfg["ext_app_prompt"] = pe.read_text(encoding="utf-8").replace("{artifact_url}", cfg.get("artifact_url", "")).strip()
    src = ops / "ext_sources.json"
    if src.exists():
        cfg["ext_libs"] = {k: {"name": v["name"]} for k, v in json.loads(src.read_text(encoding="utf-8"))["libs"].items()}
    cfg.pop("kosis_api_key", None)  # 혹시 넣어 둔 키는 패널에 싣지 않음
    return "window.TAAS_AUTO=" + json.dumps(cfg, ensure_ascii=False) + ";"


def write_online_packs(lib, target=1_200_000):
    """게시용 데이터 묶음: panel/p*.json.gz 를 약 1.2MB(gzip) 단위 묶음 online/pack_NN.txt(gzip→base64)로 합침 → 게시 파일 수를 20개 안팎으로"""
    out = lib / "online"
    if out.exists():
        for f in list(out.glob("pack_*.json.gz")) + list(out.glob("pack_*.txt")):
            f.unlink()
    out.mkdir(exist_ok=True)
    files = [f for _, f in sorted(panel_files(lib).items())]
    where, cur, size, n = {}, {}, 0, 0

    def flush():
        nonlocal cur, size, n
        if not cur:
            return
        name = f"pack_{n:02d}"
        # 아티팩트는 .gz 를 서비스하지 않으므로 gzip 을 base64 텍스트(.txt)로 게시 — 패널이 받아 풂
        raw = gzip.compress(json.dumps(cur, ensure_ascii=False, separators=(",", ":")).encode("utf-8"), compresslevel=6)
        (out / f"{name}.txt").write_bytes(base64.b64encode(raw))
        for pid in cur:
            where[pid] = name
        cur, size, n = {}, 0, n + 1

    for f in files:
        pid = f.name.split(".")[0][1:]
        cur[pid] = json.loads(gzip.open(f, "rt", encoding="utf-8").read())
        size += f.stat().st_size
        if size >= target:
            flush()
    flush()
    (out / "packs.json").write_text(json.dumps(where, separators=(",", ":")), encoding="utf-8")
    return n


def main(lib, tpl, sample_out=None, online_out=None):
    lib = Path(lib); html = Path(tpl).read_text(encoding="utf-8")
    auto = auto_config(tpl)
    html = html.replace("/*__SAMPLE__*/", auto + "/*__SAMPLE__*/")
    (lib / "panel.html").write_text(html.replace("/*__SAMPLE__*/", ""), encoding="utf-8")
    if online_out:  # claude.ai 게시용: index.json·online/packs.json·online/pack_*.txt 를 같은 위치에서 받아 씀 (index.js·panel_js 불필요)
        man = lib / "online" / "packs.json"
        newest = max(f.stat().st_mtime for f in panel_files(lib).values())
        if not man.exists() or man.stat().st_mtime < newest:
            write_online_packs(lib)
        Path(online_out).write_text(html.replace("/*__SAMPLE__*/", "window.TAAS_ONLINE=1;").replace('<script src="index.js" onerror="void 0"></script>', "").replace('<script src="ext_index.js" onerror="void 0"></script>', ""), encoding="utf-8")
    idx = json.loads((lib / "index.json").read_text(encoding="utf-8"))
    ext = json.loads((lib / "ext_index.json").read_text(encoding="utf-8")) if (lib / "ext_index.json").exists() else {"patterns": [], "libs": {}, "events": []}
    # 차량기술 카드 장표명 점검
    names = {p["name"] for p in idx["patterns"] + ext["patterns"]}
    tech = re.findall(r"\{t:'[^']+',std:.*?name:'([^']+)'", html)
    missing = [t for t in tech if t not in names and not any(t.replace(" ", "") in n.replace(" ", "") for n in names)]
    if sample_out:
        files = {}
        pf = panel_files(lib)
        for pid in SAMPLE_PIDS:
            if pid in pf:
                files[pid] = json.loads(gzip.open(pf[pid], "rt", encoding="utf-8").read())
        sidx = dict(idx); sidx["patterns"] = idx["patterns"]  # 목록은 전체, 데이터는 일부
        sidx["n_facts"] = sum(len(o["v"]) for o in files.values())
        sample = "window.TAAS_SAMPLE=" + json.dumps({"index": sidx, "ext": ext, "files": files}, ensure_ascii=False, separators=(",", ":")) + ";"
        Path(sample_out).write_text(html.replace("/*__SAMPLE__*/", sample).replace('<script src="index.js" onerror="void 0"></script>', "").replace('<script src="ext_index.js" onerror="void 0"></script>', ""), encoding="utf-8")
    return {"tech_cards": len(tech), "tech_missing": missing, "sample_bytes": Path(sample_out).stat().st_size if sample_out else 0}


if __name__ == "__main__":
    print(main(*sys.argv[1:]))
