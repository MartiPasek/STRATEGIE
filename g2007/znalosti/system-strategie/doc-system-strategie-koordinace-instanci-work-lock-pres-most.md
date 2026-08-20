# Koordinace instanci: @@WORK/@@LOCK/@@WHO pres most misto WORK_LOCK.txt (bod 2)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

## Proc
`WORK_LOCK.txt` (git-trackovany sdileny soubor) se dostaval do merge konfliktu (`UU`), ktere blokovaly commit VSEM instancim na stroji. Bod 2 (Marti 5.8.2026) to presouva do databaze.

## Nove prikazy mostu (diag_sql, konstruktivni, bez banneru; instance_id volajiciho z requestu)
- `@@WORK <tema> [| <soubory>]` — nastav "delam na cem" (→ `fw.claude_instance.current_work*`). Nahrazuje radek do WORK_LOCK.txt. Existujici heartbeat board (`OTHER_CLAUDE_WORK.txt`) to ukaze.
- `@@WORKDONE` — vycisti current_work (→ idle).
- `@@LOCK <scope> <key> [| <note>]` — **MEKKY** exclusive zamek (→ `fw.work_lock`). Marti 5.8.: tvrde blokovani by prineslo deadlocky, takze zamek JEN OHLASI obsazeni ("uz drzi C-XX"), akci NEBLOKUJE. TTL 15 min.
- `@@LOCKBEAT <scope> <key>` — prodluz TTL o 15 min (dlouha prace).
- `@@UNLOCK <scope> <key>` — uvolni svuj zamek.
- `@@WHO` — nastenka: kdo dela na cem (aktivni instance) + aktivni zamky.

## Konvence (nahrazuje editaci WORK_LOCK.txt)
- Start prace: `@@WORK <tema> | <soubory>` (misto radku do WORK_LOCK.txt).
- Pred sahnutim na sdileny zdroj: `@@LOCK file <cesta>` / `@@LOCK service <name>` / `@@LOCK repo deploy` (+ `@@LOCKBEAT` pri delsi praci).
- Prehled ostatnich: `@@WHO`.
- Konec: `@@UNLOCK <...>` + `@@WORKDONE`.

## Vlastnosti / gotchy
- **Serverove** (v diag_sql na cloudu) → vsechny instance je pouzivaji HNED, bez zasahu do runneru na strojich. Rollout = jen rict konvenci.
- Tabulka `fw.work_lock` (PostgreSQL data_db 188.12, schema Marti-AI). FK `instance_id → fw.claude_instance(instance_id)` (PK). Unique `(scope, lock_key)` PLNY (ne partial s NOW() — PG nedovoli STABLE fci v predikatu indexu); acquire dela `DELETE WHERE expires_at < NOW()` pred INSERT.
- **current_work vlastni @@WORK/@@WORKDONE**, ne heartbeat. Fix (5.8., commit b99932dd): heartbeat prepisuje current_work JEN kdyz nese NEPRAZDNOU hodnotu (runner ho cte z WORK_LOCK.txt, casto prazdne → driv mazal @@WORK). Zpetne kompatibilni: kdo jeste pise do WORK_LOCK.txt, tomu to jede taky.
- Commity: @@ prikazy c3ae1456; fix heartbeat b99932dd.

## Zbyva
`WORK_LOCK.txt` po prechodu → gitignore + nechat posledni stav jako archiv (Marti rozhodl; udelat az budou instance na nove konvenci, nemazat zprudka). Doplnit konvenci do CLAUDE.md multi-lane sekce.

