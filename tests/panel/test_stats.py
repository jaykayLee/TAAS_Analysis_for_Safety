import sys, json, asyncio
from playwright.async_api import async_playwright
LIB=sys.argv[1]; OUT=sys.argv[2]
SP = __import__("os").environ.get("CHARTJS_DIR", str(__import__("pathlib").Path(__file__).resolve().parents[2]))
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); ctx=await b.new_context(viewport={"width":1500,"height":1000},accept_downloads=True); pg=await ctx.new_page()
        await pg.route('**/chart.umd.min.js',lambda r:r.fulfill(path=SP+'/node_modules/chart.js/dist/chart.umd.js',content_type='text/javascript'))
        await pg.route('**/fonts.googleapis.com/**',lambda r:r.fulfill(body='',content_type='text/css'))
        errs=[]; pg.on("pageerror",lambda e:errs.append(str(e))); pg.on("console",lambda m:m.type=="error" and errs.append(m.text))
        await pg.goto(f"file://{LIB}/panel.html"); await pg.wait_for_timeout(2000)
        await pg.evaluate("localStorage.clear()")
        await pg.evaluate("""()=>{const D=TAAS_DEBUG(); [9001,7196,7240,7030,1].forEach(p=>D.S.checked.add(p));}""")
        await pg.fill("#q","x"); await pg.fill("#q","")
        await pg.click("#btnStatGo"); await pg.wait_for_timeout(4000)
        print("pool", await pg.inner_text("#sPool"))
        pool=await pg.evaluate("()=>TAAS_DEBUG().yearPool().map(c=>({no:c.no,name:c.name,pts:Object.fromEntries(c.pts)}))")
        json.dump(pool,open(OUT+"_pool.json","w"),ensure_ascii=False)
        print("series", len(pool)); [print(" ",c["no"],c["name"][:70]) for c in pool]
        for m in ["trend","lag","ols","pca","its"]:
            await pg.click(f"#stabs button[data-m={m}]"); await pg.wait_for_timeout(900)
            if m=="lag": await pg.check("#gAll"); await pg.wait_for_timeout(900)
            if m=="its": await pg.click(".presets [data-y='2020']>>nth=1"); await pg.wait_for_timeout(700)
            cur=await pg.evaluate(f"()=>TAAS_DEBUG().S.cur['{m}']")
            json.dump(cur,open(f"{OUT}_{m}.json","w"),ensure_ascii=False)
            print(m,"rows",len(cur))
            await pg.screenshot(path=f"{OUT}_{m}.png",full_page=True)
            await pg.click(f"[data-add={m}]"); await pg.wait_for_timeout(200)
        await pg.click("#stabs button[data-m=res]"); await pg.wait_for_timeout(600)
        print("res", await pg.inner_text("#rSum"))
        async with pg.expect_download() as d: await pg.click("#rCsv")
        dl=await d.value; await dl.save_as(OUT+"_results.csv"); print("csv", dl.suggested_filename)
        await pg.screenshot(path=f"{OUT}_res.png")
        print("errors",errs); await b.close()
asyncio.run(main())
