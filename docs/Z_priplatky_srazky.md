# 💰 Modul „Příplatky a srážky" (Mzdy) — analýza + DB základ (1:1 z Centrály)

**Připravil:** Claude, 21. 7. 2026 · **Stav:** analýza hotová, DB základ nasazen, UI zbývá.
**Cíl (Marti):** funkční **1:1 modul do mezd** — jako u „Vyhodnocení zakázek". EUROSOFT‑specifické → PG schéma `ec`.

---

## 1. Co modul dělá
Evidence **příplatků a srážek ke mzdě** per pracovník. Jeden řádek = jeden příplatek/srážka:
*druh odměny (Typ)* · komu (dostane) · kdo navrhl · měsíc/rok proplacení · částka / sazba / hodiny ·
zakázka · **Schváleno** · **Vyplaceno**. Napojení na mzdy přes **mzdovou složku** typu (651, 700, 953…)
a flag **ReakceMzdy** (jde reálně do výplaty). Je to sourozenec vyhodnocení — rodina `EC_Fin*`
(jako `EC_ZakazkyFinanceZam`), most mezi vyhodnocením/odměnami a mzdovým listem.

## 2. Zdroj v Centrále (DB_EC)
- **Jádro `645:0 „Příplatky‑Srážky‑Definice"`** — editační formulář (viz printscreen): druh odměny,
  č. odměnu navrhl, č. odměnu dostane, Měsíc/Rok proplacení, Skutečně vyplaceno dne, Hodiny, Sazba,
  Částka, Číslo zakázky, Poznámka; checkboxy Měsíčně / Fix / Schváleno / Propsat poznámku do VOBJ.
- **Přehled „Mzdy/Příplatky/Srážky"** + pohledy: *…pojištění · ‑ tarif · …‑ kvalita · ‑ vše*
  (grid nad definicí + join na typy a osoby; ~11 800 řádků).
- **Tabulky:** `EC_FinPriplatkySrazkyDefinice` (31 sl.), `EC_FinPriplatkySrazkyDefiniceTypy` (12 sl., 49 typů).
- **Procedury:** `EC_Mzdy_VyplatitPriplSrazky(@ID,@Command)` (toggle vyplaceno: 1=nastav DatVyplaceni+Vyplatil, 2=zruš),
  `EC_GenMesicnichSrazek` (generuje měsíční „Měsíčně" řádky), `EC_GenDobropisBonus`.
  (Stovky `hp_Mz*` = celý Helios mzdový engine — daňový bonus, exekuční srážky — **mimo tento modul**.)

## 3. DB port do PG — HOTOVO (schéma `ec`)
| DB_EC | → PG `ec.` | pozn. |
|---|---|---|
| `EC_FinPriplatkySrazkyDefiniceTypy` | **`ec.pripl_srazky_typy`** | katalog „druh odměny", 49 typů **naseedováno** |
| `EC_FinPriplatkySrazkyDefinice` | **`ec.pripl_srazky`** | 31 sloupců 1:1 (id GENERATED, typ FK → typy) |

Mapování sloupců (definice): `ID→id, IDZdroj→id_zdroj, Typ→typ (FK), Schvaleno→schvaleno, CisloZamNavrhl→cislo_zam_navrhl,
CisloZam→cislo_zam, Přeneseno→preneseno, IdMzdoveSlozky→id_mzdove_slozky, Mesicne→mesicne, Fix→fix, Mesic→mesic,
Rok→rok, PlatnostOd/Do→platnost_od/do, Hodiny→hodiny, Sazba→sazba, Castka→castka, CisloZakazky→cislo_zakazky,
DatVyplaceni→dat_vyplaceni, Vyplaceno→vyplaceno, Vyplatil→vyplatil, Poznamka→poznamka, Zdroj→zdroj,
Autor/DatPorizeni/Zmenil/DatZmeny, IDPolVobj→id_pol_vobj, IDPolPF→id_pol_pf,
PropsatPoznamkuDoVOBJ→propsat_poznamku_do_vobj, CastkaVypocetHodSazby→castka_vypocet_hod_sazby`.
Typy: int→integer, bit→boolean, nvarchar→text, numeric→numeric, datetime→timestamptz.
Granty pro roli `strategie` nastaveny.

## 4. Katalog typů (druh odměny) — 49, vazba na mzdovou složku
Např.: 4 = Telefonní tarif do MZDY (953, ReakceMzdy=ne), 7 = Jednorázové odměny od vedoucího (651),
23 = Odměna garant (651), 44 = Odměna garant ‑ čtvrtletní (651), 20–25/31/45/46/48 = Fakturace:* (bez mzdové složky,
ReakceMzdy=ne — jen evidence/fakturace), 1–3 = DPP (700), 17 = Odměna Jednatel (693), 18 = Roční zúčtování daně (97),
32 = Odstupné (697), 47 = Cesťák (791), 37/38 = Landmark náhrady (794/795). Flag **ZobrazujVeVyplatnici** řídí zobrazení na pásce.

## 5. Zbývá dodělat (pokračování modulu)
1. **Procedury** → `ec.pripl_srazky_vyplatit(p_id, p_cmd)` (1:1 toggle) + `ec.pripl_srazky_gen_mesicni(rok,mesic)` (generátor „Měsíčně").
2. **Přehled „Mzdy/Příplatky/Srážky"** v Mzdy stromu + 4 pohledy (pojištění/tarif/kvalita/vše) — filtry přes `typ` / mzdovou složku
   (grid_modern nad `ec.pripl_srazky` JOIN `pripl_srazky_typy` + jména z `cis_zam`).
3. **Jádro 645** (fw form 302) nad `ec.pripl_srazky` — pole dle formuláře, lookup „druh odměny" na `pripl_srazky_typy`,
   lookupy osob na `cis_zam`; klíč = `id`.
4. **Akční tlačítka**: Vyplatit / Zrušit vyplacení (`pripl_srazky_vyplatit`), příp. Schválit. Endpoint `/action/run` rozšířit o `pripl_*` whitelist.

## 6. Framework gotchas (viz zápis „Vyhodnocení zakázek", oblast Výroba)
Identity id (RETURNING), `:master_id` přes `chr(58)`, JSON layout přes `jsonb_build_object`, constraint root/parent (child root NULL),
**edit‑op potřebuje `core_id`**, vnořený grid potřebuje `layout.kind='select-detail'+filter_field='master_id'`, grant schématu `ec` roli `strategie`.
Stejné vzory platí i tady — postup 1:1 zopakovat.

## 7. Poznámka k datům
Katalog typů je naseedován k 20. 7. 2026 (snapshot). Ostrá data řádků (`ec.pripl_srazky`) zatím prázdná —
pro produkci napojit sync z DB_EC (nebo import). Typy udržovat sync‑em, protože se v Centrále mění.
