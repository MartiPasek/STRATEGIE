/* CRM — band „Vytížení + plán" nad přehledem „Přehled pro obchodníka" (core 136).
 * Grafy vytížení dílny (baterky 3 měsíce + tank volné kapacity za celý rok) +
 * týdenní souhrn hovorů (po termínu / tento týden). Read-only, fail-safe.
 * page_render volá jen gated hook → window.ObchodnikPult.mount. (Kristý 29.6.2026) */
(function () {
  "use strict";
  var EP_VYT = "/api/v1/erp/app/vytizeni-mesice";
  var EP_PLAN = "/api/v1/erp/app/crm/plan-hovoru";
  var EP_HOVORY = "/api/v1/erp/app/crm/hovory-tyden";
  var NAMES = ["Leden", "Únor", "Březen", "Duben", "Květen", "Červen",
               "Červenec", "Srpen", "Září", "Říjen", "Listopad", "Prosinec"];

  function col(p) { return p >= 70 ? "#3ecf8e" : p >= 35 ? "#f0a93b" : "#ff6b6b"; }
  function csNum(n) { return Math.round(n).toLocaleString("cs"); }
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c];
    });
  }

  function mount(el) {
    if (!el) return;
    el.style.cssText = "background:#0f141a;padding:10px 12px 8px;border-bottom:1px solid #1e2730;";
    el.innerHTML =
      '<div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:8px;">' +
      '  <span style="font-size:13px;font-weight:700;color:#aac8ec;">🔋 Vytížení dílny — výhled 3 měsíce</span>' +
      '  <span id="opPlanKpi" style="font-size:12px;color:#9fb6cc;"></span>' +
      '  <span id="opStav" style="font-size:11px;color:#6f8296;margin-left:auto;"></span>' +
      '</div>' +
      '<div id="opBaty" style="display:flex;gap:10px;flex-wrap:wrap;align-items:stretch;"></div>' +
      '<div style="margin-top:10px;padding-top:8px;border-top:1px solid #1e2730;' +
      'font-size:13px;font-weight:700;color:#aac8ec;">📞 Plán hovorů — tento týden</div>';

    var baty = el.querySelector("#opBaty");
    var planKpi = el.querySelector("#opPlanKpi");
    var stav = el.querySelector("#opStav");

    fetch(EP_VYT, { credentials: "include" })
      .then(function (r) { return r.json().catch(function () { return {}; }); })
      .then(function (j) {
        if (!j || !j.ok || !j.rows) { stav.textContent = "✗ vytížení"; return; }
        renderVyt(j.rows);
      })
      .catch(function () { stav.textContent = "✗ síť"; });

    fetch(EP_PLAN, { credentials: "include" })
      .then(function (r) { return r.json().catch(function () { return {}; }); })
      .then(function (j) {
        if (!j || !j.ok || !j.rows) { return; }
        renderPlanKpi(j.rows);
      })
      .catch(function () {});

    function renderVyt(rows) {
      var cy = (new Date()).getFullYear();
      var cm = (new Date()).getMonth() + 1;
      var letos = {};
      rows.forEach(function (r) { if (r.rok === cy) letos[r.mesic] = r; });

      var win = [];
      for (var i = 0; i < 3; i++) { var mn = cm + i; if (mn > 12) break; win.push(mn); }

      var html = "";
      win.forEach(function (mn) {
        var d = letos[mn] || {};
        var p = Math.round(d.vytizeni || 0);
        var c = col(p);
        html +=
          '<div style="background:#161c24;border:1px solid #233040;border-radius:8px;padding:8px 11px;min-width:120px;">' +
          '<div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px;">' +
          '<span style="font-size:12px;color:#cdd6e2;">' + NAMES[mn - 1] + '</span>' +
          '<span style="font-size:15px;font-weight:700;color:' + c + ';">' + p + ' %</span></div>' +
          '<div style="height:10px;border-radius:5px;background:#0e1630;overflow:hidden;">' +
          '<div style="height:100%;width:' + Math.min(Math.max(p, 2), 100) + '%;background:' + c + ';border-radius:5px;"></div>' +
          '</div></div>';
      });

      var kapY = 0, splY = 0;
      for (var m = 1; m <= 12; m++) {
        var dd = letos[m];
        if (!dd) continue;
        kapY += (dd.kapacita || 0);
        splY += (dd.hodiny || 0);
      }
      var volnaY = Math.max(kapY - splY, 0);
      var freePct = kapY > 0 ? Math.round(100 * volnaY / kapY) : 0;
      var soldPct = 100 - freePct;
      html +=
        '<div style="background:#161c24;border:1px solid #233040;border-radius:8px;padding:8px 11px;min-width:210px;flex:1;">' +
        '<div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px;">' +
        '<span style="font-size:12px;color:#cdd6e2;">Volná kapacita (celý rok)</span>' +
        '<span style="font-size:15px;font-weight:700;color:#eef3f8;">' + csNum(volnaY) + ' h</span></div>' +
        '<div style="height:10px;border-radius:5px;background:rgba(91,141,239,.16);overflow:hidden;display:flex;">' +
        '<div style="height:100%;width:' + soldPct + '%;background:#5b8def;"></div></div>' +
        '<div style="display:flex;justify-content:space-between;font-size:10.5px;color:#7e8aa3;margin-top:4px;">' +
        '<span>naplánováno ' + soldPct + ' %</span><span>volno ' + freePct + ' %</span></div>' +
        '</div>';

      baty.innerHTML = html;
    }

    function renderPlanKpi(rows) {
      var today = new Date(); today.setHours(0, 0, 0, 0);
      var dow = (today.getDay() + 6) % 7;
      var weekEnd = new Date(today);
      weekEnd.setDate(weekEnd.getDate() + (6 - dow));
      var over = 0, week = 0;
      rows.forEach(function (r) {
        var p = (r.pristi || "").split("-");
        if (p.length !== 3) return;
        var d = new Date(+p[0], +p[1] - 1, +p[2]);
        if (d < today) over++;
        else if (d <= weekEnd) week++;
      });
      planKpi.innerHTML =
        '📞 Plán hovorů: <b style="color:#ff6b6b;">' + over + '</b> po termínu · ' +
        '<b style="color:#3ecf8e;">' + week + '</b> tento týden';
    }
  }

  function mountHovory(el) {
    if (!el) return;
    el.style.cssText = "background:#0f141a;border-top:1px solid #1e2730;padding:8px 12px 10px;" +
      "max-height:230px;overflow:auto;flex:0 0 auto;";
    el.innerHTML =
      '<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">' +
      '  <span style="font-size:13px;font-weight:700;color:#aac8ec;">✅ Proběhlé hovory — tento týden</span>' +
      '  <span id="opHovStav" style="font-size:11px;color:#6f8296;"></span>' +
      '</div>' +
      '<div id="opHovBody"></div>';
    var body = el.querySelector("#opHovBody");
    var stav = el.querySelector("#opHovStav");

    fetch(EP_HOVORY, { credentials: "include" })
      .then(function (r) { return r.json().catch(function () { return {}; }); })
      .then(function (j) {
        if (!j || !j.ok || !j.rows) { stav.textContent = "✗ " + ((j && j.error) || "chyba"); return; }
        render(j.rows);
      })
      .catch(function () { stav.textContent = "✗ síť"; });

    function render(rows) {
      var n = rows.length;
      stav.textContent = n + (n === 1 ? " hovor" : (n >= 2 && n <= 4 ? " hovory" : " hovorů"));
      if (!n) {
        body.innerHTML = '<div style="font-size:12px;color:#6f8296;padding:6px 2px;">' +
          'Tento týden zatím žádné proběhlé hovory — jakmile Pavel zapíše telefonát, objeví se tady.</div>';
        return;
      }
      var h = '<table style="width:100%;border-collapse:collapse;font-size:12px;">' +
        '<thead><tr style="color:#7e8aa3;text-align:left;">' +
        '<th style="padding:3px 8px 3px 0;">Datum</th><th style="padding:3px 8px;">Firma</th>' +
        '<th style="padding:3px 8px;">Typ</th><th style="padding:3px 8px;">Telefon</th>' +
        '<th style="padding:3px 8px;">Průběh</th></tr></thead><tbody>';
      rows.forEach(function (r) {
        h += '<tr style="border-top:1px solid #1a2230;">' +
          '<td style="padding:4px 8px 4px 0;color:#cdd6e2;white-space:nowrap;">' + esc(r.datum || "") + '</td>' +
          '<td style="padding:4px 8px;color:#eef3f8;">' + esc(r.firma || "") + '</td>' +
          '<td style="padding:4px 8px;color:#9fb6cc;white-space:nowrap;">' + esc(r.typ || "") + '</td>' +
          '<td style="padding:4px 8px;color:#9fb6cc;white-space:nowrap;">' + esc(r.telefon || "") + '</td>' +
          '<td style="padding:4px 8px;color:#cdd6e2;">' + esc(String(r.poznamka || "").slice(0, 160)) + '</td>' +
          '</tr>';
      });
      h += '</tbody></table>';
      body.innerHTML = h;
    }
  }

  window.ObchodnikPult = { mount: mount, mountHovory: mountHovory };
})();
