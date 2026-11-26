TAAS 교통사고 분석 (TAAS) — v2.3
================================================
시작: Main_TAAS.bat (프로젝트 홈 → 메인 패널) · 프로젝트 정보: PROJECT.json · 지금 상태: 05_UserComments/STATUS.md
온라인 패널: https://claude.ai/artifact/UaFGY49Midoyg6h7BVLune
저장소: https://github.com/jaykayLee/TAAS_Analysis_for_Safety (브랜치 main)

구조(project-structure/1.0):
   Main_TAAS.bat      시작 파일 — 프로젝트 홈(폴더·파일 지도) → 메인 패널(인자 online이면 게시 패널)
   install.bat        의존성 설치 — 02_Strategy/05_Dependencies의 목록대로 도구·패키지 설치
   README.txt         이번 버전에 구현된 내용 정리·설명
   PROJECT.json       프로젝트 신분증 — 시스템(LLM)이 가장 먼저 읽는 파일
   _source/           시스템 중심 컨트롤러 — 구현에 필요한 모든 소스 코드
   01_Panel/          사용자 중심 컨트롤러 — 전략·결과·새 입력을 한 화면에서 관리
   02_Strategy/       프로젝트를 표현하는 전략과 결과를 '문서'로 정리
   03_References/     실제 존재하는 문서·사이트 링크·법률과 표준
   04_Libraries/      References 정보를 시스템이 쓰는 라이브러리로 정제 — 03과 같은 분류
   05_UserComments/   사용자가 결과를 보며 요청·결정한 내용 — 항상 현재 상태(STATUS)를 남김

이번 버전: 2026-11-26 — v2.3 PC 폴더 자동 동기화
- 예약 작업 *TAAS PC 동기화*(`trig_01PrVhbHL2T2LgZa4fgdXR1m`, 일정 없음, 이 PC 필요, 자동 승인) + 절차서 `02_Strategy/04_LLM/LLM전략_PC동기화절차_v1.0.md`(상태 db `ops/last_sync`)
- 자동 갱신(4-8)·부처 자료 갱신(4-9) 절차 끝에 PC 동기화 단계 추가 → 갱신이 `main` 에 병합되면 PC 폴더도 그 자리에서 맞춤
- 패널 [업데이트] 창에 'PC 폴더' 줄: PC 버전 ↔ 게시된 패널 버전 비교, **PC 폴더 맞추기** 버튼(두 번 눌러 실행)
- `build.py` — 삭제가 막힌 폴더(PC 연결 셸)에서는 이전 라이브러리를 지우지 않고 `_to_delete/` 로 옮김
- 부처 자료 안내 문구를 표준 구조 경로로 고침

Main_TAAS.bat 인자: (없음)=홈 · main · serve(업데이트 버튼) · update · sync(바뀐 파일만) · build · online
생성물 — _source/build/project_meta.py
