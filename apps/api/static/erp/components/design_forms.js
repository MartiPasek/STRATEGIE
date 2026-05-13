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
        document.removeEventListener("keydown", onKey);
      }
      // A1t safety: Esc / click outside = null (keep modal, "did nothing").
      // Explicit Ano (true) / Ne (false) jsou jediné destruktivni cesty.
      // Caller pak rozlisuje: true = positive action, false = negative
      // action, null = no-op (nepokracuj).
      function onKey(ev) {
        if (ev.key === "Escape") { cleanup(); resolve(null); }
        else if (ev.key === "Enter") { cleanup(); resolve(true); }
      }
      if (cancelBtn) cancelBtn.addEventListener("click", () => { cleanup(); resolve(false); });
      okBtn.addEventListener("click", () => { cleanup(); resolve(true); });
      ovr.addEventListener("click", (ev) => {
        if (ev.target === ovr) { cleanup(); resolve(null); }
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
      const initialTab = this.opts.initialTab === "prehled" ? "prehled" : "soudecek";
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
      // opts.coreCode (required) — fw.core.code (e.g. 'user_edit')
      // opts.rowId (required)    — data row ID (e.g. users.id=14)
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
      const toggle = document.createElement("button");
      toggle.type = "button";
      toggle.className = "erp-form-design-toggle";
      this._formDesignToggle = toggle;
      this._updateFormDesignToggle();  // initial text + style
      toggle.addEventListener("click", () => {
        this._setFormDesignMode(!this._formDesignMode);
      });
      // Insert PRED sysToggle (= prvni button v rightActions) — toggle
      // je hlavni mode switch, ostatni jsou pomocna nastaveni.
      const sysToggle = rightActions.querySelector(".erp-design-systoggle");
      if (sysToggle) {
        rightActions.insertBefore(toggle, sysToggle);
      } else {
        // Fallback: prepend
        rightActions.insertBefore(toggle, rightActions.firstChild);
      }
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
      // Phase 38.4 Krok 14c hotfix (13.5.2026 ~17:30): live dirty indicator
      // v modal title bar (po _setupFooter consolidation pres footer panel,
      // dirty badge musi byt nekde visible). Pojistka — pokud titleEl exists,
      // update jeho text s count suffix.
      if (this._shell && this._shell.title) {
        const baseTitle = this._spec && this._spec.core
          ? (this._spec.core.label || this._spec.core.code || "Editace")
          : "Editace";
        if (count > 0) {
          const _wBadge2 = count === 1 ? "změna" : (count < 5 ? "změny" : "změn");
          this._shell.title.textContent = baseTitle + " — ● " + count + " " + _wBadge2;
          this._shell.title.style.color = "#d4b88a"; // amber dirty accent
        } else {
          this._shell.title.textContent = baseTitle;
          this._shell.title.style.color = ""; // default white
        }
      }
      _markFormDirty(this, count > 0);
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
      const coreCode = this.opts.coreCode;
      const rowId = this.opts.rowId;
      if (!coreCode || rowId == null) {
        console.error("DesignFwForm: coreCode + rowId required");
        return;
      }

      // Build shell s loading placeholder
      this._shell = _buildModalShell({
        title: "Načítám…",
        width: "920px",
        beforeClose: () => this._beforeCloseHandler(),
        onClose: () => _markFormDirty(this, false),
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
      loading.textContent = "Načítám " + coreCode + " #" + rowId + "…";
      this._shell.body.appendChild(loading);

      try {
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
        if (!this._spec || !this._spec.ok) {
          throw new Error(
            "Backend error: " + (this._spec && this._spec.error || "unknown")
          );
        }
        this._render();
      } catch (e) {
        this._showError("Načítání selhalo: " + e.message);
      }
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

      // Group fields by region_slot (data komponenty z fw.comp_def, parent=form)
      const fieldsBySlot = {};
      for (const f of fields) {
        const slot = f.region_slot || "main";
        if (!fieldsBySlot[slot]) fieldsBySlot[slot] = [];
        fieldsBySlot[slot].push(f);
      }

      // Render každý panel jako sekce
      const D = this._onDirty.bind(this);
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
          // Grid: flex row right-aligned, buttons centered vertical
          sec.grid.style.display = "flex";
          sec.grid.style.justifyContent = "flex-end";
          sec.grid.style.alignItems = "center";
          // Marti's polish (13.5.2026 ~14:45): visible gap mezi OK/Storno
          sec.grid.style.gap = "16px";
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
        for (const comp of templateComponents) {
          const compEl = this._renderTemplateComponent(comp, core, data);
          if (compEl) sec.grid.appendChild(compEl);
        }

        // Render data fields (z fw.comp_def) — pokud nějaké patří k tomuto panelu
        if (slotFields.length > 0) {
          slotFields.sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0));
          for (const f of slotFields) {
            const value = data[f.name];
            const fieldEl = this._renderField(f, value, D);
            if (fieldEl) sec.grid.appendChild(fieldEl);
          }
        }

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

            // Click → open FieldPickerModal
            const formId = this._spec.form.id;
            hint.addEventListener("click", async () => {
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
            });
            hint.title = "Klikni pro otevření palety komponent (Krok 14c)";
          } else if (canPick) {
            hint.title = "Pro přidávání polí přepni form do DESIGN módu (button vpravo nahoře v header).";
          }

          sec.grid.appendChild(hint);
        }

        root.appendChild(sec.wrap);
      }

      this._shell.body.appendChild(root);

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

        if (!entityType || rowId == null) {
          alert("Save selhal: missing entity_type nebo row_id");
          btnEl.disabled = false;
          btnEl.innerHTML = originalHtml;
          return;
        }

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

        // Pokud žádné changes -> clean close (Marti's "OK clean = close" doctrine)
        if (Object.keys(fieldChanges).length === 0) {
          console.info("[DesignFwForm] OK clicked, no dirty changes — closing.");
          this._dirty.clear();
          _markFormDirty(this, false);
          this._shell.close();
          return;
        }

        // POST PATCH
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
          // Optimistic lock conflict
          const errData = await r.json().catch(() => ({}));
          alert(
            "Konflikt: někdo jiný mezitím změnil tento řádek.\\n" +
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
            "Uložení selhalo: HTTP " + r.status + "\\n" +
            (errData.error || "(žádný error message)")
          );
          btnEl.disabled = false;
          btnEl.innerHTML = originalHtml;
          return;
        }

        // 200 OK — toast + close
        const respData = await r.json();
        console.info("[DesignFwForm] PATCH success:", respData);

        // Visual feedback — green flash krátce před close
        btnEl.style.background = "#3a7a3a";
        btnEl.style.borderColor = "#4a9a4a";
        btnEl.innerHTML = "✅ Uloženo";

        // Clear dirty state (modal close handler nepokusí dirty check)
        this._dirty.clear();
        _markFormDirty(this, false);

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
        alert("Chyba spojení: " + (e.message || e));
        btnEl.disabled = false;
        btnEl.innerHTML = originalHtml;
      }
    }

    _renderField(field, value, onDirty) {
      const fieldKey = (this._spec.core.code || "fw_form") + "." + field.name;
      const compType = field.comp_type_code;
      const fieldLayout = field.layout || {};
      const label = field.caption || field.name;
      const readonly = !!fieldLayout.readonly;

      // Phase 38.4 Krok 14c (13.5.2026 ~16:00): dispatch rozsiren o vsech
      // 10 Marti-AI's preview_html-ready comp_types. Drz "uniformita
      // vítězí" — kazdy known comp_type ma explicit branch, novy comp_type
      // = pridat case + pripadne UI Kit helper.
      // Phase 38.4 Krok 14c hotfix (13.5.2026 ~17:30): _field/_dropdown/_memo
      // signature je (label, value, opts) — fieldKey patri DO opts, nepredavat
      // jako 3rd parameter (predtim bug: opts = string fieldKey, opts.onDirty
      // undefined → dirty tracking nikdy nezavolan).
      switch (compType) {
        case "edit":
          return _field(label, value, {
            fieldKey: fieldKey,
            readonly: readonly,
            mono: !!fieldLayout.mono,
            onDirty: onDirty,
          });

        case "number": {
          // _field s type=number — ErpInput podporuje type via opts
          const el = _field(label, value, {
            fieldKey: fieldKey,
            readonly: readonly,
            onDirty: onDirty,
          });
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
          const items = Array.isArray(fieldLayout.enum_values)
            ? fieldLayout.enum_values.map(e => ({ value: e.value, label: e.label }))
            : [];
          return _dropdown(label, value, {
            fieldKey: fieldKey,
            readonly: readonly,
            items: items,
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
      this._shell = _buildModalShell({
        title: "Vyberte pole z databáze",
        width: "780px",
        hideDescToggle: true,
      });
      document.body.appendChild(this._shell.overlay);

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
        // Parallel fetch — comp_types + entity_columns
        const [ctResp, ecResp] = await Promise.all([
          fetch("/api/v1/erp/design/comp-types", { credentials: "include" }),
          fetch(
            "/api/v1/erp/design/entity-columns/" + encodeURIComponent(this.opts.entityType),
            { credentials: "include" }
          ),
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

        this._render();
      } catch (e) {
        loading.style.color = "#e88";
        loading.textContent = "Načítání selhalo: " + (e.message || e);
        console.error("[FieldPickerModal] load failed:", e);
      }
    }

    _render() {
      this._shell.body.innerHTML = "";

      // Top hint
      const hint = document.createElement("div");
      hint.style.cssText = "color:#8a96a4;font-size:12px;margin-bottom:10px;line-height:1.5;";
      hint.innerHTML =
        "Klikni na řádek pro výběr / odznačení. Typ komponenty lze přepsat " +
        "pres dropdown vpravo. <b>" + this._columns.length + "</b> sloupců dostupných.";
      this._shell.body.appendChild(hint);

      // Palette container — scrollable list of rows
      const palette = document.createElement("div");
      palette.style.cssText =
        "flex:1 1 auto;overflow-y:auto;border:1px solid #2a3340;border-radius:4px;background:#0f141a;";
      this._shell.body.appendChild(palette);

      // Render each column as a row
      for (const col of this._columns) {
        const row = this._renderColumnRow(col);
        palette.appendChild(row);
      }

      // Footer bar — Selected count + actions
      const footer = document.createElement("div");
      footer.style.cssText =
        "margin-top:12px;display:flex;align-items:center;justify-content:flex-end;gap:16px;" +
        "border-top:1px solid #2a3340;padding-top:10px;";
      const counter = document.createElement("span");
      counter.id = "fpmCounter";
      counter.style.cssText = "color:#a8b4c2;font-size:12px;margin-right:auto;";
      counter.textContent = "Vybráno: 0";
      footer.appendChild(counter);

      const okBtn = document.createElement("button");
      okBtn.type = "button";
      okBtn.style.cssText =
        "min-width:110px;padding:6px 16px;background:#3a5a8a;border:1px solid #4a7ba8;" +
        "border-radius:3px;color:#e8eef5;cursor:pointer;font-size:13px;font-weight:600;";
      okBtn.innerHTML = '<span style="color:#5dbf5d;font-weight:700;margin-right:6px;">✓</span>Přidat vybraná';
      okBtn.addEventListener("click", () => this._handleSubmit(okBtn));
      footer.appendChild(okBtn);

      const cancelBtn = document.createElement("button");
      cancelBtn.type = "button";
      cancelBtn.style.cssText =
        "min-width:90px;padding:6px 16px;background:#2a3340;border:1px solid #3a4754;" +
        "border-radius:3px;color:#cfd6df;cursor:pointer;font-size:13px;";
      cancelBtn.innerHTML = '<span style="color:#d4888a;font-weight:700;margin-right:6px;">✗</span>Storno';
      cancelBtn.addEventListener("click", () => this._shell.close());
      footer.appendChild(cancelBtn);

      this._shell.body.appendChild(footer);
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

      // Success — close + trigger onComplete callback
      btnEl.style.background = "#3a7a3a";
      btnEl.innerHTML = "✅ Hotovo (" + (okCount + existingCount) + ")";
      setTimeout(() => {
        if (typeof this.opts.onComplete === "function") {
          try { this.opts.onComplete({ added: okCount, existing: existingCount }); }
          catch (e) { console.error("[FieldPickerModal] onComplete failed:", e); }
        }
        this._shell.close();
      }, 600);
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
