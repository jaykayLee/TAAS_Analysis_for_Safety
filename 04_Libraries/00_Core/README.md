# 04_Libraries/00_Core — 공통 기준

프로젝트 내부 기준(참고문헌 목록)를 시스템이 쓰는 라이브러리로 정제한 곳. 원문은 `03_References/00_Core`.

> 이 파일은 `_source/strategy/content.py`(규약 project-structure/1.0, `_source/build/template/contract.py`)에서 생성됩니다. 폴더 규칙을 바꾸려면 원천을 고친 뒤 빌드하세요.

## 라이브러리
- `LIB-REFS` — 참고문헌 목록(03 색인의 원천) (장표 -) · 원문 `04_Libraries/00_Core/LIB-REFS/refs.json` · 빌드 `python _source/build/project_meta.py --version <버전>` · 새 문헌은 refs.json 에 추가

## 규칙
- 라이브러리 폴더 하나 = `library.json` 하나(버전·파일·적재 테이블·의존)
- 수정 → 검사 → 버전 올림(bump) → 빌드
- 읽기용 카탈로그 `라이브러리_<이름>_v*.xlsx`는 생성물
