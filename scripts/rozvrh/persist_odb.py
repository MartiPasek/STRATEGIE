import json,sys
VAR=sys.argv[1] if len(sys.argv)>1 else "A"
SEED=sys.argv[2] if len(sys.argv)>2 else "0"
CUR={"2A":"1.GD","25":"2.GD","1U":"3.GD","2B":"1.MI","26":"2.MI","1W":"3.MI"}
OVR={"2E":"1.GD","2F":"1.MI"}
def roll(c):
    if c in OVR: return OVR[c]
    z=CUR.get(c)
    if z and z[0].isdigit(): return str(int(z[0])+1)+z[1:]
    return c
def q(s): return "'"+str(s).replace("'","''")+"'"
GDMI={"2A","25","1U","2B","26","1W","2E","2F"};WH={}
for ln in open('raw_skup.txt',encoding='utf-8'):
    ln=ln.strip()
    if not ln: continue
    t,p,s,u,h=ln.split('|')
    if t in GDMI and p=='0P': WH[t]=s
COLS="(verze_id,tenant_id,den,hodina,kod_trid,trida,kod_skup,kod_spoj,skup_zkr,kod_pred,pred,kod_ucit,ucitel,kod_mist,mist,kod_cykl,cj_uroven,blok)"
out=["DELETE FROM tenant.rozvrh_bunka WHERE verze_id=4 AND tenant_id=13 AND blok='predmet';"]
rows=[]
for c in json.load(open('gen_odb_%s_%s.json'%(VAR,SEED)))['cells']:
    t=c['trid'];sk=c['obor'];szkr='' if sk==WH.get(t) else sk;uk=c['teachers'][0];room=c.get('room') or ''
    for i in range(c['L']):
        rows.append("(4,13,%d,%d,'',%s,%s,'',%s,'',%s,%s,'',%s,%s,'',NULL,'predmet')"%(
            c['d'],c['h1']+i,q(roll(t)),q(sk),q(szkr),q(c['pnaz']),q(uk),q(room),q(room)))
out.append("INSERT INTO tenant.rozvrh_bunka "+COLS+" VALUES\n"+",\n".join(rows)+";")
open('persist_v4_odb.sql','w',encoding='utf-8').write("\n".join(out))
print("verze 4 predmet radku:",len(rows),"| bunky:",len(json.load(open('gen_odb_%s_%s.json'%(VAR,SEED)))['cells']))
print("velikost SQL:",len("\n".join(out)),"B")
