TAAS 교통사고 분석 (TAAS) — v1.8
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

이번 버전: 2026-11-23 — v1.8 표준 구조 전환 2단계(코드·데이터 이동)
- 코드 → `_source/`(build.py·serve.py·src·collector·panel 원천·ops 스크립트·tests·매뉴얼 생성기·분석 스크립트), 경로는 `_source/taas_paths.py` 한 곳에서 정의
- TAAS 수집 원문·부처 원자료 → `03_References/02_Statistics/files/`(taas·kostat·police), 부처 원천 → `04_Libraries/02_Statistics/LIB-KOSTAT·LIB-POLICE`, 제도 연표·근거 → `04_Libraries/01_Standard_Law/LIB-POLICY`
- 라이브러리 생성물 → `04_Libraries/02_Statistics/LIB-TAAS/build/`(git 제외). 원본 서명은 파일 이름 기준이라 폴더를 옮겨도 다시 조립하지 않음
- 문서 → 02_Strategy(자동 갱신·부처 갱신 절차 → 04_LLM, 사용 매뉴얼 → 03_User, 수집 현황 → 01_Update/Log, 분석 워크북 → 02_Analysis/Workbooks), Claude 앱 프롬프트 → `05_UserComments/03_Prompts/`
- `pc_sync.py`: 이름·위치만 바뀐 파일은 다시 받지 않고 그 자리로 옮김, 예전 `library/` 를 새 위치로 옮김
- 검증: 2025 전국 193,889건·부상 합 불일치 0, 부처 라이브러리 ok, 통계 기법 대조 MISMATCHES 0, 패널·부처 시험 통과

라이브러리 다시 만들기: python _source/build.py   · 바뀐 파일만 받기: python _source/ops/pc_sync.py
생성물 — _source/build/project_meta.py
