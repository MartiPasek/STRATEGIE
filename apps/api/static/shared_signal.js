/* eslint-disable */
/**
 * shared_signal.js — signál nové zprávy ve SDÍLENÉ konverzaci (Marti 3.6.2026).
 * ─────────────────────────────────────────────────────────────────────────────
 * Když ve sdílené konverzaci přijde zpráva od někoho jiného (jiný člověk nebo
 * Marti-AI), ozve se jemný „ding-dong" (jako u write-approval) a **opakuje se**
 * v intervalu, dokud uživatel konverzaci neotevře (= nepotvrdí).
 *
 * Funguje v CHATU i v ERP (sdílené přes localStorage, stejný origin):
 *  - CHAT: ding; když ale tu konverzaci právě čteš (viditelná), auto-potvrdí (žádný ding).
 *  - ERP (Pavel jen v ERP): ding + animace ikonky „Tvoje Marti" (#erpMartiAiBtn);
 *    proklik na ni → otevře tu sdílenou konverzaci v chatu.
 *
 * Backend: GET /api/v1/conversation/shared-activity → { activity: {latest_message_id,
 * conversation_id, conv_title, author_name, at} | null }.
 *
 * Interval opakování: localStorage `stg_shared_signal_interval_s` (default 30 s) —
 * později nastavitelné v prostředí aplikace.
 *
 * Self-contained, bez závislostí. Expozice: window.SharedSignal.
 */
(function () {
  "use strict";

  var EP = "/api/v1/conversation/shared-activity";
  var POLL_MS = 15000;
  var DEFAULT_REPEAT_S = 30;
  var SEEN_KEY = "stg_shared_seen_msg";   // per-origin → chat i ERP sdílí

  var _ac = null, _repeatTimer = null, _signalingId = null;
  var _btnEl = null, _btnHandler = null, _curAct = null;

  function _isErp() { return location.pathname.indexOf("/erp") === 0; }

  // ── audio (ding-dong, reuse z write-approval) ──
  function _audioCtx() {
    try {
      if (!_ac) { var AC = window.AudioContext || window.webkitAudioContext; if (AC) _ac = new AC(); }
      if (_ac && _ac.state === "suspended") _ac.resume();
    } catch (e) {}
    return _ac;
  }
  document.addEventListener("pointerdown", _audioCtx, { once: true, capture: true });
  document.addEventListener("keydown", _audioCtx, { once: true, capture: true });
  function _tone(ctx, f, t, d) {
    var o = ctx.createOscillator(), g = ctx.createGain();
    o.type = "sine"; o.frequency.value = f;
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(0.09, t + 0.02);
    g.gain.exponentialRampToValueAtTime(0.0001, t + d);
    o.connect(g); g.connect(ctx.destination);
    o.start(t); o.stop(t + d + 0.03);
  }
  function _beep() {
    try {
      var c = _audioCtx(); if (!c) return;
      var t = c.currentTime + 0.01;
      _tone(c, 880.0, t, 0.14);
      _tone(c, 1174.66, t + 0.16, 0.18);
    } catch (e) {}
  }

  function _seen() { try { return parseInt(localStorage.getItem(SEEN_KEY) || "0", 10) || 0; } catch (e) { return 0; } }
  function _setSeen(id) { try { localStorage.setItem(SEEN_KEY, String(id)); } catch (e) {} }
  function _repeatMs() {
    var s = DEFAULT_REPEAT_S;
    try { var v = parseInt(localStorage.getItem("stg_shared_signal_interval_s") || "", 10); if (v >= 5) s = v; } catch (e) {}
    return s * 1000;
  }

  function _stopRepeat() {
    if (_repeatTimer) { clearInterval(_repeatTimer); _repeatTimer = null; }
    _signalingId = null;
    _stopAvatar();
  }
  function _startRepeat() {
    if (_repeatTimer) return;
    _repeatTimer = setInterval(function () {
      if (_curAct && _curAct.latest_message_id > _seen()) { _beep(); }
      else { _stopRepeat(); }
    }, _repeatMs());
  }

  // ── ERP: animace ikonky „Tvoje Marti" + proklik ──
  function _injectPulseCss() {
    if (document.getElementById("stg-shared-pulse-css")) return;
    var st = document.createElement("style");
    st.id = "stg-shared-pulse-css";
    st.textContent =
      "@keyframes stgSharedPulse{0%,100%{box-shadow:0 0 0 0 rgba(249,115,22,0);}" +
      "50%{box-shadow:0 0 0 5px rgba(249,115,22,.5);}}" +
      ".stg-shared-pulse{animation:stgSharedPulse 1.2s ease-in-out infinite!important;" +
      "border-radius:10px!important;outline:1px solid rgba(249,115,22,.6);}";
    document.head.appendChild(st);
  }
  function _animateAvatar(act) {
    var el = document.getElementById("erpMartiAiBtn");
    if (!el) return;
    _injectPulseCss();
    _btnEl = el;
    el.classList.add("stg-shared-pulse");
    el.setAttribute("title", "Nová zpráva ve sdílené konverzaci od " +
      (act.author_name || "") + " — klikni a otevři");
    if (!_btnHandler) {
      // capture fáze → poběží PŘED defaultním „otevři chat" handlerem
      _btnHandler = function (ev) {
        if (_curAct && _curAct.latest_message_id > _seen()) {
          ev.preventDefault(); ev.stopPropagation();
          var cid = _curAct.conversation_id;
          _setSeen(_curAct.latest_message_id);
          _stopRepeat();
          location.href = "/?open_conv=" + cid;
        }
      };
      el.addEventListener("click", _btnHandler, true);
    }
  }
  function _stopAvatar() {
    if (_btnEl) {
      try {
        _btnEl.classList.remove("stg-shared-pulse");
        _btnEl.removeAttribute("title");
      } catch (e) {}
    }
  }

  function _tick() {
    fetch(EP, { credentials: "same-origin", cache: "no-store" })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (j) {
        var act = j && j.activity;
        if (!act || !act.latest_message_id) { _stopRepeat(); return; }
        var seen = _seen();
        // baseline: úplně první běh (seen=0) → jen zapamatuj, neding pro historii
        if (seen === 0) { _setSeen(act.latest_message_id); return; }
        if (act.latest_message_id <= seen) { _stopRepeat(); return; }
        // NOVÁ aktivita
        _curAct = act;
        // chat + právě čtu tu konverzaci + viditelné → auto-potvrď (žádný ding)
        if (!_isErp() && document.visibilityState === "visible" &&
            window.__chatActiveConvId === act.conversation_id) {
          _setSeen(act.latest_message_id); _stopRepeat(); return;
        }
        if (_signalingId !== act.latest_message_id) {
          _signalingId = act.latest_message_id;
          _beep();
          if (_isErp()) _animateAvatar(act);
          _startRepeat();
        }
      })
      .catch(function () {});
  }

  setTimeout(_tick, 4000);
  setInterval(_tick, POLL_MS);
  document.addEventListener("visibilitychange", function () { if (!document.hidden) _tick(); });
  window.addEventListener("focus", _tick);

  // CHAT volá při otevření konverzace → potvrzení (stop signál) pokud sedí.
  window.SharedSignal = {
    notifyOpened: function (convId) {
      try { window.__chatActiveConvId = convId; } catch (e) {}
      if (_curAct && _curAct.conversation_id === convId) {
        _setSeen(_curAct.latest_message_id);
        _stopRepeat();
      }
    },
    ack: function () { if (_curAct) _setSeen(_curAct.latest_message_id); _stopRepeat(); },
  };
})();
