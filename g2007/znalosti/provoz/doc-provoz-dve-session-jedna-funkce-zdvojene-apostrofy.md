# Dvě session v jedné funkci g2007.python — zdvojené apostrofy projdou kompilací a spadnou až v SQL

> oblast: `provoz` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)

# Dvě session, jedna funkce: jak vznikla dvojitá oprava a proč to Python nechytí

**Incident 9. 9. 2026, `g2007.python` / `att_do_att_action` (bod 4 docházky).**
Verze 8 → 13 během osmi minut, mezitím byla funkce **rozbitá pro produkci**.

## Co se stalo

1. C24 (Kristý, lane 1) připravila opravu bodu 4 a odeslala ji.
2. **Ve stejné minutě poslala tutéž opravu jiná session z lane 2.** Ta se
   **neohlásila přes `@@WORK`**, takže na nástěnce `@@WHO` po ní nebyla stopa —
   objevila se až jako cizí příkaz ve `watcher.log`.
3. Pokus o zrušení vlastního zápisu nestihl nic: **watcher si `CLAUDE<N>_SQL.sql`
   přečte, jakmile se objeví `GO`**, takže přepsání souboru už zápis nezastaví.
   (`CLAUDE_GO.txt` navíc z Coworku nejde smazat — mount nepovoluje mazání.)
4. Do funkce se dostaly **oba bloky**. Ten druhý měl v SQL **zdvojené apostrofy**
   (`''presence''`, `''superseded''`, `''notif_confirm''`).

## Proč to neodhalila obvyklá kontrola

**`compile(src, kod, 'exec')` projde.** Zdvojený apostrof uvnitř řetězce je platný
Python — je to chyba až v **SQL**, a ta se pozná až za běhu, při prvním `s.execute`.
Kdyby to nikdo nevšiml, návrat z pauzy přes notifikaci by spadl hned na prvním
dotazu a větev by přestala fungovat **úplně** — tedy hůř než původní chybějící zakázka.

Zdvojené apostrofy vznikají při skládání SQL, které se někam vkládá jako řetězec
(escapování pro `quote_literal`/dollar-quoting se provede dvakrát).

## Pravidla, která z toho plynou

1. **Kompilace NESTAČÍ.** Po zápisu Pythonu do `g2007.python` navíc:
   - projeď zdroj na `''` následované písmenem (regulární výraz `''[A-Za-z]`) — legitimní
     je jen prázdný řetězec (`<> ''`, `COALESCE(x,'')`), nikdy `''slovo''`;
   - **spusť vložené dotazy naostro** jako obyčejný SELECT s dosazenými hodnotami.
     Trvá to deset vteřin a je to jediný důkaz, že SQL opravdu poběží.
2. **Než sáhneš na sdílenou funkci, `@@WHO` + `@@LOCK <scope> <klic>`** — a hlavně
   **sama se ohlas přes `@@WORK`**. Nástěnka funguje jen tomu, kdo do ní píše;
   session z lane 2 se neohlásila a tím celý mechanismus obešla.
3. **Zápis nejde vzít zpět.** Po `GO` už jen zbývá zkontrolovat výsledek čtením
   a případně opravit dalším zápisem. Proto se před odesláním vyplatí ověřit
   `verze` a otisk cíle — když se od přečtení změnily, sáhla na to jiná instance.
4. **Cizí kód maž jen se čteným důvodem** a co je v něm dobré, si vezmi.
   Tady měla cizí verze navíc kontrolu `vyrobne_uzavrena` — to je správně a zůstává
   jako návrh (žádná aktivní funkce ten sloupec zatím nekontroluje, jen `pichatelna`).

## Stav po incidentu

`att_do_att_action` **v13**: jeden funkční blok, žádný `_zak_prev`, žádné zdvojené
apostrofy, kompilace OK, oba vložené dotazy ověřené naostro. Bod 4 je tím hotový —
návrat z pauzy přes notifikaci přebírá poslední píchnutou zakázku dne (`work`/`overhead`),
jen pokud je zakázka pořád `pichatelna`; jinak nechává prázdno k ručnímu doplnění.

