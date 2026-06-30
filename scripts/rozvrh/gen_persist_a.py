import json
from collections import defaultdict
CUR={"27":"1.A","29":"1.CR","2A":"1.GD","28":"1.L","2B":"1.MI","2C":"1.O","21":"2.A","20":"2.B","22":"2.CR","25":"2.GD","26":"2.MI","23":"2.VO","24":"2.ZO","1S":"3.A","1T":"3.CR","1U":"3.GD","1W":"3.MI","1Y":"3.VO","1Z":"3.ZO"}
OVR={"2E":"1.GD","2F":"1.MI"};NEW={"2D":"1.D","2G":"1.G","2I":"1.I","2J":"1.J"}
def roll(c):
    if c in OVR: return OVR[c]
    z=CUR.get(c)
    if z and z[0].isdigit(): return str(int(z[0])+1)+z[1:]
    return NEW.get(c,c)
def q(s): return "'"+str(s).replace("'","''")+"'"
GDMI={"2A","25","1U","2B","26","1W","2E","2F"};WH={}
for ln in open('raw_skup.txt'):
    ln=ln.strip()
    if not ln: continue
    t,p,s,u,h=ln.split('|')
    if t in GDMI and p=='0P': WH[t]=s
COLS="(verze_id,tenant_id,den,hodina,kod_trid,trida,kod_skup,kod_spoj,skup_zkr,kod_pred,pred,kod_ucit,ucitel,kod_mist,mist,kod_cykl,cj_uroven,blok)"
out=["DELETE FROM tenant.rozvrh_bunka WHERE verze_id=4 AND blok='predmet';"]
rows=[]
for c in json.load(open('gen_pred_cp24g_0.json'))['cells']:
    t=c['trid'];sk=c['obor'];szkr='' if sk==WH.get(t) else sk;uk=c['teachers'][0];room=c.get('room') or ''
    for i in range(c['L']):
        rows.append("(4,13,%d,%d,'',%s,%s,'',%s,'',%s,%s,'',%s,%s,'',NULL,'predmet')"%(c['d'],c['h1']+i,q(roll(t)),q(sk),q(szkr),q(c['pnaz']),q(uk),q(room),q(room)))
out.append("INSERT INTO tenant.rozvrh_bunka "+COLS+" VALUES\n"+",\n".join(rows)+";")
open('persist_v4.sql','w',encoding='utf-8').write("\n".join(out))
print("verze 4 predmet řádků",len(rows))
