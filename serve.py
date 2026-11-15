"""
TAAS 패널 로컬 서버 — 패널의 [업데이트] 버튼이 이 서버를 통해 최신 버전을 받고 다시 빌드합니다.

    python serve.py              library/panel.html 을 http://127.0.0.1:8765 로 열기 (브라우저 자동 실행)
    python serve.py --update     서버 없이 업데이트만 실행 (git pull 또는 zip 내려받기 → build.py)
    python serve.py --port 9000 --no-browser

업데이트 방식
  - 이 폴더가 git 저장소이고 git 이 설치돼 있으면  : git pull --ff-only
  - 아니면 GitHub 에서 main 최신본 zip 을 받아 덮어씀 (library/·.git 제외, 공개 저장소일 때)
  그 뒤 build.py 실행 — 원본이 바뀌었으면 라이브러리 전체 조립(약 4분), 아니면 패널만(수 초)

보안: 127.0.0.1 에서만 열리고, 업데이트 요청은 같은 주소의 패널에서 보낸 것만 받습니다. 표준 라이브러리만 사용합니다.
"""
import argparse, http.server, io, json, os, shutil, subprocess, sys, threading, time, urllib.request, webbrowser, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LIB = ROOT / "library"
REPO = "jaykayLee/TAAS_Analysis_for_Safety"
BRANCH = "main"
JOB = {"state": "idle"}
_lock = threading.Lock()
_remote = {"t": 0, "v": None}
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def build_info():
    p = LIB / "build_info.json"
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def git_ok():
    return bool(shutil.which("git")) and (ROOT / ".git").exists()


def remote_head(force=False):
    """GitHub main 의 최신 커밋 (5분 캐시)"""
    if not force and time.time() - _remote["t"] < 300:
        return _remote["v"]
    try:
        req = urllib.request.Request(f"https://api.github.com/repos/{REPO}/commits/{BRANCH}", headers={"User-Agent": "taas-panel", "Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=8) as r:
            j = json.load(r)
        v = {"sha": j["sha"], "date": j["commit"]["committer"]["date"], "message": j["commit"]["message"].split("\n")[0]}
    except Exception as e:  # 오프라인·비공개 저장소 등
        v = {"error": str(e)[:200]}
    _remote.update(t=time.time(), v=v)
    return v


def status():
    b = build_info()
    r = remote_head()
    behind = bool(r and r.get("sha") and b.get("commit") and r["sha"] != b["commit"])
    return {"build": b, "mode": "git" if git_ok() else "zip", "remote": r, "behind": behind, "job": JOB}


def log(line):
    JOB.setdefault("log", []).append(line.rstrip())
    JOB["log"] = JOB["log"][-200:]
    print(line.rstrip(), flush=True)


def run(cmd, step):
    JOB["step"] = step
    log(f"$ {' '.join(map(str, cmd))}")
    p = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", env=ENV)
    for line in p.stdout:
        log(line)
        if line.startswith("["):
            JOB["step"] = line.strip()[:80]
    if p.wait() != 0:
        raise RuntimeError(f"{step} 실패 (종료 코드 {p.returncode}) — 아래 기록 참고")


def zip_update():
    JOB["step"] = "최신본 내려받기 (zip)"
    r = remote_head(force=True)
    if not r or not r.get("sha"):
        raise RuntimeError("GitHub 에 연결하지 못했습니다: " + (r or {}).get("error", ""))
    url = f"https://codeload.github.com/{REPO}/zip/refs/heads/{BRANCH}"
    log(f"내려받기 {url}")
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "taas-panel"}), timeout=120) as resp:
        data = resp.read()
    n = 0
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for m in z.infolist():
            rel = m.filename.split("/", 1)[1] if "/" in m.filename else ""
            if not rel or rel.startswith(("library/", ".git/")) or m.is_dir():
                continue
            dst = ROOT / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            new = z.read(m)
            if dst.exists() and dst.read_bytes() == new:
                continue
            dst.write_bytes(new)
            n += 1
    (ROOT / ".zip_commit.json").write_text(json.dumps({"sha": r["sha"], "date": r["date"]}, ensure_ascii=False), encoding="utf-8")
    log(f"바뀐 파일 {n}개")


def update_job():
    with _lock:
        if JOB.get("state") == "running":
            return
        JOB.clear()
        JOB.update(state="running", started=now(), step="새 버전 확인", log=[])
    try:
        before = build_info().get("commit")
        if git_ok():
            run(["git", "pull", "--ff-only", "origin", BRANCH], "내려받기 (git pull)")
        else:
            zip_update()
        run([sys.executable, "build.py"], "라이브러리·패널 만들기")
        after = build_info()
        JOB.update(state="done", finished=now(), changed=after.get("commit") != before, build=after, step="완료")
        _remote["t"] = 0
    except Exception as e:
        msg = str(e)
        if "No module named" in "\n".join(JOB.get("log", [])):
            msg += " — pip install -r requirements.txt 를 먼저 실행하세요."
        JOB.update(state="error", finished=now(), error=msg)
        log("오류: " + msg)


class H(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map,
                      ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
                      ".json": "application/json; charset=utf-8", ".md": "text/markdown; charset=utf-8", ".gz": "application/gzip"}

    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(LIB), **k)

    def log_message(self, fmt, *args):
        if "/api/" in (args[0] if args else ""):
            return
        super().log_message(fmt, *args)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def _json(self, code, obj):
        b = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/":
            self.send_response(302); self.send_header("Location", "/panel.html"); self.end_headers(); return
        if path == "/api/status":
            return self._json(200, status())
        return super().do_GET()

    def do_POST(self):
        if self.path.split("?")[0] != "/api/update":
            return self._json(404, {"error": "not found"})
        host = self.headers.get("Host", "")
        origin = self.headers.get("Origin")
        if self.headers.get("X-TAAS") != "1" or (origin and origin.split("//")[-1] != host):
            return self._json(403, {"error": "패널에서 보낸 요청만 받습니다"})
        if JOB.get("state") == "running":
            return self._json(409, {"error": "이미 업데이트 중입니다", "job": JOB})
        threading.Thread(target=update_job, daemon=True).start()
        time.sleep(0.2)
        return self._json(202, {"job": JOB})


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-browser", action="store_true")
    ap.add_argument("--update", action="store_true")
    a = ap.parse_args()
    if a.update:
        update_job()
        print("결과:", JOB.get("state"), JOB.get("error", ""))
        sys.exit(0 if JOB.get("state") == "done" else 1)
    if not (LIB / "panel.html").exists():
        print("library 가 없어 먼저 빌드합니다…")
        subprocess.run([sys.executable, "build.py"], cwd=ROOT, env=ENV)
    srv = None
    for port in range(a.port, a.port + 10):
        try:
            srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), H)
            break
        except OSError:
            continue
    if not srv:
        sys.exit("빈 포트를 찾지 못했습니다.")
    url = f"http://127.0.0.1:{srv.server_address[1]}/panel.html"
    print(f"TAAS 패널: {url}  (끄려면 이 창을 닫거나 Ctrl+C)")
    if not a.no_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
