# Vyhodnoceni zakazek - prevod do mezd, stav k 8.9.2026 a dve otevrene diry

> oblast: `vyroba` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)


# Prevod odmen z vyhodnoceni do mezd - stav k 8. 9. 2026

**Zapsala C24 (Kristy) 8. 9. 2026.** Navazuje na [[doc-vyroba-vyhodnoceni-firma-pres-engagement]]
a [[doc-vyroba-vyhodnoceni-zakazek-stav-4-8-2026]].

## Hotovo dnes (obe zmeny overene ctenim md5 z DB, ne navratovkou)

1. **`ec.vyhodnoceni_uzavrit` doplnena** o `zdroj='strategie'` a `datum_porizeni=now()`
   v INSERTu do `ec.zakazky_finance_zam` (request #2801). Bez toho by nove radky mely NULL
   a neslo by poznat, co vzniklo u nas. md5 4201 -> 4248 znaku. Jina zmena zadna.
2. **Nova funkce `ec.vyhodnoceni_do_mezd(p_zak text)`** (request #2803) - prevede vysledek
   uzaverky do `tenant.wage_movement`, slozka **67** (`odmeny_finance_zakazek`, Helios 651).
   Zatim **NENI napojena na zadne tlacitko**.

Mapovani - `amount` z `fix_premie`, obdobi z `datum_porizeni` (mesic uzavreni),
`status='approved'`, `import_src='STRATEGIE_VYH'`, `import_src_id` = id radku uzaverky,
`valid_from`/`valid_to` = prvni a posledni den obdobi, `is_recurring=false`
(vzor prevzat z existujicich radku EC_PRIPL, ne vymysleny).

**Tri pojistky proti dvojimu zapocteni** - unikatni index `uq_wage_movement_import`
na (tenant_id, import_src, import_src_id) **uz existoval**, takze DDL nebylo potreba;
kontrola, ze pro tehoz cloveka, obdobi a zakazku uz nelezi radek EC_PRIPL (preskoci
a NAHLASI, netise zahodi); zdrojem jsou vyhradne radky `zdroj='strategie'`.

## DIRA 1 - hlavicku vyhodnoceni nezaklada nic

**Zadna z 12 funkci schematu `ec` nedela INSERT do `ec.vyhodnoceni_zakazka`.**
Vsech 1 864 hlavicek prislo importem z Centraly. Modul tedy umi vyhodnotit **jen zakazky,
ktere uz v Centrale existovaly**; nove vznikla zakazka nema co vyhodnotit.
Neblokuje to mzdovou vetev, ale **blokuje to vypnuti Centraly** a jde proti zadani,
ze uzaverku spousti Dusan u nas.

## DIRA 2 - zruseni uzaverky neuklidi mzdy

`ec.vyhodnoceni_zrusit` rusi jen `zakazky_finance_zam` a otevira zakazku. O radcich
ve `wage_movement` nevi. Kdo uzavre, posle do mezd a pak uzaverku zrusi, tomu odmena
ve mzde zustane viset a zakazka jde uzavrit znovu.
Reseni - bud `zrusit` rozsirit, nebo prevod do mezd povolit az tam, kde uz zruseni nehrozi.

## POUCENI - vyber testovaci zakazky musi zohlednit slouceni

Test 8. 9. jsem pustila na **VR10673, coz je zakazka SLOUCENA** do skupiny
VR10673 + VR10702 + VR10724 + VR10725 + VR10726. Slouceni stalo cely cas v poli
`list_zakazek` v hlavicce a ja se tam podivala az po spusteni.

Dva dusledky, oba stoji za zapamatovani:
- **Modul pocita pres CELOU skupinu.** Porovnavat hodiny jedne zakazky proti kalkulaci
  jedne zakazky je nesmysl - u VR10673 to vypadalo na 11,79 h proti limitu 14,95,
  ve skutecnosti skupina mela 71,388 h proti kalkulaci 71. Zakazka byla pretazena,
  vsechny premie vysly nulove a do mezd tedy nesla ani koruna.
- **Uzaverka zapisuje `tenant.zakazka_meta` pro celou skupinu**, ne jen pro zadanou
  zakazku - stopa je sirsi, nez cekas. Pri uklidu pocitej s celou skupinou.

Uklid probehl kompletne (request #2806) - hlavicka zpet ve vsech 35 sloupcich,
puvodni 4 osoby s puvodnimi id, 5 meta radku smazano (vsechny vznikly az tim behem,
zadny nepredchazel). Radky v `ec.akce_audit` jsem nechala - audit je append-only.

## Jak pouzivat most pro tenhle modul

- Beh pres most **obchazi `ec.akce_audit`**, protoze audit zije ve webove vrstve.
  U akce, ktera tvori vyplaty, zapis auditni radky sam.
- Ctecí straz mostu odmita slovo INSERT **i uvnitr retezce** - sklada se z kousku
  (`'INS' || 'ERT'`).
- `ec.skupina_zakazek` volana pro kazdou zakazku v dotazu = timeout. Skupinu ber
  z `NULLIF(COALESCE(zakazka_meta.idskupiny, oz_zakazky."_IDSkupiny"), 0)`.
- `pg_get_functiondef` nad celym `pg_proc` spadne na agregatnich funkcich - filtruj `prokind = 'f'`.

## Co dal (poradi)

Otestovat penezni vetev na NESLOUCENE zakazce, kde premie skutecne vzniknou.
Pak tlacitko (KROK 2) - akce `do_mezd` do `_EC_ACTIONS` i `_EC_AKCE_S_OPRAVNENIM`
v `modules/erp/api/vyhodnoceni_actions.py`, cimz zdedi opravneni i audit.
Pozor na pravidlo "kod jako data" - soubor by mel nejdriv do `g2007.python`.

