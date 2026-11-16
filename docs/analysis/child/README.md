# 어린이 교통사고 분석 (차대사람·차대차, 2005~2025)

보고서·초보자용 패널 설명서: https://claude.ai/artifact/MsT8t6q7mTun7qUcBoXzB2

| 파일 | 내용 |
|---|---|
| `data.py` | 라이브러리(`../../../library`)에서 분석 데이터셋 `child_dataset.csv` 생성 |
| `analyze.py` | 지표·추세(MK/Sen/Pettitt)·분해·ITS·회귀 → `child_metrics.csv`, `results.json` |
| `test_repro.py` | 패널을 설명서 순서대로 조작해 같은 수치가 나오는지 확인 (`CHARTJS_DIR` = chart.js 가 든 node_modules 상위 폴더) |

이 폴더에서 `python data.py && python analyze.py` 로 다시 계산합니다.
