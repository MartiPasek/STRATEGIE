# Docházka — nápověda + hlasový průvodce (SPEC / paměťový soubor)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Docházka — nápověda + hlasový průvodce (SPEC / paměťový soubor)

> Kanonický popis, **jak to teď funguje**, aby se to dalo snadno opravovat a ladit
> a aby obsah **vždy odpovídal skutečné funkčnosti** docházky.
> Udržuj tenhle soubor při každé změně nápovědy/průvodce nebo menu docházky.
> Poslední aktualizace: 8. 7. 2026.

## ⚠️⚠️ BUILD: `mobile.html` je od 5. 7. 2026 GENEROVANÝ — needituj ho přímo!

`apps/api/static/mobile.html` (jeden velký servírovaný soubor, ~9 000 řádků) je
od 5. 7. 2026 **generovaný** scriptem `scripts/build_mobile.py` slepením partialů
z **`apps/api/static/mobile_parts/`** (`NN_nazev.js|html|css`, řadí se čísly).
Split udělal **Claude-27 (Zuzka)** na rozhodnutí **Claude-23 (Marti)** —
„mechanismus A: build-step concat, ne deploy-time". Hlavička v `mobile.html` to hlásí.

**🎯 Docházka (nápověda + průvodce + celá obrazovka) = partial `mobile_parts/60_dochazka.js`**
(`dochHelp` ~ř. 1, `dochPruvodce` ~ř. 60; `35_apps_vedeni.js` na to jen volá dlaždicí).
To je 147 kB partial — největší ze všech.

**Workflow, když děláme s docházkou:**
```
1. edituj mobile_parts/60_dochazka.js   (NE mobile.html!)
2. python scripts/build_mobile.py       (přegeneruje mobile.html)
3. commit OBOJE: 60_dochazka.js + mobile.html
```

**🚨 KRITICKÁ PAST — partialy bývají ZASTARALÉ (reality ≠ workflow):** Claude-23/Marti
i po splitu **občas editují `mobile.html` napřímo** a nepropíšou to zpět do partialů
(ověřeno 8.7.: committnutý `mobile.html` měl 2 přímé úpravy — dlaždice „📦 Po zakázkách"
+ „HR modul" rename — které v partialech NEBYLY). **Kdybys editoval partial a rebuildoval,
tyhle přímé úpravy SMAŽEŠ.** Proto PŘED každou prací s partialem:
```
python scripts/build_mobile.py; git diff --stat apps/api/static/mobile.html
# prázdný diff = parts jsou v souladu, můžeš editovat partial.
# NEprázdný diff = někdo editoval mobile.html napřímo → NEJDŘÍV ty přímé
#   úpravy přenes do správného partialu (a teprve pak edituj/rebuild),
#   jinak je rebuildem přepíšeš. Pak: git checkout -- mobile.html a začni.
```
(Dřív bylo možné mobile.html editovat přímo — proto memory + tento SPEC. Doctrine (e)
„srovnej lokál s realitou" platí i tady: čerstvý `git fetch/pull` před buildem.)

## Kde to je v kódu (partial `apps/api/static/mobile_parts/60_dochazka.js` → build → `mobile.html`)

| Co | Funkce / místo |
|---|---|
| **Textová nápověda** (overlay ❓) | `function dochHelp(openKey)` — intro + ▶️ tlačítko na hlasový průvodce + 📋 tahák + rozbalovací sekce (`items=[...]`). **Bez obrázků, jen text.** |
| **Hlasový průvodce** (přehrávač) | `function dochPruvodce()` — pole **`SL=[...]`** (kroky: `{t, img, cap, v}`), přehrávač s řečí. |
| **Obrazovka docházky** (zdroj pravdy) | `function dochazka()` + `showOpts()` (menu „Potřebuji ti něco říct"), `window._buildWorkSwitch` (Zakázky a činnosti + Makat), `osobniBuild`/`sluzebniBuild`/`jindeBuild` (Tady budu jinde), `prace_zak`/`prace_cin` (pickery). |
| **Vstupní body** | Dlaždice „❓ Nápověda docházka" v Aplikacích (`apps()`), ❓ tlačítko v hlavičce Spolupráce, kontextové ⓘ tipy (`dochHelp("prichod")`, `dochHelp("potvrzeni")`). |

`SL` kroku: `t`=titulek, `img`=`IMG+"pruvodce_*.png"` (IMG=`/static/navod_dochazka/`), `cap`=HTML popis (single-quoted JS string), `v`=text k vyslovení (double-quoted JS string).

## ⚠️ SKUTEČNÁ funkčnost docházky (ground truth — proti tomu se píše nápověda)

Obrazovka **🤝 Spolupráce** (Firma → Spolupráce, nebo dlaždice v Aplikacích), shora:
1. **ZAKÁZKY A ČINNOSTI** (`_buildWorkSwitch`): dlaždice **🧾 Zakázka** (vyber / 🧰 Režie) + **🔧 Činnost**, tlačítko **▶️ Makat** (spustí docházku z předvýběru). Když makáš: „🟢 MAKÁŠ — klikni a změň" (zakázku/činnost lze měnit za běhu). Pickery: `prace_zak`, `prace_cin`.
2. **💬 Potřebuji ti něco říct…** (`showOpts`) — menu se liší dle stavu:
   - **MIMO směnu (příchod):** 🚗 Jedu do práce… (5/15/30/45 min/1/1,5/2 h) · 🏢 Jsem v práci… · 🏠 Nejsem v práci… (home office) · 🌅 Potřebuji přijít později… · 🕔 Potřebuji skončit dříve… · 💬 Píši přímo tobě, Marti… · 🙋 Mám dotaz na nadřízeného…
   - **VE směně:** 🙈 Teď to bude jinak… → (☕ Krátká pauza · 🍃 Jdu se provětrat/najíst · 🕔 skončit dříve · 🌅 přijít později · 📅 Mám jednání · 🚗 Mám služební pochůzku · 🫡 Dnes už se mnou nepočítej) · 🛠 Zpráva vedoucímu výroby · 🏁 Budu brzy hotov · 💬 Píši Marti · 🙋 Mám dotaz na nadřízeného · (🏭 Plánovač výroby jen vedoucí). **Jednání/pochůzka = hodiny BĚŽÍ dál.**
3. **MOJE DOCHÁZKA** (dlaždice): 📅 Dnešek · 📅 Týden · 🔭 Výhled · 🕓 Historie · 📋 Moje žádosti · **🧭 Tady budu jinde**.
   - **🧭 Tady budu jinde** (`jindeBuild`) → **🏠 Osobní důvody** (🏡 makat z domova/HO · 🕐 Něco si zařizuji · 👨‍👧 Zase řeším rodinu/OČR · 🤒 Je mi fakt blbě/sick day · 🤧 Mám neschopenku do · 🩺 Jedu k lékaři · 🌴 Že by dovolená) + **💼 Služební důvody** (🚙 k zákazníkovi · 🎓 školení · 📦 pochůzka pak dorazím · 📝 Ostatní). **Absence jdou TUDY, NE přes 💬.**
4. **PODMÍNKY & FINANCE** (dlaždice): 📋 Moje podmínky · 📐 Můj úvazek · 👤 Můj plán · 💰 Moje finance · 🗓️ Nepřítomnosti.
5. **Potvrzení dne** = jantarová karta → ✓ Potvrzuji svou docházku / 🔍 detaily / ✋ Rozpor. Bez potvrzení se ráno nepíchneš (14 dní).
6. Historie + **💰 Moje odmakané prašule** (páska, PIN).
7. **Oprava záznamu:** v sekci „Tak to bylo dneska…" ťukni na záznam → ⏱ Zkrátit konec / 🧾 Změnit zakázku.

## Hlasový průvodce — kroky (SL) a jejich obrázky (stav 26.6.2026)

| # | Titulek | Obrázek |
|---|---|---|
| 1 | 📱 Docházka v mobilu (úvod) | — |
| 2 | 🏢 Kde docházku najdeš | pruvodce_firma.png |
| 3 | 👀 Obrazovka docházky — kde co je | pruvodce_prehled.png |
| 4 | 🧾 Příchod: vyber zakázku | pruvodce_zakazka.png |
| 5 | 🔧 Příchod: vyber činnost a Makat | pruvodce_cinnost.png |
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
- `pruvodce_prehled.png` ← P_prehled (ZAKÁZKY A ČINNOSTI + Makat + 💬 + Moje docházka)
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


