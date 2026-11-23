# -*- coding: utf-8 -*-
"""번들 경로 단일 정의(project-structure/1.0, new_project.py가 생성한 일반판) — 폴더를 옮기면 여기만 고친다."""
import os, re, glob
BUILD = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(BUILD); BUNDLE = os.path.dirname(ROOT)
DIST = os.path.join(ROOT, "dist"); OUT_REPORTS = os.path.join(DIST, "md"); OUT_DB = os.path.join(DIST, "db"); WORK = os.path.join(BUILD, "_work")
REFS_HOME = os.path.join(BUNDLE, "03_References"); LIBS_HOME = os.path.join(BUNDLE, "04_Libraries"); USERCOMMENTS = os.path.join(BUNDLE, "05_UserComments")
for _d in (OUT_REPORTS, OUT_DB, WORK): os.makedirs(_d, exist_ok=True)
_RULES = [('^(프로젝트_변경이력|문서관리_색인_)', '02_Strategy/00_History'), ('^갱신전략_', '02_Strategy/01_Update'), ('^분석전략_', '02_Strategy/02_Analysis'), ('^(프로젝트구조_규약_|사용자전략_)', '02_Strategy/03_User'), ('^(LLM전략_|프로젝트표준_)', '02_Strategy/04_LLM'), ('^의존성_목록_', '02_Strategy/05_Dependencies')]
def folder_of(name):
    b = os.path.basename(name)
    for pat, d in _RULES:
        if re.search(pat, b): return d
    return ""
def place(name):
    d = folder_of(name); return f"{d}/{os.path.basename(name)}" if d else os.path.basename(name)
def out(name):
    p = os.path.join(BUNDLE, *place(name).split("/")); os.makedirs(os.path.dirname(p), exist_ok=True); return p
def brel(p): return os.path.relpath(p, BUNDLE).replace(os.sep, "/")
def rel(p): return os.path.relpath(p, ROOT).replace(os.sep, "/")
def lib_dir(lid):
    hit = glob.glob(os.path.join(LIBS_HOME, "*", lid)); return hit[0] if hit else os.path.join(LIBS_HOME, "05_New_Strategies", lid)
def lib_brel(lid): return brel(lib_dir(lid))
def dbfile(v): return os.path.join(OUT_DB, f"TAAS_DB_{v}.sqlite")
