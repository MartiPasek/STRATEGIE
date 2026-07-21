# 🏭 Modul „Vyhodnocení zakázek" (pro Dušana / vedoucího výroby)

> oblast: `vyroba` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# 🏭 Modul „Vyhodnocení zakázek" (pro Dušana / vedoucího výroby)

**Připravil:** Claude, 20. 7. 2026 · **Pro:** Jirka (doladění) · **Stav:** funkčně kompletní, ověřeno 1:1 na VR10704.

Kopie modulu „Vyhodnocování zakázek" z Centrály (DB_EC) do STRATEGIE. Cíl (Marti):
**funkční 1:1 zrcadlo originálu** — hodiny → efektivita → prémie/srážka per pracovník → uzávěrka → výplata (SuperHrubá). EUROSOFT‑specifické → vlastní PG schéma `ec`.

---

## 1. Kde to je
ERP workspace `strategie-ai.com/erp` → levý strom → **🏭 Výroba → Zakázky k vyhodnocení**.
(Není to ve FLOW `/flow` — to je jiná, read‑only plocha.)

- **Přehled „Zakázky k vyhodnocení"** (fw.core `ec.vyhodnoceni_prehled`, id 199) — seznam zakázek, klik na řádek otevře jádro.
- **Jádro „Vyhodnocení zakázky"** (fw.core `ec.vyhodnoceni_jadro`, id 203) — detail: sekce **Souhrn** + **Pomocné výpočty**, gridy **Hodnocení vše** a **Finální vyhodnocení (výplata)**, nahoře lišta akčních tlačítek.

---

## 2. Backend — PG schéma `ec` (1:1 port z DB_EC)

### Tabulky (zrcadlo Centrály)
`ec.vyhodnoceni_zakazka` (hlavička per zakázka), `ec.vyhodnoceni_osoba` (pracovní hodnocení osoby),
`ec.zakazky_finance_zam` (+`_archiv`) (finální výplata), `ec.vyhodnoceni_konstanty` (globální sazby),
`ec.tab_zakazka` / `ec.tab_zakazka_ext`, `ec.dochazka` (+`_neevidovana`), `ec.dilna_cinnosti`,
`ec.cis_zam`, `ec.zakazky_skupiny` (sloučené zakázky). Typy: numeric→numeric, bit→boolean, nvarchar→text, datetime→timestamptz.

### Funkce (port procedur `EC_Zakazky_Vyhodnoceni_*`)
| PG funkce `ec.` | Origin (DB_EC) | Co dělá |
|---|---|---|
| `prepocet_vyhodnoceni(p_zak)` | `EC_Zakazky_PrepocetVyhodnoceni` | **jádro**: hodiny z docházky přes skupinu → efektivita → prémie(ušetřený čas)/srážka per osoba → `premie_osoba_final = ceil(x/5)*5`; šéfmontér; součet do hlavičky |
| `priprava_vyhodnoceni(p_zak)` | `EC_Zakazky_PripravaVyhodnoceni` | naplní `vyhodnoceni_osoba` z odpracovaných hodin, pak přepočet |
| `vypocet_konstant(p_zak)` | `EC_Zakazky_Vyhodnoceni_vypocetKonstant` | „Nastav koeficienty" — dopočet hlavičky (kalk h, limit srážky, ušetřeno/přetaženo, plánováno…) |
| `vyhodnoceni_uzavrit(p_zak)` | `EC_Zakazky_VyhodnoceniUzavrit` | uzávěrka → zápis výplaty do `zakazky_finance_zam`; `vyplatit = mzda + premie_final × 1,4` (OSVČ ×1) |
| `vyhodnoceni_zrusit(p_zak)` | `EC_Zakazky_VyhodnoceniZrusit` | archiv neuzavřených + smaz finance + reopen hlavičky/ext |
| `slouci_zakazky(p_zaks[])` / `slouci_zakazky_zrus` | `SlouciZakazky_hromadny` / `_Zrus` | Hodnotit společné / Zruš — přes `idskupiny` + `zakazky_skupiny` |
| `nastav_sefmontera(p_id)` / `nastav_multif(p_id,p_mode)` | `NastavSefmontera` / `NastavMultif` | toggle šéfmontér (+propagace do ext) / nepodepsaný ZL |

**Vědomě neportováno** (mimo modul dvou obrazovek): `EC_KontrolaVyhodnocenychZakazek` (měsíční kontrola dílů — úkolník + sklad), `VyhodnoceniOdesliUkol`, `Garanti_ZaznamyProVypocetOdmen`.

### Akční endpoint (kód)
`POST /api/v1/erp/action/run` — `modules/erp/api/vyhodnoceni_actions.py`. Body `{action_code, id}` (nebo `cislo`/`zaks`/`osoba_id`+`mode`). Whitelist 9 `ec.*` funkcí, běží na `get_data_session()` **s commitem** (generický `/data/{code}` necommituje → pro side‑effecty nepoužitelný), role‑gate `_require_erp_member`. Business chyby vrací funkce jako `E#...`.
Frontend: `apps/api/static/erp/components/ec_vyhodnoceni_actions.js` — wrapuje `DesignFwForm.prototype._render`, pro core `ec.vyhodnoceni_jadro` vloží lištu tlačítek (Připravit / Přepočet / Nastav koeficienty / Uzavřít / Zrušit).

---

## 3. UI složeno z `fw.*` (data‑driven, žádný deploy pro DB změny)
Screen = `fw.core` + strom `fw.comp_def` (typy: 302 form, 12 groupbox/sekce, 2 edit/pole, 101 grid_modern). Data přes `fw.data_source` → `fw.data_source_op` → `fw.data_set.sql_text`. Klíč modulu = **`ec.vyhodnoceni_zakazka.id`** (bigint).

- **Přehled**: 1 grid (101) nad data_setem `ec.vyhodnoceni_prehled_list` (SELECT z `ec.vyhodnoceni_zakazka`, „ID" = z.id). Menu uzel pod „🏭 Výroba".
- **Jádro**: form_root (302) → data_set `ec.vyhodnoceni_jadro_rec` (`SELECT * FROM ec.vyhodnoceni_zakazka`); pod ním 2 sekce s poli + 2 gridy s `select-detail` data_sety (`WHERE z.id = :master_id`). Otevření z přehledu = `edit` op na přehledu s `core_id` = jádro.

---

## 4. ⚠️ Klíčové framework „gotchas" (ať to nemusíš objevovat znovu)
1. **`fw.core/comp_def/menu_node.id` = GENERATED ALWAYS identity** → nevkládat id ručně, používat `RETURNING id`.
2. **Bridge (SQLAlchemy) bere `:slovo` i `:číslo` jako bind param** i uvnitř stringů/JSONu. Pro literál `:master_id` v uloženém SQL použij `... || chr(58) || 'master_id'`; pro JSON `layout` použij `jsonb_build_object(...)` (ne string s `"height_px":320`).
3. **`comp_def` constraint `chk_comp_def_single_parent`**: root (top‑level) má `root NOT NULL` a `parent_comp_def_id NULL`; **child má `root NULL` a `parent` vyplněný** (nedávat root=0!).
4. **Záznam jádra se načte jen když `edit` op má `core_id`** (resolver `_resolve_entity_config_from_db` hledá `op.core_id = <core>`). Bez toho prázdná pole.
5. **Vnořený grid (101) potřebuje `layout` s `kind:"select-detail"` + `filter_field:"master_id"` + `data_source_code`** — jinak frontend nepředá master_id a grid je prázdný.
6. **Schéma `ec` musí mít grant pro aplikační roli `strategie`** (USAGE/SELECT/INSERT/UPDATE/DELETE/EXECUTE/sekvence) — jinak přehled i jádro nevidí data.

---

## 5. Ověření 1:1 (VR10704)
Sedláčková 320 · Navrátil 195 · Bláha 40 · **PremieCelkem 555** = přesná shoda s printscreenem Centrály.
Hlavička: Kalkulováno 7 · Odpracováno 2,79 · Limit 8,05 · Ušetřeno 4,21 · Celkem s prémiemi 1113 · Plánováno 1330 · Sazba prémie 130 · Sazba srážka 30 · Rezerva 1,15.
Uzávěrka: SuperHrubá výplaty **774 / 469 / 92** (mzda + PremieFinal × 1,4). Zrušit: archiv 3 + reopen.

---

## 6. Co zbývá doladit (pro Jirku)
- **„Hodnotit společné"** na přehledu — multi‑select řádků → `ec.slouci_zakazky(zaks[])`. Endpoint připravený (`action_code:"slouci"`), chybí tlačítko/multi‑select na přehledu.
- **Napojení reálného zdroje hodin/mezd** (`ec.dochazka.kc_celkem`, `cascelkemzakazka`) na produkční docházku — teď jsou v `ec` jen testovací data VR10704.
- **Kvalita** (Flexibilita / Chybovost / Estetika) + poznámky VV/VP/šéfmontér — editace v gridu „Hodnocení vše" (přidat CRUD op / inline edit).
- **Read‑only počítaná pole** v jádru (teď jsou editovatelná — jen nástřel).
- **Viditelnost uzlu** — „🏭 Výroba" i „Zakázky k vyhodnocení" mají `visibility_scope='private'` (jen admin). Pro Dušana (vedoucí výroby) nastavit vhodný scope.
- **`nastav_sefmontera` / `nastav_multif`** — napojit na akci řádku gridu (toggle šéfmontér / nepodepsaný ZL).
- **Efektivita‑weighted odpracováno** ve `vypocet_konstant` — v originálu je drobná nejednoznačnost (SUM sloupce se stejným názvem); portováno věrně, ale při doladění ověřit na víc zakázkách.

---

### Reference (kód/DB)
- Backend port: PG schéma `ec` (funkce + tabulky). Akční endpoint: `modules/erp/api/vyhodnoceni_actions.py`. FE: `apps/api/static/erp/components/ec_vyhodnoceni_actions.js`.
- UI: `fw.core` 199 (přehled) + 203 (jádro), `fw.comp_def` strom, `fw.data_source`/`_op`/`data_set` `ec.vyhodnoceni_*`.
- Zdroj procedur: DB_EC `dbo.EC_Zakazky_Vyhodnoceni_*` (přes EUROSOFT MCP).


