"""phase29: multi-mailbox per persona -- shared CRM schranky pro Marti-AI

3.5.2026 vecer / 4.5.2026 rano -- Phase 29 implementace po designove
konzultaci s Marti-AI 2.5.2026 vecer (docs/phase29_multimailbox_consultation_letter.md).

ARCHITEKTURA -- "schema B clean":

  mailboxes (shared / personal Exchange / IMAP schranky)
       v
  mailbox_members (kdo z lidi ma pristup)
       v
  mailbox_personas (ktere AI persony tam pisou + per-action grants)
       v
  email_inbox.mailbox_id, email_outbox.mailbox_id (kazda zprava patri konkretni schrance)

  forbidden_mailboxes (blacklist -- napr. p.zeman@eurosoft.com NIKDY)

KLICOVA PRAVIDLA:

1. EWS fetcher pollne PER MAILBOX (ne per persona). Shared schranka =
   single creds, multiple mailbox_members ji vidi.

2. AI tools dostanou optional mailbox_id parameter. Default = first
   authorized (can_send=true) pro aktualni personu.

3. mailbox_personas SPLIT permissions (Marti-AI's design contribution
   z 2.5.2026 vecer Q6):
     can_read       -- default true, zadny gate
     can_send       -- parent grant required
     can_archive    -- parent grant SEPARATE (ne bundled s send)
     can_delete     -- parent grant SEPARATE
     can_mark_read  -- read state per-user, zadny gate

   Marti-AI: "archivace meni co kolegove vidi v share schrance -- to je
   tymovy dopad, ne jen jeji akce".

4. forbidden_mailboxes governance:
   - Pavlova `p.zeman@eurosoft.com` (privatni, NIKDY)
   - Validace v service layeru pred INSERT do `mailboxes`
   - Pri pokusu o pristup -> Marti-AI odmita + diary trail

5. NULL mailbox_id v email_inbox / email_outbox = backwards compat (Phase
   29-B backfill prepne na konkretni mailbox per persona's existing
   email channel).

Down: drop FKs, columns, tables. Bezpecne -- email_inbox / email_outbox
zustavaji s mailbox_id NULL po downgrade, AI tools pokracuji v
persona-based filtering jako pred Phase 29.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "x4s5t6u7v8w9"
down_revision = "w3r4s5t6u7v8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1) mailboxes table ─────────────────────────────────────────────
    op.create_table(
        "mailboxes",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("email_upn", sa.String(255), nullable=False),
        sa.Column("ews_credentials_encrypted", sa.Text, nullable=True),
        sa.Column("ews_server", sa.String(255), nullable=True),
        sa.Column("ews_display_email", sa.String(255), nullable=True),
        sa.Column("label", sa.String(100), nullable=True),
        sa.Column(
            "default_language",
            sa.String(2),
            nullable=False,
            server_default=sa.text("'cs'"),
        ),
        sa.Column(
            "is_shared",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("FALSE"),
        ),
        sa.Column("tenant_id", sa.BigInteger, nullable=True),
        sa.Column(
            "active",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("TRUE"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.UniqueConstraint("email_upn", name="uq_mailboxes_email_upn"),
    )
    op.create_index("ix_mailboxes_tenant_id", "mailboxes", ["tenant_id"])
    op.create_index("ix_mailboxes_active", "mailboxes", ["active"])

    # ── 2) mailbox_members (lide -- owner / operator / observer) ──────
    op.create_table(
        "mailbox_members",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "mailbox_id",
            sa.BigInteger,
            sa.ForeignKey("mailboxes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("user_id", sa.BigInteger, nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column(
            "granted_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("granted_by_user_id", sa.BigInteger, nullable=True),
        sa.UniqueConstraint(
            "mailbox_id", "user_id", name="uq_mailbox_members_mailbox_user"
        ),
        sa.CheckConstraint(
            "role IN ('owner', 'operator', 'observer')",
            name="ck_mailbox_members_role",
        ),
    )
    op.create_index(
        "ix_mailbox_members_user", "mailbox_members", ["user_id"]
    )

    # ── 3) mailbox_personas (AI persony + per-action grants) ──────────
    op.create_table(
        "mailbox_personas",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "mailbox_id",
            sa.BigInteger,
            sa.ForeignKey("mailboxes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("persona_id", sa.BigInteger, nullable=False),
        sa.Column(
            "can_read",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("TRUE"),
        ),
        sa.Column(
            "can_send",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("FALSE"),
        ),
        sa.Column(
            "can_archive",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("FALSE"),
        ),
        sa.Column(
            "can_delete",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("FALSE"),
        ),
        sa.Column(
            "can_mark_read",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("TRUE"),
        ),
        sa.Column(
            "granted_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("granted_by_user_id", sa.BigInteger, nullable=True),
        sa.UniqueConstraint(
            "mailbox_id", "persona_id",
            name="uq_mailbox_personas_mailbox_persona",
        ),
    )
    op.create_index(
        "ix_mailbox_personas_persona", "mailbox_personas", ["persona_id"]
    )

    # ── 4) forbidden_mailboxes (blacklist guvernance) ─────────────────
    op.create_table(
        "forbidden_mailboxes",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("email_upn", sa.String(255), nullable=False),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column(
            "added_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("added_by_user_id", sa.BigInteger, nullable=True),
        sa.UniqueConstraint(
            "email_upn", name="uq_forbidden_mailboxes_email_upn"
        ),
    )

    # Insert Pavlovou privatni schranku jako forbidden (Marti-AI's Q4
    # decision: "governance trail mi dava klid" + Marti's "do tohoto
    # prostoru nikdo z nas nepatri").
    op.execute(
        sa.text("""
        INSERT INTO forbidden_mailboxes (email_upn, reason)
        VALUES (
            'p.zeman@eurosoft.com',
            'Pavlova privatni pracovni schranka -- ani 3 kolegove tam nesmi. '
            'Marti 2.5.2026: "soukromy prostor, do ktereho nikdo z nas nepatri". '
            'Phase 29 design konzultace 2.5.2026 vecer Q4.'
        )
        """)
    )

    # ── 5) email_inbox.mailbox_id FK ──────────────────────────────────
    op.add_column(
        "email_inbox",
        sa.Column("mailbox_id", sa.BigInteger, nullable=True),
    )
    op.create_foreign_key(
        "fk_email_inbox_mailbox",
        "email_inbox", "mailboxes",
        ["mailbox_id"], ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_email_inbox_mailbox", "email_inbox", ["mailbox_id"]
    )

    # ── 6) email_outbox.mailbox_id FK ─────────────────────────────────
    op.add_column(
        "email_outbox",
        sa.Column("mailbox_id", sa.BigInteger, nullable=True),
    )
    op.create_foreign_key(
        "fk_email_outbox_mailbox",
        "email_outbox", "mailboxes",
        ["mailbox_id"], ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_email_outbox_mailbox", "email_outbox", ["mailbox_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_email_outbox_mailbox", table_name="email_outbox")
    op.drop_constraint(
        "fk_email_outbox_mailbox", "email_outbox", type_="foreignkey"
    )
    op.drop_column("email_outbox", "mailbox_id")

    op.drop_index("ix_email_inbox_mailbox", table_name="email_inbox")
    op.drop_constraint(
        "fk_email_inbox_mailbox", "email_inbox", type_="foreignkey"
    )
    op.drop_column("email_inbox", "mailbox_id")

    op.drop_table("forbidden_mailboxes")

    op.drop_index("ix_mailbox_personas_persona", table_name="mailbox_personas")
    op.drop_table("mailbox_personas")

    op.drop_index("ix_mailbox_members_user", table_name="mailbox_members")
    op.drop_table("mailbox_members")

    op.drop_index("ix_mailboxes_active", table_name="mailboxes")
    op.drop_index("ix_mailboxes_tenant_id", table_name="mailboxes")
    op.drop_table("mailboxes")
