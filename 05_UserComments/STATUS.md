# STATUS — 지금 상태

다음 세션은 `PROJECT.json` → 이 파일 → 관련 폴더 README 순서로 읽고 이어 갑니다(이전 `ops/HANDOFF.md`). 끝낸 항목은 지우지 말고 ✅ 와 날짜를 남깁니다.

- 갱신: 2026-11-23 · 번들 v2.0 · 구조 project-structure/1.0 전환 완료(REQ-20261123-01)
- 다음 단계 계획(업데이트·연동 분석·최종 산출물): https://claude.ai/artifact/3S1hsjTwodhXmQs8sJpYiU — 사용자 결정 대기: OpenAPI 키, 산출물 독자·용도, ADAS 보급 자료, 부처 예약 작업 승인, 주제 순서(기본 음주→속도→노출량→고령→이륜)

## 요청(01_Requests)

- [완료] `REQ-20261123-01_표준구조_전환.md` — 공통 표준 구조 전환 1~3단계(v1.7·v1.8·v2.0). 남은 확인: Windows 에서 `install.bat` → V(Office 열기 시험)

## 결정 묶음(02_Decisions)

- 대기 0 · 적용 0 · 충돌 0 (TAAS 패널에는 결정 묶음 보내기 기능이 아직 없음)

## 지금 상태 (v1.6 데이터)
- 부처별 외부 라이브러리: kostat(9001·9002) · police(9003, 9302 성별 2005~2021, 9305~9308 공공데이터) · policy(9901 + events 25건) 반영.
- 패널 분석 묶음 6종(상관관계 분석 탭) — '주행거리당'은 9205 수집 전까지 꺼짐. 어린이·고령 묶음은 9102(주민등록) 가 생기면 자동으로 그것을 분모로 씀.
- **수치 미수집(KOSIS)**: mois 9101·9102, molit 9201~9205, police 9301·9303·9304 (9302 는 2019~ 를 KOSIS 로 보충) — KOSIS 가 2026-11-17 반복 접속을 차단, 사용자가 OpenAPI 키를 한도 리셋 뒤 알려 주기로 함.
- 패널 아티팩트(https://claude.ai/artifact/UaFGY49Midoyg6h7BVLune) — 게시할 때 Artifact read 후, 이전 게시 파일(index.json·online/*)도 path 로 read 해야 publish 가 통과함.

## 다음 할 일 (순서대로)
1. **KOSIS OpenAPI 키로 수집** — 사용자가 키를 알려 주면(주간 한도 리셋 뒤) `02_Strategy/04_LLM/LLM전략_부처자료갱신절차_v1.0.md` 3단계를 부처마다 따로: `KC.run(jobs, {apiKey})`.
   - 순서 권장: mois(2표) → police(5표) → molit(7표). 표 하나당 OpenAPI 호출 1~15회(월자료는 연도마다 1회).
   - **키는 저장소·패널 db 에 쓰지 않음.**
   - OpenAPI 응답 형식은 아직 실제로 확인하지 못함(코드는 문서 기준) — 첫 표에서 `KC.apiMeta` 결과와 레코드 열(C1_NM 등)을 먼저 확인하고 `_source/src/make_ext_raw.py` 의 변환(분류 이름)이 맞는지 점검.
   - 받은 뒤: `python _source/src/make_ext_raw.py --import <도구 결과 파일>` → `python _source/build.py --ext <부처>` → `python _source/ops/verify_ext.py <부처>` → 커밋·PR·병합 → 패널 재게시.
2. **예약 작업 "TAAS 부처 자료 갱신" 만들기** — 사용자 승인 필요(새 메시지에서 요청 받으면 `create_trigger`, 프롬프트는 이 저장소 기록의 v1.5 세션 참고: lib= 를 읽어 `02_Strategy/04_LLM/LLM전략_부처자료갱신절차_v1.0.md` 수행). 만든 뒤 trigger id 를 `_source/ops/auto_update.json` 의 `ext_trigger_id` 에 넣고 패널 재게시.
3. ✅ 2026-11-18 **KOSIS 밖 경찰청 자료** — 공공데이터포털에서 PC 브라우저로 받음(`03_References/02_Statistics/files/police/datagokr`): 9305 면허 자진반납(2015~2025 시도) · 9306 무인단속카메라(현존 44,650대 설치연도 집계) · 9307 음주운전 단속(재범 횟수별 2010~2025) · 9308 교통법규 위반 단속(2014~2018).
   - 남은 것: 음주운전 단속 2005~2009(경찰통계연보), 교통법규 위반 단속 2019~(공개 파일 없음), 무인카메라 코드 뜻(표준 정의서) 확인.
4. ✅ 2026-11-19 **PC 반영** — `pc_sync` 로 v1.6 코드 반영(연결 셸에서 git fetch 됨), 라이브러리는 클라우드에서 조립해 바뀐 파일 403개만 `04_Libraries\02_Statistics\LIB-TAAS\build\` 에 덮어씀. 연결 셸은 메모리 3GB·호출당 45초라 PC 에서 전체 조립 불가 → 원본이 바뀌면 같은 방식(클라우드 조립 → 바뀐 파일만 전송, `_incoming` 에서 이어 풀기)
5. **다음 단계** — 위 계획 문서의 1단계(데이터 보강) → 2단계(주제별 분석, 음주·속도는 지금 가능) → 3단계(차량 기술 대응 매트릭스·종합 보고서·발표 자료·매뉴얼 갱신)

## 진행 기록
- 2026-11-23 v2.0 표준 구조(project-structure/1.0) 전환 — 이전 구조는 브랜치 archive/pre-standard-v1.6
- 2026-11-20 다음 단계 계획 문서, PC v1.6 반영 기록
- 2026-11-16 v1.4 어린이 사고 분석 보고서 https://claude.ai/artifact/MsT8t6q7mTun7qUcBoXzB2
- 2026-11-18 v1.6 경찰청 공공데이터 4종 + 9302 보충, 패널 분석 묶음, 이 인계 파일
- 2026-11-17 v1.5 구조·연표·패널(비율 환산 배율, 제도 시행 세로선·빠른 선택, 부처 갱신 목록) — PR #11
