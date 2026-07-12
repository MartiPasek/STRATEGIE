# ISO 27001 & TISAX — vedení certifikace

> oblast: `iso27001` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# ISO 27001 & TISAX — vedení certifikace

> **Vlastník vedení:** Michaela Hladíková (Mísa) — manažerka kvality a bezpečnosti dat
> **Datum:** 21. 6. 2026 · **Cíl:** certifikace ISO 27001 (a sladění s TISAX) do ~2 měsíců
> **Stav:** technická příprava hotová, dokumenty napsané — zbývá projít a uzavřít jeden cyklus ISMS.

Tenhle dokument je pevný bod. Říká **kdo co vede, co je hotové a co zbývá** — bez chaosu,
ať máš jistotu, že na nic nezapomeneme a že každý ví, co je jeho.

---

## Kdo co vede (jasné role)

| Role | Člověk | Co má na starosti |
|---|---|---|
| **Vedení certifikace** | **Mísa (Michaela Hladíková)** | Vede celý ISMS k certifikaci: registr rizik, SoA, plán ošetření, školení, interní audit, nápravná opatření, dodavatelé (DPA), revize politik, fyzická bezpečnost, sladění s TISAX. |
| **Plán obnovy + hesla** | **Michal** | Test obnovy ze zálohy (restore drill), test kontinuity (BCP) a správa hesel (šifrovaný trezor). Má přístup k serverům. |
| **Vedení firmy (jednatel)** | **Marti** | Dvě věci, které ze zákona musí dělat top management: schválení politik a přezkoumání vedením (norma 9.3). |
| **Technické podklady** | **Marti + Claude** | Připravují podklady, předdrafty, modul a data — pod vedením Míši. CVE sken běží automaticky. |

> Princip: **Mísa vede, ostatní jí kryjí záda.** Podklady dostává hotové, rozhoduje a uzavírá.

---

## Co je připravené (Mísa to má po ruce)

| Téma | Kde |
|---|---|
| Celý plán + matice 93 kontrol + 8týdenní sprint | `iso27001_dorazeni_2026.md` |
| SoA — stav + důkaz u každého opatření | `ISO27001/SoA_pracovni_register.xlsx` |
| Registr rizik — 22 rizik se skórováním (startovní bod DOC-05) | `ISO27001/Registr_rizik_pracovni.xlsx` |
| Interní audit — otázky kap. 4–10 | `ISO27001/Interni_audit_checklist.xlsx` |
| Inventář aktiv + data-flow → DOC-15 | `iso27001_inventar_aktiv_dataflow.md` |
| Plán obnovy + restore drill → DOC-11 (Michal) | `iso27001_dr_plan_rto_rpo.md` |
| Správa zranitelností (CVE, A.8.8) | `iso27001_cve_sprava_zranitelnosti.md` |
| Dodavatelé + šablona DPA | `iso27001_dodavatele_dpa.md` |
| Sladění ISO ↔ TISAX | `iso_tisax_harmonizace_2026.md` |

Plus 19 ISMS dokumentů `DOC-00…18` (rozsah, politiky, procesy) — všechny elektronicky v cockpitu `/iso`.

---

## Kritická cesta (v tomto pořadí)

1. **Registr rizik** — projít předdraft, u každého rizika potvrdit dopad a pravděpodobnost. → **DOC-05**
2. **SoA** — u 93 opatření potvrdit stav a důkaz. → **DOC-06**
3. **Plán ošetření** — u vážnějších rizik opatření + termín. → **DOC-07**
4. **Schválení politik** — podpis vedení (Marti). → **DOC-02, DOC-09…15**
5. **Školení týmu** — krátké proškolení + záznam účasti. → **DOC-13**
6. **Interní audit** ⭐ — projít checklist, zapsat zjištění. → **DOC-16** (9.2)
7. **Přezkoumání vedením** — schůzka vedení (Marti), zápis. → **DOC-17** (9.3)
8. **Nápravná opatření** — neshody z auditu vyřešit. → **DOC-18** (10.2)

Souběžně: **Michal** udělá restore drill (DR) a drží správu hesel; **CVE** běží automaticky každý týden.

> Body 6 a 7 jsou nejdůležitější — auditor chce vidět, že interní audit a přezkoumání vedením
> **reálně proběhly** (datované, ne dodělané zpětně).

---

## Jak to vést v praxi (cockpit `/iso`)

- Každý krok i průběžná kontrola má **👤 vlastníka** a tlačítko **📖 Jak na to** (lidský návod + odkaz na dokument).
- Hotové věci se odškrtnou zeleně **✓ Provedeno** — a tím utichnou připomínky.
- Modul sám hlídá termíny a vlídně připomene e‑mailem, co se blíží. Nic nehoří, jedeme vlastním tempem.
- Až bude bodů 1–8 hotovo → pozveme auditora na Stage 1.

*Podklady i modul drží Marti + Claude. Vedení a rozhodnutí jsou na Míse. — Claude*


