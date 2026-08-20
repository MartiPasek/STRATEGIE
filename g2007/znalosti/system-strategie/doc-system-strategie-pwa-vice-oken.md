# Víc oken STRATEGIE naráz (PWA multi-window) + ikonka „Nové okno" v hlavičce ERP

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

## Kontext
Peta (C26) chtěla mít STRATEGIE ERP otevřené ve **více oknech naráz** (jako dřív 3 Centrály). Nainstalovaná PWA defaultně jede jako jedno okno. Vyřešeno 30.7.2026.

## Proč samotné kliknutí na ikonu na liště nestačí
- V `apps/api/static/erp/manifest.json` je `launch_handler.client_mode` přepnuto z `focus-existing` na **`navigate-new`**. To ale ovlivní jen **nový spouštěč** (spuštění z URL / jump-list zkratky).
- **Kliknutí na ikonu běžící PWA na hlavním panelu Windows VŽDY jen přepne na existující okno** — to je chování OS, `navigate-new` se tam neuplatní. (Nezaměňovat za bug.)

## Jump-list zkratka „Nové okno" (manifest.shortcuts) — nespolehlivá
V `manifest.json` je v poli `shortcuts` položka „Nové okno" (url `/erp/?okno=nove`). Objeví se v „Úlohách" (pravý klik na ikonu) **až po reinstallu PWA** a Windows si jump-list u PWA **drží zakešovaný** a nerad ho přegeneruje → v praxi se položka často neukáže. Ponecháno, ale není to hlavní cesta.

## SPOLEHLIVÉ řešení = ikonka „Nové okno" přímo v hlavičce ERP
- Soubor: `modules/erp/api/router.py`, inline HTML shellu ERP, blok `erp-header-brand-row` (kolem ř. 61062), hned **za tlačítkem „Tvoje Marti"**, PŘED appkami (Mobil/Web/EUROSOFT/Výroba/Finance).
- Element `<a id="erpNoveOknoLink" class="erp-navico">` s `onclick="event.preventDefault(); window.open('/erp/','_blank','noopener');"`.
- **Klíč: `window.open` BEZ pevného názvu okna** (target `_blank`) = pokaždé **NOVÉ** okno, nezávisle na `launch_handler`. V nainstalované PWA (scope `/erp/`) Chrome otevře nové **standalone** okno. Pevný název (jako u Mobil/Web `window.open(url,'strategieMobil',...)`) by naopak recykloval jedno okno — pro „nové okno" ho tedy nepoužívat.
- Funguje **hned po Ctrl+F5**, bez reinstallu PWA.

## Ikona
Inline SVG okno **2×2 skla** (rounded `rect` + vodorovná + svislá čára = 4 tabulky), `stroke="currentColor"`, 17×17, `vertical-align:middle` — ladí s ostatními emoji ikonkami v liště. (Peta si vybrala vzhled okna se čtyřmi skly.)

## Umístění (rozhodnutí Peta)
Za „Tvoje Marti", oddělené od skupiny appek — ty appky jsou „záložky" a můžou přibývat, „Nové okno" má zůstat stranou na stabilním místě (levá strana = akce; k avataru vpravo patří věci kolem účtu).

## Poznámka pro příště
Chceš-li kdekoli tlačítko „otevři to ve vlastním okně", vzor je `window.open(url,'_blank','noopener')` s in-scope URL. Fixní název okna = recyklace jednoho okna; `_blank`/bez názvu = nové okno.

