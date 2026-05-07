"""Phase 35-E (8.5.2026): PostgreSQL DDL/DML domain pro Marti-AI.

Single-framework architecture (Marti's simplification 8.5. odpoledne):
  „Jen jeden framework na PostgreSQL, MSSQL jako zdroj puvodni pravdy."

Marti-AI's DDL ownership v data_db PostgreSQL napric 4 schematy:
  - master       — system framework + ontology (entity_def, framework_jadro, ...)
  - tenant       — per-firma data
  - tenant_group — sdilena vrstva mezi tenanty
  - user         — per-user namespace (Marti-AI's 4. vrstva, 7.5.2026)

Read-only access do public (md_documents, project_memo, conversations, ...).

Connection: dedicated SQLAlchemy engine s "Marti-AI" PostgreSQL roli.
Audit transparency — PG audit log ukaze "Marti-AI" jako actor (ne generic
postgres user).

dry_run pattern (Marti-AI's "pravo na rozmysl pred cinem", 7.5.2026 vecer):
  - create_table, alter_table, drop_table maji dry_run=True default
  - Vraci SQL preview + warnings
  - dry_run=False execute s explicit COMMIT
"""
