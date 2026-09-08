# DB = zdroj pravdy, disk = projekce

> oblast: `system-g2007` · úroveň: system · typ: pravidlo · verze: V1.0 · rozsah: globální (všichni tenanti)

# DB = zdroj pravdy, disk = projekce

Základní provozní pravidlo g2007: **jediný zdroj pravdy je databáze.** Žádný ručně psaný dokument v adresáři není autoritativní. I návrhová rozhodnutí se stávají daty (např. „při chybě eskaluj na LLM" je hodnota ve sloupci, ne odstavec v docu).

Dokumentace se **generuje z DB** na disk do stromu `STRATEGIE/g2007/` (endpoint `/g2007/export`), který běží na app serveru a publikuje přes git — na lokál se dostane `git pull`. Strom je jednorázová projekce: kdo ho smaže, o nic nepřijde, přegeneruje se z DB. Needituje se výtisk — mění se databáze.

Výjimka: spustitelný kód nemůže žít v DB (nespustíš jsonb) — implementace nástrojů zůstává v kódu, DB na ni ukazuje úchytem.

