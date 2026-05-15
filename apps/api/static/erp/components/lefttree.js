/**
 * ErpLeftPanelTree — ERP left panel tree (subclass ErpTreeView).
 *
 * První consumer base ErpTreeView. Specializace pro:
 *   • Centrála 1 menu strom (EC_CentralaMenu) + System soudečky
 *   • Numerické ikony (n.ikona % 100, char code)
 *   • Leaf vs folder podle cislo_def != null (ne podle hasChildren)
 *   • Star ★ pro pinned (favorites)
 *   • Multi-select (Ctrl+klik) pro context-menu bulk akce
 *   • System data attrs (is_system, system_view, ...)
 *   • Toggle ▶/▼ klik = JEN expand (Marti's UX: nikdy neaktivuje přehled)
 *   • Plain klik na leaf = activate (open tab)
 *
 * Phase B+6.11e (10.5.2026 odpoledne) — první consumer base ErpTreeView.
 *
 * ─────────────────────────────────────────────────────────────────────
 * USAGE (z router.py)
 * ─────────────────────────────────────────────────────────────────────
 *
 *   const tree = new ErpLeftPanelTree(treeRootEl, {
 *     dataSource: async () => {
 *       const r = await fetch("/api/v1/erp/strom");
 *       const j = await r.json();
 *       return ErpLeftPanelTree.adaptServerTree(j.tree || []);
 *     },
 *     onActivate: (node, e, cislo) => openTab(cislo, ..., node),
 *     onPinToggle: (cislo, node, e) => toggleTreeFavorite(cislo),
 *     onMultiSelect: (cislo, isSelected, e) => updateBulkUI(),
 *     onContextMenu: (node, e) => showContextMenu(node, e),
 *   });
 *   await tree.init();
 *   // Po init:
 *   tree.applyPinSet(loadTreeFavorites());
 *
 *   // External events:
 *   document.getElementById("erpTreeSearch").addEventListener("input", (e) => {
 *     tree.setFilter(e.target.value);
 *   });
 *
 *   // View modes (router.py wrapper logic):
 *   tree.applyViewFilter(new Set(loadTreeFavorites()), "favorites");
 *   tree.setEmptyViewMessage("Žádné oblíbené.<br>...");
 *
 * ─────────────────────────────────────────────────────────────────────
 * STORAGE COMPATIBILITY
 * ─────────────────────────────────────────────────────────────────────
 *
 *   • erp.tree.expanded — Set IDs (sdíleno s base, kompatibilní)
 *   • erp.tree.active — UCHOVÁVÁ ROUTER.PY (cislo, ne node ID).
 *     Subclass override _saveToStorage / _restoreFromStorage SKIP active.
 *   • erp.tree.{view, favorites, recent, order.v1, collapsed, width} —
 *     plně v režii router.py wrapper logic.
 *
 * ─────────────────────────────────────────────────────────────────────
 */
(function (global) {
  "use strict";

  if (typeof global.ErpTreeView !== "function") {
    console.error("[ErpLeftPanelTree] requires ErpTreeView to be loaded first");
    return;
  }

  class ErpLeftPanelTree extends global.ErpTreeView {
    /**
     * Adapt server tree response to ErpTreeView TreeNode shape.
     * Server vrací nodes s `menu_text`, `cislo_def`, `ikona`, `is_system`, ...
     * Base čte `n.label` — zde mappujeme + zachováváme original props
     * pro klikové handlery (cislo_def, ikona, is_system).
     */
    static adaptServerTree(serverNodes) {
      if (!Array.isArray(serverNodes)) return [];
      return serverNodes.map(n => {
        const label = n.label || n.menu_text || n.nazev || ('#' + (n.id || '?'));
        return {
          id: n.id,
          label: label,
          // Pass-through pro click handler + decorator
          cislo_def: n.cislo_def,
          ikona: n.ikona,
          is_system: n.is_system === true,
          system_view: n.system_view || null,
          system_view_mode: n.system_view_mode || null,
          single: n.single === true,
          // Phase 38.4 inventory (9.5.2026 vecer): metadata pass-through
          // pro hardcoded marker (🛠️). Backend posila JSONB column z
          // master.menu_node.metadata (DB-driven) nebo Python dict
          // (hardcoded fallback). _decorateLeftPanelLi cte
          // node.metadata?.hardcoded a appenduje 🛠️ k row.
          metadata: n.metadata || null,
          // Phase 38.4 Krok 13.4 (11.5.2026): dispatch_kind pass-through
          // pro A3/HW/orphan marker (✅/🛠️/🔄/⚠️). Backend _build_node
          // computuje z fw.hw_registry.shadow_mode lookup (LEFT JOIN via
          // menu_node.core_id → core.code → hw_registry.code).
          // _decorateLeftPanelLi cte node.dispatch_kind a appenduje
          // symbol k row.
          dispatch_kind: n.dispatch_kind || null,
          // Phase 38.4 (11.5.2026 vecer): core.id + core.code + menu_node PK
          // pass-through pro DESIGN mode alerty (smazat legacy cislo_def).
          // n.id = row["code"] (text identifier), n.menu_node_pk = row["id"] (INT PK).
          menu_node_pk: n.menu_node_pk || null,
          core_id: n.core_id || null,
          core_code: n.core_code || null,
          // Recursive children
          children: Array.isArray(n.children) && n.children.length > 0
            ? ErpLeftPanelTree.adaptServerTree(n.children)
            : [],
        };
      });
    }

    constructor(container, options) {
      super(container, Object.assign({
        cssClassPrefix: "erp-tree",
        storageKeyPrefix: "erp.tree",
        // Search input je externí (#erpTreeSearch v workspace HTML),
        // wire ho přes setFilter() z router.py
        enableSearch: false,
        enableKeyboard: true,
        enablePersistence: true,
        // Default empty/loading messages — router.py je může override
        emptyMessage: "Strom prázdný.",
        loadingMessage: "Načítám strom…",
        indentPx: 16,
        // Default ikony pull z node.ikona — žádný fallback
        defaultIcons: { folderClosed: null, folderOpen: null, leaf: null },
      }, options || {}));

      // ERP-specific state
      this._pinnedSet = new Set();
      this._selectedSet = new Set();
      this._viewFilterSet = null;     // null = no filter (zobrazí vše)
      this._viewMode = "all";         // "all" | "favorites" | "recent"
      this._emptyViewMessage = "(Žádné položky)";
    }

    // ════════════════════════════════════════════════════════════════
    // OVERRIDES — rendering
    // ════════════════════════════════════════════════════════════════

    /**
     * Numerické ikony z n.ikona (Marti's pattern: ikona % 100 = char code).
     * Vrátí null pro folder/leaf bez explicit ikony (žádný fallback).
     */
    _resolveIcon(node, isExpanded, isFolder) {
      if (node.ikona == null) return null;
      try {
        const n = parseInt(node.ikona, 10);
        if (isNaN(n)) return null;
        return String(n % 100);
      } catch (e) {
        return null;
      }
    }

    /**
     * Render hooks — base dělá heavy lifting (DOM construction + rekurze),
     * subclass post-decoruje direct children o ERP-specific markery:
     *
     *   1. Leaf/folder semantic fix (cislo_def != null = leaf, vždy)
     *   2. data-cislo-def attribute (legacy DOM API)
     *   3. System markers (.erp-tree-system, data-system-*)
     *   4. Pinned ★ ikona (ze stavu _pinnedSet)
     *   5. Selection state (ze stavu _selectedSet)
     */
    _renderNodes(nodes, depth, parentUlEl) {
      // Base impl renders this level (recurzivně volá this._renderNodes
      // pro children, takže subclass post-decoruje per-level direct kids).
      super._renderNodes(nodes, depth, parentUlEl);

      const cls = this.options.cssClassPrefix;
      const directLis = parentUlEl.querySelectorAll(":scope > li[data-id]");
      directLis.forEach(li => {
        const id = li.dataset.id;
        const node = this._nodeIndex.get(String(id));
        if (!node) return;
        this._decorateLeftPanelLi(li, node, cls);
      });
    }

    _decorateLeftPanelLi(li, node, cls) {
      const cisloDefStr = (node.cislo_def != null && node.cislo_def !== '')
        ? String(node.cislo_def)
        : '';

      // 1. Leaf/folder semantic — cislo_def != null = leaf (klikatelný přehled),
      //    bez ohledu na hasChildren (Marti's Centrála 1 pattern: jádro může
      //    být i container pro sub-přehledy).
      if (cisloDefStr) {
        li.classList.remove(cls + "-folder");
        li.classList.add(cls + "-leaf");
      }

      // 2. data-cislo-def attribute (legacy API pro tabs/MRU/favorites)
      if (cisloDefStr) li.dataset.cisloDef = cisloDefStr;

      // Phase 38.4 (11.5.2026 vecer): expose fw.* identifiers na DOM
      // pro DESIGN mode context menu (akce 1/3 - soudecek + core prehledu).
      // Tree context menu handler v router.py je vyčítá přes getAttribute.
      // menu_node_pk = INT PK z fw.menu_node.id (data-id je row["code"] text).
      if (node.dispatch_kind) li.dataset.dispatchKind = node.dispatch_kind;
      if (node.menu_node_pk != null) li.dataset.menuNodePk = String(node.menu_node_pk);
      if (node.core_id != null) li.dataset.coreId = String(node.core_id);
      if (node.core_code) li.dataset.coreCode = node.core_code;

      // 3. System markers (Phase 35-E.4)
      if (node.is_system === true) {
        li.classList.add(cls + "-system");
        li.dataset.isSystem = "1";
        if (node.system_view) {
          li.classList.add(cls + "-system-leaf");
          li.dataset.systemView = node.system_view;
          li.dataset.systemViewMode = node.system_view_mode || "";
          li.dataset.systemSingle = node.single ? "1" : "0";
        }
      }

      // 4. Pinned ★ ikona (z _pinnedSet, idempotent)
      if (cisloDefStr) {
        const cisloN = parseInt(cisloDefStr, 10);
        if (cisloN && this._pinnedSet.has(cisloN)) {
          this._injectStarOn(li, cls);
        }
      }

      // 5. Selection state (po refresh přežije)
      if (cisloDefStr) {
        const cisloN = parseInt(cisloDefStr, 10);
        if (cisloN && this._selectedSet.has(cisloN)) {
          const row = li.querySelector(":scope > ." + cls + "-row");
          if (row) row.classList.add(cls + "-selected");
        }
      }

      // 6. Hardcoded marker (🛠️) — DEPRECATED Phase 38.4 Krok 13.4 (11.5.2026).
      //    Puvodne ze 9.5. vecer (metadata.hardcoded=true). Nahrazen
      //    dispatch_kind markerem (sekce 7) ktery rozlisuje a3_primary
      //    vs hw_off vs hw_audit/compare vs orphan — preciznejsi semantika
      //    via fw.hw_registry.shadow_mode lookup.
      //    Marti's *„Ted jen odebrat tu puvodni ikonu ze stromu"* (11.5. vecer).

      // 7. Dispatch kind marker (Phase 38.4 Krok 13.4 — 11.5.2026 vecer).
      //    Backend (router.py _build_system_root_from_db) computuje
      //    node.dispatch_kind z fw.menu_node.core_id → fw.core.code →
      //    fw.hw_registry.shadow_mode lookup chain. Marker zobrazuje
      //    runtime dispatch stav per node:
      //    Marti's doctrine 11.5. vecer: *„Standard je A3, marker jen
      //    pro odchylky"*. Tj. a3_primary = no marker (expected behavior),
      //    markery jen pro anomalies (legacy, migration, orphan).
      //
      //      'a3_primary'  → no marker (standard A3 chain, expected)
      //      'hw_off'      → 🛠️ (legacy hardcoded endpoint, no shadow)
      //      'hw_audit'    → 🔄 (audit shadow mode — passive observation)
      //      'hw_compare'  → 🔄 (compare shadow mode — diff validation)
      //      'orphan'      → ⚠️ (leaf bez hw_registry match — needs attention)
      //      null/folder   → no marker (folders nejsou dispatchable)
      if (node.dispatch_kind) {
        const dispatchMarkers = {
          "hw_off":     { symbol: "🛠️", title: "Legacy hardcoded endpoint (hw_registry shadow_mode=off)" },
          "hw_audit":   { symbol: "🔄", title: "Shadow audit mode (hw_registry shadow_mode=audit)" },
          "hw_compare": { symbol: "🔄", title: "Shadow compare mode (hw_registry shadow_mode=compare)" },
          "orphan":     { symbol: "⚠️", title: "Leaf bez fw.hw_registry zaznamu (orphan dispatch)" }
        };
        const m = dispatchMarkers[node.dispatch_kind];
        if (m) {
          const row = li.querySelector(":scope > ." + cls + "-row");
          if (row && !row.querySelector("." + cls + "-dispatch-marker")) {
            const dm = document.createElement("span");
            dm.className = cls + "-dispatch-marker";
            dm.textContent = " " + m.symbol;
            dm.title = m.title;
            row.appendChild(dm);
          }
        }
      }

      // Phase 38.4 Krok 14g-H (15.5.2026 rano, Marti's "dragable napric
      // celym stromem v design mode only"): cross-parent move pro
      // menu_node nodes. Drag source → drop target → PATCH parent_id.
      //
      // Gate: jen v DESIGN mode + node ma menu_node_pk (skip leaves bez fw mappingu).
      //
      // KOREKCE Krok 14g-H+1 (15.5.2026 rano, Marti's "drop se neprovede"):
      // Existing tree drag delegate na treeRoot (router.py inline JS line
      // 13089+) drag-drop pro same-UL reorder (in-memory). Konflikt s
      // mojeho cross-parent move:
      //   - row.draggable=true (existing) → row.dragstart fires
      //   - treeRoot.dragstart fires (delegation) → set _dragSourceItem
      //   - treeRoot.dragover kontroluje same-UL check → blocks cross-parent
      // Fix: pres ev.stopPropagation() v li.dragstart prevent bubble do
      // treeRoot listener. Plus diagnostic console.info pro Marti smoke.
      try {
        const designOn = (typeof window !== "undefined" && window._erpDesignMode === true);
        const menuPk = li.dataset.menuNodePk ? parseInt(li.dataset.menuNodePk, 10) : null;
        if (designOn && menuPk && !li.dataset.dragAttached) {
          li.dataset.dragAttached = "1";
          li.draggable = true;
          const row = li.querySelector(":scope > ." + cls + "-row");
          // ZRUSIT row.draggable (existing setup) — necht li-level handler vede.
          // Bez toho dragstart fires na row first (innermost), neumeli jsme
          // by zachytit menuPk z li (we'd need walk up). Plus row's existing
          // dragstart NEMAJI handler (jen treeRoot delegation), takze bezpecne.
          if (row) {
            row.removeAttribute("draggable");
          }

          li.addEventListener("dragstart", (ev) => {
            // Capture-phase stopPropagation — block existing treeRoot
            // delegated dragstart (line 13089). Pres delegaci by se nastavil
            // _dragSourceItem + delegated dragover by mohl interfere.
            ev.stopPropagation();
            if (row) row.style.opacity = "0.5";
            try {
              ev.dataTransfer.effectAllowed = "move";
              const payload = {
                menuPk: menuPk,
                label: (li.querySelector("." + cls + "-label") || {}).textContent || ""
              };
              ev.dataTransfer.setData("application/x-erp-menu-node-move", JSON.stringify(payload));
              ev.dataTransfer.setData("text/plain", "menunode:" + menuPk);
              console.info("[LeftTree] dragstart menuPk=" + menuPk, payload);
            } catch (e) {
              console.error("[LeftTree] dragstart setData failed:", e);
            }
          }, true);  // capture phase
          li.addEventListener("dragend", () => {
            if (row) row.style.opacity = "";
            // Clean all drop highlights v tree
            const treeRoot = li.closest("#erpTreeRoot") || document;
            treeRoot.querySelectorAll("." + cls + "-row").forEach((r) => {
              r.style.outline = "";
              r.style.background = "";
            });
          });
          li.addEventListener("dragover", (ev) => {
            const types = ev.dataTransfer && ev.dataTransfer.types;
            const hasMime = types && Array.from(types).includes("application/x-erp-menu-node-move");
            if (!hasMime) return;
            ev.preventDefault();
            ev.stopPropagation();
            try { ev.dataTransfer.dropEffect = "move"; } catch (e) {}
            if (row) {
              row.style.outline = "2px solid #a88cd4";
              row.style.outlineOffset = "-2px";
              row.style.background = "rgba(168, 140, 212, 0.1)";
            }
          });
          li.addEventListener("dragleave", () => {
            if (row) {
              row.style.outline = "";
              row.style.background = "";
            }
          });
          li.addEventListener("drop", async (ev) => {
            console.info("[LeftTree] drop fired on menuPk=" + menuPk);
            const raw = ev.dataTransfer.getData("application/x-erp-menu-node-move");
            console.info("[LeftTree] drop raw payload:", raw);
            if (!raw) {
              console.warn("[LeftTree] drop: empty payload — drag started bez mime?");
              return;
            }
            ev.preventDefault();
            ev.stopPropagation();
            if (row) {
              row.style.outline = "";
              row.style.background = "";
            }
            let payload;
            try { payload = JSON.parse(raw); } catch (e) {
              console.error("[LeftTree] drop: JSON parse failed:", e);
              return;
            }
            if (!payload || !payload.menuPk) {
              console.warn("[LeftTree] drop: payload bez menuPk:", payload);
              return;
            }
            const sourceId = payload.menuPk;
            const targetId = menuPk;
            if (sourceId === targetId) {
              console.info("[LeftTree] drop: self-drop ignored");
              return;
            }
            console.info("[LeftTree] PATCH move", sourceId, "→ parent", targetId);
            try {
              const r = await fetch(
                "/api/v1/erp/design/fw-menu-node/update/" + encodeURIComponent(sourceId),
                {
                  method: "PATCH",
                  headers: { "Content-Type": "application/json" },
                  credentials: "include",
                  body: JSON.stringify({ parent_id: targetId }),
                }
              );
              const d = await r.json().catch(() => ({}));
              console.info("[LeftTree] PATCH response", r.status, d);
              if (!r.ok || !d.ok) {
                throw new Error(d.error || ("HTTP " + r.status));
              }
              // Tree reload
              if (typeof window.reloadErpTree === "function") {
                console.info("[LeftTree] reloadErpTree available — calling");
                await window.reloadErpTree();
              } else {
                console.warn("[LeftTree] reloadErpTree NOT available, full page reload");
                window.location.reload();
              }
            } catch (e) {
              console.error("[LeftTree] menu_node drop fetch failed:", e);
              alert("Přesun selhal: " + (e.message || e));
            }
          });
        }
      } catch (e) {
        console.warn("[LeftTree] drag-drop setup failed:", e);
      }
    }

    _injectStarOn(li, cls) {
      const row = li.querySelector(":scope > ." + cls + "-row");
      if (!row) return;
      row.classList.add(cls + "-pinned");
      if (!row.querySelector("." + cls + "-star")) {
        const star = document.createElement("span");
        star.className = cls + "-star";
        star.textContent = "★";
        star.title = "Odepnout (klik) nebo pravý-klik";
        row.appendChild(star);
      }
    }

    _removeStarFrom(li, cls) {
      const row = li.querySelector(":scope > ." + cls + "-row");
      if (!row) return;
      row.classList.remove(cls + "-pinned");
      const star = row.querySelector("." + cls + "-star");
      if (star) star.remove();
    }

    /**
     * Custom skeleton — router.py už poskytuje wrapper structure
     * (.erp-tree-pane > .erp-tree-header + #erpTreeRoot + .erp-tree-footer).
     * Subclass dostane #erpTreeRoot jako container; používá ho přímo jako
     * rootEl (NE wraps v dalším divu, NE přidává .erp-tree-pane class —
     * jinak CSS collision: treeRoot by měl .erp-tree-root + .erp-tree-pane,
     * což rozbije flex layout (footer nezůstane na bottom).
     */
    _buildSkeleton() {
      const cls = this.options.cssClassPrefix;
      this.container.innerHTML = "";

      // Container IS rootEl (existing #erpTreeRoot div from router.py HTML).
      // Žádný extra wrapper, žádný .erp-tree-pane add (router.py má vlastní
      // <aside class="erp-tree-pane"> jako parent).
      this.rootEl = this.container;
      this.rootEl.setAttribute("role", "tree");
      if (this.options.enableKeyboard) {
        this.rootEl.tabIndex = 0;
      }

      // 5-line skeleton (Marti's existing styl)
      this.rootEl.innerHTML =
        '<div class="' + cls + '-skeleton">' +
        '<div class="erp-skel-line"></div>' +
        '<div class="erp-skel-line short"></div>' +
        '<div class="erp-skel-line"></div>' +
        '<div class="erp-skel-line short"></div>' +
        '<div class="erp-skel-line"></div>' +
        '</div>';
    }

    // ════════════════════════════════════════════════════════════════
    // OVERRIDES — click handling
    // ════════════════════════════════════════════════════════════════

    /**
     * Click semantics:
     *   • Klik na ★ ikonu          → onPinToggle hook (quick unpin)
     *   • Klik na ▶/▼ toggle       → expand/collapse only (žádný activate)
     *   • Ctrl/Cmd+klik             → multi-select toggle
     *   • Plain klik (folder)       → expand + activate (pokud má cislo_def)
     *   • Plain klik (leaf)         → activate via onActivate hook
     */
    _onRowClick(e) {
      const cls = this.options.cssClassPrefix;
      const row = e.target.closest("." + cls + "-row");
      if (!row) return;
      const li = row.parentElement;
      if (!li || !li.classList.contains(cls + "-item")) return;
      const id = li.dataset.id;
      if (id == null) return;
      const node = this._nodeIndex.get(String(id));
      if (!node) return;

      // Disabled = ignore
      if (li.classList.contains(cls + "-disabled")) return;

      // Star click — quick unpin (delegate hook)
      if (e.target.classList && e.target.classList.contains(cls + "-star")) {
        e.stopPropagation();
        const cisloN = parseInt(li.dataset.cisloDef || "0", 10);
        if (cisloN && typeof this.options.onPinToggle === "function") {
          try { this.options.onPinToggle(cisloN, node, e); }
          catch (err) { console.error("[ErpLeftPanelTree] onPinToggle failed:", err); }
        }
        return;
      }

      const targetRole = e.target.dataset && e.target.dataset.role;

      // Toggle (▶/▼) click — JEN expand/collapse (Marti's UX z B+8.2a+++++++)
      if (targetRole === "toggle") {
        this._toggleExpanded(id);
        e.stopPropagation();
        return;
      }

      // Ctrl/Cmd+klik — multi-select toggle (žádný activate, žádné expand)
      if (e.ctrlKey || e.metaKey) {
        e.preventDefault();
        const cisloN = parseInt(li.dataset.cisloDef || "0", 10);
        if (cisloN) {
          this._toggleSelectionInternal(cisloN);
          if (typeof this.options.onMultiSelect === "function") {
            try {
              this.options.onMultiSelect(cisloN, this._selectedSet.has(cisloN), e);
            } catch (err) {
              console.error("[ErpLeftPanelTree] onMultiSelect failed:", err);
            }
          }
        }
        return;
      }

      // Plain klik — clear selection, expand pokud folder, activate pokud leaf
      this.clearSelection();

      // Expand/collapse pokud má children (toggle existence)
      const childrenWrap = li.querySelector(":scope > ." + cls + "-children");
      if (childrenWrap) {
        this._toggleExpanded(id);
      }

      // Activate pokud má cislo_def (klikatelný přehled)
      const cisloDefStr = li.dataset.cisloDef;
      if (cisloDefStr) {
        const cisloN = parseInt(cisloDefStr, 10);
        if (cisloN) {
          // Visual active class (base setActive čistí jiné active rows)
          this.setActive(id);
          // Activate hook → router.py openTab
          if (typeof this.options.onActivate === "function") {
            try { this.options.onActivate(node, e, cisloN); }
            catch (err) { console.error("[ErpLeftPanelTree] onActivate failed:", err); }
          }
        }
      }
    }

    // ════════════════════════════════════════════════════════════════
    // OVERRIDES — persistence (active je v režii router.py, ne base)
    // ════════════════════════════════════════════════════════════════

    /**
     * Subclass save: jen expanded set. Active key je conflict s router.py,
     * který ukládá cislo (ne node ID). Router.py si vede saveActive/loadActive
     * separately. Subclass nepište do `${prefix}.active`.
     */
    _saveToStorage() {
      if (!this.options.enablePersistence) return;
      const prefix = this.options.storageKeyPrefix;
      try {
        localStorage.setItem(
          prefix + ".expanded",
          JSON.stringify(Array.from(this._expandedIds))
        );
      } catch (e) {
        console.warn("[ErpLeftPanelTree] storage save failed:", e);
      }
    }

    /**
     * Subclass restore: jen expanded set. Router.py restoruje active přes
     * vlastní tryRestoreActive() po init().
     */
    _restoreFromStorage() {
      if (!this.options.enablePersistence) return;
      const prefix = this.options.storageKeyPrefix;
      try {
        const expRaw = localStorage.getItem(prefix + ".expanded");
        if (expRaw) {
          const arr = JSON.parse(expRaw);
          if (Array.isArray(arr)) arr.forEach(id => this._expandedIds.add(String(id)));
        }
      } catch (e) {
        console.warn("[ErpLeftPanelTree] storage restore failed:", e);
      }
    }

    // ════════════════════════════════════════════════════════════════
    // PUBLIC API — pinned (favorites)
    // ════════════════════════════════════════════════════════════════

    /**
     * Set entire pinned set. Re-applies ★ visual on all matching rows.
     * Volat po init() pro restore z localStorage favorites.
     */
    applyPinSet(cislos) {
      this._pinnedSet = new Set(
        (cislos || [])
          .map(c => parseInt(c, 10))
          .filter(c => !isNaN(c) && c !== 0)
      );
      if (!this.rootEl) return;
      const cls = this.options.cssClassPrefix;
      this.rootEl.querySelectorAll("li." + cls + "-item").forEach(li => {
        const cisloN = parseInt(li.dataset.cisloDef || "0", 10);
        if (!cisloN) return;
        if (this._pinnedSet.has(cisloN)) this._injectStarOn(li, cls);
        else this._removeStarFrom(li, cls);
      });
    }

    /**
     * Toggle single pinned state. Volat z router.py toggleTreeFavorite po
     * localStorage update + API sync.
     */
    setPinned(cislo, on) {
      const c = parseInt(cislo, 10);
      if (!c) return;
      if (on) this._pinnedSet.add(c);
      else this._pinnedSet.delete(c);
      if (!this.rootEl) return;
      const cls = this.options.cssClassPrefix;
      this.rootEl.querySelectorAll("li." + cls + "-item").forEach(li => {
        if (parseInt(li.dataset.cisloDef || "0", 10) !== c) return;
        if (on) this._injectStarOn(li, cls);
        else this._removeStarFrom(li, cls);
      });
    }

    isPinned(cislo) {
      return this._pinnedSet.has(parseInt(cislo, 10));
    }

    // ════════════════════════════════════════════════════════════════
    // PUBLIC API — multi-select
    // ════════════════════════════════════════════════════════════════

    _toggleSelectionInternal(cislo) {
      const c = parseInt(cislo, 10);
      if (!c) return;
      const cls = this.options.cssClassPrefix;
      if (this._selectedSet.has(c)) {
        this._selectedSet.delete(c);
        this._setSelectionDOM(c, false, cls);
      } else {
        this._selectedSet.add(c);
        this._setSelectionDOM(c, true, cls);
      }
    }

    _setSelectionDOM(cislo, on, cls) {
      if (!this.rootEl) return;
      this.rootEl.querySelectorAll("li." + cls + "-item").forEach(li => {
        if (parseInt(li.dataset.cisloDef || "0", 10) !== cislo) return;
        const row = li.querySelector(":scope > ." + cls + "-row");
        if (!row) return;
        if (on) row.classList.add(cls + "-selected");
        else row.classList.remove(cls + "-selected");
      });
    }

    /**
     * Toggle selection externally (router.py může volat).
     */
    toggleSelection(cislo) {
      this._toggleSelectionInternal(cislo);
    }

    /**
     * Clear all selections. Volat z router.py při Esc nebo na plain klik.
     */
    clearSelection() {
      this._selectedSet.clear();
      if (!this.rootEl) return;
      const cls = this.options.cssClassPrefix;
      this.rootEl
        .querySelectorAll("." + cls + "-row." + cls + "-selected")
        .forEach(r => r.classList.remove(cls + "-selected"));
    }

    /**
     * Returns array of selected cislos. Pro context-menu bulk akce.
     */
    getSelected() {
      return Array.from(this._selectedSet);
    }

    isSelected(cislo) {
      return this._selectedSet.has(parseInt(cislo, 10));
    }

    // ════════════════════════════════════════════════════════════════
    // PUBLIC API — view mode filter (favorites / recent)
    // ════════════════════════════════════════════════════════════════

    /**
     * Apply view mode filter. matchSet = Set<cislo> nebo array.
     * Při mode='all' nebo prázdném matchSet → clear filter (vše viditelné).
     *
     * @param {Set|Array|null} matchCislos
     * @param {string} mode  "all" | "favorites" | "recent"
     */
    applyViewFilter(matchCislos, mode) {
      this._viewMode = mode || "all";
      if (this._viewMode === "all" || matchCislos == null) {
        this._viewFilterSet = null;
      } else {
        const arr = matchCislos instanceof Set
          ? Array.from(matchCislos)
          : Array.isArray(matchCislos) ? matchCislos : [];
        this._viewFilterSet = new Set(
          arr.map(c => parseInt(c, 10)).filter(c => !isNaN(c))
        );
      }
      this._renderViewFilter();
    }

    clearViewFilter() {
      this.applyViewFilter(null, "all");
    }

    setEmptyViewMessage(html) {
      this._emptyViewMessage = String(html || "");
    }

    getViewMode() {
      return this._viewMode;
    }

    _renderViewFilter() {
      if (!this.rootEl) return;
      const cls = this.options.cssClassPrefix;

      // Reset visual state
      this.rootEl.classList.remove(cls + "-view-favorites", cls + "-view-recent");
      this.rootEl.querySelectorAll("." + cls + "-row").forEach(r => {
        r.classList.remove(cls + "-view-match", cls + "-view-match-parent");
      });
      const oldEmpty = this.rootEl.querySelector("." + cls + "-empty-view");
      if (oldEmpty) oldEmpty.remove();

      if (!this._viewFilterSet) return;  // mode = all

      if (this._viewMode === "favorites") {
        this.rootEl.classList.add(cls + "-view-favorites");
      } else if (this._viewMode === "recent") {
        this.rootEl.classList.add(cls + "-view-recent");
      }

      if (this._viewFilterSet.size === 0) {
        // Empty state placeholder (caller poskytl message přes setEmptyViewMessage)
        const empty = document.createElement("div");
        empty.className = cls + "-empty-view";
        empty.innerHTML = this._emptyViewMessage;
        this.rootEl.appendChild(empty);
        return;
      }

      // Mark match rows + ancestor parents (s expand)
      this.rootEl.querySelectorAll("li." + cls + "-item").forEach(li => {
        const cisloN = parseInt(li.dataset.cisloDef || "0", 10);
        if (!cisloN || !this._viewFilterSet.has(cisloN)) return;
        const row = li.querySelector(":scope > ." + cls + "-row");
        if (row) row.classList.add(cls + "-view-match");

        // Expand all ancestors + označ jako match-parent
        let parent = li.parentElement;
        while (parent && parent !== this.rootEl) {
          if (parent.classList && parent.classList.contains(cls + "-children")) {
            parent.style.display = "block";
            const parentLi = parent.parentElement;
            if (parentLi && parentLi.classList && parentLi.classList.contains(cls + "-item")) {
              const pRow = parentLi.querySelector(":scope > ." + cls + "-row");
              if (pRow) pRow.classList.add(cls + "-view-match-parent");
              const tg = pRow ? pRow.querySelector("." + cls + "-toggle") : null;
              if (tg) tg.textContent = "▼";
              if (parentLi.dataset.id) this._expandedIds.add(parentLi.dataset.id);
            }
          }
          parent = parent.parentElement;
        }
      });
    }

    // ════════════════════════════════════════════════════════════════
    // PUBLIC API — lookup helpers (legacy DOM compat)
    // ════════════════════════════════════════════════════════════════

    /**
     * Find first node with given cislo_def. Returns full node or null.
     */
    getNodeByCislo(cislo) {
      const c = parseInt(cislo, 10);
      if (!c) return null;
      for (const node of this._nodeIndex.values()) {
        if (node.cislo_def != null && parseInt(node.cislo_def, 10) === c) {
          return node;
        }
      }
      return null;
    }

    /**
     * Find first <li> element with data-cislo-def == cislo. Pro legacy
     * DOM-aware kód (drag-drop, scrollIntoView, ...).
     */
    findLiByCislo(cislo) {
      if (!this.rootEl) return null;
      const cls = this.options.cssClassPrefix;
      const c = parseInt(cislo, 10);
      if (!c) return null;
      const lis = this.rootEl.querySelectorAll("li." + cls + "-item");
      for (const li of lis) {
        if (parseInt(li.dataset.cisloDef || "0", 10) === c) return li;
      }
      return null;
    }

    /**
     * Build path z node ID na root (pro breadcrumbs). Returns array
     * [{id, label, cislo_def}] od root k node.
     */
    getPathForId(id) {
      const path = [];
      // Walk parent_id chain — base _buildIndex tracks parent přes Map.
      // Bohužel base ukládá node bez parentId reference. Musíme si build
      // vlastní parent map nebo iterovat tree. Simple: walk DOM upward.
      if (!this.rootEl) return path;
      const cls = this.options.cssClassPrefix;
      let li = this.rootEl.querySelector("li[data-id=\"" + String(id) + "\"]");
      while (li && li.classList.contains(cls + "-item")) {
        const node = this._nodeIndex.get(li.dataset.id);
        if (node) {
          path.unshift({
            id: String(node.id),
            label: node.label,
            cislo_def: node.cislo_def != null ? node.cislo_def : null,
          });
        }
        // Step up: li → ul → children → li (parent)
        const ul = li.parentElement;
        const childWrap = ul ? ul.parentElement : null;
        const isChildWrap = childWrap && childWrap.classList.contains(cls + "-children");
        li = isChildWrap ? childWrap.parentElement : null;
      }
      return path;
    }

    /**
     * Expose root element for external listeners (drag-drop, etc.).
     * Inherited from base, but stays explicit here for clarity.
     */
    // getRootElement() — already in base
  }

  global.ErpLeftPanelTree = ErpLeftPanelTree;
})(typeof window !== "undefined" ? window : globalThis);
