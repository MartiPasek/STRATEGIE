/* eslint-disable */
/**
 * carddav_connect.js — F1.6/F1.7: self-service připojení telefonu na kontakty.
 * ─────────────────────────────────────────────────────────────────────────────
 * Marti 3.6.2026 ("dotáhnout kontakty pro Pavla"): každý user (Pavel, Kristý…)
 * si sám klikem vygeneruje CardDAV přístup pro svůj telefon + dostane návod.
 * Žádné ruční SQL tokeny.
 *
 * Modal: stav (kolik kontaktů připraveno) + seznam zařízení (odpojit) +
 * "Připojit nový telefon" → token (PLAINTEXT 1×) + URL/login + krok-za-krokem
 * (Android přes DAVx5, iOS nativně).
 *
 * Backend (carddav.py mgmt router):
 *   GET  /api/v1/erp/carddav/info
 *   POST /api/v1/erp/carddav/token            {device_label}
 *   POST /api/v1/erp/carddav/token/{id}/revoke
 *
 * Sdílené — loadováno chatem (index.html) i ERP. Self-contained.
 * Expozice: window.openCarddavConnect().
 */
(function () {
  "use strict";

  var BASE = "/api/v1/erp/carddav";
  var _open = false;
  // TEL = zařízení s telefonem (mobil / naše appka). APP = PC/notebook/tablet.
  var IS_TEL = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent || "") || !!window.STRATEGIE;
  var IS_IOS = /iPhone|iPad|iPod/i.test(navigator.userAgent || "");
  var IS_ANDROID = /Android/i.test(navigator.userAgent || "");

  function _esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  function _toast(msg) {
    try {
      var t = document.createElement("div");
      t.textContent = msg;
      t.style.cssText =
        "position:fixed;left:50%;bottom:34px;transform:translateX(-50%);" +
        "background:#1f2a37;color:#e8eef5;border:1px solid #3a4a5e;" +
        "border-radius:9px;padding:9px 16px;font-size:13px;z-index:100090;" +
        "box-shadow:0 8px 24px rgba(0,0,0,.45);";
      document.body.appendChild(t);
      setTimeout(function () { try { t.remove(); } catch (e) {} }, 1900);
    } catch (e) {}
  }

  function _copy(text, label) {
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(
          function () { _toast("✓ Zkopírováno" + (label ? " — " + label : "")); },
          function () { _fallbackCopy(text, label); });
      } else { _fallbackCopy(text, label); }
    } catch (e) { _fallbackCopy(text, label); }
  }
  function _fallbackCopy(text, label) {
    try {
      var ta = document.createElement("textarea");
      ta.value = text; ta.style.cssText = "position:fixed;opacity:0;";
      document.body.appendChild(ta); ta.select();
      document.execCommand("copy"); ta.remove();
      _toast("✓ Zkopírováno" + (label ? " — " + label : ""));
    } catch (e) { _toast("Kopírování selhalo — zkopíruj ručně."); }
  }

  function _api(path, method, body) {
    var opts = { method: method || "GET", credentials: "same-origin",
                 headers: { "Accept": "application/json" } };
    if (body) { opts.headers["Content-Type"] = "application/json";
                opts.body = JSON.stringify(body); }
    return fetch(BASE + path, opts).then(function (r) {
      return r.json().catch(function () { return { ok: false, error: "parse" }; })
        .then(function (j) { j._status = r.status; return j; });
    });
  }

  // ── DOM ────────────────────────────────────────────────────────────────

  function _close() {
    _open = false;
    var ov = document.getElementById("carddavConnectOverlay");
    if (ov) { try { ov.remove(); } catch (e) {} }
    document.removeEventListener("keydown", _esckey, true);
  }
  function _esckey(e) { if (e.key === "Escape") _close(); }

  function _row(label, value, copyLabel) {
    return '<div style="display:flex;align-items:center;gap:8px;margin:6px 0;">' +
      '<div style="min-width:78px;color:#9fb0c4;font-size:12px;">' + _esc(label) + '</div>' +
      '<code style="flex:1;background:#0f1620;border:1px solid #2c3a4c;border-radius:6px;' +
      'padding:7px 9px;font-size:12.5px;color:#dbe6f2;word-break:break-all;">' + _esc(value) + '</code>' +
      '<button type="button" class="cdav-copy" data-copy="' + _esc(value) + '" ' +
      'data-lbl="' + _esc(copyLabel || label) + '" ' +
      'style="background:#2b3a4d;color:#cfe0f2;border:none;border-radius:6px;' +
      'padding:7px 10px;font-size:12px;cursor:pointer;white-space:nowrap;">Kopírovat</button>' +
      '</div>';
  }

  function _dateOnly(s) { return String(s || "").split(" ")[0]; }

  function _devicesHtml(info) {
    var active = (info.tokens || []).filter(function (t) { return !t.revoked; });
    if (!active.length) {
      return '<div style="color:#8aa0b8;font-size:13px;padding:4px 0 2px;">' +
        'Zatím žádné spárování.</div>';
    }
    var uname = info.user_name || "";
    var h = '';
    active.forEach(function (t) {
      h += '<div style="display:flex;align-items:center;gap:10px;padding:8px 0;' +
        'border-bottom:1px solid #233140;">' +
        '<span style="font-size:18px;">📱</span>' +
        '<div style="flex:1;min-width:0;">' +
        '<div style="font-size:13.5px;color:#e8eef5;">' + _esc(t.device_label || "Telefon") +
        (uname ? ' <span style="color:#7fd6c2;">· ' + _esc(uname) + '</span>' : '') + '</div>' +
        '<div style="font-size:11px;color:#8aa0b8;">spárováno ' + _esc(_dateOnly(t.created)) +
        (t.last_used ? ' · naposledy ' + _esc(t.last_used) : ' · zatím nesynchronizováno') + '</div>' +
        '</div>' +
        '<button type="button" class="cdav-revoke" data-id="' + t.id + '" ' +
        'data-lbl="' + _esc(t.device_label || "Telefon") + '" ' +
        'style="background:transparent;color:#e89b9b;border:1px solid #5a3a3a;' +
        'border-radius:6px;padding:6px 10px;font-size:12px;cursor:pointer;">Odpojit</button>' +
        '</div>';
    });
    return h;
  }

  function _instructionsHtml(info, username, token, appleOnly) {
    var url = info.carddav_url || "";
    return '' +
      '<details style="margin-top:14px;" open>' +
      '<summary style="cursor:pointer;color:#bcd0e6;font-size:13px;font-weight:600;' +
      'margin-bottom:8px;">📖 Návod — jak telefon připojit</summary>' +
      '<div style="font-size:13px;color:#d4e0ec;line-height:1.55;">' +

      (appleOnly ? '' : (
      '<div style="font-weight:700;color:#7fd6c2;margin:10px 0 4px;">📱 Android (přes DAVx5)</div>' +
      '<ol style="margin:0 0 6px 18px;padding:0;">' +
      '<li>Nainstaluj <strong>DAVx5</strong> (Google Play — malý jednorázový poplatek; nebo zdarma přes <strong>F-Droid</strong>).</li>' +
      '<li>Otevři DAVx5 → <strong>+</strong> → <strong>Přihlásit pomocí URL a uživ. jména</strong>.</li>' +
      '<li>URL: <code style="color:#bfe;">' + _esc(url) + '</code> · Uživatel: <code style="color:#bfe;">' + _esc(username) + '</code> → Pokračovat.</li>' +
      '<li>Heslo: vlož <strong>token</strong> výše → Přihlásit.</li>' +
      '<li>Otevři účet → <strong>Metoda seskupování kontaktů</strong> → zvol <strong>„Skupiny jako kategorie" (CATEGORIES)</strong>.</li>' +
      '<li><strong>Obnovit seznam adresářů</strong> → vyber <em>Reální / Potenciální klienti</em>.</li>' +
      '<li><strong>⟳ Synchronizovat</strong> (nebo stáhni seznam dolů) — DAVx5 ukáže svoji sync notifikaci a stáhne kontakty.</li>' +
      '<li>Zapni <strong>Synchronizace v pravidelných intervalech</strong> a vyber <strong>interval</strong> (např. 1–4 h). Volbu <em>„VPN vyžaduje nadřazené připojení"</em> nech <strong>vypnutou</strong>.</li>' +
      '</ol>')) +

      '<div style="font-weight:700;color:#7fd6c2;margin:12px 0 4px;">🍏 iPhone (nativně)</div>' +
      '<ol style="margin:0 0 6px 18px;padding:0;">' +
      '<li>Nastavení → <strong>Kontakty</strong> → Účty → <strong>Přidat účet</strong> → <strong>Jiný</strong>.</li>' +
      '<li>Přidat účet <strong>CardDAV</strong>.</li>' +
      '<li>Server: <code style="color:#bfe;">' + _esc((url || "").replace(/^https?:\/\//, "").replace(/\/carddav\/?$/, "")) + '</code></li>' +
      '<li>Uživatel: <code style="color:#bfe;">' + _esc(username) + '</code> · Heslo: <strong>token</strong> výše.</li>' +
      '<li>Další → Uložit. Kontakty se objeví v aplikaci Telefon/Kontakty.</li>' +
      '</ol>' +

      '<div style="margin-top:8px;color:#8aa0b8;font-size:12px;">' +
      'Sync je <strong>jednosměrný</strong> (telefon zrcadlí STRATEGII) a <strong>jen pro čtení</strong> — ' +
      'úpravy v telefonu se nikam nepřepíšou. Sada se průběžně doplňuje, jak voláš klientům.</div>' +
      '</div></details>';
  }

  function _credentialPanel(info, res, mode) {
    // res = výsledek POST /token (obsahuje plaintext token 1× + handoff_url pro QR)
    var qrBlock = "";
    if (res.handoff_url) {
      qrBlock =
        '<div style="text-align:center;margin:4px 0 10px;">' +
        '<div style="font-size:14px;color:#f0d98a;font-weight:700;margin-bottom:8px;">' +
        '📷 Naskenuj telefonem</div>' +
        '<div data-cdav-qr="1" data-url="' + _esc(res.handoff_url) + '" ' +
        'style="display:inline-block;background:#fff;padding:10px;border-radius:10px;' +
        'min-width:170px;min-height:170px;line-height:0;">' +
        '<div style="color:#888;font-size:12px;line-height:1.4;padding:64px 12px;">QR…</div></div>' +
        '<div style="font-size:12.5px;color:#bcd0e6;margin:8px auto 0;max-width:300px;line-height:1.45;">' +
        'Fotoaparátem (bez instalace appky) → token a návod naskočí přímo v mobilu. ' +
        'Platí ~' + (res.handoff_ttl_min || 15) + ' min.</div>' +
        '</div>';
    }
    // Android — veřejná stránka /app-setup (stáhne appku BEZ loginu + spáruje).
    // Funguje i na čerstvém telefonu, který ve STRATEGII nikdy nebyl přihlášený.
    var appSetupUrl = res.app_setup_url ||
      ((location && location.origin || "") + "/app-setup/");
    var deepLink = "strategiemobil://pair?u=" + encodeURIComponent((location && location.origin) || "") +
      "&t=" + encodeURIComponent(res.token || "") + "&k=mobile";
    // Na telefonu (Android): tap přímo na app-setup stránku. Na PC: QR.
    var appBody = IS_TEL
      ? ('<a href="' + _esc(appSetupUrl) + '" ' +
         'style="display:inline-block;background:#1f3a2e;border:1px solid #3a7a4a;color:#cdeede;' +
         'border-radius:8px;padding:12px 18px;font-size:14px;font-weight:700;text-decoration:none;">' +
         '⬇️ Stáhnout appku a spárovat</a>' +
         '<div style="font-size:12px;color:#8aa0b8;margin-top:8px;">Máš appku už nainstalovanou? ' +
         '<a href="' + _esc(deepLink) + '" style="color:#7fd6c2;">Jen spárovat</a></div>')
      : ('<div data-app-qr="1" data-url="' + _esc(appSetupUrl) + '" ' +
         'style="display:inline-block;background:#fff;padding:10px;border-radius:10px;' +
         'min-width:170px;min-height:170px;line-height:0;">' +
         '<div style="color:#888;font-size:12px;line-height:1.4;padding:64px 12px;">QR…</div></div>' +
         '<div style="font-size:12.5px;color:#bcd0e6;margin:8px auto 0;max-width:300px;line-height:1.45;">' +
         'Naskenuj telefonem fotoaparátem → appka se stáhne a po instalaci spáruje. ' +
         'Bez přihlašování na telefonu.</div>');
    var appQrBlock =
      '<div style="text-align:center;margin:4px 0 10px;">' +
      '<div style="font-size:14px;color:#7fd6c2;font-weight:700;margin-bottom:8px;">' +
      '🤖 Android — STRATEGIE Mobil</div>' +
      appBody +
      '</div>';
    // mode: "android" = naše appka (app-setup QR, bez loginu) · "ios" = iPhone
    // nativní CardDAV · jinak obojí
    var inner, showCredDetails;
    if (mode === "android") { inner = appQrBlock; showCredDetails = false; }
    else if (mode === "ios") {
      inner =
        '<div style="font-size:12.5px;color:#bcd0e6;margin:0 0 10px;line-height:1.5;">' +
        '🍏 <strong>iPhone</strong> — kontakty přidáš přes nativní CardDAV. Naskenuj QR, ' +
        'nebo zadej údaje ručně níž:</div>' + qrBlock;
      showCredDetails = true;
    } else { inner = qrBlock + appQrBlock; showCredDetails = true; }
    return '' +
      '<div style="background:rgba(232,185,35,.08);border:1px solid #6b5a22;' +
      'border-radius:10px;padding:14px;margin-top:12px;">' +
      '<div style="font-size:13px;color:#f0d98a;font-weight:700;margin-bottom:8px;">' +
      '🔑 Přístup pro „' + _esc(res.device_label || "Telefon") + '"</div>' +
      inner +
      (showCredDetails ?
        ('<details ' + (res.handoff_url ? "" : "open") + ' style="margin-top:4px;">' +
        '<summary style="cursor:pointer;color:#cdb87a;font-size:12.5px;font-weight:600;">' +
        'Nebo zadat ručně (token, URL, login + návod)</summary>' +
        '<div style="font-size:12px;color:#cdb87a;margin:8px 0;">' +
        'Token se zobrazí <strong>jen teď</strong>. Pak už ho neuvidíš (vygeneruješ nový).</div>' +
        _row("Adresa", info.carddav_url, "CardDAV URL") +
        _row("Uživatel", info.username, "uživatel") +
        _row("Token", res.token, "token") +
        _instructionsHtml(info, info.username, res.token, true) +
        '</details>') : '') +
      '</div>';
  }

  // ── QR (lazy-load knihovny z CDN) ────────────────────────────────────────
  var _qrCbs = null;
  function _loadQrLib(cb) {
    if (window.qrcode) { cb(true); return; }
    if (_qrCbs) { _qrCbs.push(cb); return; }
    _qrCbs = [cb];
    var s = document.createElement("script");
    s.src = "https://cdn.jsdelivr.net/npm/qrcode-generator@1.4.4/qrcode.js";
    s.onload = function () { var q = _qrCbs; _qrCbs = null; q.forEach(function (f) { f(!!window.qrcode); }); };
    s.onerror = function () { var q = _qrCbs; _qrCbs = null; q.forEach(function (f) { f(false); }); };
    document.head.appendChild(s);
  }
  function _renderQr(url, el) {
    if (!url || !el) return;
    _loadQrLib(function (ok) {
      if (!ok || !window.qrcode) {
        el.innerHTML = '<div style="color:#a33;font-size:12px;line-height:1.4;padding:30px 10px;">QR se nenačetlo — rozbal „ručně" níž.</div>';
        return;
      }
      try {
        var qr = window.qrcode(0, "M");
        qr.addData(url);
        qr.make();
        el.innerHTML = qr.createSvgTag({ cellSize: 4, margin: 1, scalable: true });
        var svg = el.querySelector("svg");
        if (svg) { svg.style.width = "100%"; svg.style.height = "auto"; svg.style.maxWidth = "220px"; svg.style.display = "block"; }
      } catch (e) {
        el.innerHTML = '<div style="color:#a33;font-size:12px;line-height:1.4;padding:30px 10px;">QR chyba — rozbal „ručně" níž.</div>';
      }
    });
  }

  function _render(info, credPanelHtml) {
    var ov = document.getElementById("carddavConnectOverlay");
    if (!ov) return;
    var card = ov.querySelector("[data-cdav-card]");
    if (!card) return;

    var n = info.active_contacts || 0;
    var contactsLine = n > 0
      ? '<strong style="color:#7fd6c2;">' + n + '</strong> ' +
        (n === 1 ? "kontakt připraven" : (n < 5 ? "kontakty připraveny" : "kontaktů připraveno")) +
        " k synchronizaci"
      : 'Sada se naplní automaticky, jak začneš <strong>volat klientům</strong> z CRM.';

    card.innerHTML =
      '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">' +
      '<div style="font-size:17px;font-weight:700;color:#e8eef5;">📱 Synchronizace s telefonem</div>' +
      '<button type="button" data-cdav-close style="background:transparent;border:none;' +
      'color:#9fb0c4;font-size:22px;line-height:1;cursor:pointer;">×</button></div>' +

      '<div style="font-size:13px;color:#bcd0e6;line-height:1.5;margin-bottom:10px;">' +
      'Když si telefon připojíš, při <strong>příchozím i odchozím hovoru uvidíš jméno klienta</strong> ' +
      'ze STRATEGIE. ' + contactsLine + '</div>' +

      // STRATEGIE Mobil — stažení appky z webu (i pro vzdálené kolegy s loginem).
      '<a href="/api/v1/erp/app/mobile/download" ' +
      'style="display:block;text-align:center;background:#22344a;color:#bfe3ff;' +
      'border:1px solid #35506e;border-radius:8px;padding:10px 12px;font-size:12.5px;' +
      'text-decoration:none;margin-bottom:6px;">📥 Stáhnout appku STRATEGIE Mobil (Android)</a>' +

      // F1.4: sjednocení sady (STR- prefix do starších vCardů)
      (n > 0 ?
        '<button type="button" data-cdav-refresh style="background:#2b3a4d;' +
        'color:#cfe0f2;border:1px solid #3a4a5e;border-radius:8px;padding:9px 12px;' +
        'font-size:12.5px;cursor:pointer;width:100%;margin-bottom:6px;">' +
        '🔄 Obnovit a sjednotit kontakty (vyhledatelné přes „STR-")</button>' : '') +

      // credential panel (jen po vytvoření)
      (credPanelHtml || '') +

      // device list (kontext: APP = PC/tablet ukazuje spárované telefony;
      // TEL = telefon ukazuje, s kým je spárovaný)
      '<div style="margin-top:14px;">' +
      '<div style="font-size:12px;text-transform:uppercase;letter-spacing:.04em;' +
      'color:#7e93a8;font-weight:700;margin-bottom:4px;">' +
      (IS_TEL ? "Tento telefon je spárovaný" : "Spárované telefony") +
      ((info.tokens || []).filter(function (t) { return !t.revoked; }).length
        ? ' (' + (info.tokens || []).filter(function (t) { return !t.revoked; }).length + ')' : '') +
      '</div>' +
      '<div data-cdav-devices>' + _devicesHtml(info) + '</div></div>' +

      // create button
      '<div data-cdav-create style="margin-top:14px;"></div>';

    // wire close
    var cl = card.querySelector("[data-cdav-close]");
    if (cl) cl.addEventListener("click", _close);

    // wire copy
    card.querySelectorAll(".cdav-copy").forEach(function (b) {
      b.addEventListener("click", function () {
        _copy(b.getAttribute("data-copy") || "", b.getAttribute("data-lbl") || "");
      });
    });
    // wire revoke
    card.querySelectorAll(".cdav-revoke").forEach(function (b) {
      b.addEventListener("click", function () {
        var id = b.getAttribute("data-id");
        var lbl = b.getAttribute("data-lbl") || "zařízení";
        if (!confirm('Odpojit „' + lbl + '"? Telefon přestane synchronizovat kontakty.')) return;
        b.disabled = true; b.textContent = "…";
        _api("/token/" + id + "/revoke", "POST").then(function (j) {
          if (j && j.ok) { _toast("✓ Odpojeno"); info.tokens = j.tokens || info.tokens; _render(info, ''); }
          else { b.disabled = false; b.textContent = "Odpojit"; _toast("Nepodařilo se odpojit."); }
        });
      });
    });

    // F1.4 obnovit/sjednotit sadu
    var rf = card.querySelector("[data-cdav-refresh]");
    if (rf) rf.addEventListener("click", function () {
      rf.disabled = true;
      var old = rf.innerHTML; rf.textContent = "Obnovuji…";
      _api("/refresh", "POST").then(function (j) {
        rf.disabled = false; rf.innerHTML = old;
        if (j && j.ok) {
          _toast("✓ Sjednoceno " + (j.refreshed || 0) + " z " + (j.total || 0) +
                 " kontaktů. V DAVx5 ťukni ⟳ Synchronizovat (nebo počkej na interval).");
        } else { _toast("Obnovení se nepodařilo."); }
      });
    });

    _renderCreateArea(card, info);

    // QR (po vykreslení panelu) — naskenuj telefonem → token na mobil.
    var qrEl = card.querySelector("[data-cdav-qr]");
    if (qrEl) _renderQr(qrEl.getAttribute("data-url"), qrEl);
    var appQrEl = card.querySelector("[data-app-qr]");
    if (appQrEl) _renderQr(appQrEl.getAttribute("data-url"), appQrEl);
  }

  function _renderCreateArea(card, info) {
    var area = card.querySelector("[data-cdav-create]");
    if (!area) return;
    var btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = "➕ Spárovat s telefonem";
    btn.style.cssText =
      "background:#e8b923;color:#1c2530;border:none;padding:11px 18px;" +
      "border-radius:9px;font-size:14px;font-weight:700;cursor:pointer;width:100%;";
    btn.addEventListener("click", function () { _showCreateForm(area, info); });
    area.innerHTML = "";
    area.appendChild(btn);
  }

  function _showCreateForm(area, info) {
    area.innerHTML =
      '<div style="font-size:13px;color:#bcd0e6;margin-bottom:8px;">Pojmenuj telefon (např. „Mirek soukromý", „Sdílený Mirek+Zuzka") a vyber způsob:</div>' +
      '<input type="text" data-cdav-label placeholder="Název telefonu" ' +
      'maxlength="80" style="width:100%;background:#0f1620;border:1px solid #2c3a4c;' +
      'border-radius:8px;padding:10px 11px;color:#e8eef5;font-size:13px;margin-bottom:8px;">' +
      '<div style="display:flex;gap:8px;">' +
      '<button type="button" data-cdav-app style="flex:1;background:#1f3a2e;color:#cdeede;' +
      'border:1px solid #3a7a4a;padding:11px;border-radius:8px;font-size:14px;font-weight:700;cursor:pointer;">🤖 Android</button>' +
      '<button type="button" data-cdav-noapp style="flex:1;background:#22344a;color:#bfe3ff;' +
      'border:1px solid #35506e;padding:11px;border-radius:8px;font-size:14px;font-weight:700;cursor:pointer;">🍏 iPhone</button>' +
      '</div>' +
      '<div style="font-size:11.5px;color:#8aa0b8;margin-top:6px;line-height:1.45;">' +
      '<b>Android</b> = naše appka STRATEGIE Mobil (QR stáhne a spáruje, i na čerstvém telefonu). ' +
      '<b>iPhone</b> = nativní kontakty přes CardDAV.</div>' +
      '<button type="button" data-cdav-cancel style="background:transparent;color:#9fb0c4;' +
      'border:1px solid #44566c;padding:9px;border-radius:8px;font-size:13px;cursor:pointer;width:100%;margin-top:8px;">Zpět</button>';
    var inp = area.querySelector("[data-cdav-label]");
    var cancel = area.querySelector("[data-cdav-cancel]");
    if (inp) { try { inp.focus(); } catch (e) {} }
    if (cancel) cancel.addEventListener("click", function () { _renderCreateArea(area.closest("[data-cdav-card]"), info); });
    function _do(mode) {
      _api("/token", "POST", { device_label: (inp && inp.value || "").trim() || "Telefon" }).then(function (j) {
        if (j && j.ok && j.token) {
          info.tokens = j.tokens || info.tokens;
          info.active_contacts = (j.active_contacts != null) ? j.active_contacts : info.active_contacts;
          _render(info, _credentialPanel(info, j, mode));
        } else if (j && j.error === "limit") {
          _toast(j.message || "Dosažen limit zařízení.");
        } else {
          _toast((j && j.message) || "Nepodařilo se vygenerovat token.");
        }
      });
    }
    var bApp = area.querySelector("[data-cdav-app]");
    var bNo = area.querySelector("[data-cdav-noapp]");
    if (bApp) bApp.addEventListener("click", function () { _do("android"); });
    if (bNo) bNo.addEventListener("click", function () { _do("ios"); });
  }

  function _shell() {
    var ov = document.createElement("div");
    ov.id = "carddavConnectOverlay";
    ov.style.cssText =
      "position:fixed;inset:0;z-index:100060;background:rgba(8,12,18,.64);" +
      "display:flex;align-items:flex-start;justify-content:center;padding:24px 14px;" +
      "overflow:auto;backdrop-filter:blur(2px);";
    var card = document.createElement("div");
    card.setAttribute("data-cdav-card", "1");
    card.style.cssText =
      "max-width:480px;width:100%;margin:auto;background:#1c2530;color:#e8eef5;" +
      "border:1px solid #3a4a5e;border-top:3px solid #e8b923;border-radius:14px;" +
      "padding:20px;box-shadow:0 18px 50px rgba(0,0,0,.55);font-family:inherit;";
    card.innerHTML = '<div style="padding:30px;text-align:center;color:#8aa0b8;">Načítám…</div>';
    ov.appendChild(card);
    ov.addEventListener("click", function (e) { if (e.target === ov) _close(); });
    document.body.appendChild(ov);
    document.addEventListener("keydown", _esckey, true);
  }

  function openCarddavConnect() {
    if (_open) return;
    _open = true;
    _shell();
    _api("/info", "GET").then(function (info) {
      if (!info || info.ok === false) {
        if (info && info._status === 401) { _close(); _toast("Nejdřív se přihlas."); return; }
        var card = document.querySelector("#carddavConnectOverlay [data-cdav-card]");
        if (card) card.innerHTML =
          '<div style="padding:24px;text-align:center;color:#e89b9b;">Nepodařilo se načíst.' +
          '<br><button type="button" onclick="(window.openCarddavConnect&&(' +
          'document.getElementById(\'carddavConnectOverlay\').remove(),window.__cdavReopen()))" ' +
          'style="margin-top:12px;background:#2b3a4d;color:#cfe0f2;border:none;border-radius:7px;' +
          'padding:8px 14px;cursor:pointer;">Zkusit znovu</button></div>';
        return;
      }
      _render(info, '');
    });
  }
  window.__cdavReopen = function () { _open = false; openCarddavConnect(); };
  window.openCarddavConnect = openCarddavConnect;
})();
