// TAAS 새 연도 수집기 (자동 갱신용) — runner_inject.js → runner_v9.js 를 먼저 주입한 뒤 이 파일을 주입합니다.
//   주입 순서: window.__noAutoStart = true;  → runner_inject.js → runner_v9.js → taas_update.js
//
//   await TAASU.check()                    장표 정보(연도 범위)를 TAAS에서 새로 읽어 저장 → {latest, years:{연도: 장표 수}, patterns}
//   TAASU.run({years:[2026], force:false}) 해당 연도만 v9 직접 조회로 수집 (다시 부르면 받은 것은 건너뛰고 이어받음)
//                                          force:true = 그 연도를 이미 받았어도 다시 받음 (확정치 재수집)
//   TAASU.status()                         {실행중, 진행, 남은작업, 오류, 경과초, 완료}
//   await TAASU.pack([2026])               내보낼 원본을 gzip+base64 로 준비 → {chunks, bytes, recs}
//   TAASU.chunk(i)                         i번째 조각(base64 문자열, 최대 400KB) — 차례로 읽어 이어 붙인 뒤 base64 디코드하면 json.gz
//   await TAASU.download([2026])           (대안) 다운로드 폴더로 taas_raw_full_2026.json.gz 저장
//
// 레코드 label 은 '연도-연도'(예: 2026-2026). 라이브러리 조립 때 같은 장표·같은 구간은 나중에 받은 값이 이깁니다.
(() => {
  if (!location.host.includes('taas.koroad.or.kr') || !window.statsMenuList) return 'TAAS 상세통계 페이지(typical.do)에서 실행하세요';
  if (!window.__put || !window.__startRunnerV9) return 'runner_inject.js 와 runner_v9.js 를 먼저 주입하세요';
  const byId = Object.fromEntries(statsMenuList.map(x => [x.menuId, x]));
  const path = x => { const p = []; let c = x; while (c && c.menuId !== '0') { p.unshift(c.menuName); c = byId[c.pMenuId]; } return p; };
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  let packed = null, lastYears = null;

  async function check() {
    const years = {}, fail = []; let latest = 0, n = 0;
    for (const x of statsMenuList.filter(m => m.menuType === 'P')) {
      const termsYn = (x.rootName.startsWith('교통사고') && x.trendYn === 'N') ? 'Y' : 'N';
      let d = null;
      for (let a = 0; a < 3 && !d; a++) {
        try { d = await fetch(`/sta/acs/exs/selectPatternInfo.do?subjectId=${x.subjectId}&patternId=${x.patternId}&termsYn=${termsYn}`).then(r => r.ok ? r.json() : null); } catch (e) { d = null; }
        if (!d) await sleep(1500);
      }
      if (!d) { fail.push(x.patternId); continue; }
      const di = d.dateInfo || null;
      await __put('meta', { pid: x.patternId, subjectId: x.subjectId, menuId: x.menuId, name: x.menuName, path: path(x), root: x.rootName, trend: x.trendYn, dateInfo: di,
        dims: (d.dimensionList || []).map(z => ({ name: z.dispName, id: z.dimAttrId, n: z.dimensionDetailList.length })) });
      n++;
      if (di) { const y = +di.maxYear.slice(0, 4); years[y] = (years[y] || 0) + 1; if (y > latest) latest = y; }
    }
    return { latest, years, patterns: n, failed: fail };
  }

  async function run({ years, force = false } = {}) {
    if (!years || !years.length) throw new Error('years 를 주세요. 예: TAASU.run({years:[2026]})');
    lastYears = years;
    const metas = await __all('meta'), jobs = [];
    for (const x of metas) {
      const di = x.dateInfo;
      if (!di) { jobs.push({ pid: x.pid, vc: '', label: 'all' }); continue; } // 연도 축이 없는 장표는 통째로 다시 받음
      const L = di.minYear.length, y0 = +di.minYear.slice(0, 4), y1 = +di.maxYear.slice(0, 4);
      for (const y of years) {
        if (y < y0 || y > y1) continue;
        const vc = L === 4 ? `D${di.dimAttrId}=${y}~${y};` : L === 6 ? `D${di.dimAttrId}=${y}01~${y}12;` : `D${di.dimAttrId}=${y}0101~${y}1231;`;
        jobs.push({ pid: x.pid, vc, label: `${y}-${y}` });
      }
    }
    // 'all' 장표와 force 대상은 이전 기록을 지워 새로 받게 함
    const del = new Set(jobs.filter(j => j.label === 'all' || force).map(j => j.pid + '|' + j.label));
    if (del.size) await new Promise(res => { const t = __db.transaction('rec', 'readwrite'); const s = t.objectStore('rec'); del.forEach(k => s.delete(k)); t.oncomplete = res; });
    window.__jobs = jobs; packed = null;
    __startRunnerV9();
    return { jobs: jobs.length, years };
  }

  function status() {
    const S = window.__state || {};
    const el = S.started ? Math.round((Date.now() - S.started) / 1000) : 0;
    return { 실행중: !!S.running, 진행: S.fetched || 0, 남은작업: S.missing ?? null, 순회: S.pass || 0, 현재: S.current || null,
      오류: (S.errors || []).length, 최근오류: (S.errors || []).slice(-3), 경과초: el, 완료: !!S.allDone };
  }

  async function records(years) {
    const ys = years || lastYears || [];
    return (await __all('rec')).filter(r => r.label === 'all' || ys.includes(+r.label.slice(0, 4)));
  }

  async function blobOf(years) {
    const recs = await records(years), meta = await __all('meta');
    const json = JSON.stringify({ exported: new Date().toISOString(), range: years, meta, recs });
    return { blob: await new Response(new Blob([json]).stream().pipeThrough(new CompressionStream('gzip'))).blob(), recs: recs.length };
  }

  async function pack(years) {
    const { blob, recs } = await blobOf(years);
    const b = new Uint8Array(await blob.arrayBuffer()); let s = '';
    for (let i = 0; i < b.length; i += 0x8000) s += String.fromCharCode.apply(null, b.subarray(i, i + 0x8000));
    const b64 = btoa(s), size = 400000; packed = [];
    for (let i = 0; i < b64.length; i += size) packed.push(b64.slice(i, i + size));
    return { chunks: packed.length, bytes: b.length, recs, file: `taas_raw_full_${(years || lastYears).join('_')}.json.gz` };
  }

  async function download(years) {
    const { blob, recs } = await blobOf(years);
    const name = `taas_raw_full_${(years || lastYears).join('_')}.json.gz`;
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = name; document.body.appendChild(a); a.click(); a.remove();
    return { file: name, recs, bytes: blob.size };
  }

  window.TAASU = { check, run, status, pack, chunk: i => (packed || [])[i] ?? null, download, stop: () => { window.__gen = (window.__gen || 0) + 1; return '중지했습니다'; } };
  return 'TAASU ready';
})();
