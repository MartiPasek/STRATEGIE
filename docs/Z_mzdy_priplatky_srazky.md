# 💰 Modul „Příplatky a srážky" (Mzdy) — HOTOVO k 22. 7. 2026

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V3.0 · rozsah: globální (všichni tenanti)

**Stav:** ✅ funkčně kompletní 1:1 (jako „Vyhodnocení zakázek"). Postavil Claude-27 21. 7. 2026 přes bridge (lane 2), schéma `ec`.
**Převzal a doladil Claude-28 (Jirka) 22. 7. 2026:** viditelnost pro mzdovou účetní, živé zrcadlo z Centrály, vypnutí zápisových tlačítek.
Browse → edit. Napojení na Helios přes mzdovou složku + flag ReakceMzdy.

---

## 1. Co je hotové (ID v produkci)

**Data** — `ec.pripl_srazky` (port z DB_EC `EC_FinPriplatkySrazkyDefinice`, původní ID zachovány přes `OVERRIDING SYSTEM VALUE`). Od 22. 7. **živé zrcadlo, ne snapshot** — viz §4. Katalog `ec.pripl_srazky_typy` = 49 typů (45 aktivních). Číselník `ec.cis_zam` = 430 zaměstnanců.

**Přehled** (grid) — core `ec.pripl_srazky_prehled` (id 206), grid comp_def 1279 (typ 101), data_source 197 → data_set 193 `ec.pripl_srazky_list` (JOIN typy=druh odměny + cis_zam 2× dostane/navrhl). 2 ops: select(262 list) + edit(264 opener, core_id=207).

**Jádro** (edit formulář) — core `ec.pripl_srazky_jadro` (id 207), 20 comp_defů: form_root(302) + 2 sekce groupbox(12) + 17 polí(typ 2, name=sloupec). data_source jádro → edit op 263 + data_set 194 `SELECT * FROM ec.pripl_srazky`.

**Menu** — uzel `💰 Mzdy` (id 194, top-level) + leaf „Příplatky a srážky" (id 195, core_id=207).

**Viditelnost** (Claude-28, 22. 7.) — oba uzly `visibility_scope='restricted'`, `visibility_user_ids={13,18}`:
**Petra Šafránková (uid 18) = mzdová účetní** (ověřeno: org post 66 MZDOVÁ ÚČETNÍ) a **Šárka Novotná (uid 13) = personalistka** (post 35/36) — stejná dvojice, jaká vidí uzel „Finanční podmínky". Obě mají v tenantu 2 roli `member`, takže projdou i přes `_require_erp_member`. Rodiče a admini vidí uzel tak jako tak (doctrine #5). Rozhodl Jirka 22. 7.
Mechanika (ověřeno v kódu `router.py` `_build_system_root_from_db`): `parent_only`/NULL vidí všichni, `private`/`restricted` jen lidé ve `visibility_user_ids` + kaskáda předků, rodič vidí vše.

**Procedury** (port z `EC_Mzdy_VyplatitPriplSrazky`) — `ec.pripl_srazky_vyplatit(id, cmd)` (1=vyplatit / 2=zrušit) a `ec.pripl_srazky_schvalit(id, cmd)`. Grant EXECUTE roli `strategie`. Stav „vyplaceno" = `dat_vyplaceni IS NOT NULL`.

**Akční tlačítka** — `ec_pripl_srazky_actions.js` → `POST /api/v1/erp/action/run`, whitelist v `vyhodnoceni_actions.py` (`pripl_vyplatit`/`pripl_schvalit`, kind `id_cmd`, s COMMITem).
⚠️ **Od 22. 7. VYPNUTÁ** (`var ENABLED = false`) — důvod v §5. Kód zůstal kompletní, zapnutí = přepnout jednu konstantu.

## 2. Framework gotchas (21. 7. Claude-27)

1. **Bridge write routuje podle PRVNÍHO klíčového slova.** `WITH ... (INSERT ...)` (CTE) se tváří jako READ → filtr zařízne `INSERT`. **Multi-tabulkový build dělej sérií samostatných `INSERT`**, kde pozdější dohledávají id dřívějších přes unikátní `code`/`name` subquery (ne RETURNING/CTE, ne DO blok).
2. **Read-path má naivní substring blocklist** — zařízne i slova ve stringu/literálu (`EXECUTE`, `UPDATE`…).
3. **`CREATE FUNCTION`/DDL projde write cestou.** POZOR na SQLAlchemy bind-param past: „dvojtečka+písmeno" je parametr i uvnitř dollar-quote → řeš přes `chr(58)`.
4. Platí vše z „Vyhodnocení zakázek": comp_def root(top-level) root=1+parent NULL, child root NULL+parent set; edit-op MUSÍ mít `core_id`; NOT NULL `created_by_text`/`updated_by_text`; grant `ec` roli `strategie`.

## 3. Multi-lane bridge (vedlejší výstup, commit 4b4abf58)
Lane „" = default `CLAUDE_*`, lane 2 = `CLAUDE2_*`, lane 3 = `CLAUDE3_*`. Detail v [[doc-system-strategie-bridge-most-lanes-ops]].

---

## 4. ✅ Živé zrcadlo z Centrály (Claude-28, 22. 7. 2026)

**Problém:** modul zobrazoval demo vzorek 132 řádků za 6–7/2026, zatímco v Centrále je za 2026 celkem 792 řádků. Uživatel by viděl neúplnou pravdu.

**Řešení:** `modules/erp/api/pripl_srazky_sync.py` + job **`sync_pripl_srazky_ec`** v řídícím centru zrcadel (`fw.mirror_job`, interval 60 min).
- Rozsah **aktuální + předchozí rok** (Marti-AI: Petra potřebuje historický kontext při kontrolách; starší mzdy jsou uzavřené).
- Inkrementálně podle `ISNULL(DatZmeny, DatPorizeni)`; **vyplacené řádky se přepisují taky** (opravné doklady se dějí a chceme je vidět).
- **Sebeléčení podle seznamu ID:** co je v Centrále a chybí u nás → dotáhne adresně; co v Centrále není → smaže.
- Souběžně se obnovuje i katalog typů (`sync_typy`).

### ⚠️ Dvě různá zrcadla TÉHOŽ zdroje — nepleť si je
| Job | Cíl | Účel |
|---|---|---|
| `sync_priplatky` (Marti 10. 6.) | `tenant.wage_movement` | **univerzální CÍLOVÝ model** (781 řádků 1–7/2026, 1×/h) |
| `sync_pripl_srazky_ec` (22. 7.) | `ec.pripl_srazky` | **1:1 zrcadlo pro modul 💰 Mzdy** |

Obojí čte `EC_FinPriplatkySrazkyDefinice`. Zrcadlo `ec` je **přechodný stav** — neinvestovat do něj, cíl je `wage_movement`.

## 5. 🚦 Směr dat — ZÁVAZNÉ (verdikt Marti-AI, 22. 7. 2026, msg 11066)

**Centrála = zdroj pravdy. STRATEGIE = zrcadlo JEN KE ČTENÍ. Zpětný zápis se NEDĚLÁ.**

Petra schvaluje a vyplácí dál v Centrále, protože mzdu počítá Helios z dat Centrály. Kdyby u nás zůstala aktivní tlačítka: (a) první další sync by jejich výsledek přepsal, (b) změna by se nikdy nedostala do mezd. Proto jsou vypnutá.

**Zapnutí zpětného zápisu do `EC_FinPriplatkySrazkyDefinice` musí OSOBNĚ odsouhlasit Marti Pašek** — Marti-AI to označila za nepřekročitelné (mzdová data = právní dopad) a pojmenovala tři rizika:
1. **PrenesDoMezd / uzávěrka** — změna stavu po běhu přenosu → složka v Heliosu jinak než v Centrále. Vyžaduje analýzu s Petrou, která PrenesDoMezd zná.
2. **Přesčasové konto** — kumulace přes měsíce; změna historického záznamu konto rozhodí.
3. **Kontroly integrity Centrály** — zápis zvenčí je obejde a projeví se až při uzávěrce.

**Otázka pro Marti (30 s, formulace Marti-AI):** *„Příplatky/srážky: chceme zapsat schválení z STRATEGIE zpět do Centrály, nebo nechat Petru schvalovat v Centrále a my jen čteme? Zápis do mzdových dat chceme dělat vědomě."*

## 6. Gotchas z 22. 7. (Claude-28)

1. **EC sloupec `Přeneseno` má diakritiku** → v dotazu `[Přeneseno]` + alias na PG název. Bez toho dotaz spadne.
2. **Watermark sync sám nedorovná historii.** `max(dat_zmeny)` říká „od kdy jsou změny", ne „co chybí" — první ostrý běh proto udělal `ins=0, upd=1` místo ~1600 řádků. Vždy přidej srovnání podle seznamu ID.
3. **Diakritika v SQL přes most se překóduje** (`Příplatk` → `Ĺ™Ă­platk`) a MSSQL vrátí `internal_error`. Přes most piš **ASCII-only** dotazy.
4. Typ komponenty pro výběr ze seznamu je **110 `lookup`**: `comp_def.data_source_id` + `layout {lookup_id_field, lookup_display_field, data_source_code}` (živý vzor: core 191 `prijate_objednavky_uprava`).

## 7. Zbývá (nice-to-have, neblokuje)
- **Lookupy místo číselných ID** v Jádru (typ → `pripl_srazky_typy`, zaměstnanec → `cis_zam`). Připraveno, čeká na schválení zápisů do `fw.*`.
- **Pohledy pojištění / tarif / kvalita jako filtry přehledu** — ⚠️ **nejasné zadání**: v katalogu typů odpovídá „tarif" typům 4+43 (telefonní tarif) a „kvalita" typům 30+31, ale **žádný typ neodpovídá „pojištění"**. Před stavbou si vyžádat od Claude-27/Petry, co ty tři pohledy v Centrále přesně filtrují.
- **Export do Heliosu** (`hp_VlozMzPausDoMzSloz`) — blokováno stejným rozhodnutím jako §5.
- Read-only počítaná pole v jádru.

## Návaznosti
- [[doc-mzdy-priplatky-srazky-mirror]] (univerzální mirror + přesčasové konto) · [[doc-vyroba-vyhodnoceni-zakazek]] (vzor frameworku) · [[doc-system-strategie-bridge-most-lanes-ops]]
