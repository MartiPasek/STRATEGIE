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
      '  <button id="opImportBtn" style="margin-left:auto;font-size:12px;font-weight:600;color:#0f141a;' +
      'background:#3ecf8e;border:0;border-radius:6px;padding:5px 11px;cursor:pointer;">📥 Import firem</button>' +
      '  <span id="opStav" style="font-size:11px;color:#6f8296;"></span>' +
      '</div>' +
      '<div id="opBaty" style="display:flex;gap:10px;flex-wrap:wrap;align-items:stretch;"></div>' +
      '<div style="margin-top:10px;padding-top:8px;border-top:1px solid #1e2730;' +
      'font-size:13px;font-weight:700;color:#aac8ec;">📞 Plán hovorů — tento týden</div>';

    var baty = el.querySelector("#opBaty");
    var planKpi = el.querySelector("#opPlanKpi");
    var stav = el.querySelector("#opStav");
    var impBtn = el.querySelector("#opImportBtn");
    if (impBtn) impBtn.onclick = function () { openImportModal(); };

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
        var d = letos[mn];
        if (!d || d.bez_planu) {
          html +=
            '<div style="background:#161c24;border:1px solid #233040;border-radius:8px;padding:8px 11px;min-width:120px;">' +
            '<div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px;">' +
            '<span style="font-size:12px;color:#cdd6e2;">' + NAMES[mn - 1] + '</span>' +
            '<span style="font-size:12px;color:#9fb6cc;">zatím neplánováno</span></div>' +
            '<div style="height:10px;border-radius:5px;background:#0e1630;border:1px dashed #33415a;"></div>' +
            '<div style="font-size:10.5px;color:#6f8296;margin-top:4px;">ve výrobě zatím není plán (ne 0 %)</div>' +
            '</div>';
          return;
        }
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
        '<th style="padding:3px 8px;">Osoba</th>' +
        '<th style="padding:3px 8px;">Typ</th><th style="padding:3px 8px;">Telefon</th>' +
        '<th style="padding:3px 8px;">Průběh</th></tr></thead><tbody>';
      rows.forEach(function (r) {
        h += '<tr style="border-top:1px solid #1a2230;">' +
          '<td style="padding:4px 8px 4px 0;color:#cdd6e2;white-space:nowrap;">' + esc(r.datum || "") + '</td>' +
          '<td style="padding:4px 8px;color:#eef3f8;">' + esc(r.firma || "") + '</td>' +
          '<td style="padding:4px 8px;color:#cdd6e2;white-space:nowrap;">' + esc(r.osoba || "") + '</td>' +
          '<td style="padding:4px 8px;color:#9fb6cc;white-space:nowrap;">' + esc(r.typ || "") + '</td>' +
          '<td style="padding:4px 8px;color:#9fb6cc;white-space:nowrap;">' + esc(r.telefon || "") + '</td>' +
          '<td style="padding:4px 8px;color:#cdd6e2;">' + esc(String(r.poznamka || "").slice(0, 160)) + '</td>' +
          '</tr>';
      });
      h += '</tbody></table>';
      body.innerHTML = h;
    }
  }

  // ── Import firem (Kristý 6.7.2026) ──────────────────────────────────────
  var IMP_BASE = "/api/v1/erp/crm/import";

  function openImportModal() {
    if (document.getElementById("crmImpOverlay")) return;
    var ov = document.createElement("div");
    ov.id = "crmImpOverlay";
    ov.style.cssText = "position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:9999;" +
      "display:flex;align-items:center;justify-content:center;padding:16px;";
    ov.innerHTML =
      '<div style="background:#131a22;border:1px solid #253143;border-radius:12px;width:560px;max-width:100%;' +
      'max-height:90vh;overflow:auto;box-shadow:0 12px 40px rgba(0,0,0,.5);">' +
      '<div style="display:flex;align-items:center;gap:10px;padding:14px 16px;border-bottom:1px solid #1e2730;">' +
      '<span style="font-size:15px;font-weight:700;color:#eef3f8;">📥 Import firem do CRM</span>' +
      '<button id="crmImpClose" style="margin-left:auto;background:none;border:0;color:#9fb6cc;font-size:20px;cursor:pointer;">×</button>' +
      '</div>' +
      '<div style="padding:16px;display:flex;flex-direction:column;gap:12px;">' +
      '  <div style="font-size:12px;color:#9fb6cc;">Nahraj Excel/CSV podle šablony. Založí kontakty v CRM' +
      ' a volitelně akci „Email na info". <a id="crmImpTpl" href="#" style="color:#5b8def;">Stáhnout šablonu</a></div>' +
      '  <label style="font-size:12px;color:#cdd6e2;">Soubor (Excel/CSV)' +
      '   <input id="crmImpFile" type="file" accept=".xlsx,.xls,.csv" style="display:block;margin-top:4px;color:#cdd6e2;font-size:12px;"></label>' +
      '  <label style="font-size:12px;color:#cdd6e2;">Obchodník (autor záznamů)' +
      '   <select id="crmImpObch" style="display:block;width:100%;margin-top:4px;background:#0e1620;color:#eef3f8;' +
      'border:1px solid #2a3646;border-radius:6px;padding:6px;font-size:13px;"></select></label>' +
      '  <label style="font-size:12px;color:#cdd6e2;">Zdroj (štítek kampaně)' +
      '   <input id="crmImpZdroj" type="text" value="Import" maxlength="50" style="display:block;width:100%;margin-top:4px;' +
      'background:#0e1620;color:#eef3f8;border:1px solid #2a3646;border-radius:6px;padding:6px;font-size:13px;box-sizing:border-box;"></label>' +
      '  <label style="font-size:12px;color:#cdd6e2;display:flex;align-items:center;gap:8px;">' +
      '   <input id="crmImpAkce" type="checkbox" checked> Zakládat akci „Email na info" (u řádků s datem oslovení)</label>' +
      '  <div id="crmImpMsg" style="font-size:12px;color:#9fb6cc;min-height:18px;"></div>' +
      '  <div id="crmImpSummary" style="font-size:12.5px;color:#cdd6e2;"></div>' +
      '  <div style="display:flex;gap:10px;justify-content:flex-end;border-top:1px solid #1e2730;padding-top:12px;">' +
      '   <button id="crmImpPreview" style="font-size:13px;font-weight:600;color:#eef3f8;background:#2a3646;border:0;border-radius:6px;padding:8px 14px;cursor:pointer;">Náhled</button>' +
      '   <button id="crmImpGo" disabled style="font-size:13px;font-weight:700;color:#0f141a;background:#3a4657;border:0;border-radius:6px;padding:8px 16px;cursor:not-allowed;">Importovat</button>' +
      '  </div>' +
      '</div></div>';
    document.body.appendChild(ov);

    var previewRows = null;
    var fileEl = ov.querySelector("#crmImpFile");
    var obchEl = ov.querySelector("#crmImpObch");
    var zdrojEl = ov.querySelector("#crmImpZdroj");
    var akceEl = ov.querySelector("#crmImpAkce");
    var msgEl = ov.querySelector("#crmImpMsg");
    var sumEl = ov.querySelector("#crmImpSummary");
    var goBtn = ov.querySelector("#crmImpGo");
    var prevBtn = ov.querySelector("#crmImpPreview");

    function close() { if (ov.parentNode) ov.parentNode.removeChild(ov); }
    ov.querySelector("#crmImpClose").onclick = close;
    ov.onclick = function (e) { if (e.target === ov) close(); };
    ov.querySelector("#crmImpTpl").onclick = function (e) {
      e.preventDefault(); window.open(IMP_BASE + "/sablona", "_blank");
    };

    function setGo(on) {
      goBtn.disabled = !on;
      goBtn.style.background = on ? "#3ecf8e" : "#3a4657";
      goBtn.style.cursor = on ? "pointer" : "not-allowed";
    }

    fetch(IMP_BASE + "/obchodnici", { credentials: "include" })
      .then(function (r) { return r.json().catch(function () { return {}; }); })
      .then(function (j) {
        var html = "";
        (j && j.obchodnici || []).forEach(function (o) {
          var sel = (j.current && o.login === j.current) ? " selected" : "";
          html += '<option value="' + esc(o.login) + '"' + sel + '>' + esc(o.label) +
            ' (' + esc(o.login) + ')</option>';
        });
        obchEl.innerHTML = html || '<option value="">(žádní obchodníci)</option>';
      })
      .catch(function () { obchEl.innerHTML = '<option value="">(nepodařilo se načíst)</option>'; });

    prevBtn.onclick = function () {
      if (!fileEl.files || !fileEl.files[0]) { msgEl.textContent = "Vyber soubor."; return; }
      msgEl.style.color = "#9fb6cc"; msgEl.textContent = "Načítám náhled…";
      sumEl.innerHTML = ""; setGo(false); previewRows = null;
      var fd = new FormData(); fd.append("file", fileEl.files[0]);
      fetch(IMP_BASE + "/preview", { method: "POST", credentials: "include", body: fd })
        .then(function (r) { return r.json().catch(function () { return {}; }); })
        .then(function (j) {
          if (!j || !j.ok) { msgEl.style.color = "#ff6b6b"; msgEl.textContent = "✗ " + ((j && j.error) || "chyba náhledu"); return; }
          previewRows = j.rows || [];
          var s = j.summary || {};
          msgEl.style.color = "#3ecf8e"; msgEl.textContent = "✓ Náhled hotový";
          sumEl.innerHTML =
            '<div style="background:#0e1620;border:1px solid #253143;border-radius:8px;padding:10px 12px;line-height:1.7;">' +
            '<b>' + (s.total || 0) + '</b> firem v souboru · ' +
            '<span style="color:#3ecf8e;">' + (s.novych || 0) + ' nových</span> · ' +
            '<span style="color:#f0a93b;">' + (s.duplicit || 0) + ' už v CRM (přeskočí se)</span><br>' +
            'Akce „Email na info": <b>' + (s.s_akci || 0) + '</b> · ' +
            'z toho nedoručeno: <b style="color:#ff6b6b;">' + (s.nedoruceno || 0) + '</b></div>';
          setGo((s.novych || 0) > 0);
        })
        .catch(function () { msgEl.style.color = "#ff6b6b"; msgEl.textContent = "✗ síť"; });
    };

    goBtn.onclick = function () {
      if (!previewRows || !previewRows.length) return;
      if (!obchEl.value) { msgEl.style.color = "#ff6b6b"; msgEl.textContent = "Vyber obchodníka."; return; }
      setGo(false); prevBtn.disabled = true;
      msgEl.style.color = "#9fb6cc"; msgEl.textContent = "Zapisuji do CRM… (může chvíli trvat)";
      fetch(IMP_BASE + "/commit", {
        method: "POST", credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          rows: previewRows, obchodnik: obchEl.value,
          create_akce: !!akceEl.checked, zdroj: (zdrojEl.value || "Import")
        })
      })
        .then(function (r) { return r.json().catch(function () { return {}; }); })
        .then(function (j) {
          prevBtn.disabled = false;
          if (!j || !j.ok) { msgEl.style.color = "#ff6b6b"; msgEl.textContent = "✗ " + ((j && j.error) || "zápis selhal"); setGo(true); return; }
          var rp = j.report || {};
          msgEl.style.color = "#3ecf8e"; msgEl.textContent = "✓ Import dokončen";
          var eh = "";
          if (rp.errors && rp.errors.length) {
            eh = '<div style="color:#ff6b6b;margin-top:6px;">Chyby (' + rp.errors.length + '): ' +
              esc(rp.errors.slice(0, 5).join(" · ")) + '</div>';
          }
          sumEl.innerHTML =
            '<div style="background:#0e1620;border:1px solid #253143;border-radius:8px;padding:10px 12px;line-height:1.7;">' +
            '✅ Založeno kontaktů: <b>' + (rp.created || 0) + '</b> (autor ' + esc(rp.obchodnik || "") + ')<br>' +
            'Akcí „Email na info": <b>' + (rp.akce_created || 0) + '</b> · nedoručeno: <b>' + (rp.bounced || 0) + '</b><br>' +
            'Přeskočeno (duplicita): <b>' + (rp.skipped_dup || 0) + '</b>' + eh + '</div>';
          previewRows = null;
        })
        .catch(function () { prevBtn.disabled = false; msgEl.style.color = "#ff6b6b"; msgEl.textContent = "✗ síť při zápisu"; setGo(true); });
    };
  }

  window.ObchodnikPult = { mount: mount, mountHovory: mountHovory, openImport: openImportModal };
})();
