/**
 * ErpDate — UI Kit datum / čas / datum+čas picker s českým kalendářem.
 *
 * Phase B+6.7 (6.5.2026). Marti's spec: "ErpDate, ErpMemo..." po
 * dokončení Phase B+8.1 user state persistence.
 *
 * API matching ErpInput:
 *   - constructor: new ErpDate(container, opts)
 *   - methods: value() / rawValue() / setValue() / isValid() / setError()
 *              focus() / destroy() / open() / close()
 *
 * Modes:
 *   - "date":     "25.5.1972"        ↔ "1972-05-25"        (ISO storage)
 *   - "datetime": "25.5.1972 20:44"  ↔ "1972-05-25T20:44"  (ISO storage)
 *   - "time":     "20:44"            ↔ "20:44"             (HH:MM)
 *
 * Czech locale:
 *   - Pondělí jako první den v týdnu (weekStart=1)
 *   - Měsíce: Leden, Únor, Březen, ...
 *   - Dny: Po, Út, St, Čt, Pá, So, Ne
 *   - Display formát: D.M.YYYY (žádné padding pro day/month)
 *
 * Popup kalendář:
 *   - Header: ◀ Květen 2026 ▶ (kliknutím na měsíc → year jump grid)
 *   - 6 týdnů × 7 dnů, current month visible, prev/next month dimmed
 *   - States: today (accent border), selected (filled accent bg),
 *             out-of-range disabled (min/max), weekend muted
 *   - Footer: [Dnes] [Včera] [Zítra] [Smazat]
 *   - Datetime: time spinner pod kalendářem
 *   - Outside click / Esc / select day → close
 *
 * Usage:
 *
 *   const d = new ErpDate(container, {
 *     mode: "date",
 *     value: "1972-05-25",
 *     label: "Datum narození",
 *     required: true,
 *     min: "1900-01-01",   // ISO
 *     max: "2099-12-31",   // ISO
 *     onChange: (display) => { ... },              // every commit
 *     onValidatedChange: (raw, isValid) => { ... }, // on blur
 *     onEnter: (raw, isValid) => { ... },
 *   });
 *
 *   d.value();      // "25.5.1972" (display)
 *   d.rawValue();   // "1972-05-25" (ISO)
 */
(function (global) {
  "use strict";

  const MODES = ["date", "datetime", "time"];
  const CS_MONTHS = [
    "Leden", "Únor", "Březen", "Duben", "Květen", "Červen",
    "Červenec", "Srpen", "Září", "Říjen", "Listopad", "Prosinec",
  ];
  const CS_WEEKDAYS = ["Po", "Út", "St", "Čt", "Pá", "So", "Ne"];

  let _OPEN_INSTANCE = null;

  function _esc(s) {
    return String(s).replace(/[&<>"']/g, c =>
      ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])
    );
  }

  function _pad2(n) {
    n = String(n);
    return n.length < 2 ? "0" + n : n;
  }

  // ── Parse / format helpers ──────────────────────────────────────────

  /**
   * Parse uživatelský vstup nebo ISO datum do { y, m, d, hh, mm } | null.
   * Akceptuje:
   *   - ISO: "1972-05-25" / "1972-05-25T20:44" / "1972-05-25 20:44"
   *   - CZ:  "25.5.1972" / "25. 5. 1972" / "25.5.1972 20:44"
   *   - Time only: "20:44" / "20:44:00"
   */
  function _parse(raw, mode) {
    if (raw == null) return null;
    const s = String(raw).trim();
    if (!s) return null;

    if (mode === "time") {
      const m = s.match(/^(\d{1,2}):(\d{1,2})(?::\d{1,2})?$/);
      if (!m) return null;
      const hh = parseInt(m[1], 10);
      const mm = parseInt(m[2], 10);
      if (hh < 0 || hh > 23 || mm < 0 || mm > 59) return null;
      return { y: null, m: null, d: null, hh, mm };
    }

    // Try ISO first: YYYY-MM-DD[ T]HH:MM
    let m = s.match(/^(\d{4})-(\d{1,2})-(\d{1,2})(?:[ T](\d{1,2}):(\d{1,2}))?/);
    if (m) {
      const y = parseInt(m[1], 10);
      const mo = parseInt(m[2], 10);
      const d = parseInt(m[3], 10);
      const hh = m[4] ? parseInt(m[4], 10) : 0;
      const mm = m[5] ? parseInt(m[5], 10) : 0;
      if (!_validDMY(d, mo, y)) return null;
      if (hh < 0 || hh > 23 || mm < 0 || mm > 59) return null;
      return { y, m: mo, d, hh, mm };
    }

    // CZ format: D.M.YYYY[ HH:MM]
    m = s.match(/^(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})(?:\s+(\d{1,2}):(\d{1,2}))?/);
    if (m) {
      const d = parseInt(m[1], 10);
      const mo = parseInt(m[2], 10);
      const y = parseInt(m[3], 10);
      const hh = m[4] ? parseInt(m[4], 10) : 0;
      const mm = m[5] ? parseInt(m[5], 10) : 0;
      if (!_validDMY(d, mo, y)) return null;
      if (hh < 0 || hh > 23 || mm < 0 || mm > 59) return null;
      return { y, m: mo, d, hh, mm };
    }
    return null;
  }

  function _validDMY(d, m, y) {
    if (m < 1 || m > 12) return false;
    if (d < 1) return false;
    const daysInMonth = new Date(y, m, 0).getDate();  // m=1..12, day 0 of next = last of m
    return d <= daysInMonth;
  }

  function _formatDisplay(parsed, mode) {
    if (!parsed) return "";
    if (mode === "time") {
      return _pad2(parsed.hh) + ":" + _pad2(parsed.mm);
    }
    const datePart = parsed.d + "." + parsed.m + "." + parsed.y;
    if (mode === "datetime") {
      return datePart + " " + _pad2(parsed.hh) + ":" + _pad2(parsed.mm);
    }
    return datePart;
  }

  function _formatRaw(parsed, mode) {
    if (!parsed) return "";
    if (mode === "time") {
      return _pad2(parsed.hh) + ":" + _pad2(parsed.mm);
    }
    const iso = parsed.y + "-" + _pad2(parsed.m) + "-" + _pad2(parsed.d);
    if (mode === "datetime") {
      return iso + "T" + _pad2(parsed.hh) + ":" + _pad2(parsed.mm);
    }
    return iso;
  }

  function _today() {
    const t = new Date();
    return { y: t.getFullYear(), m: t.getMonth() + 1, d: t.getDate(), hh: 0, mm: 0 };
  }

  function _addDays(parsed, n) {
    const dt = new Date(parsed.y, parsed.m - 1, parsed.d);
    dt.setDate(dt.getDate() + n);
    return {
      y: dt.getFullYear(), m: dt.getMonth() + 1, d: dt.getDate(),
      hh: parsed.hh, mm: parsed.mm,
    };
  }

  function _cmp(a, b) {
    // Compare two parsed objects (date-level comparison). a < b → -1, etc.
    if (!a || !b) return 0;
    if (a.y !== b.y) return a.y - b.y;
    if (a.m !== b.m) return a.m - b.m;
    return a.d - b.d;
  }

  // ── ErpDate class ─────────────────────────────────────────────────

  class ErpDate {
    constructor(container, options) {
      this.container = container || null;
      this.options = Object.assign({
        mode: "date",
        value: "",
        label: null,
        placeholder: null,
        required: false,
        readonly: false,
        disabled: false,
        autoFocus: false,
        hint: null,
        min: null,            // ISO date string
        max: null,            // ISO date string
        weekStart: 1,         // 1=Monday (Czech default)
        onChange: null,        // (display) => void
        onValidatedChange: null,  // (raw, isValid) => void
        onBlur: null,
        onFocus: null,
        onEnter: null,         // (raw, isValid) => void
      }, options || {});

      if (MODES.indexOf(this.options.mode) === -1) {
        console.warn("ErpDate: unknown mode '" + this.options.mode + "', falling back to date");
        this.options.mode = "date";
      }

      this._destroyed = false;
      this._parsed = null;        // canonical state
      this._isValid = true;
      this._errorMsg = null;
      this._isOpen = false;
      this._popup = null;
      this._viewYear = null;       // calendar viewport (current month shown)
      this._viewMonth = null;
      this._minParsed = this.options.min ? _parse(this.options.min, "date") : null;
      this._maxParsed = this.options.max ? _parse(this.options.max, "date") : null;

      this._render();

      if (this.options.value !== "" && this.options.value != null) {
        this.setValue(this.options.value);
      }
      if (this.options.autoFocus) {
        setTimeout(() => this.focus(), 50);
      }
    }

    // ── Render ────────────────────────────────────────────────────

    _render() {
      this.wrapper = document.createElement("div");
      this.wrapper.className = "erp-date-wrapper erp-date-mode-" + this.options.mode;

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

      // Input row (text input + calendar trigger button)
      const row = document.createElement("div");
      row.className = "erp-input-row erp-date-row";

      this.input = document.createElement("input");
      this.input.className = "erp-input";
      this.input.type = "text";
      this.input.autocomplete = "off";
      if (this.options.placeholder) {
        this.input.placeholder = this.options.placeholder;
      } else {
        this.input.placeholder =
          this.options.mode === "time" ? "HH:MM"
          : this.options.mode === "datetime" ? "D.M.YYYY HH:MM"
          : "D.M.YYYY";
      }
      // B+10++++++++ (6.5.2026): readonly gate jen save flow (Phase C).
      // UI input + trigger button volně klikatelné.
      if (this.options.disabled) this.input.disabled = true;
      row.appendChild(this.input);

      // Calendar / clock trigger button
      this.trigger = document.createElement("button");
      this.trigger.type = "button";
      this.trigger.className = "erp-date-trigger";
      this.trigger.tabIndex = -1;  // input focus only, trigger via mouse
      this.trigger.innerHTML = this.options.mode === "time" ? "🕒" : "📅";
      this.trigger.title =
        this.options.mode === "time" ? "Vybrat čas" : "Otevřít kalendář";
      if (this.options.disabled) {
        this.trigger.disabled = true;
      }
      row.appendChild(this.trigger);

      this.wrapper.appendChild(row);

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

      // Events
      this.input.addEventListener("input", () => this._onTextInput());
      this.input.addEventListener("blur", (ev) => this._onBlur(ev));
      this.input.addEventListener("focus", (ev) => this._onFocus(ev));
      this.input.addEventListener("keydown", (ev) => this._onKeydown(ev));
      this.trigger.addEventListener("click", (ev) => {
        ev.preventDefault();
        if (this._isOpen) this.close();
        else this.open();
      });

      if (this.container) this.container.appendChild(this.wrapper);
    }

    // ── Public API ───────────────────────────────────────────────

    value() {
      return _formatDisplay(this._parsed, this.options.mode);
    }

    rawValue() {
      return _formatRaw(this._parsed, this.options.mode);
    }

    setValue(v) {
      if (v === "" || v == null) {
        this._parsed = null;
        this.input.value = "";
        this._validate();
        return;
      }
      const parsed = _parse(v, this.options.mode);
      if (parsed) {
        this._parsed = parsed;
        this.input.value = _formatDisplay(parsed, this.options.mode);
      } else {
        // Invalid input — store raw for user to see
        this.input.value = String(v);
      }
      this._validate();
    }

    isValid() {
      return this._isValid;
    }

    setError(msg) {
      if (msg) {
        this.input.classList.add("erp-input-invalid");
        this.errorEl.textContent = msg;
        this.errorEl.hidden = false;
        this._isValid = false;
        this._errorMsg = msg;
      } else {
        this.input.classList.remove("erp-input-invalid");
        this.errorEl.hidden = true;
        this._isValid = true;
        this._errorMsg = null;
      }
    }

    focus() {
      if (this.input) this.input.focus();
    }

    destroy() {
      if (this._destroyed) return;
      this._destroyed = true;
      this.close();
      if (this.wrapper && this.wrapper.parentNode) {
        this.wrapper.parentNode.removeChild(this.wrapper);
      }
    }

    // ── Validation ───────────────────────────────────────────────

    _validate() {
      const raw = this.input.value.trim();
      if (!raw) {
        if (this.options.required) {
          this.setError("Povinné");
          return;
        }
        this.setError(null);
        this._parsed = null;
        return;
      }
      const parsed = _parse(raw, this.options.mode);
      if (!parsed) {
        this.setError("Neplatný formát");
        return;
      }
      // Range check (date / datetime)
      if (this.options.mode !== "time") {
        if (this._minParsed && _cmp(parsed, this._minParsed) < 0) {
          this.setError("Mimo rozsah (min " + _formatDisplay(this._minParsed, "date") + ")");
          return;
        }
        if (this._maxParsed && _cmp(parsed, this._maxParsed) > 0) {
          this.setError("Mimo rozsah (max " + _formatDisplay(this._maxParsed, "date") + ")");
          return;
        }
      }
      this._parsed = parsed;
      this.setError(null);
    }

    // ── Input event handlers ─────────────────────────────────────

    _onTextInput() {
      // Live re-validate but don't fire onValidatedChange (only on blur)
      this._validate();
      if (typeof this.options.onChange === "function") {
        try { this.options.onChange(this.input.value); } catch (e) {}
      }
    }

    _onBlur(ev) {
      // On blur, if parsed valid, normalize display
      this._validate();
      if (this._parsed && this._isValid) {
        this.input.value = _formatDisplay(this._parsed, this.options.mode);
      }
      if (typeof this.options.onBlur === "function") {
        try { this.options.onBlur(this.rawValue()); } catch (e) {}
      }
      if (typeof this.options.onValidatedChange === "function") {
        try {
          this.options.onValidatedChange(this.rawValue(), this._isValid);
        } catch (e) {}
      }
    }

    _onFocus(ev) {
      if (typeof this.options.onFocus === "function") {
        try { this.options.onFocus(); } catch (e) {}
      }
    }

    _onKeydown(ev) {
      if (ev.key === "Enter") {
        this._validate();
        if (this._parsed && this._isValid) {
          this.input.value = _formatDisplay(this._parsed, this.options.mode);
        }
        if (typeof this.options.onEnter === "function") {
          try {
            this.options.onEnter(this.rawValue(), this._isValid);
          } catch (e) {}
        }
        return;
      }
      if (ev.key === "Escape" && this._isOpen) {
        ev.preventDefault();
        this.close();
        return;
      }
      // Alt+Down or F4 = open popup
      if ((ev.altKey && ev.key === "ArrowDown") || ev.key === "F4") {
        ev.preventDefault();
        if (!this._isOpen) this.open();
      }
    }

    // ── Popup open / close / position ─────────────────────────────

    open() {
      // B+10++++++++ (6.5.2026): readonly gate jen save flow.
      if (this._destroyed || this._isOpen || this.options.disabled) return;
      // Close any other open ErpDate first
      if (_OPEN_INSTANCE && _OPEN_INSTANCE !== this) {
        try { _OPEN_INSTANCE.close(); } catch (e) {}
      }
      _OPEN_INSTANCE = this;
      this._isOpen = true;
      this.wrapper.classList.add("erp-date-open");

      // Initial viewport = parsed value or today
      const seed = this._parsed || _today();
      this._viewYear = seed.y || _today().y;
      this._viewMonth = seed.m || _today().m;

      this._popup = document.createElement("div");
      this._popup.className = "erp-date-popup erp-date-popup-mode-" + this.options.mode;
      this._renderPopup();
      document.body.appendChild(this._popup);
      this._positionPopup();

      // Listeners
      this._outsideClickListener = (ev) => {
        if (!this._popup.contains(ev.target) && !this.wrapper.contains(ev.target)) {
          this.close();
        }
      };
      this._escapeListener = (ev) => {
        if (ev.key === "Escape") {
          ev.preventDefault();
          this.close();
          this.input.focus();
        }
      };
      this._scrollListener = () => this._positionPopup();
      setTimeout(() => {
        document.addEventListener("mousedown", this._outsideClickListener);
        document.addEventListener("keydown", this._escapeListener);
        window.addEventListener("scroll", this._scrollListener, true);
        window.addEventListener("resize", this._scrollListener);
      }, 0);
    }

    close() {
      if (this._destroyed || !this._isOpen) return;
      this._isOpen = false;
      this.wrapper.classList.remove("erp-date-open");
      if (this._popup && this._popup.parentNode) {
        this._popup.parentNode.removeChild(this._popup);
      }
      this._popup = null;
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
    }

    _positionPopup() {
      if (!this._popup) return;
      const rect = this.wrapper.getBoundingClientRect();
      const popupRect = this._popup.getBoundingClientRect();
      const popupHeight = popupRect.height || 320;
      const popupWidth = popupRect.width || 280;
      const spaceBelow = window.innerHeight - rect.bottom - 8;
      const spaceAbove = rect.top - 8;
      const openUp = spaceBelow < popupHeight && spaceAbove > spaceBelow;
      this._popup.style.position = "fixed";
      // Horizontal: align left, but clamp to viewport
      let left = rect.left;
      const maxLeft = window.innerWidth - popupWidth - 8;
      if (left > maxLeft) left = Math.max(8, maxLeft);
      this._popup.style.left = left + "px";
      if (openUp) {
        this._popup.style.bottom = (window.innerHeight - rect.top + 4) + "px";
        this._popup.style.top = "auto";
      } else {
        this._popup.style.top = (rect.bottom + 4) + "px";
        this._popup.style.bottom = "auto";
      }
    }

    // ── Popup rendering ───────────────────────────────────────────

    _renderPopup() {
      this._popup.innerHTML = "";
      if (this.options.mode === "time") {
        this._renderTimePicker();
        this._renderFooter();
        return;
      }
      this._renderCalendarHeader();
      this._renderCalendarGrid();
      if (this.options.mode === "datetime") {
        this._renderTimePicker();
      }
      this._renderFooter();
    }

    _renderCalendarHeader() {
      const header = document.createElement("div");
      header.className = "erp-date-header";

      const prevBtn = document.createElement("button");
      prevBtn.type = "button";
      prevBtn.className = "erp-date-nav";
      prevBtn.innerHTML = "◀";
      prevBtn.title = "Předchozí měsíc";
      prevBtn.addEventListener("click", (ev) => {
        ev.preventDefault();
        this._navigateMonth(-1);
      });
      header.appendChild(prevBtn);

      const monthLabel = document.createElement("button");
      monthLabel.type = "button";
      monthLabel.className = "erp-date-month-label";
      monthLabel.textContent = CS_MONTHS[this._viewMonth - 1] + " " + this._viewYear;
      monthLabel.title = "Klikni pro skok roku";
      monthLabel.addEventListener("click", (ev) => {
        ev.preventDefault();
        this._toggleYearPicker();
      });
      header.appendChild(monthLabel);

      const nextBtn = document.createElement("button");
      nextBtn.type = "button";
      nextBtn.className = "erp-date-nav";
      nextBtn.innerHTML = "▶";
      nextBtn.title = "Další měsíc";
      nextBtn.addEventListener("click", (ev) => {
        ev.preventDefault();
        this._navigateMonth(1);
      });
      header.appendChild(nextBtn);

      this._popup.appendChild(header);
    }

    _renderCalendarGrid() {
      const grid = document.createElement("div");
      grid.className = "erp-date-grid";

      // Weekday headers (Po Út St Čt Pá So Ne)
      CS_WEEKDAYS.forEach(d => {
        const wd = document.createElement("div");
        wd.className = "erp-date-weekday";
        wd.textContent = d;
        grid.appendChild(wd);
      });

      // Find first Monday of the calendar grid (might be in previous month)
      const firstOfMonth = new Date(this._viewYear, this._viewMonth - 1, 1);
      let dayOfWeek = firstOfMonth.getDay();  // 0=Sun, 1=Mon, ..., 6=Sat
      // Convert to Monday=0, Tuesday=1, ..., Sunday=6
      dayOfWeek = (dayOfWeek + 6) % 7;
      const gridStart = new Date(firstOfMonth);
      gridStart.setDate(gridStart.getDate() - dayOfWeek);

      const today = _today();
      const sel = this._parsed;

      for (let i = 0; i < 42; i++) {
        const dt = new Date(gridStart);
        dt.setDate(dt.getDate() + i);
        const cellY = dt.getFullYear();
        const cellM = dt.getMonth() + 1;
        const cellD = dt.getDate();
        const cell = document.createElement("button");
        cell.type = "button";
        cell.className = "erp-date-day";
        cell.textContent = String(cellD);

        if (cellM !== this._viewMonth) {
          cell.classList.add("erp-date-day-other");
        }
        if (dt.getDay() === 0 || dt.getDay() === 6) {
          cell.classList.add("erp-date-day-weekend");
        }
        if (cellY === today.y && cellM === today.m && cellD === today.d) {
          cell.classList.add("erp-date-day-today");
        }
        if (sel && cellY === sel.y && cellM === sel.m && cellD === sel.d) {
          cell.classList.add("erp-date-day-selected");
        }
        // Range check (min/max)
        const cellParsed = { y: cellY, m: cellM, d: cellD, hh: 0, mm: 0 };
        if (this._minParsed && _cmp(cellParsed, this._minParsed) < 0) {
          cell.classList.add("erp-date-day-disabled");
          cell.disabled = true;
        }
        if (this._maxParsed && _cmp(cellParsed, this._maxParsed) > 0) {
          cell.classList.add("erp-date-day-disabled");
          cell.disabled = true;
        }
        cell.addEventListener("click", (ev) => {
          ev.preventDefault();
          this._selectDay(cellY, cellM, cellD);
        });
        grid.appendChild(cell);
      }

      this._popup.appendChild(grid);
    }

    _renderTimePicker() {
      const tp = document.createElement("div");
      tp.className = "erp-date-timepicker";

      const hh = (this._parsed && this._parsed.hh != null) ? this._parsed.hh : 0;
      const mm = (this._parsed && this._parsed.mm != null) ? this._parsed.mm : 0;

      const hhInput = document.createElement("input");
      hhInput.type = "number";
      hhInput.min = "0";
      hhInput.max = "23";
      hhInput.value = _pad2(hh);
      hhInput.className = "erp-date-time-input";

      const colon = document.createElement("span");
      colon.className = "erp-date-time-colon";
      colon.textContent = ":";

      const mmInput = document.createElement("input");
      mmInput.type = "number";
      mmInput.min = "0";
      mmInput.max = "59";
      mmInput.value = _pad2(mm);
      mmInput.className = "erp-date-time-input";

      const apply = () => {
        const h = Math.max(0, Math.min(23, parseInt(hhInput.value, 10) || 0));
        const m = Math.max(0, Math.min(59, parseInt(mmInput.value, 10) || 0));
        if (!this._parsed) {
          if (this.options.mode === "time") {
            this._parsed = { y: null, m: null, d: null, hh: h, mm: m };
          } else {
            const t = _today();
            this._parsed = { y: t.y, m: t.m, d: t.d, hh: h, mm: m };
          }
        } else {
          this._parsed.hh = h;
          this._parsed.mm = m;
        }
        this.input.value = _formatDisplay(this._parsed, this.options.mode);
        this._validate();
        if (typeof this.options.onChange === "function") {
          try { this.options.onChange(this.input.value); } catch (e) {}
        }
        if (typeof this.options.onValidatedChange === "function") {
          try {
            this.options.onValidatedChange(this.rawValue(), this._isValid);
          } catch (e) {}
        }
      };
      hhInput.addEventListener("change", apply);
      mmInput.addEventListener("change", apply);
      hhInput.addEventListener("input", apply);
      mmInput.addEventListener("input", apply);

      tp.appendChild(hhInput);
      tp.appendChild(colon);
      tp.appendChild(mmInput);
      this._popup.appendChild(tp);
    }

    _renderFooter() {
      const footer = document.createElement("div");
      footer.className = "erp-date-footer";

      if (this.options.mode !== "time") {
        const todayBtn = this._mkFooterBtn("Dnes", () => {
          const t = _today();
          this._selectDay(t.y, t.m, t.d, /*close*/ false);
        });
        const yesterdayBtn = this._mkFooterBtn("Včera", () => {
          const t = _addDays(_today(), -1);
          this._selectDay(t.y, t.m, t.d, /*close*/ false);
        });
        const tomorrowBtn = this._mkFooterBtn("Zítra", () => {
          const t = _addDays(_today(), 1);
          this._selectDay(t.y, t.m, t.d, /*close*/ false);
        });
        footer.appendChild(todayBtn);
        footer.appendChild(yesterdayBtn);
        footer.appendChild(tomorrowBtn);
      } else {
        const nowBtn = this._mkFooterBtn("Nyní", () => {
          const now = new Date();
          this._parsed = {
            y: null, m: null, d: null,
            hh: now.getHours(), mm: now.getMinutes(),
          };
          this.input.value = _formatDisplay(this._parsed, this.options.mode);
          this._validate();
          this._renderPopup();
          if (typeof this.options.onValidatedChange === "function") {
            try {
              this.options.onValidatedChange(this.rawValue(), this._isValid);
            } catch (e) {}
          }
        });
        footer.appendChild(nowBtn);
      }

      const spacer = document.createElement("div");
      spacer.className = "erp-date-footer-spacer";
      footer.appendChild(spacer);

      const clearBtn = this._mkFooterBtn("Smazat", () => {
        this._parsed = null;
        this.input.value = "";
        this._validate();
        this._renderPopup();
        this.close();
        if (typeof this.options.onChange === "function") {
          try { this.options.onChange(""); } catch (e) {}
        }
        if (typeof this.options.onValidatedChange === "function") {
          try {
            this.options.onValidatedChange("", this._isValid);
          } catch (e) {}
        }
      });
      clearBtn.classList.add("erp-date-footer-btn-danger");
      footer.appendChild(clearBtn);

      this._popup.appendChild(footer);
    }

    _mkFooterBtn(label, onClick) {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "erp-date-footer-btn";
      b.textContent = label;
      b.addEventListener("click", (ev) => {
        ev.preventDefault();
        onClick();
      });
      return b;
    }

    // ── Actions ───────────────────────────────────────────────────

    _navigateMonth(delta) {
      let m = this._viewMonth + delta;
      let y = this._viewYear;
      while (m < 1) { m += 12; y -= 1; }
      while (m > 12) { m -= 12; y += 1; }
      this._viewMonth = m;
      this._viewYear = y;
      this._renderPopup();
      this._positionPopup();
    }

    _toggleYearPicker() {
      // Simple year-jump prompt — minimal UX for MVP
      const v = window.prompt("Skok na rok:", String(this._viewYear));
      if (v == null) return;
      const y = parseInt(v, 10);
      if (isNaN(y) || y < 1900 || y > 2999) return;
      this._viewYear = y;
      this._renderPopup();
      this._positionPopup();
    }

    _selectDay(y, m, d, doClose) {
      // Preserve hh/mm from existing parsed if datetime mode
      const hh = (this._parsed && this.options.mode === "datetime") ? this._parsed.hh : 0;
      const mm = (this._parsed && this.options.mode === "datetime") ? this._parsed.mm : 0;
      this._parsed = { y, m, d, hh, mm };
      this.input.value = _formatDisplay(this._parsed, this.options.mode);
      this._viewYear = y;
      this._viewMonth = m;
      this._validate();
      // Re-render so selection highlight updates
      this._renderPopup();
      if (typeof this.options.onChange === "function") {
        try { this.options.onChange(this.input.value); } catch (e) {}
      }
      if (typeof this.options.onValidatedChange === "function") {
        try {
          this.options.onValidatedChange(this.rawValue(), this._isValid);
        } catch (e) {}
      }
      // For "date" mode close immediately. For "datetime" stay open
      // (user nastaví hh/mm). Footer shortcut buttons předají doClose=false.
      if (doClose === undefined) {
        doClose = (this.options.mode === "date");
      }
      if (doClose) {
        this.close();
        this.input.focus();
      }
    }
  }

  global.ErpDate = ErpDate;
})(typeof window !== "undefined" ? window : globalThis);
