"""
TAAS_Analysis_for_Safety — 원본(data/raw) → 분석 라이브러리(library/) 한 번에 만들기

    python build.py                  원본이 바뀌었으면 라이브러리 전체 조립, 아니면 패널만 다시 생성
    python build.py --full           무조건 전체 조립 (약 5분, 메모리 4GB 이상 권장)
    python build.py --panel-only     패널(panel.html)만 다시 생성 (수 초 — 패널 템플릿만 바뀐 경우)
    python build.py --sample         예시 패널(일부 장표 내장, 단일 파일)도 생성 → library/panel_sample.html
    python build.py --pop            통계청 원본(data/source/kosis/*.xlsx)으로 인구 원본을 다시 만든 뒤 조립
    python build.py --excel 2025     해당 연도 엑셀(장표별 시트) → library/TAAS_교통사고상세통계_2025.xlsx
    python build.py --out D:\\taas   다른 폴더에 만들기 (기본: 저장소의 library/)

library/ 는 git 에 올리지 않습니다(.gitignore). git pull 뒤 이 스크립트를 실행하면 최신 상태가 됩니다.
"""
import argparse, hashlib, json, shutil, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

RAW_DIRS = [ROOT / "data" / "raw" / "taas", ROOT / "data" / "raw" / "population"]
TEMPLATE = ROOT / "panel" / "panel_template.html"
MANIFEST = ".build_manifest.json"
COPY_TO_LIB = {SRC / "taas.py": "taas.py", SRC / "LIBRARY_README.md": "README.md"}


def sha(p, n=1 << 20):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while b := f.read(n):
            h.update(b)
    return h.hexdigest()[:16]


def raw_files():
    out = []
    for d in RAW_DIRS:
        out += sorted(d.glob("*.json.gz"))
    return out


def data_signature(raws):
    return {"raw": {p.relative_to(ROOT).as_posix(): sha(p) for p in raws}, "build_library.py": sha(SRC / "build_library.py")}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(ROOT / "library"))
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--panel-only", action="store_true")
    ap.add_argument("--sample", action="store_true")
    ap.add_argument("--pop", action="store_true")
    ap.add_argument("--excel", type=int)
    a = ap.parse_args()
    out = Path(a.out).resolve()
    t0 = time.time()

    if a.pop:
        import make_pop_raw
        src = sorted((ROOT / "data" / "source" / "kosis").glob("*.xlsx"))
        old = [p for p in src if "2005" in p.name and "2010" in p.name]
        new = [p for p in src if "2015" in p.name]
        if not old or not new:
            sys.exit("data/source/kosis 에 2005_2010, 2015_2025 원본 엑셀이 필요합니다.")
        make_pop_raw.main(str(old[0]), str(new[0]), str(ROOT / "data" / "raw" / "population" / "taas_raw_population_kosis.json.gz"))

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
        print(f"[1/3] 라이브러리 조립: 원본 {len(raws)}개 → {out}")
        from build_library import build
        tmp = out.with_name(out.name + ".building")
        if tmp.exists():
            shutil.rmtree(tmp)
        res = build([str(p) for p in raws], tmp)
        if out.exists():
            shutil.rmtree(out)
        tmp.rename(out)
        print(f"      장표 {res['patterns']}개 · 셀 {res['facts']:,} · {res['year_min']}~{res['year_max']} · 확인 필요 {res['n_issues']}건")
    else:
        print("[1/3] 원본 변화 없음 — 데이터 조립 생략 (전체 다시: --full)")

    print("[2/3] 패널 생성")
    from build_panel import main as build_panel
    for s, name in COPY_TO_LIB.items():
        if s.exists():
            shutil.copy2(s, out / name)
    info = build_panel(out, TEMPLATE, str(out / "panel_sample.html") if a.sample else None)
    print("      ", info)

    if a.excel:
        print(f"[+] {a.excel}년 엑셀")
        import build_excel
        build_excel.build(str(out), a.excel, str(out / f"TAAS_교통사고상세통계_{a.excel}.xlsx"))

    git = ""
    try:
        head = (ROOT / ".git" / "HEAD").read_text().strip()
        ref = ROOT / ".git" / head[5:] if head.startswith("ref: ") else None
        git = (ref.read_text().strip() if ref and ref.exists() else head)[:10]
    except OSError:
        pass
    man_p.write_text(json.dumps({"data": sig, "template": sha(TEMPLATE), "commit": git, "built_at": time.strftime("%Y-%m-%dT%H:%M:%S")}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[3/3] 완료 ({time.time() - t0:.0f}초) → {out / 'panel.html'} 를 더블클릭해서 여세요.")


if __name__ == "__main__":
    main()
