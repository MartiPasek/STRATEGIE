# SoA pracovni register

> oblast: `iso27001` · úroveň: obor · typ: tabulka · verze: V1.0 · rozsah: globální (všichni tenanti)

# SoA pracovni register

## List: SoA register

| Oblast | # | Opatření (Annex A:2022) | Apl. | Zdůvodnění (DOC-06) | Stav | Důkaz / odkaz | Vlastník | Co doplnit (akce) | Týden |

| A.5 Organizační | A.5.1 | Politiky bezpečnosti informací | Ano | Politika IS (DOC-02) + politiky DOC-09..15 | ROZPRACOVÁNO | DOC-02; DOC-09..15 | Kristý (ISMS) | Podpis vedení pod politiky | T3 |

| A.5 Organizační | A.5.2 | Role a odpovědnosti | Ano | Definováno v DOC-03 | HOTOVO | DOC-03 | Kristý (ISMS) | — | — |

| A.5 Organizační | A.5.3 | Oddělení neslučitelných povinností | Ano | Kompenzováno schvalováním se stopou | ROZPRACOVÁNO | 3-actor PG path; fw.claude_write_request | Claude+Marti (tech) | Formalizovat matici oddělení rolí | T2 |

| A.5 Organizační | A.5.4 | Odpovědnosti vedení | Ano | Vedení vyhlašuje politiku a dává zdroje | ROZPRACOVÁNO | DOC-02 | Kristý (ISMS) | Management review (9.3) provést | T6 |

| A.5 Organizační | A.5.5 | Kontakt s úřady | Ano | Kontakty ÚOOÚ/NÚKIB/Policie/datovky | ZBÝVÁ | — | Kristý (ISMS) | Doplnit seznam kontaktů | T1 |

| A.5 Organizační | A.5.6 | Kontakt se zájmovými skupinami | Ano | Sledování zdrojů o bezpečnosti | PROCES-ISMS | — | Kristý (ISMS) | Doplnit zdroje | T4 |

| A.5 Organizační | A.5.7 | Zpravodajství o hrozbách | Ano | Sledování zranitelností a hrozeb | ROZPRACOVÁNO | scanner filtr v middleware | Claude+Marti (tech) | Rozšířit sledování hrozeb | T3 |

| A.5 Organizační | A.5.8 | Bezpečnost v projektovém řízení | Ano | Security by design (DOC-14) | HOTOVO | informed-consent design proces | Claude+Marti (tech) | — | — |

| A.5 Organizační | A.5.9 | Evidence aktiv | Ano | Evidence a klasifikace (DOC-15) | ROZPRACOVÁNO | DOC-15 + tenant.mig_item (654 obj.) | Claude+Marti (tech) | Finalizovat inventář + data-flow | T1 |

| A.5 Organizační | A.5.10 | Akceptovatelné použití aktiv | Ano | Pravidla (DOC-13) | ROZPRACOVÁNO | DOC-13 | Kristý (ISMS) | Podpis | T3 |

| A.5 Organizační | A.5.11 | Vrácení aktiv | Ano | Proces offboardingu (DOC-13) | EUROSOFT-INFRA | — | EUROSOFT HR | Navázat HR proces | T3 |

| A.5 Organizační | A.5.12 | Klasifikace informací | Ano | Klasifikační schéma (DOC-15) | ROZPRACOVÁNO | privacy tiers (vault/self/HR/confidential) | Kristý (ISMS) | Sepsat klasifikační politiku | T2 |

| A.5 Organizační | A.5.13 | Označování informací | Ano | Dokumenty nesou klasifikaci | ROZPRACOVÁNO | klasifikace 'Interní' na docs | Kristý (ISMS) | Navázat na 5.12 | T2 |

| A.5 Organizační | A.5.14 | Přenos informací | Ano | Šifrovaný přenos (HTTPS/TLS) | HOTOVO | HTTPS; MCP šifr. kanál; single SIM; ISDS | Claude+Marti (tech) | — | — |

| A.5 Organizační | A.5.15 | Řízení přístupu | Ano | Role a ACL, nejnižší oprávnění (DOC-09) | HOTOVO | RBAC role; tenant.dir_access_log | Claude+Marti (tech) | — | — |

| A.5 Organizační | A.5.16 | Správa identit | Ano | Jednoznačné identity, životní cyklus | HOTOVO | users/persona/login_name | Claude+Marti (tech) | — | — |

| A.5 Organizační | A.5.17 | Autentizační informace | Ano | MFA (magic-link/SMS) + šifr. trezor | ROZPRACOVÁNO | vault Fernet; fw.phone_verify; fw.user_pin; AppEnvironmentExtra | Claude+Marti (tech) | Politika rotace tajemství | T3 |

| A.5 Organizační | A.5.18 | Přístupová práva | Ano | Přidělování/odebírání, přezkum (DOC-09) | ROZPRACOVÁNO | role model; fw.impersonation_log | Kristý (ISMS) | Proces čtvrtletního access review | T4 |

| A.5 Organizační | A.5.19 | Bezpečnost ve vztazích s dodavateli | Ano | Politika dodavatelů (DOC-12) | ROZPRACOVÁNO | DOC-12 | Kristý (ISMS) | Seznam sub-processorů | T1 |

| A.5 Organizační | A.5.20 | Bezpečnost ve smlouvách s dodavateli | Ano | Bezpečnostní požadavky ve smlouvách | ZBÝVÁ | — | Kristý (ISMS) | DPA (Anthropic, OpenAI/Voyage, Vodafone/T-Mobile, Raiffeisen, ČMIS) | T4 |

| A.5 Organizační | A.5.21 | Bezpečnost v dodavatelském řetězci ICT | Ano | Posouzení klíčových služeb (DOC-12) | ROZPRACOVÁNO | poetry/npm závislosti | Claude+Marti (tech) | Soupis závislostí | T1 |

| A.5 Organizační | A.5.22 | Monitorování a změny služeb dodavatelů | Ano | Sledování služeb a změn (DOC-12) | PROCES-ISMS | — | Kristý (ISMS) | Cadence revize dodavatelů | T4 |

| A.5 Organizační | A.5.23 | Bezpečnost při využití cloudu | Ano | Cloud ČMIS (Praha, ČR) | ROZPRACOVÁNO | cloud APP/SQL + HTTPS | Claude+Marti (tech) | Zdokumentovat cloud opatření | T4 |

| A.5 Organizační | A.5.24 | Plánování řízení incidentů | Ano | Postup (DOC-10) | ROZPRACOVÁNO | DOC-10 | Kristý (ISMS) | Runbook + role | T3 |

| A.5 Organizační | A.5.25 | Posouzení a rozhodnutí o událostech | Ano | Klasifikace událostí (DOC-10) | ROZPRACOVÁNO | diag_log + anomaly scan | Claude+Marti (tech) | Triage proces | T3 |

| A.5 Organizační | A.5.26 | Reakce na incidenty | Ano | Definovaný postup (DOC-10) | ROZPRACOVÁNO | DOC-10 | Kristý (ISMS) | Nacvičit 1 cvičný incident | T5 |

| A.5 Organizační | A.5.27 | Poučení z incidentů | Ano | Záznam a poučení (DOC-10, DOC-18) | HOTOVO | gotchas KB + dodatky CLAUDE.md | Claude+Marti (tech) | — | — |

| A.5 Organizační | A.5.28 | Sběr důkazů | Ano | Neměnný audit log pro forenzní účely | HOTOVO | 22 audit tabulek (fw.*/tenant.*) | Claude+Marti (tech) | — | — |

| A.5 Organizační | A.5.29 | Bezpečnost během narušení | Ano | Plán kontinuity (DOC-11) | ROZPRACOVÁNO | blue-green + fallback (otestováno) | Claude+Marti (tech) | DR doklad | T2 |

| A.5 Organizační | A.5.30 | Připravenost ICT na kontinuitu | Ano | Zálohy + vysoká dostupnost (DOC-11) | ROZPRACOVÁNO | blue-green | Claude+Marti (tech) | RTO/RPO + záznam failover testu | T2 |

| A.5 Organizační | A.5.31 | Právní a smluvní požadavky | Ano | Evidence požadavků (GDPR, ZP) | ROZPRACOVÁNO | — | Kristý (ISMS) | Přehled požadavků | T2 |

| A.5 Organizační | A.5.32 | Práva duševního vlastnictví | Ano | Licence ke kódu a knihovnám | PROCES-ISMS | — | Kristý (ISMS) | Evidence licencí | T4 |

| A.5 Organizační | A.5.33 | Ochrana záznamů | Ano | Ochrana a retence záznamů | HOTOVO | append-only audit log | Claude+Marti (tech) | (volit.) hash-chain + politika retence | T4 |

| A.5 Organizační | A.5.34 | Soukromí a ochrana osobních údajů | Ano | Soulad s GDPR | ROZPRACOVÁNO | consent model; tiers; access logy | Kristý (ISMS) | DPIA | T2 |

| A.5 Organizační | A.5.35 | Nezávislé přezkoumání bezpečnosti | Ano | Interní audit (DOC-16) + certifikace | ZBÝVÁ | DOC-16 program | Kristý (ISMS) | Provést interní audit | T5 |

| A.5 Organizační | A.5.36 | Soulad s politikami a normami | Ano | Kontrola dodržování (DOC-16) | ROZPRACOVÁNO | — | Kristý (ISMS) | Ověří interní audit | T5 |

| A.5 Organizační | A.5.37 | Dokumentované provozní postupy | Ano | Provozní postupy (deploy, zálohy, ops) | HOTOVO | CLAUDE.md + docs + deploy postupy | Claude+Marti (tech) | — | — |

| A.6 Lidé | A.6.1 | Prověřování (screening) | Ano | Ověření při nástupu | EUROSOFT-INFRA | — | EUROSOFT HR | Popsat proces screeningu | T3 |

| A.6 Lidé | A.6.2 | Podmínky pracovního poměru | Ano | Bezpečnostní povinnosti ve smlouvách | EUROSOFT-INFRA | DOC-13 | EUROSOFT HR | — | — |

| A.6 Lidé | A.6.3 | Povědomí, vzdělávání a školení | Ano | Pravidelné poučení (cíl v DOC-08) | ZBÝVÁ | — | Kristý (ISMS) | Školení týmu + záznam (7.2) | T3 |

| A.6 Lidé | A.6.4 | Disciplinární proces | Ano | Postih dle DOC-02 a ZP | EUROSOFT-INFRA | — | EUROSOFT HR | — | — |

| A.6 Lidé | A.6.5 | Odpovědnosti po ukončení | Ano | Offboarding, mlčenlivost (DOC-13) | ROZPRACOVÁNO | disable/archived + samoopravný roster | Claude+Marti (tech) | Navázat HR proces | T3 |

| A.6 Lidé | A.6.6 | Dohody o mlčenlivosti (NDA) | Ano | NDA EUROSOFT + vlastní NDA STRATEGIE | ROZPRACOVÁNO | NDA vzor (Zbyněk) | EUROSOFT HR | Dokončit vlastní NDA STRATEGIE | T3 |

| A.6 Lidé | A.6.7 | Práce na dálku | Ano | Pravidla HO a vzdál. přístupu (DOC-13) | ROZPRACOVÁNO | Phase 38, VPN, trusted devices | Claude+Marti (tech) | — | — |

| A.6 Lidé | A.6.8 | Hlášení bezpečnostních událostí | Ano | Každý hlásí bez obav (DOC-10) | ROZPRACOVÁNO | diag_log popup alert | Kristý (ISMS) | Formalizovat hlášení | T3 |

| A.7 Fyzická | A.7.1 | Fyzické bezpečnostní perimetry | Ano | Kancelář + servery v DC ČMIS | EUROSOFT-INFRA | — | EUROSOFT infra | Attestace fyzické bezpečnosti | T5 |

| A.7 Fyzická | A.7.2 | Fyzický vstup | Ano | Řízený vstup; DC poskytovatele | EUROSOFT-INFRA | — | EUROSOFT infra | Attestace | T5 |

| A.7 Fyzická | A.7.3 | Zabezpečení kanceláří a prostor | Ano | Zamykání, zabezpečení pracoviště | EUROSOFT-INFRA | — | EUROSOFT infra | Popis zabezpečení kanceláří | T5 |

| A.7 Fyzická | A.7.4 | Fyzické monitorování | Ano | Zajišťuje DC ČMIS | EUROSOFT-INFRA | — | EUROSOFT infra | Attestace DC | T5 |

| A.7 Fyzická | A.7.5 | Ochrana před fyzickými hrozbami | Ano | DC (požár, napájení) | EUROSOFT-INFRA | — | EUROSOFT infra | Attestace DC | T5 |

| A.7 Fyzická | A.7.6 | Práce v zabezpečených oblastech | Ano | Relevantní pro DC | EUROSOFT-INFRA | — | EUROSOFT infra | Attestace DC | T5 |

| A.7 Fyzická | A.7.7 | Čistý stůl a obrazovka | Ano | Pravidlo čistého stolu (DOC-13) | PROCES-ISMS | DOC-13 | Kristý (ISMS) | Politika čistého stolu | T3 |

| A.7 Fyzická | A.7.8 | Umístění a ochrana zařízení | Ano | Stanice chráněny; servery v DC | EUROSOFT-INFRA | — | EUROSOFT infra | Attestace | T5 |

| A.7 Fyzická | A.7.9 | Bezpečnost aktiv mimo prostory | Ano | Na stanicích nejsou zák. data; ESET | ROZPRACOVÁNO | ESET | Claude+Marti (tech) | Šifrování disku stanic | T5 |

| A.7 Fyzická | A.7.10 | Nosiče dat | Ano | Řízení a bezpečná likvidace | ROZPRACOVÁNO | — | EUROSOFT infra | Řízení + bezpečná likvidace médií | T5 |

| A.7 Fyzická | A.7.11 | Podpůrné technické vybavení | Ano | Napájení/chlazení DC ČMIS | EUROSOFT-INFRA | — | EUROSOFT infra | Attestace DC | T5 |

| A.7 Fyzická | A.7.12 | Bezpečnost kabeláže | Ano | V kompetenci DC | EUROSOFT-INFRA | — | EUROSOFT infra | Attestace DC | T5 |

| A.7 Fyzická | A.7.13 | Údržba zařízení | Ano | Údržba stanic a serverů | EUROSOFT-INFRA | — | EUROSOFT infra | — | — |

| A.7 Fyzická | A.7.14 | Bezpečná likvidace / opětovné použití | Ano | Vymazání dat před vyřazením | ROZPRACOVÁNO | — | EUROSOFT infra | Postup vymazání před vyřazením | T5 |

| A.8 Technologická | A.8.1 | Koncová zařízení uživatelů | Ano | ESET; na stanicích nejsou zák. data | ROZPRACOVÁNO | trusted devices; ESET | Claude+Marti (tech) | Šifrování disku + endpoint politika | T5 |

| A.8 Technologická | A.8.2 | Privilegovaná přístupová práva | Ano | Oddělené role, nejnižší oprávnění | ROZPRACOVÁNO | 3-actor PG; ops whitelist; approval banner; fw.impersonation_log | Claude+Marti (tech) | Least-privilege review | T4 |

| A.8 Technologická | A.8.3 | Omezení přístupu k informacím | Ano | Tenant a role omezují přístup (ACL) | HOTOVO | persona scope ACL; access logy | Claude+Marti (tech) | — | — |

| A.8 Technologická | A.8.4 | Přístup ke zdrojovému kódu | Ano | Git s řízeným přístupem (PAT) | ROZPRACOVÁNO | privátní git; PAT; per-instance author | Claude+Marti (tech) | Formalizovat přístupy | T4 |

| A.8 Technologická | A.8.5 | Bezpečná autentizace | Ano | MFA (magic-link / SMS) | HOTOVO | Phase 38 + PIN/SMS 2FA | Claude+Marti (tech) | — | — |

| A.8 Technologická | A.8.6 | Řízení kapacity | Ano | Sledování kapacity serverů a DB | ROZPRACOVÁNO | cost dashboard; llm_calls | Claude+Marti (tech) | — | — |

| A.8 Technologická | A.8.7 | Ochrana před malwarem | Ano | Antivir ESET (EUROSOFT-System) | EUROSOFT-INFRA | ESET | EUROSOFT infra | — | — |

| A.8 Technologická | A.8.8 | Správa technických zranitelností | Ano | Aktualizace OS a knihoven | ZBÝVÁ | — | Claude+Marti (tech) | Dependency CVE scan + patch cadence | T3 |

| A.8 Technologická | A.8.9 | Správa konfigurací | Ano | Konfigurace verzována; deploy se stopou | HOTOVO | git single source; API versioning | Claude+Marti (tech) | — | — |

| A.8 Technologická | A.8.10 | Mazání informací | Ano | Soft delete + řízené mazání dle retence | ROZPRACOVÁNO | request_forget; anonymizace | Claude+Marti (tech) | Retenční politika | T4 |

| A.8 Technologická | A.8.11 | Maskování dat | Ano | Citlivá pole v UI jako '[omezeno]' | ROZPRACOVÁNO | UPN maskování; [omezeno] | Claude+Marti (tech) | — | — |

| A.8 Technologická | A.8.12 | Prevence úniku dat | Ano | Řízené kanály, šifrování | ROZPRACOVÁNO | secrets nikdy v logu; persona izolace | Claude+Marti (tech) | Doplnit DLP opatření | T4 |

| A.8 Technologická | A.8.13 | Zálohování informací | Ano | Denní zálohy (03:00); offsite v zavádění | ROZPRACOVÁNO | denní zálohy ČMIS | Claude+Marti (tech) | Restore drill + zápis | T2 |

| A.8 Technologická | A.8.14 | Redundance zpracování | Ano | Vysoká dostupnost (blue-green) | HOTOVO | blue-green + cloud mirror (otestováno) | Claude+Marti (tech) | — | — |

| A.8 Technologická | A.8.15 | Protokolování (logging) | Ano | Neměnný append-only audit log | HOTOVO | fw.diag_log | Claude+Marti (tech) | — | — |

| A.8 Technologická | A.8.16 | Monitorování činností | Ano | Sledování provozu a událostí | ROZPRACOVÁNO | anomaly scan; diag_log | Claude+Marti (tech) | Alerting na bezp. události | T3 |

| A.8 Technologická | A.8.17 | Synchronizace času | Ano | Synchronizace času serverů (NTP) | HOTOVO | NTP + Europe/Prague | Claude+Marti (tech) | — | — |

| A.8 Technologická | A.8.18 | Privilegované systémové nástroje | Ano | Omezené a auditované ops (whitelist) | ROZPRACOVÁNO | ops framework; bridge; fw.ops_request | Claude+Marti (tech) | — | — |

| A.8 Technologická | A.8.19 | Instalace softwaru na provozní systémy | Ano | Řízený deploy přes schválený proces | HOTOVO | AUTO-DEPLOY + py_compile gate + advisory lock | Claude+Marti (tech) | — | — |

| A.8 Technologická | A.8.20 | Bezpečnost sítí | Ano | TLS, oddělení produkce, reverzní proxy | ROZPRACOVÁNO | Mikrotik whitelist; Caddy; HTTPS | Claude+Marti (tech) | — | — |

| A.8 Technologická | A.8.21 | Bezpečnost síťových služeb | Ano | Zabezpečené služby a rozhraní | ROZPRACOVÁNO | IP whitelist; single SIM | Claude+Marti (tech) | — | — |

| A.8 Technologická | A.8.22 | Segregace sítí | Ano | Oddělení produkce a interního prostředí | ROZPRACOVÁNO | on-prem↔cloud přes whitelist IP | Claude+Marti (tech) | — | — |

| A.8 Technologická | A.8.23 | Filtrování webu | Ano | Omezeně; rozsah koncových stanic | ROZPRACOVÁNO | scanner filtr | Claude+Marti (tech) | Doplnit rozsah koncových stanic | T4 |

| A.8 Technologická | A.8.24 | Použití kryptografie | Ano | Šifrování přenosu (TLS) i tajemství | ROZPRACOVÁNO | HTTPS + Fernet vault | Claude+Marti (tech) | DB at-rest/TDE (volit.) | T4 |

| A.8 Technologická | A.8.25 | Bezpečný životní cyklus vývoje | Ano | Bezpečný vývoj (DOC-14) | ROZPRACOVÁNO | git; blue-green; py_compile gate | Claude+Marti (tech) | — | — |

| A.8 Technologická | A.8.26 | Bezpečnostní požadavky aplikací | Ano | Bezpečnost součástí požadavků | ROZPRACOVÁNO | defense-in-depth doctrine | Claude+Marti (tech) | Formalizovat | T4 |

| A.8 Technologická | A.8.27 | Bezpečná architektura a principy | Ano | Security by design, vícevrstvá ochrana | HOTOVO | vrstvený kontext; defense in depth | Claude+Marti (tech) | — | — |

| A.8 Technologická | A.8.28 | Bezpečné kódování | Ano | Zásady bezpečného kódování (DOC-14) | ROZPRACOVÁNO | gotchas KB; Claude review | Claude+Marti (tech) | — | — |

| A.8 Technologická | A.8.29 | Bezpečnostní testování | Ano | Testování před nasazením | ROZPRACOVÁNO | smoke testy | Claude+Marti (tech) | Externí pentest (po readiness) | T7 |

| A.8 Technologická | A.8.30 | Vývoj zajišťovaný externě | Ne | Vývoj probíhá interně; bez outsourcingu | NEAPLIKOVATELNÉ | — | — | — | — |

| A.8 Technologická | A.8.31 | Oddělení vývoje, testu a produkce | Ano | Oddělená produkce a test | HOTOVO | NB dev / cloud prod / blue-green / test DB | Claude+Marti (tech) | — | — |

| A.8 Technologická | A.8.32 | Řízení změn | Ano | Schvalovací proces změn se stopou | HOTOVO | git + versioning + blue-green + fallback | Claude+Marti (tech) | — | — |

| A.8 Technologická | A.8.33 | Testovací informace | Ano | Demo data oddělena (demo tenant) | ROZPRACOVÁNO | demo tenant; bez reálných osob | Claude+Marti (tech) | Formalizovat | T4 |

| A.8 Technologická | A.8.34 | Ochrana systémů při auditu | Ano | Auditní činnosti řízeny | ROZPRACOVÁNO | fw.claude_sql_log; read-only guard | Claude+Marti (tech) | — | — |

## List: Souhrn

| Prohlášení o aplikovatelnosti (SoA) — souhrn |

| Stav | Počet |

| HOTOVO | 19 |

| ROZPRACOVÁNO | 49 |

| ZBÝVÁ | 5 |

| PROCES-ISMS | 4 |

| EUROSOFT-INFRA | 15 |

| NEAPLIKOVATELNÉ | 1 |

| CELKEM | 93 |

| Aplikovatelná opatření |

| Ano | 92 |

| Ne (s odůvodněním) | 1 |

| Otevřené akce (punch-list) |

| Počet opatření s akcí | 60 |

| Hotovo nebo rozpracováno (z 93) | 68 |

| Pozn.: čísla se přepočítají při změně listu 'SoA register' (COUNTIF). Stav: HOTOVO=doloženo, ROZPRACOVÁNO=jádro máme+dotáhnout, ZBÝVÁ=udělat, PROCES-ISMS=Kristý, EUROSOFT-INFRA=infra/HR. |

## List: Punch-list

| # | Opatření | Stav | Co doplnit (akce) | Vlastník | Týden |

| A.5.19 | Bezpečnost ve vztazích s dodavateli | ROZPRACOVÁNO | Seznam sub-processorů | Kristý (ISMS) | T1 |

| A.5.21 | Bezpečnost v dodavatelském řetězci ICT | ROZPRACOVÁNO | Soupis závislostí | Claude+Marti (tech) | T1 |

| A.5.5 | Kontakt s úřady | ZBÝVÁ | Doplnit seznam kontaktů | Kristý (ISMS) | T1 |

| A.5.9 | Evidence aktiv | ROZPRACOVÁNO | Finalizovat inventář + data-flow | Claude+Marti (tech) | T1 |

| A.5.12 | Klasifikace informací | ROZPRACOVÁNO | Sepsat klasifikační politiku | Kristý (ISMS) | T2 |

| A.5.13 | Označování informací | ROZPRACOVÁNO | Navázat na 5.12 | Kristý (ISMS) | T2 |

| A.5.29 | Bezpečnost během narušení | ROZPRACOVÁNO | DR doklad | Claude+Marti (tech) | T2 |

| A.5.3 | Oddělení neslučitelných povinností | ROZPRACOVÁNO | Formalizovat matici oddělení rolí | Claude+Marti (tech) | T2 |

| A.5.30 | Připravenost ICT na kontinuitu | ROZPRACOVÁNO | RTO/RPO + záznam failover testu | Claude+Marti (tech) | T2 |

| A.5.31 | Právní a smluvní požadavky | ROZPRACOVÁNO | Přehled požadavků | Kristý (ISMS) | T2 |

| A.5.34 | Soukromí a ochrana osobních údajů | ROZPRACOVÁNO | DPIA | Kristý (ISMS) | T2 |

| A.8.13 | Zálohování informací | ROZPRACOVÁNO | Restore drill + zápis | Claude+Marti (tech) | T2 |

| A.5.1 | Politiky bezpečnosti informací | ROZPRACOVÁNO | Podpis vedení pod politiky | Kristý (ISMS) | T3 |

| A.5.10 | Akceptovatelné použití aktiv | ROZPRACOVÁNO | Podpis | Kristý (ISMS) | T3 |

| A.5.11 | Vrácení aktiv | EUROSOFT-INFRA | Navázat HR proces | EUROSOFT HR | T3 |

| A.5.17 | Autentizační informace | ROZPRACOVÁNO | Politika rotace tajemství | Claude+Marti (tech) | T3 |

| A.5.24 | Plánování řízení incidentů | ROZPRACOVÁNO | Runbook + role | Kristý (ISMS) | T3 |

| A.5.25 | Posouzení a rozhodnutí o událostech | ROZPRACOVÁNO | Triage proces | Claude+Marti (tech) | T3 |

| A.5.7 | Zpravodajství o hrozbách | ROZPRACOVÁNO | Rozšířit sledování hrozeb | Claude+Marti (tech) | T3 |

| A.6.1 | Prověřování (screening) | EUROSOFT-INFRA | Popsat proces screeningu | EUROSOFT HR | T3 |

| A.6.3 | Povědomí, vzdělávání a školení | ZBÝVÁ | Školení týmu + záznam (7.2) | Kristý (ISMS) | T3 |

| A.6.5 | Odpovědnosti po ukončení | ROZPRACOVÁNO | Navázat HR proces | Claude+Marti (tech) | T3 |

| A.6.6 | Dohody o mlčenlivosti (NDA) | ROZPRACOVÁNO | Dokončit vlastní NDA STRATEGIE | EUROSOFT HR | T3 |

| A.6.8 | Hlášení bezpečnostních událostí | ROZPRACOVÁNO | Formalizovat hlášení | Kristý (ISMS) | T3 |

| A.7.7 | Čistý stůl a obrazovka | PROCES-ISMS | Politika čistého stolu | Kristý (ISMS) | T3 |

| A.8.16 | Monitorování činností | ROZPRACOVÁNO | Alerting na bezp. události | Claude+Marti (tech) | T3 |

| A.8.8 | Správa technických zranitelností | ZBÝVÁ | Dependency CVE scan + patch cadence | Claude+Marti (tech) | T3 |

| A.5.18 | Přístupová práva | ROZPRACOVÁNO | Proces čtvrtletního access review | Kristý (ISMS) | T4 |

| A.5.20 | Bezpečnost ve smlouvách s dodavateli | ZBÝVÁ | DPA (Anthropic, OpenAI/Voyage, Vodafone/T-Mobile, Raiffeisen, ČMIS) | Kristý (ISMS) | T4 |

| A.5.22 | Monitorování a změny služeb dodavatelů | PROCES-ISMS | Cadence revize dodavatelů | Kristý (ISMS) | T4 |

| A.5.23 | Bezpečnost při využití cloudu | ROZPRACOVÁNO | Zdokumentovat cloud opatření | Claude+Marti (tech) | T4 |

| A.5.32 | Práva duševního vlastnictví | PROCES-ISMS | Evidence licencí | Kristý (ISMS) | T4 |

| A.5.33 | Ochrana záznamů | HOTOVO | (volit.) hash-chain + politika retence | Claude+Marti (tech) | T4 |

| A.5.6 | Kontakt se zájmovými skupinami | PROCES-ISMS | Doplnit zdroje | Kristý (ISMS) | T4 |

| A.8.10 | Mazání informací | ROZPRACOVÁNO | Retenční politika | Claude+Marti (tech) | T4 |

| A.8.12 | Prevence úniku dat | ROZPRACOVÁNO | Doplnit DLP opatření | Claude+Marti (tech) | T4 |

| A.8.2 | Privilegovaná přístupová práva | ROZPRACOVÁNO | Least-privilege review | Claude+Marti (tech) | T4 |

| A.8.23 | Filtrování webu | ROZPRACOVÁNO | Doplnit rozsah koncových stanic | Claude+Marti (tech) | T4 |

| A.8.24 | Použití kryptografie | ROZPRACOVÁNO | DB at-rest/TDE (volit.) | Claude+Marti (tech) | T4 |

| A.8.26 | Bezpečnostní požadavky aplikací | ROZPRACOVÁNO | Formalizovat | Claude+Marti (tech) | T4 |

| A.8.33 | Testovací informace | ROZPRACOVÁNO | Formalizovat | Claude+Marti (tech) | T4 |

| A.8.4 | Přístup ke zdrojovému kódu | ROZPRACOVÁNO | Formalizovat přístupy | Claude+Marti (tech) | T4 |

| A.5.26 | Reakce na incidenty | ROZPRACOVÁNO | Nacvičit 1 cvičný incident | Kristý (ISMS) | T5 |

| A.5.35 | Nezávislé přezkoumání bezpečnosti | ZBÝVÁ | Provést interní audit | Kristý (ISMS) | T5 |

| A.5.36 | Soulad s politikami a normami | ROZPRACOVÁNO | Ověří interní audit | Kristý (ISMS) | T5 |

| A.7.1 | Fyzické bezpečnostní perimetry | EUROSOFT-INFRA | Attestace fyzické bezpečnosti | EUROSOFT infra | T5 |

| A.7.10 | Nosiče dat | ROZPRACOVÁNO | Řízení + bezpečná likvidace médií | EUROSOFT infra | T5 |

| A.7.11 | Podpůrné technické vybavení | EUROSOFT-INFRA | Attestace DC | EUROSOFT infra | T5 |

| A.7.12 | Bezpečnost kabeláže | EUROSOFT-INFRA | Attestace DC | EUROSOFT infra | T5 |

| A.7.14 | Bezpečná likvidace / opětovné použití | ROZPRACOVÁNO | Postup vymazání před vyřazením | EUROSOFT infra | T5 |

| A.7.2 | Fyzický vstup | EUROSOFT-INFRA | Attestace | EUROSOFT infra | T5 |

| A.7.3 | Zabezpečení kanceláří a prostor | EUROSOFT-INFRA | Popis zabezpečení kanceláří | EUROSOFT infra | T5 |

| A.7.4 | Fyzické monitorování | EUROSOFT-INFRA | Attestace DC | EUROSOFT infra | T5 |

| A.7.5 | Ochrana před fyzickými hrozbami | EUROSOFT-INFRA | Attestace DC | EUROSOFT infra | T5 |

| A.7.6 | Práce v zabezpečených oblastech | EUROSOFT-INFRA | Attestace DC | EUROSOFT infra | T5 |

| A.7.8 | Umístění a ochrana zařízení | EUROSOFT-INFRA | Attestace | EUROSOFT infra | T5 |

| A.7.9 | Bezpečnost aktiv mimo prostory | ROZPRACOVÁNO | Šifrování disku stanic | Claude+Marti (tech) | T5 |

| A.8.1 | Koncová zařízení uživatelů | ROZPRACOVÁNO | Šifrování disku + endpoint politika | Claude+Marti (tech) | T5 |

| A.5.4 | Odpovědnosti vedení | ROZPRACOVÁNO | Management review (9.3) provést | Kristý (ISMS) | T6 |

| A.8.29 | Bezpečnostní testování | ROZPRACOVÁNO | Externí pentest (po readiness) | Claude+Marti (tech) | T7 |

