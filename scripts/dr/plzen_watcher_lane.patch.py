# PATCH pro scripts/claude_sql_runner.py — enqueue lane "CLAUDE_PLZEN" (Claude C23, 23.7.2026)
# Srovnáno s živým souborem (helpery: _log, HTTP_TIMEOUT_SEC=30, ts=datetime.now(timezone.utc).strftime).
# Aplikovat AŽ po opravě token-401 (jinak enqueue POSTuje na endpoint, co vrací 401).
#
# ── EDIT 1: vložit ZA blok CLOUD_URL/DEPLOY_URL/PUSH_URL (~ř.188; CLOUD_URL už musí být definované) ──
PLZEN_MSG_FILE    = BRIDGE_DIR / "CLAUDE_PLZEN.txt"       # ř.1 = label; další řádky = PowerShell příkaz
PLZEN_GO_FILE     = BRIDGE_DIR / "CLAUDE_PLZEN_GO.txt"    # trigger (zapsat JAKO POSLEDNÍ)
PLZEN_OUT_FILE    = BRIDGE_DIR / "CLAUDE_PLZEN_OUT.txt"   # výsledek zařazení
PLZEN_AUDIT_FILE  = BRIDGE_DIR / "CLAUDE_PLZEN_LOG.txt"   # append-only audit
PLZEN_ENQUEUE_URL = CLOUD_URL.replace("/api/v1/erp/diag-sql", "/api/v1/ops/plzen/enqueue")


# ── EDIT 2: vložit celou funkci PŘED `def main() -> None:` (~ř.1767) ──
def _process_plzen() -> None:
    """Enqueue lane: přečti CLAUDE_PLZEN.txt (ř.1=label, zbytek=příkaz), POSTni na cloud
    /plzen/enqueue s X-Deploy-Token, zapiš CLAUDE_PLZEN_OUT.txt + audit. GO se uklidí.
    Enqueue jen ZAŘADÍ; výsledek Claude čte přes read-only SQL most z fw.plzen_cmd_queue."""
    import json as _json
    import urllib.request as _rq
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    try:
        raw = PLZEN_MSG_FILE.read_text(encoding="utf-8", errors="replace").strip()
    except Exception:
        raw = ""
    lines = raw.splitlines()
    label = (lines[0].strip() if lines else "")[:200]
    command = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""

    def _out(status: str, body: str) -> None:
        try:
            PLZEN_OUT_FILE.write_text(f"# PLZEN ENQUEUE: {status}\n# {ts}\n{body}\n", encoding="utf-8")
        except OSError as exc:
            _log(f"write PLZEN_OUT failed: {exc}")
        try:
            with PLZEN_AUDIT_FILE.open("a", encoding="utf-8") as fh:
                fh.write(f"[{ts}] {status} label={label!r} cmd_len={len(command)} :: {body[:200]}\n")
        except OSError:
            pass
        _log(f"PLZEN enqueue: {status} label={label!r}")
        try:
            if PLZEN_GO_FILE.exists():
                PLZEN_GO_FILE.unlink()
        except OSError:
            pass

    if not command:
        _out("ODMITNUTO", "Prazdny prikaz (radek 2+ musi obsahovat PowerShell).")
        return
    token = (os.environ.get("STRATEGIE_DEPLOY_TOKEN", "") or "").strip()
    if not token:
        _out("CHYBA", "STRATEGIE_DEPLOY_TOKEN neni v env watcheru.")
        return
    try:
        payload = _json.dumps({"command": command, "label": label, "created_by": "claude-23"}).encode("utf-8")
        rq = _rq.Request(PLZEN_ENQUEUE_URL, data=payload, method="POST",
                         headers={"Content-Type": "application/json", "X-Deploy-Token": token})
        with _rq.urlopen(rq, timeout=HTTP_TIMEOUT_SEC) as resp:
            data = _json.loads(resp.read().decode("utf-8", errors="replace"))
    except Exception as exc:
        _out("CHYBA", f"enqueue POST selhal: {str(exc)[:250]}")
        return
    if data.get("ok"):
        _out("OK", f"nonce={data.get('nonce')} id={data.get('id')} duplicate={data.get('duplicate', False)}")
    else:
        _out("CHYBA", f"cloud: {str(data)[:250]}")


# ── EDIT 3: v main() dispatch, HNED ZA blokem OPS (`if OPS_GO_FILE.exists(): _process_ops()...` ~ř.1801) ──
#                 if PLZEN_GO_FILE.exists():
#                     _process_plzen(); _did_work = True
#    (celá while smyčka už je obalená try/except → pád lane neshodí heartbeat)
