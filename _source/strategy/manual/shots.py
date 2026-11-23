import asyncio
from playwright.async_api import async_playwright
import os, pathlib
ROOT=pathlib.Path(__file__).resolve().parents[3]
SP=os.environ.get('CHARTJS_DIR',str(ROOT))
PANEL=(ROOT/'01_Panel'/'Main'/'TAAS_분석패널_offline.html').as_uri()
OUT=str(pathlib.Path(__file__).resolve().parent/'img')+'/'
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox','--allow-file-access-from-files'])
        pg=await b.new_page(viewport={'width':1440,'height':900},device_scale_factor=2,color_scheme='light')
        await pg.route('**/chart.umd.min.js',lambda r: r.fulfill(path=SP+'/node_modules/chart.js/dist/chart.umd.js',content_type='text/javascript'))
        await pg.route('**/fonts.googleapis.com/**',lambda r: r.fulfill(body='',content_type='text/css'))
        errs=[]; pg.on('pageerror',lambda e: errs.append(str(e)))
        await pg.goto(PANEL); await pg.wait_for_timeout(3000)
        await pg.screenshot(path=OUT+'01_main.png')
        # 상단 영역 / 컨트롤 영역 클립
        await pg.screenshot(path=OUT+'02_controls.png',clip={'x':300,'y':60,'width':1140,'height':330})
        # 검색
        await pg.fill('#q','음주'); await pg.wait_for_timeout(600)
        await pg.screenshot(path=OUT+'03_search.png',clip={'x':0,'y':60,'width':330,'height':520})
        await pg.fill('#q',''); await pg.wait_for_timeout(300)
        # 값 변환: 비중
        await pg.select_option('#selNorm','share'); await pg.wait_for_timeout(800)
        await pg.screenshot(path=OUT+'04_share.png',clip={'x':310,'y':380,'width':1130,'height':480})
        await pg.select_option('#selNorm','raw'); await pg.wait_for_timeout(500)
        # 가로축 = 사고유형 대분류 (막대)
        opts=await pg.eval_on_selector_all('#selX option','os=>os.map(o=>[o.value,o.textContent])')
        v=[o[0] for o in opts if '대분류' in o[1]]
        if v:
            await pg.select_option('#selX',v[0]); await pg.wait_for_timeout(500)
            sopts=await pg.eval_on_selector_all('#selS option','os=>os.map(o=>[o.value,o.textContent])')
            await pg.select_option('#selS','year') if any(o[0]=='year' for o in sopts) else None
            await pg.fill('#y0','2021'); await pg.dispatch_event('#y0','change'); await pg.wait_for_timeout(800)
            await pg.screenshot(path=OUT+'05_xaxis.png',clip={'x':310,'y':60,'width':1130,'height':830})
        # 표 영역
        await pg.goto(PANEL); await pg.wait_for_timeout(2500)
        el=await pg.query_selector('#tbl'); await el.scroll_into_view_if_needed(); await pg.wait_for_timeout(300)
        bb=await (await pg.query_selector('#tbl')).bounding_box()
        await pg.screenshot(path=OUT+'06_table.png',clip={'x':bb['x']-20,'y':max(0,bb['y']-50),'width':bb['width']+40,'height':min(420,bb['height']+110)})
        # 차량기술 매핑
        await pg.click('#tab-tech'); await pg.wait_for_timeout(800); await pg.evaluate('scrollTo(0,0)')
        await pg.screenshot(path=OUT+'07_tech.png')
        # 카드 추가 → 상관분석 : AEB(추돌), 음주, 노면
        cards=await pg.query_selector_all('.tech')
        for i in (0,5,6):
            btns=await cards[i].query_selector_all('button'); await btns[1].click(); await pg.wait_for_timeout(1500)
            await pg.click('#tab-tech'); await pg.wait_for_timeout(500); cards=await pg.query_selector_all('.tech')
        await pg.click('#tab-corr'); await pg.wait_for_timeout(1500); await pg.evaluate('scrollTo(0,0)')
        await pg.screenshot(path=OUT+'08_corr.png',full_page=True)
        # 그래프 조작 (기준선 M1/M2 + 메모)
        await pg.click('#tab-explore'); await pg.fill('#q','월별·요일별'); await pg.wait_for_timeout(300)
        await pg.evaluate("[...document.querySelectorAll('.tree button.item')].find(x=>x.textContent==='월별·요일별 교통사고').click()"); await pg.wait_for_timeout(1500)
        for t in ['01월','03월','04월','05월','06월','07월','08월','09월','10월','11월']: await pg.click(f'.chip:has-text("{t}")')
        await pg.wait_for_timeout(500)
        await pg.set_viewport_size({'width':1440,'height':1600}); await pg.wait_for_timeout(500)
        card=await pg.query_selector('#cbox'); await card.scroll_into_view_if_needed(); await pg.wait_for_timeout(300)
        box=await card.bounding_box(); ca=await pg.evaluate("(()=>{const a=Chart.getChart(document.querySelector('#chart')).chartArea;return [a.left,a.top,a.right,a.bottom]})()")
        X=lambda f: box['x']+ca[0]+(ca[2]-ca[0])*f; Y=lambda f: box['y']+ca[1]+(ca[3]-ca[1])*f
        await pg.mouse.click(X(0.33),Y(0.5)); await pg.wait_for_timeout(400)
        await pg.keyboard.down('Control'); await pg.mouse.click(X(0.88),Y(0.5)); await pg.keyboard.up('Control'); await pg.wait_for_timeout(400)
        await pg.mouse.dblclick(X(0.62),Y(0.25)); await pg.wait_for_timeout(300); await pg.keyboard.type('2020 이후 2월 증가'); await pg.mouse.click(5,5); await pg.wait_for_timeout(300)
        await pg.mouse.move(X(0.5),Y(0.6)); await pg.wait_for_timeout(200)
        h3=await pg.query_selector('#chartTitle'); hb=await h3.bounding_box(); mb=await (await pg.query_selector('#mbar')).bounding_box()
        await pg.screenshot(path=OUT+'09_cursor.png',clip={'x':hb['x']-16,'y':hb['y']-14,'width':box['width']+32,'height':mb['y']+mb['height']-hb['y']+24})
        await b.close(); print('errors',errs)
asyncio.run(main())
