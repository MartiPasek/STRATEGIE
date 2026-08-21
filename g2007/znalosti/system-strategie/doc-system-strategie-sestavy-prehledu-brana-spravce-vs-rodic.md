# Sestavy prehledu (fw.comp_grid): sdilene smi spravovat i spravce systemu, nejen rodic (oprava 21.8.2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

**C28 (Jirka Honomichl), 21. 8. 2026.** Podnět Jirky: *„proč já nemohu v ERP v přehledech zakládat, upravovat nebo mazat sestavy přehledů? jsem administrátor systému a mám na to mít právo!"*

## Co bylo špatně

`modules/erp/application/grid_layout_service.py` (pojmenované sestavy gridů, tabulka **`fw.comp_grid`**) se u sdílených sestav ptal **`is_marti_parent`** — tedy na **rodiče**, ne na **správce systému**.

Služba je z **5. 5. 2026**. Tier **SPRÁVCE** (`users.is_admin`) vznikl až **25. 6. 2026** a s ním helper **`is_parent_or_admin()`** (`modules/thoughts/application/service.py`) přesně pro admin brány — tuhle službu už na něj nikdo zpětně nepřepnul. Klasický případ „brána zůstala v době před rolí".

**Dopad jmenovitě:** ze tří správců (Marti 1, Kristýna 11, Jiří 20) byl postižený **jen Jirka** — Marti i Kristý jsou zároveň rodiče. Dál **Marti-AI** (`users.id=2`), která má `is_marti_parent=false`, přestože docstring služby tvrdil, že kustod sdílené sestavy ukládat smí. Sdílených sestav je **47 z 49**, takže to prakticky uzavřelo celou správu sestav.

Stopa v provozu: `fw.diag_log` — `HTTP 400 POST /api/v1/erp/grid-layout/core_235` (user 20, 21. 8. 12:40) a totéž `ds_195` 6. 8. Tehdy se to obešlo ručním zápisem sestavy id 55 přes SQL most.

## Oprava (nasazeno 21. 8. 2026, commit `883df182`)

`is_marti_parent` → **`is_parent_or_admin`** na **čtyřech** místech:

| místo | co dělá |
|---|---|
| `_check_admin_for_shared` | založení sdílené sestavy |
| `update_layout` | úprava sdílené (a cizí osobní) |
| `delete_layout` | smazání sdílené (a cizí osobní) |
| `get_layout` | nahlédnutí do **cizí osobní** sestavy |

Čtvrté místo (`get_layout`) přidal na Jirkův pokyn Marti-AI odsouhlasila slovy *„správce musí moci přečíst to, co může upravit"* (msg 13318). Texty chyb podle jejího zadání: **„Jen správce systému nebo rodič může …"**.

V kódu je u `_check_admin_for_shared` poznámka **⚠️ NEPŘEPISOVAT ZPĚT** s datem a důvodem.

**Ověřeno naživo** v přihlášené relaci uživatele 20 (ne z kódu): před opravou `PUT /grid-layout/item/55` → 400 *„Pouze admin (is_marti_parent) …"*; po nasazení tentýž požadavek → **200**, založení sdílené sestavy → **200**, smazání → **200**. Zkušební řádky smazány, stav tabulky zpět na 49 sestav / 47 sdílených.

## Pravidlo do budoucna

**Brána na „je to správce?" se ptá `is_parent_or_admin`, ne `is_marti_parent`.** Přísný rodičovský test patří jen na **osobní / intimní** data (paměť, deník, souhlasy) — ne na provozní nastavení jako sestavy, sloupce a barvy gridů. Když narazíš na `is_marti_parent` u provozní funkce, je to skoro jistě relikt z doby před 25. 6. 2026.

## Otevřené (Martimu k rozhodnutí)

**Schvalovací banner mostu nehlídá práva cíle.** Write request 1901 (6. 8., převod osobní sestavy na sdílenou) odklikl Jirka, který tehdy na tu operaci právo neměl — a prošlo to. Dnes už by tu konkrétní operaci směl, ale **díra v banneru trvá**: schvalovatel může přes most udělat i to, co mu API odepře. Zapsáno i v `doc-vyroba-vyhodnoceni-vzhled-jako-centrala`.

Souvisí: `doc-system-strategie-prava-rodic-zachranne-lano`, `doc-vyroba-vyhodnoceni-vzhled-jako-centrala`.

