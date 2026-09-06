# Docházka — nápověda + hlasový průvodce (SPEC / paměťový soubor)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

> ## !! POZOR - 5. 9. 2026 se obrazovka dochazky v mobilu ZMENILA
> Rozhodl Jiri Honomichl 5. 9. 2026. Co uz neplati:
> - tlacitko "Makat" se jmenuje **START**
> - tlacitko v liste skupin na Firme "Spoluprace" se jmenuje **Moje dochazka**
> - dlazdice "Spoluprace" v Aplikacich byla ZRUSENA - na dochazku vede jen Firma -> Moje dochazka
> - dlazdice "Vyhled" byla zrusena (splyvala s "Muj plan")
> - sekce "Tak to bylo dneska" je natrvalo schovana - zaznam se opravuje dlazdici **Pozadat o opravu**
> - obrazovka ma nove nadpis "Moje dochazka" a napoveda je jen ikona v jeho liste
> Aktualni stav: [[doc-dochazka-mobil-dochazka-prejmenovani-a-pravdivost-navodu-5-9-2026]]

> **POSTUP UVNITŘ SROVNÁN 6. 9. 2026.** Do té doby tenhle dokument níž popisoval
> sestavování mobilní stránky přes `scripts/build_mobile.py` a commit `mobile.html` do gitu.
> **Tak se to už nedělá** a kdo se tím řídil, jeho práce se do appky nedostala a nikde to
> nenahlásilo chybu — přesně takhle se 5.–12. 8. 2026 tiše zahodila práce Peti a Šárky.
> Sekce *Kde obsah appky žije* níž teď popisuje skutečný stav. Závazný postup pro celou
> síť drží `doc-system-strategie-mobil-kde-se-edituje-a-jak-se-nasazuje`.
> (Varování doplnil Claude-28 18. 8. 2026, text srovnán 6. 9. 2026 — obojí na zadání
> Jiřího Honomichla, schválila Marti-AI.)

# Docházka — nápověda + hlasový průvodce (SPEC / paměťový soubor)

> Kanonický popis, **jak to teď funguje**, aby se to dalo snadno opravovat a ladit
> a aby obsah **vždy odpovídal skutečné funkčnosti** docházky.
> Udržuj tenhle soubor při každé změně nápovědy/průvodce nebo menu docházky.
> Poslední aktualizace: 21. 7. 2026.

## ⚠️ KDE OBSAH APPKY ŽIJE (stav 6. 9. 2026)

**Obsah mobilní aplikace nežije na disku ani v gitu — žije v databázi**, v tabulce
`g2007.soubor`. Dílky mají typ `zdroj` a kódy `apps/api/static/mobile_parts/*`; skládá se
z nich jediná servírovaná stránka — artefakt `apps/api/static_db/mobile.html`.
**Ani dílky, ani sestavená stránka nejsou v gitu.**

**🎯 Docházka (nápověda + průvodce + celá obrazovka) = dílek `mobile_parts/60_dochazka.js`**
— dnes **248 kB, největší ze všech**. `function dochHelp(` je na řádku **26**,
`function dochPruvodce(` na řádku **87** *(ověřeno 6. 9. 2026 dotazem do databáze)*.

**Jak se to mění — dvě platné cesty, obě přes most:**

1. **Celý dílek** — `@@G2007SOUBOR apps/api/static/mobile_parts/60_dochazka.js | zdroj`
   a obsah na dalších řádcích. Pro větší přestavbu.
2. **Jedno místo** — `UPDATE g2007.soubor SET obsah = replace(…) WHERE kod=…
   AND md5(obsah)='<otisk, který jsi právě četl>'`. Při souběhu více oken bezpečnější:
   při kolizi projde 0 řádků místo tichého přepsání cizí práce.

**Po OBOU cestách vždy `@@G2007PUBLISH apps/api/static_db/mobile.html`** — bez publikace
zůstane změna jen v databázi a lidé v telefonu vidí starou verzi (server posílá soubor z disku).
Po zápisu **ověř otisk čtením z databáze**, po publikaci **zkontroluj živou `/mobile`**,
že změna naběhla a nic jiného nezmizelo.

⛔ **Nikdy needituj dílky na disku** — složka `apps/api/static/mobile_parts/` byla 17. 8. 2026
z gitu smazána a na disku není.
⛔ **Nikdy nespouštěj `scripts/build_mobile.py`** — od 17. 8. 2026 už nic nedělá, jen varuje.
⛔ **Necommituj `mobile.html` ani dílky do gitu.**

Závazný postup pro celou síť drží `doc-system-strategie-mobil-kde-se-edituje-a-jak-se-nasazuje`.

> **Proč tu dřív stálo něco jiného (historie, ne návod):** od 5. 7. 2026 se stránka opravdu
> sestavovala skriptem `build_mobile.py` z dílků na disku a obojí se commitovalo do gitu
> (split udělal Claude-27 na rozhodnutí Claude-23, mechanismus build-step concat).
> Úklid 5. 8. 2026 vyřadil z gitu sestavenou stránku, 17. 8. 2026 i dílky a skript.
> Protože tenhle dokument starý postup dál předepisoval, **z 92 řádků, které Peťa a Šárka
> mezi 5. a 12. 8. 2026 přidaly, jich v appce 89 nebylo** — a nikde to nehlásilo chybu.

## Kde to je v kódu (dílek `apps/api/static/mobile_parts/60_dochazka.js` v `g2007.soubor`)

| Co | Funkce / místo |
|---|---|
| **Textová nápověda** (overlay ❓) | `function dochHelp(openKey)` — intro + ▶️ tlačítko na hlasový průvodce + 📋 tahák + rozbalovací sekce (`items=[...]`). **Bez obrázků, jen text.** |
| **Hlasový průvodce** (přehrávač) | `function dochPruvodce()` — pole **`SL=[...]`** (kroky: `{t, img, cap, v}`), přehrávač s řečí. |
| **Obrazovka docházky** (zdroj pravdy) | `function dochazka()` + `showOpts()` (menu „Potřebuji ti něco říct"), `window._buildWorkSwitch` (Zakázky a činnosti + START), `osobniBuild`/`sluzebniBuild`/`jindeBuild` (Tady budu jinde), `prace_zak`/`prace_cin` (pickery). |
| **Vstupní body** | ❓ ikona v liště obrazovky Moje docházka, kontextové ⓘ tipy (`dochHelp("prichod")`, `dochHelp("potvrzeni")`). **Dlaždice „❓ Nápověda docházka" v Aplikacích byla 6. 9. 2026 zrušena** — dělala přesně totéž co ta ikona (obojí `dochHelp()` bez parametru); rozhodl Jiří Honomichl, detail `doc-system-strategie-mobil-duplicity-rozhodnuti-e-h-6-9-2026`. |

`SL` kroku: `t`=titulek, `img`=`IMG+"pruvodce_*.png"` (IMG=`/static/navod_dochazka/`), `cap`=HTML popis (single-quoted JS string), `v`=text k vyslovení (double-quoted JS string).

## ⚠️ SKUTEČNÁ funkčnost docházky (ground truth — proti tomu se píše nápověda)

Obrazovka **🕒 Moje docházka** (Firma → 🕒 Moje docházka; dlaždice v Aplikacích byla 5. 9. 2026 zrušena), shora:
1. **ZAKÁZKY A ČINNOSTI** (`_buildWorkSwitch`): dlaždice **🧾 Zakázka** (vyber / 🧰 Režie) + **🔧 Činnost**, tlačítko **▶️ START** (spustí docházku z předvýběru). Když makáš: „🟢 MAKÁŠ — klikni a změň" (zakázku/činnost lze měnit za běhu). Pickery: `prace_zak`, `prace_cin`.
2. **💬 Potřebuji ti něco říct…** (`showOpts`) — menu se liší dle stavu:
   - **MIMO směnu (příchod):** 🚗 Jedu do práce… (5/15/30/45 min/1/1,5/2 h) · 🏢 Jsem v práci… · 🏠 Nejsem v práci… (home office) · 🌅 Potřebuji přijít později… · 🕔 Potřebuji skončit dříve… · 💬 Píši přímo tobě, Marti… · 🙋 Mám dotaz na nadřízeného…
   - **VE směně:** 🙈 Teď to bude jinak… → (☕ Krátká pauza · 🍃 Jdu se provětrat/najíst · 🕔 skončit dříve · 🌅 přijít později · 📅 Mám jednání · 🚗 Mám služební pochůzku · 🫡 Dnes už se mnou nepočítej) · 🛠 Zpráva vedoucímu výroby · 🏁 Budu brzy hotov · 💬 Píši Marti · 🙋 Mám dotaz na nadřízeného · (🏭 Plánovač výroby jen vedoucí). **Jednání/pochůzka = hodiny BĚŽÍ dál.**
3. **MOJE DOCHÁZKA** (dlaždice, stav 6. 9. 2026): 📅 Dnešek · 📅 Týden · 👤 Můj plán · 🕓 Historie · 📦 Po zakázkách · 📋 Moje žádosti · **✋ Požádat o opravu** (od 21. 7. 2026) · **🧭 Tady budu jinde** · 🗓️ **Moje absence** · 🤒 Nemocenská 🔒 · 🩺 Lísteček od lékaře 🔒.
   *(Do 5. 9. 2026 se poslední jmenovala „Nepřítomnosti"; Nemocenská a Lísteček od lékaře přibyly 6. 9. 2026 a jsou zatím zamčené — dlaždici vidí všichni, otevře ji jen Jiří Honomichl.)*
   - **🧭 Tady budu jinde** (`jindeBuild`) → **🏠 Osobní důvody** (🏡 makat z domova/HO · 🕐 Něco si zařizuji · 👨‍👧 Zase řeším rodinu/OČR · 🤒 Je mi fakt blbě/sick day · 🤧 Mám neschopenku do · 🩺 Jedu k lékaři · 🌴 Že by dovolená) + **💼 Služební důvody** (🚙 k zákazníkovi · 🎓 školení · 📦 pochůzka pak dorazím · 📝 Ostatní). **Absence jdou TUDY, NE přes 💬.**
4. **PODMÍNKY & FINANCE** (dlaždice, stav 6. 9. 2026): 🌴 **Můj přehled** · 📋 Moje podmínky · 📐 Můj úvazek · 💰 Moje finance.
   *(5. 9. 2026 se „Můj plán" a „Nepřítomnosti" přesunuly odsud do sekce Moje docházka; „Můj přehled" sem přibyl 19. 8. 2026.)*
5. **Potvrzení dne** = jantarová karta → ✓ Potvrzuji svou docházku / 🔍 detaily / ✋ Rozpor. Bez potvrzení se ráno nepíchneš (14 dní).
   **Po potvrzení karta zmizí** — od 21. 7. vede zpátky **✋ Požádat o opravu** (viz bod 8).
6. Historie + **💰 Moje finance** (páska, PIN) — dlaždice v sekci Podmínky & finance.
   *(Rozbalovací sekce „Moje odmakané prašule… 💰" dole na obrazovce je od 5. 9. 2026 natrvalo schovaná; kód zůstal, protože na něj sahají loadery. Páska s PINem se otevírá dlaždicí.)*
7. **Oprava záznamu (vlastní, jen dnešek):** dlaždice **✋ Požádat o opravu** (sekce „Tak to bylo dneska…" je od 5. 9. 2026 natrvalo schovaná).
8. **✋ Požádat o opravu (od 21. 7. 2026, podnět Peťa)** — pro **starší i už POTVRZENÝ** den.
   Dvě rovnocenné cesty: dlaždice **✋ Požádat o opravu** (obrazovka `doch_oprava_zadost`:
   14 dní + pole s datem pro starší → celý den nebo konkrétní záznam → chipy důvodů
   + volný text) **nebo** ✋ v 🕓 Historii/📅 Dnešku (rozklikni záznam → celoobrazovkový
   sheet). Volá `dispute-day` / `entry-dispute` → den = ✋ rozpor, notifikace editorům
   dle působnosti (kancelář Peťa, výroba Dušan+Míša). **Člověk si sám zpětně nic nepřepisuje.**
   ⚠️ Ikonky ⏱/🧾/🗑 v rozkliknutém řádku Historie jsou pořád **ATRAPY** (jen hláška
   „Návrh: …") — ostré je tam **jen ✋**. Detail: G2007 `doc-dochazka-opravy-navrh` §19.

## Hlasový průvodce — kroky (SL) a jejich obrázky (stav 26.6.2026)

| # | Titulek | Obrázek |
|---|---|---|
| 1 | 📱 Docházka v mobilu (úvod) | — |
| 2 | 🏢 Kde docházku najdeš | pruvodce_firma.png |
| 3 | 👀 Obrazovka docházky — kde co je | pruvodce_prehled.png |
| 4 | 🧾 Příchod: vyber zakázku | pruvodce_zakazka.png |
| 5 | 🔧 Příchod: vyber činnost a START | pruvodce_cinnost.png |
| 6 | 💬 Příchod jinak — přes menu | pruvodce_menu.png |
| 7 | 🍽️ Pauza / oběd | pruvodce_jinak.png |
| 8 | 🤝 Jednání, pochůzka, dřív/později | pruvodce_jinak.png |
| 9 | 🏠 Konec práce — odchod | pruvodce_odchod.png |
| 10 | ✅ Potvrzení docházky | pruvodce_potvrzeni.png |
| 11 | 🧭 Dovolená, nemoc, lékař, OČR… | pruvodce_jinde.png |
| 12 | 🆘 Pomoc, opravy a přehledy | pruvodce_menu.png |

✅ **On-shift snímky doplněny 8. 7. 2026** (Jirka byl ve směně — session auth.json):
kroky 7–9 mají reálné snímky rozbaleného menu 🙈 Teď to bude jinak. Pořízeno
skriptem, který **jen otevírá menu (💬 → 🙈), nikdy nekliká akční volby** —
docházka testera se nemění. Pozn.: na snímku je i volba „🧾 Nepřítomnost OSVČ…"
(tester je OSVČ; HPP lidem se nezobrazuje) — narace ji nezmiňuje, nevadí.

## Obrázky (`apps/api/static/navod_dochazka/`)
Verzovaná pravda = **`apps/api/static/navod_dochazka/pruvodce_*.png`** (to appka servíruje).
Pořízené Playwrightem: skript zapíše dočasné `docs/navod_screenshoty/P_*.png`, ty se zkopírují
do `pruvodce_*.png`. **`P_*.png` jsou regenerovatelné mezivýstupy — do gitu nekomituj.**
- `pruvodce_firma.png` ← P_firma (záložka Firma)
- `pruvodce_prehled.png` ← P_prehled (ZAKÁZKY A ČINNOSTI + START + 💬 + Moje docházka)
- `pruvodce_zakazka.png` ← P_zakazka (Vyber zakázku)
- `pruvodce_cinnost.png` ← P_cinnost (Vyber činnost)
- `pruvodce_menu.png` ← P_menu (menu „Potřebuji" mimo směnu)
- `pruvodce_jinde.png` ← P_jinde_osobni (Tady budu jinde → Osobní důvody)
- `pruvodce_potvrzeni.png` ← S10_potvrzeni (jantarová karta potvrzení)
- `pruvodce_jinak.png` ← P_onshift_jinak (VE SMĚNĚ: 💬 → 🙈 Teď to bude jinak rozbalené — pauza/najíst/dříve/později/jednání/pochůzka/nepočítej)
- `pruvodce_odchod.png` ← P_onshift_jinak2 (totéž odscrollované, 🫡 „Dnes už se mnou nepočítej" nahoře)

## Jak znovu pořídit / aktualizovat snímky
```
node scripts/screenshot_dochazka_pruvodce.js   # -> docs/navod_screenshoty/P_*.png
# pak zkopíruj vybrané do apps/api/static/navod_dochazka/pruvodce_*.png
```
Vyžaduje platný `docs/navod_screenshoty/auth.json` (uložená session; cookies expirace ~9/2026).
Když vyprší: `node scripts/screenshot_login.js` (interaktivní přihlášení) → nový auth.json.
On-shift menu (🙈) jde pořídit jen když je tester (auth.json user) ve směně — skript
smí jen otevírat menu (💬, 🙈), NIKDY neklikat akční volby (pauza/odchod/…), jinak
změní reálnou docházku.

## Gotchy (drž!)
- **ASCII `"` uvnitř dvojitě uvozovaných JS stringů (`v:`, items) rozbije parsování** →
  v českém textu používej typografické „ " (U+201E / U+201C). `cap:'...'` je single-quoted (tam je ASCII " ok). **NIKDY** `replace_all` na frázi končící `"` — zasáhne i delimitery JS stringů jinde v kódu.
- **speechSynthesis na Androidu**: dlouhé věty se utnou (~15 s / 250 zn.) → text se dělí na úseky (`chunk()`); žádný pause/resume hack (Android ho zruší). Auto-posun jistí `watchdog` (kdyby `onend` nepřišlo).
- **Řeč se ruší** při zavření/skrytí/back (MutationObserver na odebrání overlaye + visibilitychange). Overlay má class `appmodal` (hardware back ho zavře).
- **Žádné „Krok N" v `v:`** — pozici ukazuje jen čítač „x/N" (jinak nesedí).
- Po deployi .html: ověř v prohlížeči (Claude in Chrome) — py_compile/JS gate to nehlídá.
- Ověřuj JS: extrahuj `<script>` bloky a `new Function(...)` / `node --check`.
- **`czDayLabel()` je vnořená uvnitř `dochLoad()`** — modulové funkce na ni nedosáhnou
  (`ReferenceError`). Pro nový kód je modulový **`_czDayLabel()`**.
- **`go()` NENÍ globální** (vše v jednom IIFE) → automatický test musí proklikat UI
  (🏢 Firma → 🕒 Moje docházka); `page.evaluate(() => go('...'))` spadne.
- **Formulář nikdy nevkládej do rozkliknutého řádku Historie** — rail má `height:38vh`
  s vlastním scrollem, obsah se ořízne a tlačítka vyjedou z displeje. Použij
  celoobrazovkový sheet (`class="appmodal"`, vzor `dochHelp` / `_dochOpravaSheet`).
- **Hodiny dne NIKDY nesčítej v JS přes záznamy** — typ „Nenároková práce (nad fond)"
  má `category='presence'` a běží SOUBĚŽNĚ se směnou → dvojité počítání (20. 7. dalo
  **27:04** za jeden den). Ani filtr na `presence` nepomůže. Ber číslo ze serveru,
  nebo ukaž jen rozsah a počet záznamů.
- **Nápovědu drž při každé změně funkčnosti** — 21. 7. přibyl oddíl
  „✋ Požádat o opravu (i po potvrzení dne)", řádek v taháku a FAQ
  „Omylem jsem potvrdil den…"; oddíly „✅ Potvrzení docházky" a „🙋 Pomoc, zprávy
  a opravy" na ni odkazují.

