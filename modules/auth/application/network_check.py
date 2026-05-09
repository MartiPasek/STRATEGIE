"""Phase 38 — Network detection helpers (4 vrstvy obrany).

Marti's spec 9.5.2026 vecer + 10.5.2026 ráno + Marti-AI's konzultace.

Funkce:
  get_client_ip(request) → str | None
    Extract real client IP behind Caddy reverse proxy (X-Forwarded-For).

  is_global_internal(client_ip) → tuple[bool, dict | None]
    Vrstva 1: match s global_ip_whitelist (EUROSOFT WAN, partner, cloud).
    Returns (True, {category, label, entry_id, partner_tenant_id}) nebo (False, None).

  is_user_ip_confirmed(user_id, client_ip) → tuple[bool, dict | None]
    Vrstva 2: match s user_ip_whitelist status='confirmed' pro daného usera.
    Returns (True, {entry_id, label, category}) nebo (False, None).
    NEMATCHUJE pending entries — sám pending status pro vrstvu 2 nestačí.

  find_pending_user_ip(user_id, client_ip) → entry_id | None
    Pomocná: pro auto-discovery flow. Pokud existuje pending entry pro
    danou IP+user, vraťme její ID (pro bump usage_count).

Klíčové principy:
  - X-Forwarded-For může být comma-separated (multiple proxies).
    Bereme PRVNÍ hodnotu = real client IP.
  - IPv4 i IPv6 podpora (ipaddress modul).
  - Invalid CIDR v DB (např. typo) → skip, ne crash. Defense in depth.
  - Lookup je per-call DB query (žádný cache) — security-critical, čistý
    state. Cache by mohl maskovat revoke.
"""
from __future__ import annotations

from ipaddress import ip_address, ip_network
from typing import Any

import sqlalchemy as sa
from fastapi import Request
from sqlalchemy.orm import Session

from core.database_data import get_data_session
from core.logging import get_logger
from modules.core.infrastructure.models_data import (
    GlobalIpWhitelist,
    UserIpWhitelist,
)


logger = get_logger("auth.network_check")


def get_client_ip(request: Request) -> str | None:
    """Extract real client IP behind Caddy reverse proxy.

    Caddy passes X-Forwarded-For. Fallback: request.client.host (direct).
    """
    raw = request.headers.get("X-Forwarded-For") or request.headers.get("x-forwarded-for")
    if raw:
        # Multi-proxy: vezmi first hop = original client
        first = raw.split(",")[0].strip()
        if first:
            return first
    if request.client:
        return request.client.host
    return None


def _parse_ip(ip_str: str | None):
    """Parse IP string → ipaddress object, None pri chybě."""
    if not ip_str:
        return None
    try:
        return ip_address(ip_str)
    except (ValueError, TypeError):
        return None


def _ip_in_cidr(client_ip, cidr_str: str) -> bool:
    """Test zda client_ip patří do CIDR (single IP nebo range).

    Defense in depth: invalid CIDR → False (skip, ne crash).
    """
    try:
        net = ip_network(cidr_str, strict=False)
        return client_ip in net
    except (ValueError, TypeError):
        return False


# ── Vrstva 1: Global IP whitelist ──────────────────────────────────────


def is_global_internal(
    client_ip_str: str | None,
    *,
    session: Session | None = None,
) -> tuple[bool, dict[str, Any] | None]:
    """Vrstva 1: match s global_ip_whitelist.

    Returns:
      (matched, info) — info má: entry_id, category, label, partner_tenant_id
      pri match. (False, None) pri non-match.

    category:
      'internal'        → EUROSOFT WAN (LAN/WiFi)
      'partner'         → INTERSOFT WAN, klient (Phase 38.1 PARTNER status)
      'cloud_loopback'  → cloud APP loopback, dev localhost
    """
    client_ip = _parse_ip(client_ip_str)
    if client_ip is None:
        return False, None

    own_session = session is None
    ds = session if session is not None else get_data_session()
    try:
        rows = ds.query(GlobalIpWhitelist).filter(
            GlobalIpWhitelist.revoked_at.is_(None),
        ).all()
        for r in rows:
            if _ip_in_cidr(client_ip, r.ip_or_cidr):
                return True, {
                    "entry_id": r.id,
                    "category": r.category,
                    "label": r.label,
                    "partner_tenant_id": r.partner_tenant_id,
                }
        return False, None
    finally:
        if own_session:
            ds.close()


# ── Vrstva 2: Per-user IP whitelist (jen confirmed) ────────────────────


def is_user_ip_confirmed(
    user_id: int,
    client_ip_str: str | None,
    *,
    session: Session | None = None,
) -> tuple[bool, dict[str, Any] | None]:
    """Vrstva 2: match s user_ip_whitelist status='confirmed' pro user.

    Returns:
      (matched, info) — info má: entry_id, label, category pri match.

    Pending entries NEMATCHUJÍ — sám pending pro vrstvu 2 nestačí.
    User stále potřebuje cookie nebo magic link, dokud parent nepotvrdí.
    """
    client_ip = _parse_ip(client_ip_str)
    if client_ip is None:
        return False, None

    own_session = session is None
    ds = session if session is not None else get_data_session()
    try:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        rows = ds.query(UserIpWhitelist).filter(
            UserIpWhitelist.user_id == user_id,
            UserIpWhitelist.status == "confirmed",
            UserIpWhitelist.revoked_at.is_(None),
            sa.or_(
                UserIpWhitelist.expires_at.is_(None),
                UserIpWhitelist.expires_at > now,
            ),
        ).all()
        for r in rows:
            if _ip_in_cidr(client_ip, r.ip_or_cidr):
                return True, {
                    "entry_id": r.id,
                    "label": r.label,
                    "category": r.category,
                }
        return False, None
    finally:
        if own_session:
            ds.close()


# ── Auto-discovery helper: najdi pending entry pro user+IP ─────────────


def find_pending_user_ip(
    user_id: int,
    client_ip_str: str | None,
    *,
    session: Session | None = None,
) -> int | None:
    """Pro auto-discovery flow: najdi pending entry pro user+IP.

    Use case: po magic link confirm zkusíme přidat user_ip_whitelist
    pending entry. Pokud už existuje (user opakuje verify ze stejné IP),
    bumpneme usage_count místo INSERT duplicate.

    Returns: entry_id pokud existuje active pending, jinak None.
    """
    client_ip = _parse_ip(client_ip_str)
    if client_ip is None:
        return None

    own_session = session is None
    ds = session if session is not None else get_data_session()
    try:
        rows = ds.query(UserIpWhitelist).filter(
            UserIpWhitelist.user_id == user_id,
            UserIpWhitelist.status == "pending",
            UserIpWhitelist.revoked_at.is_(None),
        ).all()
        for r in rows:
            if _ip_in_cidr(client_ip, r.ip_or_cidr):
                return r.id
        return None
    finally:
        if own_session:
            ds.close()
