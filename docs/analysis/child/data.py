import duckdb, pandas as pd, json
LIB=str(__import__("pathlib").Path(__file__).resolve().parents[3] / "library")
c=duckdb.connect(); F=f"read_parquet('{LIB}/parquet/facts.parquet')"
def q(s): return c.sql(s).df()
Y=list(range(2005,2026))
# 1) 어린이 사고 (7199, 시간대 합계)
a=q(f"select year,d1,d2,d3,measure,value from {F} where pid=7199 and d4='합계'")
def grab(d1,d2='합계',d3='합계',m='사고[건]',pid_df=a):
    s=pid_df[(pid_df.d1==d1)&(pid_df.d2==d2)&(pid_df.d3==d3)&(pid_df.measure==m)].set_index('year').value
    return s.reindex(Y)
D=pd.DataFrame(index=Y)
for m,k in [('사고[건]','acc'),('사망[명]','death'),('부상[명]','inj'),('중상자[명]','serious')]:
    D[f'all_{k}']=grab('합계',m=m)
    D[f'ped_{k}']=grab('차대사람',m=m)
    D[f'v2v_{k}']=grab('차대차',m=m)
    D[f'single_{k}']=grab('차량단독',m=m)
for sub,k in [('횡단중','cross'),('차도통행중','road'),('길가장자리구역통행중','edge'),('보도통행중','sidewalk'),('기타','other')]:
    D[f'ped_{k}_acc']=grab('차대사람',sub,sub)
    D[f'ped_{k}_death']=grab('차대사람',sub,sub,'사망[명]')
# 2) 보호구역 내 (7212)
b=q(f"select year,d1,d2,d3,measure,value from {F} where pid=7212 and d4='합계'")
for d1,k in [('합계','all'),('차대사람','ped'),('차대차','v2v')]:
    D[f'sz_{k}_acc']=grab(d1,m='사고[건]',pid_df=b)
D['sz_all_death']=grab('합계',m='사망[명]',pid_df=b)
# 3) 노출·인프라
p=q(f"select year,measure,value from {F} where pid=9001 and d1='전국' and d2='어린이 0~12세'")
D['child_pop']=p[p.measure=='인구_연간보간[명]'].set_index('year').value.reindex(Y)
D['child_pop_measured']=p[p.measure=='인구[명]'].set_index('year').value.reindex(Y)
k=q(f"select year,d1,value from {F} where pid=1 and d2='지표'")
for d1,col in [('자동차등록대수(대)','vehicles'),('교통사고건수(건)','total_acc'),('교통사고사망자(명)','total_death'),('도로연장거리(Km)','road_km')]:
    D[col]=k[k.d1==d1].set_index('year').value.reindex(Y)
s=q(f"select year,value from {F} where pid=19 and d1='신호기' and d2='보행등'"); D['ped_signals']=s.set_index('year').value.reindex(Y)
# 전체 차대사람 사고 (7012 가해차종 합계)
t=q(f"select year,value from {F} where pid=7012 and d1='합계' and d2='차대사람' and d3='합계' and d4='합계' and measure='사고[건]'"); D['total_ped_acc']=t.set_index('year').value.reindex(Y)
# 4) 어린이보호구역 지정 개소 (경찰청 「어린이보호구역 정기보고」, e-나라지표 1616)
SZ={2009:9584,2010:13207,2011:14921,2012:15136,2013:15444,2014:15799,2015:16085,2016:16355,2017:16555,2018:16765,2019:16912,2020:16896,2021:16759,2022:16641,2023:16490,2024:16308}
D['school_zones']=pd.Series(SZ).reindex(Y)
D.index.name='year'
D.to_csv('child_dataset.csv',encoding='utf-8-sig')
print(D[['all_acc','ped_acc','v2v_acc','single_acc','all_death','ped_death','v2v_death','child_pop','vehicles','total_acc','total_ped_acc','sz_all_acc','school_zones','ped_signals','road_km']].to_string())
