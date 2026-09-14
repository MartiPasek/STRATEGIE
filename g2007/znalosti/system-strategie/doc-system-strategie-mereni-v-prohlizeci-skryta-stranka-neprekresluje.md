# Mereni v prohlizeci: na skryte nebo minimalizovane strance nefiruje ResizeObserver ani animace - a vypada to jako vada aplikace

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)

Zapsal Claude-28 (okno strategie-29) 14. 9. 2026. Vzniklo tim, ze dve okna nezavisle na sobe
"nasla" vadu, ktera zadna vada nebyla. Zastavilo se to tesne pred zasahem do kodu.

## Co se stalo

Pri praci na vzhledu mobilu jsme meriti, jestli reaguje pojistka, ktera hlida vysku spodni listy
(`ResizeObserver` nad `navwrap` v `74_claude27_render_init.js`). Namereno: lista vyrostla z 61 na
109 bodu, ale promenna `--navh` zustala na 61. Po vyvolani udalosti `resize` naskocila spravne.

Z toho oba vyvodili totez: "observer je hluchy, registrace nejspis selhala v `try/catch`".
**Byl to spatny zaver.** Skutecna pricina: okno prohlizece bylo minimalizovane.

## Mereni, ktere to odhalilo (udelej ho VZDY, nez z prohlizece vyvodis zaver)

    document.visibilityState            // "hidden" = stranka se nepřekresluje
    let n=0; requestAnimationFrame(function t(){n++;requestAnimationFrame(t)});
    // po ~900 ms: n === 0 znamena, ze se nekresli vubec

Namereno dvakrat nezavisle (dve ruzna okna, tataz stranka): `hidden` a **0 snimku za 900 ms**.

## Proc to matlo

**ResizeObserver dorucuje volani v prekreslovacim kroku.** Kdyz se stranka nekresli, nedorucí
se nic - a to ani prvni volani, ktere po `observe()` prijde jinak vzdy. Naproti tomu **udalosti
jako `resize` se doruci i skryte strance**. Proto to vypadalo jako "observer nefunguje, ale
funkce ano" - tedy presne jako vada v registraci.

## Co merenim na skryte strance NAMERIS spolehlive (a co ne)

| funguje i skryte | nefunguje |
|---|---|
| `getComputedStyle` (barvy, velikosti, pisma) | `ResizeObserver`, `IntersectionObserver` |
| `getBoundingClientRect`, `offsetHeight` (rozvrzeni se pocita) | `requestAnimationFrame` |
| `canvas.measureText` (test, jestli se pismo opravdu nacetlo) | animace a prechody |
| udalosti `resize`, `orientationchange`, klikani | cokoli, co ceka na vykresleni |

Snimky obrazovky pres rozsireni v prohlizeci vyjdou spravne i tehdy - zachyceni si vykresleni
vynuti. Proto snimek nic neprozradi a clovek si mysli, ze stranka bezi normalne.

## Co z puvodniho zjisteni zustava platne - DOMERENO 14. 9. 2026

`_syncNavH` funguje a reakce na `resize` funguje. **A observer je v poradku take - domereno
tyz den na vytazenem okne (okno strategie-4c).** Na tomto miste do te doby stalo, ze to
NEVIME; **to uz neplati.**

Namereno pri `visibilityState` = "visible" a bezicim vykreslovani:

| co | vysledek |
|---|---|
| volani po `observe()` | 1 (prijde vzdy - na skryte strance neprislo ani ono) |
| volani po zmene vysky listy | 2 |
| `--navh` po zvetseni listy z 61 na 101 bodu | naskocilo samo na 101 |

Overeno i na druhem miste: panel obrazovky "Kdo kde", ktery si vysku dopocitava stejnym
zpusobem (`_paneFit` v `50_skupiny_vyroba.js`), se po zvetseni spodni listy sam zmensil
ze 722 na 682 bodu **bez vyvolani jakekoli udalosti** a po uklidu se sam vratil na 722.

**Zaver: v kodu se nic neopravovalo, protoze nebylo co.** Hypoteza "registrace selhala
v `try/catch`" byla nepodlozena a neplati - nezakladej na ni zadny zasah.

## Pravidlo

Nez z chovani v prohlizeci udelas nalez, over si, ze se stranka **opravdu kresli**.
Bez toho hrozi, ze se vyhodi funkcni pojistka kvuli tomu, ze mel nekdo minimalizovane okno.

