# Docházka new: zakládat a rušit docházku jen v Opravách — Nový/Smazat/Schválit skryté mimo Správu docházky (rozhodnutí Peťi 31. 8. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

**Peťa + Claude‑26, 31. 8. 2026.** Rozhodnutí Peťi: **zakládat a rušit docházku jde jen v Opravách.**

## Co se stalo

Peťa 31. 8. zadala Šárce Novotné (os. č. 16) v „Docházce new" na pátek 28. 8. docházku
08:00–15:00, 7 h. V Opravách se nezměnilo nic — den zůstal prázdný (odpracováno 0,00),
automat mu v noci dopsal 7 h do fondu a fronta Oprav ho dál hlásila jako
„pracovní den bez docházky i bez absence".

Zápis se přitom uložil. Jen do půlky systému.

## Příčina (ověřeno v kódu)

`modules/erp/api/dochazka_zak_tab.py`, endpoint `/app/dochazka-zak-tab/save-new` (ř. 452)
dělá **jediný `INSERT` do `tenant.vyroba_work`** a nic víc:

- **žádný `att_entry`** — docházkový záznam nevznikne
- **`att_entry_id` zůstane NULL** — řádek je sirotek
- žádný audit, žádná notifikace člověku, **žádný přepočet fondu**
- žádná kontrola překryvu ani uzamčeného období

Zrcadlově `/app/dochazka-zak-tab/delete-usek` (ř. 660) jen nastaví řádku rozpadu
`is_active=false` a připíše poznámku — **na `att_entry` nesáhne**. Hodiny tedy dál
běží v docházce i ve mzdách, jen nevisí na žádné zakázce.

Dohromady: „Nový" založí hodiny, které mzdy nevidí. „Smazat" schová hodiny, které
mzdy pořád počítají.

**Samo se to nesrovná.** Kaskáda `att_sync_vyroba_work` jde jen jedním směrem —
čte `att_entry` a z něj staví rozpad. Opačně to neumí; sirotka navíc při dalším
srovnání dne nejspíš deaktivuje.

## Rozsah — proč se to neprovalilo dřív

| tlačítko | kolikrát použito | kdo | naposledy |
|---|---|---|---|
| Nový (`save-new`) | **1×** za celou historii tabulky | Peťa | 31. 8. 2026 |
| Smazat (`delete-usek`) | 10× | jen Peťa | 4. 8. 2026 |
| Schválit (`save-doch-meta`, `ved_schvaleno`) | 0× na pracovním záznamu | — | — |

Živí sirotci s reálnými hodinami od 1. 7. 2026: **dva** — tenhle Šárčin a Martiho
z 31. 7. (13,2 h, noční běh, záměrně nedorovnaný, viz
`doc-dochazka-rozpad-polozky-bez-vazby-na-dochazku`).

## Ke „Schválit" — pozor na falešnou stopu

Napřed to vypadalo, že fajfku „S" používá Dušan (29 záznamů, naposledy 31. 8.).
Rozbor podle typu ukázal, že **všech 29 jsou absence** (21× dovolená, 4× sick day,
2× OSVČ absence, 2× dovolená ze žádosti) — fajfka se mu nastavuje **sama** při zadání
absence ve Správě docházky (pravidlo „co zadá správce, platí hned", Peťa 31. 7.).
V „Docházce new" si ji na pracovní záznam nedal nikdy nikdo. Peťa: *„tam přece
není co schvalovat."*

**Gotcha:** `ved_schvaleno_kym` sám o sobě neříká, kterou obrazovkou to prošlo.
Rozliš to podle `entry_type.category` (`absence` × `presence`) a `source`.

## Rozhodnutí

1. Z „Docházky new" (`apps/api/static_db/dochazka-po-zakazkach.html`) jdou pryč
   tlačítka **Nový**, **Smazat** i **Schválit**.
2. Zakládání a rušení docházky **jen v Opravách** — `att_fix_add` / `att_fix_void`.
   Obě (i `att_fix_entry`, `att_fix_polozka`) volají kaskádu do rozpadu **a** přepočet
   fondu `_att_automat_recalc_day`, takže den sedí včetně doplnění nad/do fondu.
3. **Úprava zakázky a činnosti na existujícím řádku v „Docházce new" ZŮSTÁVÁ.**
   To je čistě rozpad, docházky se netýká a je to přesně účel té obrazovky.

Zvažovaná varianta „přeposlat `save-new` na `att_fix_add`" **zamítnuta**: formulář
v „Docházce new" nemá pole, která ta funkce potřebuje, takže by se musel domýšlet
typ záznamu ze zakázky, dosazovat důvod a ignorovat ručně zadané hodiny. Tři
domyšlené hodnoty = tři budoucí tiché chyby.

## Souvislosti

- `doc-dochazka-rozpad-polozky-bez-vazby-na-dochazku` — starší kolo téhož problému;
  jeho „DOŘEŠENO 12.–14. 8." platí jen pro cestu z mobilní appky, ne pro tuhle.
- `doc-dochazka-att-entry-vyroba-work-kaskada` — kanonický model hlavička × položky.
- `doc-dochazka-doch-bod1-att-entry-id-app-link` — samodoplňování vazby časem;
  u prázdného dne nemá co najít, sirotek zůstane.

## PAST: „Docházka new" a „Správa docházky" jsou JEDNA stránka

Ověřeno bolestivě 31. 8. 2026 — nejdřív jsem tlačítka odebrala natvrdo a **vzala je tím
i Správě docházky**, kde být musí. Vráceno do minuty, pak uděláno pořádně.

`apps/api/static_db/dochazka-po-zakazkach.html` obsahuje **oba pohledy**. Přepínají se
chipy nad tabulkou a drží se v proměnné `OBD`:

| `OBD` | pohled |
|---|---|
| `vse` / `all` | Docházka new (docházka po zakázkách) |
| `budoucnost` | **Správa docházky** (plánované absence) |
| `ohlaseni` | Ohlášení nepřítomnosti |

**Kontextové menu je jen jedno** (`<div class="ctxm" id="ctxm">`) a obsluhuje všechny
pohledy. Táž položka tam znamená pokaždé něco jiného:

- **Nový** — v docházce zakládal úsek rozpadu (`save-new`), ve Správě zakládá **absenci**
  (`absOpen('new')`, ř. 969)
- **Smazat** — v docházce `delete-usek`, ve Správě **maže absenci** (`absDel`, ř. 1430)
- **Schválit / zamítnout absenci**, **Schválit označené**, **Vzít schválení zpět** —
  patří k absencím, tedy do Správy

**Řešení (nasazeno, verze souboru 48):** položky v menu zůstaly, jen dostaly `id`
(`ctx_novy`, `ctx_smazat`, `ctx_schval`, `ctx_schval_ozn`, `ctx_odschval_ozn`) a
`openCtx()` je **skrývá, když `OBD !== 'budoucnost'`**. Ve Správě docházky funguje
všechno jako dřív, v Docházce new zbyl Excel, Import, Sumace a spol.

**Poučení pro příště:** než v téhle stránce něco odebereš, zjisti, ve kterém pohledu to
žije. Skoro nic tam není jen pro jeden.

**Gotcha k nasazení:** `@@G2007PUBLISH` na téhle stránce padá na falešném poplachu
s počty `<div>` (viz `doc-system-strategie-g2007publish-falesny-poplach-tagy`), takže
zápis jde přes `@@G2007SOUBOR <kod> | artefakt` + obsah a pak `@@G2007EXPORT <kod>` na disk.
Obě vracejí **prázdnou návratovku i když uspějí** — ověřuj čtením délky a verze v
`g2007.soubor`. Předchozí verze je v `g2007.soubor_historie`.

