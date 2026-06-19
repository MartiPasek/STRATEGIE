/* eslint-disable */
/**
 * app_version_watch.js — "Nová verze" přes JEMNOU ANIMACI LOGA (Marti 2.6.2026, Volba D).
 * ─────────────────────────────────────────────────────────────────────────────
 * Produkce: po každém nasazení mají lidi s otevřenou appkou starou verzi.
 * Watcher polluje /api/v1/erp/app-version (git HEAD sha). Když se verze změní
 * oproti té při načtení → logo STRATEGIE v hlavičce začne JEMNĚ zářit/pulzovat.
 *
 * Marti's požadavky:
 *  - musí být jasné, že je nová verze (animace = vždy si všimne)
 *  - žádný auto-reload (A/B nebezpečné — ztráta rozdělané práce)
 *  - nesmí jít odkliknout křížkem a zapomenout (animace drží do reloadu)
 *  - D: nenásilná animace loga → klik → milý popup od Marti-AI + potvrzení reloadu
 *
 * Logo: chat = #brandLogo (jinak klik → audit modal), ERP = #erpLogoLink (odkaz).
 * Klik na zářící logo zachytíme v capture fázi → otevřeme popup (ne audit/navigaci).
 * Když verze NENÍ nová → logo se chová normálně.
 *
 * Sdílené — loadováno chatem (index.html) i ERP. Self-contained, bez závislostí.
 */
(function () {
  "use strict";

  var EP = "/api/v1/erp/app-version";
  var POLL_MS = 20000;  // 20 s — animace naskočí brzy po deployi
  var LOGO_IDS = ["brandLogo", "erpLogoLink"];
  var GLOW_CLASS = "stg-version-glow";
  var _loaded = null;
  var _pending = false;     // je k dispozici nová verze?
  var _wired = false;       // capture click listener nainstalován?
  var _popupOpen = false;

  function _fetchVer(cb) {
    try {
      fetch(EP, { cache: "no-store", credentials: "same-origin" })
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (j) { cb(j && j.version ? j.version : null); })
        .catch(function () { cb(null); });
    } catch (e) { cb(null); }
  }

  function _injectStyle() {
    if (document.getElementById("stg-version-style")) return;
    var st = document.createElement("style");
    st.id = "stg-version-style";
    st.textContent =
      "@keyframes stgVerGlow{" +
      "0%,100%{text-shadow:0 0 0 rgba(232,185,35,0);transform:scale(1);}" +
      "50%{text-shadow:0 0 10px rgba(232,185,35,.9),0 0 20px rgba(232,185,35,.5);transform:scale(1.045);}" +
      "}" +
      "." + GLOW_CLASS + "{" +
      "animation:stgVerGlow 2.2s ease-in-out infinite !important;" +
      "cursor:pointer !important;transform-origin:left center;" +
      "}" +
      "@keyframes stgPopIn{from{opacity:0;transform:translateY(14px) scale(.97);}to{opacity:1;transform:none;}}";
    document.head.appendChild(st);
  }

  function _eachLogo(fn) {
    for (var i = 0; i < LOGO_IDS.length; i++) {
      var el = document.getElementById(LOGO_IDS[i]);
      if (el) fn(el);
    }
  }

  function _applyGlow() {
    _eachLogo(function (el) {
      if (!el.classList.contains(GLOW_CLASS)) el.classList.add(GLOW_CLASS);
      if (!el.getAttribute("data-stg-orig-title")) {
        var t = el.getAttribute("title") || el.getAttribute("data-hint") || "";
        el.setAttribute("data-stg-orig-title", t);
      }
      el.setAttribute("title", "Nová verze STRATEGIE — klikni 🕯️");
    });
  }

  function _martiAvatarHtml() {
    // Marti 3.6.2026: avatar Marti-AI v chatu (#chatMartiAiAvatar) i ERP
    // (#erpMartiAiAvatar). Driv jen ERP -> chat spadl na svicku.
    var av = document.getElementById("chatMartiAiAvatar")
          || document.getElementById("erpMartiAiAvatar");
    var src = av && av.getAttribute("src");
    if (src) {
      return '<img src="' + src + '" alt="Marti-AI" ' +
        'style="width:54px;height:54px;border-radius:50%;object-fit:cover;' +
        'border:2px solid #e8b923;box-shadow:0 0 0 3px rgba(232,185,35,.18);">';
    }
    return '<div style="width:54px;height:54px;border-radius:50%;' +
      'display:flex;align-items:center;justify-content:center;font-size:30px;' +
      'background:rgba(232,185,35,.14);border:2px solid #e8b923;">🕯️</div>';
  }

  function _showPopup() {
    if (_popupOpen) return;
    _popupOpen = true;

    var ov = document.createElement("div");
    ov.id = "stgVerOverlay";
    ov.style.cssText =
      "position:fixed;inset:0;z-index:100070;background:rgba(8,12,18,.62);" +
      "display:flex;align-items:center;justify-content:center;padding:18px;" +
      "backdrop-filter:blur(2px);";

    var card = document.createElement("div");
    card.style.cssText =
      "max-width:420px;width:100%;background:#1c2530;color:#e8eef5;" +
      "border:1px solid #3a4a5e;border-top:3px solid #e8b923;border-radius:14px;" +
      "padding:22px 22px 18px;box-shadow:0 18px 50px rgba(0,0,0,.55);" +
      "animation:stgPopIn .22s ease-out;font-size:15px;line-height:1.5;";

    var head = document.createElement("div");
    head.style.cssText = "display:flex;align-items:center;gap:14px;margin-bottom:14px;";
    head.innerHTML = _martiAvatarHtml() +
      '<div><div style="font-weight:700;font-size:16px;color:#f0d98a;">Marti-AI</div>' +
      '<div style="font-size:12px;color:#9fb0c4;">nová verze STRATEGIE</div></div>';
    card.appendChild(head);

    var msg = document.createElement("div");
    msg.style.cssText = "margin-bottom:18px;color:#dbe6f2;";
    msg.innerHTML =
      "Ahoj 🕯️ Mám pro tebe <strong>čerstvou verzi STRATEGIE</strong> — pár vylepšení " +
      "už čeká připravených. Až se ti to hodí, kliknutím ji načteme a poběžíš na " +
      "nejnovějším. <span style=\"color:#9fb0c4;\">Žádný spěch — rozdělanou práci si " +
      "klidně dodělej, logo bude svítit, dokud neobnovíš.</span>";
    card.appendChild(msg);

    var row = document.createElement("div");
    row.style.cssText = "display:flex;gap:10px;justify-content:flex-end;flex-wrap:wrap;";

    // Marti 3.6.2026: primární "Obnovit teď" PRVNÍ (vlevo), "Za chvíli" druhé.
    var go = document.createElement("button");
    go.type = "button";
    go.textContent = "Obnovit teď";
    go.style.cssText =
      "background:#e8b923;color:#1c2530;border:none;padding:10px 20px;" +
      "border-radius:8px;font-size:15px;font-weight:700;cursor:pointer;";
    go.addEventListener("click", function () {
      // Marti 7.6.: HARD reload — smaž SW cache + refresh SW, ať nikdo nemusí
      // ručně Ctrl+Shift+R. Fallback obyčejný reload (max 2,5 s čekání).
      var done = false;
      var fin = function () {
        if (done) return; done = true;
        try { location.reload(); } catch (e) { location.href = location.href; }
      };
      try {
        var ps = [];
        if (window.caches && caches.keys) {
          ps.push(caches.keys().then(function (ks) {
            return Promise.all(ks.map(function (k) { return caches.delete(k); }));
          }));
        }
        if (navigator.serviceWorker && navigator.serviceWorker.getRegistrations) {
          ps.push(navigator.serviceWorker.getRegistrations().then(function (rs) {
            return Promise.all(rs.map(function (r) { return r.update(); }));
          }));
        }
        Promise.all(ps).then(fin, fin);
        setTimeout(fin, 2500);
      } catch (e) { fin(); }
    });
    row.appendChild(go);

    var later = document.createElement("button");
    later.type = "button";
    later.textContent = "Za chvíli";
    later.style.cssText =
      "background:transparent;color:#bcd0e6;border:1px solid #44566c;" +
      "padding:10px 16px;border-radius:8px;font-size:14px;cursor:pointer;";
    later.addEventListener("click", _closePopup);
    row.appendChild(later);

    card.appendChild(row);
    ov.appendChild(card);
    ov.addEventListener("click", function (e) { if (e.target === ov) _closePopup(); });
    document.body.appendChild(ov);

    document.addEventListener("keydown", _escClose, true);
    try { go.focus(); } catch (e) {}
  }

  function _escClose(e) { if (e.key === "Escape") _closePopup(); }

  function _closePopup() {
    _popupOpen = false;
    var ov = document.getElementById("stgVerOverlay");
    if (ov) { try { ov.remove(); } catch (e) {} }
    document.removeEventListener("keydown", _escClose, true);
    // logo dál svítí — animace drží, dokud uživatel neobnoví
  }

  function _wireLogoClick() {
    if (_wired) return;
    _wired = true;
    // capture fáze → poběží PŘED audit-modal handlerem (#brandLogo) i navigací (#erpLogoLink)
    document.addEventListener("click", function (e) {
      if (!_pending) return;
      var el = e.target && e.target.closest ?
        e.target.closest("#" + LOGO_IDS[0] + ",#" + LOGO_IDS[1]) : null;
      if (!el) return;
      e.preventDefault();
      e.stopPropagation();
      _showPopup();
    }, true);
  }

  function _activate() {
    if (_pending) { _applyGlow(); return; }  // re-apply (ERP přerenderuje brand row)
    _pending = true;
    _injectStyle();
    _wireLogoClick();
    _applyGlow();
  }

  function _tick() {
    _fetchVer(function (v) {
      if (!v || v === "unknown") return;
      if (_loaded === null) { _loaded = v; return; }  // baseline při prvním načtení
      if (v !== _loaded) _activate();
      else if (_pending) _applyGlow();  // udrž glow i kdyby se logo přerenderovalo
    });
  }

  setTimeout(_tick, 3000);
  setInterval(_tick, POLL_MS);
  document.addEventListener("visibilitychange", function () {
    if (!document.hidden) _tick();
  });
  window.addEventListener("focus", _tick);  // návrat na okno → okamžitá kontrola

  // ── Handoff mobil → PC (Marti 19.6.2026): ťuk na doklad v mobilu → detail tady ──
  // Tento soubor běží v chatu/ERP na POČÍTAČI (mobilní appka ho nenačítá), takže
  // je to ten správný „PC přijímač". Pollujeme frontu a otevřeme interní URL v nové
  // záložce. Server označí požadavek za vyřízený, takže se otevře právě jednou.
  var OPC_EP = "/api/v1/erp/app/open-on-pc/poll";
  var OPC_MS = 5000;
  function _opcTick() {
    try {
      fetch(OPC_EP, { cache: "no-store", credentials: "same-origin" })
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (j) {
          if (j && j.ok && j.url && /^\/[^/]/.test(j.url)) {
            var w = null;
            try { w = window.open(j.url, "stgDoklad"); } catch (e) {}
            if (!w) { try { window.open(j.url, "_blank"); } catch (e) {} }
          }
        }).catch(function () {});
    } catch (e) {}
  }
  setTimeout(_opcTick, 4000);
  setInterval(_opcTick, OPC_MS);
  window.addEventListener("focus", _opcTick);
})();
