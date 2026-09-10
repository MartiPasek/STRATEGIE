# Nárok a čerpání: necelá čísla u sick days, dva součtové sloupce a roztahovatelné sloupce (Peťa 9. 9. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)

**Peťa + Claude‑26, 9. 9. 2026.** Peťa: *„my jsme tam dělali přepočet na hodiny, protože se to smí čerpat po hodině, ale teď nám tam visí takový jako celý něco, a to je špatně."*

Navazuje na `doc-dochazka-sick-days-narok-ve-dnech-cerpani-v-hodinach` (1. 9. 2026).

## 1. Necelá čísla u sick days — zaokrouhlený mezivýsledek

Dušan Havlát měl v přehledu **SD nárok 16,04 h** a **zbývá 11,04 h**, i když má rovné 2 dny nároku při osmihodinovém fondu.

Příčina — dny se zaokrouhlily na dvě desetiny a **teprve z nich se počítaly hodiny**, takže se chyba dotáhla až do nároku:

- 5 h čerpání při 8h fondu = **0,625 dne**, uloženo jako 0,62
- zbytek 2 − 0,62 = **1,38** dne (správně 1,375)
- hodiny zbytku 1,38 × 8 = **11,04** (správně 11,00)
- nárok = 5 + 11,04 = **16,04** místo 16

**Oprava (`att_narok_cerpani`):** počítá se z nezaokrouhlených dnů (`_sd_cerp_dny`, `_sd_plan_dny`, `_sd_zbyva_dny`), zaokrouhluje se **až pro zobrazení**. Týká se i `sd_po_h` a `sd_po_dny`.

Ověřeno naostro — Havlát 16 h / 11 h, a v celém přehledu (79 lidí) nezůstala ani jedna neceločíselná hodnota, kde být nemá.

## 2. Dva součtové sloupce (jako to měla Centrála)

Peťa chtěla sloupec, kde je sečtené všechno ještě nevybrané volno. Nakonec jsou dva, oba ve DNECH a oba sčítají D + DN + SD:

| Sloupec | Co je v něm |
|---|---|
| **vše vč. naplán. (dny)** | všechno nevybrané volno — naplánované dny se POČÍTAJÍ, protože naplánováno ještě neznamená vybráno |
| **vše bez naplán. (dny)** | totéž po odečtení naplánovaných dnů, tedy co má člověk volně k dispozici |

Příklad Artim Josef — D 11 (celá naplánovaná), DN 5 (z toho 3 naplánované), SD 2 → **18 celkem, 4 po plánu**.

## 3. Jméno zopakované vpravo

Peťa: *„když zajedu na SD, už nevím, komu který řádek patří."* Poslední sloupec je proto znovu **Příjmení Jméno**.

## 4. Roztahovatelné sloupce (chyběly úplně)

Přehled jako jediný neuměl tažení za pravý okraj hlavičky. Doplněno do `apps/api/static/dochazka-narok.html` — soubor **žije v gitu, ne v `g2007.soubor`**, takže se mění deployem:

- úchyt `.colgrip` v každé hlavičce, kurzor `ew-resize`, tažení mění šířku v `colgroup`,
- **dvojklik na úchyt** = zpět na výchozí šířku,
- šířky si drží prohlížeč (`localStorage`, klíč `narok_colw`) — sdílené výchozí šířky pro všechny se dají povýšit stejným postupem jako u docházky (`tenant.att_ui_pref`), zatím se to neudělalo,
- klik na úchyt neřadí (`stopPropagation`).

## Kontrola celého přehledu (9. 9. 2026)

Projeto všech 79 řádků — nárok = čerpáno + zbývá, zbývá dny × fond = zbývá h, D i DN sedí. Jediný skutečný nález mimo výpočet- **Hladíková Michaela má sick days přečerpané o 0,5 dne (−4 h)**, nárok 12 dní proti vyčerpaným 12,5 dne.

