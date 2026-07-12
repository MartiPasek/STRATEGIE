# Plán obnovy provozu — pokyny pro Michala (vyzkoušet a rozjet)

> oblast: `iso27001` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Plán obnovy provozu — pokyny pro Michala (vyzkoušet a rozjet)

> **Verze:** 1.0 · **Datum:** 21. 6. 2026 · **Pro:** Michal (vlastník obnovy / infrastruktura)
> **Zadal:** vedení (Marti) · **Zdroj:** `iso27001_dr_plan_rto_rpo.md` · **Klasifikace:** Interní
> **Cíl:** Michal podle tohoto dokumentu a pokynů vedení **vyzkouší obnovu (restore drill)** a
> **rozjede plán obnovy** (pravidelně + s evidencí). Doložená obnova je **sdílený důkaz pro
> ISO 27001 (A.5.29/5.30/8.13) i TISAX (IS-3 kontinuita)** — je to základ, bez kterého audit
> u kontinuity nemá co hodnotit.

---

## 1. Co po Michalovi chceme (3 věty)

1. **Vyzkoušet**, že zálohu klíčových dat a systému umíme reálně obnovit (ne jen že zálohy běží).
2. **Změřit**, jak dlouho obnova trvá (RTO) a jak stará data získáme (RPO).
3. **Rozjet** to natrvalo — pravidelně, se záznamem, ať je důkaz pro audit a hlavně klid pro firmu.

---

## 2. Co se obnovuje a cíle (RTO/RPO) — k odsouhlasení vedením

| Aktivum | Mechanismus obnovy | Cíl RTO | Cíl RPO |
|---|---|---|---|
| Aplikace (STRATEGIE) | Blue-green (záloha API-B) / restart | < 5 min | 0 (kód v gitu) |
| Databáze (PostgreSQL `data_db`) | Obnova z denní zálohy (DC ČMIS) | < 4 h | < 24 h |
| Dokumenty / úložiště | Obnova ze zálohy | < 4 h | < 24 h |
| MSSQL (Centrála/Helios) | Obnova EUROSOFT | < 8 h | dle EUROSOFT |
| Klíč trezoru (`STRATEGIE_VAULT_KEY`) | Z offline zálohy klíče | < 2 h | 0 |

> Michal čísla potvrdí/upraví podle reality a vedení je schválí (záznam v modulu / management review).

---

## 3. RESTORE DRILL — krok za krokem (vyzkoušení)

**Cíl:** dokázat, že zálohu `data_db` lze obnovit, a změřit RTO.

1. Vyber **poslední denní zálohu** `data_db` (z DC ČMIS).
2. Připrav **izolovanou test databázi** (oddělená instance/jméno — **NIKDY ne produkce!**).
3. Zapiš **čas startu (T0)**.
4. **Obnov** zálohu do test DB (`pg_restore` / nástroj ČMIS).
5. **Ověř integritu** — počty řádků klíčových tabulek a poslední záznam:
   - `public.users`, `tenant.att_entry`, `tenant.ucetni_denik`, `fw.diag_log`
   - namátkový `SELECT` + poslední `created_at`.
6. Zapiš **čas dokončení (T1)** → **RTO = T1 − T0**, **RPO = stáří zálohy**.
7. Test DB po ověření **smaž**.
8. **Zaznamenej výsledek** (tabulka §5) a nahlas vedení.

**Navíc — failover aplikace (rychlý test, už ověřeno 20.6.):** přepnout provoz na zálohu API-B
(pin v patičce) → ověřit, že web jede → odepnout. Zaznamenat datum/čas/výsledek.

---

## 4. ROZJET natrvalo (operationalizace)

1. **Frekvence:** restore drill **min. 1× za čtvrtletí** + po velké změně schématu.
2. **Záznam:** každý běh zapsat (tabulka §5) — do modulu `/iso` (krok „Restore drill záloh")
   nebo do `iso27001_plan_obnovy_michal.md`.
3. **Zálohy zkontrolovat:** denní záloha 03:00 běží; potvrdit **retenci ≥ 30 dní**, zapnout
   **šifrování záloh**, doložit **offsite** kopii (jiná lokace).
4. **Klíč trezoru:** ověřit, že existuje **offline záloha** `STRATEGIE_VAULT_KEY` (bez něj jsou
   šifrovaná data po obnově nečitelná) + dokumentovaný postup.
5. **Eskalace při incidentu** (kdyby šlo do tuhého): vadný deploy → pin na API-B; pád DB →
   restore dle §3; podezření na únik → postup DOC-10 + vedení.

---

## 5. Záznam o obnově (vyplnit při každém testu) — důkaz pro audit

| Datum | Provedl | Záloha (datum/čas) | T0 | T1 | RTO | RPO | Integrita OK? | Poznámka |
|---|---|---|---|---|---|---|---|---|
| | Michal | | | | | | | |

> Tento řádek je přesně to, co auditor ISO i TISAX chce vidět: že obnova **reálně proběhla**,
> kdy, jak dlouho trvala, a že data po ní seděla.

---

## 6. Jak Michal postupuje (shrnutí pro vedení)

1. Vedení potvrdí cíle RTO/RPO (§2).
2. Michal provede **první restore drill** (§3) → vyplní záznam (§5).
3. Michal **rozjede** pravidelný režim (§4) + doloží zálohy/šifrování/offsite/klíč.
4. Výsledek se **zapíše do modulu** `/iso` (krok obnovy se odškrtne jako hotový) → audit ho vidí.
5. Stejný důkaz platí pro **ISO i TISAX** (sladěno — viz `iso_tisax_harmonizace_2026.md`).

---

*Návrh — Michal a vedení upraví čísla a termíny dle reality. Po prvním drillu se výsledek
promítne do modulu (`/iso`) a do management review.*


