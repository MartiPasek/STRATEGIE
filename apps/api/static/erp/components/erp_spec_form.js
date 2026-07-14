/* erp_spec_form.js — data-driven detail (Fáze 3b, Kristý 14.7.2026).
 *
 * Napojení na přehled: když se otevírá editace řádku a pro dané jádro existuje
 * definice ve fw.centrala_form_spec, vykreslí se MŮJ data-driven detail
 * IN-PLACE (na místo tabulky v mainContent), strom/záložky/dlaždice zůstanou
 * živé. Detail = iframe na /static/erp/proto/objednavka.html (spec + záznam +
 * živé číselníky + grid s filtrováním). Aditivní, gated: pro jádra BEZ specu se
 * nic nemění (fallback na původní DesignFwForm). Marti's komponent se to
 * nedotýká kromě malého gated hooku v erp_grid_actions.js.
 */
(function (global) {
  "use strict";
  var SPECS = null; // coreId(str) -> {ec_form_id, code, core_id}

  function jget(u) {
    return fetch(u, { credentials: "include" }).then(function (r) {
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    });
  }

  function seed() {
    return jget("/api/v1/erp/centrala-form-specs").then(function (j) {
      SPECS = {};
      (((j && j.specs) || [])).forEach(function (s) {
        if (s && s.core_id != null) SPECS[String(s.core_id)] = s;
      });
      try { console.info("[ErpSpecForm] seed cores:", Object.keys(SPECS)); } catch (e) {}
      return SPECS;
    }).catch(function (e) {
      SPECS = SPECS || {};
      try { console.warn("[ErpSpecForm] seed failed", e); } catch (_) {}
    });
  }

  function hasCore(coreId) { return !!(SPECS && SPECS[String(coreId)]); }

  function _mainContent() {
    // mainContent = rodič viditelného grid hostu přehledu (erp-page-grid-<coreId>)
    var hosts = document.querySelectorAll('[id^="erp-page-grid-"]');
    for (var i = 0; i < hosts.length; i++) {
      if (hosts[i].offsetParent !== null) return hosts[i].parentNode;
    }
    return hosts.length ? hosts[hosts.length - 1].parentNode : null;
  }

  function tryOpen(opts) {
    opts = opts || {};
    if (!hasCore(opts.coreId)) return false;
    var meta = SPECS[String(opts.coreId)];
    var main = _mainContent();
    if (!main) return false; // necháme fallback na původní formulář
    var rowId = (opts.rowId != null ? opts.rowId : "");

    var prev = [].slice.call(main.children);
    prev.forEach(function (n) { n.__esfDisp = n.style.display; n.style.display = "none"; });

    if (getComputedStyle(main).position === "static") {
      main.__esfPos = ""; main.style.position = "relative";
    }

    var box = document.createElement("div");
    box.setAttribute("data-esf", "1");
    box.style.cssText = "position:absolute;inset:0;display:flex;flex-direction:column;background:#0e1320;z-index:5;";

    var bar = document.createElement("div");
    bar.style.cssText = "flex:0 0 auto;display:flex;align-items:center;gap:12px;padding:8px 14px;background:#151b2a;border-bottom:1px solid #273049;font:600 13px -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;";
    var back = document.createElement("span");
    back.textContent = "← Zpět na seznam";
    back.style.cssText = "cursor:pointer;color:#7d95ff;";
    var lbl = document.createElement("span");
    lbl.textContent = (meta.code || "detail") + (rowId ? (" · #" + rowId) : "");
    lbl.style.color = "#93a0bc";
    bar.appendChild(back); bar.appendChild(lbl);

    var frame = document.createElement("iframe");
    frame.style.cssText = "flex:1 1 auto;width:100%;border:0;background:#0e1320;";
    frame.src = "/static/erp/proto/objednavka.html?ecFormId=" + encodeURIComponent(meta.ec_form_id) +
      "&coreId=" + encodeURIComponent(opts.coreId) + "&rowId=" + encodeURIComponent(rowId);

    box.appendChild(bar); box.appendChild(frame);
    main.appendChild(box);

    function close() {
      if (box.parentNode) box.parentNode.removeChild(box);
      prev.forEach(function (n) { n.style.display = (n.__esfDisp || ""); });
      if (main.__esfPos !== undefined) { main.style.position = main.__esfPos; delete main.__esfPos; }
      if (typeof opts.onClose === "function") { try { opts.onClose(); } catch (e) {} }
    }
    back.addEventListener("click", close);
    return true;
  }

  global.ErpSpecForm = { seed: seed, hasCore: hasCore, tryOpen: tryOpen };
  if (document.readyState !== "loading") seed();
  else document.addEventListener("DOMContentLoaded", seed);
})(window);
