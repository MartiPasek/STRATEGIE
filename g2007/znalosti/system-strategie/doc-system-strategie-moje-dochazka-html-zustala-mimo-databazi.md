# Stránka moje-dochazka.html zůstala jako jediná ze své rodiny mimo databázi (a proč se to 13. 9. 2026 záměrně neopravilo)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)

> **Stav k 13. 9. 2026: ZÁMĚRNĚ NEOPRAVENO.** Jiří Honomichl rozhodl, že se místo úpravy
> stávající stránky postaví nová obrazovka „Moje docházka B" přímo v appce. Tento soubor proto
> zůstává v gitu i na disku. **Kdo to najde: není to nedodělek, je to vědomé rozhodnutí.**
> Zapsal Claude-28, formulaci si vyžádala Marti-AI (msg 15366).

## Co je špatně

Při přechodu servírovaných statických stránek do databáze (5. 8. 2026, varianta A —
viz `doc-system-strategie-staticke-artefakty-db-materializace-vyrazeni-z-gitu`) se
`apps/api/static/moje-dochazka.html` **vynechala**. Její sourozenci přešli, ona ne.

Ověřeno čtením 13. 9. 2026 (git i databáze):

| stránka | v gitu | na disku ve `static/` | v `g2007.soubor` |
|---|---|---|---|
| dochazka-zakazky.html | ne | ne | ano |
| registr-absenci.html | ne | ne | ano |
| dochazka-opravy.html | ne | ne | ano |
| mobile.html | ne | ne | ano |
| **moje-dochazka.html** | **ano** | **ano** | **ne** |

Tři důsledky:

1. **Zdroj pravdy je git, ne databáze** — což je v rozporu s pravidlem, že webový obsah mobilní
   aplikace žije v databázi. Mění se nasazením, ne publikací.
2. **Její routa jako jediná nepoužívá `_resolve_static()`** — sahá přímo do staré složky
   (`os.path.join(static_dir, "moje-dochazka.html")` v `apps/api/main.py`), takže by neviděla
   ani databázový obraz, kdyby vznikl.
3. **Chybí v `.gitignore`**, kde všichni její sourozenci jsou (řádky kolem 141–153).

## Proč na tom záleží

Právě stav „jeden soubor, dva vlastníci" (git **i** databáze) způsobil 4.–5. 8. 2026
**zablokování nasazení všem instancím na stroji** (`dirty_working_tree`) a **tiché mazání
práce v obou směrech**. Dokud je soubor jen v gitu, past nehrozí — vznikne ve chvíli,
kdy ho někdo založí i do databáze a **nedodělá zbytek**.

## Co je potřeba udělat, až na to dojde řada

Pořadí není libovolné, jinak past vznikne:

1. Založit artefakt v `g2007.soubor` s kódem `apps/api/static_db/moje-dochazka.html`
   (`typ='artefakt'`, `stav_zivota='active'`) — obsahem **živé verze**, bajt po bajtu.
2. Přepnout routu v `apps/api/main.py` na `_resolve_static("moje-dochazka.html")`.
3. Odstranit soubor z gitu a přidat ho do `.gitignore` mezi ostatní.
4. Nasadit; materializace při startu API zapíše obraz z databáze na disk.

**Nikdy neudělat krok 1 bez kroku 3** — mezi nimi je soubor v obou světech.

## Co ta stránka dělá (stav k 13. 9. 2026)

Vlastní historie docházky s rozpadem po zakázkách, otevírá se z dlaždice „Moje docházka"
v sekci DOCHÁZKA. Má nahoře nadpis, větu s popisem, **výběr člověka** (hledání + seznam)
a dvě souhrnné dlaždice (počet dní, hodin celkem).

**Výběr člověka je vědomé rozhodnutí Martiho z 8. 7. 2026** — v jádře u obou dotčených adres
stojí doslova *„Kdokoli přihlášený — každý smí vidět i kolegu."* Seznam nabízí 73 lidí a listovat
si v něm může každý přihlášený, ne jen vedoucí. 13. 9. 2026 Jiří Honomichl uvedl, že kvůli tomu
byly problémy mezi lidmi a někteří nesouhlasili, aby jim do docházky viděl někdo jiný — a chtěl
výběr odstranit. **Marti-AI k tomu řekla, že na změnu Martiho rozhodnutí je potřeba souhlas
Martiho, ne jen Jirkův.** Než se to dořešilo, Jirka změnil směr na novou obrazovku, takže
**výběr člověka zůstal beze změny a Martiho rozhodnutí nedotčené**.

Kdo se k tomu vrátí: rozhodnutí je na Martim, ne na tom, kdo zrovna sahá do kódu. A pozor —
odstranění výběru z obrazovky ruší **ovládání, ne oprávnění**; adresa v jádře kolegu vrátí dál,
když se na ni někdo zeptá přímo.

