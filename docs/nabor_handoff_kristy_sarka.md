# Nábor — předávka Šárce + Kristý (Claude‑24)

Stav k 13. 6. 2026 (od Claude‑23). Marti: „ještě to nesedí, nechme to na holky."

## Kde to je
- Appka → **Vedení firmy → 🧲 Nábor** (pipeline) + **Skupiny/HR → Nábor**.
- Data: `tenant.recruit_candidate` (1 836) + `tenant.recruit_application` (1 867),
  migrováno z DB_EC `ec_jednani` WHERE `Kategorie=901`. Hodnocení se nemigruje
  (Marti‑AI Q1). Anonymizace po lhůtě = ops `recruit_anonymize` (GDPR Q4).

## Co je hotové (a drží i na příští sync)
Příznak otevřenosti v EC = **`Stav`** (O = otevřeno, U = uzavřeno, NULL = staré).
Pravidlo v `_sync_nabor_from_ec`:
- aktivní fáze (Ve hře / 1. kolo / 2. kolo) **bez `Stav='O'`** → archiv (**mimo hru**),
- `Stav='O'` bez fáze → **Ve hře**,
- `nástup` = přijatí, `mimo hru` = archiv (beze změny).

**Výsledek teď:** ve hře **60** (47 + 10 + 3), nástup 139, mimo hru 984, historické 684.

## Co „nesedí" (na doladění — Šárka ví nejlíp)
Reálně otevřených bude nejspíš **míň než 60** — část `Stav='O'` jsou staré
nedouzavřené záznamy. Možné cesty:
1. **Šárka projde 60 „ve hře"** v appce a co není živé, klikne „mimo hru" (in‑app,
   bez DB zásahu) — nejčistší, ona zná pravdu.
2. **Jemnější pravidlo** (Claude‑24): přidat časový filtr — např. `Stav='O'`
   **a** `DatumJednaniOd`/`DatPorizeni` za poslední ~rok; starší O = archiv.
   (Sloupce v `ec_jednani`: `DatumJednaniOd`, `DatPorizeni`, `DatZmeny`.)
3. Nový nábor půjde rovnou správně (zakládá se s `Stav='O'`).

## Pro Claude‑24
- Re‑sync: ops **`sync_nabor`** (přepíše migrované řádky, drží pravidlo výše).
- Bridge read na EC: `db=mssql`, tabulka `ec_jednani` (Kategorie 901), klíč `ID`
  ↔ `recruit_application.ec_jednani_id`. Stav uložen v `recruit_application.status`.
- Časový filtr přidat do `_sync_nabor_from_ec` (modules/erp/api/router.py) k pravidlu
  fáze/stav. Pak `sync_nabor` + ověřit pipeline.

Předáno s důvěrou — holky to dotáhnou. 🌳
— Claude (id 23)
