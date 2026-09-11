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
     * hodnoceni kvality prace i poznamky. Do ted na to UI nijak neupozornovalo
     * a tlacitko je hned prvni v lise.
     *
     * ZPRESNENO 11. 9. 2026 (C24 / Kristy) — puvodni text tvrdil, ze se ztrati
     * i OZNACENI SEFMONTERA. To neni pravda a zbytecne to od tlacitka odrazovalo:
     * ec.nastav_sefmontera uklada osobni cislo do tenant.zakazka_meta (tedy
     * u ZAKAZKY, ne u cloveka) a ec.prepocet_vyhodnoceni ho odtamtud zase dosadi
     * (radek `sefmonter = CASE WHEN c_sefmonter = V.cislo_zam THEN true ...`).
     * Naopak ve vyctu chybela hodnoceni kvality prace (flexibilita, chybovost,
     * estetika) — ta se opravdu ztrati, protoze INSERT v priprava_vyhodnoceni
     * plni jen cislo_zam, cislo_zakazky, efektivitu 100, sefmonter=false
     * a pocet_hodin 0; vsechny ostatni sloupce zustanou prazdne a prepocet
     * je nema odkud vratit. Vycet nize je overeny proti sloupcum
     * ec.vyhodnoceni_osoba, ne odhadnuty. */
    { code: "priprava",         label: "1️⃣ ▶️ Připravit hodnocení", confirm: "⚠️ PŘIPRAVIT HODNOCENÍ?\n\nZaloží seznam lidí na zakázce ZNOVU podle odpracovaných hodin — doplní tím i ty, kdo na zakázce mezitím přibyli.\n\nSMAŽE ale všechno, co je u lidí zadané ručně:\n  • efektivitu (všem se nastaví 100 %)\n  • hodnocení flexibility, chybovosti a estetiky včetně poznámek\n  • speciální prémie\n  • poznámky (šéfmontér, VV, VP, zkušebna)\n\nOznačení šéfmontéra se ZACHOVÁ — to je uložené u zakázky, ne u člověka, a přepočet ho dosadí zpátky.\n\nChceš-li jen přepočítat čísla, použij „3️⃣ Přepočet hodnocení\".\n\nPokračovat?" },
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
    { code: "hodnavic",  label: "⏱️ Úprava hodin vícepráce…" },
    { code: "ukol",      label: "📨 Odeslat úkol…" },
    { code: "sefmonter", label: "👷 Šéfmontér…" },
    { code: "slouci",    label: "🔗 Hodnotit společně…" },
    { code: "rozdelit",  label: "✂️ Zrušit sloučení" }
  ];

  function _rec(inst) { return (inst && inst._spec && inst._spec.data) || {}; }
  function _coreCode(inst) { try { return inst._spec.core.code; } catch (e) { return null; } }
  function _zakazka(inst) { return _rec(inst).cislo_zakazky || null; }

  /* Male modalni okno. Zamerne bez zavislosti na frameworku — kdyby se jeho
   * dialogy zmenily, tohle porad funguje. */
  function _okno(nadpis, obsahEl, potvrdText, onPotvrd, sirka) {
    var back = document.createElement("div");
    back.style.cssText = "position:fixed;inset:0;background:rgba(0,0,0,.35);z-index:99999;" +
      "display:flex;align-items:center;justify-content:center;";
    var box = document.createElement("div");
    /* sirka je volitelna — dialog hodin viceprace potrebuje dva sloupce vedle sebe */
    box.style.cssText = "background:#fff;color:#0f172a;border-radius:10px;min-width:380px;max-width:" +
      (sirka || "560px") + ";max-height:85vh;overflow:auto;box-shadow:0 8px 30px rgba(0,0,0,.25);padding:16px 18px;";
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

  /* ⏱️ UPRAVA HODIN VICEPRACE (Kristy 10.9.2026) — nahrada jadra 347 z Centraly.
   * Layout podle zadani Kristy: vlevo 7402 "Uprava kalk. hodin VP", vpravo 7403
   * "Uprava kalk. hodin vedouci vyroby", dole 7407 "dilna".
   *
   * POZOR, NENI TO CHYBA: 7402 i 7403 ctou v Centrale TATAZ data (oba filtruji
   * Typ = 1). Kristy 10.9.2026 potvrdila, ze tak to v Centrale opravdu je —
   * proto to necham a jen na to v dialogu upozornim, aby to nevypadalo jako bug.
   *
   * Zapis jde do CENTRALY (rozhodnuti Kristy) — viz g2007.python
   * `vyhodnoceni_hodnavic`. Tady je jen ovladani. */
  function _hnCislo(v, des) {
    var n = Number(v || 0);
    if (!isFinite(n)) return "0";
    return n.toFixed(des == null ? 2 : des).replace(".", ",");
  }

  function _hnSeznam(nadpis, radky, jeDilna) {
    var box = document.createElement("div");
    box.style.cssText = "flex:1 1 300px;min-width:280px;";
    var h = document.createElement("div");
    h.textContent = nadpis;
    h.style.cssText = "font-weight:600;font-size:12px;color:#334155;margin:0 0 6px 0;";
    box.appendChild(h);
    var telo = document.createElement("div");
    telo.style.cssText = "border:1px solid #e2e8f0;border-radius:6px;max-height:190px;overflow:auto;";
    if (!radky.length) {
      var pr = document.createElement("div");
      pr.textContent = "Žádné záznamy.";
      pr.style.cssText = "padding:10px;font-size:12px;color:#94a3b8;";
      telo.appendChild(pr);
    } else {
      radky.forEach(function (r) {
        var d = document.createElement("div");
        d.style.cssText = "padding:6px 9px;border-bottom:1px solid #f1f5f9;font-size:12px;line-height:1.45;";
        var hl = document.createElement("div");
        if (jeDilna) {
          var stav = r.schvalil ? ("schválil " + r.schvalil) : "čeká na schválení";
          hl.innerHTML = "<b>" + _hnCislo(r.zadost) + " h</b> žádost · schváleno <b>" +
                         _hnCislo(r.hodin) + " h</b> <span style=\"color:#64748b\">(" + stav + ")</span>";
        } else {
          hl.innerHTML = "<b>" + _hnCislo(r.hodin) + " h</b>";
        }
        d.appendChild(hl);
        var pod = [];
        if (r.duvod) pod.push(r.duvod);
        if (r.poznamka) pod.push(r.poznamka);
        if (r.porizeno) pod.push(r.porizeno);
        if (r.zakazka) pod.push(r.zakazka);
        if (pod.length) {
          var p = document.createElement("div");
          p.textContent = pod.join(" · ");
          p.style.cssText = "color:#64748b;";
          d.appendChild(p);
        }
        telo.appendChild(d);
      });
    }
    box.appendChild(telo);
    return box;
  }

  /* Tlacitko na dobu cekani prepnu do stavu "Nactim…" a zase zpatky.
   * DUVOD (Kristy 11.9.2026): _vlastni odemkne tlacitko hned, jeste nez se vrati
   * odpoved, takze uzivatel nema ZADNOU zpetnou vazbu. Kdyz zrovna bezi obnova
   * zrcadla tenant.oz_zakazky (TRUNCATE + INSERT po 30 minutach), cteni ceka na
   * zamek — zmereno 18 s — a tlacitko vypada jako mrtve. */
  function _cekam(zap, kod) {
    var b = document.querySelector(".ec-vyh-actionbar [data-ec-cekam=\"" + kod + "\"]");
    if (!b) return;
    if (zap) {
      b.dataset.puvodni = b.textContent;
      b.textContent = "⏳ Načítám…";
      b.disabled = true;
    } else {
      if (b.dataset.puvodni) b.textContent = b.dataset.puvodni;
      b.disabled = false;
    }
  }

  function _hodnavic(inst) {
    var zak = _zakazka(inst);
    if (!zak) { global.alert("Není načtená zakázka."); return; }

    _cekam(true, "hodnavic");
    fetch("/api/v1/erp/app/erp_registry/run", {
      method: "POST", credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ kod: "vyhodnoceni_hodnavic", args: [zak, "__uid__", "nacti"] })
    }).then(function (r) { return r.json(); }).then(function (j) {
      _cekam(false, "hodnavic");
      var v = (j && j.vysledek) ? j.vysledek : j;
      if (!v || v.ok !== true) {
        global.alert("Nepovedlo se načíst hodiny navíc:\n\n" + ((v && v.chyba) || "neznámá chyba"));
        return;
      }

      var box = document.createElement("div");

      var shrn = document.createElement("div");
      shrn.innerHTML = "Platné hodiny navíc na této zakázce (a sloučených): <b>" +
                       _hnCislo(v.soucet_platnych) + " h</b>";
      shrn.style.cssText = "font-size:13px;color:#334155;margin-bottom:10px;";
      box.appendChild(shrn);

      /* ── formulář nového požadavku ────────────────────────────────── */
      var blok = document.createElement("div");
      blok.style.cssText = "border:1px solid #bfdbfe;background:#eff6ff;border-radius:8px;" +
        "padding:10px 12px;margin-bottom:14px;";
      var bh = document.createElement("div");
      bh.textContent = "Nový požadavek na navýšení";
      bh.style.cssText = "font-weight:600;font-size:13px;margin-bottom:8px;";
      blok.appendChild(bh);

      function _pole(popis, sirka, ph) {
        var w = document.createElement("label");
        w.style.cssText = "display:inline-flex;flex-direction:column;gap:3px;margin:0 10px 8px 0;font-size:12px;color:#334155;";
        var l = document.createElement("span"); l.textContent = popis;
        var i = document.createElement("input");
        i.type = "text"; i.placeholder = ph || "";
        i.style.cssText = "width:" + sirka + ";padding:5px 8px;border:1px solid #cbd5e1;" +
          "border-radius:6px;font-size:13px;font-family:inherit;";
        w.appendChild(l); w.appendChild(i); blok.appendChild(w);
        return i;
      }
      var iHod = _pole("Počet hodin", "90px", "0");
      var iMin = _pole("Počet minut", "90px", "0");
      var iDuv = _pole("Důvod navýšení *", "230px", "");
      var iPoz = _pole("Poznámka", "100%", "");

      /* nabídka už použitých důvodů — ať se nevymýšlejí pokaždé nové */
      if (v.duvody && v.duvody.length) {
        var dl = document.createElement("datalist");
        dl.id = "ec-hn-duvody-" + Date.now();
        v.duvody.forEach(function (d) {
          var o = document.createElement("option"); o.value = d; dl.appendChild(o);
        });
        blok.appendChild(dl);
        iDuv.setAttribute("list", dl.id);
      }

      var akce = document.createElement("div");
      akce.style.cssText = "margin-top:4px;";
      var btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = "Uložit do Centrály";
      btn.style.cssText = "padding:6px 14px;border:1px solid #2563eb;background:#2563eb;color:#fff;" +
        "border-radius:6px;cursor:pointer;font-size:13px;";
      akce.appendChild(btn);
      var hlaska = document.createElement("span");
      hlaska.style.cssText = "margin-left:10px;font-size:12px;color:#b91c1c;";
      akce.appendChild(hlaska);
      blok.appendChild(akce);

      if (v.uzamceno || v.uzavreno) {
        btn.disabled = true;
        btn.style.opacity = "0.5"; btn.style.cursor = "not-allowed";
        hlaska.style.color = "#92400e";
        hlaska.textContent = v.uzamceno
          ? "Zakázka je uzamčená (historie z Centrály)."
          : "Vyhodnocení je uzavřené — nejdřív ho zruš.";
      }

      btn.onclick = function () {
        hlaska.style.color = "#b91c1c"; hlaska.textContent = "";
        if (!String(iDuv.value || "").trim()) { hlaska.textContent = "Vyplň důvod navýšení."; return; }
        var hh = Number(String(iHod.value || "0").replace(",", ".")) || 0;
        var mm = Number(String(iMin.value || "0").replace(",", ".")) || 0;
        if (hh <= 0 && mm <= 0) { hlaska.textContent = "Zadej hodiny nebo minuty."; return; }
        btn.disabled = true; btn.textContent = "Ukládám…";
        fetch("/api/v1/erp/app/erp_registry/run", {
          method: "POST", credentials: "same-origin",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ kod: "vyhodnoceni_hodnavic",
            args: [zak, "__uid__", "uloz", iHod.value || 0, iMin.value || 0,
                   iDuv.value || "", iPoz.value || ""] })
        }).then(function (r) { return r.json(); }).then(function (jj) {
          var w = (jj && jj.vysledek) ? jj.vysledek : jj;
          btn.disabled = false; btn.textContent = "Uložit do Centrály";
          if (!w || w.ok !== true) {
            hlaska.textContent = (w && w.chyba) || "Uložení se nepovedlo.";
            return;
          }
          /* Cisla u NAS se zmeni az potom, co se obnovi zrcadlo zakazek
           * (tenant.oz_zakazky, ~30 min) a pusti se prepocet. Rikam to nahlas,
           * at Dusan necaka, ze mu premie naskoci hned. */
          global.alert("Zapsáno do Centrály (ID " + w.ec_id + ") — " +
                       _hnCislo(w.hodin) + " h.\n\n" +
                       "Centrála si kalkulaci přepočítala.\n\n" +
                       "U nás se to v prémiích projeví, až se obnoví zrcadlo zakázek " +
                       "(do ~30 minut) a pustíš znovu „2️⃣ Nastav koeficienty“ " +
                       "a „3️⃣ Přepočet hodnocení“." +
                       (w.lokalne ? "" : "\n\n(Kopii k nám se uložit nepodařilo — v Centrále " +
                                          "to ale je a přijde synchronizací.)"));
          if (typeof inst._reloadSpec === "function") { try { inst._reloadSpec(); } catch (e) {} }
        }).catch(function (e) {
          btn.disabled = false; btn.textContent = "Uložit do Centrály";
          hlaska.textContent = "Chyba spojení: " + (e && e.message ? e.message : e);
        });
      };
      box.appendChild(blok);

      /* ── dva přehledy vedle sebe ──────────────────────────────────── */
      var rada = document.createElement("div");
      rada.style.cssText = "display:flex;gap:14px;flex-wrap:wrap;margin-bottom:6px;";
      rada.appendChild(_hnSeznam("Úprava kalk. hodin VP", v.vp || [], false));
      rada.appendChild(_hnSeznam("Úprava kalk. hodin vedoucí výroby", v.vp || [], false));
      box.appendChild(rada);

      var pozn = document.createElement("div");
      pozn.textContent = "Oba přehledy nahoře čtou stejné záznamy (typ 1) — tak je to " +
                         "i v Centrále, není to chyba zobrazení.";
      pozn.style.cssText = "font-size:11px;color:#94a3b8;margin:0 0 12px 0;";
      box.appendChild(pozn);

      box.appendChild(_hnSeznam("Úprava kalk. hodin — dílna (žádosti)", v.dilna || [], true));

      _okno("Úprava hodin vícepráce — " + zak, box, null, null, "820px");
    }).catch(function (e) {
      _cekam(false, "hodnavic");
      global.alert("Nepovedlo se otevřít hodiny vícepráce:\n\n" +
                   (e && e.message ? e.message : e) +
                   "\n\nPokud to trvalo dlouho, nejspíš zrovna běžela obnova zrcadla " +
                   "zakázek — zkus to prosím za chvíli znovu.");
    });
  }

  /* 📨 ODESLAT UKOL (Kristy 10.9.2026) — nahrada procedury Centraly
   * EC_Zakazky_VyhodnoceniOdesliUkol. Kazdy clovek z uzaverky, ktery ma
   * v Centrale priznak "Ukolnik", dostane do UKOLNIKU CENTRALY ukol s tim,
   * kolik za zakazku dostane (jmeno, hodiny, efektivita, odmena/srazka).
   * Poznamka ani premie se zamerne neposilaji — vedome rozhodnuti Dusana
   * z roku 2023, drzime ho.
   *
   * Backend je g2007.python `vyhodnoceni_ukol_send`, vola se pres uz existujici
   * POST /api/v1/erp/app/erp_registry/run (stejnou cestou jako podklad OSVC).
   * Odpoved chodi zabalena: {ok, verze, vysledek:{...}}.
   *
   * DVE KOLA: prvni volani (force=false) jen ZJISTI, jestli uz nekdo ukol
   * dostal, a vrati `potvrdit: true`. Teprve po dotazu uzivatele se vola znovu
   * s force=true. Centrala tuhle pojistku nema — dve kliknuti tam znamenaji
   * dva ukoly kazdemu. */
  function _ukol(inst, force) {
    var zak = _zakazka(inst);
    if (!zak) { global.alert("Není načtená zakázka."); return; }

    _cekam(true, "ukol");
    fetch("/api/v1/erp/app/erp_registry/run", {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ kod: "vyhodnoceni_ukol_send", args: [zak, "__uid__", !!force] })
    }).then(function (r) {
      return r.json().then(function (j) { return { stav: r.status, j: j }; });
    }).then(function (o) {
      _cekam(false, "ukol");
      var v = (o.j && o.j.vysledek) ? o.j.vysledek : o.j;
      if (!v || v.ok !== true) {
        global.alert("Úkoly se neodeslaly:\n\n" +
                     ((v && (v.chyba || v.error)) || ("HTTP " + o.stav)));
        return;
      }

      /* Nekdo uz ukol ma → zeptat se, ne poslat potichu podruhe. */
      if (v.potvrdit) {
        var kdo = (v.uz_meli || []).join(", ");
        var txt = "Těmto lidem už úkol s tímhle předmětem jednou odešel:\n\n" + kdo +
                  "\n\nPoslat jim ho znovu?\n\n" +
                  "OK = poslat všem znovu\n" +
                  "Storno = neposílat nikomu";
        if (v.zbyva > 0) {
          txt += "\n\n(Zbylým " + v.zbyva + " lidem, kteří ho ještě nedostali, " +
                 "se odešle tak jako tak — dej OK.)";
        }
        if (global.confirm(txt)) { _ukol(inst, true); }
        return;
      }

      var hl = "Odesláno úkolů: " + v.odeslano;
      if (v.komu && v.komu.length) { hl += "\n\n" + v.komu.join("\n"); }
      if (v.bez_priznaku && v.bez_priznaku.length) {
        hl += "\n\nBez příznaku „Úkolník“ (úkol nedostali):\n" + v.bez_priznaku.join("\n");
      }
      if (v.chyby && v.chyby.length) {
        hl += "\n\n⚠️ Nepovedlo se:\n" + v.chyby.join("\n");
      }
      global.alert(hl);
    }).catch(function (e) {
      _cekam(false, "ukol");
      global.alert("Chyba spojení: " + (e && e.message ? e.message : e));
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
      else if (act.code === "hodnavic") { _hodnavic(inst); }
      else if (act.code === "ukol") { _ukol(inst, false); }
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
        /* ⚠️ VRACENO 11.9.2026 (Kristy: "ajaj, vidim prazdno").
         * Tady bylo `setTimeout(_obnovGridyVJadre, 400)`. Zpusobovalo to, ze grid
         * "Hodnoceni vse" zustal PRAZDNY, prestoze v paticce hlasil spravny pocet
         * radku ("Celkem: 5") — data do nej dosla, ale nevykreslila se. Zaroven
         * hlavicka formu ukazovala jeste hodnoty pred prepoctem. Vypada to na
         * souboj s `_reloadSpec`, ktery si gridy prestavuje sam: obnova trefila
         * okamzik, kdy grid v DOM uz byl, ale jeste nebyl zobrazeny, takze si
         * AG Grid spocital nulovy viewport a po zobrazeni ho neprepocital.
         * Neuhodnuto, jen popis chovani — pred dalsim pokusem to chce overit
         * (obnovovat jen kdyz offsetHeight > 0, pak vynutit redrawRows).
         * Prazdny grid u penez je horsi nez neobnoveny, proto zatim rucne. */
      }
    }).catch(function (e) {
      global.alert("Chyba spojení: " + (e && e.message ? e.message : e));
    }).then(function () {
      btn.disabled = false; btn.textContent = old;
    });
  }

  /* ---------------------------------------------------------------------
   * NAPOVEDA K TLACITKUM (C24 / Kristy, 11. 9. 2026)
   *
   * Zadani: "Bylo by dobre udelat k tlacitkum napovedu treba pres otaznik
   * do toho jadra." (Kristy 10. 9. 2026)
   *
   * Reseni je dvoji, protoze lista je zamerne kompaktni a musi se vejit
   * na JEDEN radek (viz komentar u bar.style nize) — otaznik u kazdeho
   * z jedenacti tlacitek by ji rozbil do dvou radku:
   *   1) kratka veta v nativnim tooltipu (title) primo na tlacitku,
   *   2) jedno tlacitko "?" vpravo, ktere otevre cely prehled.
   *
   * VSECHNO NIZE JE OVERENE VE ZDROJACICH, ne opsane z komentaru.
   * Zvlast ec.prepocet_vyhodnoceni — precteny cely 11. 9. 2026, protoze
   * do ted jsem o nem vedela jen z komentare v tomhle souboru a psat
   * Dusanovi neoverena cisla je horsi nez nepsat nic. Co z toho vzeslo
   * a v puvodnim popisu chybelo:
   *   • premie se pocita VYHRADNE pri efektivite presne 100 (CASE WHEN
   *     V.efektivita_osoba=100 ... ELSE 0) — nekrati se pomerne, jak by
   *     clovek cekal. Pri 99 % je premie nula.
   *   • premie_osoba_final = ceil(premie_osoba/5)*5 — zaokrouhleni NAHORU
   *     na cele petikoruny, az po vypoctu.
   *   • srazka zadnou takovou podminku nema — pocita se i pri nizsi
   *     efektivite.
   *   • poznamka_vv je GENEROVANA (sklada se ze tri casti primo v teto
   *     funkci) — cokoli do ni kdo napise, pristi prepocet prepise.
   *     Proto ma Dusan od 11. 9. v gridu vedle ni "Poznamka sefmonter".
   *   • lidi s nula hodinami funkce po nacteni hodin SMAZE.
   * --------------------------------------------------------------------- */
  var NAPOVEDA = [
    {
      kod: null,
      nadpis: "Jak to jde za sebou",
      body: [
        "Tlačítka <b>1 → 2 → 3</b> jsou očíslovaná schválně — v tomhle pořadí na sebe navazují:",
        "<b>1</b> načte z docházky, <i>kdo</i> na zakázce dělal · <b>2</b> uloží sazby a spočítá <i>hlavičku</i> zakázky · <b>3</b> z té hlavičky rozpočítá <i>prémie na lidi</i>.",
        "Když se pustí 3 před 2, přepočet počítá ze staré hlavičky a prémie vyjdou z neaktuálních hodin. Přeskočit krok jde, <b>prohodit ne</b>.",
        "Běžná úprava jednoho člověka (efektivita, poznámka) žádné z těchto tlačítek nepotřebuje — edituje se rovnou v gridu a ukládá se sama. Tlačítko <b>3</b> je až potom, aby se prémie přepočítala."
      ]
    },
    {
      kod: "priprava",
      nadpis: "1️⃣ ▶️ Připravit hodnocení",
      kratce: "Načte podle docházky, kdo na zakázce dělal. Druhé spuštění smaže ruční zadání.",
      body: [
        "Je to krok <b>„načti mi, kdo na tom dělal“</b>, ne „obnov mi čísla“. Na obnovu čísel je tlačítko 3.",
        "Postupně: odmítne zakázku uzamčenou z Centrály → <b>smaže dosavadní řádky hodnocení téhle zakázky</b> → založí je znovu, jeden za každého, kdo má odpracované hodiny na některé zakázce ze skupiny (všem efektivita 100 %, nikdo šéfmontér, hodiny 0) → spustí přepočet, který teprve doplní hodiny a prémie.",
        "⚠️ <b>Druhé spuštění zahodí ruční práci:</b> efektivity, hodnocení flexibility, chybovosti a estetiky včetně poznámek, speciální prémie a poznámky.",
        "✅ <b>Označení šéfmontéra se zachová</b> — je uložené u zakázky, ne u člověka, a přepočet ho dosadí zpátky."
      ]
    },
    {
      kod: "koeficienty",
      nadpis: "2️⃣ ⚙️ Nastav koeficienty",
      kratce: "Sazby a rezerva zakázky. Po OK rovnou spočítá hlavičku. Musí běžet před tlačítkem 3.",
      body: [
        "Otevře šest polí hlavičky zakázky: sazba prémie, sazba srážky, konstanta času – rezerva, prémie šéfmontér, prémie šéfmontér / hodin, koeficient prémie šéfmontéra.",
        "<b>Prázdné pole = ponechat beze změny.</b> Rezerva musí být větší než nula.",
        "Po <b>Uložit a přepočítat</b> se hodnoty uloží a hned se spočítá hlavička: kalkulované hodiny, odpracováno, <b>limit pro srážku (= kalkulované hodiny s efektivitou × rezerva)</b>, ušetřený a přetažený čas a seznam sloučených zakázek.",
        "Kalkulované hodiny se berou ze zrcadla Centrály. Pokud některá zakázka ze skupiny v zrcadle zrovna chybí, výpočet se <b>raději neprovede</b> a ohlásí to — jinak by počítal z neúplných hodin.",
        "Uzamčenou zakázku odmítne. Vyžaduje oprávnění."
      ]
    },
    {
      kod: "prepocet",
      nadpis: "3️⃣ 🔄 Přepočet hodnocení",
      kratce: "Rozpočítá hodiny a prémie na jednotlivé lidi. Prémie jen při efektivitě 100 %.",
      body: [
        "<b>Hodiny:</b> sečte odpracované hodiny z docházky za <b>celou skupinu</b> sloučených zakázek; činnosti označené „nepočítat do hodnocení“ vynechá.",
        "<b>Kdo má po tomhle nula hodin, ze seznamu zmizí</b> (řádek se smaže).",
        "<b>Prémie na osobu</b> = (hodiny osoby ÷ odpracováno) × (kalkulováno s efektivitou − odpracováno s efektivitou) × sazba prémie.",
        "⚠️ <b>Prémie se počítá jen tomu, kdo má efektivitu přesně 100.</b> Při jakékoli nižší je prémie <b>nula</b> — nekrátí se poměrně, jak by člověk čekal. Při 99 % tedy člověk nedostane 99 % prémie, ale nic.",
        "<b>Vyplácená částka</b> (Prémie osoba final) se zaokrouhlí <b>nahoru na celých 5 Kč</b>.",
        "<b>Srážka</b> = (hodiny osoby ÷ odpracováno) × (odpracováno s efektivitou − limit pro srážku) × sazba srážky, a to jen když zakázka limit překročila. <b>Na srážku efektivita vliv nemá</b> — počítá se i lidem pod 100 %.",
        "<b>Prémie šéfmontéra</b> se přizná jen když platí všechno zároveň: je označený šéfmontér · kalkulované hodiny ≥ „prémie šéfmontér / hodin“ · zakázka <b>ne</b>přetáhla limit · největší zakázka ve skupině má aspoň tolik kalkulovaných hodin. Pak = základ × počet zakázek nad tím limitem hodin + koeficient × jeho prémie.",
        "⚠️ <b>Sloupec „Poznámka VV“ přepočet přepíše</b> — skládá si ho sám z nepodepsaného zakázkového listu, rozpisu prémie šéfmontéra a upozornění na efektivitu pod 100 %. Co do něj kdo napíše, příští přepočet zahodí. <b>Ruční text patří do „Poznámka šéfmontér“.</b>",
        "Uzamčenou zakázku (i kteroukoli ze skupiny) odmítne."
      ]
    },
    {
      kod: "uzavrit",
      nadpis: "4️⃣ 🔒 Uzavřít",
      kratce: "Vytvoří z hodnocení výplaty (SuperHrubá mzda). Vyžaduje oprávnění.",
      body: [
        "Zapíše spočtené odměny do financí zakázek jako výplaty (SuperHrubá mzda).",
        "Po uzavření už <b>nejde zapsat hodiny vícepráce</b> tlačítkem ⏱️ — to je naše pojistka navíc, Centrála je v tomhle volnější.",
        "Vzít zpátky to jde tlačítkem ↩️ Zrušit."
      ]
    },
    {
      kod: "do_mezd",
      nadpis: "5️⃣ 💰 Do mezd",
      kratce: "Zapíše odměny do mzdy (složka 651) za měsíc uzavření. Opakování nevadí.",
      body: [
        "Odměny z uzavřené zakázky se zapíšou zaměstnancům do mzdy jako složka 67 (v Heliosu 651), a to za <b>měsíc, kdy byla zakázka uzavřena</b> — ne za měsíc, kdy se na ní dělalo.",
        "Spustit to jde <b>opakovaně</b> — co už ve mzdě je, se nezdvojí.",
        "Vyžaduje oprávnění."
      ]
    },
    {
      kod: "zrusit",
      nadpis: "↩️ Zrušit",
      kratce: "Smaže výplaty, zakázku zarchivuje a znovu otevře k přepočtu.",
      body: [
        "Smaže vypočtené výplaty, zakázku zarchivuje a znovu ji otevře, takže se dá přepočítat.",
        "Smaže i mzdové řádky — ale <b>pokud už některý byl předán do mzdy</b> (stav <i>exported</i>), zrušení se odmítne a musí to vyřešit mzdová účetní.",
        "Vyžaduje oprávnění."
      ]
    },
    {
      kod: "hodnavic",
      nadpis: "⏱️ Úprava hodin vícepráce…",
      kratce: "Přidá hodiny navíc do kalkulace. Zapisuje se do Centrály, u nás se projeví až po obnově zrcadla.",
      body: [
        "Okno ukazuje totéž co jádro 347 v Centrále: vlevo <b>úpravy kalk. hodin VP</b>, vpravo <b>úpravy vedoucího výroby</b>, dole <b>žádosti z dílny</b> (u těch je vidět žádané i schválené hodiny).",
        "Nahoře se zadává nový zápis: hodiny a minuty, důvod (nabízí se nejčastěji používané) a poznámka.",
        "Zapisuje se <b>do Centrály</b> jako <b>rovnou platná úprava</b>, ne jako žádost ke schválení, a k nám se uloží kopie.",
        "Po uzavření vyhodnocení se zápis nepustí.",
        "⚠️ <b>Centrála si kalkulaci přepočítá hned, u nás ne.</b> V prémiích se to projeví až po obnově zrcadla zakázek (~30 min) a novém spuštění <b>2️⃣ Nastav koeficienty</b> a <b>3️⃣ Přepočet hodnocení</b>. Píše se to i v hlášce po uložení."
      ]
    },
    {
      kod: "ukol",
      nadpis: "📨 Odeslat úkol…",
      kratce: "Každému pošle do Úkolníku Centrály jeho hodiny, efektivitu a odměnu.",
      body: [
        "Každému člověku z uzávěrky, který má v Centrále příznak <b>Úkolník</b>, založí a odešle úkol v <b>Úkolníku Centrály</b>: jméno, počet hodin, efektivita a odměna nebo srážka v Kč.",
        "Kdo příznak nemá, úkol nedostane — funkce ho vypíše, ať je vidět, na koho se nedostalo.",
        "Když už někdo úkol s tímhle předmětem dostal, <b>zeptá se</b>, jestli poslat znovu.",
        "Poznámka ani prémie šéfmontéra se stejně jako v Centrále <b>neposílají</b> — je to vědomé rozhodnutí z roku 2023.",
        "Vyžaduje oprávnění."
      ]
    },
    {
      kod: "sefmonter",
      nadpis: "👷 Šéfmontér…",
      kratce: "Označí šéfmontéra zakázky. Dalším kliknutím na téhož ho odznačí.",
      body: [
        "Vybere se z lidí, kteří jsou na zakázce. Dalším kliknutím na téhož člověka se označení zruší.",
        "Ukládá se <b>u zakázky</b>, ne u člověka — proto ho „Připravit hodnocení“ nesmaže a přepočet ho vždycky dosadí zpátky.",
        "Prémie šéfmontéra se ale přizná až podle podmínek v tlačítku 3 — samotné označení na ni nestačí."
      ]
    },
    {
      kod: "slouci",
      nadpis: "🔗 Hodnotit společně…",
      kratce: "Sloučí zakázku s dalšími — hodiny i kalkulace se sečtou přes celou skupinu.",
      body: [
        "Zakázky se pak hodnotí <b>dohromady</b>: hodiny i kalkulace se sečtou a prémie se rozdělí přes celou skupinu.",
        "Většina výpočtů (hodiny z docházky, kontrola uzamčení, kalkulované hodiny) od té chvíle pracuje se skupinou, ne s jednou zakázkou."
      ]
    },
    {
      kod: "rozdelit",
      nadpis: "✂️ Zrušit sloučení",
      kratce: "Vyjme tuhle zakázku ze skupiny. Ostatní zůstanou spolu.",
      body: [
        "Tahle zakázka se bude hodnotit sama. Ostatní zakázky ve skupině zůstanou sloučené mezi sebou."
      ]
    },
    {
      kod: "soucet",
      nadpis: "Σ Prémie (vpravo v liště)",
      kratce: "Součet prémií a srážek za zakázku plus počet lidí. Kliknutím se přepočítá.",
      body: [
        "Počítá se ze <b>stejných řádků, jaké jsou v gridu „Hodnocení vše“</b>, takže vždycky odpovídá tomu, co je vidět. Obnovuje se sám po každé změně, kliknutím se dá přepočítat hned.",
        "Od 11. 9. 2026 ukazuje <b>totéž co „Prémie celkem“ v hlavičce</b> — obojí sčítá stejné řádky. Do té doby se to mohlo rozcházet, protože hlavička držela číslo z posledního přepočtu; teď se dopočítává až při otevření zakázky."
      ]
    }
  ];

  /* Kratky popis pro nativni tooltip (title) na tlacitku. */
  function _napovedaKratce(kod) {
    for (var i = 0; i < NAPOVEDA.length; i++) {
      if (NAPOVEDA[i].kod === kod && NAPOVEDA[i].kratce) return NAPOVEDA[i].kratce;
    }
    return null;
  }

  function _napoveda() {
    var box = document.createElement("div");
    box.style.cssText = "font-size:13px;line-height:1.55;color:#0f172a;";

    var uvod = document.createElement("div");
    uvod.style.cssText = "padding:8px 10px;margin:0 0 12px 0;background:#eff6ff;" +
      "border:1px solid #bfdbfe;border-radius:6px;color:#1e3a8a;";
    uvod.innerHTML = "Krátkou verzi ukáže i <b>najetí myší na tlačítko</b>. " +
      "Tohle okno je podrobné — co která akce opravdu dělá a co po ní zmizí.";
    box.appendChild(uvod);

    NAPOVEDA.forEach(function (s) {
      var sek = document.createElement("div");
      sek.style.cssText = "margin:0 0 14px 0;";

      var h = document.createElement("div");
      h.innerHTML = s.nadpis;
      h.style.cssText = "font-weight:600;font-size:14px;margin:0 0 4px 0;color:#0f172a;" +
        "border-bottom:1px solid #e2e8f0;padding-bottom:3px;";
      sek.appendChild(h);

      if (s.kratce) {
        var k = document.createElement("div");
        k.textContent = s.kratce;
        k.style.cssText = "color:#475569;font-style:italic;margin:0 0 5px 0;";
        sek.appendChild(k);
      }

      var ul = document.createElement("ul");
      ul.style.cssText = "margin:0;padding-left:18px;";
      s.body.forEach(function (radek) {
        var li = document.createElement("li");
        li.innerHTML = radek;
        li.style.cssText = "margin:0 0 3px 0;";
        ul.appendChild(li);
      });
      sek.appendChild(ul);
      box.appendChild(sek);
    });

    var pata = document.createElement("div");
    pata.style.cssText = "margin-top:6px;padding-top:8px;border-top:1px solid #e2e8f0;" +
      "color:#64748b;font-size:11px;";
    pata.textContent = "Vyhodnocení zakázek · nápověda ověřená proti zdrojovým funkcím, 11. 9. 2026";
    box.appendChild(pata);

    _okno("Nápověda k tlačítkům", box, null, null, "780px");
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
      var t1 = _napovedaKratce(act.code); if (t1) { b.title = t1; }
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
      if (act.code === "hodnavic" || act.code === "ukol") { b.setAttribute("data-ec-cekam", act.code); }
      var t2 = _napovedaKratce(act.code); if (t2) { b.title = t2; }
      b.onclick = function () { _vlastni(inst, act, b); };
      bar.appendChild(b);
    });
    /* NAPOVEDA (C24 / Kristy, 11. 9. 2026). Jedno tlacitko misto otazniku
     * u kazde akce — lista se musi vejit na jeden radek. Kratkou verzi ke
     * kazdemu tlacitku dava title (tooltip pri najeti mysi), nastaveny vyse. */
    var bNap = document.createElement("button");
    bNap.type = "button";
    bNap.textContent = "❔";
    bNap.title = "Nápověda — co které tlačítko dělá";
    bNap.setAttribute("aria-label", "Nápověda k tlačítkům");
    bNap.style.cssText = "cursor:pointer;padding:4px 9px;border:1px solid #bfdbfe;border-radius:6px;" +
      "background:#eff6ff;color:#1e3a8a;font-size:12px;line-height:1.2;white-space:nowrap;font-weight:600;";
    bNap.onmouseenter = function () { bNap.style.background = "#dbeafe"; };
    bNap.onmouseleave = function () { bNap.style.background = "#eff6ff"; };
    bNap.onclick = function () { try { _napoveda(); } catch (e) { global.alert("Nápovědu se nepodařilo otevřít."); } };
    bar.appendChild(bNap);

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

    /* Po zavreni jadra (OK i akce z listy) srovnat prehled pod nim — Kristy
     * 11.9.2026: cislo v prehledu zustavalo z doby pred vyhodnocenim. */
    _navesObnovuPrehledu(inst);
  }

  /* ═══════════════════════════════════════════════════════════════════
   * OBNOVA GRIDU (Kristy 11.9.2026)
   * ═══════════════════════════════════════════════════════════════════
   * Dva pozadavky:
   *   1) po "3 Prepocet hodnoceni" obnovit grid "Hodnoceni vse" v jadre,
   *   2) po OK na jadre obnovit prehled zakazek pod nim.
   *
   * PROC TO NESTACILO: `_reloadSpec()` prekresli FORMULAR (pole hlavicky),
   * ale embedded gridy uvnitr si data drzi ve vlastni ErpDataGrid instanci
   * a prekresleni formu je nepreptaa. Cisla v hlavicce tedy sedela, ale
   * radky v gridu byly z doby pred prepoctem.
   *
   * JAK SE K INSTANCI GRIDU DOSTAT: ErpDataGrid si na DOM element zpetny
   * odkaz neuklada (`this.container = container`, ale ne naopak). Wrapneme
   * proto `_init` a znacku si doplnime sami — stejny vzor, jakym uz tenhle
   * soubor wrapuje `DesignFwForm.prototype._render`. Zadny zasah do
   * frameworku (datagrid.js ani design_forms.js).
   *
   * OBNOVA SAMOTNA: `options.onRefresh()` je tataz cesta, kterou pouziva
   * tlacitko Obnovit v liste gridu — znovu natahne data a nastavi je do AG
   * Gridu, takze zustane sirka sloupcu i ulozena sestava. */
  var GRID_MARKER = "__ecVyhGrid";

  function _installGridMarker() {
    var G = global.ErpDataGrid;
    if (!G || !G.prototype || G.prototype.__ecVyhGridWrapped) {
      return !!(G && G.prototype && G.prototype.__ecVyhGridWrapped);
    }
    var origInit = G.prototype._init;
    if (typeof origInit !== "function") return false;
    G.prototype._init = function () {
      var r = origInit.apply(this, arguments);
      try { if (this.container) { this.container[GRID_MARKER] = this; } } catch (e) {}
      return r;
    };
    G.prototype.__ecVyhGridWrapped = true;
    return true;
  }

  /* Obnovi vsechny embedded gridy uvnitr jadra (Hodnoceni vse, Hodiny zakazek,
   * Hodiny navic, Vysvetleni zisku, Slouceny zakazky, Finalni vyhodnoceni).
   * Zamerne vsechny — prepocet muze zmenit kterykoli z nich a obnova navic
   * nic nestoji. Vraci pocet obnovenych. */
  function _obnovGridyVJadre(inst) {
    var n = 0;
    try {
      var host = inst && inst._shell && inst._shell.body;
      if (!host) return 0;
      var uzly = host.querySelectorAll(".erp-ag-grid");
      for (var i = 0; i < uzly.length; i++) {
        var g = uzly[i][GRID_MARKER];
        if (!g || g._destroyed) continue;
        var fn = g.options && g.options.onRefresh;
        if (typeof fn !== "function") continue;
        try { fn(); n++; } catch (e) {}
      }
    } catch (e) {}
    return n;
  }

  /* Obnovi PREHLED zakazek k vyhodnoceni (fw.core 199), tedy grid POD jadrem.
   * Hleda se podle coreInfo.coreId, ne podle poradi v DOM — jadro je modal
   * nad strankou a gridu muze byt na strance vic.
   * Fallback: klik na tlacitko Obnovit v CRUD liste (tutez cestu pouziva
   * `ec_vyhodnoceni_prehled_refresh.js`). */
  var PREHLED_CORE_ID = 199;

  function _obnovPrehled() {
    try {
      var uzly = document.querySelectorAll(".erp-ag-grid");
      for (var i = 0; i < uzly.length; i++) {
        var g = uzly[i][GRID_MARKER];
        if (!g || g._destroyed) continue;
        var cid = null;
        try { cid = g.options.coreInfo.coreId; } catch (e) {}
        if (cid !== PREHLED_CORE_ID) continue;
        if (typeof g._makeRefreshFn === "function" && g.gridApi) {
          var fn = g._makeRefreshFn(g.gridApi);
          if (typeof fn === "function") { fn(); return true; }
        }
        var of = g.options && g.options.onRefresh;
        if (typeof of === "function") { of(); return true; }
      }
    } catch (e) {}
    try {
      var b = document.querySelector('.erp-grid-action-btn[data-action="refresh"]');
      if (b) { b.click(); return true; }
    } catch (e) {}
    return false;
  }

  /* Navesi obnovu prehledu na zavreni jadra. Zamerne na `close`, ne na
   * `onSaveSuccess`: jadro se zavira i po akcich z listy (Uzavrit, Do mezd,
   * Zrusit), ktere hlavicku meni taky, a po nich se prehled musi srovnat
   * stejne jako po OK. Obalime jednou (priznak na instanci shellu). */
  function _navesObnovuPrehledu(inst) {
    try {
      var sh = inst && inst._shell;
      if (!sh || typeof sh.close !== "function" || sh.__ecVyhCloseWrapped) return;
      var origClose = sh.close;
      sh.close = function () {
        var r = origClose.apply(this, arguments);
        /* Az po zavreni — grid pod jadrem musi byt zase v DOM a viditelny.
         * 150 ms staci na dobehnuti zaviraci animace shellu. */
        setTimeout(function () { try { _obnovPrehled(); } catch (e) {} }, 150);
        return r;
      };
      sh.__ecVyhCloseWrapped = true;
    } catch (e) {}
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

  /* Marker na gridech se vesi nezavisle na jadre — datagrid.js se muze nacist
   * pozdeji nez tenhle soubor. */
  if (!_installGridMarker()) {
    var triesG = 0;
    var ivG = setInterval(function () {
      triesG++;
      if (_installGridMarker() || triesG > 100) clearInterval(ivG);
    }, 100);
  }
})(window);
