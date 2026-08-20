# proj.kalk_kmen (katalog dilu Kristy+C24, 1749 dilu) - nalezen a analyzovan 2.8.2026. DULEZITE: existujici compute()/@@KALKABS je rozbity (spatne schema), compute_absv1()/@@KALKABSV1 tenhle katalog vubec nepouziva

> oblast: `kalkulace-rozvadecu` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

**Kontext:** Marti 2.8.2026 upozornil, ze v PG existuji nove tabulky pro kalkulovani (katalog dilu a ceniky), ktere delala Kristy s C24 - pozadal me je prozkoumat a analyzovat jako zaklad pro kalkulovani.

## Co to je (nalezeno, overeno primo v DB a gitu)

`scripts/kalk_kmen_standard_load.py` (C24/Kristy, commity 23.-24.7.2026) je loader, ktery parsuje master referencni "STANDARD" excel sesit (`K260XXXXStandSiem_Zakaznik_Nazev_xxx_260107.xlsm`, listy: Zakladni 2026 > Rozsireni 2025 > ICOTEK 2025 > Sinovy system > UL508A > Sie Schraube > Siemens 3SU1+ Metall, v tomto poradi priority pri dedupu) a naplnuje `proj.kalk_kmen`. Kazdy radek = jeden dil (`reg_cis`, uz ve tvaru PREFIX+cislo jako "RIT 8206000") s: `vyrobce`, `oznaceni`, `k_vkm`/`k_arb` (koeficient - v tomhle zdroji STEJNA hodnota pro oba, sloupec H "Koeffiz."), `cena_cc_ref` (cenikova), `cena_nc_ref` (po rabatu), `rabatt_ref` (%), + puvod (excel_soubor/list/radek/pozice).

**Overeno primo:** 1749 dilu, naposledy synced 24.7.2026 08:51. Priklad radku: `RIT 8206000 | Rittal | VX Schaltschrank 1200x2000x600 (195kg) | k_vkm=1.0 k_arb=1.0 | cena_cc=803.0 cena_nc=923.45 rabatt=14%`. Loader je idempotentni (ON CONFLICT DO NOTHING pri append) a ma i --rebuild rezim. Tohle JE ta "knihovna koeficientu" popsana v #37 jako dusevni vlastnictvi firmy - real, cerstva, ne 2014 baseline.

## KRITICKY NALEZ: tenhle katalog dnes NEPOUZIVA ZADNY funkcni vypocet

Overeno primo v kodu `kalkulace_engine.py`:
- **`compute()`/`compute_profile()`/`@@KALKABS`** (puvodni cesta) cte z `tenant.kalk_kmen`/`tenant.kalk_cena`/`tenant.kalk_rabat`/`tenant.kalk_koef` (`_resolve_item()`, radek 336+). ALE tyhle tabulky **UZ NEEXISTUJI** - byly presunuty do schematu `proj` (commit `df8e66c9f`, 22.7. 21:18, "presun cenik_* do schematu proj" - presunulo zjevne vic nez jen cenik_*). Kod na to nebyl aktualizovan. **`@@KALKABS`/`compute()` je tedy dnes rozbity** (spadne na `UndefinedTable`).
- **`compute_absv1()`/`@@KALKABSV1`** (novejsi, "GESAMT zevnitr") tohle nezasahuje - bezi, ale material bere z `price_bom()` (`proj.cenik_polozka`, Velke ceniky) + koeficienty z **`_coef_ec()`, ktera cte primo DB_EC `EC_KalkKoeficienty` pres MSSQL** (live, ne PG). **Nepouziva `proj.kalk_kmen` vubec.**

Jinymi slovy: mame TRI castecne prekryvajici se zdroje materialu/koeficientu (2014 DB_EC live pres MCP, Velke ceniky 539k polozek, a cerstvy STANDARD katalog 1749 dilu od Kristy+C24) a ZADNY z nich dnes neni spojeny se vsemi ostatnimi do jedne funkcni cesty, ktera by pouzivala prave ten nejcerstvejsi/nejcistsi zdroj (`proj.kalk_kmen`).

## Co jeste chybi k rucnimu/AI proведeni kalkulace (2.8., podle Martiho popisu)

1. **SMART**: Marti popsal Excel s ~11 listy, kazdy list = jeden JIZ NAKALKULOVANY SMART rozvadec podle vykonu (kW). Tohle NENI totez jako STANDARD katalog dilu vyse (ten je katalog KOMPONENT, ne hotovych kalkulaci). Tenhle SMART soubor jsem v gitu/DB nenasel ani nezmineny - zrejme zije jen lokalne na Martiho/Elisce pocitaci, mimo pripojenou slozku STRATEGIE (mount ma jen /mnt/STRATEGIE, zadna slozka s referencnimi Excely jako u ceniku "D:\Data\ZZ_Marti-AI RW\").
2. **FLEX**: per objednavka - EPLAN nejdriv, pak Zdenek Cepicky preda Elisce PDF (s kusovnikem) + Excel (s kusovnikem). Realny priklad uz mame zminen v #37 (EK262940), ale samotny soubor take nedohledatelny v pripojenych slozkach.

**-> Potreba od Martiho: dodat/zpristupnit oba soubory (SMART 11-listovy Excel + jeden realny FLEX PDF+Excel kusovnik priklad), abych mohl kalkulaci provest rucne/krok za krokem a napsat znalostni dokument z prvni ruky.**

_Zapsano Claude-23, 2.8.2026. Navazuje na #37, #107, #147, #316._

