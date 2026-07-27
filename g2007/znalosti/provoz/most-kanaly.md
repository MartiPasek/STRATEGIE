# Most (bridge) — kanály a spouštění

> oblast: `provoz` · úroveň: system · typ: postup · verze: V1.0 · rozsah: globální (všichni tenanti)

# Most (bridge) — kanály a spouštění

Claude obsluhuje STRATEGII přes soubory ve `scripts/claude_sql/` na Martiho stroji (watcher `claude_sql_runner.py`, služba STRATEGIE-CLAUDE-SQL). Zapisuje se přes `device_commit_files` — můj sandbox shell `device_bash` na GitHub NEDOSÁHNE (403 proxy), most ano.

## Kanály
- **SQL:** `CLAUDE_SQL.sql` + `CLAUDE_GO.txt` (1. řádek `db=pg` nebo `db=mssql` + popis). SELECT se spustí sám; WRITE/DDL → Marti schvaluje v banneru. Výsledek `CLAUDE_OUT.txt` (plný `CLAUDE_OUT_FULL.txt`).
- **Git pull (lokál):** `CLAUDE_PULL_GO.txt` (JEN trigger, spotřebuje se) → `fetch + rebase --autostash` lokálu na origin/main, bez commitu. Výsledek `CLAUDE_PULL_OUT.txt`. NENÍ to `CLAUDE_PULL.txt`!
- **Deploy:** `CLAUDE_DEPLOY.txt` (ř.1 = commit msg, další = cesty souborů) + `CLAUDE_DEPLOY_GO.txt` → py_compile gate → commit + push → cloud pull + restart API. Výsledek `CLAUDE_DEPLOY_OUT.txt`.
- **Ops:** `CLAUDE_OPS.txt` (klíčové slovo, např. `service_status`) → stav služeb. `CLAUDE_OPS_OUT.txt`.
- **Docpush:** `CLAUDE_DOCPUSH.txt` (ř.1 lokální složka dokumentů, ř.2 volit. ro_subdir).
- Další: `CLAUDE_NOTIFY`, `CLAUDE_BUILD`, `CLAUDE_TASKS`, `INBOX_MARTI`, `MARTIAI_TO_CLAUDE` (kanál Marti-AI ↔ Claude), `OTHER_CLAUDE_WORK`, `LOCAL_STATUS`, `INSTANCE_ID`.

## Pravidla
Výsledek čti VŽDY `device_bash cat scripts/claude_sql/CLAUDE_*_OUT.txt` — mount byte-counts u velkých souborů lžou. Trigger (`*_GO`) se zapisuje JAKO POSLEDNÍ (watcher na něj čeká).

