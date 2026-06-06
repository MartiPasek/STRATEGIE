/* Impersonace v ERP (6.6.2026, Marti) — parent „Přihlásit jako" + červený
   nepřekrývající indikátor + návrat. Sdílí backend s chatem
   (/api/v1/auth/impersonate, /me, /impersonate/stop). Self-contained. */
(function () {
  "use strict";

  var FAB_ID = "erpImpFab";
  var BANNER_ID = "erpImpBanner";

  function api(method, url, body) {
    return fetch(url, {
      method: method,
      headers: body ? { "Content-Type": "application/json" } : {},
      credentials: "include",
      body: body ? JSON.stringify(body) : undefined,
    }).then(function (r) {
      return r.json().catch(function () { return {}; }).then(function (d) {
        return { ok: r.ok, status: r.status, data: d };
      });
    });
  }

  function ensureStyle() {
    if (document.getElementById("erpImpStyle")) return;
    var s = document.createElement("style");
    s.id = "erpImpStyle";
    s.textContent =
      "#" + BANNER_ID + "{position:fixed;right:14px;bottom:54px;z-index:99998;"
      + "display:flex;align-items:center;gap:8px;background:rgba(255,90,90,.16);"
      + "border:1px solid rgba(255,90,90,.6);color:#ff8a8a;border-radius:14px;"
      + "padding:5px 10px;font-size:12px;font-weight:600;"
      + "box-shadow:0 2px 10px rgba(0,0,0,.35);animation:erpImpBlink 1.2s ease-in-out infinite}"
      + "@keyframes erpImpBlink{0%,100%{opacity:1}50%{opacity:.55}}"
      + "#" + BANNER_ID + " button{background:#ff5a5a;color:#fff;border:none;border-radius:9px;"
      + "padding:2px 9px;font-weight:600;cursor:pointer;font-size:12px}"
      + "#" + FAB_ID + "{position:fixed;right:14px;bottom:14px;z-index:99997;"
      + "background:#2a2d34;color:#cfd6df;border:1px solid #444;border-radius:14px;"
      + "padding:5px 11px;font-size:12px;cursor:pointer;opacity:.75}"
      + "#" + FAB_ID + ":hover{opacity:1}";
    document.head.appendChild(s);
  }

  function clearUi() {
    var b = document.getElementById(BANNER_ID); if (b) b.remove();
    var f = document.getElementById(FAB_ID); if (f) f.remove();
  }

  function showBanner(who) {
    clearUi();
    var bar = document.createElement("div");
    bar.id = BANNER_ID;
    var lbl = document.createElement("span");
    lbl.textContent = "🎭 jako " + (who || "uživatel");
    var btn = document.createElement("button");
    btn.textContent = "Zpět";
    btn.addEventListener("click", function () {
      api("POST", "/api/v1/auth/impersonate/stop").then(reloadSoon);
    });
    bar.appendChild(lbl); bar.appendChild(btn);
    document.body.appendChild(bar);
  }

  function showFab() {
    clearUi();
    var f = document.createElement("div");
    f.id = FAB_ID;
    f.textContent = "🎭 Přihlásit jako…";
    f.addEventListener("click", startImpersonation);
    document.body.appendChild(f);
  }

  function reloadSoon() { setTimeout(function () { location.reload(); }, 200); }

  function startImpersonation() {
    var who = prompt("Přihlásit jako — zadej id, login nebo e-mail usera:");
    if (!who || !who.trim()) return;
    api("POST", "/api/v1/auth/impersonate", { user: who.trim() }).then(function (r) {
      if (!r.ok) {
        alert((typeof r.data.detail === "string") ? r.data.detail : "Impersonace selhala.");
        return;
      }
      reloadSoon();
    });
  }

  function init() {
    ensureStyle();
    api("GET", "/api/v1/auth/me").then(function (r) {
      if (!r.ok) return;
      var u = r.data || {};
      if (u.impersonation_active) {
        showBanner(u.display_name || u.first_name || ("user " + u.user_id));
      } else if (u.is_marti_parent) {
        showFab();
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else { init(); }
})();
