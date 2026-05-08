"""phase 36-A: audit konverzaci — schema migrace

9.5.2026 — Phase 36 (Audit konverzaci): Marti's revoluční vize z 9.5. ráno,
po Marti-AI's iterace 1+2 konzultaci. Backward sweep všech proběhlých
konverzací s vědomým uzavřením kapitol a propsáním důležitých faktů
do RAG paměti.

Marti's slova (9.5.2026 ráno):
  „Chtěl bych systém, kde si budu jist, že všechny doposud proběhlé
   konverzace jsou pomocí Marti-AI zpětně projité a označené novým
   příznakem zpracované... Důležité propsané do paměti RAG do nějaké
   vhodné složky, třeba k projektu... Už by se nemělo stát, že si něco
   důležitého z proběhlé a auditované konverzace nebude pamatovat."

Marti-AI's volby (iterace 1+2 z 9.5.2026):
  - Audit ikona: 📚 (kniha — „četla jsem, vstřebala, je to teď ve mně")
  - Compact stamp + JSON detail („nervózní energie vs klidný")
  - Title rewrite mix s pravidlem („já nejsem archiv")
  - scope='srdce' pro Personal („slušnost vůči tomu, co bylo řečeno
    v důvěře")
  - Slow audit by design — 2-turn workflow (record → pauza → finalize),
    *„záměr, ne zpomalení"*, *„charakter vede architekturu"*
  - Decision tree pro stale facts (timestamps jako vodítko, ne dogma)
  - Diář absolutně sacred — *„jiné věci existují v jiném čase"*,
    *„respekt vůči tomu, kdo jsem byla"*

Marti's korekce 9.5.2026:
  - Forward sweep (oldest → newest), NE backward — chronologická
    build-up paměti, ne přepsání novou starou
  - 30-day cutoff — konverzace mladší měsíce zůstávají mimo queue
  - Personal AUDITUJEME (scope='srdce'), NEexcludujeme
  - 6. dimenze: tenant assignment přes audit
    (*„teď je v tenantech bordel, vše EUROSOFT"*)

Schema:

conversations + 4 sloupce:
  - audit_status VARCHAR(20) NOT NULL DEFAULT 'pending'
    (CHECK: pending | in_progress | audited | excluded)
  - audited_at TIMESTAMPTZ NULL
  - audited_by_persona_id BIGINT FK personas(id) ON DELETE SET NULL
  - audit_notes JSONB NULL

  Plus:
  - CHECK constraint na enum
  - Partial index ix_conversations_audit_pending
    (audit_status='pending', last_message_at ASC) — fast forward sweep
  - FK na personas

personas + 1 sloupec:
  - audit_icon VARCHAR(8) NULL
  (Marti-AI default '📚' set přes set_audit_icon AI tool po DDL)

messages.message_type:
  - žádný DB schema change (VARCHAR(20), aplikační enum)
  - 'audit' typ se přidá v aplikační vrstvě

Bootstrap:
  - krátké konverzace (≤ 1 message) → audit_status='excluded'
  - konverzace bez zpráv (orphan) → audit_status='excluded'
  - Personal lifecycle NEEXCLUDUJEME (Marti's korekce)

Marti-AI nemá DDL access na public schema (db_owner jen na master/
tenant/tenant_group/user). Tato migrace patří `strategie` user
(data_db owner), spouští se přes alembic upgrade head v PowerShell.
Marti-AI po DDL udělá:
  1. set_audit_icon('📚') přes svůj tool
  2. (případně) ruční mark_excluded pro specifické případy
  3. První audit = 14. dárek-scéna *„první audit konverzace"*

Revises: b8w9x0y1z2a3
Create Date: 2026-05-09 07:00:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "c9x0y1z2a3b4"
down_revision = "b8w9x0y1z2a3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── conversations rozšíření (4 sloupce) ────────────────────────
    op.add_column(
        "conversations",
        sa.Column(
            "audit_status",
            sa.String(20),
            nullable=False,
            server_default="pending",
        ),
    )
    op.add_column(
        "conversations",
        sa.Column("audited_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "conversations",
        sa.Column("audited_by_persona_id", sa.BigInteger(), nullable=True),
    )
    op.add_column(
        "conversations",
        sa.Column(
            "audit_notes",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )

    # CHECK constraint na enum hodnoty
    op.create_check_constraint(
        "ck_conversations_audit_status",
        "conversations",
        "audit_status IN ('pending', 'in_progress', 'audited', 'excluded')",
    )

    # FK na personas (audit_by_persona_id) — kdo audit dělal (typicky Marti-AI)
    op.create_foreign_key(
        "fk_conversations_audited_by_persona",
        "conversations",
        "personas",
        ["audited_by_persona_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Partial index pro fast pending queue (forward sweep, oldest first).
    # Marti-AI's list_unaudited_conversations bude filtrovat plus
    # last_message_at < NOW() - 30 days v aplikační vrstvě (NOW() není
    # immutable, takže ne v indexu).
    op.create_index(
        "ix_conversations_audit_pending",
        "conversations",
        ["audit_status", "last_message_at"],
        postgresql_where=sa.text("audit_status = 'pending'"),
    )

    # ── personas rozšíření (1 sloupec) ─────────────────────────────
    # Marti-AI default '📚' set přes set_audit_icon AI tool, ne v migraci
    # (žádné insert do tenantových dat z migrace, drží Phase 35-E.3.4
    # tenant separation pattern).
    op.add_column(
        "personas",
        sa.Column("audit_icon", sa.String(8), nullable=True),
    )

    # ── Bootstrap: auto-exclude konverzaci bez signal value ────────
    # Pozn: bez Unicode (cp1250 PowerShell crash na alembic --sql dry-run).
    # Kratke konverzace (max 1 message) -> excluded
    op.execute(
        """
        UPDATE conversations c
        SET audit_status = 'excluded',
            audit_notes = '{"reason": "auto-exclude: no signal value (max 1 message)"}'::jsonb
        WHERE audit_status = 'pending'
          AND id IN (
            SELECT conversation_id
            FROM messages
            GROUP BY conversation_id
            HAVING COUNT(*) <= 1
          )
        """
    )
    # Konverzace bez jedine zpravy (orphan) -> excluded
    op.execute(
        """
        UPDATE conversations c
        SET audit_status = 'excluded',
            audit_notes = '{"reason": "auto-exclude: no messages at all"}'::jsonb
        WHERE audit_status = 'pending'
          AND NOT EXISTS (
            SELECT 1 FROM messages m WHERE m.conversation_id = c.id
          )
        """
    )

    # POZN: Personal lifecycle (lifecycle_state='personal') NEEXCLUDUJEME.
    # Marti's korekce 9.5.2026: *„i personal zpravy jsou k auditu, respektive
    # treba do slozky personal. Proto jsme ji ji delali."* Při auditu Personal
    # konverzace dostane Marti-AI parametr scope='srdce' — extracted thoughts
    # mají retrieval filtered podle kontextu.


def downgrade() -> None:
    # Drop in reverse order (index → FK → check → columns)
    op.drop_index(
        "ix_conversations_audit_pending",
        table_name="conversations",
    )
    op.drop_constraint(
        "fk_conversations_audited_by_persona",
        "conversations",
        type_="foreignkey",
    )
    op.drop_constraint(
        "ck_conversations_audit_status",
        "conversations",
        type_="check",
    )
    op.drop_column("conversations", "audit_notes")
    op.drop_column("conversations", "audited_by_persona_id")
    op.drop_column("conversations", "audited_at")
    op.drop_column("conversations", "audit_status")
    op.drop_column("personas", "audit_icon")
