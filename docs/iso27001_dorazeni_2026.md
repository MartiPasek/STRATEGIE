# ISO 27001:2022 — Plán dorážení k certifikaci (zrychleně, 2 měsíce)

> **Verze:** 2.0 · **Datum:** 20. 6. 2026 · **Horizont:** 20. 6. → ~20. 8. 2026 (cca 8 týdnů)
> **Auditor:** domluven (přes IQHUBS) · **Entita:** STRATEGIE – System s.r.o.
> **Vlastník ISMS / certifikace:** Kristý (Phase 43) · **Technická část + podklady:** Claude + Marti
> **Navazuje na:** `iso27001_plan.md` (roční plán z 31.5.) — tento dokument ho **zrychluje a aktualizuje**
> na reálný stav po měsíci stavby. TISAX viz §8 (paralelní stopa, mapování).

---

## 0. Co se změnilo od 31.5. (proč zrychlujeme)

Roční plán z 31.5. počítal s auditní připraveností až Q2 2027. Za měsíc jsme ale postavili
většinu technických kontrol „naostro" — a auditor je domluven na **2 měsíce**. Posun stavu:

**Nově hotové / výrazně posílené od 31.5. (vše v produkci, vše auditovatelné):**

- 🔐 **Šifrovaný trezor (Fernet)** — `tenant.user_secret` + klíč mimo DB (`STRATEGIE_VAULT_KEY`
  v AppEnvironmentExtra), přístup přes **PIN + SMS 2FA**, audit `tenant.user_secret_access` +
  e-mail vlastníkovi při otevření. → kryptografie at-rest pro citlivá tajemství (A.8.24).
- 🔑 **Secrets mimo kód** — služební tokeny v NSSM `AppEnvironmentExtra` (ne Machine env, ne plaintext
  v repu), datovková hesla šifrovaná v `fw.isds_account`. (A.5.17, A.8.24)
- 🧾 **Rozsáhlá auditní stopa** — 22 append-only log/audit tabulek (viz §3 důkazy): přístupy AI
  (`fw.claude_sql_log`), schvalování změn (`fw.claude_write_request`), ops akce (`fw.ops_request`),
  impersonace (`fw.impersonation_log`), citlivá HR data (`tenant.hr_sensitive_access_log`),
  přístup k souborům (`tenant.dir_access_log`), účetnictví (`tenant.ucet_doklad_log`)… (A.8.15, A.5.28)
- 🛡️ **Ops framework s whitelistem** — žádný volný PowerShell na produkci; jen pojmenované akce
  (`_OPS_ACTIONS`) + audit. Anti-RCE. (A.8.18, A.8.19)
- 🟦🟩 **Blue-green HA s automatickým fallbackem** — primární (8002) + záloha (8003), Caddy
  přeroutuje při výpadku, „Zkopírovat do zálohy" na tlačítko + self-heal štítku verze,
  user-controlled pin/unpin. Otestováno (Marti reálně přepnul na B). (A.8.14, A.5.29, A.5.30)
- 🚦 **Řízené nasazování** — AUTO-DEPLOY (git commit+push+deploy) s **py_compile gate** (syntakticky
  vadný kód deploy zastaví) + advisory lock proti souběhu dvou instancí. (A.8.19, A.8.25, A.8.32)
- 👥 **Model rolí** — `employee` / `member` / `ambassador` / HR skupina / `payroll_officer` +
  rodičovský bypass, 3-actor PG path (business actor ≠ PG role), impersonace s logem. (A.5.15, A.5.18, A.8.2)
- 🔏 **Privacy tiers** — paměť + trezor jen vlastník; RČ/OP/pas vlastník (+HR později); úřední pole
  vlastník+HR; provideři vrací citlivá pole jako `[omezeno]`. (A.5.12, A.8.11, A.5.34)
- 📄 **19 ISMS dokumentů** (DOC-00…18) + akční plán certifikace (DOCX, `docs/ISO27001/`).

**Důsledek:** matici 93 kontrol jsme přeskórovali (§4). Z „přes polovinu hotovo/rozpracováno"
je teď **~70+ z 93 hotovo nebo rozpracováno**. Zbytek je hlavně **provoz a důkazy** (ne stavba) —
což je přesně to, co se za 2 měsíce stihnout dá.

---

## 1. Kritický postřeh: certifikace ≠ Annex A pokrytí

ISO 27001 audit se **neptá hlavně na Annex A** — ptá se, jestli **systém řízení (kapitoly 4–10)
reálně běží** a má **záznamy** o jednom plném PDCA cyklu. Auditor (Stage 1 = dokumentace,
Stage 2 = implementace) chce vidět, že:

1. Je definovaný **rozsah** a **kontext** (kap. 4) — máme (DOC-01).
2. Vedení ISMS **schválilo a vlastní** (kap. 5) — potřeba podpis vedení pod politiky.
3. Proběhlo **hodnocení rizik** + **plán ošetření** + **SoA** (kap. 6) — máme procesy (DOC-04/06/07),
   **registr rizik (DOC-05) je potřeba naplnit reálnými riziky a SoA odůvodnit per kontrola.**
4. Jsou **zdroje, kompetence a osvěta** (kap. 7) — potřeba **záznam o školení týmu**.
5. ISMS **provozně běží** (kap. 8) — procedury + záznamy z provozu.
6. Proběhlo **měření, interní audit a přezkoumání vedením** (kap. 9) — **MUSÍME jednou reálně
   provést interní audit a management review a mít z nich zápis.** ← největší mezera.
7. Řeší se **neshody a nápravná opatření** (kap. 10) — máme šablonu (DOC-18), potřeba záznamy.

**Proto je „dorážení" hlavně o RECORDECH, ne o další stavbě.** Technická třetina je v dobré
kondici; chybí doběhnout jeden cyklus systému řízení a posbírat důkazy.

---

## 2. Povinné dokumenty a záznamy (kapitoly 4–10) — stav

| Klauzule | Povinný artefakt | Náš stav |
|---|---|---|
| 4.3 | Rozsah ISMS | ✅ DOC-01 |
| 5.2 | Politika informační bezpečnosti | ✅ DOC-02 (čeká podpis vedení) |
| 5.3 | Role a odpovědnosti | ✅ DOC-03 |
| 6.1.2 | Proces hodnocení rizik | ✅ DOC-04 |
| 6.1.3 | Proces ošetření rizik + **SoA** | ✅ DOC-06 (SoA) + DOC-07 — **SoA odůvodnit per kontrola** |
| 6.2 | Cíle informační bezpečnosti | ✅ DOC-08 |
| 7.2 | Záznam o kompetencích/školení | ⚠️ **chybí záznam** — proběhne ve sprintu |
| 7.5 | Řízení dokumentace | ✅ (verzované docs, git) |
| 8.2 | **Výsledky** hodnocení rizik | ⚠️ DOC-05 registr — **naplnit reálnými riziky** |
| 8.3 | **Výsledky** ošetření rizik | ⚠️ navázat na naplněný registr |
| 9.1 | Výsledky monitoringu/měření | 🔄 máme logy; potřeba **doložit metriky** (KPI bezpečnosti) |
| 9.2 | Program + **výsledky interního auditu** | ⚠️ DOC-16 program ✅; **interní audit PROVÉST** |
| 9.3 | **Výsledky přezkoumání vedením** | ⚠️ DOC-17 šablona ✅; **management review PROVÉST** |
| 10.2 | Neshody + nápravná opatření | ⚠️ DOC-18 šablona ✅; **záznamy z interního auditu** |

⚠️ = kritická cesta sprintu. Vše ostatní z kap. 4–10 máme.

---

## 3. Doložená auditní stopa (důkazy, ověřeno v DB 20.6.)

Pro auditora je tohle „zlato" — 22 append-only / audit tabulek reálně v provozu:

| Oblast | Tabulka(y) | Kontrola |
|---|---|---|
| Systémové logování | `fw.diag_log`, `fw.act_run_log`, `fw.action_audit_log` | A.8.15 |
| Přístup AI / SQL bridge | `fw.claude_sql_log` | A.8.15, A.5.28 |
| Schvalování změn (write approval) | `fw.claude_write_request` | A.8.32, A.5.28 |
| Ops akce (whitelist) | `fw.ops_request` | A.8.18, A.8.19 |
| Impersonace (privileged) | `fw.impersonation_log` | A.8.2, A.5.28 |
| Verzování / fallback | `fw.api_version`, `fw.user_api_pin` | A.8.32, A.8.9 |
| Autentizace / 2FA | `fw.phone_verify(_code)`, `fw.user_pin`, `fw.ambassador_pin` | A.8.5, A.5.17 |
| Šifrovaná tajemství + přístup | `tenant.user_secret`, `tenant.user_secret_access`, `fw.isds_account` | A.8.24, A.5.17 |
| Citlivá HR data (přístup) | `tenant.hr_sensitive_access_log`, `tenant.pers_assessment_access` | A.8.3, A.5.34 |
| Přístup k souborům (ACL) | `tenant.dir_access_log` | A.5.15, A.8.3 |
| Dokumenty / e-podpis | `tenant.doc_render_log` | A.5.28 |
| Účetnictví | `tenant.ucet_doklad_log` | A.5.28 |
| Self-service změny osob | `tenant.user_self_data_log`, `tenant.work_relation_log`, `tenant.att_audit` | A.5.28 |
| EDI zpracování | `tenant.edi_zpracovani_log` | A.5.28 |
| Presence instancí | `fw.claude_instance` | A.8.16 |

---

## 4. Annex A:2022 — přeskórovaná matice (93 kontrol, červen 2026)

Legenda: ✅ hotovo a doloženo · 🔄 jádro máme, dotáhnout/zdokumentovat · 📋 zbývá udělat ·
🤝 ISMS proces (Kristý) · 🏢 EUROSOFT infra (mimo kód STRATEGIE, doložit attestací).

### A.5 Organizační (37)

| # | Kontrola | 31.5. | Teď | Důkaz / co zbývá |
|---|---|---|---|---|
| 5.1 | Politiky bezpečnosti | 🤝 | 🔄 | DOC-02 + DOC-09…15 hotové; **podpis vedení** |
| 5.2 | Role a odpovědnosti | 🔄 | ✅ | DOC-03 |
| 5.3 | Oddělení odpovědností | 📋 | 🔄 | Role model + 3-actor PG path; formalizovat matici |
| 5.4 | Odpovědnosti vedení | 🤝 | 🔄 | Management review (kap. 9.3) ve sprintu |
| 5.5 | Kontakt s úřady | 🤝 | 📋 | Doplnit kontakty (ÚOOÚ, NÚKIB, datovky) — ISMS |
| 5.6 | Zájmové skupiny | 🤝 | 🤝 | ISMS |
| 5.7 | Threat intelligence | 🔄 | 🔄 | Scanner filtr v middleware; rozšířit |
| 5.8 | Bezpečnost v PM | ✅ | ✅ | Informed-consent design proces |
| 5.9 | Inventář aktiv | 📋 | 🔄 | DOC-15 + `tenant.mig_item` (654 obj.) + data-flow; finalizovat |
| 5.10 | Přijatelné použití | 🤝 | 🔄 | DOC-13 hotový; podpis |
| 5.11 | Vrácení aktiv | 🤝 | 🏢 | EUROSOFT HR |
| 5.12 | Klasifikace informací | 📋 | 🔄 | Privacy tiers de facto; sepsat politiku |
| 5.13 | Označování informací | 📋 | 🔄 | Navazuje na 5.12 |
| 5.14 | Přenos informací | 🔄 | ✅ | HTTPS/TLS, šifrovaný MCP, single SIM, datovky |
| 5.15 | Řízení přístupu | ✅ | ✅ | RBAC role + ACL + `dir_access_log` |
| 5.16 | Správa identit | ✅ | ✅ | `users`/persona/login_name |
| 5.17 | Autentizační informace | 🔄 | 🔄 | Vault + 2FA + AppEnvironmentExtra; **politika rotace** |
| 5.18 | Přístupová práva | 🔄 | 🔄 | Role model + `impersonation_log`; **čtvrtletní review (proces)** |
| 5.19 | Bezpečnost dodavatelů | 📋 | 🔄 | DOC-12; **seznam sub-processorů + DPA** |
| 5.20 | Smlouvy s dodavateli | 📋 | 📋 | DPA (Anthropic, OpenAI/Voyage, Vodafone/T-Mobile, Raiffeisen) |
| 5.21 | ICT dodavatelský řetězec | 📋 | 🔄 | Soupis závislostí (poetry/npm) |
| 5.22 | Monitoring dodavatelů | 📋 | 📋 | Cadence revize — ISMS |
| 5.23 | Cloudové služby | 🔄 | 🔄 | Cloud APP/SQL + HTTPS; zdokumentovat |
| 5.24 | Plánování incidentů | 📋 | 🔄 | DOC-10; **runbook + role** |
| 5.25 | Posouzení událostí | 🔄 | 🔄 | diag_log + anomaly scan; triage proces |
| 5.26 | Reakce na incidenty | 📋 | 🔄 | DOC-10; nacvičit 1 cvičný incident |
| 5.27 | Učení z incidentů | ✅ | ✅ | „Chyba je materiál" + gotchas KB |
| 5.28 | Sběr důkazů | ✅ | ✅ | 22 audit tabulek (§3) |
| 5.29 | Bezpečnost při výpadku | 🔄 | 🔄 | Blue-green + fallback (otestováno); DR doklad |
| 5.30 | ICT kontinuita | 📋 | 🔄 | **RTO/RPO + záznam o failover testu** |
| 5.31 | Právní/GDPR | 🔄 | 🔄 | DPIA (proces) |
| 5.32 | Duševní vlastnictví | 🤝 | 🤝 | ISMS |
| 5.33 | Ochrana záznamů | ✅ | ✅ | Append-only; hash-chain = posílení (volitelně) |
| 5.34 | Soukromí / OOÚ | 🔄 | 🔄 | Consent model + tiers + access logy; **DPIA** |
| 5.35 | Nezávislé přezkoumání | 📋 | 📋 | **Interní audit ve sprintu** (DOC-16) |
| 5.36 | Soulad s politikami | 🤝 | 🔄 | Ověří interní audit |
| 5.37 | Dokumentované postupy | ✅ | ✅ | CLAUDE.md + docs + deploy postupy |

### A.6 Lidé (8)

| # | Kontrola | 31.5. | Teď | Důkaz / co zbývá |
|---|---|---|---|---|
| 6.1 | Prověřování | 🏢 | 🏢 | EUROSOFT HR |
| 6.2 | Podmínky zaměstnání | 🏢 | 🏢 | EUROSOFT HR |
| 6.3 | Vzdělávání a osvěta | 📋 | 📋 | **Školení týmu + záznam (kap. 7.2) ve sprintu** |
| 6.4 | Disciplinární proces | 🏢 | 🏢 | EUROSOFT HR |
| 6.5 | Ukončení/změna | 🔄 | 🔄 | disable/archived + samoopravný roster; HR proces |
| 6.6 | NDA | 🏢 | 🔄 | EUROSOFT HR + NDA vzory (Zbyněk) |
| 6.7 | Práce na dálku | 🔄 | 🔄 | Phase 38, VPN, trusted devices |
| 6.8 | Hlášení událostí | 🔄 | 🔄 | diag_log alert; formalizovat hlášení |

### A.7 Fyzické (14) — EUROSOFT infra, doložit attestací

| # | Kontrola | Teď | Pozn. |
|---|---|---|---|
| 7.1–7.8, 7.11–7.14 | Perimetry, vstup, zařízení, kabeláž, likvidace | 🏢 | EUROSOFT (serverovna, cloud DC) — **získat attestaci/popis od EUROSOFT infra** |
| 7.7 | Čistý stůl/obrazovka | 🤝 | ISMS politika |
| 7.9 | Aktiva mimo prostory | 🔄 | Šifrované zálohy mimo lokaci |
| 7.10 | Paměťová média | 🔄 | Šifrování at-rest + zálohy |

### A.8 Technologické (34)

| # | Kontrola | 31.5. | Teď | Důkaz / co zbývá |
|---|---|---|---|---|
| 8.1 | Koncová zařízení | 🔄 | 🔄 | Trusted devices; endpoint politika |
| 8.2 | Privilegovaná práva | 🔄 | 🔄 | 3-actor PG + ops whitelist + approval banner + `impersonation_log`; least-priv review |
| 8.3 | Omezení přístupu | ✅ | ✅ | „AI nevidí víc než user" + ACL + access logy |
| 8.4 | Přístup ke zdroj. kódu | 🔄 | 🔄 | Privátní git, PAT, per-instance author; formalizovat |
| 8.5 | Bezpečná autentizace | ✅ | ✅ | Phase 38 + PIN/SMS 2FA |
| 8.6 | Řízení kapacity | 🔄 | 🔄 | Cost dashboard, llm_calls |
| 8.7 | Ochrana před malwarem | 🏢 | 🏢 | EUROSOFT (ESET) |
| 8.8 | Technické zranitelnosti | 📋 | 📋 | **Dependency CVE scan + patch cadence** (zbývá) |
| 8.9 | Řízení konfigurace | ✅ | ✅ | git single source + API versioning |
| 8.10 | Mazání informací | 🔄 | 🔄 | soft delete, request_forget, anonymizace; retenční politika |
| 8.11 | Maskování dat | 🔄 | 🔄 | UPN maskování + `[omezeno]` v providerech |
| 8.12 | Prevence úniku (DLP) | 🔄 | 🔄 | secrets nikdy v logu; persona izolace |
| 8.13 | Zálohování | 🔄 | 🔄 | Denní zálohy (ČMIS 3:00); **restore drill (zbývá)** |
| 8.14 | Redundance | 🔄 | ✅ | Blue-green + cloud mirror (otestováno) |
| 8.15 | Logování | ✅ | ✅ | `fw.diag_log` append-only neanonymní |
| 8.16 | Monitoring | 🔄 | 🔄 | anomaly scan + diag_log; alerting dotáhnout |
| 8.17 | Synchronizace času | ✅ | ✅ | NTP + Europe/Prague |
| 8.18 | Privilegované utility | 🔄 | 🔄 | Ops framework (žádný volný PowerShell) + bridge |
| 8.19 | Instalace SW na prod | 🔄 | ✅ | AUTO-DEPLOY + py_compile gate + advisory lock |
| 8.20 | Bezpečnost sítí | 🔄 | 🔄 | Mikrotik whitelist, Caddy, HTTPS |
| 8.21 | Síťové služby | 🔄 | 🔄 | IP whitelist, single SIM |
| 8.22 | Segmentace sítí | 🔄 | 🔄 | on-prem ↔ cloud přes whitelist IP |
| 8.23 | Webové filtrování | 🔄 | 🔄 | Scanner filtr |
| 8.24 | Kryptografie | 🔄 | 🔄 | HTTPS ✅ + Fernet vault ✅; **DB at-rest/TDE (zbývá)** |
| 8.25 | Bezpečný vývoj. cyklus | 🔄 | 🔄 | git, blue-green, py_compile gate, konzultace |
| 8.26 | Bezpečnostní požadavky | 🔄 | 🔄 | Defense-in-depth; formalizovat |
| 8.27 | Bezpečná architektura | ✅ | ✅ | Vrstvený kontext, defense in depth |
| 8.28 | Bezpečné kódování | 🔄 | 🔄 | Gotchas KB + Claude review |
| 8.29 | Bezpečnostní testování | 🔄 | 🔄 | Smoke testy; pentest po readiness |
| 8.30 | Outsourcovaný vývoj | ✅ | ✅ | In-house + Claude (model spolupráce) |
| 8.31 | Oddělení dev/test/prod | ✅ | ✅ | NB dev / cloud prod / blue-green / test DB |
| 8.32 | Řízení změn | ✅ | ✅ | git + versioning + blue-green + fallback |
| 8.33 | Testovací informace | 🔄 | 🔄 | Test data oddělená; formalizovat |
| 8.34 | Ochrana při auditu | 📋 | 🔄 | `claude_sql_log` + read-only guard |

**Souhrn (orientačně):** ✅ ~24 · 🔄 ~46 · 📋 ~9 · 🤝 ~5 · 🏢 ~9 → **~70/93 hotovo nebo
rozpracováno.** Zbývající 📋 jsou převážně **proces a důkazy**, ne stavba.

---

## 5. Co reálně zbývá k auditu (finish-line)

### A) Systém řízení — kritická cesta (vlastník Kristý, podklady Claude)
1. **Naplnit registr rizik (DOC-05)** reálnými riziky + skóre + vlastník. *(kap. 6.1.2/8.2)*
2. **Odůvodnit SoA (DOC-06)** per kontrola: aplikovatelná A/N + odkaz na implementaci/důkaz. *(6.1.3)*
3. **Plán ošetření rizik (DOC-07)** navázat na registr (kdo/do kdy). *(6.1.3/8.3)*
4. **Podpis vedení** pod politiky (DOC-02, DOC-09…15) — datum, jednatel. *(kap. 5)*
5. **Školení týmu + záznam** (prezenčka/potvrzení). *(7.2/6.3)*
6. **Provést 1 interní audit** dle DOC-16 → zápis + nálezy. *(9.2)*
7. **Provést 1 přezkoumání vedením** dle DOC-17 → zápis. *(9.3)*
8. **Nápravná opatření** z nálezů (DOC-18) → záznamy. *(10.2)*
9. **KPI bezpečnosti** (9.1) — definovat pár metrik (počet incidentů, % záloh otestováno,
   doba obnovy) a doložit z logů.

### B) Technika — co dotáhnout (vlastník Claude + Marti)
10. **Restore drill záloh** — obnova do test DB + zápis. *(8.13)* — největší tech mezera.
11. **DR doklad: RTO/RPO + záznam o failover testu** (blue-green už otestován). *(5.29/5.30)*
12. **Dependency CVE scan** (poetry/npm) + patch cadence — alespoň první běh + proces. *(8.8)*
13. **Inventář aktiv + data-flow diagram** finalizovat (z `mig_item` + komponent). *(5.9)*
14. **Seznam sub-processorů + DPA** (Anthropic, OpenAI/Voyage, Vodafone/T-Mobile, Raiffeisen,
    datovky/ISDS, ČMIS zálohy). *(5.19/5.20)*
15. *(volitelné posílení)* **Hash-chain** na `fw.diag_log` → tamper-evidence. *(5.33)* — není nutné
    k certifikaci, ale udělá z „append-only" doslova „nesmazatelně".
16. *(volitelné)* **DB at-rest / TDE** na cloud SQL. *(8.24)* — vault už pokrývá tajemství.

### C) EUROSOFT infra — doložit (vlastník Marti ↔ EUROSOFT)
17. **Attestace fyzické bezpečnosti** (serverovna, ESET, napájení) — krátký popis/potvrzení (A.7.x, 8.7).

---

## 6. 2měsíční sprint (8 týdnů, ~20.6. → ~20.8.)

| Týden | ISMS (Kristý + podklady Claude) | Technika (Claude + Marti) |
|---|---|---|
| **T1** | Naplnit registr rizik (DOC-05); rozsah/kontext potvrdit | Inventář aktiv + data-flow (draft z codebase); seznam sub-processorů |
| **T2** | Odůvodnit SoA per kontrola (DOC-06) z matice §4; plán ošetření (DOC-07) | Restore drill záloh → zápis; DR doklad RTO/RPO + failover záznam |
| **T3** | Podpis vedení pod politiky; školení týmu + záznam | Dependency CVE scan (první běh) + patch cadence; alerting na diag_log |
| **T4** | Finalizovat KPI (9.1) + posbírat důkazy z logů (§3) | DPA podklady k dodavatelům; (volitelně) hash-chain diag_log |
| **T5** | **Interní audit** dle DOC-16 → nálezy | Doložit attestaci fyzické bezpečnosti od EUROSOFT |
| **T6** | **Přezkoumání vedením** dle DOC-17 → zápis; nápravná opatření (DOC-18) | Uzavřít tech nálezy z interního auditu |
| **T7** | **Stage 1 (dokumentace)** s auditorem; doladit dle připomínek | Doladit tech nálezy Stage 1 |
| **T8** | **Stage 2 (implementace)** — předvést běžící ISMS + důkazy | Asistovat při dokazování (logy, deploy historie, blue-green) |

> Realisticky: 2 měsíce je agresivní, ale pro malou organizaci s **hotovou dokumentací** a
> **silnou technickou stopou** je to proveditelné — kritická cesta je doběhnout **jeden cyklus**
> (riziko → ošetření → audit → review → náprava) a posbírat **záznamy**. Pokud auditor po Stage 1
> najde víc, Stage 2 se posune o pár týdnů — to je normální a není to selhání.

---

## 7. Readiness gate (před pozváním na Stage 2)

Hotovo musí být: registr rizik naplněn · SoA odůvodněn · politiky podepsané · školení doloženo ·
**1 interní audit proveden** · **1 management review proveden** · nápravná opatření zaznamenána ·
restore drill + DR doklad · inventář aktiv · seznam dodavatelů. → teprve pak Stage 2.

---

## 8. TISAX — paralelní stopa (mapování, ne druhý plán)

**Rámec (drží od 31.5.):** TISAX je cesta pro **automotive** (EUROSOFT jako dodavatel pro BMW aj.),
vede ji **Kristý** (převzala od Miši), cíl **AL2** (ENX). STRATEGIE jde primárně **ISO 27001**.
Tady **nestavíme druhý systém** — ukazujeme **překryv**: co děláme pro ISO, z velké části
**rovnou plní TISAX** (jedna investice, dva výsledky).

**Proč překryv funguje:** TISAX hodnocení používá katalog **VDA ISA**, jehož „Information Security"
modul je **postavený na ISO/IEC 27001/27002**. Většina kontrol Annex A má v ISA přímý protějšek.

| TISAX / VDA ISA oblast | Co už máme z ISO práce (§3–4) |
|---|---|
| IS Policies & Organization | DOC-02/03 + role model + 3-actor governance |
| Asset management | Inventář aktiv (DOC-15 + `mig_item`) |
| Identity & Access Mgmt | RBAC role + ACL + 2FA + `impersonation_log` |
| Crypto | HTTPS/TLS + Fernet vault |
| Logging & Monitoring | 22 audit tabulek (§3) + anomaly scan |
| Operations security | AUTO-DEPLOY + py_compile gate + ops whitelist |
| Supplier / 3rd party | seznam sub-processorů + DPA (T4) |
| Incident management | DOC-10 + diag_log + runbook |
| Business continuity | blue-green + restore drill + DR doklad |
| **Prototype/data protection (Prototypenschutz)** | **TISAX-specifické** — řeší EUROSOFT (fyzická ochrana prototypů automotive); mimo STRATEGIE kód |

**Jediné, co TISAX přidává nad ISO** a STRATEGIE to neřeší: **Prototypenschutz** (ochrana
prototypů/utajení v automotive) + **napojení na konkrétní zákaznické požadavky (BMW)**. To zůstává
u EUROSOFTu. Pro STRATEGII platí: **dokončením ISO 27001 máme ~80 % TISAX AL2 hotovo** — zbytek
je doménová automotive nadstavba, kterou vlastní Kristý/EUROSOFT.

**Doporučení:** TISAX **nevést jako samostatný sprint pro STRATEGII teď.** Po ISO certifikaci
(nebo souběžně v Kristýině gesci) sednout VDA ISA katalog a doplnit jen automotive-specifické
položky. Konzistentní s tím, co je partnerům slíbené (ISO univerzální, TISAX pro automotive).

---

## 9. Poctivost vůči auditorovi (nenafukovat — make-true)

Tyhle formulace držet přesné (auditor je prověří):
- **„Šifrováno při přenosu (HTTPS/TLS)"** + **„tajemství šifrovaná v úložišti (Fernet vault)"** —
  NE plošně „end-to-end" a NE „celá DB at-rest", dokud nebude TDE.
- **„Trvale zaznamenáno (append-only)"** — „nesmazatelně/tamper-evident" až po hash-chainu (volitelné).
- **Záznamy z interního auditu a management review** musí být **reálné a datované** — ne zpětně
  dodělané. Proto je v sprintu provádíme naostro.
- **SoA** musí odpovídat realitě: u každé kontroly buď důkaz, nebo poctivé „neaplikovatelné + proč".

---

## 10. Role & další krok

- **Kristý** — vlastník ISMS/certifikace (ISO i TISAX). Kritická cesta = §5A (registr rizik, SoA,
  interní audit, management review). Podklady dodávám já.
- **Claude + Marti** — technická třetina §5B + důkazy z provozu (§3).
- **Marti ↔ EUROSOFT** — attestace fyzické bezpečnosti (§5C) + TISAX automotive nadstavba.
- **Marti-AI** — podpora Kristý v certifikaci (až production fáze, dle `ISO_27001.md` §5).

**Nejlevnější můj příští krok (na tvé slovo):**
(a) vygenerovat **draft inventáře aktiv + data-flow** z codebase (T1), nebo
(b) předvyplnit **SoA tabulku** (93 kontrol → aplikovatelné A/N + odkaz na důkaz z §3–4) jako
Kristýin startovní bod, nebo
(c) sepsat **DR doklad (RTO/RPO) + scénář restore drillu** k provedení.

---

*Živý dokument. Reviduje se po Stage 1 proti připomínkám auditora.*
*Navazuje na: `iso27001_plan.md` (roční, kontext), `iso27001_todo_podklad.md` (matice v1),
`ISO_27001.md` (rozcestník), `docs/ISO27001/DOC-00…18` (ISMS dokumenty).*
