# Docházka má DVA číselníky — druh záznamu a činnost. Nepleť si je (Peťa 25. 8. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Docházka má DVA číselníky. Nepleť si je.

**Zapsáno 25. 8. 2026 po tom, co si je Claude-26 spletl a tvrdil Peti, že „dovolená navíc
u nás není". Je. Jen v tom druhém číselníku.** Peťa: *„udělej vše proto, abychom se k tomu
nemuseli vracet."*

## 1. Číselník DRUHŮ záznamu — `tenant.att_entry_type`

21 položek. To je ten seznam, ze kterého se **vybírá při zadávání** absence ve Správě docházky.
Absence (13): Dovolená · Lékař · Mateřská · Náhradní volno · Nemoc (PN) · Neplacené volno ·
Nepřítomnost OSVČ · OČR · Ostatní/Nepřítomen s náhradou mzdy · Sickday · Volno 70, 80 a 90 procent.
Dál práce, režie, home office, doplnění do fondu, nenároková práce, přestávka, konec dne, cesta.

**„Dovolená navíc" tady NENÍ — a nemá tady být.** V okamžiku zadání se ještě neví, jestli
dovolená navíc bude; rozhodne o tom až pořadí čerpání během roku.

## 2. Číselník ČINNOSTÍ — `tenant.vyroba_cinnost`

Čísla z Centrály (`ec_cislo`), Centrála je autoritativní (Peťa 3. 8. 2026).
20 Dovolená · **30 Dovolená navíc** · 31 Sickday · 34 Ostatní/Nepřítomen s náhradou mzdy ·
10 Nařízené volno · 33 Otcovská · 35 Volno 60 procent · 39 Neplacené volno · 133 Náhradní volno…

**Dovolená navíc TADY JE.** Na záznamu docházky ji drží `att_entry.ec_druh`.

## 3. Kdo se řídí čím

| kde | řídí se | co je vidět |
|---|---|---|
| Správa docházky (zadávání, plán) | druhem | „Dovolená" bez čísla — správně, ještě se neví |
| **Docházka new** (denní záznamy) | **činností** | „20 Dovolená" a „**30 Dovolená navíc**" zvlášť |
| Stravenky (`mzdy_stravenky_rows`) | činností, fallback druh | DN a sick day = stravenka NÁLEŽÍ |
| Nároky a čerpání | činností | D a DN se počítají odděleně |
| **Mzdový podklad** (`mzdy_absence_rows`) | **druhem** ← tady byla chyba | viz níže |

## 4. Chyba, která z toho vznikla (opraveno 25. 8. 2026)

Mzdový podklad seskupoval **podle druhu**. Řádná dovolená i dovolená navíc mají tentýž druh
„Dovolená", takže se **sčítaly do jedné mzdové složky 211**. Přitom dovolená navíc má jít
**jako běžný odpracovaný den** a s dovolenou se sčítat nesmí (Peťa 25. 8. 2026; ověřeno
v Centrále — tam si každá činnost nese vlastní číslo pro mzdy, 20 zůstane 20 a 30 zůstane 30).

Opraveno podmínkou nad `att_entry.ec_druh` v `mzdy_absence_rows`. Hlídá to pojistka
`dovolena-navic-nesmi-do-slozky-211`.

## 5. ⛔ Pravidlo pro příště

**Než prohlásíš, že u docházky nějaký druh nebo činnost „nemáme", podívej se do OBOU číselníků
a do toho, co obrazovka reálně vrací.** Jeden pohled do jedné tabulky nestačí — přesně tím
25. 8. 2026 vzniklo mylné tvrzení, které stálo Peťu čas a důvěru.

Souvisí: `doc-dochazka-dovolena-radna-vs-navic-rozpad` (rozpad, dělení zlomového dne, stravenky),
`doc-dochazka-dovolena-navic-sickday-osvc-do-mezd` (mzdové složky a co do mezd nejde).

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

