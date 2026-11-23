// KOSIS 통계표 수집기 — 사용자 PC 의 브라우저(Claude 앱 내장 브라우저)에서 kosis.kr 페이지에 주입해 씁니다.
//
// 두 가지 길
//   1) OpenAPI (권장)  KC.run(jobs, {apiKey})   — 공식 OpenAPI(statisticsParameterData) 로 받음. 화면을 열지 않아 가볍고 차단 위험이 없음.
//   2) 화면 다운로드   KC.run(jobs)             — 통계표 화면(statHtml)을 숨은 iframe 으로 열고 [다운로드](CSV)와 같은 요청을 보냄.
//      화면 하나에 요청이 100개 넘게 나가므로, KOSIS 가 짧은 시간의 반복 접속을 '비정상 이용'으로 막을 수 있음
//      (2026-11-17 실제로 차단됨). 이 길은 표 사이에 간격(gapMs, 기본 60초)을 두고, 차단 응답이 오면 바로 멈춤.
//
// 결과는 OpenAPI 와 같은 긴 형식 레코드 배열 [{C1_NM, C2_NM, …, ITM_NM, UNIT_NM, PRD_DE, DT}] 로 window.__kc.out[key] 에 쌓이고,
// KC.dump() 가 큰 문자열로 돌려줍니다(10만 자 이상이면 도구가 파일로 저장 → 클라우드에서 그대로 읽음).
//
//   job = {key, orgId, tblId, prd:'Y'|'M', from, to, months:['12'], items:[ITM_ID]|null,
//          levels:{<분류ID>:1}, only:{<분류ID>:[코드]}, match:{<분류ID>:'^\\d{2}$'}}
//   분류ID 는 화면 길에서는 objVarId(A, B, 13101873443A …), OpenAPI 길에서는 OBJ_ID — 둘이 같은 값입니다.
(() => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const st = window.__kc = window.__kc || { out: {}, err: {}, meta: {}, running: false, done: 0, total: 0, current: '', blocked: false };
  const BLOCK = /비정상적인 서비스 이용|접근이 차단/;

  function periods(job, prd) {
    const per = [];
    for (let y = job.from; y <= job.to; y++) {
      if (prd === 'Y') per.push(String(y));
      else if (prd === 'M') (job.months || ['12']).forEach(m => per.push(y + m));
      else if (prd === 'Q') per.push(y + '04');
      else if (prd === 'H') per.push(y + '02');
    }
    return per;
  }
  // 분류 노드 고르기: only(코드 목록) > match(정규식) > levels(단계, 기본 1)
  function pick(nodes, id, job) {
    const only = (job.only || {})[id], re = (job.match || {})[id], L = (job.levels || {})[id] || 1;
    return nodes.filter(n => only ? only.includes(n.code) : re ? new RegExp(re).test(n.code) : n.lvl <= L);
  }

  /* ---------- 1) OpenAPI ---------- */
  async function apiGet(url) {
    const r = await fetch(url, { credentials: 'omit' });
    const t = await r.text();
    if (BLOCK.test(t)) { st.blocked = true; throw new Error('KOSIS 접근 차단 응답') }
    let j; try { j = JSON.parse(t) } catch (e) { throw new Error('응답이 JSON 이 아님: ' + t.slice(0, 160)) }
    if (j && !Array.isArray(j) && (j.err || j.errMsg)) throw new Error('OpenAPI 오류 ' + (j.err || '') + ' ' + (j.errMsg || ''));
    return j;
  }
  async function apiMeta(job, key) {
    const u = `https://kosis.kr/openapi/statisticsData.do?method=getMeta&type=ITM&apiKey=${encodeURIComponent(key)}&format=json&jsonVD=Y&orgId=${job.orgId}&tblId=${job.tblId}`;
    const rows = await apiGet(u);
    const items = [], cls = new Map();
    for (const r of rows) {
      if (r.OBJ_ID === 'ITEM' || r.OBJ_NM === '항목') { items.push({ code: r.ITM_ID, name: r.ITM_NM }); continue }
      if (!cls.has(r.OBJ_ID)) cls.set(r.OBJ_ID, { id: r.OBJ_ID, name: r.OBJ_NM, sn: +r.OBJ_ID_SN || cls.size + 1, nodes: [] });
      cls.get(r.OBJ_ID).nodes.push({ code: r.ITM_ID, name: r.ITM_NM, up: r.UP_ITM_ID || '' });
    }
    for (const c of cls.values()) { // 단계 = 상위 코드를 따라 올라간 횟수 + 1
      const by = new Map(c.nodes.map(n => [n.code, n]));
      for (const n of c.nodes) { let l = 1, u = n.up; while (u && by.has(u) && l < 9) { l++; u = by.get(u).up } n.lvl = l }
    }
    return { items, classes: [...cls.values()].sort((a, b) => a.sn - b.sn) };
  }
  async function apiJob(job, key) {
    const M = await apiMeta(job, key);
    const prd = job.prd || 'Y';
    const objL = M.classes.map(c => pick(c.nodes, c.id, job).map(n => n.code));
    const itm = (job.items || M.items.map(n => n.code));
    const rows = [];
    // 4만 셀 제한 → 기간을 나눠 요청 (월자료는 해당 월만)
    const per = periods(job, prd);
    const cellsPer = itm.length * objL.reduce((a, l) => a * Math.max(1, l.length), 1);
    const chunk = Math.max(1, Math.floor(36000 / Math.max(1, cellsPer)));
    const groups = prd === 'Y' ? [] : per.map(p => [p]);
    if (prd === 'Y') for (let i = 0; i < per.length; i += chunk) groups.push(per.slice(i, i + chunk));
    for (const g of groups) {
      const q = new URLSearchParams({ method: 'getList', apiKey: key, itmId: itm.join('+') + '+', format: 'json', jsonVD: 'Y',
        prdSe: prd, startPrdDe: g[0], endPrdDe: g[g.length - 1], orgId: job.orgId, tblId: job.tblId });
      objL.forEach((l, i) => q.set('objL' + (i + 1), l.join('+') + '+'));
      const part = await apiGet('https://kosis.kr/openapi/Param/statisticsParameterData.do?' + q.toString());
      for (const r of part) {
        const o = { PRD_DE: r.PRD_DE, ITM_ID: r.ITM_ID, ITM_NM: r.ITM_NM, UNIT_NM: r.UNIT_NM, DT: r.DT };
        for (let i = 1; i <= 8; i++) if (r['C' + i] !== undefined) { o['C' + i] = r['C' + i]; o['C' + i + '_NM'] = r['C' + i + '_NM'] }
        rows.push(o);
      }
      await sleep(1200);
    }
    st.meta[job.key] = { route: 'openapi', orgId: job.orgId, tblId: job.tblId, prd, from: job.from, to: job.to, rows: rows.length,
      classes: M.classes.map(c => c.id + ':' + c.name), at: new Date().toISOString() };
    return rows;
  }

  /* ---------- 2) 화면 다운로드 ---------- */
  async function openTable(orgId, tblId) {
    const old = document.getElementById('kc_frame'); if (old) old.remove();
    const f = document.createElement('iframe'); f.id = 'kc_frame';
    f.style.cssText = 'width:1400px;height:900px;position:absolute;left:-6000px;top:0';
    document.body.appendChild(f);
    f.src = `/statHtml/statHtml.do?orgId=${orgId}&tblId=${tblId}&conn_path=I2`;
    const t0 = Date.now();
    while (Date.now() - t0 < 60000) {
      await sleep(800);
      try {
        if (BLOCK.test(f.contentWindow.document.body.innerText || '')) { st.blocked = true; throw new Error('KOSIS 접근 차단 응답') }
        const r = f.contentWindow.document.getElementById('iframe_rightMenu');
        const c = r && r.contentWindow.document.getElementById('iframe_centerMenu1');
        const W = c && c.contentWindow;
        const fm = W && W.document.forms.ParamInfo;
        if (fm && fm.fieldList && fm.fieldList.value && W.$ && W.$.ui && W.$.ui.fancytree && W.document.getElementById('fancytree_0')) {
          let nCls = 0; try { nCls = JSON.parse(fm.classAllArr.value || '[]').length } catch (e) { }
          const cnt = id => { try { const t = W.$.ui.fancytree.getTree('#' + id); let n = 0; t.visit(() => { n++ }); return n } catch (e) { return 0 } };
          let ok = cnt('fancytree_0') > 0;
          for (let i = 1; i <= nCls; i++) ok = ok && cnt('fancytree_' + i) > 0;
          if (ok) { await sleep(500); return W }
        }
      } catch (e) { if (st.blocked) throw e }
    }
    throw new Error('통계표 화면을 열지 못했습니다: ' + orgId + '/' + tblId);
  }
  function trees(W) {
    const $ = W.$, out = { items: [], classes: [], name: W.document.forms.ParamInfo.tblNm.value };
    W.document.querySelectorAll('[id^=fancytree_]').forEach(el => {
      let t; try { t = $.ui.fancytree.getTree('#' + el.id) } catch (e) { return }
      if (!t) return;
      const nodes = []; t.visit(nd => { nodes.push({ code: nd.data.itmId, name: nd.title, lvl: nd.data.lvl || nd.getLevel(), up: nd.data.upItmId || '', ov: nd.data.objVarId }) });
      if (el.id === 'fancytree_0') out.items = nodes; else out.classes.push({ id: nodes[0] && nodes[0].ov, nodes });
    });
    out.periods = (W.document.forms.ParamInfo.periodStr.value || '').split('#').filter(Boolean);
    return out;
  }
  async function info(orgId, tblId) {
    const W = await openTable(orgId, tblId); const t = trees(W);
    return { name: t.name, periods: t.periods, items: t.items.map(n => n.code + ':' + n.name),
      classes: t.classes.map(c => ({ id: c.id, n: c.nodes.length, levels: [...new Set(c.nodes.map(n => n.lvl))], lvl1: c.nodes.filter(n => n.lvl == 1).slice(0, 40).map(n => n.code + ':' + n.name) })) };
  }
  function parseCsv(t) {
    const rows = []; let row = [], cur = '', q = false;
    for (let i = 0; i < t.length; i++) {
      const ch = t[i];
      if (q) { if (ch === '"') { if (t[i + 1] === '"') { cur += '"'; i++ } else q = false } else cur += ch }
      else if (ch === '"') q = true; else if (ch === ',') { row.push(cur); cur = '' }
      else if (ch === '\n') { row.push(cur); rows.push(row); row = []; cur = '' } else if (ch !== '\r') cur += ch;
    }
    if (cur || row.length) { row.push(cur); rows.push(row) }
    return rows;
  }
  async function uiJob(job) {
    const W = await openTable(job.orgId, job.tblId); const t = trees(W);
    const prd = job.prd || (t.periods.includes('Y') ? 'Y' : t.periods[0]);
    const fl = [{ targetId: 'PRD', targetValue: '', prdValue: prd + ',' + periods(job, prd).join(',') + ',@' }];
    (job.items || t.items.map(n => n.code)).forEach(c => fl.push({ targetId: 'ITM_ID', targetValue: c, prdValue: '' }));
    t.classes.forEach((c, i) => pick(c.nodes, c.id, job).forEach(n => fl.push({ targetId: `OV_L${i + 1}_ID`, targetValue: n.code, prdValue: '' })));
    const f = W.document.forms.ParamInfo, fd = new URLSearchParams(new W.FormData(f));
    const set = (k, v) => { fd.delete(k); fd.set(k, v) };
    set('fieldList', JSON.stringify(fl)); set('view', 'csv'); set('viewSubKind', '2_3'); set('viewKind', '2');
    set('downGridFileType', 'csv'); set('downGridCsvType', 'ANSI'); set('smblYn', 'Y'); set('expDash', 'Y'); set('dataOpt', 'ko');
    // 화면에 설정된 축 배치(rowAxis·colAxis)는 그대로 둠 — 바꾸면 서버가 거절함. 배치는 아래에서 머리글로 판별.
    const r = await fetch('/statHtml/downGrid.do', { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'X-Requested-With': 'XMLHttpRequest' }, body: fd.toString() });
    const txt0 = await r.text();
    if (BLOCK.test(txt0)) { st.blocked = true; throw new Error('KOSIS 접근 차단 응답') }
    let j = {}; try { j = JSON.parse(txt0) } catch (e) { }
    if (!j.file) throw new Error('downGrid: ' + txt0.slice(0, 160));
    fd.set('file', j.file);
    const r2 = await fetch('/statHtml/downNormal.do', { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: fd.toString() });
    const csv = new TextDecoder('euc-kr').decode(await r2.arrayBuffer());
    const recs = csvToRecs(csv, f.rowAxis.value, f.colAxis.value, t);
    st.meta[job.key] = { route: 'screen', name: t.name, orgId: job.orgId, tblId: job.tblId, prd, from: job.from, to: job.to, rows: recs.length,
      rowAxis: f.rowAxis.value, colAxis: f.colAxis.value, classes: t.classes.map(c => c.id), at: new Date().toISOString() };
    return recs;
  }
  // 화면 CSV(행 머리글 여러 줄) → 긴 형식. 축: rowAxis/colAxis 에 TIME, ITEM, 분류ID 가 섞여 있음
  function csvToRecs(csv, rowAxis, colAxis, t) {
    const R = parseCsv(csv).filter(r => r.length > 1);
    const ra = rowAxis.split(',').filter(Boolean), ca = colAxis.split(',').filter(Boolean);
    const nl = ra.length;
    const hdr = R.slice(0, ca.length), body = R.slice(ca.length);
    const clsIdx = id => t.classes.findIndex(c => c.id === id);
    const out = [];
    for (const row of body) {
      const base = {};
      ra.forEach((ax, i) => assign(base, ax, row[i], clsIdx));
      for (let j = nl; j < row.length; j++) {
        const v = row[j]; if (v === undefined || v === '') continue;
        const o = { ...base };
        ca.forEach((ax, k) => assign(o, ax, (hdr[k] || [])[j], clsIdx));
        o.DT = v.replace(/,/g, ''); out.push(o);
      }
    }
    return out;
    function assign(o, ax, val, ci) {
      val = (val || '').trim();
      if (ax === 'TIME') o.PRD_DE = val.replace(/[^0-9]/g, '');
      else if (ax === 'ITEM') { const m = val.match(/^(.*?)\s*\(([^()]*)\)\s*$/); o.ITM_NM = m ? m[1] : val; if (m) o.UNIT_NM = m[2] }
      else { const i = ci(ax); o['C' + (i + 1) + '_NM'] = val }
    }
  }

  /* ---------- 실행 ---------- */
  async function run(jobs, opt = {}) {
    if (st.running) return '이미 실행 중';
    st.running = true; st.total = jobs.length; st.done = 0; st.err = {}; st.blocked = false;
    const gap = opt.apiKey ? 1500 : (opt.gapMs || 60000);
    (async () => {
      for (const j of jobs) {
        if (st.blocked) { st.err[j.key] = '건너뜀 — KOSIS 차단 응답 뒤 중지'; st.done++; continue }
        st.current = j.key;
        try { st.out[j.key] = JSON.stringify(opt.apiKey ? await apiJob(j, opt.apiKey) : await uiJob(j)); delete st.err[j.key] }
        catch (e) { st.err[j.key] = String(e).slice(0, 300) }
        st.done++;
        if (st.done < jobs.length && !st.blocked) await sleep(gap);
      }
      st.running = false; st.current = '';
    })();
    return 'started ' + jobs.length + (opt.apiKey ? ' (OpenAPI)' : ` (화면, 간격 ${gap / 1000}초)`);
  }
  const status = () => ({ running: st.running, blocked: st.blocked, done: st.done, total: st.total, current: st.current, errors: st.err,
    have: Object.fromEntries(Object.entries(st.out).map(([k, v]) => [k, v.length])) });
  const dump = keys => { const o = {}; (keys || Object.keys(st.out)).forEach(k => { o[k] = { meta: st.meta[k], recs: JSON.parse(st.out[k]) } });
    const s = JSON.stringify(o); return '<<KC>>' + s + '<<KC>>' + ' '.repeat(Math.max(0, 120000 - s.length)) };
  const stop = () => { st.blocked = true; return '다음 작업부터 멈춤' };

  window.KC = { run, status, dump, stop, info, apiMeta, apiJob, uiJob, csvToRecs };
  return 'KC ready';
})();
