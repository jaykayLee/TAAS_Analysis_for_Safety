"""
TAAS 교통사고 상세통계 수집기 (Python, v9 직접 조회 전략)

전략
 1) TAAS 상세통계 페이지를 Playwright(Chromium)로 열어 장표 목록(statsMenuList)과
    장표별 연도 정보(selectPatternInfo.do)를 읽는다.
 2) 장표마다 한 번만 뷰어(TypicalAnalysis.jsp)를 띄워, 뷰어가 만든 조회 파라미터
    (:row_list / :col_list / :mea_list / :condition / :vcondition …)를 얻는다.
    → 장표 정의를 서버 형식으로 바꾸는 일은 TAAS 자체 스크립트에 맡김(가장 안전).
 3) 파라미터의 '*'(꺼진 항목)를 지워 모든 축·수치항목을 켠 상태로
    /OBIP25/servlet/OctagonProxyServlet 에 직접 POST. 연도 구간은 vcondition 만 바꾸고,
    페이지는 :pagenum 으로 넘김. 화면 렌더링·체크박스 클릭 대기가 없어 v8 대비 수~수십 배 빠름.
 4) 검증: 페이지 번호 일치, 행 길이 일정, 화면의 수치항목 수 = 켠 수치항목 수.
    모두 켠 조회가 서버 오류면 꺼져 있던 항목을 하나씩 빼며 재시도하고, 뺀 항목은 기록.
 5) 결과는 SQLite(재시작 시 이어받기)에 저장, export 로 build_library.py 호환 원본(json.gz) 생성.

비회원 제한: 한 번에 5개 연도까지(일별 장표는 1년) — 작업을 그 단위로 나눈다.
주의: 같은 PC의 다른 TAAS 수집(브라우저 수집기 등)과 동시에 돌리지 말 것.
"""
from __future__ import annotations

import argparse
import gzip
import json
import re
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from . import octagon as O

BASE = "https://taas.koroad.or.kr"
LIST_URL = BASE + "/sta/acs/exs/typical.do?menuId=WEB_KMP_OVT_UAS_ASA"
VIEWER = "/OBIP25/analysis/TypicalAnalysis.jsp"
PROXY = "/OBIP25/servlet/OctagonProxyServlet"
YEAR_FROM = 2005


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


# ================================================================ 저장소
class Store:
    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.db.execute("create table if not exists meta(pid text primary key, j text)")
        self.db.execute("create table if not exists rec(key text primary key, pid text, label text, ok int, ts real, j text)")
        self.db.execute("create table if not exists err(key text, ts real, err text)")
        self.db.commit()

    def put_meta(self, m):
        self.db.execute("replace into meta values(?,?)", (str(m["pid"]), json.dumps(m, ensure_ascii=False)))
        self.db.commit()

    def metas(self):
        return [json.loads(j) for (j,) in self.db.execute("select j from meta")]

    def put_rec(self, r):
        self.db.execute("replace into rec values(?,?,?,?,?,?)", (r["key"], str(r["pid"]), r["label"], 1, r["ts"], json.dumps(r, ensure_ascii=False)))
        self.db.commit()

    def done_keys(self):
        return {k for (k,) in self.db.execute("select key from rec")}

    def recs(self, where="1=1", args=()):
        for (j,) in self.db.execute(f"select j from rec where {where}", args):
            yield json.loads(j)

    def put_err(self, key, err):
        self.db.execute("insert into err values(?,?,?)", (key, time.time(), err))
        self.db.commit()


# ================================================================ 브라우저 세션
class Taas:
    def __init__(self, headed=False):
        from playwright.sync_api import sync_playwright  # pip install playwright && playwright install chromium
        self._pw = sync_playwright().start()
        self.browser = self._pw.chromium.launch(headless=not headed)
        self.ctx = self.browser.new_context(locale="ko-KR", viewport={"width": 1500, "height": 1000})
        self.page = self.ctx.new_page()      # 목록·직접 조회용
        self.viewer = self.ctx.new_page()    # 장표 틀(조회 파라미터) 얻기용
        self.open()

    def open(self):
        self.page.goto(LIST_URL, wait_until="domcontentloaded", timeout=120000)
        self.page.wait_for_function("window.statsMenuList && statsMenuList.length > 0", timeout=120000)

    def close(self):
        try:
            self.browser.close()
        finally:
            self._pw.stop()

    # ---- 장표 목록
    def menu(self):
        return self.page.evaluate("statsMenuList.map(x => ({...x}))")

    def pattern_info(self, subject_id, pattern_id, terms_yn):
        url = f"/sta/acs/exs/selectPatternInfo.do?subjectId={subject_id}&patternId={pattern_id}&termsYn={terms_yn}"
        for a in range(3):
            try:
                return self.page.evaluate("u => fetch(u).then(r => r.ok ? r.json() : null)", url)
            except Exception:
                time.sleep(2 + 2 * a)
        return None

    # ---- 장표 틀: 뷰어를 띄워 TAAS 스크립트가 만든 조회 파라미터를 읽음
    def template(self, pid, vc):
        v = self.viewer
        if not v.url.startswith(BASE):
            v.goto(BASE + "/sta/acs/exs/typical.do?menuId=WEB_KMP_OVT_UAS_ASA", wait_until="domcontentloaded", timeout=120000)
        with v.expect_navigation(wait_until="domcontentloaded", timeout=120000):
            v.evaluate("""([act, pid, vc]) => { const f = document.createElement('form'); f.method = 'post'; f.action = act;
            for (const [k, val] of Object.entries({uid: 'taas_viewer', pid, vCondition: vc})) { const i = document.createElement('input'); i.type = 'hidden'; i.name = k; i.value = val; f.appendChild(i); }
            document.body.appendChild(f); f.submit(); }""", [VIEWER, str(pid), vc])
        js = """() => { try { const ov = window.viewer && viewer.getViewer && viewer.getViewer(); return ov && ov.preParamTmp && /:mea_list=/.test(ov.preParamTmp) ? ov.preParamTmp : null; } catch (e) { return null; } }"""
        t0 = time.time()
        pre = None
        while time.time() - t0 < 90:
            pre = v.evaluate(js)
            if pre:
                break
            time.sleep(0.5)
        if not pre:
            return None
        info = v.evaluate("""() => {
            const ov = viewer.getViewer();
            const names = {}; document.querySelectorAll('.ovTag').forEach(e => { const m = /^(dim|mea)_(\\d+)_/.exec(e.id || ''); if (m) names[m[2]] = (e.querySelector('.ovTagText') || e).innerText.trim(); });
            return { sid: (ov.preParamTmp.match(/:subject_id="(\\d+)"/) || [])[1] || (ov.config && ov.config.subjectId) || '',
                     colDims: [...document.querySelectorAll('[id^=colDrop_] .ovTagText')].map(e => e.innerText.trim()),
                     names, body: document.body.innerText.slice(0, 20000) }; }""")
        notes = re.findall(r"주\)[^\n]*", info["body"])
        meas = [x.lstrip("*") for x in O.list_ids(pre, "mea_list")]
        return {"raw": pre, "pre": O.all_on(pre), "sid": info["sid"], "colDims": info["colDims"], "names": info["names"],
                "notes": notes, "nMea": len(meas), "off": [x.lstrip("*") for n in ("row_list", "col_list", "mea_list")
                                                          for x in O.list_ids(pre, n) if x.startswith("*")], "meas": meas}

    # ---- 직접 조회
    def post(self, params, sid, trid):
        js = """async ([url, body]) => { const c = new AbortController(); const t = setTimeout(() => c.abort(), 180000);
            try { const r = await fetch(url, {method: 'POST', signal: c.signal, headers: {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'X-Requested-With': 'XMLHttpRequest'}, body});
                  return await r.text(); } finally { clearTimeout(t); } }"""
        from urllib.parse import quote
        body = "params=" + quote(params, safe="") + f"&lic&info=10001&odfname=&cubeinfo=&trid={trid}&subjectId={sid}"
        return self.page.evaluate(js, [PROXY, body])


# ================================================================ 작업 목록
def menu_path(menu, x):
    by = {m["menuId"]: m for m in menu}
    p, c = [], x
    while c and c["menuId"] != "0":
        p.insert(0, c["menuName"])
        c = by.get(c["pMenuId"])
    return p


def build_meta(t: Taas, store: Store, pids=None, refresh=False):
    have = {str(m["pid"]): m for m in store.metas()}
    menu = t.menu()
    out = []
    pats = [m for m in menu if m.get("menuType") == "P"]
    for i, x in enumerate(pats):
        pid = str(x["patternId"])
        if pids and int(pid) not in pids:
            continue
        if pid in have and not refresh:
            out.append(have[pid]); continue
        terms = "Y" if (x["rootName"].startswith("교통사고") and x.get("trendYn") == "N") else "N"
        d = t.pattern_info(x["subjectId"], pid, terms)
        if not d:
            log("장표 정보 실패", pid, x["menuName"]); continue
        m = {"pid": pid, "subjectId": x["subjectId"], "menuId": x["menuId"], "name": x["menuName"], "path": menu_path(menu, x),
             "root": x["rootName"], "trend": x.get("trendYn"), "dateInfo": d.get("dateInfo"),
             "dims": [{"name": z.get("dispName"), "id": z.get("dimAttrId"), "n": len(z.get("dimensionDetailList") or [])} for z in (d.get("dimensionList") or [])]}
        store.put_meta(m)
        out.append(m)
        if (i + 1) % 25 == 0:
            log(f"장표 정보 {i+1}/{len(pats)}")
    return out


def jobs_for(metas, y_from, y_to):
    jobs = []
    for m in metas:
        di = m.get("dateInfo")
        if not di:
            jobs.append({"pid": m["pid"], "vc": "", "label": "all"}); continue
        L = len(di["minYear"])
        y0 = max(y_from, int(di["minYear"][:4]))
        y1 = min(y_to, int(di["maxYear"][:4]))
        span = 1 if "일별" in m["name"] else 5
        a = y0
        while a <= y1:
            b = min(a + span - 1, y1)
            vc = (f"D{di['dimAttrId']}={a}~{b};" if L == 4 else f"D{di['dimAttrId']}={a}01~{b}12;" if L == 6
                  else f"D{di['dimAttrId']}={a}0101~{b}1231;")
            jobs.append({"pid": m["pid"], "vc": vc, "label": f"{a}-{b}"})
            a += span
    # 최신 연도 먼저
    jobs.sort(key=lambda j: (-int(j["label"].split("-")[-1]) if j["label"] != "all" else 0, int(j["pid"])))
    return jobs


# ================================================================ 한 구간 수집
class Collector:
    def __init__(self, t: Taas, store: Store):
        self.t, self.store, self.tpl, self.trid = t, store, {}, 90000

    def template(self, job, vcs):
        pid = job["pid"]
        if pid not in self.tpl:
            for vc in vcs:
                T = self.t.template(pid, vc)
                if T:
                    self.tpl[pid] = T
                    break
        return self.tpl.get(pid)

    def query(self, base, sid):
        """한 조회(모든 페이지). 반환: dict 또는 {'err':..} 또는 {'nodata': msg}"""
        self.trid += 1
        x = self.t.post(O.set_page(base, 1), sid, self.trid)
        pi = O.page_info(x)
        if not pi["total"]:
            msg = pi["message"]
            if not msg or O.TRANSIENT.search(msg):
                return {"err": "transient: " + msg[:80]}
            return {"nodata": msg[:160]}
        P = O.parse(x)
        seen = set(P["meaT"])
        for n in range(2, pi["total"] + 1):
            q = None
            for a in range(3):
                self.trid += 1
                y = self.t.post(O.set_page(base, n), sid, self.trid)
                if O.page_info(y)["current"] == n:
                    q = O.parse(y); break
                time.sleep(2)
            if q is None:
                return {"err": f"page {n}"}
            seen |= set(q["meaT"])
            O.merge_page(P, q)
        if len({len(r) for r in P["rows"]}) > 1:
            return {"err": "inconsistent-rows"}
        P["pages"], P["meaSeen"], P["rowcount"] = pi["total"], len(seen), pi["rowcount"]
        return P

    def fetch(self, job, vcs):
        t0 = time.time()
        T = self.template(job, vcs)
        if not T:
            return {"err": "no-template"}
        base = O.set_range(T["pre"], job["vc"])
        if base is None:
            return {"err": "no-vcondition"}
        r = None
        for a in range(4):
            r = self.query(base, T["sid"])
            if "err" not in r or not r["err"].startswith("transient"):
                break
            # 새 조건의 첫 조회는 서버가 cube 를 만드는 동안 '지정된 cube가 존재하지 않습니다' 를 자주 돌려줌 → 곧바로 재시도
            time.sleep(0.3 if "cube가 존재하지" in r["err"] else 5 * (a + 1))
        missing = []
        if "nodata" in r and T["off"]:
            # 모두 켠 조회가 서버 오류 → 원래 꺼져 있던 항목을 하나씩 빼며 재시도
            for item in T["off"]:
                rr = self.query(O.set_off(base, item), T["sid"])
                if "err" not in rr and "nodata" not in rr:
                    r, missing = rr, [item]; break
            else:
                rr = self.query(O.set_range(T["raw"], job["vc"]) or base, T["sid"])  # 기본(원래) 상태
                if "err" not in rr and "nodata" not in rr:
                    r, missing = rr, list(T["off"])
        if "err" in r:
            return r
        mea_off = [T["names"].get(i, i) for i in missing if i in T["meas"]]
        dim_off = [T["names"].get(i, i) for i in missing if i not in T["meas"]]
        n_mea_on = T["nMea"] - len([i for i in missing if i in T["meas"]])
        base_rec = {"key": f"{job['pid']}|{job['label']}", "pid": job["pid"], "label": job["label"], "vc": job["vc"],
                    "meaAll": T["nMea"], "meaMissing": mea_off, "dimAll": True, "dimsEnabled": [], "dimMissing": dim_off,
                    "v8": True, "v9": True, "py": True, "ts": int(time.time() * 1000)}
        if "nodata" in r:
            return {**base_rec, "lab": [], "colDims": [], "rows": [], "cols": [], "data": [], "pages": 0, "nodata": True,
                    "meaOn": 0, "msg": ["서버 응답: " + r["nodata"]], "ms": int((time.time() - t0) * 1000)}
        if r["meaSeen"] and r["meaSeen"] != n_mea_on:
            return {"err": f"mea {r['meaSeen']}/{n_mea_on}"}
        msg = list(T["notes"])
        if mea_off:
            msg.append("서버 오류로 다음 수치항목 제외: " + ", ".join(mea_off))
        if dim_off:
            msg.append("서버 오류로 다음 축을 켜지 못함: " + ", ".join(dim_off))
        return {**base_rec, "lab": r["lab"], "colDims": T["colDims"], "rows": r["rows"], "cols": r["cols"], "data": r["data"],
                "pages": r["pages"], "nodata": False, "meaOn": n_mea_on, "msg": msg, "rowcount": r["rowcount"],
                "colRealigned": r.get("colRealigned", 0), "ms": int((time.time() - t0) * 1000)}


# ================================================================ 명령
def cmd_run(a):
    store = Store(a.db)
    pids = {int(x) for x in a.pids.split(",")} if a.pids else None
    t = Taas(headed=a.headed)
    try:
        log("장표 목록 읽는 중…")
        metas = build_meta(t, store, pids, refresh=a.refresh_meta)
        jobs = jobs_for(metas, a.year_from, a.year_to)
        done = set() if a.force else store.done_keys()
        todo = [j for j in jobs if f"{j['pid']}|{j['label']}" not in done]
        log(f"장표 {len(metas)}개, 작업 {len(jobs)}건, 남은 작업 {len(todo)}건")
        C = Collector(t, store)
        by_pid = {}
        for j in jobs:
            by_pid.setdefault(j["pid"], []).append(j["vc"])
        t_start, n_ok, n_err = time.time(), 0, 0
        for i, j in enumerate(todo, 1):
            key = f"{j['pid']}|{j['label']}"
            vcs = [j["vc"]] + list(reversed(by_pid[j["pid"]]))
            try:
                r = C.fetch(j, vcs)
            except Exception as e:  # 브라우저/네트워크 끊김 → 세션 다시 열고 한 번 더
                log("예외", key, str(e)[:120])
                try:
                    t.open(); C.tpl.pop(j["pid"], None); r = C.fetch(j, vcs)
                except Exception as e2:
                    r = {"err": "exception: " + str(e2)[:120]}
            if "err" in r:
                n_err += 1
                store.put_err(key, r["err"])
                log(f"[{i}/{len(todo)}] 실패 {key}: {r['err']}")
            else:
                n_ok += 1
                store.put_rec(r)
                rate = n_ok / max(1e-9, (time.time() - t_start) / 60)
                log(f"[{i}/{len(todo)}] {key} 행 {len(r['rows'])} 열 {len(r['cols'])} 쪽 {r['pages']} {r['ms']/1000:.1f}s"
                    + (" (자료 없음)" if r["nodata"] else "") + f"  | {rate:.1f}건/분")
            if len(C.tpl) > 30:  # 메모리 관리
                C.tpl.pop(next(iter(C.tpl)))
        log(f"끝: 성공 {n_ok}, 실패 {n_err}. 실패분은 같은 명령을 다시 실행하면 이어서 받습니다.")
    finally:
        t.close()


def cmd_status(a):
    store = Store(a.db)
    metas = store.metas()
    jobs = jobs_for(metas, a.year_from, a.year_to)
    done = store.done_keys()
    errs = list(store.db.execute("select key, err from err order by ts desc limit 10"))
    by_year = {}
    for j in jobs:
        y = j["label"].split("-")[0]
        d = by_year.setdefault(y, [0, 0])
        d[0] += 1
        d[1] += f"{j['pid']}|{j['label']}" in done
    n_done = sum(1 for j in jobs if (j["pid"] + "|" + j["label"]) in done)
    print(f"장표 {len(metas)}개, 작업 {len(jobs)}건, 완료 {n_done}건")
    for y in sorted(by_year):
        print(f"  {y}: {by_year[y][1]}/{by_year[y][0]}")
    if errs:
        print("최근 실패:")
        for k, e in errs:
            print("  ", k, e)


def cmd_export(a):
    store = Store(a.db)
    lo, hi = a.year_from, a.year_to
    def inside(r):
        if r["label"] == "all":
            return True
        y0, y1 = (int(x) for x in r["label"].split("-"))
        return y1 >= lo and y0 <= hi
    recs = [r for r in store.recs() if inside(r)]
    out = {"exported": datetime.now(timezone.utc).isoformat(), "meta": store.metas(), "recs": recs}
    with gzip.open(a.out, "wt", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
    print(f"{a.out}: 레코드 {len(recs)}건, 장표 {len(out['meta'])}개")


def cmd_import(a):
    """브라우저 수집기(runner_v9.js 등)로 받은 원본(json.gz)을 SQLite 로 가져옴 — 이어받기용."""
    store = Store(a.db)
    j = json.load(gzip.open(a.file, "rt", encoding="utf-8"))
    for m in j.get("meta", []):
        store.put_meta(m)
    n = 0
    for r in j.get("recs", []):
        if r.get("v8") or r.get("v9"):
            store.put_rec(r); n += 1
    print(f"가져옴: 장표 {len(j.get('meta', []))}개, 레코드 {n}건")


def main(argv=None):
    p = argparse.ArgumentParser(prog="taas_collector", description="TAAS 교통사고 상세통계 수집기 (v9 직접 조회)")
    p.add_argument("--db", default="taas_collect.sqlite", help="수집 저장소(SQLite). 중단 후 다시 실행하면 이어받음")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="수집 실행")
    r.add_argument("--from", dest="year_from", type=int, default=YEAR_FROM)
    r.add_argument("--to", dest="year_to", type=int, default=datetime.now().year)
    r.add_argument("--pids", help="일부 장표만 (예: 7121,7120)")
    r.add_argument("--headed", action="store_true", help="브라우저 창을 띄워 진행 (기본: 숨김)")
    r.add_argument("--force", action="store_true", help="이미 받은 구간도 다시 받음 (예: 확정치 재수집)")
    r.add_argument("--refresh-meta", action="store_true", help="장표 목록·연도 정보를 새로 읽음 (새 연도 공개 후)")
    r.set_defaults(func=cmd_run)
    s = sub.add_parser("status", help="진행 현황")
    s.add_argument("--from", dest="year_from", type=int, default=YEAR_FROM)
    s.add_argument("--to", dest="year_to", type=int, default=datetime.now().year)
    s.set_defaults(func=cmd_status)
    e = sub.add_parser("export", help="build_library.py 용 원본(json.gz) 내보내기")
    e.add_argument("out")
    e.add_argument("--from", dest="year_from", type=int, default=YEAR_FROM)
    e.add_argument("--to", dest="year_to", type=int, default=9999)
    e.set_defaults(func=cmd_export)
    i = sub.add_parser("import", help="브라우저 수집 원본(json.gz)을 저장소로 가져오기")
    i.add_argument("file")
    i.set_defaults(func=cmd_import)
    a = p.parse_args(argv)
    a.func(a)


if __name__ == "__main__":
    main()
