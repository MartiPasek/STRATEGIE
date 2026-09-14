# Dlazdice obrazovky Aplikace ziji od 14. 9. 2026 v datech (public.mobile_app_dlazdice) - hledani v kodu je slepe

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)

# Dlaždice obrazovky Aplikace žijí od 14. 9. 2026 v datech — hledání v kódu je slepé

**Zapsal Claude-28 (okno strategie-c3) 14. 9. 2026** po vlastním falešném poplachu.
Samotnou přestavbu (tři záložky + přesun seznamu dlaždic do databáze) dělalo jiné okno
na zadání Jiřího Honomichla, schválila Marti-AI (msg 15486, 15495, 15514).

## Co se změnilo

Seznam dlaždic obrazovky **Aplikace** už **není v kódu**. Žije v tabulce
**`public.mobile_app_dlazdice`** — jeden řádek = jedna dlaždice:

| sloupec | k čemu je |
|---|---|
| `kod` | ustálený klíč dlaždice (odvozený z názvu bez diakritiky) — drží oblíbené při přejmenování |
| `nazev`, `ikona`, `sekce`, `poradi` | co člověk vidí |
| `akce_typ` + `akce_cil` | co se stane po klepnutí: `openInApp` (uvnitř appky), `openApp` (ven), `go` (obrazovka), `openVyroba`, nebo **`zadna`** = schválně nic |
| `zalozka` | `vsechny` (vidí každý) nebo `vyvoj` (jen rodič a správce) |
| `aktivni` | zapnutá/vypnutá |

Stav k 14. 9. 2026: na záložce **„Všechny aplikace" dvě dlaždice** — 🎁 Benefity
(`openInApp` → `/benefity`) a 💡 Světla (`akce_typ='zadna'`, cíl schválně žádný,
rozhodl Jirka 7. 9. 2026); na „Vývoj aplikací" **67 dlaždic**, ty se pořád kreslí z kódu.

## Past, na kterou jsem naletěl (ať na ni nenaletí nikdo další)

Hledal jsem dlaždici jako **pevný text ve zdroji** (`appCell("🎁","Benefity"` v `g2007.soubor`
i ve složené `/mobile`). Nenašel jsem ji — a **z její nepřítomnosti jsem udělal závěr**,
že z appky zmizela. Nezmizela: kreslí se z dat, takže v kódu být nemá.

**Jak se to ověřuje správně** (v tomhle pořadí):

1. **v datech** — `SELECT zalozka, count(*) FROM public.mobile_app_dlazdice WHERE aktivni GROUP BY 1;`
   a u konkrétní dlaždice `kod, akce_typ, akce_cil, zalozka`;
2. **v appce v prohlížeči** — otevřít obrazovku a podívat se; hledání v souboru je jen vodítko.

⚠️ **Prohlížeč po publikaci drží starou stránku.** Kdo ověřuje appku hned po nasazení,
musí ji načíst s **`?fresh=<cokoli>`** za adresou, jinak měří starý kód. *(Narazilo na to
i okno, které přestavbu dělalo.)*

## Druhé poučení: rozlišuj „chybí v kódu" od „appka je rozbitá"

Poplach jsem poslal ve chvíli, kdy živá appka ještě rozbitá **nebyla** — a naopak
zhruba tři a půl minuty (01:31:28–01:35:02) rozbitá **byla**, ale z úplně jiného důvodu
(v kódu se dvě proměnné po naplnění znovu vyrobily jako prázdné, vykreslování spadlo;
doloženo porovnáním verzí 33 a 34 dílku `35_apps_vedeni.js` v `g2007.soubor_historie`).

Z toho plyne: **doba, po kterou to lidé mohli vidět, se nečte z času zápisu do databáze,
ale z času složení appky** (`g2007.soubor_historie` pro `apps/api/static_db/mobile.html`,
sloupce `platne_od` / `nahrazeno_at`). Mezi zápisem dílku a publikací bývá i deset minut.

