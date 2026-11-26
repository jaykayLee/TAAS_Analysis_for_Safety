# 자동 갱신 절차 — TAAS Analysis for Safety

패널의 **[업데이트] → ▶ 지금 갱신 실행** 버튼(예약 작업 *TAAS Analysis for Safety*)이나, 사용자가 Claude 앱에 붙여 넣은 프롬프트로 시작합니다.
흐름: **① 실행 환경 확인 → ② 브라우저 실행 → ③ 수집 → ④ 업데이트(빌드·검증·저장소·패널 재게시)**

- 설정: `_source/ops/auto_update.json` (저장소, 패널 아티팩트 URL, 예약 작업 ID)
- 진행 상태는 패널이 실시간으로 보여 줍니다 → 아래 **상태 기록**을 단계마다 꼭 남깁니다.
- 실행 경로
  - **예약 작업**: 사람이 지켜보지 않습니다. 질문하지 말고 진행하고, 막히면 상태에 사유를 남기고 멈춥니다.
  - **Claude 앱**(사용자가 프롬프트를 붙여 넣은 대화): 사용자가 보고 있으니 필요한 승인은 요청해도 됩니다.
- 명령은 모두 저장소 루트에서 실행합니다. 답은 한국어로 합니다.

## 상태 기록 (패널 연결)

`ArtifactData` 도구로 패널 아티팩트(`artifact_url`)의 문서 `ops/last_run` 을 갱신합니다.
먼저 `get`(collection `ops`, doc_id `last_run`)으로 `version` 을 읽고, `update` 에 `if_version` 으로 넘깁니다(충돌하면 다시 읽고 재시도).

| 필드 | 값 |
|---|---|
| `status` | `env_check` · `browser` · `collect` · `build` · `publish` · `done` · `no_new_data` · `needs_app` · `error` |
| `step` | 1~4 (위 흐름 번호) |
| `message` | 사용자에게 보일 한 줄 (예: "2026년 장표 214/340 수집 중") |
| `run_id` | 패널이 보낸 실행 번호(실행 메시지에 있음) 또는 `app-<UTC시각>` |
| `source` | `scheduled` 또는 `app` |
| `started` · `updated` · `finished` | ISO 시각(UTC, `Z`) |
| `year_target` · `collected_years` · `version` · `panel_published` | 수집 대상 연도, 수집한 연도 목록, 반영 커밋, 재게시 여부 |
| `prompt` | `needs_app` 일 때만: Claude 앱에 붙여 넣을 프롬프트(`05_UserComments/03_Prompts/Claude앱_갱신프롬프트_v1.0.md` 내용 그대로) |

## 0. 준비
1. `add_repo`(owner `jaykayLee`, repo `TAAS_Analysis_for_Safety`, access `push`)로 저장소를 붙이고 안내대로 클론합니다.
2. 상태 기록: `status=env_check, step=1, message="실행 환경 확인 중", started=지금`.
3. `pip install --break-system-packages -r requirements.txt` (pandas·pyarrow·duckdb 필수, playwright·statsmodels 는 없어도 됨).

## 1. 실행 환경 확인
TAAS·KOSIS 사이트는 클라우드에서 접속되지 않습니다. **사용자 PC의 브라우저**가 필요합니다.
1. 이 세션에 PC 연결 도구(`mcp__remote-devices__*`)가 있고 `get_device_info` 가 성공하는지 확인합니다.
2. 브라우저: Claude 앱 내장 브라우저(`…Claude_Browser…` 도구, 필요하면 `enable__…Claude_Browser` 로 켬)의 `tabs_context` 가 응답하는지 → 안 되면 Claude in Chrome(`tabs_context_mcp`)을 확인합니다. 사용 전 해당 브라우저 스킬(built-in-browser / chrome-browser)을 읽습니다.
3. 둘 다 안 되면 (PC 꺼짐, Claude 앱 닫힘, 연결 안 됨):
   - 상태 기록: `status=needs_app, step=1, message="Claude 앱을 열고 아래 프롬프트로 진행하세요", prompt=<05_UserComments/03_Prompts/Claude앱_갱신프롬프트_v1.0.md 전문>`.
   - 여기서 멈춥니다(커밋·게시 없음). 마지막 응답에 같은 안내와 프롬프트를 남깁니다.

## 2. 브라우저 실행
1. 상태 기록: `status=browser, step=2`.
2. 새 탭에서 `https://taas.koroad.or.kr/sta/acs/exs/typical.do?menuId=WEB_KMP_OVT_UAS_ASA` 를 엽니다. `typeof statsMenuList !== 'undefined'` 가 될 때까지 기다립니다.
3. 자바스크립트 도구로 차례로 주입합니다(파일 내용을 그대로 실행):
   1. `window.__noAutoStart = true;`
   2. `_source/collector/browser/runner_inject.js` → `'runner v8 loaded (not started)'`
   3. `_source/collector/browser/runner_v9.js` → `'v9 ready'`
   4. `_source/collector/browser/taas_update.js` → `'TAASU ready'`

## 3. 수집
1. 상태 기록: `status=collect, step=3, message="TAAS 연도 확인 중"`.
2. `await TAASU.check()` → `latest`(TAAS 최신 연도). `python _source/ops/status.py --latest <latest>` → `need_collect`, `collect_years`.
3. `need_collect` 가 **false** 면:
   - 저장소 HEAD 가 패널에 게시된 버전(`04_Libraries/02_Statistics/LIB-TAAS/build/build_info.json` 없으면 직전 `ops/last_run.version`)과 같으면 → 상태 `no_new_data`(message "TAAS 최신 {latest}년 — 이미 반영됨", finished) 로 끝냅니다.
   - 다르면(코드·패널만 바뀜) → 4단계로 가되 수집 없이 빌드·게시만 합니다.
4. 수집: `TAASU.run({years: collect_years})` → 몇 분마다 `TAASU.status()` 를 확인하고, 10분마다 상태 message 를 "{연도}년 {진행}/{작업 수} 수집 중" 으로 갱신합니다. `완료: true` 가 되면 다음으로.
   - 한 해치(장표 약 340개)는 보통 30분 안팎입니다. 오류가 남으면 `TAASU.run` 을 한 번 더 부릅니다(받은 것은 건너뜀).
5. 내보내기: `await TAASU.pack(collect_years)` → `chunks` 개수만큼 `TAASU.chunk(i)` 를 읽어 순서대로 이어 붙이고 base64 디코드해 `03_References/02_Statistics/files/taas/taas_raw_full_<연도>.json.gz` 로 저장합니다.
   - `python -c "import gzip,json;j=json.load(gzip.open('<파일>','rt',encoding='utf-8'));print(len(j['recs']))"` 로 열리는지, 레코드 수가 `pack` 결과의 `recs` 와 같은지 확인합니다.

## 4. 업데이트 (빌드 · 검증 · 저장소 · 패널)
1. 상태 기록: `status=build, step=4, message="라이브러리 조립 중"`.
2. `python _source/build.py --sample` (원본이 바뀌면 약 5분).
3. `python _source/ops/verify.py --expect-year <latest>` → `ok: false` 면 상태 `error`(message 에 fail 내용) 로 멈춥니다(커밋하지 않음).
4. `_source/strategy/CHANGELOG.md` 맨 위에 한 줄: `## <날짜> — <연도>년 TAAS 반영 (자동 갱신)` 과 장표 수·셀 수·전국 사고건수.
5. 저장소 반영: 브랜치 `claude/auto-<YYYYMMDD-HHMM>` 커밋 → `git -c push.negotiate=true push -u origin <브랜치>` → REST 로 PR 생성(`gh api repos/jaykayLee/TAAS_Analysis_for_Safety/pulls -f head=… -f base=main …`) → 병합(`gh api -X PUT …/pulls/<번호>/merge -f merge_method=merge`). 병합이 막히면 PR 을 열어 둔 채 message 에 PR 주소를 남깁니다.
6. 패널 재게시: 상태 `status=publish`. `python _source/build.py` 를 한 번 더 실행해 `04_Libraries/02_Statistics/LIB-TAAS/build/build_info.*` 에 병합 커밋을 넣은 뒤 `python _source/ops/publish_plan.py`.
   - `Artifact` 도구로 `artifact_url` 을 먼저 `read` 합니다.
   - `publish`(url=`artifact_url`, file_path=`01_Panel/Main/TAAS_분석패널.html`, files=`_source/ops/_publish_1.json` 내용 — 페이지·`index.json`·`build_info.*`·`online/` 데이터 묶음 약 20개). `_publish_2.json` 이 있으면 같은 file_path 로 한 번 더.
   - **`capabilities` 는 넘기지 않습니다**(넘기면 패널 버튼의 연결 권한이 바뀝니다).
7. 상태 기록: `status=done, step=4, finished, version=<병합 커밋>, collected_years, panel_published=true, message="<연도>년 반영 완료 — 장표 n개, 셀 n개"`.
8. **PC 폴더 동기화**(병합한 경우에만): `02_Strategy/04_LLM/LLM전략_PC동기화절차_v1.0.md` 1~4 단계를 그대로 수행해 사용자 PC 폴더를 방금 병합한 `main` 으로 맞추고, 상태 문서 `ops/last_sync` 를 `source=after_update` 로 기록합니다. PC 셸을 쓸 수 없으면 `ops/last_sync` 를 `needs_pc` 로 남기고 이 갱신 자체는 `done` 으로 둡니다(패널의 'PC 폴더 맞추기' 버튼이나 PC 의 `Main_TAAS.bat sync` 로 나중에 맞춤). 끝나면 4-7 의 기록에 `pc_synced=true|false` 를 더합니다.

## 실패
- 어느 단계든 같은 오류가 두 번 나면 상태 `error`(message 에 단계와 사유) 로 기록하고 멈춥니다.
- 수집 원본을 받았는데 빌드·검증에서 막히면, 원본만 브랜치에 올려 두고(PR 생성, 병합하지 않음) message 에 PR 주소를 남깁니다.
