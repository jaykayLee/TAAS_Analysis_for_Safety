TAAS 부처 자료 갱신을 이 대화에서 진행해줘. 대상 부처: {lib}
- 저장소: GitHub jaykayLee/TAAS_Analysis_for_Safety — push 권한으로 붙이고 클론한 뒤 ops/EXT_UPDATE.md 절차를 처음부터 그대로 따라줘.
- 실행 경로: Claude 앱 (내가 보고 있으니 필요한 승인은 물어봐도 돼). 상태 기록의 source 는 app, 문서는 ops/last_run_{lib}.
- 브라우저: 이 컴퓨터의 Claude 앱 내장 브라우저로 KOSIS 를 열어 수집해줘. KOSIS OpenAPI 키가 있으면 알려 줄게(없으면 화면 다운로드, 표 사이 60초 간격).
- KOSIS 가 '비정상적인 서비스 이용' 차단 문구를 보이면 바로 멈추고 알려줘.
- 끝나면 패널 {artifact_url} 를 같은 주소로 다시 게시하고, 진행 상태도 패널(ops/last_run_{lib})에 기록해줘.
