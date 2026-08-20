# Mobil - fragmenty nesdili scope a nativni appka nema JS dialogy (dve pasti, 11.8.2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Mobil - dve pasti, ktere stály cely den (11. 8. 2026)

Zapsal C-28 (Jirka Honomichl), schvalila Marti-AI (msg 12566 a 12575).
Obe pasti se projevily na stejne veci - tlacitko "Zrusit" u zadosti o absenci.

## 1) Fragmenty mobile.html NESDILEJI scope - helpery volej pres `window.__M2W`

**Pravidlo (formulace Marti-AI):** *"V mobile.html fragmentech vzdy volat helpery pres
`window.__M2W`, nikdy holym jmenem - 30 samostatnych `<script>` bloku nesdili scope."*

Sestavena `mobile.html` neni jeden velky IIFE. Je to **30 samostatnych bloku `<script>`**
a kazdy si pomocne funkce vytahuje z `window.__M2W`. Kdyz zavolas helper holym jmenem
v bloku, ktery si ho nevytahl, spadne to na `ReferenceError` az za behu.

**Realny prusvih 11.8.2026-** nahradil jsem systemove `confirm()` za `confirmDialog()`
v `50_skupiny_vyroba.js`. `confirmDialog` je definovan v bloku 5, pouzil jsem ho v bloku 19,
ktery si ho neimportuje. Vysledek- tlacitko misto "nic nedela" nove **spadlo**, tedy horsi
stav nez pred opravou. Jirka to nasel do 10 minut (screenshot z iPhonu-
`ReferenceError- Can't find variable- confirmDialog`, radek 4305).

**Jak overit PRED nasazenim** (spolehlive, v prohlizeci na zive strance)-
```js
const src = await fetch('/mobile', {cache:'no-store'}).then(r=>r.text());
const bloky = src.split(/<script[^>]*>/i);
// v kterem bloku je definice a v kterem pouziti - musi to byt tentyz blok,
// jinak volej pres window.__M2W
```
A za behu- `typeof window.__M2W.confirmDialog` vs `typeof window.confirmDialog`.

**Poučeni, ktere plati obecne-** pritomnost retezce v souboru NENI dukaz, ze to za behu
funguje. Overovat dosazitelnost, ne vyskyt.

## 2) Nativni appka (Android I iOS) nema obsluhu systemovych dialogu

V nativni appce **`confirm()` a `alert()` mlcky neudelaji nic**. Neni to chyba webu,
je to chybejici obsluha na strane obalu-

| Platforma | Soubor | Co tam JE | Co CHYBI |
|---|---|---|---|
| Android | `APP/Mobile/.../HybridActivity.kt` (WebChromeClient, ~radek 675) | onPermissionRequest, onShowFileChooser | **onJsConfirm, onJsAlert** |
| iOS | `APP/iOS/mobile/ContentView.swift` (WKUIDelegate, ~radek 35) | requestMediaCapturePermissionFor, decidePolicyFor | **runJavaScriptConfirmPanelWithMessage, runJavaScriptAlertPanelWithMessage** |

**Dusledek-** `if(!confirm(...)) return;` v nativni appce skonci hned na tom `return`.
Zadny request, zadna hlaska - uzivatel hlasi "kliknul jsem a nic se nestalo". A hlavne-
**mizi i CHYBOVE hlasky**, takze operace selze a clovek se to nedozvi. To je zavaznejsi
nez samotna tlacitka.

**Dukaz z obou stran (11.8.2026)-** ve zdrojacich obou obalu chybi obsluha; a naostro
v prohlizeci- kdyz okenko vrati nepravdu, neodesle se nic, kdyz pravdu, akce projde
a server vrati ok (zadost 81 skoncila jako `cancelled`).

**Rozsah k 11.8.2026-** v zive strance zbyva **91 `alert()` a 30 `confirm()`**.

**Reseni (schvalila Marti-AI)-**
- **(A) hned, bez vydani appky-** nahradit za `window.__M2W.confirmDialog(title, msg, okLabel, onOk)`
  (definovan v `10_core.js`) a za in-page hlasky. Zije to v `g2007.soubor`, takze plati
  okamzite i pro uz nainstalovane verze appky. **Po davkach, kazda davka ke schvaleni.**
- **(B) do pristiho buildu-** doplnit dialogy **na obou platformach v JEDNOM buildu**
  (ne Android ted a iOS pozdeji, jinak je (B) napul).

## 3) Bonus - dve pasti pri editaci fragmentu pres SQL most

- **Lokalni kopie fragmentu byva zastarala.** `60_dochazka.js` byl tyz den refaktorovan
  jinou instanci (`app` -> `window.__M2W.app`), moje kotva podle lokalniho souboru
  nesedla a `replace()` tise neudelal NIC - pritom most vratil "OK, 1 radek".
  **Kotvu vzdy over dotazem do `g2007.soubor`, ne podle souboru na disku, a po zapisu
  over obsah ctenim.**
- **Dvojtecka v JS payloadu je pro most parametr.** `{id:z.id}` v SQL retezci se vylozi
  jako bind parametr `:z`. Piš `{id : z.id}` (mezera za dvojteckou) nebo skladej pres
  `chr(58)`. Tyka se i CSS - `margin-top:6px` je `:6px`.

