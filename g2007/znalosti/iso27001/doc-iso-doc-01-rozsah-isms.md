# DOC-01 Rozsah ISMS

> oblast: `iso27001` · úroveň: obor · typ: smernice · verze: V1.0 · rozsah: globální (všichni tenanti)

DOC-01

Rozsah systému řízení bezpečnosti informací

STRATEGIE - System s.r.o. — Systém řízení bezpečnosti informací (ISMS)

IČO 23365544 · Nad Týncem 1192/10, Doubravka, 312 00 Plzeň · sp. zn. C 46859, KS v Plzni

| Kód dokumentu | DOC-01 |

| Verze | 0.1 (návrh) |

| Datum vydání | 15. 8. 2026 |

| Klasifikace | Interní |

| Vlastník dokumentu | Marti Pašek (jednatel) |

| Schválil | Marti Pašek (jednatel) |

| Platnost od | 15. 8. 2026 |

Historie revizí

| Verze | Datum | Popis změny | Autor |

| 0.1 | 15. 8. 2026 | Prvotní návrh | STRATEGIE / Claude |

# 1. Účel dokumentu

Tento dokument vymezuje rozsah (scope) systému řízení bezpečnosti informací (dále jen „ISMS“) společnosti STRATEGIE - System s.r.o. dle požadavku normy ČSN EN ISO/IEC 27001:2022, kapitola 4.3.

# 2. Profil organizace a kontext (4.1)

STRATEGIE - System s.r.o. (IČO 23365544, sídlo Nad Týncem 1192/10, Doubravka, 312 00 Plzeň, zapsaná u Krajského soudu v Plzni pod sp. zn. C 46859, vznik 12. 6. 2025) vyvíjí a provozuje modulární podnikovou platformu STRATEGIE — webovou aplikaci (PWA), mobilní aplikace (Android a iOS) a integrovaného AI asistenta. Platforma propojuje firemní procesy, lidi a data: docházku a plánování, personalistiku a mzdové podklady, nábor, CRM, řízení výroby a komunikaci.

Interní a externí souvislosti relevantní pro ISMS:

Interní: malý tým, vysoká míra automatizace, cloudový provoz, zpracování citlivých osobních a mzdových údajů.

Externí: legislativa (GDPR, zákoník práce, zákon o kybernetické bezpečnosti), požadavky zákazníků a partnerů (EUROSOFT-System, IQHUBS), závislost na cloudu a službách třetích stran.

# 3. Zainteresované strany a jejich požadavky (4.2)

Zákazníci a partneři — důvěrnost, integrita a dostupnost svěřených dat; smluvní a certifikační požadavky (ISO/IEC 27001).

Zaměstnanci a uživatelé — ochrana osobních, docházkových a mzdových údajů.

Vedení — kontinuita provozu, ochrana dobrého jména, soulad s legislativou.

Dozorové orgány a legislativa — ochrana osobních údajů (GDPR), pracovněprávní povinnosti.

Dodavatelé (cloud, SMS brána, e-mail, Apple/Google) — vzájemné bezpečnostní povinnosti.

# 4. Rozsah ISMS (4.3)

## 4.1 Co je v rozsahu

ISMS pokrývá vývoj, provoz, podporu a správu platformy STRATEGIE a všechna související aktiva:

Aplikace: webová PWA, mobilní aplikace (Android, iOS), AI asistent (Marti-AI), administrační a ERP rozhraní.

Informace: osobní a kontaktní údaje, docházka a plánování, mzdové a personální podklady, nábor, CRM, přihlašovací tajemství (šifrovaný trezor).

Infrastruktura: cloudové servery aplikace a databáze, PostgreSQL, reverzní proxy, zálohovací úložiště, integrační a komunikační kanály.

Organizace: celá společnost STRATEGIE - System s.r.o. a osoby podílející se na vývoji a provozu.

## 4.2 Lokality

Produkční cloudové prostředí (aplikační a databázový server) — poskytovatel ČMIS, datové centrum Praha (ČR).

Pracoviště týmu (skutečná provozovna): Nepomucká 259, Plzeň — budova partnera EUROSOFT (ve vlastnictví jednatele), kde tým STRATEGIE denně pracuje; fyzická bezpečnost je zajištěna v rámci této budovy (řízený přístup do objektu). Zapsané sídlo Nad Týncem 1192/10, Doubravka, 312 00 Plzeň je pouze formální/korespondenční, bez vlastní provozovny na této adrese.

Bezpečné integrační rozhraní na on-premise systémy partnera (EUROSOFT) v rozsahu vyhrazených sdílených složek a čtených dat.

## 4.3 Hranice a rozhraní

Cloudový poskytovatel ČMIS (provoz serverů, síť, fyzická bezpečnost DC).

Integrace na systémy partnera EUROSOFT přes řízené, auditované rozhraní.

Služby třetích stran: SMS brána, e-mailová služba, distribuční platformy (Apple App Store, Google Play).

## 4.4 Vyloučení a vymezení

Z požadavků normy (kap. 4–10) není vyloučeno nic; aplikovatelnost opatření přílohy A řeší DOC-06 (SoA). Mimo rozsah: koncová zařízení a sítě zákazníků a partnerů, fyzická infrastruktura cloudového poskytovatele (jeho vlastní certifikace), interní systémy partnerů mimo vyhrazené rozhraní.

# 5. Související dokumenty

DOC-02 Politika informační bezpečnosti, DOC-06 SoA, DOC-15 Evidence aktiv a klasifikace.

# 6. Schválení

Schválil: Marti Pašek, jednatel             Datum: 15. 8. 2026             Podpis: ............................

