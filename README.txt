TAAS 교통사고 분석 (TAAS) — v2.1
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

이번 버전: 2026-11-25 — v2.1 KOSIS OpenAPI 로 부처 자료 수집(행정안전부·국토교통부·경찰청)
- KOSIS OpenAPI(사용자 인증키, PC 브라우저)로 14표 수집 → 원문 `03_References/02_Statistics/files/<부처>/kosis/`
  - LIB-MOIS 9101·9102 주민등록인구 5세별·연령구분별 2005~2025 매년 실측(인구총조사 빈 연도 대체)
  - LIB-MOLIT 9201 자동차 등록대수(시도·차종·용도 2011~, 2005~2010 시도 합계) · 9202 이륜차 · 9203 도로 연장(km, 포장률) · 9204 평균 일교통량 · 9205 주행거리(2012~, ㎞)
  - LIB-POLICE 9301 면허종별(1종·2종 구분) · 9302 성별(2019~ KOSIS) · 9303 연령대별 · 9304 시도별(2019~)
  - 대조: 자동차 등록대수·운전면허 소지자 2005~2024 가 TAAS 주요 교통지표(장표 1)와 모두 일치
- 패널 분석 묶음 '주행거리당'(1억 대·㎞ 당) 켜짐, 어린이·고령 묶음 분모가 주민등록인구(9102)로 바뀜
- `make_ext_raw.py --import-csv`, `KC.dumpCsv(i)` — 큰 수집 결과를 CSV 조각으로 받기
- 부처 자료 갱신 절차: 키 위치(PC 키 파일), 조각 내보내기, 수집기 주소 수정

Main_TAAS.bat 인자: (없음)=홈 · main · serve(업데이트 버튼) · update · sync(바뀐 파일만) · build · online
생성물 — _source/build/project_meta.py
