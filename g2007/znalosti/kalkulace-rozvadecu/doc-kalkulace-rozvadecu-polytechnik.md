# 🏭 Zákazník Polytechnik — profil, model spolupráce a případ PolyClean (EN263390)

> oblast: `kalkulace-rozvadecu` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# 🏭 Zákazník Polytechnik — profil, model spolupráce a případ PolyClean (EN263390)

**Oblast:** kalkulace‑rozvaděčů · **Zapsal:** Claude‑26 (Marti), 20. 7. 2026
**Typ:** zákaznický modul. Navazuje na `doc-carkovani-plan-kalkulace`, `doc-srdce-firmy-kalkulace-nabidky-analyza`, `doc-kalkulace-standard-struktura`.

## 1. Kdo je Polytechnik
**POLYTECHNIK Luft- und Feuerungstechnik GmbH** — rakouský výrobce technologií pro
spalování biomasy („Transforming Biomass", od 1965).
- Sídlo: Hainfelderstraße 69, A‑2564 Weißenbach an der Triesting.
- FN 194342y · UID **ATU49304006** · office@polytechnik.at · www.polytechnik.com.
- Segment: kotelny/spalovací a vzduchotechnika (termoolejové kotle, biomasa).

**Model spolupráce:** Polytechnik je **OEM / stavitel technologie**; koncová místa jsou
jeho zákazníci (např. **PUP Complex sp. z o.o.**, ul. Kościuszki 7/9, 80‑451 Gdaňsk, PL).
Polytechnik navrhne **EPLAN schéma**, **EUROSOFT‑Control staví rozváděče** (Schaltschränke)
a kalkuluje/nabízí. My tedy nekreslíme, stavíme a naceňujeme.

## 2. Kontakty
- **Zákazník:** Reinhard **Brandl** — `r.brandl@polytechnik.at`, Automatisierungstechnik /
  Abt.‑Leiter Stv. (zástupce vedoucího automatizace). CC bývá Matthias **Brenner**
  `m.brenner@polytechnik.at`.
- **Naše strana:** Radek **Hellmayer** — vedoucí projektu, EUROSOFT‑Control,
  `r.hellmayer@eurosoft.com`, tel. 773 738 581.

## 3. ⚠️ Klíčové obchodní pravidlo — Siemens = Beistellung
**Polytechnik si díly Siemens dodává SÁM.** Doslova z poptávky (Brandl, 16. 7. 2026):
*„In diesem Fall stellen wir die Siemensteile bei."* → V kusovníku jsou označené
`Beistellung Polytechnik` a **nesmí vstoupit do naší nabídkové ceny** — jen se vykazují.
Ověřeno: v Complex kusovníku, ve vestavěné Stückliste EPLANu (SIE = 0,00) i v kalkulaci
(dodavatel „Beistellung" = cena 0). **Pozor:** Siemens tvoří i ~80 % nákupní sumy skříně
(BJY30: ~2 112 z 2 666) — kdyby se omylem nacenil, nabídka je úplně mimo.

## 4. Podoba dokumentace Polytechniku (na co si zvyknout)
- **EPLAN P8** export (zde V3.2). Struktura `+BJYxx` = jedna skříň (Schrank).
- **Vestavěná `Artikelsummenstückliste`** na konci PDF (formulář F02) = strojově blízký
  kusovník; Radek z něj kopíruje `Complex_Artikelsummenstückliste_*.xls` do kalkulace.
- ⚠️ **EPLAN PDF nemá textovou vrstvu** (vektor/obraz) → strojově čitelný je až ten
  `.xls` kusovník, ne PDF. Z PDF jen OCR/vision.
- **Kódy výrobců v kusovníku:** `ALB`=Allen‑Bradley/Rockwell (Polytechnik ho používá
  masivně — ovládání, jističe, svorky!), `SIE`=Siemens (beistellt), `RIT`=Rittal
  (skříně/chlazení), `FIN`=Finder, `EAT`=Eaton, `PHO`=Phoenix, `SCHR`=Schrack,
  `KEY`=Keyence, `TUR`=Turck, `DUMMY`=zástupná položka bez reálného obj. čísla.
- Ceny v kusovníku k `Preisdatum` — ověřovat aktuálnost.

## 5. Referenční případ — PolyClean / EN263390 (Thermoöl 5500 kW)
- **Poptávka EP26302** (jádro 3) → **nabídka EN263390** (jádro 88), kalkulace `EK263390`.
  Projekt „Complex / Thermoöl 5500 kW", EPLAN Projektnr. 00000718, Auftrag V22008.
- **Termínová urgence:** Brandl žádal kapacitu na stavbu ve **KW33–34**; **správný E‑Plan
  až v KW32** (tahle V3.2 je předběžná, „der Aufbau wird aber ziemlich gleich sein").
- **Dvě funkčně různé skříně** (ne kopie!):
  - **BJY30 = hlavní řídicí skříň** — CPU `6ES7512‑1SK01` (1512SP F‑1, fail‑safe),
    SITOP zdroj, PROFIBUS CM, ovládání (START/STOP/NOT‑HALT, signálky), jištění motorů,
    filtrační ventilátory. ~68 položek kusovníku.
  - **BJY31 = decentrální I/O skříň** — kompakt Rittal `AX.1050000` + **aktivní chlazení**
    `SK 3302.100`, PROFIBUS `IM 155‑6DP`, AI moduly `6ES7134` (proud + RTD/TC teploty),
    signální maják `856T`, Keyence světelná závora, PT100. ~53 položek.
- Společných jen 26 typů (svorky, varistory, generické díly).

## 6. Adresář dokladů v Centrále (kde soubory jsou)
- Poptávka: `D:\Data\poptavky\EP26302` — příchozí `dringende Anfrage PolyClean.msg`
  (Brandl → Hellmayer, cc Brenner), EPLAN PDF, oba Complex kusovníky.
- Nabídka: `D:\Data\nabidky\EN263390` — kalkulace `EK263390_PolyClean_RH_260720.xlsx`,
  Complex kusovníky, podsložka `Jednotlivé kusovníky\BJY30.xlsx|BJY31.xlsx`.
  (Kalkulace EK sdílí adresář nabídky — viz `doc-go-adresar_ec_orgadresare`.)

## 7. Nálezy z ověření úplnosti (EPLAN ↔ kusovník)
`.xls` kusovník je věrný export vestavěné `Artikelsummenstückliste` EPLANu — koncové
položky (RIT Kühlgerät, SCHR jističe, SIE ET200SP, STM dioda) sedí 1:1. Kalkulace na
vstupu nic nevynechala. Reziduální riziko = **předběžný EPLAN** (finál KW32).

## 7b. Ověření A — výsledek kalkulace EK263390 (hotovo 20. 7. 2026)
Kalkulace `EK263390_PolyClean_RH_260720.xlsx` = kopie STANDARDu (listy `BJY30 OBJ`,
`BJY31 OBJ`, `Souhrn`, ` Souhrn BEI SIE`). Ověřeno:
- **Beistellung/Siemens se nenacení — mechanismus funguje.** V `BJY30 OBJ` je 13 položek
  s dodavatelem „Beistellung" a cenou **0,00** (= Siemens od zákazníka, mimo naši cenu). ✓
- **BJY30 (hotová):** 72 položek, materiál **819,51 €**, instalovaná cena **1 886 €**, **24 h**.
- **BJY31 (rozpracovaná) — konkrétní mezery:**
  1. Naceněno jen **36 z 53** položek kusovníku (~17 chybí).
  2. **Chybí chladička Rittal `SK 3302.100` (~1 250 €)** — ve STANDARDu je (řádky ~204–212),
     Stückzahl prázdný → BJY31 podhodnocená. Místo Rittal AX je v kalkulaci Eldon (180,94 €).
  3. Beistellung Siemens označeno jen **7 z 10**.
  4. `DUMMY` bez obj. čísla: PT100/2‑Leiter, 100 µF/63 V, 2200 µF/100 V, FST5,0H.
- **List `Souhrn` je stále ze šablony** (`#REF!`, odkazy na cizí skříně BJY11/13/14/18/21‑26)
  → předrátovat na BJY30/BJY31, aby dal celkovou cenu.
- Drobnost: 1 Siemens položka `ET 200SP server modul` (26,04 €) je naceněná (ne Beistellung).

**Punch‑list pro Radka** (dle dopadu na cenu): chladička ~1 250 € → sjednotit skříň →
dorovnat 17 položek → 3× Beistellung Siemens → DUMMY → Souhrn. (Soubor
`BJY31_punchlist_EN263390.md`, 20. 7. 2026.)

## 8. Poznámky do budoucna
- Polytechnik = **opakovaný typ zakázky** (rozváděče k biomasovým technologiím, EPLAN +
  Beistellung Siemens). Vyplatí se mít na něj v kalkulačním enginu připravený vzor
  (STANDARD) a rabatový profil per CisloOrg.
- Vždy hlídat: (1) Siemens = beistellt (vyloučit z ceny), (2) předběžný vs finální EPLAN,
  (3) DUMMY položky dořešit před nabídkou, (4) při kopii STANDARDu předrátovat Souhrn.


