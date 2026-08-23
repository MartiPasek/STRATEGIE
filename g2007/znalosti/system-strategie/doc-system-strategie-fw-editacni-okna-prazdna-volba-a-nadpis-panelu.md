# FW editační okna — prázdná volba ve výběru a nadpis panelu v mřížce

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## 1) Prázdná volba ve výběru shazovala ukládání (opraveno 22.8.2026)

**Příznak.** Na obrazovce Výchozí podmínky skupin (fw core 236) hodilo uložení HTTP 500,
když uživatel zvolil „— dědí se ze systému —" u pole Víkend jen se schválením.
V `fw.diag_log`: `design_patch_entity failed: invalid input syntax for type boolean ""`,
tedy `UPDATE tenant.podminky_skupin SET pod_vikend_jen_schvaleni = ''`.

**Příčina.** Combobox posílá u prázdné volby prázdný řetězec (v `fw.comp_def.layout`
je `enum_values` s položkou `{"label": "— dědí se ze systému —", "value": ""}`).
Handler `design_patch_entity` (modules/erp/api/router.py, větev „Default direct SQL")
skládal UPDATE z `field_changes` tak, jak přišly — prázdný řetězec šel rovnou
do sloupce typu boolean/numeric/date/time.

**Oprava u kořene** (commit 43303b6e, schválila Marti-AI msg 13324).
V `design_patch_entity`, hned za výpočtem `_table_cols` a PŘED rozvětvením fw / default,
se z `information_schema.columns` načtou typy sloupců cílové tabulky a každá hodnota,
která je prázdný řetězec a její sloupec NENÍ textový (text, character varying,
character, citext), se změní na NULL. Když se typy nepodaří zjistit, hodnoty projdou
beze změny (fallback si vyžádala Marti-AI — pojistka nesmí být sama zdrojem pádu).

**Proč u kořene a ne na obrazovce.** Platí pro každý výběr s prázdnou volbou nad
nečíselným/nelogickým sloupcem, ne jen pro tuhle obrazovku. K 22.8.2026 měla takové
výběry jediná obrazovka (hr.podminky_skupin_edit, 4 pole), ale oprava chrání i příští.

**Starší, slabší pojistka.** V `apps/api/static/erp/components/design_forms.js` je od
21.8.2026 pravidlo „prázdné číselné/časové/datumové pole a prázdný `erp-dropdown`
posílej jako null". Na tyhle comboboxy nesedlo (nemají tu CSS třídu), proto ta
serverová. Obě mohou existovat vedle sebe.

## 2) Nadpis panelu uvnitř mřížky musí zabrat celý řádek (opraveno 22.8.2026)

Panel, který má JEN listová pole (`useImplicitGrid`), si sám dělá CSS grid
`repeat(auto-fit, minmax(220px,1fr))`. Jeho `caption` se ale vykresloval jako
`display:block` — tedy jako obyčejná buňka mřížky: nadpis seděl v prvním sloupci
a pole se kolem něj rozsypala.

Oprava (commit 936240c3, schválila Marti-AI msg 13333): u obou větví panel captionu
(DESIGN i PROD) se přidá `grid-column:1 / -1`, ale JEN když `useImplicitGrid`.
Panely s kontejnerovými dětmi jedou flex-column, tam se nic nemění — proto nulový
dopad na CRM (Kontakt, Komunikace, Potenciál), kalkulace i přijaté objednávky.
Groupbox tenhle problém nikdy neměl, `grid-column:1/-1` má rovnou na wrapu.

## 3) Editační okno netahá hodnoty z data_setu, ale z tabulky

Pokus přidat do okna readonly „Skupina" přes počítaný sloupec v `fw.data_set` 218
NEFUNGOVAL — pole zůstalo prázdné. Editační okno si hodnoty bere přes design entity
fetch přímo z `entity_config` (schema + tabulka), takže počítané sloupce z data_setu
se do formuláře nedostanou. Pole bylo zase odebráno a data_set vrácen do původní
podoby. Kdo bude chtít v okně zobrazit dopočítanou hodnotu, musí ji přidat do
entity fetch, ne do data_setu.

## 4) Rozvržení okna Výchozí podmínky skupin (22.8.2026)

18 polí v jedné mřížce bylo nepřehledné, proto jsou pole rozdělena do čtyř panelů
(border_mode top, s nadpisem), pod panelem `client_panel` 1345 core 236:
Pracovní doba a docházka · Přesčasy a home office · Dovolená a zdraví · Peníze a daně.
Číslo řádku zůstalo v hlavičce. Nic se nemazalo ani nepřejmenovávalo, měnil se jen
`parent_comp_def_id` a `sort_order`.

