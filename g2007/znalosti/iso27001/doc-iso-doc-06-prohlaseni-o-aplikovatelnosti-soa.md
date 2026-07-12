# DOC-06 Prohlaseni o aplikovatelnosti SoA

> oblast: `iso27001` · úroveň: obor · typ: smernice · verze: V1.0 · rozsah: globální (všichni tenanti)

DOC-06

Prohlášení o aplikovatelnosti (SoA)

STRATEGIE - System s.r.o. — Systém řízení bezpečnosti informací (ISMS)

IČO 23365544 · Nad Týncem 1192/10, Doubravka, 312 00 Plzeň · sp. zn. C 46859, KS v Plzni

| Kód dokumentu | DOC-06 |

| Verze | 0.1 (návrh) |

| Datum vydání | 15. 8. 2026 |

| Klasifikace | Interní |

| Vlastník dokumentu | Marti Pašek (jednatel) |

| Schválil | Marti Pašek (jednatel) |

| Platnost od | 15. 8. 2026 |

Historie revizí

| Verze | Datum | Popis změny | Autor |

| 0.1 | 15. 8. 2026 | Prvotní návrh | STRATEGIE / Claude |

# 1. Účel a použití

SoA uvádí všech 93 opatření přílohy A normy ČSN EN ISO/IEC 27001:2022, jejich aplikovatelnost a stav implementace. Vychází z DOC-05 a DOC-07. „Apl.“ = aplikovatelnost (Ano/Ne).

Položky [DOPLNIT] nebo „v zavádění/plánováno“ jsou aplikovatelné a jejich zavedení probíhá v rámci přípravy na certifikaci.

## A.5 Organizační opatření (37)

| Opatření (příloha A 2022) | Apl. | Zdůvodnění a stav implementace |

| A.5.1 Politiky bezpečnosti informací | Ano | Politika IS (DOC-02) schválena vedením. |

| A.5.2 Role a odpovědnosti | Ano | Definováno v DOC-03. |

| A.5.3 Oddělení neslučitelných povinností | Ano | Kompenzováno schvalováním se stopou a audit logem. |

| A.5.4 Odpovědnosti vedení | Ano | Vedení vyhlašuje politiku a poskytuje zdroje (DOC-02). |

| A.5.5 Kontakt s úřady | Ano | Kontakty (ÚOOÚ, Policie, NÚKIB) — [DOPLNIT seznam]. |

| A.5.6 Kontakt se zájmovými skupinami | Ano | Sledování zdrojů o bezpečnosti. |

| A.5.7 Zpravodajství o hrozbách | Ano | Sledování zranitelností a hrozeb (A.8.8). |

| A.5.8 Bezpečnost v projektovém řízení | Ano | Security by design (DOC-14). |

| A.5.9 Evidence aktiv | Ano | Evidence a klasifikace (DOC-15). |

| A.5.10 Akceptovatelné použití aktiv | Ano | Pravidla (DOC-13). |

| A.5.11 Vrácení aktiv | Ano | Proces offboardingu (DOC-13). |

| A.5.12 Klasifikace informací | Ano | Klasifikační schéma (DOC-15). |

| A.5.13 Označování informací | Ano | Dokumenty nesou klasifikaci „Interní“. |

| A.5.14 Přenos informací | Ano | Šifrovaný přenos (HTTPS/TLS), řízené kanály. |

| A.5.15 Řízení přístupu | Ano | Role a ACL, nejnižší oprávnění (DOC-09). |

| A.5.16 Správa identit | Ano | Jednoznačné identity, životní cyklus účtu. |

| A.5.17 Autentizační informace | Ano | MFA (magic-link/SMS), šifrovaný trezor. |

| A.5.18 Přístupová práva | Ano | Přidělování/odebírání, přezkum (DOC-09). |

| A.5.19 Bezpečnost ve vztazích s dodavateli | Ano | Politika dodavatelů (DOC-12). |

| A.5.20 Bezpečnost ve smlouvách s dodavateli | Ano | Bezpečnostní požadavky ve smlouvách — [DOPLNIT]. |

| A.5.21 Bezpečnost v dodavatelském řetězci ICT | Ano | Posouzení klíčových služeb (cloud ČMIS, SMS, AI) — DOC-12. |

| A.5.22 Monitorování a změny služeb dodavatelů | Ano | Sledování služeb a změn (DOC-12). |

| A.5.23 Bezpečnost při využití cloudu | Ano | Cloud ČMIS (Praha, ČR); smluvní a technická opatření (DOC-12). |

| A.5.24 Plánování řízení incidentů | Ano | Postup (DOC-10). |

| A.5.25 Posouzení a rozhodnutí o událostech | Ano | Klasifikace událostí (DOC-10). |

| A.5.26 Reakce na incidenty | Ano | Definovaný postup (DOC-10). |

| A.5.27 Poučení z incidentů | Ano | Záznam a poučení (DOC-10, DOC-18). |

| A.5.28 Sběr důkazů | Ano | Neměnný audit log pro forenzní účely. |

| A.5.29 Bezpečnost během narušení | Ano | Plán kontinuity (DOC-11). |

| A.5.30 Připravenost ICT na kontinuitu | Ano | Zálohy + vysoká dostupnost (DOC-11). |

| A.5.31 Právní a smluvní požadavky | Ano | Evidence požadavků (GDPR, ZP) — [DOPLNIT přehled]. |

| A.5.32 Práva duševního vlastnictví | Ano | Licence ke kódu a knihovnám. |

| A.5.33 Ochrana záznamů | Ano | Ochrana a retence záznamů — [DOPLNIT retence]. |

| A.5.34 Soukromí a ochrana osobních údajů | Ano | Soulad s GDPR; zpracovatelské smlouvy, retence. |

| A.5.35 Nezávislé přezkoumání bezpečnosti | Ano | Interní audit (DOC-16) + certifikační audit. |

| A.5.36 Soulad s politikami a normami | Ano | Kontrola dodržování, interní audit (DOC-16). |

| A.5.37 Dokumentované provozní postupy | Ano | Provozní postupy (deploy, zálohy, ops). |

## A.6 Opatření týkající se osob (8)

| Opatření (příloha A 2022) | Apl. | Zdůvodnění a stav implementace |

| A.6.1 Prověřování (screening) | Ano | Ověření při nástupu — [DOPLNIT proces]. |

| A.6.2 Podmínky pracovního poměru | Ano | Bezpečnostní povinnosti ve smlouvách (DOC-13). |

| A.6.3 Povědomí, vzdělávání a školení | Ano | Pravidelné poučení (cíl v DOC-08). |

| A.6.4 Disciplinární proces | Ano | Postih dle DOC-02 a pracovněprávních pravidel. |

| A.6.5 Odpovědnosti po ukončení | Ano | Offboarding, mlčenlivost (DOC-13). |

| A.6.6 Dohody o mlčenlivosti (NDA) | Ano | NDA s EUROSOFT zavedena; vlastní NDA STRATEGIE se připravuje. |

| A.6.7 Práce na dálku | Ano | Pravidla home-office a vzdáleného přístupu (DOC-13). |

| A.6.8 Hlášení bezpečnostních událostí | Ano | Každý hlásí bez obav z postihu (DOC-10). |

## A.7 Fyzická opatření (14)

| Opatření (příloha A 2022) | Apl. | Zdůvodnění a stav implementace |

| A.7.1 Fyzické bezpečnostní perimetry | Ano | Kancelář [DOPLNIT]; servery v DC poskytovatele ČMIS. |

| A.7.2 Fyzický vstup | Ano | Řízený vstup; DC poskytovatele. |

| A.7.3 Zabezpečení kanceláří a prostor | Ano | Zamykání, zabezpečení pracoviště — [DOPLNIT]. |

| A.7.4 Fyzické monitorování | Ano | Zajišťuje poskytovatel ČMIS v DC. |

| A.7.5 Ochrana před fyzickými hrozbami | Ano | DC poskytovatele (požár, napájení). |

| A.7.6 Práce v zabezpečených oblastech | Ano | Relevantní pro DC poskytovatele. |

| A.7.7 Čistý stůl a obrazovka | Ano | Pravidlo čistého stolu/obrazovky (DOC-13). |

| A.7.8 Umístění a ochrana zařízení | Ano | Stanice chráněny; servery v DC. |

| A.7.9 Bezpečnost aktiv mimo prostory | Ano | Na stanicích nejsou zákaznická data; ESET; šifrování [plánováno] (DOC-13). |

| A.7.10 Nosiče dat | Ano | Řízení a bezpečná likvidace — [DOPLNIT]. |

| A.7.11 Podpůrné technické vybavení | Ano | Napájení/chlazení zajišťuje DC ČMIS. |

| A.7.12 Bezpečnost kabeláže | Ano | V kompetenci DC poskytovatele. |

| A.7.13 Údržba zařízení | Ano | Údržba stanic a serverů (poskytovatel). |

| A.7.14 Bezpečná likvidace / opětovné použití | Ano | Vymazání dat před vyřazením zařízení. |

## A.8 Technologická opatření (34)

| Opatření (příloha A 2022) | Apl. | Zdůvodnění a stav implementace |

| A.8.1 Koncová zařízení uživatelů | Ano | Antivir ESET (EUROSOFT-System); na stanicích nejsou zákaznická data; šifrování disku [plánováno]. |

| A.8.2 Privilegovaná přístupová práva | Ano | Oddělené role (rodič/admin), nejnižší oprávnění. |

| A.8.3 Omezení přístupu k informacím | Ano | Tenant a role omezují přístup (ACL). |

| A.8.4 Přístup ke zdrojovému kódu | Ano | Git s řízeným přístupem (PAT). |

| A.8.5 Bezpečná autentizace | Ano | MFA (magic-link / SMS). |

| A.8.6 Řízení kapacity | Ano | Sledování kapacity serverů a DB. |

| A.8.7 Ochrana před malwarem | Ano | Antivir ESET, správu zajišťuje EUROSOFT-System. |

| A.8.8 Správa technických zranitelností | Ano | Aktualizace OS a knihoven; kritické opravy v rámci dne. |

| A.8.9 Správa konfigurací | Ano | Konfigurace verzována; deploy se stopou. |

| A.8.10 Mazání informací | Ano | Soft delete (archivace) + řízené mazání dle retence. |

| A.8.11 Maskování dat | Ano | Citlivá pole v UI zobrazena jako „[omezeno]“ dle role. |

| A.8.12 Prevence úniku dat | Ano | Řízené kanály, šifrování — [DOPLNIT]. |

| A.8.13 Zálohování informací | Ano | Denní zálohy (03:00); offsite kopie a šifrování v zavádění (DOC-11). |

| A.8.14 Redundance zpracování | Ano | Vysoká dostupnost (blue-green) — DOC-11. |

| A.8.15 Protokolování (logging) | Ano | Neměnný append-only audit log. |

| A.8.16 Monitorování činností | Ano | Sledování provozu a událostí. |

| A.8.17 Synchronizace času | Ano | Synchronizace času serverů (NTP). |

| A.8.18 Privilegované systémové nástroje | Ano | Omezené a auditované ops nástroje (whitelist). |

| A.8.19 Instalace softwaru na provozní systémy | Ano | Řízený deploy přes schválený proces. |

| A.8.20 Bezpečnost sítí | Ano | TLS, oddělení produkce, reverzní proxy. |

| A.8.21 Bezpečnost síťových služeb | Ano | Zabezpečené služby a rozhraní. |

| A.8.22 Segregace sítí | Ano | Oddělení produkce a interního prostředí. |

| A.8.23 Filtrování webu | Ano | Omezeně; v rozsahu koncových stanic — [DOPLNIT]. |

| A.8.24 Použití kryptografie | Ano | Šifrování přenosu (TLS) i tajemství (trezor, Fernet). |

| A.8.25 Bezpečný životní cyklus vývoje | Ano | Bezpečný vývoj (DOC-14). |

| A.8.26 Bezpečnostní požadavky aplikací | Ano | Bezpečnost součástí požadavků. |

| A.8.27 Bezpečná architektura a principy | Ano | Security by design, vícevrstvá ochrana. |

| A.8.28 Bezpečné kódování | Ano | Zásady bezpečného kódování (DOC-14). |

| A.8.29 Bezpečnostní testování | Ano | Testování před nasazením; externí pentest zatím neproběhl — plánováno. |

| A.8.30 Vývoj zajišťovaný externě | Ne | Vývoj probíhá interně; bez outsourcingu. |

| A.8.31 Oddělení vývoje, testu a produkce | Ano | Oddělená produkce a testovací prostředí. |

| A.8.32 Řízení změn | Ano | Schvalovací proces změn se stopou. |

| A.8.33 Testovací informace | Ano | Demo data oddělena (demo tenant), bez reálných osob. |

| A.8.34 Ochrana systémů při auditu | Ano | Auditní činnosti řízeny tak, aby nenarušily provoz. |

# 2. Schválení

Schválil: Marti Pašek, jednatel             Datum: 15. 8. 2026             Podpis: ............................

