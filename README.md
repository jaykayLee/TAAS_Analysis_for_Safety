# TAAS Analysis for Safety

한국도로교통공단 **TAAS 교통사고 상세통계(338개 장표, 2005~2025)** 와 부처 통계(인구·차량·면허·단속)·제도 시행 연표를 하나의 라이브러리로 모아,
브라우저 패널에서 탐색 · 상관관계 · 5가지 통계 기법으로 분석하고 차량 안전기술(ADAS 등)과 연결해 보는 프로젝트입니다.

- 공통 표준 구조 **project-structure/1.0** (프로젝트 ID `TAAS`) — 규약 `02_Strategy/03_User/프로젝트구조_규약_v1.0.docx`, 프로젝트 정보 `PROJECT.json`, 지금 상태 `05_UserComments/STATUS.md`
- 패널: 탐색 / 상관관계 분석(분석 묶음) / 통계 기법(추세·그레인저·다중회귀·주성분·중단 시계열) / 차량기술 매핑 — 온라인 게시본은 `PROJECT.json` 의 `panel_url`
- 이전 구조(v1.6)는 git 브랜치 `archive/pre-standard-v1.6` 에 압축본과 함께 보관

## 폴더

| 위치 | 내용 |
|---|---|
| `Main_TAAS.bat` | 시작 — 인자 없음: 프로젝트 홈 · `main` 메인 패널 · `serve` 로컬 서버(업데이트 버튼) · `update` · `sync`(바뀐 파일만) · `build` · `online` |
| `install.bat` | 의존성 설치(B) · 확인만(V — 글꼴·Office 열기 시험) |
| `_source/` | 코드 — `build.py`(라이브러리·패널 조립) · `serve.py` · `src/` · `collector/` · `panel/panel_template.html` · `ops/`(자동 갱신·검증·PC 동기화) · `tests/` · `build/`(표준 키트·문서 생성기) · `strategy/`(문서 원천·CHANGELOG) · 경로 정의 `taas_paths.py` |
| `01_Panel/` | `Home/` 프로젝트 홈(폴더·파일 지도) · `Main/` 메인 패널(오프라인판·온라인 게시본 — 빌드 생성물) |
| `02_Strategy/` | `00_History` 변경 이력 · `01_Update/Log` 수집 현황 · `02_Analysis/Workbooks` 분석 워크북 · `03_User` 구조 규약·사용 매뉴얼 · `04_LLM` 자동 갱신·부처 갱신 절차 · `05_Dependencies` 의존성 |
| `03_References/` | 분류별 참고문헌 색인(Excel) · `02_Statistics/files/` TAAS 수집 원문(json.gz)·부처 원자료(엑셀·CSV) |
| `04_Libraries/` | `02_Statistics/LIB-TAAS`(생성물 `build/` 는 git 제외)·`LIB-KOSTAT`·`LIB-MOIS`·`LIB-MOLIT`·`LIB-POLICE` · `01_Standard_Law/LIB-POLICY`(제도 연표) · `00_Core/LIB-REFS`(참고문헌 목록) — 각 `library.json` |
| `05_UserComments/` | `STATUS.md` 지금 상태·다음 할 일 · `01_Requests` 요청 · `03_Prompts` Claude 앱 프롬프트 |

## 빠른 시작 (Windows)

```bat
git clone https://github.com/jaykayLee/TAAS_Analysis_for_Safety.git
cd TAAS_Analysis_for_Safety
install.bat                 :: B = 빌드용 설치 (Python·Node·pandoc + 패키지)
Main_TAAS.bat build         :: 처음 한 번 약 5분 → 04_Libraries\02_Statistics\LIB-TAAS\build 와 01_Panel\Main 생성
Main_TAAS.bat               :: 프로젝트 홈 → 메인 패널
```

## 업데이트

| 방법 | 하는 일 |
|---|---|
| `Main_TAAS.bat sync` | GitHub `main` 과 비교해 **바뀐 파일만** 받아 제자리에 덮어쓰고(이름만 바뀐 파일은 이동) 패널만 다시 만듦(수 초). TAAS 원문이 바뀐 업데이트일 때만 전체 조립이 필요하다고 알려 줌 |
| `Main_TAAS.bat serve` → 패널 **[업데이트]** | 로컬 서버가 `git pull`(또는 zip) → `_source/build.py` 실행 후 패널을 새로 고침 |
| 온라인 패널 **[업데이트] → ▶ 지금 갱신 실행** | 예약 작업 *TAAS Analysis for Safety* 가 ① 실행 환경 확인 ② 브라우저 실행 ③ 수집 ④ 업데이트(빌드·검증·PR 병합·재게시) — 절차 `02_Strategy/04_LLM/LLM전략_자동갱신절차_v1.0.md`. PC·Claude 앱이 꺼져 있으면 `05_UserComments/03_Prompts/Claude앱_갱신프롬프트_v1.0.md` 를 Claude 앱에 붙여 넣어 진행 |

새 연도 TAAS 를 수동으로 넣을 때: `_source/collector` 로 수집 → `03_References/02_Statistics/files/taas/` 에 `taas_raw_full_<연도>.json.gz` → `python _source/build.py` → 검증 → 커밋.

## 데이터

| 장표 | 출처 | 비고 |
|---|---|---|
| 1~7322 (338개) | [TAAS 교통사고분석시스템 › 교통사고 상세통계](https://taas.koroad.or.kr/sta/acs/exs/typical.do?menuId=WEB_KMP_OVT_UAS_ASA) | 수치항목 6종(사고·사망·부상·중상·경상·부상신고) 모두 켬, 조건 필터 없음 |
| 9001 연령구분별 인구 (어린이·일반·노인) | 통계청 KOSIS 「인구총조사」 (라이브러리 `kostat`) | 어린이 0~12세(TAAS 기준)는 5세 단위 자료로 **추정**: 0~4 + 5~9 + 10~14×3/5 |
| 9002 연령별 인구 (5세 단위) | 〃 | 2005·2010년 외국인 제외 / 2015년~ 외국인 포함 — 2010→2015 사이 수준 차이 |
| 9003 어린이보호구역 지정 현황 | 경찰청 (e-나라지표 1616, 라이브러리 `police`) | 2009~2024 지정개소, 지정대상·지정률은 2021년까지 |
| 9101·9102 주민등록인구 (5세 단위 · 어린이·일반·노인) | 행정안전부 (KOSIS DT_1B04005·DT_1B04005N, `mois`) | 2005~2025 **매년 실측** (12월 말) — 인구총조사 빈 연도를 보간 대신 이것으로 |
| 9201~9205 자동차 등록대수·이륜차·도로 연장·평균 일교통량·주행거리 | 국토교통부·한국교통안전공단 (KOSIS, `molit`) | 사고율 분모(노출량). 주행거리는 2012~ |
| 9301~9304 운전면허 소지자 (면허종별·성별·연령대별·시도별) | 경찰청 (KOSIS, `police`; 성별 2005~2021 은 공공데이터포털) | 연령대·시도별은 2019~ |
| 9305~9308 면허 자진반납 · 무인단속카메라 · 음주운전 단속 · 교통법규 위반 단속 | 경찰청 (공공데이터포털, `police/datagokr`) | 반납 2015~ 시도별 · 카메라 현존 대수의 설치연도 집계 · 음주단속 2010~ · 위반 단속 2014~2018 |
| 9901 교통안전 제도 시행 (연도 더미) | 국가법령정보센터 등 (`policy`, `04_Libraries/01_Standard_Law/LIB-POLICY/정책_연표.csv`) | 음주·속도·어린이·보행자·고령·PM 등 18개 제도 — 중단 시계열 개입 연도·다중회귀 더미 |

- 9101~9304 는 KOSIS 에서 부처마다 따로 받습니다(`02_Strategy/04_LLM/LLM전략_부처자료갱신절차_v1.0.md`). 아직 받지 않은 장표는 목록에 나오지 않습니다.
- 인구총조사(9001) 실측 연도: 2005, 2010, 2015~2025 (2006~09·2011~14는 `인구_연간보간[명]` 직선 보간). 매년 실측이 필요하면 주민등록인구(9102)를 분모로 쓰세요.
- 패널 '비율 환산'은 분모 계열과 배율(10만·1만·1천·%·1억)을 고릅니다 — 예: 사고 ÷ 자동차 등록대수 × 1만, 사망 ÷ 주행거리(대·km) × 1억.
- Python: `from taas import Library; t = Library("04_Libraries/02_Statistics/LIB-TAAS/build"); t.search("어린이")` (자세한 사용법은 `_source/src/LIBRARY_README.md`)

## 검증

```bat
python _source\ops\verify.py                       :: 2025 전국 193,889건(134개 장표) 일치 · 부상 = 중상+경상+부상신고 · 중복 셀 0
python _source\ops\verify_ext.py                   :: 부처 라이브러리
python _source\tests\panel\test_stats.py "%CD%\04_Libraries\02_Statistics\LIB-TAAS\build" out\st
python _source\tests\stats\verify_stats.py out\st :: 통계 기법 계산값을 statsmodels 등과 대조 → MISMATCHES 0
python _source\collector\tests\test_parser.py     :: TAAS 응답 파서
```

문서·홈·색인을 다시 만들 때: `python _source\build\project_meta.py --version <버전>` → `cd _source && python build\strategy\docset.py --version <버전>` → `python build\template\home.py --version <버전>` (Office 호환성 검사 자동, 실패 0이어야 전달).

## 주의

- 공개 통계를 화면과 같은 경로로 조회하지만, 사이트 약관과 서버 부하를 고려해 수집기를 동시에 여러 개 돌리지 마세요.
- 상관·선행 관계(그레인저)는 인과가 아닙니다. TAAS 경찰 DB에는 차량의 ADAS 장착 여부가 없습니다.
