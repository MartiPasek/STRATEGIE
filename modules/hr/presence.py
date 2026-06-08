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
_dev_ts: dict[str, float] = {}        # device_key -> last hr_device upsert
_lock = threading.Lock()

_PRESENCE_THROTTLE_S = 60      # hr_presence upsert max 1×/min/uživatel
_EVENT_THROTTLE_S = 300       # event log max 1×/5 min/uživatel
_NETS_TTL_S = 300


def _load_building_nets() -> list:
    """Vrací list (ip_network, place) — place je 'building'/'home_office'/…"""
    now = time.time()
    if _nets_cache["nets"] and (now - _nets_cache["ts"] < _NETS_TTL_S):
        return _nets_cache["nets"]
    nets: list = []
    try:
        from core.database_data import get_data_session
        s = get_data_session()
        try:
            rows = s.execute(_t(
                "SELECT value, COALESCE(place,'building') FROM fw.hr_building_network "
                "WHERE is_active = true AND kind = 'ip'"
            )).fetchall()
            for r in rows:
                try:
                    nets.append((ipaddress.ip_network(str(r[0]), strict=False), str(r[1])))
                except Exception:
                    pass
        finally:
            s.close()
        _nets_cache["nets"] = nets
        _nets_cache["ts"] = now
    except Exception:
        pass
    return _nets_cache["nets"]


def ip_place(ip_str: str | None) -> str | None:
    """Místo dle IP ('building'/'home_office'/…) nebo None."""
    if not ip_str:
        return None
    try:
        ip = ipaddress.ip_address(ip_str.strip())
    except Exception:
        return None
    for net, place in _load_building_nets():
        try:
            if ip in net:
                return place
        except Exception:
            pass
    return None


def ip_in_building(ip_str: str | None) -> bool:
    return ip_place(ip_str) == "building"


_ssid_cache: dict = {"ts": 0.0, "ssids": {}}


def _load_building_ssids() -> dict:
    """Mapa firemních WiFi {ssid_lower: place} (kind='ssid')."""
    now = time.time()
    if _ssid_cache["ssids"] and (now - _ssid_cache["ts"] < _NETS_TTL_S):
        return _ssid_cache["ssids"]
    ssids: dict = {}
    try:
        from core.database_data import get_data_session
        s = get_data_session()
        try:
            rows = s.execute(_t(
                "SELECT lower(value), COALESCE(place,'building') "
                "FROM fw.hr_building_network "
                "WHERE is_active = true AND kind = 'ssid'"
            )).fetchall()
            ssids = {str(r[0]).strip(): str(r[1]) for r in rows if r[0]}
        finally:
            s.close()
        _ssid_cache["ssids"] = ssids
        _ssid_cache["ts"] = now
    except Exception:
        pass
    return _ssid_cache["ssids"]


def ssid_place(ssid: str | None) -> str | None:
    """Místo dle WiFi názvu ('building'/'home_office'/…) nebo None."""
    if not ssid:
        return None
    return _load_building_ssids().get(str(ssid).strip().lower())


def ssid_in_building(ssid: str | None) -> bool:
    return ssid_place(ssid) == "building"


def match_place(ip_str: str | None, ssid: str | None) -> str | None:
    """Místo zařízení: WiFi (přesnější) má přednost před IP. None = neznámé."""
    return ssid_place(ssid) or ip_place(ip_str)


def device_kind(user_agent: str | None) -> str:
    """Hrubá klasifikace zařízení z User-Agent: 'mobile' vs 'pc'."""
    u = (user_agent or "").lower()
    if any(m in u for m in ("mobile", "android", "iphone", "ipod", "strategiemobil")):
        return "mobile"
    return "pc"


def touch_presence(uid: int | None, ip_str: str | None,
                   user_agent: str | None = None, source: str = "company_ip",
                   force_kind: str | None = None) -> None:
    """Když je IP firemní, zapíše presence pro daný typ zařízení (PC/mobil).
    force_kind='mobile'/'pc' přebije klasifikaci z UA (např. heartbeat appky
    posílá UA 'okhttp', ale víme, že je to mobil).
    Throttle 60 s/(uživatel, typ). Best-effort — nikdy neshodí request."""
    if not uid:
        return
    if not ip_in_building(ip_str):
        return
    kind = force_kind if force_kind in ("pc", "mobile") else device_kind(user_agent)
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


def touch_device(device_key: str | None, device_type: str, name: str | None,
                 uid: int | None, ip_str: str | None, source: str,
                 ssid: str | None = None, force_place: str | None = None,
                 link_user: bool = True) -> None:
    """Upsert zařízení do IT inventury fw.hr_device + vazba na člověka (1:N).
    Presence (last_place) z firemní IP/WiFi, nebo force_place (např. Mikrotik:
    zařízení na firemní síti = v budově i drátově). link_user=False u
    síťově objevených (neznámý vlastník). Best-effort. device_key = stabilní id."""
    if not device_key:
        return
    now = time.time()
    with _lock:
        if now - _dev_ts.get(device_key, 0.0) < _PRESENCE_THROTTLE_S:
            return
        _dev_ts[device_key] = now
    place = force_place or match_place(ip_str, ssid)
    inb = (place == "building")
    try:
        from core.database_data import get_data_session
        s = get_data_session()
        try:
            row = s.execute(_t("""
                INSERT INTO fw.hr_device
                    (device_type, name, owner_user_id, device_key,
                     last_seen_at, last_source, last_in_building, last_ip, last_place,
                     first_seen_today,
                     bld_first, bld_last, out_first, out_last)
                VALUES (:dt, :nm, :uid, :dk, now(), :src, :inb, :ip, :place, now(),
                     CASE WHEN :inb THEN now() END, CASE WHEN :inb THEN now() END,
                     CASE WHEN :inb THEN NULL ELSE now() END, CASE WHEN :inb THEN NULL ELSE now() END)
                ON CONFLICT (device_key) WHERE device_key IS NOT NULL DO UPDATE SET
                    name = COALESCE(NULLIF(EXCLUDED.name, ''), fw.hr_device.name),
                    owner_user_id = COALESCE(fw.hr_device.owner_user_id, EXCLUDED.owner_user_id),
                    last_seen_at = now(), last_source = :src,
                    last_in_building = :inb, last_ip = :ip, last_place = :place,
                    -- Marti 8.6.: první spatření dne (reset přes půlnoc)
                    first_seen_today = CASE
                        WHEN fw.hr_device.first_seen_today IS NULL
                          OR fw.hr_device.first_seen_today::date < current_date
                        THEN now() ELSE fw.hr_device.first_seen_today END,
                    -- Marti 8.6.: zóny v budově / mimo — poprvé (reset/den) + naposledy
                    bld_first = CASE WHEN :inb AND (fw.hr_device.bld_first IS NULL
                                       OR fw.hr_device.bld_first::date < current_date)
                                     THEN now() ELSE fw.hr_device.bld_first END,
                    bld_last  = CASE WHEN :inb THEN now() ELSE fw.hr_device.bld_last END,
                    out_first = CASE WHEN NOT :inb AND (fw.hr_device.out_first IS NULL
                                       OR fw.hr_device.out_first::date < current_date)
                                     THEN now() ELSE fw.hr_device.out_first END,
                    out_last  = CASE WHEN NOT :inb THEN now() ELSE fw.hr_device.out_last END
                RETURNING id
            """), {"dt": device_type, "nm": (name or ""), "uid": uid, "dk": device_key,
                   "src": source, "inb": inb, "ip": (ip_str or ""),
                   "place": place}).fetchone()
            dev_id = row[0] if row else None
            if dev_id and uid and link_user:
                s.execute(_t("""
                    INSERT INTO fw.hr_device_user (device_id, user_id, rel)
                    VALUES (:d, :u, 'owner')
                    ON CONFLICT (device_id, user_id) DO NOTHING
                """), {"d": int(dev_id), "u": int(uid)})
            s.commit()
        finally:
            s.close()
    except Exception:
        pass


def refresh_user_phone(uid: int | None, ip_str: str | None) -> None:
    """Osvěží čerstvost telefonu uživatele (z 4s command-pollu appky). Řeší řídké
    heartbeaty (Android uspává) — poll běží spolehlivě, dokud appka žije.
    Marti 8.6.: obnovuje „naposledy" i MIMO budovu → „online (mimo)" místo offline.
    V budově → place='building'; mimo → place='away' (jen pokud zrovna není doma/
    u zákazníka z čerstvého netscanu). Throttle 60 s/uživatel. Best-effort."""
    if not uid:
        return
    in_bld = ip_in_building(ip_str)
    now = time.time()
    key = "phonepoll:" + str(int(uid))
    with _lock:
        if now - _dev_ts.get(key, 0.0) < _PRESENCE_THROTTLE_S:
            return
        _dev_ts[key] = now
    try:
        from core.database_data import get_data_session
        s = get_data_session()
        try:
            if in_bld:
                s.execute(_t("""
                    UPDATE fw.hr_device
                    SET last_seen_at = now(), last_in_building = true,
                        last_place = 'building', last_source = 'mobile_poll',
                        first_seen_today = CASE
                            WHEN first_seen_today IS NULL OR first_seen_today::date < current_date
                            THEN now() ELSE first_seen_today END,
                        bld_first = CASE WHEN bld_first IS NULL OR bld_first::date < current_date
                                         THEN now() ELSE bld_first END,
                        bld_last = now()
                    WHERE owner_user_id = :uid AND device_type = 'phone'
                      AND last_seen_at > now() - interval '2 days'
                """), {"uid": int(uid)})
            else:
                # Mimo budovu: jen „žije" → online (mimo). Nepřepisuj čerstvý
                # building/home/customer status (z netscanu < 12 min).
                s.execute(_t("""
                    UPDATE fw.hr_device
                    SET last_seen_at = now(), last_in_building = false,
                        last_source = 'mobile_poll',
                        last_place = CASE
                            WHEN last_place IN ('building','home_office','customer')
                                 AND last_seen_at > now() - interval '12 minutes'
                            THEN last_place ELSE 'away' END,
                        out_first = CASE WHEN out_first IS NULL OR out_first::date < current_date
                                         THEN now() ELSE out_first END,
                        out_last = now()
                    WHERE owner_user_id = :uid AND device_type = 'phone'
                      AND last_seen_at > now() - interval '2 days'
                """), {"uid": int(uid)})
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
