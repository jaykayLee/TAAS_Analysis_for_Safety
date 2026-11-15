"""
파서 검증: TAAS 실제 응답(XML)을 파싱한 결과가 브라우저 수집기(v8/v9)가 저장한 레코드와 같은지.
    python -m pytest tests -q      (또는)   python tests/test_parser.py
"""
import gzip
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from taas_collector import octagon as O  # noqa: E402

S = json.load(gzip.open(Path(__file__).with_name("samples.json.gz"), "rt", encoding="utf-8"))["samples"]


def parsed(s):
    P = None
    for x in s["pages"]:
        q = O.parse(x)
        P = q if P is None else O.merge_page(P, q)
    return P


def test_tables_match_browser_records():
    for s in S:
        P, r = parsed(s), s["rec"]
        n, k = len(P["rows"]), len(P["cols"])
        assert P["lab"] == r["lab"], s["pid"]
        assert P["rows"] == r["rows"][:n], s["pid"]
        assert P["cols"] == r["cols"][:k], s["pid"]
        assert all(a == b[:k] for a, b in zip(P["data"], r["data"][:n])), s["pid"]
        assert len(set(P["meaT"])) == s["tpl"]["nMea"], s["pid"]


def test_param_tools():
    p = ':row_list="906:*907",:col_list="888:911",:mea_list="334:*336",:vcondition="D1443@|@P08 S01 T111 #OTE![202501]!# #OTE![202512]!#;|;",:pagenum="1"'
    on = O.all_on(p)
    assert ":row_list=\"906:907\"" in on and ":mea_list=\"334:336\"" in on
    assert O.set_off(on, "336").count("*336") == 1
    r = O.set_range(on, "D1443=201001~201412;")
    assert "#OTE![201001]!# #OTE![201412]!#" in r
    assert O.set_range(on, "D9999=2010~2014;") is None
    assert ':pagenum="7"' in O.set_page(on, 7)


if __name__ == "__main__":
    test_tables_match_browser_records()
    test_param_tools()
    print("ok", len(S), "samples")
