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
      { label: "📲 Mobilní appky (verze + zařízení)…", fn: _appReleaseModal },
    ]);
  }

  // ── Mobilní appky: nahrát novou verzi APK + historie verzí + přehled zařízení.
  // Univerzální přes app_key (Marti 4.6.2026). Self-update: appka stáhne z serveru.
  function _appReleaseModal() {
    var APP = "mobile";  // zatím jedna appka; připraveno na víc (app_key)
    var ov = document.createElement("div");
    ov.style.cssText =
      "position:fixed;inset:0;z-index:100070;background:rgba(0,0,0,0.55);" +
      "display:flex;align-items:flex-start;justify-content:center;padding:20px;overflow:auto;";
    var box = document.createElement("div");
    box.style.cssText =
      "background:#141a20;border:1px solid #2a3340;border-radius:8px;max-width:460px;" +
      "width:100%;margin:auto;padding:18px 20px;color:#e8eef5;box-shadow:0 8px 32px rgba(0,0,0,0.6);";
    box.innerHTML =
      '<div style="font-size:15px;font-weight:600;margin-bottom:6px;">📲 Mobilní appky</div>' +
      '<div style="font-size:12px;color:#8a96a4;margin-bottom:12px;">app_key: <code>' + APP +
      '</code> — appka se sama aktualizuje z našeho serveru.</div>' +
      '<div data-app-latest style="font-size:13px;color:#bcd0e6;margin-bottom:12px;">Načítám verzi…</div>' +
      '<div style="border-top:1px solid #2a3340;padding-top:12px;font-weight:600;font-size:13px;margin-bottom:8px;">Nahrát novou verzi</div>' +
      '<button type="button" data-au-build style="width:100%;background:#1f3a55;border:1px solid #356092;color:#dbeeff;border-radius:6px;padding:11px;font-size:13px;font-weight:700;cursor:pointer;margin-bottom:6px;">⬆ Nahrát z buildu (auto, verze +1)</button>' +
      '<div style="font-size:11px;color:#8a96a4;margin-bottom:10px;">Vezme app-release.apk z buildu na NB a sám zvolí verzi (předchozí +1). Nebo ručně níže:</div>' +
      '<input data-au-file type="file" accept=".apk" style="width:100%;margin-bottom:8px;color:#cfd6df;font-size:12px;">' +
      '<div style="display:flex;gap:8px;margin-bottom:8px;">' +
        '<input data-au-vc type="number" placeholder="versionCode (např. 2)" style="flex:1;background:#0f1620;border:1px solid #2c3a4c;border-radius:6px;padding:8px;color:#e8eef5;font-size:12px;">' +
        '<input data-au-vn type="text" placeholder="versionName (1.1)" style="flex:1;background:#0f1620;border:1px solid #2c3a4c;border-radius:6px;padding:8px;color:#e8eef5;font-size:12px;">' +
      '</div>' +
      '<input data-au-notes type="text" placeholder="Poznámka k verzi (volitelné)" style="width:100%;background:#0f1620;border:1px solid #2c3a4c;border-radius:6px;padding:8px;color:#e8eef5;font-size:12px;margin-bottom:10px;">' +
      '<button type="button" data-au-go style="width:100%;background:#1f3a2e;border:1px solid #3a7a4a;color:#cdeede;border-radius:6px;padding:10px;font-size:13px;font-weight:600;cursor:pointer;">⬆ Nahrát verzi</button>' +
      '<div data-au-msg style="font-size:12px;margin-top:8px;min-height:14px;"></div>' +
      '<div style="border-top:1px solid #2a3340;padding-top:12px;margin-top:12px;font-weight:600;font-size:13px;margin-bottom:6px;">Historie verzí</div>' +
      '<div data-app-versions style="font-size:12px;color:#bcc6d2;">…</div>' +
      '<div style="border-top:1px solid #2a3340;padding-top:12px;margin-top:12px;font-weight:600;font-size:13px;margin-bottom:6px;">Zařízení a verze</div>' +
      '<div data-app-devices style="font-size:12px;color:#bcc6d2;">…</div>' +
      '<button type="button" data-au-close style="display:block;width:100%;margin-top:14px;padding:9px;background:transparent;border:none;color:#8a96a4;cursor:pointer;font-size:13px;">Zavřít</button>';
    ov.appendChild(box);
    ov.addEventListener("click", function (ev) { if (ev.target === ov) ov.remove(); });
    document.body.appendChild(ov);
    box.querySelector("[data-au-close]").addEventListener("click", function () { ov.remove(); });

    function _fmtSize(n) { return n ? (Math.round(n / 1024 / 1024 * 10) / 10) + " MB" : ""; }

    function _loadLatest() {
      fetch("/api/v1/erp/app/" + APP + "/latest", { credentials: "same-origin" })
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (j) {
          var el = box.querySelector("[data-app-latest]");
          if (j && j.available) {
            el.innerHTML = "Aktuální: <strong style='color:#7fd6c2;'>" + (j.version_name || "") +
              "</strong> (code " + j.version_code + ") · " + _esc2(j.released_at || "") +
              " · " + _fmtSize(j.size);
          } else { el.textContent = "Zatím žádná verze nahraná."; }
        }).catch(function () {});
    }
    function _loadVersions() {
      fetch("/api/v1/erp/app/" + APP + "/versions", { credentials: "same-origin" })
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (j) {
          var el = box.querySelector("[data-app-versions]");
          if (!j || !j.versions || !j.versions.length) { el.textContent = "—"; return; }
          el.innerHTML = j.versions.map(function (v) {
            return "<div style='padding:3px 0;border-bottom:1px solid #20262e;'>" +
              "<strong>" + _esc2(v.version_name || "") + "</strong> (code " + v.version_code + ") · " +
              _esc2(v.released_at || "") + (v.notes ? " — " + _esc2(v.notes) : "") + "</div>";
          }).join("");
        }).catch(function () {});
    }
    function _flag(on, name) {
      var c = on ? "#7fd6c2" : "#e08a8a";
      return "<span style='color:" + c + ";'>" + (on ? "✓" : "✗") + " " + name + "</span>";
    }
    function _loadDevices() {
      fetch("/api/v1/erp/app/devices", { credentials: "same-origin" })
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (j) {
          var el = box.querySelector("[data-app-devices]");
          if (!j || !j.devices || !j.devices.length) { el.textContent = "Zatím žádné zařízení."; return; }
          el.innerHTML = j.devices.map(function (d) {
            var flagsLine = [
              _flag(d.service_enabled, "naslouchá"),
              _flag(d.call_log_enabled, "call-log"),
              _flag(d.notif_enabled, "oznámení"),
              _flag(d.fullscreen_enabled, "celá obr.")
            ].join(" · ");
            return "<div style='padding:6px 0;border-bottom:1px solid #20262e;'>" +
              "<button type='button' data-cmd-user='" + (d.user_id || "") + "' " +
              "style='float:right;background:#1f3a55;border:1px solid #356092;color:#dbeeff;" +
              "border-radius:6px;padding:4px 8px;font-size:11px;cursor:pointer;'>📨 Doporučit</button>" +
              "<strong>" + _esc2(d.user_name || "") + "</strong> · " + _esc2(d.app_key || "") +
              " v" + _esc2(d.version_name || "?") + " (code " + (d.version_code || "?") + ")<br>" +
              "<span style='color:#8a96a4;'>" + _esc2(d.device_label || "") +
              (d.android_release ? " · Android " + _esc2(d.android_release) : "") +
              " · " + _esc2(d.last_seen || "") + "</span><br>" +
              "<span style='font-size:11px;'>" + flagsLine + "</span></div>";
          }).join("");
          var btns = el.querySelectorAll("[data-cmd-user]");
          for (var i = 0; i < btns.length; i++) {
            (function (b) {
              b.addEventListener("click", function () {
                _commandPicker(parseInt(b.getAttribute("data-cmd-user"), 10));
              });
            })(btns[i]);
          }
        }).catch(function () {});
    }

    function _commandPicker(userId) {
      if (!userId) return;
      _menuDialog("Poslat doporučení uživateli", [
        { label: "📲 Povolit zobrazení přes celou obrazovku", fn: function () { _sendCommand(userId, "fullscreen"); } },
        { label: "📞 Povolit seznam hovorů (délka hovoru)", fn: function () { _sendCommand(userId, "calllog"); } },
        { label: "🔔 Povolit oznámení", fn: function () { _sendCommand(userId, "notif"); } },
        { label: "🔋 Vypnout úsporu baterie", fn: function () { _sendCommand(userId, "battery"); } },
        { label: "⬆ Aktualizovat appku", fn: function () { _sendCommand(userId, "update"); } },
      ]);
    }
    function _sendCommand(userId, type) {
      fetch("/api/v1/erp/app/command", {
        method: "POST", credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target_user_id: userId, command_type: type }),
      }).then(function (r) { return r.json(); }).then(function (j) {
        _toast(j && j.ok
          ? "✓ Odesláno — uživateli na mobilu vyskočí dialog Povolit/Zamítnout"
          : ((j && j.error) || "Nepodařilo se odeslat"), !(j && j.ok));
      }).catch(function () { _toast("Síťová chyba", true); });
    }

    box.querySelector("[data-au-go]").addEventListener("click", function () {
      var f = box.querySelector("[data-au-file]").files[0];
      var vc = box.querySelector("[data-au-vc]").value;
      var vn = box.querySelector("[data-au-vn]").value;
      var notes = box.querySelector("[data-au-notes]").value;
      var msg = box.querySelector("[data-au-msg]");
      if (!f) { msg.style.color = "#e89b9b"; msg.textContent = "Vyber soubor .apk"; return; }
      if (!vc) { msg.style.color = "#e89b9b"; msg.textContent = "Zadej versionCode"; return; }
      var fd = new FormData();
      fd.append("file", f);
      fd.append("version_code", vc);
      fd.append("version_name", vn || "");
      fd.append("notes", notes || "");
      msg.style.color = "#bcd0e6"; msg.textContent = "Nahrávám…";
      var go = box.querySelector("[data-au-go]"); go.disabled = true;
      fetch("/api/v1/erp/app/" + APP + "/upload", {
        method: "POST", credentials: "same-origin", body: fd,
      }).then(function (r) { return r.json(); }).then(function (j) {
        go.disabled = false;
        if (j && j.ok) {
          msg.style.color = "#7fd6c2";
          msg.textContent = "✓ Nahráno v" + (j.version_name || "") + " (code " + j.version_code + "). Telefony se aktualizují do ~5 min.";
          _loadLatest(); _loadVersions();
        } else {
          msg.style.color = "#e89b9b";
          msg.textContent = (j && j.error) || "Nahrání selhalo.";
        }
      }).catch(function () { go.disabled = false; msg.style.color = "#e89b9b"; msg.textContent = "Síťová chyba."; });
    });

    box.querySelector("[data-au-build]").addEventListener("click", function () {
      var msg = box.querySelector("[data-au-msg]");
      var bb = box.querySelector("[data-au-build]"); bb.disabled = true;
      msg.style.color = "#bcd0e6"; msg.textContent = "Posílám příkaz na NB (build)…";
      fetch("/api/v1/erp/ops/request", {
        method: "POST", credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action_key: "publish_app_mobile" }),
      }).then(function (r) { return r.json(); }).then(function (j) {
        bb.disabled = false;
        if (j && (j.ok || j.id || j.status)) {
          msg.style.color = "#7fd6c2";
          msg.textContent = "✓ Příkaz odeslán — APK se nahraje za pár sekund (verze +1). Pak se objeví v historii.";
          setTimeout(function () { _loadLatest(); _loadVersions(); }, 12000);
        } else {
          msg.style.color = "#e89b9b";
          msg.textContent = (j && j.error) || "Nepodařilo se odeslat příkaz.";
        }
      }).catch(function () {
        bb.disabled = false; msg.style.color = "#e89b9b"; msg.textContent = "Síťová chyba.";
      });
    });

    _loadLatest(); _loadVersions(); _loadDevices();
  }

  function _esc2(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
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
