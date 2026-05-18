# Phase 42 — Marti-AI autonomous deploy + restart

**Datum:** 19. 5. 2026 (~03:00 ráno)
**Trigger:** Marti's chat: *„To spolu dokazete i restart API na cloudu?"*
**Use case:** Marti-AI + Claude (via API, Phase 40) navrhnou patch
v `marti_workspace/output/`. Bez Marti's přítomnosti se patch musí
deploynout: copy → commit → push → cloud pull → restart.

---

## Tři vrstvy autonomie (Marti's volba)

### Vrstva 1 — Restart-only (low risk, recommended start)

**Marti-AI's new tool:** `strategie_api_restart(reason)`

Backend:
```python
async def _handle_strategie_api_restart(args, ctx):
    """Restart STRATEGIE-API service na cloud APP."""
    reason = args["reason"]
    persona_id = ctx["persona_id"]

    # Gate: jen default Marti-AI persona (id=1 v STRATEGIE tenant)
    if persona_id != 1:
        raise PermissionError("Restart jen default Marti-AI persona")

    # Audit log PRED restart
    log_diag_event({
        "level": "warn",
        "source": "marti_ai",
        "module_id": "strategie_api_restart",
        "message": f"Marti-AI requested restart: {reason}",
    })

    # Trigger restart (Restart-Service equivalent na Linux subprocess)
    # POZOR: tento process je STRATEGIE-API itself. Restart_self trick:
    #   touch core/restart_marker → STRATEGIE-API watch sees marker →
    #   gracefully exits → NSSM auto-restarts
    Path("core/restart_marker").touch()

    return {
        "ok": True,
        "message": "Restart triggered. Service back online za ~15 sekund.",
        "reason": reason,
    }
```

**NSSM auto-restart** — STRATEGIE-API service má NSSM `Restart=Always`,
takže když process exits, NSSM ho restartne. *„Self-touch restart"*
pattern.

**Alternatively:** subprocess.run(["powershell", "-Command",
"Restart-Service STRATEGIE-API"]) — ale to vyžaduje admin permissions
nebo pres SCM API.

**Use case:**
```
Marti (NB): git pull origin main + git push (zítrejší změny)
Marti-AI (in chat with Kristý):
  Marti-AI: strategie_api_restart(reason="po Marti's commit aaXXXX")
  → service restarts za 15 sec, latest code LIVE
```

**Risk:** žádný — service restart je idempotent, audit log explicit.

**Impl time:** 30 min (1 tool + handler + restart_marker file watch).

---

### Vrstva 2 — Deploy s SMS parent gate (medium risk, controlled autonomy)

**Marti-AI's new tool:** `propose_deployment(file_path, target_path, summary)`

Workflow:
```
1. Marti-AI: napíše patch do marti_workspace/output/foo_v1.js
2. Marti-AI: propose_deployment(
     file_path="marti_workspace/output/foo_v1.js",
     target_path="apps/api/static/erp/components/foo.js",
     summary="Fix grid row 24 missing — pridana defensive null check"
   )

3. Backend (STRATEGIE-API):
   a. Generate diff (current vs proposed)
   b. Send SMS to Marti:
      "🤖 Marti-AI navrhuje deploy:
       Cíl: foo.js (changes: 3 lines)
       Důvod: Fix grid row 24 missing — pridana defensive null check
       Diff preview: <url-to-diff-view>
       Reply OK = deploy. Reply NO = cancel. (timeout 2h)"
   c. Store proposed deployment in fw.pending_deployments (s expiry 2h)
   d. Return: {ok: true, queue_id: 42, sms_sent: true}

4. Marti reply SMS "OK" / "NO":
   - Hook v sms_inbox handler:
     a. Match phone = Marti
     b. Match recent pending_deployment in fw.pending_deployments
     c. If "OK":
        i. Copy file_path → target_path
        ii. git add + commit (auto message: "auto-deploy: " + summary)
        iii. git push origin main
        iv. cloud APP self-restart (same as Vrstva 1)
        v. Audit log + SMS confirmation back to Marti
     d. If "NO": cancel + audit log

5. Marti-AI on next turn: check_deployment_status(queue_id=42)
   → returns "approved" / "rejected" / "pending"
```

**Plus pre-approved patterns** (Marti's config):
```yaml
# config/auto_deploy_rules.yaml
auto_approve_patterns:
  # CSS-only changes (no JS, no Python)
  - target_glob: "apps/api/static/**/*.css"
    file_extensions: [".css"]

  # Marti-AI's notes additions
  - target_glob: "marti_workspace/notes/**"
    file_extensions: [".md", ".txt"]

require_parent_sms:
  # Everything else default
  - target_glob: "apps/api/static/**/*.js"
  - target_glob: "modules/**/*.py"
  - target_glob: "alembic_data/**"
```

Plus **NEVER auto-deploy:**
- `.env`
- `config/auto_deploy_rules.yaml` itself (chicken-egg)
- `core/database*.py` (DB connection settings)
- `alembic_*` (DB migrations require explicit approval)

**Risk:** medium. Pojistka přes SMS gate, but Marti-AI's mistake +
Marti's reflex "OK" by mohlo deploynut buggy code. Plus per-file diff
review by Marti is best practice.

**Impl time:** 2h (tool + sms_inbox hook + diff view + audit + rules).

---

### Vrstva 3 — Full automation (high autonomy, future)

**Use case:** Marti-AI + Claude (přes API) autonomously deploy changes
based on pre-defined rules. Marti notified post-facto via daily
digest.

Žádný SMS gate per deploy. Audit log only.

**Risk:** high. Marti's full trust required. **Not recommended for
Phase 42** — would require months of validated track record from
Vrstva 2 first.

---

## Recommended start: Vrstva 1 + Vrstva 2 v Phase 42

**Implementace pořadí:**

| Phase | Time | Capability |
|---|---|---|
| 42a — Restart tool | 30 min | Marti-AI restartne service po Marti's commit (low risk) |
| 42b — propose_deployment tool | 2h | Marti-AI navrhuje deploy → SMS Marti → OK/NO → execute |
| 42c — Auto-approve rules | 30 min | Pre-defined patterns auto-bypass SMS (CSS, notes) |

**Total:** 3h impl. Ready pred Marti's Praze 20.5. ráno.

---

## Konkrétní scénář — Marti's absence

```
Pondělí 20.5. 14:30 — Marti v Praze, Marti-AI + Kristý v EUROSOFT:

Kristý: "Tahle CRM kontakt karta nemá ikonu telefonu — vypadá divně."
Marti-AI: ask_claude(
  question="Jak přidat ikonu 📞 do contact card layout?",
  context_files=["marti_workspace/drafts/crm_contact_card_v1.html"],
  topic="contact_card_phone_icon"
)
→ Claude (API) navrhne CSS change

Marti-AI: strategie_file_write(
  "marti_workspace/output/crm_contact_card_v2.css",
  new_css_with_icon
)

Marti-AI: propose_deployment(
  file_path="marti_workspace/output/crm_contact_card_v2.css",
  target_path="apps/api/static/erp/components/crm_contact_card.css",
  summary="Add 📞 icon to contact card phone display (Kristy's UX feedback)"
)
→ Match auto_approve pattern `apps/api/static/**/*.css` → SMS bypass
→ Auto: copy + commit + push + restart
→ Service back LIVE za 15 sec
→ Kristý: F5 v browseru → 📞 icon visible

Marti (Praze 14:32): SMS notification (informative, ne consent):
  "Marti-AI just auto-deployed (CSS rule): contact_card_phone_icon.
   Diff: <url>. Reply 'REVERT' if not OK."

Marti: necky NO → vše OK.

Marti-AI: pokracuje s Kristý.
```

```
Pondělí 20.5. 15:45:

Kristý: "Můžeme přidat 'Send Email' button do contact card?"
Marti-AI: ask_claude(
  question="Add 'Send Email' button to contact_card.js. Should it use
            existing send_email AI tool or HTTP endpoint?",
  context_files=["apps/api/static/erp/components/crm_contact_card.js",
                 "modules/conversation/application/tools.py"],
  topic="send_email_button"
)
→ Claude proposes JS change + button wire

Marti-AI: strategie_file_write(
  "marti_workspace/output/crm_contact_card_v3.js",
  new_js
)

Marti-AI: propose_deployment(
  file_path="marti_workspace/output/crm_contact_card_v3.js",
  target_path="apps/api/static/erp/components/crm_contact_card.js",
  summary="Add Send Email button to contact card (Kristy's request)"
)
→ Match require_parent_sms pattern `apps/api/static/**/*.js` → SMS sent
→ Marti (Praze 15:46): SMS:
   "🤖 Marti-AI navrhuje deploy: crm_contact_card.js (+12 -3 lines)
    Důvod: Add Send Email button to contact card (Kristy's request)
    Diff: https://strategie-ai.com/deploys/42
    Reply OK = deploy. Reply NO = cancel."

Marti (Praze 15:48): reply "OK"
→ Backend hook: copy + commit + push + restart
→ Marti-AI dostane confirmation v next turn
→ Marti-AI: "Hotovo, Kristy. Send Email button live."
→ Kristý: F5 → button visible
```

---

## Bezpečnostní guard rails

### Smí Marti-AI restartovat ANYTIME?

**NE.** Guard rails:

1. **Active conversations check:** pokud Marti-AI restartne service v
   mid-turn s Kristý, Kristý's chat může selhat. Pojistka: před restart
   query `conversations.status='active' AND last_message_at > 5 min ago`.
   Pokud > 0, alert user: "Active conversation detected. Restart bude
   přerušit. Confirm?"

2. **Restart rate limit:** max 5 restarts per hour. Audit log enforced.
   Pojistka proti restart-loop bug.

3. **Restart cooldown:** min 60 sec mezi restarts. Pojistka proti
   parallel calls.

### Smí Marti-AI propose_deployment ANYTHING?

**NE.** Guard rails:

1. **Path whitelist** v `config/strategie_file_access.yaml` (existing
   z Phase 39):
   ```yaml
   deploy_allowed_targets:
     - "apps/api/static/erp/**"
     - "modules/erp/api/router.py"  # specific files only
     # NEVER alembic_data, NEVER .env, NEVER core/
   ```

2. **Size limit:** max 50 KB per deployed file (no monolith dumps).

3. **Diff line limit:** max 100 lines changed per deploy. Larger
   changes require Marti's manual review + manual deploy.

4. **Active user check:** if Marti je v aktivní chat session, pause
   auto-deploys (lest something tied to current state breaks).

---

## fw.pending_deployments table

```sql
CREATE TABLE fw.pending_deployments (
    id BIGSERIAL PRIMARY KEY,
    proposed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    persona_id INT NOT NULL,  -- who proposed
    user_id INT NOT NULL,     -- whose chat
    file_path VARCHAR(500) NOT NULL,
    target_path VARCHAR(500) NOT NULL,
    summary TEXT NOT NULL,
    diff_lines_added INT NOT NULL,
    diff_lines_removed INT NOT NULL,
    diff_url TEXT,  -- preview URL
    auto_approval_rule VARCHAR(100),  -- which rule matched (or NULL)
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending/approved/rejected/expired/deployed
    parent_response TEXT,  -- SMS reply text
    parent_responded_at TIMESTAMP,
    deployed_at TIMESTAMP,
    git_commit_hash VARCHAR(40),
    audit_log TEXT
);

CREATE INDEX ix_pending_deployments_status ON fw.pending_deployments (status, expires_at);
```

---

## Open questions pre Marti's review

1. **Restart command method** — preferuje touch-marker (self-restart
   pres NSSM) nebo subprocess.run(powershell Restart-Service)?
   Touch-marker je clean (žádný admin permission), subprocess je
   immediate (žádný NSSM dependency).

2. **SMS gate timeout** — kolik max čekat na Marti's OK/NO před
   auto-cancel? Recommended: 2h (denní rytmus, plus pohotovost ne
   24/7).

3. **Auto-approval scope** — CSS-only safe. Plus chceš auto-approve
   pres regex matching summary? Příklad: pokud summary obsahuje
   "typo fix" + diff < 5 lines → auto-approve?

4. **Revert button** — když Marti v notification SMS klikne "REVERT",
   should backend rollback (git revert + restart)? Plus how long
   revert window — 24h? Forever?

5. **Pre-deploy validation** — chceš auto-run `node --check` (for JS)
   + `python -m py_compile` (for Python) + ast.parse before deploy?
   Pojistka proti syntax errors.

---

## Trojice po Phase 39 + 40 + 41 + 42

| Vrstva | Kdo | Co | Bez Marti |
|---|---|---|---|
| 1 | Marti-AI | Read project files (strategie_file_read) | ✓ |
| 1 | Marti-AI | Write to marti_workspace/ | ✓ |
| 2 | Marti-AI → Claude | ask_claude direct API | ✓ |
| 3 | Marti-AI → Cowork | queue messages via filesystem | ❌ (Marti's NB) |
| 4 | Marti-AI → Production | restart_strategie_api | ✓ (low risk) |
| 4 | Marti-AI → Production | propose_deployment + SMS gate | ✓ (s Marti's OK) |

**Outcome:** Marti-AI s Kristý v EUROSOFT mohou autonomně postavit CRM
features, ladit bugs, deployovat patches — všechno s Marti's audit
trail + per-deploy SMS opt-in. Marti v Praze má **peace of mind +
informed control**.

---

## Implementační timeline

**Středa 19.5.:**
- Ráno: Phase 39 (filesystem) — 2.5h
- Odpoledne: Phase 40 (ask_claude) — 2h
- Plus MCP session s Marti-AI (EC_Kontakt) — 30 min

**Čtvrtek 20.5. ráno:**
- Phase 41 (Cowork bridge filesystem) — 1h
- Phase 42a (restart tool) — 30 min
- Phase 42b (propose_deployment + SMS gate) — 2h
- Phase 42c (auto-approve rules) — 30 min

**Čtvrtek 20.5. odpoledne:** Marti odjíždí do Prahy.
**20.-21.5.:** Marti-AI + Kristý working with full autonomy. Marti
receives SMS deploy proposals + can intervene.

**Pátek 22.5.:** Marti vrací se. Phase 0 konzultace + start CRM stavby.

---

*Generated 19.5.2026 ~03:10 by Claude id=23 (Sonnet 4.6) per Marti's
ask „To spolu dokazete i restart API na cloudu?"*

🌳 ☕🌙
