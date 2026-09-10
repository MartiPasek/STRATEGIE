# Most: timeout schvalovacího banneru NENÍ storno — zápis zůstává pending a pozdější schválení ho provede

> oblast: `provoz` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)

# Most: „timeout" NENÍ storno zápisu — schválení po hodině ho pořád provede

**Ověřeno naostro 9. 9. 2026 (C24 / Kristý).**

Když zápis přes SQL most čeká na schvalovací banner, runner ho polluje
**120 s natvrdo** (`claude_sql_runner.py`, `_poll_write_status(request_id, max_wait_sec=120)`,
volané bez argumentu — **není na to žádná env proměnná**). Po vypršení napíše do
`watcher.log` `WRITE #<id> resolved: timeout` a do výstupu `STATUS: TIMEOUT`.

## To, co je snadné si z toho odvodit, je ŠPATNĚ

Požadavek **zůstává v `fw.claude_write_request` ve stavu `pending`** a čeká dál.
Když ho člověk odklikne za deset minut nebo za hodinu, **provede se** — jen se to
už žádná instance nedozví, protože runner mezitím přestal poslouchat.

**Doklad:** požadavek **#2847** (havarijní oprava `att_do_att_action`) hlásil timeout
v 11:44:18. Kristý ho odklikla v **11:46:05** a zápis **proběhl** (`status='done'`,
`row_count=0`). Mezi odesláním a schválením přitom jiná instance tutéž funkci opravila —
kdyby zápis neměl pojistku, **přepsal by opravený kód zpátky do rozbitého stavu**.

## Pravidla

1. **Každý zápis musí být neškodný i za hodinu.** Do `WHERE` patří podmínka, která
   ho po zpožděném schválení zneškodní: kontrola `md5(obsah)` / `verze`, nebo
   `length(zdroj) - length(replace(zdroj, kotva, '')) = length(kotva)` (kotva právě jednou).
   Právě tahle podmínka udělala z #2847 neškodných 0 řádků.
2. **`STATUS: TIMEOUT` neznamená „neproběhlo".** Znamená „nevím". Zjisti to čtením —
   `SELECT status, row_count, decided_at FROM fw.claude_write_request WHERE id=<id>` —
   a NIKDY neposílej stejný zápis znovu jen proto, že první hlásil timeout.
3. **Nedokončený zápis nejde vzít zpět.** Watcher si SQL přečte, jakmile se objeví `GO`;
   přepsání `CLAUDE<N>_SQL.sql` už nic nezastaví a `CLAUDE_GO.txt` z Coworku nejde smazat
   (mount nepovoluje mazání). Jediná obrana je pojistka v `WHERE` podle bodu 1.
4. **Když je bannerů moc, timeouty jsou pravidlo, ne výjimka.** 9. 9. 2026 vyrobily tři
   souběžné session Kristý čtrnáct bannerů za hodinu (#2842–#2858) a dva z nich vypršely.
   Souvislost s doktrínou souběhu — čím víc oken, tím delší prodleva mezi odesláním
   a schválením, a tím větší šance, že mezitím někdo jiný sáhl na totéž místo.

