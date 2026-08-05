# Oddělený adresář `static_db` — cutover runbook (aktivace s Martim)

**Připravil:** Claude‑24 (Kristý) · **Datum:** 5. 8. 2026 · **Schválil směr:** Marti (5.8. „zvláštní adresář pro DB obraz")
**Cíl:** DB artefakty (11) přesunout z `apps/api/static/` do `apps/api/static_db/` = gitignorovaný RO obraz z `g2007.soubor`. Prevence „dvou zdrojů pravdy" strukturálně.

## Co je připravené (v lokálním working tree, NEnasazeno)
- **`apps/api/main.py`** — `static_db_dir` + helper `_resolve_static(fname)` (najde soubor nejdřív v `static_db/`, jinak `static/`). Přepojeno **8 přímých rout** (mobile, vyroba, foto, overit, dochazka‑zakazky, dochazka‑po‑zakazkach, dochazka‑opravy, registr‑absenci) + **`index.html`** (4 místa přes resolver) + **`_web_subpage`** (pokrývá `marti.html` na `/web/marti` i genuine web stránky). `py_compile` OK.
- **`modules/erp/api/router.py`** — `@@G2007PUBLISH` self‑test `_url_map6` doplněn o `static_db/` cesty (transition‑safe: fungují stará i nová cesta). `py_compile` OK.
- **`.gitignore`** — přidán celý `apps/api/static_db/`.
- **`martinky.html`** — bez route (osiřelý); přenese se jen migrací `kod` + gitignore, žádná změna kódu. (Samostatná otázka: ověřit/vyřadit jako mrtvý.)

## Klíč: proč je cutover plynulý
`_resolve_static` servíruje soubor **ať je kdekoli** (`static_db/` má přednost, jinak `static/`). Proto:
- Kód lze nasadit **dřív** — dokud je `static_db/` prázdný a `kod` míří na `static/`, jede vše ze `static/` beze změny (zpětně kompatibilní).
- Přepnutí nastane, až materializace zapíše soubory do `static_db/`. Žádný „flag day".

## Postup (aktivace)

### Krok 1 — nasadit kód (bezpečné, beze změny chování)
Commit + push (přes MOST) `apps/api/main.py`, `modules/erp/api/router.py`, `.gitignore`. Cloud pull + restart. Materializace stále píše do `static/` (kod zatím `apps/api/static/…`), resolver servíruje ze `static/`. **Nic se navenek nezmění.** Ověřit, že appka jede normálně.

### Krok 2 — DB migrace `kod` (přepnutí zdroje), přes MOST `db=pg` (konstruktivní UPDATE)
```sql
UPDATE g2007.soubor
SET kod = 'apps/api/static_db/' || substring(kod FROM length('apps/api/static/') + 1)
WHERE kod LIKE 'apps/api/static/%' AND typ = 'artefakt';
```
Dotkne se přesně 11 artefaktů (fragmenty `typ='zdroj'` mobile_parts se NEtýkají). Ověřit čtením: `SELECT kod FROM g2007.soubor WHERE typ='artefakt' ORDER BY kod;` → všech 11 má `apps/api/static_db/`.

### Krok 3 — restart API → materializace do `static_db/`
`Restart-Service STRATEGIE-API` (přes ops most / UI). Materializace přečte nové `kod` a zapíše 11 souborů do `apps/api/static_db/`. Resolver je od teď servíruje odtud. V logu: `[lifespan] g2007 artefakty materializovany: written=11 …`.

### Krok 4 — ověření
- Stránky se načítají: `/mobile`, `/`, `/vyroba`, `/foto`, `/overit`, `/dochazka-zakazky`, `/dochazka-po-zakazkach`, `/dochazka-opravy`, `/registr-absenci`, `/web/marti`.
- Otisky souborů v `static_db/` sedí na `md5(obsah)` v DB.
- `@@G2007PUBLISH apps/api/static_db/mobile.html` projde (self‑test OK — url_map má novou cestu).
- `git status` čistý (`static_db/` je gitignorovaný).

### Krok 5 — úklid
- Smazat staré kopie 11 souborů v `apps/api/static/` (na cloudu; už se neservírují). Genuine statické soubory v `static/` zůstávají.
- Volitelně `static_db/` NTFS **read‑only** (jako naše RO zóny) — zdůrazní „needituj na disku, edituj v DB".
- Staré individuální řádky v `.gitignore` (`apps/api/static/*.html`) lze později uklidit (teď neškodí).

### Rollback
- Kód: `git revert` commitu z Kroku 1.
- `kod` v DB: opačný UPDATE (`static_db/` → `static/`), pak restart (materializace zpět do `static/`). Resolver mezitím servíruje z `static/` (staré kopie tam do úklidu jsou).

## Poznámky / rozhodnutí
- `index.html` (SPA kořen) se přesouvá taky — přes resolver, s extra ověřením „/" po restartu. Když by dělal problém, resolver umožní okamžitý fallback (nechat `index.html` ve `static/`).
- `mobile.html` je skládaný — po migraci `@@G2007SESTAV`/`@@G2007PUBLISH` píše do `static_db/` (kod‑driven); fragmenty zůstávají beze změny.
- `martinky.html` — ověřit, zda se vůbec používá; případně vyřadit z `g2007` (samostatně).
- Prevence: tímto adresářem je „soubor v gitu I v DB" strukturálně těžší → hlídač z předchozího návrhu **není potřeba**.
