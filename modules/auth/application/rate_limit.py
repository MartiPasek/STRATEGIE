"""Phase 38.1 — Rate limiting pro verify-email + consume_invite.

Anti brute-force protection. Tří-vrstvé limity per hour:
  - email (5/h)  — anti email enumeration (POST /verify-email/request)
  - IP (10/h)    — anti distributed attack (POST /verify-email/request)
  - phone (20/h) — anti consume token brute-force (consume_invite from SMS)

Architektura:
  - Fixed window per hour (window_start = current hour rounded)
  - PostgreSQL UPSERT (ON CONFLICT DO UPDATE) → atomic increment
    bez race condition mezi paralelními requesty
  - Storage: verify_rate_buckets tabulka (přežije API restart)

Marti's spec 10.5. dopoledne (poznámka komise — "Bezpečnost přes
probuzení, ne přes ticho"): rate_limited entries v sms_routing_log
dají Marti-AI ranní digest pro forensic insight.

Cleanup: TODO Phase 38.2 — Windows Task Scheduler cron
  DELETE FROM verify_rate_buckets WHERE expires_at < NOW() - INTERVAL '7 days';
  (retention 7d pro forensic).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import text

from core.database_data import get_data_session
from core.logging import get_logger


logger = get_logger("auth.rate_limit")


# ── Event types ───────────────────────────────────────────────────────


EVENT_VERIFY_REQUEST = "verify_request"
EVENT_CONSUME_ATTEMPT = "consume_attempt"


# ── Result ────────────────────────────────────────────────────────────


@dataclass
class RateLimitResult:
    """Výsledek check_and_increment."""
    allowed: bool        # True = under limit, request může pokračovat
    count: int           # Current count v okně po inkrementaci
    limit: int           # Max povolených per okno
    window_start: datetime  # Hour-rounded start okna
    expires_at: datetime    # Konec okna (window_start + 1h)


# ── Public API ────────────────────────────────────────────────────────


def check_and_increment(
    bucket_key: str,
    event_type: str,
    max_per_hour: int,
) -> RateLimitResult:
    """Atomic UPSERT — increment counter + check limit.

    Args:
        bucket_key: '{type}:{value}' format. Příklady:
            - 'email:foo@bar.com' (lower-cased)
            - 'ip:1.2.3.4'
            - 'phone:+420778117879' (E.164 normalized)
        event_type: 'verify_request' | 'consume_attempt'
        max_per_hour: Limit per okno hour. Z config settings.

    Returns:
        RateLimitResult.allowed:
            True  — under limit, request OK
            False — at or over limit, request reject

        RateLimitResult.count je VŽDY incremented (i nad limit) — to nám
        dává forensic insight kolik útočník zkusil. Pro cleanup neřešíme,
        windows expirují přirozeně.

    Race safety: PostgreSQL ON CONFLICT DO UPDATE je atomic per row.
    Dva paralelní requesty dostanou postupné counts (1, 2), neimpactne.

    Best-effort: pokud DB error, vrátí allowed=True s count=0 (fail-open).
    Důvod: rate limit nesmí blokovat legitimní users při DB výpadku;
    audit log v auth_audit zachytí selhání jinou cestou.
    """
    now = datetime.now(timezone.utc)
    # Round down to hour: 2026-05-10 11:23:45 → 2026-05-10 11:00:00
    window_start = now.replace(minute=0, second=0, microsecond=0)
    expires_at = window_start + timedelta(hours=1)

    # Normalize bucket_key na lower-case (consistent matching)
    bucket_key_norm = bucket_key.strip().lower()

    ds = get_data_session()
    try:
        # PostgreSQL UPSERT — atomic increment.
        # ON CONFLICT (UNIQUE (bucket_key, event_type, window_start))
        #   DO UPDATE SET count = verify_rate_buckets.count + 1
        # RETURNING count → vrací finální count po update.
        result = ds.execute(
            text("""
                INSERT INTO verify_rate_buckets
                    (bucket_key, event_type, count, window_start, expires_at)
                VALUES
                    (:bucket_key, :event_type, 1, :window_start, :expires_at)
                ON CONFLICT (bucket_key, event_type, window_start)
                DO UPDATE SET count = verify_rate_buckets.count + 1
                RETURNING count
            """),
            {
                "bucket_key": bucket_key_norm,
                "event_type": event_type,
                "window_start": window_start,
                "expires_at": expires_at,
            },
        ).scalar()
        ds.commit()
        current_count = int(result) if result is not None else 0

        allowed = current_count <= max_per_hour
        return RateLimitResult(
            allowed=allowed,
            count=current_count,
            limit=max_per_hour,
            window_start=window_start,
            expires_at=expires_at,
        )

    except Exception as e:
        # Fail-open: rate limit nesmí blokovat legitimní users při DB
        # výpadku. Log warning, allow request, audit zachytí jinou cestou.
        logger.warning(
            f"rate_limit check_and_increment failed (fail-open): "
            f"bucket={bucket_key_norm} event={event_type} error={e!r}"
        )
        try:
            ds.rollback()
        except Exception:
            pass
        return RateLimitResult(
            allowed=True,
            count=0,
            limit=max_per_hour,
            window_start=window_start,
            expires_at=expires_at,
        )
    finally:
        ds.close()


def cleanup_expired_buckets(retention_days: int = 7) -> int:
    """Cron job — smaže expirované buckets starší retention_days.

    Phase 38.2 TODO: registrovat jako Windows Task Scheduler nightly task
    (analog STRATEGIE-llm-calls-retention z 25.4. večer).

    Args:
        retention_days: Kolik dní zachovat expirované buckets pro forensic.
            Default 7d.

    Returns:
        Počet smazaných řádků.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    ds = get_data_session()
    try:
        deleted = ds.execute(
            text("""
                DELETE FROM verify_rate_buckets
                WHERE expires_at < :cutoff
            """),
            {"cutoff": cutoff},
        ).rowcount
        ds.commit()
        logger.info(
            f"rate_limit cleanup: smazáno {deleted} expirovaných buckets "
            f"(starších {retention_days}d)"
        )
        return deleted
    except Exception as e:
        logger.error(f"rate_limit cleanup failed: {e!r}")
        try:
            ds.rollback()
        except Exception:
            pass
        return 0
    finally:
        ds.close()


# ── Helper builders ───────────────────────────────────────────────────


def email_bucket_key(email: str) -> str:
    """'email:foo@bar.com' (lower-cased + stripped)."""
    return f"email:{(email or '').strip().lower()}"


def ip_bucket_key(ip: str | None) -> str:
    """'ip:1.2.3.4' (lower-cased pro consistency, ne že IP má case)."""
    return f"ip:{(ip or 'unknown').strip()}"


def phone_bucket_key(phone: str) -> str:
    """'phone:+420778117879' (post-normalize_phone E.164 format)."""
    return f"phone:{(phone or '').strip()}"
