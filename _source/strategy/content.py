# -*- coding: utf-8 -*-
"""02_Strategy 문서 세트·폴더 README의 원천 — TAAS 교통사고 분석. 수정은 여기서만 → python3 build/strategy/docset.py --version <버전> (cd _source).
새 전략 문서는 docs()에 정의(docset/1.0)를 추가: 처음 만드는 문서는 docx·xlsx·pptx 3종(formats 생략), 이후 갱신은 formats=["docx"] 등 대표 1종."""
import os, sys, re
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(os.path.dirname(HERE), "build", "template")); sys.path.insert(0, os.path.join(os.path.dirname(HERE), "build"))
import contract as K
NAME, PID = "TAAS 교통사고 분석", "TAAS"
import project_meta as PM

# 이동표 — 표준 구조 전환(2026-11-23, REQ-20261123-01). 이전 구조 전체는 git 브랜치 archive/pre-standard-v1.6 (압축본 포함)
MOVES = [
    ("build.py · serve.py", "_source/", "코드"), ("src/", "_source/src/", "코드"), ("collector/", "_source/collector/", "코드"),
    ("panel/panel_template.html", "_source/panel/", "패널 원천(코드)"), ("tests/", "_source/tests/", "코드"),
    ("ops/*.py · auto_update.json · ext_sources.json", "_source/ops/", "자동 갱신 스크립트·설정"),
    ("docs/manual/ (deck.js·shots.py·img)", "_source/strategy/manual/", "매뉴얼 생성 원천"), ("docs/analysis/child/*.py", "_source/analysis/child/", "분석 스크립트"),
    ("CHANGELOG.md", "_source/strategy/CHANGELOG.md", "변경 이력 원천 → 02_Strategy/00_History/프로젝트_변경이력_v*.xlsx 생성"),
    ("data/raw/taas/*.json.gz", "03_References/02_Statistics/files/taas/", "TAAS 수집 원문"),
    ("data/source/ext/kostat/ · police/", "03_References/02_Statistics/files/kostat/ · police/", "부처 원자료(엑셀·CSV)"),
    ("data/raw/ext/kostat · police", "04_Libraries/02_Statistics/LIB-KOSTAT · LIB-POLICE/", "부처 라이브러리 원천(json.gz)"),
    ("data/raw/ext/policy · data/source/ext/policy", "04_Libraries/01_Standard_Law/LIB-POLICY/", "제도 연표(직접 작성한 원천)·근거"),
    ("library/ (빌드 결과, git 제외)", "04_Libraries/02_Statistics/LIB-TAAS/build/", "라이브러리 생성물"),
    ("library/panel.html · panel_online.html", "01_Panel/Main/", "메인 패널(생성물)"),
    ("docs/TAAS_교통사고분석패널_사용매뉴얼.pptx", "02_Strategy/03_User/사용자전략_패널사용매뉴얼_v1.3.pptx", "사용자 문서"),
    ("docs/reports/TAAS_수집현황_*", "02_Strategy/01_Update/Log/", "수집 보고"),
    ("docs/reports/*.xlsx·*.csv, docs/analysis/child/*.csv·*.json", "02_Strategy/02_Analysis/Workbooks/", "분석 워크북"),
    ("ops/AUTO_UPDATE.md · EXT_UPDATE.md", "02_Strategy/04_LLM/LLM전략_*_v1.0.md", "LLM 실행 절차(md 예외)"),
    ("ops/APP_PROMPT*.md", "05_UserComments/03_Prompts/", "Claude 앱 프롬프트"), ("ops/HANDOFF.md", "05_UserComments/STATUS.md", "지금 상태·다음 할 일"),
    ("패널_열기·업데이트·빌드_실행·바뀐파일만_받기.bat", "Main_TAAS.bat (메뉴) · install.bat", "시작 파일 통합"),
]
STEPS = [
    ("1 진행 범위", "권장 3단계(문서·상태 층 → 코드·데이터 이동 → 패널·시작 파일)를 연속 수행", "사용자 선택 2026-11-23"),
    ("2 프로젝트 ID", "TAAS", "사용자 지정"),
    ("3 이전 구조 보존", "git 브랜치 archive/pre-standard-v1.6 + 압축본(_archive/, main·PC 폴더에는 없음)", "사용자 요청"),
    ("4 라이브러리 생성물 위치", "04_Libraries/02_Statistics/LIB-TAAS/build (git 제외, 부처 라이브러리는 그 안 ext/)", "권장안"),
    ("5 03·04 구분", "수집 원문(json.gz·엑셀·CSV)=03 files/, 변환한 원천(json.gz)·직접 작성한 연표=04 LIB", "권장안"),
    ("6 최상위 예외", "CLAUDE.md·README.md·.gitignore 유지(동작에 필요), 기본 브랜치 main 유지", "권장안"),
    ("7 시작 파일", "기존 .bat 4개 → Main_TAAS.bat 메뉴 + install.bat", "권장안"),
    ("8 전략 문서", "새로 만드는 문서(구조 규약·의존성·변경 이력)는 3종, 기존 문서는 이름만 규약에 맞춤", "권장안"),
]


def changelog_rows():
    t = open(os.path.join(HERE, "CHANGELOG.md"), encoding="utf-8").read()
    rows = []
    for m in re.finditer(r"^## (\d{4}-\d{2}-\d{2}) — (.+?)\n(.*?)(?=^## |\Z)", t, re.S | re.M):
        items = [re.sub(r"\s+", " ", x.strip("- ").strip()) for x in re.split(r"\n- ", "\n" + m.group(3).strip()) if x.strip()]
        rows.append([m.group(1), m.group(2), " / ".join(items)[:900]])
    return rows


def history_doc(V):
    rows = changelog_rows()
    return {"id": "history", "file": f"프로젝트_변경이력_{V}", "version": V, "owner": "J.K. Lee", "kicker": "Change Management",
            "title": "프로젝트 변경 이력", "subtitle": f"{NAME} — 버전별 변경 대장",
            "purpose": "버전마다 무엇이 바뀌었는지 한 곳에 남긴다. 이전 판 파일은 두지 않고 이 대장과 git 커밋으로 복원한다.",
            "summary": [f"최신: {rows[0][0]} {rows[0][1]}" if rows else "", f"기록 {len(rows)}건 — 원천 _source/strategy/CHANGELOG.md",
                        "이전 구조(v1.6) 전체: git 브랜치 archive/pre-standard-v1.6 (압축본 포함)"],
            "sections": [{"h": "변경 대장", "table": {"head": ["날짜", "버전·제목", "내용"], "rows": rows}},
                         {"h": "구조 전환 이동표 (2026-11-23)", "table": {"head": ["이전 위치", "새 위치", "사유"], "rows": [list(x) for x in MOVES]}}],
            "sheets": [{"name": "변경 대장", "title": "버전별 변경 대장", "head": ["날짜", "버전·제목", "내용"], "rows": rows, "widths": [12, 34, 120], "height": 60},
                       {"name": "이동표", "title": "구조 전환 이동표 (2026-11-23)", "head": ["이전 위치", "새 위치", "사유"], "rows": [list(x) for x in MOVES], "widths": [44, 52, 34]}],
            "slides": [{"kind": "title", "title": "프로젝트 변경 이력", "sub": f"{NAME} · {len(rows)}건", "meta": V},
                       {"kind": "table", "title": "최근 변경", "head": ["날짜", "버전·제목"], "rows": [r[:2] for r in rows[:10]], "colW": [2.0, 10.1], "rowH": 0.4, "fontSize": 11}]}


def docs(con, V):
    import deps as D
    cat_rows = [[c, n, PM.CAT_DESC.get(c, d), {"01_Standard_Law": "법령·제도", "02_Statistics": "통계 DB·통계표·파일데이터"}.get(c, "—"),
                 sum(1 for r in _refs() if r["cat"] == c)] for c, n, d in K.CATS]
    extra = [{"h": "8. 이 프로젝트(TAAS)에 적용한 결정", "table": {"head": ["Step", "결정", "근거"], "rows": [list(s) for s in STEPS]}},
             {"h": "9. 이동표", "p": ["이전 구조 전체는 git 브랜치 archive/pre-standard-v1.6에 압축본과 함께 보관했다."], "table": {"head": ["이전 위치", "새 위치", "사유"], "rows": [list(x) for x in MOVES]}}]
    sheets = [{"name": "결정", "title": "TAAS 적용 결정(Step)", "head": ["Step", "결정", "근거"], "rows": [list(s) for s in STEPS], "widths": [22, 90, 20]},
              {"name": "이동표", "title": "이동표", "head": ["이전 위치", "새 위치", "사유"], "rows": [list(x) for x in MOVES], "widths": [44, 52, 34]}]
    slides = [{"kind": "table", "title": "TAAS 이동표 — 이전 위치 → 새 위치", "head": ["이전", "새 위치"], "rows": [list(x[:2]) for x in MOVES[:12]], "colW": [5.4, 6.7], "rowH": 0.34, "fontSize": 9.5}]
    return [K.structure_doc(NAME, PID, V, cat_rows=cat_rows, extra_sections=extra, extra_sheets=sheets, extra_slides=slides, panel_items=("Home", "Main (TAAS 분석 패널)", "온라인 게시본")),
            D.doc(D.load(), V), history_doc(V)]


def _refs():
    import json
    p = os.path.join(os.path.dirname(os.path.dirname(HERE)), "04_Libraries", "00_Core", "LIB-REFS", "refs.json")
    return json.load(open(p, encoding="utf-8"))["refs"] if os.path.exists(p) else []


def readmes(V):
    lib_lines = {}
    for L in PM.LIBS:
        lib_lines.setdefault(L["cat"], []).append(f"- `{L['id']}` — {L['name']} (장표 {L['pids']}) · 원문 `{L['source']}` · 빌드 `{L['build']}` · {L['note']}")
    ref_kinds = {"01_Standard_Law": "법령·제도(국가법령정보센터 등 링크)", "02_Statistics": "TAAS·KOSIS·e-나라지표·공공데이터포털 통계와 수집 원문"}
    return K.readmes(PID, cat_desc=PM.CAT_DESC, ref_kinds=ref_kinds, lib_lines=lib_lines, refs_src="04_Libraries/00_Core/LIB-REFS/refs.json")
