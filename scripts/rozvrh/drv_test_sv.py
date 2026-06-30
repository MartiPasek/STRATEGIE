sv=[u for u in units if "UXS9D" in u["teachers"]]
print("Švehlová units:",len(sv),"souhrn L:",sum(u["L"] for u in sv),"| předměty:",sorted(set(u["pnaz"] for u in sv)))
for u in sv: print("  ",u["trid"],u["pnaz"][:28],"L",u["L"],"rooms",u["rooms"],"cap",u["cap"])
o,un,_=solve(sv,set(tbusy0),set(),20.0,{})
print("SAMOTNÁ Švehlová umístěno hodin:",sum(c["L"] for c in o),"/ cíl",sum(u["L"] for u in sv),"| neum:",[(x[1][:20],x[2]) for x in un])
