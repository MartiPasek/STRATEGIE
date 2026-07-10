  function apps(){
    app.innerHTML=topbar("", false, true);
    var bd=getBadges()||{whatsapp:0,sms:0,access:true};
    var g=el('<div class="appgrid"></div>');
    // Marti 7.6.: S ERP ikona = „STRATEGIE" → spouští ERP; S CHAT ikona = „Tvoje Marti" → spouští chat.
    // /erp/ S LOMÍTKEM — jinak URL nespadá do scope ERP PWA a Android otevře chat PWA (S CHAT splash).
    g.appendChild(appCell("🌐","Web",0,function(){ openApp("/web"); }));
    g.appendChild(appCell('<img src="/static/erp/icon-erp-192.png">',"STRATEGIE",0,function(){openApp("/erp/");}));
    g.appendChild(appCell('<img src="/static/erp/icon-chat-192.png">',"Tvoje Marti",0,function(){openApp("/");}));
    g.appendChild(appCell("🤝","Spolupráce",0,function(){go("dochazka");}));
    g.appendChild(appCell("❓","Nápověda docházka",0,function(){ dochHelp(); }));   // Jirka 26.6.: rychlý návod docházky ze seznamu aplikací
    // Marti 9.6.: vše ze složky Firma = aplikace. Výroba + její seznamy jako ikony,
    // řízení (Vedení) jako složka. Deep-link otevře Výrobu rovnou na daném seznamu.
    app.appendChild(g);  // základ: hlavní launchery nahoře (bez nadpisu)
    // Marti 1.7.2026 — member RO rozcestník: citlivé sekce (finance/HR/řízení/systém/AI)
    // se vykreslí JEN podle role (příznaky z /app/cockpit/access: fin/parent/vp).
    // Běžný člen (member) vidí bohaté provozní a týmové přehledy (RO), ne účetní jádro.
    function sec(t){ app.appendChild(el('<div style="margin:16px 6px 6px;font-size:12px;font-weight:700;letter-spacing:.5px;color:#7c8cdb;">'+t+'</div>')); }
    function grp(){ var gg=el('<div class="appgrid"></div>'); app.appendChild(gg); return gg; }
    function buildApps(ac){
      ac=ac||{}; var fin=!!ac.fin, par=!!ac.parent, vp=!!ac.vp; var uid=ac.uid||0;
      var isMember=!fin&&!par&&!vp; var gg;
      if(isMember){
        app.appendChild(el('<div style="margin:12px 4px 2px;background:linear-gradient(110deg,rgba(45,212,191,.10),rgba(96,165,250,.06));border:1px solid var(--bord);border-radius:14px;padding:12px 14px;font-size:13.5px;line-height:1.5;color:var(--mut);">👋 <b style="color:var(--tx);">Vítej!</b> Tady vidíš, co se ve firmě děje — kdo na čem dělá, kapacity dílny, zakázky i dokumentace. Klidně se rozhlédni.</div>'));
      }
      sec("🧑 MOJE"); gg=grp();
      gg.appendChild(appCell("🧰","Moje činnosti",0,function(){go("moje_cinnosti");}));
      gg.appendChild(appCell("🪪","Moje osobní údaje",0,function(){go("hr_me");}));
      gg.appendChild(appCell("📥","Zadat úkol",0,function(){ go("fronta"); }));
      sec("🏭 VÝROBA & OBCHOD"); gg=grp();
      gg.appendChild(appCell("🏭","Výroba",0,function(){go("vyroba_hub");}));
      if(vp) gg.appendChild(appCell("👔","VP",0,function(){openVyroba("vp");}));
      if(uid===1||uid===11||uid===34) gg.appendChild(appCell("🗼","VP věž",0,function(){openInApp("/vp-vez");}));
      gg.appendChild(appCell("🧪","Zkušebna",0,function(){openVyroba("zkusebna");}));
      gg.appendChild(appCell("📊","FLOW",0,function(){openInApp("/flow");}));
      gg.appendChild(appCell("📈","Vytížení",0,function(){openInApp("/vytizeni");}));
      gg.appendChild(appCell("🔋","Vytížení dílny",0,function(){openInApp("/vytizeni-prehled");}));
      gg.appendChild(appCell("📞","Plán hovorů",0,function(){openInApp("/crm-plan-hovoru");}));
      gg.appendChild(appCell("📥","Poptávky",0,function(){go("poptavka");}));
      gg.appendChild(appCell("🤖","SW zakázky",0,function(){go("sw_zakazky");}));
      sec("🛒 NÁKUP & SKLAD"); gg=grp();
      gg.appendChild(appCell("🛒","Nákup (výroba)",0,function(){openVyroba("nakup");}));
      gg.appendChild(appCell("🛒","Nákup",0,function(){openInApp("/nakup");}));
      gg.appendChild(appCell("🛒","Co objednat",0,function(){openInApp("/objednavky");}));
      if(fin){
        sec("🏦 FINANCE & ÚČETNICTVÍ"); gg=grp();
        gg.appendChild(appCell("💰","Finance",0,function(){openInApp("/finance");}));
        gg.appendChild(appCell("🏦","Banka",0,function(){openInApp("/banka");}));
        gg.appendChild(appCell("💸","Platby",0,function(){openInApp("/platby");}));
        gg.appendChild(appCell("🔌","Bank. napojení",0,function(){openInApp("/banka-napojeni");}));
        gg.appendChild(appCell("🧾","Účetní deník",0,function(){openInApp("/denik");}));
        gg.appendChild(appCell("📊","Předvaha",0,function(){openInApp("/predvaha");}));
        gg.appendChild(appCell("💰","Mzdy & odvody",0,function(){openInApp("/mzdy");}));
        gg.appendChild(appCell("🧾","Přefakturace",0,function(){go("prefakturace");}));
        gg.appendChild(appCell("📒","Účetní",0,function(){ _auMode="helios"; go("alluser"); }));
        sec("📨 ČSSZ & COMPLIANCE"); gg=grp();
        gg.appendChild(appCell("📨","Datovky / ČSSZ",0,function(){go("isds");}));
        gg.appendChild(appCell("🤒","Neschopenky",0,function(){openInApp("/neschopenky?typ=nemoc");}));
        gg.appendChild(appCell("🧑‍⚕️","Ošetřovné (OČR)",0,function(){go("ocr");}));
        gg.appendChild(appCell("📤","Dávky ČSSZ",0,function(){openInApp("/davky");}));
        gg.appendChild(appCell("🛡️","Audit dávek",0,function(){openInApp("/audit-davky");}));
        gg.appendChild(appCell("🛡️","ISO 27001",0,function(){openInApp("/iso");}));
        sec("🔌 EDI"); gg=grp();
        gg.appendChild(appCell("📊","Statistika EDI",0,function(){openInApp("/edi-stat");}));
        gg.appendChild(appCell("🧩","EDI definice",0,function(){openInApp("/edi-definice");}));
        sec("🧑‍💼 HR & LIDÉ"); gg=grp();
        gg.appendChild(appCell("📺","HR přehled",0,function(){openInApp("/hr-modul");}));
        gg.appendChild(appCell("💰","Finanční podmínky 🔒",0,function(){openInApp("/finance-podminky");}));
        gg.appendChild(appCell("🔒","HR",0,function(){go("hr_hub");}));
        gg.appendChild(appCell("🗂️","Vedení",0,function(){go("vedeni");}));
        gg.appendChild(appCell("✍️","Podpisy smluv",(_signPend||0),function(){openInApp("/podpisy");}));
      }
      sec("👥 TÝM & PŘEHLEDY"); gg=grp();
      gg.appendChild(appCell("👀","Kdo kde dnes",0,function(){go("kdekdo");}));
      gg.appendChild(appCell("👥","Skupiny",0,function(){go("skupiny");}));
      gg.appendChild(appCell("🏖️","Plán absencí",0,function(){openInApp("/absence-plan");}));
      gg.appendChild(appCell("⚡","Výuka",0,function(){go("uceni");}));
      gg.appendChild(appCell("🪞","Zrcadla",0,function(){openInApp("/zrcadla");}));  // RO všem; spouštění gated backend
      gg.appendChild(appCell("📚","Dokumentace",0,function(){openInApp("/dokument");}));
      if(par){
        sec("🏛️ ŘÍZENÍ & SYSTÉM"); gg=grp();
        gg.appendChild(appCell("🌐","Uživatelé",0,function(){ _auMode="users"; go("alluser"); }));
        gg.appendChild(appCell("⚙️","Ops akce",0,function(){go("ops");}));
        gg.appendChild(appCell("🔀","Migrace",0,function(){go("migrace");}));
        gg.appendChild(appCell("🗂️","Digitalizace",0,function(){openInApp("/digitalizace");}));
        gg.appendChild(appCell("🟩","Záloha",0,function(){openInApp("/zaloha-status");}));  // blue-green API B stav
        sec("🤖 AI & KOMUNIKACE"); gg=grp();
        gg.appendChild(appCell("🤖","Claude-27",0,function(){go("claude27");}));
        gg.appendChild(appCell("🕸️","Síť Claudů",0,function(){go("coord");}));
        gg.appendChild(appCell("📲","Sdílený telefon",0,function(){go("sdileny");}));
        gg.appendChild(appCell("⏰","Buzení Marti-AI",0,function(){openInApp("/ai-buzeni");}));
        gg.appendChild(appCell("💰","Co AI ušetřila",0,function(){openInApp("/ai-uspora");}));
      }
      sec("🔗 NÁSTROJE"); gg=grp();
      gg.appendChild(appCell("📧","Napojit e-mail",0,function(){openInApp("/pripojit-schranku");}));
      gg.appendChild(appCell("🧲","Teamio",0,function(){ openApp("https://my.teamio.com"); }));
      app.appendChild(el('<div style="height:200px;"></div>'));
    }
    api("GET","/api/v1/erp/app/cockpit/access","").then(function(j){ buildApps(j&&j.ok?j:{}); }).catch(function(){ buildApps({}); });
  }
  // Marti 9.6.: složka „Vedení" v Aplikacích — řídicí agendy. Příprava/Odvozy/
  // Zakázky deep-link do Výroby; IT/PLC/HR zatím placeholder „Připravujeme".
  // Marti 13.6.: cockpit „Vedení firmy" — sjednocující pohled, který spojuje živé
  // moduly do jednoho celku (lidé, personalistika, obchod/výroba, řízení) + KPI strip.
  function vedeni(){
    app.innerHTML=topbar("🏛️ Vedení firmy", true);
    var kpi=el('<div id="vfKpi" style="display:flex;gap:8px;margin:4px 2px 6px;"></div>');
    app.appendChild(kpi);
    var _p=null,_t=null,_n=null;
    function kc(lbl,val,col){ return '<div style="flex:1;background:rgba(255,255,255,.03);border:1px solid var(--bord);border-radius:12px;padding:10px 6px;text-align:center;"><div style="font-size:22px;font-weight:800;color:'+col+';">'+(val==null?"…":val)+'</div><div style="font-size:10.5px;color:var(--mut);line-height:1.2;margin-top:2px;">'+lbl+'</div></div>'; }
    function drawKpi(){ kpi.innerHTML=kc("V práci dnes",_p,"var(--green)")+kc("Sledováno lidí",_t,"#60a5fa")+kc("Nábor — kandidáti",_n,"#a78bfa"); }
    drawKpi();
    var d=new Date(), _isod=d.getFullYear()+"-"+("0"+(d.getMonth()+1)).slice(-2)+"-"+("0"+d.getDate()).slice(-2);
    api("GET","/api/v1/erp/app/attendance/whereabouts?den="+_isod,"").then(function(j){ var L=(j&&j.ok&&j.lide)||[]; _t=L.length; _p=L.filter(function(x){return x.kind==="prace";}).length; drawKpi(); });
    api("GET","/api/v1/erp/app/recruit/pipeline","").then(function(j){ if(j&&j.ok){ _n=j.candidates; drawKpi(); } });
    var aiP=el('<div style="margin:8px 2px 2px;background:linear-gradient(110deg,rgba(45,212,191,.1),rgba(96,165,250,.06));border:1px solid var(--bord);border-radius:14px;padding:12px;"></div>');
    aiP.innerHTML='<div style="font-weight:800;display:flex;align-items:center;gap:7px;margin-bottom:4px;">🧠 Marti-AI hlídá <span style="font-size:11px;color:var(--mut);font-weight:600;">živě</span></div><div id="aiIns" style="font-size:13.5px;color:var(--mut);">Dívám se na to…</div>';
    app.appendChild(aiP);
    api("GET","/api/v1/erp/app/cockpit/insights","").then(function(j){
      var b=document.getElementById("aiIns"); if(!b) return;
      if(!j||!j.ok){ b.textContent=(j&&j.error==="forbidden")?"Přehled vidí jen rodiče.":"—"; return; }
      b.innerHTML=""; (j.items||[]).forEach(function(it){
        var col=it.sev==="warn"?"#fbbf24":(it.sev==="ok"?"#34d399":"var(--tx)");
        var r=el('<div style="display:flex;gap:8px;align-items:center;padding:6px 0;'+(it.go?'cursor:pointer;':'')+'"><span style="font-size:17px;">'+it.icon+'</span><span style="flex:1;color:'+col+';line-height:1.3;">'+esc(it.text)+'</span>'+(it.go?'<span style="color:var(--mut);">›</span>':'')+'</div>');
        if(it.go) r.addEventListener("click",function(){ go(it.go); });
        b.appendChild(r);
      });
    });
    function sec(t){ app.appendChild(el('<div style="margin:14px 6px 6px;font-size:12px;font-weight:700;letter-spacing:.5px;color:#7c8cdb;">'+t+'</div>')); }
    sec("LIDÉ & DOCHÁZKA");
    var g1=el('<div class="appgrid"></div>');
    g1.appendChild(appCell("👀","Kdo kde dnes",0,function(){go("kdekdo");}));
    g1.appendChild(appCell("📅","Plán",0,function(){go("plan");}));
    g1.appendChild(appCell("🗓️","Absence",0,function(){go("absence");}));
    app.appendChild(g1);
    sec("PERSONALISTIKA");
    var g2=el('<div class="appgrid"></div>');
    g2.appendChild(appCell("🔒","HR",0,function(){go("hr_hub");}));
    g2.appendChild(appCell("🧲","Nábor",0,function(){go("hr_nabor");}));
    g2.appendChild(appCell("📊","Produktivita",0,function(){go("kara");}));
    app.appendChild(g2);
    sec("OBCHOD & VÝROBA");
    var g3=el('<div class="appgrid"></div>');
    g3.appendChild(appCell("🧾","Zakázky",0,function(){openVyroba("zakazky");}));
    g3.appendChild(appCell("🔧","Příprava",0,function(){openVyroba("priprava");}));
    g3.appendChild(appCell("🚚","Odvozy",0,function(){openVyroba("odvozy");}));
    g3.appendChild(appCell("📈","Vytížení montérů",0,function(){openInApp("/vytizeni");}));
    app.appendChild(g3);
    sec("ŘÍZENÍ & MZDY");
    var g4=el('<div class="appgrid"></div>');
    g4.appendChild(appCell("💰","Mzdy: Helios × my",0,function(){go("wage_cmp");}));
    g4.appendChild(appCell("📈","Návštěvnost webu",0,function(){go("web_stats");}));
    g4.appendChild(appCell("⚙️","Ops akce",0,function(){go("ops");}));
    g4.appendChild(appCell("💻","IT",0,function(){openSoon("IT");}));
    g4.appendChild(appCell("🎛️","PLC",0,function(){openSoon("PLC");}));
    app.appendChild(g4);
    // 🟩 Záloha (blue-green API B) — kompaktní stav; klik otevře plnou stránku s tlačítkem „Povýšit". Jen rodič (endpoint gated).
    sec("🟩 ZÁLOHA (BLUE-GREEN)");
    var zbox=el('<div style="margin:2px 2px;background:rgba(255,255,255,.03);border:1px solid var(--bord);border-radius:12px;padding:11px 13px;font-size:13px;color:var(--mut);cursor:pointer;">Načítám stav zálohy…</div>');
    zbox.addEventListener("click",function(){ openInApp("/zaloha-status"); });
    app.appendChild(zbox);
    api("GET","/api/v1/erp/app/ops/secondary-info","").then(function(d){
      if(!d||d.ok===false){ zbox.style.display="none"; return; }   // nedostupné pro ne-rodiče → skryj
      var a=d.a||{}, b=d.b||{}, aRun=a&&a.ok!==false, bRun=b&&b.ok!==false;
      // „aktuální" = shoda mtime router.py v obou složkách (stejná definice jako /zaloha-status)
      var cur=!!(d.code_primary&&d.code_prev&&d.code_primary===d.code_prev)&&aRun&&bRun;
      var badge=cur?'<span style="color:#34d399;font-weight:800;">✅ Aktuální</span>'
        :'<span style="color:#fbbf24;font-weight:800;">⚠️ Pozadu</span>';
      zbox.innerHTML='<div style="display:flex;justify-content:space-between;align-items:center;gap:8px;">'
        +'<div><b style="color:var(--tx);">🟩 Záloha API‑B</b> <span style="font-size:11px;">(blue‑green)</span><br>'
        +'<span style="font-size:11.5px;">kód B: '+esc(d.code_prev||"?")+' · A: '+esc(d.code_primary||"?")
        +(d.pending?' · <span style="color:#a9caff;">⏳ probíhá</span>':'')+'</span></div>'
        +'<div style="text-align:right;white-space:nowrap;">'+badge
        +'<br><span style="color:#60a5fa;font-size:12px;">otevřít →</span></div></div>';
    }).catch(function(){ zbox.style.display="none"; });
    sec("DOKUMENTY & ADRESÁŘE");
    var gDoc=el('<div class="appgrid"></div>');
    gDoc.appendChild(appCell("🗂️","Adresáře (správa)",0,function(){openInApp("/dir-admin");}));
    gDoc.appendChild(appCell("📁","Dokumenty",0,function(){openInApp("/files");}));
    app.appendChild(gDoc);
    sec("VÝUKA & ŠKOLENÍ");
    var g6=el('<div class="appgrid"></div>');
    g6.appendChild(appCell("⚡","Výuka — elektro & metoda",0,function(){go("uceni");}));
    app.appendChild(g6);
    sec("ŠKOLY & KRAJ");
    var g5=el('<div class="appgrid"></div>');
    g5.appendChild(appCell("🗓️","Rozvrh Nerudovka",0,function(){go("bk_rozvrh");}));
    g5.appendChild(appCell("🏫","Kraj — digitalizace škol",0,function(){openApp("/web/kraj");}));
    app.appendChild(g5);
    var apiInfo=el('<div style="margin:14px 6px 4px;font-size:11px;color:var(--mut);text-align:center;line-height:1.4;">API…</div>');
    app.appendChild(apiInfo);
    api("GET","/api/v1/api-info","").then(function(j){
      if(!j||!j.ok){ apiInfo.textContent=""; return; }
      var inst=j.instance||"?";
      var tag=inst==="secondary"?"B (záloha)":inst==="primary"?"A (primární)":("?"+" ("+esc(inst)+")");
      if(j.stale){ apiInfo.style.color="#f87171"; apiInfo.style.fontWeight="700";
        apiInfo.innerHTML="⚠ STARÝ SERVER — běžíš na "+tag+" / "+esc(j.dir||"")+" (build "+esc(j.commit||"?")+")<br>Obnov stránku nebo srovnej zálohu."; }
      else { apiInfo.style.color="var(--mut)"; apiInfo.style.fontWeight="400";
        apiInfo.innerHTML="Běžíš na: <b style='color:var(--tx)'>"+tag+"</b> · build "+(j.commit||"?")+" · port "+(j.port||"?"); }
    });
    app.appendChild(el('<div style="height:80px;"></div>'));
  }
  // ── Bakaláři Nerudovka — rozvrhové přehledy (čte ze zrcadla tenant 13). ──
  function _bkUrl(p){ var q=window._bkPO?("po="+encodeURIComponent(window._bkPO)):""; return q?(p+(p.indexOf("?")>=0?"&":"?")+q):p; }
