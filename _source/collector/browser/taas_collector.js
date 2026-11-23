/*
 * TAAS 교통사고 상세통계 수집기
 *
 * 사용법
 *  1. 크롬에서 https://taas.koroad.or.kr/sta/acs/exs/typical.do?menuId=WEB_KMP_OVT_UAS_ASA 를 엽니다.
 *  2. F12 → Console 탭. (처음이면 크롬이 붙여넣기 허용을 물으니 안내대로 "allow pasting" 입력)
 *  3. 이 파일 내용을 통째로 붙여넣고 Enter.
 *  4. TAAS.run({from: 2026, to: 2026})      // 2026년만 수집
 *     TAAS.status()                         // 진행 상황
 *     TAAS.export()                         // taas_raw_2026.json.gz 를 다운로드 폴더에 저장
 *  5. python update_library.py taas_library taas_raw_2026.json.gz
 *
 * - 수치항목 6종(사고·사망·부상·중상·경상·부상신고)을 모두 켜고 받습니다. 서버가 오류를 내면 기본 항목으로 받고 기록합니다.
 * - 200행을 넘는 장표는 모든 페이지를 넘겨 받습니다.
 * - 비회원 조회 제한에 맞춰 5개년(일별 장표는 1년) 단위로 나눠 받습니다.
 * - 받은 결과는 브라우저 저장소(IndexedDB 'taas_collector')에 쌓이므로, 탭을 닫았다가 다시 붙여넣고 run 하면 이어 받습니다.
 * - 주의: 수집 중에는 같은 브라우저에서 TAAS 장표를 따로 조회하지 마세요. TAAS 장표 엔진은 브라우저 세션 하나를 공유해,
 *   동시에 조회하면 수치항목 설정이 서로 간섭합니다. 탭은 다른 창 뒤에 가려져 있어도 됩니다.
 */
(() => {
  if (!location.host.includes('taas.koroad.or.kr') || !window.statsMenuList) {
    console.error('TAAS 교통사고 상세통계 페이지(typical.do)에서 실행하세요.'); return;
  }
  // 크롬은 보이지 않는 탭의 타이머를 1분 단위로 늦추므로(intensive throttling), 대기는 워커 타이머로 처리
  const wsrc = `const T=new Map();onmessage=e=>{const d=e.data;if(d.c==='set'){T.set(d.id,setTimeout(()=>{T.delete(d.id);postMessage(d.id)},d.ms))}}`;
  const worker = new Worker(URL.createObjectURL(new Blob([wsrc], { type: 'text/javascript' })));
  const wcb = new Map(); let wseq = 0; worker.onmessage = e => { const f = wcb.get(e.data); wcb.delete(e.data); if (f) f(); };
  const sleep = ms => new Promise(r => { const id = ++wseq; wcb.set(id, r); worker.postMessage({ c: 'set', id, ms }); });
  const DB = 'taas_collector', FRAME = 'taas_cx';
  const EMPTYMSG = /조회된 데이터가 없습니다|데이터가 없습니다|SQL오류|오류가 발생/;
  // 서버 일시 오류(집계 큐브 갱신 중, 연결 끊김 등)는 '데이터 없음'으로 저장하지 않고 다시 시도
  const TRANSIENT = /cube가 존재하지|Exception|Connection reset|timed out|timeout/i;
  const st = { running: false, stop: false, done: 0, total: 0, errors: [], current: null };

  /* ---------- 저장소 ---------- */
  let db;
  const openDB = () => new Promise((res, rej) => { const q = indexedDB.open(DB, 1);
    q.onupgradeneeded = () => { const d = q.result; d.createObjectStore('rec', { keyPath: 'key' }); d.createObjectStore('meta', { keyPath: 'pid' }); };
    q.onsuccess = () => res(q.result); q.onerror = () => rej(q.error); });
  const put = (s, o) => new Promise((res, rej) => { const t = db.transaction(s, 'readwrite'); t.objectStore(s).put(o); t.oncomplete = res; t.onerror = () => rej(t.error); });
  const all = s => new Promise(res => { const q = db.transaction(s).objectStore(s).getAll(); q.onsuccess = () => res(q.result); });
  const keys = s => new Promise(res => { const q = db.transaction(s).objectStore(s).getAllKeys(); q.onsuccess = () => res(q.result); });

  /* ---------- 장표 불러오기 ---------- */
  const load = (pid, vc) => new Promise(res => {
    let f = document.getElementById(FRAME); if (f) f.remove();
    f = document.createElement('iframe'); f.id = FRAME; f.name = FRAME; f.style.cssText = 'width:1400px;height:900px;position:absolute;left:-5000px';
    document.body.appendChild(f);
    const fm = document.createElement('form'); fm.method = 'post'; fm.action = '/OBIP25/analysis/TypicalAnalysis.jsp'; fm.target = FRAME;
    for (const [k, v] of Object.entries({ uid: 'taas_viewer', pid, vCondition: vc })) { const i = document.createElement('input'); i.type = 'hidden'; i.name = k; i.value = v; fm.appendChild(i); }
    document.body.appendChild(fm); f.onload = () => res(true); fm.submit(); fm.remove();
  });
  const gd = () => document.getElementById(FRAME).contentDocument;
  const expand = tbl => { const M = []; if (!tbl) return M; const w = tbl.ownerDocument.defaultView;
    [...tbl.rows].forEach((tr, ri) => { M[ri] = M[ri] || []; let ci = 0;
      [...tr.cells].forEach(td => { if (w.getComputedStyle(td).display === 'none') return; while (M[ri][ci] !== undefined) ci++;
        const rs = +td.getAttribute('rowspan') || 1, cs = +td.getAttribute('colspan') || 1, tx = td.innerText.trim();
        for (let a = 0; a < rs; a++) { M[ri + a] = M[ri + a] || []; for (let b = 0; b < cs; b++) M[ri + a][ci + b] = tx; } ci += cs; }); });
    return M; };
  const parse = doc => { const lab = [...(doc.getElementById('labelSession')?.rows[0]?.cells || [])].map(c => c.innerText.trim());
    const R = expand(doc.getElementById('rowSession')), C = expand(doc.getElementById('colSession'));
    const D = [...doc.getElementById('dataSession').rows].map(r => [...r.cells].map(c => c.innerText.trim()));
    const nc = Math.max(0, ...C.map(r => r.length)), cols = []; for (let j = 0; j < nc; j++) cols.push(C.map(r => r[j]));
    const colDims = [...doc.querySelectorAll('[id^=colDrop_] .ovTagText')].map(e => e.innerText.trim());
    return { lab, colDims, rows: R, cols, data: D }; };
  const sig = doc => { if (!doc || !doc.body) return null;
    if (EMPTYMSG.test(doc.body.innerText.slice(0, 400))) return 'NODATA';
    const d = doc.getElementById('dataSession'); if (!d) return null;
    if ([...doc.querySelectorAll('img[src*=loading],img[src*=progress]')].some(i => i.offsetParent !== null)) return null;
    if (d.rows.length === 0) return 'EMPTY';
    return d.rows.length + ':' + (d.rows[0]?.cells.length || 0) + ':' + (doc.getElementById('rowSession')?.rows.length || 0) + ':' + d.innerText.length; };
  const waitStable = async (maxMs = 90000) => { const t0 = Date.now(); let last = null, same = 0;
    while (Date.now() - t0 < maxMs) { await sleep(500); const s = sig(gd()); if (s && s === last) { if (++same >= 3) return s; } else { same = 0; last = s; } } return null; };
  const nod = why => ({ lab: [], colDims: [], rows: [], cols: [], data: [], pages: 0, nodata: true,
    msg: [why + ': ' + (gd()?.body?.innerText.split('\n').slice(0, 2).join(' ') || '')] });

  // 페이지마다 열 구성이 다르면(값 없는 열 숨김 등) 열 머리글 기준으로 맞춰 합침
  const mergePage = (p, q) => { const key = c => c.join('\u0001');
    if (q.cols.length === p.cols.length && q.cols.every((c, i) => key(c) === key(p.cols[i]))) { p.rows.push(...q.rows); p.data.push(...q.data); return p; }
    const idx = new Map(p.cols.map((c, i) => [key(c), i]));
    for (const c of q.cols) if (!idx.has(key(c))) { idx.set(key(c), p.cols.length); p.cols.push(c); p.data.forEach(r => r.push('')); }
    const n = p.cols.length, pos = q.cols.map(c => idx.get(key(c)));
    q.rows.forEach((r, i) => { const row = new Array(n).fill(''); q.data[i].forEach((v, j) => { row[pos[j]] = v; }); p.rows.push(r); p.data.push(row); });
    p.colRealigned = (p.colRealigned || 0) + 1; return p; };
  async function fetchTable(pid, vc) {
    const t0 = Date.now(); await load(pid, vc);
    let s = await waitStable(60000);
    if (!s) { const d = gd(); if (d && d.getElementById('rowDrop_1') && !d.getElementById('dataSession')) return nod('빈 화면'); return { err: 'timeout-load' }; }
    if (s === 'NODATA') return nod('서버 응답'); if (s === 'EMPTY') return nod('빈 표');
    const boxes = [...gd().querySelectorAll('[id^=meaDrop_] input[type=checkbox]')];
    const off = boxes.filter(c => !c.checked), offNames = off.map(c => c.id.replace('chkBox_', ''));
    let fallback = false;
    if (off.length) {
      const before = sig(gd()); off.forEach(c => c.click());
      let t = Date.now(), changed = false;
      while (Date.now() - t < 90000) { await sleep(500); const g = sig(gd()); if (g === 'NODATA' || g === 'EMPTY' || (g && g !== before)) { changed = true; break; } }
      if (!changed) return { err: 'mea-no-rerender' };
      s = await waitStable(); if (!s) return { err: 'timeout-mea' };
      if (s === 'NODATA' || s === 'EMPTY') { fallback = true; await load(pid, vc); s = await waitStable(60000);
        if (!s) return { err: 'timeout-load2' }; if (s === 'NODATA' || s === 'EMPTY') return nod('서버 응답'); }
      else { // 저장 전 확인: 체크박스가 모두 켜졌고 화면 항목 수가 맞는지
        const on = [...gd().querySelectorAll('[id^=meaDrop_] input[type=checkbox]')].filter(c => c.checked).length;
        if (on !== boxes.length) return { err: `mea-check ${on}/${boxes.length}` };
        const rs = gd().getElementById('rowSession'); const shown = rs ? new Set([...rs.querySelectorAll('td.rowMeaTitle')].map(t => t.innerText.trim())).size : 0;
        if (shown > 0 && shown !== boxes.length) return { err: `mea-shown ${shown}/${boxes.length}` }; }
    }
    const p = parse(gd());
    const span = gd().querySelector('[id^=pageDIV_] span'); const nPages = span ? +((span.innerText.match(/\d+/) || [1])[0]) : 1;
    for (let pg = 2; pg <= nPages; pg++) {
      const before = sig(gd()); gd().querySelector('[id^=pageDIV_] img[alt="Next Page"]').click();
      let t = Date.now(); while (Date.now() - t < 30000) { await sleep(400); const g = sig(gd()); if (g && g !== before) break; }
      s = await waitStable(); if (!s || s === 'NODATA' || s === 'EMPTY') return { err: 'timeout-page' + pg };
      if (+gd().querySelector('[id^=pageDIV_] input').value !== pg) return { err: 'page-mismatch' };
      mergePage(p, parse(gd()));
    }
    if (new Set(p.rows.map(x => x.length)).size > 1) return { err: 'inconsistent-rows' };
    p.pages = nPages; p.ms = Date.now() - t0; p.meaAll = boxes.length; p.meaOn = fallback ? boxes.length - off.length : boxes.length;
    p.meaMissing = fallback ? offNames : [];
    p.msg = gd().body.innerText.match(/주\)[^\n]*/g) || []; if (fallback) p.msg.push('서버 오류로 다음 수치항목 제외: ' + offNames.join(', '));
    return p;
  }

  /* ---------- 작업 목록 ---------- */
  const byId = Object.fromEntries(statsMenuList.map(x => [x.menuId, x]));
  const path = x => { const p = []; let c = x; while (c && c.menuId !== '0') { p.unshift(c.menuName); c = byId[c.pMenuId]; } return p; };
  async function buildJobs(from, to, onlyPids) {
    const jobs = [], skipped = [];
    for (const x of statsMenuList.filter(m => m.menuType === 'P')) {
      if (onlyPids && !onlyPids.includes(+x.patternId)) continue;
      const termsYn = (x.rootName.startsWith('교통사고') && x.trendYn === 'N') ? 'Y' : 'N';
      let d = null;
      for (let a = 0; a < 3 && !d; a++) {
        try { d = await fetch(`/sta/acs/exs/selectPatternInfo.do?subjectId=${x.subjectId}&patternId=${x.patternId}&termsYn=${termsYn}`).then(r => r.ok ? r.json() : null); } catch (e) { d = null; }
        if (!d) await sleep(2000);
      }
      if (!d) { st.errors.push({ key: x.patternId, err: 'pattern-info' }); continue; }
      const di = d.dateInfo || null;
      await put('meta', { pid: x.patternId, subjectId: x.subjectId, menuId: x.menuId, name: x.menuName, path: path(x), root: x.rootName, trend: x.trendYn, dateInfo: di,
        dims: (d.dimensionList || []).map(z => ({ name: z.dispName, id: z.dimAttrId, n: z.dimensionDetailList.length })) });
      if (!di) { jobs.push({ pid: x.patternId, vc: '', label: 'all' }); continue; }
      const L = di.minYear.length, y0 = Math.max(from, +di.minYear.slice(0, 4)), y1 = Math.min(to, +di.maxYear.slice(0, 4));
      if (y0 > y1) { skipped.push({ pid: x.patternId, name: x.menuName, maxYear: di.maxYear }); continue; }
      const span = /일별/.test(x.menuName) ? 1 : 5;
      for (let a = y0; a <= y1; a += span) { const b = Math.min(a + span - 1, y1);
        const vc = L === 4 ? `D${di.dimAttrId}=${a}~${b};` : L === 6 ? `D${di.dimAttrId}=${a}01~${b}12;` : `D${di.dimAttrId}=${a}0101~${b}1231;`;
        jobs.push({ pid: x.patternId, vc, label: `${a}-${b}` }); }
    }
    return { jobs, skipped };
  }

  /* ---------- 실행 ---------- */
  async function run({ from = new Date().getFullYear() - 1, to = from, pids = null, passes = 3 } = {}) {
    if (st.running) return console.warn('이미 실행 중입니다. TAAS.status() 로 확인하세요.');
    db = db || await openDB();
    Object.assign(st, { running: true, stop: false, done: 0, errors: [], from, to, started: Date.now() });
    console.log(`장표 정보를 읽는 중 (${from}~${to})…`);
    const { jobs, skipped } = await buildJobs(from, to, pids);
    st.total = jobs.length; st.skipped = skipped;
    if (skipped.length) console.log(`${skipped.length}개 장표는 TAAS에 ${from}~${to}년 자료가 아직 없습니다.`, skipped);
    for (let pass = 1; pass <= passes && !st.stop; pass++) {
      const have = new Set(await keys('rec')); const miss = jobs.filter(j => !have.has(j.pid + '|' + j.label));
      st.pass = pass; if (!miss.length) break;
      for (const j of miss) {
        if (st.stop) break; const key = j.pid + '|' + j.label; st.current = key; let r = null;
        for (let a = 0; a < 2; a++) { while (!navigator.onLine) await sleep(10000);
          try { r = await Promise.race([fetchTable(j.pid, j.vc), sleep(300000).then(() => ({ err: 'job-timeout' }))]); } catch (e) { r = { err: String(e) }; }
          if (r && r.nodata && TRANSIENT.test((r.msg || []).join(' '))) r = { err: 'transient: ' + (r.msg || [''])[0].slice(0, 80) };
          if (!r.err) break; await sleep(4000); }
        if (r.err) st.errors.push({ key, err: r.err, pass });
        else await put('rec', { key, pid: j.pid, label: j.label, vc: j.vc, lab: r.lab, colDims: r.colDims, rows: r.rows, cols: r.cols, data: r.data,
          msg: r.msg, pages: r.pages, ms: r.ms, nodata: !!r.nodata, meaAll: r.meaAll ?? 0, meaOn: r.meaOn ?? 0, meaMissing: r.meaMissing || [], ts: Date.now() });
        st.done++; if (st.done % 10 === 0) console.log(status()); await sleep(600);
      }
    }
    st.running = false; st.current = null; console.log('수집 완료.', status(), '→ TAAS.export() 로 저장하세요.');
  }
  function status() {
    const s = st, el = s.started ? Math.round((Date.now() - s.started) / 1000) : 0;
    return { 실행중: s.running, 구간: `${s.from}~${s.to}`, 진행: `${s.done}/${s.total}`, 순회: s.pass, 현재: s.current, 오류: s.errors.length, 경과초: el };
  }
  async function exportFile(filename) {
    db = db || await openDB();
    const recs = (await all('rec')).filter(r => { if (!st.from) return true; const a = +r.label.slice(0, 4); return isNaN(a) || (a >= st.from && a <= st.to) || r.label === 'all'; });
    const meta = await all('meta');
    const json = JSON.stringify({ exported: new Date().toISOString(), range: [st.from, st.to], meta, recs });
    const blob = await new Response(new Blob([json]).stream().pipeThrough(new CompressionStream('gzip'))).blob();
    const name = filename || `taas_raw_${st.from && st.from === st.to ? st.from : (st.from ? st.from + '-' + st.to : 'all')}.json.gz`;
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = name; document.body.appendChild(a); a.click(); a.remove();
    return { 파일: name, 장표구간: recs.length, 크기MB: (blob.size / 1e6).toFixed(2) };
  }
  async function reset() { db = db || await openDB();
    await new Promise(res => { const t = db.transaction(['rec', 'meta'], 'readwrite'); t.objectStore('rec').clear(); t.objectStore('meta').clear(); t.oncomplete = res; });
    return '저장된 수집 결과를 비웠습니다.'; }

  window.TAAS = { run, status, export: exportFile, stop: () => { st.stop = true; return '현재 장표를 마치고 멈춥니다.'; }, reset, errors: () => st.errors };
  console.log('TAAS 수집기 준비 완료. 예) TAAS.run({from: 2026, to: 2026})');
})();
