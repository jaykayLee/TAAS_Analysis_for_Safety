# 시험

패널 시험은 Playwright(Chromium)로 `library/panel.html` 을 열어 실제로 조작합니다.
Chart.js 는 CDN 대신 로컬 사본을 씁니다: 저장소 최상위에서 `npm install chart.js@4.4.1` (또는 `CHARTJS_DIR` 환경변수로 node_modules 가 있는 폴더 지정).

```bash
python build.py
python tests/panel/test_stats.py "$PWD/library" out/st     # 5개 기법 실행, out/st_*.json·png·results.csv
python tests/stats/verify_stats.py out/st                  # statsmodels·pymannkendall 대조 → MISMATCHES 0 이어야 함
python tests/panel/test_multi.py "$PWD/library" out/multi  # 체크박스 → 상관관계 분석
python tests/panel/test_panel.py                            # 탐색 탭·그래프 조작
```

`tests/stats/sample_results.csv` 는 결과 모음 CSV(13열)의 예시입니다.
