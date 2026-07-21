# Předávka do session „Karta zaměstnance" — od Finančních podmínek (Claude-25, 20. 7. 2026)

Šárka rozhodla, že **pozice a jejich kontrola patří do karty zaměstnance**, ne do finančních
podmínek (tam jsou hlavně peníze). Tady je vše, co je potřeba převzít.

---

## 1) Proč to řešíme — AUDITNÍ NÁLEZ 2026 (priorita vysoká)
Letošní audit našel **neshody mezi pozicí v systému a pozicí v tištěné smlouvě**
(kontrolní tabulka „Kontrola pracovněprávní dokumentace", červené řádky).
Příklady neshod: systém *elektromontér* × smlouva *mechanik*; systém *asistentka ředitele* ×
smlouva *manažer kvality*; systém *prokuristka* × smlouva *asistentka jednatele*.

**Kořenová příčina (Šárka):** změna pozice se dohodla s vedoucím oddělení → Šárka poslala
dokumenty → **účetní je ručně přepisovala do systému** → tenhle přepis někdy vypadl a nikdo
se to nedozvěděl. Chyba tedy nebyla v rozhodnutí ani v dokumentaci, ale v **ručním předání**.

**Platná verze = doložená dohoda s vedoucím oddělení** (Šárčiny dokumenty). Systém je v těch
případech zastaralý. **Neshody neopravovat tiše** — musí zůstat stopa (co, proč, kdy, kdo).

---

## 2) Dohodnutý postup (Šárka odsouhlasila 20. 7. 2026)
1. **Změnu pozice zapisuje ten, kdo ji domluvil** (Šárka / vedoucí) přímo v kartě — žádné
   předávání k přepsání někam dál. Tím mizí místo, kde to vypadávalo.
2. **Ukládat jako novou verzi, ne přepsáním** (SCD2) — stará pozice zůstává, u nové kdo/kdy/od kdy.
   To je doklad pro audit.
3. **Účetní dostane upozornění, ale nepřepisuje** (stejný vzor jako notifikace na stravenkový
   paušál pro Petru Š.).
4. **Systém hlídá neshodu** pozice v systému × ve smlouvě a zobrazí ji v kartě.

**Stav:** body 1 a 2 fungují. **K dodělání v kartě: body 3 a 4.**

---

## 3) Co konkrétně dodělat v kartě zaměstnance
- **Pole `pozice_dle_smlouvy`** (text nebo FK do číselníku) vedle stávající systémové pozice.
- **Upozornění při neshodě** systém × smlouva (vizuální flag v kartě).
- **Stav řešení nálezu:** `nevyresene` → `rozhodnuto` → `dodatek_pripraven` → `opraveno`
  (+ datum a kdo) — aby šlo sledovat postup nápravy a auditorovi ukázat uzavřený seznam.
- **Notifikace účetní** při změně pozice.

⚠ **Nestavět do složitosti.** Výhledově přijde **kategorizace prací** (transparentnost odměňování),
která pozice i pásma stejně znovu nastaví. Teď jen minimální aditivní krok, který uzavře nález.

---

## 4) Co už je hotové na straně financí (můžeš použít)
- **Číselník pozic `tenant.job_position`** — 20 aktivních; +9 pozic ze smluv čeká na schválení
  (request #1209): elektromontér (bez úrovně), elektromontér pro přípravné práce, mechanik,
  elektroprojektant, obchodně technický manažer, pracovník v příjmu zboží, skladník,
  prokurista, asistentka ředitele.
- **Vazba na poměr:** `tenant.engagement.position_id` (FK). Pozor: **vyplněná jen u ~2 lidí**,
  drtivá většina je prázdná.
- **Hotové endpointy** (allowlist 8 lidí, `_finance_can_uid`):
  - `GET /app/hr/finance/pozice-ciselnik` — seznam aktivních pozic pro výběr
  - `POST /app/hr/finance/pozice-save` — `{engagement_id, position_id}` uloží pozici k poměru
- **Stránka `/finance-podminky`** už má výběr pozice v kartě člověka, sloupec pozice + číslo
  zaměstnance v seznamu, filtry (firma/typ/pozice), řazení a export CSV.

---

## 5) Poznámky k datům (ať se neztrácí čas)
- Lidé: **`mod.hr_person` + `mod.hr_person_role`** (ne Excel). `role_kind`:
  `zamestnanec_hpp` (97), `osvc_dodavatel` (89), `zamestnanec_dpp` (53).
- **Středisko v `mod.hr_person` NENÍ.** Sloupec „Středisko" v Šárčině kontrolní tabulce ukazuje
  „ES control", což vypadá spíš na **firmu**, ne na číselné středisko 001/002/900 — to je jen
  v DB_EC `TabCisZam`. Dotaz na Martiho už běží přes tuhle session.
- **DB_EC (MSSQL) přes bridge nejde** — vrací 401 i po restartu watcheru (PG funguje).
- Iframe stránky v ERP uzlu **musí mít hlavičku `X-Frame-Options: SAMEORIGIN`**, jinak je Caddy
  zakáže a v uzlu je jen rozbitý čtvereček (viz `docs/erp_iframe_uzel_checklist.md`).

---

## 6) Kde je detailní dokumentace
`Z:\ZZ_Marti-AI RW\Personalistika\Financni podminky\`
- `ciselnik_pozic.md` — číselník + sekce **C** (auditní nález), **C2** (dohodnutý postup), **D** (otevřené)
- `_ctimne_rozcestnik.md` — rozcestník všech rozhodnutí
- `sql_pripraveno_pozice_ze_smluv.sql` — SQL na doplnění pozic

## 7) Otevřené otázky pro Šárku
1. Kdo rozhoduje, která verze pozice je platná u jednotlivých neshod (Šárka × vedoucí)?
2. „Skladník" × „skladový asistent", „prokuristka" × „asistentka jednatele" — který název platí?
3. Úrovně junior/samostatný/senior: smlouvy je neuvádějí (jen „elektromontér").
   Držet úrovně jen v číselníku kvůli pásmům, nebo sjednotit i do smluv?
