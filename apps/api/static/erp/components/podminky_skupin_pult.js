/* Výchozí podmínky skupin — nástěnka dlaždic místo tabulky (jádro 235).
 * Vzor: hr_pult.js (band, který si sám schová grid) + crm_obchodnik_pult.js.
 * page_render volá jen gated hook → window.PodminkySkupinPult.mount.
 *
 * ZADÁNÍ (Jirka Honomichl 24.8.2026, schválila Marti-AI msg 13558 + 13568):
 *   Jedna dlaždice = jeden řádek tenant.podminky_skupin. První je vždy „Systém",
 *   za ním skupiny ve stejném pořadí, jaké měla tabulka. Klik otevře stávající
 *   editační jádro 236, křížek řádek smaže. Dlaždice „Systém" křížek NEMÁ —
 *   plní se z ní podmínky každé nově zakládané smlouvě. Přidat lze jen skupinu,
 *   která řádek ještě nemá. Přepínač nechává tabulku dostupnou.
 *
 * POJISTKA U MAZÁNÍ: skupinové hodnoty se čtou za běhu (osobní → skupina →
 * systém), takže smazání může změnit čísla živým lidem. Před smazáním se proto
 * server dotáže na skutečný dopad a potvrzení ukáže, KOHO a JAK se to dotkne.
 *
 * Fail-safe: každá chyba jen zaloguje a nechá tabulku být (stejně jako HR pult).
 */
(function () {
  "use strict";

  var EP = "/api/v1/erp/app/hr/podminky-skupin/dlazdice";
  var EDIT_CORE_ID = 236;      // „Výchozí podmínky — řádek"
  var LS_KEY = "erp.podminky_skupin.pohled";   // zapamatovaný přepínač

  var _el = null;
  var _data = null;

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c];
    });
  }

  function gridHost() {
    try { return document.querySelector('[id^="erp-page-grid-"]'); } catch (e) { return null; }
  }

  function pohled() {
    try { return window.localStorage.getItem(LS_KEY) === "tabulka" ? "tabulka" : "dlazdice"; }
    catch (e) { return "dlazdice"; }
  }

  function setPohled(v) {
    try { window.localStorage.setItem(LS_KEY, v); } catch (e) { /* fail-safe */ }
    kresli();
  }

  function api(body) {
    var opts = {
      credentials: "include",
      headers: { "Content-Type": "application/json" },
    };
    if (body) { opts.method = "POST"; opts.body = JSON.stringify(body); }
    return fetch(EP, opts).then(function (r) {
      return r.json().catch(function () { return {}; }).then(function (j) {
        if (!r.ok && !j.error) { j.error = "HTTP " + r.status; }
        return j;
      });
    });
  }

  function nacti() {
    return api(null).then(function (j) {
      if (!j || !j.ok) { throw new Error((j && j.error) || "nepodařilo se načíst"); }
      _data = j;
      return j;
    });
  }

  // ── vykreslení ────────────────────────────────────────────────────────────
  function kresli() {
    if (!_el) { return; }
    var jeTabulka = (pohled() === "tabulka");
    var g = gridHost();
    if (g) { g.style.display = jeTabulka ? "" : "none"; }
    _el.style.cssText = jeTabulka
      ? "background:#0f141a;padding:10px 14px 0;"
      : "background:#0f141a;padding:14px 16px 18px;overflow:auto;flex:1 1 auto;min-height:0;";

    var h = styl() + '<div class="psp-wrap">' + hlavicka(jeTabulka);
    if (!jeTabulka) { h += telo(); }
    h += "</div>";
    _el.innerHTML = h;
    zapoj();
  }

  function hlavicka(jeTabulka) {
    var volnych = (_data && _data.volne_skupiny) ? _data.volne_skupiny.length : 0;
    var smi = !!(_data && _data.smi_menit);
    return '' +
      '<div class="psp-bar">' +
      '  <div class="psp-prep" role="group" aria-label="Zobrazení">' +
      '    <button type="button" class="psp-tab' + (jeTabulka ? "" : " on") + '" data-pohled="dlazdice">▦ Dlaždice</button>' +
      '    <button type="button" class="psp-tab' + (jeTabulka ? " on" : "") + '" data-pohled="tabulka">☰ Tabulka</button>' +
      '  </div>' +
      (jeTabulka ? '' :
        '  <button type="button" class="psp-add" id="pspAdd"' +
        (smi && volnych > 0 ? '' : ' disabled') + ' title="' +
        (!smi ? 'Měnit smí jen HR nebo rodič'
              : (volnych > 0 ? 'Přidat výchozí podmínky další skupině'
                             : 'Všechny skupiny už svůj řádek mají')) + '">' +
        '➕ Přidat skupinu' + (volnych > 0 ? ' (' + volnych + ')' : '') + '</button>') +
      '</div>';
  }

  function telo() {
    var d = (_data && _data.dlazdice) || [];
    if (!d.length) { return '<div class="psp-empty">Zatím tu nic není.</div>'; }
    var smi = !!(_data && _data.smi_menit);
    return '<div class="psp-grid">' + d.map(function (x) {
      var hod = (x.hodnoty || []).map(function (h) {
        return '<div class="psp-h' + (h.zdedeno ? " ded" : "") + '">' +
               '<span class="psp-hp">' + esc(h.popis) + '</span>' +
               '<span class="psp-hv">' + (h.hodnota == null ? "—" : esc(h.hodnota)) +
               (h.zdedeno && h.hodnota != null ? '<i class="psp-ded">ze Systému</i>' : '') +
               '</span></div>';
      }).join("");
      return '' +
        '<div class="psp-tile' + (x.system ? " sys" : "") + '" data-id="' + x.id +
        '" tabindex="0" role="button" title="Otevřít podmínky – ' + esc(x.nazev) + '">' +
        (x.smi_smazat && smi
          ? '<button type="button" class="psp-del" data-del="' + x.id +
            '" title="Smazat výchozí podmínky skupiny ' + esc(x.nazev) + '">✕</button>'
          : (x.system ? '<span class="psp-lock" title="Systémový řádek smazat nelze — plní se z něj podmínky každé nové smlouvě">🔒</span>' : '')) +
        '  <div class="psp-head"><span class="psp-ic">' + esc(x.ikona) + '</span>' +
        '    <span class="psp-name">' + esc(x.nazev) + '</span></div>' +
        (x.podnadpis ? '  <div class="psp-sub">' + esc(x.podnadpis) + '</div>' : '') +
        (x.lidi != null ? '  <div class="psp-sub">' + x.lidi + ' ' + sklonLidi(x.lidi) + '</div>' : '') +
        '  <div class="psp-vals">' + hod + '</div>' +
        '</div>';
    }).join("") + '</div>';
  }

  function sklonLidi(n) {
    if (n === 1) { return "člověk"; }
    if (n >= 2 && n <= 4) { return "lidé"; }
    return "lidí";
  }

  // ── akce ──────────────────────────────────────────────────────────────────
  function zapoj() {
    if (!_el) { return; }
    Array.prototype.forEach.call(_el.querySelectorAll("[data-pohled]"), function (b) {
      b.addEventListener("click", function () { setPohled(b.getAttribute("data-pohled")); });
    });
    var add = _el.querySelector("#pspAdd");
    if (add) { add.addEventListener("click", pridat); }
    Array.prototype.forEach.call(_el.querySelectorAll(".psp-del"), function (b) {
      b.addEventListener("click", function (ev) {
        ev.stopPropagation();
        smazat(parseInt(b.getAttribute("data-del"), 10));
      });
    });
    Array.prototype.forEach.call(_el.querySelectorAll(".psp-tile"), function (t) {
      function otevri() { otevriEditaci(parseInt(t.getAttribute("data-id"), 10)); }
      t.addEventListener("click", otevri);
      t.addEventListener("keydown", function (ev) {
        if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); otevri(); }
      });
    });
  }

  function obnov() {
    return nacti().then(kresli).catch(function (e) {
      console.warn("[PodminkySkupinPult] obnovení selhalo:", e);
    });
  }

  function otevriEditaci(rowId) {
    if (rowId == null || isNaN(rowId)) { return; }
    if (typeof window.DesignFwForm !== "function") {
      alert("⚠ Editační formulář není načtený. Zkus obnovit stránku (Ctrl+F5).");
      return;
    }
    var uz = document.querySelector(
      '[data-design-fw-form-root="1"][data-design-fw-form-core-id="' + EDIT_CORE_ID + '"]'
    );
    if (uz) { return; }   // stejný formulář už je otevřený (parita s ErpGridActions)
    try {
      new window.DesignFwForm({
        coreId: EDIT_CORE_ID,
        rowId: rowId,
        mode: "edit",
        onSaveSuccess: function () { obnov(); },
      });
    } catch (e) {
      console.warn("[PodminkySkupinPult] otevření editace selhalo:", e);
      alert("⚠ Editaci se nepodařilo otevřít: " + (e && e.message ? e.message : e));
    }
  }

  function pridat() {
    var volne = (_data && _data.volne_skupiny) || [];
    if (!volne.length) {
      alert("Všechny skupiny už svoje výchozí podmínky mají.");
      return;
    }
    var seznam = volne.map(function (g, i) {
      return "  " + (i + 1) + ") " + g.nazev;
    }).join("\n");
    var odp = window.prompt(
      "Které skupině založit vlastní výchozí podmínky?\n" +
      "Napiš číslo ze seznamu (skupiny, které řádek zatím nemají):\n\n" + seznam,
      "1"
    );
    if (odp == null) { return; }
    var idx = parseInt(String(odp).trim(), 10);
    if (isNaN(idx) || idx < 1 || idx > volne.length) {
      alert("Nerozumím volbě „" + odp + "\". Zkus to prosím znovu.");
      return;
    }
    var vybrana = volne[idx - 1];
    api({ akce: "pridat", group_id: vybrana.id }).then(function (j) {
      if (!j || !j.ok) {
        alert("⚠ Nepodařilo se přidat: " + ((j && j.error) || "neznámá chyba"));
        return;
      }
      return obnov().then(function () {
        // Rovnou otevři nový řádek k vyplnění — prázdné hodnoty dědí ze Systému.
        otevriEditaci(j.id);
      });
    }).catch(function (e) {
      alert("⚠ Nepodařilo se přidat: " + (e && e.message ? e.message : e));
    });
  }

  function smazat(rowId) {
    if (rowId == null || isNaN(rowId)) { return; }
    api({ akce: "dopad", radek_id: rowId }).then(function (j) {
      if (!j || !j.ok) {
        alert("⚠ " + ((j && j.error) || "Nepodařilo se zjistit dopad, mazání zastaveno."));
        return;
      }
      var d = j.dopad || {};
      var t = "Smazat výchozí podmínky skupiny „" + (d.nazev || "?") + "\"?\n\n";
      if (d.zmeny && d.zmeny.length) {
        t += "POZOR — tímhle se změní hodnoty živým lidem:\n\n";
        d.zmeny.forEach(function (z) {
          t += "• " + z.podminka + ": " + z.ze + " → " + z.na +
               "  (" + z.lidi + " " + sklonLidi(z.lidi) + ")\n" +
               "    " + (z.kdo || "") + "\n";
        });
        t += "\nSkupina pak bude dědit hodnoty ze Systému.";
      } else {
        t += "Nikomu se tím číslo nezmění — nikdo z téhle skupiny nemá hodnotu jen ze " +
             "skupiny.\nSkupina bude dědit hodnoty ze Systému.";
      }
      if (!window.confirm(t)) { return; }
      return api({ akce: "smazat", radek_id: rowId }).then(function (r) {
        if (!r || !r.ok) {
          alert("⚠ Nepodařilo se smazat: " + ((r && r.error) || "neznámá chyba"));
          return;
        }
        return obnov();
      });
    }).catch(function (e) {
      alert("⚠ Mazání selhalo: " + (e && e.message ? e.message : e));
    });
  }

  // ── styl ──────────────────────────────────────────────────────────────────
  function styl() {
    return '<style>' +
      '.psp-wrap{color:#e6edf3;font:13px/1.45 -apple-system,Segoe UI,Roboto,sans-serif;}' +
      '.psp-bar{display:flex;align-items:center;gap:12px;margin:0 0 12px;flex-wrap:wrap;}' +
      '.psp-prep{display:inline-flex;border:1px solid #2b3541;border-radius:8px;overflow:hidden;}' +
      '.psp-tab{background:#151c24;color:#9fb0c0;border:0;padding:6px 12px;cursor:pointer;font:inherit;}' +
      '.psp-tab.on{background:#243040;color:#e6edf3;font-weight:600;}' +
      '.psp-tab:hover{background:#1b232d;}' +
      '.psp-add{margin-left:auto;background:#1f6feb;color:#fff;border:0;border-radius:8px;' +
      'padding:6px 12px;cursor:pointer;font:inherit;}' +
      '.psp-add:disabled{background:#2b3541;color:#7d8b99;cursor:not-allowed;}' +
      '.psp-add:not(:disabled):hover{background:#2b7cf3;}' +
      '.psp-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(232px,1fr));gap:12px;}' +
      '.psp-tile{position:relative;background:#151c24;border:1px solid #2b3541;border-radius:11px;' +
      'padding:12px 12px 10px;cursor:pointer;transition:background .12s,border-color .12s;}' +
      '.psp-tile:hover,.psp-tile:focus{background:#1b232d;border-color:#3d4b5c;outline:none;}' +
      '.psp-tile:focus{box-shadow:0 0 0 2px #1f6feb55;}' +
      '.psp-tile.sys{border-color:#3f5570;background:#16202b;}' +
      '.psp-head{display:flex;align-items:center;gap:8px;}' +
      '.psp-ic{font-size:20px;line-height:1;}' +
      '.psp-name{font-weight:600;font-size:14px;}' +
      '.psp-sub{color:#8b9bab;font-size:11.5px;margin:3px 0 0 28px;}' +
      '.psp-vals{margin-top:9px;border-top:1px solid #232d38;padding-top:7px;}' +
      '.psp-h{display:flex;justify-content:space-between;gap:8px;padding:1.5px 0;}' +
      '.psp-hp{color:#8b9bab;}' +
      '.psp-hv{font-variant-numeric:tabular-nums;}' +
      '.psp-h.ded .psp-hv{color:#7d8b99;}' +
      '.psp-ded{font-style:normal;font-size:10px;color:#6b7885;margin-left:5px;}' +
      '.psp-del{position:absolute;top:7px;right:7px;background:transparent;color:#7d8b99;' +
      'border:0;border-radius:6px;width:22px;height:22px;cursor:pointer;font-size:13px;line-height:1;}' +
      '.psp-del:hover{background:#5c1f27;color:#ffb3bc;}' +
      '.psp-lock{position:absolute;top:8px;right:9px;font-size:11px;opacity:.55;}' +
      '.psp-empty{color:#8b9bab;padding:14px 0;}' +
      '</style>';
  }

  // ── vstupní bod ───────────────────────────────────────────────────────────
  function mount(el) {
    if (!el) { return; }
    _el = el;
    el.innerHTML = '<div style="color:#8b9bab;padding:14px 16px;">Načítám…</div>';
    nacti().then(kresli).catch(function (e) {
      console.warn("[PodminkySkupinPult] mount selhal, nechávám tabulku:", e);
      var g = gridHost();
      if (g) { g.style.display = ""; }
      _el.innerHTML = '<div style="color:#c9926b;padding:10px 14px;">' +
        'Nástěnku se nepodařilo načíst, zobrazuje se tabulka.</div>';
    });
  }

  window.PodminkySkupinPult = { mount: mount, refresh: obnov };
})();
