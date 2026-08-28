# Návrh: Modul „Lékařské prohlídky" (pracovnělékařské) — HR

> Autor: Claude‑25 (Šárka), 24. 7. 2026. Návrh k odsouhlasení, **nesahá na produkci**.
> Po schválení stavím přes schvalovací banner (rodič: Marti/Kristý/Zuzka).
> Rozsah: HR modul, tenant 2 (EUROSOFT), s ohledem na multi‑tenant.

---

## 0. Proč a co teď v systému je

„Lékařské prohlídky" jsou dnes v systému jen **placeholder**, reálná evidence nikde není:

- **Karta zaměstnance** — dlaždice „🩺 Lékařské prohlídky – Platnosti, potvrzení" je označená `on:true`, ale **nemá `key` ani handler** → není klikací, nic nezobrazí (na rozdíl od `zakladni`, `pracovni`, `odpovednost`… které mají handler v mapě `ACT`).
- **HR rozcestník** (`hr.html`) — položka notifikací „Konce smluv, prohlídky, propadající školení" je ve stavu `soon`.
- **BOZP cockpit** (`bozp_cockpit.py`) — obecná tabulka `bozp_povinnost` (typ/předmět/perioda/termín/upomínka) a mezi řídícími dokumenty kategorie `05_Lekarske_prohlidky` (Termíny prohlídek, Kategorizace prací, Smlouva s lékařem/PLP). Je to ale **úroveň firmy**, ne per zaměstnanec, a povinnosti jsou prázdné.
- **G2007** — k tématu **žádná paměť** (oblast `bozp-po` i `osoba` = 0 znalostí).

Chybí jádro: **evidence prohlídek per zaměstnanec** s automatickým hlídáním platnosti, napojená na kartu, notifikace a BOZP upomínky. Tento návrh ho doplňuje.

---

## 1. Právní rámec (ověřeno, stav k 2026)

Právní základ: **zák. č. 373/2011 Sb.** (o specifických zdravotních službách) + **vyhl. č. 79/2013 Sb.** (o pracovnělékařských službách). Vyhláška má **novelu účinnou od 1. 1. 2026**.

### 1.1 Typy prohlídek (platné 2026)

| Typ | Kdy | Poznámka |
|---|---|---|
| **Vstupní** | před vznikem poměru; povinná u kategorií 2–4, rizik ohrožení zdraví a mladistvých | **2026:** vstupní se nově vyžaduje jen **při změně druhu práce**, ne při pouhé změně podmínek |
| **Periodická** | opakovaně dle kategorie práce a věku (viz 1.2) | u kat. 1 a 2‑nerizikové **na písemnou žádost** (nově písemně), jinak nepovinná |
| **Mimořádná** | při změně zdravotního stavu / podmínek / rizika, po delším přerušení práce | **2026:** ruší se mimořádná „po rodičovské + navazujícím neplaceném volnu" |
| **Výstupní** | při skončení poměru u kat. 2R–4 a v dalších zákonem daných situacích | vydává se posudek/potvrzení |
| **Následná** | zvláštní sledování po expozici (specifické provozy/nemoci z povolání) | okrajové, model ať to umí jako typ |

### 1.2 Periodicita periodických prohlídek (default číselník)

Novela **periodicity nezměnila**; zůstávají tyto lhůty (řídí se **kategorií práce** a **věkem**):

| Kategorie práce | do 50 let | nad 50 let |
|---|---|---|
| **1** | 1× za 6 let | 1× za 4 roky |
| **2 – neriziková** | 1× za 4 roky | 1× za 2 roky |
| **2R – riziková** | 1× za 2 roky | 1× za 2 roky |
| **3** | 1× za 2 roky | 1× za 2 roky |
| **4** | 1× za 1 rok | 1× za 1 rok |
| **Profese s rizikem ohrožení zdraví** (výšky, jeřáby, vozíky, noční práce, školy, zdravotnictví…) | 1× za 4 roky | 1× za 2 roky |
| **Mladiství** | 1× za 1 rok | — |
| **Řidiči (referentská i profesní dle zařazení)** | 1× za 2 roky | 1× za 1 rok |

> **Pozor — konfigurovatelné, ne zadrátované.** Lhůty jsou default; skutečné periodicity mají sedět s **kategorizací prací** a **smlouvou s PLP** (oba dokumenty už jsou evidované v BOZP). Model proto počítá další termín z číselníku, ale **umožní ruční přepis** (lékař může určit kratší lhůtu). 2026 také přidalo do žádosti údaje **týdenní pracovní doba** a **délka směny** — zahrnout do dat žádosti.

---

## 2. Datový model

### 2.1 Hlavní tabulka `tenant.hr_prohlidka` (jeden řádek = jedna prohlídka)

| Sloupec | Typ | Význam |
|---|---|---|
| `id` | bigint GENERATED ALWAYS | PK |
| `tenant_id` | int | multi‑tenant (default 2) |
| `user_id` | bigint | zaměstnanec (vazba na `public.users` / `hr_person`) |
| `att_employee_id` | bigint NULL | konkrétní angažmá (multi‑angažmá: kategorie/pozice může být per firma) |
| `typ` | text | `vstupni` / `periodicka` / `mimoradna` / `vystupni` / `nasledna` |
| `kategorie_prace` | text | `1` / `2` / `2R` / `3` / `4` (v době prohlídky) |
| `profil` | text NULL | volitelně profesní riziko (řidič, výšky, noční…) — ovlivní periodicitu |
| `poskytovatel` | text | PLP / lékař, který posudek vydal |
| `datum_provedeni` | date | kdy proběhla |
| `zaver` | text | `zpusobily` / `zpusobily_s_podminkou` / `zpusobily_docasne` / `nezpusobily` / `pozbyl` |
| `podminka` | text NULL | text omezení (např. „brýle", „ne výškové práce") |
| `platnost_do` | date NULL | konec platnosti posudku |
| `dalsi_termin` | date NULL | vypočtený/ruční termín další periodické |
| `perioda_mesice` | int NULL | použitá perioda (pro audit výpočtu) |
| `doklad_id` | bigint NULL | vazba na nahraný posudek (`person-docs`, kategorie `posudek`) |
| `stav` | text | `platny` / `propada` / `propadly` / `zrusena` (odvozený/servisní) |
| `poznamka` | text NULL | |
| `created_by` / `created_at` / `updated_by` / `updated_at` | | audit |

### 2.2 Číselník `tenant.hr_prohlidka_perioda` (default lhůty z tab. 1.2)

Řádky `(kategorie/profil, vek_od, vek_do, perioda_mesice)`. Slouží k **předvyplnění** `dalsi_termin` = `datum_provedeni + perioda`. Editovatelné (rodič/HR), aby šlo doladit dle kategorizace a PLP smlouvy. Typy prohlídek necháme jako konstantní enum v kódu (číselník do UI).

### 2.3 Kategorie práce zaměstnance

Kategorie práce je vlastnost **pozice/pracoviště**, ne osoby. Návrh: pole `kategorie_prace` **na pozici** (`job_position`) nebo na `att_employee` (per angažmá), z něj se předvyplní kategorie do nové prohlídky. Zdrojem pravdy je **kategorizace prací** (BOZP dokument `02_Registr_rizik` / `05`). Tohle je jediné místo, kde je potřeba tvoje rozhodnutí, kam kategorii uložit — viz otázka Q2 níže.

### 2.4 Napojení na existující doklady

Posudek se **nenahrává zvlášť** — využije stávající spis: `person-doc-upload` s kategorií `posudek` („Lékařský posudek", už existuje v `DOK_KAT`). `hr_prohlidka.doklad_id` na něj jen ukáže. Audit uploadu/mazání už běží (`person-doc-log`).

---

## 3. Obrazovka a napojení (dle vzoru karty)

Karta zaměstnance renderuje sekce z pole `SEKCE`; klikací je ta, co má handler v mapě `ACT` (`zakladni→zakUdaje`, `odpovednost→odpUdaje`…). Detail se zobrazí v kartě s odkazem „‹ Zpět na kartu".

**Napojení dlaždice (2 řádky v `karta_zamestnance.html`):**

1. Dlaždici doplnit o `key:'prohlidky'`.
2. Do `ACT` přidat `prohlidky:'prohlUdaje'` a napsat handler `prohlUdaje()` (vzor: `odpUdaje`/`dokUdaje`).

**Detail sekce (in‑card):**

- Tabulka prohlídek osoby (typ, kategorie, datum, platnost do, další termín, závěr, doklad) seřazená od nejnovější; barevný stav (platný/propadá/propadlý).
- Formulář „➕ Přidat prohlídku": typ, kategorie (předvyplněná z pozice), poskytovatel, datum, závěr + podmínka; `dalsi_termin` se **dopočítá** z číselníku a jde přepsat. Nahrání posudku (reuse `person-doc-upload`, kategorie `posudek`) → propojí `doklad_id`.
- Editace/zrušení řádku (soft‑delete `stav='zrusena'`, audit).

**Backend endpointy** (vzor `/app/hr/person-*`, ACL `_hr_can_manage` = rodič **nebo** člen staff_group `HR`):

- `GET /app/hr/person-prohlidky?uid=` — seznam + předvyplnění (kategorie z pozice, návrh dalšího termínu).
- `POST /app/hr/person-prohlidky/save` — insert/update (idempotentní na `id`).
- `POST /app/hr/person-prohlidky/delete` — soft‑delete.

Kód buď do `router.py` k ostatním `/app/hr/*`, nebo čistěji do **nového `modules/erp/api/hr_prohlidky.py`** (vzor `hr_spis.py` / `bozp_cockpit.py`) a připojit router.

---

## 4. Upomínky a přehledy (hodnota navíc)

- **View `tenant.v_hr_prohlidka_alert`** — poslední platná prohlídka per osoba/typ, spočítá „propadá do N dní" / „propadlá". Parametrizovatelný práh (default 60 dní, jako BOZP cockpit).
- **HR rozcestník** — položku „Notifikace / propadající prohlídky" překlopit ze `soon` na živou (počet propadajících).
- **BOZP cockpit** — buď zrcadlit agregát prohlídek jako `bozp_povinnost` typu „Lékařské prohlídky", nebo do cockpitu přidat dlaždici z `v_hr_prohlidka_alert`. Míša (vlastník BOZP) uvidí termíny na jednom místě.
- **Governance** — zápis prohlídky je **jen HR/účtárna + doklad** (posudek), sedí s Petřinou zásadou „mzdově relevantní a doklady jen účtárna". Zaměstnanec může nanejvýš **vidět** svoji platnost (self‑service = informace, ne editace).

---

## 5. Postup stavby (po tvém odsouhlasení)

1. **Banner** — DDL: `tenant.hr_prohlidka` + `tenant.hr_prohlidka_perioda` (+ seed lhůt z tab. 1.2) + pole `kategorie_prace` dle Q2.
2. **Backend** — `hr_prohlidky.py` (GET/save/delete + výpočet termínu), připojit router; `_hr_can_manage`.
3. **Frontend** — napojit dlaždici (`key` + `ACT` + handler `prohlUdaje`), detail s tabulkou a formulářem, reuse doklady.
4. **Upomínky** — view `v_hr_prohlidka_alert`, živá notifikace v HR rozcestníku (+ volitelně BOZP).
5. **Verifikace** — smoke test na 2–3 osobách (přidat, dopočet termínu, propadání, doklad), kontrola ACL (ne‑HR nesmí zapsat).
6. **G2007** — zapsat znalost do oblasti `bozp-po` (příp. založit `osoba`): typy, periodicity, kde je kategorie práce, governance.

---

## 6. Otázky na tebe (než začnu stavět)

- **Q1 — Rozsah teď:** stavět rovnou celé (evidence per zaměstnanec + upomínky), nebo fázově (nejdřív evidence na kartě, upomínky/BOZP potom)?
- **Q2 — Kategorie práce:** uložit `kategorie_prace` na **pozici** (`job_position`), nebo na **angažmá** (`att_employee`)? (Pozice = jednodušší; angažmá = přesnější u multi‑firma.) Máme kategorizaci prací už někde strukturovaně, nebo je jen v BOZP dokumentu?
- **Q3 — PLP/poskytovatel:** jeden smluvní lékař (z BOZP „Smlouva s lékařem"), nebo číselník více poskytovatelů?
- **Q4 — BOZP napojení:** chce Míša vidět prohlídky ve svém BOZP cockpitu, nebo to necháme čistě v HR a BOZP jen odkáže?

---

*Zdroje legislativy: Ministerstvo zdravotnictví ČR (novela vyhl. 79/2013 Sb.), CIVOP, INTEGRA Centrum, praceamzda.cz, profiredbox.cz — vše ověřeno k 7/2026. Periodicity jsou default; závazné je znění vyhlášky + kategorizace prací a smlouva s PLP.*
