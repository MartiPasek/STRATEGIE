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
    body="".join(open(os.path.join(PARTS,n),encoding="utf-8",newline="").read() for n in names)
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
