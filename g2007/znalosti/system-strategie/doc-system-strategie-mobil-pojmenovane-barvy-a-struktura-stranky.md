# Mobil - pojmenovane barvy pro tlacitka a odznaky, a past s tmavym textem na zelene

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Mobilní appka — pojmenované barvy a struktura stránky (stav k 2. 9. 2026)

**Vzniklo 1.–2. 9. 2026** při plošné opravě kontrastu (zadal Jirka Honomichl, schválila Marti-AI).
Kdo bude appku dělat dál, tohle musí vědět — jinak si nechtěně vyrobí neviditelné tlačítko
nebo znovu zavede odstín, který jsme právě odstranili.

## Čtyři nové pojmenované barvy v 02_styles.html

| proměnná | hodnota | k čemu | kontrast |
|---|---|---|---|
| --on-green | #04150e | text na zelené ploše | 7,40 : 1 |
| --blue-nav | #9fc4ff | zvýrazněná položka spodní lišty | 7,70 : 1 |
| --badge | #c62828 | všechny odznaky (puntíky s číslem) | 5,62 : 1 |
| --btn | #2563eb | pozadí základního tlačítka a vybraného filtru | 5,17 : 1 |

**Používej je, nepiš barvy natvrdo.** Původní hodnoty byly pod normou:
bílá na zelené 2,11 · zvýraznění lišty 4,27 · odznaky 1,92 až 3,93 · modré tlačítko 3,21.

Proměnná --blue (#4f8ef7) **zůstala beze změny** — používá se na odkazy a tam má kontrast
v pořádku. Neměň ji.

## PAST: zelené tlačítko má nově tmavý text

Pravidlo je dnes: třída green nastavuje pozadí na zelenou a barvu textu na --on-green.

**Kdo udělá zelené tlačítko a přebarví mu pozadí na jinou barvu, musí mu dát i vlastní barvu
textu** — jinak zdědí tmavou a text na tmavém pozadí zmizí. Jeden takový případ v appce už byl
(tlačítko Zamítnout s červeným pozadím) a je ošetřený inline. Marti-AI k tomu řekla: až přibude
druhý takový případ, patří to vyřešit třídou, ne dalším inline stylem.

## Odznaky: jedna červená, ale pozor na výjimku

Všechny čtyři třídy odznaků (nbadge, appbadge, rbadge, vybadge) berou barvu z --badge.
Sedm dalších odznaků bylo psaných úplně natvrdo bez třídy — ty jsou srovnané taky.

**Zelená varianta vybadge (třída gr) zůstává zelená s tmavým textem** — to není notifikační
odznak, ale stavový příznak hotovo ve Výrobě. Překlopení na červenou by převrátilo význam.
Nesjednocovat.

## Struktura stránky se změnila

- Kořenový prvek appky byl div a je z něj nově main — stránka konečně má hlavní oblast.
- Funkce topbar vrací nadpis obrazovky jako h1. Když je nadpis prázdný (docházka ho má
  prázdný záměrně), vrací vizuálně skrytý h1 s textem STRATEGIE Mobil.
- Přibyla třída skryty pro text jen pro čtečky. Obrazovky Domů a Firma, které nepoužívají
  topbar, mají skrytý nadpis vložený na začátku.
- Třída title dostala nulový okraj — h1 má výchozí okraje, span je neměl.

**Kdo bude dělat novou obrazovku:** použij topbar a nemusíš řešit nic. Když si hlavičku kreslíš
sám, přidej na začátek skrytý h1 s názvem obrazovky.

## Dotykové terčíky

Tlačítka přes celou šířku mají minimální výšku 48 px. Norma doporučuje 44 px jako minimum
pro prst; u nových tlačítek a polí to drž.

## Sjednocení odstínů — kde je hranice

Barev bylo 302, sloučením neviditelných dvojníků jich je 262; velikostí písma bylo 36, je 29;
poloměrů rohů bylo 19, je 12. **Slučovalo se jen to, co je v RGB vzdálené nejvýš 3**
(u rohů 1 px, u písma půlpixely) — tam rozdíl nemůže být záměr.

**Zbylé dvojice ve vzdálenosti 4 až 8 se slučovat NESMÍ bez ověření**, jestli obě barvy nejsou
přiřazeny prvkům ve vztahu kontejner a jeho obsah. Karta o odstín světlejší než pozadí za ní
je legitimní návrh; sloučením by hranice mezi vrstvami zmizela.

## Související

- [[doc-system-strategie-audit-vzhledu-mobilni-appky-postup]] — čím se vzhled měří a jak to pustit bezpečně
- [[doc-system-strategie-mereni-kontrastu-axe-kratke-texty-demo-ucet]] — proč nástroj mlčí u odznaků
- [[doc-system-strategie-mobil-kde-se-edituje-a-jak-se-nasazuje]] — kde obsah appky žije

