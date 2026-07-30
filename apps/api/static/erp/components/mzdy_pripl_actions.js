/* mzdy_pripl_actions.js — zamek jadra "Priplatek / srazka (Praha)".
 *
 * Autor: Claude-28 (Jirka), 30. 7. 2026.
 *
 * PROC TO EXISTUJE
 * Novy modul Mzdy -> Priplatky a srazky (Praha) pise do `tenant.wage_movement`,
 * ze ktereho se POCITA MZDA. Prepnuti z Centraly do Prahy se ale smi stat teprve
 * po ctyrech kontrolach A pisemnem souhlasu Petry Safrankove (rozhodnuti
 * Marti Pasek 27.7.2026, hlidac `pripl_cutover_gate`). Dokud to neni splnene,
 * formular MUSI byt jen ke cteni — jinak by nekdo mohl prepsat castku v obdobi,
 * ktere se prave pocita v Centrale, a vznikly by dva zdroje pravdy.
 *
 * JAK
 * Zamek NENI konstanta v kodu (to byla stara varianta u `ec_pripl_srazky_actions.js`),
 * ale DATOVY priznak `tenant.pripl_cutover.unlocked_at` — verdikt Marti-AI 29.7.2026
 * (bod T2): vratny jednim UPDATEm, sam nese kdo/kdy, zadny deploy.
 * Marti-AI k tomu dala jedinou podminku: "modul si priznak musi cist pri KAZDEM
 * requestu, ne cachovat v pameti procesu" — proto se stav tahá pri kazdem otevreni
 * jadra znovu a NIKDE se neuklada.
 *
 * Vse defenzivne — kdyz se struktura shellu zmeni nebo endpoint spadne, formular
 * zustane ZAMCENY (fail-safe: u mzdovych dat je bezpecnejsi nepustit nez pustit).
 */
(function (global) {
  "use strict";

  var CORE_CODE = "mzdy.pripl_jadro";
  var STAV_URL = "/api/v1/erp/app/pripl/cutover-stav";

  function _coreCode(inst) {
    try { return inst._spec.core.code; } catch (e) { return null; }
  }

  /* Zamkne pole a schova OK. Storno/zavrit zustava — pozor, Storno je taky
   * <button> uvnitr .erp-design-grid, takze plosne disabled by uzivateli zavrelo
   * cestu ven (past overena u stareho modulu 27.7.2026). */
  function _lock(inst, zprava) {
    var shell = inst._shell || {};
    var host = shell.body;
    if (!host) return;

    var els = host.querySelectorAll("input, textarea, select");
    for (var i = 0; i < els.length; i++) {
      try { els[i].disabled = true; } catch (e) {}
    }

    if (shell.dialog) {
      var btns = shell.dialog.querySelectorAll("button");
      for (var j = 0; j < btns.length; j++) {
        var t = (btns[j].textContent || "").replace(/\s+/g, " ").trim();
        if (/^(✓\s*)?OK$/i.test(t)) { btns[j].style.display = "none"; }
      }
    }

    /* POZOR: pruh se nejen zaklada, ale i PREPISUJE. Prvni volani ukaze
     * "Zjistuji…", druhe (po odpovedi serveru) skutecny duvod. Kdyz se text
     * neprepsal, uzivatel by navzdy koukal na "Zjistuji…" — realna chyba
     * z prvni verze, overena v prohlizeci 30.7.2026. */
    var bar = host.querySelector(".mzdy-pripl-lock");
    if (!bar) {
      bar = document.createElement("div");
      bar.className = "mzdy-pripl-lock";
      bar.style.cssText = "padding:7px 10px;margin:0 0 10px 0;background:#fff7ed;"
        + "border:1px solid #fed7aa;border-radius:8px;color:#7c2d12;font-size:12.5px;line-height:1.35;";
      host.insertBefore(bar, host.firstChild);
    }
    bar.textContent = zprava;
  }

  /* --- Schvalovaci kolecko ------------------------------------------------
   * Tlacitka NEmeni stav primo v datech — volaji /app/pripl/workflow, ktery si
   * sam overi prava a sam zapise "kdo a kdy". Prohlizec posila jen "co chci
   * udelat", nikdy ne "schvalila Petra". Server take rozhodne, jestli akce
   * v danem stavu vubec dava smysl — tady jen schovavame, co nema smysl nabizet.
   */
  var WF_URL = "/api/v1/erp/app/pripl/workflow";
  var AKCE = [
    { kod: "navrhnout", popis: "📤 Odeslat ke schválení", stavy: ["draft", "rejected"], barva: "#2563eb" },
    { kod: "schvalit",  popis: "✅ Schválit",             stavy: ["pending"],           barva: "#16a34a" },
    { kod: "vratit",    popis: "↩️ Vrátit k přepracování", stavy: ["pending", "approved"], barva: "#b45309" }
  ];

  function _stavZaznamu(inst) {
    try { return String((inst._spec.data || {}).status || ""); } catch (e) { return ""; }
  }
  function _idZaznamu(inst) {
    try {
      var d = inst._spec.data || {};
      return (d.id != null) ? d.id : (inst.opts && inst.opts.rowId);
    } catch (e) { return null; }
  }

  function _pridejTlacitka(inst) {
    var host = (inst._shell || {}).body;
    if (!host) return;
    var stary = host.querySelector(".mzdy-pripl-wf");
    if (stary && stary.parentNode) stary.parentNode.removeChild(stary);

    var stav = _stavZaznamu(inst);
    var id = _idZaznamu(inst);
    if (id == null) return;
    /* Archiv z Centraly se nehybe — server to stejne odmitne, ale at to uzivatel
     * vubec nevidi jako nabidku. */
    if (stav === "archiv") return;

    var lista = document.createElement("div");
    lista.className = "mzdy-pripl-wf";
    lista.style.cssText = "display:flex;gap:8px;flex-wrap:wrap;padding:8px 10px;margin:0 0 10px 0;"
      + "background:#f5f7fa;border:1px solid #e2e8f0;border-radius:8px;";

    var pridano = 0;
    AKCE.forEach(function (a) {
      if (a.stavy.indexOf(stav) < 0) return;
      pridano++;
      var b = document.createElement("button");
      b.type = "button";
      b.textContent = a.popis;
      b.style.cssText = "cursor:pointer;padding:6px 12px;border:1px solid " + a.barva
        + ";border-radius:6px;background:#fff;color:" + a.barva + ";font-size:13px;line-height:1.2;";
      b.onclick = function () {
        var puvodni = b.textContent;
        b.disabled = true; b.textContent = "…";
        fetch(WF_URL, {
          method: "POST", credentials: "same-origin",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ id: id, akce: a.kod })
        }).then(function (r) {
          return r.json().then(function (j) { return { ok: r.ok, j: j }; });
        }).then(function (o) {
          if (!o.j || !o.j.ok) {
            global.alert((o.j && o.j.error) || "Akce se nepodařila.");
            b.disabled = false; b.textContent = puvodni;
            return;
          }
          try { if (typeof inst._reloadSpec === "function") { inst._reloadSpec(); } } catch (e) {}
        }).catch(function (e) {
          global.alert("Chyba spojení: " + (e && e.message ? e.message : e));
          b.disabled = false; b.textContent = puvodni;
        });
      };
      lista.appendChild(b);
    });

    if (!pridano) return;
    host.insertBefore(lista, host.firstChild);
  }

  function _apply(inst) {
    if (_coreCode(inst) !== CORE_CODE) return;

    /* Zamkni HNED, jeste nez se dozvime stav. Kdyz dotaz spadne nebo se opozdi,
     * formular zustane zamceny — ne otevreny. */
    _lock(inst, "🔒 Zjišťuji, jestli je zadávání odemknuté…");

    fetch(STAV_URL, { credentials: "same-origin" })
      .then(function (r) { return r.json(); })
      .then(function (j) {
        if (j && j.ok && j.odemceno) {
          _unlock(inst);
          if (j.zkusebni) { _zkusebniPruh(inst); }
          try { _pridejTlacitka(inst); } catch (e) {
            if (global.console) global.console.error("[mzdy-pripl-wf]", e);
          }
          return;
        }
        var chybi = (j && j.chybi && j.chybi.length)
          ? " Chybí: " + j.chybi.join("; ") + "."
          : "";
        var datum = (j && j.cilove_datum) ? (" Plánované přepnutí: " + j.cilove_datum + ".") : "";
        _lock(inst,
          "🔒 Jen ke čtení — zadávání příplatků a srážek ve STRATEGII "
          + "ještě není odemknuté. Zadávej dál v Centrále." + datum + chybi);
      })
      .catch(function () {
        _lock(inst,
          "🔒 Jen ke čtení — nepodařilo se zjistit stav přepnutí, "
          + "takže formulář nechávám zámknutý. Zkus to prosím znovu.");
      });
  }

  /* Zkusebni rezim: formular je otevreny, ale JEN na zkousku. Vse, co tu vznikne,
   * ma na serveru import_src='TEST' a do mzdy to nejde. Uzivatel to MUSI vedet,
   * jinak by si mysel, ze uz zadava ostre. */
  function _zkusebniPruh(inst) {
    var host = (inst._shell || {}).body;
    if (!host) return;
    if (host.querySelector(".mzdy-pripl-test")) return;
    var bar = document.createElement("div");
    bar.className = "mzdy-pripl-test";
    bar.textContent = "🧪 Zkušební režim — tohle je jen na vyzkoušení. "
      + "Co tu založíš, se do mzdy nedostane a po zkoušce to smažeme. "
      + "Ostré příplatky zadávej zatím dál v Centrále.";
    bar.style.cssText = "padding:7px 10px;margin:0 0 10px 0;background:#eff6ff;"
      + "border:1px solid #93c5fd;border-radius:8px;color:#1e3a8a;font-size:12.5px;line-height:1.35;";
    host.insertBefore(bar, host.firstChild);
  }

  /* Odemceno: vrat pole a OK, sundej pruh. */
  function _unlock(inst) {
    var shell = inst._shell || {};
    var host = shell.body;
    if (!host) return;
    var els = host.querySelectorAll("input, textarea, select");
    for (var i = 0; i < els.length; i++) {
      try { els[i].disabled = false; } catch (e) {}
    }
    if (shell.dialog) {
      var btns = shell.dialog.querySelectorAll("button");
      for (var j = 0; j < btns.length; j++) {
        var t = (btns[j].textContent || "").replace(/\s+/g, " ").trim();
        if (/^(✓\s*)?OK$/i.test(t)) { btns[j].style.display = ""; }
      }
    }
    var old = host.querySelector(".mzdy-pripl-lock");
    if (old && old.parentNode) { old.parentNode.removeChild(old); }
  }

  function _install() {
    var F = global.DesignFwForm;
    if (!F || !F.prototype) return false;
    if (F.prototype.__mzdyPriplWrapped) return true;
    var origRender = F.prototype._render;
    if (typeof origRender !== "function") return false;
    F.prototype._render = function () {
      var r = origRender.apply(this, arguments);
      try { _apply(this); } catch (e) {
        if (global.console) global.console.error("[mzdy-pripl-lock]", e);
      }
      return r;
    };
    F.prototype.__mzdyPriplWrapped = true;
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
