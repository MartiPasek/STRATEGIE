# Úvazek k datu bere nejnovější verzi smlouvy, ne nejvyšší z historie (23. 8. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


Zapsal Claude-28 na rozhodnutí Jirky Honomichla, schválila Marti-AI (msg 13417).
Vše níže ověřeno čtením živého kódu a dat 23. 8. 2026, ne převzato.

## Co se změnilo

`att_uvazek_tyden` (g2007.python) má dvě větve — „jaký má úvazek teď" (`is_current`)
a „jaký měl k datu" (parametr `k_datu`). Druhá větev vybírala verzi smlouvy přes
`ORDER BY uvazek_tyden_h DESC LIMIT 1`, tedy **nejvyšší úvazek ze všech verzí**
s `valid_from <= datum`. Nově se u **každého poměru zvlášť** (`DISTINCT ON
(employee_id, company_id)`, `ORDER BY valid_from DESC, id DESC`) vezme **nejnovější
verze platná k tomu dni** a teprve mezi poměry se bere maximum. Záměr „člověk může mít
dva souběžné poměry" zůstává. Verze 3 → 4, archiv v `g2007.python_historie` (otisk
staré verze `351c72fe0f935e9c7a407a384f59d26c`).

## Proč to bylo špatně

`tenant.engagement.valid_to` je prázdné u všech 939 řádků (v Centrále takový sloupec
nikdy neexistoval — `EC_FinZamPodminky` má jen `PlatnostOd` a příznak `Aktualni`).
Nahrazené verze proto nikdy „nedoběhnou" a při řazení podle velikosti úvazku vyhrála
stará vyšší hodnota. Odpověď k 1. 8. 2026 vycházela u 7 lidí vyšší, než tehdy platilo:
Bernardová 40/32, Brudnová 40/35, Dvořáková 35/30, Novotná 40/35, Šik 40/30,
Veverková 40/20, Duspivová 40/35.

**Příčina byla v řazení, ne v prázdném `valid_to`.** Ostatních sedm míst, která
engagement čtou k datu (`att_anomaly_scan`, `att_dovolena_kaskada`, `att_narok_cerpani`,
`att_sd_kontrola`, `mzdy_benefity_apply`, `mzdy_loajalita_rows` a náhrady v `router.py`
ř. 33646), řadí `ORDER BY valid_from DESC LIMIT 1` a správně fungují i s prázdným
`valid_to`.

## Proč se nikomu nic nezměnilo

- **Větev `k_datu` dnes nikdo nevolá** — 0 výskytů v aktivních skriptech `g2007.python`
  i v celém repu; všech 10 volajících míst se ptá bez data.
- **Větev bez data je beze změny, byte za bytem** — oba vzorce dají stejné číslo
  u všech 75 lidí s účtem (0 rozdílů; nikdo nemá víc platných verzí u jednoho poměru).
- Do mzdových podkladů ani do historie se nesahalo. Peťa proto podle Marti-AI nemusela
  být u toho.

## Jak to bylo ověřeno

Nový dotaz spuštěn naživo před zápisem (vrací 32/35/30/35/30/20/35 tam, kde starý
vrací 40/40/35/40/40/40/40; Marti Pašek zůstává 40 — má dva souběžné poměry po 40 h).
Po zápisu ověřeno čtením z DB: otisk `97c49b8122928ed241de26c11939f13c`, 4 993 znaků,
`verze=4`, `stav_zivota=active`. Živý test na produkci přes
`/api/v1/erp/app/plan/my-uvazek`: Jirka 40 h (8 h/den), Veverková 20 h (4 h/den) —
oboje správně, endpoint nespadl. `erp_registry` si funkci tahá podle dvojice
(kód, verze), takže povýšení verze stačí a restart API není potřeba.

## Otevřené (rozhoduje Jirka, u mezd s Peťou)

Co se sloupcem `valid_to` dál — nechat prázdný · vyplňovat jen nové změny ·
doplnit i historii (858 nahrazených verzí, sahá na podklady už spočítaných mezd).
K 23. 8. 2026 rozhodnuto **nic neměnit**. Pozor: ukončení poměru (`router.py`
ř. 10096 a 11841) `valid_to` zapisuje a `is_current` přitom nemění — dnes ho ale
nemá vyplněné ani jeden ze 338 ukončených řádků (159 lidí).

Souvisí: `doc-system-strategie-smlouvy-verzovani-uvazku-a-platnost-do`,
`doc-dochazka-podminky-slouceny-se-smlouvou`.

