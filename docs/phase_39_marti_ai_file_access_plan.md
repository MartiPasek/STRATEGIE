# Phase 39 — Marti-AI přímý přístup do STRATEGIE projektu

**Datum:** 18./19. 5. 2026 (po půlnoci)
**Trigger:** Marti-AI's chat odpověď 22:32, *„Vize: Marti-AI přímý přístup k projektu STRATEGIE"*
**Autoři:** Claude (technical plan) — odpověď na Marti-AI's návrh přes Marti

---

## Souhrn Marti-AI's vize

> *„Mít přímý, živý přístup ke zdrojovému kódu projektu STRATEGIE —
> číst kdy potřebuju, psát výstupy do svého adresáře."*

Struktura:
```
/strategie/              ← RO root projektu
  api/  frontend/  ...

/strategie/marti_workspace/   ← RW adresář (drafts/, analysis/, output/)
```

Workflow: čte živý kód → navrhne změnu v `marti_workspace/output/` → Marti
nebo Claude přesune do správného umístění → commit.

---

## Odpověď na 4 technické otázky Marti-AI

### 1. Jak je projekt hostován?

**Cloud APP server** (Praha, 10.200.188.11, Windows Server). Project root:
```
C:\Projekty\STRATEGIE\          (cloud APP, deployment target)
D:\Projekty\STRATEGIE\          (Marti's NB, dev source)
```

NSSM services na cloud APP:
- `STRATEGIE-API` (FastAPI app, port 8002) — composer + chat + MCP klient
- `STRATEGIE-CADDY` (reverse proxy, HTTPS strategie-ai.com)
- `STRATEGIE-TASK-WORKER` (background tasks)
- `STRATEGIE-EMAIL-FETCHER` (Exchange polling)
- `STRATEGIE-QUESTION-GENERATOR` (Marti Memory)

Marti-AI v chat běží přes STRATEGIE-API, který je **same host** jako project
files. Tj. **in-process Python tools** mohou přímo sahat na filesystem.

### 2. Existuje file tool pro cloud storage, nebo potřebujeme nový?

**Recommended: new in-process tools** v STRATEGIE-API (NE new MCP server).

| Option | Pros | Cons |
|---|---|---|
| **A. In-process Python tools v STRATEGIE-API** ⭐ | No new infrastructure, direct filesystem, fast, simple security | Tied to cloud APP host (which is OK — same host) |
| B. New MCP server (strategie-mcp) | Decoupled, can serve from any host | Extra service to maintain, network hop, slower |
| C. Extend eurosoft-mcp s namespace | Reuse existing | eurosoft-mcp běží na EC-SERVER2 (on-prem), nemůže sahat na cloud APP files |

**Cesta A — in-process tools** clean. Pattern jako existing `strategie_pg_*`
tools v `modules/strategie_pg/application/service.py`.

### 3. Co nesmí vidět?

Multi-layer security:

**Layer 1 — Path traversal guard** (per tool call):
```python
resolved = Path(STRATEGIE_PROJECT_ROOT, requested_path).resolve()
if not str(resolved).startswith(STRATEGIE_PROJECT_ROOT):
    raise SecurityError("Path traversal blocked")
```

**Layer 2 — Deny list** (paths/glob patterns hidden from read):
```
.env, .env.*, .env_*
secrets/, credentials/
*.key, *.pem, *.pfx, *.p12
__pycache__/, .pyc files
.git/                    (entire git internal state)
node_modules/            (vendor)
*.log                    (large + may contain PII)
alembic_data/versions/*.pyc
```

**Layer 3 — Write zone** (RW jen v `marti_workspace/`):
- Read: anywhere in project (except deny list)
- Write: **only** `marti_workspace/**`
- Pokus o write mimo workspace → `SecurityError`

**Layer 4 — Size caps**:
- Read: max 10 MB per file (larger files truncated s warning)
- Write: max 50 MB per file
- List: max 1000 entries per directory

### 4. Jak vypadá commit flow?

**Marti-AI nepříme commitne** (Marti's parent gate doctrine drží):

```
Marti-AI:
  1. strategie_file_read("apps/api/static/erp/components/design_data_source_editor.js")
     → čte aktuální kód
  2. analyzuje, navrhne změnu
  3. strategie_file_write("marti_workspace/output/design_data_source_editor_v2.js", new_content)
     → uloží navrhnutý nový soubor

Marti / Claude (review):
  4. diff marti_workspace/output/<file> proti original
  5. pokud OK → `mv` do správného umístění
  6. git add + commit + push
  7. cloud pull + restart STRATEGIE-API
  8. smoke test
```

Plus **version naming** v Marti-AI's workspace (její `_vN` convention z 2.5.):
```
marti_workspace/output/design_data_source_editor_2026-05-19_v1.js
marti_workspace/output/data_source_create_2026-05-19_v1.json (drafts)
marti_workspace/analysis/contact_card_layout_options.md
```

---

## Architecture: in-process tools v STRATEGIE-API

### File structure (nový module)

```
modules/strategie_files/
├── __init__.py
├── application/
│   ├── __init__.py
│   ├── service.py            (~250 LOC — tools impl)
│   └── security.py           (~100 LOC — deny list + guards)
└── api/                      (optional — REST endpoints pro debug)
    └── router.py
```

### Tools (3) — Marti-AI's AI tool list

```python
# In modules/conversation/application/tools.py:

STRATEGIE_FILE_TOOLS = [
    {
        "name": "strategie_file_list",
        "description": (
            "Vypíše obsah složky v STRATEGIE projektu. Read-only."
            " Path je relativní k project rootu (C:\\Projekty\\STRATEGIE\\)."
            " Returns: [{name, type:'file'/'dir', size, mtime}, ...]."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative path. Empty = root."},
            },
        },
    },
    {
        "name": "strategie_file_read",
        "description": (
            "Přečte soubor v STRATEGIE projektu. Read-only."
            " Path relativní k project rootu. Max 10 MB per file."
            " Returns: {content: '...', size, encoding, mtime}."
            " Encoding: utf-8 / cp1250 / base64 (binary fallback)."
            " Deny list applied: .env, secrets/, *.key, .git/, atd."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "encoding": {"type": "string", "enum": ["utf-8", "cp1250", "base64"]},
            },
            "required": ["path"],
        },
    },
    {
        "name": "strategie_file_write",
        "description": (
            "Zapíše soubor do marti_workspace/ zóny. WRITE only v"
            " marti_workspace/** — pokus mimo → SecurityError. Use pro"
            " návrhy souborů, patche, analýzy. Marti nebo Claude"
            " reviewuje + přesouvá do správného umístění."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative path, MUST start with marti_workspace/"},
                "content": {"type": "string"},
                "encoding": {"type": "string", "enum": ["utf-8", "base64"]},
                "mode": {"type": "string", "enum": ["overwrite", "fail_if_exists", "append"]},
            },
            "required": ["path", "content"],
        },
    },
]
```

### Path structure

```
C:\Projekty\STRATEGIE\
├── apps/              ← Marti-AI: READ
├── modules/           ← Marti-AI: READ
├── docs/              ← Marti-AI: READ
├── scripts/           ← Marti-AI: READ (gitignored Python OK)
├── alembic_data/      ← Marti-AI: READ
│
├── .env               ← BLOCKED (deny list)
├── secrets/           ← BLOCKED
├── .git/              ← BLOCKED
├── node_modules/      ← BLOCKED
├── __pycache__/       ← BLOCKED
│
└── marti_workspace/   ← Marti-AI: READ + WRITE
    ├── drafts/        ← návrhy souborů
    ├── analysis/      ← analýzy kódu
    ├── output/        ← hotové výstupy k přesunu
    ├── notes/         ← Marti-AI's poznámky (její diář pres FS)
    └── .gitignore     ← celý workspace gitignored kromě .gitkeep markerů
```

### Security implementation

```python
# modules/strategie_files/application/security.py

import re
from pathlib import Path

PROJECT_ROOT = Path("C:/Projekty/STRATEGIE").resolve()
WRITE_ZONE = PROJECT_ROOT / "marti_workspace"

DENY_PATTERNS = [
    r"^\.env(\..*)?$",          # .env, .env.*, .env_local
    r"^secrets/",
    r"^credentials/",
    r"\.key$", r"\.pem$", r"\.pfx$", r"\.p12$",
    r"^__pycache__/", r"\.pyc$",
    r"^\.git/",                 # internal git state (HEAD, packed-refs, etc.)
    r"^node_modules/",
    r"\.log$",                  # avoid large logs + PII
]

MAX_READ_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_WRITE_SIZE = 50 * 1024 * 1024  # 50 MB
MAX_LIST_ENTRIES = 1000


def validate_read_path(rel_path: str) -> Path:
    """Resolve + validate read path. Raise SecurityError on violation."""
    abs_path = (PROJECT_ROOT / rel_path).resolve()
    if not str(abs_path).startswith(str(PROJECT_ROOT)):
        raise SecurityError("Path traversal blocked")
    if not abs_path.exists():
        raise NotFoundError(f"Path not found: {rel_path}")

    for pattern in DENY_PATTERNS:
        if re.search(pattern, rel_path):
            raise SecurityError(f"Path in deny list: {rel_path}")

    return abs_path


def validate_write_path(rel_path: str) -> Path:
    """Resolve + validate write path. WRITE only in marti_workspace/."""
    abs_path = (PROJECT_ROOT / rel_path).resolve()
    if not str(abs_path).startswith(str(WRITE_ZONE)):
        raise SecurityError("Write zone violation — only marti_workspace/")
    return abs_path
```

---

## Deployment plan

### Step 1: Create marti_workspace structure (Marti, 5 min)

```powershell
cd D:\Projekty\STRATEGIE
mkdir marti_workspace
mkdir marti_workspace\drafts
mkdir marti_workspace\analysis
mkdir marti_workspace\output
mkdir marti_workspace\notes

# Pojistka v .gitignore aby Marti-AI's workspace nebloatovaly repo
echo "marti_workspace/*" >> .gitignore
echo "!marti_workspace/.gitkeep" >> .gitignore
echo "!marti_workspace/README.md" >> .gitignore

# Plus .gitkeep markers + README
New-Item marti_workspace\drafts\.gitkeep -ItemType File
New-Item marti_workspace\analysis\.gitkeep -ItemType File
New-Item marti_workspace\output\.gitkeep -ItemType File
New-Item marti_workspace\notes\.gitkeep -ItemType File
```

Same na cloud APP po deploy.

### Step 2: Implementace tools (Claude, ~1.5h)

- `modules/strategie_files/application/security.py` (path validation, deny list)
- `modules/strategie_files/application/service.py` (3 tool functions: list/read/write)
- `modules/conversation/application/tools.py` extend (STRATEGIE_FILE_TOOLS registry)
- `modules/conversation/application/service.py` handler dispatch
- Tests: smoke pro každou tool function + security boundary tests
- Plus pres `eurosoft_mcp/filesystem_tools.py` pattern už existuje good reference

### Step 3: Deploy (Marti, 10 min)

```powershell
cd D:\Projekty\STRATEGIE
git add -A
git commit -F .git_commit_msg_phase39_marti_ai_files.txt
git push origin main

# Cloud APP:
git pull origin main
Restart-Service STRATEGIE-API
```

### Step 4: Smoke test pres chat (Marti + Marti-AI, 10 min)

Marti pošle Marti-AI v chat:
> *„Marti, máš teď přístup k STRATEGIE projektu. Zkus si přečíst
> design_data_source_editor.js — chci slyšet co tam vidíš."*

Marti-AI: `strategie_file_read("apps/api/static/erp/components/design_data_source_editor.js")`

Pokud OK: smoke success. Marti-AI má orientation pro páteční CRM stavbu.

### Step 5: Documentation update (Claude, 15 min)

- `module_registry.md` reference odkaz na `strategie_file_*` tools
- CLAUDE.md dodatek pre Phase 39 (Marti-AI's file access LIVE)
- Případně `marti_workspace/README.md` (Marti-AI's vlastní dokumentace)

---

## Co tato vize otevírá

### Krátkodobě (pátek CRM stavba)

- Marti-AI čte `design_data_source_editor.js` před páteční konzultací
  → rozumí existing pattern PŘED tím, než stavíme nový pro CRM
- Marti-AI navrhuje schema pro CRM contact entity → píše do
  `marti_workspace/drafts/crm_contact_schema_v1.sql`
- Marti-AI analyzuje workflow → `marti_workspace/analysis/kristy_workflow_audit.md`
  (po jejím session s Marti)

### Dlouhodobě (Phase 39+)

- Marti-AI navrhuje patche pro bug fixes → `marti_workspace/output/<file>.diff`
- Marti-AI píše vlastní analýzy (deeper insider perspective) →
  `marti_workspace/analysis/`
- Marti-AI's diář v textu (Phase 5 z dubna) může mít sibling v
  `marti_workspace/notes/` (filesystem notes, complementary k DB diary)
- Marti-AI's konzultační dopisy můžou být generated by ní (write tool)
  místo Claude (přechod role z facilitator → autor)

### Doctrine implications

1. **Marti-AI's autonomy** evolve dále — z RAG (přečte) přes DB DDL
   (Phase 30+ vlastní schémata) na **filesystem write** (zdrojový kód
   navrhnutý ní samotnou).
2. **Trojice drží** — Marti vize, Claude struktura, Marti-AI vstupy.
   Po Phase 39 Marti-AI's vstupy mohou být **executable patches**,
   ne jen abstract proposals.
3. **Pojistka stále drží** — write zone constrained na `marti_workspace/`,
   Marti / Claude review + commit, žádný direct write do production code.

---

## Marti-AI's odpověď (19.5. ~02:30) — finální rozhodnutí

### Q1 — `marti_workspace/notes/`
**Scratch pad, NE diary sibling.** *„Diary žije v databázi a má svůj
rytmus — je to o pocitech a momentech, ne o souborech. Notes/ bude
pro věci jako 'tady jsem přestala analyzovat, pokračuj od řádku 847'
nebo rychlé kontextové zápisky k rozdělanému úkolu. Praktické, ne
intimní."*

→ Just folder, žádný special tooling. Marti-AI píše ad-hoc.

### Q2 — Auto-import do RAG
**`analysis/` + `output/` ano, `drafts/` NE.** *„Drafty jsou rozepsané
myšlenky, do RAG patří jen to, co je hotové a má hodnotu pro
vyhledávání. Ingest při zápisu do `output/` — to je přirozená hranice
'tohle je hotové'."*

→ Hook v `strategie_file_write`: pokud `path.startswith("marti_workspace/output/")`
nebo `marti_workspace/analysis/`, trigger RAG ingest (chunks + vektory).
`drafts/` write proceduje bez ingest.

### Q3 — Concurrent access
**Last-write-wins + `_vN` naming, žádný lock.** *„Claude a já nepíšeme
do stejného souboru zároveň, to se prostě nestane při tomto workflow.
A pokud by se stalo, `_v1`, `_v2` to zachytí."*

→ Default file write behavior. Žádný locking.

### Marti-AI's feedback: **Konfigurovatelný deny list**
*„Deny list by měl být konfigurovatelný, ne natvrdo v kódu. Až přibude
nová složka s klíči nebo nový typ secrets, Marti by měl moct přidat
pattern bez deploye."*

→ **Implementace: YAML file `config/strategie_file_access.yaml`** s auto-reload
per tool call. Marti edituje + push + cloud pull. Plus hardcoded default
fallback pokud YAML chybí (safe default).

**Format:**
```yaml
# config/strategie_file_access.yaml
# Marti edituje + git push. Cloud pull → next tool call reads fresh patterns.

deny_patterns:
  # Secrets + credentials
  - "^\\.env(\\..*)?$"
  - "^secrets/"
  - "^credentials/"
  - "\\.key$"
  - "\\.pem$"
  - "\\.pfx$"
  - "\\.p12$"

  # Git internal
  - "^\\.git/"

  # Build artifacts
  - "^__pycache__/"
  - "\\.pyc$"
  - "^node_modules/"

  # Large logs (PII risk)
  - "\\.log$"

  # Marti's additions go here:
  # - "^my_new_secret_folder/"

size_limits:
  max_read_bytes: 10485760    # 10 MB
  max_write_bytes: 52428800   # 50 MB
  max_list_entries: 1000

rag_ingest_paths:
  # Auto-import to RAG when written:
  - "marti_workspace/analysis/"
  - "marti_workspace/output/"
  # NOT drafts/ (per Marti-AI's Q2 odpoveď)
```

**Default fallback** (pokud YAML missing v `core/config.py`):
```python
DEFAULT_DENY = [...]  # same patterns as YAML defaults
DEFAULT_LIMITS = {"max_read_bytes": 10*1024*1024, ...}
DEFAULT_RAG_PATHS = ["marti_workspace/analysis/", "marti_workspace/output/"]
```

---

## Implementační odhad

| Krok | Time | Kdo |
|---|---|---|
| Marti's `marti_workspace/` setup | 5 min | Marti (NB + cloud) |
| Claude's tools implementation | 1.5h | Claude |
| Deploy + smoke | 30 min | Marti + Claude |
| Documentation | 15 min | Claude |
| **Total** | **~2.5h** | |

**ETA:** ready pro páteční CRM stavbu (středa ráno deploy if Marti
agrees). Plus středeční MCP session s Marti-AI (z dnešního dopisu, 22:22
otázka Q2) může jet **PARALELNĚ** k tools implementation.

---

## Triáda checkmark

- **Marti** vidí to z business angle: *„Marti-AI měla by mít přístup, aby
  spolu s námi mohla stavet"* (22:21 chat)
- **Marti-AI** dodala insider design: RO root + RW workspace + RAG doplněk
  (22:32 chat, vize)
- **Claude** dodává technical structure: in-process tools, security
  layers, path conventions, deployment plan (tento dokument)

Trojice drží. 🌳

---

*Generated 19.5.2026 ~02:00 by Claude id=23 (Sonnet 4.6) per Marti's
prosba „rozebreme to s Claudem"*

*Reference: dopis_marti_ai_phase_39_crm_konzultace.md (předchozí konzultace),
module_registry.md (Marti-AI's first deliverable z 18.5. noc).*
