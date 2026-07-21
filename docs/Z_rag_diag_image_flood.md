# RAG: obrázky z e-mailů zaplavovaly diag_log (storage_only fallback)

**Oblast:** system-g2007 · **Zapsal:** Claude-24 (Kristý), 21. 7. 2026 · **Oprava:** commit `b56e8f9b`

## Příznak
Popup „Nové chyby v systému" hlásil stovky errorů za 24 h, nejčastější modul `rag.service:upload_document`, a **diag log v UI nic neukázal.** Zpráva u chyb: *„Z dokumentu nebyl extrahován žádný text (prázdný nebo nekompatibilní formát)."*

## Příčina (dvě věci se sešly)
1. **Odjakživa mírně špatné chování:** vložené obrázky z e-mailů (loga z podpisu `eurosoft_logo_20let.png`, `image001.png`…) a přílohy se ukládají jako `public.documents` a RAG je zkouší indexovat. Obrázky jsou schválně v `EXTRACTABLE_EXTENSIONS` (kvůli OCR), ale `extract_text()` u log/fotek vrátí prázdno → `process_document()` házel `RuntimeError` → zaloguje se jako **error** do `fw.diag_log`.
2. **Zesílení:** sync e-mailů byl mrtvý 7.–18. 7. (TZ bug „No time zone found with key UTC+02:00"). Po opravě naběhl a **dohnal 11denní backlog** → 376 obrázků 20. 7. + 305 dnes → objem chyb přeskočil práh alarmu. Proto „minulý týden to nevyskakovalo" — mail nechodil, žádné nové obrázky.

## Oprava
`modules/rag/application/service.py`, `process_document()` (místo `if not text_content …`): prázdná extrakce **není chyba** → spadne na **storage_only** (uloží + „filename chunk" pro dohledání podle jména) a loguje `info`, ne error. OCR zůstává funkční tam, kde text najde. Řeší i obrázková PDF bez textové vrstvy.

## Znalost o RAG pipeline (pro příště)
- `upload_document()` → `Document` (`storage_only = not is_extractable(ext)`) → `process_document()`.
- `is_extractable()` = whitelist `EXTRACTABLE_EXTENSIONS`. `storage_only=True` obchází `extract_text()` a vyrobí 1 filename chunk (`_process_storage_only`).
- Extrakce → `chunk_text` → `embed_documents` (Voyage) → `document_chunks` + `document_vectors`.

## Znalost o diag_log + badge (gotchy pro diagnostiku)
- Tabulka **`fw.diag_log`**: `source` = jen `py`/`js` (NE modul!), **`module_id` = jméno loggeru** (např. `rag.service:upload_document`) — badge „nejčastější modul" bere `module_id`. Dedup přes `dedup_hash` + `occurrences`; `status` `new`→`resolved`/`acknowledged`/`ignored`; `stack`, `first_seen_at`, `last_seen_at`.
- Badge polling: `GET /api/v1/erp/diag-log/badge` (počítá otevřené = `status='new'` za 24 h). Detail: `GET /diag-log/events`. Resolve: `PATCH /diag-log/events/{id}/resolve` (nastaví `status`, `resolved_at/by`).
- **Proč UI diag log občas „nic neukáže":** tabulka je velká, dotazy trvají vteřiny → grid se nenačte/timeoutne. Rychlejší je číst přímo přes most (`db=pg`).
- Hromadné vyřešení: `UPDATE fw.diag_log SET status='resolved', resolved_at=now(), resolved_by_text=… WHERE module_id=… AND status='new'` přes most (schvalovací banner).

## Ponaučení
Netextové přílohy (obrázky, obrázková PDF) do RAG textového indexu nepatří — „nenašel jsem text" je normální stav, ne chyba. A když někde skokově naroste počet chyb, hledej **co se změnilo** (tady: oživení mrtvého mailu → backlog), ne jen ten samotný modul.
