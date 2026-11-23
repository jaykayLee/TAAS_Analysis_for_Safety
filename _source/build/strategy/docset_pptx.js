// 문서 세트 PowerPoint 생성기(v3.9 디자인 개편, 프로젝트 공통) — docset.py가 만든 _work/_docset_pptx.json → 덱마다 .pptx 1개.
// 디자인: 경영진 보고용 — 표지·구분은 어두운 배경 이미지(칩·회로, 흐리게), 본문은 아주 옅은 같은 이미지. 얇은 선·여백·그림자·번호 배지로 위계 표현.
// 슬라이드 종류: title · summary(핵심 요약, 자동) · structure(프로젝트 구조도) · cards · bullets · flow · table · map · timeline
const fs = require("fs"); const pptxgen = require("pptxgenjs"); const path = require("path");
const SKILL = process.env.PPTX_SKILL || "/root/.claude/skills/synced/79e9ec66-b16f-4601-8565-ce11f53a5e3c_f6823d10-b84a-4539-9527-e4da2f4edf0d/pptx";
let applyTheme = null; try { ({ applyTheme } = require(path.join(SKILL, "scripts", "apply_theme.js"))); } catch (e) { }
const WORK = path.join(__dirname, "..", "_work");
const THEME = { name: "Executive Navy", headFontFace: "Malgun Gothic", bodyFontFace: "Malgun Gothic",
  colors: { dk1: "1B2433", lt1: "FFFFFF", dk2: "0B1F3A", lt2: "F3F6FA", accent1: "00A3AD", accent2: "2F6FDB", accent3: "C8475E", accent4: "6B7A90", accent5: "D99A1E", accent6: "3E8E5E", hlink: "2F6FDB", folHlink: "6A4FD0" } };
const C = THEME.colors, NAVY = C.dk2, INK = C.dk1, TEAL = C.accent1, BLUE = C.accent2, AMBER = C.accent5, SLATE = C.accent4;
const MUTED = "5B677A", FAINT = "8C97A8", LINE = "D9E0E8", CARD = "FFFFFF", TINT = "EEF4F8";
const W = 13.333, H = 7.5, M = 0.65;
const shadow = () => ({ type: "outer", blur: 8, offset: 2, angle: 90, color: "0B1F3A", opacity: 0.12 });

async function deck(D) {
  const pres = new pptxgen(); pres.layout = "LAYOUT_WIDE";
  pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
  pres.title = D.title; pres.author = "J.K. Lee"; pres.subject = D.subtitle || D.title;
  const bgD = path.join(WORK, "bg_dark.jpg"), bgL = path.join(WORK, "bg_light.jpg");
  pres.defineSlideMaster({ title: "TITLE", background: fs.existsSync(bgD) ? { path: bgD } : { color: NAVY }, objects: [
    { placeholder: { options: { name: "title", type: "title", x: M, y: 2.45, w: 7.4, h: 1.5, fontSize: 40, bold: true, color: "FFFFFF", valign: "top", align: "left", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: M, y: 4.05, w: 7.0, h: 1.3, fontSize: 17, color: "C9D6E8", valign: "top", align: "left", margin: 0 }, text: "" } }] });
  pres.defineSlideMaster({ title: "CONTENT", background: fs.existsSync(bgL) ? { path: bgL } : { color: "FAFBFD" }, margin: [0.5, M, 0.6, M], objects: [
    { placeholder: { options: { name: "title", type: "title", x: M, y: 0.62, w: W - 2 * M, h: 0.62, fontSize: 24, bold: true, color: NAVY, valign: "middle", align: "left", margin: 0 }, text: "" } },
    { text: { text: D.footer, options: { x: M, y: H - 0.42, w: 8, h: 0.28, fontSize: 9, color: FAINT, margin: 0 } } }],
    slideNumber: { x: W - 1.05, y: H - 0.42, w: 0.45, h: 0.28, fontSize: 9, color: FAINT, fontFace: "Malgun Gothic", align: "right" } });
  const T = (s, text, o) => s.addText(text, Object.assign({ isTextBox: true, margin: 0, fontSize: 12, color: INK, valign: "top" }, o));
  const card = (s, x, y, w, h, o = {}) => s.addShape(pres.shapes.ROUNDED_RECTANGLE, Object.assign({ x, y, w, h, rectRadius: 0.06, fill: { color: o.fill || CARD }, line: { color: o.line || LINE, width: 0.75 }, shadow: o.noShadow ? undefined : shadow() }, o.extra || {}));
  const badge = (s, x, y, d, c, lab, fz = 11) => { s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: c }, line: { color: c } }); T(s, lab, { x, y, w: d, h: d, align: "center", valign: "middle", color: "FFFFFF", bold: true, fontSize: fz }); };
  // 선은 폭·높이가 음수면 PowerPoint가 파일을 열지 못한다(<a:ext cx<0>) — 시작점을 옮기고 뒤집기로 정규화
  const ln = (s, x, y, w, h, o = {}) => { o = Object.assign({}, o);
    if (w < 0) { x += w; w = -w; o.flipH = !o.flipH; } if (h < 0) { y += h; h = -h; o.flipV = !o.flipV; }
    return lnRaw(s, x, y, w, h, o); };
  const lnRaw = (s, x, y, w, h, o = {}) => s.addShape(pres.shapes.LINE, Object.assign({ x, y, w, h, line: { color: o.color || SLATE, width: o.width || 1.25, dashType: o.dash || "solid", endArrowType: o.arrow === false ? undefined : "triangle", beginArrowType: o.both ? "triangle" : undefined } }, o.flipV ? { flipV: true } : {}, o.flipH ? { flipH: true } : {}));
  const kicker = (s, t) => T(s, t.toUpperCase(), { x: M, y: 0.36, w: 8, h: 0.26, fontSize: 10, bold: true, color: TEAL, charSpacing: 2 });
  const head = (s, sl, k) => { kicker(s, sl.kicker || k || D.kicker || "Project"); s.addText(sl.title, { placeholder: "title" }); if (sl.lead) T(s, sl.lead, { x: M, y: 1.26, w: W - 2 * M, h: 0.34, fontSize: 12.5, color: MUTED }); };
  const top0 = (sl) => (sl.lead ? 1.75 : 1.5);

  const slides = D.slides.slice();
  if (D.summary && D.summary.length && slides[0] && slides[0].kind === "title" && !slides.some(x => x.kind === "summary"))
    slides.splice(1, 0, { kind: "summary", title: "핵심 요약", items: D.summary.slice(0, 4) });

  for (let sl of slides) {
    if (sl.kind === "title") {
      const s = pres.addSlide({ masterName: "TITLE" });
      T(s, (D.kicker || "Strategy Document").toUpperCase(), { x: M, y: 1.95, w: 7, h: 0.3, fontSize: 11, bold: true, color: "5FD3DA", charSpacing: 3 });
      s.addText(sl.title || D.title, { placeholder: "title" }); s.addText(sl.sub || D.subtitle || "", { placeholder: "body" });
      T(s, sl.meta || `번들 ${D.bundle}`, { x: M, y: 6.55, w: 7, h: 0.3, fontSize: 10.5, color: "8FA6C4" });
      if (sl.notes) s.addNotes(sl.notes); continue;
    }
    const s = pres.addSlide({ masterName: "CONTENT" }); head(s, sl);
    const Y = top0(sl);
    if (sl.kind === "summary") {
      const n = sl.items.length, gap = 0.28, rh = (5.2 - gap * (n - 1)) / n;
      sl.items.forEach((t, i) => { const y = 1.55 + i * (rh + gap);
        card(s, M, y, W - 2 * M, rh); s.addShape(pres.shapes.RECTANGLE, { x: M, y, w: 0.08, h: rh, fill: { color: i === 0 ? TEAL : BLUE }, line: { color: i === 0 ? TEAL : BLUE } });
        T(s, String(i + 1).padStart(2, "0"), { x: M + 0.35, y, w: 0.8, h: rh, fontSize: 26, bold: true, color: i === 0 ? TEAL : "B7C3D2", valign: "middle" });
        T(s, t, { x: M + 1.3, y, w: W - 2 * M - 1.6, h: rh, fontSize: 15, color: INK, valign: "middle" }); });
    } else if (sl.kind === "structure") {
      const F = sl.folders, cw = 3.25, cx = [M, 4.95, 9.43], r1 = Y - 0.05, rh1 = 2.0, r2 = Y + 2.35, rh2 = 2.05;
      const folder = (x, y, w, h, f, acc) => { card(s, x, y, w, h);
        s.addShape(pres.shapes.RECTANGLE, { x, y: y + 0.0, w: 0.07, h, fill: { color: acc }, line: { color: acc } });
        T(s, f.title, { x: x + 0.25, y: y + 0.14, w: w - 0.4, h: 0.32, fontSize: 14, bold: true, color: NAVY });
        if (f.role) T(s, f.role, { x: x + 0.25, y: y + 0.45, w: w - 0.4, h: 0.28, fontSize: 9.5, color: MUTED });
        const n = f.items.length, ih = Math.min(0.24, (h - 0.9) / n);
        f.items.forEach((it, i) => { const yy = y + 0.82 + i * ih; s.addShape(pres.shapes.OVAL, { x: x + 0.3, y: yy + ih / 2 - 0.035, w: 0.07, h: 0.07, fill: { color: acc }, line: { color: acc } });
          T(s, it, { x: x + 0.45, y: yy, w: w - 0.6, h: ih, fontSize: 10, color: INK, valign: "middle" }); }); };
      folder(cx[0], r1, cw, rh1, F.strategy, BLUE); folder(cx[0], r2, cw, rh2, F.references, TEAL);
      folder(cx[2], r1, cw, rh1, F.comments, AMBER); folder(cx[2], r2, cw, rh2, F.libraries, TEAL);
      // 패널(가운데) — 어두운 카드
      const px = cx[1], pw = cw + 0.18, ph = 2.95;
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: px, y: r1, w: pw, h: ph, rectRadius: 0.06, fill: { color: NAVY }, line: { color: NAVY }, shadow: shadow() });
      T(s, F.panel.title, { x: px + 0.25, y: r1 + 0.14, w: pw - 0.5, h: 0.32, fontSize: 14, bold: true, color: "FFFFFF" });
      T(s, F.panel.role || "사용자 중심 컨트롤러", { x: px + 0.25, y: r1 + 0.45, w: pw - 0.5, h: 0.28, fontSize: 9.5, color: "AFC2DA" });
      F.panel.items.forEach((it, i) => { const yy = r1 + 0.85 + i * 0.5, hi = it === "Main";
        s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: px + 0.25, y: yy, w: pw - 0.5, h: 0.42, rectRadius: 0.05, fill: { color: hi ? TEAL : "16335A" }, line: { color: hi ? TEAL : "2C4D78", width: 0.75 } });
        T(s, it, { x: px + 0.25, y: yy, w: pw - 0.5, h: 0.4, align: "center", valign: "middle", fontSize: 11.5, bold: hi, color: "FFFFFF" }); });
      // 연결선 — 굵기·색 = 중요도
      const sR = cx[0] + cw, pL = px, pR = px + pw, lL = cx[2];
      ln(s, sR + 0.05, r1 + 1.1, pL - sR - 0.1, 0, { color: BLUE, width: 2.5 });                         // 전략 → 패널
      ln(s, pR + 0.05, r2 + 0.3, lL - pR - 0.1, 0, { color: TEAL, width: 2.5, flipH: true });            // 라이브러리 → 패널
      ln(s, sR + 0.05, r2 + 0.3, pL - sR - 0.1, 0, { color: SLATE, width: 1, dash: "dash" });              // 참고 → 패널(코멘트)
      ln(s, cx[0] + 1.1, r1 + rh1 + 0.06, 0, r2 - r1 - rh1 - 0.12, { color: SLATE, width: 1.5 });          // 전략 → 참고
      ln(s, cx[0] + 2.1, r1 + rh1 + 0.06, 0, r2 - r1 - rh1 - 0.12, { color: SLATE, width: 1.5, flipV: true });  // 참고 → 전략
      // 정제 레인: 참고 → 라이브러리(패널 아래)
      const yl = r2 + 1.45; ln(s, sR + 0.05, yl, lL - sR - 0.1, 0, { color: TEAL, width: 4 });
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: px + 0.05, y: yl - 0.22, w: pw - 0.1, h: 0.44, rectRadius: 0.22, fill: { color: "FFFFFF" }, line: { color: TEAL, width: 1 } });
      T(s, "정제 — 같은 분류 00~06", { x: px + 0.05, y: yl - 0.22, w: pw - 0.1, h: 0.44, align: "center", valign: "middle", fontSize: 10.5, bold: true, color: TEAL });
      // 시스템 바(_source)
      const by = r2 + rh2 + 0.18;
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: M, y: by, w: W - 2 * M, h: 0.5, rectRadius: 0.06, fill: { color: "1E2A3C" }, line: { color: "1E2A3C" } });
      T(s, [{ text: "_source", options: { bold: true, color: "5FD3DA", fontSize: 12 } }, { text: "   시스템 중심 컨트롤러 — 빌드 · 검사 · 패널 조립 · 자동 갱신 (코드만)", options: { color: "D5DEEA", fontSize: 11 } }], { x: M + 0.25, y: by, w: W - 2 * M - 0.5, h: 0.5, valign: "middle" });
      // 피드백 루프: 사용자 코멘트 → _source(다음 업데이트)
      const rx = W - M + 0.18; ln(s, lL + cw, r1 + 1.0, rx - lL - cw, 0, { color: AMBER, width: 1.75, arrow: false });
      ln(s, rx, r1 + 1.0, 0, by + 0.25 - r1 - 1.0, { color: AMBER, width: 1.75, arrow: false });
      ln(s, W - M, by + 0.25, rx - (W - M), 0, { color: AMBER, width: 1.75, flipH: true });          // 오른쪽 → 왼쪽(바 안으로) 화살표
      // 범례
      const ly = by + 0.58; T(s, [{ text: "━ ", options: { color: TEAL, bold: true } }, { text: "핵심 전달(굵기 = 중요도)    ", options: { color: MUTED } }, { text: "┄ ", options: { color: SLATE } }, { text: "근거·코멘트    ", options: { color: MUTED } }, { text: "━ ", options: { color: AMBER, bold: true } }, { text: "피드백 → 다음 업데이트", options: { color: MUTED } }], { x: M, y: ly, w: 9, h: 0.26, fontSize: 9.5 });
    } else if (sl.kind === "cards") {
      const n = sl.cards.length, gap = 0.3, cw = (W - 2 * M - gap * (n - 1)) / n, ch = Math.max(sl.h || 0, 3.5), pal = [TEAL, BLUE, AMBER, C.accent6, C.accent3];
      sl.cards.forEach(([k, big, d], i) => { const x = M + i * (cw + gap), c = pal[i % pal.length];
        card(s, x, Y, cw, ch); badge(s, x + 0.25, Y + 0.25, 0.42, c, String(i + 1));
        T(s, k, { x: x + 0.8, y: Y + 0.27, w: cw - 1.0, h: 0.38, fontSize: 12.5, bold: true, color: c, valign: "middle" });
        T(s, big, { x: x + 0.25, y: Y + 0.85, w: cw - 0.5, h: 0.7, fontSize: n > 3 ? 15 : 17, bold: true, color: NAVY });
        s.addShape(pres.shapes.LINE, { x: x + 0.25, y: Y + 1.6, w: cw - 0.5, h: 0, line: { color: LINE, width: 0.75 } });
        T(s, d, { x: x + 0.25, y: Y + 1.72, w: cw - 0.5, h: ch - 1.85, fontSize: 10.5, color: MUTED }); });
      if (sl.foot) { const fy = Y + ch + 0.4; s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: M, y: fy, w: W - 2 * M, h: 0.62, rectRadius: 0.06, fill: { color: TINT }, line: { color: TINT } });
        s.addShape(pres.shapes.RECTANGLE, { x: M, y: fy, w: 0.07, h: 0.62, fill: { color: TEAL }, line: { color: TEAL } }); T(s, sl.foot, { x: M + 0.3, y: fy, w: W - 2 * M - 0.5, h: 0.62, fontSize: 12.5, color: NAVY, bold: true, valign: "middle" }); }
    } else if (sl.kind === "bullets") {
      const n = sl.items.length, cols = n <= 4 ? 2 : 2, rows = Math.ceil(n / cols), gap = 0.3, cw = (W - 2 * M - gap) / cols, rh = Math.min(2.2, (5.0 - gap * (rows - 1)) / rows), big = rh > 1.6;
      sl.items.forEach(([k, d], i) => { const x = M + (i % cols) * (cw + gap), y = Y + Math.floor(i / cols) * (rh + gap);
        card(s, x, y, cw, rh); badge(s, x + 0.35, y + 0.35, big ? 0.62 : 0.5, i % 2 ? BLUE : TEAL, String(i + 1), big ? 16 : 13);
        T(s, k, { x: x + (big ? 1.2 : 1.0), y: y + 0.36, w: cw - 1.45, h: 0.5, fontSize: big ? 19 : 14, bold: true, color: NAVY, valign: "middle" });
        T(s, d, { x: x + (big ? 1.2 : 1.0), y: y + (big ? 1.0 : 0.62), w: cw - 1.45, h: rh - (big ? 1.2 : 0.75), fontSize: big ? 13 : 11, color: MUTED }); });
    } else if (sl.kind === "flow") {
      const n = sl.steps.length, w = (W - 2 * M) / n, cy = Y + 1.0;
      s.addShape(pres.shapes.LINE, { x: M + w / 2, y: cy, w: w * (n - 1), h: 0, line: { color: LINE, width: 2 } });
      sl.steps.forEach(([k, d], i) => { const x = M + i * w, c = i === n - 1 ? AMBER : TEAL;
        s.addShape(pres.shapes.OVAL, { x: x + w / 2 - 0.36, y: cy - 0.36, w: 0.72, h: 0.72, fill: { color: "FFFFFF" }, line: { color: c, width: 2.25 }, shadow: shadow() });
        T(s, String(i + 1).padStart(2, "0"), { x: x + w / 2 - 0.36, y: cy - 0.36, w: 0.72, h: 0.72, align: "center", valign: "middle", fontSize: 14, bold: true, color: c });
        card(s, x + 0.12, cy + 0.65, w - 0.24, 1.75);
        T(s, k, { x: x + 0.25, y: cy + 0.8, w: w - 0.5, h: 0.4, align: "center", fontSize: 13, bold: true, color: NAVY });
        T(s, d, { x: x + 0.25, y: cy + 1.25, w: w - 0.5, h: 1.4, align: "center", fontSize: 10.5, color: MUTED }); });
      if (sl.foot) { const fy = cy + 2.85; s.addShape(pres.shapes.RECTANGLE, { x: M, y: fy, w: 0.06, h: 0.5, fill: { color: TEAL }, line: { color: TEAL } }); T(s, sl.foot, { x: M + 0.2, y: fy, w: W - 2 * M - 0.2, h: 0.5, fontSize: 12.5, bold: true, color: NAVY, valign: "middle" }); }
    } else if (sl.kind === "table" || sl.kind === "map") {
      const nr = sl.rows.length + 1, rh = Math.min(sl.rowH || 0.32, 5.05 / nr), fz = Math.min(sl.fontSize || 10.5, rh < 0.3 ? 9 : 10.5); sl = Object.assign({}, sl, { rowH: rh });
      const hd = sl.head.map(t => ({ text: t, options: { bold: true, color: NAVY, fill: { color: TINT }, fontSize: fz, border: [{ type: "none" }, { type: "none" }, { pt: 1.5, color: NAVY }, { type: "none" }] } }));
      const rows = sl.rows.map((r) => r.map((c, j) => ({ text: String(c), options: { fontSize: fz, color: j === 0 ? NAVY : INK, bold: j === 0, fill: { color: "FFFFFF" }, border: [{ type: "none" }, { type: "none" }, { pt: 0.5, color: LINE }, { type: "none" }] } })));
      card(s, M - 0.1, Y - 0.1, W - 2 * M + 0.2, Math.min(5.35, (sl.rowH || 0.32) * (rows.length + 1) + 0.25), { noShadow: false });
      s.addTable([hd, ...rows], { x: M, y: Y, w: W - 2 * M, colW: sl.colW, valign: "middle", margin: [0.03, 0.08, 0.03, 0.08], rowH: sl.rowH || 0.32 });
      if (sl.foot) T(s, sl.foot, { x: M, y: 6.55, w: W - 2 * M, h: 0.35, fontSize: 10.5, color: MUTED });
    } else if (sl.kind === "timeline") {
      const n = sl.items.length, per = Math.ceil(n / 2), cw = (W - 2 * M) / per;
      [0, 1].forEach(row => { const y = Y + 0.35 + row * 2.6; if (row * per < n) s.addShape(pres.shapes.LINE, { x: M, y, w: W - 2 * M, h: 0, line: { color: LINE, width: 2 } }); });
      sl.items.forEach(([v, dt, t], i) => { const row = Math.floor(i / per), c = i % per, x = M + c * cw, y = Y + 0.35 + row * 2.6, last = i === n - 1;
        s.addShape(pres.shapes.OVAL, { x: x + 0.05, y: y - 0.12, w: 0.24, h: 0.24, fill: { color: last ? AMBER : TEAL }, line: { color: "FFFFFF", width: 1.5 } });
        T(s, v, { x: x + 0.4, y: y - 0.2, w: cw - 0.45, h: 0.32, fontSize: 14, bold: true, color: NAVY }); T(s, dt, { x: x + 0.4, y: y + 0.12, w: cw - 0.45, h: 0.24, fontSize: 9.5, color: FAINT });
        T(s, t, { x: x + 0.05, y: y + 0.5, w: cw - 0.2, h: 1.8, fontSize: 9.5, color: MUTED }); });
    }
    if (sl.notes) s.addNotes(sl.notes);
  }
  await pres.writeFile({ fileName: D.file });
  if (applyTheme) await applyTheme(D.file, THEME);
  console.log("saved", path.basename(D.file));
}
(async () => { for (const D of JSON.parse(fs.readFileSync(process.argv[2], "utf8"))) await deck(D); })();
