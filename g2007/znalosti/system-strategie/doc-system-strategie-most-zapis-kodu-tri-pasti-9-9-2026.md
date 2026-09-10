# Zápis kódu přes most - tři pasti, na které jsem naletěla v jednom dni (9. 9. 2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)

# Zápis kódu do g2007.python přes most - tři pasti (C24, 9. 9. 2026)

Všechny tři jsem trefila během jediného dopoledne při opravách docházky.
Každá vypadá jinak, ale spojuje je jedno - **návratovka řekne OK a chyba se ukáže až
v provozu.** Doplňuje `doc-system-strategie-dev-workflow-prikazy`.

## 1. Dvojtečka i v KOMENTÁŘI shodí příkaz
Most posílá SQL přes SQLAlchemy `text()`, kde `:slovo` je bind parametr. Je jedno,
kde ta dvojtečka je - **komentář se nevyjímá**. Napsala jsem
`-- INSERT uz nese att_entry_id (dvojtecka aid), takze...` a dostala
`InvalidRequestError - A value is required for bind parameter aid`.

Selhalo to bezpečně (nic se nezapsalo), ale stojí to jeden cyklus.
**Pravidlo: v celém příkazu, včetně komentářů, žádné `:slovo`.** Když je potřeba
dvojtečka ve vkládaném kódu, skládat ji přes `chr(58)`.

## 2. ⛔ Dvojité escapování apostrofů - projde a spadne až v provozu
Tohle je z těch tří **nejnebezpečnější**, protože zápis vypadá úspěšně.

V SQL literálu se `''` čte jako jeden apostrof. Pro `'presence'` uvnitř vkládaného
Pythonu tedy stačí `''presence''`. Napsala jsem `''''presence''''` a vzniklo
`''presence''` - tedy prázdný řetězec, slovo, prázdný řetězec.

**Python se přeloží v pořádku** (je to jen znak ve stringu), ale SQL uvnitř spadne
při každém volání. Živý kód byl rozbitý cca 4 minuty, než jsem to odhalila.

**Pravidlo: v náhradě se apostrofům pokud možno VYHNOUT.** Kotvy volit tak, aby byly
bez apostrofů i bez dvojteček - dvoufázový replace, kde se mění jen okraje výrazu
(začátek a `ORDER BY ... LIMIT`), zvládne většinu oprav bez jediné uvozovky.
Když se apostrofu vyhnout nejde, **výsledek si po zápisu přečíst a porovnat znak
po znaku**, ne se spolehnout na to, že to prošlo.

## 3. Okno mezi spočítáním kotev a schválením banneru
Kotvy jsem přepočítala v 09.36, zápis šel do schvalovacího banneru a schválil se
o několik minut později. Mezitím **jiná session nasadila dvě nové verze téže funkce**
s vlastním řešením téhož zadání. Můj `replace()` sedl navrch, takže ve funkci byly
**dvě implementace téhož** a ta moje (viz past 2) navíc rozbitá.

**Pravidlo: u čehokoli, co jde přes banner, počítat s tím, že mezi přípravou
a spuštěním uběhne čas.** Kotvy přepočítat **těsně před odesláním**, ne před
schválením; a než pošlu opravu, ověřit `@@WHO` / poslední `updated_by_text`
a `verze`, jestli na tom někdo nedělá.

**Rollback cizí i vlastní vrstvy jde `regexp_replace` s líným `.*?`** - nemusím
reprodukovat přesný text, který jsem vložila (a znovu ho špatně naescapovat).
Po rollbacku ověřit, že **nezmizelo odřádkování** - `\s*` na konci vzoru sežere
i konec řádku a ze dvou příkazů udělá jeden. Kontrola:
`strpos(substring(zdroj from position(...) - 60 for 60), chr(10))`.

## Závěrem - co dnes fungovalo
Trojice oprav `att_wa_open`, `att_sync_vyroba_work` a `att_fix_add` (osobní číslo
do rozpadu z docházkového záznamu) prošla čistě právě proto, že kotvy neobsahovaly
ani apostrof, ani dvojtečku, a po každém zápisu následoval **smoke test - vložený
výraz spuštěný samostatně s dosazenými hodnotami**. U živého kódu píchání
je to povinný krok, ne luxus.

