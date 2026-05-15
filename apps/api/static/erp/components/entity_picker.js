/* eslint-disable */
/**
 * Phase 38.4 Krok 14g-H+31 (15.5.2026 vecer, Marti's "vyrobit
 * plnohodnotnou FW komponentu z provizornich inline groupboxu"):
 * ErpEntityPicker — reusable widget pro 1:1 FK vazbu na entitu.
 *
 * Layout (1 groupbox, 4 prvku inline):
 *   ┌─ {label} ─────────────────────────────────────┐
 *   │  [🔗]  [🚫]  [Číslo: {id}]  [Název: {name}]    │
 *   └────────────────────────────────────────────────┘
 *
 * Pouziti:
 *   const picker = new ErpEntityPicker({
 *     label: "Přehled",
 *     subtitle: "fw.core — vazba na core_id",
 *     entity: { id: 22, name: "Editace uživatele", code: "user_edit" },
 *     pickerConfig: {
 *       title: "🔗 Vybrat core přehled",
 *       endpoint: "/api/v1/erp/design/fw-core/list",
 *       listKey: "cores",
 *       labelField: "label",
 *       columns: [...]
 *     },
 *     placeholderText: "(žádný core — klik 🔗)",
 *     onPick: (row) => this._associateCoreWithMenuNode(row.id, row.label),
 *     onUnassociate: () => this._unassociateCore(),
 *     onCreate: (prefilledCode) => this._openCoreCreateForm(),
 *     showCreate: true,
 *   });
 *   picker.mount(parentEl);
 *
 * Public API:
 *   - mount(parentEl) — append wrapper element to parent
 *   - setEntity(entity) — update displayed state (re-render)
 *   - clear() — set to empty placeholder state
 *   - getEntity() — returns current { id, name, code }
 *   - dispose() — cleanup
 */
(function(global) {
  "use strict";

  // Helpers — same as design_forms.js _sectionBuild + _field stripped down.
  function _sectionBuild(label, subtitle) {
    const wrap = document.createElement("div");
    wrap.className = "erp-design-section";
    wrap.style.cssText =
      "margin-bottom:14px;border:1px solid #2a3340;border-radius:5px;" +
      "background:#13181f;display:flex;flex-direction:column;";

    const header = document.createElement("div");
    header.className = "erp-design-section-title";
    header.style.cssText =
      "padding:8px 12px;border-bottom:1px solid #2a3340;background:#1a2028;" +
      "color:#a8c4dc;font-size:11px;font-weight:600;letter-spacing:0.05em;" +
      "text-transform:uppercase;display:flex;align-items:center;gap:8px;";
    header.textContent = label;
    if (subtitle) {
      const sub = document.createElement("span");
      sub.style.cssText =
        "color:#6a7682;font-weight:400;font-size:10px;text-transform:none;" +
        "letter-spacing:normal;font-style:italic;margin-left:6px;";
      sub.textContent = subtitle;
      header.appendChild(sub);
    }
    wrap.appendChild(header);

    const grid = document.createElement("div");
    grid.className = "erp-design-section-grid";
    grid.style.cssText =
      "padding:10px 12px;display:flex;flex-direction:row;align-items:flex-end;" +
      "gap:8px;flex-wrap:wrap;";
    wrap.appendChild(grid);

    return { wrap, header, grid };
  }

  function _mkLabeledInput(label, value, opts) {
    opts = opts || {};
    const fwrap = document.createElement("div");
    fwrap.style.cssText = "display:flex;flex-direction:column;gap:4px;";
    if (opts.style) fwrap.setAttribute("style", fwrap.getAttribute("style") + opts.style);

    const lbl = document.createElement("label");
    lbl.style.cssText =
      "color:#a8b4c2;font-size:10px;font-weight:500;letter-spacing:0.03em;" +
      "display:flex;align-items:center;gap:4px;";
    lbl.textContent = label;
    if (opts.locked) {
      const lock = document.createElement("span");
      lock.textContent = "🔒";
      lock.style.cssText = "font-size:10px;opacity:0.6;";
      lbl.appendChild(lock);
    }
    fwrap.appendChild(lbl);

    const input = document.createElement("input");
    input.type = "text";
    input.value = (value === null || value === undefined) ? "" : String(value);
    input.readOnly = true;
    input.placeholder = opts.placeholder || "";
    const monoCss = opts.mono ? "font-family:monospace;" : "";
    input.style.cssText =
      "padding:7px 10px;background:#0f141a;border:1px solid #2a3340;" +
      "border-radius:4px;color:#cfd6df;font-size:12px;outline:none;" +
      monoCss +
      "cursor:default;";
    if (input.value === "") {
      input.style.color = "#5a6573";
    }
    fwrap.appendChild(input);

    return { wrap: fwrap, input };
  }

  function _mkIconBtn(icon, title, accentColor, handler, disabled) {
    const colWrap = document.createElement("div");
    colWrap.style.cssText =
      "display:flex;flex-direction:column;justify-content:flex-end;flex:0 0 auto;";
    const b = document.createElement("button");
    b.type = "button";
    const dim = disabled ? "#4a4a4a" : accentColor;
    b.style.cssText =
      "padding:7px 10px;background:#1f262f;border:1px solid " + dim + ";" +
      "color:" + dim + ";border-radius:4px;cursor:" +
      (disabled ? "not-allowed" : "pointer") + ";" +
      "font-size:14px;line-height:1;min-width:34px;height:32px;" +
      (disabled ? "opacity:0.65;" : "");
    b.textContent = icon;
    b.title = title;
    if (!disabled) {
      b.onmouseover = () => { b.style.background = "#252d37"; };
      b.onmouseout = () => { b.style.background = "#1f262f"; };
      b.onclick = handler;
    } else {
      b.onclick = (e) => {
        e.preventDefault();
        if (typeof handler === "function") handler();
      };
    }
    colWrap.appendChild(b);
    return colWrap;
  }

  class ErpEntityPicker {
    constructor(opts) {
      this.opts = opts || {};
      // Defaults
      this.opts.label = this.opts.label || "Entity";
      this.opts.subtitle = this.opts.subtitle || "";
      this.opts.placeholderText = this.opts.placeholderText || "(prázdno — klik 🔗)";
      this.opts.idLabel = this.opts.idLabel || "Číslo";
      this.opts.nameLabel = this.opts.nameLabel || "Název";
      this.opts.showCreate = this.opts.showCreate !== false; // default true
      this.opts.showUnassociate = this.opts.showUnassociate !== false; // default true

      this._entity = this.opts.entity || null;
      this._sectionEl = null; // root wrapper
      this._mounted = false;
    }

    /**
     * Render the picker into parentEl. Idempotent — second call re-mounts.
     */
    mount(parentEl) {
      if (this._mounted) {
        this.dispose();
      }
      const section = _sectionBuild(this.opts.label, this.opts.subtitle);
      this._sectionEl = section.wrap;
      this._renderInto(section.grid);
      parentEl.appendChild(section.wrap);
      this._mounted = true;
      return this._sectionEl;
    }

    /**
     * Update displayed state (after picker pick or external data refresh).
     * Re-renders inline.
     */
    setEntity(entity) {
      this._entity = entity || null;
      if (this._mounted && this._sectionEl) {
        const grid = this._sectionEl.querySelector(".erp-design-section-grid");
        if (grid) {
          grid.innerHTML = "";
          this._renderInto(grid);
        }
      }
    }

    clear() {
      this.setEntity(null);
    }

    getEntity() {
      return this._entity ? Object.assign({}, this._entity) : null;
    }

    dispose() {
      if (this._sectionEl && this._sectionEl.parentNode) {
        this._sectionEl.parentNode.removeChild(this._sectionEl);
      }
      this._sectionEl = null;
      this._mounted = false;
    }

    // ─── Internal ────────────────────────────────────────────────

    _renderInto(grid) {
      const hasEntity = !!(this._entity && this._entity.id);
      const disabled = !!this.opts.disabled;
      const readOnly = !!this.opts.readOnly;
      const self = this;

      // Phase 38.4 Krok 14g-H+31 step 3 (15.5.2026 vecer, Marti's
      // "pridat Soudecek nad Prehled+Datovy zdroj"): readOnly option
      // — skip 🔗 + 🚫 buttons, just display ID + Name (Soudecek picker
      // ukazuje aktualne editovany menu_node, ne picker akce).
      if (!readOnly) {
        // 1. 🔗 Picker
        const pickTitle = disabled
          ? (this.opts.disabledReason || "Nelze otevřít picker")
          : (hasEntity
              ? "Změnit asociovanou entitu"
              : "Vybrat existing entitu (nebo ➕ Nová)");
        grid.appendChild(_mkIconBtn(
          "🔗",
          pickTitle,
          "#4a7ba8",
          () => self._handlePickerClick(),
          disabled
        ));

        // 2. 🚫 Unassociate (only if hasEntity AND showUnassociate)
        if (hasEntity && this.opts.showUnassociate) {
          grid.appendChild(_mkIconBtn(
            "🚫",
            "Zrušit asociaci.\nEntita sama zůstane v DB.",
            "#8a3a3a",
            () => self._handleUnassociateClick()
          ));
        }
      }

      // 3. Číslo (compact)
      const idWrap = _mkLabeledInput(
        this.opts.idLabel,
        hasEntity ? this._entity.id : "",
        { mono: true, locked: true }
      );
      idWrap.wrap.style.flex = "0 0 100px";
      grid.appendChild(idWrap.wrap);

      // 4. Název (flex)
      const nameValue = hasEntity
        ? (this._entity.name || this._entity.label || this._entity.code || "")
        : "";
      const namePlaceholder = hasEntity ? "" : this.opts.placeholderText;
      const nameWrap = _mkLabeledInput(
        this.opts.nameLabel,
        nameValue,
        { locked: true, placeholder: namePlaceholder }
      );
      nameWrap.wrap.style.flex = "1 1 200px";
      nameWrap.wrap.style.minWidth = "200px";
      grid.appendChild(nameWrap.wrap);
    }

    _handlePickerClick() {
      const self = this;
      if (this.opts.disabled) {
        // Show disabled reason via dialog if available, else alert.
        const reason = this.opts.disabledReason || "Picker je aktuálně nedostupný.";
        if (typeof global._confirmDarkDialog === "function") {
          global._confirmDarkDialog({
            title: "Picker nedostupný",
            message: reason,
            ok: "OK",
            cancel: null,
          });
        } else {
          alert(reason);
        }
        return;
      }
      if (typeof global.ErpCatalogPicker !== "function") {
        alert("ErpCatalogPicker není načten (catalog_picker.js missing).");
        return;
      }

      const cfg = Object.assign({}, this.opts.pickerConfig || {});
      // Wire onSelect to internal handler that calls onPick callback.
      const userOnSelect = cfg.onSelect;
      cfg.onSelect = (row) => {
        if (typeof userOnSelect === "function") userOnSelect(row);
        if (typeof self.opts.onPick === "function") self.opts.onPick(row);
      };
      // Wire enableNew + onNew if showCreate.
      if (self.opts.showCreate) {
        cfg.enableNew = true;
        const userOnNew = cfg.onNew;
        cfg.onNew = (picker) => {
          if (typeof userOnNew === "function") userOnNew(picker);
          if (typeof self.opts.onCreate === "function") {
            self.opts.onCreate(picker, self.opts.prefillCode || null);
          }
        };
      }

      const picker = new global.ErpCatalogPicker(cfg);
      picker.open();
    }

    _handleUnassociateClick() {
      if (typeof this.opts.onUnassociate === "function") {
        this.opts.onUnassociate();
      } else {
        console.warn("[ErpEntityPicker] onUnassociate callback not set");
      }
    }
  }

  global.ErpEntityPicker = ErpEntityPicker;
})(window);
