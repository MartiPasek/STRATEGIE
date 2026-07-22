# Claude SQL most - lanes 1-3, OPS lane a gotchy z ostreho provozu

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Claude SQL most — lanes 1-3 + OPS lane (restart služeb)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.1 · rozsah: globální (všichni tenanti)

# Claude SQL most — víc-lane vstup + OPS lane (restart služeb)

Oblast: system-strategie. Zdroj: C23 (Marti/Cowork), 21.7.2026. Runner: `scripts/claude_sql_runner.py`, služba NSSM `STRATEGIE-CLAUDE-SQL`.
Doplněno 22.7.2026 (Claude-28/Jirka) — §Gotchas 4–7 z ostrého provozu.

## Multi-lane vstup (víc Cowork session na JEDNOM stroji)
Víc souběžných Cowork session psalo do jednoho kanálu (`CLAUDE_SQL.sql`/`CLAUDE_GO.txt`) → kolize. Fix = lanes s indexem:
- Lane 1 (default, beze změny): `CLAUDE_SQL.sql` / `CLAUDE_GO.txt` / `CLAUDE_OUT.txt` / `CLAUDE_OUT_FULL.txt`.
- Lane 2: `CLAUDE2_*`. Lane 3: `CLAUDE3_*` (přidáno 21.7. pro Kristý+Peťu, kteří jedou 3 session naráz).
- DEFAULT runneru = lanes 1–3 (`CLAUDE_EXTRA_LANES` default `"2,3"`); víc přes env `CLAUDE_EXTRA_LANES="2,3,4"`.
- Prefix `CLAUDE<N>_` (ne `__N`) schválně — nekoliduje s nonce úklidem lane1.
- Společné (ne per-lane): deploy/pull/notify/build/docpush/OPS, `WORK_LOCK.txt`, heartbeat. Jen SQL dotaz má lane.
- Session svůj Cowork title NEVIDÍ (`get_device_info` vrací jen deviceName+složky) → self-identifikace řádkem do `WORK_LOCK.txt` na startu; novou session ber na první volnou lane (1→2→3).

## OPS lane — restart služeb PŘÍMO z mostu (bez schvalování, s auditem)
Motivace: Claude nemá shell na Windows hostu (device_bash = izolovaný Linux VM jen se složkou; cloud bash = jiný stroj), takže služby nešly restartovat. Watcher ale na Windows běží → dá se to přes trigger soubor.
- Vstup: `CLAUDE_OPS.txt` (1. řádek = akce) + `CLAUDE_OPS_GO.txt` (JAKO POSLEDNÍ).
- Výstup: `CLAUDE_OPS_OUT.txt`. Audit: append-only `CLAUDE_OPS_LOG.txt` (+ `watcher.log`).
- Akce: `restart_service <NAME>` (whitelist regex `^STRATEGIE-[A-Za-z0-9-]+$`, nic systémového) · `restart_self` (restart watcheru) · `service_status [<NAME>|prázdné = všechny STRATEGIE-*]`.
- BEZ schvalovacího banneru (rozhodnutí Marti 21.7.), ale S AUDITEM (doctrine #21 „audit = paradoxně víc bezpečí"). Restart je reverzibilní, proto bez gate.
- Restart vlastní služby jde detached (nelze synchronně) — `restart_service STRATEGIE-CLAUDE-SQL` i `restart_self` volají `_restart_self()` (odpojený PowerShell, za ~3 s).

## Gotchas
1. Po JAKÉKOLI změně `claude_sql_runner.py` MUSÍ restart služby (LANES i handlery se čtou při načtení modulu). Bootstrap nové verze = 1× ruční restart, pak self-service přes `restart_self`.
2. Každý stroj má vlastní watcher ze svého lokálu → Kristý (C24), Peťa (C26), Jirka (C28) musí `git pull` + restart svého watcheru, jinak lane 3/OPS lane nevidí.
3. device_stage_files (9p mount) servíruje fixní soubory STALE; `device_bash cat` čte živě. Velké soubory eDituj atomicky (python temp→os.replace), ne append přes mount.
4. **⚠️ BOM na začátku `CLAUDE*_SQL.sql` udělá ze SELECTu ZÁPIS.** Klasifikace zápis/čtení se dívá na PRVNÍ klíčové slovo; když soubor začíná `﻿`, neshoduje se se `SELECT` → dotaz spadne do write-approval větve, **Martimu přijde falešný schvalovací banner + push** a lane se zablokuje pollingem (až 120 s). V PowerShellu to způsobí `Set-Content -Encoding utf8` (PS 5.1 píše UTF-8 **s BOM**). Řešení: psát `CLAUDE*_SQL.sql` **Write toolem** (bez BOM), nebo `[System.IO.File]::WriteAllText(path, text, (New-Object System.Text.UTF8Encoding($false)))`. Pozorováno 22.7. (requesty #1291, #1292 = obyčejné SELECTy).
5. **Diakritika v SQL přes most se překóduje** (`Příplatk` → `Ĺ™Ă­platk`); u MSSQL se to projeví jako `internal_error`, u PG jako nesmyslné porovnání. **Přes most piš ASCII-only dotazy** (`LIKE '%riplatk%'` místo `'%říplatk%'`). Týká se i commit zpráv v `CLAUDE_DEPLOY.txt` (BOM/diakritika skončí v git logu).
6. **Hláška „plný výstup bez ořezu" ukazuje vždy na `scripts/claude_sql/CLAUDE_OUT_FULL.txt`, i když jedeš na lane 2/3.** Soubor se přitom zapíše správně do `CLAUDE2_OUT_FULL.txt`. Kosmetická chyba, ale svádí přečíst cizí lane — což je přesně to, čemu mají lanes bránit. Čti vždy soubor SVÉ lane.
7. **Deploy může hlásit `dirty_working_tree` (= NENASAZENO), i když commit+push proběhl.** Je to stav pracovního stromu na cloud APP, ne tvoje chyba; commit v gitu je, na produkci ale ne. Ověřuj `fw.api_version` (řádek `current` nese `git_sha` + čas restartu), ne návratovku. Když to trvá, opakuj deploy — po chvíli projde („cloud: OK, API restart").

## Souvislosti
- [[doc-mzdy-priplatky-srazky]] (ostrý provoz 22.7., odkud gotchy 4–6 pocházejí)


