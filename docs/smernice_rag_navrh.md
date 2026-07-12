# 📚 RAG modul SMĚRNICE — know-how celé firmy do vyhledatelné znalostní báze

> Cíl (Marti 1. 7. 2026): *„RAG všech směrnic → pak přes most přístup pro Claude k celému RAG a know-how."*
> Zdroj = EC_OrgSmernice (DB_EC) + přílohy na sdíleném disku. Grounded na skutečné struktuře.

## 1. Zdroje (ověřeno v DB_EC)

| Zdroj | Objem | Obsah |
|---|---|---|
| `EC_OrgSmernice` | **1453 směrnic** (633 aktivních) | metadata: Cislo, Nazev, TypText, Priorita, Platnost, Verze, StatusText, CisloOrg, kategorie |
| `EC_OrgSmernice.Popis` (ntext) | **1340 s textem** (⌀ ~1 kB) | tělo směrnice — RAG-ovatelné rovnou z DB |
| **Přílohy na disku** | `\\192.168.30.11\Smernice\Verejne\SM<Cislo>\` | PDF/DOC/XLS s reálným know-how (schémata, tabulky, návody) — *„jde o soubory v příloze"* |
| `EC_OrgSmerniceCiselniky` | — | číselník kategorií (pořádek) |

Pozn.: EC_Soubory (23 ř.) NENÍ zdroj příloh směrnic — ty jsou soubory na SMB share (folder per směrnice = `SM` + Cislo, sekce Verejne/Neverejne).

## 2. Architektura (3 vrstvy, přírůstkově)

**Vrstva A — metadata + Popis (bez závislosti, hned):**
- `tenant.kb_smernice` — zrcadlo směrnic (ec_id, cislo, nazev, typ, kategorie, popis_text, status, verze, platnost, org). Sync přes bridge z DB_EC.
- Popis (1340×) → chunk + embed → hned vyhledatelné.

**Vrstva B — přílohy (potřebuje 1 config krok):**
- MCP `eurosoft_file_list`/`read` čte `\\192.168.30.11\Smernice\...` → cloud API extrahuje text (pdf/doc/xls) → `tenant.kb_smernice_soubor` (ec_id, nazev_souboru, typ, text, hash) → chunk + embed.
- **Závislost:** přidat kořen Smernice do `MCP_FS_RO_ROOTS` v NSSM env EUROSOFT-MCP na EC-SERVER2 + restart služby. (Marti — jediný ruční krok; env na serveru nevidím/needitujeme z cloudu.)

**Vrstva C — embedding + vyhledávání (reuse Marti Memory RAG / pgvector):**
- `tenant.kb_chunk` (source_type 'smernice'/'priloha', ec_id, chunk_text, embedding vector, meta) — pgvector index.
- Embedding přes stávající infra (Marti Memory používá pgvector + embed pipeline).

## 3. Přístup pro Claude přes most (cíl Martiho)

- **`@@KB <dotaz>`** (bridge command, token-auth) — semantické vyhledání v `kb_chunk` → vrátí top-N úryvků + odkaz na směrnici (cislo, nazev, soubor). Můj přímý přístup ke know-how celé firmy.
- **`@@KB SMERNICE <cislo|text>`** — konkrétní směrnice + její přílohy (seznam + text).
- Volitelně UI dlaždice „📚 Znalostní báze" (RO pro okruh) — vyhledávač nad směrnicemi.

## 3b. Přístupové sekce = složky na share (Marti 1. 7.) — podle pole `Pristupnost`

Přílohy jsou ve více sekcích, ne jen veřejné. Aktivních 633, rozdělení:

| PristupnostText | Počet | Složka na share (odhad) | RAG úroveň |
|---|---|---|---|
| Veřejná | 379 | `\Smernice\Verejne\SM<n>` | member+ (všichni RO) |
| Vedoucí | 184 | `\Smernice\Vedouci\SM<n>` | vedoucí+ |
| Plná | 60 | (ověřit — Verejne/Plna) | dle obsahu |
| Interní | 5 | `\Smernice\Interni\SM<n>` | interní/parent |
| Vedení | 5 | `\Smernice\Vedeni\SM<n>` | vedení/parent |

➡️ **Resolver složky:** `Pristupnost` → sekce → `SM`+`Cislo`. **RAG nese úroveň přístupu** (`pristupnost_text`) → vyhledávání ctí, kdo co smí (běžný člen jen Veřejná, vedoucí výš, Interní/Vedení jen parent). Přesné názvy složek ověřím `eurosoft_file_list` na kořeni share po zapnutí FS rootu.

Typy (pořádek): Směrnice 379 · Formulář 133 · Nápověda 60 · Informace 43 · Školení 16 · Rozhodnutí 2.

## 4. Pořádek (Martiho *„a pořádek"*)

- Kategorizace směrnic dle `EC_OrgSmerniceCiselniky` + TypText (Směrnice/Formulář/Informace) + org (EUROSOFT/zákazník: ABSAUGWERK/AUTKOM/DÜCKER/KOHLBACH/FOUNDRY…).
- Verze: RAG drží jen nejnovější aktivní verzi (Archiv=0), staré verze mimo (ať nešumí).
- Doména „výroba rozvaděčů" = samostatný pohled/filtr (Eliščino jádro) → napojení na kalkulační digitalizaci (SRDCE FIRMY).

## 4b. STAV (1. 7. 2026 večer) — LIVE

- ✅ **Vrstva A LIVE**: modul `modules/erp/api/smernice_rag.py` nasazen. `@@SMSYNC` zrcadlil **633 aktivních směrnic** do `tenant.kb_smernice`. `@@KB` hledání ověřeno (našlo KOHLBACH M-BUS podle obsahu). Respektuje úroveň přístupu.
- ✅ **Naming složek potvrzen: `SM<ec_id>`** (KOHLBACH ec_id 372 → `SM372`), sekce = Pristupnost.
- ⏳ **Vrstva B čeká na FS root**: přidat do `MCP_FS_RO_ROOTS` (NSSM EUROSOFT-MCP na EC-SERVER2) kořen `\\192.168.30.11\Smernice` + restart služby. Pak `@@SMFILES` naplní přílohy.
- Bridge příkazy: `@@SMSYNC`, `@@SMFILES [limit] [ec_id]`, `@@KB <dotaz> [| level]`.

## 5. Plán realizace

1. **A** — DDL kb_* + mirror 1453 směrnic + Popis (dnes, bez závislosti). ← startuju
2. **B** — přidat FS root (Marti) → ingest příloh + extrakce textu.
3. **C** — embedding + `@@KB` most + (volit.) UI vyhledávač.
4. Rozvaděčové .md „nakopnutí" (Rozvadece.md a další) = destilát z RAG po naplnění příloh.

*Pozn.: první rozvaděčový destilát (koeficienty, VKM, překlad čísel, katalog cen) už je v `docs/srdce_firmy_kalkulace_nabidky_analyza.md`.*
