import random, json
CUR={"27":"1.A","29":"1.CR","2A":"1.GD","28":"1.L","2B":"1.MI","2C":"1.O","21":"2.A","20":"2.B",
"22":"2.CR","25":"2.GD","26":"2.MI","23":"2.VO","24":"2.ZO","1S":"3.A","1T":"3.CR","1U":"3.GD",
"1W":"3.MI","1Y":"3.VO","1Z":"3.ZO"}
def roll(c):
    z=CUR.get(c)
    if z and z[0].isdigit(): return str(int(z[0])+1)+z[1:]
    return {"2D":"1.D?","2E":"1.E?","2F":"1.F?","2G":"1.G?","2I":"1.I?","2J":"1.J?"}.get(c,c)
FOURTH={"1S","1T","1U","1W","1Y","1Z"}
GDMI={"2A","25","1U","2B","26","1W","2E","2F"}  # GD+MI -> jazyky od 1. hodiny
GDc={"2A","25","1U","2E"}; MIc={"2B","26","1W","2F"}  # GD max 3 dny jazyků (2 ateliérové), MI max 4 (1 pro DI)
def jcap(c): return 3 if c in GDc else (4 if c in MIc else 99)
VLK_CLS={"2E"}  # Vlková (volný Čt) -> jazyky/TV jejích tříd na čtvrtek, ateliéry jinam
NOFRI_CLS={"1U"}  # 4.GD: Tesliuk učí MD jen pátek 6h -> pátek bez jazyků
ZDIMER="UZS4U"; SEDOVA="UOS6Q"
# konsolidovaná učitelská availability (den 1=Po..5=Pá)
def t_ok(uk,d,hh,L):
    end=hh+L-1
    if uk=="UZS4U" and hh<2: return False           # Ždimerová od 2.h
    if uk=="UHDY5" and hh<2: return False           # Vroblová od 2.h
    if uk=="UOS6Q" and end>7: return False          # Šedová do 7.h
    if uk=="UI7OD" and d==3 and hh<4: return False  # Kubálková středa od 4.h
    if uk=="UYS9G" and d==5 and end>4: return False # Layerová pátek do 4.h
    return True
PREDZKR={"4":"AJ","5":"NJ","1G":"FJ","1I":"ŠJ","AN":"RJ"}
# TV obsazenost - jazyky se MUSÍ vyhnout slotům tělocviku (jinak TV přerušené jazykem)
TVBUSY_C=set(); TVBUSY_T=set()
try:
    for _c in json.load(open("gen_tv_week.json"))["cells"]:
        for _hh in (_c["h1"],_c["h2"]):
            TVBUSY_C.add((_c["c"],_c["d"],_hh))
            if _c.get("uk"): TVBUSY_T.add((_c["uk"],_c["d"],_hh))
    print("TV slotů blokováno pro jazyky:",len(TVBUSY_C))
except Exception as _e: print("WARN tv:",_e)
units=[]
for ln in open("lang_units.txt",encoding="utf-8"):
    ln=ln.strip()
    if not ln: continue
    spoj,uk,pred,pnaz,hod,tridy=ln.split("|")
    cls=tuple(sorted(c.strip() for c in tridy.split(",") if c.strip()))
    h=int(float(hod)); cj=1 if pred=="4" else (2 if h>=3 else 3)
    units.append({"spoj":spoj,"uk":uk,"pred":pred,"pnaz":pnaz,"zkr":PREDZKR.get(pred,pred),"h":h,"cls":cls,"cj":cj,"bk":""})
import os as _os
if _os.path.exists("kaj_units.txt"):
    _nk=0
    for ln in open("kaj_units.txt",encoding="utf-8"):
        ln=ln.strip()
        if not ln: continue
        spoj,uk,pred,pnaz,hod,tridy,roc=ln.split("|")
        cls=tuple(sorted(c.strip() for c in tridy.split(",") if c.strip()))
        units.append({"spoj":spoj,"uk":uk,"pred":"KAJ","pnaz":pnaz,"zkr":"KAJ","h":int(hod),"cls":cls,"cj":1,"bk":"KAJ"+roc}); _nk+=1
    print("KAJ jednotek přidáno:",_nk)

# BANDY: sloučit přes propojené komponenty tříd (celý ročník/kohorta, stejná úroveň + stejné hodiny = jeden synchronizovaný band)
parent={}
def _f(x):
    parent.setdefault(x,x); r=x
    while parent[r]!=r: r=parent[r]
    while parent[x]!=r: parent[x],x=r,parent[x]
    return r
def _u(a,b):
    ra,rb=_f(a),_f(b)
    if ra!=rb: parent[ra]=rb
for u in units:
    ks=[(u["cj"],u["bk"],c) for c in u["cls"]]
    for k in ks[1:]: _u(ks[0],k)
bands_d={}
for u in units:
    root=_f((u["cj"],u["bk"],u["cls"][0])); key=(root,u["h"])
    b=bands_d.setdefault(key,{"cls":set(),"cj":u["cj"],"units":[],"h":u["h"]})
    b["cls"].update(u["cls"]); b["units"].append(u)
# pokud má band stejného učitele 2x (nemůže učit 2 skupiny naráz) -> rozděl ho
bands=[]
for b in bands_d.values():
    from collections import defaultdict as _dd
    seen=_dd(list)
    for u in b["units"]: seen[u["uk"]].append(u)
    maxdup=max(len(v) for v in seen.values())
    if maxdup==1:
        bands.append(b)
    else:
        for i in range(maxdup):
            sub={"cls":set(),"cj":b["cj"],"units":[],"h":b["h"]}
            for uk,us in seen.items():
                if i<len(us): sub["units"].append(us[i]); sub["cls"].update(us[i]["cls"])
            if sub["units"]: bands.append(sub)

def sessions(b):
    h=b["h"]; cj=b["cj"]; fourth=any(c in FOURTH for c in b["cls"])
    if cj==3: return [1]*h
    if cj==1: return ([2]+[1]*(h-2)) if (fourth and h>=2) else [1]*h  # 4.roč AJ dvouhodinovka, jinak 1+1+1+1
    return [2,1,1] if h==4 else [1]*h
def cap(cj): return 7 if cj==1 else 8
DAYS=[1,2,3,4,5]

def gen(seed):
    rnd=random.Random(seed)
    cbusy={k:1 for k in TVBUSY_C}   # (cls,day,hour)->band id (předplněno TV)
    tbusy=set(TVBUSY_T)# (uk,day,hour) (předplněno TV učiteli)
    cls_days={} # cls->set days s jazykem
    slot_lv={}  # (day,hour)->set cj (pro rule18)
    cls_slot_cj={}  # (cls,day,hour)->cj uroven
    cells=[]; unplaced=[]
    order=list(range(len(bands))); rnd.shuffle(order)
    order.sort(key=lambda i:(0 if any(c in GDMI for c in bands[i]["cls"]) else 1, 0 if bands[i]["cj"]==1 else 1, -len(bands[i]["cls"]), -bands[i]["h"]))
    for bi in order:
        b=bands[bi]; sess=sessions(b); cp=cap(b["cj"]); used=set()
        teachers=set(u["uk"] for u in b["units"])
        for L in sorted(sess,reverse=True):
            best=None;bsc=10**9
            cand=[(d,hh) for d in DAYS for hh in range(1,cp-L+2)]; rnd.shuffle(cand)
            for d,hh in cand:
                hrs=range(hh,hh+L)
                if any(not t_ok(t,d,hh,L) for t in teachers): continue
                if any((c,d,x) in cbusy for c in b["cls"] for x in hrs): continue
                if any((t,d,x) in tbusy for t in teachers for x in hrs): continue
                if d in used: continue
                if d==5 and any(c in NOFRI_CLS for c in b["cls"]): continue  # 4.GD pátek = Tesliuk MD
                # rezervace ateliérových dnů: GD max 3 dny jazyků, MI max 4 (zbytek pro odborné v ateliérech)
                _capbad=False
                for _c in b["cls"]:
                    if d not in cls_days.get(_c,set()) and len(cls_days.get(_c,set()))>=jcap(_c): _capbad=True; break
                if _capbad: continue
                _adj=False  # 1./2./3. CJ nesmí být za sebou (různé úrovně CJ ne sousedně)
                for _c in b["cls"]:
                    for _nb in (hh-1, hh+L):
                        _ncj=cls_slot_cj.get((_c,d,_nb))
                        if _ncj is not None and _ncj!=b["cj"]: _adj=True; break
                    if _adj: break
                if _adj: continue
                _gd=any(c in GDMI for c in b["cls"])
                sc=(hh-1)*8.0 if _gd else abs(hh-3)*0.2
                nd=sum(1 for c in b["cls"] if d not in cls_days.get(c,set())); sc-=nd*3
                if d==4 and any(c in VLK_CLS for c in b["cls"]): sc-=20  # Vlkové třída: jazyky na Čt
                for x in hrs:
                    lv=slot_lv.get((d,x),set())
                    if b["cj"] in (1,2) and ((1 in lv and b["cj"]==2) or (2 in lv and b["cj"]==1)): sc+=4
                if sc<bsc: bsc=sc;best=(d,hh,list(hrs))
            if not best: unplaced.append((b["cj"],sorted(b["cls"]),L)); continue
            d,hh,hrs=best; used.add(d)
            for x in hrs:
                for t in teachers: tbusy.add((t,d,x))
                slot_lv.setdefault((d,x),set()).add(b["cj"])
                for c in b["cls"]:
                    cbusy[(c,d,x)]=1; cls_days.setdefault(c,set()).add(d); cls_slot_cj[(c,d,x)]=b["cj"]
                for u in b["units"]:
                    for c in u["cls"]:
                        cells.append({"d":d,"h":x,"c":c,"spoj":u["spoj"],"uk":u["uk"],"pred":u["pnaz"],"zkr":u["zkr"],"cj":u["cj"],"L":L})
    pen=0
    for (d,x),lv in slot_lv.items():
        if 1 in lv and 2 in lv: pen+=3
    for c,days in cls_days.items():
        if len(days)<3: pen+=2*(3-len(days))
    return {"cells":cells,"unplaced":unplaced,"pen":pen,"seed":seed,"nb":len(bands)}

res=[gen(s) for s in range(60)]
res.sort(key=lambda r:(len(r["unplaced"]),r["pen"]))
print("bandů:",len(bands))
for i,r in enumerate(res[:6]):
    print("Var",chr(65+i),"seed",r["seed"],"bunky",len(r["cells"]),"neumisteno",len(r["unplaced"]),"pen",r["pen"])
json.dump(res[:6],open("gen_lang3_out.json","w"))
# KAJ konverzace integrated 2026-06-22
