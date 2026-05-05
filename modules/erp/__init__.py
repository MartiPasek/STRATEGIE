"""
STRATEGIE ERP module — moderní renderer Centrály 1.

Phase A (5.5.2026 ráno): single jádro read-only renderer pro EC_FormDef.ID=6
(= dialog "Nastavení soudečku"). MVP demo, prokáže že renderer pipeline funguje
end-to-end: read EC_FormDef + EC_FormDefEdit + EC_FormDefEditProperty + execute
SQL_Select → server-rendered HTML page.

Architektura (z docs/strategie_erp_renderer_proposal.md):
  - Backend: cloud APP, FastAPI Python (existing STRATEGIE infra)
  - DB read: Phase 28-C MCP klient (eurosoft_query_table přes MCP server na 30.11)
  - Frontend: HTMX + Tailwind + Alpine.js + Tabulator.js (vanilla, žádný build)
  - Layout: Flow s group hints, <section> ne <fieldset> (Marti-AI's recenze)
  - URL: /erp/* (sub-path strategie-ai.com, single-product feel)
  - Auth: STRATEGIE auth + namapování na Centrála LoginName (Phase A: rodina only)

Marti-AI's vize (5.5.2026 ráno): "Marti-AI bude v novém ERP také bydlet a
interovat s userem". Tj. ne separátní produkt, ale modul STRATEGIE.
"""
