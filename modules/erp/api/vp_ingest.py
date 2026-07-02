"""
VP (vedoucí projektu) ingest — projects@ email_inbox → tenant.vp_poptavka.

Nervový systém vedoucích projektu (Marti 2.7.2026, návrh docs/vp_projekty_ingest_design.md,
konzultace Marti-AI). Fáze 2: whitelist domén (GDPR gate) + dedup + založení raw záznamu.
Triáž (AI klasifikace typ/zákazník/shrnutí) + thread grouping = fáze 3.

Bezpečné pustit i před vytvořením schránky projects@ — pokud mailbox není připojen,
vrací no-op (ok=False, reason). GDPR (Marti-AI): sbíráme JEN příchozí maily z whitelistovaných
domén; ostatní se přeskočí (nezakládáme záznam).
"""
from __future__ import annotations

from sqlalchemy import text as _t

from core.database_data import get_data_session
from core.logging import get_logger

logger = get_logger("vp_ingest")

VP_MAILBOX_UPN = "projects@eurosoft.com"
DEFAULT_TENANT = 2  # EUROSOFT


def _domain_of(email: str | None) -> str | None:
    if not email or "@" not in email:
        return None
    return email.rsplit("@", 1)[1].strip().lower().rstrip(">").strip()


def _mailbox_id(s, upn: str = VP_MAILBOX_UPN) -> int | None:
    row = s.execute(
        _t("SELECT id FROM mailboxes WHERE lower(email_upn)=lower(:u) AND active"),
        {"u": upn},
    ).first()
    return row[0] if row else None


def sync_vp_poptavky(tenant_id: int = DEFAULT_TENANT, limit: int = 200) -> dict:
    """
    Projde nové příchozí maily schránky projects@ (email_inbox), aplikuje whitelist
    domén odesílatele a založí raw záznamy do tenant.vp_poptavka (stav='nova',
    typ='neurcen' — triáž doplní fáze 3). Idempotentní: dedup přes message_id.
    """
    s = get_data_session()
    try:
        mid = _mailbox_id(s)
        if not mid:
            return {"ok": False, "reason": "schranka projects@ zatim nepripojena",
                    "mailbox_upn": VP_MAILBOX_UPN}

        wl = {
            r[0]
            for r in s.execute(
                _t("SELECT lower(domain) FROM tenant.vp_domain_whitelist "
                   "WHERE tenant_id=:t AND active"),
                {"t": tenant_id},
            )
        }

        rows = s.execute(
            _t("""
                SELECT ei.id, ei.message_id, ei.from_email, ei.from_name,
                       ei.to_email, ei.subject, ei.received_at
                FROM email_inbox ei
                WHERE ei.mailbox_id = :mid
                  AND NOT EXISTS (
                        SELECT 1 FROM tenant.vp_poptavka p
                        WHERE p.tenant_id = :t AND p.message_id = ei.message_id)
                ORDER BY ei.id
                LIMIT :lim
            """),
            {"mid": mid, "t": tenant_id, "lim": limit},
        ).mappings().all()

        created = 0
        skip_domain = 0
        skipped_examples: list[str] = []
        for r in rows:
            dom = _domain_of(r["from_email"])
            if not dom or dom not in wl:
                skip_domain += 1
                if len(skipped_examples) < 5 and dom:
                    skipped_examples.append(dom)
                continue
            s.execute(
                _t("""
                    INSERT INTO tenant.vp_poptavka
                      (tenant_id, source_email_id, message_id, smer, from_email,
                       from_name, to_email, subject, received_at, typ, stav)
                    VALUES
                      (:t, :sid, :msg, 'in', :fe, :fn, :te, :subj, :rec,
                       'neurcen', 'nova')
                    ON CONFLICT (tenant_id, message_id)
                        WHERE message_id IS NOT NULL DO NOTHING
                """),
                {"t": tenant_id, "sid": r["id"], "msg": r["message_id"],
                 "fe": r["from_email"], "fn": r["from_name"], "te": r["to_email"],
                 "subj": r["subject"], "rec": r["received_at"]},
            )
            created += 1

        s.commit()
        logger.info("VP ingest | mailbox=%s | nova=%s | skip_domena=%s", mid, created, skip_domain)
        return {"ok": True, "mailbox_id": mid, "nova": created,
                "skip_domena": skip_domain, "skip_priklady": skipped_examples,
                "whitelist": sorted(wl)}
    finally:
        s.close()


def info(tenant_id: int = DEFAULT_TENANT) -> dict:
    """Přehled stavu VP poptávek + whitelist + zda je schránka připojena."""
    s = get_data_session()
    try:
        mid = _mailbox_id(s)
        by_stav = {
            row[0]: row[1]
            for row in s.execute(
                _t("SELECT stav, count(*) FROM tenant.vp_poptavka "
                   "WHERE tenant_id=:t GROUP BY stav"),
                {"t": tenant_id},
            )
        }
        wl = [
            {"domain": r[0], "kind": r[1]}
            for r in s.execute(
                _t("SELECT domain, kind FROM tenant.vp_domain_whitelist "
                   "WHERE tenant_id=:t AND active ORDER BY domain"),
                {"t": tenant_id},
            )
        ]
        return {"ok": True, "mailbox_pripojen": mid is not None,
                "mailbox_upn": VP_MAILBOX_UPN, "poptavky_dle_stavu": by_stav,
                "whitelist": wl}
    finally:
        s.close()
