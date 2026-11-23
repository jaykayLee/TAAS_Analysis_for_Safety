# TAAS Analysis for Safety

한국도로교통공단 **TAAS 교통사고 상세통계(338개 장표, 2005~2025)** 와 **통계청 연령별 인구**를 하나의 라이브러리로 모아,
브라우저 패널에서 탐색 · 상관관계 · 5가지 통계 기법으로 분석하고 차량 안전기술(ADAS 등)과 연결해 보는 프로젝트입니다.

- 라이브러리: 장표 340개 · 셀 30,249,410개 · 2005~2025년 (TAAS 338 + 인구 2)
- 패널: 탐색 / 상관관계 분석 / 통계 기법(추세·그레인저·다중회귀·주성분·중단 시계열) / 차량기술 매핑
- 결과 내보내기: 통계 기법 결과를 같은 13열 형식(CSV/JSON)으로 모아 기법별로 합칠 수 있음

## 빠른 시작

```bat
git clone https://github.com/jaykayLee/TAAS_Analysis_for_Safety.git
cd TAAS_Analysis_for_Safety
pip install -r 02_Strategy/05_Dependencies/requirements.txt
python _source/build.py            :: 처음 한 번 약 5분 → 04_Libraries\02_Statistics\LIB-TAAS\build\ 생성
04_Libraries\02_Statistics\LIB-TAAS\build\panel.html         :: 더블클릭
```

Windows 에서는 `빌드_실행.bat` 을 더블클릭해도 됩니다.

## 온라인 패널과 자동 갱신 (claude.ai)

전체 데이터(장표 340개)가 들어간 패널이 claude.ai 아티팩트로 게시되어 있습니다 (`_source/ops/auto_update.json` 의 `artifact_url`).

오른쪽 위 **[업데이트]** → **▶ 지금 갱신 실행** 을 누르면 예약 작업 *TAAS Analysis for Safety* 가 새 Claude 세션을 열어 아래를 진행하고, 단계가 바뀔 때마다 창에 표시됩니다.

1. **실행 환경 확인** — 사용자 PC 연결과 Claude 앱 브라우저 (TAAS·KOSIS 는 클라우드에서 접속되지 않아 PC 브라우저가 필요)
2. **브라우저 실행** — TAAS 상세통계 페이지를 열고 수집기(`_source/collector/browser/*.js`) 주입
3. **수집** — TAAS 최신 연도를 확인해 저장소에 없는 연도만 수집 (`taas_update.js`)
4. **업데이트** — `_source/build.py` → `_source/ops/verify.py` → GitHub PR 병합 → 같은 주소로 패널 재게시

PC가 꺼져 있거나 Claude 앱이 닫혀 있으면 상태가 **"Claude 앱에서 진행이 필요합니다"** 로 바뀌고, 창 아래 **Claude 앱에서 직접 실행** 칸에 붙여 넣을 프롬프트(`05_UserComments/03_Prompts/Claude앱_갱신프롬프트_v1.0.md`)가 열립니다. Claude 데스크톱 앱에서 새 대화에 붙여 넣으면 같은 절차(`02_Strategy/04_LLM/LLM전략_자동갱신절차_v1.0.md`)로 진행됩니다.

## 바뀐 파일만 받기 (PC)

```bat
python _source\ops\pc_sync.py          :: 또는 바뀐파일만_받기.bat
```

GitHub `main` 과 비교해 **바뀐 파일만** 받아 제자리에 덮어쓰고 패널만 다시 만듭니다(보통 수 초). 전체 zip 을 다시 받을 필요가 없습니다.
`--check` 를 붙이면 무엇이 바뀌는지만 보여 줍니다. 원본 데이터가 바뀐 업데이트(새 연도)일 때만 `python _source/build.py` 로 전체 조립이 필요하다고 알려 줍니다.
Claude 가 PC 에 연결돼 있으면 Claude 가 이 스크립트를 직접 실행해 동기화합니다.

## 패널 열기와 업데이트 (PC)

| 방법 | 업데이트 |
|---|---|
| **`패널_열기.bat`** (권장) — 로컬 서버(`_source/serve.py`)로 `http://127.0.0.1:8765/panel.html` 을 엽니다 | 오른쪽 위 **[업데이트]** 버튼이 최신 버전을 받아 다시 빌드한 뒤 패널을 새로 고칩니다 |
| `04_Libraries\02_Statistics\LIB-TAAS\build\panel.html` 더블클릭 | 버튼은 새 버전 여부만 알려 줍니다 → `업데이트.bat` 실행 |

버튼 아래에 **업데이트 시각**(이 PC에서 마지막으로 빌드한 때)과 **버전**(커밋·날짜, 최신 여부)이 표시됩니다. 새 버전이 있으면 버튼이 노란색으로 바뀝니다.

업데이트가 하는 일:
1. 내려받기 — 이 폴더가 git 저장소면 `git pull --ff-only`, 아니면 GitHub 최신본 zip 으로 덮어쓰기(공개 저장소일 때, 로컬 수정은 덮임)
2. `python _source/build.py` — 원본(`data/raw`)이 바뀌었으면 라이브러리 전체 조립(약 4분), 아니면 패널만(수 초)

명령으로 직접 하려면:

```bat
git pull
python _source/build.py
```

`04_Libraries\02_Statistics\LIB-TAAS\build\build_info.json` 에 버전·빌드 시각이, `04_Libraries\02_Statistics\LIB-TAAS\build\.build_manifest.json` 에 원본 해시가 남습니다.

`_source/build.py` 는 `04_Libraries\02_Statistics\LIB-TAAS\build\.build_manifest.json` 에 원본 해시를 남겨, 원본(`data/raw`)이나 조립 스크립트가 바뀐 경우에만 데이터를 다시 만듭니다.
`04_Libraries\02_Statistics\LIB-TAAS\build\` 는 생성물이라 git 에 올리지 않습니다.

### 새 연도(예: 2026) 통계가 공개되면

1. `_source\collector\` 로 2026년을 수집하고 원본을 내보냅니다 → `taas_raw_full_2026.json.gz`
   ```bat
   cd collector
   python -m taas_collector run --from 2026 --to 2026 --refresh-meta
   python -m taas_collector export ..\03_References\02_Statistics\files\taas\taas_raw_full_2026.json.gz --from 2026 --to 2026
   ```
2. `python _source/build.py` → 새 원본이 자동 포함됩니다. 같은 장표·구간이 겹치면 **더 늦게 수집한 값**이 쓰입니다(2025년 확정치 재수집 등).
3. 검증(아래) 후 `03_References/02_Statistics/files/taas/` 의 새 파일과 `_source/strategy/CHANGELOG.md` 를 커밋합니다.

## 폴더 구성

| 경로 | 내용 |
|---|---|
| `_source/build.py`, `빌드_실행.bat` | 원본 → 라이브러리·패널 한 번에 만들기 |
| `ops/` | 자동 갱신 절차서(TAAS `AUTO_UPDATE.md`, 부처 자료 `EXT_UPDATE.md`)·설정(`auto_update.json`, 부처 수집 목록 `ext_sources.json`)·Claude 앱 프롬프트·상태 점검·검증(`verify.py`, `verify_ext.py`)·게시 계획 |
| `_source/serve.py`, `패널_열기.bat`, `업데이트.bat` | 로컬 서버로 패널 열기(업데이트 버튼 동작) / 업데이트만 실행 |
| `03_References/02_Statistics/files/taas/` | TAAS 수집 원본 (5년 단위 json.gz) |
| `04_Libraries/<분류>/LIB-<부처>/<부처>.json.gz/` | 부처별 외부 라이브러리 원본 (kostat 통계청 · mois 행정안전부 · molit 국토교통부 · police 경찰청 · policy 제도 연표) |
| `03_References/02_Statistics/files/<부처>/` | 부처 원자료 — KOSIS 수집 결과(`kosis/*.csv.gz`), 인구총조사 엑셀, 어린이보호구역·제도 연표 CSV (`python _source/build.py --ext [부처]` 로 원본 재생성) |
| `_source/src/` | 라이브러리 조립(`build_library.py`), 패널 생성(`build_panel.py`), 새 연도 통합(`update_library.py`), 엑셀(`build_excel.py`), 부처 자료 변환(`make_ext_raw.py`, 인구총조사 `make_pop_raw.py`), Python 로더(`taas.py`) |
| `_source/panel/panel_template.html` | 분석 패널 원본 (모든 화면 기능·통계 기법 코드) |
| `_source/collector/` | TAAS 수집기 (Python + Playwright, v9 직접 조회 전략), KOSIS 수집기(`browser/kosis_collect.js`, OpenAPI 또는 화면 다운로드) |
| `docs/` | 사용 매뉴얼(pptx)과 매뉴얼 생성 코드, 수집 현황·2025 엑셀·분석 결과 |
| `_source/tests/` | 패널 자동 시험(Playwright), 통계 기법 계산 검증(statsmodels·pymannkendall 대조) |
| `04_Libraries/02_Statistics/LIB-TAAS/build/` | **생성물 (git 제외)** — `panel.html`, `index.js`, `panel_js/`, `parquet/` 등 · 부처 라이브러리 `ext/<부처>/` · 부처 장표 목록 `ext_index.json` |

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
- Python: `from taas import Taas; t = Taas("library"); t.search("어린이")` (자세한 사용법은 `_source/src/LIBRARY_README.md`)

## 검증

```bat
python _source\tests\stats\verify_stats.py      :: 통계 기법 계산값을 statsmodels 등과 대조 (패널 시험 결과 파일 필요)
python _source\tests\panel\test_stats.py library out\st   :: 패널에서 5개 기법 실행 (Playwright)
python _source\collector\_source\tests\test_parser.py   :: TAAS 응답 파서
```

라이브러리 점검 기준: 연도별 전국 사고건수(2025 = 193,889건) 장표 간 일치, 부상 = 중상 + 경상 + 부상신고, 중복 셀 0.

## 주의

- 공개 통계를 화면과 같은 경로로 조회하지만, 사이트 약관과 서버 부하를 고려해 수집기를 동시에 여러 개 돌리지 마세요.
- 상관·선행 관계(그레인저)는 인과가 아닙니다. TAAS 경찰 DB에는 차량의 ADAS 장착 여부가 없습니다.
