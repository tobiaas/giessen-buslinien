import csv,io,zipfile,pickle,sys
z=zipfile.ZipFile('gtfs.zip')
rd=lambda n:csv.DictReader(io.TextIOWrapper(z.open(n),encoding='utf-8-sig'))
S={};names={}
for r in rd('stops.txt'):
    try: la,lo=float(r['stop_lat']),float(r['stop_lon'])
    except: continue
    if 50.54<la<50.63 and 8.60<lo<8.75: S[r['stop_id']]=r['stop_name']
print('stops in GI',len(S),file=sys.stderr)
routes={r['route_id']:(r['route_short_name'],r['agency_id']) for r in rd('routes.txt') if r['route_type'] in ('3','700','702','704','705','715')}
trips={}
for r in rd('trips.txt'):
    if r['route_id'] in routes: trips[r['trip_id']]=(r['route_id'],r['service_id'])
print('bus trips',len(trips),file=sys.stderr)
def t2m(t): h,m,s=t.split(':'); return int(h)*60+int(m)
out={}
cur=None;rec=None
f=io.TextIOWrapper(z.open('stop_times.txt'),encoding='utf-8-sig'); f.readline()
for line in f:
    p=line.split(',',5)
    tid=p[0]
    if tid!=cur:
        if rec and rec[5]: out[cur]=rec[:5]
        cur=tid
        rec=[None,None,None,None,0,False] if tid in trips else None
    if rec is None: continue
    sid=p[3]
    if rec[0] is None: rec[0]=t2m(p[2]); rec[2]=sid
    rec[1]=t2m(p[1]); rec[3]=sid; rec[4]+=1
    if sid in S: rec[5]=True
if rec and rec[5]: out[cur]=rec[:5]
print('trips touching GI',len(out),file=sys.stderr)
pickle.dump(dict(S=S,routes=routes,trips={k:trips[k] for k in out},out=out),open('gtfs1.pkl','wb'))
