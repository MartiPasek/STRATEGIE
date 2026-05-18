/**
 * ErpMemo — UI Kit multi-line textarea s auto-resize a char counter.
 *
 * Phase B+6.7 (6.5.2026). Marti's spec: "ErpDate, ErpMemo..." po
 * Phase B+8.1 user state persistence.
 *
 * API matching ErpInput:
 *   - constructor: new ErpMemo(container, opts)
 *   - methods: value() / rawValue() / setValue() / isValid() / setError()
 *              focus() / destroy()
 *
 * Features:
 *   - Auto-resize: rows grow with content do max-rows, pak scroll
 *   - Char counter (display only když maxLength definovaný)
 *   - States: enabled / disabled / readonly / error
 *   - Dark theme via existing CSS tokens (--bg, --border, --accent)
 *
 * Usage:
 *
 *   const m = new ErpMemo(container, {
 *     value: "...",
 *     label: "Poznámka",
 *     placeholder: "Zadej text...",
 *     rows: 4,           // initial visible rows
 *     maxRows: 12,       // auto-grow up to this many rows
 *     maxLength: 2000,   // char limit + counter display
 *     required: false,
 *     readonly: false,
 *     disabled: false,
 *     hint: "Stiskni Ctrl+Enter pro potvrdit",
 *     autoFocus: false,
 *     onChange: (val) => { ... },              // every keystroke
 *     onBlur: (val) => { ... },
 *     onCtrlEnter: (val) => { ... },           // Ctrl+Enter shortcut
 *   });
 *
 *   m.value();      // current text
 *   m.rawValue();   // alias to value() (no formatting transform for memo)
 *   m.setValue(s);
 *   m.focus();
 *   m.destroy();
 */
(function (global) {
  "use strict";

  // Phase JS-9 (18.5.2026): mutual immunity wrap pro Module Health visibility.
  const _loader = (typeof global !== "undefined" && global._erpLoadModule)
    ? global._erpLoadModule
    : function (id, ver, fn) { try { fn(); } catch (e) { console.error("[" + id + "] init failed:", e); } };

  _loader("memo.js", "v1.0.0", function () {


  function _esc(s) {
    return String(s).replace(/[&<>"']/g, c =>
      ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])
    );
  }

  class ErpMemo {
    constructor(container, options) {
      this.container = container || null;
      this.options = Object.assign({
        value: "",
        label: null,
        placeholder: null,
        rows: 4,            // initial visible rows
        maxRows: 12,        // auto-grow cap
        maxLength: null,    // char limit (also enables counter)
        required: false,
        readonly: false,
        disabled: false,
        hint: null,
        autoFocus: false,
        onChange: null,
        onBlur: null,
        onFocus: null,
        onCtrlEnter: null,
      }, options || {});

      this._destroyed = false;
      this._isValid = true;
      this._errorMsg = null;
      this._lineHeight = 0;  // computed po render
      this._render();

      if (this.options.value !== "" && this.options.value != null) {
        this.setValue(this.options.value);
      } else {
        this._autoResize();
        this._updateCounter();
      }
      if (this.options.autoFocus) {
        setTimeout(() => this.focus(), 50);
      }
    }

    // ── Render ────────────────────────────────────────────────────

    _render() {
      this.wrapper = document.createElement("div");
      this.wrapper.className = "erp-memo-wrapper";

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

      // Textarea row (no flex prefix/suffix unlike input)
      const row = document.createElement("div");
      row.className = "erp-input-row erp-memo-row";

      this.textarea = document.createElement("textarea");
      this.textarea.className = "erp-input erp-memo-textarea";
      this.textarea.rows = this.options.rows;
      if (this.options.placeholder) this.textarea.placeholder = this.options.placeholder;
      // B+10++++++++ (6.5.2026): readonly gate jen save flow (Phase C).
      // UI textarea volně editovatelný.
      if (this.options.disabled) this.textarea.disabled = true;
      if (this.options.maxLength) this.textarea.maxLength = this.options.maxLength;
      row.appendChild(this.textarea);

      this.wrapper.appendChild(row);

      // Footer (counter + error/hint)
      this.footer = document.createElement("div");
      this.footer.className = "erp-memo-footer";

      this.errorEl = document.createElement("span");
      this.errorEl.className = "erp-input-error";
      this.errorEl.hidden = true;
      this.footer.appendChild(this.errorEl);

      if (this.options.hint) {
        this.hintEl = document.createElement("span");
        this.hintEl.className = "erp-input-hint";
        this.hintEl.textContent = this.options.hint;
        this.footer.appendChild(this.hintEl);
      }

      this.counterEl = document.createElement("span");
      this.counterEl.className = "erp-memo-counter";
      if (!this.options.maxLength) this.counterEl.hidden = true;
      this.footer.appendChild(this.counterEl);

      this.wrapper.appendChild(this.footer);

      // Events
      this.textarea.addEventListener("input", () => this._onInput());
      this.textarea.addEventListener("blur", () => this._onBlur());
      this.textarea.addEventListener("focus", () => this._onFocus());
      this.textarea.addEventListener("keydown", (ev) => this._onKeydown(ev));

      if (this.container) this.container.appendChild(this.wrapper);
    }

    // ── Public API ───────────────────────────────────────────────

    value() {
      return this.textarea.value;
    }

    rawValue() {
      return this.textarea.value;
    }

    setValue(v) {
      const s = (v == null) ? "" : String(v);
      this.textarea.value = s;
      this._autoResize();
      this._updateCounter();
      this._validate();
    }

    isValid() {
      return this._isValid;
    }

    setError(msg) {
      if (msg) {
        this.textarea.classList.add("erp-input-invalid");
        this.errorEl.textContent = msg;
        this.errorEl.hidden = false;
        this._isValid = false;
        this._errorMsg = msg;
      } else {
        this.textarea.classList.remove("erp-input-invalid");
        this.errorEl.hidden = true;
        this._isValid = true;
        this._errorMsg = null;
      }
    }

    focus() {
      if (this.textarea) this.textarea.focus();
    }

    destroy() {
      if (this._destroyed) return;
      this._destroyed = true;
      if (this.wrapper && this.wrapper.parentNode) {
        this.wrapper.parentNode.removeChild(this.wrapper);
      }
    }

    // ── Internal ────────────────────────────────────────────────

    _validate() {
      const v = this.textarea.value;
      if (this.options.required && !v.trim()) {
        this.setError("Povinné");
        return;
      }
      this.setError(null);
    }

    _onInput() {
      this._autoResize();
      this._updateCounter();
      this._validate();
      if (typeof this.options.onChange === "function") {
        try { this.options.onChange(this.textarea.value); } catch (e) {}
      }
    }

    _onBlur() {
      this._validate();
      if (typeof this.options.onBlur === "function") {
        try { this.options.onBlur(this.textarea.value); } catch (e) {}
      }
    }

    _onFocus() {
      if (typeof this.options.onFocus === "function") {
        try { this.options.onFocus(); } catch (e) {}
      }
    }

    _onKeydown(ev) {
      if ((ev.ctrlKey || ev.metaKey) && ev.key === "Enter") {
        ev.preventDefault();
        if (typeof this.options.onCtrlEnter === "function") {
          try { this.options.onCtrlEnter(this.textarea.value); } catch (e) {}
        }
      }
    }

    /**
     * Auto-grow textarea height to fit content, up to maxRows.
     * Beyond that, scrollbar kicks in.
     */
    _autoResize() {
      if (!this.textarea) return;
      // Lazy compute line-height (depends on font, padding)
      if (!this._lineHeight) {
        // Reset to single row to measure
        const original = this.textarea.style.height;
        this.textarea.style.height = "auto";
        this.textarea.rows = 1;
        const oneRowHeight = this.textarea.scrollHeight;
        this.textarea.rows = this.options.rows;
        this._lineHeight = oneRowHeight || 22;
        this.textarea.style.height = original;
      }
      // Reset and re-measure full content
      this.textarea.style.height = "auto";
      const contentHeight = this.textarea.scrollHeight;
      const maxHeight = this._lineHeight * this.options.maxRows;
      const minHeight = this._lineHeight * this.options.rows;
      const targetHeight = Math.max(minHeight, Math.min(contentHeight, maxHeight));
      this.textarea.style.height = targetHeight + "px";
      // Show scrollbar when at cap
      this.textarea.style.overflowY = (contentHeight > maxHeight) ? "auto" : "hidden";
    }

    _updateCounter() {
      if (!this.options.maxLength) return;
      const len = this.textarea.value.length;
      this.counterEl.textContent = len + " / " + this.options.maxLength;
      // Soft warning při blízkosti k limitu
      if (len >= this.options.maxLength) {
        this.counterEl.classList.add("erp-memo-counter-full");
        this.counterEl.classList.remove("erp-memo-counter-near");
      } else if (len >= this.options.maxLength * 0.9) {
        this.counterEl.classList.add("erp-memo-counter-near");
        this.counterEl.classList.remove("erp-memo-counter-full");
      } else {
        this.counterEl.classList.remove("erp-memo-counter-near", "erp-memo-counter-full");
      }
    }
  }

  global.ErpMemo = ErpMemo;

  }); // _erpLoadModule end
})(typeof window !== "undefined" ? window : globalThis);
