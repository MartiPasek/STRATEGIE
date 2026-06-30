s=open("gen_odb5.py").read()
BLOCK='''    # === Klárka 23.6.: SYNCHRONIZACE POLOVIN (1.sk ∥ 2.sk / DI ∥ MT) ===
    # Pulky tridy musi mit odborne bloky NA SOBE. Whole-class lanes vynechany.
    HALF={
      "2E":(["FW"],["FX"]),
      "25":(["5P","KB","KD"],["5Q","KC","KE"]),
      "1U":(["XD","D3","D4"],["XE","D5","D6"]),
      "2F":(["FY"],["FZ"]),
      "26":(["5R"],["KF","KG","5S"]),
      "1W":(["XF"],["EA","EB","XG"]),
    }
    # kohortni exkluzivita: hlavni lane vs GDN-sub (stejna kohorta -> nesmi naraz; GDN-suby smi paralelne)
    COH={
      "25":[(["5P"],["KB","KD"]),(["5Q"],["KC","KE"])],
      "1U":[(["XD"],["D3","D4"]),(["XE"],["D5","D6"])],
    }
    def _occ(lanes,cc,d,x,tag):
        vs=[]
        for ln in lanes: vs+=cl.get(((cc,ln),d,x),[])
        if not vs: return None
        b=m.NewBoolVar("o_%s_%s_%d_%d"%(tag,cc,d,x))
        for v in vs: m.Add(b>=v)
        m.Add(b<=sum(vs))
        return b
    _sync=[]
    for cc,(la,lb) in HALF.items():
        for d in range(1,6):
            for x in range(1,11):
                ao=_occ(la,cc,d,x,"A"); bo=_occ(lb,cc,d,x,"B")
                if ao is None and bo is None: continue
                if ao is None: ao=0
                if bo is None: bo=0
                xo=m.NewBoolVar("xo_%s_%d_%d"%(cc,d,x))
                m.Add(xo>=ao-bo); m.Add(xo>=bo-ao)   # XOR = jen jedna pulka odborne
                _sync.append(xo)
    for cc,pairs in COH.items():
        for mains,subs in pairs:
            for d in range(1,6):
                for x in range(1,11):
                    mo=_occ(mains,cc,d,x,"M"); so=_occ(subs,cc,d,x,"S")
                    if mo is not None and so is not None:
                        m.Add(mo+so<=1)   # hlavni a GDN nesmi naraz (stejni studenti)
    m.Maximize(sum(terms) - 40*sum(_mixed) - 25*sum(_holes) - 150*sum(_sync))'''
old='    m.Maximize(sum(terms) - 40*sum(_mixed) - 25*sum(_holes))'
assert old in s, "Maximize radek nenalezen"
s=s.replace(old,BLOCK)
open("gen_odb6.py","w").write(s)
print("napsano gen_odb6.py len",len(s))
