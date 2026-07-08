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
    g1.appendChild(appCell("🪪","Karta zaměstnance",0,function(){go("hr_people");}));
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
    l3.appendChild(row("🪪","Karta zaměstnance","Karta člověka: režim · podmínky · docházka",function(){ go("hr_people"); }));
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
