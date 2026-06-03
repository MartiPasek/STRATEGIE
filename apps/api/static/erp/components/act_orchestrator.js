/* act_orchestrator.js — FE orchestrátor FW Action Pipelines (Marti 3.6.).
 *
 * Tenký orchestrátor (logika „co dál" je v DB/executoru): spustí pipeline přes
 * /act/run, a dokud engine vrací status=paused + client_action (FE krok),
 * vykoná FE handler v prohlížeči a zavolá /act/resume s jeho result_code +
 * outputs. Opakuje, dokud done/error.
 *
 * FE handlery (běží tady): cell_trigger / open_core / grid_refresh.
 * BE handlery (db_insert/push/note_writeback) běží na serveru v executoru.
 *
 * Public: window.ActPipeline.run(pipelineCodeNeboId, context) -> Promise<finalState>
 */
(function () {
  function _boot() {
    var BASE = "/api/v1/erp/act";

    function postJSON(url, body) {
      return fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        cache: "no-store",
        body: JSON.stringify(body || {}),
      }).then(function (r) { return r.json(); });
    }

    // ── FE handlery ──────────────────────────────────────────────────
    var FE = {};

    // cell_trigger: kontext už přišel v run.context (spouštěč ho naplnil) —
    // jen potvrď a pokračuj.
    FE.cell_trigger = function () {
      return Promise.resolve({ result_code: "ok", outputs: {} });
    };

    // open_core: otevři DesignFwForm (jádro pro zápis), počkej na zavření.
    // saved -> closed_saved, jinak closed_cancel. Robustní: 30 min strop.
    FE.open_core = function (ca) {
      return new Promise(function (resolve) {
        var coreId = ca.params && ca.params.core_id;
        var rowId = ca.inputs && ca.inputs.rowId;
        if (typeof window.DesignFwForm !== "function" || coreId == null) {
          resolve({ result_code: "closed_cancel",
                    outputs: { detail: "DesignFwForm/core_id chybí" } });
          return;
        }
        var saved = false, savedNote = null;
        var fwf = new window.DesignFwForm({
          coreId: coreId, rowId: rowId,
          mode: (rowId != null ? "edit" : "create"),
          onSaveSuccess: function (resp) {
            saved = true;
            try {
              savedNote = (resp && (resp.poznamka
                || (resp.data && resp.data.poznamka))) || null;
            } catch (e) {}
          },
        });
        if (typeof fwf.open === "function") fwf.open();
        // detekce zavření přes root marker jádra
        var sel = '[data-design-fw-form-root="1"][data-design-fw-form-core-id="'
          + coreId + '"]';
        var t0 = Date.now();
        var iv = setInterval(function () {
          var stillOpen = !!document.querySelector(sel);
          if (!stillOpen) {
            clearInterval(iv);
            resolve({ result_code: (saved ? "closed_saved" : "closed_cancel"),
                      outputs: { rowId: rowId, note: savedNote, saved: saved } });
          } else if (Date.now() - t0 > 30 * 60 * 1000) {
            clearInterval(iv);
            resolve({ result_code: "closed_cancel", outputs: { detail: "timeout" } });
          }
        }, 400);
      });
    };

    // grid_refresh: best-effort obnova příslušného gridu (event + ErpGridActions).
    FE.grid_refresh = function (ca) {
      try {
        document.dispatchEvent(new CustomEvent("erp:pipeline-grid-refresh",
          { detail: (ca && ca.params) || {} }));
        if (window.ErpGridActions && typeof window.ErpGridActions.dispatch === "function"
            && ca && ca.params && ca.params.grid_code) {
          window.ErpGridActions.dispatch("refresh", { gridCode: ca.params.grid_code });
        }
      } catch (e) { /* nekritické */ }
      return Promise.resolve({ result_code: "ok", outputs: {} });
    };

    // ── orchestrátor: run + resume smyčka ────────────────────────────
    function run(pipeline, context) {
      return postJSON(BASE + "/run", { pipeline: pipeline, context: context || {} })
        .then(function step(res) {
          if (!res || res.status !== "paused" || !res.client_action) return res;
          var ca = res.client_action;
          var token = res.resume_token;
          var h = FE[ca.handler];
          var hp = h ? h(ca) : Promise.resolve({ result_code: "ok", outputs: {} });
          return hp.catch(function (e) {
            return { result_code: "error",
                     outputs: { detail: String((e && e.message) || e) } };
          }).then(function (r) {
            return postJSON(BASE + "/resume", {
              resume_token: token,
              result_code: r.result_code,
              outputs: r.outputs || {},
            }).then(step);
          });
        });
    }

    window.ActPipeline = { run: run, FE: FE };
    try {
      console.log("[ActPipeline] orchestrator ready (FE: cell_trigger, open_core, grid_refresh)");
    } catch (e) {}
  }

  if (window._erpLoadModule) {
    window._erpLoadModule("act_orchestrator.js", "v1.0.0", _boot);
  } else {
    _boot();
  }
})();
