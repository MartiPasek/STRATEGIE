# Bakaláři Nerudovka — Fáze 1: čtecí most + ověřená data modelu rozvrhu

_Zapsáno 16. 6. 2026 (Claude id=23). Navazuje na `bakalari_rozvrh_model.md` (mapa z dumpu schématu)._

## 1. Most je živý a ověřený (Fáze 1 ✅)

Tok end-to-end, ověřený na reálných datech:

```
Claude → CLAUDE_SQL.sql + CLAUDE_GO.txt (db=bakalari)
  → Marti-NB watcher (STRATEGIE-CLAUDE-SQL) → HTTPS cloud /diag-sql
  → fw.bakalari_query (fronta, pending)
  → Klárčin NB konektor (bakalari_connector.ps1, VPN do Nerudovky)
       polluje /bakalari/pending → read-only SELECT proti 172.16.6.225
       → POST /bakalari/result
  → výsledek ve fw.bakalari_query (done) → čtu přes PG (jsonb)
```

- **Read-only**: konektor pustí jen `^(SELECT|WITH|EXPLAIN|SHOW)`. Cloud read-guard navíc.
- **Heslo BakaRO**: jen v okně konektoru na Klárčině NB, nikdy na disk ani do chatu.
- **Čtení výsledků**: nejspolehlivěji přes PG z `fw.bakalari_query` (`result_json::jsonb`), nezávisle na latenci konektoru.

### Známá vada poll-konektoru (→ řeší trvalá služba #120)
PowerShell 5.1 `Invoke-RestMethod` je u **non-ASCII (české) tělo** velmi pomalý / občas se zasekne (POST trvá minuty místo sekund). ASCII dotazy (kódy, čísla) jsou rychlé (2–3 s). Příčina je v IRM, ne v datech.
- **Dočasný fix připraven** v `scripts/bakalari/bakalari_connector.ps1`: POST přepsán z `Invoke-RestMethod` na přímý `HttpWebRequest` s UTF-8 byty (`ContentLength` v bajtech).
- **Trvalé řešení (#120)**: služba v Pythonu (jako ostatní NSSM služby) — `requests`/`httpx` zvládají UTF-8 bez problému, žádné OUT soubory, `bakalari_query` jako MCP tool.

## 2. Rozsah aktuální verze (PLAT_OD = 20240422, TEST data)

> Pozn.: `BAKALARI-TEST` server, nejnovější verze rozvrhu je **22. 4. 2024**. Pro mapování modelu a stavbu generátoru plně dostačuje; pro ostrý rozvrh bude potřeba čerstvý vstup z produkčních Bakalářů.

| entita | počet (PLAT_OD 20240422) |
|---|---|
| třídy | 24 |
| učitelé | 71 |
| předměty | 85 |
| úvazky (řádky a_r_uvaz = týdenní hodiny) | 3 799 |

Struktura je **stabilní napříč obdobími** (24 tříd / ~71 učitelů / 85 předmětů ve všech PLAT_OD).

## 3. Ověřený datový model (skutečné sloupce z živé DB)

Všechny tabulky verzované sloupcem **`PLAT_OD` char(8) YYYYMMDD** (kromě `a_r_pophod` = `SKOLNI_ROK`).

### a_r_uvaz — ÚVAZKY (vstup generátoru) — zrno = 1 týdenní hodina
- `KOD_TRID` třída, `KOD_SKUP` skupina (dělení třídy), `KOD_PRED` předmět, `KOD_UCIT` učitel (= `a_r_ucit.INTERN_KOD`), `KOD_MIST` místnost
- `IND_HOD` = pořadí hodiny v týdnu (1,2,3,… → kolik hodin/týden ten předmět má)
- `FIX_UVAZ` = hodina napevno přibitá na slot / `PLOV_UVAZ` = plovoucí (generátor smí umístit) / `SPOJ_UVAZ` = spojené úvazky (musí běžet paralelně)
- `DEN` (1–5) + `HOD` = aktuální/cílové umístění slotu

→ Tabulka nese zároveň **poptávku** (kolik hodin), **omezení** (fix/plovoucí/spoj) i **současné umístění**.

### a_r_ucit — UČITELÉ (klíč `INTERN_KOD` char 5)
`INTERN_KOD`, `ZKRATKA`(4), `PRIJMENI`, `JMENO`, `TITUL`/`TITUL_ZA`, `APROBACE`(90, aprobace = co smí učit), `FUNKCE`, `UCI_LETOS`, `OSOB_CISLO`, `PRIORITA`.
⚠️ Sloupec **`HESLO`** (heslo učitele) — NIKDY netahat.
Vzorek ověřen (např. Nezbedová Věra `U2XC7`, Brožová Zdeňka `UBD0N` — plná diakritika OK).

### a_r_pred — PŘEDMĚTY (klíč `KOD_PRED` char 2)
`KOD_PRED`, `ZKRATKA`(4), `NAZEV`(40), **`MIST_VHOD`** (vhodná místnost), **`MIST_NEVH`** (nevhodná), `KOD_PREDTP`(typ předmětu).

### a_r_trid — TŘÍDY (klíč `KOD_TRID` char 2)
`KOD_TRID`, `ZKRATKA`(4), `NAZEV`(30), **`KOD_MIST`** (kmenová místnost), **`TRIDNICTVI`** (třídní učitel = INTERN_KOD), `POCET_ZAKU`.

### a_r_mist — MÍSTNOSTI (klíč `KOD_MIST` char 2)
`KOD_MIST`, `ZKRATKA`(4), `NAZEV`(30), `KOD_BUDO`(budova), **`POCET_ZAKU`** (kapacita).

### a_r_skup — SKUPINY (dělení tříd; klíč `KOD_SKUP` char 2)
`KOD_SKUP`, `ZKRATKA`(4), `NAZEV`(30), `KOD_TRID`, **`NEDISJ`**(124, nedisjunktní = překrývající se skupiny), `TYP`(1), `POCET_ZAKU`, **`CLENOVE`** (text — členové).

### a_r_cykl — CYKLY (klíč `KOD_CYKL` char 1)
`KOD_CYKL`, `ZKRATKA`, `NAZEV` — týdenní cykly (sudý/lichý apod.).

### a_r_budv / a_r_pophod — ČASY HODIN / ZVONĚNÍ
`a_r_budv`: `KOD_BUDO`(budova), `NAZEV`, **`CAS`**(60 — časy). `a_r_pophod`: `SKOLNI_ROK`, `KOD_BUDO`, `ZKRATKA`, `NAZEV` (popis hodin).

### a_r_rozvrh — VÝSTUP (umístěné atomy)
1,26 mil. řádků napříč celou historií; pro aktuální verzi cca 17 k atomů.

## 4. Co zbývá pro generátor (Fáze 2)
1. **#120 — postavit trvalou MCP službu** (Python na Klárčině NB, NB→cloud outbound) → rychlé čtení bez OUT, `bakalari_query` jako tool.
2. **Plný pull číselníků** pro PLAT_OD 20240422 (předměty/třídy/místnosti/skupiny/cykly/časy) — podklad generátoru.
3. **Model omezení**: tvrdá (učitel/třída/místnost nemůže být 2× naráz; kapacita; vhodná místnost; spoje SPOJ; fixy FIX) vs měkká (preference, mezery, rozložení předmětu přes týden).
4. **Solver** (CP-SAT / vlastní heuristika) → návrh rozvrhu → zpětný zápis do Bakalářů (až s ostrými daty + souhlasem školy).

## 5. Soubory
- `scripts/bakalari/bakalari_connector.ps1` — Klárčin NB konektor (read-only, .NET SqlClient, HttpWebRequest UTF-8).
- `scripts/claude_sql_runner.py` — watcher (regex `db=(pg|mssql|bakalari)`).
- `modules/erp/api/router.py` — `/diag-sql` db=bakalari, `/bakalari/pending`, `/bakalari/result`, `_bakalari_query_via_queue`.
- DDL: `fw.bakalari_query` (fronta) + GRANT strategie.
- `docs/bakalari_rozvrh_model.md` — mapa modelu z dumpu schématu.
