/* Odpracované hodiny komplet (do 2. 9. 2026 „Nesplněný FPD"; Výroba, jádro 209)
 * — pruh s volbou měsíce nad tabulkou.
 *
 * ZADÁNÍ (Jirka Honomichl 1.9.2026 pro Dušana Havláta, schválila Marti-AI msg 14071):
 *   Dušan potřebuje u přehledu přepínat mezi měsíci — aktuální a 12 měsíců zpět,
 *   nic do budoucna. Do 1.9.2026 byl měsíc natvrdo podle dnešního data a vybrat
 *   se nedal.
 *
 * JAK TO DRŽÍ POHROMADĚ:
 *   - Seznam měsíců I VÝCHOZÍ MĚSÍC dodává server (data_source vyroba.fpd_mesice).
 *     Schválně se tu NEPOČÍTÁ v prohlížeči: pravidlo „do 12. dne v měsíci se
 *     ukazuje měsíc minulý" žije v datové sadě 198 a kopie v prohlížeči by se
 *     s ní časem rozešla, aniž by to kdekoli ohlásilo chybu.
 *   - Volba se ukládá do _erpGridQuery na panelu záložky (page_render.js), takže tlačítko
 *     Obnovit i automatické obnovení použijí tentýž měsíc. Bez toho by Obnovit
 *     tiše skočilo zpátky na výchozí měsíc.
 *   - Při prvním otevření se ZÁMĚRNĚ nenačítá znovu: tabulka i pruh vyjdou ze
 *     stejného výchozího měsíce, takže by to bylo zbytečné druhé volání.
 *
 * Fail-safe: jakákoli chyba se jen zaloguje a tabulka jede dál (vzor HR pult).
 */
(function () {
  "use strict";

  var DS_MESICE = "/api/v1/erp/data-by-id/214?limit=50";  // vyroba.fpd_mesice
  var _el = null;
  var _vybrany = null;

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c];
    });
  }

  // Přepínač patří k tabulce ve STEJNÉ záložce, ne k naposledy vykreslené —
  // proto se hledá na vlastním panelu, ne v globální proměnné okna.
  function dotaz() {
    try {
      var host = _el && _el.parentElement;
      return (host && host._erpGridQuery) || null;
    } catch (e) { return null; }
  }

  function stav(text, barva) {
    try {
      var s = _el && _el.querySelector("#fpdStav");
      if (s) {
        s.textContent = text || "";
        s.style.color = barva || "#6f8296";
      }
    } catch (e) { /* fail-safe */ }
  }

  function prepni(kod) {
    if (!kod || kod === _vybrany) return;
    _vybrany = kod;
    try {
      var q = dotaz();
      if (!q) {
        stav("Přepínání měsíců není dostupné, tabulka ukazuje výchozí měsíc.", "#f0a93b");
        return;
      }
      q.set("&mesic=" + encodeURIComponent(kod));
      stav("Načítám…");
      var ret = q.reload();
      if (ret && typeof ret.then === "function") {
        ret.then(function () { stav(""); }).catch(function () {
          stav("Data se nepodařilo načíst, zkus to prosím znovu.", "#ff6b6b");
        });
      } else {
        stav("");
      }
    } catch (e) {
      console.warn("[FpdMesicPult] přepnutí měsíce selhalo:", e);
      stav("Data se nepodařilo načíst, zkus to prosím znovu.", "#ff6b6b");
    }
  }

  function kresli(mesice) {
    var vychozi = null;
    for (var i = 0; i < mesice.length; i++) {
      if (mesice[i].je_vychozi) { vychozi = mesice[i].kod; break; }
    }
    if (!vychozi && mesice.length) vychozi = mesice[0].kod;
    _vybrany = vychozi;

    var opts = mesice.map(function (m) {
      return '<option value="' + esc(m.kod) + '"' +
             (m.kod === vychozi ? " selected" : "") + ">" + esc(m.popisek) + "</option>";
    }).join("");

    _el.innerHTML =
      '<div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">' +
      '  <span style="font-size:13px;font-weight:700;color:#aac8ec;">📅 Měsíc</span>' +
      '  <select id="fpdMesic" style="font-size:13px;color:#e8edf6;background:#1e2a3a;' +
      'border:1px solid #2f4256;border-radius:6px;padding:5px 9px;cursor:pointer;min-width:150px;">' +
      opts +
      '  </select>' +
      '  <span style="font-size:11px;color:#6f8296;">aktuální měsíc a 12 měsíců zpět</span>' +
      '  <span id="fpdStav" style="font-size:11px;color:#6f8296;margin-left:auto;"></span>' +
      '</div>';

    var sel = _el.querySelector("#fpdMesic");
    if (sel) {
      sel.onchange = function () { prepni(sel.value); };
    }
  }

  function mount(el) {
    if (!el) return;
    _el = el;
    el.style.cssText = "background:#0f141a;padding:8px 12px;border-bottom:1px solid #1e2730;";
    el.innerHTML = '<div style="font-size:12px;color:#6f8296;">Načítám měsíce…</div>';

    fetch(DS_MESICE, { credentials: "include" })
      .then(function (r) { return r.json(); })
      .then(function (j) {
        if (!j || !j.ok || !Array.isArray(j.rows) || !j.rows.length) {
          throw new Error((j && j.error) || "prázdný seznam měsíců");
        }
        kresli(j.rows);
      })
      .catch(function (e) {
        console.warn("[FpdMesicPult] seznam měsíců se nenačetl, nechávám tabulku:", e);
        // Tabulka funguje dál na výchozím měsíci — pruh jen řekne, že volba není.
        try {
          _el.innerHTML =
            '<div style="font-size:12px;color:#f0a93b;">' +
            'Volbu měsíce se nepodařilo načíst — tabulka ukazuje výchozí měsíc.' +
            '</div>';
        } catch (e2) { /* fail-safe */ }
      });
  }

  window.FpdMesicPult = { mount: mount };
})();
