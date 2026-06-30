#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Klasifikace odborné vs všeobecné pro GDMI třídy — ověření před generátorem.
import json
from collections import defaultdict
GDMI={"2A","25","1U","2B","26","1W","2E","2F"}
_LBL_CUR={"2A":"1.GD","25":"2.GD","1U":"3.GD","2B":"1.MI","26":"2.MI","1W":"3.MI"}
_LBL_OVR={"2E":"1.GD","2F":"1.MI"}
def lbl(c):
    if c in _LBL_OVR: return _LBL_OVR[c]
    z=_LBL_CUR.get(c); return (str(int(z[0])+1)+z[1:]) if z else c
LANG={"4","5","1G","1I","9B","AN","22","43","46","55","17"}  # jazyky+KAJ+TV+volitelné dvojhod
NAME={}
for ln in open("predmap.txt",encoding="utf-8"):
    a=ln.rstrip("\n").split("|")
    if a[0]: NAME[a[0]]=a[1]
# VŠEOBECNÉ = akademické (placeholder, Klárka potvrdí). Klíčová slova v názvu.
VSEOB_KW=["český jazyk","literatura","literární","matematik","fyzik","chemie","dějepis",
 "dějiny umění","dějiny designu","dějiny multim","dějiny kultury","dějiny grafick","dějiny",
 "historie","občansk","společenskovědní","základy spol","základy společ","zeměp","ekolog",
 "biolog","přírodních věd","psycholog","právo","ekonom","management","marketing","finance",
 "daň","účetn","náuka","nauka","třídnick","chování","kariér","kulturní dědictví",
 "umění v souvislostech","člověk a média","profesní komunikace","jazykové praktikum",
 "informační a komunikační","výpočet","praktikum","seminář","mezinárodní vztahy","naučná literatura",
 "propagace","aranžování","zbožíznalství","jakost","služby cestov","průvodcov","cestovní ruch"]
def is_vseob(naz):
    p=naz.lower()
    return any(k in p for k in VSEOB_KW)
def force_len(naz,trid,kp):
    p=naz.lower()
    if kp=="PT": return 3
    if "grafick" in p and "techni" in p: return 2 if trid=="2A" else 3
    if "technologie" in p and trid=="1U": return 2
    if "motion" in p: return 3 if trid=="1U" else 2
    if any(k in p for k in ("animace","audiovizu","game design","figurální","prostorová tvorba",
        "design interi","design nábytku","design nabytku","konstrukč","výtvarná příprava",
        "výtvarná tvorba","vizualizace","grafické umělecké")): return 3
    return None
def blk(h):
    h=int(round(h)); out=[]
    while h>0: out.append(min(3,h)); h-=min(3,h)
    return out
raw=[]
for ln in open("raw_skup.txt",encoding="utf-8"):
    ln=ln.rstrip("\n")
    if not ln: continue
    t,pred,skup,uk,hod=ln.split("|")
    if t not in GDMI or pred in LANG: continue
    raw.append((t,pred,skup,uk,float(hod)))
# merge PT/CJ jako v generátoru
present=defaultdict(set)
for t,pred,skup,uk,hod in raw: present[(t,skup,uk)].add(pred)
def key_of(t,pred,skup,uk):
    pr=present[(t,skup,uk)]
    if pred in ("FR","0D") and ("FR" in pr and "0D" in pr): return "PT","Písmo a typografie"
    if pred in ("0P","0R"): return "CJ","Český jazyk a literatura"
    return pred,NAME.get(pred,pred)
agg=defaultdict(float); meta={}
for t,pred,skup,uk,hod in raw:
    kp,naz=key_of(t,pred,skup,uk); agg[(t,kp,skup,uk)]+=hod; meta[(t,kp,skup,uk)]=naz
odb=defaultdict(list); vse=defaultdict(list)
odb_h=0; vse_h=0
for (t,kp,skup,uk),hod in agg.items():
    naz=meta[(t,kp,skup,uk)]; wh=hod/2.0
    F=force_len(naz,t,kp); Ls=None
    if F:
        Ls=[]; rem=int(round(wh))
        while rem>0: Ls.append(min(F,rem)); rem-=min(F,rem)
    else: Ls=blk(wh)
    rec=(naz,round(wh,1),Ls,skup,uk)
    if is_vseob(naz): vse[lbl(t)].append(rec); vse_h+=wh
    else: odb[lbl(t)].append(rec); odb_h+=wh
print("=== ODBORNÉ (sázíme teď) — %d jednotek-skupin, %.0f h/tyd ==="%(sum(len(v) for v in odb.values()),odb_h))
for cl in sorted(odb):
    print("\n--",cl,"--")
    for naz,wh,Ls,skup,uk in sorted(odb[cl],key=lambda r:-r[1]):
        big="★" if (Ls and max(Ls)>=3) else " "
        print("  %s %-34s %4.1fh bloky=%s skup=%s uk=%s"%(big,naz[:34],wh,Ls,skup,uk))
print("\n\n=== VŠEOBECNÉ (zatím NE) — %d jednotek-skupin, %.0f h/tyd ==="%(sum(len(v) for v in vse.values()),vse_h))
for cl in sorted(vse):
    nm=sorted(set(r[0] for r in vse[cl]))
    print("  %s: %s"%(cl,", ".join(nm)))
