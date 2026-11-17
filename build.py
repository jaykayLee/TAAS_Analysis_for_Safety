"""
TAAS_Analysis_for_Safety — 원본(data/raw) → 분석 라이브러리(library/) 한 번에 만들기

    python build.py                  원본이 바뀌었으면 라이브러리 전체 조립, 아니면 패널만 다시 생성
    python build.py --full           무조건 전체 조립 (약 5분, 메모리 4GB 이상 권장)
    python build.py --panel-only     패널(panel.html)만 다시 생성 (수 초 — 패널 템플릿만 바뀐 경우)
    python build.py --sample         예시 패널(일부 장표 내장, 단일 파일)도 생성 → library/panel_sample.html
    python build.py --ext            부처 자료(data/source/ext)로 부처별 원본을 다시 만든 뒤 조립 (--ext mois molit 처럼 부처 지정)
    python build.py --pop            (--ext kostat 과 같음) 통계청 인구 원본을 다시 만든 뒤 조립
    python build.py --excel 2025     해당 연도 엑셀(장표별 시트) → library/TAAS_교통사고상세통계_2025.xlsx
    python build.py --out D:\\taas   다른 폴더에 만들기 (기본: 저장소의 library/)

library/ 는 git 에 올리지 않습니다(.gitignore). git pull 뒤 이 스크립트를 실행하면 최신 상태가 됩니다.

라이브러리 구성 (부처별로 따로 조립·갱신)
    library/                 TAAS 교통사고 상세통계 (data/raw/taas)
    library/ext/<부처>/      부처별 외부 라이브러리 (data/raw/ext/<부처>) — kostat 통계청 · mois 행정안전부 · molit 국토교통부 · police 경찰청 · policy 제도 연표
    library/ext_index.json   패널이 함께 불러오는 부처 장표 목록(+ 제도 연표 events)
한 부처의 원본만 바뀌면 그 부처 라이브러리만 다시 조립합니다.
"""
import argparse, hashlib, json, shutil, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

RAW_DIRS = [ROOT / "data" / "raw" / "taas"]
EXT_RAW = ROOT / "data" / "raw" / "ext"
TEMPLATE = ROOT / "panel" / "panel_template.html"
MANIFEST = ".build_manifest.json"
REPO, BRANCH = "jaykayLee/TAAS_Analysis_for_Safety", "main"
COPY_TO_LIB = {SRC / "taas.py": "taas.py", SRC / "LIBRARY_README.md": "README.md"}


def sha(p, n=1 << 20):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while b := f.read(n):
            h.update(b)
    return h.hexdigest()[:16]


def repo_commit():
    """지금 폴더의 버전: git 저장소면 HEAD, zip 으로 받았으면 .zip_commit.json"""
    import subprocess
    if (ROOT / ".git").exists() and shutil.which("git"):
        try:
            out = subprocess.run(["git", "log", "-1", "--format=%H%n%cI%n%s"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=10).stdout.split("\n")
            if len(out) >= 2 and out[0]:
                return {"commit": out[0], "commit_date": out[1], "commit_msg": out[2] if len(out) > 2 else ""}
        except Exception:
            pass
    z = ROOT / ".zip_commit.json"
    if z.exists():
        j = json.loads(z.read_text(encoding="utf-8"))
        return {"commit": j.get("sha", ""), "commit_date": j.get("date", ""), "commit_msg": ""}
    return {"commit": "", "commit_date": "", "commit_msg": ""}


def raw_files():
    out = []
    for d in RAW_DIRS:
        out += sorted(d.glob("*.json.gz"))
    return out


def ext_libs():
    """부처별 원본: {lib: [json.gz …]}"""
    if not EXT_RAW.exists():
        return {}
    return {d.name: sorted(d.glob("*.json.gz")) for d in sorted(EXT_RAW.iterdir()) if d.is_dir() and list(d.glob("*.json.gz"))}


def data_signature(raws):
    return {"raw": {p.relative_to(ROOT).as_posix(): sha(p) for p in raws}, "build_library.py": sha(SRC / "build_library.py")}


def build_into(raws, dest, keep=()):
    """raws → dest 를 임시 폴더에서 조립한 뒤 교체. keep: 기존 dest 안에서 옮겨 둘 하위 폴더(예: ext)"""
    from build_library import build
    tmp = dest.with_name(dest.name + ".building")
    if tmp.exists():
        shutil.rmtree(tmp)
    res = build([str(p) for p in raws], tmp)
    if dest.exists():
        for k in keep:
            if (dest / k).exists():
                shutil.move(str(dest / k), str(tmp / k))
        shutil.rmtree(dest)
    tmp.rename(dest)
    return res


def write_ext_index(out, libs):
    """부처 라이브러리 목록을 하나로 — 패널이 TAAS 목록에 붙여 보여 줌"""
    cat = json.loads((ROOT / "ops" / "ext_sources.json").read_text(encoding="utf-8"))["libs"]
    pats, info = [], {}
    for lib in libs:
        f = out / "ext" / lib / "index.json"
        if not f.exists():
            continue
        idx = json.loads(f.read_text(encoding="utf-8"))
        for p in idx["patterns"]:
            p["lib"] = lib
        pats += idx["patterns"]
        info[lib] = {"name": cat.get(lib, {}).get("name", lib), "built_at": idx.get("built_at"), "n_facts": idx.get("n_facts"),
                     "year_min": idx.get("year_min"), "year_max": idx.get("year_max"), "patterns": len(idx["patterns"])}
    ev = EXT_RAW / "policy" / "events.json"
    events = json.loads(ev.read_text(encoding="utf-8"))["events"] if ev.exists() else []
    obj = {"libs": info, "patterns": sorted(pats, key=lambda p: p["pid"]), "events": events}
    (out / "ext_index.json").write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
    (out / "ext_index.js").write_text("window.TAAS_EXT=" + json.dumps(obj, ensure_ascii=False) + ";", encoding="utf-8")
    return info


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(ROOT / "library"))
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--panel-only", action="store_true")
    ap.add_argument("--sample", action="store_true")
    ap.add_argument("--pop", action="store_true")
    ap.add_argument("--ext", nargs="*", help="부처 원본 다시 만들기 (부처 이름 생략 = 전부)")
    ap.add_argument("--excel", type=int)
    a = ap.parse_args()
    out = Path(a.out).resolve()
    t0 = time.time()

    if a.pop or a.ext is not None:
        import make_ext_raw
        print("[0] 부처 원본 만들기")
        if a.ext is None:
            todo = ["kostat"]                      # --pop 만
        elif not a.ext:
            todo = []                              # --ext (전부)
        else:
            todo = list(a.ext) + (["kostat"] if a.pop and "kostat" not in a.ext else [])
        make_ext_raw.main(todo)

    raws = raw_files()
    if not raws:
        sys.exit("data/raw 에 원본(json.gz)이 없습니다.")
    sig = data_signature(raws)
    man_p = out / MANIFEST
    old = json.loads(man_p.read_text(encoding="utf-8")) if man_p.exists() else {}
    need_data = a.full or not (out / "index.json").exists() or old.get("data") != sig
    if a.panel_only:
        if not (out / "index.json").exists():
            sys.exit(f"{out} 에 라이브러리가 없습니다. 먼저 python build.py 를 실행하세요.")
        need_data = False

    if need_data:
        print(f"[1/3] TAAS 라이브러리 조립: 원본 {len(raws)}개 → {out}")
        res = build_into(raws, out, keep=("ext",))
        print(f"      장표 {res['patterns']}개 · 셀 {res['facts']:,} · {res['year_min']}~{res['year_max']} · 확인 필요 {res['n_issues']}건")
    else:
        print("[1/3] TAAS 원본 변화 없음 — 데이터 조립 생략 (전체 다시: --full)")
    # 부처별 라이브러리 (원본이 바뀐 부처만)
    libs = ext_libs(); ext_sig = {}; ext_built = dict(old.get("ext_built_at", {}))
    for lib, files in libs.items():
        ext_sig[lib] = data_signature(files)
        dest = out / "ext" / lib
        if not a.panel_only and (a.full or not (dest / "index.json").exists() or old.get("ext", {}).get(lib) != ext_sig[lib]):
            dest.parent.mkdir(parents=True, exist_ok=True)
            r = build_into(files, dest)
            ext_built[lib] = time.strftime("%Y-%m-%dT%H:%M:%S")
            print(f"      부처 {lib}: 장표 {r['patterns']}개 · 셀 {r['facts']:,} · {r['year_min']}~{r['year_max']}")
    if (out / "ext").exists():
        for d in (out / "ext").iterdir():
            if d.is_dir() and d.name not in libs:
                shutil.rmtree(d)  # 원본이 없어진 부처
    info_ext = write_ext_index(out, list(libs))
    print("      부처 라이브러리: " + (", ".join(f"{k} {v['patterns']}개" for k, v in info_ext.items()) or "없음"))

    print("[2/3] 패널 생성")
    from build_panel import main as build_panel
    for s, name in COPY_TO_LIB.items():
        if s.exists():
            shutil.copy2(s, out / name)
    info = build_panel(out, TEMPLATE, str(out / "panel_sample.html") if a.sample else None, str(out / "panel_online.html"))
    print("      ", info)

    if a.excel:
        print(f"[+] {a.excel}년 엑셀")
        import build_excel
        build_excel.build(str(out), a.excel, str(out / f"TAAS_교통사고상세통계_{a.excel}.xlsx"))

    c = repo_commit()
    built = time.strftime("%Y-%m-%dT%H:%M:%S")
    data_built = built if need_data else old.get("data_built_at", old.get("built_at", built))
    man_p.write_text(json.dumps({"data": sig, "ext": ext_sig, "ext_built_at": ext_built, "template": sha(TEMPLATE), "commit": c["commit"], "built_at": built, "data_built_at": data_built}, ensure_ascii=False, indent=1), encoding="utf-8")
    # 패널이 읽는 버전 정보 (헤더의 [업데이트] 버튼 아래 표시)
    info = {"repo": REPO, "branch": BRANCH, **c, "built_at": built, "data_built_at": data_built, "data_rebuilt": need_data, "ext_built_at": ext_built}
    (out / "build_info.json").write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "build_info.js").write_text("window.TAAS_BUILD=" + json.dumps(info, ensure_ascii=False) + ";", encoding="utf-8")
    print(f"[3/3] 완료 ({time.time() - t0:.0f}초) → {out / 'panel.html'} 를 더블클릭해서 여세요.")


if __name__ == "__main__":
    main()
