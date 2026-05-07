/**
 * ErpFormSection — UI Kit GroupBox container.
 *
 * Wrapper kolem skupiny fields s hlavičkou (GroupBox pattern z Centrály 1).
 * Nahradí server-side .erp-group + .erp-group-header + .erp-fields.
 *
 * Usage:
 *
 *   const sec = new ErpFormSection(container, {
 *     title: "Vzhled a název soudečku",
 *     orphan: false,         // styling: dashed border pokud true
 *     emptyHint: null,       // dim message pokud žádné fields
 *     gridMinmax: "200px",   // CSS minmax pro auto-fit grid
 *   });
 *
 *   sec.addField(componentInstance);
 *     // componentInstance = { wrapperElement(): HTMLElement } (ErpInput,
 *     // ErpCheckbox, ErpFormList, ...) NEBO raw HTMLElement
 *
 *   sec.getFields();        // array of component instances
 *   sec.setTitle("New header");
 *   sec.element();          // wrapper <div class="erp-section">
 *   sec.getFieldsContainer();  // <div class="erp-fields"> uvnitř
 *   sec.destroy();
 *
 * Phase B+6.5 (6.5.2026).
 */
(function (global) {
  "use strict";

  function _esc(s) {
    return String(s).replace(/[&<>"']/g, c =>
      ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])
    );
  }

  class ErpFormSection {
    constructor(container, options) {
      this.container = container || null;
      this.options = Object.assign({
        title: "",
        orphan: false,
        emptyHint: null,
        gridMinmax: "200px",
      }, options || {});
      this._destroyed = false;
      this._fields = [];  // array of component instances or HTMLElements
      this._render();
    }

    _render() {
      this.wrapper = document.createElement("div");
      this.wrapper.className = "erp-section erp-group";
      // Use existing .erp-group class for visual parity s server-side render
      // (B+2.7+ compact density v jádro modalu pak override stejně přes
      // .erp-jadro-content .erp-group).
      if (this.options.orphan) {
        this.wrapper.classList.add("erp-group-orphan");
      }

      // Header
      this.headerEl = document.createElement("div");
      this.headerEl.className = "erp-group-header";
      this.headerEl.textContent = this.options.title || "";
      if (!this.options.title) this.headerEl.style.display = "none";
      this.wrapper.appendChild(this.headerEl);

      // Fields grid container
      this.fieldsEl = document.createElement("div");
      this.fieldsEl.className = "erp-fields";
      // Inline style — auto-fit grid s nastavitelným minmax
      this.fieldsEl.style.gridTemplateColumns =
        "repeat(auto-fit, minmax(" + this.options.gridMinmax + ", 1fr))";
      this.wrapper.appendChild(this.fieldsEl);

      // Empty hint
      if (this.options.emptyHint) {
        this.emptyHintEl = document.createElement("div");
        this.emptyHintEl.className = "erp-group-empty-hint";
        this.emptyHintEl.textContent = this.options.emptyHint;
        this.emptyHintEl.style.display = "none";  // shown jen pokud žádné fields
        this.wrapper.appendChild(this.emptyHintEl);
      }

      if (this.container) this.container.appendChild(this.wrapper);
    }

    /**
     * Append field do sekce.
     * @param {object|HTMLElement} field — komponenta s .wrapperElement() nebo
     *                                     samotný DOM element
     */
    addField(field) {
      if (this._destroyed) return;
      let el = null;
      if (field && typeof field.wrapperElement === "function") {
        el = field.wrapperElement();
      } else if (field instanceof HTMLElement) {
        el = field;
      } else if (field && field.nodeType === 1) {
        el = field;  // duck typing pro HTMLElement
      }
      if (!el) {
        console.warn("ErpFormSection.addField: invalid field", field);
        return;
      }
      this._fields.push(field);
      this.fieldsEl.appendChild(el);
      this._updateEmptyVisual();
    }

    _updateEmptyVisual() {
      if (!this.emptyHintEl) return;
      const empty = this._fields.length === 0;
      this.emptyHintEl.style.display = empty ? "" : "none";
      if (empty) this.wrapper.classList.add("erp-group-empty");
      else this.wrapper.classList.remove("erp-group-empty");
    }

    /** Returns array of registered field components / elements. */
    getFields() {
      return this._fields.slice();
    }

    /** Returns underlying <div class="erp-section"> wrapper. */
    element() {
      return this.wrapper;
    }
    wrapperElement() {
      return this.wrapper;
    }

    /** Returns <div class="erp-fields"> grid container (pro custom append). */
    getFieldsContainer() {
      return this.fieldsEl;
    }

    /**
     * Phase A+1 (7.5.2026): Convert section na pixel container.
     * Sekce sama je positioned absolute (within form root), fieldsEl
     * je relative container pro absolutely positioned children.
     *
     * @param {object} sectionLayout - {top, left, width, height, align, anchors}
     *                                 pro positioning sekce v parent containeru
     * @param {object} opts - {scale: number, noCaption: bool}
     */
    setPixelMode(sectionLayout, opts) {
      if (this._destroyed) return;
      opts = opts || {};
      const scale = opts.scale || 1;
      // Mark wrapper jako pixel container
      this.wrapper.classList.add("pixel-container");
      if (opts.noCaption || !this.options.title) {
        this.wrapper.classList.add("no-caption");
      }
      // Apply layout na samotný section wrapper (positioning v form root)
      if (sectionLayout) {
        if (typeof global._erpApplyLayout === "function") {
          global._erpApplyLayout(this.wrapper, sectionLayout, scale, opts.reservations);
        } else {
          // Fallback inline (pokud helper není dostupný)
          this.wrapper.style.position = "absolute";
          if (sectionLayout.top != null) this.wrapper.style.top = (sectionLayout.top * scale) + "px";
          if (sectionLayout.left != null) this.wrapper.style.left = (sectionLayout.left * scale) + "px";
          if (sectionLayout.width > 0) this.wrapper.style.width = (sectionLayout.width * scale) + "px";
          if (sectionLayout.height > 0) this.wrapper.style.height = (sectionLayout.height * scale) + "px";
        }
      }
      // fieldsEl: relative container, žádný grid (children pixel positioned)
      this.fieldsEl.style.display = "block";
      this.fieldsEl.style.position = "relative";
      this.fieldsEl.style.gridTemplateColumns = "";
      this.fieldsEl.style.height = "100%";  // fill section minus header
      this._pixelMode = true;
      this._pixelScale = scale;
    }

    /**
     * Phase A+1: Append field s pixel layout positioning. Vyžaduje
     * setPixelMode() předem. Field's wrapper element dostane absolute
     * positioning podle layout dict.
     */
    addPixelField(field, layout) {
      if (this._destroyed) return;
      if (!this._pixelMode) {
        // Fallback na vertical addField
        return this.addField(field);
      }
      let el = null;
      if (field && typeof field.wrapperElement === "function") {
        el = field.wrapperElement();
      } else if (field instanceof HTMLElement) {
        el = field;
      } else if (field && field.nodeType === 1) {
        el = field;
      }
      if (!el) {
        console.warn("ErpFormSection.addPixelField: invalid field", field);
        return;
      }
      this._fields.push(field);
      this.fieldsEl.appendChild(el);
      // Apply layout na child element (relative k fieldsEl)
      // POZOR: child layout.top/left jsou absolute koordináty v form root
      // (z Centrály 1 properties), ale v pixel mode jsou children section
      // relativní k section.left/top. Frontend musí to ofsetovat —
      // child.relativeTop = layout.top - section.top, atd.
      // Tohle je řízeno z form.js _build (znalost section layout context).
      // Zde jen aplikuje co dostane.
      if (layout && typeof global._erpApplyLayout === "function") {
        global._erpApplyLayout(el, layout, this._pixelScale);
      }
      this._updateEmptyVisual();
    }

    setTitle(title) {
      if (this._destroyed) return;
      this.options.title = title;
      if (this.headerEl) {
        this.headerEl.textContent = title || "";
        this.headerEl.style.display = title ? "" : "none";
      }
    }

    setOrphan(orphan) {
      if (this._destroyed) return;
      this.options.orphan = !!orphan;
      if (orphan) this.wrapper.classList.add("erp-group-orphan");
      else this.wrapper.classList.remove("erp-group-orphan");
    }

    /** Remove a field by index nebo by component instance reference. */
    removeField(fieldOrIdx) {
      if (this._destroyed) return false;
      let idx = -1;
      if (typeof fieldOrIdx === "number") {
        idx = fieldOrIdx;
      } else {
        idx = this._fields.indexOf(fieldOrIdx);
      }
      if (idx < 0 || idx >= this._fields.length) return false;
      const field = this._fields[idx];
      let el = null;
      if (field && typeof field.wrapperElement === "function") {
        el = field.wrapperElement();
      } else if (field instanceof HTMLElement) {
        el = field;
      }
      if (el && el.parentNode === this.fieldsEl) {
        this.fieldsEl.removeChild(el);
      }
      this._fields.splice(idx, 1);
      this._updateEmptyVisual();
      return true;
    }

    /** Remove všech fields (a destroy je pokud mají destroy()). */
    clear(destroyFields) {
      if (this._destroyed) return;
      if (destroyFields) {
        for (const f of this._fields) {
          if (f && typeof f.destroy === "function") {
            try { f.destroy(); } catch (e) {}
          }
        }
      }
      this._fields = [];
      this.fieldsEl.innerHTML = "";
      this._updateEmptyVisual();
    }

    destroy() {
      if (this._destroyed) return;
      this._destroyed = true;
      // Destroy registered components s destroy()
      for (const f of this._fields) {
        if (f && typeof f.destroy === "function") {
          try { f.destroy(); } catch (e) {}
        }
      }
      this._fields = [];
      if (this.wrapper && this.wrapper.parentNode) {
        this.wrapper.parentNode.removeChild(this.wrapper);
      }
      this.wrapper = null;
      this.headerEl = null;
      this.fieldsEl = null;
      this.emptyHintEl = null;
    }
  }

  // ── Factory ────────────────────────────────────────────────────────
  ErpFormSection.create = function (options) {
    const sec = new ErpFormSection(null, options);
    return sec.element();
  };

  global.ErpFormSection = ErpFormSection;
})(typeof window !== "undefined" ? window : this);
