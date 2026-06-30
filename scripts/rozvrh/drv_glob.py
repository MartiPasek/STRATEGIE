import time as _t
o,un=solve(units,set(tbusy0),set(),float(sys.argv[3]) if len(sys.argv)>3 else 38.0,{})
from collections import defaultdict
target=defaultdict(float)
for trid,pred,skup,uk,hod in raw: target[uk]+=hod/2.0
placed=defaultdict(int)
for c in o:
    for t in c["teachers"]: placed[t]+=c["L"]
print("GLOBAL um",len(o),"neum",len(un),"| hodin",sum(placed.values()),"/ cíl",round(sum(target.values()),1),"=",round(100*sum(placed.values())/sum(target.values())),"%")
print("Vlková",placed["UNS6G"],"| Švehlová UXS9D",placed["UXS9D"],"cíl 20 | Pejřim UTS88",placed["UTS88"],"cíl 20")
json.dump({"cells":o,"un":un},open("gen_pred_cp24g_%d.json"%SEED,"w"))
