import time as _t,os
hint=None
HF="g19_hint_%s.json"%VARIANT
if os.path.exists(HF): hint=json.load(open(HF))
o,un,assign=solve(units,set(tbusy0),set(),float(sys.argv[3]) if len(sys.argv)>3 else 38.0,{},hint)
from collections import defaultdict
target=defaultdict(float)
for trid,pred,skup,uk,hod in raw: target[uk]+=hod/2.0
placed=defaultdict(int)
for c in o:
    for t in c["teachers"]: placed[t]+=c["L"]
cov=round(100*sum(placed.values())/sum(target.values()))
print("RESUME[%s] um"%VARIANT,len(o),"neum",len(un),"| hodin",sum(placed.values()),"/",round(sum(target.values()),1),"=",cov,"%")
print("Vlkova",placed["UNS6G"],"Svehlova",placed["UXS9D"],"Pejrim",placed["UTS88"],"Rousova",placed["UZS4O"],"Jezkova",placed["UZSA4"])
best=0; BF="g19_best_%s.txt"%VARIANT
if os.path.exists(BF):
    try: best=int(open(BF).read() or 0)
    except: best=0
if len(o)>=best:
    json.dump(assign,open(HF,"w")); open(BF,"w").write(str(len(o)))
    json.dump({"cells":o,"un":un},open("gen_pred_v19_%s.json"%VARIANT,"w"))
    print("ULOZENO best",len(o))
else: print("horsi nez best",best)
