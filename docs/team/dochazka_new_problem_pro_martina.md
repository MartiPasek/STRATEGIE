# Docházka new — v čem a kde je problém (podklad pro Martina)

> Peťa + Claude‑26, 23. 7. 2026. Ke konzultaci s Martinem, **než to Peťa projde**.
> Souvisí: `doc-mzdy-mzdy-podklad-zdroj-pravdy`, `doc-dochazka-vs-vyroba-separace`.

## Co stavíme a proč
Přehled **„Docházka new"** (dřív „Docházka po zakázkách", uzel 189) má ukazovat
**docházku VŠECH lidí** za období (default 2 měsíce), jako v Centrále:
- **výroba** → přes svoje zakázky (VR… + Rezie),
- **kancelář / ostatní** → jejich docházka jako **„Rezie"**,
- **absence** (dovolená/nemoc/lékař).
Jednotlivé řádky od–do (nesčítají se v přehledu), + **„Sumace označených"** (jako v Centrále).
Vedlejší, ale důležitý účel: **srovnat app vs. Centrála** kvůli přechodu mezd na náš systém.

**Hotové a živé:** přehled ukazuje docházku všech za 2 měsíce (~5 900 řádků), editace
výrobních řádků dvojklikem (formulář jako Centrála), uzel přejmenován, sumace hotová.
(Poslední kosmetika + sumace čekají na nasazení — cloud je zaseklý na „dirty tree".)

## Jádro problému: kancelářská data v naší docházce jsou zdvojená
Kvůli separaci docházka×výroba (Marti 13. 6.) kancelář **nemá `vyroba_work`** — jejich čas
je v `att_entry` (přítomnost). Jenže `att_entry` u kanceláře přichází z **víc zdrojů, které
se překrývají**:

- **Táž směna je tam víckrát** — z **tabletu** i z **importu Centrály** (`ec_import`),
  navíc drobná píchnutí z **app**.
- Příklad **Petra, 8. 6. 2026**:

  | druh | od–do | hodin | zdroj |
  |---|---|---|---|
  | Režie (overhead) | 5:32–14:02 | 8,5 | tablet |
  | Režie (overhead) | 5:32–13:02 | 8,5 | **import z Centrály** |
  | Práce (work) | 12:29–12:43 | 0,24 | app |
  | Práce | 17:34–17:35 | 0,01 | app |

- **Důsledek:** prostý součet nafoukne hodiny. Petra červen = **359 h** místo reálných ~168.
- Nenárokovou práci a „doplnění do fondu" (automat) už z přehledu vynecháváme; problém je ta
  **duplicita tablet × import Centrály** u téže směny (sync duplicity neřeší).

## Peťino pravidlo a jeho mez
Peťa: **u kanceláře má při překrytí přednost app.** Ověřeno na jejích datech:
- **červenec 135 h** (čisté ✅) — protože v červenci už píchala v app,
- **červen 242 h** (pořád rozházené) — v červnu app skoro nepíchala, takže část dnů spadne
  na tablet/Centrálu a část (kde je v app jen drobek) se seřízne skoro na nulu.

**Závěr:** pravidlo funguje **dopředu** (odkdy lidi píchají v app), ale **přechodové měsíce
žádné automatické pravidlo nevyčistí** — to je ruční kontrola per člověk (dle data přechodu).
Peťa to bere: kde app a Centrála +/- sedí, OK; kde ne, projde se ručně.

## ⭐ Klíč, na který Peťa upozornila: co šlo do mezd, je platné
Mzdy se dnes počítají z `tenant.att_day_summary`, což je **živé zrcadlo Centrály**
(`EC_Dochazka_SumaDen`, sync á 10 min). Tedy **čísla, ze kterých se dělaly mzdy, jsou
z Centrály** → měla by být **autoritativní reference** pro srovnání.
- Opačný směr (my → Centrála, `mirror_att_to_ec`) je **vypnutý od 29. 6.** — app se do Centrály nevrací.
- Rozdíl naše `att_entry` vs. Centrála za 1.–21. 7.: **5 lidí u nás míň (−67 h)**, **15 víc (+170 h)**.
- Marti (22. 7.) rozhodl: mzdy z naší docházky, v Centrále už neopravovat — ale **napřed srovnat**.

## Otázky na Martina
1. **Reference pro srovnání:** brát Centrálu / `att_day_summary` jako pravdu (protože z ní šly
   mzdy), a naši docházku k ní dorovnávat? (Peťin postřeh.)
2. **Duplicita tablet × `ec_import`** u téže směny — je to chyba importu/synchronizace, kterou
   opravit u zdroje (aby se táž směna nebrala dvakrát)?
3. **Kancelář v přehledu:** ukázat syrové řádky s pravidlem „app má přednost" (nástroj na
   ruční srovnání), nebo brát čistý **denní součet z mzdového podkladu** (bez duplicit, ale
   bez rozpadu na úseky)?
4. **Přechodové měsíce:** jak sjednotně vyřešit per‑osoba datum přechodu z Centrály na app.
