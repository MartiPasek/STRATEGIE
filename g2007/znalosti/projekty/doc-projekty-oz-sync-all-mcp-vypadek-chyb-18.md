# Oz sync all mcp vypadek chyb 18

> oblast: `projekty` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

**oz_sync_all chyb=18 = přechodný výpadek EUROSOFT MCP, data bezpečná, samo se zhojí**

## oz_sync_all: chyb=18 = výpadek MCP (5.9.2026)

### Příznak
`last_result="celkem=0, tabulek=18, chyb=18"` — 100% tabulek selhalo, `last_status=chyba`.

### Root cause
EUROSOFT MCP byl přechodně nedostupný (~2 min). `sync_all()` volá `describe()` pro každou tabulku → `_mcp_query()` → `get_eurosoft_mcp_client()` vrátil None → `RuntimeError("EUROSOFT MCP nedostupný")` → catch per-tabulka → chyb=18.

### Jak poznat příčinu (MCP vs. jiné)
- Všechny tabulky selhaly naráz (100%) → systémová, ne datová chyba
- `oz_mirror_def.last_sync_at` nepřeskočilo na čas selhání (TRUNCATE+INSERT se nestal — `describe()` failovalo ještě před přenosem dat)
- `last_rows=36` není počet řádků — je to `sum({celkem:0, tabulek:18, chyb:18})` = quirk scheduleru
- Ostatní MCP joby (sync_ec_kalkulace, sync_vyroba_plan) po chybě jely OK → MCP se obnovil

### Data jsou bezpečná
TRUNCATE nenastane před úspěšným `describe()`. Tabulky zůstanou s daty z posledního úspěšného běhu.

### Akce
Žádná — job se zhojí při příštím plánovaném běhu (+30 min). Eskalovat pouze pokud i další běh skončí stejnou chybou (MCP trvale padlý).

### Odlišit od false-alarmu (G2007 oz-sync-all-false-alarm)
False alarm: `stav=běží` (running=True) + overdue=False → normální dlouhý běh (~30 min), NE chyba.
Tento vzor: `stav=chyba` + `running=False` + `chyb=18` → reálná chyba, ale přechodná.

_Souvisí:_ oz-sync-all-false-alarm-check-vp-freshness

