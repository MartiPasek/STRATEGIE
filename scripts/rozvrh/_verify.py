#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Nezavisla verifikace odborneho bloku: konflikty trida/ucitel/ucebna (i proti DB jazyky+tv) + uvazky + Vlkova.
import json,sys
from collections import defaultdict
VAR=sys.argv[1] if len(sys.argv)>1 else "A"
SEED=sys.argv[2] if len(sys.argv)>2 else "0"
GDMI={"2A","25","1U","2B","26","1W","2E","2F"}
LANG={"4","5","1G","1I","9B","AN","43","46","55","17"}
# WHOLE/LANES jako v generatoru
raw=[]
for ln in open("raw_skup.txt",encoding="utf-8"):
    ln=ln.rstrip("\n")
    if not ln: continue
    t,pred,skup,uk,hod=ln.split("|")
    if t not in GDMI or pred in LANG: continue
    raw.append((t,pred,skup,uk,float(hod)))
WHOLE={}
for t,pred,skup,uk,hod in raw:
    if pred=="0P": WHOLE[t]=skup
LANES=defaultdict(set)
for t,pred,skup,uk,hod in raw:
    if skup!=WHOLE.get(t): LANES[t].add(skup)
LANES={t:sorted(s) for t,s in LANES.items()}
def subkeys(trid,skup):
    if skup==WHOLE.get(trid): return [(trid,ln) for ln in LANES.get(trid,[skup])]
    return [(trid,skup)]
# DB busy
dbc=set()
for ln in open("db_cbusy.txt"):
    ln=ln.strip()
    if ln: c,d,h=ln.split(":"); dbc.add((c,int(d),int(h)))
dbt=set(); dbr=set()
for ln in open("db_trbusy.txt"):
    ln=ln.strip()
    if not ln: continue
    typ,key,d,h=ln.split(":")
    if typ=="T": dbt.add((key,int(d),int(h)))
    else: dbr.add((key,int(d),int(h)))
# nas vystup
J=json.load(open("gen_odb_%s_%s.json"%(VAR,SEED)))
cells=J["cells"]
cl_occ=defaultdict(list)   # (lane-trida,d,h) -> [popis]
tc_occ=defaultdict(list)
ro_occ=defaultdict(list)
for c in cells:
    desc="%s %s %s"%(c["trid"],c["pnaz"][:14],c["obor"])
    for d_h in range(c["h1"],c["h1"]+c["L"]):
        for sk in subkeys(c["trid"],c["obor"]):
            cl_occ[(sk,c["d"],d_h)].append(desc)
        for t in c["teachers"]:
            tc_occ[(t,c["d"],d_h)].append(desc)
        if c["room"]:
            ro_occ[(c["room"],c["d"],d_h)].append(desc)
errc=0
# 1) interni dvojity zabor (trida-lane / ucitel / ucebna)
for occ,nm in ((cl_occ,"TRIDA"),(tc_occ,"UCITEL"),(ro_occ,"UCEBNA")):
    for k,v in occ.items():
        if len(v)>1:
            errc+=1; print("KONFLIKT %s %s: %s"%(nm,k,v))
# 2) proti DB jazyky+tv
for c in cells:
    for d_h in range(c["h1"],c["h1"]+c["L"]):
        for sk in subkeys(c["trid"],c["obor"]):
            if (sk[0],c["d"],d_h) in dbc:
                errc+=1; print("KONFLIKT vs DB TRIDA: %s %s d%d h%d"%(sk[0],c["pnaz"][:14],c["d"],d_h))
        for t in c["teachers"]:
            if (t,c["d"],d_h) in dbt:
                errc+=1; print("KONFLIKT vs DB UCITEL: %s %s d%d h%d"%(t,c["pnaz"][:14],c["d"],d_h))
        if c["room"] and (c["room"],c["d"],d_h) in dbr:
            errc+=1; print("KONFLIKT vs DB UCEBNA: %s d%d h%d"%(c["room"],c["d"],d_h))
# 3) uvazky per ucitel (odborne)
tgt=defaultdict(float)
VSEOB_KW=["český jazyk","literatura","matematik","fyzik","chemie","dějepis","dějiny","historie",
 "občansk","společenskovědní","základy spol","základy společ","zeměp","ekolog","biolog",
 "přírodních věd","psycholog","právo","ekonom","management","marketing","finance","daň","účetn",
 "nauka","třídnick","chování","kariér","kulturní dědictví","umění v souvislostech","člověk a média",
 "profesní komunikace","jazykové praktikum","informační a komunikační","výpočet","praktikum",
 "seminář","mezinárodní vztahy","naučná literatura","propagace","aranžování","zbožíznalství",
 "jakost","služby cestov","průvodcov","cestovní ruch","literární","náuka"]
NAME={}
for ln in open("predmap.txt",encoding="utf-8"):
    a=ln.rstrip("\n").split("|")
    if a[0]: NAME[a[0]]=a[1]
def vseob(naz): p=(naz or "").lower(); return any(k in p for k in VSEOB_KW)
present=defaultdict(set)
for t,pred,skup,uk,hod in raw: present[(t,skup,uk)].add(pred)
for t,pred,skup,uk,hod in raw:
    pr=present[(t,skup,uk)]
    if pred in("FR","0D") and ("FR" in pr and "0D" in pr): naz="Písmo a typografie"
    elif pred in("0P","0R"): naz="Český jazyk a literatura"
    else: naz=NAME.get(pred,pred)
    if not vseob(naz): tgt[uk]+=hod/2.0
got=defaultdict(int)
for c in cells:
    for t in c["teachers"]: got[t]+=c["L"]
mis=0
for uk in sorted(set(list(tgt)+list(got))):
    if abs(tgt[uk]-got[uk])>0.01:
        mis+=1; print("UVAZEK NESEDI %s: cil %.1f umisteno %d"%(uk,tgt[uk],got[uk]))
# Vlkova pozdni dny
vl=[c for c in cells if "UNS6G" in c["teachers"]]
late=sorted(set(c["d"] for c in vl if c["h1"]+c["L"]-1>=9))
print("---")
print("KONFLIKTU:",errc,"| uvazku nesedi:",mis,"| Vlkova pozdnich dnu:",len(late),late)
print("bunky:",len(cells),"hodin:",sum(c["L"] for c in cells))
