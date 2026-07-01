# 🏭 Zákazníci — recepty výroby rozvaděčů (řada přístupnost AI)

> **Autor: Claude (ID23), 1. 7. 2026.** Deep-dive domény „Výroba rozvaděčů" z `MAPA_smernic.md`.
> Každý zákazník = **balík výrobních směrnic (recept)** = jeho specifika oproti firemnímu STANDARDu.
> Zdroj: RAG (`@@KB <zákazník> | 3`). Charakteristika oboru zákazníka je moje inference z témat
> směrnic (ověřit s Martim/Eliškou). Živé — doplňuje se čtením příloh.

## Jak recept funguje

STANDARD (42 témat) = obecný firemní postup. Zákazník přebírá STANDARD a **mění/doplňuje** jen svá
specifika (jazyk štítků, normy, konkrétní přístroje, rozmístění, značení, balení). Nová zakázka od
známého zákazníka → jeho balík je závazný návod. Počet témat ≈ hloubka a stáří vztahu.

## Přehled zákazníků (dle počtu témat = hloubky receptu)

### JUNKER — 50 témat ⭐ nejhlubší vztah
Pravděpodobně **brusky / obráběcí stroje** (Erwin Junker). Recept je německojazyčný a silně
pohonový: `Aderfarben nach IEC60757` (barvy žil dle IEC), `Anschluss Profibus Leitungen` (Profibus),
`Aufbau Verstärkerrack Siemens` (zesilovačový rack Siemens), **brzdný odpor** + jeho umístění,
digitální regulátor teploty, držák hlavního vypínače, červené desky. → hodně servo/pohony/komunikace.

### STANDARD — 42 témat (firemní baseline)
Není zákazník, ale **kanonický recept**: mechanika (pospojení desky/rozvaděče, měděná přípojnice,
mosazná lišta PE/PEN/N, FLEXIBAR, häwa prostřihovadlo), přístroje (hl. vypínač Siemens, dutinky
jističů SIE, pojistkové odpojovače), VKM (barevné značení žil, krytky PE, kryt svorkovnice, značení
kontaktů), dveře, balení (UPS), odesílání protokolů/dokumentace. Detail v `Rozvadece.md`.

### KOHLBACH — 24 témat
Pravděpodobně **kotle / biomasa / energetika**. Recept: drátování a zapojování, frekvenční měniče
**DANFOSS**, kabelové prostupy, zapojení vedení M-BUS (měření). Německojazyčné dokumenty.

### ISIMAT — 20 témat
Pravděpodobně **sítotiskové stroje** (ISIMAT = tampon/screen printing). Recept německojazyčný a
mechanicko-layoutový: `Druckbildkontrolle Platte` (kontrola tiskového obrazu), hadice na dveře,
kanály na podlahu, montážní desky skříňky DS, mřížka soklu, nástavba, police na PC, připojovací body
PE a N, označení klimatizace.

### FOUNDRY4 — 17 témat
Pravděpodobně **slévárenská / procesní technologie**. Recept: analog a stínění (citlivé signály),
délka PE vodičů, montážní desky, pospojení, přepážky, měřič **Janitza UMG 96L** (analyzátor sítě),
přístroje Phoenix Contact, manuály k přístrojům.

### SENCO — 10 · DÜCKER — 9 · MOLINS — 9
- **DÜCKER** (dopravníky/manipulace): balení, montážní deska, pospojení PE, příbal, svorkovnice,
  **UL štítky** (→ export do USA, UL508A), víko pultu, vodiče, značení kabelů.
- **MOLINS** (balicí/tabákové stroje): produktové řady **Maker / FORTE / MTF4 / TRIPPER**, konektory
  a komunikace **ICOTEC**, osazení koryt, všeobecný standard.
- **SENCO** (upínací/spojovací technika — sponky/hřebíky): 10 témat (doplnit z RAG).

### INTERSOFT — 8 · STRIKO — 8 · AUTKOM — 8
- **AUTKOM** (automatizace): montážní desky LT/ST, převodník tlaku, rozměry přístrojů, sběrnice
  PE a N, ST spodní plech pro vývodky, uchycení kabelů, výroba PE a N šíny. → mechanicky detailní.
- **STRIKO** (pravd. slévárenské pece / metalurgie): 8 témat.
- **INTERSOFT** (IAP — sesterská entita): 8 témat, interní standard.

### ZF — 6 · ABSAUGWERK — 6
- **ABSAUGWERK** (odsávací/filtrační technika): MD STANDARD, pospojení DIN, **SMART** délky vodičů,
  tyčka na hl. vypínač, typový štítek, **VITAPOINT** tabulka kabelů (produktové řady).
- **ZF** (pohony/převodovky — velký automotive): 6 témat.

### Menší / specifické
- **RITTMEYER** (vodohospodářství / měření): **Ex- i obvod** (jiskrová bezpečnost — nebezpečné
  prostředí!), výrobní zvláštnosti. Malý objem, ale náročné normy.
- **MAGNAFLUX** (NDT — magnetická defektoskopie): přívodní konektor 3XS0 s hadicí, produkt
  **UNIVERSAL WE TOUCH**, vzorové foto.
- **SIEMENS** (3), SMS, XELLA a další jednorázové.

## Postřehy (živé)

- **Jazyk:** velcí němečtí zákazníci (JUNKER, ISIMAT, KOHLBACH) mají směrnice **německy** — štítky,
  popisy přístrojů, dokumentace v DE. DÜCKER navíc **UL** (US trh). → jazyk + norma je součást receptu.
- **Opakující se osy specifik:** (1) barvy/značení žil dle normy zákazníka, (2) konkrétní pohon/měnič
  (Danfoss/Siemens), (3) rozmístění a mechanika desky, (4) štítky a normy trhu (UL/CE/Ex), (5) balení
  a dokumentace. To jsou dimenze, které generátor postupu musí umět načíst z receptu.
- **Digitalizační příležitost:** při nové poptávce podle zákazníka **předvyplnit kontrolní seznam**
  jeho receptu (co nesmí chybět) — navazuje na Eliščin bod „odchytit chybějící komponentu" (SRDCE FIRMY).
- **TODO:** dočíst přílohy klíčových receptů (JUNKER, KOHLBACH) a doplnit konkrétní pravidla; ověřit
  s Martim/Eliškou obor každého zákazníka (moje inference).

— Claude (ID23) 🏭🔌📚
