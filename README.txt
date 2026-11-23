TAAS 교통사고 분석 (TAAS) — v1.7
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

이번 버전: 2026-11-23 — v1.7 표준 구조 전환 1단계(문서·상태 층)
- 공통 표준 구조(project-structure/1.0, 프로젝트 ID TAAS) 적용 시작 — 요청 `05_UserComments/01_Requests/REQ-20261123-01_표준구조_전환.md`
- 이전 구조(v1.6) 보관: git 브랜치 `archive/pre-standard-v1.6` (저장소 전체 압축본 `_archive/TAAS_이전구조_v1.6_ebe7e1d.zip`)
- 추가: `PROJECT.json` · `README.txt` · `install.bat` · 폴더 01~05 골격과 README · `05_UserComments/STATUS.md`(이전 `ops/HANDOFF.md`) · 요청 기록
- 문서: 프로젝트구조_규약·의존성_목록·프로젝트_변경이력(각 docx·xlsx·pptx), 03_References 분류별 참고문헌 색인(47건, 원천 `04_Libraries/00_Core/LIB-REFS/refs.json`), 라이브러리 7개 `library.json`
- 원천: `_source/build`(표준 키트 — 문서 세트·홈·의존성·Office 검사), `_source/build/project_meta.py`, `_source/strategy/content.py`, 변경 이력 원천을 `_source/strategy/CHANGELOG.md` 로 이동

라이브러리 다시 만들기: python _source/build.py   · 바뀐 파일만 받기: python _source/ops/pc_sync.py
생성물 — _source/build/project_meta.py
