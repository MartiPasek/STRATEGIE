// Phase 22.5.2026 cleanup B+C diagnostic helper.
// Paste do DevTools Console (F12) → výpis stavu všech otevřených gridů.
//
// Usage: Otevři grid, kde nefunguje save/restore. Paste tento blok.
//
// Marti's expectation:
//   - layoutKey: "core_XXX" (set per grid v page_render.js line 233)
//   - currentLayoutId: id z fw.comp_grid pokud byla vybrána sestava
//   - isDirty: true po column resize/move/sort/pin
//   - listLayouts result: { shared: [...], personal: [...], effective_default: {...} | null }

(async () => {
  const grids = [];
  if (typeof window.activeErpDataGrid !== "undefined" && window.activeErpDataGrid) {
    grids.push({ key: "activeErpDataGrid", grid: window.activeErpDataGrid });
  }
  if (typeof window._sysCurrentGrid !== "undefined" && window._sysCurrentGrid) {
    grids.push({ key: "_sysCurrentGrid", grid: window._sysCurrentGrid });
  }
  // Hledej v DOM ostatní gridy (live React-like refs)
  document.querySelectorAll("[data-erp-grid-root]").forEach((el, i) => {
    if (el.__erpGridInstance) {
      grids.push({ key: "dom["+i+"]", grid: el.__erpGridInstance });
    }
  });

  if (grids.length === 0) {
    console.warn("[DIAG] Žádný aktivní ErpDataGrid nenalezen. Klikni na grid v tree (např. STRATEGIE Users).");
    return;
  }

  for (const { key, grid } of grids) {
    console.group("[DIAG] Grid: " + key);
    console.log("layoutKey:", grid.options && grid.options.layoutKey);
    console.log("autoLoadDefault:", grid.options && grid.options.autoLoadDefault);
    console.log("_currentLayoutId:", grid._currentLayoutId);
    console.log("_isDirty:", grid._isDirty);
    console.log("gridApi:", grid.gridApi ? "PRESENT" : "MISSING");
    if (grid.gridApi) {
      try {
        const colState = grid.gridApi.getColumnState();
        console.log("Current column state (" + colState.length + " cols):",
          colState.slice(0, 3).map(c => ({colId: c.colId, width: c.width, hide: c.hide, pinned: c.pinned})));
      } catch (e) {
        console.warn("getColumnState failed:", e.message);
      }
    }
    if (typeof grid.listLayouts === "function") {
      try {
        const result = await grid.listLayouts();
        console.log("listLayouts result:", result);
        if (result) {
          console.log("  shared count:", (result.shared || []).length);
          console.log("  personal count:", (result.personal || []).length);
          console.log("  effective_default:", result.effective_default || "NONE");
        } else {
          console.warn("  listLayouts returned null — coreId parse failed nebo endpoint 4xx");
        }
      } catch (e) {
        console.error("listLayouts threw:", e);
      }
    }
    console.groupEnd();
  }

  // Test PUT endpoint reachability pro current layout
  for (const { key, grid } of grids) {
    if (!grid._currentLayoutId) continue;
    console.group("[DIAG] PUT test — Grid " + key + ", layout #" + grid._currentLayoutId);
    try {
      const r = await fetch(
        "/api/v1/erp/grid-layout/item/" + grid._currentLayoutId,
        {
          method: "PUT",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            layout_json: {
              columns: grid.getCurrentColumnState(),
              formatting_rules: grid._formattingRules || [],
              heuristics_enabled: grid._heuristicsEnabled === true,
            },
          }),
        }
      );
      console.log("PUT status:", r.status);
      const body = await r.json().catch(() => null);
      console.log("PUT response body:", body);
    } catch (e) {
      console.error("PUT fetch threw:", e);
    }
    console.groupEnd();
  }

  console.info("[DIAG] DONE — pošli screenshot Console + Network tab Claude.");
})();
