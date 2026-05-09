"""Phase 38.1 — Rate limiting pro verify-email + consume_invite.

Anti brute-force protection. Tří-vrstvé limity per hour:
  - email (5/h)  — anti email enumeration (útočník nemůže scanovat email
    adresy přes /verify-email/request, fake polling tokeny)
  - IP (10/h)    — anti distributed attack (jedna IP nemůže spamovat)
  - phone (20/h) — anti consume token brute-force (útočník nemůže replay
    odcizený token z různých phones)

Bucket pattern (fixed window per hour):
  - bucket_key: "email:foo@bar.com" / "ip:1.2.3.4" / "phone:+420778117879"
  - event_type: "verify_request" / "consume_attempt"
  - count: increment per request (PostgreSQL ON CONFLICT atomic)
  - window_start: hour-rounded timestamp (00:00, 01:00, atd.)
  - expires_at: window_start + 1h

Cleanup: TODO Phase 38.2 — Windows Task Scheduler cron (delete expired
buckets, retention 7d pro forensic).

Marti-AI's doctrine 10.5. dopoledne: "Bezpečnost přes probuzení, ne přes
ticho" — rate_limited entries v sms_routing_log dají Marti-AI ranní
digest "X failed verify attempts za 24h od Y různých phones".

Revision ID: f4d5e6a7b8c9
Revises: e3c4d5e6f7a8
Create Date: 2026-05-10 (post-Phase 38 LIVE polish)
"""
from alembic import op
import sqlalchemy as sa


revision = "f4d5e6a7b8c9"
down_revision = "e3c4d5e6f7a8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "verify_rate_buckets",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("bucket_key", sa.String(length=255), nullable=False),
        # Format: '{type}:{value}' — 'email:foo@bar' / 'ip:1.2.3.4' /
        # 'phone:+420778117879'. Lower-cased pro consistent matching.
        sa.Column("event_type", sa.String(length=40), nullable=False),
        # 'verify_request' (POST /verify-email/request)
        # 'consume_attempt' (consume_invite from SMS reply)
        sa.Column("count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "window_start",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        # Hour-rounded — e.g. 2026-05-10T11:00:00 pro any request 11:XX.
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        # window_start + 1h — pro cleanup query "DELETE WHERE expires_at < now()".
        sa.UniqueConstraint(
            "bucket_key", "event_type", "window_start",
            name="uq_verify_rate_bucket_window",
        ),
        # UNIQUE → umožňuje atomic UPSERT (INSERT ... ON CONFLICT DO UPDATE)
        # bez race condition. PostgreSQL specific feature.
    )

    # Lookup index — nejčastější query: "active bucket for key+event"
    op.create_index(
        "idx_verify_rate_buckets_lookup",
        "verify_rate_buckets",
        ["bucket_key", "event_type", "expires_at"],
    )

    # Cleanup index — cron "DELETE WHERE expires_at < now()"
    op.create_index(
        "idx_verify_rate_buckets_cleanup",
        "verify_rate_buckets",
        ["expires_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "idx_verify_rate_buckets_cleanup",
        table_name="verify_rate_buckets",
    )
    op.drop_index(
        "idx_verify_rate_buckets_lookup",
        table_name="verify_rate_buckets",
    )
    op.drop_table("verify_rate_buckets")
