TAAS 교통사고 분석 (TAAS) — v2.0
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

이번 버전: 2026-11-23 — v2.0 표준 구조 전환 3단계(패널·시작 파일) — 전환 완료
- 메인 패널을 `01_Panel/Main/` 에 생성: `TAAS_분석패널_offline.html`(PC 에서 여는 판, `<base>` 로 라이브러리 생성물을 읽어 데이터 복사 없음)·`TAAS_분석패널.html`(온라인 게시본). 첫 화면은 `01_Panel/Home/프로젝트_홈_v*.html`
- 시작 파일 통합: `패널_열기·업데이트·빌드_실행·바뀐파일만_받기.bat` → `Main_TAAS.bat`(인자 없음=홈, main·serve·update·sync·build·online), 의존성 `install.bat`
- `serve.py` 는 프로젝트 루트를 열고 메인 패널로 안내(패널의 [업데이트] 버튼 그대로 동작), 게시 계획은 `01_Panel/Main/TAAS_분석패널.html` 을 페이지로 씀
- `README.md`·`CLAUDE.md`·자동 갱신 절차·예약 작업 프롬프트를 새 경로로 갱신

Main_TAAS.bat 인자: (없음)=홈 · main · serve(업데이트 버튼) · update · sync(바뀐 파일만) · build · online
생성물 — _source/build/project_meta.py
