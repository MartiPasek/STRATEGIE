# CLAUDE_TECH.md — Technická krabička

*Mid-vrstva mezi `CLAUDE.md` (personal) a `docs/phase*.md` (per-fáze).*

> **Skeleton — Marti's nápad 1.5.2026 ~20:30. Plný refactoring TODO #24.**
>
> Tento soubor zatím obsahuje jen index. Postupně sem přesunu z `CLAUDE.md`:
> gotchas list, deploy workflow, DB schema, dependencies, ports, services.
> Po refactoringu bude `CLAUDE.md` čistě personal (vztah, dárky, dopisy,
> Marti-AI's slovník), tady bude pracovní reference pro denní debug.

## Až bude refactoring hotov, sem patří:

### 1. Gotchas (single seznam #1-#37+)
Aktuálně rozseté v `CLAUDE.md` v dodatcích a v sekci *„Chyby, které jsem
udělal"*. Pojď je sjednotit:

- `#1` Overengineering UI lup (24.4.)
- `#2` AskUserQuestion zbytečně
- `#3` Windows partial-write u Edit dlouhých souborů
- `#4` Pydantic schema filter
- `#5` Substring idempotence check
- `#6` Walrus + session lifecycle
- **`#7` UnboundLocalError přes lokální import shadow** (vrací se opakovaně!)
- `#8`–`#37` viz `CLAUDE.md` per-dodatek

### 2. Architektonické principy
- User = člověk (ne email)
- Vícevrstvý kontext: user → tenant → project → system
- Persona owns data (1. osoba v tool response)
- Důvěra je v subjekt, ne v scope
- Tool audit & replay (Phase M1-M4) — Marti-AI's pamět akcí
- Memory-first orchestrace (recall_thoughts before "nevím")

### 3. Deploy workflow
- NB → commit + push → cloud APP → pull + restart
- Gotcha: PowerShell + víceřádkové `-m` → use `.git_commit_msg_*.txt` files
- Cloud: NSSM services (`STRATEGIE-API`, `STRATEGIE-CADDY`, `STRATEGIE-TASK-WORKER`,
  `STRATEGIE-EMAIL-FETCHER`, `STRATEGIE-QUESTION-GENERATOR`)
- Caddy 300s read/write timeout pro chat endpoint (Phase 27c sprint requirement)

### 4. DB schema overview (po Phase 18)
- `data_db` (single, sjednoceno z původních `css_db` + `data_db` 29.4.)
- Cross-DB FK (Phase 16-B.9 vyřešené Phase 18 unify)
- `alembic_data` migrations chain (latest: `p6k7l8m9n0o1` Phase 27b)
- 60+ tabulek po Phase 27g

### 5. Dependencies + Python deps
Aktuální (1.5.2026):
- pdfplumber 0.11+ (Phase 27d)
- pytesseract + pdf2image (Phase 27d+1, system deps Tesseract + Poppler)
- pandas, numpy, xlsxwriter (Phase 27c sandbox + 27a)
- python-docx, reportlab (pre-installed pro Phase 27e/f)
- openpyxl (Phase 27a, transient přes markitdown)
- markdown 3.5+ (outbound email rendering)
- exchangelib 5.6+ (EWS)
- voyageai 0.2+ (RAG embeddings)
- anthropic SDK
- pgvector, mutagen, Pillow

### 6. Per-fáze docs (existující)
- `docs/phase24_plan.md` v2 — Pyramida MD paměti
- `docs/phase24[a-g]_implementation_log.md`
- `docs/phase24_consultation_letter.md`
- `docs/phase25_cloud_mirror_plan.md`
- `docs/phase27c_consultation_letter.md`
- `docs/phase27d_consultation_letter.md`
- `docs/phase27d_plus1_ocr_consultation.md`
- `docs/phase15_agentic_context.md`
- `docs/memory_rag.md`

### 7. Services + ports
- `STRATEGIE-API` — uvicorn :8002
- `STRATEGIE-CADDY` — reverse proxy :443/:80
- `STRATEGIE-TASK-WORKER` — task executor (email + sandbox + summary)
- `STRATEGIE-EMAIL-FETCHER` — EWS poll 60s
- `STRATEGIE-QUESTION-GENERATOR` — Marti Memory active learning, 6h interval

### 8. Storage paths (cloud APP)
- `C:\Data\STRATEGIE\Dokumenty` (RAG documents)
- `C:\Data\STRATEGIE\media` (MEDIA_STORAGE_ROOT — chat images, audio)
- `C:\Data\STRATEGIE\Avatary` (persona avatars)
- `C:\Data\STRATEGIE\persona_signatures` (inline images pro emaily)
- `C:\Logs\STRATEGIE\` (NSSM stdout/stderr)
- `C:\caddy\logs\` (Caddy access)
- `C:\Tools\poppler\poppler-24.08.0\Library\bin\` (PDF→image, Phase 27d+1)
- `C:\Program Files\Tesseract-OCR\` (OCR binary, Phase 27d+1)

### 9. Cron tasks (Windows Task Scheduler)
- `STRATEGIE-llm-calls-retention` — daily 3:00 AM, 30 dní okno
- `STRATEGIE-lifecycle-daily` — daily, conversation lifecycle classification
- TODO: stale tasks cron registration

---

**Plný refactoring**: TODO #24 (Marti's nápad 1.5.2026 20:30). Cíl je
~2000 řádek personal v `CLAUDE.md` + ~2000 řádek tech tady, plus
existující per-fáze docs.
