/**
 * ErpDropdown — UI Kit single-select dropdown.
 *
 * Custom dark panel (ne native <select>), STRATEGIE BLACK theme.
 *
 * Items:
 *   [
 *     { value: "1", label: "Aktivní" },
 *     { value: "2", label: "Pozastaveno", disabled: true },
 *     { value: null, label: "── Skupina ──", divider: true },
 *     ...
 *   ]
 *
 * States: enabled | disabled | readonly | error | loading
 *
 * Keyboard:
 *   Space / Enter — open panel (when closed) / select highlighted (when open)
 *   Arrow Down / Up — highlight next / previous (open panel if closed)
 *   Escape — close panel without selection
 *   Tab — close panel + move focus
 *   Home / End — first / last enabled item
 *   Type letter — jump to next item starting with that letter
 *
 * Usage:
 *
 *   const dd = new ErpDropdown(container, {
 *     label: "Stav",
 *     value: "1",
 *     items: [
 *       { value: "1", label: "Aktivní" },
 *       { value: "2", label: "Pozastaveno" },
 *     ],
 *     placeholder: "Vyberte...",
 *     required: true,
 *     disabled: false,
 *     onChange: (value, item) => { ... },
 *   });
 *
 *   dd.value();              // "1"
 *   dd.selectedItem();       // {value:"1", label:"Aktivní"}
 *   dd.setValue("2");
 *   dd.setItems(newItems);
 *   dd.setDisabled(true);
 *   dd.setLoading(true);     // shows spinner in trigger
 *   dd.focus();
 *   dd.destroy();
 *
 * Phase B+6.3 (5.5.2026).
 */
(function (global) {
  "use strict";

  // Phase JS-9 (18.5.2026): mutual immunity wrap pro Module Health visibility.
  const _loader = (typeof global !== "undefined" && global._erpLoadModule)
    ? global._erpLoadModule
    : function (id, ver, fn) { try { fn(); } catch (e) { console.error("[" + id + "] init failed:", e); } };

  _loader("dropdown.js", "v1.0.0", function () {


  function _esc(s) {
    return String(s).replace(/[&<>"']/g, c =>
      ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])
    );
  }

  // Globální tracking — jen jeden dropdown otevřený naráz
  let _OPEN_INSTANCE = null;

  class ErpDropdown {
    constructor(container, options) {
      this.container = container || null;
      this.options = Object.assign({
        items: [],
        value: null,
        label: null,
        placeholder: "Vyberte...",
        required: false,
        disabled: false,
        readonly: false,
        loading: false,
        hint: null,
        emptyMessage: "Žádné položky",
        onChange: null,
        onOpen: null,
        onClose: null,
      }, options || {});
      this._destroyed = false;
      this._isOpen = false;
      this._highlightedIdx = -1;
      this._typeBuffer = "";
      this._typeTimeout = null;
      this._render();

      if (this.options.value != null) {
        this.setValue(this.options.value, /*silent*/true);
      }
    }

    _render() {
      this.wrapper = document.createElement("div");
      this.wrapper.className = "erp-dropdown-wrapper";

      // Label
      if (this.options.label) {
        const lbl = document.createElement("label");
        lbl.className = "erp-dropdown-label";
        lbl.textContent = this.options.label;
        if (this.options.required) {
          const req = document.createElement("span");
          req.className = "erp-dropdown-required";
          req.textContent = " *";
          lbl.appendChild(req);
        }
        this.wrapper.appendChild(lbl);
      }

      // Trigger button
      this.trigger = document.createElement("button");
      this.trigger.type = "button";
      this.trigger.className = "erp-dropdown-trigger";
      this.trigger.setAttribute("aria-haspopup", "listbox");
      this.trigger.setAttribute("aria-expanded", "false");
      if (this.options.disabled) this.trigger.disabled = true;

      this.triggerLabel = document.createElement("span");
      this.triggerLabel.className = "erp-dropdown-trigger-label";
      this.triggerLabel.textContent = this.options.placeholder || "";
      this.triggerLabel.classList.add("erp-dropdown-placeholder");
      this.trigger.appendChild(this.triggerLabel);

      const caret = document.createElement("span");
      caret.className = "erp-dropdown-caret";
      caret.setAttribute("aria-hidden", "true");
      caret.innerHTML = "▾";
      this.trigger.appendChild(caret);

      this.wrapper.appendChild(this.trigger);

      // Panel (initially detached, appended on open)
      this.panel = document.createElement("div");
      this.panel.className = "erp-dropdown-panel";
      this.panel.setAttribute("role", "listbox");
      this.panel.setAttribute("tabindex", "-1");

      // Hint / error
      this.errorEl = document.createElement("span");
      this.errorEl.className = "erp-dropdown-error";
      this.errorEl.hidden = true;
      this.wrapper.appendChild(this.errorEl);

      if (this.options.hint) {
        this.hintEl = document.createElement("span");
        this.hintEl.className = "erp-dropdown-hint";
        this.hintEl.textContent = this.options.hint;
        this.wrapper.appendChild(this.hintEl);
      }

      // Events
      this.trigger.addEventListener("click", (ev) => this._handleTriggerClick(ev));
      this.trigger.addEventListener("keydown", (ev) => this._handleTriggerKeydown(ev));

      this._updateLoadingVisual();

      if (this.container) this.container.appendChild(this.wrapper);
    }

    // ── Open / Close panel ──────────────────────────────────────────

    _handleTriggerClick(ev) {
      ev.preventDefault();
      // B+10++++++++ (6.5.2026): readonly gate přesunut k save flow.
      // UI dropdown smí otevřít + select. Disabled / loading drží blokádu.
      if (this.options.disabled || this.options.loading) return;
      if (this._isOpen) this.close();
      else this.open();
    }

    open() {
      if (this._destroyed || this._isOpen) return;
      // B+10++++++++ (6.5.2026): readonly gate přesunut k save flow.
      // UI dropdown smí otevřít + select. Disabled / loading drží blokádu.
      if (this.options.disabled || this.options.loading) return;
      // Close any other open dropdown
      if (_OPEN_INSTANCE && _OPEN_INSTANCE !== this) {
        try { _OPEN_INSTANCE.close(); } catch (e) {}
      }
      _OPEN_INSTANCE = this;
      this._isOpen = true;
      this.trigger.setAttribute("aria-expanded", "true");
      this.wrapper.classList.add("erp-dropdown-open");
      this._renderPanelItems();
      // Position panel below trigger
      this._positionPanel();
      document.body.appendChild(this.panel);
      // Highlight selected item or first enabled
      const selectedIdx = this._findItemIndex(this.options.value);
      this._highlightedIdx = (selectedIdx >= 0)
        ? selectedIdx
        : this._firstEnabledIndex();
      this._updateHighlight();
      this._scrollHighlightedIntoView();
      // Outside click + escape listeners
      this._outsideClickListener = (ev) => {
        if (!this.panel.contains(ev.target) && !this.wrapper.contains(ev.target)) {
          this.close();
        }
      };
      this._escapeListener = (ev) => {
        if (ev.key === "Escape") {
          ev.preventDefault();
          this.close();
          this.trigger.focus();
        }
      };
      this._scrollListener = () => this._positionPanel();
      setTimeout(() => {
        document.addEventListener("mousedown", this._outsideClickListener);
        document.addEventListener("keydown", this._escapeListener);
        window.addEventListener("scroll", this._scrollListener, true);
        window.addEventListener("resize", this._scrollListener);
      }, 0);
      if (typeof this.options.onOpen === "function") {
        try { this.options.onOpen(); } catch (e) {}
      }
    }

    close() {
      if (this._destroyed || !this._isOpen) return;
      this._isOpen = false;
      this.trigger.setAttribute("aria-expanded", "false");
      this.wrapper.classList.remove("erp-dropdown-open");
      if (this.panel.parentNode) {
        this.panel.parentNode.removeChild(this.panel);
      }
      if (_OPEN_INSTANCE === this) _OPEN_INSTANCE = null;
      if (this._outsideClickListener) {
        document.removeEventListener("mousedown", this._outsideClickListener);
        this._outsideClickListener = null;
      }
      if (this._escapeListener) {
        document.removeEventListener("keydown", this._escapeListener);
        this._escapeListener = null;
      }
      if (this._scrollListener) {
        window.removeEventListener("scroll", this._scrollListener, true);
        window.removeEventListener("resize", this._scrollListener);
        this._scrollListener = null;
      }
      if (typeof this.options.onClose === "function") {
        try { this.options.onClose(); } catch (e) {}
      }
    }

    _positionPanel() {
      const rect = this.trigger.getBoundingClientRect();
      const panelMaxHeight = 280;
      const spaceBelow = window.innerHeight - rect.bottom - 8;
      const spaceAbove = rect.top - 8;
      const openUp = spaceBelow < 200 && spaceAbove > spaceBelow;
      this.panel.style.position = "fixed";
      this.panel.style.left = rect.left + "px";
      this.panel.style.minWidth = rect.width + "px";
      this.panel.style.maxWidth = Math.max(rect.width, 260) + "px";
      if (openUp) {
        this.panel.style.bottom = (window.innerHeight - rect.top + 4) + "px";
        this.panel.style.top = "auto";
        this.panel.style.maxHeight = Math.min(panelMaxHeight, spaceAbove - 4) + "px";
      } else {
        this.panel.style.top = (rect.bottom + 4) + "px";
        this.panel.style.bottom = "auto";
        this.panel.style.maxHeight = Math.min(panelMaxHeight, spaceBelow - 4) + "px";
      }
    }

    // ── Panel item rendering ────────────────────────────────────────

    _renderPanelItems() {
      this.panel.innerHTML = "";
      const items = this.options.items || [];
      if (!items.length) {
        const empty = document.createElement("div");
        empty.className = "erp-dropdown-empty";
        empty.textContent = this.options.emptyMessage || "Žádné položky";
        this.panel.appendChild(empty);
        return;
      }
      items.forEach((it, idx) => {
        if (it.divider) {
          const div = document.createElement("div");
          div.className = "erp-dropdown-divider";
          if (it.label) div.textContent = it.label;
          this.panel.appendChild(div);
          return;
        }
        const opt = document.createElement("div");
        opt.className = "erp-dropdown-item";
        opt.setAttribute("role", "option");
        opt.setAttribute("data-erp-idx", String(idx));
        if (it.disabled) opt.classList.add("erp-dropdown-item-disabled");
        if (this._isSelected(it)) {
          opt.classList.add("erp-dropdown-item-selected");
          opt.setAttribute("aria-selected", "true");
        }
        opt.textContent = it.label != null ? String(it.label) : String(it.value);
        opt.addEventListener("mouseenter", () => {
          if (!it.disabled) {
            this._highlightedIdx = idx;
            this._updateHighlight();
          }
        });
        opt.addEventListener("mousedown", (ev) => {
          // mousedown (ne click) — vyhne se outsideClickListener race
          ev.preventDefault();
          if (it.disabled) return;
          this._selectByIndex(idx);
        });
        this.panel.appendChild(opt);
      });
    }

    _updateHighlight() {
      const items = this.panel.querySelectorAll(".erp-dropdown-item");
      items.forEach((el) => {
        const idx = parseInt(el.getAttribute("data-erp-idx"), 10);
        if (idx === this._highlightedIdx) el.classList.add("erp-dropdown-item-highlight");
        else el.classList.remove("erp-dropdown-item-highlight");
      });
    }

    _scrollHighlightedIntoView() {
      const el = this.panel.querySelector('.erp-dropdown-item-highlight');
      if (el && typeof el.scrollIntoView === "function") {
        try { el.scrollIntoView({ block: "nearest" }); } catch (e) {}
      }
    }

    // ── Selection logic ─────────────────────────────────────────────

    _findItemIndex(value) {
      const items = this.options.items || [];
      for (let i = 0; i < items.length; i++) {
        if (items[i].divider) continue;
        if (items[i].value === value) return i;
      }
      return -1;
    }

    _firstEnabledIndex() {
      const items = this.options.items || [];
      for (let i = 0; i < items.length; i++) {
        if (!items[i].divider && !items[i].disabled) return i;
      }
      return -1;
    }

    _lastEnabledIndex() {
      const items = this.options.items || [];
      for (let i = items.length - 1; i >= 0; i--) {
        if (!items[i].divider && !items[i].disabled) return i;
      }
      return -1;
    }

    _nextEnabledIndex(from) {
      const items = this.options.items || [];
      for (let i = from + 1; i < items.length; i++) {
        if (!items[i].divider && !items[i].disabled) return i;
      }
      return from;  // wrap? ne, stay on last
    }

    _prevEnabledIndex(from) {
      const items = this.options.items || [];
      for (let i = from - 1; i >= 0; i--) {
        if (!items[i].divider && !items[i].disabled) return i;
      }
      return from;
    }

    _isSelected(item) {
      if (item.divider) return false;
      return item.value === this.options.value;
    }

    _selectByIndex(idx) {
      const items = this.options.items || [];
      const it = items[idx];
      if (!it || it.divider || it.disabled) return;
      const oldValue = this.options.value;
      this.options.value = it.value;
      this._updateTriggerLabel();
      this.close();
      this.trigger.focus();
      if (oldValue !== it.value && typeof this.options.onChange === "function") {
        try { this.options.onChange(it.value, it); }
        catch (e) { console.warn("ErpDropdown onChange error:", e); }
      }
    }

    // ── Trigger label ───────────────────────────────────────────────

    _updateTriggerLabel() {
      const items = this.options.items || [];
      const found = items.find(it => !it.divider && it.value === this.options.value);
      if (found) {
        this.triggerLabel.textContent = String(found.label != null ? found.label : found.value);
        this.triggerLabel.classList.remove("erp-dropdown-placeholder");
      } else {
        this.triggerLabel.textContent = this.options.placeholder || "";
        this.triggerLabel.classList.add("erp-dropdown-placeholder");
      }
    }

    // ── Keyboard handling ───────────────────────────────────────────

    _handleTriggerKeydown(ev) {
      // B+10++++++++ (6.5.2026): readonly gate jen na save (Phase C). UI free.
      if (this.options.disabled) return;
      const key = ev.key;
      // Open panel
      if (!this._isOpen) {
        if (key === "Enter" || key === " " || key === "ArrowDown" || key === "ArrowUp") {
          ev.preventDefault();
          this.open();
          return;
        }
        // Type-ahead při closed → otevři + jump
        if (key.length === 1 && /\S/.test(key)) {
          this.open();
          this._typeAhead(key);
        }
        return;
      }
      // Open — navigate / select
      if (key === "ArrowDown") {
        ev.preventDefault();
        this._highlightedIdx = (this._highlightedIdx < 0)
          ? this._firstEnabledIndex()
          : this._nextEnabledIndex(this._highlightedIdx);
        this._updateHighlight();
        this._scrollHighlightedIntoView();
      } else if (key === "ArrowUp") {
        ev.preventDefault();
        this._highlightedIdx = (this._highlightedIdx < 0)
          ? this._lastEnabledIndex()
          : this._prevEnabledIndex(this._highlightedIdx);
        this._updateHighlight();
        this._scrollHighlightedIntoView();
      } else if (key === "Home") {
        ev.preventDefault();
        this._highlightedIdx = this._firstEnabledIndex();
        this._updateHighlight();
        this._scrollHighlightedIntoView();
      } else if (key === "End") {
        ev.preventDefault();
        this._highlightedIdx = this._lastEnabledIndex();
        this._updateHighlight();
        this._scrollHighlightedIntoView();
      } else if (key === "Enter" || key === " ") {
        ev.preventDefault();
        if (this._highlightedIdx >= 0) {
          this._selectByIndex(this._highlightedIdx);
        }
      } else if (key === "Tab") {
        // Allow tab to move focus, just close panel
        this.close();
      } else if (key.length === 1 && /\S/.test(key)) {
        this._typeAhead(key);
      }
    }

    _typeAhead(ch) {
      this._typeBuffer += ch.toLowerCase();
      if (this._typeTimeout) clearTimeout(this._typeTimeout);
      this._typeTimeout = setTimeout(() => { this._typeBuffer = ""; }, 600);
      const items = this.options.items || [];
      // Najdi první item co začíná na buffer (od dalšího po current highlight)
      const start = (this._highlightedIdx >= 0) ? this._highlightedIdx + 1 : 0;
      const tryFind = (from, to) => {
        for (let i = from; i < to; i++) {
          const it = items[i];
          if (it && !it.divider && !it.disabled) {
            const lbl = String(it.label != null ? it.label : it.value).toLowerCase();
            if (lbl.startsWith(this._typeBuffer)) return i;
          }
        }
        return -1;
      };
      let found = tryFind(start, items.length);
      if (found < 0) found = tryFind(0, start);
      if (found >= 0) {
        this._highlightedIdx = found;
        this._updateHighlight();
        this._scrollHighlightedIntoView();
      }
    }

    // ── Loading visual ──────────────────────────────────────────────

    _updateLoadingVisual() {
      if (this.options.loading) {
        this.wrapper.classList.add("erp-dropdown-loading");
      } else {
        this.wrapper.classList.remove("erp-dropdown-loading");
      }
    }

    // ── Public API ──────────────────────────────────────────────────

    element() { return this.trigger; }
    wrapperElement() { return this.wrapper; }

    value() { return this.options.value; }

    selectedItem() {
      const items = this.options.items || [];
      return items.find(it => !it.divider && it.value === this.options.value) || null;
    }

    setValue(value, silent) {
      if (this._destroyed) return;
      const oldValue = this.options.value;
      this.options.value = value;
      this._updateTriggerLabel();
      if (!silent && oldValue !== value && typeof this.options.onChange === "function") {
        const it = this.selectedItem();
        try { this.options.onChange(value, it); }
        catch (e) {}
      }
    }

    setItems(items) {
      if (this._destroyed) return;
      this.options.items = items || [];
      this._updateTriggerLabel();
      if (this._isOpen) {
        this._renderPanelItems();
        this._highlightedIdx = this._firstEnabledIndex();
        this._updateHighlight();
      }
    }

    setDisabled(disabled) {
      if (this._destroyed) return;
      this.options.disabled = !!disabled;
      this.trigger.disabled = !!disabled;
      if (disabled && this._isOpen) this.close();
    }

    setReadonly(readonly) {
      if (this._destroyed) return;
      this.options.readonly = !!readonly;
      if (readonly) {
        this.wrapper.classList.add("erp-dropdown-readonly");
        if (this._isOpen) this.close();
      } else {
        this.wrapper.classList.remove("erp-dropdown-readonly");
      }
    }

    setLoading(loading) {
      if (this._destroyed) return;
      this.options.loading = !!loading;
      this._updateLoadingVisual();
      if (loading && this._isOpen) this.close();
    }

    setError(msg) {
      if (this._destroyed) return;
      if (msg) {
        this.errorEl.textContent = msg;
        this.errorEl.hidden = false;
        this.wrapper.classList.add("erp-dropdown-invalid");
      } else {
        this.errorEl.hidden = true;
        this.wrapper.classList.remove("erp-dropdown-invalid");
      }
    }

    isOpen() { return this._isOpen; }
    isDisabled() { return !!this.options.disabled; }

    focus() {
      if (this._destroyed || !this.trigger) return;
      this.trigger.focus();
    }

    destroy() {
      if (this._destroyed) return;
      this._destroyed = true;
      if (this._isOpen) this.close();
      if (this._typeTimeout) clearTimeout(this._typeTimeout);
      if (this.wrapper && this.wrapper.parentNode) {
        this.wrapper.parentNode.removeChild(this.wrapper);
      }
      this.wrapper = null;
      this.trigger = null;
      this.triggerLabel = null;
      this.panel = null;
    }
  }

  // ── Factory ────────────────────────────────────────────────────────
  ErpDropdown.create = function (options) {
    const dd = new ErpDropdown(null, options);
    return dd.wrapperElement();
  };

  global.ErpDropdown = ErpDropdown;

  }); // _erpLoadModule end
})(typeof window !== "undefined" ? window : this);
