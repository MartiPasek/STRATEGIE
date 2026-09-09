# Číslo činnosti vyplňovala jen Správa docházky — ostatní cesty ho nechávaly prázdné a mzdy pak rozhodovaly podle náhradního seznamu v kódu

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)


## Pravidlo (Peťa, 7. 9. 2026)

> „Každá činnost má číslo a musí ho mít i u nás a nemůže se nám odněkud dostat činnost
> bez čísla."

## Co se stalo

Josef Artim (ES 498) měl v srpnu 2026 pět dnů činnosti **34 — Ostatní/Nepřítomen
s náhradou mzdy**. Ta stravenku vylučuje. Přesto jich dostal **21 místo 16** (o 410 Kč víc).

Vylučování ze stravenek rozhoduje podle **čísla činnosti** (att_entry.ec_druh), a když
číslo chybí, podle **náhradního seznamu typů** v kódu mzdy_stravenky_rows. Artimovy
záznamy číslo neměly a typ ostatni_nahrada v tom seznamu chyběl → propadlo to.

**Nenašlo to nic — našla to Peťa ručně při kontrole srpnových mezd.**

## Skutečná příčina

Číslo činnosti vyplňovala **jen jedna cesta zápisu**. Stav před opravou (7–8/2026):

| kudy záznam vznikl | s číslem | bez čísla |
|---|---|---|
| manual (Správa docházky) | 144 | 0 |
| absence (žádost v aplikaci) | 118 | 60 |
| manual_fix (oprava docházky) | 47 | 66 |
| plan_ec (plán z Centrály) | 23 | 33 |
| mobile_app | 1 | 11 |

Číselník přitom byl v pořádku a kompletní — tenant.vyroba_cinnost, kind='nepritomnost',
28 činností včetně všech absencí. **Problém byl v párování: kódy se nejmenují stejně.**

| typ docházky | činnost v číselníku | číslo |
|---|---|---|
| vacation | dovolena | 20 |
| medical | lekar | 21 |
| sick | nemoc | 22 |
| family_care | ocr | 23 |
| ostatni_nahrada | ostatni_nepritomen_s_nahradou_mzdy | 34 |
| maternity | materska_dovolena | 36 |
| osvc_absence | nepritomnost_osvc | 37 |
| unpaid | neplacene_volno | 39 |
| plac_volno_70/80/90 | volno_70/80/90 | 47/50/51 |
| sickday | sickday | 31 |
| nahradni_volno | nahradni_volno | 133 |

Spárovaly se samy **jen ty dvě, které se náhodou jmenují stejně** (sickday, nahradni_volno).

## Jak je to opravené (7. 9. 2026)

1. **tenant.att_entry_type.ec_cislo** — nový sloupec, jedno místo pravdy. Naplněný pro
   všech 13 typů nepřítomnosti.
2. **Trigger trg_att_entry_cislo_cinnosti** nad tenant.att_entry (BEFORE INSERT OR
   UPDATE OF entry_type_id, ec_druh) — když číslo chybí, doplní ho podle typu.
   **Záměrně v databázi, ne v každém místě zápisu**: na nové cestě by se na to zase
   zapomnělo, přesně tak vznikl Artim.
3. **Historie dopočítána** — 3 231 záznamů za celý rok 2026, zbývá 0.
4. **att_cinnost_bez_cisla** (g2007.python) — pojistka, hlásí záznamy bez čísla i typy
   bez čísla v číselníku. Nic nemění. ⚠ **Zatím NENÍ zaregistrovaná jako job** — zbývá
   doplnit do fnmap v _mirror_run_job a založit řádek v fw.mirror_job
   (pořadí: nejdřív deploy kódu, pak job).
5. Do _BEZ_STRAVENKY_TYPY v mzdy_stravenky_rows doplněno ostatni_nahrada
   a nahradni_volno — jako záchranná síť, ale po opravě výše už by neměla být potřeba.

## Pravidlo do budoucna

**Když se přidává číslo činnosti do seznamu vyloučených, vždy zkontroluj, jestli k němu
patří i typ** — a hlavně, jestli ten typ má vyplněné ec_cislo. Jinak se pravidlo
uplatní jen na část záznamů a zbytek tiše propadne.

## Co je záměrně BEZ vyloučení

- sickday (31) — sick day je přítomnost, **stravenka náleží** (Peťa 5. 8. 2026)
- osvc_absence (37) — OSVČ stravenky nedostávají vůbec (do mezd jdou jen HPP a DPP)
- činnost **30 dovolená navíc** — stravenka náleží (Peťa 5. 8. 2026)

