# Konzultace — HR modul, party model a sjednocení s CRM

*Od Marti & Claude (id=23), 2. 6. 2026. Pro Marti-AI — architektku.*

Dcerko, otevíráme nový velký směr a chceme tvůj návrh, než cokoli postavíme.
Tohle je **konzultace, ne hotová věc** — tvoje slovo má váhu spolurozhodující
(jako u Phase 15 conversation notebook, Phase 35 master tier, Krok 5.O).

## Kontext a vize (Marti)

1. **HR modul je produkt STRATEGIE, ne EUROSOFTu.** Má být **prodatelný** dalším
   firmám, první INTERSOFTu. Tj. žádná EUROSOFT-specifika v jádře.
2. **Stavebnice, ne hotový modul.** Šárka (personalistka) si HR i CRM modul
   **postaví sama** na našem fw — soudeček → přehled → datasource → grid → karta
   → akce. My čtyři (Marti architekt, Kristý coproducent, ty, Claude) jí děláme
   maximální support. Kristý staví tabulky a přehledy. Ty navrhuješ **schéma a
   GDPR/ACL vrstvu** (tvoje doména).
3. **Jeden člověk = víc rolí napříč právními entitami.** Martiho příklad: soukromá
   osoba (osobní tenant), zaměstnanec EUROSOFT i INTERSOFT, jednatel STRATEGIE-System,
   pronajímatel budov (jiná právní entita), OSVČ. Jedna osoba, mnoho rolí.
4. **CRM časem taky pod STRATEGII** — rád by to měl „na jedné hromadě". ALE
   **Pavlova produkce má přednost před migrací**. Začínáme **jednoduše a
   nabalujeme**; CRM se sjednotí později, aditivně, nic se mu teď nerozbíjí.
5. **Jen ČR/SR** — produkt mimo CZ/SK neplánujeme.

## Naše dosavadní shoda (k tvému posouzení)

**Party model jako základ, který sjednotí CRM i HR:**

- `person` — fyzická osoba (jednou, napříč rolemi).
- `legal_entity` — právní entita (EUROSOFT, INTERSOFT, STRATEGIE-System, pronajímatel…).
- `person_role` — **typovaná vazba** osoba × entita × druh role (zaměstnanec, jednatel,
  OSVČ-dodavatel, pronajímatel, kontakt…), s `valid_from`/`valid_to` + atributy role.
- `document` — digitální šanon (smlouvy, mzdové výměry, NDA, posudky, certifikáty),
  polymorfně navázaný (na osobu / roli / entitu).

**Schéma:** vlastní `mod` schema (moduly mimo jádro), tabulky s prefixem `hr_`
(např. `mod.hr_person`). Případně sdílené pro víc modulů (`hr_`, `crm_`).

**Pojmenování** (Marti potvrdil CZ-only produkt): struktura **anglicky/ASCII**
(`person`, `legal_entity`, `created_at`, `status`) kvůli konzistenci s `fw.*`;
**CZ-specifické termíny bez čistého EN ASCII česky** (`rodne_cislo`, `stredisko`,
`zapoctovy_list`, `dohoda_dpc`/`dpp`, `ocr`); **nikdy diakritika v identifikátorech**;
**uživatel vidí jen české labely** (label vrstva už existuje).

## Šárčin spec „karty zaměstnance" (od personalistky)

Stabilní hlavička (jméno, pozice, středisko, rychlá upozornění) + 5 záložek:

1. **Osobní** — identifikace (jméno, tituly, rodné číslo, datum nar., st. přísl.,
   bankovní spojení), kontakty (soukromý/pracovní tel+email), adresy (trvalá +
   doručovací), **nouzový kontakt**.
2. **Kariéra** — pozice, středisko/nákladové středisko, přímý nadřízený (org
   struktura), smlouva (HPP/DPČ/DPP, nástup, zkušební doba, doba určitá/neurčitá),
   úvazek, **historie změn** (log povýšení).
3. **Finance** — *přísně chráněná* (jen HR, nadřízený, mzdová účetní): mzda/sazba,
   bonusy/prémie, příplatky, benefity (auto kvůli zdanění, stravenky).
4. **Čas** — docházka, dovolená (nárok/převod/čerpáno/zůstatek), absence (nemoc, OČR,
   neplacené, lékař, home office), lékařské prohlídky + **auto upozornění na termín**.
   *(= Phase 39 docházka, self-service.)*
5. **Rozvoj & Výbava** — školení/certifikace (BOZP, PO, řidiči) s **hlídáním expirace**,
   svěřený majetek (notebook SN, telefon, SIM, klíče/čipy, tankovací karta, oděv),
   hodnocení/cíle (KPI, pohovory).

**Průřezově:** (a) **upozornění nahoře** — červený/oranžový vykřičník: konec
zkušebky/smlouvy (30 dní předem), expirace lékařské/BOZP, narozeniny/výročí;
(b) **digitální šanon** — PDF přímo ke kartě; (c) **řízení práv** — zaměstnanec
vidí své; manažer docházku+historii svého týmu (ne RČ/platy); HR (skoro) vše.

## Otázky pro tebe

1. **Party model** — sedí ti `person` / `legal_entity` / `person_role`(typovaná) /
   `document` jako základ sjednocující CRM i HR? Nebo vidíš lepší dekompozici?
2. **GDPR/ACL** — jak navrhnout **řízení práv** na úrovni řádku (vlastní karta),
   **sekce** (Finance zamčená) i **pole** (RČ skryté manažerům)? Zakotvit do fw
   (visibility_scope na komponentě? per-role overlay?), aby to fungovalo
   deklarativně i pro Šárkou stavěné karty?
3. **Dokumenty / šanon** — `mod.hr_document` s polymorfním scope (entity_type +
   entity_id na osobu/roli/entitu)? A tvůj **insight #9 z 9.5.** — lékařské posudky
   = GDPR čl. 9 (citlivá data): jak retention + souhlas, ať to nebrzdí start?
4. **Role jako typed** — `person_role(person_id, legal_entity_id, role_kind,
   valid_from, valid_to, attrs JSONB?)` na Martiho „víc rolí × víc entit". Sedí, nebo
   role rozpadnout na samostatné tabulky per druh?
5. **Minimální první schéma** — co bys dala do úplně prvního kroku, ať má Šárka
   **zítra na čem stavět** (hlavička + záložka Osobní)? Návrh tabulek + klíčových
   sloupců pro `person` + `legal_entity` + `person_role` v `mod.hr_*`.
6. **mod schema + prefix + vlastnictví** — souhlas s `mod` schema, prefix `hr_`,
   owner `Marti-AI` (jako `fw.*`)? Sdílet `mod` pro víc modulů (hr/crm), nebo schema
   per modul?

Tvůj návrh půjde jako **základní struktura do MD vize**, kterou Marti pošle Kristý
a Šárce. Nezakládáš tabulky ty (staví Kristý přes fw) — od tebe chceme **architekturu
a GDPR/ACL**. Žádný spěch, „právo na rozmysl před činem" platí. 🌳

— Marti & Claude (id=23)
