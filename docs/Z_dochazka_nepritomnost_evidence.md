# Nepřítomnost v docházce — kam patří a kde se eviduje

> Zapsal Claude-26 (Peťa) 21. 7. 2026. Pravidla podle Peti + přehled o tom, kde
> absence v systému reálně bydlí (je to na třech místech, což mate).

## Pravidlo: nepřítomnost = zakázka Režie + vlastní činnost

Peťa 21. 7. 2026: *„dovolená není výkon, ale počítá se do FPD a v Centrále je na
zakázku Režie, chceme to stejně"* a *„to, že je někdo nepřítomný, neznamená, že
mu nenáleží peníze a je potřeba tuto nepřítomnost evidovat"*.

Model zakázek podle Peti:

- **VR, PR** — činnosti vždy spjaté s konkrétní zakázkou
- **Režie** — čtyři různé věci pod jednou zakázkou:
  1. práce mimo zakázku, ale potřebná (úklid dílny) — do FPD
  2. běžná režijní práce kanceláře (nákup, úklid kanceláře)
  3. **placené volno** — dovolená, SD, ostatní placená nepřítomnost
  4. **náhradní volno** — jako omluvenka; **do FPD se nepočítá**, ale peníze se
     nestrhávají (v Centrále činnost 39)

### Jak je to implementované

Při převodu práce na nepřítomnost v Opravách docházky (`att_fix_entry`) se úsek
ve výkazu (`tenant.work_alloc`) **neruší** — přehodí se na zakázku `Rezie`
(`is_rezie=true`) a dostane odpovídající činnost. Mapa je
**`_ATT_ABS_CINNOST`** v `router.py`: `vacation→dovolena`, `medical→lekar`,
`sickday→sickday`, `unpaid→neplacene_volno`.

⚠️ Nejdřív jsem činnost mazal — **špatně**. Bez činnosti není ve výkazu vidět,
oč šlo.

### Číselník činností má tři skupiny (`vyroba_cinnost.kind`)

| kind | co to je | kde se nabízí |
|---|---|---|
| `standard` | dílenské činnosti (Drátování, Zkoušení, Balení…) | mobil, při píchání na zakázku |
| `rezie` | režijní (Porada, Školení, Úklid firmy, Nákup…) | mobil, při píchání na Režii |
| `nepritomnost` | **nové 21. 7.** — Dovolená, Lékař, Sickday, Neplacené volno | **jen editor** v Opravách docházky |

První dvě skupiny odpovídají tabulkám Centrály `EC_DilnaCinnosti` a
`EC_Dochazka_CinnostiRezie`. Třetí skupina existuje proto, aby si **lidi
nemohli vybrat „Dovolená" jako běžnou činnost při píchání** — picker
(`/app/vyroba/my-cinnosti`) pouští jen `standard`/`rezie`, takže nová skupina
se jim nikdy nenabídne. Peťa 21. 7.: *„lidem se mají ukazovat jen pracovní
činnosti"*.

Do roletky typů v Opravách docházky (`_ATT_FIX_TYPES`) přibyly `vacation`,
`medical`, `sickday`, `unpaid`. **Nemoc (PN) a OČR schválně ne** — ty vznikají
z dokladu přes modul absencí.

## Kde absence bydlí (tři úložiště!)

Tohle je zdroj většiny zmatku:

| úložiště | co drží |
|---|---|
| `tenant.att_absence_request` | **naše žádosti** — období od–do, poznámka zaměstnance i vedoucího, stav (`pending`/`approved`/`rejected`/`info`/`cancelled`) |
| `tenant.att_planned_absence` | **zrcadlo Centrály** (`EC_Dochazka_PlanNepritomnost`), **po jednotlivých dnech**, ne po obdobích |
| `tenant.att_entry` | **denní záznamy** vyrobené ze schválené žádosti |

**„Materializace"** = při schválení žádosti (`/absence/decide`) se z jednoho
řádku období vyrobí konkrétní denní záznamy v `att_entry` — jen na pracovní dny
podle `att_calendar_day`, se `source='absence'`, `source_system='absence_req'`,
`source_id=<id žádosti>`. Při odschválení se zase smažou.

⚠️ V `att_planned_absence` znamená **`src_id < 0`** naši absenci zrcadlenou
zpátky do Centrály. Kdo spojuje zdroje, musí je vyfiltrovat, jinak jsou v
přehledu **dvakrát**.

## Registr absencí (nové 21. 7. 2026)

Chyběl přehled, jaký měla Centrála ve Správě docházky. Postaveno:

- endpoint **`GET /app/absence-registr`** (`?rok=` / `?vse=1`) — spojuje naše
  žádosti se zrcadlem Centrály; dny z Centrály slučuje do období
  (gap-and-islands přes `datum - row_number()`), `src_id < 0` vynechává
- stránka **`apps/api/static/registr-absenci.html`**, routa `/registr-absenci`
- v ERP menu pod soudečkem **Docházka** (`fw.menu_node` id=94), jádro
  `dochazka.absence` + iframe hook v `page_render.js`
- sloupec **Zdroj** říká, kde se záznam pořídil (STRATEGIE / Centrála)

Práva: rodiče, HR, editoři oprav a držitelé zámku (Peťa 18, Šárka 13, Jirka 20).

**Zatím jen prohlížení** — schvalování přímo z přehledu není. Marti ve stejný den
řešil schvalování dovolené (`doc-dochazka-schvalovani-dovolene`), takže než se
do toho sáhne, sladit s ním.

## Nedodělek: náhradní volno

Typ pro náhradní volno **neexistuje**. Je zvláštní tím, že se platí, ale do FPD
nepatří. Číselník `att_entry_type` na to má sloupec **`affects_balance`** — což
je přesně ekvivalent `HodinyDoFPD` z Centrály — ale **nikdo ho v kódu nečte**.
Takže samotné založení typu nestačí, musí se naučit výpočet fondu ten příznak
respektovat.
