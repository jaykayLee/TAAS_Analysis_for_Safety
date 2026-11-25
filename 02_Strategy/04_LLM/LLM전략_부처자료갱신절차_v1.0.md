# 부처 자료 갱신 절차 — TAAS Analysis for Safety

TAAS 와 따로, **부처 한 곳씩** 통계를 새로 받아 그 부처 라이브러리(`04_Libraries/02_Statistics/LIB-TAAS/build/ext/<부처>`)만 다시 만듭니다.
패널 [업데이트] 창의 **부처 자료 → 갱신** 버튼(예약 작업 *TAAS 부처 자료 갱신*, 실행 메시지에 `lib=<부처>`)이나, Claude 앱에 붙여 넣은 프롬프트(`05_UserComments/03_Prompts/Claude앱_부처갱신프롬프트_v1.0.md`)로 시작합니다.

| lib | 부처 | 장표 | 받는 곳 |
|---|---|---|---|
| `mois` | 행정안전부 | 9101 주민등록인구(5세) · 9102 연령구분별 주민등록인구 | KOSIS |
| `molit` | 국토교통부(교통안전공단 포함) | 9201 자동차 등록대수 · 9202 이륜차 · 9203 도로 연장 · 9204 평균 일교통량 · 9205 주행거리 | KOSIS |
| `police` | 경찰청 | 9003 어린이보호구역 · 9301~9304 운전면허 소지자 | KOSIS (+ 9003 은 e-나라지표 CSV) |
| `kostat` | 통계청 | 9001·9002 인구총조사 | 수동 (엑셀 → `03_References/02_Statistics/files/kostat`) |
| `policy` | 제도 연표 | 9901 제도 시행 더미 · events | 수동 (`04_Libraries/01_Standard_Law/LIB-POLICY/정책_연표.csv`) |

- 수집 목록(통계표 ID·기간·분류 선택): `_source/ops/ext_sources.json` / 수집기: `_source/collector/browser/kosis_collect.js` / 변환: `_source/src/make_ext_raw.py`
- 실행 경로: **예약 작업**은 묻지 말고 진행(막히면 상태에 사유를 남기고 멈춤), **Claude 앱**은 필요한 승인을 물어도 됨. 답은 한국어.

## 상태 기록

`ArtifactData` 로 패널 아티팩트(`_source/ops/auto_update.json` 의 `artifact_url`) 문서 **`ops/last_run_<lib>`** 를 갱신합니다(collection `ops`, doc_id `last_run_<lib>`).
처음이면 `if_version` 없이 `set`, 이후 `get` 으로 version 을 읽어 `update`. 필드는 TAAS 와 같습니다
(`status` env_check·browser·collect·build·publish·done·no_new_data·needs_app·error, `step`, `message`, `run_id`, `source`, `started`·`updated`·`finished`, `year_target`, `collected`, `version`, `panel_published`, `prompt`).

## 0. 준비
1. 저장소를 push 권한으로 붙이고 클론. 실행 메시지에서 `lib` 를 읽음(없거나 `kostat`·`policy` 면 '수동 부처'라 기록하고 멈춤).
2. 상태: `env_check, step=1`. `pip install --break-system-packages -r requirements.txt`.

## 1. 실행 환경 확인
TAAS 와 같습니다(`02_Strategy/04_LLM/LLM전략_자동갱신절차_v1.0.md` 1단계). PC 연결·브라우저가 없으면 `needs_app` + `prompt`=`05_UserComments/03_Prompts/Claude앱_부처갱신프롬프트_v1.0.md`(`{lib}`·`{artifact_url}` 치환) 로 기록하고 멈춤.

## 2. 브라우저
1. 상태: `browser, step=2`.
2. 새 탭에서 `https://kosis.kr/robots.txt` 를 엽니다(가벼운 kosis.kr 페이지 — OpenAPI 를 같은 출처에서 부름). **KOSIS 는 짧은 시간에 화면을 여러 번 열면 '비정상적인 서비스 이용'으로 접속을 막습니다** — 아래 순서를 지키고, 차단 문구가 보이면 즉시 멈춥니다(상태 `error`, message "KOSIS 접속 차단 — 몇 시간 뒤 다시").
3. 수집기 주입: 저장소 `main` 의 `_source/collector/browser/kosis_collect.js` 를 `fetch('https://raw.githubusercontent.com/jaykayLee/TAAS_Analysis_for_Safety/main/_source/collector/browser/kosis_collect.js')` 로 받아 `(0,eval)(src)` → `'KC ready'`.

## 3. 수집
1. 상태: `collect, step=3`.
2. 대상: `_source/ops/ext_sources.json` 의 `libs.<lib>.kosis`. `to` 는 **올해-1** 까지(그 연도가 아직 없으면 KOSIS 가 빈 결과를 줌). `from` 은 그대로(전체 다시 받기 — 과거 수정치 반영).
   key 는 `<lib>/<key>` 로 넘깁니다.
3. **OpenAPI 키**: 사용자 PC 연결 폴더 `Claude_Projects` 의 `KOSIS_통계_OpenAI 인증키.txt`(연결 셸 `cat "$HOME/mnt/Claude_Projects/KOSIS_통계_OpenAI 인증키.txt"`) 또는 Claude 앱 대화에서 받은 키로 `KC.run(jobs, {apiKey})` — 화면을 열지 않음(권장, 2026-11-25 확인: 14표 약 1분).
   없으면 `KC.run(jobs)` — 화면 다운로드, 표 사이 60초 간격. 표가 7개면 약 10분.
4. `KC.status()` 를 1~2분마다 확인 → `running:false`. `blocked:true` 면 멈춤(위 2-2). `errors` 가 있는 표는 message 에 적고 계속.
5. 내보내기: `KC.dumpCsv(0)`, `KC.dumpCsv(1)` … 을 `{done:true}` 가 나올 때까지 하나씩 **마지막 식으로 반환**합니다(조각마다 10만 자 이상이라 도구가 결과를 파일로 저장 — 경로가 안내됨. 한 번에 수 MB 를 돌려주는 `KC.dump()` 는 도구가 잘라 버림).
   `python _source/src/make_ext_raw.py --import-csv <조각 파일들>` → `03_References/02_Statistics/files/<lib>/kosis/<key>.csv.gz`. 행 수가 `KC.status()`·`__kc.meta[key].rows` 와 같은지 확인.

## 4. 업데이트
1. 상태: `build, step=4`.
2. `python _source/build.py --ext <lib>` (그 부처 원본만 다시 만들고 그 부처 라이브러리만 조립).
3. `python _source/ops/verify_ext.py <lib>` → `ok:false` 면 상태 `error` 로 멈춤(커밋하지 않음).
4. 바뀐 것이 없으면(`git status` 에 `03_References`·`04_Libraries` 변화 없음) 상태 `no_new_data` 로 끝.
5. `_source/strategy/CHANGELOG.md` 맨 위에 `## <날짜> — <부처> 자료 갱신 (자동)` 과 장표·연도 범위 한 줄.
6. 브랜치 `claude/ext-<lib>-<YYYYMMDD-HHMM>` 커밋 → push → PR → 병합(`02_Strategy/04_LLM/LLM전략_자동갱신절차_v1.0.md` 4-5 와 같은 방법).
7. 패널 재게시: 상태 `publish`. `python _source/build.py` → `python _source/ops/publish_plan.py` → `Artifact` read 후 publish(**`capabilities` 넘기지 않음**).
8. 상태: `done, finished, version=<병합 커밋>, collected=[<key>…], panel_published=true, message="<부처> 갱신 — 장표 n개, ~<최신 연도>"`.

## OpenAPI 키
KOSIS OpenAPI(무료, kosis.kr 로그인 → OpenAPI → 활용신청)로 받으면 화면을 열지 않아 차단 걱정이 없습니다.
키는 저장소에 올리지 않습니다 — 패널 db 문서 `ops/secrets` 같은 곳도 다른 사람이 볼 수 있으니 쓰지 말고, 사용자 PC 의 키 파일(위 3-3)이나 Claude 앱 대화에서 받습니다.
클라우드와 PC 연결 셸은 kosis.kr 에 접속하지 못합니다(2026-11-25 확인) — 수집은 PC 브라우저에서만.
