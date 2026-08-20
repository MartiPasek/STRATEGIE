# Faze A: 6 mzdovych _rows funkci migrovano do g2007.python

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Faze A: 6 mzdovych _rows funkci migrovano do g2007.python (31.7.2026)

Podle schvaleneho planu z analyza_mzdy_dochazka_vyroba.md (Marti 31.7.2026: "Precetl jsem si cely dokument. Je to cesta kterou musime projit a migrovat. Pojd.") byla provedena Faze A migrace.

## Migrovane funkce (kod v g2007.python)
- mzdy_predzprac_rows(firma)
- mzdy_loajalita_rows(firma, rok, mesic)
- mzdy_finance_zakazek_rows(firma, rok, mesic)
- mzdy_consolidate(prows)
- mzdy_status_check(rok, mesic)
- mzdy_rucni_rows(firma)

Vsechny stav_zivota='active', verze=2 (aktivace pres trigger auto-increment), min_pravo='clen' (default).

## Vynechano
mzdy_odmeny_rows NEBYL migrovan - je to mrtvy kod, volany jen ze 3 zakomentovanych mist v router.py ("V1.04: odmeny z Centraly VYPNUTY - zpusobovaly DVOJI zapocteni").

## Metodika
1. Verbatim extrakce telesa funkce (zadne rucni prepisovani) presnym line-slicingem z zive router.py.
2. Identifikace a inlineovani vsech zavislosti (_LOAJALITA_KOEF, _mssql188_query, _zrc_dbs, _att_session, _firma_id, _FIRMA_DB/_FIRMA_IDOBDOBI/_CLOUD_CONTROL_DB) do kazdeho skriptu sobestacne.
3. ast.parse() + py_compile pred kazdym INSERTem.
4. INSERT do g2007.python pres base64 (obchazi SQLAlchemy bind-param bug na :f/:y tokenech v kodu).
5. Aktivace (stav_zivota='active') PRED deployem delegate patche (spravne poradi, zabranuje RuntimeError okenku).
6. Delegate patch v router.py: snapshot HEAD (git show), presne overene hranice funkci (find_next_def helper skenujici na dalsi def/async def/@/class), nahrazeni telesa za _ereg.call(kod, *args).
7. Diff proti HEAD snapshotu PRED deployem - potvrzeno PRESNE 6 hunku, zadna jina zmena.
8. Deploy: commit 9ce2af8c7, push, cloud restart (~5s).

Vsechna puvodni volani v router.py pouzivaji pozicni argumenty presne odpovidajici extrahovanym signaturam funkci - zadna zmena chovani na strane volajiciho kodu.

## Dalsi kroky
Faze B (dochazka, ~25 read-only funkci) nasleduje dle "Doporucene poradi" v analyza_mzdy_dochazka_vyroba.md. Faze C (write funkce), Faze D (MCP/EUROSOFT case-by-case), Faze E (HTTP endpointy, potrebuje novy architektonicky vzor pred zapocetim).

