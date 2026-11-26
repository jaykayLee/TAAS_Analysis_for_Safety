# 작업 규칙 (Claude)

- 사용자와는 한국어로 대화합니다.
- **이 프로젝트는 공통 표준 구조(project-structure/1.0, ID `TAAS`)를 따릅니다.** 작업 시작 시 `PROJECT.json` → `05_UserComments/STATUS.md` → 관련 폴더 README 순서로 읽습니다. 규약 문서: `02_Strategy/03_User/프로젝트구조_규약_v1.0.docx`(원천 `_source/build/template/contract.py`·`_source/strategy/content.py`).
  - 최상위 = `_source`(코드만) + `01_Panel` `02_Strategy` `03_References` `04_Libraries` `05_UserComments` + `Main_TAAS.bat` `install.bat` `README.txt` `PROJECT.json` (예외: 이 `CLAUDE.md`, GitHub용 `README.md`, `.gitignore`).
  - 원문은 03, 정제한 원천은 04(같은 분류 번호), 읽기용 문서는 02, 사용자 요청·결정은 05. 폴더 `NN_English`, 파일 `한글_제목_vX.Y.확장자`. 이전 판 사본을 두지 않고 변경 이력 + git 으로 관리합니다.
  - 생성물(문서 세트·홈·색인·README·PROJECT.json)은 손으로 고치지 않고 원천을 고친 뒤 다시 만듭니다: `python3 _source/build/project_meta.py --version <버전>` · `cd _source && python3 build/strategy/docset.py --version <버전>` · `python3 _source/build/template/home.py --version <버전>`.
  - 구조 변경·자료 이동·새 형식은 Step 선택지(권장 표시)로 먼저 묻습니다. 요청 1건 = `05_UserComments/01_Requests/REQ-YYYYMMDD-NN_<제목>.md`, 끝나면 STATUS.md 갱신.
  - PPT·Word·Excel 은 `office_check.py`(실패 0)를 통과한 뒤에만 전달하고, 필요한 프로그램(Microsoft Office 2016+)·글꼴(맑은 고딕·Calibri·Cambria)·Windows 확인 방법(install.bat → V)을 함께 알립니다.
- 이 저장소가 프로젝트의 정본입니다. 작업 브랜치 → 커밋 → push → PR → `main` 병합 순서로 올리고, `_source/strategy/CHANGELOG.md` 에 한 줄 이상 남깁니다(→ `02_Strategy/00_History/프로젝트_변경이력_v*.xlsx` 생성). 사용자 PC의 패널 [업데이트] 버튼은 `main` 을 받습니다.
- 이전 구조(v1.6) 전체: git 브랜치 `archive/pre-standard-v1.6` (압축본 포함, main·PC 폴더에는 없음).
- 사용자 PC 프로젝트 폴더: `C:\Users\USER\Desktop\Claude_Projects\TAAS_Analysis_for_Safety` (git 작업 사본). 다운로드 폴더에는 저장하지 않습니다.
- PC 반영은 전체 zip 이 아니라 **바뀐 파일만**: `main` 병합 후 PC 연결 셸에서 `cd ~/mnt/Claude_Projects/TAAS_Analysis_for_Safety && python3 _source/ops/pc_sync.py` (git fetch → 바뀐 파일 제자리 덮어쓰기·이름 바뀐 파일은 이동 → 패널만 재생성). TAAS 원문이 바뀐 경우에만 라이브러리를 클라우드에서 조립해 바뀐 파일만 전달(연결 셸은 메모리 3GB·호출당 45초).
- 라이브러리 생성물 `04_Libraries/02_Statistics/LIB-TAAS/build/` 는 커밋하지 않고 `python _source/build.py` 로 만듭니다. 모든 경로는 `_source/taas_paths.py` 한 곳에서 정의합니다.

## 구조 요점

- 원문: `03_References/02_Statistics/files/taas/*.json.gz` (레코드 `{key,pid,label,rows,cols,data,ts,…}`), 같은 key 는 `ts` 가 늦은 것이 이김.
- 조립: `_source/src/build_library.py` (스트리밍, Parquet `pid,year,measure,d1..d8,value,raw` + `panel/`·`panel_js/` + `index.json` + `coverage.json`).
- 패널: `_source/panel/panel_template.html` 한 파일(HTML+CSS+JS). `/*__SAMPLE__*/` 자리에 예시 데이터가 들어가면 단일 파일 예시판이 됩니다. 메인 패널은 `01_Panel/Main/`(오프라인판은 `<base>` 로 라이브러리 생성물을 읽음), 첫 화면은 `01_Panel/Home/`.
  - 상태 객체 `S`, 그래프 조작기 `makeCtl`(`CTL.*`), 통계 기법은 `ST.*`(OLS·Mann-Kendall·Pettitt·Jacobi) 와 `mTrend/mLag/mOls/mPca/mIts`.
  - 결과 행 형식(13열): run_id, 기법, 실행시각, 기간, 처리, 대상, 상대, 항목, 통계량, 값, p값, n, 비고 — 바꾸면 기존 CSV 와 합칠 수 없으니 열을 **추가만** 합니다.
  - 자동화·검증용 훅: `window.TAAS_DEBUG()` → `{S, ST, yearPool, grid, UPD}`.
  - 업데이트: `_source/serve.py`(`/api/status`, `POST /api/update` + 헤더 `X-TAAS: 1`), 패널 `UPD`/`updStatus`/`runUpdate`, 버전 정보는 라이브러리의 `build_info.js`.
- 자동 갱신: `02_Strategy/04_LLM/LLM전략_자동갱신절차_v1.0.md`(절차, 상태는 패널 db `ops/last_run`), `_source/ops/auto_update.json`(예약 작업 ID·아티팩트 URL). 패널을 다시 게시할 때 `capabilities` 를 넘기지 않습니다(버튼의 연결 권한 유지). 게시 파일은 `python _source/ops/publish_plan.py` 로 만듭니다.
- PC 동기화: 예약 작업 *TAAS PC 동기화*(`auto_update.json` 의 `sync_trigger_id`), 절차 `02_Strategy/04_LLM/LLM전략_PC동기화절차_v1.0.md`, 상태 db `ops/last_sync`. 자동 갱신·부처 갱신 절차의 마지막 단계도 이 절차(1~4)를 수행해 병합 직후 PC 폴더를 맞춤. 패널 [업데이트] 창의 **PC 폴더 맞추기** 버튼이 이 예약 작업을 실행.
- 부처별 외부 라이브러리: 원자료 `03_References/02_Statistics/files/<부처>` → 원천 `04_Libraries/<분류>/LIB-<부처>/<부처>.json.gz`(변환 `_source/src/make_ext_raw.py`, 목록 `_source/ops/ext_sources.json`) → 생성물 `<라이브러리>/ext/<부처>`. TAAS 와 따로 조립·갱신(`python _source/build.py --ext <부처>`, 절차 `02_Strategy/04_LLM/LLM전략_부처자료갱신절차_v1.0.md`, 상태 db `ops/last_run_<부처>`). 패널은 `ext_index.json` 으로 합쳐 보여 줌.
  - 장표 번호: kostat 9001~9099(통계청) · police 9003, 9301~(경찰청) · mois 9101~(행정안전부) · molit 9201~(국토교통부) · policy 9901~(제도 연표, `04_Libraries/01_Standard_Law/LIB-POLICY`). 새 외부 자료도 그 부처 범위에 추가.
  - KOSIS 는 짧은 시간에 화면을 여러 번 열면 '비정상적인 서비스 이용'으로 차단함 — OpenAPI 키 우선, 화면 다운로드는 표 사이 60초.
  - 큰 결과는 브라우저 JS 반환값을 10만 자 이상으로 돌려주면 도구가 파일로 저장 → `python _source/src/make_ext_raw.py --import <파일>`.
- 참고문헌: `04_Libraries/00_Core/LIB-REFS/refs.json` 에 추가 → `project_meta.py` 가 03 분류별 색인(Excel) 생성.

## 바꾼 뒤 확인

1. `python _source/build.py --sample` (데이터를 안 바꿨으면 수 초)
2. `python _source/tests/panel/test_stats.py "$PWD/04_Libraries/02_Statistics/LIB-TAAS/build" <출력접두어>` 와 `python _source/tests/stats/verify_stats.py <출력접두어>` (Chart.js 는 시험 스크립트가 로컬 사본으로 대체 — `CHARTJS_DIR`)
3. 데이터를 바꿨으면: `python _source/ops/verify.py` — 2025 전국 사고 193,889건(134개 장표), 부상=중상+경상+부상신고, 중복 셀 0
4. 부처 라이브러리를 바꿨으면: `python _source/ops/verify_ext.py` 와 `python _source/tests/panel/test_ext.py "$PWD/04_Libraries/02_Statistics/LIB-TAAS/build"`
5. 구조·문서를 바꿨으면: 생성기 3종(위) 실행 → `office_check.py` 실패 0, 11절 점검표(`02_Strategy/03_User/프로젝트구조_규약_v1.0.xlsx` 점검표 시트)
