/* HR — přehled personalistiky jako band v ERP (jádro s kódem hr.prehled).
 * Vzor: crm_obchodnik_pult.js (band nad gridem). Rozdíl: HR pult renderuje celý
 * Pinya-styl dashboard (KPI + dlaždice + aktuality) a je hlavním obsahem stránky,
 * takže skryje prázdný grid placeholder pod sebou. Read-only, fail-safe.
 * page_render volá jen gated hook → window.HrPult.mount. (Claude-25 / Šárka 2.7.2026) */
(function () {
  "use strict";
  var EP = "/api/v1/erp/app/hr/dashboard";

  var TILES = [
    { ic: "🏖️", t: "Mimo kancelář", d: "Kdo dnes není ve firmě (absence + home office).", st: "live", act: "mimo" },
    { ic: "🎂", t: "Narozeniny a výročí", d: "Blížící se narozeniny a výročí nástupu.", st: "live" },
    { ic: "🆕", t: "Noví + budoucí nástupy", d: "Kdo nastoupil za poslední rok a kdo teprve nastoupí.", st: "live" },
    { ic: "🧲", t: "Výběrová řízení", d: "Běžící nábor, editace, publikace (Teamio).", st: "live", go: "/recruit" },
    { ic: "👥", t: "Zaměstnanci", d: "Přehled lidí → karta 360°.", st: "soon" },
    { ic: "🔔", t: "Notifikace", d: "Konce smluv, prohlídky, propadající školení.", st: "soon" },
    { ic: "✅", t: "Úkoly", d: "HR úkoly z jednoho místa.", st: "soon" },
    { ic: "🗓️", t: "Kalendář", d: "Události + import z Outlooku (na konec).", st: "soon" }
  ];

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c];
    });
  }

  // Skryj prázdný tmavý grid placeholder pod pultem (HR přehled = jen pult).
  function hideGridHost() {
    try {
      var g = document.querySelector('[id^="erp-page-grid-"]');
      if (g) { g.style.display = "none"; }
    } catch (e) { /* fail-safe */ }
  }

  function mount(el) {
    if (!el) return;
    hideGridHost();
    el.style.cssText = "background:#f4f5f7;padding:16px 18px;overflow:auto;flex:1 1 auto;min-height:0;";
    el.innerHTML =
      style() +
      '<div class="hrp-wrap">' +
      '  <div class="hrp-badges" id="hrpBadges"><div class="hrp-empty">Načítám…</div></div>' +
      '  <div class="hrp-panel">' +
      '    <div class="hrp-phd"><span class="hrp-pi">🏖️</span> Mimo kancelář dnes <span class="hrp-cnt" id="hrpMimoCnt"></span></div>' +
      '    <div id="hrpMimoList"><div class="hrp-empty">Načítám…</div></div>' +
      '  </div>' +
      '  <div class="hrp-panel">' +
      '    <div class="hrp-phd"><span class="hrp-pi">🎂</span> Narozeniny a výročí <span class="hrp-cnt" id="hrpJubCnt"></span><span class="hrp-jhint">nejbližších 30 dní</span></div>' +
      '    <div id="hrpJubList"><div class="hrp-empty">Načítám…</div></div>' +
      '  </div>' +
      '  <div class="hrp-panel">' +
      '    <div class="hrp-phd"><span class="hrp-pi">▦</span> Personalistika — přehled</div>' +
      '    <div class="hrp-grid" id="hrpGrid"></div>' +
      '  </div>' +
      '  <div class="hrp-panel hrp-feed">' +
      '    <div class="hrp-phd"><span class="hrp-pi">📣</span> Aktuality</div>' +
      '    <div id="hrpAkt"><div class="hrp-empty">Načítám…</div></div>' +
      '  </div>' +
      '</div>';

    renderTiles(el.querySelector("#hrpGrid"));
    loadMimoPanel(el);
    loadJubilea(el);

    fetch(EP, { credentials: "include" })
      .then(function (r) { return r.json().catch(function () { return {}; }); })
      .then(function (d) {
        var bEl = el.querySelector("#hrpBadges"), aEl = el.querySelector("#hrpAkt");
        if (!d || !d.ok) {
          bEl.innerHTML = '<div class="hrp-empty">Nemáš oprávnění nebo chyba: ' + esc(d && d.error || "") + '</div>';
          aEl.innerHTML = ""; return;
        }
        var b = d.badges || {};
        bEl.innerHTML =
          badge(b.mimo, "Mimo kancelář dnes", "mimo") +
          badge(b.naroz, "Narozeniny / výročí (7 dní)") +
          badge(b.novi, "Noví (do roka)") +
          badge(b.vyberka, "Běžící výběrová řízení");
        var _mb = bEl.querySelector('[data-act="mimo"]');
        if (_mb) { _mb.onclick = openMimo; }
        var akt = d.aktuality || [];
        if (!akt.length) { aEl.innerHTML = '<div class="hrp-empty">Žádné aktuality.</div>'; return; }
        aEl.innerHTML = akt.map(function (a) {
          return '<div class="hrp-row"><span class="hrp-ic">' + esc(a.ikona || "•") + '</span><span>' + esc(a.text) + '</span></div>';
        }).join("");
      })
      .catch(function () {
        var bEl = el.querySelector("#hrpBadges");
        if (bEl) bEl.innerHTML = '<div class="hrp-empty">✗ síť</div>';
      });
  }

  function renderTiles(g) {
    if (!g) return;
    g.innerHTML = "";
    TILES.forEach(function (x) {
      var d = document.createElement("div");
      d.className = "hrp-tile" + ((x.go || x.act) ? " click" : "");
      var tag = (x.st === "live")
        ? '<span class="hrp-tag live">funkční</span>'
        : '<span class="hrp-tag soon">připravujeme</span>';
      d.innerHTML =
        '<div class="hrp-ico">' + x.ic + '</div><div class="hrp-bd">' +
        '<div class="hrp-tt">' + esc(x.t) + ' ' + tag + '</div>' +
        '<div class="hrp-dd">' + esc(x.d) + '</div></div>';
      if (x.go) { d.onclick = function () { window.open(x.go, "_blank"); }; }
      else if (x.act === "mimo") { d.onclick = openMimo; }
      g.appendChild(d);
    });
  }

  function badge(n, l, act) {
    return '<div class="hrp-badge' + (act ? ' click' : '') + '"' +
      (act ? ' data-act="' + act + '"' : '') + '><div class="hrp-n">' + (n == null ? "0" : n) +
      '</div><div class="hrp-l">' + esc(l) + '</div><div class="hrp-bar"></div></div>';
  }

  // Řádky seznamu Mimo kancelář (sdílené panel + modal).
  function mimoRowsHtml(lide) {
    return lide.map(function (p) {
      return '<div class="hrp-mrow"><span class="hrp-mic">' + esc(p.ikona || "•") +
        '</span><div><div class="hrp-mnm">' + esc(p.jmeno) + '</div><div class="hrp-mdv">' +
        esc(p.duvod) + '</div></div></div>';
    }).join("");
  }

  // Viditelný panel „Mimo kancelář dnes" přímo v přehledu (Šárka 3.7.2026 — přehled
  // pro svolávání schůzek: kdo dnes není v kanceláři, hned na očích).
  function loadMimoPanel(root) {
    var list = root.querySelector("#hrpMimoList");
    var cnt = root.querySelector("#hrpMimoCnt");
    if (!list) return;
    fetch("/api/v1/erp/app/hr/mimo", { credentials: "include" })
      .then(function (r) { return r.json().catch(function () { return {}; }); })
      .then(function (d) {
        if (!d || !d.ok) {
          list.innerHTML = '<div class="hrp-empty">Nemáš oprávnění nebo chyba: ' + esc(d && d.error || "") + '</div>';
          return;
        }
        if (cnt) { cnt.textContent = "(" + (d.pocet || 0) + ")"; }
        if (!d.lide || !d.lide.length) {
          list.innerHTML = '<div class="hrp-empty">Dnes jsou všichni v kanceláři. 🎉</div>'; return;
        }
        list.innerHTML = mimoRowsHtml(d.lide);
      })
      .catch(function () { list.innerHTML = '<div class="hrp-empty">✗ síť</div>'; });
  }

  // Panel „Narozeniny a výročí" (Krok 2, Šárka 3.7.2026) — nadcházející jubilea,
  // významná (10/20 let) zvýrazněná 🏆, ostatní kulatá ⭐.
  function jubRowHtml(j) {
    var badge = "";
    if (j.tier && j.tier !== "normal") {
      var bt = (j.kind === "vyroci") ? (j.roky + " LET") : (j.roky + ". NAR.");
      badge = '<span class="hrp-jbadge">' + esc(bt) + '</span>';
    }
    var za = (j.za_dni === 0) ? "dnes" : (j.za_dni === 1 ? "zítra" : ("za " + j.za_dni + " dní"));
    return '<div class="hrp-jrow hrp-j-' + esc(j.tier || "normal") + '">' +
      '<span class="hrp-jic">' + esc(j.ikona || "•") + '</span>' +
      '<div class="hrp-jbd"><div class="hrp-jnm">' + esc(j.jmeno) + badge + '</div>' +
      '<div class="hrp-jsub">' + esc(j.popis) + ' · ' + esc(j.datum_cz) + ' · ' + za + '</div></div></div>';
  }
  function loadJubilea(root) {
    var list = root.querySelector("#hrpJubList");
    var cnt = root.querySelector("#hrpJubCnt");
    if (!list) return;
    fetch("/api/v1/erp/app/hr/jubilea?days=30", { credentials: "include" })
      .then(function (r) { return r.json().catch(function () { return {}; }); })
      .then(function (d) {
        if (!d || !d.ok) {
          list.innerHTML = '<div class="hrp-empty">Nemáš oprávnění nebo chyba: ' + esc(d && d.error || "") + '</div>';
          return;
        }
        if (cnt) { cnt.textContent = "(" + (d.pocet || 0) + ")"; }
        if (!d.jubilea || !d.jubilea.length) {
          list.innerHTML = '<div class="hrp-empty">V nejbližších 30 dnech žádná jubilea. 🎈</div>'; return;
        }
        list.innerHTML = d.jubilea.map(jubRowHtml).join("");
      })
      .catch(function () { list.innerHTML = '<div class="hrp-empty">✗ síť</div>'; });
  }

  // Modal „Mimo kancelář dnes" — seznam jmen + důvod (Krok 1).
  function openMimo() {
    var m = ensureModal();
    m.classList.add("on");
    var body = m.querySelector("#hrpModalBody");
    var ttl = m.querySelector("#hrpModalTitle");
    body.innerHTML = '<div class="hrp-empty">Načítám…</div>';
    ttl.textContent = "🏖️ Mimo kancelář dnes";
    fetch("/api/v1/erp/app/hr/mimo", { credentials: "include" })
      .then(function (r) { return r.json().catch(function () { return {}; }); })
      .then(function (d) {
        if (!d || !d.ok) {
          body.innerHTML = '<div class="hrp-empty">Chyba: ' + esc(d && d.error || "") + '</div>'; return;
        }
        ttl.textContent = "🏖️ Mimo kancelář dnes (" + (d.pocet || 0) + ")";
        if (!d.lide || !d.lide.length) {
          body.innerHTML = '<div class="hrp-empty">Dnes jsou všichni v kanceláři. 🎉</div>'; return;
        }
        body.innerHTML = d.lide.map(function (p) {
          return '<div class="hrp-mrow"><span class="hrp-mic">' + esc(p.ikona || "•") +
            '</span><div><div class="hrp-mnm">' + esc(p.jmeno) + '</div><div class="hrp-mdv">' +
            esc(p.duvod) + '</div></div></div>';
        }).join("");
      })
      .catch(function () { body.innerHTML = '<div class="hrp-empty">✗ síť</div>'; });
  }
  function closeMimo() { var m = document.getElementById("hrpModal"); if (m) m.classList.remove("on"); }
  function ensureModal() {
    var m = document.getElementById("hrpModal");
    if (m) return m;
    m = document.createElement("div");
    m.id = "hrpModal";
    m.className = "hrp-modal";
    m.innerHTML =
      '<div class="hrp-modal-card">' +
      '<div class="hrp-modal-hd"><span id="hrpModalTitle">🏖️ Mimo kancelář dnes</span>' +
      '<span class="hrp-x">✕</span></div>' +
      '<div id="hrpModalBody"><div class="hrp-empty">Načítám…</div></div>' +
      '</div>';
    m.addEventListener("click", function (e) { if (e.target === m) closeMimo(); });
    m.querySelector(".hrp-x").addEventListener("click", closeMimo);
    document.body.appendChild(m);
    return m;
  }

  function style() {
    return '<style>' +
      '.hrp-wrap{max-width:1180px;margin:0 auto;color:#33404d;font:14px/1.55 -apple-system,Segoe UI,Roboto,system-ui,sans-serif;}' +
      '.hrp-badges{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin-bottom:16px;}' +
      '.hrp-badge{background:#fff;border:1px solid #e7eaef;border-radius:12px;padding:14px 16px;}' +
      '.hrp-n{font-size:28px;font-weight:800;color:#2b3a4a;line-height:1;}' +
      '.hrp-l{font-size:12px;color:#8a94a3;margin-top:2px;}' +
      '.hrp-bar{height:3px;border-radius:3px;background:#7cb342;width:34px;margin-top:8px;opacity:.85;}' +
      '.hrp-panel{background:#fff;border:1px solid #e7eaef;border-radius:14px;padding:18px 20px;margin-bottom:16px;}' +
      '.hrp-phd{display:flex;align-items:center;gap:9px;font-size:16px;font-weight:800;color:#2b3a4a;margin:2px 0 16px;}' +
      '.hrp-pi{width:26px;height:26px;border-radius:50%;background:#f0f4ec;color:#5f9331;display:inline-flex;align-items:center;justify-content:center;font-size:14px;}' +
      '.hrp-cnt{font-size:13px;color:#8a94a3;font-weight:600;margin-left:2px;}' +
      '.hrp-jhint{font-size:11px;color:#aab2bd;font-weight:500;margin-left:auto;}' +
      '.hrp-jrow{display:flex;gap:12px;align-items:center;padding:10px 12px;border-top:1px solid #f2f4f6;border-radius:9px;margin:2px 0;}' +
      '.hrp-jrow:first-child{border-top:0;}' +
      '.hrp-jic{flex:0 0 36px;height:36px;border-radius:9px;background:#f0f4ec;display:flex;align-items:center;justify-content:center;font-size:18px;}' +
      '.hrp-jbd{flex:1;min-width:0;}' +
      '.hrp-jnm{font-weight:700;color:#2b3a4a;display:flex;align-items:center;gap:8px;flex-wrap:wrap;}' +
      '.hrp-jsub{font-size:12.5px;color:#8a94a3;margin-top:1px;}' +
      '.hrp-jbadge{font-size:10.5px;font-weight:800;letter-spacing:.3px;padding:1px 8px;border-radius:20px;background:#eef1f4;color:#66707d;}' +
      '.hrp-j-major{background:linear-gradient(180deg,#fff7e0,#fffdf6);border:1px solid #f0d98a;padding:12px;}' +
      '.hrp-j-major .hrp-jic{background:#fbe6a0;}' +
      '.hrp-j-major .hrp-jnm{font-size:15px;}' +
      '.hrp-j-major .hrp-jbadge{background:#e0a400;color:#fff;}' +
      '.hrp-j-minor{background:#f7fafd;border:1px solid #e4ecf5;padding:11px 12px;}' +
      '.hrp-j-minor .hrp-jic{background:#e9f1fb;}' +
      '.hrp-j-minor .hrp-jbadge{background:#dbe7ff;color:#3a5a9c;}' +
      '.hrp-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:6px 26px;}' +
      '.hrp-tile{display:flex;gap:13px;padding:14px 10px;border-radius:10px;align-items:flex-start;}' +
      '.hrp-tile.click{cursor:pointer;}' +
      '.hrp-tile.click:hover{background:#fafcf7;}' +
      '.hrp-ico{flex:0 0 40px;height:40px;border-radius:10px;background:#f0f4ec;display:flex;align-items:center;justify-content:center;font-size:19px;}' +
      '.hrp-bd{flex:1;min-width:0;}' +
      '.hrp-tt{font-weight:700;color:#2b3a4a;font-size:14.5px;display:flex;align-items:center;gap:8px;flex-wrap:wrap;}' +
      '.hrp-dd{font-size:12.5px;color:#8a94a3;margin-top:2px;}' +
      '.hrp-tag{display:inline-block;border-radius:20px;padding:1px 9px;font-size:10.5px;font-weight:700;}' +
      '.hrp-tag.soon{background:#f1f3f5;color:#9aa4b1;}' +
      '.hrp-tag.live{background:#f0f4ec;color:#5f9331;}' +
      '.hrp-feed .hrp-row{display:flex;gap:11px;padding:10px 6px;border-top:1px solid #f2f4f6;font-size:13.5px;align-items:center;}' +
      '.hrp-feed .hrp-row:first-of-type{border-top:0;}' +
      '.hrp-ic{flex:0 0 30px;height:30px;border-radius:8px;background:#f0f4ec;display:flex;align-items:center;justify-content:center;font-size:15px;}' +
      '.hrp-empty{padding:20px;color:#8a94a3;text-align:center;font-style:italic;}' +
      '.hrp-badge.click{cursor:pointer;}' +
      '.hrp-modal{display:none;position:fixed;inset:0;background:rgba(20,30,50,.45);z-index:99999;align-items:flex-start;justify-content:center;padding:56px 16px;}' +
      '.hrp-modal.on{display:flex;}' +
      '.hrp-modal-card{background:#fff;border-radius:14px;max-width:520px;width:100%;box-shadow:0 20px 60px rgba(20,30,50,.25);overflow:hidden;max-height:80vh;display:flex;flex-direction:column;font:14px/1.55 -apple-system,Segoe UI,Roboto,system-ui,sans-serif;}' +
      '.hrp-modal-hd{display:flex;align-items:center;justify-content:space-between;padding:14px 18px;border-bottom:1px solid #e7eaef;font-weight:800;color:#2b3a4a;}' +
      '.hrp-x{cursor:pointer;color:#8a94a3;font-size:18px;line-height:1;}' +
      '#hrpModalBody{overflow:auto;}' +
      '.hrp-mrow{display:flex;gap:12px;align-items:center;padding:11px 18px;border-top:1px solid #f2f4f6;}' +
      '.hrp-mrow:first-child{border-top:0;}' +
      '.hrp-mic{flex:0 0 34px;height:34px;border-radius:9px;background:#f0f4ec;display:flex;align-items:center;justify-content:center;font-size:17px;}' +
      '.hrp-mnm{font-weight:700;color:#2b3a4a;}' +
      '.hrp-mdv{font-size:12.5px;color:#8a94a3;}' +
      '</style>';
  }

  window.HrPult = { mount: mount };
})();
