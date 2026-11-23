import json, numpy as np, pymannkendall as mk, statsmodels.api as sm
from statsmodels.tsa.stattools import grangercausalitytests
import warnings; warnings.filterwarnings("ignore")
import sys; P=sys.argv[1] if len(sys.argv)>1 else "out/st"; pool=json.load(open(P+"_pool.json"))
YRS=list(range(2005,2026))
def ser(c): return [c["pts"].get(str(y)) for y in YRS]
def get(rows,**k): return [r for r in rows if all(r.get(a)==b for a,b in k.items())]
bad=0
def chk(lbl,a,b,tol=1e-6):
    global bad
    ok=(a is None and b is None) or (abs(a-b)<=tol*max(1,abs(b)))
    if not ok: bad+=1; print("  MISMATCH",lbl,a,b)
    return ok
# 1 trend
T=json.load(open(P+"_trend.json")); n1=0
for c in pool:
    v=[(y,x) for y,x in zip(YRS,ser(c)) if x is not None]; ys=[a for a,_ in v]; xs=[b for _,b in v]
    r=mk.original_test(xs); 
    js=get(T,대상=c["name"])
    tau=[x for x in js if x["통계량"]=="tau"][0]; z=[x for x in js if x["통계량"]=="Z"][0]
    sl=[x for x in js if x["통계량"]=="기울기(/년)"][0]
    chk("tau "+c["name"][:20],tau["값"],r.Tau); chk("Z",z["값"],r.z); chk("p",tau["p값"],r.p,1e-5)
    # Sen with actual years (gaps): compute directly
    s=np.median([(xs[j]-xs[i])/(ys[j]-ys[i]) for i in range(len(xs)) for j in range(i+1,len(xs))]); chk("sen",sl["값"],s)
    # pettitt
    n=len(xs); U=[sum(np.sign(xs[j]-xs[i]) for i in range(t+1) for j in range(t+1,n)) for t in range(n-1)]; t=int(np.argmax(np.abs(U)))
    cy=[x for x in js if x["통계량"]=="변화 시작 연도"][0]; chk("pettitt",cy["값"],ys[t+1]); n1+=1
print("trend checked",n1)
# 2 lag (diff, L=2): granger rows
L=json.load(open(P+"_lag.json")); n2=0
def dif(a): return [None]+[None if (a[i] is None or a[i-1] is None) else a[i]-a[i-1] for i in range(1,len(a))]
for r in [x for x in L if x["항목"].startswith("Granger") and "행렬" not in x["항목"] and x["값"] not in ("",None)]:
    l=int(r["항목"].split("시차 ")[1].rstrip(")")); Y=dif(ser([c for c in pool if c["name"]==r["대상"]][0])); X=dif(ser([c for c in pool if c["name"]==r["상대"]][0]))
    idx=[i for i in range(len(YRS)) if Y[i] is not None and X[i] is not None]
    # consecutive block (diff of full series → nulls only where gaps); take rows with consecutive years
    arr=np.array([[Y[i],X[i]] for i in idx]); yrs=[YRS[i] for i in idx]
    # statsmodels requires contiguous; check contiguity
    if yrs!=list(range(yrs[0],yrs[-1]+1)): print("  skip noncontig",r["대상"][:20]); continue
    g=grangercausalitytests(arr,maxlag=l)[l][0]["ssr_ftest"]
    chk(f"granger F l{l}",r["값"],g[0],1e-5); chk("granger p",r["p값"],g[1],1e-4); n2+=1
for r in [x for x in L if x["항목"]=="교차상관"][:7]:
    k=int(r["통계량"].split("시차 ")[1].rstrip(")")); Y=dif(ser([c for c in pool if c["name"]==r["대상"]][0])); X=dif(ser([c for c in pool if c["name"]==r["상대"]][0]))
    pr=[(X[i],Y[i+k]) for i in range(len(YRS)) if 0<=i+k<len(YRS) and X[i] is not None and Y[i+k] is not None]
    if len(pr)>2: chk(f"ccf {k}",r["값"],float(np.corrcoef(np.array(pr).T)[0,1])); n2+=1
print("lag checked",n2)
# 3 ols (raw)
O=json.load(open(P+"_ols.json")); co=[r for r in O if r["항목"]=="계수"]; tgt=co[0]["대상"]; xn=[r["상대"] for r in co[1:]]
Yv=ser([c for c in pool if c["name"]==tgt][0]); Xv=[ser([c for c in pool if c["name"]==n][0]) for n in xn]
idx=[i for i in range(len(YRS)) if Yv[i] is not None and all(x[i] is not None for x in Xv)]
m=sm.OLS(np.array([Yv[i] for i in idx]),sm.add_constant(np.array([[x[i] for x in Xv] for i in idx]))).fit()
for j,r in enumerate(co): chk(f"b{j}",r["값"],m.params[j],1e-5); chk(f"p{j}",r["p값"],m.pvalues[j],1e-4)
chk("R2",[r for r in O if r["통계량"]=="R²"][0]["값"],m.rsquared); chk("F p",[r for r in O if r["통계량"]=="F"][0]["p값"],m.f_pvalue,1e-4)
from statsmodels.stats.stattools import durbin_watson; chk("DW",[r for r in O if r["통계량"]=="Durbin-Watson"][0]["값"],durbin_watson(m.resid))
print("ols checked: target",tgt[:30],"X",len(xn),"n",len(idx))
# 4 pca (raw)
Pc=json.load(open(P+"_pca.json")); ev=[r["값"] for r in Pc if r["통계량"]=="고유값"]
cols=[ser(c) for c in pool]; keep=[j for j,c in enumerate(cols) if sum(v is not None for v in c)>=4]
idx=[i for i in range(len(YRS)) if all(cols[j][i] is not None for j in keep)]
M=np.array([[cols[j][i] for j in keep] for i in idx]); M=M[:,M.std(0)>0]
w=np.sort(np.linalg.eigvalsh(np.corrcoef(M.T)))[::-1]
for k,e in enumerate(ev): chk(f"eig{k}",e,max(0,w[k]),1e-6)
print("pca checked", len(ev), "eigs; n",len(idx))
# 5 its (T=2020, raw)
I=json.load(open(P+"_its.json")); n5=0
for c in pool:
    js=get(I,대상=c["name"]); b2=[r for r in js if r["통계량"]=="b2"]
    if not b2: continue
    Tn=int(b2[0]["상대"].split()[1].rstrip("년"))
    v=[(y,x) for y,x in zip(YRS,ser(c)) if x is not None]; ys=np.array([a for a,_ in v]); xs=np.array([b for _,b in v])
    X=np.column_stack([ys-ys[0],(ys>=Tn).astype(float),np.where(ys>=Tn,ys-Tn,0)])
    m=sm.OLS(xs,sm.add_constant(X)).fit()
    chk("its b2",b2[0]["값"],m.params[2],1e-5); chk("its p2",b2[0]["p값"],m.pvalues[2],1e-4)
    b3=[r for r in js if r["통계량"]=="b3"][0]; chk("its b3",b3["값"],m.params[3],1e-5); chk("its p3",b3["p값"],m.pvalues[3],1e-4); n5+=1
print("its checked",n5,"T",Tn)
print("MISMATCHES",bad)
