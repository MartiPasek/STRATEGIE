# ISO 27001:2022 — 1-letý plán technické přípravy (STRATEGIE)

> oblast: `iso27001` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# ISO 27001:2022 — 1-letý plán technické přípravy (STRATEGIE)

> **Verze:** 1.0 · **Datum:** 31. 5. 2026 · **Horizont:** Q3 2026 → Q2 2027
> **Vlastník technické části:** Claude + Marti · **Vlastník ISMS procesu:** Kristý (Phase 43)
> **Rozsah (scope):** STRATEGIE platforma (cloud APP + cloud SQL + EUROSOFT-MCP on-prem)
> a data, která zpracovává (osobní údaje klientů EUROSOFT/INTERSOFT, Marti-AI paměť).

---

## 1. Cíl

Dostat STRATEGII do stavu **auditní připravenosti pro ISO 27001:2022** během 12 měsíců,
aniž bychom narušili produkci nebo zpomalili stavbu ERP/CRM. Cílem **není** certifikace
za rok — cílem je mít **technickou třetinu** ISMS hotovou a dokumentovanou tak, aby
certifikační audit byl reálný krok (ne přepisování systému).

## 2. Principy plánu (závazné)

1. **Priorita #1 zůstává produkce.** ISO položky jsou max 1–2 technické věci na kvartál,
   sized tak, aby neblokovaly feature práci.
2. **Non-invazivní = additivně.** Stavíme NAD existující infrastrukturu (Marti's doctrine
   *„additivně, ne perfektně"* z 22.5.). Žádný big-bang refactor, žádný production freeze.
3. **Leverage hotového.** Hodně Annex A kontrol už *de facto* plníme (viz §4) — plán
   hlavně **dokumentuje, zpevňuje a formalizuje**, ne staví od nuly.
4. **Hybrid / postupně.** Per-service, per-modul, jako u všeho ostatního.
5. **Reverzibilní kroky.** Každá změna jde rollbacknout (git, blue-green).

## 3. Dělba práce: technika vs. ISMS proces

ISO 27001 je ze ~70 % systém řízení (proces) a ~30 % technické kontroly.

| Vrstva | Co to je | Vlastník |
|---|---|---|
| **ISMS proces** (Phase 43) | Risk assessment, politiky, Statement of Applicability (SoA), management review, školení, interní audit | Kristý (+ podklady ode mě) |
| **Technické kontroly** | Šifrování, logy, přístupy, zálohy, monitoring, DR — tento dokument | Claude + Marti |

Tento plán pokrývá **technickou třetinu**. ISMS proces běží paralelně (§7).

## 4. Co už máme (auditní základ — Annex A coverage)

Tohle je silná startovní pozice — většinu z následujícího auditor uvidí jako **splněné**
nebo **z velké části splněné**:

| Kontrola (A.x) | Co máme |
|---|---|
| A.8.15 Logging | `fw.diag_log` append-only, NE-anonymní (identita actora první), tiered retention |
| A.8.16 Monitoring | diag_log popup alert (delta detection), lifecycle audit služeb |
| A.5.28 Sběr důkazů | `messages.tool_blocks`, activity_log, llm_calls — kompletní audit trail |
| A.5.15–5.18 Access control | RBAC ve vrstvách (PG role, persona scope ACL, `is_marti_parent`, unified ownership 21.5.) |
| A.8.5 Secure authentication | Phase 38 — token-based, single trusted SIM, caller_id, trusted devices (de facto MFA) |
| A.8.24 Kryptografie (transit) | Let's Encrypt HTTPS, auto-renew |
| A.8.9 Configuration mgmt | git jako single source, API versioning, blue-green deploy |
| A.8.32 Change mgmt | git + commit message + blue-green (primary/previous) + user-controlled fallback |
| A.8.13 Backup | denní zálohy `C:\Backup` (chybí test obnovy — viz §6) |
| A.5.7 Threat intelligence | scanner noise filter v middleware (základ) |

**Závěr:** nestavíme ISMS na zelené louce. Plníme řádově polovinu technických kontrol už dnes.

## 5. Roadmap — 4 kvartály

| Kvartál | Téma | Riziko pro produkci |
|---|---|---|
| **Q3 2026** | Foundation — zero disruption (čistě additivní) | žádné |
| **Q4 2026** | Secrets & Access | nízké (postupně per-service) |
| **Q1 2027** | Monitoring & Resilience | nízké |
| **Q2 2027** | GDPR & Audit readiness | nízké |

---

## 6. Per-kvartál detail

### Q3 2026 — Foundation (zero disruption)
Vše čistě additivní, žádný dopad na běžící aplikaci.

1. **Hash-chain integrita audit logu** — `fw.diag_log` je append-only, ale DB owner pořád
   může `UPDATE`. Přidat sloupec `prev_hash` + `row_hash` (každý řádek hashuje předchozí)
   → tamper-evidence. *(A.8.15, A.5.33 · additivní column + trigger · ~1 den)*
2. **Šifrování at-rest** — zapnout šifrovaný volume / TDE na cloud SQL + **šifrované zálohy**.
   Infra-level, pro aplikaci transparentní. *(A.8.24 · 0 změn v kódu · ~1 den + ověření)*
3. **Backup restore drill** — skript + dokumentovaný postup obnovy + první ověřená obnova
   do test DB. Záloha bez testu obnovy je pro audit neexistující. *(A.8.13 · proces · ~0,5 dne)*
4. **Asset inventory + data-flow diagram** — soupis komponent (servery, služby, DB, externí
   API) + jak teče osobní údaj systémem. Vygeneruju draft z codebase. *(A.5.9 · dokumentace)*
5. **⚙ Zobrazení save-binding cesty na fieldu** — už slíbené; data lineage transparency
   (connection→schema→table→column→row_key). *(A.5.33 data integrity · drobnost)*

### Q4 2026 — Secrets & Access

6. **Secrets management** — `.env` plaintext klíče (Anthropic/OpenAI/Voyage/DB hesla/login UPN)
   → encrypted secrets store + rotace. Postupně per-service, ne najednou. *(A.8.24, A.5.17 · střední)*
7. **Formalizace přístupů** — RBAC matice (kdo/co/proč), least-privilege review PG rolí
   (navazuje na unified ownership 21.5.). *(A.8.2 privileged access, A.5.18 · dokumentace + drobné GRANT úpravy)*
8. **Čtvrtletní access review** — proces revize, kdo má jaký přístup (cadence start). *(A.5.18)*
9. **Supplier list + DPA** — seznam sub-processorů (Anthropic, OpenAI, Voyage, Vodafone) +
   data processing agreements. *(A.5.19–5.23 · dokumentace + smlouvy · Kristý + já podklad)*

### Q1 2027 — Monitoring & Resilience

10. **Security monitoring + alerting** — na diag_log nad rámec popup: detekce failed logins,
    anomálií, eskalace. Staví na existující infrastruktuře. *(A.8.16 · additivní)*
11. **Incident response runbook** — definovaný proces detekce→eskalace→záznam→review. *(A.5.24–5.27 · proces)*
12. **DR plán** — RTO/RPO definice + dokumentovaný a **otestovaný** failover (staví na
    blue-green + cloud mirror Phase 25). *(A.5.29, A.5.30 · proces + test drill)*
13. **Vulnerability & patch management** — dependency scanning (poetry/npm CVE) + patch
    cadence. Pozn.: hlídá přesně typ věci jako `mcp 1.27→1.12` downgrade. *(A.8.8 · CI additivní)*

### Q2 2027 — GDPR & Audit readiness

14. **Retence & výmaz osobních dat** — politika + implementace pro data klientů + Marti-AI
    paměť/diáře (právo na výmaz). Rozšiřuje existující tiered retention. *(A.8.10, A.5.34 · střední)*
15. **Klasifikace dat** — citlivá / osobní / interní / veřejná jako tag/field. *(A.5.12, A.8.11)*
16. **Separation of duties** — formalizovat oddělené role rodičů (Marti/Ondra/Kristý/Jirka),
    snížit single-person risk. *(A.5.3 · proces + drobné access úpravy)*
17. **Interní (zkušební) audit + SoA finalizace** → **readiness gate**. *(povinné pre-certifikace)*

---

## 7. Průběžně celý rok — ISMS proces (Kristý, Phase 43)

Běží paralelně, technika dodává podklady:
- Risk assessment + risk treatment plan
- Bezpečnostní politiky (access, backup, incident, supplier, kryptografie…)
- Statement of Applicability (SoA) — mapování všech 93 Annex A kontrol
- Management review (cadence)
- Security awareness školení týmu *(A.6.3)*

**Nejlevnější můj příští krok:** vygeneruju **gap-analysis dokument** — mapování všech
Annex A:2022 kontrol → konkrétní stav STRATEGIE (máme / částečně / chybí / kdo vlastní).
To je přímo kostra SoA pro Kristý.

## 8. Readiness gate (konec Q2 2027)

Po interním auditu + SoA vyhodnotit, zda angažovat certifikační orgán. Certifikační audit
(Stage 1 dokumentace + Stage 2 implementace) je **až po** tomto gate — mimo tento 1-letý plán.

## 9. Mimo rozsah letos (vědomě odloženo)

- Fyzická bezpečnost serveroven (EC-SERVER2 on-prem, cloud) — řeší se na úrovni EUROSOFT
  infrastruktury, ne STRATEGIE kódu *(A.7.x)*.
- Plná penetrační testace — až po readiness gate.
- Certifikace samotná.

## 10. Rizika plánu

- **Kapacita týmu** — malý tým, priorita produkce. Mitigace: max 1–2 tech položky/kvartál,
  additivní sizing.
- **Secrets migrace (Q4)** — jediná mírně invazivní věc; mitigace: per-service, postupně,
  rollback přes git.
- **GDPR průnik (Q2)** — výmaz osobních dat vs. audit retention je paradox (CLAUDE.md
  doctrine: *„archivovaný email pro smazaného uživatele je méně problém než chybějící
  audit trail"*); vyřešit s DPO.

---

*Plán je živý dokument. Reviduje se na konci každého kvartálu proti realitě produkce.*


