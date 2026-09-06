# Mobil: obrazovky bez cesty — jak dosažitelnost měřit (mapa SCREENS), past se čtyřmi registračními místy a co se 6. 9. 2026 zpřístupnilo a zrušilo

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Obrazovky bez cesty v mobilu — jak je poznat a co se s nimi udělalo (6. 9. 2026)

Zadal Jiří Honomichl, navazuje na `doc-system-strategie-mobil-duplicitni-cesty-audit-5-9-2026`
(oddíl F). Provedl Claude-28.

## ⚠️ Dosažitelnost NEHLEDEJ podle názvu funkce — appka přepíná podle mapy `SCREENS`

Tohle je hlavní poučení. Napřed jsem dosažitelnost počítal průchodem přes `go("…")` a názvy
funkcí a **dvakrát mi vyšel špatný výsledek** — jednou moc velký (28 „mrtvých", mezi nimi
běžně používaná Nemocenská nebo Vyber zakázku), jednou zavádějící.

Spolehlivé je až tohle:

1. Vytáhni mapu `var SCREENS={klic:funkce,…}` (dnes v `73_pref_poptavka.js`) — **appka
   naviguje podle KLÍČE, ne podle názvu funkce.** Klíč se od názvu funkce může lišit
   (např. klíč `vpfinzak` → funkce `vpFinZak`).
2. Pro každý klíč hledej `go("<klic>")`, `selectTab("<klic>")` a `screen:"<klic>"`.
3. **Projdi to do hloubky** — obrazovka, na kterou vede odkaz jen z jiné nedosažitelné
   obrazovky, je taky nedosažitelná.
4. Obrazovka **nezaregistrovaná v `SCREENS`** není nutně mrtvá — bývá otevíraná přímým
   voláním funkce z rodičovské obrazovky (formuláře typu `sickForm`, `ocrForm`).

**Past, do které jsem spadl:** cíl předaný proměnnou (`go(kam)`) je při takové kontrole
neviditelný a obrazovka vypadá mrtvá. Proto **piš cíle natvrdo** (`if(x) go("sick"); else go("med");`),
i když je to delší — jinak ti ji příští úklid smaže.

## Smazání obrazovky = ČTYŘI místa, ne jedno

Fragmenty appky nejsou jedna společná closure; každý je vlastní IIFE a funkce se sdílejí
přes `window.__M2W`. Jedna obrazovka je proto zapsaná na čtyřech až pěti místech
a **když smažeš jen tělo, appka spadne tiše až v prohlížeči** (`node --check` při publikaci projde):

| co | kde (stav 6. 9. 2026) |
|---|---|
| obal `window.__M2W.X = mkWrap();` | `10_core.js` |
| tělo `function X(){…}` | fragment, kde obrazovka bydlí |
| registrace `window.__M2W.X.__setImpl(X);` | konec téhož fragmentu |
| alias `X=window.__M2W.X,` | `72_migrace_sw_isds.js` |
| klíč v přepínači `X:X,` | `73_pref_poptavka.js` |

Obal, registrace, alias i klíč jsou **natěsnané na jednom řádku vedle sousedů**, takže se
maže přesný úsek, ne celý řádek. Ověř si, že každá kotva je v dílku právě jednou.

## Co se 6. 9. 2026 rozhodlo a udělalo

**Přidáno** (obrazovky, které existovaly, ale nikdo se k nim nedostal):

- Docházka → **🤒 Nemocenská** a **🩺 Lísteček od lékaře**. Jsou **ZAMČENÉ**: dlaždici vidí
  všichni, otevře ji zatím jen Jiří Honomichl (user 20), ostatním se ukáže „připravuje se".
  Důvod: obě funkce si chce nejdřív projít a teprve pak je odemknout všem.
  V kódu je u toho `TODO` — číslo uživatele je natvrdo a patří nahradit oprávněním.
- HR — personalistika → **🎂 Narozeniny a výročí**, **🆕 Noví zaměstnanci**,
  **🩺 Lékař — přehled**, **🏢 Firemní výjimky**.

**Proč Nemocenská a Lísteček nejsou totéž co dnešní hlášení nepřítomnosti:** přes
Docházka → 🧭 Tady budu jinde → 🏠 Osobní důvody se pošle **jen informace vedoucímu**.
Tyhle dvě obrazovky umí navíc číslo rozhodnutí o DPN (eNeschopenka), vyfotit lísteček
a čerpat sick day do limitu.

**Zrušeno** (mrtvý kód, ve všech pěti místech):

- `hr` „🔒 HR — personalistika" — starší rozcestník; jeho náhrada `hr_hub` se stejným
  názvem je dostupná z Aplikací i z Vedení firmy.
- `hr_interni` „🏢 Interní personalistika" — slepá kopie `hr_hub`; jediné unikátní
  (Lékař — přehled) se přeneslo.
- `prace` „🧾 Na čem dělám" — dvojče sekce „ZAKÁZKY A ČINNOSTI" v Docházce.
- `doch_zitrek` „🌅 Tady budu jinde" — starší dvojče; stejnojmenná dlaždice v Docházce
  otevírá vysouvací nabídku, ne tuhle obrazovku.
- `_moje_zadosti_pred_slouceni_11_8_2026` — zbytek po sloučení z 11. 8. 2026.

⚠️ **`prace_zak` a `prace_cin` se NESMAZALY a mazat se nesmí** — volá je živá sekce
„ZAKÁZKY A ČINNOSTI", tedy to, čím lidé píchají zakázku a činnost. Nejdřív jsem je omylem
označil za mrtvé spolu s `prace`; mrtvý byl jen rozcestník nad nimi.

**Vědomě NEzpřístupněno:**

- `mytodo` „📝 Moje TODO", `phone` „Telefon", `webview` „🌐 Web ekosystému" — Jiří Honomichl
  je zatím nechtěl; leží dál bez cesty.
- „🏠 Mimo kancelář" a „🧲 Výběrová řízení" ze zrušené HR obrazovky se **nepřenesly schválně** —
  vedou na `kdekdo` a `hr_nabor`, které v dostupném HR už jsou pod jmény „Kdo kde dnes"
  a „Nábor". Přenést je by znamenalo vyrobit dvě jména pro totéž místo.

## Zamčená dlaždice musí být poznat i BEZ ťuknutí

Napoprvé jsem zámek udělal jen jako kontrolu při ťuknutí — dlaždice vypadala úplně normálně
a člověk se o zámku dozvěděl až po kliknutí. Jiří Honomichl na to upozornil týž den:
**„zamčeno" musí být vidět na dlaždici.**

Řešení: **šedý 🔒 v pravém horním rohu dlaždice**, přidaný jako `<span>` s vlastním inline
stylem (`position:absolute; top:-2px; right:6px; opacity:.8; filter:grayscale(1)`).
`.appcell` má `position:relative`, takže to drží samo.

⚠️ **Nepoužívej k tomu `.appbadge`**, i když je to hotový odznak přesně v tom rohu:
červené kolečko v appce znamená **„máš tu něco k řešení"** (počet položek), a u zámku by to
říkalo pravý opak. Vlastní inline styl navíc nemění nic sdíleného.

Zámeček vidí **všichni včetně toho, komu je odemčeno** — jinak by se před vykreslením dlaždice
muselo zjišťovat, kdo je přihlášený, a to je zbytečná složitost navíc.

**Jak zkontrolovat vzhled, když se na tu obrazovku v prohlížeči nedostaneš:** otevři živou
`/mobile`, přepiš `document.body.innerHTML` na pár dlaždic postavených ze stejného značkování,
jaké vyrábí `appCell`, a vyfoť to. Použije se skutečný vzhled appky, ne nákres.

## Jak se to ověřovalo

Živá stránka `/mobile` stažená před i po každém kroku; porovnání na obě strany (nové texty
tam jsou, staré už ne), počet dlaždic, počet skriptových bloků (31 → 31, tedy žádný fragment
se nerozbil) a kontrola, že po smazání nezůstal viset ani jeden odkaz na `__M2W.hr`,
`__M2W.prace`, `__M2W.hr_interni` ani `__M2W.doch_zitrek`. Každý zápis šel cíleně
s pojistkou na otisk a napřed nanečisto na serveru — délka pokaždé seděla na znak.

