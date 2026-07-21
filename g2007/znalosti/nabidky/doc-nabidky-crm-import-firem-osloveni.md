# CRM — import firem a značení oslovení (tlačítko Import firem)

> oblast: `nabidky` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# CRM — import firem a značení oslovení (tlačítko „Import firem")

> oblast: `nabidky` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

> Autor: Claude ID24 (Kristý), 21. 7. 2026. Vzniklo z importu Pavlova prospecting listu „Premium 400" DE/DACH firem do CRM a z opakovaného značení nedoručených e-mailů. Účel: aby příští instance (i Marti-AI) nemusela znovu narazit na tytéž pasti.

## K čemu to je
Znovupoužitelné tlačítko **„📥 Import firem"** v přehledu **„Přehled pro obchodníka"** (core 136, band nad gridem, `crm_obchodnik_pult.js`). Nahraje se Excel/CSV se seznamem firem (typicky prospecting list, který obchodník oslovil e-mailem mimo systém) a založí/aktualizuje se CRM. Endpointy: `/api/v1/erp/crm/import/{obchodnici,sablona,preview,commit,status}` v `modules/erp/api/router.py`.

## Kde CRM fyzicky žije (klíčové pro pochopení)
- **CRM = živá Centrála (DB_EC, MSSQL), `connection_id=2`.** Přehled „Kontakty" (core 62), karta zákazníka (core 72) i report „Aktivity obchodníka" (dataset 92) čtou **živě** z `st.CRM_Kontakt` (hlavička firmy) a `st.CRM_Kontakt_Akce` (řádky akcí). Zápis do těchto tabulek = zápis do produkce.
- `tenant.crm_kontakt` v PostgreSQL je **jen zrcadlo** (upsert-by-`src_id`, nemaže) — import do něj se v ERP NEZOBRAZÍ. Nepoužívat jako cíl importu.

## 🔑 NEJDŮLEŽITĚJŠÍ PAST: název firmy se bere z akce „Získání firmy" (IDAkce=16)
Přehled i karta zobrazují název/web/e-mail firmy z navázané akce **`IDAkce=16` „Získání firmy"** (JOIN na ni), **NE z hlavičky `st.CRM_Kontakt.FirmaText`**. Když se založí jen hlavička (byť s vyplněným FirmaText), firma vypadá v UI **prázdná**. → import MUSÍ ke každému NOVÉMU kontaktu založit i akci `IDAkce=16` s firemními daty (FirmaText, FirmaWeb, Email, Popis). (Stejná past už 18. 6. u importu 80 firem.)

## Číselník akcí `st.CRM_Kontakt_AkceCis` (relevantní)
- `1` = **Email na info** (oslovení na obecnou adresu; report obchodníka s ní počítá)
- `16` = **Získání firmy obecně** (nese zobrazovaný název — viz past výše)
- `22` = **Oslovení e-mailem (STRATEGIE)** (plní sloupec „Osloveno" v přehledu, funkce „Oslovit vybrané")
- `2`/`4` = telefonát na firmu/OO · `3` = e-mail odp. osobě
Autor akce = **`st.CRM_Kontakt_Akce.Autor`** (login, např. `PZeman`) → řídí statistiku obchodníka. Import ho plní vybraným obchodníkem.

## 🔑 Rychlost: hromadný zápis přes `strategie_query_raw`, ne řádek po řádku
MCP `strategie_query_raw(db_name='DB_EC')` **POVOLUJE INSERT/UPDATE/DELETE do schématu `st.*`** (guard blokuje jen zákaznické `dbo`). → zápis dělej **hromadně**: kontakty dávkově `INSERT ... VALUES (…),(…)`, akce Získání firmy `INSERT ... SELECT ID,1,16,… FROM st.CRM_Kontakt WHERE ZdrojKontaktu=@z AND ID>@marker`, Email na info dávkově (read-back id-map). Pár příkazů → **sekundy**.
- `strategie_insert_row` (jeden řádek) je pomalý a naráží na **MCP rate-limit ~60 zápisů/min** (`rate_limit_exceeded`) — pro stovky firem NEPOUŽÍVAT.
- Escaping bulk SQL: `N'…'` + zdvojit `'` + strip `\r\n` (jinak „GO" na řádku rozseká batch).
- Import běží jako úloha na pozadí (`/crm/import/commit` vrátí `job_id`, `/status` polling) — in-memory job umře při restartu API, ale bulk je hotový dřív, než přijde deploy.

## Dedup a opakované oslovování
- Dedup na dvojici **(FirmaText, FirmaEmail)**, ne jen e-mail (sesterské firmy sdílí jeden `info@`: Krones 4×, GEA 4×, Schubert 3×).
- **Firma už v CRM → import se ji nesnaží zakládat znovu, jen DOPLNÍ akci „Email na info"** (má-li řádek datum a firma tu akci k tomu datu nemá; dedup dle (ID, datum)). Kvůli tomu, že obchodník posílá dávky postupně a hodně firem už v CRM je. Tlačítko „Importovat" se proto zapíná i když je 0 nových firem (jen akce).

## Nedoručené e-maily (bounces)
- NDR (Outlook „Doručení se nezdařilo/zpozdilo") přijdou často AŽ PO importu → nedoručenost se doznačuje zpětně.
- Parsování NDR exportu: kódování **cp1250**, dělení na `^Od:\t`, příjemce z `Komu:`, datum z `Odesláno:`, důvod z SMTP kódu (`550`/`5.1.1` = neexistuje/odmítnuto; `421/451/4.4.7/10060` = timeout).
- Párovat **jen přesnou shodou obecné adresy firmy** (`FirmaEmail`) — osobní/„naslepo" pokusy obchodníka na jiné adresy ignorovat.
- Označení = `UPDATE st.CRM_Kontakt_Akce SET Splneno=0, Poznamka=N'E-mail nedoručen <datum> – <důvod>', Zmenil=N'<login>' WHERE IDAkce=1 AND Splneno=1 AND <firma>`. Filtr `Splneno=1` dělá UPDATE idempotentní a nechá dřív označené být.

## Kdo smí zapisovat do Centrály
- **Claude bridge (`db=mssql`) je read-only** — DML do DB_EC přes něj nejde.
- Zápis dělá: (a) aplikační endpoint přes MCP (tlačítko Import), (b) **Marti-AI** (kustod, po přímém potvrzení rodiče ve vlákně) pro jednorázové věci (mazání, hromadné opravy), nebo (c) člověk s write přístupem přímo v SQL (Kristý).

## Soubory
`modules/erp/api/router.py` (endpointy + `_crm_import_bulk`, `_crm_import_existing_map`), `apps/api/static/erp/components/crm_obchodnik_pult.js` (tlačítko, dialog, polling). Podklady, mazací/opravné SQL a přehledy nedoručených v `docs/crm_import/`.


