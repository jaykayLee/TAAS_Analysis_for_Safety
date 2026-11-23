import sys, asyncio
from playwright.async_api import async_playwright

LIB = sys.argv[1]
OUT = sys.argv[2] if len(sys.argv) > 2 else "/tmp/multi"


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1500, "height": 1000})
        SP = __import__("os").environ.get("CHARTJS_DIR", str(__import__("pathlib").Path(__file__).resolve().parents[3]))
        import os
        for c in [SP]:
            if os.path.exists(c + "/node_modules/chart.js/dist/chart.umd.js"): SP = c; break
        await pg.route('**/chart.umd.min.js', lambda r: r.fulfill(path=SP + '/node_modules/chart.js/dist/chart.umd.js', content_type='text/javascript'))
        await pg.route('**/fonts.googleapis.com/**', lambda r: r.fulfill(body='', content_type='text/css'))
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda m: m.type == "error" and errs.append(m.text))
        await pg.goto(f"file://{LIB}/panel.html")
        await pg.wait_for_timeout(2500)
        # 인구 장표 탐색
        await pg.fill("#q", "인구")
        await pg.wait_for_timeout(300)
        await pg.click("text=연령구분별 인구 (어린이·일반·노인)")
        await pg.wait_for_timeout(1200)
        await pg.screenshot(path=f"{OUT}_explore.png")
        print("explore title", await pg.inner_text("#chartTitle"))
        # 체크: 인구 + 어린이 사고 + 노인 사고
        await pg.evaluate("localStorage.clear()")
        for q, nm in [("인구", "연령구분별 인구 (어린이·일반·노인)"), ("어린이", "월별·요일별 (어린이) 교통사고"), ("노인", "월별·요일별 (노인) 교통사고")]:
            await pg.fill("#q", q)
            await pg.wait_for_timeout(300)
            row = pg.locator(".irow", has=pg.locator(f"button.item:text-is('{nm}')"))
            await row.locator("input").check()
        print("checked", await pg.inner_text("#ckN"))
        await pg.click("#btnMulti")
        await pg.wait_for_timeout(2500)
        print("corrN", await pg.inner_text("#corrN"))
        print("sets", await pg.locator(".setbox").count(), "series", await pg.locator("#slist .sitem").count())
        print("trend title", await pg.inner_text("#trTitle"))
        print("matrix cells", await pg.locator("#cmat td").count())
        await pg.screenshot(path=f"{OUT}_corr.png", full_page=True)
        # 비율 환산: 어린이 인구 기준
        opts = await pg.eval_on_selector_all("#cRate option", "o=>o.map(x=>x.value)")
        den = next((o for o in opts if "어린이 0~12세" in o), None)
        if den:
            await pg.select_option("#cRate", den)
            await pg.wait_for_timeout(800)
            print("rate trend", await pg.inner_text("#trTitle"))
        # 트렌드 클릭 → M1
        await pg.locator("#trend").scroll_into_view_if_needed()
        box = await pg.locator("#trend").bounding_box()
        await pg.mouse.click(box["x"] + box["width"] * 0.6, box["y"] + box["height"] * 0.5)
        await pg.wait_for_timeout(500)
        await pg.keyboard.down("Control"); await pg.mouse.click(box["x"] + box["width"] * 0.9, box["y"] + box["height"] * 0.5); await pg.keyboard.up("Control")
        await pg.wait_for_timeout(500)
        await pg.screenshot(path=f"{OUT}_trend.png")
        print("tbar", (await pg.inner_text("#tbar"))[:200].replace("\n", " | "))
        # 조건 바꾸기: 어린이 사고 장표의 수치항목 변경
        sel = pg.locator(".setbox").nth(1).locator("select[data-k=m]")
        opts2 = await sel.evaluate("s=>[...s.options].map(o=>o.text)")
        print("measures", opts2)
        await sel.select_option(index=min(1, len(opts2) - 1))
        await pg.wait_for_timeout(800)
        await pg.screenshot(path=f"{OUT}_corr2.png", full_page=True)
        print("errors", errs)
        await b.close()

asyncio.run(main())
