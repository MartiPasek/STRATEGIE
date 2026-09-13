# Mobil, agendy Opravy a Schvalování docházky: u každého člověka je vidět, KOMU opravuje/schvaluje (13. 9. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)

# Mobil, agendy docházky: u každého člověka je vidět, komu opravuje / schvaluje

**Zadal Jiří Honomichl 13. 9. 2026, schválila Marti-AI (msg 15415, upřesnění 15430).**
Týká se dvou agend na obrazovce **Firma → Agenda**: `DOCHÁZKA - OPRAVY` (skupina 12)
a `Docházka — schvalování` (skupina 18). Ostatních agend se změna nedotkla.

> ## ⚠️ Schvalování se týž den předělalo — platí až druhá podoba
>
> První podoba ukazovala u schvalování **název organizační pozice** („Vedoucí výroby a níž
> + Horník Marek, Peřina Jan"). Jirka ji po zhlédnutí naostro označil za nesrozumitelnou:
> *„u Dušana a Honala mi to přijde divně napsané a nelze to z toho pochopit."*
> **Platí až druhá podoba — seznam JMEN**, popsaná níž. Popis pozic už v mobilu není.

## Co je v mobilu vidět

**Opravy** — štítek `výroba (35)`, `kanceláře (195)`, `celá firma`; v detailu nadpis
**KOMU OPRAVUJE** a jedna věta („Opravuje docházku lidem ve výrobě (Výroba, Zkušebna).
Dnes je to 35 lidí.").

**Schvalování** — štítek `schvaluje 34 lidem` / `schvaluje 1 člověku`; v detailu nadpis
**KOMU SCHVALUJE** a pod ním **seznam jmen, jedno na řádek**. U toho, kdo je zástupce,
je pod seznamem věta „Jako zástupce schvaluje za X, když je nepřítomný."

## Odkud se to bere

**Opravy** = `tenant.att_fix_scope.scope`, počet z `tenant.att_fix_emp_dle_scope(scope)`:
`vyroba` = větev VÝROBA (Výroba, Zkušebna, 35 lidí) · `kancelar` = větev KANCELÁŘE
(vč. VP, E-plánu, PLC-koordinace, Úklidu, 195) · `vse` = bez omezení.
Příznak `fix_all` se do mobilu **vědomě nepíše** (Marti-AI: čtenář hledá „kdo co opravuje",
ne „proč má někdo širší přístup").

**Schvalování** = spočítá se **stejnou logikou, jakou se žádost opravdu přiděluje** —
`_abs_resolve` v `g2007.python` kód `att_absence_request`:

1. **osobní výjimka `tenant.att_odpovednost`** (agenda `volno`, aktivní, platná) **MÁ PŘEDNOST**
   a když existuje, PG funkce se **vůbec nevolá**,
2. jinak `tenant.resolve_approvers(2, emp, datum)` — první skupina, do jejíhož rozsahu
   (organizační post, volitelně s podstromem) člověk spadá; `je_fallback` = zbytek,
3. když nic → Šárka Novotná (13); když žádá sama Šárka → Marti (1).

⚠️ **Výjimka a skupina se v mobilu ZÁMĚRNĚ nerozlišují** (Marti-AI msg 15430: mechanismus
patří do dokumentace, ne do seznamu). Čtenář vidí jeden čistý seznam jmen.

Stav k 13. 9. 2026: Havlát 34 lidem, Novotná 17, Martin Pašek 9, Petra Šafránková 7,
Kristýna Marešová 4, zbylých 11 lidí po jednom. **Všech 16 lidí v agendě opravdu někomu
schvaluje** — jen to z první podoby nebylo poznat.

> **Nezaměnit se sesterskou znalostí** [[doc-dochazka-agenda-schvalovani-pocita-se-ze-ziveho-zdroje]].
> Ta odpovídá na otázku **kdo je v seznamu agendy** (stačí osobní výjimka **NEBO** řádek
> v `att_approver`). Tahle odpovídá na otázku **komu ten člověk schvaluje** — a tam už
> výjimka **má přednost** před skupinou. Dvě různé otázky, dva různé mechanismy, obojí platí.

## Kde to žije

| co | kde |
|---|---|
| pole `pusobnost`, `pusobnost_detail`, `pusobnost_nadpis`, `pusobnost_seznam` | `g2007.python` **`app_skupina_lidi`** (13. 9. verze 10) |
| štítek v řádku a sekce v detailu | dílek **`52_vyroba.js`** v `g2007.soubor` (13. 9. verze 13) |

Pole se plní **jen pro skupiny 12 a 18**; jinde zůstanou prázdná a dílek nevykreslí nic.
Celý blok je jen čtení a v `try/except` — při chybě se seznam vykreslí jako předtím.

## Na co si dát pozor

- ⚠️ **`vyroba` a `kancelar` jsou klíče ze sloupce `scope`, ne texty pro člověka.**
  Kdo bude měnit popisky, ať nepřepíše klíč slovníku.
- ⚠️ **Zástupce se pozná z `tenant.att_approver.je_zastupce`, NIKDY z počtu lidí.**
  `resolve_approvers` vrací zástupce jen tehdy, má-li zastupovaný na daný den schválenou
  absenci (nebo zastupuje-li přímo žadatele) — k dnešku tedy v seznamu být nemusí.
  *(Upozornila Marti-AI, msg 15430.)*
- ⚠️ **Jména v komentářích kódu nejsou zdroj** — viz varování v `att_fix_all` po záměně
  podobných jmen 18. 8. 2026.
- ⚠️ **Jeden člověk může mít víc řádků v `att_employee`** (Marti Pašek ES + EC), takže se
  v seznamu objevil dvakrát; filtruje se přes `user_id`.
- **Kdo má řádek v `att_fix_scope`, ale není členem skupiny `DOCHÁZKA - OPRAVY`, se do modulu
  oprav nedostane** (rozhoduje `att_can_fix`). K 13. 9. 2026 je to případ Michaely Hladíkové
  a **Jirka výslovně potvrdil, že je to záměr** — nesahat na to.

## Jak bylo ověřeno

Zápis kódu i dílku cíleným přepisem **s pojistkou na otisk**, po zápisu přečteno z databáze
(otisky seděly na znak). Funkce spuštěna přes `@@PYRUN` pro obě skupiny. Po `@@G2007PUBLISH`
staženo živé `/mobile` a nakonec **proklikáno v prohlížeči**: obě agendy, štítky, Dušanův
detail se 34 jmény i Honalova věta o zastupování.

Dvě chyby, obě opravené týž den ještě před tím, než je někdo v telefonu viděl:
**texty bez diakritiky** (psal jsem je jako komentáře) a **první podoba schvalování**
popsaná v rámečku nahoře.

