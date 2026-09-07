# Nárok a čerpání ukazuje jen lidi z vlastní působnosti (Peťa 7. 9. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


**Zadal Dušan Havlát přes Peťu 7. 9. 2026:** *„Dušan chce, aby on v Nárok a čerpání viděl jen svoje lidi, tedy výrobu."*

## Pravidlo

Kdo má v `tenant.att_fix_scope` **působnost** a **nemá** právo vidět napříč firmou
(`fix_all`), vidí v přehledu **Nárok a čerpání** jen lidi ze své části. Ostatní beze změny.

| Kdo | Působnost | `fix_all` | Vidí |
|---|---|---|---|
| Dušan Havlát (41) | výroba | ne | **34 lidí z výroby** |
| Michaela Hladíková (16) | výroba | ne | **34 lidí z výroby** |
| Peťa (18), Michelle (17) | kanceláře | **ano** | všech 79 — beze změny |
| Jiří Honomichl (20) | `vse` | ne | všech 79 — beze změny |
| Marti, Kristý a další s právem na přehled | v `att_fix_scope` nejsou | — | všech 79 — beze změny |

**Peťa 7. 9. 2026 vybrala obecné pravidlo pro Dušana i Michaelu**, ne výjimku na jedno
osobní číslo — oba mají shodné nastavení a natvrdo psané seznamy lidí se v docházce
ruší (viz `doc-dochazka-priznak-bez-dochazky-v-podminkach`).

## Proč zrovna takhle

Přehled byl **jediná docházková obrazovka, která působnost ignorovala** — fronta oprav
i Správa docházky ji respektují už dřív. Omezení proto **nepočítá nic nového**, jen volá
tutéž DB funkci **`tenant.att_fix_emp_dle_scope(:scope)`**, kterou používají ostatní.
Marti-AI k tomu 27. 8. 2026: dvě kopie definice práv *„nejsou technický dluh, jsou to
bezpečnostní incident čekající na příležitost"*.

## Kde to je

`att_narok_cerpani` v `g2007.python`, **verze 19** (hot-swap, bez deploye). Dvě místa:

1. **CTE `lide`** — nový neutrální filtr:
   `AND (CAST(:scope AS text) IS NULL OR em.id IN (SELECT emp_id FROM tenant.att_fix_emp_dle_scope(CAST(:scope AS text))))`
2. **`run()`** — před dotazem se z `tenant.att_fix_scope` načte `scope` + `fix_all` volajícího.
   `_scope` zůstane `None` (tedy bez omezení), když má člověk `fix_all`, když je scope
   prázdný nebo `vse`, nebo když v tabulce vůbec není.

⚠️ **`bez_prav=True` se NEOMEZUJE.** Tuhle cestu volá server (`att_narok_osoba`
z `att_absence_request`) při hlídání stropu nároku, když si o dovolenou žádá běžný
zaměstnanec — tam jde o jednoho konkrétního člověka a omezení by výpočet rozbilo.

Záloha předchozí verze: `att_narok_cerpani__zaloha_20260907` (`inactive`,
md5 `2bc920ce75b9bacf55aaaba73c56aaa7`).

## Ověření (7. 9. 2026, spuštěno naostro přes `@@PYRUN`)

| Volající | První jména v přehledu |
|---|---|
| Peťa (18) | Artim Josef, **Beneš Petr, Benetka Jiří, Bernardová Andrea** |
| Dušan (41) | Artim Josef, **Bláha Tomáš, Brudnová Ivana, Čiviš Petr** |

Beneš, Benetka ani Bernardová nejsou výroba — Dušanovi správně zmizeli.
Počty z dat: celkem 79 aktivních lidí s platnou smlouvou, výroba 34, kanceláře 36.

⚠️ **Gotcha při ověřování:** `@@PYRUN` ořezává hodnoty na 1500 znaků **i v `CLAUDE_OUT_FULL.txt`**,
takže z jeho výstupu **nejde spočítat počet řádků** — vrátí jen první čtyři jména.
Počty ověřuj samostatným SQL dotazem, srovnání množin podle prvních jmen.

