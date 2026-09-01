# Sick days: vedou se ve DNECH, čerpá se po hodinách, nárok v hodinách = čerpáno + zbývá (oprava pro změnu úvazku během roku, 1. 9. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

**Peťa, 1. 9. 2026.** Peťa: *„má nárok na 2 dny = 16 hodin, vzala si jeden den 8 hodin,
zbylo jí 8 hodin přepočteno na den 1 den. Pak se jí změnil úvazek, ale měla 1 den, tedy
7 hodin, a ty si teď chce vzít — měla by vyčerpáno 8 a 7, tedy 15."*

## Pravidlo

**Nárok a zbytek se vedou ve DNECH. Čerpat se dá po hodinách. Hodiny zbytku se
dopočítávají až na výstupu z aktuálního denního fondu.**

Za rok tedy člověk se změnou úvazku vyčerpá jiný počet hodin, než kolik mu vyšlo
na začátku roku — a je to správně. Dva dny nároku u Duspivové = 8 h (duben) + 7 h
(září) = 15 h za rok.

## Co bylo špatně (do 1. 9. 2026)

Dovolená se počítala ve dnech správně, **sick days jako jediné v hodinách**:

    narok_h = pocet_dnu * dnesni_fond
    zbyva_h = narok_h - vycerpane_hodiny

Kdo měl během roku jiný úvazek, o zbytek přicházel. **Duspivová (os. č. 50):**
nárok 2 dny, v dubnu vyčerpala 1 den = 8 h (tehdy 8h den), od 1. 7. má 7h den →
starý výpočet (2 × 7) − 8 = **6 h** místo správného 1 dne = **7 h**.

## Nárok v hodinách NENÍ pevné číslo — dopočítává se (Peťa 1. 9. 2026)

Peťa: *„za mě by měl být nárok 15"* a *„nejen to tam napsat, ale aby to vycházelo
z logiky počítání."*

Prostý převod „počet dnů × dnešní fond" u člověka se změnou úvazku **nesedí ani sám
se sebou**: Duspivové vyšel nárok 14 h, přitom za své 2 dny nároku vyčerpala 15 h —
vypadalo to, že nárok překročila, i když měla přesně dva dny.

**Nárok v hodinách se proto nepočítá samostatným vzorcem, ale skládá se z částí řádku:**

    narok_h = cerpano_h + zbyva_h

kde `cerpano_h` jsou skutečně vybrané hodiny (každý den svým tehdejším fondem) a
`zbyva_h` je zbytek ve dnech × dnešní fond. Řádek tak vždycky sedí a hodinu si nikde
nevymýšlíme.

- **Duspivová:** 8 h (duben, 8h den) + 7 h (září, 7h den) = **15 h**
- **Kdo úvazek neměnil** (Šafránková): 8 + 8 = **16 h**, tedy stejně jako dřív

**Vedoucí jednotkou zůstávají DNY.** Hodiny jsou vždycky jen dopočet — u vybraných dnů
z fondu, který platil tehdy, u zbytku z dnešního.

## Oprava (nasazeno 1. 9. 2026, `att_narok_cerpani`)

CTE `cerp` počítalo dny (hodiny ÷ fond **platný k datu záznamu**) už dřív, jen se
pro sick days nebraly — používaly se jen hodiny. Nově:

    sd_cerp_dny  = suma(hodiny / fond k datu zaznamu)
    sd_zbyva_dny = narok_dny - sd_cerp_dny
    sd_zbyva_h   = sd_zbyva_dny * dnesni_fond

Čerpání se dál ukazuje ve skutečných hodinách (SD se čerpá po hodinách).

**Přehled Nárok a čerpání ukazuje u sick days OBĚ jednotky vedle sebe** (Peťa: *„aby
tam byla vidět ta logika, kterou jsem vymyslela — vzájemně se to přepočítává"*):
nárok dny · nárok h · čerp. dny · čerp. h · zbývá dny · zbývá h · naplán. dny ·
naplán. h · zbývá po dny · zbývá po h.

## Ověřeno naostro

Duspivová po opravě: fond 7 h · nárok 2 dny = 14 h · čerpáno 8 h = 1,00 dne ·
**zbývá 1,00 dne = 7,00 h** (dřív 6,00 h). Přes `att_narok_osoba`:
`{"narok_h": 14.0, "cerpano_h": 8.0, "zbyva_h": 7.0}`.

Komu se úvazek neměnil, tomu se nezměnilo nic — Šafránková: nárok 16 h, čerpáno 8 h,
zbývá 8 h.

## Souvislosti

- `doc-dochazka-narok-dovolena-sick-days-jeden-zdroj-pravdy` — nárok žije v Podmínkách
- `att_narok_osoba` je jediné místo, odkud si žádosti berou zbývající nárok — bere
  data z `att_narok_cerpani`, takže oprava platí i pro kontrolu při podání žádosti.

