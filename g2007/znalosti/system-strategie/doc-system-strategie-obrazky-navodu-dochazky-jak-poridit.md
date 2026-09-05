# Obrázky hlasového průvodce docházkou: jak je pořídit znovu (a jak si při tom NEZALOŽIT ostrý záznam)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Obrázky průvodce docházkou — jak je vyměnit

**Ověřeno 5. 9. 2026 (Claude-28), vyměněno všech 9.** Zadal Jiří Honomichl:
*„vše musí být podle pravdy — ani obrázky, ani text, ani hlas."*

## Kde žijí

`apps/api/static/navod_dochazka/pruvodce_*.png` — **soubory v gitu**, ne v databázi
(je to `static/`, ne `static_db/`). Mění se běžným nasazením. Rozměr **780 × 1688 px**.
Používá je `dochPruvodce` v dílku `60_dochazka.js` přes `IMG="/static/navod_dochazka/"`.

## Jak je pořídit

Nejsou to snímky z telefonu — jsou **z prohlížeče** (poznáš to podle odznaku „prohlížeč").
Dají se tedy pořídit znovu úplně stejně:

1. Otevři `/mobile` v prohlížeči pod živým přihlášením.
2. **Změna velikosti okna nefunguje** (`resize_window` projde, ale plocha zůstane 1920×945).
   Není potřeba: sloupec appky je `BODY` o šířce **436 px** na pozici `x=742`, poměr
   436:945 = 0,461 — prakticky totožný s cílem 780:1688 = 0,462.
3. Snímek okna přijde jako **1568×772**, tedy měřítko `1568/1920 = 0,8167`.
   Výřez: `x0 = round(742 × 0,8167)`, šířka `round(436 × 0,8167)`, celá výška.
4. Zvětši na 780×1688 (`Image.LANCZOS`). Výsledek je čitelný a věrný.

## ⭐ Jak nafotit stavy, které zrovna nenastaly (bez zásahu do dat)

Tři obrázky ukazují **běžící směnu** a jeden **nepotvrzený den**. Nezakládej je!
Místo toho **přepiš ODPOVĚĎ serveru v prohlížeči** — server o tom neví a nic se nezapíše:

- běžící směna: u `/attendance/status` doplň
  `open={open_type:"work", zac:"07:30", …}`
- nepotvrzený den: u `/attendance/unconfirmed` doplň
  `days=[{day:"<ISO>", od:"7:26", do:"16:26", hodin:7.52, zaznamu:3}]`
  ⚠️ **Názvy polí musí sedět přesně** (`day/od/do/hodin/zaznamu`) — jinak se karta
  vykreslí s „undefined" a takový obrázek se nesmí nasadit.

Sekci „Tady budu jinde" otevřeš tak, že `document.getElementById("dochJindeBox")`
zviditelníš a zavoláš `window._dochJinde(box)` — **opakovaný klik na dlaždici ji zavírá.**

## ⛔ VAROVÁNÍ: klikání v živé appce ZAKLÁDÁ ostré záznamy

5. 9. 2026 při focení vznikly Jiřímu Honomichlovi **dva skutečné záznamy docházky**
(`att_entry` 10017839 a 10017840, jeden z nich zůstal otevřený s poznámkou
„Dnes už se mnou nepočítej ;)"). Nikomu naštěstí nepřišla notifikace.

Znalost `doc-system-strategie-bezpecne-prochazeni-mobilu-bez-vzniku-zaznamu` říká
**„nemačkej nic — jen zobrazuj"**. To platí doslova: samotné procházení přes
`window.__M2W.go()` je bezpečné, **klikání není.**

**Pojistku (odposlech `window.fetch`) čti PRŮBĚŽNĚ, ne až na konci.** 5. 9. byla zapnutá
a oba zápisy poctivě zachytila — jen se na ni nikdo nepodíval včas. Kdo ji kontroluje po
každém kliknutí, zastaví se u prvního zápisu místo u druhého.

## Souvisí

- `doc-system-strategie-bezpecne-prochazeni-mobilu-bez-vzniku-zaznamu`
- `doc-dochazka-mobil-dochazka-prejmenovani-a-pravdivost-navodu-5-9-2026`
- `doc-dochazka-napoveda-pruvodce-spec`

