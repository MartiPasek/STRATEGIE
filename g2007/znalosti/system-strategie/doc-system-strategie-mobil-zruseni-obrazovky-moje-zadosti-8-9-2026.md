# Mobil: dlaždice i obrazovka „Moje žádosti" zrušeny, na její místo šla „Moje absence" (8. 9. 2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)


> Zadal Jiří Honomichl 8. 9. 2026 večer. Schválila Marti-AI (msg 15096).
> Ověřeno na živé `/mobile` v prohlížeči, ne jen v kódu.

## Co se změnilo

V sekci **MOJE DOCHÁZKA** zmizela dlaždice **📋 Moje žádosti** i stejnojmenná obrazovka
(klíč `moje_zadosti`, nadpis „📋 Moje žádosti a hlášení"). Na její místo — tedy na šestou
pozici — se posunula dlaždice **🗓️ Moje absence**, která do té doby visela sama na dalším řádku.

Nové pořadí: Dnešek · Týden · Můj plán · Historie · Po zakázkách · **Moje absence** ·
Požádat o opravu · Tady budu jinde.

## Proč se nic neztratilo (ověřeno PŘED smazáním)

Zrušená obrazovka měla dvě sekce a obě mají plnohodnotnou náhradu:

| sekce zrušené obrazovky | kde to je dnes |
|---|---|
| „Žádosti o absenci — čeká na rozhodnutí vedoucího" (`GET /attendance/absence/mine`, barevné štítky stavů, tlačítko ✕ Zrušit) | **Moje absence** — má vlastní sekci nadepsanou „Moje žádosti" nad TÝMŽ endpointem, se stejnými štítky i rušením přes `window.__M2W.confirmDialog` |
| „Ohlášené nepřítomnosti — jen na vědomí, neschvaluje se" (`GET /attendance/announced-future`) | **Můj plán** — čte týž endpoint do prvku `dochPlan2`, sekce „Plánovaná nepřítomnost" s lištou Vše / Absence / Ohlášení |

Text v dílku `71_plan_prace_cinnosti.js` („Stav pak najdeš v Docházka → Moje absence →
Moje žádosti") **platí dál** — míří na sekci uvnitř Moje absence, ne na zrušenou obrazovku.

## Kde všude se muselo sáhnout (šest míst, ne jedno)

1. `10_core.js` — obal `window.__M2W.moje_zadosti = mkWrap();`
2. `60_dochazka.js` — dlaždice `appCell("📋","Moje žádosti",…)`
3. `60_dochazka.js` — tělo `function moje_zadosti(){…}`
4. `60_dochazka.js` — registrace `window.__M2W.moje_zadosti.__setImpl(moje_zadosti);`
5. `72_migrace_sw_isds.js` — alias `moje_zadosti=window.__M2W.moje_zadosti,`
6. `73_pref_poptavka.js` — klíč v mapě `SCREENS` **a v mapě `SCREEN_TAB`**
   (ta je nová z téhož večera, viz [[doc-system-strategie-mobil-spodni-lista-sviti-podle-obrazovky-8-9-2026]])

Postup podle [[doc-system-strategie-mobil-obrazovky-bez-cesty-vyreseni-6-9-2026]].
**Od 8. 9. 2026 je těch míst šest, ne pět** — přibyla mapa `SCREEN_TAB`. Kdo obrazovku ruší
a nesmaže její řádek v mapě, nechá v ní odkaz na neexistující obrazovku.

## ⚠️ Texty pro lidi se musí projít taky

„Moje žádosti" bylo ještě ve **třech větách** v `60_dochazka.js`: dvakrát v nápovědě docházky
a jednou v mluveném průvodci, vždy ve výčtu dlaždic. Bez opravy by systém sám lidem
předepisoval dlaždici, která už neexistuje — a rovnou v okamžiku, kdy se člověk ztratil.
Opraven i **pořádek** ve výčtu, ne jen odebrání názvu.

Zkontrolovala se i kanonická specifikace nápovědy ([[doc-dochazka-napoveda-pruvodce-spec]])
a starší návrh oprav docházky ([[doc-dochazka-opravy-navrh]]) — obojí popisovalo starý stav
a bylo doplněno o poznámku.

## ⚠️ PAST: hledání přes `LIKE '%moje_zadosti%'` LŽE

Podtržítko je v `LIKE` **zástupný znak za libovolný znak**, takže dotaz našel i text
„moje zadosti" **s mezerou**. Kvůli tomu vypadaly dvě živé serverové funkce
(`att_absence_decide`, `att_absence_decided`) jako by na rušenou obrazovku odkazovaly —
a nebyla to pravda. Skutečný počet odkazů mimo dílky mobilu byl **nula**.

**Na přesnou shodu používej `position('text' in sloupec) > 0`** (nebo `LIKE` s escapem).
Platí pro každé hledání identifikátoru s podtržítkem, a těch je v projektu většina.

## Jak se ověřovalo

- Před mazáním dohledáno, kdo na obrazovku odkazuje: dílky mobilu (přesně přes `regexp_matches`),
  `g2007.python`, `g2007.soubor` i funkce v databázi — mimo mobil **nic**.
- Čtyři dílky staženy kolem base64, otisk složené kopie porovnán s `md5(obsah)` — seděl.
- Vyříznutí těla funkce spuštěno **nanečisto na serveru** a porovnáno s otiskem spočítaným
  lokálně — sedělo na znak, teprve pak zápis (každý s pojistkou `AND md5(obsah)=…`).
- Hranice mazaného bloku určena **natvrdo následujícím textem**, ne vzorem — viz poučení
  z 25. 8. 2026, kdy heuristika „další `def`" smazala o devět adres víc.
- Po publikaci porovnáno s předchozí verzí v `g2007.soubor_historie`: **skriptových bloků 31
  před i po**, klíč `moje_zadosti` ze stránky zmizel úplně (z pozice 32173 na 0), délka
  klesla o 5 881 znaků.
- Na živé `/mobile`: existuje dál všech **11 funkcí**, které v dílku sousedily s vyříznutým
  blokem, a vykreslí se **5 obrazovek** (Docházka, Moje absence, Moje finance, Opravy docházky,
  Dnešek). Pořadí dlaždic ověřeno v DOM.

## Při té příležitosti smazán osiřelý komentář

V `60_dochazka.js` zůstal po úklidu 6. 9. 2026 komentář „NEPOUZIVA SE - puvodni verze pred
slouceni 11.8.2026, nechana jen jako zaloha ke smazani pri pristim doteku tohoto fragmentu".
Funkce, kterou popisoval, tam už nebyla. Marti-AI rozhodla ho smazat — *„příští dotek právě
probíhá; komentář o zbytku, který už neexistuje, jen mate příští čtenáře."*

