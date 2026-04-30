# Phase 24-G — UI Inkarnace Badge (živý log)

**Sub-fáze:** 24-G (UI hlavička: *„Mluvíš s: ..."*)
**Začátek:** 30. 4. 2026 ~07:15 ráno
**Status:** in-progress
**Důvod předřazení:** Marti's potřeba *„musím vidět v UI s kým mluvím"* — psychologická + diagnostická hodnota.
**Reference:** `docs/phase24_plan.md` v2 sekce 9 (24-G), `docs/phase24b_implementation_log.md` (předchozí, hotová)

---

## Cíl 24-G

Rozšířit hlavičku každého chatu o **4 osy identity**:

| Osa | Příklad |
|---|---|
| **Inkarnace** | Tvoje Marti pro Marti / Privát Marti / PravnikCZ |
| **Scope úroveň** | md1 work / md1 personal / md5 |
| **Režim** | task / oversight / personal |
| **Profese (pack)** | core / tech / pravnik_cz / psycholozka |

**Recommended UI styl:** primary chip s inkarnací + scope_label, tooltip s detaily mode + profese.

Příklad render:
- *„Mluvíš s: **Tvoje Marti pro Marti** · md1 work · EUROSOFT"*
- *„Mluvíš s: **Privát Marti** · md5 · personal"*
- *„Mluvíš s: **PravnikCZ** · core · task"*

---

## Postup (checklist)

- [ ] **Krok 1:** Backend helper `_build_incarnation_info(conversation_id)` — vrátí dict s 4 osami
- [ ] **Krok 2:** Rozšířit `ChatResponse`, `LastConversationResponse`, `ConversationListItem` schemas o pole `incarnation`
- [ ] **Krok 3:** Endpointy `/chat`, `/last`, `/load/{id}`, `/list` — naplnit incarnation info
- [ ] **Krok 4:** UI: rozšířit existující `active_pack_badge` o inkarnaci nebo přidat nový badge
- [ ] **Krok 5:** CSS: sepia palette pro primary chip + lighter variant pro tooltip
- [ ] **Krok 6:** JS helper `_setIncarnationUI(info)` — render hlavičky
- [ ] **Krok 7:** Smoke test (Marti default chat / personal mode / pack switch)
- [ ] **Krok 8:** Commit + push

---

## Decisions log (průběžně)

### Backend struktura — 1 helper, 1 dict

Místo 4 separátních fields v schemas používám **1 dict `incarnation`** s 4 keys:
```python
{
    "name": "Tvoje Marti pro Marti",  # primary label
    "scope_level": "md1",  # md1 / md2 / md3 / md4 / md5
    "scope_kind": "work",  # work / personal / null
    "scope_context": "EUROSOFT",  # tenant_name / "personal" / null
    "mode": "task",  # task / oversight / personal
    "profession": "core",  # core / tech / pravnik_cz / ...
}
```

Single source of truth — backend rozhodne, frontend renderuje.

### UI struktura — primary chip + tooltip

Primary chip: `Mluvíš s: <name> · <scope>`
Tooltip on hover: `režim: <mode> · profese: <profession>`

Důvod: Marti potřebuje **identita first** (s kým mluvím), detaily jsou diagnostika.

## Soubory změněné (Krok 1-6 hotové)

| Soubor | Změna |
|---|---|
| `modules/md_pyramid/application/service.py` | +`build_incarnation_info(conversation_id)` (~80 řádků, 6-axis dict) |
| `modules/conversation/api/schemas.py` | +`incarnation: dict \| None` v `ChatResponse` + `LastConversationResponse` |
| `modules/conversation/api/router.py` | +`_build_incarnation_safe()` helper + 3 callsites (`/chat`, `/last`, `/load`) + active_pack/pack_overlay_custom v `/load` (chyběly) |
| `apps/api/static/index.html` | CSS `.incarnation-badge` + `.privat` + `.personal` variants + HTML span + JS `_setIncarnationUI()` + 3 callsites volání vedle `_setActivePackUI` |

## Smoke test (Krok 7)

Pojď restart + chat:
```powershell
Restart-Service STRATEGIE-API
# Hard reload UI: Ctrl+Shift+R
# Otevři default Marti-AI chat -> badge "Mluvíš s: Tvoje Marti pro Marti · md1 work · EUROSOFT"
```

Multi-test: Marti-AI v personal mode → "Privát Marti · md5 · privát" (po `switch_role('personal')`).