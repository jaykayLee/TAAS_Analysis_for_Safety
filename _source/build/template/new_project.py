# -*- coding: utf-8 -*-
"""새 프로젝트 골격 생성기(project-structure/1.0) — 모든 프로젝트를 같은 5개 폴더 + _source로 시작한다.
  python3 build/template/new_project.py <새 프로젝트 폴더> --id ABC --name "프로젝트 이름" [--owner "J.K. Lee"] [--repo owner/repo] [--panel-url URL] [--force]
만드는 것:
  Main_<ID>.bat(→ 프로젝트 홈) · install.bat · README.txt · PROJECT.json · .gitignore
  01_Panel(Main·Sub) · 02_Strategy(00_History·01_Update·02_Analysis·03_User·04_LLM) · 03_References(분류 6 + files/) · 04_Libraries(분류 7)
  05_UserComments(STATUS.md · 01_Requests(첫 요청) · 02_Decisions(inbox·applied·conflicts + customize.schema.json) · 03_Prompts · 99_History)
  폴더마다 README.md(규약에서 생성)
  _source/build: paths.py(일반판) · strategy/docset.py·docset_pptx.js(문서 세트 생성기) · db/md2docx.py·xlsx_style.py · pdf/reference.docx · template/(이 생성기와 규약)
  _source/strategy/content.py — 구조 규약 문서 세트(docx·xlsx·pptx) 정의 시작본
다음: cd <폴더>/_source && python3 build/strategy/docset.py --version v0.1  → 02_Strategy/03_User/프로젝트구조_규약_v1.0.(docx|xlsx|pptx)"""
import os, sys, json, shutil, argparse, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); BUILD = os.path.dirname(HERE); ROOT = os.path.dirname(BUILD)
sys.path.insert(0, HERE); import contract as K

PATHS_PY = '''# -*- coding: utf-8 -*-
"""번들 경로 단일 정의(project-structure/{ver}, new_project.py가 생성한 일반판) — 폴더를 옮기면 여기만 고친다."""
import os, re, glob
BUILD = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(BUILD); BUNDLE = os.path.dirname(ROOT)
DIST = os.path.join(ROOT, "dist"); OUT_REPORTS = os.path.join(DIST, "md"); OUT_DB = os.path.join(DIST, "db"); WORK = os.path.join(BUILD, "_work")
REFS_HOME = os.path.join(BUNDLE, "03_References"); LIBS_HOME = os.path.join(BUNDLE, "04_Libraries"); USERCOMMENTS = os.path.join(BUNDLE, "05_UserComments")
for _d in (OUT_REPORTS, OUT_DB, WORK): os.makedirs(_d, exist_ok=True)
_RULES = {rules}
def folder_of(name):
    b = os.path.basename(name)
    for pat, d in _RULES:
        if re.search(pat, b): return d
    return ""
def place(name):
    d = folder_of(name); return f"{{d}}/{{os.path.basename(name)}}" if d else os.path.basename(name)
def out(name):
    p = os.path.join(BUNDLE, *place(name).split("/")); os.makedirs(os.path.dirname(p), exist_ok=True); return p
def brel(p): return os.path.relpath(p, BUNDLE).replace(os.sep, "/")
def rel(p): return os.path.relpath(p, ROOT).replace(os.sep, "/")
def lib_dir(lid):
    hit = glob.glob(os.path.join(LIBS_HOME, "*", lid)); return hit[0] if hit else os.path.join(LIBS_HOME, "05_New_Strategies", lid)
def lib_brel(lid): return brel(lib_dir(lid))
def dbfile(v): return os.path.join(OUT_DB, f"{pid}_DB_{{v}}.sqlite")
'''
CONTENT_PY = '''# -*- coding: utf-8 -*-
"""02_Strategy 문서 세트·폴더 README의 원천 — {name}. 수정은 여기서만 → python3 build/strategy/docset.py --version <버전>.
새 전략 문서는 docs()에 정의(docset/1.0)를 추가: 처음 만드는 문서는 docx·xlsx·pptx 3종(formats 생략), 이후 갱신은 formats=["docx"] 등 대표 1종."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(os.path.dirname(HERE), "build", "template")); import contract as K
NAME, PID = {name!r}, {pid!r}

def docs(con, V):
    import deps as D
    return [K.structure_doc(NAME, PID, V), D.doc(D.load(), V)]

def readmes(V):
    return K.readmes(PID)
'''
BAT = "\r\n".join(["@echo off", "chcp 65001 >nul", "rem {name} — 시작: 프로젝트 홈 → 메인 패널(new_project.py가 생성)", 'if /i "%~1"=="online" (start "" "{url}" & goto :eof)',
                   'if /i "%~1"=="main" goto main', 'for %%f in ("%~dp001_Panel\\Home\\*.html") do (start "" "%%~ff" & goto :eof)',
                   ":main", 'for %%f in ("%~dp001_Panel\\Main\\*.html") do (start "" "%%~ff" & goto :eof)', "echo 01_Panel 에 패널이 아직 없습니다.", "pause", ""])

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("target"); ap.add_argument("--id", required=True); ap.add_argument("--name", required=True)
    ap.add_argument("--owner", default="J.K. Lee"); ap.add_argument("--repo", default=""); ap.add_argument("--panel-url", default=""); ap.add_argument("--force", action="store_true")
    a = ap.parse_args(); T = os.path.abspath(a.target); pid = a.id
    if os.path.exists(T) and os.listdir(T) and not a.force: sys.exit(f"{T} 가 비어 있지 않습니다(--force로 덮어쓰기)")
    W = lambda rel, txt, mode="w": (os.makedirs(os.path.dirname(os.path.join(T, rel)) or T, exist_ok=True), open(os.path.join(T, rel), mode, encoding="utf-8", newline="" if rel.endswith(".bat") else None).write(txt))
    today = datetime.date.today().isoformat()
    # 폴더 골격
    for p, _, _ in K.SUB: os.makedirs(os.path.join(T, p.replace("<분류>/LIB-xxx/", "").replace("<분류>/", "")), exist_ok=True)
    for c, _, _ in K.CATS:
        os.makedirs(os.path.join(T, "04_Libraries", c), exist_ok=True)
        if c != "06_Methods": os.makedirs(os.path.join(T, "03_References", c, "files"), exist_ok=True); W(f"03_References/{c}/files/.keep", "")
    for d in ("inbox", "applied", "conflicts"): os.makedirs(os.path.join(T, "05_UserComments", "02_Decisions", d), exist_ok=True); W(f"05_UserComments/02_Decisions/{d}/.keep", "")
    for rel, txt in K.readmes(pid).items(): W(rel, txt)
    # 최상위
    pj = {"schema": "project/1.0", "id": pid, "name": a.name, "version": "v0.1", "structure": {"contract": f"project-structure/{K.STRUCT_VER}", "doc": f"02_Strategy/03_User/프로젝트구조_규약_v{K.STRUCT_VER}.docx"},
          "owner": a.owner, "repo": a.repo, "branch": "", "panel_url": a.panel_url, "entry": f"Main_{pid}.bat", "folders": {t["path"].rstrip("/"): t["role"] for t in K.top(pid) if t["path"].endswith("/")},
          "libraries": [], "status": "05_UserComments/STATUS.md", "history": "02_Strategy/00_History/", "created": today, "note": "new_project.py가 생성 — 빌드가 생기면 생성기가 다시 씀"}
    W("PROJECT.json", json.dumps(pj, ensure_ascii=False, indent=1) + "\n")
    W(f"Main_{pid}.bat", BAT.format(name=a.name, url=a.panel_url or "https://claude.ai"))
    W("README.txt", "\n".join([f"{a.name} ({pid}) — v0.1", "=" * 40, f"시작: Main_{pid}.bat · 프로젝트 정보: PROJECT.json · 지금 상태: 05_UserComments/STATUS.md", "구조(project-structure/" + K.STRUCT_VER + "):",
                               *[f"   {t['path']:18} {t['role']}" for t in K.top(pid)], "", "새 전략 문서: _source/strategy/content.py에 정의 → cd _source && python3 build/strategy/docset.py --version v0.1", ""]))
    W(".gitignore", "_source/build/_work/\n__pycache__/\n*.zip\n")
    W("05_UserComments/STATUS.md", f"# STATUS — 지금 상태\n\n- 갱신: {today} · 번들 v0.1 · (빌드·업데이트가 다시 씀)\n\n## 요청(01_Requests)\n\n- [접수] `REQ-{today.replace('-', '')}-01_프로젝트_시작.md` — 프로젝트 시작\n\n## 결정 묶음(02_Decisions)\n\n- 대기 0 · 적용 0 · 충돌 0\n\n## 작업 목록\n\n- 없음\n")
    W(f"05_UserComments/01_Requests/REQ-{today.replace('-', '')}-01_프로젝트_시작.md", f"# REQ-{today.replace('-', '')}-01 프로젝트 시작\n- 상태: 접수\n- 요청일: {today} · 요청자: {a.owner}\n- 관련: 전체\n\n## 요청\n{a.name} 프로젝트를 표준 구조로 시작한다.\n\n## 결정·선택(Step)\n\n## 처리 결과(버전·커밋)\n")
    W("05_UserComments/99_History/ledger.jsonl", "")
    sch = os.path.join(os.path.dirname(ROOT), "05_UserComments", "02_Decisions", "customize.schema.json")
    if os.path.exists(sch): shutil.copy(sch, os.path.join(T, "05_UserComments", "02_Decisions", "customize.schema.json"))
    # _source — 일반 경로 모듈 + 문서 세트 생성기 + 규약
    rules = [(p, d) for p, d in K.DOC_RULES]
    W("_source/build/paths.py", PATHS_PY.format(ver=K.STRUCT_VER, rules=repr(rules), pid=pid))
    for rel in ("strategy/docset.py", "strategy/docset_pptx.js", "db/md2docx.py", "db/xlsx_style.py", "pdf/reference.docx", "template/contract.py", "template/new_project.py", "template/deps.py", "template/home.py", "template/office_check.py", "template/standard_pack.py", "strategy/bg.py"):
        dst = os.path.join(T, "_source", "build", rel); os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copy(os.path.join(BUILD, rel), dst)
    W("_source/strategy/content.py", CONTENT_PY.format(name=a.name, pid=pid))
    W("_source/README.md", f"# _source — {a.name}\n\n코드만 둡니다(데이터는 04_Libraries, 읽기용 문서는 01~03).\n\n- `build/paths.py` 폴더 규칙 · `build/strategy/` 문서 세트 생성기 · `build/template/` 규약·새 프로젝트 생성기\n- `strategy/content.py` 전략 문서 원천\n\n```\npython3 build/strategy/docset.py --version v0.1\n```\n")
    # 의존성(install.bat + 02_Strategy/05_Dependencies)·프로젝트 홈 — 새 프로젝트의 생성기로 실행
    import subprocess
    subprocess.run([sys.executable, os.path.join(T, "_source", "build", "template", "deps.py")], check=True)
    subprocess.run([sys.executable, os.path.join(T, "_source", "build", "template", "home.py"), "--version", "v0.1"], check=True)
    n = sum(len(fs) for _, _, fs in os.walk(T)); print(f"새 프로젝트 {pid} '{a.name}' → {T} (파일 {n}개)")

if __name__ == "__main__": main()
