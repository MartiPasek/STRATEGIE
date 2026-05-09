/**
 * ErpPopupMenu — context menu / popup menu jako specializovaný tree.
 *
 * Extends ErpTreeView. Stejná hierarchická primitiva (jeden subjekt
 * = jedna komponenta), jiný UX pattern:
 *
 *   • Floating positioning (fixed, viewport-clamped)
 *   • Lifecycle show(x, y) / hide() místo init()
 *   • Auto-close: outside click + Esc + after action invocation
 *   • Žádný search, žádná persistence (popup je ephemeral)
 *   • Žádný toolbar (kompaktní)
 *   • Submenu: kliknutí na folder = inline expand (default tree
 *     pattern); separate hover-open submenu container je budoucí
 *     enhancement.
 *
 * Phase B+6.11 (10.5.2026 odpoledne) — Marti's catch:
 * "pouziti teto komponenty jako popup menu (hojne vyuzivame) kde tree
 * obsahuje nejaky default polozky treba per grid a my je pomoci
 * frameworku rozsirujeme o dalsi polozky"
 *
 * ─────────────────────────────────────────────────────────────────────
 * USAGE
 * ─────────────────────────────────────────────────────────────────────
 *
 *   // Jednorázový popup
 *   const menu = new ErpPopupMenu({
 *     items: [
 *       { id: "open", label: "Otevřít", icon: "▶", handler: openFn },
 *       { id: "edit", label: "Upravit", icon: "✏", handler: editFn },
 *       { id: "_d1", kind: "divider" },
 *       { id: "danger", label: "Smazat", icon: "🗑", handler: delFn,
 *         className: "erp-popup-menu-danger" },
 *     ],
 *     onSelect: (node) => console.log("vybráno", node.id),
 *   });
 *   menu.show(event.clientX, event.clientY);
 *
 *   // S frameworkem-extended položkami (Marti's vize: default per grid +
 *   // custom items z DB master.menu_node)
 *   const menu = new ErpPopupMenu({
 *     items: [...defaultGridActions, ...customMenuFromDb],
 *   });
 *
 *   // Kontextové menu na řádek gridu
 *   gridEl.addEventListener("contextmenu", (e) => {
 *     e.preventDefault();
 *     menu.show(e.clientX, e.clientY, { rowData: gridRow });
 *   });
 *
 * ─────────────────────────────────────────────────────────────────────
 * NODE SHAPES
 * ─────────────────────────────────────────────────────────────────────
 *
 *   { id, label, icon, handler, kind, visible, enabled, className,
 *     children, ... }
 *
 *   kind = 'divider' | 'hint' | (default leaf/folder, viz ErpTreeView)
 *
 * ─────────────────────────────────────────────────────────────────────
 */
(function (global) {
  "use strict";

  if (typeof global.ErpTreeView !== "function") {
    console.error("[ErpPopupMenu] requires ErpTreeView to be loaded first");
    return;
  }

  class ErpPopupMenu extends global.ErpTreeView {
    constructor(options) {
      // Container vyrobíme sami (floating div připojený do <body>)
      const container = document.createElement("div");
      container.className = "erp-popup-menu-container";
      container.setAttribute("role", "menu");
      container.style.position = "fixed";
      container.style.zIndex = "10000";
      container.style.display = "none";  // hidden until show()

      // Předpočítáme dataSource ze statického 'items' arr (popup je
      // typicky volán s pevnými items, ne async fetchem)
      const items = Array.isArray(options && options.items) ? options.items : [];

      const baseOpts = Object.assign({
        // Items lze předat přímo nebo přes dataSource
        dataSource: items,
        // Defaultně bez search/keyboard/persistence (popup je ephemeral)
        enableSearch: false,
        enablePersistence: false,
        enableKeyboard: true,   // Esc + arrow nav v popup je užitečné
        // Custom CSS prefix (odlišíme od regular tree)
        cssClassPrefix: "erp-popup-menu",
        storageKeyPrefix: null,  // no-op (persistence vypnutá)
        // Žádný toolbar, žádné slots (popup je kompaktní)
        toolbar: null,
        nodeActions: null,
        headerSlot: null,
        footerSlot: null,
        // Default ikony pro popup (subtilní)
        defaultIcons: { folderClosed: "▶", folderOpen: "▼", leaf: "" },
        // Visual
        indentPx: 14,
      }, options || {});

      // Wrap user's onClick / onSelect — po klikku zavřít popup
      const userOnClick = baseOpts.onClick;
      const userOnSelect = options && options.onSelect;
      baseOpts.onClick = function (node, e) {
        try {
          if (typeof userOnClick === "function") userOnClick(node, e);
          if (typeof userOnSelect === "function") userOnSelect(node, e);
        } catch (err) {
          console.error("[ErpPopupMenu] onSelect failed:", err);
        }
        // Auto-close po výběru leaf (folder = expand, ne select)
        if (!node.children || node.children.length === 0) {
          this.hide();
        }
      };

      super(container, baseOpts);

      // Přiznáme se k vlastnímu wrapper containeru — _buildSkeleton
      // už proběhl v super(). Ale my chceme floating div bez
      // .erp-popup-menu-pane class navíc — necháme to být, base class
      // už nastavil cls + "-pane" na container. To je OK, máme svůj
      // CSS scope.

      this._isOpen = false;
      this._anchorContext = null;
      this._docClickHandler = null;
      this._docKeydownHandler = null;
    }

    // ════════════════════════════════════════════════════════════════
    // PUBLIC API
    // ════════════════════════════════════════════════════════════════

    /**
     * Show popup at given viewport coordinates.
     *
     * @param {number} x  client X (e.g. event.clientX)
     * @param {number} y  client Y
     * @param {object} [context]  optional context propagated to handlers
     *                            (e.g. { rowData: gridRow }) — uloží se
     *                            do this.context, dostupné v handlerech
     */
    async show(x, y, context) {
      if (this._destroyed) return;
      this._anchorContext = context || null;

      // Pokud ještě nebyl init, udělej ho teď (lazy)
      if (!this._initialized) {
        if (this.container.parentNode == null) {
          document.body.appendChild(this.container);
        }
        await this.init();
        this._initialized = true;
      }

      this._isOpen = true;
      this.container.style.display = "block";
      this._positionAt(x, y);
      this._attachAutoClose();

      // Focus root pro keyboard nav (Esc, šipky)
      if (this.options.enableKeyboard && this.rootEl) {
        try { this.rootEl.focus({ preventScroll: true }); }
        catch (e) { this.rootEl.focus(); }
      }
    }

    /**
     * Hide popup. Bezpečné volat opakovaně.
     */
    hide() {
      if (!this._isOpen) return;
      this._isOpen = false;
      if (this.container) this.container.style.display = "none";
      this._detachAutoClose();
      this._anchorContext = null;
    }

    /**
     * Re-set items dynamically (e.g. když ti DB framework přidá custom
     * položky vedle default grid akcí).
     *
     * @param {Array} items
     */
    async setItems(items) {
      this.options.dataSource = Array.isArray(items) ? items : [];
      if (this._initialized) {
        await this.refresh();
      }
    }

    /**
     * Returns the context passed to show(x, y, context).
     */
    getContext() {
      return this._anchorContext;
    }

    isOpen() {
      return this._isOpen;
    }

    destroy() {
      this.hide();
      super.destroy();
      if (this.container && this.container.parentNode) {
        this.container.parentNode.removeChild(this.container);
      }
    }

    // ════════════════════════════════════════════════════════════════
    // POSITIONING
    // ════════════════════════════════════════════════════════════════

    /**
     * Position popup at (x, y), clamped to viewport. Pokud by se nevešel
     * doprava → flip vlevo. Pokud dolů → flip nahoru.
     */
    _positionAt(x, y) {
      const el = this.container;
      // Nejdřív set left/top na požadované místo, ať si DOM změří size
      el.style.left = "0px";
      el.style.top = "0px";
      el.style.visibility = "hidden";
      el.style.display = "block";

      const rect = el.getBoundingClientRect();
      const w = rect.width;
      const h = rect.height;
      const vw = window.innerWidth || document.documentElement.clientWidth;
      const vh = window.innerHeight || document.documentElement.clientHeight;
      const margin = 4;

      let left = x;
      let top = y;

      // Horizontal clamp / flip
      if (left + w + margin > vw) {
        // Pokud máme aspoň w prostoru vlevo, otoč
        if (x - w >= margin) left = x - w;
        else left = Math.max(margin, vw - w - margin);
      }
      if (left < margin) left = margin;

      // Vertical clamp / flip
      if (top + h + margin > vh) {
        if (y - h >= margin) top = y - h;
        else top = Math.max(margin, vh - h - margin);
      }
      if (top < margin) top = margin;

      el.style.left = left + "px";
      el.style.top = top + "px";
      el.style.visibility = "";
    }

    // ════════════════════════════════════════════════════════════════
    // AUTO-CLOSE (outside click + Esc)
    // ════════════════════════════════════════════════════════════════

    _attachAutoClose() {
      this._detachAutoClose();
      const self = this;

      this._docClickHandler = (ev) => {
        if (!self._isOpen) return;
        if (!self.container.contains(ev.target)) {
          self.hide();
        }
      };
      this._docKeydownHandler = (ev) => {
        if (!self._isOpen) return;
        if (ev.key === "Escape") {
          ev.stopPropagation();
          self.hide();
        }
      };

      // setTimeout 0ms — vyhneme se zachycení toho samého clicku, který
      // popup otevřel (capture phase by jinak ihned zavřela)
      setTimeout(() => {
        if (!self._isOpen) return;
        document.addEventListener("mousedown", self._docClickHandler, true);
        document.addEventListener("keydown", self._docKeydownHandler, true);
      }, 0);
    }

    _detachAutoClose() {
      if (this._docClickHandler) {
        document.removeEventListener("mousedown", this._docClickHandler, true);
        this._docClickHandler = null;
      }
      if (this._docKeydownHandler) {
        document.removeEventListener("keydown", this._docKeydownHandler, true);
        this._docKeydownHandler = null;
      }
    }
  }

  global.ErpPopupMenu = ErpPopupMenu;
})(typeof window !== "undefined" ? window : globalThis);
