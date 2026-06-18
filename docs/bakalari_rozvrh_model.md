# Bakaláři — datový model rozvrhu (Nerudovka) — mapa pro tvorbu rozvrhu

Zdroj: read-only průzkum `bakalari_schema_dump.txt` (16. 6. 2026, BAKALARI-TEST 172.16.6.225,
DB `bakalari`, ~623 tabulek). Rozvrhové jádro je ve schématu `dbo` s prefixy
**`a_r_*`** (rozvrh) a **`a_s_*`** (suplování). Vše klíčované krátkými kódy + `PLAT_OD`
(platnost od, char(8) = RRRRMMDD). Den = `DEN`, hodina = `HOD`.

## Číselníky (master data — vstupy)

| Tabulka | Co | Klíč | Důležité sloupce |
|---|---|---|---|
| `a_r_ucit` | Učitelé | `INTERN_KOD` (5) | ZKRATKA, PRIJMENI, JMENO, TITUL, **APROBACE** (co smí učit), UCI_LETOS, PRIORITA, OSOB_CISLO |
| `a_r_pred` | Předměty | `KOD_PRED` (2) | ZKRATKA, NAZEV, MIST_VHOD/MIST_NEVH (vhodné/nevhodné místnosti), KOD_PREDTP |
| `a_r_trid` | Třídy | `KOD_TRID` (2) | ZKRATKA, NAZEV, **KOD_MIST** (kmenová učebna), **TRIDNICTVI** (třídní), POCET_ZAKU |
| `a_r_mist` | Místnosti | `KOD_MIST` (2) | ZKRATKA, NAZEV, KOD_BUDO (budova), **POCET_ZAKU** (kapacita), PRIORITA |
| `a_r_skup` | Skupiny | `KOD_SKUP` (2) | ZKRATKA, KOD_TRID, **NEDISJ** (nedisjunktní = překryv skupin), POCET_ZAKU, TYP, CLENOVE |
| `a_r_budv` | Budovy | `KOD_BUDO` (2) | ZKRATKA, NAZEV, CAS (časový posun zvonění) |
| `a_r_cykl` | Cykly (týden A/B/…) | `KOD_CYKL` (1) | ZKRATKA, NAZEV |
| `a_r_pophod` | Popis hodin (zvonění) | `KOD_BUDO`+poradí | časové úseky vyučovacích hodin per budova |
| `a_r_hudruh` | Druhy hodin | `KOD_TYP` | barva, priorita |
| `a_r_bldruh`/`a_r_blhod` | Bloky (dvouhodinovky…) | `KOD_BLOK` | DEN, HOD, BEGIN/END_TIME |
| `a_r_mnmi` | Množiny místností | `KOD_MN_MI` | MISTNOSTI (seznam) |
| `a_r_SubSubject` | Pod-předměty | `Code` | SubjectCode |
| `a_r_dohled` | Dozory | — | DATE/HOUR/OBJ |

## Jádro — VSTUP a VÝSTUP

### `a_r_uvaz` — ÚVAZKY (VSTUP pro tvorbu rozvrhu)
Kdo má co učit, kolik hodin, které třídě/skupině, kde — + omezení.
- `KOD_UVAZ` (5) — kód úvazku
- `IND_HOD` — počet hodin (týdně) k naplánování
- `KOD_TRID` + `KOD_SKUP` + `KOD_PRED` + `KOD_UCIT` + `KOD_MIST` — koho/co/komu/kde
- `KOD_MNCYKL`/`KOD_PLCYKL` — množina/plán cyklů
- `SPOJ_UVAZ` (6) — spojené úvazky (učí se společně), `SPOJ_NASZ`
- `FIX_UVAZ` / `PLOV_UVAZ` — fixní (pevně daná hodina) vs plovoucí
- `DEN`/`HOD` — pokud fixní, kdy
- `SUBSUBJECT`, `minuty`, `zacatek`

### `a_r_rozvrh` — VÝSLEDNÝ ROZVRH (VÝSTUP)
Umístěné hodiny (atomy): co se kdy/kde/kým učí.
- `DEN` (char(8) nebo den v týdnu), `HOD` — pozice
- `KOD_TRID`, `KOD_SKUP`, `KOD_PRED`, `KOD_UCIT`, `KOD_MIST`, `KOD_CYKL`
- `SPOJ_UVAZ` — vazba na úvazek, `OZNC_HODU`, `minuty`, `zacatek`, `PLAT_OD`

### Suplování (`a_s_*`)
`a_s_rozvrh`, `a_s_uvaz`, `a_s_hoduc`, `a_s_obdobi`, `a_s_dohled`, `a_s_plzmen`… —
denní změny/suplování nad rozvrhem (pro pozdější fázi, ne pro generování).

## Tvorba rozvrhu = constraint problem
**Vstup:** úvazky (`a_r_uvaz`, IND_HOD hodin) × číselníky.
**Výstup:** naplnit `a_r_rozvrh` (DEN×HOD×CYKL pro každou hodinu úvazku).
**Tvrdá omezení:** žádná kolize učitele / třídy / skupiny (mimo NEDISJ) / místnosti v tomtéž
DEN+HOD+CYKL; kapacita místnosti ≥ POCET_ZAKU; aprobace učitele; fixní úvazky na své pozici;
spojené úvazky (`SPOJ_UVAZ`) ve stejném slotu; vhodné/nevhodné místnosti předmětu.
**Měkká omezení:** mezery v rozvrhu učitele/třídy, max hodin/den, dopolední preference,
rozložení předmětu přes týden, kmenová učebna třídy.

## Postup (fáze)
- **Fáze 0 — HOTOVO**: read-only průzkum schématu (tento dokument).
- **Fáze 1**: živý čtecí most (konektor na NB s VPN → cloud → Marti-AI `bakalari_query_raw`).
  Pak číst úvazky + číselníky přímo a průběžně.
- **Fáze 2**: generátor rozvrhu (constraint solver) nad úvazky → návrh `a_r_rozvrh` + kontrola
  kolizí + ruční úpravy. Zápis zpět do Bakalářů AŽ po dohodě (zatím jen read; návrh držíme u nás).
- **Vize**: postupně celá digitalizace školy nad týmiž daty (přehledy, automatizace) jako další
  „tenant" STRATEGIE.

## Pozn. k bezpečnosti / přístupu
- Účet `BakaRO` = read-only. Heslo jen v konektoru na NB (env), nikdy v kódu/chatu/repu.
- Server je vnitřní (172.16.6.225); dosažitelný jen přes VPN na Klárčině NB.
- Zápis do Bakalářů (vložení hotového rozvrhu) = samostatné rozhodnutí, ne součást čtecí fáze.
