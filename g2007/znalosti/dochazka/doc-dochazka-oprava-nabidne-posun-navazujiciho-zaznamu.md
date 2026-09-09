# Oprava casu v dochazce nabidne posun navazujiciho zaznamu (Ano / Ne / Storno) - Peta 8.9.2026

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)


# Oprava casu nabidne posun navazujiciho zaznamu

**Zadala Peta 8.9.2026.** Kdyz se nekdo zapomene odhlasit z pauzy, editor ji zkrati
konec - a navazujici praci musel dosud posunout RUCNE druhou opravou. Peta doslova:
*"pri rucni oprave snadno vznikne chyba, at uz preklepem, nebo hur, kdyz ti do toho
neco skoci a tu navazujici praci zapomenes upravit."*

## Jak se to chova

Kdyz oprava posune **zacatek nebo konec** zaznamu a nekdo na nej **presne na minutu**
navazoval, server misto ulozeni vrati otazku a UI ukaze tri tlacitka.

| Volba | Co se stane |
|---|---|
| **Ano, oprav i navazujici** | Ulozi se **obe** opravy v JEDNE transakci. Soused jde stejnym motorem (supersede + novy radek, `source='manual_fix'`), takze zezelena, ma audit i notifikaci. |
| **Ne, jen tenhle** | Ulozi se jen opravovany zaznam - stav jako pred 8.9.2026 vcetne cerveneho varovani o prekryvu. |
| **Storno** | **Neulozi se vubec nic** - UI druhe volani na server uz neposle. |

- **Oba smery** (Peta 8.9.2026): posun konce nabidne souseda ZA nim, posun zacatku
  souseda PRED nim. Plati i u opravy prichodu u **beziciho** zaznamu.
- **Presne na minutu.** Mezera nebo prekryv se nenabizi - jinak by se tise ztracely minuty.
- **Jen prvni soused v kazdem smeru**, zadna retezova reakce.
- Duvod opravy se prebira **stejny** a k sousedovi se pripise "posunuto s opravou #ID".

## Kdy se otazka NENABIDNE (a je to zamer)

- soused je stornovany, ohlaseni, **z Centraly** (`source_system`) nebo **bezici** (bez konce),
- posunem by mu konec vysel pred zacatek,
- do uvolneneho mista zasahuje **treti zaznam** (kontrola kolize),
- **cas se nezmenil** - pri zmene jen zakazky nebo cinnosti se nikdo na nic nepta.

## Kde to zije

- **Server**: `g2007.python` kod **`att_fix_entry`** - funkce `_att_navaznost` (hledani),
  `_navaz_kolize` (kontrola tretiho zaznamu), `_navaz_otazka` (text), `_navaz_posun` (zapis).
  Endpoint bere dva nove parametry: **`navaz`** (`ano` / `ne`) a **`navaz_umim`**.
- **`navaz_umim` je opt-in** - posila ho jen UI, ktere se umi zeptat. Stary klient
  (treba appka v telefonu s ulozenou starou verzi) tim padem jede po staru
  a nic se mu nerozbije.
- **Delegat** v `modules/erp/api/router.py` (endpoint `/app/attendance/fix/entry`)
  oba klice predava - commit `40948582`, 8.9.2026.
- **UI (vsechna tri mista, kde smi k opravam dochazet)**: `dochazka-opravy.html`
  (`fixEntryPost` + `navazBox`), `dochazka-po-zakazkach.html` (`navazPtejSe` + blok
  `d_navaz` v dialogu), `mobile_parts/60_dochazka.js` (`_fixEntryPost` + `_fixNavazBox`).

## Na co si dat pozor

- Otazka prijde **skoro u kazde zmeny casu** - pichnuti na sebe navazuji temer vzdy
  (overeno na datech 8.9.2026: prace -> prestavka na minutu presne u vetsiny lidi).
  Je to zamer, ne chyba; "Ne" je jedno kliknuti.
- Kdyz clovek da **Ano**, prepocita se varovani o prekryvu znovu - to puvodni
  se pocitalo jeste pred posunem souseda a lhalo by.
- Rozpad na zakazky (`vyroba_work`) srovna kanonicka kaskada `att_sync_vyroba_work`,
  ktera bezi az po obou zapisech - proto se nemusi volat dvakrat.

Souvisi: `doc-dochazka-att-entry-vyroba-work-kaskada` (kaskada rozpadu),
`doc-dochazka-opravy-prehled-ui` (chovani obrazovky oprav) a funkce `att_fix_merge`,
ktera resi obdobnou vec po **stornu** (seseti navazujicich useku).

