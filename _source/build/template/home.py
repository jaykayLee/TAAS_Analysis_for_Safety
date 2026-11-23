# -*- coding: utf-8 -*-
"""프로젝트 홈(첫 패널) 생성기 — project-structure 공통. 폴더·파일 지도(트리·목록)와 각 파일의 의미·마지막 업데이트 날짜를 보여 주고 메인 패널로 이어 준다.
  python3 build/template/home.py [--version v3.8]  → 01_Panel/Home/프로젝트_홈_<버전>.html (Main_<ID>.bat이 먼저 연다)
업데이트 날짜 = git에서 그 파일 내용이 마지막으로 바뀐 커밋 날짜(커밋 전 변경은 생성 시각, git이 없으면 파일 수정 시각).
파일 의미 = ① 프로젝트 content.py의 file_meanings()(있으면) ② 폴더 README 제목 ③ 코드 첫 설명줄(docstring·주석) ④ 이름·확장자 규칙."""
import os, sys, json, re, glob, subprocess, datetime, argparse, html
HERE = os.path.dirname(os.path.abspath(__file__)); BUILD = os.path.dirname(HERE); ROOT = os.path.dirname(BUILD); BUNDLE = os.path.dirname(ROOT)
sys.path.insert(0, HERE); import contract as K
SKIP_DIR = {".git", "__pycache__", "_work", "node_modules"}
KIND = {".html": "패널·웹", ".docx": "Word", ".xlsx": "Excel", ".pptx": "PowerPoint", ".pdf": "PDF", ".md": "Markdown", ".json": "JSON", ".jsonl": "JSON Lines", ".py": "Python",
        ".js": "JavaScript", ".sh": "셸 스크립트", ".bat": "배치(Windows)", ".txt": "텍스트", ".css": "스타일", ".sql": "SQL", ".sqlite": "SQLite DB", ".csv": "CSV", ".gz": "압축", ".docx#": ""}

def git_dates():
    """경로(번들 기준) → (마지막 커밋 날짜 ISO, 커밋 해시 앞 7자). 작업 중 변경은 별도 집합"""
    D, dirty = {}, set()
    try: out = subprocess.run(["git", "-c", "core.quotepath=off", "-C", BUNDLE, "log", "--format=@@%h %aI", "--name-only"], capture_output=True, text=True, check=True).stdout
    except Exception: return None, dirty
    cur = None
    for ln in out.splitlines():
        if ln.startswith("@@"): h, d = ln[2:].split(" ", 1); cur = (d[:16].replace("T", " "), h)
        elif ln.strip() and cur and ln not in D: D[ln] = cur
    try:
        st = subprocess.run(["git", "-c", "core.quotepath=off", "-C", BUNDLE, "status", "--porcelain", "-uall"], capture_output=True, text=True, check=True).stdout
        for ln in st.splitlines():
            p = ln[3:].split(" -> ")[-1].strip().strip('"'); dirty.add(p)
    except Exception: pass
    return D, dirty

def first_line(p):
    try:
        t = open(p, encoding="utf-8", errors="ignore").read(1500)
    except Exception: return ""
    ext = os.path.splitext(p)[1]
    if ext == ".py":
        m = re.search(r'"""\s*(.+?)(?:\n|""")', t, re.S) or re.search(r"^#\s*(?!-\*-)(.+)$", t, re.M)
        return (m.group(1).strip() if m else "")
    if ext in (".js", ".sh", ".css", ".sql"):
        for ln in t.splitlines()[:6]:
            ln = ln.strip()
            if ln.startswith(("//", "#", "/*", "--")) and not ln.startswith("#!"): return ln.lstrip("/#* -").strip()
        return ""
    if ext == ".md":
        m = re.search(r"^#\s+(.+)$", t, re.M); return m.group(1).strip() if m else ""
    if ext == ".json":
        for k in ("note", "title", "description", "name_ko", "purpose"):
            m = re.search(r'"%s"\s*:\s*"([^"]{4,200})"' % k, t)
            if m: return m.group(1)
    return ""

def rule_meaning(rel):
    b = os.path.basename(rel); e = os.path.splitext(b)[1].lower()
    if b == "README.md": return "폴더 안내 — 목적·넣는 것·넣지 않는 것"
    if b == ".keep": return ""
    if b.startswith("Main_") and e == ".bat": return "시작 파일 — 프로젝트 홈(이 화면) → 메인 패널"
    if b == "install.bat": return "의존성 설치 — 02_Strategy/05_Dependencies의 목록대로 도구·패키지 설치"
    if b == "PROJECT.json": return "프로젝트 신분증 — 이름·버전·폴더·라이브러리·패널 URL(LLM이 먼저 읽음)"
    if b == "STATUS.md": return "지금 상태 — 열린 요청·결정 묶음·작업 목록(빌드마다 다시 씀)"
    if b == "library.json": return "라이브러리 매니페스트 — 버전·파일·적재 테이블·의존·변경 이력"
    if b.startswith("REQ-"): return "사용자 요청 기록"
    if b.startswith("CB-"): return "패널 결정 묶음(customize/1.0)"
    return ""

def folder_meanings():
    M = {t["path"].rstrip("/"): t["role"] for t in K.top() if t["path"].endswith("/")}
    for p, d, _ in K.SUB:
        if "<" not in p: M[p.rstrip("/")] = d
    for c, n, d in K.CATS:
        M.setdefault(f"03_References/{c}", f"{n} — 원문 서지·링크 색인과 files/(허가 원문)"); M.setdefault(f"04_Libraries/{c}", f"{n} — 라이브러리")
        M.setdefault(f"03_References/{c}/files", "공개·허가된 원문 파일(REF-###_제목)")
    M.update({"05_UserComments/02_Decisions/inbox": "적용 대기 결정 묶음", "05_UserComments/02_Decisions/applied": "적용 완료 묶음(apply_result 포함)", "05_UserComments/02_Decisions/conflicts": "충돌·차단 묶음 — 패널에서 다시 확인",
              "_source/build": "생성기·검사·폴더 규칙(paths.py)", "_source/panel": "패널 원천(셸·모듈·출처 메모·피드)", "_source/ops": "자동 갱신 절차·스크립트", "_source/dist": "생성 중간물(md 원문·DB)", "_source/docs": "색인·패널 출처(md)",
              "_source/strategy": "전략 문서·README의 원천(content.py)"})
    return M

def scan(meanings):
    G, dirty = git_dates(); now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M"); F = []
    for r, ds, fs in os.walk(BUNDLE):
        ds[:] = sorted(d for d in ds if d not in SKIP_DIR and not d.startswith("."))
        for f in sorted(fs):
            if f.startswith(".") and f != ".keep": continue
            ap = os.path.join(r, f); rel = os.path.relpath(ap, BUNDLE).replace(os.sep, "/")
            if f == ".keep": continue
            if G is not None:
                if rel in dirty or rel not in G: d, h, st = now, "", "이번 빌드"
                else: (d, h), st = G[rel], ""
            else: d, h, st = datetime.datetime.fromtimestamp(os.path.getmtime(ap)).strftime("%Y-%m-%d %H:%M"), "", "파일 시각"
            m = meanings.get(rel) or rule_meaning(rel) or first_line(ap)
            F.append({"p": rel, "m": m[:220], "d": d, "h": h, "s": st, "z": os.path.getsize(ap), "k": KIND.get(os.path.splitext(f)[1].lower(), os.path.splitext(f)[1][1:].upper() or "파일")})
    return F

CSS = """:root{--bg:#eef1f5;--sf:#fff;--sf2:#f5f7fa;--bd:#d4dae2;--bd2:#e5e9ef;--fg:#1a2230;--dim:#5a6678;--faint:#8a94a6;--ac:#2563c9;--acs:#dbe6fb;--g:#4e9a3e;--gs:#e4f0e6;--new:#c04670;--nav:#17375e}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#0f141c;--sf:#171e29;--sf2:#1d2633;--bd:#2c3747;--bd2:#232d3b;--fg:#e5eaf2;--dim:#9aa7ba;--faint:#6b7789;--ac:#5a9bf5;--acs:#1c2c45;--g:#6fb37e;--gs:#1b2a20;--new:#e07399;--nav:#cadcfc;color-scheme:dark}}
:root[data-theme=dark]{--bg:#0f141c;--sf:#171e29;--sf2:#1d2633;--bd:#2c3747;--bd2:#232d3b;--fg:#e5eaf2;--dim:#9aa7ba;--faint:#6b7789;--ac:#5a9bf5;--acs:#1c2c45;--g:#6fb37e;--gs:#1b2a20;--new:#e07399;--nav:#cadcfc;color-scheme:dark}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.5 'Malgun Gothic','Apple SD Gothic Neo','Noto Sans KR',system-ui,sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:18px 16px 40px}h1{font-size:21px;margin:0}.sub{color:var(--dim);font-size:12.5px;margin:2px 0 14px}
.btns{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px}.btn{display:inline-flex;align-items:center;gap:6px;padding:10px 16px;border-radius:9px;text-decoration:none;font-weight:700;border:1px solid var(--ac);color:var(--ac);background:var(--sf)}
.btn.p{background:var(--ac);color:#fff}.btn small{font-weight:400;opacity:.85}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:10px;margin-bottom:16px}.card{background:var(--sf);border:1px solid var(--bd);border-radius:11px;padding:11px 13px;border-top:3px solid var(--g);cursor:pointer}
.card h3{margin:0;font-size:14px;color:var(--nav)}.card p{margin:4px 0 6px;font-size:12px;color:var(--dim);min-height:34px}.card .n{font-size:11.5px;color:var(--faint)}.card .n b{color:var(--fg)}
.bar{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:4px 0 10px}.tab{padding:7px 14px;border-radius:8px;border:1px solid var(--bd);background:var(--sf2);cursor:pointer;font:inherit;font-weight:600;color:var(--dim)}
.tab[aria-pressed=true]{background:var(--nav);color:var(--sf);border-color:var(--nav)}input,select{font:inherit;padding:7px 9px;border-radius:8px;border:1px solid var(--bd);background:var(--sf);color:var(--fg)}input{flex:1 1 220px;min-width:160px}
.panel{background:var(--sf);border:1px solid var(--bd);border-radius:12px;padding:8px 12px}
details{margin:1px 0}summary{cursor:pointer;padding:4px 4px;border-radius:6px;list-style:none;display:flex;gap:8px;align-items:baseline}summary::-webkit-details-marker{display:none}
summary:hover{background:var(--sf2)}summary .fn{font-weight:700;color:var(--nav)}summary .fm{color:var(--dim);font-size:12px;flex:1}summary .fc{font-size:11px;color:var(--faint);white-space:nowrap}
summary::before{content:'▸';color:var(--faint);font-size:11px;width:10px}details[open]>summary::before{content:'▾'}
.kids{margin-left:16px;border-left:1px dashed var(--bd2);padding-left:8px}
.fr{display:grid;grid-template-columns:minmax(180px,330px) 1fr 132px 70px;gap:10px;align-items:baseline;padding:3px 4px;border-radius:6px;font-size:12.5px}.fr:hover{background:var(--sf2)}
.fr a{color:var(--fg);text-decoration:none;word-break:break-all}.fr a:hover{color:var(--ac);text-decoration:underline}.fr .m{color:var(--dim);font-size:12px}.fr .d{font-family:Consolas,monospace;font-size:11.5px;color:var(--dim);white-space:nowrap}
.fr .z{font-size:11px;color:var(--faint);text-align:right}.new{color:var(--new)!important;font-weight:700}.tag{font-size:10px;border:1px solid var(--new);color:var(--new);border-radius:4px;padding:0 4px;margin-left:4px}
table{width:100%;border-collapse:collapse;font-size:12.5px}th{position:sticky;top:0;background:var(--sf2);text-align:left;font-size:11px;color:var(--dim);padding:7px 8px;border-bottom:1px solid var(--bd);cursor:pointer;white-space:nowrap}
td{padding:6px 8px;border-bottom:1px solid var(--bd2);vertical-align:top}td a{color:var(--fg)}td.p{word-break:break-all}td.d{font-family:Consolas,monospace;white-space:nowrap;font-size:11.5px}.cnt{font-size:12px;color:var(--faint);margin:6px 2px}
.recent{display:grid;gap:4px}.foot{margin-top:18px;font-size:11.5px;color:var(--faint)}
@media (max-width:720px){.fr{grid-template-columns:1fr;gap:0}.fr .z{text-align:left}}"""
JS = r"""
const D=JSON.parse(document.getElementById('data').textContent),F=D.files,FM=D.folders,$=s=>document.querySelector(s),esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const today=new Date(D.generated.slice(0,10)),isNew=d=>(today-new Date(d.slice(0,10)))/864e5<=D.recent_days,kb=z=>z<1024?z+' B':z<1048576?(z/1024).toFixed(1)+' KB':(z/1048576).toFixed(1)+' MB';
const href=p=>'../../'+p.split('/').map(encodeURIComponent).join('/');
function tree(){const root={c:{},f:[]};F.forEach(f=>{const parts=f.p.split('/');let n=root,path='';parts.slice(0,-1).forEach(x=>{path=path?path+'/'+x:x;n=n.c[x]=n.c[x]||{c:{},f:[],path};});n.f.push(f);});return root;}
function agg(n){let c=n.f.length,d='';n.f.forEach(f=>{if(f.d>d)d=f.d});Object.values(n.c).forEach(k=>{const a=agg(k);c+=a.c;if(a.d>d)d=a.d});n.n=c;n.d=d;return{c,d};}
const T=tree();agg(T);
function row(f){const nw=isNew(f.d);return `<div class="fr"><a href="${href(f.p)}" title="${esc(f.p)}">${esc(f.p.split('/').pop())}</a><span class="m">${esc(f.m||'—')}</span><span class="d ${nw?'new':''}" title="${esc(f.h?'커밋 '+f.h:f.s)}">${esc(f.d)}${f.s?'<span class="tag">'+esc(f.s)+'</span>':''}</span><span class="z">${kb(f.z)}</span></div>`;}
function node(name,n,depth){const open=depth<1&&!/^_source/.test(n.path)||(depth<2&&/^0[1-5]_/.test(n.path)&&!/^04_Libraries\/.+\//.test(n.path)),q=$('#q').value.trim().toLowerCase();
 return `<details ${open||q?'open':''}><summary><span class="fn">📁 ${esc(name)}</span><span class="fm">${esc(FM[n.path]||'')}</span><span class="fc">${n.n}개 · 최근 <b class="${isNew(n.d)?'new':''}">${esc(n.d.slice(0,10))}</b></span></summary><div class="kids">${
  Object.keys(n.c).sort().map(k=>node(k,n.c[k],depth+1)).join('')}${n.f.map(row).join('')}</div></details>`;}
function filt(){const q=$('#q').value.trim().toLowerCase(),top=$('#top').value,rec=$('#rec').checked;return F.filter(f=>(!top||f.p.startsWith(top+'/')||f.p===top)&&(!rec||isNew(f.d))&&(!q||(f.p+' '+f.m).toLowerCase().includes(q)));}
let mode='tree',sortK='p',sortD=1;
function render(){const L=filt();$('#cnt').textContent=`파일 ${L.length} / ${F.length} · 최근 ${D.recent_days}일 내 변경 ${F.filter(f=>isNew(f.d)).length} · 날짜 = 내용이 마지막으로 바뀐 커밋 날짜(‘이번 빌드’ = 이번에 바뀐 파일, 생성 시각)`;
 if(mode==='tree'){const keep=new Set(L.map(f=>f.p));const t={c:{},f:[]};F.filter(f=>keep.has(f.p)).forEach(f=>{const parts=f.p.split('/');let n=t,path='';parts.slice(0,-1).forEach(x=>{path=path?path+'/'+x:x;n=n.c[x]=n.c[x]||{c:{},f:[],path};});n.f.push(f);});agg(t);
  $('#view').innerHTML=t.f.map(row).join('')+Object.keys(t.c).sort().map(k=>node(k,t.c[k],0)).join('');}
 else{const S=L.slice().sort((a,b)=>(a[sortK]>b[sortK]?1:a[sortK]<b[sortK]?-1:0)*sortD);
  $('#view').innerHTML=`<table><thead><tr>${[['p','경로'],['m','의미'],['k','종류'],['d','업데이트'],['z','크기']].map(([k,t])=>`<th data-k="${k}">${t}${sortK===k?(sortD>0?' ▲':' ▼'):''}</th>`).join('')}</tr></thead><tbody>${S.map(f=>`<tr><td class="p"><a href="${href(f.p)}">${esc(f.p)}</a></td><td>${esc(f.m||'—')}</td><td>${esc(f.k)}</td><td class="d ${isNew(f.d)?'new':''}">${esc(f.d)}${f.s?'<span class="tag">'+esc(f.s)+'</span>':''}</td><td>${kb(f.z)}</td></tr>`).join('')}</tbody></table>`;
  document.querySelectorAll('th').forEach(th=>th.onclick=()=>{const k=th.dataset.k;sortD=sortK===k?-sortD:(k==='d'?-1:1);sortK=k;render();});}}
document.querySelectorAll('.tab').forEach(b=>b.onclick=()=>{mode=b.dataset.m;document.querySelectorAll('.tab').forEach(x=>x.setAttribute('aria-pressed',x===b));render();});
['#q','#top','#rec'].forEach(s=>$(s).addEventListener('input',render));
document.querySelectorAll('.card').forEach(c=>c.onclick=()=>{$('#top').value=c.dataset.p;render();$('#view').scrollIntoView({behavior:'smooth'});});
$('#recent').innerHTML=F.slice().sort((a,b)=>a.d<b.d?1:-1).filter(f=>!/^_source\//.test(f.p)).slice(0,12).map(row).join('');
render();
"""

def build(version=None, meanings=None):
    pj = json.load(open(os.path.join(BUNDLE, "PROJECT.json"), encoding="utf-8")); V = version or pj.get("version", "")
    files = scan(meanings or {}); FM = folder_meanings()
    tops = [t for t in K.top(pj["id"]) if t["path"].endswith("/")] ; tops = [t for t in tops if t["path"] != "_source/"] + [t for t in tops if t["path"] == "_source/"]
    def stat(p): L = [f for f in files if f["p"].startswith(p)]; return len(L), max([f["d"] for f in L] or [""])
    cards = "".join(f'<div class="card" data-p="{html.escape(t["path"].rstrip("/"))}"><h3>{html.escape(t["path"])}</h3><p>{html.escape(t["role"])}</p><div class="n"><b>{stat(t["path"])[0]}</b>개 · 최근 <b>{html.escape(stat(t["path"])[1][:10])}</b></div></div>' for t in tops)
    main_off = sorted(glob.glob(os.path.join(BUNDLE, "01_Panel", "Main", "*_offline.html")))
    main_on = [p for p in sorted(glob.glob(os.path.join(BUNDLE, "01_Panel", "Main", "*.html"))) if not p.endswith("_offline.html")]
    rel = lambda p: "../Main/" + os.path.basename(p)
    btn = ""
    if main_off: btn += f'<a class="btn p" href="{html.escape(rel(main_off[-1]))}">▶ 메인 패널 열기 <small>(오프라인·글꼴 내장)</small></a>'
    if pj.get("panel_url"): btn += f'<a class="btn" href="{html.escape(pj["panel_url"])}" target="_blank" rel="noopener">게시 패널 <small>(온라인 · 지금 갱신·융합 검토 저장)</small></a>'
    elif main_on: btn += f'<a class="btn" href="{html.escape(rel(main_on[-1]))}">메인 패널(온라인판)</a>'
    for label, pat in (("문서관리 색인", "02_Strategy/00_History/문서관리_색인_*.xlsx"), ("변경 이력", "02_Strategy/00_History/프로젝트_변경이력_*.xlsx"), ("구조 규약", "02_Strategy/03_User/프로젝트구조_규약_*.pptx"), ("의존성 목록", "02_Strategy/05_Dependencies/의존성_목록_*.docx"), ("지금 상태", "05_UserComments/STATUS.md")):
        h = sorted(glob.glob(os.path.join(BUNDLE, pat)))
        if h: btn += f'<a class="btn" href="../../{html.escape(os.path.relpath(h[-1], BUNDLE).replace(os.sep, "/"))}">{label}</a>'
    data = {"generated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "recent_days": 7, "files": files, "folders": FM}
    opts = "".join(f'<option value="{html.escape(t["path"].rstrip("/"))}">{html.escape(t["path"])}</option>' for t in tops)
    H = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>프로젝트 홈 — {html.escape(pj['name'])}</title><style>{CSS}</style></head><body><div class="wrap">
<h1>{html.escape(pj['name'])} <span style="color:var(--faint);font-weight:400">— {html.escape(V)}</span></h1>
<p class="sub">프로젝트 홈(첫 패널) · 구조 {html.escape(pj.get('structure', {}).get('contract', ''))} · 생성 {data['generated']} · 원천 <code>_source/build/template/home.py</code> — 폴더를 고르면 아래 지도가 그 폴더만 보여 줍니다. 처음 빌드하려면 최상위 <b>install.bat</b>.</p>
<div class="btns">{btn}</div><div class="cards">{cards}</div>
<div class="panel" style="margin-bottom:14px"><div class="cnt" style="margin-top:2px"><b>최근 업데이트</b>(코드 제외 12개)</div><div class="recent" id="recent"></div></div>
<div class="bar"><button class="tab" data-m="tree" aria-pressed="true">트리</button><button class="tab" data-m="list" aria-pressed="false">목록</button>
<select id="top" aria-label="폴더"><option value="">전체 폴더</option>{opts}</select><input id="q" type="search" placeholder="파일 이름·의미 검색"><label style="font-size:12.5px;color:var(--dim)"><input id="rec" type="checkbox" style="flex:none;min-width:0"> 최근 7일 변경만</label></div>
<div class="cnt" id="cnt"></div><div class="panel" id="view"></div>
<p class="foot">이 화면은 빌드할 때 다시 만들어집니다(직접 수정 금지). 파일을 누르면 열립니다 — Word·Excel·PowerPoint는 브라우저 설정에 따라 내려받기 후 열립니다.</p></div>
<script id="data" type="application/json">{json.dumps(data, ensure_ascii=False).replace("</", "<\\/")}</script><script>{JS}</script></body></html>"""
    out_dir = os.path.join(BUNDLE, "01_Panel", "Home"); os.makedirs(out_dir, exist_ok=True)
    for old in glob.glob(os.path.join(out_dir, "프로젝트_홈_*.html")): os.remove(old)
    out = os.path.join(out_dir, f"프로젝트_홈_{V}.html"); open(out, "w", encoding="utf-8").write(H)
    print("saved", os.path.relpath(out, BUNDLE), f"(파일 {len(files)}개)")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--version"); a = ap.parse_args()
    M = {}
    sp = os.path.join(ROOT, "strategy")
    if os.path.exists(os.path.join(sp, "content.py")):
        sys.path.insert(0, sp); sys.path.insert(0, BUILD)
        import content as C
        if hasattr(C, "file_meanings"): M = C.file_meanings(a.version)
    build(a.version, M)
