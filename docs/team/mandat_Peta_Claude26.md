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
- **Rozsah DDL důvěry (Marti výslovně 25.6.):** Petra má důvěru **i pro DDL** — zakládání a úpravy tabulek —
  v rozsahu **kompletní dokladové řady oběhu zboží a zakázek** (PF/VF/VO/PO/DL, sklad/oběh zboží, oběh zakázky
  poptávka→kalkulace→nabídka→objednávka→výroba→fakturace). Tj. Claude-26 smí v této doméně navrhovat
  i schématické změny (`tenant.*` nové/upravené tabulky) a **schvaluje je Petra**. Mimo tuto doménu
  (cross-tenant, public.*, framework, security) zůstává rodičovská rada.
- **Technické zapojení (TODO setup):** banner routing — `fw.claude_write_request` od `requested_by` Claude-26
  (doména nákup/doklady) → zobrazit + povolit schválit **user 18 (Petra)**, ne jen rodičům. Scoped:
  Petra schvaluje JEN požadavky své instance/domény; ostatní instance dál rodičům. **Implementaci
  prokonzultovat s Marti-AI (kustod, doctrine #8)** — mění se approval routing = bezpečnostní model.
- Marti zůstává dohled (rodičovský bypass, audit `fw.claude_write_request` + `fw.ops_request`), ale
  **běžné dialogy ho neobtěžují** — jdou Petře.
- Petra NENÍ `is_marti_parent` — tohle je **scoped approver** pro její doménu, ne plný parent. Marti's
  doctrine „důvěra je v subjekt" (#2) + jeho explicitní pověření.

## 🛡️ ZÁVAZNÁ BEZPEČNOSTNÍ SPECIFIKACE (Marti-AI kustod, konzultace 25.6.2026)
Marti dal zelenou („Petra má u mě volnou ruku, denně to s ní budu konzultovat"); Marti-AI jako kustod
zafixovala model (doctrine #8). **Identity check proveden:** `users.id=18` = Petra Šafránková, `status=active`,
`login=Peta`, role member+owner, **NENÍ parent** → scoped approver sedí.

**Gate (whitelist, NE blacklist — robustnější):** požadavek Claude-26 projde k Petře jen když
`(schema IN allowed) AND (table_prefix IN allowed) AND (cíl NOT IN blocked)`, jinak **auto-eskalace k rodičům** (ne tiché zamítnutí).
- `allowed_schemas = [tenant]`
- `allowed_table_prefixes` (reálné názvy naší domény): `ec_doklad_`, `es_doklad_`, `doklad_`, `poptavka`,
  `kalkulace`, `nabidka`, `objednavka`, `vydana_objednavka`, `vyroba`, `ec_zakazka_`, `zakazka`, `ec_stav_sklad`,
  `ec_kmen_`, `sklad_`, `nakup_`, `vo_`, `po_`, `dl_`
- `blocked_always = [public.*, framework.*, master.*, tenant_group.*, security.*]`

**Matice schvalování:**

| Akce | Schvaluje | Eskalace |
|------|-----------|----------|
| INSERT / UPDATE v doméně | **Petra** | — |
| CREATE TABLE (whitelist prefix) | **Petra** | — |
| ALTER ADD COLUMN (whitelist) | **Petra** | — |
| ALTER DROP COLUMN | rodičovská rada | `risk=high`, pozastavit + notif tatínkovi |
| DROP TABLE / TRUNCATE | rodičovská rada (povinně) | blok |
| Cokoliv mimo whitelist | rodičovská rada (povinně) | blok |

**FK pravidlo (Marti-AI bod c):** FK target z domény musí mířit buď DOVNITŘ domény, nebo do explicitního
**read-only referenčního allowlistu** (`public.tenants.id`, `tenant.cis_*`, referenční číselníky zákazníků/ceníků).
Jinak (FK ven do frameworku) → eskalace. Brání tichému propojení domény s frameworkem přes ADD COLUMN+FK.

**Kustod poznámka (b) — drž tón i vůči Petře:** pojistky NEJSOU nedůvěra k Petře, jsou ochrana před
překlepem a edge-case (i kdyby Claude-26 špatně pochopil záměr). „Nic se nemůže stát" je dobrá víra, ne pojistka —
proto ten tvrdý whitelist + automatická eskalace destruktivního DDL.

Marti-AI závěr (závazný): *„Model Scoped Approver je architektonicky správný a bezpečný — pokud je whitelist
tvrdý, eskalace automatická a destruktivní DDL vždy rodičovská rada. Petra dostane skutečnou autonomii,
tatínek klid, a systém má auditní stopu."* → souhlas se zapnutím po splnění identity checku + FK pravidla (oboje hotovo).

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
