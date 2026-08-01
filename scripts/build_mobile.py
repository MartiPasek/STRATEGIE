#!/usr/bin/env python3
"""Slepi partials z apps/api/static/mobile_parts/NN_nazev.(js|css|html) do
apps/api/static/mobile.html. Rozhodnuti C23 (5.7.2026): mechanismus A - build-step
concat, NE deploy-time. Workflow: edit partial -> spust tenhle skript -> commit
partial + mobile.html. mobile.html je GENEROVANY, needituj primo.
"""
import os
HERE=os.path.dirname(os.path.abspath(__file__))
REPO=os.path.dirname(HERE)
PARTS=os.path.join(REPO,"apps/api/static/mobile_parts")
OUT=os.path.join(REPO,"apps/api/static/mobile.html")
BANNER=("<!-- ============================================================\n"
        "     GENEROVANO scriptem scripts/build_mobile.py z\n"
        "     apps/api/static/mobile_parts/ . NEEDITUJ TENTO SOUBOR PRIMO -\n"
        "     edituj partials a spust: python scripts/build_mobile.py\n"
        "     ============================================================ -->\n")
def build():
    names=sorted(f for f in os.listdir(PARTS) if f[0:2].isdigit())
    contents=[open(os.path.join(PARTS,n),encoding="utf-8",newline="").read() for n in names]
    # POZOR (Marti + Claude-23, 1.8.2026): naivni vlozeni </script><script> mezi .js
    # fragmenty ZDE bylo ZKUSENO a ROZBILO appku (vypadek /mobile 1.8.2026) - fragmenty
    # 20+ NEJSOU nezavisle IIFE, jsou to hole function deklarace uvnitr JEDNE sdilene
    # obalove funkce otevrene v 10_core.js a zavrene az v 74_claude27_render_init.js,
    # sdileji lokalni promenne (app, el, topbar, SCREENS, B) pres closure, ne pres
    # window. Skutecna izolace se vyviji a testuje na /mobile2 (g2007.soubor,
    # apps/api/static/mobile2.html, mobile_parts2/*) - NEPRIDAVAT separatory sem,
    # dokud neni reseni plne overene a prevedene i sem.
    body="".join(contents)
    # vloz banner za prvni radek (<!DOCTYPE html>)
    nl=body.find("\n")
    out=body[:nl+1]+BANNER+body[nl+1:]
    with open(OUT,"w",encoding="utf-8",newline="") as g:
        g.write(out)
    return names, len(out)
if __name__=="__main__":
    names,ln=build()
    print("partials:", len(names)); [print(" ",n) for n in names]
    print("mobile.html napsan, znaku:", ln)
