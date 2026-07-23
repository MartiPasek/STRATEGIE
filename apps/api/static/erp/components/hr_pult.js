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
    el.style.cssText = "background:#0f141a;padding:16px 18px;overflow:auto;flex:1 1 auto;min-height:0;";
    el.innerHTML =
      style() +
      '<div class="hrp-wrap">' +
      // 1) KPI statistiky (sloupce dle nadpisu s čísly)
      '  <div class="hrp-badges" id="hrpBadges"><div class="hrp-empty">Načítám…</div></div>' +
      // 2) blok s detailními informacemi (za těmi čísly)
      '  <div class="hrp-blocks">' +
      '    <div class="hrp-panel">' +
      '      <div class="hrp-phd"><span class="hrp-pi">🏖️</span> Mimo kancelář dnes <span class="hrp-cnt" id="hrpMimoCnt"></span></div>' +
      '      <div id="hrpMimoList"><div class="hrp-empty">Načítám…</div></div>' +
      '    </div>' +
      '    <div class="hrp-panel">' +
      '      <div class="hrp-phd"><span class="hrp-pi">🎂</span> Narozeniny a výročí <span class="hrp-cnt" id="hrpJubCnt"></span><span class="hrp-jhint">30 dní</span></div>' +
      '      <div id="hrpJubList"><div class="hrp-empty">Načítám…</div></div>' +
      '    </div>' +
      '  </div>' +
      // 2b) Noví + budoucí nástupy (živě z Centrály, Šárka 23.7.2026)
      '  <div class="hrp-panel">' +
      '    <div class="hrp-phd"><span class="hrp-pi">🆕</span> Noví a budoucí nástupy <span class="hrp-cnt" id="hrpNoviCnt"></span><span class="hrp-jhint">12 měsíců</span></div>' +
      '    <div id="hrpNoviList"><div class="hrp-empty">Načítám…</div></div>' +
      '  </div>' +
      // 3) Aktuality
      '  <div class="hrp-panel hrp-feed">' +
      '    <div class="hrp-phd"><span class="hrp-pi">📣</span> Aktuality</div>' +
      '    <div id="hrpAkt"><div class="hrp-empty">Načítám…</div></div>' +
      '  </div>' +
      // 4) Přehled dlaždic (až dole)
      '  <div class="hrp-panel">' +
      '    <div class="hrp-phd"><span class="hrp-pi">▦</span> Personalistika — přehled</div>' +
      '    <div class="hrp-grid" id="hrpGrid"></div>' +
      '  </div>' +
      '</div>';

    renderTiles(el.querySelector("#hrpGrid"));
    loadMimoPanel(el);
    loadJubilea(el);
    loadNovi(el);

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
          badge(b.novi, "Noví + budoucí nástupy", null, "hrpBadgeNovi") +
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

  function badge(n, l, act, id) {
    return '<div class="hrp-badge' + (act ? ' click' : '') + '"' +
      (act ? ' data-act="' + act + '"' : '') + '><div class="hrp-n"' + (id ? ' id="' + id + '"' : '') + '>' + (n == null ? "0" : n) +
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

  // Panel „Noví a budoucí nástupy" — živě z Centrály (Šárka 23.7.2026). Zahrnuje i
  // ještě nenastoupivší (příznak budouci) — kvůli přehledu, koho čekáme.
  function loadNovi(root) {
    var list = root.querySelector("#hrpNoviList");
    var cnt = root.querySelector("#hrpNoviCnt");
    if (!list) return;
    fetch("/api/v1/erp/app/hr/novi", { credentials: "include" })
      .then(function (r) { return r.json().catch(function () { return {}; }); })
      .then(function (d) {
        if (!d || !d.ok) {
          list.innerHTML = '<div class="hrp-empty">Nemáš oprávnění nebo chyba: ' + esc(d && d.error || "") + '</div>'; return;
        }
        var novi = d.novi || [];
        if (cnt) { cnt.textContent = "(" + novi.length + ")"; }
        var nb = document.getElementById("hrpBadgeNovi");
        if (nb) { nb.textContent = novi.length; }
        if (!novi.length) {
          list.innerHTML = '<div class="hrp-empty">Za posledních 12 měsíců žádný nový nástup.</div>'; return;
        }
        list.innerHTML = novi.map(function (p) {
          var chip = p.budouci ? '<span class="hrp-chip nastup">nastoupí</span>' : '';
          var ty = p.typ ? '<span class="hrp-ntyp">' + esc(p.typ) + '</span>' : '';
          return '<div class="hrp-mrow"><span class="hrp-mic">' + (p.budouci ? '🔜' : '🆕') + '</span>' +
            '<div><div class="hrp-mnm">' + esc(p.jmeno) + ' ' + chip + '</div>' +
            '<div class="hrp-mdv">' + ty + ' nástup ' + esc(p.nastup || '—') + '</div></div></div>';
        }).join("");
      })
      .catch(function () { list.innerHTML = '<div class="hrp-empty">✗ síť</div>'; });
  }

  // Panel „Narozeniny a výročí" = přehled gratulací a ocenění (Krok 2, Šárka 3.7.2026).
  // Významná jubilea (10/20) zvýrazněná; narozeniny lze odklepnout/přeskočit (výpovědní doba…).
  var _grat = [];
  function _stavChip(st) {
    if (st === "sent") return '<span class="hrp-chip sent">✓ odesláno</span>';
    if (st === "skipped") return '<span class="hrp-chip skip">přeskočeno</span>';
    return "";
  }
  function jubRowHtml(j, idx) {
    var badge = "";
    if (j.tier && j.tier !== "normal") {
      var bt = (j.kind === "vyroci") ? (j.roky + " LET") : (j.roky + ". NAR.");
      badge = '<span class="hrp-jbadge">' + esc(bt) + '</span>';
    }
    var za = (j.za_dni === 0) ? "dnes" : (j.za_dni === 1 ? "zítra" : ("za " + j.za_dni + " dní"));
    var st = j.stav || "pending";
    var act = "";
    if (j.kind === "narozeniny") {
      act += '<button class="hrp-abtn" data-a="preview" data-i="' + idx + '">Náhled</button>';
      if (st !== "sent") act += '<button class="hrp-abtn prim" data-a="send" data-i="' + idx + '">✉ Odeslat</button>';
      if (st === "pending") act += '<button class="hrp-abtn" data-a="skip" data-i="' + idx + '">Přeskočit</button>';
      else act += '<button class="hrp-abtn ghost" data-a="reset" data-i="' + idx + '" title="Vrátit">↺</button>';
    } else {
      act += '<span class="hrp-soon">certifikát brzy</span>';
      if (st === "pending") act += '<button class="hrp-abtn" data-a="skip" data-i="' + idx + '">Přeskočit</button>';
      else act += '<button class="hrp-abtn ghost" data-a="reset" data-i="' + idx + '" title="Vrátit">↺</button>';
    }
    return '<div class="hrp-jrow hrp-j-' + esc(j.tier || "normal") + '">' +
      '<span class="hrp-jic">' + esc(j.ikona || "•") + '</span>' +
      '<div class="hrp-jbd"><div class="hrp-jnm">' + esc(j.jmeno) + badge + ' ' + _stavChip(st) + '</div>' +
      '<div class="hrp-jsub">' + esc(j.popis) + ' · ' + esc(j.datum_cz) + ' · ' + za + '</div></div>' +
      '<div class="hrp-jact">' + act + '</div></div>';
  }
  function _gratPost(akce, j) {
    return fetch("/api/v1/erp/app/hr/gratulace/rozhodni", {
      method: "POST", credentials: "include", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ akce: akce, typ: j.kind, user_id: j.user_id, jmeno: j.jmeno, event_date: j.datum, roky: j.roky })
    }).then(function (r) { return r.json().catch(function () { return {}; }); });
  }
  function _gratAction(a, i, root) {
    var j = _grat[i]; if (!j) return;
    if (a === "preview") {
      _gratPost("preview", j).then(function (d) {
        if (d && d.ok) {
          var m = ensureModal(); m.classList.add("on");
          m.querySelector(".hrp-modal-card").classList.add("hrp-modal-wide");
          m.querySelector("#hrpModalTitle").textContent = "Náhled přání — " + j.jmeno;
          m.querySelector("#hrpModalBody").innerHTML = d.html;
        }
      });
      return;
    }
    if (a === "send" && !window.confirm("Odeslat narozeninové přání: " + j.jmeno + "?")) return;
    if (a === "skip" && !window.confirm("Přeskočit (neposílat) " + j.jmeno + "?")) return;
    _gratPost(a, j).then(function (d) {
      if (d && d.ok) { loadJubilea(root); }
      else { alert("Nepovedlo se: " + (d && d.error || "")); }
    });
  }
  function loadJubilea(root) {
    var list = root.querySelector("#hrpJubList");
    var cnt = root.querySelector("#hrpJubCnt");
    if (!list) return;
    fetch("/api/v1/erp/app/hr/gratulace?days=30", { credentials: "include" })
      .then(function (r) { return r.json().catch(function () { return {}; }); })
      .then(function (d) {
        if (!d || !d.ok) {
          list.innerHTML = '<div class="hrp-empty">Nemáš oprávnění nebo chyba: ' + esc(d && d.error || "") + '</div>';
          return;
        }
        _grat = d.polozky || [];
        if (cnt) { cnt.textContent = "(" + _grat.length + ")"; }
        if (!_grat.length) {
          list.innerHTML = '<div class="hrp-empty">V nejbližších 30 dnech žádná jubilea. 🎈</div>'; return;
        }
        list.innerHTML = _grat.map(function (j, i) { return jubRowHtml(j, i); }).join("");
        if (!list._wired) {
          list.addEventListener("click", function (ev) {
            var b = ev.target.closest ? ev.target.closest(".hrp-abtn") : null;
            if (b) { _gratAction(b.getAttribute("data-a"), parseInt(b.getAttribute("data-i"), 10), root); }
          });
          list._wired = true;
        }
      })
      .catch(function () { list.innerHTML = '<div class="hrp-empty">✗ síť</div>'; });
  }

  // Modal „Mimo kancelář dnes" — seznam jmen + důvod (Krok 1).
  function openMimo() {
    var m = ensureModal();
    m.classList.add("on");
    m.querySelector(".hrp-modal-card").classList.remove("hrp-modal-wide");
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
      '.hrp-wrap{max-width:1180px;margin:0 auto;color:#cdd6e2;font:14px/1.55 -apple-system,Segoe UI,Roboto,system-ui,sans-serif;}' +
      '.hrp-blocks{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;align-items:start;margin-bottom:12px;}' +
      '.hrp-blocks .hrp-panel{margin:0;}' +
      '#hrpMimoList,#hrpJubList,#hrpAkt,#hrpNoviList{max-height:224px;overflow:auto;}' +
      '.hrp-ntyp{display:inline-block;font-size:10.5px;font-weight:700;padding:0 7px;border-radius:20px;background:#1f2a37;color:#aac8ec;margin-right:5px;}' +
      '.hrp-chip.nastup{background:#241d0c;color:#e0a400;}' +
      '.hrp-badges{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-bottom:12px;}' +
      '.hrp-badge{background:#161c24;border:1px solid #233040;border-radius:12px;padding:9px 13px;}' +
      '.hrp-n{font-size:22px;font-weight:800;color:#e8eef5;line-height:1;}' +
      '.hrp-l{font-size:11.5px;color:#7f8ea0;margin-top:2px;}' +
      '.hrp-bar{height:3px;border-radius:3px;background:#aac8ec;width:30px;margin-top:6px;opacity:.85;}' +
      '.hrp-panel{background:#161c24;border:1px solid #233040;border-radius:12px;padding:12px 14px;margin-bottom:12px;}' +
      '.hrp-phd{display:flex;align-items:center;gap:8px;font-size:14px;font-weight:800;color:#e8eef5;margin:0 0 9px;}' +
      '.hrp-pi{width:26px;height:26px;border-radius:50%;background:#1f2a37;color:#aac8ec;display:inline-flex;align-items:center;justify-content:center;font-size:14px;}' +
      '.hrp-cnt{font-size:13px;color:#7f8ea0;font-weight:600;margin-left:2px;}' +
      '.hrp-jhint{font-size:11px;color:#5d6b7c;font-weight:500;margin-left:auto;}' +
      '.hrp-jrow{display:flex;gap:12px;align-items:center;padding:10px 12px;border-top:1px solid #1e2730;border-radius:9px;margin:2px 0;}' +
      '.hrp-jrow:first-child{border-top:0;}' +
      '.hrp-jic{flex:0 0 36px;height:36px;border-radius:9px;background:#1f2a37;display:flex;align-items:center;justify-content:center;font-size:18px;}' +
      '.hrp-jbd{flex:1;min-width:0;}' +
      '.hrp-jnm{font-weight:700;color:#e8eef5;display:flex;align-items:center;gap:8px;flex-wrap:wrap;}' +
      '.hrp-jsub{font-size:12.5px;color:#7f8ea0;margin-top:1px;}' +
      '.hrp-jbadge{font-size:10.5px;font-weight:800;letter-spacing:.3px;padding:1px 8px;border-radius:20px;background:#233040;color:#aac8ec;}' +
      '.hrp-j-major{background:#241d0c;border:1px solid #4a3a16;padding:12px;}' +
      '.hrp-j-major .hrp-jic{background:#4a3a16;}' +
      '.hrp-j-major .hrp-jnm{font-size:15px;}' +
      '.hrp-j-major .hrp-jbadge{background:#e0a400;color:#1a1206;}' +
      '.hrp-j-minor{background:#16202b;border:1px solid #24303d;padding:11px 12px;}' +
      '.hrp-j-minor .hrp-jic{background:#1f2a37;}' +
      '.hrp-j-minor .hrp-jbadge{background:#1f2a37;color:#aac8ec;}' +
      '.hrp-jact{display:flex;gap:6px;align-items:center;flex-shrink:0;flex-wrap:wrap;justify-content:flex-end;}' +
      '.hrp-abtn{font-size:12px;font-weight:600;padding:5px 10px;border-radius:8px;border:1px solid #2b3a4a;background:#1b232d;color:#cdd6e2;cursor:pointer;}' +
      '.hrp-abtn:hover{background:#232d39;}' +
      '.hrp-abtn.prim{background:#2e6f3e;border-color:#3a8a4d;color:#eafff0;}' +
      '.hrp-abtn.prim:hover{background:#357f47;}' +
      '.hrp-abtn.ghost{padding:5px 8px;color:#5d6b7c;}' +
      '.hrp-chip{font-size:10.5px;font-weight:700;padding:1px 8px;border-radius:20px;}' +
      '.hrp-chip.sent{background:#16301f;color:#7fe0a0;}' +
      '.hrp-chip.skip{background:#23262b;color:#8a94a3;}' +
      '.hrp-soon{font-size:11px;color:#5d6b7c;font-style:italic;}' +
      '.hrp-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:6px 10px;}' +
      '.hrp-tile{display:flex;gap:9px;padding:8px 8px;border-radius:9px;align-items:flex-start;}' +
      '.hrp-tile.click{cursor:pointer;}' +
      '.hrp-tile.click:hover{background:#1b232d;}' +
      '.hrp-ico{flex:0 0 30px;height:30px;border-radius:8px;background:#1f2a37;display:flex;align-items:center;justify-content:center;font-size:15px;}' +
      '.hrp-bd{flex:1;min-width:0;}' +
      '.hrp-tt{font-weight:700;color:#e8eef5;font-size:12.5px;display:flex;align-items:center;gap:6px;flex-wrap:wrap;line-height:1.25;}' +
      '.hrp-dd{font-size:11px;color:#7f8ea0;margin-top:1px;line-height:1.3;}' +
      '.hrp-tag{display:inline-block;border-radius:20px;padding:1px 9px;font-size:10.5px;font-weight:700;}' +
      '.hrp-tag.soon{background:#23262b;color:#7f8ea0;}' +
      '.hrp-tag.live{background:#16301f;color:#7fe0a0;}' +
      '.hrp-feed .hrp-row{display:flex;gap:11px;padding:10px 6px;border-top:1px solid #1e2730;font-size:13.5px;align-items:center;}' +
      '.hrp-feed .hrp-row:first-of-type{border-top:0;}' +
      '.hrp-ic{flex:0 0 30px;height:30px;border-radius:8px;background:#1f2a37;display:flex;align-items:center;justify-content:center;font-size:15px;}' +
      '.hrp-empty{padding:20px;color:#7f8ea0;text-align:center;font-style:italic;}' +
      '.hrp-badge.click{cursor:pointer;}' +
      '.hrp-modal{display:none;position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:99999;align-items:flex-start;justify-content:center;padding:56px 16px;}' +
      '.hrp-modal.on{display:flex;}' +
      '.hrp-modal-card{background:#161c24;border:1px solid #233040;border-radius:14px;max-width:520px;width:100%;box-shadow:0 20px 60px rgba(0,0,0,.5);overflow:hidden;max-height:80vh;display:flex;flex-direction:column;color:#cdd6e2;font:14px/1.55 -apple-system,Segoe UI,Roboto,system-ui,sans-serif;}' +
      '.hrp-modal-card.hrp-modal-wide{max-width:720px;max-height:90vh;}' +
      '.hrp-modal-hd{display:flex;align-items:center;justify-content:space-between;padding:14px 18px;border-bottom:1px solid #233040;font-weight:800;color:#e8eef5;}' +
      '.hrp-x{cursor:pointer;color:#7f8ea0;font-size:18px;line-height:1;}' +
      '#hrpModalBody{overflow:auto;}' +
      '.hrp-mrow{display:flex;gap:12px;align-items:center;padding:11px 18px;border-top:1px solid #1e2730;}' +
      '.hrp-mrow:first-child{border-top:0;}' +
      '.hrp-mic{flex:0 0 34px;height:34px;border-radius:9px;background:#1f2a37;display:flex;align-items:center;justify-content:center;font-size:17px;}' +
      '.hrp-mnm{font-weight:700;color:#e8eef5;}' +
      '.hrp-mdv{font-size:12.5px;color:#7f8ea0;}' +
      '</style>';
  }

  window.HrPult = { mount: mount };
})();
