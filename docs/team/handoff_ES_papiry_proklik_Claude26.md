# 📨 Předávka pro Claude-26 (Peťa) — ES faktura papíry: proklik na sken z Helios DMS

**Od:** Claude-23 (ID23) · **Komu:** Claude-26 (Peťa, nákup/finance/účetnictví) · **Datum:** 25.6.2026
**Pověření:** Marti (25.6.): *„Předáme to jiné tvojí instanci. Té co spolupracuje s Peťou. To je její teritorium, ať se snaží."*

## Zadání
V účetní hře pro Marti (konzervativní účetní persona) jsme postavili přehled **„Doklady — hromady"** (`/hromady`). U **EC (Control)** funguje **proklik na naskenovaný papír** (PDF) — klik na číslo faktury otevře sken. **U ES (System) tenhle proklik zatím chybí** a Marti chce, ať ho dotáhneme. **To je tvůj úkol.**

## Co už je hotové (NEdělej znovu)
- **`tenant.es_doklad_zbozi`** — ES faktury (FP/FV) nasyncované z **`[DB_IS].dbo.TabDokladyZbozi`** (cross-db z connection DB_EC, NE `db_name="DB_IS"` — ten MCP nebere!). ~200 faktur za 2025. Sync endpoint: `POST /app/uctovani/sync-es-faktury` v `modules/erp/api/bank_api.py`.
- **GOTCHA ES čísla:** `es_doklad_zbozi.cislo` je **krátká per-řada sekvence s nulami** (`000001`, `000002`…) a **opakuje se napříč řadami** — Helios čísluje jinak než Centrála. Unikátní doklad = (rada, cislo) nebo `src_id`. **NEpoužívej cislo jako klíč na složku** jako u EC!
- **EC proklik (vzor):** endpoint **`GET /app/uctovani/doklad-pdf`** v `bank_api.py` — pro EC čte z disku `D:\data\FakturyP\FP<cislo>` přes EUROSOFT MCP (`eurosoft_eurosoft_file_list` + `eurosoft_eurosoft_file_read`, `user_namespace:"ro"`, `base_override`, `encoding:"base64"`). UI: `apps/api/static/hromady.html`, FP/FV řádky mají `window.open('/api/v1/erp/app/uctovani/doklad-pdf?typ=fp&cislo=…')`.

## Co jsem zjistil o ES dokumentech (Helios DMS) — tvyjdi z toho
ES papíry **existují**, ale v Helios dokumentové agendě (ne v `D:\data\FakturyP`):
- **`[DB_IS].dbo.TabDokumenty`** drží sken **dvěma způsoby:**
  - **`JmenoACesta`** (nvarchar) — jméno + cesta k souboru na disku
  - **`Dokument`** (varbinary) — sken **přímo v DB jako BLOB**
  - + `VelikostSouboru` (bigint), `IDDokTyp` (int), `OznaceniDokumentace`, `SignedDoc` (varbinary, podepsaná verze)
- **`[DB_IS].dbo.TabDokumentyAgenda`** = vazba dokument ↔ doklad. **Sloupce jsem NEprozkoumal — to je tvůj první krok** (zjisti, jak se váže na fakturu: nejspíš IDDokument + IDAgenda/IDDoklad/Cislo).
- Další tabulky DMS: `TabDokumentyStitky(Vazba)`, `TabDokumentyPodepisujiciOsoby`.

## Doporučený postup (návrh, uprav dle svého)
1. **Prozkoumej `TabDokumentyAgenda`** (sloupce + jak se IDDoklad/IDAgenda mapuje na `TabDokladyZbozi.ID` = náš `es_doklad_zbozi.src_id`).
2. **Dotáhni vazbu** do es_doklad_zbozi (např. `id_dokument` na řádek faktury), nebo to řeš za běhu joinem přes MCP.
3. **Serving skenu — dvě cesty, vyber:**
   - **(A) BLOB z DB:** `SELECT CAST(N'' AS XML).value('xs:base64Binary(sql:column("Dokument"))','varchar(max)')` přes MCP → base64 → `Response(media_type='application/pdf')`. ⚠ Velký PDF = velká JSON odpověď přes MCP, ohlídej limit.
   - **(B) Disk cesta `JmenoACesta`:** číst přes MCP filesystem, ALE jen pokud je ta cesta v `MCP_FS_RO_ROOTS` (nejspíš NENÍ — Helios má vlastní úložiště; možná půjde přidat root, infra rozhodnutí Marti).
4. **Zapoj do `doklad-pdf` endpointu ES větev** (firma=ES → Helios DMS místo `D:\data\FakturyP`), nebo nový endpoint `doklad-pdf-es`. UI proklik v `hromady.html` na ES faktury je připravený (klikací číslo už tam je, jen pro ES vrací 404 „nemá PDF").

## Pozn. k mostu / koordinaci
- Píšu/čtu sdílené soubory **přes bridge** (`scripts/claude_sql/`), NIKDY git přes mount. Před editem `CLAUDE_PULL_GO.txt` (srovnej lokál).
- Deník je **sandbox** (write do `ucetni_denik`/`_log`/`bank_predkontace` bez banneru); ostatní write přes schvalovací banner.
- Až to dotáhneš, **hoď Marti notifikaci** (doctrine f) a Peti.

Drž se, Claude-26 — papíry tam jsou, vazba je v `TabDokumentyAgenda`, zbytek je řemeslo. 🧾📄

— Claude-23 (ID23)
