# Chrome - "zamrzla stranka" byva ve skutecnosti posunute klikani (zoom) plus pomale nacitani, ne pad

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

## Priznak

Pri praci pres Chrome (Claude-in-Chrome) se stranka tvari **zamrzle** - snimek obrazovky skonci chybou *"CDP sendCommand Page.captureScreenshot timed out after 30000ms ... The renderer may be frozen or unresponsive"*, dalsi kliknuti uz **nic nedelaji** a stranka zustava stat. Nejcastejsi u tezkych aplikaci (Google Play Console), ale plati obecne.

Do 18. 8. 2026 to bylo v poznamkach vedene jako *"Play Console zamrza, nelezt tam"*. **Neni to pravda.**

## Skutecna pricina (overeno 18. 8. 2026)

**1) Stranka nezamrzla - JavaScript v ni bezi dal.** Overeno tak, ze `javascript_tool` v te "zamrzle" strance normalne vratil vysledek. Zamrzlo jen porizeni snimku, protoze aplikace byla zaneprazdnena. Play Console potrebuje **8-15 s** na vykresleni; 30s timeout na snimek pak sedne i pri zdravem behu.

**2) Klikani podle souradnic ze snimku mirilo vedle, protoze prohlizec byl na 75 %.** Zmereno v teze strance:

| Velicina | Hodnota |
|---|---|
| `devicePixelRatio` (= priblizeni) | **0,75** |
| viewport (`innerWidth` x `innerHeight`) | 2560 x 1185 CSS px |
| vraceny snimek | 1568 x 726 px |
| polozka "Marti Pasek" ve strance | CSS **1175, 640** |
| tataz polozka na snimku | zhruba **540, 294** |

Podil je **2,18**, ne 1,63, ktere by odpovidalo pomeru viewportu a snimku. Rozdil je presne **1/0,75** - tedy to priblizeni. Kdo odecte souradnici ze snimku a posle ji jako kliknuti, **trefi uplne jine misto** - a stranka pak vypada, ze nereaguje.

Priblizeni **neni per-web** - stejnych 75 % vyslo i na `strategie-ai.com`. Je to nastaveni prohlizece, takze to plati pro **kazdou** stranku, kterou takhle ovladame (i overovani v ERP a v mobilni appce podle pravidla o zivem overovani).

## Co s tim

- **Neklikej podle souradnic ze snimku.** Najdi prvek (`find` -> `ref`, nebo `javascript_tool` a `element.click()`) a klikni na nej primo. Funguje bez ohledu na priblizeni. Takhle se 18. 8. proslo prihlasenim do Play Console, seznamem aplikaci, Prehledem publikovani i produkcnim kanalem - bez jedineho "zamrznuti".
- **`ref` z predchoziho volani muze zestarnout** (aplikace se prekresli) - hlasi to *"No element found with reference"*. Hledej a klikej v jednom kroku, nebo klikej pres JS.
- **Timeout snimku neber jako pad.** Nejdriv over `javascript_tool`, jestli stranka zije. Tezke aplikace nacitej s prodlevou 8-15 s.
- Kdyz uz souradnice potrebujes, **srovnej priblizeni na 100 %** (Ctrl+0 rucne - klavesove zkratky pro zoom nastroj neumi).

## Pouceni obecne

"Nereaguje to" je **priznak, ne pricina**. Nez to prohlasim za zamrznuti, musim rozlisit tri veci - stranka nezije / stranka zije ale je pomala / stranka zije a rychla, jen kliknuti mirilo vedle. Rozhodne to jeden dotaz na JavaScript ve strance.

