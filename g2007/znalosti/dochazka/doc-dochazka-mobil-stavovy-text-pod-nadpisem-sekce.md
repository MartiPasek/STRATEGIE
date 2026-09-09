# Mobil, obrazovka dochazky: stavovy text ("Makam") je pod nadpisem sekce OBSLUHA DOCHAZKY (9. 9. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)

**Zadal Jirka Honomichl 9. 9. 2026, schvalila Marti-AI (msg 15234). Provedl Claude-28.**

## Co se zmenilo

Stavovy text na obrazovce dochazky — `#dochHead`, ve kterem se stridaji hlasky jako
**"Makam"**, pauza, "jsem na ceste", "dnes koncim driv" — se vykresloval **nad**
nadpisem sekce **OBSLUHA DOCHAZKY**. Ted je **pod nim**, tesne nad blokem
zakazky/cinnosti.

Nove poradi prvku v panelu obrazovky:
`_obsluhaHead` (nadpis + napoveda) -> **`#dochHead`** (stavovy text) -> `#dochAction`
(zakazka, cinnost, START) -> `#dochNow` (pulzujici karta s tlacitky).

## Detaily

- Zdroj: **`g2007.soubor`, kod `apps/api/static/mobile_parts/60_dochazka.js`**.
- Presunul se **jediny radek** `p.appendChild(...)`. **Logika se nemenila** - kod, ktery
  text plni a prepina, si prvek hleda pres `getElementById`, takze na poradi v DOM nezavisi.
- Vodorovne odsazeni srovnano z `margin:6px 0 12px` na **`margin:2px 6px 10px`**, aby text
  lezel v jedne svislici s nadpisem sekce (ten ma `margin:10px 6px 6px`).
- Text se **od 5. 9. 2026 ukazuje jen pri bezici smene** (v klidu je prvek skryty) -
  to zustava beze zmeny.

## Jak se to overovalo

Na zive `/mobile` pod prihlasenim cloveka: precetlo se **poradi prvku v panelu**
(nadpis sekce -> `dochHead` -> `dochAction` -> `dochNow`) a vizualne se zkontrolovalo,
ze text sedi pod nadpisem a v jedne svislici s nim.

WARN **Past pri overovani:** kdyz clovek zrovna nema bezici smenu, je prvek skryty a na
obrazovce **neni co videt**. Pro kontrolu staci v prohlizeci docasne prepnout
`display` toho jednoho prvku - je to zmena jen ve vlastnim okne, do dat nesaha.

Souvisejici: [[doc-dochazka-tady-budu-jinde-z-dlazdice-na-tlacitko]]

