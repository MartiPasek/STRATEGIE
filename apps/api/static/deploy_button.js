/* eslint-disable */
/**
 * deploy_button.js — "Nasadit na povel" tlačítko (Marti 1.6.2026).
 * ─────────────────────────────────────────────────────────────────────────────
 * Floating 🚀 v pravém horním rohu (Kristý 2.6.2026 — přesun z levého dolního).
 * Zobrazí se JEN rodičům (preview vrátí 403 ostatním).
 * Klik → náhled (git fetch + diff) → confirm → POST /deploy/now → git pull +
 * restart API přes Phase 42 RESTART-WATCHER. Jednoklik = schválení.
 * Sdílené chatem (index.html) i ERP. Self-contained.
 *
 * Animace (Kristý 2.6.2026): pokud existuje nová verze k nasazení
 * (deploy/preview → deployable:true), raketa "ožije" — jemný bob + pulzující
 * záře (jako raketa připravená ke startu). Když není co nasadit, je v klidu.
 * Stav se zjišťuje pravidelným pollem (git fetch + porovnání origin/main).
 * Respektuje prefers-reduced-motion (vypne pohyb, nechá statický prstenec).
 */
(function () {
  "use strict";

  var PREVIEW = "/api/v1/erp/deploy/preview";
  var NOW = "/api/v1/erp/deploy/now";

  // Jak často kontrolovat, jestli je nová verze (git fetch na serveru — držíme
  // šetrně, pár rodičů × 1 fetch / 2 min je zanedbatelné). Tune dle potřeby.
  var POLL_MS = 120000;

  // Pravý horní roh. V chatu úplně do rohu. V ERP taky nahoru, NAD Module Health
  // banner — ten je proto v erp_module_kit.js posunutý na top:56px (Kristý 3.6.).
  var IS_ERP = /^\/erp(\/|$)/.test(location.pathname || "");
  var CORNER = IS_ERP ? "top:8px;right:16px;" : "top:12px;right:12px;";

  // Parent-check: preview (bez fetch) vrátí 200 jen rodičům → jinak tlačítko
  // nezobrazíme. Z téže odpovědi rovnou nastavíme úvodní stav (lokální
  // porovnání, levné), čerstvý git fetch doženou periodické polly.
  try {
    fetch(PREVIEW, { credentials: "same-origin" })
      .then(function (r) { return r.ok ? r.json() : Promise.reject(); })
      .then(function (j) {
        _injectStyle();
        _renderButton();
        _setActive(!!(j && j.deployable), j || {});
        setTimeout(function () { _poll(true); }, 4000); // první čerstvá kontrola
        setInterval(function () { _poll(true); }, POLL_MS);
      })
      .catch(function () {});
  } catch (e) {}

  // Pravidelný poll stavu nasaditelnosti. fresh=true → git fetch (čerstvý
  // origin); fresh=false → jen lokální porovnání.
  function _poll(fresh) {
    fetch(PREVIEW + (fresh ? "?fetch=1" : ""), { credentials: "same-origin" })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (j) { if (j) _setActive(!!j.deployable, j); })
      .catch(function () {});
  }

  function _injectStyle() {
    if (document.getElementById("erpDeployStyle")) return;
    var s = document.createElement("style");
    s.id = "erpDeployStyle";
    s.textContent =
      "#erpDeployBtn{box-shadow:0 2px 8px rgba(0,0,0,0.4);" +
      "transition:background .3s ease,border-color .3s ease,color .3s ease,opacity .2s ease;}" +
      // Aktivní raketa: jemný "bob" (nadnáší se a lehce naklání) + pulzující záře.
      "#erpDeployBtn.erp-deploy-active{" +
      "animation:erpRocketBob 1.7s ease-in-out infinite,erpRocketGlow 1.9s ease-out infinite;}" +
      "@keyframes erpRocketBob{" +
      "0%,100%{transform:translateY(0) rotate(0deg);}" +
      "30%{transform:translateY(-3px) rotate(-7deg);}" +
      "60%{transform:translateY(-2px) rotate(7deg);}}" +
      "@keyframes erpRocketGlow{" +
      "0%{box-shadow:0 2px 8px rgba(0,0,0,0.4),0 0 0 0 rgba(124,210,150,0.55);}" +
      "70%{box-shadow:0 2px 10px rgba(0,0,0,0.4),0 0 0 9px rgba(124,210,150,0);}" +
      "100%{box-shadow:0 2px 8px rgba(0,0,0,0.4),0 0 0 0 rgba(124,210,150,0);}}" +
      // Ohleduplnost: kdo má omezený pohyb, dostane jen klidný statický prstenec.
      "@media (prefers-reduced-motion: reduce){" +
      "#erpDeployBtn.erp-deploy-active{animation:none;" +
      "box-shadow:0 2px 8px rgba(0,0,0,0.4),0 0 0 3px rgba(124,210,150,0.45);}}";
    document.head.appendChild(s);
  }

  function _renderButton() {
    if (document.getElementById("erpDeployBtn")) return;
    var b = document.createElement("button");
    b.id = "erpDeployBtn";
    b.type = "button";
    b.textContent = "🚀";
    b.title = "Nasadit nejnovější verzi (git pull + restart API)";
    b.style.cssText =
      "position:fixed;" + CORNER + "z-index:99000;width:40px;height:40px;" +
      "border-radius:50%;background:#243a44;border:1px solid #356e6e;color:#a8d4dc;" +
      "font-size:18px;cursor:pointer;opacity:0.65;";
    b.addEventListener("mouseenter", function () { b.style.opacity = "1"; });
    b.addEventListener("mouseleave", function () {
      // Aktivní raketa zůstává výrazná i bez hoveru.
      b.style.opacity = b.classList.contains("erp-deploy-active") ? "1" : "0.65";
    });
    b.addEventListener("click", _menu);
    document.body.appendChild(b);
  }

  // Zapne/vypne "živý" stav rakety podle toho, jestli je co nasadit.
  function _setActive(active, info) {
    var b = document.getElementById("erpDeployBtn");
    if (!b) return;
    if (active) {
      b.classList.add("erp-deploy-active");
      b.style.background = "#1f3a2e";
      b.style.borderColor = "#46a05e";
      b.style.color = "#cdeede";
      b.style.opacity = "1";
      var extra = "";
      if (info && info.files_changed != null) extra += " — " + info.files_changed + " souborů";
      if (info && info.commit_message) extra += " · „" + info.commit_message + "“";
      b.title = "🚀 Nová verze k nasazení" + extra + " (klik = nasadit)";
    } else {
      b.classList.remove("erp-deploy-active");
      b.style.background = "#243a44";
      b.style.borderColor = "#356e6e";
      b.style.color = "#a8d4dc";
      b.style.opacity = "0.65";
      b.title = "Nasadit nejnovější verzi (git pull + restart API)";
    }
  }

  // Ops menu (Marti 1.6.2026): Nasadit / Restartovat API + Ops akce (3.6.).
  function _menu() {
    _menuDialog("Operace serveru", [
      { label: "🚀 Nasadit nejnovější verzi", primary: true, fn: _startDeploy },
      { label: "⚙ Ops akce (restart služeb)…", fn: _opsMenu },
      { label: "📜 Audit ops akcí", fn: _opsLog },
    ]);
  }

  // Ops framework (Marti 3.6.2026): pojmenované whitelistované akce z UI.
  // Eliminace ručního PowerShellu — vše přes confirm + audit do DB.
  var OPS_ACTIONS = "/api/v1/erp/ops/actions";
  var OPS_REQUEST = "/api/v1/erp/ops/request";
  var OPS_LOG = "/api/v1/erp/ops/log";

  function _opsMenu() {
    fetch(OPS_ACTIONS, { credentials: "same-origin" })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (j) {
        if (!j || !j.actions || !j.actions.length) { _toast("Žádné ops akce", true); return; }
        var items = j.actions.map(function (a) {
          return { label: "⚙ " + a.label, fn: function () { _opsConfirm(a); } };
        });
        _menuDialog("Ops akce", items);
      })
      .catch(function () { _toast("Ops akce: síť", true); });
  }

  function _opsConfirm(a) {
    _dialog(
      a.label + "?",
      "Spustí pojmenovanou ops akci na cíli „" + a.target + "“. " +
      "Akce se zapíše do auditu (kdo / kdy / výsledek).",
      function () { _opsDo(a); }
    );
  }

  function _opsDo(a) {
    _toast("Spouštím: " + a.label + "…");
    fetch(OPS_REQUEST, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
      body: JSON.stringify({ action_key: a.action_key }),
    })
      .then(function (r) { return r.json(); })
      .then(function (j) {
        if (j && j.ok) {
          _toast(j.remote
            ? ("✓ Zařazeno — " + (j.message || "agent provede do ~30 s") + " (audit #" + j.request_id + ")")
            : ("✓ Hotovo: " + (j.result || j.status || "ok") + " (audit #" + j.request_id + ")"), false);
        } else {
          _toast("Ops: " + ((j && j.error) || "selhalo"), true);
        }
      })
      .catch(function () { _toast("Ops selhalo (síť)", true); });
  }

  function _opsLog() {
    fetch(OPS_LOG, { credentials: "same-origin" })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (j) {
        if (!j || !j.log) { _toast("Audit: nedostupné", true); return; }
        var lines = j.log.length
          ? j.log.map(function (r) {
              var st = r.status === "done" ? "✓" : r.status === "error" ? "✕"
                     : r.status === "pending" ? "⏳" : r.status === "ack" ? "▶" : "·";
              var when = (r.created_at || "").replace("T", " ").slice(0, 16);
              return st + " #" + r.id + " " + r.action_key + " · " + (r.requested_by_name || "?") +
                     " · " + when + (r.result ? " · " + String(r.result).slice(0, 60) : "");
            }).join("\n")
          : "(zatím žádné ops akce)";
        _dialog("Audit ops akcí (posledních 30)", lines, null);
      })
      .catch(function () { _toast("Audit: síť", true); });
  }

  function _confirmRestart() {
    _dialog(
      "Restartovat API?",
      "Restartuje STRATEGIE-API na serveru (~5 s). Použij když něco drhne — " +
      "např. zaseklé spojení na EUROSOFT MCP po restartu serveru. " +
      "Nenasazuje nový kód.",
      _doRestart
    );
  }

  function _doRestart() {
    _toast("Restartuji API…");
    fetch("/api/v1/erp/restart-api", { method: "POST", credentials: "same-origin" })
      .then(function (r) { return r.json(); })
      .then(function (j) {
        if (j && j.ok) _toast("✓ Restart spuštěn — API naběhne za ~5 s.", false);
        else _toast("Restart: " + ((j && j.error) || "selhalo"), true);
      })
      .catch(function () { _toast("Restart selhal (síť)", true); });
  }

  function _startDeploy() {
    var b = document.getElementById("erpDeployBtn");
    if (b) { _setActive(false); b.disabled = true; b.textContent = "…"; }
    fetch(PREVIEW + "?fetch=1", { credentials: "same-origin" })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (j) {
        if (b) { b.disabled = false; b.textContent = "🚀"; }
        if (j) _setActive(!!j.deployable, j);
        if (!j) { _toast("Náhled selhal", true); return; }
        if (!j.deployable) {
          var why = j.reason === "already_up_to_date"
              ? "Server už běží na nejnovější verzi (origin/main)."
            : j.reason === "dirty_working_tree"
              ? "Na serveru jsou necommitnuté změny — nasazení blokováno (ruční zásah)."
            : "Nelze nasadit: " + (j.reason || "?");
          _dialog("Deploy", why, null);
          return;
        }
        // Koordinace 23/24 (Marti 3.6.): varuj, pokud je aktivní i druhá instance
        var actWarn = "";
        try {
          var act = (j.active_instances || []);
          if (act.length) {
            actWarn = "\n\n⚠ Aktivní i: " + act.map(function (o) {
              return "Claude-" + o.instance_id + " (" + (o.instance_name || "?") + ")";
            }).join(", ") + " — deploy je serializovaný (advisory lock).";
          }
        } catch (e) {}
        _dialog(
          "Nasadit nejnovější verzi?",
          j.files_changed + " souborů změněno · cíl " + j.target +
          "\n„" + (j.commit_message || "") + "\"\n\n" +
          "Spustí git pull + restart API na serveru." + actWarn,
          _doDeploy
        );
      })
      .catch(function () {
        if (b) { b.disabled = false; b.textContent = "🚀"; }
        _toast("Náhled selhal (síť)", true);
      });
  }

  function _doDeploy() {
    _toast("Nasazuji… git pull + restart");
    fetch(NOW, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
      body: JSON.stringify({ description: "Deploy z UI tlačítka" }),
    })
      .then(function (r) { return r.json(); })
      .then(function (j) {
        if (j && (j.ok || j.status === "deployed")) {
          _toast("✓ Nasazeno — API se restartuje (~5 s). Pak vyskočí nabídka Obnovit.", false);
        } else {
          _toast("Deploy: " + ((j && (j.error || j.reason)) || "selhalo"), true);
        }
        setTimeout(function () { _poll(true); }, 3000); // přehodnoť stav rakety
      })
      .catch(function () { _toast("Deploy selhal (síť)", true); });
  }

  // ── self-contained dialog + toast ──
  function _menuDialog(title, actions) {
    var ov = document.createElement("div");
    ov.style.cssText =
      "position:fixed;inset:0;z-index:100070;background:rgba(0,0,0,0.55);" +
      "display:flex;align-items:center;justify-content:center;padding:20px;";
    var box = document.createElement("div");
    box.style.cssText =
      "background:#141a20;border:1px solid #2a3340;border-radius:8px;max-width:360px;" +
      "width:100%;padding:18px 20px;color:#e8eef5;box-shadow:0 8px 32px rgba(0,0,0,0.6);";
    var h = document.createElement("div");
    h.style.cssText = "font-size:15px;font-weight:600;margin-bottom:14px;";
    h.textContent = title;
    box.appendChild(h);
    function _close() { try { ov.remove(); } catch (e) {} }
    actions.forEach(function (a) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = a.label;
      btn.style.cssText =
        "display:block;width:100%;text-align:left;margin-bottom:8px;padding:11px 14px;" +
        "border-radius:6px;cursor:pointer;font-size:14px;border:1px solid " +
        (a.primary ? "#3a7a4a" : "#2a3340") + ";background:" +
        (a.primary ? "#1f3a2e" : "#1f2530") + ";color:" +
        (a.primary ? "#cdeede" : "#cfd6df") + ";";
      btn.addEventListener("click", function () { _close(); a.fn(); });
      box.appendChild(btn);
    });
    var cancel = document.createElement("button");
    cancel.type = "button";
    cancel.textContent = "Zrušit";
    cancel.style.cssText =
      "display:block;width:100%;margin-top:4px;padding:9px 14px;background:transparent;" +
      "border:none;color:#8a96a4;cursor:pointer;font-size:13px;";
    cancel.addEventListener("click", _close);
    box.appendChild(cancel);
    ov.appendChild(box);
    ov.addEventListener("click", function (ev) { if (ev.target === ov) _close(); });
    document.body.appendChild(ov);
  }

  function _dialog(title, msg, onOk) {
    var ov = document.createElement("div");
    ov.style.cssText =
      "position:fixed;inset:0;z-index:100070;background:rgba(0,0,0,0.55);" +
      "display:flex;align-items:center;justify-content:center;padding:20px;";
    var box = document.createElement("div");
    box.style.cssText =
      "background:#141a20;border:1px solid #2a3340;border-radius:8px;max-width:420px;" +
      "width:100%;padding:18px 20px;color:#e8eef5;box-shadow:0 8px 32px rgba(0,0,0,0.6);";
    var h = document.createElement("div");
    h.style.cssText = "font-size:15px;font-weight:600;margin-bottom:10px;";
    h.textContent = title;
    var p = document.createElement("div");
    p.style.cssText = "font-size:13px;color:#bcc6d2;white-space:pre-wrap;line-height:1.5;margin-bottom:16px;";
    p.textContent = msg;
    var row = document.createElement("div");
    row.style.cssText = "display:flex;justify-content:flex-end;gap:8px;";
    function _close() { try { ov.remove(); } catch (e) {} }
    if (onOk) {
      // Marti 3.6.2026: primární "🚀 Nasadit" PRVNÍ (vlevo), "Zrušit" druhé.
      var ok = document.createElement("button");
      ok.type = "button"; ok.textContent = "🚀 Nasadit";
      ok.style.cssText = "padding:8px 16px;background:#3a7a3a;border:none;border-radius:4px;color:#fff;font-weight:600;cursor:pointer;font-size:13px;";
      ok.addEventListener("click", function () { _close(); onOk(); });
      row.appendChild(ok);
      var cancel = document.createElement("button");
      cancel.type = "button"; cancel.textContent = "Zrušit";
      cancel.style.cssText = "padding:8px 16px;background:#2a3340;border:none;border-radius:4px;color:#cfd6df;cursor:pointer;font-size:13px;";
      cancel.addEventListener("click", _close);
      row.appendChild(cancel);
    } else {
      var okOnly = document.createElement("button");
      okOnly.type = "button"; okOnly.textContent = "OK";
      okOnly.style.cssText = "padding:8px 16px;background:#2a3340;border:none;border-radius:4px;color:#cfd6df;cursor:pointer;font-size:13px;";
      okOnly.addEventListener("click", _close);
      row.appendChild(okOnly);
    }
    box.appendChild(h); box.appendChild(p); box.appendChild(row);
    ov.appendChild(box);
    ov.addEventListener("click", function (ev) { if (ev.target === ov) _close(); });
    document.body.appendChild(ov);
  }

  function _toast(msg, isErr) {
    var t = document.createElement("div");
    t.textContent = msg;
    t.style.cssText =
      "position:fixed;left:50%;bottom:60px;transform:translateX(-50%);z-index:100071;" +
      "background:" + (isErr ? "#5a2a2a" : "#1f3a2e") + ";" +
      "border:1px solid " + (isErr ? "#7a4a4a" : "#2f5a44") + ";color:#e8f4d8;" +
      "padding:10px 18px;border-radius:6px;font-size:13px;max-width:90vw;text-align:center;" +
      "box-shadow:0 4px 16px rgba(0,0,0,0.5);";
    document.body.appendChild(t);
    setTimeout(function () { try { t.remove(); } catch (e) {} }, isErr ? 5000 : 6000);
  }
})();
