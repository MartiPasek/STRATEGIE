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

    if (!host.querySelector(".mzdy-pripl-lock")) {
      var bar = document.createElement("div");
      bar.className = "mzdy-pripl-lock";
      bar.textContent = zprava;
      bar.style.cssText = "padding:7px 10px;margin:0 0 10px 0;background:#fff7ed;"
        + "border:1px solid #fed7aa;border-radius:8px;color:#7c2d12;font-size:12.5px;line-height:1.35;";
      host.insertBefore(bar, host.firstChild);
    }
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
