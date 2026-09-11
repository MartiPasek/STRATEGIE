/* ec_vyhodnoceni_prehled_refresh.js — tlacitko "Nacist z Centraly" nad prehledem
 * "Zakazky k vyhodnoceni" (fw.core id 199, dataset ec.vyhodnoceni_prehled).
 *
 * PROC (Kristy 11. 9. 2026): kdyz sefmonter v Centrale zaskrtne "vyhodnoceno
 * sefmonterem", u nas se zakazka objevi az po behu jobu `vyhodnoceni_sync` —
 * a ten jede JEDNOU ZA 60 MINUT. Dusan tedy musel cekat, nez mohl zakazku
 * vyhodnotit. Tohle mu da stejny import na povel.
 *
 * CO TO NENI: neni to "Obnovit". Obnovit znovu nacte data, ktera uz u nas jsou.
 * Tohle nejdriv stahne novinky z Centraly a AZ POTOM prehled obnovi.
 *
 * KAM SE VESI: do pruhu s hledanim nad gridem (`erp-grid-quickfilter`), vpravo.
 * Grid si ho stavi v `_init()`, takze se navesime za nej — stejny vzor jako
 * `ec_vyhodnoceni_actions.js` u jadra, jen nad jinou tridou.
 *
 * Vse defenzivne — nikdy nevyhodi do frameworku.
 */
(function (global) {
  "use strict";

  var CORE_ID = 199;                 // fw.core 'ec.vyhodnoceni_prehled'
  var TRIDA = "ec-vyh-prehled-sync";

  function _coreId(inst) {
    try { return inst.options.coreInfo.coreId; } catch (e) { return null; }
  }

  /* Po importu prehled obnovit. Tri urovne, od nejcistsi po nouzovou:
   * 1) `_makeRefreshFn` — tutez cestu pouziva tlacitko Obnovit, takze se
   *    zachova i oznaceny radek,
   * 2) klik na existujici tlacitko Obnovit v CRUD liste,
   * 3) reload stranky. */
  function _obnov(inst) {
    try {
      if (typeof inst._makeRefreshFn === "function" && inst.gridApi) {
        var fn = inst._makeRefreshFn(inst.gridApi);
        if (typeof fn === "function") { fn(); return true; }
      }
    } catch (e) {}
    try {
      var b = document.querySelector('.erp-grid-action-btn[data-action="refresh"]');
      if (b) { b.click(); return true; }
    } catch (e) {}
    try { global.location.reload(); } catch (e) {}
    return false;
  }

  function _klik(inst, btn) {
    var puvodni = btn.textContent;
    btn.disabled = true;
    btn.textContent = "⏳ Načítám z Centrály…";
    fetch("/api/v1/erp/app/erp_registry/run", {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ kod: "vyhodnoceni_prehled_sync", args: ["__uid__"] })
    }).then(function (r) {
      return r.json().then(function (j) { return { stav: r.status, j: j }; });
    }).then(function (o) {
      btn.disabled = false;
      btn.textContent = puvodni;
      var v = (o.j && o.j.vysledek) ? o.j.vysledek : o.j;
      if (!v || v.ok !== true) {
        global.alert("Načtení z Centrály se nepovedlo:\n\n" +
                     ((v && (v.chyba || v.error)) || ("HTTP " + o.stav)));
        return;
      }
      _obnov(inst);
      /* Hlasku ukazuju jen kdyz neco pribylo — pri kazdem kliknuti otravovat
       * oknem "0 novych" by bylo horsi nez nic. Kdyz nepribylo nic, da se to
       * poznat po tom, ze se prehled preblikl. */
      if (v.pribylo > 0) {
        global.alert("Z Centrály přibylo " + v.pribylo +
                     (v.pribylo === 1 ? " nová zakázka." : (v.pribylo < 5 ? " nové zakázky." : " nových zakázek.")));
      }
    }).catch(function (e) {
      btn.disabled = false;
      btn.textContent = puvodni;
      global.alert("Chyba spojení: " + (e && e.message ? e.message : e));
    });
  }

  function _inject(inst) {
    if (_coreId(inst) !== CORE_ID) return;
    var host = inst.quickFilterEl;
    if (!host) return;
    if (host.querySelector("." + TRIDA)) return;   // uz tam je

    var b = document.createElement("button");
    b.type = "button";
    b.className = TRIDA;
    b.textContent = "⬇️ Načíst z Centrály";
    b.title = "Stáhne z Centrály zakázky, které tam šéfmontér mezitím označil jako " +
              "vyhodnocené, a pak přehled obnoví. Bez toho se objeví až při pravidelné " +
              "synchronizaci (jednou za hodinu).";
    b.style.cssText = "margin-left:auto;padding:5px 12px;border:1px solid #bfdbfe;" +
      "border-radius:6px;background:#eff6ff;color:#1e3a8a;font-size:12px;font-weight:600;" +
      "line-height:1.2;white-space:nowrap;cursor:pointer;";
    b.onmouseenter = function () { b.style.background = "#dbeafe"; };
    b.onmouseleave = function () { b.style.background = "#eff6ff"; };
    b.onclick = function () { _klik(inst, b); };
    host.appendChild(b);
  }

  function _install() {
    var G = global.ErpDataGrid;
    if (!G || !G.prototype || G.prototype.__ecVyhPrehledWrapped) {
      return !!(G && G.prototype && G.prototype.__ecVyhPrehledWrapped);
    }
    var origInit = G.prototype._init;
    if (typeof origInit !== "function") return false;
    G.prototype._init = function () {
      var r = origInit.apply(this, arguments);
      var self = this;
      /* _init stavi quickFilterEl az v prubehu; injektuji na konci tiku,
       * at je element jiste v DOM. */
      setTimeout(function () {
        try { _inject(self); } catch (e) {
          if (global.console) global.console.error("[ec-vyh-prehled]", e);
        }
      }, 0);
      return r;
    };
    G.prototype.__ecVyhPrehledWrapped = true;
    return true;
  }

  if (!_install()) {
    var pokusy = 0;
    var iv = setInterval(function () {
      pokusy++;
      if (_install() || pokusy > 100) clearInterval(iv);
    }, 100);
  }
})(window);
