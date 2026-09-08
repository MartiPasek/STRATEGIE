# Žádost o souhlas člověka musí jít jako claude_confirm — zpráva (claude_msg) má v appce jen tlačítko OK, takže není co schválit

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Žádost o souhlas člověka musí jít jako `claude_confirm`, ne jako zpráva

**Zjištěno naostro 8. 9. 2026** (Claude-28 / Jiří Honomichl), poté co Kristýna Marešová
řekla, že jí na dvě rozhodnutí, která po ní systém chtěl, **nikdy nepřišel schvalovací
proužek**. Měla pravdu — a nebyla to porucha doručování.

## Co se stalo

Dvě žádosti o rozhodnutí rodiče odešly jako **`claude_msg`** (běžná zpráva):

| kdy | co | jak to přišlo |
|---|---|---|
| 6. 9. 2026 10:01 | otevřít správcům Ops akce, Migraci a Síť Claudů | `claude_msg` 23645 |
| 8. 9. 2026 09:37 | otevřít správcům Řídící centrum | `claude_msg` 23995 |

Obě dorazily a obě si přečetla. **Jenže zpráva se v appce vykreslí s jediným tlačítkem „OK".**

## Proč — je to v kódu appky

Dílky `20_home_phone_notifs.js` a `25_tasks.js` vykreslují tlačítka podle druhu položky:

```js
if (c.command_type === "claude_confirm") { b("Odmítnout","warn","reject"); b("Povolit","green","accept"); }
else { b("OK","ghost","done"); }
```

Takže **jen `claude_confirm` dá člověku Ano/Ne.** U všeho ostatního může jen odklepnout „OK",
což se do dat zapíše jako `status='done'` — a to **není souhlas**, jen potvrzení, že to viděl.

## Souhlas NEMUSÍ být navázaný na zápis do databáze

Do 8. 9. 2026 se `claude_confirm` používal skoro výhradně jako schvalovací proužek k zápisu
(v `payload` je `write_request_id` a kliknutí ten zápis rovnou provede nebo zamítne).
**Ale `payload` může být prázdný** — obsluha v jádře sáhne na zápis jen tehdy, když
`write_request_id` opravdu existuje; jinak jen uloží rozhodnutí a čas. Takže se dá
poslat **čistá otázka pro člověka**, u které se nic samo nespustí.

Precedens, podle kterého se to dělalo: souhlas Petry Šafránkové s přepnutím příplatků
a srážek (*„✍️ Příplatky a srážky — souhlasíš s přepnutím?"*).

## Jak takovou žádost poslat

Řádek do `fw.mobile_command` (jde přes schvalovací proužek, protože to není tabulka G2007):

```sql
INSERT INTO fw.mobile_command (app_key, target_user_id, command_type, title, message, created_by)
VALUES ('mobile', <ID člověka>, 'claude_confirm', '<otázka>', '<text>', <ID zadavatele>);
```

- **Upozornění na telefon odejde samo** — ověřeno 8. 9. 2026 (`tenant.notification_log`
  14677 a 14678, `odeslano = true`), o zápis do notifikací se stará server.
- Do textu patří **co se stane při Povolit a co při Odmítnout** a **kdo o to žádá**.
- **Odpověď se čte z `fw.mobile_command`** — `status` (`accepted` / `rejected`) a `decided_at`.
  Neptej se člověka „klikl jsi?", ale podívej se do dat.
- ⚠️ **Bridge NOTIFY (`CLAUDE_NOTIFY.txt`) umí jen `claude_msg`** — na souhlas se nehodí.

## Poučení

Když po člověku chceš rozhodnutí, **zkontroluj, jakým druhem položky mu to posíláš**.
Zpráva vypadá jako doručená žádost, ale příjemce nemá čím odpovědět — a v datech pak
není žádná stopa souhlasu, jen „přečteno". U rozhodnutí o právech a přístupech to znamená,
že se **nedá doložit, kdo to vlastně schválil**.

