/* HR — přehled personalistiky jako band v ERP (jádro s kódem hr.prehled).
 * Vzor: crm_obchodnik_pult.js (band nad gridem). Rozdíl: HR pult renderuje celý
 * Pinya-styl dashboard (KPI + dlaždice + aktuality) a je hlavním obsahem stránky,
 * takže skryje prázdný grid placeholder pod sebou. Read-only, fail-safe.
 * page_render volá jen gated hook → window.HrPult.mount. (Claude-25 / Šárka 2.7.2026) */
(function () {
  "use strict";
  var EP = "/api/v1/erp/app/hr/dashboard";

  var TILES = [
    { ic: "✅", t: "Úkoly", d: "Moje HR úkoly a připomínky.", st: "live", act: "ukoly" },
    { ic: "🏖️", t: "Mimo kancelář", d: "Kdo dnes není ve firmě (absence + home office).", st: "live", act: "mimo" },
    { ic: "🎂", t: "Narozeniny a výročí", d: "Blížící se narozeniny a výročí nástupu.", st: "live" },
    { ic: "🚀", t: "Onboarding a nové nástupy", d: "Kdo už nastoupil (nováčci) a kdo teprve nastoupí.", st: "live" },
    { ic: "🧲", t: "Výběrová řízení", d: "Běžící nábor, editace, publikace (Teamio).", st: "live", go: "/recruit" },
    { ic: "🔔", t: "Notifikace", d: "Konce smluv, prohlídky, propadající školení.", st: "soon" },
    { ic: "✅", t: "Úkoly", d: "HR úkoly z jednoho místa.", st: "soon" },
    { ic: "🗓️", t: "Kalendář", d: "Události + import z Outlooku (na konec).", st: "soon" }
  ];

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c];
    });
  }

  // Skryj prázdný tmavý grid placeholder pod pultem (HR přehled = jen pult).
  function hideGridHost() {
    try {
      var g = document.querySelector('[id^="erp-page-grid-"]');
      if (g) { g.style.display = "none"; }
    } catch (e) { /* fail-safe */ }
  }

  function mount(el) {
    if (!el) return;
    hideGridHost();
    el.style.cssText = "background:#0f141a;padding:16px 18px;overflow:auto;flex:1 1 auto;min-height:0;";
    el.innerHTML =
      style() +
      '<div class="hrp-wrap">' +
      // 1) KPI statistiky (sloupce dle nadpisu s čísly)
      '  <div class="hrp-badges" id="hrpBadges"><div class="hrp-empty">Načítám…</div></div>' +
      // Šárka 12.8.2026: „Ve firmě" je v KPI; 5 vyrovnaných panelů v jedné mřížce (3+2);
      // Novinky hned pod nimi (viditelné); Úkoly jsou samostatný uzel (dlaždice „Úkoly").
      '  <div class="hrp-blocks hrp-cols3">' +
      '    <div class="hrp-panel">' +
      '      <div class="hrp-phd"><span class="hrp-pi">🏢</span> Aktuálně ve firmě <span class="hrp-cnt" id="hrpVeFirmeCnt"></span></div>' +
      '      <div id="hrpVeFirmeList"><div class="hrp-empty">Načítám…</div></div>' +
      '    </div>' +
      '    <div class="hrp-panel">' +
      '      <div class="hrp-phd"><span class="hrp-pi">🏖️</span> Mimo kancelář <span class="hrp-cnt" id="hrpMimoCnt"></span></div>' +
      '      <div id="hrpMimoList"><div class="hrp-empty">Načítám…</div></div>' +
      '    </div>' +
      '    <div class="hrp-panel">' +
      '      <div class="hrp-phd"><span class="hrp-pi">🎂</span> Narozeniny a výročí <span class="hrp-cnt" id="hrpJubCnt"></span></div>' +
      '      <div id="hrpJubList"><div class="hrp-empty">Načítám…</div></div>' +
      '    </div>' +
      '    <div class="hrp-panel">' +
      '      <div class="hrp-phd"><span class="hrp-pi">🚀</span> Onboarding <span class="hrp-cnt" id="hrpOnbCnt"></span></div>' +
      '      <div id="hrpOnbList"><div class="hrp-empty">Načítám…</div></div>' +
      '    </div>' +
      '    <div class="hrp-panel">' +
      '      <div class="hrp-phd"><span class="hrp-pi">🆕</span> Nové nástupy <span class="hrp-cnt" id="hrpNoviCnt"></span></div>' +
      '      <div id="hrpNoviList"><div class="hrp-empty">Načítám…</div></div>' +
      '    </div>' +
      '    <div class="hrp-panel">' +
      '      <div class="hrp-phd"><span class="hrp-pi">🧲</span> Výběrová řízení <span class="hrp-cnt" id="hrpVrCnt"></span></div>' +
      '      <div id="hrpVrList"><div class="hrp-empty">Načítám…</div></div>' +
      '    </div>' +
      '  </div>' +
      '  <div class="hrp-panel">' +
      '    <div class="hrp-phd"><span class="hrp-pi">📣</span> Novinky <a href="#" id="hrpNovNew" style="margin-left:12px;font-size:12px;color:#7fb2e8;text-decoration:none;font-weight:600">➕ Přidat</a></div>' +
      '    <div style="font-size:11.5px;color:#8fa6c4;margin:-4px 0 9px;line-height:1.5;">ℹ️ Informace pro zaměstnance — zobrazí se jim v mobilní aplikaci. Položky označené „🔒 Jen HR" zůstávají interní a do mobilu se neposílají.</div>' +
      '    <div id="hrpNovForm"></div>' +
      '    <div id="hrpNovList"><div class="hrp-empty">Načítám…</div></div>' +
      '  </div>' +
      '</div>';

    loadMimoPanel(el);
    loadJubilea(el);
    loadNovinky(el);

    fetch(EP, { credentials: "include" })
      .then(function (r) { return r.json().catch(function () { return {}; }); })
      .then(function (d) {
        var bEl = el.querySelector("#hrpBadges"), aEl = el.querySelector("#hrpAkt");
        if (!d || !d.ok) {
          bEl.innerHTML = '<div class="hrp-empty">Nemáš oprávnění nebo chyba: ' + esc(d && d.error || "") + '</div>';
          if (aEl) aEl.innerHTML = ""; return;
        }
        var b = d.badges || {};
        bEl.innerHTML =
          badge(0, "Aktuálně ve firmě", "vefirme", "hrpBadgeVeFirme") +
          badge(b.mimo, "Mimo kancelář", "mimo") +
          badge(b.naroz, "Narozeniny a výročí") +
          badge(0, "Onboarding", null, "hrpBadgeOnb") +
          badge(b.novi, "Nové nástupy", null, "hrpBadgeNovi") +
          badge(b.vyberka, "Výběrová řízení");
        var _mb = bEl.querySelector('[data-act="mimo"]');
        if (_mb) { _mb.onclick = openMimo; }
        var _vf = bEl.querySelector('[data-act="vefirme"]');
        if (_vf) { _vf.onclick = openVeFirme; }
        loadVeFirme(el);
        loadNovi(el);   // až po vykreslení odznaků — jinak KPI Onboarding/Nové nástupy přepíše badge render (race)
        renderVyberka(el, d.vyberka || {});
        if (aEl) {
          var akt = d.aktuality || [];
          aEl.innerHTML = akt.length ? akt.map(function (a) {
            var mil = (a.typ === "milnik" || a.typ === "vyroci_firmy");
            return '<div class="hrp-row' + (mil ? ' hrp-row-mil' : '') + '"><span class="hrp-ic">' + esc(a.ikona || "•") + '</span><span>' + esc(a.text) + '</span></div>';
          }).join("") : '<div class="hrp-empty">Žádné aktuality.</div>';
        }
      })
      .catch(function () {
        var bEl = el.querySelector("#hrpBadges");
        if (bEl) bEl.innerHTML = '<div class="hrp-empty">✗ síť</div>';
      });
  }

  var VEFIRME = { lide: [], ho: 0 };
  function loadVeFirme() {
    fetch('/api/v1/erp/app/hr/dnes-ve-firme', { credentials: 'include' })
      .then(function (r) { return r.json().catch(function () { return {}; }); })
      .then(function (d) {
        if (!d || !d.ok) return;
        VEFIRME.lide = d.lide || []; VEFIRME.ho = d.ho || 0;
        var b = document.getElementById('hrpBadgeVeFirme');
        if (b) b.textContent = VEFIRME.lide.length;
        var cnt = document.getElementById('hrpVeFirmeCnt');
        if (cnt) cnt.textContent = VEFIRME.lide.length ? ('· ' + VEFIRME.lide.length) : '';
        var list = document.getElementById('hrpVeFirmeList');
        if (list) {
          var hoNote = (VEFIRME.ho ? '<div style="padding:7px 4px 2px;color:#8fb4d8;font-size:11px">🏠 + ' + VEFIRME.ho + ' na home office</div>' : '');
          if (!VEFIRME.lide.length) { list.innerHTML = (hoNote || '<div class="hrp-empty">Dnes není nikdo v práci.</div>'); }
          else {
            list.innerHTML = VEFIRME.lide.map(function (p) {
              return '<div class="hrp-mrow"><span class="hrp-mic" style="background:#12301f;color:#5ee0b7">●</span>' +
                '<div style="min-width:0"><div class="hrp-mnm">' + esc(p.jmeno) + '</div>' +
                (p.pozice ? '<div class="hrp-mdv">' + esc(p.pozice) + '</div>' : '') + '</div></div>';
            }).join('') + hoNote;
          }
        }
      })
      .catch(function () {});
  }
  function openVeFirme() {
    var m = ensureModal(); m.classList.add('on');
    m.querySelector('.hrp-modal-card').classList.remove('hrp-modal-wide');
    m.querySelector('#hrpModalTitle').textContent = '🏢 Aktuálně ve firmě (' + VEFIRME.lide.length + ')';
    var h = VEFIRME.lide.map(function (p) {
      return '<div class="hrp-mrow"><span class="hrp-mic" style="background:#12301f;color:#5ee0b7">●</span>' +
        '<div><div class="hrp-mnm">' + esc(p.jmeno) + '</div>' +
        (p.pozice ? '<div class="hrp-mdv">' + esc(p.pozice) + '</div>' : '') + '</div></div>';
    }).join('');
    if (VEFIRME.ho) h += '<div style="padding:9px 12px;color:#8fb4d8;font-size:12px">🏠 + ' + VEFIRME.ho + ' na home office</div>';
    m.querySelector('#hrpModalBody').innerHTML = h || '<div class="hrp-empty">Dnes není nikdo v práci.</div>';
  }
  function openUkoly() {
    var m = ensureModal(); m.classList.add('on');
    m.querySelector('.hrp-modal-card').classList.remove('hrp-modal-wide');
    m.querySelector('#hrpModalTitle').textContent = '✅ Úkoly';
    m.querySelector('#hrpModalBody').innerHTML = '<div id="hrpUkoly"><div class="hrp-empty">Načítám…</div></div>';
    loadUkoly(m.querySelector('.hrp-modal-card'));
  }
  function novBadge(pro) {
    return pro === 'hr'
      ? '<span style="font-size:10px;font-weight:700;padding:1px 7px;border-radius:20px;background:#3a2a12;color:#e0a94a">🔒 Jen HR</span>'
      : '<span style="font-size:10px;font-weight:700;padding:1px 7px;border-radius:20px;background:#12304a;color:#7fb2e8">👁 Zaměstnanci</span>';
  }
  function novStav(it) {
    if (!it.aktivni) return '<span style="color:#8a97a8">neaktivní</span>';
    if (it.bezi) return '<span style="color:#5ee0b7">běží</span>';
    return '<span style="color:#e0a94a">naplánováno / prošlé</span>';
  }
  function novFormHtml(it) {
    it = it || {};
    var od = it.od || new Date().toISOString().slice(0, 10);
    var inp = 'background:#0f141a;border:1px solid #283645;border-radius:6px;color:#e8eef5;padding:5px 7px;font:inherit';
    return '<div style="background:#12181f;border:1px solid #24303c;border-radius:8px;padding:10px;margin-bottom:10px">' +
      '<input id="nvNadpis" placeholder="Nadpis (např. Vánoční večírek)" value="' + esc(it.nadpis || '') + '" style="width:100%;box-sizing:border-box;margin-bottom:6px;' + inp + '">' +
      '<textarea id="nvText" rows="2" placeholder="Text novinky…" style="width:100%;box-sizing:border-box;margin-bottom:6px;resize:vertical;' + inp + '">' + esc(it.text || '') + '</textarea>' +
      '<div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:6px">' +
        '<label style="font-size:12px;color:#8fa6c4">Pro koho <select id="nvPro" style="' + inp + '"><option value="zam"' + (it.pro === 'hr' ? '' : ' selected') + '>Zaměstnanci (do mobilu)</option><option value="hr"' + (it.pro === 'hr' ? ' selected' : '') + '>Jen HR (interní)</option></select></label>' +
        '<label style="font-size:12px;color:#8fa6c4">Platí od <input id="nvOd" type="date" value="' + esc(od) + '" style="' + inp + '"></label>' +
        '<label style="font-size:12px;color:#8fa6c4">do <input id="nvDo" type="date" value="' + esc(it.do || '') + '" style="' + inp + '"></label>' +
        '<label style="font-size:12px;color:#8fa6c4"><input id="nvDul" type="checkbox"' + (it.dulezite ? ' checked' : '') + '> důležité</label>' +
      '</div>' +
      '<div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:6px">' +
        '<label style="font-size:12px;color:#8fa6c4">Datum akce <input id="nvDatum" type="date" value="' + esc(it.datum_akce || '') + '" style="' + inp + '"></label>' +
        '<label style="font-size:12px;color:#8fa6c4">Čas <input id="nvCas" placeholder="18:00" value="' + esc(it.cas || '') + '" size="6" style="' + inp + '"></label>' +
        '<label style="font-size:12px;color:#8fa6c4">Místo <input id="nvMisto" placeholder="Hotel Panorama" value="' + esc(it.misto || '') + '" style="' + inp + '"></label>' +
        '<label style="font-size:12px;color:#8fa6c4"><input id="nvRsvp" type="checkbox"' + (it.rsvp ? ' checked' : '') + '> potvrzovat účast</label>' +
      '</div>' +
      '<div style="display:flex;gap:10px;align-items:center">' +
        '<button id="nvSave" style="border:1px solid #2a5a3a;background:#26603a;color:#e8ffe8;border-radius:7px;padding:7px 13px;font:inherit;font-weight:700;cursor:pointer">Uložit</button>' +
        '<a href="#" id="nvCancel" style="color:#8a97a8;text-decoration:none">Zrušit</a>' +
        '<span id="nvMsg" style="font-size:12px;margin-left:auto"></span>' +
        '<input type="hidden" id="nvId" value="' + (it.id || '') + '">' +
      '</div></div>';
  }
  function loadNovinky(root) {
    var formBox = root.querySelector('#hrpNovForm'), list = root.querySelector('#hrpNovList'), newBtn = root.querySelector('#hrpNovNew');
    if (!formBox || !list) return;
    function openForm(it) {
      formBox.innerHTML = novFormHtml(it);
      formBox.querySelector('#nvCancel').onclick = function (e) { e.preventDefault(); formBox.innerHTML = ''; };
      formBox.querySelector('#nvSave').onclick = function () {
        var msg = formBox.querySelector('#nvMsg');
        var body = { id: formBox.querySelector('#nvId').value || 0,
          nadpis: formBox.querySelector('#nvNadpis').value.trim(),
          text: formBox.querySelector('#nvText').value.trim(),
          pro: formBox.querySelector('#nvPro').value,
          od: formBox.querySelector('#nvOd').value,
          do: formBox.querySelector('#nvDo').value,
          dulezite: formBox.querySelector('#nvDul').checked,
          datum_akce: formBox.querySelector('#nvDatum').value,
          cas: formBox.querySelector('#nvCas').value.trim(),
          misto: formBox.querySelector('#nvMisto').value.trim(),
          rsvp: formBox.querySelector('#nvRsvp').checked };
        if (!body.nadpis) { msg.style.color = '#e0a94a'; msg.textContent = 'Zadej nadpis.'; return; }
        msg.style.color = '#8fa6c4'; msg.textContent = 'Ukládám…';
        fetch('/api/v1/erp/app/hr/novinka-save', { method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
          .then(function (r) { return r.json(); }).then(function (r) {
            if (r && r.ok) { formBox.innerHTML = ''; render(); } else { msg.style.color = '#f88'; msg.textContent = 'Chyba: ' + ((r && r.error) || ''); }
          }).catch(function () { msg.style.color = '#f88'; msg.textContent = 'Chyba sítě.'; });
      };
    }
    if (newBtn) newBtn.onclick = function (e) { e.preventDefault(); openForm(null); };
    function render() {
      fetch('/api/v1/erp/app/hr/novinky', { credentials: 'include' })
        .then(function (r) { return r.json().catch(function () { return {}; }); })
        .then(function (d) {
          if (!d || !d.ok) { list.innerHTML = '<div class="hrp-empty">' + esc((d && d.error) || 'chyba') + '</div>'; return; }
          var it = d.polozky || [];
          if (!it.length) { list.innerHTML = '<div class="hrp-empty">Zatím žádné novinky. Klikni „➕ Přidat".</div>'; return; }
          list.innerHTML = it.map(function (a) {
            return '<div style="display:flex;gap:10px;align-items:flex-start;padding:8px 0;border-top:1px solid #1c2530">' +
              '<div style="flex:1;min-width:0">' +
                '<div style="color:#e8eef5;font-weight:600">' + (a.dulezite ? '⭐ ' : '') + esc(a.nadpis) + ' ' + novBadge(a.pro) + '</div>' +
                (a.text ? '<div style="color:#aab6c4;font-size:12.5px;margin-top:2px">' + esc(a.text) + '</div>' : '') +
                '<div style="color:#6b7c8d;font-size:11px;margin-top:2px">' + esc(a.od) + (a.do ? (' – ' + esc(a.do)) : '') + ' · ' + novStav(a) + '</div>' +
                (a.rsvp ? '<div style="font-size:11px;color:#8fa6c4;margin-top:3px">📅 ' + esc(a.datum_akce || '') + (a.cas ? (' ' + esc(a.cas)) : '') + (a.misto ? (' · ' + esc(a.misto)) : '') + ' &nbsp; ✅ Přijde ' + a.prijde + ' · ❌ ' + a.neprijde + ' <a href="#" data-rsvp="' + a.id + '" style="color:#7fb2e8;text-decoration:none">kdo</a></div>' : '') +
              '</div>' +
              '<div style="display:flex;gap:8px;white-space:nowrap">' +
                '<a href="#" data-ed="' + a.id + '" style="color:#7fb2e8;text-decoration:none;font-size:12px">Upravit</a>' +
                '<a href="#" data-del="' + a.id + '" style="color:#e08a7a;text-decoration:none;font-size:12px">Smazat</a>' +
              '</div></div>';
          }).join('');
          list.querySelectorAll('[data-ed]').forEach(function (a) { a.onclick = function (e) { e.preventDefault(); var id = +a.getAttribute('data-ed'); var f = it.filter(function (x) { return x.id === id; })[0]; openForm(f); }; });
          list.querySelectorAll('[data-del]').forEach(function (a) { a.onclick = function (e) { e.preventDefault(); if (!confirm('Smazat novinku?')) return; fetch('/api/v1/erp/app/hr/novinka-delete', { method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id: +a.getAttribute('data-del') }) }).then(function (r) { return r.json(); }).then(function () { render(); }); }; });
          list.querySelectorAll('[data-rsvp]').forEach(function (a) { a.onclick = function (e) { e.preventDefault(); var wrap = a.parentNode.parentNode; var ex = wrap.querySelector('.rsvpKdo'); if (ex) { ex.remove(); return; } fetch('/api/v1/erp/app/hr/novinka-rsvp?id=' + (+a.getAttribute('data-rsvp')), { credentials: 'include' }).then(function (r) { return r.json(); }).then(function (d) { var box = document.createElement('div'); box.className = 'rsvpKdo'; box.style.cssText = 'font-size:11px;color:#aab6c4;margin-top:3px;line-height:1.6'; if (d && d.ok && d.lide && d.lide.length) { box.innerHTML = d.lide.map(function (p) { return (p.odpoved === 'ano' ? '✅ ' : '❌ ') + esc(p.jmeno) + (p.pocet > 1 ? (' (' + p.pocet + ')') : ''); }).join('<br>'); } else { box.textContent = 'Zatím nikdo neodpověděl.'; } wrap.appendChild(box); }); }; });
        }).catch(function () { list.innerHTML = '<div class="hrp-empty">✗ síť</div>'; });
    }
    render();
  }
  function renderTiles(g) {
    if (!g) return;
    g.innerHTML = "";
    TILES.forEach(function (x) {
      var d = document.createElement("div");
      d.className = "hrp-tile" + ((x.go || x.act) ? " click" : "");
      var tag = (x.st === "live")
        ? '<span class="hrp-tag live">funkční</span>'
        : '<span class="hrp-tag soon">připravujeme</span>';
      d.innerHTML =
        '<div class="hrp-ico">' + x.ic + '</div><div class="hrp-bd">' +
        '<div class="hrp-tt">' + esc(x.t) + ' ' + tag + '</div>' +
        '<div class="hrp-dd">' + esc(x.d) + '</div></div>';
      if (x.go) { d.onclick = function () { window.open(x.go, "_blank"); }; }
      else if (x.act === "mimo") { d.onclick = openMimo; }
      else if (x.act === "ukoly") { d.onclick = openUkoly; }
      g.appendChild(d);
    });
  }

  function badge(n, l, act, id) {
    return '<div class="hrp-badge' + (act ? ' click' : '') + '"' +
      (act ? ' data-act="' + act + '"' : '') + '><div class="hrp-n"' + (id ? ' id="' + id + '"' : '') + '>' + (n == null ? "0" : n) +
      '</div><div class="hrp-l">' + esc(l) + '</div><div class="hrp-bar"></div></div>';
  }

  // Řádky seznamu Mimo kancelář (sdílené panel + modal).
  function mimoRowsHtml(lide) {
    var out = "", cur = null;
    (lide || []).forEach(function (p) {
      if (p.skupina && p.skupina !== cur) {
        cur = p.skupina;
        out += '<div style="font-size:10.5px;font-weight:700;color:#8fa6c4;text-transform:uppercase;letter-spacing:.03em;padding:8px 4px 2px">' + esc(cur) + '</div>';
      }
      var obd = p.obdobi ? ' <span style="color:#8fa6c4">· ' + esc(p.obdobi) + '</span>' : '';
      out += '<div class="hrp-mrow"><span class="hrp-mic">' + esc(p.ikona || "•") +
        '</span><div><div class="hrp-mnm">' + esc(p.jmeno) + '</div><div class="hrp-mdv">' +
        esc(p.duvod) + obd + '</div></div></div>';
    });
    return out;
  }

  // Viditelný panel „Mimo kancelář dnes" přímo v přehledu (Šárka 3.7.2026 — přehled
  // pro svolávání schůzek: kdo dnes není v kanceláři, hned na očích).
  function loadMimoPanel(root) {
    var list = root.querySelector("#hrpMimoList");
    var cnt = root.querySelector("#hrpMimoCnt");
    if (!list) return;
    fetch("/api/v1/erp/app/hr/mimo", { credentials: "include" })
      .then(function (r) { return r.json().catch(function () { return {}; }); })
      .then(function (d) {
        if (!d || !d.ok) {
          list.innerHTML = '<div class="hrp-empty">Nemáš oprávnění nebo chyba: ' + esc(d && d.error || "") + '</div>';
          return;
        }
        if (cnt) { cnt.textContent = "(" + (d.pocet || 0) + ")"; }
        if (!d.lide || !d.lide.length) {
          list.innerHTML = '<div class="hrp-empty">Dnes jsou všichni v kanceláři. 🎉</div>'; return;
        }
        list.innerHTML = mimoRowsHtml(d.lide);
      })
      .catch(function () { list.innerHTML = '<div class="hrp-empty">✗ síť</div>'; });
  }

  // Panel „Noví a budoucí nástupy" — živě z Centrály (Šárka 23.7.2026). Zahrnuje i
  // ještě nenastoupivší (příznak budouci) — kvůli přehledu, koho čekáme.
  function loadNovi(root) {
    var onb = root.querySelector("#hrpOnbList"), onbc = root.querySelector("#hrpOnbCnt");
    var list = root.querySelector("#hrpNoviList"), cnt = root.querySelector("#hrpNoviCnt");
    if (!list && !onb) return;
    fetch("/api/v1/erp/app/hr/novi", { credentials: "include" })
      .then(function (r) { return r.json().catch(function () { return {}; }); })
      .then(function (d) {
        if (!d || !d.ok) {
          if (list) list.innerHTML = '<div class="hrp-empty">Nemáš oprávnění nebo chyba: ' + esc(d && d.error || "") + '</div>';
          return;
        }
        var novi = d.novi || [];
        var fut = novi.filter(function (p) { return p.budouci; });
        var joined = novi.filter(function (p) { return !p.budouci; });
        function row(p, ic) {
          var chip = p.budouci ? '<span class="hrp-chip nastup">nastoupí</span>' : '';
          var ty = p.typ ? '<span class="hrp-ntyp">' + esc(p.typ) + '</span>' : '';
          return '<div class="hrp-mrow"><span class="hrp-mic">' + ic + '</span>' +
            '<div><div class="hrp-mnm">' + esc(p.jmeno) + ' ' + chip + '</div>' +
            '<div class="hrp-mdv">' + ty + ' nástup ' + esc(p.nastup || '—') + '</div></div></div>';
        }
        if (cnt) cnt.textContent = "(" + fut.length + ")";
        var nb = document.getElementById("hrpBadgeNovi");
        if (nb) nb.textContent = fut.length;
        var nbo = document.getElementById("hrpBadgeOnb");
        if (nbo) nbo.textContent = joined.length;
        if (list) list.innerHTML = fut.length ? fut.map(function (p) { return row(p, "🔜"); }).join("") : '<div class="hrp-empty">Žádné budoucí nástupy.</div>';
        if (onbc) onbc.textContent = "(" + joined.length + ")";
        if (onb) onb.innerHTML = joined.length ? joined.map(function (p) { return row(p, "🚀"); }).join("") : '<div class="hrp-empty">Žádní čerství nováčci.</div>';
      })
      .catch(function () { if (list) list.innerHTML = '<div class="hrp-empty">✗ síť</div>'; });
  }

  // Panel „Moje úkoly" — nativní úkoly STRATEGIE (/app/task, view=moje) vedle Aktualit.
  function loadUkoly(root) {
    var list = root.querySelector("#hrpUkoly");
    var cnt = root.querySelector("#hrpUkolyCnt");
    if (!list) return;
    fetch("/api/v1/erp/app/task?view=moje", { credentials: "include" })
      .then(function (r) { return r.json().catch(function () { return {}; }); })
      .then(function (d) {
        if (!d || !d.ok) {
          list.innerHTML = '<div class="hrp-empty">' + esc(d && d.error || "chyba") + '</div>'; return;
        }
        var u = d.ukoly || [];
        if (cnt) { cnt.textContent = "(" + u.length + ")"; }
        if (!u.length) {
          list.innerHTML = '<div class="hrp-empty">Žádné otevřené úkoly. 🎉</div>'; return;
        }
        list.innerHTML = u.map(function (t) {
          var pri = (t.priorita >= 2) ? "🔴" : (t.priorita === 1 ? "🟠" : "•");
          var term = t.termin ? ('<span class="hrp-utrm' + (t.pozde ? ' late' : '') + '">⏰ ' + esc(t.termin) + '</span>') : '';
          return '<div class="hrp-row"><span class="hrp-ic">' + pri + '</span><span style="min-width:0">' +
            '<div class="hrp-mnm">' + esc(t.predmet) + '</div>' +
            '<div class="hrp-mdv">' + (t.zak ? esc(t.zak) + ' · ' : '') + esc(t.stav_txt || '') + ' ' + term + '</div></span></div>';
        }).join("");
      })
      .catch(function () { list.innerHTML = '<div class="hrp-empty">✗ síť</div>'; });
  }

  // Panel „Výběrová řízení" — běžící z dashboardu; když žádné neběží, poslední doběhlé.
  function renderVyberka(root, vyb) {
    var list = root.querySelector("#hrpVrList");
    var cnt = root.querySelector("#hrpVrCnt");
    if (!list) return;
    var bezici = (vyb && vyb.bezici) || [];
    if (cnt) { cnt.textContent = "(" + bezici.length + ")"; }
    if (bezici.length) {
      list.innerHTML = bezici.map(function (v) {
        return '<div class="hrp-mrow"><span class="hrp-mic">🧲</span><div>' +
          '<div class="hrp-mnm">' + esc(v.title) + ' <span class="hrp-chip nastup">běží</span></div>' +
          '<div class="hrp-mdv">od ' + esc(v.od) + (v.do ? ' · do ' + esc(v.do) : '') + '</div></div></div>';
      }).join("");
    } else if (vyb && vyb.posledni) {
      list.innerHTML = '<div class="hrp-mrow"><span class="hrp-mic">✅</span><div>' +
        '<div class="hrp-mnm">Teď žádné neběží</div>' +
        '<div class="hrp-mdv">Poslední: ' + esc(vyb.posledni.title) + ' — ukončeno ' + esc(vyb.posledni.do) + '</div></div></div>';
    } else {
      list.innerHTML = '<div class="hrp-empty">Žádné výběrové řízení.</div>';
    }
  }

  // Panel „Narozeniny a výročí" = přehled gratulací a ocenění (Krok 2, Šárka 3.7.2026).
  // Významná jubilea (10/20) zvýrazněná; narozeniny lze odklepnout/přeskočit (výpovědní doba…).
  var _grat = [];
  function _stavChip(st) {
    if (st === "sent") return '<span class="hrp-chip sent">✓ odesláno</span>';
    if (st === "skipped") return '<span class="hrp-chip skip">přeskočeno</span>';
    return "";
  }
  function jubRowHtml(j, idx) {
    var badge = "";
    if (j.tier && j.tier !== "normal") {
      var bt = (j.kind === "vyroci") ? (j.roky + " LET") : (j.roky + ". NAR.");
      badge = '<span class="hrp-jbadge">' + esc(bt) + '</span>';
    }
    var za = (j.za_dni === 0) ? "dnes" : (j.za_dni === 1 ? "zítra" : ("za " + j.za_dni + " dní"));
    var st = j.stav || "pending";
    var chip = _stavChip(st);
    if (!chip && j.kind === "narozeniny" && st === "pending") chip = '<span class="hrp-chip" style="background:#12233a;color:#7fb2e8">📤 pošle se automaticky</span>';
    var act = "";
    if (j.kind === "narozeniny") {
      act += '<button class="hrp-abtn" data-a="preview" data-i="' + idx + '">Náhled</button>';
      if (st === "pending") act += '<button class="hrp-abtn" data-a="skip" data-i="' + idx + '">Přeskočit</button>';
      else act += '<button class="hrp-abtn ghost" data-a="reset" data-i="' + idx + '" title="Vrátit">↺</button>';
    } else if (j.certifikat === false) {
      act += '<span class="hrp-soon" style="opacity:.65">jen informace</span>';
    } else {
      act += '<span class="hrp-soon">certifikát brzy</span>';
      if (st === "pending") act += '<button class="hrp-abtn" data-a="skip" data-i="' + idx + '">Přeskočit</button>';
      else act += '<button class="hrp-abtn ghost" data-a="reset" data-i="' + idx + '" title="Vrátit">↺</button>';
    }
    return '<div class="hrp-jrow hrp-j-' + esc(j.tier || "normal") + '">' +
      '<span class="hrp-jic">' + esc(j.ikona || "•") + '</span>' +
      '<div class="hrp-jbd"><div class="hrp-jnm">' + esc(j.jmeno) + badge + ' ' + chip + '</div>' +
      '<div class="hrp-jsub">' + esc(j.popis) + ' · ' + esc(j.datum_cz) + ' · ' + za + '</div></div>' +
      '<div class="hrp-jact">' + act + '</div></div>';
  }
  function _gratPost(akce, j) {
    return fetch("/api/v1/erp/app/hr/gratulace/rozhodni", {
      method: "POST", credentials: "include", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ akce: akce, typ: j.kind, user_id: j.user_id, jmeno: j.jmeno, event_date: j.datum, roky: j.roky })
    }).then(function (r) { return r.json().catch(function () { return {}; }); });
  }
  function _gratAction(a, i, root) {
    var j = _grat[i]; if (!j) return;
    if (a === "preview") {
      _gratPost("preview", j).then(function (d) {
        if (d && d.ok) {
          var m = ensureModal(); m.classList.add("on");
          m.querySelector(".hrp-modal-card").classList.add("hrp-modal-wide");
          m.querySelector("#hrpModalTitle").textContent = "Náhled přání — " + j.jmeno;
          m.querySelector("#hrpModalBody").innerHTML = d.html;
        }
      });
      return;
    }
    if (a === "send" && !window.confirm("Odeslat narozeninové přání: " + j.jmeno + "?")) return;
    if (a === "skip" && !window.confirm("Přeskočit (neposílat) " + j.jmeno + "?")) return;
    _gratPost(a, j).then(function (d) {
      if (d && d.ok) { loadJubilea(root); }
      else { alert("Nepovedlo se: " + (d && d.error || "")); }
    });
  }
  function loadJubilea(root) {
    var list = root.querySelector("#hrpJubList");
    var cnt = root.querySelector("#hrpJubCnt");
    if (!list) return;
    fetch("/api/v1/erp/app/hr/gratulace?days=30", { credentials: "include" })
      .then(function (r) { return r.json().catch(function () { return {}; }); })
      .then(function (d) {
        if (!d || !d.ok) {
          list.innerHTML = '<div class="hrp-empty">Nemáš oprávnění nebo chyba: ' + esc(d && d.error || "") + '</div>';
          return;
        }
        _grat = d.polozky || [];
        if (cnt) { cnt.textContent = "(" + _grat.length + ")"; }
        if (!_grat.length) {
          list.innerHTML = '<div class="hrp-empty">V nejbližších 30 dnech žádná jubilea. 🎈</div>'; return;
        }
        list.innerHTML = _grat.map(function (j, i) { return jubRowHtml(j, i); }).join("");
        if (!list._wired) {
          list.addEventListener("click", function (ev) {
            var b = ev.target.closest ? ev.target.closest(".hrp-abtn") : null;
            if (b) { _gratAction(b.getAttribute("data-a"), parseInt(b.getAttribute("data-i"), 10), root); }
          });
          list._wired = true;
        }
      })
      .catch(function () { list.innerHTML = '<div class="hrp-empty">✗ síť</div>'; });
  }

  // Modal „Mimo kancelář dnes" — seznam jmen + důvod (Krok 1).
  function openMimo() {
    var m = ensureModal();
    m.classList.add("on");
    m.querySelector(".hrp-modal-card").classList.remove("hrp-modal-wide");
    var body = m.querySelector("#hrpModalBody");
    var ttl = m.querySelector("#hrpModalTitle");
    body.innerHTML = '<div class="hrp-empty">Načítám…</div>';
    ttl.textContent = "🏖️ Mimo kancelář dnes";
    fetch("/api/v1/erp/app/hr/mimo", { credentials: "include" })
      .then(function (r) { return r.json().catch(function () { return {}; }); })
      .then(function (d) {
        if (!d || !d.ok) {
          body.innerHTML = '<div class="hrp-empty">Chyba: ' + esc(d && d.error || "") + '</div>'; return;
        }
        ttl.textContent = "🏖️ Mimo kancelář dnes (" + (d.pocet || 0) + ")";
        if (!d.lide || !d.lide.length) {
          body.innerHTML = '<div class="hrp-empty">Dnes jsou všichni v kanceláři. 🎉</div>'; return;
        }
        body.innerHTML = mimoRowsHtml(d.lide);
      })
      .catch(function () { body.innerHTML = '<div class="hrp-empty">✗ síť</div>'; });
  }
  function closeMimo() { var m = document.getElementById("hrpModal"); if (m) m.classList.remove("on"); }
  function ensureModal() {
    var m = document.getElementById("hrpModal");
    if (m) return m;
    m = document.createElement("div");
    m.id = "hrpModal";
    m.className = "hrp-modal";
    m.innerHTML =
      '<div class="hrp-modal-card">' +
      '<div class="hrp-modal-hd"><span id="hrpModalTitle">🏖️ Mimo kancelář dnes</span>' +
      '<span class="hrp-x">✕</span></div>' +
      '<div id="hrpModalBody"><div class="hrp-empty">Načítám…</div></div>' +
      '</div>';
    m.addEventListener("click", function (e) { if (e.target === m) closeMimo(); });
    m.querySelector(".hrp-x").addEventListener("click", closeMimo);
    document.body.appendChild(m);
    return m;
  }

  function style() {
    return '<style>' +
      '.hrp-wrap{max-width:none;margin:0;color:#cdd6e2;font:14px/1.55 -apple-system,Segoe UI,Roboto,system-ui,sans-serif;}' +
      '.hrp-blocks{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;align-items:start;margin-bottom:12px;}' +
      '.hrp-cols3{grid-template-columns:repeat(3,minmax(0,1fr));}' +
      '.hrp-blocks .hrp-panel{margin:0;padding:10px 11px;}' +
      '@media(max-width:900px){.hrp-blocks{grid-template-columns:repeat(2,minmax(0,1fr));}}' +
      '#hrpVeFirmeList,#hrpMimoList,#hrpJubList,#hrpAkt,#hrpNoviList,#hrpVrList{max-height:184px;overflow:auto;}' +
      '#hrpUkoly{max-height:60vh;overflow:auto;}' +
      '.hrp-duo{display:grid;grid-template-columns:1fr 1fr;gap:12px;align-items:start;}' +
      '@media(max-width:800px){.hrp-duo{grid-template-columns:1fr;}}' +
      '.hrp-utrm{font-size:11px;color:#7f8ea0;}' +
      '.hrp-utrm.late{color:#ff8a7a;font-weight:700;}' +
      // Kompaktní styl uvnitř 4 sloupců (Šárka 23.7.2026 — vejít se, menší písmo)
      '.hrp-blocks .hrp-phd{font-size:12.5px;margin-bottom:7px;gap:6px;}' +
      '.hrp-blocks .hrp-pi{width:22px;height:22px;font-size:12px;}' +
      '.hrp-blocks .hrp-mrow{gap:9px;padding:8px 4px;}' +
      '.hrp-blocks .hrp-mic{flex:0 0 26px;height:26px;border-radius:7px;font-size:13px;}' +
      '.hrp-blocks .hrp-mnm{font-size:12.5px;}' +
      '.hrp-blocks .hrp-mdv{font-size:11px;}' +
      // Úzký sloupec: ikona + text nahoře, akční tlačítka na vlastní řádek pod nimi
      // (využití volného prostoru + menší tlačítka; Šárka 23.7.2026).
      '.hrp-blocks .hrp-jrow{gap:8px;padding:8px 9px;flex-wrap:wrap;align-items:flex-start;}' +
      '.hrp-blocks .hrp-jic{flex:0 0 28px;height:28px;font-size:15px;}' +
      '.hrp-blocks .hrp-jbd{flex:1 1 auto;min-width:0;}' +
      '.hrp-blocks .hrp-jnm{font-size:12.5px;gap:5px;}' +
      '.hrp-blocks .hrp-jsub{font-size:11px;}' +
      '.hrp-blocks .hrp-jact{flex:1 1 100%;justify-content:flex-start;gap:5px;margin-top:5px;padding-left:36px;}' +
      '.hrp-blocks .hrp-abtn{font-size:10.5px;padding:3px 8px;border-radius:7px;}' +
      '.hrp-blocks .hrp-soon{font-size:10px;}' +
      '.hrp-blocks .hrp-j-major .hrp-jnm{font-size:13px;}' +
      '.hrp-blocks .hrp-cnt{font-size:11.5px;}' +
      '.hrp-blocks .hrp-jhint{display:none;}' +
      '.hrp-ntyp{display:inline-block;font-size:10.5px;font-weight:700;padding:0 7px;border-radius:20px;background:#1f2a37;color:#aac8ec;margin-right:5px;}' +
      '.hrp-chip.nastup{background:#241d0c;color:#e0a400;}' +
      '.hrp-badges{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:10px;margin-bottom:12px;}' +
      '.hrp-badge{background:#161c24;border:1px solid #233040;border-radius:12px;padding:9px 13px;}' +
      '.hrp-n{font-size:22px;font-weight:800;color:#e8eef5;line-height:1;}' +
      '.hrp-l{font-size:11.5px;color:#7f8ea0;margin-top:2px;}' +
      '.hrp-bar{height:3px;border-radius:3px;background:#aac8ec;width:30px;margin-top:6px;opacity:.85;}' +
      '.hrp-panel{background:#161c24;border:1px solid #233040;border-radius:12px;padding:12px 14px;margin-bottom:12px;}' +
      '.hrp-phd{display:flex;align-items:center;gap:8px;font-size:14px;font-weight:800;color:#e8eef5;margin:0 0 9px;}' +
      '.hrp-pi{width:26px;height:26px;border-radius:50%;background:#1f2a37;color:#aac8ec;display:inline-flex;align-items:center;justify-content:center;font-size:14px;}' +
      '.hrp-cnt{font-size:13px;color:#7f8ea0;font-weight:600;margin-left:2px;}' +
      '.hrp-jhint{font-size:11px;color:#5d6b7c;font-weight:500;margin-left:auto;}' +
      '.hrp-jrow{display:flex;gap:12px;align-items:center;padding:10px 12px;border-top:1px solid #1e2730;border-radius:9px;margin:2px 0;}' +
      '.hrp-jrow:first-child{border-top:0;}' +
      '.hrp-jic{flex:0 0 36px;height:36px;border-radius:9px;background:#1f2a37;display:flex;align-items:center;justify-content:center;font-size:18px;}' +
      '.hrp-jbd{flex:1;min-width:0;}' +
      '.hrp-jnm{font-weight:700;color:#e8eef5;display:flex;align-items:center;gap:8px;flex-wrap:wrap;}' +
      '.hrp-jsub{font-size:12.5px;color:#7f8ea0;margin-top:1px;}' +
      '.hrp-jbadge{font-size:10.5px;font-weight:800;letter-spacing:.3px;padding:1px 8px;border-radius:20px;background:#233040;color:#aac8ec;}' +
      '.hrp-j-major{background:#241d0c;border:1px solid #4a3a16;padding:12px;}' +
      '.hrp-j-major .hrp-jic{background:#4a3a16;}' +
      '.hrp-j-major .hrp-jnm{font-size:15px;}' +
      '.hrp-j-major .hrp-jbadge{background:#e0a400;color:#1a1206;}' +
      '.hrp-j-major10{background:#0f2a16;border:1px solid #1f5b33;padding:12px;}' +
      '.hrp-j-major10 .hrp-jic{background:#1f5b33;}' +
      '.hrp-j-major10 .hrp-jnm{font-size:15px;}' +
      '.hrp-j-major10 .hrp-jbadge{background:#2e9e57;color:#eafff0;}' +
      '.hrp-j-info{background:#16202b;border:1px solid #24303d;padding:11px 12px;}' +
      '.hrp-j-info .hrp-jic{background:#1f2a37;}' +
      '.hrp-j-info .hrp-jbadge{background:#24303d;color:#9fb3cc;}' +
      '.hrp-j-minor{background:#16202b;border:1px solid #24303d;padding:11px 12px;}' +
      '.hrp-j-minor .hrp-jic{background:#1f2a37;}' +
      '.hrp-j-minor .hrp-jbadge{background:#1f2a37;color:#aac8ec;}' +
      '.hrp-jact{display:flex;gap:6px;align-items:center;flex-shrink:0;flex-wrap:wrap;justify-content:flex-end;}' +
      '.hrp-abtn{font-size:12px;font-weight:600;padding:5px 10px;border-radius:8px;border:1px solid #2b3a4a;background:#1b232d;color:#cdd6e2;cursor:pointer;}' +
      '.hrp-abtn:hover{background:#232d39;}' +
      '.hrp-abtn.prim{background:#2e6f3e;border-color:#3a8a4d;color:#eafff0;}' +
      '.hrp-abtn.prim:hover{background:#357f47;}' +
      '.hrp-abtn.ghost{padding:5px 8px;color:#5d6b7c;}' +
      '.hrp-chip{font-size:10.5px;font-weight:700;padding:1px 8px;border-radius:20px;}' +
      '.hrp-chip.sent{background:#16301f;color:#7fe0a0;}' +
      '.hrp-chip.skip{background:#23262b;color:#8a94a3;}' +
      '.hrp-soon{font-size:11px;color:#5d6b7c;font-style:italic;}' +
      '.hrp-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:6px 10px;}' +
      '.hrp-tile{display:flex;gap:9px;padding:8px 8px;border-radius:9px;align-items:flex-start;}' +
      '.hrp-tile.click{cursor:pointer;}' +
      '.hrp-tile.click:hover{background:#1b232d;}' +
      '.hrp-ico{flex:0 0 30px;height:30px;border-radius:8px;background:#1f2a37;display:flex;align-items:center;justify-content:center;font-size:15px;}' +
      '.hrp-bd{flex:1;min-width:0;}' +
      '.hrp-tt{font-weight:700;color:#e8eef5;font-size:12.5px;display:flex;align-items:center;gap:6px;flex-wrap:wrap;line-height:1.25;}' +
      '.hrp-dd{font-size:11px;color:#7f8ea0;margin-top:1px;line-height:1.3;}' +
      '.hrp-tag{display:inline-block;border-radius:20px;padding:1px 9px;font-size:10.5px;font-weight:700;}' +
      '.hrp-tag.soon{background:#23262b;color:#7f8ea0;}' +
      '.hrp-tag.live{background:#16301f;color:#7fe0a0;}' +
      '.hrp-feed .hrp-row{display:flex;gap:9px;padding:8px 4px;border-top:1px solid #1e2730;font-size:12.5px;align-items:center;}' +
      '.hrp-feed .hrp-ic{flex:0 0 26px;height:26px;font-size:13px;}' +
      '.hrp-feed .hrp-row:first-of-type{border-top:0;}' +
      '.hrp-feed .hrp-row-mil{background:#241d0c;border:1px solid #4a3a16;border-radius:9px;padding:10px 10px;font-weight:600;color:#f0d68a;}' +
      '.hrp-feed .hrp-row-mil .hrp-ic{background:#4a3a16;}' +
      '.hrp-ic{flex:0 0 30px;height:30px;border-radius:8px;background:#1f2a37;display:flex;align-items:center;justify-content:center;font-size:15px;}' +
      '.hrp-empty{padding:20px;color:#7f8ea0;text-align:center;font-style:italic;}' +
      '.hrp-badge.click{cursor:pointer;}' +
      '.hrp-modal{display:none;position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:99999;align-items:flex-start;justify-content:center;padding:56px 16px;}' +
      '.hrp-modal.on{display:flex;}' +
      '.hrp-modal-card{background:#161c24;border:1px solid #233040;border-radius:14px;max-width:520px;width:100%;box-shadow:0 20px 60px rgba(0,0,0,.5);overflow:hidden;max-height:80vh;display:flex;flex-direction:column;color:#cdd6e2;font:14px/1.55 -apple-system,Segoe UI,Roboto,system-ui,sans-serif;}' +
      '.hrp-modal-card.hrp-modal-wide{max-width:720px;max-height:90vh;}' +
      '.hrp-modal-hd{display:flex;align-items:center;justify-content:space-between;padding:14px 18px;border-bottom:1px solid #233040;font-weight:800;color:#e8eef5;}' +
      '.hrp-x{cursor:pointer;color:#7f8ea0;font-size:18px;line-height:1;}' +
      '#hrpModalBody{overflow:auto;}' +
      '.hrp-mrow{display:flex;gap:12px;align-items:center;padding:11px 18px;border-top:1px solid #1e2730;}' +
      '.hrp-mrow:first-child{border-top:0;}' +
      '.hrp-mic{flex:0 0 34px;height:34px;border-radius:9px;background:#1f2a37;display:flex;align-items:center;justify-content:center;font-size:17px;}' +
      '.hrp-mnm{font-weight:700;color:#e8eef5;}' +
      '.hrp-mdv{font-size:12.5px;color:#7f8ea0;}' +
      '</style>';
  }

  window.HrPult = { mount: mount };
})();
