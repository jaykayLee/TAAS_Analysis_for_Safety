TAAS 교통사고 분석 (TAAS) — v2.4
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

이번 버전: 2026-11-27 — v2.4 사용자 중심 패널(검색·연계 제안) + 조사 자료 3종
- 왼쪽 검색을 **관련도 검색**으로: 개념 사전(연관어·비슷한 말·초성)으로 '필요할 가능성이 높은' 장표를 별점 순으로, 일치 이유와 '함께 찾는 말' 표시. '정확히 일치만' 토글(이전 방식)
- **함께 보면 좋은 자료** 카드(탐색·상관관계 탭): 공통 축(연도·시도·연령 등)이 실제로 맞는 자료만 분모·원인 후보·제도 시행·비교 집단·외부 충격·다른 분해로 제안하고 볼 수 있는 결과·근거 강도·이유를 표시. 누를 때만 추가, 안 맞는 자료는 이유와 함께 접어 둠
- 조사 자료: `02_Strategy/02_Analysis/분석기법_제안목록_v1.0.xlsx`(29개 기법) · `추가라이브러리_제안_v1.0.xlsx`(14개) · `논문_조사요약_v1.0.xlsx`(23편·연구 공백·논문 주제 6개), 원천 `_source/build/strategy/research_book.py`
- 논문 23편을 참고문헌(`LIB-REFS`)에 추가, `03_References/03_Papers_Patents/files/논문모음_v1.0.zip`(요약·링크; 공개 PDF는 PC 연결 후 v1.1)

Main_TAAS.bat 인자: (없음)=홈 · main · serve(업데이트 버튼) · update · sync(바뀐 파일만) · build · online
생성물 — _source/build/project_meta.py
