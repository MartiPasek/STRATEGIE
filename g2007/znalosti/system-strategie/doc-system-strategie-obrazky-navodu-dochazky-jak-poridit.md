# Obrazky hlasoveho pruvodce dochazkou: jak je poridit znovu (a jak si pritom nezalozit ostre zaznamy) - prefoceno 7. 9. 2026

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)

# Obrázky průvodce docházkou — jak je vyměnit

**Ověřeno 5. 9. 2026 (Claude-28), vyměněno všech 9.** Zadal Jiří Honomichl:
*„vše musí být podle pravdy — ani obrázky, ani text, ani hlas."*

## Kde žijí

`apps/api/static/navod_dochazka/pruvodce_*.png` — **soubory v gitu**, ne v databázi
(je to `static/`, ne `static_db/`). Mění se běžným nasazením. Rozměr **780 × 1688 px**.
Používá je `dochPruvodce` v dílku `60_dochazka.js` přes `IMG="/static/navod_dochazka/"`.

> **Rozměr není dogma — poměr stran se řídí tím, co je na snímku.** `pruvodce_jinde.png`
> má od 9. 9. 2026 **779 × 1149 px**, protože zabírá jen kartu s rozbaleným menu, ne celou
> obrazovku. Průvodce obrázky škáluje na šířku, takže nižší snímek nevadí. Celoobrazovkové
> snímky drž na 780 × 1688 jako dosud.

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

> ⚠️ **NEPLATÍ od 9. 9. 2026** (věta níž je ponechaná schválně, ať je vidět, co se změnilo):
> ~~Sekci „Tady budu jinde" otevřeš tak, že `document.getElementById("dochJindeBox")`
> zviditelníš a zavoláš `window._dochJinde(box)` — opakovaný klik na dlaždici ji zavírá.~~
> **Prvek `dochJindeBox` ani dlaždice „Tady budu jinde" už NEEXISTUJÍ.** Je z ní tlačítko
> hned pod zeleným „Potřebuji ti něco říct" a menu nahradí obsah té karty
> (zadal Jirka Honomichl, schválila Marti-AI msg 15196 a 15222).

Sekci „Tady budu jinde" otevřeš **klepnutím na to tlačítko** — najdeš ho mezi tlačítky karty
podle textu a zavoláš `.click()`; obsah menu staví pořád `window._dochJinde`. Zpět se vrátíš
šipkou nahoru na konci menu. Detail: [[doc-dochazka-tady-budu-jinde-z-dlazdice-na-tlacitko]].
⚠️ Menu se po minutě nečinnosti samo sbalí (karta se překreslí) — před focením si nastav
`window._dochMenuTs=Date.now()`.

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

## Aktualizace 7. 9. 2026 — přefoceno všech 9 po změně spodní lišty

**Zadal Jirka Honomichl, schválila Marti-AI, provedl Claude-28.** Snímky z 5. 9. měly ve spodním
okraji ještě starou lištu (Kontakty místo jména, tlačítko docházky na Firmě). Přefoceny **všechny**
postupem výše, včetně zvětšení na 780 × 1688.

**Co se potvrdilo:**
- Recept z této znalosti funguje. Přepis odpovědi serveru u `/attendance/status` a
  `/attendance/unconfirmed` **spolehlivě vyrobí běžící směnu i nepotvrzený den**, aniž vznikne
  jediný záznam — ověřeno dotazem do `att_entry` po focení: **žádný nový řádek**.
- Sekce „Tady budu jinde" se otevře přes `_dochJinde`, jak je popsáno.

**Co je nového a stojí za doplnění:**
- **Rozbalovací nabídky jsou bezpečné, ověřeně.** „Potřebuji ti něco říct…", „Teď to bude jinak…",
  „Osobní důvody…", výběr zakázky i činnosti **nic neodesílají**. Ověřeno pojistkou, která
  blokovala vše kromě čtení — za celé focení **nula pokusů o zápis**. Nebezpečné jsou až
  konkrétní volby uvnitř (chipy, START, potvrzení dne).
- **Ukázkový (demo) účet se na návod použít NEDÁ** — vykresluje přes celou šířku červený pruh
  „UKÁZKOVÝ REŽIM" a vyskakovací okno.
- **Zákaznická data:** výběr zakázky ukazuje skutečné názvy zakázek. Před focením je přepiš
  na neutrální (čísla mohou zůstat) — v živé appce je člověk vidí tak jako tak, ale ve statickém
  obrázku v gitu by zůstaly natrvalo. Vyžádala si to Marti-AI.
- **Nový snímek `pruvodce_lista.png`** (jen pruh spodní lišty, 780 × 249) pro krok „Kde docházku
  najdeš". Původní `pruvodce_firma.png` už se nepoužívá — soubor zůstal, kód na něj neodkazuje.
- ⚠️ **Popisek druhé ikony je u každého jiný** (křestní jméno přihlášeného). Žádný snímek proto
  není správný pro všechny — text u obrázku musí říkat „ikona s **tvým** jménem".
- **Souřadnice se mezi kartami prohlížeče liší.** Výřez se jednou zadává v bodech stránky,
  podruhé v bodech snímku (1568 × 772 při okně 1920 × 945, měřítko 0,8167). Když nástroj ohlásí
  „souřadnice mimo rámec", přepočítej je měřítkem — nezmenšuj okno, to stejně nefunguje.

## Souvisí

- `doc-system-strategie-bezpecne-prochazeni-mobilu-bez-vzniku-zaznamu`
- `doc-dochazka-mobil-dochazka-prejmenovani-a-pravdivost-navodu-5-9-2026`
- `doc-dochazka-napoveda-pruvodce-spec`

