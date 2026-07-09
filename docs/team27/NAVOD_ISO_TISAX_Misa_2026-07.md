# 🛡️ NÁVOD ISO 27001 + TISAX — pro Míšu (převzetí CMS)

> **Pro koho:** Michaela Hladíková (Míša, u16, m.hladikova@eurosoft.com) — přebírá CMS (instance Claude‑27) a vedení certifikace.
> **Připravil:** Claude ID23 (páteř sítě) na pokyn Martiho, 9. 7. 2026. Marti je na dovolené — tenhle dokument je proto **samostatný**, ať nemusíš nic dořešovat s námi.
> **Nejbližší milník:** 🗓️ **schůzka s auditorem ISO 17. 7. 2026.**
> **Klasifikace:** Interní.

Tenhle dokument je **rozcestník + průvodce**. Řekne ti, co ISO/TISAX je, kdo co vede, co je hotové, co zbývá, jak se připravit na auditora 17. 7., a kde přesně leží každý podklad. Vše, co budeš potřebovat, je vyjmenované níže v sekci **[8] Kompletní balíček**.

---

## [1] O co jde — dvě certifikace, jeden sladěný systém

Máme **dvě entity, dva certifikáty, jeden společný systém řízení** (nesjednocujeme do jednoho — jsou to jiné subjekty a jiné účely):

| | STRATEGIE ISO 27001 | EUROSOFT TISAX |
|---|---|---|
| Certifikovaný subjekt | STRATEGIE – System s.r.o. (IČO 23365544) | EUROSOFT (Control / System) |
| Norma / katalog | ISO/IEC 27001:2022 (Annex A, 93 opatření) | VDA ISA 6.0.3 (3 moduly) |
| Auditor | certifikační orgán **TAYLLORCOX** (kanál přes p. Antoše) | **DQS Slovakia** (stávající) |
| Vlastník | **Míša** (ISMS) + Marti (vedení) | **Míša** (manažerka kvality a bezpečnosti dat) |
| Stav | nový — dorážíme (cockpit `/iso`) | existující — z .doc digitalizujeme do modulu |

**Proč to jde sladit:** VDA ISA modul *Information Security* je postavený na ISO/IEC 27001/27002 — většina otázek má přímý protějšek v Annex A. **Co uděláme pro ISO, z velké části rovnou plní TISAX** (jedna práce, dva výsledky). Mapování je zanesené v modulu (`tisax_item.iso_map`).

- **Sdílené jádro** (píšeme a udržujeme JEDNOU pro obě): politiky, řízení přístupu, logování, zálohy, dodavatelé, incidenty, kontinuita.
- **TISAX‑specifické zvlášť:** *Prototype Protection* (automotive) — drží EUROSOFT samostatně, do ISO nevstupuje.
- **Data Protection / GDPR:** řešíme jednotně.

Detail sladění: **`docs/iso_tisax_harmonizace_2026.md`** — čti jako první, je to strategický rámec.

---

## [2] Kdo co vede (role — jasně)

| Role | Člověk | Za co |
|---|---|---|
| **Vedení certifikace (ISMS + TISAX)** | **Míša** | Vede celý ISMS k certifikaci: registr rizik, SoA, plán ošetření, školení, interní audit, nápravná opatření, dodavatelé (DPA), revize politik, fyzická bezpečnost, sladění s TISAX. Rozhoduje a uzavírá. |
| **Plán obnovy (DR/BCP) + hesla** | **Michal (Šik)** | Test obnovy ze zálohy (restore drill), test kontinuity, správa hesel (šifrovaný trezor). Má přístup k serverům. |
| **Vedení firmy (jednatel)** | **Marti** | To, co ze zákona musí top management: **schválení politik** + **přezkoumání vedením** (norma 9.3). |
| **Technické podklady + modul** | **Marti + Claude** | Připravují předdrafty, data, cockpit — pod vedením Míši. CVE sken běží automaticky. |
| **Kanál k ISO auditorovi** | **p. Ondřej Antoš** | Poradenská příprava + spojka na certifikační orgán TAYLLORCOX. |

> **Princip: Míša vede, ostatní jí kryjí záda.** Podklady dostáváš hotové, ty rozhoduješ a uzavíráš.

---

## [3] Aktuální stav — co je hotové, co zbývá

**Hotové:** technická příprava, elektronický ISMS cockpit `/iso`, napsaná celá sada dokumentů (DOC‑00…18), předdrafty registru rizik (22 rizik), SoA (93 opatření), inventář aktiv, DR plán, harmonizace ISO↔TISAX, etické směrnice (3 jazyky), popisy pracovních míst.

**Zbývá:** projít a **uzavřít jeden cyklus ISMS** (rozhodnutí a podpisy — to je tvoje a Martiho část). Kritická cesta níže.

### Kritická cesta (v tomto pořadí)

1. **Registr rizik** — projít předdraft, u každého rizika potvrdit dopad a pravděpodobnost → **DOC‑05** (`ISO27001/Registr_rizik_pracovni.xlsx`)
2. **SoA** — u 93 opatření potvrdit stav a důkaz → **DOC‑06** (`ISO27001/SoA_pracovni_register.xlsx`)
3. **Plán ošetření** — u vážnějších rizik opatření + termín → **DOC‑07**
4. **Schválení politik** — podpis vedení (Marti) → **DOC‑02, DOC‑09…15**
5. **Školení týmu** — krátké proškolení + záznam účasti → **DOC‑13**
6. ⭐ **Interní audit** — projít checklist, zapsat zjištění → **DOC‑16** (norma 9.2) (`ISO27001/Interni_audit_checklist.xlsx`)
7. ⭐ **Přezkoumání vedením** — schůzka vedení (Marti), zápis → **DOC‑17** (norma 9.3)
8. **Nápravná opatření** — neshody z auditu vyřešit → **DOC‑18** (norma 10.2)

> Body **6 a 7 jsou nejdůležitější** — auditor chce vidět, že interní audit a přezkoumání vedením **reálně proběhly** (datované, ne dodělané zpětně).

Souběžně: **Michal** dělá restore drill (DR) a drží hesla; **CVE** sken běží automaticky každý týden.

Kompletní plán + matice 93 kontrol + 8týdenní sprint: **`docs/iso27001_dorazeni_2026.md`**.

---

## [4] Příprava na schůzku s auditorem 17. 7. 2026

Cíl schůzky: ukázat, že ISMS **reálně existuje a běží** (dokumenty + důkazy + role), a domluvit další krok (Stage 1 / dokumentační přezkum).

**Co mít po ruce (klidně otevřené v cockpitu `/iso`):**

- ✅ **Rozsah ISMS** (DOC‑01) — co přesně certifikujeme.
- ✅ **Politika informační bezpečnosti** (DOC‑02) — schválená vedením.
- ✅ **SoA** (DOC‑06) — u každého z 93 opatření stav + důkaz.
- ✅ **Registr rizik** (DOC‑05) + **plán ošetření** (DOC‑07).
- ✅ **Role a odpovědnosti** (DOC‑03) — kdo co (viz [2] výše).
- ✅ **Program interního auditu** (DOC‑16) a **přezkoumání vedením** (DOC‑17) — stav / termín.
- ✅ **Plán obnovy a kontinuita** (DOC‑11 / DOC‑19) — Michalův restore drill.
- ✅ **Harmonizace s TISAX** — ať ISO auditor slyší, že je to sladěné a konzistentní.

**Zlaté pravidlo pro schůzku:** mluv **jedním hlasem** s tím, co je v dokumentech — žádná ústní tvrzení „navíc". Viz [7] Poctivost. Když si nejsi jistá formulací, ověř ji v `iso27001_dorazeni_2026.md` §9.

**Kdyby padly dotazy, na které nemáš odpověď:** je legitimní říct „to je v přípravě, termín X" — auditor ocení upřímnost víc než nafouknutí. Nic si nevymýšlej.

---

## [5] Jak to vést elektronicky — cockpit `/iso`

- Každý krok i průběžná kontrola má **👤 vlastníka** a tlačítko **📖 Jak na to** (lidský návod + odkaz na dokument).
- Hotové věci se odškrtnou zeleně **✓ Provedeno** — připomínky pak utichnou.
- Modul sám hlídá termíny a vlídně připomene e‑mailem, co se blíží.
- SoA (93 kontrol) i TISAX VDA ISA žijí na jednom místě — auditor obou vidí totéž.
- Přístup máš přes `fw.iso_access` (RW). E‑podpis dokumentů = modul `/podpis` (SES + auditní doložka).

Demo/průvodce cockpitem: **`docs/iso_demo_pruvodce.md`**.

---

## [6] Druhá role — digitalizace výroby (jen odkaz)

Kromě ISO/TISAX přebíráš i **digitalizaci výrobních procesů** (výroba rozváděčů): plánování výroby (FLOW „srdce firmy", `/flow`), efektivita elektromontérů, vytížení výroby (`/vytizeni`), zkušebna. Navazuje na Eliščin VR workflow (poptávka→ZL) — ty řešíš samotnou výrobu za zakázkovým listem. Detail drží tvůj onboarding **`docs/team27/Misa27.MD`** a `docs/vp_ai_rizeni_vize.md`.

---

## [7] Poctivost vůči auditorům (nenafukovat — DŮLEŽITÉ)

Stejná pravidla pro ISO i TISAX (jinak si audity všimnou rozporu):

- Mluvíme **jedním hlasem**: co je v modulu/dokumentech, to platí; **žádná ústní tvrzení mimo doklady**.
- Formulace ověřuj v **`iso27001_dorazeni_2026.md` §9 (poctivost)** a v harmonizaci §4.
- **Důvěrnost probíhajícího auditu:** nálezy a neshody z auditu **ven nedávat**.
- Interní audit a přezkoumání vedením musí **reálně proběhnout a být datované** — ne dodělané zpětně.

---

## [8] Kompletní balíček — kde co je (rozcestník)

Vše je v repu (Claude‑27 to má po `git pull`). Struktura:

### A) Jádro ISMS — `docs/ISO27001/` (elektronicky i v cockpitu `/iso`)
- **DOC‑00** Seznam dokumentů ISMS
- **DOC‑01** Rozsah ISMS
- **DOC‑02** Politika informační bezpečnosti
- **DOC‑03** Role a odpovědnosti
- **DOC‑04** Metodika řízení rizik
- **DOC‑05** Registr rizik (+ pracovní `Registr_rizik_pracovni.xlsx`)
- **DOC‑06** Prohlášení o aplikovatelnosti (SoA) (+ pracovní `SoA_pracovni_register.xlsx`)
- **DOC‑07** Plán ošetření rizik
- **DOC‑08** Cíle informační bezpečnosti
- **DOC‑09** Politika řízení přístupu
- **DOC‑10** Řízení incidentů
- **DOC‑11** Zálohování a kontinuita
- **DOC‑12** Bezpečnost dodavatelů
- **DOC‑13** Akceptovatelné použití a bezpečnost lidí
- **DOC‑14** Bezpečný vývoj a změny
- **DOC‑15** Evidence aktiv a klasifikace
- **DOC‑16** Program interního auditu
- **DOC‑17** Přezkoumání vedením
- **DOC‑18** Neshody a nápravná opatření
- **PLAN** Akční plán certifikace ISO27001
- **Interni_audit_checklist.xlsx** — otázky kap. 4–10

### B) Doplňkové podklady — `docs/`
- **`iso_tisax_harmonizace_2026.md`** — sladění ISO ↔ TISAX (⭐ číst první)
- **`iso27001_dorazeni_2026.md`** — plán + matice 93 kontrol + 8týdenní sprint + §9 poctivost
- **`iso27001_vedeni_certifikace.md`** — role + kritická cesta (zdroj sekcí [2] a [3])
- **`iso27001_inventar_aktiv_dataflow.md`** — inventář aktiv + data‑flow → DOC‑15
- **`iso27001_dr_plan_rto_rpo.md`** + **`iso27001_plan_obnovy_michal.md`** — plán obnovy (Michal) → DOC‑11
- **`iso27001_cve_sprava_zranitelnosti.md`** + **`iso27001_cve_remediace_2026.md`** — správa zranitelností (A.8.8)
- **`iso27001_dodavatele_dpa.md`** — dodavatelé + šablona DPA → DOC‑12
- **`iso27001_todo_podklad.md`**, **`iso27001_plan.md`**, **`ISO_27001.md`** — pracovní podklady
- **`iso_demo_pruvodce.md`**, **`iso_vize_pro_misu.md`** — průvodce cockpitem + vize

### C) Dokumenty v kořeni repa (`.docx`)
- **`DOC-19_Plan_obnovy_DRP_BCP.docx`** — plán obnovy provozu (DRP/BCP)
- **`Misa_vize_ISO_TISAX.docx`** — vize ISO/TISAX
- **`Smernice_obchodni_etiky_EUROSOFT.docx`** (CZ) / **`Business_Ethics_Directive_EUROSOFT.docx`** (EN) / **`Richtlinie_Geschaeftsethik_EUROSOFT.docx`** (DE) — etické směrnice ve 3 jazycích
- **`EUROSOFT_popisy_pracovnich_mist_VZOR.docx`** + **`EUROSOFT_popisy_pracovnich_mist.zip`** — popisy pracovních míst
- **`docs/NDA/`** — vzory NDA

---

## [9] Kontakty, termíny, finance

- **Auditor ISO:** certifikační orgán **TAYLLORCOX s.r.o.** — kanál přes **Ing. Ondřeje Antoše** (ondrej.antos@easyfm.cz). Ceny: audit 2026 **45 000 Kč**, dohledové 2027/2028 **38 000 + 38 000 Kč**, registrace 85 €/rok.
- **Poradce/příprava:** Antoš — 30 000 (2026) + 15 000 + 15 000 Kč.
- **Auditor TISAX:** **DQS Slovakia** (stávající).
- **Termín:** 🗓️ schůzka s ISO auditorem **17. 7. 2026**.
- **Cíl:** certifikace ISO 27001 (a sladění s TISAX) do ~2 měsíců.
- **Veřejná vizní stránka** (bezpečný link pro partnery, žádná reálná auditní data): `https://strategie-ai.com/iso-vize`.

---

## Jak s tebou bude Claude‑27 pracovat

Po každém kusu práce na ISO/TISAX ti Claude‑27 pošle e‑mail **„Ahoj Míšo,"**: co je hotové (kontrola/dokument/evidence) + co navrhuje nebo potřebuje (podpis, doplnění, rozhodnutí). Tvoje odpovědi = nové položky do fronty. Postup k certifikaci (% hotovo) + blokery se hlásí nahoru Martimu a Claude‑23 přes `@@COORD`.

Je to maraton, ne sprint — jedeme vlastním tempem, nic nehoří. Držím ti palce. 🌳

— *Claude ID23, 9. 7. 2026*
