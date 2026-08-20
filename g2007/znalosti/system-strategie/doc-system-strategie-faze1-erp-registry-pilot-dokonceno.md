# Fáze 1 "kód jako data" DOKONČENA — první dva ERP piloty aktivní přes erp_registry

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Stav: HOTOVO A NASAZENO (31.7.2026, C23 + Marti)

Fáze 1 z vize `doc-system-strategie-vize-kod-jako-data-bez-restartu` je dokončená end-to-end. Mechanismus "DB řádek → exec() bez restartu API → self-test proti originálu → aktivace" je ověřený naostro na reálných datech.

## Co vzniklo

- **`g2007.python`** — tabulka pro spustitelné Python funkce (schéma: kod, popis, kategorie, zdroj, vedlejsi_ucinek, stav_zivota, verze, puvodni_umisteni, updated_by_*, created_by_text, timestamps).
- **`g2007.python_historie`** + `fn_python_archiv_pred_update` trigger — archivuje OLD řádek při každé změně `zdroj`/`stav_zivota` A auto-inkrementuje `verze` (ověřeno naostro: aktivace 1→2 proběhla automaticky, správně).
- **`modules/erp/api/erp_registry.py`** — loader modul (vzor 1:1 s Tool Factory `runtime.py`): `call(kod, *args)` natáhne aktivní (`stav_zivota='active'`) zdroj z DB, zkompiluje+exec() do izolovaného namespace, cachuje podle verze. `selftest_compare_any_stav(kod, legacy_fn, args)` pro srovnání DB-driven vs. legacy před aktivací.
- **`POST /api/v1/erp/app/erp_registry/selftest`** — admin-gated (`_require_admin`) endpoint, jen čte/srovnává, nic nezapisuje. Body: `{kod, args:[...]}`.

## Piloti (oba `stav_zivota='active'`, verze 2)

1. **`mzdy_absence_rows`** (`router.py:_mzdy_absence_rows`) — absence z docházky pro předzpracování mezd, čist-only.
2. **`mzdy_stravenky_rows`** (`router.py:_mzdy_stravenky_rows`) — nárok na stravenky, čist-only.

Oba: self-test PŘED aktivací (`shoda:true` na reálných datech, červenec 2026) i PO aktivaci/deployi delegát patche (`shoda:true` znovu, potvrzuje že live delegace `erp_registry.call(...)` funguje bez regrese).

## Jak to teď funguje

`router.py._mzdy_absence_rows()` a `._mzdy_stravenky_rows()` mají teď 2řádkové tělo: `from modules.erp.api import erp_registry as _ereg; return _ereg.call("<kod>", ...)`. Skutečná logika žije v `g2007.python`. Volací místa (3× u absence, 3× u stravenek) beze změny — pořád volají stejné jméno funkce.

**DŮLEŽITÉ pro příští úpravu těchto dvou funkcí:** needituj tělo v router.py (delegát) — uprav/přidej řádek v `g2007.python` (nová verze, self-test, pak `stav_zivota='active'`). Editace router.py by se přepsala příštím pullem a hlavně by ji delegát ignoroval.

## Commity

- `479f4052b` — g2007.python registrace + selftest endpoint (dormantní)
- `43e1fcc08` — registrace pilotu 2 do selftest dictu
- `00ab72e82` — aktivace: delegát patch obou pilotů na `erp_registry.call`

## Zbývá (další kroky mimo Fázi 1)

- `expected_version` optimistická pojistka pro `g2007.znalost` (a analogicky `g2007.python`, kde je verze skutečně enforced triggerem, takže riziko nižší) — patch připraven v `doc-system-g2007-expected-version-implementace-pripraveno`, čeká na nasazení.
- Fáze 2 (zobecnit governance lifecycle na ERP kód, ne jen AI nástroje), Fáze 3 (postupná migrace po doménách), Fáze 4 (čisté výpočty → PL/pgSQL) — viz vize doc.
- Generický `g2007.python_historie` prohlížeč (read UI) — zatím není, historie je jen v DB.

