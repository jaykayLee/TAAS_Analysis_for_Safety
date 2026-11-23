"""
PC 폴더를 GitHub main 과 맞추기 — 바뀐 파일만 받아 덮어쓰고, 패널만 다시 만듦 (전체를 다시 받지 않음)

    python _source/ops/pc_sync.py            바뀐 파일 목록 → 받기 → 덮어쓰기 → git 기록 맞춤 → build.py(패널만, 수 초)
    python _source/ops/pc_sync.py --check    받기만 하고 무엇이 바뀌는지 보여 줌 (파일은 그대로)

- git fetch 로 바뀐 내용(차이분)만 내려받습니다.
- 파일은 '지우고 새로 만들기' 대신 제자리에 덮어씁니다 → 파일 삭제가 막힌 폴더(Claude 연결 폴더)에서도 동작.
  저장소에서 지워진 파일은 지우지 않고 _to_delete/ 로 옮깁니다(git 이 무시). 이름·위치만 바뀐 파일은 그 자리로 옮깁니다(다시 받지 않음).
- TAAS 원문(03_References/02_Statistics/files/taas)이 바뀌었으면 라이브러리 전체 조립이 필요하다고 알려 줍니다(pandas·pyarrow 필요, 약 5분).
표준 라이브러리 + git 만 사용합니다.
"""
import argparse, io, json, os, shutil, subprocess, sys, tarfile, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # _source/ops/pc_sync.py → 프로젝트 루트
TAAS_RAW = "03_References/02_Statistics/files/taas/"
BUILD_LIB = "_source/src/build_library.py"
EXT_RAW = ("04_Libraries/02_Statistics/LIB-", "04_Libraries/01_Standard_Law/LIB-")
G = ["git", "-c", "safe.directory=*", "-c", "core.filemode=false", "-c", "core.autocrlf=false"]


def git(*a, binary=False):
    r = subprocess.run(G + list(a), cwd=ROOT, capture_output=True, timeout=300)
    if r.returncode:
        raise SystemExit(f"git {' '.join(a)} 실패: {r.stderr.decode('utf-8', 'replace').strip()}")
    return r.stdout if binary else r.stdout.decode("utf-8", "replace").strip()


def tidy_locks(since):
    """삭제가 막힌 폴더에서는 git 이 자기 잠금 파일(.lock)을 못 지워 남김 → .git 바로 아래 stale-* 로 옮겨 다음 git 명령이 막히지 않게 함"""
    moved = []
    for lk in (ROOT / ".git").rglob("*.lock"):
        try:
            if since and lk.stat().st_mtime < since - 5:
                continue
            dst = ROOT / ".git" / f"stale-{lk.relative_to(ROOT / '.git').as_posix().replace('/', '_')}-{int(time.time())}"
            os.replace(lk, dst)
            moved.append(lk.name)
        except OSError:
            pass
    return moved


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--no-build", action="store_true", help="파일만 맞추고 build.py 는 실행하지 않음")
    ap.add_argument("--no-fetch", action="store_true", help="이미 받은 origin/<브랜치> 로 맞춤(fetch 생략)")
    ap.add_argument("--branch", default="main")
    a = ap.parse_args()
    t0 = time.time()
    head = git("rev-parse", "HEAD")
    for k, v in (("gc.auto", "0"), ("maintenance.auto", "false"), ("core.filemode", "false")):  # 정리 작업이 파일 삭제를 시도하지 않게
        subprocess.run(G + ["config", k, v], cwd=ROOT, capture_output=True)
    None if a.no_fetch else git("fetch", "--quiet", "--no-auto-gc", "origin", f"{a.branch}:refs/remotes/origin/{a.branch}")
    new = git("rev-parse", f"origin/{a.branch}")
    if head == new:
        print(json.dumps({"changed": 0, "version": new[:7], "message": "이미 최신입니다", "stale_locks_moved": tidy_locks(0)}, ensure_ascii=False))
        return
    rows = [l.split("\t") for l in git("-c", "core.quotepath=false", "diff", "--name-status", "--find-renames", head, new).splitlines() if l]
    plan = [{"status": r[0], "path": r[-1], "old": r[1] if r[0].startswith("R") else None} for r in rows]
    is_taas = lambda q: q["path"].startswith(TAAS_RAW) or q["path"] == BUILD_LIB
    is_ext = lambda q: q["path"].startswith(EXT_RAW) and q["path"].endswith(".json.gz")
    # 이름만 바뀐 원본(R100)은 데이터 변화가 아님(build.py 가 파일 이름으로 비교)
    data_changed = any((is_taas(p) or is_ext(p)) and p["status"] != "R100" for p in plan)
    # 부처 라이브러리 원본만 바뀌면 그 부처만 다시 조립하므로 빠름 → 여기서 바로 build.py 실행
    ext_only = data_changed and not any(is_taas(p) and p["status"] != "R100" for p in plan)
    if a.check:
        print(json.dumps({"from": head[:7], "to": new[:7], "files": plan, "data_changed": data_changed}, ensure_ascii=False, indent=1))
        return
    moved, todo = [], []
    for p in plan:
        dst = ROOT / p["path"]
        if p["status"].startswith("D"):
            if dst.exists():
                td = ROOT / "_to_delete" / p["path"]
                td.parent.mkdir(parents=True, exist_ok=True)
                os.replace(dst, td) if not td.exists() else None
                moved.append(p["path"])
            continue
        if p["old"]:  # 이름·위치 변경: 그 자리로 옮김(내용이 같으면 다시 받지 않음)
            src = ROOT / p["old"]
            if src.exists() and not dst.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                os.replace(src, dst)
            elif src.exists():
                td = ROOT / "_to_delete" / p["old"]
                td.parent.mkdir(parents=True, exist_ok=True)
                os.replace(src, td) if not td.exists() else None
                moved.append(p["old"])
            if p["status"] == "R100" and dst.exists():
                continue
        todo.append(p["path"])
    # 받을 파일을 git archive 한 번으로 꺼내 제자리에 덮어씀(파일마다 git show 하면 수백 번 호출돼 느림)
    for i in range(0, len(todo), 200):
        part = todo[i:i + 200]
        tar = subprocess.run(G + ["-c", "core.quotepath=false", "archive", "--format=tar", new, "--", *part], cwd=ROOT, capture_output=True, timeout=300)
        if tar.returncode:
            raise SystemExit("git archive 실패: " + tar.stderr.decode("utf-8", "replace"))
        with tarfile.open(fileobj=io.BytesIO(tar.stdout)) as tf:
            for m in tf:
                if not m.isfile():
                    continue
                dst = ROOT / m.name
                dst.parent.mkdir(parents=True, exist_ok=True)
                with open(dst, "wb") as f:  # 제자리 덮어쓰기 (삭제 권한 불필요)
                    f.write(tf.extractfile(m).read())
    git("reset", "--quiet", "--mixed", new)  # HEAD·기록만 새 버전으로 (작업 파일은 위에서 이미 맞춤)
    # 표준 구조 전환(2026-11-23): 예전 위치의 라이브러리 생성물(library/)을 새 위치로 옮김 — 다시 조립·전송하지 않음
    old_lib, new_lib = ROOT / "library", ROOT / "04_Libraries" / "02_Statistics" / "LIB-TAAS" / "build"
    if old_lib.is_dir() and not new_lib.exists():
        new_lib.parent.mkdir(parents=True, exist_ok=True)
        os.replace(old_lib, new_lib)
        moved.append("library/ → " + new_lib.relative_to(ROOT).as_posix())
    # 비어 버린 예전 폴더(파일 없이 __pycache__ 만 남은 것 포함)는 _to_delete/ 로 옮김 — 연결 폴더는 폴더 삭제도 막혀 있음
    gone = sorted({Path(q["old"] or q["path"]).parts[0] for q in plan if q["status"][0] in "DR" and len(Path(q["old"] or q["path"]).parts) > 1})
    for d in gone:
        dp = ROOT / d
        if dp.is_dir() and not any(f.is_file() and "__pycache__" not in f.parts for f in dp.rglob("*")):
            td = ROOT / "_to_delete" / (d + "_" + time.strftime("%Y%m%d%H%M%S"))
            td.parent.mkdir(parents=True, exist_ok=True)
            os.replace(dp, td)
            moved.append(d + "/")
    locks = tidy_locks(t0)
    dirty = git("status", "--porcelain", "--untracked-files=no")
    res = {"from": head[:7], "to": new[:7], "changed": len(plan), "files": [p["path"] for p in plan], "moved_to__to_delete": moved,
           "git_clean": not dirty, "data_changed": data_changed, "stale_locks_moved": locks}
    if a.no_build:
        res["next"] = "python _source/build.py" + ("" if data_changed else " --panel-only")
    elif data_changed and not ext_only:
        res["next"] = "TAAS 원문이 바뀌었습니다 — python _source/build.py (전체 조립, pandas·pyarrow 필요)"
    else:
        b = subprocess.run([sys.executable, str(Path("_source") / "build.py")] + ([] if ext_only else ["--panel-only"]), cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace",
                           env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        res["build"] = ("부처 라이브러리·패널 다시 생성 완료" if ext_only else "패널 다시 생성 완료") if b.returncode == 0 else ("패널 생성 실패: " + b.stdout[-300:] + b.stderr[-300:])
    res["stale_locks_moved"] = locks + tidy_locks(t0)  # git status 등이 뒤늦게 남긴 잠금도 마지막에 한 번 더 정리
    res["seconds"] = round(time.time() - t0, 1)
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
