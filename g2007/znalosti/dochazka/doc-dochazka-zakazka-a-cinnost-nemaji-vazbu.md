# Zakázka a činnost nemají vazbu — 1046 a 1047 jsou dva SEZNAMY, ne dvě škatulky (Peťa 27. 8. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Zakázka a činnost nemají vazbu

**27. 8. 2026, ověřeno přímo v Centrále na pokyn Peti.** Zapsáno proto, že si to systém
sám vymyslel a stálo to 91 hodin bez činnosti.

## Pravidlo (Peťa)
Zakázka je **VR / PR / SW + číslo**, plus zakázka **Rezie** (bez háčku).
Činnosti jsou samostatný seznam. **Jakákoli zakázka + jakákoli činnost.**
Žádné omezení, které by říkalo „tuhle činnost jen k téhle zakázce", neexistuje.

**REŽIE s háčkem není nic a nemá se nikdy používat.** `Rezie` bez háčku je ZAKÁZKA,
ne činnost (Peťa + Marti 20. 7. 2026; činnost „Režie" id 14 byla omyl, 3. 8. archivována).

## Co je v Centrále (ověřeno v DB_EC)
Číselník činností je rozdělený do **dvou přehledů**:

| Přehled | Název | Tabulka | Položek |
|---|---|---|---|
| **1046** | Docházka – činnosti – **režie** | `EC_Dochazka_CinnostiRezie` | 32 (čísla 101–138, 999) |
| **1047** | Docházka – činnosti – **dílna** | `EC_DilnaCinnosti` | 76 |

Jsou to **dva seznamy, ne dvě škatulky na zakázky.** Ani jedna tabulka nemá sloupec,
který by činnost vázal na zakázku. (`EC_Dochazka_CinnostiRezie.Zakazka` existuje,
ale je u všech 32 položek prázdný.)

## Důkaz z provozu (EC_Dochazka, rok 2026)
| Zakázka | Záznamů | z toho 1046 režie | z toho 1047 dílna |
|---|---:|---:|---:|
| VR (229 zakázek) | 12 878 | 20 | 12 858 |
| **Rezie** | 7 386 | **3 287** | **4 099** |
| PR (13 zakázek) | 285 | 26 | 259 |

Na zakázce Rezie se používají **oba seznamy** a dílenských je tam dokonce víc.
Na VR se objevují i režijní. Míchá se to volně.

## Jak to bylo u nás
`tenant.vyroba_cinnost.kind` (`standard` / `rezie` / `nepritomnost`) **kopíruje ten
centrálský rozdíl 1046/1047 správně** — s tím rozdílem, že absence jsou u nás vytažené
zvlášť do `nepritomnost`. Počty: 19 standard (17 aktivních) · 33 rezie (30) · 28
nepřítomností. Pracovních je tedy 47 aktivních.

**Chyba nebyla v dělení seznamu, ale v tom, že z něj kód udělal omezení výběru:**
- nabídka činností (`app_vyroba_my_cinnosti`) vrací **jednu skupinu podle parametru**,
  mobilní appka si ji volí sama podle zakázky (`71_plan_prace_cinnosti.js` ~ř. 1006:
  `rez ? "rezie" : "standard"`),
- paměť poslední činnosti při výběru zakázky brala jen `kind='standard'` (viz
  [[doc-dochazka-cinnost-se-nesmi-mazat-pri-vyberu-zakazky]]).

## Stav opravy k 27. 8. 2026
- `app_vyroba_my_cinnosti` umí nově `kind='prace'` = **obě pracovní skupiny naráz**;
  `standard`/`rezie` zůstávají kvůli správě číselníku (dvě záložky). **Zpětně
  kompatibilní — dokud appka nepošle `kind=prace`, nic se nemění.**
- **Zbývá:** mobilní appka má přestat volit skupinu a žádat si `kind=prace`.
  Nenasazeno 27. 8. — v souboru souběžně pracoval C28.

## Pravidlo pro příště
Než prohlásíš, že nějaká činnost k nějaké zakázce „nepatří", **podívej se do Centrály,
co se tam reálně páruje.** Rozdělení číselníku do dvou přehledů je způsob zobrazení,
ne omezení.

Souvisí: [[doc-dochazka-dva-ciselniky-druh-zaznamu-vs-cinnost]] · [[doc-dochazka-cinnosti-ciselnik-centrala-vs-strategie]]

---

## ⛔ ID NENÍ ČÍSLO ČINNOSTI (Peťa 4. 9. 2026, ZÁVAZNÉ)

Peťa: *„ID a číslo činnosti jsou dvě naprosto rozdílné věci. ID nás nezajímá — to vás zajímá
někde na pozadí, ale pořád jsou to dvě rozdílné věci."*

Když se mluví o čísle činnosti, platí **VÝHRADNĚ** `tenant.vyroba_cinnost.ec_cislo` (u nás)
a sloupec `Cislo` (v Centrále). Interní `id` je technika na pozadí a **nikdy** se za číslo
činnosti nevydává — ani v hlídači, ani v dotazu, ani v řeči s Peťou.

Živý příklad: služební cesta je **činnost 9**, ale její `id` je 16. Pod `id = 9` sedí u nás
Značení vodičů a v Centrále dokonce Nemoc.

**Mapa všech číselníků, které se dají zaměnit — včetně těch, do kterých se dívat NEMÁ:**
`doc-dochazka-cinnosti-ciselnik-centrala-vs-strategie`.

