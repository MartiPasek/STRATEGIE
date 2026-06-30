dst="gen_odb4.py"
s=open("gen_odb3.py").read()
BLOCK='''    # --- Kompaktnost ucitele (Marti 23.6.): penalizuj OKNA = volna hodina mezi vyukou (vc. jazyku/TV) ---
    _holes=[]
    _allt=set(k[0] for k in tc.keys())
    for _ht in _allt:
        if _ht=="UXS9D": continue
        for _hd in range(1,6):
            occ={}
            for _h in range(1,11):
                if (_ht,_hd,_h) in tbusy:
                    occ[_h]=True
                else:
                    _ys=tc.get((_ht,_hd,_h),[])
                    if _ys:
                        _ob=m.NewBoolVar("oc_%s_%d_%d"%(_ht,_hd,_h))
                        for _y in _ys: m.Add(_ob>=_y)
                        occ[_h]=_ob
            present=sorted(occ)
            if len(present)<2: continue
            for _h in range(present[0]+1,present[-1]):
                if occ.get(_h) is True: continue
                bef=[occ[x] for x in present if x<_h]
                aft=[occ[x] for x in present if x>_h]
                if not bef or not aft: continue
                _ba=m.NewBoolVar("ba_%s_%d_%d"%(_ht,_hd,_h))
                if any(v is True for v in bef): m.Add(_ba==1)
                else:
                    for v in bef: m.Add(_ba>=v)
                    m.Add(_ba<=sum(v for v in bef))
                _aa=m.NewBoolVar("aa_%s_%d_%d"%(_ht,_hd,_h))
                if any(v is True for v in aft): m.Add(_aa==1)
                else:
                    for v in aft: m.Add(_aa>=v)
                    m.Add(_aa<=sum(v for v in aft))
                _hole=m.NewBoolVar("hl_%s_%d_%d"%(_ht,_hd,_h))
                if _h in occ:
                    m.Add(_hole>=_ba+_aa+(1-occ[_h])-2)
                else:
                    m.Add(_hole>=_ba+_aa-1)
                _holes.append(_hole)
    m.Maximize(sum(terms) - 40*sum(_mixed) - 25*sum(_holes))'''
old='    m.Maximize(sum(terms) - 40*sum(_mixed))'
assert old in s, "Maximize radek nenalezen"
s=s.replace(old,BLOCK)
open(dst,"w").write(s)
print("napsano",dst,"len",len(s),"| holes blok:", "_holes" in s)
