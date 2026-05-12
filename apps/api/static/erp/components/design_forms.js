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

  function _confirmDarkDialog(opts) {
    opts = opts || {};
    const title = opts.title || "Potvrdit";
    const message = opts.message || "";
    const okLabel = opts.ok || "OK";
    const cancelLabel = opts.cancel || "Zrušit";
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
      hdr.style.cssText = "padding:12px 16px;border-bottom:1px solid #2a3340;background:#141a20;font-size:14px;font-weight:600;color:#e8eef5;";
      hdr.textContent = title;
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
        ftr.appendChild(cancelBtn);
        ftr.appendChild(noBtn);
        ftr.appendChild(yesBtn);
        dlg.appendChild(ftr);
        ovr.appendChild(dlg);
        document.body.appendChild(ovr);
        function cleanup() {
          try { ovr.parentNode && ovr.parentNode.removeChild(ovr); } catch (e) {}
          document.removeEventListener("keydown", onKey);
        }
        function onKey(ev) {
          if (ev.key === "Escape") { cleanup(); resolve("cancel"); }
          else if (ev.key === "Enter") { cleanup(); resolve("yes"); }
        }
        yesBtn.addEventListener("click", () => { cleanup(); resolve("yes"); });
        noBtn.addEventListener("click", () => { cleanup(); resolve("no"); });
        cancelBtn.addEventListener("click", () => { cleanup(); resolve("cancel"); });
        ovr.addEventListener("click", (ev) => {
          if (ev.target === ovr) { cleanup(); resolve("cancel"); }
        });
        dlg.addEventListener("contextmenu", (ev) => ev.preventDefault());
        document.addEventListener("keydown", onKey);
        setTimeout(() => yesBtn.focus(), 50);
        return;
      }

      // 2-button (default): OK / Cancel
      const cancelBtn = document.createElement("button");
      cancelBtn.type = "button";
      cancelBtn.textContent = cancelLabel;
      cancelBtn.style.cssText = "padding:6px 16px;background:#2a3340;border:1px solid #3a4754;border-radius:3px;color:#cfd6df;cursor:pointer;font-size:12px;";

      const okBtn = document.createElement("button");
      okBtn.type = "button";
      okBtn.textContent = okLabel;
      okBtn.style.cssText = "padding:6px 16px;background:#5a3a3a;border:1px solid #7a4a4a;border-radius:3px;color:#e8eef5;cursor:pointer;font-size:12px;font-weight:600;";

      ftr.appendChild(cancelBtn);
      ftr.appendChild(okBtn);
      dlg.appendChild(ftr);
      ovr.appendChild(dlg);
      document.body.appendChild(ovr);

      function cleanup() {
        try { ovr.parentNode && ovr.parentNode.removeChild(ovr); } catch (e) {}
        document.removeEventListener("keydown", onKey);
      }
      function onKey(ev) {
        if (ev.key === "Escape") { cleanup(); resolve(false); }
        else if (ev.key === "Enter") { cleanup(); resolve(true); }
      }
      cancelBtn.addEventListener("click", () => { cleanup(); resolve(false); });
      okBtn.addEventListener("click", () => { cleanup(); resolve(true); });
      ovr.addEventListener("click", (ev) => {
        if (ev.target === ovr) { cleanup(); resolve(false); }
      });
      dlg.addEventListener("contextmenu", (ev) => ev.preventDefault());
      document.addEventListener("keydown", onKey);
      setTimeout(() => okBtn.focus(), 50);
    });
  }

  // ────────────────────────────────────────────────────────────────────
  // Shared modal skeleton (reuse modal CSS z erp-modal patternu)
  // ────────────────────────────────────────────────────────────────────

  function _buildModalShell(opts) {
    // Returns { overlay, dialog, header, body, footer, close() }
    const overlay = document.createElement("div");
    overlay.className = "erp-modal-overlay";
    overlay.style.cssText = "position:fixed;inset:0;background:rgba(0,0,0,0.6);z-index:9000;display:flex;align-items:center;justify-content:center;";

    const dialog = document.createElement("div");
    dialog.className = "erp-modal-dialog erp-design-modal";
    dialog.style.cssText = "background:#1a1f26;border:1px solid #2a3340;border-radius:6px;width:" + (opts.width || "920px") + ";max-width:95vw;max-height:90vh;display:flex;flex-direction:column;color:#cfd6df;font-size:13px;box-shadow:0 12px 40px rgba(0,0,0,0.5);resize:both;overflow:hidden;";

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
      sysToggle.textContent = on ? "👁️ system" : "👁️ uživatel";
      sysToggle.title = on
        ? "Zobrazují se system fieldKey. Klikni pro přepnutí na uživatelské názvy."
        : "Zobrazují se uživatelské názvy. Klikni pro přepnutí na system fieldKey (debug).";
      sysToggle.style.cssText = "background:" + (on ? "#3a4a5a" : "#1f2530") +
        ";border:1px solid " + (on ? "#5a6877" : "#2a3340") +
        ";color:#cfd6df;padding:4px 10px;border-radius:3px;cursor:pointer;font-size:11px;";
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
    descToggle.textContent = "📖";
    descToggle.title = "Otevřít popis core (systémový + uživatelský — jako CLAUDE.md pro tohle jádro).";
    descToggle.style.cssText = "background:#1f2530;border:1px solid #2a3340;color:#cfd6df;padding:4px 8px;border-radius:3px;cursor:pointer;font-size:13px;line-height:1;";
    descToggle.addEventListener("click", () => {
      if (typeof opts.onShowDescriptions === "function") {
        try { opts.onShowDescriptions(); }
        catch (e) { console.error("onShowDescriptions failed:", e); }
      } else {
        console.warn("📖 clicked but form did not register onShowDescriptions handler");
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
    const titleText = "📖 Popis: " + labelStr;

    // Popup nepouziva beforeClose handler — dirty tracking je v hlavnim
    // formu (memo nas vola onDirty primo). Close = vzdy povoleno, data
    // zustanou v form's state.
    const shell = _buildModalShell({
      title: titleText,
      width: "1100px",
      hideDescToggle: true,
    });
    document.body.appendChild(shell.overlay);

    // Body — vertikalni flex, 2 memos vedle sebe via CSS toggle.
    // Memo full-width, full-height (60vh).
    shell.body.style.padding = "0";
    shell.body.style.display = "flex";
    shell.body.style.flexDirection = "column";

    const info = document.createElement("div");
    info.style.cssText = "padding:10px 16px;background:#141a20;border-bottom:1px solid #2a3340;color:#8a96a4;font-size:11px;line-height:1.5;";
    info.innerHTML =
      "<span class=\"section-title-user\">👁️ Uživatelský popis — k čemu jádro slouží, jak s ním pracovat. Markdown.</span>" +
      "<span class=\"section-title-system\">🔧 Systémový popis (vývojáři) — implementace, data zdroje, edge cases, debug. Markdown.</span>" +
      "<br><span style=\"font-size:10px;opacity:0.7;\">Přepnout pomocí ikony 👁️ uživatel / system v hlavičce. Je to jako CLAUDE.md pro tohle jádro.</span>";
    shell.body.appendChild(info);

    // Memo container — fills body, 60vh height
    const memoContainer = document.createElement("div");
    memoContainer.style.cssText = "padding:12px 16px;flex:1 1 auto;display:flex;flex-direction:column;min-height:0;";
    shell.body.appendChild(memoContainer);

    // User memo
    const userWrap = _memo("Popis (uživatel)", opts.descUser, {
      fieldKey: entityKind + ".description_user",
      onDirty: opts.onDirty,
      rows: 22,
      maxRows: 40,
    });
    userWrap.classList.add("desc-memo-user");
    userWrap.classList.add("design-desc-popup-memo");
    userWrap.style.flex = "1 1 auto";
    userWrap.style.minHeight = "0";
    userWrap.style.display = "flex";
    userWrap.style.flexDirection = "column";
    memoContainer.appendChild(userWrap);

    // System memo
    const sysWrap = _memo("Popis (systém — vývojáři)", opts.descSystem, {
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

    // Stretch memo textareas to fill memoContainer
    function _stretchMemo(wrap) {
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
      if (!displayValue && inp.input) {
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
        inp.input.style.cursor = "not-allowed";
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
        memo.textarea.style.cursor = "not-allowed";
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

      ftr.appendChild(clearBtn);
      ftr.appendChild(cancelBtn);
      ftr.appendChild(okBtn);
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
        dd.trigger.style.cursor = "not-allowed";
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
      // opts.initialTab = 'soudecek' (default) | 'prehled'
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
        this._dirtyBadge.textContent = count > 0
          ? "● " + count + " změna" + (count > 1 ? (count < 5 ? "y" : "") : "")
          : "";
        this._dirtyBadge.style.display = count > 0 ? "" : "none";
      }
    }

    _onSaveClick() {
      // Krok 14b backend save flow chybi — placeholder alert
      const fields = Array.from(this._dirty).join(", ");
      alert(
        "Save flow přijde v Kroku 14b (backend POST endpointy).\n\n" +
        "Změněná pole (zatím nejsou ukládána):\n" + fields
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
      let entityKind, entityLabel, descUser, descSystem;
      if (activeId === "prehled" && data.core && data.core.id) {
        entityKind = "core";
        entityLabel = data.core.label || data.core.code || "(bez labelu)";
        descUser = data.core.description_user;
        descSystem = data.core.description_system;
      } else {
        // Default: Soudecek tab / menu_node
        const mn = data.menu_node || {};
        entityKind = "menu_node";
        entityLabel = mn.label || mn.code || "(bez labelu)";
        descUser = mn.description_user;
        descSystem = mn.description_system;
      }
      _buildDescriptionsPopup({
        entityKind: entityKind,
        entityLabel: entityLabel,
        descUser: descUser,
        descSystem: descSystem,
        onDirty: this._onDirty.bind(this),
      });
    }

    // Phase 38.4 Krok 14a-A1k #4: před zavřením oken pres ✕ se zeptej,
    // pokud jsou neuložené změny. Dark design, 3 tlačítka.
    async _beforeCloseHandler() {
      if (!this._dirty || this._dirty.size === 0) return "close";
      const count = this._dirty.size;
      const fields = Array.from(this._dirty).join(", ");
      // A1p: Czech grammar — adjektivum + noun spolu (1 = provedenou změnu,
      // 2-4 = provedené změny, 5+ = provedených změn).
      const phrase = count > 1
        ? (count < 5 ? "provedené změny" : "provedených změn")
        : "provedenou změnu";
      const decision = await _confirmDarkDialog({
        title: "Neuložené změny",
        message: "Mám uložit tebou " + phrase + "? (" + count + ")\n\nPole: " + fields,
        threeButtons: true,
        yes: "Ano",
        no: "Ne",
        cancel: "Zrušit",
      });
      if (decision === "cancel") return "cancel";
      if (decision === "yes") {
        this._onSaveClick();
        return "save";
      }
      return "close"; // "no" — zavřít bez uložení
    }

    _onRevertClick() {
      // Phase 38.4 Krok 14a-A1f #4: klik na dirty badge — confirm + revert.
      // Krok 14a-A1g #2 (12.5.2026 odpoledne): nahrazujeme native confirm()
      // za dark centered dialog (Marti's polish — UX konzistence).
      if (!this._dirty.size) return;
      const count = this._dirty.size;
      const fields = Array.from(this._dirty).join(", ");
      _confirmDarkDialog({
        title: "Vrátit změny?",
        message: "Vrátit " + count + " změn" + (count > 1 ? (count < 5 ? "y" : "") : "") +
          " do původního stavu?\n\nPole: " + fields,
        ok: "Vrátit",
        cancel: "Zrušit",
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
      const initialTab = this.opts.initialTab === "prehled" ? "prehled" : "soudecek";
      // Sjednoceny title napric obema akcemi (tree akce 1 + grid akce 2) —
      // form je stejny, jen jiny default tab. Uzivatel vidi scope (soudecek + core).
      const title = "Design: Soudeček + Core přehledu";

      this._shell = _buildModalShell({
        title: title,
        width: "920px",
        beforeClose: () => this._beforeCloseHandler(),
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
          { id: "soudecek", label: "Soudeček", content: soudecekDiv },
          { id: "prehled", label: "Přehled (Core)", content: prehledDiv },
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
      const root = document.createElement("div");
      root.className = "erp-design-tab-prehled";
      const core = (this._data && this._data.core) || null;
      if (!core || !core.id) {
        const empty = document.createElement("div");
        empty.style.cssText = "padding:20px;color:#8a96a4;font-style:italic;";
        empty.textContent = "Tento soudeček nemá Core přehledu (menu_node.core_id IS NULL). Folder / iframe / special — nezná list view.";
        root.appendChild(empty);
        return root;
      }

      // Dirty tracking closures (sdilene s _buildSoudecekTab — modal-level)
      const D = this._onDirty.bind(this);
      const _f = (l, v, key, o) => _field(l, v, Object.assign({fieldKey: key, onDirty: D}, o || {}));
      const _d = (l, v, items, key, o) => _dropdown(l, v, items, Object.assign({fieldKey: key, onDirty: D}, o || {}));

      // Section: Core identita — ID/version/parent_framework_id readonly,
      // layout_type je enum dropdown, ostatni editable.
      // Krok 14a-A1m #1: section title pair.
      const idSec = _sectionBuild("Identifikace Core", "fw.core — identita + layout + version");
      idSec.grid.appendChild(_f("ID (core.id)", core.id, "core.id", { mono: true, readonly: true }));
      idSec.grid.appendChild(_f("Code", core.code, "core.code", { mono: true }));
      idSec.grid.appendChild(_f("Label", core.label, "core.label"));
      idSec.grid.appendChild(_d("Layout type", core.layout_type, "layout_type", "core.layout_type"));
      idSec.grid.appendChild(_f("Data entity type", core.data_entity_type, "core.data_entity_type", { mono: true }));
      idSec.grid.appendChild(_f("Layout template", core.layout_template, "core.layout_template", { mono: true }));
      idSec.grid.appendChild(_f("Version", core.version, "core.version", { mono: true, readonly: true }));
      idSec.grid.appendChild(_f("Parent framework ID", core.parent_framework_id, "core.parent_framework_id", { mono: true, readonly: true }));
      root.appendChild(idSec.wrap);

      // Phase 38.4 Krok 14a-A1m #2 (12.5.2026): popis v separatnim popupu
      // (📖 ikona v header). Zadna inline Popis sekce v form.

      // Section: Sloupce (preview, Krok 14b doplni inline editor)
      const colsSec = _sectionBuild("Sloupce", "fw.comp_def WHERE parent_core_id = " + core.id);
      const cols = (this._data && this._data.columns) || [];
      if (cols.length === 0) {
        const empty = document.createElement("div");
        empty.style.cssText = "padding:8px 12px;color:#5d6975;font-style:italic;grid-column:1/-1;";
        empty.textContent = "Žádné sloupce (comp_def WHERE core_id=" + core.id + " is empty).";
        colsSec.grid.appendChild(empty);
      } else {
        const table = document.createElement("table");
        table.style.cssText = "grid-column:1/-1;width:100%;font-size:12px;border-collapse:collapse;";
        const thead = document.createElement("thead");
        thead.innerHTML = "<tr style=\"background:#141a20;color:#a8b4c2;text-align:left;\">" +
          "<th style=\"padding:5px 8px;border-bottom:1px solid #2a3340;\">ID</th>" +
          "<th style=\"padding:5px 8px;border-bottom:1px solid #2a3340;\">Field name</th>" +
          "<th style=\"padding:5px 8px;border-bottom:1px solid #2a3340;\">Label</th>" +
          "<th style=\"padding:5px 8px;border-bottom:1px solid #2a3340;\">Type</th>" +
          "<th style=\"padding:5px 8px;border-bottom:1px solid #2a3340;\">Sort</th>" +
          "</tr>";
        table.appendChild(thead);
        const tbody = document.createElement("tbody");
        cols.forEach(c => {
          const tr = document.createElement("tr");
          tr.style.cssText = "border-bottom:1px solid #1a2026;";
          tr.innerHTML =
            "<td style=\"padding:4px 8px;color:#5d6975;font-family:monospace;\">" + _esc(c.id) + "</td>" +
            "<td style=\"padding:4px 8px;font-family:monospace;\">" + _esc(c.field_name || c.code) + "</td>" +
            "<td style=\"padding:4px 8px;\">" + _esc(c.label) + "</td>" +
            "<td style=\"padding:4px 8px;color:#8a96a4;\">" + _esc(c.comp_type_id || c.type) + "</td>" +
            "<td style=\"padding:4px 8px;color:#5d6975;font-family:monospace;\">" + _esc(c.sort_order) + "</td>";
          tbody.appendChild(tr);
        });
        table.appendChild(tbody);
        colsSec.grid.appendChild(table);
      }
      root.appendChild(colsSec.wrap);

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
        this._dirtyBadge.textContent = count > 0
          ? "● " + count + " změna" + (count > 1 ? (count < 5 ? "y" : "") : "")
          : "";
        this._dirtyBadge.style.display = count > 0 ? "" : "none";
      }
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
      _buildDescriptionsPopup({
        entityKind: "core",
        entityLabel: core.label || core.code || "(bez labelu)",
        descUser: core.description_user,
        descSystem: core.description_system,
        onDirty: this._onDirty.bind(this),
      });
    }

    // Phase 38.4 Krok 14a-A1k #4: před zavřením oken pres ✕ se zeptej,
    // pokud jsou neuložené změny. Dark design, 3 tlačítka.
    async _beforeCloseHandler() {
      if (!this._dirty || this._dirty.size === 0) return "close";
      const count = this._dirty.size;
      const fields = Array.from(this._dirty).join(", ");
      // A1p: Czech grammar — adjektivum + noun spolu (1 = provedenou změnu,
      // 2-4 = provedené změny, 5+ = provedených změn).
      const phrase = count > 1
        ? (count < 5 ? "provedené změny" : "provedených změn")
        : "provedenou změnu";
      const decision = await _confirmDarkDialog({
        title: "Neuložené změny",
        message: "Mám uložit tebou " + phrase + "? (" + count + ")\n\nPole: " + fields,
        threeButtons: true,
        yes: "Ano",
        no: "Ne",
        cancel: "Zrušit",
      });
      if (decision === "cancel") return "cancel";
      if (decision === "yes") {
        this._onSaveClick();
        return "save";
      }
      return "close"; // "no" — zavřít bez uložení
    }

    open() {
      const title = "Design: Jádro pro řádek";
      this._shell = _buildModalShell({
        title: title,
        width: "920px",
        beforeClose: () => this._beforeCloseHandler(),
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
      const url = "/api/v1/erp/design/core-by-code/" + encodeURIComponent(gridCode);
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
      const ctxSec = _sectionBuild("Kontext kliku v gridu", "UI state (gridCode + rowId + headerName + compDefId)");
      ctxSec.grid.appendChild(_f("Grid (core.code)", this.opts.gridCode, "ctx.gridCode", { mono: true, readonly: true }));
      ctxSec.grid.appendChild(_f("Řádek (ID)", this.opts.rowId, "ctx.rowId", { mono: true, readonly: true }));
      ctxSec.grid.appendChild(_f("Klepnutý sloupec", this.opts.headerName, "ctx.headerName", { readonly: true }));
      ctxSec.grid.appendChild(_f("comp_def_id sloupce", this.opts.compDefId, "ctx.compDefId", { mono: true, readonly: true }));
      root.appendChild(ctxSec.wrap);

      // Section: Jadro identita — ID/version readonly (PK + lineage), ostatni editable
      const core = (this._data && this._data.core) || null;
      if (core && core.id) {
        // Krok 14a-A1m #1: section title pair.
        const idSec = _sectionBuild("Jádro pro řádek — identita", "fw.core — identita + layout + version");
        idSec.grid.appendChild(_f("ID", core.id, "core.id", { mono: true, readonly: true }));
        idSec.grid.appendChild(_f("Code", core.code, "core.code", { mono: true }));
        idSec.grid.appendChild(_f("Label", core.label, "core.label"));
        idSec.grid.appendChild(_d("Layout type", core.layout_type, "layout_type", "core.layout_type"));
        idSec.grid.appendChild(_f("Data entity type", core.data_entity_type, "core.data_entity_type", { mono: true }));
        idSec.grid.appendChild(_f("Version", core.version, "core.version", { mono: true, readonly: true }));
        root.appendChild(idSec.wrap);

        // Phase 38.4 Krok 14a-A1m #2 (12.5.2026): popis v separatnim popupu
        // (📖 ikona v header). Zadna inline Popis sekce.
      } else {
        const noCore = _sectionBuild("Jádro pro řádek", "fw.core — žádný záznam");
        const empty = document.createElement("div");
        empty.style.cssText = "padding:8px 12px;color:#5d6975;font-style:italic;grid-column:1/-1;";
        empty.textContent = "Žádné jádro pro grid '" + (this.opts.gridCode || "?") + "' (hardcoded view bez core entry, nebo grid neexistuje v fw.core).";
        noCore.grid.appendChild(empty);
        root.appendChild(noCore.wrap);
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
  // Export
  // ────────────────────────────────────────────────────────────────────

  global.DesignSoudecekCoreForm = DesignSoudecekCoreForm;
  global.DesignJadroRadekForm = DesignJadroRadekForm;

})(window);
