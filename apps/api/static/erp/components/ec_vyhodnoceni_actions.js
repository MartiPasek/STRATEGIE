/* ec_vyhodnoceni_actions.js — akcni lista pro jadro "Vyhodnoceni zakazky".
 * Wrapuje DesignFwForm.prototype._render: po renderu jadra (core code
 * 'ec.vyhodnoceni_jadro') vlozi listu tlacitek volajicich
 * POST /api/v1/erp/action/run (ec.* funkce, 1:1 zrcadlo Centraly).
 * Autor: Claude, 20.7.2026. Vse defenzivne — nikdy nevyhodi do frameworku.
 */
(function (global) {
  "use strict";

  var CORE_CODE = "ec.vyhodnoceni_jadro";
  /* POŘADÍ TLAČÍTEK = POŘADÍ KROKŮ (C24 / Kristý, 9. 9. 2026).
   * Do 9. 9. byla lišta v pořadí Připravit → Přepočet → Nastav koeficienty, což svádělo
   * klikat je zleva doprava a počítat prémie ze starých hodnot. Závislost v DB je totiž:
   *   1) ec.priprava_vyhodnoceni   naplní ec.vyhodnoceni_osoba z odpracovaných hodin
   *                                (uvnitř si volá přepočet, ale ještě nad starou hlavičkou),
   *   2) ec.vypocet_konstant       z těch hodin spočítá HLAVIČKU zakázky
   *                                (kalk_hod_celkem_s_ef, odpracovano, limit_pro_srazku),
   *   3) ec.prepocet_vyhodnoceni   teprve Z HLAVIČKY počítá prémii na osobu jako
   *                                (hodiny osoby / odpracovano) × (kalk_s_ef − odpracovano_ef) × sazba.
   * Koeficienty tedy MUSÍ běžet před přepočtem, jinak přepočet pracuje s hlavičkou,
   * která ještě neodpovídá aktuálním hodinám. Ověřeno na VR10686 9. 9. 2026 —
   * v tomhle pořadí vyšlo ušetřeno 4,059 h a prémie 535 Kč, ověřeno proti ruční kontrole.
   */
  var ACTIONS = [
    /* POTVRZENI PRIDANO 10. 9. 2026 (Kristy). priprava_vyhodnoceni nejdriv SMAZE
     * radky hodnoceni te zakazky a zalozi je znovu z odpracovanych hodin — vsem
     * s efektivitou 100 %. Druhe spusteni tedy zahodi rucne zadane efektivity,
     * poznamky sefmontera, specialni premie i oznaceni sefmontera. Do ted na to
     * UI nijak neupozornovalo a tlacitko je hned prvni v lise. */
    { code: "priprava",         label: "1️⃣ ▶️ Připravit hodnocení", confirm: "⚠️ PŘIPRAVIT HODNOCENÍ?\n\nZaloží seznam lidí na zakázce ZNOVU podle odpracovaných hodin.\n\nSMAŽE tím dosavadní hodnocení této zakázky — ručně zadané efektivity, poznámky šéfmontéra, speciální prémie i označení šéfmontéra. Všem se nastaví efektivita 100 %.\n\nChceš-li jen přepočítat čísla, použij „3️⃣ Přepočet hodnocení\".\n\nPokračovat?" },
    /* OD 10. 9. 2026 (C24 / Kristy) OTEVIRA JADRO, NE ROVNOU PREPOCET.
     * Do ted tlacitko volalo ec.vypocet_konstant primo — jenze koeficienty
     * (sazby, rezerva, premie sefmontera) nemel uzivatel kde zadat, takze
     * prepocet vzdycky pocital ze STARE rezervy. Ted se nejdriv otevre jadro
     * nad hlavickou zakazky, Dusan hodnoty upravi, a teprve OK je ulozi
     * A HNED spusti prepocet — jednim kliknutim, o krok navic nevi.
     * Poradi odpovida tomu, jak to uvnitr funguje: vypocet_konstant cte
     * konst_cas_rezerva jako VSTUP (limit_pro_srazku = kalk_hod_celkem_s_ef
     * x rezerva) a zadny z tech sesti sloupcu neprepisuje. */
    { code: "koeficienty",      label: "2️⃣ ⚙️ Nastav koeficienty", confirm: null, vlastni: true },
    { code: "prepocet",         label: "3️⃣ 🔄 Přepočet hodnocení", confirm: null },
    { code: "uzavrit",          label: "4️⃣ 🔒 Uzavřít", confirm: "⚠️ UZAVŘÍT vyhodnocení?\n\nTato akce VYTVOŘÍ VÝPLATY (SuperHrubá mzda) pro pracovníky této zakázky — zápis do financí zakázek.\n\nPokračovat?" },
    { code: "do_mezd",          label: "5️⃣ 💰 Do mezd", confirm: "⚠️ PŘEVÉST ODMĚNY DO MEZD?\n\nOdměny z této zakázky se zapíšou zaměstnancům do mzdy (složka 651) za měsíc, kdy byla zakázka uzavřena.\n\nSpustit to jde i opakovaně — co už je ve mzdě, se nezdvojí.\n\nPokračovat?" },
    { code: "zrusit",           label: "↩️ Zrušit", confirm: "⚠️ ZRUŠIT vyhodnocení?\n\nSMAŽE vypočtené výplaty, zakázku zarchivuje a znovu otevře k přepočtu.\n\nPokud už odměny šly do mezd, SMAŽOU SE i odtud — pokud ale některá z nich už byla předána do mzdy (stav exported), zrušení se odmítne a musí to vyřešit mzdová účetní.\n\nPokračovat?" }
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
    box.style.cssText = "background:#fff;color:#0f172a;border-radius:10px;min-width:380px;max-width:560px;" +
      "max-height:80vh;overflow:auto;box-shadow:0 8px 30px rgba(0,0,0,.25);padding:16px 18px;";
    var h = document.createElement("div");
    h.textContent = nadpis;
    /* BARVA NATVRDO (C24 / Kristy, 10.9.2026): ERP jede v tmavem motivu, okno je
     * bile — nadpis bez vlastni barvy zdedil svetle pismo a byl na bilem pozadi
     * necitelny. Tyka se vsech dialogu, ktere tohle okno pouzivaji. */
    h.style.cssText = "font-weight:600;font-size:15px;margin:0 0 10px 0;color:#0f172a;";
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

  /* Σ SOUCET PREMII ZA ZAKAZKU (Dusan pres Kristy, 10.9.2026).
   * Dusan chtel videt, kolik za zakazku odchazi na premiich celkem, aniz by
   * musel scitat radky v gridu.
   *
   * PROC SE NECTE Z HLAVICKY: `ec.vyhodnoceni_zakazka.premie_celkem` ten soucet
   * sice drzi, ale plni ho AZ prepocet (`vypocet_konstant`) a scita ho pres CELOU
   * skupinu slouceni. Kdyz nekdo upravi premii jednomu cloveku a prepocet nespusti,
   * hlavicka je zastarala — a cislo, ktere sedi jen nekdy, je horsi nez zadne.
   * Proto ctu STEJNY dataset, ze ktereho se kresli grid "Hodnoceni vse", a scitam
   * jeho radky. Cislo tedy vzdy odpovida tomu, co ma uzivatel pred ocima.
   *
   * Aliasy "Prémie" / "Srážka" jsou z datasetu ec.vyhodnoceni_jadro_osoba
   * (o.premie_osoba_final a o.srazka_osoba). Kdyby se prejmenovaly, _klicSoucet
   * si sloupec najde podle zacatku nazvu, aby soucet nezmizel potichu. */
  function _klicSoucet(radek, zacatek) {
    if (!radek) return null;
    var klice = Object.keys(radek);
    for (var i = 0; i < klice.length; i++) {
      if (klice[i] === zacatek) return klice[i];
    }
    for (var j = 0; j < klice.length; j++) {
      if (klice[j].indexOf(zacatek) === 0) return klice[j];
    }
    return null;
  }

  function _kc(n) {
    try {
      var des = (Math.abs(n - Math.round(n)) > 0.004) ? 2 : 0;
      return n.toLocaleString("cs-CZ", { minimumFractionDigits: des, maximumFractionDigits: des }) + " Kč";
    } catch (e) {
      return String(Math.round(n)) + " Kč";
    }
  }

  /* KDY SE SOUCET OBNOVUJE (Kristy 10.9.2026 — "aktualizuje se po zmene hodnot?").
   * Sam od sebe se prekresluje s celym jadrem, tedy po kazde akci z listy
   * (_volej i _run volaji _reloadSpec). Rucni uprava jednoho cloveka v gridu
   * "Hodnoceni vse" ale jadro prekreslit nemusi — a zastarale cislo u penez je
   * horsi nez zadne. Proto jeste:
   *   1) klik na samotny soucet ho prepocita hned (kurzor je "pointer"),
   *   2) jakykoli klik na strance ho po 1,5 s tise prepocita — tim se srovna
   *      i po zavreni dialogu "zadani efektivity", ktery je mimo nase jadro.
   * Listener je jeden na cely dokument, navesi se jednou a kdyz uz soucet
   * v DOM neni (jadro zavrene), nedela nic. */
  var _soucetChip = null, _soucetInst = null, _soucetTimer = null, _soucetHook = false;

  function _soucetHookNavesit() {
    if (_soucetHook) return;
    _soucetHook = true;
    document.addEventListener("click", function () {
      if (_soucetTimer) { clearTimeout(_soucetTimer); }
      _soucetTimer = setTimeout(function () {
        _soucetTimer = null;
        if (!_soucetChip || !_soucetInst) return;
        if (!document.body.contains(_soucetChip)) return;
        try { _soucet(_soucetInst, _soucetChip); } catch (e) {}
      }, 1500);
    }, true);
  }

  function _soucet(inst, chip) {
    var rec = _rec(inst);
    var id = (rec.id != null) ? rec.id : (inst.opts && inst.opts.rowId);
    if (id == null) { chip.style.display = "none"; return; }
    var url = "/api/v1/erp/data/ec.vyhodnoceni_jadro_osoba?master_id=" +
              encodeURIComponent(id) + "&kind=select-detail";
    fetch(url, { credentials: "same-origin" })
      .then(function (r) { return r.json(); })
      .then(function (j) {
        var rows = (j && j.ok && Array.isArray(j.rows)) ? j.rows : [];
        if (!rows.length) { chip.style.display = "none"; return; }
        var kP = _klicSoucet(rows[0], "Prémie");
        var kS = _klicSoucet(rows[0], "Srážka");
        var sumP = 0, sumS = 0;
        rows.forEach(function (r) {
          if (kP) { var p = Number(r[kP]); if (isFinite(p)) sumP += p; }
          if (kS) { var v = Number(r[kS]); if (isFinite(v)) sumS += v; }
        });
        var txt = "Σ Prémie: " + _kc(sumP);
        if (sumS > 0) txt += "  ·  Σ Srážka: " + _kc(sumS);
        txt += "  ·  " + rows.length + (rows.length === 1 ? " člověk" : (rows.length < 5 ? " lidi" : " lidí"));
        chip.textContent = txt;
        chip.title = "Součet za tuto zakázku, počítaný ze stejných řádků, jaké jsou v gridu „Hodnocení vše\". Obnovuje se sám po změnách; kliknutím ho přepočítáš hned.";
        chip.style.display = "";
      })
      .catch(function () { chip.style.display = "none"; });
  }

  /* ⚙️ Koeficienty zakazky — jadro nad hlavickou ec.vyhodnoceni_zakazka.
   * Sest poli je nas ekvivalent EC_VyhodnoceniZak_KonstantyKZak (prehled 74100
   * v Centrale). Hodnoty se v Centrale realne lisi zakazku od zakazky
   * (SazbaPremie 0-130, KonstCasRezerva 1,15-115, PremieSefmonter 0-500),
   * takze to nejsou globalni konstanty a patri sem.
   *
   * Predvyplnuju z `inst._spec.data`, protoze edit dataset jadra je
   * `SELECT * FROM ec.vyhodnoceni_zakazka` — vsech sest sloupcu uz v zaznamu
   * je a nemusi se nic dotahovat.
   *
   * Prazdne pole = "nemenit" (backend si drzi puvodni hodnotu), NE "vynulovat".
   * Vyjimka je rezerva, ta je povinna — pocita se z ni limit pro srazku. */
  var KOEF_POLE = [
    { klic: "sazba_premie",          popis: "Sazba prémie (Kč/h)" },
    { klic: "sazba_srazka",          popis: "Sazba srážky (Kč/h)" },
    { klic: "konst_cas_rezerva",     popis: "Konstanta času — rezerva", povinne: true },
    { klic: "premie_sefmonter",      popis: "Prémie šéfmontér (Kč)" },
    { klic: "premie_sefmonter_hod",  popis: "Prémie šéfmontér — hodin" },
    { klic: "premie_sefmonter_koef", popis: "Prémie šéfmontér — koeficient" }
  ];

  /* Cesky zapis cisla (carka) i strojovy (tecka). Prazdne = null = nemenit. */
  function _cislo(txt) {
    var t = String(txt == null ? "" : txt).trim().replace(/\s/g, "").replace(",", ".");
    if (t === "") return null;
    var n = Number(t);
    return isFinite(n) ? n : NaN;
  }

  /* Cislo do inputu — bez zbytecnych nul na konci (130.000000 → 130). */
  function _zobraz(v) {
    if (v == null || v === "") return "";
    var n = Number(v);
    if (!isFinite(n)) return String(v);
    return String(Math.round(n * 1e6) / 1e6).replace(".", ",");
  }

  function _koeficienty(inst) {
    var rec = _rec(inst);
    var zak = _zakazka(inst);
    if (!zak) { global.alert("Není načtená zakázka."); return; }
    if (rec.uzamceno) {
      global.alert("Zakázka " + zak + " je uzamčená (historie z Centrály).\n\n" +
                   "Koeficienty u ní měnit nejde.");
      return;
    }

    var box = document.createElement("div");
    var info = document.createElement("div");
    info.innerHTML = "Uprav koeficienty této zakázky. Po <b>Uložit a přepočítat</b> se " +
      "rovnou spustí přepočet hlavičky, takže se z nich hned spočítá limit pro srážku " +
      "i ušetřený čas.<br><br><span style=\"color:#64748b\">Prázdné pole = ponechat " +
      "beze změny.</span>";
    info.style.cssText = "font-size:13px;color:#334155;margin-bottom:12px;line-height:1.5;";
    box.appendChild(info);

    var vstupy = {};
    KOEF_POLE.forEach(function (p) {
      var radek = document.createElement("label");
      radek.style.cssText = "display:flex;align-items:center;gap:10px;margin-bottom:8px;font-size:13px;";
      var lbl = document.createElement("span");
      lbl.textContent = p.popis + (p.povinne ? " *" : "");
      lbl.style.cssText = "flex:1 1 auto;color:#334155;";
      var inp = document.createElement("input");
      inp.type = "text";
      inp.inputMode = "decimal";
      inp.value = _zobraz(rec[p.klic]);
      inp.style.cssText = "flex:0 0 120px;padding:5px 8px;border:1px solid #cbd5e1;" +
        "border-radius:6px;font-size:13px;text-align:right;font-family:inherit;";
      vstupy[p.klic] = inp;
      radek.appendChild(lbl);
      radek.appendChild(inp);
      box.appendChild(radek);
    });

    _okno("Koeficienty zakázky " + zak, box, "Uložit a přepočítat", function () {
      var telo = { action_code: "koeficienty_uloz", cislo: zak };
      var chyba = null;
      KOEF_POLE.forEach(function (p) {
        if (chyba) return;
        var n = _cislo(vstupy[p.klic].value);
        if (isNaN(n)) { chyba = "„" + p.popis + "“ není číslo."; return; }
        if (p.povinne && n === null) { chyba = "„" + p.popis + "“ je povinná."; return; }
        if (n !== null && n < 0) { chyba = "„" + p.popis + "“ nemůže být záporná."; return; }
        telo[p.klic] = n;
      });
      if (chyba) { global.alert(chyba); return; }
      _volej(inst, telo, "Koeficienty uloženy a hlavička přepočítána.");
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
      if (act.code === "koeficienty") { _koeficienty(inst); }
      else if (act.code === "sefmonter") { _sefmonter(inst); }
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
      b.onclick = function () { if (act.vlastni) { _vlastni(inst, act, b); } else { _run(inst, act, b); } };
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
    /* Soucet vpravo v liste — oddeleny mezerou, aby splyval s tlacitky co nejmin
     * a zaroven byl videt hned, bez rolovani (lista je position:sticky). */
    var chip = document.createElement("span");
    chip.className = "ec-vyh-soucet";
    chip.style.cssText = "margin-left:auto;align-self:center;padding:4px 10px;" +
      "border:1px solid #bfdbfe;border-radius:6px;background:#eff6ff;color:#1e3a8a;" +
      "font-size:12px;line-height:1.2;white-space:nowrap;font-weight:600;display:none;";
    chip.style.cursor = "pointer";
    chip.onclick = function () { try { _soucet(inst, chip); } catch (e) {} };
    bar.appendChild(chip);
    _soucetChip = chip; _soucetInst = inst;
    _soucetHookNavesit();
    try { _soucet(inst, chip); } catch (e) {}

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
