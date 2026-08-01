# -*- coding: utf-8 -*-
"""Verifikace TUZ multi-line: platák 8088 (12 plateb) vs PAY_TUZ_02-07-2026_6-00-37.p11"""
import glob, os
from gemini_render import render_tuz_line

# (CisloRadku, Castka, vs, ks, ss, KodUstavu, recv, klient, splat, ucel)
ROWS = [
    (1, 7769.60, "1200016758", "0308", "", "2700", "1545471501", "9251651001", "260702", "500001307 Geis CZ s.r.o."),
    (2, 5052.00, "2606621", "0008", "", "0300", "173352629", "9251651001", "260702", "500001306 Helukabel CZ s.r.o."),
    (3, 19481.00, "202605255", "0308", "", "0300", "249349646", "9251651001", "260702", "500001287 Pilsco s.r.o."),
    (4, 18347.47, "12672162", "0008", "", "0600", "180936067", "9251651001", "260702", "500001412 Barevné kovy Tetour, s.r.o."),
    (5, 1448.10, "2601002361", "0008", "", "2700", "264473004", "9251651001", "260702", "500001319 Jork"),
    (6, 5716.00, "260101217", "0308", "", "0300", "270859181", "9251651001", "260702", "500001393 LANDMARK TAX s.r.o."),
    (7, 1329.45, "27962026", "0008", "", "0100", "1658643621", "9251651001", "260702", "500001446 TTI s.r.o."),
    (8, 1490.42, "27932026", "0008", "", "0100", "1658643621", "9251651001", "260702", "500001447 TTI s.r.o."),
    (9, 216.86, "261015324", "0008", "", "0300", "168725128", "9251651001", "260702", "500001383 Papera s.r.o"),
    (10, 2904.00, "2260250", "0008", "", "0300", "254093630", "9251651001", "260702", "500001455 VINETY ART s.r.o."),
    (11, 8949.76, "212600477", "0008", "", "5500", "6071954001", "9251651001", "260702", "500001467 CUPRO PK s.r.o."),
    (12, 1982.52, "1261010220", "0008", "", "0300", "366094312", "9251651001", "260702", "500001320 Bi Esse Cz s.r.o."),
]

gen = b""
for (cr, castka, vs, ks, ss, ku, recv, kli, splat, ucel) in ROWS:
    line = render_tuz_line(porad=cr, datum_vytv="260702", castka=castka, ks=ks, vs=vs,
                           ss=ss, kod_ustavu_prij=ku, ucet_prij=recv, ucet_klient=kli,
                           datum_splat=splat, ucel=ucel)
    gen += line.encode("cp1250") + b"\r\n"

up = "/sessions/lucid-kind-knuth/mnt/uploads"
real = open(glob.glob(os.path.join(up, "*PAY_TUZ_02-07-2026_6-00-37.p11"))[0], "rb").read()

print("GEN len :", len(gen), " REAL len:", len(real))
print("MATCH   :", gen == real)
if gen != real:
    for i, (a, b) in enumerate(zip(gen, real)):
        if a != b:
            print("prvni rozdil na bytu", i)
            print("  GEN :", repr(gen[max(0, i-20):i+20]))
            print("  REAL:", repr(real[max(0, i-20):i+20]))
            break
