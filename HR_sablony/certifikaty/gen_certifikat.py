#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generátor certifikátu k pracovnímu výročí — EUROSOFT (Šárka / Claude-25).

Návrh „navy pás + medailon", minimalistický, značkově konzistentní.
FIREMNÍ PRAVIDLO (Šárka 4.8.2026): grafika do tisku = písmo GALANO GROTESQUE.
(Pro pracovněprávní dokumenty se používá Verdana — sem se to netýká.)

Skládá se z:
  - navy postranní pás s jemným přechodem + zlatá dělící linka
  - logo EUROSOFT v bílém políčku
  - medailon „10 LET" (dvojitý zlatý kroužek s ryskami + stužka)
  - jemný vodoznak „10", zlatý rámeček s navy rohovými body
  - jméno v Galano SemiBold, skutečný podpis Marti (barevný)

Použití:
    python gen_certifikat.py "Jiří Veverka" --datum "V Plzni dne 1. 9. 2026" \
        --let 10 --out "../_Vyplnene/Certifikat_Jiri_Veverka.pdf"

Výstup: PDF (pokud --out končí .pdf) NEBO PNG. Vždy se vedle uloží i PNG náhled.
Renderuje se v tiskovém rozlišení (scale=3 ≈ 255 DPI na A4 na šířku).
"""
import argparse
import math
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import pypdfium2 as pdfium

HERE = os.path.dirname(os.path.abspath(__file__))
PRE = os.path.join(HERE, "..", "_Predlohy")
LOGO = os.path.join(PRE, "Vzhled firmy", "EC_logo_png.png")
SIG = os.path.join(PRE, "MartiPasek_podpis_barevny.pdf")
GDIR = os.path.join(PRE, "Vzhled firmy", "Galano Grotesque Complete")
GBASE = os.path.join(GDIR, "Rene Bieder - Galano Grotesque")

# firemní barvy
NAVY = (27, 37, 89)
NAVY2 = (18, 26, 62)
GOLD = (193, 157, 74)
GOLDL = (214, 183, 110)
GREY = (90, 100, 124)
LGREY = (140, 150, 170)
GHOST = (27, 37, 89)


def G(sz, w=""):
    """Galano Grotesque daného řezu (w='' = Regular, 'Light', 'Medium',
    'SemiBold', 'Bold', 'Light Italic', ...)."""
    suff = "" if w == "" else " " + w
    return ImageFont.truetype(f"{GBASE}{suff}.otf", int(sz))


def _spaced(dr, cx, y, text, font, fill, sp):
    ws = [dr.textlength(c, font=font) for c in text]
    tot = sum(ws) + sp * (len(text) - 1)
    x = cx - tot / 2
    for c, w in zip(text, ws):
        dr.text((x, y), c, font=font, fill=fill, anchor="lm")
        x += w + sp
    return tot


def _sig_img(hpx):
    """Barevný podpis Marti — spodní (čistší) z podpisové stránky, bílá -> alpha."""
    pg = pdfium.PdfDocument(SIG)[0].render(scale=3).to_pil().convert("RGB")
    a = np.asarray(pg).astype(int)
    m = (a[:, :, 0] < 130)
    m[: int(a.shape[0] * 0.55), :] = False
    ys, xs = np.where(m)
    pad = 10
    crop = pg.crop((xs.min() - pad, ys.min() - pad, xs.max() + pad, ys.max() + pad))
    br = np.asarray(crop).astype(int).max(axis=2)
    al = np.clip((250 - br) * 3, 0, 255).astype("uint8")
    rgba = Image.fromarray(np.dstack([np.asarray(crop), al]), "RGBA")
    return rgba.resize((int(rgba.width * hpx / rgba.height), hpx))


def generuj(jmeno, datum_misto="V Plzni dne 1. 9. 2026", let=10,
            pohlavi=None, out="cert.png", scale=3):
    S = scale
    W, H, SB = 1000 * S, 707 * S, 336 * S
    im = Image.new("RGB", (W, H), (255, 255, 255))
    dr = ImageDraw.Draw(im)

    # navy pás s přechodem
    grad = Image.new("RGB", (1, H))
    for y in range(H):
        t = y / H
        grad.putpixel((0, y), tuple(int(NAVY[i] + (NAVY2[i] - NAVY[i]) * t) for i in range(3)))
    im.paste(grad.resize((SB, H)), (0, 0))
    dr.rectangle([SB, 0, SB + 4 * S, H], fill=GOLD)

    # vodoznak čísla let
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    od.text((666 * S, 400 * S), str(let), font=G(300 * S, "Bold"), fill=(*GHOST, 9), anchor="mm")
    im = Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")
    dr = ImageDraw.Draw(im)

    # zlatý rámeček + navy rohové body
    fx0, fy0, fx1, fy1 = SB + 40 * S, 34 * S, 966 * S, 673 * S
    dr.rectangle([fx0, fy0, fx1, fy1], outline=GOLD, width=max(1, S // 2))
    for (cxc, cyc) in [(fx0, fy0), (fx1, fy0), (fx0, fy1), (fx1, fy1)]:
        dr.rectangle([cxc - 3 * S // 2, cyc - 3 * S // 2, cxc + 3 * S // 2, cyc + 3 * S // 2], fill=NAVY)

    # logo EUROSOFT (bílá varianta) přímo na navy pásu — bez políčka
    lg = Image.open(LOGO).convert("RGBA")
    px = lg.load()
    for yy in range(lg.height):
        for xx in range(lg.width):
            r, g, b, al = px[xx, yy]
            if al > 20:
                px[xx, yy] = (255, 255, 255, al)
    tw = 232 * S
    th = int(lg.height * tw / lg.width)
    lg = lg.resize((tw, th))
    im.paste(lg, (54 * S, 66 * S), lg)
    dr = ImageDraw.Draw(im)

    # medailon se stuhou
    mcx, mcy = 168 * S, 360 * S
    GDARK = (150, 120, 55)

    def _tail(sgn, col):
        # pás stuhy vylézající zpoza medailonu, dole vlaštovčí zástřih
        return [
            (mcx + sgn * 40 * S, mcy + 96 * S),   # horní vnější (schová se za kroužek)
            (mcx + sgn * 6 * S, mcy + 100 * S),   # horní vnitřní
            (mcx + sgn * 13 * S, mcy + 182 * S),  # dolní vnitřní
            (mcx + sgn * 27 * S, mcy + 160 * S),  # zástřih (nahoru)
            (mcx + sgn * 47 * S, mcy + 182 * S),  # dolní vnější
        ]
    dr.polygon(_tail(-1, GDARK), fill=GDARK)   # levý pás (vzadu, tmavší)
    dr.polygon(_tail(1, GOLD), fill=GOLD)      # pravý pás (vpředu)

    # medailon (kroužky + rysky) přes horní konce stuhy
    dr.ellipse([mcx - 104 * S, mcy - 104 * S, mcx + 104 * S, mcy + 104 * S], outline=GOLD, width=max(1, S))
    dr.ellipse([mcx - 90 * S, mcy - 90 * S, mcx + 90 * S, mcy + 90 * S], outline=GOLDL, width=max(1, S // 2))
    for i in range(60):
        a = 2 * math.pi * i / 60
        dr.line([mcx + math.cos(a) * 91 * S, mcy + math.sin(a) * 91 * S,
                 mcx + math.cos(a) * 101 * S, mcy + math.sin(a) * 101 * S], fill=GOLD, width=max(1, S // 2))
    dr.text((mcx, mcy - 8 * S), str(let), font=G(92 * S, "SemiBold"), fill="white", anchor="mm")
    _spaced(dr, mcx, mcy + 50 * S, "LET", G(18 * S, "Medium"), GOLDL, 10 * S)
    _spaced(dr, mcx, 632 * S, "DĚKUJEME", G(13 * S, "Medium"), (150, 160, 195), 9 * S)

    # obsah
    cx = 666 * S
    _spaced(dr, cx, 168 * S, "CERTIFIKÁT", G(46 * S, "Light"), NAVY, 16 * S)
    dr.rectangle([cx - 48 * S, 204 * S, cx + 48 * S, 206 * S], fill=GOLD)
    _spaced(dr, cx, 284 * S, "ZA DLOUHOLETOU VĚRNOST A PŘÍNOS SPOLEČNOSTI", G(13 * S, "Medium"), GREY, 2 * S)

    nm = G(50 * S, "SemiBold")
    nw = dr.textlength(jmeno, font=nm)
    dr.text((cx, 372 * S), jmeno, font=nm, fill=NAVY, anchor="mm")
    for sgn in (-1, 1):
        dx = cx + sgn * (nw / 2 + 40 * S)
        dr.polygon([(dx, 366 * S), (dx + 7 * S, 373 * S), (dx, 380 * S), (dx - 7 * S, 373 * S)], fill=GOLD)
    dr.rectangle([cx - 150 * S, 408 * S, cx + 150 * S, int(409.5 * S)], fill=GOLD)

    # číslovka slovy (5–40 po pěti), jinak číslicí
    slovy = {5: "pět", 10: "deset", 15: "patnáct", 20: "dvacet", 25: "dvacet pět",
             30: "třicet", 35: "třicet pět", 40: "čtyřicet"}
    lw = slovy.get(let, str(let))
    # vřelé, přirozené znění (tykání) — genderově neutrální, jméno v 1. pádě zůstává
    l1 = f"Za {lw} let poctivé práce, věrnosti a přínosu naší firmě"
    l2 = "Ti ze srdce děkujeme a těšíme se na další společné roky."
    fb = G(14 * S, "Light")
    dr.text((cx, 450 * S), l1, font=fb, fill=GREY, anchor="mm")
    dr.text((cx, 473 * S), l2, font=fb, fill=GREY, anchor="mm")

    # podpis jednatele (vycentrovaný) + datum pod ním
    cxs = 666 * S
    sg = _sig_img(int(46 * S))
    im.paste(sg, (int(cxs - sg.width / 2), int(592 * S - sg.height)), sg)
    dr = ImageDraw.Draw(im)
    dr.rectangle([cxs - 95 * S, 596 * S, cxs + 95 * S, int(597.5 * S)], fill=(180, 188, 205))
    dr.text((cxs, 612 * S), "Marti Pašek, jednatel", font=G(12 * S, "Light"), fill=GREY, anchor="mm")
    dr.text((cxs, 636 * S), datum_misto, font=G(11 * S, "Light"), fill=LGREY, anchor="mm")

    # uložení
    base, ext = os.path.splitext(out)
    png_path = base + ".png"
    im.save(png_path)
    if ext.lower() == ".pdf":
        im.save(out, "PDF", resolution=float(3000 / (297 / 25.4)))  # ~256 DPI
        return out
    return png_path


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Generátor certifikátu k výročí (EUROSOFT, Galano).")
    ap.add_argument("jmeno")
    ap.add_argument("--datum", default="V Plzni dne 1. 9. 2026", help="datum a místo, celý řádek")
    ap.add_argument("--let", type=int, default=10, help="počet let (výchozí 10)")
    ap.add_argument("--pohlavi", default=None, help="m / z (jinak neutrální znění)")
    ap.add_argument("--out", required=True, help="cesta; .pdf = tiskové PDF, jinak PNG")
    ap.add_argument("--scale", type=int, default=3, help="rozlišení (3 = tisk)")
    a = ap.parse_args()
    print("Uloženo:", generuj(a.jmeno, a.datum, a.let, a.pohlavi, a.out, a.scale))
