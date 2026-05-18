/**
 * ErpPageControl + ErpTabSheet — UI Kit in-form tabs.
 *
 * Phase B+6.9 (6.5.2026 večer). Marti's spec: typ 15 PageControl (parent)
 * + typ 16 TabSheet (child) z Centrály 1. Lokální scope — tabs uvnitř
 * formu, ne globální workspace tabs (které jsou v Phase B+8 multi-tab
 * přehled bar).
 *
 * Centrála 1 vzor (screenshot 2):
 *   PageControl
 *     ├── TabSheet "SQL definice přehledu"
 *     │     └── RichEdit (SQL)
 *     └── TabSheet "Parametry přehledu"
 *           └── ... další components
 *
 * API:
 *
 *   const pc = new ErpPageControl(container, {
 *     tabs: [
 *       { id: "sql", label: "SQL definice", content: <Element> },
 *       { id: "params", label: "Parametry", content: <Element> },
 *     ],
 *     activeId: "sql",
 *     onChange: (newId, oldId) => { ... },
 *   });
 *
 *   pc.activeId() / pc.setActive(id) / pc.addTab(opts) / pc.removeTab(id)
 *   pc.getTab(id) → { id, label, contentEl }
 *   pc.destroy()
 *
 * ErpTabSheet je sama o sobě "container element" — typicky se vytvoří
 * separately a pass-uje do ErpPageControl jako tab.content. Pro form
 * orchestrator použití: ErpForm vytvoří div pro každý TabSheet z metadat
 * + napustí ho child components, a všechny tab divy předá ErpPageControl.
 *
 * Visual: kompaktnější než globální .erp-tab (font 12 vs 13, padding 6/12
 * vs 8/16). Active tab má accent bottom border (3px) — visually attached
 * k content panelu.
 */
(function (global) {
  "use strict";

  // Phase JS-9 (18.5.2026): mutual immunity wrap pro Module Health visibility.
  const _loader = (typeof global !== "undefined" && global._erpLoadModule)
    ? global._erpLoadModule
    : function (id, ver, fn) { try { fn(); } catch (e) { console.error("[" + id + "] init failed:", e); } };

  _loader("pagecontrol.js", "v1.0.0", function () {


  function _esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, c =>
      ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])
    );
  }

  let _instanceCounter = 0;

  class ErpPageControl {
    constructor(container, options) {
      this.container = container || null;
      this.options = Object.assign({
        tabs: [],            // [{id, label, content?, badge?}]
        activeId: null,      // initial active tab id (default = první tab)
        onChange: null,      // (newId, oldId) => void
        tabHeight: 32,       // visual hint pro tab bar
      }, options || {});

      this._destroyed = false;
      this._instanceId = ++_instanceCounter;
      this._tabs = [];       // internal mutable copy
      this._activeId = null;
      this._render();
      // Add initial tabs
      (this.options.tabs || []).forEach(t => this._addTabInternal(t));
      // Set active
      const initialId = this.options.activeId
        || (this._tabs[0] ? this._tabs[0].id : null);
      if (initialId) this.setActive(initialId);
    }

    _render() {
      this.wrapper = document.createElement("div");
      this.wrapper.className = "erp-pagecontrol";

      this.tabsBar = document.createElement("div");
      this.tabsBar.className = "erp-pagecontrol-tabs";
      this.tabsBar.setAttribute("role", "tablist");
      this.wrapper.appendChild(this.tabsBar);

      this.contentArea = document.createElement("div");
      this.contentArea.className = "erp-pagecontrol-content";
      this.wrapper.appendChild(this.contentArea);

      if (this.container) this.container.appendChild(this.wrapper);
    }

    _addTabInternal(tabOpts) {
      const id = tabOpts.id != null ? String(tabOpts.id)
        : ("tab-" + this._instanceId + "-" + (this._tabs.length + 1));
      const tab = {
        id: id,
        label: tabOpts.label || id,
        badge: tabOpts.badge != null ? tabOpts.badge : null,
        contentEl: tabOpts.content || document.createElement("div"),
      };
      tab.contentEl.classList.add("erp-pagecontrol-tab-content");
      tab.contentEl.setAttribute("role", "tabpanel");
      tab.contentEl.setAttribute("data-tab-id", id);
      tab.contentEl.hidden = true;
      this._tabs.push(tab);
      this.contentArea.appendChild(tab.contentEl);
      this._renderTabsBar();
    }

    _renderTabsBar() {
      this.tabsBar.innerHTML = "";
      this._tabs.forEach(tab => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "erp-pagecontrol-tab";
        btn.setAttribute("role", "tab");
        btn.setAttribute("data-tab-id", tab.id);
        if (tab.id === this._activeId) {
          btn.classList.add("active");
          btn.setAttribute("aria-selected", "true");
        } else {
          btn.setAttribute("aria-selected", "false");
        }
        // Label + optional badge
        const lbl = document.createElement("span");
        lbl.className = "erp-pagecontrol-tab-label";
        lbl.textContent = tab.label;
        btn.appendChild(lbl);
        if (tab.badge != null && tab.badge !== "") {
          const bdg = document.createElement("span");
          bdg.className = "erp-pagecontrol-tab-badge";
          bdg.textContent = String(tab.badge);
          btn.appendChild(bdg);
        }
        btn.addEventListener("click", () => this.setActive(tab.id));
        this.tabsBar.appendChild(btn);
      });
    }

    // ── Public API ───────────────────────────────────────────────

    addTab(opts) {
      this._addTabInternal(opts || {});
      // Pokud žádný active, set first tab as active
      if (!this._activeId && this._tabs.length === 1) {
        this.setActive(this._tabs[0].id);
      }
    }

    removeTab(id) {
      const idx = this._tabs.findIndex(t => t.id === String(id));
      if (idx < 0) return false;
      const tab = this._tabs[idx];
      this._tabs.splice(idx, 1);
      if (tab.contentEl && tab.contentEl.parentNode) {
        tab.contentEl.parentNode.removeChild(tab.contentEl);
      }
      // Pokud byl active, switch na sousední
      if (this._activeId === tab.id) {
        const next = this._tabs[idx] || this._tabs[idx - 1] || null;
        this._activeId = null;
        if (next) this.setActive(next.id);
      }
      this._renderTabsBar();
      return true;
    }

    setActive(id) {
      const targetId = String(id);
      const tab = this._tabs.find(t => t.id === targetId);
      if (!tab) return false;
      const oldId = this._activeId;
      if (oldId === targetId) return true;
      // Hide current, show new
      this._tabs.forEach(t => {
        t.contentEl.hidden = (t.id !== targetId);
      });
      this._activeId = targetId;
      this._renderTabsBar();
      // Notify (pokud někteří child komponenty potřebují resize hook —
      // ErpRichEdit s Ace měl by .resize() po visibility change)
      this._notifyChildrenVisible(tab);
      if (typeof this.options.onChange === "function") {
        try { this.options.onChange(targetId, oldId); } catch (e) {}
      }
      return true;
    }

    /**
     * Po switch tabu — child elements typu Ace Editor potřebují resize()
     * protože během display:none nemají pravdivé dimensions. Heuristic:
     * jdi přes contentEl, zavolej .resize() na elementech které mají
     * `__erpResize` callback (volitelně připnutý při instantiation).
     */
    _notifyChildrenVisible(tab) {
      if (!tab || !tab.contentEl) return;
      const candidates = tab.contentEl.querySelectorAll("[data-erp-resize-hook]");
      candidates.forEach(el => {
        if (typeof el.__erpResize === "function") {
          try { el.__erpResize(); } catch (e) {}
        }
      });
    }

    activeId() {
      return this._activeId;
    }

    getTab(id) {
      const tab = this._tabs.find(t => t.id === String(id));
      if (!tab) return null;
      return { id: tab.id, label: tab.label, contentEl: tab.contentEl };
    }

    /**
     * Vrať contentEl aktivního tabu — pro caller který chce přidávat
     * children do aktivního panelu post-init.
     */
    getActiveContent() {
      const tab = this._tabs.find(t => t.id === this._activeId);
      return tab ? tab.contentEl : null;
    }

    /**
     * Vrať contentEl tabu podle id — pro caller který chce naplnit
     * konkrétní tab post-init (typicky ErpForm orchestrator iteruje přes
     * komponenty s c_parent="t<id>" a appendá je do správného TabSheet
     * contentEl).
     */
    getTabContent(id) {
      const tab = this._tabs.find(t => t.id === String(id));
      return tab ? tab.contentEl : null;
    }

    setBadge(id, badge) {
      const tab = this._tabs.find(t => t.id === String(id));
      if (!tab) return;
      tab.badge = badge;
      this._renderTabsBar();
    }

    /** UI Kit pattern — vrací wrapper element (pro ErpFormSection.addField()
     *  nebo ErpForm dispatch loop). */
    wrapperElement() { return this.wrapper; }

    destroy() {
      if (this._destroyed) return;
      this._destroyed = true;
      this._tabs = [];
      if (this.wrapper && this.wrapper.parentNode) {
        this.wrapper.parentNode.removeChild(this.wrapper);
      }
    }
  }

  global.ErpPageControl = ErpPageControl;

  }); // _erpLoadModule end
})(typeof window !== "undefined" ? window : globalThis);
