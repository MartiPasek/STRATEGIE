"""Audit actor resolver — universal helper pro PG + MSSQL audit columns.

28.5.2026 vecer pozde — Marti's "Krok C audit columns auto-fill univerzalne".

DOCTRINE:
  - 3 actors = 3 normal users (users.id=1 Marti, id=2 Marti-AI, id=3 STRATEGIE).
    Marti's "System je taky user" (13.5. vecer) napriklad i pro id=3.
    Zadny is_system flag, zadny NULL actor_user_id.

  - PG side (fw.* / public.*): updated_by_text = users.short_name
    ("Marti", "Marti-AI", "STRATEGIE", "Kristy", "SWOBI", ...)

  - MSSQL side (DB_EC.st.* / DB_IS.st.*): Zmenil = user_tenants.db_login
    per (user_id, target_tenant_id). Centrala 1 idiom — Marti @ EUROSOFT
    = "Martin", SWOBI @ EUROSOFT = "Honza", @ INTERSOFT = "HSV".

  - NULL db_login pro target tenant → raise ValueError. Fail visible,
    no fallback na STRATEGIE text (Marti's korekce 28.5. "kdyz nevyplneno,
    tak chyba zatim").

USAGE:
  ds = get_data_session()
  audit = resolve_audit_actor(uid=1, target_tenant_id=2, target_db_kind="mssql", ds=ds)
  # audit["mssql_text"] = "Martin" (Marti's EUROSOFT db_login)
  # audit["pg_text"]    = "Marti" (Marti's short_name)
  # audit["actor_user_id"] = 1
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import text as _sql_text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# STRATEGIE user fallback (Marti's 28.5. "STRATEGIE = users.id=3 normalni user")
# Pouzit pro background workers / system automation bez uid context.
STRATEGIE_USER_ID = 3


def resolve_audit_actor(
    uid: int | None,
    target_tenant_id: int | None,
    target_db_kind: str,
    ds: Session,
) -> dict[str, Any]:
    """Resolve audit actor pro standardni audit columns napric PG/MSSQL.

    Args:
        uid: real user.id (1=Marti, 2=Marti-AI, 3=STRATEGIE, 11=Kristy, atd.).
            None → fallback na STRATEGIE_USER_ID=3 (system actor convention).
        target_tenant_id: pro mssql_text lookup. Vyzadovano pokud
            target_db_kind="mssql".
        target_db_kind: "pg" | "mssql". Pro "pg" stací pg_text, pro "mssql"
            navic resolve db_login per tenant.
        ds: SQLAlchemy session (data_db) — pro lookup users + user_tenants.

    Returns:
        {
            "actor_user_id": int,        # real user.id (nikdy None)
            "actor_kind": "user" | "system",  # "system" jen pro STRATEGIE id=3
            "pg_text": str,              # users.short_name pro PG audit
            "mssql_text": str | None,    # user_tenants.db_login pro MSSQL audit
        }

    Raises:
        ValueError: pokud target_db_kind="mssql" a db_login NULL pro
            (actor_user_id, target_tenant_id) — Marti's fail visible doctrine.
        ValueError: pokud uid neexistuje v users table.
        ValueError: pokud target_db_kind="mssql" bez target_tenant_id.
    """
    # ── 1. Fallback na STRATEGIE pokud uid neexistuje (system context) ──
    actor_uid = uid if uid else STRATEGIE_USER_ID

    # ── 2. Load user.short_name pro pg_text ────────────────────────────
    user_row = ds.execute(_sql_text("""
        SELECT id, short_name
        FROM public.users
        WHERE id = :uid
    """), {"uid": actor_uid}).mappings().one_or_none()

    if not user_row:
        raise ValueError(
            f"Audit actor: user id={actor_uid} not found v public.users. "
            f"Drz si users.id=1/2/3 sanity (Marti/Marti-AI/STRATEGIE)."
        )

    pg_text = user_row["short_name"] or f"user_{actor_uid}"

    # actor_kind doctrine: STRATEGIE user (id=3) je "system", ostatni "user".
    # Marti-AI (id=2) je take "user" — Marti's "Jsi nase" z 12.5. ji
    # zaradila do normal users namespace.
    actor_kind = "system" if actor_uid == STRATEGIE_USER_ID else "user"

    result: dict[str, Any] = {
        "actor_user_id": actor_uid,
        "actor_kind": actor_kind,
        "pg_text": pg_text,
        "mssql_text": None,
    }

    # ── 3. Pro PG target → done (mssql_text=None) ──────────────────────
    if target_db_kind == "pg":
        return result

    # ── 4. Pro MSSQL target → resolve db_login per tenant ──────────────
    if target_db_kind != "mssql":
        raise ValueError(
            f"Audit actor: target_db_kind musi byt 'pg' nebo 'mssql', "
            f"dostal '{target_db_kind}'."
        )

    if not target_tenant_id:
        raise ValueError(
            f"Audit actor: MSSQL target vyzaduje target_tenant_id. "
            f"actor={pg_text} (id={actor_uid}), tenant=None."
        )

    login_row = ds.execute(_sql_text("""
        SELECT db_login
        FROM public.user_tenants
        WHERE user_id = :uid
          AND tenant_id = :tid
          AND membership_status = 'active'
    """), {
        "uid": actor_uid,
        "tid": target_tenant_id,
    }).mappings().one_or_none()

    if not login_row:
        raise ValueError(
            f"Audit actor: user {pg_text} (id={actor_uid}) neni active member "
            f"tenantu id={target_tenant_id}. Pridej v UI clenstvi tenantu."
        )

    db_login = login_row["db_login"]
    if not db_login or not db_login.strip():
        raise ValueError(
            f"Audit actor: db_login neni nastaven pro {pg_text} "
            f"(user.id={actor_uid}, tenant.id={target_tenant_id}). "
            f"Nastav v UI Uzivatel → tenant member → db_login. "
            f"Marti's fail visible doctrine (28.5.) — bez db_login MSSQL "
            f"audit neprobehne."
        )

    result["mssql_text"] = db_login.strip()
    return result


# ────────────────────────────────────────────────────────────────────────
# Helper: dc_code → tenant_id mapping
# ────────────────────────────────────────────────────────────────────────

# Per dc_code → tenant_id pro MSSQL audit lookup.
# Marti's 16. darek-scene 12.5. večer + Phase 35-E.3 router.py EUROSOFT_TENANT_ID=2.
_DC_CODE_TENANT_MAP: dict[str, int] = {
    "eurosoft_db_ec": 2,  # EUROSOFT tenant
    # "intersoft_db_is": 3,  # INTERSOFT tenant — pridej az bude potreba
}


def resolve_tenant_id_from_dc_code(dc_code: str | None) -> int | None:
    """Map fw.db_connection.code (dc_code) na public.tenants.id.

    Pouzito v MSSQL audit branchi — dc_code "eurosoft_db_ec" → tenant_id=2
    → user_tenants.db_login lookup per (uid, tenant_id=2).

    Args:
        dc_code: fw.db_connection.code (e.g., "eurosoft_db_ec")

    Returns:
        tenant_id pokud known, jinak None.
    """
    if not dc_code:
        return None
    return _DC_CODE_TENANT_MAP.get(dc_code.lower().strip())
