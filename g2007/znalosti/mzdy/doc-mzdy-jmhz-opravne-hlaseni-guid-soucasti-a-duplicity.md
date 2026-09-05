# JMHZ — opravné hlášení: GUID součásti (40238) a duplicitní ID zaměstnání (40251)

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# JMHZ — opravné hlášení: GUID součásti a duplicity

**Oblast:** mzdy · **Zapsal:** Claude-24 (Kristý), 4. 9. 2026 · Navazuje na [[doc-mzdy-jmhz2026-podani-a-opravy]] a [[doc-mzdy-jmhz-cervenec2026-tichy-propad-generatoru]].

## Dva různé GUIDy — neplest
1. **GUID podání** = `<n1:idPodani>` = GUID celého měsíčního hlášení. Opravné podání musí nést GUID **řádného** podání, jinak vada **40217** „Chybný GUID podání. Řádné podání se nenašlo" a celé podání je zamítnuto.
2. **GUID součásti** = `<n1:idFormulare>` u každého `formularOsoby`. Opravný formulář musí nést GUID **už přijatého řádného formuláře té osoby**, jinak vada **40238** „V rámci opravného podání nebyl nalezen GUID součásti".

Generátor původně dělal `uuid4()` u obou → obojí padalo.

## Tři stavy formuláře v opravném podání
ČSSZ v protokolu o kompletnosti u každé osoby sama napíše, co poslat:
- **typ O + EXISTUJÍCÍ GUID** — řádný formulář té osoby byl přijat, opravuje se. *„pošlete OPRAVNÝ formulář … s EXISTUJÍCÍM <guid> (GUID přijatého řádného formuláře — NEgenerujte nový)"*
- **typ R + NOVÝ GUID** — řádný formulář byl odmítnut, není na co navázat. *„Pošlete NOVÝ ŘÁDNÝ formulář … s NOVĚ vygenerovaným GUID formuláře"*
- **VŮBEC NEPOSÍLAT** — formulář už je přijatý a v pořádku. Tenhle stav v mapě zpočátku chyběl a stál nás jedno kolo (viz 40251 níže).

Implementace: `modules/erp/api/jmhz_maps/forms_map_<FIRMA>_<rok>-<mesic>.json` (mapa oič → {typ, guid}), načítá `load_forms_map`, aplikuje `build_jmhz` (commit `76835bec`). ⚠️ `docs/jmhz/` je v .gitignore, mapy tam nepatří.

## 40251 — duplicitní ID zaměstnání
*„(nepropustná) Bylo zjištěno opakované použití stejného ID zaměstnání na více součástech v měsíčním hlášení… Formulář pro dané ID zaměstnání byl již přijat, není tedy nutné podávat další opravný formulář."*

Vzniká, když se **za jedno rozhodné období pošle formulář osoby, jejíž formulář už ČSSZ přijala** — typicky když se odešlou dvě verze opravného podání po sobě a druhá zopakuje lidi ze skupiny „nový řádný", kteří se mezitím přijali z té první.

**Není to chyba dat.** ČSSZ duplicitní formulář odmítne a ten původní přijatý zůstává platný. Nic se nedoposílá.

## Jak poznat, že 40007/40012 jsou jen důsledek duplicity
Obě jsou **propustné** a při duplicitě ukazují součet přes formuláře **včetně duplicit**. Rozdíl proti PVPOJ pak sedí přesně na vyměřovací základy a pojistné duplicitních osob — ověřeno 4. 9. 2026 na obou firmách:

| Firma | Úhrn ČSSZ / náš | Rozdíl | Pojistné ČSSZ / naše | Rozdíl | Duplicitní osoby |
|---|---|---|---|---|---|
| EC | 783 907 / 647 845 | 136 062 | 55 666 / 46 004 | 9 662 | Vlková 22 762, Pašek 90 800, Mózer 22 500 (SP 1 617 + 6 447 + 1 598) |
| ES | 1 339 327 / 1 248 527 | 90 800 | 95 106 / 88 659 | 6 447 | Pašek 90 800 (SP 6 447) |

Když rozdíl sedí na korunu na duplicitní osoby, je to artefakt duplicity, **ne chyba ve výpočtu PVPOJ**.

## Postup pro příští opravné hlášení
1. Vzít protokol o kompletnosti k poslednímu podání.
2. Sestavit mapu: kdo O (s GUIDem), kdo R (nový GUID), **kdo se vynechá (už přijat)**.
3. Poslat JEDNU verzi a počkat na protokol. Neposílat druhou verzi „pro jistotu" — vyrobí to 40251.
4. Rozhoduje protokol o kompletnosti, ne protokol o dílčím podání.

