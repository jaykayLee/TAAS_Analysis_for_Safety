// 공공데이터포털(data.go.kr) 파일데이터 받기 — 사용자 PC 브라우저에서 www.data.go.kr 페이지에 주입해 씁니다.
//   await DGK.file('15065567')   → {pk, title, bytes, text}  (CSV 는 UTF-8/EUC-KR 자동 판별)
//   DGK.dump(['15065567', …])    → 큰 문자열(10만 자 이상이면 도구가 파일로 저장) — 클라우드에서 <<DGK>>…<<DGK>> 사이 JSON
// 표준데이터(standard.do)는 화면의 StdDownloadManager 로 페이지별 JSON 을 받아 집계합니다(ops/EXT_UPDATE.md 참고).
(() => {
  const dec = b => { let t = new TextDecoder('utf-8').decode(b); if (t.includes('�')) t = new TextDecoder('euc-kr').decode(b); return t };
  async function file(pk) {
    const h = await (await fetch(`/data/${pk}/fileData.do`)).text();
    const m = h.match(/fn_fileDataDown\('(\d+)',\s*'([^']+)'/);
    const title = ((h.match(/<title>([^<]*)/) || [])[1] || '').replace(/\s*\|\s*공공데이터포털\s*$/, '');
    if (!m) return { pk, title, err: '다운로드 버튼 없음' };
    const j = JSON.parse(await (await fetch('/tcs/dss/selectFileDataDownload.do?recommendDataYn=Y&publicDataPk=' + m[1] + '&publicDataDetailPk=' + encodeURIComponent(m[2]))).text());
    if (!j.status && !j.atchFileId) return { pk, title, err: '파일 정보 없음' };
    const r = await fetch(`/cmm/cmm/fileDownload.do?atchFileId=${j.atchFileId}&fileDetailSn=${j.fileDetailSn}&dataNm=x`);
    const b = await r.arrayBuffer();
    return { pk, title, bytes: b.byteLength, text: dec(b) };
  }
  async function dump(pks) {
    const o = {};
    for (const pk of pks) { try { o[pk] = await file(pk) } catch (e) { o[pk] = { pk, err: String(e) } } await new Promise(r => setTimeout(r, 1500)) }
    const s = JSON.stringify(o); return '<<DGK>>' + s + '<<DGK>>' + ' '.repeat(Math.max(0, 110000 - s.length));
  }
  window.DGK = { file, dump };
  return 'DGK ready';
})();
