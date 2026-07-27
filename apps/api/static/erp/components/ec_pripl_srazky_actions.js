/* ec_pripl_srazky_actions.js — akcni lista pro jadro "Priplatek / srazka".
 * Wrapuje DesignFwForm.prototype._render: po renderu jadra (core code
 * 'ec.pripl_srazky_jadro') vlozi listu tlacitek volajicich
 * POST /api/v1/erp/action/run (ec.pripl_srazky_* funkce).
 * Autor: Claude-27, 21.7.2026. Vse defenzivne — nikdy nevyhodi do frameworku.
 */
(function (global) {
  "use strict";

  var CORE_CODE = "ec.pripl_srazky_jadro";

  /* ⚠️ TLACITKA JSOU ZAMERNE VYPNUTA (Claude-28 / Jirka, 22.7.2026).
   * Duvod (verdikt Marti-AI msg 11066): ec.pripl_srazky je od 22.7. ZIVE zrcadlo
   * Centraly (job "sync_pripl_srazky_ec", 1x za hodinu, jednosmerne EC -> STRATEGIE).
   * Tahle tlacitka zapisuji POUZE do naseho zrcadla, takze by: (a) je pri prvnim
   * dalsim syncu prepsal stav z Centraly, (b) se zmena nikdy nedostala do mezd
   * (mzdu pocita Helios z dat Centraly). Schvaluje a vyplaci se dal v Centrale.
   *
   * ZAPNOUT AZ TEHDY, kdyz bude hotovy zpetny zapis do EC_FinPriplatkySrazkyDefinice
   * NEBO kdyz modul presedla na tenant.wage_movement. Zpetny zapis do mzdovych dat
   * Centraly musi podle Marti-AI odsouhlasit OSOBNE Marti Pasek (pravni dopad;
   * rizika: PrenesDoMezd, prescasove konto, kontroly integrity Centraly).
   * Kod nechavame kompletni — staci prepnout ENABLED na true. */
  var ENABLED = false;

  /* 🔒 ZAMEK NA CTENI (Claude-28 / Jirka, 27.7.2026).
   * Ze stejneho duvodu jako vypnuta tlacitka: `ec.pripl_srazky` je zive
   * jednosmerne zrcadlo Centraly. Formular byl doted plne editovatelny vcetne
   * tlacitka OK — uzivatel mohl prepsat castku/schvaleni, ulozilo by se to JEN
   * k nam a nejblizsi hodinovy sync by to prepsal zpet (a do mezd by se to
   * nikdy nedostalo). Proto pole zamykame a OK schovavame; Storno/zavrit
   * zustava. Vypnout = READ_ONLY na false (az bude rozhodnuty smer dat). */
  var READ_ONLY = true;
  var LOCK_NOTE = "🔒 Jen ke čtení — data se každou hodinu načítají z Centrály. "
                + "Schvaluje a vyplácí se dál v Centrále (Helios počítá mzdu z jejích dat).";

  var ACTIONS = [
    { code: "pripl_schvalit", mode: 1, label: "✅ Schválit", confirm: null },
    { code: "pripl_schvalit", mode: 2, label: "↩️ Zrušit schválení", confirm: "Zrušit schválení tohoto příplatku/srážky?" },
    { code: "pripl_vyplatit", mode: 1, label: "💸 Vyplatit", confirm: "Označit jako vyplacené (nastaví datum vyplacení)?" },
    { code: "pripl_vyplatit", mode: 2, label: "↩️ Zrušit vyplacení", confirm: "Zrušit vyplacení tohoto příplatku/srážky?" }
  ];

  function _rec(inst) { return (inst && inst._spec && inst._spec.data) || {}; }
  function _coreCode(inst) { try { return inst._spec.core.code; } catch (e) { return null; } }

  function _run(inst, act, btn) {
    var rec = _rec(inst);
    var id = (rec.id != null) ? rec.id : (inst.opts && inst.opts.rowId);
    if (id == null) { global.alert("Není načtený záznam."); return; }
    if (act.confirm && !global.confirm(act.confirm)) return;
    var old = btn.textContent;
    btn.disabled = true; btn.textContent = "…";
    fetch("/api/v1/erp/action/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action_code: act.code, id: id, mode: act.mode })
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
    if (!ENABLED) return;
    if (_coreCode(inst) !== CORE_CODE) return;
    var host = inst._shell && inst._shell.body;
    if (!host) return;
    var old = host.querySelector(".ec-pripl-actionbar");
    if (old && old.parentNode) old.parentNode.removeChild(old);
    var bar = document.createElement("div");
    bar.className = "ec-pripl-actionbar";
    bar.style.cssText = "display:flex;gap:8px;flex-wrap:wrap;padding:8px 10px;margin:0 0 10px 0;background:#f5f7fa;border:1px solid #e2e8f0;border-radius:8px;";
    ACTIONS.forEach(function (act) {
      var b = document.createElement("button");
      b.type = "button";
      b.textContent = act.label;
      b.style.cssText = "cursor:pointer;padding:6px 12px;border:1px solid #cbd5e1;border-radius:6px;background:#fff;font-size:13px;line-height:1.2;";
      b.onmouseenter = function () { b.style.background = "#eef2ff"; };
      b.onmouseleave = function () { b.style.background = "#fff"; };
      b.onclick = function () { _run(inst, act, b); };
      bar.appendChild(b);
    });
    host.insertBefore(bar, host.firstChild);
  }

  /* Zamkne jadro na cteni: pole disabled, OK schovane, nahore informacni pruh.
   * Vse defenzivne — kdyz se struktura shellu zmeni, jen se nic nestane. */
  function _lock(inst) {
    if (!READ_ONLY) return;
    if (_coreCode(inst) !== CORE_CODE) return;
    var shell = inst._shell || {};
    var host = shell.body;
    if (!host) return;

    var els = host.querySelectorAll("input, textarea, select, button");
    for (var i = 0; i < els.length; i++) {
      try { els[i].disabled = true; } catch (e) {}
      try { els[i].setAttribute("readonly", "readonly"); } catch (e) {}
    }

    /* OK (ulozit) schovat. Pozor: tlacitka NEJSOU v .erp-modal-footer, ale
     * v .erp-design-grid uvnitr dialogu (overeno v prohlizeci 27.7.2026),
     * proto hledame v celem dialogu. Storno/zavrit zustava. */
    if (shell.dialog) {
      var btns = shell.dialog.querySelectorAll("button");
      for (var j = 0; j < btns.length; j++) {
        var t = (btns[j].textContent || "").replace(/\s+/g, " ").trim();
        if (/^(✓\s*)?OK$/i.test(t)) { btns[j].style.display = "none"; }
      }
    }

    if (!host.querySelector(".ec-pripl-rolock")) {
      var bar = document.createElement("div");
      bar.className = "ec-pripl-rolock";
      bar.textContent = LOCK_NOTE;
      bar.style.cssText = "padding:7px 10px;margin:0 0 10px 0;background:#fff7ed;"
        + "border:1px solid #fed7aa;border-radius:8px;color:#7c2d12;font-size:12.5px;line-height:1.35;";
      host.insertBefore(bar, host.firstChild);
    }
  }

  function _install() {
    var F = global.DesignFwForm;
    if (!F || !F.prototype || F.prototype.__ecPriplWrapped) return !!(F && F.prototype && F.prototype.__ecPriplWrapped);
    var origRender = F.prototype._render;
    if (typeof origRender !== "function") return false;
    F.prototype._render = function () {
      var r = origRender.apply(this, arguments);
      try { _inject(this); } catch (e) { if (global.console) global.console.error("[ec-pripl-actions]", e); }
      try { _lock(this); } catch (e2) { if (global.console) global.console.error("[ec-pripl-rolock]", e2); }
      return r;
    };
    F.prototype.__ecPriplWrapped = true;
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
