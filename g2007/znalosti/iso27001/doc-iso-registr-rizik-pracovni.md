# Registr rizik pracovni

> oblast: `iso27001` · úroveň: obor · typ: tabulka · verze: V1.0 · rozsah: globální (všichni tenanti)

# Registr rizik pracovni

## List: Registr rizik

| Registr rizik ISMS — STRATEGIE – System s.r.o. (předdraft DOC-05) |

| Stupnice 1-5 (1=zanedbatelné, 5=kritické). Míra = Dopad × Pravděp. Úroveň: ≤6 Nízké, 7-14 Střední, ≥15 Vysoké. Hodnoty jsou návrh k odsouhlasení (Kristý + management review). |

| ID | Oblast / aktivum | Hrozba / scénář | Dopad (1-5) | Pravděp. (1-5) | Míra (D×P) | Úroveň | Stávající opatření | Ošetření (plán) | Vlastník | Vazba Annex A | Zbytkové riziko (cíl) |

| R01 | Nasazení / kód | Vadný deploy shodí produkci | 4 | 3 | 12 | Střední | Blue-green + py_compile gate + advisory lock | Restore drill; monitoring deploy; pin na B | Claude+Marti | A.8.19/8.32/5.29 | Nízké |

| R02 | Databáze | Ztráta / poškození data_db | 5 | 2 | 10 | Střední | Denní zálohy ČMIS (03:00) | Restore drill; retence ≥30 dní; offsite; at-rest | Claude+Marti | A.8.13/5.30 | Nízké |

| R03 | Osobní údaje | Únik osobních údajů klientů | 5 | 2 | 10 | Střední | RBAC + ACL + šifr. přenos + access logy | DLP; DPIA; klasifikace dat | Kristý (ISMS) | A.5.34/8.12/8.3 | Střední |

| R04 | Tajemství | Kompromitace API klíčů / hesel | 4 | 2 | 8 | Střední | Vault Fernet; AppEnvironmentExtra; nikdy v logu | Rotace klíčů; secrets review | Claude+Marti | A.5.17/8.24 | Nízké |

| R05 | Závislosti | Zranitelnost v knihovně (CVE) | 3 | 3 | 9 | Střední | — | pip-audit týdně + SLA patch (A.8.8) | Claude+Marti | A.8.8 | Nízké |

| R06 | Přístup | Krádež přihlašovacích údajů | 4 | 2 | 8 | Střední | 2FA (PIN/SMS); single SIM; trusted devices | MFA všude; čtvrtletní access review | Claude+Marti | A.8.5/5.18 | Nízké |

| R07 | Privileg. přístup | Zneužití privilegovaného přístupu / impersonace | 4 | 2 | 8 | Střední | impersonation_log; 3-actor PG; approval banner | Least-privilege review; oddělení rolí | Claude+Marti | A.8.2/5.3 | Nízké |

| R08 | Dodavatelé | Výpadek klíčového dodavatele (AI / cloud) | 3 | 3 | 9 | Střední | — | Degradovaný režim; SLA dodavatele; DPA | Kristý (ISMS) | A.5.22/5.30 | Střední |

| R09 | Tajemství | Ztráta klíče trezoru (vault) | 5 | 1 | 5 | Nízké | Klíč mimo DB (AppEnvironmentExtra) | Offline záloha klíče; dokumentovaný postup obnovy | Marti | A.8.24/5.30 | Nízké |

| R10 | On-prem | Výpadek EC-SERVER2 (MSSQL Centrála/Helios) | 3 | 2 | 6 | Nízké | Zrcadlo v PG → degradovaný běh STRATEGIE | EUROSOFT DR; attestace | EUROSOFT | A.5.30 | Nízké |

| R11 | Stanice | Ransomware / malware na stanici | 4 | 2 | 8 | Střední | ESET; na stanicích nejsou zákaznická data | Endpoint politika; šifrování disku | EUROSOFT | A.8.7/8.1 | Nízké |

| R12 | AI / LLM | Chybná autonomní akce AI | 3 | 3 | 9 | Střední | Approval banner u zápisů; audit; „AI nevidí víc než user“ | Human-in-loop u rizik. operací; review | Claude+Marti | A.8.34/5.8 | Nízké |

| R13 | AI / dodavatel | Únik dat přes AI sub-processora | 4 | 2 | 8 | Střední | Minimalizace kontextu; ACL | DPA; pravidla co posílat do LLM | Kristý (ISMS) | A.5.19/8.12 | Střední |

| R14 | Kontinuita | Záloha nepoužitelná při potřebě (neotestovaná) | 4 | 2 | 8 | Střední | Denní zálohy existují | Restore drill čtvrtletně + záznam | Claude+Marti | A.5.30/8.13 | Nízké |

| R15 | GDPR | Neshoda v retenci / výmazu osobních dat | 3 | 2 | 6 | Nízké | Soft delete; request_forget; anonymizace | Retenční politika; DPIA | Kristý (ISMS) | A.5.34/8.10 | Nízké |

| R16 | Lidé | Lidská chyba / sociální inženýrství | 3 | 3 | 9 | Střední | — | Školení + osvěta; hlášení událostí | Kristý (ISMS) | A.6.3/6.8 | Střední |

| R17 | Síť | Síťový útok / neoprávněný přístup zvenčí | 4 | 2 | 8 | Střední | Mikrotik whitelist; Caddy; HTTPS; scanner filtr | Segmentace; monitoring + alerting | Claude+Marti | A.8.20/8.16 | Nízké |

| R18 | SMS brána | Kompromitace / výpadek SMS brány (vlastní SIM) | 3 | 2 | 6 | Nízké | Vlastní SIM; caller_id | Záložní kanál; monitoring | Claude+Marti | A.8.21/5.14 | Nízké |

| R19 | ČSSZ / datovky | Chybné / opožděné podání (NEMPRI) na ČSSZ | 3 | 2 | 6 | Nízké | Audit dávek; měsíční kontrola | Dvojitá kontrola; záznam | Kristý/Claude | A.5.28 | Nízké |

| R20 | Audit | Mezera v auditní stopě / tamper | 3 | 2 | 6 | Nízké | 22 audit tabulek append-only | Hash-chain (volit.); pravidelná revize logů | Claude+Marti | A.8.15/5.28 | Nízké |

| R21 | Lidé | Odchod klíčové osoby (znalostní riziko) | 3 | 2 | 6 | Nízké | CLAUDE.md krabička; dokumentace | Oddělení rolí; zástupnost | Marti | A.5.3/6.5 | Nízké |

| R22 | Mobilní app | Kompromitace mobilního zařízení | 3 | 2 | 6 | Nízké | Token auth; allowBackup=false | Endpoint/MDM politika | Claude+Marti | A.8.1/6.7 | Nízké |

## List: Souhrn

| Souhrn rizik |

| Vysoké | 0 |

| Střední | 14 |

| Nízké | 8 |

| Celkem rizik | 22 |

| Pozn.: Dopad/Pravděp. jsou návrh — Kristý upraví dle reality; Míra a Úroveň se přepočítají. Vysoká/střední rizika → plán ošetření (DOC-07) + termín. Zbytkové riziko = cílový stav po ošetření. |

