# 04_Libraries/02_Statistics — 통계·관측

TAAS 사고 통계와 부처 통계(인구·차량·면허·단속)를 시스템이 쓰는 라이브러리로 정제한 곳. 원문은 `03_References/02_Statistics`.

> 이 파일은 `_source/strategy/content.py`(규약 project-structure/1.0, `_source/build/template/contract.py`)에서 생성됩니다. 폴더 규칙을 바꾸려면 원천을 고친 뒤 빌드하세요.

## 라이브러리
- `LIB-TAAS` — TAAS 교통사고 상세통계 (장표 1~7345 (338개 장표)) · 원문 `03_References/02_Statistics/files/taas` · 빌드 `python _source/build.py` · 수집 원문(json.gz)이 곧 원천 — 같은 key 는 ts 가 늦은 것이 이김
- `LIB-KOSTAT` — 통계청 인구총조사 연령별 인구 (장표 9001·9002) · 원문 `03_References/02_Statistics/files/kostat` · 빌드 `python _source/build.py --ext kostat` · 어린이 0~12세는 5세 단위로 추정
- `LIB-MOIS` — 행정안전부 주민등록인구 (장표 9101·9102) · 원문 `03_References/02_Statistics/files/mois` · 빌드 `python _source/build.py --ext mois` · 수집 예정(KOSIS OpenAPI 키)
- `LIB-MOLIT` — 국토교통부 자동차·도로·교통량·주행거리 (장표 9201~9205) · 원문 `03_References/02_Statistics/files/molit` · 빌드 `python _source/build.py --ext molit` · 수집 예정(KOSIS OpenAPI 키)
- `LIB-POLICE` — 경찰청 보호구역·면허·단속 (장표 9003, 9301~9308) · 원문 `03_References/02_Statistics/files/police` · 빌드 `python _source/build.py --ext police` · KOSIS 면허 9301·9303·9304 는 수집 예정

## 규칙
- 라이브러리 폴더 하나 = `library.json` 하나(버전·파일·적재 테이블·의존)
- 수정 → 검사 → 버전 올림(bump) → 빌드
- 읽기용 카탈로그 `라이브러리_<이름>_v*.xlsx`는 생성물
