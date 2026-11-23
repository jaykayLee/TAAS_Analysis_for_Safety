import pandas as pd, numpy as np, json, warnings; warnings.filterwarnings('ignore')
import pymannkendall as mk, statsmodels.api as sm
D=pd.read_csv('child_dataset.csv',index_col=0)
R={}
pop=D.child_pop; veh=D.vehicles
for t in ['all','ped','v2v','single']:
    D[f'{t}_acc_rate']=D[f'{t}_acc']/pop*1e5        # 어린이 10만 명당 사고
    D[f'{t}_cas_rate']=(D[f'{t}_death']+D[f'{t}_inj'])/pop*1e5
    D[f'{t}_death_rate']=D[f'{t}_death']/pop*1e5     # 10만 명당 사망 (패널 비율 환산과 같은 단위)
    D[f'{t}_fatal']=D[f'{t}_death']/D[f'{t}_acc']*100 # 치사율(사고 100건당 사망)
    D[f'{t}_serious_share']=D[f'{t}_serious']/(D[f'{t}_inj']+D[f'{t}_death'])*100
    D[f'{t}_acc_per_veh']=D[f'{t}_acc']/veh*1e5      # 자동차 10만 대당
D['child_share_all']=D.all_acc/D.total_acc*100
D['child_ped_share_ped']=D.ped_acc/D.total_ped_acc*100
D['ped_share_child']=D.ped_acc/D.all_acc*100
D['sz_per_zone']=D.sz_all_acc/D.school_zones*100
D.to_csv('child_metrics.csv',encoding='utf-8-sig')
def cagr(a,b,n): return ((b/a)**(1/n)-1)*100
summ={}
for col in ['all_acc','ped_acc','v2v_acc','single_acc','all_death','ped_death','v2v_death','child_pop','vehicles','all_acc_rate','ped_acc_rate','v2v_acc_rate','all_death_rate','ped_death_rate','v2v_death_rate','all_acc_per_veh','ped_acc_per_veh','v2v_acc_per_veh','all_fatal','ped_fatal','v2v_fatal','child_share_all','child_ped_share_ped','ped_share_child','sz_all_acc']:
    a,b=D[col][2005],D[col][2025]
    summ[col]={'2005':round(a,3),'2019':round(D[col][2019],3),'2025':round(b,3),'chg%':round((b/a-1)*100,1),'CAGR%':round(cagr(a,b,20),2) if a>0 and b>0 else None}
R['summary']=summ
# 3-year averages for deaths (small counts)
def avg(col,y0,y1): return D.loc[y0:y1,col].mean()
R['death_3yr']={k:{'2005-07':round(avg(k,2005,2007),1),'2023-25':round(avg(k,2023,2025),1)} for k in ['all_death','ped_death','v2v_death']}
# Mann-Kendall & Pettitt
def pettitt(x):
    x=np.asarray(x); n=len(x); U=[sum(np.sign(x[j]-x[i]) for i in range(t+1) for j in range(t+1,n)) for t in range(n-1)]
    t=int(np.argmax(np.abs(U))); K=abs(U[t]); return t, min(1,2*np.exp(-6*K**2/(n**3+n**2)))
trend={}
for col in ['ped_acc_rate','v2v_acc_rate','single_acc_rate','all_acc_rate','ped_death_rate','v2v_death_rate','ped_fatal','v2v_fatal','ped_share_child','child_ped_share_ped','all_acc_per_veh']:
    s=D[col].dropna(); r=mk.original_test(s.values); sen=mk.sens_slope(s.values)
    t,pp=pettitt(s.values)
    trend[col]={'tau':round(r.Tau,3),'p':float(f"{r.p:.2g}"),'sen_per_yr':round(sen.slope,4),'pct_per_yr':round(sen.slope/np.median(s)*100,2),'change_year':int(s.index[t+1]),'pettitt_p':float(f"{pp:.2g}"),
                'mean_before':round(s.iloc[:t+1].mean(),3),'mean_after':round(s.iloc[t+1:].mean(),3)}
R['trend']=trend
# 분해: ln(사고 변화) = ln(인구 변화) + ln(인구당 비율 변화)
dec={}
for t in ['all','ped','v2v']:
    tot=np.log(D[f'{t}_acc'][2025]/D[f'{t}_acc'][2005]); popc=np.log(pop[2025]/pop[2005]); ratec=tot-popc
    dec[t]={'total_ln':round(tot,3),'pop_part%':round(popc/tot*100,1),'rate_part%':round(ratec/tot*100,1),'acc_chg%':round((np.exp(tot)-1)*100,1)}
R['decomp']=dec
# 중단 시계열 2020 (민식이법 2020.3, 코로나 등교 중단 동시) — 비율(어린이 10만 명당)
def its(col,T=2020,y0=2005,y1=2025,log=True):
    s=D[col].loc[y0:y1].dropna(); y=np.log(s.values) if log else s.values; yr=s.index.values
    X=np.column_stack([yr-yr[0],(yr>=T).astype(float),np.where(yr>=T,yr-T,0)]); m=sm.OLS(y,sm.add_constant(X)).fit()
    from statsmodels.stats.stattools import durbin_watson
    return {'level_chg%':round((np.exp(m.params[2])-1)*100,1),'p_level':round(m.pvalues[2],4),'slope_pre%/yr':round((np.exp(m.params[1])-1)*100,2),
            'slope_post%/yr':round((np.exp(m.params[1]+m.params[3])-1)*100,2),'p_slope':round(m.pvalues[3],4),'r2':round(m.rsquared,3),'dw':round(durbin_watson(m.resid),2),'n':len(s)}
R['its2020']={c:its(c) for c in ['ped_acc_rate','v2v_acc_rate','all_acc_rate','child_ped_share_ped']}
R['its2020_sz']=its('sz_all_acc',y1=2024)
# 회귀 1: 노출 탄력성  ln(사고) = a + b ln(어린이 인구) + c ln(자동차) (+ 코로나 더미)
def ols(y,Xd,names):
    X=sm.add_constant(np.column_stack(Xd)); m=sm.OLS(y,X).fit()
    from statsmodels.stats.outliers_influence import variance_inflation_factor as vif
    v=[round(vif(X,i),1) for i in range(1,X.shape[1])]
    return {'coef':{n:round(b,3) for n,b in zip(['const']+names,m.params)},'p':{n:float(f"{p:.2g}") for n,p in zip(['const']+names,m.pvalues)},'r2':round(m.rsquared,3),'adj_r2':round(m.rsquared_adj,3),'vif':dict(zip(names,v)),'n':int(m.nobs),'dw':round(float(sm.stats.stattools.durbin_watson(m.resid)),2)}
cov=pd.Series(((D.index>=2020)&(D.index<=2021)).astype(float),index=D.index)
reg={}
for t in ['ped','v2v']:
    y=np.log(D[f'{t}_acc'])
    reg[f'{t}_exposure']=ols(y.values,[np.log(pop).values,np.log(veh).values,cov.values],['ln어린이인구','ln자동차','코로나20-21'])
# 회귀 2: 인프라 (2009~2024) ln(인구당 보행사고) ~ ln(보호구역) + ln(보행등) + 코로나
m=D.loc[2009:2024]
c2=pd.Series(((m.index>=2020)&(m.index<=2021)).astype(float),index=m.index)
reg['ped_infra_counts']=ols(np.log(m.ped_acc).values,[np.log(m.child_pop).values,np.log(m.school_zones).values,np.log(m.ped_signals).values,c2.values],['ln어린이인구','ln보호구역','ln보행등','코로나20-21'])
reg['ped_infra']=ols(np.log(m.ped_acc_rate).values,[np.log(m.school_zones).values,np.log(m.ped_signals).values,c2.values],['ln보호구역','ln보행등','코로나20-21'])
reg['ped_infra_trend']=ols(np.log(m.ped_acc_rate).values,[np.log(m.school_zones).values,np.log(m.ped_signals).values,c2.values,np.asarray(m.index-2009,dtype=float)],['ln보호구역','ln보행등','코로나20-21','연도추세'])
# 1차 차분 상관 (추세 제거)
fd={}
for a_,b_ in [('ped_acc_rate','ped_signals'),('ped_acc_rate','vehicles'),('v2v_acc_rate','vehicles'),('ped_acc_rate','school_zones'),('all_acc','child_pop')]:
    x=np.log(D[a_]).diff(); y=np.log(D[b_]).diff(); ok=x.notna()&y.notna()
    from scipy.stats import pearsonr
    r,p=pearsonr(x[ok],y[ok]); fd[f'{a_}~{b_}']={'r':round(r,3),'p':round(p,3),'n':int(ok.sum())}
R['firstdiff_corr']=fd
R['reg']=reg
# 보행 세부 유형 구성 (2005 vs 2025)
sub={}
for k in ['cross','road','edge','sidewalk','other']:
    sub[k]={'2005':int(D[f'ped_{k}_acc'][2005]),'2025':int(D[f'ped_{k}_acc'][2025]),'share2005':round(D[f'ped_{k}_acc'][2005]/D.ped_acc[2005]*100,1),'share2025':round(D[f'ped_{k}_acc'][2025]/D.ped_acc[2025]*100,1),
            'death05_07':round(D.loc[2005:2007,f'ped_{k}_death'].sum(),0),'death23_25':round(D.loc[2023:2025,f'ped_{k}_death'].sum(),0)}
R['ped_sub']=sub
json.dump(R,open('results.json','w'),ensure_ascii=False,indent=1,default=float)
print(json.dumps(R,ensure_ascii=False,indent=1,default=float))
