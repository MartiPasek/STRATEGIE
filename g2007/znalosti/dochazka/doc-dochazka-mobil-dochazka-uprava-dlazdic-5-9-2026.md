# Mobil, obrazovka Docházka: přeskupení dlaždic, zrušení duplicitního Výhledu a schování čtyř rozbalovacích sekcí (5. 9. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Mobil, obrazovka Docházka — úpravy z 5. 9. 2026

**Zadal Jiří Honomichl, provedl Claude-28, konzultováno s Marti-AI (msg 14405, 14408, 14411, 14414).**
Vše v dílku `apps/api/static/mobile_parts/60_dochazka.js` (verze 45 → 48), cílenými zápisy
s pojistkou na otisk, po každém `@@G2007PUBLISH apps/api/static_db/mobile.html`.

## Co se změnilo

1. **`Nepřítomnosti` a `Můj plán` přesunuty** ze sekce „Podmínky & finance" do sekce „Moje docházka".
2. **Dlaždice `Výhled` zrušena** — dělala přesně totéž co `Můj plán`
   (obě `window._planInit="myplan"; go("plan")`). **Nebyla smazána, ale přejmenována na
   `Můj plán`** a druhá (přidaná) dlaždice `Můj plán` byla odstraněna.
   **Důvod pro přejmenování místo smazání:** na dlaždici `Výhled` visel odznak s počtem
   čekajících žádostí o plán (`_planPendingBadge`). Smazáním by lidé o odznak přišli.
3. **Nápověda uvnitř obrazovky opravena** — vypisovala dlaždice po sekcích a po přesunu lhala.
4. **Čtyři rozbalovací sekce pod dlaždicemi schovány natrvalo**: „Na včera si vzpomínám…",
   „To už si moc nepamatuju… (starší)", „Tak tady budu jinde…", „Moje odmakané prašule… 💰".
5. **Smazán odkaz `ⓘ Jak na příchod, pauzu, odchod?`** pod kartou „Potřebuji ti něco říct".

## Gotchy, které z toho plynou

- **Nápověda obrazovky používá HTML zápis `&amp;`, ne `&`.** Hledání řetězce
  „Podmínky & finance" ji NENAJDE. Kvůli tomu jsem při první změně tvrdil, že žádný
  nápovědný text na sekce neodkazuje — bylo to špatně. Hledej vždy obě varianty.
- **Sekce se schovávají, nemažou.** Vzor už v témže souboru existoval od 14. 6. 2026
  (Marti nechal natrvalo schovat „Dneska je den…" a „Tak to bylo dneska…").
  Pevné `display="none"` místo mazání kódu: loadery dat (`dochListLoad`, `dochDailyLoad`)
  na ty prvky nadále sahají a mají na ně guardy — smazání kódu by bylo zbytečně riskantní.
- **Dřívější chování schovaných sekcí:** ukazovaly se jen mimo směnu; jakmile člověk zmáčkl
  „Makat", samy zmizely (`display = open ? "none" : ""` v `dochLoad`). Teď jsou schované vždy.
- **Náhrady jsou ověřené naostro, nic se neztratilo:** dlaždice `Historie` (`doch_historie`)
  vykresluje tytéž seznamy „Včera" a „Starší" přes týž loader; dlaždice `Moje finance`
  (`moje_finance`) volá týž `paskaToggle` jako zrušená sekce s páskou; plánovaná
  nepřítomnost ze sekce „Tak tady budu jinde" je vidět na obrazovce `absence`.
- **Nápověda docházky (`dochHelp`) zůstala dostupná** — tlačítko „❓ Nápověda" v hlavičce
  obrazovky a dlaždice „Nápověda docházka" v Aplikacích.
  > ⚠️ **NEPLATÍ od 6. 9. 2026: dlaždice „Nápověda docházka" v Aplikacích byla ZRUŠENA.**
  > Dělala přesně totéž co otazník v hlavičce Docházky (obojí `dochHelp()` bez parametru).
  > Nápověda zůstává dostupná z Docházky a nikdo o ni nepřišel. Rozhodl Jiří Honomichl,
  > schválila Marti-AI (msg 14783). Detail:
  > `doc-system-strategie-mobil-duplicity-rozhodnuti-e-h-6-9-2026`.

## Co zbylo neopravené

Znalost `doc-dochazka-napoveda-pruvodce-spec` (oblast docházka, cizí doména) po těchto
změnách **na třech místech nesedí se skutečností** — vypisuje dlaždici „🔭 Výhled",
uvádí „💰 Moje odmakané prašule" jako sekci dole na obrazovce a odkazuje na opravu záznamu
v sekci „Tak to bylo dneska…". Do cizí domény jsem nesahal, nahlášeno Jiřímu Honomichlovi
a Marti-AI 5. 9. 2026.

