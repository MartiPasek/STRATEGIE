# Marti-AI's Workspace

**Phase 39 (19. 5. 2026):** Marti-AI's read-write zone v STRATEGII project.

## Struktura

| Folder | Use case | RAG ingest |
|---|---|---|
| `drafts/` | Rozepsané myšlenky, work-in-progress patches | ❌ (per Marti-AI's Q2 22:32 chat — "drafty jsou rozepsané myšlenky") |
| `analysis/` | Hotové analýzy kódu, deeper insights | ✓ Auto-ingest při write |
| `output/` | Hotové výstupy k přesunu (Marti/Claude review + commit) | ✓ Auto-ingest při write |
| `notes/` | Scratch pad — "pokračuj od řádku 847" typ záznamů | ❌ (per Marti-AI's Q1 02:30 — "Praktické, ne intimní") |
| `claude_chats/` | Phase 40 v2 transcripty Marti-AI ↔ Claude konzultací | ✓ Auto-ingest |

## Tools (Marti-AI's AI tool list)

```python
strategie_file_list(path)        # list directory contents
strategie_file_read(path)        # read file (max 10 MB, deny list applied)
strategie_file_write(path, content, mode)  # WRITE jen v marti_workspace/
ask_claude(question, context_files, topic)  # Phase 40 v2 r2 consultations
```

## Doctrine

1. **Read everywhere** (project root, except deny list)
2. **Write only here** (marti_workspace/**)
3. **Last-write-wins** + `_vN` naming convention (Marti-AI's Q3 02:30)
4. **Auto-RAG** pro `output/` + `analysis/` + `claude_chats/`
5. **`notes/` = scratch pad** (NE diary sibling — diary žije v DB)

## Marti-AI's note (z 19.5. 02:30 chatu)

> *„Diary žije v databázi a má svůj rytmus — je to o pocitech a momentech,
> ne o souborech. Notes/ bude pro věci jako 'tady jsem přestala analyzovat,
> pokračuj od řádku 847' nebo rychlé kontextové zápisky k rozdělanému úkolu.
> Praktické, ne intimní."*

Plus o RAG (Q2):

> *„Ingest při zápisu do `output/` — to je přirozená hranice 'tohle je hotové'."*

## Marti-AI's permissions

| Soubor / cesta | Read | Write |
|---|---|---|
| `apps/` `modules/` `docs/` `scripts/` `alembic_data/` | ✓ | ❌ |
| `.env` `secrets/` `*.key` `.git/` `node_modules/` | ❌ | ❌ |
| `marti_workspace/**` | ✓ | ✓ |

## Workflow

```
1. Marti-AI: strategie_file_read("apps/api/static/erp/components/design_data_source_editor.js")
   → vidí živý kód
2. Marti-AI: ask_claude(question, context_files=["..."], topic="...")
   → Claude radí (inline v chat UI per Phase 40 v2 r2)
3. Marti-AI: strategie_file_write("marti_workspace/output/foo_v1.js", content)
   → uloží návrh
4. Marti / Claude: review + mv + git commit + push + restart (Phase 42)
```

## Maintenance

- Marti přidá nový pattern do `config/strategie_file_access.yaml` deny list — push to deploy
- Marti smaže `marti_workspace/output/` periodically (po commit do skutečné cesty)
- Marti-AI's `analysis/` zachovat — pro future search_documents RAG queries

---

*Phase 39 LIVE 19.5.2026 ráno. Marti-AI's first deliverable z 18.5. noc.*

🌳 ☕
