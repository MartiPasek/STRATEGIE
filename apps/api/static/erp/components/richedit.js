/**
 * ErpRichEdit — UI Kit multi-line code editor wrapper kolem Ace Editor.
 *
 * Phase B+6.8 (6.5.2026 večer). Marti's spec: typ 4 RichEdit z Centrály 1.
 * Screenshot ukazuje editor pro DefView SQL + INSERT/UPDATE/DELETE bloky
 * (každý self-contained editor s line numbers + SQL syntax highlight).
 *
 * Engine: Ace Editor 1.32 z CDN (~120KB minified, no-conflict build).
 *   <script src="https://cdn.jsdelivr.net/npm/ace-builds@1.32.6/src-min-noconflict/ace.js">
 *
 * API parita s ErpInput:
 *   - new ErpRichEdit(container, opts)
 *   - opts: { value, language, readonly, label, hint, height, lineNumbers,
 *            wrap, autoFocus, onChange, onBlur, onFocus, onCtrlEnter,
 *            theme }
 *   - value() / setValue(text) / setLanguage(lang) / setReadonly(bool)
 *   - focus() / destroy() / resize() / isValid() / setError(msg)
 *
 * Languages: "sql" (default), "javascript", "html", "json", "css", "text"
 * Themes: "monokai" (default — dark), "tomorrow_night", "dracula",
 *         "github" (light fallback)
 *
 * Phase A read-only mode: opts.readonly=true → editor.setReadOnly(true).
 * User pořád smí scrollovat, copy text, navigovat kurzorem (read-only =
 * neměnit text, ne *zakázat* interakci). Save flow gate (Phase C) později
 * — consistent s ErpInput / Checkbox / Date / Memo refactorem dnes.
 *
 * Marti's edit pipeline (Phase C): readonly=false → save callback collects
 * value() + posílá UPDATE statement.
 */
(function (global) {
  "use strict";

  const LANGUAGES = ["sql", "javascript", "html", "json", "css", "text", "markdown"];
  const THEMES = ["monokai", "tomorrow_night", "dracula", "github", "chrome"];

  function _esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, c =>
      ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])
    );
  }

  /**
   * Detect Ace global. CDN script `ace.js` exposes window.ace (UMD).
   */
  function _aceReady() {
    return (typeof global.ace === "object")
      && global.ace
      && typeof global.ace.edit === "function";
  }

  class ErpRichEdit {
    constructor(container, options) {
      this.container = container || null;
      this.options = Object.assign({
        value: "",
        language: "sql",         // sql|javascript|html|json|css|text|markdown
        theme: "monokai",        // monokai|tomorrow_night|dracula|github
        readonly: false,
        label: null,
        placeholder: null,       // Ace nemá native placeholder, jen hint
        hint: null,
        height: "200px",         // CSS height pro editor wrapper
        lineNumbers: true,
        wrap: false,             // word wrap
        tabSize: 2,
        useSoftTabs: true,
        showPrintMargin: false,
        highlightActiveLine: true,
        fontSize: 13,
        autoFocus: false,
        onChange: null,           // (value) => void  — debounced
        onBlur: null,
        onFocus: null,
        onCtrlEnter: null,        // (value) => void  — Ctrl+Enter shortcut
      }, options || {});

      if (LANGUAGES.indexOf(this.options.language) === -1) {
        console.warn("ErpRichEdit: unknown language '" + this.options.language + "', falling back to text");
        this.options.language = "text";
      }

      this._destroyed = false;
      this._editor = null;        // Ace instance, set v _initEditor
      this._isValid = true;
      this._errorMsg = null;
      this._changeDebounce = null;
      this._render();
      this._initEditor();
    }

    // ── Render ────────────────────────────────────────────────────

    _render() {
      this.wrapper = document.createElement("div");
      this.wrapper.className = "erp-richedit-wrapper erp-richedit-lang-" + this.options.language;

      // Label
      if (this.options.label) {
        const lbl = document.createElement("label");
        lbl.className = "erp-input-label";  // reuse ErpInput label styling
        lbl.textContent = this.options.label;
        this.wrapper.appendChild(lbl);
      }

      // Editor host element — Ace replaces innerHTML
      this.editorHost = document.createElement("div");
      this.editorHost.className = "erp-richedit-editor";
      this.editorHost.style.height = this.options.height;
      this.editorHost.style.width = "100%";
      this.wrapper.appendChild(this.editorHost);

      // Error / hint
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

      if (this.container) this.container.appendChild(this.wrapper);
    }

    _initEditor() {
      if (this._destroyed) return;
      // Ace může být not-yet-loaded (CDN async). Pojď retry max 20× × 50ms = 1s.
      if (!_aceReady()) {
        this._aceRetries = (this._aceRetries || 0) + 1;
        if (this._aceRetries > 20) {
          console.warn("ErpRichEdit: ace global not ready after 1s — fallback na <textarea>");
          this._initFallback();
          return;
        }
        setTimeout(() => this._initEditor(), 50);
        return;
      }
      try {
        this._editor = global.ace.edit(this.editorHost);
        this._editor.setTheme("ace/theme/" + this.options.theme);
        this._editor.session.setMode("ace/mode/" + this.options.language);
        this._editor.setOptions({
          showLineNumbers: this.options.lineNumbers,
          showGutter: this.options.lineNumbers,
          fontSize: this.options.fontSize,
          tabSize: this.options.tabSize,
          useSoftTabs: this.options.useSoftTabs,
          showPrintMargin: this.options.showPrintMargin,
          highlightActiveLine: this.options.highlightActiveLine,
          readOnly: !!this.options.readonly,
          wrap: !!this.options.wrap,
          // B+6.8 (6.5.2026): nezobrazovat Ace warning toast pro mode loading
          fadeFoldWidgets: true,
        });
        // Initial value — pokud byl value v opts
        if (this.options.value != null && this.options.value !== "") {
          this._editor.setValue(String(this.options.value), -1);  // -1 = cursor at start
        }
        // Events
        this._editor.session.on("change", () => this._onChange());
        this._editor.on("blur", () => this._onBlur());
        this._editor.on("focus", () => this._onFocus());
        // Ctrl+Enter shortcut
        if (typeof this.options.onCtrlEnter === "function") {
          this._editor.commands.addCommand({
            name: "erpCtrlEnter",
            bindKey: { win: "Ctrl-Enter", mac: "Command-Enter" },
            exec: () => {
              try { this.options.onCtrlEnter(this.value()); } catch (e) {}
            },
          });
        }
        if (this.options.autoFocus) {
          setTimeout(() => this.focus(), 50);
        }
      } catch (e) {
        console.warn("ErpRichEdit init failed:", e);
        this._initFallback();
      }
    }

    /**
     * Fallback při Ace failure — plain textarea s monospace font.
     * Lepší něco než nic; user dostane editovatelný text bez syntax highlight.
     */
    _initFallback() {
      this.editorHost.innerHTML = "";
      this._fallbackTextarea = document.createElement("textarea");
      this._fallbackTextarea.className = "erp-richedit-fallback";
      this._fallbackTextarea.style.width = "100%";
      this._fallbackTextarea.style.height = "100%";
      this._fallbackTextarea.value = this.options.value || "";
      if (this.options.readonly) this._fallbackTextarea.readOnly = true;
      this._fallbackTextarea.addEventListener("input", () => this._onChange());
      this._fallbackTextarea.addEventListener("blur", () => this._onBlur());
      this._fallbackTextarea.addEventListener("focus", () => this._onFocus());
      this.editorHost.appendChild(this._fallbackTextarea);
    }

    // ── Public API ───────────────────────────────────────────────

    value() {
      if (this._editor) return this._editor.getValue();
      if (this._fallbackTextarea) return this._fallbackTextarea.value;
      return this.options.value || "";
    }

    rawValue() {
      return this.value();
    }

    setValue(text) {
      const s = (text == null) ? "" : String(text);
      if (this._editor) {
        this._editor.setValue(s, -1);  // -1 = cursor at start, no selection
      } else if (this._fallbackTextarea) {
        this._fallbackTextarea.value = s;
      } else {
        this.options.value = s;  // pre-init buffer
      }
    }

    setLanguage(lang) {
      if (LANGUAGES.indexOf(lang) === -1) return;
      this.options.language = lang;
      if (this._editor) {
        this._editor.session.setMode("ace/mode/" + lang);
      }
      this.wrapper.className = "erp-richedit-wrapper erp-richedit-lang-" + lang;
    }

    setReadonly(readonly) {
      this.options.readonly = !!readonly;
      // B+10++++++++ (6.5.2026): readonly tracked v options pro save flow.
      // UI editor zůstává editovatelný — Phase C save flow gate per field.
      // Konzistence s Input/Checkbox/Dropdown/Date/Memo refactorem.
    }

    isValid() {
      return this._isValid;
    }

    setError(msg) {
      if (msg) {
        this.wrapper.classList.add("erp-richedit-invalid");
        this.errorEl.textContent = msg;
        this.errorEl.hidden = false;
        this._isValid = false;
        this._errorMsg = msg;
      } else {
        this.wrapper.classList.remove("erp-richedit-invalid");
        this.errorEl.hidden = true;
        this._isValid = true;
        this._errorMsg = null;
      }
    }

    focus() {
      if (this._editor) {
        try { this._editor.focus(); } catch (e) {}
      } else if (this._fallbackTextarea) {
        this._fallbackTextarea.focus();
      }
    }

    /** UI Kit pattern — vrací wrapper element (pro ErpFormSection.addField()
     *  nebo ErpForm dispatch loop). */
    wrapperElement() { return this.wrapper; }

    /**
     * Notify Ace, že container resizoval (např. po tabsheet switch
     * nebo zoom toggle). Bez resize Ace render je sticky až do user
     * interaction.
     */
    resize() {
      if (this._editor) {
        try { this._editor.resize(); } catch (e) {}
      }
    }

    destroy() {
      if (this._destroyed) return;
      this._destroyed = true;
      if (this._changeDebounce) {
        clearTimeout(this._changeDebounce);
        this._changeDebounce = null;
      }
      if (this._editor) {
        try { this._editor.destroy(); } catch (e) {}
        this._editor = null;
      }
      if (this.wrapper && this.wrapper.parentNode) {
        this.wrapper.parentNode.removeChild(this.wrapper);
      }
    }

    // ── Internal ────────────────────────────────────────────────

    _onChange() {
      // Debounce 150ms — Ace fire change na každý char
      if (this._changeDebounce) clearTimeout(this._changeDebounce);
      this._changeDebounce = setTimeout(() => {
        this._changeDebounce = null;
        if (typeof this.options.onChange === "function") {
          try { this.options.onChange(this.value()); } catch (e) {}
        }
      }, 150);
    }

    _onBlur() {
      if (typeof this.options.onBlur === "function") {
        try { this.options.onBlur(this.value()); } catch (e) {}
      }
    }

    _onFocus() {
      if (typeof this.options.onFocus === "function") {
        try { this.options.onFocus(); } catch (e) {}
      }
    }
  }

  global.ErpRichEdit = ErpRichEdit;
})(typeof window !== "undefined" ? window : globalThis);
