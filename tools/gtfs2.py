import pickle,zipfile,io,csv,json,statistics as st
from collections import defaultdict,Counter
from datetime import date
d=pickle.load(open('gtfs1.pkl','rb'));z=zipfile.ZipFile('gtfs.zip')
rd=lambda n:csv.DictReader(io.TextIOWrapper(z.open(n),encoding='utf-8-sig'))
raw={};par={}
for r in rd('stops.txt'): raw[r['stop_id']]=r['stop_name']; par[r['stop_id']]=r['parent_station']
allstops={k:(raw.get(par[k]) if par[k] and par[k] in raw else v) for k,v in raw.items()}
cal={r['service_id']:r for r in rd('calendar.txt')}
exc=defaultdict(dict)
for r in rd('calendar_dates.txt'): exc[r['service_id']][r['date']]=r['exception_type']
DAYS={'wd':'20261013','sa':'20261017','su':'20261018'}
WK=['monday','tuesday','wednesday','thursday','friday','saturday','sunday']
def active(sid,ds):
    e=exc.get(sid,{}).get(ds)
    if e: return e=='1'
    c=cal.get(sid)
    if not c or not(c['start_date']<=ds<=c['end_date']): return False
    y,m,dd=int(ds[:4]),int(ds[4:6]),int(ds[6:])
    return c[WK[date(y,m,dd).weekday()]]=='1'
MAP={'24':'GI-24','N Saturn':'Saturn','N Venus':'Venus','GI-44':'ALT GI-44'}
osmrefs={l['ref'] for l in json.load(open('data2.json'))['lines']}
by=defaultdict(lambda:defaultdict(list))
for tid,(rid,sid) in d['trips'].items():
    sn=d['routes'][rid][0]; ref=MAP.get(sn,sn)
    if ref not in osmrefs: continue
    f,l,a,b,n=d['out'][tid]
    for k,ds in DAYS.items():
        if active(sid,ds): by[ref][k].append((f,l-f,allstops.get(a,a),allstops.get(b,b),n,tid))
for ref in by:
    for k in by[ref]:
        u={}
        for t in by[ref][k]: u.setdefault((t[0],t[2],t[3]),t)
        by[ref][k]=list(u.values())
hm=lambda m:f"{m//60%24:02d}:{m%60:02d}"
res={};rep=set()
for ref,dd in by.items():
    wd=dd['wd'] or dd['sa'] or dd['su']
    if not wd: continue
    basis='wd' if dd['wd'] else 'sa' if dd['sa'] else 'su'
    pats=Counter((t[2],t[3]) for t in wd)
    (a,b),_=pats.most_common(1)[0]
    main=[t for t in wd if (t[2],t[3])==(a,b)]
    durs=sorted(t[1] for t in main)
    deps=sorted(t[0] for t in main)
    day=[x for x in deps if 9*60<=x<=16*60]
    gaps=[y-x for x,y in zip(day,day[1:]) if y>x]
    med=st.median(durs)
    r=min(main,key=lambda t:abs(t[1]-med)); rep.add(r[5])
    alld=[t[1] for t in wd]
    res[ref]=dict(basis=basis,trips={k:len(v) for k,v in dd.items()},first=hm(min(t[0] for t in wd)),last=hm(max(t[0] for t in wd)),
        from_=a,to=b,dur=round(med),dmin=min(durs),dmax=max(durs),longest=max(alld),headway=round(st.median(gaps)) if gaps else None,rep=r[5])
    print(ref,{k:v for k,v in res[ref].items() if k!='rep'})
seq=defaultdict(list)
f=io.TextIOWrapper(z.open('stop_times.txt'),encoding='utf-8-sig');f.readline()
def t2m(t): h,m,s=t.split(':'); return int(h)*60+int(m)
for line in f:
    p=line.split(',',5)
    if p[0] in rep: seq[p[0]].append((int(p[4]),t2m(p[2]),allstops.get(p[3],p[3])))
for ref,r in res.items():
    s=sorted(seq[r['rep']]); t0=s[0][1]
    r['seq']=[[n,m-t0] for _,m,n in s]
json.dump(res,open('times.json','w'),ensure_ascii=False)
