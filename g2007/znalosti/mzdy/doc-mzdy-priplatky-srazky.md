# 💰 Modul „Příplatky a srážky" (Mzdy) — STAV k 21. 7. 2026 (odpoledne)

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# 💰 Modul „Příplatky a srážky" (Mzdy) — STAV k 21. 7. 2026 (odpoledne)

**Připravil:** Claude, 21. 7. 2026 · **Cíl (Marti):** funkční **1:1 modul do mezd** (jako „Vyhodnocení zakázek"). Schéma `ec`.
**Stav:** analýza hotová · DB základ + katalog typů nasazen · **datový sync připraven, čeká na schválení** · UI zatím nepostaveno (pauza).

---

## 1. Co modul dělá
Evidence **příplatků a srážek ke mzdě** per pracovník. Řádek = *druh odměny (Typ)* · komu (dostane) · kdo navrhl ·
měsíc/rok proplacení · částka/sazba/hodiny · zakázka · Schváleno · Vyplaceno. Napojení na mzdy přes **mzdovou složku**
typu (651, 700, 953…) + flag **ReakceMzdy**. Rodina `EC_Fin*` (jako `EC_ZakazkyFinanceZam` z vyhodnocení).

## 2. Zdroj v Centrále (DB_EC)
- Jádro **`645:0 „Příplatky‑Srážky‑Definice"`** (edit formulář).
- Přehled **„Mzdy/Příplatky/Srážky"** + pohledy *pojištění · tarif · kvalita · vše*.
- Tabulky: `EC_FinPriplatkySrazkyDefinice` (31 sl.), `EC_FinPriplatkySrazkyDefiniceTypy` (12 sl., 49 typů).
- Proc: `EC_Mzdy_VyplatitPriplSrazky(@ID,@Command)` (1=vyplatit/2=zrušit), `EC_GenMesicnichSrazek`, `EC_GenDobropisBonus`.
  (Stovky `hp_Mz*` = celý Helios mzdový engine — MIMO tento modul.)

## 3. HOTOVO — DB v PG (schéma `ec`)
| DB_EC | → PG `ec.` | stav |
|---|---|---|
| `EC_FinPriplatkySrazkyDefiniceTypy` | **`ec.pripl_srazky_typy`** | ✅ 49 typů naseedováno (45 aktivních), granty pro `strategie` |
| `EC_FinPriplatkySrazkyDefinice` | **`ec.pripl_srazky`** | ✅ tabulka (31 sl. 1:1, id GENERATED, typ FK → typy) |

Mapa sloupců beze změny (viz předchozí verze): int→integer, bit→boolean, nvarchar→text, numeric→numeric, datetime→timestamptz.

## 4. PŘIPRAVENO — datový sync (čeká na schválení #1258)
Vygenerováno z DB_EC, připraveno jako **jeden** write‑request:
- **`ec.cis_zam`** — plný číselník **430 zaměstnanců** (TabCisZam); `prijmenijmeno` se v PG přepočítává z prijmeni+jmeno (čisté).
- **`ec.pripl_srazky`** — **131 řádků** za 6–7/2026 (přesně data z printscreenu: id 19955 Zeman −57, 19940 Havlát 6921/15,64 h, 19938 Fakturace 407 269 …).

⚠️ **Pozor (multi‑instance):** #1258 je stále `pending` — v banneru se schvalovaly requesty jiných Claude instancí (Kristy/Šárka/Péťa/Jirka). Než se modul dostaví, **schválit #1258** (nebo znovu vygenerovat sync). Do té doby `cis_zam` obsahuje jen 3 testovací (z vyhodnocení) a `pripl_srazky` je prázdné.

## 5. ZBÝVÁ (po schválení dat) — postup jako vyhodnocení
1. **Procedura** `ec.pripl_srazky_vyplatit(p_id, p_cmd)` — toggle vyplaceno (1:1 z `EC_Mzdy_VyplatitPriplSrazky`).
2. **Přehled „Mzdy/Příplatky/Srážky"** — fw core + grid_modern nad `ec.pripl_srazky` JOIN `pripl_srazky_typy` (druh odměny) + `cis_zam` (dostane/navrhl). Pohledy pojištění/tarif/kvalita/vše = varianty/filtry přes `typ`/mzdovou složku. Uzel v Mzdy stromu (založit „💰 Mzdy" — dnes není).
3. **Jádro 645** — fw form (302) nad `ec.pripl_srazky`, klíč `id`. Pole: druh odměny (lookup na typy), navrhl/dostane (lookup cis_zam), měsíc/rok proplacení, hodiny/sazba/částka, zakázka, checkboxy Měsíčně/Fix/Schváleno, poznámka. **edit‑op MUSÍ mít `core_id`** (jinak prázdný záznam).
4. **Akční tlačítka** Vyplatit / Zrušit vyplacení / Schválit → endpoint `/action/run` (rozšířit whitelist o `pripl_*`).

## 6. Framework gotchas (viz zápis „Vyhodnocení zakázek", oblast Výroba)
Identity id (RETURNING) · `:master_id` přes `chr(58)` · JSON layout přes `jsonb_build_object` · constraint root/parent (child root NULL) ·
**edit‑op potřebuje `core_id`** · vnořený grid potřebuje `layout.kind='select-detail'+filter_field='master_id'` · grant `ec` roli `strategie` ·
**NOT NULL `created_by_text`/`updated_by_text`** na core/comp_def/menu_node (vždy vyplnit) · TRUNCATE s FK → použít DELETE/ON CONFLICT.

## 7. Data / poznámka
Katalog typů (49) + číselník (430) jsou snapshot k 21. 7. 2026. Řádky `ec.pripl_srazky` = vzorek 6–7/2026 (131) pro demo;
pro produkci napojit průběžný sync z DB_EC. Typy i číselník udržovat sync‑em (v Centrále se mění).


