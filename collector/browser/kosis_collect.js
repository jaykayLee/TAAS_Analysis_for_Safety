// KOSIS 통계표 수집기 — 사용자 PC 브라우저(Claude 앱 내장 브라우저)에서 kosis.kr 페이지에 주입해 씁니다.
// 통계표 화면(statHtml)을 숨은 iframe 으로 열고, 화면의 [다운로드] 와 같은 요청(downGrid.do → downNormal.do, CSV)을
// 원하는 기간·항목·분류로 직접 보냅니다. 결과는 CSV 텍스트(EUC-KR 해독)로 window.__kc.out[key] 에 쌓입니다.
//
//   await KC.info('101','DT_1B04005N')            분류·항목·주기 확인
//   KC.run([{key, orgId, tblId, prd:'Y', from:2011, to:2025, levels:{A:1}, items:null, only:{A:['00','11']}}, …])
//   KC.status()                                    → {done, total, current, errors}
//   KC.dump(keys)                                  → 큰 문자열(그대로 반환하면 도구가 파일로 저장)
(() => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const st = window.__kc = window.__kc || { out: {}, err: {}, meta: {}, running: false, done: 0, total: 0, current: '' };

  async function openTable(orgId, tblId) {
    const old = document.getElementById('kc_frame'); if (old) old.remove();
    const f = document.createElement('iframe'); f.id = 'kc_frame';
    f.style.cssText = 'width:1400px;height:900px;position:absolute;left:-6000px;top:0';
    document.body.appendChild(f);
    f.src = `/statHtml/statHtml.do?orgId=${orgId}&tblId=${tblId}&conn_path=I2`;
    const t0 = Date.now();
    while (Date.now() - t0 < 60000) {
      await sleep(700);
      try {
        const r = f.contentWindow.document.getElementById('iframe_rightMenu');
        const c = r && r.contentWindow.document.getElementById('iframe_centerMenu1');
        const W = c && c.contentWindow;
        const fm = W && W.document.forms.ParamInfo;
        if (fm && fm.fieldList && fm.fieldList.value && W.$ && W.$.ui && W.$.ui.fancytree && W.document.getElementById('fancytree_0')) return W;
      } catch (e) { }
    }
    throw new Error('통계표 화면을 열지 못했습니다: ' + orgId + '/' + tblId);
  }

  function trees(W) {
    const $ = W.$, out = { items: [], classes: [], periods: [], name: W.document.forms.ParamInfo.tblNm.value };
    W.document.querySelectorAll('[id^=fancytree_]').forEach(el => {
      let t; try { t = $.ui.fancytree.getTree('#' + el.id) } catch (e) { return }
      if (!t) return;
      const nodes = []; t.visit(nd => { nodes.push({ code: nd.data.itmId, name: nd.title, lvl: nd.data.lvl || nd.getLevel(), up: nd.data.upItmId || '', ov: nd.data.objVarId }) });
      if (el.id === 'fancytree_0') out.items = nodes; else out.classes.push({ tree: el.id, objVarId: nodes[0] && nodes[0].ov, nodes });
    });
    out.periods = (W.document.forms.ParamInfo.periodStr.value || '').split('#').filter(Boolean);
    return out;
  }

  async function info(orgId, tblId) {
    const W = await openTable(orgId, tblId); const t = trees(W);
    return { name: t.name, periods: t.periods, items: t.items.map(n => n.code + ':' + n.name),
             classes: t.classes.map(c => ({ objVarId: c.objVarId, n: c.nodes.length, levels: [...new Set(c.nodes.map(n => n.lvl))],
               lvl1: c.nodes.filter(n => n.lvl == 1).slice(0, 40).map(n => n.code + ':' + n.name) })) };
  }

  async function down(W, fieldList, rowAxis, colAxis) {
    const f = W.document.forms.ParamInfo, fd = new URLSearchParams(new W.FormData(f));
    const set = (k, v) => { fd.delete(k); fd.set(k, v) };
    set('fieldList', JSON.stringify(fieldList)); set('view', 'csv'); set('viewSubKind', '2_3'); set('viewKind', '2');
    set('downGridFileType', 'csv'); set('downGridCsvType', 'ANSI'); set('smblYn', 'Y'); set('expDash', 'Y'); set('dataOpt', 'ko');
    set('periodCo', '99'); set('prdSort', 'asc'); set('downSort', 'asc'); set('rowAxis', rowAxis); set('colAxis', colAxis); set('usePivot', 'Y');
    const r = await fetch('/statHtml/downGrid.do', { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'X-Requested-With': 'XMLHttpRequest' }, body: fd.toString() });
    const j = await r.json().catch(() => ({}));
    if (!j.file) throw new Error('downGrid: ' + JSON.stringify(j).slice(0, 200));
    fd.set('file', j.file);
    const r2 = await fetch('/statHtml/downNormal.do', { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: fd.toString() });
    return new TextDecoder('euc-kr').decode(await r2.arrayBuffer());
  }

  // job: {key, orgId, tblId, prd:'Y'|'M', from, to, months:['12'], levels:{A:1}, items:[codes]|null, only:{A:[codes]}}
  async function fetchJob(job) {
    const W = await openTable(job.orgId, job.tblId); const t = trees(W);
    const prd = job.prd || (t.periods.includes('Y') ? 'Y' : t.periods[0]);
    const per = [];
    for (let y = job.from; y <= job.to; y++) {
      if (prd === 'Y') per.push(String(y));
      else if (prd === 'M') (job.months || ['12']).forEach(m => per.push(y + m));
      else if (prd === 'H') per.push(y + '02');
      else if (prd === 'Q') per.push(y + '04');
    }
    const fl = [{ targetId: 'PRD', targetValue: '', prdValue: prd + ',' + per.join(',') + ',@' }];
    const items = job.items || t.items.map(n => n.code);
    items.forEach(c => fl.push({ targetId: 'ITM_ID', targetValue: c, prdValue: '' }));
    const axes = [];
    t.classes.forEach((c, i) => {
      const L = (job.levels || {})[c.objVarId] || 1, only = (job.only || {})[c.objVarId];
      const pick = c.nodes.filter(n => (only ? only.includes(n.code) : n.lvl <= L));
      pick.forEach(n => fl.push({ targetId: `OV_L${i + 1}_ID`, targetValue: n.code, prdValue: '' }));
      axes.push(c.objVarId);
    });
    const csv = await down(W, fl, axes.concat(['ITEM']).join(','), 'TIME');
    st.meta[job.key] = { name: t.name, orgId: job.orgId, tblId: job.tblId, prd, from: job.from, to: job.to, cells: fl.length, at: new Date().toISOString() };
    return csv;
  }

  async function run(jobs) {
    if (st.running) return '이미 실행 중';
    st.running = true; st.total = jobs.length; st.done = 0; st.err = {};
    (async () => {
      for (const j of jobs) {
        st.current = j.key;
        for (let a = 0; a < 2; a++) {
          try { st.out[j.key] = await fetchJob(j); delete st.err[j.key]; break }
          catch (e) { st.err[j.key] = String(e).slice(0, 300); await sleep(3000) }
        }
        st.done++;
      }
      st.running = false; st.current = '';
    })();
    return 'started ' + jobs.length;
  }

  const status = () => ({ running: st.running, done: st.done, total: st.total, current: st.current, errors: st.err,
    have: Object.fromEntries(Object.entries(st.out).map(([k, v]) => [k, v.length])) });
  // 반환 문자열이 커야(약 10만 자 이상) 도구가 파일로 저장 → 클라우드에서 그대로 읽음
  const dump = keys => { const o = {}; (keys || Object.keys(st.out)).forEach(k => { o[k] = { meta: st.meta[k], csv: st.out[k] } });
    const s = JSON.stringify(o); return '<<KC>>' + s + '<<KC>>' + ' '.repeat(Math.max(0, 120000 - s.length)) };

  window.KC = { info, run, status, dump, fetchJob, openTable, trees };
  return 'KC ready';
})();
