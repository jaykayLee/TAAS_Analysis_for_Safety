# TAAS 교통사고 상세통계 수집기 (Python, v9)

TAAS(한국도로교통공단 교통사고분석시스템) **교통사고 상세통계 338개 장표**를 모든 옵션(행·열 축, 수치항목 6종)을 켠 상태로
2005년부터 받아 하나의 라이브러리로 만드는 도구 모음입니다.
지금까지 브라우저 안에서 돌린 수집 전략(v1 → v9)을 PC에서 바로 실행할 수 있게 Python 으로 옮겼습니다.

```
taas_collector/      수집기 (python -m taas_collector …)
  collector.py       브라우저 세션, 작업 나누기, 직접 조회, 검증, 이어받기, 내보내기
  octagon.py         TAAS 응답(XML+HTML 표) 파서와 조회 파라미터 도구 (표준 라이브러리만 사용)
(라이브러리 조립·패널·엑셀 스크립트는 저장소의 ../src, ../build.py 에 있습니다)
browser/             같은 전략의 브라우저 콘솔판 (참고용, Claude 수집에 실제 사용)
_source/tests/               실제 TAAS 응답 표본으로 만든 파서 검증 + 전체 흐름 모의 시험
```

## 설치 (Windows / macOS / Linux 공통, Python 3.10+)

```bat
pip install -r requirements.txt
python -m playwright install chromium
```

## 사용

```bat
:: 1) 수집 (중단해도 같은 명령을 다시 실행하면 받은 것은 건너뛰고 이어받음)
python -m taas_collector run --from 2005 --to 2025

:: 일부 장표만 / 브라우저 창 보면서
python -m taas_collector run --pids 7121,7120 --from 2025 --to 2025 --headed

:: 2) 진행 현황 (연도별 완료/전체, 최근 실패)
python -m taas_collector status

:: 3) 라이브러리용 원본 내보내기
python -m taas_collector export taas_raw_full.json.gz

:: 4) 라이브러리·엑셀·패널 만들기
::    내보낸 원본을 ..\03_References\02_Statistics\files\taas\ 에 두고 저장소 최상위에서
cd ..
python _source/build.py --excel 2025
```

`taas_collect.sqlite` 가 수집 저장소입니다(`--db` 로 바꿀 수 있음). 원본 응답을 표 형태로 저장하므로
라이브러리 형식을 바꿔도 다시 수집할 필요가 없습니다.

### 2026년 통계가 공개되면

```bat
python -m taas_collector run --from 2026 --to 2026 --refresh-meta
python -m taas_collector export ..\03_References\02_Statistics\files\taas\taas_raw_full_2026.json.gz --from 2026 --to 2026
cd .. && python _source/build.py
```

- `--refresh-meta` : 장표 목록과 장표별 최대 연도를 새로 읽음 (새 장표·새 연도 반영).
- 2025년이 확정치로 바뀌었다면 `run --from 2025 --to 2025 --force` 로 다시 받은 뒤 함께 내보내면,
  `_source/build.py` 가 더 늦게 받은 값을 사용합니다.
- 이미 브라우저로 받은 원본이 있으면 `python -m taas_collector import taas_raw_2025_v8.json.gz` 로 가져와 이어받을 수 있습니다.

## 수집 전략 (v9 직접 조회)

TAAS 상세통계 화면은 OBIP25(Octagon BI) 뷰어입니다. 화면에서 항목을 하나 켤 때마다 서버가 표 전체를 다시 계산하므로,
화면을 조작하는 방식(v8)은 장표 하나에 수십 초~수 분이 걸렸습니다. v9 는 화면을 거치지 않습니다.

1. **장표 목록**: 상세통계 페이지의 `statsMenuList`(338개 장표)와 `selectPatternInfo.do`(장표별 연도 차원·최소/최대 연도).
2. **장표 틀**: 장표마다 **한 번만** 뷰어(`/OBIP25/analysis/TypicalAnalysis.jsp`)를 띄워, 뷰어 스크립트가 만든 조회 파라미터
   (`:row_list`, `:col_list`, `:mea_list`, `:condition`, `:vcondition`, `:agg_info` …)를 읽습니다.
   저장된 장표 정의를 서버 형식으로 바꾸는 일은 TAAS 자체 스크립트가 하므로 형식이 바뀌어도 안전합니다.
3. **모두 켜기**: 파라미터에서 꺼진 항목 표시 `*`를 지웁니다 (예: `:row_list="906:*907"` → `"906:907"` = 시군구 축 켜기,
   `:mea_list="334:335:701:*336:*702:*337"` → 수치항목 6종 모두).
4. **직접 조회**: `POST /OBIP25/servlet/OctagonProxyServlet`
   `params=<파라미터>&lic&info=10001&odfname=&cubeinfo=&trid=<번호>&subjectId=<주제영역>`
   - 연도 구간은 `:vcondition="D<연도차원>@|@P08 S01 T111 #OTE![202501]!# #OTE![202512]!#;|;"` 의 두 값만 바꿉니다.
   - 응답은 XML(`TOTALPAGE`, `CURRENTPAGE`, `ROWCOUNT` …)이고 표는 `LABELSESSION / COLSESSION / ROWSESSION / DATASESSION`
     안에 HTML 조각으로 들어 있습니다. 200행 단위로 나뉘며 `:pagenum` 으로 넘깁니다. 첫 조회 뒤 서버가 결과를 캐시해 다음 페이지는 약 1초.
   - 열이 아주 많은 장표(예: 시도 시군구별·일별)는 열 블록도 페이지로 나뉩니다(`TOTALPAGEX`). 열 머리글 기준으로 합칩니다.
5. **검증** (하나라도 어긋나면 저장하지 않고 실패로 기록 → 다시 실행 시 재시도)
   - 받은 페이지 번호 = 요청한 페이지 번호
   - 모든 행의 머리글 길이 동일
   - 표에 나타난 수치항목 종류 수 = 켠 수치항목 수
6. **오류 처리**
   - `지정된 cube가 존재하지 않습니다`, `Connection reset`, `DB오류`, 시간 초과 → 일시 오류로 보고 5·10·15초 뒤 재시도.
   - 모두 켠 조회만 `SQL오류` 등으로 실패하면 원래 꺼져 있던 항목을 **하나씩 빼며** 재시도하고,
     뺀 항목은 레코드의 `meaMissing` / `dimMissing` 와 주석에 남깁니다 (라이브러리 coverage.json 에 반영).
   - 데이터가 정말 없는 구간(오래된 연도에 없는 장표 등)은 `nodata` 로 저장하고 서버 메시지를 남깁니다.
7. **작업 나누기**: 비회원은 한 번에 최대 5개 연도 → 5년 단위(일별 장표는 1년 단위), 최신 연도 먼저.

### 버전별로 겪은 문제와 대응 (요약)

| 판 | 방식 | 문제 → 대응 |
|---|---|---|
| v1~v5 | 화면 조작 | 200행에서 잘림 → 페이지 넘김 / 숨김 머리글 중복 → `display:none` 칸 제외 / 다시 그리는 중에 읽음 → 화면 서명이 3번 같을 때까지 대기 |
| v6 | 〃 | 백그라운드 탭에서 타이머가 1분 이상 지연 → Worker 타이머 / 동시 조회 간섭 → 전역 잠금 |
| v7 | 한꺼번에 켜기 | 클릭마다 재조회라 일부 항목이 빠짐 → v8 |
| v8 | 하나씩 클릭 + 재조회 대기 | 정확하지만 느림(장표당 평균 40초, 최대 6분). 7322 장표에서 한 페이지를 두 번 읽은 사례 발견 |
| **v9** | **직접 조회** | 화면·클릭 없음. 표본 40개 장표 v8 결과와 칸 단위 일치(39개 동일, 1개는 v8 쪽 오류였음) / 7120 장표 380초 → 31초 |

## 시험

```bat
python _source\tests\test_parser.py       :: 실제 TAAS 응답 4개(열 블록 페이지 포함)를 파싱해 브라우저 수집 결과와 비교
python _source\tests\test_e2e_mock.py     :: TAAS 를 흉내 낸 가짜 서버로 수집→저장→내보내기→예비 경로까지 전체 흐름 시험
```

## 주의

- TAAS 서버는 같은 세션 안에서 조회가 겹치면 결과가 섞일 수 있습니다. **한 PC 에서 수집기를 하나만** 돌리세요.
- 수집 속도는 서버 상태에 따라 분당 5~15건 정도입니다. 2005~2025 전체(약 2,500건)는 수 시간.
- 공개 통계를 화면과 같은 경로로 조회하지만, 사이트 이용 약관과 서버 부하를 고려해 동시 실행·과도한 반복은 피하세요.
- 사이트 구조가 바뀌면 `octagon.py`(응답 형식)와 `collector.py` 의 `Taas.template`(뷰어 변수 `viewer.getViewer().preParamTmp`)를 먼저 확인하세요.
