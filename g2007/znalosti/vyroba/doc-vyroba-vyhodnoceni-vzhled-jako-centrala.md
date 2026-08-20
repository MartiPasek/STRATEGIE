# Vyhodnocení zakázek — vzhled podle Centrály (záložky, barvy, Hodiny zakázek)

> oblast: `vyroba` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

**C28 (Jirka), 6. 8. 2026.** Zadání Jirky: *„ať se to co nejvíc podobá Centrále"* (podle 5 screenshotů z Centrály). Uživatel modulu = **Dušan Havlát** (user 41, os. č. 105).

## Hotovo

| co | kde |
|---|---|
| Záložky nahoře **Souhrn / Pomocné výpočty** | `fw.comp_def` 1325 (pagecontrol), 1326, 1327 |
| **Barvy** — Prémie zeleně, Srážka červeně | sdílená sestava `fw.comp_grid` **id 55**, klíč `ds_195`, pravidlo „není prázdné", rozsah buňka |
| Záložka **Hodiny zakázek** | comp_def 1328–1332 + `fw.data_set`/`fw.data_source` kód `ec.vyhodnoceni_jadro_hodiny` |

Struktura jádra **203** (pořadí jako Centrála): pagecontrol 1325 nahoře (Souhrn 1326, Pomocné 1327) · pagecontrol 1328 uprostřed (Hodnocení vše 1329 → gb 1275 → grid 1276; Hodiny zakázek 1330 → gb 1331 → grid 1332) · groupbox 1277 dole (Finální, grid 1278).

**Ověřeno v prohlížeči:** detail se vejde celý, **0 px rolování** (před záložkami 246 px).
**Ověřeno na datech (VR10704):** hlavička `odpracováno` = záložka Hodiny zakázek = tabulka lidí = **7,552 h**.

Zdroj hodin nové záložky = **naše** `tenant.vyroba_work` (pravidlo Jirka 5. 8.: *„vyhodnocování zakázek musí probíhat z našich tabulek strategie"*).

## Zbývá — a proč

Tři záložky z Centrály nejdou udělat bez přenosu dat, protože u nás ta data **vůbec nejsou**:
**Neevidované hodiny** (`EC_Dochazka_Neevidovana`) · **Více hodiny** (`EC_ZakazkyHodNavic`) · **Vysvětlení** (`EC_ZakazkyZisk_Vysvetleni`). Dohoda s Jirkou 6. 8.: **počkat na Dušanovy připomínky**, teprve pak se rozhodnout.

Tlačítka mezi tabulky (jako v Centrále) = kosmetika; **doporučeno nechat je v horní sticky liště**, kde jsou vidět vždycky.

## ⛔ Červená u sloupce Efektivita — slepá ulička, NEDĚLAT

V Centrále je `EfektivitaOsoba` červená jen u některých řádků, i když všude stojí 100. **Vzor rozluštěn** (VR10627, 8 z 8 bez výjimky): červené řádky mají `EfPrumer` **pod 100** (90, 93, 91, 99), bílé rovných 100. Jirka to potvrdil.

**Jenže sloupec `EfPrumer` v databázi Centrály neexistuje** — prohledáno `INFORMATION_SCHEMA.COLUMNS` vzory `%EfPrum%` i `%Prumer%`, není ani v `EC_TempVyhodnoceniZak` (jinak 1:1 se stejnou sadou sloupců jako naše `ec.vyhodnoceni_osoba`). **Delphi si ho dopočítává až v programu a nikam neukládá.**

Vlastní výpočet průměru bychom udělat uměli (15 310 hodnocení, 1 362 řádků má efektivitu ≠ 100), ale byl by to **náš výpočet, ne ten z Centrály** → červená by svítila u jiných lidí, než na jaké je Dušan zvyklý = horší než žádná barva. **Odemkne to až vzorec od Dušana.**

## 🔴 Bezpečnostní nález — banner nehlídá pravidlo rodiče

**Sdílenou sestavu gridu smí uložit jen rodič** (`is_marti_parent`) — `grid_layout_service._check_admin_for_shared`. API nerodiče odmítne hláškou *„Pouze admin (is_marti_parent) smí ukládat sdílené sestavy."*

**Ale schvalovací banner mostu tohle pravidlo NEHLÍDÁ.** Write request 1901 (převod osobní sestavy na sdílenou) **odklikl Jirka, který rodič není** (`users.id=20`, `is_marti_parent=false`) a prošlo. Ověřeno v `fw.claude_write_request.decided_by_user_id`. Věcně to nevadilo (jen barvy gridu), **ale je to obcházka práva a patří to Martimu k rozhodnutí.**

## Pasti při zakládání komponent přes most

- **Dvojtečka před názvem parametru se bere jako bind parametr, I V `--` KOMENTÁŘI** — SQLAlchemy prohledává celý text. Do `sql_text` datasetu skládej přes **`chr(58)`**; v komentáři ji před názvem nepiš vůbec. (Pokus #1907 padl na tom, že v komentáři stálo, na čem padl pokus #1903.)
- **`fw.comp_def.id` je GENERATED ALWAYS** → id nezadávej; na právě vloženého rodiče se odkazuj přes `SELECT id FROM fw.comp_def WHERE core_id=… AND name='…'`. NOT NULL bez defaultu: `type_id`, `name`, `core_id`, `created_by_text`, `updated_by_text`.
- **Občasné HTTP 401 „Nejsi přihlášen"** z mostu — není rozbité, stačí poslat znovu.

## Návrat zpět

```sql
UPDATE fw.comp_def SET parent_comp_def_id = 1250, sort_order = 30 WHERE id = 1275;
DELETE FROM fw.comp_def WHERE core_id = 203 AND name IN
  ('grid_hodiny_zakazek','gb_hodiny','tab_vyh_hodiny','tab_vyh_hodnoceni','pc_vyh_stred');
UPDATE fw.comp_def SET parent_comp_def_id = 1250, sort_order = 10 WHERE id = 1251;
UPDATE fw.comp_def SET parent_comp_def_id = 1250, sort_order = 20 WHERE id = 1262;
DELETE FROM fw.comp_def WHERE name IN ('pc_vyh_hlavicka','tab_vyh_souhrn','tab_vyh_pomoc');
```

Souvisí: `doc-vyroba-vyhodnoceni-penize-z-nasich-tabulek`, `doc-vyroba-vyhodnoceni-opravneni-uzaverka`, `doc-vyroba-vyhodnoceni-tlacitka-sefmonter-slouceni`.

