# ERP schvalovani absenci: akce v kontextovem menu, fajfka ve sloupci S, hlaska "nic neceka", vlastni poznamka

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# ERP schvalovani absenci — menu, fajfka, hlaska, poznamka

**6. 8. 2026, C28/Jirka. Podnet Dusan Havlat (uid 41). Schvalila Marti-AI (msg 12359, 12362, 12365, 12368, 12371, 12374).**

## Podnet a skutecna pricina

Dusan hlasil, ze v ERP `Dochazka -> Absence - schvalovani` nevidi tlacitka. Nebyla to
chyba prav (na obrazovku ma; `fw.menu_node` 210 ma 41 ve `visibility_user_ids`, registr
gateuje `_att_can_fix`, Dusan je ve skupine `DOCHAZKA - OPRAVY`). **Nemel co schvalovat** —
5. 8. ve 13\:02 rozhodl v mobilu vsech 6 svych zadosti a nova nepribyla. Vada byla v UI\:
pri prazdnem seznamu **cely blok zmizel bez hlasky**, takze fungujici obrazovka vypadala rozbite.

## Co je hotove

**1. `att_absence_inbox` (g2007.python v1 -> v3)**
- `je_vedouci` byl `parent or len(out) > 0` = **stavova**, ne identitni hodnota\: pro
  nerodice vysla `false` prave kdyz nic neceka. Nove rodic NEBO aktivni radek v
  `tenant.att_approver` (join na `att_employee.user_id`, `LIMIT 1` kvuli doktrine #24).
- Novy klic **`statusy_map`** = `dict(_ABS_STATUSY)` (veta -> stav). `statusy` beze zmeny,
  mobilni appka (`mobile_parts/50_skupiny_vyroba.js`) se nemeni.

**2. `registr-absenci.html` (id 73)** — hlaska "Ke schvaleni\: nic neceka." pri prazdnu, ale
jen schvalovatelum; pod kazdou zadosti nepovinne pole na vlastni poznamku.

**3. `dochazka-po-zakazkach.html` (id 68) = ERP Sprava dochazky** — Dusan NECHTEL pruh nad
tabulkou (prvni verze, odstranena), chtel **akci v kontextovem menu**. Hotovo\:
- polozka `#ctx_schval` v `div#ctxm`, akce `data-a="schvalit"`
- `openCtx` ji zobrazi **jen kdyz** radek je cekajici zadost (RadekId zacina `Z:`) A je
  ve **mnou rozhodnutelnych** (nactenych z inboxu) -> pravomoc se neresi zvlast
- `ctxAction` vetev otevre okno `#ovsch`\: kdo, druh, obdobi, poznamka zamestnance,
  nepovinna vlastni poznamka, 6 vet jako tlacitka
- zdroj je samostatny fragment `apps/api/static_db/_fragment_schvalovani_absenci.html` (typ zdroj)

**4. Fajfka ve sloupci "S"** — byla naprogramovana (`CASE WHEN schvaleno THEN ...` v datasetu
`dochazka.zakazky_budoucnost_list`), ale nikdy se nevyplnila. Pricina\: `att_absence_decide`
pri materializaci zadosti do `att_entry` **nenastavoval `ved_schvaleno`** (delala to jen
spravcovska cesta Peti v `dochazka_absence_sprava._zapis_dny`). Opraveno v obou smerech\:
- `att_absence_decide` nove vklada `ved_schvaleno=true`
- backfill 22 radku (9 lidi, 12 zadosti) tam, kde zadost je `approved` a priznak chybel;
  zbylych 35 NULL radku bez approved zadosti se VEDOME nedotklo
- overeno\: v prehledu ma nove 32 radku fajfku (drive 0)

## Klicove\: volny text NESMI prepsat stav

`att_absence_decide` odvozuje stav z vety pres `_ABS_STATUSY.get(status_text, "approved")`.
Vlastni text by mapa nenasla a **zamitnuti by se tise zmenilo na schvaleni**. Proto UI posila
**vzdy i explicitni `stav`** ze `statusy_map`; poznamka se pripoji za vetu. Overeno v
prohlizeci se zachycenym `fetch` (na server nesel zadny zapis)\: zamitnuti + poznamka ->
`rejected`, "Kontaktuj me osobne" -> `info`, bez poznamky -> ciste veta + `approved`.

## Prava se NEMENILA

Inbox vraci jen zadosti, kde je clovek `manager_user_id` (rodic vse); `decide` pousti tytez.
Dusan nevidi ani nerozhoduje cizi zadosti — tak to Jirka 6. 8. vyslovne chtel.

## Nasazeni a nedodelky

Vse jen v DB, **bez deploye a restartu API**. `registr-absenci.html` sel pres `@@G2007PUBLISH`,
`dochazka-po-zakazkach.html` pres `@@G2007EXPORT` (PUBLISH na ni hlasi falesny poplach — viz
`doc-system-strategie-g2007publish-falesny-poplach-tagy`).

Vedome nedodelano\: schvalovani klikem primo z radku na strance registr-absenci (endpoint
`/app/absence-registr` nevraci `id` a jeste zije v `router.py`). Zdravotni doklady jdou dal
na HR, viz `doc-dochazka-schvalovani-absenci-kde-a-jak`.

