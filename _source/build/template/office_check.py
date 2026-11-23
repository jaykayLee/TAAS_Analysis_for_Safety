# -*- coding: utf-8 -*-
"""Office 호환성 검사·보정(프로젝트 공통, 필수 게이트) — 생성한 .pptx·.docx·.xlsx가 Windows의 PowerPoint·Word·Excel에서 열리는지 사전 점검.
  python3 build/template/office_check.py [경로 또는 폴더 ...] [--no-fix] [-q] [--fonts]     (인자 없으면 번들 전체)
PowerPoint는 LibreOffice·python-pptx보다 엄격하다 — 미리보기가 정상이어도 PowerPoint는 '열 수 없음'/'복구' 대화상자를 띄울 수 있다.
이 검사가 FAIL이면 파일을 전달하지 않는다. 최종 확인은 Windows에서 install.bat 마지막 단계(02_Strategy/05_Dependencies/verify_office.ps1)가
실제 PowerPoint·Word·Excel로 열어 본다.

ID 규칙(ISO/IEC 29500 pml.xsd — 2026-11-23 스키마로 확인):
  sldId 256 ~ 2147483647 · sldMasterId·sldLayoutId 2147483648 이상(PowerPoint 자신도 2147483648부터 씀) · 마스터·레이아웃 ID 전체에서 중복 없음
  ※ 'sldMasterId를 800000 등으로 낮추라'는 안내는 스키마 위반이다 — 낮춘 파일은 되돌려 보정한다.
보정(--no-fix가 아니면):
  · 슬라이드·레이아웃·마스터 안 도형 ID(p:cNvPr) 중복 → 새 번호(pptxgenjs 쪽 번호 자리표시자 id 25 충돌 등)
  · 크기가 음수인 도형(<a:ext cx/cy < 0>) → 시작점을 옮기고 flipH/flipV로 정규화
  · 범위를 벗어난 마스터·레이아웃 ID → 2147483648부터 다시 매김
검사: ZIP 무결성 · [Content_Types].xml 형식 등록 · 모든 XML 파싱 · .rels 대상 존재 · ID 범위·중복 · 도형 ID 중복 · 음수 크기
      · 8자리 색상(투명도 혼입) · 음수 그림자 거리 · 라이브러리로 다시 열기(python-pptx·python-docx·openpyxl) · 사용 글꼴 목록(--fonts)"""
import sys, os, re, zipfile, posixpath, argparse
import xml.etree.ElementTree as ET
SLD_MIN, SLD_MAX = 256, 2147483647
ML_MIN, ML_MAX = 2147483648, 4294967295
HERE = os.path.dirname(os.path.abspath(__file__)); BUNDLE = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
SKIP = {".git", "_work", "__pycache__", "node_modules"}
SHAPE_PART = re.compile(r"ppt/(slides/slide|slideLayouts/slideLayout|slideMasters/slideMaster)\d+\.xml$")

def read(p):
    with zipfile.ZipFile(p) as z:
        bad = z.testzip()
        if bad: raise zipfile.BadZipFile(f"손상된 항목 {bad}")
        return [(i, z.read(i.filename)) for i in z.infolist()]

def write(p, items):
    tmp = p + ".__fix__"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for info, data in items:                     # 원래 순서 유지([Content_Types].xml 맨 앞)
            zi = zipfile.ZipInfo(info.filename, date_time=info.date_time); zi.compress_type = zipfile.ZIP_DEFLATED; zi.external_attr = info.external_attr
            z.writestr(zi, data)
    os.replace(tmp, p)

def _neg_ext(t, fixes, nm):
    """<a:xfrm [flipH] [flipV]><a:off x y/><a:ext cx cy/> 에서 cx·cy 음수 → 정규화."""
    def r(m):
        head, x, y, cx, cy, tail = m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5)), m.group(6)
        if cx >= 0 and cy >= 0: return m.group(0)
        fh = 'flipH="1"' in head; fv = 'flipV="1"' in head
        if cx < 0: x += cx; cx = -cx; fh = not fh
        if cy < 0: y += cy; cy = -cy; fv = not fv
        h = re.sub(r'\s+flip[HV]="[01]"', "", head)
        h = h[:-1] + (' flipH="1"' if fh else "") + (' flipV="1"' if fv else "") + ">"
        fixes.append(f"{posixpath.basename(nm)} 음수 크기 정규화")
        return f'{h}<a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/>{tail}'
    return re.sub(r'(<a:xfrm\b[^>]*>)<a:off x="(-?\d+)" y="(-?\d+)"/><a:ext cx="(-?\d+)" cy="(-?\d+)"/>()', r, t)

def fix_pptx(items):
    fixes = []; D = {i.filename: d for i, d in items}
    # 1) 마스터·레이아웃 ID 범위(스키마: 2147483648 이상) — 벗어나면 전부 다시 매김
    prs = D.get("ppt/presentation.xml", b"").decode("utf-8")
    masters = sorted(n for n in D if re.match(r"ppt/slideMasters/slideMaster\d+\.xml$", n))
    mids = [int(v) for v in re.findall(r'<p:sldMasterId\b[^>]*?\bid="(\d+)"', prs)]
    lids = [int(v) for n in masters for v in re.findall(r'<p:sldLayoutId\b[^>]*?\bid="(\d+)"', D[n].decode("utf-8"))]
    allids = mids + lids
    renum = any(not ML_MIN <= v <= ML_MAX for v in allids) or len(set(allids)) != len(allids) or (lids and mids and min(lids) <= max(mids))
    new = {}
    if renum:
        nxt = [ML_MIN]
        def take():
            v = nxt[0]; nxt[0] += 1; return v
        def rp(tag):
            def r(m):
                n = take(); fixes.append(f"{tag} {m.group(2)}→{n}"); return f'{m.group(1)}id="{n}"'
            return r
        new["ppt/presentation.xml"] = re.sub(r'(<p:sldMasterId\b[^>]*?\b)id="(\d+)"', rp("sldMasterId"), prs)
        for n in masters: new[n] = re.sub(r'(<p:sldLayoutId\b[^>]*?\b)id="(\d+)"', rp("sldLayoutId"), D[n].decode("utf-8"))
    out = []
    for info, data in items:
        n = info.filename
        t = new.get(n)
        if SHAPE_PART.match(n):
            t = t if t is not None else data.decode("utf-8"); t0 = t
            # 2) 도형 ID 중복
            seen = set(); top = max([int(x) for x in re.findall(r'<p:cNvPr\b[^>]*?\bid="(\d+)"', t)] or [1])
            def dd(m, nm=n):
                nonlocal top
                v = m.group(2)
                if v in seen: top += 1; fixes.append(f"{posixpath.basename(nm)} 도형 ID {v}→{top}"); return f'{m.group(1)}id="{top}"'
                seen.add(v); return m.group(0)
            t = re.sub(r'(<p:cNvPr\b[^>]*?\b)id="(\d+)"', dd, t)
            # 3) 음수 크기
            t = _neg_ext(t, fixes, n)
            if t == t0 and n not in new: t = None
        out.append((info, t.encode("utf-8") if t is not None else data))
    return out, fixes

def fonts_of(items):
    f = set()
    for i, d in items:
        if i.filename.endswith(".xml"):
            s = d.decode("utf-8", "replace")
            f |= set(re.findall(r'<a:(?:latin|ea|cs) typeface="([^"+@][^"]*)"', s))          # pptx·xlsx 도형(+mj-lt 등 테마 참조 제외)
            for rf in re.findall(r'<w:rFonts\b[^>]*>', s): f |= set(re.findall(r'w:(?:ascii|hAnsi|eastAsia|cs)="([^"]+)"', rf))   # docx(w:lang 제외)            f |= set(re.findall(r'<(?:x:)?name val="([^"]+)"', s)) if i.filename.startswith("xl/") else set()
    return sorted(x for x in f if x and not x.startswith("+"))

def check(p, items):
    F, names = [], {i.filename for i, _ in items}; D = {i.filename: d for i, d in items}
    ext = os.path.splitext(p)[1].lower()
    if "[Content_Types].xml" not in names: return ["[Content_Types].xml 없음"]
    ct = D["[Content_Types].xml"].decode("utf-8", "replace")
    defaults = {x.lower() for x in re.findall(r'<Default\b[^>]*?\bExtension=["\']([^"\']+)', ct, re.I)}
    overrides = set(re.findall(r'<Override\b[^>]*?\bPartName=["\']/([^"\']+)', ct))
    for n in names:
        if n.endswith("/") or n == "[Content_Types].xml": continue
        if n not in overrides and n.rsplit(".", 1)[-1].lower() not in defaults: F.append(f"형식 미등록 부품 {n}")
    for n, d in D.items():
        if n.endswith((".xml", ".rels")):
            try: ET.fromstring(d)
            except ET.ParseError as e: F.append(f"XML 오류 {n}: {e}")
    for n, d in D.items():
        if not n.endswith(".rels"): continue
        base = posixpath.dirname(posixpath.dirname(n))
        try: root = ET.fromstring(d)
        except ET.ParseError: continue
        for rel in root:
            t = rel.get("Target", ""); mode = rel.get("TargetMode", "")
            if not t or mode == "External" or t.startswith(("http:", "https:", "mailto:")): continue
            r = posixpath.normpath(t.lstrip("/") if t.startswith("/") else posixpath.join(base, t))
            if r not in names: F.append(f"끊어진 참조 {n} → {t}")
    if ext == ".pptx":
        prs = D.get("ppt/presentation.xml", b"").decode("utf-8", "replace")
        for v in re.findall(r'<p:sldId\b[^>]*?\bid="(\d+)"', prs):
            if not SLD_MIN <= int(v) <= SLD_MAX: F.append(f"sldId id={v} 범위 밖(256~2147483647)")
        mids = [int(v) for v in re.findall(r'<p:sldMasterId\b[^>]*?\bid="(\d+)"', prs)]
        lids = [int(v) for n, d in D.items() if re.match(r"ppt/slideMasters/slideMaster\d+\.xml$", n)
                for v in re.findall(r'<p:sldLayoutId\b[^>]*?\bid="(\d+)"', d.decode("utf-8", "replace"))]
        for v in mids + lids:
            if not ML_MIN <= v <= ML_MAX: F.append(f"마스터/레이아웃 id={v} 범위 밖(2147483648 이상이어야 함)")
        if len(set(mids + lids)) != len(mids + lids): F.append("마스터·레이아웃 ID 중복")
        if mids and lids and min(lids) <= max(mids): F.append("sldLayoutId가 sldMasterId보다 작거나 같음")
        for n, d in D.items():
            if not SHAPE_PART.match(n): continue
            s = d.decode("utf-8", "replace"); sp = re.findall(r'<p:cNvPr\b[^>]*?\bid="(\d+)"', s)
            if len(sp) != len(set(sp)): F.append(f"{n}: 도형 ID 중복")
            if re.search(r'<a:(?:ext|chExt) cx="-|<a:(?:ext|chExt) cx="\d+" cy="-', s): F.append(f"{n}: 음수 크기 도형(PowerPoint 열기 실패 원인)")
            if re.search(r'<a:srgbClr val="[0-9A-Fa-f]{8}"', s): F.append(f"{n}: 8자리 색상값(투명도 혼입)")
            if re.search(r'dist="-\d', s): F.append(f"{n}: 음수 그림자 거리")
    try:                                             # 라이브러리로 다시 열기
        if ext == ".pptx": import pptx; pptx.Presentation(p)
        elif ext == ".docx": import docx; docx.Document(p)
        elif ext == ".xlsx": import openpyxl; openpyxl.load_workbook(p)
    except ImportError: pass
    except Exception as e: F.append(f"다시 열기 실패: {type(e).__name__}: {str(e)[:120]}")
    return F

def collect(paths):
    files = []
    for a in paths or [BUNDLE]:
        if os.path.isdir(a):
            for r, ds, fs in os.walk(a):
                ds[:] = [d for d in ds if d not in SKIP]
                files += [os.path.join(r, f) for f in fs if f.lower().endswith((".pptx", ".docx", ".xlsx")) and not f.startswith("~$")]
        elif a.lower().endswith((".pptx", ".docx", ".xlsx")): files.append(a)
    return sorted(files)

def run(paths=None, fix=True, quiet=False, fonts=False):
    files = collect(paths); bad = fixed = 0; allf = {}
    for p in files:
        rel = os.path.relpath(p, BUNDLE)
        try:
            items = read(p)
            if fix and p.lower().endswith(".pptx"):
                items2, fx = fix_pptx(items)
                if fx:
                    write(p, items2); items = read(p); fixed += 1
                    print(f"[보정] {rel}: {len(fx)}건 — " + ", ".join(fx[:4]) + (" …" if len(fx) > 4 else ""))
            F = check(p, items)
            for f in fonts_of(items): allf.setdefault(f, []).append(os.path.basename(p))
        except Exception as e: F = [f"열기 실패: {type(e).__name__}: {e}"]
        if F: bad += 1; print(f"[FAIL] {rel}"); [print("       -", x) for x in F]
        elif not quiet: print(f"[ OK ] {rel}")
    if fonts: print("사용 글꼴:", " · ".join(f"{k}({len(v)})" for k, v in sorted(allf.items())))
    print(f"Office 검사: {len(files)}개 · 보정 {fixed} · 실패 {bad}")
    return 1 if bad else 0

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("paths", nargs="*"); ap.add_argument("--no-fix", action="store_true")
    ap.add_argument("-q", action="store_true"); ap.add_argument("--fonts", action="store_true"); a = ap.parse_args()
    sys.exit(run(a.paths, not a.no_fix, a.q, a.fonts))
