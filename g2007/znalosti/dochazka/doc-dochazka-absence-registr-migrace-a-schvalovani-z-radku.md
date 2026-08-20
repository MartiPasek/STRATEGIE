# Registr absenci: migrace endpointu do g2007.python, req_id a schvalovani pravym klikem na radek

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Registr absenci — migrace endpointu, req_id, schvalovani z radku

**6. 8. 2026, C28/Jirka. Podnet Dusan Havlat. Schvalila Marti-AI (msg 12380, 12383).**

## Proc migrace

Dusan chtel schvalovat absenci **klikem primo z radku** prehledu. Endpoint
`GET /app/absence-registr` ale zil jeste v `router.py` a ve vystupu **nemel id zadosti** —
bez nej nejde poznat, na co uzivatel klikl.

**Parovani podle jmena + datumu + typu jsem odmitl**, a to je duvod hodny zapamatovani\:
v datech realne existuji duplicitni zadosti se **shodnym clovekem, typem i obdobim**
(napr. Michaela Hladikova 28. 7. jako id 42 i 43, Andrea Bernardova 20.–24. 7. jako id 20 i 21).
Parovani na castecny klic by u schvalovani znamenalo rozhodnout **cizi zadost**.

## Postup (poradi zamerne, schvalila Marti-AI)

1. **Migrace 1:1** do `g2007.python` kod `absence_registr` (kategorie `dochazka`).
   Zadna zmena logiky, prav ani vystupu.
2. **Deploy** jednoho souboru — v `router.py` zustal tenky delegate. Commit `b9820bfa`,
   diffstat 1 file, +10 / −89. Jedina dnesni vec, ktera vyzadovala deploy.
3. **Az potom** samostatna zmena v DB\: do vystupu pridano `req_id` (nase radky), Centrala
   dostava `null`. Overeno\: 47 nasich radku ma id, 1090 radku z Centraly nema.

**Jak jsem overil, ze migrace nic nezmenila\:** pred deployem jsem stahl vystup obou
variant (`rok=2026` a `vse=1`) z zive produkce, po deployi znovu a porovnal **jako
mnozinu, ne podle poradi** — `ORDER BY 6 DESC, 4` neni u shodnych hodnot deterministicky,
takze otisk zavisly na poradi je nepouzitelny. Vysledek\: **0 radku ubylo, 2 pribyly** —
a obe byly nove zadosti Jana Periny podane v 9\:53 a 9\:54, tedy behem overovani. Po jejich
odecteni **otisk mnoziny sedel na chlup** (fd12d270 pred i po).

## Gotcha pri zapisu kodu do DB pres most

Skript ma desitky `\:parametru` v SQL retezcich — v `UPDATE ... zdroj = '...'` by je
SQLAlchemy vzala jako bind parametry. Cesta, ktera to obchazi bez escapovani\:
**poslat telo pres `@@G2007SOUBOR` jako `typ='zdroj'`** (text za prikazem se neparsuje)
a pak `INSERT INTO g2007.python ... SELECT f.obsah FROM g2007.soubor f WHERE f.kod=...`.
Po zapisu **overeno md5** — shoda az na chybejici koncovy newline (7295 vs 7294 znaku).

**Nutne zachovat\:** v UNION vetvi je `'Centrála'` **s diakritikou** — stranka na tu
hodnotu porovnava pri vykreslovani znacky zdroje. Bez diakritiky by se tise rozbil
sloupec Zdroj.

## UI

Radky nesou `data-rid` (jen nase zadosti). Pravy klik -> male menu s jednou polozkou ->
stejne okno jako ve Sprave dochazky. Polozka se nabidne **jen** u radku, ktery ma `req_id`
A je mezi cekajicimi zadostmi z inboxu -> pravomoc se neresi zvlast. Handler visi na
`document` (delegace), protoze tabulka se pri kazdem filtru prekresluje.

Horni blok "Ke schvaleni" **zustava** — je to rozcestnik, akce z radku je jiny use case.

Souvisi\: `doc-dochazka-schvalovani-absenci-erp-menu-a-fajfka`.

