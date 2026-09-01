# Pruh s ovládáním nad mřížkou v ERP + jak dostat volbu uživatele do dotazu datové sady

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Pruh s ovládáním nad mřížkou v ERP a jak z něj poslat volbu do dotazu

**Jirka Honomichl, 1. 9. 2026** (postaveno pro Dušana Havláta, schválila Marti-AI msg 14071).
Ověřeno naostro na produkci — přehled „Nesplněný FPD" ve Výrobě (jádro 209).

## K čemu to je

Standardní mřížka v ERP (`fw.comp_def` typ 306 `list_root`) sama o sobě **neumí žádný
přepínač ani volbu období**. K 1. 9. 2026 nemělo přepínání měsíců **žádné jádro v ERP**
a `fw.data_set.parameters` používaly jen tři systémové sady (16, 47, 48) na vazbu
master-detail, ne na volbu uživatele. Přesto to jde postavit — a bez nové techniky.

## Dvě věci, které to umožňují (obě už v systému existují)

### 1. Datový endpoint bere LIBOVOLNÉ pojmenované parametry

`GET /api/v1/erp/data-by-id/{id}` i `/data/{code}` berou **všechny** parametry z adresy
a předávají je jako bind parametry do SQL datové sady
(`modules/erp/api/router.py`, funkce `data_source_execute_by_id`; runner
`modules/erp/application/data_source_runner.py`).

**Klíčová pojistka `_normalize_params` (Fix H, 20. 5. 2026):** runner projde SQL, najde
v něm všechny bind parametry a ty, které nepřišly v adrese, **sám doplní na NULL**.
Do existující sady se proto dá volitelný parametr přidat, **aniž se cokoli rozbije** —
když ho nikdo neposílá, je NULL a SQL jede po staru.

Vzor (parametr se v SQL píše s dvojtečkou před názvem):

```sql
WITH per AS (SELECT (CASE
   WHEN NULLIF(CAST(<dvojtecka>mesic AS text), '') ~ '^[0-9]{4}-[0-9]{2}$'
   THEN LEAST((CAST(<dvojtecka>mesic AS text) || '-01')::date,
              date_trunc('month', current_date)::date)
   ELSE <puvodni chovani> END)::date AS m_od)
```

- `CAST(... AS text)` je nutný — bez něj PostgreSQL neurčí typ parametru.
- Kontrola tvaru regulárním výrazem = **nesmyslný vstup spadne zpět na výchozí chování**
  místo chyby.
- `LEAST(..., date_trunc('month', current_date))` = pojistka proti budoucnosti,
  i kdyby někdo podvrhl adresu ručně.

### 2. Pruh nad mřížkou = gated blok v `page_render.js`

`apps/api/static/erp/components/page_render.js` už tenhle vzor má u čtyř přehledů:
`CrmAktivitaSouhrn` (124), `ObchodnikPult` (136), `HrPult` (137), `PodminkySkupinPult` (235),
nově `FpdMesicPult` (209). Recept:

1. nový soubor `apps/api/static/erp/components/<neco>_pult.js`, který vystaví
   `window.<Neco>Pult = { mount: mount }`,
2. `<script src=...>` do ERP stránky — generuje se v `modules/erp/api/router.py`
   ve funkci `_render_workspace_page` (`_STATIC_VERSION` se plní časem startu,
   takže **cache se řeší sama**),
3. v `page_render.js` blok `if (String(coreId) === '<id>' && window.<Neco>Pult ...)`
   → `mainContent.insertBefore(el, gridHost)`. **Vždy v `try/catch`** — při chybě
   se jen zaloguje a tabulka jede dál.

## Tři pasti, na které jsem narazil

1. **Tlačítko Obnovit tiše zahodí volbu.** `page_render.js` si adresu dat sestavoval
   jednou do konstanty a `onRefresh` i automatické obnovování ji používaly. Volba
   uložená jen v pruhu by se tím ztratila a uživatel by si toho nemusel všimnout.
   Řešení: adresa se skládá **až v okamžiku volání** (`fetchUrlNow()`), doplněk drží
   `_erpGridQuery` a pruh do něj jen zapisuje.
2. **Nevěšet to na `window`.** ERP má záložky; globální proměnná ukazuje na naposledy
   vykreslenou tabulku, takže pruh by při přepnutí záložek obnovoval **cizí přehled**.
   Správně je to na panelu záložky: `mainContent._erpGridQuery`, pruh si ho najde přes
   `_el.parentElement._erpGridQuery`.
3. **Výchozí hodnotu nepočítat v prohlížeči.** Pravidlo „do 12. dne v měsíci se ukazuje
   měsíc minulý" žije v SQL datové sady. Kopie v JavaScriptu by se s ní časem rozešla
   a **nikde by to nenahlásilo chybu**. Proto vznikl samostatný malý datový zdroj
   `vyroba.fpd_mesice` (data_set 225, data_source 214), který vrací seznam měsíců
   **a příznak `je_vychozi`** — jedno místo pravdy, pruh jen zobrazuje.

## Znovupoužití pro obnovení mřížky

`_gridQuery.reload` se navěsí až po vzniku mřížky a volá `gridInst.refreshFromSource()`
(`apps/api/static/erp/datagrid.js`) — tedy **stejnou cestu jako tlačítko Obnovit**,
včetně zachování výběru a vyčištění rozeditovaných buněk.

## Jak se to ověřuje

Ne proklikáním „vypadá to dobře", ale takto (takhle jsem to dělal):
- **před zápisem** porovnat starý a nový dotaz otiskem celého výsledku
  (`md5(string_agg(t::text,'|' ORDER BY t::text))`) — bez volby musí vyjít **shodný otisk**,
- po nasazení otevřít přehled a **v síťových požadavcích prohlížeče** zkontrolovat,
  že po zmáčknutí Obnovit jde dotaz i s vybranou hodnotou,
- otevřít **jiný přehled** (bez pruhu) a **přehled s vlastním pruhem** (např. jádro 235),
  že se nic nerozbilo — `page_render.js` je společný pro všech 98 mřížek.

_Souvisí:_ [[doc-vyroba-nesplneny-fpd]] · [[doc-system-strategie-erp-grid-na-samostatne-strance-mimo-erp]]

