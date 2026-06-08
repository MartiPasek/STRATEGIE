#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""STRATEGIE netscan agent (Marti 5.6.2026, cesta B).

Bezi na EC-SERVER2 (na firemni LAN, dosahne na Mikrotik). Pravidelne (a 60 s)
precte z Mikrotiku DHCP leases + wireless registracni tabulku (= IP/MAC/hostname/
SSID + kdo je online) a POSTne seznam na STRATEGIE endpoint /app/netscan/ingest
(X-Deploy-Token). Backend upsertne do fw.hr_device dle MAC. Zarizeni na firemni
siti = "v budove".

Bez Mikrotiku se ZADNA data neztrati — agent jen mlci a loguje chybu.

Konfigurace z ENV (AppEnvironmentExtra v NSSM — NE Machine env, NE do gitu):
  MIKROTIK_HOST       IP/host routeru na LAN (napr. 192.168.30.1)
  MIKROTIK_USER       read-only API uzivatel
  MIKROTIK_PASS       heslo
  MIKROTIK_MODE       'rest' (RouterOS v7, HTTPS) | 'api' (v6, port 8728, vyzaduje librouteros)
  MIKROTIK_REST_SCHEME 'https' (default) | 'http'
  MIKROTIK_VERIFY_TLS '0' (default, self-signed router cert) | '1'
  STRATEGIE_URL       default https://strategie-ai.com
  STRATEGIE_DEPLOY_TOKEN  token (stejny jako pro deploy/notify)
  NETSCAN_INTERVAL_S  default 60
  NETSCAN_DRYRUN      '1' = jen vypis, neodesilat (test)

Spusteni rucne (test):
  set MIKROTIK_HOST=192.168.30.1 & set MIKROTIK_USER=stratread & ...
  python scripts\netscan_agent.py --once

NSSM sluzba (pondeli, az budou creds):
  C:\Tools\nssm.exe install STRATEGIE-NETSCAN python C:\Projekty\STRATEGIE\scripts\netscan_agent.py
  C:\Tools\nssm.exe set STRATEGIE-NETSCAN AppDirectory C:\Projekty\STRATEGIE
  C:\Tools\nssm.exe set STRATEGIE-NETSCAN AppEnvironmentExtra MIKROTIK_HOST=... MIKROTIK_USER=... MIKROTIK_PASS=... MIKROTIK_MODE=rest STRATEGIE_DEPLOY_TOKEN=...
  C:\Tools\nssm.exe start STRATEGIE-NETSCAN
"""
import base64
import json
import os
import ssl
import sys
import time
import urllib.request
import urllib.error

HOST = os.environ.get("MIKROTIK_HOST", "").strip()
USER = os.environ.get("MIKROTIK_USER", "").strip()
PASS = os.environ.get("MIKROTIK_PASS", "")
MODE = os.environ.get("MIKROTIK_MODE", "rest").strip().lower()
SCHEME = os.environ.get("MIKROTIK_REST_SCHEME", "https").strip().lower()
VERIFY_TLS = os.environ.get("MIKROTIK_VERIFY_TLS", "0").strip() == "1"
STRATEGIE_URL = os.environ.get("STRATEGIE_URL", "https://strategie-ai.com").rstrip("/")
TOKEN = os.environ.get("STRATEGIE_DEPLOY_TOKEN", "")
INTERVAL_S = int(os.environ.get("NETSCAN_INTERVAL_S", "60") or "60")
DRYRUN = os.environ.get("NETSCAN_DRYRUN", "").strip() == "1"


def _log(msg):
    print(f"[netscan {time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _rest_get(path):
    """RouterOS v7 REST GET → list[dict]. path napr. '/ip/dhcp-server/lease'."""
    url = f"{SCHEME}://{HOST}/rest{path}"
    auth = base64.b64encode(f"{USER}:{PASS}".encode()).decode()
    req = urllib.request.Request(url, headers={"Authorization": f"Basic {auth}"})
    ctx = None
    if SCHEME == "https" and not VERIFY_TLS:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def _collect_rest():
    """RouterOS v7: DHCP leases + wireless/wifi registration → device list."""
    devices = {}
    # DHCP leases — IP/MAC/hostname/status
    try:
        for le in _rest_get("/ip/dhcp-server/lease"):
            mac = (le.get("mac-address") or "").strip().lower()
            if not mac:
                continue
            status = (le.get("status") or "").lower()
            active = bool(le.get("active-address")) or status == "bound"
            devices[mac] = {
                "mac": mac,
                "ip": le.get("active-address") or le.get("address") or "",
                "hostname": le.get("host-name") or le.get("comment") or "",
                "ssid": "",
                "active": active,
            }
    except Exception as exc:
        _log(f"dhcp lease read fail: {exc}")
    # Wireless registration — MAC → SSID (kdo je na WiFi = online). Cesty se
    # lisi dle RouterOS (wireless vs wifiwave2 vs wifi). Zkusime postupne.
    for rpath in ("/interface/wireless/registration-table",
                  "/interface/wifiwave2/registration-table",
                  "/interface/wifi/registration-table"):
        try:
            regs = _rest_get(rpath)
        except Exception:
            continue
        for rg in regs:
            mac = (rg.get("mac-address") or "").strip().lower()
            if not mac:
                continue
            ssid = rg.get("ssid") or rg.get("interface") or ""
            d = devices.setdefault(mac, {"mac": mac, "ip": "", "hostname": "", "ssid": "", "active": True})
            d["ssid"] = ssid
            d["active"] = True
        break  # prvni existujici cesta staci
    return list(devices.values())


def _collect_api():
    """RouterOS v6 binary API — 'librouteros'. Plain API = port 8728;
    api-ssl (TLS, doporuceno) = port 8729 + MIKROTIK_API_SSL=1 (Marti 8.6.,
    Michal zapnul api-ssl). Router self-signed cert -> verify vypnuty."""
    try:
        from librouteros import connect  # type: ignore
    except Exception:
        _log("librouteros neni nainstalovan (v6 API). pip install librouteros")
        return []
    api_ssl = os.environ.get("MIKROTIK_API_SSL", "").strip() == "1"
    kwargs = {"host": HOST, "username": USER, "password": PASS}
    if api_ssl:
        import ssl as _ssl
        ctx = _ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = _ssl.CERT_NONE
        kwargs["ssl_wrapper"] = ctx.wrap_socket
        kwargs["port"] = int(os.environ.get("MIKROTIK_API_PORT", "8729") or "8729")
        _log("api-ssl mode (TLS, port %s)" % kwargs["port"])
    else:
        kwargs["port"] = int(os.environ.get("MIKROTIK_API_PORT", "8728") or "8728")
    api = connect(**kwargs)
    devices = {}
    try:
        for le in api.path("ip", "dhcp-server", "lease"):
            mac = (le.get("mac-address") or "").strip().lower()
            if not mac:
                continue
            devices[mac] = {
                "mac": mac,
                "ip": le.get("active-address") or le.get("address") or "",
                "hostname": le.get("host-name") or "",
                "ssid": "",
                "active": le.get("status") == "bound" or bool(le.get("active-address")),
            }
        try:
            for rg in api.path("interface", "wireless", "registration-table"):
                mac = (rg.get("mac-address") or "").strip().lower()
                if not mac:
                    continue
                d = devices.setdefault(mac, {"mac": mac, "ip": "", "hostname": "", "ssid": "", "active": True})
                d["ssid"] = rg.get("ssid") or ""
                d["active"] = True
        except Exception:
            pass
    finally:
        try:
            api.close()
        except Exception:
            pass
    return list(devices.values())


def collect():
    return _collect_api() if MODE == "api" else _collect_rest()


def push(devices):
    payload = json.dumps({"devices": devices}).encode("utf-8")
    req = urllib.request.Request(
        f"{STRATEGIE_URL}/api/v1/erp/app/netscan/ingest",
        data=payload, method="POST",
        headers={"Content-Type": "application/json", "X-Deploy-Token": TOKEN},
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def tick():
    if not HOST or not USER:
        _log("MIKROTIK_HOST/USER nenastaveno — cekam na konfiguraci (pondeli).")
        return
    devs = collect()
    active = [d for d in devs if d.get("active")]
    _log(f"nalezeno {len(devs)} zarizeni, {len(active)} aktivnich")
    if DRYRUN:
        for d in active[:50]:
            _log(f"  {d['mac']}  ip={d['ip']}  host={d['hostname']}  ssid={d['ssid']}")
        return
    if not TOKEN:
        _log("STRATEGIE_DEPLOY_TOKEN nenastaven — neodesilam.")
        return
    try:
        res = push(active)
        _log(f"odeslano → {res}")
    except urllib.error.HTTPError as exc:
        _log(f"ingest HTTP {exc.code}: {exc.read()[:200]}")
    except Exception as exc:
        _log(f"ingest fail: {exc}")


def main():
    once = "--once" in sys.argv
    _log(f"start mode={MODE} host={HOST or '(nenastaven)'} interval={INTERVAL_S}s dryrun={DRYRUN}")
    if once:
        tick()
        return
    while True:
        try:
            tick()
        except Exception as exc:
            _log(f"tick fail: {exc}")
        time.sleep(INTERVAL_S)


if __name__ == "__main__":
    main()
