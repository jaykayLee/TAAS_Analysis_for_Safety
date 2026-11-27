# -*- coding: utf-8 -*-
"""REQ-20261127-01 조사 결과 엑셀 3종 생성 (손으로 고치지 말고 이 파일을 고친 뒤 다시 실행)
  python3 _source/build/strategy/research_book.py --version v1.0
  → 02_Strategy/02_Analysis/분석기법_제안목록_v1.0.xlsx · 추가라이브러리_제안_v1.0.xlsx · 논문_조사요약_v1.0.xlsx
글꼴 맑은 고딕(Office 2016+). 검증은 _source/build/template/office_check.py"""
import argparse, sys
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "02_Strategy" / "02_Analysis"
F = "맑은 고딕"
HEAD = PatternFill("solid", fgColor="1D5FAE")
BAND = {"SOTA": "E3EDF9", "고신뢰": "E8F5E9", "역발상": "FFF4D6", "보강": "F2F2F2"}
THIN = Side(style="thin", color="C9D1DA")

# ───────────────────────── ③ 분석 기법 ─────────────────────────
TECH_COLS = ["번호", "분류", "기법", "한 줄 요약", "효과 — 무엇을 알 수 있나", "방법 — 절차", "이 프로젝트 적용 예 (장표)",
             "필요 자료·최소 길이", "신뢰도·주의", "난이도", "패널 반영 우선순위", "지금 패널과의 관계", "참고문헌", "출처 확인"]
TECH = [
 ("SOTA", "베이지안 구조 시계열 (BSTS · CausalImpact)", "개입이 없었을 때의 반사실 추세를 다른 계열로 예측하고 실제와의 차이를 효과로 봄",
  "제도 효과를 신뢰구간(사후분포)과 함께 '누적 몇 건 감소'로 제시. 공변량(인구·차량·주행거리)을 함께 넣어 추세를 통제",
  "① 개입 전 구간에서 목표 계열 ~ 공변량 + 국소 추세 + 계절 성분 상태공간 모형 적합 ② 개입 후 구간을 예측 ③ 실제 − 예측의 누적합과 사후 확률",
  "어린이 사고(7196) ~ 전체 사고(1)·어린이 인구(9102), 개입 2020(민식이법). 음주 사고(7159) ~ 단속(9307), 개입 2019",
  "연 단위면 개입 전 10년 이상 권장. 월 자료(7159·7196 월별)를 쓰면 훨씬 안정적",
  "공변량이 개입의 영향을 받지 않아야 함(예: 같은 해 단속 강화). 연 단위 21개 점은 사후 구간이 넓음", "중", 1, "⑤ 중단 시계열을 보완(공변량·불확실성)",
  "Brodersen et al. (2015) Annals of Applied Statistics 9(1) — doi:10.1214/14-AOAS788", "기억(DOI 확인 권장)"),
 ("SOTA", "합성통제법 (Synthetic Control)", "개입받지 않은 단위들의 가중 조합으로 '개입받지 않은 한국(또는 시도)'을 만들어 비교",
  "단일 국가·단일 정책의 효과를 투명한 비교군으로 추정. 가중치가 공개되어 해석이 쉬움",
  "① 기증 풀(OECD 국가 또는 정책 미시행 시도) 구성 ② 개입 전 추세가 맞도록 가중치 추정 ③ 개입 후 격차 ④ 위약(placebo) 단위 검정으로 유의성",
  "5030(2021) 효과: OECD 국가 사망자(6809~) 기증 풀. 시도별로 시행 시기가 다른 제도(카메라 확대 9306)는 시도 단위로",
  "개입 전 기간이 충분하고 기증 단위 10개 이상", "한국과 비슷한 추세의 기증국이 없으면 적합 불량 — 개입 전 RMSPE 확인 필수", "중", 2, "없음 (새 탭 기법)",
  "Abadie, Diamond & Hainmueller (2010) JASA 105(490) — doi:10.1198/jasa.2009.ap08746", "기억(DOI 확인 권장)"),
 ("SOTA", "합성 이중차분 (Synthetic DiD)", "합성통제의 가중치 + 이중차분의 시간 가중치를 함께 써서 두 방법의 약점을 보완",
  "비교군 추세가 완전히 평행하지 않아도 안정적인 효과 추정", "① 단위 가중치·시간 가중치 추정 ② 가중 이중차분 ③ 부트스트랩·jackknife 표준오차",
  "시도(17개) × 연도 패널에서 특정 시도만 먼저 시행한 제도(예: 노인보호구역 확대, 카메라 집중 설치)", "시도 × 연도 패널, 개입 전 5년 이상",
  "전국 동시 시행 제도에는 쓸 수 없음", "상", 3, "없음",
  "Arkhangelsky et al. (2021) American Economic Review 111(12) — doi:10.1257/aer.20190159", "기억(DOI 확인 권장)"),
 ("SOTA", "시차 도입 이중차분 (Callaway–Sant'Anna)", "단위마다 시행 시점이 다를 때 생기는 기존 이중차분(TWFE)의 편향을 피하는 방법",
  "'시행 후 n년차 효과'(event study)를 편향 없이 추정", "① 시행 시점별 집단(cohort) 정의 ② 집단·연도별 ATT 추정 ③ 사건 시점 기준으로 합산",
  "시군구별 어린이보호구역 지정·무인카메라 설치 시점이 다른 경우 (시군구 사고 장표 7195·7207)", "시군구 × 연도, 시행 시점 정보 필요",
  "시행 시점 자료가 아직 라이브러리에 없음 — 지자체 자료 확보 필요", "상", 3, "없음",
  "Callaway & Sant'Anna (2021) Journal of Econometrics 225(2) — doi:10.1016/j.jeconom.2020.12.001", "기억(DOI 확인 권장)"),
 ("SOTA", "이중 머신러닝 (Double/Debiased ML)", "많은 통제변수를 머신러닝으로 걸러 낸 뒤 관심 변수의 효과만 추정",
  "변수가 많은 시군구 패널에서 단속·시설 등 한 요인의 효과를 과적합 없이 추정", "① 결과·처치를 각각 통제변수로 ML 예측 ② 잔차끼리 회귀 ③ 교차 적합(cross-fitting)",
  "시군구 사고율 ~ 카메라 밀도 + (인구구조·도로연장·차량 등 다수)", "관측치 수백 개 이상 (시군구 × 연도)", "연도 21개 전국 계열에는 부적합", "상", 3, "없음",
  "Chernozhukov et al. (2018) Econometrics Journal 21(1) — doi:10.1111/ectj.12097", "기억(DOI 확인 권장)"),
 ("SOTA", "인과 포레스트 (이질적 효과)", "같은 제도라도 어느 지역·집단에서 효과가 컸는지 나무 모형으로 찾음",
  "'효과가 큰 곳'을 찾아 정책 우선순위에 바로 쓰임", "① 처치·통제 데이터 ② honest tree 숲 학습 ③ 단위별 CATE와 변수 중요도",
  "5030 효과가 큰 시도·도로형태 찾기(7087 도로형태별)", "단위 수백 개 이상", "표본이 작으면 잡음 — 탐색용으로만", "상", 3, "없음",
  "Wager & Athey (2018) JASA 113(523) — doi:10.1080/01621459.2017.1319839", "기억(DOI 확인 권장)"),
 ("SOTA", "변화점 탐지 (PELT · 베이지안 온라인 변화점)", "평균·기울기가 바뀐 시점을 여러 개까지 자동으로 찾음",
  "제도 연도를 미리 정하지 않고 '데이터가 말하는' 변곡점을 찾아 제도 연표와 대조", "① 비용함수(평균·분산 변화) ② 벌점으로 변화점 개수 조절 ③ 찾은 시점과 연표 비교",
  "모든 사고 장표 — 지금 Pettitt(1개)을 여러 개로 확장", "연 단위 15개 이상, 월 자료 권장", "벌점 값에 결과가 민감 — 민감도 표 함께", "하", 1, "① 추세·변곡점(Pettitt 1개)을 확장",
  "Killick, Fearnhead & Eckley (2012) JASA 107(500) — doi:10.1080/01621459.2012.737745", "기억(DOI 확인 권장)"),
 ("SOTA", "베이지안 계층 공간 모형 (BYM2 · INLA)", "작은 지역의 들쭉날쭉한 사고율을 이웃 지역 정보로 안정화",
  "시군구 '진짜 위험 지역'과 우연히 높았던 지역을 구분", "① 시군구 인접 행렬 ② 포아송 + 공간 랜덤효과(BYM2) ③ INLA로 사후 사고율·초과 확률",
  "시군구 어린이·노인 사고(7195·7238) ÷ 인구", "시군구 경계(인접) 정보·인구", "인접 정보 자료 추가 필요", "상", 2, "없음 (지도 탭 필요)",
  "Riebler et al. (2016) Stat Methods Med Res 25(4) — doi:10.1177/0962280216660421; Rue et al. (2009) JRSS-B — doi:10.1111/j.1467-9868.2008.00700.x", "기억(DOI 확인 권장)"),
 ("SOTA", "그래디언트 부스팅 + SHAP 해석", "비선형·상호작용을 학습한 예측 모형을 SHAP 값으로 요인별 기여로 설명",
  "어떤 조건 조합(야간 × 노면 × 도로형태)이 사망 비율을 높이는지 순위", "① 셀 단위(조건 조합) 사망률을 목표로 학습 ② 교차검증 ③ SHAP 요약·의존도 그림",
  "기상상태·시간대·도로형태 장표(7090·7093·7144)의 사망/사고 비율", "조건 조합 셀 수백 개 이상", "인과가 아니라 연관 — '설명'이라는 말에 주의", "중", 2, "없음",
  "Lundberg & Lee (2017) NeurIPS — arXiv:1705.07874", "기억(확인 권장)"),
 ("SOTA", "등각 예측 (Conformal Prediction)", "분포 가정 없이 '이 범위에 90% 확률로 들어간다'는 예측 구간을 붙임",
  "내년 사고·사망 예측에 믿을 수 있는 범위를 붙여 목표 달성 가능성 판단", "① 예측 모형 학습 ② 보정 구간의 잔차 분위수 ③ 새 예측에 구간 부여(시계열은 블록 방식)",
  "2026년 사망자 예측 범위, 국가 목표 대비 달성 확률", "학습·보정 분할이 가능한 길이", "시계열은 교환가능성 가정이 깨짐 — 적응형 변형 사용", "중", 2, "없음 (예측 기능 신설 시)",
  "Angelopoulos & Bates (2021) — arXiv:2107.07511", "기억(확인 권장)"),
 ("고신뢰", "음이항 회귀 + 노출 오프셋 (사고빈도 GLM)", "사고 '건수'를 포아송·음이항 분포로 모형화하고 인구·차량·주행거리를 오프셋으로 넣음",
  "건수 자료에 맞는 표준 방법 — 과산포를 반영해 p값이 부풀지 않음", "① 과산포 검정 ② log(노출)을 오프셋 ③ 계수 = 율비(rate ratio)",
  "모든 사고 건수 장표 ÷ 9102·9201·9205 — 지금 OLS(원값·로그) 대신 권장", "연도 10개 이상", "교통안전 분야 표준. 영과잉이면 ZINB 검토", "하", 1, "③ 다중회귀(OLS)를 건수용으로 보강",
  "Lord & Mannering (2010) Transportation Research Part A 44(5) — doi:10.1016/j.tra.2010.02.001", "기억(DOI 확인 권장)"),
 ("고신뢰", "경험적 베이즈 전후 비교 (Hauer EB)", "평균으로의 회귀(사고 많던 곳이 저절로 줄어드는 현상)를 보정한 전후 비교",
  "시설·단속 '설치 효과'의 과대추정을 막는 교통안전 표준", "① 비교 지점으로 안전성능함수(SPF) ② EB 기대치 = 가중(SPF, 관측) ③ 설치 후 관측/기대",
  "보호구역·카메라 설치 지점 자료가 생기면 (현재는 지점 자료 없음). 5030 세계은행 보고서도 이 방식 권고", "지점 × 연도, 비교 지점", "지점 자료 필요", "중", 3, "없음",
  "Hauer (1997) Observational Before-After Studies in Road Safety, Pergamon; Mitra et al. (2021) World Bank GRSF 5030 보고서", "보고서 확인"),
 ("고신뢰", "분절회귀 ITS + 자기상관·계절 보정", "지금 ⑤ 중단 시계열에 자기상관(Newey-West/ARIMA 오차)·월 계절성·비교 계열을 더함",
  "같은 결과라도 표준오차가 정직해져 '유의'가 바뀔 수 있음", "① 월 자료로 전환 ② 계절 더미/푸리에 ③ 잔차 자기상관 검정 후 보정 ④ 비교 계열(통제 ITS)",
  "음주 월별(7159)·어린이 월별(7196) — 민식이법 ITS 논문(Epidemiol Health 2024)과 같은 설계", "월 자료 개입 전후 각 24개월 이상", "연 단위로는 한계 — 월 장표 활용", "하", 1, "⑤ 중단 시계열 보강",
  "Lopez Bernal, Cummins & Gasparrini (2017) Int J Epidemiol 46(1) — doi:10.1093/ije/dyw098", "기억(DOI 확인 권장)"),
 ("고신뢰", "조인포인트 회귀 (AAPC)", "추세가 꺾인 지점을 찾고 구간별 연평균 변화율(APC)·전체 평균(AAPC)을 제시",
  "역학·보건 분야 표준 보고 형식 — 논문 비교가 쉬움", "① 로그 선형 구간 회귀 ② 순열검정으로 꺾임 수 결정 ③ APC·AAPC와 신뢰구간",
  "연령별 사망(7344), 노인·어린이 사망 추이", "연 15개 이상", "꺾임 수가 많으면 과적합", "하", 1, "① 추세 탭에 보고 형식 추가",
  "Kim et al. (2000) Statistics in Medicine 19(3):335-351; 한국 적용 예 Eun (2020) AAP — doi:10.1016/j.aap.2019.105325", "Eun(2020) 웹 확인"),
 ("고신뢰", "연령-기간-코호트 (APC) 분석", "사망률 변화를 나이·시대·출생 세대 효과로 나눔",
  "'고령이라서'인지 '그 세대라서'인지 구분 — 출생 코호트(출생률 주제)와 바로 연결", "① 연령 × 연도 사망률 표 ② 식별 문제 처리(내재추정·제약) ③ 세 효과 곡선",
  "연령별 사상자(7344, 10세 단위) × 2005~2025, 인구 9101", "연령 × 기간 표 (5세 단위 권장)", "식별 문제 — 가정에 따라 결과가 달라짐을 명시", "중", 2, "없음",
  "Eun (2020) Accident Analysis & Prevention 134:105325 — doi:10.1016/j.aap.2019.105325", "웹 확인"),
 ("고신뢰", "율 분해 (Das Gupta · Kitagawa 표준화 분해)", "사망자 변화를 '인구구조 변화 몫'과 '연령별 위험도 변화 몫'으로 정확히 나눔",
  "저출산·고령화가 사고 통계를 얼마나 밀어 올리거나 내렸는지 숫자로 제시", "① 연령별 인구·사망률 두 시점 ② 구조 효과·율 효과 분해 ③ 연도 쌍마다 누적",
  "2005→2025 사망 감소 중 고령화가 상쇄한 양 (7344 + 9101/9102)", "연령별 인구·사고", "연령 구간이 거칠면 구조 효과 과소", "하", 1, "없음 (작은 기능으로 추가 가능)",
  "Das Gupta (1993) Standardization and Decomposition of Rates, U.S. Census Bureau; Van Hout et al. (Hasselt Univ.) 고령화 분해 예측", "Van Hout 웹 확인"),
 ("고신뢰", "토다-야마모토 그레인저 검정", "추세가 있는(비정상) 계열을 차분하지 않고도 쓸 수 있는 그레인저 검정",
  "차분으로 잃는 장기 관계를 보존 — 지금 차분 방식과 결과 비교", "① 적분 차수 d 확인 ② VAR(p+d) 적합 ③ 처음 p개 시차만 왈드 검정",
  "음주 단속(9307) → 음주 사고(7159), 면허 반납(9305) → 노인 사고", "연 15개 이상", "표본이 작아 검정력 낮음", "중", 2, "② 그레인저 보강",
  "Toda & Yamamoto (1995) Journal of Econometrics 66 — doi:10.1016/0304-4076(94)01616-8", "기억(DOI 확인 권장)"),
 ("고신뢰", "STL 분해 · 계절 조정 (월 자료)", "월별 계열을 추세·계절·잔차로 나눔",
  "명절·휴가철 효과를 걷어 낸 '진짜 추세'와 이상 달(코로나 등) 확인", "① 월 계열 ② LOESS 기반 STL ③ 계절 조정 계열로 다른 기법 적용",
  "월별 장표(6992·7159·7196·7240)", "월 36개 이상", "연 단위 장표에는 해당 없음", "하", 2, "탐색 탭 값 변환에 추가 가능",
  "Cleveland et al. (1990) Journal of Official Statistics 6(1)", "기억(확인 권장)"),
 ("고신뢰", "구조적 시계열 (상태공간 · 칼만 필터)", "추세 수준·기울기를 시간에 따라 변하는 숨은 상태로 추정 — 교통안전 시계열 표준 도구",
  "개입·노출을 넣은 추세 분석, 결측 연도 처리, 예측", "① 국소 선형 추세 모형 ② 개입·노출 설명변수 ③ 평활 상태와 진단",
  "사망자(1) ~ 주행거리(9205) + 개입 더미", "연 15개 이상", "모형 선택 진단 필요", "중", 2, "BSTS(1번)와 같은 계열",
  "Commandeur & Koopman (2007) An Introduction to State Space Time Series Analysis, OUP; Wegman·Allsop 외(ITF) 경기와 교통사망 분석에서 사용", "Wegman 웹 확인"),
 ("고신뢰", "부트스트랩·순열 검정 (작은 표본)", "분포 가정 대신 재표집으로 신뢰구간·p값 계산",
  "21개 점에서도 정직한 불확실성", "① 블록 부트스트랩(시계열) ② 통계량 반복 계산 ③ 분위수 구간",
  "모든 기법의 p값 보조 표시", "—", "블록 길이 선택 필요", "하", 1, "결과 행에 '부트스트랩 구간' 열 추가(열 추가 규칙 준수)",
  "Efron & Tibshirani (1993) An Introduction to the Bootstrap, Chapman & Hall", "기억"),
 ("역발상", "음성 대조 결과 (Negative Control Outcome)", "제도가 영향을 줄 수 없는 결과에서도 같은 변화가 보이면 '제도 효과'가 아니라 다른 요인",
  "가짜 효과를 걸러 내는 가장 값싼 반증", "① 제도와 무관한 결과 선정 ② 같은 ITS·DiD 적용 ③ 효과가 0 근처인지 확인",
  "민식이법(2020) → '어린이보호구역 밖 고속도로 화물차 사고'에도 같은 감소가 있으면 코로나 등 공통 요인", "같은 기간 다른 결과 계열", "음성 대조가 정말 무관한지 논증 필요", "하", 1, "⑤ 중단 시계열에 '비교 계열' 버튼",
  "Lipsitch, Tchetgen Tchetgen & Cohen (2010) Epidemiology 21(3) — doi:10.1097/EDE.0b013e3181d61eeb", "기억(DOI 확인 권장)"),
 ("역발상", "위약 시점 검정 (Placebo-in-time)", "가짜 개입 연도를 여러 개 넣어 '진짜' 연도의 변화가 유난히 큰지 봄",
  "효과가 우연한 추세 꺾임이 아닌지 확인", "① 개입 전 구간의 모든 연도를 가짜 T로 ② 같은 통계량 분포 ③ 진짜 T 순위 = p값",
  "⑤ 중단 시계열의 모든 계열", "개입 전 8년 이상", "연 단위면 가짜 T가 적음", "하", 1, "⑤ 중단 시계열에 버튼 하나로 추가 가능",
  "Abadie (2021) Journal of Economic Literature 59(2) — doi:10.1257/jel.20191450", "기억(DOI 확인 권장)"),
 ("역발상", "준유도 노출 (Quasi-induced Exposure)", "주행거리 자료가 없을 때 '과실 없는 피해 차량'을 노출의 대리로 씀",
  "가해 집단(예: 고령·특정 차종)의 상대 위험을 노출 자료 없이 추정", "① 2차량 사고에서 가해·피해 구분 ② 피해 쪽 구성비 = 노출 ③ 가해/피해 비 = 상대 위험",
  "가해운전자 연령대·차종 장표(7147·7030)와 피해 쪽 분포", "가해·피해가 모두 있는 2차량 사고 표", "피해 쪽이 '무작위 노출'이라는 가정 — ADAS 차량처럼 피해도 줄면 왜곡", "중", 2, "없음",
  "Cicchino (2022) Accident Analysis & Prevention — 보행자 AEB 효과에서 사용 (IIHS 서지 2243)", "웹 확인"),
 ("역발상", "분모 바꿔 보기 (노출 교차 점검)", "같은 사고를 인구·차량·면허·주행거리로 각각 나눠 결론이 뒤집히는지 확인",
  "'줄었다'는 결론이 분모 선택 때문인지 판단 — Smeed 법칙류 함정 방지", "① 분모 4종으로 비율 ② 추세 방향·크기 비교 ③ 뒤집히면 원인 서술",
  "노인 사고 ÷ 노인 인구 vs ÷ 노인 면허 소지자(6863) — 고령 운전 증가 효과 분리", "분모 계열 2개 이상", "분모끼리 기간이 다름", "하", 1, "상관관계 탭 비율 환산을 '여러 분모 한 번에'로",
  "Huang et al. (2016) PLoS ONE 11(4) — doi:10.1371/journal.pone.0153251 (Smeed 식, 경찰 vs 보건 자료)", "웹 확인"),
 ("역발상", "E-value (숨은 교란 민감도)", "관측된 효과를 '설명해 버리려면' 숨은 교란 요인이 얼마나 강해야 하는지 계산",
  "'다른 요인 때문 아니냐'는 반론에 숫자로 답함", "① 위험비(율비) ② E-value = RR + √(RR(RR−1)) ③ 신뢰구간 한계도 계산",
  "음주 사고 감소 율비, 보호구역 효과 율비", "율비와 신뢰구간", "정량적 해석에 대한 논쟁 있음 — 보조 지표로", "하", 1, "결과 모음에 열 추가",
  "VanderWeele & Ding (2017) Annals of Internal Medicine 167(4) — doi:10.7326/M16-2607", "기억(DOI 확인 권장)"),
 ("역발상", "양의 일탈 (Positive Deviance) — 예외부터 보기", "전국 추세와 반대로 움직인 시도·집단을 먼저 찾아 원인을 거꾸로 추적",
  "평균에 묻힌 성공 사례(또는 실패 사례)를 정책 근거로", "① 시도별 기대치(전국 추세) 대비 잔차 ② 상·하위 단위 선정 ③ 그 단위의 제도·시설 차이 조사",
  "시도별 노인 사고(7255)·무면허(7174)에서 전국과 반대로 움직인 시도", "시도 × 연도", "작은 시도는 우연 변동 — BYM2와 함께", "하", 1, "연계 제안·순위 목록과 결합 가능",
  "Marsh et al. (2004) BMJ 329:1177 — doi:10.1136/bmj.329.7475.1177", "기억(DOI 확인 권장)"),
 ("역발상", "심슨의 역설 점검 (층화 vs 합계)", "전체 사망률은 오르는데 연령층마다는 모두 내리는지 — 구성 변화가 만든 착시 확인",
  "고령화 사회에서 '사고가 늘었다'는 해석 오류 방지", "① 전체와 층별 추세 동시 산출 ② 방향이 다르면 구성비 효과 분해(율 분해)",
  "연령층별 사망(7344) vs 전체(1)", "층별 자료", "—", "하", 1, "탐색 탭 '층별/합계 비교' 토글 아이디어",
  "Simpson (1951) JRSS-B 13(2) 고전", "고전 문헌"),
 ("역발상", "보고 편향 삼각검증 (경찰 vs 보험 vs 응급실 vs 사망원인)", "같은 현상을 정의가 다른 자료원끼리 비교해 '통계가 줄어든 것'과 '실제가 줄어든 것'을 구분",
  "경찰DB 과소보고·정의 변경(30일 사망)을 감지", "① 같은 기간·집단 맞춤 ② 비율(경찰/보건) 추세 ③ 비율이 변하면 보고 체계 변화 의심",
  "TAAS 사망 vs 통계청 사망원인 운수사고 vs 질병청 손상 통계 (추가 라이브러리 필요)", "다른 자료원 2개 이상", "정의 차이(30일 기준·거주지 기준) 명시", "중", 1, "추가 라이브러리 제안 1·3번과 연결",
  "Huang et al. (2016) PLoS ONE (경찰 vs 보건 자료 비교) — doi:10.1371/journal.pone.0153251", "웹 확인"),
 ("역발상", "회귀 불연속 (나이 기준선)", "적성검사 주기가 바뀌는 나이(예: 75세) 바로 위·아래를 비교",
  "제도 대상 연령 경계에서의 위험 변화 — 강한 인과 설계", "① 1세 단위 연령별 자료 ② 경계 양쪽 국소 회귀 ③ 불연속 크기",
  "75세 적성검사 3년 주기(2019) — 1세 단위 운전자 연령 자료가 필요(현재 10세·5세 단위라 불가)", "1세 단위 연령", "현재 자료로는 불가 — 자료 확보 시", "중", 3, "없음",
  "Lee & Lemieux (2010) Journal of Economic Literature 48(2) — doi:10.1257/jel.48.2.281", "기억(DOI 확인 권장)"),
]

# ───────────────────────── ④ 추가 라이브러리 ─────────────────────────
LIB_COLS = ["우선순위", "자료명", "제공 기관", "형태", "기간·단위(확인 필요 포함)", "공통 축", "현재 패널과 연계 (장표)", "볼 수 있는 것", "주의·한계",
            "새 라이브러리(안)", "확인 근거", "확인 상태"]
LIBS = [
 (1, "사망원인통계 — 운수사고 사망(V01–V99) 시도·연령·성별", "통계청(국가데이터처) KOSIS", "통계표(KOSIS OpenAPI 가능)", "연 · 1983~ (Eun 2020이 1983~2017 사용)",
  "연도·시도·연령·성", "1 주요 교통지표·7344 연령별 사상자·7131 시도 사망", "경찰 30일 사망 vs 사망신고 기준 차이 → 과소보고·정의 변화 삼각검증, 장기 추세(1983~)",
  "거주지 기준(경찰은 발생지) — 시도 비교 시 주의", "LIB-KOSTAT 확장 (9003 다음 번호 9010~)", "index.go.kr 사망원인 지표, 통계청 2024 사망원인통계 보도자료", "존재 확인"),
 (1, "인구동향(출생·사망)·장래인구추계 (연령별 2072년까지)", "통계청 KOSIS", "통계표(OpenAPI)", "연 · 출생 1970~, 추계 2022~2072",
  "연도·시도·연령", "9001·9102 인구(분모), 7196 어린이·7240 노인", "출생아 감소 → 어린이 노출 감소 전망, 고령 사고 2040 전망(율 분해·APC와 결합)",
  "추계는 가정(중위·저위) 선택 명시", "LIB-KOSTAT 확장", "통계청 KOSIS 상시 공개 통계 (작성자 지식)", "연계 방식 확인 필요"),
 (1, "국가손상정보포털 — 응급실손상환자심층조사(EDIIS)·퇴원손상통계", "질병관리청", "웹 통계·원자료 신청", "연 · 2017~2022 요약 공개(포털), 원자료 2006~",
  "연도·연령·운송수단(보행·자전거·이륜·차량)", "보행자(7285)·이륜·자전거(7272) 장표", "경찰에 신고되지 않은 손상 규모, 중증도·입원·사망 비율 (2022 입원 27.9%)",
  "표본 병원 기반 — 전국 추정 아님", "LIB-KDCA (번호 9401~ 새 범위)", "kdca.go.kr 국가손상정보포털 교통사고 손상 페이지 (2024-03-18 업데이트)", "존재 확인"),
 (1, "자동차보험 교통사고 통계 (사고·피해자·손해액)", "보험개발원(KIDI)", "보고서·통계(bigin.kidi.or.kr)", "연 · 차종·사고유형",
  "연도·차종·사고유형", "7030 가해 차종·7002 사고유형", "경찰 미신고 경미 사고 포함한 '전체 사고' 규모, 경찰 통계와 비율 추세",
  "보험 가입 차량만, 이용 조건 확인", "LIB-KIDI (9501~)", "bigin.kidi.or.kr 공개 PDF (2022·2023)", "존재 확인"),
 (1, "자동차안전도평가(KNCAP) ADAS 점수 + 보험사 실사고 분석", "국토교통부·한국교통안전공단 / 삼성화재 교통안전문화연구소", "평가 결과·분석 보고", "평가 2013~, 사고 2018~2024 약 83만 건",
  "차종(모델)·연식", "차량기술 매핑 탭, 7030 차종별·추돌", "AEB 장착 시 추돌 약 26.5%·보행자 약 28.1% 낮음(보도 기준) → 기술 효과의 국내 근거",
  "보험사 분석은 보도자료 — 원보고서 확인 필요, 모델별 노출 차이", "LIB-KNCAP (9601~) 또는 참고문헌만", "아시아경제 2026-03-24 보도(삼성화재 분석)", "보도 확인(원문 확인 필요)"),
 (2, "교통사고다발지역 (전국 표준데이터·보행노인·보행어린이 다발지역 API)", "도로교통공단 / 공공데이터포털", "API·CSV(좌표·폴리곤)", "연 · 지점",
  "연도·시도·시군구·위경도", "7207 보호구역 어린이·7255 보행노인 시군구", "위험 지점 지도, 지점 단위 EB 전후 비교·BYM2 공간 모형의 기반",
  "다발지역만(전체 사고 아님) — 선택 편향", "LIB-GIS (9701~, 지도 탭 신설 시)", "data.go.kr 15029185·15057666·15058925", "존재 확인"),
 (2, "교통문화지수 (안전띠·신호준수·횡단보도 정지선·스마트폰 사용 등, 지자체별)", "한국교통안전공단(국토교통부 발표)", "보고서·지수", "연 · 229개 지자체",
  "연도·시군구", "시도·시군구 사고 장표", "행동 지표 ↔ 사고율 (원인 후보), 지자체 순위와 사고 순위 비교", "조사 방법 변경 연도 확인 필요", "LIB-MOLIT 확장 (9206~)",
  "국토교통부 보도자료(molit.go.kr), 관련 KCI 논문", "존재 확인"),
 (2, "온라인쇼핑동향 — 음식서비스 거래액", "통계청 KOSIS", "통계표", "월 · 2017~",
  "연월", "9202 이륜차 신고대수·이륜 사고", "배달 수요(노출 대리변수) ↔ 이륜차 사고 — 배달 이륜 논문들이 다루지 못한 전국 노출",
  "거래액 ≠ 주행거리 (대리변수)", "LIB-KOSTAT 확장", "통계청 상시 통계 (작성자 지식)", "연계 방식 확인 필요"),
 (2, "경제활동인구조사 실업률·지역소득 (시도)", "통계청 KOSIS", "통계표", "월·연 · 시도",
  "연도·시도", "전체 사고(1)·시도 사고", "경기 순환 통제 — 실업률 1%p↑ 시 사망 약 2.9%↓(미국, French & Gumus 2021)·OECD 동일 경향(Wegman 외)",
  "한국에서 크기는 미확인 — 논문 주제 후보", "LIB-KOSTAT 확장", "IZA DP14324, Wegman·Allsop 외 원고", "문헌 확인"),
 (2, "기상 관측 (강수·적설·결빙일수, 시도)", "기상청 기상자료개방포털", "API·CSV", "일·월 · 관측소",
  "연월·시도", "7105 기상상태별 월별·7111 노면상태별", "'비 오는 날 사고'를 비 오는 날 수로 나눈 기상 노출 사고율",
  "관측소→시도 집계 방식 정해야", "LIB-KMA (9801~)", "기상청 공개 자료 (작성자 지식)", "연계 방식 확인 필요"),
 (3, "유가(휘발유·경유) 월평균", "한국석유공사 오피넷", "통계", "월 · 전국·시도", "연월", "전체 사고(1)·주행거리(9205)",
  "주행량 대리변수 — 주행거리 자료가 없는 2005~2011 보완", "간접 지표", "LIB-MOTIE (9811~)", "오피넷 공개 통계 (작성자 지식)", "연계 방식 확인 필요"),
 (3, "차령·연식별 자동차 등록대수", "국토교통부 통계누리 / KOSIS", "통계표", "연 · 차종·차령", "연도·차종", "9201 등록대수·차량기술 탭",
  "신차 비중 → ADAS 보급률 대리(의무화 연식 이후 차량 비율)", "옵션 장착률은 별도", "LIB-MOLIT 확장 (9207~)", "국토부 등록 통계 (작성자 지식)", "연계 방식 확인 필요"),
 (3, "IRTAD/ITF 국가 프로필 · GBD(IHME) 사망률", "ITF-OECD / IHME", "보고서·데이터 도구", "연 · 국가", "연도·국가·연령",
  "6809~ OECD 장표(2022까지)", "2023~ 국제 비교 갱신, 연령표준화 사망률·DALY(GBD)", "정의·추정 방법이 TAAS와 다름", "LIB-INTL (9901 앞 범위 조정 필요)",
  "ITF Korea Road Safety Country Profile 2023, GBD 2019 논문(IJERPH 2022)", "존재 확인"),
 (3, "교통법규 위반 단속 2019년 이후", "경찰청", "공개 통계(경찰청 정보공개)", "연 · 위반 유형", "연도·위반 유형", "9308(2014~2018) 공백 보완",
  "법규위반별 사고(7052)와 단속 강도 비교", "공개 범위 확인 필요", "LIB-POLICE 확장", "police.go.kr 공개 통계 페이지", "공개 범위 확인 필요"),
]
LIB_NOT = [
 ("SNS·검색량(예: '음주운전' 검색 추이)", "관심도와 행동의 관계가 불분명 — 상관이 나와도 해석 근거가 약함"),
 ("카드 매출·유동인구 단기 자료", "기간이 짧고(대부분 2019~) 연 단위 사고와 축이 맞지 않음"),
 ("개별 차량 텔레매틱스", "표본 대표성·개인정보 문제, 공개 자료 아님"),
 ("지역 축제·행사 일정", "연 단위 사고에 영향이 작고 수집 비용이 큼"),
]

# ───────────────────────── ⑤ 논문 ─────────────────────────
PAPER_COLS = ["번호", "주제", "제목", "저자", "학술지·발행", "연도", "자료·기간", "방법", "핵심 결과", "이 프로젝트와의 연결 (장표)", "원문 공개", "링크", "PDF(공개본)", "확인"]
PAPERS = [
 ("자동차", "Effectiveness of forward collision warning and autonomous emergency braking systems in reducing front-to-rear crash rates", "Cicchino JB",
  "Accident Analysis & Prevention", 2017, "미국 22개 주 경찰 보고 사고, 2010~2014 (보험 차량-연)", "포아송 회귀(같은 모델의 장착/미장착 비교)",
  "추돌(가해) 사고율: FCW 단독 −27%, 저속 AEB −43%, FCW+AEB −50%. 부상 추돌 −20%/−45%/−56%", "차량기술 매핑 탭(AEB), 7002 사고유형(추돌)",
  "유료(학술지)", "https://www.iihs.org/research-areas/bibliography/ref/2111", "", "IIHS 서지 페이지 확인"),
 ("자동차", "Effects of automatic emergency braking systems on pedestrian crash risk", "Cicchino JB", "Accident Analysis & Prevention", 2022,
  "미국 경찰 보고 사고 (보험 차량-연)", "포아송 회귀 + 준유도 노출(로지스틱)", "보행자 사고 위험 −25~27%, 보행자 부상 사고 −29~30%. 가로등 없는 야간·제한속도 50mph 이상·회전 중에는 효과 근거 없음",
  "보행자 사고(7285)·야간 — 국내 야간 보행 사고에 기술 한계 시사", "유료(학술지)", "https://iihs.org/topics/bibliography/ref/2243", "", "IIHS 서지 페이지 확인"),
 ("자동차", "KNCAP ADAS 평가 점수별 실제 사고율 분석 (보도)", "삼성화재 교통안전문화연구소", "보도자료(아시아경제 보도)", 2026,
  "사고 약 83만 건 2018~2024, KNCAP 평가 121개 차종(2013~2023)", "장착·점수 구간별 사고율 비교", "AEB 장착 시 추돌 약 26.5%·보행자 충돌 약 28.1% 낮음, BSD 고득점은 저득점보다 약 45.8% 낮음",
  "차량기술 매핑 탭의 국내 근거", "보도(원보고서 미확인)", "https://view.asiae.co.kr/en/article/2026032410335170944", "", "보도 확인"),
 ("자동차", "플랫폼 기반 배달 이륜차 교통사고 영향요인 분석 (Analysis on Factors Contributing to Motorcycle Accidents of Food Delivery Riders)", "이상준·박준태",
  "한국안전학회지 37(1)", 2022, "배달 라이더 554명 설문, 2020-11", "포아송 회귀, CHAID", "경력 1년 미만 연 약 2.3건 vs 4년 이상 약 1.2건. 운행 중 콜 수락·강제 배정·다중 플랫폼이 사고 증가 요인",
  "9202 이륜차 신고대수·이륜 사고 — 노출(배달량) 변수 필요성", "공개(KoreaScience)", "https://koreascience.kr/article/JAKO202213841426196.pdf", "https://koreascience.kr/article/JAKO202213841426196.pdf", "원문 확인"),
 ("자동차", "종사상 지위별 음식 배달 종사자의 이륜차 산업재해 특성 분석", "문병두·이수동·정기효", "한국안전학회지 37(6) doi:10.14346/JKOSOS.2022.37.6.118", 2022,
  "산재 승인 6,367건 2020~2021 + 기상청 자료", "카이제곱·이원분산분석", "경력 3개월 미만에서 약 64% 발생, 겨울 30.7%, 수도권 눈 오는 날 하루 12.7건 vs 맑은 날 5.3건",
  "7105 기상상태별·이륜 — 기상 노출 라이브러리 근거", "공개(KoreaScience)", "https://koreascience.kr/article/JAKO202209636294773.pdf", "https://koreascience.kr/article/JAKO202209636294773.pdf", "원문 확인"),
 ("자동차", "Changes in incidence and severity of commercial motorcycle accidents due to the use of delivery service platforms in Korea: a retrospective cohort study",
  "Moon D, Jang JH, Cho JS, et al.", "Journal of Trauma and Injury 36(2)", 2023, "EDIIS 응급실 8,123명 2011~2020", "다변량 로지스틱(EMR-ISS 중증도)",
  "2016~2020 사고가 2011~2015보다 중증 OR 1.49, 중환자실·사망 OR 2.59", "이륜 사고 심각도(사망/사고 비)", "공개(KoreaScience)", "https://koreascience.kr/article/JAKO202321961157934.pdf", "https://koreascience.kr/article/JAKO202321961157934.pdf", "원문 확인"),
 ("교통", "Do Speed Limit Reductions Help Road Safety? Lessons from the Republic of Korea's Recent Move to Lower Speed Limit on Urban Roads", "Mitra S, Job S, Han S, Eom K",
  "World Bank GRSF · 한국교통연구원", 2021, "대구 사고 2013~2018(전후 3년), 울산 통행시간 측정", "비교군 전후 비교(Hauer)",
  "총사고 −4.2%, 사망 −15.2%, 보행자 사망 −30.4%(3년 6명). 통행시간 영향 작음. 실제 속도 자료 없음", "⑤ 중단 시계열 2021, 9306 카메라", "공개(PDF)",
  "https://www.globalroadsafetyfacility.org/sites/default/files/2023-10/Do-Speed-Limit-Reductions-Help-Road-Safety-Lessons-from-the-Republic-of-Koreas-Recent-Move-to-Lower-Speed-Limit-on-Urban-Roads.pdf",
  "https://www.globalroadsafetyfacility.org/sites/default/files/2023-10/Do-Speed-Limit-Reductions-Help-Road-Safety-Lessons-from-the-Republic-of-Koreas-Recent-Move-to-Lower-Speed-Limit-on-Urban-Roads.pdf", "원문 확인"),
 ("교통", "Impact of lowering the maximum speed limit of city roads on pedestrian traffic accident patients: A nationwide before-and-after study", "Lee HG, Kim JH",
  "PLoS ONE doi:10.1371/journal.pone.0325320", 2025, "전국 보행자 사고 환자, 5030(2021-04-17) 전후", "전국 전후 비교", "수치는 원문 확인 필요(초록 일부만 확인)",
  "보행자 사고(7285)·⑤ 중단 시계열 2021", "공개(CC BY, PMC12157059)", "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12157059/", "https://doi.org/10.1371/journal.pone.0325320", "서지 확인(수치 미확인)"),
 ("교통", "Assessing the impact and implications of the revised Act on the Aggravated Punishment of Specific Crimes in preventing child traffic injuries in school zones in Korea: an interrupted time series analysis",
  "(저자 표기 원문 확인 필요)", "Epidemiology and Health 46", 2024, "TAAS 2017~2022 (월)", "중단 시계열", "보호구역 중상 월 11→8건(p=0.017), 어린이 전체 부상 위험비 0.987(95% CI 0.977–0.997)",
  "7196·7207 어린이·보호구역 — 같은 TAAS 자료로 재현 가능", "공개(PMC11099565)", "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11099565/", "", "서지·결과 확인(저자 미확인)"),
 ("교통", "Effect of Lowering the Blood Alcohol Concentration Limit to 0.03 Among Hospitalized Trauma Patients in Southern Taiwan: A Cross-Sectional Analysis",
  "Huang CY, Chou SE, Su WT, et al.", "Risk Management and Healthcare Policy 13:571–581 doi:10.2147/RMHP.S250734", 2020, "대만 외상센터, 2013 기준 강화 전후 각 2년",
  "교차분석·오즈비", "음주 외상환자 12.4%→7.1%, 입원 비용 약 40% 감소 (대만 사례 — 한국 2019 0.03% 비교 근거)", "7159 음주·⑤ 중단 시계열 2019", "공개(CC BY-NC)",
  "https://pmc.ncbi.nlm.nih.gov/articles/PMC7305841", "https://pmc.ncbi.nlm.nih.gov/articles/PMC7305841/pdf/rmhp-13-571.pdf", "원문 확인"),
 ("교통", "How did the economic recession (2008-2010) influence traffic fatalities in OECD-countries?", "Wegman F, Allsop R, Antoniou C, et al.", "ITF/IRTAD 보고 기반 논문(수락 원고)", 2017,
  "유럽 30개국 1975~2011 등 3개 분석 + 41개 선행연구", "음이항·상태공간·메타분석", "모든 국가에서 불황기 사망 감소가 추세보다 빠름. 감소의 큰 몫은 주행량 감소보다 km당 사망률 하락",
  "경기 변수(실업률) 라이브러리 근거, 2008·2020 해석", "공개(UCL 수락 원고)", "https://discovery-pp.ucl.ac.uk/10124562/1/Allsop_accepted%20manuscript%20of%20Wegman%20Allsop%20et%20al%202017.pdf",
  "https://discovery-pp.ucl.ac.uk/10124562/1/Allsop_accepted%20manuscript%20of%20Wegman%20Allsop%20et%20al%202017.pdf", "원문 확인"),
 ("교통", "Death on the Job: The Great Recession and Work-Related Traffic Fatalities", "French MT, Gumus G", "IZA Discussion Paper 14324", 2021, "미국 FARS 주×분기 2004~2012",
  "고정효과 회귀", "실업률 1%p↑ → 업무 관련 사망 −4.7%, 전체 −2.9%, 음주 관련 −3.6%", "사업용(7040 차량용도)·경기 변수", "공개(PDF)", "https://docs.iza.org/dp14324.pdf", "https://docs.iza.org/dp14324.pdf", "원문 확인"),
 ("교통", "Global impact of COVID-19 pandemic on road traffic collisions", "Yasin YJ, Grivna M, Abu-Zidan FM", "World Journal of Emergency Surgery 16:51 doi:10.1186/s13017-021-00395-8", 2021,
  "2021-06까지 문헌·보고", "서술적 문헌고찰", "2020-04 도로 사망 36개국 중 32개국 감소, 연간 42개국 중 33개국 감소. 건수는 줄고 심각도는 증가(과속·빈 도로)",
  "외부 충격(2020) 더미, 사망/사고 비", "공개(CC BY)", "https://pmc.ncbi.nlm.nih.gov/articles/PMC8478263", "https://pmc.ncbi.nlm.nih.gov/articles/PMC8478263/pdf/13017_2021_Article_395.pdf", "원문 확인"),
 ("안전", "Comparison of traffic collision victims between older and younger drivers in South Korea: Epidemiologic characteristics, risk factors and types of collisions",
  "Ahn JY, Ryoo HW, Park JB, et al.", "PLoS ONE 14(4):e0214205 doi:10.1371/journal.pone.0214205", 2019, "EDIIS 응급실 운전자 37,511명 2011~2015", "포아송·선형 회귀, CMH·카이제곱",
  "부상 운전자 중 고령 비중 5.0%→8.4%, 단독사고 25.9% vs 20.3%, 안전띠 79.0% vs 83.0%, 병원 내 사망 1.8% vs 0.7%", "7266 노인운전자·7269 사고유형", "공개(CC BY)",
  "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6456194/", "https://pmc.ncbi.nlm.nih.gov/articles/PMC6456194/pdf/pone.0214205.pdf", "원문 확인"),
 ("안전", "고령운전자 연령구간별 사망사고 발생위험도와 사고비용 분석 연구 (Study on Fatality Risk of Older Driver and Traffic Accident Cost)", "최재성", "한국안전학회지 33(4):111–118", 2018,
  "도로교통공단 법규위반 사망 자료 2011~2015(약 8.9만 건)", "로짓(최우추정)", "65세 이상 운전자 관련 사망 586→776명(+32.5%), 80세 이상에서 차로위반 사망 오즈 약 2.24배",
  "7266 노인운전자·7052 법규위반 — 연령 구간 세분화 근거", "공개(KoreaScience)", "https://koreascience.kr/article/JAKO201829562508985.pdf", "https://koreascience.kr/article/JAKO201829562508985.pdf", "원문 확인"),
 ("안전", "Revisiting Older Drivers' Risks of At-fault Motor Vehicle Collisions in Japan", "Ichikawa M, Inada H, Nakahara S", "Journal of Epidemiology 34(6):295–300 doi:10.2188/jea.JE20230217", 2024,
  "일본 경찰 보고 사고 2016~2020", "면허 소지자당 가해 사고율, 사고당 피해자 수", "고령 운전자 가해 사고율은 중년보다 높지만 청년보다는 낮음. 고령 가해 사망사고의 사망자는 주로 본인·동승자",
  "분모 바꿔 보기(면허 소지자 6863), 노인운전자 장표", "공개(CC BY)", "https://www.jstage.jst.go.jp/article/jea/34/6/34_JE20230217/_article", "https://www.jstage.jst.go.jp/article/jea/34/6/34_JE20230217/_pdf", "원문 확인"),
 ("출생률·인구", "Predicting road casualties in Flanders in relation to an ageing population: combining decomposition and disaggregation", "Van Hout K, Brijs T, Daniels S, Hermans E, Wets G",
  "Hasselt Univ. IMOB 원고(TRB 제출)", 2012, "벨기에 플랑드르 인구 표본·통행조사·사상자 1997~2009, 전망 2010~2020", "노출(인구×통행거리)·위험 분해, 로짓 가중치 갱신",
  "위험이 그대로면 고령화로 사상자 약 +8%, 실제 전망은 위험 감소로 −57%. 고령 여성 비중 약 2배", "율 분해 기법, 9101 연령별 인구·장래추계 라이브러리", "공개(원고)",
  "https://documentserver.uhasselt.be/bitstream/1942/15173/1/vanhoutTRB%20paper.pdf", "https://documentserver.uhasselt.be/bitstream/1942/15173/1/vanhoutTRB%20paper.pdf", "원문 확인"),
 ("출생률·인구", "Pregnancy and the risk of a traffic crash", "Redelmeier DA, May SC, Thiruchelvam D, Barrett JFR", "CMAJ 186(10) doi:10.1503/cmaj.131650", 2014,
  "캐나다 온타리오 출산 여성 (임신 전·중·후 비교)", "자기 대조 설계", "임신 2분기 중대 사고 위험 증가 보고 — 수치는 원문 확인 필요", "출생률 주제와 교통안전의 연결 고리(직접 자료는 없음)",
  "공개(CMAJ)", "https://www.cmaj.ca/content/186/10/733", "", "검색 결과로 서지 확인(수치 미확인)"),
 ("출생률·사망률", "Trends in mortality from road traffic injuries in South Korea, 1983-2017: Joinpoint regression and age-period-cohort analyses", "Eun SJ",
  "Accident Analysis & Prevention 134:105325 doi:10.1016/j.aap.2019.105325", 2020, "사망신고·센서스 추계인구 1983~2017", "조인포인트, APC(내재추정)",
  "J자형 연령 효과(65세 이상 급증), 1938~1943 출생 코호트 정점 후 감소, 1978~1983 출생 세대 위험 상대적으로 높음", "7344 연령별·APC 기법·사망원인 라이브러리", "유료(학술지)",
  "http://www.ncbi.nlm.nih.gov/pubmed/31706185", "", "초록 확인"),
 ("사망률", "Global, Regional, and National Burden of Road Injuries from 1990 to 2019", "Xu Y, Chen M, Yang R, et al.", "IJERPH 19(24):16479 doi:10.3390/ijerph192416479", 2022,
  "GBD 2019, 1990~2019", "연령표준화율, EAPC", "세계 연령표준화 사망률 21.92→14.99/10만(EAPC −1.29), 발생은 63.3% 증가", "6809~ OECD 장표·국제 라이브러리", "공개(CC BY)",
  "https://mdpi.com/1660-4601/19/24/16479", "https://www.mdpi.com/1660-4601/19/24/16479/pdf", "원문 확인"),
 ("사망률", "Road traffic injury mortality and morbidity by country development status, 2011-2017", "He JY, Xiao WX, Schwebel DC, et al.", "Chinese Journal of Traumatology 24(2):88–93 doi:10.1016/j.cjtee.2021.01.007", 2021,
  "GBD 2017 + WHO 보고, 2011~2017", "조인포인트(AAPC)", "모든 SDI 집단에서 연령보정 사망률 감소(고-중 SDI −2.7%/년 최대)", "조인포인트 기법", "공개(CC BY-NC-ND)",
  "https://pmc.ncbi.nlm.nih.gov/articles/PMC8071733", "https://pmc.ncbi.nlm.nih.gov/articles/PMC8071733/pdf/main.pdf", "원문 확인"),
 ("사망률", "Examining Road Traffic Mortality Status in China: A Simulation Study", "Huang H, Yin Q, Schwebel DC, et al.", "PLoS ONE 11(4):e0153251 doi:10.1371/journal.pone.0153251", 2016,
  "중국 경찰 1970~2013·보건 2002~2013, OECD 13개국", "수정 Smeed 식", "경찰 자료는 2002 정점, 보건 자료는 2012 정점 — 경찰 자료 과소보고 가능성", "분모 바꿔 보기·삼각검증 기법",
  "공개(CC BY)", "https://pmc.ncbi.nlm.nih.gov/articles/PMC4829231", "https://pmc.ncbi.nlm.nih.gov/articles/PMC4829231/pdf/pone.0153251.pdf", "원문 확인"),
 ("사망률", "Korea: Road Safety Country Profile 2023", "ITF-OECD (IRTAD)", "ITF 국가 프로필", 2023, "한국 2012~2022", "기술 통계",
  "2022 사망 2,735명(2012 대비 −49.3%), 인구 10만 명당 5.3명, 보행자 35%·이륜 25%, 75세 이상 사망률 일반의 약 4배", "1 주요 교통지표·OECD 장표 검증", "공개(PDF)",
  "https://www.itf-oecd.org/sites/default/files/korea-road-safety.pdf", "https://www.itf-oecd.org/sites/default/files/korea-road-safety.pdf", "원문 확인"),
]
GAPS = [
 ("출생률 × 교통안전", "출생률(저출산)과 교통사고를 직접 연결한 통계 연구는 이번 검색에서 찾지 못함. 인구 고령화 전망(Van Hout)·코호트 효과(Eun 2020)·임신 중 위험(Redelmeier)만 간접적",
  "어린이 사고 감소의 몇 %가 어린이 수 감소(출생률) 때문인지 아무도 분해하지 않음"),
 ("다중 제도 분리", "국내 제도 효과 연구는 대부분 단일 제도 전후 비교(5030, 민식이법)", "2019~2021에 몰린 윤창호법·민식이법·5030·코로나를 한 모형에서 분리한 연구가 드묾"),
 ("배달 이륜 노출", "배달 이륜 연구는 설문·산재·응급실 표본 중심", "전국 배달량(노출) 대비 이륜 사고율 시계열이 없음"),
 ("ADAS 국내 효과", "국외(IIHS)는 보험·경찰 자료로 정량화, 국내는 보험사 보도자료 수준", "국가 통계(TAAS 사고유형) 수준에서 ADAS 보급과 추돌·보행 사고 비율을 연결한 연구가 드묾"),
 ("자료원 간 차이", "중국은 경찰 vs 보건 자료 차이를 정량화(Huang 2016)", "한국 TAAS·사망원인통계·응급실 자료의 장기 비율 추세 비교는 확인하지 못함"),
 ("경기와 교통사망", "OECD·미국은 실업률 탄력성 추정", "한국(1997·2008·2020 충격)을 다룬 시계열 추정은 확인하지 못함"),
]
TOPICS = [
 (1, "저출산·고령화가 교통사고 통계에 미친 영향의 분해 — 2005~2025 한국, 2040 전망", "출생률·사망률",
  "사망·사상 감소 중 '연령별 위험 감소' 몫과 '인구구조(어린이 감소·노인 증가)' 몫을 분해하고, 장래인구추계로 2040년 고령 사고를 전망",
  "율 분해(Das Gupta) + APC + 장래추계 시나리오", "7344·7196·7240 + 9101·9102 (있음), 장래인구추계·사망원인통계(추가)", "높음 — 핵심 자료 대부분 보유", "국내 공백(출생률 직접 연결 연구 미확인) + 정책 시사점 분명",
  "Accident Analysis & Prevention / 한국안전학회지 / 대한교통학회지"),
 (2, "2019~2021 교통안전 제도 묶음의 효과 분리 — 베이지안 구조 시계열과 음성 대조", "교통",
  "윤창호법(2019)·민식이법(2020)·5030(2021)·코로나(2020)가 겹친 기간에 각 제도의 효과를 공변량·음성 대조·위약 시점으로 분리",
  "BSTS/ITS(월 자료) + 음성 대조 + 위약 시점 + E-value", "7159·7196·7285 월별, 9307·9306·9003, 제도 연표 9901 (있음)", "높음 — 패널 기능 확장으로 가능", "단일 제도 연구들의 한계 보완",
  "Traffic Injury Prevention / Epidemiology and Health / Injury Prevention"),
 (3, "경찰 통계는 얼마나 실제를 반영하나 — TAAS·사망원인통계·응급실 손상 자료의 20년 비교", "사망률·안전",
  "자료원별 사망·중상 규모와 비율 추세를 비교해 과소보고·정의 변화가 추세 해석에 주는 영향을 정량화",
  "삼각검증 + 수정 Smeed 식 + 상태공간", "TAAS (있음) + 통계청 사망원인·질병청 손상(추가)", "중간 — 라이브러리 2개 추가 필요", "중국 연구(Huang 2016)의 한국판, 통계 신뢰도 기초 연구",
  "Injury Prevention / Journal of Korean Medical Science"),
 (4, "배달 수요와 이륜차 사고 — 노출 보정 시계열 분석", "자동차·교통",
  "음식서비스 거래액·이륜차 신고대수를 노출로 쓴 이륜 사고율 추세와 계절·기상 효과",
  "음이항 회귀(오프셋) + STL + 기상 노출", "9202 (있음), 온라인쇼핑동향·기상(추가)", "중간", "설문·산재 중심 연구의 전국 단위 보완",
  "한국안전학회지 / Case Studies on Transport Policy"),
 (5, "ADAS 보급과 사고 유형 구성의 변화 — 국가 통계 수준의 준유도 노출 분석", "자동차",
  "연식별 등록(보급 대리)·KNCAP 점수와 추돌·보행 사고 구성비 변화를 연결해 기술 효과의 국가 단위 신호 확인",
  "준유도 노출 + 분모 바꿔 보기 + 변화점 탐지", "7002·7030·7285 (있음), 차령별 등록·KNCAP(추가)", "중간 — 보급률 자료 확보가 관건", "KATECH 차량기술 연구와 직접 연결",
  "SAE / 한국자동차공학회 논문집 / AAP"),
 (6, "경기 순환과 한국 교통사망 — 1997·2008·2020 충격의 비교", "교통·사망률",
  "실업률·유가를 노출 대리로 써서 경기 충격 시기 사망 감소의 몫을 추정하고 OECD 추정치와 비교", "상태공간 + 고정효과(시도 패널)", "1·시도 사고 (있음), 실업률·유가(추가)",
  "중간", "국외 문헌의 한국 미적용 공백", "Accident Analysis & Prevention / 국토연구"),
]

def sheet(wb, title, cols, rows, widths, band_col=None, first=False):
    ws = wb.active if first else wb.create_sheet(title)
    ws.title = title
    ws.append(cols)
    for c in ws[1]:
        c.font = Font(name=F, bold=True, color="FFFFFF", size=10); c.fill = HEAD
        c.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center"); c.border = Border(top=THIN, bottom=THIN, left=THIN, right=THIN)
    for r in rows:
        ws.append(list(r))
    for row in ws.iter_rows(min_row=2):
        fill = None
        if band_col is not None:
            k = row[band_col].value
            if k in BAND: fill = PatternFill("solid", fgColor=BAND[k])
        for c in row:
            c.font = Font(name=F, size=10); c.alignment = Alignment(wrap_text=True, vertical="top"); c.border = Border(top=THIN, bottom=THIN, left=THIN, right=THIN)
            if fill: c.fill = fill
            if isinstance(c.value, str) and c.value.startswith("http"):
                c.hyperlink = c.value; c.font = Font(name=F, size=10, color="1D5FAE", underline="single")
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    import math  # 줄바꿈 높이: 한글 1자 ≈ 너비 1.9, 영문 1자 ≈ 1.1
    for row in ws.iter_rows(min_row=1):
        n = 1
        for c, w in zip(row, widths):
            t = str(c.value or ""); u = sum(1.9 if ord(ch) > 0x2E80 else 1.1 for ch in t)
            n = max(n, math.ceil(u / max(w - 1, 4)))
        ws.row_dimensions[row[0].row].height = min(15 * n + 4, 400)
    ws.freeze_panes = "C2" if len(cols) > 4 else "A2"
    ws.auto_filter.ref = ws.dimensions
    ws.sheet_view.zoomScale = 90
    return ws

def readme(ws, lines):
    for ln in lines:
        ws.append([ln])
    ws.column_dimensions["A"].width = 120
    for i, row in enumerate(ws.iter_rows(), 1):
        for c in row:
            c.font = Font(name=F, size=11 if i == 1 else 10, bold=(i == 1)); c.alignment = Alignment(wrap_text=True, vertical="top")

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--version", default="v1.0"); a = ap.parse_args(); v = a.version
    OUT.mkdir(parents=True, exist_ok=True); outs = []
    # ③
    wb = Workbook(); ws = wb.active; ws.title = "읽는 법"
    readme(ws, [f"분석 기법 제안 목록 {v} — REQ-20261127-01 ③ (적용 전 검토용)", "분류: SOTA = 최근 표준이 된 인과·시계열·공간 기법 / 고신뢰 = 교통안전·역학에서 검증된 표준 / 역발상 = 결론을 반증·뒤집어 보는 점검 기법",
        "패널 반영 우선순위: 1 = 지금 자료로 바로 가능하고 효과 큼 · 2 = 자료 일부 추가 또는 구현 중간 · 3 = 새 자료(시군구 시행 시점·1세 단위 등) 필요",
        "'지금 패널과의 관계'는 현재 통계 기법 탭(① 추세·변곡점 ② 시차상관·그레인저 ③ 다중회귀 ④ 주성분·군집 ⑤ 중단 시계열)과 어떻게 이어지는지",
        "출처 확인: '웹 확인' = 이번 조사에서 원문·서지 페이지를 직접 확인 / '기억(DOI 확인 권장)' = 작성자가 아는 표준 문헌 — 인용 전에 DOI를 한 번 확인하세요",
        "적용 방식은 아직 정하지 않았습니다 — 고르신 기법만 패널에 넣습니다(결과 행 13열 형식은 열 추가만)."])
    sheet(wb, "기법 목록", TECH_COLS, [(i + 1,) + t for i, t in enumerate(TECH)], [6, 8, 26, 34, 38, 44, 40, 22, 34, 7, 9, 26, 40, 14], band_col=1)
    f = OUT / f"분석기법_제안목록_{v}.xlsx"; wb.save(f); outs.append(f)
    # ④
    wb = Workbook(); ws = wb.active; ws.title = "읽는 법"
    readme(ws, [f"추가 라이브러리 제안 {v} — REQ-20261127-01 ④", "기준: 지금 원천(TAAS·통계청·행안부·국토부·경찰청·제도 연표)과 공통 축(연도·시도·연령·차종)이 실제로 맞고, 함께 인용했을 때 결론을 검증하거나 노출(분모)을 보완하는 자료만",
        "우선순위 1 = 지금 결론의 신뢰도를 바로 높임 · 2 = 새 분석 주제를 엶 · 3 = 보조·장기", "새 라이브러리(안)의 번호 범위는 제안이며, 추가할 때 CLAUDE.md 장표 번호 규칙에 맞춰 확정합니다.",
        "확인 상태: '존재 확인' = 이번에 공개 페이지를 확인 / '연계 방식 확인 필요' = 존재는 알려져 있으나 표 구성·API는 수집 때 확인", "'넣지 않는 것이 나은 자료' 시트: 억지로 붙이면 해석이 흐려지는 자료"])
    sheet(wb, "추가 제안", LIB_COLS, LIBS, [8, 34, 24, 18, 22, 18, 30, 44, 30, 22, 34, 16])
    sheet(wb, "넣지 않는 것이 나은 자료", ["자료", "이유"], LIB_NOT, [40, 80])
    f = OUT / f"추가라이브러리_제안_{v}.xlsx"; wb.save(f); outs.append(f)
    # ⑤
    wb = Workbook(); ws = wb.active; ws.title = "읽는 법"
    readme(ws, [f"논문 조사 요약 {v} — REQ-20261127-01 ⑤ (자동차·교통·안전·출생률·사망률 × 통계 분석)", "검색: 2026-11-27 웹 검색. 각 논문은 원문 또는 서지 페이지에서 제목·자료·방법·결과를 확인했고, 확인하지 못한 부분은 '확인' 열에 적었습니다.",
        "출생률 주제는 직접 연결한 통계 연구를 찾지 못해 인구구조·코호트·임신 관련 간접 연구로 채웠습니다 — '연구 공백' 시트 참고.",
        "원문 공개: 공개 PDF가 있는 논문만 'PDF(공개본)' 열에 링크 — zip 에는 PC 브라우저로 받은 공개 PDF를 넣습니다(유료 논문은 링크만).",
        "시트: 논문 목록 · 주제별 요약 · 연구 공백 · 논문 주제 제안"])
    sheet(wb, "논문 목록", PAPER_COLS, [(i + 1,) + p for i, p in enumerate(PAPERS)], [6, 10, 46, 24, 30, 7, 30, 24, 50, 32, 14, 36, 36, 16])
    summ = []
    for t in ["자동차", "교통", "안전", "출생률·인구", "출생률·사망률", "사망률"]:
        ps = [p for p in PAPERS if p[0] == t]
        if ps: summ.append((t, len(ps), " / ".join(f"{p[3]} ({p[4]})" for p in ps)))
    SUMTXT = {"자동차": "AEB 등 ADAS는 미국 실사고에서 추돌 27~50%·보행자 25~30% 감소, 국내는 보험사 분석이 비슷한 방향. 배달 이륜은 경력·플랫폼 배정 방식·기상이 사고·중증도와 연관",
              "교통": "5030·민식이법·음주 기준 강화 모두 전후 비교에서 감소 방향이나 대부분 단일 제도·짧은 기간. 경기 불황·코로나는 사고 수를 줄이고 심각도는 높이는 공통 패턴",
              "안전": "고령 운전자는 단독사고·안전띠 미착용·병원 내 사망이 높고, 80세 이상에서 위험이 급증. 일본은 면허 소지자 기준으로 보면 청년보다 낮은 가해율 — 분모 선택이 결론을 좌우",
              "출생률·인구": "고령화는 위험이 그대로면 사상자를 늘림(벨기에 +8%). 임신 중 운전 위험 증가 보고. 출생률 자체를 다룬 교통 통계 연구는 미확인",
              "출생률·사망률": "한국 교통사망은 J자형 연령 효과와 출생 코호트 효과(1938~43 정점)가 뚜렷 — 세대 구성 변화가 장기 추세에 기여",
              "사망률": "세계 연령표준화 사망률은 1990~2019 약 32% 감소, 한국은 2012~2022 절반 감소. 경찰 자료는 과소보고 가능 — 보건 자료와 대조 필요"}
    sheet(wb, "주제별 요약", ["주제", "논문 수", "논문", "요약"], [(a, b, c, SUMTXT.get(a, "")) for a, b, c in summ], [14, 8, 70, 80])
    sheet(wb, "연구 공백", ["영역", "기존 연구에서 확인한 것", "남아 있는 공백"], GAPS, [18, 70, 70])
    sheet(wb, "논문 주제 제안", ["추천 순위", "가제", "주제", "연구 질문", "방법", "자료 (보유/추가)", "실현 가능성", "기여", "투고 후보"], TOPICS, [8, 46, 12, 54, 34, 44, 18, 36, 30])
    f = OUT / f"논문_조사요약_{v}.xlsx"; wb.save(f); outs.append(f)
    sys.path.insert(0, str(ROOT / "_source" / "build" / "template")); import office_check
    r = office_check.run([str(p) for p in outs])
    print("saved", *[o.relative_to(ROOT) for o in outs], sep="\n  ")

if __name__ == "__main__":
    main()
