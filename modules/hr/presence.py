"""HR presence — detekce „v budově" z firemní IP (Marti 5.6.2026).

Princip: zařízení na firemní WiFi má egress = firemní veřejná IP. Každý
request na backend z té IP → daný člověk je v budově. Bez GPS, privacy-by-design.

Tabulky: fw.hr_building_network (co je „budova"), fw.hr_presence (aktuální stav),
fw.hr_presence_event (append-only log). Vše best-effort — presence nikdy
nesmí shodit request ani zpomalit.
"""
from __future__ import annotations

import ipaddress
import threading
import time

from sqlalchemy import text as _t

# Cache firemních sítí (refresh á 5 min) + per-(user,device) throttle zápisu
_nets_cache: dict = {"ts": 0.0, "nets": []}
_touch_ts: dict[tuple, float] = {}    # (uid, kind) -> last hr_presence upsert
_event_ts: dict[tuple, float] = {}    # (uid, kind) -> last event log
_lock = threading.Lock()

_PRESENCE_THROTTLE_S = 60      # hr_presence upsert max 1×/min/uživatel
_EVENT_THROTTLE_S = 300       # event log max 1×/5 min/uživatel
_NETS_TTL_S = 300


def _load_building_nets() -> list:
    now = time.time()
    if _nets_cache["nets"] and (now - _nets_cache["ts"] < _NETS_TTL_S):
        return _nets_cache["nets"]
    nets: list = []
    try:
        from core.database_data import get_data_session
        s = get_data_session()
        try:
            rows = s.execute(_t(
                "SELECT value FROM fw.hr_building_network "
                "WHERE is_active = true AND kind = 'ip'"
            )).fetchall()
            for r in rows:
                try:
                    nets.append(ipaddress.ip_network(str(r[0]), strict=False))
                except Exception:
                    pass
        finally:
            s.close()
        _nets_cache["nets"] = nets
        _nets_cache["ts"] = now
    except Exception:
        pass
    return _nets_cache["nets"]


def ip_in_building(ip_str: str | None) -> bool:
    if not ip_str:
        return False
    try:
        ip = ipaddress.ip_address(ip_str.strip())
    except Exception:
        return False
    for net in _load_building_nets():
        try:
            if ip in net:
                return True
        except Exception:
            pass
    return False


def device_kind(user_agent: str | None) -> str:
    """Hrubá klasifikace zařízení z User-Agent: 'mobile' vs 'pc'."""
    u = (user_agent or "").lower()
    if any(m in u for m in ("mobile", "android", "iphone", "ipod", "strategiemobil")):
        return "mobile"
    return "pc"


def touch_presence(uid: int | None, ip_str: str | None,
                   user_agent: str | None = None, source: str = "company_ip") -> None:
    """Když je IP firemní, zapíše presence pro daný typ zařízení (PC/mobil).
    Throttle 60 s/(uživatel, typ). Best-effort — nikdy neshodí request."""
    if not uid:
        return
    if not ip_in_building(ip_str):
        return
    kind = device_kind(user_agent)
    is_pc = (kind == "pc")
    is_mobile = (kind == "mobile")
    now = time.time()
    tkey = (int(uid), kind)
    with _lock:
        if now - _touch_ts.get(tkey, 0.0) < _PRESENCE_THROTTLE_S:
            return
        _touch_ts[tkey] = now
        log_event = (now - _event_ts.get(tkey, 0.0) >= _EVENT_THROTTLE_S)
        if log_event:
            _event_ts[tkey] = now
    try:
        from core.database_data import get_data_session
        s = get_data_session()
        try:
            # Overall sloupce (in_building/last_seen_at) = nejnovější signál
            # z libovolného zařízení; navíc per-zařízení pc_* / mobile_*.
            s.execute(_t("""
                INSERT INTO fw.hr_presence
                    (user_id, state, in_building, source, last_seen_at, updated_at,
                     pc_in_building, pc_last_seen_at,
                     mobile_in_building, mobile_last_seen_at)
                VALUES (:u, 'in_building', true, :src, now(), now(),
                        :is_pc, CASE WHEN :is_pc THEN now() END,
                        :is_mob, CASE WHEN :is_mob THEN now() END)
                ON CONFLICT (user_id) DO UPDATE SET
                    state = 'in_building', in_building = true, source = :src,
                    last_seen_at = now(), updated_at = now(),
                    pc_in_building = CASE WHEN :is_pc THEN true ELSE fw.hr_presence.pc_in_building END,
                    pc_last_seen_at = CASE WHEN :is_pc THEN now() ELSE fw.hr_presence.pc_last_seen_at END,
                    mobile_in_building = CASE WHEN :is_mob THEN true ELSE fw.hr_presence.mobile_in_building END,
                    mobile_last_seen_at = CASE WHEN :is_mob THEN now() ELSE fw.hr_presence.mobile_last_seen_at END
            """), {"u": int(uid), "src": source, "is_pc": is_pc, "is_mob": is_mobile})
            if log_event:
                s.execute(_t("""
                    INSERT INTO fw.hr_presence_event
                        (user_id, source, in_building, state)
                    VALUES (:u, :src, true, 'in_building')
                """), {"u": int(uid), "src": source + "_" + kind})
            s.commit()
        finally:
            s.close()
    except Exception:
        pass


def client_ip(request) -> str:
    """Reálná IP klienta za Caddy reverse proxy (X-Forwarded-For)."""
    try:
        xff = request.headers.get("x-forwarded-for")
        if xff:
            return xff.split(",")[0].strip()
        if request.client:
            return request.client.host or ""
    except Exception:
        pass
    return ""
