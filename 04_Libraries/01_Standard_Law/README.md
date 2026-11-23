# 04_Libraries/01_Standard_Law — 표준·법규

교통안전 법령·제도(시행 연표의 근거)를 시스템이 쓰는 라이브러리로 정제한 곳. 원문은 `03_References/01_Standard_Law`.

> 이 파일은 `_source/strategy/content.py`(규약 project-structure/1.0, `_source/build/template/contract.py`)에서 생성됩니다. 폴더 규칙을 바꾸려면 원천을 고친 뒤 빌드하세요.

## 라이브러리
- `LIB-POLICY` — 교통안전 제도 시행 연표 (장표 9901) · 원문 `04_Libraries/01_Standard_Law/LIB-POLICY/정책_연표.csv` · 빌드 `python _source/build.py --ext policy` · 근거 SOURCES.md(확인 13·부분확인 6·미확인 6), 법령 링크는 03_References/01_Standard_Law 색인

## 규칙
- 라이브러리 폴더 하나 = `library.json` 하나(버전·파일·적재 테이블·의존)
- 수정 → 검사 → 버전 올림(bump) → 빌드
- 읽기용 카탈로그 `라이브러리_<이름>_v*.xlsx`는 생성물
