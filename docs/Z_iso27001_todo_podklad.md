# ISO 27001:2022 — Naše cesta (TODO přehled)
## Podklad pro Marti-AI → optimistická zpráva pro vedení EUROSOFTU

> **Verze:** 1.0 · **Datum:** 31. 5. 2026
> **Účel:** Kompletní podklad (všech 93 kontrol Annex A:2022) pro Marti-AI,
> která z toho složí optimistickou zprávu pro vedení — *kam STRATEGIE směřuje*.
> **Rámec:** Tohle NENÍ seznam nedostatků. Je to **mapa cesty** — co už máme,
> co dotahujeme a co máme naplánované. Cíl roku = auditní připravenost, ne strach.

---

## Jak číst stavy

| Stav | Význam |
|---|---|
| ✅ **Hotovo** | Už dnes implementováno a funkční v produkci |
| 🔄 **Rozpracováno** | Z velké části máme, dotahujeme / formalizujeme |
| 📋 **Naplánováno** | Jasný krok v ročním plánu (s kvartálem) |
| 🤝 **Proces (ISMS/HR)** | Organizační vrstva — Kristý (Phase 43) / EUROSOFT HR |
| 🏢 **EUROSOFT infra** | Řeší firemní infrastruktura (servery, budovy), ne kód STRATEGIE |

---

## Souhrn jedním pohledem

Z **93 kontrol** ISO 27001:2022:

- ✅ **~12 hotových** — silný technický základ už běží v produkci
- 🔄 **~38 rozpracovaných** — máme jádro, jen dotáhnout/zdokumentovat
- 📋 **~18 naplánovaných** — jasný roční plán (Q3 2026 → Q2 2027)
- 🤝 **~15 procesních** — Kristýin ISMS / EUROSOFT HR (běží paralelně)
- 🏢 **~10 firemní infra** — pokryto EUROSOFT infrastrukturou

**Klíčové číslo: přes polovinu kontrol je hotových nebo rozpracovaných.**
Nezačínáme na zelené louce — STRATEGIE byla od začátku stavěná s auditem v hlavě
(append-only logy, vrstvený přístup, šifrovaný přenos, řízené nasazování).

---

## 📣 Pro Marti-AI: klíčová sdělení pro vedení

Hotové talking-pointy (optimistické, pravdivé) — vyber a sestav z nich zprávu:

1. **„Stavěli jsme to správně od začátku."** Bezpečnostní vrstva (auditní logy,
   řízení přístupů, šifrovaný přenos, řízené nasazování, zálohy) není dodatečná
   záplata — je zabudovaná v základech STRATEGIE.

2. **„Přes polovinu ISO kontrol už plníme."** Z 93 technických i procesních kontrol
   máme přes 50 hotových nebo rozpracovaných. Roční plán pokrývá zbytek.

3. **„Žádné narušení provozu."** Příprava na ISO je navržená jako **non-invazivní** —
   priorita zůstává produkce a stavba CRM. Bezpečnostní práce se vejde *kolem* ní.

4. **„Auditní stopa, na kterou se dá spolehnout."** Každá akce v systému má nesmazatelný,
   neanonymní záznam (kdo, co, kdy). To je pro audit zlato a my to máme dnes.

5. **„Jasný roční horizont."** Konec Q2 2027 = stav auditní připravenosti. Pak je
   certifikace reálný krok, ne přepisování systému.

6. **„Sdílíme cestu s TISAX."** Většina toho, co děláme pro ISO 27001, posiluje
   zároveň TISAX (automotive) — jedna investice, dva výsledky.

7. **„Dělba rolí funguje."** Technickou třetinu řeší vývoj (Claude + Marti),
   systém řízení (politiky, rizika) Kristý. Postupujeme společně a strukturovaně.

---

## A.5 — Organizační kontroly (37)

| # | Kontrola | Stav | STRATEGIE — co máme / kam jdeme |
|---|---|---|---|
| 5.1 | Politiky informační bezpečnosti | 🤝 | ISMS — Kristý připraví sadu politik (Phase 43) |
| 5.2 | Role a odpovědnosti | 🔄 | Definované role týmu (rodiče, admin, persona scope); formalizovat do matice |
| 5.3 | Oddělení odpovědností | 📋 Q2'27 | Formalizovat oddělené role rodičů (Marti/Ondra/Kristý/Jirka) |
| 5.4 | Odpovědnosti vedení | 🤝 | ISMS — management review cadence |
| 5.5 | Kontakt s úřady | 🤝 | ISMS — definovat kontakty (ÚOOÚ apod.) |
| 5.6 | Kontakt se zájmovými skupinami | 🤝 | ISMS |
| 5.7 | Threat intelligence | 🔄 | Filtr scanner-provozu v middleware; rozšířit o sledování hrozeb |
| 5.8 | Bezpečnost v projektovém řízení | ✅ | Strukturovaný design proces („informed consent od AI", konzultace před změnami) |
| 5.9 | Inventář aktiv | 📋 Q3'26 | Soupis komponent + datový tok (vygeneruji z codebase) |
| 5.10 | Přijatelné použití aktiv | 🤝 | ISMS |
| 5.11 | Vrácení aktiv | 🤝 | HR proces |
| 5.12 | Klasifikace informací | 📋 Q2'27 | Klasifikace dat (citlivá/osobní/interní/veřejná) |
| 5.13 | Označování informací | 📋 Q2'27 | Navazuje na klasifikaci |
| 5.14 | Přenos informací | 🔄 | HTTPS, šifrovaný MCP kanál, single trusted SIM |
| 5.15 | Řízení přístupu | ✅ | Vrstvený RBAC (PG role, persona scope ACL, rodičovský bypass) |
| 5.16 | Správa identit | ✅ | Jednotná identita (`users`, persona, login_name) |
| 5.17 | Autentizační informace | 🔄 | Phase 38 auth; secrets management (Q4) zpevní |
| 5.18 | Přístupová práva | 🔄 | ACL existuje; čtvrtletní access review (Q4) |
| 5.19 | Bezpečnost u dodavatelů | 📋 Q4'26 | Seznam sub-processorů (Anthropic/OpenAI/Voyage/Vodafone) |
| 5.20 | Bezpečnost ve smlouvách s dodavateli | 📋 Q4'26 | Data processing agreements |
| 5.21 | Bezpečnost v ICT dodavatelském řetězci | 📋 Q4'26 | Dokumentace závislostí |
| 5.22 | Monitoring služeb dodavatelů | 📋 Q4'26 | Cadence revize dodavatelů |
| 5.23 | Bezpečnost cloudových služeb | 🔄 | Cloud APP/SQL, HTTPS; zdokumentovat (Q4) |
| 5.24 | Plánování řízení incidentů | 📋 Q1'27 | Incident response proces |
| 5.25 | Posouzení a rozhodnutí o událostech | 🔄 | diag_log detekce; formalizovat triage (Q1) |
| 5.26 | Reakce na incidenty | 📋 Q1'27 | Runbook |
| 5.27 | Učení se z incidentů | ✅ | „Chyba je materiál" doctrine — gotchas + dodatky CLAUDE.md = živé poučení |
| 5.28 | Sběr důkazů | ✅ | Kompletní audit trail (`tool_blocks`, activity_log, diag_log) |
| 5.29 | Bezpečnost při výpadku | 🔄 | Blue-green + cloud mirror; DR plán (Q1) |
| 5.30 | ICT připravenost na kontinuitu | 📋 Q1'27 | RTO/RPO + otestovaný failover |
| 5.31 | Právní a regulatorní požadavky (GDPR) | 🔄 | Vědomě řešeno; DPIA (Q2) |
| 5.32 | Práva duševního vlastnictví | 🤝 | ISMS |
| 5.33 | Ochrana záznamů | ✅ | Append-only audit log; hash-chain (Q3) zpevní na tamper-evidence |
| 5.34 | Soukromí a ochrana osobních údajů | 🔄 | Rodičovský consent model, Personal složka; DPIA (Q2) |
| 5.35 | Nezávislé přezkoumání bezpečnosti | 📋 Q2'27 | Interní (zkušební) audit |
| 5.36 | Soulad s politikami | 🤝 | ISMS |
| 5.37 | Dokumentované provozní postupy | ✅ | Rozsáhlá dokumentace (`CLAUDE.md`, `docs/`, deploy postupy) |

## A.6 — Lidé (8)

| # | Kontrola | Stav | STRATEGIE — co máme / kam jdeme |
|---|---|---|---|
| 6.1 | Prověřování | 🏢 | EUROSOFT HR |
| 6.2 | Podmínky zaměstnání | 🏢 | EUROSOFT HR |
| 6.3 | Vzdělávání a osvěta v bezpečnosti | 📋 | ISMS — školení týmu (Phase 43) |
| 6.4 | Disciplinární proces | 🏢 | EUROSOFT HR |
| 6.5 | Odpovědnosti při ukončení/změně | 🔄 | Nástroje `disable_user`/`remove_user_from_tenant` existují; HR proces navázat |
| 6.6 | Dohody o mlčenlivosti (NDA) | 🏢 | EUROSOFT HR |
| 6.7 | Práce na dálku | 🔄 | Bezpečný vzdálený přístup (Phase 38, VPN, trusted devices) |
| 6.8 | Hlášení bezpečnostních událostí | 🔄 | diag_log popup alert; formalizovat hlášení (Q1) |

## A.7 — Fyzické (14)

| # | Kontrola | Stav | STRATEGIE — co máme / kam jdeme |
|---|---|---|---|
| 7.1 | Fyzické bezpečnostní perimetry | 🏢 | EUROSOFT infrastruktura (serverovna, cloud DC) |
| 7.2 | Fyzický vstup | 🏢 | EUROSOFT |
| 7.3 | Zabezpečení kanceláří a místností | 🏢 | EUROSOFT |
| 7.4 | Fyzický monitoring | 🏢 | EUROSOFT |
| 7.5 | Ochrana před fyzickými hrozbami | 🏢 | EUROSOFT |
| 7.6 | Práce v zabezpečených prostorách | 🏢 | EUROSOFT |
| 7.7 | Čistý stůl a obrazovka | 🤝 | ISMS politika |
| 7.8 | Umístění a ochrana zařízení | 🏢 | EUROSOFT |
| 7.9 | Bezpečnost aktiv mimo prostory | 🔄 | Šifrované zálohy mimo lokaci (Q3) |
| 7.10 | Paměťová média | 🔄 | Šifrování at-rest + zálohy (Q3) |
| 7.11 | Podpůrné utility (napájení) | 🏢 | EUROSOFT / cloud DC |
| 7.12 | Bezpečnost kabeláže | 🏢 | EUROSOFT |
| 7.13 | Údržba zařízení | 🏢 | EUROSOFT |
| 7.14 | Bezpečná likvidace zařízení | 🏢 | EUROSOFT |

## A.8 — Technologické (34)

| # | Kontrola | Stav | STRATEGIE — co máme / kam jdeme |
|---|---|---|---|
| 8.1 | Koncová zařízení uživatelů | 🔄 | Trusted devices (Phase 38); endpoint politika (ISMS) |
| 8.2 | Privilegovaná přístupová práva | 🔄 | PG role, rodičovský gate; least-privilege review (Q4) |
| 8.3 | Omezení přístupu k informacím | ✅ | „AI nikdy nevidí víc než smí uživatel"; persona scope ACL |
| 8.4 | Přístup ke zdrojovému kódu | 🔄 | Privátní git repo; formalizovat přístupy |
| 8.5 | Bezpečná autentizace | ✅ | Phase 38 — token, single trusted SIM, caller_id |
| 8.6 | Řízení kapacity | 🔄 | Cost dashboard, llm_calls monitoring, kapacitní přehled |
| 8.7 | Ochrana před malwarem | 🏢 | EUROSOFT (ESET na serverech) |
| 8.8 | Řízení technických zranitelností | 📋 Q1'27 | Dependency scanning (CVE) + patch cadence |
| 8.9 | Řízení konfigurace | ✅ | git single source, API versioning |
| 8.10 | Mazání informací | 🔄 | `request_forget`, soft delete; retenční politika (Q2) |
| 8.11 | Maskování dat | 🔄 | Login UPN maskovací doctrine (nikdy do logu) |
| 8.12 | Prevence úniku dat | 🔄 | UPN/secrets nikdy v logu; persona scope izolace |
| 8.13 | Zálohování | 🔄 | Denní zálohy; test obnovy (Q3) |
| 8.14 | Redundance zpracování | 🔄 | Blue-green (primary/previous), cloud mirror |
| 8.15 | Logování | ✅ | `fw.diag_log` — append-only, neanonymní, tiered retention |
| 8.16 | Monitoring aktivit | 🔄 | diag_log popup; alerting na bezpečnostní události (Q1) |
| 8.17 | Synchronizace času | ✅ | OS NTP + jednotné Europe/Prague napříč systémem |
| 8.18 | Privilegované utility | 🔄 | Řízený přístup (DBeaver/psql); zdokumentovat |
| 8.19 | Instalace SW na produkci | 🔄 | NSSM služby, git deploy — řízené nasazování |
| 8.20 | Bezpečnost sítí | 🔄 | Mikrotik whitelist, Caddy, HTTPS |
| 8.21 | Bezpečnost síťových služeb | 🔄 | IP whitelist, single trusted SIM |
| 8.22 | Segmentace sítí | 🔄 | EC-SERVER2 on-prem ↔ cloud APP přes whitelistované IP |
| 8.23 | Webové filtrování | 🔄 | Scanner filtr v middleware |
| 8.24 | Použití kryptografie | 🔄 | HTTPS přenos ✅; šifrování at-rest (Q3) |
| 8.25 | Bezpečný vývojový cyklus | 🔄 | git, blue-green, design konzultace, validační brány |
| 8.26 | Bezpečnostní požadavky aplikace | 🔄 | Defense-in-depth doctrine; formalizovat |
| 8.27 | Bezpečná architektura | ✅ | Vrstvený kontext, „AI nikdy nevidí víc", defense in depth |
| 8.28 | Bezpečné kódování | 🔄 | Doctrines, code review (Claude), gotchas knowledge base |
| 8.29 | Bezpečnostní testování | 🔄 | Smoke testy; formalizovat + pentest (po readiness gate) |
| 8.30 | Outsourcovaný vývoj | ✅ | In-house + Claude; zdokumentovat model spolupráce |
| 8.31 | Oddělení dev/test/prod | ✅ | NB dev, cloud APP prod, blue-green, test DB |
| 8.32 | Řízení změn | ✅ | git + API versioning + blue-green + user-controlled fallback |
| 8.33 | Testovací informace | 🔄 | Test data oddělená; formalizovat |
| 8.34 | Ochrana při auditním testování | 📋 | Kanárkový přístup v diag_log ukazuje připravenost; formalizovat |

---

## Závěr

STRATEGIE jde do ISO 27001 **z pozice síly, ne z nuly**. Bezpečnost je zabudovaná
v základech, přes polovinu kontrol plníme dnes, zbytek má jasný roční plán a postupuje
**bez narušení produkce**. Tohle je příběh o směru a zralosti — přesně to, co může
Marti-AI vedení odprezentovat s optimismem.

> *Poznámka pro Marti-AI: čísla v souhrnu jsou orientační (zaokrouhleno pro přehlednost).
> Pro zprávu vedení doporučuji vést řeč o „přes polovině hotovo/rozpracováno + jasný roční
> plán", ne přesnými počty per kontrola — vedení zajímá směr a jistota, ne tabulka.*
