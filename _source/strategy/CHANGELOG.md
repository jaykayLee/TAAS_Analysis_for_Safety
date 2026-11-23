# 변경 기록

## 2026-11-23 — v1.7 표준 구조 전환 1단계(문서·상태 층)

- 공통 표준 구조(project-structure/1.0, 프로젝트 ID TAAS) 적용 시작 — 요청 `05_UserComments/01_Requests/REQ-20261123-01_표준구조_전환.md`
- 이전 구조(v1.6) 보관: git 브랜치 `archive/pre-standard-v1.6` (저장소 전체 압축본 `_archive/TAAS_이전구조_v1.6_ebe7e1d.zip`)
- 추가: `PROJECT.json` · `README.txt` · `install.bat` · 폴더 01~05 골격과 README · `05_UserComments/STATUS.md`(이전 `ops/HANDOFF.md`) · 요청 기록
- 문서: 프로젝트구조_규약·의존성_목록·프로젝트_변경이력(각 docx·xlsx·pptx), 03_References 분류별 참고문헌 색인(47건, 원천 `04_Libraries/00_Core/LIB-REFS/refs.json`), 라이브러리 7개 `library.json`
- 원천: `_source/build`(표준 키트 — 문서 세트·홈·의존성·Office 검사), `_source/build/project_meta.py`, `_source/strategy/content.py`, 변경 이력 원천을 `_source/strategy/CHANGELOG.md` 로 이동

## 2026-11-20 — 작업 인계 갱신

- `src/build_panel.py`: 삭제가 막힌 PC 연결 폴더에서도 패널 재생성이 되도록 이전 게시 묶음을 지우는 대신 비워서 덮어씀 (`pc_sync` 패널 생성 실패 수정)
- `ops/HANDOFF.md`: PC v1.6 반영 완료, 다음 단계 계획(업데이트·연동 분석·최종 산출물) 링크와 사용자 결정 대기 항목

## 2026-11-18 — v1.6 경찰청 공공데이터 · 분석 묶음

- 경찰청 자료(공공데이터포털, KOSIS 밖)를 PC 브라우저로 받아 police 라이브러리에 추가 — `data/source/ext/police/datagokr`, 수집기 `collector/browser/datagokr_collect.js`
  - 9302 운전면허 소지자 성별 2005~2021(KOSIS 값이 생기면 그쪽 우선) · 9305 운전면허 자진반납(시도·65세 이상, 2015~2025) · 9306 무인교통단속카메라 설치 대수(현존 44,650대의 설치연도 집계, 신규·누적, 어린이보호구역 추정) · 9307 음주운전 단속(재범 횟수별, 2010~2025) · 9308 교통법규 위반 단속(위반 유형별, 2014~2018)
- 패널 **분석 묶음**(상관관계 분석 탭): 노출량(사고·사망 ÷ 자동차 1만 대) · 주행거리당(9205 수집 후) · 음주(사고 vs 단속, 2019) · 과속(과속·신호위반 사고 vs 무인카메라, 2021) · 어린이(인구 10만 명당, 2020) · 고령(노인 사고 vs 면허 반납, 2019) — 통계·분모·배율·개입 연도를 한 번에. 시설·단속 계열은 비율 환산에서 제외
- 작업 인계 파일 `ops/HANDOFF.md` (다음 세션이 먼저 읽음)

## 2026-11-18 — v1.5 부처별 외부 라이브러리 · 제도 시행 연표

- **부처마다 따로 조립·갱신하는 외부 라이브러리** `library/ext/<부처>` (원본 `data/raw/ext/<부처>`, 원자료 `data/source/ext/<부처>`): kostat 통계청(9001·9002, 기존 인구총조사 이전) · police 경찰청(9003 이전, 9301~9304 운전면허 소지자) · mois 행정안전부(9101·9102 주민등록인구 5세별·연령구분별, 2005~2025 매년 실측) · molit 국토교통부(9201~9205 자동차 등록대수·이륜차·도로 연장·평균 일교통량·주행거리) · policy 제도 연표(9901)
  - `python build.py --ext [부처]` — 그 부처 원본만 다시 만들고 그 부처 라이브러리만 다시 조립. TAAS 라이브러리(`library/`)는 그대로
  - 패널은 `ext_index.json` 으로 부처 장표를 목록에 붙여 보여 줌(로컬·온라인·예시 모두). Python: `Library("library").ext("mois")`
- KOSIS 수집기 `collector/browser/kosis_collect.js` (OpenAPI 키가 있으면 OpenAPI, 없으면 화면 다운로드 — 표 사이 60초, '비정상 이용' 차단 응답이면 즉시 중지), 수집 목록 `ops/ext_sources.json`, 변환 `src/make_ext_raw.py`
  - 9101~9304 수치는 아직 받지 않음: 2026-11-17 첫 수집 중 KOSIS 가 짧은 시간의 반복 접속을 차단 → 부처별 갱신(`ops/EXT_UPDATE.md`)으로 받음
- 부처 자료 갱신 절차 `ops/EXT_UPDATE.md`·`ops/APP_PROMPT_EXT.md`, 검증 `ops/verify_ext.py`, 패널 [업데이트] 창에 **부처 자료 — 부처마다 따로 갱신** 목록(상태 db `ops/last_run_<부처>`)
- **제도 시행 연표** 25건(확인 13·부분확인 6·미확인 6, 근거 `data/source/ext/policy/SOURCES.md`) → 장표 9901(18개 제도 연도 더미, 다중회귀 설명변수) · 중단 시계열 '빠른 선택' 버튼 · 추세 비교 '제도 시행' 세로선 · 제도가 몰린 해(2019·2020·2021·2023) 경고
- 비율 환산: 분모를 인구 외 어떤 계열로도(자동차·면허·주행거리·도로 연장), 배율 선택(10만·1만·1천·%·1·1억), 제도 더미는 나누지 않음
- `ops/pc_sync.py`: 부처 원본만 바뀌면 PC 에서 바로 `build.py` 실행(빠름) · 시험 `tests/panel/test_ext.py`

## 2026-11-16 — v1.4 어린이 사고 분석 예시

- 외부 장표 9003 「어린이보호구역 지정 현황」(경찰청, e-나라지표 1616, 2009~2024): `data/source/external/*.csv` → `src/make_external_raw.py` → `data/raw/external/` (build.py 가 자동 포함)
- 다중회귀 더미 연도에 구간 입력 허용(`2020-2021` = 해당 연도만 1, 코로나 시기 통제)
- `docs/analysis/child/`: 어린이 사고(차대사람·차대차) 분석 스크립트·결과, 패널 재현 시험(`test_repro.py`, 패널 수치 = Python 수치 확인)

## 2026-11-15 — v1.3.1 바뀐 파일만 받기

- `ops/pc_sync.py`·`바뀐파일만_받기.bat`: GitHub main 과의 차이분만 받아 제자리 덮어쓰기 → 패널만 재생성 (삭제 권한이 없는 연결 폴더에서도 동작, 지워진 파일은 `_to_delete/` 로 이동, git 이 남긴 잠금 파일은 `.git/stale-*` 로 치움)

## 2026-11-15 — v1.3 OECD 국가 비교

- 계열이 국가인 장표(OECD 10종): 기본 선택 = 대한민국 + 같은 지표 값이 가장 가까운 4개국 (대한민국 값이 있는 최근 연도 기준). 지표·수치항목을 바꾸면 다시 고름, 칩을 직접 고르면 유지
- 오른쪽에 국가별 순위표(순위·국가·막대·값, 대한민국 강조) — 눌러서 그래프에 넣기/빼기, [대한민국 근접 5개국]으로 되돌리기

## 2026-11-15 — v1.2 온라인 패널 · 자동 갱신

- 전체 데이터 패널을 claude.ai 아티팩트로 게시(`library/panel_online.html` + `index.json` + `panel/*.json.gz`, 장표를 열 때 받음)
- [업데이트] → ▶ 지금 갱신 실행: 예약 작업 *TAAS Analysis for Safety*(이 PC 필요) — ① 실행 환경 확인 ② 브라우저 실행 ③ 수집 ④ 업데이트, 단계별 진행 상태를 패널에 실시간 표시(db `ops/last_run`)
- PC·앱을 쓸 수 없으면 Claude 앱에 붙여 넣을 프롬프트 표시(`ops/APP_PROMPT.md`)
- `collector/browser/taas_update.js`(새 연도만 v9 직접 조회, base64 조각 내보내기), `ops/AUTO_UPDATE.md`·`status.py`·`verify.py`(DuckDB)·`publish_plan.py`
- 게시된 패널에서 CSV·PNG 저장은 다운로드 확인 창으로 동작

## 2026-11-15 — v1.1 패널 업데이트 버튼

- `serve.py`: 로컬 서버(127.0.0.1)로 패널을 열고, 버튼으로 git pull(또는 zip) → build.py 실행
- 패널 헤더 [업데이트] 버튼 + 아래에 업데이트 시각·버전·최신 여부 표시 (파일로 연 경우 GitHub 와 비교만)
- `build.py` 가 `library/build_info.json·js`(커밋·커밋 날짜·빌드 시각·데이터 조립 시각) 생성
- `패널_열기.bat`, `업데이트.bat` 추가 / 패널에 `<meta charset="utf-8">`

## 2026-11-15 — 저장소 시작 (v1.0)

- TAAS 교통사고 상세통계 338개 장표 2005~2025 원본(5년 단위 5개 파일), 셀 30,228,592개
- 통계청 인구총조사 연령별 인구 → 장표 9001(어린이·일반·노인·전체), 9002(5세 단위). 라이브러리 합계 셀 30,249,410개
- 패널 v3
  - 탐색: 즉시 적용/분석 실행, 계층형 축 합산, 30개 계열, 그래프 조작(기준선 M1·M2 차이, 드래그 확대, 메모, PNG)
  - 목록 체크박스 → 상관관계 분석(추세 비교·비율 환산·상관행렬·산점도)
  - 통계 기법 5종 탭: 추세·변곡점(Mann-Kendall·Sen·Pettitt), 시차상관·그레인저, 다중회귀(OLS·β·VIF·DW), 주성분·군집, 중단 시계열 + 결과 모음(13열 CSV/JSON)
- `build.py`: 원본 해시 비교로 필요한 경우만 데이터 조립, 패널만 빠르게 재생성
- 수집기 Python v9(직접 조회), 사용 매뉴얼 v1.3, 수집 현황 엑셀, 2025 엑셀, ADAS 의무장착 전후 분석 CSV
