# 🔧 Rozvaděče — konkrétní výrobní pravidla STANDARD (řada přístupnost AI)

> **Autor: Claude (ID23), 1. 7. 2026.** Hloubková vrstva k `Rozvadece.md` — **skutečná pravidla**
> čtená přímo z příloh směrnic (`@@KBREAD <téma>`). Konkrétní čísla a postupy, ne jen témata.
> Zdroj pravdy = oficiální směrnice; tady je můj destilát pro rychlou orientaci. **Živé** — plním
> postupně, jak čtu dalších 42 STANDARD témat + zákaznická specifika.

## Pospojení (PE / ochranné pospojení) — směrnice „STANDARD – pospojení rozvaděče" (ec_id 362)
- **Všechny plechy a rámy** v rozvaděči musí být pospojeny.
- U rámů/montážních/bočních plechů, kde je namontován **hlavní vypínač**, se **průřez PE volí podle
  přívodu**.
- Není-li v el. plánu určen průřez: pospojení **dveří, zad, střech, boků = Ø 6 mm² žluto‑zelená (YE/GN)**.
- **Nejmenší používaný ochranný vodič = Ø 2,5 mm² YE/GN** (pokud plán neurčuje jinak).
- Řeší se zvlášť: pospojení dveří/střechy/boku/zad, rámu desky, montážního plechu.

## Barevné značení žil vodičů — „STANDARD – barevné značení žil vodičů" (ec_id 354)
- Definuje **barvy žil** (CZ i cizojazyčně): černá, hnědá, červená, oranžová, žlutá, zelená, modrá,
  fialová, šedá… → mapování barva ↔ funkce/napětí (silové/řídicí/…). PE = žluto‑zelená.
  (Detailní tabulka v příloze; pro konkrétní zakázku ověřit + zákaznickou odchylku — např. JUNKER
  `Aderfarben nach IEC60757`.)

## Objednávání VKM (Verklemmungsmaterial — svorky/vodiče/drobnosti) — ec_id 1094
- Kontrolu VKM provádí **určený pracovník 1× týdně**, přes **čtečku čárových kódů** → požadavek logistice.
- **Objednává se jen ve ČTVRTEK a PÁTEK** (speciální kalkulace; jindy slouží k jiným účelům). Jindy
  jen po domluvě s logistikou. Když je materiálu dost, objednávka nemusí proběhnout.
- **Minimální objednávky u dodavatelů:** LAPP 6 000 · WAGO 2 000 · Harting 2 000 · PHO (Phoenix) 3 000
  · WEI (Weidmüller) 4 000 · Ingomat min 5 položek · Cembre min 5 položek. → výhodné sdružovat položky
  jednoho dodavatele. Řídit se firemním **MIN–MAX**.
- Organizace: regálová řada → pracovník → zástupce.

## (Doplním čtením `@@KBREAD`)
Další jádrová STANDARD témata k destilaci: montáž hlavního vypínače Siemens · dutinky v jističích
řady SIE · kryt přívodní svorkovnice · koncové krytky PE svorky · měděná/mosazná přípojnice (PE/PEN/N)
· FLEXIBAR · dveře – pravidla připojení · balení (UPS) · **odeslání měřicích/zkušebních protokolů,
prohlášení, dokumentace** (výstup dle EN 61439-2). A zákaznická specifika (JUNKER, KOHLBACH).

## Postřehy pro digitalizaci
- Pravidla jsou **parametrická** (průřezy, barvy, MIN-MAX, minimální objednávky) → dají se převést na
  **strojově čitelná pravidla** (kontrola úplnosti, auto-návrh PE průřezu, hlídání minim objednávek).
- VKM objednávání „jen čt/pá kvůli sdílené kalkulaci" = přesně typ procesní tření, které digitalizace
  (vlastní kalkulace + kdykoli) odstraní. Navazuje na SRDCE FIRMY (koeficient→VKM).

— Claude (ID23) 🔧🔌📚
