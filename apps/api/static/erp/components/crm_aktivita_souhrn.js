/* CRM — souhrnný pruh „Moje CRM čísla" nad přehledem Aktivity obchodníka.
 * A.3 z Pavlových připomínek. Read-only, samostatný (page_render volá jen
 * gated hook → window.CrmAktivitaSouhrn.mount). Fail-safe. (Kristý 25.6.2026) */
(function () {
  "use strict";
  var EP = "/api/v1/erp/app/crm/aktivity-souhrn";

  var CARDS = [
    { key: "oslovene_firmy", label: "Oslovené firmy", color: "#5b9bd5" },
    { key: "emaily",         label: "E-maily",         color: "#57a773" },
    { key: "hovory",         label: "Hovory",          color: "#4f86c6" },
    { key: "osobni",         label: "Osobní jednání",  color: "#9b6dc6" },
    { key: "poptavky",       label: "Poptávky",        color: "#d9a93b" },
    { key: "zakazky",        label: "Zakázky",         color: "#e08a3c" },
    { key: "nezajem",        label: "Nezájem",         color: "#c25b5b" }
  ];
  var OBDOBI = [["mesic", "Tento měsíc"], ["rok", "Tento rok"], ["vse", "Vše"]];

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c];
    });
  }

  function mount(el) {
    if (!el) return;
    el.style.cssText = "background:#0f141a;padding:10px 12px 4px;border-bottom:1px solid #1e2730;";
    el.innerHTML =
      '<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:8px;">' +
      '  <span style="font-size:13px;font-weight:700;color:#aac8ec;">📊 Moje CRM čísla</span>' +
      '  <label style="font-size:12px;color:#9fb6cc;">Obchodník:' +
      '    <select id="crmSouhrnAutor" style="margin-left:5px;background:#0d0d0d;color:#e0e0e0;' +
      '      border:1px solid #3a4a5a;border-radius:6px;padding:4px 6px;font-size:12px;"></select>' +
      '  </label>' +
      '  <label style="font-size:12px;color:#9fb6cc;">Období:' +
      '    <select id="crmSouhrnObdobi" style="margin-left:5px;background:#0d0d0d;color:#e0e0e0;' +
      '      border:1px solid #3a4a5a;border-radius:6px;padding:4px 6px;font-size:12px;"></select>' +
      '  </label>' +
      '  <span id="crmSouhrnStav" style="font-size:11px;color:#6f8296;"></span>' +
      '</div>' +
      '<div id="crmSouhrnKarty" style="display:flex;gap:8px;flex-wrap:wrap;"></div>';

    var selAutor = el.querySelector("#crmSouhrnAutor");
    var selObdobi = el.querySelector("#crmSouhrnObdobi");
    var karty = el.querySelector("#crmSouhrnKarty");
    var stav = el.querySelector("#crmSouhrnStav");

    OBDOBI.forEach(function (o) {
      var op = document.createElement("option");
      op.value = o[0]; op.textContent = o[1];
      if (o[0] === "rok") op.selected = true;
      selObdobi.appendChild(op);
    });

    function renderKarty(counts) {
      karty.innerHTML = "";
      CARDS.forEach(function (c) {
        var v = (counts && counts[c.key] != null) ? counts[c.key] : 0;
        var card = document.createElement("div");
        card.style.cssText = "min-width:104px;flex:0 0 auto;background:#161c24;border:1px solid #233040;" +
          "border-left:3px solid " + c.color + ";border-radius:8px;padding:8px 12px;";
        card.innerHTML =
          '<div style="font-size:22px;font-weight:700;color:#eef3f8;line-height:1.1;">' + esc(v) + '</div>' +
          '<div style="font-size:11px;color:#9fb6cc;margin-top:2px;">' + esc(c.label) + '</div>';
        karty.appendChild(card);
      });
    }

    function fillAutori(list, selected) {
      selAutor.innerHTML = "";
      var optAll = document.createElement("option");
      optAll.value = "__ALL__"; optAll.textContent = "Všichni";
      selAutor.appendChild(optAll);
      var have = {};
      (list || []).forEach(function (o) {
        have[o.autor] = true;
        var op = document.createElement("option");
        op.value = o.autor; op.textContent = o.autor + " (" + o.pocet + ")";
        selAutor.appendChild(op);
      });
      // Default = přihlášený uživatel. Když není v seznamu (nemá akce v CRM),
      // přidej ho jako volbu, ať dropdown ukazuje JEHO, ne „Všichni" (Kristý 25.6.).
      if (selected && selected.length && !have[selected]) {
        var opMe = document.createElement("option");
        opMe.value = selected; opMe.textContent = selected + " (já)";
        selAutor.insertBefore(opMe, optAll.nextSibling);
      }
      selAutor.value = (selected && selected.length) ? selected : "__ALL__";
      if (selAutor.selectedIndex < 0) selAutor.value = "__ALL__";
    }

    var autoriLoaded = false;

    function load(initial) {
      stav.textContent = "načítám…";
      var params = "?obdobi=" + encodeURIComponent(selObdobi.value);
      if (!initial) {
        var a = selAutor.value === "__ALL__" ? "" : selAutor.value;
        params += "&autor=" + encodeURIComponent(a);
      }
      fetch(EP + params, { credentials: "include" })
        .then(function (r) { return r.json().catch(function () { return {}; }); })
        .then(function (j) {
          if (!j || !j.ok) { stav.textContent = "✗ " + ((j && j.error) || "chyba"); return; }
          if (!autoriLoaded) {
            // j.autor = obchodník, podle kterého server reálně filtroval (default = já).
            // Dropdown nastavíme PŘESNĚ na něj → čísla i filtr si odpovídají.
            fillAutori(j.obchodnici, j.autor || j.muj_autor || "");
            autoriLoaded = true;
          }
          renderKarty(j.counts);
          stav.textContent = "";
        })
        .catch(function (e) { stav.textContent = "✗ síť"; });
    }

    selAutor.addEventListener("change", function () { load(false); });
    selObdobi.addEventListener("change", function () { load(false); });
    load(true);
  }

  window.CrmAktivitaSouhrn = { mount: mount };
})();
