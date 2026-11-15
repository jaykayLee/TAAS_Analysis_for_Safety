"""
TAAS 교통사고 상세통계 라이브러리 빌더

입력 : taas_raw_*.json.gz  (브라우저 수집기가 내보낸 원본 장표)
출력 : taas_library.sqlite  (분석 패널·Python 공용, 단일 파일)
       taas_facts.parquet   (pandas/polars 고속 로딩용)
       taas_patterns.parquet

정규화 규칙
- 장표 1셀 = facts 1행 (pid, year, measure, d1..d8, value)
- 연도 축은 행/열 어디에 있든 자동 탐지 → year 컬럼으로 분리
- 연도 '합계'(조회 구간 합) 셀은 구간 분할에 따라 달라지므로 제외
- 행 머리글 '구분'(사고[건]/사망[명] …)은 measure 컬럼으로 분리
- 나머지 축은 d1..d8 에 순서대로, 축 이름은 patterns.dim_names(JSON) 에 기록
"""
import gzip, json, re, shutil, sys
from pathlib import Path

import pandas as pd

YEAR_NAMES = {"연도", "년도", "기준년도", "기준연도"}
MEASURE_NAMES = {"구분"}
YEAR_RE = re.compile(r"^(19|20)\d{2}$")
MAX_DIMS = 8


def to_num(s):
    if s is None:
        return None
    s = str(s).strip().replace(",", "")
    if s in ("", "-", "−"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def clean_measure(m):
    # "(중상자[명])" -> "중상자[명]"
    return m.strip().strip("()").strip() if m else m


def level_names(names, width, prefix):
    names = list(names or [])
    out = []
    for i in range(width):
        out.append(names[i] if i < len(names) and names[i] else f"{prefix}{i+1}")
    return out


def find_year_level(names, matrix):
    """matrix: list of value-lists for each level (column-major). returns index or None"""
    for i, n in enumerate(names):
        if n in YEAR_NAMES:
            return i
    for i, vals in enumerate(matrix):
        v = [x for x in vals if x not in ("합계", "계", "")]
        if v and all(YEAR_RE.match(x) for x in v):
            return i
    return None


def record_to_rows(rec):
    rows, cols, data = rec["rows"], rec["cols"], rec["data"]
    if not rows or not cols or not data:
        return [], {}
    rw = max(len(r) for r in rows)
    cw = max(len(c) for c in cols)
    rnames = level_names(rec.get("lab"), rw, "행")
    # 행 라벨 목록에 '구분'이 마지막에 오는 형태가 대부분
    cnames = level_names(rec.get("colDims"), cw, "열")
    # 열 머리글 단계가 colDims 보다 많으면(예: 지표/지수) 나머지는 '세부'
    if rec.get("colDims") and cw > len(rec["colDims"]):
        cnames = list(rec["colDims"]) + [f"세부{i+1}" for i in range(cw - len(rec["colDims"]))]

    rmat = [[r[i] if i < len(r) else "" for r in rows] for i in range(rw)]
    cmat = [[c[i] if i < len(c) else "" for c in cols] for i in range(cw)]
    y_row = find_year_level(rnames, rmat)
    y_col = None if y_row is not None else find_year_level(cnames, cmat)
    m_row = next((i for i, n in enumerate(rnames) if n in MEASURE_NAMES), None)

    dim_names = [n for i, n in enumerate(rnames) if i not in (y_row, m_row)] + \
                [n for i, n in enumerate(cnames) if i != y_col]
    dim_names = dim_names[:MAX_DIMS]

    # 같은 행 머리글이 다시 나올 때: 값이 있는 열이 겹치면 이름만 같은 별개 행(예: 2010년 통합 전·후 '창원시') → " (2)" 를 붙여 구분.
    # 겹치지 않으면 열 블록 페이지로 나뉜 같은 행이므로 그대로 둠.
    inner = max((i for i in range(rw) if i not in (y_row, m_row)), default=None)
    seen_cols, renamed = {}, {}
    for ri, r in enumerate(rows[:len(data)]):
        key = tuple(r)
        nz = {ci for ci, v in enumerate(data[ri]) if v != ""}
        prev = seen_cols.setdefault(key, [])
        k = next((n for n, s in enumerate(prev) if not (s & nz)), None)
        if k is None:
            prev.append(set(nz)); k = len(prev) - 1
        else:
            prev[k] |= nz
        if k and inner is not None:
            renamed[ri] = k + 1

    out = []
    for ri, r in enumerate(rows):
        if ri >= len(data):
            break
        r = list(r) + [""] * (rw - len(r))
        if ri in renamed:
            r[inner] = f"{r[inner]} ({renamed[ri]})"
        yr_r = r[y_row] if y_row is not None else None
        if yr_r is not None and not YEAR_RE.match(yr_r):
            continue  # 연도 합계 행
        meas = clean_measure(r[m_row]) if m_row is not None else None
        rdims = [v for i, v in enumerate(r) if i not in (y_row, m_row)]
        drow = data[ri]
        for ci, c in enumerate(cols):
            if ci >= len(drow):
                break
            if drow[ci] == "":
                continue  # 열 방향 페이지 나눔으로 다른 페이지에 값이 있는 칸 (수집기가 빈 문자열로 채움)
            c = list(c) + [""] * (cw - len(c))
            yr = yr_r
            if y_col is not None:
                yr = c[y_col]
                if not YEAR_RE.match(yr):
                    continue  # 연도 합계 열
            cdims = [v for i, v in enumerate(c) if i != y_col]
            dims = (rdims + cdims)[:MAX_DIMS]
            out.append((int(yr) if yr else None, meas, dims, to_num(drow[ci]), drow[ci]))
    info = {"dim_names": dim_names, "row_levels": rnames, "col_levels": cnames,
            "year_axis": "row" if y_row is not None else ("col" if y_col is not None else None),
            "has_measure": m_row is not None}
    return out, info


PANEL_MAX_FACTS = 1_500_000   # 패널(브라우저)용 파일 한도 — 넘는 장표는 최근 연도부터 이 한도까지만 패널에 넣음 (Parquet 은 전체)


def _winner(old, r):
    """같은 장표·구간이 여러 파일에 있으면 더 늦게 수집한 것 (빈 결과는 실데이터를 덮지 않음)"""
    if old is None:
        return True
    if not old["has_rows"] and r["has_rows"]:
        return True
    return r["ts"] >= old["ts"] and (r["has_rows"] or not old["has_rows"])


def load_raw(paths, tmp):
    """원본을 한 파일씩 읽어 레코드를 임시 폴더에 하나씩 풀어 둠(메모리 절약). 반환: meta, {key: 위치정보}"""
    meta, pick = {}, {}
    tmp.mkdir(parents=True, exist_ok=True)
    n = 0
    for fi, p in enumerate(paths):
        with gzip.open(p, "rt", encoding="utf-8") as f:
            j = json.load(f)
        for m in j["meta"]:
            meta[str(m["pid"])] = m
        for r in j["recs"]:
            n += 1
            info = {"ts": r.get("ts", 0), "has_rows": bool(r.get("rows")), "file": tmp / f"r{n}.json", "pid": str(r["pid"]), "label": r["label"]}
            if _winner(pick.get(r["key"]), info):
                info["file"].write_text(json.dumps(r, ensure_ascii=False), encoding="utf-8")
                old = pick.get(r["key"])
                if old:
                    old["file"].unlink(missing_ok=True)
                pick[r["key"]] = info
        del j
    return meta, pick


def build(raw_paths, out_dir):
    import pyarrow as pa
    import pyarrow.parquet as papq

    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    tmp = out_dir / "_tmp_recs"
    if tmp.exists():
        shutil.rmtree(tmp)
    meta, pick = load_raw(raw_paths, tmp)
    by_pid = {}
    for key, inf in pick.items():
        by_pid.setdefault(inf["pid"], []).append((key, inf))

    dcols = [f"d{i+1}" for i in range(MAX_DIMS)]
    cols = ["pid", "year", "measure"] + dcols + ["value", "raw"]
    schema = pa.schema([("pid", pa.int32()), ("year", pa.int32()), ("measure", pa.string())] +
                       [(c, pa.string()) for c in dcols] + [("value", pa.float64()), ("raw", pa.string())])
    pq = out_dir / "parquet"; pq.mkdir(exist_ok=True)
    pn = out_dir / "panel"; pn.mkdir(exist_ok=True)
    pj = out_dir / "panel_js"; pj.mkdir(exist_ok=True)
    writer = papq.ParquetWriter(pq / "facts.parquet", schema, compression="zstd")

    pinfo, coverage, issues, stats = {}, {}, [], {}
    total, dup_total, ymin, ymax = 0, 0, None, None
    for pid in sorted(by_pid, key=int):
        items = by_pid[pid]
        cov = coverage.setdefault(pid, {"chunks": {}, "dim_variants": []})
        # 최근 구간부터 (축 기준 = 가장 최근 구간, 과거에만 있는 축은 뒤에 추가)
        items.sort(key=lambda t: t[1]["label"], reverse=True)
        canon, variants, notes, base = None, set(), set(), None
        st = {"n": 0, "measures": set(), "ymin": None, "ymax": None, "measure_years": {}}
        panel_parts, panel_n, panel_years, n_data = [], 0, [], 0
        for key, inf in items:
            rec = json.loads(inf["file"].read_text(encoding="utf-8"))
            rows, info = record_to_rows(rec)
            cst = {"status": "ok", "cells": len(rows)}
            if not rows:
                cst = {"status": "empty", "msg": " ".join(rec.get("msg") or [])[:200]}
                issues.append((key, "empty"))
            elif rec.get("meaMissing"):
                cst["status"] = "partial_measures"; cst["missing"] = rec["meaMissing"]
            if rec.get("dimMissing"):
                cst["dim_missing"] = rec["dimMissing"]
            cov["chunks"][rec["label"]] = cst
            for n in rec.get("msg") or []:
                notes.add(n)
            if not rows:
                continue
            n_data += 1
            if canon is None:
                base = info; canon = list(info["dim_names"])[:MAX_DIMS]
            for n in info["dim_names"]:
                if n not in canon and len(canon) < MAX_DIMS:
                    canon.append(n)
            variants.add(tuple(info["dim_names"]))
            seen, pos = {}, []
            for n in info["dim_names"]:
                k = seen.get(n, 0); seen[n] = k + 1
                idxs = [i for i, c in enumerate(canon) if c == n]
                pos.append(idxs[k] if k < len(idxs) else None)
            recs_out = []
            for yr, meas, dims, val, raw in rows:
                d = [None] * MAX_DIMS
                for j, v in enumerate(dims):
                    if j < len(pos) and pos[j] is not None:
                        d[pos[j]] = v
                recs_out.append((int(pid), yr, meas, *d, val, raw))
            del rows
            df = pd.DataFrame(recs_out, columns=cols); del recs_out
            before = len(df)
            df = df.drop_duplicates(subset=cols[:-2], keep="last").reset_index(drop=True)
            dup_total += before - len(df)
            df["year"] = df["year"].astype("Int32")
            writer.write_table(pa.Table.from_pandas(df, schema=schema, preserve_index=False))
            # 통계
            st["n"] += len(df); total += len(df)
            st["measures"] |= set(df.measure.dropna().unique())
            yrs = df.year.dropna()
            if len(yrs):
                a, b = int(yrs.min()), int(yrs.max())
                st["ymin"] = a if st["ymin"] is None else min(st["ymin"], a)
                st["ymax"] = b if st["ymax"] is None else max(st["ymax"], b)
                ymin = a if ymin is None else min(ymin, a); ymax = b if ymax is None else max(ymax, b)
            vv = df.dropna(subset=["value"])
            for m, g in vv.groupby(vv.measure.fillna("값")):
                st["measure_years"].setdefault(m, set()).update(int(x) for x in g.year.dropna().unique())
            # 패널용 (최근 구간부터 한도까지)
            if panel_n + len(df) <= PANEL_MAX_FACTS or not panel_parts:
                panel_parts.append(df); panel_n += len(df)
                panel_years.append(rec["label"])
            del df
        if len(variants) > 1:
            cov["dim_variants"] = [list(v) for v in variants]
            issues.append((pid, f"dim names differ across years: {[list(v) for v in variants]}"))
        if canon is not None:
            pinfo[pid] = {**base, "dim_names": canon, "chunks": [i["label"] for _, i in items], "notes": notes,
                          "panel_partial": len(panel_years) < n_data,
                          "panel_chunks": panel_years}
        else:
            pinfo[pid] = {"chunks": [i["label"] for _, i in items], "notes": notes}
        stats[pid] = st
        # 패널 파일
        if panel_parts:
            g = pd.concat(panel_parts, ignore_index=True); del panel_parts
            dn = canon; nd = len(dn)
            years = sorted(int(x) for x in g.year.dropna().unique())
            meas = list(dict.fromkeys(g.measure.fillna("값")))
            dicts, didx = [], []
            for c in dcols[:nd]:
                vals = list(dict.fromkeys(g[c].fillna("")))
                posd = {v: i for i, v in enumerate(vals)}
                dicts.append(vals); didx.append([posd[v] for v in g[c].fillna("")])
            ypos = {y: i for i, y in enumerate(years)}; mpos = {m: i for i, m in enumerate(meas)}
            obj = {"pid": int(pid), "dim_names": dn, "years": years, "measures": meas, "dicts": dicts,
                   "y": [ypos.get(int(y), -1) if pd.notna(y) else -1 for y in g.year],
                   "m": [mpos[m] for m in g.measure.fillna("값")], "d": didx,
                   "v": [None if pd.isna(v) else (int(v) if float(v).is_integer() else round(float(v), 4)) for v in g.value]}
            js = json.dumps(obj, ensure_ascii=False, separators=(",", ":")); del obj, g
            with gzip.open(pn / f"p{pid}.json.gz", "wt", encoding="utf-8", compresslevel=6) as f:
                f.write(js)
            (pj / f"p{pid}.js").write_text(f"TAAS_LOAD({js});", encoding="utf-8")
            del js
    writer.close()
    shutil.rmtree(tmp, ignore_errors=True)

    prow = []
    for pid, m in meta.items():
        i = pinfo.get(pid, {}); st = stats.get(pid, {"n": 0, "measures": set(), "ymin": None, "ymax": None})
        note_list = sorted(i.get("notes", []))
        if i.get("panel_partial"):
            note_list.append("패널에는 장표가 커서 " + ", ".join(sorted(i["panel_chunks"])) + " 구간만 실음 (전체는 parquet/facts.parquet · taas.py)")
        prow.append({
            "pid": int(pid), "name": m["name"], "path": " > ".join(m["path"]),
            "category": m["path"][1] if len(m["path"]) > 1 else m["root"],
            "root": m["root"], "subject_id": int(m["subjectId"]),
            "dim_names": json.dumps(i.get("dim_names", []), ensure_ascii=False),
            "row_levels": json.dumps(i.get("row_levels", []), ensure_ascii=False),
            "col_levels": json.dumps(i.get("col_levels", []), ensure_ascii=False),
            "year_axis": i.get("year_axis"), "has_measure": int(bool(i.get("has_measure"))),
            "measures": json.dumps(sorted(st["measures"]), ensure_ascii=False),
            "year_min": st["ymin"], "year_max": st["ymax"], "n_facts": int(st["n"]),
            "chunks": ",".join(sorted(i.get("chunks", []))),
            "empty_chunks": ",".join(sorted(k for k, v in coverage.get(pid, {}).get("chunks", {}).items() if v["status"] == "empty")),
            "partial_chunks": ",".join(sorted(k for k, v in coverage.get(pid, {}).get("chunks", {}).items() if v["status"] == "partial_measures")),
            "dim_changed": int(bool(coverage.get(pid, {}).get("dim_variants"))),
            "panel_partial": int(bool(i.get("panel_partial"))),
            "notes": " / ".join(note_list),
            "source_url": m.get("source_url") or f"https://taas.koroad.or.kr/sta/acs/exs/typical.do?menuId=WEB_KMP_OVT_UAS_ASA&patternId={pid}",
        })
    pdf = pd.DataFrame(prow).sort_values("pid").reset_index(drop=True)
    pdf["year_min"] = pdf["year_min"].astype("Int32"); pdf["year_max"] = pdf["year_max"].astype("Int32")

    for pid, cov in coverage.items():
        cov["name"] = meta.get(pid, {}).get("name")
        cov["measure_years"] = {k: sorted(v) for k, v in stats.get(pid, {}).get("measure_years", {}).items()}
        cov["chunks"] = dict(sorted(cov["chunks"].items()))
    for pid, m in meta.items():
        coverage.setdefault(pid, {"name": m["name"], "chunks": {}, "dim_variants": [], "measure_years": {}, "not_collected": True})
    (out_dir / "coverage.json").write_text(json.dumps(dict(sorted(coverage.items(), key=lambda kv: int(kv[0]))), ensure_ascii=False, indent=1), encoding="utf-8")

    built_at = pd.Timestamp.now(tz="Asia/Seoul").isoformat(timespec="seconds")
    pdf.to_parquet(pq / "patterns.parquet", index=False)

    index = {"source": "한국도로교통공단 TAAS 교통사고분석시스템 > 교통사고 상세통계",
             "source_url": "https://taas.koroad.or.kr/sta/acs/exs/typical.do?menuId=WEB_KMP_OVT_UAS_ASA",
             "built_at": built_at, "n_facts": int(total), "year_min": ymin, "year_max": ymax,
             "patterns": json.loads(pdf.to_json(orient="records", force_ascii=False))}
    for p in index["patterns"]:
        for k in ("dim_names", "row_levels", "col_levels", "measures"):
            p[k] = json.loads(p[k])
    (out_dir / "index.json").write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")
    (out_dir / "index.js").write_text("window.TAAS_INDEX=" + json.dumps(index, ensure_ascii=False) + ";", encoding="utf-8")

    rd = out_dir / "raw"; rd.mkdir(exist_ok=True)
    for p in raw_paths:
        p = Path(p)
        if p.resolve().parent != rd.resolve():
            shutil.copy2(p, rd / p.name)

    return {"facts": int(total), "patterns": len(pdf), "with_data": int((pdf.n_facts > 0).sum()),
            "year_min": ymin, "year_max": ymax, "dups_removed": int(dup_total), "issues": issues[:30], "n_issues": len(issues)}


if __name__ == "__main__":
    raws = sys.argv[1:-1]
    print(json.dumps(build(raws, sys.argv[-1]), ensure_ascii=False, indent=1))
