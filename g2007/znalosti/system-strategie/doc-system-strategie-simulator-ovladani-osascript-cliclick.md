# iOS Simulátor na Macu: jak v něm klikat a tahat prstem (osascript + cliclick), ověřeno 26.8.2026

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# iOS Simulátor na Macu: jak v něm klikat a tahat prstem

Zapsal Claude-28 (Jirka Honomichl) 26.8.2026 při testování gesta zpět
(`doc-system-strategie-ios-gesto-zpet-screen-edge-pan`). Nástroje ani
postup nejsou pro jednu appku, jde o obecně použitelnou techniku.

## Předpoklad

Terminál, ze kterého se pouští `osascript`, musí mít v macOS povolenou
**Přístupnost** (Nastavení systému → Soukromí a zabezpečení → Přístupnost).
Když ve VS Code, je to proces `Code Helper`, ne `Visual Studio Code`
samotný. Ověření bez klikání: `osascript -e 'tell application "System
Events" to get name of first process whose frontmost is true'` — chyba
`-25211 nema povolen asistencni pristup` znamená, že oprávnění chybí nebo
po jeho zapnutí ještě neproběhl **úplný restart VS Code** (Cmd+Q).

## Jediný klik

`osascript -e 'tell application "System Events" to click at {x,y}'` funguje,
ale je to klik na **absolutní souřadnici celé obrazovky Macu**, ne v appce.

## Tažení (drag) — System Events samo neumí

Pro gesta jako tažení od kraje obrazovky (swipe) `System Events` nemá
vestavěný příkaz. Řešení: **`cliclick`** (`brew install cliclick`) —
`cliclick dd:x,y dm:x2,y2 dm:x3,y3 du:x4,y4` (drag-down = stisk,
drag-move = tažení, drag-up = puštění).

## Past: terminál přebírá focus zpět mezi příkazy

Simulátor je potřeba mít na obrazovce **frontmost** (`osascript -e 'tell
application "Simulator" to activate'`), jinak `System Events` ani
`cliclick` neklikají do simulátoru, ale do okna, které je zrovna nahoře
(typicky VS Code). **Mezi jednotlivými bash příkazy se ale VS Code
samo vrací do popředí** — proto musí být aktivace Simulátoru a samotná
akce (klik/tažení) v **jednom** bash příkazu (`osascript ... activate &&
sleep 0.5 && cliclick ...`), ne ve dvou po sobě.

## Jak najít přesné souřadnice tlačítek

1. `screencapture -x plny_screenshot.png` — screenshot celé obrazovky Macu.
   Souřadnice v tomto obrázku (v pixelech) odpovídají **1:1** souřadné
   soustavě, kterou používá `System Events`/`cliclick` (ověřeno: okno
   Simulátoru zjištěné přes `System Events ... get {position, size} of
   window 1` sedělo s tím, co je vidět na screenshotu).
2. `screencapture -x -R<x>,<y>,<w>,<h> vyrez.png` — ořízne jen danou
   oblast, užitečné pro přesné doladění (tlačítko v dolní liště appky
   apod.). Rozměr výstupního PNG odpovídá přesně zadanému `w`,`h`
   (ověřeno přes `sips -g pixelWidth -g pixelHeight`).
3. Pro **pixelově přesné** hledání hranice (např. přesně kde končí černý
   rámeček telefonu a začíná dotyková plocha obrazovky, důležité u gest
   od kraje) nestačí jen se dívat na obrázek — `sips` neumí číst
   jednotlivé pixely a na Macu není `ImageMagick`/`PIL` předinstalované.
   Řešení: `python3 -m venv venv && venv/bin/pip install Pillow` (systémový
   `pip3 install --user` na tomhle Macu odmítne kvůli PEP 668 ochraně
   Homebrew Pythonu) a pak `im.getpixel((x,y))` po řádcích/sloupcích
   najít přechod barvy (černý rámeček → bílé/barevné pozadí appky).

## Screenshot obsahu appky (bez rámečku okna)

`xcrun simctl io <UDID> screenshot vystup.png` — čistý obsah appky,
nezávislé na tom, jestli je Simulátor frontmost. Pro zjištění UDID/stavu:
`xcrun simctl list devices | grep -i booted`.

