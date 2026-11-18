"""
부처 라이브러리(ext) 패널 시험 — 로컬(panel.html)·온라인(panel_online.html, http)·예시(panel_sample.html) 세 방식에서
  1) 부처 장표가 목록에 붙고(9001·9003·9901 …) 데이터가 열리는지
  2) 비율 환산 배율(×1만 등)과 이름(…당)이 맞는지
  3) 중단 시계열 '빠른 선택'에 제도 연표 버튼이 생기고, 누르면 개입 연도가 바뀌는지
  4) 추세 비교의 '제도 시행' 세로선 표시가 오류 없이 켜지는지
  5) 업데이트 창의 부처 자료 목록이 그려지는지 (온라인)

    python tests/panel/test_ext.py "$PWD/library"
"""
import asyncio, functools, http.server, json, os, sys, threading
from pathlib import Path
from playwright.async_api import async_playwright

LIB = Path(sys.argv[1]).resolve()
SP = os.environ.get("CHARTJS_DIR", str(Path(__file__).resolve().parents[2]))


def serve():
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a, **k):
            pass
    h = functools.partial(Q, directory=str(LIB))
    s = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s


async def check(pg, label, errs, online=False):
    out = {}
    ext = await pg.evaluate("()=>{const S=TAAS_DEBUG().S; return {n:S.index.patterns.length, ext:S.index.patterns.filter(p=>p.lib).map(p=>p.pid), ev:S.events.length, mode:S.mode}}")
    out["patterns"], out["ext_pids"], out["events"], out["mode"] = ext["n"], ext["ext"], ext["ev"], ext["mode"]
    assert 9001 in ext["ext"] and 9901 in ext["ext"], ext
    assert ext["ev"] >= 10, ext
    # 9901 열기
    await pg.evaluate("()=>{const D=TAAS_DEBUG(); D.S.checked.clear(); [9001,9901,7196].forEach(p=>D.S.checked.add(p))}")
    await pg.fill("#q", "x"); await pg.fill("#q", "")
    await pg.click("#btnMulti"); await pg.wait_for_timeout(3500)
    names = await pg.evaluate("()=>TAAS_DEBUG().S.corr.map(c=>c.name)")
    out["series"] = len(names)
    assert any("제도 시행" in n for n in names), names[:5]
    # 비율 환산: 분모 = 9001 전체, 배율 1만
    den = next(n for n in names if "연령구분별 인구" in n and "전체" in n)
    await pg.select_option("#cRate", den); await pg.select_option("#cRateK", "10000"); await pg.wait_for_timeout(600)
    pool = await pg.evaluate("()=>TAAS_DEBUG().yearPool().map(c=>c.name)")
    out["rate_names"] = [n for n in pool if "당)" in n][:2]
    assert not any("[0/1]" in n and "당)" in n for n in pool), "제도 더미가 비율 환산됨"
    assert any("(1만 명당)" in n for n in pool), pool
    await pg.select_option("#cRateK", "100000"); await pg.wait_for_timeout(300)
    pool = await pg.evaluate("()=>TAAS_DEBUG().yearPool().map(c=>c.name)")
    assert any("(10만 명당)" in n for n in pool), pool
    await pg.select_option("#cRate", "")
    # 제도 시행 세로선
    await pg.check("#tEv"); await pg.wait_for_timeout(500)
    # 중단 시계열 제도 버튼
    await pg.click("#tab-stat") if await pg.query_selector("#tab-stat") else None
    n_btn = await pg.evaluate("()=>document.querySelectorAll('#evPresets [data-y]').length")
    out["its_buttons"] = n_btn
    assert n_btn >= 10
    await pg.evaluate("()=>{const b=[...document.querySelectorAll('#evPresets [data-y]')].find(x=>x.dataset.y==='2021'); b.click()}")
    yv = await pg.input_value("#iYear"); assert yv == "2021", yv
    out["evWarn"] = await pg.inner_text("#evWarn")
    # 분석 묶음(프리셋): 켜진 묶음마다 계열이 생기고 오류가 없어야 함
    pr = await pg.evaluate("()=>[...document.querySelectorAll('#cPresets [data-pr]')].filter(b=>!b.disabled).map(b=>b.dataset.pr)")
    out["presets"] = {}
    for k in pr:
        await pg.evaluate(f"()=>document.querySelector('[data-pr={k}]').click()"); await pg.wait_for_timeout(2500)
        r = await pg.evaluate("()=>{const D=TAAS_DEBUG(); const p=D.yearPool(); return {n:p.length, den:D.S.rateDen, rated:p.filter(c=>/당\)$/.test(c.name)).length}}")
        assert r["n"] >= 2, (k, r)
        out["presets"][k] = r
    if label != "sample":  # 예시판은 일부 장표만 실어 묶음 대부분이 꺼짐
        assert {"exposure", "drunk", "speed", "child", "elderly"} <= set(pr), pr
        assert out["presets"]["child"]["rated"] == 2, out["presets"]["child"]  # 사고·사망만 나눔(보호구역·카메라는 그대로)  # 사고·사망만 나눔(보호구역·카메라는 그대로)
    if online:
        await pg.evaluate("()=>{document.getElementById('updDlg').hidden=false}")
        await pg.evaluate("()=>document.getElementById('btnUpd').click()")
        await pg.wait_for_timeout(800)
        rows = await pg.evaluate("()=>document.querySelectorAll('#extRows .extrow').length")
        out["ext_rows"] = rows
        assert rows >= 3, rows
    assert not errs, errs
    print(label, json.dumps(out, ensure_ascii=False))


async def main():
    srv = serve(); port = srv.server_address[1]
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for label, url, online in [("local", f"file://{LIB}/panel.html", False), ("online", f"http://127.0.0.1:{port}/panel_online.html", True),
                                   ("sample", f"file://{LIB}/panel_sample.html", False)]:
            ctx = await b.new_context(viewport={"width": 1500, "height": 1000}); pg = await ctx.new_page()
            await pg.route("**/chart.umd.min.js", lambda r: r.fulfill(path=SP + "/node_modules/chart.js/dist/chart.umd.js", content_type="text/javascript"))
            await pg.route("**/fonts.googleapis.com/**", lambda r: r.fulfill(body="", content_type="text/css"))
            errs = []; pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("console", lambda m: m.type == "error" and "favicon" not in m.text and errs.append(m.text))
            await pg.goto(url); await pg.wait_for_timeout(2500)
            await pg.evaluate("localStorage.clear()")
            await check(pg, label, errs, online)
            await ctx.close()
        await b.close()
    srv.shutdown()
    print("OK")


asyncio.run(main())
