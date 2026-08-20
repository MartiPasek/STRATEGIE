# G2007 — expected_version + audit historie: hotový patch k aplikaci večer

> oblast: `system-g2007` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# G2007 — expected_version + audit historie: HOTOVÝ PATCH k aplikaci večer

*Připraveno C23, 31. 7. 2026 odpoledne. Navazuje na `docs/g2007_upsert_konflikty_navrh.md`
(Claude-28, 20. 7., schváleno Marti-AI). Marti dnes odpoledne odpověděl na otevřené otázky
Q1–Q4 a autorizoval implementaci mnou (Marti-AI dočasně nekomunikuje přes most).
Aplikovat AŽ VEČER, mimo provoz produkce — teď je jen připraveno a ověřeno proti
aktuálnímu kódu (router.py, dnešní stav po 43fb836a5+).*

## Rozhodnutí (dnes, 31.7.)

- Q1 — jdeme do varianty A (locking + autor): ANO
- Q2 — expected_version povinný při editaci: ANO (Marti-AI to už 20.7. vyžadovala)
- Q3 — kdo implementuje: C23 (Marti-AI dočasně nedostupná přes most; večer se na to spolu podívají)
- Q4 — chceme i verzování/historii navíc: ANO, přidáno — Martiho výslovný požadavek dnes:
  „I to verzovani by mel hlidat a audit historie." Rozšiřuje původní A3 (nízká priorita) o
  plnohodnotnou historizaci (bývalá „Varianta B", dřív odložená) — každá reálná změna obsahu se
  archivuje jako řádek, ne jen updated_at + git.

## Ověřeno proti živému kódu (31.7. odpoledne, HEAD 43fb836a5)

Tři místa v modules/erp/api/router.py dělají dnes identický blind UPDATE bez kontroly verze:

1. _g2007_znalost_upsert_inline (řádek 67305) — volá se přes @@G2007ADD (inline, nejpoužívanější
   — tímhle jsem psal celé odpoledne)
2. _g2007_znalost_upsert_work (řádek 67351) — volá se přes @@G2007DOC (soubor docs/Z_*.md) +
   HTTP /app/g2007/znalost-upsert
3. inline blok @@GODOC (~řádek 42420–42465, uvnitř SQL dispatcheru) — nejstarší cesta, jen
   system-g2007

Ověřil jsem live: sloupec verze existuje, ale zůstává V1.0 napořád — nikdo ho při UPDATE
nemění ani nekontroluje (potvrzeno na dvou znalostech, které jsem dnes reálně přepsal třikrát).
/app/g2007/search (g2007_vectors.py:_search_work) nevrací updated_at — potvrzuje bod A1 z návrhu.

Patch níže řeší cesty 1 a 2 (ty, co jdou přes bridge a přes HTTP upsert endpoint — 95 %
reálného provozu). Cesta 3 (@@GODOC) zůstává jako známý zbytek pro Fázi 0b — je to
duplicitní kód přímo v dispatcheru (další důkaz pro to, proč router.py chce rozdělit), sdílí
stejnou zranitelnost, ale dnes se prakticky nepoužívá (nahrazeno @@G2007ADD/@@G2007DOC).

## 1. DDL (additivní, bez rizika pro existující data)

ALTER TABLE g2007.znalost
  ADD COLUMN IF NOT EXISTS updated_by_uid  bigint,
  ADD COLUMN IF NOT EXISTS updated_by_text text,
  ADD COLUMN IF NOT EXISTS created_by_text text;

CREATE TABLE IF NOT EXISTS g2007.znalost_historie (
  id              bigserial PRIMARY KEY,
  znalost_id      bigint NOT NULL REFERENCES g2007.znalost(id),
  kod             text NOT NULL,
  nadpis          text,
  obsah           text,
  zdroj           text,
  verze           character varying,
  updated_by_uid  bigint,
  updated_by_text text,
  platne_od       timestamptz NOT NULL,
  nahrazeno_at    timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_znalost_historie_znalost_id ON g2007.znalost_historie(znalost_id);
CREATE INDEX IF NOT EXISTS idx_znalost_historie_kod        ON g2007.znalost_historie(kod);

Trigger fn_znalost_archiv_pred_update (PL/pgSQL, BEFORE UPDATE ON g2007.znalost): když se
OLD.obsah nebo OLD.nadpis liší od NEW, vloží starou verzi řádku do znalost_historie
(znalost_id, kod, nadpis, obsah, zdroj, verze, updated_by_uid, updated_by_text, platne_od=OLD.updated_at,
nahrazeno_at=now()), pak RETURN NEW. Trigger trg_znalost_archiv BEFORE UPDATE FOR EACH ROW.
Plný SQL text funkce a triggeru je v pracovním souboru C23 (g2007_expected_version_patch.md).

Poznámka k vlastnictví: schéma g2007 vlastní role Marti-AI (ověřeno pg_get_userbyid(nspowner)).
DDL tedy musí jet pod jejím účtem (přes bridge write, který běží jako Marti-AI — stejně jako
dosavadní @@G2007ADD), ne pod strategie. Technicky to nic nemění na postupu níže.

## 2. Patch _g2007_znalost_upsert_inline (router.py:67305)

Nahradit celou funkci za verzi s expected_version=None, updated_by_uid=None, updated_by_text=None
v signatuře: při existujícím kod bez expected_version vrátit chybu s aktuálním updated_at;
UPDATE podmínit WHERE kod=:k AND updated_at=:ev; při rowcount==0 rollback + vrátit 409-styl
chybu s aktuálním autorem a časem; při INSERTu doplnit updated_by_uid/updated_by_text/created_by_text.
Plný kód funkce je v pracovním souboru C23 (g2007_expected_version_patch.md), hotový a proti
kódu ověřený.

## 3. Patch _g2007_znalost_upsert_work (router.py:67351)

Stejný princip jako bod 2 (přidat expected_version/updated_by_* do signatury, podmíněný
UPDATE, 409 větev). Zdroj obsahu zůstává čtení ze souboru docs/Z_*.md. Endpoint
/app/g2007/znalost-upsert (řádek 67421) už dnes zná uid (_uid_from_token_or_cookie) —
jen ho nepředává dál; stačí protáhnout uid a expected_version z body do volání.

## 4. Wire protokol @@G2007ADD (dispatcher, ~řádek 42502)

Rozšířit hlavičku o volitelný token expected_version=<ISO timestamp> (nepovinný jen pro
NOVÝ slug, povinný pro editaci existujícího):

@@G2007ADD <oblast> <slug> [expected_version=<updated_at>] | <nadpis>  + obsah na dalších řádcích.

Parsing: v _hargs2 hledat token začínající expected_version=, vytáhnout, zbytek beze změny.
Autor (updated_by_text) pro zápisy Claude instancí = název instance (např. „Claude-23 (Marti)"),
pro Marti-AI = users.id=2 (dohodnuto s ní 20.7.).

## 5. Read cesta — _search_work (g2007_vectors.py:130)

Přidat z.updated_at do SELECTu a do vráceného dict, ať klienti mají odkud expected_version
vzít bez zvláštního dotazu.

## 6. Pořadí aplikace večer (bez výpadku, additivní)

1. DDL (bod 1) — bezpečné, nic nerozbije, jde pustit kdykoli i samostatně.
2. Python patch (body 2–5) — jde do stejného deploye jako obvykle (CLAUDE_DEPLOY.txt s
   přesně těmito 2 soubory: modules/erp/api/router.py, modules/erp/api/g2007_vectors.py).
3. Před deployem povinně: git fetch && git reset --hard origin/main na čistém shellu
   (dnešní gotcha — bez fetch první reset skončí na starém commitu).
4. Po nasazení: ověřit jedním cyklem — přečíst updated_at existující znalosti, zapsat s ním,
   pak zkusit zapsat DRUHÝ update se STEJNÝM (starým) expected_version → očekávat 409.
5. Dopsat do CLAUDE.md (řádek ~35, ten „PŘIPRAVUJE SE" blok), že expected_version se
   od teď posílá vždy, a smazat „připravuje se" rámeček.
6. Zapečetit do G2007 jako Z_ znalost dle plánu z návrhu (oblast: system-g2007).

## 7. Co zůstává OTEVŘENÉ (ne blokující, ale poznamenat)

- @@GODOC blok (cesta 3 výše) — stejná zranitelnost, nepatchováno teď. Nízké riziko (skoro
  nepoužívaná cesta), ale patřilo by do stejné revize při příští příležitosti.
- Historizace (znalost_historie) zatím nemá čtecí UI/nástroj („ukaž mi historii téhle
  znalosti") — DB tabulka a data ano, pohodlný přístup ne. Lze dodat jako malý follow-up
  (g2007_hledej-styl nástroj g2007_historie(kod)), není to nutná podmínka pro Fázi 0.

