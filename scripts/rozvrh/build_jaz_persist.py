import json,sys
from collections import defaultdict
CUR={"27":"1.A","29":"1.CR","2A":"1.GD","28":"1.L","2B":"1.MI","2C":"1.O","21":"2.A","20":"2.B","22":"2.CR","25":"2.GD","26":"2.MI","23":"2.VO","24":"2.ZO","1S":"3.A","1T":"3.CR","1U":"3.GD","1W":"3.MI","1Y":"3.VO","1Z":"3.ZO"}
OVR={"2E":"1.GD","2F":"1.MI"};NEW={"2D":"1.D","2G":"1.G","2I":"1.I","2J":"1.J"}
def roll(c):
    if c in OVR: return OVR[c]
    z=CUR.get(c)
    if z and z[0].isdigit(): return str(int(z[0])+1)+z[1:]
    return NEW.get(c,c)
def q(s): return "'"+str(s).replace("'","''")+"'"
res=json.load(open("gen_lang3_out.json"))
# pairs: idx->verze
PAIRS=[[(0,4),(1,5)],[(2,6),(3,7)],[(4,8),(5,9)]]
which=int(sys.argv[1])
COLS="(verze_id,tenant_id,den,hodina,kod_trid,trida,kod_skup,kod_spoj,skup_zkr,kod_pred,pred,kod_ucit,ucitel,kod_mist,mist,kod_cykl,cj_uroven,blok)"
verzes=[v for _,v in PAIRS[which]]
out=["DELETE FROM tenant.rozvrh_bunka WHERE tenant_id=13 AND verze_id IN (%s) AND blok='jazyky';"%(",".join(map(str,verzes)))]
total=0
for idx,verze in PAIRS[which]:
    cells=res[idx]["cells"]; g=defaultdict(lambda:{"cls":set()}); meta={}
    for c in cells:
        k=(c["spoj"],c["d"],c["h"]); g[k]["cls"].add(roll(c["c"])); meta[k]=(c["uk"],c["pred"],c["zkr"],c["cj"])
    rows=[]
    for (spoj,d,h),v in g.items():
        uk,pnaz,zkr,cj=meta[(spoj,d,h)]; trida=", ".join(sorted(v["cls"]))
        rows.append("(%d,13,%d,%d,'',%s,'',%s,%s,'',%s,%s,'','','','',%d,'jazyky')"%(verze,d,h,q(trida),q(spoj),q(zkr),q(pnaz),q(uk),cj))
    out.append("INSERT INTO tenant.rozvrh_bunka "+COLS+" VALUES\n"+",\n".join(rows)+";"); total+=len(rows)
sql="\n".join(out)
open("/sessions/clever-fervent-edison/mnt/STRATEGIE/scripts/claude_sql/CLAUDE_SQL.sql","w",encoding="utf-8").write(sql)
print("dávka",which,"verze",verzes,"řádků",total,"velikost",len(sql),"B")
