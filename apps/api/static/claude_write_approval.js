/* eslint-disable */
/**
 * claude_write_approval.js — Claude SQL bridge Krok 2 (Marti 1.6.2026).
 * ─────────────────────────────────────────────────────────────────────────────
 * Když Claude pošle přes bridge WRITE SQL, cloud ho nespustí ale uloží jako
 * pending. Tenhle poller (chat + ERP) ho ukáže Martimu jako banner nahoře se
 * SQL textem → [Potvrdit a spustit] / [Odmítnout]. Po rozhodnutí cloud zápis
 * provede (Marti-AI engine) a watcher si výsledek vyzvedne.
 *
 * Parent-only: /diag-write/pending vrátí 403 ostatním → banner se nezobrazí.
 * Self-contained, sdílené chatem i ERP.
 */
(function () {
  "use strict";

  var PENDING = "/api/v1/erp/diag-write/pending";
  var POLL_MS = 4000;
  var _shownId = null;
  var _el = null;

  // ── zvukový signál při novém požadavku ke schválení (Marti 2.6.2026) ──
  var _ac = null;
  function _audioCtx() {
    try {
      if (!_ac) {
        var AC = window.AudioContext || window.webkitAudioContext;
        if (AC) _ac = new AC();
      }
      if (_ac && _ac.state === "suspended") _ac.resume();
    } catch (e) {}
    return _ac;
  }
  // prohlížeč blokuje zvuk před prvním gestem → odemkneme při interakci
  function _unlock() { _audioCtx(); }
  document.addEventListener("pointerdown", _unlock, { once: true, capture: true });
  document.addEventListener("keydown", _unlock, { once: true, capture: true });

  function _tone(ctx, freq, startAt, dur) {
    var osc = ctx.createOscillator();
    var g = ctx.createGain();
    osc.type = "sine";
    osc.frequency.value = freq;
    g.gain.setValueAtTime(0.0001, startAt);
    g.gain.exponentialRampToValueAtTime(0.09, startAt + 0.02);
    g.gain.exponentialRampToValueAtTime(0.0001, startAt + dur);
    osc.connect(g); g.connect(ctx.destination);
    osc.start(startAt);
    osc.stop(startAt + dur + 0.03);
  }
  function _beep() {
    try {
      var ctx = _audioCtx();
      if (!ctx) return;
      var t0 = ctx.currentTime + 0.01;
      _tone(ctx, 880.0, t0, 0.14);            // jemné „ding-"
      _tone(ctx, 1174.66, t0 + 0.16, 0.18);   // „-dong"
    } catch (e) {}
  }

  function _remove() {
    if (_el) { try { _el.remove(); } catch (e) {} _el = null; }
    _shownId = null;
  }

  function _decide(id, decision, btn) {
    if (btn) { btn.disabled = true; btn.textContent = "…"; }
    fetch("/api/v1/erp/diag-write/" + id + "/decide", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
      body: JSON.stringify({ decision: decision }),
    })
      .then(function (r) { return r.json(); })
      .then(function () { _remove(); _tick(); })
      .catch(function () { if (btn) { btn.disabled = false; } });
  }

  function _show(reqObj) {
    if (_shownId === reqObj.id) return;
    _remove();
    _shownId = reqObj.id;
    _beep();

    var bar = document.createElement("div");
    bar.style.cssText =
      "position:fixed;top:0;left:0;right:0;z-index:100080;" +
      "background:#3a2e1f;border-bottom:2px solid #a87a3a;color:#f4e8d8;" +
      "padding:12px 14px;box-shadow:0 4px 16px rgba(0,0,0,0.5);font-size:14px;";

    var t = document.createElement("div");
    t.style.cssText = "font-weight:600;margin-bottom:6px;";
    t.textContent = "🔶 Claude chce spustit zápis (request #" + reqObj.id +
      " · db=" + reqObj.db_target + ")";
    bar.appendChild(t);

    var pre = document.createElement("pre");
    pre.style.cssText =
      "margin:0 0 8px;padding:8px;background:#1f1810;border-radius:4px;" +
      "overflow:auto;max-height:180px;font-size:12px;white-space:pre-wrap;color:#e8dcc8;";
    pre.textContent = reqObj.sql_text || "";
    bar.appendChild(pre);

    var row = document.createElement("div");
    row.style.cssText = "display:flex;gap:8px;justify-content:flex-end;flex-wrap:wrap;";

    var ok = document.createElement("button");
    ok.type = "button";
    ok.textContent = "✓ Potvrdit a spustit";
    ok.style.cssText = "background:#3a7a3a;color:#fff;border:none;padding:9px 16px;" +
      "border-radius:5px;font-weight:600;cursor:pointer;";
    ok.addEventListener("click", function () { _decide(reqObj.id, "approve", ok); });
    row.appendChild(ok);

    var no = document.createElement("button");
    no.type = "button";
    no.textContent = "✕ Odmítnout";
    no.style.cssText = "background:#5a3a3a;color:#fff;border:none;padding:9px 16px;" +
      "border-radius:5px;cursor:pointer;";
    no.addEventListener("click", function () { _decide(reqObj.id, "reject", no); });
    row.appendChild(no);

    bar.appendChild(row);
    document.body.appendChild(bar);
    _el = bar;
  }

  var _pollTimer = null;
  var _stopped = false;   // 403 = uzivatel neni parent -> zastav polling

  function _tick() {
    if (_stopped) return;
    try {
      fetch(PENDING, { credentials: "same-origin" })
        .then(function (r) {
          // 403 = uzivatel neni rodic (nema Claude bridge / approval banner).
          // Zastav polling, at nezahlcuje diag_log warningy (Marti 3.6.:
          // stovky 403/min od Pavla — non-parent poller bezel kazdou minutu).
          if (r.status === 403) {
            _stopped = true;
            if (_pollTimer) { clearInterval(_pollTimer); _pollTimer = null; }
            return null;
          }
          return r.ok ? r.json() : null;
        })
        .then(function (j) {
          if (!j || !j.ok) return;
          var reqs = j.requests || [];
          if (!reqs.length) { _remove(); return; }
          var still = _shownId && reqs.some(function (x) { return x.id === _shownId; });
          if (!still) _show(reqs[0]);
        })
        .catch(function () {});
    } catch (e) {}
  }

  setTimeout(_tick, 2500);
  _pollTimer = setInterval(_tick, POLL_MS);
  document.addEventListener("visibilitychange", function () {
    if (!document.hidden && !_stopped) _tick();
  });
})();
