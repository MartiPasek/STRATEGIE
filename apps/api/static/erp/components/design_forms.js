/**
 * Design Forms — 3 hardcoded forms pro framework editor.
 *
 * Phase 38.4 Krok 14a (12.5.2026 ranni). Marti+Marti-AI's konsolidace:
 *   - Form 1+2 sloucene do `DesignSoudecekCoreForm` (2 taby pres ErpPageControl)
 *     Tab 'soudecek' = fw.menu_node fields
 *     Tab 'prehled'  = fw.core fields + (priste) inline grid editor fw.comp_def
 *   - Form 3 = `DesignJadroRadekForm` (1 tab MVP, prepared pro rozsireni)
 *     Tab 'jadro' = fw.core identity + (priste) field picker + data source
 *
 * MVP scope (Krok 14a):
 *   - Read-only fields, taby fungujou
 *   - Save NEZAREN (Krok 14b pozdeji)
 *   - Inline grid editor pro fw.comp_def NEZAREN (Krok 14b)
 *   - Field picker dvoupanelovy NEZAREN (Krok 14c)
 *
 * Marti's rytmus 12.5. rano: *"nejde to dat na prvni dobrou... bude se to
 * mesice vyvijet, tak jak fw poroste"*. Iterativni pristup.
 *
 * Dependencies:
 *   - ErpPageControl (components/pagecontrol.js)
 *   - ErpFormSection (components/formsection.js)
 *   - ErpInput, ErpCheckbox, ErpDropdown, ErpMemo, ErpFormList (components/*)
 *   - ErpButton (components/button.js) - pro modal footer
 *
 * Backend (Krok 14a):
 *   GET /api/v1/erp/design/menu-node/{id}  -> {menu_node, core}
 *   GET /api/v1/erp/design/jadro/{core_id} -> {core, columns_preview}
 */
(function (global) {
  "use strict";

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
      body.textContent = message;
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
    "mn.cislo_def": "Číslo definice (legacy Centrála 1)",
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
    "core.layout_type": "Typ rozložení",
    "core.layout_template": "Šablona rozložení",
    "core.data_entity_type": "Typ datové entity",
    "core.parent_framework_id": "Nadřazené jádro (lineage)",
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
    "mn.cislo_def": "Legacy číslo z Centrály 1. Nové uzly mají core_id FK na fw.core.",
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
    "core.layout_type": "list = grid view (přehled řádků), form = single record (jádro), special = hardcoded.",
    "core.layout_template": "Volitelná šablona pro pixel-aware layout (single, multi-pane).",
    "core.data_entity_type": "FK na fw.entity_def.code — typ entity, kterou core reprezentuje (např. menu_node, core, comp_def).",
    "core.version": "Phase 8.5. Marti-AI's Q6 — verze pro lineage bez history tabulky.",
    "core.parent_framework_id": "Phase 8.5. Marti-AI's Q6 — FK na předchozí verzi (self-FK pro lineage).",
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

  class DesignSoudecekCoreForm {
    constructor(opts) {
      this.opts = opts || {};
      // opts.menuNodeId (preferred) | opts.menuNodeCode | opts.coreId
      // opts.initialTab = 'prehled' (default po Krok 14g-H+31 step 8) | 'soudecek'
      this._shell = null;
      this._pc = null;
      this._data = null;
      // Phase 38.4 Krok 14a-A1d: dirty tracking
      this._dirty = new Set();
      this._saveBtn = null;
      this._dirtyBadge = null;
    }

    _onDirty(fieldKey, isDirty) {
      if (isDirty) this._dirty.add(fieldKey);
      else this._dirty.delete(fieldKey);
      const count = this._dirty.size;
      if (this._saveBtn) this._saveBtn.style.display = count > 0 ? "" : "none";
      if (this._dirtyBadge) {
        // A1q (12.5.2026 vecer): Czech plural fix — Marti's polish.
        // 1 = "změna", 2-4 = "změny", 5+ = "změn".
        const _wBadge = count === 1 ? "změna" : (count < 5 ? "změny" : "změn");
        this._dirtyBadge.textContent = count > 0
          ? "● " + count + " " + _wBadge
          : "";
        this._dirtyBadge.style.display = count > 0 ? "" : "none";
      }
      // A1r (12.5.2026 vecer): global dirty tracking pro F5/tab close warning.
      _markFormDirty(this, count > 0);
    }

    async _onSaveClick() {
      // Phase 38.4 Krok 14g-H+18 (15.5.2026 ~14:49, Marti's "Nejde mi
      // ulozit nastaveni soudecku v HC formu"): reuse Form 3 PATCH pattern
      // pres generic /design/{entity}/{id} endpoint. Form 1 ma 2 entity
      // (menu_node + core), takze split dirty fields by prefix.
      if (this._dirty.size === 0) {
        this._shell.close();
        return;
      }

      const mn = (this._data && this._data.menu_node) || null;
      const core = (this._data && this._data.core) || null;

      // Collect dirty changes z DOM. Wraps drzi _fieldKey (mn.label, core.code)
      // + _inst (UI Kit instance pro .value() read).
      const mnChanges = {};
      const coreChanges = {};
      const allWraps = this._shell.body.querySelectorAll(".erp-field, .erp-dropdown, .erp-memo");
      for (const wrap of allWraps) {
        const fk = wrap._fieldKey;
        if (!fk || !this._dirty.has(fk)) continue;
        const parts = fk.split(".");
        if (parts.length < 2) continue;
        const prefix = parts[0];  // "mn" | "core"
        const fieldName = parts.slice(1).join(".");
        let val = null;
        if (wrap._inst && typeof wrap._inst.value === "function") {
          val = wrap._inst.value();
        } else if (wrap._inst && wrap._inst.input) {
          val = wrap._inst.input.value;
        } else {
          const inp = wrap.querySelector("input, textarea, select");
          if (inp) val = inp.value;
        }
        if (prefix === "mn") mnChanges[fieldName] = val;
        else if (prefix === "core") coreChanges[fieldName] = val;
      }

      // Save menu_node + core sekvenčně (oba entity = oba PATCH calls)
      const errors = [];
      let savedCount = 0;

      const _doPatch = async (entityType, rowId, changes, expectedUpdatedAt) => {
        if (!Object.keys(changes).length) return;
        if (rowId == null) {
          errors.push(entityType + ": missing row id");
          return;
        }
        try {
          const r = await fetch(
            "/api/v1/erp/design/" + encodeURIComponent(entityType) + "/" + encodeURIComponent(rowId),
            {
              method: "PATCH",
              credentials: "include",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                field_changes: changes,
                expected_updated_at: expectedUpdatedAt,
              }),
            }
          );
          if (r.status === 409) {
            errors.push(entityType + ": konflikt (někdo jiný editoval)");
            return;
          }
          if (!r.ok) {
            const errData = await r.json().catch(() => ({}));
            errors.push(entityType + ": " + (errData.error || ("HTTP " + r.status)));
            return;
          }
          savedCount += Object.keys(changes).length;
        } catch (e) {
          errors.push(entityType + ": " + (e.message || e));
        }
      };

      if (mn && Object.keys(mnChanges).length) {
        await _doPatch("menu_node", mn.id, mnChanges, mn.updated_at);
      }
      if (core && Object.keys(coreChanges).length) {
        await _doPatch("core", core.id, coreChanges, core.updated_at);
      }

      if (errors.length) {
        alert("Uložení selhalo:\n" + errors.join("\n"));
        return;
      }

      // Success — toast + close
      this._dirty.clear();
      _markFormDirty(this, false);
      const _wToast = savedCount === 1 ? "změna" : (savedCount < 5 ? "změny" : "změn");
      if (typeof _showToast === "function") {
        _showToast("Uloženo — " + savedCount + " " + _wToast, "success");
      }
      this._shell.close();
      // Refresh tree + grid (drag-drop H+9/H+15 pattern)
      try {
        if (typeof window.reloadErpTree === "function") {
          await window.reloadErpTree();
        }
        if (window._sysHelpers
            && typeof window._sysHelpers.renderSystemGrid === "function"
            && window._sysCurrentMode === "menu_nodes") {
          await window._sysHelpers.renderSystemGrid("menu_nodes", window._sysCurrentLabel || "");
        }
      } catch (eRefresh) {
        console.warn("[DesignSoudecekCoreForm] post-save refresh failed:", eRefresh);
      }
    }

    /**
     * Phase 38.4 Krok 14g-H+22 (15.5.2026 ~17:30): core picker pres novou
     * ErpCatalogPicker komponentu (Centrála 1 parita). Reusable napriС
     * vsechny FK reference scenarios.
     */
    async _openCorePickerModal() {
      const menuNode = (this._data && this._data.menu_node) || null;
      if (!menuNode || !menuNode.id) {
        alert("Picker chyba: chybi menu_node ID.");
        return;
      }
      if (typeof window.ErpCatalogPicker !== "function") {
        alert("ErpCatalogPicker not loaded (catalog_picker.js missing).");
        return;
      }

      const usedRenderer = function (params) {
        const v = params && params.value;
        if (v && v > 0) {
          return '<span title="Použit v ' + v + ' soudečku(ů)" style="color:#7a8696;">🔗 ' + v + '×</span>';
        }
        return '';
      };

      const self = this;
      const picker = new window.ErpCatalogPicker({
        title: "🔗 Vybrat existing core přehled",
        endpoint: "/api/v1/erp/design/fw-core/list",
        listKey: "cores",
        labelField: "label",
        columns: [
          { headerName: "Code", field: "code", width: 220, filter: "agTextColumnFilter", sortable: true },
          { headerName: "Label", field: "label", flex: 1, minWidth: 200, filter: "agTextColumnFilter", sortable: true },
          { headerName: "Layout", field: "layout_type", width: 130, filter: "agTextColumnFilter", sortable: true },
          { headerName: "Data entity", field: "data_entity_type", width: 130, filter: "agTextColumnFilter", sortable: true },
          { headerName: "v", field: "version", width: 60, type: "numericColumn", sortable: true },
          { headerName: "Použit ×", field: "is_used_count", width: 110, type: "numericColumn", sortable: true, cellRenderer: usedRenderer },
        ],
        onSelect: (row) => {
          this._associateCoreWithMenuNode(row.id, row.label, null);
        },
        // Phase 38.4 Krok 14g-H+23 (15.5.2026 ~18:00, Marti's "tlacitko +"):
        // Day 2 first task — enable CRUD ➕ Nový. Edit / Delete stay disabled.
        enableNew: true,
        enableEdit: false,
        enableDelete: false,
        onNew: () => self._openCoreCreateForm(picker),
      });
      picker.open();
    }

    /**
     * Phase 38.4 Krok 14g-H+23 (15.5.2026 ~18:00, Marti's "tlacitko +
     * bez nej se systemove nepohneme"): mini form modal pro CREATE
     * fw.core. Po success refresh picker grid + auto-associate s
     * current menu_node.
     */
    _openCoreCreateForm(picker) {
      // Mini overlay
      const overlay = document.createElement("div");
      overlay.style.cssText =
        "position:fixed;inset:0;background:rgba(0,0,0,0.6);z-index:10020;" +
        "display:flex;align-items:center;justify-content:center;";

      const modal = document.createElement("div");
      modal.style.cssText =
        "width:480px;max-width:95vw;background:#1a1f26;border:1px solid #2a3340;" +
        "border-radius:6px;display:flex;flex-direction:column;color:#cfd6df;" +
        "font-size:13px;box-shadow:0 8px 32px rgba(0,0,0,0.5);";

      // Header
      const header = document.createElement("div");
      header.style.cssText =
        "padding:14px 18px;border-bottom:1px solid #2a3340;display:flex;" +
        "align-items:center;justify-content:space-between;";
      header.innerHTML = '<div style="font-size:14px;font-weight:600;color:#e8eef5;">' +
        '➕ Vytvořit nový core přehled</div>';
      const closeBtn = document.createElement("button");
      closeBtn.type = "button";
      closeBtn.textContent = "✕";
      closeBtn.style.cssText =
        "background:none;border:none;color:#7a8696;font-size:18px;cursor:pointer;padding:0 4px;";
      closeBtn.onclick = () => overlay.remove();
      header.appendChild(closeBtn);
      modal.appendChild(header);

      // Body — form fields
      const body = document.createElement("div");
      body.style.cssText = "padding:18px;display:flex;flex-direction:column;gap:14px;";

      const _mkField = (label, hint, isRequired) => {
        const wrap = document.createElement("div");
        wrap.style.cssText = "display:flex;flex-direction:column;gap:4px;";
        const lbl = document.createElement("label");
        lbl.style.cssText = "color:#a8b4c2;font-size:11px;font-weight:500;";
        lbl.innerHTML = label + (isRequired ? ' <span style="color:#d4a8a8;">*</span>' : '');
        wrap.appendChild(lbl);
        if (hint) {
          const h = document.createElement("div");
          h.style.cssText = "color:#7a8696;font-size:10px;font-style:italic;";
          h.textContent = hint;
          wrap.appendChild(h);
        }
        return wrap;
      };

      // code
      const codeWrap = _mkField("Code", "Lowercase snake_case (a-z, 0-9, _). Unikátní v fw.core. Např. 'users_grid', 'audit_dashboard'.", true);
      const codeInput = document.createElement("input");
      codeInput.type = "text";
      codeInput.style.cssText =
        "padding:8px 10px;background:#0f141a;border:1px solid #3a4754;border-radius:4px;" +
        "color:#e8eef5;font-size:12px;font-family:monospace;outline:none;";
      codeInput.placeholder = "users_grid";
      codeWrap.appendChild(codeInput);
      body.appendChild(codeWrap);

      // label
      const labelWrap = _mkField("Label", "Human-readable jméno (UI label). Např. 'Uživatelé', 'Audit dashboard'.", true);
      const labelInput = document.createElement("input");
      labelInput.type = "text";
      labelInput.style.cssText =
        "padding:8px 10px;background:#0f141a;border:1px solid #3a4754;border-radius:4px;" +
        "color:#e8eef5;font-size:12px;outline:none;";
      labelInput.placeholder = "Uživatelé";
      labelWrap.appendChild(labelInput);
      body.appendChild(labelWrap);

      // layout_type (dropdown)
      const layoutWrap = _mkField("Layout type", "Jak se přehled zobrazuje. 'list' = AG Grid table. 'form' = single-row editor. Default 'list'.", false);
      const layoutSelect = document.createElement("select");
      layoutSelect.style.cssText =
        "padding:8px 10px;background:#0f141a;border:1px solid #3a4754;border-radius:4px;" +
        "color:#e8eef5;font-size:12px;outline:none;";
      ["list", "form", "dashboard", "kanban"].forEach(v => {
        const opt = document.createElement("option");
        opt.value = v;
        opt.textContent = v;
        layoutSelect.appendChild(opt);
      });
      layoutWrap.appendChild(layoutSelect);
      body.appendChild(layoutWrap);

      // data_entity_type
      const entityWrap = _mkField("Data entity (table)", "Volitelně. fw.menu_node entity ref. Např. 'user', 'menu_node', 'security_device'.", false);
      const entityInput = document.createElement("input");
      entityInput.type = "text";
      entityInput.style.cssText =
        "padding:8px 10px;background:#0f141a;border:1px solid #3a4754;border-radius:4px;" +
        "color:#e8eef5;font-size:12px;font-family:monospace;outline:none;";
      entityInput.placeholder = "user";
      entityWrap.appendChild(entityInput);
      body.appendChild(entityWrap);

      modal.appendChild(body);

      // Footer
      const footer = document.createElement("div");
      footer.style.cssText =
        "padding:12px 18px;border-top:1px solid #2a3340;display:flex;" +
        "gap:10px;justify-content:flex-end;align-items:center;";

      const cancelBtn = document.createElement("button");
      cancelBtn.type = "button";
      cancelBtn.textContent = "Storno";
      cancelBtn.style.cssText =
        "padding:8px 18px;background:#2a3340;border:1px solid #3a4754;color:#cfd6df;" +
        "border-radius:4px;cursor:pointer;font-size:12px;";
      cancelBtn.onclick = () => overlay.remove();
      footer.appendChild(cancelBtn);

      const createBtn = document.createElement("button");
      createBtn.type = "button";
      createBtn.textContent = "➕ Vytvořit";
      createBtn.style.cssText =
        "padding:8px 18px;background:#2a4760;border:1px solid #4a7ba8;color:#a8c4dc;" +
        "border-radius:4px;cursor:pointer;font-size:12px;font-weight:500;";
      createBtn.onclick = async () => {
        const code = codeInput.value.trim();
        const label = labelInput.value.trim();
        const layoutType = layoutSelect.value;
        const dataEntity = entityInput.value.trim() || null;

        if (!code) { alert("Code je povinný."); codeInput.focus(); return; }
        if (!/^[a-z][a-z0-9_]*$/.test(code)) {
          alert("Code musí být lowercase snake_case (a-z, 0-9, _), začínat písmenem.");
          codeInput.focus();
          return;
        }
        if (!label) { alert("Label je povinný."); labelInput.focus(); return; }

        createBtn.disabled = true;
        createBtn.textContent = "⏳ Vytvářím…";
        try {
          const r = await fetch("/api/v1/erp/design/fw-core", {
            method: "POST",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              code: code,
              label: label,
              layout_type: layoutType,
              data_entity_type: dataEntity,
            }),
          });
          const data = await r.json().catch(() => ({}));
          if (!r.ok || !data.ok) {
            alert("Vytvoření selhalo: " + (data.error || ("HTTP " + r.status)));
            createBtn.disabled = false;
            createBtn.textContent = "➕ Vytvořit";
            return;
          }
          // Success — toast + close create modal
          if (typeof _showToast === "function") {
            _showToast("Core '" + label + "' vytvořen", "success");
          }
          overlay.remove();
          // Refresh picker grid (new row visible)
          if (picker && typeof picker.refresh === "function") {
            await picker.refresh();
          }
        } catch (e) {
          alert("Vytvoření selhalo: " + (e.message || e));
          createBtn.disabled = false;
          createBtn.textContent = "➕ Vytvořit";
        }
      };
      footer.appendChild(createBtn);
      modal.appendChild(footer);

      overlay.appendChild(modal);
      document.body.appendChild(overlay);
      setTimeout(() => codeInput.focus(), 50);
    }

    async _associateCoreWithMenuNode(coreId, coreLabel, overlay) {
      const menuNode = (this._data && this._data.menu_node) || null;
      if (!menuNode || !menuNode.id) {
        alert("Asociace chyba: chybi menu_node ID.");
        return;
      }
      try {
        const r = await fetch(
          "/api/v1/erp/design/menu_node/" + encodeURIComponent(menuNode.id),
          {
            method: "PATCH",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              field_changes: { core_id: coreId },
              expected_updated_at: menuNode.updated_at,
            }),
          }
        );
        if (!r.ok) {
          const errData = await r.json().catch(() => ({}));
          alert("Asociace selhala: " + (errData.error || ("HTTP " + r.status)));
          return;
        }
        if (typeof _showToast === "function") {
          _showToast("Core " + coreLabel + " asociovan", "success");
        }
        if (overlay) overlay.remove();
        // Reload spec — re-render Prehled tab s new core data
        this._dirty.clear();
        _markFormDirty(this, false);
        this._shell.close();
        // Otevri popup znovu (refresh data)
        setTimeout(() => {
          try {
            new window.DesignSoudecekCoreForm({
              menuNodeId: menuNode.id,
              initialTab: "prehled",
            }).open();
          } catch (e) {
            console.error("[CorePicker] re-open failed:", e);
          }
        }, 150);
        // Tree + grid refresh (H+9/H+15 pattern)
        try {
          if (typeof window.reloadErpTree === "function") {
            await window.reloadErpTree();
          }
        } catch (eRefresh) {
          console.warn("[CorePicker] tree refresh failed:", eRefresh);
        }
      } catch (e) {
        alert("Asociace selhala: " + (e.message || e));
      }
    }

    /**
     * Phase 38.4 Krok 14g-H+21 (15.5.2026 ~17:00, Marti's "musi byt tlacitko
     * zrusit"): unassociate core přehled od menu_node. PATCH core_id = NULL.
     * Po success → re-open popup s tab='prehled' = empty state placeholder.
     */
    async _unassociateCore() {
      const menuNode = (this._data && this._data.menu_node) || null;
      const core = (this._data && this._data.core) || null;
      if (!menuNode || !menuNode.id) {
        alert("Chybi menu_node ID.");
        return;
      }
      const ok = confirm(
        "Zrušit asociaci core přehledu '" + (core && core.label || "?") + "' " +
        "od soudečku '" + (menuNode.label || "?") + "'?\n\n" +
        "menu_node.core_id bude NULL. Core sám zůstane v fw.core (může být " +
        "znovu vybrán nebo asociovaný s jiným soudečkem)."
      );
      if (!ok) return;
      try {
        const r = await fetch(
          "/api/v1/erp/design/menu_node/" + encodeURIComponent(menuNode.id),
          {
            method: "PATCH",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              field_changes: { core_id: null },
              expected_updated_at: menuNode.updated_at,
            }),
          }
        );
        if (!r.ok) {
          const errData = await r.json().catch(() => ({}));
          alert("Zrušení selhalo: " + (errData.error || ("HTTP " + r.status)));
          return;
        }
        if (typeof _showToast === "function") {
          _showToast("Asociace zrušena", "success");
        }
        // Re-open popup s tab='prehled' → empty state placeholder
        this._dirty.clear();
        _markFormDirty(this, false);
        this._shell.close();
        setTimeout(() => {
          try {
            new window.DesignSoudecekCoreForm({
              menuNodeId: menuNode.id,
              initialTab: "prehled",
            }).open();
          } catch (e) {
            console.error("[Unassociate] re-open failed:", e);
          }
        }, 150);
        try {
          if (typeof window.reloadErpTree === "function") {
            await window.reloadErpTree();
          }
        } catch (eRefresh) {
          console.warn("[Unassociate] tree refresh failed:", eRefresh);
        }
      } catch (e) {
        alert("Zrušení selhalo: " + (e.message || e));
      }
    }

    // ────────────────────────────────────────────────────────────────────
    // Phase 38.4 Krok 14g-H+30 Etapa 3/4/5 (15.5.2026 vecer, Marti's B
    // varianta dotahnout do finale): data_source picker + unassociate.
    //
    // Etapa 3 stub: alert placeholders → real impl v Etape 4 (picker pres
    // ErpCatalogPicker) + Etape 5 (backend PATCH associate). Etapa 6
    // (➕ Novy data_source button) prijde po picker funkcnim.
    // ────────────────────────────────────────────────────────────────────
    async _openDataSourcePickerModal() {
      // Phase 38.4 Krok 14g-H+30 Etapa 4 (15.5.2026 vecer, Marti's
      // "B varianta dotahnout do finale"): real picker via
      // ErpCatalogPicker (reuse z H+22). On-select zatim placeholder —
      // Etapa 5 (associate backend) prijde dal.
      const menuNode = (this._data && this._data.menu_node) || null;
      const core = (this._data && this._data.core) || null;
      if (!core || !core.id) {
        alert("Picker chyba: chybi core (asociuj nejdriv core v 1. radku).");
        return;
      }
      if (typeof window.ErpCatalogPicker !== "function") {
        alert("ErpCatalogPicker not loaded (catalog_picker.js missing).");
        return;
      }

      // Renderer pro Used by N cores (analog _openCorePickerModal)
      const usedRenderer = function (params) {
        const v = params && params.value;
        if (v && v > 0) {
          return '<span title="Pouzit v ' + v + ' core(s) pres code" ' +
                 'style="color:#7a8696;">🔗 ' + v + '×</span>';
        }
        return '';
      };

      // Renderer pro operation_kinds (compact list)
      const opsRenderer = function (params) {
        const v = params && params.value;
        if (!v) return '<span style="color:#5a6573;">—</span>';
        return '<span style="color:#a8b4c2;font-size:11px;">' + v + '</span>';
      };

      const self = this;
      const coreCode = core.code || "";
      const picker = new window.ErpCatalogPicker({
        title: "🔗 Vybrat existing data_source (vazba pres core.code = '" +
               coreCode + "')",
        endpoint: "/api/v1/erp/design/fw-data-source/list",
        listKey: "data_sources",
        labelField: "name",
        columns: [
          { headerName: "Code", field: "code", width: 220,
            filter: "agTextColumnFilter", sortable: true },
          { headerName: "Nazev", field: "name", flex: 1, minWidth: 200,
            filter: "agTextColumnFilter", sortable: true },
          { headerName: "Refresh", field: "refresh_type", width: 110,
            filter: "agTextColumnFilter", sortable: true },
          { headerName: "Status", field: "status", width: 100,
            filter: "agTextColumnFilter", sortable: true },
          { headerName: "Operations", field: "operation_kinds", flex: 1,
            minWidth: 160, sortable: false, cellRenderer: opsRenderer },
          { headerName: "Ops #", field: "operation_count", width: 80,
            type: "numericColumn", sortable: true },
          { headerName: "v", field: "version", width: 60,
            type: "numericColumn", sortable: true },
          { headerName: "Pouzit ×", field: "is_used_count", width: 100,
            type: "numericColumn", sortable: true, cellRenderer: usedRenderer },
        ],
        onSelect: (row) => {
          // Phase 38.4 Krok 14g-H+30 Etapa 5 (15.5.2026 vecer, Marti's
          // Varianta C "nechat stavajici jak jsou, zacit 1:1 k novemu
          // jadru"): picker je view-only. Pro vytvoreni noveho data_source
          // pro tento core klikni "➕ Novy" v toolbar pickeru.
          alert(
            "📖 View-only browse\n\n" +
            "Vybrane: '" + (row.name || row.code) + "' (id=" + row.id + ")\n\n" +
            "Marti's doctrine 1:1 vazba pres code: kazdy core ma vlastni\n" +
            "data_source s code = core.code. Stavajici data_sources se\n" +
            "nemichaji.\n\n" +
            "Pro vytvoreni noveho data_source pro core '" + coreCode + "'\n" +
            "klikni ➕ Novy vlevo nahore."
          );
        },
        // Phase 38.4 Krok 14g-H+30 Etapa 6 (FINALE): real wizard
        enableNew: true,
        enableEdit: false,
        enableDelete: false,
        onNew: () => self._openDataSourceCreateForm(picker, coreCode),
      });
      picker.open();
    }

    /**
     * Phase 38.4 Krok 14g-H+30 Etapa 6 (15.5.2026 vecer, Marti's Varianta C
     * "1:1 vazba pres code"): mini-form modal pro CREATE fw.data_source.
     * Pre-filled code = core.code (readonly auto-link). Po success refresh
     * picker grid + close picker + reopen Form 1 s tab='prehled'.
     */
    _openDataSourceCreateForm(picker, coreCode) {
      const self = this;
      const menuNode = (this._data && this._data.menu_node) || null;
      const core = (this._data && this._data.core) || null;

      // Mini overlay
      const overlay = document.createElement("div");
      overlay.style.cssText =
        "position:fixed;inset:0;background:rgba(0,0,0,0.6);z-index:10020;" +
        "display:flex;align-items:center;justify-content:center;";

      const modal = document.createElement("div");
      modal.style.cssText =
        "width:520px;max-width:95vw;background:#1a1f26;border:1px solid #2a3340;" +
        "border-radius:6px;display:flex;flex-direction:column;color:#cfd6df;" +
        "font-size:13px;box-shadow:0 8px 32px rgba(0,0,0,0.5);";

      // Header
      const header = document.createElement("div");
      header.style.cssText =
        "padding:14px 18px;border-bottom:1px solid #2a3340;display:flex;" +
        "align-items:center;justify-content:space-between;";
      header.innerHTML =
        '<div style="font-size:14px;font-weight:600;color:#e8eef5;">' +
        '➕ Vytvorit novy datovy zdroj pro core ' +
        '<code style="background:#0f141a;padding:1px 6px;border-radius:3px;' +
        'color:#a8c4dc;font-size:12px;">' + coreCode + '</code></div>';
      const closeBtn = document.createElement("button");
      closeBtn.type = "button";
      closeBtn.textContent = "✕";
      closeBtn.style.cssText =
        "background:none;border:none;color:#7a8696;font-size:18px;cursor:pointer;padding:0 4px;";
      closeBtn.onclick = () => overlay.remove();
      header.appendChild(closeBtn);
      modal.appendChild(header);

      // Body — form fields
      const body = document.createElement("div");
      body.style.cssText = "padding:18px;display:flex;flex-direction:column;gap:14px;";

      const _mkField = (label, hint, isRequired) => {
        const wrap = document.createElement("div");
        wrap.style.cssText = "display:flex;flex-direction:column;gap:4px;";
        const lbl = document.createElement("label");
        lbl.style.cssText = "color:#a8b4c2;font-size:11px;font-weight:500;";
        lbl.innerHTML = label + (isRequired
          ? ' <span style="color:#d4a8a8;">*</span>' : '');
        wrap.appendChild(lbl);
        if (hint) {
          const h = document.createElement("div");
          h.style.cssText = "color:#7a8696;font-size:10px;font-style:italic;";
          h.textContent = hint;
          wrap.appendChild(h);
        }
        return wrap;
      };

      // code (readonly — Marti's 1:1 doctrine, auto-link via code)
      const codeWrap = _mkField(
        "Code (auto-link na core)",
        "Marti's Varianta C: 1:1 vazba pres code. Hodnota = core.code, readonly.",
        true
      );
      const codeInput = document.createElement("input");
      codeInput.type = "text";
      codeInput.value = coreCode;
      codeInput.readOnly = true;
      codeInput.style.cssText =
        "padding:8px 10px;background:#1a2028;border:1px solid #3a4754;border-radius:4px;" +
        "color:#7a8696;font-size:12px;font-family:monospace;outline:none;cursor:not-allowed;";
      codeWrap.appendChild(codeInput);
      body.appendChild(codeWrap);

      // name (required)
      const nameWrap = _mkField(
        "Nazev",
        "Human-readable jmeno datoveho zdroje (UI label). Napr. 'IP whitelists data source'.",
        true
      );
      const nameInput = document.createElement("input");
      nameInput.type = "text";
      nameInput.placeholder = "Nazev datoveho zdroje";
      nameInput.style.cssText =
        "padding:8px 10px;background:#0f141a;border:1px solid #3a4754;border-radius:4px;" +
        "color:#e8eef5;font-size:12px;outline:none;";
      nameWrap.appendChild(nameInput);
      body.appendChild(nameWrap);

      // refresh_type (dropdown)
      const refreshWrap = _mkField(
        "Refresh type",
        "Kdy data_source obnovuje data. 'manual' = vyzaduje user akci. " +
        "'on_open' = pri otevreni gridu. 'interval' = periodicky. " +
        "'on_event' = trigger jinou udalosti. Default 'manual'.",
        false
      );
      const refreshSelect = document.createElement("select");
      refreshSelect.style.cssText =
        "padding:8px 10px;background:#0f141a;border:1px solid #3a4754;border-radius:4px;" +
        "color:#e8eef5;font-size:12px;outline:none;";
      ["manual", "on_open", "interval", "on_event"].forEach(v => {
        const opt = document.createElement("option");
        opt.value = v;
        opt.textContent = v;
        refreshSelect.appendChild(opt);
      });
      refreshSelect.value = "manual";
      refreshWrap.appendChild(refreshSelect);
      body.appendChild(refreshWrap);

      // description (optional textarea)
      const descWrap = _mkField(
        "Popis (optional)",
        "Kratky popis k cemu data_source slouzi. Pro budouci developery / kolegyni.",
        false
      );
      const descInput = document.createElement("textarea");
      descInput.placeholder = "Volitelny popis...";
      descInput.rows = 3;
      descInput.style.cssText =
        "padding:8px 10px;background:#0f141a;border:1px solid #3a4754;border-radius:4px;" +
        "color:#e8eef5;font-size:12px;outline:none;resize:vertical;font-family:inherit;";
      descWrap.appendChild(descInput);
      body.appendChild(descWrap);

      modal.appendChild(body);

      // Footer
      const footer = document.createElement("div");
      footer.style.cssText =
        "padding:12px 18px;border-top:1px solid #2a3340;display:flex;" +
        "gap:10px;justify-content:flex-end;align-items:center;";

      const cancelBtn = document.createElement("button");
      cancelBtn.type = "button";
      cancelBtn.textContent = "Storno";
      cancelBtn.style.cssText =
        "padding:8px 18px;background:#2a3340;border:1px solid #3a4754;color:#cfd6df;" +
        "border-radius:4px;cursor:pointer;font-size:12px;";
      cancelBtn.onclick = () => overlay.remove();
      footer.appendChild(cancelBtn);

      const createBtn = document.createElement("button");
      createBtn.type = "button";
      createBtn.textContent = "➕ Vytvorit";
      createBtn.style.cssText =
        "padding:8px 18px;background:#2a4760;border:1px solid #4a7ba8;color:#a8c4dc;" +
        "border-radius:4px;cursor:pointer;font-size:12px;font-weight:500;";
      createBtn.onclick = async () => {
        const code = codeInput.value.trim();
        const name = nameInput.value.trim();
        const refreshType = refreshSelect.value;
        const description = descInput.value.trim() || null;

        if (!name) { alert("Nazev je povinny."); nameInput.focus(); return; }

        createBtn.disabled = true;
        createBtn.textContent = "⏳ Vytvarim…";
        try {
          const r = await fetch("/api/v1/erp/design/fw-data-source", {
            method: "POST",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              code: code,
              name: name,
              refresh_type: refreshType,
              description: description,
            }),
          });
          const data = await r.json().catch(() => ({}));
          if (!r.ok || !data.ok) {
            alert("Vytvoreni selhalo: " + (data.error || ("HTTP " + r.status)));
            createBtn.disabled = false;
            createBtn.textContent = "➕ Vytvorit";
            return;
          }
          // Success
          if (typeof _showToast === "function") {
            _showToast("Data_source '" + name + "' vytvoren", "success");
          }
          overlay.remove();
          // Close picker (auto-link via code-based vazba — uz je linknuto)
          if (picker && typeof picker.close === "function") {
            picker.close();
          } else if (picker && picker._overlay) {
            picker._overlay.remove();
          }
          // Reload Form 1 — vidime new data_source v 2. groupboxu
          self._dirty.clear();
          _markFormDirty(self, false);
          self._shell.close();
          setTimeout(() => {
            try {
              const reopenOpts = {
                initialTab: "prehled",
              };
              if (menuNode && menuNode.id) {
                reopenOpts.menuNodeId = menuNode.id;
              } else if (core && core.id) {
                reopenOpts.coreId = core.id;
              }
              new window.DesignSoudecekCoreForm(reopenOpts).open();
            } catch (e) {
              console.error("[DataSourceCreate] re-open failed:", e);
            }
          }, 150);
        } catch (e) {
          alert("Vytvoreni selhalo: " + (e.message || e));
          createBtn.disabled = false;
          createBtn.textContent = "➕ Vytvorit";
        }
      };
      footer.appendChild(createBtn);
      modal.appendChild(footer);

      overlay.appendChild(modal);
      document.body.appendChild(overlay);
      setTimeout(() => nameInput.focus(), 50);
    }

    async _unassociateDataSource() {
      // Phase 38.4 Krok 14g-H+30 Etapa 5 (15.5.2026 vecer, Marti's
      // Varianta C "1:1 vazba pres code"): archive data_source where
      // code=core.code. Soft delete (status='archived'), defense in
      // depth — Marti muze kdykoli un-archive pres SQL.
      const dataSource = (this._data && this._data.data_source) || null;
      const core = (this._data && this._data.core) || null;
      if (!dataSource || !dataSource.id) {
        alert("Nelze archivovat: chybi data_source.");
        return;
      }
      const dsLabel = (dataSource.name || dataSource.code || "?");
      const coreLabel = core ? (core.label || core.code || "?") : "?";

      const decision = await _confirmDarkDialog({
        title: "Archivovat datovy zdroj",
        message:
          "Chces archivovat datovy zdroj?\n\n" +
          "  '" + dsLabel + "' (id=" + dataSource.id + ", code='" +
          (dataSource.code || "") + "')\n" +
          "  asociovany s core '" + coreLabel + "'\n\n" +
          "Soft delete: status -> 'archived'. Data zustavaji v DB.\n" +
          "Marti muze un-archivovat pres SQL nebo budouci 🗄️ Archiv tab.",
        ok: "Archivovat",
        cancel: "Zrusit",
      });
      if (decision !== true) return;

      try {
        const r = await fetch(
          "/api/v1/erp/design/fw-data-source/" +
          encodeURIComponent(dataSource.id) + "/archive",
          {
            method: "PATCH",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
          }
        );
        if (!r.ok) {
          const errData = await r.json().catch(() => ({}));
          alert("Archivace selhala: " + (errData.error || ("HTTP " + r.status)));
          return;
        }
        if (typeof _showToast === "function") {
          _showToast("Datovy zdroj archivovan", "success");
        }
        // Re-open Form 1 s tab='prehled' — vidime updated state (data_source=null)
        const menuNode = (this._data && this._data.menu_node) || null;
        this._dirty.clear();
        _markFormDirty(this, false);
        this._shell.close();
        setTimeout(() => {
          try {
            new window.DesignSoudecekCoreForm({
              menuNodeId: menuNode ? menuNode.id : (core ? null : null),
              coreId: !menuNode && core ? core.id : null,
              initialTab: "prehled",
            }).open();
          } catch (e) {
            console.error("[Unassociate DS] re-open failed:", e);
          }
        }, 150);
      } catch (e) {
        alert("Archivace selhala: " + (e.message || e));
      }
    }

    // ────────────────────────────────────────────────────────────────────
    // Phase 38.4 Krok 14g-H+31 step 4 (15.5.2026 vecer, Marti's "stejne
    // ikonky pro Soudecek"): navigation + archive pro soudecekPicker.
    // ────────────────────────────────────────────────────────────────────

    /**
     * Switch na jiny menu_node (z soudecekPicker 🔗 picker). Close current
     * Form 1 + reopen with new menuNodeId. Standard navigation pattern.
     */
    _switchToMenuNode(newMenuNodeId) {
      if (!newMenuNodeId) return;
      const currentMenuNode = (this._data && this._data.menu_node) || null;
      if (currentMenuNode && currentMenuNode.id === newMenuNodeId) {
        // No-op — same menu_node
        return;
      }
      this._dirty.clear();
      _markFormDirty(this, false);
      this._shell.close();
      setTimeout(() => {
        try {
          new window.DesignSoudecekCoreForm({
            menuNodeId: newMenuNodeId,
            initialTab: "prehled",
          }).open();
        } catch (e) {
          console.error("[SoudecekPicker switch] re-open failed:", e);
        }
      }, 150);
    }

    /**
     * Archive aktualni soudecek (menu_node status='archived'). Soft delete
     * pres existing PATCH /design/menu_node/{id} s field_changes.
     * Po success: close Form 1 + reload tree (gone from sidebar).
     */
    async _archiveSoudecek() {
      const menuNode = (this._data && this._data.menu_node) || null;
      if (!menuNode || !menuNode.id) {
        alert("Nelze archivovat: chybi menu_node.");
        return;
      }
      const decision = await _confirmDarkDialog({
        title: "Archivovat soudeček",
        message:
          "Chceš archivovat soudeček?\n\n" +
          "  '" + (menuNode.label || menuNode.code || "?") + "' " +
          "(id=" + menuNode.id + ", code='" + (menuNode.code || "") + "')\n\n" +
          "Soft delete: status -> 'archived'. Data zustavaji v DB.\n" +
          "Soudeček zmizí ze stromu. Marti muze un-archivovat pres SQL nebo\n" +
          "budouci 🗄️ Archiv tab.",
        ok: "Archivovat",
        cancel: "Zrušit",
      });
      if (decision !== true) return;

      try {
        const r = await fetch(
          "/api/v1/erp/design/menu_node/" + encodeURIComponent(menuNode.id),
          {
            method: "PATCH",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              field_changes: { status: "archived" },
              expected_updated_at: menuNode.updated_at,
            }),
          }
        );
        if (!r.ok) {
          const errData = await r.json().catch(() => ({}));
          alert("Archivace selhala: " + (errData.error || ("HTTP " + r.status)));
          return;
        }
        if (typeof _showToast === "function") {
          _showToast("Soudeček archivován", "success");
        }
        this._dirty.clear();
        _markFormDirty(this, false);
        this._shell.close();
        // Reload tree — archived soudeček zmizí
        try {
          if (typeof window.reloadErpTree === "function") {
            await window.reloadErpTree();
          }
        } catch (eRefresh) {
          console.warn("[ArchiveSoudecek] tree refresh failed:", eRefresh);
        }
      } catch (e) {
        alert("Archivace selhala: " + (e.message || e));
      }
    }

    // ────────────────────────────────────────────────────────────────────
    // Phase 38.4 Krok 14g-H+31 step 7 (15.5.2026 vecer, Marti's "pridat
    // tlacitko pro edit"): edit handlery pro 3 pickery. Zatim placeholdery
    // — real edit modal prijde v Krok 14g-H+31 step 8 (po Marti's
    // rozhodnuti jaky scope: full detail vs jen label/description).
    // ────────────────────────────────────────────────────────────────────

    _openCoreEditForm(row) {
      if (!row || !row.id) { alert("Vyber radek pro editaci."); return; }
      alert(
        "✏️ Editovat fw.core\n\n" +
        "Vybrano: '" + (row.label || row.code || "?") + "' (id=" + row.id + ")\n\n" +
        "Edit modal prijde v Krok 14g-H+31 step 8 (TBD scope: label +\n" +
        "description_user + description_system + layout_type? — Marti rozhodne)."
      );
    }

    _openDataSourceEditForm(row) {
      if (!row || !row.id) { alert("Vyber radek pro editaci."); return; }
      alert(
        "✏️ Editovat fw.data_source\n\n" +
        "Vybrano: '" + (row.name || row.code || "?") + "' (id=" + row.id + ")\n\n" +
        "Edit modal prijde v Krok 14g-H+31 step 8.\n" +
        "Pole: name, refresh_type, description, row_memory, filter_delay_ms,\n" +
        "default_record_limit (krome immutable: code, version, status)."
      );
    }

    _openSoudecekEditForm(row) {
      if (!row || !row.id) { alert("Vyber radek pro editaci."); return; }
      alert(
        "✏️ Editovat fw.menu_node\n\n" +
        "Vybrano: '" + (row.label || row.code || "?") + "' (id=" + row.id + ")\n\n" +
        "Edit modal prijde v Krok 14g-H+31 step 8.\n" +
        "Pole: label, parent_id, sort_order, kind, visibility_scope,\n" +
        "description (krome immutable: code, id)."
      );
    }

    // Phase 38.4 Krok 14a-A1m #2 (12.5.2026 odpoledne): 📖 popup pro
    // description memo. Vybere entitu podle aktivniho tabu —
    // Soudecek tab → menu_node, Prehled tab → core.
    _openDescriptionsPopup() {
      // Vyber aktivni entity podle aktivniho tabu PageControl.
      const activeId = this._pc && typeof this._pc.getActiveId === "function"
        ? this._pc.getActiveId() : "soudecek";
      const data = this._data || {};
      let entityKind, entityLabel, descUser, descSystem, entityId;
      if (activeId === "prehled" && data.core && data.core.id) {
        entityKind = "core";
        entityId = data.core.id;
        entityLabel = data.core.label || data.core.code || "(bez labelu)";
        descUser = data.core.description_user;
        descSystem = data.core.description_system;
      } else {
        // Default: Soudecek tab / menu_node
        const mn = data.menu_node || {};
        entityKind = "menu_node";
        entityId = mn.id;
        entityLabel = mn.label || mn.code || "(bez labelu)";
        descUser = mn.description_user;
        descSystem = mn.description_system;
      }
      // Krok 14b+21 (14.5.2026 rano): entityId + onSaved -> popup ma 💾
      // Uložit button + PATCH backend. onSaved updates local spec
      // consistency (no reload nutny).
      const self = this;
      _buildDescriptionsPopup({
        entityKind: entityKind,
        entityId: entityId,
        entityLabel: entityLabel,
        descUser: descUser,
        descSystem: descSystem,
        onDirty: this._onDirty.bind(this),
        onSaved: function(payload) {
          if (entityKind === "core" && self._spec && self._spec.data && self._spec.data.core) {
            self._spec.data.core.description_user = payload.description_user;
            self._spec.data.core.description_system = payload.description_system;
          } else if (entityKind === "menu_node" && self._spec && self._spec.data && self._spec.data.menu_node) {
            self._spec.data.menu_node.description_user = payload.description_user;
            self._spec.data.menu_node.description_system = payload.description_system;
          }
        },
      });
    }

    // Phase 38.4 Krok 14a-A1k #4: před zavřením oken pres ✕ se zeptej,
    // pokud jsou neuložené změny. Dark design, 3 tlačítka.
    async _beforeCloseHandler() {
      if (!this._dirty || this._dirty.size === 0) return "close";
      const count = this._dirty.size;
      // A1q (12.5.2026 vecer): drop "Pole: ..." výpis — Marti's request.
      // Userové konkretním fieldKey názvům (mn.visibility_scope) nerozumí.
      const phrase = count > 1
        ? (count < 5 ? "provedené změny" : "provedených změn")
        : "provedenou změnu";
      // A1t (12.5.2026 vecer doma): Marti's polish — drop 3-button mode.
      // 3 stavy decision:
      //   true (Ano click) → save + close
      //   false (Ne click) → close without save (explicit destructive)
      //   null (Esc / click outside) → keep modal open (invisible cancel)
      const decision = await _confirmDarkDialog({
        title: "Neuložené změny",
        message: "Mám uložit tebou " + phrase + "? (" + count + ")",
      });
      if (decision === true) {
        this._onSaveClick();
        return "save";
      }
      if (decision === false) {
        return "close"; // explicit Ne → zavřít bez uložení
      }
      return "cancel"; // null (Esc / click outside) → keep modal open
    }

    _onRevertClick() {
      // Phase 38.4 Krok 14a-A1f #4: klik na dirty badge — confirm + revert.
      // Krok 14a-A1g #2 (12.5.2026 odpoledne): nahrazujeme native confirm()
      // za dark centered dialog (Marti's polish — UX konzistence).
      if (!this._dirty.size) return;
      const count = this._dirty.size;
      // A1q (12.5.2026 vecer): plural fix (1=zmenu, 2-4=zmeny, 5+=zmen)
      // + drop "Pole: ..." výpis (Marti's request, userove fieldKey nerozumi).
      const _wRevert = count === 1 ? "změnu" : (count < 5 ? "změny" : "změn");
      _confirmDarkDialog({
        title: "Vrátit změny?",
        message: "Vrátit " + count + " " + _wRevert + " do původního stavu?",
        // A1t: default Ano/Ne (Marti's polish — Vrátit/Zrušit lidsky matoucí)
      }).then(ok => {
        if (ok) this._revertAll();
      });
    }

    _revertAll() {
      // Iterace pres vsechny .erp-field-design wrappery v modal body —
      // kazdy ma attached _inst + _origVal + _kind (set v _field/_dropdown/_memo).
      if (!this._shell || !this._shell.body) return;
      const wraps = this._shell.body.querySelectorAll(".erp-field-design");
      wraps.forEach(w => {
        if (!w._inst || w._origVal == null) return;
        try {
          // Set original hodnotu
          if (w._kind === "dropdown") {
            w._inst.setValue(w._origVal);
            // Clear dirty styling (onChange neproběhne při setValue programmatically v některých variantách,
            // tak explicit cleanup)
            if (w._inst.trigger) {
              w._inst.trigger.style.borderLeft = "";
              w._inst.trigger.style.background = "";
            }
          } else {
            // _field / _memo — ErpInput / ErpMemo
            w._inst.setValue(w._origVal);
            const el = w._inst.input || w._inst.textarea;
            if (el) {
              el.style.borderLeft = "";
              el.style.background = "";
            }
          }
        } catch (e) {
          console.warn("revert field failed:", w._fieldKey, e);
        }
      });
      // Clear dirty state + hide save button
      this._dirty.clear();
      if (this._saveBtn) this._saveBtn.style.display = "none";
      if (this._dirtyBadge) {
        this._dirtyBadge.textContent = "";
        this._dirtyBadge.style.display = "none";
      }
    }

    open() {
      // Phase 38.4 Krok 14g-H+31 step 8 (15.5.2026 vecer, Marti's "Prehled
      // je 1. tab"): default na "prehled", "soudecek" jen pokud explicit
      // requested. Zachovava back-compat pro existing callers s initialTab.
      const initialTab = this.opts.initialTab === "soudecek" ? "soudecek" : "prehled";
      // Sjednoceny title napric obema akcemi (tree akce 1 + grid akce 2) —
      // form je stejny, jen jiny default tab. Uzivatel vidi scope (soudecek + core).
      const title = "Design: Soudeček + Core přehledu";

      this._shell = _buildModalShell({
        title: title,
        width: "920px",
        beforeClose: () => this._beforeCloseHandler(),
        // A1r (12.5.2026): cleanup global dirty tracking po close.
        onClose: () => _markFormDirty(this, false),
        // Phase 38.4 Krok 14a-A1m #2: 📖 callback — otevre popup s description
        // memo. Podle aktivniho tabu vybere entity (Soudecek tab → menu_node,
        // Prehled tab → core).
        onShowDescriptions: () => this._openDescriptionsPopup(),
      });
      document.body.appendChild(this._shell.overlay);

      // Loading placeholder
      const loading = document.createElement("div");
      loading.style.cssText = "padding:24px;text-align:center;color:#8a96a4;";
      loading.textContent = "Načítám…";
      this._shell.body.appendChild(loading);

      // Footer — dirty badge (left, clickable → revert) + Save button (hidden) + Zavřít
      this._dirtyBadge = document.createElement("span");
      this._dirtyBadge.style.cssText = "color:#d4b88a;font-size:12px;margin-right:auto;display:none;cursor:pointer;text-decoration:underline;text-decoration-style:dotted;text-underline-offset:3px;";
      this._dirtyBadge.title = "Klik pro vrácení všech změn (po potvrzení)";
      this._dirtyBadge.addEventListener("click", () => this._onRevertClick());
      this._shell.footer.appendChild(this._dirtyBadge);

      this._saveBtn = document.createElement("button");
      this._saveBtn.type = "button";
      this._saveBtn.textContent = "💾 Uložit";
      this._saveBtn.style.cssText = "padding:6px 16px;background:#3a5a3a;border:1px solid #4a7a4a;border-radius:3px;color:#e8eef5;cursor:pointer;font-size:12px;font-weight:600;display:none;";
      this._saveBtn.addEventListener("click", () => this._onSaveClick());
      this._shell.footer.appendChild(this._saveBtn);

      const closeFooter = document.createElement("button");
      closeFooter.type = "button";
      closeFooter.textContent = "Zavřít";
      closeFooter.style.cssText = "padding:6px 16px;background:#2a3340;border:1px solid #3a4754;border-radius:3px;color:#cfd6df;cursor:pointer;font-size:12px;";
      closeFooter.addEventListener("click", () => this._shell.close());
      this._shell.footer.appendChild(closeFooter);

      // Fetch data
      this._fetchData(initialTab);
    }

    _fetchData(initialTab) {
      const id = this.opts.menuNodeId || this.opts.menuNodeCode
        || this.opts.coreId || this.opts.coreCode;
      if (!id) {
        this._showError("Chybí ID — předej menuNodeId, menuNodeCode, coreId nebo coreCode.");
        return;
      }
      // Build URL — backend resolve podle typu identifiku.
      // Vsechny 4 endpointy vraci {menu_node, core, columns} — frontend
      // si poradi (Tab "Soudecek" empty pokud menu_node=null, Tab "Prehled"
      // empty pokud core=null).
      let url;
      if (this.opts.menuNodeId) {
        url = "/api/v1/erp/design/menu-node/" + encodeURIComponent(this.opts.menuNodeId);
      } else if (this.opts.coreId) {
        url = "/api/v1/erp/design/core/" + encodeURIComponent(this.opts.coreId);
      } else if (this.opts.coreCode) {
        url = "/api/v1/erp/design/core-by-code/" + encodeURIComponent(this.opts.coreCode);
      } else {
        url = "/api/v1/erp/design/menu-node-by-code/" + encodeURIComponent(this.opts.menuNodeCode);
      }
      fetch(url, { credentials: "same-origin", cache: "no-store" })
        .then(r => r.ok ? r.json() : r.text().then(t => Promise.reject("HTTP " + r.status + ": " + t)))
        .then(data => {
          this._data = data || {};
          this._render(initialTab);
        })
        .catch(err => {
          console.error("DesignSoudecekCoreForm fetch failed:", err);
          this._showError("Chyba načtení: " + String(err).slice(0, 200));
        });
    }

    _showError(msg) {
      this._shell.body.innerHTML = "";
      const err = document.createElement("div");
      err.style.cssText = "padding:20px;color:#e88;background:#3a1818;border:1px solid #5a2828;border-radius:4px;";
      err.textContent = msg;
      this._shell.body.appendChild(err);
    }

    _render(initialTab) {
      this._shell.body.innerHTML = "";

      // Build 2 tab content divs
      const soudecekDiv = this._buildSoudecekTab();
      const prehledDiv = this._buildPrehledTab();

      // ErpPageControl
      this._pc = new global.ErpPageControl(this._shell.body, {
        tabs: [
          // Phase 38.4 Krok 14g-H+31 step 8 (15.5.2026 vecer, Marti's
          // "Prohod ty dve zalozky"): Prehled je teď 1. tab (primary),
          // Soudecek se stava 2. tabem s názvem "Smazat později" —
          // predprava pro uplne smazani po prenesem parametrizace do
          // Prehled tabu (Marti's dlouhodoba vize).
          { id: "prehled", label: "Přehled", content: prehledDiv },
          { id: "soudecek", label: "Smazat později", content: soudecekDiv },
        ],
        activeId: initialTab,
      });
      // Phase 38.4 Krok 14a-A1e (12.5.2026 odpoledne): TabSheet stable height
      // — Marti's #3 polish: switching tab nemá uskakovat. Set min-height na
      // pageControl content area = vyssi z obou tab obsahu. Computed once
      // po render (oba taby maji content vyrenderovany, jen jeden visible).
      if (this._pc && this._pc.contentArea) {
        // Compute max height pres oba taby (musime docasne unhide oba)
        const maxH = this._computeMaxTabHeight(soudecekDiv, prehledDiv);
        if (maxH > 0) {
          this._pc.contentArea.style.minHeight = maxH + "px";
        }
      }
    }

    _computeMaxTabHeight(...tabContents) {
      // Trick: docasne ukaž každý tab content (hidden = false), zmer scrollHeight,
      // pak vrať zpet. Pages with display:none nemaji computed height.
      let maxH = 0;
      tabContents.forEach(div => {
        if (!div) return;
        const wasHidden = div.hidden;
        const prevDisplay = div.style.display;
        div.hidden = false;
        div.style.display = "block";
        div.style.position = "absolute";
        div.style.visibility = "hidden";
        const h = div.scrollHeight || 0;
        if (h > maxH) maxH = h;
        div.hidden = wasHidden;
        div.style.display = prevDisplay;
        div.style.position = "";
        div.style.visibility = "";
      });
      return maxH;
    }

    _buildSoudecekTab() {
      const root = document.createElement("div");
      root.className = "erp-design-tab-soudecek";
      const mn = (this._data && this._data.menu_node) || {};
      if (!mn || !mn.id) {
        const empty = document.createElement("div");
        empty.style.cssText = "padding:20px;color:#8a96a4;font-style:italic;";
        empty.textContent = "Žádná data pro soudeček (menu_node nenalezeno).";
        root.appendChild(empty);
        return root;
      }

      // Dirty tracking — local closures
      const D = this._onDirty.bind(this);
      const _f = (l, v, key, o) => _field(l, v, Object.assign({fieldKey: key, onDirty: D}, o || {}));
      const _d = (l, v, items, key, o) => _dropdown(l, v, items, Object.assign({fieldKey: key, onDirty: D}, o || {}));

      // Section: Identifikace — ID readonly (PK), Kind je enum dropdown
      // Krok 14a-A1m #1: section title pair (user / system technical name).
      const idSec = _sectionBuild("Identifikace", "fw.menu_node — identita");
      idSec.grid.appendChild(_f("ID (menu_node.id)", mn.id, "mn.id", { mono: true, readonly: true }));
      idSec.grid.appendChild(_f("Code", mn.code, "mn.code", { mono: true }));
      idSec.grid.appendChild(_f("Label", mn.label, "mn.label"));
      idSec.grid.appendChild(_d("Kind", mn.kind, "kind", "mn.kind"));
      root.appendChild(idSec.wrap);

      // Section: Hierarchie — parent_id/parent_code readonly, status/visibility/
      // is_immutable jsou enum dropdowny
      const treeSec = _sectionBuild("Hierarchie a pořadí", "fw.menu_node — tree position + visibility");
      treeSec.grid.appendChild(_f("Parent ID", mn.parent_id, "mn.parent_id", { mono: true, readonly: true }));
      treeSec.grid.appendChild(_f("Parent Code", mn.parent_code, "mn.parent_code", { mono: true, readonly: true }));
      treeSec.grid.appendChild(_f("Sort Order", mn.sort_order, "mn.sort_order", { mono: true }));
      treeSec.grid.appendChild(_d("Status", mn.status, "status", "mn.status"));
      treeSec.grid.appendChild(_d("Visibility Scope", mn.visibility_scope, "visibility_scope", "mn.visibility_scope"));
      treeSec.grid.appendChild(_d("Is Immutable", mn.is_immutable, "bool_ano_ne", "mn.is_immutable"));
      root.appendChild(treeSec.wrap);

      // Section: Core vazba — FK readonly (vybira se pres picker, Krok 14b)
      const coreSec = _sectionBuild("Vazba na Core přehledu", "fw.menu_node — core_id FK + legacy chain");
      coreSec.grid.appendChild(_f("core_id (FK)", mn.core_id, "mn.core_id", { mono: true, readonly: true }));
      coreSec.grid.appendChild(_f("cislo_def (legacy)", mn.cislo_def, "mn.cislo_def", { mono: true, readonly: true }));
      coreSec.grid.appendChild(_f("framework_jadro_id", mn.framework_jadro_id, "mn.framework_jadro_id", { mono: true, readonly: true }));
      coreSec.grid.appendChild(_f("special_handler", mn.special_handler, "mn.special_handler"));
      root.appendChild(coreSec.wrap);

      // Phase 38.4 Krok 14a-A1m #2 (12.5.2026): popis je v separatnim popupu
      // (📖 ikona v header). Zadna inline Popis sekce v form. Krabicka pro
      // detailni popis core / soudecku — obdoba CLAUDE.md per entity.

      return root;
    }

    _buildPrehledTab() {
      // Phase 38.4 Krok 14g-H+31 step 2 (15.5.2026 vecer, Marti's
      // "vyrobit plnohodnotne FW componenty z provizornich inline
      // groupboxu"): full refactor — drop ~178 LOC inline kódu,
      // instantiate 2x ErpEntityPicker (corePicker + dsPicker).
      // Reusable pattern pripraven pro DataSource Operation editor
      // (Krok 14g-H+32: dalsi ErpEntityPicker pro DataSet picker).
      const root = document.createElement("div");
      root.className = "erp-design-tab-prehled";

      // Defensive: pokud entity_picker.js nenacten, ukaz error
      if (typeof window.ErpEntityPicker !== "function") {
        const err = document.createElement("div");
        err.style.cssText =
          "padding:20px;color:#e88;background:#3a1818;border:1px solid #5a2828;" +
          "border-radius:4px;font-size:13px;";
        err.textContent =
          "ErpEntityPicker komponenta nenactena (entity_picker.js missing). " +
          "Zkus hard reload prohlížeč (Ctrl+Shift+R).";
        root.appendChild(err);
        return root;
      }

      const menuNode = (this._data && this._data.menu_node) || null;
      const core = (this._data && this._data.core) || null;
      const hasCore = !!(core && core.id);
      const dataSource = (this._data && this._data.data_source) || null;
      const coreCode = hasCore ? (core.code || "") : "";
      const self = this;

      // Cell renderery sdilene mezi pickery
      const usedRenderer = function (params) {
        const v = params && params.value;
        if (v && v > 0) {
          return '<span title="Pouzit v ' + v + ' core(s)" ' +
                 'style="color:#7a8696;">🔗 ' + v + '×</span>';
        }
        return '';
      };
      const opsRenderer = function (params) {
        const v = params && params.value;
        if (!v) return '<span style="color:#5a6573;">—</span>';
        return '<span style="color:#a8b4c2;font-size:11px;">' + v + '</span>';
      };

      // ─── 0. SoudecekPicker (Soudeček — vazba na menu_node) ─────────────
      // Phase 38.4 Krok 14g-H+31 step 4 (15.5.2026 vecer, Marti's "drop
      // readOnly, dat soudecku stejne ikonky jako Prehled+Datovy zdroj —
      // vzhled sjednoceny, cilem do budoucna je smazat 1. tab Soudecek
      // a mit jen Prehled tab s parametrizaci"): full ErpEntityPicker.
      // - 🔗 Vybrat: switch na jiny menu_node (navigation)
      // - 🚫 Archivovat: soft delete menu_node (status='archived')
      // - ➕ Novy: disabled — pouzij "+ Novy soudecek" v tree footer
      this._soudecekPicker = new window.ErpEntityPicker({
        label: "Soudeček",
        subtitle: "fw.menu_node — aktualne editovany soudecek",
        idLabel: "Číslo",
        nameLabel: "Název soudečku",
        entity: menuNode ? {
          id: menuNode.id,
          name: menuNode.label || menuNode.code,
          code: menuNode.code,
        } : null,
        placeholderText: "(žádný soudeček — Form 3 mode)",
        pickerConfig: {
          title: "🔗 Vybrat jiný soudeček (switch na jiný menu_node)",
          endpoint: "/api/v1/erp/design/menu-nodes",
          listKey: "items",
          labelField: "label",
          // Phase 38.4 Krok 14g-H+31 step 5 (15.5.2026 vecer, Marti's
          // "pro zacatek jen ID + Label fixne, pozdeji ulozeni sestavy"):
          // minimal columns. TODO: persist user sestava (analog grid).
          columns: [
            { headerName: "ID", field: "id", width: 90,
              type: "numericColumn", sortable: true,
              filter: "agNumberColumnFilter" },
            { headerName: "Label", field: "label", flex: 1, minWidth: 240,
              filter: "agTextColumnFilter", sortable: true },
          ],
        },
        onPick: (row) => self._switchToMenuNode(row.id),
        onUnassociate: () => self._archiveSoudecek(),
        // Phase 38.4 Krok 14g-H+31 step 6 (15.5.2026 vecer, Marti's "jedna
        // komponenta pro vsechny 3 pripady"): showCreate=true, onCreate
        // volá existing wizard window._erpOpenNewSoudecekDialog (sjednoceni
        // s "+ Novy soudecek" v tree footer).
        showCreate: true,
        onEdit: (row) => self._openSoudecekEditForm(row),
        onCreate: (picker) => {
          if (typeof window._erpOpenNewSoudecekDialog !== "function") {
            alert(
              "Wizard pro novy soudecek neni nacten.\n\n" +
              "(window._erpOpenNewSoudecekDialog missing — pravdepodobne " +
              "STRATEGIE-API nebyl restartovan po deploy router.py changes.)"
            );
            return;
          }
          // Close picker pred wizard (avoid nesting modals confusion)
          if (picker && typeof picker.close === "function") {
            picker.close();
          } else if (picker && picker._overlay) {
            picker._overlay.remove();
          }
          // Wizard params: defaultParentId = current menuNode parent_id
          // (pokud existuje), onSuccess switch na new menu_node.
          const currentMenuNode = (self._data && self._data.menu_node) || null;
          window._erpOpenNewSoudecekDialog({
            defaultParentId: currentMenuNode
              ? (currentMenuNode.parent_id != null
                  ? currentMenuNode.parent_id
                  : null)
              : null,
            onSuccess: (newId) => {
              if (newId) self._switchToMenuNode(newId);
            },
          });
        },
      });
      this._soudecekPicker.mount(root);

      // ─── 1. CorePicker (Přehled) ──────────────────────────────────
      this._corePicker = new window.ErpEntityPicker({
        label: "Přehled",
        subtitle: "fw.core — vazba na core_id",
        idLabel: "Číslo",
        nameLabel: "Název definice přehledu",
        entity: core ? {
          id: core.id,
          name: core.label || core.code,
          code: core.code,
        } : null,
        placeholderText: "(žádný core — klik 🔗)",
        pickerConfig: {
          title: "🔗 Vybrat existing core přehled",
          endpoint: "/api/v1/erp/design/fw-core/list",
          listKey: "cores",
          labelField: "label",
          columns: [
            { headerName: "Code", field: "code", width: 220,
              filter: "agTextColumnFilter", sortable: true },
            { headerName: "Label", field: "label", flex: 1, minWidth: 200,
              filter: "agTextColumnFilter", sortable: true },
            { headerName: "Layout", field: "layout_type", width: 130,
              filter: "agTextColumnFilter", sortable: true },
            { headerName: "Data entity", field: "data_entity_type", width: 130,
              filter: "agTextColumnFilter", sortable: true },
            { headerName: "v", field: "version", width: 60,
              type: "numericColumn", sortable: true },
            { headerName: "Použit ×", field: "is_used_count", width: 110,
              type: "numericColumn", sortable: true, cellRenderer: usedRenderer },
          ],
        },
        onPick: (row) => self._associateCoreWithMenuNode(row.id, row.label, null),
        onUnassociate: () => self._unassociateCore(),
        onCreate: (picker) => self._openCoreCreateForm(picker),
        onEdit: (row) => self._openCoreEditForm(row),
        showCreate: true,
      });
      this._corePicker.mount(root);

      // ─── 2. DsPicker (Datový zdroj) — gated na hasCore ────────────
      this._dsPicker = new window.ErpEntityPicker({
        label: "Datový zdroj",
        subtitle: "fw.data_source — vazba pres code (s.code = c.code)",
        idLabel: "Číslo",
        nameLabel: "Název datového zdroje",
        entity: dataSource ? {
          id: dataSource.id,
          name: dataSource.name || dataSource.code,
          code: dataSource.code,
        } : null,
        placeholderText: hasCore
          ? "(žádný data_source — klik 🔗)"
          : "(nejdřív vyber core 👆)",
        disabled: !hasCore,
        disabledReason:
          "Datový zdroj se váže na core (přes code).\n" +
          "Nejdřív vyber/vytvoř core přehled v 1. řádku.",
        prefillCode: coreCode,
        pickerConfig: {
          title: "🔗 Vybrat existing data_source (vazba pres core.code = '" +
                 coreCode + "')",
          endpoint: "/api/v1/erp/design/fw-data-source/list",
          listKey: "data_sources",
          labelField: "name",
          columns: [
            { headerName: "Code", field: "code", width: 220,
              filter: "agTextColumnFilter", sortable: true },
            { headerName: "Nazev", field: "name", flex: 1, minWidth: 200,
              filter: "agTextColumnFilter", sortable: true },
            { headerName: "Refresh", field: "refresh_type", width: 110,
              filter: "agTextColumnFilter", sortable: true },
            { headerName: "Status", field: "status", width: 100,
              filter: "agTextColumnFilter", sortable: true },
            { headerName: "Operations", field: "operation_kinds", flex: 1,
              minWidth: 160, sortable: false, cellRenderer: opsRenderer },
            { headerName: "Ops #", field: "operation_count", width: 80,
              type: "numericColumn", sortable: true },
            { headerName: "v", field: "version", width: 60,
              type: "numericColumn", sortable: true },
            { headerName: "Pouzit ×", field: "is_used_count", width: 100,
              type: "numericColumn", sortable: true, cellRenderer: usedRenderer },
          ],
          onSelect: (row) => {
            // Marti's Varianta C — view-only browse
            alert(
              "📖 View-only browse\n\n" +
              "Vybrane: '" + (row.name || row.code) + "' (id=" + row.id + ")\n\n" +
              "Marti's doctrine 1:1 vazba pres code: kazdy core ma vlastni\n" +
              "data_source s code = core.code. Stavajici data_sources se\n" +
              "nemichaji.\n\n" +
              "Pro vytvoreni noveho data_source pro core '" + coreCode + "'\n" +
              "klikni ➕ Novy vlevo nahore."
            );
          },
        },
        onUnassociate: () => self._unassociateDataSource(),
        onCreate: (picker) => self._openDataSourceCreateForm(picker, coreCode),
        onEdit: (row) => self._openDataSourceEditForm(row),
        showCreate: true,
      });
      this._dsPicker.mount(root);

      // Note: popis (📖 popup) zustava v header (separate flow).
      // _openCorePickerModal + _openDataSourcePickerModal jsou nyni
      // dead code (logic moved into ErpEntityPicker.pickerConfig).
      // Cleanup v separate commitu po smoke test.

      return root;
    }
  }

  // ────────────────────────────────────────────────────────────────────
  // Form 3: Jadro pro radek (1 tab MVP, prepared for expansion)
  // ────────────────────────────────────────────────────────────────────

  class DesignJadroRadekForm {
    constructor(opts) {
      this.opts = opts || {};
      // opts.gridCode (required)   - fw.core.code
      // opts.rowId (required)      - id radku v gridu (pro budoucy form open)
      // opts.compDefId (optional)  - sloupec kde Marti kliknul
      // opts.headerName (optional) - human-readable z header textu
      this._shell = null;
      this._pc = null;
      this._data = null;
      // Phase 38.4 Krok 14a-A1d: dirty tracking
      this._dirty = new Set();
      this._saveBtn = null;
      this._dirtyBadge = null;
    }

    _onDirty(fieldKey, isDirty) {
      if (isDirty) this._dirty.add(fieldKey);
      else this._dirty.delete(fieldKey);
      const count = this._dirty.size;
      if (this._saveBtn) this._saveBtn.style.display = count > 0 ? "" : "none";
      if (this._dirtyBadge) {
        // A1q (12.5.2026 vecer): Czech plural fix — Marti's polish.
        // 1 = "změna", 2-4 = "změny", 5+ = "změn".
        const _wBadge = count === 1 ? "změna" : (count < 5 ? "změny" : "změn");
        this._dirtyBadge.textContent = count > 0
          ? "● " + count + " " + _wBadge
          : "";
        this._dirtyBadge.style.display = count > 0 ? "" : "none";
      }
      // A1r (12.5.2026 vecer): global dirty tracking pro F5/tab close warning.
      _markFormDirty(this, count > 0);
    }

    _onSaveClick() {
      const fields = Array.from(this._dirty).join(", ");
      alert(
        "Save flow přijde v Kroku 14b (backend POST endpointy).\n\n" +
        "Změněná pole (zatím nejsou ukládána):\n" + fields
      );
    }

    // Phase 38.4 Krok 14a-A1m #2: 📖 popup pro description memo.
    // Form 3 ma jednu entity (core), tedy bez tab-aware vyberu.
    _openDescriptionsPopup() {
      const core = (this._data && this._data.core) || null;
      if (!core || !core.id) {
        _confirmDarkDialog({
          title: "Popis není k dispozici",
          message: "Tento grid nemá záznam v fw.core (hardcoded view).\nPopis bude k dispozici, až mu vytvoříme core entry.",
          ok: "OK",
          cancel: null,
        });
        return;
      }
      // Krok 14b+21 (14.5.2026 rano): entityId + onSaved
      const self = this;
      _buildDescriptionsPopup({
        entityKind: "core",
        entityId: core.id,
        entityLabel: core.label || core.code || "(bez labelu)",
        descUser: core.description_user,
        descSystem: core.description_system,
        onDirty: this._onDirty.bind(this),
        onSaved: function(payload) {
          if (self._data && self._data.core) {
            self._data.core.description_user = payload.description_user;
            self._data.core.description_system = payload.description_system;
          }
        },
      });
    }

    // Phase 38.4 Krok 14a-A1k #4: před zavřením oken pres ✕ se zeptej,
    // pokud jsou neuložené změny. Dark design, 3 tlačítka.
    async _beforeCloseHandler() {
      if (!this._dirty || this._dirty.size === 0) return "close";
      const count = this._dirty.size;
      // A1q (12.5.2026 vecer): drop "Pole: ..." výpis — Marti's request.
      // Userové konkretním fieldKey názvům (mn.visibility_scope) nerozumí.
      const phrase = count > 1
        ? (count < 5 ? "provedené změny" : "provedených změn")
        : "provedenou změnu";
      // A1t (12.5.2026 vecer doma): Marti's polish — drop 3-button mode.
      // 3 stavy decision:
      //   true (Ano click) → save + close
      //   false (Ne click) → close without save (explicit destructive)
      //   null (Esc / click outside) → keep modal open (invisible cancel)
      const decision = await _confirmDarkDialog({
        title: "Neuložené změny",
        message: "Mám uložit tebou " + phrase + "? (" + count + ")",
      });
      if (decision === true) {
        this._onSaveClick();
        return "save";
      }
      if (decision === false) {
        return "close"; // explicit Ne → zavřít bez uložení
      }
      return "cancel"; // null (Esc / click outside) → keep modal open
    }

    open() {
      const title = "Design: Jádro pro řádek";
      this._shell = _buildModalShell({
        title: title,
        width: "920px",
        beforeClose: () => this._beforeCloseHandler(),
        // A1r (12.5.2026): cleanup global dirty tracking po close.
        onClose: () => _markFormDirty(this, false),
        // Krok 14a-A1m #2: 📖 callback — otevre popup s description memo.
        onShowDescriptions: () => this._openDescriptionsPopup(),
      });
      document.body.appendChild(this._shell.overlay);

      const loading = document.createElement("div");
      loading.style.cssText = "padding:24px;text-align:center;color:#8a96a4;";
      loading.textContent = "Načítám…";
      this._shell.body.appendChild(loading);

      // Footer — dirty badge + Save (hidden) + Zavřít
      this._dirtyBadge = document.createElement("span");
      this._dirtyBadge.style.cssText = "color:#d4b88a;font-size:12px;margin-right:auto;display:none;";
      this._shell.footer.appendChild(this._dirtyBadge);

      this._saveBtn = document.createElement("button");
      this._saveBtn.type = "button";
      this._saveBtn.textContent = "💾 Uložit";
      this._saveBtn.style.cssText = "padding:6px 16px;background:#3a5a3a;border:1px solid #4a7a4a;border-radius:3px;color:#e8eef5;cursor:pointer;font-size:12px;font-weight:600;display:none;";
      this._saveBtn.addEventListener("click", () => this._onSaveClick());
      this._shell.footer.appendChild(this._saveBtn);

      const closeFooter = document.createElement("button");
      closeFooter.type = "button";
      closeFooter.textContent = "Zavřít";
      closeFooter.style.cssText = "padding:6px 16px;background:#2a3340;border:1px solid #3a4754;border-radius:3px;color:#cfd6df;cursor:pointer;font-size:12px;";
      closeFooter.addEventListener("click", () => this._shell.close());
      this._shell.footer.appendChild(closeFooter);

      this._fetchData();
    }

    _fetchData() {
      const gridCode = this.opts.gridCode;
      if (!gridCode) {
        this._showError("Chybí gridCode (fw.core.code).");
        return;
      }
      // Phase 38.4 Krok 14b (12.5.2026 ~23:30): Marti's bug catch —
      // pred fix fetched /design/core-by-code/{grid} (= list core), now
      // fetches /design/form-core-for-grid/{grid} → vrací form_core nebo
      // empty state s entity_type + suggested_form_code (pro scaffold akci).
      const url = "/api/v1/erp/design/form-core-for-grid/" + encodeURIComponent(gridCode);
      fetch(url, { credentials: "same-origin", cache: "no-store" })
        .then(r => r.ok ? r.json() : r.text().then(t => Promise.reject("HTTP " + r.status + ": " + t)))
        .then(data => {
          this._data = data || {};
          this._render();
        })
        .catch(err => {
          console.error("DesignJadroRadekForm fetch failed:", err);
          this._showError("Chyba načtení: " + String(err).slice(0, 200));
        });
    }

    _showError(msg) {
      this._shell.body.innerHTML = "";
      const err = document.createElement("div");
      err.style.cssText = "padding:20px;color:#e88;background:#3a1818;border:1px solid #5a2828;border-radius:4px;";
      err.textContent = msg;
      this._shell.body.appendChild(err);
    }

    _render() {
      this._shell.body.innerHTML = "";

      const jadroDiv = this._buildJadroTab();

      this._pc = new global.ErpPageControl(this._shell.body, {
        tabs: [
          { id: "jadro", label: "Jádro", content: jadroDiv },
          // Future taby (Krok 14c+): Workflow, Audit, Validace
        ],
        activeId: "jadro",
      });
    }

    _buildJadroTab() {
      const root = document.createElement("div");
      root.className = "erp-design-tab-jadro";

      // Dirty tracking closures
      const D = this._onDirty.bind(this);
      const _f = (l, v, key, o) => _field(l, v, Object.assign({fieldKey: key, onDirty: D}, o || {}));
      const _d = (l, v, items, key, o) => _dropdown(l, v, items, Object.assign({fieldKey: key, onDirty: D}, o || {}));

      // Section: Kontext kliku — vsechno readonly (jen orientacni informace)
      // Krok 14a-A1m #1: section title pair (UI state, no DB)
      // Krok 14b (12.5.2026 ~23:30): plus data_entity_type z list core
      // (po refactoru _fetchData → /form-core-for-grid endpoint)
      // Krok 14b-4 (12.5.2026 ~23:45): plus list_core.id + list_core.code
      // (Marti's "ID 11" catch — primary info, alias je secondary)
      const ctxSec = _sectionBuild("Kontext kliku v gridu", "UI state (gridCode + rowId + headerName + compDefId)");
      const listCore = (this._data && this._data.list_core) || null;
      ctxSec.grid.appendChild(_f("List core ID", listCore ? listCore.id : null, "ctx.listCoreId", { mono: true, readonly: true }));
      ctxSec.grid.appendChild(_f("List core (skutečný kód)", listCore ? listCore.code : null, "ctx.listCoreCode", { mono: true, readonly: true }));
      ctxSec.grid.appendChild(_f("Grid (layout alias)", this.opts.gridCode, "ctx.gridCode", { mono: true, readonly: true }));
      ctxSec.grid.appendChild(_f("Řádek (ID)", this.opts.rowId, "ctx.rowId", { mono: true, readonly: true }));
      ctxSec.grid.appendChild(_f("Klepnutý sloupec", this.opts.headerName, "ctx.headerName", { readonly: true }));
      ctxSec.grid.appendChild(_f("comp_def_id sloupce", this.opts.compDefId, "ctx.compDefId", { mono: true, readonly: true }));
      const entityType = (this._data && this._data.entity_type) || null;
      ctxSec.grid.appendChild(_f("Typ datové entity", entityType, "ctx.entityType", { mono: true, readonly: true }));
      root.appendChild(ctxSec.wrap);

      // Section: Jadro identita — pro FORM core (ne list core!).
      // Phase 38.4 Krok 14b (12.5.2026 ~23:30): Marti's bug catch fix —
      // pred refactor zobrazoval list core (security_users, id=11, layout=list)
      // jako "Jádro pro řádek identita", což bylo semanticky nesprávné.
      // Po refactor: form_core (kind='form', data_entity_type matches list).
      // Pokud form_core neexistuje → empty state s "Vytvoř form detail" button.
      const formCore = (this._data && this._data.form_core) || null;
      const found = !!(this._data && this._data.found);
      const suggestedCode = (this._data && this._data.suggested_form_code) || null;

      if (found && formCore && formCore.id) {
        // Form core existuje — render identitu (existing pattern)
        const idSec = _sectionBuild("Jádro pro řádek — identita", "fw.core — identita + layout + version");
        idSec.grid.appendChild(_f("ID", formCore.id, "form_core.id", { mono: true, readonly: true }));
        idSec.grid.appendChild(_f("Code", formCore.code, "form_core.code", { mono: true }));
        idSec.grid.appendChild(_f("Label", formCore.label, "form_core.label"));
        idSec.grid.appendChild(_d("Layout type", formCore.layout_type, "layout_type", "form_core.layout_type"));
        idSec.grid.appendChild(_f("Data entity type", formCore.data_entity_type, "form_core.data_entity_type", { mono: true }));
        idSec.grid.appendChild(_f("Layout template", formCore.layout_template, "form_core.layout_template", { mono: true }));
        idSec.grid.appendChild(_f("Version", formCore.version, "form_core.version", { mono: true, readonly: true }));
        root.appendChild(idSec.wrap);

        // Krok 14a-A1m #2: popis v separatnim popupu (📖 ikona v header).
      } else {
        // Form core neexistuje → Marti's "Vytvoř form detail" vychytávka.
        // Phase 38.4 Krok 14b-3 (12.5.2026 ~23:30): empty state s placeholder
        // button. Backend scaffold POST endpoint v Krok 14b-4 (next commit).
        const emptySec = _sectionBuild("Jádro pro řádek — identita", "fw.core form — zatím neexistuje");
        const wrap = document.createElement("div");
        wrap.style.cssText = "padding:20px;text-align:center;grid-column:1/-1;";

        const hint = document.createElement("div");
        hint.style.cssText = "color:#8a96a4;font-size:13px;line-height:1.6;margin-bottom:16px;";
        if (entityType) {
          hint.innerHTML =
            "Tento grid (<code style='color:#cfd6df;'>" +
            _esc(this.opts.gridCode || "?") +
            "</code>) zatím nemá <strong>form detail</strong>." +
            "<br>Klik založí <code style='color:#cfd6df;'>fw.core (" +
            _esc(suggestedCode || "?") +
            ")</code> + <code style='color:#cfd6df;'>fw.comp_def form 302</code> root s defaultním panelem <em>Obsah</em>.";
        } else {
          hint.innerHTML =
            "Tento grid (<code style='color:#cfd6df;'>" +
            _esc(this.opts.gridCode || "?") +
            "</code>) nemá nastavený <strong>typ datové entity</strong>." +
            "<br>Bez něj nelze založit form detail. Doplň <code style='color:#cfd6df;'>data_entity_type</code> v list core přes <em>Design: Core přehledu</em>.";
        }
        wrap.appendChild(hint);

        if (entityType) {
          const btn = document.createElement("button");
          btn.type = "button";
          btn.textContent = "🪄 Vytvoř form detail";
          btn.style.cssText =
            "padding:10px 24px;background:#3a5a3a;border:1px solid #4a7a4a;" +
            "border-radius:4px;color:#e8eef5;cursor:pointer;font-size:13px;" +
            "font-weight:600;box-shadow:0 2px 6px rgba(0,0,0,0.3);";
          btn.title = "POST /api/v1/erp/design/scaffold-form — atomic INSERT fw.core + fw.comp_def form 302";
          // Phase 38.4 Krok 14b-4 (12.5.2026 ~23:45): scaffold POST wire-up.
          // Marti's vize "Tim bychom meli vyhrano" — 1 klik = celý form
          // detail vytvořený. Atomic, idempotent (pokud existuje, vrátí
          // existing). Po success reload _fetchData() → re-render with
          // new form core identity.
          btn.addEventListener("click", async () => {
            btn.disabled = true;
            btn.textContent = "⏳ Vytvářím...";
            try {
              const payload = {
                entity_type: entityType,
                suggested_code: suggestedCode,
                list_core_id: listCore ? listCore.id : null,
                list_core_code: listCore ? listCore.code : null,
              };
              const resp = await fetch("/api/v1/erp/design/scaffold-form", {
                method: "POST",
                credentials: "same-origin",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
              });
              if (!resp.ok) {
                const errBody = await resp.json().catch(() => ({}));
                throw new Error("HTTP " + resp.status + ": " + (errBody.error || resp.statusText));
              }
              const result = await resp.json();
              if (!result.ok) {
                throw new Error(result.error || "Unknown backend error");
              }
              // Success — show toast + reload
              const msg = result.existing
                ? "📂 Form detail '" + result.core_code + "' už existoval — otevírám."
                : "✅ Form detail '" + result.core_code + "' vytvořen (core_id=" + result.core_id + ", form_id=" + result.form_id + ").";
              // Simple inline notification (no Material toast — drobnost MVP)
              btn.style.background = "#2d5a2d";
              btn.textContent = msg;
              // Reload data + re-render after short pause
              setTimeout(() => {
                this._fetchData();
              }, 1200);
            } catch (e) {
              console.error("Scaffold form failed:", e);
              btn.disabled = false;
              btn.style.background = "#5a3a3a";
              btn.textContent = "❌ " + e.message.slice(0, 80);
              setTimeout(() => {
                btn.disabled = false;
                btn.style.background = "#3a5a3a";
                btn.textContent = "🪄 Vytvoř form detail";
              }, 4000);
            }
          });
          wrap.appendChild(btn);
        }

        emptySec.grid.appendChild(wrap);
        root.appendChild(emptySec.wrap);
      }

      // Section: Picker poli (placeholder Krok 14c)
      // Krok 14a-A1m #1: section title pair.
      const pickerSec = _sectionBuild("Výběr polí pro formulář", "fw.comp_def + fw.entity_def attributes (Krok 14c)");
      const pickerHint = document.createElement("div");
      pickerHint.style.cssText = "padding:14px;background:#0f141a;border:1px dashed #2a3340;border-radius:4px;color:#5d6975;font-style:italic;text-align:center;grid-column:1/-1;";
      pickerHint.textContent = "Vlevo dostupná pole (entity_def attributes), vpravo vybraná pro form. Drag-drop nebo dvojklik. Implementace v Kroku 14c.";
      pickerSec.grid.appendChild(pickerHint);
      root.appendChild(pickerSec.wrap);

      // Section: Data source (placeholder)
      const dsSec = _sectionBuild("Data — odkud čte, kam zapisuje", "fw.data_set + fw.data_source + fw.data_source_op (Krok 14b)");
      const dsHint = document.createElement("div");
      dsHint.style.cssText = "padding:14px;background:#0f141a;border:1px dashed #2a3340;border-radius:4px;color:#5d6975;font-style:italic;text-align:center;grid-column:1/-1;";
      dsHint.textContent = "fw.data_source linkovaný k tomuto jádru pro zápis. Mode: insert / update / upsert. Implementace v Kroku 14b.";
      dsSec.grid.appendChild(dsHint);
      root.appendChild(dsSec.wrap);

      return root;
    }
  }

  // ────────────────────────────────────────────────────────────────────
  // Phase 38.4 Krok 14b (12.5.2026 vecer): DesignFwForm — generic
  // fw-native form renderer.
  //
  // Marti's pivot z 12.5. večera: dogfooding fw framework. Marti-AI's
  // flat-data doctrine: panels jsou v form's layout JSONB metadata,
  // fields mají region_slot=panel_slot. Žádný container comp_def per
  // panel — drží *„Container = Panel"* + *„Panel je v form template
  // embedded"* doctrines (Marti 12.5. ~21:30).
  //
  // Backend endpoint: GET /api/v1/erp/fw-form/{core_code}/{row_id}
  // Returns: {ok, core, form, fields, data}
  //
  // Rendering flow:
  //   1. Fetch backend → spec + data
  //   2. Iterate form.layout.panels → vyrender section header per panel
  //   3. Group fields by region_slot → render each field do svého panelu
  //   4. Per field: switch comp_type_code → _field (edit) / _dropdown (combobox)
  //
  // Read-only zatím (Phase 38.4 Krok 14b save flow ráno přes PATCH).
  // ────────────────────────────────────────────────────────────────────

  class DesignFwForm {
    constructor(opts) {
      this.opts = opts || {};
      // Phase 38.4 Krok 14g Etapa F Step E.1 (16.5.2026, Marti's "pro jistotu
      // o vikendu"): drop coreCode EXTERNAL — constructor refuses coreCode
      // parameter. Pokud caller jeste posila coreCode, console.error +
      // _erpLogToDb error event (visible v fw.diag_log).
      //
      // Internal: open() lazy-resolves coreCode-from-coreId pres /fw-form/by-id
      // endpoint pro subsequent URL builds (children/save/refresh).
      //
      // Constructor signature:
      //   opts.coreId   (required — fw.core.id, e.g. 22)
      //   opts.rowId    (required — data row ID, e.g. users.id=14)
      if (this.opts.coreCode && !this.opts.coreId) {
        const _errMsg = "DesignFwForm: coreCode parameter NOT SUPPORTED (Etapa F Step E.1 drop). Pass coreId instead.";
        console.error(_errMsg);
        if (typeof window !== "undefined" && window._erpLogToDb) {
          try {
            window._erpLogToDb.error("design_forms.js", _errMsg, {
              extra: { passed_coreCode: this.opts.coreCode, passed_rowId: this.opts.rowId },
            });
          } catch (e) { /* fail-safe */ }
        }
        // Constructor must not throw (existing flow chains .open() — let validation
        // handle it in open()). Mark coreId missing for open() to bail.
        this.opts._etapaFInvalid = true;
      } else if (!this.opts.coreId) {
        console.error("DesignFwForm: coreId required");
        this.opts._etapaFInvalid = true;
      }
      this._shell = null;
      this._spec = null;       // backend response: {core, form, fields, data}
      this._dirty = new Set();
      this._saveBtn = null;
      this._dirtyBadge = null;
      // Phase 38.4 Krok 14b+7 (13.5.2026 ~20:00, Marti's "PROD/DESIGN
      // trigger i na tom formu"): per-form mode flag, separate od
      // window._erpDesignMode (global). Default PRODUCTION (safe — uzivatel
      // otevre form, nesahá na strukturu nahodne). DESIGN mode aktivuje
      // field picker + design-only UI. Toggle button v header (visible
      // jen pokud global _erpDesignMode = true).
      this._formDesignMode = false;
      this._formDesignToggle = null;  // ref na button v header
    }

    // Phase 38.4 Krok 14b+7: helper pro UI re-render po toggle change.
    // Re-render je nutny aby empty hint, field actions, drag handles, atd.
    // reaktivne reflektovaly novy mode. Toggle se sama nepre-render — to
    // udela _updateFormDesignToggle.
    _setFormDesignMode(on) {
      this._formDesignMode = !!on;
      this._updateFormDesignToggle();
      this._updateFormAddFieldBtn();  // Krok 14b+7.1: "+ Pole" button visibility
      this._updateFormEntityBtn();    // Krok 5.F: 🎯 Entita button visibility
      this._updateFormSaveSizeBtn();  // Krok 14b+11: 💾 Velikost button visibility
      this._updateFormDetectMinBtn(); // Krok 14b+12: 📐 Min button visibility
      if (this._spec) {
        // Re-render body (zachovat header) — hints + click handlers nove
        this._render();
      }
    }

    _updateFormDesignToggle() {
      if (!this._formDesignToggle) return;
      const on = this._formDesignMode;
      this._formDesignToggle.textContent = on ? "🎨 DESIGN" : "📋 PRODUCTION";
      this._formDesignToggle.title = on
        ? "Form je v DESIGN módu — můžeš přidávat pole + editovat strukturu. Klikni pro PRODUCTION."
        : "Form je v PRODUCTION módu — jen edit dat. Klikni pro DESIGN (přidávání polí).";
      // Vizuálně: DESIGN = teal akcent (analog global DESIGN badge),
      // PRODUCTION = neutral šedý.
      this._formDesignToggle.style.cssText =
        "background:" + (on ? "#1f4858" : "#1f2530") + ";" +
        "border:1px solid " + (on ? "#3a8aa8" : "#2a3340") + ";" +
        "color:" + (on ? "#7ed4e8" : "#cfd6df") + ";" +
        "padding:4px 10px;border-radius:3px;cursor:pointer;font-size:11px;" +
        "font-weight:" + (on ? "600" : "400") + ";";
    }

    // ════════════════════════════════════════════════════════════════
    // Phase 38.4 Krok 14g-D (15.5.2026 rano, Marti's volba A "simple
    // undo, jeden dva kroky zpet a je happy"): memory-only operation
    // history. Per-session, no DB persist.
    //
    // _undoStack = array of { label, inverse } entries (max 15)
    // _pushUndoOp called BEFORE destructive action, snapshots state.
    // _performUndo pops last + executes inverse, reload spec.
    //
    // Coverage:
    //   - Delete → inverse: PATCH is_active=true
    //   - Move (cross-parent) → inverse: PATCH parent + sort_order back
    //   - Reorder (same-parent) → inverse: PUT field_orders s old order
    //   - Settings save → inverse: PATCH caption + layout back
    //   - Create from gallery → inverse: DELETE new id
    // ════════════════════════════════════════════════════════════════
    _ensureUndoStack() {
      if (!Array.isArray(this._undoStack)) this._undoStack = [];
    }

    _pushUndoOp(label, inverse) {
      this._ensureUndoStack();
      this._undoStack.push({ label, inverse });
      // Keep max 15 (drop oldest)
      if (this._undoStack.length > 15) {
        this._undoStack.shift();
      }
      this._updateUndoButton();
    }

    _updateUndoButton() {
      const btn = this._formUndoBtn;
      if (!btn) return;
      this._ensureUndoStack();
      const n = this._undoStack.length;
      if (n === 0) {
        btn.style.opacity = "0.4";
        btn.disabled = true;
        btn.textContent = "↶ Zpět";
        btn.title = "Žádná akce k vrácení";
      } else {
        btn.style.opacity = "1";
        btn.disabled = false;
        btn.textContent = "↶ Zpět (" + n + ")";
        const last = this._undoStack[n - 1];
        btn.title = "Vrátit: " + last.label + " (Ctrl+Z)";
      }
    }

    async _performUndo() {
      this._ensureUndoStack();
      if (this._undoStack.length === 0) {
        _showToast("Nic k vrácení", "info", 1500);
        return;
      }
      const op = this._undoStack.pop();
      this._updateUndoButton();
      try {
        _showToast("Vracím: " + op.label, "info", 1500);
        await op.inverse();
        _showToast("✓ Vráceno: " + op.label, "success", 2000);
        await this._reloadSpec();
      } catch (e) {
        console.error("[DesignFwForm] undo failed:", e);
        _showToast("Vrácení selhalo: " + (e.message || e), "error", 3500);
        // Push back na stack (preserve order pokud user chce retry)
        this._undoStack.push(op);
        this._updateUndoButton();
      }
    }

    _attachFormDesignToggle() {
      // Krok 14b+7: toggle button visible jen pokud global ERP DESIGN
      // je ON. Bez global flagu form je vzdy PRODUCTION (zadny toggle
      // available — uzivatel nesmi sahat na strukturu).
      if (!this._shell || !this._shell.header) return;
      if (window._erpDesignMode !== true) return;  // gate
      const rightActions = this._shell.header.querySelector(".erp-modal-header-actions");
      if (!rightActions) return;
      // Defensive: nepridavat duplikat (pri opt-out / re-open)
      if (rightActions.querySelector(".erp-form-design-toggle")) return;

      // Toggle button — PROD / DESIGN switch
      const toggle = document.createElement("button");
      toggle.type = "button";
      toggle.className = "erp-form-design-toggle";
      this._formDesignToggle = toggle;
      this._updateFormDesignToggle();  // initial text + style
      toggle.addEventListener("click", () => {
        this._setFormDesignMode(!this._formDesignMode);
      });

      // Krok 14b+7.1 (13.5.2026 ~20:30, Marti's "po pridani 1 pole hint
      // zmizi, nikde jinde nelze pridat"): "+ Pole" button vedle toggle.
      // Visible JEN v DESIGN mode. Klik -> _openFieldPicker (vsechny entry
      // points -- empty hint, footer hint, header button -- volaji stejnou
      // logiku).
      const addBtn = document.createElement("button");
      addBtn.type = "button";
      addBtn.className = "erp-form-design-addfield";
      addBtn.textContent = "➕ Pole";
      addBtn.title = "Přidat pole do formuláře (otevře paletu komponent).";
      this._formAddFieldBtn = addBtn;
      this._updateFormAddFieldBtn();  // initial visibility (hidden bo PRODUCTION default)
      addBtn.addEventListener("click", () => {
        this._openFieldPicker();
      });

      // Krok 14b+11 (13.5.2026 ~23:00, Marti's "ukladat vychozi velikost
      // formu"): 💾 Velikost button. Visible jen v DESIGN mode. Click ->
      // getBoundingClientRect aktualniho dialogu -> PATCH form layout
      // JSONB s default_width + default_height -> toast.
      const saveSizeBtn = document.createElement("button");
      saveSizeBtn.type = "button";
      saveSizeBtn.className = "erp-form-design-savesize";
      saveSizeBtn.textContent = "💾 Velikost";
      saveSizeBtn.title = "Uložit aktuální výšku a šířku jako výchozí pro tento formulář.";
      this._formSaveSizeBtn = saveSizeBtn;
      this._updateFormSaveSizeBtn();  // initial visibility
      saveSizeBtn.addEventListener("click", () => {
        this._saveFormDefaultSize();
      });

      // Krok 14b+12 (13.5.2026 ~23:30, Marti's "detekovat min velikost"):
      // 📐 Min button. Auto-detect kde fields zacnou "ukrajovat"
      // (overflow). Iterate decrement width od current down po 20px until
      // scrollWidth > clientWidth. Save layout.min_width / _height.
      const detectMinBtn = document.createElement("button");
      detectMinBtn.type = "button";
      detectMinBtn.className = "erp-form-design-detectmin";
      detectMinBtn.textContent = "📐 Min";
      detectMinBtn.title = "Auto-detekce minimální velikosti formuláře — najít hranici kde komponenty začnou být ukrojené.";
      this._formDetectMinBtn = detectMinBtn;
      this._updateFormDetectMinBtn();
      detectMinBtn.addEventListener("click", () => {
        this._detectAndSaveMinSize();
      });

      // Phase 38.4 Krok 14g-D (15.5.2026 rano, Marti's volba A simple
      // undo): ↶ Zpět button. Visible jen v DESIGN mode. Click → pop
      // last undoStack entry + execute inverse.
      const undoBtn = document.createElement("button");
      undoBtn.type = "button";
      undoBtn.className = "erp-form-design-undo";
      undoBtn.textContent = "↶ Zpět";
      this._formUndoBtn = undoBtn;
      this._updateUndoButton();  // initial: opacity 0.4 / disabled
      undoBtn.addEventListener("click", () => {
        this._performUndo();
      });

      // Phase 38.4 Krok 14g Etapa F Krok 5.F (16.5.2026 odpoledne, Marti's
      // "schazi Pole + magic"): 🎯 Entita button. Visible jen v DESIGN
      // mode + když core.data_entity_type IS NULL. Click → entity picker
      // modal → PATCH /design/fw-core/update/{id} → reload form spec →
      // ➕ Pole button se objeví (_canPickFields() returns true).
      const entityBtn = document.createElement("button");
      entityBtn.type = "button";
      entityBtn.className = "erp-form-design-entity";
      entityBtn.textContent = "🎯 Entita";
      entityBtn.title = "Přiřadit datovou entitu (user / menu_node / core). Po assign se ➕ Pole stane dostupný.";
      this._formEntityBtn = entityBtn;
      this._updateFormEntityBtn();  // initial visibility
      entityBtn.addEventListener("click", () => {
        this._openEntityTypePicker();
      });
      // Ctrl+Z keyboard shortcut — capture phase aby browser default
      // (undo v inputu) nepřebijel (jen pokud focus mimo input).
      this._undoKeyHandler = (ev) => {
        if ((ev.ctrlKey || ev.metaKey) && ev.key === "z" && !ev.shiftKey) {
          const t = ev.target;
          const tag = t && t.tagName;
          if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;
          if (this._formDesignMode !== true) return;
          ev.preventDefault();
          ev.stopPropagation();
          this._performUndo();
        }
      };
      document.addEventListener("keydown", this._undoKeyHandler, true);

      // Insert PRED sysToggle (= prvni button v rightActions) — toggle
      // je hlavni mode switch, ostatni jsou pomocna nastaveni.
      // Order v rightActions po insertBefore (kazdy pred sysToggle):
      //   toggle -> undoBtn -> addBtn -> saveSizeBtn -> detectMinBtn -> sysToggle
      //   (leftmost to rightmost)
      const sysToggle = rightActions.querySelector(".erp-design-systoggle");
      if (sysToggle) {
        rightActions.insertBefore(toggle, sysToggle);
        rightActions.insertBefore(undoBtn, sysToggle);
        rightActions.insertBefore(entityBtn, sysToggle);
        rightActions.insertBefore(addBtn, sysToggle);
        rightActions.insertBefore(saveSizeBtn, sysToggle);
        rightActions.insertBefore(detectMinBtn, sysToggle);
      } else {
        // Fallback: prepend (reverse order)
        rightActions.insertBefore(detectMinBtn, rightActions.firstChild);
        rightActions.insertBefore(saveSizeBtn, rightActions.firstChild);
        rightActions.insertBefore(addBtn, rightActions.firstChild);
        rightActions.insertBefore(entityBtn, rightActions.firstChild);
        rightActions.insertBefore(undoBtn, rightActions.firstChild);
        rightActions.insertBefore(toggle, rightActions.firstChild);
      }
    }

    _updateFormDetectMinBtn() {
      if (!this._formDetectMinBtn) return;
      const on = this._formDesignMode === true;
      const visible = on && !!(this._spec && this._spec.form && this._spec.form.id);
      this._formDetectMinBtn.style.cssText =
        "background:#1f4858;border:1px solid #3a8aa8;color:#7ed4e8;" +
        "padding:4px 10px;border-radius:3px;cursor:pointer;font-size:11px;" +
        "font-weight:600;" +
        (visible ? "" : "display:none;");
    }

    async _detectAndSaveMinSize() {
      // Krok 14b+12: auto-detect min size via iterate decrement +
      // overflow check. Algorithm:
      //   1. Save current dialog dimensions
      //   2. Remove min constraints temporarily (allow shrinking)
      //   3. Iterate decrement width (current → 200px, step 20px)
      //      - Each step: set width, await rAF, check overflow
      //      - First overflow = found minimum
      //   4. Height: header + footer + min body (100px) — static calc
      //   5. PATCH save min_width + min_height
      //   6. Restore dialog to original size + apply new mins
      if (!this._spec || !this._spec.form || !this._spec.form.id) {
        _showToast("Form ID chybí v spec", "error");
        return;
      }
      const dialog = this._shell && this._shell.dialog;
      if (!dialog) {
        _showToast("Dialog reference chybí", "error");
        return;
      }

      // Save original state pro restore
      const origW = dialog.style.width;
      const origH = dialog.style.height;
      const origMinW = dialog.style.minWidth;
      const origMinH = dialog.style.minHeight;
      const origTransition = dialog.style.transition;

      _showToast("Detekce minimální velikosti…", "info", 1500);

      // Temporarily remove min constraints (allow shrinking past current
      // min) + disable transitions (instant resize per step)
      dialog.style.minWidth = "0";
      dialog.style.minHeight = "0";
      dialog.style.transition = "none";

      try {
        // === WIDTH DETECTION (iterate + horizontal overflow check) ===
        const startW = dialog.clientWidth;
        let lastOKWidth = startW;
        let testW = startW;
        const STEP_W = 20;
        const FLOOR_W = 200;
        while (testW > FLOOR_W) {
          dialog.style.width = testW + "px";
          await new Promise((r) => requestAnimationFrame(r));
          if (this._hasHorizontalOverflow(dialog)) {
            break;
          }
          lastOKWidth = testW;
          testW -= STEP_W;
        }
        const minWidth = Math.max(lastOKWidth + STEP_W, FLOOR_W);

        // Restore width PRED height detection (isolated test axes)
        dialog.style.width = origW;
        await new Promise((r) => requestAnimationFrame(r));

        // === HEIGHT DETECTION (iterate + vertical overflow check) ===
        // Krok 14b+12.1 (13.5.2026 ~23:50, Marti's "u vysky to chce jeste
        // nejakou korekci"): static calc (header + footer + 120px) byla
        // moc malá — body fields scrollované za footer. Replace dynamic
        // iterate decrement (analog width) — first body overflow = found
        // boundary kde fields zacnou byt skryté za footer.
        //
        // Krok 14b+12.2 (13.5.2026 ~00:10, Marti's korekce po smoke:
        // "Asi to chce korekci o vysku hlavicky + vysku paticky"):
        // iterate detekuje overflow boundary, ale visible body content
        // muze mit edge case (padding mimo scrollHeight diff, sub-pixel
        // rounding). Marti's intuition: PLUS bezpecnostni polštář =
        // header.offsetHeight + footer.offsetHeight. To garantuje ze pri
        // min height body content area >= "lastOK content" + (jeste jednou
        // chrome velikost) → fields VŽDY visible bez nutnosti scroll.
        const startH = dialog.clientHeight;
        let lastOKHeight = startH;
        let testH = startH;
        const STEP_H = 20;
        const FLOOR_H = 200;
        while (testH > FLOOR_H) {
          dialog.style.height = testH + "px";
          // Double rAF pro robust layout reflow (1x bylo nedostatecne v
          // edge cases — Marti's height korekce smoke odhalila)
          await new Promise((r) => requestAnimationFrame(r));
          await new Promise((r) => requestAnimationFrame(r));
          if (this._hasVerticalOverflow(dialog)) {
            break;
          }
          lastOKHeight = testH;
          testH -= STEP_H;
        }
        // Marti's korekce: + headerH + footerH bezpecnostni polštář
        const headerEl = dialog.querySelector(".erp-modal-header");
        const footerEl = dialog.querySelector(".erp-modal-footer");
        const headerH = headerEl ? headerEl.offsetHeight : 50;
        const footerH = footerEl ? footerEl.offsetHeight : 50;
        const minHeight = Math.max(
          lastOKHeight + headerH + footerH,
          FLOOR_H
        );
        console.info(
          "[DesignFwForm] min height calc: lastOK=" + lastOKHeight +
          " + header=" + headerH + " + footer=" + footerH +
          " = " + minHeight + "px"
        );

        // === Restore original size ===
        dialog.style.width = origW;
        dialog.style.height = origH;
        // Apply new mins (browser CSS prevent shrink under)
        dialog.style.minWidth = minWidth + "px";
        dialog.style.minHeight = minHeight + "px";
        dialog.style.transition = origTransition;

        // === PATCH save ===
        const newLayout = Object.assign({}, this._spec.form.layout || {}, {
          min_width: minWidth + "px",
          min_height: minHeight + "px",
        });
        const r = await fetch(
          "/api/v1/erp/design/comp-def/update/" + encodeURIComponent(this._spec.form.id),
          {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ layout: newLayout }),
          }
        );
        if (!r.ok) {
          const errBody = await r.json().catch(() => ({}));
          throw new Error("HTTP " + r.status + ": " + (errBody.error || r.statusText));
        }
        this._spec.form.layout = newLayout;
        _showToast(
          "Min velikost detekována: " + minWidth + " × " + minHeight + " px",
          "success",
          2500
        );
      } catch (e) {
        // Restore original state na fail
        dialog.style.width = origW;
        dialog.style.height = origH;
        dialog.style.minWidth = origMinW;
        dialog.style.minHeight = origMinH;
        dialog.style.transition = origTransition;
        console.error("[DesignFwForm] detect min failed:", e);
        _showToast("Detekce selhala: " + (e.message || e), "error", 3500);
      }
    }

    _hasHorizontalOverflow(dialog) {
      // Check #1: dialog content exceeds dialog client width
      // (rare protoze dialog ma overflow:hidden, ale defensive)
      if (dialog.scrollWidth > dialog.clientWidth + 1) return true;
      // Check #2: any field input clipped horizontally
      // (form's grid auto-fit minmax(220px, 1fr) — when modal < 220+padding,
      // grid item shrinks below 220 a input overflow contains its label/value)
      const inputs = dialog.querySelectorAll(
        "input, select, textarea, .erp-input-input, .erp-dropdown-trigger"
      );
      for (let i = 0; i < inputs.length; i++) {
        const el = inputs[i];
        // scrollWidth > clientWidth = horizontal content overflow (text
        // clipped). +2px tolerance for sub-pixel rounding.
        if (el.scrollWidth > el.clientWidth + 2) return true;
      }
      // Check #3: grid main panel scrollWidth (grid items extending beyond)
      const grid = dialog.querySelector(".erp-design-grid");
      if (grid && grid.scrollWidth > grid.clientWidth + 1) return true;
      return false;
    }

    _hasVerticalOverflow(dialog) {
      // Krok 14b+12.1 (13.5.2026 ~23:50, Marti's height korekce):
      // Detekuje kdy body fields zacnou byt skryté za footer (body
      // ma overflow-y:auto → scrollbar appear když scrollHeight > clientHeight).
      //
      // Marti's UX kriterium: VŠECHNY fields musi byt visible bez scroll.
      // Pokud body scrolly, posledni field je hidden za footer → moc malá výška.
      //
      // Check #1: body scrollHeight > clientHeight (primary signal)
      const body = dialog.querySelector(".erp-modal-body");
      if (body && body.scrollHeight > body.clientHeight + 2) return true;
      // Check #2: root grid scrollHeight > clientHeight (root je body content)
      const root = dialog.querySelector(".erp-design-tab-content");
      if (root && root.scrollHeight > root.clientHeight + 2) return true;
      return false;
    }

    _updateFormSaveSizeBtn() {
      if (!this._formSaveSizeBtn) return;
      const on = this._formDesignMode === true;
      // Visible jen v DESIGN mode (analog addFieldBtn). Visible vzdy v
      // DESIGN, ne hover-only — Marti chce easy klik pro save size.
      const visible = on && !!(this._spec && this._spec.form && this._spec.form.id);
      this._formSaveSizeBtn.style.cssText =
        "background:#1f4858;border:1px solid #3a8aa8;color:#7ed4e8;" +
        "padding:4px 10px;border-radius:3px;cursor:pointer;font-size:11px;" +
        "font-weight:600;" +
        (visible ? "" : "display:none;");
    }

    async _saveFormDefaultSize() {
      // Krok 14b+11: PATCH form root comp_def layout s aktualnimi
      // dialog dimensions. _spec.form.id je root form comp_def (type_id=302).
      if (!this._spec || !this._spec.form || !this._spec.form.id) {
        _showToast("Form ID chybí v spec", "error");
        return;
      }
      if (!this._shell || !this._shell.dialog) {
        _showToast("Dialog reference chybí", "error");
        return;
      }
      const dialog = this._shell.dialog;
      // getBoundingClientRect vrati actual rendered size (po user resize
      // pres CSS resize:both v dialog.style).
      const rect = dialog.getBoundingClientRect();
      const w = Math.round(rect.width);
      const h = Math.round(rect.height);
      // Defensive sanity (modal nesmi byt menší nez prakticky pouzitelne)
      if (w < 400 || h < 300) {
        _showToast(
          "Velikost je moc malá (" + w + "×" + h + "). Min 400×300.",
          "error",
          3000
        );
        return;
      }
      const currentLayout = (this._spec.form.layout && typeof this._spec.form.layout === "object")
        ? this._spec.form.layout
        : {};
      const newLayout = Object.assign({}, currentLayout, {
        default_width: w + "px",
        default_height: h + "px",
      });
      try {
        const r = await fetch(
          "/api/v1/erp/design/comp-def/update/" + encodeURIComponent(this._spec.form.id),
          {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ layout: newLayout }),
          }
        );
        if (!r.ok) {
          const errBody = await r.json().catch(() => ({}));
          throw new Error("HTTP " + r.status + ": " + (errBody.error || r.statusText));
        }
        // Update local spec consistency — pri pristim open() pripada uz z
        // backendu, ale instant local update pro current session
        this._spec.form.layout = newLayout;
        _showToast(
          "Výchozí velikost uložena (" + w + " × " + h + " px)",
          "success"
        );
      } catch (e) {
        console.error("[DesignFwForm] save size failed:", e);
        _showToast("Uložení velikosti selhalo: " + (e.message || e), "error", 3500);
      }
    }

    _updateFormAddFieldBtn() {
      if (!this._formAddFieldBtn) return;
      const on = this._formDesignMode === true;
      // Visible jen v DESIGN mode + pokud picker je vubec dostupny
      // (entity_type + formId + FieldPickerModal class). Pred _spec
      // loaded jen schovat default.
      const canPick = this._canPickFields();
      const visible = on && canPick;
      this._formAddFieldBtn.style.display = visible ? "" : "none";
      this._formAddFieldBtn.style.cssText =
        "background:#1f4858;border:1px solid #3a8aa8;color:#7ed4e8;" +
        "padding:4px 10px;border-radius:3px;cursor:pointer;font-size:11px;" +
        "font-weight:600;" +
        (visible ? "" : "display:none;");
    }

    _updateFormEntityBtn() {
      // Phase 38.4 Krok 14g Etapa F Krok 5.F REVERT (16.5.2026, Marti's "vyber
      // entity uz kdyz jsme na formulari tam nepatri"): entity volba je
      // higher-level concept (tree node nebo cmi). Form je layout + fields,
      // entity je inherited. Button vždy hidden — funkce zachovaná jako
      // dead code pro budoucí Krok 5.G implementaci na správné vrstvě.
      if (!this._formEntityBtn) return;
      this._formEntityBtn.style.cssText = "display:none;";
    }

    async _openEntityTypePicker() {
      // Phase 38.4 Krok 14g Etapa F Krok 5.F (16.5.2026): entity picker modal.
      // Marti's "schazi Pole + magic" — assign data_entity_type je preconditie
      // pro ➕ Pole button. Po výběru → PATCH /design/fw-core/update/{id}
      // body {data_entity_type: <code>} → reload _spec → buttons refresh.
      const core = this._spec && this._spec.core;
      if (!core || !core.id) {
        alert("Core data nejsou loaded.");
        return;
      }
      const ENTITY_TYPES = [
        {
          code: "user",
          icon: "👤",
          title: "Uživatel",
          desc: "Editace user záznamu. Fields: legal_name, first_name, last_name, status, ews_email, atd. + EMAILY/TELEFONY sub-grids.",
        },
        {
          code: "menu_node",
          icon: "📁",
          title: "Menu node",
          desc: "Editace tree node / soudeček. Fields: code, label, kind, parent_id, sort_order, visibility_scope, atd.",
        },
        {
          code: "core",
          icon: "🎨",
          title: "Core (fw.core)",
          desc: "Editace samotné core entity. Fields: code, label, layout_type, data_entity_type, version, atd. (meta-design).",
        },
      ];

      const overlay = document.createElement("div");
      overlay.style.cssText =
        "position:fixed;inset:0;background:rgba(0,0,0,0.65);z-index:10025;" +
        "display:flex;align-items:center;justify-content:center;";

      const dialog = document.createElement("div");
      dialog.style.cssText =
        "background:#1a1f26;border:1px solid #2a3340;border-radius:6px;" +
        "padding:24px;width:840px;max-width:95vw;max-height:85vh;overflow:auto;" +
        "color:#cfd6df;font-size:13px;box-shadow:0 12px 40px rgba(0,0,0,0.6);";

      const titleEl = document.createElement("div");
      titleEl.style.cssText =
        "font-size:16px;font-weight:600;color:#c89eee;margin-bottom:6px;";
      titleEl.textContent = "🎯 Vybrat datovou entitu pro core id=" + core.id;
      dialog.appendChild(titleEl);

      const currentEnt = core.data_entity_type || null;
      const subtitleEl = document.createElement("div");
      subtitleEl.style.cssText =
        "font-size:12px;color:#8a96a4;margin-bottom:20px;font-style:italic;";
      subtitleEl.innerHTML = currentEnt
        ? ("Aktuální entita: <code style=\"color:#c89eee;\">" + currentEnt +
           "</code>. Klik na jinou kartu → změna (varování pokud existují fields). Storno zachová stávající.")
        : "Entita určuje main panel fields a children sub-grids. Po assign se ➕ Pole stane dostupný.";
      dialog.appendChild(subtitleEl);

      const cardsRow = document.createElement("div");
      cardsRow.style.cssText =
        "display:flex;gap:14px;flex-wrap:wrap;justify-content:space-between;";

      let _busy = false;
      const self = this;
      ENTITY_TYPES.forEach(function (et) {
        const isCurrent = (et.code === currentEnt);
        const card = document.createElement("div");
        card.style.cssText =
          "flex:1 1 240px;min-width:240px;max-width:280px;" +
          (isCurrent
            ? "background:#2a1f3a;border:2px solid #8a5fb0;"
            : "background:#0f1419;border:1px solid #2a3340;") +
          "border-radius:6px;padding:18px;cursor:" +
          (isCurrent ? "default" : "pointer") + ";transition:all 0.15s;" +
          "display:flex;flex-direction:column;gap:10px;" +
          "position:relative;";
        if (!isCurrent) {
          card.onmouseenter = function () {
            if (_busy) return;
            card.style.borderColor = "#8a5fb0";
            card.style.background = "#161c24";
          };
          card.onmouseleave = function () {
            card.style.borderColor = "#2a3340";
            card.style.background = "#0f1419";
          };
        }
        const currentBadge = isCurrent
          ? '<div style="position:absolute;top:6px;right:6px;font-size:10px;' +
            'color:#c89eee;background:#3a2a4a;padding:2px 6px;border-radius:3px;' +
            'font-weight:600;">AKTUÁLNÍ</div>'
          : '';
        card.innerHTML =
          currentBadge +
          '<div style="font-size:42px;line-height:1;">' + et.icon + '</div>' +
          '<div style="font-size:14px;font-weight:600;color:#c89eee;">' +
          et.title + '</div>' +
          '<div style="font-size:12px;line-height:1.5;color:#a8b3bf;">' +
          et.desc + '</div>';
        card.onclick = async function () {
          if (_busy || isCurrent) return;
          // Marti-AI's "pojistka se stala dospelosti" — pokud entity already
          // assigned, confirm mind change (potential field loss).
          if (currentEnt && currentEnt !== et.code) {
            const ok = window.confirm(
              "Změnit entitu z '" + currentEnt + "' na '" + et.code + "'?\n\n" +
              "Pozor: main panel přerenderuje s fields podle nové entity. " +
              "Custom fields přidané přes ➕ Pole zůstávají v DB (parent_comp_def_id), " +
              "ale entity_config fields se přepnou na nový typ.\n\n" +
              "Pokračovat?"
            );
            if (!ok) return;
          }
          _busy = true;
          card.style.background = "rgba(138,95,176,0.15)";
          try {
            const r = await fetch(
              "/api/v1/erp/design/fw-core/update/" + encodeURIComponent(core.id),
              {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                credentials: "include",
                body: JSON.stringify({ data_entity_type: et.code }),
              }
            ).then(function (rr) { return rr.json(); });
            if (r && r.ok) {
              // Update local _spec + refresh buttons
              if (self._spec && self._spec.core) {
                self._spec.core.data_entity_type = et.code;
              }
              try { document.body.removeChild(overlay); } catch (e) {}
              // Reload form spec (re-fetch + re-render)
              try {
                const reload = await fetch(
                  "/api/v1/erp/fw-form/by-id/" +
                    encodeURIComponent(core.id) + "/" +
                    encodeURIComponent(self.opts.rowId || 1),
                  { credentials: "include" }
                ).then(function (rr) { return rr.json(); });
                if (reload && reload.ok) {
                  self._spec = reload;
                  self._render();
                }
              } catch (e) {
                console.warn("[DesignFwForm] reload after entity assign failed:", e);
              }
            } else {
              _busy = false;
              card.style.background = "#0f1419";
              alert("Assign entity selhal: " + ((r && r.error) || "unknown"));
            }
          } catch (e) {
            _busy = false;
            card.style.background = "#0f1419";
            alert("Assign entity (network): " + (e.message || e));
          }
        };
        cardsRow.appendChild(card);
      });

      dialog.appendChild(cardsRow);

      // Footer — Zrušit přiřazení (pokud entity assigned) + Storno
      const footer = document.createElement("div");
      footer.style.cssText =
        "margin-top:20px;padding-top:16px;border-top:1px solid #2a3340;" +
        "display:flex;justify-content:space-between;align-items:center;";

      // Phase 38.4 Krok 14g Etapa F Krok 5.F (Marti's "jak se tam zpatky?"):
      // 🚫 Zrušit přiřazení — entity → NULL. Analog Zrušit asociaci pattern
      // z Krok 5.C. Visible jen pokud currentEnt existuje.
      if (currentEnt) {
        const btnUnassign = document.createElement("button");
        btnUnassign.type = "button";
        btnUnassign.textContent = "🚫 Zrušit přiřazení";
        btnUnassign.style.cssText =
          "padding:7px 14px;font-size:12px;border-radius:4px;" +
          "background:rgba(212,135,135,0.12);" +
          "border:1px solid rgba(212,135,135,0.4);color:#d48787;" +
          "cursor:pointer;font-weight:600;";
        btnUnassign.onclick = async function () {
          if (_busy) return;
          const ok = window.confirm(
            "Zrušit přiřazení entity '" + currentEnt + "'?\n\n" +
            "Form se vrátí do drafted stavu (data_entity_type=NULL). " +
            "Main panel ztratí fields z entity_config. ➕ Pole button " +
            "schová se dokud nevybereš novou entitu.\n\n" +
            "Pokračovat?"
          );
          if (!ok) return;
          _busy = true;
          btnUnassign.disabled = true;
          btnUnassign.textContent = "Ruším…";
          try {
            const r = await fetch(
              "/api/v1/erp/design/fw-core/update/" + encodeURIComponent(core.id),
              {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                credentials: "include",
                body: JSON.stringify({ data_entity_type: "" }),
              }
            ).then(function (rr) { return rr.json(); });
            if (r && r.ok) {
              if (self._spec && self._spec.core) {
                self._spec.core.data_entity_type = null;
              }
              try { document.body.removeChild(overlay); } catch (e) {}
              // Reload form spec
              try {
                const reload = await fetch(
                  "/api/v1/erp/fw-form/by-id/" +
                    encodeURIComponent(core.id) + "/" +
                    encodeURIComponent(self.opts.rowId || 1),
                  { credentials: "include" }
                ).then(function (rr) { return rr.json(); });
                if (reload && reload.ok) {
                  self._spec = reload;
                  self._render();
                }
              } catch (e) {}
            } else {
              _busy = false;
              btnUnassign.disabled = false;
              btnUnassign.textContent = "🚫 Zrušit přiřazení";
              alert("Zrušení selhalo: " + ((r && r.error) || "unknown"));
            }
          } catch (e) {
            _busy = false;
            btnUnassign.disabled = false;
            btnUnassign.textContent = "🚫 Zrušit přiřazení";
            alert("Zrušení (network): " + (e.message || e));
          }
        };
        footer.appendChild(btnUnassign);
      } else {
        // Spacer aby Storno bylo vpravo (flex justify-content space-between)
        const spacer = document.createElement("div");
        footer.appendChild(spacer);
      }

      const btnCancel = document.createElement("button");
      btnCancel.type = "button";
      btnCancel.textContent = "Storno";
      btnCancel.style.cssText =
        "padding:7px 16px;font-size:13px;border-radius:4px;" +
        "background:#22282f;border:1px solid #2a3340;color:#cfd6df;cursor:pointer;";
      btnCancel.onclick = function () {
        try { document.body.removeChild(overlay); } catch (e) {}
      };
      footer.appendChild(btnCancel);
      dialog.appendChild(footer);

      overlay.appendChild(dialog);
      document.body.appendChild(overlay);

      // Esc to close
      function _escH(ev) {
        if (ev.key === "Escape" && !_busy) {
          ev.preventDefault();
          btnCancel.click();
          document.removeEventListener("keydown", _escH);
        }
      }
      document.addEventListener("keydown", _escH);
    }

    _canPickFields() {
      // Krok 14b+7.1: shared predicate — kdy je field picker dostupny.
      // Pouziva header "+ Pole" button + empty hint + footer hint.
      if (!this._spec) return false;
      const core = this._spec.core;
      const form = this._spec.form;
      if (!core || !form) return false;
      if (!core.data_entity_type) return false;
      if (!form.id) return false;
      if (typeof global.FieldPickerModal !== "function") return false;
      return true;
    }

    async _openFieldPicker() {
      // Krok 14b+7.1: shared handler pro vsechny field picker entry points
      // (header "+ Pole" button, empty hint click, footer hint click).
      // Bez tohoto helperu jsou 3 misto stejne logiky -- duplicita.
      if (!this._canPickFields()) {
        console.warn("[DesignFwForm] _openFieldPicker called but not canPick");
        return;
      }
      const core = this._spec.core;
      const formId = this._spec.form.id;
      const picker = new global.FieldPickerModal({
        entityType: core.data_entity_type,
        parentCompDefId: formId,
        onComplete: async (result) => {
          console.info("[DesignFwForm] FieldPicker complete:", result);
          // Reload form spec — fields by se měly objevit v main panel
          try {
            const r = await fetch(
              "/api/v1/erp/fw-form/" +
                encodeURIComponent(this._spec.core.code) + "/" +
                encodeURIComponent(this._spec.data.id || 0),
              { credentials: "include" }
            );
            if (r.ok) {
              const newSpec = await r.json();
              if (newSpec.ok) {
                this._spec = newSpec;
                this._render(); // re-render s novými fields
              }
            }
          } catch (e) {
            console.error("[DesignFwForm] reload after picker failed:", e);
            alert("Pole přidána, ale reload selhal. Zavři a otevři modal znovu.");
          }
        },
      });
      await picker.open();
    }

    _onDirty(fieldKey, isDirty) {
      if (isDirty) this._dirty.add(fieldKey);
      else this._dirty.delete(fieldKey);
      const count = this._dirty.size;
      if (this._saveBtn) this._saveBtn.style.display = count > 0 ? "" : "none";
      if (this._dirtyBadge) {
        const _wBadge = count === 1 ? "změna" : (count < 5 ? "změny" : "změn");
        this._dirtyBadge.textContent = count > 0 ? "● " + count + " " + _wBadge : "";
        this._dirtyBadge.style.display = count > 0 ? "" : "none";
      }
      // Krok 14b+16 (14.5.2026 rano, Marti's polish):
      //   1. Title bar zachovava AMBER accent pri dirty (visual signal)
      //   2. ALE textContent BEZ "● N změn" — vyhodit count z hlavicky
      //   3. Footer ma decent "● N změn" button (clickable revert) — _renderDirtyDiscardBtn
      // Marti: "Z hlavicky vyhodit ostatni text ohledne zmen.
      //         Pridat do paticky doleva ten kontext."
      if (this._shell && this._shell.title) {
        const baseTitle = this._spec && this._spec.core
          ? (this._spec.core.label || this._spec.core.code || "Editace")
          : "Editace";
        this._shell.title.textContent = baseTitle;  // VZDY base, bez count
        this._shell.title.style.color = count > 0 ? "#d4b88a" : "";  // amber pri dirty
      }
      // Refresh footer dirty discard button (visible jen pokud count > 0)
      this._updateDirtyDiscardBtn();
      _markFormDirty(this, count > 0);
    }

    _updateDirtyDiscardBtn() {
      if (!this._dirtyDiscardBtn) return;
      const count = this._dirty.size;
      // Krok 14b+16.1: flex spacer v footeru drzi OK+Storno vpravo bez
      // ohledu na discard visibility. Jen toggle display:
      if (count === 0) {
        this._dirtyDiscardBtn.style.display = "none";
        return;
      }
      const wBadge = count === 1 ? "změna" : (count < 5 ? "změny" : "změn");
      this._dirtyDiscardBtn.textContent = "● " + count + " " + wBadge;
      this._dirtyDiscardBtn.style.display = "";
    }

    async _revertAllChanges() {
      // Krok 14b+16: discard all dirty changes — reset každý field na origVal.
      // Body fields jsou v sec.grid (per panel), kazdy field el ma _inst.
      // Pro _field-based widgets (_inst.input.value = origVal),
      // Pro checkbox/_dropdown vlastni reset.
      if (!this._shell || !this._shell.body) return;
      const fieldEls = this._shell.body.querySelectorAll("[data-design-fieldkey]");
      const visited = new Set();
      fieldEls.forEach((el) => {
        // Find ancestor with _inst + _origVal (field wrapper)
        let wrap = el;
        while (wrap && !(wrap._inst && "_origVal" in wrap)) {
          wrap = wrap.parentElement;
          if (wrap === this._shell.body) { wrap = null; break; }
        }
        if (!wrap || !wrap._inst) return;
        const fk = wrap._fieldKey;
        if (!fk || visited.has(fk)) return;
        visited.add(fk);
        try {
          const orig = wrap._origVal;
          // Set value zpet — depend na widget type
          if (wrap._inst.input && "checked" in wrap._inst.input) {
            // Checkbox
            wrap._inst.input.checked = !!orig;
            const valLabel = wrap.querySelector("span");
            if (valLabel && valLabel.textContent === "Ano" || valLabel && valLabel.textContent === "Ne") {
              valLabel.textContent = wrap._inst.input.checked ? "Ano" : "Ne";
            }
          } else if (wrap._inst.input) {
            // Input / textarea
            wrap._inst.input.value = orig == null ? "" : String(orig);
            // Reset visual dirty marker (amber border-left)
            wrap._inst.input.style.borderLeft = "";
            wrap._inst.input.style.background = "";
          } else if (typeof wrap._inst.setValue === "function") {
            // Dropdown / UI Kit widget
            wrap._inst.setValue(orig);
          }
        } catch (e) {
          console.warn("[DesignFwForm] revert field failed:", fk, e);
        }
      });
      // Clear dirty set + update UI
      this._dirty.clear();
      _markFormDirty(this, false);
      if (this._shell && this._shell.title) {
        const baseTitle = this._spec && this._spec.core
          ? (this._spec.core.label || this._spec.core.code || "Editace")
          : "Editace";
        this._shell.title.textContent = baseTitle;
        this._shell.title.style.color = "";
      }
      this._updateDirtyDiscardBtn();
      if (this._saveBtn) this._saveBtn.style.display = "none";
      _showToast("Změny zrušeny", "info");
    }

    // Krok 14b+21 (14.5.2026 rano, Marti's "📘 Popis save"): popup pro
    // core description (user + system). Volane z header 📘 button
    // (onShowDescriptions handler v _buildModalShell). PATCH backend
    // pres /design/fw-core/update/{id} -> toast + update local spec.
    _openDescriptionsPopup() {
      if (!this._spec || !this._spec.core) {
        _showToast("Spec není načtený, nelze otevřít popis", "error");
        return;
      }
      const core = this._spec.core;
      const self = this;
      _buildDescriptionsPopup({
        entityKind: "core",
        entityId: core.id,
        entityLabel: core.label || core.code || "(bez labelu)",
        descUser: core.description_user,
        descSystem: core.description_system,
        onDirty: this._onDirty.bind(this),
        onSaved: function(payload) {
          // Update local spec consistency (no full reload nutny)
          self._spec.core.description_user = payload.description_user;
          self._spec.core.description_system = payload.description_system;
        },
      });
    }

    async _beforeCloseHandler() {
      if (!this._dirty || this._dirty.size === 0) return "close";
      const count = this._dirty.size;
      const phrase = count > 1
        ? (count < 5 ? "provedené změny" : "provedených změn")
        : "provedenou změnu";
      const decision = await _confirmDarkDialog({
        title: "Neuložené změny",
        message: "Mám uložit tebou " + phrase + "? (" + count + ")",
      });
      if (decision === true) {
        // TODO Phase 38.4 Krok 14b ráno — PATCH endpoint
        console.warn("Save not implemented yet — Krok 14b ráno.");
        return "save";
      }
      if (decision === false) return "close";
      return "cancel"; // null (Esc / click outside) → keep modal open
    }

    async open() {
      // Phase 38.4 Krok 14g Etapa F Step B: dual {coreId|coreCode, rowId} support.
      // Pokud jen coreId, fetch /fw-form/by-id/{coreId}/{rowId} (Step A endpoint)
      // vrátí spec včetně core.code → store this.opts.coreCode pro subsequent
      // URL builds (children/save/refresh — Step C migrate na coreId paths).
      const rowId = this.opts.rowId;
      if (rowId == null) {
        console.error("DesignFwForm: rowId required");
        return;
      }
      if (!this.opts.coreCode && this.opts.coreId) {
        // coreId-only call: resolve via by-id endpoint
        // (Step A backend, /fw-form/by-id/{core_id}/{row_id})
        try {
          const lookup = await fetch(
            "/api/v1/erp/fw-form/by-id/" +
            encodeURIComponent(this.opts.coreId) + "/" +
            encodeURIComponent(rowId)
          ).then(r => r.json());
          // Phase 38.4 Krok 14g Etapa F Krok 5.C (16.5.2026 odpoledne):
          // tolerate drafted core (code=NULL after Krok 5.C DDL "nic nas
          // nesmi omezovat"). Backend vrati lookup.empty_container=true
          // pro drafted — accept + cache spec, render placeholder.
          if (lookup && lookup.ok && lookup.core) {
            this.opts.coreCode = lookup.core.code || null;
            this._spec = lookup; // cache — skip second fetch ve vsech pripadech
          } else {
            console.error("DesignFwForm: by-id lookup failed for coreId=" + this.opts.coreId, lookup);
            return;
          }
        } catch (e) {
          console.error("DesignFwForm: by-id lookup network error:", e);
          return;
        }
      }
      const coreCode = this.opts.coreCode;
      // Phase 38.4 Krok 14g Etapa F Krok 5.C: coreCode CAN be null pro drafted
      // core (empty_container). Pokud chybi coreCode AND chybi cached _spec,
      // fail (neni co renderovat). Jinak pokracujeme — _render handle
      // empty_container placeholder branch.
      if (!coreCode && !this._spec) {
        console.error("DesignFwForm: ani coreCode ani _spec (provide coreId or coreCode)");
        return;
      }

      // Build shell s loading placeholder
      this._shell = _buildModalShell({
        title: "Načítám…",
        width: "920px",
        beforeClose: () => this._beforeCloseHandler(),
        onClose: () => {
          _markFormDirty(this, false);
          // Phase 38.4 Krok 14g-C: cleanup schema tree panel po modal close
          try {
            const panel = document.body.querySelector(".erp-schema-tree-panel");
            if (panel) document.body.removeChild(panel);
          } catch (e) {}
          // Phase 38.4 Krok 14g-D: cleanup undo state + keyboard listener
          try {
            if (this._undoKeyHandler) {
              document.removeEventListener("keydown", this._undoKeyHandler, true);
              this._undoKeyHandler = null;
            }
            this._undoStack = [];
          } catch (e) {}
        },
        // Krok 14b+21 (14.5.2026 rano): 📘 popup pro core description
        // (user + system). PATCH /design/fw-core/update/{id} po save.
        onShowDescriptions: () => this._openDescriptionsPopup(),
      });
      document.body.appendChild(this._shell.overlay);

      // Phase 38.4 Krok 14b+7 (13.5.2026 ~20:00, Marti's "PROD/DESIGN
      // trigger i na tom formu"): attach toggle button v header. Visible
      // jen pokud global _erpDesignMode = true. Default form mode =
      // PRODUCTION (safe — uzivatel musi explicit prepnout do DESIGN).
      this._attachFormDesignToggle();

      // Phase 38.4 Krok 14b+5 polish fix #5 (13.5.2026 ~14:30, po
      // Marti's DevTools diagnostic):
      //
      // ROOT CAUSE NALEZEN: DevTools ukázal `body.display: "block"`,
      // `body.flexDirection: "row"`. DesignFwForm.open() NIKDY nezavolal
      // setup body = flex column (to byl jen v DesignSoudecekCoreForm).
      // Bez body flex column, root flex:1 ne propagated, grid 1fr main
      // panel zustal natural height.
      //
      // Plus Marti has manually resized dialog (drag corner) -> inline
      // height: 394px. min-height: 500px nas chrání proti tomu být moc
      // malé, ale dialog stále content-sized pokud user drag-shrinks.
      if (this._shell && this._shell.dialog) {
        this._shell.dialog.style.minHeight = "500px";
        // POZN: 70vh height removed — Marti's resize via drag corner
        // override anyway. min-height 500px je dostatek pojistka.
      }
      // CRITICAL FIX — body MUSÍ být flex column pro root grid alClient:
      if (this._shell && this._shell.body) {
        this._shell.body.style.display = "flex";
        this._shell.body.style.flexDirection = "column";
        // Marti's polish (13.5.2026 ~15:00, iterace ~15:15):
        // - Horizontal: 20px → 12px (40% reduce dle Marti's request)
        // - Vertical: 16px → 8px (na polovinu)
        // Compact ale stale visible breathing room od edges modalu.
        this._shell.body.style.padding = "8px 12px";
      }

      const loading = document.createElement("div");
      loading.style.cssText = "padding:24px;text-align:center;color:#8a96a4;";
      // Phase 38.4 Krok 14g Etapa F Krok 5.C: fallback label pro drafted
      // core (coreCode=null).
      const _loadLabel = coreCode || ("id=" + this.opts.coreId);
      loading.textContent = "Načítám " + _loadLabel + " #" + rowId + "…";
      this._shell.body.appendChild(loading);

      try {
        // Phase 38.4 Krok 14g Etapa F Krok 5.C (16.5.2026 odpoledne):
        // Pokud _spec uz cached z by-id lookup (drafted core nebo bonus
        // cache z fully-formed core), skip second fetch — by-id response
        // ma identical shape jako /fw-form/{code}/{rowId} po Krok 5.A.
        // Pro fully-formed core mozeme re-fetch pres code (kontrola
        // konzistence), ale primarni dispatch path je teted by-id.
        if (!this._spec) {
          const resp = await fetch(
            "/api/v1/erp/fw-form/" + encodeURIComponent(coreCode) + "/" + encodeURIComponent(rowId)
          );
          if (!resp.ok) {
            const errBody = await resp.json().catch(() => ({}));
            throw new Error(
              "HTTP " + resp.status + ": " + (errBody.error || resp.statusText)
            );
          }
          this._spec = await resp.json();
        }
        if (!this._spec || !this._spec.ok) {
          throw new Error(
            "Backend error: " + (this._spec && this._spec.error || "unknown")
          );
        }
        // Krok 14b+11 (13.5.2026 ~23:00, Marti's "ukladat vychozi velikost
        // formu"): apply layout.default_width / default_height z form root
        // comp_def. Spec.form.layout je JSONB, persisted pres PATCH endpoint.
        // Apply pred _render() aby grid layout (auto-fit) zacal s novou
        // sirkou.
        this._applyDefaultSize();
        this._render();
        // Phase 38.4 Krok 14c+2 part B (14.5.2026 odpoledne): attach
        // drop target po render. Body je teted drop zone pro gallery
        // cards z FieldPickerModal Preview tabu. Drop kdekoli na form
        // → POST /design/comp-def s computed sort_order. MVP: region='main'
        // vždy, sort_order = max+10 (= konec main panelu). Future polish
        // (Krok 14c+3): compute region z drop coords (header/main/footer
        // dle Y pozice).
        this._attachDropTargetForGalleryDrag();
      } catch (e) {
        this._showError("Načítání selhalo: " + e.message);
      }
    }

    // Phase 38.4 Krok 14c+2 part B: drop target listener pro gallery
    // drag from FieldPickerModal. HTML5 DnD API — dragover preventDefault
    // (allow drop) + drop handler. Visual: tealové hint border na body
    // během dragover.
    _attachDropTargetForGalleryDrag() {
      const body = this._shell && this._shell.body;
      if (!body) return;
      if (body.dataset.galleryDropAttached === "1") return;  // idempotent
      body.dataset.galleryDropAttached = "1";

      // Gate: drop target aktivní jen v DESIGN mode (Marti's polish doctrine)
      const isDesignOn = () => this._formDesignMode === true;

      // Phase 38.4 Krok 14c+3 (14.5.2026 odpoledne, Marti's "drag-and-drop
      // na to spravne misto"): detekce target region z Y coord. Panel je
      // tagged data-region-slot (z _render() při buildování panelu).
      // Dragover → highlight target panel teal accent (zelená pro success).
      // Drop → POST s computed region_slot.
      let _lastHighlightedPanel = null;
      const _clearPanelHighlight = () => {
        if (_lastHighlightedPanel) {
          _lastHighlightedPanel.style.outline = "";
          _lastHighlightedPanel.style.outlineOffset = "";
          _lastHighlightedPanel.style.background = "";
          _lastHighlightedPanel = null;
        }
      };
      const _highlightPanel = (panel) => {
        if (_lastHighlightedPanel === panel) return;
        _clearPanelHighlight();
        if (!panel) return;
        panel.style.outline = "2px dashed #5dbf5d";
        panel.style.outlineOffset = "-2px";
        panel.style.background = "rgba(93, 191, 93, 0.05)";
        panel.style.transition = "background 0.1s, outline 0.1s";
        _lastHighlightedPanel = panel;
      };
      // Z Y coord najdi target panel + region_slot (legacy template panels)
      const _findPanelAtY = (clientY) => {
        const panels = body.querySelectorAll("[data-region-slot]");
        for (const p of panels) {
          const rect = p.getBoundingClientRect();
          if (clientY >= rect.top && clientY <= rect.bottom) {
            return p;
          }
        }
        return null;
      };

      // Phase 38.4 Krok 14f-J (14.5.2026 vecer, Marti's "drop se neuskutecni
      // na panel #22"): novy resolver — najit container (panel/groupbox)
      // pod kurzorem pres elementsFromPoint. Pokud nalezen, drop pujde do
      // toho kontejneru (parent_comp_def_id = container.id). Fallback na
      // template panel (region_slot) pokud zadny container nenalezen.
      //
      // Vraci: { container: HTMLElement | null, templatePanel: HTMLElement | null }
      const _findDropTarget = (clientX, clientY) => {
        let container = null;
        let templatePanel = null;
        try {
          const els = document.elementsFromPoint(clientX, clientY);
          for (const el of els) {
            if (!el || !el.dataset) continue;
            // Container match (panel/groupbox) — most specific
            if (!container && el.dataset.compDefId && el.dataset.compTypeCode &&
                (el.dataset.compTypeCode === "panel" || el.dataset.compTypeCode === "groupbox")) {
              container = el;
            }
            // Template panel match (legacy region_slot wrapper) — fallback
            if (!templatePanel && el.dataset.regionSlot) {
              templatePanel = el;
            }
            if (container && templatePanel) break;
          }
        } catch (e) {
          console.warn("[DesignFwForm] _findDropTarget failed:", e);
        }
        return { container, templatePanel };
      };

      body.addEventListener("dragover", (ev) => {
        if (!isDesignOn()) return;
        // Allow drop jen pokud je to naše gallery card mime type
        const types = ev.dataTransfer && ev.dataTransfer.types;
        if (!types || !Array.from(types).includes("application/x-erp-comp-type")) return;
        ev.preventDefault();
        ev.dataTransfer.dropEffect = "copy";
        // Phase 38.4 Krok 14f-J: prefer container target (panel/groupbox)
        // pred legacy template panel. Container highlight = primary,
        // template panel = sekundarni fallback.
        const { container, templatePanel } = _findDropTarget(ev.clientX, ev.clientY);
        if (container) {
          _highlightPanel(container);
          body.style.outline = "1px solid rgba(168, 140, 212, 0.3)";  // purple subtle
        } else if (templatePanel) {
          _highlightPanel(templatePanel);
          body.style.outline = "1px solid rgba(58,138,168,0.3)";
        } else {
          _clearPanelHighlight();
          body.style.outline = "2px dashed #3a8aa8";
        }
        body.style.outlineOffset = "-4px";
      });

      body.addEventListener("dragleave", (ev) => {
        // Only clear pokud opravdu opustime body (ne sub-element hover)
        if (ev.target === body) {
          body.style.outline = "";
          body.style.outlineOffset = "";
          _clearPanelHighlight();
        }
      });

      body.addEventListener("drop", async (ev) => {
        if (!isDesignOn()) return;
        const raw = ev.dataTransfer.getData("application/x-erp-comp-type");
        if (!raw) return;
        ev.preventDefault();
        body.style.outline = "";
        body.style.outlineOffset = "";
        // Phase 38.4 Krok 14f-J: detect container OR template panel target
        const { container, templatePanel } = _findDropTarget(ev.clientX, ev.clientY);
        const targetRegion = (templatePanel && templatePanel.dataset.regionSlot) || "main";
        const targetContainerId = container ? parseInt(container.dataset.compDefId, 10) : null;
        const targetContainerCode = container ? container.dataset.compTypeCode : null;
        _clearPanelHighlight();

        let payload;
        try {
          payload = JSON.parse(raw);
        } catch (e) {
          _showToast("Drop payload corrupt — chyba parsování", "error");
          return;
        }
        if (!payload || !payload.id) {
          _showToast("Drop bez comp_type id", "error");
          return;
        }

        // POST /design/comp-def — Phase 38.4 Krok 14f-J:
        // Pokud drop na container (panel/groupbox), parent = container.id.
        // Jinak parent = form root + region_slot z template panel.
        const formRootId = this._spec && this._spec.form && this._spec.form.id;
        if (!formRootId) {
          _showToast("Form root chybi — drop selhal", "error");
          return;
        }
        // Decide parent: container (if found) vs form root (legacy)
        const parentId = targetContainerId || formRootId;
        const targetLabel = targetContainerId
          ? (targetContainerCode + " #" + targetContainerId)
          : ("panel '" + targetRegion + "'");

        // Phase 38.4 Krok 14f-L (14.5.2026 vecer, Marti's "nedodelana
        // parametrizace ke kteremu DB fieldu to patri"): otevri column
        // picker pro non-container, non-label types. Container/label
        // skip — direct create s auto-name.
        const isContainer = payload.is_container === true ||
                            payload.code === "panel" ||
                            payload.code === "groupbox";
        const isLabel = payload.code === "label" || payload.code === "label_readonly";

        let nameToUse, captionToUse;
        if (isContainer || isLabel) {
          // No DB binding needed — direct create
          nameToUse = payload.code + "_" + Date.now().toString(36);
          captionToUse = payload.label;
        } else {
          // Open column picker dialog
          const choice = await this._pickColumnForNewField(payload, parentId);
          if (!choice) {
            _showToast("Pridani zrušeno", "info", 1500);
            return;
          }
          nameToUse = choice.name;
          captionToUse = choice.caption;
        }

        try {
          // Phase 38.4 Krok 14f-C (14.5.2026 vecer): pass-through layout
          // pro container types (panel/groupbox). Drag payload obsahuje
          // default layout (panel → {"align":"client"}, groupbox →
          // {"border_mode":"top","label":null}).
          const postBody = {
            parent_comp_def_id: parentId,
            name: nameToUse,
            caption: captionToUse,
            type_id: payload.id,
            region_slot: targetRegion,
          };
          if (payload.layout && typeof payload.layout === "object") {
            postBody.layout = payload.layout;
          }
          const r = await fetch("/api/v1/erp/design/comp-def", {
            method: "POST",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(postBody),
          });
          const d = await r.json();
          if (!r.ok || !d.ok) {
            throw new Error(d.error || "HTTP " + r.status);
          }
          _showToast(
            "Přidáno: " + payload.label + " → " + targetLabel,
            "success",
            2500
          );
          // Refresh spec + re-render
          const refreshResp = await fetch(
            "/api/v1/erp/fw-form/" +
            encodeURIComponent(this.opts.coreCode) + "/" +
            encodeURIComponent(this.opts.rowId)
          );
          if (refreshResp.ok) {
            this._spec = await refreshResp.json();
            this._render();
            this._attachDropTargetForGalleryDrag();  // re-attach po _render
          }
        } catch (e) {
          console.error("[DesignFwForm] gallery drop POST failed:", e);
          _showToast("Drop selhal: " + (e.message || e), "error", 3500);
        }
      });
    }

    // ──────────────────────────────────────────────────────────────────
    // Phase 38.4 Krok 14d-D (14.5.2026 vecer, Marti-AI's Q3 polymorphic):
    // Children sub-grid rendering + CRUD. MVP s native prompt() pro
    // add/edit inputs, polish v Krok 14d-E (inline edit dialog).
    // ──────────────────────────────────────────────────────────────────

    _renderChildSection(childKey, childInfo) {
      // Section wrap (analog section v form fields)
      const sec = _sectionBuild(
        childInfo.label || childKey,
        "child:" + childKey
      );

      // Phase 38.4 Krok 14f-O (14.5.2026 vecer, Marti's "v production mode
      // jsou gridy dragabled... to ma byt jen v design mode"):
      // Drag handle + grip + contextmenu jsou DESIGN-only features.
      // V PROD mode child section je read-only display.
      const designMode = this._formDesignMode === true;
      if (!designMode) {
        // PROD mode: short-circuit — pouze static render bez drag/context.
        // Pokracuj k table rendering (data display) niz.
      } else {
        // Phase 38.4 Krok 14d-D+ (14.5.2026 vecer, Marti's "dragable"):
        // Per-section drag handle + dragover/drop reorder. MVP — in-memory
        // state přes this._childOrder. Section wrap dostane draggable=true,
        // grip ⋮⋮ vlevo (visual hint), drop target = jiná section / form.
        sec.wrap.draggable = true;
        sec.wrap.dataset.childSectionKey = childKey;
        sec.wrap.style.cursor = "default";  // default — grab jen na grip

        // Drag handle grip (visual + cursor:grab on hover)
        const grip = document.createElement("div");
        grip.textContent = "⋮⋮";
        grip.title = "Drag pro přesun sekce nahoru/dolů";
        grip.style.cssText =
          "position:absolute;left:4px;top:8px;width:18px;height:24px;" +
          "color:#5d6975;font-size:14px;line-height:1;cursor:grab;" +
          "user-select:none;display:flex;align-items:center;justify-content:center;" +
          "z-index:2;transition:color 0.15s;";
        grip.addEventListener("mouseenter", () => grip.style.color = "#7ed4e8");
        grip.addEventListener("mouseleave", () => grip.style.color = "#5d6975");
        sec.wrap.style.position = "relative";
        sec.wrap.style.paddingLeft = "28px";  // make room pro grip
        sec.wrap.appendChild(grip);

        // Drag handlers — only initiate drag z grip area (mousedown na grip)
        let _dragArmed = false;
        grip.addEventListener("mousedown", () => { _dragArmed = true; });
        // Globální mouseup fallback — pokud user neuvolnil dragstart
        document.addEventListener("mouseup", () => { _dragArmed = false; }, { once: true });

        // Phase 38.4 Krok 14f-I (14.5.2026 vecer, Marti's "dodelat
        // nastaveni gridu, minimalne tlacitko odebrat"): right-click na
        // child section → settings popup.
        sec.wrap.addEventListener("contextmenu", (ev) => {
          const tag = ev.target && ev.target.tagName;
          if (tag === "INPUT" || tag === "BUTTON" || tag === "TEXTAREA" || tag === "SELECT") {
            return;
          }
          ev.preventDefault();
          ev.stopPropagation();
          this._openChildSectionSettings(childKey, childInfo);
        });

        sec.wrap.addEventListener("dragstart", (ev) => {
          if (!_dragArmed) {
            ev.preventDefault();  // ignore drag pokud ne z grip
            return;
          }
          sec.wrap.style.opacity = "0.5";
          ev.dataTransfer.effectAllowed = "move";
          ev.dataTransfer.setData(
            "application/x-erp-child-section",
            childKey
          );
        });
        sec.wrap.addEventListener("dragend", () => {
          sec.wrap.style.opacity = "1";
          _dragArmed = false;
        });

        sec.wrap.addEventListener("dragover", (ev) => {
          const types = ev.dataTransfer && ev.dataTransfer.types;
          if (!types || !Array.from(types).includes("application/x-erp-child-section")) return;
          ev.preventDefault();
          ev.dataTransfer.dropEffect = "move";
          sec.wrap.style.borderTop = "2px solid #7ed4e8";
        });
        sec.wrap.addEventListener("dragleave", (ev) => {
          if (ev.target === sec.wrap) {
            sec.wrap.style.borderTop = "";
          }
        });
        sec.wrap.addEventListener("drop", (ev) => {
          ev.preventDefault();
          sec.wrap.style.borderTop = "";
          const draggedKey = ev.dataTransfer.getData("application/x-erp-child-section");
          if (!draggedKey || draggedKey === childKey) return;

          // Reorder this._childOrder — move dragged key before this section
          const order = this._childOrder || [];
          const draggedIdx = order.indexOf(draggedKey);
          const targetIdx = order.indexOf(childKey);
          if (draggedIdx < 0 || targetIdx < 0) return;

          order.splice(draggedIdx, 1);
          // Insert dragged BEFORE target (Marti's "dat nahoru" pattern)
          // Recompute targetIdx after splice (may have shifted)
          const newTargetIdx = order.indexOf(childKey);
          order.splice(newTargetIdx, 0, draggedKey);
          this._childOrder = order;

          // Re-render (preserve form data via this._spec, fresh DOM)
          this._render();
          this._attachDropTargetForGalleryDrag();
        });
      }  // /designMode

      // Hidden cols z select_columns (interní metadata)
      const HIDDEN_COLS = new Set([
        "id", "created_at", "updated_at", "created_by_id", "created_by_text",
        "updated_by_id", "updated_by_text",
      ]);
      const rows = childInfo.rows || [];
      // Visible cols z first row keys (or empty fallback)
      const sampleRow = rows[0] || {};
      const visibleCols = Object.keys(sampleRow).filter(
        c => !HIDDEN_COLS.has(c)
      );
      // Fallback pokud žádné rows — default columns z childInfo
      const cols = visibleCols.length > 0
        ? visibleCols
        : ["contact_value", "label", "is_primary", "is_verified", "status"];

      // Table
      const table = document.createElement("table");
      table.className = "erp-nested-grid";
      table.style.cssText =
        "width:100%;border-collapse:collapse;font-size:12px;margin-top:4px;";

      // Header row
      const thead = document.createElement("thead");
      const headerRow = document.createElement("tr");
      for (const col of cols) {
        const th = document.createElement("th");
        th.textContent = col;
        th.style.cssText =
          "padding:6px 8px;background:#141a20;border:1px solid #2a3340;" +
          "text-align:left;color:#8a96a4;font-size:11px;font-weight:600;";
        headerRow.appendChild(th);
      }
      // Actions column header — Phase 38.4 Krok 14d-D polish (14.5.2026
      // večer Marti's "tlacitko + v ramecku zelene v hlavicce gridu nad ✕"):
      // Místo prázdné header buňky → zelený + button (cleaner UX,
      // konzistentní pozice nad action column ✕ buttons per row).
      const thActions = document.createElement("th");
      thActions.style.cssText =
        "padding:4px;background:#141a20;border:1px solid #2a3340;" +
        "width:36px;text-align:center;";
      const headerAddBtn = document.createElement("button");
      headerAddBtn.type = "button";
      headerAddBtn.textContent = "+";
      headerAddBtn.title = "Přidat nový " + (childInfo.label || childKey);
      headerAddBtn.style.cssText =
        "background:transparent;border:1px solid #5dbf5d;color:#5dbf5d;" +
        "padding:0;width:22px;height:22px;border-radius:3px;cursor:pointer;" +
        "font-size:16px;font-weight:600;line-height:1;transition:background 0.15s;";
      headerAddBtn.addEventListener("mouseenter", () => {
        headerAddBtn.style.background = "rgba(93,191,93,0.15)";
      });
      headerAddBtn.addEventListener("mouseleave", () => {
        headerAddBtn.style.background = "transparent";
      });
      headerAddBtn.addEventListener("click", () => {
        this._addChildRow(childKey, childInfo);
      });
      thActions.appendChild(headerAddBtn);
      headerRow.appendChild(thActions);
      thead.appendChild(headerRow);
      table.appendChild(thead);

      // Body rows
      const tbody = document.createElement("tbody");
      if (rows.length === 0) {
        const tr = document.createElement("tr");
        const td = document.createElement("td");
        td.colSpan = cols.length + 1;
        td.style.cssText =
          "padding:14px;text-align:center;color:#5d6975;font-style:italic;" +
          "border:1px solid #2a3340;background:#0f141a;";
        td.textContent = "Žádné záznamy v " + (childInfo.label || childKey);
        tr.appendChild(td);
        tbody.appendChild(tr);
      } else {
        for (const row of rows) {
          tbody.appendChild(this._renderChildRow(childKey, childInfo, row, cols));
        }
      }
      table.appendChild(tbody);
      sec.grid.appendChild(table);

      // Phase 38.4 Krok 14d-D polish (14.5.2026 vecer, Marti's "tlacitko
      // + v ramecku v zelenem v hlavicce gridu nad tlacitka odebrat"):
      // Velký "+ Přidat" rectangle pod tabulkou dropped — nahrazený malým
      // zeleným + buttonem v header (above ✕ column). Cleaner UX, méně
      // visuálního noise.

      return sec.wrap;
    }

    _renderChildRow(childKey, childInfo, row, cols) {
      const tr = document.createElement("tr");
      tr.dataset.childRowId = String(row.id);

      for (const col of cols) {
        const td = document.createElement("td");
        td.style.cssText =
          "padding:5px 8px;border:1px solid #2a3340;color:#cfd6df;cursor:pointer;";
        td.title = "Dvojklik pro editaci";
        const v = row[col];
        if (typeof v === "boolean") {
          td.textContent = v ? "✓" : "";
          td.style.textAlign = "center";
          td.style.color = v ? "#5dbf5d" : "#5d6975";
        } else if (v == null) {
          td.textContent = "—";
          td.style.color = "#5d6975";
        } else {
          td.textContent = String(v);
        }
        // Dvojklik pro inline edit (MVP — native prompt)
        td.addEventListener("dblclick", (ev) => {
          ev.stopPropagation();
          this._editChildCell(childKey, childInfo, row, col, td);
        });
        tr.appendChild(td);
      }

      // Action — ✕ archive
      const tdAct = document.createElement("td");
      tdAct.style.cssText =
        "padding:5px 4px;border:1px solid #2a3340;text-align:center;background:#0f141a;";
      const archBtn = document.createElement("button");
      archBtn.type = "button";
      archBtn.textContent = "✕";
      archBtn.title = "Archivovat řádek (status='archived', soft delete)";
      archBtn.style.cssText =
        "background:transparent;border:1px solid #5a2828;color:#e57373;" +
        "padding:0;width:22px;height:22px;border-radius:3px;cursor:pointer;" +
        "font-size:11px;line-height:1;";
      archBtn.addEventListener("mouseenter", () => {
        archBtn.style.background = "#3a1f1f";
      });
      archBtn.addEventListener("mouseleave", () => {
        archBtn.style.background = "transparent";
      });
      archBtn.addEventListener("click", () => {
        this._archiveChildRow(childKey, childInfo, row);
      });
      tdAct.appendChild(archBtn);
      tr.appendChild(tdAct);

      return tr;
    }

    async _addChildRow(childKey, childInfo) {
      // Phase 38.4 Krok 14d-D polish (14.5.2026 vecer, Marti's "Popup
      // dialog zmen na dark theme"): _promptDarkDialog místo window.prompt.
      const label = childInfo.label || childKey;
      const value = await _promptDarkDialog({
        title: "Přidat " + label,
        message: "Zadej hodnotu (např. email adresa nebo telefonní číslo):",
        placeholder: "...",
        okLabel: "Přidat",
        cancelLabel: "Zrušit",
      });
      if (!value || !value.trim()) return;

      try {
        const url = "/api/v1/erp/fw-form/" +
          encodeURIComponent(this.opts.coreCode) + "/" +
          encodeURIComponent(this.opts.rowId) +
          "/children/" + encodeURIComponent(childKey);
        const r = await fetch(url, {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            contact_value: value.trim(),
            label: childInfo.default_label || null,
            is_primary: false,
            is_verified: false,
          }),
        });
        const d = await r.json();
        if (!r.ok || !d.ok) {
          throw new Error(d.error || "HTTP " + r.status);
        }
        _showToast("Přidáno: " + value, "success", 2500);
        await this._reloadSpec();
      } catch (e) {
        console.error("[DesignFwForm] _addChildRow failed:", e);
        _showToast("Přidání selhalo: " + (e.message || e), "error", 3500);
      }
    }

    async _editChildCell(childKey, childInfo, row, col, tdEl) {
      // Phase 38.4 Krok 14d-D polish (14.5.2026 vecer, Marti's "Popup
      // dialog zmen na dark theme"): _promptDarkDialog místo window.prompt.
      // Boolean cols: toggle (no dialog — instant flip)
      const currentVal = row[col];
      let newVal;
      if (typeof currentVal === "boolean") {
        newVal = !currentVal;
      } else {
        const input = await _promptDarkDialog({
          title: "Editovat " + col,
          message: "Aktuální hodnota: " + (currentVal == null ? "—" : currentVal),
          defaultValue: currentVal == null ? "" : String(currentVal),
          okLabel: "Uložit",
          cancelLabel: "Zrušit",
        });
        if (input == null) return;  // Cancel (Esc / × / Storno)
        newVal = input.trim() === "" ? null : input.trim();
        if (newVal === (currentVal == null ? null : String(currentVal))) return;  // No change
      }

      try {
        const url = "/api/v1/erp/fw-form/" +
          encodeURIComponent(this.opts.coreCode) + "/" +
          encodeURIComponent(this.opts.rowId) +
          "/children/" + encodeURIComponent(childKey) +
          "/" + encodeURIComponent(row.id);
        const r = await fetch(url, {
          method: "PATCH",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            [col]: newVal,
            expected_updated_at: row.updated_at,
          }),
        });
        const d = await r.json();
        if (r.status === 409) {
          // Concurrent edit conflict (Marti-AI's Q4 atomic guard)
          _showToast(
            "Konflikt — " + col + " mezitím změnil " +
            (d.by_user && d.by_user.short_name || "někdo") + ". Načti znovu.",
            "error", 4000
          );
          await this._reloadSpec();
          return;
        }
        if (!r.ok || !d.ok) {
          throw new Error(d.error || "HTTP " + r.status);
        }
        _showToast("Uloženo: " + col, "success", 2000);
        await this._reloadSpec();
      } catch (e) {
        console.error("[DesignFwForm] _editChildCell failed:", e);
        _showToast("Edit selhal: " + (e.message || e), "error", 3500);
      }
    }

    async _archiveChildRow(childKey, childInfo, row) {
      const display = row.contact_value || ("id=" + row.id);
      const confirmed = await _confirmDarkDialog({
        title: "Archivovat řádek?",
        message:
          "Archivovat '" + display + "' z " + (childInfo.label || childKey) + "?\n\n" +
          "(soft delete — status='archived', forensic audit zachovaný)",
      });
      if (!confirmed) return;

      try {
        const url = "/api/v1/erp/fw-form/" +
          encodeURIComponent(this.opts.coreCode) + "/" +
          encodeURIComponent(this.opts.rowId) +
          "/children/" + encodeURIComponent(childKey) +
          "/" + encodeURIComponent(row.id) + "/archive";
        const r = await fetch(url, {
          method: "PATCH",
          credentials: "include",
        });
        const d = await r.json();
        if (!r.ok || !d.ok) {
          throw new Error(d.error || "HTTP " + r.status);
        }
        _showToast("Archivováno: " + display, "success", 2500);
        await this._reloadSpec();
      } catch (e) {
        console.error("[DesignFwForm] _archiveChildRow failed:", e);
        _showToast("Archive selhal: " + (e.message || e), "error", 3500);
      }
    }

    // Reload spec po CRUD operations (parent + children refresh)
    async _reloadSpec() {
      try {
        const resp = await fetch(
          "/api/v1/erp/fw-form/" +
          encodeURIComponent(this.opts.coreCode) + "/" +
          encodeURIComponent(this.opts.rowId)
        );
        if (!resp.ok) throw new Error("HTTP " + resp.status);
        this._spec = await resp.json();
        if (!this._spec || !this._spec.ok) {
          throw new Error("Backend: " + (this._spec && this._spec.error || "unknown"));
        }
        this._render();
        // Re-attach drop target po _render (gotcha — _render přepisuje body innerHTML)
        this._attachDropTargetForGalleryDrag();
      } catch (e) {
        console.error("[DesignFwForm] _reloadSpec failed:", e);
        _showToast("Reload selhal: " + (e.message || e), "error", 3500);
      }
    }

    _applyDefaultSize() {
      // Krok 14b+11: read this._spec.form.layout.default_width/_height
      // (saved via 💾 Velikost button v DESIGN header). Apply jako inline
      // dialog.style. Pokud nejsou, fallback na default modal velikost
      // (920px width + min-height 500px z _buildModalShell).
      //
      // Krok 14b+12 (13.5.2026 ~23:30, Marti's "min velikost"): apply
      // i min_width / min_height pres dialog.style.minWidth/minHeight.
      // Browser native CSS min-* constraints prevent drag-resize pod min
      // (resize:both nemoze shrink pod min-width).
      if (!this._shell || !this._shell.dialog) return;
      const formLayout = (this._spec.form && this._spec.form.layout) || {};
      const dialog = this._shell.dialog;
      if (formLayout.default_width) {
        dialog.style.width = String(formLayout.default_width);
      }
      if (formLayout.default_height) {
        dialog.style.height = String(formLayout.default_height);
      }
      if (formLayout.min_width) {
        dialog.style.minWidth = String(formLayout.min_width);
      }
      if (formLayout.min_height) {
        dialog.style.minHeight = String(formLayout.min_height);
      }
      // Refresh button visibility — _attachFormDesignToggle se volal
      // PRED fetch spec, gates `this._spec.form.id` byly false. Teď spec
      // live, re-evaluate.
      this._updateFormSaveSizeBtn();
      this._updateFormDetectMinBtn();
    }

    _showError(msg) {
      if (this._shell && this._shell.body) {
        this._shell.body.innerHTML = "";
        const err = document.createElement("div");
        err.style.cssText = "padding:20px;color:#e88;background:#3a1818;border:1px solid #5a2828;border-radius:4px;margin:16px;";
        err.textContent = msg;
        this._shell.body.appendChild(err);
      }
    }

    _render() {
      this._shell.body.innerHTML = "";

      const core = this._spec.core;
      const form = this._spec.form;
      const fields = this._spec.fields || [];
      const data = this._spec.data || {};
      // Phase 38.4 Krok 14b+3 (13.5.2026 rano): template.layout takes precedence
      // over form.layout. template ma vlastni header / main / footer panels +
      // header/footer components (title / entity_badge / status_pill / button).
      // Forms bez template_id → fallback na form.layout (legacy pre-Krok 14b+1).
      const template = this._spec.template || null;

      // Phase 38.4 Krok 14g Etapa F Krok 5.F: refresh entity btn visibility
      // po _render (post-PATCH _spec.core.data_entity_type update reflektovat).
      try { this._updateFormEntityBtn(); } catch (e) {}
      try { this._updateFormAddFieldBtn(); } catch (e) {}

      // Phase 38.4 Krok 14g Etapa F Krok 5.A (16.5.2026, Marti's "core =
      // kontejner"): pokud core nema root comp_def (empty_container=true),
      // render placeholder + picker preparation message. Marti's "uniformita
      // vitezi nad specialnimi pripady" + "core je plocha, na ni se rozhodne
      // uzivatelsky co vlozit". Plny picker UI (Krok 5.B/5.C) prijde po
      // konzultaci s Marti-AI.
      if (form === null || this._spec.empty_container === true) {
        if (this._shell.title) {
          const _coreLabel = core.label
            || core.code
            || ("id=" + (core.id || "?"));
          this._shell.title.textContent = "Prázdný core · " + _coreLabel;
        }

        // Phase 38.4 Krok 14g Etapa F Krok 5.C (16.5.2026, Marti's "B
        // logicky krok"): origin provenance display + "A Zrusit asociaci
        // s potvrzenim" button. Origin payload from /by-id endpoint
        // (LEFT JOIN na origin_menu_node_id + origin_cmi_id).
        const origin = this._spec.origin || {};
        const ocmi = origin.cmi || null;
        const omn = origin.menu_node || null;

        // Origin banner (jen pokud aspon jeden origin set)
        const empty = document.createElement("div");
        empty.style.cssText =
          "padding:32px 32px;color:#8a96a4;" +
          "display:flex;flex-direction:column;align-items:center;gap:14px;";

        if (omn || ocmi) {
          const originBar = document.createElement("div");
          originBar.style.cssText =
            "background:rgba(139,115,85,0.12);" +
            "border:1px solid rgba(139,115,85,0.3);" +
            "border-radius:4px;padding:10px 14px;" +
            "font-size:12px;color:#d4b88a;width:100%;max-width:640px;" +
            "display:flex;justify-content:space-between;align-items:center;gap:12px;";
          let originHtml = '<div><span style="opacity:0.7;">Pochází z:</span> ';
          if (omn) {
            originHtml += '<span style="color:#a8c5dc;">📁 ' +
              _esc(omn.label || omn.code || ("menu_node#" + omn.id)) +
              '</span>';
          }
          if (omn && ocmi) originHtml += ' <span style="opacity:0.5;">→</span> ';
          if (ocmi) {
            originHtml += '<span style="color:#d4b88a;">📋 ' +
              _esc(ocmi.label || ocmi.code || ("cmi#" + ocmi.id)) +
              '</span>';
          }
          originHtml += '</div>';
          originBar.innerHTML = originHtml;

          // Zrusit asociaci button (jen pokud originCmiId set v opts)
          if (this.opts.originCmiId) {
            const btnUnlink = document.createElement("button");
            btnUnlink.type = "button";
            btnUnlink.textContent = "🚫 Zrušit asociaci";
            btnUnlink.style.cssText =
              "padding:5px 12px;font-size:11px;border-radius:3px;" +
              "background:rgba(212,135,135,0.12);" +
              "border:1px solid rgba(212,135,135,0.4);color:#d48787;" +
              "cursor:pointer;white-space:nowrap;";
            btnUnlink.onmouseenter = function () {
              btnUnlink.style.background = "rgba(212,135,135,0.22)";
            };
            btnUnlink.onmouseleave = function () {
              btnUnlink.style.background = "rgba(212,135,135,0.12)";
            };
            const self = this;
            btnUnlink.onclick = async function () {
              const cmiLabel = (ocmi && (ocmi.label || ocmi.code))
                || ("cmi#" + self.opts.originCmiId);
              const ok = window.confirm(
                "Zrušit asociaci kontejneru s '" + cmiLabel + "'?\n\n" +
                "Po potvrzení se kontextové menu vrátí do drafted stavu " +
                "(target_core_id = NULL). Při dalším pravém kliku se " +
                "otevře Kontejner picker pro novou volbu."
              );
              if (!ok) return;
              btnUnlink.disabled = true;
              btnUnlink.textContent = "Ruším…";
              try {
                const r = await fetch(
                  "/api/v1/erp/design/context-menu-item/" +
                    encodeURIComponent(self.opts.originCmiId) + "/link-core",
                  {
                    method: "PATCH",
                    headers: { "Content-Type": "application/json" },
                    credentials: "include",
                    body: JSON.stringify({ target_core_id: null }),
                  }
                ).then(function (rr) { return rr.json(); });
                if (r && r.ok) {
                  // Close modal — pri pristim kliku zase picker
                  try { self._shell.close(); } catch (e) {}
                } else {
                  btnUnlink.disabled = false;
                  btnUnlink.textContent = "🚫 Zrušit asociaci";
                  alert("Zrušení selhalo: " + ((r && r.error) || "unknown"));
                }
              } catch (e) {
                btnUnlink.disabled = false;
                btnUnlink.textContent = "🚫 Zrušit asociaci";
                alert("Zrušení selhalo (network): " + (e.message || e));
              }
            };
            originBar.appendChild(btnUnlink);
          }

          empty.appendChild(originBar);
        }

        // Big icon + headline + Marti doctrine
        const big = document.createElement("div");
        big.style.cssText =
          "display:flex;flex-direction:column;align-items:center;gap:14px;" +
          "padding:20px 0;";
        big.innerHTML =
          '<div style="font-size:64px;line-height:1;">🎨</div>' +
          '<div style="font-size:18px;color:#d4b88a;font-weight:600;">' +
          'Prázdný core kontejner' +
          '</div>' +
          '<div style="font-size:13px;max-width:480px;line-height:1.6;text-align:center;">' +
          '<code style="color:#8fb8d4;">' +
          _esc(core.code || ("id=" + (core.id || "?"))) +
          '</code> ' +
          'zatím nemá žádnou root komponentu. ' +
          'Marti doctrine: <em>„core = plocha, na ní se rozhodne uživatelsky ' +
          'co vložit (form 302, list, dashboard, ...)."</em>' +
          '</div>' +
          '<div style="font-size:12px;color:#6a7684;font-style:italic;margin-top:4px;">' +
          'Picker root komponenty přijde v Krok 5.D ' +
          '(po konzultaci s Marti-AI).' +
          '</div>';
        empty.appendChild(big);
        this._shell.body.appendChild(empty);
        return;
      }

      // Title z core.label (preferuj nad form.caption)
      if (this._shell.title) {
        this._shell.title.textContent = core.label || form.caption || core.code;
      }

      // Root content container — Phase 38.4 Krok 14b+5 polish #4
      // (13.5.2026 ~14:15, Marti's "main panel se na vysku nehybe"):
      // Switch z flex column chain na **CSS Grid 3-row layout**.
      //
      // Důvod: flex chain propagation byla křehká (margin-top:auto +
      // flex:1 + min-height:0 + nested wrappers). Pri jakémkoli broken
      // link na vyšší úrovni main panel zustaval natural-sized.
      //
      // CSS Grid s `grid-template-rows: auto 1fr auto` je DETERMINISTIC:
      //   - row 1: header (auto = natural height)
      //   - row 2: main (1fr = fills remaining space — alClient!)
      //   - row 3: footer (auto = natural)
      //
      // Vzdy funguje bez ohledu na parent dimensions (pokud root sám
      // ma height — z flex:1 v body).
      const root = document.createElement("div");
      root.className = "erp-design-tab-content";
      root.style.cssText =
        "padding:0;" +
        "display:grid;" +
        "grid-template-rows:auto 1fr auto;" +
        "flex:1 1 auto;" +
        "min-height:0;" +
        // Marti's polish (13.5.2026 ~15:15): gap mezi panel rows na
        // polovinu (14px → 7px) — compact spacing mezi header/main/footer.
        "gap:7px;";

      // Extract panels — template.layout (Krok 14b+3) > form.layout (legacy)
      let panels = [];
      let layoutSource = "form"; // pro debug
      if (template && template.layout) {
        const tLayout = (typeof template.layout === "string")
          ? JSON.parse(template.layout)
          : template.layout;
        if (Array.isArray(tLayout.panels)) {
          panels = tLayout.panels.slice();
          layoutSource = "template:" + (template.code || "?");
        }
      }
      if (panels.length === 0) {
        const formLayout = form.layout || {};
        if (Array.isArray(formLayout.panels)) {
          panels = formLayout.panels.slice();
          layoutSource = "form.layout";
        }
      }
      // Posledni fallback: default panel "main" (Marti's doctrine: panel je MANDATORY)
      if (panels.length === 0) {
        panels = [{ slot: "main", label: "", order: 10, components: [] }];
        layoutSource = "default-fallback";
      }
      console.info("[DesignFwForm] layout source:", layoutSource, "panels:", panels.length);

      // Sort panels by order
      panels.sort((a, b) => (a.order || 0) - (b.order || 0));

      // Phase 38.4 Krok 14e-C (14.5.2026 vecer): Build byParent map pro
      // recursive container rendering. Backend (Krok 14e-B) vraci flat list
      // ALL descendants of form (recursive CTE), kazdy s parent_comp_def_id.
      // Tree postaveni client-side groupingem.
      const byParent = new Map();
      for (const f of fields) {
        const pid = f.parent_comp_def_id;
        if (!byParent.has(pid)) byParent.set(pid, []);
        byParent.get(pid).push(f);
      }
      // Sort each parent's children by sort_order (z SQL uz seralene, ale
      // defensive — pripadny re-sort po DnD)
      for (const arr of byParent.values()) {
        arr.sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0));
      }

      // Group ONLY direct children of form root by region_slot (top-level
      // containers a/nebo leaf fields v legacy formech). Nested children
      // (groupbox -> fields) jdou pres recursive _renderComponentTree.
      const formChildren = byParent.get(form.id) || [];
      const fieldsBySlot = {};
      for (const f of formChildren) {
        const slot = f.region_slot || "main";
        if (!fieldsBySlot[slot]) fieldsBySlot[slot] = [];
        fieldsBySlot[slot].push(f);
      }

      // Render každý panel jako sekce
      const D = this._onDirty.bind(this);

      // Cache byParent + data + D pro recursive helper volane v loop nize
      // (musi byt AZ po `const D` declaraci — TDZ guard, jinak hodi
      // "Cannot access 'D' before initialization")
      this.__renderCtx = { byParent, data, onDirty: D };

      // Phase 38.4 Krok 14f-G (14.5.2026 vecer, Marti's "dropnul jsem
      // novy panel, zkopirovaly se gridy"): reset flag per _render cycle.
      // Child sections (TELEFONY/EMAILY) renderujeme JEN v prvnim alClient
      // panelu, ne ve vsech. Pokud Marti pridal alTop/alBottom/alLeft/
      // alRight, child sections zustavaji v alClient panelu (canonical
      // main area).
      this._childrenRenderedInAnyPanel = false;

      for (const panel of panels) {
        const slotFields = fieldsBySlot[panel.slot] || [];
        const templateComponents = Array.isArray(panel.components) ? panel.components : [];

        // Panel header — empty label = "panel je plocha" doctrine (12.5. 23:30)
        const sec = _sectionBuild(panel.label || "", "panel: " + panel.slot);

        // Phase 38.4 Krok 14b+5 polish #4 (13.5.2026 ~14:15): CSS Grid
        // 3-row layout v root (auto 1fr auto) reseni alClient deterministicky.
        // Sekce uz nepotrebuji flex magic — Grid jim assignuje row slot.
        // Per-panel jen styling specific (footer separator, main fill).
        //
        // Drop default margin-bottom: 14px z _sectionBuild — root grid
        // gap (7px po polish #7) ridi spacing mezi panel rows.
        sec.wrap.style.marginBottom = "0";

        if (panel.slot === "footer") {
          // Margin-bottom: 0 (vlastni grid row, no spacing below)
          sec.wrap.style.marginBottom = "0";
          // Visual separator nad footer
          sec.wrap.style.borderTop = "1px solid #2a3340";
          sec.wrap.style.paddingTop = "10px";
          // Krok 14b+16 (14.5.2026 rano, Marti's polish):
          //   - Discard btn (vlevo) + spacer (flex:1) + OK/Storno (vpravo)
          // Krok 14b+16.1 (14.5.2026 rano, Marti's catch "OK uteklo doprostred"):
          //   space-between s 3 children rozhazoval OK do stredu. Fix:
          //   flex spacer mezi discard a OK/Storno -> spacer absorbuje
          //   prostor, OK+Storno drzi vpravo. Konzistentni v obou stavech
          //   (discard visible/hidden).
          sec.grid.style.display = "flex";
          sec.grid.style.justifyContent = "flex-start";
          sec.grid.style.alignItems = "center";
          sec.grid.style.gap = "16px";

          // Inject dirty discard button na ZACATEK (vlevo)
          const discardBtn = document.createElement("button");
          discardBtn.type = "button";
          discardBtn.className = "erp-form-dirty-discard";
          discardBtn.style.cssText =
            "background:transparent;border:1px solid #5a4830;color:#d4b88a;" +
            "padding:5px 12px;border-radius:3px;cursor:pointer;font-size:11px;" +
            "font-style:italic;transition:background 0.15s,border-color 0.15s;" +
            "display:none;";  // initially hidden (count=0)
          discardBtn.title = "Klikni pro zrušení všech tebou provedených změn (vrátit původní hodnoty).";
          discardBtn.addEventListener("mouseenter", () => {
            discardBtn.style.background = "#1f1810";
            discardBtn.style.borderColor = "#7a5a3a";
          });
          discardBtn.addEventListener("mouseleave", () => {
            discardBtn.style.background = "transparent";
            discardBtn.style.borderColor = "#5a4830";
          });
          discardBtn.addEventListener("click", async () => {
            const decision = await _confirmDarkDialog({
              title: "Zrušit změny",
              message: "Chceš, abych tebou provedené změny zrušila?",
            });
            if (decision === true) {
              await this._revertAllChanges();
            }
          });
          this._dirtyDiscardBtn = discardBtn;
          sec.grid.appendChild(discardBtn);

          // Krok 14b+16.1: flex spacer aby OK+Storno drzela vpravo. Bez
          // ohledu na discard visibility (visible -> [discard][spacer]
          // [OK][Storno]; hidden -> [-][spacer][OK][Storno]).
          const spacer = document.createElement("div");
          spacer.className = "erp-form-footer-spacer";
          spacer.style.cssText = "flex:1 1 auto;";
          sec.grid.appendChild(spacer);

          // Update visibility podle aktualniho dirty count (volane po _render)
          this._updateDirtyDiscardBtn();
          // OK/Storno buttons (template footer komponenty) append v dalším loop.
        } else if (panel.slot === "main") {
          // Main je v Grid row 2 (1fr) — alClient automaticky.
          // Marti's polish (13.5.2026 ~14:45): "alClient ten panel" —
          // empty state hint MA rozsahnut na celou main panel area
          // (sec.grid je hint container, fills wrap fully).
          sec.wrap.style.minHeight = "0"; // critical pro grid 1fr shrink
          sec.wrap.style.display = "flex";
          sec.wrap.style.flexDirection = "column";
          sec.grid.style.flex = "1 1 auto";
          sec.grid.style.minHeight = "0";
          // Drop alignContent:start — necháme hint stretch fill
          // (alignContent default = stretch v grid s 1 item)
        }
        // header — no extra styling, Grid auto-rows assignuje natural height

        // Phase 38.4 Krok 14b+3: render template-level components (header/footer)
        // PRED fields (fields jsou typicky v 'main' panel, components v 'header' / 'footer')
        //
        // Krok 14b+7.2 (13.5.2026 ~20:45, Marti's "Zrus pomocne fieldy
        // Editace uživatele user #14 pending... jsou tam navic"): SKIP
        // title / entity_badge / status_pill template komponenty. Modal
        // title bar v _shell.title (z core.label) je sole title source —
        // template komponenty duplikuji informaci ktera je vzdy viditelna.
        // Buttons (OK/Storno) ZUSTAVAJI — to jsou funkcni actions, ne
        // pomocne pills.
        const SUPPRESSED_TEMPLATE_TYPES = new Set([
          "title", "entity_badge", "status_pill"
        ]);
        for (const comp of templateComponents) {
          const compType = comp && comp.type ? String(comp.type) : "";
          if (SUPPRESSED_TEMPLATE_TYPES.has(compType)) continue;  // skip
          const compEl = this._renderTemplateComponent(comp, core, data);
          if (compEl) sec.grid.appendChild(compEl);
        }

        // Phase 38.4 Krok 14e-C (14.5.2026 vecer): Recursive component
        // rendering. slotFields obsahuje TOP-LEVEL children form rootu pro
        // dany region_slot.
        //
        // Phase 38.4 Krok 14f-B (14.5.2026 vecer, Marti's B alClient):
        // Pokud slotFields obsahuje container (panel/groupbox) s layout.align,
        // pouzij Delphi VCL align layout (flexbox). Jinak fallback na
        // legacy per-field render.
        if (slotFields.length > 0) {
          slotFields.sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0));

          // Detect align system: aspoň jeden top-level container s layout.align
          const hasContainers = slotFields.some(
            (f) => f.comp_type_code === "panel" || f.comp_type_code === "groupbox"
          );

          if (hasContainers && panel.slot === "main") {
            // NEW Krok 14f-B: Delphi VCL align layout (flexbox)
            // Sec.grid musi být flex container (drop CSS Grid behavior)
            sec.grid.style.display = "flex";
            sec.grid.style.flexDirection = "column";
            sec.grid.style.minHeight = "0";
            sec.grid.style.padding = "0";
            sec.grid.style.gap = "0";
            const alignLayout = this._buildAlignLayout(slotFields);
            sec.grid.appendChild(alignLayout);
          } else {
            // LEGACY: per-field render (slot=header/footer, nebo flat fields)
            for (let idx = 0; idx < slotFields.length; idx++) {
              const f = slotFields[idx];
              const compEl = this._renderComponentTree(f, idx, slotFields.length);
              if (compEl) sec.grid.appendChild(compEl);
            }
          }
        }
        // Krok 14b+7.2 (13.5.2026 ~20:45, Marti's "to okno na formu pridat
        // dalsi pole je k nicemu... Nahradila ho tvoje futura v hlavicce +
        // Pole"): footer hint "+ Pridat dalsi pole" SMAZAN. Header button
        // "+ Pole" (z 14b+7.1) je sole entry point — vzdy visible v DESIGN
        // mode, nezavisly od panel content / scroll position. Empty hint
        // (v full-empty case) zustava — discoverability pro novy form.

        // Empty state — panel 'main' bez fields i bez template components
        if (templateComponents.length === 0 && slotFields.length === 0) {
          const hint = document.createElement("div");
          // Phase 38.4 Krok 14b+5 polish #6 (13.5.2026 ~14:45, Marti's
          // "alClient ten panel"): hint fills entire grid (1/-1 v obou
          // axes) + display:flex + center align aby text vystreden uprostred
          // velkeho boxu.
          //
          // Krok 14c (13.5.2026 odpoledne): hint je clickable trigger pro
          // FieldPickerModal.
          //
          // Krok 14b+7 (13.5.2026 ~20:00): hint je clickable JEN v DESIGN
          // mode. V PRODUCTION je hint neutralni info text bez click handleru
          // (uzivatel nesmi sahat na strukturu omylem). Marti's "PROD/DESIGN
          // trigger" doctrine — strukturalni zmeny vyzaduji explicit DESIGN
          // mode.
          const designMode = this._formDesignMode === true;
          const canPick = panel.slot === "main"
            && core.data_entity_type
            && (this._spec.form && this._spec.form.id)
            && typeof global.FieldPickerModal === "function";
          const interactive = designMode && canPick;

          hint.style.cssText =
            "padding:14px;background:#0f141a;border:1px dashed " +
            (interactive ? "#3a5a8a" : "#2a3340") + ";" +
            "border-radius:4px;color:#5d6975;font-style:italic;" +
            "text-align:center;grid-column:1/-1;grid-row:1/-1;" +
            "display:flex;align-items:center;justify-content:center;" +
            "cursor:" + (interactive ? "pointer" : "default") + ";" +
            "transition:background 0.15s,border-color 0.15s;";

          if (interactive) {
            hint.innerHTML =
              "(panel '" + panel.slot + "' nemá žádné fields)<br>" +
              "<span style=\"font-size:11px;color:#7ed4e8;margin-top:4px;\">" +
              "🎨 Klikni pro otevření palety komponent ➕" +
              "</span>";
          } else if (canPick) {
            // Production mode — info text s navodom prepnout DESIGN
            hint.innerHTML =
              "(panel '" + panel.slot + "' nemá žádné fields)<br>" +
              "<span style=\"font-size:11px;color:#7a8696;margin-top:4px;\">" +
              "Form je v PRODUCTION módu. Pro přidání polí přepni vpravo nahoře na 🎨 DESIGN." +
              "</span>";
          } else {
            // No picker available (entity_type / formId chybi / panel != main)
            hint.innerHTML = "(panel '" + panel.slot + "' nemá žádné fields)";
          }

          if (interactive) {
            // Hover visual (jen v design mode)
            hint.addEventListener("mouseenter", () => {
              hint.style.background = "#141a20";
              hint.style.borderColor = "#5a8aaa";
            });
            hint.addEventListener("mouseleave", () => {
              hint.style.background = "#0f141a";
              hint.style.borderColor = "#3a5a8a";
            });

            // Click → open FieldPickerModal (Krok 14b+7.1: shared helper)
            hint.addEventListener("click", () => {
              this._openFieldPicker();
            });
            hint.title = "Klikni pro otevření palety komponent (Krok 14c)";
          } else if (canPick) {
            hint.title = "Pro přidávání polí přepni form do DESIGN módu (button vpravo nahoře v header).";
          }

          sec.grid.appendChild(hint);
        }

        // Phase 38.4 Krok 14c+3 (14.5.2026 odpoledne, Marti's "drag-and-drop
        // na to spravne misto"): tag panel s data-region-slot pro drop
        // detection. Drop handler dohledá target panel pres Y coord +
        // dataset lookup.
        sec.wrap.dataset.regionSlot = panel.slot || "main";

        // Phase 38.4 Krok 14d-D polish 2 (14.5.2026 vecer, Marti's
        // "Gridy prosim dragabled pro presun nahoru do main"):
        // Main panel jako drop target pro children sections. Drop nad
        // main → child se přesune před main panel (this._childPosition).
        if (panel.slot === "main") {
          sec.wrap.addEventListener("dragover", (ev) => {
            const types = ev.dataTransfer && ev.dataTransfer.types;
            if (!types || !Array.from(types).includes("application/x-erp-child-section")) return;
            ev.preventDefault();
            ev.dataTransfer.dropEffect = "move";
            sec.wrap.style.borderTop = "3px solid #5dbf5d";
          });
          sec.wrap.addEventListener("dragleave", (ev) => {
            if (ev.target === sec.wrap || ev.currentTarget === sec.wrap) {
              sec.wrap.style.borderTop = "";
            }
          });
          sec.wrap.addEventListener("drop", (ev) => {
            const draggedKey = ev.dataTransfer.getData("application/x-erp-child-section");
            if (!draggedKey) return;
            ev.preventDefault();
            sec.wrap.style.borderTop = "";
            // Move child to before-main position
            this._childPosition = this._childPosition || {};
            this._childPosition[draggedKey] = "before-main";
            this._render();
            this._attachDropTargetForGalleryDrag();
            _showToast("Sekce přesunuta nahoru", "success", 1500);
          });
        }

        root.appendChild(sec.wrap);

        // Phase 38.4 Krok 14d-D polish 2: insert children with position=
        // 'before-main' RIGHT AFTER main panel — no, BEFORE main panel...
        // wait, we already appended main. We need to insert before.
        // Re-think: pojďme insert children-before-main PRED main append.
      }

      // Phase 38.4 Krok 14e-G (14.5.2026 vecer, Marti's "patri ty gridy
      // taky na panel?"): Child sections JIZ jsou rendered UVNITR panel
      // wrapper (viz _renderContainerNode pro 'panel'). Root level
      // child rendering NENI potreba — children sit pod panelem.
      //
      // _childOrder + _childPosition state initialization zachovan pro
      // backward compat (legacy forms bez panelu, kde panel je memory-only
      // virtual concept). _renderChildSection drag handlers stale pouzivaji
      // tyto pro position tracking.
      const childrenData = (this._spec && this._spec.children) || {};
      const allKeys = Object.keys(childrenData);
      if (allKeys.length > 0) {
        if (!this._childOrder || this._childOrder.length !== allKeys.length) {
          this._childOrder = [...allKeys];
        } else {
          this._childOrder = this._childOrder.filter(k => allKeys.includes(k));
          for (const k of allKeys) {
            if (!this._childOrder.includes(k)) this._childOrder.push(k);
          }
        }
        this._childPosition = this._childPosition || {};
      }
      // Defensive fallback: pokud form NEMA panel (legacy forms), render
      // children sections na root level (former behavior). Probehne jen
      // pokud root nema zadny .erp-design-panel descendant po render.
      if (allKeys.length > 0 && !root.querySelector(".erp-design-panel")) {
        console.warn(
          "[DesignFwForm] form nemá panel container — render child sections " +
          "na root level (legacy fallback). Doporuceni: pridat panel " +
          "(comp_type_code='panel') jako prvni dite form rootu."
        );
        const beforeMain = this._childOrder.filter(
          k => this._childPosition[k] === "before-main"
        );
        const afterMain = this._childOrder.filter(
          k => this._childPosition[k] !== "before-main"
        );
        if (beforeMain.length > 0) {
          const mainPanelEl = root.querySelector('[data-region-slot="main"]');
          for (const childKey of beforeMain) {
            const childInfo = childrenData[childKey];
            if (!childInfo) continue;
            const childSec = this._renderChildSection(childKey, childInfo);
            if (mainPanelEl) {
              root.insertBefore(childSec, mainPanelEl);
            } else {
              root.appendChild(childSec);
            }
          }
        }
        for (const childKey of afterMain) {
          const childInfo = childrenData[childKey];
          if (!childInfo) continue;
          root.appendChild(this._renderChildSection(childKey, childInfo));
        }
      }

      this._shell.body.appendChild(root);

      // Phase 38.4 Krok 14g-C (15.5.2026 rano, Marti's "videt v separatnim
      // liste graficky schema toho layoutu"): floating right-side schema
      // tree panel. DESIGN mode only. Persistent state v localStorage
      // (Marti's "videt co se stalo" debugging when form je v broken
      // state).
      if (this._formDesignMode === true) {
        this._renderSchemaTreePanel();
      }

      // Phase 38.4 Krok 14b+5 polish (13.5.2026 dopoledne, Marti's
      // request): footer template's OK/Storno tlacitka jsou jedine
      // close actions — modal shell footer (Zavřít) ZRUSENO. Konsolidace
      // UX: jedna paticka, jedne actions.
      // Hide shell footer pokud existuje (defensive — _buildModalShell
      // muze default render footer s padding).
      if (this._shell && this._shell.footer) {
        this._shell.footer.style.display = "none";
      }
    }

    // ════════════════════════════════════════════════════════════════
    // Phase 38.4 Krok 14g-C (15.5.2026 rano, Marti's "schema layoutu
    // v separatnim liste"): read-only schema tree side panel.
    //
    // Floating fixed-position container vpravo (z-index nad form modal).
    // Toggle pres button v DESIGN header. Persistent open/closed state
    // v localStorage ("erp_design_schema_tree_open").
    //
    // Tree displays form.id root + all descendants z this._spec.fields
    // (recursive CTE response z Krok 14e-B). Per node:
    //   - Indentace podle depth (level * 16px)
    //   - Icon emoji per code (▦ panel, ▣ groupbox, ○ leaf)
    //   - Color: panel purple, groupbox amber, leaf gray
    //   - Display: code · #id · caption
    //
    // Click na node → scroll do view + flash. Plus ✕ per row =
    // emergency delete (calls _performFieldDelete).
    // ════════════════════════════════════════════════════════════════
    _renderSchemaTreePanel() {
      // Cleanup existing panel (re-render scenario)
      const existing = document.body.querySelector(".erp-schema-tree-panel");
      if (existing) {
        try { document.body.removeChild(existing); } catch (e) {}
      }

      // Read persistent open state
      const STORAGE_KEY = "erp_design_schema_tree_open";
      let isOpen;
      try {
        isOpen = localStorage.getItem(STORAGE_KEY) === "1";
      } catch (e) {
        isOpen = false;
      }

      // Container — fixed position vpravo, collapsible
      const panel = document.createElement("div");
      panel.className = "erp-schema-tree-panel";
      panel.style.cssText =
        "position:fixed;top:80px;right:" + (isOpen ? "16px" : "-340px") + ";" +
        "width:360px;max-height:calc(100vh - 120px);" +
        "background:#0d1117;border:1px solid #2a3340;border-radius:6px;" +
        "color:#cfd6df;font-size:12px;font-family:inherit;" +
        "box-shadow:-4px 0 16px rgba(0,0,0,0.5);" +
        "display:flex;flex-direction:column;z-index:10001;" +
        "transition:right 0.25s ease;";

      // Toggle handle button (always visible, attached to panel right edge)
      const handle = document.createElement("button");
      handle.type = "button";
      handle.title = isOpen ? "Skryj schema (Esc)" : "Ukaz schema layoutu";
      handle.style.cssText =
        "position:absolute;top:50%;left:-32px;transform:translateY(-50%);" +
        "width:32px;height:64px;background:#1a2028;border:1px solid #2a3340;" +
        "border-right:none;border-radius:6px 0 0 6px;color:#a88cd4;" +
        "cursor:pointer;font-size:14px;line-height:1;" +
        "display:flex;align-items:center;justify-content:center;" +
        "writing-mode:vertical-rl;letter-spacing:1px;";
      handle.innerHTML = "🌳 " + (isOpen ? "▶" : "◀");
      handle.addEventListener("click", () => {
        const opening = panel.style.right === "-340px" || panel.style.right === "";
        panel.style.right = opening ? "16px" : "-340px";
        handle.innerHTML = "🌳 " + (opening ? "▶" : "◀");
        handle.title = opening ? "Skryj schema (Esc)" : "Ukaz schema layoutu";
        try {
          localStorage.setItem(STORAGE_KEY, opening ? "1" : "0");
        } catch (e) {}
      });
      panel.appendChild(handle);

      // Header
      const header = document.createElement("div");
      header.style.cssText =
        "padding:10px 14px;background:#1a2028;border-bottom:1px solid #2a3340;" +
        "display:flex;align-items:center;justify-content:space-between;" +
        "border-radius:6px 6px 0 0;flex-shrink:0;";
      const title = document.createElement("div");
      title.style.cssText = "font-weight:600;font-size:13px;";
      const fields = this._spec.fields || [];
      const counts = {
        panel: fields.filter(f => f.comp_type_code === "panel").length,
        groupbox: fields.filter(f => f.comp_type_code === "groupbox").length,
        leaf: fields.filter(f =>
          f.comp_type_code !== "panel" && f.comp_type_code !== "groupbox"
        ).length,
      };
      title.innerHTML = "🌳 Schema · <span style=\"color:#7a8696;font-weight:400;\">" +
                        counts.panel + " panely · " + counts.groupbox + " groupboxy · " +
                        counts.leaf + " fields</span>";
      header.appendChild(title);
      panel.appendChild(header);

      // Body — scrollable tree
      const body = document.createElement("div");
      body.style.cssText =
        "padding:8px 4px;overflow-y:auto;flex:1 1 auto;min-height:0;" +
        "font-family:ui-monospace,Consolas,monospace;";
      panel.appendChild(body);

      // Build tree z byParent map (same algorithm as _render but for display)
      const byParent = new Map();
      for (const f of fields) {
        const pid = f.parent_comp_def_id;
        if (!byParent.has(pid)) byParent.set(pid, []);
        byParent.get(pid).push(f);
      }
      for (const arr of byParent.values()) {
        arr.sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0));
      }

      // Root marker — form root
      const form = this._spec.form;
      if (form) {
        const rootNode = this._buildSchemaTreeNode(
          { id: form.id, comp_type_code: "form", caption: this._spec.core.label || form.caption || form.name },
          0,
          /*isRoot*/ true
        );
        body.appendChild(rootNode);
      }

      // Walk byParent recursively start from form.id
      const _walk = (parentId, depth) => {
        const children = byParent.get(parentId) || [];
        for (const child of children) {
          const node = this._buildSchemaTreeNode(child, depth, false);
          body.appendChild(node);
          // Recurse only for containers
          if (child.comp_type_code === "panel" || child.comp_type_code === "groupbox") {
            _walk(child.id, depth + 1);
          }
        }
      };
      if (form) _walk(form.id, 1);

      // Empty state
      if (fields.length === 0) {
        const empty = document.createElement("div");
        empty.style.cssText = "padding:20px;text-align:center;color:#5d6975;font-style:italic;";
        empty.textContent = "Žádné komponenty v formuláři.";
        body.appendChild(empty);
      }

      document.body.appendChild(panel);
      this._schemaTreePanel = panel;
    }

    _buildSchemaTreeNode(comp, depth, isRoot) {
      const code = comp.comp_type_code;
      const isContainer = code === "panel" || code === "groupbox";
      const isForm = code === "form";

      // Color + icon per type
      let icon, color;
      if (isForm) { icon = "▣"; color = "#7ed4e8"; }
      else if (code === "panel") { icon = "▦"; color = "#a88cd4"; }
      else if (code === "groupbox") { icon = "▤"; color = "#d4b88a"; }
      else { icon = "○"; color = "#9ba8b8"; }

      const node = document.createElement("div");
      node.className = "erp-schema-tree-node";
      node.dataset.compDefId = String(comp.id);
      node.dataset.compTypeCode = code;
      node.style.cssText =
        "display:flex;align-items:center;gap:6px;" +
        "padding:3px 8px 3px " + (8 + depth * 14) + "px;" +
        "cursor:pointer;border-left:2px solid transparent;" +
        "transition:background 0.1s, border-left-color 0.1s;";
      node.addEventListener("mouseenter", () => {
        // Highlight jen pokud ne v drag mode (dragover override)
        if (!this._schemaTreeDragging) {
          node.style.background = "#141a20";
          node.style.borderLeftColor = color;
        }
      });
      node.addEventListener("mouseleave", () => {
        if (!this._schemaTreeDragging) {
          node.style.background = "";
          node.style.borderLeftColor = "transparent";
        }
      });

      // Phase 38.4 Krok 14g-E (15.5.2026 rano, Marti's "drop ve strome"):
      // Drag-and-drop reorder/move pres schema tree. Non-root, non-form
      // nodes draggable. Pres _dragState pipeline.
      if (!isRoot && !isForm) {
        node.draggable = true;
        node.addEventListener("dragstart", (ev) => {
          ev.stopPropagation();
          this._schemaTreeDragging = true;
          node.style.opacity = "0.5";
          this._dragState = {
            fieldId: comp.id,
            fromIndex: 0,
            el: node,
            isContainer: isContainer,
            fromSchemaTree: true,
          };
          try {
            ev.dataTransfer.effectAllowed = "move";
            ev.dataTransfer.setData("text/plain", "schema:" + comp.id);
          } catch (e) {}
        });
        node.addEventListener("dragend", () => {
          this._schemaTreeDragging = false;
          node.style.opacity = "";
          // Clean all node highlights
          const panel = document.body.querySelector(".erp-schema-tree-panel");
          if (panel) {
            panel.querySelectorAll(".erp-schema-tree-node").forEach((n) => {
              n.style.background = "";
              n.style.borderLeftColor = "transparent";
              n.style.outline = "";
            });
          }
          this._dragState = null;
        });
        node.addEventListener("dragover", (ev) => {
          if (!this._dragState || !this._dragState.fromSchemaTree) return;
          if (this._dragState.fieldId === comp.id) return;
          ev.preventDefault();
          ev.stopPropagation();
          try { ev.dataTransfer.dropEffect = "move"; } catch (e) {}
          // Visual: container target = outline INSIDE (move INTO)
          //         non-container = top/bottom edge (reorder)
          if (isContainer) {
            node.style.background = "rgba(168, 140, 212, 0.15)";
            node.style.outline = "2px solid #a88cd4";
            node.style.outlineOffset = "-2px";
          } else {
            const rect = node.getBoundingClientRect();
            const isAbove = (ev.clientY - rect.top) < (rect.height / 2);
            node.style.borderTop = isAbove ? "3px solid #7ed4e8" : "2px solid transparent";
            node.style.borderBottom = isAbove ? "2px solid transparent" : "3px solid #7ed4e8";
            node.style.background = "rgba(126, 212, 232, 0.08)";
          }
        });
        node.addEventListener("dragleave", () => {
          node.style.background = "";
          node.style.outline = "";
          node.style.borderTop = "";
          node.style.borderBottom = "";
        });
        node.addEventListener("drop", (ev) => {
          if (!this._dragState || !this._dragState.fromSchemaTree) return;
          ev.preventDefault();
          ev.stopPropagation();
          const fromId = this._dragState.fieldId;
          const toId = comp.id;
          if (fromId === toId) return;
          // Clear visual
          node.style.background = "";
          node.style.outline = "";
          node.style.borderTop = "";
          node.style.borderBottom = "";

          if (isContainer) {
            // Drop ON container → move INTO (parent_comp_def_id = container.id)
            const fields = this._spec.fields || [];
            const fromComp = fields.find((f) => f.id === fromId);
            if (fromComp && fromComp.parent_comp_def_id === comp.id) {
              _showToast("Komponenta uz je v tomto kontejneru", "info", 1500);
              return;
            }
            this._performFieldMove(fromId, comp.id);
          } else {
            // Drop on sibling (leaf field) → reorder OR cross-parent
            const rect = node.getBoundingClientRect();
            const isAbove = (ev.clientY - rect.top) < (rect.height / 2);
            this._performFieldReorder(fromId, toId, isAbove);
          }
        });
      }

      // Icon
      const iconEl = document.createElement("span");
      iconEl.textContent = icon;
      iconEl.style.cssText = "color:" + color + ";font-size:13px;line-height:1;flex-shrink:0;";
      node.appendChild(iconEl);

      // Code
      const codeEl = document.createElement("span");
      codeEl.textContent = code;
      codeEl.style.cssText = "color:" + color + ";font-weight:600;flex-shrink:0;";
      node.appendChild(codeEl);

      // #id
      const idEl = document.createElement("span");
      idEl.textContent = "#" + comp.id;
      idEl.style.cssText = "color:#5d6975;font-size:10px;flex-shrink:0;";
      node.appendChild(idEl);

      // Caption + align/border info
      let captionText = comp.caption || comp.name || "";
      if (comp.layout) {
        if (code === "panel" && comp.layout.align) {
          captionText += " · " + comp.layout.align;
        } else if (code === "groupbox" && comp.layout.border_mode) {
          captionText += " · " + comp.layout.border_mode;
        }
      }
      if (captionText) {
        const capEl = document.createElement("span");
        capEl.textContent = captionText;
        capEl.style.cssText = "color:#cfd6df;font-size:11px;flex:1 1 auto;" +
                              "overflow:hidden;text-overflow:ellipsis;white-space:nowrap;";
        node.appendChild(capEl);
      } else {
        const spacer = document.createElement("span");
        spacer.style.cssText = "flex:1 1 auto;";
        node.appendChild(spacer);
      }

      // Action buttons (jen pro non-root, non-form)
      if (!isRoot && !isForm) {
        // ⚙ Settings
        const settingsBtn = document.createElement("button");
        settingsBtn.type = "button";
        settingsBtn.textContent = "⚙";
        settingsBtn.title = "Nastaveni komponenty";
        settingsBtn.style.cssText =
          "background:transparent;border:none;color:#5d6975;" +
          "cursor:pointer;font-size:11px;padding:2px 4px;line-height:1;" +
          "border-radius:2px;transition:color 0.1s;";
        settingsBtn.addEventListener("mouseenter", () => {
          settingsBtn.style.color = "#a88cd4";
        });
        settingsBtn.addEventListener("mouseleave", () => {
          settingsBtn.style.color = "#5d6975";
        });
        settingsBtn.addEventListener("click", (ev) => {
          ev.stopPropagation();
          if (isContainer) {
            this._openContainerSettings(comp);
          } else {
            this._openFieldSettings(comp);
          }
        });
        node.appendChild(settingsBtn);

        // ✕ Delete
        const delBtn = document.createElement("button");
        delBtn.type = "button";
        delBtn.textContent = "✕";
        delBtn.title = "Smazat tuto komponentu";
        delBtn.style.cssText =
          "background:transparent;border:none;color:#5d2828;" +
          "cursor:pointer;font-size:11px;padding:2px 4px;line-height:1;" +
          "border-radius:2px;transition:color 0.1s;";
        delBtn.addEventListener("mouseenter", () => {
          delBtn.style.color = "#e57373";
        });
        delBtn.addEventListener("mouseleave", () => {
          delBtn.style.color = "#5d2828";
        });
        delBtn.addEventListener("click", async (ev) => {
          ev.stopPropagation();
          const decision = await _confirmDarkDialog({
            title: "Smazat z schema",
            message: "Smazat " + code + " '" + (comp.caption || comp.name) +
                     "' (#" + comp.id + ")?\n\n(soft-delete, audit zustava)",
          });
          if (decision !== true) return;
          await this._performFieldDelete(comp);
        });
        node.appendChild(delBtn);
      }

      // Click on node — scroll do view + flash
      node.addEventListener("click", () => {
        if (isRoot || isForm) return;
        const targetEl = this._shell && this._shell.body &&
          this._shell.body.querySelector('[data-comp-def-id="' + comp.id + '"]') ||
          this._shell.body.querySelector('[data-field-id="' + comp.id + '"]');
        if (targetEl) {
          targetEl.scrollIntoView({ behavior: "smooth", block: "center" });
          // Flash highlight
          const orig = targetEl.style.outline;
          targetEl.style.outline = "3px solid " + color;
          targetEl.style.outlineOffset = "2px";
          targetEl.style.transition = "outline-color 0.6s ease";
          setTimeout(() => {
            targetEl.style.outline = orig;
            targetEl.style.outlineOffset = "";
          }, 1200);
        }
      });

      return node;
    }

    // Phase 38.4 Krok 14b+3 (13.5.2026 rano): render template-level component.
    // template.layout.panels[].components = [{type: 'title'|'entity_badge'|'status_pill'|'button', ...}]
    // - title: source='core.label' -> velky text
    // - entity_badge: format='{entity_type} #{row_id}' -> maly badge
    // - status_pill: source='data.status', optional=true -> colored pill (jen pokud data.status exists)
    // - button: action='save_and_close'|'abandon' -> visual button s onClick (Save flow Krok 14b+5 wire-up)
    _renderTemplateComponent(comp, core, data) {
      if (!comp || !comp.type) return null;
      const compType = comp.type;
      try {
        if (compType === "title") {
          const el = document.createElement("h2");
          el.className = "erp-fw-template-title";
          el.style.cssText = "margin:0 0 8px;font-size:18px;font-weight:600;color:#e8eef5;grid-column:1/-1;";
          el.textContent = this._resolveTemplateSource(comp.source, core, data) || core.label || "(bez nazvu)";
          return el;
        }
        if (compType === "entity_badge") {
          const el = document.createElement("span");
          el.className = "erp-fw-template-badge";
          el.style.cssText = "display:inline-block;padding:2px 8px;background:rgba(74,123,168,0.18);border:1px solid rgba(74,123,168,0.4);border-radius:10px;font-size:11px;color:#9bb5d6;font-family:'JetBrains Mono',monospace;grid-column:1/-1;justify-self:start;";
          const entityType = core.data_entity_type || "?";
          const rowId = (data && (data.id != null ? data.id : data.ID != null ? data.ID : "?")) ?? "?";
          const format = comp.format || "{entity_type} #{row_id}";
          el.textContent = format
            .replace("{entity_type}", entityType)
            .replace("{row_id}", rowId);
          return el;
        }
        if (compType === "status_pill") {
          const value = this._resolveTemplateSource(comp.source, core, data);
          if (value == null || value === "") {
            // Marti-AI's 'optional: true' doctrine — skip render pokud chybi
            if (comp.optional) return null;
            // ELSE: render empty pill (visible že tam má být status)
          }
          const el = document.createElement("span");
          el.className = "erp-fw-template-status-pill";
          el.style.cssText = "display:inline-block;padding:2px 10px;border-radius:10px;font-size:11px;font-weight:500;grid-column:1/-1;justify-self:start;";
          // Color by status
          const stat = String(value || "").toLowerCase();
          if (stat === "active") {
            el.style.background = "rgba(80,150,80,0.18)";
            el.style.border = "1px solid rgba(80,150,80,0.5)";
            el.style.color = "#8bc88b";
          } else if (stat === "pending") {
            el.style.background = "rgba(180,140,60,0.18)";
            el.style.border = "1px solid rgba(180,140,60,0.5)";
            el.style.color = "#d4b88a";
          } else if (stat === "disabled") {
            el.style.background = "rgba(180,80,80,0.18)";
            el.style.border = "1px solid rgba(180,80,80,0.5)";
            el.style.color = "#d4888a";
          } else {
            el.style.background = "rgba(140,140,140,0.18)";
            el.style.border = "1px solid rgba(140,140,140,0.5)";
            el.style.color = "#9ca3af";
          }
          el.textContent = value || "(no status)";
          return el;
        }
        if (compType === "button") {
          // Phase 38.4 Krok 14b+3 visual MVP -> Krok 14b+5 LIVE Save flow.
          // 13.5.2026 ~12:30 polish (Marti's request):
          //   - Standardni sirka (min/max constraint), ne grid-full
          //   - ✓ green check icon na save action, ✗ red cross na abandon
          //   - Right-aligned v grid cell (justify-self: end)
          //
          // action='save_and_close' -> PATCH endpoint + close modal
          // action='abandon' -> dirty check -> "Mám uložit změny?" modal
          const el = document.createElement("button");
          el.type = "button";
          el.className = "erp-fw-template-btn";
          const variant = comp.variant || "secondary";
          const action = comp.action || "noop";

          // Icon prefix podle action (ne podle variant — variant je color,
          // action je semantic: save vs abandon vs custom)
          let iconHtml = "";
          if (action === "save_and_close") {
            iconHtml = '<span style="color:#5dbf5d;font-weight:700;margin-right:6px;">✓</span>';
          } else if (action === "abandon") {
            iconHtml = '<span style="color:#d4888a;font-weight:700;margin-right:6px;">✗</span>';
          }
          // Custom actions (future) — ne forcing icon

          // Sirka: min 90px (visible), max 140px (compact). margin pro
          // mezeru mezi buttons. grid-column: auto + justify-self: end aby
          // sedele do flex-end pravidla footer panel.
          const sizeStyle =
            "min-width:90px;max-width:140px;padding:6px 16px;" +
            "border-radius:3px;cursor:pointer;font-size:13px;" +
            "margin:6px 4px 0 0;grid-column:auto;justify-self:end;";

          if (variant === "primary") {
            el.style.cssText = sizeStyle +
              "background:#3a5a8a;border:1px solid #4a7ba8;color:#e8eef5;font-weight:600;";
          } else {
            el.style.cssText = sizeStyle +
              "background:#2a3340;border:1px solid #3a4754;color:#cfd6df;";
          }
          el.innerHTML = iconHtml + (comp.label || "(button)");
          el.addEventListener("click", async () => {
            console.info("[DesignFwForm] template button click — action:", action);
            // Phase 38.4 Krok 14b+5 (13.5.2026 dopoledne): Save flow LIVE
            if (action === "save_and_close") {
              await this._handleSaveAndClose(el);
            } else if (action === "abandon") {
              // Reuse existing _beforeCloseHandler (dirty check + close)
              this._shell.close();
            } else {
              alert("Unknown action: " + action);
            }
          });
          return el;
        }
        // Unknown component type → log + skip
        console.warn("[DesignFwForm] unknown template component type:", compType, comp);
        return null;
      } catch (e) {
        console.error("[DesignFwForm] template component render error:", e, comp);
        return null;
      }
    }

    // Helper — resolve template source path (e.g. 'core.label' -> core.label, 'data.status' -> data.status)
    _resolveTemplateSource(source, core, data) {
      if (!source) return null;
      const parts = String(source).split(".");
      let cur = null;
      if (parts[0] === "core") cur = core;
      else if (parts[0] === "data") cur = data;
      else return null;
      for (let i = 1; i < parts.length; i++) {
        if (cur == null) return null;
        cur = cur[parts[i]];
      }
      return cur;
    }

    // Phase 38.4 Krok 14b+5 (13.5.2026 dopoledne): OK button save_and_close action
    // Marti's Centrala 1 doctrine: "OK = optimistic save + close. Bez ptaní."
    //
    // Flow:
    //   1. Collect dirty field changes z this._dirty Set (field values z DOM)
    //   2. Pokud žádné changes -> just close (clean OK = no-op + close)
    //   3. POST PATCH /api/v1/erp/design/{entity}/{id} s field_changes + expected_updated_at
    //   4. 200 -> green toast "Uloženo" + close modal
    //   5. 409 -> dialog "Někdo jiný mezitím změnil řádek. Načíst znovu?"
    //   6. Jiná chyba -> error toast, modal zůstane otevřený (user může retry)
    async _handleSaveAndClose(btnEl) {
      // Visual: btn disabled + "Ukládám..." během PATCH
      // (preserve HTML innerHTML aby icon mohl být restored při error revert)
      const originalHtml = btnEl.innerHTML;
      btnEl.disabled = true;
      btnEl.innerHTML = "⏳ Ukládám…";

      try {
        const core = this._spec.core;
        const data = this._spec.data || {};
        const entityType = core.data_entity_type;
        const rowId = data.id != null ? data.id : (data.ID != null ? data.ID : null);
        const expectedUpdatedAt = data.updated_at;

        // Krok 5.I-G hotfix (16.5.2026 ~22:45, Marti's "Save selhal: missing
        // entity_type nebo row_id" pri pickeru-only zmenach): NE early-exit.
        // Pokud user mení JEN entity_picker comp_def root (no core data
        // changes), nepotrebujeme entity_type/row_id. Validace presunuta na
        // conditional check po collect — vyžadována jen pri fieldChanges
        // non-empty (core entity save flow).

        // Collect dirty changes z DOM. _field / _dropdown helpers ukladaji
        // wrap._fieldKey + wrap._inst (UI Kit instance). Walkujem vsechny
        // wrap divy v body a filtrujem ty co maji fieldKey v this._dirty.
        const fieldChanges = {};
        const allWraps = this._shell.body.querySelectorAll(".erp-field, .erp-dropdown, .erp-memo");
        for (const wrap of allWraps) {
          const fk = wrap._fieldKey;
          if (!fk || !this._dirty.has(fk)) continue;
          // fieldKey format: "<core.code>.<field.name>" -> extract field name
          const parts = fk.split(".");
          if (parts.length < 2) continue;
          const fieldName = parts.slice(1).join(".");
          // Get current value via UI Kit instance (.value() method) nebo
          // fallback na DOM input.value
          let val = null;
          if (wrap._inst && typeof wrap._inst.value === "function") {
            val = wrap._inst.value();
          } else if (wrap._inst && wrap._inst.input) {
            val = wrap._inst.input.value;
          } else {
            const inp = wrap.querySelector("input, textarea, select");
            if (inp) val = inp.value;
          }
          fieldChanges[fieldName] = val;
        }

        // Phase 38.4 Krok 14g Etapa F Krok 5.I-G (16.5.2026 vecer): collect
        // entity_picker changes pro comp_def root PATCH (Marti's two-layer
        // data_source pattern). Picker #3 Datovy zdroj (display_mode='editable',
        // field_extern='data_source_id') ukladame na form root comp_def.
        const compDefChanges = {};
        const pickerWraps = this._shell.body.querySelectorAll(".erp-entity-picker-host");
        for (const pwrap of pickerWraps) {
          if (pwrap._displayMode !== "editable" || !pwrap._fieldExtern) continue;
          const initialId = pwrap._initialValue ? pwrap._initialValue.id : null;
          // _selectedValue je null po unlink, undefined pred user action.
          // Pokud undefined -> stale na initial. Pokud null nebo new value -> changed.
          let currentId;
          if (pwrap._selectedValue === undefined) {
            currentId = initialId;
          } else if (pwrap._selectedValue === null) {
            currentId = null;
          } else {
            currentId = pwrap._selectedValue.id;
          }
          if (currentId !== initialId) {
            compDefChanges[pwrap._fieldExtern] = currentId;
          }
        }

        // Pokud žádné changes -> clean close (Marti's "OK clean = close" doctrine)
        if (Object.keys(fieldChanges).length === 0 && Object.keys(compDefChanges).length === 0) {
          console.info("[DesignFwForm] OK clicked, no dirty changes — closing.");
          this._dirty.clear();
          _markFormDirty(this, false);
          this._shell.close();
          return;
        }

        // Krok 5.I-G: PATCH 1 — core entity (existing behavior, pokud
        // jsou core field changes)
        let savedFieldsCount = 0;
        let lastRespData = null;
        if (Object.keys(fieldChanges).length > 0) {
          // Krok 5.I-G hotfix (16.5.2026 ~22:45): validace entity context
          // PRESUNUTA sem (early exit v top byla too strict — blokovalo i
          // picker-only changes pres comp_def root). Aktivuje se jen pokud
          // user opravdu modifikoval core entity sloupce.
          if (!entityType || rowId == null) {
            alert(
              "Save selhal: missing entity_type nebo row_id\n\n" +
              "Core entity changes detected (" +
              Object.keys(fieldChanges).join(", ") +
              ") ale form nema kontext entity row."
            );
            btnEl.disabled = false;
            btnEl.innerHTML = originalHtml;
            return;
          }
          const r = await fetch(
            "/api/v1/erp/design/" + encodeURIComponent(entityType) + "/" + encodeURIComponent(rowId),
            {
              method: "PATCH",
              credentials: "include",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                field_changes: fieldChanges,
                expected_updated_at: expectedUpdatedAt,
              }),
            }
          );

          if (r.status === 409) {
            const errData = await r.json().catch(() => ({}));
            alert(
              "Konflikt na " + entityType + ": někdo jiný mezitím změnil tento řádek.\\n" +
              "Server čas: " + (errData.server_updated_at || "?") + "\\n" +
              "Tvůj čas: " + (errData.expected_updated_at || "?") + "\\n\\n" +
              "Zavři modal a otevři znovu (Enter / dvojklik), tvé změny budou ztraceny."
            );
            btnEl.disabled = false;
            btnEl.innerHTML = originalHtml;
            return;
          }

          if (!r.ok) {
            const errData = await r.json().catch(() => ({}));
            alert(
              "Uložení " + entityType + " selhalo: HTTP " + r.status + "\\n" +
              (errData.error || "(žádný error message)")
            );
            btnEl.disabled = false;
            btnEl.innerHTML = originalHtml;
            return;
          }

          lastRespData = await r.json();
          savedFieldsCount += Object.keys(fieldChanges).length;
          console.info("[DesignFwForm] PATCH " + entityType + " success:", lastRespData);
        }

        // Krok 5.I-G: PATCH 2 — comp_def root (Picker #3 + future per-instance
        // settings). Optimistic lock pres form.updated_at (Krok 5.I-A2 trigger).
        const formRoot = this._spec.form || {};
        if (Object.keys(compDefChanges).length > 0) {
          if (formRoot.id == null || !formRoot.updated_at) {
            alert(
              "Save selhal: form root comp_def chybi id nebo updated_at.\\n" +
              "Backend musi vracet form.id + form.updated_at (Krok 5.I-F)."
            );
            btnEl.disabled = false;
            btnEl.innerHTML = originalHtml;
            return;
          }
          const r2 = await fetch(
            "/api/v1/erp/design/comp_def/" + encodeURIComponent(formRoot.id),
            {
              method: "PATCH",
              credentials: "include",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                field_changes: compDefChanges,
                expected_updated_at: formRoot.updated_at,
              }),
            }
          );

          if (r2.status === 409) {
            const errData = await r2.json().catch(() => ({}));
            alert(
              "Konflikt na comp_def root: někdo jiný mezitím změnil form metadata.\\n" +
              "Server čas: " + (errData.server_updated_at || "?") + "\\n" +
              "Zavři modal a otevři znovu."
            );
            btnEl.disabled = false;
            btnEl.innerHTML = originalHtml;
            return;
          }

          if (!r2.ok) {
            const errData = await r2.json().catch(() => ({}));
            alert(
              "Uložení comp_def root selhalo: HTTP " + r2.status + "\\n" +
              (errData.error || "(žádný error message)")
            );
            btnEl.disabled = false;
            btnEl.innerHTML = originalHtml;
            return;
          }

          lastRespData = await r2.json();
          savedFieldsCount += Object.keys(compDefChanges).length;
          console.info("[DesignFwForm] PATCH comp_def success:", lastRespData);
        }

        // 200 OK — toast + close
        const respData = lastRespData || {};

        // Visual feedback — green flash krátce před close
        btnEl.style.background = "#3a7a3a";
        btnEl.style.borderColor = "#4a9a4a";
        btnEl.innerHTML = "✅ Uloženo";

        // Clear dirty state (modal close handler nepokusí dirty check)
        const _changeCount = this._dirty.size;
        this._dirty.clear();
        _markFormDirty(this, false);

        // Phase 38.4 Krok 14b+9-A (13.5.2026 ~21:30): toast notification
        // misto silent close. Marti's prezentace polish.
        const _wToast = _changeCount === 1 ? "změna" : (_changeCount < 5 ? "změny" : "změn");
        _showToast(
          _changeCount > 0
            ? "Uloženo — " + _changeCount + " " + _wToast
            : "Uloženo",
          "success"
        );

        // Phase 38.4 Krok 14b+5 polish (13.5.2026 ~18:35, Marti's
        // "refresh gridu po save" request): trigger callback s response
        // data. Callback v openFwFormForRow re-renderuje aktualni grid.
        if (typeof this.opts.onSaveSuccess === "function") {
          try {
            this.opts.onSaveSuccess(respData);
          } catch (e) {
            console.error("[DesignFwForm] onSaveSuccess callback failed:", e);
          }
        }

        // Po krátké pauze close
        setTimeout(() => {
          this._shell.close();
        }, 600);
      } catch (e) {
        console.error("[DesignFwForm] save failed:", e);
        _showToast("Save selhal: " + (e.message || e), "error", 3500);
        btnEl.disabled = false;
        btnEl.innerHTML = originalHtml;
      }
    }

    // Krok 14b+8 (13.5.2026 ~21:00, Marti's "komponenty RO a ready for
    // Drag and drop"): wrap field element do draggable containeru s grip
    // handle. Volat jen v DESIGN mode + main panel.
    //
    // Drag state je per-form-instance (this._dragState). Drop computes
    // novy sort_order pole + PATCH backend /design/comp-def/reorder.
    _wrapFieldForDesign(fieldEl, field, index, total) {
      const wrap = document.createElement("div");
      wrap.className = "erp-field-design-wrap";
      wrap.draggable = true;
      wrap.dataset.fieldId = String(field.id);
      wrap.dataset.fieldIndex = String(index);
      // Phase 38.4 Krok 14c+3.1 (14.5.2026 odpoledne, Marti's polish
      // po dnešním testu):
      //   "rendruj ty mazaci krizky na pravy okrak komponenty, ne mimo ni.
      //    Tu sipku vlevo pinned rendruj hned vedle toho krizku vlevo."
      //
      // Refactor: action buttons (✕ delete, ⬅ pinned, 🎯 detect-values)
      // jsou teted absolute overlay v pravem hornim rohu content. Grid
      // template = jen grip (20px) + content (1fr) — žádné side columns.
      // Content má position:relative pro absolute child positioning.
      wrap.style.cssText =
        "display:grid;grid-template-columns:20px 1fr;gap:6px;align-items:start;" +
        "padding:4px 6px;border:1px dashed transparent;border-radius:4px;" +
        "cursor:grab;position:relative;";

      // Krok 14b+9-C (13.5.2026 ~21:35): pending flash animation —
      // pokud _pendingFlashFieldId match field.id, apply flash class +
      // clear flag. Pouziva se po reorder + delete na novou pozici.
      if (this._pendingFlashFieldId === field.id) {
        wrap.classList.add("erp-field-flash-success");
        this._pendingFlashFieldId = null;
        // Cleanup class po animation tak ze re-render neopakuje
        setTimeout(() => {
          try { wrap.classList.remove("erp-field-flash-success"); } catch (e) {}
        }, 800);
      }

      // Grip handle vlevo (drag icon)
      const grip = document.createElement("div");
      grip.className = "erp-field-design-grip";
      grip.style.cssText =
        "display:flex;align-items:center;justify-content:center;" +
        "color:#5d6975;font-size:14px;line-height:1;cursor:grab;" +
        "user-select:none;height:24px;margin-top:18px;";
      grip.textContent = "⋮⋮";  // double-vertical-dots grip
      grip.title = "Drag pro zmenu poradi pole";
      wrap.appendChild(grip);

      // Field content — position:relative pro absolute overlay buttons
      // (Krok 14c+3.1, Marti's "rendruj na pravy okrak komponenty").
      const content = document.createElement("div");
      content.style.cssText = "min-width:0;position:relative;";
      content.appendChild(fieldEl);
      wrap.appendChild(content);

      // Phase 38.4 Krok 14c+3.1 (14.5.2026 odpoledne, Marti's polish):
      // Action buttons jako absolute overlay v PRAVEM HORNIM rohu content
      // (komponenta — input/select/atd.). Order zprava doleva:
      //   ✕ delete (right:4px)        — destruktivni, nejvic vpravo
      //   ⬅ pinned (right:30px)       — vedle ✕
      //   🎯 detect-values (right:56px) — jen lookup, vedle ⬅
      //
      // Hover behavior: default opacity 0, parent .erp-field-design-wrap:hover
      // → opacity 1 (CSS rule existing). ⬅ ON state má opacity:1 !important
      // override (Marti vidí stav i bez hover).
      const alwaysNewRow = !!(field.layout && field.layout.always_new_row);
      const isLookupField = field.comp_type_code === "lookup" ||
                            field.comp_type_code === "combobox";

      // Helper pro consistent button styling
      const _mkActionBtn = (text, title, bg, border, color, right) => {
        const b = document.createElement("button");
        b.type = "button";
        b.textContent = text;
        b.title = title;
        b.style.cssText =
          "position:absolute;top:2px;right:" + right + "px;" +
          "background:" + bg + ";border:1px solid " + border + ";" +
          "color:" + color + ";padding:0;width:22px;height:22px;" +
          "border-radius:3px;cursor:pointer;font-size:11px;line-height:1;" +
          "display:flex;align-items:center;justify-content:center;" +
          "z-index:2;transition:opacity 0.15s;";
        // Defensive: button nezachycuje drag wrap (preserve drag handle UX)
        b.addEventListener("dragstart", (ev) => {
          ev.preventDefault();
          ev.stopPropagation();
        });
        return b;
      };

      // ⬅ Pinned button (always_new_row toggle)
      // Phase 38.4 Krok 14c+3.3 (14.5.2026 odpoledne, Marti's polish):
      // Hover-only pattern napříč VŠEMI action buttons — sjednoceno
      // i pro ⬅ ON state a 🎯 detect-values. Bez opacity:1 inline override.
      // State pro ⬅ ON visible přes border + bg accent (modry), Marti uvidí
      // při hover. Pro long-term state visibility: future polish field-level
      // left border accent (4px modra pinned indicator).
      const leftBtn = _mkActionBtn(
        "⬅",
        alwaysNewRow
          ? "Vždy na novém řádku — ZAP. Klikni pro vypnutí."
          : "Vždy na novém řádku — VYP. Klikni pro zapnutí.",
        alwaysNewRow ? "rgba(58,138,168,0.2)" : "transparent",
        alwaysNewRow ? "#3a8aa8" : "#2a3340",
        alwaysNewRow ? "#7ed4e8" : "#5d6975",
        30 + (isLookupField ? 26 : 0)  // pokud 🎯 visible, ⬅ se posune doleva
      );
      leftBtn.className = "erp-field-design-leftpin erp-field-design-action-hoveronly";
      leftBtn.addEventListener("click", async (ev) => {
        ev.stopPropagation();
        ev.preventDefault();
        await this._performFieldToggleAlwaysLeft(field);
      });
      content.appendChild(leftBtn);

      // 🎯 Detect values button — jen lookup/combobox, hover-only
      // (Marti's 14c+3.3 polish: sjednocený hover pattern)
      if (isLookupField) {
        const detectValsBtn = _mkActionBtn(
          "🎯",
          "Auto-detekce hodnot pro dropdown — SELECT DISTINCT z DB.",
          "rgba(58,138,168,0.2)",
          "#3a8aa8",
          "#7ed4e8",
          30  // vedle ⬅
        );
        detectValsBtn.className = "erp-field-design-detectvals erp-field-design-action-hoveronly";
        detectValsBtn.addEventListener("click", async (ev) => {
          ev.stopPropagation();
          ev.preventDefault();
          await this._detectAndSaveEnumValues(field);
        });
        content.appendChild(detectValsBtn);
      }

      // Phase 38.4 Krok 14f-M (14.5.2026 vecer, Marti's "max_length /
      // min_length parametrizace"): ⚙ Settings button v action overlay.
      // Right-most position posunut o 26px doleva (delete zustava na 4).
      const settingsBtn = _mkActionBtn(
        "⚙",
        "Nastavení komponenty — caption, max/min length, readonly, required",
        "rgba(168, 140, 212, 0.15)",
        "#7a5fa8",
        "#a88cd4",
        30 + (isLookupField ? 26 : 0) + 26  // vlevo od ⬅ (ktery je vedle 🎯)
      );
      settingsBtn.className = "erp-field-design-settings erp-field-design-action-hoveronly";
      settingsBtn.addEventListener("click", (ev) => {
        ev.stopPropagation();
        ev.preventDefault();
        this._openFieldSettings(field);
      });
      content.appendChild(settingsBtn);

      // ✕ Delete button — nejvic vpravo (destruktivni action)
      const delBtn = _mkActionBtn(
        "✕",
        "Smazat pole '" + (field.caption || field.name) + "'",
        "transparent",
        "#5a2828",
        "#e57373",
        4  // pravy okraj komponenty
      );
      delBtn.className = "erp-field-design-delete erp-field-design-action-hoveronly";
      delBtn.addEventListener("click", async (ev) => {
        ev.stopPropagation();
        ev.preventDefault();
        const decision = await _confirmDarkDialog({
          title: "Smazat pole",
          message: "Opravdu smazat pole '" + (field.caption || field.name) + "'?\n\n" +
                   "(soft-delete, struktura zachovana v audit historii)",
        });
        if (decision !== true) return;
        await this._performFieldDelete(field);
      });
      // Krok 14c+3.1: append do content (ne wrap), aby absolute positioning
      // bylo relative k komponente, ne k cele rowě.
      content.appendChild(delBtn);

      // Krok 14b+9-B (13.5.2026 ~21:35): inline rename label (dvojklik).
      // Najit label el v fieldEl + attach dblclick. Vsechny comp_type
      // pouzivaji bud .erp-input-label nebo similar label div.
      try {
        const labelEl = fieldEl.querySelector(".erp-input-label, .erp-design-section-title, label");
        if (labelEl) {
          labelEl.style.cursor = "text";
          labelEl.title = "Dvojklik pro přejmenování";
          labelEl.addEventListener("dblclick", (ev) => {
            ev.stopPropagation();
            this._startInlineRename(labelEl, field);
          });
        }
      } catch (e) {
        console.warn("[DesignFwForm] inline rename attach failed:", e);
      }

      // Phase 38.4 Krok 14f-M (14.5.2026 vecer): right-click → field settings
      wrap.addEventListener("contextmenu", (ev) => {
        const tag = ev.target && ev.target.tagName;
        // Skip pokud na child input/button — necht native context menu
        if (tag === "INPUT" || tag === "BUTTON" || tag === "TEXTAREA" || tag === "SELECT") {
          return;
        }
        ev.preventDefault();
        ev.stopPropagation();
        this._openFieldSettings(field);
      });

      // Drag events
      wrap.addEventListener("dragstart", (ev) => {
        wrap.style.opacity = "0.5";
        wrap.style.cursor = "grabbing";
        this._dragState = {
          fieldId: field.id,
          fromIndex: index,
          el: wrap,
        };
        try {
          ev.dataTransfer.effectAllowed = "move";
          ev.dataTransfer.setData("text/plain", String(field.id));
        } catch (e) {}
      });
      wrap.addEventListener("dragend", (ev) => {
        wrap.style.opacity = "";
        wrap.style.cursor = "grab";
        // Clean drop indicators
        const parent = wrap.parentElement;
        if (parent) {
          parent.querySelectorAll(".erp-field-design-wrap").forEach((el) => {
            el.style.borderTopColor = "transparent";
            el.style.borderBottomColor = "transparent";
          });
        }
        this._dragState = null;
      });
      wrap.addEventListener("dragover", (ev) => {
        if (!this._dragState) return;
        if (this._dragState.fieldId === field.id) return; // sam sebe nemuze
        ev.preventDefault();
        try { ev.dataTransfer.dropEffect = "move"; } catch (e) {}
        // Visual indicator — pred / za podle vertical mouse position
        const rect = wrap.getBoundingClientRect();
        const isAbove = (ev.clientY - rect.top) < (rect.height / 2);
        wrap.style.borderTopColor = isAbove ? "#7ed4e8" : "transparent";
        wrap.style.borderBottomColor = isAbove ? "transparent" : "#7ed4e8";
      });
      wrap.addEventListener("dragleave", (ev) => {
        wrap.style.borderTopColor = "transparent";
        wrap.style.borderBottomColor = "transparent";
      });
      wrap.addEventListener("drop", (ev) => {
        ev.preventDefault();
        // Phase 38.4 Krok 14g-A (15.5.2026 rano, Marti's "drop se
        // neuskutecni"): stopPropagation — bez nej event bubble do
        // container.drop (panel/groupbox), ktery dual-fire _performFieldMove
        // bez position. Field.drop ma authoritative position info (Y coord
        // relative k field rect), takze drop ZASTAVIT zde.
        ev.stopPropagation();
        if (!this._dragState) return;
        const fromId = this._dragState.fieldId;
        const toId = field.id;
        if (fromId === toId) return;
        const rect = wrap.getBoundingClientRect();
        const isAbove = (ev.clientY - rect.top) < (rect.height / 2);
        // _performFieldReorder detekuje cross-parent automaticky (Krok 14g-A)
        // → delegate na _performCrossParentMove. Same-parent → existing flow.
        this._performFieldReorder(fromId, toId, isAbove);
      });

      return wrap;
    }

    async _performFieldDelete(field) {
      // Krok 14b+9-D: DELETE /design/comp-def/{id} -> reload + toast.
      // Phase 38.4 Krok 14g-B (15.5.2026 rano, Marti's "404 ale stale
      // visible"): graceful 404 handling. Pokud row nenalezen (true
      // not found), reload spec stejne — UI mozno stale ho zobrazuje
      // z cache. Backend 200 was_already_deactivated → success toast +
      // reload (cleanup stale UI).
      //
      // Phase 38.4 Krok 14g-D (15.5.2026 rano): undo support — push
      // inverse PATCH is_active=true PRED delete. Po success undo
      // restoruje row.
      const undoLabel = "Smaz " + (field.comp_type_code || "comp") +
                        " '" + (field.caption || field.name) + "' (#" + field.id + ")";
      const undoInverse = async () => {
        await fetch(
          "/api/v1/erp/design/comp-def/update/" + encodeURIComponent(field.id),
          {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ is_active: true }),
          }
        );
      };

      try {
        const r = await fetch(
          "/api/v1/erp/design/comp-def/" + encodeURIComponent(field.id),
          { method: "DELETE", credentials: "include" }
        );
        if (r.status === 404) {
          // True not found — row neexistuje v DB. UI cache stale, force reload.
          console.warn("[DesignFwForm] delete 404 — force reload pro stale UI cleanup");
          _showToast(
            "Komponenta byla mezitim smazana — obnovuji formular",
            "info",
            2500
          );
          await this._reloadSpec();
          return;
        }
        if (!r.ok) {
          const errBody = await r.json().catch(() => ({}));
          throw new Error("HTTP " + r.status + ": " + (errBody.error || r.statusText));
        }
        const data = await r.json().catch(() => ({}));
        if (data.was_already_deactivated) {
          // Idempotent backend response — info toast pro UX clarity
          _showToast(
            "Komponenta uz byla drive smazana — obnovuji formular",
            "info",
            2500
          );
        } else {
          _showToast(
            "Pole '" + (field.caption || field.name) + "' smazáno",
            "success"
          );
          // Krok 14g-D: push undo only on actual delete (ne na already-deactivated)
          this._pushUndoOp(undoLabel, undoInverse);
        }
        await this._reloadSpec();
      } catch (e) {
        console.error("[DesignFwForm] delete failed:", e);
        _showToast("Smazání selhalo: " + (e.message || e), "error", 3500);
      }
    }

    async _detectAndSaveEnumValues(field) {
      // Krok 14b+13: GET distinct hodnoty z DB pro lookup field -> PATCH
      // layout.enum_values. Backend dela: walk parent chain -> core ->
      // data_entity_type -> table -> SELECT DISTINCT column.
      //
      // Krok 14b+13.1 (14.5.2026 ~01:00): diagnostic logging (Marti's
      // smoke: "Detekce probehne, ale do listboxu se to nepropise").
      console.info(
        "[DesignFwForm] _detectAndSaveEnumValues START",
        "field.id=" + field.id,
        "field.name=" + field.name,
        "field.comp_type_code=" + field.comp_type_code,
        "current field.layout=", field.layout
      );
      try {
        _showToast("Detekce hodnot pro '" + (field.caption || field.name) + "'…", "info", 1500);
        const r = await fetch(
          "/api/v1/erp/design/comp-def/" + encodeURIComponent(field.id) + "/distinct-values",
          { credentials: "include" }
        );
        if (!r.ok) {
          const errBody = await r.json().catch(() => ({}));
          throw new Error("HTTP " + r.status + ": " + (errBody.error || r.statusText));
        }
        const data = await r.json();
        console.info("[DesignFwForm] distinct-values response:", data);
        if (!data.ok) {
          throw new Error(data.error || "unknown");
        }
        if (!Array.isArray(data.values) || data.values.length === 0) {
          _showToast(
            "Žádné distinct hodnoty pro '" + field.name + "' v tabulce " + (data.table || "?"),
            "error",
            3000
          );
          return;
        }
        // PATCH layout.enum_values (preserve other layout keys)
        const newLayout = Object.assign({}, field.layout || {}, {
          enum_values: data.values,
        });
        console.info("[DesignFwForm] PATCH newLayout:", newLayout);
        const pr = await fetch(
          "/api/v1/erp/design/comp-def/update/" + encodeURIComponent(field.id),
          {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ layout: newLayout }),
          }
        );
        if (!pr.ok) {
          const errBody = await pr.json().catch(() => ({}));
          throw new Error("PATCH HTTP " + pr.status + ": " + (errBody.error || pr.statusText));
        }
        const pData = await pr.json();
        console.info("[DesignFwForm] PATCH response:", pData);
        _showToast(
          "Detekováno " + data.values.length + " hodnot pro '" + (field.caption || field.name) + "'",
          "success"
        );
        this._pendingFlashFieldId = field.id;
        await this._reloadSpec();
        // Po reload — verify spec contains enum_values
        const reloadedField = (this._spec.fields || []).find(f => f.id === field.id);
        console.info(
          "[DesignFwForm] POST-RELOAD field.layout:",
          reloadedField ? reloadedField.layout : "(field not found)"
        );
      } catch (e) {
        console.error("[DesignFwForm] detect enum values failed:", e);
        _showToast("Detekce hodnot selhala: " + (e.message || e), "error", 3500);
      }
    }

    async _performFieldToggleAlwaysLeft(field) {
      // Krok 14b+10: toggle layout.always_new_row. PATCH endpoint
      // (Krok 14b+9-B) accept partial layout JSONB — preserve other
      // layout keys (mono, readonly, etc.) pri toggle.
      const currentLayout = (field.layout && typeof field.layout === "object")
        ? field.layout
        : {};
      const wasOn = !!currentLayout.always_new_row;
      const newLayout = Object.assign({}, currentLayout, {
        always_new_row: !wasOn,
      });
      try {
        // Krok 14b+10 hotfix #2: 3-segment route /comp-def/update/{id} aby
        // nematchoval generic 2-segment /design/{entity_type}/{row_id}
        const r = await fetch(
          "/api/v1/erp/design/comp-def/update/" + encodeURIComponent(field.id),
          {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ layout: newLayout }),
          }
        );
        if (!r.ok) {
          const errBody = await r.json().catch(() => ({}));
          throw new Error("HTTP " + r.status + ": " + (errBody.error || r.statusText));
        }
        _showToast(
          !wasOn
            ? "Pole '" + (field.caption || field.name) + "' — vždy na novém řádku ZAP"
            : "Pole '" + (field.caption || field.name) + "' — vždy na novém řádku VYP",
          "success"
        );
        this._pendingFlashFieldId = field.id;
        await this._reloadSpec();
      } catch (e) {
        console.error("[DesignFwForm] toggle always-left failed:", e);
        _showToast("Přepnutí selhalo: " + (e.message || e), "error", 3500);
      }
    }

    _startInlineRename(labelEl, field) {
      // Krok 14b+9-B: replace label DIV s INPUT, focus + select.
      // Enter -> PATCH caption. Esc -> revert. Blur -> commit pokud
      // non-empty + zmena, jinak revert.
      const originalLabel = field.caption || field.name;
      const input = document.createElement("input");
      input.type = "text";
      input.value = originalLabel;
      input.style.cssText =
        "font-size:12px;color:#e8eef5;background:#0f141a;" +
        "border:1px solid #3a8aa8;border-radius:3px;padding:2px 6px;" +
        "width:100%;outline:none;";
      // Hide label DIV, insert input pred nim (zachovat label v DOM
      // pro snadny revert)
      labelEl.style.display = "none";
      labelEl.parentNode.insertBefore(input, labelEl);
      // Vyznacit cely text pro rychly retype
      setTimeout(() => {
        input.focus();
        try { input.select(); } catch (e) {}
      }, 0);

      let _committed = false;
      const commit = async (newLabel) => {
        if (_committed) return;
        _committed = true;
        const trimmed = String(newLabel || "").trim();
        // Restore label DIV bez ohledu na outcome
        try { input.parentNode.removeChild(input); } catch (e) {}
        labelEl.style.display = "";
        if (!trimmed || trimmed === originalLabel) {
          return; // revert beze zmeny
        }
        // PATCH backend (Krok 14b+10 hotfix #2: 3-segment route
        // /comp-def/update/{id} aby nematchoval generic 2-segment
        // /design/{entity_type}/{row_id})
        try {
          const r = await fetch(
            "/api/v1/erp/design/comp-def/update/" + encodeURIComponent(field.id),
            {
              method: "PATCH",
              headers: { "Content-Type": "application/json" },
              credentials: "include",
              body: JSON.stringify({ caption: trimmed }),
            }
          );
          if (!r.ok) {
            const errBody = await r.json().catch(() => ({}));
            throw new Error("HTTP " + r.status + ": " + (errBody.error || r.statusText));
          }
          _showToast("Popisek změněn: '" + trimmed + "'", "success");
          // Flash na renamed field po reload
          this._pendingFlashFieldId = field.id;
          await this._reloadSpec();
        } catch (e) {
          console.error("[DesignFwForm] rename failed:", e);
          _showToast("Přejmenování selhalo: " + (e.message || e), "error", 3500);
        }
      };
      const cancel = () => {
        if (_committed) return;
        _committed = true;
        try { input.parentNode.removeChild(input); } catch (e) {}
        labelEl.style.display = "";
      };
      input.addEventListener("keydown", (ev) => {
        if (ev.key === "Enter") {
          ev.preventDefault();
          commit(input.value);
        } else if (ev.key === "Escape") {
          ev.preventDefault();
          cancel();
        }
      });
      input.addEventListener("blur", () => {
        commit(input.value);
      });
    }

    async _reloadSpec() {
      // Krok 14b+9: shared reload helper (used by delete + rename + reorder)
      // Phase 38.4 Krok 14g Etapa F Krok 5.G (16.5.2026 vecer): null guards
      // pro drafted core (code=NULL, data=null). Fallback na /by-id endpoint
      // pokud code chybi.
      try {
        const core = this._spec && this._spec.core;
        const data = this._spec && this._spec.data;
        const rowId = (data && data.id) || this.opts.rowId || 0;

        let url;
        if (core && core.code) {
          // Fully-formed core — code-based path
          url = "/api/v1/erp/fw-form/" +
                encodeURIComponent(core.code) + "/" +
                encodeURIComponent(rowId);
        } else if (core && core.id) {
          // Drafted core (code=NULL) — fallback na by-id
          url = "/api/v1/erp/fw-form/by-id/" +
                encodeURIComponent(core.id) + "/" +
                encodeURIComponent(rowId);
        } else {
          console.warn("[DesignFwForm] _reloadSpec: no core code or id");
          return;
        }

        const r = await fetch(url, { credentials: "include" });
        if (r.ok) {
          const newSpec = await r.json();
          if (newSpec.ok) {
            this._spec = newSpec;
            this._render();
          }
        }
      } catch (e) {
        console.error("[DesignFwForm] _reloadSpec failed:", e);
      }
    }

    async _performFieldReorder(fromId, toId, dropAbove) {
      // Phase 38.4 Krok 14e-F (14.5.2026 vecer): generalized to siblings
      // (parent_comp_def_id match), ne pouze region_slot='main' fields.
      // Funguje pro:
      //   - leaf fields uvnitr groupbox (parent_comp_def_id=groupbox.id)
      //   - panels uvnitr formu (parent_comp_def_id=form.id)
      //   - groupboxes uvnitr panelu (parent_comp_def_id=panel.id)
      //
      // Phase 38.4 Krok 14g-A (15.5.2026 rano, Marti's "drop se neuskutecni"
      // diagnoza): cross-parent drag teted PODPOROVAN. Detect cross-parent
      // → delegate na _performCrossParentMove (atomic move + position).
      const fields = this._spec.fields || [];
      const fromComp = fields.find((f) => f.id === fromId);
      const toComp = fields.find((f) => f.id === toId);
      if (!fromComp || !toComp) {
        console.warn("[DesignFwForm] reorder: from/to not found", fromId, toId);
        return;
      }
      if (fromId === toId) return;
      const parentId = fromComp.parent_comp_def_id;
      if (toComp.parent_comp_def_id !== parentId) {
        // Cross-parent: move + position v target parent
        return this._performCrossParentMove(fromId, toComp, dropAbove);
      }
      // Sibling filter — vsech comp_def se stejnym parent_comp_def_id
      const siblings = fields
        .filter((f) => f.parent_comp_def_id === parentId)
        .sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0));
      // Krok 14g-D undo: snapshot original sort_orders PRED reorder
      const originalOrders = siblings.map((f) => ({
        id: f.id,
        sort_order: f.sort_order != null ? f.sort_order : 0,
      }));
      const fromIdx = siblings.findIndex((f) => f.id === fromId);
      const toIdx = siblings.findIndex((f) => f.id === toId);
      if (fromIdx < 0 || toIdx < 0) {
        console.warn("[DesignFwForm] reorder: sibling lookup failed", fromId, toId);
        return;
      }
      // Reorder
      const [moved] = siblings.splice(fromIdx, 1);
      // Po splice se toIdx mohl posunout (pokud fromIdx < toIdx)
      let insertAt = siblings.findIndex((f) => f.id === toId);
      if (insertAt < 0) insertAt = siblings.length;
      if (!dropAbove) insertAt += 1;
      siblings.splice(insertAt, 0, moved);
      // Assign new sort_order — multiples of 10 pro budouci insert space
      const payload = siblings.map((f, i) => ({
        id: f.id,
        sort_order: (i + 1) * 10,
      }));
      try {
        const r = await fetch("/api/v1/erp/design/comp-def/reorder", {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({ field_orders: payload }),
        });
        if (!r.ok) {
          const errBody = await r.json().catch(() => ({}));
          throw new Error("HTTP " + r.status + ": " + (errBody.error || r.statusText));
        }
        console.info("[DesignFwForm] reorder OK:", payload);
        _showToast("Pořadí uloženo", "success");
        // Krok 14g-D undo: push inverse (restore originalOrders)
        this._pushUndoOp(
          "Zmena poradi v parent #" + parentId,
          async () => {
            await fetch("/api/v1/erp/design/comp-def/reorder", {
              method: "PUT",
              headers: { "Content-Type": "application/json" },
              credentials: "include",
              body: JSON.stringify({ field_orders: originalOrders }),
            });
          }
        );
        // Krok 14b+9-C: flash na moved field po reload (pendingFlashFieldId
        // se cte v _wrapFieldForDesign pri render).
        this._pendingFlashFieldId = fromId;
        // Reload spec + re-render — nova order se projevi
        await this._reloadSpec();
      } catch (e) {
        console.error("[DesignFwForm] reorder failed:", e);
        _showToast("Pořadí selhalo: " + (e.message || e), "error", 3500);
      }
    }

    // ════════════════════════════════════════════════════════════════
    // Phase 38.4 Krok 14e-C (14.5.2026 vecer): Recursive component tree
    // rendering. Backend (Krok 14e-B) vraci flat list ALL descendants of
    // form root pres recursive CTE. _render postavi byParent map
    // (Map<parent_comp_def_id, [children]>) v this.__renderCtx.
    //
    // _renderComponentTree(comp, idx, total) → DOM node | null
    //   Dispatch podle comp_type_code:
    //     - panel/groupbox → _renderContainerNode (wrapper + recurse)
    //     - else → _renderLeafField (legacy single field render)
    // ════════════════════════════════════════════════════════════════
    _renderComponentTree(comp, idx, total) {
      const code = comp.comp_type_code;
      // Container types (Marti's 19yr Delphi compat + new modern UI):
      //   panel    = invisible structural section
      //   groupbox = visual border-top + optional label
      // Future containers (tab_pageless, accordion, etc) lze pridat sem.
      const CONTAINER_CODES = new Set(["panel", "groupbox"]);
      if (CONTAINER_CODES.has(code)) {
        return this._renderContainerNode(comp);
      }
      // Leaf field — existing behavior
      return this._renderLeafField(comp, idx, total);
    }

    // ════════════════════════════════════════════════════════════════
    // Phase 38.4 Krok 14f-D (14.5.2026 vecer, Marti's "moznost zakladni
    // parametrizace techto panelu"): right-click → settings popup.
    //
    // Editable fields:
    //   - caption (label panelu, empty = invisible)
    //   - layout.align (left/right/top/bottom/client/none dropdown)
    //   - layout.width (pixels | 'auto' — pro left/right)
    //   - layout.height (pixels | 'auto' — pro top/bottom)
    //   - layout.min_width (pixels — responsive constraint)
    //   - layout.min_height (pixels)
    //   - layout.border_mode (none/top/all — relevantni pro groupbox)
    //
    // PATCH /api/v1/erp/design/comp-def/update/{id} s caption + layout
    // (merge s existing keys). After save → _reloadSpec + re-render.
    // ════════════════════════════════════════════════════════════════
    _openContainerSettings(container) {
      const isPanel = container.comp_type_code === "panel";
      const isGroupbox = container.comp_type_code === "groupbox";
      const typeLabel = isPanel ? "Panel" : (isGroupbox ? "Groupbox" : "Container");
      const currentLayout = container.layout || {};

      // Build modal overlay (analog _confirmDarkDialog ale s form)
      const overlay = document.createElement("div");
      overlay.style.cssText =
        "position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:10001;" +
        "display:flex;align-items:center;justify-content:center;";

      const modal = document.createElement("div");
      modal.style.cssText =
        "background:#141a20;border:1px solid #2a3340;border-radius:6px;" +
        "min-width:420px;max-width:520px;color:#e8eef5;font-size:13px;" +
        "box-shadow:0 8px 32px rgba(0,0,0,0.6);overflow:hidden;";

      // Header
      const header = document.createElement("div");
      header.style.cssText =
        "padding:12px 16px;background:#1a2028;border-bottom:1px solid #2a3340;" +
        "display:flex;align-items:center;justify-content:space-between;";
      const title = document.createElement("div");
      title.style.cssText = "font-weight:600;font-size:14px;";
      title.innerHTML = (isPanel ? "📦" : "▦") + " Nastavení: " + typeLabel +
                        " <span style=\"color:#5d6975;font-weight:400;font-size:11px;\">#" + container.id + "</span>";
      header.appendChild(title);
      const closeBtn = document.createElement("button");
      closeBtn.type = "button";
      closeBtn.textContent = "✕";
      closeBtn.style.cssText =
        "background:transparent;border:none;color:#8a96a4;font-size:18px;" +
        "cursor:pointer;padding:0;line-height:1;";
      closeBtn.addEventListener("click", () => document.body.removeChild(overlay));
      header.appendChild(closeBtn);
      modal.appendChild(header);

      // Form body
      const body = document.createElement("div");
      body.style.cssText = "padding:16px;display:flex;flex-direction:column;gap:10px;";

      // Helper: build labeled input row
      const _row = (labelText, inputEl) => {
        const wrap = document.createElement("div");
        wrap.style.cssText = "display:grid;grid-template-columns:130px 1fr;gap:10px;align-items:center;";
        const lbl = document.createElement("label");
        lbl.textContent = labelText;
        lbl.style.cssText = "color:#a8b4c2;font-size:12px;";
        wrap.appendChild(lbl);
        wrap.appendChild(inputEl);
        return wrap;
      };
      const _inputStyle =
        "padding:6px 10px;background:#0f141a;border:1px solid #2a3340;" +
        "color:#e8eef5;border-radius:3px;font-size:13px;width:100%;" +
        "box-sizing:border-box;";

      // caption
      const captionInput = document.createElement("input");
      captionInput.type = "text";
      captionInput.style.cssText = _inputStyle;
      captionInput.value = container.caption || "";
      captionInput.placeholder = "(empty = invisible label)";
      body.appendChild(_row("Caption", captionInput));

      // layout.align (jen pro panel — groupbox je vždy uvnitř panelu)
      let alignSelect = null;
      if (isPanel) {
        alignSelect = document.createElement("select");
        alignSelect.style.cssText = _inputStyle;
        const aligns = [
          ["client", "alClient — fill remaining (default)"],
          ["top", "alTop — full width strip nahore"],
          ["bottom", "alBottom — full width strip dole"],
          ["left", "alLeft — vertical strip vlevo"],
          ["right", "alRight — vertical strip vpravo"],
          ["none", "alNone — absolute (top/left/width/height)"],
        ];
        for (const [val, label] of aligns) {
          const opt = document.createElement("option");
          opt.value = val;
          opt.textContent = label;
          if ((currentLayout.align || "client") === val) opt.selected = true;
          alignSelect.appendChild(opt);
        }
        body.appendChild(_row("Align", alignSelect));
      }

      // layout.width (pro left/right panely)
      const widthInput = document.createElement("input");
      widthInput.type = "text";
      widthInput.style.cssText = _inputStyle;
      widthInput.value = currentLayout.width != null ? String(currentLayout.width) : "";
      widthInput.placeholder = "px (např. 200) | '30%' | 'auto'";
      body.appendChild(_row("Width", widthInput));

      // layout.height (pro top/bottom panely)
      const heightInput = document.createElement("input");
      heightInput.type = "text";
      heightInput.style.cssText = _inputStyle;
      heightInput.value = currentLayout.height != null ? String(currentLayout.height) : "";
      heightInput.placeholder = "px (např. 60) | 'auto'";
      body.appendChild(_row("Height", heightInput));

      // layout.min_width
      const minWidthInput = document.createElement("input");
      minWidthInput.type = "number";
      minWidthInput.style.cssText = _inputStyle;
      minWidthInput.value = currentLayout.min_width != null ? String(currentLayout.min_width) : "";
      minWidthInput.placeholder = "px (responsive constraint)";
      body.appendChild(_row("Min width", minWidthInput));

      // layout.min_height
      const minHeightInput = document.createElement("input");
      minHeightInput.type = "number";
      minHeightInput.style.cssText = _inputStyle;
      minHeightInput.value = currentLayout.min_height != null ? String(currentLayout.min_height) : "";
      minHeightInput.placeholder = "px";
      body.appendChild(_row("Min height", minHeightInput));

      // layout.border_mode (relevant pro groupbox primarne)
      const borderSelect = document.createElement("select");
      borderSelect.style.cssText = _inputStyle;
      const borderModes = [
        ["none", "Žádný (default pro panel)"],
        ["top", "Top — linka nahore (modern groupbox)"],
        ["all", "All — full rámeček (Delphi compat)"],
      ];
      const currentBorder = currentLayout.border_mode || (isGroupbox ? "top" : "none");
      for (const [val, label] of borderModes) {
        const opt = document.createElement("option");
        opt.value = val;
        opt.textContent = label;
        if (currentBorder === val) opt.selected = true;
        borderSelect.appendChild(opt);
      }
      body.appendChild(_row("Border mode", borderSelect));

      modal.appendChild(body);

      // Footer
      const footer = document.createElement("div");
      footer.style.cssText =
        "padding:12px 16px;background:#1a2028;border-top:1px solid #2a3340;" +
        "display:flex;align-items:center;gap:8px;";

      // Phase 38.4 Krok 14f-H (14.5.2026 vecer, Marti's "tlacitko odebrat
      // aby sel panel odebrat z formu"): Delete button vlevo (destructive
      // action separated). Confirm dialog s warning pokud panel ma child
      // comp_defs (groupbox + fields).
      const deleteBtn = document.createElement("button");
      deleteBtn.type = "button";
      deleteBtn.innerHTML = '<span style="color:#e57373;font-weight:700;margin-right:6px;">✕</span>Odebrat';
      deleteBtn.style.cssText =
        "padding:6px 16px;background:transparent;border:1px solid #5a2828;" +
        "border-radius:3px;color:#e57373;cursor:pointer;font-size:13px;" +
        "margin-right:auto;";  // push to left
      deleteBtn.title = "Smazat tento " + typeLabel.toLowerCase() + " z formuláře";
      deleteBtn.addEventListener("mouseenter", () => {
        deleteBtn.style.background = "#1f1010";
        deleteBtn.style.borderColor = "#7a3838";
      });
      deleteBtn.addEventListener("mouseleave", () => {
        deleteBtn.style.background = "transparent";
        deleteBtn.style.borderColor = "#5a2828";
      });
      deleteBtn.addEventListener("click", async () => {
        // Detect children — warning pokud nejsou empty
        const ctx = this.__renderCtx || {};
        const byParent = ctx.byParent || new Map();
        const childCount = (byParent.get(container.id) || []).length;
        const childWarn = childCount > 0
          ? "\n\n⚠ Tento " + typeLabel.toLowerCase() + " obsahuje " + childCount +
            " vnitřních komponent (groupbox/fields). Ty zůstanou v DB, ale ztratí parent — doporučení: nejdřív přesun nebo smaž jejich obsah."
          : "";
        const decision = await _confirmDarkDialog({
          title: "Smazat " + typeLabel.toLowerCase(),
          message: "Opravdu smazat " + typeLabel.toLowerCase() + " '" +
                   (container.caption || container.name) + "' (#" + container.id + ")?" +
                   childWarn + "\n\n(soft-delete — záznam v audit historii zustava)",
        });
        if (decision !== true) return;
        // DELETE /design/comp-def/{id}
        try {
          const r = await fetch(
            "/api/v1/erp/design/comp-def/" + encodeURIComponent(container.id),
            { method: "DELETE", credentials: "include" }
          );
          if (!r.ok) {
            const errBody = await r.json().catch(() => ({}));
            throw new Error("HTTP " + r.status + ": " + (errBody.error || r.statusText));
          }
          _showToast(typeLabel + " '" + (container.caption || container.name) + "' smazán", "success", 2200);
          document.body.removeChild(overlay);
          await this._reloadSpec();
        } catch (e) {
          console.error("[DesignFwForm] container delete failed:", e);
          _showToast("Mazání selhalo: " + (e.message || e), "error", 3500);
        }
      });
      footer.appendChild(deleteBtn);

      const cancelBtn = document.createElement("button");
      cancelBtn.type = "button";
      cancelBtn.textContent = "Storno";
      cancelBtn.style.cssText =
        "padding:6px 16px;background:#2a3340;border:1px solid #3a4754;" +
        "border-radius:3px;color:#cfd6df;cursor:pointer;font-size:13px;";
      cancelBtn.addEventListener("click", () => document.body.removeChild(overlay));
      footer.appendChild(cancelBtn);

      const saveBtn = document.createElement("button");
      saveBtn.type = "button";
      saveBtn.innerHTML = '<span style="color:#5dbf5d;font-weight:700;margin-right:6px;">✓</span>Uložit';
      saveBtn.style.cssText =
        "padding:6px 16px;background:#3a5a8a;border:1px solid #4a7ba8;" +
        "border-radius:3px;color:#e8eef5;cursor:pointer;font-size:13px;font-weight:600;";
      saveBtn.addEventListener("click", async () => {
        saveBtn.disabled = true;
        saveBtn.style.opacity = "0.6";
        try {
          // Build new layout (merge with existing)
          const newLayout = Object.assign({}, currentLayout);
          if (alignSelect) newLayout.align = alignSelect.value;

          // Parse width/height — pokud cislo, ulozit jako int; pokud string s '%' nebo 'auto', ulozit string
          const _parseSize = (v) => {
            const s = String(v || "").trim();
            if (s === "") return null;
            if (s === "auto") return "auto";
            if (/%$/.test(s)) return s;
            const n = parseInt(s, 10);
            return isNaN(n) ? null : n;
          };
          const newWidth = _parseSize(widthInput.value);
          const newHeight = _parseSize(heightInput.value);
          if (newWidth == null) delete newLayout.width; else newLayout.width = newWidth;
          if (newHeight == null) delete newLayout.height; else newLayout.height = newHeight;

          const newMinW = minWidthInput.value.trim() ? parseInt(minWidthInput.value, 10) : null;
          const newMinH = minHeightInput.value.trim() ? parseInt(minHeightInput.value, 10) : null;
          if (newMinW == null || isNaN(newMinW)) delete newLayout.min_width; else newLayout.min_width = newMinW;
          if (newMinH == null || isNaN(newMinH)) delete newLayout.min_height; else newLayout.min_height = newMinH;

          newLayout.border_mode = borderSelect.value;

          const newCaption = captionInput.value.trim();

          // PATCH /design/comp-def/update/{id}
          const pr = await fetch(
            "/api/v1/erp/design/comp-def/update/" + encodeURIComponent(container.id),
            {
              method: "PATCH",
              headers: { "Content-Type": "application/json" },
              credentials: "include",
              body: JSON.stringify({
                caption: newCaption,
                layout: newLayout,
              }),
            }
          );
          if (!pr.ok) {
            const errBody = await pr.json().catch(() => ({}));
            throw new Error("HTTP " + pr.status + ": " + (errBody.error || pr.statusText));
          }
          _showToast(typeLabel + " nastaveni ulozeno", "success", 2000);
          document.body.removeChild(overlay);
          await this._reloadSpec();
        } catch (e) {
          console.error("[DesignFwForm] _openContainerSettings save failed:", e);
          _showToast("Ulozeni selhalo: " + (e.message || e), "error", 3500);
          saveBtn.disabled = false;
          saveBtn.style.opacity = "1";
        }
      });
      footer.appendChild(saveBtn);
      modal.appendChild(footer);

      overlay.appendChild(modal);
      document.body.appendChild(overlay);

      // Esc to close
      const escHandler = (ev) => {
        if (ev.key === "Escape") {
          ev.stopPropagation();
          document.body.removeChild(overlay);
          document.removeEventListener("keydown", escHandler, true);
        }
      };
      document.addEventListener("keydown", escHandler, true);

      // Focus first input
      setTimeout(() => captionInput.focus(), 50);
    }

    // ════════════════════════════════════════════════════════════════
    // Phase 38.4 Krok 14f-M (14.5.2026 vecer, Marti's "U tech komponent
    // potrebujeme editovat nejlepe dva parametry... Maximal lenght a
    // Minimal lenght"): per-field settings modal.
    //
    // Editable fields (uloziste = comp_def.caption + comp_def.layout JSONB):
    //   - caption (input text)
    //   - layout.max_length (input number, optional)
    //   - layout.min_length (input number, optional)
    //   - layout.readonly (checkbox)
    //   - layout.required (checkbox)
    //   - layout.placeholder (input text)
    //
    // PATCH /api/v1/erp/design/comp-def/update/{id} s caption + layout
    // (merge with existing). After save → _reloadSpec + re-render.
    // Re-render automaticky pouzije nove layout.max_length pres _renderField.
    // ════════════════════════════════════════════════════════════════
    _openFieldSettings(field) {
      const currentLayout = field.layout || {};

      const overlay = document.createElement("div");
      overlay.style.cssText =
        "position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:10001;" +
        "display:flex;align-items:center;justify-content:center;";

      const modal = document.createElement("div");
      modal.style.cssText =
        "background:#141a20;border:1px solid #2a3340;border-radius:6px;" +
        "min-width:440px;max-width:540px;color:#e8eef5;font-size:13px;" +
        "box-shadow:0 8px 32px rgba(0,0,0,0.6);overflow:hidden;";

      // Header
      const header = document.createElement("div");
      header.style.cssText =
        "padding:12px 16px;background:#1a2028;border-bottom:1px solid #2a3340;" +
        "display:flex;align-items:center;justify-content:space-between;";
      const title = document.createElement("div");
      title.style.cssText = "font-weight:600;font-size:14px;";
      title.innerHTML = "⚙ Nastavení komponenty <span style=\"color:#7ed4e8;font-size:11px;font-weight:400;\">" +
                        (field.comp_type_code || "field") + " · #" + field.id + "</span>";
      header.appendChild(title);
      const closeBtn = document.createElement("button");
      closeBtn.type = "button";
      closeBtn.textContent = "✕";
      closeBtn.style.cssText =
        "background:transparent;border:none;color:#8a96a4;font-size:18px;" +
        "cursor:pointer;padding:0;line-height:1;";
      closeBtn.addEventListener("click", () => document.body.removeChild(overlay));
      header.appendChild(closeBtn);
      modal.appendChild(header);

      // Body
      const body = document.createElement("div");
      body.style.cssText = "padding:16px;display:flex;flex-direction:column;gap:10px;";

      const _row = (labelText, inputEl) => {
        const wrap = document.createElement("div");
        wrap.style.cssText = "display:grid;grid-template-columns:130px 1fr;gap:10px;align-items:center;";
        const lbl = document.createElement("label");
        lbl.textContent = labelText;
        lbl.style.cssText = "color:#a8b4c2;font-size:12px;";
        wrap.appendChild(lbl);
        wrap.appendChild(inputEl);
        return wrap;
      };
      const _inputStyle =
        "padding:6px 10px;background:#0f141a;border:1px solid #2a3340;" +
        "color:#e8eef5;border-radius:3px;font-size:13px;width:100%;" +
        "box-sizing:border-box;";

      // Info: DB column name (read-only display)
      const infoDb = document.createElement("div");
      infoDb.style.cssText =
        "padding:8px 10px;background:#0f141a;border:1px dashed #2a3340;" +
        "border-radius:3px;color:#7a8696;font-size:11px;line-height:1.5;";
      infoDb.innerHTML = "🔗 DB sloupec: <code style=\"color:#7ed4e8;\">" + field.name +
                         "</code>" + (field.region_slot ? " · panel: <code style=\"color:#a8b4c2;\">" + field.region_slot + "</code>" : "");
      body.appendChild(infoDb);

      // Caption
      const captionInput = document.createElement("input");
      captionInput.type = "text";
      captionInput.style.cssText = _inputStyle;
      captionInput.value = field.caption || "";
      captionInput.placeholder = field.name;
      body.appendChild(_row("Caption (label)", captionInput));

      // Placeholder
      const placeholderInput = document.createElement("input");
      placeholderInput.type = "text";
      placeholderInput.style.cssText = _inputStyle;
      placeholderInput.value = currentLayout.placeholder || "";
      placeholderInput.placeholder = "např. '—' nebo 'Zadej hodnotu...'";
      body.appendChild(_row("Placeholder", placeholderInput));

      // Phase 38.4 Krok 14f-N (14.5.2026 vecer, Marti's correction):
      // šířka komponenty na displeji — Min width / Max width (px).
      // Aplikuje se na field wrap div jako inline CSS min/max-width.
      // Marti's use case: "3 komponenty vedle sebe" pres min_width
      // nizsi (default ~280px) + max_width upper cap.
      const minWidthInput = document.createElement("input");
      minWidthInput.type = "number";
      minWidthInput.min = "0";
      minWidthInput.style.cssText = _inputStyle;
      minWidthInput.value = currentLayout.min_width != null ? String(currentLayout.min_width) : "";
      minWidthInput.placeholder = "px (např. 150 — minimum sirka pred reflow)";
      body.appendChild(_row("Min width", minWidthInput));

      const maxWidthInput = document.createElement("input");
      maxWidthInput.type = "number";
      maxWidthInput.min = "0";
      maxWidthInput.style.cssText = _inputStyle;
      maxWidthInput.value = currentLayout.max_width != null ? String(currentLayout.max_width) : "";
      maxWidthInput.placeholder = "px (např. 300 — empty = bez limitu)";
      body.appendChild(_row("Max width", maxWidthInput));

      // Phase 38.4 Krok 14f-M (text length validation, advanced):
      // Max/Min length textu (HTML5 maxlength/minlength). Optional.
      const maxLenInput = document.createElement("input");
      maxLenInput.type = "number";
      maxLenInput.min = "0";
      maxLenInput.style.cssText = _inputStyle;
      maxLenInput.value = currentLayout.max_length != null ? String(currentLayout.max_length) : "";
      maxLenInput.placeholder = "max počet znaků (HTML5 maxlength, empty = bez limitu)";
      body.appendChild(_row("Max length (text)", maxLenInput));

      const minLenInput = document.createElement("input");
      minLenInput.type = "number";
      minLenInput.min = "0";
      minLenInput.style.cssText = _inputStyle;
      minLenInput.value = currentLayout.min_length != null ? String(currentLayout.min_length) : "";
      minLenInput.placeholder = "min počet znaků (validace pri submit, empty = bez minima)";
      body.appendChild(_row("Min length (text)", minLenInput));

      // Readonly checkbox
      const roCheckWrap = document.createElement("div");
      roCheckWrap.style.cssText = "display:grid;grid-template-columns:130px 1fr;gap:10px;align-items:center;";
      const roLbl = document.createElement("label");
      roLbl.textContent = "Read-only";
      roLbl.style.cssText = "color:#a8b4c2;font-size:12px;";
      roCheckWrap.appendChild(roLbl);
      const roCheck = document.createElement("input");
      roCheck.type = "checkbox";
      roCheck.checked = !!currentLayout.readonly;
      roCheck.style.cssText = "width:18px;height:18px;cursor:pointer;justify-self:start;";
      roCheckWrap.appendChild(roCheck);
      body.appendChild(roCheckWrap);

      // Required checkbox
      const reqCheckWrap = document.createElement("div");
      reqCheckWrap.style.cssText = "display:grid;grid-template-columns:130px 1fr;gap:10px;align-items:center;";
      const reqLbl = document.createElement("label");
      reqLbl.textContent = "Required";
      reqLbl.style.cssText = "color:#a8b4c2;font-size:12px;";
      reqCheckWrap.appendChild(reqLbl);
      const reqCheck = document.createElement("input");
      reqCheck.type = "checkbox";
      reqCheck.checked = !!currentLayout.required;
      reqCheck.style.cssText = "width:18px;height:18px;cursor:pointer;justify-self:start;";
      reqCheckWrap.appendChild(reqCheck);
      body.appendChild(reqCheckWrap);

      modal.appendChild(body);

      // Footer
      const footer = document.createElement("div");
      footer.style.cssText =
        "padding:12px 16px;background:#1a2028;border-top:1px solid #2a3340;" +
        "display:flex;align-items:center;gap:8px;";

      // Delete button (left, red)
      const deleteBtn = document.createElement("button");
      deleteBtn.type = "button";
      deleteBtn.innerHTML = '<span style="color:#e57373;font-weight:700;margin-right:6px;">✕</span>Odebrat';
      deleteBtn.style.cssText =
        "padding:6px 16px;background:transparent;border:1px solid #5a2828;" +
        "border-radius:3px;color:#e57373;cursor:pointer;font-size:13px;margin-right:auto;";
      deleteBtn.title = "Smazat tuto komponentu z formuláře";
      deleteBtn.addEventListener("mouseenter", () => {
        deleteBtn.style.background = "#1f1010";
        deleteBtn.style.borderColor = "#7a3838";
      });
      deleteBtn.addEventListener("mouseleave", () => {
        deleteBtn.style.background = "transparent";
        deleteBtn.style.borderColor = "#5a2828";
      });
      deleteBtn.addEventListener("click", async () => {
        const decision = await _confirmDarkDialog({
          title: "Smazat komponentu",
          message: "Opravdu smazat pole '" + (field.caption || field.name) + "'?\n\n(soft-delete — záznam v audit historii zustava)",
        });
        if (decision !== true) return;
        try { document.body.removeChild(overlay); } catch (e) {}
        await this._performFieldDelete(field);
      });
      footer.appendChild(deleteBtn);

      const cancelBtn = document.createElement("button");
      cancelBtn.type = "button";
      cancelBtn.textContent = "Storno";
      cancelBtn.style.cssText =
        "padding:6px 16px;background:#2a3340;border:1px solid #3a4754;" +
        "border-radius:3px;color:#cfd6df;cursor:pointer;font-size:13px;";
      cancelBtn.addEventListener("click", () => document.body.removeChild(overlay));
      footer.appendChild(cancelBtn);

      const saveBtn = document.createElement("button");
      saveBtn.type = "button";
      saveBtn.innerHTML = '<span style="color:#5dbf5d;font-weight:700;margin-right:6px;">✓</span>Uložit';
      saveBtn.style.cssText =
        "padding:6px 16px;background:#3a5a8a;border:1px solid #4a7ba8;" +
        "border-radius:3px;color:#e8eef5;cursor:pointer;font-size:13px;font-weight:600;";
      saveBtn.addEventListener("click", async () => {
        saveBtn.disabled = true;
        saveBtn.style.opacity = "0.6";
        try {
          // Build new layout (merge with existing — preserve other keys)
          const newLayout = Object.assign({}, currentLayout);

          // Phase 38.4 Krok 14f-N: Min/Max width (px) — display layout
          const newMinW = minWidthInput.value.trim() ? parseInt(minWidthInput.value, 10) : null;
          const newMaxW = maxWidthInput.value.trim() ? parseInt(maxWidthInput.value, 10) : null;
          if (newMinW == null || isNaN(newMinW) || newMinW <= 0) delete newLayout.min_width;
          else newLayout.min_width = newMinW;
          if (newMaxW == null || isNaN(newMaxW) || newMaxW <= 0) delete newLayout.max_width;
          else newLayout.max_width = newMaxW;
          if (newLayout.min_width != null && newLayout.max_width != null &&
              newLayout.min_width > newLayout.max_width) {
            _showToast("Min width nesmí být větší než max width", "error", 3000);
            saveBtn.disabled = false;
            saveBtn.style.opacity = "1";
            return;
          }

          // Max/Min length — text content (HTML5 maxlength/minlength)
          const newMaxLen = maxLenInput.value.trim() ? parseInt(maxLenInput.value, 10) : null;
          const newMinLen = minLenInput.value.trim() ? parseInt(minLenInput.value, 10) : null;
          if (newMaxLen == null || isNaN(newMaxLen) || newMaxLen <= 0) delete newLayout.max_length;
          else newLayout.max_length = newMaxLen;
          if (newMinLen == null || isNaN(newMinLen) || newMinLen < 0) delete newLayout.min_length;
          else newLayout.min_length = newMinLen;
          if (newLayout.min_length != null && newLayout.max_length != null &&
              newLayout.min_length > newLayout.max_length) {
            _showToast("Min length nesmí být větší než max length", "error", 3000);
            saveBtn.disabled = false;
            saveBtn.style.opacity = "1";
            return;
          }

          // Placeholder
          const newPh = placeholderInput.value.trim();
          if (newPh) newLayout.placeholder = newPh;
          else delete newLayout.placeholder;

          // Readonly + required boolean flags
          if (roCheck.checked) newLayout.readonly = true;
          else delete newLayout.readonly;
          if (reqCheck.checked) newLayout.required = true;
          else delete newLayout.required;

          const newCaption = captionInput.value.trim();

          const pr = await fetch(
            "/api/v1/erp/design/comp-def/update/" + encodeURIComponent(field.id),
            {
              method: "PATCH",
              headers: { "Content-Type": "application/json" },
              credentials: "include",
              body: JSON.stringify({
                caption: newCaption,
                layout: newLayout,
              }),
            }
          );
          if (!pr.ok) {
            const errBody = await pr.json().catch(() => ({}));
            throw new Error("HTTP " + pr.status + ": " + (errBody.error || pr.statusText));
          }
          _showToast("Nastavení uloženo", "success", 2000);
          document.body.removeChild(overlay);
          this._pendingFlashFieldId = field.id;
          await this._reloadSpec();
        } catch (e) {
          console.error("[DesignFwForm] _openFieldSettings save failed:", e);
          _showToast("Uložení selhalo: " + (e.message || e), "error", 3500);
          saveBtn.disabled = false;
          saveBtn.style.opacity = "1";
        }
      });
      footer.appendChild(saveBtn);
      modal.appendChild(footer);

      overlay.appendChild(modal);
      document.body.appendChild(overlay);

      const escHandler = (ev) => {
        if (ev.key === "Escape") {
          ev.stopPropagation();
          try { document.body.removeChild(overlay); } catch (e) {}
          document.removeEventListener("keydown", escHandler, true);
        }
      };
      document.addEventListener("keydown", escHandler, true);

      setTimeout(() => captionInput.focus(), 50);
    }

    // ════════════════════════════════════════════════════════════════
    // Phase 38.4 Krok 14f-L (14.5.2026 vecer, Marti's "tam mame jeste
    // nedodelanou parametrizaci ke kteremu DB fieldu to patri"):
    // Mini column picker dialog pri drag z palette pro data-bound fields.
    //
    // Trigger: drag-drop z gallery pro non-container, non-label-only types.
    // Modal: dropdown s available columns (entity-columns API) + "Bez DB
    // vazby" option pro pure-visual fields. OK → POST s name=column.name,
    // caption=column.caption_default. Cancel → no INSERT.
    //
    // Returns Promise<{name, caption} | null> — null pri cancel.
    // ════════════════════════════════════════════════════════════════
    async _pickColumnForNewField(payload, parentId) {
      return new Promise(async (resolve) => {
        // 1. Fetch entity-columns pres backend (same source jako FieldPickerModal)
        const entityType = this._spec && this._spec.core && this._spec.core.data_entity_type;
        if (!entityType) {
          _showToast("Form nema data_entity_type — nelze ziskat columns", "error", 3000);
          resolve(null);
          return;
        }

        let columns = [];
        try {
          const formId = this._spec && this._spec.form && this._spec.form.id;
          const url = "/api/v1/erp/design/entity-columns/" + encodeURIComponent(entityType) +
                      (formId ? "?parent_comp_def_id=" + encodeURIComponent(formId) : "");
          const r = await fetch(url, { credentials: "include" });
          if (!r.ok) throw new Error("HTTP " + r.status);
          const d = await r.json();
          if (!d.ok) throw new Error(d.error || "unknown");
          columns = d.columns || [];
        } catch (e) {
          _showToast("Nepodarilo se nacist sloupce: " + (e.message || e), "error", 3500);
          resolve(null);
          return;
        }

        // Filter: nejdrive available (existing_comp_def_id == null) — Marti
        // zridka chce duplikovat existujici field. Show all as info (used).
        const availableCols = columns.filter(c => c.existing_comp_def_id == null);
        const usedCols = columns.filter(c => c.existing_comp_def_id != null);

        // 2. Build modal
        const overlay = document.createElement("div");
        overlay.style.cssText =
          "position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:10002;" +
          "display:flex;align-items:center;justify-content:center;";

        const modal = document.createElement("div");
        modal.style.cssText =
          "background:#141a20;border:1px solid #2a3340;border-radius:6px;" +
          "min-width:460px;max-width:560px;color:#e8eef5;font-size:13px;" +
          "box-shadow:0 8px 32px rgba(0,0,0,0.6);overflow:hidden;";

        // Header
        const header = document.createElement("div");
        header.style.cssText =
          "padding:12px 16px;background:#1a2028;border-bottom:1px solid #2a3340;" +
          "display:flex;align-items:center;justify-content:space-between;";
        const title = document.createElement("div");
        title.style.cssText = "font-weight:600;font-size:14px;";
        title.innerHTML = "🔗 DB vazba pro " + payload.label +
                          " <span style=\"color:#7ed4e8;font-size:11px;font-weight:400;\">(" + payload.code + ")</span>";
        header.appendChild(title);
        const closeBtn = document.createElement("button");
        closeBtn.type = "button";
        closeBtn.textContent = "✕";
        closeBtn.style.cssText =
          "background:transparent;border:none;color:#8a96a4;font-size:18px;" +
          "cursor:pointer;padding:0;line-height:1;";
        const _close = (result) => {
          try { document.body.removeChild(overlay); } catch (e) {}
          document.removeEventListener("keydown", escHandler, true);
          resolve(result);
        };
        closeBtn.addEventListener("click", () => _close(null));
        header.appendChild(closeBtn);
        modal.appendChild(header);

        // Body
        const body = document.createElement("div");
        body.style.cssText = "padding:16px;display:flex;flex-direction:column;gap:10px;";

        const intro = document.createElement("div");
        intro.style.cssText = "color:#a8b4c2;font-size:12px;line-height:1.5;";
        intro.innerHTML =
          "Vyber DB sloupec, který tato komponenta reprezentuje. " +
          "Nebo zvol <b>Bez DB vazby</b> pro pure-visual element (label, decorativní).";
        body.appendChild(intro);

        // Column dropdown
        const colWrap = document.createElement("div");
        colWrap.style.cssText = "display:flex;flex-direction:column;gap:6px;";
        const colLabel = document.createElement("label");
        colLabel.textContent = "DB sloupec";
        colLabel.style.cssText = "color:#a8b4c2;font-size:12px;";
        colWrap.appendChild(colLabel);

        const colSelect = document.createElement("select");
        colSelect.style.cssText =
          "padding:8px 10px;background:#0f141a;border:1px solid #2a3340;" +
          "color:#e8eef5;border-radius:3px;font-size:13px;width:100%;";

        // Available group
        if (availableCols.length > 0) {
          const og = document.createElement("optgroup");
          og.label = "📋 Volné (" + availableCols.length + ")";
          for (const c of availableCols) {
            const opt = document.createElement("option");
            opt.value = c.name;
            opt.textContent = c.caption_default + "  (" + c.name + ")";
            opt.dataset.caption = c.caption_default;
            og.appendChild(opt);
          }
          colSelect.appendChild(og);
        }
        // Used group (warning, duplicate)
        if (usedCols.length > 0) {
          const og2 = document.createElement("optgroup");
          og2.label = "⚠ Jiz pouzite na forme (" + usedCols.length + ")";
          for (const c of usedCols) {
            const opt = document.createElement("option");
            opt.value = c.name;
            opt.textContent = c.caption_default + "  (" + c.name + ")";
            opt.dataset.caption = c.caption_default;
            og2.appendChild(opt);
          }
          colSelect.appendChild(og2);
        }
        // No-binding option
        const opt0 = document.createElement("option");
        opt0.value = "__NO_BINDING__";
        opt0.textContent = "── Bez DB vazby (visual only) ──";
        colSelect.appendChild(opt0);

        // Default: prvni available, jinak no-binding
        if (availableCols.length === 0) {
          opt0.selected = true;
        }
        colWrap.appendChild(colSelect);
        body.appendChild(colWrap);

        // Caption override (optional rename)
        const capWrap = document.createElement("div");
        capWrap.style.cssText = "display:flex;flex-direction:column;gap:6px;";
        const capLabel = document.createElement("label");
        capLabel.textContent = "Caption (label v UI)";
        capLabel.style.cssText = "color:#a8b4c2;font-size:12px;";
        capWrap.appendChild(capLabel);
        const capInput = document.createElement("input");
        capInput.type = "text";
        capInput.style.cssText =
          "padding:8px 10px;background:#0f141a;border:1px solid #2a3340;" +
          "color:#e8eef5;border-radius:3px;font-size:13px;width:100%;" +
          "box-sizing:border-box;";
        // Auto-fill caption ze selected column
        const _syncCaption = () => {
          const sel = colSelect.options[colSelect.selectedIndex];
          if (sel && sel.dataset && sel.dataset.caption) {
            capInput.value = sel.dataset.caption;
          } else if (sel && sel.value === "__NO_BINDING__") {
            capInput.value = payload.label;  // fallback comp_type label
          }
        };
        _syncCaption();
        colSelect.addEventListener("change", _syncCaption);
        capWrap.appendChild(capInput);
        body.appendChild(capWrap);

        modal.appendChild(body);

        // Footer
        const footer = document.createElement("div");
        footer.style.cssText =
          "padding:12px 16px;background:#1a2028;border-top:1px solid #2a3340;" +
          "display:flex;justify-content:flex-end;gap:8px;";

        const cancelBtn = document.createElement("button");
        cancelBtn.type = "button";
        cancelBtn.textContent = "Storno";
        cancelBtn.style.cssText =
          "padding:6px 16px;background:#2a3340;border:1px solid #3a4754;" +
          "border-radius:3px;color:#cfd6df;cursor:pointer;font-size:13px;";
        cancelBtn.addEventListener("click", () => _close(null));
        footer.appendChild(cancelBtn);

        const okBtn = document.createElement("button");
        okBtn.type = "button";
        okBtn.innerHTML = '<span style="color:#5dbf5d;font-weight:700;margin-right:6px;">✓</span>Přidat';
        okBtn.style.cssText =
          "padding:6px 16px;background:#3a5a8a;border:1px solid #4a7ba8;" +
          "border-radius:3px;color:#e8eef5;cursor:pointer;font-size:13px;font-weight:600;";
        okBtn.addEventListener("click", () => {
          const selValue = colSelect.value;
          const caption = capInput.value.trim() || payload.label;
          if (selValue === "__NO_BINDING__") {
            // Visual-only — auto-name s timestamp
            const name = payload.code + "_" + Date.now().toString(36);
            _close({ name, caption, hasBinding: false });
          } else {
            _close({ name: selValue, caption, hasBinding: true });
          }
        });
        footer.appendChild(okBtn);
        modal.appendChild(footer);

        overlay.appendChild(modal);
        document.body.appendChild(overlay);

        const escHandler = (ev) => {
          if (ev.key === "Escape") {
            ev.stopPropagation();
            _close(null);
          }
        };
        document.addEventListener("keydown", escHandler, true);

        setTimeout(() => colSelect.focus(), 50);
      });
    }

    // ════════════════════════════════════════════════════════════════
    // Phase 38.4 Krok 14f-I (14.5.2026 vecer, Marti's "dodelat nastaveni
    // gridu, minimalne tlacitko odebrat zatim"): right-click na child
    // section (TELEFONY/EMAILY) → mini settings popup s Odebrat.
    //
    // Child grids (1:N joined tables) zatim NEJSOU v fw.comp_def — jsou
    // memory-only z _spec.children. "Odebrat" = hide flag v memory
    // (this._childHidden[childKey] = true). Survive _render cycles ale
    // ne sessions (re-open form ukaze vsechny grids znovu).
    //
    // Future (post-MVP): persist v DB pres user_preferences nebo
    // form_layout_overrides tabulku.
    // ════════════════════════════════════════════════════════════════
    _openChildSectionSettings(childKey, childInfo) {
      const overlay = document.createElement("div");
      overlay.style.cssText =
        "position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:10001;" +
        "display:flex;align-items:center;justify-content:center;";

      const modal = document.createElement("div");
      modal.style.cssText =
        "background:#141a20;border:1px solid #2a3340;border-radius:6px;" +
        "min-width:380px;max-width:460px;color:#e8eef5;font-size:13px;" +
        "box-shadow:0 8px 32px rgba(0,0,0,0.6);overflow:hidden;";

      // Header
      const header = document.createElement("div");
      header.style.cssText =
        "padding:12px 16px;background:#1a2028;border-bottom:1px solid #2a3340;" +
        "display:flex;align-items:center;justify-content:space-between;";
      const title = document.createElement("div");
      title.style.cssText = "font-weight:600;font-size:14px;";
      title.innerHTML = "📋 Nastavení sekce: <span style=\"color:#a8b4c2;\">" +
                        (childInfo.label || childKey) + "</span>";
      header.appendChild(title);
      const closeBtn = document.createElement("button");
      closeBtn.type = "button";
      closeBtn.textContent = "✕";
      closeBtn.style.cssText =
        "background:transparent;border:none;color:#8a96a4;font-size:18px;" +
        "cursor:pointer;padding:0;line-height:1;";
      closeBtn.addEventListener("click", () => document.body.removeChild(overlay));
      header.appendChild(closeBtn);
      modal.appendChild(header);

      // Body
      const body = document.createElement("div");
      body.style.cssText = "padding:16px;display:flex;flex-direction:column;gap:10px;";

      // Position dropdown (above/below groupbox)
      const posWrap = document.createElement("div");
      posWrap.style.cssText = "display:grid;grid-template-columns:130px 1fr;gap:10px;align-items:center;";
      const posLabel = document.createElement("label");
      posLabel.textContent = "Pozice v panelu";
      posLabel.style.cssText = "color:#a8b4c2;font-size:12px;";
      posWrap.appendChild(posLabel);
      const posSelect = document.createElement("select");
      posSelect.style.cssText =
        "padding:6px 10px;background:#0f141a;border:1px solid #2a3340;" +
        "color:#e8eef5;border-radius:3px;font-size:13px;width:100%;";
      const positions = [
        ["before-main", "Nad groupboxem (default)"],
        ["after-main", "Pod groupboxem"],
      ];
      const currentPos = (this._childPosition && this._childPosition[childKey]) || "before-main";
      for (const [val, label] of positions) {
        const opt = document.createElement("option");
        opt.value = val;
        opt.textContent = label;
        if (currentPos === val) opt.selected = true;
        posSelect.appendChild(opt);
      }
      posWrap.appendChild(posSelect);
      body.appendChild(posWrap);

      // Info text
      const info = document.createElement("div");
      info.style.cssText =
        "padding:10px;background:#0f141a;border:1px dashed #2a3340;" +
        "border-radius:3px;color:#7a8696;font-size:11px;line-height:1.5;";
      info.innerHTML =
        "📊 Tato sekce zobrazuje 1:N joined data (např. <code>user_contacts</code>). " +
        "<strong>Odebrat z formuláře</strong> skryje sekci — data v DB zůstanou. " +
        "Re-add zatím vyžaduje DB UPDATE (post-MVP polish: pridani z palety).";
      body.appendChild(info);

      modal.appendChild(body);

      // Footer
      const footer = document.createElement("div");
      footer.style.cssText =
        "padding:12px 16px;background:#1a2028;border-top:1px solid #2a3340;" +
        "display:flex;align-items:center;gap:8px;";

      // Odebrat (red, left, push others right via margin-right:auto)
      const hideBtn = document.createElement("button");
      hideBtn.type = "button";
      hideBtn.innerHTML = '<span style="color:#e57373;font-weight:700;margin-right:6px;">✕</span>Odebrat z formuláře';
      hideBtn.style.cssText =
        "padding:6px 16px;background:transparent;border:1px solid #5a2828;" +
        "border-radius:3px;color:#e57373;cursor:pointer;font-size:13px;" +
        "margin-right:auto;";
      hideBtn.title = "Skryje sekci '" + (childInfo.label || childKey) + "' z formuláře. Data v DB zůstanou.";
      hideBtn.addEventListener("mouseenter", () => {
        hideBtn.style.background = "#1f1010";
        hideBtn.style.borderColor = "#7a3838";
      });
      hideBtn.addEventListener("mouseleave", () => {
        hideBtn.style.background = "transparent";
        hideBtn.style.borderColor = "#5a2828";
      });
      hideBtn.addEventListener("click", () => {
        if (!this._childHidden) this._childHidden = {};
        this._childHidden[childKey] = true;
        _showToast("Sekce '" + (childInfo.label || childKey) + "' odebrana", "success", 2200);
        document.body.removeChild(overlay);
        this._render();
        this._attachDropTargetForGalleryDrag();
      });
      footer.appendChild(hideBtn);

      const cancelBtn = document.createElement("button");
      cancelBtn.type = "button";
      cancelBtn.textContent = "Storno";
      cancelBtn.style.cssText =
        "padding:6px 16px;background:#2a3340;border:1px solid #3a4754;" +
        "border-radius:3px;color:#cfd6df;cursor:pointer;font-size:13px;";
      cancelBtn.addEventListener("click", () => document.body.removeChild(overlay));
      footer.appendChild(cancelBtn);

      const saveBtn = document.createElement("button");
      saveBtn.type = "button";
      saveBtn.innerHTML = '<span style="color:#5dbf5d;font-weight:700;margin-right:6px;">✓</span>Uložit';
      saveBtn.style.cssText =
        "padding:6px 16px;background:#3a5a8a;border:1px solid #4a7ba8;" +
        "border-radius:3px;color:#e8eef5;cursor:pointer;font-size:13px;font-weight:600;";
      saveBtn.addEventListener("click", () => {
        if (!this._childPosition) this._childPosition = {};
        this._childPosition[childKey] = posSelect.value;
        _showToast("Pozice sekce uložena", "success", 1800);
        document.body.removeChild(overlay);
        this._render();
        this._attachDropTargetForGalleryDrag();
      });
      footer.appendChild(saveBtn);
      modal.appendChild(footer);

      overlay.appendChild(modal);
      document.body.appendChild(overlay);

      // Esc to close
      const escHandler = (ev) => {
        if (ev.key === "Escape") {
          ev.stopPropagation();
          document.body.removeChild(overlay);
          document.removeEventListener("keydown", escHandler, true);
        }
      };
      document.addEventListener("keydown", escHandler, true);
    }

    // Phase 38.4 Krok 14e-E (14.5.2026 vecer, Marti's "Panel musi byt
    // dragabled"): generic drag-and-drop pro containers (panel/groupbox).
    // Analog _wrapFieldForDesign drag events, ale na container wrap.
    // Reuse _performFieldReorder (Krok 14e-F generalized na siblings podle
    // parent_comp_def_id).
    _attachContainerDragEvents(wrap, container) {
      wrap.addEventListener("dragstart", (ev) => {
        // Defensive: pokud drag started z child input/button, neaktivuj
        // container drag (necht child mu da event)
        const isFromAction = ev.target && (
          ev.target.tagName === "INPUT" ||
          ev.target.tagName === "BUTTON" ||
          ev.target.tagName === "TEXTAREA"
        );
        if (isFromAction) return;
        wrap.style.opacity = "0.5";
        this._dragState = {
          fieldId: container.id,
          fromIndex: 0,
          el: wrap,
          isContainer: true,
        };
        try {
          ev.dataTransfer.effectAllowed = "move";
          ev.dataTransfer.setData("text/plain", String(container.id));
        } catch (e) {}
      });
      wrap.addEventListener("dragend", () => {
        wrap.style.opacity = "";
        wrap.style.outline = "";
        // Clean drop indicators na siblings
        if (wrap.parentElement) {
          wrap.parentElement.querySelectorAll(".erp-design-panel, .erp-design-groupbox")
            .forEach((el) => {
              el.style.borderTopColor = "";
              el.style.borderBottomColor = "";
            });
        }
        this._dragState = null;
      });
      wrap.addEventListener("dragover", (ev) => {
        if (!this._dragState) return;
        // Phase 38.4 Krok 14f-K (14.5.2026 vecer, Marti's "drop se
        // neuskutecni"): support cross-container drag — existing field
        // (non-isContainer) drop NA container → move (PATCH parent).
        if (this._dragState.isContainer) {
          // Container reorder (panel/groupbox swap sort_order)
          if (this._dragState.fieldId === container.id) return;
          ev.preventDefault();
          try { ev.dataTransfer.dropEffect = "move"; } catch (e) {}
          const rect = wrap.getBoundingClientRect();
          const isAbove = (ev.clientY - rect.top) < (rect.height / 2);
          wrap.style.borderTop = isAbove
            ? "2px solid #7ed4e8"
            : "1px dashed rgba(122, 134, 150, 0.3)";
          wrap.style.borderBottom = isAbove
            ? "1px dashed rgba(122, 134, 150, 0.3)"
            : "2px solid #7ed4e8";
        } else {
          // Existing field drag → highlight container as "move INTO" target
          // Skip pokud field uz JE direct child tohoto containeru (no-op move)
          ev.preventDefault();
          try { ev.dataTransfer.dropEffect = "move"; } catch (e) {}
          wrap.style.outline = "2px solid #a88cd4";
          wrap.style.outlineOffset = "-2px";
          wrap.style.background = "rgba(168, 140, 212, 0.05)";
        }
      });
      wrap.addEventListener("dragleave", () => {
        wrap.style.outline = "";
        wrap.style.background = "";
        wrap.style.borderTop = "1px dashed rgba(122, 134, 150, 0.3)";
        wrap.style.borderBottom = "1px dashed rgba(122, 134, 150, 0.3)";
      });
      wrap.addEventListener("drop", (ev) => {
        if (!this._dragState) return;
        ev.preventDefault();
        ev.stopPropagation();  // block body.drop dual-fire
        wrap.style.outline = "";
        wrap.style.background = "";
        wrap.style.borderTop = "1px dashed rgba(122, 134, 150, 0.3)";
        wrap.style.borderBottom = "1px dashed rgba(122, 134, 150, 0.3)";

        if (this._dragState.isContainer) {
          // Container reorder
          const fromId = this._dragState.fieldId;
          const toId = container.id;
          if (fromId === toId) return;
          const rect = wrap.getBoundingClientRect();
          const isAbove = (ev.clientY - rect.top) < (rect.height / 2);
          this._performFieldReorder(fromId, toId, isAbove);
        } else {
          // Phase 38.4 Krok 14f-K: existing field MOVE INTO this container
          const fromId = this._dragState.fieldId;
          // No-op pokud uz jsme direct child
          const fields = this._spec.fields || [];
          const fromComp = fields.find((f) => f.id === fromId);
          if (fromComp && fromComp.parent_comp_def_id === container.id) {
            _showToast("Komponenta uz je v tomto kontejneru", "info", 1500);
            return;
          }
          this._performFieldMove(fromId, container.id);
        }
      });
    }

    // ════════════════════════════════════════════════════════════════
    // Phase 38.4 Krok 14g-A (15.5.2026 rano, Marti's "drop na field
    // v jinem panelu se neuskutecni"): atomic cross-parent move + position.
    //
    // Drive (14f-K): _performFieldMove appendl field na konec target
    // containeru bez position control. Plus _performFieldReorder cross-
    // parent → error toast.
    //
    // NEW: cross-parent drag z field A (panel #20) na field B (panel #22):
    //   1. Compute target position v panel #22 siblings (dropAbove = isAbove)
    //   2. PATCH /design/comp-def/update/{A.id} s {parent_comp_def_id:
    //      panel22.id} — move to new parent
    //   3. PUT /design/comp-def/reorder s field_orders array (siblings v
    //      novem parent + moved field na target position) — set sort_order
    //   4. _reloadSpec + flash
    //
    // 2-step (PATCH + reorder) zachovava idempotency. Sort_order multiples
    // of 10 — pripadne re-pad.
    // ════════════════════════════════════════════════════════════════
    async _performCrossParentMove(fromId, toComp, dropAbove) {
      const fields = this._spec.fields || [];
      // Krok 14g-D undo: snapshot original parent + sort_order PRED move
      const fromCompPre = fields.find((f) => f.id === fromId);
      const originalParentId = fromCompPre && fromCompPre.parent_comp_def_id;
      const originalSortOrder = fromCompPre && fromCompPre.sort_order;
      const originalLabel = fromCompPre &&
        (fromCompPre.caption || fromCompPre.name || ("#" + fromId));

      const targetParentId = toComp.parent_comp_def_id;
      // Build new sibling list v target parent (excluding fromId pro pripad
      // ze tam uz neni)
      const targetSiblings = fields
        .filter((f) => f.parent_comp_def_id === targetParentId && f.id !== fromId)
        .sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0));
      // Compute insert position
      let insertAt = targetSiblings.findIndex((f) => f.id === toComp.id);
      if (insertAt < 0) insertAt = targetSiblings.length;
      if (!dropAbove) insertAt += 1;
      // Insert moved field reference
      targetSiblings.splice(insertAt, 0, { id: fromId });
      // Compute new sort_order array (multiples of 10)
      const reorderPayload = targetSiblings.map((f, i) => ({
        id: f.id,
        sort_order: (i + 1) * 10,
      }));

      console.info(
        "[DesignFwForm] crossParentMove",
        "fromId=" + fromId,
        "→ targetParentId=" + targetParentId,
        "@insertAt=" + insertAt,
        "(dropAbove=" + dropAbove + ")"
      );

      try {
        // Step 1: PATCH parent_comp_def_id
        const pr = await fetch(
          "/api/v1/erp/design/comp-def/update/" + encodeURIComponent(fromId),
          {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ parent_comp_def_id: targetParentId }),
          }
        );
        if (!pr.ok) {
          const eb = await pr.json().catch(() => ({}));
          throw new Error("PATCH HTTP " + pr.status + ": " + (eb.error || pr.statusText));
        }
        // Step 2: Reorder v target parent (set sort_order vsech siblings)
        const rr = await fetch("/api/v1/erp/design/comp-def/reorder", {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({ field_orders: reorderPayload }),
        });
        if (!rr.ok) {
          const eb = await rr.json().catch(() => ({}));
          throw new Error("reorder HTTP " + rr.status + ": " + (eb.error || rr.statusText));
        }
        _showToast("Komponenta presunuta + serazena", "success", 2200);
        // Krok 14g-D undo: push inverse (PATCH parent + sort_order back)
        if (originalParentId != null) {
          this._pushUndoOp(
            "Presun '" + originalLabel + "' zpet do parent #" + originalParentId,
            async () => {
              await fetch(
                "/api/v1/erp/design/comp-def/update/" + encodeURIComponent(fromId),
                {
                  method: "PATCH",
                  headers: { "Content-Type": "application/json" },
                  credentials: "include",
                  body: JSON.stringify({
                    parent_comp_def_id: originalParentId,
                    sort_order: originalSortOrder || 10,
                  }),
                }
              );
            }
          );
        }
        this._pendingFlashFieldId = fromId;
        await this._reloadSpec();
      } catch (e) {
        console.error("[DesignFwForm] _performCrossParentMove failed:", e);
        _showToast("Cross-parent presun selhal: " + (e.message || e), "error", 3500);
      }
    }

    // Phase 38.4 Krok 14f-K (14.5.2026 vecer, Marti's "drop se neuskutecni"):
    // Move existing field/groupbox do jineho containeru (panel/groupbox).
    // PATCH /design/comp-def/update/{id} s parent_comp_def_id. Po success
    // reload + flash on moved field. Bez position control — appenduje na
    // konec siblings (auto sort_order). Pro position-aware drop → pouzij
    // _performCrossParentMove (14g-A).
    async _performFieldMove(fieldId, newParentId) {
      // Krok 14g-D undo: snapshot original parent + sort_order PRED move
      const fields = this._spec.fields || [];
      const preComp = fields.find((f) => f.id === fieldId);
      const origParent = preComp && preComp.parent_comp_def_id;
      const origSort = preComp && preComp.sort_order;
      const origLabel = preComp &&
        (preComp.caption || preComp.name || ("#" + fieldId));

      try {
        const r = await fetch(
          "/api/v1/erp/design/comp-def/update/" + encodeURIComponent(fieldId),
          {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ parent_comp_def_id: newParentId }),
          }
        );
        if (!r.ok) {
          const errBody = await r.json().catch(() => ({}));
          throw new Error("HTTP " + r.status + ": " + (errBody.error || r.statusText));
        }
        _showToast("Komponenta presunuta", "success", 2200);
        // Krok 14g-D undo: push inverse
        if (origParent != null) {
          this._pushUndoOp(
            "Presun '" + origLabel + "' zpet do parent #" + origParent,
            async () => {
              await fetch(
                "/api/v1/erp/design/comp-def/update/" + encodeURIComponent(fieldId),
                {
                  method: "PATCH",
                  headers: { "Content-Type": "application/json" },
                  credentials: "include",
                  body: JSON.stringify({
                    parent_comp_def_id: origParent,
                    sort_order: origSort || 10,
                  }),
                }
              );
            }
          );
        }
        this._pendingFlashFieldId = fieldId;
        await this._reloadSpec();
      } catch (e) {
        console.error("[DesignFwForm] _performFieldMove failed:", e);
        _showToast("Presun selhal: " + (e.message || e), "error", 3500);
      }
    }

    // ════════════════════════════════════════════════════════════════
    // Phase 38.4 Krok 14f-B (14.5.2026 vecer, Marti's "B alClient zbytek
    // se nehneme dal"): Delphi VCL dynamic align layout pro panels.
    //
    // Marti's 19yr Delphi doctrine — alClient reservation pattern:
    //   alTop    → reserve top horizontal strip (full width, height=panel.height)
    //   alBottom → reserve bottom strip
    //   alLeft   → reserve left vertical strip (full height po reservations)
    //   alRight  → reserve right vertical strip
    //   alClient → fill REMAINING space (zbytek)
    //   alNone   → absolute positioning (Phase A+1 pattern)
    //
    // Order matters: top → bottom → left → right → client. Client je vzdy
    // posledni, absorbuje zbytek.
    //
    // CSS implementation via nested flexbox:
    //   <div column>
    //     [alTop panels rows]
    //     <div row flex=1>  -- middle
    //       [alLeft cols]
    //       [alClient cols (flex=1)]
    //       [alRight cols]
    //     </div>
    //     [alBottom panels rows]
    //   </div>
    //
    // Bez align key: backward compat → treat as 'client'.
    // ════════════════════════════════════════════════════════════════
    _buildAlignLayout(comps) {
      // Group by align (default = 'client' pro backward compat)
      const byAlign = { top: [], bottom: [], left: [], right: [], client: [], none: [] };
      for (const c of comps) {
        const a = String((c.layout && c.layout.align) || "client").toLowerCase();
        const key = (a in byAlign) ? a : "client";
        byAlign[key].push(c);
      }
      // Sort each align bucket by sort_order
      for (const k of Object.keys(byAlign)) {
        byAlign[k].sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0));
      }

      // Helper: apply size + min size constraint pro align panel
      const _applySize = (el, c, axis) => {
        const layout = c.layout || {};
        const sizeKey = axis === "h" ? "height" : "width";
        const minKey = axis === "h" ? "min_height" : "min_width";
        const size = layout[sizeKey];
        const min = layout[minKey];
        if (size != null && size !== "auto") {
          const v = (typeof size === "number") ? size + "px" : String(size);
          el.style.flex = "0 0 " + v;
        } else {
          el.style.flex = "0 0 auto";
        }
        if (min != null) {
          const m = (typeof min === "number") ? min + "px" : String(min);
          el.style[axis === "h" ? "minHeight" : "minWidth"] = m;
        }
      };

      // Root: column flex
      const wrap = document.createElement("div");
      wrap.className = "erp-design-align-layout";
      wrap.style.cssText =
        "display:flex;flex-direction:column;" +
        "flex:1 1 auto;min-height:0;height:100%;" +
        "position:relative;";  // pro alNone absolute children

      // alTop panels (full width strips, stacked top)
      for (const c of byAlign.top) {
        const el = this._renderComponentTree(c, 0, 1);
        if (el) {
          _applySize(el, c, "h");
          el.style.width = "100%";
          wrap.appendChild(el);
        }
      }

      // Middle row (alLeft + alClient + alRight)
      const hasMiddle = byAlign.left.length > 0 ||
                       byAlign.right.length > 0 ||
                       byAlign.client.length > 0;
      let middle = null;
      if (hasMiddle) {
        middle = document.createElement("div");
        middle.className = "erp-design-align-middle";
        middle.style.cssText =
          "display:flex;flex-direction:row;" +
          "flex:1 1 auto;min-height:0;min-width:0;";
        // alLeft panels (full height, fixed width)
        for (const c of byAlign.left) {
          const el = this._renderComponentTree(c, 0, 1);
          if (el) {
            _applySize(el, c, "w");
            el.style.height = "100%";
            middle.appendChild(el);
          }
        }
        // alClient panels (fill remaining)
        // Multiple alClient — stack vertically inside flex=1 wrapper
        if (byAlign.client.length > 0) {
          const clientWrap = document.createElement("div");
          clientWrap.className = "erp-design-align-client-wrap";
          clientWrap.style.cssText =
            "display:flex;flex-direction:column;" +
            "flex:1 1 auto;min-width:0;min-height:0;";
          for (const c of byAlign.client) {
            const el = this._renderComponentTree(c, 0, byAlign.client.length);
            if (el) {
              el.style.flex = "1 1 auto";
              el.style.minHeight = "0";
              el.style.minWidth = "0";
              const layout = c.layout || {};
              if (layout.min_width != null) {
                el.style.minWidth = (typeof layout.min_width === "number")
                  ? layout.min_width + "px" : String(layout.min_width);
              }
              if (layout.min_height != null) {
                el.style.minHeight = (typeof layout.min_height === "number")
                  ? layout.min_height + "px" : String(layout.min_height);
              }
              clientWrap.appendChild(el);
            }
          }
          middle.appendChild(clientWrap);
        }
        // alRight panels
        for (const c of byAlign.right) {
          const el = this._renderComponentTree(c, 0, 1);
          if (el) {
            _applySize(el, c, "w");
            el.style.height = "100%";
            middle.appendChild(el);
          }
        }
        wrap.appendChild(middle);
      }

      // alBottom panels (full width strips, stacked bottom)
      for (const c of byAlign.bottom) {
        const el = this._renderComponentTree(c, 0, 1);
        if (el) {
          _applySize(el, c, "h");
          el.style.width = "100%";
          wrap.appendChild(el);
        }
      }

      // alNone panels — absolute positioning (Phase A+1 pattern)
      for (const c of byAlign.none) {
        const el = this._renderComponentTree(c, 0, 1);
        if (el) {
          const layout = c.layout || {};
          el.style.position = "absolute";
          if (layout.top != null) {
            el.style.top = (typeof layout.top === "number")
              ? layout.top + "px" : String(layout.top);
          }
          if (layout.left != null) {
            el.style.left = (typeof layout.left === "number")
              ? layout.left + "px" : String(layout.left);
          }
          if (layout.width != null && layout.width !== "auto") {
            el.style.width = (typeof layout.width === "number")
              ? layout.width + "px" : String(layout.width);
          }
          if (layout.height != null && layout.height !== "auto") {
            el.style.height = (typeof layout.height === "number")
              ? layout.height + "px" : String(layout.height);
          }
          wrap.appendChild(el);
        }
      }

      return wrap;
    }

    _renderLeafField(comp, idx, total) {
      const ctx = this.__renderCtx || {};
      const data = ctx.data || {};
      const D = ctx.onDirty || (() => {});

      const value = data[comp.name];
      const fieldEl = this._renderField(comp, value, D);
      if (!fieldEl) return null;

      // Krok 14b+10 (13.5.2026 ~22:00, Marti's "always-left" property):
      // apply grid-column-start:1 pokud layout.always_new_row === true.
      const alwaysNewRow = !!(comp.layout && comp.layout.always_new_row);

      // Phase 38.4 Krok 14f-N (14.5.2026 vecer, Marti's "sirka komponenty
      // na displeji"): aply layout.min_width / max_width na field wrap.
      // Pozor: drz se v rozumnem range (CSS grid auto-fit reaguje).
      const _applyWidthConstraints = (el) => {
        if (!comp.layout) return;
        if (comp.layout.min_width != null && comp.layout.min_width > 0) {
          el.style.minWidth = comp.layout.min_width + "px";
        }
        if (comp.layout.max_width != null && comp.layout.max_width > 0) {
          el.style.maxWidth = comp.layout.max_width + "px";
        }
      };

      // Krok 14b+8 (13.5.2026 ~20:45): v DESIGN mode wrap field do
      // draggable containeru pro reorder. Plus drag handle.
      // Krok 14c+3.2 (14.5.2026 odp.): DESIGN wrap napric VSEMI panels
      // (Marti's "Lookup v footer nema ikonky").
      if (this._formDesignMode === true) {
        const wrapped = this._wrapFieldForDesign(fieldEl, comp, idx, total);
        if (alwaysNewRow) wrapped.style.gridColumnStart = "1";
        _applyWidthConstraints(wrapped);
        return wrapped;
      } else {
        if (alwaysNewRow) fieldEl.style.gridColumnStart = "1";
        _applyWidthConstraints(fieldEl);
        return fieldEl;
      }
    }

    _renderContainerNode(container) {
      const ctx = this.__renderCtx || {};
      const byParent = ctx.byParent || new Map();
      const code = container.comp_type_code;
      const layout = container.layout || {};
      const children = byParent.get(container.id) || [];

      // ─── Panel = structural container ─────────────────────────────
      // Marti's doctrine (Krok 14e, 14.5.2026 vecer): panel je purely
      // structural — visual styling delegujeme na nested groupbox.
      //
      // V PROD mode: display:contents (panel se "rozpusti", children
      //   prevzimaji grid placement of parent sec.grid → groupbox je
      //   prime dite sec.grid grid-column:1/-1).
      // V DESIGN mode (Krok 14e-E, 14.5. vecer): visible wrapper
      //   s dashed border + drag handle pro reorder + child grid
      //   sections uvnitr panelu (Marti's Q3 — child grids "patri na panel").
      if (code === "panel") {
        const designMode = this._formDesignMode === true;
        const wrap = document.createElement("div");
        wrap.className = "erp-design-panel";
        wrap.dataset.compDefId = String(container.id);
        wrap.dataset.compTypeCode = "panel";
        wrap.dataset.parentCompDefId = String(container.parent_comp_def_id || "");

        // Phase 38.4 Krok 14f-B (14.5.2026 vecer): panel ma display:flex
        // v obou modes — wrapper musi byt flex item kvuli _buildAlignLayout
        // flex:1 sizing. display:contents (drive Krok 14e-E) ze rusi flex
        // styling (no box). Switch na display:flex column.
        //
        // Phase 38.4 Krok 14f-N (14.5.2026 vecer, Marti's "3 komponenty
        // vedle sebe"): pokud panel ma direct leaf fields (no groupbox/
        // panel children), apply CSS grid auto-fit pro side-by-side layout.
        // Pokud panel ma container children (groupbox), zustane flex column
        // (groupbox samotny dela inner grid).
        const hasContainerChild = children.some(c =>
          c.comp_type_code === "panel" || c.comp_type_code === "groupbox"
        );
        const hasLeafChild = children.some(c =>
          c.comp_type_code !== "panel" && c.comp_type_code !== "groupbox"
        );
        const useImplicitGrid = !hasContainerChild && hasLeafChild;
        const baseStyle = useImplicitGrid
          ? "display:grid;grid-template-columns:repeat(auto-fit, minmax(220px, 1fr));" +
            "gap:6px 14px;align-items:start;min-width:0;position:relative;"
          : "display:flex;flex-direction:column;min-height:0;min-width:0;position:relative;";

        if (designMode) {
          // Visible wrapper s drag affordance
          wrap.style.cssText = baseStyle +
            "border:1px dashed rgba(122, 134, 150, 0.3);" +
            "border-radius:4px;" +
            "padding:8px;" +
            "margin:2px;";
          wrap.draggable = true;

          // Label "panel" v levem hornim rohu — clickable pro settings (Krok 14f-D)
          const lbl = document.createElement("div");
          const alignLabel = (container.layout && container.layout.align) || "client";
          lbl.textContent = "▦ panel #" + container.id + " · " + alignLabel + " ⚙";
          lbl.title = "Klikni pro nastaveni panelu (nebo right-click)";
          lbl.style.cssText =
            "position:absolute;top:-8px;left:8px;" +
            "background:#0d1117;color:#5d6975;" +
            "font-size:10px;padding:2px 8px;" +
            "border-radius:2px;letter-spacing:0.5px;" +
            "user-select:none;cursor:pointer;z-index:2;" +
            "transition:color 0.15s, background 0.15s;";
          lbl.addEventListener("mouseenter", () => {
            lbl.style.color = "#a88cd4";
            lbl.style.background = "#1a2028";
          });
          lbl.addEventListener("mouseleave", () => {
            lbl.style.color = "#5d6975";
            lbl.style.background = "#0d1117";
          });
          lbl.addEventListener("click", (ev) => {
            ev.stopPropagation();
            this._openContainerSettings(container);
          });
          wrap.appendChild(lbl);

          // Right-click handler — open settings popup (Krok 14f-D)
          wrap.addEventListener("contextmenu", (ev) => {
            // Skip pokud klik na child interactive element (input/button)
            const tag = ev.target && ev.target.tagName;
            if (tag === "INPUT" || tag === "BUTTON" || tag === "TEXTAREA" || tag === "SELECT") {
              return;  // necht browser default kontextmenu chodi
            }
            ev.preventDefault();
            ev.stopPropagation();
            this._openContainerSettings(container);
          });

          // Drag listeners (analog _wrapFieldForDesign)
          this._attachContainerDragEvents(wrap, container);
        } else {
          // PROD: invisible wrapper but s flex sizing
          wrap.style.cssText = baseStyle;
        }

        // Phase 38.4 Krok 14e-G (Marti's Q3, volba A memory-only):
        // Child sections (TELEFONY/EMAILY) jsou UVNITR panelu, ne paralelne.
        //
        // Phase 38.4 Krok 14f-G fix (14.5.2026 vecer, Marti's "dropnul
        // jsem novy panel, zkopirovaly se gridy"): render child sections
        // JEN v prvnim alClient panelu. Pokud Marti pridal alTop/alBottom/
        // alLeft/alRight panel, child sections zustavaji v alClient
        // (canonical main area — Delphi alClient = "remaining space").
        const isClientAlign = ((container.layout && container.layout.align) || "client") === "client";
        const shouldRenderChildren = isClientAlign && !this._childrenRenderedInAnyPanel;
        if (shouldRenderChildren) {
          this._childrenRenderedInAnyPanel = true;  // mark for subsequent panels
        }

        const childrenData = (this._spec && this._spec.children) || {};
        const childKeys = Object.keys(childrenData);
        const childPosition = this._childPosition || {};
        const childOrder = Array.isArray(this._childOrder) && this._childOrder.length === childKeys.length
          ? this._childOrder
          : childKeys.slice();
        // Phase 38.4 Krok 14f-I (14.5.2026 vecer, Marti's "settings pro
        // gridy s Odebrat"): filter hidden child keys (this._childHidden)
        const childHidden = this._childHidden || {};
        const visibleChildOrder = childOrder.filter((k) => !childHidden[k]);
        const beforeGroupbox = shouldRenderChildren ? visibleChildOrder.filter(
          (k) => (childPosition[k] || "before-main") === "before-main"
        ) : [];
        const afterGroupbox = shouldRenderChildren ? visibleChildOrder.filter(
          (k) => childPosition[k] === "after-main"
        ) : [];

        // Render child sections BEFORE groupbox
        for (const childKey of beforeGroupbox) {
          const childInfo = childrenData[childKey];
          if (!childInfo) continue;
          const sec = this._renderChildSection(childKey, childInfo);
          if (sec) wrap.appendChild(sec);
        }

        // Render container children (typically groupbox)
        for (let i = 0; i < children.length; i++) {
          const childEl = this._renderComponentTree(children[i], i, children.length);
          if (childEl) wrap.appendChild(childEl);
        }

        // Render child sections AFTER groupbox
        for (const childKey of afterGroupbox) {
          const childInfo = childrenData[childKey];
          if (!childInfo) continue;
          const sec = this._renderChildSection(childKey, childInfo);
          if (sec) wrap.appendChild(sec);
        }

        return wrap;
      }

      // ─── Groupbox = visual border-top + optional label ────────────
      // Marti's 14.5. vecer doctrine: 2 border_mode varianty
      //   - 'top'  → linka nahore + optional label uvnitr (modern, default)
      //   - 'all'  → full ramecek (classic Delphi compat)
      // layout.label (NULL = bez labelu).
      //
      // Phase 38.4 Krok 14f-P (14.5.2026 vecer, Marti's "ja jsem si to
      // ponicil... vlozil jsem tam groupbox, neni nikde videt... muzes
      // ho zviditelnit a umoznit parametrizaci a smazani"):
      // V DESIGN mode pridat dashed wrapper + label tag (▦ groupbox #ID ⚙)
      // + drag handle. Analog panel wrapper pattern.
      if (code === "groupbox") {
        const designMode = this._formDesignMode === true;
        const wrap = document.createElement("div");
        wrap.className = "erp-design-groupbox";
        wrap.dataset.compDefId = String(container.id);
        wrap.dataset.compTypeCode = "groupbox";

        const borderMode = (layout.border_mode || "top").toLowerCase();
        const labelText = (layout.label != null && String(layout.label).trim().length > 0)
          ? String(layout.label).trim()
          : null;

        if (designMode) {
          // DESIGN: visible wrapper s dashed border + drag + settings affordance.
          // Drop PROD-only border-top / 'all' ramecek — DESIGN overlay je
          // dashed gray identifier. Po prepnuti na PROD se zobrazi PROD
          // styling (border-top nebo full ramecek) podle layout.border_mode.
          wrap.style.cssText =
            "display:flex;flex-direction:column;" +
            "border:1px dashed rgba(212, 184, 138, 0.4);" +  // amber dashed
            "border-radius:4px;" +
            "padding:14px 8px 8px 8px;" +
            "margin:8px 0 2px 0;" +
            "grid-column:1/-1;" +
            "min-width:0;position:relative;";
          wrap.draggable = true;

          // Label tag v levem hornim rohu — clickable settings
          const tag = document.createElement("div");
          const labelDisplay = labelText
            ? labelText
            : "(no label)";
          tag.textContent = "▦ groupbox #" + container.id + " · " + labelDisplay + " ⚙";
          tag.title = "Klikni pro nastaveni groupboxu (nebo right-click)";
          tag.style.cssText =
            "position:absolute;top:-8px;left:8px;" +
            "background:#0d1117;color:#d4b88a;" +
            "font-size:10px;padding:2px 8px;" +
            "border-radius:2px;letter-spacing:0.5px;" +
            "user-select:none;cursor:pointer;z-index:2;" +
            "transition:color 0.15s, background 0.15s;";
          tag.addEventListener("mouseenter", () => {
            tag.style.color = "#a88cd4";
            tag.style.background = "#1a2028";
          });
          tag.addEventListener("mouseleave", () => {
            tag.style.color = "#d4b88a";
            tag.style.background = "#0d1117";
          });
          tag.addEventListener("click", (ev) => {
            ev.stopPropagation();
            this._openContainerSettings(container);
          });
          wrap.appendChild(tag);

          // Right-click handler — open settings popup (Krok 14f-D)
          wrap.addEventListener("contextmenu", (ev) => {
            const tg = ev.target && ev.target.tagName;
            if (tg === "INPUT" || tg === "BUTTON" || tg === "TEXTAREA" || tg === "SELECT") {
              return;
            }
            ev.preventDefault();
            ev.stopPropagation();
            this._openContainerSettings(container);
          });

          // Drag listeners — analog panel (reorder + cross-container move
          // pres _attachContainerDragEvents). Marti muze drag groupbox
          // mezi panely / reorder uvnitr panelu.
          this._attachContainerDragEvents(wrap, container);
        } else {
          // PROD mode: existing visual styling (border-top / 'all')
          if (borderMode === "all") {
            wrap.style.cssText =
              "border:1px solid #2a3340;border-radius:4px;" +
              "padding:14px 12px 10px 12px;" +
              "margin:6px 0;" +
              "grid-column:1/-1;";
          } else {
            // 'top' default — jen linka nahore, padding-top
            wrap.style.cssText =
              "border-top:1px solid #2a3340;" +
              "padding:10px 0 4px 0;" +
              "margin:6px 0 0 0;" +
              "grid-column:1/-1;";
          }

          // Optional label (PROD: subtle uppercase legend)
          if (labelText) {
            const lbl = document.createElement("div");
            lbl.className = "erp-design-groupbox-label";
            lbl.textContent = labelText;
            lbl.style.cssText =
              "display:inline-block;" +
              "background:#0d1117;" +
              "color:#7a8696;" +
              "font-size:11px;" +
              "font-weight:600;" +
              "text-transform:uppercase;" +
              "letter-spacing:0.5px;" +
              "padding:2px 8px;" +
              "margin-bottom:8px;" +
              (borderMode === "top"
                ? "margin-top:-18px;"
                : "margin-top:-20px;");
            wrap.appendChild(lbl);
          }
        }

        // Inner grid pro children — same layout jako sec.grid (2 cols, auto)
        const inner = document.createElement("div");
        inner.className = "erp-design-groupbox-inner";
        inner.style.cssText =
          "display:grid;" +
          "grid-template-columns:repeat(auto-fit, minmax(220px, 1fr));" +
          "gap:6px 14px;" +
          "align-items:start;";
        wrap.appendChild(inner);

        for (let i = 0; i < children.length; i++) {
          const childEl = this._renderComponentTree(children[i], i, children.length);
          if (childEl) inner.appendChild(childEl);
        }

        return wrap;
      }

      // Unknown container code — defensive: render jako transparent wrapper
      console.warn("[DesignFwForm] Unknown container code:", code, container);
      const fallback = document.createElement("div");
      fallback.style.display = "contents";
      for (let i = 0; i < children.length; i++) {
        const childEl = this._renderComponentTree(children[i], i, children.length);
        if (childEl) fallback.appendChild(childEl);
      }
      return fallback;
    }

    _renderField(field, value, onDirty) {
      const fieldKey = (this._spec.core.code || "fw_form") + "." + field.name;
      const compType = field.comp_type_code;
      const fieldLayout = field.layout || {};
      const label = field.caption || field.name;
      // Krok 14b+8 (13.5.2026 ~21:00, Marti's "v design form modu musi byt
      // komponenty RO"): v DESIGN mode vsechny fields readonly bez ohledu
      // na fieldLayout.readonly. Uzivatel vidi pozici/strukturu, ale
      // needitujeme data behem reorder operace. Drz "audit primary, edit
      // secondary, struktura terciary" — nelze najednou edit struct +
      // edit dat (data save endpoint nesahá na struct).
      const readonly = !!fieldLayout.readonly || this._formDesignMode === true;

      // Phase 38.4 Krok 14c (13.5.2026 ~16:00): dispatch rozsiren o vsech
      // 10 Marti-AI's preview_html-ready comp_types. Drz "uniformita
      // vítězí" — kazdy known comp_type ma explicit branch, novy comp_type
      // = pridat case + pripadne UI Kit helper.
      // Phase 38.4 Krok 14c hotfix (13.5.2026 ~17:30): _field/_dropdown/_memo
      // signature je (label, value, opts) — fieldKey patri DO opts, nepredavat
      // jako 3rd parameter (predtim bug: opts = string fieldKey, opts.onDirty
      // undefined → dirty tracking nikdy nezavolan).
      // Phase 38.4 Krok 14f-M (14.5.2026 vecer, Marti's "max_length /
      // min_length"): forward layout properties do _field opts.
      // _field aplikuje HTML5 maxLength + minLength + placeholder +
      // required attributes na inp.input.
      const _fieldOptsBase = {
        fieldKey: fieldKey,
        readonly: readonly || !!fieldLayout.readonly,
        onDirty: onDirty,
        maxLength: fieldLayout.max_length,
        minLength: fieldLayout.min_length,
        placeholder: fieldLayout.placeholder,
        required: !!fieldLayout.required,
      };
      switch (compType) {
        case "edit":
          return _field(label, value, Object.assign({}, _fieldOptsBase, {
            mono: !!fieldLayout.mono,
          }));

        case "number": {
          // _field s type=number — ErpInput podporuje type via opts
          const el = _field(label, value, _fieldOptsBase);
          // Override input type to number (post-render tweak)
          try {
            const input = el.querySelector("input");
            if (input) input.type = "number";
          } catch (e) {}
          return el;
        }

        case "checkbox_modern": {
          // Boolean checkbox — value je true/false (nebo string '1'/'0')
          const wrap = document.createElement("div");
          wrap.className = "erp-field erp-field-design";
          wrap.style.cssText = "display:flex;flex-direction:column;gap:3px;";
          wrap._fieldKey = fieldKey;
          wrap._kind = "field";

          const labelEl = document.createElement("div");
          labelEl.className = "erp-input-label";
          labelEl.style.cssText = "font-size:12px;color:#a8b4c2;cursor:context-menu;";
          labelEl.setAttribute("data-design-fieldkey", fieldKey);
          labelEl.dataset.designOrigLabel = label;
          labelEl.textContent = label;

          const cbWrap = document.createElement("label");
          cbWrap.style.cssText = "display:flex;align-items:center;gap:8px;padding:6px 0;cursor:pointer;";
          const cb = document.createElement("input");
          cb.type = "checkbox";
          cb.style.cssText = "width:18px;height:18px;cursor:pointer;";
          // Coerce value to bool: true / 'true' / 1 / '1' all → true
          cb.checked = (value === true || value === "true" || value === 1 || value === "1");
          cb.disabled = readonly;

          const valLabel = document.createElement("span");
          valLabel.style.cssText = "font-size:13px;color:#cfd6df;";
          valLabel.textContent = cb.checked ? "Ano" : "Ne";
          cbWrap.appendChild(cb);
          cbWrap.appendChild(valLabel);

          // _inst exposed pro Save handler (collect dirty value via .value())
          wrap._inst = {
            value: () => cb.checked,
            input: cb,
          };
          wrap._origVal = cb.checked;
          if (!readonly) {
            cb.addEventListener("change", () => {
              valLabel.textContent = cb.checked ? "Ano" : "Ne";
              const isDirty = cb.checked !== wrap._origVal;
              if (typeof onDirty === "function") onDirty(fieldKey, isDirty);
            });
          }
          wrap.appendChild(labelEl);
          wrap.appendChild(cbWrap);
          return wrap;
        }

        case "date_modern": {
          // ErpDate komponenta (Phase B+6.7) — pokud zaregistrovana,
          // jinak fallback na _field s type='date'.
          const el = _field(label, value, {
            fieldKey: fieldKey,
            readonly: readonly,
            onDirty: onDirty,
          });
          try {
            const input = el.querySelector("input");
            if (input) input.type = "date";
          } catch (e) {}
          return el;
        }

        case "memo": {
          // Textarea — pokud _memo helper zaregistrovan
          if (typeof _memo === "function") {
            return _memo(label, value, {
              fieldKey: fieldKey,
              readonly: readonly,
              onDirty: onDirty,
            });
          }
          // Fallback: _field but multiline (cosmetic — height: 60px)
          const el = _field(label, value, {
            fieldKey: fieldKey,
            readonly: readonly,
            onDirty: onDirty,
          });
          try {
            const input = el.querySelector("input");
            if (input) {
              const txt = document.createElement("textarea");
              txt.value = value || "";
              txt.style.cssText = input.style.cssText + ";min-height:60px;resize:vertical;";
              txt.disabled = readonly;
              input.parentElement.replaceChild(txt, input);
              // Update _inst.value() to read from textarea
              if (el._inst) {
                el._inst.value = () => txt.value;
                el._inst.input = txt;
              }
              if (!readonly) {
                txt.addEventListener("input", () => {
                  if (typeof onDirty === "function") {
                    onDirty(fieldKey, txt.value !== (value || ""));
                  }
                });
              }
            }
          } catch (e) {}
          return el;
        }

        case "lookup":
        case "combobox": {
          // Lookup / combobox — _dropdown helper s enum_values z layout
          //
          // Krok 14b+13.2 hotfix (14.5.2026 ~01:00, Marti's smoke "Detekce
          // probehne, ale do listboxu se to nepropise"): SIGNATURE MISMATCH
          // FIX. _dropdown signature je (label, value, ITEMS, opts) —
          // items jako 3. parameter, ne v opts.
          //
          // Krok 14b+13.3 (14.5.2026 ~01:20, Marti's "Zatim se do listu
          // nepropisou"): diagnostic log + defensive enum_values parsing.
          // Pokud DB ulozil enum_values jako string (psycopg2 quirk pro
          // double-encoded JSONB), parse pres JSON.parse fallback.
          let enumVals = fieldLayout.enum_values;
          if (typeof enumVals === "string") {
            try {
              enumVals = JSON.parse(enumVals);
            } catch (e) {
              console.warn("[DesignFwForm] enum_values is string, JSON.parse failed:", enumVals);
              enumVals = null;
            }
          }
          const items = Array.isArray(enumVals)
            ? enumVals.map(e => {
                if (typeof e === "string") return { value: e, label: e };
                if (e && typeof e === "object") {
                  return {
                    value: e.value != null ? String(e.value) : "",
                    label: e.label != null ? String(e.label) : String(e.value || ""),
                  };
                }
                return null;
              }).filter(Boolean)
            : [];
          // Diagnostic log pro Marti — uvidí co lookup case dostává
          console.info(
            "[DesignFwForm] lookup case fieldKey=" + fieldKey,
            "compType=" + compType,
            "raw enum_values=", fieldLayout.enum_values,
            "parsed enumVals=", enumVals,
            "items.length=" + items.length,
            "items=", items
          );
          return _dropdown(label, value, items, {
            fieldKey: fieldKey,
            readonly: readonly,
            onDirty: onDirty,
          });
        }

        case "lookup_multi": {
          // Multi-select — fallback na _field s comma-separated values (MVP).
          // Future: dedicated multi-select komponent.
          const displayVal = Array.isArray(value) ? value.join(", ") : (value || "");
          return _field(label + " (multi)", displayVal, {
            fieldKey: fieldKey,
            readonly: true, // MVP: readonly pro multi-select
            onDirty: onDirty,
          });
        }

        case "label_readonly": {
          // Read-only display label — bez input, jen text
          const wrap = document.createElement("div");
          wrap.className = "erp-field erp-field-design erp-field-readonly-label";
          wrap.style.cssText = "display:flex;flex-direction:column;gap:3px;";
          wrap._fieldKey = fieldKey;
          wrap._kind = "field";

          const labelEl = document.createElement("div");
          labelEl.style.cssText = "font-size:12px;color:#a8b4c2;cursor:context-menu;";
          labelEl.setAttribute("data-design-fieldkey", fieldKey);
          labelEl.dataset.designOrigLabel = label;
          labelEl.textContent = label;

          const valEl = document.createElement("div");
          valEl.style.cssText = "padding:6px 8px;color:#cfd6df;font-size:13px;font-style:italic;";
          valEl.textContent = (value == null || value === "") ? "—" : String(value);

          wrap.appendChild(labelEl);
          wrap.appendChild(valEl);
          // No _inst — readonly, no dirty tracking
          return wrap;
        }

        case "file":
        case "button":
          // File upload + button jsou special (non-edit) — render readonly placeholder
          // pro main panel display. Real interactivity prijde v dedicated UI Kit
          // wrappers (Phase 14d+).
          return _field(label + " (" + compType + ")", value || "", {
            fieldKey: fieldKey,
            readonly: true,
            onDirty: onDirty,
          });

        case "entity_picker": {
          // Phase 38.4 Krok 14g Etapa F Krok 5.G (16.5.2026 vecer, Marti's
          // "1 komponenta + N instancí s data_source binding"):
          // entity_picker komponenta — render groupbox s label + 2 fields
          // (Číslo + Název) + 3 quick action ikony (🔗 / 🚫 / ➕).
          //
          // Data flow: comp_def.data_source_id → backend SELECT JOIN vraci
          // data_source_code → frontend volá /api/v1/erp/data/{code} pro
          // rows + builds picker on click.
          //
          // Marti's Centrála 1 paralela: TUserFormList s LookupView/LookupField/
          // LookupDisplay. Drz "uniformita vítězí" — 1 entity_picker comp_type,
          // N instances přes per-instance data_source_id binding.
          const dsCode = field.data_source_code || null;
          const dsName = field.data_source_name || null;
          const lookupId = (fieldLayout.lookup_id_field) || "id";
          const lookupDisplay = (fieldLayout.lookup_display_field) || "label";
          const actions = fieldLayout.show_quick_actions || ["link", "unlink", "create_new"];

          // Phase 38.4 Krok 14g Etapa F Krok 5.I-D/E/F (16.5.2026 vecer,
          // Marti's two-layer data_source pattern volby):
          //   display_mode='origin'    -> Picker #1 Soudecek: display-only,
          //     ctena z this._spec.origin.menu_node (backend denormalize)
          //   display_mode='self'      -> Picker #2 Prehled: display-only,
          //     ctena z this._spec.core (currentCore.id + currentCore.label)
          //   display_mode='editable'  -> Picker #3 Datovy zdroj: full
          //     functionality, field_extern='data_source_id' jako save target
          //
          // Marti's "field_extern, ne target_field" terminologie (16.5. odp.):
          //   bidirectional binding column ve fw.comp_def row pres
          //   PATCH design/comp_def/{id} (Marti's "SELECT EDIT POST"
          //   dirty fields pattern z Centraly 1).
          const displayMode = fieldLayout.display_mode || "editable";
          const fieldExtern = fieldLayout.field_extern || null;
          const isDisplayOnly = (displayMode === "origin" || displayMode === "self");

          // Pre-populate values dle display_mode
          let initialId = null;
          let initialLabel = null;
          if (displayMode === "origin") {
            // Z this._spec.origin.menu_node (backend JOIN fw.menu_node)
            const origin = (this._spec && this._spec.origin) || {};
            const mn = origin.menu_node || null;
            if (mn) {
              initialId = mn.id;
              initialLabel = mn.label;
            }
          } else if (displayMode === "self") {
            // Krok 5.I-E hotfix (16.5.2026 ~22:35, Marti's screenshot bug):
            // self-reference = current CORE (ne data row). Marti's logika z
            // 16.5. dopoledne: "Picker #2 Prehled zobrazuje current core.id +
            // core.label, NE data.id". Pro core_design data IS core, ale pro
            // user_edit data je users row (bez label sloupce) — bug viditelny.
            const coreRow = (this._spec && this._spec.core) || {};
            initialId = coreRow.id != null ? coreRow.id : null;
            initialLabel = coreRow.label || coreRow.code || null;
          } else if (displayMode === "editable" && fieldExtern) {
            // Krok 5.I-F: Picker #3 (Datovy zdroj) — initial z form root
            // comp_def via this._spec.form (po Krok 5.I-F backend extension).
            // field_extern='data_source_id' → form.data_source_id + JOIN ds.code/name.
            const formRoot = (this._spec && this._spec.form) || {};
            if (fieldExtern === "data_source_id") {
              initialId = formRoot.data_source_id != null ? formRoot.data_source_id : null;
              initialLabel = formRoot.data_source_name || formRoot.data_source_code || null;
            } else {
              // Generic fallback — budouci pickery s jinym field_extern.
              // Backend root_row musi tyto sloupce vracet (pro now jen
              // data_source_id explicit JOIN-uto).
              initialId = formRoot[fieldExtern] != null ? formRoot[fieldExtern] : null;
              initialLabel = null;
            }
          }

          const wrap = document.createElement("div");
          wrap.className = "erp-field erp-field-design erp-entity-picker-host";
          wrap.style.cssText =
            "display:flex;flex-direction:column;gap:6px;" +
            "border:1px solid #2a3340;border-radius:6px;padding:12px;background:#0f1419;";
          wrap._fieldKey = fieldKey;
          wrap._kind = "entity_picker";
          wrap._displayMode = displayMode;
          wrap._fieldExtern = fieldExtern;

          // Header — label + data_source code/name badge
          const headerRow = document.createElement("div");
          headerRow.style.cssText =
            "display:flex;justify-content:space-between;align-items:center;" +
            "padding-bottom:4px;border-bottom:1px solid #1f2630;";

          const labelEl = document.createElement("div");
          labelEl.style.cssText =
            "font-size:11px;font-weight:600;color:#a8b4c2;letter-spacing:0.05em;" +
            "text-transform:uppercase;cursor:context-menu;";
          labelEl.setAttribute("data-design-fieldkey", fieldKey);
          labelEl.dataset.designOrigLabel = label;
          labelEl.textContent = label;
          headerRow.appendChild(labelEl);

          if (dsCode) {
            const badge = document.createElement("div");
            badge.style.cssText =
              "font-size:10px;color:#6a7684;font-style:italic;";
            badge.title = dsName || dsCode;
            badge.textContent = "ds: " + dsCode;
            headerRow.appendChild(badge);
          }

          // Display-mode badge — visual distinction pro origin/self pickery
          // (Marti-AI's "neni to omezeni, je to pojistka" doctrine 27.4.)
          if (isDisplayOnly) {
            const modeBadge = document.createElement("div");
            modeBadge.style.cssText =
              "font-size:10px;color:#8fb8d4;font-style:italic;" +
              "padding:2px 6px;background:#1a2632;border-radius:3px;";
            if (displayMode === "origin") {
              modeBadge.textContent = "📍 origin";
              modeBadge.title = "Display-only: zobrazeno z origin_menu_node_id (Soudeček, ze kterého byl form otevřen)";
            } else if (displayMode === "self") {
              modeBadge.textContent = "↺ self";
              modeBadge.title = "Display-only: editujeme tento záznam (self-reference)";
            }
            headerRow.appendChild(modeBadge);
          }
          wrap.appendChild(headerRow);

          // Action ikony row (🔗 / 🚫 / ➕)
          const actionsRow = document.createElement("div");
          actionsRow.style.cssText = "display:flex;gap:6px;align-items:center;";

          const ACTION_DEFS = {
            link: { icon: "🔗", title: "Vybrat existující záznam", color: "#8fb8d4" },
            unlink: { icon: "🚫", title: "Zrušit asociaci", color: "#d48787" },
            create_new: { icon: "➕", title: "Vytvořit nový záznam", color: "#7ed4a8" },
          };

          // Číslo (id) + Název (display) fields (read-only — populate přes link)
          const fieldsRow = document.createElement("div");
          fieldsRow.style.cssText =
            "display:grid;grid-template-columns:120px 1fr;gap:10px;align-items:end;flex:1;";

          // Krok 5.I-D/E: pre-populate s initialId/initialLabel (z origin/self
          // display_mode). Pro editable mode initialId zatim null — Krok 5.I-F
          // pro post-load fetch z data_source.
          const idColValue = initialId != null ? String(initialId) : "";
          const labelColValue = initialLabel != null ? String(initialLabel) : "";
          const idCol = _field("Číslo", idColValue, {
            fieldKey: fieldKey + "._id",
            readonly: true,
            mono: true,
            onDirty: onDirty,
          });
          const labelCol = _field("Název", labelColValue, {
            fieldKey: fieldKey + "._label",
            readonly: true,
            onDirty: onDirty,
          });
          fieldsRow.appendChild(idCol);
          fieldsRow.appendChild(labelCol);

          // Store initial value pro Krok 5.I-G dirty check (jen pro editable mode)
          if (!isDisplayOnly && initialId != null) {
            wrap._initialValue = {
              id: initialId,
              display: initialLabel,
            };
          }

          // Phase 38.4 Krok 14g Etapa F Krok 5.H (16.5.2026 vecer, Marti's
          // "pauza, ty pracuj"): 🔗 link onclick → fetch /api/v1/erp/data/{dsCode}
          // → ErpCatalogPicker (existing class) → onSelect populate idCol/labelCol.
          // PATCH persistence parent entity = Krok 5.I (post Marti-AI consult).
          actions.forEach(function (act) {
            const def = ACTION_DEFS[act];
            if (!def) return;
            const btn = document.createElement("button");
            btn.type = "button";
            btn.textContent = def.icon;
            btn.title = def.title;
            // Link je vždy klikatelný (browse picker). Unlink + create_new
            // disabled v PROD/RO mode.
            // Krok 5.I-D/E (16.5.2026 vecer): display-only mode (origin/self)
            // disables VSECHNY buttons — Picker #1 cte z core.origin_menu_node_id
            // (display-only), Picker #2 cte z current core row (readonly self-ref).
            const btnDisabled = isDisplayOnly || (readonly && act !== "link");
            btn.disabled = btnDisabled;
            btn.style.cssText =
              "padding:6px 10px;font-size:14px;border-radius:4px;cursor:" +
              (btnDisabled ? "default" : "pointer") + ";" +
              "background:#1a1f26;border:1px solid #2a3340;color:" + def.color + ";" +
              (btnDisabled ? "opacity:0.4;" : "");

            if (act === "link" && dsCode) {
              btn.addEventListener("click", async function () {
                if (typeof window.ErpCatalogPicker !== "function") {
                  alert("ErpCatalogPicker není načtený (catalog_picker.js).");
                  return;
                }
                try {
                  const _picker = new window.ErpCatalogPicker({
                    title: "🔗 Vybrat " + label + " (z " + (dsName || dsCode) + ")",
                    endpoint: "/api/v1/erp/data/" + encodeURIComponent(dsCode) + "?limit=500",
                    listKey: "rows",
                    idField: lookupId,
                    labelField: lookupDisplay,
                    width: "900px",
                    columns: [
                      { headerName: "ID", field: lookupId, width: 80, type: "numericColumn" },
                      { headerName: "Code", field: "code", width: 220 },
                      { headerName: "Název", field: lookupDisplay, flex: 1, minWidth: 200 },
                    ],
                    onSelect: function (row) {
                      // Populate read-only fields s vybranou hodnotou
                      try {
                        const idInput = idCol.querySelector("input");
                        const labelInput = labelCol.querySelector("input");
                        if (idInput) idInput.value = row[lookupId] != null ? String(row[lookupId]) : "";
                        if (labelInput) labelInput.value = row[lookupDisplay] != null ? String(row[lookupDisplay]) : "";
                      } catch (e) {}
                      // Store selection na wrap pro Krok 5.I PATCH persistence
                      wrap._selectedValue = {
                        id: row[lookupId],
                        display: row[lookupDisplay],
                        rawRow: row,
                      };
                      console.info(
                        "[entity_picker]", field.name, "selected:",
                        row[lookupId], "(" + row[lookupDisplay] + ")"
                      );
                    },
                  });
                  _picker.open();
                } catch (e) {
                  alert("Picker selhal: " + (e.message || e));
                }
              });
            } else if (act === "unlink") {
              btn.addEventListener("click", function () {
                if (btn.disabled) return;
                // Clear fields lokálně (Krok 5.I: plus PATCH parent entity)
                try {
                  const idInput = idCol.querySelector("input");
                  const labelInput = labelCol.querySelector("input");
                  if (idInput) idInput.value = "";
                  if (labelInput) labelInput.value = "";
                } catch (e) {}
                wrap._selectedValue = null;
                console.info("[entity_picker]", field.name, "unlinked");
              });
            } else if (act === "create_new") {
              btn.addEventListener("click", function () {
                if (btn.disabled) return;
                alert(
                  "➕ Vytvořit nový '" + label + "' — Krok 5.I wizard.\n\n" +
                  "Picker pro create-new přijde po konzultaci s Marti-AI " +
                  "(potřebujeme řešit target table + minimální fields)."
                );
              });
            }
            actionsRow.appendChild(btn);
          });

          // Layout: actions row | fields row vedle sebe
          const innerRow = document.createElement("div");
          innerRow.style.cssText = "display:flex;gap:12px;align-items:flex-end;";
          innerRow.appendChild(actionsRow);
          innerRow.appendChild(fieldsRow);
          wrap.appendChild(innerRow);

          // Krok 5.H placeholder hint
          if (!dsCode) {
            const hint = document.createElement("div");
            hint.style.cssText =
              "font-size:11px;color:#d48787;font-style:italic;margin-top:6px;";
            hint.textContent = "⚠ data_source_id nenastaveno — picker bez dat.";
            wrap.appendChild(hint);
          }

          return wrap;
        }

        default:
          // Unknown comp_type → readonly fallback (don't crash, just show value as text)
          console.warn(
            "DesignFwForm: unknown comp_type '" + compType + "' for field '" +
            field.name + "' — falling back to readonly input."
          );
          return _field(label + " (?" + compType + ")", value, {
            fieldKey: fieldKey,
            readonly: true,
            onDirty: onDirty,
          });
      }
    }

    // Phase 38.4 Krok 14b+5 polish (13.5.2026 dopoledne): _setupFooter
    // ZRUSENO. Marti's request: "OK + Storno z templatu jsou v paticce
    // formu, tlacitko Zavrit smazat" — konsolidace UX. Template buttons
    // (footer panel components) jsou jedine close actions. _onDirty
    // graceful no-op pokud _saveBtn / _dirtyBadge null.
  }

  // ────────────────────────────────────────────────────────────────────
  // Phase 38.4 Krok 14c (13.5.2026 odpoledne): FieldPickerModal
  //
  // Marti-AI's "preview_html doctrine" + "palette as visual reference,
  // not interactive surface" (Claude's pojmenovani z dnes ~14:00):
  //
  // 1. Fetchne /api/v1/erp/design/comp-types (10 typu s preview_html)
  // 2. Fetchne /api/v1/erp/design/entity-columns/{entity_type}
  //    (columns z _FW_FORM_ENTITY_MAP + suggested_type_id per column)
  // 3. Render palette: per column → row s:
  //    - checkbox (multi-select)
  //    - column name + caption (label)
  //    - comp_type selector (default suggested, override dropdown)
  //    - iframe srcdoc s preview_html (sandbox isolation,
  //      Marti-AI's "gift, ne overhead")
  // 4. Submit → loop POST /design/comp-def per checked column
  // 5. Close + reload DesignFwForm to show new fields
  //
  // Trigger z DesignFwForm — pres button v main panel empty hint nebo
  // right-click. MVP: right-click pres _bindMainPanelTrigger.
  // ────────────────────────────────────────────────────────────────────

  class FieldPickerModal {
    constructor(opts) {
      this.opts = opts || {};
      // opts: { entityType: 'user', parentCompDefId: 2, onComplete: cb }
      this._shell = null;
      this._compTypes = [];       // [{id, code, label, kind, preview_html}]
      this._compTypesById = {};
      this._columns = [];         // [{name, caption_default, suggested_type_id, ...}]
      this._selected = new Set(); // column names checked
      this._typeOverrides = {};   // column.name -> type_id (override)
    }

    async open() {
      // Phase 38.4 Krok 14c+2 part A.2 (14.5.2026 odpoledne, Marti's
      // "musi se chovat jako normalni samostatne okno, ne modal"):
      //   floating=true → žádný overlay backdrop, lze proklikat přes ERP.
      //   Drop přes form panel funguje (HTML5 DnD nebyl blokován overlay
      //   pointer-events).
      // startPos: pravý horní roh viewport (drop target = DesignFwForm
      // pod modal, který je default v středu — Marti vidí form + drag
      // ze strany).
      this._shell = _buildModalShell({
        title: "🎨 Paleta komponent",
        width: "780px",
        hideDescToggle: true,
        floating: true,
        noBackdropClose: true,
        startPos: { top: "80px", left: "calc(100vw - 820px)" },
      });
      document.body.appendChild(this._shell.overlay);

      // Phase 38.4 Krok 14c+2 part B (14.5.2026 odpoledne, Marti's
      // "Drzi se stale vevnitr"): "Detach do okna" button v header.
      // Click → window.open() popup window, lze přesunout na druhý
      // monitor / kamkoliv mimo browser viewport. Cross-window drag-drop
      // funguje nativně (HTML5 DnD je cross-window pro same-origin).
      try {
        const headerActions = this._shell.header &&
          this._shell.header.querySelector(".erp-modal-header-actions");
        if (headerActions) {
          const detachBtn = document.createElement("button");
          detachBtn.type = "button";
          detachBtn.className = "erp-palette-detach";
          detachBtn.textContent = "🪟 Do okna";
          detachBtn.title = "Otevřít paletu v samostatném okně — lze přesunout na druhý monitor / mimo browser. Drag-drop do ERP funguje napříč okny.";
          detachBtn.style.cssText =
            "background:#1f2530;border:1px solid #2a3340;color:#cfd6df;" +
            "padding:4px 10px;border-radius:3px;cursor:pointer;font-size:11px;" +
            "margin-right:4px;";
          detachBtn.addEventListener("click", () => {
            // Open popup window — Marti vidí standalone gallery
            const popup = window.open(
              "/erp/palette-popup",
              "erp-palette-popup",
              "width=420,height=720,resizable=yes,scrollbars=yes,toolbar=no,menubar=no"
            );
            if (!popup) {
              _showToast("Popup blokován prohlížečem — povol popups pro tuto stránku", "error", 4000);
              return;
            }
            // Close parent modal — popup je teted primary palette
            // (Marti's intent: detach + use popup ve standalone režimu).
            // Pokud Marti chce obojí, ot evře +Pole znovu.
            popup.focus();
            _showToast("Paleta otevřena v okně. Drag z popup → drop na ERP form.", "success", 3500);
            this._shell.close();
          });
          // Insert pred closeBtn (poslední button v rightActions)
          const closeBtn = headerActions.querySelector("button:last-child");
          if (closeBtn) {
            headerActions.insertBefore(detachBtn, closeBtn);
          } else {
            headerActions.appendChild(detachBtn);
          }
        }
      } catch (e) {
        console.warn("[FieldPickerModal] detach button attach failed:", e);
      }

      // Body styling — same as DesignFwForm (flex column)
      if (this._shell.body) {
        this._shell.body.style.display = "flex";
        this._shell.body.style.flexDirection = "column";
        this._shell.body.style.padding = "12px 16px";
      }
      // Dialog explicit height pro layout stability
      if (this._shell.dialog) {
        this._shell.dialog.style.minHeight = "500px";
      }

      // Loading state
      const loading = document.createElement("div");
      loading.style.cssText = "padding:20px;text-align:center;color:#8a96a4;";
      loading.textContent = "Načítám paletu komponent…";
      this._shell.body.appendChild(loading);

      try {
        // Phase 38.4 Krok 14c+1 (14.5.2026 vecer): pridan parent_comp_def_id
        // query param. Backend pak vraci `existing_comp_def_id` per column,
        // ktery rozdeli sloupce do "available" / "already on form" tabs.
        const ecUrl = "/api/v1/erp/design/entity-columns/" +
                      encodeURIComponent(this.opts.entityType) +
                      (this.opts.parentCompDefId
                        ? "?parent_comp_def_id=" + encodeURIComponent(this.opts.parentCompDefId)
                        : "");
        // Parallel fetch — comp_types + entity_columns (s merge)
        const [ctResp, ecResp] = await Promise.all([
          fetch("/api/v1/erp/design/comp-types", { credentials: "include" }),
          fetch(ecUrl, { credentials: "include" }),
        ]);
        if (!ctResp.ok) throw new Error("comp-types HTTP " + ctResp.status);
        if (!ecResp.ok) throw new Error("entity-columns HTTP " + ecResp.status);
        const ctData = await ctResp.json();
        const ecData = await ecResp.json();
        if (!ctData.ok) throw new Error("comp-types: " + (ctData.error || "unknown"));
        if (!ecData.ok) throw new Error("entity-columns: " + (ecData.error || "unknown"));

        this._compTypes = ctData.items || [];
        this._compTypesById = {};
        for (const ct of this._compTypes) this._compTypesById[ct.id] = ct;
        this._columns = ecData.columns || [];

        // Phase 38.4 Krok 14c+1: rozdeleni do dvou kolekci podle existing
        this._columnsAvailable = this._columns.filter(
          c => c.existing_comp_def_id == null
        );
        this._columnsOnForm = this._columns.filter(
          c => c.existing_comp_def_id != null
        );
        // Active tab — default 'available' (kde user akce sedi)
        this._activeTab = "available";

        this._render();
      } catch (e) {
        loading.style.color = "#e88";
        loading.textContent = "Načítání selhalo: " + (e.message || e);
        console.error("[FieldPickerModal] load failed:", e);
      }
    }

    // Phase 38.4 Krok 14c+1: switch tab + re-render body
    _switchTab(tabKey) {
      if (this._activeTab === tabKey) return;
      this._activeTab = tabKey;
      this._render();
    }

    // Phase 38.4 Krok 14c+1: tab strip header (button per tab + counter
    // badge). Pattern z UI Kit ErpPageControl, ale inline pro modal (no
    // dependency, ne velka komponenta v jenom palette).
    _renderTabStrip() {
      const strip = document.createElement("div");
      strip.style.cssText =
        "display:flex;gap:2px;border-bottom:1px solid #2a3340;margin-bottom:10px;";

      // Phase 38.4 Krok 14f-C (14.5.2026 vecer, Marti's "Layout containers"
      // tab): paleta panel + groupbox pro drag-drop na formular. Marti's
      // choice A: rozsireni existing FieldPickerModal o novy tab (vs
      // samostatny PanelPickerModal).
      const tabs = [
        {
          key: "available",
          label: "Schází přidat",
          count: this._columnsAvailable.length,
          accent: "#5dbf5d",
        },
        {
          key: "onform",
          label: "Již na formě",
          count: this._columnsOnForm.length,
          accent: "#7ed4e8",
        },
        {
          key: "preview",
          label: "Preview",
          count: null,
          accent: "#d4b88a",
        },
        {
          key: "layout",
          label: "📐 Layout",
          count: null,
          accent: "#a88cd4",
        },
      ];

      for (const t of tabs) {
        const btn = document.createElement("button");
        btn.type = "button";
        const active = this._activeTab === t.key;
        const countStr = t.count != null ? " (" + t.count + ")" : "";
        btn.textContent = t.label + countStr;
        btn.style.cssText =
          "padding:6px 14px;background:" + (active ? "#1f2530" : "transparent") +
          ";border:1px solid " + (active ? "#3a4754" : "transparent") +
          ";border-bottom:" + (active
            ? "3px solid " + t.accent
            : "3px solid transparent") +
          ";color:" + (active ? t.accent : "#8a96a4") +
          ";cursor:pointer;font-size:12px;font-weight:" + (active ? "600" : "400") +
          ";border-radius:3px 3px 0 0;transition:color 0.15s;";
        btn.addEventListener("click", () => this._switchTab(t.key));
        btn.addEventListener("mouseenter", () => {
          if (!active) btn.style.color = "#cfd6df";
        });
        btn.addEventListener("mouseleave", () => {
          if (!active) btn.style.color = "#8a96a4";
        });
        strip.appendChild(btn);
      }
      return strip;
    }

    _render() {
      this._shell.body.innerHTML = "";

      // Phase 38.4 Krok 14c+1 (14.5.2026 vecer, Marti's "tabsheet pro
      // schazi/na forme/preview"): tab strip + tab content + footer.
      // Header counter agreguje cisla per tab.
      this._shell.body.appendChild(this._renderTabStrip());

      // Top hint (per tab)
      const hint = document.createElement("div");
      hint.style.cssText = "color:#8a96a4;font-size:12px;margin-bottom:10px;line-height:1.5;";
      if (this._activeTab === "available") {
        hint.innerHTML =
          "Klikni na řádek pro výběr / odznačení. Typ komponenty lze přepsat " +
          "pres dropdown vpravo. <b>" + this._columnsAvailable.length +
          "</b> sloupců zbývá přidat.";
      } else if (this._activeTab === "onform") {
        hint.innerHTML =
          "<b>" + this._columnsOnForm.length + "</b> polí už je na formě. " +
          "Klikni na ✕ vpravo pro odebrání (soft delete — komponenta zmizí " +
          "z formu, ale data v DB zůstanou).";
      } else if (this._activeTab === "preview") {
        hint.innerHTML =
          "Preview formuláře po insertu vybraných polí. " +
          "<span style=\"opacity:0.7;font-style:italic;\">(Phase 38.4 Krok 14c+2 — TODO)</span>";
      } else if (this._activeTab === "layout") {
        hint.innerHTML =
          "<b style=\"color:#a88cd4;\">📐 Layout containers</b> — strukturální komponenty (panel + groupbox). " +
          "Drag kartu na formulář → vytvořit novy container. Default panel align='client', " +
          "groupbox border_mode='top'. Změna parametrů pres right-click na panel/groupbox.";
      }
      this._shell.body.appendChild(hint);

      // Tab content container — scrollable list of rows
      const content = document.createElement("div");
      content.style.cssText =
        "flex:1 1 auto;overflow-y:auto;border:1px solid #2a3340;border-radius:4px;background:#0f141a;";
      this._shell.body.appendChild(content);

      // Render per active tab
      if (this._activeTab === "available") {
        if (this._columnsAvailable.length === 0) {
          const empty = document.createElement("div");
          empty.style.cssText = "padding:24px;text-align:center;color:#5dbf5d;font-size:13px;";
          empty.innerHTML = "✓ Všechny sloupce už jsou na formě. Není co přidat.";
          content.appendChild(empty);
        } else {
          for (const col of this._columnsAvailable) {
            content.appendChild(this._renderColumnRow(col));
          }
        }
      } else if (this._activeTab === "onform") {
        if (this._columnsOnForm.length === 0) {
          const empty = document.createElement("div");
          empty.style.cssText = "padding:24px;text-align:center;color:#8a96a4;font-size:13px;";
          empty.innerHTML = "Form je zatím prázdný — žádné pole.";
          content.appendChild(empty);
        } else {
          for (const col of this._columnsOnForm) {
            content.appendChild(this._renderOnFormRow(col));
          }
        }
      } else if (this._activeTab === "preview") {
        // Phase 38.4 Krok 14c+2 part A (14.5.2026 odpoledne po IT prezentaci):
        // Preview gallery — visual paleta dostupných komponent. Marti's "pro
        // relax" iteration. Per card: preview_html v iframe + label +
        // comp_type code (mono) + draggable=true (foundation pro Part B
        // drag-drop na DesignFwForm main panel).
        //
        // Filter: form-relevant typy (input, dropdown, memo, button, atd.) —
        // grid-only typy (grid_modern, grid_column, 7 column types) skip,
        // protoze nepouzitelne v form fields. Whitelist by renderer_hint
        // OR code prefix.
        const FORM_RELEVANT_HINTS = new Set([
          "input", "input-number", "textarea", "checkbox",
          "select", "multiselect", "datepicker", "datetimepicker",
          "timepicker", "button", "speedbutton",
          "fieldset",     // groupbox container
          "tabs_outer",   // pagecontrol container
          "tab_inner",    // tabsheet container
          "label",        // label / label_readonly
          "fileupload",   // file
          "md_render",    // markdown_view
        ]);
        const galleryItems = (this._compTypes || []).filter(ct =>
          FORM_RELEVANT_HINTS.has(ct.renderer_hint) ||
          ["label", "edit", "checkbox", "combobox", "memo", "number",
           "checkbox_modern", "date_modern", "datetime", "lookup",
           "lookup_multi", "file", "label_readonly", "groupbox",
           "pagecontrol", "tabsheet", "button", "richedit"].includes(ct.code)
        );

        // Hint
        const galleryHint = document.createElement("div");
        galleryHint.style.cssText =
          "padding:10px 14px;color:#8a96a4;font-size:11px;line-height:1.5;background:#141a20;border-bottom:1px solid #2a3340;";
        galleryHint.innerHTML =
          "<b style=\"color:#d4b88a;\">🎨 Paleta komponent</b> — " +
          galleryItems.length + " typů dostupných pro formuláře. " +
          "Klikni na kartu pro detail. <span style=\"opacity:0.7;font-style:italic;\">" +
          "(Drag-and-drop na formulář přijde v části B.)</span>";
        content.appendChild(galleryHint);

        // Gallery grid (3 columns auto-fit)
        const gallery = document.createElement("div");
        gallery.style.cssText =
          "padding:12px;display:grid;" +
          "grid-template-columns:repeat(auto-fill, minmax(220px, 1fr));" +
          "gap:12px;";
        content.appendChild(gallery);

        if (galleryItems.length === 0) {
          const empty = document.createElement("div");
          empty.style.cssText = "grid-column:1/-1;padding:24px;text-align:center;color:#8a96a4;";
          empty.innerHTML = "Žádné form-relevant komponenty s preview_html. " +
                            "UPDATE fw.comp_type SET preview_html=... pro form fields.";
          gallery.appendChild(empty);
        } else {
          for (const ct of galleryItems) {
            gallery.appendChild(this._renderGalleryCard(ct));
          }
        }
      } else if (this._activeTab === "layout") {
        // Phase 38.4 Krok 14f-C (14.5.2026 vecer, Marti's "Layout containers"
        // tab): paleta strukturalnich komponent (panel + groupbox).
        // Filter: kind='container'. Backend (Krok 14f-C fix) uz prefiltruje
        // status='active' — frontend dropnu redundantni check.
        const layoutItems = (this._compTypes || []).filter(ct =>
          ct.kind === "container"
        );

        // Gallery grid (2-3 columns wider cards pro layout types)
        const gallery = document.createElement("div");
        gallery.style.cssText =
          "padding:12px;display:grid;" +
          "grid-template-columns:repeat(auto-fill, minmax(260px, 1fr));" +
          "gap:12px;";
        content.appendChild(gallery);

        if (layoutItems.length === 0) {
          const empty = document.createElement("div");
          empty.style.cssText = "grid-column:1/-1;padding:24px;text-align:center;color:#8a96a4;";
          empty.innerHTML =
            "Žádné active container types. UPDATE fw.comp_type SET status='active' " +
            "pro panel (id=13) + groupbox (id=12).";
          gallery.appendChild(empty);
        } else {
          for (const ct of layoutItems) {
            gallery.appendChild(this._renderLayoutCard(ct));
          }
        }
      }

      // Footer bar — Selected count + actions
      const footer = document.createElement("div");
      footer.style.cssText =
        "margin-top:12px;display:flex;align-items:center;justify-content:flex-end;gap:16px;" +
        "border-top:1px solid #2a3340;padding-top:10px;";
      const counter = document.createElement("span");
      counter.id = "fpmCounter";
      counter.style.cssText = "color:#a8b4c2;font-size:12px;margin-right:auto;";
      counter.textContent = "Vybráno: " + this._selected.size;
      footer.appendChild(counter);

      // OK button visible jen na tab 'available' (akcni tab)
      if (this._activeTab === "available") {
        const okBtn = document.createElement("button");
        okBtn.type = "button";
        okBtn.style.cssText =
          "min-width:110px;padding:6px 16px;background:#3a5a8a;border:1px solid #4a7ba8;" +
          "border-radius:3px;color:#e8eef5;cursor:pointer;font-size:13px;font-weight:600;";
        okBtn.innerHTML = '<span style="color:#5dbf5d;font-weight:700;margin-right:6px;">✓</span>Přidat vybraná';
        okBtn.addEventListener("click", () => this._handleSubmit(okBtn));
        footer.appendChild(okBtn);
      }

      const cancelBtn = document.createElement("button");
      cancelBtn.type = "button";
      cancelBtn.style.cssText =
        "min-width:90px;padding:6px 16px;background:#2a3340;border:1px solid #3a4754;" +
        "border-radius:3px;color:#cfd6df;cursor:pointer;font-size:13px;";
      cancelBtn.innerHTML = this._activeTab === "available"
        ? '<span style="color:#d4888a;font-weight:700;margin-right:6px;">✗</span>Storno'
        : 'Zavřít';
      cancelBtn.addEventListener("click", () => this._shell.close());
      footer.appendChild(cancelBtn);

      this._shell.body.appendChild(footer);
    }

    // Phase 38.4 Krok 14c+1: render row v tabu "Již na formě".
    // Read-only display (name, caption, current type) + ✕ remove button.
    _renderOnFormRow(col) {
      const row = document.createElement("div");
      row.style.cssText =
        "display:grid;grid-template-columns:200px 1fr 140px 32px;" +
        "align-items:center;gap:10px;padding:8px 12px;border-bottom:1px solid #1a2028;" +
        "background:rgba(126,212,232,0.04);";

      // 1. Column name + caption
      const labelWrap = document.createElement("div");
      labelWrap.style.cssText = "display:flex;flex-direction:column;gap:2px;";
      const labelName = document.createElement("div");
      labelName.style.cssText = "font-family:ui-monospace,Consolas,monospace;font-size:11px;color:#9bb5d6;";
      labelName.textContent = col.name;
      const labelCap = document.createElement("div");
      labelCap.style.cssText = "font-size:13px;color:#e8eef5;";
      labelCap.textContent = col.existing_label || col.caption_default;
      labelWrap.appendChild(labelName);
      labelWrap.appendChild(labelCap);

      // 2. Region slot badge + comp_def id (info)
      const meta = document.createElement("div");
      meta.style.cssText = "color:#8a96a4;font-size:11px;";
      const ct = this._compTypesById[col.existing_type_id];
      meta.innerHTML =
        "<span style=\"background:#1f2530;padding:2px 6px;border-radius:3px;margin-right:6px;\">" +
        (col.existing_region_slot || "main") + "</span>" +
        (ct ? ct.label : "type#" + col.existing_type_id);

      // 3. Type label (current)
      const typeBadge = document.createElement("div");
      typeBadge.style.cssText = "font-size:11px;color:#7ed4e8;font-family:ui-monospace,Consolas,monospace;";
      typeBadge.textContent = "id=" + col.existing_comp_def_id;

      // 4. ✕ remove button
      const removeBtn = document.createElement("button");
      removeBtn.type = "button";
      removeBtn.textContent = "✕";
      removeBtn.title = "Odebrat pole z formuláře (soft delete — is_active=false)";
      removeBtn.style.cssText =
        "width:28px;height:28px;background:transparent;border:1px solid #3a4754;" +
        "color:#d4888a;cursor:pointer;border-radius:3px;font-size:14px;";
      removeBtn.addEventListener("mouseenter", () => {
        removeBtn.style.background = "#3a1f1f";
        removeBtn.style.borderColor = "#d4888a";
      });
      removeBtn.addEventListener("mouseleave", () => {
        removeBtn.style.background = "transparent";
        removeBtn.style.borderColor = "#3a4754";
      });
      removeBtn.addEventListener("click", async () => {
        const confirmed = await _confirmDarkDialog({
          title: "Odebrat pole '" + (col.existing_label || col.name) + "'?",
          message: "Pole zmizí z formuláře, ale data v DB zůstanou (soft delete is_active=false). Lze později vrátit.",
        });
        if (!confirmed) return;
        removeBtn.disabled = true;
        try {
          const r = await fetch("/api/v1/erp/design/comp-def/" + col.existing_comp_def_id, {
            method: "DELETE",
            credentials: "include",
          });
          if (!r.ok) {
            const errBody = await r.json().catch(() => ({}));
            throw new Error("HTTP " + r.status + ": " + (errBody.error || r.statusText));
          }
          _showToast("Pole odebráno", "success");
          // Move column z onForm → available + re-render
          col.existing_comp_def_id = null;
          col.existing_label = null;
          col.existing_region_slot = null;
          col.existing_type_id = null;
          this._columnsAvailable.push(col);
          this._columnsOnForm = this._columnsOnForm.filter(c => c !== col);
          this._render();
          // Parent form refresh — analog onComplete callback
          if (typeof this.opts.onComplete === "function") {
            try { this.opts.onComplete({ removed: 1 }); }
            catch (e) { console.error("[FieldPickerModal] onComplete failed:", e); }
          }
        } catch (e) {
          console.error("[FieldPickerModal] remove failed:", e);
          _showToast("Odebrání selhalo: " + (e.message || e), "error", 3500);
          removeBtn.disabled = false;
        }
      });

      row.appendChild(labelWrap);
      row.appendChild(meta);
      row.appendChild(typeBadge);
      row.appendChild(removeBtn);
      return row;
    }

    // Phase 38.4 Krok 14c+2 part A.1 (14.5.2026 odpoledne, Marti's
    // "obdelnicky jsou super, jen drag jen ta komponenta uvnitr, ne cela
    // karta"):
    //
    // Card je teted kontextový rámeček (label + id + meta — NE draggable).
    // Drag = pouze first interactive element preview_html (input / button /
    // select / atd.). Drag preview = real DOM komponenta, ne 220px karta —
    // víc "živé", Marti uvidi přesně co bude na formě.
    //
    // Iframe → inline DOM s scoped CSS (drag nepřechází přes iframe
    // boundary). Scope CSS reset v hlavní stylesheet bloku (řádek ~510).
    _renderGalleryCard(ct) {
      const card = document.createElement("div");
      card.style.cssText =
        "background:#141a20;border:1px solid #2a3340;border-radius:5px;" +
        "padding:10px;cursor:default;transition:border-color 0.15s;" +
        "display:flex;flex-direction:column;gap:8px;";
      card.dataset.compTypeId = String(ct.id);
      card.dataset.compTypeCode = ct.code;
      // Card NEMÁ draggable=true — drag je delegated na vnitřní komponentu.

      // Hover accent na CARD (visual feedback že se s tím dá interagovat)
      card.addEventListener("mouseenter", () => {
        card.style.borderColor = "#3a8aa8";
      });
      card.addEventListener("mouseleave", () => {
        card.style.borderColor = "#2a3340";
      });

      // 1. Preview INLINE (replace iframe). preview_html injected do
      // scope wrap, first child se stane draggable handle.
      const previewWrap = document.createElement("div");
      previewWrap.style.cssText =
        "background:#1f2530;border-radius:3px;padding:6px;" +
        "min-height:42px;display:flex;align-items:center;justify-content:center;" +
        "overflow:hidden;";
      const previewScope = document.createElement("div");
      previewScope.className = "erp-gallery-preview-scope";
      previewScope.innerHTML = ct.preview_html ||
        "<span style=\"color:#8a96a4;font-size:11px;\">(no preview)</span>";

      // Phase 38.4 Krok 14c+3.5 (14.5.2026 odpoledne, Marti's bug "drag
      // funguje jen Lookup/LookupMulti/Checkbox/Label"):
      //
      // PATTERN ROOT CAUSE:
      //   Funguje:    <select>, <label>  → container elementy bez vlastní
      //               interaction model
      //   Nefunguje:  <input>, <button>, <textarea> → mají vlastní pointer
      //               behavior co interferuje s HTML5 DnD v Chrome:
      //                 <input readonly>: text-select claims drag space
      //                 <button>: pointer event model nefire dragstart
      //                 <textarea>: text-select + scrollable same issue
      //
      // FIX: wrapper div approach — divs jsou universal drag handles.
      //   Pro input/button/textarea: wrapnout do <div draggable=true>,
      //   inner element + pointer-events:none (no interaction passing).
      //   Pro select/label: direct draggable (osvědčené pro 4 working
      //   komponenty Lookup/LookupMulti/Checkbox/Label).
      const innerEl = previewScope.querySelector(
        "input, select, textarea, button, label"
      ) || previewScope.firstElementChild;

      let dragHandle = null;
      if (innerEl) {
        const tag = innerEl.tagName;
        const needsWrapper = tag === "INPUT" || tag === "BUTTON" || tag === "TEXTAREA";

        if (needsWrapper) {
          // Wrap input/button/textarea v div pro clean drag init.
          // Inner element pointer-events:none — no click/select interfere.
          const wrapperDiv = document.createElement("div");
          wrapperDiv.style.cssText =
            "display:inline-block;cursor:grab;line-height:0;";
          innerEl.parentNode.insertBefore(wrapperDiv, innerEl);
          wrapperDiv.appendChild(innerEl);
          innerEl.style.pointerEvents = "none";
          if (tag === "INPUT" || tag === "TEXTAREA") {
            innerEl.setAttribute("readonly", "");
          }
          dragHandle = wrapperDiv;
        } else {
          // <select> / <label> / fallback firstElementChild: direct draggable
          dragHandle = innerEl;
          if (tag === "SELECT") {
            dragHandle.style.pointerEvents = "auto";
          }
        }
      }

      if (dragHandle) {
        dragHandle.setAttribute("draggable", "true");
        dragHandle.style.cursor = "grab";
        // Phase 38.4 Krok 14c+3.5: mousedown preventDefault není potřeba
        // (wrapper div approach pro input/button/textarea + native drag pro
        // select/label — žádný text-select interference).
        dragHandle.addEventListener("dragstart", (ev) => {
          ev.stopPropagation();
          dragHandle.style.opacity = "0.5";
          dragHandle.style.cursor = "grabbing";
          ev.dataTransfer.effectAllowed = "copy";
          ev.dataTransfer.setData(
            "application/x-erp-comp-type",
            JSON.stringify({ id: ct.id, code: ct.code, label: ct.label })
          );
          ev.dataTransfer.setData("text/plain", ct.code);
        });
        dragHandle.addEventListener("dragend", () => {
          dragHandle.style.opacity = "1";
          dragHandle.style.cursor = "grab";
        });
      }

      previewWrap.appendChild(previewScope);
      card.appendChild(previewWrap);

      // 2. Label (human-readable)
      const lbl = document.createElement("div");
      lbl.style.cssText = "font-size:13px;color:#e8eef5;font-weight:600;";
      lbl.textContent = ct.label;
      card.appendChild(lbl);

      // 3. Comp type code + id (mono, subtle)
      const code = document.createElement("div");
      code.style.cssText =
        "font-family:ui-monospace,Consolas,monospace;font-size:10px;" +
        "color:#7ed4e8;opacity:0.7;";
      code.textContent = ct.code + " · id=" + ct.id;
      card.appendChild(code);

      // 4. Footer (kind badge + description short)
      const meta = document.createElement("div");
      meta.style.cssText =
        "font-size:10px;color:#8a96a4;line-height:1.3;" +
        "border-top:1px solid #1a2028;padding-top:6px;margin-top:auto;";
      const kindBadge =
        "<span style=\"background:#1f2530;padding:1px 5px;border-radius:2px;margin-right:4px;\">" +
        (ct.kind || "leaf") + "</span>";
      meta.innerHTML = kindBadge + (ct.description || "").slice(0, 60);
      card.appendChild(meta);

      // Click na card (mimo dragHandle) → toast hint pro discoverability
      card.addEventListener("click", (ev) => {
        // Skip pokud klik na drag handle (komponenta uvnitř)
        if (dragHandle && (ev.target === dragHandle || dragHandle.contains(ev.target))) {
          return;
        }
        _showToast(
          ct.label + " (" + ct.code + ") — drag tu komponentu nahoře na formulář",
          "info",
          2200
        );
      });

      return card;
    }

    // ════════════════════════════════════════════════════════════════
    // Phase 38.4 Krok 14f-C (14.5.2026 vecer, Marti's "Layout containers"
    // tab): render karta pro container type (panel/groupbox).
    // Analog _renderGalleryCard ale s container-specific:
    //   - Visual: large emoji/icon (📦 panel, ▦ groupbox)
    //   - Description: align (panel) / border (groupbox) hints
    //   - Draggable=true s payload {id, code, label, layout: default}
    //   - Drop pipeline → DesignFwForm._attachDropTargetForGalleryDrag
    //     receives layout in payload, POST /design/comp-def s layout JSONB
    // ════════════════════════════════════════════════════════════════
    _renderLayoutCard(ct) {
      const card = document.createElement("div");
      card.style.cssText =
        "background:#0f141a;border:1px solid #2a3340;border-radius:6px;" +
        "padding:14px;display:flex;flex-direction:column;gap:8px;" +
        "transition:border-color 0.15s, transform 0.15s;" +
        "position:relative;";
      card.addEventListener("mouseenter", () => {
        card.style.borderColor = "#a88cd4";
      });
      card.addEventListener("mouseleave", () => {
        card.style.borderColor = "#2a3340";
      });

      // Per-type icon + visual hint
      const isPanel = ct.code === "panel";
      const isGroupbox = ct.code === "groupbox";
      const icon = isPanel ? "📦" : (isGroupbox ? "▦" : "▣");
      const accentColor = isPanel ? "#a88cd4" : "#d4b88a";

      // Default layout pro drag payload (drop pipeline pouzije pro POST body)
      let defaultLayout;
      if (isPanel) {
        defaultLayout = { align: "client" };
      } else if (isGroupbox) {
        defaultLayout = { border_mode: "top", label: null };
      } else {
        defaultLayout = {};
      }

      // 1. Icon + visual hint
      const visualWrap = document.createElement("div");
      visualWrap.style.cssText =
        "padding:12px;background:#141a20;border:1px dashed " + accentColor + ";" +
        "border-radius:4px;display:flex;align-items:center;justify-content:center;" +
        "gap:8px;min-height:60px;cursor:grab;";
      visualWrap.setAttribute("draggable", "true");

      const iconEl = document.createElement("span");
      iconEl.textContent = icon;
      iconEl.style.cssText = "font-size:28px;line-height:1;";
      visualWrap.appendChild(iconEl);

      const iconLabel = document.createElement("span");
      iconLabel.textContent = ct.label;
      iconLabel.style.cssText = "font-size:14px;color:" + accentColor + ";font-weight:600;";
      visualWrap.appendChild(iconLabel);

      visualWrap.addEventListener("dragstart", (ev) => {
        ev.stopPropagation();
        visualWrap.style.opacity = "0.5";
        visualWrap.style.cursor = "grabbing";
        ev.dataTransfer.effectAllowed = "copy";
        // Phase 38.4 Krok 14f-C: payload obsahuje layout (default per code)
        // — DesignFwForm drop handler ho posila do POST body.
        ev.dataTransfer.setData(
          "application/x-erp-comp-type",
          JSON.stringify({
            id: ct.id,
            code: ct.code,
            label: ct.label,
            layout: defaultLayout,  // novy klic — backend pass-through
            is_container: true,
          })
        );
        ev.dataTransfer.setData("text/plain", ct.code);
      });
      visualWrap.addEventListener("dragend", () => {
        visualWrap.style.opacity = "1";
        visualWrap.style.cursor = "grab";
      });

      card.appendChild(visualWrap);

      // 2. Label (human-readable)
      const lbl = document.createElement("div");
      lbl.style.cssText = "font-size:13px;color:#e8eef5;font-weight:600;";
      lbl.textContent = ct.label;
      card.appendChild(lbl);

      // 3. Code + id (mono)
      const code = document.createElement("div");
      code.style.cssText =
        "font-family:ui-monospace,Consolas,monospace;font-size:10px;" +
        "color:" + accentColor + ";opacity:0.7;";
      code.textContent = ct.code + " · id=" + ct.id;
      card.appendChild(code);

      // 4. Default behavior hint (per-type)
      const meta = document.createElement("div");
      meta.style.cssText =
        "font-size:10px;color:#8a96a4;line-height:1.4;" +
        "border-top:1px solid #1a2028;padding-top:6px;margin-top:auto;";
      let hint;
      if (isPanel) {
        hint = "Strukturální container (alClient default). " +
               "Right-click pro nastavení align/width/height.";
      } else if (isGroupbox) {
        hint = "Vizuální wrapper s linkou nahoře (default). " +
               "Optional label. Drag dovnitř panelu.";
      } else {
        hint = ct.description || "Container component.";
      }
      meta.innerHTML = '<span style="background:#1f2530;padding:1px 5px;border-radius:2px;margin-right:4px;">container</span>' + hint;
      card.appendChild(meta);

      // Click na card → toast (discoverability)
      card.addEventListener("click", (ev) => {
        if (visualWrap.contains(ev.target)) return;
        _showToast(
          ct.label + " (" + ct.code + ") — drag ikonu nahoře na formulář",
          "info",
          2200
        );
      });

      return card;
    }

    _renderColumnRow(col) {
      const row = document.createElement("div");
      row.style.cssText =
        "display:grid;grid-template-columns:24px 200px 1fr 160px;" +
        "align-items:center;gap:10px;padding:8px 12px;border-bottom:1px solid #1a2028;" +
        "cursor:pointer;transition:background 0.1s;";
      row.addEventListener("mouseenter", () => row.style.background = "#141a20");
      row.addEventListener("mouseleave", () => {
        row.style.background = this._selected.has(col.name) ? "#1a2530" : "transparent";
      });

      // 1. Checkbox
      const cb = document.createElement("input");
      cb.type = "checkbox";
      cb.style.cssText = "width:16px;height:16px;cursor:pointer;";
      cb.addEventListener("change", () => {
        if (cb.checked) this._selected.add(col.name);
        else this._selected.delete(col.name);
        row.style.background = cb.checked ? "#1a2530" : "transparent";
        this._updateCounter();
      });

      // 2. Column name + caption
      const labelWrap = document.createElement("div");
      labelWrap.style.cssText = "display:flex;flex-direction:column;gap:2px;";
      const labelName = document.createElement("div");
      labelName.style.cssText = "font-family:ui-monospace,Consolas,monospace;font-size:11px;color:#9bb5d6;";
      labelName.textContent = col.name;
      const labelCap = document.createElement("div");
      labelCap.style.cssText = "font-size:13px;color:#e8eef5;";
      labelCap.textContent = col.caption_default;
      labelWrap.appendChild(labelName);
      labelWrap.appendChild(labelCap);

      // 3. Preview (iframe srcdoc — Marti-AI's "sandbox isolation is gift")
      const previewWrap = document.createElement("div");
      previewWrap.style.cssText = "min-height:36px;display:flex;align-items:center;";
      const initialTypeId = this._typeOverrides[col.name] || col.suggested_type_id;
      const initialCt = this._compTypesById[initialTypeId];
      const iframe = this._buildPreviewIframe(initialCt);
      previewWrap.appendChild(iframe);

      // 4. Type override dropdown
      const typeSel = document.createElement("select");
      typeSel.style.cssText =
        "padding:4px 8px;background:#1f2530;border:1px solid #2a3340;color:#cfd6df;" +
        "border-radius:3px;font-size:12px;cursor:pointer;";
      for (const ct of this._compTypes) {
        const opt = document.createElement("option");
        opt.value = String(ct.id);
        opt.textContent = ct.label + " (id=" + ct.id + ")";
        if (ct.id === initialTypeId) opt.selected = true;
        typeSel.appendChild(opt);
      }
      typeSel.addEventListener("change", () => {
        const newId = parseInt(typeSel.value, 10);
        this._typeOverrides[col.name] = newId;
        // Re-render preview iframe
        previewWrap.innerHTML = "";
        const newIframe = this._buildPreviewIframe(this._compTypesById[newId]);
        previewWrap.appendChild(newIframe);
      });

      // Row click toggle (except direct interaction with cb/typeSel)
      row.addEventListener("click", (ev) => {
        if (ev.target === cb || ev.target === typeSel ||
            typeSel.contains(ev.target) || iframe.contains(ev.target)) return;
        cb.checked = !cb.checked;
        cb.dispatchEvent(new Event("change"));
      });

      row.appendChild(cb);
      row.appendChild(labelWrap);
      row.appendChild(previewWrap);
      row.appendChild(typeSel);
      return row;
    }

    _buildPreviewIframe(compType) {
      const iframe = document.createElement("iframe");
      // iframe srcdoc — sandbox isolation (Marti-AI's "gift")
      // Default theme styling pro consistent look napříč all comp_types
      const srcdoc =
        '<!DOCTYPE html><html><head><style>' +
        'body{margin:0;padding:4px 6px;background:transparent;' +
        'font-family:system-ui,-apple-system,sans-serif;font-size:12px;color:#cfd6df;}' +
        'input,select,textarea,button{font-family:inherit;font-size:12px;' +
        'background:#1f2530;border:1px solid #2a3340;color:#cfd6df;border-radius:3px;' +
        'padding:3px 6px;width:auto;max-width:100%;}' +
        'input[type="checkbox"]{width:14px;height:14px;}' +
        'label{display:flex;align-items:center;gap:5px;}' +
        '</style></head><body>' +
        (compType && compType.preview_html ? compType.preview_html : '<span style="color:#8a96a4">(no preview)</span>') +
        '</body></html>';
      iframe.srcdoc = srcdoc;
      iframe.style.cssText =
        "width:100%;height:36px;border:none;background:transparent;" +
        "pointer-events:none;"; // Decorative only — Marti-AI's doctrine
      iframe.setAttribute("sandbox", "allow-same-origin");
      return iframe;
    }

    _updateCounter() {
      const counter = this._shell.body.querySelector("#fpmCounter");
      if (counter) counter.textContent = "Vybráno: " + this._selected.size;
    }

    async _handleSubmit(btnEl) {
      if (this._selected.size === 0) {
        alert("Vyber alespoň 1 pole z palety.");
        return;
      }

      const origHtml = btnEl.innerHTML;
      btnEl.disabled = true;
      btnEl.innerHTML = "⏳ Ukládám…";

      const parentId = this.opts.parentCompDefId;
      const results = { ok: [], failed: [], existing: [] };

      // Sequential POST per column (parallel by způsobit FK race conditions)
      for (const colName of this._selected) {
        const col = this._columns.find(c => c.name === colName);
        if (!col) continue;
        const typeId = this._typeOverrides[colName] || col.suggested_type_id;
        try {
          const r = await fetch("/api/v1/erp/design/comp-def", {
            method: "POST",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              parent_comp_def_id: parentId,
              name: colName,
              caption: col.caption_default,
              type_id: typeId,
              region_slot: "main",
            }),
          });
          const d = await r.json();
          if (r.ok && d.ok) {
            if (d.existing) results.existing.push(colName);
            else results.ok.push(colName);
          } else {
            results.failed.push({ name: colName, error: d.error || "HTTP " + r.status });
          }
        } catch (e) {
          results.failed.push({ name: colName, error: e.message || String(e) });
        }
      }

      // Report results
      const okCount = results.ok.length;
      const existingCount = results.existing.length;
      const failedCount = results.failed.length;
      if (failedCount > 0) {
        const errLines = results.failed.map(f => "• " + f.name + ": " + f.error).join("\\n");
        alert(
          "Přidáno: " + okCount + ", už existovalo: " + existingCount + ", chyby: " + failedCount + "\\n\\n" +
          errLines
        );
        btnEl.disabled = false;
        btnEl.innerHTML = origHtml;
        return;
      }

      // Phase 38.4 Krok 14c+1: po success NEzavirat modal. Misto toho
      // refresh state z backendu + switch na "Na forme" tab — Marti
      // okamzite vidi pridana pole + muze pokracovat (further add /
      // remove / Preview). Modal je teted live form editor.
      btnEl.style.background = "#3a7a3a";
      btnEl.innerHTML = "✅ Přidáno (" + (okCount + existingCount) + ")";

      try {
        await this._refreshState();
        this._selected.clear();
        this._typeOverrides = {};
        this._activeTab = "onform"; // switch na vysledek
        // _render pretvori cely modal vc. footeru — toast oznamuje
        // success pro discoverability
        _showToast(
          "Přidáno: " + okCount + (existingCount > 0 ? ", existovalo: " + existingCount : ""),
          "success"
        );
        this._render();
      } catch (e) {
        console.error("[FieldPickerModal] refresh after submit failed:", e);
        // Fallback: stale close
        btnEl.disabled = false;
        btnEl.innerHTML = origHtml;
      }

      // Parent form refresh — analog DELETE flow
      if (typeof this.opts.onComplete === "function") {
        try { this.opts.onComplete({ added: okCount, existing: existingCount }); }
        catch (e) { console.error("[FieldPickerModal] onComplete failed:", e); }
      }
    }

    // Phase 38.4 Krok 14c+1: re-fetch entity-columns s mergem existing
    // comp_def (po POST/DELETE). Updatuje _columns / _columnsAvailable /
    // _columnsOnForm in-place — caller pak vola _render().
    async _refreshState() {
      const ecUrl = "/api/v1/erp/design/entity-columns/" +
                    encodeURIComponent(this.opts.entityType) +
                    (this.opts.parentCompDefId
                      ? "?parent_comp_def_id=" + encodeURIComponent(this.opts.parentCompDefId)
                      : "");
      const r = await fetch(ecUrl, { credentials: "include" });
      if (!r.ok) throw new Error("entity-columns refresh HTTP " + r.status);
      const d = await r.json();
      if (!d.ok) throw new Error("entity-columns refresh: " + (d.error || "unknown"));
      this._columns = d.columns || [];
      this._columnsAvailable = this._columns.filter(c => c.existing_comp_def_id == null);
      this._columnsOnForm = this._columns.filter(c => c.existing_comp_def_id != null);
    }
  }

  // ────────────────────────────────────────────────────────────────────
  // Export
  // ────────────────────────────────────────────────────────────────────

  global.DesignSoudecekCoreForm = DesignSoudecekCoreForm;
  global.DesignJadroRadekForm = DesignJadroRadekForm;
  global.DesignFwForm = DesignFwForm;
  global.FieldPickerModal = FieldPickerModal;

})(window);
