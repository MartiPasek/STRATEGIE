order=["2E","2A","1W","2F","2B","26","1U","25"]
byc=defaultdict(list)
for u in units: byc[u["trid"]].append(u)
import os,time as _t
STATE="cp24_state_%s.json"%VARIANT
PERCLS=float(sys.argv[3]) if len(sys.argv)>3 else 18.0
BUDGET=float(sys.argv[4]) if len(sys.argv)>4 else 40.0
if os.path.exists(STATE):
    st=json.load(open(STATE))
    tb=set(tuple(x) for x in st["tb"]); rb=set(tuple(x) for x in st["rb"])
    allout=st["allout"]; allun=[tuple(x) for x in st["allun"]]
    tdays={k:set(v) for k,v in st["tdays"].items()}; done=set(st["done"]); logs=st["logs"]
else:
    tb=set(tbusy0); rb=set(); allout=[]; allun=[]; logs=[]; tdays={}; done=set()
t0=_t.time()
for cls in order:
    if cls in done: continue
    if _t.time()-t0 > BUDGET: break
    g=byc.get(cls,[])
    if not g: done.add(cls); continue
    o,un=solve(g,tb,rb,PERCLS,tdays)
    logs.append("%s:%d/%d"%(cls,len(o),len(o)+len(un)))
    for c in o:
        for x in range(c["h1"],c["h1"]+c["L"]):
            for t in c["teachers"]: tb.add((t,c["d"],x))
            if c["room"]: rb.add((c["room"],c["d"],x))
        for t in c["teachers"]: tdays.setdefault(t,set()).add(c["d"])
    allout+=o; allun+=un; done.add(cls)
json.dump({"tb":[list(x) for x in tb],"rb":[list(x) for x in rb],"allout":allout,
    "allun":[list(x) for x in allun],"tdays":{k:list(v) for k,v in tdays.items()},
    "done":list(done),"logs":logs}, open(STATE,"w"))
print(" ".join(logs))
target=defaultdict(float)
for trid,pred,skup,uk,hod in raw: target[uk]+=hod/2.0
placed=defaultdict(int)
for c in allout:
    for t in c["teachers"]: placed[t]+=c["L"]
print("CELKEM um",len(allout),"| hodin",sum(placed.values()),"/ cíl",round(sum(target.values()),1),"| hotové",sorted(done))
print("Vlková UNS6G placed",placed["UNS6G"])
json.dump({"cells":allout,"un":allun},open("gen_pred_cp24_%d.json"%SEED,"w"))
