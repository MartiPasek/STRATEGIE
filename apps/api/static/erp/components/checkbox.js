/**
 * ErpCheckbox — UI Kit boolean toggle.
 *
 * Variants:
 *   - standard (default) — square checkbox + label
 *   - switch — iOS-style toggle slider
 *
 * States: unchecked | checked | indeterminate | disabled | readonly
 *
 * Usage:
 *
 *   const cb = new ErpCheckbox(container, {
 *     label: "Aktivní",
 *     checked: true,
 *     variant: "standard",        // standard | switch
 *     labelPosition: "right",      // right | left
 *     disabled: false,
 *     readonly: false,
 *     indeterminate: false,
 *     hint: "Helper text pod checkboxem",
 *     onChange: (checked) => { ... },
 *   });
 *
 *   cb.value();           // boolean
 *   cb.setValue(true);
 *   cb.setIndeterminate(true);
 *   cb.setDisabled(true);
 *   cb.setLabel("Nový label");
 *   cb.toggle();
 *   cb.focus();
 *   cb.destroy();
 *
 * Phase B+6.3 (5.5.2026).
 */
(function (global) {
  "use strict";

  function _esc(s) {
    return String(s).replace(/[&<>"']/g, c =>
      ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])
    );
  }

  class ErpCheckbox {
    constructor(container, options) {
      this.container = container || null;
      this.options = Object.assign({
        label: "",
        checked: false,
        variant: "standard",       // standard | switch
        labelPosition: "right",    // right | left
        disabled: false,
        readonly: false,
        indeterminate: false,
        hint: null,
        onChange: null,
      }, options || {});
      this._destroyed = false;
      this._render();
    }

    _render() {
      this.wrapper = document.createElement("label");
      this.wrapper.className =
        "erp-checkbox-wrapper" +
        (this.options.variant === "switch" ? " erp-checkbox-switch" : "") +
        (this.options.labelPosition === "left" ? " erp-checkbox-label-left" : "");

      // Native input (visually hidden but keyboard-accessible)
      this.input = document.createElement("input");
      this.input.type = "checkbox";
      this.input.className = "erp-checkbox-input";
      this.input.checked = !!this.options.checked;
      if (this.options.disabled) this.input.disabled = true;
      this.input.indeterminate = !!this.options.indeterminate;

      // Visual box (custom)
      const box = document.createElement("span");
      box.className = "erp-checkbox-box";
      box.setAttribute("aria-hidden", "true");
      // checkmark / indeterminate dash kreslíme přes CSS pseudo-elementy
      this.box = box;

      // Label text
      const labelText = document.createElement("span");
      labelText.className = "erp-checkbox-label";
      labelText.textContent = this.options.label || "";
      this.labelEl = labelText;

      // Order podle labelPosition
      if (this.options.labelPosition === "left") {
        this.wrapper.appendChild(labelText);
        this.wrapper.appendChild(this.input);
        this.wrapper.appendChild(box);
      } else {
        this.wrapper.appendChild(this.input);
        this.wrapper.appendChild(box);
        this.wrapper.appendChild(labelText);
      }

      // Hint
      if (this.options.hint) {
        this.hintEl = document.createElement("span");
        this.hintEl.className = "erp-checkbox-hint";
        this.hintEl.textContent = this.options.hint;
        this.wrapper.appendChild(this.hintEl);
      }

      // Event
      this.input.addEventListener("change", (ev) => this._handleChange(ev));
      // B+10++++++++ (drobnost 6.5.2026 večer): readonly intercept smazán —
      // user smí toggle. Save flow gate (Phase C edit pipeline) bude
      // collect values + skip readonly fields. Marti: "povol i ostatni
      // komponenty, at nejsou read only... checkboxy a inputy".

      this._updateState();

      if (this.container) this.container.appendChild(this.wrapper);
    }

    _handleChange(ev) {
      if (this._destroyed) return;
      // Indeterminate clear on user toggle
      this.options.indeterminate = false;
      this.input.indeterminate = false;
      this.options.checked = this.input.checked;
      this._updateState();
      if (typeof this.options.onChange === "function") {
        try { this.options.onChange(this.options.checked); }
        catch (e) { console.warn("ErpCheckbox onChange error:", e); }
      }
    }

    _updateState() {
      if (this.options.disabled) {
        this.wrapper.classList.add("erp-checkbox-disabled");
      } else {
        this.wrapper.classList.remove("erp-checkbox-disabled");
      }
      if (this.options.readonly) {
        this.wrapper.classList.add("erp-checkbox-readonly");
      } else {
        this.wrapper.classList.remove("erp-checkbox-readonly");
      }
      if (this.options.indeterminate) {
        this.wrapper.classList.add("erp-checkbox-indeterminate");
      } else {
        this.wrapper.classList.remove("erp-checkbox-indeterminate");
      }
    }

    // ── Public API ────────────────────────────────────────────────────

    element() { return this.input; }
    wrapperElement() { return this.wrapper; }

    value() { return !!this.input.checked; }

    setValue(checked) {
      if (this._destroyed) return;
      this.options.checked = !!checked;
      this.input.checked = !!checked;
      this.options.indeterminate = false;
      this.input.indeterminate = false;
      this._updateState();
    }

    toggle() {
      // B+10++++++++ (6.5.2026): readonly nebrání toggle UI. Save flow
      // má vlastní gate (Phase C). Pouze disabled blokuje (HW-level).
      if (this._destroyed || this.options.disabled) return;
      this.setValue(!this.options.checked);
      if (typeof this.options.onChange === "function") {
        try { this.options.onChange(this.options.checked); }
        catch (e) {}
      }
    }

    setIndeterminate(indeterminate) {
      if (this._destroyed) return;
      this.options.indeterminate = !!indeterminate;
      this.input.indeterminate = !!indeterminate;
      this._updateState();
    }

    setDisabled(disabled) {
      if (this._destroyed) return;
      this.options.disabled = !!disabled;
      this.input.disabled = !!disabled;
      this._updateState();
    }

    setReadonly(readonly) {
      if (this._destroyed) return;
      this.options.readonly = !!readonly;
      this._updateState();
    }

    setLabel(label) {
      if (this._destroyed || !this.labelEl) return;
      this.options.label = label;
      this.labelEl.textContent = label || "";
    }

    isDisabled() { return !!this.options.disabled; }
    isReadonly() { return !!this.options.readonly; }
    isIndeterminate() { return !!this.options.indeterminate; }

    focus() {
      if (this._destroyed || !this.input) return;
      this.input.focus();
    }

    destroy() {
      if (this._destroyed) return;
      this._destroyed = true;
      if (this.wrapper && this.wrapper.parentNode) {
        this.wrapper.parentNode.removeChild(this.wrapper);
      }
      this.wrapper = null;
      this.input = null;
      this.box = null;
      this.labelEl = null;
    }
  }

  // ── Factory ────────────────────────────────────────────────────────
  ErpCheckbox.create = function (options) {
    const cb = new ErpCheckbox(null, options);
    return cb.wrapperElement();
  };

  global.ErpCheckbox = ErpCheckbox;
})(typeof window !== "undefined" ? window : this);
