/* eslint-disable */
/**
 * phone_dial_banner.js — Fáze 3 cross-device telefon (Marti 1.6.2026).
 * ─────────────────────────────────────────────────────────────────────────────
 * Mobil (PWA chat) pollne frontu fw.phone_dial_request → ťukací banner nahoře
 * → tap "Volat" → tel: dial → consume. PC pushne dial-request přes
 * erp_cell_actions.js (dvojklik na telefon) → objeví se tady na mobilu.
 *
 * Samostatný soubor — izolace syntax rizika od velkého inline scriptu
 * v index.html. Běží JEN na mobilu (PC iniciuje, nezobrazuje).
 */
(function () {
  "use strict";

  function isMobile() {
    try {
      if (/Mobi|Android|iPhone|iPad|iPod/i.test(navigator.userAgent || "")) return true;
      if (window.matchMedia && window.matchMedia("(pointer:coarse)").matches) return true;
    } catch (e) {}
    return false;
  }
  if (!isMobile()) return;  // jen mobil

  var POLL_MS = 6000;
  var _shownId = null;
  var _bannerEl = null;

  function _removeBanner() {
    if (_bannerEl) { try { _bannerEl.remove(); } catch (e) {} _bannerEl = null; }
    _shownId = null;
  }

  function _consume(id, status) {
    try {
      fetch("/api/v1/erp/phone-dial-request/" + id + "/consume", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "same-origin",
        body: JSON.stringify({ status: status }),
      }).catch(function () {});
    } catch (e) {}
  }

  // sendBeacon přežije navigaci na tel: (fetch by se zrušil → řádek by zůstal
  // pending → banner by se znovu objevil). Cookies jdou s beaconem automaticky.
  function _beaconConsume(id, status) {
    var url = "/api/v1/erp/phone-dial-request/" + id + "/consume";
    try {
      if (navigator.sendBeacon) {
        var blob = new Blob([JSON.stringify({ status: status })], { type: "application/json" });
        if (navigator.sendBeacon(url, blob)) return;
      }
    } catch (e) {}
    _consume(id, status);  // fallback
  }

  function _showBanner(reqObj) {
    if (_shownId === reqObj.id) return;
    _removeBanner();
    _shownId = reqObj.id;
    var phone = reqObj.phone;
    var title = reqObj.label || reqObj.raw_value || phone;

    var bar = document.createElement("div");
    bar.style.cssText =
      "position:fixed;top:0;left:0;right:0;z-index:100050;" +
      "background:#1f4858;border-bottom:2px solid #3a8aa8;color:#e8f4f8;" +
      "padding:12px 14px;display:flex;align-items:center;gap:12px;" +
      "box-shadow:0 4px 16px rgba(0,0,0,0.5);font-size:15px;";

    var txt = document.createElement("div");
    txt.style.cssText = "flex:1 1 auto;min-width:0;";
    var t1 = document.createElement("div");
    t1.style.cssText = "font-weight:600;";
    t1.textContent = "📞 Volat";
    var t2 = document.createElement("div");
    t2.style.cssText = "font-size:13px;color:#bfe3ef;overflow:hidden;" +
      "text-overflow:ellipsis;white-space:nowrap;";
    t2.textContent = title + "  ·  " + phone;
    txt.appendChild(t1);
    txt.appendChild(t2);
    bar.appendChild(txt);

    // Vytočit: consume (beacon, přežije navigaci) → banner pryč → tel:.
    var doDial = function () {
      _beaconConsume(reqObj.id, "done");
      _removeBanner();
      try { window.location.href = "tel:" + phone; } catch (e) {}
    };
    // Celý text je ťukací (min. tapů — ťukneš kamkoliv na banner → vytočí).
    try { txt.style.cursor = "pointer"; txt.addEventListener("click", doDial); } catch (e) {}

    var callBtn = document.createElement("button");
    callBtn.type = "button";
    callBtn.textContent = "Volat";
    callBtn.style.cssText =
      "background:#2ea043;color:#fff;border:none;padding:12px 22px;" +
      "border-radius:6px;font-weight:700;font-size:16px;white-space:nowrap;cursor:pointer;";
    callBtn.addEventListener("click", doDial);
    bar.appendChild(callBtn);

    var closeBtn = document.createElement("button");
    closeBtn.type = "button";
    closeBtn.textContent = "×";
    closeBtn.style.cssText =
      "background:transparent;border:none;color:#bfe3ef;font-size:26px;" +
      "line-height:1;cursor:pointer;padding:4px 10px;";
    closeBtn.addEventListener("click", function (ev) {
      try { ev.stopPropagation(); } catch (e) {}
      _beaconConsume(reqObj.id, "dismissed");
      _removeBanner();
    });
    bar.appendChild(closeBtn);

    document.body.appendChild(bar);
    _bannerEl = bar;
  }

  function _tick() {
    try {
      fetch("/api/v1/erp/phone-dial-request/pending", { credentials: "same-origin" })
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (j) {
          if (!j || !j.ok) return;
          var reqs = j.requests || [];
          if (!reqs.length) { _removeBanner(); return; }
          var stillPending = _shownId && reqs.some(function (x) { return x.id === _shownId; });
          if (!stillPending) _showBanner(reqs[0]);
        })
        .catch(function () {});
    } catch (e) {}
  }

  setInterval(_tick, POLL_MS);
  setTimeout(_tick, 1500);
})();
