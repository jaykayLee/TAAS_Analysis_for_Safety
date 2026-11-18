# 이어서 할 일 (작업 인계)

다음 세션이 이 파일부터 읽고 이어 갑니다. 끝낸 항목은 지우지 말고 ✅ 로 표시하고 날짜를 남깁니다.
마지막 갱신: 2026-11-18

## 지금 상태 (v1.5, PR #11 병합)
- 부처별 외부 라이브러리 구조 완성: kostat(9001·9002) · police(9003) · policy(9901, 제도 18개 더미 + events 25건) 반영.
- **수치 미수집**: mois 9101·9102, molit 9201~9205, police 9301~9304 — KOSIS 가 2026-11-17 반복 접속을 차단(사용자 PC IP).
- 패널 아티팩트(https://claude.ai/artifact/UaFGY49Midoyg6h7BVLune) v1.5 로 다시 게시함(version 11).

## 다음 할 일 (순서대로)
1. **KOSIS OpenAPI 키로 수집** — 사용자가 키를 알려 주면(주간 한도 리셋 뒤) `ops/EXT_UPDATE.md` 3단계를 부처마다 따로: `KC.run(jobs, {apiKey})`.
   - 순서 권장: mois(2표) → police(5표) → molit(7표). 표 하나당 OpenAPI 호출 1~15회(월자료는 연도마다 1회).
   - **키는 저장소·패널 db 에 쓰지 않음.**
   - OpenAPI 응답 형식은 아직 실제로 확인하지 못함(코드는 문서 기준) — 첫 표에서 `KC.apiMeta` 결과와 레코드 열(C1_NM 등)을 먼저 확인하고 `src/make_ext_raw.py` 의 변환(분류 이름)이 맞는지 점검.
   - 받은 뒤: `python src/make_ext_raw.py --import <도구 결과 파일>` → `python build.py --ext <부처>` → `python ops/verify_ext.py <부처>` → 커밋·PR·병합 → 패널 재게시.
2. **예약 작업 "TAAS 부처 자료 갱신" 만들기** — 사용자 승인 필요(새 메시지에서 요청 받으면 `create_trigger`, 프롬프트는 이 저장소 기록의 v1.5 세션 참고: lib= 를 읽어 `ops/EXT_UPDATE.md` 수행). 만든 뒤 trigger id 를 `ops/auto_update.json` 의 `ext_trigger_id` 에 넣고 패널 재게시.
3. **KOSIS 밖 경찰청 자료** (4번 요청 중 단속 실적) — 음주운전 단속 건수, 무인단속장비 대수, 고령 운전자 면허 자진반납.
   후보: 공공데이터포털 15065567(자진반납 시도별 2015~), 「전국무인교통단속카메라표준데이터」(설치연도로 연도별·시도별 누적 대수 산출), 경찰청 경찰통계연보(음주단속).
4. **PC 반영** — PC 저장소(바탕화면\Claude_Projects\TAAS_Analysis_for_Safety)는 v1.4. 원본 폴더 구조가 바뀌어 `python ops/pc_sync.py` 후 `python build.py`(전체 조립 약 5분) 필요. 연결 셸(device_bash)은 인터넷이 안 돼 git fetch 불가 → 사용자가 PC 에서 `업데이트.bat` 또는 위 명령 실행.

## 진행 기록
- 2026-11-17 v1.5 구조·연표·패널(비율 환산 배율, 제도 시행 세로선·빠른 선택, 부처 갱신 목록) — PR #11
