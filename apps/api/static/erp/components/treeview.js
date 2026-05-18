/**
 * ErpTreeView — UI Kit hierarchical primitive.
 *
 * Universal tree komponenta. Reusable napříč STRATEGIÍ + base pro
 * specializované subclasses (ERP left panel, System DB-driven, Files,
 * Pyramida paměti) plus **popup menu** (přes ErpPopupMenu subclass).
 *
 * Phase B+6.11 (10.5.2026 odpoledne) — Marti's catch:
 * tree + popup menu = stejná hierarchická primitiva, jen jiné UX patterns.
 *
 * ─────────────────────────────────────────────────────────────────────
 * USAGE — basic tree
 * ─────────────────────────────────────────────────────────────────────
 *
 *   const tree = new ErpTreeView(rootEl, {
 *     dataSource: async () => fetchTreeData(),
 *     onClick: (node, e) => openNode(node),
 *     onContextMenu: (node, e) => showCustomMenu(node, e),
 *     enableSearch: true,
 *     enableKeyboard: true,
 *     enablePersistence: true,
 *     storageKeyPrefix: "erp.tree",
 *     cssClassPrefix: "erp-tree",
 *   });
 *   await tree.init();
 *
 * ─────────────────────────────────────────────────────────────────────
 * USAGE — toolbar + per-node actions
 * ─────────────────────────────────────────────────────────────────────
 *
 *   new ErpTreeView(el, {
 *     toolbar: [
 *       { label: "Refresh", icon: "🔄", handler: (tree) => tree.refresh() },
 *       { label: "Rozbalit vše", icon: "▼", handler: (tree) => tree.expandAll() },
 *       { label: "Sbalit vše", icon: "▶", handler: (tree) => tree.collapseAll() },
 *     ],
 *     nodeActions: [
 *       { label: "Otevřít", icon: "▶", handler: (node, e) => openNode(node) },
 *       { label: "Smazat", icon: "🗑️", handler: (node, e) => deleteNode(node),
 *         visible: (node) => node.data?.canDelete },
 *     ],
 *   });
 *
 * ─────────────────────────────────────────────────────────────────────
 * USAGE — slots (header / footer custom HTML)
 * ─────────────────────────────────────────────────────────────────────
 *
 *   new ErpTreeView(el, {
 *     headerSlot: customToolbarEl,   // rendered above search
 *     footerSlot: customFooterEl,    // rendered below tree
 *   });
 *
 * ─────────────────────────────────────────────────────────────────────
 * USAGE — icons
 * ─────────────────────────────────────────────────────────────────────
 *
 *   // Per-node explicit:
 *   { id: "users", label: "Uživatelé", icon: "👥" }
 *
 *   // Callback resolver (Files use case):
 *   new ErpTreeView(el, {
 *     iconResolver: (node, isExpanded) => {
 *       if (node.kind === "folder") return isExpanded ? "📂" : "📁";
 *       if (node.data?.fileType === "pdf") return "📄";
 *       return null;
 *     },
 *   });
 *
 *   // Default icons (built-in mapping):
 *   new ErpTreeView(el, {
 *     defaultIcons: { folderClosed: "📁", folderOpen: "📂", leaf: null },
 *   });
 *
 * ─────────────────────────────────────────────────────────────────────
 * KEYBOARD NAVIGATION (when enableKeyboard: true, default)
 * ─────────────────────────────────────────────────────────────────────
 *
 *   ↑ / ↓        Move active mezi visible nodes
 *   ← / →        Collapse / expand current folder (na leaf nothing)
 *   Enter        Trigger onClick (or per-node handler)
 *   Space        Same as Enter
 *   Esc          Clear filter (pokud focus v search) NEBO unfocus tree
 *   Home / End   First / last visible node
 *   F2           Trigger context menu na current active node
 *   /            Focus search input (Ctrl+F as alternative)
 *
 * ─────────────────────────────────────────────────────────────────────
 * TreeNode shape
 * ─────────────────────────────────────────────────────────────────────
 *
 *   {
 *     id: string|number,             // unique
 *     parent_id?: string|number,     // null = root (or pre-grouped via children)
 *     label: string,                 // display text
 *     icon?: string,                 // emoji nebo CSS class
 *     kind?: 'folder' | 'leaf' | 'divider' | 'hint',
 *                                    // default 'leaf'
 *                                    // 'divider' renders <hr> (popup menu)
 *                                    // 'hint' renders italic dim text (popup menu)
 *     children?: TreeNode[],         // optional pre-grouped (jinak flat with parent_id)
 *     data?: object,                 // app-specific (cislo_def, atd.) →
 *                                     pass-through na li.dataset
 *     handler?: (node, e) => void,   // per-node action callback (popup menu)
 *     visible?: (node, ctx) => bool, // conditional show
 *     enabled?: (node, ctx) => bool, // conditional enable (disabled = grayed, no click)
 *     badge?: { text, color },       // optional badge
 *     className?: string,            // extra CSS class na <li>
 *     sort_order?: number,           // optional sort within parent
 *     keepOpen?: bool,               // popup menu: nezavírat po click (toggle items)
 *   }
 *
 * Phase B+6.11 (10.5.2026 odpoledne).
 * Marti's catches: TreeView je also ERP komponenta + popup menu primitive.
 */
(function (global) {
  "use strict";

  // Phase JS-9 (18.5.2026): mutual immunity wrap pro Module Health visibility.
  const _loader = (typeof global !== "undefined" && global._erpLoadModule)
    ? global._erpLoadModule
    : function (id, ver, fn) { try { fn(); } catch (e) { console.error("[" + id + "] init failed:", e); } };

  _loader("treeview.js", "v1.0.0", function () {


  // ── Helpers ──────────────────────────────────────────────────────

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
    return String(value).replace(/[^\w-]/g, "\\$&");
  }

  // ── Class ────────────────────────────────────────────────────────

  class ErpTreeView {
    constructor(container, options) {
      this.container = container;
      this.options = Object.assign({
        // Data
        dataSource: null,             // async callback returning TreeNode[] OR Array
        // Callbacks
        onClick: null,                // (node, event) — global click (subclass override or per-node handler preferred)
        onContextMenu: null,          // (node, event) — right-click forward
        onExpand: null,               // (node, isExpanded)
        // Features
        enableSearch: true,
        enableKeyboard: true,
        enablePersistence: true,
        // Slots / actions
        headerSlot: null,             // HTMLElement rendered above search
        footerSlot: null,             // HTMLElement rendered below tree
        toolbar: null,                // [{label, icon, handler(treeView), tooltip}]
        nodeActions: null,            // [{label, icon, handler(node, e), visible(node), tooltip}]
        // Icons
        iconResolver: null,           // (node, isExpanded) => string|null  (overrides defaults)
        defaultIcons: null,           // { folderClosed, folderOpen, leaf }  (built-in fallback)
        // Storage
        storageKeyPrefix: "erp.tree",
        // Visual
        cssClassPrefix: "erp-tree",
        indentPx: 16,
        searchPlaceholder: "Hledat…",
        emptyMessage: "Žádné položky",
        loadingMessage: "Načítám...",
        filterDebounceMs: 80,
      }, options || {});

      this._destroyed = false;
      this._data = null;
      this._nodeIndex = new Map();   // String(id) → node
      this._expandedIds = new Set();
      this._activeId = null;
      this._filterText = "";
      this._filterDebounceTimer = null;
      this._activeRow = null;        // cached active row element

      this._buildSkeleton();
      this._restoreFromStorage();
    }

    // ════════════════════════════════════════════════════════════════
    // LIFECYCLE
    // ════════════════════════════════════════════════════════════════

    /**
     * Override-able by subclass.
     * Builds search input + root container + optional slots/toolbar.
     */
    _buildSkeleton() {
      const cls = this.options.cssClassPrefix;
      this.container.classList.add(cls + "-pane");
      this.container.innerHTML = "";

      // Header slot (custom HTML above everything)
      if (this.options.headerSlot) {
        this.headerSlotEl = document.createElement("div");
        this.headerSlotEl.className = cls + "-header-slot";
        this.headerSlotEl.appendChild(this.options.headerSlot);
        this.container.appendChild(this.headerSlotEl);
      }

      // Toolbar (built-in actions)
      if (Array.isArray(this.options.toolbar) && this.options.toolbar.length > 0) {
        this.toolbarEl = document.createElement("div");
        this.toolbarEl.className = cls + "-toolbar";
        this.options.toolbar.forEach((action, idx) => {
          if (!action) return;
          const btn = document.createElement("button");
          btn.type = "button";
          btn.className = cls + "-toolbar-btn";
          btn.dataset.actionIdx = String(idx);
          if (action.tooltip) btn.title = action.tooltip;
          if (action.label) btn.setAttribute("aria-label", action.label);
          if (action.icon) {
            const ico = document.createElement("span");
            ico.className = cls + "-toolbar-icon";
            ico.textContent = String(action.icon);
            btn.appendChild(ico);
          }
          if (action.label && !action.iconOnly) {
            const lbl = document.createElement("span");
            lbl.className = cls + "-toolbar-label";
            lbl.textContent = action.label;
            btn.appendChild(lbl);
          }
          this.toolbarEl.appendChild(btn);
        });
        this.container.appendChild(this.toolbarEl);
      }

      // Search input (optional)
      if (this.options.enableSearch) {
        this.searchEl = document.createElement("div");
        this.searchEl.className = cls + "-search";

        this.searchInput = document.createElement("input");
        this.searchInput.type = "search";
        this.searchInput.className = cls + "-search-input";
        this.searchInput.placeholder = this.options.searchPlaceholder;
        this.searchInput.setAttribute("aria-label", "Vyhledávání ve stromu");
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
      this.rootEl.setAttribute("role", "tree");  // ARIA
      if (this.options.enableKeyboard) {
        this.rootEl.tabIndex = 0;  // make focusable for keyboard nav
      }
      this.rootEl.innerHTML =
        '<div class="' + cls + '-loading">' +
        _esc(this.options.loadingMessage) +
        '</div>';
      this.container.appendChild(this.rootEl);

      // Footer slot (custom HTML below tree)
      if (this.options.footerSlot) {
        this.footerSlotEl = document.createElement("div");
        this.footerSlotEl.className = cls + "-footer-slot";
        this.footerSlotEl.appendChild(this.options.footerSlot);
        this.container.appendChild(this.footerSlotEl);
      }
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
      const oldExpanded = new Set(this._expandedIds);
      const oldActive = this._activeId;
      const oldFilter = this._filterText;
      try {
        const ds = this.options.dataSource;
        const data = (typeof ds === "function") ? await ds() : (Array.isArray(ds) ? ds : []);
        this._data = data || [];
        this._buildIndex();
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
      if (this._docKeydownHandler) {
        document.removeEventListener("keydown", this._docKeydownHandler, true);
      }
      if (this.container) {
        this.container.innerHTML = "";
        this.container.classList.remove(this.options.cssClassPrefix + "-pane");
      }
      this._nodeIndex.clear();
      this._expandedIds.clear();
      this._data = null;
      this._activeId = null;
    }

    // ════════════════════════════════════════════════════════════════
    // PUBLIC API
    // ════════════════════════════════════════════════════════════════

    setActive(id) {
      const cls = this.options.cssClassPrefix;
      const oldActive = this.rootEl.querySelector("." + cls + "-row.active");
      if (oldActive) {
        oldActive.classList.remove("active");
        oldActive.setAttribute("aria-selected", "false");
      }
      this._activeId = (id == null || id === "") ? null : String(id);
      this._activeRow = null;
      if (this._activeId != null) {
        const item = this._findItemById(this._activeId);
        if (item) {
          const row = item.querySelector(":scope > ." + cls + "-row");
          if (row) {
            row.classList.add("active");
            row.setAttribute("aria-selected", "true");
            this._activeRow = row;
          }
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

    getContainer() { return this.container; }

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

    /**
     * Trigger context menu callback programmaticky (used by F2 keyboard shortcut).
     */
    triggerContextMenu(id, syntheticEvent) {
      if (typeof this.options.onContextMenu !== "function") return;
      const sid = id != null ? String(id) : this._activeId;
      if (sid == null) return;
      const node = this._nodeIndex.get(sid);
      if (!node) return;
      try {
        this.options.onContextMenu(node, syntheticEvent || { preventDefault: () => {}, target: this._activeRow });
      } catch (e) {
        console.error("[ErpTreeView] triggerContextMenu failed:", e);
      }
    }

    // ════════════════════════════════════════════════════════════════
    // INTERNAL: index + lookup
    // ════════════════════════════════════════════════════════════════

    _buildIndex() {
      this._nodeIndex.clear();
      const walk = (nodes, parentId) => {
        for (const n of nodes || []) {
          if (n == null || n.id == null) continue;
          const norm = Object.assign({}, n);
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

    /**
     * Override-able by subclass.
     * Returns icon string for node based on iconResolver / defaultIcons / explicit n.icon.
     */
    _resolveIcon(node, isExpanded, isFolder) {
      // Priority 1: iconResolver callback
      if (typeof this.options.iconResolver === "function") {
        try {
          const resolved = this.options.iconResolver(node, isExpanded);
          if (resolved != null) return String(resolved);
        } catch (e) {
          console.warn("[ErpTreeView] iconResolver failed:", e);
        }
      }
      // Priority 2: explicit node.icon
      if (node.icon != null) return String(node.icon);
      // Priority 3: defaultIcons
      if (this.options.defaultIcons) {
        const di = this.options.defaultIcons;
        if (isFolder) {
          return isExpanded ? (di.folderOpen || null) : (di.folderClosed || null);
        }
        return di.leaf || null;
      }
      return null;
    }

    /**
     * Evaluate node visibility / enable state.
     * Override-able by subclass.
     */
    _isNodeVisible(node) {
      if (typeof node.visible === "function") {
        try { return !!node.visible(node, this); } catch (e) { return true; }
      }
      return true;
    }
    _isNodeEnabled(node) {
      if (typeof node.enabled === "function") {
        try { return !!node.enabled(node, this); } catch (e) { return true; }
      }
      return true;
    }

    // ════════════════════════════════════════════════════════════════
    // INTERNAL: render
    // ════════════════════════════════════════════════════════════════

    /**
     * Override-able by subclass.
     */
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
      ul.setAttribute("role", "group");
      this._renderNodes(rootNodes, 0, ul);
      this.rootEl.innerHTML = "";
      this.rootEl.appendChild(ul);

      if (this._filterText) this._applyFilter(this._filterText);
    }

    /**
     * Override-able by subclass — recursive node renderer.
     * Called with { nodes, depth, parentUlEl }.
     */
    _renderNodes(nodes, depth, parentUlEl) {
      const cls = this.options.cssClassPrefix;
      for (const n of nodes) {
        if (!this._isNodeVisible(n)) continue;

        // Special kinds: divider + hint (popup menu use case)
        if (n.kind === "divider") {
          const li = document.createElement("li");
          li.className = cls + "-item " + cls + "-divider";
          li.setAttribute("role", "separator");
          li.dataset.id = String(n.id);
          parentUlEl.appendChild(li);
          continue;
        }
        if (n.kind === "hint") {
          const li = document.createElement("li");
          li.className = cls + "-item " + cls + "-hint";
          li.setAttribute("role", "presentation");
          li.dataset.id = String(n.id);
          const hintLabel = document.createElement("span");
          hintLabel.className = cls + "-hint-label";
          hintLabel.textContent = String(n.label || "");
          li.appendChild(hintLabel);
          parentUlEl.appendChild(li);
          continue;
        }

        // Standard node (folder or leaf)
        const li = document.createElement("li");
        li.className = cls + "-item";
        li.setAttribute("role", "treeitem");

        const childrenNodes = this._getChildren(n.id);
        const hasChildren = childrenNodes.length > 0;
        // Phase 38.4 Krok 14g-H+6 (15.5.2026 dopo, Marti's "bez kind"):
        // isFolder = ma children. Uniform components — folder vs leaf je
        // strukturalni fakt, ne typ field. Soudecek s core_id + children =
        // expandable AND clickable.
        const isFolder = hasChildren;

        if (isFolder) li.classList.add(cls + "-folder");
        else li.classList.add(cls + "-leaf");

        if (n.className) {
          for (const c of String(n.className).split(/\s+/)) {
            if (c) li.classList.add(c);
          }
        }
        li.dataset.id = String(n.id);
        const labelText = String(n.label != null ? n.label : n.id);
        li.dataset.text = _normalizeSearch(labelText);

        const isEnabled = this._isNodeEnabled(n);
        if (!isEnabled) {
          li.classList.add(cls + "-disabled");
          li.setAttribute("aria-disabled", "true");
        }

        // Pass-through n.data → li.dataset
        if (n.data && typeof n.data === "object") {
          for (const [k, v] of Object.entries(n.data)) {
            if (v == null) continue;
            li.dataset[k] = String(v);
          }
        }

        // Row
        const row = document.createElement("div");
        row.className = cls + "-row";
        row.style.paddingLeft = (depth * this.options.indentPx) + "px";
        row.setAttribute("role", "presentation");

        const isExpanded = this._expandedIds.has(String(n.id));
        if (hasChildren) {
          li.setAttribute("aria-expanded", isExpanded ? "true" : "false");
        }

        // Toggle / spacer
        const toggle = document.createElement("span");
        if (hasChildren) {
          toggle.className = cls + "-toggle";
          toggle.textContent = isExpanded ? "▼" : "▶";
          toggle.dataset.role = "toggle";
          toggle.setAttribute("aria-hidden", "true");
        } else {
          toggle.className = cls + "-spacer";
          toggle.setAttribute("aria-hidden", "true");
        }
        row.appendChild(toggle);

        // Icon
        const iconStr = this._resolveIcon(n, isExpanded, isFolder);
        if (iconStr) {
          const ico = document.createElement("span");
          ico.className = cls + "-icon";
          ico.textContent = iconStr;
          ico.setAttribute("aria-hidden", "true");
          row.appendChild(ico);
        }

        // Label
        const label = document.createElement("span");
        label.className = cls + "-label";
        label.textContent = labelText;
        row.appendChild(label);

        // Submenu arrow indicator (folder s handler — popup menu pattern)
        if (hasChildren && typeof n.handler === "function") {
          const arrow = document.createElement("span");
          arrow.className = cls + "-submenu-arrow";
          arrow.textContent = "▶";
          arrow.setAttribute("aria-hidden", "true");
          row.appendChild(arrow);
        }

        // Badge
        if (n.badge && n.badge.text) {
          const badge = document.createElement("span");
          badge.className = cls + "-badge";
          if (n.badge.color) badge.style.color = n.badge.color;
          badge.textContent = String(n.badge.text);
          row.appendChild(badge);
        }

        // Per-node kebab actions menu (universal nodeActions config)
        if (Array.isArray(this.options.nodeActions) && this.options.nodeActions.length > 0) {
          const visibleActions = this.options.nodeActions.filter(a =>
            !a.visible || (() => { try { return !!a.visible(n, this); } catch (e) { return true; } })()
          );
          if (visibleActions.length > 0) {
            const kebab = document.createElement("span");
            kebab.className = cls + "-kebab";
            kebab.dataset.role = "kebab";
            kebab.setAttribute("aria-label", "Akce");
            kebab.title = "Akce";
            kebab.textContent = "⋮";
            row.appendChild(kebab);
          }
        }

        if (this._activeId != null && String(this._activeId) === String(n.id)) {
          row.classList.add("active");
          row.setAttribute("aria-selected", "true");
        }

        li.appendChild(row);

        // Children container
        if (hasChildren) {
          const childWrap = document.createElement("div");
          childWrap.className = cls + "-children";
          childWrap.style.display = isExpanded ? "block" : "none";
          const childUl = document.createElement("ul");
          childUl.className = cls + "-list";
          childUl.setAttribute("role", "group");
          this._renderNodes(childrenNodes, depth + 1, childUl);
          childWrap.appendChild(childUl);
          li.appendChild(childWrap);
        }

        parentUlEl.appendChild(li);
      }
    }

    // ════════════════════════════════════════════════════════════════
    // INTERNAL: handlers
    // ════════════════════════════════════════════════════════════════

    /**
     * Override-able by subclass.
     */
    _attachHandlers() {
      const cls = this.options.cssClassPrefix;

      // Click handler (delegated)
      this.rootEl.addEventListener("click", (e) => this._onRowClick(e));

      // Right-click context menu
      if (typeof this.options.onContextMenu === "function") {
        this.rootEl.addEventListener("contextmenu", (e) => this._onContextMenu(e));
      }

      // Search input
      if (this.options.enableSearch && this.searchInput) {
        this.searchInput.addEventListener("input", () => {
          if (this._filterDebounceTimer) clearTimeout(this._filterDebounceTimer);
          this._filterDebounceTimer = setTimeout(() => {
            this.setFilter(this.searchInput.value);
          }, this.options.filterDebounceMs);
        });
        this.searchInput.addEventListener("keydown", (e) => {
          if (e.key === "Escape") {
            if (this.searchInput.value) {
              this.searchInput.value = "";
              this.setFilter("");
            } else {
              this.searchInput.blur();
            }
            e.stopPropagation();
          }
        });
        if (this.searchClearBtn) {
          this.searchClearBtn.addEventListener("click", () => {
            this.searchInput.value = "";
            this.setFilter("");
            this.searchInput.focus();
          });
        }
      }

      // Toolbar
      if (this.toolbarEl && Array.isArray(this.options.toolbar)) {
        this.toolbarEl.addEventListener("click", (e) => {
          const btn = e.target.closest("." + cls + "-toolbar-btn");
          if (!btn) return;
          const idx = parseInt(btn.dataset.actionIdx, 10);
          const action = this.options.toolbar[idx];
          if (action && typeof action.handler === "function") {
            try { action.handler(this); }
            catch (err) { console.error("[ErpTreeView] toolbar action failed:", err); }
          }
        });
      }

      // Keyboard navigation (when enabled)
      if (this.options.enableKeyboard) {
        this.rootEl.addEventListener("keydown", (e) => this._onKeyDown(e));
      }
    }

    /**
     * Override-able by subclass.
     */
    _onRowClick(e) {
      const cls = this.options.cssClassPrefix;
      const row = e.target.closest("." + cls + "-row");
      if (!row) return;
      const item = row.parentElement;
      if (!item || !item.classList.contains(cls + "-item")) return;
      const id = item.dataset.id;
      if (id == null) return;
      const node = this._nodeIndex.get(String(id));
      if (!node) return;

      // Disabled = no action
      if (item.classList.contains(cls + "-disabled")) return;

      const targetRole = e.target.dataset && e.target.dataset.role;

      // Toggle click → expand/collapse only
      if (targetRole === "toggle") {
        this._toggleExpanded(id);
        e.stopPropagation();
        return;
      }

      // Kebab click → open per-node actions menu
      if (targetRole === "kebab") {
        e.stopPropagation();
        this._showKebabMenu(node, e.target);
        return;
      }

      // Active row click — selection + handler dispatch
      this.setActive(id);

      // Per-node handler priority over global onClick (popup menu pattern)
      if (typeof node.handler === "function") {
        try { node.handler(node, e); }
        catch (err) { console.error("[ErpTreeView] node handler failed:", err); }
        return;
      }

      // Global onClick callback
      if (typeof this.options.onClick === "function") {
        try { this.options.onClick(node, e); }
        catch (err) { console.error("[ErpTreeView] onClick failed:", err); }
      }
    }

    _onContextMenu(e) {
      const cls = this.options.cssClassPrefix;
      const row = e.target.closest("." + cls + "-row");
      if (!row) return;
      const item = row.parentElement;
      const id = item && item.dataset && item.dataset.id;
      if (id == null) return;
      const node = this._nodeIndex.get(String(id));
      if (!node) return;
      e.preventDefault();
      try { this.options.onContextMenu(node, e); }
      catch (err) { console.error("[ErpTreeView] onContextMenu failed:", err); }
    }

    /**
     * Per-node kebab menu — drobný popup s actions z options.nodeActions.
     * Override-able by subclass for custom UX.
     */
    _showKebabMenu(node, kebabEl) {
      const cls = this.options.cssClassPrefix;
      // Close any existing kebab
      this._hideKebabMenu();

      const actions = (this.options.nodeActions || []).filter(a =>
        !a.visible || (() => { try { return !!a.visible(node, this); } catch (e) { return true; } })()
      );
      if (actions.length === 0) return;

      const dropdown = document.createElement("div");
      dropdown.className = cls + "-kebab-dropdown";
      dropdown.setAttribute("role", "menu");

      actions.forEach((action) => {
        const item = document.createElement("button");
        item.type = "button";
        item.className = cls + "-kebab-item";
        item.setAttribute("role", "menuitem");
        if (action.tooltip) item.title = action.tooltip;
        if (action.icon) {
          const ico = document.createElement("span");
          ico.className = cls + "-kebab-icon";
          ico.textContent = String(action.icon);
          item.appendChild(ico);
        }
        const lbl = document.createElement("span");
        lbl.className = cls + "-kebab-label";
        lbl.textContent = String(action.label || "");
        item.appendChild(lbl);
        item.addEventListener("click", (ev) => {
          ev.stopPropagation();
          this._hideKebabMenu();
          if (typeof action.handler === "function") {
            try { action.handler(node, ev); }
            catch (err) { console.error("[ErpTreeView] kebab action failed:", err); }
          }
        });
        dropdown.appendChild(item);
      });

      // Position near kebab button
      const rect = kebabEl.getBoundingClientRect();
      dropdown.style.position = "fixed";
      dropdown.style.top = rect.bottom + "px";
      dropdown.style.left = Math.max(0, rect.right - 180) + "px";  // right-align
      dropdown.style.zIndex = "9999";
      document.body.appendChild(dropdown);

      // Auto-close on outside click + Esc
      this._kebabDropdown = dropdown;
      this._kebabCloseHandler = (ev) => {
        if (!dropdown.contains(ev.target)) this._hideKebabMenu();
      };
      this._kebabKeyHandler = (ev) => {
        if (ev.key === "Escape") this._hideKebabMenu();
      };
      setTimeout(() => {
        document.addEventListener("click", this._kebabCloseHandler);
        document.addEventListener("keydown", this._kebabKeyHandler);
      }, 0);
    }

    _hideKebabMenu() {
      if (this._kebabDropdown && this._kebabDropdown.parentNode) {
        this._kebabDropdown.parentNode.removeChild(this._kebabDropdown);
      }
      this._kebabDropdown = null;
      if (this._kebabCloseHandler) {
        document.removeEventListener("click", this._kebabCloseHandler);
        this._kebabCloseHandler = null;
      }
      if (this._kebabKeyHandler) {
        document.removeEventListener("keydown", this._kebabKeyHandler);
        this._kebabKeyHandler = null;
      }
    }

    // ════════════════════════════════════════════════════════════════
    // KEYBOARD NAVIGATION
    // ════════════════════════════════════════════════════════════════

    _onKeyDown(e) {
      // Ignore if focus v search input (search má vlastní handler)
      if (e.target === this.searchInput) return;

      const cls = this.options.cssClassPrefix;
      const k = e.key;

      if (k === "ArrowDown") {
        this._moveActive(+1);
        e.preventDefault();
      } else if (k === "ArrowUp") {
        this._moveActive(-1);
        e.preventDefault();
      } else if (k === "ArrowRight") {
        if (this._activeId != null) {
          const node = this._nodeIndex.get(this._activeId);
          if (node && this._getChildren(node.id).length > 0) {
            if (!this._expandedIds.has(this._activeId)) {
              this.expand(this._activeId);
            } else {
              // Already expanded — move to first child
              this._moveActive(+1);
            }
          }
          e.preventDefault();
        }
      } else if (k === "ArrowLeft") {
        if (this._activeId != null) {
          if (this._expandedIds.has(this._activeId)) {
            this.collapse(this._activeId);
          } else {
            // Move to parent
            const node = this._nodeIndex.get(this._activeId);
            if (node && node.parent_id != null) {
              this.setActive(node.parent_id);
            }
          }
          e.preventDefault();
        }
      } else if (k === "Enter" || k === " ") {
        if (this._activeId != null && this._activeRow) {
          const fakeEvent = { target: this._activeRow, preventDefault: () => {}, stopPropagation: () => {} };
          this._onRowClick(fakeEvent);
          e.preventDefault();
        }
      } else if (k === "Home") {
        const visibleRows = this._getVisibleRows();
        if (visibleRows.length > 0) {
          const firstId = visibleRows[0].parentElement.dataset.id;
          this.setActive(firstId);
        }
        e.preventDefault();
      } else if (k === "End") {
        const visibleRows = this._getVisibleRows();
        if (visibleRows.length > 0) {
          const lastId = visibleRows[visibleRows.length - 1].parentElement.dataset.id;
          this.setActive(lastId);
        }
        e.preventDefault();
      } else if (k === "F2") {
        this.triggerContextMenu(this._activeId, { preventDefault: () => {}, target: this._activeRow });
        e.preventDefault();
      } else if (k === "Escape") {
        // Pokud filter aktivní, clear; jinak unfocus
        if (this._filterText) {
          this.setFilter("");
          if (this.searchInput) this.searchInput.value = "";
        }
      } else if (k === "/" && !e.ctrlKey && !e.metaKey) {
        if (this.searchInput) {
          this.searchInput.focus();
          e.preventDefault();
        }
      } else if ((e.ctrlKey || e.metaKey) && k === "f") {
        if (this.searchInput) {
          this.searchInput.focus();
          this.searchInput.select();
          e.preventDefault();
        }
      }
    }

    _getVisibleRows() {
      const cls = this.options.cssClassPrefix;
      // Visible = not hidden by filter, not inside collapsed parent
      const all = Array.from(this.rootEl.querySelectorAll("." + cls + "-row"));
      return all.filter(row => {
        if (row.offsetParent === null) return false;  // hidden
        const item = row.parentElement;
        if (item && item.style.display === "none") return false;
        return true;
      });
    }

    _moveActive(direction) {
      const visible = this._getVisibleRows();
      if (visible.length === 0) return;
      let currentIdx = -1;
      if (this._activeRow) {
        currentIdx = visible.indexOf(this._activeRow);
      }
      let nextIdx;
      if (currentIdx === -1) {
        nextIdx = direction > 0 ? 0 : visible.length - 1;
      } else {
        nextIdx = currentIdx + direction;
        if (nextIdx < 0) nextIdx = 0;
        if (nextIdx >= visible.length) nextIdx = visible.length - 1;
      }
      const nextRow = visible[nextIdx];
      const nextItem = nextRow && nextRow.parentElement;
      if (nextItem && nextItem.dataset.id != null) {
        this.setActive(nextItem.dataset.id);
      }
    }

    // ════════════════════════════════════════════════════════════════
    // EXPAND / COLLAPSE
    // ════════════════════════════════════════════════════════════════

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
        item.setAttribute("aria-expanded", wasExpanded ? "false" : "true");
        // Re-resolve icon (folder open vs closed default)
        const iconEl = item.querySelector(
          ":scope > ." + cls + "-row > ." + cls + "-icon"
        );
        if (iconEl) {
          const node = this._nodeIndex.get(sid);
          if (node) {
            // Phase 38.4 Krok 14g-H+6 (15.5.2026 dopo): drop kind check,
            // jen hasChildren rozhoduje. Uniform components doctrine.
            const isFolder = this._getChildren(sid).length > 0;
            const newIcon = this._resolveIcon(node, !wasExpanded, isFolder);
            if (newIcon != null) iconEl.textContent = newIcon;
          }
        }
      }
      this._saveToStorage();

      if (typeof this.options.onExpand === "function") {
        const node = this._nodeIndex.get(sid);
        if (node) {
          try { this.options.onExpand(node, !wasExpanded); }
          catch (e) { console.error("[ErpTreeView] onExpand failed:", e); }
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
            parentItem.setAttribute("aria-expanded", "true");
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
      if (row) {
        row.classList.add("active");
        row.setAttribute("aria-selected", "true");
        this._activeRow = row;
      }
      this._expandAncestors(item);
      if (row && typeof row.scrollIntoView === "function") {
        try { row.scrollIntoView({ block: "nearest" }); } catch (e) { /* noop */ }
      }
    }

    // ════════════════════════════════════════════════════════════════
    // FILTER
    // ════════════════════════════════════════════════════════════════

    _applyFilter(text) {
      const cls = this.options.cssClassPrefix;
      const norm = _normalizeSearch(text);
      const allItems = this.rootEl.querySelectorAll("." + cls + "-item");

      if (this.searchClearBtn) {
        this.searchClearBtn.style.display = norm ? "" : "none";
      }

      if (!norm) {
        allItems.forEach(it => {
          it.style.display = "";
          it.classList.remove(
            cls + "-match", cls + "-match-parent", cls + "-match-descendant"
          );
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

      const matchedIds = new Set();
      allItems.forEach(it => {
        it.classList.remove(
          cls + "-match", cls + "-match-parent", cls + "-match-descendant"
        );
        const label = it.querySelector(
          ":scope > ." + cls + "-row > ." + cls + "-label"
        );
        if (label && label.dataset.original) {
          label.textContent = label.dataset.original;
          delete label.dataset.original;
        }

        const txt = it.dataset.text || "";
        if (txt && txt.indexOf(norm) !== -1) {
          matchedIds.add(it.dataset.id);
          it.classList.add(cls + "-match");
          if (label) {
            const original = label.textContent;
            const lower = _normalizeSearch(original);
            const idx = lower.indexOf(norm);
            if (idx !== -1) {
              label.dataset.original = original;
              label.innerHTML =
                _esc(original.substring(0, idx)) +
                '<mark>' + _esc(original.substring(idx, idx + norm.length)) + '</mark>' +
                _esc(original.substring(idx + norm.length));
            }
          }
        }
      });

      // Mark ancestors of matches
      matchedIds.forEach(matchedId => {
        const item = this._findItemById(matchedId);
        if (!item) return;
        let cur = item.parentElement;
        while (cur) {
          if (cur.classList && cur.classList.contains(cls + "-children")) {
            cur.style.display = "block";
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

      // Mark descendants of folder matches
      matchedIds.forEach(matchedId => {
        const item = this._findItemById(matchedId);
        if (!item || !item.classList.contains(cls + "-folder")) return;
        const descendants = item.querySelectorAll("." + cls + "-item");
        descendants.forEach(d => {
          if (d !== item) d.classList.add(cls + "-match-descendant");
        });
      });

      // Hide non-match/parent/descendant
      allItems.forEach(it => {
        const isMatch = it.classList.contains(cls + "-match");
        const isParent = it.classList.contains(cls + "-match-parent");
        const isDesc = it.classList.contains(cls + "-match-descendant");
        it.style.display = (isMatch || isParent || isDesc) ? "" : "none";
      });
    }

    // ════════════════════════════════════════════════════════════════
    // PERSISTENCE
    // ════════════════════════════════════════════════════════════════

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

  }); // _erpLoadModule end
})(typeof window !== "undefined" ? window : globalThis);
