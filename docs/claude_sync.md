# Synchronizace Claudů (23 Marti / 24 Kristy) — freshness + work-lock

Marti 3.6.2026. Cíl: každý Claude na začátku práce ví (a) jestli je na aktuálních
datech (→ pull), (b) co právě staví ten druhý (→ počítá s tím). **Soft/advisory** —
informuje, neblokuje.

## Soubory v `scripts/claude_sql/<machine>` (gitignored, per-stroj)

| Soubor | Píše | Čte | Obsah |
|---|---|---|---|
| `WORK_LOCK.txt` | **Claude (agent)** | watcher | 1. řádek = co stavím, další řádky = soubory |
| `OTHER_CLAUDE_WORK.txt` | watcher | **Claude** | co staví ostatní instance (z heartbeatu) |
| `LOCAL_STATUS.txt` | watcher | **Claude** | jsi N commitů pozadu + poslední cizí commit |

## Tok

```
Claude-A zapíše WORK_LOCK.txt {co + soubory}
   ↓ watcher-A heartbeat (à 30s) → cloud → fw.claude_instance (current_work, files, work_status)
   ↓ cloud heartbeat response pro watcher-B nese „others" vč. current_work
watcher-B zapíše OTHER_CLAUDE_WORK.txt
   ↓
Claude-B čte → ví, co staví Claude-A → uhne / počká / pullne

Souběžně: watcher à 90s `git fetch` → spočítá behind (HEAD..origin/main) →
  LOCAL_STATUS.txt + předřadí ⚠ banner do CLAUDE_OUT (Claude to vidí po každém dotazu).
Po úspěšném deployi watcher WORK_LOCK smaže (práce odeslaná, behind=0).
```

## Konvence agenta (POVINNÉ pro Claude-23 i Claude-24)

1. **Na začátku práce** přečti:
   - `scripts/claude_sql/<machine>/LOCAL_STATUS.txt` → jsem-li pozadu, řekni člověku
     ať udělá `git pull origin main` (než budu editovat sdílené soubory).
   - `scripts/claude_sql/<machine>/OTHER_CLAUDE_WORK.txt` → vím, co staví druhý Claude;
     vyhnu se stejným souborům / zkoordinuju.
2. **Před editací** zapiš `WORK_LOCK.txt`: 1. řádek = stručně co stavím, další řádky =
   soubory/oblast, které se dotknu. (Druhý Claude to do ~30s uvidí.)
3. **Po deployi** watcher WORK_LOCK sám smaže — nemusíš řešit.
4. Každý bridge dotaz: pokud v `CLAUDE_OUT` vidíš `⚠ TVUJ LOKAL JE POZADI` → pull.

Pozn.: cesta `<machine>` = adresář watcheru na daném stroji (23 = Martiho, 24 = Kristýin).
Soubory se NEsynchronizují (gitignored) — každý stroj má své.

## Aktivace (po nasazení kódu — commit ffccc62)

Kód je nasazený (cloud heartbeat + watcher). Aktivace = restart watcheru na obou strojích:

**Marti (23):** lokál už má nový watcher (z deploye). Stačí:
```powershell
Restart-Service STRATEGIE-CLAUDE-SQL
```

**Kristy (24):**
```powershell
cd D:\Projekty\STRATEGIE
git pull origin main
Set-Content -Path "scripts\claude_sql\INSTANCE_ID.txt" -Value "24" -NoNewline   # pokud chybí
Restart-Service STRATEGIE-CLAUDE-SQL
```

## Smoke test (po restartu obou)

1. Claude-23 zapíše `WORK_LOCK.txt` („test sync\nrouter.py"). Do ~30s ověř
   `SELECT instance_id, current_work, work_status FROM fw.claude_instance` → 23 má current_work.
2. Na druhém stroji se do ~30s objeví v `OTHER_CLAUDE_WORK.txt` „Claude-23 STAVI: test sync".
3. Když Claude-23 deployne, Claude-24 dostane v `LOCAL_STATUS.txt` + `CLAUDE_OUT` banner
   „pozadu o 1 commit".
