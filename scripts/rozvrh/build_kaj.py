# KAJ (Konverzace AJ) z bakalari_uvaz_cyc (mirror) — každý učitel 1h/ročník
CUR={"27":"1.A","29":"1.CR","2A":"1.GD","28":"1.L","2B":"1.MI","2C":"1.O","21":"2.A","20":"2.B","22":"2.CR","25":"2.GD","26":"2.MI","23":"2.VO","24":"2.ZO","1S":"3.A","1T":"3.CR","1U":"3.GD","1W":"3.MI","1Y":"3.VO","1Z":"3.ZO"}
def roll(c):
    z=CUR.get(c)
    return str(int(z[0])+1)+z[1:] if (z and z[0].isdigit()) else c
rev={roll(c):c for c in CUR}  # rolled name -> current code
# (teacher, [rolled class names], hodin) z dotazu
KAJ=[
 ("UPS77",["3.CR","3.MI","3.VO","4.CR","4.MI"],2),
 ("UZSA7",["3.CR","3.MI","4.ZO"],2),
 ("UHDY5",["3.CR","3.VO"],1),
 ("UWS8Z",["3.GD","3.MI","3.VO","3.ZO"],1),
 ("UTEMU",["3.GD","3.MI","3.VO","3.ZO","4.CR","4.GD","4.MI","4.VO"],2),
 ("UZS4W",["3.GD","3.ZO"],1),
 ("URS7L",["3.GD","4.GD","4.MI"],2),
 ("UYMUL",["3.MI","3.VO","4.MI","4.VO"],2),
 ("UZS3W",["3.ZO","4.CR","4.ZO"],2),
 ("U0SAI",["4.CR","4.GD","4.MI","4.VO","4.ZO"],1),
 ("UOS6Q",["4.CR","4.VO","4.ZO"],1),
 ("URS7F",["4.GD"],1),
]
units=[]; tot=0
for uk,cls,hod in KAJ:
    y3=[rev[c] for c in cls if c.startswith("3.")]
    y4=[rev[c] for c in cls if c.startswith("4.")]
    parts=[("3",y3),("4",y4)]
    nyears=sum(1 for _,p in parts if p)
    assert nyears==hod, f"{uk}: roč {nyears} != hodin {hod}"
    for yr,p in parts:
        if not p: continue
        spoj=f"K{yr}{uk[-2:]}"  # unikátní spoj
        units.append((spoj,uk,"KAJ","Konverzace v anglickém jazyce",1,",".join(sorted(p)),yr))
        tot+=1
# zapiš kaj_units.txt: spoj|uk|pred|pnaz|hod|tridy|rocnik
with open("kaj_units.txt","w",encoding="utf-8") as f:
    for u in units: f.write("|".join(map(str,u))+"\n")
print(f"KAJ jednotek: {tot} (suma hodin = {tot})  | 3.roč: {sum(1 for u in units if u[6]=='3')}  4.roč: {sum(1 for u in units if u[6]=='4')}")
for u in units: print(" ",u[0],u[1],u[5])
