/* eslint-disable */
/**
 * action_card.js — FW UI Kit: ErpActionCard + grafický přehled pipeline.
 * ─────────────────────────────────────────────────────────────────────────────
 * Marti 3.6.2026 (prezentace IT šéfům EUROSOFT/INTERSOFT):
 *   "vytvor novou komponentu pro action, kterou dokazeme podobne jako button
 *    poskladat podle kroku pod sebe a zobrazit na ni adekvatni udaje."
 *
 * ErpActionCard = jedna akční karta (krok pipeline). Skládá se pod sebe se
 * šipkovými konektory → vizuální pipeline. Zobrazuje: pořadí, název akce,
 * kontext (backend/frontend/sub-pipeline), kód handleru, popis, error_mode,
 * větvení (result_code → krok).
 *
 * Public API:
 *   new ErpActionCard(node, opts).render() → HTMLElement   (node = graf step)
 *   window.openPipelineGraph(ref)          → modal se stackem karet
 *   window.ErpPipelineGraph.renderInto(el, ref)  → render do elementu
 *
 * Data: GET /api/v1/erp/act/pipeline/{ref}/graph → {pipeline, steps[]}.
 * Wrapped v _erpLoadModule (Module Health visibility).
 */
"use strict";

(function (global) {
  "use strict";

  var _loader = (typeof global !== "undefined" && global._erpLoadModule)
    ? global._erpLoadModule
    : function (id, ver, fn) { try { fn(); } catch (e) { console.error("[" + id + "]", e); } };

  _loader("action_card.js", "v1.0.0", function () {

    // ── jednorázový CSS inject ──────────────────────────────────────────
    var STYLE_ID = "erp-action-card-style";
    function _injectStyle() {
      if (document.getElementById(STYLE_ID)) return;
      var s = document.createElement("style");
      s.id = STYLE_ID;
      s.textContent = [
        ".erp-pg-overlay{position:fixed;inset:0;background:rgba(8,12,18,.72);",
        "  z-index:100050;display:flex;align-items:flex-start;justify-content:center;",
        "  overflow:auto;padding:32px 16px;backdrop-filter:blur(2px);}",
        ".erp-pg-modal{background:#141b24;border:1px solid #2a3744;border-radius:12px;",
        "  width:min(560px,96vw);box-shadow:0 18px 60px rgba(0,0,0,.55);color:#e8eaed;}",
        ".erp-pg-head{padding:16px 20px;border-bottom:1px solid #243240;",
        "  display:flex;align-items:flex-start;gap:12px;}",
        ".erp-pg-head h3{margin:0;font-size:16px;font-weight:600;color:#fff;}",
        ".erp-pg-head .erp-pg-code{font:12px ui-monospace,Menlo,monospace;color:#7fb3e6;}",
        ".erp-pg-head .erp-pg-meta{margin-top:4px;font-size:11px;color:#8a98a6;}",
        ".erp-pg-x{margin-left:auto;cursor:pointer;border:none;background:transparent;",
        "  color:#8a98a6;font-size:20px;line-height:1;padding:2px 6px;border-radius:6px;}",
        ".erp-pg-x:hover{background:#243240;color:#fff;}",
        ".erp-pg-body{padding:18px 20px 24px;display:flex;flex-direction:column;align-items:center;}",
        ".erp-pg-conn{width:2px;height:18px;background:#3a4b5c;position:relative;}",
        ".erp-pg-conn::after{content:'';position:absolute;bottom:-1px;left:-4px;",
        "  border:5px solid transparent;border-top-color:#3a4b5c;}",
        ".erp-act-card{width:100%;background:#1b2530;border:1px solid #2c3a48;",
        "  border-left:4px solid #4a7ba8;border-radius:9px;padding:11px 13px;",
        "  display:flex;gap:11px;align-items:flex-start;transition:border-color .15s,transform .1s;}",
        ".erp-act-card:hover{border-color:#3d5b78;transform:translateY(-1px);}",
        ".erp-act-card.ctx-frontend{border-left-color:#9d7bd4;}",
        ".erp-act-card.ctx-backend{border-left-color:#4a7ba8;}",
        ".erp-act-card.ctx-sub{border-left-color:#d4954a;}",
        ".erp-act-card.ctx-empty{border-left-color:#5a6b7a;}",
        ".erp-act-num{flex:0 0 auto;width:26px;height:26px;border-radius:50%;",
        "  background:#0f1620;border:1px solid #34465a;color:#cfe0f0;font-size:13px;",
        "  font-weight:700;display:flex;align-items:center;justify-content:center;}",
        ".erp-act-main{flex:1 1 auto;min-width:0;}",
        ".erp-act-title{font-size:14px;font-weight:600;color:#fff;display:flex;",
        "  align-items:center;gap:8px;flex-wrap:wrap;}",
        ".erp-act-badge{font-size:10px;font-weight:600;padding:2px 7px;border-radius:10px;",
        "  white-space:nowrap;}",
        ".erp-act-badge.ctx-frontend{background:#2e2540;color:#c9aef0;}",
        ".erp-act-badge.ctx-backend{background:#1c3046;color:#9fd0f5;}",
        ".erp-act-badge.ctx-sub{background:#3a2c18;color:#f0c48a;}",
        ".erp-act-badge.ctx-empty{background:#28333d;color:#9aa8b6;}",
        ".erp-act-code{font:11px ui-monospace,Menlo,monospace;color:#7d8d9c;margin-top:2px;}",
        ".erp-act-desc{font-size:12px;color:#aab8c5;margin-top:5px;line-height:1.4;}",
        ".erp-act-foot{margin-top:8px;display:flex;gap:6px;flex-wrap:wrap;align-items:center;}",
        ".erp-act-chip{font-size:10px;padding:2px 7px;border-radius:6px;background:#222e39;",
        "  color:#9aa8b6;border:1px solid #2e3d4b;}",
        ".erp-act-chip.err{background:#2c1d1d;color:#e0a0a0;border-color:#4a2a2a;}",
        ".erp-act-chip.branch{background:#1d2c22;color:#a0d8b0;border-color:#2a4a35;}",
        ".erp-pg-empty{color:#8a98a6;font-size:13px;padding:20px;text-align:center;}",
      ].join("");
      document.head.appendChild(s);
    }

    var CTX_LABEL = {
      backend:  { badge: "🖥 Backend",      cls: "ctx-backend" },
      frontend: { badge: "🌐 Frontend",     cls: "ctx-frontend" },
      sub:      { badge: "🧩 Sub-pipeline", cls: "ctx-sub" },
    };
    function _ctxInfo(node) {
      var c = node && node.context;
      return CTX_LABEL[c] || { badge: "• " + (c || "neznámý"), cls: "ctx-empty" };
    }

    function _esc(v) {
      var d = document.createElement("div");
      d.textContent = (v == null ? "" : String(v));
      return d.innerHTML;
    }

    // ── ErpActionCard — jedna karta kroku ───────────────────────────────
    function ErpActionCard(node, opts) {
      this.node = node || {};
      this.opts = opts || {};
    }
    ErpActionCard.prototype.render = function () {
      _injectStyle();
      var n = this.node;
      var ci = _ctxInfo(n);
      var card = document.createElement("div");
      card.className = "erp-act-card " + ci.cls;

      var num = document.createElement("div");
      num.className = "erp-act-num";
      num.textContent = (n.step_no != null ? n.step_no : "•");
      card.appendChild(num);

      var main = document.createElement("div");
      main.className = "erp-act-main";

      var title = document.createElement("div");
      title.className = "erp-act-title";
      title.innerHTML = _esc(n.title || n.action_code || ("krok " + n.step_no)) +
        '<span class="erp-act-badge ' + ci.cls + '">' + _esc(ci.badge) + "</span>";
      main.appendChild(title);

      if (n.action_code) {
        var code = document.createElement("div");
        code.className = "erp-act-code";
        code.textContent = n.action_code +
          (n.handler ? "  ·  " + n.handler : "");
        main.appendChild(code);
      }

      if (n.description) {
        var desc = document.createElement("div");
        desc.className = "erp-act-desc";
        desc.textContent = n.description;
        main.appendChild(desc);
      }

      var foot = document.createElement("div");
      foot.className = "erp-act-foot";
      var em = document.createElement("span");
      em.className = "erp-act-chip" + (n.error_mode === "stop" ? " err" : "");
      em.textContent = "error: " + (n.error_mode || "stop");
      foot.appendChild(em);
      (n.branches || []).forEach(function (b) {
        var ch = document.createElement("span");
        ch.className = "erp-act-chip branch";
        ch.textContent = (b.result_code || "?") + " → " +
          (b.next_step_no != null ? ("krok " + b.next_step_no) : "konec");
        foot.appendChild(ch);
      });
      main.appendChild(foot);

      card.appendChild(main);
      return card;
    };

    // ── stack renderer (karty pod sebe + konektory) ─────────────────────
    function _renderStack(container, data) {
      _injectStyle();
      container.innerHTML = "";
      var steps = (data && data.steps) || [];
      if (!steps.length) {
        var e = document.createElement("div");
        e.className = "erp-pg-empty";
        e.textContent = "Pipeline nemá žádné kroky.";
        container.appendChild(e);
        return;
      }
      steps.forEach(function (st, i) {
        container.appendChild(new ErpActionCard(st).render());
        if (i < steps.length - 1) {
          var conn = document.createElement("div");
          conn.className = "erp-pg-conn";
          container.appendChild(conn);
        }
      });
    }

    function renderInto(el, ref) {
      _injectStyle();
      el.innerHTML = '<div class="erp-pg-empty">Načítám graf…</div>';
      return fetch("/api/v1/erp/act/pipeline/" + encodeURIComponent(ref) + "/graph",
                   { credentials: "include" })
        .then(function (r) { return r.json(); })
        .then(function (j) {
          if (!j || !j.ok) {
            el.innerHTML = '<div class="erp-pg-empty">Chyba: ' +
              _esc((j && j.error) || "neznámá") + "</div>";
            return null;
          }
          _renderStack(el, j);
          return j;
        })
        .catch(function (e) {
          el.innerHTML = '<div class="erp-pg-empty">Síťová chyba: ' + _esc(e && e.message) + "</div>";
          return null;
        });
    }

    // ── modal launcher ──────────────────────────────────────────────────
    function openPipelineGraph(ref) {
      _injectStyle();
      var ov = document.createElement("div");
      ov.className = "erp-pg-overlay";
      var modal = document.createElement("div");
      modal.className = "erp-pg-modal";
      modal.innerHTML =
        '<div class="erp-pg-head">' +
        '  <div><h3>Pipeline</h3><div class="erp-pg-code"></div>' +
        '    <div class="erp-pg-meta"></div></div>' +
        '  <button class="erp-pg-x" title="Zavřít">×</button>' +
        '</div><div class="erp-pg-body"></div>';
      ov.appendChild(modal);

      function close() {
        document.removeEventListener("keydown", onKey);
        if (ov.parentNode) ov.parentNode.removeChild(ov);
      }
      function onKey(e) { if (e.key === "Escape") close(); }
      modal.querySelector(".erp-pg-x").addEventListener("click", close);
      ov.addEventListener("click", function (e) { if (e.target === ov) close(); });
      document.addEventListener("keydown", onKey);

      document.body.appendChild(ov);
      var body = modal.querySelector(".erp-pg-body");
      renderInto(body, ref).then(function (j) {
        if (!j || !j.pipeline) return;
        var p = j.pipeline;
        modal.querySelector(".erp-pg-head h3").textContent = p.name || p.code || ("pipeline #" + p.id);
        modal.querySelector(".erp-pg-code").textContent = p.code + "  ·  v" + (p.version || 1);
        modal.querySelector(".erp-pg-meta").textContent =
          (p.step_count || (j.steps || []).length) + " kroků  ·  error_mode: " +
          (p.error_mode || "stop") + "  ·  status: " + (p.status || "—") +
          (p.description ? "  ·  " + p.description : "");
      });
    }

    global.ErpActionCard = ErpActionCard;
    global.ErpPipelineGraph = { renderInto: renderInto, render: _renderStack };
    global.openPipelineGraph = openPipelineGraph;

    console.log("[ErpActionCard] registered (v1.0.0) — openPipelineGraph ready");
  });
})(window);
