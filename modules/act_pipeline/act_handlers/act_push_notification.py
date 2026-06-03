"""act_push_notification — backend handler: notifikace na mobil.

V telefonním flow je vlastní doručení na mobil řešené frontou fw.phone_dial_request
(mobil pollne /pending). Tento handler je generický bod pro budoucí kanály
(FCM apod.). result: sent / failed. error_mode obvykle 'continue' (nekritické).

params: channel (default "mobile"), message (volitelné)
inputs: target_user_id, phone, label (volitelné)
"""
from __future__ import annotations

from core.log_queue import log_event


def run(ctx):
    p = ctx.get("params") or {}
    inp = ctx.get("inputs") or {}
    channel = p.get("channel") or "mobile"

    if ctx.get("dry_run"):
        return {"result_code": "sent", "output": {"channel": channel, "dry_run": True}}

    try:
        # v1: zaloguj záměr (reálné doručení drží fronta phone_dial_request /
        # budoucí FCM). Nekritické — error_mode=continue.
        log_event(level="info", source="py", module_id="act:push_notification",
                  message="push_notification (%s) target_user=%s phone=%s" % (
                      channel, inp.get("target_user_id"), inp.get("phone")),
                  extra={"channel": channel, "inputs": inp})
        return {"result_code": "sent", "output": {"channel": channel}}
    except Exception as exc:
        return {"result_code": "failed", "output": {"detail": "%s: %s" % (type(exc).__name__, exc)}}
