#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generátor certifikátu k pracovnímu výročí (Šárka / Claude-25, 24.7.2026).

Vezme designovou šablonu `_Predlohy/Certifikát 10 let.pdf`, doplní jméno, datum
a barevný podpis Marti Paška (spodní z `MartiPasek_podpis_barevny.pdf`) a uloží
tiskový PDF. Šablona pro placeholder „Jméno Příjmení" je vektorová kaligrafie —
překrýváme ji čistým pruhovaným pozadím zkopírovaným zespodu, pak píšeme jméno.

Použití:
    python gen_certifikat.py "Jiří Veverka" --datum "1. 8. 2026" \
        --out "../_Vyplnene/Certifikat_10let_Jiri_Veverka.pdf"

Pozn.: font kaligrafie není v systému → jméno sázíme DejaVu Serif Italic (má české
znaky). Kdyby byl k dispozici script font s háčky/čárkami, stačí přepsat FONT_NAME.
"""
import argparse
import os
import numpy as np
import pypdfium2 as pdfium
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
PREDLOHY = os.path.join(HERE, "..", "_Predlohy")
TMPL = os.path.join(PREDLOHY, "Certifikát 10 let.pdf")
SIG = os.path.join(PREDLOHY, "MartiPasek_podpis_barevny.pdf")
FONT_NAME = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf"
FONT_SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
DPI = 300
NAVY = (35, 20, 95)


def generuj(jmeno, datum, out_path, podpis_popis="Marti Pašek, jednatel"):
    S = DPI / 72.0

    def px(x, y):
        return int(x * S), int(y * S)

    tpl = pdfium.PdfDocument(TMPL)[0].render(scale=S).to_pil().convert("RGB")
    dr = ImageDraw.Draw(tpl)

    # 1) překryj placeholder „Jméno Příjmení" čistým pruhovaným pozadím zespodu
    tpl.paste(tpl.crop((*px(60, 430), *px(590, 502))), px(60, 250))

    # 2) jméno (navy italic), zarovnané vlevo, vertikálně na střed pásu
    fnt = ImageFont.truetype(FONT_NAME, int(46 * S))
    bb = dr.textbbox((0, 0), jmeno, font=fnt)
    dr.text((px(96, 0)[0], int(288 * S - (bb[3] - bb[1]) / 2 - bb[1])), jmeno, font=fnt, fill=NAVY)

    # 3) datum na řádek DATUM
    dfnt = ImageFont.truetype(FONT_SANS, int(13 * S))
    dr.text(px(126, 505), datum, font=dfnt, fill=(40, 40, 60))

    # 4) podpis = SPODNÍ z podpisové stránky (čistější), bílá -> průhledná
    sig = pdfium.PdfDocument(SIG)[0].render(scale=S).to_pil().convert("RGB")
    sa = np.asarray(sig).astype(int)
    m = (sa[:, :, 0] < 130)
    m[: int(sa.shape[0] * 0.55), :] = False   # jen spodní polovina
    ys, xs = np.where(m)
    pad = 12
    crop = sig.crop((xs.min() - pad, ys.min() - pad, xs.max() + pad, ys.max() + pad))
    bright = np.asarray(crop).astype(int).max(axis=2)
    alpha = np.clip((250 - bright) * 3, 0, 255).astype("uint8")
    sig_rgba = Image.fromarray(np.dstack([np.asarray(crop), alpha]), "RGBA")
    th = int(50 * S)
    sig_rgba = sig_rgba.resize((int(sig_rgba.width * th / sig_rgba.height), th))
    cxp, cyb = px(455, 512)
    tpl.paste(sig_rgba, (cxp - sig_rgba.width // 2, cyb - sig_rgba.height), sig_rgba)
    cfnt = ImageFont.truetype(FONT_SANS, int(11 * S))
    cb = dr.textbbox((0, 0), podpis_popis, font=cfnt)
    dr.text((cxp - (cb[2] - cb[0]) // 2, px(0, 516)[1]), podpis_popis, font=cfnt, fill=(40, 40, 60))

    tpl.save(out_path, "PDF", resolution=DPI)
    return out_path


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("jmeno")
    ap.add_argument("--datum", required=True, help="např. '1. 8. 2026'")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    print("Uloženo:", generuj(a.jmeno, a.datum, a.out))
