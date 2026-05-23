/**
 * ERP Batch Row Action — Mód 1 (Centrála 1 cyklický per-row)
 * ============================================================
 * Krok 5.X (23.5.2026) — Marti's spec:
 *   "Centrale mame dva rozdilne mody. 1. Single (cyklicky per zaznam)
 *    2. Batch array do DB najednou. Pro mne ted staci jen Mód 1."
 *   "Nejde jen o mazani, jde i o ruzne actions" (HW/FW dynamicky)
 *
 * Generic helper pro multi-row action processing:
 *   - Frontend sequential loop (Mód 1, NE backend batch array)
 *   - Per-row error tolerance (1 fail nezastaví ostatní)
 *   - Audit row per delete (Centrála 1 19yr pattern)
 *   - Reusable napříč existing actions (Smazat/Archivovat/Obnovit)
 *     + future HW/FW dynamic actions (data_source_op driven)
 *
 * Public API:
 *   await window._erpBatchRowAction({
 *     rowIds: [1748, 1747, 1745],          // array of row IDs (1+ items)
 *     opLabel: "Smazat",                    // display name (header)
 *     opVerb: "smazat",                     // lowercase pro confirm copy
 *     actionFn: async (rowId, idx, total) => {
 *       // Must return: {ok: true} | {ok: false, error: "..."}
 *       const resp = await fetch(`/api/v1/.../${rowId}`, {method: 'DELETE'});
 *       const j = await resp.json();
 *       return resp.ok && j.ok ? {ok: true} : {ok: false, error: j.error || `HTTP ${resp.status}`};
 *     },
 *     refreshFn: async () => { ... },       // optional — re-fetch grid po success
 *     destructive: true,                    // red Ano button + button order
 *   });
 *   // Returns: {success: int, failed: int, errors: [{rowId, error}]}
 *
 * Used by:
 *   - page_render.js onDelete (Krok 5.X-B, 23.5.2026)
 *   - future: Archivovat, Obnovit, custom data_source_op kinds
 *
 * Z-index: 100001 (NAD error popup, modal je active foreground)
 */
(function (global) {
  "use strict";

  const _loader = global._erpLoadModule;
  if (typeof _loader !== "function") {
    console.error("[erp_batch_action] _erpLoadModule not found — skip");
    return;
  }

  _loader("erp_batch_action.js", "v1.0.0", function () {
    // Singleton state lock — race protection
    let _inProgress = false;

    // ──────────────────────────────────────────────────────────────
    // HTML escape helper
    // ──────────────────────────────────────────────────────────────
    function _escapeHtml(s) {
      if (s == null) return "";
      return String(s)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
    }

    // ──────────────────────────────────────────────────────────────
    // Dark confirm dialog (analog Krok 14b+15-18 polish style)
    // Returns Promise<boolean> — true = Ano, false = Ne/Esc/close
    // ──────────────────────────────────────────────────────────────
    function _confirmDialog({ title, bodyHtml, btnOkLabel, btnCancelLabel, destructive }) {
      return new Promise((resolve) => {
        let resolved = false;
        const _resolve = (v) => {
          if (resolved) return;
          resolved = true;
          document.removeEventListener("keydown", _escHandler, true);
          if (backdrop && backdrop.parentNode) {
            backdrop.style.animation = "erpBatchFadeOut 0.12s ease-in";
            setTimeout(() => {
              if (backdrop.parentNode) backdrop.parentNode.removeChild(backdrop);
            }, 120);
          }
          resolve(v);
        };

        const backdrop = document.createElement("div");
        backdrop.style.cssText = [
          "position:fixed", "inset:0",
          "background:rgba(0,0,0,0.65)",
          "backdrop-filter:blur(2px)",
          "z-index:100001",
          "display:flex", "align-items:center", "justify-content:center",
          "animation:erpBatchFadeIn 0.18s ease-out",
        ].join(";");

        const dialog = document.createElement("div");
        dialog.style.cssText = [
          "background:#1a1a1a",
          `border:2px solid ${destructive ? "#c62828" : "#3a4a5a"}`,
          "border-radius:12px",
          "padding:22px 26px",
          "max-width:520px", "width:90%",
          "color:#e0e0e0",
          "font-family:system-ui, -apple-system, sans-serif",
          "box-shadow:0 12px 48px rgba(0,0,0,0.6)",
          "animation:erpBatchSlideIn 0.2s ease-out",
        ].join(";");

        const titleEl = document.createElement("div");
        titleEl.style.cssText = [
          "font-size:17px", "font-weight:700",
          `color:${destructive ? "#ff8a8a" : "#aac8ec"}`,
          "margin-bottom:12px",
        ].join(";");
        titleEl.textContent = title;

        const bodyEl = document.createElement("div");
        bodyEl.style.cssText = "font-size:14px; line-height:1.6; margin-bottom:18px; color:#cfd6dc;";
        bodyEl.innerHTML = bodyHtml;

        const btnRow = document.createElement("div");
        btnRow.style.cssText = "display:flex; gap:10px; justify-content:flex-end;";

        const btnCancel = _mkButton(btnCancelLabel || "Ne", "secondary", () => _resolve(false));
        const btnOk = _mkButton(btnOkLabel || "Ano", destructive ? "danger" : "primary", () => _resolve(true));

        // Button order: pro destructive Ano vlevo (red), Ne vpravo (default)
        // Pro non-destructive Ano vlevo (primary blue), Ne vpravo
        // Marti's pattern z A1t — Ano-left/Ne-right (both modes)
        btnRow.appendChild(btnOk);
        btnRow.appendChild(btnCancel);

        dialog.appendChild(titleEl);
        dialog.appendChild(bodyEl);
        dialog.appendChild(btnRow);
        backdrop.appendChild(dialog);

        // Esc = Ne (Marti's A1t safety)
        function _escHandler(ev) {
          if (ev.key === "Escape") {
            ev.preventDefault();
            _resolve(false);
          }
        }
        document.addEventListener("keydown", _escHandler, true);

        document.body.appendChild(backdrop);

        // Focus Ne button by default (Marti's "default Ne" doctrine z A1s)
        setTimeout(() => { try { btnCancel.focus(); } catch (e) {} }, 50);
      });
    }

    function _mkButton(text, variant, onClick) {
      const btn = document.createElement("button");
      btn.textContent = text;
      btn.type = "button";

      const variants = {
        primary: { bg: "#2563eb", hover: "#1d4ed8", color: "#fff", border: "#2563eb" },
        danger:  { bg: "#c62828", hover: "#d63838", color: "#fff", border: "#c62828" },
        secondary: { bg: "#3a3a3a", hover: "#4a4a4a", color: "#e0e0e0", border: "#555" },
      };
      const v = variants[variant] || variants.secondary;

      btn.style.cssText = [
        `background:${v.bg}`,
        `color:${v.color}`,
        `border:1px solid ${v.border}`,
        "padding:8px 18px",
        "border-radius:6px",
        "font-size:13px", "font-weight:600",
        "cursor:pointer",
        "transition:background 0.15s",
        "user-select:none",
        "min-width:80px",
      ].join(";");
      btn.addEventListener("mouseenter", () => { btn.style.background = v.hover; });
      btn.addEventListener("mouseleave", () => { btn.style.background = v.bg; });
      btn.addEventListener("click", onClick);
      return btn;
    }

    // ──────────────────────────────────────────────────────────────
    // Progress toast — sticky pill v rohu (update in-place)
    // ──────────────────────────────────────────────────────────────
    function _createProgressToast() {
      const toast = document.createElement("div");
      toast.style.cssText = [
        "position:fixed",
        "top:50px",        // pod modul health banner
        "right:8px",
        "background:rgba(20,40,60,0.95)",
        "color:#aac8ec",
        "padding:10px 16px",
        "border:1px solid #3a5a7a",
        "border-radius:8px",
        "font-size:13px", "font-weight:600",
        "font-family:system-ui, -apple-system, sans-serif",
        "z-index:100001",
        "box-shadow:0 4px 16px rgba(0,0,0,0.4)",
        "user-select:none",
        "backdrop-filter:blur(4px)",
        "animation:erpBatchFadeIn 0.15s ease-out",
      ].join(";");
      document.body.appendChild(toast);
      return {
        update(msg) { toast.innerHTML = msg; },
        close() {
          toast.style.animation = "erpBatchFadeOut 0.15s ease-in";
          setTimeout(() => { if (toast.parentNode) toast.parentNode.removeChild(toast); }, 150);
        },
      };
    }

    // ──────────────────────────────────────────────────────────────
    // Result toast — aggregate report (3 variants)
    // ──────────────────────────────────────────────────────────────
    function _showResultToast({ variant, msg, sticky }) {
      const toast = document.createElement("div");

      const variants = {
        success: { bg: "rgba(30,80,30,0.95)", color: "#a3e4a3", border: "#4a8a4a" },
        warning: { bg: "rgba(120,80,20,0.95)", color: "#ffc480", border: "#a08040" },
        error:   { bg: "rgba(120,30,30,0.95)", color: "#ff8a8a", border: "#a04040" },
      };
      const v = variants[variant] || variants.success;

      toast.style.cssText = [
        "position:fixed",
        "top:50px",
        "right:8px",
        `background:${v.bg}`,
        `color:${v.color}`,
        `border:1px solid ${v.border}`,
        "padding:10px 36px 10px 16px",
        "border-radius:8px",
        "font-size:13px", "font-weight:600",
        "font-family:system-ui, -apple-system, sans-serif",
        "z-index:100001",
        "box-shadow:0 4px 16px rgba(0,0,0,0.4)",
        "user-select:none",
        "backdrop-filter:blur(4px)",
        "animation:erpBatchSlideIn 0.18s ease-out",
        "max-width:480px",
        "cursor:pointer",
        "position:relative",
      ].join(";");

      const msgSpan = document.createElement("span");
      msgSpan.innerHTML = msg;
      toast.appendChild(msgSpan);

      const closeBtn = document.createElement("span");
      closeBtn.textContent = "✕";
      closeBtn.style.cssText = [
        "position:absolute", "right:10px", "top:50%",
        "transform:translateY(-50%)",
        "font-size:14px", "opacity:0.7",
        "cursor:pointer",
      ].join(";");
      closeBtn.addEventListener("mouseenter", () => { closeBtn.style.opacity = "1"; });
      closeBtn.addEventListener("mouseleave", () => { closeBtn.style.opacity = "0.7"; });

      const _close = () => {
        toast.style.animation = "erpBatchFadeOut 0.15s ease-in";
        setTimeout(() => { if (toast.parentNode) toast.parentNode.removeChild(toast); }, 150);
      };
      closeBtn.addEventListener("click", (ev) => { ev.stopPropagation(); _close(); });
      toast.appendChild(closeBtn);
      toast.addEventListener("click", _close);

      document.body.appendChild(toast);

      // Auto-close pro success (sticky=false), warning + error sticky default
      if (variant === "success" && !sticky) {
        setTimeout(_close, 3500);
      }
    }

    // ──────────────────────────────────────────────────────────────
    // CSS keyframes
    // ──────────────────────────────────────────────────────────────
    function _injectStyles() {
      if (document.getElementById("erp-batch-action-styles")) return;
      const style = document.createElement("style");
      style.id = "erp-batch-action-styles";
      style.textContent = `
        @keyframes erpBatchFadeIn  { from { opacity: 0; } to { opacity: 1; } }
        @keyframes erpBatchFadeOut { from { opacity: 1; } to { opacity: 0; } }
        @keyframes erpBatchSlideIn {
          from { transform: translateY(-12px); opacity: 0; }
          to   { transform: translateY(0); opacity: 1; }
        }
      `;
      document.head.appendChild(style);
    }

    // ──────────────────────────────────────────────────────────────
    // MAIN — _erpBatchRowAction
    // ──────────────────────────────────────────────────────────────
    async function _batchRowAction(opts) {
      const {
        rowIds = [],
        opLabel = "Akce",
        opVerb = opLabel.toLowerCase(),
        actionFn,
        refreshFn = null,
        destructive = false,
      } = opts || {};

      // Validation
      if (!Array.isArray(rowIds) || rowIds.length === 0) {
        console.warn("[erp_batch_action] No rowIds — abort");
        return { success: 0, failed: 0, errors: [] };
      }
      if (typeof actionFn !== "function") {
        console.error("[erp_batch_action] actionFn required");
        return { success: 0, failed: 0, errors: [] };
      }
      if (_inProgress) {
        console.warn("[erp_batch_action] Already in progress — ignoring");
        return { success: 0, failed: 0, errors: [] };
      }

      _injectStyles();

      const N = rowIds.length;

      // ── Confirm dialog ──
      const idsPreview = rowIds.slice(0, 10).map(id => `#${id}`).join(", ");
      const idsExtra = N > 10 ? ` <span style="color:#888;">a ${N - 10} dalších</span>` : "";
      const titleText = N === 1
        ? `${opLabel} 1 záznam?`
        : `${opLabel} ${N} záznamů?`;
      const bodyHtml = `
        <div style="margin-bottom:8px;">Chcete ${_escapeHtml(opVerb)} následující záznamy:</div>
        <div style="background:#0d0d0d; padding:8px 12px; border-radius:6px; font-family:monospace; font-size:12px; color:#d4d4d4;">
          ${_escapeHtml(idsPreview)}${idsExtra}
        </div>
        ${destructive ? '<div style="margin-top:10px; color:#ff8a8a; font-size:12px;">⚠ Tato akce je nevratná.</div>' : ''}
      `;

      const ok = await _confirmDialog({
        title: titleText,
        bodyHtml,
        btnOkLabel: "Ano",
        btnCancelLabel: "Ne",
        destructive,
      });

      if (!ok) {
        return { success: 0, failed: 0, errors: [], cancelled: true };
      }

      // ── State lock ──
      _inProgress = true;

      const result = { success: 0, failed: 0, errors: [] };
      const progress = _createProgressToast();

      try {
        for (let i = 0; i < N; i++) {
          const rowId = rowIds[i];
          progress.update(`🔄 ${_escapeHtml(opVerb)} ${i + 1}/${N}... (id #${_escapeHtml(rowId)})`);

          let res;
          try {
            res = await actionFn(rowId, i, N);
          } catch (e) {
            res = { ok: false, error: `JS exception: ${e && e.message ? e.message : String(e)}` };
          }

          if (res && res.ok) {
            result.success++;
          } else {
            result.failed++;
            result.errors.push({
              rowId,
              error: (res && res.error) || "Unknown failure",
            });
          }
        }
      } finally {
        progress.close();
        _inProgress = false;
      }

      // ── Refresh grid (jen pokud něco prošlo) ──
      if (result.success > 0 && typeof refreshFn === "function") {
        try {
          await refreshFn();
        } catch (e) {
          console.warn("[erp_batch_action] refreshFn failed:", e);
        }
      }

      // ── Aggregate report ──
      if (result.failed === 0) {
        // All success
        _showResultToast({
          variant: "success",
          msg: `✓ ${_escapeHtml(opLabel)}: ${result.success} ${result.success === 1 ? "záznam" : "záznamů"}`,
          sticky: false,
        });
      } else if (result.success > 0) {
        // Partial
        const errorPreview = result.errors.slice(0, 3).map(e =>
          `#${e.rowId}: ${_escapeHtml(String(e.error).slice(0, 80))}`
        ).join("<br>");
        const errorMore = result.errors.length > 3 ? `<br>...a ${result.errors.length - 3} dalších` : "";
        _showResultToast({
          variant: "warning",
          msg: `⚠ ${_escapeHtml(opLabel)}: ${result.success}/${N} OK, ${result.failed} selhalo<br>` +
               `<div style="font-size:11px; margin-top:6px; opacity:0.85;">${errorPreview}${errorMore}<br>(viz Diag log)</div>`,
          sticky: true,
        });
      } else {
        // All fail
        const errorPreview = result.errors.slice(0, 3).map(e =>
          `#${e.rowId}: ${_escapeHtml(String(e.error).slice(0, 80))}`
        ).join("<br>");
        _showResultToast({
          variant: "error",
          msg: `✗ ${_escapeHtml(opLabel)} selhalo (0/${N})<br>` +
               `<div style="font-size:11px; margin-top:6px; opacity:0.85;">${errorPreview}<br>(viz Diag log)</div>`,
          sticky: true,
        });
      }

      console.info(`[erp_batch_action] ${opLabel}: ${result.success}/${N} success, ${result.failed} failed`, result);
      return result;
    }

    // ──────────────────────────────────────────────────────────────
    // Public API
    // ──────────────────────────────────────────────────────────────
    global._erpBatchRowAction = _batchRowAction;
    global._erpBatchActionInProgress = () => _inProgress;

    console.log("[erp_batch_action] LIVE — Mód 1 (cyklický per-row)");
  });
})(window);
