# Kalkulace rozváděčů — Vize 1 (náš engine = zdroj pravdy) + systém Velkých ceníků

> **Zapsáno: Claude ID23, 18. 7. 2026, po konzultaci s Marti.** Zásadní směrové rozhodnutí
> ke kalkulačnímu enginu + inventura reálného stavu ceníkového systému na Cloudu.

## 1. CÍL = Vize 1: náš engine se stane zdrojem pravdy MÍSTO Excelu

Marti (18. 7.): *„Naším cílem je si v tom mém původním 2014 enginu schránkovat kalkulace
jednotlivých zákazníků, koeficienty těch dílů a **zejména aktuální ověřené nákupní ceny**
a dělat si zdroj pravdy namísto Excelu tak v našem enginu."*

Náš engine (model z DB_EC 2014, zrcadlený do `tenant.kalk_*`) má držet a udržovat tři pilíře:
1. **Per‑zákazník kalkulace / sestavy / rabaty** (STANDARD per CisloOrg) — už z velké části máme (141 skupin / 1675 položek, rabaty per CisloOrg).
2. **Koeficienty dílů** (K_VKM + K_ARB → VKM/Arbeit) — už máme bohatě (3676 dílů, jádro know‑how).
3. **⭐ Zejména AKTUÁLNÍ OVĚŘENÉ NÁKUPNÍ CENY** — to je základní kámen, na kterém stojí důvěryhodnost celého enginu. Musí být čerstvé a ověřené, ne jednorázově zrcadlené.

**Vize 2 (dočasná, Marti ji „moc nemá rád, ale cesta to je"):** nechat pravdu v konkrétních
Excelech a čárkovat (nastavovat množství) přímo do nich, jak to lidi dělají dnes. Berlička,
nestaví aktivum, drží nás na Excelu. → Jdeme **Vize 1.**

## 2. Jak to teče DNES (Marti: „funguje to obráceně, vzhůru nohama")

**Zdroj pravdy dnes = LIDI v EXCELU.** Kalkulují v konkrétních Excelech s živými cenami,
ceníky a nákupkami. Když dokalkulují, **použité řádky z Excelu se IMPORTUJÍ do DB → tabulka
`EC_KalkulacePolozky`** (235 637 ř.). Čili DB dnes **NENÍ** cenová databáze, kterou udržujeme —
je to **sběrné místo hotových kalkulací** (výstup Excelu). Vize 1 = tenhle vztah OTOČIT.

`EC_KalkulacePolozky` nese na řádku vše (import z Excelu): `RegCis`, `Bezeichnung`,
`IDHlav`→`EC_KalkulaceHlav` (CisloKalkulace EK…, globální VKM/Arbeit/Koeffizient/MarzeProcent),
`PocetKusu`, `JCenaEUR` (CC/Einheitspreis), `RabatP`/`RabatN`, `K_VKM`/`K_ARB`, **`NC_Posledni`
= poslední nákupka**, `PC_Cenik`/`NC_Cenik`/`IDCenik` = z platného ceníku, hotové:
`EinheitpreisPoSleve`/`GesamtPreis`/`VKM`/`Arbeit`/`Marze`/`Hmotnost`, `IndArchiv`, `ChybaCeny`.

⚠️ Cloud zrcadlo `tenant.ec_kalkulace_polozka` nese jen PODMNOŽINU (pro objednávky):
src_id, id_hlav, id_kmen_zbozi, jcena_eur, kcen_cena, dodavatel, objednej… — **NE** rabaty/koef/
NC_Posledni/ceník. Ty jsou jen v DB_EC `EC_KalkulacePolozky` → staging odtud musí číst z DB_EC (MCP).

## 3. ⭐ PRAVIDLO NÁKUPNÍ CENY (Marti 18. 7.)

- **Věříme cenám dodavatelů, od kterých kupujeme → poslední nákupní cena z faktury.**
- ALE: kvůli **každoročnímu zdražování dílů** se slepá důvěra v poslední nákupku nevyplácí.
- Proto máme **„Velké ceníky" = `EC_Ceniky`** (dodavatelské ceníky) jako korekční/ověřovací vrstvu.
- Model tedy: **poslední skutečně zaplacená nákupka z faktury, korigovaná/ověřená proti platnému Velkému ceníku dodavatele.**

## 4. Velké ceníky — systém a REÁLNÝ stav na Cloudu (k 18. 7. 2026)

Ceníky už jsou **dotažené z EUROSOFTu na náš Cloud** (dřív MSSQL `DB-Ceniky`, teď u nás v PG).
Návrh: `docs/Z_ceniky_system_navrh.md`. Kód: **`modules/erp/api/cenik_engine.py`** + dispatch
`@@CENIK` v `router.py`.

**Tabulky (PG, tenant_id=2):**
- `tenant.cenik_import` — hlavička per dodavatelský XLS (vyrobce, mena, platnost_od/do, zdroj_soubor, mapovani, pocet_polozek, zpracovano).
- `tenant.cenik_polozka` — řádky: `raw` (jsonb syrové sloupce) + normalizovaná pole: `kat_kod`, **`kat_kod_norm`** (párovací klíč = bez mezer, velká písmena), `popis`, `list_price` (EC_PC = ceníková), `net_price` (EC_NC = nákupní/netto), `rabat`, `mj`, `ean`, `hmotnost_kg`, `mena`.
- `tenant.ec_cenik_*` (hlav/vzorec/vzorec_default/vzorec_par/nastaveni) — zrcadlo **vzorcového** systému z DB‑Ceniky.

**Vzorcový engine (Martiho @P styl):** `cenik_engine.py` má BEZPEČNÝ evaluátor výrazů (bez
dynamického SQL) — `@Pnn` parametry (syrové XLS sloupce) → funkce SUBSTRING/LEFT/RIGHT/REPLACE/
CAST/CONCAT/… → normalizovaná pole. Každý dodavatel má jinou strukturu XLS → sada vzorců per výrobce
(`RegCisHeo = 'EAT ' + SUBSTRING(@P13,1,3)…`, `EC_NC = @P05/@P04`).

**Příkazy `@@CENIK`:** `PEEK <xls>` (náhled layoutu), `IMPORT <vyrobce> [cesta]` (import XLS na
pozadí), `SETMAP <vyrobce> P01=1,…` (override mapování + reimport), `MIGRATE1`/`MIGRATEALL`
(přenos vzorců z DB‑Ceniky + import), `FIND <kat_kod>` (→ `find_price`), `DEDUP`, **`MEDI`**
(cena mědi — komoditní vstup pro kabely/přípojnice: SYNC/LIST/ADD).

**Dohledávka ceny:** `find_price(kat_kod)` → `WHERE kat_kod_norm = norm(vstup)` proti **NEJNOVĚJŠÍMU
importu per dodavatel** (`max(id) per vyrobce`) → vrací `net_price`/`list_price`/rabat/mena/vyrobce.

**Zdroj XLS:** `D:\Data\ZZ_Marti-AI RW\Ceniky\` (17 XLSX + PrevodniTabulka.xlsx), názvy
`<Výrobce>_…platný od <datum>_JV_<datum>.xlsx`. Udržuje JV v EUROSOFTu.

**STAV DAT (ověřeno 18. 7.): 11 dodavatelů, ~540 tis. položek:**
EAT 32 291 · FIN 1 399 · HAR 456 · LAP 21 887 · MUR 57 898 · PHO 46 866 · RIT 4 617 ·
SCH 31 252 · **SIE 261 385** · WAG 30 366 · WEI 51 042.

## 5. 🔴 ODHALENÝ LINCHPIN: párování BOM ↔ ceník je NEVYŘEŠENÉ

Test 18. 7.: 18 dílů Absaugwerk BOMu (5SY4110‑6, 3RV2031‑4PA10, 6ED1052‑1MD08‑0BA2, …) proti
Velkým ceníkům přes `find_price` → **0 z 18 nacenění**, přestože Siemens má 261 385 řádků.
Příčina: `kat_kod_norm` v ceníku **neodpovídá syrovému objednacímu číslu** z BOMu — ceník má kód
v jiné podobě (nejspíš s prefixem dodavatele / jinou segmentací `RegCisHeo`, nebo se musí projít
přes **`PrevodniTabulka`** = mapování dodavatel kód ↔ interní komponenta). **Mít ceníky nestačí —
musí se umět napárovat na díl.** Tohle je klíč Vize 1 (a auto‑kalkulace SRDCE FIRMY).

## 6. Absaugwerk engine (kontext) — stav

`modules/erp/api/kalkulace_engine.py`: profily **FLEX+** (EK262940, src_id 9135) a **SMART NASS**
(EK263380, src_id 9182), příkaz `@@KALKABS profil=flex kw=15 | REGCIS*QTY, …` (commit bd5c3781).
Výpočet (koef→VKM/Arbeit, marže, floor per kW, fix přirážky) běží; **materiál se necení**,
protože (a) 2014 baseline díly nemá, (b) párování na ceník je rozbité (§5). 2014 baseline `tenant.kalk_*`
= HISTORIE, přestat používat jako zdroj (Marti 18. 7.).

## 7. Plán Vize 1 (návrh)

1. **Vyřešit párování** díl ↔ ceník (PrevodniTabulka / RegCisHeo transform / kat_kod_norm sjednocení). Bez toho nic dalšího nefunguje.
2. **Cenový zdroj pravdy** per díl: poslední nákupka z faktury (zdroj v DB_EC — kandidát `NC_Posledni` / nákupní doklady, doověřit), **korekce/ověření platným Velkým ceníkem** (`find_price` net_price). Flag rozporu (stará cena / mimo ceník / zdražení).
3. **Napojit `find_price` (+ nákupku) do `compute()`** jako materiálovou cenu místo 2014 `kalk_cena`.
4. **Per‑zákazník** sestavy + rabaty z jejich historie; koeficienty už máme.
5. **Validace:** GESAMT enginu proti skutečné ceně reálných kalkulací EK262940 / EK263380.

## Odkazy
- Kód: `modules/erp/api/kalkulace_engine.py`, `modules/erp/api/cenik_engine.py`, `@@KALK*`/`@@CENIK*` v `router.py`.
- Doc: `docs/Z_Kalkulacni_engine_DB_EC_2014.md`, `docs/Z_Kalkulace_standard_struktura.md`, `docs/Z_ceniky_system_navrh.md`, `docs/Z_srdce_firmy_kalkulace_nabidky_analyza.md`.
