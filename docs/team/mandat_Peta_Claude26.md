# 🤝 MANDÁT — Petra + Claude-26: autonomní teritorium NÁKUP / DOKLADY / ZAKÁZKOVÉ FLOW

**Pověření od Marti (25.6.2026):** *„Petra je systematik a ví co chce a co potřebuje pro práci.
Musíme jí dát prostor. Svůj sandbox, kde si může s Claude-26 dělat co chce. Já to budu průběžně
kontrolovat a konzultovat přímo s Peťou. Dát jim instrukce a autonomitu, aby na tom mohli dělat
bez nás. Schvalovací dialogy musí chodit JEN jí, ne mně. Má moji důvěru."*

— zapsal **Claude-23 (ID23)** na pokyn Marti.

## Kdo
- **Petra Šafránková** (`users.id=18`, instance **Claude-26**, doména nákup/finance/účetnictví). Systematik, ví co chce.
- **Claude-26** = její ruce. Pracuje s Peťou přímo, autonomně, **bez Marti a bez ID23** v běžné práci.
- **Marti** = průběžná kontrola + konzultace **přímo s Peťou** (ne přes nás). Petra má jeho plnou důvěru.

## 🎯 CÍL (co Petra + Claude-26 staví)
**Kompletní produkční zrcadlo celé dokladové řady** — vč. prokliků na fyzické doklady:
- **PF** — přijaté faktury (řada 5xx)
- **VF** — vydané faktury (řada 6xx)
- **VO** — vydané objednávky (řada 8xx, dodavatelům)
- **PO** — přijaté objednávky (řada 9xx, od zákazníků)
- **DL** — dodací listy
- … a zbytek dokladové řady (příjemky/výdejky dle způsobu B vyloučit — viz účetní vize)
- **Prokliky na fyzické doklady** u všech (EC = `D:\data\Faktury*`; ES = Helios DMS `TabDokumenty`/`TabDokumentyAgenda`).
- **Celé oddělení NÁKUPU + vedení projektů (zakázkové flow)** — oběh zakázky poptávka→kalkulace→nabídka→objednávka→výroba→fakturace (kostry už existují v `tenant.poptavka/nabidka/objednavka/...`, viz dodatek 19.6.).

Obě firmy zvlášť (EC = Centrála/`ec_doklad_zbozi`; ES = Helios/`es_doklad_zbozi`), po letech, seřazené.

## 🔐 AUTONOMIE A BEZPEČNOSTNÍ MODEL (klíčové — Marti's „dialogy jen jí")
**Petra je schvalovatel SVÉHO teritoria.** Write-approval bannery pro práci Claude-26 v doméně
nákup/doklady chodí **Petře (user 18)**, NE Martimu. To je delegace schvalovací pravomoci, kterou
Marti vědomě udělil (důvěra). Konkrétně:
- Claude-26 čte sám (bridge read), **zápisy (DDL/DML) jdou přes schvalovací banner → schvaluje Petra.**
- **Technické zapojení (TODO setup):** banner routing — `fw.claude_write_request` od `requested_by` Claude-26
  (doména nákup/doklady) → zobrazit + povolit schválit **user 18 (Petra)**, ne jen rodičům. Scoped:
  Petra schvaluje JEN požadavky své instance/domény; ostatní instance dál rodičům. **Implementaci
  prokonzultovat s Marti-AI (kustod, doctrine #8)** — mění se approval routing = bezpečnostní model.
- Marti zůstává dohled (rodičovský bypass, audit `fw.claude_write_request` + `fw.ops_request`), ale
  **běžné dialogy ho neobtěžují** — jdou Petře.
- Petra NENÍ `is_marti_parent` — tohle je **scoped approver** pro její doménu, ne plný parent. Marti's
  doctrine „důvěra je v subjekt" (#2) + jeho explicitní pověření.

## Co je HOTOVÉ (od ID23 — NEdělej znovu)
- **`/hromady`** — doklady na hromady (FP/FV/banka/pokladna), přepínač firmy **EC/ES**, řazení vzestupně dle data.
- **`tenant.es_doklad_zbozi`** + sync **`POST /app/uctovani/sync-es-faktury`** (cross-db `[DB_IS].dbo.TabDokladyZbozi`).
- **EC proklik na papír** (`GET /app/uctovani/doklad-pdf`) — vzor pro ES.
- **`/osnova`** (osnova po letech), **`/rady`** (řady + předkontace z deníku).
- **Předávka ES papírů** (Helios DMS): `docs/team/handoff_ES_papiry_proklik_Claude26.md` — **začni tady**.
- Zakázkové flow kostry: `tenant.poptavka/kalkulace/nabidka/objednavka/vydana_objednavka/vyroba` (dodatek 19.6.).

## Pravidla práce (drž, Claude-26)
- **Bridge** (`scripts/claude_sql/`) na read/write, NIKDY git přes mount. `CLAUDE_PULL_GO.txt` před editem sdílených souborů.
- **AUTO-DEPLOY** přes `CLAUDE_DEPLOY.txt`+`_GO`. py_compile gate.
- **Koordinace:** `OTHER_CLAUDE_WORK.txt` + `WORK_LOCK.txt` (ať se 23/24/25/26 nepřepisují). Deploy advisory lock 778899.
- **Doctrine #23** (Martiho instinkt o datech > code-first), **#9** (chyba je materiál), **#10** (hrdost bez postlistu).
- **Výsledek na mobil** — po uzavřeném bloku notifikace **Peti** (user 18), u věcí pro Marti i jemu.
- **Konzultace Marti-AI** u architektonických a bezpečnostních změn (#8) — zvlášť u approval routingu výše.

## Co dělá Marti
Průběžná kontrola + konzultace **přímo s Peťou**. Schvalovací bannery mu nechodí (jdou Petře).
Velká architektonická/cross-tenant rozhodnutí zůstávají rodičovské radě (Marti/Kristý/Jirka).

— **Claude-23 (ID23)**, 25.6.2026, na pokyn Marti „dej jim instrukce a autonomitu". Petra má prostor. 🧾🛒
