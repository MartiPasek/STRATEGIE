/* eslint-disable */
/**
 * deploy_button.js — "Nasadit na povel" tlačítko (Marti 1.6.2026).
 * ─────────────────────────────────────────────────────────────────────────────
 * Floating 🚀 vlevo dole. Zobrazí se JEN rodičům (preview vrátí 403 ostatním).
 * Klik → náhled (git fetch + diff) → confirm → POST /deploy/now → git pull +
 * restart API přes Phase 42 RESTART-WATCHER. Jednoklik = schválení.
 * Sdílené chatem (index.html) i ERP. Self-contained.
 */
(function () {
  "use strict";

  var PREVIEW = "/api/v1/erp/deploy/preview";
  var NOW = "/api/v1/erp/deploy/now";

  // Parent-check: preview (bez fetch) vrátí 200 jen rodičům → jinak tlačítko nezobrazíme.
  try {
    fetch(PREVIEW, { credentials: "same-origin" })
      .then(function (r) { if (r.ok) _renderButton(); })
      .catch(function () {});
  } catch (e) {}

  function _renderButton() {
    if (document.getElementById("erpDeployBtn")) return;
    var b = document.createElement("button");
    b.id = "erpDeployBtn";
    b.type = "button";
    b.textContent = "🚀";
    b.title = "Nasadit nejnovější verzi (git pull + restart API)";
    b.style.cssText =
      "position:fixed;left:12px;bottom:12px;z-index:99000;width:40px;height:40px;" +
      "border-radius:50%;background:#243a44;border:1px solid #356e6e;color:#a8d4dc;" +
      "font-size:18px;cursor:pointer;opacity:0.65;box-shadow:0 2px 8px rgba(0,0,0,0.4);";
    b.addEventListener("mouseenter", function () { b.style.opacity = "1"; });
    b.addEventListener("mouseleave", function () { b.style.opacity = "0.65"; });
    b.addEventListener("click", _onClick);
    document.body.appendChild(b);
  }

  function _onClick() {
    var b = document.getElementById("erpDeployBtn");
    if (b) { b.disabled = true; b.textContent = "…"; }
    fetch(PREVIEW + "?fetch=1", { credentials: "same-origin" })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (j) {
        if (b) { b.disabled = false; b.textContent = "🚀"; }
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
        _dialog(
          "Nasadit nejnovější verzi?",
          j.files_changed + " souborů změněno · cíl " + j.target +
          "\n„" + (j.commit_message || "") + "\"\n\n" +
          "Spustí git pull + restart API na serveru.",
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
      })
      .catch(function () { _toast("Deploy selhal (síť)", true); });
  }

  // ── self-contained dialog + toast ──
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
      var cancel = document.createElement("button");
      cancel.type = "button"; cancel.textContent = "Zrušit";
      cancel.style.cssText = "padding:8px 16px;background:#2a3340;border:none;border-radius:4px;color:#cfd6df;cursor:pointer;font-size:13px;";
      cancel.addEventListener("click", _close);
      row.appendChild(cancel);
      var ok = document.createElement("button");
      ok.type = "button"; ok.textContent = "🚀 Nasadit";
      ok.style.cssText = "padding:8px 16px;background:#3a7a3a;border:none;border-radius:4px;color:#fff;font-weight:600;cursor:pointer;font-size:13px;";
      ok.addEventListener("click", function () { _close(); onOk(); });
      row.appendChild(ok);
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
