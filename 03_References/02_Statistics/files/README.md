# 부처 원자료 (TAAS 외)

부처마다 폴더가 따로 있고, `python _source/build.py --ext <부처>` 가 `_source/src/make_ext_raw.py` 로 `04_Libraries/<분류>/LIB-<부처>/<부처>.json.gz` 를 만든 뒤 그 부처 라이브러리(`04_Libraries/02_Statistics/LIB-TAAS/build/ext/<부처>`)만 다시 조립합니다.

| 폴더 | 부처 | 내용 | 갱신 |
|---|---|---|---|
| `kostat/` | 통계청 | 인구총조사 연령·성별 인구 엑셀 2개 (9001·9002) | 엑셀 교체 후 `python _source/build.py --ext kostat` |
| `mois/kosis/` | 행정안전부 | KOSIS 주민등록인구 5세별 (9101·9102) | `02_Strategy/04_LLM/LLM전략_부처자료갱신절차_v1.0.md` (패널 부처 자료 → 갱신) |
| `molit/kosis/` | 국토교통부 | KOSIS 자동차·이륜차·도로·교통량·주행거리 (9201~9205) | 〃 |
| `police/` | 경찰청 | `어린이보호구역_지정현황.csv` (9003, e-나라지표 1616 — 새 연도 행 추가), `kosis/` 운전면허 소지자 (9301~9304) | CSV 는 직접, KOSIS 는 〃 |
| `policy/` | 제도 연표 | `정책_연표.csv` (9901 + 패널 개입 연도 버튼·그래프 표시), 근거 `SOURCES.md` | CSV 직접 수정 |

`kosis/<key>.csv.gz` 열: PRD_DE, C1_NM…C4_NM(분류), ITM_NM(항목), UNIT_NM, DT — KOSIS OpenAPI 의 긴 형식과 같습니다. 어떤 통계표를 받는지는 `_source/ops/ext_sources.json`.

## 출처
- 어린이보호구역: 경찰청 「어린이보호구역 정기보고」 — e-나라지표 1616 (https://www.index.go.kr/unity/potal/main/EachDtlPageDetail.do?idx_cd=1616), 2025-11-28 갱신분. 2009~2024년, 지정대상·지정률은 2021년까지만 공표
- 제도 연표: 항목별 근거 법령·공포/시행일·확인 출처와 확인 상태(확인 13 · 부분확인 6 · 미확인 6)는 `policy/SOURCES.md`
