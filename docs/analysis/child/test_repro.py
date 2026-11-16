"""패널 재현 시험 — 설명서의 순서를 그대로 클릭해 같은 수치가 나오는지 확인"""
import asyncio, json, sys
from playwright.async_api import async_playwright
SP = "/tmp/claude-0/-home-claude/0273b183-29fa-51a8-bda9-5907ce493a03/scratchpad"
LIB = "/home/claude/taas_analysis_for_safety/library"
SHOT = "/home/claude/child_analysis/shots/"
TABLES = [("7199", "사고유형별·시간대별 (어린이) 교통사고"), ("7194", "시도 시군구별 (어린이) 교통사고"), ("9001", "연령구분별 인구 (어린이·일반·노인)"),
          ("1", "주요 교통지표의 추이"), ("19", "교통안전시설"), ("9003", "어린이보호구역 지정 현황")]


async def setsel(pg, set_name, label, option_text):
    box = pg.locator(".setbox", has=pg.locator(f"b:has-text('{set_name}')"))
    field = box.locator(".field", has=pg.locator(f"label:text-is('{label}')"))
    sel = field.locator("select")
    opts = await sel.evaluate("s=>[...s.options].map(o=>o.text)")
    idx = next(i for i, o in enumerate(opts) if o == option_text)
    await sel.select_option(index=idx)
    await pg.wait_for_timeout(700)


async def main():
    import os; os.makedirs(SHOT, exist_ok=True)
    out = {}
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page(viewport={"width": 1500, "height": 950})
        await pg.route('**/chart.umd.min.js', lambda r: r.fulfill(path=SP + '/node_modules/chart.js/dist/chart.umd.js', content_type='text/javascript'))
        await pg.route('**/fonts.googleapis.com/**', lambda r: r.fulfill(body='', content_type='text/css'))
        errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto(f"file://{LIB}/panel.html"); await pg.wait_for_timeout(2000)
        await pg.evaluate("localStorage.clear()")
        # 1) 장표 체크
        for pid, nm in TABLES:
            await pg.fill("#q", nm); await pg.wait_for_timeout(250)
            row = pg.locator(".irow", has=pg.locator(f"button.item:text-is('{nm}')")).first
            await row.locator("input").check()
        await pg.fill("#q", "어린이"); await pg.wait_for_timeout(300)
        await pg.screenshot(path=SHOT + "01_check.png")
        # 2) 상관관계 분석
        await pg.fill("#q", ""); await pg.click("#btnMulti"); await pg.wait_for_timeout(3500)
        # 3) 조건 바꾸기
        await setsel(pg, "사고유형별·시간대별 (어린이) 교통사고", "사고유형 대분류", "▦ 계열로 나누기")
        await setsel(pg, "연령구분별 인구", "수치항목", "인구_연간보간[명]")
        await setsel(pg, "주요 교통지표의 추이", "분석지표 (지표)", "자동차등록대수(대)")
        await setsel(pg, "주요 교통지표의 추이", "세부1 (지표)", "지표")
        await setsel(pg, "교통안전시설", "안전시설물 대분류", "신호기")
        await setsel(pg, "교통안전시설", "안전시설물", "보행등")
        names = await pg.evaluate("()=>TAAS_DEBUG().S.corr.map(c=>c.name)")
        out["series"] = names
        await pg.screenshot(path=SHOT + "02_sets.png", full_page=False)
        # 4) 비율 환산: 어린이 인구 10만 명당
        opts = await pg.eval_on_selector_all("#cRate option", "o=>o.map(x=>x.value)")
        den = next(o for o in opts if "인구_연간보간" in o and "어린이 0~12세" in o)
        await pg.select_option("#cRate", den); await pg.select_option("#tNorm", "raw"); await pg.wait_for_timeout(900)
        pool = await pg.evaluate("()=>TAAS_DEBUG().yearPool().map(c=>({no:c.no,name:c.name,v2005:c.pts.get('2005'),v2025:c.pts.get('2025')}))")
        out["rate_pool"] = pool
        await pg.locator("#trCard").scroll_into_view_if_needed(); await pg.screenshot(path=SHOT + "03_rate.png")
        # 5) 통계 기법 ① 추세
        await pg.click("#tab-stat"); await pg.wait_for_timeout(800)
        await pg.click("#stabs button[data-m=trend]"); await pg.wait_for_timeout(900)
        out["trend"] = await pg.evaluate("()=>TAAS_DEBUG().S.cur.trend.filter(r=>/차대사람|차대차/.test(r.대상)).map(r=>[r.대상.slice(-30),r.통계량,r.값,r.p값])")
        await pg.screenshot(path=SHOT + "04_trend.png")
        # ⑤ 중단 시계열 2020 로그
        await pg.click("#stabs button[data-m=its]"); await pg.fill("#iYear", "2020"); await pg.select_option("#iMode", "log")
        await pg.dispatch_event("#iYear", "change"); await pg.wait_for_timeout(900)
        out["its"] = await pg.evaluate("()=>TAAS_DEBUG().S.cur.its.filter(r=>/차대사람|차대차/.test(r.대상)&&/수준|기울기 변화|개입 전/.test(r.항목)).map(r=>[r.대상.slice(-30),r.항목,r.값,r.p값,r.비고])")
        await pg.screenshot(path=SHOT + "05_its.png")
        # ③ 다중회귀 (비율 환산 끄고, 로그, 더미 2020-2021)
        await pg.click("#tab-corr"); await pg.select_option("#cRate", ""); await pg.wait_for_timeout(500)
        await pg.click("#tab-stat"); await pg.click("#stabs button[data-m=ols]"); await pg.wait_for_timeout(500)
        ped = next(n for n in names if "사고유형별·시간대별" in n and "차대사람" in n)
        await pg.select_option("#oY", ped); await pg.select_option("#oMode", "log"); await pg.fill("#oDummy", "2020-2021"); await pg.dispatch_event("#oDummy", "change"); await pg.wait_for_timeout(600)
        async def setX(keys):
            for _ in range(40):  # 체크할 때마다 목록이 다시 그려지므로 매번 새로 읽음
                st = await pg.eval_on_selector_all("#oX input", "l=>l.map(x=>[x.value,x.checked])")
                bad = [i for i, (v, c) in enumerate(st) if c != any(all(k in v for k in ks) for ks in keys)]
                if not bad: return
                await pg.locator("#oX input").nth(bad[0]).click(); await pg.wait_for_timeout(300)
        await setX([("인구_연간보간", "어린이 0~12세"), ("자동차등록대수",)]); await pg.wait_for_timeout(800)
        out["ols_exposure"] = await pg.evaluate("()=>TAAS_DEBUG().S.cur.ols.filter(r=>r.항목==='계수'||r.통계량==='R²').map(r=>[r.상대.slice(-28),r.통계량,r.값,r.p값])")
        await pg.screenshot(path=SHOT + "06_ols.png", full_page=True)
        await pg.fill("#sY0", "2009"); await pg.fill("#sY1", "2024"); await pg.dispatch_event("#sY1", "change"); await pg.wait_for_timeout(500)
        await setX([("인구_연간보간", "어린이 0~12세"), ("지정개소",), ("보행등",)]); await pg.wait_for_timeout(800)
        out["ols_infra"] = await pg.evaluate("()=>TAAS_DEBUG().S.cur.ols.filter(r=>r.항목==='계수'||r.통계량==='R²').map(r=>[r.상대.slice(-28),r.통계량,r.값,r.p값])")
        out["errors"] = errs
        await b.close()
    json.dump(out, open("/home/claude/child_analysis/repro.json", "w"), ensure_ascii=False, indent=1, default=str)
    print(json.dumps(out, ensure_ascii=False, indent=1, default=str)[:6000])

asyncio.run(main())
