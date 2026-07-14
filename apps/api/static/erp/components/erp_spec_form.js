/* erp_spec_form.js — data-driven detail (Faze 3b, Kristy 14.7.2026).
 * Klik na radek prehledu s definici ve fw.centrala_form_spec -> vykresli
 * data-driven detail IN-PLACE (na misto tabulky), primo do stranky (bez iframe).
 * Aditivni, gated: pro jadra bez specu fallback na DesignFwForm.
 */
(function (global) {
  "use strict";
  var SPECS = null, SPEC_CACHE = {}, RECORD = {}, LOOKCACHE = {};

  function jget(u) {
    return fetch(u, { credentials: "include" }).then(function (r) {
      if (!r.ok) throw new Error("HTTP " + r.status + " · " + u);
      return r.json();
    });
  }
  function seed() {
    return jget("/api/v1/erp/centrala-form-specs").then(function (j) {
      SPECS = {};
      (((j && j.specs) || [])).forEach(function (s) { if (s && s.core_id != null) SPECS[String(s.core_id)] = s; });
      try { console.info("[ErpSpecForm] seed cores:", Object.keys(SPECS)); } catch (e) {}
      return SPECS;
    }).catch(function (e) { SPECS = SPECS || {}; try { console.warn("[ErpSpecForm] seed failed", e); } catch (_) {} });
  }
  function hasCore(coreId) { return !!(SPECS && SPECS[String(coreId)]); }

  function _mainContent() {
    var hosts = document.querySelectorAll('[id^="erp-page-grid-"]');
    for (var i = 0; i < hosts.length; i++) if (hosts[i].offsetParent !== null) return hosts[i].parentNode;
    return hosts.length ? hosts[hosts.length - 1].parentNode : null;
  }

  var CSS = ""
    + ".esf-root{position:absolute;inset:0;display:flex;flex-direction:column;background:#0e1320;color:#e8ecf6;font:14px/1.45 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;z-index:5;}"
    + ".esf-bar{flex:0 0 auto;display:flex;align-items:center;gap:12px;padding:9px 14px;background:#151b2a;border-bottom:1px solid #273049;font-weight:600;font-size:13px;}"
    + ".esf-back{cursor:pointer;color:#7d95ff;}.esf-bar .m{color:#93a0bc;font-weight:500;}"
    + ".esf-scroll{flex:1 1 auto;overflow:auto;padding:16px 18px;}"
    + ".esf-status{font-size:12.5px;padding:9px 13px;border-radius:10px;margin-bottom:14px;border:1px solid #284067;background:#141d33;color:#93a0bc;}"
    + ".esf-status.err{border-color:#ff6b6b;color:#ff9a9a;}"
    + ".esf-card{background:#151b2a;border:1px solid #273049;border-radius:12px;margin-bottom:16px;overflow:hidden;}"
    + ".esf-ch{padding:12px 18px;border-bottom:1px solid #1e2639;font-weight:680;}.esf-ch .s{font-weight:500;color:#93a0bc;font-size:12.5px;}"
    + ".esf-cb{padding:16px 18px;}"
    + ".esf-fields{display:grid;grid-template-columns:repeat(3,1fr);gap:13px 20px;}"
    + ".esf-f{display:flex;flex-direction:column;gap:5px;min-width:0;}.esf-f.s2{grid-column:span 2;}"
    + ".esf-f label{font-size:12px;color:#93a0bc;font-weight:600;}"
    + ".esf-ctrl{border:1px solid #273049;border-radius:9px;padding:8px 11px;background:#111726;font-size:14px;color:#e8ecf6;min-height:37px;display:flex;align-items:center;gap:8px;}"
    + ".esf-ctrl input,.esf-ctrl select,.esf-ctrl textarea{border:0;outline:0;background:transparent;width:100%;font:inherit;color:inherit;}"
    + ".esf-ctrl textarea{resize:vertical;min-height:52px;}.esf-ctrl select{cursor:pointer;}"
    + ".esf-tag{font-size:10.5px;color:#7d95ff;background:#1e2743;border-radius:6px;padding:2px 7px;font-weight:700;white-space:nowrap;flex:none;}"
    + ".esf-tag.f{color:#e6b25a;background:transparent;border:1px solid #284067;}"
    + ".esf-chk{display:flex;align-items:center;gap:9px;}.esf-chk input{width:18px;height:18px;accent-color:#7d95ff;}"
    + ".esf-sect{grid-column:span 3;color:#93a0bc;font-weight:700;font-size:11px;letter-spacing:.05em;text-transform:uppercase;border-bottom:1px solid #1e2639;padding-bottom:5px;margin-top:4px;}"
    + ".esf-tabs{display:flex;gap:2px;border-bottom:1px solid #273049;padding:0 6px;}"
    + ".esf-tab{padding:11px 15px;font-weight:640;color:#93a0bc;cursor:pointer;border-bottom:2px solid transparent;font-size:13.5px;}"
    + ".esf-tab.a{color:#7d95ff;border-bottom-color:#7d95ff;}"
    + ".esf-tab .n{background:#212a42;border-radius:999px;font-size:11px;padding:1px 7px;margin-left:6px;}"
    + ".esf-pane{display:none;padding:16px 18px;}.esf-pane.a{display:block;}"
    + ".esf-root table{width:100%;border-collapse:collapse;font-size:13px;}"
    + ".esf-root thead th{background:#171f30;text-align:left;font-size:11px;color:#93a0bc;font-weight:700;text-transform:uppercase;padding:8px 10px;border-bottom:1px solid #273049;white-space:nowrap;}"
    + ".esf-root thead th.fil{padding:5px 8px;text-transform:none;}"
    + ".esf-root thead input{width:100%;border:1px solid #273049;border-radius:6px;padding:4px 7px;background:#111726;color:#e8ecf6;font-size:12px;}"
    + ".esf-root tbody td{padding:8px 10px;border-bottom:1px solid #1e2639;white-space:nowrap;}"
    + ".esf-root tbody tr:hover{background:#1a2135;}"
    + ".esf-root th.num,.esf-root td.num{text-align:right;}"
    + ".esf-empty{color:#93a0bc;font-size:13px;padding:8px 2px;}"
    + ".esf-drop{border:1.5px dashed #313d5c;border-radius:12px;padding:22px;text-align:center;color:#93a0bc;background:#121a2b;}"
    + ".esf-path{font-size:11.5px;color:#93a0bc;margin-top:12px;background:#212a42;border-radius:8px;padding:8px 11px;display:inline-block;font-family:ui-monospace,monospace;}";

  function injectCss() {
    if (document.getElementById("esf-css")) return;
    var st = document.createElement("style"); st.id = "esf-css"; st.textContent = CSS;
    document.head.appendChild(st);
  }
  function el(tag, cls, html) { var e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; }
  function ciResolve(o, w) { if (!o || w == null) return w; if (w in o) return w; var wl = String(w).toLowerCase(); for (var k in o) if (k.toLowerCase() === wl) return k; return w; }
  function getVal(name) { var k = ciResolve(RECORD, name); var v = RECORD[k]; return v == null ? "" : v; }

  var GRID_COLS = [
    { k: "Poradi", t: "#", num: true }, { k: "RegCis", t: "Reg. cislo" }, { k: "Nazev1", t: "Nazev" },
    { k: "Mnozstvi", t: "Mnozstvi", num: true }, { k: "MJ", t: "MJ" }, { k: "JCbezDaniKC", t: "JC bez DPH", num: true },
    { k: "SlevaZboKmen", t: "Sleva %", num: true }, { k: "CCbezDaniKC", t: "Celkem bez DPH", num: true },
    { k: "SazbaDPH", t: "DPH", num: true }, { k: "CisloZakazky", t: "Zakazka" }, { k: "PotvrzDatDod", t: "Potvrz. termin" }, { k: "Dodano", t: "Dodano" }
  ];

  function fetchLookup(f) {
    var lk = f.lookup; if (!lk || !lk.source_code) return Promise.resolve([]);
    var url = "/api/v1/erp/data/" + encodeURIComponent(lk.source_code) + "?limit=1000";
    if (lk.filter && lk.filter.param) { var fv = getVal(lk.filter.field); if (fv !== "") url += "&" + encodeURIComponent(lk.filter.param) + "=" + encodeURIComponent(fv); }
    if (LOOKCACHE[url]) return Promise.resolve(LOOKCACHE[url]);
    return jget(url).then(function (j) { var rows = (j && j.rows) || []; LOOKCACHE[url] = rows; return rows; }).catch(function () { return []; });
  }

  function renderField(f) {
    if (f.type === "label") return el("div", "esf-sect", f.caption || f.name);
    var wrap = el("div", "esf-f" + (f.type === "memo" ? " s2" : ""));
    if (f.type === "checkbox") { var row = el("div", "esf-chk"); var cb = el("input"); cb.type = "checkbox"; var v = getVal(f.name); cb.checked = (v === true || v === 1 || v === "1" || v === "t" || v === "true"); row.appendChild(cb); row.appendChild(el("label", null, f.caption || f.name)); wrap.appendChild(row); return wrap; }
    wrap.appendChild(el("label", null, f.caption || f.name));
    var val = getVal(f.name);
    if (f.type === "lookup") {
      var c = el("div", "esf-ctrl"); var sel = el("select"); sel.appendChild(el("option", null, "—")); c.appendChild(sel);
      var badge = el("span"); badge.style.cssText = "display:flex;gap:6px;flex:none;";
      if (f.lookup) { badge.appendChild(el("span", "esf-tag", f.lookup.source_code)); if (f.lookup.filter) badge.appendChild(el("span", "esf-tag f", "filtr " + f.lookup.filter.param)); }
      else badge.appendChild(el("span", "esf-tag f", "ciselnik nenastaven"));
      c.appendChild(badge); wrap.appendChild(c);
      if (f.lookup) fetchLookup(f).then(function (rows) {
        var idf = f.lookup.id_field, df = f.lookup.display_field;
        sel.innerHTML = ""; sel.appendChild(el("option", null, "—"));
        rows.forEach(function (r) { var o = el("option"); var iv = r[ciResolve(r, idf)]; o.value = iv != null ? String(iv) : ""; var dv = r[ciResolve(r, df)]; o.textContent = dv != null ? String(dv) : o.value; sel.appendChild(o); });
        if (val !== "") sel.value = String(val);
        if (sel.selectedIndex <= 0 && val !== "") { var o2 = el("option"); o2.value = String(val); o2.textContent = String(val); o2.selected = true; sel.appendChild(o2); }
      });
      return wrap;
    }
    if (f.type === "memo") { var cm = el("div", "esf-ctrl"); var t = el("textarea"); t.value = val; cm.appendChild(t); wrap.appendChild(cm); return wrap; }
    if (f.type === "file") { var cf = el("div", "esf-ctrl"); cf.innerHTML = '<span style="color:#93a0bc">soubory: ' + (f.caption || f.name) + '</span>'; wrap.appendChild(cf); return wrap; }
    var ct = el("div", "esf-ctrl"); var i = el("input"); i.type = "text"; i.value = val; ct.appendChild(i); wrap.appendChild(ct); return wrap;
  }
  function fieldsGrid(list) { var g = el("div", "esf-fields"); list.slice().sort(function (a, b) { return (a.order || 0) - (b.order || 0); }).forEach(function (f) { g.appendChild(renderField(f)); }); return g; }

  function renderGrid(gr, pane, rowId) {
    var card = el("div", "esf-card");
    card.appendChild(el("div", "esf-ch", 'Polozky <span class="s">— ' + gr.source_code + ' · filtr ' + gr.filter_field + ' <- hlavicka · zive z DB_EC</span>'));
    var b = el("div", "esf-cb"); var host = el("div", "esf-empty", "Nacitam polozky…"); b.appendChild(host); card.appendChild(b); pane.appendChild(card);
    jget("/api/v1/erp/data/" + encodeURIComponent(gr.source_code) + "?" + encodeURIComponent(gr.filter_field) + "=" + encodeURIComponent(rowId || "")).then(function (j) {
      var rows = (j && j.rows) || [];
      host.className = ""; host.innerHTML = "";
      if (!rows.length) { host.className = "esf-empty"; host.textContent = "Zadne polozky pro tento doklad."; return; }
      b.insertBefore(el("div", null, '<div style="color:#93a0bc;font-size:12px;margin-bottom:8px">Nacteno ' + rows.length + ' polozek · pod hlavickami je filtr</div>'), host);
      var wrapT = el("div"); wrapT.style.overflowX = "auto";
      var html = '<table><thead><tr>';
      GRID_COLS.forEach(function (c) { html += '<th' + (c.num ? ' class="num"' : '') + '>' + c.t + '</th>'; });
      html += '</tr><tr>';
      GRID_COLS.forEach(function (c, i) { html += '<th class="fil"><input data-col="' + i + '" placeholder="filtr…"></th>'; });
      html += '</tr></thead><tbody></tbody></table>';
      wrapT.innerHTML = html; host.appendChild(wrapT);
      var tb = wrapT.querySelector("tbody");
      function draw(ff) {
        tb.innerHTML = ""; ff = (ff || []).map(function (x) { return x.toLowerCase(); });
        rows.forEach(function (r) {
          var cells = GRID_COLS.map(function (c) { var v = r[ciResolve(r, c.k)]; return v == null ? "" : String(v); });
          for (var i = 0; i < ff.length; i++) { if (ff[i] && cells[i].toLowerCase().indexOf(ff[i]) < 0) return; }
          var tr = el("tr"); cells.forEach(function (v, i) { var td = el("td", GRID_COLS[i].num ? "num" : null); td.textContent = v; tr.appendChild(td); }); tb.appendChild(tr);
        });
      }
      draw();
      var inputs = [].slice.call(wrapT.querySelectorAll("thead input"));
      inputs.forEach(function (inp) { inp.addEventListener("input", function () { draw(inputs.map(function (x) { return x.value.trim(); })); }); });
    }).catch(function (e) { host.className = "esf-empty"; host.textContent = "Polozky se nepodarilo nacist: " + e.message; });
  }

  function renderFiles(pane) {
    var card = el("div", "esf-card"); card.appendChild(el("div", "esf-ch", "Adresare & soubory"));
    var b = el("div", "esf-cb"); b.innerHTML = '<div class="esf-drop">Pretahni soubory sem, nebo <b>klikni pro vyber</b></div><div class="esf-path">Adresar Centraly (dle filelistbox.Directory) — doplni se z definice</div>';
    card.appendChild(b); pane.appendChild(card);
  }

  function renderForm(scroll, spec, rowId) {
    var header = spec.fields.filter(function (f) { return !f.tab && f.type !== "grid"; });
    if (header.length) { var card = el("div", "esf-card"); card.appendChild(el("div", "esf-ch", 'Hlavicka <span class="s">— ' + header.length + ' poli z definice</span>')); var bb = el("div", "esf-cb"); bb.appendChild(fieldsGrid(header)); card.appendChild(bb); scroll.appendChild(card); }
    var tabCard = el("div", "esf-card"); var tabbar = el("div", "esf-tabs"); var panesWrap = el("div");
    (spec.tabs || []).forEach(function (t, idx) {
      var tf = spec.fields.filter(function (f) { return f.tab === t.label; });
      var tab = el("div", "esf-tab" + (idx === 0 ? " a" : ""), t.label + (tf.length ? ' <span class="n">' + tf.length + '</span>' : ''));
      var pane = el("div", "esf-pane" + (idx === 0 ? " a" : ""));
      tab.onclick = function () { var tabs = tabbar.children, ps = panesWrap.children; for (var i = 0; i < tabs.length; i++) tabs[i].className = "esf-tab"; for (var j = 0; j < ps.length; j++) ps[j].className = "esf-pane"; tab.className = "esf-tab a"; pane.className = "esf-pane a"; };
      tabbar.appendChild(tab);
      if (tf.length) pane.appendChild(fieldsGrid(tf)); else pane.appendChild(el("div", "esf-empty", "(V definici zatim na teto zalozce nejsou pole.)"));
      if (t.label === "Obecné" && (spec.grids || []).length) spec.grids.forEach(function (gr) { renderGrid(gr, pane, rowId); });
      if (t.label === "Adresáře") renderFiles(pane);
      panesWrap.appendChild(pane);
    });
    tabCard.appendChild(tabbar); tabCard.appendChild(panesWrap); scroll.appendChild(tabCard);
  }

  function tryOpen(opts) {
    opts = opts || {};
    if (!hasCore(opts.coreId)) return false;
    var meta = SPECS[String(opts.coreId)];
    var main = _mainContent();
    if (!main) return false;
    var rowId = (opts.rowId != null ? opts.rowId : "");
    injectCss();
    RECORD = {}; LOOKCACHE = {};
    var prev = [].slice.call(main.children);
    prev.forEach(function (n) { n.__esfDisp = n.style.display; n.style.display = "none"; });
    if (getComputedStyle(main).position === "static") { main.__esfPos = ""; main.style.position = "relative"; }
    var box = el("div", "esf-root");
    var bar = el("div", "esf-bar");
    var back = el("span", "esf-back", "← Zpet na seznam");
    bar.appendChild(back);
    bar.appendChild(el("span", "m", (meta.code || "detail") + (rowId ? (" · #" + rowId) : "")));
    var scroll = el("div", "esf-scroll");
    var status = el("div", "esf-status", "Nacitam definici a zaznam…");
    scroll.appendChild(status);
    box.appendChild(bar); box.appendChild(scroll);
    main.appendChild(box);
    function close() {
      if (box.parentNode) box.parentNode.removeChild(box);
      prev.forEach(function (n) { n.style.display = (n.__esfDisp || ""); });
      if (main.__esfPos !== undefined) { main.style.position = main.__esfPos; delete main.__esfPos; }
    }
    back.addEventListener("click", close);
    var specP = SPEC_CACHE[meta.ec_form_id]
      ? Promise.resolve(SPEC_CACHE[meta.ec_form_id])
      : jget("/api/v1/erp/centrala-form-spec/" + meta.ec_form_id).then(function (j) { if (!j.ok || !j.spec) throw new Error(j.error || "spec prazdny"); SPEC_CACHE[meta.ec_form_id] = j.spec; return j.spec; });
    specP.then(function (spec) {
      var recP = rowId
        ? jget("/api/v1/erp/fw-form/by-id/" + opts.coreId + "/" + encodeURIComponent(rowId)).then(function (rec) { return rec.data || rec.record || rec.row || (rec.spec && rec.spec.data) || {}; }).catch(function () { return {}; })
        : Promise.resolve({});
      return recP.then(function (rec) { RECORD = rec || {}; if (status.parentNode) status.parentNode.removeChild(status); renderForm(scroll, spec, rowId); });
    }).catch(function (e) { status.className = "esf-status err"; status.textContent = "Chyba: " + e.message; try { console.warn("[ErpSpecForm] render", e); } catch (_) {} });
    return true;
  }

  global.ErpSpecForm = { seed: seed, hasCore: hasCore, tryOpen: tryOpen };
  if (document.readyState !== "loading") seed(); else document.addEventListener("DOMContentLoaded", seed);
})(window);
