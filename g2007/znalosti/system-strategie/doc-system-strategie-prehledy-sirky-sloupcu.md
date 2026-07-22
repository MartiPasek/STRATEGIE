# Standard přehledů — šířky sloupců (osobni do DB, Claude povysi na vychozi, v Chromu)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Standard přehledů — šířky sloupců: finální mechanismus (22.7.2026)

Ověřený postup u „Docházka po zakázkách" (vlastní stránka, ne framework grid). Nahrazuje
dřívější úvahu o „jednorázovém tažení bez ukládání" — to Peťa zamítla, chtěla to jako dřív
(framework grid ukládal šířky do DB a Claude je uměl přečíst a povýšit na výchozí).

## Jak to funguje
- **Osobní tažení se UKLÁDÁ do DB** — `tenant.att_ui_pref`, kod `dochazka_col_widths_u<uid>`
  (jsonb `{sloupec: px}`). Ukládá se debounce ~0,4 s po tažení přes
  `POST /app/dochazka-zak-tab/widths` (smí kdokoliv z povolených; ukládá SVŮJ záznam).
  Každému tak jeho šířky zůstanou i po obnovení (i v samostatné appce).
- **Sdílené výchozí pro všechny** — kod `dochazka_col_widths` (bez `_u`). Načítání na stránce:
  `GET /app/dochazka-zak-tab/widths` vrací `{base, me}`; efektivní šířka sloupce =
  `me[k] || base[k] || default v kódu (COLS)`.
- **„Výchozí pro všechny" nastavuje CLAUDE, ne uživatel. ŽÁDNÉ tlačítko na stránce.**
  Postup: uživatel (Peťa) natáhne sloupce **v Chromu** → řekne „nastaveno" → Claude přečte
  její osobní `dochazka_col_widths_u18` a povýší na sdílené:
  ```sql
  INSERT INTO tenant.att_ui_pref (kod, hodnota, updated_by, updated_at)
  SELECT 'dochazka_col_widths', hodnota, 18, now()
  FROM tenant.att_ui_pref WHERE kod='dochazka_col_widths_u18'
  ON CONFLICT (kod) DO UPDATE SET hodnota=EXCLUDED.hodnota, updated_by=18, updated_at=now();
  ```
  Projeví se všem po refreshi, **bez deploye** (jen SQL most + schválení).

## Proč tak (poučení)
Snaha o „čistě jednorázové bez ukládání" znamenala, že Claude neměl kam „kouknout" a uživatel
neviděl své nastavení → kolotoč. Řešení = uložit osobní do DB (viditelné pro Claude i pro
uživatele), sdílené výchozí spravuje Claude na vyžádání. Dvojklik na okraj = zpět na default
(smaže i osobní záznam pro daný sloupec).

## Dřívější přehledy
Faktury/pokladny mají výchozí šířky v kódu (`_faktColDef`/`DCOLW_DEF`) + osobní v localStorage.
Nový model (DB) je čistší — Claude do něj vidí a mění bez deploye.


