# Modul „Příplatky a srážky" (Mzdy) — HOTOVO 21.7.2026

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V2.0 · rozsah: globální (všichni tenanti)


# 💰 Modul „Příplatky a srážky" (Mzdy) — HOTOVO k 21. 7. 2026

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V2.0 · rozsah: globální (všichni tenanti)

**Stav:** ✅ **funkčně kompletní 1:1** (jako „Vyhodnocení zakázek"). Postavil Claude-27, 21. 7. 2026 přes bridge (lane 2). Schéma `ec`.
Browse → edit → schválit/vyplatit. Napojení na Helios přes mzdovou složku + flag ReakceMzdy (příště: průběžný sync + entity-pickery).

---

## 1. Co je hotové (ID v produkci)

**Data** — `ec.pripl_srazky` = **132 řádků** za 6–7/2026 (port z DB_EC `EC_FinPriplatkySrazkyDefinice`, původní ID zachovány přes `OVERRIDING SYSTEM VALUE`). Katalog `ec.pripl_srazky_typy` = 49 typů (45 aktivních). Číselník `ec.cis_zam` = 430 zaměstnanců.

**Přehled** (grid) — core `ec.pripl_srazky_prehled` (id 206), grid comp_def 1279 (typ 101), data_source 197 → data_set 193 `ec.pripl_srazky_list` (JOIN typy=druh odměny + cis_zam 2× dostane/navrhl). 2 ops: select(262 list) + edit(264 opener, core_id=207).

**Jádro** (edit formulář) — core `ec.pripl_srazky_jadro` (id 207), 20 comp_defů: form_root(302) + 2 sekce groupbox(12): „Příplatek/srážka" + „Vyplacení a audit" + 17 polí(typ 2, name=sloupec). data_source jádro → edit op 263 + data_set 194 `SELECT * FROM ec.pripl_srazky` (framework filtruje na id řádku).

**Menu** — nový uzel `💰 Mzdy` (id 194, top-level) + leaf „Příplatky a srážky" (id 195, core_id=207). Cesta: ERP strom → 💰 Mzdy → Příplatky a srážky.

**Procedury** (port z `EC_Mzdy_VyplatitPriplSrazky`) — `ec.pripl_srazky_vyplatit(id, cmd)` (1=vyplatit: dat_vyplaceni+vyplatil+poznámka / 2=zrušit) a `ec.pripl_srazky_schvalit(id, cmd)` (1/2). Grant EXECUTE roli `strategie`. Stav „vyplaceno" = `dat_vyplaceni IS NOT NULL` (jako v Centrále).

**Akční tlačítka** — FE lišta `ec_pripl_srazky_actions.js` (wrap DesignFwForm._render pro core `ec.pripl_srazky_jadro`): Schválit / Zrušit schválení / Vyplatit / Zrušit vyplacení → `POST /api/v1/erp/action/run`. Backend whitelist v `vyhodnoceni_actions.py` (`pripl_vyplatit`/`pripl_schvalit`, kind `id_cmd`, běží s COMMITem). Registrace v `router.py`. Commity: grid+jádro přes bridge write (#1283/#1284/#1285), tlačítka deploy `418522c5`.

## 2. Framework gotchas nově objevené (21.7., cenné pro další moduly)

1. **Bridge write routuje podle PRVNÍHO klíčového slova.** `WITH ... (INSERT ...)` (CTE) se tváří jako READ → read-path substring filtr zařízne `INSERT` („forbidden keyword"). **Multi-tabulkový build dělej sérií samostatných `INSERT` příkazů**, kde pozdější dohledávají id dřívějších přes unikátní `code`/`name` subquery (ne RETURNING/CTE, ne DO blok). První příkaz musí začínat `INSERT`/`CREATE` → routuje se na write-approval.
2. **Read-path má naivní substring blocklist** — zařízne i slova ve stringu/literálu (`EXECUTE`, `UPDATE`…). Ve verifikačních SELECTech se jim vyhni (např. `has_function_privilege(...,'EXECUTE')` spadne).
3. **`CREATE FUNCTION`/DDL projde write cestou** (jako `CREATE TABLE`), $$-quoting OK. POZOR na SQLAlchemy bind-param past: token „dvojtečka+písmeno" bere jako parametr i uvnitř dollar-quote/stringu → v uloženém SQL se mu vyhni (řeš přes `chr(58)`); přetypování dvěma dvojtečkami funguje. Ironií tahle znalost na tu past narazila při vlastním zápisu (#1286).
4. Platí vše z „Vyhodnocení zakázek": comp_def root(top-level) root=1+parent NULL, child root NULL+parent set; edit-op MUSÍ mít `core_id`; NOT NULL `created_by_text`/`updated_by_text`; grant `ec` roli `strategie`.

## 3. Multi-lane bridge (vedlejší výstup, commit 4b4abf58)
Víc Cowork session na jednom stroji kolidovalo na jednom kanálu → přidány lanes: lane „" = default `CLAUDE_*`, lane 2 = `CLAUDE2_*`, lane 3 = `CLAUDE3_*` (Kris). Prefix `CLAUDE<N>_` (ne `__N`, kolize s nonce úklidem). Detail v CLAUDE.md.

## 4. Zbývá (nice-to-have, ne blokující)
- Entity-pickery místo číselných ID (typ→typy, zaměstnanec→cis_zam) v Jádru.
- Pohledy pojištění/tarif/kvalita jako filtry/varianty přehledu.
- Průběžný produkční sync z DB_EC místo demo snapshotu.
- Viditelnost uzlu 💰 Mzdy pro mzdovou účetní (teď `private`=admin).
- Export do Heliosu (`hp_VlozMzPausDoMzSloz`) — viz mirror analýza.

## Návaznosti
- [[doc-mzdy-priplatky-srazky-mirror]] (univerzální mirror + přesčasové konto) · [[doc-vyroba-vyhodnoceni-zakazek]] (vzor frameworku)


