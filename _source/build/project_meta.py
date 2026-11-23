# -*- coding: utf-8 -*-
"""TAAS 프로젝트 메타 생성기 — PROJECT.json · README.txt · 04_Libraries/*/LIB-*/library.json · 03_References 분류별 색인(Excel).
  python3 _source/build/project_meta.py --version v1.7
원천: 이 파일의 LIBS(라이브러리 선언) · 04_Libraries/00_Core/LIB-REFS/refs.json(문헌) · _source/strategy/CHANGELOG.md(이번 버전 내용)."""
import os, sys, json, glob, argparse, datetime, re
BUILD = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.dirname(BUILD); BUNDLE = os.path.dirname(SRC)
sys.path.insert(0, os.path.join(BUILD, "db")); sys.path.insert(0, os.path.join(BUILD, "template"))
import contract as K

PID, NAME = "TAAS", "TAAS 교통사고 분석"
REPO, BRANCH = "jaykayLee/TAAS_Analysis_for_Safety", "main"
PANEL_URL = "https://claude.ai/artifact/UaFGY49Midoyg6h7BVLune"
# 라이브러리 선언 — 원문(03) → 원천(04) → 생성물(빌드 결과, git 제외)
OUT = "04_Libraries/02_Statistics/LIB-TAAS/build"
LIBS = [
    {"id": "LIB-TAAS", "cat": "02_Statistics", "name": "TAAS 교통사고 상세통계", "pids": "1~7345 (338개 장표)", "version": "2025",
     "source": "03_References/02_Statistics/files/taas", "raw": "03_References/02_Statistics/files/taas/taas_raw_full_*.json.gz",
     "output": OUT, "build": "python _source/build.py", "verify": "python _source/ops/verify.py", "note": "수집 원문(json.gz)이 곧 원천 — 같은 key 는 ts 가 늦은 것이 이김"},
    {"id": "LIB-KOSTAT", "cat": "02_Statistics", "name": "통계청 인구총조사 연령별 인구", "pids": "9001·9002", "version": "2025",
     "source": "03_References/02_Statistics/files/kostat", "raw": "04_Libraries/02_Statistics/LIB-KOSTAT/kostat.json.gz", "output": OUT + "/ext/kostat",
     "build": "python _source/build.py --ext kostat", "verify": "python _source/ops/verify_ext.py kostat", "note": "어린이 0~12세는 5세 단위로 추정"},
    {"id": "LIB-MOIS", "cat": "02_Statistics", "name": "행정안전부 주민등록인구", "pids": "9101·9102", "version": "-",
     "source": "03_References/02_Statistics/files/mois", "raw": "04_Libraries/02_Statistics/LIB-MOIS/mois.json.gz", "output": OUT + "/ext/mois",
     "build": "python _source/build.py --ext mois", "verify": "python _source/ops/verify_ext.py mois", "note": "수집 예정(KOSIS OpenAPI 키)"},
    {"id": "LIB-MOLIT", "cat": "02_Statistics", "name": "국토교통부 자동차·도로·교통량·주행거리", "pids": "9201~9205", "version": "-",
     "source": "03_References/02_Statistics/files/molit", "raw": "04_Libraries/02_Statistics/LIB-MOLIT/molit.json.gz", "output": OUT + "/ext/molit",
     "build": "python _source/build.py --ext molit", "verify": "python _source/ops/verify_ext.py molit", "note": "수집 예정(KOSIS OpenAPI 키)"},
    {"id": "LIB-POLICE", "cat": "02_Statistics", "name": "경찰청 보호구역·면허·단속", "pids": "9003, 9301~9308", "version": "2025",
     "source": "03_References/02_Statistics/files/police", "raw": "04_Libraries/02_Statistics/LIB-POLICE/police.json.gz", "output": OUT + "/ext/police",
     "build": "python _source/build.py --ext police", "verify": "python _source/ops/verify_ext.py police", "note": "KOSIS 면허 9301·9303·9304 는 수집 예정"},
    {"id": "LIB-POLICY", "cat": "01_Standard_Law", "name": "교통안전 제도 시행 연표", "pids": "9901", "version": "25건",
     "source": "04_Libraries/01_Standard_Law/LIB-POLICY/정책_연표.csv", "raw": "04_Libraries/01_Standard_Law/LIB-POLICY/policy.json.gz", "output": OUT + "/ext/policy",
     "build": "python _source/build.py --ext policy", "verify": "python _source/ops/verify_ext.py policy", "note": "근거 SOURCES.md(확인 13·부분확인 6·미확인 6), 법령 링크는 03_References/01_Standard_Law 색인"},
    {"id": "LIB-REFS", "cat": "00_Core", "name": "참고문헌 목록(03 색인의 원천)", "pids": "-", "version": "1.0",
     "source": "04_Libraries/00_Core/LIB-REFS/refs.json", "raw": "04_Libraries/00_Core/LIB-REFS/refs.json", "output": "03_References/<분류>/참고문헌_색인_<분류>_v*.xlsx",
     "build": "python _source/build/project_meta.py --version <버전>", "verify": "-", "note": "새 문헌은 refs.json 에 추가"},
]
CAT_DESC = {"00_Core": "프로젝트 내부 기준(참고문헌 목록)", "01_Standard_Law": "교통안전 법령·제도(시행 연표의 근거)", "02_Statistics": "TAAS 사고 통계와 부처 통계(인구·차량·면허·단속)",
            "03_Papers_Patents": "논문·연구 보고서(아직 없음)", "04_Other_Projects": "다른 기관·과제 산출물(아직 없음)", "05_New_Strategies": "새 분석 방법 후보(아직 없음)", "06_Methods": "계산 방법(아직 없음 — 통계 기법은 패널 코드에 있음)"}


def rp(*a): return os.path.join(BUNDLE, *a)


def changelog_top():
    p = rp("_source", "strategy", "CHANGELOG.md")
    if not os.path.exists(p): p = rp("CHANGELOG.md")
    t = open(p, encoding="utf-8").read()
    m = re.search(r"^## (.+?)\n(.*?)(?=^## |\Z)", t, re.S | re.M)
    return (m.group(1).strip(), m.group(2).strip()) if m else ("", "")


def project_json(V):
    pj = {"schema": "project/1.0", "id": PID, "name": NAME, "version": V,
          "structure": {"contract": f"project-structure/{K.STRUCT_VER}", "doc": f"02_Strategy/03_User/프로젝트구조_규약_v{K.STRUCT_VER}.docx"},
          "owner": "J.K. Lee", "repo": REPO, "branch": BRANCH, "panel_url": PANEL_URL, "entry": f"Main_{PID}.bat",
          "folders": {"_source": "코드 — 라이브러리 조립(build.py)·패널 원천·수집기·자동 갱신·시험·문서 원천",
                      "01_Panel": "Home(프로젝트 홈) · Main(TAAS 분석 패널, 온라인 게시본은 panel_url)",
                      "02_Strategy": "변경 이력·갱신 절차·분석 보고서·사용 매뉴얼·LLM 절차·의존성",
                      "03_References": "TAAS·KOSIS·공공데이터 원문(수집본)과 법령 링크 색인",
                      "04_Libraries": "LIB-TAAS·부처 라이브러리(KOSTAT·MOIS·MOLIT·POLICE)·제도 연표·참고문헌 목록 — 빌드 결과는 LIB-TAAS/build(git 제외)",
                      "05_UserComments": "STATUS.md(지금 상태·다음 할 일) · 요청 · 예약 작업 프롬프트"},
          "libraries": [{"id": L["id"], "version": L["version"], "category": L["cat"], "path": f"04_Libraries/{L['cat']}/{L['id']}"} for L in LIBS],
          "library_output": OUT, "status": "05_UserComments/STATUS.md", "history": "02_Strategy/00_History/",
          "exceptions": ["최상위 CLAUDE.md(Claude 작업 규칙 — 저장소 루트에 있어야 읽힘)·README.md(GitHub 첫 화면)·.gitignore 는 표준 목록 밖이지만 유지",
                         "기본 브랜치는 main(PC 업데이트·패널 [업데이트] 버튼이 main 을 받음)"],
          "updated": datetime.date.today().isoformat(), "note": "생성물 — _source/build/project_meta.py"}
    open(rp("PROJECT.json"), "w", encoding="utf-8").write(json.dumps(pj, ensure_ascii=False, indent=1) + "\n")


def readme_txt(V):
    head, body = changelog_top()
    L = [f"{NAME} ({PID}) — {V}", "=" * 48, f"시작: Main_{PID}.bat (프로젝트 홈 → 메인 패널) · 프로젝트 정보: PROJECT.json · 지금 상태: 05_UserComments/STATUS.md",
         f"온라인 패널: {PANEL_URL}", f"저장소: https://github.com/{REPO} (브랜치 {BRANCH})", "", f"구조(project-structure/{K.STRUCT_VER}):",
         *[f"   {t['path']:18} {t['role']}" for t in K.top(PID)], "", f"이번 버전: {head}", body, "",
         "라이브러리 다시 만들기: python _source/build.py   · 바뀐 파일만 받기: python _source/ops/pc_sync.py", "생성물 — _source/build/project_meta.py", ""]
    open(rp("README.txt"), "w", encoding="utf-8").write("\n".join(L))


def library_jsons():
    for L in LIBS:
        d = rp("04_Libraries", L["cat"], L["id"]); os.makedirs(d, exist_ok=True)
        j = {"schema": "library/1.0", **{k: L[k] for k in ("id", "name", "version", "pids", "source", "raw", "output", "build", "verify", "note")},
             "category": L["cat"], "generated_output_in_git": False if L["output"].startswith(OUT) else True, "updated": datetime.date.today().isoformat()}
        open(os.path.join(d, "library.json"), "w", encoding="utf-8").write(json.dumps(j, ensure_ascii=False, indent=1) + "\n")


def ref_indexes(V):
    from openpyxl import Workbook
    from xlsx_style import title as xt, table as xtab, finish as xfin
    refs = json.load(open(rp("04_Libraries", "00_Core", "LIB-REFS", "refs.json"), encoding="utf-8"))["refs"]
    head = ["REF", "제목", "발행기관·근거", "기간·시행일", "종류", "링크", "원문 사본(files/)", "라이브러리", "비고"]
    for c, n, _ in K.CATS:
        if c == "06_Methods": continue
        rows = [[r["id"], r["title"], r["org"], r["period"], r["kind"], r["url"], r["files"], r["lib"], r["note"]] for r in refs if r["cat"] == c]
        out = rp("03_References", c, f"참고문헌_색인_{c}_{V}.xlsx")
        for old in glob.glob(rp("03_References", c, f"참고문헌_색인_{c}_v*.xlsx")):
            if old != out: os.remove(old)
        wb = Workbook(); ws = wb.active; ws.title = "색인"
        xt(ws, f"참고문헌 색인 — {c} {n} ({len(rows)}건)", f"{NAME} · {V} · 원천 04_Libraries/00_Core/LIB-REFS/refs.json — 생성물, 직접 수정 금지", len(head))
        xtab(ws, head, rows or [["(이 분류의 문헌 없음 — 자리 유지)"] + [""] * (len(head) - 1)], [9, 44, 30, 16, 10, 46, 30, 12, 26], center=(1, 5, 8))
        xfin(wb); wb.save(out)
        os.makedirs(rp("03_References", c, "files"), exist_ok=True); open(rp("03_References", c, "files", ".keep"), "a").close()
    return [rp("03_References", c, f"참고문헌_색인_{c}_{V}.xlsx") for c, _, _ in K.CATS if c != "06_Methods"]


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--version", required=True); a = ap.parse_args()
    project_json(a.version); readme_txt(a.version); library_jsons(); made = ref_indexes(a.version)
    import subprocess
    subprocess.run([sys.executable, os.path.join(BUILD, "template", "office_check.py"), "-q", *made], check=True)
    print("saved PROJECT.json · README.txt · library.json", len(LIBS), "· 03 색인", len(made))
