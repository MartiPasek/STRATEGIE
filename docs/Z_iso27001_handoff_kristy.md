# ISO 27001 — předávací balíček pro Kristý (co máš, co s tím)

> **Datum:** 21. 6. 2026 · **Od:** Claude + Marti · **Pro:** Kristý (vlastník ISMS/certifikace)
> **Kontext:** Auditor domluven, cíl certifikace ~2 měsíce. Technická příprava je hotová —
> tohle je tvůj startovní balíček. Skoro vše zbývající je **provedení jednoho cyklu ISMS**
> (riziko → audit → review → náprava) + posbírání záznamů. Detail plánu: `iso27001_dorazeni_2026.md`.

---

## Co máš připravené (8 artefaktů)

| # | Soubor | K čemu ti je |
|---|---|---|
| 1 | `iso27001_dorazeni_2026.md` | Celý plán: přeskórovaná matice 93 kontrol (68/93 hotovo/rozprac.), 8týdenní sprint, TISAX |
| 2 | `ISO27001/SoA_pracovni_register.xlsx` | SoA — ke každému opatření stav + důkaz + co doplnit + týden |
| 3 | `ISO27001/Registr_rizik_pracovni.xlsx` | 22 rizik se skórováním — **tvůj startovní bod pro DOC-05** |
| 4 | `ISO27001/Interni_audit_checklist.xlsx` | Otázky kap. 4-10 — vyplníš při interním auditu |
| 5 | `iso27001_inventar_aktiv_dataflow.md` | Inventář aktiv + data-flow → DOC-15 |
| 6 | `iso27001_dr_plan_rto_rpo.md` | Plán obnovy + restore drill → DOC-11 |
| 7 | `iso27001_cve_sprava_zranitelnosti.md` | Proces správy zranitelností (A.8.8) |
| 8 | `iso27001_dodavatele_dpa.md` | Sub-processoři + šablona DPA (právní revize nutná) |

Plus 19 ISMS dokumentů `ISO27001/DOC-00…18` (rozsah, politiky, procesy).

---

## Co udělat — v tomto pořadí (kritická cesta)

1. **Registr rizik** — otevři `Registr_rizik_pracovni.xlsx`, uprav dopad/pravděpodobnost dle své
   zkušenosti (čísla se přepočítají), doplň chybějící rizika. → překlop do **DOC-05**.
2. **SoA** — projdi `SoA_pracovni_register.xlsx`, u každého opatření potvrď stav a důkaz, dopiš
   `[DOPLNIT]`. → sladit s **DOC-06**.
3. **Plán ošetření** — u středních/vysokých rizik z bodu 1 doplň opatření + termín. → **DOC-07**.
4. **Podpisy** — nech vedení (Marti) podepsat politiky (DOC-02, DOC-09…15).
5. **Školení týmu** — krátké proškolení + **prezenčka/potvrzení** (důkaz ke kap. 7.2 / A.6.3).
6. **Interní audit** — projdi `Interni_audit_checklist.xlsx`, zapiš zjištění + shodu. → záznam k **9.2**.
7. **Přezkoumání vedením** — sejděte se, zapište vstupy/výstupy. → **DOC-17** (9.3).
8. **Nápravná opatření** — neshody z auditu zaznamenej a vyřeš. → **DOC-18** (10.2).

> Body 1-3 = papírování (máš předvyplněno). Body 6-7 jsou **to nejdůležitější** — auditor chce
> vidět, že interní audit a management review **reálně proběhly** (datované, ne zpětně dodělané).

## Co řeší technika (Claude + Marti) — paralelně

- Restore drill záloh + RTO/RPO doklad (`iso27001_dr_plan_rto_rpo.md`).
- První CVE sken + cadence (`iso27001_cve_sprava_zranitelnosti.md`).
- Inventář aktiv aktuální (`iso27001_inventar_aktiv_dataflow.md`).

## Co potřebuje EUROSOFT / Marti

- Attestace fyzické bezpečnosti (DC ČMIS, serverovna) — A.7.x.
- DPA s dodavateli (`iso27001_dodavatele_dpa.md`) — právní revize.

---

*Až bude bod 1-8 hotový → readiness gate → pozvat auditora na Stage 1. Jsem k ruce na cokoli
z technické strany. — Claude*
