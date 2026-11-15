const pptxgen = require("pptxgenjs");
const path = require("path");
const fs = require("fs");
const sizeOf = f => { const b = fs.readFileSync(f); return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) }; };
// 테마 색 적용 도구 경로는 환경변수 APPLY_THEME 로 지정 (없으면 테마 적용 생략)
const applyTheme = process.env.APPLY_THEME ? require(process.env.APPLY_THEME).applyTheme : async () => {};

const IMG = p => path.join(__dirname, "img", p);
const OUT = process.env.OUT || path.join(__dirname, "..", "TAAS_교통사고분석패널_사용매뉴얼.pptx");
const FONT = "맑은 고딕";
const THEME = {
  name: "TAAS Manual White",
  headFontFace: FONT, bodyFontFace: FONT,
  colors: { dk1: "1B2433", lt1: "FFFFFF", dk2: "0B2545", lt2: "F3F6FA",
    accent1: "0B5CAD", accent2: "0EA5C6", accent3: "F2A900", accent4: "E4572E", accent5: "1BAA7A", accent6: "7A8699",
    hlink: "0B5CAD", folHlink: "5B4BA8" },
};
const HX = { navy: "0B2545", blue: "0B5CAD", cyan: "0EA5C6", amber: "F2A900", coral: "E4572E", green: "1BAA7A", gray: "7A8699", ink: "1B2433", tint: "F3F6FA", line: "D5DBE3", mute: "5A6472" };

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5
pres.theme = { headFontFace: FONT, bodyFontFace: FONT };
pres.title = "TAAS 교통사고 분석 패널 사용 매뉴얼";
pres.author = "J.K. Lee";
const C = pres.SchemeColor;

// ---------- 레이아웃
pres.defineSlideMaster({
  title: "COVER", background: { color: "FFFFFF" },
  objects: [{ image: { x: 0, y: 0, w: 13.333, h: 7.5, path: IMG("wm_cover.png") } }],
});
pres.defineSlideMaster({
  title: "CONTENT", background: { color: "FFFFFF" },
  margin: [0.5, 0.6, 0.6, 0.6],
  objects: [
    { image: { x: 0, y: 0, w: 13.333, h: 7.5, path: IMG("wm.png") } },
    { placeholder: { options: { name: "kicker", type: "body", x: 0.6, y: 0.32, w: 9, h: 0.32, fontSize: 11, bold: true, color: C.accent2, margin: 0 }, text: "" } },
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.62, w: 12.1, h: 0.7, fontSize: 28, bold: true, color: C.text2, margin: 0, valign: "middle", align: "left" }, text: "" } },
    { text: { text: "TAAS 교통사고 분석 패널 · 사용 매뉴얼", options: { x: 0.6, y: 7.05, w: 6, h: 0.3, fontSize: 9, color: C.accent6, margin: 0 } } },
  ],
  slideNumber: { x: 12.2, y: 7.05, w: 0.5, h: 0.3, fontSize: 9, color: C.accent6, align: "right" },
});

let n = 0;
function content(kicker, title, section) {
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: section });
  s.addText(kicker, { placeholder: "kicker" });
  s.addText(title, { placeholder: "title" });
  return s;
}
const shadow = () => ({ type: "outer", blur: 6, offset: 2, angle: 90, color: "1B2433", opacity: 0.18 });
function shot(s, file, x, y, w, h, name) { // 비율 유지로 상자 안에 맞춤 + 테두리·그림자
  const im = sizeOf(IMG(file)); const r = Math.min(w / im.w, h / im.h); const ww = im.w * r, hh = im.h * r;
  const xx = x + (w - ww) / 2, yy = y;
  s.addShape(pres.shapes.RECTANGLE, { x: xx, y: yy, w: ww, h: hh, fill: { color: C.background1 }, line: { color: HX.line, width: 0.75 }, shadow: shadow(), objectName: name + " 테두리" });
  s.addImage({ path: IMG(file), x: xx, y: yy, w: ww, h: hh, altText: name, objectName: name });
  return { x: xx, y: yy, w: ww, h: hh };
}
function badge(s, num, x, y, d = 0.34, color = C.accent1) {
  s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color }, line: { color: C.background1, width: 1.5 }, objectName: "번호 " + num });
  s.addText(String(num), { x, y, w: d, h: d, fontSize: d > 0.4 ? 14 : 11, bold: true, color: C.background1, align: "center", valign: "middle", margin: 0, isTextBox: true });
}
function card(s, x, y, w, h, fill = C.background2) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: fill }, line: { color: HX.line, width: 0.5 } });
}
function tx(s, text, o) { s.addText(text, { isTextBox: true, margin: 0, valign: "top", fontSize: 14, color: C.text1, ...o }); }

// ================= 1. 표지
pres.addSection({ title: "시작" });
{
  const s = pres.addSlide({ masterName: "COVER", sectionTitle: "시작" });
  tx(s, "TAAS 교통사고 상세통계 라이브러리", { x: 0.9, y: 1.75, w: 9, h: 0.4, fontSize: 16, bold: true, color: C.accent2 });
  tx(s, "교통사고 분석 패널\n사용 매뉴얼", { x: 0.9, y: 2.25, w: 9, h: 1.9, fontSize: 44, bold: true, color: C.text2, lineSpacingMultiple: 1.05 });
  tx(s, "338개 장표 + 인구 통계 · 2005~2025년 · 3,025만 칸의 교통사고 통계를\n한 화면에서 고르고, 비교하고, 상관관계를 확인하는 방법", { x: 0.9, y: 4.35, w: 9.5, h: 0.9, fontSize: 18, color: C.text1 });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.9, y: 5.65, w: 3.4, h: 0.5, rectRadius: 0.25, fill: { color: C.text2 }, line: { color: C.text2 } });
  tx(s, "버전 1.3 · 2026. 11", { x: 0.9, y: 5.65, w: 3.4, h: 0.5, fontSize: 13, bold: true, color: C.background1, align: "center", valign: "middle" });
  tx(s, "출처: 한국도로교통공단 TAAS 교통사고분석시스템 › 교통사고 상세통계 · 통계청 KOSIS 인구총조사 · 패널 버전 3", { x: 0.9, y: 6.75, w: 9, h: 0.3, fontSize: 10, color: C.accent6 });
  s.addNotes("패널을 처음 쓰는 분을 위한 안내서입니다. 라이브러리를 여는 법, 화면 구성, 탐색·상관분석·차량기술 매핑 세 탭의 모든 기능과 결과를 읽는 법, 데이터 유의사항을 다룹니다.");
}

// ================= 2. 한눈에 보기
{
  const s = content("개요", "패널은 TAAS 통계 전체를 한 곳에서 다루는 분석 화면입니다", "시작");
  const stats = [["338", "개 장표", "TAAS 상세통계 메뉴 전체"], ["21", "개 연도", "2005 ~ 2025년"], ["3,023만", "칸", "모든 축·수치항목을 켠 값"]];
  stats.forEach(([big, unit, sub], i) => {
    const y = 1.65 + i * 1.65;
    card(s, 0.6, y, 4.0, 1.4, C.background1);
    s.addText([{ text: big, options: { fontSize: 40, bold: true, color: C.accent1 } }, { text: " " + unit, options: { fontSize: 16, bold: true, color: C.text2 } }],
      { x: 0.85, y: y + 0.18, w: 3.6, h: 0.7, margin: 0, isTextBox: true, valign: "middle" });
    tx(s, sub, { x: 0.85, y: y + 0.92, w: 3.6, h: 0.32, fontSize: 13, color: HX.mute });
  });
  const tabs = [
    ["탐색", "장표 하나를 골라 연도·지역·사고유형 같은 축을 원하는 대로 펼쳐 차트와 표로 봅니다.", "예) 사고유형별 사고건수 2005~2025 추이"],
    ["상관분석", "여러 장표에서 뽑은 시계열을 모아 서로 얼마나 같이 움직이는지(상관계수·p값)를 계산합니다.", "예) 음주운전 사고와 노면 결빙 사고의 연도별 증감"],
    ["차량기술 매핑", "AEB·LKA·DMS 같은 12개 안전기술을 그 기술이 겨냥하는 사고 장표와 조건에 바로 연결합니다.", "예) AEB → 사고유형별 · 추돌"],
  ];
  tabs.forEach(([t, d, e], i) => {
    const y = 1.65 + i * 1.65;
    card(s, 5.0, y, 7.7, 1.4);
    badge(s, i + 1, 5.25, y + 0.22, 0.44, [C.accent1, C.accent2, C.accent3][i]);
    tx(s, t, { x: 5.9, y: y + 0.18, w: 6.6, h: 0.4, fontSize: 18, bold: true, color: C.text2 });
    tx(s, d, { x: 5.9, y: y + 0.58, w: 6.6, h: 0.5, fontSize: 13 });
    tx(s, e, { x: 5.9, y: y + 1.04, w: 6.6, h: 0.28, fontSize: 11, color: HX.mute, italic: true });
  });
  s.addNotes("왼쪽은 라이브러리 규모, 오른쪽은 패널의 세 탭입니다. 탐색에서 본 계열을 상관분석으로 보내고, 차량기술 매핑은 탐색과 상관분석의 바로가기 역할을 합니다.");
}

// ================= 3. 시작하기
{
  const s = content("시작하기", "라이브러리 폴더를 열면 바로 쓸 수 있습니다", "시작");
  card(s, 0.6, 1.6, 6.0, 5.15, C.background1);
  tx(s, "taas_library 폴더 구성", { x: 0.85, y: 1.78, w: 5.5, h: 0.35, fontSize: 15, bold: true, color: C.text2 });
  const tree = [
    ["panel.html", "패널 화면 — 더블클릭해서 엽니다", true],
    ["index.js · index.json", "장표 목록과 요약(목차)"],
    ["panel_js/", "패널용 장표 데이터 (panel.html 이 바로 읽음)"],
    ["panel/", "같은 데이터의 압축본 (‘폴더 열기’ 방식용)"],
    ["parquet/", "분석용 전체 표 — Python·R·DuckDB용"],
    ["raw/", "TAAS 수집 원본 — 2026년 등 새 연도 통합에 사용"],
    ["COVERAGE.md · coverage.json", "빈 구간·누락 항목 기록"],
    ["taas.py · update_library.py 등", "불러오기·연도 추가 도구"],
  ];
  tree.forEach(([a, b, hi], i) => {
    const y = 2.28 + i * 0.54;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.85, y, w: 2.55, h: 0.4, rectRadius: 0.06, fill: { color: hi ? C.accent1 : C.background2 }, line: { color: hi ? C.accent1 : HX.line, width: 0.5 } });
    tx(s, a, { x: 0.95, y, w: 2.4, h: 0.4, fontSize: 11, bold: true, color: hi ? C.background1 : C.text2, valign: "middle", fontFace: "Consolas" });
    tx(s, b, { x: 3.55, y, w: 2.95, h: 0.4, fontSize: 11, valign: "middle" });
  });
  const ways = [
    ["panel.html 더블클릭 (권장)", "라이브러리 폴더 안의 panel.html 을 크롬·엣지로 열면 전체 336개 장표가 자동으로 연결됩니다."],
    ["‘라이브러리 폴더 열기’ 버튼", "다른 곳에 있는 패널(예: 공유받은 예시 패널)에서 taas_library 폴더를 고르면 그 데이터로 바뀝니다."],
    ["‘파일로 열기’ 또는 끌어다 놓기", "폴더 선택이 막힌 환경에서 index.json 과 panel 폴더의 파일을 함께 선택하거나 창에 끌어다 놓습니다."],
  ];
  tx(s, "여는 방법", { x: 7.0, y: 1.6, w: 5.7, h: 0.35, fontSize: 15, bold: true, color: C.text2 });
  ways.forEach(([t, d], i) => {
    const y = 2.1 + i * 1.22;
    badge(s, i + 1, 7.0, y + 0.02, 0.4);
    tx(s, t, { x: 7.55, y, w: 5.15, h: 0.36, fontSize: 15, bold: true, color: C.text1 });
    tx(s, d, { x: 7.55, y: y + 0.4, w: 5.15, h: 0.72, fontSize: 12.5, color: HX.mute });
  });
  card(s, 7.0, 5.85, 5.7, 0.9, "FFF6DB");
  tx(s, [{ text: "인터넷 연결 필요  ", options: { bold: true, color: C.text2 } }, { text: "차트 그리는 기능(Chart.js)을 인터넷에서 불러옵니다. 화면 상단에 ‘예시 데이터’ 표시가 보이면 라이브러리가 아직 연결되지 않은 상태입니다." }],
    { x: 7.2, y: 5.95, w: 5.35, h: 0.72, fontSize: 11.5, valign: "middle" });
  s.addNotes("panel_js 와 panel 은 같은 데이터를 두 형식으로 담고 있습니다. panel.html 을 더블클릭하면 브라우저 보안 규칙상 압축 파일을 직접 읽을 수 없어 panel_js(스크립트 형식)를 쓰고, '폴더 열기'로 고르면 panel(압축 형식)을 씁니다. parquet 는 패널과 별개로 Python 등에서 전체를 분석할 때 쓰는 표준 열 형식 파일입니다.");
}

// ================= 4. 화면 구성
pres.addSection({ title: "탐색" });
{
  const s = content("화면 구성", "화면은 왼쪽 목록, 위쪽 탭, 가운데 분석 영역으로 나뉩니다", "탐색");
  const b = shot(s, "01_main.png", 0.6, 1.5, 7.9, 5.3, "패널 첫 화면");
  const pts = [[0.30, 0.04], [0.785, 0.04], [0.105, 0.10], [0.33, 0.115], [0.64, 0.17], [0.765, 0.30], [0.475, 0.37], [0.70, 0.60]];
  pts.forEach(([fx, fy], i) => badge(s, i + 1, b.x + fx * b.w - 0.15, b.y + fy * b.h - 0.15, 0.3, C.accent4));
  const items = [
    ["적용 라이브러리", "연결된 라이브러리 연도 (예: 2005~2025)"],
    ["데이터 열기", "taas_library 폴더 / 파일로 열기"],
    ["장표 목록·검색", "« 로 숨기기 · 경계선 드래그로 너비 조절"],
    ["탭", "탐색 · 상관분석(담긴 계열 수) · 차량기술 매핑"],
    ["장표 제목·주석", "TAAS 메뉴 경로와 ‘주)’ 설명"],
    ["조건 바", "수치항목·연도·축·차트·값 변환·분석 실행"],
    ["축 필터", "어떤 값들을 그릴지 고름"],
    ["차트와 표", "아래로 내리면 표·복사·상관 추가 버튼"],
  ];
  items.forEach(([t, d], i) => {
    const y = 1.55 + i * 0.66;
    badge(s, i + 1, 8.85, y + 0.04, 0.3, C.accent4);
    tx(s, t, { x: 9.3, y, w: 3.4, h: 0.3, fontSize: 13, bold: true, color: C.text2 });
    tx(s, d, { x: 9.3, y: y + 0.3, w: 3.45, h: 0.3, fontSize: 11, color: HX.mute });
  });
  s.addNotes("숫자는 이 매뉴얼에서 계속 같은 의미로 씁니다. 장표를 바꾸면 5~8번 영역이 그 장표의 축 구성에 맞게 다시 만들어집니다.");
}

// ================= 5. 장표 고르기 + 조건 바
{
  const s = content("탐색 ① 장표와 조건", "장표를 고르고 조건 바에서 무엇을 어떻게 볼지 정합니다", "탐색");
  shot(s, "03_search.png", 0.6, 1.5, 2.75, 4.35, "장표 검색 결과");
  tx(s, "검색창에 ‘음주’를 넣으면 이름에 음주가 들어간 장표만 남습니다. 목록에서 누르면 그 장표가 열립니다.", { x: 0.6, y: 5.95, w: 2.85, h: 0.9, fontSize: 11, color: HX.mute });
  shot(s, "02_controls.png", 3.75, 1.5, 8.95, 2.55, "조건 바");
  const rows = [
    ["수치항목", "사고[건]·사망[명]·부상[명]·중상·경상·부상신고 중 하나"],
    ["연도", "시작~끝 연도. 장표마다 값이 있는 연도가 다를 수 있음"],
    ["가로축", "차트 x축에 펼칠 축 (연도 또는 시도·사고유형 등)"],
    ["계열(색)", "선·막대를 색으로 나눌 축. ‘없음’이면 한 줄"],
    ["차트", "자동(연도는 선, 그 외 막대) · 선 · 막대"],
    ["값 변환", "원값 · 계열 내 비중(%) · 첫 연도=100 · 전년 대비(%)"],
    ["분석 실행", "‘자동 적용’이 켜져 있으면 바꾸는 즉시 반영. 끄면 여러 조건을 바꾼 뒤 이 버튼으로 한 번에 적용(노란색 = 반영 대기)"],
  ];
  const tbl = rows.map(([a, b]) => [{ text: a, options: { bold: true, color: C.text2, fill: { color: C.background2 } } }, { text: b }]);
  s.addTable(tbl, { x: 3.75, y: 4.2, w: 8.95, colW: [1.6, 7.35], fontSize: 11.5, fontFace: FONT, color: C.text1, border: { type: "solid", pt: 0.5, color: HX.line }, rowH: [0.34, 0.34, 0.34, 0.34, 0.34, 0.34, 0.56], valign: "middle", margin: [0, 0.12, 0, 0.12] });
  s.addNotes("조건을 바꾸면 차트와 표가 즉시 다시 그려집니다. 장표에 축이 1개뿐이거나 수치항목이 1개뿐이면 해당 선택지도 하나만 보입니다.");
}

// ================= 6. 축 필터
{
  const s = content("탐색 ② 축 필터", "축 필터로 차트에 올릴 값을 고릅니다", "탐색");
  shot(s, "05_xaxis.png", 0.6, 1.5, 6.3, 5.3, "가로축을 사고유형 대분류로 바꾼 예");
  const items = [
    ["칩 필터 — 가로축·계열로 고른 축", "눌러서 켜고 끕니다. 파란 칩이 그려지는 값입니다. ‘전체’·‘해제’로 한 번에 바꿉니다. ‘합계’ 칩(점선)은 나머지 값을 더한 값이라 기본으로 꺼 둡니다."],
    ["드롭다운 — 나머지 축", "차트에 펼치지 않는 축은 한 값으로 고정합니다. 기본은 ‘합계’라서 전체 값을 보여줍니다. 특정 값(예: 서울)으로 바꾸면 그 조건의 값만 그립니다."],
    ["(모두 · 가로축에 표시)", "사고유형 대분류 > 중분류 > 사고유형처럼 계층이 있는 축은 하위 축에 합계가 없을 수 있습니다. 이때 이 항목이 기본으로 잡혀 하위 값들이 가로축에 함께 표시됩니다."],
  ];
  items.forEach(([t, d], i) => {
    const y = 1.55 + i * 1.62;
    card(s, 7.3, y, 5.4, 1.45);
    tx(s, t, { x: 7.5, y: y + 0.14, w: 5.0, h: 0.35, fontSize: 14, bold: true, color: C.text2 });
    tx(s, d, { x: 7.5, y: y + 0.52, w: 5.0, h: 0.85, fontSize: 11.5 });
  });
  s.addNotes("화면 예시는 가로축을 사고유형 대분류, 계열을 연도, 연도를 2021~2025로 바꾼 모습입니다. 대분류별로 다섯 해의 막대가 나란히 그려집니다.");
}

// ================= 7. 값 변환과 표
{
  const s = content("탐색 ③ 값 변환과 표", "값 변환으로 규모가 다른 계열도 비교할 수 있습니다", "탐색");
  const modes = [
    ["원값", "TAAS 값 그대로", "건수·인원 자체"],
    ["계열 내 비중(%)", "값 ÷ 같은 가로축 값의 계열 합 × 100", "구성비 변화 (예: 차대사람 비중)"],
    ["첫 연도 = 100", "값 ÷ 시작 연도 값 × 100", "규모가 다른 계열의 증감 속도"],
    ["전년 대비(%)", "(올해 − 전년) ÷ 전년 × 100", "해마다의 증감률"],
  ];
  modes.forEach(([t, f, u], i) => {
    const x = 0.6 + i * 3.08;
    card(s, x, 1.55, 2.9, 1.75, C.background1);
    tx(s, t, { x: x + 0.18, y: 1.68, w: 2.6, h: 0.36, fontSize: 15, bold: true, color: C.accent1 });
    tx(s, f, { x: x + 0.18, y: 2.08, w: 2.6, h: 0.62, fontSize: 11.5, color: C.text1 });
    tx(s, u, { x: x + 0.18, y: 2.75, w: 2.6, h: 0.45, fontSize: 11, color: HX.mute, italic: true });
  });
  shot(s, "04_share.png", 0.6, 3.55, 6.3, 3.25, "계열 내 비중으로 본 사고유형 대분류");
  tx(s, "표 아래 두 버튼", { x: 7.3, y: 3.55, w: 5.4, h: 0.36, fontSize: 15, bold: true, color: C.text2 });
  const btns = [
    ["표 복사 (탭 구분)", "지금 표를 클립보드에 복사합니다. 엑셀에 그대로 붙여 넣을 수 있습니다."],
    ["현재 계열을 상관분석에 추가", "차트에 보이는 계열(조건 포함)을 상관분석 목록에 넣습니다. 상관분석 탭 옆 숫자가 하나 늘어납니다."],
  ];
  btns.forEach(([t, d], i) => {
    const y = 4.05 + i * 1.35;
    badge(s, i + 1, 7.3, y + 0.02, 0.36);
    tx(s, t, { x: 7.8, y, w: 4.9, h: 0.34, fontSize: 13.5, bold: true });
    tx(s, d, { x: 7.8, y: y + 0.38, w: 4.9, h: 0.8, fontSize: 12, color: HX.mute });
  });
  s.addNotes("왼쪽 아래 화면은 사고유형 대분류를 '계열 내 비중'으로 바꾼 모습입니다. 표에도 같은 변환이 적용되므로 복사하면 변환된 값이 붙여 넣어집니다.");
}


// ================= 7-2. 그래프 조작
{
  const s = content("탐색 ④ 그래프 조작", "그래프를 눌러 기준선을 놓고 두 시점의 차이를 바로 계산합니다", "탐색");
  shot(s, "09_cursor.png", 0.6, 1.5, 7.6, 3.97, "기준선 M1·M2와 메모를 놓은 그래프");
  tx(s, "표 아래에 계열별 M1·M2 값, 차이(M2−M1), 변화율이 자동으로 나옵니다.", { x: 0.6, y: 5.6, w: 7.6, h: 0.35, fontSize: 11, color: HX.mute });
  const ops = [
    ["클릭", "기준선 M1 — 가장 가까운 점에 형광 노란 선"],
    ["Ctrl + 클릭", "비교선 M2 — 계열별 차이·변화율 계산"],
    ["드래그", "그 구간만 확대 (세로축도 자동 맞춤)"],
    ["Ctrl + 휠", "마우스 위치를 중심으로 확대·축소"],
    ["더블클릭", "그 자리에 메모 (PNG 저장에 포함)"],
    ["Ctrl + 우클릭", "전체 보기로 되돌리기"],
    ["Esc · 범례 클릭", "기준선 지우기 · 계열 숨기기/보이기"],
  ];
  const tbl = ops.map(([a, b]) => [{ text: a, options: { bold: true, color: C.text2, fill: { color: C.background2 } } }, { text: b }]);
  s.addTable(tbl, { x: 8.5, y: 1.5, w: 4.2, colW: [1.45, 2.75], fontSize: 11.5, fontFace: FONT, color: C.text1, border: { type: "solid", pt: 0.5, color: HX.line }, rowH: 0.55, valign: "middle", margin: [0, 0.1, 0, 0.1] });
  card(s, 8.5, 5.55, 4.2, 1.2, C.background1);
  tx(s, [{ text: "버튼  ", options: { bold: true, color: C.text2 } }, { text: "전체 보기 · 기준선·메모 지우기 · PNG 저장(제목·메모 포함). 상관분석의 산점도도 같은 방식으로 조작합니다." }],
    { x: 8.7, y: 5.62, w: 3.85, h: 1.06, fontSize: 11.5, valign: "middle" });
  s.addNotes("CAN 데이터 분석 도구의 plot 조작 방식을 그대로 옮겼습니다. 기준선은 장표의 조건을 바꿔도 같은 가로축 값(예: 2012년)이 있으면 유지되어, 수치항목을 바꿔 가며 같은 두 시점을 비교할 수 있습니다.");
}

// ================= 8. 상관분석 설정
pres.addSection({ title: "상관분석" });
{
  const s = content("상관분석 ① 계열 모으기와 설정", "탐색에서 계열을 보내고 계산 방법을 고릅니다", "상관분석");
  const steps = ["탐색에서 장표·조건을 맞춤", "‘현재 계열을 상관분석에 추가’", "다른 장표로 반복 (2개 이상)", "상관분석 탭에서 설정 선택"];
  steps.forEach((t, i) => {
    const x = 0.6 + i * 3.08;
    card(s, x, 1.55, 2.85, 0.75, C.background1);
    badge(s, i + 1, x + 0.15, 1.75, 0.36, C.accent2);
    tx(s, t, { x: x + 0.62, y: 1.55, w: 2.15, h: 0.75, fontSize: 12.5, bold: true, valign: "middle" });
    if (i < 3) s.addShape(pres.shapes.CHEVRON, { x: x + 2.89, y: 1.79, w: 0.15, h: 0.27, fill: { color: HX.gray }, line: { color: HX.gray } });
  });
  shot(s, "08_corr_c.png", 0.6, 2.6, 6.6, 4.2, "상관분석 탭");
  const rows = [
    ["방법", "피어슨 r : 직선 관계의 강도\n스피어만 ρ : 순위 기준, 이상값에 덜 민감"],
    ["시계열 처리", "원값 · 1차 차분(기본, 해마다 증감끼리 비교) · 증감률(%)"],
    ["시차", "B 계열을 n년 뒤로 밀어 비교 (예: 정책 1년 뒤 효과)"],
    ["맞춤 축", "연도끼리, 또는 시도처럼 같은 축 값끼리 짝지음"],
    ["계열 목록", "체크를 풀면 계산에서 빠짐 · 삭제 · 모두 지우기"],
  ];
  const tbl = rows.map(([a, b]) => [{ text: a, options: { bold: true, color: C.text2, fill: { color: C.background2 } } }, { text: b }]);
  s.addTable(tbl, { x: 7.5, y: 2.6, w: 5.2, colW: [1.35, 3.85], fontSize: 11.5, fontFace: FONT, color: C.text1, border: { type: "solid", pt: 0.5, color: HX.line }, rowH: [0.85, 0.75, 0.75, 0.75, 0.75], valign: "middle", margin: [0.04, 0.1, 0.04, 0.1] });
  s.addNotes("계열 옆 '연도·21' 같은 표시는 맞춤 축과 점 개수입니다. 점 개수가 다른 계열끼리는 겹치는 값만 써서 계산합니다. 차량기술 매핑 카드의 '추가' 버튼으로도 계열을 넣을 수 있습니다.");
}

// ================= 9. 결과 읽기
{
  const s = content("상관분석 ② 결과 읽는 법", "숫자 하나보다 차분·p값·산점도를 함께 봅니다", "상관분석");
  // 색 막대 (발산형)
  tx(s, "상관행렬 색", { x: 0.6, y: 1.55, w: 5.6, h: 0.35, fontSize: 15, bold: true, color: C.text2 });
  const cols = ["2A78D6", "8DB4E8", "F0EFEC", "F0A3A2", "E34948"];
  cols.forEach((c, i) => s.addShape(pres.shapes.RECTANGLE, { x: 0.6 + i * 1.12, y: 2.0, w: 1.12, h: 0.42, fill: { color: c }, line: { color: c } }));
  ["−1", "−0.5", "0", "+0.5", "+1"].forEach((t, i) => tx(s, t, { x: 0.6 + i * 1.12, y: 2.47, w: 1.12, h: 0.3, fontSize: 11, align: "center", color: HX.mute }));
  tx(s, "파랑은 반대로, 빨강은 같이 움직임. 진할수록 강함. 칸을 누르면 아래 산점도가 그 두 계열로 바뀝니다.", { x: 0.6, y: 2.85, w: 5.6, h: 0.65, fontSize: 12 });
  const reads = [
    ["r / ρ", "−1~+1. 절댓값 0.7 이상이면 강한 편, 0.3 미만이면 약한 편"],
    ["점 개수", "계산에 쓰인 짝의 수. 연도 시계열은 최대 21개 (1차 차분은 20개)"],
    ["p값", "0.05 미만이면 우연일 가능성이 낮음. 점이 적으면 r이 커도 p가 큼"],
  ];
  reads.forEach(([a, b], i) => {
    const y = 3.75 + i * 0.95;
    card(s, 0.6, y, 5.6, 0.8, C.background1);
    tx(s, a, { x: 0.8, y, w: 1.3, h: 0.8, fontSize: 15, bold: true, color: C.accent1, valign: "middle" });
    tx(s, b, { x: 2.1, y, w: 3.95, h: 0.8, fontSize: 11.5, valign: "middle" });
  });
  tx(s, "꼭 알아둘 점", { x: 6.8, y: 1.55, w: 5.9, h: 0.35, fontSize: 15, bold: true, color: C.text2 });
  const warns = [
    ["추세 공유", "대부분의 사고 지표가 2005년 이후 함께 줄어 원값끼리는 상관이 높게 나옵니다. 기본값인 ‘1차 차분’으로 해마다의 증감을 비교하세요."],
    ["상관은 인과가 아님", "같이 움직여도 원인은 제3의 요인(경기·인구·제도)일 수 있습니다. TAAS 경찰DB에는 차량의 기술 장착 여부가 없습니다."],
    ["분류가 바뀐 연도", "일부 항목은 특정 연도부터만 집계됩니다(예: 과속 2021년~, 사고유형 ‘추돌’은 11개 연도). 계열의 점 개수를 확인하세요."],
  ];
  warns.forEach(([t, d], i) => {
    const y = 2.0 + i * 1.6;
    card(s, 6.8, y, 5.9, 1.45, "FFF6DB");
    tx(s, t, { x: 7.0, y: y + 0.14, w: 5.5, h: 0.35, fontSize: 14, bold: true, color: C.text2 });
    tx(s, d, { x: 7.0, y: y + 0.52, w: 5.5, h: 0.85, fontSize: 11.5 });
  });
  s.addNotes("예시 화면의 추돌·음주·노면 세 계열은 1차 차분 기준 상관이 0.19, −0.01 수준으로 약합니다. 원값으로 바꾸면 모두 감소 추세라 상관이 크게 나오는데, 이것이 차분을 기본값으로 둔 이유입니다.");
}

// ================= 9-1. 체크해서 모아 보기 + 인구 통계
{
  const s = content("상관관계 분석 ③ 체크해서 모아 보기", "왼쪽 목록에서 여러 통계를 체크 → ‘상관관계 분석’ 한 번에", "상관분석");
  const steps = ["목록에서 통계 체크 (인구 포함)", "‘상관관계 분석’ 버튼", "조건 바꾸기 · 계열로 나누기", "추세 비교 · 상관행렬 · 산점도"];
  steps.forEach((t, i) => {
    const x = 0.6 + i * 3.08;
    card(s, x, 1.55, 2.85, 0.75, C.background1);
    badge(s, i + 1, x + 0.15, 1.75, 0.36, C.accent2);
    tx(s, t, { x: x + 0.62, y: 1.55, w: 2.15, h: 0.75, fontSize: 12.5, bold: true, valign: "middle" });
    if (i < 3) s.addShape(pres.shapes.CHEVRON, { x: x + 2.89, y: 1.79, w: 0.15, h: 0.27, fill: { color: HX.gray }, line: { color: HX.gray } });
  });
  shot(s, "10_multi.png", 0.6, 2.6, 6.6, 4.2, "체크한 통계만 모은 상관관계 분석");
  const rows = [
    ["추세 비교", "단위가 다른 통계를 첫 연도=100 지수·표준화·원값으로 한 그래프에. 번호 = 상관행렬 번호"],
    ["조건 바꾸기", "장표마다 수치항목·축 값을 고르고, 한 축을 ‘계열로 나누기’로 값별 계열 생성"],
    ["비율 환산", "고른 계열(예: 어린이 인구)로 나눠 10만 명당 사고로 비교"],
    ["인구 통계", "통계청 인구총조사 — 전체·어린이(0~12세)·일반(13~64세)·노인(65세 이상)"],
    ["유의", "어린이는 5세 단위 자료로 추정(10~14세×3/5). 2006~09·2011~14년은 실측 없음(‘인구_연간보간’ 수치로 보완)"],
  ];
  const tbl = rows.map(([a, b]) => [{ text: a, options: { bold: true, color: C.text2, fill: { color: C.background2 } } }, { text: b }]);
  s.addTable(tbl, { x: 7.5, y: 2.6, w: 5.2, colW: [1.35, 3.85], fontSize: 11, fontFace: FONT, color: C.text1, border: { type: "solid", pt: 0.5, color: HX.line }, rowH: [0.85, 0.85, 0.7, 0.75, 1.0], valign: "middle", margin: [0.04, 0.1, 0.04, 0.1] });
  s.addNotes("체크 상태는 브라우저에 기억됩니다. '상관관계 분석'을 누르면 이전 목록을 비우고 체크한 통계만 다시 모읍니다. 인구 자료는 2005·2010년이 외국인 제외, 2015년부터 외국인 포함이라 2010→2015 사이 수준이 한 번 뜁니다. 연도 범위를 2015~2025로 두거나 구성비로 보세요.");
}

// ================= 9-2. 통계 기법 5종
pres.addSection({ title: "통계 기법" });
{
  const s = content("통계 기법 — 5가지 기법을 탭으로", "모은 연도 계열에 기법별로 적용하고, 결과는 같은 형식으로 담아 합칩니다", "통계 기법");
  shot(s, "11_stat.png", 0.6, 1.55, 6.3, 4.75, "통계 기법 탭 (중단 시계열)");
  const rows = [
    ["① 추세·변곡점", "Mann-Kendall 추세 검정 · Sen 기울기 · Pettitt 변곡점 — 꾸준히 늘거나 주는지, 언제 꺾였는지"],
    ["② 시차상관·그레인저", "교차상관(몇 년 앞서나) · 그레인저 F 검정(과거가 예측에 보탬이 되나). 기본 1차 차분"],
    ["③ 다중회귀", "여러 계열로 한 계열 설명 — 계수·p·표준화 β·VIF·더빈-왓슨, 추세항·연도 더미"],
    ["④ 주성분·군집", "공통 흐름(PC) 설명력·적재값, 1−r 거리 계층적 군집"],
    ["⑤ 중단 시계열", "도입 연도 T 전후 수준·기울기 변화와 반사실 추세 (AEBS 2017, 민식이법 2020, 5030 2021 등)"],
    ["결과 모음", "‘결과 담기’ → run_id·기법·기간·처리·대상·상대·항목·통계량·값·p값·n·비고 13열로 쌓여 CSV/JSON 저장"],
  ];
  const tbl = rows.map(([a, b]) => [{ text: a, options: { bold: true, color: C.text2, fill: { color: C.background2 } } }, { text: b }]);
  s.addTable(tbl, { x: 7.15, y: 1.55, w: 5.6, colW: [1.6, 4.0], fontSize: 10.5, fontFace: FONT, color: C.text1, border: { type: "solid", pt: 0.5, color: HX.line }, rowH: [0.75, 0.75, 0.75, 0.62, 0.75, 0.85], valign: "middle", margin: [0.04, 0.08, 0.04, 0.08] });
  tx(s, "연 단위 자료는 최대 21개 점입니다. p값과 함께 처리(차분·로그)와 n을 확인하고, 상관·선행 관계를 인과로 단정하지 마세요.", { x: 7.15, y: 6.1, w: 5.6, h: 0.5, fontSize: 10.5, color: HX.mute });
  s.addNotes("왼쪽 목록에서 통계를 체크하고 '통계 기법' 버튼을 누르면 체크한 통계만 모아 이 탭이 열립니다. 각 기법 탭의 '이 기법은?'을 펼치면 해석 방법이 나옵니다. 계산 값은 statsmodels·pymannkendall과 대조해 같음을 확인했습니다.");
}

// ================= 10. 차량기술 매핑
pres.addSection({ title: "차량기술 매핑" });
{
  const s = content("차량기술 매핑", "안전기술 12종을 해당 사고 장표에 바로 연결합니다", "차량기술 매핑");
  shot(s, "07_tech_c.png", 0.6, 1.5, 6.9, 4.7, "차량기술 매핑 탭");
  tx(s, "매핑은 기술의 작동 영역과 사고 분류를 대응시킨 가설입니다. 효과 추정이 아니라 대상 사고의 규모와 추이를 보는 출발점으로 쓰세요.", { x: 0.6, y: 6.3, w: 6.9, h: 0.6, fontSize: 11, color: HX.mute });
  tx(s, "카드 읽는 법", { x: 7.9, y: 1.5, w: 4.8, h: 0.35, fontSize: 15, bold: true, color: C.text2 });
  const parts = [["기술 이름", "예) 자동긴급제동 (AEB, 차량)"], ["관련 규정·평가", "UN R152 · Euro NCAP 등"], ["대상 사고", "기술이 막으려는 사고 유형"], ["연결 장표·조건", "노란 표시줄: 장표 · 축=값"], ["분석 질문", "이 장표로 확인할 만한 물음"]];
  parts.forEach(([a, b], i) => {
    const y = 1.95 + i * 0.5;
    badge(s, i + 1, 7.9, y + 0.04, 0.3, C.accent3);
    tx(s, [{ text: a + "  ", options: { bold: true } }, { text: b, options: { color: HX.mute } }], { x: 8.32, y, w: 4.4, h: 0.4, fontSize: 12, valign: "middle" });
  });
  card(s, 7.9, 4.6, 4.8, 1.0, C.background1);
  tx(s, [{ text: "탐색 ", options: { bold: true, color: C.accent1 } }, { text: "장표를 열고 카드의 조건을 맞춘 채 탐색 탭으로 이동" }], { x: 8.1, y: 4.68, w: 4.45, h: 0.84, fontSize: 12, valign: "middle" });
  card(s, 7.9, 5.75, 4.8, 1.0, C.background1);
  tx(s, [{ text: "추가 ", options: { bold: true, color: C.accent1 } }, { text: "그 조건의 연도 시계열을 바로 상관분석 목록에 넣음" }], { x: 8.1, y: 5.83, w: 4.45, h: 0.84, fontSize: 12, valign: "middle" });
  s.addNotes("12종: AEB(차량), 보행자·자전거 AEB, 차로유지보조, 지능형 속도제한, 운전자 상태 모니터링, 음주운전 방지, ESC·노면 인지, 교차로 충돌 방지·V2X, 야간 시인성, 고령 운전자 지원, 어린이 보호구역 대응, 이륜차·개인형 이동장치 감지. 라이브러리에 연결 장표의 데이터가 없으면 버튼이 꺼집니다.");
}

// ================= 11. 활용 예
{
  const s = content("활용 예", "예시: AEB가 겨냥하는 추돌 사고를 5단계로 살펴보기", "차량기술 매핑");
  const flow = [
    ["카드에서 시작", "차량기술 매핑 › ‘자동긴급제동 (AEB, 차량)’ › 탐색"],
    ["추이 확인", "사고유형별 교통사고 · 사고유형=추돌 · 연도 추이(선)"],
    ["비중 비교", "값 변환 ‘계열 내 비중(%)’ · 계열=사고유형 → 추돌 비중 변화"],
    ["비교 계열 추가", "같은 장표의 다른 유형(측면충돌 등)과 전체를 ‘상관분석에 추가’"],
    ["관계 점검", "상관분석 · 1차 차분 · p값 확인 → 표 복사로 보고서에 정리"],
  ];
  flow.forEach(([t, d], i) => {
    const x = 0.6 + i * 2.46;
    card(s, x, 1.7, 2.25, 3.0, i % 2 ? C.background2 : C.background1);
    badge(s, i + 1, x + 0.2, 1.9, 0.5, C.accent1);
    tx(s, t, { x: x + 0.2, y: 2.6, w: 1.9, h: 0.45, fontSize: 15, bold: true, color: C.text2 });
    tx(s, d, { x: x + 0.2, y: 3.1, w: 1.9, h: 1.5, fontSize: 13 });
  });
  card(s, 0.6, 5.0, 12.1, 1.5, "EAF4FB");
  tx(s, [{ text: "볼 때의 기준  ", options: { bold: true, color: C.text2 } },
    { text: "추돌 사고가 AEB 보급 확대기(2016년 이후)에 다른 유형보다 빠르게 줄었는지, 그 차이가 1차 차분·p값에서도 유지되는지를 봅니다. 차이가 보여도 보급률 자료가 없으므로 ‘가능성’까지만 말할 수 있습니다." }],
    { x: 0.85, y: 5.1, w: 11.6, h: 1.3, fontSize: 14, valign: "middle" });
  s.addNotes("같은 순서로 음주운전 방지(음주운전 장표), ISA(과속 장표, 2021년~) 등 다른 카드도 분석할 수 있습니다.");
}

// ================= 12. 유의사항·FAQ
pres.addSection({ title: "참고" });
{
  const s = content("데이터 유의사항과 자주 묻는 질문", "값이 비어 보이거나 다를 때 먼저 확인할 것", "참고");
  const qa = [
    ["차트가 비어 있어요", "그 장표·연도에 TAAS 값이 없는 경우입니다. 과속 장표는 2021년, 마약·약물운전은 2024년부터 있습니다. 7079·7165 두 장표는 TAAS 서버 오류로 값이 없습니다. 상세는 TAAS_수집현황 엑셀 참고."],
    ["7120은 2년치만 보여요", "‘시도 시군구별·일별’은 약 1,100만 칸이라 패널에는 2024~2025년만 실었습니다. 전체는 parquet/facts.parquet 를 taas.py 나 DuckDB로 읽으세요."],
    ["‘창원시 (2)’가 뭔가요", "2010년 통합 전·후 창원시처럼 이름은 같지만 다른 행을 구분하려고 붙인 표시입니다."],
    ["‘라이브러리 폴더 열기’는 어느 폴더?", "raw 가 아니라 taas_library 폴더(index.json·panel 이 있는 폴더)를 고릅니다. 상단에 ‘적용 라이브러리 2005~2025’처럼 연도가 표시됩니다."],
    ["2026년 통계가 나오면", "수집기로 2026년만 받은 뒤 update_library.py 로 기존 라이브러리에 합치고 panel.html 을 다시 엽니다."],
    ["Python 으로 쓰려면", "import taas → lib = taas.Library('taas_library') → lib.table(7019), lib.series(…), lib.corr(…)"],
  ];
  qa.forEach(([q, a], i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = 0.6 + col * 6.15, y = 1.55 + row * 1.75;
    card(s, x, y, 5.95, 1.6, C.background1);
    s.addShape(pres.shapes.OVAL, { x: x + 0.2, y: y + 0.2, w: 0.38, h: 0.38, fill: { color: C.accent2 }, line: { color: C.accent2 } });
    tx(s, "Q", { x: x + 0.2, y: y + 0.2, w: 0.38, h: 0.38, fontSize: 13, bold: true, color: C.background1, align: "center", valign: "middle" });
    tx(s, q, { x: x + 0.72, y: y + 0.2, w: 5.0, h: 0.38, fontSize: 14, bold: true, color: C.text2, valign: "middle" });
    tx(s, a, { x: x + 0.72, y: y + 0.66, w: 5.05, h: 0.88, fontSize: 11 });
  });
  s.addNotes("수집 범위·빈 구간·누락 항목의 전체 목록은 TAAS_수집현황_2005_2025.xlsx 에 장표별로 정리되어 있습니다.");
}

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("written", OUT);
})();
