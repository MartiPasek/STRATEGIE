import time as _t
SEC=float(sys.argv[3]) if len(sys.argv)>3 else 60.0
o,un,assign=solve(units,set(tbusy0),set(),SEC,{})
from collections import defaultdict
tot=sum(u["L"] for u in units); pl=sum(c["L"] for c in o)
print("ODB umisteno",len(o),"/",len(units),"jednotek | neum",len(un),
      "| hodin",pl,"/",tot,"=",round(100*pl/tot) if tot else 0,"%")
# Vlková (UNS6G) kontrola "ne do vecera"
vl=[c for c in o if "UNS6G" in c["teachers"]]
late=sorted(set(c["d"] for c in vl if c["h1"]+c["L"]-1>=9))
print("Vlkova UNS6G: umisteno",sum(c["L"] for c in vl),"h | pozdni dny(konec>=9h):",late)
for c in sorted(vl,key=lambda x:(x["d"],x["h1"])):
    print("   d%d h%d-%d %-24s %s"%(c["d"],c["h1"],c["h1"]+c["L"]-1,c["pnaz"][:24],c["room"]))
if un:
    print("NEUMISTENO (%d):"%len(un))
    for t,p,L,uk in sorted(un): print("   ",t,p[:30],"L",L,uk)
json.dump({"cells":o,"un":un,"seed":SEED,"variant":VARIANT},
          open("gen_odb_%s_%d.json"%(VARIANT,SEED),"w"))
print("-> gen_odb_%s_%d.json"%(VARIANT,SEED))
