/**
 * ERP Error Alert — popup dialog pro fw.diag_log open errors
 * ============================================================
 * Krok 5.W observability (23.5.2026) — Marti's catch:
 *   "errory musi byt viditelny alert on time... Popup dialog, ne pilulka"
 *
 * Doctrine "Bezpecnost pres probuzeni, ne pres ticho"
 * (Marti-AI 9.5. → Fix N 21.5. → dnes UI propagation).
 *
 * Co dělá:
 *   - Polling 60s na GET /api/v1/erp/diag-log/badge
 *   - Při error_count > acknowledgedCount (delta detected) → AUTO-OPEN modal
 *   - Modal nedismissable accidentally — vyžaduje explicit user action
 *   - Actions: [Otevřít Diag log] [Acknowledge — odložit 5 min] [Zavřít — re-show při dalším]
 *   - LocalStorage tracks last acknowledged count + snooze timestamp
 *   - Při 0 errors / snoozed → no popup
 *
 * Z-index: 100000 (NAD všema modaly, ERROR má prioritu nad všim ostatním)
 *
 * Kanárek pattern (test pipeline):
 *   Klik na broken kanárek grid → SQL execute fail → log_event() → fw.diag_log →
 *   /badge endpoint → polling detects delta → MODAL POPUP "🚨 Nová chyba"
 */
(function (global) {
  "use strict";

  const _loader = global._erpLoadModule;
  if (typeof _loader !== "function") {
    console.error("[erp_error_alert] _erpLoadModule not found — skip");
    return;
  }

  _loader("erp_error_badge.js", "v2.0.0-popup", function () {
    const POLL_INTERVAL_MS = 60000; // 60s
    const SNOOZE_DURATION_MS = 5 * 60 * 1000; // 5 min
    const LS_ACK_COUNT = "erp_error_alert_ack_count";
    const LS_SNOOZE_UNTIL = "erp_error_alert_snooze_until";

    let _pollTimer = null;
    let _lastData = null;
    let _modalOpen = false;

    // ──────────────────────────────────────────────────────────────
    // LocalStorage helpers
    // ──────────────────────────────────────────────────────────────
    function _getAckCount() {
      try {
        return parseInt(localStorage.getItem(LS_ACK_COUNT) || "0", 10);
      } catch (e) { return 0; }
    }
    function _setAckCount(n) {
      try { localStorage.setItem(LS_ACK_COUNT, String(n)); } catch (e) {}
    }
    function _getSnoozeUntil() {
      try {
        return parseInt(localStorage.getItem(LS_SNOOZE_UNTIL) || "0", 10);
      } catch (e) { return 0; }
    }
    function _setSnoozeUntil(ts) {
      try { localStorage.setItem(LS_SNOOZE_UNTIL, String(ts)); } catch (e) {}
    }
    function _isSnoozed() {
      return Date.now() < _getSnoozeUntil();
    }

    // ──────────────────────────────────────────────────────────────
    // Modal dialog
    // ──────────────────────────────────────────────────────────────
    function _openModal(data) {
      if (_modalOpen) return;
      if (!document.body) return;

      _modalOpen = true;

      const errCount = data.error_count || 0;
      const warnCount = data.warn_count || 0;
      const topModule = data.top_module || "—";
      let lastSeenStr = "—";
      if (data.last_seen) {
        try {
          const d = new Date(data.last_seen);
          lastSeenStr = d.toLocaleString("cs-CZ");
        } catch (e) {}
      }

      // Backdrop
      const backdrop = document.createElement("div");
      backdrop.id = "erpErrorAlertBackdrop";
      backdrop.style.cssText = [
        "position:fixed", "inset:0",
        "background:rgba(0,0,0,0.65)",
        "backdrop-filter:blur(2px)",
        "z-index:100000",
        "display:flex", "align-items:center", "justify-content:center",
        "animation:erpErrorAlertFadeIn 0.2s ease-out",
      ].join(";");

      // Dialog box
      const dialog = document.createElement("div");
      dialog.style.cssText = [
        "background:#1a1a1a",
        "border:2px solid #c62828",
        "border-radius:12px",
        "padding:24px 28px",
        "max-width:560px", "width:90%",
        "color:#e0e0e0",
        "font-family:system-ui, -apple-system, sans-serif",
        "box-shadow:0 12px 48px rgba(198,40,40,0.4), 0 4px 16px rgba(0,0,0,0.6)",
        "animation:erpErrorAlertSlideIn 0.25s ease-out",
      ].join(";");

      // Title
      const title = document.createElement("div");
      title.style.cssText = [
        "font-size:18px", "font-weight:700",
        "color:#ff6b6b",
        "margin-bottom:14px",
        "display:flex", "align-items:center", "gap:10px",
      ].join(";");
      title.innerHTML = `<span style="font-size:28px;">🚨</span> Nové chyby v systému`;

      // Body
      const body = document.createElement("div");
      body.style.cssText = "font-size:14px; line-height:1.6; margin-bottom:20px;";

      const rows = [];
      if (errCount > 0) {
        rows.push(`<div><strong style="color:#ff8a8a;">${errCount}</strong> otevřených <strong>errorů</strong> za posledních 24h</div>`);
      }
      if (warnCount > 0) {
        rows.push(`<div><strong style="color:#ffc480;">${warnCount}</strong> warningů</div>`);
      }
      rows.push(`<div style="margin-top:8px;color:#aaa;">Nejčastější modul: <code style="background:#2a2a2a;padding:2px 6px;border-radius:4px;color:#d4d4d4;">${_escapeHtml(topModule)}</code></div>`);
      rows.push(`<div style="color:#aaa;">Poslední výskyt: ${_escapeHtml(lastSeenStr)}</div>`);

      body.innerHTML = rows.join("");

      // Buttons row
      const buttonsRow = document.createElement("div");
      buttonsRow.style.cssText = "display:flex; gap:10px; justify-content:flex-end; flex-wrap:wrap;";

      const btnOpenDiag = _mkButton(
        "📊 Otevřít Diag log",
        "primary",
        () => {
          _setAckCount(errCount);
          _closeModal(backdrop);
          _navigateToDiagLog();
        }
      );

      const btnSnooze = _mkButton(
        "⏰ Odložit 5 min",
        "secondary",
        () => {
          _setSnoozeUntil(Date.now() + SNOOZE_DURATION_MS);
          _setAckCount(errCount);
          _closeModal(backdrop);
        }
      );

      const btnClose = _mkButton(
        "Zavřít",
        "ghost",
        () => {
          _setAckCount(errCount);
          _closeModal(backdrop);
        }
      );

      buttonsRow.appendChild(btnClose);
      buttonsRow.appendChild(btnSnooze);
      buttonsRow.appendChild(btnOpenDiag);

      dialog.appendChild(title);
      dialog.appendChild(body);
      dialog.appendChild(buttonsRow);
      backdrop.appendChild(dialog);

      // ESC key handler — same as Zavřít
      function _escHandler(ev) {
        if (ev.key === "Escape") {
          ev.preventDefault();
          _setAckCount(errCount);
          _closeModal(backdrop);
          document.removeEventListener("keydown", _escHandler, true);
        }
      }
      document.addEventListener("keydown", _escHandler, true);

      document.body.appendChild(backdrop);
    }

    function _closeModal(backdrop) {
      if (!backdrop || !backdrop.parentNode) return;
      backdrop.style.animation = "erpErrorAlertFadeOut 0.15s ease-in";
      setTimeout(() => {
        if (backdrop.parentNode) backdrop.parentNode.removeChild(backdrop);
        _modalOpen = false;
      }, 150);
    }

    function _mkButton(text, variant, onClick) {
      const btn = document.createElement("button");
      btn.textContent = text;
      btn.type = "button";

      const variants = {
        primary: {
          bg: "#c62828",
          color: "#fff",
          border: "1px solid #c62828",
          hover: "#d63838",
        },
        secondary: {
          bg: "#3a3a3a",
          color: "#e0e0e0",
          border: "1px solid #555",
          hover: "#4a4a4a",
        },
        ghost: {
          bg: "transparent",
          color: "#aaa",
          border: "1px solid #444",
          hover: "#2a2a2a",
        },
      };
      const v = variants[variant] || variants.secondary;

      btn.style.cssText = [
        `background:${v.bg}`,
        `color:${v.color}`,
        `border:${v.border}`,
        "padding:8px 16px",
        "border-radius:6px",
        "font-size:13px", "font-weight:600",
        "cursor:pointer",
        "transition:background 0.15s",
        "user-select:none",
      ].join(";");
      btn.addEventListener("mouseenter", () => { btn.style.background = v.hover; });
      btn.addEventListener("mouseleave", () => { btn.style.background = v.bg; });
      btn.addEventListener("click", onClick);
      return btn;
    }

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
    // Navigate na Diag log node v System tree
    // ──────────────────────────────────────────────────────────────
    function _navigateToDiagLog() {
      const treeNodes = document.querySelectorAll(
        '#sidebarTree [data-menu-node-id], #sidebarTree .tree-node[data-node-id]'
      );
      let targetNode = null;
      treeNodes.forEach((node) => {
        const label = (node.textContent || "").trim().toLowerCase();
        if (label.includes("diag log") || label.includes("diag_log")) {
          targetNode = node;
        }
      });

      if (targetNode) {
        targetNode.click();
      } else {
        console.warn("[erp_error_alert] Diag log node not found in tree");
        if (typeof global._erpToast === "function") {
          global._erpToast(
            "⚠ Diag log node nenalezen — otevři ručně přes System → Security → Diag log",
            "warning"
          );
        }
      }
    }

    // ──────────────────────────────────────────────────────────────
    // Polling — fetch /diag-log/badge + check delta
    // ──────────────────────────────────────────────────────────────
    async function _poll() {
      try {
        const res = await fetch("/api/v1/erp/diag-log/badge", {
          credentials: "include",
          cache: "no-store",
        });
        if (!res.ok) {
          console.warn(`[erp_error_alert] /badge HTTP ${res.status}`);
          return;
        }
        const data = await res.json();
        if (!data || data.ok !== true) {
          console.warn("[erp_error_alert] /badge returned !ok", data);
          return;
        }
        _lastData = data;
        _checkAndAlert(data);
      } catch (e) {
        console.error("[erp_error_alert] poll failed:", e);
      }
    }

    function _checkAndAlert(data) {
      const errCount = data.error_count || 0;
      const ackCount = _getAckCount();

      // No errors → reset ack baseline (next error = delta)
      if (errCount === 0) {
        if (ackCount > 0) _setAckCount(0);
        return;
      }

      // Snoozed → silent
      if (_isSnoozed()) return;

      // Delta detected — open modal
      if (errCount > ackCount) {
        console.log(`[erp_error_alert] DELTA detected: ${errCount} errors (was ${ackCount}) → OPEN modal`);
        _openModal(data);
      }
    }

    function _startPolling() {
      if (_pollTimer) return;
      // Initial fetch immediately
      _poll();
      _pollTimer = setInterval(_poll, POLL_INTERVAL_MS);
    }

    function _stopPolling() {
      if (_pollTimer) {
        clearInterval(_pollTimer);
        _pollTimer = null;
      }
    }

    // ──────────────────────────────────────────────────────────────
    // CSS keyframes
    // ──────────────────────────────────────────────────────────────
    function _injectStyles() {
      if (document.getElementById("erp-error-alert-styles")) return;
      const style = document.createElement("style");
      style.id = "erp-error-alert-styles";
      style.textContent = `
        @keyframes erpErrorAlertFadeIn {
          from { opacity: 0; }
          to   { opacity: 1; }
        }
        @keyframes erpErrorAlertFadeOut {
          from { opacity: 1; }
          to   { opacity: 0; }
        }
        @keyframes erpErrorAlertSlideIn {
          from { transform: translateY(-20px); opacity: 0; }
          to   { transform: translateY(0); opacity: 1; }
        }
      `;
      document.head.appendChild(style);
    }

    // ──────────────────────────────────────────────────────────────
    // Public API
    // ──────────────────────────────────────────────────────────────
    global._erpErrorAlert = {
      refresh: _poll,
      start: _startPolling,
      stop: _stopPolling,
      forceShow: () => {
        if (_lastData) _openModal(_lastData);
      },
      getLastData: () => _lastData,
      resetAck: () => { _setAckCount(0); _setSnoozeUntil(0); },
    };

    // ──────────────────────────────────────────────────────────────
    // Init
    // ──────────────────────────────────────────────────────────────
    function _init() {
      if (!document.body) {
        setTimeout(_init, 200);
        return;
      }
      _injectStyles();
      _startPolling();
      console.log("[erp_error_alert] LIVE — polling every 60s, modal on delta");
    }

    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", _init);
    } else {
      _init();
    }
  });
})(window);
