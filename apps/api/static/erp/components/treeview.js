/**
 * ErpTreeView — UI Kit tree komponenta.
 *
 * Hierarchical tree s expand/collapse, click selection, search filter,
 * active state, persistence. Reusable napříč STRATEGIÍ:
 *   - ERP left panel (EUROSOFT EC_CentralaMenu + System tree)
 *   - System tier (Phase 38.4 master.menu_node)
 *   - Files modal navigation
 *   - Future: Pyramida paměti, dashboards, ...
 *
 * MVP Core (Phase B+6.11):
 *   - Recursive render (flat list with parent_id NEBO pre-grouped children)
 *   - Expand/collapse (per-node toggle, expandAll/collapseAll, persistence)
 *   - Click selection + active state highlight + scroll into view
 *   - Search filter (Czech diacritics normalization, descendants visible
 *     při folder match, label <mark> highlight, debounce 80ms)
 *   - Context menu callback (right-click)
 *   - localStorage persistence (expanded, active)
 *
 * Optional (post-render hooks, Phase B+6.11+1, +2, ...):
 *   - Pinning + star toggle
 *   - View modes (Vše/Oblíbené/MRU)
 *   - Multi-select (Ctrl+klik)
 *   - Drag-drop reorder
 *   - System tier hooks (negative cislo, system_view_mode)
 *
 * Usage:
 *
 *   const tree = new ErpTreeView(rootEl, {
 *     dataSource: async () => fetchTreeJson(),  // callback returns TreeNode[]
 *     onClick: (node, event) => { openTab(node.data.cislo_def); },
 *     onContextMenu: (node, event) => { showCustomMenu(node); },
 *     onExpand: (node, isExpanded) => { ... },
 *     onAfterRender: (rootEl) => { attachLegacyHandlers(rootEl); },
 *
 *     enableSearch: true,
 *     enablePersistence: true,
 *     storageKeyPrefix: "erp.tree",
 *     cssClassPrefix: "erp-tree",
 *     indentPx: 16,
 *     searchPlaceholder: "Hledat…",
 *     emptyMessage: "Žádné položky",
 *     loadingMessage: "Načítám...",
 *     filterDebounceMs: 80,
 *   });
 *
 *   await tree.init();
 *   tree.setActive(nodeId);
 *   tree.setFilter(text);
 *   tree.refresh();
 *   tree.destroy();
 *
 * TreeNode shape:
 *   {
 *     id: string|number,             // unique
 *     parent_id?: string|number,     // null = root
 *     label: string,                 // display
 *     icon?: string,                 // emoji nebo CSS class
 *     kind?: 'folder' | 'leaf',      // default 'leaf'
 *     children?: TreeNode[],          // optional pre-grouped (jinak flat)
 *     data?: object,                  // app-specific (cislo_def, atd.) →
 *                                      pass-through na li.dataset
 *     badge?: { text, color },        // optional badge
 *     className?: string,             // extra CSS class na <li>
 *     sort_order?: number,            // optional sort within parent
 *   }
 *
 * Phase B+6.11 (10.5.2026 odpoledne).
 * Marti's catch — TreeView je also ERP komponenta, reusable napříč STRATEGIÍ.
 */
(function (global) {
  "use strict";

  function _esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, c =>
      ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])
    );
  }

  function _normalizeSearch(text) {
    if (!text) return "";
    try {
      return String(text).toLowerCase()
        .normalize("NFD")
        .replace(/[̀-ͯ]/g, "");
    } catch (e) {
      return String(text).toLowerCase();
    }
  }

  function _cssEscape(value) {
    if (typeof CSS !== "undefined" && CSS.escape) return CSS.escape(value);
    // Fallback minimal escape pro selectory
    return String(value).replace(/[^\w-]/g, "\\$&");
  }

  class ErpTreeView {
    constructor(container, options) {
      this.container = container;
      this.options = Object.assign({
        dataSource: null,
        onClick: null,
        onContextMenu: null,
        onExpand: null,
        onAfterRender: null,         // hook pro post-render attach (legacy ERP features)
        enableSearch: true,
        enablePersistence: true,
        storageKeyPrefix: "erp.tree",
        cssClassPrefix: "erp-tree",
        indentPx: 16,
        searchPlaceholder: "Hledat…",
        emptyMessage: "Žádné položky",
        loadingMessage: "Načítám...",
        filterDebounceMs: 80,
      }, options || {});

      this._destroyed = false;
      this._data = null;             // raw nodes from dataSource
      this._nodeIndex = new Map();   // String(id) → node
      this._expandedIds = new Set();
      this._activeId = null;
      this._filterText = "";
      this._filterDebounceTimer = null;

      this._buildSkeleton();
      this._restoreFromStorage();
    }

    // ── Lifecycle ──────────────────────────────────────────────────

    _buildSkeleton() {
      const cls = this.options.cssClassPrefix;
      this.container.classList.add(cls + "-pane");

      // Search input (optional)
      if (this.options.enableSearch) {
        this.searchEl = document.createElement("div");
        this.searchEl.className = cls + "-search";

        this.searchInput = document.createElement("input");
        this.searchInput.type = "search";
        this.searchInput.className = cls + "-search-input";
        this.searchInput.placeholder = this.options.searchPlaceholder;
        this.searchEl.appendChild(this.searchInput);

        this.searchClearBtn = document.createElement("button");
        this.searchClearBtn.type = "button";
        this.searchClearBtn.className = cls + "-search-clear";
        this.searchClearBtn.setAttribute("aria-label", "Vymazat");
        this.searchClearBtn.textContent = "×";
        this.searchClearBtn.style.display = "none";
        this.searchEl.appendChild(this.searchClearBtn);

        this.container.appendChild(this.searchEl);
      }

      // Root list container
      this.rootEl = document.createElement("div");
      this.rootEl.className = cls + "-root";
      this.rootEl.innerHTML =
        '<div class="' + cls + '-loading">' +
        _esc(this.options.loadingMessage) +
        '</div>';
      this.container.appendChild(this.rootEl);
    }

    async init() {
      if (this._destroyed) return;
      try {
        const ds = this.options.dataSource;
        let data;
        if (typeof ds === "function") {
          data = await ds();
        } else if (Array.isArray(ds)) {
          data = ds;
        } else {
          throw new Error("dataSource must be callback function or array");
        }
        this._data = data || [];
        this._buildIndex();
        this._render();
        this._attachHandlers();
        this._tryRestoreActive();
      } catch (e) {
        console.error("[ErpTreeView] init failed:", e);
        this.rootEl.innerHTML =
          '<div class="' + this.options.cssClassPrefix + '-error">' +
          'Chyba: ' + _esc(String(e && e.message ? e.message : e)) +
          '</div>';
      }
    }

    async refresh() {
      if (this._destroyed) return;
      // Preserve state across re-fetch
      const oldExpanded = new Set(this._expandedIds);
      const oldActive = this._activeId;
      const oldFilter = this._filterText;
      try {
        const ds = this.options.dataSource;
        const data = (typeof ds === "function") ? await ds() : (Array.isArray(ds) ? ds : []);
        this._data = data || [];
        this._buildIndex();
        // Restore (re-apply preserved state — _render uses these)
        oldExpanded.forEach(id => this._expandedIds.add(id));
        this._activeId = oldActive;
        this._filterText = oldFilter;
        this._render();
        this._tryRestoreActive();
        if (this._filterText && this.searchInput) {
          this.searchInput.value = this._filterText;
          this._applyFilter(this._filterText);
        }
      } catch (e) {
        console.error("[ErpTreeView] refresh failed:", e);
      }
    }

    destroy() {
      this._destroyed = true;
      if (this._filterDebounceTimer) clearTimeout(this._filterDebounceTimer);
      if (this.container) {
        this.container.innerHTML = "";
        this.container.classList.remove(this.options.cssClassPrefix + "-pane");
      }
      this._nodeIndex.clear();
      this._expandedIds.clear();
      this._data = null;
      this._activeId = null;
    }

    // ── Public API ─────────────────────────────────────────────────

    setActive(id) {
      const cls = this.options.cssClassPrefix;
      const oldActive = this.rootEl.querySelector("." + cls + "-row.active");
      if (oldActive) oldActive.classList.remove("active");
      this._activeId = (id == null || id === "") ? null : String(id);
      if (this._activeId != null) {
        const item = this._findItemById(this._activeId);
        if (item) {
          const row = item.querySelector(":scope > ." + cls + "-row");
          if (row) row.classList.add("active");
          this._expandAncestors(item);
          if (row && typeof row.scrollIntoView === "function") {
            try { row.scrollIntoView({ block: "nearest" }); } catch (e) { /* noop */ }
          }
        }
      }
      this._saveToStorage();
    }

    getActive() { return this._activeId; }

    getNode(id) { return this._nodeIndex.get(String(id)) || null; }

    getRootElement() { return this.rootEl; }

    expand(id) {
      const sid = String(id);
      if (!this._expandedIds.has(sid)) this._toggleExpanded(sid);
    }

    collapse(id) {
      const sid = String(id);
      if (this._expandedIds.has(sid)) this._toggleExpanded(sid);
    }

    expandAll() {
      for (const n of this._nodeIndex.values()) {
        if (this._getChildren(n.id).length > 0) {
          this._expandedIds.add(String(n.id));
        }
      }
      this._saveToStorage();
      this._render();
      this._tryRestoreActive();
    }

    collapseAll() {
      this._expandedIds.clear();
      this._saveToStorage();
      this._render();
      this._tryRestoreActive();
    }

    setFilter(text) {
      this._filterText = text || "";
      if (this.searchInput && this.searchInput.value !== this._filterText) {
        this.searchInput.value = this._filterText;
      }
      this._applyFilter(this._filterText);
    }

    getFilter() { return this._filterText; }

    // ── Internal: index + lookup ──────────────────────────────────

    _buildIndex() {
      this._nodeIndex.clear();
      const walk = (nodes, parentId) => {
        for (const n of nodes || []) {
          if (n == null || n.id == null) continue;
          const norm = Object.assign({}, n);
          // Normalize: if pre-grouped (children), set parent_id explicitly
          if (parentId != null && norm.parent_id == null) {
            norm.parent_id = parentId;
          }
          this._nodeIndex.set(String(n.id), norm);
          if (Array.isArray(n.children) && n.children.length) {
            walk(n.children, n.id);
          }
        }
      };
      walk(this._data, null);
    }

    _getChildren(parentId) {
      const target = (parentId == null) ? null : String(parentId);
      const out = [];
      for (const n of this._nodeIndex.values()) {
        const npid = (n.parent_id == null) ? null : String(n.parent_id);
        if (npid === target) out.push(n);
      }
      // Stable sort: sort_order asc, then id asc
      out.sort((a, b) => {
        const ao = (a.sort_order != null) ? Number(a.sort_order) : 999999;
        const bo = (b.sort_order != null) ? Number(b.sort_order) : 999999;
        if (ao !== bo) return ao - bo;
        return String(a.id).localeCompare(String(b.id));
      });
      return out;
    }

    _findItemById(id) {
      const cls = this.options.cssClassPrefix;
      const sid = _cssEscape(String(id));
      return this.rootEl.querySelector('.' + cls + '-item[data-id="' + sid + '"]');
    }

    // ── Internal: render ──────────────────────────────────────────

    _render() {
      const cls = this.options.cssClassPrefix;
      const rootNodes = this._getChildren(null);
      if (rootNodes.length === 0) {
        this.rootEl.innerHTML =
          '<div class="' + cls + '-empty">' +
          _esc(this.options.emptyMessage) +
          '</div>';
        return;
      }
      const ul = document.createElement("ul");
      ul.className = cls + "-list";
      this._renderNodes(rootNodes, 0, ul);
      this.rootEl.innerHTML = "";
      this.rootEl.appendChild(ul);

      // Re-apply filter if active (re-render preserved filter text)
      if (this._filterText) this._applyFilter(this._filterText);

      // Hook pro post-render attach (legacy ERP features — pinning,
      // drag-drop, view modes — postupně migrované do core)
      if (typeof this.options.onAfterRender === "function") {
        try {
          this.options.onAfterRender(this.rootEl, this);
        } catch (e) {
          console.error("[ErpTreeView] onAfterRender failed:", e);
        }
      }
    }

    _renderNodes(nodes, depth, parentUlEl) {
      const cls = this.options.cssClassPrefix;
      for (const n of nodes) {
        const li = document.createElement("li");
        li.className = cls + "-item";
        const childrenNodes = this._getChildren(n.id);
        const hasChildren = childrenNodes.length > 0;
        const isFolder = (n.kind === "folder") || hasChildren;

        if (isFolder) {
          li.classList.add(cls + "-folder");
        } else {
          li.classList.add(cls + "-leaf");
        }
        if (n.className) {
          for (const c of String(n.className).split(/\s+/)) {
            if (c) li.classList.add(c);
          }
        }
        li.dataset.id = String(n.id);
        const labelText = String(n.label != null ? n.label : n.id);
        li.dataset.text = _normalizeSearch(labelText);

        // Pass-through data attributes (n.data → li.dataset)
        if (n.data && typeof n.data === "object") {
          for (const [k, v] of Object.entries(n.data)) {
            if (v == null) continue;
            // Convert camelCase or snake_case to kebab via dataset
            // (browser auto-converts data-foo-bar → dataset.fooBar)
            li.dataset[k] = String(v);
          }
        }

        // Row
        const row = document.createElement("div");
        row.className = cls + "-row";
        row.style.paddingLeft = (depth * this.options.indentPx) + "px";

        const isExpanded = this._expandedIds.has(String(n.id));

        // Toggle / spacer
        const toggle = document.createElement("span");
        if (hasChildren) {
          toggle.className = cls + "-toggle";
          toggle.textContent = isExpanded ? "▼" : "▶";
          toggle.dataset.role = "toggle";
        } else {
          toggle.className = cls + "-spacer";
        }
        row.appendChild(toggle);

        // Icon (optional)
        if (n.icon) {
          const ico = document.createElement("span");
          ico.className = cls + "-icon";
          ico.textContent = String(n.icon);
          row.appendChild(ico);
        }

        // Label
        const label = document.createElement("span");
        label.className = cls + "-label";
        label.textContent = labelText;
        row.appendChild(label);

        // Badge (optional)
        if (n.badge && n.badge.text) {
          const badge = document.createElement("span");
          badge.className = cls + "-badge";
          if (n.badge.color) badge.style.color = n.badge.color;
          badge.textContent = String(n.badge.text);
          row.appendChild(badge);
        }

        if (this._activeId != null && String(this._activeId) === String(n.id)) {
          row.classList.add("active");
        }

        li.appendChild(row);

        // Children container
        if (hasChildren) {
          const childWrap = document.createElement("div");
          childWrap.className = cls + "-children";
          childWrap.style.display = isExpanded ? "block" : "none";
          const childUl = document.createElement("ul");
          childUl.className = cls + "-list";
          this._renderNodes(childrenNodes, depth + 1, childUl);
          childWrap.appendChild(childUl);
          li.appendChild(childWrap);
        }

        parentUlEl.appendChild(li);
      }
    }

    // ── Internal: handlers ────────────────────────────────────────

    _attachHandlers() {
      const cls = this.options.cssClassPrefix;

      // Single delegated click handler
      this.rootEl.addEventListener("click", (e) => {
        const row = e.target.closest("." + cls + "-row");
        if (!row) return;
        const item = row.parentElement;
        if (!item || !item.classList.contains(cls + "-item")) return;
        const id = item.dataset.id;
        if (id == null) return;

        // Toggle click? (skip selection)
        const isToggleClick = e.target.dataset && e.target.dataset.role === "toggle";
        if (isToggleClick) {
          this._toggleExpanded(id);
          e.stopPropagation();
          return;
        }

        const node = this._nodeIndex.get(String(id));
        if (!node) return;

        // Active row click
        this.setActive(id);
        if (typeof this.options.onClick === "function") {
          try {
            this.options.onClick(node, e);
          } catch (err) {
            console.error("[ErpTreeView] onClick failed:", err);
          }
        }
      });

      // Right-click context menu
      if (typeof this.options.onContextMenu === "function") {
        this.rootEl.addEventListener("contextmenu", (e) => {
          const row = e.target.closest("." + cls + "-row");
          if (!row) return;
          const item = row.parentElement;
          const id = item && item.dataset && item.dataset.id;
          if (id == null) return;
          const node = this._nodeIndex.get(String(id));
          if (!node) return;
          e.preventDefault();
          try {
            this.options.onContextMenu(node, e);
          } catch (err) {
            console.error("[ErpTreeView] onContextMenu failed:", err);
          }
        });
      }

      // Search input
      if (this.options.enableSearch && this.searchInput) {
        this.searchInput.addEventListener("input", () => {
          if (this._filterDebounceTimer) clearTimeout(this._filterDebounceTimer);
          this._filterDebounceTimer = setTimeout(() => {
            this.setFilter(this.searchInput.value);
          }, this.options.filterDebounceMs);
        });
        if (this.searchClearBtn) {
          this.searchClearBtn.addEventListener("click", () => {
            this.searchInput.value = "";
            this.setFilter("");
            this.searchInput.focus();
          });
        }
      }
    }

    // ── Internal: expand/collapse ─────────────────────────────────

    _toggleExpanded(id) {
      const cls = this.options.cssClassPrefix;
      const sid = String(id);
      const wasExpanded = this._expandedIds.has(sid);
      if (wasExpanded) this._expandedIds.delete(sid);
      else this._expandedIds.add(sid);

      const item = this._findItemById(sid);
      if (item) {
        const childWrap = item.querySelector(":scope > ." + cls + "-children");
        const toggle = item.querySelector(
          ":scope > ." + cls + "-row > ." + cls + "-toggle"
        );
        if (childWrap) {
          childWrap.style.display = wasExpanded ? "none" : "block";
        }
        if (toggle) {
          toggle.textContent = wasExpanded ? "▶" : "▼";
        }
      }
      this._saveToStorage();

      if (typeof this.options.onExpand === "function") {
        const node = this._nodeIndex.get(sid);
        if (node) {
          try {
            this.options.onExpand(node, !wasExpanded);
          } catch (e) {
            console.error("[ErpTreeView] onExpand failed:", e);
          }
        }
      }
    }

    _expandAncestors(item) {
      const cls = this.options.cssClassPrefix;
      let cur = item.parentElement;
      while (cur) {
        if (cur.classList && cur.classList.contains(cls + "-children")) {
          cur.style.display = "block";
          const parentItem = cur.parentElement;
          if (parentItem && parentItem.dataset && parentItem.dataset.id) {
            this._expandedIds.add(String(parentItem.dataset.id));
            const tg = parentItem.querySelector(
              ":scope > ." + cls + "-row > ." + cls + "-toggle"
            );
            if (tg) tg.textContent = "▼";
          }
          cur = parentItem ? parentItem.parentElement : null;
        } else {
          cur = cur.parentElement;
        }
      }
    }

    _tryRestoreActive() {
      if (this._activeId == null) return;
      const cls = this.options.cssClassPrefix;
      const item = this._findItemById(this._activeId);
      if (!item) return;
      const row = item.querySelector(":scope > ." + cls + "-row");
      if (row) row.classList.add("active");
      this._expandAncestors(item);
      if (row && typeof row.scrollIntoView === "function") {
        try { row.scrollIntoView({ block: "nearest" }); } catch (e) { /* noop */ }
      }
    }

    // ── Internal: filter ──────────────────────────────────────────

    _applyFilter(text) {
      const cls = this.options.cssClassPrefix;
      const norm = _normalizeSearch(text);
      const allItems = this.rootEl.querySelectorAll("." + cls + "-item");

      if (this.searchClearBtn) {
        this.searchClearBtn.style.display = norm ? "" : "none";
      }

      if (!norm) {
        // No filter — restore default visibility
        allItems.forEach(it => {
          it.style.display = "";
          it.classList.remove(
            cls + "-match",
            cls + "-match-parent",
            cls + "-match-descendant"
          );
          // Restore label text (no <mark>)
          const label = it.querySelector(
            ":scope > ." + cls + "-row > ." + cls + "-label"
          );
          if (label && label.dataset.original) {
            label.textContent = label.dataset.original;
            delete label.dataset.original;
          }
        });
        return;
      }

      // Pass 1: mark direct matches + highlight label
      const matchedIds = new Set();
      allItems.forEach(it => {
        // Reset previous classification
        it.classList.remove(
          cls + "-match",
          cls + "-match-parent",
          cls + "-match-descendant"
        );
        const label = it.querySelector(
          ":scope > ." + cls + "-row > ." + cls + "-label"
        );
        if (label && label.dataset.original) {
          label.textContent = label.dataset.original;
          delete label.dataset.original;
        }

        const txt = it.dataset.text || "";
        if (txt.indexOf(norm) !== -1) {
          matchedIds.add(it.dataset.id);
          it.classList.add(cls + "-match");
          // Highlight match in label
          if (label) {
            const original = label.textContent;
            const lower = _normalizeSearch(original);
            const idx = lower.indexOf(norm);
            if (idx !== -1) {
              label.dataset.original = original;
              label.innerHTML =
                _esc(original.substring(0, idx)) +
                '<mark>' +
                _esc(original.substring(idx, idx + norm.length)) +
                '</mark>' +
                _esc(original.substring(idx + norm.length));
            }
          }
        }
      });

      // Pass 2: mark ancestors of matches (parent path) + auto-expand
      matchedIds.forEach(matchedId => {
        const item = this._findItemById(matchedId);
        if (!item) return;
        let cur = item.parentElement;
        while (cur) {
          if (cur.classList && cur.classList.contains(cls + "-children")) {
            cur.style.display = "block"; // ensure visible
            const parentItem = cur.parentElement;
            if (parentItem && parentItem.dataset && parentItem.dataset.id) {
              parentItem.classList.add(cls + "-match-parent");
              const tg = parentItem.querySelector(
                ":scope > ." + cls + "-row > ." + cls + "-toggle"
              );
              if (tg) tg.textContent = "▼";
            }
            cur = parentItem ? parentItem.parentElement : null;
          } else {
            cur = cur.parentElement;
          }
        }
      });

      // Pass 3: descendants of folder matches (Phase B+7+++)
      matchedIds.forEach(matchedId => {
        const item = this._findItemById(matchedId);
        if (!item) return;
        if (!item.classList.contains(cls + "-folder")) return;
        const descendants = item.querySelectorAll("." + cls + "-item");
        descendants.forEach(d => {
          if (d !== item) d.classList.add(cls + "-match-descendant");
        });
      });

      // Pass 4: hide non-match/parent/descendant
      allItems.forEach(it => {
        const isMatch = it.classList.contains(cls + "-match");
        const isParent = it.classList.contains(cls + "-match-parent");
        const isDesc = it.classList.contains(cls + "-match-descendant");
        it.style.display = (isMatch || isParent || isDesc) ? "" : "none";
      });
    }

    // ── Internal: persistence ─────────────────────────────────────

    _restoreFromStorage() {
      if (!this.options.enablePersistence) return;
      const prefix = this.options.storageKeyPrefix;
      try {
        const expRaw = localStorage.getItem(prefix + ".expanded");
        if (expRaw) {
          const arr = JSON.parse(expRaw);
          if (Array.isArray(arr)) arr.forEach(id => this._expandedIds.add(String(id)));
        }
        const active = localStorage.getItem(prefix + ".active");
        if (active) this._activeId = active;
      } catch (e) {
        console.warn("[ErpTreeView] storage restore failed:", e);
      }
    }

    _saveToStorage() {
      if (!this.options.enablePersistence) return;
      const prefix = this.options.storageKeyPrefix;
      try {
        localStorage.setItem(
          prefix + ".expanded",
          JSON.stringify(Array.from(this._expandedIds))
        );
        if (this._activeId != null) {
          localStorage.setItem(prefix + ".active", String(this._activeId));
        } else {
          localStorage.removeItem(prefix + ".active");
        }
      } catch (e) {
        console.warn("[ErpTreeView] storage save failed:", e);
      }
    }
  }

  global.ErpTreeView = ErpTreeView;
})(typeof window !== "undefined" ? window : globalThis);
