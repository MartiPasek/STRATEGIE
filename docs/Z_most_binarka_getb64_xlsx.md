# Most: bezztrátový přenos souborů k LLM — @@FILES GETB64 + @@FILES XLSX

**Oblast:** system-g2007 · **Zapsal:** Claude-26 (Marti), 20. 7. 2026
**Pro koho:** všechny file-based Claude instance. Používej místo mangleného `@@FILES READ` u binárek.

## Problém (proč READ nestačí)
`@@FILES READ` čte přes EUROSOFT MCP base64 → server ho dekóduje na bajty →
**dekóduje jako text (utf-8/latin-1)**. U ne-textových souborů (xlsx = ZIP, msg = OLE,
docx, obrázky) to poslední text-dekódování binárku **nevratně rozbije** (magic zůstane,
ale ZIP/OLE struktura je pryč). PDF chodí, protože se z něj extrahuje text.

## Řešení — dva nové režimy (Claude-26, 20.7.2026, commit 2e694191)

### 1) `@@FILES GETB64 <abs_cesta>` — bezztrátová binárka
Vrátí **surový base64 BEZ text-dekódu**. Watcher uloží ASCII base64 do
`scripts/claude_sql/files/<name>.b64` (base64 = čisté ASCII → přežije UTF-8 zápis).
Postup pro cloud/LLM instanci:
1. `@@FILES GETB64 D:\Data\...\soubor.xlsx`
2. `device_stage_files` na `D:\Projekty\STRATEGIE\scripts\claude_sql\files\soubor.xlsx.b64`
3. u sebe: `base64.b64decode(open(...).read())` → originální bajty.
Ověřeno: `EK263390…xlsx` = 805 939 B přesně, openpyxl otevřel bez chyby.

### 2) `@@FILES XLSX <abs_cesta>` — extrakce buněk na serveru (data, ne binárka)
Server přečte sešit (openpyxl pro .xlsx/.xlsm, xlrd pro .xls) a vrátí **TSV per list**
(ořez 500 řádků/list). Binárka **vůbec neopustí server** → data minimization (ISO/TISAX).
Použij, když potřebuješ jen data z tabulky, ne původní soubor.

## Kdy co
- binárka obecně (xlsx, msg, docx, zip, obrázky) → **GETB64**
- tabulka, kde stačí data → **XLSX** (rychlejší, bez přenosu binárky)
- PDF → `READ` (už extrahuje text; sken → OCR chybí)
- textový soubor (txt, csv, xml, json, sql) → `READ`

## Bezpečnost (nic nového se neotevřelo)
Obojí jede přes stávající **RO** namespace + whitelist `MCP_FS_RO_ROOTS` + TLS kanál
aplikace. Base64 je jen kódování, ne nová datová cesta. Soubor končí v privátním
session kontejneru dané instance. Mění se jen cloudová aplikace (router `@@FILES`);
watcher ani model oprávnění se nedotýká. Read-only — zápis zpět tudy nejde.

## Pozn.
Definováno v `modules/erp/api/router.py`, handler `@@FILES` (větve `GETB64`, `XLSX`).
Doplňuje `COPY`/`DIRCOPY` (server↔server) — ty jsou pro přesun v rámci serveru, ne k LLM.
