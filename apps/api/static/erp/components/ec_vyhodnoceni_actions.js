/* ec_vyhodnoceni_actions.js — akcni lista pro jadro "Vyhodnoceni zakazky".
 * Wrapuje DesignFwForm.prototype._render: po renderu jadra (core code
 * 'ec.vyhodnoceni_jadro') vlozi listu tlacitek volajicich
 * POST /api/v1/erp/action/run (ec.* funkce, 1:1 zrcadlo Centraly).
 * Autor: Claude, 20.7.2026. Vse defenzivne — nikdy nevyhodi do frameworku.
 */
(function (global) {
  "use strict";

  var CORE_CODE = "ec.vyhodnoceni_jadro";
  var ACTIONS = [
    { code: "priprava",         label: "▶️ Připravit hodnocení", confirm: null },
    { code: "prepocet",         label: "🔄 Přepočet hodnocení", confirm: null },
    { code: "vypocet_konstant", label: "⚙️ Nastav koeficienty", confirm: null },
    { code: "uzavrit",          label: "🔒 Uzavřít", confirm: "⚠️ UZAVŘÍT vyhodnocení?\n\nTato akce VYTVOŘÍ VÝPLATY (SuperHrubá mzda) pro pracovníky této zakázky — zápis do financí zakázek.\n\nPokračovat?" },
    { code: "zrusit",           label: "↩️ Zrušit", confirm: "⚠️ ZRUŠIT vyhodnocení?\n\nSMAŽE vypočtené výplaty, zakázku zarchivuje a znovu otevře k přepočtu.\n\nPokračovat?" }
  ];

  /* Akce, ktere potrebuji vlastni obsluhu (vyber cloveka / seznam zakazek),
   * proto nejsou v ACTIONS vyse. Doplneno C28 (Jirka) 6.8.2026 — body 4 a 5
   * z doladeni modulu. Backend obou uz existoval a byl overeny, chybelo ovladani.
   *
   * PROC JSOU V JADRE A NE NA PREHLEDU: puvodni zadani znelo "hromadny vyber
   * radku na prehledu". Prehled je ale grid, ne DesignFwForm — tenhle soubor se
   * na nej nevesi. Slucovani z jadra ma navic prirozeny smysl: divam se na
   * zakazku a rikam, ktere dalsi se k ni maji pripojit. Kdyby to melo byt
   * na prehledu s multi-selectem, je to samostatna prace na jinem miste.
   */
  var VLASTNI = [
    { code: "sefmonter", label: "👷 Šéfmontér…" },
    { code: "slouci",    label: "🔗 Hodnotit společně…" },
    { code: "rozdelit",  label: "✂️ Zrušit sloučení" }
  ];

  function _rec(inst) { return (inst && inst._spec && inst._spec.data) || {}; }
  function _coreCode(inst) { try { return inst._spec.core.code; } catch (e) { return null; } }
  function _zakazka(inst) { return _rec(inst).cislo_zakazky || null; }

  /* Male modalni okno. Zamerne bez zavislosti na frameworku — kdyby se jeho
   * dialogy zmenily, tohle porad funguje. */
  function _okno(nadpis, obsahEl, potvrdText, onPotvrd) {
    var back = document.createElement("div");
    back.style.cssText = "position:fixed;inset:0;background:rgba(0,0,0,.35);z-index:99999;" +
      "display:flex;align-items:center;justify-content:center;";
    var box = document.createElement("div");
    box.style.cssText = "background:#fff;border-radius:10px;min-width:380px;max-width:560px;" +
      "max-height:80vh;overflow:auto;box-shadow:0 8px 30px rgba(0,0,0,.25);padding:16px 18px;";
    var h = document.createElement("div");
    h.textContent = nadpis;
    h.style.cssText = "font-weight:600;font-size:15px;margin:0 0 10px 0;";
    box.appendChild(h);
    box.appendChild(obsahEl);
    var lista = document.createElement("div");
    lista.style.cssText = "display:flex;gap:8px;justify-content:flex-end;margin-top:14px;";
    function zavri() { if (back.parentNode) back.parentNode.removeChild(back); }
    if (potvrdText) {
      var ok = document.createElement("button");
      ok.type = "button"; ok.textContent = potvrdText;
      ok.style.cssText = "padding:6px 14px;border:1px solid #2563eb;background:#2563eb;color:#fff;" +
        "border-radius:6px;cursor:pointer;font-size:13px;";
      ok.onclick = function () { zavri(); try { onPotvrd(); } catch (e) {} };
      lista.appendChild(ok);
    }
    var storno = document.createElement("button");
    storno.type = "button"; storno.textContent = "Zavřít";
    storno.style.cssText = "padding:6px 14px;border:1px solid #cbd5e1;background:#fff;" +
      "border-radius:6px;cursor:pointer;font-size:13px;";
    storno.onclick = zavri;
    lista.appendChild(storno);
    box.appendChild(lista);
    back.appendChild(box);
    back.onclick = function (e) { if (e.target === back) zavri(); };
    document.body.appendChild(back);
    return zavri;
  }

  /* Zavola ec.* akci a po uspechu prekresli jadro. Sdileno vsemi vlastnimi akcemi. */
  function _volej(inst, telo, hotovoText) {
    return fetch("/api/v1/erp/action/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(telo)
    }).then(function (r) {
      return r.json().then(function (j) { return { stav: r.status, j: j }; });
    }).then(function (o) {
      if (!o.j || !o.j.ok) {
        global.alert("Akce se nepovedla:\n\n" + ((o.j && o.j.error) || ("HTTP " + o.stav)));
        return false;
      }
      try { if (typeof inst._reloadSpec === "function") { inst._reloadSpec(); } } catch (e) {}
      if (hotovoText) global.alert(hotovoText);
      return true;
    }).catch(function (e) {
      global.alert("Chyba spojení: " + (e && e.message ? e.message : e));
      return false;
    });
  }

  /* 👷 Sefmonter — nabidne lidi z teto zakazky a nastavi vybraneho.
   * Lidi ctu ze stejneho zdroje jako grid "Hodnoceni vse", takze seznam
   * vzdy odpovida tomu, co uzivatel vidi. */
  function _sefmonter(inst) {
    var rec = _rec(inst);
    var id = (rec.id != null) ? rec.id : (inst.opts && inst.opts.rowId);
    if (id == null) { global.alert("Není načtená zakázka."); return; }
    var url = "/api/v1/erp/data/ec.vyhodnoceni_jadro_osoba?master_id=" +
              encodeURIComponent(id) + "&kind=select-detail";
    fetch(url, { credentials: "same-origin" })
      .then(function (r) { return r.json(); })
      .then(function (j) {
        var rows = (j && j.ok && Array.isArray(j.rows)) ? j.rows : [];
        var box = document.createElement("div");
        if (!rows.length) {
          box.textContent = "Na zakázce zatím nikdo není. Nejdřív dej „Připravit hodnocení“.";
          box.style.cssText = "font-size:13px;color:#475569;";
          _okno("Šéfmontér", box, null, null);
          return;
        }
        var info = document.createElement("div");
        info.textContent = "Klikni na člověka, kterého chceš nastavit jako šéfmontéra. " +
                           "Dalším kliknutím na téhož ho zase odznačíš.";
        info.style.cssText = "font-size:12px;color:#475569;margin-bottom:10px;";
        box.appendChild(info);
        var zavriOkno = null;   // naplni se hned pod cyklem (_okno vraci zaviraci funkci)
        rows.forEach(function (r) {
          var b = document.createElement("button");
          b.type = "button";
          var jmeno = r["Pracovník"] || r["Os. č."] || "?";
          var jeSefm = String(r["Šéfm."] || "").trim() !== "";
          b.textContent = (jeSefm ? "👷 " : "") + jmeno + (jeSefm ? "  (nyní šéfmontér)" : "");
          b.style.cssText = "display:block;width:100%;text-align:left;margin:0 0 6px 0;" +
            "padding:8px 10px;border:1px solid " + (jeSefm ? "#2563eb" : "#cbd5e1") +
            ";border-radius:6px;background:" + (jeSefm ? "#eff6ff" : "#fff") +
            ";cursor:pointer;font-size:13px;";
          b.onclick = function () {
            var osobaId = r["ID"];
            if (osobaId == null) { global.alert("U řádku chybí ID."); return; }
            if (typeof zavriOkno === "function") zavriOkno();
            _volej(inst, { action_code: "nastav_sefmontera", osoba_id: osobaId });
          };
          box.appendChild(b);
        });
        zavriOkno = _okno("Šéfmontér zakázky " + (_zakazka(inst) || ""), box, null, null);
      })
      .catch(function (e) {
        global.alert("Nepovedlo se načíst lidi: " + (e && e.message ? e.message : e));
      });
  }

  /* 🔗 Hodnotit spolecne — slouci tuto zakazku s dalsimi zadanymi.
   * Zadavaji se cisla zakazek, protoze jich je pres 5 600 a seznam by byl
   * nepouzitelny. Backend si skupinu poresi sam (ec.slouci_zakazky). */
  function _slouci(inst) {
    var zak = _zakazka(inst);
    if (!zak) { global.alert("Není načtená zakázka."); return; }
    var box = document.createElement("div");
    var info = document.createElement("div");
    info.innerHTML = "Zakázky se budou hodnotit <b>dohromady</b> — hodiny i kalkulace se " +
      "sečtou a prémie se rozdělí přes celou skupinu.<br><br>Napiš čísla dalších zakázek " +
      "(oddělená čárkou nebo mezerou). Zakázka <b>" + zak + "</b> se přidá automaticky.";
    info.style.cssText = "font-size:13px;color:#334155;margin-bottom:10px;line-height:1.5;";
    box.appendChild(info);
    var ta = document.createElement("textarea");
    ta.rows = 3;
    ta.placeholder = "např. VR10005, VR10007";
    ta.style.cssText = "width:100%;box-sizing:border-box;padding:8px;border:1px solid #cbd5e1;" +
      "border-radius:6px;font-size:13px;font-family:inherit;";
    box.appendChild(ta);
    _okno("Hodnotit společně se zakázkou " + zak, box, "Sloučit", function () {
      var dalsi = String(ta.value || "").split(/[,;\s]+/)
        .map(function (s) { return s.trim(); })
        .filter(function (s) { return s.length > 0; });
      if (!dalsi.length) { global.alert("Nezadal jsi žádnou další zakázku."); return; }
      var vse = [zak].concat(dalsi.filter(function (z) { return z !== zak; }));
      _volej(inst, { action_code: "slouci", zaks: vse },
             "Sloučeno. Skupina má " + vse.length + " zakázek.");
    });
  }

  /* ✂️ Zruseni slouceni teto zakazky (ostatni ve skupine zustavaji spolu). */
  function _rozdelit(inst) {
    var zak = _zakazka(inst);
    if (!zak) { global.alert("Není načtená zakázka."); return; }
    if (!global.confirm("Zrušit sloučení u zakázky " + zak + "?\n\n" +
        "Zakázka se bude hodnotit sama. Ostatní zakázky ve skupině zůstanou spolu.\n\nPokračovat?")) return;
    _volej(inst, { action_code: "slouci_zrus", zaks: [zak] }, "Sloučení zrušeno.");
  }

  function _vlastni(inst, act, btn) {
    var old = btn.textContent;
    btn.disabled = true;
    try {
      if (act.code === "sefmonter") { _sefmonter(inst); }
      else if (act.code === "slouci") { _slouci(inst); }
      else if (act.code === "rozdelit") { _rozdelit(inst); }
    } catch (e) {
      global.alert("Chyba: " + (e && e.message ? e.message : e));
    }
    btn.disabled = false; btn.textContent = old;
  }

  function _run(inst, act, btn) {
    var rec = _rec(inst);
    var id = (rec.id != null) ? rec.id : (inst.opts && inst.opts.rowId);
    if (id == null) { global.alert("Není načtená zakázka."); return; }
    if (act.confirm && !global.confirm(act.confirm)) return;
    var old = btn.textContent;
    btn.disabled = true; btn.textContent = "…";
    fetch("/api/v1/erp/action/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action_code: act.code, id: id })
    }).then(function (resp) {
      return resp.json().then(function (j) { return { ok: resp.ok, j: j }; });
    }).then(function (o) {
      if (!o.j || !o.j.ok) {
        global.alert("Akce selhala: " + ((o.j && o.j.error) || "HTTP " + (o.ok ? "200" : "err")));
      } else {
        try { if (typeof inst._reloadSpec === "function") { inst._reloadSpec(); } } catch (e) {}
      }
    }).catch(function (e) {
      global.alert("Chyba spojení: " + (e && e.message ? e.message : e));
    }).then(function () {
      btn.disabled = false; btn.textContent = old;
    });
  }

  function _inject(inst) {
    if (_coreCode(inst) !== CORE_CODE) return;
    var host = inst._shell && inst._shell.body;
    if (!host) return;
    var old = host.querySelector(".ec-vyh-actionbar");
    if (old && old.parentNode) old.parentNode.removeChild(old);
    var bar = document.createElement("div");
    bar.className = "ec-vyh-actionbar";
    /* PRILEPENA NAHORE (C28 6.8.2026, podnet Dusana): obsah jadra je vyssi nez okno
     * (~1 240 px proti ~860 viditelnym), takze se roluje - a lista tlacitek driv
     * odrolovala pryc. Uzivatel u gridu dole uz nevidel, cim ma pokracovat.
     * position:sticky ji drzi nahore po celou dobu rolovani.
     * Zaroven kompaktneji (mensi padding a pismo), aby se veslo na JEDEN radek -
     * osm tlacitek se driv lamalo do dvou a lista brala 85 px z vysky. */
    bar.style.cssText = "position:sticky;top:0;z-index:5;display:flex;gap:6px;flex-wrap:wrap;" +
      "padding:6px 8px;margin:0 0 8px 0;background:#f5f7fa;border:1px solid #e2e8f0;" +
      "border-radius:8px;box-shadow:0 2px 6px rgba(0,0,0,.06);";
    ACTIONS.forEach(function (act) {
      var b = document.createElement("button");
      b.type = "button";
      b.textContent = act.label;
      b.style.cssText = "cursor:pointer;padding:4px 9px;border:1px solid #cbd5e1;border-radius:6px;background:#fff;font-size:12px;line-height:1.2;white-space:nowrap;";
      b.onmouseenter = function () { b.style.background = "#eef2ff"; };
      b.onmouseleave = function () { b.style.background = "#fff"; };
      b.onclick = function () { _run(inst, act, b); };
      bar.appendChild(b);
    });
    // Oddelovac + akce s vlastni obsluhou (sefmonter, slouceni) — C28 6.8.2026.
    var del = document.createElement("span");
    del.style.cssText = "width:1px;background:#cbd5e1;margin:0 4px;";
    bar.appendChild(del);
    VLASTNI.forEach(function (act) {
      var b = document.createElement("button");
      b.type = "button";
      b.textContent = act.label;
      b.style.cssText = "cursor:pointer;padding:4px 9px;border:1px solid #cbd5e1;border-radius:6px;background:#fff;font-size:12px;line-height:1.2;white-space:nowrap;";
      b.onmouseenter = function () { b.style.background = "#eef2ff"; };
      b.onmouseleave = function () { b.style.background = "#fff"; };
      b.onclick = function () { _vlastni(inst, act, b); };
      bar.appendChild(b);
    });
    host.insertBefore(bar, host.firstChild);
  }

  function _install() {
    var F = global.DesignFwForm;
    if (!F || !F.prototype || F.prototype.__ecVyhWrapped) return !!(F && F.prototype && F.prototype.__ecVyhWrapped);
    var origRender = F.prototype._render;
    if (typeof origRender !== "function") return false;
    F.prototype._render = function () {
      var r = origRender.apply(this, arguments);
      try { _inject(this); } catch (e) { if (global.console) global.console.error("[ec-vyh-actions]", e); }
      return r;
    };
    F.prototype.__ecVyhWrapped = true;
    return true;
  }

  if (!_install()) {
    var tries = 0;
    var iv = setInterval(function () {
      tries++;
      if (_install() || tries > 100) clearInterval(iv);
    }, 100);
  }
})(window);
