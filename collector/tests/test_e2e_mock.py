"""
수집 흐름 전체를 TAAS 없이 시험: Playwright 로 진짜 Chromium 을 띄우되, TAAS 주소 요청은
가짜 응답(목록 페이지, 장표 정보, 뷰어, 조회 결과 = 실제 TAAS 응답 표본)으로 돌려준다.
    python tests/test_e2e_mock.py
"""
import gzip
import json
import re
import sys
import tempfile
from pathlib import Path
from urllib.parse import parse_qs, unquote_plus

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from taas_collector import collector as C  # noqa: E402
from taas_collector import octagon as O  # noqa: E402

S = {s["pid"]: s for s in json.load(gzip.open(Path(__file__).with_name("samples.json.gz"), "rt", encoding="utf-8"))["samples"]}
PIDS = ["6808", "7306"]
FAIL_ALL_ON = False

MENU = [{"menuId": "1", "pMenuId": "0", "menuName": "교통사고", "menuType": "F", "subjectId": "0", "patternId": "0", "rootName": "교통사고", "trendYn": "N"}]
for i, pid in enumerate(PIDS):
    MENU.append({"menuId": str(10 + i), "pMenuId": "1", "menuName": f"표본 {pid}", "menuType": "P", "subjectId": S[pid]["tpl"]["sid"],
                 "patternId": pid, "rootName": "교통사고", "trendYn": "N"})


def list_page():
    return f"<html><body><script>var statsMenuList = {json.dumps(MENU, ensure_ascii=False)};</script></body></html>"


def viewer_page(pid):
    T = S[pid]["tpl"]
    raw = T["pre"]  # 표본 틀 (실제 TAAS 에서는 '*' 가 섞여 있음 → 일부러 하나 꺼서 시험)
    ids = O.list_ids(raw, "mea_list")
    raw = O.set_off(raw, O.list_ids(raw, "row_list")[-1])  # 기본 화면에서 꺼진 축 하나
    tags = "".join(f'<div class="ovTag" id="mea_{x}_1"><div class="ovTagText">M{x}</div></div>' for x in ids)
    cols = "".join(f'<div id="colDrop_{i}"><div class="ovTagText">{n}</div></div>' for i, n in enumerate(S[pid]["rec"]["colDims"]))
    notes = "\\n".join(S[pid]["rec"]["msg"])
    return f"""<html><body><div id="x"></div>{tags}{cols}<pre>{"<br>".join(S[pid]["rec"]["msg"])}</pre>
      <script>setTimeout(() => {{ window.viewer = {{ getViewer: () => ({{ preParamTmp: {json.dumps(raw, ensure_ascii=False)}, config: {{}} }}) }}; }}, 300);</script></body></html>"""


def proxy(body):
    q = parse_qs(body)
    params = q["params"][0]
    pid = re.search(r':pattern_id="(\d+)"', params).group(1)
    pages = S[pid]["pages"]
    n = int(re.search(r':pagenum="(\d+)"', params).group(1))
    x = pages[min(n, len(pages)) - 1]
    x = re.sub(r"<TOTALPAGE>\d+</TOTALPAGE>", f"<TOTALPAGE>{len(pages)}</TOTALPAGE>", x)
    x = re.sub(r"<CURRENTPAGE>\d+</CURRENTPAGE>", f"<CURRENTPAGE>{n}</CURRENTPAGE>", x)
    mea = re.search(r':mea_list="([^"]*)"', params).group(1)
    lists = "".join(re.findall(r':(?:row|col|mea)_list="([^"]*)"', params))
    if FAIL_ALL_ON and pid == "6808" and "*" not in lists:  # 모두 켜면 서버 오류 나는 장표 흉내
        return "<OCTAGONDATA><PAGE><TOTALPAGE></TOTALPAGE></PAGE><MESSAGE><![CDATA[조회된 데이터가 없습니다. SQL오류]]></MESSAGE></OCTAGONDATA>"
    assert FAIL_ALL_ON or "*" not in mea, "모두 켠 상태로 요청해야 함"
    return x


class MockTaas(C.Taas):
    def open(self):
        if not getattr(self, "_routed", False):
            self.ctx.route("https://taas.koroad.or.kr/**", self._handle)
            self._routed = True
        super().open()

    def _handle(self, route):
        req = route.request
        u = req.url
        if "typical.do" in u:
            return route.fulfill(status=200, content_type="text/html; charset=utf-8", body=list_page())
        if "selectPatternInfo.do" in u:
            pid = re.search(r"patternId=(\d+)", u).group(1)
            return route.fulfill(status=200, content_type="application/json", body=json.dumps(
                {"dateInfo": {"minYear": "202001" if pid == "7306" else "2020", "maxYear": "202512" if pid == "7306" else "2022", "dimAttrId": 1443 if pid == "7306" else 2565}}))
        if "TypicalAnalysis.jsp" in u:
            pid = parse_qs(req.post_data or "")["pid"][0]
            return route.fulfill(status=200, content_type="text/html; charset=utf-8", body=viewer_page(pid))
        if "OctagonProxyServlet" in u:
            return route.fulfill(status=200, content_type="text/xml; charset=utf-8", body=proxy(req.post_data))
        return route.fulfill(status=404, body="")


def main():
    # 표본 틀의 vcondition 을 표본 구간에 맞춤
    db = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(tempfile.mkdtemp()) / "t.sqlite"
    C.Taas = MockTaas
    C.main(["--db", str(db), "run", "--from", "2020", "--to", "2025", "--pids", ",".join(PIDS)])
    store = C.Store(db)
    recs = {r["key"]: r for r in store.recs()}
    print("수집된 키:", sorted(recs))
    for pid, key in (("6808", "6808|2020-2022"), ("7306", "7306|2025-2025")):
        r, s = recs[key], S[pid]
        n = len(r["rows"])
        assert r["rows"] == s["rec"]["rows"][:n] and n > 0, key
        assert r["lab"] == s["rec"]["lab"], key
        assert r["colDims"] == s["rec"]["colDims"], key
        print("일치:", key, n, "행")
    out = db.with_suffix(".json.gz")
    C.main(["--db", str(db), "export", str(out)])
    j = json.load(gzip.open(out, "rt", encoding="utf-8"))
    assert j["meta"] and j["recs"]
    C.main(["--db", str(db), "status", "--from", "2020", "--to", "2025"])
    # 예비 경로: 모두 켠 조회가 서버 오류 → 꺼져 있던 수치항목만 빼고 받기
    global FAIL_ALL_ON
    FAIL_ALL_ON = True
    C.main(["--db", str(db), "run", "--from", "2020", "--to", "2025", "--pids", "6808", "--force"])
    r = {x["key"]: x for x in C.Store(db).recs()}["6808|2020-2022"]
    assert r["dimMissing"] and r["rows"] and any("서버 오류" in m for m in r["msg"]), r["msg"]
    print("예비 경로 일치:", r["dimMissing"], r["msg"][-1])
    print("e2e ok")


if __name__ == "__main__":
    main()
