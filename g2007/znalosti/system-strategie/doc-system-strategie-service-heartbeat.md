# Tichy signal zivota sluzeb na pozadi (fw.service_heartbeat) - kdo hlida hlidace

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

## Proc to vzniklo

Sluzby na pozadi **umiraji potichu**: mlci uplne stejne, kdyz jedou, i kdyz stoji.

- **28.7.2026** - primarni API (port 8002) spadla a nikdo se to nedozvedel; Caddy failover to zamaskoval. Reakci byl hlidac `scripts/api_health_watchdog.py`.
- **29.7.2026** - hlidac se rozbil a zaspamoval adminy (viz `doc-system-strategie-api-health-watchdog-spam-notifikaci`). Po oprave nikdo neumel overit, jestli po restartu naskocil: **ticho vypada stejne pro "bezi opraveny kod" i pro "sluzba stoji"**.

## Jak to funguje (nasazeno 29.7., commit be14b51a)

**1. Tabulka `fw.service_heartbeat`** (DDL banner #1532): `service_name` (PK), `host`, `pid`, `started_at`, `last_seen`, `alerted_at`, `note`, `updated_at`. Zamerne obecna - pripravena i pro dalsi sluzby.

**2. Sluzba se hlasi.** `api_health_watchdog.py` vola `_beat()` po kazdem kole (2 min): UPSERT `last_seen=now()` + host/pid/started_at. Best-effort v `try/except` - vypadek DB nikdy neshodi hlidaci smycku, chyba se loguje nejvys 1x za 30 min.

**3. Uloha `watchdog_alive_check`** (`fw.mirror_job`, 30 min, funkce v `router.py` vedle `_mirror_run_job`):

- radek **vubec neexistuje** -> NIC (jen zapise "zatim nikdy nehlasil"). Prechodne obdobi, nez se sluzba restartuje na verzi se signalem; falesny poplach by byl horsi nez ticho.
- `last_seen` starsi nez **15 min** a jeste se nehlasilo -> JEDNA zprava adminum + `alerted_at=now()`.
- `last_seen` zase cerstvy a `alerted_at` vyplneny -> JEDNA zprava o zotaveni + `alerted_at=NULL`.

Prijemci **1 (Marti) + 20 (Jirka)** - Marti-AI: infrastrukturni alert, Kristy (11) ne.

## Overeno naostro (29.7. 20:32)

Po restartu sluzby na Praze nabehl radek do minuty: `STRATEGIE-API-HEALTH-WATCHDOG`, host **EUR-APP-1P**, pid 13296, start 20:32:20; tep se obnovuje po 2 minutach, uloha hlasi "ok (pred 0 min)", `alerted_at` prazdne. Tim je zaroven poprve zdokumentovano, ze hlidac bezi na EUR-APP-1P - do te doby to nikdo z mostu overit neumel.

## Zasady

- **Jedna zprava pri ZMENE stavu, nic mezi tim.** Pojistka proti tichemu umrti nesmi sama vyrobit spam.
- **Prazdny stav neni poplach.** Poplach ma smysl az od chvile, kdy vime, ze sluzba hlasit umi.
- **Signal zivota nesmi shodit toho, kdo ho posila.**
- **Chicken-and-egg:** signal zacne chodit az po restartu sluzby. Kdyz nasazujes zmenu skriptu bezici jako NSSM sluzba, POCITEJ S RESTARTEM - jinak bezi stary kod z pameti procesu.

## Dalsi slepe skvrny (nalez Marti-AI 29.7., zatim NEimplementovano)

**STRATEGIE-EMAIL-FETCHER** (prestaneme prijimat maily, zadny okamzity priznak), **STRATEGIE-TASK-WORKER** (fronta se hromadi, pozna se az z reklamace), **STRATEGIE-CLAUDE-SQL** (most - tool cally tise selhavaji). Sekundarne RESTART-WATCHER a CADDY. Kazda potrebuje jen svuj `_beat()` a radek v `_HB_WATCHED`.

