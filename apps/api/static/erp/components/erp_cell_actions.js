/* eslint-disable */
/**
 * erp_cell_actions.js — dynamické akce na buňkách/polích (Marti 1.6.2026).
 * ─────────────────────────────────────────────────────────────────────────────
 *
 * Pavel obchodník: dvojklik na buňku v gridu / klik na ikonu ve formu, kde je
 * telefon / email / web → akce:
 *   - web   → normalizace (www.x → https://www.x) + window.open
 *   - phone → tel: odkaz → na mobilu v PWA otevře nativní dialer
 *   - email → mailto: (Fáze 1 fallback; Fáze 2 → in-app editor + šablona)
 *
 * Hybrid detekce (Marti's volba): auto-detekce podle hodnoty + explicit
 * override v layout.action (Fáze 2 — ⚙ settings, email šablony per pole).
 *
 * Každá akce se ARCHIVUJE — POST /api/v1/erp/contact-action (audit RO,
 * "archivovat čísla která se vytáčely"). Logujeme čas zahájení; délku hovoru
 * z tel: nelze (dialer je černá skříňka).
 *
 * Public API:
 *   window.ErpCellActions.detect(value) → {kind,value,normalized} | null
 *   window.ErpCellActions.resolve(layout, value) → action | null
 *   window.ErpCellActions.execute(action, ctx) → bool
 *
 * Wrapped v _erpLoadModule (Module Health visibility).
 */
"use strict";

(function (global) {
  "use strict";

  var _loader = (typeof global !== "undefined" && global._erpLoadModule)
    ? global._erpLoadModule
    : function (id, ver, fn) { try { fn(); } catch (e) { console.error("[" + id + "]", e); } };

  _loader("erp_cell_actions.js", "v1.0.0", function () {

    // Email: jednoduchý ale dostatečně přísný (jeden @, doména s tečkou).
    var EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]{2,}$/;
    // Web: http(s):// nebo www. nebo holá doména (domain.tld[/...]).
    var WEB_SCHEME_RE = /^https?:\/\//i;
    var WEB_WWW_RE = /^www\./i;
    var WEB_DOMAIN_RE = /^[a-z0-9][a-z0-9.-]*\.[a-z]{2,}(?:[/?#].*)?$/i;
    // Phone: jen +, číslice a oddělovače; aspoň 6 číslic.
    var PHONE_SHAPE_RE = /^[+(]?[\d][\d\s()\/.\-]+$/;

    function _digits(v) { return String(v).replace(/[^\d]/g, ""); }

    /** Auto-detekce typu akce z hodnoty. null = neaktivní. */
    function detect(raw) {
      if (raw == null) return null;
      var v = String(raw).trim();
      if (!v || v === "—") return null;

      if (EMAIL_RE.test(v)) {
        return { kind: "email", value: v, normalized: v };
      }
      // Web (před telefonem — "www.x" by jinak nematchlo phone, ok)
      if (WEB_SCHEME_RE.test(v)) {
        return { kind: "web", value: v, normalized: v };
      }
      if (WEB_WWW_RE.test(v) || WEB_DOMAIN_RE.test(v)) {
        return { kind: "web", value: v, normalized: "https://" + v.replace(/^\/+/, "") };
      }
      // Phone — shape + aspoň 6 číslic (vyhne se "2", "16" diskriminátorům)
      if (PHONE_SHAPE_RE.test(v) && _digits(v).length >= 6) {
        var d = _digits(v);
        var tel = (v.charAt(0) === "+" ? "+" : "") + d;
        return { kind: "phone", value: v, normalized: tel };
      }
      return null;
    }

    /**
     * Resolve akce: explicit layout.action override > auto-detekce.
     * layout.action = {kind:'auto'|'web'|'email'|'phone'|'none', template_id?}
     */
    function resolve(layout, raw) {
      var act = layout && layout.action;
      if (act && act.kind && act.kind !== "auto") {
        if (act.kind === "none") return null;
        var base = detect(raw) || { value: String(raw == null ? "" : raw).trim() };
        if (!base.value) return null;
        return {
          kind: act.kind,
          value: base.value,
          normalized: base.normalized || base.value,
          template_id: act.template_id || null,
        };
      }
      return detect(raw);
    }

    /** Archiv akce (audit RO, append-only). Best-effort — nikdy nehodí. */
    function _log(kind, value, ctx) {
      try {
        fetch("/api/v1/erp/contact-action", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "same-origin",
          body: JSON.stringify({
            action_kind: kind,
            value: value,
            contact_table: (ctx && ctx.table) || null,
            contact_row_id: (ctx && ctx.rowId) || null,
            template_id: (ctx && ctx.templateId) || null,
            contact_name: (ctx && ctx.name) || null,            // CardDAV F1.2: jméno z řádku
            typ_zakazky: (ctx && ctx.typ != null) ? ctx.typ : null,  // 10 = potential
          }),
        }).catch(function () { /* offline / 500 — akce proběhne i tak */ });
      } catch (e) { /* defensive */ }
    }

    function _openTel(tel) {
      var a = document.createElement("a");
      a.href = "tel:" + tel;
      a.style.display = "none";
      document.body.appendChild(a);
      try { a.click(); } finally {
        setTimeout(function () { try { document.body.removeChild(a); } catch (e) {} }, 0);
      }
    }

    // Fáze 3 (cross-device telefon): mobil → lokální dialer; PC → push do
    // fronty fw.phone_dial_request → mobil (PWA chat) pollne + ťukne + vytočí.
    function _isMobile() {
      try {
        if (/Mobi|Android|iPhone|iPad|iPod/i.test(navigator.userAgent || "")) return true;
        if (window.matchMedia && window.matchMedia("(pointer:coarse)").matches) return true;
      } catch (e) {}
      return false;
    }

    function _cookieUid() {
      try {
        var m = document.cookie.match(/(?:^|;\s*)user_id=(\d+)/);
        return m ? parseInt(m[1], 10) : null;
      } catch (e) { return null; }
    }

    function _miniToast(msg) {
      try {
        var t = document.createElement("div");
        t.textContent = msg;
        t.style.cssText =
          "position:fixed;left:50%;bottom:32px;transform:translateX(-50%);" +
          "background:#1f3a2e;border:1px solid #2f5a44;color:#cdeede;" +
          "padding:10px 18px;border-radius:6px;font-size:13px;z-index:100002;" +
          "box-shadow:0 4px 16px rgba(0,0,0,0.4);opacity:0;transition:opacity .15s;";
        document.body.appendChild(t);
        requestAnimationFrame(function () { t.style.opacity = "1"; });
        setTimeout(function () {
          t.style.opacity = "0";
          setTimeout(function () { try { document.body.removeChild(t); } catch (e) {} }, 220);
        }, 2600);
      } catch (e) {}
    }

    function _pushDialRequest(phone, raw, label) {
      try {
        fetch("/api/v1/erp/phone-dial-request", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "same-origin",
          body: JSON.stringify({ phone: phone, raw_value: raw, label: label || null }),
        }).then(function (r) { return r.json(); })
          .then(function (j) {
            if (j && j.ok) {
              _miniToast("📲 Posláno na mobil — vytoč tam: " + (label || phone));
              // Marti 3.6.: po založení záznamu otevři jádro pro zápis hovoru
              // (Protokol vytáčení → poznámka) na nový řádek. edit_core_id +
              // id (request) vrací backend; fail-soft pokud DesignFwForm chybí.
              try {
                if (j.edit_core_id && j.id && typeof window.DesignFwForm === "function") {
                  var _fwf = new window.DesignFwForm({
                    coreId: j.edit_core_id, rowId: j.id, mode: "edit",
                  });
                  // DesignFwForm konstruktor jen uloží opts — render dělá .open()
                  if (typeof _fwf.open === "function") _fwf.open();
                }
              } catch (e) { console.warn("[cell-action dial→edit form]", e); }
            } else {
              _miniToast("⚠ Odeslání na mobil selhalo");
            }
          })
          .catch(function () { _miniToast("⚠ Odeslání na mobil selhalo"); });
      } catch (e) { console.warn("[cell-action dial push]", e); }
    }

    // ── Email link mode (Marti 2.6.2026, "Obojí"): per-user volba jak otevřít
    // e-mail. 'mailto' (default = systémový klient) | 'owa' (webmail compose
    // v prohlížeči) | 'copy' (zkopírovat adresu). Uloženo v "user".ui_pref
    // přes /api/v1/erp/user-prefs. První dvojklik nabídne volbu + zapamatuje;
    // změna kdykoli přes ErpCellActions.openEmailPrefDialog() (profil menu).
    var _emailMode = null;        // null = nenačteno / nenastaveno → chooser
    var OWA_BASE = "https://mail.eurosoft-control.cz/owa/?path=/mail/action/compose&to=";

    function _loadPrefs() {
      try {
        fetch("/api/v1/erp/user-prefs", { credentials: "same-origin", cache: "no-store" })
          .then(function (r) { return r.ok ? r.json() : null; })
          .then(function (j) {
            if (j && j.prefs && j.prefs.email_link_mode) _emailMode = j.prefs.email_link_mode;
          })
          .catch(function () {});
      } catch (e) {}
    }
    _loadPrefs();

    function _savePrefMode(mode) {
      _emailMode = mode;
      try {
        fetch("/api/v1/erp/user-prefs", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "same-origin",
          body: JSON.stringify({ email_link_mode: mode }),
        }).catch(function () {});
      } catch (e) {}
    }

    function _modeLabel(mode) {
      if (mode === "owa") return "Webmail (OWA)";
      if (mode === "copy") return "Kopírovat adresu";
      return "Systémový klient";
    }

    function _owaCompose(email) {
      try { window.open(OWA_BASE + encodeURIComponent(email), "_blank", "noopener,noreferrer"); }
      catch (e) { console.warn("[cell-action owa]", e); }
    }

    function _copyEmail(email) {
      try {
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(email).then(
            function () { _miniToast("📋 Zkopírováno: " + email); },
            function () { _miniToast("📋 " + email); }
          );
          return;
        }
      } catch (e) {}
      try {
        var ta = document.createElement("textarea");
        ta.value = email;
        ta.style.cssText = "position:fixed;opacity:0;";
        document.body.appendChild(ta);
        ta.select();
        try { document.execCommand("copy"); _miniToast("📋 Zkopírováno: " + email); }
        catch (e2) { _miniToast("📋 " + email); }
        document.body.removeChild(ta);
      } catch (e3) { _miniToast("📋 " + email); }
    }

    function _dispatchEmail(mode, email) {
      if (mode === "owa") { _owaCompose(email); return; }
      if (mode === "copy") { _copyEmail(email); return; }
      try { window.location.href = "mailto:" + encodeURIComponent(email); }
      catch (e) { console.warn("[cell-action email]", e); }
    }

    /**
     * Chooser dialog (3 možnosti + "zapamatovat"). onPick(mode, remember).
     * email==null → settings režim (z profilu): podtitulek bez konkrétní adresy.
     */
    function _emailChooser(email, onPick) {
      var ov = document.createElement("div");
      ov.style.cssText =
        "position:fixed;inset:0;z-index:100065;background:rgba(8,12,18,.6);" +
        "display:flex;align-items:center;justify-content:center;padding:18px;";
      var card = document.createElement("div");
      card.style.cssText =
        "max-width:440px;width:100%;background:#1c2530;color:#e8eef5;" +
        "border:1px solid #3a4a5e;border-radius:12px;padding:20px;" +
        "box-shadow:0 18px 50px rgba(0,0,0,.55);font-size:14px;";

      var h = document.createElement("div");
      h.style.cssText = "font-weight:700;font-size:15px;margin-bottom:6px;";
      h.textContent = "Jak otevírat e-maily?";
      card.appendChild(h);

      var sub = document.createElement("div");
      sub.style.cssText = "color:#9fb0c4;font-size:12px;margin-bottom:14px;";
      sub.textContent = email
        ? ("Kliknul jsi na " + email)
        : "Vyber, jak se otevře e-mail po dvojkliku na buňku/pole.";
      card.appendChild(sub);

      function close() { try { ov.remove(); } catch (e) {} document.removeEventListener("keydown", esc, true); }
      function esc(e) { if (e.key === "Escape") close(); }

      [
        { mode: "mailto", title: "Systémový klient", desc: "Otevře výchozí e-mailový program (Outlook…)." },
        { mode: "owa", title: "Webmail (OWA)", desc: "Napsat v prohlížeči přes webový Outlook." },
        { mode: "copy", title: "Zkopírovat adresu", desc: "Jen zkopíruje e-mail do schránky." },
      ].forEach(function (o) {
        var b = document.createElement("button");
        b.type = "button";
        var sel = (o.mode === _emailMode);
        b.style.cssText =
          "display:block;width:100%;text-align:left;margin-bottom:8px;" +
          "background:#243140;color:#e8eef5;border:1px solid " +
          (sel ? "#e8b923" : "#3a4a5e") + ";border-radius:8px;padding:10px 12px;cursor:pointer;";
        b.innerHTML =
          "<div style='font-weight:600;'>" + o.title + (sel ? " ✓" : "") + "</div>" +
          "<div style='font-size:12px;color:#9fb0c4;margin-top:2px;'>" + o.desc + "</div>";
        b.addEventListener("click", function () {
          var remember = !rememberCb || rememberCb.checked;
          close();
          onPick(o.mode, remember);
        });
        card.appendChild(b);
      });

      var foot = document.createElement("label");
      foot.style.cssText =
        "display:flex;align-items:center;gap:8px;margin-top:6px;" +
        "font-size:12px;color:#bcd0e6;cursor:pointer;";
      var rememberCb = document.createElement("input");
      rememberCb.type = "checkbox";
      rememberCb.checked = true;
      foot.appendChild(rememberCb);
      foot.appendChild(document.createTextNode("Zapamatovat tuto volbu (lze změnit v profilu)"));
      card.appendChild(foot);

      ov.appendChild(card);
      ov.addEventListener("click", function (e) { if (e.target === ov) close(); });
      document.addEventListener("keydown", esc, true);
      document.body.appendChild(ov);
    }

    /** Otevři chooser jako nastavení (z profil menu). Vždy uloží volbu. */
    function openEmailPrefDialog() {
      _emailChooser(null, function (mode) {
        _savePrefMode(mode);
        _miniToast("✉ E-maily: " + _modeLabel(mode));
      });
    }

    /** Provede akci + zaloguje. Vrací true pokud něco udělala. */
    function execute(action, ctx) {
      if (!action || !action.kind) return false;
      var val = action.value;
      if (val == null || String(val).trim() === "") return false;

      if (action.kind === "web") {
        _log("web", val, ctx);
        try {
          window.open(action.normalized || val, "_blank", "noopener,noreferrer");
        } catch (e) { console.warn("[cell-action web]", e); }
        return true;
      }
      if (action.kind === "phone") {
        _log("phone", val, ctx);
        var tel = action.normalized || _digits(val);
        if (_isMobile()) {
          _openTel(tel);  // lokální dialer (mobil v PWA)
        } else if (window.ActPipeline && typeof window.ActPipeline.run === "function") {
          // PC → FW Action Pipeline (3.6.2026, Marti: "prevorat na akce").
          // Engine ridi: db_insert -> push_notification -> open_core ->
          // note_writeback -> grid_refresh. Nahrazuje hardcoded _pushDialRequest.
          window.ActPipeline.run("phone_dial_flow", {
            phone: tel,
            raw_value: val,
            label: (ctx && ctx.label) || null,
            target_user_id: window._erpCurrentUserId || _cookieUid(),
            contact_table: (ctx && (ctx.table || ctx.contact_table)) || null,
            contact_row_id: (ctx && (ctx.rowId || ctx.contact_row_id)) || null
          }).then(function (res) {
            if (!res || res.status === "error") {
              _miniToast("⚠ Pipeline: " + ((res && res.error) || "chyba"));
            }
          }).catch(function () { _miniToast("⚠ Telefonní pipeline selhala"); });
        } else {
          // Fallback (orchestrátor nenačten): původní cross-device push.
          _pushDialRequest(tel, val, (ctx && ctx.label) || null);
        }
        return true;
      }
      if (action.kind === "email") {
        _log("email", val, Object.assign({}, ctx, { templateId: action.template_id || null }));
        if (_emailMode) {
          _dispatchEmail(_emailMode, val);          // volba už uložená
        } else {
          // první použití → nabídni volbu, případně zapamatuj
          _emailChooser(val, function (mode, remember) {
            if (remember) _savePrefMode(mode);      // persist (+ set _emailMode)
            _dispatchEmail(mode, val);
          });
        }
        return true;
      }
      return false;
    }

    global.ErpCellActions = {
      detect: detect,
      resolve: resolve,
      execute: execute,
      openEmailPrefDialog: openEmailPrefDialog,
      _log: _log,
    };
  });
})(window);
