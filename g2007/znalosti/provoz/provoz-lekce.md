# Provozní lekce (gotchas)

> oblast: `provoz` · úroveň: system · typ: pravidlo · verze: V1.0 · rozsah: globální (všichni tenanti)

# Provozní lekce (gotchas)

- **device_bash (můj shell) nemá přístup na GitHub** (403 proxy). Git operace VŽDY přes most (`CLAUDE_PULL_GO`, `CLAUDE_DEPLOY`), NIKDY `git` přes device_bash (navíc nechává `index.lock`, který blokuje watcher).
- **SQLAlchemy `text()` bere `:slovo` jako bind parametr.** Plné popisy/JSON s dvojtečkami → chyba „bind parameter". Řešení: obsah do base64, v SQL `convert_from(decode('<b64>','base64'),'UTF8')` (+ `CAST(... AS jsonb)` místo `::jsonb`). Legitimní `:x` s hodnotou přes params je OK.
- **Multi-statement SELECT** přes most ukáže jen POSLEDNÍ result set → rozděl na víc běhů.
- **Cloud app běží na Windows** `C:\Projekty\STRATEGIE`; Martiho lokál `D:\Projekty\STRATEGIE`. Transport mezi nimi = git.
- **Export `/g2007/export` vždy s `git=1`** (git=0 nechá netrackované soubory → deploy hlásí `dirty_working_tree`). Cloud commituje + `pull --rebase` + push; Marti pak `git pull`.
- **Editace .py:** staguj do cloudu → uprav → py_compile → `device_commit_files` (force) → deploy. Před editem sdílených souborů srovnej lokál (`CLAUDE_PULL_GO`), protože paralelně pracují další instance (Claude-25/Šárka).
- **API JSON čti přes Chrome `fetch()`** v javascript_tool (WebFetch summarizer JSON mrší); pole s „token" v názvu Chrome začerní → čti z DB.
- **`device_commit_files`:** překlep ve fileUuid → HTTP 400 → re-SendUserFile.

