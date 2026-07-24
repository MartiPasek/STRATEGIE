  function contacts(){ app.innerHTML=topbar("", false, true); var p=el('<div class="panel" style="margin-top:4px;"></div>');
    if(!(B&&typeof B.getContacts==="function")){ p.appendChild(el('<div class="hint">Kontakty jsou nativní funkce — funguje v appce STRATEGIE.</div>')); app.appendChild(p); return; }
    // Zelené telefonní pole: vybraný kontakt → jeho velké číslo; klik na prázdné → nativní klávesnice.
    var drow=el('<div style="display:flex;gap:8px;align-items:stretch;margin-bottom:10px;"></div>');
    var dial=el('<div id="ctdial" style="flex:1;min-height:44px;background:#0d1828;border:1px solid var(--green);box-shadow:0 0 0 2px rgba(34,197,94,.18);border-radius:8px;padding:0 12px;font-size:15px;font-weight:600;cursor:pointer;display:flex;align-items:center;justify-content:flex-start;gap:8px;">'+PHONE_SVG+'<span id="ctdialtxt" style="color:var(--mut);">Vytáčení…</span></div>');
    dial.addEventListener("click",function(){ if(_dialNum){ doDial(_dialNum); } else if(B&&typeof B.openDialpad==="function"){ B.openDialpad(); } else { openApp("tel:"); } });
    var bHist=el('<button class="ghost" style="padding:0 13px;font-size:18px;" title="Historie volání">🕓</button>'); bHist.addEventListener("click",function(){ go("calllog"); });
    var bSmsH=el('<button class="ghost" style="padding:0 13px;font-size:18px;" title="Historie SMS">💬</button>'); bSmsH.addEventListener("click",function(){ openApp("sms:"); });
    drow.appendChild(dial); drow.appendChild(bHist); drow.appendChild(bSmsH); p.appendChild(drow);
    var bar=el('<div style="display:flex;gap:10px;align-items:stretch;"></div>');
    var s=el('<input id="ctsearch" placeholder="🔍 Hledat kontakt…" autocomplete="off" style="flex:1;border:1px solid var(--blue);background:#0d1828;box-shadow:0 0 0 2px rgba(79,142,247,.18);font-weight:600;">');
    s.addEventListener("input",renderContactsList);
    var allBtn=el('<button id="ctall" class="ghost" style="white-space:nowrap;padding:0 12px;font-size:13px;border-color:'+(_allContacts?'var(--green)':'var(--bord)')+';color:'+(_allContacts?'var(--green)':'var(--mut)')+';">'+(_allContacts?'☑':'☐')+' 👥 Vše</button>');
    allBtn.addEventListener("click",function(){
      _allContacts=!_allContacts; try{localStorage.setItem("stg_all_contacts",_allContacts?"1":"0");}catch(e){}
      allBtn.innerHTML=(_allContacts?'☑':'☐')+' 👥 Vše';
      allBtn.style.borderColor=_allContacts?'var(--green)':'var(--bord)'; allBtn.style.color=_allContacts?'var(--green)':'var(--mut)';
      var h=document.getElementById("ctHint"); if(h)h.innerHTML=_allContacts?'Zobrazeny <b>všechny</b> kontakty v telefonu.':'Jen kontakty s prefixem: <b>'+esc(getPrefixes())+'</b> (změna v Nastavení).';
      loadContacts();
    });
    bar.appendChild(s); bar.appendChild(allBtn); p.appendChild(bar);
    p.appendChild(el('<div class="hint" id="ctHint">'+(_allContacts?'Zobrazeny <b>všechny</b> kontakty v telefonu.':'Jen kontakty s prefixem: <b>'+esc(getPrefixes())+'</b> (změna v Nastavení).')+'</div>'));
    p.appendChild(el('<div class="list" style="padding:0 14px;margin-top:10px;"><ul id="ctlist"><li style="color:var(--mut);border:none;">Načítám…</li></ul></div>'));
    p.appendChild(el('<div style="height:120px;"></div>'));  // místo pod patičku + extra lišty (poslední kontakt nesmí zajíždět)
    app.appendChild(p); setDialNum(_dialNum); loadContacts(); }

  // ───── HISTORIE HOVORŮ ─────
  function loadCalllog(){ var ul=document.getElementById("cllist"); if(!ul)return; var j=bjson("getCallLog", getPrefixes());
    if(j&&j.need){ ul.innerHTML='<li style="border:none;"><div style="color:var(--mut);margin-bottom:8px;">Appka potřebuje přístup k protokolu hovorů.</div><button class="green sm" id="clperm">Povolit přístup</button></li>'; var pb=document.getElementById("clperm"); if(pb)pb.addEventListener("click",function(){bjson("getCallLog",getPrefixes());setTimeout(loadCalllog,700);}); return; }
    var list=(j&&j.calls)||[]; if(!list.length){ ul.innerHTML='<li style="color:var(--mut);border:none;">Žádné hovory s prefixem '+esc(getPrefixes())+'.</li>'; return; }
    // Stejná stylizace jako Kontakty (Marti 7.6.): avatar + jméno + accordion s akcemi.
    ul.innerHTML=""; list.forEach(function(c){
      var li=document.createElement("li"); li.className="ct"; li.style.padding="0"; li.style.borderBottom="none";
      var nm=c.name||c.number||"?";
      var av='<div class="cav" style="background:'+avColor(nm)+'">'+esc((nm.replace(/[^A-Za-zÀ-ž]/g,"").charAt(0)||"?").toUpperCase())+'</div>';
      var missed=(c.type===3); var tCl=missed?"var(--red)":"var(--mut)";
      var head=el('<div class="cthead">'+av+'<div style="flex:1;min-width:0;"><div class="ctname">'+esc(nm)+'</div>'
        +(c.name?('<div class="ctnum">'+esc(c.number||"")+'</div>'):"")
        +'<div class="ctnum" style="color:'+tCl+';">'+esc(fmtCall(c))+'</div></div></div>');
      var exp=el('<div class="ctexp" style="display:none;"><div class="ctacts"></div></div>');
      var acts=exp.querySelector(".ctacts");
      var bCall=el('<div class="cact call">'+PHONE_SVG_W+'</div>'); bCall.addEventListener("click",function(e){e.stopPropagation();doDial(c.number);});
      var bSms=el('<div class="cact sms" style="color:#fff;font-size:20px;">💬</div>'); bSms.addEventListener("click",function(e){e.stopPropagation();openApp("sms:"+(c.number||"").replace(/\s/g,""));});
      acts.appendChild(bCall); acts.appendChild(bSms);
      head.addEventListener("click",function(){
        ul.querySelectorAll("li.ct").forEach(function(o){ o.classList.remove("open"); var x=o.querySelector(".ctexp"); if(x)x.style.display="none"; });
        exp.style.display="block"; li.classList.add("open"); li.scrollIntoView({block:"nearest",behavior:"smooth"});
      });
      li.appendChild(head); li.appendChild(exp); ul.appendChild(li);
    }); }
  // ───── HISTORIE SMS (most getSmsLog, Marti 7.6.) ─────
  function fmtSms(s){ var t={1:"přijatá",2:"odeslaná",3:"koncept",4:"odchozí",5:"neodeslaná",6:"ve frontě"}[s.type]||"SMS"; var d=new Date(s.date); return t+" · "+d.toLocaleDateString("cs")+" "+d.toLocaleTimeString("cs",{hour:"2-digit",minute:"2-digit"}); }
  function loadSmslog(){ var ul=document.getElementById("smslist"); if(!ul)return; var j=bjson("getSmsLog", getPrefixes());
    if(j&&j.need){ ul.innerHTML='<li style="border:none;"><div style="color:var(--mut);margin-bottom:8px;">Appka potřebuje přístup ke zprávám SMS.</div><button class="green sm" id="smperm">Povolit přístup</button></li>'; var pb=document.getElementById("smperm"); if(pb)pb.addEventListener("click",function(){bjson("getSmsLog",getPrefixes());setTimeout(loadSmslog,700);}); return; }
    var list=(j&&j.sms)||[]; if(!list.length){ ul.innerHTML='<li style="color:var(--mut);border:none;">Žádné SMS s prefixem '+esc(getPrefixes())+'.</li>'; return; }
    ul.innerHTML=""; list.forEach(function(s){
      var li=document.createElement("li"); li.className="ct"; li.style.padding="0"; li.style.borderBottom="none";
      var nm=s.name||s.number||"?";
      var av='<div class="cav" style="background:'+avColor(nm)+'">'+esc((nm.replace(/[^A-Za-zÀ-ž]/g,"").charAt(0)||"?").toUpperCase())+'</div>';
      var head=el('<div class="cthead">'+av+'<div style="flex:1;min-width:0;"><div class="ctname">'+esc(nm)+'</div>'
        +'<div class="ctnum" style="color:var(--tx);opacity:.85;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">'+esc(s.body||"")+'</div>'
        +'<div class="ctnum">'+esc(fmtSms(s))+'</div></div></div>');
      var exp=el('<div class="ctexp" style="display:none;"><div style="color:var(--tx);font-size:13.5px;line-height:1.5;margin-bottom:10px;white-space:pre-wrap;">'+esc(s.body||"")+'</div><div class="ctacts"></div></div>');
      var acts=exp.querySelector(".ctacts");
      var bCall=el('<div class="cact call">'+PHONE_SVG_W+'</div>'); bCall.addEventListener("click",function(e){e.stopPropagation();doDial(s.number);});
      var bSms=el('<div class="cact sms" style="color:#fff;font-size:20px;">💬</div>'); bSms.addEventListener("click",function(e){e.stopPropagation();openApp("sms:"+(s.number||"").replace(/\s/g,""));});
      acts.appendChild(bCall); acts.appendChild(bSms);
      head.addEventListener("click",function(){
        ul.querySelectorAll("li.ct").forEach(function(o){ o.classList.remove("open"); var x=o.querySelector(".ctexp"); if(x)x.style.display="none"; });
        exp.style.display="block"; li.classList.add("open"); li.scrollIntoView({block:"nearest",behavior:"smooth"});
      });
      li.appendChild(head); li.appendChild(exp); ul.appendChild(li);
    }); }
  var _histMode="calls"; // přepínač Historie: hovory / SMS (Marti 7.6.)
  function calllog(){ app.innerHTML=topbar("", false, true); var p=el('<div class="panel"></div>');
    var hd=el('<div style="display:flex;align-items:center;gap:10px;margin-top:12px;"></div>');
    hd.appendChild(el('<span class="title">Historie</span>'));
    var bC=el('<button class="ghost sm">📞 Hovory</button>');
    var bS=el('<button class="ghost sm">💬 SMS</button>');
    hd.appendChild(bC); hd.appendChild(bS); p.appendChild(hd);
    var body=el('<div></div>'); p.appendChild(body);
    p.appendChild(el('<div style="height:120px;"></div>'));  // rezerva pod patičku
    app.appendChild(p);
    function paint(){
      var c=_histMode==="calls";
      bC.style.borderColor=c?"var(--blue)":"var(--bord)"; bC.style.color=c?"var(--blue)":"var(--mut)";
      bS.style.borderColor=!c?"var(--blue)":"var(--bord)"; bS.style.color=!c?"var(--blue)":"var(--mut)";
      if(c){
        if(!(B&&typeof B.getCallLog==="function")){ body.innerHTML='<div class="hint">Historie hovorů je nativní funkce — funguje v appce STRATEGIE.</div>'; return; }
        body.innerHTML='<div class="hint">Jen hovory kontaktů s prefixem: <b>'+esc(getPrefixes())+'</b>.</div><div class="list" style="padding:0 14px;margin-top:10px;"><ul id="cllist"><li style="color:var(--mut);border:none;">Načítám…</li></ul></div>';
        loadCalllog();
      } else {
        if(B&&typeof B.getSmsLog==="function"){
          body.innerHTML='<div class="hint">Jen SMS kontaktů s prefixem: <b>'+esc(getPrefixes())+'</b>.</div><div class="list" style="padding:0 14px;margin-top:10px;"><ul id="smslist"><li style="color:var(--mut);border:none;">Načítám…</li></ul></div>';
          loadSmslog();
        } else {
          body.innerHTML='<div class="hint" style="margin-top:12px;">Historie SMS vyžaduje novější verzi appky (aktualizace v Nastavení → O aplikaci). Zatím:</div>';
          var b=el('<button class="green sm" style="margin-top:8px;">💬 Otevřít Zprávy</button>');
          b.addEventListener("click",function(){openApp("sms:");}); body.appendChild(b);
        }
      }
    }
    bC.addEventListener("click",function(){_histMode="calls";paint();});
    bS.addEventListener("click",function(){_histMode="sms";paint();});
    paint(); }

  // ───── NASTAVENÍ ─────
  function clearAndReload(){
    (async function(){
      try{var rs=await navigator.serviceWorker.getRegistrations();for(var i=0;i<rs.length;i++){await rs[i].unregister();}}catch(e){}
      try{var ks=await caches.keys();for(var j=0;j<ks.length;j++){await caches.delete(ks[j]);}}catch(e){}
      try{sessionStorage.removeItem("stgAutoHeal");}catch(e){}
      try{location.replace(location.pathname+"?fresh="+Date.now());}catch(e){location.reload();}
    })();
  }
  function settings(){ app.innerHTML=topbar("Nastavení", false); var l=el('<div class="list"></div>');
    l.appendChild(row("🧹","Vyčistit a načíst","Načíst čerstvá data (když něco svítí staré)",function(){ clearAndReload(); }));
    l.appendChild(row("🟢","Párování s ERP","Stav spojení s ERP",function(){go("set_listen");}));
    l.appendChild(row("📌","Ikony na plochu","ERP a Chat zkratky",function(){go("set_icons");}));
    l.appendChild(row("📲","Nainstalovat na plochu","/mobile jako PWA",function(){go("set_install");}));
    l.appendChild(row("👥","Sdílený telefon","Více lidí na jednom mobilu — přepínání + PIN",function(){go("sdileny");}));
    if(native) l.appendChild(row("📞","Telefonní číslo","Číslo tohoto telefonu (ze SIM)",function(){go("set_phone");}));
    l.appendChild(row("🔤","Prefixy kontaktů a hovorů","Filtr (STR, EC)",function(){go("set_prefixes");}));
    l.appendChild(row("🔔","Přístup k oznámením","Počty WhatsApp / SMS",function(){go("set_notifaccess");}));
    l.appendChild(row("📷","Snímek obrazovky","Zmrazit, nakreslit a odeslat",function(){go("set_shot");}));
    l.appendChild(row("🆘","Nutně někoho sehnat","Urgentní upozornění s reakcí",function(){go("urgent");}));
    l.appendChild(row("🎭","Přihlásit jako (test)","Docházka za jiného usera — jen rodiče",function(){go("set_imp");}));
    if(native && B && typeof B.isSmsGateway==="function") l.appendChild(row("📨","SMS brána","Tento telefon přeposílá ověřovací SMS",function(){go("set_smsgw");}));
    l.appendChild(row("📱","Stav aplikací","Kdo má appku, verzi, jestli běží/pinguje (jen rodiče)",function(){go("dev_stav");}));
    l.appendChild(row("📨","Stav odeslaných SMS","Doručení + zda brána reálně poslala (jen rodiče)",function(){go("sms_stav");}));
    l.appendChild(row("🛠️","STRATEGIE — nástroje","Správa systému: obnova DB, testovací prostředí (jen rodiče)",function(){go("strategie_nastroje");}));
    l.appendChild(row("🧪","Vývojářské","DEV mód, most",function(){go("set_dev");}));
    l.appendChild(row("ℹ️","O aplikaci", _hasUpdate?"🆕 Nová verze k dispozici":(ver?("Verze "+ver):"Verze a stav"),function(){go("set_about");}, _hasUpdate?1:0));
    app.appendChild(l); }
  // Marti 16.6.: admin prostor pro rodiče — správa STRATEGIE (stejný template jako Vedení).
  function strategie_nastroje(){
    app.innerHTML=topbar("🛠️ STRATEGIE — nástroje", true);
    app.appendChild(el('<div class="hint" style="margin:8px 6px;line-height:1.6;">Správa STRATEGIE pro rodiče — provoz, obnova a testování systému. Domácí zázemí pro správu samotné platformy.</div>'));
    function sec(t){ app.appendChild(el('<div style="margin:14px 6px 6px;font-size:12px;font-weight:700;letter-spacing:.5px;color:#7c8cdb;">'+t+'</div>')); }
    sec("DATA & OBNOVA");
    var g1=el('<div class="appgrid"></div>');
    g1.appendChild(appCell("🗄️","Obnova DB do API D",0,function(){ go("apid_restore"); }));
    app.appendChild(g1);
  }
  function apid_restore(){
    app.innerHTML=topbar("🗄️ Obnova databáze do API D", true);
    app.appendChild(el('<div class="hint" style="margin:8px 6px;line-height:1.6;"><b>API D</b> = oddělené prostředí na <b>neživých datech</b>. Vyber zálohu a rozbal ji do API D — <b>produkce se nedotkne</b>. Pro obnovu (vytáhnout, co se rozbilo) i bezpečné testování.</div>'));
    var box=el('<div class="list"><div class="hint">Načítám zálohy…</div></div>'); app.appendChild(box);
    function load(){
      api("GET","/api/v1/erp/app/admin/apid/backups","").then(function(j){
        box.innerHTML="";
        if(!j||!j.ok){ box.innerHTML='<div class="hint">'+((j&&j.error==="forbidden")?"🔒 Jen rodiče.":esc((j&&j.error)||"Nepodařilo se načíst."))+'</div>'; return; }
        if(j.pending){ box.appendChild(el('<div class="hint" style="color:#fbbf24;margin:4px 6px;">⏳ Obnova právě probíhá… (obnov za chvíli)</div>')); }
        if(j.status){ var ok=j.status.ok; box.appendChild(el('<div style="margin:4px 6px 8px;font-size:13px;color:'+(ok?"#34d399":"#f87171")+';">'+(ok?"✅ Naposledy obnoveno: ":"✗ Poslední obnova selhala: ")+esc(j.status.file||"")+(j.status.finished?(" · "+esc(j.status.finished)):"")+(ok?'  ·  <a href="/apid/" target="_blank" style="color:#5ee0b7;">Otevřít API D →</a>':"")+'</div>')); }
        if(!j.items||!j.items.length){ box.appendChild(el('<div class="hint">Ve složce '+esc(j.dir||"")+' nejsou žádné zálohy (.dump/.backup/.sql).</div>')); return; }
        j.items.forEach(function(f){
          var rw=el('<div style="display:flex;align-items:center;gap:10px;padding:10px 6px;border-bottom:1px solid var(--bord);"></div>');
          rw.appendChild(el('<div style="flex:1;min-width:0;"><div style="font-weight:600;word-break:break-all;">'+esc(f.name)+'</div><div class="hint">'+esc(f.mtime)+' · '+f.size_mb+' MB</div></div>'));
          var b=el('<button style="padding:8px 12px;border-radius:10px;border:0;background:linear-gradient(110deg,#34d399,#2dd4bf);color:#04150e;font-weight:700;cursor:pointer;white-space:nowrap;">Rozbalit do API D</button>');
          b.addEventListener("click",function(){
            if(!confirm("Rozbalit zálohu „"+f.name+"\" do API D?\n(Produkce se nedotkne — jen testovací DB.)")) return;
            b.disabled=true; b.textContent="Zařazuji…";
            api("POST","/api/v1/erp/app/admin/apid/restore",{file:f.name}).then(function(r){
              if(r&&r.ok){ alert(r.info||"Obnova zařazena."); load(); }
              else { b.disabled=false; b.textContent="Rozbalit do API D"; alert("Chyba: "+((r&&r.error)||"?")); }
            });
          });
          rw.appendChild(b); box.appendChild(rw);
        });
      });
    }
    load();
  }
  // Marti 8.6.: SMS brána — JEN Marti-AI mobil přeposílá ověřovací SMS (vlastní
  // gateway, bez cizího provideru). Ostatní telefony nech vypnuté.
  function set_smsgw(){
    app.innerHTML=topbar("SMS brána", true);
    var p=el('<div class="panel"></div>');
    var on=false; try{ on=!!(B&&B.isSmsGateway&&B.isSmsGateway()); }catch(e){}
    p.appendChild(el('<div class="hint" style="margin-bottom:8px;">Zapni JEN na firemním telefonu, který slouží jako brána pro ověřování čísel (Marti-AI mobil). Ten pak přeposílá příchozí ověřovací SMS (s kódem STG-) do STRATEGIE. Soukromé SMS se nikdy nepřeposílají. Na ostatních telefonech nech vypnuté.</div>'));
    var st=el('<div class="hint" style="margin-top:8px;"></div>');
    var b=el('<button class="'+(on?"ghost":"green")+' full" style="font-size:16px;">'+(on?"✅ Brána je zapnutá — klepni pro vypnutí":"📨 Zapnout SMS bránu na tomto telefonu")+'</button>');
    b.addEventListener("click",function(){
      var want=!on;
      var r=""; try{ r=B.setSmsGateway(want); }catch(e){ r="0"; }
      if(r==="need"){ st.textContent="🔐 Povol příjem SMS a klepni znovu."; return; }
      on=(r==="1");
      b.className=(on?"ghost":"green")+" full"; b.style.fontSize="16px";
      b.textContent=on?"✅ Brána je zapnutá — klepni pro vypnutí":"📨 Zapnout SMS bránu na tomto telefonu";
      st.textContent=on?"✅ Tento telefon teď přeposílá ověřovací SMS.":"Brána vypnuta.";
    });
    p.appendChild(b); p.appendChild(st); app.appendChild(p);
  }
  function set_listen(){ app.innerHTML=topbar("Párování s ERP", true); var p=el('<div class="panel"></div>'); var ls=listenState();
    p.appendChild(el('<div class="big">Párování: <b>'+(ls==null?"(jen v appce)":(ls?"aktivní ✓":"pozastaveno"))+'</b></div>'));
    if(B&&typeof B.startListening==="function"){
      if(ls){ var off=el('<button class="warn full">Pozastavit párování</button>'); off.addEventListener("click",function(){ B.stopListening(); setTimeout(function(){ render(); },700); }); p.appendChild(off); }
      else { var on=el('<button class="green full">Aktivovat párování</button>'); on.addEventListener("click",function(){ B.startListening(); setTimeout(function(){ render(); },900); }); p.appendChild(on); }
      if(typeof B.openBatterySettings==="function"){ var bb=el('<button class="ghost full">Vypnout úsporu baterie (ať párování nepadá)</button>'); bb.addEventListener("click",function(){B.openBatterySettings();}); p.appendChild(bb); }
    } else { p.appendChild(el('<div class="hint">Párování se ovládá v appce STRATEGIE.</div>')); }
    p.appendChild(el('<div class="hint">Když je párování aktivní, ve stavovém řádku svítí <b>zelená ikona energie</b> a telefon přijímá vytáčení/úkoly z ERP. Vyžaduje povolená oznámení a vypnutou úsporu baterie pro STRATEGII — jinak ji systém uspí.</div>')); app.appendChild(p); }
  function set_icons(){ app.innerHTML=topbar("Ikony na plochu", true); var p=el('<div class="panel"></div>');
    p.appendChild(el('<div class="hint">Přidání ikon ERP a Chat na plochu je nativní akce v appce STRATEGIE. Most doplníme.</div>')); app.appendChild(p); }
  function set_install(){ app.innerHTML=topbar("Nainstalovat na plochu", true); var p=el('<div class="panel"></div>');
    var b=el('<button class="green full">Nainstalovat /mobile jako appku</button>'); var info=el('<div class="hint"></div>');
    b.addEventListener("click",function(){ if(deferredPrompt){deferredPrompt.prompt();try{deferredPrompt.userChoice.then(function(){deferredPrompt=null;});}catch(e){}} else {info.textContent="Pokud nabídka nevyskočí: v prohlížeči ⋮ → Přidat na plochu / Nainstalovat aplikaci.";} });
    p.appendChild(b); p.appendChild(info); p.appendChild(el('<div class="hint">Nainstaluje /mobile jako samostatnou PWA (vlastní ikona, bez lišty prohlížeče).</div>')); app.appendChild(p); }
  function set_prefixes(){ app.innerHTML=topbar("Prefixy kontaktů a hovorů", true); var p=el('<div class="panel"></div>');
    p.appendChild(el('<label>Zobrazovat jen kontakty a hovory začínající (oddělené čárkou)</label>'));
    var inp=el('<input id="pfx" value="'+esc(getPrefixes())+'">'); p.appendChild(inp);
    var b=el('<button class="green full">Uložit</button>'); b.addEventListener("click",function(){var v=(inp.value||"").trim()||"STR,EC";try{localStorage.setItem("stg_prefixes",v);}catch(e){}back();}); p.appendChild(b);
    p.appendChild(el('<div class="hint">Standardně STR, EC. Platí pro Kontakty i Historii hovorů.</div>')); app.appendChild(p); }
  function set_dev(){ app.innerHTML=topbar("Vývojářské", true); var p=el('<div class="panel"></div>');
    p.appendChild(el('<div class="big">DEV mód: <b>'+(DEV?"zapnutý":"vypnutý")+'</b></div>'));
    var t=el('<button class="'+(DEV?"warn":"green")+' full">'+(DEV?"Vypnout DEV mód":"Zapnout DEV mód")+'</button>');
    t.addEventListener("click",function(){try{if(DEV)localStorage.removeItem("stg_mobile_dev");else localStorage.setItem("stg_mobile_dev","1");}catch(e){}location.href=location.pathname;}); p.appendChild(t);
    p.appendChild(el('<div class="devinfo">Most: '+(native?("aktivní — "+[canDial?"dialNumber":"",canListen?"listening":"",canFetch?"authedFetch":"",(B&&B.getContacts)?"getContacts":"",(B&&B.getCallLog)?"getCallLog":""].filter(Boolean).join(", ")):"není (prohlížeč)")+'</div>')); app.appendChild(p); }
  function set_about(){ app.innerHTML=topbar("O aplikaci", true); var p=el('<div class="panel"></div>'); app.appendChild(p);
    if(!(B&&typeof B.checkUpdate==="function")){
      p.appendChild(el('<div class="list"><div class="row" style="cursor:default"><div class="tx"><div class="tt">Verze</div><div class="sub">'+(ver||"— (jen v appce)")+'</div></div></div><div class="row" style="cursor:default"><div class="tx"><div class="tt">Režim</div><div class="sub">prohlížeč (PWA)</div></div></div></div>'));
      return;
    }
    var status=el('<div class="hint">Kontroluji novou verzi…</div>'); p.appendChild(status);
    setTimeout(function(){
      var j={}; try{ var t=B.checkUpdate(); if(t)j=JSON.parse(t); }catch(e){}
      var bt=j.build_time||(B.buildTime?(function(){try{return B.buildTime();}catch(e){return "";}})():"");
      var box=el('<div class="list"></div>');
      box.appendChild(el('<div class="row" style="cursor:default"><div class="tx"><div class="tt">Verze appky</div><div class="sub">'+esc(j.current_name||ver)+' (code '+esc(String(j.current_code||""))+')</div></div></div>'));
      box.appendChild(el('<div class="row" style="cursor:default"><div class="tx"><div class="tt">Sestaveno</div><div class="sub">'+esc(bt)+'</div></div></div>'));
      p.replaceChild(box,status);
      if(j.has_update){
        p.appendChild(el('<div class="big" style="color:#5ee0b7;margin-top:12px;">Nová verze '+esc(j.latest_name)+' (code '+esc(String(j.latest_code))+')</div>'));
        var ub=el('<button class="green full">Aktualizovat na novou verzi</button>'); ub.addEventListener("click",function(){ try{B.installUpdate();}catch(e){} }); p.appendChild(ub);
      } else if(j.error){ p.appendChild(el('<div class="hint" style="margin-top:12px;">Verzi se nepodařilo zjistit (zkontroluj párování / připojení).</div>')); }
      else { p.appendChild(el('<div class="hint" style="margin-top:12px;">Máš nejnovější verzi ✓</div>')); }
      p.appendChild(el('<div class="group">Telefon a ERP</div>'));
      var pair=el('<button class="ghost full" style="margin-top:0;">Spárovat telefon (sken QR)</button>');
      pair.addEventListener("click",function(){ try{ if(typeof B.scanPairQr==="function") B.scanPairQr(); else B.openPairing(); }catch(e){} });
      p.appendChild(pair);
      p.appendChild(el('<div class="hint">Na PC otevři <b>strategie-ai.com/app-pair</b> (ukáže QR), pak tady klepni Spárovat a naskenuj ho fotoaparátem.</div>'));
    },60);
  }

  // ───── APLIKACE (launcher) ─────
  function openApp(url){ var u=(url.charAt(0)==="/")?(location.origin+url):url; if(B&&typeof B.openExternal==="function")B.openExternal(u); else { try{window.open(u,"_blank");}catch(e){ location.href=u; } } }
  // Interní STRATEGIE přehledy (/flow, /absence-plan…) — otevřít jako OVERLAY (iframe) UVNITŘ appky.
  // Appka se neopustí → Android Back nezavře aplikaci, jen zavře overlay. Žádný externí prohlížeč.
  // Přehledy se otevírají jako NATIVNÍ obrazovka v zásobníku (stejné schéma jako Skupiny) →
  // Zpět řídí výhradně back() appky (topbar i systémové Zpět). Žádný vlastní overlay/history hack.
  var _XV_TITLES={"/flow":"📊 FLOW","/vytizeni":"📈 Vytížení","/vytizeni-prehled":"🔋 Vytížení dílny","/crm-plan-hovoru":"📞 Plán hovorů","/absence-plan":"🏖️ Plán absencí","/dir-admin":"🗂️ Adresáře","/files":"📁 Dokumenty","/payroll":"💰 Mzdové podklady","/objednavky":"🛒 Co objednat","/digitalizace":"🗂️ Digitalizace","/zrcadla":"🪞 Zrcadla","/banka":"🏦 Banka","/denik":"🧾 Účetní deník","/parovani":"🏦 Párování plateb","/uctovani":"📒 Účetnictví","/edi-stat":"📊 Statistika EDI","/edi-definice":"🧩 EDI definice","/neschopenky":"🤒 Neschopenky","/davky":"📤 Dávky ČSSZ","/audit-davky":"🛡️ Audit dávek","/iso":"🛡️ ISO 27001","/dokument":"📚 Dokumentace","/rozvrh-verze":"🗓️ Varianty rozvrhu","/rozvrh-prehled":"🗓️ Přehled po ročnících","/claude-chat":"🛠️ Chat s Claudem","/cil":"🎯 Cíle"};
  var _xvUrl="", _xvTitle="", _xvStack=[];
  function _xvSet(url){ _xvUrl=url; _xvTitle=_XV_TITLES[(url||"").split("?")[0]]||"Přehled"; }
  function openInApp(url){
    if(stack[stack.length-1]==="extview"){ _xvStack.push(url); _xvSet(url); render(); }  // navigace UVNITŘ appky → zásobník (zpět se vrátí o krok, ne ven)
    else { _xvStack=[url]; _xvSet(url); go("extview"); }
  }
  function extview(){
    app.innerHTML=topbar(_xvTitle||"Přehled", true, true);
    var fr=el('<iframe id="stgXvF" style="display:block;width:100%;height:calc(100vh - 56px);border:0;background:var(--bg);"></iframe>');
    app.appendChild(fr);
    var u=(_xvUrl.charAt(0)==="/")?(location.origin+_xvUrl):_xvUrl;
    function _w(html){ try{ var d=fr.contentWindow.document; d.open(); d.write(html); d.close(); } catch(e){ fr.srcdoc=html; } }
    // Caddy dává X-Frame-Options: DENY globálně → iframe src padá; vepíšeme obsah přes document.write.
    // + skryjeme vnitřní „← Zpět" stránky (máme topbar appky) a neutralizujeme history uvnitř iframu.
    var _inj='<base href="'+location.origin+'/"><style>[onclick*="goBackApp"],#navBackBtn{display:none!important}</style>'+
             '<script>window.__navBack=1;history.pushState=function(){};history.replaceState=function(){};<\/script>';
    _w('<!doctype html><meta charset=utf-8><body style="background:#0b1020;color:#9fb0d0;font:15px system-ui;padding:16px">Načítám…</body>');
    fetch(u,{credentials:"same-origin"}).then(function(r){return r.text();}).then(function(html){
      if(html.indexOf("<base")<0){ html=html.replace(/<head([^>]*)>/i,'<head$1>'+_inj); }
      else { html=html.replace(/<head([^>]*)>/i,'<head$1><style>[onclick*="goBackApp"],#navBackBtn{display:none!important}</style><script>window.__navBack=1;history.pushState=function(){};history.replaceState=function(){};<\/script>'); }
      _w(html);
    }).catch(function(){ _w('<!doctype html><meta charset=utf-8><body style="background:#0b1020;color:#ff8a8a;font:15px system-ui;padding:16px">Nepodařilo se načíst přehled.</body>'); });
  }
  // Vnitřní „← Zpět" v přehledu (pokud zůstane) → nativní back() appky.
  window.addEventListener("message",function(ev){ if(ev&&ev.data==="stgCloseOverlay"){ try{back();}catch(e){} } else if(ev&&ev.data&&ev.data.stgOpen){ try{ openInApp(ev.data.stgOpen); }catch(e){} } else if(ev&&ev.data&&ev.data.stgOpenExt){ try{ (typeof openApp==="function"?openApp(ev.data.stgOpenExt):window.open(ev.data.stgOpenExt,"_blank")); }catch(e){} } });
  function appCell(iconHtml,label,badge,fn){ var c=el('<div class="appcell"><div class="appicon">'+iconHtml+'</div><div class="applabel">'+esc(label)+'</div>'+(badge?'<span class="appbadge">'+(badge>99?"99+":badge)+'</span>':'')+'</div>'); c.addEventListener("click",fn); return c; }
  function _isoWeek(d){ var t=new Date(Date.UTC(d.getFullYear(),d.getMonth(),d.getDate())); var dn=(t.getUTCDay()+6)%7; t.setUTCDate(t.getUTCDate()-dn+3); var f=new Date(Date.UTC(t.getUTCFullYear(),0,4)); return 1+Math.round(((t-f)/86400000 - 3 + ((f.getUTCDay()+6)%7))/7); }
