/**
 * ErpForm — UI Kit form orchestrator (auto-render z FormDef metadat).
 *
 * Bere metadata jádra (komponenty + properties + data row), staví DOM
 * pomocí UI Kit komponent (ErpInput, ErpCheckbox, ErpFormList,
 * ErpFormSection). Drží form state (initial vs current) pro Phase C
 * save flow (OK/Storno tlačítka).
 *
 * Architektura:
 *   1. Components z EC_FormDefEdit (Typ + cFieldName + cCaption + cParent)
 *   2. Properties z EC_FormDefEditProperty (LookupView, ReadOnly, ...)
 *   3. Data dict (raw values + _lookup_{field} enriched display labels)
 *   4. Title z FormSetting (Typ=30) FormCaption property nebo FormDef.Nazev
 *
 * State:
 *   _initialValues — snapshot po build (pro dirty diff)
 *   _components    — registry: c_field_name → component instance
 *
 * API:
 *   form.getValues()         { fieldName: currentValue }
 *   form.getInitialValues()  { fieldName: initialValue }
 *   form.getDirtyValues()    diff vs initial — JEN změněné fields
 *   form.getDirtyFields()    array of changed field names
 *   form.isDirty()           boolean
 *   form.validate()          { valid, errors: { fieldName: msg } }
 *   form.setValue(name, val) programmatic update + sync component
 *   form.getField(name)      component instance pro field
 *   form.markClean()         _initialValues = current (po úspěšném save)
 *   form.reset()             restore initial values
 *   form.setReadOnly(bool)   propagate na komponenty
 *   form.setTitle(text)
 *   form.element()           wrapper <form>
 *   form.destroy()
 *
 * Phase B+6.6a (6.5.2026) — most do Phase C edit pipeline.
 * Phase A read-only: Phase A=true. Phase C: read_only=false + footer
 * s OK/Storno (přijde s následující fází).
 */
(function (global) {
  "use strict";

  // EC_FormDefEdit Typ enum
  const TYP_LABEL_ONLY = 1;
  const TYP_EDIT = 2;
  const TYP_CHECKBOX = 3;
  const TYP_DATE = 5;
  const TYP_FORMLIST = 6;
  const TYP_COMBOBOX = 7;
  const TYP_BUTTON = 8;
  const TYP_GROUPBOX = 12;
  const TYP_DATASET = 17;     // non-visual
  const TYP_DBFIELD = 18;     // non-visual
  const TYP_FORMSETTING = 30; // non-visual (FormCaption override)

  const NON_VISUAL_TYPS = new Set([TYP_DATASET, TYP_DBFIELD, TYP_FORMSETTING]);

  function _esc(s) {
    return String(s).replace(/[&<>"']/g, c =>
      ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])
    );
  }

  function _normalize(s) {
    return String(s || "").toLowerCase().replace(/\s+/g, "");
  }

  /**
   * Parse cParent="c{id}" → integer ID. Vrací null pokud format nesedí.
   * Centrála konvence: cParent string ref na GroupBox.id přes prefix "c".
   * Např. "c12" → 12, "c469" → 469.
   * Mirror server-side render_generator._parse_parent_id().
   */
  function _parseParentId(cParent) {
    if (!cParent) return null;
    const s = String(cParent).trim();
    if (!s.startsWith("c") && !s.startsWith("C")) return null;
    const n = parseInt(s.slice(1), 10);
    return Number.isFinite(n) ? n : null;
  }

  /**
   * Resolve real caption — replikuje server-side _resolve_caption().
   * Phase A.3 (render_generator.py): real Caption je v properties,
   * ne v EC_FormDefEdit.cCaption (= "NOVÁ" default při vytvoření).
   *
   * Priorita:
   *   1. properties.Caption / cCaption / PropertyCaption / Text / cText
   *   2. comp.c_caption (pokud != "NOVÁ")
   *   3. comp.c_field_name
   *   4. ""
   */
  function _resolveCaption(comp) {
    const props = comp.properties || {};
    const KEYS = ["Caption", "cCaption", "PropertyCaption", "Text", "cText"];
    for (const k of KEYS) {
      const v = props[k];
      if (v != null && String(v).trim() !== "") return String(v).trim();
    }
    const cc = String(comp.c_caption || "").trim();
    if (cc && cc.toUpperCase() !== "NOVÁ") return cc;
    if (comp.c_field_name && String(comp.c_field_name).trim()) {
      return String(comp.c_field_name).trim();
    }
    return "";
  }

  /**
   * Detect ErpInput type podle komponenta + properties + cMask heuristic.
   * Default = "text".
   */
  function _detectInputType(comp) {
    const fname = _normalize(comp.c_field_name);
    const mask = (comp.c_mask || "").trim();
    // Pattern matching na cFieldName
    if (/^(telefon|tel|phone|mobil)$/.test(fname)) return "phone";
    if (/^(ico|ic)$/.test(fname)) return "ico";
    if (/^dic$/.test(fname)) return "dic";
    if (/^(email|mail)$/.test(fname)) return "email";
    // cMask heuristic
    if (mask.includes("##.##.####") || mask.includes("dd.mm.yyyy")) return "date";
    if (/^\d+(\.\d+)?$/.test(mask) || mask.includes("#,##0")) return "number";
    return "text";
  }

  class ErpForm {
    /**
     * @param {HTMLElement} container — kde se form vykreslí
     * @param {Object} options:
     *   formId           : int (požadováno pro lookup endpoint)
     *   formNazev        : string (default title)
     *   components       : array of {id, typ, c_field_name, c_caption,
     *                                c_parent, c_mask, properties: {}}
     *   data             : dict { field_name: value, _lookup_{field}: display }
     *   readOnly         : boolean (default true v Phase A)
     *   lookupEndpoint   : function(fieldName) → Promise<items[]>
     *                       (default = fetch /api/v1/erp/jadro/{id}/lookup/{f})
     *   onChange         : function(fieldName, newValue, oldValue) — per-field
     *   onAnyChange      : function(form) — kdykoliv se forma změní
     *   onValidate       : function(form, errors) — po každém validate()
     *   debugInfo        : object (přidá <details> Debug info Phase A)
     */
    constructor(container, options) {
      this.container = container || null;
      this.options = Object.assign({
        formId: null,
        formNazev: "",
        components: [],
        data: {},
        readOnly: true,
        lookupEndpoint: null,
        onChange: null,
        onAnyChange: null,
        onValidate: null,
        debugInfo: null,
      }, options || {});
      this._destroyed = false;
      this._components = new Map();   // fieldName → entry {component, getValue, setValue, typ}
      this._sections = [];            // ErpFormSection instances
      this._initialValues = {};       // fieldName → value (snapshot po build)
      this._sourcePropsByField = {};  // fieldName → properties dict (audit)
      this._build();
    }

    _build() {
      this.wrapper = document.createElement("form");
      this.wrapper.className = "erp-form";
      this.wrapper.setAttribute("data-read-only", this.options.readOnly ? "true" : "false");
      if (this.options.formId != null) {
        this.wrapper.setAttribute("data-erp-form-id", String(this.options.formId));
      }
      this.wrapper.addEventListener("submit", (ev) => ev.preventDefault());

      const components = this.options.components || [];
      const data = this.options.data || {};

      // Title — preferuj FormSetting.FormCaption, fallback FormDef.Nazev
      let title = this.options.formNazev || "";
      for (const c of components) {
        if (c.typ === TYP_FORMSETTING) {
          const fc = ((c.properties && c.properties.FormCaption) || "").trim();
          if (fc) { title = fc; break; }
        }
      }
      this.titleEl = null;
      if (title) {
        const header = document.createElement("header");
        header.className = "erp-form-header";
        const h2 = document.createElement("h2");
        h2.className = "erp-form-title";
        h2.textContent = title;
        header.appendChild(h2);
        this.wrapper.appendChild(header);
        this.titleEl = h2;
      }

      // Filter visual components
      const visuals = components.filter(c => !NON_VISUAL_TYPS.has(c.typ));

      // Build sections (Typ=12 = GroupBox)
      const groups = visuals.filter(c => c.typ === TYP_GROUPBOX);
      const fields = visuals.filter(c => c.typ !== TYP_GROUPBOX);

      // Sekce per GroupBox (lookup podle cParent na fieldech)
      // Plus orphan section pro fields bez parenta nebo s neznámým parentem
      // B+6.6c-fix4 (6.5.2026): c_parent konvence je "c{id}" (např. "c12")
      // — string referent na ID GroupBoxu, NE jeho caption. Match přes
      // section by ID, ne by name. (Server-side render_generator.py
      // _parse_parent_id má stejnou logiku.)
      const sectionById = new Map();  // groupbox.id (number) → ErpFormSection
      groups.forEach(g => {
        const realCaption = _resolveCaption(g);
        const sec = new global.ErpFormSection(this.wrapper, {
          title: realCaption,
        });
        sectionById.set(g.id, sec);
        this._sections.push(sec);
      });

      // Orphan section (lazy create — jen pokud je potřeba)
      let orphanSection = null;
      const ensureOrphan = () => {
        if (!orphanSection) {
          orphanSection = new global.ErpFormSection(this.wrapper, {
            title: "",
            orphan: true,
          });
          this._sections.push(orphanSection);
        }
        return orphanSection;
      };

      // Dispatch fields → komponenty + assign do sekcí
      const lookupFieldRefs = [];  // {comp, lookupField} — pro hide siblings post-build
      const buttonComps = [];      // Typ=8 — footer
      for (const comp of fields) {
        if (comp.typ === TYP_BUTTON) {
          buttonComps.push(comp);
          continue;
        }
        const fieldName = comp.c_field_name || "";
        const rawValue = fieldName ? this._extractValue(data, fieldName) : null;
        const lookupDisplay = (fieldName && data["_lookup_" + fieldName] != null)
          ? data["_lookup_" + fieldName]
          : null;
        const entry = this._buildField(comp, rawValue, lookupDisplay);
        if (!entry) continue;

        // Audit properties
        if (fieldName) {
          this._sourcePropsByField[fieldName] = comp.properties || {};
        }

        // Register
        if (entry.fieldName) {
          this._components.set(entry.fieldName, entry);
          // Initial value snapshot
          this._initialValues[entry.fieldName] = entry.getValue();
        }

        // Lookup ref pro post-build sibling hide
        if ((comp.typ === TYP_FORMLIST || comp.typ === TYP_COMBOBOX) &&
            comp.properties && comp.properties.LookupField) {
          lookupFieldRefs.push({
            comp: comp,
            lookupField: comp.properties.LookupField.trim(),
          });
        }

        // Place do sekce — match cParent="c{id}" na GroupBox.id
        const parentRaw = String(comp.c_parent || "").trim();
        const parentId = _parseParentId(parentRaw);
        let targetSec = null;
        if (parentId != null && sectionById.has(parentId)) {
          targetSec = sectionById.get(parentId);
        } else {
          // No parent OR parent ID nenalezen mezi GroupBoxes → orphan
          targetSec = ensureOrphan();
        }
        if (entry.component) {
          targetSec.addField(entry.component);
        } else if (entry.element) {
          targetSec.addField(entry.element);
        }
      }

      // Post-build: hide sourozenecké FK fields. Dvě cesty:
      // (1) Primary — LookupField property z Centrála metadat (clean)
      // (2) Fallback heuristic — value match (B+6.4+++ logic): FK value
      //     v lookup === input.value sourozence Edit fieldu.
      // Centrála nemusí mít LookupField property na všech FormList /
      // Combobox — Marti's UI feedback po B+6.6c-fix4 ukázal že fallback
      // je nutný.
      const hiddenFieldNames = new Set();
      // (1) LookupField property
      for (const ref of lookupFieldRefs) {
        const lookupFieldName = ref.lookupField;
        if (!lookupFieldName) continue;
        const sibling = this._components.get(lookupFieldName);
        if (sibling && sibling.component &&
            typeof sibling.component.wrapperElement === "function") {
          const el = sibling.component.wrapperElement();
          if (el) {
            el.style.display = "none";
            el.setAttribute("data-erp-hidden-sibling", "true");
            hiddenFieldNames.add(lookupFieldName);
          }
        }
      }
      // (2) Heuristic fallback — pro každý FormList/Combobox najdi
      // Edit sourozence jehož initial value === lookup FK value.
      for (const [name, entry] of this._components.entries()) {
        if (entry.typ !== TYP_FORMLIST && entry.typ !== TYP_COMBOBOX) continue;
        const fk = entry.getValue();
        if (fk == null || fk === "") continue;
        const fkStr = String(fk).trim();
        for (const [otherName, otherEntry] of this._components.entries()) {
          if (otherName === name) continue;
          if (hiddenFieldNames.has(otherName)) continue;
          if (otherEntry.typ !== TYP_EDIT) continue;
          // Initial value match (snapshot from _initialValues)
          const otherInitial = this._initialValues[otherName];
          if (otherInitial == null) continue;
          if (String(otherInitial).trim() !== fkStr) continue;
          // Match — schovat
          if (otherEntry.component &&
              typeof otherEntry.component.wrapperElement === "function") {
            const el = otherEntry.component.wrapperElement();
            if (el) {
              el.style.display = "none";
              el.setAttribute("data-erp-hidden-sibling", "true");
              hiddenFieldNames.add(otherName);
            }
          }
          break;  // jen první match per lookup
        }
      }

      // Footer s Buttons (Typ=8) — Phase A: žádný save flow, jen render
      // labels jako readonly buttons. Phase C: OK/Storno bind handlers.
      if (buttonComps.length > 0) {
        const footer = document.createElement("footer");
        footer.className = "erp-form-footer";
        buttonComps.forEach((b) => {
          const caption = (_resolveCaption(b) || "Akce").trim();
          if (typeof global.ErpButton === "function") {
            const isPrimary = /^(ok|uložit|save)$/i.test(caption);
            const isCancel = /^(storno|cancel|zrušit|zavřít)$/i.test(caption);
            const variant = isPrimary ? "primary"
                          : isCancel  ? "ghost"
                          : "secondary";
            new global.ErpButton(footer, {
              label: caption,
              variant: variant,
              size: "medium",
              disabled: this.options.readOnly,
              onClick: () => {
                if (caption === "OK" && typeof this.options.onSubmit === "function") {
                  try { this.options.onSubmit(this); } catch (e) { console.warn(e); }
                }
              },
            });
          } else {
            // Fallback
            const btn = document.createElement("button");
            btn.type = "button";
            btn.className = "erp-btn";
            btn.textContent = caption;
            btn.disabled = this.options.readOnly;
            footer.appendChild(btn);
          }
        });
        this.wrapper.appendChild(footer);
      }

      // Debug panel (volitelný — pro Phase A landing parity)
      if (this.options.debugInfo) {
        this._renderDebugPanel(this.options.debugInfo);
      }

      if (this.container) this.container.appendChild(this.wrapper);
    }

    /**
     * Extract value z data dict — case-insensitive fallback
     * (Centrála data row může mít keys v jiném case než cFieldName).
     */
    _extractValue(data, fieldName) {
      if (data[fieldName] !== undefined) return data[fieldName];
      // Case-insensitive lookup
      const lower = fieldName.toLowerCase();
      for (const k of Object.keys(data)) {
        if (k.toLowerCase() === lower) return data[k];
      }
      return null;
    }

    /**
     * Dispatcher: comp + value → komponenta entry.
     * Returns { component, fieldName, getValue, setValue, typ } pokud
     * komponenta, NEBO { element, fieldName, getValue, setValue, typ } pokud
     * raw element.
     */
    _buildField(comp, value, lookupDisplay) {
      const fieldName = comp.c_field_name || "";
      // B+6.6c-fix2 (6.5.2026): _resolveCaption replikuje server-side
      // logiku — properties.Caption má prioritu, "NOVÁ" default je
      // skrytý, fallback field_name (Phase A.3).
      const caption = _resolveCaption(comp) || fieldName || "";
      const isReadOnly = this.options.readOnly;
      const props = comp.properties || {};
      const isFieldReadOnly = isReadOnly ||
        ((props.ReadOnly || "").toString().toLowerCase() === "true") ||
        ((props.ReadOnly || "").toString() === "1");

      const typ = comp.typ;

      // Helper: emit change event do onAnyChange
      const emitChange = (oldV, newV) => {
        if (typeof this.options.onChange === "function") {
          try { this.options.onChange(fieldName, newV, oldV); } catch (e) {}
        }
        if (typeof this.options.onAnyChange === "function") {
          try { this.options.onAnyChange(this); } catch (e) {}
        }
      };

      switch (typ) {
        case TYP_LABEL_ONLY: {
          const el = document.createElement("div");
          el.className = "erp-label-only";
          el.textContent = caption;
          return { element: el, fieldName: null, getValue: () => null, setValue: () => {}, typ };
        }

        case TYP_EDIT: {
          if (typeof global.ErpInput !== "function") return null;
          const inputType = _detectInputType(comp);
          const inp = new global.ErpInput(null, {
            type: inputType,
            label: caption,
            value: value != null ? String(value) : "",
            readonly: isFieldReadOnly,
            onValidatedChange: (raw, isValid) => {
              emitChange(this._initialValues[fieldName], raw);
            },
          });
          return {
            component: inp,
            fieldName: fieldName,
            getValue: () => {
              const raw = inp.rawValue();
              return raw !== "" ? raw : (inp.value() || "");
            },
            setValue: (v) => inp.setValue(v),
            typ: typ,
            instance: inp,
          };
        }

        case TYP_CHECKBOX: {
          if (typeof global.ErpCheckbox !== "function") return null;
          const cb = new global.ErpCheckbox(null, {
            label: caption,
            checked: !!value && value !== "0" && value !== 0,
            readonly: isFieldReadOnly,
            disabled: false,
            onChange: (newV) => {
              emitChange(this._initialValues[fieldName], newV);
            },
          });
          return {
            component: cb,
            fieldName: fieldName,
            getValue: () => cb.value(),
            setValue: (v) => cb.setValue(!!v),
            typ: typ,
            instance: cb,
          };
        }

        case TYP_DATE: {
          if (typeof global.ErpInput !== "function") return null;
          const inp = new global.ErpInput(null, {
            type: "date",
            label: caption,
            value: value != null ? String(value) : "",
            readonly: isFieldReadOnly,
            onValidatedChange: (raw, isValid) => {
              emitChange(this._initialValues[fieldName], raw);
            },
          });
          return {
            component: inp,
            fieldName: fieldName,
            getValue: () => inp.rawValue(),
            setValue: (v) => inp.setValue(v),
            typ: typ,
            instance: inp,
          };
        }

        case TYP_FORMLIST:
        case TYP_COMBOBOX: {
          if (typeof global.ErpFormList !== "function") return null;
          const fl = new global.ErpFormList(null, {
            label: caption,
            value: value,
            displayValue: lookupDisplay != null
              ? String(lookupDisplay)
              : (value != null ? String(value) : ""),
            showValuePrefix: true,
            valuePrefixWidth: "60px",
            items: [],
            readonly: isFieldReadOnly,
            onLoadItems: () => this._loadLookupOptions(fieldName),
            browseTitle: caption ? "Vybrat — " + caption : "Vybrat hodnotu",
            browseColumns: [
              { field: "value", header: "Číslo", width: "100px" },
              { field: "label", header: "Název", width: "auto" },
            ],
            onChange: (newV, item) => {
              const oldV = this._initialValues[fieldName];
              emitChange(oldV, newV);
              // Propagate FK do sourozenecké hidden Edit komponenty
              const lookupFieldName = (comp.properties &&
                comp.properties.LookupField || "").trim();
              if (lookupFieldName && lookupFieldName !== fieldName) {
                const sib = this._components.get(lookupFieldName);
                if (sib && typeof sib.setValue === "function") {
                  sib.setValue(newV);
                }
              }
            },
          });
          return {
            component: fl,
            fieldName: fieldName,
            getValue: () => fl.value(),
            setValue: (v, displayValue) => fl.setValue(v, displayValue),
            typ: typ,
            instance: fl,
          };
        }

        case TYP_GROUPBOX:
          // Handled v sections building — never reaches here normally
          return null;

        default: {
          const el = document.createElement("div");
          el.className = "erp-unknown";
          el.textContent = "Typ=" + typ + " " + caption;
          return { element: el, fieldName: null, getValue: () => null, setValue: () => {}, typ };
        }
      }
    }

    /**
     * Default lookup loader — fetch /api/v1/erp/jadro/{formId}/lookup/{field}
     * Lze override přes options.lookupEndpoint.
     */
    async _loadLookupOptions(fieldName) {
      if (typeof this.options.lookupEndpoint === "function") {
        try { return await this.options.lookupEndpoint(fieldName); }
        catch (e) { console.warn("ErpForm lookupEndpoint error:", e); return []; }
      }
      if (this.options.formId == null) return [];
      try {
        const r = await fetch(
          "/api/v1/erp/jadro/" + encodeURIComponent(this.options.formId) +
            "/lookup/" + encodeURIComponent(fieldName),
          { credentials: "include" }
        );
        if (!r.ok) return [];
        const j = await r.json();
        return (j.ok && Array.isArray(j.items)) ? j.items : [];
      } catch (e) {
        console.warn("ErpForm fetch lookup error:", e);
        return [];
      }
    }

    _renderDebugPanel(debugInfo) {
      const wrap = document.createElement("details");
      wrap.className = "erp-debug erp-form-debug";
      const summary = document.createElement("summary");
      summary.textContent = "⚙ Debug info (Phase A)";
      wrap.appendChild(summary);
      const pre = document.createElement("pre");
      try {
        pre.textContent = JSON.stringify(debugInfo, null, 2);
      } catch (e) {
        pre.textContent = String(debugInfo);
      }
      wrap.appendChild(pre);
      this.wrapper.appendChild(wrap);
    }

    // ── Public API ──────────────────────────────────────────────────

    element() { return this.wrapper; }
    wrapperElement() { return this.wrapper; }

    /** Returns dict { fieldName: currentValue } pro VŠECHNY registered fields. */
    getValues() {
      const out = {};
      for (const [name, entry] of this._components.entries()) {
        out[name] = entry.getValue();
      }
      return out;
    }

    /** Returns dict { fieldName: initialValue } — snapshot po build. */
    getInitialValues() {
      return Object.assign({}, this._initialValues);
    }

    /** Returns dict { fieldName: newValue } — JEN změněné fields vs initial. */
    getDirtyValues() {
      const out = {};
      const current = this.getValues();
      for (const name of Object.keys(current)) {
        if (!this._isEqual(current[name], this._initialValues[name])) {
          out[name] = current[name];
        }
      }
      return out;
    }

    /** Array of changed field names. */
    getDirtyFields() {
      return Object.keys(this.getDirtyValues());
    }

    /** Boolean — máme nějaké dirty fields? */
    isDirty() {
      const current = this.getValues();
      for (const name of Object.keys(current)) {
        if (!this._isEqual(current[name], this._initialValues[name])) return true;
      }
      return false;
    }

    _isEqual(a, b) {
      if (a === b) return true;
      // null/undefined/empty treat jako equivalent
      const aEmpty = a === null || a === undefined || a === "";
      const bEmpty = b === null || b === undefined || b === "";
      if (aEmpty && bEmpty) return true;
      // String coerce pro numeric FK ("18" === 18)
      return String(a) === String(b);
    }

    /** Validate všechny fields (B+6.2 ErpInput.validate(), B+6.4+ ErpFormList).
     *  Returns { valid: bool, errors: { fieldName: msg } }.
     */
    validate() {
      const errors = {};
      for (const [name, entry] of this._components.entries()) {
        const inst = entry.instance;
        if (inst && typeof inst.validate === "function") {
          const ok = inst.validate();
          if (!ok && typeof inst.options === "object" && inst.options &&
              typeof inst._errorMsg === "string" && inst._errorMsg) {
            errors[name] = inst._errorMsg;
          } else if (!ok) {
            errors[name] = "Neplatná hodnota";
          }
        }
      }
      const result = { valid: Object.keys(errors).length === 0, errors };
      if (typeof this.options.onValidate === "function") {
        try { this.options.onValidate(this, result); } catch (e) {}
      }
      return result;
    }

    /** Programmatic value set + sync component. */
    setValue(fieldName, value, displayValue) {
      if (this._destroyed) return;
      const entry = this._components.get(fieldName);
      if (!entry) return;
      try {
        if (entry.typ === TYP_FORMLIST || entry.typ === TYP_COMBOBOX) {
          entry.setValue(value, displayValue);
        } else {
          entry.setValue(value);
        }
      } catch (e) {
        console.warn("ErpForm.setValue error", fieldName, e);
      }
    }

    /** Get component instance pro field (ErpInput / ErpCheckbox / ErpFormList). */
    getField(fieldName) {
      const entry = this._components.get(fieldName);
      return entry ? entry.instance : null;
    }

    /** Get array of all field names (registered components). */
    getFieldNames() {
      return Array.from(this._components.keys());
    }

    /** Reset _initialValues = current. Po úspěšném save (Phase C). */
    markClean() {
      if (this._destroyed) return;
      this._initialValues = this.getValues();
    }

    /** Restore initial values do všech komponent. */
    reset() {
      if (this._destroyed) return;
      for (const [name, entry] of this._components.entries()) {
        const initVal = this._initialValues[name];
        try { entry.setValue(initVal); } catch (e) {}
      }
    }

    setReadOnly(readOnly) {
      if (this._destroyed) return;
      this.options.readOnly = !!readOnly;
      this.wrapper.setAttribute("data-read-only", readOnly ? "true" : "false");
      for (const [, entry] of this._components.entries()) {
        const inst = entry.instance;
        if (inst && typeof inst.setReadonly === "function") {
          try { inst.setReadonly(readOnly); } catch (e) {}
        }
      }
    }

    setTitle(title) {
      if (this._destroyed) return;
      if (this.titleEl) this.titleEl.textContent = title || "";
    }

    isReadOnly() { return !!this.options.readOnly; }
    getFormId() { return this.options.formId; }

    destroy() {
      if (this._destroyed) return;
      this._destroyed = true;
      // Destroy all sections (které destroy fields)
      for (const sec of this._sections) {
        if (sec && typeof sec.destroy === "function") {
          try { sec.destroy(); } catch (e) {}
        }
      }
      this._sections = [];
      this._components.clear();
      this._initialValues = {};
      if (this.wrapper && this.wrapper.parentNode) {
        this.wrapper.parentNode.removeChild(this.wrapper);
      }
      this.wrapper = null;
    }
  }

  global.ErpForm = ErpForm;
  global.ErpForm_TYP = {
    LABEL_ONLY: TYP_LABEL_ONLY,
    EDIT: TYP_EDIT,
    CHECKBOX: TYP_CHECKBOX,
    DATE: TYP_DATE,
    FORMLIST: TYP_FORMLIST,
    COMBOBOX: TYP_COMBOBOX,
    BUTTON: TYP_BUTTON,
    GROUPBOX: TYP_GROUPBOX,
  };
})(typeof window !== "undefined" ? window : this);
