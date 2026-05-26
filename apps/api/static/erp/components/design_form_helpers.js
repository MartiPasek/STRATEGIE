/**
 * design_form_helpers.js — utility helpers for design forms.
 *
 * Phase JS-2 (18.5.2026 ~22:30): Extract z design_forms.js (~2334 LOC).
 * Marti's direktiva: "maximalni modularni poradek pro lepsi ladeni".
 *
 * Exports via global._erpDFH namespace. Loaded BEFORE design_forms.js.
 *
 * Contains:
 *   - Toast: _showToast, _markFormDirty + module state _dirtyForms
 *   - User overrides: _loadUserOverrides, _saveUserOverride + LS_KEY, palette
 *   - Tooltip: _installDarkTooltips + DOM refs
 *   - Dialogs: _promptDarkDialog, _confirmDarkDialog
 *   - Modal shell: _buildModalShell, _buildDescriptionsPopup
 *   - Widgets: _field, _memo, _dropdown, _readonlyInput
 *   - Field settings: _openFieldSettingsPopup, _resolveColor + overrides
 *   - Section helpers: _sectionKeyFromTitle, _sectionBuild
 */
(function (global) {
  "use strict";

  // Phase JS-4 (18.5.2026): mutual immunity wrap pro Module Health visibility.
  // Pri init failure: chyba do _erpModuleHealth + diag_log, ostatni moduly pokracuji.
  const _loader = (typeof global !== "undefined" && global._erpLoadModule)
    ? global._erpLoadModule
    : function (id, ver, fn) { try { fn(); } catch (e) { console.error("[" + id + "] init failed:", e); } };

  _loader("design_form_helpers.js", "v1.0.0", function () {



  // Esc helper
  function _esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, c =>
      ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])
    );
  }

  // ────────────────────────────────────────────────────────────────────
  // Phase 38.4 Krok 14b+9-A (13.5.2026 ~21:30, Marti's "vysperkovat pred
  // zitrejsi prezentaci IT timu"): Toast notification system. Fixed
  // bottom-right, fade-in/hold/fade-out animation. Stack support pokud
  // multiple toasts (top-down).
  //
  // Types:
  //   success (default) → green accent, ✓ icon
  //   error             → red accent, ✕ icon
  //   info              → blue accent, ℹ icon
  // ────────────────────────────────────────────────────────────────────
  function _ensureToastContainer() {
    let c = document.getElementById("erp-toast-container");
    if (c) return c;
    c = document.createElement("div");
    c.id = "erp-toast-container";
    c.style.cssText =
      "position:fixed;bottom:20px;right:20px;z-index:99999;" +
      "display:flex;flex-direction:column-reverse;gap:8px;" +
      "pointer-events:none;";
    document.body.appendChild(c);
    return c;
  }

  function _ensureToastStyles() {
    if (document.getElementById("erp-toast-styles")) return;
    const styles = document.createElement("style");
    styles.id = "erp-toast-styles";
    styles.textContent = [
      "@keyframes erpToastIn {",
      "  from { opacity: 0; transform: translateX(20px); }",
      "  to   { opacity: 1; transform: translateX(0); }",
      "}",
      "@keyframes erpToastOut {",
      "  from { opacity: 1; transform: translateX(0); }",
      "  to   { opacity: 0; transform: translateX(20px); }",
      "}",
      ".erp-toast {",
      "  display: flex; align-items: center; gap: 10px;",
      "  padding: 10px 16px; border-radius: 4px;",
      "  background: #1a1f26; border: 1px solid #2a3340;",
      "  color: #cfd6df; font-size: 13px;",
      "  box-shadow: 0 6px 20px rgba(0,0,0,0.5);",
      "  pointer-events: auto; min-width: 220px; max-width: 380px;",
      "  animation: erpToastIn 200ms ease;",
      "}",
      ".erp-toast.fadeout { animation: erpToastOut 300ms ease forwards; }",
      ".erp-toast-icon { font-size: 16px; line-height: 1; flex: 0 0 auto; }",
      ".erp-toast-msg { flex: 1 1 auto; }",
      ".erp-toast-success { border-left: 3px solid #4caf6a; }",
      ".erp-toast-success .erp-toast-icon { color: #4caf6a; }",
      ".erp-toast-error { border-left: 3px solid #e57373; }",
      ".erp-toast-error .erp-toast-icon { color: #e57373; }",
      ".erp-toast-info { border-left: 3px solid #5a8aaa; }",
      ".erp-toast-info .erp-toast-icon { color: #7ed4e8; }",
      // Phase 38.4 Krok 14b+9-C: drag drop flash animations
      "@keyframes erpFieldFlashSuccess {",
      "  0%   { background: rgba(76,175,106,0.0); }",
      "  20%  { background: rgba(76,175,106,0.3); }",
      "  100% { background: rgba(76,175,106,0.0); }",
      "}",
      ".erp-field-design-wrap {",
      "  transition: transform 200ms ease, border-color 150ms;",
      "}",
      ".erp-field-flash-success {",
      "  animation: erpFieldFlashSuccess 700ms ease;",
      "}",
      // Phase 38.4 Krok 14b+9-D: hover ✕ delete button
      ".erp-field-design-wrap .erp-field-design-delete {",
      "  opacity: 0 !important; transition: opacity 150ms;",
      "}",
      ".erp-field-design-wrap:hover .erp-field-design-delete {",
      "  opacity: 1 !important;",
      "}",
      // Phase 38.4 Krok 14c+3.5 (14.5.2026 odpoledne, Marti's regrese
      // "od posledni zmeny renderuji ty ikonky i kdyz se pres ne neprejizdi"):
      //   ROOT CAUSE: opacity rules měly low specificity. Inline style.opacity
      //   z dragend handlerů (Krok 14c+3.4 nastavil inline transition) +
      //   default opacity:1 user-agent style přebily naše hover-only rules.
      //   Fix: !important na opacity rules — top specificity guarantee.
      //
      // Action buttons (✕ + ⬅ + 🎯) jako absolute overlay v pravem hornim
      // rohu komponenty — visible jen on parent .erp-field-design-wrap
      // hover. Sdílí `erp-field-design-action-hoveronly` class.
      ".erp-field-design-wrap .erp-field-design-action-hoveronly {",
      "  opacity: 0 !important; transition: opacity 150ms;",
      "}",
      ".erp-field-design-wrap:hover .erp-field-design-action-hoveronly {",
      "  opacity: 1 !important;",
      "}",
    ].join("\n");
    document.head.appendChild(styles);
  }

  function _showToast(msg, type, durationMs) {
    _ensureToastStyles();
    const c = _ensureToastContainer();
    type = type || "success";
    durationMs = durationMs || 1800;
    const icons = { success: "✓", error: "✕", info: "ℹ" };
    const t = document.createElement("div");
    t.className = "erp-toast erp-toast-" + type;
    const iconEl = document.createElement("span");
    iconEl.className = "erp-toast-icon";
    iconEl.textContent = icons[type] || icons.success;
    const msgEl = document.createElement("span");
    msgEl.className = "erp-toast-msg";
    msgEl.textContent = String(msg || "");
    t.appendChild(iconEl);
    t.appendChild(msgEl);
    c.appendChild(t);
    setTimeout(() => {
      t.classList.add("fadeout");
      setTimeout(() => {
        try { t.parentNode && t.parentNode.removeChild(t); } catch (e) {}
      }, 320);
    }, durationMs);
  }
  // Export pro pouziti mimo design_forms.js (budouci ERP toasts)
  global.erpShowToast = _showToast;

  // ────────────────────────────────────────────────────────────────────
  // Phase 38.4 Krok 14a-A1r (12.5.2026 vecer, Marti's bug catch):
  // F5 / tab close / browser back s otevrenym Design modal s dirty fields
  // mel zavrit modal bez varovani. Fix: window.beforeunload listener
  // + global Set s dirty form instances. Browser ukaze NATIVE warning
  // (custom message neni v modernich prohlizecich supportable kvuli
  // security — phishing prevention). Native hlaska je dostatecna.
  // ────────────────────────────────────────────────────────────────────
  const _dirtyForms = new Set();
  function _markFormDirty(formInst, isDirty) {
    if (!formInst) return;
    if (isDirty) {
      _dirtyForms.add(formInst);
    } else {
      _dirtyForms.delete(formInst);
    }
  }
  if (!global._erpDesignBeforeUnloadInstalled) {
    global._erpDesignBeforeUnloadInstalled = true;
    // Fallback: native browser warning pro tab close / browser back /
    // adresar manual URL change (kde keydown intercept nepomuze).
    global.addEventListener("beforeunload", (ev) => {
      if (_dirtyForms.size > 0) {
        ev.preventDefault();
        ev.returnValue = "";
        return "";
      }
    });
    // A1r polish (12.5.2026 vecer doma): Marti's request "uprav dialog
    // na dark design". Native beforeunload dialog NELZE prepsat (security
    // / phishing prevention v modernich prohlizecich). ALE F5 / Ctrl+R
    // muzeme zachytit pres keydown event a ukazat nas dark
    // _confirmDarkDialog. Pokud user potvrdi, location.reload(). Pokud
    // zrusi, modal zustane otevreny.
    //
    // Pokryti:
    //   F5         → keydown intercept → dark dialog ✓
    //   Ctrl+R     → keydown intercept → dark dialog ✓
    //   Ctrl+Shift+R → same ✓
    //   ✕ tab      → beforeunload native dialog (fallback)
    //   Browser back/forward → beforeunload native dialog (fallback)
    //   Address bar URL change → beforeunload native dialog (fallback)
    global.addEventListener("keydown", async (ev) => {
      const isF5 = ev.key === "F5" || ev.keyCode === 116;
      const isCtrlR = (ev.ctrlKey || ev.metaKey) && (ev.key === "r" || ev.key === "R");
      if (!isF5 && !isCtrlR) return;
      if (_dirtyForms.size === 0) return; // no dirty → allow native reload
      // Intercept native reload
      ev.preventDefault();
      ev.stopPropagation();
      // Count dirty fields across all open forms
      let totalDirty = 0;
      _dirtyForms.forEach((f) => {
        if (f && f._dirty && typeof f._dirty.size === "number") {
          totalDirty += f._dirty.size;
        }
      });
      // Czech plural (A1q pattern): 1 = neulozenou zmenu, 2-4 = neulozene zmeny, 5+ = neulozenych zmen
      const phrase = totalDirty === 1
        ? "1 neuloženou změnu"
        : (totalDirty < 5 ? totalDirty + " neuložené změny" : totalDirty + " neuložených změn");
      // A1t: default Ano/Ne (Marti's polish — sjednoceny lidsky pattern).
      const decision = await _confirmDarkDialog({
        title: "Obnovit stránku?",
        message: "Máš " + phrase + " v otevřeném design dialogu.\n\nPři obnovení (F5) se neuložené změny ztratí. Opravdu chceš obnovit?",
      });
      if (decision === true) {
        // User potvrdil — clear dirty tracking aby beforeunload neprerusil reload
        _dirtyForms.clear();
        global.location.reload();
      }
      // decision === false → keep dialog open, do nothing
    }, true); // capture phase — zachyti i pred input field handler
  }

  // ────────────────────────────────────────────────────────────────────
  // Phase 38.4 Krok 14a-A1g #3 (12.5.2026 odpoledne): Dark scrollbar
  // pro design modal body + page control content. Inject once při module load.
  // ────────────────────────────────────────────────────────────────────

  // ────────────────────────────────────────────────────────────────────
  // Phase 38.4 Krok 14a-A1i (12.5.2026): Marti's polish — custom dark
  // tooltip nahrazuje browser native `title` attribute (Marti's #1:
  // hinty maji byt take dark design). 1s delay before show, fade-in.
  //
  // Plus inline override editing: right-click na label otevre popup
  // (userLabel + hint editor). Save → localStorage MVP, Etapa 3 do DB.
  // ────────────────────────────────────────────────────────────────────

  const OVERRIDES_LS_KEY = "erp.design.overrides.v1";

  // Load user-side overrides z localStorage (merge nad hardcoded defaults)
  // Krok 14a-A1n #2 (12.5.2026 vecer): pridana kategorie "colors" pro
  // dekorativni barvy field-by-field (Marti's request — 10 decent colors).
  function _loadUserOverrides() {
    try {
      const raw = localStorage.getItem(OVERRIDES_LS_KEY);
      if (!raw) return { labels: {}, hints: {}, colors: {} };
      const obj = JSON.parse(raw);
      return {
        labels: (obj && obj.labels) || {},
        hints: (obj && obj.hints) || {},
        colors: (obj && obj.colors) || {},
      };
    } catch (e) {
      return { labels: {}, hints: {}, colors: {} };
    }
  }

  function _saveUserOverride(kind, fieldKey, value) {
    // kind = "labels" | "hints" | "colors"; value: string | null (null = delete override)
    try {
      const u = _loadUserOverrides();
      if (value == null || value === "") {
        delete u[kind][fieldKey];
      } else {
        u[kind][fieldKey] = value;
      }
      localStorage.setItem(OVERRIDES_LS_KEY, JSON.stringify(u));
    } catch (e) {
      console.warn("save override failed:", e);
    }
  }

  // Krok 14a-A1n #2: palette pro field decorations. Decentni dark-friendly
  // accent barvy, navrzene tak aby kontrastovaly s pozadim #1a1f26 ale
  // nedominantni. Pouzite jako border-top na .erp-field-design (3px).
  const DESIGN_FIELD_PALETTE = [
    { id: null,        name: "Bez barvy",  hex: "transparent" },
    { id: "sand",      name: "Písek",      hex: "#d4b88a" },
    { id: "sage",      name: "Šalvěj",     hex: "#a8c69b" },
    { id: "steel",     name: "Ocel",       hex: "#9bb8e0" },
    { id: "rose",      name: "Růže",       hex: "#c69eb0" },
    { id: "lavender",  name: "Levandule",  hex: "#b8a4d4" },
    { id: "peach",     name: "Broskev",    hex: "#d4a87f" },
    { id: "mint",      name: "Máta",       hex: "#8fc8b9" },
    { id: "mustard",   name: "Hořčice",    hex: "#c4b076" },
    { id: "slate",     name: "Břidlice",   hex: "#9aabbf" },
    { id: "coral",     name: "Korál",      hex: "#d4858f" },
  ];

  // User overrides cache — nactema jednou při module load
  let _USER_OVERRIDES = _loadUserOverrides();

  // ────────────────────────────────────────────────────────────────────
  // Dark tooltip — global singleton, hover handler s 1s delay
  // ────────────────────────────────────────────────────────────────────

  let _tooltipEl = null;
  let _tooltipTimer = null;

  function _getTooltipEl() {
    if (_tooltipEl) return _tooltipEl;
    _tooltipEl = document.createElement("div");
    _tooltipEl.className = "erp-design-tooltip";
    _tooltipEl.style.cssText = (
      "position:fixed;z-index:9700;background:#0f141a;border:1px solid #3a4754;" +
      "color:#cfd6df;font-size:11px;line-height:1.5;padding:8px 10px;border-radius:4px;" +
      "max-width:340px;box-shadow:0 4px 16px rgba(0,0,0,0.6);" +
      "pointer-events:none;display:none;opacity:0;transition:opacity 0.15s ease;"
    );
    document.body.appendChild(_tooltipEl);
    return _tooltipEl;
  }

  function _showTooltip(text, x, y) {
    const t = _getTooltipEl();
    t.textContent = text;
    t.style.display = "block";
    // Position — prefer below cursor, but flip above if no space
    const pad = 12;
    let left = x + pad;
    let top = y + pad;
    // After 1ms (DOM measured), adjust
    requestAnimationFrame(() => {
      const r = t.getBoundingClientRect();
      if (left + r.width > window.innerWidth - 8) left = window.innerWidth - r.width - 8;
      if (top + r.height > window.innerHeight - 8) top = y - r.height - pad;
      if (left < 8) left = 8;
      if (top < 8) top = 8;
      t.style.left = left + "px";
      t.style.top = top + "px";
      t.style.opacity = "1";
    });
  }

  function _hideTooltip() {
    if (_tooltipTimer) { clearTimeout(_tooltipTimer); _tooltipTimer = null; }
    if (_tooltipEl) {
      _tooltipEl.style.opacity = "0";
      _tooltipEl.style.display = "none";
    }
  }

  function _installDarkTooltips() {
    if (window._erpDesignTooltipsInstalled) return;
    window._erpDesignTooltipsInstalled = true;
    let lastX = 0, lastY = 0;
    document.addEventListener("mousemove", (ev) => {
      lastX = ev.clientX; lastY = ev.clientY;
    }, true);
    document.addEventListener("mouseover", (ev) => {
      // Find ancestor element s data-design-hint
      const el = ev.target.closest && ev.target.closest("[data-design-hint]");
      if (!el) return;
      const hint = el.getAttribute("data-design-hint");
      if (!hint) return;
      _hideTooltip();
      _tooltipTimer = setTimeout(() => {
        _showTooltip(hint, lastX, lastY);
      }, 1000);
    }, true);
    document.addEventListener("mouseout", (ev) => {
      const el = ev.target.closest && ev.target.closest("[data-design-hint]");
      if (!el) return;
      _hideTooltip();
    }, true);
  }
  _installDarkTooltips();

  (function _injectDesignFormsCss() {
    if (document.getElementById("erp-design-forms-css")) return;
    const style = document.createElement("style");
    style.id = "erp-design-forms-css";
    style.textContent = (
      // Dark scrollbar pro design modal body + page control content area + memo
      ".erp-design-modal .erp-modal-body::-webkit-scrollbar,\n" +
      ".erp-design-modal .erp-pagecontrol-content::-webkit-scrollbar,\n" +
      ".erp-design-modal textarea::-webkit-scrollbar {\n" +
      "  width: 10px; height: 10px;\n" +
      "}\n" +
      ".erp-design-modal .erp-modal-body::-webkit-scrollbar-track,\n" +
      ".erp-design-modal .erp-pagecontrol-content::-webkit-scrollbar-track,\n" +
      ".erp-design-modal textarea::-webkit-scrollbar-track {\n" +
      "  background: #0f141a;\n" +
      "}\n" +
      ".erp-design-modal .erp-modal-body::-webkit-scrollbar-thumb,\n" +
      ".erp-design-modal .erp-pagecontrol-content::-webkit-scrollbar-thumb,\n" +
      ".erp-design-modal textarea::-webkit-scrollbar-thumb {\n" +
      "  background: #2a3340; border-radius: 5px;\n" +
      "  border: 2px solid #1a1f26;\n" +
      "}\n" +
      ".erp-design-modal .erp-modal-body::-webkit-scrollbar-thumb:hover,\n" +
      ".erp-design-modal .erp-pagecontrol-content::-webkit-scrollbar-thumb:hover,\n" +
      ".erp-design-modal textarea::-webkit-scrollbar-thumb:hover {\n" +
      "  background: #3a4754;\n" +
      "}\n" +
      // Firefox scrollbar
      ".erp-design-modal .erp-modal-body,\n" +
      ".erp-design-modal .erp-pagecontrol-content,\n" +
      ".erp-design-modal textarea {\n" +
      "  scrollbar-width: thin;\n" +
      "  scrollbar-color: #2a3340 #0f141a;\n" +
      "}\n" +
      // Krok 14a-A1m #3 (12.5.2026 odpoledne): PageControl content uvnitr
      // design modalu nemusi mit vlastni scroll — body uz scrolluje.
      // Schova zdvojený scrollbar napravo od PageControl. Marti's polish.
      ".erp-design-modal .erp-pagecontrol-content {\n" +
      "  overflow: visible !important;\n" +
      "}\n" +
      // Krok 14a-A1j #3 (12.5.2026): sjednocena min-height u all design fields
      // — Marti's polish, aby po revertu / show system names komponenty
      // nepreskakovaly nahoru/dolu. Label vzdy zabira misto i kdyz prazdny.
      // Krok 14a-A1n #1 (12.5.2026 vecer): vsechny inputs/dropdowns/formlist
      // maji forced 32px height — sjednoceno napric komponentami.
      ".erp-design-modal .erp-field-design {\n" +
      "  min-height: 56px;\n" +
      "  box-sizing: border-box;\n" +
      "}\n" +
      ".erp-design-modal .erp-field-design > *,\n" +
      ".erp-design-modal .erp-field-design *[class*=\"erp-\"] {\n" +
      "  box-sizing: border-box;\n" +
      "}\n" +
      // Unified 32px height pro all input-like controls v design modu.
      // Vyhradi se memo (multiline) — to ma vlastni height.
      ".erp-design-modal .erp-field-design:not(.erp-field-memo) .erp-input,\n" +
      ".erp-design-modal .erp-field-design:not(.erp-field-memo) .erp-input-input,\n" +
      ".erp-design-modal .erp-field-design:not(.erp-field-memo) .erp-input input,\n" +
      ".erp-design-modal .erp-field-design:not(.erp-field-memo) .erp-dropdown,\n" +
      ".erp-design-modal .erp-field-design:not(.erp-field-memo) .erp-dropdown-trigger,\n" +
      ".erp-design-modal .erp-field-design:not(.erp-field-memo) .erp-formlist,\n" +
      ".erp-design-modal .erp-field-design:not(.erp-field-memo) .erp-formlist-trigger,\n" +
      ".erp-design-modal .erp-field-design:not(.erp-field-memo) > select,\n" +
      ".erp-design-modal .erp-field-design:not(.erp-field-memo) > input {\n" +
      "  height: 32px !important;\n" +
      "  min-height: 32px !important;\n" +
      "  line-height: 1.4;\n" +
      "}\n" +
      ".erp-design-modal .erp-input-label,\n" +
      ".erp-design-modal .erp-dropdown-label,\n" +
      ".erp-design-modal .erp-memo-label {\n" +
      "  min-height: 16px;\n" +
      "  display: block;\n" +
      "}\n" +
      // Krok 14a-A1o (12.5.2026 vecer, Marti's polish po amnesii): field
      // color decoration — barva pisma uvnitr fieldu (input value text,
      // dropdown selected, memo textarea, formlist trigger) misto puvodni
      // top-border linky z A1n. Marti's slova: "misto linky nahore aplikuj
      // barvy na pismo fieldu". Vizualne intuitivnejsi — color je TAM,
      // kde se ctou data, ne mimo. Set via data-design-color attribute +
      // CSS variable --field-color.
      ".erp-design-modal .erp-field-design[data-design-color] .erp-input-input,\n" +
      ".erp-design-modal .erp-field-design[data-design-color] .erp-dropdown-trigger,\n" +
      ".erp-design-modal .erp-field-design[data-design-color] .erp-formlist-trigger,\n" +
      ".erp-design-modal .erp-field-design[data-design-color] .erp-memo-input,\n" +
      ".erp-design-modal .erp-field-design[data-design-color] input,\n" +
      ".erp-design-modal .erp-field-design[data-design-color] textarea,\n" +
      ".erp-design-modal .erp-field-design[data-design-color] select {\n" +
      "  color: var(--field-color, inherit) !important;\n" +
      "}\n" +
      // Krok 14a-A1o (12.5.2026 vecer): section title (GroupBox header)
      // color override — stejny pattern jako field text. Cilime na cely
      // header element (i jeho user/system spans), aby color zustal i
      // pri toggle system mode.
      ".erp-design-modal .erp-design-section-title[data-design-color],\n" +
      ".erp-design-modal .erp-design-section-title[data-design-color] .section-title-user,\n" +
      ".erp-design-modal .erp-design-section-title[data-design-color] .section-title-system {\n" +
      "  color: var(--field-color, inherit) !important;\n" +
      "}\n" +
      // Phase 38.4 Krok 14a-A1l #1 (12.5.2026): description pair toggling.
      // - Sekce Popis je hidden by default; 📖 ikona ji ukaze
      //   (dialog[data-design-descriptions="1"]).
      // - Uvnitr sekce vzdy dvojice memo — user + system. Pres globalni
      //   sysToggle (body[data-design-system-names]) se ukaze jen jeden.
      // - sysToggle existuje uz drive (pro labely), tady sdilime stejny
      //   trigger. Marti's design: "stejny triger jako v hlavicke pro labely".
      ".erp-design-modal .erp-design-descriptions {\n" +
      "  display: none;\n" +
      "}\n" +
      ".erp-design-modal[data-design-descriptions=\"1\"] .erp-design-descriptions {\n" +
      "  display: block;\n" +
      "}\n" +
      // user mode (default = systemToggle off): show user memo, hide system
      "body:not([data-design-system-names=\"1\"]) .erp-design-modal .desc-memo-system {\n" +
      "  display: none;\n" +
      "}\n" +
      // system mode (systemToggle on): show system memo, hide user
      "body[data-design-system-names=\"1\"] .erp-design-modal .desc-memo-user {\n" +
      "  display: none;\n" +
      "}\n" +
      // Phase 38.4 Krok 14a-A1m #1 (12.5.2026 odpoledne): section title
      // (GroupBox label) pair — stejny pattern jako u komponent. User
      // mode = user title, system mode = system title (typicky table /
      // column nazev nebo technicky popis).
      "body:not([data-design-system-names=\"1\"]) .erp-design-modal .section-title-system {\n" +
      "  display: none;\n" +
      "}\n" +
      "body[data-design-system-names=\"1\"] .erp-design-modal .section-title-user {\n" +
      "  display: none;\n" +
      "}\n" +
      // System title — barevny accent (orange) aby vyvojar videl ze je v\n" +
      // system rezimu. Pattern z desc-memo-system.\n" +
      "body[data-design-system-names=\"1\"] .erp-design-modal .erp-design-section-title {\n" +
      "  color: #c9943a;\n" +
      "  font-family: 'Consolas', 'Monaco', monospace;\n" +
      "  text-transform: none;\n" +
      "  letter-spacing: 0;\n" +
      "}\n" +
      // Krok 14a-A1l #1: vizualne odlisit system description (pro vyvojare)
      // — tmavsi pozadi + zluty/oranzovy okraj. User description je default.
      ".erp-design-modal .desc-memo-system .erp-memo-input,\n" +
      ".erp-design-modal .desc-memo-system textarea {\n" +
      "  background: #1a1612 !important;\n" +
      "  border-left: 3px solid #c9943a !important;\n" +
      "}\n" +
      ".erp-design-modal .desc-memo-system .erp-memo-label,\n" +
      ".erp-design-modal .desc-memo-system label {\n" +
      "  color: #c9943a !important;\n" +
      "}\n" +
      // Phase 38.4 Krok H+5 (26.5.2026, Marti's "zvyraznit oznacenej
      // panel na forme"): green outline + animated glow pro active
      // container target. FieldPickerModal radio button toggle ↔ aplikace
      // class .erp-design-active-container. Single-select pattern —
      // jen jeden container na formu zvyrazneny.
      "@keyframes erpActiveContainerPulse {\n" +
      "  0%, 100% { box-shadow: 0 0 0 3px rgba(93, 191, 93, 0.45), 0 0 12px rgba(93, 191, 93, 0.25); }\n" +
      "  50% { box-shadow: 0 0 0 3px rgba(93, 191, 93, 0.75), 0 0 18px rgba(93, 191, 93, 0.45); }\n" +
      "}\n" +
      ".erp-design-modal .erp-design-active-container {\n" +
      "  outline: 2px solid #5dbf5d !important;\n" +
      "  outline-offset: 2px;\n" +
      "  animation: erpActiveContainerPulse 2s ease-in-out infinite;\n" +
      "  border-radius: 4px;\n" +
      "  position: relative;\n" +
      "}\n" +
      ".erp-design-modal .erp-design-active-container::before {\n" +
      "  content: '🎯 Aktivní cíl';\n" +
      "  position: absolute;\n" +
      "  top: -10px;\n" +
      "  right: 12px;\n" +
      "  background: #5dbf5d;\n" +
      "  color: #0f1418;\n" +
      "  font-size: 10px;\n" +
      "  font-weight: 700;\n" +
      "  padding: 2px 8px;\n" +
      "  border-radius: 3px;\n" +
      "  z-index: 10;\n" +
      "  pointer-events: none;\n" +
      "  letter-spacing: 0.3px;\n" +
      "}\n" +
      // Phase 38.4 Krok H+7 (26.5.2026, Marti's "klik v palete -> zvyraznit
      // komponentu na forme"): transient flash (orange outline ~1.5s)
      // pro orchestraci click → highlight komponenty. Jiny effect nez
      // .erp-design-active-container (zelena infinite pulse) — flash je
      // single-shot reakce na klik.
      "@keyframes erpFlashHighlight {\n" +
      "  0% { box-shadow: 0 0 0 4px rgba(255, 165, 80, 0.85), 0 0 18px rgba(255, 165, 80, 0.55); outline-color: #ffa550; }\n" +
      "  100% { box-shadow: 0 0 0 0 rgba(255, 165, 80, 0.0), 0 0 0 rgba(255, 165, 80, 0.0); outline-color: transparent; }\n" +
      "}\n" +
      ".erp-design-modal .erp-design-flash-highlight,\n" +
      ".erp-design-flash-highlight {\n" +
      "  outline: 2px solid #ffa550;\n" +
      "  outline-offset: 2px;\n" +
      "  border-radius: 4px;\n" +
      "  animation: erpFlashHighlight 1500ms ease-out forwards;\n" +
      "}\n" +
      // Phase 38.4 Krok 14c+2 part A.1 (14.5.2026 odpoledne, Marti's
      // "drag jen ta komponenta uvnitr, ne cela karta"):
      // Scoped CSS pro inline preview komponenty v gallery cards.
      // Replace iframe sandbox (drag nepřechází přes iframe boundary)
      // → inline DOM s scoped reset (drag funguje, vizuálně sjednoceno).
      ".erp-gallery-preview-scope {\n" +
      "  display: flex; align-items: center; gap: 5px;\n" +
      "  font-family: system-ui, -apple-system, sans-serif;\n" +
      "  font-size: 12px; color: #cfd6df;\n" +
      "  pointer-events: auto;\n" +
      "}\n" +
      ".erp-gallery-preview-scope input,\n" +
      ".erp-gallery-preview-scope select,\n" +
      ".erp-gallery-preview-scope textarea,\n" +
      ".erp-gallery-preview-scope button {\n" +
      "  font-family: inherit; font-size: 12px;\n" +
      "  background: #1f2530; border: 1px solid #2a3340;\n" +
      "  color: #cfd6df; border-radius: 3px;\n" +
      "  padding: 3px 6px; max-width: 100%;\n" +
      "  caret-color: transparent;\n" +
      "}\n" +
      ".erp-gallery-preview-scope input[type=\"checkbox\"] {\n" +
      "  width: 14px; height: 14px;\n" +
      "}\n" +
      ".erp-gallery-preview-scope label {\n" +
      "  display: flex; align-items: center; gap: 5px;\n" +
      "}\n" +
      // Phase 38.4 Krok 14c+3.4 (14.5.2026 odpoledne, Marti's bug "Vetsina
      // komponent nejde drag. Neukaze se symbol ruky."):
      //   ROOT CAUSE: CSS selector "> [draggable=true]" je direct-child only.
      //   Pokud preview_html má wrapper (např. <label><input/></label> pro
      //   checkbox), querySelector najde deep <input> + nastaví draggable,
      //   ale CSS rule miss = žádný cursor:grab + možné drag init issues.
      //
      //   FIX:
      //     1. Drop ">" v selectoru — match any descendant draggable
      //     2. Drop user-select:none (defensive — někdy blokuje drag init)
      //     3. JS-side inline style.cursor = "grab" jako fallback
      ".erp-gallery-preview-scope [draggable=\"true\"] {\n" +
      "  cursor: grab; transition: border-color 0.15s, box-shadow 0.15s;\n" +
      "}\n" +
      ".erp-gallery-preview-scope [draggable=\"true\"]:hover {\n" +
      "  border-color: #3a8aa8 !important;\n" +
      "  box-shadow: 0 0 0 1px rgba(58,138,168,0.3);\n" +
      "}\n" +
      ".erp-gallery-preview-scope [draggable=\"true\"]:active {\n" +
      "  cursor: grabbing;\n" +
      "}\n" +
      // Phase 38.4 Krok 14c+2 part A.3 (14.5.2026, Marti's polish "komponenty
      // tady v preview"): hide spinner v number input (Marti's screenshot
      // ukázal vysoké šipky). webkit + firefox notation.
      ".erp-gallery-preview-scope input[type=\"number\"] {\n" +
      "  -moz-appearance: textfield;\n" +
      "}\n" +
      ".erp-gallery-preview-scope input[type=\"number\"]::-webkit-inner-spin-button,\n" +
      ".erp-gallery-preview-scope input[type=\"number\"]::-webkit-outer-spin-button {\n" +
      "  -webkit-appearance: none;\n" +
      "  margin: 0;\n" +
      "}\n" +
      // Date / datetime / time picker — hide native spinner / clear button.
      ".erp-gallery-preview-scope input[type=\"date\"]::-webkit-inner-spin-button,\n" +
      ".erp-gallery-preview-scope input[type=\"datetime-local\"]::-webkit-inner-spin-button,\n" +
      ".erp-gallery-preview-scope input[type=\"time\"]::-webkit-inner-spin-button {\n" +
      "  -webkit-appearance: none;\n" +
      "  display: none;\n" +
      "}\n" +
      ".erp-gallery-preview-scope input[type=\"date\"]::-webkit-calendar-picker-indicator,\n" +
      ".erp-gallery-preview-scope input[type=\"datetime-local\"]::-webkit-calendar-picker-indicator,\n" +
      ".erp-gallery-preview-scope input[type=\"time\"]::-webkit-calendar-picker-indicator {\n" +
      "  filter: invert(0.7);\n" +  // tonal s dark theme
      "  cursor: grab;\n" +
      "  opacity: 0.6;\n" +
      "}\n" +
      // Select multiple (Lookup Multi) — fix scrollbar + clean look,
      // pokud preview má <select multiple size=N>.
      ".erp-gallery-preview-scope select[multiple] {\n" +
      "  min-height: 24px; max-height: 24px;\n" +
      "  background-image: linear-gradient(to bottom, #1f2530, #1a1f26);\n" +
      "}\n" +
      ".erp-gallery-preview-scope select[multiple]::-webkit-scrollbar {\n" +
      "  width: 4px;\n" +
      "}\n" +
      // File input — clean look (input[type=file] je sotva preview-able,
      // hide button decoration, jen show placeholder).
      ".erp-gallery-preview-scope input[type=\"file\"] {\n" +
      "  font-size: 11px; padding: 2px 4px;\n" +
      "}\n" +
      ".erp-gallery-preview-scope input[type=\"file\"]::-webkit-file-upload-button {\n" +
      "  background: #2a3340; color: #cfd6df; border: none;\n" +
      "  border-radius: 2px; padding: 2px 6px; font-size: 10px;\n" +
      "  margin-right: 6px; cursor: grab;\n" +
      "}\n"
    );
    document.head.appendChild(style);
  })();

  // ────────────────────────────────────────────────────────────────────
  // Phase 38.4 Krok 14a-A1g #2 (12.5.2026 odpoledne): Dark confirm dialog
  // centered v page. Replace native browser confirm() (Marti's stížnost
  // na bílý native prompt v levém horním rohu).
  //
  // Vraci Promise<boolean> — true = OK, false = Zrušit/Esc.
  // ────────────────────────────────────────────────────────────────────

  // Phase 38.4 Krok 14d-D polish (14.5.2026 vecer, Marti's "Popup dialog
  // zmen na dark theme"): _promptDarkDialog — input variant of
  // _confirmDarkDialog. Replaces native window.prompt() (white system).
  //
  // opts: {
  //   title: string (header)
  //   message: string (body — instruction text above input)
  //   defaultValue: string (input initial value)
  //   placeholder: string (input placeholder)
  //   okLabel: string (default 'Uložit')
  //   cancelLabel: string (default 'Zrušit')
  // }
  // Returns: Promise<string | null> — string with user input, or null on cancel/Esc
  function _promptDarkDialog(opts) {
    opts = opts || {};
    const title = opts.title || "Zadej hodnotu";
    const message = opts.message || "";
    const defaultValue = opts.defaultValue != null ? String(opts.defaultValue) : "";
    const placeholder = opts.placeholder || "";
    const okLabel = opts.okLabel || "Uložit";
    const cancelLabel = opts.cancelLabel || "Zrušit";

    return new Promise((resolve) => {
      const ovr = document.createElement("div");
      ovr.className = "erp-prompt-overlay";
      ovr.style.cssText =
        "position:fixed;inset:0;background:rgba(0,0,0,0.7);z-index:9500;" +
        "display:flex;align-items:center;justify-content:center;";

      const dlg = document.createElement("div");
      dlg.className = "erp-prompt-dialog erp-design-modal";
      dlg.style.cssText =
        "background:#1a1f26;border:1px solid #2a3340;border-radius:6px;" +
        "width:480px;max-width:90vw;color:#cfd6df;font-size:13px;" +
        "box-shadow:0 16px 50px rgba(0,0,0,0.6);overflow:hidden;";

      // Header (analog _confirmDarkDialog s × close)
      const hdr = document.createElement("div");
      hdr.style.cssText =
        "padding:12px 16px;border-bottom:1px solid #2a3340;background:#141a20;" +
        "font-size:14px;font-weight:600;color:#e8eef5;" +
        "display:flex;align-items:center;justify-content:space-between;gap:12px;";
      const hdrTitle = document.createElement("span");
      hdrTitle.style.cssText = "flex:1 1 auto;";
      hdrTitle.textContent = title;
      hdr.appendChild(hdrTitle);
      const hdrClose = document.createElement("button");
      hdrClose.type = "button";
      hdrClose.textContent = "×";
      hdrClose.setAttribute("aria-label", "Zavřít");
      hdrClose.style.cssText =
        "background:transparent;border:none;color:#8a96a4;font-size:22px;" +
        "cursor:pointer;padding:0 6px;line-height:1;flex:0 0 auto;";
      hdr.appendChild(hdrClose);
      dlg.appendChild(hdr);

      // Body — message + input
      const body = document.createElement("div");
      body.style.cssText =
        "padding:16px;color:#cfd6df;font-size:13px;line-height:1.5;" +
        "display:flex;flex-direction:column;gap:10px;";
      if (message) {
        const msgEl = document.createElement("div");
        msgEl.style.cssText = "white-space:pre-wrap;color:#a8b4c2;";
        msgEl.textContent = message;
        body.appendChild(msgEl);
      }
      const input = document.createElement("input");
      input.type = "text";
      input.value = defaultValue;
      if (placeholder) input.placeholder = placeholder;
      input.style.cssText =
        "background:#0f141a;border:1px solid #3a4754;color:#e8eef5;" +
        "padding:8px 10px;border-radius:3px;font-size:13px;" +
        "font-family:inherit;outline:none;width:100%;box-sizing:border-box;";
      input.addEventListener("focus", () => {
        input.style.borderColor = "#3a8aa8";
        input.style.boxShadow = "0 0 0 1px rgba(58,138,168,0.3)";
      });
      input.addEventListener("blur", () => {
        input.style.borderColor = "#3a4754";
        input.style.boxShadow = "none";
      });
      body.appendChild(input);
      dlg.appendChild(body);

      // Footer — Storno + OK (OK vpravo, Marti's pattern z confirm dialog)
      const ftr = document.createElement("div");
      ftr.style.cssText =
        "padding:10px 16px;border-top:1px solid #2a3340;background:#141a20;" +
        "display:flex;justify-content:flex-end;gap:8px;";

      const cancelBtn = document.createElement("button");
      cancelBtn.type = "button";
      cancelBtn.textContent = cancelLabel;
      cancelBtn.style.cssText =
        "padding:6px 16px;background:#2a3340;border:1px solid #3a4754;" +
        "border-radius:3px;color:#cfd6df;cursor:pointer;font-size:12px;";
      ftr.appendChild(cancelBtn);

      const okBtn = document.createElement("button");
      okBtn.type = "button";
      okBtn.textContent = okLabel;
      okBtn.style.cssText =
        "padding:6px 16px;background:#3a5a8a;border:1px solid #4a7ba8;" +
        "border-radius:3px;color:#e8eef5;cursor:pointer;font-size:12px;" +
        "font-weight:600;";
      ftr.appendChild(okBtn);

      dlg.appendChild(ftr);
      ovr.appendChild(dlg);
      document.body.appendChild(ovr);

      function cleanup() {
        try { ovr.parentNode && ovr.parentNode.removeChild(ovr); } catch (e) {}
        document.removeEventListener("keydown", onKey, true);
      }
      function onKey(ev) {
        if (ev.key === "Escape") {
          ev.preventDefault();
          ev.stopPropagation();
          cleanup();
          resolve(null);
        } else if (ev.key === "Enter") {
          // Plus check že nemáme multiline input (textarea) — input single-line OK
          ev.preventDefault();
          ev.stopPropagation();
          cleanup();
          resolve(input.value);
        }
      }
      document.addEventListener("keydown", onKey, true);

      cancelBtn.addEventListener("click", () => { cleanup(); resolve(null); });
      hdrClose.addEventListener("click", () => { cleanup(); resolve(null); });
      okBtn.addEventListener("click", () => { cleanup(); resolve(input.value); });

      // Auto-focus input + select all default value
      setTimeout(() => {
        try {
          input.focus();
          input.select();
        } catch (e) {}
      }, 50);
    });
  }

  function _confirmDarkDialog(opts) {
    opts = opts || {};
    const title = opts.title || "Potvrdit";
    const message = opts.message || "";
    // A1t (12.5.2026 vecer doma): Marti's polish — defaults Ano/Ne misto
    // OK/Zrušit. Lidsky srozumitelnejsi. Plus order Ano-left/Ne-right
    // (Marti's "rad vzdy nejdrive Ano a pak Ne").
    // opts.cancel === null → 1-button mode (info dialog s jen OK)
    const okLabel = opts.ok || "Ano";
    const cancelLabel = opts.cancel === null ? null : (opts.cancel || "Ne");
    const showCancel = cancelLabel !== null;
    // Krok 14a-A1k #4: 3-button mode (Ano / Ne / Zrušit) pro close-with-dirty.
    // Resolve hodnoty: opts.threeButtons → "yes" | "no" | "cancel"
    //                  normal mode      → true | false
    const threeBtn = !!opts.threeButtons;
    const yesLabel = opts.yes || "Ano";
    const noLabel = opts.no || "Ne";

    return new Promise((resolve) => {
      const ovr = document.createElement("div");
      ovr.className = "erp-confirm-overlay";
      ovr.style.cssText = "position:fixed;inset:0;background:rgba(0,0,0,0.7);z-index:9500;display:flex;align-items:center;justify-content:center;";

      const dlg = document.createElement("div");
      dlg.className = "erp-confirm-dialog erp-design-modal";
      dlg.style.cssText = "background:#1a1f26;border:1px solid #2a3340;border-radius:6px;width:420px;max-width:90vw;color:#cfd6df;font-size:13px;box-shadow:0 16px 50px rgba(0,0,0,0.6);overflow:hidden;";

      const hdr = document.createElement("div");
      // Krok 14b+15 (14.5.2026 ranni, Marti's "pridej do hlavicky standardni
      // rusici x"): flex row — title vlevo, × close button vpravo.
      // Click × ma stejnou semantiku jako Esc: null (2-button) / "cancel"
      // (3-button) — "did nothing" path.
      hdr.style.cssText =
        "padding:12px 16px;border-bottom:1px solid #2a3340;background:#141a20;" +
        "font-size:14px;font-weight:600;color:#e8eef5;" +
        "display:flex;align-items:center;justify-content:space-between;gap:12px;";
      const hdrTitle = document.createElement("span");
      hdrTitle.style.cssText = "flex:1 1 auto;";
      hdrTitle.textContent = title;
      hdr.appendChild(hdrTitle);
      const hdrClose = document.createElement("button");
      hdrClose.type = "button";
      hdrClose.textContent = "×";
      hdrClose.setAttribute("aria-label", "Zavřít");
      hdrClose.style.cssText =
        "background:transparent;border:none;color:#8a96a4;font-size:22px;" +
        "cursor:pointer;padding:0 6px;line-height:1;flex:0 0 auto;";
      hdr.appendChild(hdrClose);
      dlg.appendChild(hdr);

      const body = document.createElement("div");
      body.style.cssText = "padding:16px;color:#cfd6df;font-size:13px;line-height:1.5;white-space:pre-wrap;";
      // Excel mode Faze 2-D polish (25.5.2026 rano, Marti's catch "v dialogu
      // se neukazuje tucne to cislo — konflikt s formatovanim"): caller
      // muze poslat HTML v message (<b>4</b>, <em>, atd.). Pred Faze 2-D
      // textContent escapoval. Pri jeho innerHTML render funguje tucne +
      // ostatni HTML tagy. Caller je parent-gated (DESIGN mode service),
      // XSS risk acceptable. Pro plain text bez HTML chova se identicky.
      body.innerHTML = message;
      dlg.appendChild(body);

      const ftr = document.createElement("div");
      ftr.style.cssText = "padding:10px 16px;border-top:1px solid #2a3340;background:#141a20;display:flex;justify-content:flex-end;gap:8px;";

      if (threeBtn) {
        // 3-button: Ano (save) | Ne (discard) | Zrušit (stay)
        const yesBtn = document.createElement("button");
        yesBtn.type = "button";
        yesBtn.textContent = yesLabel;
        yesBtn.style.cssText = "padding:6px 16px;background:#3a5a3a;border:1px solid #4a7a4a;border-radius:3px;color:#e8eef5;cursor:pointer;font-size:12px;font-weight:600;";
        const noBtn = document.createElement("button");
        noBtn.type = "button";
        noBtn.textContent = noLabel;
        noBtn.style.cssText = "padding:6px 16px;background:#5a3a3a;border:1px solid #7a4a4a;border-radius:3px;color:#e8eef5;cursor:pointer;font-size:12px;";
        const cancelBtn = document.createElement("button");
        cancelBtn.type = "button";
        cancelBtn.textContent = cancelLabel;
        cancelBtn.style.cssText = "padding:6px 16px;background:#2a3340;border:1px solid #3a4754;border-radius:3px;color:#cfd6df;cursor:pointer;font-size:12px;";
        // A1t: 3-button mode (dead code po A1t, ale konzistentni order
        // pro budouce pouziti) — Ano vlevo, Ne, Zrušit vpravo.
        ftr.appendChild(yesBtn);
        ftr.appendChild(noBtn);
        ftr.appendChild(cancelBtn);
        dlg.appendChild(ftr);
        ovr.appendChild(dlg);
        document.body.appendChild(ovr);
        function cleanup() {
          try { ovr.parentNode && ovr.parentNode.removeChild(ovr); } catch (e) {}
          // Krok 14b+15.1: useCapture=true musi byt v remove taky
          document.removeEventListener("keydown", onKey, true);
        }
        // Krok 14b+15.1: capture + stopPropagation (viz 2-button mode komentar)
        function onKey(ev) {
          if (ev.key === "Escape") {
            ev.preventDefault();
            ev.stopPropagation();
            cleanup();
            resolve("cancel");
          } else if (ev.key === "Enter") {
            ev.preventDefault();
            ev.stopPropagation();
            cleanup();
            resolve("yes");
          }
        }
        yesBtn.addEventListener("click", () => { cleanup(); resolve("yes"); });
        noBtn.addEventListener("click", () => { cleanup(); resolve("no"); });
        cancelBtn.addEventListener("click", () => { cleanup(); resolve("cancel"); });
        // Krok 14b+15: × close = stejna semantika jako Esc / Zrušit / klik
        // mimo dialog = "cancel" (no-op, keep parent modal otevreny).
        hdrClose.addEventListener("click", () => { cleanup(); resolve("cancel"); });
        ovr.addEventListener("click", (ev) => {
          if (ev.target === ovr) { cleanup(); resolve("cancel"); }
        });
        dlg.addEventListener("contextmenu", (ev) => ev.preventDefault());
        // Krok 14b+15.1: capture=true (3. arg) priority pred parent shell Esc
        document.addEventListener("keydown", onKey, true);
        setTimeout(() => yesBtn.focus(), 50);
        return;
      }

      // 2-button (default): Ano / Ne — nebo 1-button mode (info dialog, cancel: null)
      let cancelBtn = null;
      if (showCancel) {
        cancelBtn = document.createElement("button");
        cancelBtn.type = "button";
        cancelBtn.textContent = cancelLabel;
        cancelBtn.style.cssText = "padding:6px 16px;background:#2a3340;border:1px solid #3a4754;border-radius:3px;color:#cfd6df;cursor:pointer;font-size:12px;";
      }

      const okBtn = document.createElement("button");
      okBtn.type = "button";
      okBtn.textContent = okLabel;
      okBtn.style.cssText = "padding:6px 16px;background:#5a3a3a;border:1px solid #7a4a4a;border-radius:3px;color:#e8eef5;cursor:pointer;font-size:12px;font-weight:600;";

      // A1t order: Ano (left/primary) → Ne (right/secondary)
      ftr.appendChild(okBtn);
      if (cancelBtn) ftr.appendChild(cancelBtn);
      dlg.appendChild(ftr);
      ovr.appendChild(dlg);
      document.body.appendChild(ovr);

      function cleanup() {
        try { ovr.parentNode && ovr.parentNode.removeChild(ovr); } catch (e) {}
        // Krok 14b+15.1 (14.5.2026 rano, Marti's "reakce na Esc"):
        // useCapture=true musi byt v removeEventListener taky aby
        // listener byl spravne unregistered.
        document.removeEventListener("keydown", onKey, true);
      }
      // A1t safety: Esc / click outside = null (keep modal, "did nothing").
      // Explicit Ano (true) / Ne (false) jsou jediné destruktivni cesty.
      // Caller pak rozlisuje: true = positive action, false = negative
      // action, null = no-op (nepokracuj).
      //
      // Krok 14b+15.1 (14.5.2026 rano, Marti's "reakce na ESC"):
      // Pridana stopPropagation + capture phase. Bez nich Esc dropal
      // do parent _buildModalShell._onKey listeneru, ktery zavolal
      // parent close() -> _beforeCloseHandler -> NOVY confirm dialog
      // (loop). Capture phase + stopPropagation zaruci ze Esc je
      // zachycen JEN confirm dialogem, parent neuvidí.
      function onKey(ev) {
        if (ev.key === "Escape") {
          ev.preventDefault();
          ev.stopPropagation();
          cleanup();
          resolve(null);
        } else if (ev.key === "Enter") {
          ev.preventDefault();
          ev.stopPropagation();
          cleanup();
          resolve(true);
        }
      }
      if (cancelBtn) cancelBtn.addEventListener("click", () => { cleanup(); resolve(false); });
      okBtn.addEventListener("click", () => { cleanup(); resolve(true); });
      // Krok 14b+15: × close = stejna semantika jako Esc / klik mimo
      // dialog = null (no-op, "did nothing", keep parent modal otevreny).
      hdrClose.addEventListener("click", () => { cleanup(); resolve(null); });
      ovr.addEventListener("click", (ev) => {
        if (ev.target === ovr) { cleanup(); resolve(null); }
      });
      dlg.addEventListener("contextmenu", (ev) => ev.preventDefault());
      // Krok 14b+15.1: capture=true (3. arg) aby confirm dialog zachyti
      // Esc PRED parent _buildModalShell listener (registered earlier,
      // bubble phase). Plus event.stopPropagation v handleru.
      document.addEventListener("keydown", onKey, true);
      setTimeout(() => okBtn.focus(), 50);
    });
  }

  // ────────────────────────────────────────────────────────────────────
  // Shared modal skeleton (reuse modal CSS z erp-modal patternu)
  // ────────────────────────────────────────────────────────────────────

  function _buildModalShell(opts) {
    // Returns { overlay, dialog, header, body, footer, close() }
    //
    // Phase 38.4 Krok 14c+2 part A.2 (14.5.2026 odpoledne, Marti's
    // "musi se chovat jako normalni samostatne okno, ne modal"):
    //   opts.floating = true → drop overlay backdrop (žádné zatemnění),
    //     dialog je position:fixed jako floating panel. Lze proklikat
    //     přes ERP form pod tím. Drag-drop přes z-index hraniční vrstvu
    //     funguje (žádný overlay nezachycuje pointer-events).
    //   opts.noBackdropClose = true → klik mimo dialog NEZAVŘE (jen × button).
    //   opts.startPos = { top: '80px', left: '80px' } — initial pozice
    //     (jinak default = top-left rohu viewport pro floating).
    //
    // Drop-fix doctrine: HTML5 drag-drop přes dimming overlay je blokován,
    // protože overlay (z-index 9000) chytá dragover events a form panel
    // pod ním nedostane drop target chance. Floating panel bez overlay
    // řeší.
    const isFloating = opts.floating === true;

    const overlay = document.createElement("div");
    overlay.className = "erp-modal-overlay" + (isFloating ? " erp-modal-overlay--floating" : "");
    if (isFloating) {
      // Žádný backdrop, žádný dimming, žádné centrování.
      // overlay je jen "anchor" pro dialog v document.body — nezachycuje
      // pointer-events (lze prokliknout ERP form pod gallery).
      overlay.style.cssText =
        "position:fixed;inset:0;pointer-events:none;z-index:9000;";
    } else {
      overlay.style.cssText =
        "position:fixed;inset:0;background:rgba(0,0,0,0.6);z-index:9000;" +
        "display:flex;align-items:center;justify-content:center;";
    }

    const dialog = document.createElement("div");
    dialog.className = "erp-modal-dialog erp-design-modal" +
                       (isFloating ? " erp-modal-dialog--floating" : "");
    // Pro floating mode: position:fixed + explicit top/left + pointer-events:auto
    // (dialog se re-aktivuje pro interakci, ale overlay zustane proklikateln).
    // Max-height 85vh (ne 90), aby user videl ze panel ma okraje + lze drag.
    const floatingStartTop = (opts.startPos && opts.startPos.top) || "80px";
    const floatingStartLeft = (opts.startPos && opts.startPos.left) || "80px";
    const positioning = isFloating
      ? "position:fixed;top:" + floatingStartTop + ";left:" + floatingStartLeft +
        ";pointer-events:auto;"
      : "";
    dialog.style.cssText = positioning +
      "background:#1a1f26;border:1px solid #2a3340;border-radius:6px;" +
      "width:" + (opts.width || "920px") + ";max-width:95vw;max-height:" +
      (isFloating ? "85vh" : "90vh") +
      ";display:flex;flex-direction:column;color:#cfd6df;font-size:13px;" +
      "box-shadow:0 12px 40px rgba(0,0,0,0.5);resize:both;overflow:hidden;";

    const header = document.createElement("div");
    header.className = "erp-modal-header";
    header.style.cssText = "padding:10px 16px;border-bottom:1px solid #2a3340;display:flex;align-items:center;justify-content:space-between;background:#141a20;user-select:none;";
    const title = document.createElement("div");
    title.className = "erp-modal-title";
    title.style.cssText = "font-size:14px;font-weight:600;color:#e8eef5;flex:1 1 auto;";
    title.textContent = opts.title || "Design";
    header.appendChild(title);

    // Krok 14a-A1k #1 (12.5.2026): header right container — toggle vpravo
    // s gapem od close button.
    const rightActions = document.createElement("div");
    rightActions.className = "erp-modal-header-actions";
    rightActions.style.cssText = "display:flex;align-items:center;gap:12px;flex:0 0 auto;";

    const sysToggle = document.createElement("button");
    sysToggle.type = "button";
    sysToggle.className = "erp-design-systoggle";
    function _renderSysToggleLabel() {
      const on = window._erpDesignShowSystemNames === true;
      // Krok 14b+17 (14.5.2026 rano, Marti's polish):
      //   1. Velka pismena na zacatku — "Uživatel" / "System"
      //   2. Button visible JEN v DESIGN mode (window._erpDesignMode === true)
      sysToggle.textContent = on ? "👁️ System" : "👁️ Uživatel";
      sysToggle.title = on
        ? "Zobrazují se system fieldKey. Klikni pro přepnutí na uživatelské názvy."
        : "Zobrazují se uživatelské názvy. Klikni pro přepnutí na system fieldKey (debug).";
      // Visibility gate — pouze v DESIGN mode (Marti's "tlacitko se ma
      // zobrazovat pouze v design mode cele aplikace")
      const designOn = window._erpDesignMode === true;
      const displayStyle = designOn ? "" : "display:none;";
      sysToggle.style.cssText = "background:" + (on ? "#3a4a5a" : "#1f2530") +
        ";border:1px solid " + (on ? "#5a6877" : "#2a3340") +
        ";color:#cfd6df;padding:4px 10px;border-radius:3px;cursor:pointer;font-size:11px;" +
        displayStyle;
    }
    // Krok 14a-A1l #1: sync globalni sysToggle state na body[data-...]
    // — pouziva se v CSS rules pro toggle user/system description memo.
    function _syncSysAttrToBody() {
      try {
        document.body.dataset.designSystemNames =
          window._erpDesignShowSystemNames === true ? "1" : "0";
      } catch (e) { /* SSR / no body */ }
    }
    _renderSysToggleLabel();
    _syncSysAttrToBody();
    sysToggle.addEventListener("click", () => {
      window._erpDesignShowSystemNames = !window._erpDesignShowSystemNames;
      _renderSysToggleLabel();
      _syncSysAttrToBody();
      _reapplyAllOverridesInDOM();
    });
    rightActions.appendChild(sysToggle);

    // Phase 38.4 Krok 14a-A1m #2 (12.5.2026 odpoledne): 📖 ikona otevre
    // SAMOSTATNY popup s jednim velkym memo (CLAUDE.md per core). Pres
    // sysToggle se prepina mezi user a system popis. Nepouziva inline
    // sekci ve form — popis je v krabicce per entity.
    const descToggle = document.createElement("button");
    descToggle.type = "button";
    descToggle.className = "erp-design-desctoggle";
    // Krok 14b+18 (14.5.2026 rano, Marti's "ikonka kniha se tvari jako
    // bily obdelnicek"): 📖 → 📘 (modra kniha, colored emoji glyph).
    // Krok 14b+18.1: Marti's polish "nech ji bez toho textu jen samotnou
    // ikonku" — drop "Popis" label, jen 📘 emoji. Tooltip drzi affordance.
    descToggle.textContent = "📘";
    descToggle.title = "Otevřít popis core (systémový + uživatelský — jako CLAUDE.md pro tohle jádro).";
    descToggle.style.cssText =
      "background:#1f2530;border:1px solid #2a3340;color:#cfd6df;" +
      "padding:4px 8px;border-radius:3px;cursor:pointer;font-size:13px;" +
      "line-height:1;";
    descToggle.addEventListener("click", () => {
      if (typeof opts.onShowDescriptions === "function") {
        try { opts.onShowDescriptions(); }
        catch (e) { console.error("onShowDescriptions failed:", e); }
      } else {
        console.warn("📘 clicked but form did not register onShowDescriptions handler");
      }
    });
    // Krok 14a-A1m #2: v popupu (recursion) nepotrebujeme dalsi 📖 ikonu.
    if (opts.hideDescToggle !== true) {
      rightActions.appendChild(descToggle);
    }

    const closeBtn = document.createElement("button");
    closeBtn.type = "button";
    closeBtn.textContent = "×";
    closeBtn.style.cssText = "background:transparent;border:none;color:#8a96a4;font-size:22px;cursor:pointer;padding:0 6px;line-height:1;";
    closeBtn.setAttribute("aria-label", "Zavrit");
    rightActions.appendChild(closeBtn);
    header.appendChild(rightActions);

    // Phase 38.4 Krok 14a-A1m #4 (12.5.2026 odpoledne): body flex:1 1 auto
    // + min-height:0 → footer vždy viditelný i při zmenšení okna. Footer
    // flex:0 0 auto = vždy rendered na bottom flex columnu. Body scrolluje
    // když content > available space. Žádný margin-top:auto na footer —
    // body fills empty space (dialog bg = body bg = invisible).
    const body = document.createElement("div");
    body.className = "erp-modal-body";
    body.style.cssText = "padding:12px 16px;overflow-y:auto;overflow-x:hidden;flex:1 1 auto;min-height:0;";

    const footer = document.createElement("div");
    footer.className = "erp-modal-footer";
    footer.style.cssText = "padding:10px 16px;border-top:1px solid #2a3340;display:flex;align-items:center;justify-content:flex-end;gap:8px;background:#141a20;flex:0 0 auto;";

    dialog.appendChild(header);
    dialog.appendChild(body);
    dialog.appendChild(footer);
    overlay.appendChild(dialog);

    function _doClose() {
      try { overlay.parentNode && overlay.parentNode.removeChild(overlay); } catch (e) {}
      document.removeEventListener("keydown", _onKey);
      _removeDragListeners();
    }
    // Krok 14a-A1k #4 (12.5.2026): requestClose ptá se attached
    // beforeClose callback (form třídy) — pokud dirty, 3-button confirm.
    async function close() {
      if (typeof opts.beforeClose === "function") {
        try {
          const decision = await opts.beforeClose();
          if (decision === "cancel") return;
          // "save" / "close" / undefined → close pokračuje (save side řeší callback)
        } catch (e) {
          console.warn("beforeClose handler failed:", e);
          // fallback: close anyway
        }
      }
      _doClose();
      // A1r (12.5.2026): notify caller (form class) ze close je hotovy
      // — pro cleanup dirty tracking v global Set.
      if (typeof opts.onClose === "function") {
        try { opts.onClose(); } catch (e) { console.warn("onClose handler failed:", e); }
      }
    }
    function _onKey(ev) {
      if (ev.key === "Escape") close();
    }
    closeBtn.addEventListener("click", close);
    // Krok 14a-A1k #2: click mimo modal NEzavírá (Marti's polish — popup
    // musí být explicit). Jen × button / Esc / footer Zavřít.
    document.addEventListener("keydown", _onKey);
    // Phase 38.4 Krok 14a-A1f: disable nativni context menu v modal dialog
    dialog.addEventListener("contextmenu", (ev) => ev.preventDefault());

    // Krok 14a-A1k #3 (12.5.2026): movable popup — drag na header.
    // Initial: dialog je centered via flex layout. Po prvním drag přepneme
    // na manual positioning (position:fixed + computed left/top).
    let _dragState = null;
    function _onHeaderMouseDown(ev) {
      // Ne dragujeme pokud klik na buttons (sysToggle, closeBtn) — preserve native click
      if (ev.target.closest("button")) return;
      if (ev.button !== 0) return;  // jen left mouse
      const rect = dialog.getBoundingClientRect();
      // Switch overlay z flex-centering na manual placement
      overlay.style.alignItems = "flex-start";
      overlay.style.justifyContent = "flex-start";
      dialog.style.position = "absolute";
      dialog.style.left = rect.left + "px";
      dialog.style.top = rect.top + "px";
      dialog.style.margin = "0";
      _dragState = {
        startX: ev.clientX,
        startY: ev.clientY,
        startLeft: rect.left,
        startTop: rect.top,
      };
      document.addEventListener("mousemove", _onDragMove);
      document.addEventListener("mouseup", _onDragEnd);
      ev.preventDefault();
    }
    function _onDragMove(ev) {
      if (!_dragState) return;
      const dx = ev.clientX - _dragState.startX;
      const dy = ev.clientY - _dragState.startY;
      const newLeft = Math.max(0, Math.min(window.innerWidth - 100, _dragState.startLeft + dx));
      const newTop = Math.max(0, Math.min(window.innerHeight - 60, _dragState.startTop + dy));
      dialog.style.left = newLeft + "px";
      dialog.style.top = newTop + "px";
    }
    function _onDragEnd() {
      _dragState = null;
      document.removeEventListener("mousemove", _onDragMove);
      document.removeEventListener("mouseup", _onDragEnd);
    }
    function _removeDragListeners() {
      document.removeEventListener("mousemove", _onDragMove);
      document.removeEventListener("mouseup", _onDragEnd);
    }
    header.style.cursor = "move";
    header.addEventListener("mousedown", _onHeaderMouseDown);

    return { overlay, dialog, header, body, footer, title, close };
  }

  // Phase 38.4 Krok 14a-A1m #2 (12.5.2026 odpoledne): popup pro description
  // memo (system + user). Otevre se z 📖 ikony v hlavnim formu. Obdoba
  // CLAUDE.md pro jednu konkretni core entitu — velky memo pres cele okno,
  // toggle mezi system a user popisem pres globalni sysToggle.
  //
  // opts:
  //   - entityLabel: human-readable nazev entity (zobrazi se v title)
  //   - entityKind: "core" nebo "menu_node" (urcuje fieldKey prefix)
  //   - descUser: aktualni text user popisu
  //   - descSystem: aktualni text system popisu
  //   - onDirty: callback (fieldKey, isDirty) — kompatibilni s form's _onDirty
  function _buildDescriptionsPopup(opts) {
    opts = opts || {};
    const entityKind = opts.entityKind === "menu_node" ? "mn" : "core";
    const labelStr = opts.entityLabel ? String(opts.entityLabel) : "(bez labelu)";
    const titleText = "📘 Popis: " + labelStr;

    // Phase 38.4 Krok 14b+22 (14.5.2026 odpoledne, Marti's "schovej tu
    // sekci pro vyvojare pokud neni globalni DESIGN mode"):
    // System (developer) memo viditelne JEN v DESIGN mode. V PROD rezimu
    // zobrazi se full-width jen user memo — bezny uzivatel nevidi
    // developer popis (analog Krok 14b+17 sysToggle visibility gate).
    //
    // Backend save endpoint chodi pro oboji popisy bez ohledu na UI gate
    // (description_system zustane preserved at field hidden, ale opts.descSystem
    // se neulozi pres tento popup v PROD mode — jen description_user).
    const designModeOn = window._erpDesignMode === true;

    // Popup nepouziva beforeClose handler — dirty tracking je v hlavnim
    // formu (memo nas vola onDirty primo). Close = vzdy povoleno, data
    // zustanou v form's state.
    const shell = _buildModalShell({
      title: titleText,
      width: "1100px",
      hideDescToggle: true,
    });
    document.body.appendChild(shell.overlay);

    // Body — vertikalni flex, 2 memos vedle sebe via CSS toggle (DESIGN),
    // nebo jediny user memo full-width (PROD). Full-height (60vh).
    shell.body.style.padding = "0";
    shell.body.style.display = "flex";
    shell.body.style.flexDirection = "column";

    const info = document.createElement("div");
    info.style.cssText = "padding:10px 16px;background:#141a20;border-bottom:1px solid #2a3340;color:#8a96a4;font-size:11px;line-height:1.5;";
    if (designModeOn) {
      info.innerHTML =
        "<span class=\"section-title-user\">👁️ Uživatelský popis — k čemu jádro slouží, jak s ním pracovat. Markdown.</span>" +
        "<span class=\"section-title-system\">🔧 Systémový popis (vývojáři) — implementace, data zdroje, edge cases, debug. Markdown.</span>" +
        "<br><span style=\"font-size:10px;opacity:0.7;\">Přepnout pomocí ikony 👁️ Uživatel / System v hlavičce. Je to jako CLAUDE.md pro tohle jádro.</span>";
    } else {
      info.innerHTML =
        "👁️ Popis — k čemu jádro slouží, jak s ním pracovat. Markdown.";
    }
    shell.body.appendChild(info);

    // Memo container — fills body, 60vh height
    const memoContainer = document.createElement("div");
    memoContainer.style.cssText = "padding:12px 16px;flex:1 1 auto;display:flex;flex-direction:column;min-height:0;";
    shell.body.appendChild(memoContainer);

    // User memo. V PROD nepridavame `desc-memo-user` class — body's
    // data-design-system-names="1" leftover by jinak skryl user memo
    // pres CSS pravidlo (line ~482). V PROD je sysToggle nedostupny, ale
    // body attribute muze byt persistent leftover z drivejsi DESIGN session.
    const userMemoLabel = designModeOn ? "Popis (uživatel)" : "Popis";
    const userWrap = _memo(userMemoLabel, opts.descUser, {
      fieldKey: entityKind + ".description_user",
      onDirty: opts.onDirty,
      rows: 22,
      maxRows: 40,
    });
    if (designModeOn) {
      userWrap.classList.add("desc-memo-user");
    }
    userWrap.classList.add("design-desc-popup-memo");
    userWrap.style.flex = "1 1 auto";
    userWrap.style.minHeight = "0";
    userWrap.style.display = "flex";
    userWrap.style.flexDirection = "column";
    memoContainer.appendChild(userWrap);

    // System memo — jen v DESIGN mode. V PROD vubec nerendrujem (Marti's
    // pozadavek "schovej tu sekci pro vyvojare"). sysWrap zustava null
    // a saveBtn handler to detekuje (description_system se nepošle).
    let sysWrap = null;
    if (designModeOn) {
      sysWrap = _memo("Popis (systém — vývojáři)", opts.descSystem, {
        fieldKey: entityKind + ".description_system",
        onDirty: opts.onDirty,
        rows: 22,
        maxRows: 40,
      });
      sysWrap.classList.add("desc-memo-system");
      sysWrap.classList.add("design-desc-popup-memo");
      sysWrap.style.flex = "1 1 auto";
      sysWrap.style.minHeight = "0";
      sysWrap.style.display = "flex";
      sysWrap.style.flexDirection = "column";
      memoContainer.appendChild(sysWrap);
    }

    // Stretch memo textareas to fill memoContainer
    function _stretchMemo(wrap) {
      if (!wrap) return;
      const ta = wrap.querySelector("textarea");
      if (ta) {
        ta.style.flex = "1 1 auto";
        ta.style.minHeight = "300px";
        ta.style.height = "60vh";
        ta.style.resize = "vertical";
      }
    }
    _stretchMemo(userWrap);
    _stretchMemo(sysWrap);

    // Phase 38.4 Krok 14b+21 (14.5.2026 rano, Marti's "📘 Popis save"):
    // 💾 Uložit button v popup footer — PATCH backend, save oba popisy
    // (user + system), update parent spec consistency, toast.
    //
    // Backend endpoints:
    //   - PATCH /api/v1/erp/design/fw-core/update/{id}      (entityKind='core')
    //   - PATCH /api/v1/erp/design/fw-menu-node/update/{id} (entityKind='menu_node')
    // Whitelist: label, description_user, description_system
    const saveBtn = document.createElement("button");
    saveBtn.type = "button";
    saveBtn.textContent = "💾 Uložit";
    saveBtn.style.cssText =
      "padding:6px 16px;background:#1f4858;border:1px solid #3a8aa8;" +
      "color:#7ed4e8;cursor:pointer;font-size:12px;font-weight:600;border-radius:3px;";
    // Visible jen pokud entityId set (volajici musi predat)
    if (!opts.entityId) {
      saveBtn.style.display = "none";
    }
    saveBtn.addEventListener("click", async () => {
      const entityId = opts.entityId;
      if (!entityId) {
        _showToast("Entity ID chybi — popup nezná koho uložit", "error");
        return;
      }
      // Read current values z memo textareas. sysTextarea muze byt null
      // (PROD mode bez DESIGN — system memo se vubec nerendruje, popup
      // posila jen description_user; system value zustane preserved at
      // field na backendu).
      const userTextarea = userWrap.querySelector("textarea");
      const sysTextarea = sysWrap ? sysWrap.querySelector("textarea") : null;
      const newUser = userTextarea ? userTextarea.value : "";
      const newSys = sysTextarea ? sysTextarea.value : null;
      // 3-segment route podle entityKind
      const routeSegment = opts.entityKind === "menu_node" ? "fw-menu-node" : "fw-core";
      const url = "/api/v1/erp/design/" + routeSegment + "/update/" +
                  encodeURIComponent(entityId);
      saveBtn.disabled = true;
      const origHtml = saveBtn.innerHTML;
      saveBtn.innerHTML = "💾 Ukládám…";
      try {
        // V PROD posilame jen description_user (system se nedotyka).
        // V DESIGN posilame oboji (backend whitelist akceptuje obojí).
        const payload = { description_user: newUser };
        if (sysTextarea) {
          payload.description_system = newSys;
        }
        const r = await fetch(url, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify(payload),
        });
        if (!r.ok) {
          const errBody = await r.json().catch(() => ({}));
          throw new Error("HTTP " + r.status + ": " + (errBody.error || r.statusText));
        }
        _showToast("Popis uložen", "success");
        // Update parent form's local spec consistency (no reload nutny).
        // V PROD posilame jen description_user; description_system zustane
        // pri stare hodnote — opts.onSaved dostane oba klice jen pokud
        // jsme oboji menili.
        if (typeof opts.onSaved === "function") {
          try {
            const savedPayload = { description_user: newUser };
            if (sysTextarea) {
              savedPayload.description_system = newSys;
            }
            opts.onSaved(savedPayload);
          } catch (e) {
            console.error("[DescriptionsPopup] onSaved callback failed:", e);
          }
        }
        shell.close();
      } catch (e) {
        console.error("[DescriptionsPopup] save failed:", e);
        _showToast("Uložení popisu selhalo: " + (e.message || e), "error", 3500);
        saveBtn.disabled = false;
        saveBtn.innerHTML = origHtml;
      }
    });
    shell.footer.appendChild(saveBtn);

    // Footer — Zavrit (Save flow Krok 14b)
    const closeBtn = document.createElement("button");
    closeBtn.type = "button";
    closeBtn.textContent = "Zavřít";
    closeBtn.style.cssText = "padding:6px 16px;background:#2a3340;border:1px solid #3a4754;border-radius:3px;color:#cfd6df;cursor:pointer;font-size:12px;";
    closeBtn.addEventListener("click", () => shell.close());
    shell.footer.appendChild(closeBtn);

    return shell;
  }

  function _field(label, value, opts) {
    // Phase 38.4 Krok 14a-A1b (12.5.2026 dop.): UI Kit dogfooding + edit mode.
    // Default: editable (disabled=false). Save flow chybi (Krok 14b TODO) —
    // user-typed zmeny zustavaji v inputu, pri zavreni modalu se ztrati.
    //
    // Pouzij `opts.readonly = true` pro system metadata fields (ID,
    // created_at, updated_at, parent_code computed, framework_jadro_id atd.).
    // `opts.mono = true` pro monospace font (id, code, FK fields).
    opts = opts || {};
    const isReadonly = !!opts.readonly;
    const displayValue = (value == null || value === "") ? "" : String(value);
    // Krok 14a-A1h: label override + hint resolution (Marti's polish #2 + #3)
    const resolvedLabel = _resolveLabel(opts.fieldKey, label);
    const resolvedHint = _resolveHint(opts.fieldKey);

    // UI Kit cesta — pokud ErpInput zaregistrovan
    if (typeof global.ErpInput === "function") {
      const wrap = document.createElement("div");
      wrap.className = "erp-field erp-field-design" + (isReadonly ? " erp-field-readonly-uikit" : " erp-field-editable-uikit");
      wrap.style.cssText = "display:flex;flex-direction:column;gap:3px;";
      // Hint na wrap (browser native title, ~1s delay)
      if (resolvedHint) wrap.dataset.designHint = resolvedHint;
      const inp = new global.ErpInput(wrap, {
        type: "text",
        label: resolvedLabel,
        value: displayValue,
        disabled: isReadonly,
        placeholder: "—",
        // Phase 38.4 Krok 14a-A1d (12.5.2026): dirty tracking — Marti's
        // pozadavek "zmenene hodnoty decentne probarvit + Save tlacitko
        // jen kdyz neco zmeneno". Listener compare current vs initial.
        onChange: (display) => {
          if (isReadonly) return;
          const isDirty = String(display || "") !== displayValue;
          if (inp.input) {
            if (isDirty) {
              inp.input.style.borderLeft = "3px solid #d4b88a";
              inp.input.style.background = "#1f1810";
            } else {
              inp.input.style.borderLeft = "";
              inp.input.style.background = "";
            }
          }
          if (typeof opts.onDirty === "function" && opts.fieldKey) {
            opts.onDirty(opts.fieldKey, isDirty);
          }
        },
      });
      // Mono variant
      if (opts.mono && inp.input) {
        inp.input.style.fontFamily = "ui-monospace,Consolas,monospace";
        inp.input.style.fontSize = "11px";
      }
      // Phase 38.4 Krok 14f-M (14.5.2026 vecer, Marti's "max_length /
      // min_length parametrizace"): aply HTML5 maxlength + minlength
      // attributes na input. Browser native validation pri user typing.
      if (inp.input) {
        if (opts.maxLength != null && opts.maxLength > 0) {
          inp.input.maxLength = parseInt(opts.maxLength, 10);
        }
        if (opts.minLength != null && opts.minLength > 0) {
          inp.input.minLength = parseInt(opts.minLength, 10);
        }
        // Phase 38.4 Krok 14f-M: placeholder override z layout
        if (opts.placeholder) {
          inp.input.placeholder = opts.placeholder;
        }
        // Phase 38.4 Krok 14f-M: required attribute (browser native validation)
        if (opts.required) {
          inp.input.required = true;
        }
      }
      if (!displayValue && inp.input && !opts.placeholder) {
        inp.input.placeholder = "—";
      }
      // Phase 38.4 Krok 14a-A1c: readonly visual zvyrazneni
      // Krok 14a-A1p (12.5.2026 vecer, druhy pokus): Marti's polish —
      // accent border (3px solid #5a6877) zrusen u RO uplne. Patri JEN
      // na dirty fields (amber #d4b88a, line ~782). RO se odlisuje
      // tichym pattern: background + color + cursor + 🔒 badge.
      // A1f mel uz to delat ale jen vypnul rohy — accent border tam
      // zustal. Ted ho dropnem cely.
      if (isReadonly && inp.input) {
        inp.input.style.background = "#1a2028";
        inp.input.style.color = "#9ba8b8";
        inp.input.style.opacity = "1";
        // Phase 38.4 Krok 14c+3.5 (14.5.2026 odpoledne, Marti's polish
        // "Mela by se chovat mys standardne, jako kdyz komponenta neni RO"):
        // drop "not-allowed" cursor — Marti chce default arrow,
        // ne preškrtnuté kolečko. RO state je visualně signalizovaný
        // přes 🔒 badge na labelu + tmavší pozadí, cursor není nutný.
        inp.input.style.cursor = "default";
        const labelEl = wrap.querySelector(".erp-input-label");
        if (labelEl && !labelEl.dataset.lockBadge) {
          labelEl.dataset.lockBadge = "1";
          labelEl.insertAdjacentHTML(
            "beforeend",
            ' <span data-lock-badge="1" style="color:#8a96a4;font-size:10px;margin-left:4px;" title="Read-only">🔒</span>'
          );
        }
      }
      // Krok 14a-A1f #4: attach instance + origVal pro _revertAll()
      wrap._inst = inp;
      wrap._origVal = displayValue;
      wrap._fieldKey = opts.fieldKey || null;
      wrap._kind = "field";
      // Krok 14a-A1j #1: ulozit puvodni hardcoded label pro revert fallback
      wrap.dataset.designOrigLabel = label || "";
      // Krok 14a-A1n #2: initial color apply (z localStorage overrides)
      _applyInitialColor(wrap, opts.fieldKey);
      // Krok 14a-A1i #2: right-click handle na label pro inline override edit
      if (opts.fieldKey) {
        const labelEl = wrap.querySelector(".erp-input-label");
        if (labelEl) {
          labelEl.setAttribute("data-design-fieldkey", opts.fieldKey);
          labelEl.style.cursor = "context-menu";
        }
      }
      return wrap;
    }

    // Fallback raw divs (pokud ErpInput.js nezaregistrován) — vzdy "ne-editable"
    // protoze raw div neumi typing. ErpInput musi byt nactenej (B+6.2).
    const wrap = document.createElement("div");
    wrap.className = "erp-field erp-field-fallback";
    wrap.style.cssText = "display:flex;flex-direction:column;gap:3px;";
    const lab = document.createElement("label");
    lab.textContent = label;
    lab.style.cssText = "font-size:11px;color:#8a96a4;font-weight:500;";
    wrap.appendChild(lab);
    const val = document.createElement("div");
    val.className = "erp-readonly-value";
    val.style.cssText = "padding:5px 8px;background:#0f141a;border:1px solid #2a3340;border-radius:3px;min-height:22px;color:#cfd6df;font-family:" + (opts.mono ? "ui-monospace,Consolas,monospace" : "inherit") + ";font-size:" + (opts.mono ? "11px" : "12px") + ";word-break:break-all;";
    if (!displayValue) {
      val.textContent = "—";
      val.style.color = "#5d6975";
    } else {
      val.textContent = displayValue;
    }
    wrap.appendChild(val);
    return wrap;
  }

  // Backward-compat alias (stara nazev pred Krok 14a-A1b refactor)
  const _readonlyInput = _field;

  // ────────────────────────────────────────────────────────────────────
  // _memo — multi-line textarea pro description / poznamky
  // Phase 38.4 Krok 14a-A1e (12.5.2026 odpoledne): Marti's polish #b —
  // description fields jsou victs víceradkové, single-line ErpInput byl tesny.
  // ────────────────────────────────────────────────────────────────────

  function _memo(label, value, opts) {
    opts = opts || {};
    const isReadonly = !!opts.readonly;
    const displayValue = (value == null || value === "") ? "" : String(value);
    // Krok 14a-A1h: label + hint override
    const resolvedLabel = _resolveLabel(opts.fieldKey, label);
    const resolvedHint = _resolveHint(opts.fieldKey);

    if (typeof global.ErpMemo === "function") {
      const wrap = document.createElement("div");
      wrap.className = "erp-field erp-field-design erp-field-memo" +
        (isReadonly ? " erp-field-readonly-memo" : "");
      // Span full width — description je dlouhy text, neni vhodne v auto-fit grid 220px
      wrap.style.cssText = "display:flex;flex-direction:column;gap:3px;grid-column:1/-1;";
      if (resolvedHint) wrap.dataset.designHint = resolvedHint;
      const memo = new global.ErpMemo(wrap, {
        label: resolvedLabel,
        value: displayValue,
        rows: opts.rows || 3,
        maxRows: opts.maxRows || 8,
        disabled: isReadonly,
        placeholder: "—",
        onChange: (val) => {
          if (isReadonly) return;
          const isDirty = String(val || "") !== displayValue;
          if (memo.textarea) {
            if (isDirty) {
              memo.textarea.style.borderLeft = "3px solid #d4b88a";
              memo.textarea.style.background = "#1f1810";
            } else {
              memo.textarea.style.borderLeft = "";
              memo.textarea.style.background = "";
            }
          }
          if (typeof opts.onDirty === "function" && opts.fieldKey) {
            opts.onDirty(opts.fieldKey, isDirty);
          }
        },
      });
      // Readonly vizualni boost (analog _field)
      // Krok 14a-A1p (12.5.2026 vecer): accent border zrusen u RO,
      // viz _field komentar (RO = tichy lock pattern).
      if (isReadonly && memo.textarea) {
        memo.textarea.style.background = "#1a2028";
        memo.textarea.style.color = "#9ba8b8";
        memo.textarea.style.opacity = "1";
        // Krok 14c+3.5: default cursor pro RO (Marti's "standardne, jako
        // kdyz komponenta neni RO"). 🔒 badge + tmavší bg signalizují stav.
        memo.textarea.style.cursor = "default";
        const labelEl = wrap.querySelector(".erp-memo-label, .erp-input-label, label");
        if (labelEl && !labelEl.dataset.lockBadge) {
          labelEl.dataset.lockBadge = "1";
          labelEl.insertAdjacentHTML(
            "beforeend",
            ' <span data-lock-badge="1" style="color:#8a96a4;font-size:10px;margin-left:4px;" title="Read-only">🔒</span>'
          );
        }
      }
      // Krok 14a-A1f #4: attach instance pro _revertAll()
      wrap._inst = memo;
      wrap._origVal = displayValue;
      wrap._fieldKey = opts.fieldKey || null;
      wrap._kind = "memo";
      // Krok 14a-A1j #1: puvodni label fallback
      wrap.dataset.designOrigLabel = label || "";
      // Krok 14a-A1n #2: initial color apply (z localStorage overrides)
      _applyInitialColor(wrap, opts.fieldKey);
      // Krok 14a-A1i #2: right-click handle na label
      if (opts.fieldKey) {
        const labelEl = wrap.querySelector(".erp-memo-label, .erp-input-label, label");
        if (labelEl) {
          labelEl.setAttribute("data-design-fieldkey", opts.fieldKey);
          labelEl.style.cursor = "context-menu";
        }
      }
      return wrap;
    }

    // Fallback — pokud ErpMemo chybi, ukaze text block
    const wrap = document.createElement("div");
    wrap.className = "erp-field erp-field-memo-fallback";
    wrap.style.cssText = "display:flex;flex-direction:column;gap:3px;grid-column:1/-1;";
    const lab = document.createElement("label");
    lab.textContent = label;
    lab.style.cssText = "font-size:11px;color:#8a96a4;font-weight:500;";
    wrap.appendChild(lab);
    const val = document.createElement("div");
    val.style.cssText = "padding:8px 10px;background:#0f141a;border:1px solid #2a3340;border-radius:3px;min-height:50px;color:#cfd6df;font-size:12px;white-space:pre-wrap;";
    if (!displayValue) {
      val.textContent = "—";
      val.style.color = "#5d6975";
    } else {
      val.textContent = displayValue;
    }
    wrap.appendChild(val);
    return wrap;
  }

  // ────────────────────────────────────────────────────────────────────
  // Phase 38.4 Krok 14a-A1h (12.5.2026 odpoledne): Marti's polish #2 + #3.
  //   #2 LABEL_OVERRIDES — human-friendly display label per fieldKey.
  //      MVP hardcoded; Etapa 3 (Phase 30+) nahradí z fw.framework_property.
  //   #3 HINT_OVERRIDES — popisy field-by-field, ukáží se po ~1s hover
  //      (browser native title attribute). Pokud hint neni, nic se neukaze.
  //      MVP hardcoded; Etapa 3 nahradí z DB.
  // ────────────────────────────────────────────────────────────────────

  const LABEL_OVERRIDES = {
    // fw.menu_node
    "mn.menu_node_pk": "Číslo definice (legacy Centrála 1)",
    "mn.framework_jadro_id": "Vazba na jádro (legacy)",
    "mn.special_handler": "Speciální handler",
    "mn.visibility_scope": "Rozsah viditelnosti",
    "mn.is_immutable": "Neměnitelný",
    "mn.sort_order": "Pořadí řazení",
    "mn.parent_id": "Nadřazený uzel (ID)",
    "mn.parent_code": "Nadřazený uzel (kód)",
    "mn.core_id": "Vazba na Core přehled (FK)",
    // Krok 14a-A1l #1 — dva popisy
    "mn.description_user": "Popis uzlu (pro uživatele)",
    "mn.description_system": "Popis uzlu (pro vývojáře)",
    // fw.core
    // Phase fw.core slim 20.5.2026: layout_type + layout_template + parent_framework_id DROPPED
    "core.version": "Verze",
    // Krok 14a-A1l #1 — dva popisy
    "core.description_user": "Popis core (pro uživatele)",
    "core.description_system": "Popis core (pro vývojáře)",
    // Form 3 context
    "ctx.gridCode": "Grid kde uživatel klikl (core.code)",
    "ctx.rowId": "ID řádku v gridu",
    "ctx.headerName": "Sloupec, na který uživatel klikl",
    "ctx.compDefId": "ID definice sloupce (comp_def)",
  };

  const HINT_OVERRIDES = {
    // fw.menu_node
    "mn.id": "Primární klíč v fw.menu_node tabulce (read-only).",
    "mn.code": "Unikátní textový identifikátor uzlu (např. system.framework.menu_nodes).",
    "mn.label": "Lidsky čitelný název uzlu zobrazený v ERP stromě.",
    "mn.kind": "Typ uzlu: list (přehled), form (jádro), folder (soudeček), iframe, special.",
    "mn.parent_id": "FK na rodičovský fw.menu_node — určuje pozici ve stromě.",
    "mn.parent_code": "Computed: code rodiče. Změna parenta se dělá přes parent_id (Krok 14c picker).",
    "mn.sort_order": "Pořadí ve stromě v rámci stejného rodiče (rostoucí).",
    "mn.status": "active = viditelný, draft = ve vývoji, archived = skrytý.",
    "mn.visibility_scope": "Kdo vidí tento uzel: parent_only (rodiče), admin, tenant_member, public.",
    "mn.menu_node_pk": "Legacy číslo z Centrály 1. Nové uzly mají core_id FK na fw.core.",
    "mn.framework_jadro_id": "Phase 28-D legacy lineage. Pro nové uzly použij core_id.",
    "mn.special_handler": "Custom handler pro speciální typy (např. dynamic generation pro audit_*).",
    "mn.is_immutable": "Pokud ano, nelze editovat ani smazat (system pojistka).",
    "mn.description": "Volitelný popis uzlu — kde se používá, kdo ho vytvořil, pro koho je určen.",
    // Krok 14a-A1l #1 — dva popisy
    "mn.description_user": "K čemu uzel slouží z pohledu uživatele — co od něj může čekat. Píše buď uživatel sám, nebo Marti-AI po dohodě.",
    "mn.description_system": "Technický popis pro vývojáře — implementační poznámky, závislosti, edge case, debug tipy.",
    "mn.core_id": "FK na fw.core (Core přehled). NULL pro folders/iframes/special bez data view.",
    // fw.core
    "core.id": "Primární klíč v fw.core (read-only).",
    "core.code": "Unikátní textový identifikátor core (např. framework_menu_nodes).",
    "core.label": "Lidsky čitelný název core zobrazený jako title přehledu / formu.",
    // Phase fw.core slim 20.5.2026: layout_type + layout_template hints DROPPED
    "core.version": "Phase 8.5. Marti-AI's Q6 — verze pro lineage bez history tabulky.",
    // Phase fw.core slim 20.5.2026: parent_framework_id hint DROPPED
    "core.description": "Popis core — co reprezentuje, kdy byl vytvořen, kdo je tvůrce.",
    // Krok 14a-A1l #1 — dva popisy
    "core.description_user": "K čemu jádro / přehled slouží z pohledu uživatele. Co tam najde, jak s tím pracuje.",
    "core.description_system": "Technický popis pro vývojáře — co reprezentuje, data zdroje, vazby, edge cases.",
    // Form 3 context
    "ctx.gridCode": "core.code gridu, kde uživatel klikl pravým na řádek.",
    "ctx.rowId": "ID řádku v datovém zdroji (např. menu_node.id, comp_def.id).",
    "ctx.headerName": "Header label sloupce + field_name v technické formě.",
    "ctx.compDefId": "FK na fw.comp_def (definice sloupce). NULL pro System grids bez comp_def chain.",
  };

  // ────────────────────────────────────────────────────────────────────
  // Phase 38.4 Krok 14a-A1i #2: Right-click popup pro inline editaci
  // user labelu + hintu komponenty. Persistence v localStorage (MVP),
  // Etapa 3 přesune do fw.framework_property POST endpointu.
  // ────────────────────────────────────────────────────────────────────

  function _openFieldSettingsPopup(fieldKey, currentLabel, currentHint, anchorEl, currentColor) {
    return new Promise((resolve) => {
      const ovr = document.createElement("div");
      ovr.className = "erp-confirm-overlay";
      ovr.style.cssText = "position:fixed;inset:0;background:rgba(0,0,0,0.6);z-index:9600;display:flex;align-items:center;justify-content:center;";
      const dlg = document.createElement("div");
      dlg.className = "erp-confirm-dialog erp-design-modal";
      dlg.style.cssText = "background:#1a1f26;border:1px solid #2a3340;border-radius:6px;width:520px;max-width:95vw;color:#cfd6df;font-size:13px;box-shadow:0 16px 50px rgba(0,0,0,0.6);overflow:hidden;";

      const hdr = document.createElement("div");
      hdr.style.cssText = "padding:12px 16px;border-bottom:1px solid #2a3340;background:#141a20;font-size:14px;font-weight:600;color:#e8eef5;";
      hdr.textContent = "Nastavení komponenty";
      const sub = document.createElement("div");
      sub.style.cssText = "font-size:11px;color:#8a96a4;font-weight:normal;font-family:ui-monospace,Consolas,monospace;margin-top:2px;";
      sub.textContent = "fieldKey: " + fieldKey;
      hdr.appendChild(sub);
      dlg.appendChild(hdr);

      const body = document.createElement("div");
      body.style.cssText = "padding:16px;display:flex;flex-direction:column;gap:12px;";

      // Label input
      const labelWrap = document.createElement("div");
      labelWrap.style.cssText = "display:flex;flex-direction:column;gap:4px;";
      const labelLbl = document.createElement("label");
      labelLbl.textContent = "Uživatelský název (zobrazí se místo systémového)";
      labelLbl.style.cssText = "font-size:11px;color:#8a96a4;font-weight:500;";
      labelWrap.appendChild(labelLbl);
      const labelInp = document.createElement("input");
      labelInp.type = "text";
      labelInp.value = currentLabel || "";
      labelInp.placeholder = "(nechej prázdné pro výchozí)";
      labelInp.style.cssText = "padding:6px 8px;background:#0f141a;border:1px solid #2a3340;border-radius:3px;color:#cfd6df;font-size:13px;";
      labelWrap.appendChild(labelInp);
      body.appendChild(labelWrap);

      // Hint textarea
      const hintWrap = document.createElement("div");
      hintWrap.style.cssText = "display:flex;flex-direction:column;gap:4px;";
      const hintLbl = document.createElement("label");
      hintLbl.textContent = "Hint (popis při hover > 1s)";
      hintLbl.style.cssText = "font-size:11px;color:#8a96a4;font-weight:500;";
      hintWrap.appendChild(hintLbl);
      const hintArea = document.createElement("textarea");
      hintArea.value = currentHint || "";
      hintArea.placeholder = "(nechej prázdné pro žádný hint)";
      hintArea.rows = 4;
      hintArea.style.cssText = "padding:8px 10px;background:#0f141a;border:1px solid #2a3340;border-radius:3px;color:#cfd6df;font-size:12px;font-family:inherit;resize:vertical;line-height:1.5;";
      hintWrap.appendChild(hintArea);
      body.appendChild(hintWrap);

      // Phase 38.4 Krok 14a-A1n #2 (12.5.2026 vecer): color palette pro
      // dekorativni obarveni fieldu. Click swatch → select; "Bez barvy"
      // swatch resetuje. Vybrana barva ma vizualni hint (border ring).
      const colorWrap = document.createElement("div");
      colorWrap.style.cssText = "display:flex;flex-direction:column;gap:6px;";
      const colorLbl = document.createElement("label");
      colorLbl.textContent = "Barva pole (organizační — horní okraj)";
      colorLbl.style.cssText = "font-size:11px;color:#8a96a4;font-weight:500;";
      colorWrap.appendChild(colorLbl);
      const swatches = document.createElement("div");
      swatches.style.cssText = "display:flex;flex-wrap:wrap;gap:6px;align-items:center;";
      let _selectedColor = currentColor || null;
      function _renderSwatches() {
        swatches.innerHTML = "";
        DESIGN_FIELD_PALETTE.forEach((c) => {
          const sw = document.createElement("button");
          sw.type = "button";
          sw.title = c.name;
          sw.dataset.colorId = c.id || "";
          const isSelected = (c.id || null) === (_selectedColor || null);
          const isClear = c.id === null;
          if (isClear) {
            sw.textContent = "✕";
            sw.style.cssText = "width:28px;height:28px;border-radius:50%;border:1.5px solid " +
              (isSelected ? "#d4b88a" : "#3a4754") + ";background:transparent;color:#8a96a4;cursor:pointer;font-size:11px;display:flex;align-items:center;justify-content:center;line-height:1;";
          } else {
            sw.style.cssText = "width:28px;height:28px;border-radius:50%;border:" +
              (isSelected ? "3px solid #e8eef5" : "1.5px solid " + c.hex) +
              ";background:" + c.hex + ";cursor:pointer;padding:0;";
          }
          sw.addEventListener("click", () => {
            _selectedColor = c.id || null;
            _renderSwatches();
          });
          swatches.appendChild(sw);
        });
      }
      _renderSwatches();
      colorWrap.appendChild(swatches);
      body.appendChild(colorWrap);

      const note = document.createElement("div");
      note.style.cssText = "font-size:11px;color:#5d6975;font-style:italic;line-height:1.5;";
      note.textContent = "MVP: ukládá se do prohlížeče (localStorage). V budoucí Etapě 3 půjde do databáze (fw.framework_property).";
      body.appendChild(note);

      dlg.appendChild(body);

      const ftr = document.createElement("div");
      ftr.style.cssText = "padding:10px 16px;border-top:1px solid #2a3340;background:#141a20;display:flex;justify-content:space-between;gap:8px;align-items:center;";

      const clearBtn = document.createElement("button");
      clearBtn.type = "button";
      clearBtn.textContent = "Vrátit na výchozí";
      clearBtn.style.cssText = "padding:6px 12px;background:transparent;border:1px solid #3a4754;border-radius:3px;color:#8a96a4;cursor:pointer;font-size:11px;margin-right:auto;";

      const cancelBtn = document.createElement("button");
      cancelBtn.type = "button";
      cancelBtn.textContent = "Zrušit";
      cancelBtn.style.cssText = "padding:6px 16px;background:#2a3340;border:1px solid #3a4754;border-radius:3px;color:#cfd6df;cursor:pointer;font-size:12px;";

      const okBtn = document.createElement("button");
      okBtn.type = "button";
      okBtn.textContent = "💾 Uložit";
      okBtn.style.cssText = "padding:6px 16px;background:#3a5a3a;border:1px solid #4a7a4a;border-radius:3px;color:#e8eef5;cursor:pointer;font-size:12px;font-weight:600;";

      // A1t (12.5.2026 vecer doma): Marti's polish — Uložit (primary) vlevo,
      // Zrušit (secondary) vpravo. Sjednoceny order s _confirmDarkDialog.
      // clearBtn ma margin-right:auto → zustava uplne vlevo.
      ftr.appendChild(clearBtn);
      ftr.appendChild(okBtn);
      ftr.appendChild(cancelBtn);
      dlg.appendChild(ftr);
      ovr.appendChild(dlg);
      document.body.appendChild(ovr);

      function cleanup() {
        try { ovr.parentNode && ovr.parentNode.removeChild(ovr); } catch (e) {}
        document.removeEventListener("keydown", onKey);
      }
      function onKey(ev) {
        if (ev.key === "Escape") { cleanup(); resolve(null); }
      }
      cancelBtn.addEventListener("click", () => { cleanup(); resolve(null); });
      clearBtn.addEventListener("click", () => {
        cleanup();
        resolve({ label: null, hint: null, color: null, _cleared: true });
      });
      okBtn.addEventListener("click", () => {
        cleanup();
        resolve({
          label: labelInp.value.trim() || null,
          hint: hintArea.value.trim() || null,
          color: _selectedColor || null,
        });
      });
      ovr.addEventListener("click", (ev) => {
        if (ev.target === ovr) { cleanup(); resolve(null); }
      });
      dlg.addEventListener("contextmenu", (ev) => ev.preventDefault());
      document.addEventListener("keydown", onKey);
      setTimeout(() => labelInp.focus(), 50);
    });
  }

  // Krok 14a-A1n #2 (12.5.2026 vecer): resolve color override → hex string
  function _resolveColor(fieldKey) {
    if (!fieldKey) return null;
    const colorId = _USER_OVERRIDES.colors[fieldKey];
    if (!colorId) return null;
    const palette = DESIGN_FIELD_PALETTE.find(c => c.id === colorId);
    return palette ? palette.hex : null;
  }

  // Krok 14a-A1n #2: initial color apply pri konstrukci field wrappu.
  // Pouziva se v _field, _memo, _dropdown po wrap._fieldKey assignment.
  function _applyInitialColor(w, fieldKey) {
    if (!fieldKey) return;
    const hex = _resolveColor(fieldKey);
    if (hex) {
      w.dataset.designColor = _USER_OVERRIDES.colors[fieldKey];
      w.style.setProperty("--field-color", hex);
    }
  }

  // Krok 14a-A1o (12.5.2026 vecer): initial label + color apply pro
  // section title — analogie _applyInitialColor pro GroupBox header.
  function _applyInitialSectionOverrides(hdr, sectionKey) {
    if (!hdr || !sectionKey) return;
    const userLabel = _USER_OVERRIDES.labels[sectionKey];
    if (userLabel) {
      const userSpan = hdr.querySelector(".section-title-user");
      if (userSpan) userSpan.textContent = userLabel;
      else if (!hdr.dataset.designOrigSystemLabel) hdr.textContent = userLabel;
    }
    const hex = _resolveColor(sectionKey);
    if (hex) {
      hdr.dataset.designColor = _USER_OVERRIDES.colors[sectionKey];
      hdr.style.setProperty("--field-color", hex);
    }
  }

  // Krok 14a-A1o: re-apply overrides na section title po popup save / revert.
  function _reapplyOverridesForSection(hdr, sectionKey) {
    const origLabel = hdr.dataset.designOrigLabel || "";
    const origSysLabel = hdr.dataset.designOrigSystemLabel || "";
    const newLabel = _USER_OVERRIDES.labels[sectionKey] || origLabel;
    const newColor = _resolveColor(sectionKey);

    // Update user span (default visible) nebo plain textContent (no systemTitle)
    const userSpan = hdr.querySelector(".section-title-user");
    if (userSpan) {
      userSpan.textContent = newLabel;
    } else {
      // Plain section bez system title pair — preserve fieldkey attr
      hdr.textContent = newLabel;
      hdr.setAttribute("data-design-fieldkey", sectionKey);
    }

    // Color apply (font color via CSS rule + var)
    if (newColor) {
      hdr.dataset.designColor = _USER_OVERRIDES.colors[sectionKey];
      hdr.style.setProperty("--field-color", newColor);
    } else {
      delete hdr.dataset.designColor;
      hdr.style.removeProperty("--field-color");
    }
  }

  // Apply override → update DOM labels + hints v live modal po Save.
  // Krok 14a-A1j #1 bugfix: pouzij wrap.dataset.designOrigLabel jako
  // fallback (jinak po "Vratit na vychozi" label zmizel uplne).
  // Krok 14a-A1n #2: applyje i color override (border-top + CSS var).
  function _reapplyOverridesForField(w, fieldKey) {
    const origFallback = w.dataset.designOrigLabel || "";
    const newLabel = _resolveLabel(fieldKey, origFallback);
    const newHint = _resolveHint(fieldKey);
    const newColor = _resolveColor(fieldKey);
    const labelEl = w.querySelector(".erp-input-label, .erp-dropdown-label, .erp-memo-label, label");
    if (labelEl) {
      // Preserve lock badge if present (data-lock-badge byl set v helpers)
      const lockBadge = labelEl.querySelector("[data-lock-badge]");
      labelEl.textContent = newLabel;
      if (lockBadge) labelEl.appendChild(lockBadge);
      // Keep right-click handle (dataset attr survives textContent assignment? NE — dataset attr persists on element directly, NOT on textNode)
      labelEl.setAttribute("data-design-fieldkey", fieldKey);
      labelEl.style.cursor = "context-menu";
    }
    if (newHint) w.dataset.designHint = newHint;
    else delete w.dataset.designHint;
    // Krok 14a-A1n #2 color decoration — CSS var + data attribute.
    if (newColor) {
      w.dataset.designColor = _USER_OVERRIDES.colors[fieldKey];
      w.style.setProperty("--field-color", newColor);
    } else {
      delete w.dataset.designColor;
      w.style.removeProperty("--field-color");
    }
  }

  function _reapplyOverridesInDOM(fieldKey) {
    // Krok 14a-A1o: section.* prefix → cilenie na GroupBox title
    if (fieldKey && fieldKey.indexOf("section.") === 0) {
      document.querySelectorAll(
        '.erp-design-section-title[data-design-fieldkey="' + fieldKey + '"]'
      ).forEach(hdr => _reapplyOverridesForSection(hdr, fieldKey));
      return;
    }
    document.querySelectorAll(".erp-field-design").forEach(w => {
      if (w._fieldKey !== fieldKey) return;
      _reapplyOverridesForField(w, fieldKey);
    });
  }

  // Krok 14a-A1j #2: full-form re-apply pro system mode toggle (flip flag a refresh labels napric vsech otevrenych modalu).
  function _reapplyAllOverridesInDOM() {
    document.querySelectorAll(".erp-field-design").forEach(w => {
      if (!w._fieldKey) return;
      _reapplyOverridesForField(w, w._fieldKey);
    });
    // Krok 14a-A1o: section titles too
    document.querySelectorAll(".erp-design-section-title[data-design-fieldkey]").forEach(hdr => {
      const sectionKey = hdr.getAttribute("data-design-fieldkey");
      if (sectionKey) _reapplyOverridesForSection(hdr, sectionKey);
    });
  }

  function _installFieldLabelRightClick() {
    if (window._erpDesignLabelRCInstalled) return;
    window._erpDesignLabelRCInstalled = true;
    document.addEventListener("contextmenu", (ev) => {
      // Find ancestor element s data-design-fieldkey
      const labelEl = ev.target.closest && ev.target.closest("[data-design-fieldkey]");
      if (!labelEl) return;
      // Jen v design modu (Marti's request)
      if (!window._erpDesignMode) return;
      ev.preventDefault();
      ev.stopPropagation();
      const fieldKey = labelEl.getAttribute("data-design-fieldkey");
      if (!fieldKey) return;
      const currentLabel = _USER_OVERRIDES.labels[fieldKey] || LABEL_OVERRIDES[fieldKey] || "";
      const currentHint = _USER_OVERRIDES.hints[fieldKey] || HINT_OVERRIDES[fieldKey] || "";
      const currentColor = _USER_OVERRIDES.colors[fieldKey] || null;
      _openFieldSettingsPopup(fieldKey, currentLabel, currentHint, labelEl, currentColor).then(result => {
        if (result == null) return;  // cancelled
        // Apply changes
        if (result._cleared) {
          delete _USER_OVERRIDES.labels[fieldKey];
          delete _USER_OVERRIDES.hints[fieldKey];
          delete _USER_OVERRIDES.colors[fieldKey];
          _saveUserOverride("labels", fieldKey, null);
          _saveUserOverride("hints", fieldKey, null);
          _saveUserOverride("colors", fieldKey, null);
        } else {
          if (result.label != null) {
            _USER_OVERRIDES.labels[fieldKey] = result.label;
            _saveUserOverride("labels", fieldKey, result.label);
          } else {
            delete _USER_OVERRIDES.labels[fieldKey];
            _saveUserOverride("labels", fieldKey, null);
          }
          if (result.hint != null) {
            _USER_OVERRIDES.hints[fieldKey] = result.hint;
            _saveUserOverride("hints", fieldKey, result.hint);
          } else {
            delete _USER_OVERRIDES.hints[fieldKey];
            _saveUserOverride("hints", fieldKey, null);
          }
          if (result.color != null) {
            _USER_OVERRIDES.colors[fieldKey] = result.color;
            _saveUserOverride("colors", fieldKey, result.color);
          } else {
            delete _USER_OVERRIDES.colors[fieldKey];
            _saveUserOverride("colors", fieldKey, null);
          }
        }
        _reapplyOverridesInDOM(fieldKey);
      });
    }, true);
  }
  _installFieldLabelRightClick();

  function _resolveLabel(fieldKey, fallback) {
    if (!fieldKey) return fallback;
    // Krok 14a-A1j #2: pokud je zapnuty system mode toggle, zobraz fieldKey
    // raw (napr. "mn.code" misto "Code") — pro techniky pri ladeni.
    if (window._erpDesignShowSystemNames === true) return fieldKey;
    // User override má prednost pred hardcoded (Marti's polish #2)
    if (_USER_OVERRIDES.labels[fieldKey]) return _USER_OVERRIDES.labels[fieldKey];
    if (LABEL_OVERRIDES[fieldKey]) return LABEL_OVERRIDES[fieldKey];
    return fallback;
  }

  function _resolveHint(fieldKey) {
    if (!fieldKey) return null;
    // User override má prednost
    if (_USER_OVERRIDES.hints[fieldKey]) return _USER_OVERRIDES.hints[fieldKey];
    if (HINT_OVERRIDES[fieldKey]) return HINT_OVERRIDES[fieldKey];
    return null;
  }

  // ────────────────────────────────────────────────────────────────────
  // Enum item presets pro _dropdown — hardcoded MVP, Krok 14b nacita z DB
  // (fw.entity_def attributes nebo dedicated enum tabulka).
  // ────────────────────────────────────────────────────────────────────

  const ENUM_ITEMS = {
    // fw.menu_node.kind — list/form/folder/iframe/special (Phase 38.3+ schema)
    kind: [
      { value: "list", label: "📋 list (přehled)" },
      { value: "form", label: "📝 form (jádro)" },
      { value: "folder", label: "📁 folder (soudeček)" },
      { value: "iframe", label: "🖼️ iframe (vnořený obsah)" },
      { value: "special", label: "⚙️ special (hardcoded)" },
    ],
    // fw.menu_node.status — active/archived/draft (Marti-AI's actual schema)
    status: [
      { value: "active", label: "✓ active" },
      { value: "draft", label: "📝 draft" },
      { value: "archived", label: "📦 archived" },
    ],
    // fw.menu_node.visibility_scope — parent_only/admin/tenant/public
    visibility_scope: [
      { value: "parent_only", label: "🔒 parent_only (jen rodiče)" },
      { value: "parent_or_admin", label: "🔐 parent_or_admin" },
      { value: "tenant_member", label: "👥 tenant_member" },
      { value: "public", label: "🌐 public" },
    ],
    // Boolean ano/ne — pouzitý napriklad pro is_immutable
    bool_ano_ne: [
      { value: "true", label: "✓ ano" },
      { value: "false", label: "✗ ne" },
    ],
    // fw.core.layout_type
    layout_type: [
      { value: "list", label: "📋 list (grid view)" },
      { value: "form", label: "📝 form (single record)" },
      { value: "special", label: "⚙️ special" },
    ],
  };

  function _dropdown(label, value, items, opts) {
    // Phase 38.4 Krok 14a-A1c (12.5.2026): listbox/dropdown wrapper.
    // Marti's #2 feedback - "komponenta Listbox pro vyber stavu jako ano/ne".
    //
    // items: array of {value, label} NEBO string key z ENUM_ITEMS (preset).
    // value: aktualni hodnota (string nebo bool). null/undefined = nic vybrane.
    // opts.readonly: true = disabled dropdown (system metadata).
    opts = opts || {};
    const isReadonly = !!opts.readonly;
    // Krok 14a-A1h: label + hint override
    const resolvedLabel = _resolveLabel(opts.fieldKey, label);
    const resolvedHint = _resolveHint(opts.fieldKey);

    // Resolve items — string preset OR array
    let resolvedItems = [];
    if (typeof items === "string" && ENUM_ITEMS[items]) {
      resolvedItems = ENUM_ITEMS[items];
    } else if (Array.isArray(items)) {
      resolvedItems = items;
    }

    // Normalize value — bool/number → string (ErpDropdown porovnava .value === ===)
    let resolvedValue = value;
    if (typeof value === "boolean") resolvedValue = value ? "true" : "false";
    else if (value == null) resolvedValue = null;
    else resolvedValue = String(value);

    // UI Kit cesta — pokud ErpDropdown zaregistrovan
    if (typeof global.ErpDropdown === "function") {
      const wrap = document.createElement("div");
      wrap.className = "erp-field erp-field-design erp-field-dropdown";
      wrap.style.cssText = "display:flex;flex-direction:column;gap:3px;";
      if (resolvedHint) wrap.dataset.designHint = resolvedHint;
      // Phase 38.4 Krok 14a-A1g #1 (12.5.2026 odpoledne polish): marker
      // "← původní" se v panel ukazuje JEN kdyz je hodnota zmenena.
      // V initial state (clean): items bez markeru.
      const dd = new global.ErpDropdown(wrap, {
        label: label,
        value: resolvedValue,
        items: resolvedItems,
        disabled: isReadonly,
        placeholder: "—",
        // Phase 38.4 Krok 14a-A1d (12.5.2026): dirty tracking pro dropdowns
        // Krok 14a-A1g #1 (12.5.2026 odpoledne): dynamic re-mark — pri zmene
        // pridame "← původní" marker na puvodni polozku v items list (panel),
        // pri vraceni zpet ho odstranime.
        onChange: (newVal, item) => {
          if (isReadonly) return;
          const isDirty = String(newVal || "") !== String(resolvedValue || "");
          if (dd.trigger) {
            if (isDirty) {
              dd.trigger.style.borderLeft = "3px solid #d4b88a";
              dd.trigger.style.background = "#1f1810";
            } else {
              dd.trigger.style.borderLeft = "";
              dd.trigger.style.background = "";
            }
          }
          // Dynamic marker: pri dirty pridame marker na puvodni polozku
          // (jen v panel — trigger label ukazuje aktualne vybranou, ktera
          // marker nepotrebuje). Pri clean state: items bez markerů.
          if (isDirty && resolvedValue) {
            const markedItems = resolvedItems.map(it => {
              if (String(it.value) === String(resolvedValue)) {
                return Object.assign({}, it, { label: it.label + "  ← původní" });
              }
              return it;
            });
            dd.setItems(markedItems);
          } else {
            dd.setItems(resolvedItems);
          }
          if (typeof opts.onDirty === "function" && opts.fieldKey) {
            opts.onDirty(opts.fieldKey, isDirty);
          }
        },
      });
      // Readonly vizualni boost
      // Krok 14a-A1p (12.5.2026 vecer): accent border zrusen u RO,
      // viz _field komentar (RO = tichy lock pattern).
      if (isReadonly && dd.trigger) {
        dd.trigger.style.background = "#1a2028";
        dd.trigger.style.color = "#9ba8b8";
        dd.trigger.style.opacity = "1";
        // Krok 14c+3.5: default cursor pro RO (Marti's "standardne, jako
        // kdyz komponenta neni RO"). 🔒 badge + tmavší bg signalizují stav.
        dd.trigger.style.cursor = "default";
        // Lock badge na label
        const labelEl = wrap.querySelector(".erp-dropdown-label");
        if (labelEl && !labelEl.dataset.lockBadge) {
          labelEl.dataset.lockBadge = "1";
          labelEl.insertAdjacentHTML(
            "beforeend",
            ' <span data-lock-badge="1" style="color:#8a96a4;font-size:10px;margin-left:4px;" title="Read-only">🔒</span>'
          );
        }
      }
      // Krok 14a-A1f #4: attach instance + origVal pro _revertAll()
      wrap._inst = dd;
      wrap._origVal = resolvedValue;
      wrap._fieldKey = opts.fieldKey || null;
      wrap._kind = "dropdown";
      // Krok 14a-A1j #1: puvodni label fallback pro revert
      wrap.dataset.designOrigLabel = label || "";
      // Krok 14a-A1n #2: initial color apply (z localStorage overrides)
      _applyInitialColor(wrap, opts.fieldKey);
      // Krok 14a-A1i #2: right-click handle na label
      if (opts.fieldKey) {
        const labelEl = wrap.querySelector(".erp-dropdown-label");
        if (labelEl) {
          labelEl.setAttribute("data-design-fieldkey", opts.fieldKey);
          labelEl.style.cursor = "context-menu";
        }
      }
      return wrap;
    }

    // Fallback — pokud ErpDropdown chybi, ukaze raw label + value
    const wrap = document.createElement("div");
    wrap.className = "erp-field erp-field-dropdown-fallback";
    wrap.style.cssText = "display:flex;flex-direction:column;gap:3px;";
    const lab = document.createElement("label");
    lab.textContent = label;
    lab.style.cssText = "font-size:11px;color:#8a96a4;font-weight:500;";
    wrap.appendChild(lab);
    const val = document.createElement("div");
    val.style.cssText = "padding:5px 8px;background:#0f141a;border:1px solid #2a3340;border-radius:3px;min-height:22px;color:#cfd6df;font-size:12px;";
    // Lookup label pro value v items
    let displayLabel = resolvedValue;
    const match = resolvedItems.find(it => String(it.value) === resolvedValue);
    if (match) displayLabel = match.label;
    if (!displayLabel) {
      val.textContent = "—";
      val.style.color = "#5d6975";
    } else {
      val.textContent = displayLabel;
    }
    wrap.appendChild(val);
    return wrap;
  }

  // Phase 38.4 Krok 14a-A1m #1 (12.5.2026 odpoledne): GroupBox label
  // pair (user + system). Stejny princip jako pro komponenty:
  // sysToggle prepina mezi user title (default) a system title (developer
  // mode). Pokud `systemTitle` nezadan, ukaze se title v obou rezimech.
  //
  // Krok 14a-A1o (12.5.2026 vecer, Marti's polish po amnesii): section
  // title je teď taky right-click target — stejny popup (Label / Hint /
  // Color) jako u field labelu. SectionKey odvozen z systemTitle (stable
  // technical key) nebo z user title (fallback). Prefix "section." aby
  // collision s fieldKey nehrozila.
  function _sectionKeyFromTitle(title, systemTitle) {
    // Preferuj systemTitle (stable identifier), fallback na user title.
    const src = systemTitle || title || "";
    const slug = String(src)
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/^_+|_+$/g, "")
      .slice(0, 60);
    return "section." + (slug || "unnamed");
  }

  function _sectionBuild(title, systemTitle) {
    const sectionKey = _sectionKeyFromTitle(title, systemTitle);
    const wrap = document.createElement("div");
    wrap.className = "erp-design-section";
    wrap.style.cssText = "margin-bottom:14px;";

    // Marti's doctrine (12.5.2026 ~23:30): "Panel nema label... Je to jen
    // plocha." Pokud title (user label) je empty string nebo NULL → SKIP
    // header rendering uplne (zadne padding, zadny border-bottom).
    // Drzi Centrala 1 paralela — root form panel byl 'def' (parent_name),
    // ne věc s display title.
    //
    // Edge case: pokud title="" ale systemTitle="..." (technical), stale
    // skip — Marti's intent je 'panel as canvas', technical info je
    // pro debug ne pro UI.
    const hasUserTitle = title != null && String(title).trim() !== "";

    if (hasUserTitle) {
      const hdr = document.createElement("div");
      hdr.className = "erp-design-section-title";
      hdr.style.cssText = "font-size:12px;font-weight:600;color:#a8b4c2;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;padding-bottom:4px;border-bottom:1px solid #2a3340;cursor:context-menu;";
      // A1o: stable fieldKey + orig label fallback (pro Vratit na vychozi)
      hdr.setAttribute("data-design-fieldkey", sectionKey);
      hdr.dataset.designOrigLabel = title;
      if (systemTitle) {
        hdr.dataset.designOrigSystemLabel = systemTitle;
        const userSpan = document.createElement("span");
        userSpan.className = "section-title-user";
        userSpan.textContent = title;
        hdr.appendChild(userSpan);
        const sysSpan = document.createElement("span");
        sysSpan.className = "section-title-system";
        sysSpan.textContent = systemTitle;
        hdr.appendChild(sysSpan);
      } else {
        hdr.textContent = title;
      }
      // A1o: initial label/color apply (uzivatelske preference z localStorage)
      _applyInitialSectionOverrides(hdr, sectionKey);
      wrap.appendChild(hdr);
    }
    // ELSE: panel je plocha, header skip (Marti's "panel nema label" doctrine).

    const grid = document.createElement("div");
    grid.className = "erp-design-grid";
    grid.style.cssText = "display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:8px 14px;";
    wrap.appendChild(grid);
    return { wrap, grid };
  }

  // ────────────────────────────────────────────────────────────────────
  // Form 1+2 konsolidovany: Soudecek + Core prehledu (2 taby)
  // ────────────────────────────────────────────────────────────────────


  // ─────────────────────────────────────────────────────────────────
  // Phase JS-2 export: global namespace for design_forms.js classes
  // ─────────────────────────────────────────────────────────────────
  global._erpDFH = {
    _esc: _esc,
    _ensureToastContainer: _ensureToastContainer,
    _ensureToastStyles: _ensureToastStyles,
    _showToast: _showToast,
    _markFormDirty: _markFormDirty,
    _dirtyForms: _dirtyForms,
    _loadUserOverrides: _loadUserOverrides,
    _saveUserOverride: _saveUserOverride,
    OVERRIDES_LS_KEY: OVERRIDES_LS_KEY,
    DESIGN_FIELD_PALETTE: DESIGN_FIELD_PALETTE,
    _getTooltipEl: _getTooltipEl,
    _showTooltip: _showTooltip,
    _hideTooltip: _hideTooltip,
    _installDarkTooltips: _installDarkTooltips,
    _promptDarkDialog: _promptDarkDialog,
    _confirmDarkDialog: _confirmDarkDialog,
    _buildModalShell: _buildModalShell,
    _buildDescriptionsPopup: _buildDescriptionsPopup,
    _field: _field,
    _memo: _memo,
    _dropdown: _dropdown,
    _readonlyInput: _readonlyInput,
    _openFieldSettingsPopup: _openFieldSettingsPopup,
    _resolveColor: _resolveColor,
    LABEL_OVERRIDES: LABEL_OVERRIDES,
    HINT_OVERRIDES: HINT_OVERRIDES,
    _applyInitialColor: _applyInitialColor,
    _applyInitialSectionOverrides: _applyInitialSectionOverrides,
    _reapplyOverridesForSection: _reapplyOverridesForSection,
    _reapplyOverridesForField: _reapplyOverridesForField,
    _reapplyOverridesInDOM: _reapplyOverridesInDOM,
    _reapplyAllOverridesInDOM: _reapplyAllOverridesInDOM,
    _installFieldLabelRightClick: _installFieldLabelRightClick,
    _resolveLabel: _resolveLabel,
    _resolveHint: _resolveHint,
    _sectionKeyFromTitle: _sectionKeyFromTitle,
    _sectionBuild: _sectionBuild,
    ENUM_ITEMS: ENUM_ITEMS,
  };

  }); // _erpLoadModule end
})(typeof window !== "undefined" ? window : this);
