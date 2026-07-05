# ZADÁNÍ pro Claude‑27 (CMS): Srovnání dokumentů do ZZ_Marti‑AI RO/RW + sémantické indexování

**Zadal:** Marti (přes ID23, 5. 7. 2026). **Vlastník úkolu:** Marti (u1), doména dokumenty/ISO → konzultuj Mísu (u16).
**Cíl (Martiho slovy):** „Máme bordel v dokumentech, nevidím dovnitř STRATEGIE co kde evidujeme. Všechny klíčové files by měly ležet ve složkách ZZ_Marti‑AI RO/RW, ať o nich my lidé víme a vy je máte sémanticky zaindexované. Doplnit tam dokumenty ze STRATEGIE, které tam nejsou. Hezky přehledně a do správné adresářové struktury."

ID23 tenhle úkol **nepřesouvá sám** — připravuje ti kompletní data, ať to odmakáš ty na druhém stroji. Postupuj s rozmyslem, po fázích, a klíčová rozhodnutí (finální strom, co je „klíčový dokument") si nech odsouhlasit od Marti/Mísy.

---

## 1) Současný stav (ověřeno v DB + přes @@FILES LISTREC, 5. 7. 2026)

### Fyzické složky za MCP EUROSOFT (kořen `D:\Data\...`, EC‑SERVER2)
- **`D:\Data\ZZ_Marti-AI RO`** = lidský RO strom (lidé jen čtou, píše MCP/Claude). **1 736 souborů**, 3 top složky:
  - `BOZP_PO\` (+ `_ARCHIV_PO\`, `_ARCHIV_RW\`) — bezpečnost práce a PO, hodně dokumentů
  - `Personalistika_NEW\`
  - `Prezentace_IT\`
- **`D:\Data\ZZ_Marti-AI RW`** = pracovní sandbox (Claude + Marti‑AI, plný zápis). ~47 položek:
  - `EUROSOFT_STRATEGIE_prehled_2026.pdf` (v1 přehled)
  - `Ceniky\` — 18 dodavatelských ceníků XLSX (Eaton, Finder, Harting, LAPP, MBS, Murr, PhoenixContact, Pilz, Rittal, Rockwell, Schneider, Siemens, SOCOMEC, WAGO, Weidmüller, Woehner, PrevodniTabulka…)

### DB STRATEGIE — `public.documents` (2 046 dokumentů, ~366 MB)
| projekt | dokumentů | pozn. |
|---|---|---|
| **(project_id NULL)** | **1 278** (303 MB, 24 typů) | ČERNÁ DÍRA — nezařazené, směs |
| DB_EC | 655 (864 kB, 1 typ) | drobné (extrakty/přílohy EC) |
| TISAX (project_id **5**, tenant 2) | 104 (59 MB) | fyzicky `D:\Data\STRATEGIE\Dokumenty\2\<id>.<ext>` |
| ŠKOLA | 9 (3,9 MB) | |

**Rozpad 1 278 bez projektu (typy):** pdf 572 (197 MB), png 321 + jpg 163 + jpeg 10 + gif 4 + heic 1 (~500 obrázků — **hodně inline z mailů = ŠUM**), xlsx 46, docx 40, doc 24, xls 13, pptx 7, xlam 5, xlsm 2, **py 25 (generátorové skripty = artefakty, NE dokumenty)**, isdoc 19 + isdocx 2 (EDI faktury), md 11, txt 4, html/htm 3, p11 2 (cert), json/sql 1.
Úložiště DB dokumentů: `public.documents.storage_path` (na cloud APP, typicky `C:\Data\STRATEGIE\Dokumenty\<tenant>\<id>.<ext>`).

### Sémantické indexování (stav)
- `tenant.kb_smernice`: **704/704 embedded** (BOZP: 35 bezpečnostních směrnic, ISO/TISAX: 7 — vše embedded).
- TISAX projekt 5: **71/104 dokumentů má vektory** (931 chunků). **33 chybí** (skeny/obrázky bez OCR / nepodporované formáty).
- `public.document_vectors`: 7 201 chunků celkem (RAG). Vazba: `document_vectors.chunk_id → document_chunks.id → document_chunks.document_id → documents.id`.
- **Auto re‑embed (LIVE od 4. 7.):** `tenant.knowledge` + `tenant.kb_smernice` mají vlajku `reembed_due` + trigger + self‑gated pass v `_att_sync_loop` (edit textu → sám přeembeduje). RAG dokumenty (document_vectors) tímhle NEJEDOU — ty se indexují při ingestu.

---

## 2) Cílový stav
1. **RO = jediný přehledný lidský strom** klíčových dokumentů, organizovaný per doména. Lidé vidí (RO), vědí co kde je.
2. **RW = pracovní/staging** (Claude/Marti‑AI); z něj se publikuje do RO (`@@FILES COPY RW >> RO`).
3. **Vše sémanticky zaindexované** — fyzické RO soubory, které ještě nejsou v RAG, ingestovat; TISAX 33 doembedovat.
4. **Doplnit chybějící** — business dokumenty ze STRATEGIE DB, které v RO/RW nejsou.

### Navržená struktura RO (nástřel — dolaď s Marti/Mísou)
```
ZZ_Marti-AI RO\
  BOZP_PO\            (už existuje)
  Personalistika\     (sjednotit s Personalistika_NEW)
  ISO_TISAX\          (DOC-xx politiky, SoA, VDA ISA, TISAX dokumenty projektu 5)
  Ceniky\             (z RW – dodavatelské ceníky)
  Smlouvy\            (rámcové, pronájem serveru ES↔ST, T-Mobile…)
  Obchod_CRM\         (nabídky, kampaně, zákaznické standardy)
  Vyroba\             (výrobní standardy zákazníků, EPLAN)
  Ekonomika_Ucetnictvi\ (ISDOC faktury, daně, DPPO)
  STRATEGIE_dokumentace\ (přehledy, architektura, prezentace)
  _ARCHIV\            (staré verze)
```

---

## 3) Triáž pravidla (KLÍČOVÉ — ne slepé kopírování)
- Do RO **jen skutečné business dokumenty**. **NEPATŘÍ** tam: inline obrázky z mailů (png/jpg podpisy/loga/screenshoty), sandbox `.py` skripty, dočasné generované `.md`, duplicitní `Thumbs.db`.
- **Dedup:** nekopíruj, co už v RO je (porovnej podle názvu + velikosti/hashe).
- **Verze:** zachovej `V1/V2` a datumové sufixy v názvech; starší verze → `_ARCHIV\`.
- **Citlivé:** mzdy jednotlivců, tokeny, hesla do RO NEPATŘÍ (jen sandbox/trezor). Finance osob řeš s Petrou/Mísou.
- U 1 278 bez projektu očekávej, že **reálných business dokumentů bude výrazná menšina** (velká část = mailový šum + artefakty). Radši konzervativně.

## 4) Nástroje (Claude SQL bridge — `scripts/claude_sql/`, VŽDY CLAUDE_SQL.sql přes Write tool)
- **Čtení složek:** `@@FILES LIST <abs>` / `@@FILES LISTREC <abs>` (kořen jen `D:\Data\...`).
- **DB dokument → RW:** `@@FILES PUTDOC <rw_dest_path> <doc_id>` (přečte `public.documents.storage_path`, pošle na RW přes MCP). *(Postavil ID23 4. 7., commit 7de2c52.)*
- **RW → RO:** `@@FILES COPY <src_abs> >> <dst_ro_subpath>` (server‑side, MCP). Hromadně `@@FILES COPYDIR`, `@@FILES COPYTREE`, `@@FILES COPYBATCH`.
- **Repo → RW:** `@@FILES PUTREPO <rw_dest> <repo_src>` / `PUTREPODIR`.
- **Úklid:** `@@FILES RMDIR`, `@@FILES REORG` (hromadné přejmenování/přesun).
- **DB dotazy:** `db=pg` na `public.documents` (id, name, original_filename, file_type, project_id, storage_path, file_size_bytes). Pro TISAX: `WHERE project_id=5`.
- **Indexování RAG:** fyzické soubory, co nejsou v `documents`, nahraj do STRATEGIE (upload → chunk → `document_vectors`). TISAX 33 bez vektorů: dohledej přes `document_vectors ← document_chunks ← documents WHERE project_id=5` které chybí, doOCR/embed.

## 5) Fázový plán (doporučené pořadí)
- **F0 — Inventura:** `@@FILES LISTREC` obou složek (celé stromy) + `db=pg` dump `public.documents` (id, name, type, project, storage_path). Ulož si mapu.
- **F1 — Strom:** dotáhni finální strukturu RO (výše je nástřel) → **odsouhlas Marti/Mísou** přes @@COORD nebo mail.
- **F2 — Triáž:** roztřiď DB dokumenty (business vs šum) a namapuj na cílové složky. Vyřaď obrázky/artefakty.
- **F3 — Naplnění:** chybějící business DB dokumenty → RW (`@@FILES PUTDOC`) → RO (`@@FILES COPY`), organizovaně, s dedup.
- **F4 — Indexace:** RO fyzické soubory, které nejsou v RAG, ingestuj → sémanticky prohledatelné.
- **F5 — TISAX 33:** doembeduj (OCR skenů) → 104/104.
- **F6 — Přehled pro lidi:** vygeneruj do RO `_PREHLED.md` (co kde je) + ověř v cockpitu/appce. Nahlas hotovo.

## 6) Gotchy / pravidla
- `@@FILES` bere jen kořen `D:\Data\...`, NE UNC přes hostname.
- RO je lidem **read‑only** (píše jen MCP/Claude); RW plný zápis.
- **Nemazej originály**, dokud není zkopírováno + ověřeno (idempotence, dedup).
- Velké soubory (Siemens ceník 46 MB apod.) — kopíruj server‑side (`@@FILES COPY/COPYTREE`), ne přes base64.
- **Před editem sdílených souborů srovnej lokál** (`CLAUDE_PULL_GO.txt` → rebase), NIKDY git přes mount.
- Postup hlas přes `@@COORD` / notifikaci; koordinační páteř = ID23.
- Dotazy/blokace → napiš ID23 (přes @@COORD nebo most), doladíme.

— Připravil **Claude ID23** (páteř sítě) pro **Claude‑27 (CMS)**, 5. 7. 2026.
