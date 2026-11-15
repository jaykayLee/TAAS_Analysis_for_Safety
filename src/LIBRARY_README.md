# TAAS 교통사고 상세통계 라이브러리

한국도로교통공단 TAAS 교통사고분석시스템의 **교통사고 상세통계** 전체 통계장표(338개)를
2005년부터 수집해 한 폴더로 정리한 라이브러리입니다.

- 출처: https://taas.koroad.or.kr/sta/acs/exs/typical.do?menuId=WEB_KMP_OVT_UAS_ASA
- 수치항목 6종(사고건수·사망자수·부상자수·중상자수·경상자수·부상신고자수)을 모두 켠 상태로 수집
  - 일부 장표는 추가 항목을 켜면 TAAS 서버가 SQL 오류를 내므로, 기본 항목만 수집하고 `notes`에 표시
- 조건설정(시도·도로종류 등) 필터는 적용하지 않은 전체 값
- 비회원 조회 제한(최대 5개년)에 맞춰 5년 단위로 나눠 수집. 연도 '합계' 열은 구간마다 달라지므로 제외

## 폴더 구성

| 경로 | 용도 |
|---|---|
| `panel.html` | 분석 패널. 더블클릭하면 이 폴더의 데이터를 바로 읽습니다 |
| `index.json` / `index.js` | 장표 목록(이름, 분류 경로, 축 이름, 수치항목, 연도 범위, 주석) |
| `panel/p<장표ID>.json.gz` | 장표별 데이터(패널의 '라이브러리 폴더 열기'용) |
| `panel_js/p<장표ID>.js` | 위와 같은 데이터의 스크립트 사본(panel.html 더블클릭용) |
| `parquet/facts.parquet` | 전체 셀(롱포맷). Python·R·DuckDB용 |
| `parquet/patterns.parquet` | 장표 목록 |
| `taas.py` | Python 로더 |
| `coverage.json` | 수집 현황: 장표·구간별 상태(정상/데이터 없음/일부 항목 누락), 수치항목별 연도, 축 구성 변화 |
| `raw/` | 원본 수집 파일. 새 연도 통합 때 다시 사용 |
| `taas_collector.js` | TAAS 페이지에서 실행하는 수집기 |
| `update_library.py`, `build_library.py` | 새 연도 통합 / 라이브러리 조립 |

## 데이터 구조 (facts)

| 컬럼 | 내용 |
|---|---|
| `pid` | 장표 ID (TAAS patternId) |
| `year` | 연도 |
| `measure` | 수치항목 (예: `사고[건]`, `사망[명]`, `중상자[명]`). 교통여건 장표처럼 없는 경우 비어 있음 |
| `d1`…`d8` | 장표의 축 값. 각 축 이름은 `patterns.dim_names` 순서 |
| `value` | 값 (`-`는 빈 값) |

## Python

```python
import taas
lib = taas.Library("taas_library")
lib.search("사고유형")                                 # 장표 찾기
df = lib.table(7019)                                 # 축 이름이 붙은 롱포맷
aeb = lib.series(7019, measure="사고[건]", 사고유형="추돌")
night = lib.series(7089, measure="사망[명]", 주야="야")
lib.corr([aeb, night], diff=True)                    # 1차 차분 상관
```

지정하지 않은 축은 `합계`/`계`/`전국` 값을 씁니다. 상위 분류가 있는 장표(예: 사고유형 대분류 > 중분류 > 사고유형)에서는
하위 값만 지정해도 됩니다.

## 새 연도 추가 (예: 2026년 통계 공개 후)

1. **수집**: 크롬에서 TAAS 교통사고 상세통계 페이지를 열고 F12 → Console에 `taas_collector.js` 내용을 붙여넣은 뒤
   ```js
   TAAS.run({from: 2026, to: 2026})   // 진행: TAAS.status()
   TAAS.export()                      // 다운로드 폴더에 taas_raw_2026.json.gz 저장
   ```
   - 아직 2026년 자료가 없는 장표는 건너뛰고 목록을 보여 줍니다(`TAAS.status()`의 '건너뜀').
   - 직전 연도 확정치가 바뀌었을 수 있으면 `from: 2025, to: 2026`처럼 함께 받으세요. 통합 시 더 늦게 받은 값이 우선합니다.
2. **통합**:
   ```
   python update_library.py taas_library taas_raw_2026.json.gz
   ```
   `raw/`에 보관된 기존 수집분과 합쳐 라이브러리 전체를 다시 조립합니다. 기존 폴더는 `taas_library.bak_<시각>`으로 남습니다.
3. `panel.html`을 다시 열면 2026년이 반영됩니다.

HTML 패널은 브라우저 보안 정책(CORS) 때문에 TAAS에 직접 접속할 수 없어, 수집은 TAAS 페이지 안에서 도는 수집기가 맡습니다.

## 해석 시 주의

- 경찰 접수 인피사고 기준입니다. 물피사고는 포함되지 않습니다.
- 법규위반 장표는 2021년부터 과속을 별도 집계합니다(법규위반에서 제외).
- 연도별 시계열은 대부분 함께 감소하는 추세를 공유하므로, 원값끼리의 상관은 과대평가됩니다. 차분이나 증감률로 비교하세요.
- 차량의 첨단운전자보조장치 장착 여부는 경찰DB에 없습니다. 기술 효과 추정이 아니라 대상 사고의 규모·추이 파악용입니다.
