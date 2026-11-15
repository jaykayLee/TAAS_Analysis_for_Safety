// 데스크톱 앱 브라우저용 본 수집 실행기 (IndexedDB 'taaslib' 이어받기). 페이지를 새로 연 뒤 통째로 주입.
(async () => {
  // 1) 숨김 상태에서도 느려지지 않는 워커 타이머
  if (!window.__wt) {
    const src = `const T=new Map();onmessage=e=>{const d=e.data;if(d.c==='set'){T.set(d.id,setTimeout(()=>{T.delete(d.id);postMessage(d.id)},d.ms))}else if(d.c==='clr'){clearTimeout(T.get(d.id));T.delete(d.id)}}`;
    const w = new Worker(URL.createObjectURL(new Blob([src], { type: 'text/javascript' })));
    const cbs = new Map(); let seq = 1e6;
    w.onmessage = e => { const f = cbs.get(e.data); cbs.delete(e.data); if (f) try { f(); } catch (err) { console.error(err); } };
    const nST = window.setTimeout.bind(window), nCT = window.clearTimeout.bind(window);
    window.setTimeout = (fn, ms = 0, ...a) => { if (typeof fn !== 'function') return nST(fn, ms, ...a); const id = ++seq; cbs.set(id, () => fn(...a)); w.postMessage({ c: 'set', id, ms: Math.max(0, +ms || 0) }); return id; };
    window.clearTimeout = id => { if (cbs.has(id)) { cbs.delete(id); w.postMessage({ c: 'clr', id }); } else nCT(id); };
    window.__wt = w;
  }
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const EMPTYMSG = /조회된 데이터가 없습니다|데이터가 없습니다|SQL오류|오류가 발생/;

  // 2) 장표 불러오기·읽기
  window.__load = (pid, vc) => new Promise(res => {
    let f = document.getElementById('xf'); if (f) f.remove();
    f = document.createElement('iframe'); f.id = 'xf'; f.name = 'xf'; f.style.cssText = 'width:1400px;height:900px;position:absolute;left:-5000px'; document.body.appendChild(f);
    const fm = document.createElement('form'); fm.method = 'post'; fm.action = '/OBIP25/analysis/TypicalAnalysis.jsp'; fm.target = 'xf';
    for (const [k, v] of Object.entries({ uid: 'taas_viewer', pid, vCondition: vc })) { const i = document.createElement('input'); i.type = 'hidden'; i.name = k; i.value = v; fm.appendChild(i); }
    document.body.appendChild(fm); f.onload = () => res(true); fm.submit(); fm.remove();
  });
  const gd = () => document.getElementById('xf').contentDocument;
  window.__expand = tbl => { const M = []; if (!tbl) return M; const w = tbl.ownerDocument.defaultView;
    [...tbl.rows].forEach((tr, ri) => { M[ri] = M[ri] || []; let ci = 0; [...tr.cells].forEach(td => { if (w.getComputedStyle(td).display === 'none') return; while (M[ri][ci] !== undefined) ci++;
      const rs = +td.getAttribute('rowspan') || 1, cs = +td.getAttribute('colspan') || 1, tx = td.innerText.trim();
      for (let a = 0; a < rs; a++) { M[ri + a] = M[ri + a] || []; for (let b = 0; b < cs; b++) M[ri + a][ci + b] = tx; } ci += cs; }); }); return M; };
  window.__parse = doc => { const lab = [...(doc.getElementById('labelSession')?.rows[0]?.cells || [])].map(c => c.innerText.trim());
    const R = __expand(doc.getElementById('rowSession')), C = __expand(doc.getElementById('colSession'));
    const D = [...doc.getElementById('dataSession').rows].map(r => [...r.cells].map(c => c.innerText.trim()));
    const nc = Math.max(0, ...C.map(r => r.length)), cols = []; for (let j = 0; j < nc; j++) cols.push(C.map(r => r[j]));
    const colDims = [...doc.querySelectorAll('[id^=colDrop_] .ovTagText')].map(e => e.innerText.trim()); return { lab, colDims, rows: R, cols, data: D }; };
  window.__sig = doc => { if (!doc || !doc.body) return null; if (EMPTYMSG.test(doc.body.innerText.slice(0, 400))) return 'NODATA';
    const d = doc.getElementById('dataSession'); if (!d) return null;
    if ([...doc.querySelectorAll('img[src*=loading],img[src*=progress]')].some(i => i.offsetParent !== null)) return null;
    if (d.rows.length === 0) return 'EMPTY';
    return d.rows.length + ':' + (d.rows[0]?.cells.length || 0) + ':' + (doc.getElementById('rowSession')?.rows.length || 0) + ':' + d.innerText.length; };
  window.__waitStable = async (g, maxMs = 90000) => { const t0 = Date.now(); let last = null, same = 0;
    while (Date.now() - t0 < maxMs) { await sleep(500); const s = __sig(g()); if (s && s === last) { if (++same >= 3) return s; } else { same = 0; last = s; } } return null; };
  const nod = why => { const d = gd(); return { lab: [], colDims: [], rows: [], cols: [], data: [], pages: 0, ms: 0, nodata: true, msg: [why + ': ' + (d?.body?.innerText.split('\n').slice(0, 2).join(' ') || '')] }; };
  const meaShown = () => { const rs = gd().getElementById('rowSession'); if (!rs) return -1; return new Set([...rs.querySelectorAll('td.rowMeaTitle')].map(t => t.innerText.trim())).size; };
  // 꺼진 항목 켜기 — TAAS는 클릭마다 재조회하므로 하나씩 누르고 매번 끝까지 기다림
  const DIMSEL = '[id^=rowDrop_] input[type=checkbox],[id^=colDrop_] input[type=checkbox]';
  const MEASEL = '[id^=meaDrop_] input[type=checkbox]';
  const ALLSEL = DIMSEL + ',' + MEASEL;
  async function settle() { // 재조회 완료 대기. 빈 화면/오류는 5초 더 지켜보고 확정
    let s = await __waitStable(gd, 120000); if (!s) return null;
    if (s === 'NODATA' || s === 'EMPTY') { await sleep(5000); const s2 = await __waitStable(gd, 30000); if (s2 && s2 !== 'NODATA' && s2 !== 'EMPTY') return s2; return s2 || s; }
    return s;
  }
  async function clickOne(id) {
    const c = gd().getElementById(id); if (!c || c.checked) return 'skip';
    const before = __sig(gd()); c.click();
    let t = Date.now(); while (Date.now() - t < 120000) { await sleep(400); const g = __sig(gd()); if (g === 'NODATA' || g === 'EMPTY' || (g && g !== before)) break; }
    return await settle();
  }
  const msgOf = () => (gd()?.body?.innerText || '').split('\n').slice(0, 2).join(' ');
  // 페이지마다 열 구성이 다르면(값 없는 열 숨김 등) 열 머리글 기준으로 맞춰 합침
  const mergePage = (p, q) => { const key = c => c.join('\u0001');
    if (q.cols.length === p.cols.length && q.cols.every((c, i) => key(c) === key(p.cols[i]))) { p.rows.push(...q.rows); p.data.push(...q.data); return p; }
    const idx = new Map(p.cols.map((c, i) => [key(c), i]));
    for (const c of q.cols) if (!idx.has(key(c))) { idx.set(key(c), p.cols.length); p.cols.push(c); p.data.forEach(r => r.push('')); }
    const n = p.cols.length, pos = q.cols.map(c => idx.get(key(c)));
    q.rows.forEach((r, i) => { const row = new Array(n).fill(''); q.data[i].forEach((v, j) => { row[pos[j]] = v; }); p.rows.push(r); p.data.push(row); });
    p.colRealigned = (p.colRealigned || 0) + 1; return p; };
  async function fetchOnce(pid, vc) {
    const t0 = Date.now(); await __load(pid, vc);
    let s = await settle();
    if (!s) { const d = gd(); if (d && d.getElementById('rowDrop_1') && !d.getElementById('dataSession')) return nod('빈 화면'); return { err: 'timeout-load' }; }
    if (s === 'NODATA') return nod('서버 응답'); if (s === 'EMPTY') return nod('빈 표');
    const ids = [...gd().querySelectorAll(ALLSEL)].map(c => c.id);
    const meaIds = new Set([...gd().querySelectorAll(MEASEL)].map(c => c.id));
    const failed = new Set();
    for (let round = 0; round < 6; round++) {
      let bad = null;
      for (const id of ids) {
        if (failed.has(id)) continue;
        const r = await clickOne(id); if (r === 'skip') continue;
        if (!r) return { err: 'rerender-timeout ' + id };
        if (r === 'NODATA' || r === 'EMPTY') { const m = msgOf(); if (/cube가 존재하지|Exception|Connection reset|timed out|timeout/i.test(m)) return { err: 'transient: ' + m.slice(0, 80) }; bad = id; break; }
      }
      if (!bad) break;
      failed.add(bad); // 이 항목만 빼고 처음부터 다시
      await __load(pid, vc); s = await settle(); if (!s || s === 'NODATA' || s === 'EMPTY') return { err: 'reload' };
    }
    // 저장 전 확인: 실패로 뺀 것 외에는 모두 켜졌고, 화면의 수치항목 수가 켠 개수와 같아야 함
    const offNow = [...gd().querySelectorAll(ALLSEL)].filter(c => !c.checked).map(c => c.id);
    if (offNow.some(id => !failed.has(id))) return { err: 'not-all-on ' + offNow.join(',') };
    const meaOnN = [...gd().querySelectorAll(MEASEL)].filter(c => c.checked).length;
    const shown = meaShown(); if (shown > 0 && shown !== meaOnN) return { err: `mea-shown ${shown}/${meaOnN}` };
    const p = __parse(gd());
    const span = gd().querySelector('[id^=pageDIV_] span'); const nPages = span ? +((span.innerText.match(/\d+/) || [1])[0]) : 1;
    for (let pg = 2; pg <= nPages; pg++) {
      const before = __sig(gd()); gd().querySelector('[id^=pageDIV_] img[alt="Next Page"]').click();
      let t = Date.now(); while (Date.now() - t < 30000) { await sleep(400); const g = __sig(gd()); if (g && g !== before) break; }
      s = await __waitStable(gd); if (!s || s === 'NODATA' || s === 'EMPTY') return { err: 'timeout-page' + pg };
      if (+gd().querySelector('[id^=pageDIV_] input').value !== pg) return { err: 'page-mismatch' };
      mergePage(p, __parse(gd()));
    }
    if (new Set(p.rows.map(x => x.length)).size > 1) return { err: 'inconsistent-rows' };
    const nm = id => id.replace('chkBox_', '');
    const meaOff = [...failed].filter(id => meaIds.has(id)).map(nm), dimOff = [...failed].filter(id => !meaIds.has(id)).map(nm);
    p.pages = nPages; p.ms = Date.now() - t0; p.meaAll = meaIds.size; p.meaOn = meaOnN; p.meaMissing = meaOff;
    p.dimAll = true; p.dimsEnabled = []; p.dimMissing = dimOff;
    p.msg = (gd().body.innerText.match(/주\)[^\n]*/g) || []);
    if (meaOff.length) p.msg.push('서버 오류로 다음 수치항목 제외: ' + meaOff.join(', '));
    if (dimOff.length) p.msg.push('서버 오류로 다음 축을 켜지 못함: ' + dimOff.join(', '));
    return p;
  }
  window.__lock = Promise.resolve();
  const TRANSIENT = /cube가 존재하지|Exception|Connection reset|timed out|timeout/i;
  window.__fetchTable = (pid, vc) => { const run = window.__lock.then(() => fetchOnce(pid, vc)).catch(e => ({ err: String(e) }))
      .then(r => (r && r.nodata && TRANSIENT.test((r.msg || []).join(' '))) ? { err: 'transient: ' + (r.msg || [''])[0].slice(0, 80) } : r);
    window.__lock = run.then(() => {}, () => {}); return run; };

  // 3) 저장소
  window.__db = await new Promise((res, rej) => { const q = indexedDB.open('taaslib', 1);
    q.onupgradeneeded = () => { const d = q.result; d.createObjectStore('rec', { keyPath: 'key' }); d.createObjectStore('meta', { keyPath: 'pid' }); };
    q.onsuccess = () => res(q.result); q.onerror = () => rej(q.error); });
  window.__put = (s, o) => new Promise((res, rej) => { const t = __db.transaction(s, 'readwrite'); t.objectStore(s).put(o); t.oncomplete = res; t.onerror = () => rej(t.error); });
  window.__keys = s => new Promise(res => { const q = __db.transaction(s).objectStore(s).getAllKeys(); q.onsuccess = () => res(q.result); });
  window.__all = s => new Promise(res => { const q = __db.transaction(s).objectStore(s).getAll(); q.onsuccess = () => res(q.result); });
  window.__export = async (filterFn, filename, dryRun) => { const recs = (await __all('rec')).filter(filterFn); const meta = await __all('meta');
    const json = JSON.stringify({ exported: new Date().toISOString(), meta, recs });
    const blob = await new Response(new Blob([json]).stream().pipeThrough(new CompressionStream('gzip'))).blob();
    if (!dryRun) { const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = filename; document.body.appendChild(a); a.click(); a.remove(); }
    return { recs: recs.length, rawMB: (json.length / 1e6).toFixed(1), gzMB: (blob.size / 1e6).toFixed(2) }; };

  // 4) 작업 목록 (2025 우선)
  const metas = await __all('meta'); const jobs = [];
  for (const x of metas) { const di = x.dateInfo; if (!di) { jobs.push({ pid: x.pid, vc: '', label: 'all' }); continue; }
    const L = di.minYear.length, y0 = Math.max(2005, +di.minYear.slice(0, 4)), y1 = +di.maxYear.slice(0, 4), start = Math.min(y0, y1), span = /일별/.test(x.name) ? 1 : 5;
    for (let a = start; a <= y1; a += span) { const b = Math.min(a + span - 1, y1);
      const vc = L === 4 ? `D${di.dimAttrId}=${a}~${b};` : L === 6 ? `D${di.dimAttrId}=${a}01~${b}12;` : `D${di.dimAttrId}=${a}0101~${b}1231;`;
      jobs.push({ pid: x.pid, vc, label: `${a}-${b}` }); } }
  jobs.sort((a, b) => (b.label.endsWith('2025') ? 1 : 0) - (a.label.endsWith('2025') ? 1 : 0) || (+a.pid - +b.pid));
  window.__jobs = jobs;

  // 5) 실행기
  window.__startRunner = () => {
    window.__gen = (window.__gen || 0) + 1; const G = window.__gen;
    window.__state = { phase: 'run', errors: [], fetched: 0, gen: G, started: Date.now(), running: true };
    (async () => {
      for (let pass = 1; pass <= 4; pass++) { if (G !== window.__gen) return;
        const have = new Set((await __all('rec')).filter(r => r.v8 || (r.nodata && !r.dimAll && /SQL오류/.test((r.msg||[]).join(' ')))).map(r => r.key)); const miss = jobs.filter(j => !have.has(j.pid + '|' + j.label));
        __state.pass = pass; __state.missing = miss.length; if (!miss.length) break;
        for (const j of miss) { if (G !== window.__gen) return; const key = j.pid + '|' + j.label; __state.current = key; __state.curSince = Date.now(); let r = null;
          for (let a = 0; a < 2; a++) { while (!navigator.onLine) await sleep(10000);
            r = await Promise.race([__fetchTable(j.pid, j.vc), sleep(600000).then(() => ({ err: 'job-timeout' }))]);
            if (G !== window.__gen) return; if (!r.err) break; await sleep(4000); }
          if (r.err) __state.errors.push({ key, err: r.err, pass });
          else await __put('rec', { key, pid: j.pid, label: j.label, vc: j.vc, lab: r.lab, colDims: r.colDims, rows: r.rows, cols: r.cols, data: r.data, msg: r.msg,
            pages: r.pages, ms: r.ms, nodata: !!r.nodata, meaAll: r.meaAll ?? 0, meaOn: r.meaOn ?? 0, meaMissing: r.meaMissing || [], v8: true, dimAll: !!r.dimAll, dimsEnabled: r.dimsEnabled || [], dimMissing: r.dimMissing || [], ts: Date.now() });
          __state.fetched++; await sleep(600); }
      }
      if (G === window.__gen) { __state.running = false; __state.allDone = Date.now(); }
    })(); return G; };
  if (window.__noAutoStart) return 'runner v8 loaded (not started)';
  __startRunner();
  return 'runner v8 started';
})();
