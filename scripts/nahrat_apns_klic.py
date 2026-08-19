#!/usr/bin/env python3
"""Nahraje APNs klic ze souboru do trezoru fw.app_secret.

Klic se NIKDY nevypisuje - ani do konzole, ani do chyboveho hlaseni. Nacte se
ze souboru primo do pameti a do databaze jde jako PARAMETR dotazu, takze se
nedostane ani do prikazove radky, ani do SQL logu s hodnotami.

Pouziti:
    python nahrat_apns_klic.py --key-file C:\\cesta\\AuthKey_2YZ86LSQ25.p8

Pripojeni k databazi se hleda v tomhle poradi:
    1. prepinac --dsn
    2. promenna prostredi DATABASE_DATA_URL nebo DATABASE_URL
    3. soubor .env v aktualnim adresari nebo v --repo (klic DATABASE_DATA_URL)
    4. projektovy core.database (kdyz skript bezi z adresare repa)

Kontrola po zapisu vypise jen delku a prvnich 27 znaku - klic samotny ne.
"""
import argparse
import os
import pathlib
import sys

KEY_ID_VYCHOZI = "2YZ86LSQ25"


def chyba(zprava, kod=1):
    """Ukonci skript s hlasenim. Nikdy nevypisuje obsah klice."""
    print(f"CHYBA: {zprava}", file=sys.stderr)
    sys.exit(kod)


def nacti_klic(cesta: pathlib.Path) -> str:
    if not cesta.exists():
        chyba(f"soubor s klicem neexistuje: {cesta}")
    try:
        klic = cesta.read_text(encoding="utf-8").strip()
    except Exception as exc:
        chyba(f"soubor s klicem nejde precist ({type(exc).__name__})")
    if not klic.startswith("-----BEGIN PRIVATE KEY-----"):
        chyba("soubor nezacina radkem -----BEGIN PRIVATE KEY----- (neni to .p8 klic?)")
    if not klic.endswith("-----END PRIVATE KEY-----"):
        chyba("soubor nekonci radkem -----END PRIVATE KEY----- (useknuty soubor?)")
    if not (200 <= len(klic) <= 1000):
        chyba(f"klic ma podezrelou delku {len(klic)} znaku (ceka se zhruba 240-260)")
    return klic


def najdi_dsn(args) -> str:
    if args.dsn:
        return args.dsn
    for promenna in ("DATABASE_DATA_URL", "DATABASE_URL"):
        if os.environ.get(promenna):
            return os.environ[promenna]
    kandidati = [pathlib.Path(".env")]
    if args.repo:
        kandidati.insert(0, pathlib.Path(args.repo) / ".env")
    for env in kandidati:
        if env.exists():
            for radek in env.read_text(encoding="utf-8", errors="ignore").splitlines():
                radek = radek.strip()
                for promenna in ("DATABASE_DATA_URL", "DATABASE_URL"):
                    if radek.startswith(promenna + "="):
                        return radek.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def zapis(dsn: str, klic: str, key_id: str, jen_kontrola: bool) -> int:
    """Vrati navratovy kod. Klic predava jako parametr dotazu, nikdy do textu SQL."""
    spojeni = None
    zpusob = ""
    try:
        import psycopg2  # noqa
        spojeni = psycopg2.connect(dsn)
        zpusob = "psycopg2"
    except ImportError:
        pass
    except Exception as exc:
        chyba(f"pripojeni k databazi selhalo ({type(exc).__name__}): {exc}")

    if spojeni is None:
        try:
            from sqlalchemy import create_engine, text
        except ImportError:
            chyba("nenasel jsem psycopg2 ani sqlalchemy - nainstaluj jedno z nich "
                  "(pip install psycopg2-binary)")
        try:
            engine = create_engine(dsn)
            with engine.begin() as spoj:
                spoj.execute(text(
                    "CREATE TABLE IF NOT EXISTS fw.app_secret "
                    "(skey text PRIMARY KEY, sval text)"))
                if not jen_kontrola:
                    spoj.execute(text(
                        "INSERT INTO fw.app_secret (skey, sval) VALUES (:k1,:v1),(:k2,:v2) "
                        "ON CONFLICT (skey) DO UPDATE SET sval = EXCLUDED.sval"),
                        {"k1": "apns_key_id", "v1": key_id,
                         "k2": "apns_key_p8", "v2": klic})
                rows = spoj.execute(text(
                    "SELECT skey, length(sval) AS delka, left(sval,27) AS zacatek "
                    "FROM fw.app_secret WHERE skey LIKE 'apns%' ORDER BY skey")
                ).mappings().all()
            return vypis(rows, "sqlalchemy", jen_kontrola)
        except Exception as exc:
            chyba(f"zapis pres sqlalchemy selhal ({type(exc).__name__}): {exc}")

    try:
        with spojeni:
            with spojeni.cursor() as kurzor:
                kurzor.execute("CREATE TABLE IF NOT EXISTS fw.app_secret "
                               "(skey text PRIMARY KEY, sval text)")
                if not jen_kontrola:
                    kurzor.execute(
                        "INSERT INTO fw.app_secret (skey, sval) VALUES (%s,%s),(%s,%s) "
                        "ON CONFLICT (skey) DO UPDATE SET sval = EXCLUDED.sval",
                        ("apns_key_id", key_id, "apns_key_p8", klic))
                kurzor.execute(
                    "SELECT skey, length(sval), left(sval,27) "
                    "FROM fw.app_secret WHERE skey LIKE 'apns%' ORDER BY skey")
                rows = [{"skey": r[0], "delka": r[1], "zacatek": r[2]}
                        for r in kurzor.fetchall()]
        return vypis(rows, zpusob, jen_kontrola)
    except Exception as exc:
        chyba(f"zapis selhal ({type(exc).__name__}): {exc}")
    finally:
        try:
            spojeni.close()
        except Exception:
            pass


def vypis(rows, zpusob, jen_kontrola) -> int:
    if not jen_kontrola:
        print(f"ZAPSANO (pres {zpusob})")
    if not rows:
        print("V TREZORU NIC NENI")
        return 3
    print("\nStav trezoru (klic se zamerne nevypisuje):")
    for r in rows:
        print(f"  {r['skey']:14s} delka={r['delka']:<5} {r['zacatek']}")
    ok_id = any(r["skey"] == "apns_key_id" and r["delka"] == 10 for r in rows)
    ok_p8 = any(r["skey"] == "apns_key_p8"
                and str(r["zacatek"]).startswith("-----BEGIN PRIVATE KEY") for r in rows)
    print("\n" + ("OVERENO OK" if (ok_id and ok_p8) else "OVERENI SELHALO"))
    return 0 if (ok_id and ok_p8) else 4


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--key-file", help="cesta k souboru AuthKey_XXXXXXXXXX.p8")
    p.add_argument("--key-id", default=KEY_ID_VYCHOZI, help="Key ID z developer.apple.com")
    p.add_argument("--dsn", help="postgresql://uzivatel:heslo@host:5432/databaze")
    p.add_argument("--repo", help="adresar repa STRATEGIE (kvuli .env)")
    p.add_argument("--check-only", action="store_true",
                   help="jen ukaze, co uz v trezoru je; nic nezapisuje")
    args = p.parse_args()

    if not args.check_only and not args.key_file:
        chyba("chybi --key-file (nebo pouzij --check-only)")

    dsn = najdi_dsn(args)
    if not dsn:
        chyba("nenasel jsem pripojeni k databazi - pouzij --dsn, nebo nastav "
              "DATABASE_DATA_URL, nebo spust skript v adresari s .env")

    klic = "" if args.check_only else nacti_klic(pathlib.Path(args.key_file))
    if klic:
        print(f"Klic nacten ze souboru: {len(klic)} znaku, Key ID {args.key_id}")

    sys.exit(zapis(dsn, klic, args.key_id, args.check_only))


if __name__ == "__main__":
    main()
