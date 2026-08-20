# Zadost z appky dostavala fajfku Schvaleno drive, nez ji vedouci rozhodl - pricina a oprava

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Falesna fajfka "Schvaleno" u zadosti z appky

**6. 8. 2026, C28/Jirka. Odhaleno pri testu Dusana Havlata. Schvalila Marti-AI (msg 12392, 12418).**

## Priznak

Ve Sprave dochazky se absence objevila **rovnou se zaskrtnutim ve sloupci S**, prestoze ji
vedouci nikdy nerozhodl. Doloženo testem\: Matej Svoboda (uid 42) zadal v appce dovolenou,
zadost #69 vznikla ve 12\:16\:22 se stavem `pending` a **ve stejnou vterinu** vznikl den
v `att_entry` s `ved_schvaleno=true`.

## Pricina — retez dvou veci, z nichz jen jedna je chyba

1. **Zamer (Peta, 30. 7. 2026, NEMENIT).** `att_absence_request` po vytvoreni zadosti vola
   `dochazka_absence_sprava.abs_promitni_zadost`. Komentar v kodu\: *„dovolena a sick day se
   propisou do dochazky ROVNOU podle pravidel, bez ohledu na schvaleni — jako to bylo
   v Centrale"*. Duvod\: do te doby neschvalena zadost = prazdny den v dochazce (viselo
   23 zadosti u 14 lidi). Tyka se typu `vacation` a `sickday` (`_ROVNOU_DO_DOCHAZKY`).
2. **Chyba (vedlejsi efekt).** `abs_promitni_zadost` volala `_zapis_dny(...)` **bez parametru
   `schvaleno`**, takze se pouzil jeho **default `True`**. Ten default patri **spravcovskemu
   zadani** (*„co zada spravce, plati hned"*, Peta 31. 7.) — ale touhle cestou chodi i bezna
   zadost z appky, ktera zadne rozhodnuti za sebou nema.

**Proc to vadi\:** prazdny sloupec S je jen chybejici informace, ale **fajfka je tvrzeni, ze
vedouci rozhodl** — a to nebyla pravda. U mezd a schvalovani je to horsi nez prazdno.

## Oprava

**Kod** (commit `f573b094`, `modules/erp/api/dochazka_absence_sprava.py`)\:
`abs_promitni_zadost` predava `schvaleno=(stav == "approved")`. Funkce stav zadosti uz
nacitala (pouziva ho na gate `cancelled`/`rejected`), takze slo o jeden parametr navic.
**Zapis dnu dopredu zustava presne jak chtela Peta** — meni se jen ten priznak.

**Data\:** 17 dnu melo fajfku neopravnene (16 u 3 cekajicich zadosti, 1 u zrusene) → `false`.
Marti-AI\: **`false`, ne NULL** — NULL rika „nevime", `false` rika „neschvaleno", a to je pravda.

## Gotcha ke kontrole vysledku

Po oprave zustal **jeden** schvaleny den bez fajfky\: Kristyna Maresova 27. 7. Petra ji
schvalila v **9\:18\:56** a oprava `att_absence_decide` sla do provozu v **9\:19\:20** — o 24 s
pozdeji. Neni to nova dira, ale posledni dozvuk stareho chovani. Pri podobnych opravach
**porovnavej casy nasazeni s casy zapisu**, nez zacnes hledat druhou chybu.

## Kdo o tom vi

Petra Safrankova informovana mailem (je to jeji pravidlo z 30. 7. a na oblasti aktivne
pracuje — tyz den nasadila pojistku proti dvojimu zapsani teze absence). Marti-AI\:
*„tichy zapis do G2007 nestaci — muze zitra napsat kod, ktery na starem chovani stavi"*.

Souvisi\: `doc-dochazka-schvalovani-absenci-erp-menu-a-fajfka`.

