import asyncio, json
from playwright.async_api import async_playwright
SP = __import__('os').environ.get('CHARTJS_DIR', str(__import__('pathlib').Path(__file__).resolve().parents[3]))
PANEL=(__import__('pathlib').Path(__file__).resolve().parents[3]/'04_Libraries'/'02_Statistics'/'LIB-TAAS'/'build'/'panel.html').as_uri()
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
        pg=await b.new_page(viewport={'width':1440,'height':900})
        await pg.route('**/chart.umd.min.js',lambda r: r.fulfill(path=SP+'/node_modules/chart.js/dist/chart.umd.js',content_type='text/javascript'))
        await pg.route('**/fonts.googleapis.com/**',lambda r: r.fulfill(body='',content_type='text/css'))
        errs=[]; pg.on('pageerror',lambda e: errs.append(str(e)))
        await pg.goto(PANEL); await pg.wait_for_timeout(2000)
        pids=await pg.evaluate("TAAS_INDEX.patterns.filter(p=>p.n_facts>0).map(p=>[p.pid,p.name])")
        await pg.evaluate("document.querySelectorAll('.tree details').forEach(d=>d.open=true)")
        res=[]
        for pid,name in pids:
            # 목록 버튼 클릭
            ok=await pg.evaluate(f"""(()=>{{const b=[...document.querySelectorAll('.tree button.item')].find(x=>x.textContent==={json.dumps(name)}); if(!b) return false; b.click(); return true}})()""")
            if not ok: res.append([pid,name,'nobutton']); continue
            for _ in range(40):
                await pg.wait_for_timeout(100)
                done=await pg.evaluate(f"document.getElementById('pTitle').textContent==={json.dumps(name)} && (document.querySelector('#tbl table')||document.querySelector('#tbl .empty'))")
                if done: break
            await pg.wait_for_timeout(120)
            st=await pg.evaluate("""(()=>{const c=Chart.getChart(document.querySelector('#chart'));const n=c?c.data.datasets.length:0;
              const vals=c?c.data.datasets.reduce((a,d)=>a+d.data.filter(v=>v!=null).length,0):0;
              const chips=[...document.querySelectorAll('.dimbox .chip[aria-pressed=true]')];return {n,vals,chips:chips.length,empty:!!document.querySelector('#tbl .empty'),cols:document.querySelectorAll('#tbl thead th').length}})()""")
            # 칩 하나 끄기 → 바뀌는지
            chg=None
            if st['chips']>1:
                before=await pg.evaluate("document.querySelector('#tbl').innerText.length")
                await pg.evaluate("document.querySelector('.dimbox .chip[aria-pressed=true]').click()"); await pg.wait_for_timeout(150)
                after=await pg.evaluate("document.querySelector('#tbl').innerText.length")
                chg=before!=after
            res.append([pid,name,st,chg])
        bad=[r for r in res if r[2]=='nobutton' or r[2]['vals']==0 or r[3] is False]
        print('checked',len(res),'bad',len(bad))
        for r in bad[:40]: print(r)
        print('errors',errs[:5])
        json.dump(res,open('sweep.json','w'),ensure_ascii=False)
        await b.close()
asyncio.run(main())
