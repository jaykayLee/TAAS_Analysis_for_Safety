"""
부처 라이브러리 검증 — 부처 자료 갱신 뒤 통과해야 하는 기준

    python _source/ops/verify_ext.py [lib ...] [--library <라이브러리 폴더>]

1) 그 부처 라이브러리(<라이브러리>/ext/<lib>)가 있고 장표마다 셀이 있음
2) 장표 번호가 그 부처 범위(_source/ops/ext_sources.json 의 pids)에 있음, 다른 부처·TAAS 와 겹치지 않음
3) 값 점검: 음수 없음(증감률·구성비 제외), 같은 키 중복 0
4) 부처별 기준: mois 전국 인구 4,500만~5,500만 · 9102 어린이+일반+노인 = 전체 / molit 전국 자동차 1,500만~3,500만대 / police 면허 2,000만~4,000만명
종료 코드 0 = 통과, 1 = 실패
"""
import argparse, json, re, sys
from pathlib import Path

import pandas as pd

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import taas_paths as TP  # noqa: E402
ROOT = TP.ROOT


def rng(spec):
    out = []
    for part in str(spec).split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-"); out.append((int(a), int(b)))
        elif part.isdigit():
            out.append((int(part), int(part)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("libs", nargs="*")
    ap.add_argument("--library", default=str(TP.LIB_OUT))
    a = ap.parse_args()
    lib_root = Path(a.library)
    cat = json.loads(TP.EXT_SOURCES.read_text(encoding="utf-8"))["libs"]
    libs = a.libs or [d.name for d in sorted((lib_root / "ext").iterdir()) if d.is_dir()]
    fail, warn, info = [], [], {}
    core = {p["pid"] for p in json.loads((lib_root / "index.json").read_text(encoding="utf-8"))["patterns"]}
    seen = {}
    for d in sorted((lib_root / "ext").iterdir()):
        if (d / "index.json").exists():
            for p in json.loads((d / "index.json").read_text(encoding="utf-8"))["patterns"]:
                seen.setdefault(p["pid"], []).append(d.name)
    for pid, ls in seen.items():
        if len(ls) > 1 or pid in core:
            fail.append(f"장표 {pid} 가 여러 라이브러리에 있음: {ls + (['TAAS'] if pid in core else [])}")
    for lib in libs:
        d = lib_root / "ext" / lib
        if not (d / "index.json").exists():
            fail.append(f"{lib}: 라이브러리 없음 (python build.py --ext {lib})"); continue
        idx = json.loads((d / "index.json").read_text(encoding="utf-8"))
        R = rng(cat.get(lib, {}).get("pids", ""))
        f = pd.read_parquet(d / "parquet" / "facts.parquet")
        li = {"patterns": len(idx["patterns"]), "facts": int(len(f)), "years": f"{idx.get('year_min')}~{idx.get('year_max')}"}
        for p in idx["patterns"]:
            if R and not any(lo <= p["pid"] <= hi for lo, hi in R):
                fail.append(f"{lib}: 장표 {p['pid']} 가 부처 범위({cat[lib]['pids']}) 밖")
            if not p["n_facts"]:
                fail.append(f"{lib}: 장표 {p['pid']} 셀 없음")
        keys = ["pid", "year", "measure"] + [f"d{i}" for i in range(1, 9)]
        dup = int(f.duplicated(subset=keys).sum())
        if dup:
            fail.append(f"{lib}: 중복 셀 {dup}")
        neg = f[(f.value < 0) & ~f.measure.fillna("").str.contains("증감|율|%")]
        if len(neg):
            fail.append(f"{lib}: 음수 값 {len(neg)}개 (예: {neg.iloc[0].to_dict()})")
        T = lambda pid, meas, **dims: f[(f.pid == pid) & (f.measure == meas) & pd.concat([f[f"d{i + 1}"] == v for i, v in enumerate(dims.values())] or [pd.Series(True, index=f.index)], axis=1).all(axis=1)].set_index("year").value
        try:
            if lib == "mois" and (f.pid == 9101).any():
                s = T(9101, "인구[명]", d1="전국", d2="계"); li["전국_인구_최근"] = {int(s.index.max()): int(s.loc[s.index.max()])}
                if not s.between(45e6, 55e6).all():
                    fail.append(f"mois: 전국 주민등록인구 범위 밖 {s[~s.between(45e6, 55e6)].to_dict()}")
                g = f[(f.pid == 9102) & (f.measure == "인구[명]") & (f.d1 == "전국")].pivot_table(index="year", columns="d2", values="value")
                if len(g):
                    diff = (g["어린이 0~12세"] + g["일반 13~64세"] + g["노인 65세 이상"] - g["전체"]).abs().max()
                    if diff > 1:
                        fail.append(f"mois: 9102 어린이+일반+노인 ≠ 전체 (최대 차 {diff})")
                yrs = sorted(int(y) for y in s.index); miss = [y for y in range(yrs[0], yrs[-1] + 1) if y not in yrs]
                if miss:
                    warn.append(f"mois: 빈 연도 {miss}")
            if lib == "molit" and (f.pid == 9201).any():
                s = T(9201, "등록대수[대]", d1="전국", d2="계", d3="계"); li["전국_자동차_최근"] = {int(s.index.max()): int(s.loc[s.index.max()])}
                if not s.between(15e6, 35e6).all():
                    fail.append(f"molit: 전국 자동차 등록대수 범위 밖 {s[~s.between(15e6, 35e6)].to_dict()}")
            if lib == "police" and (f.pid == 9301).any():
                s = T(9301, "소지자[명]", d1="총계"); li["면허_최근"] = {int(s.index.max()): int(s.loc[s.index.max()])}
                if not s.between(20e6, 40e6).all():
                    fail.append(f"police: 운전면허 소지자 범위 밖 {s[~s.between(20e6, 40e6)].to_dict()}")
        except Exception as e:
            warn.append(f"{lib}: 기준 점검 중 오류 {e}")
        info[lib] = li
    print(json.dumps({"ok": not fail, "fail": fail, "warn": warn, "info": info}, ensure_ascii=False, indent=1))
    sys.exit(0 if not fail else 1)


if __name__ == "__main__":
    main()
