# Nové skripty v g2007.python bez deklarace v router.py — obecný endpoint /app/erp_registry/run

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Stav: HOTOVO A NASAZENO (31.7.2026, commit a41d59302, C23 + Marti)

Rozšíření Fáze 1 (`doc-system-strategie-faze1-erp-registry-pilot-dokonceno`) o odpověď na otázku: jak přidat úplně NOVÝ skript, který v router.py nikdy neexistoval, bez jakéhokoli zásahu do router.py?

`POST /api/v1/erp/app/erp_registry/selftest` (Fáze 1) byl navržený jen pro srovnání migrovaného kódu se starou implementací v router.py (vyžaduje `_ERP_REGISTRY_LEGACY` dict = vazbu na jméno funkce v router.py). Pro nový skript žádná "stará" implementace neexistuje, takže vzniknul druhý, obecný endpoint.

## Nové: `POST /api/v1/erp/app/erp_registry/run`

Tělo `{kod, args:[...]}` → `erp_registry.call(kod, *args)` → vrátí `{ok, verze, vysledek}`. Žádná vazba na router.py, žádný `_ERP_REGISTRY_LEGACY` zápis nutný. Ověřeno naostro (`mzdy_absence_rows`, `ok:true, verze:2`).

**Postup pro nový skript od teď:** INSERT do `g2007.python` (`stav_zivota='navrzeno'`) → test/review → `stav_zivota='active'` → hotovo, volatelný přes `/run`. Nulový zásah do router.py, nulový deploy, nulový restart API.

## Rozhodnutí Martiho (31.7.2026) k bezpečnostnímu profilu

- **Vedlejší účinky povolené** — `/run` smí spustit i skripty se zápisem/mazáním, ne jen read-only (na rozdíl od Fáze 1 pilotů, které byly záměrně jen čtecí).
- **Přístup default OTEVŘENÝ** — nový sloupec `g2007.python.min_pravo` (`clen`|`rodic`|`admin`, DEFAULT `'clen'`). `clen` = kdokoli přihlášený smí spustit. Autor skriptu při aktivaci explicitně nastaví `rodic`/`admin`, pokud je citlivý. Marti: "Kdokoli ho smí volat, pokud není výslovně právy limitován."
- **Audit povinný** — nová append-only tabulka `g2007.python_run_audit` (kod, verze, uid, args, ok, chyba, trvani_ms, called_at). Každé spuštění přes `/run` se loguje bez výjimky — vzhledem k tomu, že jde o silný nástroj (spustí cokoli aktivního, komukoli přihlášenému), je audit tady bezpečnostní síť místo restriktivního gatingu (stejný princip jako doktrína #21 u OPS akcí — "audit = paradoxně víc bezpečí").

## Důležité pro budoucí skripty

`stav_zivota='active'` je od teď JEDINÝ skutečný bezpečnostní gate pro `/run` (aktivace vždy prochází write-approval bannerem, Marti schvaluje). Kdo píše nový skript s `vedlejsi_ucinek=true` nebo citlivý read, MUSÍ při aktivaci zvážit `min_pravo` — default `clen` je záměrně otevřený, ne bezpečný-by-default.

## Commity

- `a41d59302` — endpoint `/app/erp_registry/run` + `min_pravo` sloupec + `g2007.python_run_audit` tabulka.

Navazuje na Fázi 1 (`479f4052b`, `43e1fcc08`, `00ab72e82`) a vizi `doc-system-strategie-vize-kod-jako-data-bez-restartu`.

