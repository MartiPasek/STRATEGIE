# JMHZ — stav a co zbývá dotáhnout

> Znalostní karta k Jednotnému měsíčnímu hlášení zaměstnavatele (ČSSZ, povinné od 1. 4. 2026).
> Modul: `modules/erp/api/mzdy_jmhz.py` (generace z cloud Heliosu + ověření u ČSSZ), tlačítko
> 🏛️ JMHZ → ČSSZ na Výplatnici. Zpracováno 12. 7. 2026 (Claude ID23). **Dotáhnout příští týden.**

## Co je HOTOVÉ a ověřené (červen 2026)

- **BOD 1 — identifikátory:** reálné IK MPSV + ID PPV z Heliosu (`TabMzJmhzPP`, poslední měsíc, primární PPV). Pro červen mají **všichni reálné** (ES 33/33, EC 17/17, žádný placeholder).
- **BOD 2 — OČR/absence (ošetřovné):** `attach_absence` tahá schválené OČR z `tenant.att_ocr_case`, páruje na osobu přes `att_employee.cislo_zam` == Helios číslo, doplní vyloučené + odečitatelné dny a neodpracované hodiny. Kristý (ES č. 21, 23.–28. 6., 4 dny / 32 h) integrováno a ověřeno u ČSSZ (VysledekKod OK).
- **BOD 3 — daně a čistá:** berou se reálně z Heliosu (`TabZamVyp`, `helios_ready`), takže čistá mzda sedí 1:1 včetně slev na děti. Sleva poplatníka + prohlášení z `TabMzJmhzPP`.
- **VS zaměstnavatele u ČSSZ:** EC = „EUROSOFT - Control" = **4445158191**, ES = „EUROSOFT - System" = **4442058998** (nahradilo placeholder z pilotu). Stejný VS = klíč pro automatické stahování notifikací k nemocenské/OČR (eNeschopenka).
- **Ověření:** celý červen prošel ČSSZ TEST validátorem — 50/50 osob + OČR OK.

## Reconciliace proti Heliosu (po updatu Heliosu, 12. 7. večer)

Marti po updatu Heliosu vygeneroval JMHZ přímo z Heliosu (modul Mzdy → JMHZ, tabulky `TabMzJmhz` / `TabMzJmhzPP`, podání ID=4 pro EC i ES, Rok 2026 Měsíc 6, typ Řádné, stav „Pořízeno" = neodesláno). Porovnáno s naším generátorem:

- **Počet osob sedí:** Helios `TabMzJmhzPP` = **EC 17 / ES 33** = náš generátor. (Přehledová hlavička hlásí 19/35 — to je počet formulářů = osoby + souhrn + PVPOJ, ne lidé. Domněnka „dohody DPP/DPČ" vyvrácena: `TabMzHlaseniDohod` má ES 0 řádků.)
- **Identifikátory 50/50 IDENTICKÉ:** náš generátor dává pro všech 50 lidí byte-shodné IK MPSV i ID PPV jako Heliosovo podání (0 neshod, ověřeno skriptem proti per-osoba exportu „HEO – JMHZ – pracovní poměry").
- **Heliosova vlastní validace = 0 chyb** u všech 50 (Kód chyby i N.ch. = 0, `TabMzJMHZPPErr` prázdná). Všichni „Bez příznaku", „Řádné". IK MPSV všech 50 správně 10-místné.
- **Payload dávky (XML `<n1:jmhz>`) Helios v DB nedrží** — staví ho až při zápisu na disk. Uploadované soubory „HEO – Jednotné měsíční hlášení" i „…pracovní poměry" jsou přehledové gridy (`<CACHE>`), ne payload. Na plnou obsahovou kontrolu přes `@@EPVAL` (částky) je potřeba soubor dávky, co Helios zapíše na disk při přípravě k odeslání.

## Co SCHÁZÍ / rizika (dotáhnout příští týden)

1. **BOD 4 — speciální pojistné vztahy (největší díra).** Generátor teď každého pošle jako standardního zaměstnance s plným měsícem pojištění a plným fondem. Reálně:
   - **Šafránková — mateřská dovolená** = vyloučená doba, ne odpracovaný měsíc. I když XSD projde, je to sémanticky špatně (měla by mít mateřskou jako vyloučenou dobu, ne fond 160 h / 30 dní).
   - **Herejtová, Senft — srážková daň** (prohlášení = 0): částky z Heliosu jsou správné, ale typ vztahu (DPP/DPČ?) se nerozlišuje.
   → Doplnit rozpoznání typu vztahu a mateřské/DPP do formuláře.
   → POZN. z reconciliace 12.7.: Helios sám vede Šafránkovou/Herejtovou/Senfta jako „Bez příznaku" s 0 chybami — takže díra může být menší, než se zdálo. Ověřit, jestli Helios mateřskou/srážkovou řeší uvnitř formuláře (vyloučené doby), a případně to dorovnat u nás.

2. **⚠️ Dvě krátká ID PPV v EC (dořešit před ostrým podáním).** V Heliosím podání i u nás (bereme ze stejné tabulky) mají dva lidé ID PPV, které nemá 13 číslic:
   - **Pašek, os. č. 2:** `400276552758` (12 číslic; jeho ES záznam má správné 13-místné `4002992990225`).
   - **Peřina, os. č. 536:** `9279914` (7 číslic; nový zaměstnanec — identifikátor zaměstnání zřejmě ještě není plně přiřazený).
   Helios u nich hlásí 0 chyb, ale formát je kratší než u ostatních → ověřit registraci PPV u ČSSZ, jinak riziko odmítnutí při ostrém podání. Ostatních 48 má ID PPV správně 13-místné.

2. **Absence mimo OČR se nepromítají.** `attach_absence` řeší zatím jen ošetřovné. **Nemoc, mateřská, dovolená** vytvářejí taky vyloučené doby v ELDP — teď se do JMHZ nedostanou. → Projít, kdo měl v červnu jakou absenci, a napojit i tyto druhy.

3. **OČR párování přes `cislo_zam` == Helios číslo.** U Kristý sedí (21 = 21). Kdyby příště měl OČR někdo, komu se docházkové číslo liší od Helios čísla, párování **tiše mine** (OČR se neukáže, bez chyby). → Zpevnit párování (přes user_id / mapovací tabulku), ne jen shodu čísel.

4. **Sandbox „OK" ≠ přijato v produkci.** Vše ověřené proti ČSSZ **TEST** validátoru — ten hlídá jen strukturu (XSD) a základní pravidla, **neověřuje, že částky sedí na realitu ani že IK MPSV jsou skutečně registrované.** Ostré podání jde ručně přes ePortál/datovku a je **regulatorně na Peťe/vedení** (AI za vás podat nemůže).

5. **Finální uzavřené mzdy.** Generátor čte živě z Heliosu, kde červen ještě není uzavřený. Kdyby se čísla při uzávěrce hnula, před podáním přegenerovat.

6. **Drobnosti.** Místo výkonu / obec je natvrdo „Plzeň" (kód 554791) pro všechny — pro ES ověřit, jestli sedí. ELDP kód „1++" je hardcoded (pro speciální vztahy může být jiný).

## Konkrétní další kroky (příští týden)

- Rozšířit `attach_absence` o nemoc / mateřskou / dovolenou (vyloučené doby do ELDP) — projít červnové absence z docházky (ES i EC).
- BOD 4: rozpoznat typ pojistného vztahu (standard / DPP / DPČ / mateřská) a podle toho stavět formulář (Šafránková mateřská, Herejtová/Senft srážková).
- Zpevnit OČR párování (user_id místo shody čísel) + přidat varování, když OČR case nenajde svou osobu.
- Ověřit místo výkonu / obec pro ES.
- Po uzávěrce červnových mezd přegenerovat + `@@EPVAL … PROD` (produkční validátor) → pak ruční podání přes ePortál/datovku (Peťa).
- (Nice-to-have) VS zaměstnavatele do sloupce `tenant.company.cssz_vs` jako jediný zdroj pravdy sdílený s eNeschopenka syncem.
