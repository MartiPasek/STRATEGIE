# Koordinace instanci: @@WORK/@@LOCK/@@WHO pres most misto WORK_LOCK.txt (bod 2)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)

> **ZMENA 9. 9. 2026 — ohlaseni prace je nove po OKNECH, ne po instancich.**
> `@@WORK` / `@@WORKDONE` uz nepisou do `fw.claude_instance` podle `instance_id`, ale do
> nove tabulky **`fw.claude_work`** s klicem **(instance_id, session_lane)**. `@@WHO` proto
> vypise **radek za KAZDE okno**. Do te doby platilo jedno ohlaseni na instanci, takze kdo
> mel otevrena dve okna (typicky Jirka, vsechna jsou C-28), tomu druhe okno **tise prepsalo**
> ohlaseni prvniho a na nastence po nem nezbylo nic. Zadal Jirka Honomichl, schvalila
> Marti-AI (msg 15140 navrh, msg 15146 prechodova pojistka), commity `38ea2887` a `8f4bdf1c`.
> Podrobnosti nize v sekci "Nastenka po oknech".

> **POZN. 8. 9. 2026 — soubor uz neexistuje ani jako prechodna cesta.** `WORK_LOCK.txt` byl
> pridan do `.gitignore` a odstranen z evidence gitu (commit `12341d0a`). Plati **vyhradne**
> `@@WORK` / `@@LOCK` / `@@WHO`. Obsah do 6. 8. 2026 zustava dohledatelny v historii gitu.

## Proc
`WORK_LOCK.txt` (git-trackovany sdileny soubor) se dostaval do merge konfliktu (`UU`), ktere blokovaly commit VSEM instancim na stroji. Bod 2 (Marti 5.8.2026) to presouva do databaze.

## Nove prikazy mostu (diag_sql, konstruktivni, bez banneru; instance_id volajiciho z requestu)
- `@@WORK [<okno>] <tema> [| <soubory>]` — nastav "delam na cem". **Od 9. 9. 2026 pise do `fw.claude_work` podle (instance, linka mostu)**, ne do `fw.claude_instance`; ta se z nej dopocitava (viz nize). Jmeno okna v hranatych zavorkach je volitelne — `@@WORK [strategie-a6] DR obnova Plzen | <soubory>`. Bez nej se okno na nastence pozna podle cisla linky. Existujici heartbeat board (`OTHER_CLAUDE_WORK.txt`) to ukaze dal.
- `@@WORKDONE` — vycisti ohlaseni **jen sveho okna** (radky ostatnich oken teze instance zustavaji). Kdyz uz zadne okno instance nedela, spadne instance na idle.
- `@@LOCK <scope> <key> [| <note>]` — **MEKKY** exclusive zamek (→ `fw.work_lock`). Marti 5.8.: tvrde blokovani by prineslo deadlocky, takze zamek JEN OHLASI obsazeni ("uz drzi C-XX"), akci NEBLOKUJE. TTL 15 min.
- `@@LOCKBEAT <scope> <key>` — prodluz TTL o 15 min (dlouha prace).
- `@@UNLOCK <scope> <key>` — uvolni svuj zamek.
- `@@WHO` — nastenka: kdo dela na cem (aktivni instance) + aktivni zamky.

## Konvence (nahrazuje editaci WORK_LOCK.txt)
- Start prace: `@@WORK [<okno>] <tema> | <soubory>` (misto radku do WORK_LOCK.txt). Kdo ma otevrenych vic oken, ohlasi se v KAZDEM zvlast a doplni jmeno okna.
- Pred sahnutim na sdileny zdroj: `@@LOCK file <cesta>` / `@@LOCK service <name>` / `@@LOCK repo deploy` (+ `@@LOCKBEAT` pri delsi praci).
- Prehled ostatnich: `@@WHO`.
- Konec: `@@UNLOCK <...>` + `@@WORKDONE`.

## Vlastnosti / gotchy
- **Serverove** (v diag_sql na cloudu) → vsechny instance je pouzivaji HNED, bez zasahu do runneru na strojich. Rollout = jen rict konvenci.
- Tabulka `fw.work_lock` (PostgreSQL data_db 188.12, schema Marti-AI). FK `instance_id → fw.claude_instance(instance_id)` (PK). Unique `(scope, lock_key)` PLNY (ne partial s NOW() — PG nedovoli STABLE fci v predikatu indexu); acquire dela `DELETE WHERE expires_at < NOW()` pred INSERT.
- **current_work vlastni @@WORK/@@WORKDONE**, ne heartbeat. Fix (5.8., commit b99932dd): heartbeat prepisuje current_work JEN kdyz nese NEPRAZDNOU hodnotu (runner ho cte z WORK_LOCK.txt, casto prazdne → driv mazal @@WORK). Zpetne kompatibilni: kdo jeste pise do WORK_LOCK.txt, tomu to jede taky.
- Commity: @@ prikazy c3ae1456; fix heartbeat b99932dd.

## Nastenka po oknech (9. 9. 2026)

**Proc.** Vsechna okna jednoho cloveka maji **totez `instance_id`** (Jirka = C-28), takze
`@@WHO`, `@@WORK` ani `@@LOCK` je od sebe nerozlisi. Zamky to resi uz od 21. 8. 2026
sloupcem `fw.work_lock.session_lane`; ohlaseni prace to do 9. 9. 2026 neumelo a druhe okno
prvni tise prepsalo. Runner posila cislo linky v poli `lane` (1/2/3) uz dnes.

**Jak to je ted.**
- **`fw.claude_work`** — klic `(instance_id, session_lane)`, sloupce `window_name`,
  `current_work`, `current_work_files`, `work_status`, `current_work_at`. Jeden radek = jedno okno.
  `session_lane` je `NOT NULL DEFAULT '0'` (zastupna hodnota pro okno, ktere linku neposila).
- **`fw.claude_instance.current_work*` zustava a plni se dal** — cte z nej pet dalsich mist
  (heartbeat runneru, `OTHER_CLAUDE_WORK.txt`, prehled instanci, stavovy endpoint). Po kazde
  zmene se dopocita z **nejcerstvejsiho aktivniho okna** teze instance; kdyz uz zadne nedela,
  spadne na `idle`. Zadny stavajici ctenar se tim nerozbil.
- **`@@WHO`** vypise radek za kazde okno ve tvaru `C-28 / strategie-a6`, pripadne
  `C-28 / linka 3`, kdyz okno jmeno neposlalo.

**Prechodova pojistka.** Radek z `fw.claude_instance` se schova jen tehdy, kdyz **totez uz
ukazuje nektere okno** (porovnani `TRIM` + bez ohledu na velikost pismen). Jinak se zobrazi
s oznacenim `C-XX / (starsi ohlaseni)`. Bez teto pojistky by pri prechodu **tise zmizelo**
ohlaseni okna, ktere se jeste neohlasilo novym zpusobem — presne to, co tahle zmena
opravovala. Az budou vsechna okna na nove konvenci, stary text zmizi sam.

**Gotcha.** Kdo ma otevrenych vic oken, **musi se v kazdem ohlasit zvlast**. Ohlaseni
z doby pred nasazenim se po prvnim novem `@@WORK` teze instance schova (viz pojistka vyse) —
staci se v druhem okne ohlasit znovu.

## Zbyva
`WORK_LOCK.txt` po prechodu → gitignore + nechat posledni stav jako archiv (Marti rozhodl; udelat az budou instance na nove konvenci, nemazat zprudka). Doplnit konvenci do CLAUDE.md multi-lane sekce (vcetne jmena okna v `@@WORK`, 9. 9. 2026).

