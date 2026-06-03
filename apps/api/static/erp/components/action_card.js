/* eslint-disable */
/**
 * action_card.js — FW UI Kit: ErpActionCard + grafický přehled pipeline.
 * ─────────────────────────────────────────────────────────────────────────────
 * Marti 3.6.2026 (prezentace IT šéfům EUROSOFT/INTERSOFT):
 *   "vytvor novou komponentu pro action, kterou dokazeme podobne jako button
 *    poskladat podle kroku pod sebe a zobrazit na ni adekvatni udaje."
 *   + "na klik te action vedle otevrit okno s nastavenim parameru, aby bylo
 *      videt, co ktery krok fyzicky dela."
 *   + "Melo by to byt jedno okno a klikem na action jen menit jeho obsah."
 *
 * → JEDNO okno. Akční karty pod sebou (graf). Klik na kartu ji ROZBALÍ inline
 *   a ukáže, co krok fyzicky dělá (handler, vstupy/input_mapping, params,
 *   schémata, timeout, idempotence, větvení). Klik na jinou přepne (akordeon).
 *
 * Public API:
 *   new ErpActionCard(node, opts).render() → HTMLElement
 *   window.openPipelineGraph(ref)          → modal (jedno okno, akordeon)
 *   window.ErpPipelineGraph.renderInto(el, ref)
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

  _loader("action_card.js", "v1.2.0", function () {

    var STYLE_ID = "erp-action-card-style";
    function _injectStyle() {
      if (document.getElementById(STYLE_ID)) return;
      var s = document.createElement("style");
      s.id = STYLE_ID;
      s.textContent = [
        ".erp-pg-overlay{position:fixed;inset:0;background:rgba(8,12,18,.72);",
        "  z-index:100050;display:flex;align-items:flex-start;justify-content:center;",
        "  overflow:auto;padding:30px 16px;backdrop-filter:blur(2px);}",
        ".erp-pg-modal{background:#141b24;border:1px solid #2a3744;border-radius:12px;",
        "  width:min(600px,96vw);box-shadow:0 18px 60px rgba(0,0,0,.55);color:#e8eaed;}",
        ".erp-pg-head{padding:15px 20px;border-bottom:1px solid #243240;",
        "  display:flex;align-items:flex-start;gap:12px;}",
        ".erp-pg-head h3{margin:0;font-size:16px;font-weight:600;color:#fff;}",
        ".erp-pg-head .erp-pg-code{font:12px ui-monospace,Menlo,monospace;color:#7fb3e6;margin-top:2px;}",
        ".erp-pg-head .erp-pg-meta{margin-top:4px;font-size:11px;color:#8a98a6;}",
        ".erp-pg-x{margin-left:auto;cursor:pointer;border:none;background:transparent;",
        "  color:#8a98a6;font-size:20px;line-height:1;padding:2px 6px;border-radius:6px;}",
        ".erp-pg-x:hover{background:#243240;color:#fff;}",
        ".erp-pg-body{padding:18px 20px 24px;display:flex;flex-direction:column;",
        "  align-items:center;max-height:74vh;overflow:auto;}",
        ".erp-pg-conn{width:2px;height:16px;background:#3a4b5c;position:relative;flex:0 0 auto;}",
        ".erp-pg-conn::after{content:'';position:absolute;bottom:-1px;left:-4px;",
        "  border:5px solid transparent;border-top-color:#3a4b5c;}",
        ".erp-act-card{width:100%;background:#1b2530;border:1px solid #2c3a48;",
        "  border-left:4px solid #4a7ba8;border-radius:9px;",
        "  transition:border-color .15s,box-shadow .15s;}",
        ".erp-act-card.ctx-frontend{border-left-color:#9d7bd4;}",
        ".erp-act-card.ctx-backend{border-left-color:#4a7ba8;}",
        ".erp-act-card.ctx-sub{border-left-color:#d4954a;}",
        ".erp-act-card.ctx-empty{border-left-color:#5a6b7a;}",
        ".erp-act-card.expanded{border-color:#5b8fc0;box-shadow:0 0 0 2px rgba(91,143,192,.30);}",
        ".erp-act-head{padding:11px 13px;display:flex;gap:11px;align-items:flex-start;",
        "  cursor:pointer;}",
        ".erp-act-head:hover .erp-act-title{color:#cfe6ff;}",
        ".erp-act-num{flex:0 0 auto;width:26px;height:26px;border-radius:50%;",
        "  background:#0f1620;border:1px solid #34465a;color:#cfe0f0;font-size:13px;",
        "  font-weight:700;display:flex;align-items:center;justify-content:center;}",
        ".erp-act-main{flex:1 1 auto;min-width:0;}",
        ".erp-act-title{font-size:14px;font-weight:600;color:#fff;display:flex;",
        "  align-items:center;gap:8px;flex-wrap:wrap;}",
        ".erp-act-chev{margin-left:auto;color:#6b7a88;font-size:12px;transition:transform .15s;}",
        ".erp-act-card.expanded .erp-act-chev{transform:rotate(90deg);color:#9fd0f5;}",
        ".erp-act-badge{font-size:10px;font-weight:600;padding:2px 7px;border-radius:10px;white-space:nowrap;}",
        ".erp-act-badge.ctx-frontend{background:#2e2540;color:#c9aef0;}",
        ".erp-act-badge.ctx-backend{background:#1c3046;color:#9fd0f5;}",
        ".erp-act-badge.ctx-sub{background:#3a2c18;color:#f0c48a;}",
        ".erp-act-badge.ctx-empty{background:#28333d;color:#9aa8b6;}",
        ".erp-act-code{font:11px ui-monospace,Menlo,monospace;color:#7d8d9c;margin-top:2px;}",
        ".erp-act-foot{margin-top:7px;display:flex;gap:6px;flex-wrap:wrap;align-items:center;}",
        ".erp-act-chip{font-size:10px;padding:2px 7px;border-radius:6px;background:#222e39;",
        "  color:#9aa8b6;border:1px solid #2e3d4b;}",
        ".erp-act-chip.err{background:#2c1d1d;color:#e0a0a0;border-color:#4a2a2a;}",
        ".erp-act-chip.branch{background:#1d2c22;color:#a0d8b0;border-color:#2a4a35;}",
        // rozbalený obsah (inline detail)
        ".erp-act-detail{display:none;padding:4px 14px 14px 50px;}",
        ".erp-act-card.expanded .erp-act-detail{display:block;}",
        ".erp-d-sec{margin-top:13px;}",
        ".erp-d-h{font-size:10px;text-transform:uppercase;letter-spacing:.6px;color:#7d8d9c;",
        "  margin:0 0 7px;border-bottom:1px solid #243240;padding-bottom:4px;}",
        ".erp-d-kv{display:grid;grid-template-columns:max-content 1fr;gap:5px 12px;font-size:12px;}",
        ".erp-d-k{color:#8a98a6;}",
        ".erp-d-v{color:#dfe6ec;word-break:break-word;}",
        ".erp-d-v.mono{font-family:ui-monospace,Menlo,monospace;color:#cfe0f0;}",
        ".erp-d-map{display:flex;flex-direction:column;gap:6px;}",
        ".erp-d-maprow{display:flex;gap:8px;align-items:baseline;font-size:12px;}",
        ".erp-d-mapk{color:#9fd0f5;font-family:ui-monospace,Menlo,monospace;font-weight:600;}",
        ".erp-d-mapv{color:#bcc8d4;}",
        ".erp-d-pre{background:#0f1620;border:1px solid #243240;border-radius:6px;padding:9px 10px;",
        "  font:11px ui-monospace,Menlo,monospace;color:#cfe0f0;white-space:pre-wrap;",
        "  overflow:auto;margin:0;max-height:200px;}",
        ".erp-d-muted{color:#6b7a88;font-size:12px;font-style:italic;margin-top:10px;}",
        ".erp-pg-empty{color:#8a98a6;font-size:13px;padding:24px 8px;text-align:center;}",
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
    function _isEmpty(o) {
      if (o == null) return true;
      if (typeof o === "object") return Object.keys(o).length === 0;
      return String(o).trim() === "";
    }
    function _pretty(o) {
      try { return JSON.stringify(o, null, 2); } catch (e) { return String(o); }
    }

    // ── detail (rozbalený obsah karty) ──────────────────────────────────
    function _kvSection(title, pairs) {
      var present = pairs.filter(function (p) { return p[1] != null && p[1] !== ""; });
      if (!present.length) return "";
      var rows = present.map(function (p) {
        return '<div class="erp-d-k">' + _esc(p[0]) + '</div>' +
               '<div class="erp-d-v ' + (p[2] ? "mono" : "") + '">' + _esc(p[1]) + '</div>';
      }).join("");
      return '<div class="erp-d-sec"><div class="erp-d-h">' + _esc(title) +
             '</div><div class="erp-d-kv">' + rows + '</div></div>';
    }
    function _mapForm(spec) {
      if (spec && typeof spec === "object") {
        if ("const" in spec) return "= " + _pretty(spec.const) + "  (konstanta)";
        if ("context" in spec) return "← kontext: " + spec.context;
        if ("step" in spec) return "← krok " + spec.step + (spec.field ? " . " + spec.field : "  (výstup)");
        return _pretty(spec);
      }
      return "= " + _pretty(spec) + "  (konstanta)";
    }
    function _mapSection(title, mapping) {
      if (_isEmpty(mapping)) return "";
      var rows = Object.keys(mapping).map(function (k) {
        return '<div class="erp-d-maprow"><span class="erp-d-mapk">' + _esc(k) +
               '</span><span class="erp-d-mapv">' + _esc(_mapForm(mapping[k])) + '</span></div>';
      }).join("");
      return '<div class="erp-d-sec"><div class="erp-d-h">' + _esc(title) +
             '</div><div class="erp-d-map">' + rows + '</div></div>';
    }
    function _preSection(title, obj) {
      if (_isEmpty(obj)) return "";
      return '<div class="erp-d-sec"><div class="erp-d-h">' + _esc(title) +
             '</div><pre class="erp-d-pre">' + _esc(_pretty(obj)) + '</pre></div>';
    }
    function _branchSection(branches) {
      if (!branches || !branches.length) return "";
      var rows = branches.map(function (b) {
        return '<div class="erp-d-maprow"><span class="erp-d-mapk">' +
               _esc(b.result_code || "?") + '</span><span class="erp-d-mapv">→ ' +
               (b.next_step_no != null ? ("krok " + b.next_step_no) : "konec pipeline") +
               '</span></div>';
      }).join("");
      return '<div class="erp-d-sec"><div class="erp-d-h">Větvení (result_code → krok)' +
             '</div><div class="erp-d-map">' + rows + '</div></div>';
    }
    function _detailHtml(node) {
      var d = node.detail || {};
      var html = "";
      html += _kvSection("Akce", [
        ["Handler", node.handler || node.action_code, true],
        ["Typ", d.action_type, false],
        ["Kontext", node.context, false],
        ["Timeout", d.timeout_ms != null ? (d.timeout_ms + " ms") : null, false],
        ["Verze", d.action_version, false],
        ["Stav", d.action_status, false],
        ["error_mode", node.error_mode, false],
      ]);
      if (node.kind === "sub_pipeline") {
        html += _kvSection("Vnořená pipeline", [
          ["Code", d.sub_pipeline_code, true],
          ["ID", d.sub_pipeline_id, false],
        ]);
      }
      html += _mapSection("Vstupy (input_mapping)", d.input_mapping);
      html += _preSection("Parametry (params_schema)", d.params_schema);
      if (d.idempotency_key_template) {
        html += _kvSection("Idempotence", [["key_template", d.idempotency_key_template, true]]);
      }
      html += _preSection("Vstupní schéma", d.input_schema);
      html += _preSection("Výstupní schéma", d.output_schema);
      html += _branchSection(node.branches);
      if (_isEmpty(d.input_mapping) && _isEmpty(d.params_schema) &&
          _isEmpty(d.input_schema) && _isEmpty(d.output_schema) &&
          node.kind !== "sub_pipeline") {
        html += '<div class="erp-d-muted">Krok nemá parametry ani vstupní mapování — ' +
                'běží s pevnou logikou handleru.</div>';
      }
      return html;
    }

    // ── ErpActionCard — karta s rozbalitelným obsahem ───────────────────
    function ErpActionCard(node, opts) {
      this.node = node || {};
      this.opts = opts || {};
    }
    ErpActionCard.prototype.render = function () {
      _injectStyle();
      var n = this.node, self = this;
      var ci = _ctxInfo(n);
      var card = document.createElement("div");
      card.className = "erp-act-card " + ci.cls;
      this.el = card;

      var head = document.createElement("div");
      head.className = "erp-act-head";
      head.innerHTML =
        '<div class="erp-act-num">' + _esc(n.step_no != null ? n.step_no : "•") + '</div>' +
        '<div class="erp-act-main">' +
        '  <div class="erp-act-title">' + _esc(n.title || n.action_code || ("krok " + n.step_no)) +
        '    <span class="erp-act-badge ' + ci.cls + '">' + _esc(ci.badge) + '</span>' +
        '    <span class="erp-act-chev">▶</span></div>' +
        (n.action_code ? '<div class="erp-act-code">' + _esc(n.action_code) +
          (n.handler ? "  ·  " + _esc(n.handler) : "") + '</div>' : "") +
        '</div>';
      card.appendChild(head);

      var detail = document.createElement("div");
      detail.className = "erp-act-detail";
      detail.innerHTML = _detailHtml(n);
      card.appendChild(detail);

      head.addEventListener("click", function () {
        if (typeof self.opts.onToggle === "function") self.opts.onToggle(self);
      });
      return card;
    };
    ErpActionCard.prototype.setExpanded = function (on) {
      if (this.el) this.el.classList.toggle("expanded", !!on);
    };
    ErpActionCard.prototype.isExpanded = function () {
      return !!(this.el && this.el.classList.contains("expanded"));
    };

    // ── stack (jedno okno, akordeon) ────────────────────────────────────
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
      var cards = [];
      function toggle(card) {
        var willOpen = !card.isExpanded();
        cards.forEach(function (c) { c.setExpanded(c === card && willOpen); });
      }
      steps.forEach(function (st, i) {
        var c = new ErpActionCard(st, { onToggle: toggle });
        cards.push(c);
        container.appendChild(c.render());
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

    console.log("[ErpActionCard] registered (v1.2.0) — akordeon (jedno okno, klik rozbalí krok)");
  });
})(window);
