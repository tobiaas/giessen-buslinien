import json, math
from collections import defaultdict
g=json.load(open('geom.json'))['elements']; b=json.load(open('bg2.json'))['elements']
st={e['id']:e for e in json.load(open('stops.json'))['elements']}
LAT0=50.585; KX=math.cos(math.radians(LAT0))*111320; KY=110574; CX,CY=8.672,50.585
def P(lon,lat): return ((lon-CX)*KX, -(lat-CY)*KY)
def rdp(pts,eps):
    if len(pts)<3: return pts
    out=[pts[0]]; stack=[(0,len(pts)-1)]; keep=[False]*len(pts); keep[0]=keep[-1]=True
    while stack:
        s,e=stack.pop(); a,bb=pts[s],pts[e]; dx,dy=bb[0]-a[0],bb[1]-a[1]; L=math.hypot(dx,dy)
        i,dm=-1,-1
        for k in range(s+1,e):
            p=pts[k]
            if L<1: d=math.dist(p,a)
            else:
                u=max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/(L*L)))
                d=math.dist(p,(a[0]+u*dx,a[1]+u*dy))
            if d>dm: i,dm=k,d
        if dm>eps: keep[i]=True; stack+=[(s,i),(i,e)]
    return [p for p,k in zip(pts,keep) if k]
R=lambda pts,eps:[[round(x),round(y)] for x,y in rdp(pts,eps)]
plen=lambda s:sum(math.dist(s[i],s[i+1]) for i in range(len(s)-1))
def chains(cs):
    cs=[c[:] for c in cs if len(c)>1]
    ends=True
    while ends:
        ends=False
        idx=defaultdict(list)
        for i,c in enumerate(cs): idx[c[0]].append(i); idx[c[-1]].append(i)
        for i,c in enumerate(cs):
            for end in (c[-1],c[0]):
                js=[j for j in idx[end] if j!=i]
                if len(idx[end])==2 and js:  # merge only at simple joints (no branching)
                    j=js[0]; d=cs[j]
                    a=c if end==c[-1] else c[::-1]
                    bb=d if d[0]==end else d[::-1]
                    cs[i]=a+bb[1:]; del cs[j]; ends=True; break
            if ends: break
    return cs
def ordered(ways):
    left=[w for w in ways if len(w)>1]
    # unique by geometry
    seen=set();u=[]
    for w in left:
        k=min(tuple(w),tuple(w[::-1]))
        if k not in seen: seen.add(k);u.append(w)
    left=u;runs=[]
    while left:
        cur=left.pop(0)[:]
        grew=True
        while grew and left:
            grew=False;best=None
            for end in (0,1):
                pt=cur[-1] if end else cur[0]
                for k,w in enumerate(left):
                    for rev in (0,1):
                        q=w[-1] if rev else w[0]
                        d=math.dist(pt,q)
                        if best is None or d<best[0]: best=(d,end,k,rev)
            if best and best[0]<=40:
                d,end,k,rev=best; w=left.pop(k)
                if end: cur+= (w[::-1] if rev else w)
                else: cur= (w if rev else w[::-1]) + cur
                grew=True
        runs.append(cur)
    return runs
byref=defaultdict(list)
for e in g: byref[e['tags'].get('ref')].append(e)
CITY={'1','2','3','5','6','7','10','12','13','14','15','17','18','LT 2','LT 9','800','801','802'}
NIGHT={'Venus','Saturn'}
FILL={'15':'#5B6CC4','17':'#C2185B','800':'#7E8A97','801':'#00707F','802':'#86BD3B'}
lines=[]
for ref,rels in byref.items():
    wayset={};relways=[]
    for e in rels:
        ws=[]
        for m in e['members']:
            if m['type']=='way' and m['role'] in ('','forward','backward') and 'geometry' in m:
                c=tuple(P(n['lon'],n['lat']) for n in m['geometry']); wayset[m['ref']]=c; ws.append(list(c))
        relways.append((e,ws))
    segs=[R(list(c),4) for c in chains([list(c) for c in wayset.values()])]
    segs=[s for s in segs if plen(s)>0]
    # bus runs: ordered stitch of the longest relation
    e0,ws0=max(relways,key=lambda t:sum(plen(w) for w in t[1]))
    runs=[R(r,4) for r in ordered(ws0)]; runs=[r for r in runs if plen(r)>500]
    t=max((e['tags'] for e in rels),key=lambda t:('from' in t)+('to' in t)+('=>' in t.get('name','')))
    stops=[];sn=set()
    for e in sorted(rels,key=lambda e:e['id']!=e0['id']):
        for m in e['members']:
            if m['type']=='node' and ('stop' in m['role'] or 'platform' in m['role']):
                n=st.get(m['ref']); nm=n and n.get('tags',{}).get('name')
                if nm and nm not in sn: sn.add(nm); p=P(n['lon'],n['lat']); stops.append([round(p[0]),round(p[1]),nm])
    name=t.get('name',''); fr,to=t.get('from'),t.get('to')
    if not (fr and to) and '=>' in name:
        parts=[x.strip() for x in name.split(':',1)[-1].split('=>')]; fr,to=parts[0],parts[-1]
    kind='city' if ref in CITY else 'night' if ref in NIGHT else 'region'
    lines.append(dict(ref=ref,kind=kind,colour=t.get('colour') or FILL.get(ref),name=name,from_=fr,to=to,op=t.get('operator'),segs=segs,runs=runs,stops=stops,nrel=len(rels)))
    print(f"{ref:8} rels={len(rels)} ways={len(wayset)} segs={len(segs)} km={sum(plen(s) for s in segs)/1000:.1f} runs={[round(plen(r)/1000,1) for r in runs]} stops={len(stops)}")
bg={'river':[],'rail':[],'road':[],'bound':[],'place':[]}
allpts=[p for l in lines for s in l['segs'] for p in s[::3]]
import bisect
xs=sorted(allpts)
def near(p,dmax):
    i=bisect.bisect_left(xs,[p[0]-dmax,-1e9])
    while i<len(xs) and xs[i][0]<=p[0]+dmax:
        if abs(xs[i][1]-p[1])<=dmax: return True
        i+=1
    return False
rivers=defaultdict(list)
for e in b:
    t=e.get('tags',{})
    if e['type']=='node':
        p=P(e['lon'],e['lat']); pl=t['place']
        if pl=='town' or near(p,500): bg['place'].append([round(p[0]),round(p[1]),t.get('name',''),1 if pl in('town','city') else 0])
    elif e['type']=='way':
        pts=[P(n['lon'],n['lat']) for n in e['geometry']]
        if 'waterway' in t:
            if t.get('name') in ('Lahn','Wieseck','Ohm','Dill','Wetter','Horloff','Bieber'): rivers[t.get('name')].append(pts)
        else: (bg['rail'] if 'railway' in t else bg['road']).append(pts)
    else:
        bg['bound']+= [R([P(n['lon'],n['lat']) for n in m['geometry']],8) for m in e['members'] if m['type']=='way' and m.get('role')=='outer']
for k in ('rail','road'): bg[k]=[R(c,15) for c in chains([[tuple(p) for p in w] for w in bg[k]])]
bg['river']=[[nm,R(c,10)] for nm,ws in rivers.items() for c in chains([[tuple(p) for p in w] for w in ws])]
for k in ('rail','road'): bg[k]=[s for s in bg[k] if len(s)>1]
ex=[p for l in lines for s in l['segs'] for p in s]
ext=[min(p[0] for p in ex)-1500,min(p[1] for p in ex)-1500,max(p[0] for p in ex)+1500,max(p[1] for p in ex)+1500]
hubs=[]
byname=defaultdict(list)
for l in lines:
    for x,y,n in l['stops']: byname[n].append((x,y,l['ref']))
for n,pts in byname.items():
    best=None
    for x,y,_ in pts:
        cl=[p for p in pts if math.dist(p[:2],(x,y))<400]
        refs={p[2] for p in cl}
        if best is None or len(refs)>len(best[0]): best=(refs,cl)
    refs,cl=best
    if len(refs)>=7:
        xs=sorted(p[0] for p in cl); ys=sorted(p[1] for p in cl)
        hubs.append([xs[len(xs)//2],ys[len(ys)//2],n,len(refs)])
hubs.sort(key=lambda h:-h[3]); print('hubs',[(h[2],h[3]) for h in hubs])
json.dump(dict(ext=ext,lines=lines,bg=bg,hubs=hubs),open('data2.json','w'),separators=(',',':'))
import os;print('size',os.path.getsize('data2.json'),'ext',ext,'places',len(bg['place']))
