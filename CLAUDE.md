# 작업 규칙 (Claude)

- 사용자와는 한국어로 대화합니다.
- 이 저장소가 프로젝트의 정본입니다. 작업 브랜치 → 커밋 → push → PR → `main` 병합 순서로 올리고, `CHANGELOG.md` 에 한 줄 이상 남깁니다. 사용자 PC의 패널 [업데이트] 버튼은 `main` 을 받습니다.
- 사용자 PC 산출물 위치: `C:\Users\USER\Desktop\Claude_Projects` (이 프로젝트: `TAAS Analysis`, 보조 산출물은 `TAAS Analysis\참고자료`). 다운로드 폴더에는 저장하지 않습니다.
- `library/` 는 생성물입니다. 커밋하지 말고 `python build.py` 로 만듭니다.

## 구조 요점

- 원본: `data/raw/taas/*.json.gz` (레코드 `{key,pid,label,rows,cols,data,ts,…}`), 같은 key 는 `ts` 가 늦은 것이 이김.
- 조립: `src/build_library.py` (스트리밍, Parquet `pid,year,measure,d1..d8,value,raw` + `panel/`·`panel_js/` + `index.json` + `coverage.json`).
- 패널: `panel/panel_template.html` 한 파일(HTML+CSS+JS). `/*__SAMPLE__*/` 자리에 예시 데이터가 들어가면 단일 파일 예시판이 됩니다.
  - 상태 객체 `S`, 그래프 조작기 `makeCtl`(`CTL.*`), 통계 기법은 `ST.*`(OLS·Mann-Kendall·Pettitt·Jacobi) 와 `mTrend/mLag/mOls/mPca/mIts`.
  - 결과 행 형식(13열): run_id, 기법, 실행시각, 기간, 처리, 대상, 상대, 항목, 통계량, 값, p값, n, 비고 — 바꾸면 기존 CSV 와 합칠 수 없으니 열을 **추가만** 합니다.
  - 자동화·검증용 훅: `window.TAAS_DEBUG()` → `{S, ST, yearPool, grid, UPD}`.
  - 업데이트: `serve.py`(`/api/status`, `POST /api/update` + 헤더 `X-TAAS: 1`), 패널 `UPD`/`updStatus`/`runUpdate`, 버전 정보는 `library/build_info.js`.
- 자동 갱신: `ops/AUTO_UPDATE.md`(절차, 상태는 패널 db `ops/last_run`), `ops/auto_update.json`(예약 작업 ID·아티팩트 URL). 패널을 다시 게시할 때 `capabilities` 를 넘기지 않습니다(버튼의 연결 권한 유지). 게시 파일은 `python ops/publish_plan.py` 로 두 번에 나눠 올립니다.
- 장표 ID 9001·9002 는 통계청 인구(가상 장표). 새 외부 자료도 9000번대로 추가합니다.

## 바꾼 뒤 확인

1. `python build.py --sample` (데이터를 안 바꿨으면 수 초)
2. `python tests/panel/test_stats.py library <출력접두어>` 와 `python tests/stats/verify_stats.py` (Chart.js 는 시험 스크립트가 로컬 사본으로 대체 — 경로는 스크립트 상단 `SP`)
3. 데이터를 바꿨으면: 2025 전국 사고 193,889건(134개 장표), 부상=중상+경상+부상신고, 중복 셀 0
