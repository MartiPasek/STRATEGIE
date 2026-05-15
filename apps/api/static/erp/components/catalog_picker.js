/**
 * ErpCatalogPicker — modal picker s AG Grid pro výběr FK reference.
 *
 * Phase 38.4 Krok 14g-H+22 (15.5.2026 ~17:30, Marti's "C plně nahradí B,
 * dnes začneme, zítra dotáhneme do finále"). Centrála 1 parita — nejvíc
 * používaná komponenta po edit.
 *
 * Day 1 (dnes):
 *   - Modal shell (overlay + dialog + header + toolbar + body + footer)
 *   - ErpDataGrid wrapped v body (existing class, B+4.3 era)
 *   - Toolbar buttons (➕/📝/🗑️/🔄/⚙) jako placeholders pro Day 2
 *   - Double-click row → onSelect(row) → close
 *   - OK button → onSelect(selectedRow) → close (or alert if no selection)
 *   - Storno button → onCancel() → close
 *
 * Day 2 (zítra):
 *   - ➕ Nový → inline CREATE form (DesignFwForm reuse?)
 *   - 📝 Editovat → otevři row editor
 *   - 🗑️ Smazat → confirm + DELETE endpoint (soft delete)
 *   - ⚙ Settings → column customization, save layout preset
 *   - Plus keyboard navigation (Enter/Esc/arrows)
 *
 * API (constructor opts):
 *   {
 *     title: "Vybrat core přehled",       // dialog header
 *     endpoint: "/api/v1/erp/design/fw-core/list",  // GET URL, returns {ok, <listKey>: [...]}
 *     listKey: "cores",                    // key in response (default 'rows')
 *     columns: [                           // AG Grid column defs
 *       { headerName: "Code", field: "code", flex: 1 },
 *       { headerName: "Label", field: "label", flex: 2 },
 *       ...
 *     ],
 *     idField: "id",                       // PK field (default 'id')
 *     labelField: "label",                 // display field for selection toast/preview
 *     width: "900px",                      // dialog width (default '900px')
 *     onSelect: (row) => { ... },          // klik OK nebo dvojklik row
 *     onCancel: () => { ... },             // klik Storno nebo Esc
 *     enableNew: false,                    // Day 2: ➕ button visible
 *     enableEdit: false,                   // Day 2: 📝 button visible
 *     enableDelete: false,                 // Day 2: 🗑️ button visible
 *     onNew: () => { ... },                // Day 2 callback
 *     onEdit: (row) => { ... },            // Day 2 callback
 *     onDelete: (row) => { ... },          // Day 2 callback
 *   }
 *
 * Usage:
 *   new window.ErpCatalogPicker({
 *     title: "Vybrat existing core",
 *     endpoint: "/api/v1/erp/design/fw-core/list",
 *     listKey: "cores",
 *     columns: [
 *       { headerName: "Code", field: "code", width: 200 },
 *       { headerName: "Label", field: "label", flex: 1 },
 *       { headerName: "Layout", field: "layout_type", width: 120 },
 *       { headerName: "Použit ×", field: "is_used_count", width: 100, type: "numericColumn" },
 *     ],
 *     onSelect: (row) => { console.log("vybráno:", row); },
 *   }).open();
 */
(function (global) {
  "use strict";

  function _esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  class ErpCatalogPicker {
    constructor(opts) {
      this.opts = Object.assign({
        title: "Vybrat záznam",
        endpoint: null,
        listKey: "rows",
        columns: [],
        idField: "id",
        labelField: "label",
        width: "900px",
        onSelect: null,
        onCancel: null,
        enableNew: false,
        enableEdit: false,
        enableDelete: false,
        onNew: null,
        onEdit: null,
        onDelete: null,
      }, opts || {});

      this._overlay = null;
      this._dialog = null;
      this._grid = null;        // ErpDataGrid instance
      this._gridContainer = null;
      this._selectedRow = null;
      this._isOpen = false;
    }

    /**
     * Open modal + fetch data + render grid.
     */
    async open() {
      if (this._isOpen) return;
      if (!this.opts.endpoint) {
        alert("ErpCatalogPicker: chybi opts.endpoint");
        return;
      }
      if (typeof window.ErpDataGrid !== "function") {
        alert("ErpCatalogPicker: window.ErpDataGrid not loaded (datagrid.js missing)");
        return;
      }

      // Overlay + dialog
      this._overlay = document.createElement("div");
      this._overlay.style.cssText =
        "position:fixed;inset:0;background:rgba(0,0,0,0.6);z-index:10010;" +
        "display:flex;align-items:center;justify-content:center;";

      this._dialog = document.createElement("div");
      this._dialog.style.cssText =
        "width:" + this.opts.width + ";max-width:95vw;height:80vh;max-height:680px;" +
        "background:#1a1f26;border:1px solid #2a3340;border-radius:6px;" +
        "display:flex;flex-direction:column;color:#cfd6df;font-size:13px;" +
        "box-shadow:0 8px 32px rgba(0,0,0,0.5);";

      this._buildHeader();
      this._buildToolbar();
      this._buildBody();
      this._buildFooter();

      this._overlay.appendChild(this._dialog);
      document.body.appendChild(this._overlay);
      this._isOpen = true;

      // Esc handler
      this._escHandler = (ev) => {
        if (ev.key === "Escape") this._handleCancel();
      };
      document.addEventListener("keydown", this._escHandler);

      // Fetch data + render grid
      await this._fetchAndRender();
    }

    close() {
      if (!this._isOpen) return;
      try {
        if (this._grid && typeof this._grid.destroy === "function") {
          this._grid.destroy();
        }
      } catch (e) {
        console.warn("[ErpCatalogPicker] grid destroy failed:", e);
      }
      this._grid = null;
      if (this._overlay && this._overlay.parentElement) {
        this._overlay.parentElement.removeChild(this._overlay);
      }
      this._overlay = null;
      this._dialog = null;
      this._isOpen = false;
      try { document.removeEventListener("keydown", this._escHandler); } catch (e) {}
    }

    /**
     * Refresh data — re-fetch endpoint + re-render grid.
     */
    async refresh() {
      if (!this._gridContainer) return;
      try {
        const data = await this._fetchData();
        if (this._grid && typeof this._grid.setRowData === "function") {
          this._grid.setRowData(data);
        } else {
          // Re-create grid
          this._gridContainer.innerHTML = "";
          this._grid = new window.ErpDataGrid(this._gridContainer, {
            rowData: data,
            columnDefs: this.opts.columns,
            autoColumns: false,
            onRowDoubleClick: (row) => this._handleSelect(row),
            onSelectionChange: (rows) => {
              this._selectedRow = (rows && rows.length === 1) ? rows[0] : null;
              this._syncOkButtonState();
            },
          });
        }
      } catch (e) {
        console.error("[ErpCatalogPicker] refresh failed:", e);
        alert("Refresh selhal: " + (e.message || e));
      }
    }

    // ════════════════════════════════════════════════════════════════
    // Internal — build sections
    // ════════════════════════════════════════════════════════════════

    _buildHeader() {
      const header = document.createElement("div");
      header.style.cssText =
        "padding:12px 18px;border-bottom:1px solid #2a3340;display:flex;" +
        "align-items:center;justify-content:space-between;flex-shrink:0;";
      const title = document.createElement("div");
      title.style.cssText = "font-size:14px;font-weight:600;color:#e8eef5;";
      title.textContent = this.opts.title;
      header.appendChild(title);
      const closeBtn = document.createElement("button");
      closeBtn.type = "button";
      closeBtn.textContent = "✕";
      closeBtn.style.cssText =
        "background:none;border:none;color:#7a8696;font-size:18px;cursor:pointer;" +
        "padding:0 4px;";
      closeBtn.onclick = () => this._handleCancel();
      header.appendChild(closeBtn);
      this._dialog.appendChild(header);
    }

    _buildToolbar() {
      const toolbar = document.createElement("div");
      toolbar.style.cssText =
        "padding:8px 12px;border-bottom:1px solid #2a3340;display:flex;" +
        "gap:6px;align-items:center;flex-shrink:0;";

      // Day 2 placeholder buttons — visible jen pokud enable* flag true
      const _makeBtn = (label, title, onClickFn, accentColor) => {
        const b = document.createElement("button");
        b.type = "button";
        b.style.cssText =
          "padding:5px 10px;background:#1f262f;border:1px solid #3a4754;" +
          "color:" + (accentColor || "#cfd6df") + ";border-radius:3px;" +
          "cursor:pointer;font-size:11px;font-weight:500;";
        b.textContent = label;
        b.title = title;
        b.onmouseover = () => { b.style.background = "#252d37"; };
        b.onmouseout = () => { b.style.background = "#1f262f"; };
        b.onclick = onClickFn;
        return b;
      };

      if (this.opts.enableNew) {
        const newBtn = _makeBtn("➕ Nový", "Vytvořit nový záznam (Day 2)", () => {
          if (typeof this.opts.onNew === "function") {
            try { this.opts.onNew(); }
            catch (e) { console.error("[ErpCatalogPicker] onNew failed:", e); }
          } else {
            alert("Wizard pro vytvoření nového záznamu přijde v Day 2.");
          }
        }, "#d4b88a");
        toolbar.appendChild(newBtn);
      }

      if (this.opts.enableEdit) {
        const editBtn = _makeBtn("📝 Editovat", "Editovat vybraný řádek (Day 2)", () => {
          if (!this._selectedRow) {
            alert("Vyber řádek (single click).");
            return;
          }
          if (typeof this.opts.onEdit === "function") {
            try { this.opts.onEdit(this._selectedRow); }
            catch (e) { console.error("[ErpCatalogPicker] onEdit failed:", e); }
          } else {
            alert("Editace přijde v Day 2.");
          }
        });
        toolbar.appendChild(editBtn);
      }

      if (this.opts.enableDelete) {
        const delBtn = _makeBtn("🗑️ Smazat", "Smazat vybraný řádek (Day 2)", () => {
          if (!this._selectedRow) {
            alert("Vyber řádek (single click).");
            return;
          }
          if (typeof this.opts.onDelete === "function") {
            try { this.opts.onDelete(this._selectedRow); }
            catch (e) { console.error("[ErpCatalogPicker] onDelete failed:", e); }
          } else {
            alert("Mazání přijde v Day 2.");
          }
        }, "#d4a8a8");
        toolbar.appendChild(delBtn);
      }

      // Refresh — vždy enabled
      const refreshBtn = _makeBtn("🔄 Refresh", "Načíst znovu data", () => this.refresh());
      toolbar.appendChild(refreshBtn);

      // Spacer
      const spacer = document.createElement("div");
      spacer.style.cssText = "flex:1;";
      toolbar.appendChild(spacer);

      // Selection info (right side)
      this._selectionInfo = document.createElement("div");
      this._selectionInfo.style.cssText = "color:#7a8696;font-size:11px;font-style:italic;";
      this._selectionInfo.textContent = "(žádný výběr)";
      toolbar.appendChild(this._selectionInfo);

      this._dialog.appendChild(toolbar);
    }

    _buildBody() {
      this._gridContainer = document.createElement("div");
      this._gridContainer.className = "ag-theme-quartz-dark";
      this._gridContainer.style.cssText = "flex:1;min-height:0;overflow:hidden;";
      this._dialog.appendChild(this._gridContainer);
    }

    _buildFooter() {
      const footer = document.createElement("div");
      footer.style.cssText =
        "padding:12px 18px;border-top:1px solid #2a3340;display:flex;" +
        "gap:10px;justify-content:flex-end;align-items:center;flex-shrink:0;";

      const cancelBtn = document.createElement("button");
      cancelBtn.type = "button";
      cancelBtn.textContent = "Storno";
      cancelBtn.style.cssText =
        "padding:8px 18px;background:#2a3340;border:1px solid #3a4754;" +
        "color:#cfd6df;border-radius:4px;cursor:pointer;font-size:12px;";
      cancelBtn.onclick = () => this._handleCancel();
      footer.appendChild(cancelBtn);

      this._okBtn = document.createElement("button");
      this._okBtn.type = "button";
      this._okBtn.textContent = "OK";
      this._okBtn.disabled = true;
      this._okBtn.style.cssText =
        "padding:8px 18px;background:#2a4760;border:1px solid #4a7ba8;" +
        "color:#a8c4dc;border-radius:4px;cursor:pointer;font-size:12px;" +
        "font-weight:500;opacity:0.5;";
      this._okBtn.onclick = () => {
        if (this._selectedRow) this._handleSelect(this._selectedRow);
      };
      footer.appendChild(this._okBtn);

      this._dialog.appendChild(footer);
    }

    _syncOkButtonState() {
      if (!this._okBtn) return;
      const hasSelection = !!this._selectedRow;
      this._okBtn.disabled = !hasSelection;
      this._okBtn.style.opacity = hasSelection ? "1" : "0.5";
      if (this._selectionInfo) {
        if (hasSelection) {
          const label = this._selectedRow[this.opts.labelField] || this._selectedRow[this.opts.idField];
          this._selectionInfo.textContent = "Vybráno: " + label;
          this._selectionInfo.style.color = "#a8c4dc";
          this._selectionInfo.style.fontStyle = "normal";
        } else {
          this._selectionInfo.textContent = "(žádný výběr)";
          this._selectionInfo.style.color = "#7a8696";
          this._selectionInfo.style.fontStyle = "italic";
        }
      }
    }

    // ════════════════════════════════════════════════════════════════
    // Data fetching + grid render
    // ════════════════════════════════════════════════════════════════

    async _fetchData() {
      const r = await fetch(this.opts.endpoint, { credentials: "include" });
      if (!r.ok) throw new Error("HTTP " + r.status);
      const data = await r.json();
      if (!data.ok) throw new Error(data.error || "Backend response not ok");
      return data[this.opts.listKey] || [];
    }

    async _fetchAndRender() {
      try {
        const rows = await this._fetchData();
        this._grid = new window.ErpDataGrid(this._gridContainer, {
          rowData: rows,
          columnDefs: this.opts.columns,
          autoColumns: false,
          // AG Grid native selection
          rowSelection: "single",
          onRowDoubleClick: (row) => this._handleSelect(row),
          onSelectionChange: (selectedRows) => {
            this._selectedRow = (selectedRows && selectedRows.length === 1)
              ? selectedRows[0] : null;
            this._syncOkButtonState();
          },
        });

        // Phase 38.4 Krok 14g-H+31 step 5 (15.5.2026 vecer, Marti's
        // "je treba videt, ktera veta je vybrana"): post-render highlight
        // matching aktualne vybrana entita. Use setTimeout(0) — AG Grid
        // renders synchronously when rowData passed v opts, ale necham
        // event loop tick aby grid byl plne ready.
        const initId = this.opts.initialSelectedId;
        if (initId != null) {
          setTimeout(() => {
            try {
              const api = this._grid && this._grid.gridApi;
              if (!api || typeof api.forEachNode !== "function") return;
              api.forEachNode((node) => {
                if (node && node.data && node.data.id === initId) {
                  node.setSelected(true, true);  // selected, clearSelection
                  if (typeof api.ensureNodeVisible === "function") {
                    api.ensureNodeVisible(node, "middle");
                  }
                }
              });
            } catch (e) {
              console.warn("[ErpCatalogPicker] initial select failed:", e);
            }
          }, 0);
        }
      } catch (e) {
        console.error("[ErpCatalogPicker] fetch failed:", e);
        this._gridContainer.innerHTML =
          '<div style="padding:40px;color:#d4a8a8;text-align:center;">' +
          'Načítání selhalo: ' + _esc(e.message || String(e)) +
          '</div>';
      }
    }

    // ════════════════════════════════════════════════════════════════
    // Handlers
    // ════════════════════════════════════════════════════════════════

    _handleSelect(row) {
      if (typeof this.opts.onSelect === "function") {
        try {
          this.opts.onSelect(row);
        } catch (e) {
          console.error("[ErpCatalogPicker] onSelect failed:", e);
        }
      }
      this.close();
    }

    _handleCancel() {
      if (typeof this.opts.onCancel === "function") {
        try {
          this.opts.onCancel();
        } catch (e) {
          console.error("[ErpCatalogPicker] onCancel failed:", e);
        }
      }
      this.close();
    }
  }

  global.ErpCatalogPicker = ErpCatalogPicker;
})(typeof window !== "undefined" ? window : globalThis);
