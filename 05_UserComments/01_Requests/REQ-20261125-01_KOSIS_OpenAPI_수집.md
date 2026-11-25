# REQ-20261125-01 KOSIS OpenAPI 로 부처 자료 수집
- 상태: 완료
- 요청일: 2026-11-25 · 요청자: J.K. Lee
- 관련: LIB-MOIS · LIB-MOLIT · LIB-POLICE, 패널(분석 묶음), 예약 작업

## 요청
KOSIS OpenAPI 인증키를 받았으니, 키가 없어 하지 못했던 작업(행정안전부·국토교통부·경찰청 KOSIS 통계 수집과 반영)을 바뀐 폴더 구조 기준으로 수행한다. 필요한 것은 작업을 끊지 말고 요청한다.

## 결정·선택(Step)
| Step | 결정 | 근거 |
|---|---|---|
| 1 수집 경로 | 사용자 PC 의 Claude 앱 브라우저(kosis.kr) 에서 OpenAPI 호출 — 클라우드·PC 연결 셸은 kosis.kr 에 접속 못 함 | 확인 결과 |
| 2 인증키 보관 | 저장소·패널·문서에 쓰지 않음(브라우저 메모리에서만 사용) | 기존 원칙 |
| 3 큰 결과 전달 | CSV 조각(약 33만 자)으로 나눠 받기 → `make_ext_raw.py --import-csv` | 한 번에 3.5MB 는 도구가 돌려주지 못함 |

## 처리 결과
- 수집 14표(행정안전부 2 · 경찰청 5 · 국토교통부 7), 원문 `03_References/02_Statistics/files/<부처>/kosis/*.csv.gz`
- 변환: `_source/src/make_ext_raw.py` (도로 연장 m→km·포장률, 평균 일교통량 단위, 면허종별 1종/2종 구분, 주행거리 천㎞→㎞, '1인당' 항목 제외)
- 검증: verify_ext ok(전국 주민등록 2025 51,117,378 · 자동차 2025 26,514,873 · 면허 2024 34,707,289) · TAAS 장표 1 과 자동차·면허 2005~2024 일치 · verify ok · 통계 기법 대조 MISMATCHES 0 · 부처 패널 시험(로컬·온라인·예시, 분석 묶음 6종) 통과 · office_check 실패 0
- 버전 v2.1 — PR 병합 후 온라인 패널 재게시, PC 반영
- 2026-11-25 예약 작업 'TAAS 부처 자료 갱신' 생성(trig_013LLS3CPRYSTMXMf3PitGM7, 아래 초안 8단계를 문장으로) — v2.2
- 남은 것: 2025 운전면허 소지자(KOSIS 미공표)

## 예약 작업 프롬프트 초안 (TAAS 부처 자료 갱신, 실행 메시지 `lib=<부처>`)
1. add_repo 로 jaykayLee/TAAS_Analysis_for_Safety 를 push 권한으로 붙이고 클론(main).
2. 실행 메시지의 lib(mois·molit·police)와 run_id 를 읽음. 없거나 kostat·policy 면 기록 없이 끝냄.
3. PROJECT.json → STATUS.md → `02_Strategy/04_LLM/LLM전략_부처자료갱신절차_v1.0.md` 0~4단계를 그 부처만.
4. 인증키는 PC `Claude_Projects\KOSIS_통계_OpenAI 인증키.txt` 에서 읽어 브라우저 수집에만 쓰고 기록하지 않음. 못 읽으면 needs_app.
5. 예약 작업 경로 — 질문하지 않음. 브라우저 불가 → needs_app(+`Claude앱_부처갱신프롬프트_v1.0.md`), KOSIS 차단 문구 → error.
6. 상태는 패널 db `ops/last_run_<lib>`(TAAS 용 `ops/last_run` 은 건드리지 않음).
7. 재게시: `01_Panel/Main/TAAS_분석패널.html` + `publish_plan.py` files, capabilities 넘기지 않음. CHANGELOG·STATUS 갱신.
8. 한국어, 마지막에 결과 요약.
