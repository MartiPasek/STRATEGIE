# Vyhodnoceni zakazek: ulozeni kvality a poznamek u osoby (hotovo 5.8.2026)

> oblast: `vyroba` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Ulozeni rucne zadavanych poli u hodnoceni osoby

**Hotovo a overeno naostro 5. 8. 2026** (C28/Jirka). Bod 1 ze sestice doladeni.
Varianta A dle Jirky: vlastni cesta jen pro tento modul, **bez zasahu do spolecneho frameworku**.

## Proc to nesla konfigurace

`fw.data_source_op` **nezna operaci "uloz"** - ze vsech 234 zaznamu jsou jen `select` (155),
`edit` (38), `insert` (19), `delete` (13), `select-detail` (9). Oba gridy jadra maji jen
`select-detail`, takze hodnoceni kvality ani poznamky nebylo KAM zapsat.

## Reseni

`g2007.python` kod **`vyhodnoceni_osoba_uloz`** (min_pravo=clen), spousteni pres **uz existujici**
`POST /app/erp_registry/run` s `args:[osoba_id, {pole: hodnota}, "__uid__"]`.
**Zadny novy endpoint, zadny deploy, zadny zasah do frameworku.**

## Bily seznam - co se smi ulozit

`flexibilita`, `chybovost`, `estetika` (+ jejich poznamky) · `zkusebna_poznamka` ·
`poznamka_vv`, `poznamka_vp`, `poznamka_sefmonter` · `nepodepsany_zak_list`

**Co se ulozit NESMI:** cokoli, co pocita prepocet (hodiny, premie, srazky, sefmonter)
a **`efektivita_osoba`** - ta vstupuje do vypoctu PENEZ, proto ma zustat na samostatne,
vedome schvalene ceste, ne se svezt s poznamkami.

## Pojistky

1. **Zamcena historie** - odmitne s hlaskou, stejne jako ostatni zapisove funkce.
2. **Bily seznam** - cokoli mimo nej vrati chybu a NIC neulozi (ne tise preskoci).
3. **Radek se oznaci `zdroj='strategie'`** - jinak by ho pristi beh prenosu z Centraly prepsal.
4. **Audit** do `ec.akce_audit` ve stejne transakci (kdo, co, ktera pole).

## Overeno naostro (vsechny ctyri smery)

- ulozeni poznamky + hodnoceni na nezamcene VR10704 -> OK, 2 pole, radek oznacen jako nas
- zamcena VR8265 -> "Zakázka VR8265 je uzamčena (historie z Centrály) — uložit nelze."
- pocitane pole `premie_osoba_final` -> odmitnuto
- `efektivita_osoba` -> odmitnuto
Po zkousce uklizeno do puvodniho stavu.

## Nalez k hodnotici stupnici

`flexibilita`, `chybovost` i `estetika` maji ve **vsech 15 306 radcich hodnotu 1** - v Centrale
se fakticky nepouzivaji a stupnice neni nikde zdokumentovana. Skript proto hlida jen rozsah
0-255 (rozsah puvodniho typu tinyint). **Skutecnou stupnici potvrdit s Dusanem.**
Realne vyplnovane jsou poznamky - ma je 1 867 radku.

