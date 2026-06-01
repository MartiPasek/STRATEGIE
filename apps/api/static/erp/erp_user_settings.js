/**
 * ErpUserSettings — per-user nastavení prostředí ERP.
 *
 * Marti 1.6.2026: "nastavení prostředí, které per user budeme moci měnit.
 * Začneme prosvícením gridu." Pavel kritizoval čitelnost textu v dark mode.
 *
 * Storage: localStorage, klíčováno per user_id (window._erpCurrentUserId) —
 * na sdíleném prohlížeči se nemíchá mezi uživateli. DB sync = future (stejný
 * settings objekt → snadné přenést na /api/v1/erp/user-settings).
 *
 * Apply: injektovaný <style id="erp-user-settings-style"> s !important na
 * AG CSS custom properties — spolehlivě přebije inline theme override
 * (.ag-theme-quartz-dark { --ag-data-color }) bez závislosti na specificitě.
 *
 * API:
 *   ErpUserSettings.init()           — load + apply (volat při page load)
 *   ErpUserSettings.get(key)         — hodnota
 *   ErpUserSettings.set(key, value)  — save + apply
 *   ErpUserSettings.openPanel()      — settings modal UI
 *
 * Settings:
 *   gridTextBrightness: 200..255 (grayscale jas textu v gridech; default 243)
 */
(function (global) {
  "use strict";

  const _loader = (typeof global !== "undefined" && global._erpLoadModule)
    ? global._erpLoadModule
    : function (id, ver, fn) { try { fn(); } catch (e) { console.error("[" + id + "] init failed:", e); } };

  _loader("erp_user_settings.js", "v1.0.0", function () {

    const DEFAULTS = {
      gridTextBrightness: 243,   // #f3f3f3 — světlý text gridu (dark mode)
    };

    function _storageKey() {
      let uid = "anon";
      try { if (global._erpCurrentUserId != null) uid = String(global._erpCurrentUserId); } catch (e) {}
      return "erp.user.settings.v1." + uid;
    }

    function load() {
      let s = {};
      try {
        const raw = localStorage.getItem(_storageKey());
        if (raw) s = JSON.parse(raw) || {};
      } catch (e) { s = {}; }
      return Object.assign({}, DEFAULTS, s);
    }

    function save(s) {
      try { localStorage.setItem(_storageKey(), JSON.stringify(s)); } catch (e) {}
    }

    function _clampBrightness(v) {
      v = parseInt(v, 10);
      if (isNaN(v)) v = DEFAULTS.gridTextBrightness;
      return Math.max(200, Math.min(255, v));
    }

    function _grayHex(b) {
      const h = b.toString(16).padStart(2, "0");
      return "#" + h + h + h;
    }

    let _current = load();

    function apply(s) {
      s = s || _current;
      let style = document.getElementById("erp-user-settings-style");
      if (!style) {
        style = document.createElement("style");
        style.id = "erp-user-settings-style";
        document.head.appendChild(style);
      }
      const b = _clampBrightness(s.gridTextBrightness);
      const hex = _grayHex(b);
      // !important přebije inline .ag-theme-quartz-dark override v page CSS.
      style.textContent =
        ".ag-theme-quartz, .ag-theme-quartz-dark, .erp-ag-grid {" +
        "  --ag-data-color: " + hex + " !important;" +
        "  --ag-foreground-color: " + hex + " !important;" +
        "  --ag-header-foreground-color: " + hex + " !important;" +
        "}";
    }

    function get(key) { return _current[key]; }

    function set(key, value) {
      _current[key] = value;
      save(_current);
      apply(_current);
    }

    function reset() {
      _current = Object.assign({}, DEFAULTS);
      save(_current);
      apply(_current);
    }

    function init() {
      _current = load();
      apply(_current);
    }

    // ── Settings panel (modal) ──────────────────────────────────────
    function openPanel() {
      // Zavři existující
      const old = document.getElementById("erpUserSettingsOverlay");
      if (old) { old.remove(); return; }

      const overlay = document.createElement("div");
      overlay.id = "erpUserSettingsOverlay";
      overlay.style.cssText =
        "position:fixed;inset:0;background:rgba(0,0,0,0.45);z-index:100000;" +
        "display:flex;align-items:center;justify-content:center;";

      const dlg = document.createElement("div");
      dlg.style.cssText =
        "background:#1a1f26;border:1px solid #2a3340;border-radius:8px;" +
        "width:440px;max-width:94vw;color:#cfd6df;font-size:13px;" +
        "box-shadow:0 16px 50px rgba(0,0,0,0.6);overflow:hidden;";

      // Header
      const hdr = document.createElement("div");
      hdr.style.cssText =
        "padding:12px 16px;border-bottom:1px solid #2a3340;background:#141a20;" +
        "display:flex;align-items:center;justify-content:space-between;";
      hdr.innerHTML =
        '<span style="font-size:14px;font-weight:600;color:#e8eef5;">⚙ Nastavení prostředí</span>';
      const closeX = document.createElement("button");
      closeX.type = "button";
      closeX.textContent = "✕";
      closeX.style.cssText =
        "background:transparent;border:none;color:#8a96a4;font-size:16px;" +
        "cursor:pointer;padding:0 4px;";
      closeX.addEventListener("click", () => overlay.remove());
      hdr.appendChild(closeX);
      dlg.appendChild(hdr);

      // Body
      const body = document.createElement("div");
      body.style.cssText = "padding:16px;display:flex;flex-direction:column;gap:16px;";

      // ── Prosvícení gridu ──
      const sec = document.createElement("div");
      sec.style.cssText = "display:flex;flex-direction:column;gap:8px;";
      const lbl = document.createElement("label");
      lbl.style.cssText = "font-size:12px;color:#a8b4c2;font-weight:600;";
      lbl.textContent = "Prosvícení textu v gridech";
      sec.appendChild(lbl);

      const hint = document.createElement("div");
      hint.style.cssText = "font-size:11px;color:#8a96a4;";
      hint.textContent = "Jas písma v přehledech (tmavší ↔ jasnější bílá).";
      sec.appendChild(hint);

      const row = document.createElement("div");
      row.style.cssText = "display:flex;align-items:center;gap:12px;";
      const slider = document.createElement("input");
      slider.type = "range";
      slider.min = "200";
      slider.max = "255";
      slider.step = "1";
      slider.value = String(_clampBrightness(_current.gridTextBrightness));
      slider.style.cssText = "flex:1;accent-color:#4f8ef7;cursor:pointer;";

      // Live preview swatch
      const preview = document.createElement("span");
      preview.textContent = "Abc 123";
      preview.style.cssText =
        "min-width:70px;text-align:center;padding:4px 8px;border-radius:4px;" +
        "background:#14161a;border:1px solid #2a3340;font-weight:600;";
      const _updatePreview = (b) => { preview.style.color = _grayHex(b); };
      _updatePreview(_clampBrightness(_current.gridTextBrightness));

      slider.addEventListener("input", () => {
        const b = _clampBrightness(slider.value);
        _updatePreview(b);
        set("gridTextBrightness", b);   // live apply + save
      });

      row.appendChild(slider);
      row.appendChild(preview);
      sec.appendChild(row);
      body.appendChild(sec);

      dlg.appendChild(body);

      // Footer
      const ftr = document.createElement("div");
      ftr.style.cssText =
        "padding:10px 16px;border-top:1px solid #2a3340;background:#141a20;" +
        "display:flex;align-items:center;justify-content:space-between;gap:8px;";
      const resetBtn = document.createElement("button");
      resetBtn.type = "button";
      resetBtn.textContent = "↺ Výchozí";
      resetBtn.style.cssText =
        "background:#1a2028;border:1px solid #2a3340;color:#a8b4c2;" +
        "padding:6px 12px;border-radius:4px;cursor:pointer;font-size:12px;";
      resetBtn.addEventListener("click", () => {
        reset();
        slider.value = String(DEFAULTS.gridTextBrightness);
        _updatePreview(DEFAULTS.gridTextBrightness);
      });
      const okBtn = document.createElement("button");
      okBtn.type = "button";
      okBtn.textContent = "Hotovo";
      okBtn.style.cssText =
        "background:var(--accent,#4f8ef7);border:none;color:#fff;" +
        "padding:6px 16px;border-radius:4px;cursor:pointer;font-size:12px;font-weight:600;";
      okBtn.addEventListener("click", () => overlay.remove());
      ftr.appendChild(resetBtn);
      ftr.appendChild(okBtn);
      dlg.appendChild(ftr);

      overlay.appendChild(dlg);
      overlay.addEventListener("click", (ev) => { if (ev.target === overlay) overlay.remove(); });
      document.addEventListener("keydown", function _esc(ev) {
        if (ev.key === "Escape") { overlay.remove(); document.removeEventListener("keydown", _esc); }
      });
      document.body.appendChild(overlay);
    }

    global.ErpUserSettings = {
      init: init,
      get: get,
      set: set,
      reset: reset,
      apply: apply,
      openPanel: openPanel,
    };

    // Auto-init. Pozor: window._erpCurrentUserId se v page nastavuje až
    // pozdějším inline scriptem — při načtení tohoto souboru ještě nemusí
    // existovat (storage key by byl '.anon'). Proto init() voláme DVAKRÁT:
    // hned (apply defaultů → žádný flash tmavého textu) + na DOMContentLoaded
    // (to už je _erpCurrentUserId nastaveno → načte skutečné per-user hodnoty).
    function _autoInit() {
      try { init(); } catch (e) { console.warn("[erp_user_settings] init failed", e); }
    }
    _autoInit();
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", _autoInit);
    }

  }); // _erpLoadModule end
})(typeof window !== "undefined" ? window : this);
