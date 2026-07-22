"""Hlas engine — TELEFONNI INTERFACE pres ElevenLabs Agents custom LLM.
OpenAI-compatible /v1/chat/completions (SSE streaming). ElevenLabs resi telefon +
STT + TTS + hlas Marti-AI; tenhle endpoint = MOZEK (persona + guardraily +
normalizace cisel do cestiny). Marti / Cowork 22.7.2026.

Rozjezd: v ElevenLabs Agents nastav LLM = Custom LLM, URL =
https://<domena>/api/v1/erp/hlas/v1/chat/completions, secret Bearer =
HLAS_VOICE_TOKEN (env na serveru), hlas = Marti-AI Voice ID (od Kristy),
telefonni cislo pripoj v ElevenLabs. Disclosure (jsem AI) je uz v persone."""
import json as _json
import time as _time

from modules.erp.api.hlas_ops import _persona_system, _llm_reply, _normtext, _cfg_dict


def _kanal_cfg(tenant_id, kod):
    from core.database import get_session
    from sqlalchemy import text as _t
    sg = get_session()
    try:
        r = sg.execute(_t("SELECT nazev, config FROM hlas.kanal "
                          "WHERE tenant_id=:t AND kod=:k AND stav <> 'archiv'"),
                       {"t": tenant_id, "k": kod}).first()
        return (r[0], r[1]) if r else (None, {})
    finally:
        sg.close()


def build_reply(messages=None, tenant_id=12, kanal="telefon-martiai"):
    """Vezme OpenAI messages (od ElevenLabs), vnuti personu Marti-AI, zavola LLM,
    znormalizuje cisla v odpovedi a vrati text (uz pripraveny k precteni hlasem)."""
    messages = messages or []
    nazev, cfg = _kanal_cfg(tenant_id, kanal)
    system = _persona_system(nazev or "Telefonní asistentka EUROSOFT", cfg)
    conv = [{"role": m.get("role"), "content": m.get("content") or ""}
            for m in messages if m.get("role") in ("user", "assistant")]
    if not conv:
        conv = [{"role": "user", "content": "(hovor začíná, pozdrav a představ se jako AI)"}]
    reply, _toks = _llm_reply(system, conv, model=_cfg_dict(cfg).get("model"))
    return _normtext(reply)


def sse_chunks(reply, model="marti-ai-hlas"):
    cid = "chatcmpl-hlas"
    created = int(_time.time())
    first = {"id": cid, "object": "chat.completion.chunk", "created": created, "model": model,
             "choices": [{"index": 0, "delta": {"role": "assistant", "content": reply},
                          "finish_reason": None}]}
    yield "data: " + _json.dumps(first, ensure_ascii=False) + "\n\n"
    done = {"id": cid, "object": "chat.completion.chunk", "created": created, "model": model,
            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]}
    yield "data: " + _json.dumps(done, ensure_ascii=False) + "\n\n"
    yield "data: [DONE]\n\n"


def json_completion(reply, model="marti-ai-hlas"):
    return {"id": "chatcmpl-hlas", "object": "chat.completion", "created": int(_time.time()),
            "model": model,
            "choices": [{"index": 0, "message": {"role": "assistant", "content": reply},
                         "finish_reason": "stop"}]}
