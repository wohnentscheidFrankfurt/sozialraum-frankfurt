# Population per survey area (Umfragebezirk) from the single dataset "Leben in Frankfurt 2025":
# income, landlord, origin, education, families, overcrowding. Weighted with `weight`.
# Call: python bez.py <leben-in-frankfurt_2025.csv>
import sys, numpy as np, pandas as pd
df = pd.read_csv(sys.argv[1], sep=';', encoding='utf-8-sig', low_memory=False)
cols=['Umfragebezirk','XDhhnek_a','WOmieig_a','WOverm_a','XDstang_a','XDschabl_a','XDberuf_a','XDgebjahr_a','XDhhform_a','XDhhgr017_a','WOraeu_a','XDhhgrabs_a','WOflae_a','WOkami_a','FFdauliw_a','WOumzpl_ffm','WOumzpl_rm','WOumzpl_brd','WOumzpl_0','WObelko']
d=df[cols].apply(pd.to_numeric, errors='coerce'); d[d<0]=np.nan; d['Umfragebezirk']=pd.to_numeric(df.Umfragebezirk)
d['w']=pd.to_numeric(df.weight.astype(str).str.replace(',','.'))
SURVEY_AREAS={1:'Innenstadt I',2:'Innenstadt II',3:'Innenstadt III',4:'Bornheim/Ostend',5:'Süd',6:'West',7:'Mitte-West',8:'Nord-West',9:'Mitte-Nord',10:'Nord-Ost',11:'Ost',12:'Kalbach/Riedberg',13:'Nord'}
def share(mask, base, w):
    # weighted share in percent of the cases with a value in `base`
    m=base.notna(); return 100*w[m & mask].sum()/w[m].sum()
d['persons']=np.where(d.XDhhform_a==1,1,np.where(d.XDhhform_a==2,2,d.XDhhgrabs_a))
d['over']=np.where(d.WOraeu_a.notna()&pd.notna(d.persons), d.WOraeu_a<d.persons, np.nan)
area_m2={i:25+10*(i-1) for i in range(1,13)}; area_m2[13]=155
rent_by_class={1:350}; rent_by_class.update({i:450+100*(i-2) for i in range(2,12)}); rent_by_class[12]=1550
d['eur_m2']=d.WOkami_a.map(rent_by_class)/d.WOflae_a.map(area_m2)
def weighted_quantile(x,w,q=.5):
    m=x.notna(); x,w=x[m].values,w[m].values
    o=np.argsort(x); c=np.cumsum(w[o])/w[o].sum(); return x[o][np.searchsorted(c,q)]
rows=[]
for k,name in list(SURVEY_AREAS.items())+[(0,'City total')]:
    g=d if k==0 else d[d.Umfragebezirk==k]; w=g.w; r=g[g.WOmieig_a==1]
    inc=g.XDhhnek_a
    rows.append(dict(survey_area=name, n=len(g),
      under1000=share(inc==1,inc,w), b1000_2000=share(inc==2,inc,w), under2000=share(inc<=2,inc,w), from3000=share(inc>=4,inc,w), from4000=share(inc>=5,inc,w),
      tenants=share(g.WOmieig_a==1,g.WOmieig_a,w), public_landlord=share(r.WOverm_a==2,r.WOverm_a,r.w),
      foreign=share(g.XDstang_a==2,g.XDstang_a,w), abitur=share(g.XDschabl_a==4,g.XDschabl_a,w), max_lower_secondary=share(g.XDschabl_a<=2,g.XDschabl_a,w),
      employed=share(g.XDberuf_a==1,g.XDberuf_a,w), from60=share(g.XDgebjahr_a>=5,g.XDgebjahr_a,w),
      with_child=share(g.XDhhform_a.isin([3,4]),g.XDhhform_a,w), single_parent=share(g.XDhhform_a==4,g.XDhhform_a,w),
      overcrowded_tenants=100*np.average(r.over.dropna(), weights=r.w[r.over.notna()]),
      eur_m2_tenants=weighted_quantile(r.eur_m2,r.w), eur_m2_new=weighted_quantile(r[r.FFdauliw_a==1].eur_m2, r[r.FFdauliw_a==1].w),
      burden_high=share(g.WObelko<=2, g.WObelko, w)))
t=pd.DataFrame(rows).set_index('survey_area').round(1)
pd.set_option('display.width',250); pd.set_option('display.max_columns',30)
print(t.sort_values('under2000',ascending=False).to_string())
