/**
 * ErpInput — UI Kit text input s typed masks + validation.
 *
 * Marti's MVP requests (5.5.2026 odpoledne):
 *   - phone:  "+420 777 180 511" ↔ "+420777180511"   (also accepts "777 180 511")
 *   - ico:    "27 96 48 54"      ↔ "27964854"        (mod-11 checksum validace)
 *   - dic:    "CZ27964854"       ↔ "CZ27964854"      (CZ prefix + 8-10 digits)
 *   - date:   "25.5.1972"        ↔ "1972-05-25"      (ISO storage)
 *   - time:   "20:44" / "20:44:36" ↔ same           (HH:MM[:SS])
 *   - number: "1 234,56"         ↔ "1234.56"         (CS locale, on-blur format)
 *   - text:   plain pass-through
 *   - password: type=password
 *
 * Display value (input.value()) = formatted display ("+420 777 180 511")
 * Raw value (input.rawValue()) = canonical storage ("+420777180511" / ISO date)
 *
 * States: enabled | disabled | readonly | error (invalid + msg) | valid
 *
 * Usage:
 *
 *   const inp = new ErpInput(container, {
 *     type: "phone",
 *     value: "+420777180511",     // initial (raw or display)
 *     label: "Telefon",
 *     placeholder: "+420 777 180 511",
 *     required: true,
 *     onChange: (display) => { ... },               // every keystroke
 *     onValidatedChange: (raw, isValid) => { ... }, // on blur, after validation
 *     onBlur: (raw) => { ... },
 *     onEnter: (raw, isValid) => { ... },           // Enter key
 *   });
 *
 *   inp.value();      // "+420 777 180 511" (display)
 *   inp.rawValue();   // "+420777180511" (canonical)
 *   inp.isValid();    // true
 *   inp.setValue("+420 778 117 879");
 *   inp.setError("Custom error message");
 *   inp.focus();
 *   inp.destroy();
 *
 * Phase B+6.2 (5.5.2026).
 */
(function (global) {
  "use strict";

  // Phase JS-9 (18.5.2026): mutual immunity wrap pro Module Health visibility.
  const _loader = (typeof global !== "undefined" && global._erpLoadModule)
    ? global._erpLoadModule
    : function (id, ver, fn) { try { fn(); } catch (e) { console.error("[" + id + "] init failed:", e); } };

  _loader("input.js", "v1.0.0", function () {


  const TYPES = ["text", "phone", "ico", "dic", "date", "time", "number", "password", "email"];

  function _esc(s) {
    return String(s).replace(/[&<>"']/g, c =>
      ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])
    );
  }

  // ── Mask formatters / validators per type ────────────────────────────

  const MASKS = {
    text: {
      format: (raw) => raw,
      toRaw: (display) => display,
      validate: (display, raw) => ({ valid: true, error: null }),
    },

    password: {
      format: (raw) => raw,
      toRaw: (display) => display,
      validate: (display, raw) => ({ valid: true, error: null }),
    },

    email: {
      format: (raw) => raw.trim(),
      toRaw: (display) => display.trim().toLowerCase(),
      validate: (display, raw) => {
        if (!raw) return { valid: true, error: null };
        const ok = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(raw);
        return ok
          ? { valid: true, error: null }
          : { valid: false, error: "Neplatný email" };
      },
    },

    phone: {
      format: (raw) => {
        // Pokud začíná +, mezinárodní — formatuj +XXX YYY YYY YYY
        if (raw.trim().startsWith("+")) {
          const cleaned = raw.replace(/[^\d+]/g, "");
          // +420 777 180 511 (CZ) — group 3-3-3 po prefix
          const m = cleaned.match(/^(\+\d{1,4})(\d*)$/);
          if (!m) return cleaned;
          const prefix = m[1];
          const body = m[2];
          let formatted = "";
          for (let i = 0; i < body.length; i += 3) {
            formatted += " " + body.slice(i, i + 3);
          }
          return (prefix + formatted).trim();
        }
        // Local CZ format: 9 digits, group 3-3-3
        const digits = raw.replace(/\D/g, "").slice(0, 9);
        if (digits.length > 6) return digits.slice(0, 3) + " " + digits.slice(3, 6) + " " + digits.slice(6);
        if (digits.length > 3) return digits.slice(0, 3) + " " + digits.slice(3);
        return digits;
      },
      toRaw: (display) => display.replace(/\s/g, ""),
      validate: (display, raw) => {
        if (!raw) return { valid: true, error: null };
        // CZ local: 9 digits; international: + + 9-15 digits
        const local9 = /^\d{9}$/.test(raw);
        const intl = /^\+\d{9,15}$/.test(raw);
        return (local9 || intl)
          ? { valid: true, error: null }
          : { valid: false, error: "Telefon: 9 číslic, +420 volitelné" };
      },
    },

    ico: {
      format: (raw) => {
        const digits = raw.replace(/\D/g, "").slice(0, 8);
        // Group by 2: "27 96 48 54"
        return digits.replace(/(.{2})(?=.)/g, "$1 ");
      },
      toRaw: (display) => display.replace(/\s/g, ""),
      validate: (display, raw) => {
        if (!raw) return { valid: true, error: null };
        if (raw.length !== 8 || !/^\d{8}$/.test(raw)) {
          return { valid: false, error: "IČO: 8 číslic" };
        }
        // Mod-11 checksum (standard CZ IČO algoritmus)
        const weights = [8, 7, 6, 5, 4, 3, 2];
        let sum = 0;
        for (let i = 0; i < 7; i++) sum += parseInt(raw[i], 10) * weights[i];
        const remainder = sum % 11;
        let check = 11 - remainder;
        if (check === 10) check = 0;
        else if (check === 11) check = 1;
        if (parseInt(raw[7], 10) !== check) {
          return { valid: false, error: "Neplatné IČO (kontrolní součet)" };
        }
        return { valid: true, error: null };
      },
    },

    dic: {
      format: (raw) => {
        // CZ + 8-10 digits, uppercase
        const upper = raw.toUpperCase().replace(/\s/g, "");
        if (upper.startsWith("CZ")) {
          const body = upper.slice(2).replace(/\D/g, "").slice(0, 10);
          return "CZ" + body;
        }
        // Pokud user píše bez prefixu, auto-add CZ pokud začíná číslicí
        const digits = upper.replace(/\D/g, "").slice(0, 10);
        return digits ? "CZ" + digits : "";
      },
      toRaw: (display) => display.toUpperCase().replace(/\s/g, ""),
      validate: (display, raw) => {
        if (!raw) return { valid: true, error: null };
        const m = raw.match(/^CZ(\d{8,10})$/);
        return m
          ? { valid: true, error: null }
          : { valid: false, error: "DIČ: CZ + 8-10 číslic" };
      },
    },

    date: {
      // While typing, allow free input — re-format only on blur via setValue
      format: (raw) => raw,
      toRaw: (display) => {
        // "25.5.1972" → "1972-05-25"
        const m = display.trim().match(/^(\d{1,2})\.(\d{1,2})\.(\d{4})$/);
        if (!m) return display.trim();  // not parseable, return as-is
        const d = m[1].padStart(2, "0");
        const mo = m[2].padStart(2, "0");
        return m[3] + "-" + mo + "-" + d;
      },
      validate: (display, raw) => {
        if (!display.trim()) return { valid: true, error: null };
        const m = display.trim().match(/^(\d{1,2})\.(\d{1,2})\.(\d{4})$/);
        if (!m) return { valid: false, error: "Datum: D.M.RRRR (např. 25.5.1972)" };
        const d = parseInt(m[1], 10), mo = parseInt(m[2], 10), y = parseInt(m[3], 10);
        const date = new Date(y, mo - 1, d);
        if (date.getFullYear() !== y || date.getMonth() !== mo - 1 || date.getDate() !== d) {
          return { valid: false, error: "Neplatné datum" };
        }
        return { valid: true, error: null };
      },
    },

    time: {
      format: (raw) => raw,
      toRaw: (display) => {
        const m = display.trim().match(/^(\d{1,2}):(\d{2})(:(\d{2}))?$/);
        if (!m) return display.trim();
        const h = m[1].padStart(2, "0");
        const min = m[2];
        const s = m[4] ? m[4] : "00";
        return h + ":" + min + ":" + s;
      },
      validate: (display, raw) => {
        if (!display.trim()) return { valid: true, error: null };
        const m = display.trim().match(/^(\d{1,2}):(\d{2})(:(\d{2}))?$/);
        if (!m) return { valid: false, error: "Čas: HH:MM nebo HH:MM:SS" };
        const h = parseInt(m[1], 10), mn = parseInt(m[2], 10), s = m[4] ? parseInt(m[4], 10) : 0;
        if (h > 23 || mn > 59 || s > 59) {
          return { valid: false, error: "Neplatný čas" };
        }
        return { valid: true, error: null };
      },
    },

    number: {
      // While typing, allow free input. Format on setValue / blur via re-call.
      format: (raw) => raw,
      toRaw: (display) => {
        // "1 234,56" → "1234.56"
        return display.replace(/\s/g, "").replace(",", ".");
      },
      validate: (display, raw) => {
        if (!display.trim()) return { valid: true, error: null };
        const cleaned = display.replace(/\s/g, "").replace(",", ".");
        const n = parseFloat(cleaned);
        if (isNaN(n) || !isFinite(n)) {
          return { valid: false, error: "Neplatné číslo" };
        }
        return { valid: true, error: null };
      },
      // Special: format on blur for display canonization
      formatOnBlur: (display) => {
        const cleaned = display.replace(/\s/g, "").replace(",", ".");
        const n = parseFloat(cleaned);
        if (isNaN(n) || !isFinite(n)) return display;
        // CS locale: "1 234,56" — non-breaking space jako thousands separator
        const parts = n.toString().split(".");
        const intPart = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, " ");
        return parts.length > 1 ? intPart + "," + parts[1] : intPart;
      },
    },
  };

  // ── Component class ────────────────────────────────────────────────

  class ErpInput {
    constructor(container, options) {
      this.container = container || null;
      this.options = Object.assign({
        type: "text",
        value: "",
        label: null,
        placeholder: null,
        required: false,
        readonly: false,
        disabled: false,
        maxLength: null,
        autoFocus: false,
        hint: null,            // helper text below input
        prefix: null,          // visual prefix inside input (read-only marker)
        suffix: null,          // visual suffix
        onChange: null,        // (display) => void
        onValidatedChange: null,  // (raw, isValid) => void
        onBlur: null,          // (raw) => void
        onFocus: null,
        onEnter: null,         // (raw, isValid) => void
      }, options || {});

      if (TYPES.indexOf(this.options.type) === -1) {
        console.warn("ErpInput: unknown type '" + this.options.type + "', falling back to text");
        this.options.type = "text";
      }

      this._mask = MASKS[this.options.type];
      this._destroyed = false;
      this._displayValue = "";
      this._rawValue = "";
      this._isValid = true;
      this._errorMsg = null;
      this._render();

      if (this.options.value !== "" && this.options.value != null) {
        this.setValue(this.options.value);
      }
      if (this.options.autoFocus) {
        setTimeout(() => this.focus(), 50);
      }
    }

    _render() {
      this.wrapper = document.createElement("div");
      this.wrapper.className = "erp-input-wrapper erp-input-type-" + this.options.type;

      // Label
      if (this.options.label) {
        const lbl = document.createElement("label");
        lbl.className = "erp-input-label";
        lbl.textContent = this.options.label;
        if (this.options.required) {
          const req = document.createElement("span");
          req.className = "erp-input-required";
          req.textContent = " *";
          lbl.appendChild(req);
        }
        this.wrapper.appendChild(lbl);
      }

      // Input row (prefix/input/suffix flex container)
      const row = document.createElement("div");
      row.className = "erp-input-row";

      if (this.options.prefix) {
        const prefix = document.createElement("span");
        prefix.className = "erp-input-prefix";
        prefix.textContent = this.options.prefix;
        row.appendChild(prefix);
      }

      this.input = document.createElement("input");
      this.input.className = "erp-input";
      this.input.type = this._htmlInputType();
      if (this.options.placeholder) this.input.placeholder = this.options.placeholder;
      // B+10++++++++ (drobnost 6.5.2026 večer): read-only gate přesunut
      // k save flow (analog FormList). Marti: "povol i ostatni komponenty,
      // at nejsou read only... checkboxy a inputy". V Phase A je vše save
      // no-op, v Phase C bude save flow gate isFieldReadOnly per field.
      if (this.options.disabled) this.input.disabled = true;
      if (this.options.maxLength) this.input.maxLength = this.options.maxLength;
      row.appendChild(this.input);

      if (this.options.suffix) {
        const suffix = document.createElement("span");
        suffix.className = "erp-input-suffix";
        suffix.textContent = this.options.suffix;
        row.appendChild(suffix);
      }

      this.wrapper.appendChild(row);

      // Hint / error message
      this.errorEl = document.createElement("span");
      this.errorEl.className = "erp-input-error";
      this.errorEl.hidden = true;
      this.wrapper.appendChild(this.errorEl);

      if (this.options.hint) {
        this.hintEl = document.createElement("span");
        this.hintEl.className = "erp-input-hint";
        this.hintEl.textContent = this.options.hint;
        this.wrapper.appendChild(this.hintEl);
      }

      // Events
      this.input.addEventListener("input", (ev) => this._handleInput(ev));
      this.input.addEventListener("blur", (ev) => this._handleBlur(ev));
      this.input.addEventListener("focus", (ev) => this._handleFocus(ev));
      this.input.addEventListener("keydown", (ev) => this._handleKeydown(ev));

      if (this.container) this.container.appendChild(this.wrapper);
    }

    _htmlInputType() {
      switch (this.options.type) {
        case "password": return "password";
        case "email": return "email";
        case "phone": return "tel";
        default: return "text";  // we control formatting manually
      }
    }

    _handleInput(ev) {
      const raw = ev.target.value;
      const cursor = ev.target.selectionStart;
      const formatted = this._mask.format(raw);
      if (formatted !== raw) {
        ev.target.value = formatted;
        // Best-effort cursor position
        const delta = formatted.length - raw.length;
        try {
          ev.target.setSelectionRange(cursor + delta, cursor + delta);
        } catch (e) {}
      }
      this._displayValue = formatted;
      this._rawValue = this._mask.toRaw(formatted);
      // Clear error visual on typing (error shows again on blur)
      if (!this._isValid) this._clearErrorVisual();

      if (typeof this.options.onChange === "function") {
        try { this.options.onChange(this._displayValue); }
        catch (e) { console.warn("ErpInput onChange error:", e); }
      }
    }

    _handleBlur(ev) {
      // Number type — re-format on blur (1 234,56)
      if (this._mask.formatOnBlur) {
        const reformatted = this._mask.formatOnBlur(this._displayValue);
        if (reformatted !== this._displayValue) {
          this.input.value = reformatted;
          this._displayValue = reformatted;
          this._rawValue = this._mask.toRaw(reformatted);
        }
      }

      const result = this._mask.validate(this._displayValue, this._rawValue);
      if (this.options.required && !this._rawValue) {
        this._isValid = false;
        this._errorMsg = "Povinné pole";
      } else {
        this._isValid = result.valid;
        this._errorMsg = result.error;
      }
      this._updateValidationVisual();

      if (typeof this.options.onValidatedChange === "function") {
        try { this.options.onValidatedChange(this._rawValue, this._isValid); }
        catch (e) { console.warn("ErpInput onValidatedChange error:", e); }
      }
      if (typeof this.options.onBlur === "function") {
        try { this.options.onBlur(this._rawValue); }
        catch (e) { console.warn("ErpInput onBlur error:", e); }
      }
    }

    _handleFocus(ev) {
      if (typeof this.options.onFocus === "function") {
        try { this.options.onFocus(ev); }
        catch (e) {}
      }
    }

    _handleKeydown(ev) {
      if (ev.key === "Enter" && typeof this.options.onEnter === "function") {
        // Trigger blur first to validate, then call onEnter
        this.input.blur();
        try { this.options.onEnter(this._rawValue, this._isValid); }
        catch (e) {}
      }
    }

    _updateValidationVisual() {
      if (!this._isValid && this._errorMsg) {
        this.errorEl.textContent = this._errorMsg;
        this.errorEl.hidden = false;
        this.input.classList.add("erp-input-invalid");
      } else {
        this.errorEl.hidden = true;
        this.input.classList.remove("erp-input-invalid");
      }
    }

    _clearErrorVisual() {
      this.errorEl.hidden = true;
      this.input.classList.remove("erp-input-invalid");
    }

    // ── Public API ────────────────────────────────────────────────────

    /** Returns underlying <input> DOM element. */
    element() { return this.input; }

    /** Returns wrapper <div> (label + input + error). */
    wrapperElement() { return this.wrapper; }

    /** Display value (formatted, jak vidí user). */
    value() { return this._displayValue; }

    /** Raw canonical value (storage format — ISO date, E.164 phone, atd.). */
    rawValue() { return this._rawValue; }

    isValid() { return this._isValid; }

    /**
     * Set value programmatically. Accepts raw nebo display — auto-formats.
     */
    setValue(v) {
      if (this._destroyed) return;
      const str = (v == null) ? "" : String(v);
      const formatted = this._mask.format(str);
      this.input.value = formatted;
      this._displayValue = formatted;
      this._rawValue = this._mask.toRaw(formatted);
      // Validate but don't show error visual unless invalid
      const result = this._mask.validate(this._displayValue, this._rawValue);
      this._isValid = result.valid;
      this._errorMsg = result.error;
      this._updateValidationVisual();
    }

    /** Set explicit error message (overrides validation). */
    setError(msg) {
      if (this._destroyed) return;
      this._errorMsg = msg;
      this._isValid = !msg;
      this._updateValidationVisual();
    }

    setReadonly(readonly) {
      if (this._destroyed) return;
      // B+10++++++++ (6.5.2026): readonly tracked v options pro save flow
      // gate (Phase C edit pipeline), ale UI input zůstane editovatelný.
      this.options.readonly = !!readonly;
    }

    setDisabled(disabled) {
      if (this._destroyed) return;
      this.options.disabled = !!disabled;
      this.input.disabled = !!disabled;
    }

    setLabel(label) {
      if (this._destroyed) return;
      this.options.label = label;
      const lblEl = this.wrapper.querySelector(".erp-input-label");
      if (lblEl) {
        lblEl.textContent = label;
        if (this.options.required) {
          const req = document.createElement("span");
          req.className = "erp-input-required";
          req.textContent = " *";
          lblEl.appendChild(req);
        }
      }
    }

    focus() {
      if (this._destroyed || !this.input) return;
      this.input.focus();
    }

    select() {
      if (this._destroyed || !this.input) return;
      try { this.input.select(); } catch (e) {}
    }

    /** Force re-validation (useful after external state change). */
    validate() {
      if (this._destroyed) return false;
      const result = this._mask.validate(this._displayValue, this._rawValue);
      if (this.options.required && !this._rawValue) {
        this._isValid = false;
        this._errorMsg = "Povinné pole";
      } else {
        this._isValid = result.valid;
        this._errorMsg = result.error;
      }
      this._updateValidationVisual();
      return this._isValid;
    }

    destroy() {
      if (this._destroyed) return;
      this._destroyed = true;
      if (this.wrapper && this.wrapper.parentNode) {
        this.wrapper.parentNode.removeChild(this.wrapper);
      }
      this.wrapper = null;
      this.input = null;
      this.errorEl = null;
      this.hintEl = null;
    }
  }

  // ── Factory + helpers ────────────────────────────────────────────────

  ErpInput.create = function (options) {
    const inp = new ErpInput(null, options);
    return inp.wrapperElement();
  };

  ErpInput.MASKS = MASKS;  // expose pro custom validation extending

  global.ErpInput = ErpInput;

  }); // _erpLoadModule end
})(typeof window !== "undefined" ? window : this);
