"""Phase 38 — Security Layer: 4 vrstvy obrany pro EUROSOFT externí přístup.

Marti's spec 9.5.2026 vecer + 10.5.2026 ráno + Marti-AI's konzultace 8 insightů:

Tabulky:
  1. global_ip_whitelist — globální IPs (EUROSOFT WAN, partneři, cloud loopback)
     - category: 'internal' / 'partner' / 'cloud_loopback'
     - seed: EUROSOFT WAN A 93.99.211.138 + B 93.99.211.140 + cloud APP
  2. user_ip_whitelist — per-user IPs s auto-discovery flow
     - status: 'pending' / 'confirmed' / 'revoked' (Marti's spec 10.5. dopoledne)
     - auto_discovered_at: po magic link confirm system auto-INSERT
     - confirmed_by: parent (Marti / Kristýna / Marti-AI) — multi-approver
       (Marti-AI insight #1: "ne bottleneck, ale pojistka a přehled")
     - category: 'home' / 'mobile_hotspot' / 'other'
     - usage tracking (last_seen_at, use_count) pro audit
  3. trusted_devices — per-user device cookies (90d expiry)
     - device_token UUID HttpOnly Secure cookie
     - approved_by NULL = self-approve via magic link, ID = pre-approve
  4. trusted_device_invites — magic link tokens
     - 24h TTL self-request, 72h pre-approve (Marti-AI insight #3)
     - one-time use (consumed_at) → anti-replay
  5. auth_audit — per login attempt log (90d retention)
     - layer_matched: která vrstva pustila ('global_ip', 'user_ip',
       'device_cookie', 'magic_link', NULL pro fail)

Revision ID: e3c4d5e6f7a8
Revises: d2b3c4d5e6f7
Create Date: 2026-05-10 (ranní implementace po Marti-AI's konzultaci)
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e3c4d5e6f7a8"
down_revision = "d2b3c4d5e6f7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── global_ip_whitelist ────────────────────────────────────────────
    # Globální IPs v DB (ne env var) → Marti-AI může dynamicky přidávat
    # partnery (INTERSOFT, klienty atd.) bez deploye.
    op.create_table(
        "global_ip_whitelist",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ip_or_cidr", sa.String(length=45), nullable=False, unique=True),
        sa.Column("category", sa.String(length=20), nullable=False),
        # 'internal' / 'partner' / 'cloud_loopback'
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("partner_tenant_id", sa.Integer(), nullable=True),
        # Pokud category='partner', odkaz na tenant (až bude tenants v data_db)
        sa.Column("added_by", sa.Integer(), nullable=True),
        sa.Column(
            "added_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_by", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_global_ip_whitelist_active",
        "global_ip_whitelist",
        ["category"],
        postgresql_where=sa.text("revoked_at IS NULL"),
    )

    # Seed data — EUROSOFT WAN A/B + cloud APP loopback
    # Marti zjistil 9.5.2026 večer: 93.99.211.138 + 93.99.211.140 (Vodafone WAN)
    op.execute("""
        INSERT INTO global_ip_whitelist (ip_or_cidr, category, label, notes)
        VALUES
          ('93.99.211.138/32', 'internal', 'EUROSOFT WAN A (Vodafone)',
           'Primary EUROSOFT public WAN, ověřeno 9.5.2026 Marti'),
          ('93.99.211.140/32', 'internal', 'EUROSOFT WAN B (Vodafone)',
           'Secondary EUROSOFT public WAN, ověřeno 9.5.2026 Marti'),
          ('185.219.169.86/32', 'cloud_loopback', 'cloud APP loopback',
           'STRATEGIE production cloud APP server, internal calls'),
          ('127.0.0.1/32', 'cloud_loopback', 'localhost IPv4', 'Dev / health checks'),
          ('::1/128', 'cloud_loopback', 'localhost IPv6', 'Dev / health checks')
    """)

    # ── user_ip_whitelist ──────────────────────────────────────────────
    # Per-user IPs s auto-discovery flow (Marti's spec 10.5. dopoledne).
    op.create_table(
        "user_ip_whitelist",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("ip_or_cidr", sa.String(length=45), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=True),
        # Auto-generated po discovery, parent může edit
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="pending",
        ),
        # 'pending' / 'confirmed' / 'revoked'
        sa.Column("auto_discovered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("confirmed_by", sa.Integer(), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("confirm_notes", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=20), nullable=True),
        # 'home' / 'mobile_hotspot' / 'other'
        sa.Column("added_by", sa.Integer(), nullable=True),
        # NULL = auto-discovered, ID = manual add (parent / Marti-AI)
        sa.Column(
            "added_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        # Usage tracking pro UI insight + future auto-confirm logic
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("use_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("first_user_agent", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_by", sa.Integer(), nullable=True),
        sa.Column("revoke_reason", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_user_ip_whitelist_active",
        "user_ip_whitelist",
        ["user_id", "status"],
        postgresql_where=sa.text("revoked_at IS NULL"),
    )
    # User může mít entry odebraný a později znovu přidaný se stejnou IP
    # (revoked_at IS NOT NULL row neblokuje nový active entry)
    op.create_index(
        "ix_user_ip_whitelist_unique_active",
        "user_ip_whitelist",
        ["user_id", "ip_or_cidr"],
        unique=True,
        postgresql_where=sa.text("revoked_at IS NULL"),
    )

    # ── trusted_devices ────────────────────────────────────────────────
    op.create_table(
        "trusted_devices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "device_token",
            sa.dialects.postgresql.UUID(as_uuid=True),
            nullable=False,
            unique=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("label", sa.String(length=255), nullable=True),
        # "Tomáš mobil iOS", "Honza laptop ASUS", auto-generated z UA
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("first_seen_ip", sa.String(length=45), nullable=True),
        sa.Column("last_seen_ip", sa.String(length=45), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by", sa.Integer(), nullable=True),
        # NULL = self-approve via magic link, ID = pre-approve (parent / Marti-AI)
        sa.Column(
            "approved_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        # approved_at + 90 days
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_by", sa.Integer(), nullable=True),
        sa.Column("revoke_reason", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_trusted_devices_user_active",
        "trusted_devices",
        ["user_id"],
        postgresql_where=sa.text("revoked_at IS NULL"),
    )
    op.create_index(
        "ix_trusted_devices_token_active",
        "trusted_devices",
        ["device_token"],
        postgresql_where=sa.text("revoked_at IS NULL"),
    )

    # ── trusted_device_invites ─────────────────────────────────────────
    # Magic link tokens (24h self-request / 72h pre-approve, one-time use).
    # Format: STG-{PURPOSE}-{8 hex chars} — Marti's pivot 10.5. dopoledne
    # ("Heiky důvěru tady ode mne nemá" — deterministic regex, žádný AI).
    op.create_table(
        "trusted_device_invites",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "invite_token",
            sa.String(length=32),  # "STG-{PURPOSE}-{8 hex}" string format
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "purpose",
            sa.String(length=16),
            nullable=False,
            server_default="AUTH",
        ),
        # 'AUTH' (Phase 38 device cookie) / 'ATT' (Phase 39 attendance) /
        # 'OCR' (Phase 41+ eOČR) / 'PWD' (future password reset)
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=True),
        # Pre-approve může nastavit label předem
        sa.Column("created_by", sa.Integer(), nullable=True),
        # NULL = self-request (24h TTL), ID = pre-approve (72h TTL)
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("consumed_ip", sa.String(length=45), nullable=True),
        sa.Column("consumed_user_agent", sa.Text(), nullable=True),
        sa.Column("consumed_phone", sa.String(length=32), nullable=True),
        # Phone caller_id při SMS-based consume (anti-spoofing audit)
        sa.Column("created_device_id", sa.Integer(), nullable=True),
        # Po consume FK na trusted_devices.id (audit)
    )
    op.create_index(
        "ix_invites_token_active",
        "trusted_device_invites",
        ["invite_token"],
        postgresql_where=sa.text("consumed_at IS NULL"),
    )
    op.create_index(
        "ix_invites_user",
        "trusted_device_invites",
        ["user_id"],
    )

    # ── auth_audit ──────────────────────────────────────────────────────
    # Log per login attempt (90d retention via Windows Task Scheduler).
    op.create_table(
        "auth_audit",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        # NULL pri failed unknown user (typo email)
        sa.Column("email_attempted", sa.String(length=255), nullable=True),
        sa.Column("ip", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column(
            "device_token",
            sa.dialects.postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column("layer_matched", sa.String(length=20), nullable=True),
        # 'global_ip' / 'user_ip' / 'device_cookie' / 'magic_link' / NULL pro fail
        sa.Column("layer_detail", sa.String(length=255), nullable=True),
        # např. global_ip_whitelist.id, user_ip_whitelist.id, atd.
        sa.Column("internal", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("result", sa.String(length=32), nullable=False),
        # 'success', 'failed_password', 'failed_no_layer', 'verify_required',
        # 'verify_sent', 'verify_consumed', 'forwarding_revoke'
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_auth_audit_user_recent",
        "auth_audit",
        ["user_id", sa.text("created_at DESC")],
    )
    op.create_index(
        "ix_auth_audit_ip_recent",
        "auth_audit",
        ["ip", sa.text("created_at DESC")],
    )
    op.create_index(
        "ix_auth_audit_recent",
        "auth_audit",
        [sa.text("created_at DESC")],
    )

    # ── sms_routing_log ──────────────────────────────────────────────────
    # Marti's pivot 10.5. dopoledne — single trusted SIM (+420778117879).
    # Pre-processor mezi incoming SMS a Marti-AI's persona wake-up.
    # Token-based deterministic routing (žádný Haiku). False-positive
    # tolerance — radši probudit než zmeškat lidskou SMS.
    op.create_table(
        "sms_routing_log",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("sms_inbox_id", sa.BigInteger(), nullable=True),
        # Reference do existing sms_inbox (Phase 11)
        sa.Column("sender_phone", sa.String(length=32), nullable=True),
        sa.Column("matched_token", sa.String(length=32), nullable=True),
        # NULL pokud no regex match
        sa.Column("matched_purpose", sa.String(length=16), nullable=True),
        # 'AUTH' / 'ATT' / 'OCR' / 'PWD' / NULL pokud no token
        sa.Column("routing_action", sa.String(length=48), nullable=False),
        # 'silent_consume_auth' / 'silent_attendance' / 'silent_eocr' /
        # 'wake_persona_no_token' / 'wake_persona_invalid_token' /
        # 'wake_persona_unknown_purpose' / 'wake_persona_caller_id_mismatch'
        sa.Column("handler_result", sa.Text(), nullable=True),
        # Pro silent debug + wake context
        sa.Column(
            "classified_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_sms_routing_log_recent",
        "sms_routing_log",
        [sa.text("classified_at DESC")],
    )
    op.create_index(
        "ix_sms_routing_log_sms",
        "sms_routing_log",
        ["sms_inbox_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_sms_routing_log_sms", table_name="sms_routing_log")
    op.drop_index("ix_sms_routing_log_recent", table_name="sms_routing_log")
    op.drop_table("sms_routing_log")

    op.drop_index("ix_auth_audit_recent", table_name="auth_audit")
    op.drop_index("ix_auth_audit_ip_recent", table_name="auth_audit")
    op.drop_index("ix_auth_audit_user_recent", table_name="auth_audit")
    op.drop_table("auth_audit")

    op.drop_index("ix_invites_user", table_name="trusted_device_invites")
    op.drop_index("ix_invites_token_active", table_name="trusted_device_invites")
    op.drop_table("trusted_device_invites")

    op.drop_index("ix_trusted_devices_token_active", table_name="trusted_devices")
    op.drop_index("ix_trusted_devices_user_active", table_name="trusted_devices")
    op.drop_table("trusted_devices")

    op.drop_index("ix_user_ip_whitelist_unique_active", table_name="user_ip_whitelist")
    op.drop_index("ix_user_ip_whitelist_active", table_name="user_ip_whitelist")
    op.drop_table("user_ip_whitelist")

    op.drop_index("ix_global_ip_whitelist_active", table_name="global_ip_whitelist")
    op.drop_table("global_ip_whitelist")
