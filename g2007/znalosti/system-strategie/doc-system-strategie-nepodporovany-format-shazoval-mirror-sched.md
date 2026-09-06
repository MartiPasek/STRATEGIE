# Nepodporovana priloha shazovala smycku mirror_sched — vyjimka dedila z BaseException (vyreseno 6.9.2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Nepodporovana priloha shazovala smycku mirror_sched

**Zapsal:** Claude-28 (Jiri Honomichl), 6. 9. 2026 · **Nasazeno:** `9085af82`
Navazuje na `doc-system-g2007-rag-diag-image-flood` (21. 7. 2026), ktera resila prazdnou
extrakci; tohle je jeji druha polovina — format, ktery se prevest NEDA.

## Priznak

V `C:\Logs\STRATEGIE\api-stderr.log` se opakovalo `[mirror_sched] SELF-HEAL: loop byl mrtvy
(vyjimka: UnsupportedFormatException("Could not convert ...gif to Markdown"))`.
V poslednich 6 000 radcich to bylo **180x SELF-HEAL a 90x ta vyjimka**.
Predavka z 3. 9. 2026 oznacila cestu, kudy vyjimka unika, za NEOVERENOU.

## Pricina (overeno spustenim na produkcnim serveru)

**`UnsupportedFormatException` z knihovny markitdown dedi PRIMO z `BaseException`, ne z `Exception`.**
Overeno na Praze: `mro = UnsupportedFormatException, BaseException, object`.

Proto propadla VSEMI bloky `except Exception` po ceste:
1. `process_document` — `modules/rag/application/service.py`, r. 229
2. `_mirror_sched_loop` — `modules/erp/api/router.py`, r. 29771
3. cv-import — `router.py`, r. 17983

Smycka `mirror_sched` na ni umirala, self-heal ji nahodil a kolo se opakovalo.

## Dopad na lidi (jmenovite)

- sberna schranka **projects@** (uzivatel 111, VP) — od 4. 9. 11:54 se ANI JEDNOU nedokoncila
- **Pavel Zeman** (uzivatel 30) — od 30. 8. 22:28 se ani jednou nedokoncila
  (u nej byla posledni zaznamenana chyba jina: nedostupny postovni server, nepricitat cele sem)
- **Eliska Kolarova** (uzivatel 34) — bezelo v poradku

## Oprava (u zdroje, ne symptomu)

- `modules/rag/application/extraction.py` — nova trida `UnsupportedDocumentFormat(Exception)`.
  Volani `md.convert()` je obalene tak, ze se markitdownovska vyjimka prevede na obycejnou
  `Exception`. Rozpoznava se podle `type(e).__name__`, takze to nezavisi na tom, odkud se
  da trida importovat. Jedno misto opravilo vsechny tri volajici.
- `modules/rag/application/service.py` — `process_document` ji chyta a spadne na
  `storage_only` (dokument zustane dohledatelny podle nazvu), stejne jako u prazdne extrakce.
  **Ostatni chyby padaji dal**, aby se pod tim neschovaly skutecne zavady.

## Dukaz, ze to funguje (z provozu)

- projects@ se dokoncila 6. 9. v 7:01 a zpracovala 48 dorucenych + 34 odeslanych
- Pavel Zeman se dokoncil v 6:51 a zpracoval 79 + 100
- v zaznamu je nove `nepodporovany format -> storage_only fallback | ext=gif`
  a **0 padu ulohy** (predtim 180 ve stejnem vzorku)

## Ponauceni pro priste

**`except Exception` nechyta vsechno.** Kdyz nejaka knihovna dedi vlastni vyjimku z
`BaseException` (misto z `Exception`), proleze kazdym beznym osetrenim az ven z hlidane
smycky a zabije ji. Kdyz umira smycka "bez pricin", zkontroluj `mro` te vyjimky:
`python -c "from <knihovna> import <Vyjimka> as U; print([c.__name__ for c in U.__mro__])"`.

