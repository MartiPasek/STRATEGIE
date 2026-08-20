# MZDY - VELKA ZED: odkud se berou hodiny, co je FPD, svatky, stravenky a priplatky za prescas (Peta 5.8.2026)

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# ⭐ VELKA ZED - PLATI VZDY, PRO VSECHNY INSTANCE

Peta 5.8.2026: *"napis to nekam na velkou zed"* - tahle pravidla se uz nemaji znovu
odvozovat ani dohadovat. Peta je vysvetlovala opakovane (6 hodin veceru 4.8.), tak at je
to naposled.

## 1. ZDROJ HODIN = NASE DOCHAZKA VE STRATEGII

Hodiny pro mzdy se berou z **`tenant.att_den_hodiny(2, od, do)`** (nas vypocet nad
`att_entry` - sluci prekryvajici se useky, odecte pauzy uvnitr prace, doplni fond).
**NIKDY ne ze zrcadla Centraly `tenant.att_day_summary`** - opravy dochazky delame u nas
a do Centraly nedotecou.

Dukaz (7/2026): Svatos mel v zrcadle **123,85 h / 17 dnu**, v nasi dochazce **185,66 h / 23 dnu**.
Pri cteni zrcadla by prisel o 9,66 h prescasu, z toho 7,92 h odpracovanych ve svatek za dvojnasobek.

## 2. FPD (fond pracovni doby) = ODPRACOVANO + ABSENCE

**Vyroba:** FPD = odpracovano + absence (dovolena, nemoc, lekar, OCR... plni fond).
**Kancelar:** FPD = odpracovano + absence + doplneno do fondu - nenarokova cast nad fond.

Prescas = **FPD minus mesicni fond**. Ne "odpracovano minus fond" - to bylo spatne a
Divis (6,02 h odpracovanych ve svatek) by kvuli tomu neddostal priplatek vubec.

## 3. MESICNI FOND = PRACOVNI DNY BEZ SVATKU

Svatek pripadajici na pracovni den se **proplati, ale nema se odpracovat**:
- do mzdy se pripocte, aby byl zaplaceny,
- do **fondu pro prescas NEPATRI**: cervenec 2026 = 22 dnu = **176 h** (ne 184).
Peta: *"tech 8 hodin nemaji odpracovat, to se jim jen zaplati."*

## 4. STRAVENKA ZA SVATEK NENALEZI

Svatek neni odpracovany den. (Do 5.8.2026 se pocitala vsechna Po-Pa, takze za 6.7.2026
dostal stravenku navic uplne kazdy a clovek na materske vysel 1 den misto nuly.)

## 5. PRIPLATKY ZA PRESCAS (Tynka 5.8.2026, procedura EC_Mzdy_PrepocetMesicZam)

| kdy prescas vznikl | koeficient | "nahrazeny" (kryje placene volno) |
|---|---|---|
| svatek | **2,00** | 1,10 |
| vikend (So/Ne) | **1,35** | 0,45 |
| zbytek (bezny den) | **1,25** | 0,35 |

Rozdeleni je KASKADA (jako `EC_GetPrescasyDilna`): nejdriv hodiny odpracovane ve svatek,
pak vikendove, zbytek je bezny den; stejnou kaskadou zvlast cast krytou nahrazenym volnem.
"Nahrazeny" = doplaci se jen rozdil + 0,1 = zadrzne 10 %. Vse jde do slozky **651**.
Historie: koeficient za svatek byl do r. 2023 **2,25**, od te doby **2,00**.

**Plati jen pro VYROBU.** Kancelar (kategorie "Volna kancelarska doba (bez prescasu)",
23 lidi) prescas nedostava - Centrala jim ho jen dopocita do sloupcu, ale nevyplaci.

## 6. KALENDAR SE DOPLNUJE SAM

`kalendar_zajisti` (g2007.python, 5.8.2026) dopocita ceske svatky vc. pohyblivych Velikonoc
(Meeus) do `tenant.firemni_kalendar`. Idempotentni, rucni firemni vyjimky neprepisuje,
**vola se automaticky** ze stravenek i z prescasu -> leden 2027 se doplni sam.

## KDE TO JE V KODU (g2007.python)

- `kalendar_zajisti` - doplneni kalendare.
- `mzdy_stravenky_rows` - pracovni dny z kalendare (svatky ven) + vyloucene cinnosti dle
  cisel z Centraly (att_entry.ec_druh).
- `mzdy_loajalita_rows` - FPD z `att_den_hodiny` (odpracovano + absence), fond z kalendare
  bez svatku, prescas rozdeleny svatek/vikend/zbytek + nahrazeny, konstanty `_KOEF_*`.

## OVERENI (5.8.2026)

Rozdeleni prescasu overeno proti Centrale na **cervnu 2026: 14 z 16 lidi sedi na setiny**
(zbyli 2 jsou kancelar, kterou vylucujeme). Cervenec 2026 po oprave: prescas ma **18 lidi**,
nejvic Civis 16,34 h, Svatos 9,66 h (7,92 ve svatek), Divis 7,94 h (6,02 ve svatek).
Stravenky 61 008 -> 52 398 Kc.

## POJISTKY

`mzdy-hodiny-ze-strategie` - hlida, ze prescas cte att_den_hodiny a kalendar, ne zrcadlo.

