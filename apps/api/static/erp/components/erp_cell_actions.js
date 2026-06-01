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
            if (j && j.ok) _miniToast("📲 Posláno na mobil — vytoč tam: " + (label || phone));
            else _miniToast("⚠ Odeslání na mobil selhalo");
          })
          .catch(function () { _miniToast("⚠ Odeslání na mobil selhalo"); });
      } catch (e) { console.warn("[cell-action dial push]", e); }
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
        } else {
          // PC → cross-device: vytočí mobil přes frontu + banner
          _pushDialRequest(tel, val, (ctx && ctx.label) || null);
        }
        return true;
      }
      if (action.kind === "email") {
        // Fáze 1 fallback: mailto:. Fáze 2 nahradí in-app editorem + šablonou.
        _log("email", val, Object.assign({}, ctx, { templateId: action.template_id || null }));
        try { window.location.href = "mailto:" + encodeURIComponent(val); }
        catch (e) { console.warn("[cell-action email]", e); }
        return true;
      }
      return false;
    }

    global.ErpCellActions = {
      detect: detect,
      resolve: resolve,
      execute: execute,
      _log: _log,
    };
  });
})(window);
