# -*- coding: utf-8 -*-
"""문서 세트 생성기(v3.8, 프로젝트 공통) — 문서 정의(dict) 하나로 Word(docx)·Excel(xlsx)·PowerPoint(pptx)를 같은 내용으로 만든다.
  정의 스키마 docset/1.0:
    id · file(확장자 없는 파일 이름, 예: 갱신전략_v1.0) · title · subtitle · version · owner · purpose · summary[문장]
    sections[{h, p[문단], bullets[항목], table{head, rows}, note}]      → Word(md 원문 → md2docx)
    sheets[{name, title, head, rows, widths, center}]                     → Excel(첫 시트 '개요' 자동)
    slides[{kind: title|cards|bullets|flow|table|structure|timeline|map, …}] → PowerPoint(docset_pptx.js)
    formats: ["docx","xlsx","pptx"] — 처음 만드는 문서는 3종 세트, 이후 갱신은 대표 형식 1개(사용자 결정 2026-11-22)
  사용: python build/strategy/docset.py --version v3.8 [--only id,id]   (문서 정의: _source/strategy/content.py)"""
import os, sys, json, argparse, subprocess, glob, re, sqlite3
HERE = os.path.dirname(os.path.abspath(__file__)); BUILD = os.path.dirname(HERE)
sys.path.insert(0, BUILD); sys.path.insert(0, os.path.join(BUILD, "db"))
import paths as PA
from xlsx_style import title as xt, table as xtab, finish as xfin
from openpyxl import Workbook

def md_of(d):
    esc = lambda s: str(s if s is not None else "").replace("|", "\\|").replace("\n", "<br>")
    L = [f"# {d['title']}", "", f"**{d.get('subtitle', '')}**" if d.get("subtitle") else "", "",
         f"문서 {d['file']} · 버전 {d['version']} · 작성 {d.get('owner', '')} · 번들 {d['bundle']} · 생성기 `_source/build/strategy/docset.py`(원천 `_source/strategy/content.py`) — 생성물, 직접 수정 금지", ""]
    if d.get("purpose"): L += [f"> {d['purpose']}", ""]
    if d.get("summary"): L += ["## 요약", ""] + [f"- {x}" for x in d["summary"]] + [""]
    def sec(s, lv):
        out = [f"{'#' * lv} {s['h']}", ""]
        for p in s.get("p", []): out += [p, ""]
        if s.get("bullets"): out += [f"- {b}" for b in s["bullets"]] + [""]
        if s.get("steps"): out += [f"{i}. {b}" for i, b in enumerate(s["steps"], 1)] + [""]
        if s.get("table"):
            t = s["table"]; out += ["| " + " | ".join(esc(h) for h in t["head"]) + " |", "|" + "---|" * len(t["head"])]
            out += ["| " + " | ".join(esc(c) for c in r) + " |" for r in t["rows"]] + [""]
        if s.get("code"): out += ["```", *s["code"], "```", ""]
        if s.get("note"): out += [f"> {s['note']}", ""]
        for c in s.get("sub", []): out += sec(c, lv + 1)
        return out
    for s in d.get("sections", []): L += sec(s, 2)
    return "\n".join(L) + "\n"

def xlsx_of(d, out):
    wb = Workbook(); ws = wb.active; ws.title = "개요"
    sub = f"{d['file']} · 버전 {d['version']} · 번들 {d['bundle']} · 생성기 _source/build/strategy/docset.py — 생성물, 직접 수정 금지"
    xt(ws, d["title"], sub, 2)
    rows = [["문서", d["title"]], ["목적", d.get("purpose", "")], ["버전", d["version"]], ["작성", d.get("owner", "")], ["같은 내용의 세트", " · ".join(f"{d['file']}.{x}" for x in d["formats"])]]
    rows += [["요약", x] for x in d.get("summary", [])]
    rows += [["시트", f"{s['name']} — {s['title']}"] for s in d.get("sheets", [])]
    xtab(ws, ["항목", "내용"], rows, [16, 110], height=None)
    for s in d.get("sheets", []):
        w = wb.create_sheet(s["name"][:31]); xt(w, s["title"], sub, len(s["head"]))
        xtab(w, s["head"], s["rows"], s.get("widths") or [18] * len(s["head"]), center=tuple(s.get("center", ())), height=s.get("height"))
    xfin(wb); wb.save(out)

def build(docs, bundle, only=None):
    pp = []
    for d in docs:
        if only and d["id"] not in only: continue
        d = dict(d, bundle=bundle); d.setdefault("formats", ["docx", "xlsx", "pptx"])
        base = d["file"]
        # 같은 이름 계열의 이전 판(버전만 다른 파일)은 지운다 — 이력은 02_Strategy/00_History 대장 + git
        stem = re.sub(r"_v[\d.]+$", "", base)
        for old in glob.glob(os.path.join(os.path.dirname(PA.out(base + ".x")), stem + "_v*.*")):
            if os.path.splitext(os.path.basename(old))[0] != base: os.remove(old)
        if "docx" in d["formats"]:
            mp = os.path.join(PA.OUT_REPORTS, base + ".md"); open(mp, "w", encoding="utf-8").write(md_of(d))
            subprocess.run([sys.executable, os.path.join(BUILD, "db", "md2docx.py"), mp, base + ".docx"], check=True)
        if "xlsx" in d["formats"]:
            xlsx_of(d, PA.out(base + ".xlsx")); print("saved", base + ".xlsx")
        if "pptx" in d["formats"] and d.get("slides"):
            KIK = {"structure": "Project Structure Standard", "update": "Update Strategy", "llm": "LLM Operating Strategy", "history": "Change Management", "deps": "Dependencies"}
            pp.append({"file": PA.out(base + ".pptx"), "title": d["title"], "subtitle": d.get("subtitle", ""), "bundle": bundle, "footer": f"{d['title']}  |  {base}  |  {d.get('owner', '')}",
                       "kicker": d.get("kicker") or KIK.get(d["id"], "Strategy"), "summary": d.get("summary", [])[:4], "slides": d["slides"]})
    if pp:
        jp = os.path.join(PA.WORK, "_docset_pptx.json"); json.dump(pp, open(jp, "w", encoding="utf-8"), ensure_ascii=False)
        if os.path.exists(os.path.join(HERE, "bg.py")): subprocess.run([sys.executable, os.path.join(HERE, "bg.py")], check=True, stdout=subprocess.DEVNULL)   # 배경 이미지(재현 가능)
        subprocess.run(["node", os.path.join(HERE, "docset_pptx.js"), jp], check=True)
    # Office 호환성 게이트(필수) — 방금 만든 파일을 바로 검사·보정, 실패면 중단
    made = [PA.out(d["file"] + "." + x) for d in docs if not only or d["id"] in only for x in d.get("formats", ["docx", "xlsx", "pptx"])]
    made = [p for p in made if os.path.exists(p)]
    oc = os.path.join(BUILD, "template", "office_check.py")
    if made and os.path.exists(oc): subprocess.run([sys.executable, oc, "-q", *made], check=True)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--version", required=True); ap.add_argument("--only"); a = ap.parse_args()
    sys.path.insert(0, os.path.join(PA.ROOT, "strategy")); sys.path.insert(0, os.path.join(BUILD, "template")); import content as C
    dbp = PA.dbfile(a.version) if hasattr(PA, "dbfile") else ""
    con = None
    if dbp and os.path.exists(dbp): con = sqlite3.connect(dbp); con.row_factory = sqlite3.Row      # DB가 없는 프로젝트(템플릿)는 None
    build(C.docs(con, a.version), a.version, set(a.only.split(",")) if a.only else None)
    if a.only: sys.exit(0)
    # 03_References 분류별 색인(Excel) — 원천 LIB-REFS
    for x in (C.ref_indexes(con, a.version) if hasattr(C, "ref_indexes") and con else []):
        out = PA.out(x["file"] + ".xlsx")
        for old in glob.glob(os.path.join(os.path.dirname(out), f"참고문헌_색인_{x['cat']}_v*.xlsx")):
            if old != out: os.remove(old)
        wb = Workbook(); ws = wb.active; ws.title = "색인"; xt(ws, x["title"] + f" ({x['count']}건)", x["sub"], len(x["head"]))
        xtab(ws, x["head"], x["rows"] or [["(이 분류의 문헌 없음 — 자리 유지)"] + [""] * (len(x["head"]) - 1)], [9, 10, 8, 18, 54, 6, 12, 8, 40, 10, 6, 16, 6, 18], center=(1, 3, 6, 10, 11, 13))
        xfin(wb); wb.save(out); os.makedirs(os.path.join(os.path.dirname(out), "files"), exist_ok=True)
        kp = os.path.join(os.path.dirname(out), "files", ".keep"); open(kp, "a").close()
    print("saved 03_References 색인") if hasattr(C, "ref_indexes") and con else None
    # 폴더 README(규약과 같은 원천)
    for rp, txt in C.readmes(a.version).items():
        fp = os.path.join(PA.BUNDLE, rp); os.makedirs(os.path.dirname(fp), exist_ok=True); open(fp, "w", encoding="utf-8").write(txt)
    print("saved README", len(C.readmes(a.version)))
