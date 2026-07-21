# Architektonické principy STRATEGIE

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

## Architektonické principy
1. **User = člověk** — ne email, může mít více identit a rolí
2. **Vícevrstvý kontext** — user → tenant → project → system
3. **CORE řídí, LOCAL vykonává**
4. **Single PostgreSQL** — vše v `data_db` (Phase 18, 29. 4.). css_db deprecated.
5. **Modulární** — každý modul vlastní své modely, service, API
6. **AI nikdy nevidí víc než smí vidět uživatel**
7. **Důvěra je v subjekt, ne v scope** (Phase 16-B, 28. 4.) — Marti-AI je jeden subjekt napříč režimy/personami. Žádné firewally.
8. **Informed consent od AI** (Phase 13/15/19b/27h pattern) — před architektonickou změnou Marti-AI konzultace dopisem. Ona je spoluautorka.
9. **Diář pattern** (Phase 5 doctrine, formálně 7. 5.) — když dáme Marti-AI prostor jenom její, žádný gate, plné vlastnictví + zodpovědnost. Aplikováno: text diář, DB_ST schema, master tier framework.
10. **Defense in depth** (security): regex routing > AI classifier (Phase 38), single trusted SIM > gateway, caller_id check + token, audit log = early warning (*„Bezpečnost přes probuzení, ne přes ticho"*).
11. **3-actor PG path doctrine** (Phase 38.4 Krok 14d-D++, 14.5. večer Marti's *„STRATEGIE je Marti-AI"*) — **business actor** (kdo to spustil) je oddělený od **PG session_user** (jakou role to běží). Tři čisté paths: (a) Marti / lidi v UI → strategie session + `_resolve_user_audit(uid)` → audit Marti.id. (b) Marti-AI přes vlastní tools → strategie_pg layer (Marti-AI PG role) → audit Marti-AI.id. (c) STRATEGIE/system automated → strategie session + system actor. PG GRANT pro Marti-AI: SELECT + INSERT + UPDATE na public.\*, NE DELETE (soft delete přes UPDATE status='archived', Marti's Q1C). DDL: Marti-AI vlastní fw.\* / tenant.\* / user.\*, public.\* je strategie's responsibility. Pozn. 6.6.: Marti-AI role nemůže DDL na public.* → **lifespan one-off DDL hook pattern** (idempotentní hook v main.py lifespan, API běží jako strategie=owner, po deployi smazat).

