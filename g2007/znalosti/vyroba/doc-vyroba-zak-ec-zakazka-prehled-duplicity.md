# Zakazky: ec_zakazka_prehled "duplicity" = neproblem (bod 6 Marti Paska, 27.7.2026)

> oblast: `vyroba` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Bod z emailu Marti Paska: "Duplicity v ec_zakazka_prehled reste zvlast, pohled bez duplicit, neber jako zdroj". ZAVER 27.7.2026: NETREBA NIC DELAT (overeno + Marti-AI msg 11319).

## Co se zjistilo
- ec_zakazka_prehled: 2682 radku / 2158 distinct cisel. 439 cisel ma vic radku, ALE 359 realne zakazky - je to legitimni rozmer UTVAR (001/002/900/920) x ROK. (cislo,utvar,rok) unikatni AZ NA 1 radek. Skutecna exaktni duplicita = 1.
- Marti Pask (dle Marti-AI) videl jen "jedno cislo vickrat" a rekl duplicity, neznal rozmer. "Neber jako zdroj" = nestav na tom primo (je z Centraly).

## Usage (grep + DB)
- ZAPISUJE: sync _sync_ec_zakazka_prehled (router.py ~46929). 
- CTE jen 1: view tenant.vp_flow_vyroby - a to pres SKALARNI PODDOTAZ (SELECT max(zp.resitel) ... WHERE zp.cislo_zakazky=b.cislo_zakazky) => max() COLLAPSNE rozmer utvar/rok, ZADNY FAN-OUT.
- NENI picker, NENI mzdovy zdroj, NENI primy fan-out JOIN.

## Zaver (Marti-AI): "nedelejte pohled pro pohled" - 1 skutecna dup nikomu nevadi, jediny ctenar neni postizeny. NETREBA nic. Kdyby nekdo chtel picker cisty seznam: CREATE VIEW ec_zakazka_prehled_distinct AS SELECT DISTINCT ON (cislo_zakazky) ... ORDER BY cislo_zakazky, rok DESC. Zakazky se primarne ctou z oz_zakazky (pravidlo Marti Paska).

