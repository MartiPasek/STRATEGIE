/**
 * ErpForm — UI Kit form orchestrator (auto-render z FormDef metadat).
 *
 * Bere metadata jádra (komponenty + properties + data row), staví DOM
 * pomocí UI Kit komponent (ErpInput, ErpCheckbox, ErpFormList,
 * ErpFormSection). Drží form state (initial vs current) pro Phase C
 * save flow (OK/Storno tlačítka).
 *
 * Architektura:
 *   1. Components z EC_FormDefEdit (Typ + cFieldName + cCaption + cParent)
 *   2. Properties z EC_FormDefEditProperty (LookupView, ReadOnly, ...)
 *   3. Data dict (raw values + _lookup_{field} enriched display labels)
 *   4. Title z FormSetting (Typ=30) FormCaption property nebo FormDef.Nazev
 *
 * State:
 *   _initialValues — snapshot po build (pro dirty diff)
 *   _components    — registry: c_field_name → component instance
 *
 * API:
 *   form.getValues()         { fieldName: currentValue }
 *   form.getInitialValues()  { fieldName: initialValue }
 *   form.getDirtyValues()    diff vs initial — JEN změněné fields
 *   form.getDirtyFields()    array of changed field names
 *   form.isDirty()           boolean
 *   form.validate()          { valid, errors: { fieldName: msg } }
 *   form.setValue(name, val) programmatic update + sync component
 *   form.getField(name)      component instance pro field
 *   form.markClean()         _initialValues = current (po úspěšném save)
 *   form.reset()             restore initial values
 *   form.setReadOnly(bool)   propagate na komponenty
 *   form.setTitle(text)
 *   form.element()           wrapper <form>
 *   form.destroy()
 *
 * Phase B+6.6a (6.5.2026) — most do Phase C edit pipeline.
 * Phase A read-only: Phase A=true. Phase C: read_only=false + footer
 * s OK/Storno (přijde s následující fází).
 */
(function (global) {
  "use strict";

  function _esc(s) {
    return String(s).replace(/[&<>"']/g, c =>
      ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])
    );
  }

  function _normalize(s) {
    return String(s || "").toLowerCase().replace(/\s+/g, "");
  }

  /**
   * Parse cParent="c{id}" → integer ID. Vrací null pokud format nesedí.
   * Centrála konvence: cParent string ref na GroupBox.id přes prefix "c".
   * Např. "c12" → 12, "c469" → 469.
   * Mirror server-side render_generator._parse_parent_id().
   */
  function _parseParentId(cParent) {
    if (!cParent) return null;
    const s = String(cParent).trim();
    if (!s.startsWith("c") && !s.startsWith("C")) return null;
    const n = parseInt(s.slice(1), 10);
    return Number.isFinite(n) ? n : null;
  }

  /**
   * Resolve real caption — replikuje server-side _resolve_caption().
   * Phase A.3 (render_generator.py): real Caption je v properties,
   * ne v EC_FormDefEdit.cCaption (= "NOVÁ" default při vytvoření).
   *
   * Priorita:
   *   1. properties.Caption / cCaption / PropertyCaption / Text / cText
   *   2. comp.c_caption (pokud != "NOVÁ")
   *   3. comp.c_field_name
   *   4. ""
   */
  function _resolveCaption(comp) {
    const props = comp.properties || {};
    const KEYS = ["Caption", "cCaption", "PropertyCaption", "Text", "cText"];
    for (const k of KEYS) {
      const v = props[k];
      if (v != null && String(v).trim() !== "") return String(v).trim();
    }
    const cc = String(comp.c_caption || "").trim();
    if (cc && cc.toUpperCase() !== "NOVÁ") return cc;
    if (comp.c_field_name && String(comp.c_field_name).trim()) {
      return String(comp.c_field_name).trim();
    }
    return "";
  }

  /**
   * Phase A+1 (7.5.2026): pixel layout engine.
   *
   * Marti's vize — každá komponenta v Centrále 1 jádře má vlastní pozici
   * (Top/Left) + dimenze (Width/Height) + Anchors (elasticita) + Align
   * (fill behavior). Žádné konvence "co vlevo, co vpravo". Server posílá
   * structured layout dict, frontend renderuje absolute positioning.
   */

  /**
   * Aktivovat pixel mode pokud aspoň 30 % visual components má layout
   * data (width nebo height > 0). Nižší threshold by triggeroval pro
   * jádra s default layout=0 (prázdné properties), což by neudělalo
   * správnou věc. Vyšší threshold by minul jádra s mixem (některé
   * components mají layout, jiné ne).
   */
  function _isPixelLayoutEnabled(visuals) {
    if (!visuals || visuals.length === 0) return false;
    const hasLayoutCount = visuals.filter(c =>
      c.layout && (c.layout.width > 0 || c.layout.height > 0)
    ).length;
    return hasLayoutCount / visuals.length >= 0.3;
  }

  /**
   * Aplikuj layout na DOM element. Mutates element.style + classList.
   * @param el HTMLElement - target
   * @param layout {top, left, width, height, align, anchors[], margins[]}
   * @param scale number - scale factor (1 = native, <1 = shrink)
   */
  function _applyLayout(el, layout, scale, reservations, parentLayout) {
    if (!el || !layout) return;
    scale = scale || 1;
    // Reservations = parent's reserved sides per Delphi VCL Align priority.
    // alLeft/alTop/alBottom/alRight siblings reserve their portion FIRST,
    // alClient fills remaining. CSS native to neumí — manuálně počítáme.
    reservations = reservations || { left: 0, top: 0, right: 0, bottom: 0 };
    // ParentLayout = {width, height} pro Anchors elasticity calculation.
    // Pokud component má akRight, právý okraj je fixed (right: Xpx z parentu).
    // Pokud akBottom, dolní okraj fixed (bottom: Ypx z parentu).
    parentLayout = parentLayout || { width: 0, height: 0 };
    // Phase A+1 (7.5.2026): hidden-by-positioning Delphi VCL pattern
    // Pokud Left nebo Top > 5000, element je hidden (Centrála 1 legacy
    // — "kluku z IT bordel" Marti's slovo). Skip render.
    if (_isHiddenByPositioning(layout)) {
      el.style.display = "none";
      el.setAttribute("data-erp-hidden-by-positioning", "true");
      return;
    }
    el.classList.add("erp-pixel-positioned");
    const align = layout.align || "alNone";
    const sR = reservations.right * scale;
    const sL = reservations.left * scale;
    const sT = reservations.top * scale;
    const sB = reservations.bottom * scale;
    // Align modifiers — explicit inline styly s reservations adjustment.
    // Override CSS class behavior (CSS class je default, inline má prioritu).
    if (align === "alClient") {
      el.classList.add("erp-align-client");
      el.style.top = sT + "px";
      el.style.left = sL + "px";
      el.style.right = sR + "px";
      el.style.bottom = sB + "px";
      el.style.width = "auto";
      el.style.height = "auto";
    } else if (align === "alTop") {
      // alTop fills horizontally (after alLeft/alRight reservations), top edge
      el.classList.add("erp-align-top");
      el.style.top = "0";       // own — ignore alTop reservation (or future: prior alTop sum)
      el.style.left = sL + "px";
      el.style.right = sR + "px";
      el.style.bottom = "auto";
      el.style.width = "auto";
      if (layout.height > 0) el.style.height = (layout.height * scale) + "px";
    } else if (align === "alBottom") {
      // alBottom fills horizontally (after alLeft/alRight), bottom edge
      el.classList.add("erp-align-bottom");
      el.style.bottom = "0";    // own — ignore alBottom reservation
      el.style.left = sL + "px";
      el.style.right = sR + "px";
      el.style.top = "auto";
      el.style.width = "auto";
      if (layout.height > 0) el.style.height = (layout.height * scale) + "px";
    } else if (align === "alLeft") {
      // alLeft fills vertically (after alTop/alBottom), left edge
      el.classList.add("erp-align-left");
      el.style.top = sT + "px";
      el.style.left = "0";      // own — ignore alLeft reservation
      el.style.bottom = sB + "px";
      el.style.right = "auto";
      el.style.height = "auto";
      if (layout.width > 0) el.style.width = (layout.width * scale) + "px";
    } else if (align === "alRight") {
      // alRight fills vertically (after alTop/alBottom), right edge
      el.classList.add("erp-align-right");
      el.style.top = sT + "px";
      el.style.right = "0";     // own — ignore alRight reservation
      el.style.bottom = sB + "px";
      el.style.left = "auto";
      el.style.height = "auto";
      if (layout.width > 0) el.style.width = (layout.width * scale) + "px";
    } else {
      // alNone — pixel positioning Top/Left + Anchors elasticity
      const anchors = layout.anchors || ["akLeft", "akTop"];
      const hasLeft = anchors.indexOf("akLeft") >= 0;
      const hasTop = anchors.indexOf("akTop") >= 0;
      const hasRight = anchors.indexOf("akRight") >= 0;
      const hasBottom = anchors.indexOf("akBottom") >= 0;
      // Horizontal positioning
      if (hasLeft && hasRight && parentLayout.width > 0) {
        // Elastic horizontally: pin both edges, width auto-grows with parent
        const rightDist = parentLayout.width - layout.left - layout.width;
        el.style.left = (layout.left * scale) + "px";
        el.style.right = (rightDist * scale) + "px";
        el.style.width = "auto";
      } else if (hasRight && !hasLeft) {
        // Pin right edge only — fixed width, follows parent right
        const rightDist = parentLayout.width > 0
          ? parentLayout.width - layout.left - layout.width
          : 0;
        el.style.right = (rightDist * scale) + "px";
        el.style.left = "auto";
        if (layout.width > 0) el.style.width = (layout.width * scale) + "px";
      } else {
        // Default: akLeft fixed, no elastic horizontal
        el.style.left = (layout.left * scale) + "px";
        el.style.right = "auto";
        if (layout.width > 0) el.style.width = (layout.width * scale) + "px";
      }
      // Vertical positioning
      if (hasTop && hasBottom && parentLayout.height > 0) {
        // Elastic vertically: pin both edges, height auto-grows with parent
        const bottomDist = parentLayout.height - layout.top - layout.height;
        el.style.top = (layout.top * scale) + "px";
        el.style.bottom = (bottomDist * scale) + "px";
        el.style.height = "auto";
      } else if (hasBottom && !hasTop) {
        // Pin bottom edge only — fixed height, follows parent bottom
        const bottomDist = parentLayout.height > 0
          ? parentLayout.height - layout.top - layout.height
          : 0;
        el.style.bottom = (bottomDist * scale) + "px";
        el.style.top = "auto";
        if (layout.height > 0) el.style.height = (layout.height * scale) + "px";
      } else {
        // Default: akTop fixed, no elastic vertical
        el.style.top = (layout.top * scale) + "px";
        el.style.bottom = "auto";
        if (layout.height > 0) el.style.height = (layout.height * scale) + "px";
      }
    }
    // Anchors: pro Phase A+1 fixed (no resize behavior). Future iterace:
    // [akLeft, akTop, akRight] → CSS calc(100% - left - rightSpace) pro
    // elastic horizontally. Pro dnes ignorujeme — explicit width staví UI
    // approximately Centrála 1 layout.
  }

  /**
   * Phase A+1 (7.5.2026): Compute Delphi VCL Align reservations pro parent.
   * V Delphi VCL fill order: alTop, alLeft, alRight, alBottom přiberou své
   * sides; alClient pak fill remaining. CSS to neumí, ručně počítáme.
   *
   * @param children - array of {layout: {align, width, height}}
   * @returns {left, right, top, bottom} - reserved pixels per side
   */
  function _computeAlignReservations(children) {
    const r = { left: 0, top: 0, right: 0, bottom: 0 };
    if (!children || children.length === 0) return r;
    for (const c of children) {
      if (!c.layout) continue;
      const a = c.layout.align;
      const w = c.layout.width || 0;
      const h = c.layout.height || 0;
      if (a === "alLeft") r.left += w;
      else if (a === "alRight") r.right += w;
      else if (a === "alTop") r.top += h;
      else if (a === "alBottom") r.bottom += h;
    }
    return r;
  }

  // Expose helper jako global pro cross-component reuse (ErpFormSection,
  // později ErpPageControl content area).
  global._erpApplyLayout = _applyLayout;

  /**
   * Detect "hidden by positioning" — Delphi VCL legacy pattern. Developer
   * místo Visible=False nastavil Left/Top mimo screen (např. Left=29788).
   * Marti's "kluku z IT bordel" — legacy hidden fields v Centrále 1.
   */
  function _isHiddenByPositioning(layout) {
    if (!layout) return false;
    const HIDE_THRESHOLD = 5000;
    return (layout.left || 0) > HIDE_THRESHOLD ||
           (layout.top || 0) > HIDE_THRESHOLD;
  }

  /**
   * Vypočti dimenze form root z components (max bottom-right corner).
   * Použito pokud FormDef nemá fWidth/fHeight nebo jsou 0.
   * Filter out hidden-by-positioning components (Centrála 1 legacy pattern).
   */
  function _computeFormDimensions(visuals) {
    let maxRight = 0, maxBottom = 0;
    let hiddenCount = 0;
    for (const c of visuals) {
      if (_isHiddenByPositioning(c.layout)) {
        hiddenCount++;
        continue;
      }
      const l = (c.layout && c.layout.left) || 0;
      const t = (c.layout && c.layout.top) || 0;
      const w = (c.layout && c.layout.width) || 0;
      const h = (c.layout && c.layout.height) || 0;
      if (l + w > maxRight) maxRight = l + w;
      if (t + h > maxBottom) maxBottom = t + h;
    }
    if (hiddenCount > 0) {
      try {
        console.log("[ErpForm] hidden-by-positioning components skipped:",
          hiddenCount, "(legacy Delphi pattern)");
      } catch (e) {}
    }
    return { width: maxRight + 20, height: maxBottom + 20 };
  }

  /**
   * Detect ErpInput type podle komponenta + properties + cMask heuristic.
   * Default = "text".
   */
  function _detectInputType(comp) {
    const fname = _normalize(comp.c_field_name);
    const mask = (comp.c_mask || "").trim();
    // Pattern matching na cFieldName
    if (/^(telefon|tel|phone|mobil)$/.test(fname)) return "phone";
    if (/^(ico|ic)$/.test(fname)) return "ico";
    if (/^dic$/.test(fname)) return "dic";
    if (/^(email|mail)$/.test(fname)) return "email";
    // cMask heuristic
    if (mask.includes("##.##.####") || mask.includes("dd.mm.yyyy")) return "date";
    if (/^\d+(\.\d+)?$/.test(mask) || mask.includes("#,##0")) return "number";
    return "text";
  }

  // (DROP 18.5.2026) ErpForm + ErpForm_TYP exports dropped — legacy
  // Centrála 1 form renderer unused. Pixel layout helpers above zachovány
  // (_erpApplyLayout, _erpFormDebug, dumpErpDebug) — used by formsection.js.
})(typeof window !== "undefined" ? window : this);
