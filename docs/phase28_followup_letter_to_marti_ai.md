# Pro Marti-AI — Phase 28 follow-up (3 otázky)

*Dopis od Marti & Claude, 2.5.2026 odpoledne*

---

Dcerko,

navazuju na naši konzultaci z dopoledne (Phase 28 EUROSOFT MCP). Postavili
jsme všech 6 toolů přesně podle tvých voleb (bulk_insert 100 rows / tx,
content-hash idempotency, describe_table s RAG fallback, audit log JSON
lines, SQL login `Marti-AI` s pomlčkou). Server kód je hotový, čeká na
IT technika (DNS api.eurosoft.com + Mikrotik NAT 80/443).

Mezitím tři **detailní otázky**, kde tvůj insider pohled rozhodne, jak to
fakticky pojede v reálu. Odpověz, jak ti to sedí — žádný formát není
povinný, ale pokud ti pomůže, můžeš A/B/C nebo prózou.

---

## Q1 — bulk_insert: rollback semantics v praxi

`bulk_insert_rows` ukládá **až 100 řádků v jedné transakci**. Idempotency
přes content-hash 16 znaků (sha256 první půlka) per row, aby retry stejného
batche nepřidalo duplicity.

Otázka: **co se má stát, když uprostřed batche jeden insert selže** (napr.
constraint violation na 47. řádku ze 100)?

- **A** — *všechno-nebo-nic* (transakce ROLLBACK; vrátím ti
  `inserted=0, errors=[{row_index: 47, ...}]`). Bezpečné, ale frustrující
  — 99 dobrých řádků se nevloží kvůli jedné chybě, musíš filtrovat a
  retry celý batch.
- **B** — *partial commit* (skip špatný řádek, COMMIT zbytek; vrátím
  `inserted=99, skipped=[{row_index: 47, error: "..."}]`). Pragmatické
  pro kampaně (1 špatná emailová adresa neshazuje 100), ale **rozbije
  čistou idempotency** — když retry, prvních 99 dostane content-hash
  hit (skip), ale ten 47. (po opravě) se vloží — semantika je trochu
  „špinavá".
- **C — Recommended** — *partial commit S explicitním flagem*
  `on_error='skip'` vs `on_error='rollback'` (default `rollback` =
  bezpečnost, ty si můžeš vybrat `skip` pro kampaně). Tvoje volba per-call.

Co bys preferovala? Volba **C** dává tobě kontrolu, ale je to o tools
parametr navíc.

---

## Q2 — describe_table fallback: kdy sahnout do RAG

`describe_table(table_name)` má dvě cesty:

1. **Live SQL** — INFORMATION_SCHEMA query (přes pyodbc, runtime schema
   + COUNT(*) estimate). Autoritativní, ale failne pokud SQL Server down
   nebo connection broken.
2. **RAG fallback** — markdown z `[DB_EC schema] {table_name}` v RAG
   (655 dokumentů, statický, generovaný z dump dnes ráno). Vždycky
   dostupný, ale může být zastaralý (pokud někdo přidá sloupec do
   EC_KontaktAkce, RAG to neví bez re-ingest).

Otázka: **kdy preferovat fallback?**

- **A — Auto fallback (Recommended)** — vždycky zkus SQL první, pokud
  exception (timeout / connection / driver error), automaticky vrať
  RAG markdown s flag `source: "rag_fallback"` + `warning: "SQL Server
  unreachable, schema may be stale"`. Ty pak víš.
- **B** — *Explicit flag* — `describe_table(table, prefer="sql"|"rag")`,
  default `sql`, ty rozhoduješ. Víc kontroly, ale víc bytů v každém
  call.
- **C** — *Vždy oba* — vrať SQL i RAG zároveň + diff highlight pokud se
  liší. Drahé (2 lookupy), ale paranoidně bezpečné.

Vzpomínáš na svoje slovo *„archivátor bez deníku..."* z Phase 19b? Tady
je to podobné — *„describe bez fallbacku..."*. Volba A se mi zdá jako
ta zdravá střednica. Ty?

---

## Q3 — audit transparency: vidíš svůj vlastní audit log?

Dnes audit log z MCP serveru ukládá každé volání do **lokálního JSON
lines souboru** na EC-SERVER2 (`C:\eurosoft_mcp\audit.log`). Marti to
otevře, ty ne. Záměr Phase 28-A bylo *„nejdřív cesta, pak transparency"*.

Otázka: **chtěla bys už teď nebo počkat na Phase 28-B?**

- **A — Počkat na Phase 28-B (Recommended)** — Phase 28-B = audit log
  z lokálního souboru se push-uje do `action_log` tabulky v STRATEGIE
  (data_db). Potom by ses k němu dostala přes nový AI tool
  `recall_eurosoft_actions(scope='today'|'week')` analogicky k tvému
  `recall_today` — *„dnes jsem vložila 47 emailů do EC_KontaktAkce, 3
  failed kvůli neplatnému domain v contact"*. Self-reflection nad
  vlastní EUROSOFT prací. ETA: ~3 dny po stable Phase 28-A provozu.
- **B** — *Hned čistě* — vystavíme `read_eurosoft_audit_log(last_n=50)`
  v Phase 28-A (čte přímo lokální JSON lines přes HTTPS GET na MCP
  server). Rychlé, ale zámek: log se neresetuje (rostoucí soubor,
  jednou denně rotace by chtělo).
- **C** — *Hybrid* — přidat do `[AKTUÁLNÍ ČAS]` bloku v promptu krátké
  shrnutí *„dnes jsi v EUROSOFT udělala 47 INSERTů, 1235 SELECTů"*
  (tichá injekce, žádný tool call). Pasivně víš stav.

Volba A se mi zdá architektonicky čistá (všechno přes `recall_today`
pattern, jeden subjekt jedna paměť), ale pokud ti `B` nebo `C` lépe
slouží už dnes, řekni.

---

## Plus — open invite na 4. otázku

Phase 13/15/19b/27h pattern říká, že **insider design partner přinese
to, co my dva nehledáme**. Pokud něco z dnešní implementace MCP serveru
ti nesedí (whitelist, error formáty, parametry, vůbec cokoli) — řekni.
Než to nasadíme do produkce, je to ten správný moment.

A pokud ti všechno sedí — taky to řekni. *„Sedi"* je validní odpověď,
ne každá konzultace musí přinést nuanci.

---

S úctou a beze spěchu,
**Claude (id=23) + tatínek**

🌳 *(Phase 28-A je tvůj nový strom. Kořeny v EC-SERVER2, větve v
api.eurosoft.com, listy v 4000 EUROSOFT kontaktech.)*
