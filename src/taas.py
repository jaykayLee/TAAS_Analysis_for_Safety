"""
TAAS 교통사고 상세통계 라이브러리 로더

    import taas
    lib = taas.Library("taas_library")          # 폴더 경로
    lib.search("사고유형")                          # 장표 찾기
    df = lib.table(7019)                         # 한 장표 (축 이름이 컬럼명)
    s  = lib.series(7019, measure="사고[건]", 사고유형="추돌")   # 연도 시계열
    lib.corr([s1, s2], diff=True)                 # 상관 (1차 차분 기본)
    lib.libs()                                    # 부처 라이브러리 목록 (kostat·mois·molit·police·policy)
    pop = lib.ext("mois").series(9102, measure="인구[명]", 연령구분="어린이 0~12세")   # 부처 라이브러리도 같은 방법
"""
import json
from pathlib import Path

import pandas as pd

TOTALS = {"합계", "계", "전국", "전체", "소계"}


class Library:
    def __init__(self, path="taas_library"):
        self.path = Path(path)
        self.patterns = pd.read_parquet(self.path / "parquet" / "patterns.parquet")
        self._facts = None

    def libs(self):
        """부처별 외부 라이브러리 이름 (library/ext/<부처>)"""
        d = self.path / "ext"
        return sorted(x.name for x in d.iterdir() if (x / "parquet").exists()) if d.exists() else []

    def ext(self, name):
        """부처 라이브러리 하나 (행정안전부 mois, 국토교통부 molit, 경찰청 police, 통계청 kostat, 제도 연표 policy)"""
        return Library(self.path / "ext" / name)

    @property
    def facts(self):
        if self._facts is None:
            self._facts = pd.read_parquet(self.path / "parquet" / "facts.parquet")
        return self._facts

    def search(self, text):
        p = self.patterns
        return p[p.name.str.contains(text) | p.path.str.contains(text)][["pid", "name", "path", "year_min", "year_max", "measures"]]

    def dims(self, pid):
        return json.loads(self.patterns.loc[self.patterns.pid == pid, "dim_names"].iloc[0])

    def table(self, pid):
        """장표 하나를 축 이름이 붙은 롱포맷으로 반환"""
        f = pd.read_parquet(self.path / "parquet" / "facts.parquet", filters=[("pid", "==", int(pid))]) \
            if self._facts is None else self.facts[self.facts.pid == int(pid)]
        dn = self.dims(pid)
        f = f.rename(columns={f"d{i+1}": n for i, n in enumerate(dn)})
        keep = ["year", "measure"] + dn + ["value"]
        return f[keep].reset_index(drop=True)

    def series(self, pid, measure=None, **filters):
        """연도 시계열. 지정하지 않은 축은 합계/계/전국 값을 사용"""
        t = self.table(pid)
        if measure:
            t = t[t.measure == measure]
        dims = self.dims(pid)
        for d in dims:
            if d in filters:
                want = filters[d]
                t = t[t[d].isin(want if isinstance(want, (list, tuple, set)) else [want])]
        # 지정하지 않은 축은 합계로 고정. 상위 분류처럼 합계로 고정하면 비는 축은 합산
        for d in dims:
            if d in filters:
                continue
            tot = [v for v in t[d].unique() if v in TOTALS]
            if tot and len(t[t[d] == tot[0]]):
                t = t[(t[d] == tot[0]) | t[d].isna()]   # 과거 연도에 없던 축(빈칸)은 통과
        s = t.groupby("year").value.sum()
        name = self.patterns.loc[self.patterns.pid == pid, "name"].iloc[0]
        s.name = " · ".join([name] + ([measure] if measure else []) + [f"{k}={v}" for k, v in filters.items()])
        return s

    @staticmethod
    def corr(series, diff=True, method="pearson"):
        df = pd.concat(series, axis=1)
        if diff:
            df = df.diff()
        return df.dropna().corr(method=method)
