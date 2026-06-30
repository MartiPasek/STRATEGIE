#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Porovnani realneho uvazku (uvaz_real.txt z mirroru) vs muj raw_skup -> kde chybi odborne hodiny.
from collections import defaultdict
GDMI_LBL=['1.GD','2.GD','3.GD','4.GD','1.MI','2.MI','3.MI','4.MI']
GDMI_CODE_LBL={'2E':'1.GD','2F':'1.MI'}  # nove tridy v uvazku jako "1.? (2E)"
def touches_gdmi(tridy):
    if any(l in tridy for l in GDMI_LBL): return True
    if '(2E)' in tridy or '(2F)' in tridy: return True
    return False
VSEOB_KW=["český jazyk","literatura","literární","matematik","fyzik","chemie","dějepis","dějiny",
 "historie","občansk","společenskovědní","základy spol","základy společ","zeměp","ekolog","biolog",
 "přírodních věd","psycholog","právo","ekonom","management","marketing","finance","daň","účetn",
 "nauka","náuka","třídnick","chování","kariér","kulturní dědictví","umění v souvislostech",
 "člověk a média","profesní komunikace","jazykové praktikum","informační a komunikační","výpočet",
 "praktikum","seminář","mezinárodní vztahy","naučná literatura","propagace","aranžování",
 "zbožíznalství","jakost","služby cestov","průvodcov","cestovní ruch"]
JAZYK_KW=["anglický jazyk","německý jazyk","francouzský jazyk","španělský jazyk","ruský jazyk",
 "portugalský jazyk","konverzace v","jazyk a komunikace","cizojazyčná","tělesná výchova",
 "tělesn","digitální kresba","3d modelování","modelování"]
def kind(naz):
    p=naz.lower()
    if any(k in p for k in JAZYK_KW): return "LANG"
    if any(k in p for k in VSEOB_KW): return "VSEOB"
    return "ODB"
# realny uvazek per ucitel (jen ODB, GDMI)
real=defaultdict(float); real_det=defaultdict(list)
for ln in open("uvaz_real.txt",encoding="utf-8"):
    ln=ln.strip().rstrip("|").strip()
    if not ln or "~" not in ln: continue
    parts=ln.split("~")
    if len(parts)<5: continue
    uk,naz,hod,_nm,tridy=parts[0],parts[1],parts[2],parts[3],parts[4]
    if not touches_gdmi(tridy): continue
    k=kind(naz)
    try: h=float(hod)
    except: continue
    if k=="ODB": real[uk]+=h; real_det[uk].append((naz,h,tridy.strip()))
# moje raw_skup per ucitel (ODB, GDMI)
GDMI={'2A','25','1U','2B','26','1W','2E','2F'}
LANG={'4','5','1G','1I','9B','AN','43','46','55','17'}
NAME={}
for ln in open('predmap.txt',encoding='utf-8'):
    a=ln.rstrip('\n').split('|')
    if a[0]: NAME[a[0]]=a[1]
mine=defaultdict(float)
for ln in open('raw_skup.txt',encoding='utf-8'):
    ln=ln.strip()
    if not ln: continue
    t,p,s,u,h=ln.split('|')
    if t not in GDMI or p in LANG: continue
    naz=NAME.get(p,p)
    if kind(naz)=="ODB": mine[u]+=float(h)/2
# porovnani
print("%-8s %6s %6s %6s" % ("ucitel","real","moje","CHYBI"))
allk=sorted(set(list(real)+list(mine)), key=lambda u:-(real[u]-mine[u]))
tot_chybi=0
for u in allk:
    d=real[u]-mine[u]
    if abs(d)>0.4:
        print("%-8s %6.1f %6.1f %6.1f" % (u,real[u],mine[u],d))
        if d>0: tot_chybi+=d
print("---")
print("real ODB celkem:",round(sum(real.values()),1),"| moje ODB celkem:",round(sum(mine.values()),1))
print("CHYBI celkem (real>moje):",round(tot_chybi,1),"h")
# detail nejvetsich chybejicich
print("\nDETAIL TOP chybejici:")
for u in allk[:8]:
    if real[u]-mine[u]>0.4:
        print(" ",u,"real",round(real[u],1),"moje",round(mine[u],1),"->",[(n,h,tr) for n,h,tr in real_det[u]])
