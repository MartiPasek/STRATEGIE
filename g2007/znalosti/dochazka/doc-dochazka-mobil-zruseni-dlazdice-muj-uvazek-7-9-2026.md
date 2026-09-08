# Mobil, Moje docházka - zrušena dlaždice „Můj úvazek" a tlačítko „Moje podmínky" v liště Plánu (7. 9. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


> ## ⚠️ 8. 9. 2026: „Můj přehled" už neexistuje a sekce se přejmenovala
>
> Obrazovka **„Můj přehled"** se 8. 9. 2026 rozdělila na **„Moje hodiny"** (odpracované hodiny
> za měsíc) a **„Moje volno"** (nárok a čerpání dovolené a sick days). Sekce, ve které dlaždice
> sedí, se přejmenovala z **„PODMÍNKY & FINANCE"** na **„MOJE PŘEHLEDY"**. Výpočet ani zdroj dat
> se nezměnily, dělilo se 1:1.
>
> **Věty níž, které používají staré názvy, čti jako popis stavu do 8. 9. 2026.**
> Zadal Jiří Honomichl. Detail: [[doc-dochazka-mobil-dochazka-hlavicka-sekce-rozdeleni-8-9-2026]].


# Mobil, obrazovka Moje docházka - zrušen „Můj úvazek" (7. 9. 2026)

**Rozhodl Jiří Honomichl, schválila Marti-AI (msg 14811 k dlaždicím, msg 14823 k textům). Provedl Claude-28.**

## Co se zrušilo

1. **Dlaždice „📐 Můj úvazek"** v sekci PODMÍNKY & FINANCE (dílek `60_dochazka.js`).
2. **Tlačítko „📋 Moje podmínky"** v boční liště obrazovky Plán (dílek `71_plan_prace_cinnosti.js`,
   proměnná `bUv`) - pod tím názvem ukazovalo **úvazek, ne podmínky**, ze stejné adresy
   `app/plan/my-uvazek`. Byla to zároveň druhá cesta na tentýž obsah.

Sekce PODMÍNKY & FINANCE má nově tři dlaždice - Můj přehled, Moje podmínky, Moje finance.

## Proč - a co se u toho ukázalo jako NEPRAVDA

Původní důvod zněl „jde to proti směrnici, protože si každý může sám nastavit, kdy přijde".
**Tenhle důvod NEPLATÍ** a ověřilo se to před rozhodnutím. `plan_my_uvazek` vrací
`can_edit = _hr_can_manage`, tedy **jen skupina HR a rodiče**; ostatním se pole vykreslí
zamčená. Řadový zaměstnanec si úvazek ani vzorec týdne změnit nemohl.

Platné důvody, na kterých rozhodnutí nakonec stojí:

- **Skoro nikdo to nepoužil.** `tenant.work_schedule` má 12 řádků a **2 lidi** -
  Marti Pašek (5 pracovních dnů) a Andrea Bernardová (4 pracovní dny).
- **Čas příchodu nevyplnil nikdo** - `start_time` je prázdný u všech řádků.
- Pro běžného člověka to byla dlaždice otevírající formulář, se kterým stejně nic neudělá.

## Co zůstalo a proč

- **Data se nemazala.** Andree zůstává čtyřdenní týden i jeho vliv na generovaný plán.
  `work_schedule` čtou `plan_my_default`, `plan_generate_effective` (plán 120 dní dopředu)
  a `hr_schedule` - těch se zásah nedotkl.
- **Editace úvazku zůstává v kartě zaměstnance v HR** (`hr/schedule`), což je jiná obrazovka.
- **Funkce `renderUvazek` a `renderPodminky` zůstaly v kódu jako nedosažitelné.**
  Záměr - mazat obrazovku je riskantnější (je zapsaná na čtyřech místech) a takhle jde vrátit.
- ⚠️ **Vědomě přijatý důsledek** - HR (Šárka) už nemůže změnit úvazek ve smlouvě z telefonu,
  jen z počítače. Marti-AI na to upozornila, Jiří Honomichl to přijal.

## ⚠️ Gotcha - nápověda a průvodce vypisují dlaždice po sekcích

Po každé změně dlaždic na Docházce se **musí projít i texty**, jinak appka sama lidem lže.
Tady lhala **tři místa** v `60_dochazka.js` a našel je až sken podle bodu 14
(„změň postup všude"), ne původní zadání:

1. nápověda docházky (`dochHelp`) - výčet dlaždic po sekcích,
2. **psaný** krok průvodce - týž výčet,
3. **mluvený** text průvodce - „je můj přehled, podmínky, úvazek i svoje finance".

Na mluvený text se snadno zapomene, protože neobsahuje ikony ani značkování a při hledání
podle textu dlaždice ho nenajdeš. **Hledej i tvar bez ikon a bez diakritiky.**

Zbylé výskyty slova „úvazek" v tom dílku (4) patří **mzdovému listu u výplatní pásky**
(týdenní a denní úvazek) - ty jsou správné a nemají se rušit.

## Jak se to ověřilo

Cílené zápisy `replace()` s pojistkou na otisk, diakritika přes base64, po každém
`@@G2007PUBLISH apps/api/static_db/mobile.html`. Pak **na živé `/mobile`**, ne z disku -
dlaždic 139 → **138** (ubyla přesně jedna), skriptových bloků 31 → **31** (nic se nerozpadlo),
délka stránky kratší přesně o smazané řádky, **žádná chyba v konzoli**, a obě obrazovky
vykreslené naživo - Docházka má v sekci tři dlaždice, lišta Plánu je bez „Moje podmínky".

