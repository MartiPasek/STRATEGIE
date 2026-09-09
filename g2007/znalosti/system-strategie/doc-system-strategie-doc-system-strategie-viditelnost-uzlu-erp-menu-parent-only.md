# Doc system strategie viditelnost uzlu erp menu parent only

> ⛔ **TATO ZNALOST UŽ NEPLATÍ — stav `zruseno`.** Neřiď se jí a necituj ji. Zůstává tu jen kvůli historii; zdroj pravdy je databáze `g2007.znalost`.

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `zruseno` · rozsah: globální (všichni tenanti)

**Viditelnost uzlu ERP menu — hodnoty parent_only/restricted/private/scoped; název parent_only klame, scoped je jen 1 uživatel.**

# Viditelnost uzlu ERP menu — `parent_only` a spol.

> Navigační kotva. Kanonický popis mechaniky je v **[[doc-mzdy-priplatky-srazky]]** (oblast mzdy), sekce o `_build_system_root_from_db`. Sem nechoď pro detail implementace — jdi tam.

## Hodnoty `visibility` / `parent_only` (stav září 2026)

| Hodnota | Počet uzlů | Kdo vidí |
|---|---|---|
| `parent_only` | 91 | Pouze rodiče (`is_marti_parent`) |
| *(NULL / prázdno)* | 49 | Všichni (veřejný uzel) |
| `restricted` | 20 | Jen uživatelé ve `visibility_user_ids` + kaskáda předků |
| `private` | 16 | Vlastník + kaskáda předků |
| `scoped` (user) | 41 | Dnes jen **Dušan Havlát** (UID 41) |

## ⚠️ Klíčová gotcha — název `parent_only` klame

`parent_only` **neznamená „jen pro rodiče"** ve smyslu oprávnění — jde o specifický visibility tier. Název je historický artefakt. Claude-28 (Jirka) tuto pasti narazil 9. 9. 2026 a nahlásil ji.

Mechanika ověřena v kódu `router.py → _build_system_root_from_db`:
- `parent_only` / `NULL` → vidí **všichni**
- `private` / `restricted` → jen lidé ve `visibility_user_ids` plus kaskáda předků
- Rodič vidí vše (bypass)

*(Citát z doc-mzdy-priplatky-srazky, rozhodnutí Jirky Honomichl 22. 7. 2026)*

## Scoped uživatel

Mechanismus `scoped` byl opraven Claudem-25 a Šárkou 7. 7. 2026. Dnes je takto nastaven jediný uživatel: **Dušan Havlát** (UID 41 v datech menu_node).

## Kde hledat více

- **[[doc-mzdy-priplatky-srazky]]** — kanonický popis implementace (první místo, kde to bylo zdokumentováno)
- **[[doc-system-g2007-phase38-4-framework-doctrine]]** — starý návrhový dokument fáze 38.4, popisuje hodnoty `tenant_member`/`public`/`parent_or_admin` které v datech **nejsou** — je to historický design doc, ne live popis

_Souvisí:_ doc-mzdy-priplatky-srazky, doc-system-g2007-phase38-4-framework-doctrine

