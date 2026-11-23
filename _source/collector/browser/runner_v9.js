// TAAS runner v9 — 직접 조회 방식 (runner_inject.js 주입 뒤에 주입)
// 장표마다 한 번만 화면을 띄워 조회 파라미터(:row_list/:col_list/:mea_list …)를 얻고,
// 꺼진 항목 표시(*)를 지워 "모두 켠" 상태로 OctagonProxyServlet 에 직접 요청한다.
// 구간(연도)은 vcondition 만 바꿔 요청, 페이지는 :pagenum 으로 넘김. 화면 렌더링/클릭 대기 없음.
// 실패하거나 검증이 맞지 않으면 그 작업만 v8(클릭 방식)으로 받는다.
(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const gd = () => document.getElementById('xf')?.contentDocument;
  const TRANS = /cube가 존재하지|Exception|Connection reset|timed out|timeout|DB오류|DB접속/i;

  // HTML 조각 → 칸 행렬 (숨김 칸 제외, rowspan/colspan 펼침)
  const tx = td => { const c = td.cloneNode(true); c.querySelectorAll('br').forEach(b => b.replaceWith('\n'));
    return c.textContent.replace(/[ \t\r ]+/g, ' ').replace(/ *\n */g, '\n').trim(); };
  const tableOf = html => { const h = document.createElement('div'); h.innerHTML = html || ''; return h.querySelector('table'); };
  const expand = html => { const M = []; const t = tableOf(html); if (!t) return M;
    [...t.rows].forEach((tr, ri) => { M[ri] = M[ri] || []; let ci = 0;
      [...tr.cells].forEach(td => { if ((td.getAttribute('style') || '').replace(/\s/g, '').includes('display:none')) return;
        while (M[ri][ci] !== undefined) ci++; const rs = +td.getAttribute('rowspan') || 1, cs = +td.getAttribute('colspan') || 1, v = tx(td);
        for (let a = 0; a < rs; a++) { M[ri + a] = M[ri + a] || []; for (let b = 0; b < cs; b++) M[ri + a][ci + b] = v; } ci += cs; }); });
    return M; };
  const parseX = x => { const g = n => x.querySelector(n)?.textContent || '';
    const lab = expand(g('LABELSESSION'))[0] || []; const R = expand(g('ROWSESSION')), C = expand(g('COLSESSION'));
    const t = tableOf(g('DATASESSION')); const D = t ? [...t.rows].map(r => [...r.cells].map(tx)) : [];
    const nc = Math.max(0, ...C.map(r => r.length)), cols = []; for (let j = 0; j < nc; j++) cols.push(C.map(r => r[j]));
    const rt = tableOf(g('ROWSESSION')); const meaT = rt ? [...rt.querySelectorAll('td.rowMeaTitle')].map(tx) : [];
    const ct = tableOf(g('COLSESSION')); const meaC = ct ? [...ct.querySelectorAll('td.colMeaTitle,td[type="16"]')].map(tx) : [];
    return { lab, rows: R, cols, data: D, meaT: [...meaT, ...meaC] }; };
  const mergePage = (p, q) => { const key = c => c.join('\u0001');
    if (q.cols.length === p.cols.length && q.cols.every((c, i) => key(c) === key(p.cols[i]))) { p.rows.push(...q.rows); p.data.push(...q.data); return p; }
    const idx = new Map(p.cols.map((c, i) => [key(c), i]));
    for (const c of q.cols) if (!idx.has(key(c))) { idx.set(key(c), p.cols.length); p.cols.push(c); p.data.forEach(r => r.push('')); }
    const n = p.cols.length, pos = q.cols.map(c => idx.get(key(c)));
    q.rows.forEach((r, i) => { const row = new Array(n).fill(''); q.data[i].forEach((v, j) => { row[pos[j]] = v; }); p.rows.push(r); p.data.push(row); });
    p.colRealigned = (p.colRealigned || 0) + 1; return p; };

  let trid = 90000;
  const post = async (params, sid) => {
    const body = 'params=' + encodeURIComponent(params) + '&lic&info=10001&odfname=&cubeinfo=&trid=' + (++trid) + '&subjectId=' + sid;
    const ctl = new AbortController(); const to = setTimeout(() => ctl.abort(), 180000);
    try { const r = await fetch('/OBIP25/servlet/OctagonProxyServlet', { method: 'POST', signal: ctl.signal,
        headers: { 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'X-Requested-With': 'XMLHttpRequest' }, body });
      const t = await r.text(); return new DOMParser().parseFromString(t, 'text/xml');
    } finally { clearTimeout(to); } };

  // 장표 틀: 한 번 화면에 띄워 조회 파라미터와 주석을 얻음
  window.__tpl = window.__tpl || {};
  const getTpl = async (pid, vcs) => {
    if (__tpl[pid]) return __tpl[pid];
    for (const vc of vcs) {
      await __load(pid, vc); await __waitStable(gd, 60000);
      const d = gd(); const ov = d?.defaultView?.viewer?.getViewer?.(); const pre = ov?.preParamTmp;
      if (!pre || !/:mea_list=/.test(pre)) continue;
      const notes = (d.body.innerText.match(/주\)[^\n]*/g) || []);
      const colDims = [...d.querySelectorAll('[id^=colDrop_] .ovTagText')].map(e => e.innerText.trim());
      const meaIds = (pre.match(/:mea_list="([^"]*)"/) || [, ''])[1].split(':').filter(Boolean);
      const sid = (pre.match(/:subject_id="(\d+)"/) || [])[1] || ov.config?.subjectId;
      return (__tpl[pid] = { pre: pre.replace(/\*/g, ''), notes, colDims, nMea: meaIds.length, sid });
    }
    return null; };

  const setRange = (pre, vc) => { // vc: "D1443=202501~202512;" → vcondition 안 같은 차원의 [from] [to] 교체
    const m = /^D(\d+)=(\d+)~(\d+);$/.exec(vc || ''); if (!m) return vc ? null : pre;
    const re = new RegExp(`(D${m[1]}@\\|@[^#"]*#OTE!\\[)[^\\]]*(\\]!# #OTE!\\[)[^\\]]*(\\]!#)`);
    if (!re.test(pre)) return null; return pre.replace(re, `$1${m[2]}$2${m[3]}$3`); };

  // 한 구간 직접 수집
  const fetchDirect = async (pid, vc, vcs) => {
    const t0 = Date.now(); const T = await getTpl(pid, vcs); if (!T) return { err: 'v9-no-template' };
    const base = setRange(T.pre, vc); if (!base) return { err: 'v9-no-vcondition' };
    const pg = n => base.replace(/:pagenum="\d+"/, `:pagenum="${n}"`);
    let x = await post(pg(1), T.sid); const msg = (x.querySelector('MESSAGE')?.textContent || '').trim();
    const tp = +(x.querySelector('TOTALPAGE')?.textContent || 0);
    if (!tp) { if (TRANS.test(msg) || !msg) return { err: 'transient: ' + msg.slice(0, 80) };
      return { lab: [], colDims: [], rows: [], cols: [], data: [], pages: 0, ms: Date.now() - t0, nodata: true, msg: ['서버 응답: ' + msg.slice(0, 120)],
        meaAll: T.nMea, meaOn: 0, meaMissing: [], dimAll: true, dimsEnabled: [], dimMissing: [] }; }
    const P = parseX(x); const meaSeen = new Set(P.meaT);
    for (let n = 2; n <= tp; n++) { let q = null;
      for (let a = 0; a < 3 && !q; a++) { const y = await post(pg(n), T.sid);
        if (+(y.querySelector('CURRENTPAGE')?.textContent || 0) === n) q = parseX(y); else await sleep(2000); }
      if (!q) return { err: 'v9-page ' + n };
      q.meaT.forEach(m => meaSeen.add(m)); mergePage(P, q); }
    if (new Set(P.rows.map(r => r.length)).size > 1) return { err: 'v9-inconsistent-rows' };
    if (meaSeen.size > 0 && meaSeen.size !== T.nMea) return { err: `v9-mea ${meaSeen.size}/${T.nMea}` };
    const rc = +(x.querySelector('ROWCOUNT')?.textContent || 0);
    return { lab: P.lab, colDims: T.colDims, rows: P.rows, cols: P.cols, data: P.data, pages: tp, ms: Date.now() - t0, nodata: false,
      msg: [...T.notes], meaAll: T.nMea, meaOn: T.nMea, meaMissing: [], dimAll: true, dimsEnabled: [], dimMissing: [], rowcount: rc,
      colRealigned: P.colRealigned || 0 }; };
  window.__fetchDirect = fetchDirect;

  // 실행기 v9
  window.__startRunnerV9 = () => {
    window.__gen = (window.__gen || 0) + 1; const G = window.__gen;
    const S = window.__state = { phase: 'run-v9', errors: [], fetched: 0, direct: 0, fallback: 0, gen: G, started: Date.now(), running: true };
    (async () => {
      const byPid = {}; for (const j of __jobs) (byPid[j.pid] = byPid[j.pid] || []).push(j);
      for (let pass = 1; pass <= 4; pass++) { if (G !== window.__gen) return;
        const have = new Set((await __all('rec')).filter(r => r.v8 || (r.nodata && !r.dimAll && /SQL오류/.test((r.msg || []).join(' ')))).map(r => r.key));
        const miss = __jobs.filter(j => !have.has(j.pid + '|' + j.label)); S.pass = pass; S.missing = miss.length; if (!miss.length) break;
        for (const j of miss) { if (G !== window.__gen) return;
          const key = j.pid + '|' + j.label; S.current = key; S.curSince = Date.now(); let r = null, how = 'direct';
          const vcs = [j.vc, ...byPid[j.pid].map(x => x.vc).reverse()];
          for (let a = 0; a < 3; a++) { while (!navigator.onLine) await sleep(10000);
            try { r = await fetchDirect(j.pid, j.vc, vcs); } catch (e) { r = { err: 'v9 ' + String(e).slice(0, 80) }; }
            if (G !== window.__gen) return; if (!r.err || !/^transient/.test(r.err)) break; await sleep(5000 * (a + 1)); }
          if (r.err) { S.errors.push({ key, err: r.err, pass, stage: 'direct' }); how = 'v8';
            r = await Promise.race([__fetchTable(j.pid, j.vc), sleep(600000).then(() => ({ err: 'job-timeout' }))]);
            if (G !== window.__gen) return; }
          if (r.err) S.errors.push({ key, err: r.err, pass, stage: how });
          else { await __put('rec', { key, pid: j.pid, label: j.label, vc: j.vc, lab: r.lab, colDims: r.colDims, rows: r.rows, cols: r.cols, data: r.data, msg: r.msg,
              pages: r.pages, ms: r.ms, nodata: !!r.nodata, meaAll: r.meaAll ?? 0, meaOn: r.meaOn ?? 0, meaMissing: r.meaMissing || [], v8: true, v9: how === 'direct',
              dimAll: !!r.dimAll, dimsEnabled: r.dimsEnabled || [], dimMissing: r.dimMissing || [], ts: Date.now() });
            how === 'direct' ? S.direct++ : S.fallback++; }
          S.fetched++; await sleep(300); }
      }
      if (G === window.__gen) { S.running = false; S.allDone = Date.now(); }
    })(); return G; };
  return 'v9 ready';
})();
