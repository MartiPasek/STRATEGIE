# Hlídací pravidla v tenant.pojistka nikdo nespouští — 73 pravidel bez jediného záznamu o běhu (25. 8. 2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Hlídací pravidla v `tenant.pojistka` nikdo nespouští — 73 pravidel bez jediného běhu

Našel Claude-28 **25. 8. 2026** při jiné práci, na pokyn Jirky Honomichla prověřeno do konce.
Vzala na vědomí Marti-AI (msg 13646). **Znalost stav popisuje, nepředepisuje řešení —
rozhodnutí, co s tím, je na Jirkovi.**

## Nález

`tenant.pojistka` obsahuje **73 pravidel, z toho 71 zapnutých**. Psali je Peťa + Claude-26,
Kristý + Claude-24 a další, od 4. 8. 2026 dál.

**Ani jedno nemá vyplněné `posledni_beh` ani `posledni_vysledek`.** Není to tím, že by se
výsledky ukládaly jinam — **pravidla nikdo nespouští.**

## Ověřeno ze čtyř stran (ne odvozeno)

| kde by spouštěč mohl být | výsledek |
|---|---|
| repo (`grep` na `tenant.pojistka` přes `*.py`) | **nic** |
| živý kód `g2007.python` (regulární výraz na `from/join/into/update … pojistka`) | **nic** |
| naplánované automaty `tenant.automat` | jediný záznam je `bank_v1` (bankovní zaúčtování, **vypnutý**) |
| endpoint, který by šlo zavolat (`/pojistky`, `app/pojistk…`) | **neexistuje** |

Tabulka je dnes fakticky **soupis textů**. Pravidlo ožije jen tehdy, když si jeho dotaz někdo
ručně zkopíruje a pustí — typicky Claude přes SQL most při jiné práci.

## Proč na tom záleží

**Nikomu to nemění žádné číslo** — hlídač nepočítá, jen kontroluje. Ale znamená to, že
**rozbitá kontrola se sama neozve.**

Přesně to se stalo **16. 8. 2026**: pojistka `narok-dovolene-pravidla` se opírala o tabulku
`tenant.engagement_entitlement`, která byla ten den smazána při rozpadu dovolené. Pojistka od
té chvíle hlásila **CHYBA KONTROLY** — tedy nespadla tiše do „ztraceno", ale **nehlídala vůbec
nic**, a šlo o nárok na dovolenou, tedy o peníze. Všiml si toho člověk až **o den později**,
náhodou, při jiné práci. Detail: [[doc-dochazka-pojistka-narok-dovolene-po-zruseni-engagement-entitlement]].

Autoři pravidel je přitom psali v dobré víře, že hlídají.

## Co z toho plyne pro práci (do rozhodnutí)

- **Nespoléhej na to, že tě pojistka na něco upozorní.** Když měníš tabulku, na které nějaké
  pravidlo visí, pusť si jeho dotaz **ručně** — před zásahem i po něm.
- **Když rušíš tabulku nebo pohled, projdi `tenant.pojistka`** (`kontrola ILIKE '%%<jméno>%%'`)
  a pravidla přepiš. Jinak se z nich stane CHYBA KONTROLY, kterou nikdo neuvidí.
- **Zelená v minulosti neznamená zelená dnes** — u pravidla, které nikdy neběželo, neznamená
  vůbec nic.

## Otevřené (rozhodne Jirka)

Možnosti, které se nabízejí — žádná zatím nebyla zvolena:
denní automat, který všech 71 pustí a nálezy eskaluje · spuštění na povel z ERP ·
nebo vědomé rozhodnutí, že se pouštějí ručně, a doplnění té informace do popisu pravidel,
aby si nikdo nemyslel, že hlídají sama.

