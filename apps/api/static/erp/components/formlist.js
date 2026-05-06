/**
 * ErpFormList — UI Kit lookup picker (Centrála 1 native pattern).
 *
 * 3-in-1 komponenta:
 *   1. Input typeable — píšeš text, dropdown filtruje items live
 *   2. ▾ caret button — open full list (žádný filter, vše)
 *   3. ⋮ browse button — popup grid modal s search + dvouklik select
 *
 * Marti's spec 5.5.2026: "Tahleta componenta je kombinaci trech
 * komponent... Lide pouzivaji dnes a denne napric firmami EUROSOFT
 * a INTERSOFT. Nas cil by mel byt udelat to funkce stejny, nebo lepsi."
 *
 * Items:
 *   [{value, label, [extraColumns]}, ...]
 *
 * State display:
 *   input.value = item.label (display)
 *   wrapper.dataset.fkValue = item.value (FK pro Phase C save)
 *
 * Keyboard:
 *   Type — filter items live (substring match, case-insensitive)
 *   Arrow Down/Up — navigate panel (auto-open on first arrow)
 *   Enter — select highlighted item from panel
 *   Escape — close panel + restore original display
 *   Tab — close panel + move focus
 *   Ctrl+Space — open browse modal (advanced users)
 *
 * Mouse:
 *   Click input — open panel (zobrazí všechny items)
 *   Click ▾ caret — toggle panel (žádný filter)
 *   Click ⋮ browse — open grid modal
 *   Click item v panel — select + close
 *   Dvouklik item v browse modal — select + close + OK
 *
 * Usage:
 *
 *   const fl = new ErpFormList(container, {
 *     label: "Centrála menu strom",
 *     value: "102",
 *     displayValue: "Centrála menu strom",   // initial display label
 *     items: [{value, label}],                // OR async loadItems
 *     onLoadItems: async () => fetch(...),    // lazy load při prvním focus
 *     onChange: (val, item) => {...},
 *     // Browse modal config:
 *     browseTitle: "Vybrat z přehledu",
 *     browseColumns: [
 *       {field: "value", header: "Číslo", width: 80},
 *       {field: "label", header: "Název", width: 1, grow: true},
 *     ],
 *   });
 *
 *   fl.value();        // FK string
 *   fl.displayValue(); // current label
 *   fl.setValue("102", "Display name");
 *   fl.setItems(newItems);
 *   fl.focus();
 *   fl.destroy();
 *
 * Phase B+6.4+ (5.5.2026).
 */
(function (global) {
  "use strict";

  // Globální tracking — jen jeden panel otevřený naráz
  let _OPEN_PANEL_INSTANCE = null;

  function _esc(s) {
    return String(s).replace(/[&<>"']/g, c =>
      ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])
    );
  }

  function _normalize(s) {
    // Case-insensitive + diakritika-stripping pro lepší filter
    return String(s || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[̀-ͯ]/g, "");
  }

  class ErpFormList {
    constructor(container, options) {
      this.container = container || null;
      this.options = Object.assign({
        items: [],
        value: null,
        displayValue: null,
        label: null,
        placeholder: "Začni psát nebo klikni na ⋮",
        required: false,
        disabled: false,
        readonly: false,
        hint: null,
        emptyMessage: "Žádné položky",
        loadingMessage: "Načítám...",
        onLoadItems: null,
        onChange: null,
        onBlur: null,
        onFocus: null,
        // B+6.4++ (5.5.2026): klíčová FK hodnota viditelně uvnitř komponenty
        // (Marti's spec: "ta hodnota patri a mela by byt soucasti teto
        // komponenty... aby tam bylo citelne to cislo a trochu mista").
        // To je **klíč pro DB save** — Phase C OK button píše tuhle value.
        showValuePrefix: false,
        valuePrefixWidth: "60px",
        // Browse modal:
        browseTitle: "Vybrat hodnotu",
        browseColumns: null,    // [{field, header, width}] — default = [Číslo, Název]
      }, options || {});
      this._destroyed = false;
      this._isOpen = false;
      this._items = (this.options.items || []).slice();
      this._filtered = this._items.slice();
      this._highlightedIdx = -1;
      this._lastFilterText = null;
      this._loaded = !this.options.onLoadItems;
      this._loading = false;
      this._currentValue = this.options.value;
      this._currentDisplay = this.options.displayValue || "";
      this._render();
    }

    _render() {
      this.wrapper = document.createElement("div");
      this.wrapper.className = "erp-formlist2-wrapper";

      // Label
      if (this.options.label) {
        const lbl = document.createElement("label");
        lbl.className = "erp-formlist2-label";
        lbl.textContent = this.options.label;
        if (this.options.required) {
          const req = document.createElement("span");
          req.className = "erp-formlist2-required";
          req.textContent = " *";
          lbl.appendChild(req);
        }
        this.wrapper.appendChild(lbl);
      }

      // Row: [value prefix] + input + caret + browse
      const row = document.createElement("div");
      row.className = "erp-formlist2-row";

      // B+6.4++ (5.5.2026): value prefix vlevo (FK / klíč pro DB save)
      if (this.options.showValuePrefix) {
        this.valuePrefixEl = document.createElement("span");
        this.valuePrefixEl.className = "erp-formlist2-value-prefix";
        this.valuePrefixEl.style.flex = "0 0 " + this.options.valuePrefixWidth;
        this.valuePrefixEl.style.width = this.options.valuePrefixWidth;
        this.valuePrefixEl.title = "Klíč (FK)";
        this.valuePrefixEl.setAttribute("aria-label", "Klíčová hodnota (FK)");
        this.valuePrefixEl.textContent = this._currentValue != null
          ? String(this._currentValue) : "";
        row.appendChild(this.valuePrefixEl);
      }

      this.input = document.createElement("input");
      this.input.type = "text";
      this.input.className = "erp-formlist2-input";
      this.input.placeholder = this.options.placeholder || "";
      this.input.value = this._currentDisplay || "";
      // B+10++++++ (Marti's bug 6.5.2026 večer): readonly flag NESMÍ blokovat
      // typovat do inputu (vyhledávání). User chce filtrovat lookup i v Phase
      // A read-only mode — pouze commit selection (změna hodnoty) je gated.
      // Marti: "kdyz se snazim psat do textu, do inputu, ma zacit vyhledavat,
      // ale ten text nejde prepsat. Neco jako read only..."
      // Tj. NESETOVAT input.readOnly = true zde; readonly gate jen v _selectItem.
      if (this.options.disabled) this.input.disabled = true;
      row.appendChild(this.input);

      this.caretBtn = document.createElement("button");
      this.caretBtn.type = "button";
      this.caretBtn.className = "erp-formlist2-caret";
      this.caretBtn.setAttribute("aria-label", "Zobrazit seznam");
      this.caretBtn.title = "Zobrazit seznam";
      this.caretBtn.innerHTML = "▾";
      if (this.options.disabled) this.caretBtn.disabled = true;
      row.appendChild(this.caretBtn);

      this.browseBtn = document.createElement("button");
      this.browseBtn.type = "button";
      this.browseBtn.className = "erp-formlist2-browse";
      this.browseBtn.setAttribute("aria-label", "Otevřít seznam pro výběr");
      this.browseBtn.title = "Otevřít seznam pro výběr (Ctrl+Space)";
      this.browseBtn.innerHTML = "⋮";
      if (this.options.disabled) this.browseBtn.disabled = true;
      row.appendChild(this.browseBtn);

      this.wrapper.appendChild(row);

      // Hint
      if (this.options.hint) {
        this.hintEl = document.createElement("span");
        this.hintEl.className = "erp-formlist2-hint";
        this.hintEl.textContent = this.options.hint;
        this.wrapper.appendChild(this.hintEl);
      }

      // Panel — initially detached, appended to body on open
      this.panel = document.createElement("div");
      this.panel.className = "erp-formlist2-panel";

      // Events
      this.input.addEventListener("focus", (ev) => this._handleFocus(ev));
      this.input.addEventListener("blur", (ev) => this._handleBlur(ev));
      this.input.addEventListener("input", (ev) => this._handleInput(ev));
      this.input.addEventListener("keydown", (ev) => this._handleKeydown(ev));
      this.caretBtn.addEventListener("mousedown", (ev) => {
        ev.preventDefault();  // input nesmí lose focus
        if (this._isOpen) this.closePanel();
        else this.openPanel(/*reset filter*/true);
      });
      this.browseBtn.addEventListener("mousedown", (ev) => {
        ev.preventDefault();
        this.openBrowseModal();
      });

      if (this.container) this.container.appendChild(this.wrapper);
    }

    // ── Lazy-load items ──────────────────────────────────────────────

    async _ensureLoaded() {
      if (this._loaded || this._loading) return;
      if (typeof this.options.onLoadItems !== "function") {
        this._loaded = true;
        return;
      }
      this._loading = true;
      try {
        const items = await this.options.onLoadItems();
        if (Array.isArray(items)) {
          this._items = items;
          this._filtered = items.slice();
        }
        this._loaded = true;
      } catch (e) {
        console.warn("ErpFormList loadItems error:", e);
      } finally {
        this._loading = false;
      }
    }

    // ── Panel open / close / filter ──────────────────────────────────

    async openPanel(resetFilter) {
      if (this._destroyed || this._isOpen) return;
      if (this.options.disabled) return;
      // B+10++++++++ (drobnost 6.5.2026 večer): guard proti orphan re-open
      // po dvojkliku na item. Po selectu user nechce panel znovu otevřený.
      const sinceSelect = Date.now() - (this._justSelectedAt || 0);
      if (sinceSelect < 300) return;
      // Close any other open panel
      if (_OPEN_PANEL_INSTANCE && _OPEN_PANEL_INSTANCE !== this) {
        try { _OPEN_PANEL_INSTANCE.closePanel(); } catch (e) {}
      }
      _OPEN_PANEL_INSTANCE = this;
      this._isOpen = true;
      this.wrapper.classList.add("erp-formlist2-open");

      await this._ensureLoaded();

      if (resetFilter) {
        this._filtered = this._items.slice();
        this._lastFilterText = null;
      } else {
        this._applyFilter(this.input.value || "");
      }

      this._renderPanelItems();
      this._positionPanel();
      document.body.appendChild(this.panel);

      // Highlight current selected item or first item
      const selectedIdx = this._findFilteredIndex(this._currentValue);
      this._highlightedIdx = (selectedIdx >= 0) ? selectedIdx
                          : (this._filtered.length > 0 ? 0 : -1);
      this._updateHighlight();
      this._scrollHighlightedIntoView();

      // Outside click close
      this._outsideClick = (ev) => {
        if (!this.panel.contains(ev.target) && !this.wrapper.contains(ev.target)) {
          this.closePanel();
        }
      };
      this._reposition = () => this._positionPanel();
      setTimeout(() => {
        document.addEventListener("mousedown", this._outsideClick);
        window.addEventListener("scroll", this._reposition, true);
        window.addEventListener("resize", this._reposition);
      }, 0);
    }

    closePanel() {
      if (this._destroyed || !this._isOpen) return;
      this._isOpen = false;
      this.wrapper.classList.remove("erp-formlist2-open");
      if (this.panel.parentNode) this.panel.parentNode.removeChild(this.panel);
      if (_OPEN_PANEL_INSTANCE === this) _OPEN_PANEL_INSTANCE = null;
      if (this._outsideClick) {
        document.removeEventListener("mousedown", this._outsideClick);
        this._outsideClick = null;
      }
      if (this._reposition) {
        window.removeEventListener("scroll", this._reposition, true);
        window.removeEventListener("resize", this._reposition);
        this._reposition = null;
      }
    }

    _positionPanel() {
      const rect = this.input.getBoundingClientRect();
      const browseRect = this.browseBtn.getBoundingClientRect();
      // Panel zarovnán pod input + caret + browse (full row)
      const fullWidth = (browseRect.right - rect.left);
      const panelMaxHeight = 320;
      const spaceBelow = window.innerHeight - rect.bottom - 8;
      const spaceAbove = rect.top - 8;
      const openUp = spaceBelow < 200 && spaceAbove > spaceBelow;
      this.panel.style.position = "fixed";
      this.panel.style.left = rect.left + "px";
      this.panel.style.minWidth = fullWidth + "px";
      this.panel.style.maxWidth = Math.max(fullWidth, 320) + "px";
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

    _applyFilter(text) {
      const norm = _normalize(text);
      this._lastFilterText = norm;
      if (!norm) {
        this._filtered = this._items.slice();
      } else {
        this._filtered = this._items.filter(it => {
          const lbl = _normalize(it.label != null ? it.label : it.value);
          return lbl.includes(norm);
        });
      }
    }

    _renderPanelItems() {
      this.panel.innerHTML = "";
      if (this._loading) {
        const ld = document.createElement("div");
        ld.className = "erp-formlist2-empty";
        ld.textContent = this.options.loadingMessage || "Načítám...";
        this.panel.appendChild(ld);
        return;
      }
      if (!this._filtered.length) {
        const empty = document.createElement("div");
        empty.className = "erp-formlist2-empty";
        empty.textContent = this.options.emptyMessage || "Žádné položky";
        this.panel.appendChild(empty);
        return;
      }
      this._filtered.forEach((it, idx) => {
        const opt = document.createElement("div");
        opt.className = "erp-formlist2-item";
        opt.setAttribute("data-erp-idx", String(idx));
        if (it.disabled) opt.classList.add("erp-formlist2-item-disabled");
        if (this._isCurrentValue(it)) {
          opt.classList.add("erp-formlist2-item-selected");
        }
        // Show label, optionally s value prefix (#Cislo)
        const valStr = (it.value != null) ? String(it.value) : "";
        const lblStr = (it.label != null) ? String(it.label) : valStr;
        // Highlight matched substring
        opt.innerHTML = this._highlightMatch(lblStr, this._lastFilterText || "");
        opt.addEventListener("mouseenter", () => {
          if (!it.disabled) {
            this._highlightedIdx = idx;
            this._updateHighlight();
          }
        });
        opt.addEventListener("mousedown", (ev) => {
          ev.preventDefault();
          if (it.disabled) return;
          this._selectFiltered(idx);
        });
        this.panel.appendChild(opt);
      });
    }

    _highlightMatch(label, normFilter) {
      if (!normFilter) return _esc(label);
      const normLabel = _normalize(label);
      const idx = normLabel.indexOf(normFilter);
      if (idx < 0) return _esc(label);
      // Map zpět na original (diakritika, case)
      const before = label.slice(0, idx);
      const match = label.slice(idx, idx + normFilter.length);
      const after = label.slice(idx + normFilter.length);
      return _esc(before) +
        '<mark class="erp-formlist2-mark">' + _esc(match) + '</mark>' +
        _esc(after);
    }

    _updateHighlight() {
      const items = this.panel.querySelectorAll(".erp-formlist2-item");
      items.forEach((el) => {
        const idx = parseInt(el.getAttribute("data-erp-idx"), 10);
        if (idx === this._highlightedIdx) el.classList.add("erp-formlist2-item-highlight");
        else el.classList.remove("erp-formlist2-item-highlight");
      });
    }

    _scrollHighlightedIntoView() {
      const el = this.panel.querySelector(".erp-formlist2-item-highlight");
      if (el && typeof el.scrollIntoView === "function") {
        try { el.scrollIntoView({ block: "nearest" }); } catch (e) {}
      }
    }

    _findFilteredIndex(value) {
      if (value == null || value === "") return -1;
      const sval = String(value);
      for (let i = 0; i < this._filtered.length; i++) {
        if (String(this._filtered[i].value) === sval) return i;
      }
      return -1;
    }

    _isCurrentValue(item) {
      if (this._currentValue == null) return false;
      return String(item.value) === String(this._currentValue);
    }

    _selectFiltered(idx) {
      const it = this._filtered[idx];
      if (!it || it.disabled) return;
      // B+10+++++++ (Marti's bug fix 6.5.2026 večer): read-only gate
      // přesunut k save flow, ne k UI selection (commit display + value
      // vždy v UI; Phase C save bude gate isFieldReadOnly per field).
      this._setSelectedItem(it);
      // B+10++++++++ (Marti's bug fix 6.5.2026 večer — dvojklik): guard
      // proti re-open panelu skrz focus race. Po selectu input.focus()
      // může vyvolat focus event → _handleFocus → openPanel → panel
      // re-mountuje. Plus dvojklik triggeruje 2× mousedown → 2× selectFiltered.
      // Marti: "kdyz potvrdim dvojklikem vyber, tak se formlist zavre,
      // ale zustane to ve stavu jako v printscreenu" (orphan dropdown).
      // Fix: timestamp guard 300ms suppresses re-open.
      this._justSelectedAt = Date.now();
      this.closePanel();
      // input.focus() vynechán — input už má focus (mousedown handler měl
      // preventDefault, takže input focus nezmizel). Refocus by zbytečně
      // mohl trigger focus event a race condition s async openPanel.
    }

    _setSelectedItem(item) {
      const oldValue = this._currentValue;
      this._currentValue = item.value;
      this._currentDisplay = item.label != null ? String(item.label) : String(item.value);
      this.input.value = this._currentDisplay;
      // B+6.4++ (5.5.2026): sync FK value prefix vlevo
      if (this.valuePrefixEl) {
        this.valuePrefixEl.textContent = item.value != null
          ? String(item.value) : "";
      }
      if (oldValue !== item.value && typeof this.options.onChange === "function") {
        try { this.options.onChange(item.value, item); }
        catch (e) { console.warn("ErpFormList onChange error:", e); }
      }
    }

    // ── Input event handlers ─────────────────────────────────────────

    _handleFocus(ev) {
      if (this.options.disabled) return;
      // B+10++++++++ (drobnost 6.5.2026 večer): suppress focus-triggered
      // openPanel pokud user právě vybral item (300ms guard). Bez toho
      // dvojklik na item → close panel → focus event → re-open panel
      // s vybraným itemem highlighted (orphan dropdown bug).
      const sinceSelect = Date.now() - (this._justSelectedAt || 0);
      if (sinceSelect < 300) return;
      // Select-all při focus (i v readonly — search OK, commit gated v save)
      try {
        setTimeout(() => {
          try { this.input.select(); } catch (e) {}
        }, 0);
      } catch (e) {}
      this.openPanel(/*reset*/false);
      if (typeof this.options.onFocus === "function") {
        try { this.options.onFocus(ev); } catch (e) {}
      }
    }

    _handleBlur(ev) {
      // Delay aby panel item mousedown projel
      setTimeout(() => {
        if (!this._isOpen) {
          // Restore display value pokud user napsal text + odešel bez výběru
          if (this.input.value !== this._currentDisplay) {
            this.input.value = this._currentDisplay;
          }
        }
      }, 200);
      if (typeof this.options.onBlur === "function") {
        try { this.options.onBlur(this._currentValue); } catch (e) {}
      }
    }

    _handleInput(ev) {
      // B+10++++++ (Marti's bug fix 6.5.2026): readonly NEsmí blokovat input —
      // user smí filtrovat lookup i v read-only mode. Commit gate v _selectItem.
      if (this.options.disabled) return;
      const text = this.input.value || "";
      this._applyFilter(text);
      if (!this._isOpen) {
        this.openPanel(/*reset*/false);
        return;  // openPanel renderuje
      }
      this._renderPanelItems();
      // Auto-highlight first
      this._highlightedIdx = this._filtered.length > 0 ? 0 : -1;
      this._updateHighlight();
      this._scrollHighlightedIntoView();
    }

    _handleKeydown(ev) {
      if (this.options.disabled) return;
      const key = ev.key;
      if (key === "ArrowDown") {
        ev.preventDefault();
        if (!this._isOpen) { this.openPanel(/*reset*/false); return; }
        this._moveHighlight(1);
      } else if (key === "ArrowUp") {
        ev.preventDefault();
        if (!this._isOpen) { this.openPanel(/*reset*/false); return; }
        this._moveHighlight(-1);
      } else if (key === "Home" && this._isOpen) {
        ev.preventDefault();
        this._highlightedIdx = this._filtered.length > 0 ? 0 : -1;
        this._updateHighlight();
        this._scrollHighlightedIntoView();
      } else if (key === "End" && this._isOpen) {
        ev.preventDefault();
        this._highlightedIdx = this._filtered.length - 1;
        this._updateHighlight();
        this._scrollHighlightedIntoView();
      } else if (key === "Enter") {
        if (this._isOpen && this._highlightedIdx >= 0) {
          ev.preventDefault();
          this._selectFiltered(this._highlightedIdx);
        }
      } else if (key === "Escape") {
        if (this._isOpen) {
          ev.preventDefault();
          // Restore original display on Esc
          this.input.value = this._currentDisplay;
          this._applyFilter("");
          this.closePanel();
        }
      } else if (key === "Tab") {
        // Tab close panel + let focus move
        if (this._isOpen) this.closePanel();
      } else if (key === " " && ev.ctrlKey) {
        // Ctrl+Space — open browse modal
        ev.preventDefault();
        this.openBrowseModal();
      }
    }

    _moveHighlight(dir) {
      if (!this._filtered.length) return;
      let next = this._highlightedIdx + dir;
      // Skip disabled
      while (next >= 0 && next < this._filtered.length &&
             this._filtered[next].disabled) {
        next += dir;
      }
      if (next < 0) next = 0;
      if (next >= this._filtered.length) next = this._filtered.length - 1;
      this._highlightedIdx = next;
      this._updateHighlight();
      this._scrollHighlightedIntoView();
    }

    // ── Browse modal ─────────────────────────────────────────────────

    async openBrowseModal() {
      if (this._destroyed || this.options.disabled) return;
      // Ensure items loaded
      this._loading = true;
      this._renderPanelItems();
      await this._ensureLoaded();
      this._loading = false;
      // Close inline panel pokud open
      if (this._isOpen) this.closePanel();
      const result = await this._openModalDialog();
      if (result != null) {
        const item = this._items.find(it => String(it.value) === String(result));
        if (item) this._setSelectedItem(item);
      }
      // B+10++++++++ (drobnost 6.5.2026 večer): stejný guard jako u inline
      // selectFiltered — input.focus() po modal close → focus event →
      // openPanel race. Marti: "po uzavreni takto visi... az kliknu vedle
      // tak to zmizi". Guard 300ms suppresses re-open.
      this._justSelectedAt = Date.now();
      // input.focus() vynechán — input už typicky drží focus po modal close
      // (modal close handler nepředává focus zpět). Pokud user chce focus,
      // klikne sám.
    }

    _openModalDialog() {
      return new Promise((resolve) => {
        const backdrop = document.createElement("div");
        backdrop.className = "erp-formlist2-modal-backdrop";
        const modal = document.createElement("div");
        modal.className = "erp-formlist2-modal";

        const cols = this.options.browseColumns || [
          { field: "value", header: "Číslo", width: "100px" },
          { field: "label", header: "Název", width: "auto" },
        ];

        let resolved = false;
        const close = (val) => {
          if (resolved) return;
          resolved = true;
          document.removeEventListener("keydown", onKey);
          backdrop.remove();
          resolve(val);
        };

        // Build header
        const headerHtml = cols.map(c =>
          '<div class="erp-formlist2-modal-th" style="' +
            (c.width === "auto" ? "flex:1 1 auto;" : "width:" + c.width + ";flex:0 0 " + c.width + ";") +
          '">' + _esc(c.header) + '</div>'
        ).join("");

        modal.innerHTML =
          '<div class="erp-formlist2-modal-header">' +
            '<h3>' + _esc(this.options.browseTitle || "Vybrat hodnotu") + '</h3>' +
            '<button class="erp-formlist2-modal-close" type="button" aria-label="Zavřít">×</button>' +
          '</div>' +
          '<div class="erp-formlist2-modal-toolbar">' +
            '<input type="text" class="erp-formlist2-modal-search" ' +
              'placeholder="Filtr — piš pro hledání...">' +
          '</div>' +
          '<div class="erp-formlist2-modal-table-wrap">' +
            '<div class="erp-formlist2-modal-thead">' + headerHtml + '</div>' +
            '<div class="erp-formlist2-modal-tbody"></div>' +
          '</div>' +
          '<div class="erp-formlist2-modal-footer">' +
            '<button type="button" data-erp-action="ok" class="erp-formlist2-modal-btn primary">OK</button>' +
            '<button type="button" data-erp-action="cancel" class="erp-formlist2-modal-btn">Storno</button>' +
          '</div>';

        backdrop.appendChild(modal);
        document.body.appendChild(backdrop);

        const tbody = modal.querySelector(".erp-formlist2-modal-tbody");
        const searchInput = modal.querySelector(".erp-formlist2-modal-search");

        let modalFiltered = this._items.slice();
        let modalSelectedValue = this._currentValue;
        let modalHighlightedIdx = -1;

        const renderRows = () => {
          tbody.innerHTML = "";
          if (!modalFiltered.length) {
            const empty = document.createElement("div");
            empty.className = "erp-formlist2-modal-empty";
            empty.textContent = this.options.emptyMessage || "Žádné položky";
            tbody.appendChild(empty);
            return;
          }
          modalFiltered.forEach((it, idx) => {
            const tr = document.createElement("div");
            tr.className = "erp-formlist2-modal-tr";
            tr.setAttribute("data-erp-idx", String(idx));
            if (String(it.value) === String(modalSelectedValue)) {
              tr.classList.add("erp-formlist2-modal-tr-selected");
            }
            if (idx === modalHighlightedIdx) {
              tr.classList.add("erp-formlist2-modal-tr-highlight");
            }
            cols.forEach(c => {
              const td = document.createElement("div");
              td.className = "erp-formlist2-modal-td";
              if (c.width === "auto") {
                td.style.cssText = "flex:1 1 auto;";
              } else {
                td.style.cssText = "width:" + c.width + ";flex:0 0 " + c.width + ";";
              }
              const v = it[c.field];
              td.textContent = (v != null) ? String(v) : "";
              tr.appendChild(td);
            });
            tr.addEventListener("click", () => {
              modalSelectedValue = it.value;
              modalHighlightedIdx = idx;
              renderRows();
            });
            tr.addEventListener("dblclick", () => {
              close(it.value);
            });
            tbody.appendChild(tr);
          });
        };

        const applyModalFilter = (text) => {
          const norm = _normalize(text);
          if (!norm) {
            modalFiltered = this._items.slice();
          } else {
            modalFiltered = this._items.filter(it => {
              return cols.some(c => {
                const v = it[c.field];
                return v != null && _normalize(v).includes(norm);
              });
            });
          }
          // Reset highlight na první match
          modalHighlightedIdx = modalFiltered.length > 0 ? 0 : -1;
          renderRows();
        };

        // Initial render
        // Pre-select current value if exists (highlight + scroll)
        const initialIdx = modalFiltered.findIndex(it =>
          String(it.value) === String(modalSelectedValue)
        );
        if (initialIdx >= 0) modalHighlightedIdx = initialIdx;
        renderRows();
        setTimeout(() => {
          const sel = tbody.querySelector(".erp-formlist2-modal-tr-highlight, .erp-formlist2-modal-tr-selected");
          if (sel && sel.scrollIntoView) {
            try { sel.scrollIntoView({ block: "center" }); } catch (e) {}
          }
        }, 30);

        // Search input
        searchInput.addEventListener("input", (ev) => {
          applyModalFilter(ev.target.value || "");
        });

        // Keyboard navigation v search inputu
        searchInput.addEventListener("keydown", (ev) => {
          if (ev.key === "ArrowDown") {
            ev.preventDefault();
            if (modalHighlightedIdx < modalFiltered.length - 1) modalHighlightedIdx++;
            renderRows();
            const el = tbody.querySelector(".erp-formlist2-modal-tr-highlight");
            if (el && el.scrollIntoView) try { el.scrollIntoView({ block: "nearest" }); } catch (e) {}
          } else if (ev.key === "ArrowUp") {
            ev.preventDefault();
            if (modalHighlightedIdx > 0) modalHighlightedIdx--;
            renderRows();
            const el = tbody.querySelector(".erp-formlist2-modal-tr-highlight");
            if (el && el.scrollIntoView) try { el.scrollIntoView({ block: "nearest" }); } catch (e) {}
          } else if (ev.key === "Enter") {
            ev.preventDefault();
            if (modalHighlightedIdx >= 0 && modalFiltered[modalHighlightedIdx]) {
              close(modalFiltered[modalHighlightedIdx].value);
            }
          }
        });

        // Footer buttons
        modal.querySelector('[data-erp-action="ok"]').addEventListener("click", () => {
          close(modalSelectedValue);
        });
        modal.querySelector('[data-erp-action="cancel"]').addEventListener("click", () => {
          close(null);
        });
        modal.querySelector(".erp-formlist2-modal-close").addEventListener("click", () => {
          close(null);
        });

        // Esc / backdrop click
        const onKey = (ev) => {
          if (ev.key === "Escape") {
            ev.preventDefault();
            close(null);
          }
        };
        backdrop.addEventListener("click", (ev) => {
          if (ev.target === backdrop) close(null);
        });
        document.addEventListener("keydown", onKey);

        // Auto-focus search input
        setTimeout(() => { searchInput.focus(); }, 60);
      });
    }

    // ── Public API ───────────────────────────────────────────────────

    element() { return this.input; }
    wrapperElement() { return this.wrapper; }
    value() { return this._currentValue; }
    displayValue() { return this._currentDisplay; }

    setValue(value, displayValue) {
      if (this._destroyed) return;
      this._currentValue = value;
      this._currentDisplay = displayValue || (value != null ? String(value) : "");
      this.input.value = this._currentDisplay;
      // B+6.4++ (5.5.2026): sync FK value prefix vlevo
      if (this.valuePrefixEl) {
        this.valuePrefixEl.textContent = value != null ? String(value) : "";
      }
    }

    setItems(items) {
      if (this._destroyed) return;
      this._items = (items || []).slice();
      this._filtered = this._items.slice();
      this._loaded = true;
      this._loading = false;
      if (this._isOpen) {
        this._applyFilter(this.input.value || "");
        this._renderPanelItems();
        this._highlightedIdx = this._filtered.length > 0 ? 0 : -1;
        this._updateHighlight();
      }
    }

    setDisabled(disabled) {
      if (this._destroyed) return;
      this.options.disabled = !!disabled;
      this.input.disabled = !!disabled;
      this.caretBtn.disabled = !!disabled;
      this.browseBtn.disabled = !!disabled;
      if (disabled && this._isOpen) this.closePanel();
    }

    setReadonly(readonly) {
      if (this._destroyed) return;
      this.options.readonly = !!readonly;
      this.input.readOnly = !!readonly;
    }

    setLabel(label) {
      if (this._destroyed) return;
      this.options.label = label;
      const lblEl = this.wrapper.querySelector(".erp-formlist2-label");
      if (lblEl) lblEl.textContent = label || "";
    }

    isOpen() { return this._isOpen; }
    isDisabled() { return !!this.options.disabled; }

    focus() {
      if (this._destroyed || !this.input) return;
      this.input.focus();
    }

    destroy() {
      if (this._destroyed) return;
      this._destroyed = true;
      if (this._isOpen) this.closePanel();
      if (this.wrapper && this.wrapper.parentNode) {
        this.wrapper.parentNode.removeChild(this.wrapper);
      }
      this.wrapper = null;
      this.input = null;
      this.caretBtn = null;
      this.browseBtn = null;
      this.panel = null;
    }
  }

  // ── Factory ────────────────────────────────────────────────────────
  ErpFormList.create = function (options) {
    const fl = new ErpFormList(null, options);
    return fl.wrapperElement();
  };

  global.ErpFormList = ErpFormList;
})(typeof window !== "undefined" ? window : this);
