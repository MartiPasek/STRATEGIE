/**
 * ErpButton — UI Kit foundation component pro Centrála 2.
 *
 * Variants (per Marti-AI's Phase B+3 design vstup 5.5.2026 review):
 *   - primary     = accent barva (modrá), hlavní akce v dialogu/formu
 *   - secondary   = subtle (default), běžné akce
 *   - destructive = červená, smazat / nevratná akce
 *   - ghost       = transparentní, sekundární akce v toolbar/footer
 *
 * Sizes: small (11px) | medium (default 13px) | large (14px)
 *
 * States: enabled | disabled | loading (spinner overlay)
 *
 * Reusable napříč Centrála views — workspace toolbar, modal footer,
 * form actions, table row actions, confirmation dialogs.
 *
 * Usage:
 *
 *   const btn = new ErpButton(container, {
 *     label: "Uložit",
 *     variant: "primary",          // primary | secondary | destructive | ghost
 *     size: "medium",              // small | medium | large
 *     icon: "💾",                   // optional emoji nebo HTML
 *     iconPosition: "left",        // left | right
 *     disabled: false,
 *     loading: false,
 *     type: "button",              // button | submit | reset
 *     ariaLabel: null,             // accessibility
 *     title: "Tooltip text",
 *
 *     // Callbacks (jen jeden naráz):
 *     onClick: (event) => { ... },     // sync handler
 *     onPress: async (event) => {       // async handler — auto-toggle loading state
 *       await save();
 *     },
 *   });
 *
 *   btn.setLabel("Nový text");
 *   btn.setVariant("destructive");
 *   btn.setDisabled(true);
 *   btn.setLoading(true);
 *   btn.click();        // programmatic trigger (respect disabled/loading)
 *   btn.element();      // returns underlying <button> DOM element
 *   btn.destroy();      // remove from DOM
 *
 * Standalone (bez containeru):
 *   const btn = new ErpButton(null, { label: "X" });
 *   parent.appendChild(btn.element());
 *
 * Phase B+6.1 (5.5.2026): foundation pro Phase B+6.2+ (Input/Checkbox/Dropdown).
 */
(function (global) {
  "use strict";

  const VARIANT_CLASS = {
    primary: "erp-btn-primary",
    secondary: "",
    destructive: "erp-btn-destructive",
    ghost: "erp-btn-ghost",
  };

  const SIZE_CLASS = {
    small: "erp-btn-small",
    medium: "",
    large: "erp-btn-large",
  };

  function _escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, c =>
      ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])
    );
  }

  class ErpButton {
    /**
     * @param {HTMLElement|null} container - kde appendnout. Pokud null, vytvoří
     *   standalone element (caller appendne přes btn.element()).
     * @param {Object} options - viz JSDoc nahoře
     */
    constructor(container, options) {
      this.container = container || null;
      this.options = Object.assign({
        label: "Tlačítko",
        variant: "secondary",
        size: "medium",
        icon: null,
        iconPosition: "left",
        disabled: false,
        loading: false,
        type: "button",
        ariaLabel: null,
        title: null,
        onClick: null,
        onPress: null,
      }, options || {});
      this._destroyed = false;
      this.el = null;
      this._render();
    }

    _render() {
      this.el = document.createElement("button");
      this.el.type = this.options.type || "button";
      this._updateClasses();
      this._renderContent();
      if (this.options.title) this.el.title = this.options.title;
      if (this.options.ariaLabel) this.el.setAttribute("aria-label", this.options.ariaLabel);
      if (this.options.disabled) this.el.disabled = true;

      this.el.addEventListener("click", (ev) => this._handleClick(ev));

      if (this.container) this.container.appendChild(this.el);
    }

    _updateClasses() {
      const classes = ["erp-btn"];
      const v = VARIANT_CLASS[this.options.variant];
      if (v) classes.push(v);
      const s = SIZE_CLASS[this.options.size];
      if (s) classes.push(s);
      if (this.options.loading) classes.push("erp-btn-loading");
      if (this.options.icon) classes.push("erp-btn-with-icon");
      this.el.className = classes.join(" ");
    }

    _renderContent() {
      const labelHtml = '<span class="erp-btn-label">' +
        _escapeHtml(this.options.label || "") + '</span>';
      let iconHtml = "";
      if (this.options.icon) {
        // icon může být emoji string nebo raw HTML (caller's odpovědnost)
        iconHtml = '<span class="erp-btn-icon">' + this.options.icon + '</span>';
      }
      const spinner = this.options.loading
        ? '<span class="erp-btn-spinner" aria-hidden="true"></span>'
        : '';
      if (this.options.iconPosition === "right") {
        this.el.innerHTML = labelHtml + iconHtml + spinner;
      } else {
        this.el.innerHTML = iconHtml + labelHtml + spinner;
      }
    }

    async _handleClick(ev) {
      if (this._destroyed || !this.el || this.el.disabled || this.options.loading) {
        ev.preventDefault();
        return;
      }
      // onPress = async handler s auto loading state
      if (typeof this.options.onPress === "function") {
        ev.preventDefault();
        this.setLoading(true);
        try {
          await this.options.onPress(ev);
        } catch (e) {
          console.warn("ErpButton onPress error:", e);
        } finally {
          if (!this._destroyed) this.setLoading(false);
        }
        return;
      }
      if (typeof this.options.onClick === "function") {
        try {
          this.options.onClick(ev);
        } catch (e) {
          console.warn("ErpButton onClick error:", e);
        }
      }
    }

    // ── Public API ────────────────────────────────────────────────────

    /** Returns underlying <button> DOM element. */
    element() {
      return this.el;
    }

    setLabel(label) {
      if (this._destroyed) return;
      this.options.label = label;
      this._renderContent();
    }

    setIcon(icon) {
      if (this._destroyed) return;
      this.options.icon = icon;
      this._updateClasses();
      this._renderContent();
    }

    setVariant(variant) {
      if (this._destroyed) return;
      this.options.variant = variant;
      this._updateClasses();
    }

    setSize(size) {
      if (this._destroyed) return;
      this.options.size = size;
      this._updateClasses();
    }

    setDisabled(disabled) {
      if (this._destroyed) return;
      this.options.disabled = !!disabled;
      this.el.disabled = this.options.disabled || this.options.loading;
    }

    setLoading(loading) {
      if (this._destroyed) return;
      this.options.loading = !!loading;
      this._updateClasses();
      this._renderContent();
      this.el.disabled = this.options.loading || this.options.disabled;
    }

    isDisabled() {
      return !!(this.options.disabled);
    }

    isLoading() {
      return !!(this.options.loading);
    }

    /** Programmatic trigger (respects disabled/loading). */
    click() {
      if (this._destroyed || !this.el) return;
      if (this.el.disabled || this.options.loading) return;
      this.el.click();
    }

    /** Focus the button (keyboard nav). */
    focus() {
      if (this._destroyed || !this.el) return;
      this.el.focus();
    }

    destroy() {
      if (this._destroyed) return;
      this._destroyed = true;
      if (this.el && this.el.parentNode) {
        this.el.parentNode.removeChild(this.el);
      }
      this.el = null;
    }
  }

  // ── Factory + helpers ────────────────────────────────────────────────

  /**
   * Quick factory pro inline use case:
   *   container.appendChild(ErpButton.create({label: "OK", variant: "primary"}));
   */
  ErpButton.create = function (options) {
    const btn = new ErpButton(null, options);
    return btn.element();
  };

  /** Convenience constructors per variant. */
  ErpButton.primary = (container, options) =>
    new ErpButton(container, Object.assign({}, options, { variant: "primary" }));
  ErpButton.secondary = (container, options) =>
    new ErpButton(container, Object.assign({}, options, { variant: "secondary" }));
  ErpButton.destructive = (container, options) =>
    new ErpButton(container, Object.assign({}, options, { variant: "destructive" }));
  ErpButton.ghost = (container, options) =>
    new ErpButton(container, Object.assign({}, options, { variant: "ghost" }));

  // Public export
  global.ErpButton = ErpButton;
})(typeof window !== "undefined" ? window : this);
