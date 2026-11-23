# 05_UserComments

사용자가 결과를 보며 요청·결정한 내용 — 항상 현재 상태(STATUS)를 남김

> 이 파일은 `_source/strategy/content.py`(규약 project-structure/1.0, `_source/build/template/contract.py`)에서 생성됩니다. 폴더 규칙을 바꾸려면 원천을 고친 뒤 빌드하세요.

## 넣는 것
STATUS.md · 01_Requests · 02_Decisions(inbox·applied·conflicts) · 03_Prompts · 99_History

## 넣지 않는 것
라이브러리 직접 수정(결정 묶음을 거쳐 반영)

## 작성·생성
사용자·패널 작성 + 업데이트가 처리

## 하위 폴더
- `05_UserComments/01_Requests/` — 사용자 요청 1건 = md 1개(REQ-YYYYMMDD-NN) — 상태: 접수·진행·완료·보류 (작성)
- `05_UserComments/02_Decisions/` — 패널 결정 묶음 customize/1.0 — inbox → applied | conflicts (패널·업데이트)
- `05_UserComments/03_Prompts/` — 예약 작업·LLM 프롬프트와 관리 스크립트 설명 (작성)
- `05_UserComments/99_History/` — 처리 이력 ledger.jsonl · 완료 요청 보관 (업데이트)
