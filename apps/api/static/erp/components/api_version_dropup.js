/* =====================================================================
 * Phase API Versioned Routing - Etapa D
 * UI footer dropup + version badge.
 *
 * Co dela:
 *   - Renderuje pill "V1.3.25 ▴" v patičce (id="erpFooterApiVersion")
 *   - Click → dropup menu s vsem aktivnima versionma
 *   - Color severity: current (no color) / previous (yellow) / older (red) / older_2+ (red flashed)
 *   - Date format: current "DD.M. HH:MM" / others "DD.M."
 *   - Per-row click → pin via POST /pin (with optional reason confirm dialog)
 *   - Active pin → highlighted row + "AKTUÁLNÍ" label
 *   - Bottom: "🔍 Co je nového? (diff)" button
 *
 * Doctrine alignment:
 *   - "Drz jednoduchost" - vanilla JS, no framework
 *   - "Bezpecnost pres probuzeni" - all errors → console.error + visible UI feedback
 *   - "Není to omezení, je to pojistka" - confirm dialog pro pin, ne silent set
 * =====================================================================
 */

(function (global) {
  "use strict";

  const POLL_INTERVAL_MS = 60_000; // refresh badge every 60s (catch expirations + promotions)
  const ENDPOINT_LIST = "/api/v1/erp/api-versions";
  const ENDPOINT_PIN = "/api/v1/erp/api-versions/pin";
  const ENDPOINT_UNPIN = "/api/v1/erp/api-versions/unpin";
  const ENDPOINT_DIFF = "/api/v1/erp/api-versions/diff";

  // State
  let _state = {
    versions: [],
    currentPin: null,
    dropupOpen: false,
    polling: null,
  };

  // ---------------------------------------------------------------------
  // Date formatters
  // ---------------------------------------------------------------------

  function _fmtDateShort(isoStr) {
    if (!isoStr) return "";
    try {
      const d = new Date(isoStr);
      return `${d.getDate()}.${d.getMonth() + 1}.`;
    } catch {
      return "";
    }
  }

  function _fmtDateTime(isoStr) {
    if (!isoStr) return "";
    try {
      const d = new Date(isoStr);
      const dStr = `${d.getDate()}.${d.getMonth() + 1}.`;
      const hh = String(d.getHours()).padStart(2, "0");
      const mm = String(d.getMinutes()).padStart(2, "0");
      return `${dStr} ${hh}:${mm}`;
    } catch {
      return "";
    }
  }

  function _fmtVersionForPill(v) {
    // current → "V1.3.25 · 23.5. 15:33"
    // older → "V1.3.24 · 23.5."
    if (v.severity === "current") {
      return `${v.version_string} · ${_fmtDateTime(v.released_at)}`;
    }
    return `${v.version_string} · ${_fmtDateShort(v.released_at)}`;
  }

  // ---------------------------------------------------------------------
  // API calls
  // ---------------------------------------------------------------------

  async function _fetchVersions() {
    try {
      const res = await fetch(ENDPOINT_LIST, { credentials: "include" });
      if (!res.ok) {
        console.warn("[api-version-dropup] list failed:", res.status);
        return null;
      }
      return await res.json();
    } catch (e) {
      console.warn("[api-version-dropup] list error:", e);
      return null;
    }
  }

  // Skutečná instance, která request reálně obsloužila. Jde stejnou cookie
  // routing cestou jako ostatní volání → při failoveru (pin na vypnutou B)
  // poctivě vrátí "primary". Marti 14.6.: ať pill nekecá B, když běží A.
  async function _fetchApiInfo() {
    try {
      const res = await fetch("/api/v1/api-info", { credentials: "include", cache: "no-store" });
      if (!res.ok) return null;
      return await res.json();
    } catch (e) {
      return null;
    }
  }

  async function _pinVersion(versionCode, reason) {
    const body = { version_code: versionCode };
    if (reason && reason.trim()) body.reason = reason.trim();
    try {
      const res = await fetch(ENDPOINT_PIN, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const txt = await res.text();
        throw new Error(`pin failed (${res.status}): ${txt}`);
      }
      return await res.json();
    } catch (e) {
      console.error("[api-version-dropup] pin error:", e);
      alert(`Chyba při přepnutí verze: ${e.message}`);
      return null;
    }
  }

  async function _unpinVersion() {
    try {
      const res = await fetch(ENDPOINT_UNPIN, {
        method: "POST",
        credentials: "include",
      });
      if (!res.ok) {
        const txt = await res.text();
        throw new Error(`unpin failed (${res.status}): ${txt}`);
      }
      return await res.json();
    } catch (e) {
      console.error("[api-version-dropup] unpin error:", e);
      alert(`Chyba při návratu na aktuální verzi: ${e.message}`);
      return null;
    }
  }

  async function _fetchDiff(fromCode, toCode) {
    try {
      const url = `${ENDPOINT_DIFF}?from_code=${encodeURIComponent(fromCode)}&to_code=${encodeURIComponent(toCode)}`;
      const res = await fetch(url, { credentials: "include" });
      if (!res.ok) {
        const txt = await res.text();
        throw new Error(`diff failed (${res.status}): ${txt}`);
      }
      return await res.json();
    } catch (e) {
      console.error("[api-version-dropup] diff error:", e);
      alert(`Chyba při získání diff: ${e.message}`);
      return null;
    }
  }

  // ---------------------------------------------------------------------
  // Render — pill (footer badge)
  // ---------------------------------------------------------------------

  function _renderPill() {
    const host = document.getElementById("erpFooterApiVersion");
    if (!host) return;

    const versions = _state.versions || [];
    const pin = _state.currentPin;
    const info = _state.apiInfo;

    const currentV = versions.find((v) => v.severity === "current");
    const pinnedV = pin ? versions.find((v) => v.version_code === pin.pinned_version_code) : null;

    // SKUTEČNÁ instance, co request obsloužila (z api-info).
    const realInst = info && info.instance ? info.instance : null; // "primary" | "secondary"
    const instTag = realInst === "secondary" ? "B" : realInst === "primary" ? "A" : "?";

    // Verze kódu, který REÁLNĚ běží: primary = current; secondary = pinnutá (starší).
    const runningV = realInst === "secondary" ? (pinnedV || currentV) : (currentV || pinnedV);
    let vStr = runningV ? runningV.version_string : "";
    if (!vStr && info && info.commit) vStr = "#" + info.commit;

    if (!runningV && !info) {
      host.innerHTML = "";
      return;
    }

    // Nesoulad: připnuto na starší verzi, ale fakticky běží primární (= záloha
    // neběží a failover tě obsloužil z A). Ať to pill řekne na rovinu.
    const pinnedNonCurrent = !!(pinnedV && pinnedV.severity !== "current");
    const mismatch = pinnedNonCurrent && realInst === "primary";

    let cls = "api-version-pill-current";
    let warn = "";
    let hint = "Běží primární A — aktuální verze (klik pro přepnutí)";
    if (realInst === "secondary") {
      cls = pinnedV ? `api-version-pill-${pinnedV.severity}` : "api-version-pill-previous";
      hint = "Běží záloha B — " + (pinnedV ? pinnedV.version_label : "previous") + " (klik pro změnu)";
    } else if (mismatch) {
      cls = "api-version-pill-previous";
      warn = " ⚠";
      hint = "Připnuto na " + pinnedV.version_label + ", ale ZÁLOHA B NEBĚŽÍ → fakticky běží primární A. Klik → vrátit na aktuální.";
    } else if (!info) {
      hint = "Verze API (skutečná instance se nenačetla)";
    }

    const label = `běží ${instTag}${warn} · ${vStr}`;

    host.innerHTML = `
      <button type="button" class="api-version-pill ${cls}"
              id="erpFooterApiVersionBtn"
              data-hint="${_escapeHtml(hint)}">
        <span class="api-version-pill-label">${_escapeHtml(label)}</span>
        <span class="api-version-pill-caret">▴</span>
      </button>
    `;

    const btn = document.getElementById("erpFooterApiVersionBtn");
    if (btn) {
      btn.addEventListener("click", _toggleDropup);
    }
  }

  // ---------------------------------------------------------------------
  // Render — dropup menu
  // ---------------------------------------------------------------------

  function _toggleDropup(event) {
    if (event) event.stopPropagation();
    if (_state.dropupOpen) {
      _closeDropup();
    } else {
      _openDropup();
    }
  }

  function _closeDropup() {
    const existing = document.getElementById("erpFooterApiVersionDropup");
    if (existing) existing.remove();
    _state.dropupOpen = false;
    document.removeEventListener("click", _onDocClick);
  }

  function _onDocClick(event) {
    const drop = document.getElementById("erpFooterApiVersionDropup");
    if (drop && !drop.contains(event.target)) {
      _closeDropup();
    }
  }

  function _openDropup() {
    _closeDropup(); // ensure clean

    const pillBtn = document.getElementById("erpFooterApiVersionBtn");
    if (!pillBtn) return;

    const versions = _state.versions || [];
    const pin = _state.currentPin;
    const activeCode = pin ? pin.pinned_version_code : "current";

    const drop = document.createElement("div");
    drop.id = "erpFooterApiVersionDropup";
    drop.className = "api-version-dropup";

    const rowsHtml = versions
      .map((v) => {
        const isActive = v.version_code === activeCode;
        const olderFlash = v.sort_order >= 3 ? " api-version-row-flashed" : "";
        const dateStr =
          v.severity === "current" ? _fmtDateTime(v.released_at) : _fmtDateShort(v.released_at);
        const activeLabel = isActive
          ? `<span class="api-version-row-active-label">AKTUÁLNÍ</span>`
          : "";
        return `
          <button type="button" class="api-version-row api-version-row-${v.severity}${olderFlash} ${isActive ? "api-version-row-active" : ""}"
                  data-version-code="${v.version_code}">
            <span class="api-version-row-label">${v.version_string}</span>
            <span class="api-version-row-date">${dateStr}</span>
            ${activeLabel}
          </button>
        `;
      })
      .join("");

    const pinReasonHtml = pin && pin.reason
      ? `<div class="api-version-pin-reason">Důvod: <em>${_escapeHtml(pin.reason)}</em></div>`
      : "";

    const _info = _state.apiInfo;
    const _realInst = _info && _info.instance ? _info.instance : null;
    const _instTag = _realInst === "secondary" ? "B (záloha)" : _realInst === "primary" ? "A (primární)" : "?";
    const _running = `<div class="api-version-pin-reason" style="border-top:1px solid rgba(255,255,255,.08);margin-top:2px">Fakticky běžíš na: <b>${_instTag}</b>${_info && _info.commit ? " · #" + _escapeHtml(_info.commit) : ""}</div>`;

    drop.innerHTML = `
      <div class="api-version-dropup-header">
        Verze API
        ${pin ? '<span class="api-version-dropup-pin-badge">PŘIPNUTO</span>' : ""}
      </div>
      ${_running}
      <div class="api-version-dropup-body">
        ${rowsHtml}
      </div>
      ${pinReasonHtml}
      <div class="api-version-dropup-footer">
        ${pin ? '<button type="button" class="api-version-unpin-btn" id="erpFooterApiVersionUnpinBtn">↩ Vrátit na aktuální</button>' : ""}
        <button type="button" class="api-version-diff-btn" id="erpFooterApiVersionDiffBtn">🔍 Co je nového? (diff)</button>
        ${_state.isParent ? `<button type="button" class="api-version-diff-btn" id="erpFooterApidBtn" style="margin-top:4px;${_isApidMode() ? 'background:#7a5;border-color:#7a5;color:#fff;' : ''}">${_isApidMode() ? '↩ Zpět na ostrý systém' : '🧪 Testovací API D (kopie dat)'}</button>` : ""}
      </div>
    `;

    document.body.appendChild(drop);

    // Position dropup above pill (anchor to pill button)
    const pillRect = pillBtn.getBoundingClientRect();
    const dropRect = drop.getBoundingClientRect();
    const bottomY = window.innerHeight - pillRect.top + 6; // 6px gap
    drop.style.bottom = `${bottomY}px`;
    drop.style.right = `${window.innerWidth - pillRect.right}px`;

    _state.dropupOpen = true;

    // Wire up row clicks
    drop.querySelectorAll(".api-version-row").forEach((row) => {
      row.addEventListener("click", (e) => {
        e.stopPropagation();
        const code = row.getAttribute("data-version-code");
        if (code === activeCode) {
          _closeDropup();
          return; // klik na aktivní řádek = no-op
        }
        _onPinClicked(code);
      });
    });

    // Unpin button
    const unpinBtn = document.getElementById("erpFooterApiVersionUnpinBtn");
    if (unpinBtn) {
      unpinBtn.addEventListener("click", async (e) => {
        e.stopPropagation();
        _closeDropup();
        await _onUnpinClicked();
      });
    }

    // Diff button
    const diffBtn = document.getElementById("erpFooterApiVersionDiffBtn");
    if (diffBtn) {
      diffBtn.addEventListener("click", async (e) => {
        e.stopPropagation();
        await _onDiffClicked();
      });
    }

    // API D switch (jen rodice)
    const apidBtn = document.getElementById("erpFooterApidBtn");
    if (apidBtn) {
      apidBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        _closeDropup();
        if (_isApidMode()) { _exitApid(); } else { _enterApid(); }
      });
    }

    // Close on outside click
    setTimeout(() => {
      document.addEventListener("click", _onDocClick);
    }, 0);
  }

  // ---------------------------------------------------------------------
  // Pin / unpin handlers (s confirm dialog)
  // ---------------------------------------------------------------------

  async function _onPinClicked(versionCode) {
    const version = _state.versions.find((v) => v.version_code === versionCode);
    if (!version) return;

    const reason = prompt(
      `Přepnout na verzi ${version.version_label} (${version.version_string})?\n\n` +
        `Volitelný důvod (např. "MD pyramida nefunguje"):`,
      ""
    );
    // Cancel button → null
    if (reason === null) {
      _closeDropup();
      return;
    }

    _closeDropup();
    const res = await _pinVersion(versionCode, reason);
    if (res) {
      // Page reload to apply new routing (cookie set, but cached resources still on old verze)
      window.location.reload();
    }
  }

  async function _onUnpinClicked() {
    const res = await _unpinVersion();
    if (res) {
      window.location.reload();
    }
  }

  async function _onDiffClicked() {
    const pin = _state.currentPin;
    const fromCode = pin ? pin.pinned_version_code : "previous";
    const toCode = "current";

    const diff = await _fetchDiff(fromCode, toCode);
    if (!diff) return;

    // Render simple modal s commit list
    _showDiffModal(diff);
  }

  // ---------------------------------------------------------------------
  // Diff modal
  // ---------------------------------------------------------------------

  function _showDiffModal(diff) {
    const existing = document.getElementById("erpApiVersionDiffModal");
    if (existing) existing.remove();

    const commitsHtml =
      diff.commits_preview && diff.commits_preview.length
        ? diff.commits_preview
            .map(
              (c) => `
            <li class="api-version-diff-commit">
              <code>${_escapeHtml(c.short_sha)}</code>
              <span class="api-version-diff-commit-date">${_escapeHtml((c.date || "").slice(0, 10))}</span>
              <span class="api-version-diff-commit-subject">${_escapeHtml(c.subject)}</span>
            </li>`
            )
            .join("")
        : "<li><em>Žádné commity mezi verzemi</em></li>";

    const statsHtml =
      diff.commits_count > 0
        ? `<div class="api-version-diff-stats">
             ${diff.commits_count} commit(s)${
            diff.files_changed != null ? ` · ${diff.files_changed} soubor(ů) změněno` : ""
          }
           </div>`
        : "";

    const ghLink = diff.github_compare_url
      ? `<a href="${diff.github_compare_url}" target="_blank" rel="noopener" class="api-version-diff-gh">
           Otevřít na GitHubu →
         </a>`
      : "";

    const modal = document.createElement("div");
    modal.id = "erpApiVersionDiffModal";
    modal.className = "api-version-diff-modal";
    modal.innerHTML = `
      <div class="api-version-diff-modal-backdrop"></div>
      <div class="api-version-diff-modal-card">
        <div class="api-version-diff-modal-header">
          <h3>Diff: ${_escapeHtml(diff.from_version.version_string)} → ${_escapeHtml(diff.to_version.version_string)}</h3>
          <button type="button" class="api-version-diff-modal-close" id="erpApiVersionDiffClose">✕</button>
        </div>
        <div class="api-version-diff-modal-body">
          ${statsHtml}
          <ul class="api-version-diff-commits">
            ${commitsHtml}
          </ul>
          ${ghLink}
        </div>
      </div>
    `;

    document.body.appendChild(modal);

    const closeBtn = document.getElementById("erpApiVersionDiffClose");
    if (closeBtn) {
      closeBtn.addEventListener("click", () => modal.remove());
    }
    modal.querySelector(".api-version-diff-modal-backdrop").addEventListener("click", () => modal.remove());
  }

  // ---------------------------------------------------------------------
  // Utils
  // ---------------------------------------------------------------------

  function _escapeHtml(str) {
    if (str == null) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  // ---------------------------------------------------------------------
  // API D (testovaci instance na data_db_test, port 8004) - jen rodice.
  // Prepnuti pres cookie strategie_env=apid (Caddy routuje VESKERY provoz
  // - statiku i /api - na 8004 = plna izolace od ostrych dat). Zpet = smazat.
  // ---------------------------------------------------------------------

  function _isApidMode() {
    return /(?:^|;\s*)strategie_env=apid(?:;|$)/.test(document.cookie || "");
  }

  async function _probeParent() {
    // deploy/preview vraci 200 jen rodicum (stejny gate jako raketa)
    try {
      const r = await fetch("/api/v1/erp/deploy/preview", { credentials: "same-origin" });
      return r.ok;
    } catch (e) {
      return false;
    }
  }

  function _enterApid() {
    const ok = confirm(
      "Prepnout na TESTOVACI prostredi API D?\n\n" +
      "- uvidis OBNOVENA testovaci data (ne ostra)\n" +
      "- zadne akce neodchazeji ven (mail / SMS / zapis do Centraly jsou vypnute)\n" +
      "- zpet na ostry system se vratis stejnym tlacitkem (nebo kliknutim na zluty pruh nahore)"
    );
    if (!ok) return;
    document.cookie = "strategie_env=apid; path=/; max-age=86400; samesite=lax";
    window.location.reload();
  }

  function _exitApid() {
    document.cookie = "strategie_env=apid; path=/; max-age=0; samesite=lax";
    window.location.reload();
  }

  function _renderApidBanner() {
    const on = _isApidMode();
    let b = document.getElementById("apidEnvBanner");
    if (!on) { if (b) b.remove(); return; }
    if (b) return;
    b = document.createElement("div");
    b.id = "apidEnvBanner";
    b.style.cssText =
      "position:fixed;top:0;left:0;right:0;z-index:2147483646;cursor:pointer;" +
      "background:repeating-linear-gradient(45deg,#b8860b,#b8860b 14px,#9c7209 14px,#9c7209 28px);" +
      "color:#fff;text-align:center;font:600 12px/1.9 system-ui,Segoe UI,sans-serif;" +
      "letter-spacing:.3px;box-shadow:0 2px 6px rgba(0,0,0,.35);";
    b.textContent = "🧪 TESTOVACÍ PROSTŘEDÍ API D — data nejsou ostrá · klikni pro návrat na ostrý systém";
    b.addEventListener("click", _exitApid);
    document.body.appendChild(b);
    document.body.style.paddingTop = "24px"; // ať banner nepřekryje obsah
  }

  // ---------------------------------------------------------------------
  // Init + polling
  // ---------------------------------------------------------------------

  async function _refresh() {
    const data = await _fetchVersions();
    if (data) {
      _state.versions = data.versions || [];
      _state.currentPin = data.current_pin || null;
    }
    _state.apiInfo = await _fetchApiInfo();
    _renderPill();
    _renderApidBanner();
  }

  function _startPolling() {
    if (_state.polling) clearInterval(_state.polling);
    _state.polling = setInterval(_refresh, POLL_INTERVAL_MS);
  }

  async function _init() {
    _state.isParent = await _probeParent();
    await _refresh();
    _startPolling();
  }

  // Boot when DOM ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", _init);
  } else {
    _init();
  }

  // Expose for debug
  global._apiVersionDropup = {
    refresh: _refresh,
    state: () => ({ ..._state }),
    close: _closeDropup,
  };
})(window);
