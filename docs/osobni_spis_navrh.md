# Osobní spis zaměstnance — návrh (jednoduchý, k odsouhlasení)

Autor: Claude-25 (za Šárku), 1. 7. 2026. **K odsouhlasení Marti + konzultaci Marti-AI.**
Vůdčí princip (Šárka): **jednoduché, systematické, uživatelsky přívětivé.**
„Klikni na člověka → vidíš jeho platné dokumenty." Nic víc.

## Cíl
- **HR** (personalista + rodiče) vidí u každého spolupracovníka (OSVČ i HPP)
  jeho **aktuální a podepsané** pracovněprávní dokumenty.
- **Zaměstnanec** vidí ve své appce **svoje** dokumenty (jen ke čtení).

## Princip — drží se stávající architektury
- **Osoba** = `public.users` / `tenant.att_employee` (jeden člověk, doctrine #24).
- **Zdroj dokumentů** = Centrála (složka „dokumenty" na kartě zaměstnance) →
  **mirror** do STRATEGIE (stejný vzor jako `_sync_fin_from_ec`). Generování
  z našich šablon až výhledově (fáze 2).
- **Práva** = stávající vzor: rodiče + HR přístup vidí vše; zaměstnanec **jen
  svoje** (`user_id = self`). GDPR: subject-level.

## Data — jedna minimální nová tabulka
`tenant.hr_spis_dokument`:
`id, tenant_id, user_id, employee_id, typ` (smlouva / dodatek / mzdovy_vymer /
dpp_dpc / osvc / zapoctovy_list / ostatni), `nazev, platnost_od, platnost_do,
is_current, podepsano` (bool + datum), `stav` (platny / archiv), `zdroj`
(centrala / generovano / nahrano), `storage_ref` (cesta nebo document_id),
`created_at, created_by`. Historie přes `is_current` (SCD-lite, jako engagement).

## Pohledy (dvě obrazovky, obě jednoduché)
1. **HR — „Osobní spisy"** (dlaždice v HR sekci): seznam lidí (jméno, firma,
   počet platných dok) → detail osoby → dokumenty (defaultně jen aktuální +
   podepsané, filtr typu). Otevření = PDF náhled.
2. **Zaměstnanec — „Moje dokumenty"** (dlaždice v mobilu): jen svoje, jen ke
   čtení, jen aktuální + podepsané.

## Sync z Centrály
Jakmile známe **cestu ke složce** dokumentů (od IT / Michala): mirror job
(denně + tlačítko „Načíst teď"). Spáruje soubor → osoba → typ (dle názvu /
konvence) → stav podepsáno. Idempotentní (jako ostatní syncy).

## Co teď NEřešíme (fáze 2+)
Generování dokumentů z šablon přímo do spisu, verzování dodatků, workflow
elektronického podpisu.

## Otevřené k odsouhlasení (Marti / Marti-AI)
1. **Umístění** — nová dlaždice „Osobní spisy" v HR sekci + „Moje dokumenty"
   v mobilu. Sedí to do struktury?
2. **Zdroj** — potvrdit cestu ke složce dokumentů v Centrále (IT/Michal).
3. **ACL pro self-service** — zaměstnanec vidí jen sebe: reuse stávajícího
   vzoru práv, nebo nová tenká vrstva? (kustodská otázka)
4. **GDPR** — osobní dokumenty + self-service: audit přístupu, retenční pravidla.

---

## Marti-AI review (1. 7. 2026) — zapracováno do návrhu

Marti-AI návrh schválila směrově a přidala tato vylepšení (beru do finálu):

1. **Typy dokumentů = číselník, ne volný text.** Fixní typy od začátku
   (smlouva / dodatek / mzdový výměr / DPP-DPČ / OSVČ / zápočtový list / …),
   ať za rok nemáme 5 variant „pracovní smlouva".
2. **`is_current` dopočítané, ne ruční flag** — odvozené z `platnost_do`
   (prázdné nebo ≥ dnes = aktuální). Nerozsynchronizuje se.
3. **Soubor zůstává v Centrále, STRATEGIE drží jen referenci + metadata** —
   `storage_ref` ukazuje na zdroj, soubor nekopírujeme. Čistší GDPR (za storage
   odpovídá Centrála). Pokud by se někdy kopíroval do STRATEGIE → šifrovaně.
4. **Práva: row-level filtr `osoba = přihlášený` v service vrstvě**, ne jen v UI
   (jinak by šlo upravit URL a vidět cizí spis). Pro zaměstnance **whitelist
   polí** — vidí jen to své (ne interní `stav`, `zdroj`, cizí historii).
5. **GDPR audit:** každý přístup HR k dokumentu konkrétního člověka logovat
   (kdo/kdy/co); zaměstnanec má právo si log vyžádat. Download logovat + rate
   limit (žádné „stáhnout vše").
6. **Retence:** doplnit `smazat_po` odvozené od typu dokumentu + konce poměru
   (smlouva se archivuje jinak než potvrzení BOZP). Součást číselníku typů.
7. **Prefix `hr_`** jako vědomý namespace pro HR tabulky (vedle `att_`, `wage_`).
8. **Fáze 2 (generování ze šablon)** má jiný lifecycle (draft → podpis → archiv)
   → oddělit přes `zdroj` enum ('centrala_mirror' / 'strategie_generated' /
   'manual_upload') od začátku.

**Stav:** Marti-AI to zvedla k Martimu k odsouhlasení. **Stavíme až po jeho OK.**

---

## Zdroj dokumentů — potvrzeno (Šárka, 1. 7. 2026)

- **Cesta:** `\\192.168.30.11\Data\Zamestnanci` (= `D:\Data\Zamestnanci` na EC-SERVER2).
- **Přístup:** EUROSOFT MCP souborové nástroje (`eurosoft_file_list/read`) s
  base_override na kořeny Centrály. **Nutný krok při stavbě:** přidat
  `D:\Data\Zamestnanci` do whitelistu povolených kořenů (config MCP filesystem).
- **GDPR pojistka:** do složky se nekouká předčasně; strukturu ověřím a sync
  postavím až po Martiho OK. Soubory zůstávají v Centrále, STRATEGIE drží jen
  reference + metadata (viz Marti-AI bod 3).
- **Otevřené k ověření při stavbě:** jak jsou pojmenované podsložky po lidech
  (jméno? osobní číslo?) → určí párování složka → osoba.
