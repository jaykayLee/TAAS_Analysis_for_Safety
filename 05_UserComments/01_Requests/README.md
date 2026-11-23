# 01_Requests — 사용자 요청

요청 1건 = md 1개. 이름 `REQ-YYYYMMDD-NN_<짧은 제목>.md`.

> 이 파일은 `_source/strategy/content.py`(규약 project-structure/1.0, `_source/build/template/contract.py`)에서 생성됩니다. 폴더 규칙을 바꾸려면 원천을 고친 뒤 빌드하세요.

## 양식
```
# REQ-YYYYMMDD-NN 제목
- 상태: 접수 | 진행 | 완료 | 보류
- 요청일: YYYY-MM-DD · 요청자:
- 관련: (폴더·라이브러리·패널 탭)

## 요청

## 결정·선택(Step)

## 처리 결과(버전·커밋)
```
완료된 요청은 다음 업데이트 때 `99_History/`로 옮기고 STATUS.md에서 빠집니다.
