# PC 동기화 절차 — TAAS Analysis for Safety

사용자 PC 의 프로젝트 폴더(`C:\Users\USER\Desktop\Claude_Projects\TAAS_Analysis_for_Safety`, 연결 셸에서는 `~/mnt/Claude_Projects/TAAS_Analysis_for_Safety`)를 GitHub `main` 과 같게 맞춥니다.

시작 경로
- 패널 [업데이트] 창의 **PC 폴더 맞추기** 버튼 → 예약 작업 *TAAS PC 동기화*(`_source/ops/auto_update.json` 의 `sync_trigger_id`)
- **자동 갱신·부처 자료 갱신이 끝날 때 마지막 단계로** (`LLM전략_자동갱신절차_v1.0.md` 4-8, `LLM전략_부처자료갱신절차_v1.0.md` 4-9) — 그 실행이 이미 PC 에 연결돼 있으므로 이 절차의 1~4 단계만 수행
- PC 에서 직접: `Main_TAAS.bat sync`, 또는 `Main_TAAS.bat serve` 로 연 패널의 [업데이트] 버튼

규칙
- 질문하지 않고 진행합니다(예약 작업). 저장소에 커밋하거나 패널을 다시 게시하지 않습니다.
- 연결 셸은 호출당 45초·메모리 3GB 입니다 → 명령마다 `timeout 42` 를 붙이고, 끝나지 않으면 같은 명령을 다시 실행합니다(`pc_sync` 는 다시 실행해도 안전).
- 파일 삭제가 막혀 있으면 먼저 `device_request_delete_permission`(폴더 `C:\Users\USER\Desktop\Claude_Projects`, 사유 "TAAS 동기화 중 바뀐 라이브러리 교체")을 한 번 요청합니다. 거절돼도 진행합니다 — `pc_sync`·`build.py` 는 지우지 못한 것을 `_to_delete/` 로 옮깁니다.

## 상태 기록 (패널 연결)

`ArtifactData` 로 패널 아티팩트의 문서 `ops/last_sync` 를 갱신합니다(먼저 `get` 으로 version 을 읽고 `if_version`).

| 필드 | 값 |
|---|---|
| `status` | `check` · `sync` · `build` · `done` · `up_to_date` · `needs_pc` · `error` |
| `message` | 한 줄 (예: "a8226795 → ead5ef6, 파일 12개, 패널 다시 만듦") |
| `pc_before` · `pc_version` | 동기화 전·후 PC 커밋(앞 7자) |
| `main_version` | GitHub main 커밋(앞 7자) |
| `run_id` · `source` | 실행 메시지의 run_id(없으면 `sched-<UTC시각>`), `scheduled`·`after_update`·`app` |
| `started` · `updated` · `finished` | ISO 시각(UTC, `Z`) |

## 1. 확인
1. 상태 `check`.
2. PC 연결 도구(`mcp__remote-devices__device_bash`)가 없거나 호출이 "not connected" 이면 → 상태 `needs_pc`, message "PC 가 꺼져 있거나 Claude 앱이 닫혀 있습니다 — PC 를 켜고 Claude 앱을 연 뒤 다시 누르세요" 로 끝냅니다.
3. `cd ~/mnt/Claude_Projects/TAAS_Analysis_for_Safety && git -c safe.directory=* rev-parse --short HEAD` → `pc_before`. 클라우드 클론의 `git rev-parse --short origin/main` → `main_version`.

## 2. 동기화
1. 상태 `sync`.
2. `timeout 42 python3 _source/ops/pc_sync.py --no-build` — 끝나지 않으면(출력 없음) 다시 실행. 결과 JSON 의 `changed`·`data_changed`·`next`.
3. `changed: 0`·"이미 최신" 이고 라이브러리 생성물의 `build_info.json` commit 이 main 과 같으면 → 상태 `up_to_date` 로 끝.

## 3. 다시 만들기
1. 상태 `build`.
2. `data_changed` 가 false 이거나 부처 원천만 바뀐 경우: `timeout 42 python3 -u _source/build.py`(부처 라이브러리·패널만 다시 만듦, 수 초~수십 초). 시간이 넘으면 한 번 더.
3. **TAAS 원문(`03_References/02_Statistics/files/taas/`)이 바뀐 경우**: PC 셸에서는 전체 조립(약 5분, 메모리 4GB)을 못 합니다.
   - 클라우드 클론에서 `pip install --break-system-packages pandas pyarrow duckdb` 후 `python _source/build.py` → `python _source/ops/verify.py`.
   - PC 의 `04_Libraries/02_Statistics/LIB-TAAS/build` 파일 목록·md5 를 만들어(`find … -type f ! -path './parquet/*' -print0 | xargs -0 md5sum`) `device_stage_files` 로 가져와, 다른 파일만(parquet 는 항상) zip(STORED)으로 묶습니다.
   - `SendUserFile` → `device_commit_files` 로 PC 의 `_incoming/` 에 넣고, 파이썬 zipfile 로 30초씩 이어 풀어(`_incoming/done.txt` 에 푼 파일 기록) 라이브러리 폴더에 덮어씁니다. 다 풀면 `_incoming` 을 `_to_delete/` 로 옮깁니다.
   - 마지막으로 `timeout 42 python3 _source/build.py --panel-only`.

## 4. 마무리
1. `git -c safe.directory=* rev-parse --short HEAD` → `pc_version`, `git status --porcelain --untracked-files=no` 가 비어 있는지 확인.
2. 상태 `done`, `finished`, message "<pc_before> → <pc_version>, 파일 n개, <다시 만든 것>".
3. `_to_delete/` 는 지우지 않습니다(사용자가 정리).

## 실패
- 어느 단계든 막히면 상태 `error`, message 에 원인 한 줄. PC 폴더는 `pc_sync` 를 다시 실행하면 이어서 맞춰집니다.
