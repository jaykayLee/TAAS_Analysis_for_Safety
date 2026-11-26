# -*- coding: utf-8 -*-
"""TAAS 경로 단일 정의(project-structure/1.0) — 폴더를 옮기면 여기만 고친다. 모든 스크립트가 이 모듈로 경로를 얻는다.
  원문(03_References) → 원천(04_Libraries/<분류>/LIB-*) → 라이브러리 생성물(LIB-TAAS/build, git 제외) → 패널(01_Panel)"""
from pathlib import Path

SRC = Path(__file__).resolve().parent            # _source/
ROOT = SRC.parent                                 # 프로젝트 루트(저장소)
REFS = ROOT / "03_References"
LIBS = ROOT / "04_Libraries"
STAT_FILES = REFS / "02_Statistics" / "files"     # 통계 원문(수집본·엑셀·CSV)
RAW_TAAS = STAT_FILES / "taas"                    # TAAS 수집 원문 json.gz
LIB_OUT = LIBS / "02_Statistics" / "LIB-TAAS" / "build"   # 라이브러리 생성물(패널 데이터 포함)
TEMPLATE = SRC / "panel" / "panel_template.html"
OPS = SRC / "ops"
PANEL_MAIN = ROOT / "01_Panel" / "Main"
PANEL_HOME = ROOT / "01_Panel" / "Home"
STATUS = ROOT / "05_UserComments" / "STATUS.md"
CHANGELOG = SRC / "strategy" / "CHANGELOG.md"
LLM_DOCS = ROOT / "02_Strategy" / "04_LLM"
AUTO_UPDATE_DOC = LLM_DOCS / "LLM전략_자동갱신절차_v1.0.md"
EXT_UPDATE_DOC = LLM_DOCS / "LLM전략_부처자료갱신절차_v1.0.md"
SYNC_DOC = LLM_DOCS / "LLM전략_PC동기화절차_v1.0.md"
PROMPTS = ROOT / "05_UserComments" / "03_Prompts"
APP_PROMPT = PROMPTS / "Claude앱_갱신프롬프트_v1.0.md"
APP_PROMPT_EXT = PROMPTS / "Claude앱_부처갱신프롬프트_v1.0.md"
AUTO_JSON = OPS / "auto_update.json"
EXT_SOURCES = OPS / "ext_sources.json"

# 부처 라이브러리: raw = 변환한 원천(<lib>.json.gz, 04), source = 원자료(03 files/ 또는 직접 작성한 04 원천)
EXT = {
    "kostat": {"raw": LIBS / "02_Statistics" / "LIB-KOSTAT", "source": STAT_FILES / "kostat"},
    "mois": {"raw": LIBS / "02_Statistics" / "LIB-MOIS", "source": STAT_FILES / "mois"},
    "molit": {"raw": LIBS / "02_Statistics" / "LIB-MOLIT", "source": STAT_FILES / "molit"},
    "police": {"raw": LIBS / "02_Statistics" / "LIB-POLICE", "source": STAT_FILES / "police"},
    "policy": {"raw": LIBS / "01_Standard_Law" / "LIB-POLICY", "source": LIBS / "01_Standard_Law" / "LIB-POLICY"},
}
EVENTS = EXT["policy"]["raw"] / "events.json"


def ext_raw(lib):
    return EXT[lib]["raw"]


def ext_src(lib):
    return EXT[lib]["source"]


def rel(p):
    """루트 기준 상대 경로(표시용, / 구분)"""
    try:
        return Path(p).resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(p)
