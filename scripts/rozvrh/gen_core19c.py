import json,sys,random
from ortools.sat.python import cp_model
from collections import defaultdict,Counter
SEED=int(sys.argv[1]) if len(sys.argv)>1 else 0
VARIANT=sys.argv[2] if len(sys.argv)>2 else "A"
GDMI={"2A","25","1U","2B","26","1W","2E","2F"}
MI={"2B","26","1W","2F"}; GD={"2A","25","1U","2E"}
NAME={}; MIST={}
for ln in open("predmap.txt",encoding="utf-8"):
    a=ln.rstrip("\n").split("|")
    if a[0]: NAME[a[0]]=a[1]; MIST[a[0]]=(a[2] if len(a)>2 else "")
# jazyky + TV + konverzace = řeší se jinde / mimo odborné
LANG={"4","5","1G","1I","9B","AN","43","46","55","17"}
def rooms_of(naz,mist):
    p=naz.lower()
    # akademické -> bez specializované učebny (dost kmenových 7/9/4/5...)
    if any(k in p for k in ("dějiny umění","dějiny designu","dějiny multim","mediální komunikace",
        "český jazyk","literatura","chemie","fyzik","dějepis","matematik","občansk","zeměp",
        "ekonom","biologie","základy spol")): return []
    if "informa" in p or "ikt" in p or "výpočet" in p: return ["IT5"]
    if "figurální" in p: return ["BA","BK"]
    if "výtvarná příprava" in p or "výtvarná tvorba" in p: return ["BK","BA"]
    if "digitální fotografie" in p: return ["BPG","MM","BŠ"]
    if "fotografie 2" in p: return ["MM","IT2"]
    if "fotografie" in p: return ["MM","IT2","BPG"]
    if "grafick" in p and "techni" in p: return ["BD4"]
    if "grafický design a navrh" in p: return ["BNA","BŠ","BPG"]
    if "počítačová grafika" in p: return ["BNA","BŠ","BPG","MM","IT2"]
    if "písmo" in p or "typograf" in p: return ["BD4","BD1","BNA","BŠ"]
    if "prostorový design" in p: return ["BD4"]
    if "game" in p: return ["MM","IT2"]
    if "webdesign" in p or "web design" in p or "multimediální aplik" in p: return ["MM","IT2","BŠ","BPG"]
    if "audiovizu" in p: return ["MM","IT2"]
    if "3d animace" in p: return ["IT2","MM"]
    if "vizualizace" in p or p.startswith("3d") or " 3d" in p: return ["MM","IT2","BŠ"]
    if "animace" in p or "animovan" in p: return ["IT2","MM"]
    if "technické kreslení" in p: return ["MM","BŠ","IT2"]
    if "technologie" in p: return ["BD1","IT2","MM"]
    if "design interiéru" in p or "design interieru" in p: return ["BD1","BA"]
    if "konstrukč" in p: return ["BD1","D"]
    if "prostorová tvorba" in p: return ["BA","BK","BD1"]
    if "scénár" in p or "komiks" in p or "zvuk" in p: return ["MM","IT2"]
    if "motion" in p: return ["BPG","BŠ","BNA","MM","IT2"]
    if "modelování" in p or "modelovani" in p: return ["BD1","D"]
    if "digitální kresba" in p or "digitalni kresba" in p: return ["IT2"]
    if "design nábytku" in p or "design nabytku" in p: return ["BD1","D"]
    return []
def end_cap(p):
    pl=p.lower()
    if any(k in pl for k in ("český jazyk","matematika","dějiny umění")): return 7
    if any(k in pl for k in ("fyzik","chemie","ekonom","management")): return 9
    return 10
def spread(p):
    pl=p.lower(); return any(k in pl for k in ("matematika","fyzika","občanská nauka","dějiny umění","dějepis","ekonom","management"))
def is_media(p):
    p=p.lower(); return any(k in p for k in ("animace","animovan","audiovizu","game design",
        "motion design","web design","webdesign","multimediální tvorba"))
def force_len(naz,trid,kp):
    p=naz.lower()
    if kp=="PT": return 3
    if "grafick" in p and "techni" in p: return 2 if trid=="2A" else 3   # GUT 2.GD=2h, 3.GD=3h
    if "technologie" in p and trid=="1U": return 2                       # Te 4.GD 2h
    if "motion" in p: return 3 if trid=="1U" else 2                      # MD 4.GD=3h, 3.GD=2h
    if any(k in p for k in ("animace","audiovizu","game design","figurální",
        "prostorová tvorba","design interi","design nábytku","design nabytku","konstrukč",
        "výtvarná příprava","výtvarná tvorba","vizualizace","grafické umělecké")): return 3
    return None
def blk(h,art,media,sp):
    h=int(round(h)); h=max(h,1); out=[]; step=1 if sp else (2 if (media or not art) else 3)
    while h>0: out.append(min(step,h)); h-=min(step,h)
    return out
ATELIER=set(["BA","BK","BD1","BD4","BNA","BŠ","BPG"])
def is_atel(r): return (r in ATELIER) or (isinstance(r,str) and r[:1]=="B")
def t_ok(uk,d,hh,L):
    e=hh+L-1
    if uk in("UZS4U","UHDY5") and hh<2: return False
    if uk=="UOS6Q" and e>7: return False
    if uk=="UI7OD" and d==3 and hh<4: return False
    if uk=="UYS9G" and d==5 and e>4: return False
    if uk=="UNS6G":  # Vlková: ne čtvrtek + start>=2h (var D: navíc ne pátek)
        if d==4 or hh<2: return False
        if VARIANT=="D" and d==5: return False
    if uk=="UMS61" and d==4 and e>3: return False
    if uk=="UZSA4" and d==3: return False
    return True
# --- načti reálné skupiny z úvazku: trid|pred|skup|uk|hod ---
raw=[]
for ln in open("raw_skup.txt",encoding="utf-8"):
    ln=ln.rstrip("\n")
    if not ln: continue
    trid,pred,skup,uk,hod=ln.split("|")
    if trid not in GDMI or pred in LANG: continue
    raw.append((trid,pred,skup,uk,float(hod)))
# whole-class skup = skup předmětu 0P (Český jazyk) v dané třídě
WHOLE={}
for trid,pred,skup,uk,hod in raw:
    if pred=="0P": WHOLE[trid]=skup
# lanes = distinct non-whole skup v třídě
LANES=defaultdict(set)
for trid,pred,skup,uk,hod in raw:
    if skup!=WHOLE.get(trid): LANES[trid].add(skup)
LANES={t:sorted(s) for t,s in LANES.items()}
# zjisti které preds existují per (trid,skup,uk) -> trojblok jen když Písmo+Typo OBA
present=defaultdict(set)
for trid,pred,skup,uk,hod in raw:
    present[(trid,skup,uk)].add(pred)
# slučovací mapa: (FR,0D)->PT (jen když oba), (0P,0R)->CJ Český jazyk a literatura
def key_of(trid,pred,skup,uk):
    pr=present[(trid,skup,uk)]
    if pred in ("FR","0D") and ("FR" in pr and "0D" in pr): return "PT","Písmo a typografie"
    if pred in ("0P","0R"): return "CJ","Český jazyk a literatura"
    return pred,NAME.get(pred,pred)
agg=defaultdict(float); meta={}
for trid,pred,skup,uk,hod in raw:
    kp,naz=key_of(trid,pred,skup,uk)
    k=(trid,kp,skup,uk); agg[k]+=hod; meta[k]=naz
units=[]
for (trid,kp,skup,uk),hod in agg.items():
    naz=meta[(trid,kp,skup,uk)]
    if kp=="PT": rms=["BD4","BD1","BNA","BŠ"]
    elif kp=="CJ": rms=[]
    else:
        rms=rooms_of(naz,MIST.get(kp,""))
        if not rms:
            ms=MIST.get(kp,""); rms=[ms] if ms else []
    art=bool(rms); md=is_media(naz); sp=spread(naz); cap=end_cap(naz)
    wh=hod/2.0
    F=force_len(naz,trid,kp)
    if F:
        Ls=[]; rem=int(round(wh))
        while rem>0: Ls.append(min(F,rem)); rem-=min(F,rem)
    else: Ls=blk(wh,art,md,sp)
    for L in Ls:
        units.append({"trid":trid,"pnaz":naz,"teachers":[uk],"rooms":rms,"art":art,
                      "sp":sp,"L":L,"cap":cap,"skup":skup})
# busy z jazyků + TV
lang=json.load(open("gen_lang2_out.json"))[0]["cells"]
cbusy=set()
for c in lang:
    if c["c"] in GDMI: cbusy.add((c["c"],c["d"],c["h"]))
tbusy0=set(c["uk"] and (c["uk"],c["d"],c["h"]) for c in lang)
tv=json.load(open("gen_tv_week.json"))["cells"]
for c in tv:
    for h in (c["h1"],c["h2"]):
        if c["c"] in GDMI: cbusy.add((c["c"],c["d"],h))
        tbusy0.add((c["uk"],c["d"],h))
def subkeys(u):
    t=u["trid"]
    if u["skup"]==WHOLE.get(t):
        return [(t,ln) for ln in LANES.get(t,[u["skup"]])]
    return [(t,u["skup"])]
TLIMIT={"UTS88":4,"UOS6U":4,"UZS4O":4,"UOS6X":3,"UVS8S":2,"UUS8D":4,"UPS70":3,"UXS9D":3}
def solve(group,tbusy,rbusy,tsec,tdays_prior,hint=None):
    m=cp_model.CpModel(); cand=[]; yv=[]
    for ui,u in enumerate(group):
        cs=[]; ys=[]
        for d in range(1,6):
            for h in range(1,u["cap"]-u["L"]+2):
                e=h+u["L"]-1
                if e>u["cap"] or (d==5 and e>7): continue
                hrs=range(h,e+1)
                if any((u["trid"],d,x) in cbusy for x in hrs): continue
                if any((t,d,x) in tbusy for t in u["teachers"] for x in hrs): continue
                if any(not t_ok(t,d,h,u["L"]) for t in u["teachers"]): continue
                rl=u["rooms"] if u["art"] else [""]
                for r in rl:
                    if r and any((r,d,x) in rbusy for x in hrs): continue
                    cs.append((d,h,r)); ys.append(m.NewBoolVar(f"y{ui}_{d}_{h}_{r}"))
        cand.append(cs); yv.append(ys)
        if ys: m.Add(sum(ys)<=1)
        if hint is not None and ui<len(hint) and hint[ui] and ys:
            _hd,_hh,_hr=hint[ui]
            for _k,(d,h,r) in enumerate(cs):
                if d==_hd and h==_hh and r==_hr: m.AddHint(ys[_k],1); break
    cl=defaultdict(list); tc=defaultdict(list); ro=defaultdict(list); cd=defaultdict(list)
    for ui,u in enumerate(group):
        subs=subkeys(u)
        for k,(d,h,r) in enumerate(cand[ui]):
            for x in range(h,h+u["L"]):
                for sc in subs: cl[(sc,d,x)].append(yv[ui][k])
                for t in u["teachers"]: tc[(t,d,x)].append(yv[ui][k])
                if r: ro[(r,d,x)].append(yv[ui][k])
            if u["sp"]: cd[(u["trid"],u["pnaz"],u["skup"],d)].append(yv[ui][k])
    for v in list(cl.values())+list(tc.values())+list(ro.values())+list(cd.values()):
        if len(v)>1: m.Add(sum(v)<=1)
    LUNCH=[4,5,6,7]
    fl=defaultdict(int)
    for (cc,dd,xx) in cbusy:
        if xx in LUNCH: fl[(cc,dd)]+=1
    scdays=set((sc,d) for (sc,d,x) in cl.keys())
    for (sc,d) in scdays:
        lv=[]
        for x in LUNCH: lv+=cl.get((sc,d,x),[])
        rhs=max(0,3-fl.get((sc[0],d),0))
        if lv: m.Add(sum(lv)<=rhs)
    clB=defaultdict(list); clN=defaultdict(list); tcB=defaultdict(list); tcN=defaultdict(list)
    fixN=set()
    for (cc,dd,xx) in cbusy: fixN.add((cc,dd,xx))
    for ui,u in enumerate(group):
        subs=subkeys(u)
        for k,(d,h,r) in enumerate(cand[ui]):
            atel = is_atel(r) if r else False
            for x in range(h,h+u["L"]):
                for sc in subs: (clB if atel else clN)[(sc,d,x)].append(yv[ui][k])
                for t in u["teachers"]: (tcB if atel else tcN)[(t,d,x)].append(yv[ui][k])
    def bvar(name,vlist,forceN):
        if not vlist and not forceN: return None
        b=m.NewBoolVar(name)
        for y in vlist: m.Add(b>=y)
        if forceN: m.Add(b==1)
        return b
    scset=set(k[0] for k in list(clB.keys())+list(clN.keys()))
    for sc in scset:
        cls=sc[0]
        for d in range(1,6):
            for x in range(1,11):
                bB=bvar(f"cB{sc}{d}{x}", clB.get((sc,d,x),[]), False)
                fN1=(cls,d,x+1) in fixN
                bN1=bvar(f"cN{sc}{d}{x+1}", clN.get((sc,d,x+1),[]), fN1)
                if bB is not None and bN1 is not None: m.Add(bB+bN1<=1)
                bN=bvar(f"cN{sc}{d}{x}", clN.get((sc,d,x),[]), (cls,d,x) in fixN)
                bB1=bvar(f"cB{sc}{d}{x+1}", clB.get((sc,d,x+1),[]), False)
                if bN is not None and bB1 is not None: m.Add(bN+bB1<=1)
    tset=set(k[0] for k in list(tcB.keys())+list(tcN.keys()))
    for t in tset:
        for d in range(1,6):
            for x in range(1,11):
                bB=bvar(f"tB{t}{d}{x}", tcB.get((t,d,x),[]), False)
                fN1=(t,d,x+1) in tbusy
                bN1=bvar(f"tN{t}{d}{x+1}", tcN.get((t,d,x+1),[]), fN1)
                if bB is not None and bN1 is not None: m.Add(bB+bN1<=1)
                bN=bvar(f"tN{t}{d}{x}", tcN.get((t,d,x),[]), (t,d,x) in tbusy)
                bB1=bvar(f"tB{t}{d}{x+1}", tcB.get((t,d,x+1),[]), False)
                if bN is not None and bB1 is not None: m.Add(bN+bB1<=1)
    # === Marti zásadní: (1) max 1 přejezd mezi budovami za den, (2) max 7 h v kuse ===
    def _occbool(dB,dN,tag):
        occ={}
        keys=set(k[0] for k in dB)|set(k[0] for k in dN)
        for key in keys:
            for dd in range(1,6):
                a={}; nn={}
                for x in range(1,11):
                    la=dB.get((key,dd,x),[]); ln=dN.get((key,dd,x),[])
                    if la:
                        va=m.NewBoolVar("%sA_%s_%d_%d"%(tag,str(key),dd,x))
                        for v in la: m.Add(va>=v)
                        a[x]=va
                    if ln:
                        vn=m.NewBoolVar("%sN_%s_%d_%d"%(tag,str(key),dd,x))
                        for v in ln: m.Add(vn>=v)
                        nn[x]=vn
                if a and nn: occ[(key,dd)]=(a,nn)
        return occ
    for (dB,dN,tag) in ((clB,clN,"c"),(tcB,tcN,"t")):
        for (key,dd),(a,nn) in _occbool(dB,dN,tag).items():
            if tag=="t" and key=="UXS9D": continue
            nF=m.NewBoolVar("nf_%s_%s_%d"%(tag,str(key),dd))
            xs=sorted(set(list(a)+list(nn)))
            for i,x in enumerate(xs):
                for y in xs[i+1:]:
                    if x in a and y in nn: m.Add(a[x]+nn[y]-1 <= 1-nF)   # A před N -> A-first
                    if x in nn and y in a: m.Add(nn[x]+a[y]-1 <= nF)     # N před A -> N-first
    # (2) max 7 v kuse pro UČITELE = aspoň 1 volná hodina v poledním okně 4-7 (žáci to mají přes oběd)
    for (t,d) in set((k[0],k[1]) for k in tc.keys()):
        if t=="UXS9D": continue
        lv=[]
        for x in (4,5,6,7): lv+=tc.get((t,d,x),[])
        if lv: m.Add(sum(lv) <= 3)
    for t,L in TLIMIT.items():
        P=tdays_prior.get(t,set()); perday=defaultdict(list)
        for (tt,dd,xx),vv in tc.items():
            if tt==t: perday[dd]+=vv
        cost=[]
        for dd in range(1,6):
            if dd in P or not perday.get(dd): continue
            bd=m.NewBoolVar("dl_%s_%d"%(t,dd))
            for y in perday[dd]: m.Add(bd>=y)
            cost.append(bd)
        if cost: m.Add(sum(cost)<=max(0,L-len(P)))
    rr=random.Random(SEED*97+len(group))
    WATCH={"UNS6G","UXS9D","UTS88","UOS6X","UVS8S","UZS4A","UMS61","USS80","UOS6W","UUS8D","UZS44"}
    terms=[]
    for ui,u in enumerate(group):
        w=1000+8*u["L"]+(250 if any(t in WATCH for t in u["teachers"]) else 0)+(700 if "UNS6G" in u["teachers"] else 0)+(700 if "UXS9D" in u["teachers"] else 0)+rr.randint(0,7)
        for y in yv[ui]: terms.append(w*y)
    # Soft (dohoda s ředitelkou): učitel přejíždí mezi budovami max ~2x týdně
    # -> penalizuj dny, kdy učí v OBOU budovách (ateliér B-učebny vs Nerudovka)
    _mixed=[]
    _ts=set(k[0] for k in tcB.keys()) | set(k[0] for k in tcN.keys())
    _exempt={"UXS9D"}  # Švehlová: předměty nutně v obou budovách -> z penalty ven (drží si hodiny)
    for _t in _ts:
        if _t in _exempt: continue
        for _d in range(1,6):
            _bv=[v for (tt,dd,xx),vs in tcB.items() if tt==_t and dd==_d for v in vs]
            _nv=[v for (tt,dd,xx),vs in tcN.items() if tt==_t and dd==_d for v in vs]
            if not _bv or not _nv: continue
            _hb=m.NewBoolVar("hb_%s_%d"%(_t,_d)); _hn=m.NewBoolVar("hn_%s_%d"%(_t,_d)); _mx=m.NewBoolVar("mx_%s_%d"%(_t,_d))
            for v in _bv: m.Add(_hb>=v)
            for v in _nv: m.Add(_hn>=v)
            m.Add(_mx>=_hb+_hn-1)
            _mixed.append(_mx)
    m.Maximize(sum(terms) - 40*sum(_mixed))
    s=cp_model.CpSolver(); s.parameters.max_time_in_seconds=tsec; s.parameters.num_search_workers=8; s.parameters.random_seed=SEED
    st=s.Solve(m); out=[]; un=[]; assign=[None]*len(group)
    for ui,u in enumerate(group):
        pl=None
        for k,(d,h,r) in enumerate(cand[ui]):
            if yv[ui] and s.Value(yv[ui][k])==1: pl=(d,h,r); break
        if pl:
            out.append({"trid":u["trid"],"d":pl[0],"h1":pl[1],"L":u["L"],"teachers":u["teachers"],
                           "pnaz":u["pnaz"],"room":pl[2],"obor":u["skup"]})
            assign[ui]=[pl[0],pl[1],pl[2]]
        else: un.append((u["trid"],u["pnaz"],u["L"],u["teachers"][0]))
    return out,un,assign
