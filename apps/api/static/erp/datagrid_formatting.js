/**
 * ErpGridFormatting — AG-native conditional formatting engine + UI editor.
 *
 * Phase B+10+ (6.5.2026). Marti's spec: "Per-layout pravidla, AG nativni,
 * tak jak to maji oni... Pro production mode neco mit musime, jinak mi to
 * lidi pomluvi".
 *
 * AG Grid Enterprise v32 NEMÁ native UI dialog (žádný Excel-like Format
 * Cells popup). Mají jen API: cellClassRules / rowClassRules / cellStyle.
 * Tj. **native rendering, custom UI editor**.
 *
 * Architektura:
 *   - Storage: erp_grid_layouts.layout_json.formatting_rules (žádná migrace,
 *     JSONB array). Plus layout_json.heuristics_enabled (B+10 opt-in).
 *   - Compile: rules array → AG Grid format
 *     • cell-scope rule → cellClassRules na column def
 *     • row-scope rule → rowClassRules na grid options
 *   - Render: AG Grid native (gridApi.setColumnDefs / setGridOption)
 *   - Editor: custom modal (10 operátorů, 8 preset colors, drag-drop reorder)
 *
 * Rule schema:
 *   {
 *     id: "uuid-or-counter",       // stable identifier (drag reorder, edit)
 *     column: "FirmaText" | "*",   // "*" = whole-row scope
 *     operator: "eq"|"neq"|"lt"|"lte"|"gt"|"gte"|"empty"|"notempty"|"contains"|"startswith",
 *     value: "...",                 // string (parsed na číslo / datum dle context)
 *     color: "red"|"orange"|"yellow"|"green"|"blue"|"purple"|"gray"|"strike",
 *     scope: "cell"|"row",         // cell = jen ta buňka, row = celý řádek
 *     order: 0                      // priority order (1st match wins per scope)
 *   }
 *
 * Public API (window.ErpGridFormatting):
 *   - OPERATORS: {key: {label, predicate(val, target), valueRequired, types}}
 *   - PRESET_COLORS: array {key, label, swatch, cellClass, rowClass}
 *   - compile(rules, columnDefs) → {cellClassRulesByCol, rowClassRules}
 *   - openEditor({rules, columns, onSave}) — modal Promise<rules[]>
 */
(function (global) {
  "use strict";

  // Phase JS-9 (18.5.2026): mutual immunity wrap pro Module Health visibility.
  const _loader = (typeof global !== "undefined" && global._erpLoadModule)
    ? global._erpLoadModule
    : function (id, ver, fn) { try { fn(); } catch (e) { console.error("[" + id + "] init failed:", e); } };

  _loader("datagrid_formatting.js", "v1.0.0", function () {


  // ── Operator definitions ────────────────────────────────────────────

  const OPERATORS = {
    eq: {
      label: "= rovná se",
      valueRequired: true,
      types: ["string", "number", "date", "boolean"],
      predicate: (val, target) => {
        if (val == null) return false;
        // Loose match — handle string vs number coexistence ("1" == 1)
        if (target === "" || target == null) return val === "" || val == null;
        return String(val).toLowerCase() === String(target).toLowerCase();
      },
    },
    neq: {
      label: "≠ není",
      valueRequired: true,
      types: ["string", "number", "date", "boolean"],
      predicate: (val, target) => {
        if (val == null) return target !== "" && target != null;
        return String(val).toLowerCase() !== String(target).toLowerCase();
      },
    },
    lt: {
      label: "< menší",
      valueRequired: true,
      types: ["number", "date"],
      predicate: (val, target) => _numCompare(val, target, (a, b) => a < b),
    },
    lte: {
      label: "≤ menší/rovno",
      valueRequired: true,
      types: ["number", "date"],
      predicate: (val, target) => _numCompare(val, target, (a, b) => a <= b),
    },
    gt: {
      label: "> větší",
      valueRequired: true,
      types: ["number", "date"],
      predicate: (val, target) => _numCompare(val, target, (a, b) => a > b),
    },
    gte: {
      label: "≥ větší/rovno",
      valueRequired: true,
      types: ["number", "date"],
      predicate: (val, target) => _numCompare(val, target, (a, b) => a >= b),
    },
    empty: {
      label: "je prázdné",
      valueRequired: false,
      types: ["string", "number", "date", "boolean"],
      predicate: (val) => val == null || val === "",
    },
    notempty: {
      label: "není prázdné",
      valueRequired: false,
      types: ["string", "number", "date", "boolean"],
      predicate: (val) => val != null && val !== "",
    },
    contains: {
      label: "obsahuje",
      valueRequired: true,
      types: ["string"],
      predicate: (val, target) => {
        if (val == null) return false;
        return String(val).toLowerCase().includes(String(target).toLowerCase());
      },
    },
    startswith: {
      label: "začíná na",
      valueRequired: true,
      types: ["string"],
      predicate: (val, target) => {
        if (val == null) return false;
        return String(val).toLowerCase().startsWith(String(target).toLowerCase());
      },
    },
  };

  /**
   * Numeric / date comparison. Coerce both sides — handle ISO date string,
   * "1234,56" CS number, etc.
   */
  function _numCompare(val, target, cmp) {
    if (val == null || val === "") return false;
    const a = _coerceNum(val);
    const b = _coerceNum(target);
    if (a == null || b == null) return false;
    return cmp(a, b);
  }

  function _coerceNum(v) {
    if (v == null || v === "") return null;
    if (typeof v === "number") return v;
    const s = String(v).trim();
    // ISO date YYYY-MM-DD → epoch ms
    const m = s.match(/^(\d{4})-(\d{2})-(\d{2})/);
    if (m) {
      const dt = new Date(parseInt(m[1], 10), parseInt(m[2], 10) - 1, parseInt(m[3], 10));
      if (!isNaN(dt.getTime())) return dt.getTime();
    }
    // CS date D.M.YYYY → epoch ms
    const cs = s.match(/^(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})/);
    if (cs) {
      const dt = new Date(parseInt(cs[3], 10), parseInt(cs[2], 10) - 1, parseInt(cs[1], 10));
      if (!isNaN(dt.getTime())) return dt.getTime();
    }
    // Number — strip CS thousands separator (space) + replace , with .
    const cleaned = s.replace(/\s/g, "").replace(",", ".");
    const n = parseFloat(cleaned);
    return Number.isFinite(n) ? n : null;
  }

  // ── Preset colors (8 pastel) ───────────────────────────────────────

  const PRESET_COLORS = [
    { key: "red",    label: "Červená",   swatch: "#ef4444", cellClass: "erp-fmt-cell-red",    rowClass: "erp-fmt-row-red" },
    { key: "orange", label: "Oranžová",  swatch: "#f97316", cellClass: "erp-fmt-cell-orange", rowClass: "erp-fmt-row-orange" },
    { key: "yellow", label: "Žlutá",     swatch: "#eab308", cellClass: "erp-fmt-cell-yellow", rowClass: "erp-fmt-row-yellow" },
    { key: "green",  label: "Zelená",    swatch: "#22c55e", cellClass: "erp-fmt-cell-green",  rowClass: "erp-fmt-row-green" },
    { key: "blue",   label: "Modrá",     swatch: "#3b82f6", cellClass: "erp-fmt-cell-blue",   rowClass: "erp-fmt-row-blue" },
    { key: "purple", label: "Fialová",   swatch: "#a855f7", cellClass: "erp-fmt-cell-purple", rowClass: "erp-fmt-row-purple" },
    { key: "gray",   label: "Šedá",      swatch: "#6b7280", cellClass: "erp-fmt-cell-gray",   rowClass: "erp-fmt-row-gray" },
    { key: "strike", label: "Přeškrtnuto", swatch: "#94a3b8", cellClass: "erp-fmt-cell-strike", rowClass: "erp-fmt-row-strike" },
  ];

  function _colorByKey(k) {
    return PRESET_COLORS.find(c => c.key === k) || PRESET_COLORS[0];
  }

  // ── Compile rules → AG Grid format ─────────────────────────────────

  /**
   * Compile array of rules → {cellClassRulesByCol, rowClassRules}.
   *
   * cellClassRulesByCol: Map<column, {cssClass: predicate(params), ...}>
   *   — pro každý sloupec, set cellClassRules pro AG column def
   *
   * rowClassRules: {cssClass: predicate(params), ...}
   *   — společný pro celý grid (gridOptions.rowClassRules)
   *
   * Priority: pokud více rules pro stejný sloupec/scope, ranked podle order ASC.
   * AG Grid vykreslí všechny matching classes — ale pokud chceme single-match
   * pattern, můžeme dynamic class name (per-rule unique) → CSS váha řeší.
   */
  function compile(rules, columnDefs) {
    const cellRulesByCol = {};
    const rowRules = {};
    if (!Array.isArray(rules) || rules.length === 0) {
      return { cellClassRulesByCol: cellRulesByCol, rowClassRules: rowRules };
    }
    // Sort by order ASC — first wins (stable per scope+column)
    const sorted = rules.slice().sort((a, b) =>
      (a.order || 0) - (b.order || 0)
    );

    for (const r of sorted) {
      const opDef = OPERATORS[r.operator];
      if (!opDef) continue;
      const colorDef = _colorByKey(r.color);
      const isRow = (r.scope === "row" || r.column === "*");
      // Build predicate closure. Capture rule via closure.
      const target = r.value;
      const pred = (params) => {
        try {
          const data = isRow ? params.data : null;
          const value = isRow
            ? (r.column === "*"
                ? null  // no specific column for row — predicate evaluates against any?
                : (data ? data[r.column] : null))
            : params.value;
          // For row "*" rule, evaluate against the column field if specified.
          // If column="*" with row scope, rule effectively means "evaluate against any value" — limited use.
          // Most useful row rules target specific column (e.g. "Smazana" eq "true")
          if (isRow && r.column !== "*") {
            return opDef.predicate(data ? data[r.column] : null, target);
          }
          if (isRow && r.column === "*") {
            // Whole-row catch-all — evaluate against null (only "empty"/"notempty" make sense)
            return opDef.predicate(null, target);
          }
          return opDef.predicate(value, target);
        } catch (e) {
          return false;
        }
      };

      // Unique class name per rule (so multiple rules can stack visually
      // — last write wins for color, but order ranks priority).
      const uniqueClass = colorDef[isRow ? "rowClass" : "cellClass"]
        + " erp-fmt-rule-" + (r.id || r.order || "x");

      if (isRow) {
        // Map class string → predicate
        rowRules[uniqueClass] = pred;
      } else {
        const col = r.column;
        if (!cellRulesByCol[col]) cellRulesByCol[col] = {};
        cellRulesByCol[col][uniqueClass] = pred;
      }
    }
    return { cellClassRulesByCol: cellRulesByCol, rowClassRules: rowRules };
  }

  // ── UI Editor (modal) ──────────────────────────────────────────────

  /**
   * Open formatting rules editor modal.
   *
   * @param {Object} opts
   * @param {Array} opts.rules — current rules (will not be mutated; result returns new array)
   * @param {Array} opts.columns — column metadata: [{field, headerName, type}]
   * @param {Function} opts.onSave — async (newRules) => void
   * @returns Promise<Array|null> — new rules or null if canceled
   */
  function openEditor(opts) {
    return new Promise((resolve) => {
      const initialRules = (opts.rules || []).map(r => Object.assign({}, r));
      const columns = opts.columns || [];
      const onSave = opts.onSave;

      // Dialog state
      const state = {
        rules: initialRules,  // mutable working copy
        editingId: null,      // id rule právě editovaného (form), null = nic
        nextId: _nextId(initialRules),
      };

      const backdrop = document.createElement("div");
      backdrop.className = "erp-fmt-modal-backdrop";
      backdrop.innerHTML =
        '<div class="erp-fmt-modal" role="dialog" aria-modal="true">' +
          '<div class="erp-fmt-modal-header">' +
            '<h3>Barevná pravidla</h3>' +
            '<button class="erp-fmt-modal-close" type="button" title="Zavřít">×</button>' +
          '</div>' +
          '<div class="erp-fmt-modal-body" data-fmt-body></div>' +
          '<div class="erp-fmt-modal-footer">' +
            '<button class="erp-fmt-modal-btn" data-fmt-cancel>Zrušit</button>' +
            '<button class="erp-fmt-modal-btn primary" data-fmt-save>Uložit</button>' +
          '</div>' +
        '</div>';
      document.body.appendChild(backdrop);
      // Krok 5.U Fáze H+++ (23.5.2026): stack-aware z-index — Marti's catch
      // "obarvovaci podminky se taky oteviraji za pickup komponentou".
      // .erp-fmt-modal-backdrop má CSS z-index 9500 (datagrid.css line 841),
      // ErpCatalogPicker overlay 10010 — modal byl POD pickerem (invisible).
      // Stejný pattern jako _showModal v datagrid.js: scan body > * fixed,
      // posuň o +10 nad max, hard floor 10020.
      try {
        const _bodyChildren = document.querySelectorAll("body > *");
        let _maxZ = 9500;  // CSS fallback baseline
        _bodyChildren.forEach((el) => {
          if (el === backdrop) return;  // skip self
          const _s = window.getComputedStyle(el);
          if (_s.position !== "fixed") return;
          const z = parseInt(_s.zIndex, 10);
          if (!isNaN(z) && z > _maxZ) _maxZ = z;
        });
        backdrop.style.zIndex = String(Math.max(_maxZ + 10, 10020));
      } catch (e) {
        backdrop.style.zIndex = "10020";
      }

      const body = backdrop.querySelector("[data-fmt-body]");

      function close(result) {
        if (backdrop.parentNode) backdrop.parentNode.removeChild(backdrop);
        document.removeEventListener("keydown", escListener);
        resolve(result);
      }
      const escListener = (ev) => {
        if (ev.key === "Escape") {
          ev.preventDefault();
          close(null);
        }
      };
      document.addEventListener("keydown", escListener);

      backdrop.querySelector(".erp-fmt-modal-close").addEventListener("click", () => close(null));
      backdrop.querySelector("[data-fmt-cancel]").addEventListener("click", () => close(null));
      backdrop.addEventListener("click", (ev) => {
        if (ev.target === backdrop) close(null);
      });
      backdrop.querySelector("[data-fmt-save]").addEventListener("click", async () => {
        // Renumber order based on visual order (rules array is already in display order)
        const finalRules = state.rules.map((r, i) => Object.assign({}, r, { order: i }));
        if (typeof onSave === "function") {
          try {
            await onSave(finalRules);
          } catch (e) {
            console.warn("formatting save failed:", e);
            alert("Chyba při ukládání: " + (e.message || e));
            return;
          }
        }
        close(finalRules);
      });

      renderBody();

      // ── Render functions ────────────────────────────────────────────

      function renderBody() {
        body.innerHTML = "";
        body.appendChild(renderRulesList());
        body.appendChild(renderAddButton());
      }

      function renderRulesList() {
        const wrap = document.createElement("div");
        wrap.className = "erp-fmt-rules-list";
        if (state.rules.length === 0) {
          const empty = document.createElement("div");
          empty.className = "erp-fmt-empty";
          empty.innerHTML =
            '<div class="erp-fmt-empty-icon">🎨</div>' +
            '<div>Zatím žádná pravidla.</div>' +
            '<div class="erp-fmt-empty-hint">Klikni na <b>+ Nové pravidlo</b> pro přidání.</div>';
          wrap.appendChild(empty);
          return wrap;
        }
        // Header row
        const header = document.createElement("div");
        header.className = "erp-fmt-rules-header";
        header.innerHTML =
          '<span class="erp-fmt-col-grip"></span>' +
          '<span class="erp-fmt-col-order">#</span>' +
          '<span class="erp-fmt-col-target">Sloupec</span>' +
          '<span class="erp-fmt-col-op">Podmínka</span>' +
          '<span class="erp-fmt-col-value">Hodnota</span>' +
          '<span class="erp-fmt-col-color">Barva</span>' +
          '<span class="erp-fmt-col-scope">Rozsah</span>' +
          '<span class="erp-fmt-col-actions"></span>';
        wrap.appendChild(header);
        // Rules
        state.rules.forEach((rule, idx) => {
          if (state.editingId === rule.id) {
            wrap.appendChild(renderEditForm(rule, idx));
          } else {
            wrap.appendChild(renderRuleRow(rule, idx));
          }
        });
        return wrap;
      }

      function renderRuleRow(rule, idx) {
        const row = document.createElement("div");
        row.className = "erp-fmt-rule-row";
        row.setAttribute("draggable", "true");
        row.dataset.ruleId = rule.id;

        const op = OPERATORS[rule.operator] || { label: rule.operator };
        const col = _colorByKey(rule.color);
        const target = (rule.column === "*")
          ? "(řádek)"
          : (_columnLabel(rule.column, columns) || rule.column);

        row.innerHTML =
          '<span class="erp-fmt-col-grip" title="Přetáhni pro změnu pořadí">⋮⋮</span>' +
          '<span class="erp-fmt-col-order">' + (idx + 1) + '</span>' +
          '<span class="erp-fmt-col-target">' + _esc(target) + '</span>' +
          '<span class="erp-fmt-col-op">' + _esc(op.label) + '</span>' +
          '<span class="erp-fmt-col-value">' +
            (op.valueRequired ? _esc(rule.value || "") : '<span class="erp-fmt-na">—</span>') +
          '</span>' +
          '<span class="erp-fmt-col-color">' +
            '<span class="erp-fmt-swatch" style="background:' + col.swatch + '"></span> ' +
            _esc(col.label) +
          '</span>' +
          '<span class="erp-fmt-col-scope">' +
            (rule.scope === "row" ? "Řádek" : "Buňka") +
          '</span>' +
          '<span class="erp-fmt-col-actions">' +
            '<button type="button" class="erp-fmt-icon-btn" data-fmt-edit title="Upravit">✎</button>' +
            '<button type="button" class="erp-fmt-icon-btn" data-fmt-delete title="Smazat">🗑</button>' +
          '</span>';

        row.querySelector("[data-fmt-edit]").addEventListener("click", (ev) => {
          ev.stopPropagation();
          state.editingId = rule.id;
          renderBody();
        });
        row.querySelector("[data-fmt-delete]").addEventListener("click", (ev) => {
          ev.stopPropagation();
          state.rules = state.rules.filter(r => r.id !== rule.id);
          renderBody();
        });

        // Drag-drop reorder (HTML5 native)
        row.addEventListener("dragstart", (ev) => {
          row.classList.add("erp-fmt-drag-source");
          ev.dataTransfer.effectAllowed = "move";
          ev.dataTransfer.setData("text/plain", rule.id);
        });
        row.addEventListener("dragend", () => {
          row.classList.remove("erp-fmt-drag-source");
          document.querySelectorAll(".erp-fmt-drag-over").forEach(e =>
            e.classList.remove("erp-fmt-drag-over")
          );
        });
        row.addEventListener("dragover", (ev) => {
          ev.preventDefault();
          ev.dataTransfer.dropEffect = "move";
          row.classList.add("erp-fmt-drag-over");
        });
        row.addEventListener("dragleave", () => {
          row.classList.remove("erp-fmt-drag-over");
        });
        row.addEventListener("drop", (ev) => {
          ev.preventDefault();
          row.classList.remove("erp-fmt-drag-over");
          const draggedId = ev.dataTransfer.getData("text/plain");
          if (!draggedId || draggedId === rule.id) return;
          const fromIdx = state.rules.findIndex(r => String(r.id) === String(draggedId));
          const toIdx = state.rules.findIndex(r => String(r.id) === String(rule.id));
          if (fromIdx < 0 || toIdx < 0) return;
          const [moved] = state.rules.splice(fromIdx, 1);
          state.rules.splice(toIdx, 0, moved);
          renderBody();
        });

        return row;
      }

      function renderEditForm(rule, idx) {
        const form = document.createElement("div");
        form.className = "erp-fmt-rule-row erp-fmt-rule-edit";

        // Column picker — "*" (row scope) + all columns
        const colOptions =
          '<option value="*">' + ((rule.scope === "row") ? "(celý řádek)" : "(libovolná hodnota)") + '</option>' +
          columns.map(c =>
            '<option value="' + _esc(c.field) + '"' +
            (c.field === rule.column ? " selected" : "") + '>' +
            _esc(c.headerName || c.field) +
            '</option>'
          ).join("");

        const opOptions = Object.keys(OPERATORS).map(k => {
          const o = OPERATORS[k];
          return '<option value="' + k + '"' +
            (k === rule.operator ? " selected" : "") + '>' +
            _esc(o.label) + '</option>';
        }).join("");

        const colorPills = PRESET_COLORS.map(c =>
          '<button type="button" class="erp-fmt-color-pill' +
          (c.key === rule.color ? " selected" : "") + '" ' +
          'data-color="' + c.key + '" ' +
          'title="' + _esc(c.label) + '" ' +
          'style="background:' + c.swatch + '"></button>'
        ).join("");

        form.innerHTML =
          '<div class="erp-fmt-edit-grid">' +
            '<label class="erp-fmt-edit-label">Sloupec' +
              '<select data-fmt-col>' + colOptions + '</select>' +
            '</label>' +
            '<label class="erp-fmt-edit-label">Operátor' +
              '<select data-fmt-op>' + opOptions + '</select>' +
            '</label>' +
            '<label class="erp-fmt-edit-label" data-fmt-value-wrap>Hodnota' +
              '<input type="text" data-fmt-val value="' + _esc(rule.value || "") + '">' +
            '</label>' +
            '<label class="erp-fmt-edit-label">Rozsah' +
              '<select data-fmt-scope>' +
                '<option value="cell"' + (rule.scope === "cell" ? " selected" : "") + '>Buňka</option>' +
                '<option value="row"' + (rule.scope === "row" ? " selected" : "") + '>Celý řádek</option>' +
              '</select>' +
            '</label>' +
            '<div class="erp-fmt-edit-color">' +
              '<span class="erp-fmt-edit-label-text">Barva</span>' +
              '<div class="erp-fmt-color-pills">' + colorPills + '</div>' +
            '</div>' +
          '</div>' +
          '<div class="erp-fmt-edit-actions">' +
            '<button type="button" class="erp-fmt-modal-btn" data-fmt-edit-cancel>Zrušit</button>' +
            '<button type="button" class="erp-fmt-modal-btn primary" data-fmt-edit-apply>Použít</button>' +
          '</div>';

        // Live updates of rule preview state in form (no apply yet)
        const opSelect = form.querySelector("[data-fmt-op]");
        const valWrap = form.querySelector("[data-fmt-value-wrap]");
        const updateValueVisibility = () => {
          const op = OPERATORS[opSelect.value];
          if (op && !op.valueRequired) {
            valWrap.style.display = "none";
          } else {
            valWrap.style.display = "";
          }
        };
        opSelect.addEventListener("change", updateValueVisibility);
        updateValueVisibility();

        // Color pill selection
        form.querySelectorAll(".erp-fmt-color-pill").forEach(btn => {
          btn.addEventListener("click", () => {
            form.querySelectorAll(".erp-fmt-color-pill").forEach(b => b.classList.remove("selected"));
            btn.classList.add("selected");
          });
        });

        // Cancel — abort edit (if was new rule, remove it)
        form.querySelector("[data-fmt-edit-cancel]").addEventListener("click", () => {
          // Pokud rule.id byl jen-now-vytvořen (žádný save zatím), zruš ho
          if (rule._isNew) {
            state.rules = state.rules.filter(r => r.id !== rule.id);
          }
          state.editingId = null;
          renderBody();
        });

        // Apply — write back changes
        form.querySelector("[data-fmt-edit-apply]").addEventListener("click", () => {
          const updated = {
            id: rule.id,
            column: form.querySelector("[data-fmt-col]").value,
            operator: form.querySelector("[data-fmt-op]").value,
            value: form.querySelector("[data-fmt-val]").value,
            color: form.querySelector(".erp-fmt-color-pill.selected")
                   ? form.querySelector(".erp-fmt-color-pill.selected").dataset.color
                   : rule.color,
            scope: form.querySelector("[data-fmt-scope]").value,
            order: rule.order || idx,
          };
          // Validation
          const opDef = OPERATORS[updated.operator];
          if (opDef && opDef.valueRequired && !updated.value) {
            alert("Tento operátor vyžaduje hodnotu.");
            return;
          }
          // Replace rule in state
          state.rules = state.rules.map(r =>
            r.id === rule.id ? updated : r
          );
          state.editingId = null;
          renderBody();
        });

        return form;
      }

      function renderAddButton() {
        const wrap = document.createElement("div");
        wrap.className = "erp-fmt-add-wrap";
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "erp-fmt-add-btn";
        btn.textContent = "+ Nové pravidlo";
        btn.addEventListener("click", () => {
          const newRule = {
            id: state.nextId++,
            column: columns.length > 0 ? columns[0].field : "*",
            operator: "eq",
            value: "",
            color: "yellow",
            scope: "cell",
            order: state.rules.length,
            _isNew: true,
          };
          state.rules.push(newRule);
          state.editingId = newRule.id;
          renderBody();
        });
        wrap.appendChild(btn);
        return wrap;
      }
    });
  }

  // ── Helpers ────────────────────────────────────────────────────────

  function _esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, c =>
      ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])
    );
  }

  function _columnLabel(field, columns) {
    if (!columns) return null;
    const c = columns.find(x => x.field === field);
    return c ? (c.headerName || c.field) : null;
  }

  function _nextId(rules) {
    let max = 0;
    for (const r of (rules || [])) {
      const n = parseInt(r.id, 10);
      if (!isNaN(n) && n > max) max = n;
    }
    return max + 1;
  }

  // ── Export ────────────────────────────────────────────────────────

  global.ErpGridFormatting = {
    OPERATORS,
    PRESET_COLORS,
    compile,
    openEditor,
  };

  }); // _erpLoadModule end
})(typeof window !== "undefined" ? window : globalThis);
