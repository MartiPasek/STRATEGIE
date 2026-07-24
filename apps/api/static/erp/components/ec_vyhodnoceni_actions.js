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

  function _rec(inst) { return (inst && inst._spec && inst._spec.data) || {}; }
  function _coreCode(inst) { try { return inst._spec.core.code; } catch (e) { return null; } }

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
