# -*- coding: utf-8 -*-
"""Testy skládání APNs notifikací pro iOS appku — běží bez DB i bez sítě.

Hlídají, že se iOS chová stejně jako Android (`DialPollService.notifyCommand`):
každý pending příkaz cinkne, `claude_ok` jde tiše, z payloadu se přenáší
`screen` / `label` a `url` jen u `open_url`.

Druhá půlka hlídá klasifikaci odpovědí APNs. Kdyby se přechodná chyba (výpadek
sítě, 429) vyhodnotila jako trvalá, notifikace by po prvním zaškobrtnutí
nedorazila NIKDY — proto na to test je.
"""
import json
import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(HERE)


def _modul():
    """Načte modules/erp/api/ios_push.py se stuby za fastapi/sqlalchemy —
    testujeme čistou logiku, ne HTTP vrstvu."""
    for jmeno, atributy in (
        ("fastapi", {"APIRouter": lambda **k: types.SimpleNamespace(
            post=lambda *a, **k: (lambda f: f), get=lambda *a, **k: (lambda f: f)),
            "Request": object}),
        ("fastapi.responses", {"JSONResponse": object}),
        ("sqlalchemy", {"text": lambda x: x}),
    ):
        if jmeno not in sys.modules:
            m = types.ModuleType(jmeno)
            m.__dict__.update(atributy)
            sys.modules[jmeno] = m
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "ios_push_test_modul", os.path.join(_ROOT, "modules", "erp", "api", "ios_push.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


IP = _modul()


# ── payload: co uvidí uživatel v liště ──────────────────────────────────────────

def test_bezny_prikaz_cinkne():
    p, tichy = IP._payload({
        "id": 42, "command_type": "claude_confirm", "title": "Schválit?",
        "message": "Dovolená 3 dny",
        "payload": json.dumps({"screen": "dovolena", "label": "Otevřít dovolenou"})})
    assert tichy is False
    assert p["aps"]["sound"] == "default"
    assert p["aps"]["interruption-level"] == "active"
    assert p["cmd_id"] == 42
    assert p["screen"] == "dovolena"
    assert p["label"] == "Otevřít dovolenou"


def test_claude_ok_je_tichy():
    """Android pro claude_ok používá kanál CH_OK s IMPORTANCE_LOW."""
    p, tichy = IP._payload({"id": 7, "command_type": "claude_ok",
                            "title": "Hotovo", "message": "", "payload": None})
    assert tichy is True
    assert "sound" not in p["aps"]
    assert p["aps"]["interruption-level"] == "passive"
    assert p["aps"]["alert"]["body"] == "Klepni pro zobrazení"


def test_url_jen_u_open_url():
    pl = json.dumps({"url": "https://strategie-ai.com/mobile#x", "screen": "chat"})
    p_open, _ = IP._payload({"id": 9, "command_type": "open_url",
                             "title": "T", "message": "M", "payload": pl})
    p_jiny, _ = IP._payload({"id": 10, "command_type": "claude_msg",
                             "title": "T", "message": "M", "payload": pl})
    assert p_open["url"] == "https://strategie-ai.com/mobile#x"
    assert "url" not in p_jiny


def test_rozbity_payload_neshodi_odeslani():
    p, _ = IP._payload({"id": 11, "command_type": "claude_msg",
                        "title": "T", "message": "M", "payload": "{tohle neni json"})
    assert p["cmd_id"] == 11


# ── klasifikace odpovědí APNs ───────────────────────────────────────────────────

def test_trvale_chyby_prikaz_odepisou():
    assert IP._trvala_chyba(410, "Unregistered") is True
    assert IP._trvala_chyba(400, "BadDeviceToken") is True
    assert IP._trvala_chyba(400, "DeviceTokenNotForTopic") is True


def test_prechodne_chyby_se_zkusi_znovu():
    assert IP._trvala_chyba(429, "TooManyRequests") is False
    assert IP._trvala_chyba(503, "ServiceUnavailable") is False
    assert IP._trvala_chyba(0, "timeout") is False          # síť spadla
    assert IP._trvala_chyba(403, "ExpiredProviderToken") is False
