  function hr_hub(){
    app.innerHTML=topbar("👥 HR — personalistika", true);
    app.appendChild(el('<div class="hint" style="margin:6px 6px 2px;line-height:1.6;">Tvoje sekce, Šárko — celá personalistika na jednom místě. Bloky: interní lidé, nábor, docházka a absence, nemoc/OČR, mzdy a dokumenty, přístupy. S Claudem‑25 si ji můžeš upravovat a doplňovat.</div>'));
    var _nb=null;
    var kpi=el('<div id="hrKpi" style="display:flex;gap:8px;margin:8px 2px 2px;"></div>'); app.appendChild(kpi);
    function kc(lbl,val,col){ return '<div style="flex:1;background:rgba(255,255,255,.03);border:1px solid var(--bord);border-radius:12px;padding:10px 6px;text-align:center;"><div style="font-size:22px;font-weight:800;color:'+col+';">'+(val==null?"…":val)+'</div><div style="font-size:10.5px;color:var(--mut);line-height:1.2;margin-top:2px;">'+lbl+'</div></div>'; }
    function drawKpi(){ kpi.innerHTML=kc("Nábor — kandidáti",_nb,"#a78bfa"); }
    drawKpi();
    api("GET","/api/v1/erp/app/recruit/pipeline","").then(function(j){ if(j&&j.ok){ _nb=j.candidates; drawKpi(); } else { kpi.style.display="none"; } });
    function s(t){ app.appendChild(el('<div style="margin:14px 6px 6px;font-size:12px;font-weight:700;letter-spacing:.5px;color:#7c8cdb;">'+t+'</div>')); }
    s("INTERNÍ PERSONALISTIKA");
    var g1=el('<div class="appgrid"></div>');
    g1.appendChild(appCell("🏛️","Firma",0,function(){go("hr_firma");}));
    g1.appendChild(appCell("👥","Skupiny",0,function(){go("hr_skupiny");}));
    g1.appendChild(appCell("📋","Podmínky",0,function(){go("hr_podminky");}));
    g1.appendChild(appCell("🪪","Lidé — složky",0,function(){go("hr_people");}));
    g1.appendChild(appCell("🧩","Režimy",0,function(){go("hr_rezimy");}));
    app.appendChild(g1);
    s("NÁBOR (externí)");
    var g2=el('<div class="appgrid"></div>');
    g2.appendChild(appCell("🧲","Nábor",0,function(){go("hr_nabor");}));
    g2.appendChild(appCell("👤","Kandidáti",0,function(){window._nbFilter={phase:"",title:"👤 Kandidáti"};go("hr_nabor_list");}));
    g2.appendChild(appCell("💬","Pohovory",0,function(){window._nbFilter={phase:"active",title:"💬 Pohovory — ve hře"};go("hr_nabor_list");}));
    g2.appendChild(appCell("📨","Nástupy",0,function(){window._nbFilter={phase:"hired",title:"📨 Nástupy"};go("hr_nabor_list");}));
    g2.appendChild(appCell("📣","Inzeráty",0,function(){go("hr_inzeraty");}));
    app.appendChild(g2);
    s("DOCHÁZKA & ABSENCE");
    var g3=el('<div class="appgrid"></div>');
    g3.appendChild(appCell("👀","Kdo kde dnes",0,function(){go("kdekdo");}));
    g3.appendChild(appCell("🗓️","Absence — schvalování",0,function(){go("absence");}));
    g3.appendChild(appCell("🗓️","Zdroj docházky",0,function(){go("hr_att_source");}));
    g3.appendChild(appCell("📥","Import z EUROSOFTu",0,function(){go("hr_import");}));
    app.appendChild(g3);
    s("NEMOC · OČR · LÉKAŘ");
    var g4=el('<div class="appgrid"></div>');
    g4.appendChild(appCell("🤒","Nemocenská",0,function(){go("sick_schval");}));
    g4.appendChild(appCell("🧑‍⚕️","Ošetřovné (OČR)",0,function(){go("ocr_schval");}));
    g4.appendChild(appCell("🩺","Lístečky lékař",0,function(){go("med_schval");}));
    g4.appendChild(appCell("📋","Nemoc/OČR přehled",0,function(){go("np_prehled");}));
    app.appendChild(g4);
    s("MZDY & DOKUMENTY");
    var g5=el('<div class="appgrid"></div>');
    g5.appendChild(appCell("🏦","Uzávěrka konta",0,function(){go("hr_konto");}));
    g5.appendChild(appCell("📄","Generovat dokument",0,function(){go("doc_gen");}));
    g5.appendChild(appCell("💰","Mzdy: Helios × my",0,function(){go("wage_cmp");}));
    app.appendChild(g5);
    s("PŘÍSTUPY");
    var g6=el('<div class="appgrid"></div>');
    g6.appendChild(appCell("🔑","Skupina HR — přístupy",0,function(){window._skFocusName='HR';go("skupiny");}));
    app.appendChild(g6);
  }
  function hr(){
    app.innerHTML=topbar("🔒 HR — personalistika", true);
    var dash=el('<div id="hrDash"></div>'); app.appendChild(dash); _hrDash(dash);
    var l=el('<div class="list"></div>');
    l.appendChild(row("🏢","Interní personalistika","Naši lidé — firma, skupiny, jednotlivci, režimy, docházka",function(){ go("hr_interni"); }));
    l.appendChild(row("🧲","Externí personalistika — nábor","Inzeráty, pohovory a pracovní nabídky pro nové lidi",function(){ go("hr_nabor"); }));
    l.appendChild(row("🪪","Moje osobní údaje","Zadej a aktualizuj svá data (pro každého)",function(){ go("hr_me"); }));
    l.appendChild(row("🧑‍⚕️","Ošetřovné (OČR)","Založ OČR ze SMS od ČSSZ, po skončení doplň dny",function(){ go("ocr"); }));
    l.appendChild(row("🤒","Nemocenská (eNeschopenka)","Nahlas nemoc, po uzdravení doplň konec",function(){ go("sick"); }));
    l.appendChild(row("🩺","Lísteček od lékaře","Vyfoť lísteček, čerpá sick day / proplácí do limitu",function(){ go("med"); }));
    app.appendChild(l);
    app.appendChild(el('<div class="hint" style="margin-top:10px;line-height:1.6;">Personalistika má dva světy: <b>interní</b> (lidé, které už máme — od pravidel firmy přes skupiny po jednotlivce) a <b>externí</b> (nábor nových lidí). Citlivé personální složky vidí jen rodiče a „Skupina HR".</div>'));
  }
  // HR nástěnka (Šárka 23.6.): dlaždice s notifikací + Aktuality
  function _hrDash(box){
    box.innerHTML='<div class="hint" style="margin:8px 6px;">Načítám nástěnku…</div>';
    api("GET","/app/hr/dashboard").then(function(r){
      box.innerHTML="";
      if(!r||!r.ok){ box.appendChild(el('<div class="hint" style="margin:8px 6px;">Nástěnku se nepodařilo načíst.</div>')); return; }
      var b=r.badges||{};
      var g=el('<div class="appgrid" style="margin:8px 6px;"></div>');
      g.appendChild(appCell("🏠","Mimo kancelář",b.mimo,function(){ go("kdekdo"); }));
      g.appendChild(appCell("🎂","Narozeniny a výročí",b.naroz,function(){ go("hr_naroz"); }));
      g.appendChild(appCell("🆕","Noví zaměstnanci",b.novi,function(){ go("hr_novi"); }));
      g.appendChild(appCell("🧲","Výběrová řízení",b.vyberka,function(){ go("hr_nabor"); }));
      g.appendChild(appCell("✉️","Mé zprávy",0,function(){ hrSoon("Mé zprávy k lidem","Komunikace s lidmi — jednotlivě i celé skupině. Připravujeme (Krok B): napíšeš zprávu, doručí se a cinkne dotyčným."); }));
      box.appendChild(g);
      box.appendChild(_hrSec("📰 AKTUALITY"));
      var a=el('<div class="list"></div>');
      (r.aktuality||[]).forEach(function(it){ a.appendChild(row(it.ikona,it.text,"",function(){})); });
      if(!(r.aktuality||[]).length) a.appendChild(el('<div class="hint" style="margin:6px;">Nic nového. 🎉</div>'));
      box.appendChild(a);
    }).catch(function(){ box.innerHTML='<div class="hint" style="margin:8px 6px;">Nástěnku se nepodařilo načíst.</div>'; });
  }
  function _hrFeed(title, types){
    app.innerHTML=topbar(title, true);
    var box=el('<div></div>'); app.appendChild(box);
    box.innerHTML='<div class="hint" style="margin:8px 6px;">Načítám…</div>';
    api("GET","/app/hr/dashboard").then(function(r){
      box.innerHTML="";
      var items=((r&&r.aktuality)||[]).filter(function(it){ return types.indexOf(it.typ)>=0; });
      var a=el('<div class="list"></div>');
      items.forEach(function(it){ a.appendChild(row(it.ikona,it.text,"",function(){})); });
      if(!items.length) a.appendChild(el('<div class="hint" style="margin:6px;">Nic k zobrazení.</div>'));
      box.appendChild(a);
    });
  }
  function hr_naroz(){ _hrFeed("🎂 Narozeniny a výročí", ["narozeniny","vyroci"]); }
  function hr_novi(){ _hrFeed("🆕 Noví zaměstnanci", ["novy","zkusebka","prodlouzeni"]); }
  // INTERNÍ — kostra shora dolů (firma → skupiny → jednotlivci → mzdy/dokumenty)
  function hr_interni(){
    app.innerHTML=topbar("🏢 Interní personalistika", true);
    app.appendChild(el('<div class="hint" style="margin:8px 6px 0;line-height:1.6;">Pravidla tečou shora dolů: firma dá rámec, skupina ho zpřesní, jednotlivec má své výjimky. Stejný vzor jako u docházky (systém → skupina → jednotlivec).</div>'));
    app.appendChild(_hrSec("FIRMA"));
    var l1=el('<div class="list"></div>');
    l1.appendChild(row("🏛️","Firma","Základ, kultura a pravidla firmy (EC + System)",function(){ go("hr_firma"); }));
    app.appendChild(l1);
    app.appendChild(_hrSec("SKUPINY"));
    var l2=el('<div class="list"></div>');
    l2.appendChild(row("👥","Skupiny","Rozdělení lidí + pravidla skupin",function(){ go("hr_skupiny"); }));
    l2.appendChild(row("📋","Podmínky skupin","Úvazek, nástup, dovolená, sick days… + výjimky",function(){ go("hr_podminky"); }));
    app.appendChild(l2);
    app.appendChild(_hrSec("JEDNOTLIVCI"));
    var l3=el('<div class="list"></div>');
    l3.appendChild(row("🪪","Lidé — personální složky","Karta člověka: režim · podmínky · docházka",function(){ go("hr_people"); }));
    l3.appendChild(row("🧩","Režimy","Forma HPP/OSVČ/DPP, režim docházky, konto",function(){ go("hr_rezimy"); }));
    l3.appendChild(row("🗓️","Zdroj docházky","Kdo píchá jen ve STRATEGII (a má vypnutou starou docházku)",function(){ go("hr_att_source"); }));
    l3.appendChild(row("🗓️","Absence — žádosti a schvalování","Dovolená / HO / lékař → schválí vedoucí",function(){ go("absence"); }));
    l3.appendChild(row("🧑‍⚕️","Ošetřovné (OČR) — schvalování","Případy ke schválení (EC i ES)",function(){ go("ocr_schval"); }));
    l3.appendChild(row("🤒","Nemocenská — schvalování","eNeschopenky ke schválení (EC i ES)",function(){ go("sick_schval"); }));
    l3.appendChild(row("📋","Nemoc a OČR — přehled","Kdo je a byl na nemocenské / OČR",function(){ go("np_prehled"); }));
    l3.appendChild(row("🩺","Lístečky od lékaře — schvalování","Návštěvy + foto, sick day / proplácení",function(){ go("med_schval"); }));
    l3.appendChild(row("🩺","Lékař — přehled","Návštěvy, doba, proplaceno (EC i ES)",function(){ go("med_prehled"); }));
    l3.appendChild(row("👀","Kdo kde dnes","Kdo v práci / na dovolené / nemocný",function(){ go("kdekdo"); }));
    app.appendChild(l3);
    app.appendChild(_hrSec("MZDY & DOKUMENTY"));
    var l4=el('<div class="list"></div>');
    l4.appendChild(row("🏦","Uzávěrka konta","Rozpad přesčasů: prémie / přesčas / převést",function(){ go("hr_konto"); }));
    l4.appendChild(row("📥","Import docházky z EUROSOFTu","Reálná data 1:1 (dovolené, nemoc, lékař)",function(){ go("hr_import"); }));
    l4.appendChild(row("📄","Generovat dokument","Smlouva, výměr… → PDF z živých dat",function(){ go("doc_gen"); }));
    l4.appendChild(row("💰","Mzdy: Helios × STRATEGIE","Porovnání ZDROJ × CÍL × delta (vedení)",function(){ go("wage_cmp"); }));
    app.appendChild(l4);
    app.appendChild(_hrSec("PŘÍSTUPY"));
    var l5=el('<div class="list"></div>');
    l5.appendChild(row("🔑","Skupina HR — přístupy","Kdo vidí citlivé personální složky (rodiče)",function(){ window._skFocusName='HR'; go("skupiny"); }));
    app.appendChild(l5);
  }
  // FIRMA — nejvyšší patro (placeholder kostra)
  function hr_firma(){
    app.innerHTML=topbar("🏛️ Firma", true);
    app.appendChild(el('<div class="hint" style="margin:8px 6px;line-height:1.6;">Nejvyšší patro: rámec platný pro všechny. Co se nastaví tady, dědí se na skupiny i jednotlivce (pokud nemají vlastní výjimku).</div>'));
    var l=el('<div class="list"></div>');
    l.appendChild(row("🏢","Základní údaje firmy","Firmy grupy: EUROSOFT-Control a -System (IČO, sídlo)",function(){ hrSoon("Základní údaje firmy","Firmy grupy EUROSOFT-Control a -System: IČO, sídlo, kontakty, bankovní spojení. Zdroj pro smlouvy a výměry."); }));
    l.appendChild(row("🌱","Firemní kultura & hodnoty","Co u nás platí — férovost, volnost, dobrá parta",function(){ hrSoon("Firemní kultura & hodnoty","Hodnoty, na kterých EUROSOFT 20 let staví. Sdílené napříč firmou — onboarding novým lidem, připomínka stávajícím."); }));
    l.appendChild(row("📜","Pravidla firmy","Celofiremní pravidla (pracovní doba, benefity, etika)",function(){ hrSoon("Pravidla firmy","Celofiremní pravidla, která se dědí na skupiny: pracovní doba, benefity, etika, bezpečnost. Skupina i jednotlivec je můžou zpřesnit."); }));
    app.appendChild(l);
    app.appendChild(el('<div class="hint" style="margin-top:10px;">🚧 Kostra — obsah doplníme. Klikni na položku pro náhled.</div>'));
  }
  // SKUPINY — prostřední patro
  function hr_skupiny(){
    app.innerHTML=topbar("👥 Skupiny", true);
    app.appendChild(el('<div class="hint" style="margin:8px 6px;line-height:1.6;">Mezi firmou a jednotlivcem. Skupina zpřesní pravidla firmy (jiná pro výrobu, jiná pro kancelář) a jednotlivec si může nést výjimku.</div>'));
    var l=el('<div class="list"></div>');
    l.appendChild(row("👥","Správa skupin","Kdo do které skupiny patří",function(){ go("skupiny"); }));
    l.appendChild(row("📋","Pravidla skupin","Úvazek, dovolená, sick days, volby píchání po skupinách",function(){ go("hr_podminky"); }));
    app.appendChild(l);
  }
  // EXTERNÍ — nábor nových lidí (živá data z Centrály, migrace 13.6.)
  function hr_nabor(){
    app.innerHTML=topbar("🧲 Nábor nových lidí", true);
    app.appendChild(el('<div class="hint" style="margin:8px 6px;line-height:1.6;">Externí personalistika — kandidáti a jejich pipeline. Data převzatá z Centrály. Po přijetí kandidát „přeteče" do interní personalistiky (onboarding).</div>'));
    var dash=el('<div id="nbDash" class="hint" style="margin:0 6px 10px;">Načítám pipeline…</div>');
    app.appendChild(dash);
    // 📥 Import CV — Šárka nahraje životopis, systém ho přečte a předvyplní kartu uchazeče
    var imp=el('<button style="margin:6px;padding:11px 16px;border:0;border-radius:12px;background:linear-gradient(110deg,#34d399,#2dd4bf);color:#04150e;font-weight:700;cursor:pointer;width:calc(100% - 12px);">📥 Importovat CV (PDF/soubor) — předvyplní kandidáta</button>');
    imp.addEventListener("click",function(){ cvImport(false); });
    app.appendChild(imp);
    var cam=el('<button style="margin:0 6px 6px;padding:11px 16px;border:1px solid rgba(52,211,153,.5);border-radius:12px;background:rgba(52,211,153,.08);color:#5ee0b7;font-weight:700;cursor:pointer;width:calc(100% - 12px);">📷 Vyfotit CV fotoaparátem</button>');
    cam.addEventListener("click",function(){ cvImport(true); });
    app.appendChild(cam);
    var l=el('<div class="list"></div>');
    l.appendChild(row("👤","Kandidáti","Všichni uchazeči — profil v kontextu",function(){ window._nbFilter={phase:"",title:"👤 Kandidáti"}; go("hr_nabor_list"); }));
    l.appendChild(row("💬","Pohovory — ve hře","Aktivní pipeline: Ve hře / 1. a 2. kolo",function(){ window._nbFilter={phase:"active",title:"💬 Pohovory — ve hře"}; go("hr_nabor_list"); }));
    l.appendChild(row("📨","Nástupy","Přijatí — fáze nástup (→ onboarding)",function(){ window._nbFilter={phase:"hired",title:"📨 Nástupy"}; go("hr_nabor_list"); }));
    l.appendChild(row("📣","Inzeráty → Jobs.cz / Práce.cz","Tvorba a zveřejnění přes Teamio API",function(){ go("hr_inzeraty"); }));
    app.appendChild(l);
    api("GET","/api/v1/erp/app/recruit/pipeline","").then(function(j){
      if(!j||!j.ok){ dash.textContent=(j&&j.error==="forbidden")?"🔒 Nábor vidí jen rodiče a HR skupina.":"Pipeline se nepodařilo načíst."; return; }
      var bars=(j.phases||[]).map(function(p){ var col=p.hired?"#22c55e":"#4f8ef7"; return '<div style="display:flex;align-items:center;gap:8px;margin:3px 0;font-size:13.5px;"><span style="flex:1;">'+esc(p.faze)+'</span><b style="color:'+col+';">'+p.pocet+'</b></div>'; }).join("");
      dash.innerHTML='<div style="background:rgba(255,255,255,.03);border:1px solid var(--bord);border-radius:12px;padding:12px;">'+
        '<div style="font-weight:700;margin-bottom:6px;">📊 Pipeline · '+j.candidates+' kandidátů · '+j.total+' přihlášek</div>'+bars+'</div>';
    });
  }
  // Import CV: vyber PDF nebo vyfoť → base64 → server přečte + LLM strukturuje → karta uchazeče
  function cvImport(camera){
    var fi;
    if(camera){
      fi=el('<input type="file" accept="image/*" capture="environment" style="display:none;">');
    } else {
      fi=el('<input type="file" accept=".pdf,.doc,.docx,.rtf,.txt,image/*" style="display:none;">');
    }
    fi.addEventListener("change",function(){
      var f=fi.files&&fi.files[0]; if(!f)return;
      if(f.size>25*1024*1024){ alert("Soubor je moc velký (max 25 MB)."); return; }
      go("hr_cv_result"); // přepni na obrazovku s průběhem
      var box=document.getElementById("cvResBox");
      if(box) box.innerHTML='<div class="hint">⏳ Čtu životopis a vytahuji údaje… (pár vteřin)</div>';
      var fr=new FileReader();
      fr.onload=function(){
        var b64=String(fr.result).split(",")[1]||"";
        var fn=f.name||"";
        if(!fn){ var mt=(f.type||""); fn = mt.indexOf("png")>=0?"cv.png" : (mt.indexOf("image")>=0?"cv.jpg":"cv.pdf"); }
        api("POST","/api/v1/erp/app/recruit/cv-import",{file_b64:b64,filename:fn,position:""}).then(function(r){
          renderCvResult(r);
        }).catch(function(){ renderCvResult({ok:false,error:"Nepodařilo se odeslat."}); });
      };
      fr.readAsDataURL(f);
    });
    document.body.appendChild(fi); fi.click();
    setTimeout(function(){ try{document.body.removeChild(fi);}catch(e){} },60000);
  }
  function hr_cv_result(){
    app.innerHTML=topbar("📥 Import CV", true);
    app.appendChild(el('<div id="cvResBox" class="list"><div class="hint">⏳ Zpracovávám…</div></div>'));
  }
  function renderCvResult(r){
    var box=document.getElementById("cvResBox"); if(!box)return;
    if(!r||!r.ok){
      box.innerHTML='<div class="hint" style="color:#f87171;">✗ '+esc((r&&r.error)||"Nepodařilo se zpracovat.")+'</div>';
      return;
    }
    var c=r.card||{};
    function fld(lbl,val){ if(!val&&val!==0)return ""; return '<div style="display:flex;gap:8px;margin:4px 0;font-size:14px;"><span style="min-width:120px;color:var(--mut);">'+lbl+'</span><b style="flex:1;">'+esc(String(val))+'</b></div>'; }
    var warn = r.scanned ? '<div class="hint" style="color:#fbbf24;margin:6px 0;">⚠ Naskenované PDF bez textové vrstvy — údaje doplň ručně v detailu.</div>' : '';
    box.innerHTML=
      '<div style="background:rgba(52,211,153,.08);border:1px solid rgba(52,211,153,.4);border-radius:12px;padding:12px;margin:6px;">'+
        '<div style="font-weight:700;font-size:16px;margin-bottom:6px;">✅ Uchazeč založen</div>'+ warn +
        fld("Jméno", c.jmeno)+ fld("E-mail", c.email)+ fld("Telefon", c.telefon)+
        fld("Narození", c.narozeni)+ fld("Vzdělání", c.vzdelani)+
        fld("Poslední zam.", c.posl_zam)+ fld("Jazyky", c.jazyky)+
        fld("Praxe", c.praxe)+ fld("Oček. plat", (c.plat!=null?(c.plat+" Kč"):""))+
        (c.shrnuti?('<div style="margin-top:6px;font-style:italic;color:var(--tx);">"'+esc(c.shrnuti)+'"</div>'):'')+
      '</div>';
    var det=el('<button style="margin:6px;padding:11px 16px;border:0;border-radius:12px;background:#4f8ef7;color:#fff;font-weight:700;cursor:pointer;width:calc(100% - 12px);">Otevřít v náboru →</button>');
    det.addEventListener("click",function(){ window._nbAppId=r.application_id; go("hr_nabor_detail"); });
    box.appendChild(det);
    var another=el('<button style="margin:6px;padding:11px 16px;border:1px solid var(--bord);border-radius:12px;background:rgba(255,255,255,.04);color:var(--tx);cursor:pointer;width:calc(100% - 12px);">📥 Importovat další CV</button>');
    another.addEventListener("click",function(){ cvImport(); });
    box.appendChild(another);
  }
  // Inzeráty → Teamio (Jobs.cz/Práce.cz). Připraveno na API; publikace/stahování čeká na přístupy LMC (pondělí).
  function hr_inzeraty(){
    app.innerHTML=topbar("📣 Inzeráty → Jobs.cz / Práce.cz", true);
    app.appendChild(el('<div class="hint" style="margin:6px;line-height:1.5;">Inzeráty se publikují přes <b>Teamio API</b> (Jobs.cz, Práce.cz, Práce za rohem). Uchazeči se stáhnou zpět do Náboru. Přístupy od LMC se doplní v pondělí — do té doby vše připravíš, jen se nezveřejní.</div>'));
    var add=el('<button style="margin:6px;padding:11px 16px;border:0;border-radius:12px;background:linear-gradient(110deg,#34d399,#2dd4bf);color:#04150e;font-weight:700;cursor:pointer;">+ Nový inzerát</button>');
    add.addEventListener("click",function(){ window._inzId=null; go("hr_inzerat_edit"); });
    app.appendChild(add);
    var pull=el('<button style="margin:6px;padding:11px 16px;border:1px solid var(--bord);border-radius:12px;background:rgba(255,255,255,.04);color:var(--tx);cursor:pointer;">📥 Stáhnout uchazeče z Teamia</button>');
    pull.addEventListener("click",function(){ api("POST","/api/v1/erp/app/recruit/pull-replies",{}).then(function(r){ alert(r&&r.ok?("Staženo: "+(r.imported||0)):("ℹ️ "+((r&&r.error)||"?"))); }); });
    app.appendChild(pull);
    var box=el('<div class="list"><div class="hint">Načítám…</div></div>'); app.appendChild(box);
    api("GET","/api/v1/erp/app/recruit/postings","").then(function(j){
      box.innerHTML="";
      if(!j||!j.ok){ box.innerHTML='<div class="hint">'+((j&&j.error==="forbidden")?"🔒 Vidí jen rodiče a HR.":"Nepodařilo se načíst.")+'</div>'; return; }
      if(!j.items.length){ box.innerHTML='<div class="hint">Zatím žádný inzerát. Přidej první.</div>'; return; }
      j.items.forEach(function(p){
        var st=p.status==="published"?("✅ zveřejněno"+(p.published?(" "+p.published):"")):"📝 koncept";
        box.appendChild(row("📣",p.title,(p.profession?p.profession+" · ":"")+(p.city?p.city+" · ":"")+st,function(){ window._inzId=p.id; go("hr_inzerat_edit"); }));
      });
    });
  }
  function _izV(id){ var e=document.getElementById(id); return e?e.value:""; }
  function hr_inzerat_edit(){
    app.innerHTML=topbar(window._inzId?"Úprava inzerátu":"Nový inzerát", true);
    var c=el('<div style="margin:6px;"></div>'); app.appendChild(c);
    function fld(lb,id,ph,t){ return '<div style="margin:6px 0;"><div style="font-size:12px;color:var(--mut);margin-bottom:2px;">'+lb+'</div><input id="'+id+'" type="'+(t||"text")+'" placeholder="'+(ph||"")+'" style="width:100%;box-sizing:border-box;padding:9px;border-radius:9px;border:1px solid var(--bord);background:rgba(255,255,255,.04);color:var(--tx);"></div>'; }
    var h=fld("Název pozice","izTitle","Elektromontér / PLC programátor…")
      +fld("Profese","izProf","")+fld("Město","izCity","Plzeň")+fld("Kraj","izReg","Plzeňský kraj")
      +'<div style="margin:6px 0;"><div style="font-size:12px;color:var(--mut);margin-bottom:2px;">Úvazek</div><select id="izEt" style="width:100%;padding:9px;border-radius:9px;border:1px solid var(--bord);background:rgba(255,255,255,.04);color:var(--tx);"><option value="fulltime">Plný úvazek</option><option value="parttime">Částečný</option><option value="contract">IČO</option><option value="brigada">Brigáda</option></select></div>'
      +fld("Plat od (Kč/měs)","izSmin","","number")+fld("Plat do (Kč/měs)","izSmax","","number")
      +'<div style="margin:6px 0;"><div style="font-size:12px;color:var(--mut);margin-bottom:2px;">Popis (HTML — &lt;p&gt; &lt;strong&gt; &lt;ul&gt;&lt;li&gt;)</div><textarea id="izDesc" rows="7" style="width:100%;box-sizing:border-box;padding:9px;border-radius:9px;border:1px solid var(--bord);background:rgba(255,255,255,.04);color:var(--tx);"></textarea></div>'
      +fld("Kontakt – jméno","izCn","Šárka Novotná")+fld("Kontakt – e-mail","izCe","s.novotna@eurosoft.com")
      +'<div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:10px;"><button id="izSave" style="padding:11px 16px;border:0;border-radius:12px;background:linear-gradient(110deg,#34d399,#2dd4bf);color:#04150e;font-weight:700;cursor:pointer;">Uložit</button>'
      +'<button id="izPub" style="padding:11px 16px;border:0;border-radius:12px;background:linear-gradient(110deg,#a78bfa,#7c5cff);color:#0c0820;font-weight:700;cursor:pointer;">📤 Publikovat na Jobs.cz/Práce.cz</button></div><div id="izMsg" class="hint" style="margin-top:8px;"></div>';
    c.innerHTML=h;
    function payload(){ return {id:window._inzId,title:_izV("izTitle"),profession:_izV("izProf"),city:_izV("izCity"),region:_izV("izReg"),employment_type:_izV("izEt"),salary_min:(_izV("izSmin")||null),salary_max:(_izV("izSmax")||null),description_html:_izV("izDesc"),contact_name:_izV("izCn"),contact_email:_izV("izCe")}; }
    if(window._inzId){ api("GET","/api/v1/erp/app/recruit/postings","").then(function(j){ /* prefill minimal: list nemá detail, necháme prázdné pro úpravu */ }); }
    document.getElementById("izSave").addEventListener("click",function(){
      if(!_izV("izTitle")){ document.getElementById("izMsg").textContent="Zadej název pozice."; return; }
      api("POST","/api/v1/erp/app/recruit/posting",payload()).then(function(r){ if(r&&r.ok){ window._inzId=r.id; document.getElementById("izMsg").textContent="Uloženo ✓"; } else document.getElementById("izMsg").textContent="Chyba: "+((r&&r.error)||"?"); });
    });
    document.getElementById("izPub").addEventListener("click",function(){
      if(!window._inzId){ document.getElementById("izMsg").textContent="Nejdřív ulož."; return; }
      api("POST","/api/v1/erp/app/recruit/posting/publish",{id:window._inzId}).then(function(r){ document.getElementById("izMsg").innerHTML=(r&&r.ok)?"✅ Odesláno do Teamia (draft).":("ℹ️ "+esc((r&&r.error)||"?")); });
    });
  }
  function hr_nabor_list(){
    var f=window._nbFilter||{phase:"",title:"Kandidáti"};
    app.innerHTML=topbar(f.title, true);
    var sb=el('<input placeholder="Hledat jméno…" style="width:100%;margin:6px 0;padding:10px;border-radius:10px;border:1px solid var(--bord);background:rgba(255,255,255,.04);color:var(--tx);font-size:15px;box-sizing:border-box;">');
    app.appendChild(sb);
    var box=el('<div class="list"><div class="hint">Načítám…</div></div>');
    app.appendChild(box);
    var all=[];
    function draw(){
      var q=(sb.value||"").trim().toLowerCase(); box.innerHTML=""; var n=0;
      all.forEach(function(it){
        if(q && (it.jmeno||"").toLowerCase().indexOf(q)<0) return;
        n++;
        var st=it.stav==="O"?"otevřeno":(it.stav==="U"?"uzavřeno":it.stav);
        var sub=[it.faze, st, it.pohovor?("pohovor "+it.pohovor):""].filter(Boolean).join(" · ");
        box.appendChild(row("🧑‍💼",it.jmeno,sub||it.pozice||"",function(){ window._nbAppId=it.id; go("hr_nabor_detail"); }));
      });
      if(!n) box.innerHTML='<div class="hint">Nikdo neodpovídá.</div>';
    }
    sb.addEventListener("input",draw);
    api("GET","/api/v1/erp/app/recruit/list?phase="+encodeURIComponent(f.phase||""),"").then(function(j){
      if(!j||!j.ok){ box.innerHTML='<div class="hint">'+((j&&j.error==="forbidden")?"🔒 Jen pro rodiče a HR.":"Nepodařilo se načíst.")+'</div>'; return; }
      all=j.items||[];
      app.insertBefore(el('<div class="hint" style="margin:0 6px 4px;">'+all.length+' záznamů</div>'), box);
      draw();
    });
  }
  function hr_nabor_detail(){
    app.innerHTML=topbar("🧑‍💼 Kandidát", true);
    var box=el('<div style="padding:4px;"><div class="hint">Načítám…</div></div>');
    app.appendChild(box);
    api("GET","/api/v1/erp/app/recruit/detail?id="+encodeURIComponent(window._nbAppId||0),"").then(function(j){
      if(!j||!j.ok){ box.innerHTML='<div class="hint">'+((j&&j.error==="forbidden")?"🔒 Jen pro rodiče a HR.":"Nepodařilo se načíst.")+'</div>'; return; }
      var d=j.d||{};
      function rw(k,v){ return v?('<div style="display:flex;justify-content:space-between;gap:12px;padding:7px 4px;border-bottom:1px solid rgba(255,255,255,.05);font-size:14px;"><span style="color:#9fb2d4;">'+esc(k)+'</span><span style="font-weight:600;text-align:right;">'+esc(String(v))+'</span></div>'):''; }
      box.innerHTML='<div style="font-size:20px;font-weight:800;margin:4px 4px 10px;">'+esc(d.jmeno||"")+'</div>'+
        rw("Fáze",d.faze)+rw("Stav",d.stav==="O"?"otevřeno":(d.stav==="U"?"uzavřeno":d.stav))+rw("Pozice",d.pozice)+
        rw("E-mail",d.email)+rw("Telefon",d.telefon)+rw("Vzdělání",d.vzdelani)+
        rw("Prog. jazyky",d.jazyky_prog)+rw("Cizí jazyky",d.jazyky_ciz)+
        rw("Poslední zaměstnání",d.posl_zam)+rw("Důvod odchodu",d.duvod_odchodu)+
        rw("Vyhláška 50",d.vyhl50?"ano":"")+rw("Požadovaný plat",(d.plat?(Math.round(d.plat).toLocaleString("cs")+" Kč"):""))+
        rw("Termín pohovoru",d.pohovor)+rw("Testovací dny",d.testdny)+rw("Termín nástupu",d.nastup)+
        rw("Zdroj",d.zdroj)+rw("Důvod zamítnutí",d.zamitnuti)+rw("Zadal",d.autor)+
        '<div class="hint" style="margin-top:12px;line-height:1.6;">🔒 Profil v kontextu — citlivá data uchazeče (jen rodiče + HR). Hodnocení z pohovoru se nezobrazuje ani neukládá (rozhodnutí Marti-AI).</div>';
    });
  }
  // Marti 11.6.: self-service osobních údajů — primární zdroj, logovaný,
  // s upozorněním HR na změny. Každý si spravuje svá data sám přes mobil.
  function hr_att_source(){
    app.innerHTML=topbar("🗓️ Zdroj docházky", true);
    app.appendChild(el('<div class="hint" style="margin:8px 6px;line-height:1.6;">„Jen STRATEGIE" = člověk píchá výhradně v naší appce. Vypneme mu píchání ve staré docházce (Centrála) a nebereme odtud jeho záznamy. Kdykoli lze vrátit zpět (kdyby náš systém zlobil).</div>'));
    var box=el('<div class="list"><div class="hint">Načítám…</div></div>'); app.appendChild(box);
    function load(){
      api("GET","/api/v1/erp/app/hr/att-source","").then(function(j){
        box.innerHTML="";
        if(!j||!j.ok){ box.innerHTML='<div class="hint">'+((j&&j.error==="forbidden")?"🔒 Jen rodiče a HR.":"Nepodařilo se načíst.")+'</div>'; return; }
        var items=j.items||[];
        if(!items.length){ box.innerHTML='<div class="hint">Žádní lidé.</div>'; return; }
        items.forEach(function(p){
          var on=!!p.app_only;
          var rw=el('<div style="display:flex;align-items:center;gap:10px;padding:10px 6px;border-bottom:1px solid var(--bord);"></div>');
          rw.appendChild(el('<div style="flex:1;min-width:0;"><div style="font-weight:600;">'+esc(p.jmeno)+'</div><div class="hint">'+(on?("jen STRATEGIE"+(p.ec_blocked?" · Centrála vypnutá":" · ⚠ Centrála nešla vypnout")):"Centrála (stará docházka)")+'</div></div>'));
          var b=el('<button style="padding:8px 12px;border-radius:10px;border:1px solid '+(on?"#34d399":"var(--bord)")+';background:'+(on?"rgba(52,211,153,.15)":"rgba(255,255,255,.04)")+';color:'+(on?"#5ee0b7":"var(--tx)")+';font-weight:700;cursor:pointer;white-space:nowrap;">'+(on?"✓ Jen STRATEGIE":"Přepnout")+'</button>');
          b.addEventListener("click",function(){
            var msg=on?("Vrátit "+p.jmeno+" zpět na starou docházku (Centrála)?"):("Přepnout "+p.jmeno+" na JEN STRATEGIE? Vypne se mu píchání v Centrále.");
            if(!confirm(msg)) return;
            b.disabled=true; b.textContent="…";
            api("POST","/api/v1/erp/app/hr/att-source",{user_id:p.user_id,app_only:!on}).then(function(r){
              if(r&&r.ok){ if(!on && r.ec_blocked===false){ alert("Přepnuto na naší straně, ale Centrálu se nepodařilo vypnout: "+(r.ec_error||"?")); } load(); }
              else { b.disabled=false; b.textContent=on?"✓ Jen STRATEGIE":"Přepnout"; alert("Chyba: "+((r&&r.error)||"?")); }
            });
          });
          rw.appendChild(b); box.appendChild(rw);
        });
      });
    }
    load();
  }

  // ── OČR (ošetřovné) — Fáze 1 (bez ČSSZ API) ─────────────────────────────
  var _OCR_BTN="width:100%;box-sizing:border-box;margin-top:8px;padding:12px;border-radius:12px;border:none;background:var(--green);color:#04150e;font-weight:800;font-size:15px;cursor:pointer;";
  function ocr(){
    app.innerHTML=topbar("🧑‍⚕️ Ošetřovné (OČR) · v2", true);
    // Auth gate (Kristý 29.6.): nepřihlášený host nesmí skončit u prázdného
    // formuláře bez cesty k loginu. whoami → jméno = přihlášen; jinak login karta.
    var _ocrLoad=el('<div class="hint" style="margin:12px 6px;">Ověřuji přihlášení…</div>'); app.appendChild(_ocrLoad);
    var _dev=""; try{ if(B&&typeof B.deviceId==="function") _dev=B.deviceId()||""; }catch(e){}
    api("GET","/api/v1/erp/app/whoami"+(_dev?("?device_id="+encodeURIComponent(_dev)):""),"").then(function(w){
      try{ _ocrLoad.remove(); }catch(e){}
      if(!(w && w.jmeno)){ _ocrLoginGate(); return; }
      _ocrListBody();
    });
  }
  function _ocrLoginGate(){
    var box=el('<div style="padding:14px 8px;"></div>');
    box.appendChild(el('<div style="font-weight:800;font-size:17px;margin-bottom:6px;">🔒 Nejdřív se přihlas</div>'));
    box.appendChild(el('<div class="hint" style="line-height:1.6;margin-bottom:14px;">Pro práci s ošetřovným se přihlas jako zaměstnanec. Tvůj OČR případ se založil přeposláním SMS od ČSSZ — po přihlášení ho tu uvidíš předvyplněný.</div>'));
    var bPwd=el('<button style="'+_OCR_BTN+'">🔑 Přihlásit e-mailem a heslem</button>');
    bPwd.addEventListener("click",function(){ try{ openPasswordLogin(); }catch(e){ location.href="/api/v1/auth/sms-login?next="+encodeURIComponent("/mobile?screen=ocr"); } });
    box.appendChild(bPwd);
    var bPair=el('<button class="ghost full" style="margin-top:8px;">🔗 Přihlásit odkazem (SMS)</button>');
    bPair.addEventListener("click",function(){ location.href="/api/v1/auth/sms-login?next="+encodeURIComponent("/mobile?screen=ocr"); });
    box.appendChild(bPair);
    app.appendChild(box);
  }
  function _ocrListBody(){
    app.appendChild(el('<div class="hint" style="margin:8px 6px;line-height:1.6;">Když ti přijde SMS od ČSSZ s identifikátorem ošetřování, založ tu OČR. Po skončení doplníš datum do a počet dní — vedoucí/HR to schválí. (Brzy se dokumenty z ČSSZ potáhnou samy.)</div>'));
    var nb=el('<button style="'+_OCR_BTN+'">➕ Nové ošetřovné</button>'); nb.addEventListener("click",function(){ ocrForm(); }); app.appendChild(nb);
    var box=el('<div class="list" style="margin-top:10px;"><div class="hint">Načítám…</div></div>'); app.appendChild(box);
    api("GET","/api/v1/erp/app/ocr/mine","").then(function(j){
      box.innerHTML="";
      if(!j||!j.ok){ box.innerHTML='<div class="hint">Nepodařilo se načíst.</div>'; return; }
      var cs=j.cases||[];
      if(!cs.length){ box.innerHTML='<div class="hint">Zatím žádné OČR.</div>'; return; }
      cs.forEach(function(c){
        var lbl={novy:"probíhá",ukonceno:"ke schválení",schvaleno:"schváleno"}[c.stav]||c.stav;
        var rw=el('<div style="padding:10px 6px;border-bottom:1px solid var(--bord);cursor:pointer;"></div>');
        rw.appendChild(el('<div style="font-weight:600;display:flex;justify-content:space-between;align-items:center;gap:8px;"><span>'+esc(c.osoba||"")+(c.vztah?(' · '+esc(c.vztah)):'')+'</span><span style="color:#9fd0ff;font-size:20px;line-height:1;">›</span></div>'));
        rw.appendChild(el('<div class="hint">'+_czDate(c.od)+(c.do?(' – '+_czDate(c.do)):'')+(c.dny?(' · '+c.dny+' dní'):'')+' · '+esc(lbl)+(c.company?(' · '+esc(c.company)):'')+'</div>'));
        rw.addEventListener("click",function(){ ocrVyplnit(c.id); });
        var fb=el('<button style="margin-top:6px;margin-right:6px;padding:8px 12px;border-radius:10px;border:1px solid #2b3a5c;background:rgba(159,208,255,.08);color:#9fd0ff;font-weight:700;cursor:pointer;">📋 Vyplnit formulář</button>');
        fb.addEventListener("click",function(e){ try{e.stopPropagation();}catch(_){} ocrVyplnit(c.id); }); rw.appendChild(fb);
        if(c.stav==="novy"){
          var eb=el('<button style="margin-top:6px;padding:8px 12px;border-radius:10px;border:1px solid var(--bord);background:rgba(255,255,255,.04);color:var(--tx);font-weight:700;cursor:pointer;">Ukončit a poslat ke schválení</button>');
          eb.addEventListener("click",function(e){ try{e.stopPropagation();}catch(_){} ocrEndForm(c); }); rw.appendChild(eb);
        }
        box.appendChild(rw);
      });
    });
  }
  function _ocrFld(parent,label,ph,hintTxt){
    var wr=el('<div></div>'); wr.appendChild(el('<div style="font-size:13px;color:#cdd6e2;margin-bottom:4px;">'+esc(label)+'</div>'));
    var i=el('<input type="text" placeholder="'+esc(ph||"")+'" style="width:100%;box-sizing:border-box;padding:10px;border-radius:10px;border:1px solid #2b3a5c;background:#0a1226;color:#e8eefc;">');
    wr.appendChild(i); if(hintTxt) wr.appendChild(el('<div class="hint" style="margin-top:3px;">'+esc(hintTxt)+'</div>')); parent.appendChild(wr); return i;
  }
  function ocrForm(){
    app.innerHTML=topbar("➕ Nové ošetřovné", true);
    var w=el('<div style="padding:6px;display:flex;flex-direction:column;gap:12px;"></div>'); app.appendChild(w);
    var fId=_ocrFld(w,"Identifikátor ČSSZ (ze SMS)","např. 10251643250619001N","Najdeš ve zprávě od ČSSZ s odkazem na eportal.cssz.cz.");
    var fOs=_ocrFld(w,"Ošetřovaná osoba (jméno)","Jméno a příjmení");
    var fRc=_ocrFld(w,"Rodné číslo ošetřované osoby","RRMMDD/XXXX");
    var fVz=_ocrFld(w,"Vztah","dítě / rodič / …");
    var fOd=_ocrFld(w,"Datum od","DD.MM.RRRR");
    var st=el('<div class="hint" style="min-height:16px;"></div>'); w.appendChild(st);
    var sv=el('<button style="'+_OCR_BTN+'">Založit OČR</button>'); w.appendChild(sv);
    var cx=el('<button class="ghost sm" style="margin-top:4px;">Zrušit</button>'); cx.addEventListener("click",function(){ ocr(); }); w.appendChild(cx);
    sv.addEventListener("click",function(){
      var osoba=(fOs.value||"").trim(); if(!osoba){ st.style.color="#ff8b8b"; st.textContent="Vyplň ošetřovanou osobu."; return; }
      var od=_isoDate(fOd.value); if(!/^\d{4}-\d{2}-\d{2}/.test(od)){ st.style.color="#ff8b8b"; st.textContent="Datum od ve formátu DD.MM.RRRR."; return; }
      var rc=(fRc.value||"").trim(); if(rc && !_rcValid(rc)){ st.style.color="#ff8b8b"; st.textContent="RČ nevypadá platně."; return; }
      sv.disabled=true; st.style.color="#9fb2d4"; st.textContent="Ukládám…";
      api("POST","/api/v1/erp/app/ocr/start",{identifikator:(fId.value||"").trim(),osoba_jmeno:osoba,osoba_rc:rc,osoba_vztah:(fVz.value||"").trim(),od:od}).then(function(r){
        if(r&&r.ok){ ocr(); } else { sv.disabled=false; st.style.color="#ff8b8b"; st.textContent="Chyba: "+((r&&r.error)||"?"); }
      });
    });
  }
  function ocrEndForm(c){
    app.innerHTML=topbar("Ukončit OČR", true);
    var w=el('<div style="padding:6px;display:flex;flex-direction:column;gap:12px;"></div>'); app.appendChild(w);
    w.appendChild(el('<div class="hint" style="line-height:1.6;">Péče o: <b>'+esc(c.osoba||"")+'</b>, od '+_czDate(c.od)+'. Doplň datum konce a počet dní, kdy ses staral(a).</div>'));
    var fDo=_ocrFld(w,"Datum do","DD.MM.RRRR");
    var fDny=_ocrFld(w,"Počet dní ošetřování","např. 6");
    var st=el('<div class="hint" style="min-height:16px;"></div>'); w.appendChild(st);
    var sv=el('<button style="'+_OCR_BTN+'">Poslat ke schválení</button>'); w.appendChild(sv);
    var cx=el('<button class="ghost sm" style="margin-top:4px;">Zrušit</button>'); cx.addEventListener("click",function(){ ocr(); }); w.appendChild(cx);
    sv.addEventListener("click",function(){
      var dd=_isoDate(fDo.value); if(!/^\d{4}-\d{2}-\d{2}/.test(dd)){ st.style.color="#ff8b8b"; st.textContent="Datum do ve formátu DD.MM.RRRR."; return; }
      var dny=parseInt((fDny.value||"0").replace(/\D/g,""),10)||0;
      sv.disabled=true; st.style.color="#9fb2d4"; st.textContent="Odesílám…";
      api("POST","/api/v1/erp/app/ocr/end",{id:c.id,"do":dd,dny:dny}).then(function(r){
        if(r&&r.ok){ ocr(); } else { sv.disabled=false; st.style.color="#ff8b8b"; st.textContent="Chyba: "+((r&&r.error)||"?"); }
      });
    });
  }
  // ── OČR formulář (ČSSZ §109) — předvyplněný, ukládá do att_ocr_form ──────
  function _ocrSec(title){ return el('<div style="margin-top:14px;font-weight:800;color:#9fd0ff;border-bottom:1px solid #24324f;padding-bottom:4px;">'+esc(title)+'</div>'); }
  function _ocrArea(parent,label,ph,val){
    var wr=el('<div></div>'); wr.appendChild(el('<div style="font-size:13px;color:#cdd6e2;margin-bottom:4px;">'+esc(label)+'</div>'));
    var t=el('<textarea rows="3" placeholder="'+esc(ph||"")+'" style="width:100%;box-sizing:border-box;padding:10px;border-radius:10px;border:1px solid #2b3a5c;background:#0a1226;color:#e8eefc;"></textarea>');
    t.value=val||""; wr.appendChild(t); parent.appendChild(wr); return t;
  }
  function _ocrRadio(parent,label,opts,val){
    var grp="ocrR"+Math.floor(Math.random()*1e9);  // společný name → vzájemně se vylučují
    var wr=el('<div></div>'); wr.appendChild(el('<div style="font-size:13px;color:#cdd6e2;margin-bottom:4px;">'+esc(label)+'</div>'));
    var box=el('<div style="display:flex;flex-direction:column;gap:4px;"></div>'); var cur={v:val};
    opts.forEach(function(o){
      var row=el('<label style="display:flex;align-items:center;gap:8px;font-size:14px;color:#e8eefc;cursor:pointer;"></label>');
      var r=el('<input type="radio" name="'+grp+'" style="accent-color:#34d399;width:16px;height:16px;">'); if(o.v===val)r.checked=true;
      r.addEventListener("change",function(){ cur.v=o.v; });
      row.appendChild(r); row.appendChild(el('<span>'+esc(o.t)+'</span>')); box.appendChild(row);
    });
    wr.appendChild(box); parent.appendChild(wr); return { get:function(){ return cur.v; } };
  }
  function _ocrYesNo(parent,label,val){ return _ocrRadio(parent,label,[{v:"ano",t:"Ano"},{v:"ne",t:"Ne"}],(val==="ano"?"ano":"ne")); }
  function _apiForm(path, fd){
    return fetch(path,{method:"POST",credentials:"same-origin",body:fd}).then(function(r){ return r.text(); }).then(function(t){ try{ return t?JSON.parse(t):null; }catch(e){ return null; } }).catch(function(){ return null; });
  }
  function _rcToBirth(rc){
    rc=(rc||"").replace(/[\s\/]/g,""); if(!/^\d{9,10}$/.test(rc)) return "";
    var yy=parseInt(rc.slice(0,2),10), mm=parseInt(rc.slice(2,4),10), dd=parseInt(rc.slice(4,6),10);
    if(mm>70)mm-=70; else if(mm>50)mm-=50; else if(mm>20)mm-=20;
    var full=(rc.length===10)?((yy<54?2000:1900)+yy):(1900+yy);
    if(full>(new Date().getFullYear()))full-=100;
    if(mm<1||mm>12||dd<1||dd>31)return "";
    return full+"-"+("0"+mm).slice(-2)+"-"+("0"+dd).slice(-2);
  }
  function _ocrLoadFiles(box, caseId, canDel){
    box.innerHTML='<div class="hint">Načítám přílohy…</div>';
    api("GET","/api/v1/erp/app/ocr/files?case="+caseId,"").then(function(j){
      box.innerHTML="";
      if(!j||!j.ok){ box.appendChild(el('<div class="hint">Přílohy se nepodařilo načíst.</div>')); return; }
      var fs=j.files||[];
      if(!fs.length){ box.appendChild(el('<div class="hint">Zatím žádné přílohy.</div>')); return; }
      fs.forEach(function(f){
        var r=el('<div style="display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid #1c2740;"></div>');
        var icon=(f.kind==="excel")?"📊":"📄";
        r.appendChild(el('<div style="flex:1;font-size:14px;"><a href="/api/v1/erp/app/ocr/file-view?fid='+f.id+'" target="_blank" rel="noopener" style="color:#9fd0ff;text-decoration:none;">'+icon+' '+esc(f.filename||("dokument "+f.document_id))+'</a> <span class="hint">'+esc(f.created||"")+'</span></div>'));
        if(canDel){
          var x=el('<button style="background:#3a1d28;border:0;color:#f9b;border-radius:8px;padding:5px 9px;cursor:pointer;">🗑</button>');
          x.addEventListener("click",function(){ if(!confirm("Smazat přílohu?"))return; api("POST","/api/v1/erp/app/ocr/file/delete",{id:f.id}).then(function(rr){ if(rr&&rr.ok)_ocrLoadFiles(box,caseId,canDel); else alert("Chyba: "+((rr&&rr.error)||"?")); }); });
          r.appendChild(x);
        }
        box.appendChild(r);
      });
    });
  }
  function ocrVyplnit(caseId){
    app.innerHTML=topbar("📋 Formulář ošetřovného", true);
    var w=el('<div style="padding:6px;display:flex;flex-direction:column;gap:10px;"></div>'); app.appendChild(w);
    w.appendChild(el('<div class="hint">Načítám…</div>'));
    api("GET","/api/v1/erp/app/ocr/form?case="+caseId,"").then(function(j){
      w.innerHTML="";
      if(!j||!j.ok){ w.appendChild(el('<div class="hint">'+esc((j&&j.error)||"Nepodařilo se načíst.")+'</div>')); var bk=el('<button class="ghost sm">Zpět</button>'); bk.addEventListener("click",function(){ocr();}); w.appendChild(bk); return; }
      var d=j.data||{}; var canMng=!!j.can_manage;
      w.appendChild(el('<div class="hint" style="line-height:1.6;">Formulář ČSSZ „Oznámení zaměstnavateli o potřebě ošetřování" (§109). Předvyplnili jsme, co víme — doplň zbytek a ulož. Rodné číslo jde jen do formuláře, nikdy ne SMS.</div>'));
      function _ocrLinkBtn(url,label){ return el('<div style="margin:2px 0 4px;padding:8px 10px;border-radius:10px;background:rgba(159,208,255,.08);border:1px solid #2b3a5c;"><a href="'+esc(url)+'" target="_blank" rel="noopener" style="color:#9fd0ff;font-weight:700;font-size:14px;text-decoration:none;">'+esc(label)+'</a></div>'); }
      var _ocrLnk=j.cssz_link||j.cssz_link_konec; if(_ocrLnk){ w.appendChild(_ocrLinkBtn(_ocrLnk,"📄 Stáhnout doklad z ČSSZ ePortálu")); }
      w.appendChild(_ocrSec("Zaměstnanec"));
      var fZj=_ocrFld(w,"Jméno",""); fZj.value=d.zam_jmeno||"";
      var fZp=_ocrFld(w,"Příjmení",""); fZp.value=d.zam_prijmeni||"";
      var fZr=_ocrFld(w,"Rodné číslo zaměstnance","RRMMDD/XXXX"); fZr.value=d.zam_rc||"";
      w.appendChild(_ocrSec("Ošetřovaná osoba"));
      var fOj=_ocrFld(w,"Jméno a příjmení",""); fOj.value=d.os_jmeno||"";
      var fOr=_ocrFld(w,"Rodné číslo ošetřované osoby","RRMMDD/XXXX"); fOr.value=d.os_rc||"";
      var fOv=_ocrFld(w,"Vztah k zaměstnanci","dítě / rodič / manžel…"); fOv.value=d.os_vztah||"";
      var sc=el('<button class="ghost sm" style="margin-top:2px;">👨‍👩‍👧 Uložit dítě do karty</button>');
      sc.addEventListener("click",function(){
        var nm=(fOj.value||"").trim(), rc=(fOr.value||"").trim(), rel=(fOv.value||"").trim();
        if(!nm){ alert("Vyplň jméno ošetřované osoby."); return; }
        if(rc && !_rcValid(rc)){ alert("RČ nevypadá platně."); return; }
        sc.disabled=true; sc.textContent="Ukládám…";
        api("POST","/api/v1/erp/app/self-child/save",{child_name:nm,birth_number:rc,relation:rel||"dítě",birth_date:_rcToBirth(rc)}).then(function(r){
          sc.disabled=false;
          if(r&&r.ok){ sc.textContent="✓ Uloženo do karty"; } else { sc.textContent="👨‍👩‍👧 Uložit dítě do karty"; alert("Chyba: "+((r&&r.error)||"?")); }
        });
      }); w.appendChild(sc);
      w.appendChild(_ocrSec("Rozhodnutí a období"));
      var fCr=_ocrFld(w,"Číslo rozhodnutí / identifikátor ČSSZ",""); fCr.value=d.cislo_rozhodnuti||"";
      var fDod=_ocrFld(w,"Datum od","DD.MM.RRRR"); fDod.value=_czDate(d.datum_od)||"";
      var fDdo=_ocrFld(w,"Datum do","DD.MM.RRRR"); fDdo.value=_czDate(d.datum_do)||"";
      var duvod=_ocrRadio(w,"Důvod ošetřování",[
        {v:"osetrovani_nemocne",t:"Ošetřování nemocného člena domácnosti"},
        {v:"karantena_dite",t:"Dítě v karanténě / izolaci"},
        {v:"zarizeni_uzavreno",t:"Uzavření školy / dětského zařízení"},
        {v:"osoba_onemocnela",t:"Onemocněla osoba, která jinak o dítě pečuje"}
      ], d.duvod||"osetrovani_nemocne");
      w.appendChild(_ocrSec("Podmínky nároku"));
      var spol=_ocrYesNo(w,"Žije ošetřovaná osoba s vámi ve společné domácnosti?", d.spolecna_domacnost||"ano");
      var osam=_ocrYesNo(w,"Jste osamělý/á zaměstnanec/kyně?", d.osamely_zamestnanec||"ne");
      var jina=_ocrYesNo(w,"Je v domácnosti jiná osoba, která může pečovat (pobírá PPM / rodičovský příspěvek)?", d.jina_osoba_ppm||"ne");
      var jinaNem=_ocrYesNo(w,"…a tato osoba onemocněla / nemůže pečovat?", d.jina_osoba_onemocnela||"ne");
      var ppm=_ocrYesNo(w,"Pobíráte vy peněžitou pomoc v mateřství (PPM)?", d.pobira_ppm||"ne");
      w.appendChild(_ocrSec("Žádost a poskytování péče"));
      var obd=_ocrRadio(w,"Žádám o ošetřovné za",[
        {v:"cela_doba",t:"Celou dobu ošetřování"},
        {v:"v_dnech",t:"Jen vybrané dny (od–do)"}
      ], d.obdobi_zadosti||"cela_doba");
      var fObOd=_ocrFld(w,"— období od (jen u vybraných dnů)","DD.MM.RRRR"); fObOd.value=_czDate(d.obdobi_od)||"";
      var fObDo=_ocrFld(w,"— období do","DD.MM.RRRR"); fObDo.value=_czDate(d.obdobi_do)||"";
      var posk=_ocrRadio(w,"Ošetřování jsem poskytoval(a)",[
        {v:"cela_doba",t:"Po celou dobu"},
        {v:"v_dnech",t:"Jen ve vybrané dny (od–do)"}
      ], d.osetrovani_poskytl||"cela_doba");
      var fPoOd=_ocrFld(w,"— poskytl od","DD.MM.RRRR"); fPoOd.value=_czDate(d.poskytl_od)||"";
      var fPoDo=_ocrFld(w,"— poskytl do","DD.MM.RRRR"); fPoDo.value=_czDate(d.poskytl_do)||"";
      w.appendChild(_ocrSec("Doplňující"));
      var area=_ocrArea(w,"Sdělení zaměstnance (nepovinné)","Cokoli pro účetní / úřad…", d.sdeleni||"");
      var fKont=_ocrFld(w,"Kontakt — telefon / e-mail (nepovinné)",""); fKont.value=d.kontakt||"";
      w.appendChild(_ocrSec("Přílohy (PDF / sken z ČSSZ)"));
      var filesBox=el('<div></div>'); w.appendChild(filesBox); _ocrLoadFiles(filesBox, caseId, canMng);
      var upBtn=el('<button class="ghost sm" style="margin-top:6px;">⬆️ Nahrát přílohu (PDF / foto)</button>');
      upBtn.addEventListener("click",function(){
        var fi=el('<input type="file" accept="application/pdf,image/*" style="display:none;">'); document.body.appendChild(fi);
        fi.addEventListener("change",function(){
          var f=fi.files&&fi.files[0]; if(!f){ try{fi.remove();}catch(e){} return; }
          if(f.size>25*1024*1024){ alert("Soubor je moc velký (max 25 MB)."); try{fi.remove();}catch(e){} return; }
          var fr=new FileReader();
          fr.onload=function(){
            var b64=String(fr.result).split(",")[1]||"";
            var fn=f.name||"priloha.pdf";
            upBtn.disabled=true; upBtn.textContent="Nahrávám…";
            api("POST","/api/v1/erp/app/ocr/file",{case:caseId,kind:"priloha",filename:fn,file_b64:b64}).then(function(r){
              upBtn.disabled=false; upBtn.textContent="⬆️ Nahrát přílohu (PDF / foto)";
              try{fi.remove();}catch(e){}
              _ocrLoadFiles(filesBox, caseId, canMng);
              if(!(r&&r.ok)){ alert("Chyba: "+((r&&r.error)||"nahrání selhalo")); }
            });
          };
          fr.readAsDataURL(f);
        });
        fi.click();
      }); if(canMng) w.appendChild(upBtn);
      var st=el('<div class="hint" style="min-height:16px;margin-top:8px;"></div>'); w.appendChild(st);
      function collect(){
        return {
          zam_jmeno:(fZj.value||"").trim(), zam_prijmeni:(fZp.value||"").trim(), zam_rc:(fZr.value||"").trim(),
          os_jmeno:(fOj.value||"").trim(), os_rc:(fOr.value||"").trim(), os_vztah:(fOv.value||"").trim(),
          cislo_rozhodnuti:(fCr.value||"").trim(), datum_od:_isoDate(fDod.value), datum_do:_isoDate(fDdo.value),
          duvod:duvod.get(), spolecna_domacnost:spol.get(), osamely_zamestnanec:osam.get(),
          jina_osoba_ppm:jina.get(), jina_osoba_onemocnela:jinaNem.get(), pobira_ppm:ppm.get(),
          obdobi_zadosti:obd.get(), obdobi_od:_isoDate(fObOd.value), obdobi_do:_isoDate(fObDo.value),
          osetrovani_poskytl:posk.get(), poskytl_od:_isoDate(fPoOd.value), poskytl_do:_isoDate(fPoDo.value),
          sdeleni:(area.value||"").trim(), kontakt:(fKont.value||"").trim()
        };
      }
      function doSave(stav){
        if(fOr.value && !_rcValid(fOr.value)){ st.style.color="#ff8b8b"; st.textContent="RČ ošetřované osoby nevypadá platně."; return; }
        st.style.color="#9fb2d4"; st.textContent="Ukládám…";
        api("POST","/api/v1/erp/app/ocr/form/save",{case:caseId,data:collect(),stav:stav}).then(function(r){
          if(r&&r.ok){ st.style.color="#5ee0b7"; st.textContent=(stav==="kompletni"?"✓ Uloženo jako kompletní":"✓ Uloženo"); }
          else { st.style.color="#ff8b8b"; st.textContent="Chyba: "+((r&&r.error)||"?"); }
        });
      }
      var sv=el('<button style="'+_OCR_BTN+'">💾 Uložit formulář</button>'); sv.addEventListener("click",function(){ doSave("rozpracovany"); }); w.appendChild(sv);
      var done=el('<button style="margin-top:6px;padding:11px;border-radius:12px;border:1px solid #34d399;background:rgba(52,211,153,.15);color:#5ee0b7;font-weight:800;width:100%;cursor:pointer;">✓ Označit jako kompletní</button>'); done.addEventListener("click",function(){ doSave("kompletni"); }); if(canMng) w.appendChild(done);
      var gx=el('<button style="margin-top:6px;padding:11px;border-radius:12px;border:1px solid #6aa9ff;background:rgba(106,169,255,.12);color:#9fd0ff;font-weight:800;width:100%;cursor:pointer;">📊 Vygenerovat ČSSZ Excel</button>');
      gx.addEventListener("click",function(){
        if(fOr.value && !_rcValid(fOr.value)){ st.style.color="#ff8b8b"; st.textContent="RČ ošetřované osoby nevypadá platně."; return; }
        gx.disabled=true; st.style.color="#9fb2d4"; st.textContent="Ukládám a generuji Excel…";
        api("POST","/api/v1/erp/app/ocr/form/save",{case:caseId,data:collect(),stav:"kompletni"}).then(function(r){
          if(!r||!r.ok){ gx.disabled=false; st.style.color="#ff8b8b"; st.textContent="Uložení selhalo: "+((r&&r.error)||"?"); return; }
          api("POST","/api/v1/erp/app/ocr/excel",{case:caseId}).then(function(e){
            gx.disabled=false;
            _ocrLoadFiles(filesBox, caseId, canMng);
            if(e&&e.ok){ st.style.color="#5ee0b7"; st.textContent="✓ Excel vygenerován: "+esc(e.filename||""); }
            else { st.style.color="#ff8b8b"; st.textContent="Generování selhalo: "+((e&&e.error)||"?"); }
          });
        });
      }); if(canMng) w.appendChild(gx);
      var mb=el('<button style="margin-top:6px;padding:11px;border-radius:12px;border:1px solid #f0b35e;background:rgba(240,179,94,.12);color:#f6c98a;font-weight:800;width:100%;cursor:pointer;">📧 Odeslat účetní</button>');
      mb.addEventListener("click",function(){
        if(!confirm("Odeslat formulář a přílohy e-mailem účetní (Petra Fajmonová, fajmonova@martia2000.cz), kopie Péťa (p.safrankova@eurosoft.com)?\n\nExcel se před odesláním vygeneruje z aktuálních dat."))return;
        mb.disabled=true; st.style.color="#9fb2d4"; st.textContent="Ukládám, generuji a odesílám…";
        api("POST","/api/v1/erp/app/ocr/form/save",{case:caseId,data:collect(),stav:"kompletni"}).then(function(r){
          if(!r||!r.ok){ mb.disabled=false; st.style.color="#ff8b8b"; st.textContent="Uložení selhalo: "+((r&&r.error)||"?"); return; }
          api("POST","/api/v1/erp/app/ocr/excel",{case:caseId}).then(function(e){
            if(!e||!e.ok){ mb.disabled=false; st.style.color="#ff8b8b"; st.textContent="Excel selhal: "+((e&&e.error)||"?"); return; }
            api("POST","/api/v1/erp/app/ocr/mail",{case:caseId}).then(function(m){
              mb.disabled=false;
              if(m&&m.ok){ st.style.color="#5ee0b7"; st.textContent="✓ Odesláno účetní ("+(m.attachments||0)+" příloh), kopie Péťa."; _ocrLoadFiles(filesBox, caseId, canMng); }
              else if(m&&m.error==="forbidden"){ st.style.color="#ff8b8b"; st.textContent="Odeslání může spustit jen HR/účetní."; }
              else { st.style.color="#ff8b8b"; st.textContent="Odeslání selhalo: "+((m&&m.error)||"?"); }
            });
          });
        });
      }); if(canMng) w.appendChild(mb);
      var cx=el('<button class="ghost sm" style="margin-top:4px;">Zpět na seznam OČR</button>'); cx.addEventListener("click",function(){ ocr(); }); w.appendChild(cx);
    });
  }
  function ocr_schval(){
    app.innerHTML=topbar("🧑‍⚕️ OČR — schvalování", true);
    var box=el('<div class="list"><div class="hint">Načítám…</div></div>'); app.appendChild(box);
    api("GET","/api/v1/erp/app/ocr/inbox","").then(function(j){
      box.innerHTML="";
      if(!j||!j.ok){ box.innerHTML='<div class="hint">'+((j&&j.error==="forbidden")?"🔒 Jen rodiče a HR.":"Nepodařilo se načíst.")+'</div>'; return; }
      var cs=j.cases||[];
      if(!cs.length){ box.innerHTML='<div class="hint">Nic ke schválení.</div>'; return; }
      cs.forEach(function(c){
        var rw=el('<div style="padding:10px 6px;border-bottom:1px solid var(--bord);"></div>');
        rw.appendChild(el('<div style="font-weight:600;">'+esc(c.zamestnanec||"")+'</div>'));
        rw.appendChild(el('<div class="hint">péče o: '+esc(c.osoba||"")+(c.vztah?(' ('+esc(c.vztah)+')'):'')+' · '+_czDate(c.od)+(c.do?(' – '+_czDate(c.do)):'')+(c.dny?(' · '+c.dny+' dní'):'')+(c.company?(' · '+esc(c.company)):'')+(c.identifikator?(' · id '+esc(c.identifikator)):'')+'</div>'));
        var _cl=c.link||c.link_konec; if(_cl){ rw.appendChild(el('<div style="margin-top:4px;"><a href="'+esc(_cl)+'" target="_blank" rel="noopener" style="color:#9fd0ff;font-size:13px;font-weight:600;">📄 Stáhnout doklad z ČSSZ ePortálu</a></div>')); }
        if(c.stav==="ukonceno"){
          var b=el('<button style="margin-top:6px;padding:8px 14px;border-radius:10px;border:1px solid #34d399;background:rgba(52,211,153,.15);color:#5ee0b7;font-weight:700;cursor:pointer;">✓ Schválit</button>');
          b.addEventListener("click",function(){ if(!confirm("Schválit OČR pro "+(c.zamestnanec||"")+"?"))return; b.disabled=true; b.textContent="…"; api("POST","/api/v1/erp/app/ocr/approve",{id:c.id}).then(function(r){ if(r&&r.ok){ ocr_schval(); } else { b.disabled=false; b.textContent="✓ Schválit"; alert("Chyba: "+((r&&r.error)||"?")); } }); });
          rw.appendChild(b);
        } else { rw.appendChild(el('<div class="hint" style="margin-top:4px;">probíhá (čeká na ukončení zaměstnancem)</div>')); }
        box.appendChild(rw);
      });
    });
  }
  // ── eNeschopenka (nemocenská) — Fáze 1 (mirror OČR) ────────────────────
  function sick(){
    app.innerHTML=topbar("🤒 Nemocenská", true);
    app.appendChild(el('<div class="hint" style="margin:8px 6px;line-height:1.6;">Nahlas nemoc (eNeschopenku). Pokud máš číslo rozhodnutí o DPN, zadej ho — jinak stačí datum od. Po uzdravení doplníš konec, vedoucí/HR schválí. (Brzy budeme údaje z ČSSZ tahat automaticky.)</div>'));
    var nb=el('<button style="'+_OCR_BTN+'">➕ Nahlásit nemoc</button>'); nb.addEventListener("click",function(){ sickForm(); }); app.appendChild(nb);
    var box=el('<div class="list" style="margin-top:10px;"><div class="hint">Načítám…</div></div>'); app.appendChild(box);
    api("GET","/api/v1/erp/app/sick/mine","").then(function(j){
      box.innerHTML="";
      if(!j||!j.ok){ box.innerHTML='<div class="hint">Nepodařilo se načíst.</div>'; return; }
      var cs=j.cases||[];
      if(!cs.length){ box.innerHTML='<div class="hint">Zatím žádná nemocenská.</div>'; return; }
      cs.forEach(function(c){
        var lbl={novy:"probíhá",trva:"probíhá",ukonceno:"ke schválení",schvaleno:"schváleno"}[c.stav]||c.stav;
        var konec=c.do?(" – "+_czDate(c.do)):(c.predpoklad_do?(" – předpoklad "+_czDate(c.predpoklad_do)):"");
        var rw=el('<div style="padding:10px 6px;border-bottom:1px solid var(--bord);"></div>');
        rw.appendChild(el('<div style="font-weight:600;">Nemocenská'+(c.cislo_dpn?(' · DPN '+esc(c.cislo_dpn)):'')+'</div>'));
        rw.appendChild(el('<div class="hint">'+_czDate(c.od)+konec+' · '+esc(lbl)+(c.company?(' · '+esc(c.company)):'')+'</div>'));
        if(c.stav==="novy"||c.stav==="trva"){
          var eb=el('<button style="margin-top:6px;padding:8px 12px;border-radius:10px;border:1px solid var(--bord);background:rgba(255,255,255,.04);color:var(--tx);font-weight:700;cursor:pointer;">Ukončit a poslat ke schválení</button>');
          eb.addEventListener("click",function(){ sickEndForm(c); }); rw.appendChild(eb);
        }
        box.appendChild(rw);
      });
    });
  }
  function sickForm(){
    app.innerHTML=topbar("➕ Nahlásit nemoc", true);
    var w=el('<div style="padding:6px;display:flex;flex-direction:column;gap:12px;"></div>'); app.appendChild(w);
    var fC=_ocrFld(w,"Číslo rozhodnutí o DPN (pokud máš)","nepovinné","Z eNeschopenky / od ČSSZ. Nemáš-li, nech prázdné.");
    var fOd=_ocrFld(w,"Nemocný od","DD.MM.RRRR");
    var fPd=_ocrFld(w,"Předpokládaný konec (pokud víš)","DD.MM.RRRR — nepovinné");
    var st=el('<div class="hint" style="min-height:16px;"></div>'); w.appendChild(st);
    var sv=el('<button style="'+_OCR_BTN+'">Nahlásit</button>'); w.appendChild(sv);
    var cx=el('<button class="ghost sm" style="margin-top:4px;">Zrušit</button>'); cx.addEventListener("click",function(){ sick(); }); w.appendChild(cx);
    sv.addEventListener("click",function(){
      var od=_isoDate(fOd.value); if(!/^\d{4}-\d{2}-\d{2}/.test(od)){ st.style.color="#ff8b8b"; st.textContent="Datum od ve formátu DD.MM.RRRR."; return; }
      var pd=(fPd.value||"").trim()?_isoDate(fPd.value):""; if(pd && !/^\d{4}-\d{2}-\d{2}/.test(pd)){ st.style.color="#ff8b8b"; st.textContent="Předpokládaný konec ve formátu DD.MM.RRRR."; return; }
      sv.disabled=true; st.style.color="#9fb2d4"; st.textContent="Odesílám…";
      api("POST","/api/v1/erp/app/sick/start",{cislo_dpn:(fC.value||"").trim(),od:od,predpoklad_do:pd}).then(function(r){
        if(r&&r.ok){ sick(); } else { sv.disabled=false; st.style.color="#ff8b8b"; st.textContent="Chyba: "+((r&&r.error)||"?"); }
      });
    });
  }
  function sickEndForm(c){
    app.innerHTML=topbar("Ukončit nemocenskou", true);
    var w=el('<div style="padding:6px;display:flex;flex-direction:column;gap:12px;"></div>'); app.appendChild(w);
    w.appendChild(el('<div class="hint" style="line-height:1.6;">Nemocný od '+_czDate(c.od)+'. Doplň datum konce nemocenské.</div>'));
    var fDo=_ocrFld(w,"Datum do","DD.MM.RRRR");
    var st=el('<div class="hint" style="min-height:16px;"></div>'); w.appendChild(st);
    var sv=el('<button style="'+_OCR_BTN+'">Poslat ke schválení</button>'); w.appendChild(sv);
    var cx=el('<button class="ghost sm" style="margin-top:4px;">Zrušit</button>'); cx.addEventListener("click",function(){ sick(); }); w.appendChild(cx);
    sv.addEventListener("click",function(){
      var dd=_isoDate(fDo.value); if(!/^\d{4}-\d{2}-\d{2}/.test(dd)){ st.style.color="#ff8b8b"; st.textContent="Datum do ve formátu DD.MM.RRRR."; return; }
      sv.disabled=true; st.style.color="#9fb2d4"; st.textContent="Odesílám…";
      api("POST","/api/v1/erp/app/sick/end",{id:c.id,"do":dd}).then(function(r){
        if(r&&r.ok){ sick(); } else { sv.disabled=false; st.style.color="#ff8b8b"; st.textContent="Chyba: "+((r&&r.error)||"?"); }
      });
    });
  }
  function sick_schval(){
    app.innerHTML=topbar("🤒 Nemocenská — schvalování", true);
    var box=el('<div class="list"><div class="hint">Načítám…</div></div>'); app.appendChild(box);
    api("GET","/api/v1/erp/app/sick/inbox","").then(function(j){
      box.innerHTML="";
      if(!j||!j.ok){ box.innerHTML='<div class="hint">'+((j&&j.error==="forbidden")?"🔒 Jen rodiče a HR.":"Nepodařilo se načíst.")+'</div>'; return; }
      var cs=j.cases||[];
      if(!cs.length){ box.innerHTML='<div class="hint">Nic ke schválení.</div>'; return; }
      cs.forEach(function(c){
        var rw=el('<div style="padding:10px 6px;border-bottom:1px solid var(--bord);"></div>');
        rw.appendChild(el('<div style="font-weight:600;">'+esc(c.zamestnanec||"")+'</div>'));
        var konec=c.do?(" – "+_czDate(c.do)):(c.predpoklad_do?(" – předpoklad "+_czDate(c.predpoklad_do)):"");
        rw.appendChild(el('<div class="hint">nemoc '+_czDate(c.od)+konec+(c.company?(' · '+esc(c.company)):'')+(c.cislo_dpn?(' · DPN '+esc(c.cislo_dpn)):'')+'</div>'));
        if(c.stav==="ukonceno"){
          var b=el('<button style="margin-top:6px;padding:8px 14px;border-radius:10px;border:1px solid #34d399;background:rgba(52,211,153,.15);color:#5ee0b7;font-weight:700;cursor:pointer;">✓ Schválit</button>');
          b.addEventListener("click",function(){ if(!confirm("Schválit nemocenskou pro "+(c.zamestnanec||"")+"?"))return; b.disabled=true; b.textContent="…"; api("POST","/api/v1/erp/app/sick/approve",{id:c.id}).then(function(r){ if(r&&r.ok){ sick_schval(); } else { b.disabled=false; b.textContent="✓ Schválit"; alert("Chyba: "+((r&&r.error)||"?")); } }); });
          rw.appendChild(b);
        } else { rw.appendChild(el('<div class="hint" style="margin-top:4px;">probíhá (čeká na ukončení)</div>')); }
        box.appendChild(rw);
      });
    });
  }
  function np_prehled(){
    app.innerHTML=topbar("📋 Nemoc a OČR — přehled", true);
    var bar=el('<div style="display:flex;gap:8px;margin:8px 6px;"></div>');
    var _act=true;
    var bAll=el('<button style="flex:1;padding:8px;border-radius:10px;cursor:pointer;"></button>');
    var bAct=el('<button style="flex:1;padding:8px;border-radius:10px;cursor:pointer;"></button>');
    bar.appendChild(bAct); bar.appendChild(bAll); app.appendChild(bar);
    var box=el('<div class="list"><div class="hint">Načítám…</div></div>'); app.appendChild(box);
    function paint(){
      bAct.style.cssText="flex:1;padding:8px;border-radius:10px;cursor:pointer;border:1px solid "+(_act?"var(--green)":"var(--bord)")+";background:"+(_act?"var(--green)":"rgba(255,255,255,.03)")+";color:"+(_act?"#04150e":"var(--mut)")+";font-weight:700;";
      bAll.style.cssText="flex:1;padding:8px;border-radius:10px;cursor:pointer;border:1px solid "+(!_act?"var(--green)":"var(--bord)")+";background:"+(!_act?"var(--green)":"rgba(255,255,255,.03)")+";color:"+(!_act?"#04150e":"var(--mut)")+";font-weight:700;";
      bAct.textContent="Probíhající"; bAll.textContent="Vše (i historie)";
    }
    function load(){
      paint(); box.innerHTML='<div class="hint">Načítám…</div>';
      api("GET","/api/v1/erp/app/hr/np-overview"+(_act?"?active=1":""),"").then(function(j){
        box.innerHTML="";
        if(!j||!j.ok){ box.innerHTML='<div class="hint">'+((j&&j.error==="forbidden")?"🔒 Jen rodiče a HR.":"Nepodařilo se načíst.")+'</div>'; return; }
        var it=j.items||[];
        if(!it.length){ box.innerHTML='<div class="hint">'+(_act?"Nikdo právě teď.":"Žádné záznamy.")+'</div>'; return; }
        var lblS={novy:"probíhá",trva:"probíhá",ukonceno:"ke schválení",schvaleno:"schváleno"};
        it.forEach(function(c){
          var ic=(c.kind==="ocr")?"🧑‍⚕️":"🤒"; var kindTxt=(c.kind==="ocr")?("OČR"+(c.osoba?(" · "+c.osoba):"")):"Nemocenská";
          var rw=el('<div style="display:flex;gap:10px;padding:9px 6px;border-bottom:1px solid var(--bord);"></div>');
          rw.appendChild(el('<div style="font-size:20px;">'+ic+'</div>'));
          rw.appendChild(el('<div style="flex:1;min-width:0;"><div style="font-weight:600;">'+esc(c.zamestnanec||"")+'</div><div class="hint">'+esc(kindTxt)+' · '+_czDate(c.od)+(c.do?(" – "+_czDate(c.do)):"")+(c.company?(" · "+esc(c.company)):"")+' · '+esc(lblS[c.stav]||c.stav)+'</div></div>'));
          box.appendChild(rw);
        });
      });
    }
    bAct.addEventListener("click",function(){ _act=true; load(); });
    bAll.addEventListener("click",function(){ _act=false; load(); });
    load();
  }
  // ── Lísteček od lékaře ─────────────────────────────────────────────────
  var _MED_TYP={vyset:"Vyšetření / ošetření",prevent:"Preventivní prohlídka",doprovod:"Doprovod"};
  function _krytiTxt(k){ return {sick_day:"sick day",listecek:"lísteček",kombinace:"sick day + lísteček"}[k]||k; }
  function med(){
    app.innerHTML=topbar("🩺 Lísteček od lékaře", true);
    var info=el('<div class="hint" style="margin:8px 6px;line-height:1.6;">Po návštěvě lékaře vyfoť lísteček a vyplň čas. Nejdřív se čerpá sick day (po hodinách), po jeho vyčerpání proplácíme lísteček do limitu.</div>');
    app.appendChild(info);
    var balBox=el('<div class="hint" style="margin:0 6px 6px;">Načítám zůstatek…</div>'); app.appendChild(balBox);
    var nb=el('<button style="'+_OCR_BTN+'">➕ Nová návštěva u lékaře</button>'); nb.addEventListener("click",function(){ medForm(); }); app.appendChild(nb);
    var box=el('<div class="list" style="margin-top:10px;"><div class="hint">Načítám…</div></div>'); app.appendChild(box);
    api("GET","/api/v1/erp/app/med/mine","").then(function(j){
      box.innerHTML="";
      if(!j||!j.ok){ box.innerHTML='<div class="hint">Nepodařilo se načíst.</div>'; return; }
      if(j.balance){ balBox.innerHTML='Zůstatek sick day: <b>'+j.balance.remaining_h+' h</b> (z '+j.balance.entitlement_h+' h/rok) · lísteček do <b>'+(j.limit_h||4)+' h</b>'; }
      var cs=j.cases||[];
      if(!cs.length){ box.innerHTML='<div class="hint">Zatím žádné lístečky.</div>'; return; }
      cs.forEach(function(c){
        var lbl={nahlaseno:"ke schválení",schvaleno:"schváleno",zamitnuto:"zamítnuto"}[c.stav]||c.stav;
        var rw=el('<div style="padding:10px 6px;border-bottom:1px solid var(--bord);"></div>');
        rw.appendChild(el('<div style="font-weight:600;">'+_czDate(c.datum)+(c.doba_h?(' · '+c.doba_h+' h'):'')+' · '+esc(_MED_TYP[c.typ]||c.typ)+'</div>'));
        rw.appendChild(el('<div class="hint">krytí: '+esc(_krytiTxt(c.kryti))+' · sick '+c.kryto_sick_h+' h · proplaceno '+c.proplaceno_listecek_h+' h'+(c.neplaceno_h?(' · neplac. '+c.neplaceno_h+' h'):'')+' · '+esc(lbl)+'</div>'));
        if(c.has_foto){ var a=el('<div style="margin-top:4px;"><a href="/api/v1/erp/app/med/photo/'+c.id+'" target="_blank" style="color:#5ee0b7;font-size:13px;">📷 zobrazit foto</a></div>'); rw.appendChild(a); }
        box.appendChild(rw);
      });
    });
  }
  function medForm(){
    app.innerHTML=topbar("➕ Návštěva u lékaře", true);
    var w=el('<div style="padding:6px;display:flex;flex-direction:column;gap:12px;"></div>'); app.appendChild(w);
    var fDat=_ocrFld(w,"Datum návštěvy","DD.MM.RRRR");
    var wr2=el('<div style="display:flex;gap:10px;"></div>');
    var c1=el('<div style="flex:1;"></div>'), c2=el('<div style="flex:1;"></div>'); wr2.appendChild(c1); wr2.appendChild(c2); w.appendChild(wr2);
    var fOd=_ocrFld(c1,"Čas od (odchod)","HH:MM");
    var fDo=_ocrFld(c2,"Čas do (návrat)","HH:MM");
    var tw=el('<div></div>'); tw.appendChild(el('<div style="font-size:13px;color:#cdd6e2;margin-bottom:4px;">Typ návštěvy</div>'));
    var sel=el('<select style="width:100%;box-sizing:border-box;padding:10px;border-radius:10px;border:1px solid #2b3a5c;background:#0a1226;color:#e8eefc;"><option value="vyset">Vyšetření / ošetření</option><option value="prevent">Preventivní prohlídka</option><option value="doprovod">Doprovod (rodinný příslušník)</option></select>');
    tw.appendChild(sel); w.appendChild(tw);
    var fOsoba=_ocrFld(w,"Doprovázená osoba (jen u doprovodu)","jméno");
    var fVz=_ocrFld(w,"Vztah (jen u doprovodu)","dítě / rodič / …");
    var fZar=_ocrFld(w,"Zdravotnické zařízení / lékař","nepovinné");
    // foto
    var _foto=null;
    var fw=el('<div></div>'); fw.appendChild(el('<div style="font-size:13px;color:#cdd6e2;margin-bottom:4px;">Foto lístečku</div>'));
    var cam=el('<button style="width:100%;box-sizing:border-box;padding:11px;border-radius:10px;border:1px dashed #3a4c70;background:rgba(255,255,255,.03);color:var(--tx);font-weight:700;cursor:pointer;">📷 Vyfotit lísteček</button>');
    var thumb=el('<img style="display:none;max-width:100%;margin-top:8px;border-radius:10px;border:1px solid var(--bord);">');
    cam.addEventListener("click",function(){
      var fi=el('<input type="file" accept="image/*" capture="environment" style="display:none;">'); document.body.appendChild(fi);
      fi.addEventListener("change",function(){ var f=fi.files&&fi.files[0]; if(!f){fi.remove();return;} var fr=new FileReader(); fr.onload=function(){ _foto=fr.result; thumb.src=_foto; thumb.style.display="block"; cam.textContent="📷 Přefotit lísteček"; try{fi.remove();}catch(e){} }; fr.readAsDataURL(f); });
      fi.click();
    });
    fw.appendChild(cam); fw.appendChild(thumb); w.appendChild(fw);
    var st=el('<div class="hint" style="min-height:16px;"></div>'); w.appendChild(st);
    var sv=el('<button style="'+_OCR_BTN+'">Odeslat ke schválení</button>'); w.appendChild(sv);
    var cx=el('<button class="ghost sm" style="margin-top:4px;">Zrušit</button>'); cx.addEventListener("click",function(){ med(); }); w.appendChild(cx);
    sv.addEventListener("click",function(){
      var d=_isoDate(fDat.value); if(!/^\d{4}-\d{2}-\d{2}/.test(d)){ st.style.color="#ff8b8b"; st.textContent="Datum ve formátu DD.MM.RRRR."; return; }
      if(!_foto){ st.style.color="#ff8b8b"; st.textContent="Vyfoť prosím lísteček."; return; }
      sv.disabled=true; st.style.color="#9fb2d4"; st.textContent="Odesílám…";
      api("POST","/api/v1/erp/app/med/start",{datum:d,cas_od:(fOd.value||"").trim(),cas_do:(fDo.value||"").trim(),typ:sel.value,osoba_jmeno:(fOsoba.value||"").trim(),osoba_vztah:(fVz.value||"").trim(),zarizeni:(fZar.value||"").trim(),foto:_foto}).then(function(r){
        if(r&&r.ok){ med(); } else { sv.disabled=false; st.style.color="#ff8b8b"; st.textContent="Chyba: "+((r&&r.error)||"?"); }
      });
    });
  }
  function med_schval(){
    app.innerHTML=topbar("🩺 Lístečky — schvalování", true);
    var box=el('<div class="list"><div class="hint">Načítám…</div></div>'); app.appendChild(box);
    api("GET","/api/v1/erp/app/med/inbox","").then(function(j){
      box.innerHTML="";
      if(!j||!j.ok){ box.innerHTML='<div class="hint">'+((j&&j.error==="forbidden")?"🔒 Jen rodiče a HR.":"Nepodařilo se načíst.")+'</div>'; return; }
      var cs=j.cases||[];
      if(!cs.length){ box.innerHTML='<div class="hint">Nic ke schválení.</div>'; return; }
      cs.forEach(function(c){
        var rw=el('<div style="padding:10px 6px;border-bottom:1px solid var(--bord);"></div>');
        rw.appendChild(el('<div style="font-weight:600;">'+esc(c.zamestnanec||"")+' · '+_czDate(c.datum)+(c.doba_h?(' · '+c.doba_h+' h'):'')+'</div>'));
        rw.appendChild(el('<div class="hint">'+esc(_MED_TYP[c.typ]||c.typ)+(c.zarizeni?(' · '+esc(c.zarizeni)):'')+(c.company?(' · '+esc(c.company)):'')+'<br>krytí: '+esc(_krytiTxt(c.kryti))+' · sick '+c.kryto_sick_h+' h · proplaceno '+c.proplaceno_listecek_h+' h (limit '+c.limit_h+')'+(c.neplaceno_h?(' · neplac. '+c.neplaceno_h+' h'):'')+'</div>'));
        if(c.has_foto){ rw.appendChild(el('<div style="margin-top:4px;"><a href="/api/v1/erp/app/med/photo/'+c.id+'" target="_blank" style="color:#5ee0b7;font-size:13px;">📷 zobrazit foto</a></div>')); }
        var b=el('<button style="margin-top:6px;padding:8px 14px;border-radius:10px;border:1px solid #34d399;background:rgba(52,211,153,.15);color:#5ee0b7;font-weight:700;cursor:pointer;">✓ Schválit</button>');
        b.addEventListener("click",function(){ if(!confirm("Schválit lísteček pro "+(c.zamestnanec||"")+"?"))return; b.disabled=true; b.textContent="…"; api("POST","/api/v1/erp/app/med/approve",{id:c.id}).then(function(r){ if(r&&r.ok){ med_schval(); } else { b.disabled=false; b.textContent="✓ Schválit"; alert("Chyba: "+((r&&r.error)||"?")); } }); });
        rw.appendChild(b);
        box.appendChild(rw);
      });
    });
  }
  function med_prehled(){
    app.innerHTML=topbar("🩺 Lékař — přehled", true);
    var sum=el('<div class="hint" style="margin:8px 6px;"></div>'); app.appendChild(sum);
    var box=el('<div class="list"><div class="hint">Načítám…</div></div>'); app.appendChild(box);
    api("GET","/api/v1/erp/app/hr/med-overview","").then(function(j){
      box.innerHTML="";
      if(!j||!j.ok){ box.innerHTML='<div class="hint">'+((j&&j.error==="forbidden")?"🔒 Jen rodiče a HR.":"Nepodařilo se načíst.")+'</div>'; return; }
      var it=j.items||[]; if(!it.length){ box.innerHTML='<div class="hint">Žádné lístečky.</div>'; return; }
      var tProp=0,tDoba=0; it.forEach(function(c){ tProp+=c.proplaceno_listecek_h||0; tDoba+=c.doba_h||0; });
      sum.innerHTML='Celkem '+it.length+' návštěv · doba '+(Math.round(tDoba*10)/10)+' h · proplaceno lístečkem '+(Math.round(tProp*10)/10)+' h';
      it.forEach(function(c){
        var lbl={nahlaseno:"ke schválení",schvaleno:"schváleno",zamitnuto:"zamítnuto"}[c.stav]||c.stav;
        var rw=el('<div style="padding:9px 6px;border-bottom:1px solid var(--bord);"></div>');
        rw.appendChild(el('<div style="font-weight:600;">'+esc(c.zamestnanec||"")+' · '+_czDate(c.datum)+'</div>'));
        rw.appendChild(el('<div class="hint">'+(c.doba_h||0)+' h · '+esc(_krytiTxt(c.kryti))+' · proplaceno '+c.proplaceno_listecek_h+' h'+(c.company?(' · '+esc(c.company)):'')+' · '+esc(lbl)+(c.has_foto?' · 📷':'')+'</div>'));
        box.appendChild(rw);
      });
    });
  }
  function hr_podminky(){
    app.innerHTML=topbar("📋 Podmínky skupin", true);
    var _pd={f:"system", groups:[]};
    function gLabel(key){ if(key==="system")return "Systém (výchozí pro všechny)"; if(key==="lide")return "Jednotlivci";
      var g=_pd.groups.filter(function(x){return String(x.code)===String(key);})[0]; return g?g.label:key; }
    var pane=el('<div style="display:flex;gap:10px;height:calc(64vh - 86px);align-items:stretch;">'
      +'<div id="pdC" style="flex:1;min-width:0;overflow-y:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none;border:1px solid var(--bord);border-radius:12px;background:rgba(255,255,255,0.02);padding:6px 10px;"><div class="hint">Načítám…</div></div>'
      +'<div id="pdRail" style="width:84px;flex:none;overflow-y:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none;display:flex;flex-direction:column;gap:6px;padding:0 0 86px;"></div></div>');
    app.appendChild(pane);
    var C=pane.querySelector("#pdC"), R=pane.querySelector("#pdRail");
    function railBtn(icon,label,key){
      var on=(_pd.f===key);
      var b=el('<button style="width:100%;box-sizing:border-box;margin:0;padding:9px 4px;font-size:10.5px;line-height:1.15;display:flex;flex-direction:column;align-items:center;gap:3px;border:1px solid '+(on?"var(--green)":"var(--bord)")+';background:'+(on?"var(--green)":"rgba(255,255,255,0.02)")+';color:'+(on?"#04150e":"var(--mut)")+';border-radius:12px;cursor:pointer;"><span style="font-size:20px;line-height:1;">'+icon+'</span>'+esc(label)+'</button>');
      b.addEventListener("click",function(){ _pd.f=key; render(); });
      return b;
    }
    function fieldEl(d,value){
      var v=(value==null?"":value);
      if(d.kind==="bool"){
        var s=el('<select style="width:120px;padding:7px;border-radius:8px;border:1px solid #2b3a5c;background:#0a1226;color:#e8eefc;"><option value="">— dědit —</option><option value="ANO">ANO</option><option value="NE">NE</option></select>');
        s.value=(v==="ANO"||v==="NE")?v:""; return s;
      }
      var i=el('<input type="text" value="'+esc(v)+'" '+(d.kind==="num"?'inputmode="decimal"':'')+' placeholder="'+(d.kind==="time"?"HH:MM":"— dědit —")+'" style="width:120px;box-sizing:border-box;padding:7px 9px;border-radius:8px;border:1px solid #2b3a5c;background:#0a1226;color:#e8eefc;text-align:right;">');
      return i;
    }
    function scopeView(key){
      C.innerHTML='<div class="hint">Načítám…</div>';
      var sk=(key==="system")?"system":"group", gc=(key==="system")?"":key;
      api("GET","/api/v1/erp/app/hr/conditions?scope_kind="+sk+(gc?("&group_code="+gc):""),"").then(function(j){
        C.innerHTML="";
        if(!j||!j.ok){ C.appendChild(el('<div class="hint">'+esc((j&&j.error==="forbidden")?"Jen HR / vedení.":"Nelze načíst.")+'</div>')); return; }
        C.appendChild(el('<div style="font-size:18px;font-weight:800;margin:2px 0 2px;">'+esc(gLabel(key))+'</div>'));
        C.appendChild(el('<div class="hint" style="margin-bottom:10px;">'+(sk==="system"?"Výchozí pro všechny. Skupina nebo jednotlivec to může přepsat.":"Hodnoty skupiny. Prázdné = zdědí ze systému. Členství se spravuje ve Skupinách.")+'</div>'));
        var st=el('<div class="hint" style="min-height:16px;margin-bottom:6px;"></div>'); C.appendChild(st);
        (j.defs||[]).forEach(function(d){
          var cur=(j.values&&j.values[d.code])?j.values[d.code].value:null;
          var row=el('<div style="display:flex;align-items:center;gap:10px;padding:7px 2px;border-bottom:1px solid #1b2742;"></div>');
          row.appendChild(el('<div style="flex:1;min-width:0;">'+esc(d.label)+(d.unit?(' <span class="hint">('+esc(d.unit)+')</span>'):'')+'</div>'));
          var f=fieldEl(d,cur); row.appendChild(f);
          function save(){ st.style.color="#9fb2d4"; st.textContent="Ukládám…";
            api("POST","/api/v1/erp/app/hr/conditions/save",{scope_kind:sk,group_code:gc,cond_code:d.code,value:f.value}).then(function(r){
              st.style.color=(r&&r.ok)?"#5ee0b7":"#f88"; st.textContent=(r&&r.ok)?("Uloženo: "+d.label+" ✓"):("✗ "+((r&&r.error)||"chyba")); });
          }
          f.addEventListener("change",save);
          C.appendChild(row);
        });
      });
    }
    function peopleView(){
      C.innerHTML='<input id="pdSrch" type="text" placeholder="Hledat jméno…" style="width:100%;box-sizing:border-box;padding:9px 11px;border-radius:9px;border:1px solid #2b3a5c;background:#0a1226;color:#e8eefc;margin-bottom:8px;"><div id="pdPpl"><div class="hint">Načítám…</div></div>';
      var srch=C.querySelector("#pdSrch"), box=C.querySelector("#pdPpl"), all=[], skupiny=[];
      function draw(q){
        box.innerHTML=""; var arr=all.filter(function(p){ return !q||(p.jmeno||"").toLowerCase().indexOf(q.toLowerCase())>=0; });
        if(!arr.length){ box.appendChild(el('<div class="hint">Nikdo.</div>')); return; }
        arr.forEach(function(p){
          var gl=p.cond_group||"— bez skupiny —";
          var li=el('<div class="ct" style="border-bottom:1px solid #1b2742;"></div>');
          var head=el('<div style="display:flex;align-items:center;gap:8px;cursor:pointer;padding:9px 2px;"></div>');
          head.appendChild(el('<div style="flex:1;min-width:0;"><div style="font-weight:600;">'+esc(p.jmeno)+'</div><div class="hint">'+esc(gl)+(p.vyjimka?' · <span style="color:#fbbf24;">vlastní výjimka</span>':'')+'</div></div>'));
          head.appendChild(el('<div class="chev" style="color:#5a6;">&#8250;</div>'));
          var ed=el('<div class="ctexp" style="display:none;padding:2px 2px 12px;"></div>');
          head.addEventListener("click",function(){ var op=li.classList.toggle("open"); ed.style.display=op?"block":"none"; if(op&&ed.dataset.b!=="1"){ personDetail(ed,p,skupiny); ed.dataset.b="1"; } });
          li.appendChild(head); li.appendChild(ed); box.appendChild(li);
        });
      }
      api("GET","/api/v1/erp/app/hr/conditions/people","").then(function(j){
        if(!j||!j.ok){ box.innerHTML='<div class="hint">'+esc((j&&j.error==="forbidden")?"Jen HR / vedení.":"Nelze načíst.")+'</div>'; return; }
        all=j.lide||[]; skupiny=j.skupiny||[]; draw("");
      });
      var td=null; srch.addEventListener("input",function(){ clearTimeout(td); td=setTimeout(function(){ draw(srch.value.trim()); },200); });
    }
    function personDetail(ed,p,skupiny){
      ed.innerHTML='<div class="hint">Načítám…</div>';
      api("GET","/api/v1/erp/app/hr/conditions?scope_kind=user&user_id="+p.user_id,"").then(function(j){
        ed.innerHTML="";
        if(!j||!j.ok){ ed.appendChild(el('<div class="hint">Nelze načíst.</div>')); return; }
        var glab=(skupiny.filter(function(g){return String(g.code)===String(j.group_code);})[0]||{}).label||(j.group_code?j.group_code:"— bez skupiny —");
        ed.appendChild(el('<div class="hint" style="margin-bottom:8px;">Podmínková skupina (dle členství): <b style="color:#9cf;">'+esc(glab)+'</b> <span class="hint">· mění se ve Skupinách</span></div>'));
        var st=el('<div class="hint" style="min-height:16px;margin:6px 0;"></div>'); ed.appendChild(st);
        (j.defs||[]).forEach(function(d){
          var rs=(j.resolved&&j.resolved[d.code])||{}; var own=(j.own&&j.own[d.code])?j.own[d.code].value:null;
          var row=el('<div style="display:flex;align-items:center;gap:8px;padding:6px 2px;border-bottom:1px solid #1b2742;"></div>');
          var srcCol={"osobní":"#fbbf24","skupina":"#60a5fa","systém":"#9aa"}[rs.src]||"#9aa";
          row.appendChild(el('<div style="flex:1;min-width:0;font-size:13px;">'+esc(d.label)+'<br><span class="hint">teď: <b style="color:'+srcCol+';">'+esc(rs.value==null?"—":rs.value)+'</b> ('+esc(rs.src||"—")+')</span></div>'));
          var f=fieldEl(d,own); row.appendChild(f);
          f.addEventListener("change",function(){ st.style.color="#9fb2d4"; st.textContent="Ukládám…";
            api("POST","/api/v1/erp/app/hr/conditions/save",{scope_kind:"user",user_id:p.user_id,cond_code:d.code,value:f.value}).then(function(r){
              st.style.color=(r&&r.ok)?"#5ee0b7":"#f88"; st.textContent=(r&&r.ok)?(d.label+": výjimka uložena ✓"):("✗ "+((r&&r.error)||"chyba"));
              if(r&&r.ok) setTimeout(function(){ ed.dataset.b=""; personDetail(ed,p,skupiny); },500);
            }); });
          ed.appendChild(row);
        });
        ed.appendChild(el('<div class="hint" style="margin-top:6px;">Prázdné pole = zdědí ze skupiny/systému. Vyplněné = osobní výjimka.</div>'));
        // 📅 Vzor týdne
        ed.appendChild(el('<div style="font-weight:700;margin:14px 0 2px;">📅 Vzor týdne</div>'));
        var schBox=el('<div></div>'); ed.appendChild(schBox); schBox.innerHTML='<div class="hint">Načítám…</div>';
        api("GET","/api/v1/erp/app/hr/schedule?user_id="+p.user_id,"").then(function(sj){
          schBox.innerHTML="";
          if(!sj||!sj.ok){ schBox.appendChild(el('<div class="hint">Nelze načíst.</div>')); return; }
          var info=el('<div class="hint" style="margin-bottom:4px;">Úvazek '+sj.uvazek+' h/týд · součet vzoru: <b id="schSum_'+p.user_id+'">'+sj.suma_h+'</b> h. Šedé dny = odvozeno z úvazku, dokud nenastavíš.</div>');
          schBox.appendChild(info);
          var sst=el('<div class="hint" style="min-height:14px;margin-bottom:4px;"></div>'); schBox.appendChild(sst);
          var states=[];
          function recalc(){ var sum=0; states.forEach(function(x){ if(x.chk.checked) sum+=(parseFloat(x.hin.value)||0); });
            var e=document.getElementById("schSum_"+p.user_id); if(e) e.textContent=Math.round(sum*100)/100; }
          sj.dny.forEach(function(d){
            var rowS=el('<div style="display:flex;align-items:center;gap:8px;padding:5px 2px;border-bottom:1px solid #1b2742;'+(d.explicit?'':'opacity:0.65;')+'"></div>');
            var chk=el('<input type="checkbox" '+(d.works?'checked':'')+' style="width:18px;height:18px;">');
            rowS.appendChild(chk);
            rowS.appendChild(el('<div style="width:72px;font-size:13px;">'+esc(d.label)+'</div>'));
            var hin=el('<input type="number" step="0.5" value="'+d.hours+'" style="width:56px;box-sizing:border-box;padding:6px;border-radius:8px;border:1px solid #2b3a5c;background:#0a1226;color:#e8eefc;text-align:right;">');
            rowS.appendChild(hin); rowS.appendChild(el('<span class="hint">h</span>'));
            var ein=el('<input type="text" placeholder="konec" value="'+(d.end_time||"")+'" inputmode="numeric" style="width:62px;box-sizing:border-box;padding:6px;border-radius:8px;border:1px solid #2b3a5c;background:#0a1226;color:#e8eefc;text-align:center;">');
            rowS.appendChild(ein);
            states.push({wd:d.weekday,chk:chk,hin:hin,ein:ein});
            function save(){ rowS.style.opacity="1"; sst.style.color="#9fb2d4"; sst.textContent="Ukládám…"; recalc();
              api("POST","/api/v1/erp/app/hr/schedule/save",{user_id:p.user_id,weekday:d.weekday,works:chk.checked,hours:parseFloat(hin.value)||0,end_time:ein.value.trim()}).then(function(r){
                sst.style.color=(r&&r.ok)?"#5ee0b7":"#f88"; sst.textContent=(r&&r.ok)?(d.label+" uloženo ✓"):("✗ "+((r&&r.error)||"chyba")); }); }
            chk.addEventListener("change",save); hin.addEventListener("change",save); ein.addEventListener("change",save);
            schBox.appendChild(rowS);
          });
          schBox.appendChild(el('<div class="hint" style="margin-top:6px;">Příklad: středa „konec 12:00" → zaškrtni St, hodiny 4, konec 12:00. Čtvrtek nedělá → odškrtni Čt.</div>'));
        });
      });
    }
    function render(){
      R.innerHTML="";
      R.appendChild(railBtn("⚙️","Systém","system"));
      _pd.groups.forEach(function(g){ R.appendChild(railBtn(g.icon||"👥",g.label,String(g.code))); });
      R.appendChild(railBtn("🧑","Jednotlivci","lide"));
      if(_pd.f==="lide") peopleView(); else scopeView(_pd.f);
    }
    C.innerHTML='<div class="hint">Načítám skupiny…</div>';
    api("GET","/api/v1/erp/app/hr/conditions/groups","").then(function(j){
      _pd.groups=(j&&j.ok&&j.skupiny)||[]; render();
    });
  }
  function _meIcon(lbl){ var s=(lbl||"").toLowerCase();
    if(/identi|jmén|jmen|osob/.test(s))return"🪪"; if(/osvč|osvc|ičo|ico|dič|dic|podnik/.test(s))return"🧾";
    if(/adres|bydli/.test(s))return"🏠"; if(/kontakt|e-?mail|telefon|nouz/.test(s))return"✉️";
    if(/výplat|vyplat|účet|ucet|banka|iban|pojišť|pojist/.test(s))return"🏦"; if(/doklad|rodné|op |pas|průkaz/.test(s))return"🔒";
    if(/pamě|pamet|poznám|poznam/.test(s))return"📝"; return"📄"; }
  function hr_me(){
    app.innerHTML=topbar("", true);
    var pane=el('<div style="position:relative;display:flex;gap:10px;height:calc(100vh - 168px);align-items:stretch;">'
      +'<div id="meContent" style="flex:1;min-width:0;overflow-y:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none;"><div class="hint">Načítám…</div></div>'
      +'<div id="meRail" style="width:86px;flex:none;overflow-y:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none;display:flex;flex-direction:column;gap:6px;padding:0;"></div></div>');
    app.appendChild(pane);
    var cont=pane.querySelector("#meContent"), rail=pane.querySelector("#meRail");
    var toggleBtn=el('<button style="position:absolute;top:6px;right:6px;z-index:5;display:none;padding:7px 11px;border-radius:10px;border:1px solid var(--bord);background:#1a2440;color:#cfe;font-size:13px;box-shadow:0 2px 8px rgba(0,0,0,.4);">📑 Sekce</button>');
    pane.appendChild(toggleBtn);
    function showRail(on){ rail.style.display=on?"":"none"; toggleBtn.style.display=on?"none":""; }
    // ťuknutí do seznamu → schovej lištu, plná šířka
    cont.addEventListener("click",function(){ if(rail.style.display!=="none") showRail(false); });
    toggleBtn.addEventListener("click",function(e){ e.stopPropagation(); showRail(true); });
    // Zpět: když je roztažené na celou šířku, nejdřív zúžit a vrátit lištu
    window._dochAnyOpen=function(){ if(!document.body.contains(pane)) return false;
      if(rail.style.display==="none"){ showRail(true); return true; } return false; };
    function scrollToId(id){ var t=document.getElementById(id); if(t) cont.scrollTop=Math.max(0, t.offsetTop - cont.offsetTop - 4); }
    var anchors=[], inputs={};
    function buildRail(){
      rail.innerHTML="";
      anchors.forEach(function(a){
        var b=el('<button style="width:100%;box-sizing:border-box;margin:0;padding:10px 6px;font-size:11.5px;line-height:1.2;text-align:center;word-break:break-word;border:1px solid var(--bord);background:rgba(255,255,255,0.02);color:#cdd;border-radius:11px;cursor:pointer;">'+(a.icon?('<span style="font-size:20px;display:block;line-height:1.1;margin-bottom:2px;">'+a.icon+'</span>'):'')+esc(a.label)+'</button>');
        b.addEventListener("click",function(e){ e.stopPropagation(); scrollToId(a.id); });
        rail.appendChild(b);
      });
    }
    api("GET","/api/v1/erp/app/self-data","").then(function(j){
      cont.innerHTML="";
      if(!j||!j.ok){ cont.innerHTML='<div class="hint">Nepodařilo se načíst ('+esc((j&&j.error)||"chyba")+').</div>'; return; }
      cont.appendChild(el('<div style="font-size:22px;font-weight:800;margin:2px 0 4px;">🪪 Moje osobní údaje</div>'));
      cont.appendChild(el('<div class="hint" style="line-height:1.55;margin-bottom:12px;">Tvoje údaje spravuješ ty sám — jsou <b>primárním zdrojem</b> pro smlouvu, výplatu a evidenci. Vpravo skoč rovnou na sekci; ťukni do seznamu a lišta se schová pro plnou šířku.</div>'));
      (j.sections||[]).forEach(function(sec,i){
        var sid="mesec_"+i; anchors.push({label:(sec.label||("Sekce "+(i+1))),id:sid});
        var card=el('<div id="'+sid+'" style="background:#0f1830;border:1px solid #22304f;border-radius:14px;padding:12px 14px;margin-bottom:12px;"></div>');
        card.appendChild(el('<div style="font-weight:700;font-size:16px;margin-bottom:2px;">'+esc(sec.label)+'</div>'));
        card.appendChild(el('<div class="hint" style="margin-bottom:10px;line-height:1.5;">'+esc(sec.why)+'</div>'));
        (sec.items||[]).forEach(function(it){
          var fld=el('<div style="margin-bottom:10px;"></div>');
          fld.innerHTML='<label style="display:block;font-size:13px;color:#9fb2d4;margin-bottom:3px;">'+esc(it.label)+(it.sensitive?' 🔒':'')+'</label>';
          var _sty='width:100%;box-sizing:border-box;padding:10px 12px;border-radius:10px;border:1px solid #2b3a5c;background:#0a1226;color:#e8eefc;font-size:15px;';
          var inp, isDate=(it.type==="date");
          if(it.type==="textarea"){ inp=el('<textarea rows="5" style="'+_sty+'resize:vertical;"></textarea>'); }
          else { inp=el('<input type="'+(it.type==="email"?"email":(it.type==="tel"?"tel":"text"))+'" style="'+_sty+'">'); if(isDate){ inp.placeholder="DD.MM.RRRR"; inp.inputMode="numeric"; } }
          inp.value = isDate ? _czDate(it.value) : (it.value||"");
          if(isDate) inp._isDate=true;
          if(it.key==="birth_number") inp._isRc=true;
          inputs[it.key]=inp; fld.appendChild(inp); card.appendChild(fld);
        });
        cont.appendChild(card);
      });
      if(j.updated_at){ cont.appendChild(el('<div class="hint" style="margin:-4px 0 8px;">Naposledy upraveno: '+esc(new Date(j.updated_at).toLocaleString("cs"))+'</div>')); }
      var st=el('<div class="hint" style="margin:4px 0 8px;min-height:18px;"></div>'); cont.appendChild(st);
      var btn=el('<button style="width:100%;padding:14px;border:0;border-radius:12px;background:#2563eb;color:#fff;font-size:16px;font-weight:700;margin-bottom:14px;">💾 Uložit moje údaje</button>');
      btn.addEventListener("click",function(){
        var vals={}, rcBad=false; Object.keys(inputs).forEach(function(k){ var v=inputs[k].value; if(inputs[k]._isDate) v=_isoDate(v); if(inputs[k]._isRc && (v||"").trim() && !_rcValid(v)) rcBad=true; vals[k]=v; });
        if(rcBad){ if(!confirm("Rodné číslo neprošlo kontrolou (modulo 11). Uložit přesto?"))return; }
        btn.disabled=true; st.style.color="#9fb2d4"; st.textContent="Ukládám…";
        api("POST","/api/v1/erp/app/self-data/save",{values:vals}).then(function(r){
          btn.disabled=false;
          if(r&&r.ok){ st.style.color="#5ee0b7"; st.textContent=(r.changed>0)?("Uloženo ✓ ("+r.changed+" změn)"):"Beze změn ✓"; }
          else { st.style.color="#f88"; st.textContent="Chyba: "+esc((r&&r.error)||"nepodařilo se uložit"); }
        });
      });
      cont.appendChild(btn);
      var cb=el('<div id="mesec_deti"></div>'); cont.appendChild(cb); _selfChildren(cb); anchors.push({icon:"👨‍👩‍👧",label:"Děti",id:"mesec_deti"});
      var vb=el('<div id="mesec_trezor" style="margin-top:6px;"></div>'); cont.appendChild(vb); _selfVault(vb); anchors.push({icon:"🔐",label:"Trezor",id:"mesec_trezor"});
      cont.appendChild(el('<div style="height:30px;"></div>'));
      buildRail();
    });
  }
  // --- karta: deti/blizke osoby ---
  function _card(title,hint){ var c=el('<div style="background:#0f1830;border:1px solid #22304f;border-radius:14px;padding:12px 14px;margin-bottom:12px;"></div>'); c.appendChild(el('<div style="font-weight:700;font-size:16px;margin-bottom:2px;">'+title+'</div>')); if(hint)c.appendChild(el('<div class="hint" style="margin-bottom:10px;line-height:1.5;">'+esc(hint)+'</div>')); return c; }
  function _fld(label,val,ph){ var w=el('<div style="margin-bottom:8px;"></div>'); w.innerHTML='<label style="display:block;font-size:12px;color:#9fb2d4;margin-bottom:3px;">'+esc(label)+'</label>'; var i=el('<input type="text" style="width:100%;box-sizing:border-box;padding:9px 11px;border-radius:9px;border:1px solid #2b3a5c;background:#0a1226;color:#e8eefc;font-size:15px;">'); i.value=val||""; if(ph)i.placeholder=ph; w.appendChild(i); w._inp=i; return w; }
  function _selfChildren(box){
    function render(j){
      box.innerHTML="";
      var card=_card("👨‍👩‍👧 Děti a blízké osoby","Rodná čísla dětí pro slevu na dani a kontakty na blízké. Soukromé — vidíš jen ty (a HR pro daňové).");
      box.appendChild(card);
      var deti=(j&&j.ok&&j.deti)?j.deti:[];
      if(!deti.length){ card.appendChild(el('<div class="hint" style="padding:8px 0;">Zatím nikdo. Přidej dítě nebo blízkou osobu.</div>')); }
      deti.forEach(function(d){
        var r=el('<div style="display:flex;align-items:center;gap:8px;padding:8px 0;border-top:1px solid #1b2742;"></div>');
        var t=(d.child_name||"(bez jména)")+(d.relation?(" · "+d.relation):"")+(d.relief_order?(" · "+d.relief_order+". dítě"):"");
        var sub=[_czDate(d.birth_date),d.birth_number].filter(Boolean).join(" · ");
        r.appendChild(el('<div style="flex:1;"><div style="font-weight:600;">'+esc(t)+'</div>'+(sub?'<div class="hint">'+esc(sub)+'</div>':'')+'</div>'));
        var e=el('<button style="background:#1d2a44;border:0;color:#cfe;border-radius:8px;padding:6px 9px;">✏️</button>'); e.onclick=function(){ form(d); }; r.appendChild(e);
        var x=el('<button style="background:#3a1d28;border:0;color:#f9b;border-radius:8px;padding:6px 9px;">🗑</button>'); x.onclick=function(){ if(confirm("Smazat "+(d.child_name||"záznam")+"?")) api("POST","/api/v1/erp/app/self-child/delete",{id:d.id}).then(load); }; r.appendChild(x);
        card.appendChild(r);
      });
      var add=el('<button style="width:100%;margin-top:8px;padding:10px;border:1px dashed #2b3a5c;border-radius:10px;background:transparent;color:#9fd;">➕ Přidat</button>'); add.onclick=function(){ form(null); }; card.appendChild(add);
    }
    function form(d){
      d=d||{}; box.innerHTML="";
      var f=_card(d.id?"Upravit":"➕ Přidat dítě / blízkou osobu",""); box.appendChild(f);
      var fn=_fld("Jméno",d.child_name), rel=_fld("Vztah (dítě / manželka / …)",d.relation),
          bd=_fld("Datum narození",_czDate(d.birth_date),"DD.MM.RRRR"), rc=_fld("Rodné číslo",d.birth_number),
          ord=_fld("Pořadí dítěte pro slevu (1/2/3)",d.relief_order), em=_fld("E-mail",d.email), ph=_fld("Telefon",d.phone);
      [fn,rel,bd,rc,ord,em,ph].forEach(function(w){f.appendChild(w);});
      var save=el('<button style="width:100%;padding:11px;border:0;border-radius:10px;background:#2563eb;color:#fff;font-weight:700;">💾 Uložit</button>');
      save.onclick=function(){
        var rcv=(rc._inp.value||"").trim();
        if(rcv && !_rcValid(rcv)){ if(!confirm("Rodné číslo neprošlo kontrolou (modulo 11). Uložit přesto?"))return; }
        api("POST","/api/v1/erp/app/self-child/save",{id:d.id,child_name:fn._inp.value,relation:rel._inp.value,birth_date:_isoDate(bd._inp.value),birth_number:rcv,relief_order:ord._inp.value,email:em._inp.value,phone:ph._inp.value}).then(function(r){ if(r&&r.ok)load(); else alert("Chyba: "+((r&&r.error)||"?")); });
      };
      f.appendChild(save);
      var back=el('<button style="width:100%;margin-top:6px;padding:9px;border:0;border-radius:10px;background:#26304a;color:#cdd;">Zpět</button>'); back.onclick=load; f.appendChild(back);
    }
    function load(){ api("GET","/api/v1/erp/app/self-child","").then(render); }
    load();
  }
  // --- karta: trezor hesel ---
  function _selfVault(box){
    function reveal(id,label){
      var pin=prompt("Zadej PIN pro zobrazení hesla:"); if(!pin)return;
      api("POST","/api/v1/erp/app/self-secret/reveal",{id:id,pin:pin}).then(function(x){
        if(x&&x.ok){ prompt("🔓 "+(x.label||label)+" (zkopíruj):", x.secret); }
        else alert("Chyba: "+((x&&(x.note||x.error))||"?"));
      });
    }
    function render(j){
      box.innerHTML="";
      var card=_card("🔐 Hesla a tokeny","Šifrované. Zobrazení jen po PINu + SMS kódu. Nikdo jiný (ani HR, ani vedení) je nevidí. Každé otevření ti přijde e-mailem.");
      box.appendChild(card);
      if(!j||!j.ok){ card.appendChild(el('<div class="hint">Nelze načíst.</div>')); return; }
      if(!j.vault_ready){ card.appendChild(el('<div class="hint" style="color:#fc8;">Trezor zatím není aktivní — čeká na bezpečnostní klíč na serveru.</div>')); return; }
      if(!j.has_pin){ card.appendChild(el('<div class="hint" style="color:#fc8;">Nejdřív si nastav PIN (Nastavení → PIN), pak půjde trezor odemykat.</div>')); }
      var pol=j.polozky||[];
      if(!pol.length){ card.appendChild(el('<div class="hint" style="padding:8px 0;">Trezor je prázdný. Ulož si první heslo.</div>')); }
      pol.forEach(function(p){
        var r=el('<div style="display:flex;align-items:center;gap:8px;padding:8px 0;border-top:1px solid #1b2742;"></div>');
        r.appendChild(el('<div style="flex:1;"><div style="font-weight:600;">'+esc(p.label)+'</div>'+(p.username?'<div class="hint">'+esc(p.username)+'</div>':'')+'</div>'));
        var v=el('<button style="background:#1d3a2a;border:0;color:#9f9;border-radius:8px;padding:6px 9px;">👁</button>'); v.onclick=function(){ reveal(p.id,p.label); }; r.appendChild(v);
        var e=el('<button style="background:#1d2a44;border:0;color:#cfe;border-radius:8px;padding:6px 9px;">✏️</button>'); e.onclick=function(){ form(p); }; r.appendChild(e);
        var x=el('<button style="background:#3a1d28;border:0;color:#f9b;border-radius:8px;padding:6px 9px;">🗑</button>'); x.onclick=function(){ if(confirm("Smazat „"+p.label+"\"?")) api("POST","/api/v1/erp/app/self-secret/delete",{id:p.id}).then(load); }; r.appendChild(x);
        card.appendChild(r);
      });
      var add=el('<button style="width:100%;margin-top:8px;padding:10px;border:1px dashed #2b3a5c;border-radius:10px;background:transparent;color:#9fd;">➕ Přidat heslo / token</button>'); add.onclick=function(){ form(null); }; card.appendChild(add);
    }
    function form(p){
      p=p||{}; box.innerHTML="";
      var f=_card(p.id?"Upravit položku":"➕ Nové heslo / token",""); box.appendChild(f);
      var lb=_fld("Název (např. Email, VPN, banka)",p.label), un=_fld("Uživatel / login",p.username),
          se=_fld("Heslo / token",""), ur=_fld("Web / poznámka kam",p.url);
      if(p.id) se._inp.placeholder="(nech prázdné = ponechat stávající)";
      [lb,un,se,ur].forEach(function(w){f.appendChild(w);});
      var save=el('<button style="width:100%;padding:11px;border:0;border-radius:10px;background:#2563eb;color:#fff;font-weight:700;">💾 Uložit zašifrovaně</button>');
      save.onclick=function(){ api("POST","/api/v1/erp/app/self-secret/save",{id:p.id,label:lb._inp.value,username:un._inp.value,secret:se._inp.value,url:ur._inp.value}).then(function(r){ if(r&&r.ok)load(); else alert("Chyba: "+((r&&(r.note||r.error))||"?")); }); };
      f.appendChild(save);
      var back=el('<button style="width:100%;margin-top:6px;padding:9px;border:0;border-radius:10px;background:#26304a;color:#cdd;">Zpět</button>'); back.onclick=load; f.appendChild(back);
    }
    function load(){ api("GET","/api/v1/erp/app/self-secret","").then(render); }
    load();
  }
  // --- HR: prehled lidi + karta (jen HR/rodice; citlive se nezobrazuji) ---
  function hr_people(){
    app.innerHTML=topbar("👥 Personální složky", true);
    var srch=el('<input type="text" placeholder="Hledat jméno…" style="width:100%;box-sizing:border-box;padding:11px 13px;border-radius:10px;border:1px solid #2b3a5c;background:#0a1226;color:#e8eefc;font-size:15px;margin-bottom:10px;">');
    app.appendChild(srch);
    var _hp={f:"vse",data:[]};
    var pane=el('<div style="display:flex;gap:10px;height:calc(62vh - 86px);align-items:stretch;">'
      +'<div style="flex:1;min-width:0;overflow-y:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none;border:1px solid var(--bord);border-radius:12px;background:rgba(255,255,255,0.02);padding:2px 8px;"><ul id="hpList" style="padding:0;list-style:none;margin:0;"></ul></div>'
      +'<div id="hpRail" style="width:72px;flex:none;overflow-y:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none;display:flex;flex-direction:column;gap:7px;padding:0;"></div></div>');
    app.appendChild(pane);
    function _hpLetter(p){ var c=((p.jmeno||"").trim().charAt(0)||"#").toUpperCase();
      return c.replace(/[ÁÄ]/,'A').replace(/[ČC]/,'C').replace(/[ĎD]/,'D').replace(/[ÉĚE]/,'E').replace(/Í/,'I').replace(/[ŇN]/,'N').replace(/[ÓÖ]/,'O').replace(/[ŘR]/,'R').replace(/[ŠS]/,'S').replace(/[ŤT]/,'T').replace(/[ÚŮÜU]/,'U').replace(/[ÝY]/,'Y').replace(/[ŽZ]/,'Z'); }
    function _hpPass(p,k){ k=k||_hp.f; if(k==="vse")return true; return _hpLetter(p)===k;
    }
    function _hpRailBtn(letter,key){
      var on=(_hp.f===key); var c=(key==="vse")?_hp.data.length:_hp.data.filter(function(p){return _hpPass(p,key);}).length;
      var bdg=(c>0&&key!=="vse")?'<span style="position:absolute;top:4px;right:6px;min-width:16px;height:16px;line-height:14px;border-radius:8px;background:var(--green);color:#241a02;font-size:9.5px;font-weight:700;padding:0 2px;box-sizing:border-box;text-align:center;">'+c+'</span>':'';
      var b=el('<button style="position:relative;width:100%;box-sizing:border-box;margin:0;padding:10px 2px;font-size:18px;font-weight:700;display:flex;align-items:center;justify-content:center;border:1px solid '+(on?"var(--green)":"var(--bord)")+';background:'+(on?"var(--green)":"rgba(255,255,255,0.02)")+';color:'+(on?"#04150e":"var(--mut)")+';border-radius:12px;cursor:pointer;">'+letter+bdg+'</button>');
      b.addEventListener("click",function(){ _hp.f=key; render(); });
      return b;
    }
    function render(){
      var rail=document.getElementById("hpRail"), ul=document.getElementById("hpList");
      if(!rail||!ul) return;
      rail.innerHTML=""; rail.appendChild(_hpRailBtn("∗","vse"));
      var letters={}; _hp.data.forEach(function(p){ letters[_hpLetter(p)]=1; });
      Object.keys(letters).sort().forEach(function(L){ rail.appendChild(_hpRailBtn(L,L)); });
      ul.innerHTML="";
      var arr=_hp.data.filter(function(p){return _hpPass(p);});
      if(!arr.length){ ul.appendChild(el('<li style="border:none;color:var(--mut);">Nikdo nenalezen.</li>')); return; }
      arr.forEach(function(p){
        var ini=((p.jmeno||"?").trim().charAt(0)||"?").toUpperCase();
        var li=el('<li style="border:none;display:flex;align-items:center;gap:12px;padding:9px 4px;border-bottom:1px solid #1b2742;cursor:pointer;"></li>');
        li.appendChild(el('<div style="width:38px;height:38px;border-radius:50%;background:'+avColor(p.jmeno)+';color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:16px;flex:0 0 auto;">'+esc(ini)+'</div>'));
        li.appendChild(el('<div style="flex:1;min-width:0;"><div style="font-weight:600;">'+esc(p.jmeno)+'</div>'+(p.mesto?'<div class="hint">'+esc(p.mesto)+'</div>':'')+'</div>'));
        li.appendChild(el('<div class="chev" style="color:#5a6;">&#8250;</div>'));
        li.addEventListener("click",function(){ window._hrUid=p.user_id; window._hrName=p.jmeno; go("hr_person"); });
        ul.appendChild(li);
      });
    }
    function load(q){
      var ul=document.getElementById("hpList"); if(ul) ul.innerHTML='<li style="border:none;color:var(--mut);">Načítám…</li>';
      api("GET","/api/v1/erp/app/hr/people"+(q?("?q="+encodeURIComponent(q)):""),"").then(function(j){
        if(!j||!j.ok){ if(ul) ul.innerHTML='<li style="border:none;color:var(--mut);">'+esc((j&&j.error==="forbidden")?"Nemáš přístup (jen HR / vedení).":"Nelze načíst.")+'</li>'; return; }
        _hp.data=j.lide||[]; _hp.f="vse"; render();
      });
    }
    var _td=null; srch.addEventListener("input",function(){ clearTimeout(_td); _td=setTimeout(function(){ load(srch.value.trim()); },250); });
    load("");
  }
  function hr_rezimy(){
    app.innerHTML=topbar("🧩 Režimy docházky", true);
    var srch=el('<input type="text" placeholder="Hledat jméno…" style="width:100%;box-sizing:border-box;padding:11px 13px;border-radius:10px;border:1px solid #2b3a5c;background:#0a1226;color:#e8eefc;font-size:15px;margin-bottom:10px;">');
    app.appendChild(srch);
    app.appendChild(el('<div class="hint" style="margin-bottom:8px;line-height:1.5;">Forma a režim jsou nezávislé. Píchají všichni; režim řeší jen odměnu/řízení. Člověk může mít víc záznamů (firmy/formy/tenanty).</div>'));
    var FORMY=[["HPP","HPP"],["DPP","DPP"],["OSVC","OSVČ"]];
    var REZIMY=[["hodinovy","Hodinový"],["volny","Volný"],["pausal","Paušál"]];
    var addBtn=el('<button class="ghost full" style="margin-bottom:10px;border-color:var(--blue);color:var(--blue);">➕ Přidat angažmá (další firma / forma / tenant)</button>');
    var addBox=el('<div style="display:none;border:1px solid var(--blue);border-radius:12px;padding:12px;margin-bottom:12px;"></div>');
    addBtn.addEventListener("click",function(){ if(addBox.style.display==='none'){ addBox.style.display='block'; buildAdd(addBox); } else { addBox.style.display='none'; } });
    app.appendChild(addBtn); app.appendChild(addBox);
    var _rz={f:"vse",data:[]};
    var pane=el('<div style="display:flex;gap:10px;height:calc(58vh - 86px);align-items:stretch;">'
      +'<div style="flex:1;min-width:0;overflow-y:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none;border:1px solid var(--bord);border-radius:12px;background:rgba(255,255,255,0.02);padding:2px 8px;"><ul id="rezList" style="padding:0;list-style:none;margin:0;"></ul></div>'
      +'<div id="rezRail" style="width:72px;flex:none;overflow-y:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none;display:flex;flex-direction:column;gap:7px;padding:0;"></div></div>');
    app.appendChild(pane);
    function _rzRailBtn(icon,label,key){
      var on=(_rz.f===key);
      var c=(key==="vse")?_rz.data.length:_rz.data.filter(function(p){ return _rzPass(p,key); }).length;
      var bdg=(c>0)?'<span style="position:absolute;top:4px;right:6px;min-width:17px;height:17px;line-height:15px;border-radius:9px;border:1px solid rgba(0,0,0,.25);background:var(--green);color:#241a02;font-size:10px;font-weight:700;padding:0 3px;box-sizing:border-box;text-align:center;">'+c+'</span>':'';
      var b=el('<button style="position:relative;width:100%;box-sizing:border-box;margin:0;padding:11px 2px;font-size:10.5px;line-height:1.15;display:flex;flex-direction:column;align-items:center;gap:4px;border:1px solid '+(on?"var(--green)":"var(--bord)")+';background:'+(on?"var(--green)":"rgba(255,255,255,0.02)")+';color:'+(on?"#04150e":"var(--mut)")+';border-radius:13px;cursor:pointer;"><span style="font-size:24px;line-height:1;">'+icon+'</span>'+label+bdg+'</button>');
      b.addEventListener("click",function(){ _rz.f=key; render(); });
      return b;
    }
    function _rzPass(p,k){ k=k||_rz.f;
      if(k==="vse")return true;
      if(k==="2"||k==="14")return String(p.tenant_id)===k;
      if(k==="konto")return !!p.konto_aktivni;
      return p.forma===k; }
    function buildAdd(box){
      box.innerHTML='<div class="hint">Načítám lidi…</div>';
      api("GET","/api/v1/erp/app/hr/people","").then(function(j){
        var ps=''; ((j&&j.lide)||[]).forEach(function(p){ ps+='<option value="'+p.user_id+'">'+esc(p.jmeno)+'</option>'; });
        var w=el('<div></div>');
        w.innerHTML='<label class="hint" style="display:block;margin:2px 0 2px;">Osoba</label>'
          +'<select style="width:100%;padding:9px;border-radius:9px;border:1px solid #2b3a5c;background:#0a1226;color:#e8eefc;">'+ps+'</select>'
          +sel("Firma / tenant",[["2","EUROSOFT"],["14","INTERSOFT"]],"2")
          +sel("Právní forma",FORMY,"OSVC")+sel("Mzdový režim",REZIMY,"hodinovy");
        var sa=w.querySelectorAll("select");
        var b=el('<button class="green full" style="margin-top:10px;">Vytvořit angažmá</button>');
        var st=el('<div class="hint" style="margin-top:6px;"></div>');
        b.addEventListener("click",function(){ b.disabled=true; st.textContent="Vytvářím…";
          api("POST","/api/v1/erp/app/hr/rezim/add",{user_id:parseInt(sa[0].value),tenant_id:parseInt(sa[1].value),
            forma:sa[2].value,mzdovy:sa[3].value}).then(function(r){
              b.disabled=false; st.textContent=(r&&r.ok)?"✅ Přidáno":("✗ "+((r&&r.error)||"chyba"));
              if(r&&r.ok){ setTimeout(function(){ addBox.style.display='none'; load(srch.value.trim()); },700); }
            }); });
        w.appendChild(b); w.appendChild(st); box.innerHTML=""; box.appendChild(w);
      });
    }
    var VOLBY=[["na_vyber","Na výběr"],["premie","Do prémie"],["prescas","Do přesčasu"],["prevest","Převést"]];
    function chip(t,c){ return '<span style="background:'+c+';color:#04150e;border-radius:8px;padding:2px 7px;font-size:11px;font-weight:700;">'+esc(t)+'</span>'; }
    function sel(label,opts,val){ var s='<label class="hint" style="display:block;margin:6px 0 2px;">'+label+'</label><select style="width:100%;padding:9px;border-radius:9px;border:1px solid #2b3a5c;background:#0a1226;color:#e8eefc;">';
      opts.forEach(function(o){ s+='<option value="'+o[0]+'"'+(o[0]===val?' selected':'')+'>'+esc(o[1])+'</option>'; }); return s+'</select>'; }
    function numf(label,val){ return '<label class="hint" style="display:block;margin:6px 0 2px;">'+label+'</label><input type="number" step="0.5" value="'+(val||0)+'" style="width:100%;box-sizing:border-box;padding:9px;border-radius:9px;border:1px solid #2b3a5c;background:#0a1226;color:#e8eefc;">'; }
    function buildEdit(box,p){
      var w=el('<div></div>');
      w.innerHTML=sel("Právní forma",FORMY,p.forma)+sel("Mzdový režim",REZIMY,p.mzdovy)
        +numf("Loajalita — manko do minusu (h/měs)",p.loajalita_minus_h)
        +numf("Přesčas-polštář neproplácený (h/den)",p.prescas_plus_h_den)
        +numf("Paušál (Kč/měs, jen režim paušál)",p.pausal_kc)
        +'<label class="hint" style="display:flex;align-items:center;gap:8px;margin:10px 0 2px;"><input type="checkbox" '+(p.konto_aktivni?'checked':'')+'> Konto přesčasů aktivní</label>'
        +sel("Default dispozice konta",VOLBY,p.konto_volba)
        +numf("Příplatek za přesčas (%)",p.prescas_priplatek_pct);
      var sels=w.querySelectorAll("select"), nums=w.querySelectorAll("input[type=number]"), chk=w.querySelector("input[type=checkbox]");
      var btn=el('<button class="green full" style="margin-top:10px;">Uložit</button>');
      var st=el('<div class="hint" style="margin-top:6px;"></div>');
      btn.addEventListener("click",function(){ btn.disabled=true; st.textContent="Ukládám…";
        api("POST","/api/v1/erp/app/hr/rezim/save",{emp_id:p.emp_id,
          forma:sels[0].value, mzdovy:sels[1].value, konto_volba:sels[2].value,
          loajalita_minus_h:parseFloat(nums[0].value)||0, prescas_plus_h_den:parseFloat(nums[1].value)||0,
          pausal_kc:parseFloat(nums[2].value)||0, prescas_priplatek_pct:parseFloat(nums[3].value)||0,
          konto_aktivni:chk.checked}).then(function(r){
            btn.disabled=false; st.textContent=(r&&r.ok)?"✅ Uloženo":("✗ "+((r&&r.error)||"chyba")); if(r&&r.ok) setTimeout(function(){ load(srch.value.trim()); },600);
          });
      });
      w.appendChild(btn); w.appendChild(st); box.appendChild(w);
    }
    function render(){
      var rail=document.getElementById("rezRail"), ul=document.getElementById("rezList");
      if(!rail||!ul) return;
      rail.innerHTML="";
      [["📋","Vše","vse"],["🟢","HPP","HPP"],["🟣","DPP","DPP"],["🟠","OSVČ","OSVC"],["🏢","EUR","2"],["🏬","INT","14"],["🏦","Konto","konto"]].forEach(function(it){
        if(it[2]==="vse"||_rz.data.filter(function(p){return _rzPass(p,it[2]);}).length>0) rail.appendChild(_rzRailBtn(it[0],it[1],it[2]));
      });
      ul.innerHTML="";
      var arr=_rz.data.filter(function(p){return _rzPass(p);});
      if(!arr.length){ ul.appendChild(el('<li style="border:none;color:var(--mut);">Nikdo.</li>')); return; }
      arr.forEach(function(p){
        var fc=(p.forma==='OSVC')?'#f59e0b':(p.forma==='DPP'?'#a78bfa':'#34d399');
        var rc=(p.mzdovy==='volny')?'#60a5fa':(p.mzdovy==='pausal'?'#a78bfa':'#34d399');
        var rez={hodinovy:'Hodinový',volny:'Volný',pausal:'Paušál'}[p.mzdovy]||p.mzdovy;
        var forma={HPP:'HPP',DPP:'DPP',OSVC:'OSVČ'}[p.forma]||p.forma;
        var firmaLbl=p.firma||(p.tenant_id===14?'INTERSOFT':(p.tenant_id===2?'EUROSOFT':''));
        var li=el('<li class="ct" style="border:none;border-bottom:1px solid #1b2742;padding:0;"></li>');
        var head=el('<div style="display:flex;align-items:center;gap:10px;cursor:pointer;padding:9px 4px;"></div>');
        head.appendChild(el('<div style="flex:1;min-width:0;"><div style="font-weight:600;">'+esc(p.jmeno)+(firmaLbl?(' <span class="hint">· '+esc(firmaLbl)+'</span>'):'')+'</div><div style="margin-top:4px;display:flex;gap:5px;flex-wrap:wrap;">'+chip(forma,fc)+chip(rez,rc)+(p.tenant_id===14?chip('INTERSOFT','#60a5fa'):'')+(p.konto_aktivni?chip('konto','#fbbf24'):'')+'</div></div>'));
        head.appendChild(el('<div class="chev" style="color:#5a6;">&#8250;</div>'));
        var ed=el('<div class="ctexp" style="display:none;padding:0 4px 10px;"></div>');
        head.addEventListener("click",function(){
          var open=li.classList.toggle("open"); ed.style.display=open?"block":"none";
          if(open && ed.dataset.built!=='1'){ buildEdit(ed,p); ed.dataset.built='1'; }
          _railSync("rezRail","rezList");
        });
        li.appendChild(head); li.appendChild(ed); ul.appendChild(li);
      });
      _railSync("rezRail","rezList");
    }
    function load(q){
      var ul=document.getElementById("rezList"); if(ul) ul.innerHTML='<li style="border:none;color:var(--mut);">Načítám…</li>';
      api("GET","/api/v1/erp/app/hr/rezimy"+(q?("?q="+encodeURIComponent(q)):""),"").then(function(j){
        if(!j||!j.ok){ if(ul) ul.innerHTML='<li style="border:none;color:var(--mut);">'+esc((j&&j.error==="forbidden")?"Nemáš přístup (jen HR / vedení).":"Nelze načíst.")+'</li>'; return; }
        _rz.data=j.lide||[]; render();
      });
    }
    var _td=null; srch.addEventListener("input",function(){ clearTimeout(_td); _td=setTimeout(function(){ load(srch.value.trim()); },250); });
    load("");
  }
