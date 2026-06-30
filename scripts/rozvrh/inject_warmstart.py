s=open("gen_odb6.py").read()
# 1) modul-level flag
old1='TLIMIT={"UTS88":4,"UOS6U":4,"UZS4O":4,"UOS6X":3,"UVS8S":2,"UUS8D":4,"UPS70":3,"UXS9D":3}'
assert old1 in s
s=s.replace(old1, old1+"\n_SYNC_ON=True")
# 2) gate sync + cohort loops
a2='    _sync=[]\n    for cc,(la,lb) in HALF.items():'
assert a2 in s
s=s.replace(a2,'    _sync=[]\n    for cc,(la,lb) in (HALF.items() if _SYNC_ON else []):')
a3='    for cc,pairs in COH.items():'
assert a3 in s
s=s.replace(a3,'    for cc,pairs in (COH.items() if _SYNC_ON else []):')
# 3) dvoufazovy driver
old4='o,un,assign=solve(units,set(tbusy0),set(rbusy0),SEC,{})'
assert old4 in s
new4='''import time as _tm
_SYNC_ON=False
_t0=_tm.time()
o0,_u0,a0=solve(units,set(tbusy0),set(rbusy0),min(SEC*0.4,28.0),{})
print("faze1 bez-sync: umisteno",len(o0),"/",len(units),"za %.0fs"%(_tm.time()-_t0))
_SYNC_ON=True
_rem=max(SEC-(_tm.time()-_t0),20.0)
o,un,assign=solve(units,set(tbusy0),set(rbusy0),_rem,{},hint=a0)'''
s=s.replace(old4,new4)
open("gen_odb7.py","w").write(s)
print("napsano gen_odb7.py len",len(s))
