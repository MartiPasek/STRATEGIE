# -*- coding: utf-8 -*-
"""RB Gemini platák render (převzato 1:1 z EC_Banka_RB_Gemini_Tuz / _Zahr).
Byte-exact, CP1250, CR+LF. Verifikace proti reálným .p11/.f84.
Marti 6.7.2026."""


def _r(fill, val, width):
    """RIGHT(fill+val, width) — číselné pole, doplněné VLEVO (fill = nuly)."""
    return (fill + str(val))[-width:]


def _l(val, width):
    """LEFT(val+mezery, width) — textové pole, doplněné VPRAVO mezerami, ořez na width."""
    return (str(val) + " " * width)[:width]


def _ucet(cislouctu):
    """Rozdělí 'předčíslí-číslo' → (předčíslí 6, číslo 10). Bez '-' → předčíslí 000000."""
    s = str(cislouctu or "")
    if "-" in s:
        pre, cis = s.split("-", 1)
        return _r("0000000000", pre, 6), _r("0000000000", cis, 10)
    return "000000", _r("0000000000", s, 10)


def render_tuz_line(porad, datum_vytv, castka, ks, vs, ss, kod_ustavu_prij,
                    ucet_prij, ucet_klient, datum_splat, ucel):
    """Jeden řádek TUZ (.p11) dle EC_Banka_RB_Gemini_Tuz. datum_* = 'YYMMDD'."""
    hal = int(round(float(castka) * 100))          # částka v haléřích (int)
    pre_prij, cis_prij = _ucet(ucet_prij)
    ucel = ucel or ""
    parts = [
        _r("000000", porad, 6),                    # 1 číslo řádky
        "11",                                      # 2 druh CNB
        datum_vytv,                                # 3 datum vytvoření YYMMDD
        "5500",                                    # 4 naše banka
        "   ",                                     # 5
        _l(kod_ustavu_prij, 4),                    # 6 kód banky příjemce (KodUstavu)
        "   ",                                     # 7
        _r("00000000000000", hal, 15),             # 8 částka*100
        datum_splat,                               # 9 splatnost YYMMDD
        _r("0000000000", ks or "", 10),            # 10 KS
        _r("0000000000", vs or "", 10),            # 11 VS
        _r("0000000000", ss or "", 10),            # 12 SS
        "000000",                                  # 13 předčíslí náš
        _r("000000000", ucet_klient, 10),          # 14 náš účet
        pre_prij,                                  # 15 předčíslí příjemce
        cis_prij,                                  # 16 účet příjemce
        _l(ucel, 140),                             # 17 avizo kreditní (padded)
        " " * 20,                                  # 18 název účtu plátce
        " " * 20,                                  # 19 název účtu příjemce
        _r("000000000000", vs or "", 10),          # 20 VS debetní
        "0000000000",                              # 21 SS debetní
        ucel[:140],                                # 22 avizo debetní (bez paddingu)
    ]
    return "".join(parts)


def render_zahr_line(porad, datum_vytv8, castka, mena, up_nazev, up_ulice, up_misto,
                     zup_nazev, op_firma, op_ulice, op_misto, zop_nazev, nas_ucet, iban,
                     poplatky, tit, cil_zeme, hlav_id, p1, p2, p3, p4, priorita, nas_mena,
                     swift, datum_splat):
    """Jeden řádek ZAHR (.f84) dle EC_Banka_RB_Gemini_Zahr. datum_vytv8='YYYYMMDD', datum_splat='YYMMDD'."""
    castka_s = "%.2f" % float(castka)               # numeric(19,2) → s desetinnou tečkou
    parts = [
        "INT",                                       # 1
        _r("000000", porad, 6),                      # 2 číslo řádky
        datum_vytv8,                                 # 3 datum vytvoření YYYYMMDD
        _l(up_nazev, 35),                            # 4 název banky příjemce
        _l(up_ulice, 35),                            # 5 ulice banky
        _l(up_misto, 35),                            # 6 město banky
        _l(zup_nazev, 35),                           # 7 stát banky
        _l(op_firma, 35),                            # 8 název příjemce
        _l(op_ulice, 35),                            # 9 ulice příjemce
        _l(op_misto, 35),                            # 10 město příjemce
        _l(zop_nazev, 35),                           # 11 stát příjemce
        _r("00000000000000", castka_s, 16),          # 12 částka s tečkou
        (mena or ""),                                # 13 měna
        _r("000000000", nas_ucet, 10),               # 14 náš účet
        _l(iban, 34),                                # 15 IBAN
        _l((poplatky or "") + "   ", 3),             # 16 poplatky (BEN/OUR/SHA)
        _r("000", tit or "", 3),                     # 17 platební titul
        _l((cil_zeme or "") + "  ", 2),              # 18 ISO země příjemce
        "ID:" + _r("00000", hlav_id, 6) + ":",       # 19 ID hlavičky
        _l(p1, 35),                                  # 20 popis 1
        _l(p2, 35),                                  # 21 popis 2
        _l(p3, 35),                                  # 22 popis 3
        _l(p4, 25),                                  # 23 popis 4
        " " * 20,                                    # 24 název účtu příkazce
        ("01" if int(priorita or 0) == 0 else "02"), # 25 priorita
        _l((nas_mena or "") + "   ", 3),             # 26 měna účtu klienta
        _r("0000000000", hlav_id, 10),               # 27 VS klienta = ID
        "02",                                        # 28 formát účtu (IBAN)
        "02",                                        # 29 účtování (Europlatba)
        " " * 123,                                   # 30 rezerva
        _l(swift, 11),                               # 31 SWIFT příjemce
        "000000",                                    # 32 předčíslí účtu klienta
        datum_splat,                                 # 33 datum splatnosti YYMMDD
    ]
    return "".join(parts)


if __name__ == "__main__":
    import sys, glob, os
    # --- VERIFIKACE: platák 8090 == soubor PAY_TUZ_02-07-2026_6-12-59.p11 ---
    line = render_tuz_line(
        porad=1, datum_vytv="260702", castka=27138.00,
        ks="0308", vs="26006", ss="", kod_ustavu_prij="5500",
        ucet_prij="1513126033", ucet_klient="9251651001",
        datum_splat="260702", ucel="500001545 Pavel Voříšek")
    gen = line.encode("cp1250") + b"\r\n"

    up = "/sessions/lucid-kind-knuth/mnt/uploads"
    real_path = glob.glob(os.path.join(up, "*PAY_TUZ_02-07-2026_6-12-59.p11"))[0]
    with open(real_path, "rb") as f:
        real = f.read()

    print("GEN len :", len(gen))
    print("REAL len:", len(real))
    print("MATCH   :", gen == real)
    if gen != real:
        # najdi první rozdíl
        for i, (a, b) in enumerate(zip(gen, real)):
            if a != b:
                print("prvni rozdil na bytu", i)
                print("  GEN :", repr(gen[max(0,i-15):i+15]))
                print("  REAL:", repr(real[max(0,i-15):i+15]))
                break
        else:
            print("delkovy rozdil, kratsi je prefix delsiho")
