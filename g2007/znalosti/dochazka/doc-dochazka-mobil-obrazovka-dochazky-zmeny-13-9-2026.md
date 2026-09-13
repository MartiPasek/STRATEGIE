# Mobil, obrazovka docházky: potvrzení dne nahoru, přejmenování dlaždice a sekce, nová obrazovka „Moje docházka B" (13. 9. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)

Zadal Jiří Honomichl 13. 9. 2026, schválila Marti-AI (msg 15327, 15336, 15357). Provedl Claude-28.
Vydání mobilní aplikace **v190 až v193**.

## 1. Jantarová karta „potvrď si předchozí den" je nahoře

**Dřív:** karta byla až úplně dole, za dlaždicemi i za sekcí Správa docházky. Člověk přišel
z upozornění na domovské obrazovce a musel k ní přerolovat přes celou obrazovku.

**Nově:** je hned pod pulzujícím rámečkem s tlačítky „Potřebuji ti něco říct…" a „Tady budu
jinde…", tedy nad dlaždicemi.

**Jak:** karty se vkládají do prázdného divu `dochConfirm` podle jeho `id`. Stačilo proto
přesunout **samotný prázdný div** v `60_dochazka.js` z konce obrazovky za `dochNow`
(pulzující rámeček). Do karty ani do tlačítka se nesahalo — logika se nezměnila.

> **Vzor k zapamatování:** pořadí bloků na obrazovce se řídí pořadím, v jakém se připojují
> do `p` (panel). Kdo chce něco přesunout, hledá ten `appendChild`, ne samotný obsah.
> Pořadí v kódu ale **nemusí odpovídat tomu, co je vidět** — ověřuj výpisem pořadí dětí
> panelu na živé stránce, ne čtením zdroje.

## 2. Přejmenování

| bylo | je |
|---|---|
| dlaždice „📦 Po zakázkách" | dlaždice „📦 Moje docházka" |
| nadpis sekce „MOJE DOCHÁZKA" | nadpis sekce „DOCHÁZKA" |

**Přejmenovat jen ta dvě místa nestačí.** Dohledáním se našlo dalších 18 výskytů:

- **3 věty v nápovědě a v mluveném průvodci**, které dlaždici vyjmenovávají jménem,
- **14 vět**, které odkazují na „sekci Moje docházka" (typu „v sekci Moje docházka ťukni
  dlaždici Požádat o opravu"),
- **titulek obrazovky, která se po klepnutí otevře** — je v mapě cest v `30_contacts_settings.js`.
  Bez něj by člověk klepl na „Moje docházka" a otevřela by se mu obrazovka „Po zakázkách".

> ⚠️ **Na pořadí záměn záleží.** Nejdřív „Moje docházka" → „Docházka" (sekce), **teprve pak**
> „Po zakázkách" → „Moje docházka" (dlaždice). Obráceně by druhá záměna přepsala výsledek první.

> ✅ **Mluvený průvodce nemá nahraný zvuk** — text čte až telefon při přehrání
> (`speechSynthesis`). Přepis textu tedy stačí, hlas nebude říkat starý název.

## 3. Nová obrazovka „Moje docházka B"

Dlaždice „📋 Moje docházka B" hned za „Moje docházka", klepnutí otevře obrazovku
`moje_dochazka_b` s nadpisem „Moje docházka B“.

> **Obrazovka je ZÁMĚRNĚ prázdná** — je na ní jen věta „Tato sekce se připravuje. Obsah
> doplníme." Jiří Honomichl zadal 13. 9. 2026, že obsah řekne později. **Není to nedodělek.**

Registrace obrazovky má **čtyři místa** a jedno se běžně zapomíná — závazný postup drží
`doc-system-strategie-mobil-nova-obrazovka-ctyri-mista-registrace`.

## Co se NEDĚLALO a proč

Původní zadání znělo zjednodušit **stávající** obrazovku otevíranou z dlaždice
(zrušit nadpis, popisnou větu, výběr člověka a dvě souhrnné dlaždice) a převést ji do databáze.
**Od toho se 13. 9. 2026 upustilo** — Jiří Honomichl změnil směr na novou obrazovku v appce.
Stará stránka zůstala beze změny včetně výběru člověka; detail a otevřené body drží
`doc-system-strategie-moje-dochazka-html-zustala-mimo-databazi`.

