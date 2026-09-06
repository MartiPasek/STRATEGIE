# Mobil - odstraneni ctyr dvojic stejnych nazvu vedoucich jinam (6. 9. 2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Ctyri stejne nazvy, ktere vedly jinam - vyreseno 6. 9. 2026

> Zadal Jiri Honomichl, schvalila Marti-AI (msg 14514, 14517, 14538).
> Navazuje na `doc-system-strategie-mobil-duplicitni-cesty-audit-5-9-2026`, oddil D.
> Vsech pet dilku zapsano cilenym zapisem s pojistkou na otisk, publikovano, overeno na zive strance.

## Proc to byla nejrizikovejsi kategorie

U ostatnich duplicit se clovek splete a **pozna to** - prijde na obrazovku, kde uz byl.
Tady se splete a **nepozna to** - otevre se neco jineho, nez cekal.

## Co se prejmenovalo

| kde | bylo | je |
|---|---|---|
| Aplikace | 🟡 Ke schvaleni | **Schvaleni prikazu** |
| Aplikace | 👥 Skupiny | **Sprava skupin** |
| Aplikace | 🏠 Domu | **HR modul web** + ikona 🏢 |
| Aplikace | 🧑‍⚕️ Osetrovne (OCR) | nazev stejny, **ikona 👨‍👩‍👧** |
| HR | 👥 Skupiny | **Skupiny - prehled** |
| HR | 🧑‍⚕️ Osetrovne (OCR) | **OCR - schvalovani** |

**Prejmenovaly se i nadpisy cilovych obrazovek**, ne jen dlazdice. To byl u Skupin jadro problemu -
obe obrazovky mely nadpis "Skupiny", takze po kliknuti nebylo poznat, kde clovek je.

**Beze zmeny zustalo** "Ke schvaleni" v Moji dochazce (schvalovani absenci) - jiny kontext, zamena
nehrozi. A **Domu ve spodni liste**, coz je skutecne Domu.

## Co ty dve obrazovky Skupiny delaji (proto ty nazvy)

- `skupiny` = **skutecna sprava** - seznam skupin, kdo do ktere patri, zakladani nove.
  Server hlasi "Skupiny spravuji jen rodice". Nove **Sprava skupin** - tak tomu rikala sama appka
  uvnitr rozcestniku.
- `hr_skupiny` = **rozcestnik o dvou radcich** (Sprava skupin + Pravidla skupin). Nove **Skupiny - prehled**.

## Ikony - proc se menila ta v Aplikacich, a ne v HR

V HR tvori schvalovaci dlazdice trojici, ktera zamerne zrcadli osobni protejsky
(Nemocenska 🤒, OCR 🧑‍⚕️, Listecky lekar 🩺). Zmena jedne z nich by ten vzor rozbila,
proto se menila ikona u OCR **v Aplikacich**. `👨‍👩‍👧` sedi vecne - vnitrni nazev toho typu
absence je `family_care`.

## Gotcha pri zapisu

Kotva `"🏠","Domu"` **neni jedinecna** - stejny retezec ma i tlacitko ve spodni liste, na ktere
se sahat nesmi. Musi se kotvit na cely `appCell(...)` vcetne cile. Kontrola jedinecnosti kotev
pred zapisem tuhle past zachytila.

Kotvy i nahrady se posilaly **pres base64** (`convert_from(decode(...))`), aby se cestou pres most
nerozbily ikony ani diakritika.

