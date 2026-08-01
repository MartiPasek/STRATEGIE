# -*- coding: utf-8 -*-
"""Verifikace ZAHR: platba 14119 vs 1. řádek PAY_ZAHR_02-07-2026_6-00-37.f84"""
import glob, os
from gemini_render import render_zahr_line

line = render_zahr_line(
    porad=1, datum_vytv8="20260702", castka=3506.94, mena="EUR",
    up_nazev="Československá obchodní banka, a.s.", up_ulice="", up_misto="",
    zup_nazev="Česká republika",
    op_firma="ControlTech s.r.o.", op_ulice="Ovčáry 297", op_misto="Ovčáry",
    zop_nazev="Česká republika",
    nas_ucet="9251651001", iban="CZ4403000000000074065683",
    poplatky="SHA", tit="120", cil_zeme="CZ", hlav_id=14119,
    p1="10114032", p2="10114188", p3="", p4="",
    priorita=0, nas_mena="EUR", swift="CEKOCZPP", datum_splat="260702")
gen = line.encode("cp1250") + b"\r\n"

up = "/sessions/lucid-kind-knuth/mnt/uploads"
real_full = open(glob.glob(os.path.join(up, "*PAY_ZAHR_02-07-2026_6-00-37.f84"))[0], "rb").read()
real_line1 = real_full.split(b"\r\n")[0] + b"\r\n"

print("GEN len :", len(gen), " REAL1 len:", len(real_line1))
print("MATCH   :", gen == real_line1)
if gen != real_line1:
    for i, (a, b) in enumerate(zip(gen, real_line1)):
        if a != b:
            print("prvni rozdil na bytu", i)
            print("  GEN :", repr(gen[max(0, i-25):i+25]))
            print("  REAL:", repr(real_line1[max(0, i-25):i+25]))
            break
    else:
        print("delkovy rozdil")
