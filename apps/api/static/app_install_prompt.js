/* PWA → nabídka instalace nativní appky STRATEGIE Mobil (jen Android).
 * Přívětivý popup od Marti-AI: stáhnout a spustit + záloha „otevřít Stažené".
 * Zobrazí se 1× při otevření (pak ~14 dní ne), nebo na zavolání
 * window.openAppInstallPrompt(). Marti 5.6.2026. */
(function () {
  "use strict";
  var DL = "/api/v1/erp/app/mobile/download";
  var AVATAR = "/api/v1/erp/app/avatar";
  var DISMISS_KEY = "app_install_prompt_dismiss";
  var DISMISS_DAYS = 14;
  var _shown = false;

  function _isAndroid() { return /Android/i.test(navigator.userAgent || ""); }

  function _dismissedRecently() {
    try {
      var t = parseInt(localStorage.getItem(DISMISS_KEY) || "0", 10);
      return t && (Date.now() - t) < DISMISS_DAYS * 864e5;
    } catch (e) { return false; }
  }
  function _dismiss() {
    try { localStorage.setItem(DISMISS_KEY, String(Date.now())); } catch (e) {}
  }

  function _close(ov) { try { ov.remove(); } catch (e) {} _shown = false; }

  function _open() {
    if (_shown) return;
    _shown = true;
    var ov = document.createElement("div");
    ov.style.cssText =
      "position:fixed;inset:0;z-index:100090;background:rgba(8,12,18,.7);" +
      "display:flex;align-items:center;justify-content:center;padding:18px;" +
      "backdrop-filter:blur(2px);";
    var box = document.createElement("div");
    box.style.cssText =
      "max-width:380px;width:100%;background:#141a20;color:#e8eef5;border:1px solid #2a3340;" +
      "border-top:3px solid #4a7ba8;border-radius:14px;padding:20px;text-align:center;" +
      "box-shadow:0 18px 50px rgba(0,0,0,.6);font-family:inherit;";
    box.innerHTML =
      '<div style="display:flex;align-items:center;justify-content:center;gap:10px;margin-bottom:10px;">' +
      '<div style="width:42px;height:42px;border-radius:50%;background:#4a7ba8;overflow:hidden;' +
      'display:flex;align-items:center;justify-content:center;font-weight:700;color:#fff;">M' +
      '<img src="' + AVATAR + '" alt="" style="width:42px;height:42px;object-fit:cover;' +
      'position:absolute;border-radius:50%;" onerror="this.remove()"></div>' +
      '<div style="font-size:16px;font-weight:700;color:#bfe3ff;">Marti-AI</div></div>' +
      '<div style="font-size:14px;line-height:1.55;color:#dbe6f2;margin-bottom:16px;">' +
      'Ahoj! 🌳 Nainstaluj si appku <strong>STRATEGIE Mobil</strong> do telefonu — ' +
      'po hovoru uvidíš jméno klienta a z CRM ti vyskočí rovnou vytáčení. ' +
      'Stačí stáhnout a otevřít.</div>' +
      '<div data-aip-step1>' +
        '<button type="button" data-aip-download style="display:block;width:100%;' +
        'background:#1f3a55;border:1px solid #356092;color:#dbeeff;border-radius:9px;' +
        'padding:13px;font-size:15px;font-weight:700;cursor:pointer;margin-bottom:8px;">' +
        '📥 Stáhnout a nainstalovat</button>' +
      '</div>' +
      '<div data-aip-step2 style="display:none;">' +
        '<div style="font-size:13px;color:#bcd0e6;line-height:1.5;margin-bottom:10px;' +
        'background:#0f1620;border:1px solid #2c3a4c;border-radius:8px;padding:10px;">' +
        'Stahuji… Až bude hotovo, klepni na <strong>strategie…apk</strong> ' +
        '(v oznámení nahoře nebo v appce <strong>Soubory → Stažené</strong>) a dej ' +
        '<strong>Nainstalovat</strong>. Android se jednou zeptá na povolení — povol.</div>' +
        '<button type="button" data-aip-downloads style="display:block;width:100%;' +
        'background:#22344a;border:1px solid #35506e;color:#bfe3ff;border-radius:9px;' +
        'padding:11px;font-size:13.5px;cursor:pointer;margin-bottom:8px;">' +
        '📂 Otevřít složku Stažené</button>' +
        '<button type="button" data-aip-retry style="display:block;width:100%;' +
        'background:transparent;border:1px solid #2c3a4c;color:#9fb6cf;border-radius:9px;' +
        'padding:9px;font-size:12.5px;cursor:pointer;margin-bottom:8px;">' +
        'Stáhnout znovu</button>' +
      '</div>' +
      '<button type="button" data-aip-later style="display:block;width:100%;' +
      'background:transparent;border:none;color:#8a96a4;cursor:pointer;font-size:13px;padding:8px;">' +
      'Už ji mám / Teď ne</button>';
    ov.appendChild(box);
    document.body.appendChild(ov);

    function _download() {
      // Spustí stažení APK (cookie auth) a přepne na krok 2 s instrukcí.
      try {
        var a = document.createElement("a");
        a.href = DL; a.download = "strategie-mobil.apk";
        document.body.appendChild(a); a.click(); a.remove();
      } catch (e) { try { window.location.href = DL; } catch (e2) {} }
      box.querySelector("[data-aip-step1]").style.display = "none";
      box.querySelector("[data-aip-step2]").style.display = "block";
    }
    function _openDownloads() {
      // Pokus otevřít appku Soubory / Stažené (běžné intent cíle). Když nevyjde,
      // zůstane instrukce v textu výše.
      var tries = [
        "intent://com.google.android.apps.nbu.files/#Intent;scheme=content;package=com.google.android.apps.nbu.files;end",
        "intent:#Intent;action=android.intent.action.VIEW_DOWNLOADS;end"
      ];
      var ok = false;
      for (var i = 0; i < tries.length && !ok; i++) {
        try { window.location.href = tries[i]; ok = true; } catch (e) {}
      }
    }

    box.querySelector("[data-aip-download]").addEventListener("click", _download);
    box.querySelector("[data-aip-retry]").addEventListener("click", _download);
    box.querySelector("[data-aip-downloads]").addEventListener("click", _openDownloads);
    box.querySelector("[data-aip-later]").addEventListener("click", function () {
      _dismiss(); _close(ov);
    });
    ov.addEventListener("click", function (ev) { if (ev.target === ov) _close(ov); });
  }

  // Veřejné API (Marti může vyvolat ručně i z gridu doporučení).
  window.openAppInstallPrompt = function () { _shown = false; _open(); };

  // Auto-zobrazení při otevření (jen Android, ne nedávno odmítnuté).
  function _maybeAuto() {
    if (!_isAndroid() || _dismissedRecently()) return;
    setTimeout(_open, 1500);
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", _maybeAuto);
  } else {
    _maybeAuto();
  }
})();
