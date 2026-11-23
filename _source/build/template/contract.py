# -*- coding: utf-8 -*-
"""프로젝트 표준 구조 규약(project-structure/1.0) — 모든 프로젝트가 공유하는 단일 원천.
이 파일을 읽는 곳: 각 프로젝트의 _source/strategy/content.py(규약 문서·README) · build/template/new_project.py(새 골격) · paths(폴더 규칙).
프로젝트마다 다른 것(분류별 실제 내용·라이브러리·이동표)은 content.py가 extra로 넘긴다."""
STRUCT_VER = "1.0"
FOLDERS = ["01_Panel", "02_Strategy", "03_References", "04_Libraries", "05_UserComments"]
def top(pid="<ID>"):
    return [
 {"path": f"Main_{pid}.bat", "role": "시작 파일 — 프로젝트 홈(폴더·파일 지도) → 메인 패널(인자 online이면 게시 패널)", "put": "자동 생성", "not": "—", "by": "생성"},
 {"path": "install.bat", "role": "의존성 설치 — 02_Strategy/05_Dependencies의 목록대로 도구·패키지 설치", "put": "자동 생성(원천 _source/build/deps.json)", "not": "—", "by": "생성"},
 {"path": "README.txt", "role": "이번 버전에 구현된 내용 정리·설명", "put": "자동 생성", "not": "—", "by": "생성"},
 {"path": "PROJECT.json", "role": "프로젝트 신분증 — 시스템(LLM)이 가장 먼저 읽는 파일", "put": "이름·버전·규약 버전·폴더·라이브러리·패널 URL·저장소", "not": "비밀값(토큰·비밀번호)", "by": "생성"},
 {"path": "_source/", "role": "시스템 중심 컨트롤러 — 구현에 필요한 모든 소스 코드", "put": "생성기·패널 원천·자동 갱신 스크립트·문서 원천(strategy/)", "not": "읽기용 산출물·라이브러리 데이터", "by": "작성(개발)"},
 {"path": "01_Panel/", "role": "사용자 중심 컨트롤러 — 전략·결과·새 입력을 한 화면에서 관리", "put": "Home/ 프로젝트 홈(첫 패널 — 폴더·파일 지도·업데이트 날짜) · Main/ 메인 패널(온라인·오프라인) · Sub/ 연계 분석 패널", "not": "패널 원천(→ _source/panel)", "by": "생성"},
 {"path": "02_Strategy/", "role": "프로젝트를 표현하는 전략과 결과를 '문서'로 정리", "put": "00_History · 01_Update · 02_Analysis · 03_User · 04_LLM · 05_Dependencies (docx·xlsx·pptx·pdf)", "not": "원문 자료(→ 03) · 데이터 원천(→ 04)", "by": "생성(원천 _source)"},
 {"path": "03_References/", "role": "실제 존재하는 문서·사이트 링크·법률과 표준", "put": "분류별 서지·링크 색인(Excel) + 공개·허가된 원문 파일(files/)", "not": "유료 표준 원문 무단 사본 · 분석 결과", "by": "색인 생성 + 원문 수동 추가"},
 {"path": "04_Libraries/", "role": "References 정보를 시스템이 쓰는 라이브러리로 정제 — 03과 같은 분류", "put": "<분류>/LIB-xxx/(원천 JSON + library.json) · <분류>/라이브러리_xxx_v*.xlsx(읽기용)", "not": "코드(→ _source) · 이전 판 사본(→ git)", "by": "작성(원천) + 카탈로그 생성"},
 {"path": "05_UserComments/", "role": "사용자가 결과를 보며 요청·결정한 내용 — 항상 현재 상태(STATUS)를 남김", "put": "STATUS.md · 01_Requests · 02_Decisions(inbox·applied·conflicts) · 03_Prompts · 99_History", "not": "라이브러리 직접 수정(결정 묶음을 거쳐 반영)", "by": "사용자·패널 작성 + 업데이트가 처리"}]
SUB = [
 ("01_Panel/Home/", "프로젝트 홈(첫 패널) — 폴더·파일 트리·목록, 파일 의미, 마지막 업데이트 날짜 → 메인 패널로", "생성"),
 ("01_Panel/Main/", "메인 분석 패널(온라인 게시본·오프라인판)", "생성"), ("01_Panel/Sub/", "메인과 연계된 분석 패널(필요할 때 추가)", "생성"),
 ("02_Strategy/00_History/", "변경 대장(프로젝트_변경이력)·문서관리 색인 — Change Manager", "생성"),
 ("02_Strategy/01_Update/", "갱신 전략 · Log/(갱신 실행 보고)", "생성"),
 ("02_Strategy/02_Analysis/", "분석 보고서 · Workbooks/(분석 워크북)", "생성"),
 ("02_Strategy/03_User/", "사용자 전략 — 업무 매뉴얼·브리프·설명 PPT·프로젝트 구조 규약", "생성"),
 ("02_Strategy/04_LLM/", "LLM 전략 — 자동 실행·프롬프트·권한·결정 반영 원칙", "생성"),
 ("02_Strategy/05_Dependencies/", "필요한 의존성 — 의존성 목록 문서·requirements.txt·npm-packages.txt(install.bat이 읽음)", "생성"),
 ("03_References/<분류>/", "분류별 참고문헌 색인 + files/(공개·허가 원문)", "색인 생성 · 원문 수동"),
 ("04_Libraries/<분류>/LIB-xxx/", "라이브러리 원천(library.json이 버전·파일·적재 테이블 선언)", "작성"),
 ("05_UserComments/01_Requests/", "사용자 요청 1건 = md 1개(REQ-YYYYMMDD-NN) — 상태: 접수·진행·완료·보류", "작성"),
 ("05_UserComments/02_Decisions/", "패널 결정 묶음 customize/1.0 — inbox → applied | conflicts", "패널·업데이트"),
 ("05_UserComments/03_Prompts/", "예약 작업·LLM 프롬프트와 관리 스크립트 설명", "작성"),
 ("05_UserComments/99_History/", "처리 이력 ledger.jsonl · 완료 요청 보관", "업데이트")]
CATS = [("00_Core", "공통 기준", "프로젝트 내부 기준(아키텍처·용어·절차·고정 문안)"), ("01_Standard_Law", "표준·법규", "표준·법률·규정·인증"),
        ("02_Statistics", "통계·관측", "통계·데이터셋·관측 결과"), ("03_Papers_Patents", "논문·특허", "논문·특허·연구 보고서"),
        ("04_Other_Projects", "다른 프로젝트", "기관·타 과제 산출물"), ("05_New_Strategies", "새 전략", "프레임워크·새 방법 후보"), ("06_Methods", "계산 방법", "라이브러리 전용 — 계산·판정 방법")]
RULES = [("폴더 이름", "NN_English(공백·& 없음) — 순서는 번호, 뜻은 영어", "01_Standard_Law, 02_Decisions"),
         ("파일 이름", "한글_제목_vX.Y.확장자 — 번들 산출물은 번들 버전, 전략 문서는 문서 버전(파일명 버전 유지)", "갱신전략_v1.0.docx"),
         ("이전 판", "같은 폴더에 남기지 않음 — 새 판이 생기면 지우고 변경 대장(00_History)에 한 줄 + git 커밋으로 복원", "프로젝트_변경이력 '문서 통합'"),
         ("생성물", "빌드가 만드는 파일은 손으로 고치지 않음 — 원천(_source 또는 04 라이브러리)을 고치고 재생성", "문서 머리말에 '생성물' 표시"),
         ("문서 세트", "처음 만드는 전략 문서는 docx·xlsx·pptx 3종, 이후 갱신은 대표 형식 1개", "Word가 정본, Excel은 표, PPT는 요약"),
         ("ID", "라이브러리 LIB-xxx · 문헌 REF-### · 요청 REQ-YYYYMMDD-NN · 결정 CB-/CHG- · 절차 P## · 작업 BL-####", "REQ-20261122-01"),
         ("상태", "05_UserComments/STATUS.md가 '지금'을 대표 — 업데이트가 매번 다시 씀", "열린 요청·대기 결정·작업 목록"),
         ("보안·저작권", "유료 표준 원문은 링크·서지만, 공개·허가 원문만 files/에. 비밀값은 저장소에 두지 않음", "ISO 표준 → 링크"),
         ("Office 호환(전달 게이트)", "PPT·Word·Excel은 빌드 마지막 office_check.py(ID 범위·도형 ID 중복·음수 크기·참조·다시 열기)를 통과해야 전달. Windows에서는 install.bat → V(확인만)가 실제 Office로 열어 재확인", "FAIL이면 빌드 중단·전달 금지"),
         ("글꼴", "Windows·Office 기본 글꼴만 사용(맑은 고딕·Calibri·Cambria·Consolas) — 전달할 때 필요한 글꼴·프로그램을 의존성 문서(05_Dependencies)와 함께 알림", "설치 불필요 글꼴만")]
LIFECYCLE = [("요청", "01_Requests\nREQ-YYYYMMDD-NN.md"), ("결정", "패널 검토 화면 →\n02_Decisions/inbox"), ("반영", "업데이트\n해시 대조 → applied·conflicts"), ("상태", "STATUS.md\n대기·완료·충돌 한 장"), ("보관", "99_History ledger\n+ 00_History 대장")]
DOC_RULES = [(r"^(프로젝트_변경이력|문서관리_색인_)", "02_Strategy/00_History"), (r"^갱신전략_", "02_Strategy/01_Update"), (r"^분석전략_", "02_Strategy/02_Analysis"),
             (r"^(프로젝트구조_규약_|사용자전략_)", "02_Strategy/03_User"), (r"^(LLM전략_|프로젝트표준_)", "02_Strategy/04_LLM"), (r"^의존성_목록_", "02_Strategy/05_Dependencies")]
CHECK = ["최상위에 _source와 01~05, Main_<ID>.bat·install.bat·README·PROJECT.json만 있다", "Main_<ID>.bat이 프로젝트 홈(01_Panel/Home)을 먼저 연다", "폴더마다 README.md가 있다(목적·넣는 것·넣지 않는 것)", "03과 04가 같은 분류 번호를 쓴다",
         "04의 LIB-xxx 폴더마다 library.json이 있다", "_source에는 코드만 있다(데이터·읽기용 문서 없음)", "이전 판 사본이 없다 — 00_History 대장에 기록했다",
         "05_UserComments/STATUS.md가 최신이다", "유료 표준 원문을 03에 사본으로 두지 않았다", "PROJECT.json의 버전·패널 URL이 맞다",
         "Office 호환성 검사(office_check.py) 실패 0 — PPT·Word·Excel 전달 전 필수", "Windows에서 install.bat → V(확인만) 결과가 '모두 정상'이다(office_verify_report.txt)"]

def readme_head(t, s): return f"# {t}\n\n{s}\n\n> 이 파일은 `_source/strategy/content.py`(규약 project-structure/{STRUCT_VER}, `_source/build/template/contract.py`)에서 생성됩니다. 폴더 규칙을 바꾸려면 원천을 고친 뒤 빌드하세요.\n"
def readmes(pid="<ID>", cat_desc=None, ref_kinds=None, lib_lines=None, refs_src=None):
    """폴더 README — cat_desc{분류: 이 프로젝트의 내용}, ref_kinds{분류: 문헌 종류}, lib_lines{분류: [라이브러리 줄]}, refs_src: 문헌 원천 위치"""
    cat_desc = cat_desc or {}; ref_kinds = ref_kinds or {}; lib_lines = lib_lines or {}; R = {}
    for t in top(pid):
        if not t["path"].endswith("/") or t["path"] == "_source/": continue
        subs = [f"- `{p}` — {d} ({b})" for p, d, b in SUB if p.startswith(t["path"])]
        R[t["path"] + "README.md"] = readme_head(t["path"].rstrip("/"), t["role"]) + f"\n## 넣는 것\n{t['put']}\n\n## 넣지 않는 것\n{t['not']}\n\n## 작성·생성\n{t['by']}\n" + (("\n## 하위 폴더\n" + "\n".join(subs) + "\n") if subs else "")
    for c, n, d in CATS:
        dd = cat_desc.get(c, d)
        if c != "06_Methods":
            R[f"03_References/{c}/README.md"] = readme_head(f"03_References/{c} — {n}", f"{dd}의 원문 자료. 색인 `참고문헌_색인_{c}_v*.xlsx`와 `files/`(공개·허가된 원문, 파일 이름은 `REF-###_제목.pdf`).") + \
                (f"\n- 참고문헌 종류: {ref_kinds[c]}" if c in ref_kinds else "") + "\n- 유료 표준 원문은 사본을 두지 않고 링크·서지만 기록\n" + (f"- 새 문헌은 `{refs_src}`에 추가\n" if refs_src else "")
        R[f"04_Libraries/{c}/README.md"] = readme_head(f"04_Libraries/{c} — {n}", f"{dd}를 시스템이 쓰는 라이브러리로 정제한 곳. 원문은 `03_References/{c}`.") + \
            "\n## 라이브러리\n" + ("\n".join(lib_lines.get(c, [])) or "- (아직 없음)") + \
            "\n\n## 규칙\n- 라이브러리 폴더 하나 = `library.json` 하나(버전·파일·적재 테이블·의존)\n- 수정 → 검사 → 버전 올림(bump) → 빌드\n- 읽기용 카탈로그 `라이브러리_<이름>_v*.xlsx`는 생성물\n"
    R["01_Panel/Main/README.md"] = readme_head("01_Panel/Main — 메인 패널", "메인 분석 패널(온라인 게시본·오프라인판). 시작은 최상위 `Main_" + pid + ".bat`.")
    R["01_Panel/Sub/README.md"] = readme_head("01_Panel/Sub — 연계 분석 패널", "메인 패널(Main)과 연결되는 보조 패널 자리. 메인 패널의 탭이 커지면 Sub_1… 패널로 분리합니다.")
    R["01_Panel/Home/README.md"] = readme_head("01_Panel/Home — 프로젝트 홈(첫 패널)", "폴더·파일 지도(트리·목록), 파일마다 의미와 마지막 업데이트 날짜, 메인 패널·주요 문서 바로가기. `Main_" + pid + ".bat`이 이 화면을 먼저 엽니다(생성기 `_source/build/template/home.py`).")
    for k, (p, d, _) in enumerate([x for x in SUB if x[0].startswith("02_Strategy/")]):
        R[p + "README.md"] = readme_head(p.rstrip("/"), d)
    R["05_UserComments/01_Requests/README.md"] = readme_head("01_Requests — 사용자 요청", "요청 1건 = md 1개. 이름 `REQ-YYYYMMDD-NN_<짧은 제목>.md`.") + \
        "\n## 양식\n```\n# REQ-YYYYMMDD-NN 제목\n- 상태: 접수 | 진행 | 완료 | 보류\n- 요청일: YYYY-MM-DD · 요청자:\n- 관련: (폴더·라이브러리·패널 탭)\n\n## 요청\n\n## 결정·선택(Step)\n\n## 처리 결과(버전·커밋)\n```\n완료된 요청은 다음 업데이트 때 `99_History/`로 옮기고 STATUS.md에서 빠집니다.\n"
    R["05_UserComments/02_Decisions/README.md"] = R.get("05_UserComments/02_Decisions/README.md") or readme_head("02_Decisions — 패널 결정 묶음", "패널 검토 화면에서 보낸 결정 묶음(customize/1.0). inbox → applied | conflicts. 업데이트가 결정 당시 해시를 대조해 반영합니다.")
    R["05_UserComments/03_Prompts/README.md"] = readme_head("03_Prompts — 프롬프트·관리 스크립트", "LLM이 실행하는 프롬프트의 원문. 실제 등록본(예약 작업 등)과 같게 유지하고, 바꾸면 02_Strategy/04_LLM과 변경 대장에 기록합니다.")
    R["05_UserComments/99_History/README.md"] = readme_head("99_History — 처리 이력", "`ledger.jsonl`(결정 적용 1줄 1건, append only)과 완료된 요청 md를 보관합니다.")
    return R

def structure_doc(name, pid, V, cat_rows=None, extra_sections=(), extra_sheets=(), extra_slides=(), panel_items=("Home", "Main", "Sub_1", "Sub_2")):
    """프로젝트 구조 규약 문서 세트(docset/1.0). cat_rows: [[분류, 이름, 내용, 참고 종류, 문헌 수]] — 없으면 일반 설명"""
    T = top(pid); cat_rows = cat_rows or [[c, n, d, "—", 0] for c, n, d in CATS]
    ch = ["분류", "이름", "이 프로젝트의 내용", "참고문헌 종류", "문헌 수"]
    return {"id": "structure", "file": f"프로젝트구조_규약_v{STRUCT_VER}", "version": STRUCT_VER, "owner": "J.K. Lee",
     "title": "프로젝트 표준 구조 규약", "subtitle": "모든 프로젝트가 같은 5개 폴더 + _source로 움직이는 방법",
     "purpose": "프로젝트마다 폴더가 달라 생각과 자료가 흩어지는 문제를 막는다. 사람(패널·문서)과 시스템(LLM·빌드)이 같은 위치에서 같은 것을 찾도록 최상위 역할·하위 폴더·이름·이력 규칙을 고정한다.",
     "summary": ["최상위는 _source(시스템 컨트롤러)와 01~05(사용자 쪽) 다섯 폴더 — Panel·Strategy·References·Libraries·UserComments, 파일은 Main_<ID>.bat·install.bat·README·PROJECT.json",
                 "시작은 프로젝트 홈(01_Panel/Home) — 폴더·파일 지도와 업데이트 날짜를 먼저 보고 메인 패널로 들어간다",
                 "정보 흐름: References(원문) → Libraries(정제) → Panel, Strategy → Panel, UserComments → 다음 업데이트(피드백 루프)",
                 "03 References와 04 Libraries는 같은 분류(00_Core~05_New_Strategies, 라이브러리 전용 06_Methods)를 써서 원문 → 정제 추적을 폴더로 보장",
                 "이전 판은 사본으로 두지 않고 02_Strategy/00_History 변경 대장 + git으로 관리, 현재 상태는 05_UserComments/STATUS.md",
                 "새 프로젝트는 _source/build/template/new_project.py로 같은 골격·README·PROJECT.json을 만들어 시작"],
     "sections": [
      {"h": "1. 적용 범위", "p": [f"이 규약(project-structure/{STRUCT_VER})은 {name} {V}에 적용하며, 모든 프로젝트의 기본 골격이다. 프로젝트 고유 내용은 하위 폴더(분류·문서 이름)에서만 달라진다."]},
      {"h": "2. 최상위 구조와 역할", "table": {"head": ["위치", "역할", "넣는 것", "넣지 않는 것", "작성·생성"], "rows": [[t["path"], t["role"], t["put"], t["not"], t["by"]] for t in T]}},
      {"h": "3. 정보 흐름", "bullets": ["**References → Libraries (가장 중요)**: 원문을 시스템이 쓰는 구조(JSON)로 정제. 같은 분류 폴더라 어느 원문이 어느 라이브러리가 됐는지 바로 보인다",
                                      "**Libraries → Panel / Strategy → Panel**: 패널은 라이브러리 데이터와 전략 문서의 기준을 읽어 화면을 만든다",
                                      "**Strategy ⇄ References**: 전략이 필요한 원문을 정하고, 원문이 전략을 고친다", "**References → Panel(코멘트)**: 패널의 근거 표시는 원문 서지·링크로 연결",
                                      "**UserComments → 프로젝트(피드백 루프)**: 사용자의 요청·결정이 다음 업데이트의 입력이 된다", "**_source**: 모든 연결 고리를 실행하는 코드(빌드·검사·패널 조립·자동 갱신)"]},
      {"h": "4. 하위 폴더", "table": {"head": ["폴더", "내용", "작성·생성"], "rows": [list(x) for x in SUB]}},
      {"h": "5. 분류 체계(03·04 공통)", "p": ["분류 번호는 프로젝트가 달라도 같다. 비어 있는 분류도 README로 자리를 유지한다."], "table": {"head": ch, "rows": cat_rows}},
      {"h": "6. 이름·버전·이력 규칙", "table": {"head": ["규칙", "내용", "예"], "rows": [list(r) for r in RULES]}},
      {"h": "7. 사용자 코멘트 수명주기(05_UserComments)", "steps": [f"{k}: {d.replace(chr(10), ' ')}" for k, d in LIFECYCLE]},
      *extra_sections,
      {"h": f"{8 + len(extra_sections)}. 새 프로젝트 시작", "code": ["cd <저장소>/_source", "python3 build/template/new_project.py <새 폴더> --id ABC --name \"프로젝트 이름\" --owner \"J.K. Lee\""],
       "p": ["골격(5개 폴더·분류·하위 폴더)·폴더별 README·PROJECT.json·STATUS.md·요청 양식·Main_<ID>.bat, 그리고 이 규약과 문서 세트 생성기(_source/build/strategy)를 함께 만든다. 새 프로젝트에서 `python3 build/strategy/docset.py --version v0.1`을 실행하면 이 규약 문서 세트가 그 프로젝트 이름으로 생성된다."]}],
     "sheets": [
      {"name": "최상위", "title": "최상위 구조와 역할", "head": ["위치", "역할", "넣는 것", "넣지 않는 것", "작성·생성"], "rows": [[t["path"], t["role"], t["put"], t["not"], t["by"]] for t in T], "widths": [18, 40, 46, 30, 16], "height": 34},
      {"name": "하위 폴더", "title": "하위 폴더", "head": ["폴더", "내용", "작성·생성"], "rows": [list(x) for x in SUB], "widths": [32, 70, 18]},
      {"name": "분류", "title": "03·04 공통 분류", "head": ch, "rows": cat_rows, "widths": [20, 12, 40, 30, 9], "center": [5]},
      {"name": "규칙", "title": "이름·버전·이력 규칙", "head": ["규칙", "내용", "예"], "rows": [list(r) for r in RULES], "widths": [14, 80, 40], "height": 30},
      *extra_sheets,
      {"name": "점검표", "title": "새 프로젝트·구조 변경 점검표", "head": ["#", "확인 항목", "확인"], "rows": [[i, t.replace("<ID>", pid), "☐"] for i, t in enumerate(CHECK, 1)], "widths": [5, 90, 8], "center": [1, 3]}],
     "slides": [
      {"kind": "title", "title": "프로젝트 표준 구조", "sub": "5개 폴더 + _source — 모든 프로젝트 공통 골격", "meta": f"project-structure/{STRUCT_VER} · {name} {V}"},
      {"kind": "structure", "title": "한 장 구조 — 사람은 01~05, 시스템은 _source", "kicker": "Architecture", "banner": "프로젝트 (_source로 구현)", "base": "User · LLM Strategy base",
       "folders": {"strategy": {"title": "02_Strategy", "role": "전략·결과를 문서로(docx·xlsx·pptx)", "items": ["00_History (Change Manager)", "01_Update", "02_Analysis", "03_User", "04_LLM", "05_Dependencies"]},
                   "references": {"title": "03_References", "role": "실제 원문 · 링크 · 법규 · 표준", "items": [c for c, _, _ in CATS[1:6]]}, "panel": {"title": "01_Panel", "role": "사용자 중심 컨트롤러 — 첫 화면은 Home", "items": list(panel_items)},
                   "libraries": {"title": "04_Libraries", "role": "References를 시스템용으로 정제(같은 분류)", "items": [c for c, _, _ in CATS[1:6]] + ["06_Methods"]},
                   "comments": {"title": "05_UserComments", "role": "요청·결정 → 현재 상태 → 다음 업데이트", "items": ["STATUS.md", "01_Requests", "02_Decisions", "03_Prompts", "99_History"]}},
       "legend": [["Panel", "사용자 중심 컨트롤러 — 전략·결과·새 입력"], ["Strategy", "전략·결과를 문서로(docx·xlsx·pptx)"], ["References", "실제 원문·링크·법규·표준"], ["Libraries", "References를 시스템용으로 정제(같은 분류)"], ["UserComments", "요청·결정 → 현재 상태 → 다음 업데이트"], ["_source", "시스템 중심 컨트롤러(코드만)"]],
       "notes": "굵은 화살표가 구현에 필요한 핵심 전달입니다. 가장 굵은 것은 References에서 Libraries로 가는 정제 흐름입니다. 사용자 코멘트는 다음 업데이트로 다시 들어가는 루프입니다."},
      {"kind": "table", "title": "폴더별 하위 구조", "head": ["폴더", "하위", "작성·생성"], "rows": [list(x) for x in SUB], "colW": [3.6, 6.9, 1.6], "rowH": 0.36, "fontSize": 10.5},
      {"kind": "cards", "title": "03·04 공통 분류 — 원문과 라이브러리가 같은 번호", "cards": [[r[0], r[1], r[2] + (f"\n문헌 {r[4]}건" if r[4] else "")] for r in cat_rows[:4]],
       "foot": "04_Other_Projects · 05_New_Strategies는 비어 있어도 자리를 유지, 06_Methods는 라이브러리 전용(계산 방법)", "h": 2.6},
      {"kind": "flow", "title": "사용자 코멘트 수명주기 — 항상 '지금' 상태가 남는다", "steps": [list(x) for x in LIFECYCLE]},
      *extra_slides,
      {"kind": "bullets", "title": "규칙 네 가지", "items": [["이름", "폴더 NN_English · 파일 한글_제목_vX.Y — 파일명 버전 유지"], ["이력", "이전 판 사본 금지 → 00_History 대장 한 줄 + git으로 복원"], ["생성물", "빌드 산출물은 손대지 않음 — 원천(_source·04 LIB)만 수정"], ["문서 세트", "처음은 docx·xlsx·pptx 3종, 이후 갱신은 대표 1종"]]},
      {"kind": "flow", "title": "다른 프로젝트에 적용 — 같은 골격으로 시작", "steps": [["new_project.py", "골격·README·PROJECT.json\nSTATUS·요청 양식"], ["References", "원문 서지·링크를\n분류별 색인에"], ["Libraries", "필요한 것만\nLIB-xxx로 정제"], ["Panel·Strategy", "패널 Main + 문서 세트\n(docset 생성기)"], ["UserComments", "요청·결정으로\n다음 업데이트"]],
       "foot": "규약 원천: _source/build/template/contract.py — 규약을 바꾸면 PPT·Word·Excel·폴더 README·PROJECT.json이 함께 바뀐다"}]}
