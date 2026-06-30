# použij funkce z gen_core20 (bez solve)
miss=set(); ok=0
import json as _j
seen=set()
for u in units:
    key=(_lbl(u["trid"]),u["pnaz"])
    if key in seen: continue
    seen.add(key)
    dr=room_doc(u["trid"],u["pnaz"])
    if dr: ok+=1; print(f'  ✓ {_lbl(u["trid"]):6} {u["pnaz"][:34]:34} -> {dr}')
    else:
        if u["rooms"]: miss.add((key[0],u["pnaz"],"heur:"+",".join(u["rooms"])))
        else: miss.add((key[0],u["pnaz"],"BEZ UČEBNY"))
print("\n=== bez doc-učebny (heuristika/akademické) ===")
for c,n,r in sorted(miss): print(f'  {c:6} {n[:34]:34} {r}')
print("\ndoc-matched:",ok)
