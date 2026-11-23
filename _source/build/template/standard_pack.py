# -*- coding: utf-8 -*-
"""프로젝트 표준 적용 팩(project-structure 규약 → 다른 프로젝트에 올리는 설명 파일·지침·프롬프트·키트) 생성기 — 프로젝트 공통.
  python3 build/template/standard_pack.py            → 02_Strategy/04_LLM/
    프로젝트표준_설명_v<규약>.md (+ .docx)   다른 프로젝트의 '프로젝트 지식'에 올리는 규약 전문(LLM이 읽는 정본, 사람용 Word 동봉)
    프로젝트표준_지침_v<규약>.md             프로젝트 '지침(Custom instructions)'에 붙여 넣는 짧은 상시 규칙
    프로젝트표준_프롬프트_v<규약>.md         첫 메시지로 쓰는 프롬프트 4종(기존 전환·새 시작·세션 시작·전달 전 점검)
    프로젝트표준_키트_v<규약>.zip            코드 실행 환경(Claude Code·작업 세션)용 생성기 묶음 — new_project.py로 같은 골격
원천은 contract.py(규약)·deps.json(글꼴·Office) — 규약을 바꾸면 이 팩도 함께 바뀐다. 손으로 고치지 말 것."""
import os, sys, json, zipfile, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); BUILD = os.path.dirname(HERE); ROOT = os.path.dirname(BUILD); BUNDLE = os.path.dirname(ROOT)
sys.path.insert(0, HERE); import contract as K
V = K.STRUCT_VER; OUT = os.path.join(BUNDLE, "02_Strategy", "04_LLM")
KIT = ["template/contract.py", "template/new_project.py", "template/deps.py", "template/home.py", "template/office_check.py", "template/standard_pack.py",
       "strategy/docset.py", "strategy/docset_pptx.js", "strategy/bg.py", "db/md2docx.py", "db/xlsx_style.py", "pdf/reference.docx"]

def proj():
    p = os.path.join(BUNDLE, "PROJECT.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {"id": "PRJ", "name": "프로젝트", "repo": ""}

def fonts():
    p = os.path.join(BUILD, "deps.json")
    d = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
    return d.get("fonts", []), d.get("office", {})

def tbl(head, rows):
    e = lambda s: str(s).replace("|", "\\|").replace("\n", " ")
    return "\n".join(["| " + " | ".join(head) + " |", "|" + "---|" * len(head)] + ["| " + " | ".join(e(c) for c in r) + " |" for r in rows]) + "\n"

def desc(P):
    F, O = fonts(); T = K.top("<ID>")
    L = [f"# 프로젝트 표준 구조 — 설명 파일 (project-structure/{V})", "",
         f"> 생성물 — 원천 `_source/build/template/contract.py`(규약)·`standard_pack.py`(이 팩), 기준 저장소 `{P.get('repo', '')}`. 손으로 고치지 말고 원천을 고친 뒤 다시 만든다.",
         "> 이 파일은 **다른 프로젝트의 '프로젝트 지식'에 올려 LLM이 읽는 정본**이다. 사람이 보는 그림은 같은 원천에서 만든 `프로젝트구조_규약_v1.0.pptx`·`.docx`.", "",
         "## 0. 이 파일을 읽는 LLM에게", "",
         "1. 이 프로젝트의 모든 파일·폴더·산출물은 아래 규약을 따른다. 규약과 다른 요청을 받으면 그대로 하되 **어긋나는 지점을 한 줄로 알린다**.",
         "2. 작업을 시작할 때는 `PROJECT.json` → `05_UserComments/STATUS.md` → 관련 폴더의 `README.md` 순서로 읽는다(없으면 0~1단계 전환부터).",
         "3. 구조를 바꾸거나 자료를 옮기는 제안은 **Step 선택지(각 Step에 '권장' 표시)**로 먼저 보여 주고, 사용자가 고른 뒤에 실행한다.",
         "4. PPT·Word·Excel은 **Office 호환성 검사를 통과한 뒤에만 전달**하고, 필요한 글꼴·프로그램을 함께 알린다(9절).", "",
         "## 1. 한 줄 요약", "", "최상위는 **`_source`(시스템 중심 컨트롤러, 코드만)**와 사용자 쪽 **5개 폴더(01_Panel·02_Strategy·03_References·04_Libraries·05_UserComments)**. "
         "원문(03)을 정제한 라이브러리(04)와 전략 문서(02)를 패널(01)이 읽고, 사용자 결정(05)이 다음 업데이트로 돌아간다.", "",
         "```", "<프로젝트>/", "├─ Main_<ID>.bat      시작 — 프로젝트 홈(01_Panel/Home) → 메인 패널", "├─ install.bat        의존성 설치 · V(확인만) = 글꼴·Office 열기 시험",
         "├─ README.txt  PROJECT.json", "├─ _source/           코드만(생성기·패널 원천·자동 갱신·문서 원천 strategy/)", "├─ 01_Panel/          Home · Main · Sub",
         "├─ 02_Strategy/       00_History · 01_Update · 02_Analysis · 03_User · 04_LLM · 05_Dependencies", "├─ 03_References/     00_Core … 05_New_Strategies (색인 + files/)",
         "├─ 04_Libraries/      00_Core … 05_New_Strategies + 06_Methods (LIB-xxx/library.json)", "└─ 05_UserComments/   STATUS.md · 01_Requests · 02_Decisions · 03_Prompts · 99_History", "```", "",
         "## 2. 최상위 구조와 역할", "", tbl(["위치", "역할", "넣는 것", "넣지 않는 것", "작성·생성"], [[t["path"], t["role"], t["put"], t["not"], t["by"]] for t in T]),
         "## 3. 정보 흐름(굵기 = 중요도)", "",
         "- **References → Libraries (가장 중요)**: 원문을 시스템이 쓰는 구조(JSON)로 정제. 같은 분류 번호라 어느 원문이 어느 라이브러리가 됐는지 폴더로 보인다.",
         "- **Libraries → Panel, Strategy → Panel**: 패널은 라이브러리 데이터와 전략 문서의 기준을 읽어 화면을 만든다.",
         "- **Strategy ⇄ References**: 전략이 필요한 원문을 정하고, 원문이 전략을 고친다. **References → Panel**: 근거 표시는 원문 서지·링크로.",
         "- **UserComments → 다음 업데이트(피드백 루프)**: 요청·결정이 다음 빌드의 입력. **_source**: 이 모든 연결을 실행하는 코드.", "",
         "## 4. 하위 폴더", "", tbl(["폴더", "내용", "작성·생성"], [list(x) for x in K.SUB]),
         "## 5. 분류 체계(03·04 공통 번호)", "", tbl(["분류", "이름", "넣는 것"], [list(c) for c in K.CATS]),
         "**분류 판정 순서**: ① 프로젝트 내부 기준(용어·아키텍처·절차·고정 문안) → 00_Core ② 표준·법·규정·인증 → 01 ③ 통계·데이터셋·관측 → 02 ④ 논문·특허·연구 보고서 → 03 "
         "⑤ 다른 기관·과제 산출물 → 04 ⑥ 아직 검증 전인 새 방법·프레임워크 → 05 ⑦ 계산·판정 방법(라이브러리 전용) → 06. 둘 이상이면 **원문의 성격**(누가 냈나)으로 정한다. 비어 있는 분류도 README로 자리를 유지한다.", "",
         "## 6. 이름·버전·이력 규칙", "", tbl(["규칙", "내용", "예"], [list(r) for r in K.RULES]),
         "**문서 위치(파일 이름 접두어 → 폴더)**", "", tbl(["접두어(정규식)", "폴더"], [[p, d] for p, d in K.DOC_RULES]),
         "## 7. 사용자 코멘트 수명주기(05_UserComments)", "", *[f"{i}. **{k}** — {d.replace(chr(10), ' ')}" for i, (k, d) in enumerate(K.LIFECYCLE, 1)], "",
         "요청 양식(`01_Requests/REQ-YYYYMMDD-NN_<짧은 제목>.md`):", "", "```", "# REQ-YYYYMMDD-NN 제목", "- 상태: 접수 | 진행 | 완료 | 보류", "- 요청일: YYYY-MM-DD · 요청자:",
         "- 관련: (폴더·라이브러리·패널 탭)", "", "## 요청", "", "## 결정·선택(Step)", "", "## 처리 결과(버전·커밋)", "```", "",
         "## 8. PROJECT.json — 시스템이 가장 먼저 읽는 파일", "", "```json",
         json.dumps({"schema": "project/1.0", "id": "<ID>", "name": "<프로젝트 이름>", "version": "v0.1", "structure": {"contract": f"project-structure/{V}", "doc": f"02_Strategy/03_User/프로젝트구조_규약_v{V}.docx"},
                     "owner": "J.K. Lee", "repo": "<owner/repo 또는 빈 값>", "branch": "claude/main", "panel_url": "<게시 패널 URL 또는 빈 값>", "entry": "Main_<ID>.bat",
                     "folders": {f: "<이 프로젝트에서의 내용>" for f in K.FOLDERS}, "libraries": [{"id": "LIB-xxx", "version": "1.0", "category": "00_Core", "path": "04_Libraries/00_Core/LIB-xxx"}],
                     "status": "05_UserComments/STATUS.md", "history": "02_Strategy/00_History/프로젝트_변경이력_v0.1.xlsx"}, ensure_ascii=False, indent=1), "```", "",
         "비밀값(토큰·비밀번호·개인 정보)은 넣지 않는다.", "",
         "## 9. 산출물 전달 게이트(전 프로젝트 필수)", "",
         "- **Office 호환성 검사**: PPT·Word·Excel은 생성 직후 `python3 _source/build/template/office_check.py --fonts`를 통과해야 전달한다(실패면 빌드 중단). "
         "검사·보정 항목: 슬라이드 ID 범위(sldId 256~2147483647, 마스터·레이아웃 2147483648 이상 — 낮추면 스키마 위반), 도형 ID 중복, 음수 크기 도형, 끊어진 참조, 형식 등록, 다시 열기.",
         "- **미리보기를 믿지 않는다**: LibreOffice 미리보기가 정상이어도 PowerPoint는 '열 수 없음/복구'를 띄울 수 있다.",
         "- **Windows 최종 확인**: 사용자 PC에서 `install.bat` → **V(확인만)** — 실제 PowerPoint·Word·Excel로 모든 파일을 읽기 전용으로 열고 글꼴을 확인, 결과 `02_Strategy/05_Dependencies/office_verify_report.txt`.",
         "- **전달 메시지에 함께 적을 것**: 검사 결과(통과 여부), 필요한 프로그램, 필요한 글꼴(아래), Windows 확인 방법.", "",
         f"필요한 프로그램: {O.get('name', 'Microsoft Office(PowerPoint·Word·Excel)')} {O.get('min', '2016')} 이상 — {O.get('note', '')}", "",
         tbl(["글꼴", "구분", "어디에 쓰나", "설치"], [[f["name"], f["need"], f["used"], f["source"]] for f in F]) if F else "",
         "## 10. 작업 방식(사용자와 합의된 기본값)", "",
         "- 구조 변경·자료 이동·새 형식은 **Step 선택지 + 권장 표시**로 먼저 묻는다(질문 한 번에 여러 Step 가능).",
         "- 전략 문서는 **처음 만들 때 docx·xlsx·pptx 3종**, 이후 갱신은 **대표 형식 1종**(Word가 정본, Excel은 표, PPT는 요약).",
         "- 읽기용 참고 문서는 md·json이 아니라 **Word·Excel·PPT**로 전달한다(LLM용 설명·프롬프트 파일은 예외 — 이 팩처럼 md).",
         "- 이전 판은 **사본을 남기지 않고** 00_History 변경 대장 한 줄 + git으로 관리한다. 파일 이름의 `_vX.Y`는 유지한다.",
         "- 생성물은 손으로 고치지 않는다 — 원천(`_source`·04 라이브러리)을 고치고 다시 만든다.",
         "- 유료 표준 원문은 사본을 두지 않고 서지·링크만. 비밀값은 저장소에 두지 않는다.", "",
         "## 11. 점검표(새 프로젝트·구조 변경 후)", "", *[f"- [ ] {c}" for c in K.CHECK], "",
         "## 12. 적용 방법 — 실행 환경별", "",
         tbl(["환경", "할 수 있는 것", "방법"], [
             ["코드 실행 가능(Claude Code·작업 세션)", "골격·README·PROJECT.json·문서 세트를 실제로 생성, Office 검사", f"`프로젝트표준_키트_v{V}.zip` 풀기 → `python3 _source/build/template/new_project.py <폴더> --id <ID> --name \"<이름>\"` → `docset.py --version v0.1`"],
             ["채팅만(코드 실행 없음)", "구조 설계·이동표·README·PROJECT.json·STATUS.md 초안을 텍스트로", "이 설명 파일 + 프롬프트 A/B로 진행, 파일 생성은 다음에 코드 환경에서"],
             ["GitHub 저장소 연결", "기준 생성기를 직접 가져오기", f"`{P.get('repo', '')}` (브랜치 `claude/main`)의 `_source/build/template/`"]]),
         "## 13. 왜 PPT가 아니라 설명 파일·프롬프트·스크립트인가", "",
         tbl(["기준", "PPT를 올림", "설명 파일(md) + 프롬프트 + 키트"], [
             ["LLM이 읽는 정확도", "슬라이드 텍스트만 추출 — 도형·화살표·배치 의미가 사라지고 표가 흩어짐", "표·규칙·예시가 그대로 — 해석 여지 적음"],
             ["실행", "읽고 따라 만들어야 함(사람마다 다른 결과)", "new_project.py가 같은 골격을 만듦 — 재현 가능"],
             ["지식 용량", "그림·배경 이미지로 무겁고 텍스트는 요약뿐", "필요한 규칙만, 작음"],
             ["갱신", "규약이 바뀌면 PPT를 다시 올려야 하고 어느 판인지 모호", "같은 원천(contract.py)에서 생성 — 버전이 파일명에"],
             ["사람에게 설명", "가장 좋음(한 장 구조도)", "보조 — 사람에게는 PPT·Word를 함께 둔다"]]),
         "결론: **LLM에게는 설명 파일 + 지침 + 프롬프트(+ 코드 환경이면 키트)**, **사람에게는 PPT·Word**. 둘 다 같은 원천에서 생성되므로 내용이 어긋나지 않는다.", ""]
    return "\n".join(L)

def instr(P):
    return "\n".join([f"# 프로젝트 지침 — 표준 구조 project-structure/{V}", "",
        "> 프로젝트 설정의 '지침(Custom instructions)' 칸에 아래 구분선 사이를 그대로 붙여 넣는다. `<…>`만 이 프로젝트 값으로 바꾼다.", "", "---", "",
        f"이 프로젝트(<프로젝트 이름>, ID <ID>)는 J.K. Lee의 공통 프로젝트 표준 구조(project-structure/{V})를 따른다. 상세 규약은 프로젝트 지식의 `프로젝트표준_설명_v{V}.md`가 정본이다.", "",
        "항상 지킬 것:",
        "1. 최상위 = `_source`(코드만) + `01_Panel` `02_Strategy` `03_References` `04_Libraries` `05_UserComments` + `Main_<ID>.bat` `install.bat` `README.txt` `PROJECT.json`.",
        "2. 작업 시작 시 `PROJECT.json` → `05_UserComments/STATUS.md` → 관련 README 순서로 상태를 파악한다. 아직 전환 전이면 그 사실을 먼저 알린다.",
        "3. 원문은 03_References, 정제한 데이터는 04_Libraries(같은 분류 번호 00_Core~05_New_Strategies, 계산 방법은 06_Methods), 읽기용 문서는 02_Strategy, 사용자 요청·결정은 05_UserComments.",
        "4. 폴더 `NN_English`, 파일 `한글_제목_vX.Y.확장자`(버전 유지). 이전 판 사본을 남기지 않고 02_Strategy/00_History 변경 대장 + git으로 관리한다.",
        "5. 생성물은 손으로 고치지 않는다 — 원천을 고치고 다시 만든다.",
        "6. 구조 변경·자료 이동·새 형식은 Step 선택지(각 Step에 '권장' 표시)로 먼저 묻고, 고른 뒤 실행한다.",
        "7. 전략 문서는 처음 만들 때 docx·xlsx·pptx 3종, 이후 갱신은 대표 형식 1종. 읽기용 참고 문서는 Word·Excel·PPT로 전달한다.",
        "8. PPT·Word·Excel은 Office 호환성 검사(office_check.py, 실패 0)를 통과한 뒤에만 전달하고, 검사 결과·필요한 프로그램(Microsoft Office 2016+)·글꼴(맑은 고딕·Calibri·Cambria — Windows·Office 기본)·Windows 확인 방법(install.bat → V)을 함께 알린다.",
        "9. 유료 표준 원문은 사본 없이 서지·링크만. 비밀값·개인 정보는 저장소·PROJECT.json에 두지 않는다.",
        "10. 요청 1건 = `05_UserComments/01_Requests/REQ-YYYYMMDD-NN_<제목>.md`, 끝나면 STATUS.md를 갱신한다.", "", "---", ""])

def prompts(P):
    rp = P.get("repo", "")
    A = ["## A. 기존 프로젝트를 표준 구조로 전환(그 프로젝트의 첫 메시지)", "", "```text",
         f"이 프로젝트를 공통 표준 구조(project-structure/{V})로 전환해줘. 규약 정본은 프로젝트 지식의 프로젝트표준_설명_v{V}.md야.",
         "프로젝트 이름: <이름> / ID: <영문 대문자 2~5자> / 저장소: <owner/repo 또는 없음>", "",
         "진행 방식:",
         "0) 인벤토리 — 이 프로젝트의 지식 파일·이전 대화의 산출물·(연결돼 있으면) 저장소 파일을 목록으로 만들어. 각 항목: 이름 · 종류(원문/정제 데이터/읽기용 문서/코드/사용자 결정) · 최신 여부.",
         "1) 이동표 — 항목마다 새 위치(폴더·분류 번호·새 파일 이름 한글_제목_vX.Y)를 제안해. 같은 문서의 여러 판은 최신 1개만 남기고 나머지는 '00_History 대장 기록'으로 표시.",
         "2) Step 선택지 — 판단이 갈리는 곳(분류가 애매한 자료, 라이브러리로 정제할 범위, 패널 필요 여부, 문서 3종 세트 대상 등)을 Step 1, 2, …로 묶어 각 Step에 선택지와 '권장'을 표시해서 먼저 물어봐. 내가 고르기 전에는 바꾸지 마.",
         "3) 골격 생성 — 코드 실행이 되면 프로젝트표준_키트 zip의 new_project.py로 만들고, 안 되면 폴더 트리·README·PROJECT.json·STATUS.md를 텍스트 초안으로 만들어.",
         "4) 이동·기록 — 이동표대로 옮기고 02_Strategy/00_History 변경 대장에 '이전 위치 → 새 위치 · 사유'를 남겨. 사본은 만들지 마.",
         "5) 문서 — 02_Strategy/03_User에 이 프로젝트 이름으로 구조 규약 문서 세트(docx·xlsx·pptx, 처음이므로 3종)를 만들어.",
         "6) 점검 — 설명 파일 11절 점검표를 채우고, Office 파일은 office_check.py로 검사해(실패 0이어야 전달).",
         "7) 전달 — 결과 요약, 점검표, 남은 결정, 필요한 프로그램·글꼴·Windows 확인 방법(install.bat → V)을 알려줘.", "```", ""]
    B = ["## B. 새 프로젝트 시작", "", "```text",
         f"새 프로젝트를 공통 표준 구조(project-structure/{V})로 시작해줘. 규약 정본은 프로젝트 지식의 프로젝트표준_설명_v{V}.md야.",
         "프로젝트 이름: <이름> / ID: <ID> / 목적: <한두 문장> / 저장소: <owner/repo 또는 없음>",
         "1) 목적을 보고 03·04 분류마다 무엇이 들어갈지, 첫 라이브러리(LIB-xxx) 후보와 패널 탭 후보를 Step 선택지(권장 표시)로 먼저 보여줘.",
         "2) 고른 뒤 new_project.py(키트)로 골격을 만들고 PROJECT.json·STATUS.md·첫 요청 REQ를 채워. 코드 실행이 안 되면 텍스트 초안으로.",
         "3) docset.py로 구조 규약 문서 세트(3종)를 만들고 office_check.py를 통과시킨 뒤, 필요한 프로그램·글꼴과 함께 전달해줘.", "```", ""]
    C = ["## C. 작업 세션 시작(전환 후 매번)", "", "```text",
         "PROJECT.json과 05_UserComments/STATUS.md를 먼저 읽고 현재 버전·열린 요청·대기 결정·작업 목록을 5줄 이내로 요약해줘.",
         "그 다음 오늘 요청: <요청>. 구조나 형식을 바꾸는 부분이 있으면 Step 선택지(권장 표시)로 먼저 물어봐.", "```", ""]
    D = ["## D. 산출물 전달 전 점검", "", "```text",
         "전달하기 전에 확인해줘:",
         "1) office_check.py --fonts 결과(실패 0, 보정 내역, 사용 글꼴)",
         "2) 바뀐 파일이 규약 위치·이름(한글_제목_vX.Y)에 맞는지, 이전 판 사본이 없는지, 00_History 대장에 기록했는지",
         "3) STATUS.md·PROJECT.json 버전이 맞는지",
         "4) 전달 메시지에 필요한 프로그램(Microsoft Office 2016+)·글꼴·Windows 확인 방법(install.bat → V)을 넣었는지", "```", ""]
    head = [f"# 프로젝트 표준 — 프롬프트 (project-structure/{V})", "",
            "> 다른 프로젝트에서 **첫 메시지로 붙여 넣는** 프롬프트. `<…>`만 바꾼다. 상시 규칙은 `프로젝트표준_지침`, 규약 전문은 `프로젝트표준_설명`(둘 다 프로젝트에 먼저 올려 둘 것).", "",
            "준비(프로젝트마다 한 번):", "",
            f"1. 프로젝트 지식에 `프로젝트표준_설명_v{V}.md` 올리기(사람용으로 `프로젝트구조_규약_v{V}.pptx`도 함께 올려도 됨 — LLM은 md를 정본으로 읽는다).",
            f"2. 프로젝트 지침에 `프로젝트표준_지침_v{V}.md`의 구분선 사이 붙여 넣기.",
            f"3. 코드 실행 환경에서 작업할 프로젝트라면 `프로젝트표준_키트_v{V}.zip`도 올리기" + (f"(또는 저장소 `{rp}`를 연결)." if rp else "."), "",
            "| 상황 | 쓸 프롬프트 |", "|---|---|", "| 자료가 이미 있는 프로젝트 | A |", "| 비어 있는 새 프로젝트 | B |", "| 전환한 뒤 평소 작업 | C |", "| 파일을 받기 전 | D |", ""]
    return "\n".join(head + A + B + C + D)

def kit(path):
    readme = "\n".join([f"프로젝트 표준 키트 (project-structure/{V}) — 생성물(_source/build/template/standard_pack.py)", "",
        "1) 이 zip을 빈 작업 폴더에 푼다(안에 _source/build/... 구조가 들어 있음)",
        "2) python3 _source/build/template/new_project.py <새 프로젝트 폴더> --id ABC --name \"프로젝트 이름\" --owner \"J.K. Lee\" [--repo owner/repo]",
        "3) cd <새 프로젝트 폴더>/_source && python3 build/strategy/docset.py --version v0.1",
        "   → 02_Strategy/03_User/프로젝트구조_규약_v1.0.(docx|xlsx|pptx) 생성 + Office 호환성 검사 자동 실행",
        "필요: Python 3.10+(openpyxl, python-docx, Pillow) · Node 18+(pptxgenjs) · pandoc — 새 프로젝트의 install.bat이 설치·확인", ""])
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:              # 고정 날짜 — 내용이 같으면 같은 zip
        def add(name, data):
            zi = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0)); zi.compress_type = zipfile.ZIP_DEFLATED; zi.external_attr = 0o644 << 16; z.writestr(zi, data)
        add("README_KIT.txt", readme.encode("utf-8"))
        for rel in KIT:
            src = os.path.join(BUILD, rel)
            if os.path.exists(src): add("_source/build/" + rel, open(src, "rb").read())

def main():
    P = proj(); os.makedirs(OUT, exist_ok=True)
    files = {f"프로젝트표준_설명_v{V}.md": desc(P), f"프로젝트표준_지침_v{V}.md": instr(P), f"프로젝트표준_프롬프트_v{V}.md": prompts(P)}
    for n, t in files.items(): open(os.path.join(OUT, n), "w", encoding="utf-8").write(t)
    kit(os.path.join(OUT, f"프로젝트표준_키트_v{V}.zip"))
    md2 = os.path.join(BUILD, "db", "md2docx.py")                              # 사람용 Word(같은 내용)
    if os.path.exists(md2): subprocess.run([sys.executable, md2, os.path.join(OUT, f"프로젝트표준_설명_v{V}.md"), f"프로젝트표준_설명_v{V}.docx"], check=True, stdout=subprocess.DEVNULL)
    print("saved 02_Strategy/04_LLM/프로젝트표준_{설명.md·설명.docx·지침.md·프롬프트.md·키트.zip}" + f" v{V}")

if __name__ == "__main__": main()
