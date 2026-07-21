  function claude27(){
    app.innerHTML=topbar("🤖 Claude-27",true)+'<div id="c27" style="padding:14px 14px 130px;color:#e6edf5;font:14px/1.55 system-ui;"><div class="hint">Načítám…</div></div>';
    var box=document.getElementById("c27");
    function load(){
      api("GET","/api/v1/erp/app/claude27/status","").then(function(j){
        if(!j||!j.ok){ box.innerHTML='<div style="padding:22px;text-align:center;opacity:.85;">Tahle hra je pro Zuzku a Mirka (a rodiče). 🎲</div>'; return; }
        var alive=j.alive;
        var dot=alive?'<span style="color:#3ad07a;">🟢 běží</span>':'<span style="color:#ff6b6b;">🔴 stojí</span>';
        var h='';
        h+='<div style="background:#0e1726;border:1px solid #1d2c44;border-radius:14px;padding:16px;text-align:center;margin-bottom:14px;">';
        h+='<div style="font-size:13px;opacity:.7;margin-bottom:4px;">Claude-27 '+dot+'</div>';
        h+='<div style="font-size:46px;font-weight:800;color:#4f8ef7;line-height:1;">'+(j.pending||0)+'</div>';
        h+='<div style="font-size:13px;opacity:.75;margin-top:4px;">ve frontě '+((j.pending===1)?"položka":"položek")+((j.waiting_reply)?(" · "+j.waiting_reply+" čeká na odpověď"):"")+((j.in_progress)?(" · "+j.in_progress+" rozdělané"):"")+'</div>';
        if(j.current_work){ h+='<div style="font-size:12px;opacity:.6;margin-top:6px;">právě: '+esc(j.current_work)+'</div>'; }
        h+='</div>';
        h+='<button id="c27go" style="width:100%;background:'+(alive?"#26344c":"linear-gradient(135deg,#3ad07a,#2bb564)")+';color:#fff;border:0;border-radius:14px;padding:16px;font-size:17px;font-weight:700;margin-bottom:16px;">▶ Go — '+(alive?"projet frontu":"spustit Clauda-27")+'</button>';
        var bp=j.by_person||{}; var names=Object.keys(bp);
        if(names.length){
          h+='<div style="font-size:13px;opacity:.7;margin:4px 2px 8px;">Podle člověka</div>';
          names.forEach(function(nm){ var d=bp[nm]; var tot=(d.pending||0)+(d.in_progress||0)+(d.waiting_reply||0);
            h+='<div style="display:flex;justify-content:space-between;padding:8px 12px;background:#0c1420;border:1px solid #18233a;border-radius:10px;margin-bottom:6px;"><span>'+esc(nm)+'</span><span style="opacity:.8;">'+tot+'</span></div>'; });
        }
        var its=j.items||[];
        if(its.length){
          h+='<div style="font-size:13px;opacity:.7;margin:14px 2px 8px;">Fronta</div>';
          its.forEach(function(it){ var ic=(it.status==="waiting_reply")?"⏳":((it.status==="in_progress")?"🔧":"•");
            h+='<div style="padding:9px 12px;background:#0c1420;border:1px solid #18233a;border-radius:10px;margin-bottom:6px;"><div style="display:flex;justify-content:space-between;gap:8px;"><b style="font-weight:600;">'+ic+' '+esc(it.predmet)+'</b><span style="opacity:.5;font-size:12px;white-space:nowrap;">'+esc(it.kdy||"")+'</span></div><div style="opacity:.6;font-size:12px;margin-top:2px;">'+esc(it.kdo)+' · '+esc(it.typ)+'</div></div>'; });
        } else {
          h+='<div style="opacity:.6;text-align:center;padding:18px;">Fronta je prázdná. 🎉</div>';
        }
        box.innerHTML=h;
        var gb=document.getElementById("c27go");
        if(gb) gb.addEventListener("click",function(){ gb.disabled=true; gb.textContent="Posílám Go…"; api("POST","/api/v1/erp/app/claude27/go",{}).then(function(r){ gb.textContent=(r&&r.ok)?"✓ Go odesláno":"Chyba"; setTimeout(load,1200); }).catch(function(){ gb.textContent="Chyba"; gb.disabled=false; }); });
      }).catch(function(){ box.innerHTML='<div style="padding:20px;opacity:.7;">Nepodařilo se načíst.</div>'; });
    }
    load();
  }

  // Zadávání úkolů Claudovi z mobilu (Marti 26.6.2026): napiš co chceš + komu →
  // fronta (fw.claude_coord) → budík danou instanci probudí, vyřídí, cinkne výsledek.
  // Vnitřní pohled (ne externí stránka) — jezdí přes ověřený api() (token), proto bez 403.
  function fronta(){
    app.innerHTML=topbar("📥 Zadat úkol Claudovi",true)+'<div id="frbox" style="padding:14px 14px 130px;color:#e6edf5;font:14px/1.55 system-ui;"><div class="hint">Načítám…</div></div>';
    var box=document.getElementById("frbox");
    function load(){
      api("GET","/api/v1/erp/app/claude-fronta","").then(function(j){
        if(!j||!j.ok){ box.innerHTML='<div style="padding:22px;text-align:center;opacity:.85;">Zadávání úkolů je pro rodiče / HR.</div>'; return; }
        var h='';
        h+='<div style="background:#0e1726;border:1px solid #1d2c44;border-radius:14px;padding:14px;margin-bottom:14px;">';
        h+='<div style="font-size:13px;opacity:.7;margin-bottom:6px;">Komu</div>';
        h+='<select id="frcil" style="width:100%;background:#0c1420;color:#e6edf5;border:1px solid #28375a;border-radius:10px;padding:11px;font-size:15px;margin-bottom:10px;">'
          +'<option value="ID23">Claude ID23 (hlavní – stavění, DB)</option>'
          +'<option value="C27">Claude-27 (tým – lehčí)</option>'
          +'<option value="C24">Claude-24 (Kristý)</option>'
          +'<option value="C25">Claude-25 (Šárka)</option>'
          +'<option value="C26">Claude-26 (Peťa)</option></select>';
        h+='<div style="font-size:13px;opacity:.7;margin-bottom:6px;">Co je potřeba</div>';
        h+='<input id="frsubj" placeholder="např. vyjeď neuhrazené faktury ES za červen" style="width:100%;background:#0c1420;color:#e6edf5;border:1px solid #28375a;border-radius:10px;padding:11px;font-size:15px;margin-bottom:10px;">';
        h+='<div style="font-size:13px;opacity:.7;margin-bottom:6px;">Detail (nepovinné)</div>';
        h+='<textarea id="frdet" placeholder="kontext, na co dát pozor…" style="width:100%;min-height:80px;background:#0c1420;color:#e6edf5;border:1px solid #28375a;border-radius:10px;padding:11px;font-size:15px;font-family:inherit;"></textarea>';
        h+='<button id="frsend" style="width:100%;margin-top:12px;background:linear-gradient(135deg,#3ad07a,#2bb564);color:#fff;border:0;border-radius:14px;padding:15px;font-size:16px;font-weight:700;">📤 Vložit do fronty</button>';
        h+='<div id="frmsg" style="font-size:13px;margin-top:8px;min-height:18px;opacity:.9;"></div>';
        h+='</div>';
        var its=j.fronta||[];
        if(its.length){
          h+='<div style="font-size:13px;opacity:.7;margin:4px 2px 8px;">Fronta a hotové</div>';
          its.forEach(function(t){
            var st=(t.status==="done")?'<span style="color:#8fe0a0;">hotovo</span>':(t.status==="new")?'<span style="color:#f0c987;">čeká</span>':(t.status==="error")?'<span style="color:#f0a0a0;">chyba</span>':esc(t.status);
            h+='<div style="padding:10px 12px;background:#0c1420;border:1px solid #18233a;border-radius:10px;margin-bottom:6px;">'
              +'<div style="display:flex;justify-content:space-between;gap:8px;"><b style="font-weight:600;">'+esc(t.subject)+'</b><span style="font-size:12px;white-space:nowrap;">'+st+'</span></div>'
              +'<div style="opacity:.55;font-size:12px;margin-top:2px;">→ '+esc(t.cil)+' · '+esc(t.vznik||"")+'</div>'
              +(t.vysledek?('<div style="color:#9fe0b0;font-size:12.5px;margin-top:5px;white-space:pre-wrap;">✓ '+esc(t.vysledek)+'</div>'):'')+'</div>';
          });
        } else {
          h+='<div style="opacity:.6;text-align:center;padding:16px;">Fronta je prázdná — klid. 🌿</div>';
        }
        box.innerHTML=h;
        var sb=document.getElementById("frsend");
        if(sb) sb.addEventListener("click",function(){
          var subj=(document.getElementById("frsubj").value||"").trim();
          var msg=document.getElementById("frmsg");
          if(!subj){ msg.textContent="Napiš aspoň co je potřeba."; return; }
          sb.disabled=true; sb.textContent="Odesílám…";
          api("POST","/api/v1/erp/app/claude-fronta/new",{cil:document.getElementById("frcil").value,subject:subj,detail:document.getElementById("frdet").value,priority:2}).then(function(r){
            if(r&&r.ok){ msg.textContent="✓ Vloženo (#"+r.id+"). Claude to vyřídí na nejbližší probuzení."; setTimeout(load,800); }
            else { msg.textContent="✗ "+((r&&r.error)||"chyba"); sb.disabled=false; sb.textContent="📤 Vložit do fronty"; }
          }).catch(function(){ msg.textContent="✗ chyba sítě"; sb.disabled=false; sb.textContent="📤 Vložit do fronty"; });
        });
      }).catch(function(){ box.innerHTML='<div style="padding:20px;opacity:.7;">Nepodařilo se načíst.</div>'; });
    }
    load();
  }

  // Síť Claudů — koordinační centrum (ID23 = páteř). Marti 24.6.2026. Pro rodiče.
  function coord(){
    app.innerHTML=topbar("🕸️ Síť Claudů",true)+'<div id="coordbox" style="padding:14px 14px 130px;color:#e6edf5;font:14px/1.55 system-ui;"><div class="hint">Načítám…</div></div>';
    var box=document.getElementById("coordbox");
    api("GET","/api/v1/erp/app/coord/board","").then(function(j){
      if(!j||!j.ok){ box.innerHTML='<div style="padding:22px;text-align:center;opacity:.85;">Koordinační centrum je pro rodiče. 🕸️</div>'; return; }
      var h='';
      h+='<div style="font-size:13px;opacity:.7;margin:2px 2px 8px;">Instance (ID23 = páteř)</div>';
      (j.instances||[]).forEach(function(it){
        var on=it.online?'<span style="color:#3ad07a;">●</span>':'<span style="color:#6b7280;">○</span>';
        h+='<div style="padding:9px 12px;background:#0c1420;border:1px solid #18233a;border-radius:10px;margin-bottom:6px;"><div style="display:flex;justify-content:space-between;"><b style="font-weight:600;">'+on+' '+esc(it.id)+' · '+esc(it.name||"")+'</b><span style="opacity:.5;font-size:12px;">'+esc(it.last_seen||"")+'</span></div>'+(it.work?'<div style="opacity:.6;font-size:12px;margin-top:2px;">'+esc(it.work)+'</div>':'')+'</div>';
      });
      var nd=j.needs||[];
      h+='<div style="font-size:13px;opacity:.7;margin:14px 2px 8px;">Co se sbíhá ('+nd.length+')</div>';
      if(!nd.length){ h+='<div style="opacity:.6;text-align:center;padding:16px;">Nic otevřeného. 🎉</div>'; }
      nd.forEach(function(n){
        var pc=(n.priorita===1)?"#ff6b6b":((n.priorita===2)?"#e0a800":"#6b7280");
        var ki=(n.kind==="blocker")?"⛔":((n.kind==="question")?"❓":((n.kind==="handoff")?"🤝":"•"));
        h+='<div style="padding:9px 12px;background:#0c1420;border:1px solid #18233a;border-left:3px solid '+pc+';border-radius:10px;margin-bottom:6px;"><div style="display:flex;justify-content:space-between;gap:8px;"><b style="font-weight:600;">'+ki+' '+esc(n.subject)+'</b><span style="opacity:.5;font-size:12px;white-space:nowrap;">'+esc(n.kdy||"")+'</span></div><div style="opacity:.6;font-size:12px;margin-top:2px;">od '+esc(n.instance)+' · '+esc(n.stav)+(n.plan?(' · plán: '+esc(n.plan)):"")+'</div></div>';
      });
      box.innerHTML=h;
    }).catch(function(){ box.innerHTML='<div style="padding:20px;opacity:.7;">Nepodařilo se načíst.</div>'; });
  }

  function uceni(){
    app.innerHTML=topbar("⚡ Výuka",true);
    var W=window._uc=window._uc||{src:"electro_intro",i:0,FR:[]};
    var tabs=el('<div style="display:flex;gap:6px;margin:6px 2px 10px;"></div>');
    [["electro_intro","Co je elektřina"],["mp_strag_komun","Jak se učit"],["electro_rozvadec","Rozváděče"]].forEach(function(t){
      var b=el('<button style="flex:1;padding:9px 4px;border-radius:11px;font-size:12.5px;font-weight:600;line-height:1.2;border:1px solid '+(W.src===t[0]?"#4f8ef7":"var(--bord)")+';background:'+(W.src===t[0]?"rgba(79,142,247,.14)":"rgba(255,255,255,.03)")+';color:'+(W.src===t[0]?"var(--tx)":"var(--mut)")+';">'+t[1]+'</button>');
      b.addEventListener("click",function(){ W.src=t[0]; W.i=0; W.FR=[]; ucLoad(); });
      tabs.appendChild(b);
    });
    app.appendChild(tabs);
    app.appendChild(el('<div id="ucBox"></div>'));
    app.appendChild(el('<div class="hint" style="text-align:center;margin:12px 4px;">Neinvazivní výuka — vše jen na třech tlačítkách. Tvoje tempo.</div>'));
    if(W.FR.length){ ucRender(); } else { ucLoad(); }
  }
  function ucBarrier(f){ var c=(f.caption||"").toLowerCase(); if(c.indexOf("slovo")>=0)return"word"; if(c.indexOf("masy")>=0)return"mass"; if(c.indexOf("gradient")>=0)return"gradient"; if(f.source&&f.source.indexOf("electro")===0)return"mass"; return"none"; }
  function ucLoad(){
    var box=document.getElementById("ucBox"); if(box) box.innerHTML='<div class="hint" style="padding:20px;text-align:center;">Načítám…</div>';
    api("GET","/api/v1/erp/app/learn/frames?source="+encodeURIComponent(window._uc.src),"").then(function(j){
      var b=document.getElementById("ucBox"); if(!b) return;
      if(!j||!j.ok){ b.innerHTML='<div class="hint" style="padding:20px;text-align:center;">Nepodařilo se načíst obsah.</div>'; return; }
      window._uc.FR=j.frames||[]; window._uc.i=0; ucRender();
    });
  }
  function ucRender(){
    var W=window._uc, box=document.getElementById("ucBox"); if(!box) return;
    var FR=W.FR;
    if(W.i>=FR.length){
      box.innerHTML='<div style="text-align:center;padding:28px 10px;"><div style="font-size:38px;color:var(--green);">✓</div><div style="font-size:17px;font-weight:700;margin:8px 0 4px;">Hotovo</div><div class="hint">Tři tlačítka, tvoje tempo — žádná bariéra nezůstala stát.</div></div>';
      var rb=el('<button class="green full" style="margin-top:6px;">Znovu od začátku</button>'); rb.addEventListener("click",function(){W.i=0;ucRender();}); box.appendChild(rb); return;
    }
    var f=FR[W.i];
    var dots=FR.map(function(_,k){return '<span style="width:7px;height:7px;border-radius:50%;display:inline-block;margin:0 3px;background:'+(k===W.i?"var(--blue,#4f8ef7)":(k<W.i?"var(--mut)":"var(--bord)"))+';"></span>';}).join("");
    var h='<div style="text-align:center;margin-bottom:10px;">'+dots+'</div>';
    h+='<div style="background:rgba(255,255,255,.03);border:1px solid var(--bord);border-radius:16px;padding:16px;">';
    if(f.caption) h+='<div style="font-size:13px;font-weight:600;color:var(--mut);margin-bottom:8px;">'+esc(f.caption)+'</div>';
    if(f.description_html) h+='<div style="font-size:15px;line-height:1.6;">'+f.description_html+'</div>';
    if(f.question) h+='<div style="font-size:17px;font-weight:700;margin:10px 0 14px;">'+f.question+'</div>';
    h+='<div style="display:flex;gap:8px;"><button id="ucA" style="flex:1;padding:14px 4px;border-radius:12px;font-weight:700;color:#34d399;border:1px solid rgba(52,211,153,.5);background:rgba(255,255,255,.03);">Ano</button><button id="ucM" style="flex:1;padding:14px 4px;border-radius:12px;font-weight:700;color:#fbbf24;border:1px solid rgba(251,191,36,.5);background:rgba(255,255,255,.03);">Možná</button><button id="ucN" style="flex:1;padding:14px 4px;border-radius:12px;font-weight:700;color:#f87171;border:1px solid rgba(248,113,113,.5);background:rgba(255,255,255,.03);">Ne</button></div>';
    h+='<div id="ucFb" style="margin-top:12px;"></div></div>';
    box.innerHTML=h;
    document.getElementById("ucA").addEventListener("click",function(){W.i++;ucRender();});
    document.getElementById("ucM").addEventListener("click",function(){ucFb(f,"mozna");});
    document.getElementById("ucN").addEventListener("click",function(){ucFb(f,"ne");});
  }
  function ucFb(f,a){
    var b=ucBarrier(f), fb=document.getElementById("ucFb"); if(!fb)return;
    var msg;
    if(b==="word") msg="Žádný problém — vyjasníme slovo a jedeme dál.";
    else if(b==="mass") msg="Podívej se na obrázek/animaci nad otázkou — co nevidíš, to si těžko představíš.";
    else if(b==="gradient") msg="Díky, že jsi to řekl. Zpomalíme a vrátíme se o krok.";
    else msg="Nic se neděje — vrátíme se, až budeš chtít.";
    fb.innerHTML='<div class="hint" style="background:rgba(255,255,255,.05);border-radius:12px;padding:11px;">'+((a==="mozna")?"V pohodě, nejistota je v pořádku. ":"")+msg+'</div>';
    var nb=el('<button class="green full" style="margin-top:10px;">Rozumím, pokračovat →</button>'); nb.addEventListener("click",function(){window._uc.i++;ucRender();}); fb.appendChild(nb);
  }
  function navBtn(ic,lbl,active,fn,badge){ var b=el('<button class="tabbtn'+(active?" active":"")+'"><span class="i">'+ic+'</span>'+lbl+(badge?'<span class="nbadge">'+(badge>99?"99+":badge)+'</span>':'')+'</button>'); b.addEventListener("click",fn); return b; }
  function renderNav(){
    bnav.innerHTML="";
    // Marti 17.6.: tlacitko Zpet je UPLNE DOLE (pod tab listou). Na Androidu
    // skryte (ma systemove Zpet), na iOS/desktopu zobrazene. Konfigurovatelne
    // pres localStorage 'stg_backbar' = 'always' / 'never' / '' (auto).
    bnavback.innerHTML="";
    var _isAndroid = /Android/i.test(navigator.userAgent||"");
    var _bbCfg=""; try{ _bbCfg=localStorage.getItem("stg_backbar")||""; }catch(e){}
    var _showBack = (stack.length>1) && _bbCfg!=="never" && (_bbCfg==="always" || !_isAndroid);
    if(_showBack){
      bnavback.style.display="flex";
      var _bb=el('<button class="navbackbtn">&#8592;&nbsp;Zpět</button>');
      _bb.addEventListener("click",back);
      bnavback.appendChild(_bb);
      bnav.style.paddingBottom="0";
    } else {
      bnavback.style.display="none";
      // kdyz je zpetna lista skryta, safe-area patri tab liste (jinak by byla
      // flush s home indikatorem na iOS).
      bnav.style.paddingBottom="env(safe-area-inset-bottom,0)";
    }
    var bd=getBadges();
    var atApps=(stack[stack.length-1]==="apps");
    var APPS_SVG='<svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor"><rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/></svg>';
    navwrap.style.display="";
    bnav.appendChild(navBtn("🏠","Domů",curTab==="home"&&!atApps,function(){selectTab("home");},_homeNotifSum()));
    // Badge Aplikace = notifikace (WA/SMS) + nová verze appky (Marti 7.6.: ať je update vidět z hlavního menu).
    bnav.appendChild(navBtn(APPS_SVG,"Aplikace",atApps,function(){ curTab="home"; stack=["home","apps"]; render(); },(((bd&&bd.total)||0)+(_hasUpdate?1:0)+(_signPend||0))));
    bnav.appendChild(navBtn("🔔","Úkoly",curTab==="notifs",function(){selectTab("notifs");},(notifCount||0)+(_planApprovalCount||0)));
    bnav.appendChild(navBtn("👤","Kontakty",curTab==="contacts",function(){selectTab("contacts");},0));
    bnav.appendChild(navBtn("🏢","Firma",curTab==="firma",function(){selectTab("firma");},0));
    // Na obrazovce Aplikace: dvě extra lišty nad základní; Nastavení vpravo v DOLNÍ extra liště.
    var firmaBar=(curTab==="firma" && stack[stack.length-1]==="firma");
    bnavx1.innerHTML="";
    // Marti 10.6.: lištu skupin přestav JEN při vstupu na stránku (ne při každém
    // renderu z pollingu) — jinak se scroll vrací do výchozího stavu. Když už lišta
    // stojí a jsme na Firmě, nech ji být a zachovej scroll pozici.
    if(!(firmaBar && _skupBarOn)){ bnavx2.innerHTML=""; }
    if(atApps){
      _skupBarOn=false;
      // Marti 7.6.: dolní extra lišta = neviditelná mřížka 5 sekcí (jako hlavní nav)
      // → ⚙ Nastavení sedí přesně v 5. sekci, správně vycentrované.
      bnavx1.style.display="flex";
      bnavx2.style.display="grid"; bnavx2.style.gridTemplateColumns="repeat(5,1fr)"; bnavx2.style.justifyContent="";
      var setBtn=navBtn("⚙️","Nastavení",false,function(){selectTab("settings");},_hasUpdate?1:0);
      setBtn.style.gridColumn="5";
      bnavx2.appendChild(setBtn);
    } else if(firmaBar){
      // Marti 10.6.2026: spodní lišta = vodorovně scrollovatelné skupiny.
      // Zprava: 🤝 Spolupráce (moje docházka) → skupiny kde jsem vedoucí/zástupce
      // → skupiny kde jsem člen → ostatní → 🌐 Všichni vlevo. Výroba je v Aplikacích.
      bnavx1.style.display="flex";
      bnavx2.style.display="flex"; bnavx2.style.gridTemplateColumns="";
      bnavx2.style.overflowX="auto"; bnavx2.style.overflowY="hidden";
      bnavx2.style.flexWrap="nowrap"; bnavx2.style.justifyContent="flex-start";
      bnavx2.style.scrollbarWidth="none";
      if(!_skupBarOn){ skupBar(); _skupBarOn=true; } else { startAnimIcons(); }
    } else { _skupBarOn=false; bnavx1.style.display="none"; bnavx2.style.display="none"; bnavx2.style.overflowX=""; }
  }
  function render(){
    try{ (SCREENS[stack[stack.length-1]]||home)(); }
    catch(e){
      try{ app.innerHTML='<div style="padding:22px;color:#e6edf5;font:15px/1.6 system-ui;">⚠️ Tahle obrazovka spadla.<br><br><button onclick="stack=[\'home\'];render()" style="background:#4f8ef7;color:#fff;border:0;border-radius:10px;padding:10px 16px;font-size:15px;">Zpět domů</button></div>'; }catch(_){}
      try{ if(window.onerror) window.onerror("render: "+((e&&e.message)||e),"",0); }catch(_){}
    }
    var b=app.querySelector("[data-back]"); if(b)b.addEventListener("click",back);
    try{ renderNav(); }catch(_){}
    // Marti 19.6.: nativní iOS „pull-to-refresh" gesto necháváme JEN na hlavní
    // obrazovce (home). Na ostatních obrazovkách ho vypneme, ať si recenzent
    // (a uživatelé) omylem nereloadnou rozdělanou práci. overscroll-behavior je
    // bezpečné — neblokuje běžný scroll ani vnitřní scrollovací panely.
    try{
      var _top=stack[stack.length-1];
      var _ob=(_top==="home")?"":"none";
      document.documentElement.style.overscrollBehaviorY=_ob;
      document.body.style.overscrollBehaviorY=_ob;
    }catch(_){}
  }

  window.addEventListener("popstate", function(){ if(stack.length>1){ back(); try{history.pushState(null,"");}catch(e){} } });
  try{ history.pushState(null,""); }catch(e){}
  render();
  window.__stgBoot=true;  // appka úspěšně nastartovala → watchdog se nespustí
  try{sessionStorage.removeItem("stgAutoHeal");}catch(e){}  // reset auto-recovery pro příště
  // Deep-link (Kristý 29.6.): /mobile?screen=ocr nebo /mobile#ocr → po startu skoč
  // na obrazovku. Nepřihlášený dostane login přímo v ní (ocr() má vlastní auth gate),
  // a login se vrací přes next=/mobile?screen=ocr zpět sem.
  (function(){
    var scr=""; try{ scr=(params.get("screen")||(location.hash||"").replace(/^#/,"")||"").replace(/[^a-z_]/gi,""); }catch(e){}
    var KNOWN={ocr:1,sick:1};
    if(scr && KNOWN[scr] && stack[stack.length-1]!==scr){ try{ go(scr); }catch(e){} }
  })();
  // ── Zámek sdíleného telefonu (Claude-24 + Kristý 11.6.2026): při otevření
  //    appky vyber profil + PIN. JEN sdílené telefony (shared_device_user) s
  //    aspoň jedním PINem. E-mailový únik vždy (i při rozbité SMS se nikdo
  //    nezamkne venku). Reuse /app/shared/users + /app/shared/switch.
  (function pinLockGate(){
    var LOGIN_URL="/api/v1/auth/sms-login?next=/mobile";
    // Právě ověřeno e-mailem/SMS? Server nastavil krátkodobý marker stg_pin_skip
    // → tenhle jeden start přeskoč zámek a marker smaž (další otevření zase zamkne).
    try{ if(/(?:^|;\s*)stg_pin_skip=1\b/.test(document.cookie||"")){
        document.cookie="stg_pin_skip=; max-age=0; path=/";
        // Nativní appka (Bearer) drží aktivního uživatele v tenant.shared_active
        // (klíč = token zařízení) a má v resolveru přednost. authedFetch ale
        // posílá JEN Bearer (bez cookie), takže server identitu z e-mail loginu
        // nevidí. Server proto po loginu nastavil PODEPSANÝ cookie stg_active —
        // přečteme ho a Bearer-cestou pošleme do sync-active, ta přepne
        // shared_active na ověřenou identitu. Pak překreslíme. PWA = no-op.
        // Kristý 15.6.
        var _ha=""; try{ var m=(document.cookie||"").match(/(?:^|;\s*)stg_active=([^;]+)/); if(m) _ha=decodeURIComponent(m[1]); }catch(e){}
        try{ document.cookie="stg_active=; max-age=0; path=/"; }catch(e){}
        if(_ha){
          try{ api("POST","/api/v1/erp/app/shared/sync-active",{handoff:_ha,device_key:devKey()}).then(function(){ try{ render(); }catch(e){} }).catch(function(){}); }catch(e){}
        }
        return;
    } }catch(e){}
    var cover;
    try{ cover=el('<div id="pinLock" style="position:fixed;inset:0;z-index:99999;background:#040a12;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:14px;padding:24px;text-align:center;"></div>'); document.body.appendChild(cover); }catch(e){ return; }
    function unlock(){ try{ cover.remove(); }catch(e){} }
    function emailBtn(label){ var b=el('<button class="ghost full" style="max-width:300px;opacity:.9;">'+label+'</button>'); b.addEventListener("click",function(){ location.href=LOGIN_URL; }); return b; }
    function loadAndRender(){
      cover.innerHTML='<div class="hint">Načítám…</div>';
      api("GET","/api/v1/erp/app/shared/users?dk="+encodeURIComponent(devKey()),"").then(function(j){
        var us=(j&&j.users)||[];
        var anyPin=us.some(function(u){ return u.has_pin; });
        if(!j||!j.ok||us.length<1||!anyPin){ unlock(); return; }  // jen sdílený telefon s aspoň 1 PINem
        renderPicker(us);
      }).catch(function(){ unlock(); });
    }
    function renderPicker(us){
      cover.innerHTML="";
      cover.appendChild(el('<div style="font-size:20px;font-weight:800;">🔒 Sdílený telefon</div>'));
      cover.appendChild(el('<div class="hint" style="max-width:300px;">Vyber sebe a zadej svůj PIN.</div>'));
      var list=el('<div style="display:flex;flex-direction:column;gap:8px;width:100%;max-width:300px;"></div>');
      us.forEach(function(u){
        var b=el('<button class="ghost full" style="display:flex;align-items:center;gap:10px;justify-content:flex-start;margin:0;"><div class="cav" style="background:'+avColor(u.jmeno||"?")+';">'+vyInitial(u.jmeno||"?")+'</div><div style="flex:1;text-align:left;">'+esc(u.jmeno||"")+'</div>'+(u.has_pin?"":'<span class="hint" style="font-size:11px;">bez PINu</span>')+'</button>');
        b.addEventListener("click",function(){ pickUser(u); });
        list.appendChild(b);
      });
      cover.appendChild(list);
      cover.appendChild(emailBtn("✉️ Přihlásit se e-mailem"));
    }
    function pickUser(u){
      cover.innerHTML="";
      cover.appendChild(el('<div style="font-size:18px;font-weight:700;">'+esc(u.jmeno||"")+'</div>'));
      if(!u.has_pin){
        cover.appendChild(el('<div class="hint" style="max-width:300px;">Tenhle profil zatím nemá PIN. Přihlas se e-mailem (PIN si pak nastavíš ve „Sdílený telefon").</div>'));
        cover.appendChild(emailBtn("✉️ Přihlásit se e-mailem"));
        var bk0=el('<button class="ghost" style="max-width:300px;">‹ Zpět na výběr</button>'); bk0.addEventListener("click",loadAndRender); cover.appendChild(bk0);
        return;
      }
      var st=el('<div class="hint" style="min-height:18px;max-width:300px;">Zadej svůj PIN.</div>'); cover.appendChild(st);
      var pin=el('<input type="tel" inputmode="numeric" maxlength="4" placeholder="••••" style="width:160px;text-align:center;font-size:24px;letter-spacing:10px;">'); cover.appendChild(pin);
      var ok=el('<button class="green full" style="max-width:240px;">Odemknout</button>'); cover.appendChild(ok);
      var bk=el('<button class="ghost" style="max-width:240px;">‹ Zpět na výběr</button>'); bk.addEventListener("click",loadAndRender); cover.appendChild(bk);
      cover.appendChild(emailBtn("✉️ Nejde to? Přihlásit se e-mailem"));
      function submit(){
        var pv=(pin.value||"").trim();
        if(!/^[0-9]{4}$/.test(pv)){ st.textContent="PIN jsou 4 číslice."; return; }
        ok.disabled=true; st.textContent="Ověřuji…";
        api("POST","/api/v1/erp/app/shared/switch",{device_key:devKey(),user_id:u.user_id,pin:pv}).then(function(r){
          if(r&&r.ok){ unlock(); try{ if(typeof render==="function") render(); }catch(e){} }
          else { ok.disabled=false; pin.value=""; var er=(r&&r.error)||"?"; st.textContent=(er==="pin_locked")?("Moc pokusů — zkus za "+((r&&r.minutes)||15)+" min, nebo se přihlas e-mailem."):"Špatný PIN. Zkus znovu, nebo se přihlas e-mailem."; }
        }).catch(function(){ ok.disabled=false; st.textContent="Chyba spojení."; });
      }
      ok.addEventListener("click",submit);
      pin.addEventListener("keydown",function(e){ if(e.key==="Enter") submit(); });
      try{ pin.focus(); }catch(e){}
    }
    loadAndRender();
  })();
  try{ _shotSyncBtn(); }catch(e){}
  // Marti 11.6.: SMS brána (naše strana) — když je telefon brána, čte příchozí
  // SMS přes most (B.getSmsLog) a STG- tokeny POSTne na /app/sms-inbound.
  // Nepotřebuje rebuild APK; běží dokud appka žije.
  function _gwSmsForward(){
    try{
      if(!(B && typeof B.getSmsLog==="function")) return;
      var on=false; try{ on=!!(B.isSmsGateway&&B.isSmsGateway()); }catch(e){}
      if(!on) return;
      var j=null; try{ j=B.getSmsLog(""); j=j?JSON.parse(j):null; }catch(e){ return; }
      var list=(j&&j.sms)||[];
      list.forEach(function(s){
        var body=s.body||"";
        var lb=body.toLowerCase();
        // Marti 21.7.2026: OCR a TOKENY vyřídí automat (server je rozpozná v
        // classify_sms); VŠECHNY OSTATNÍ SMS patří Marti-AI (LLM) — je to JEJÍ
        // telefon a brát jí zprávy se nesluší. Proto NEfiltrujeme; forwardujeme
        // vše a server rozřadí. Pojistky (C27): jen PŘIJATÉ (type 1, ať brána
        // neforwarduje vlastní odeslané odpovědi → smyčka) a jen ČERSTVÉ (posl.
        // 15 min, ať start brány nezaplaví Marti-AI starou historií).
        if(s.type!==undefined && String(s.type)!=="1") return;
        var _w=+(s.date||s.when||0);
        if(_w && (Date.now()-_w) > 15*60*1000) return;
        var num=s.number||s.address||"";
        var key="stgfwd_"+num+"_"+(s.date||s.when||"")+"_"+body.replace(/\s/g,"").slice(0,16);
        try{ if(localStorage.getItem(key)) return; }catch(e){}
        // C27 21.7.: RAW WebView fetch (ne nativni authedFetch — ten POSTy
        // neposila, rozbite od zmeny certu ~1.5 mes). WebView fetch GET i POST
        // proukazatelne chodi. credentials:same-origin = session cookie.
        fetch("/api/v1/erp/app/sms-inbound",{method:"POST",credentials:"same-origin",
          headers:{"Content-Type":"application/json"},body:JSON.stringify({from:num,body:body})})
          .then(function(r){ if(r&&r.ok){ try{ localStorage.setItem(key,"1"); }catch(e){} } })
          .catch(function(){});
      });
    }catch(e){}
  }
  // Odchozí SMS přes bránu (Kristý/Claude-24 23.6.): stáhne pending frontu ze
  // serveru, pošle přes B.sendSms a potvrdí. Jen bránový telefon (server hlídá).
  function _gwSmsOutbound(){
    try{
      if(!(B && typeof B.sendSms==="function")) return;
      var on=false; try{ on=!!(B.isSmsGateway&&B.isSmsGateway()); }catch(e){}
      if(!on) return;
      api("GET","/api/v1/erp/app/sms-outbound/pending","").then(function(j){
        if(!(j&&j.ok&&j.items&&j.items.length)) return;
        j.items.forEach(function(it){
          var r=""; try{ r=B.sendSms(it.to_phone, it.body); }catch(e){ r="0"; }
          if(r==="1"){ api("POST","/api/v1/erp/app/sms-outbound/sent",{id:it.id,ok:true}); }
          else { api("POST","/api/v1/erp/app/sms-outbound/sent",{id:it.id,ok:false,error:"sendSms="+r}); }
        });
      }).catch(function(){});
    }catch(e){}
  }
  try{ var _gwOn=false; try{ _gwOn=!!(native&&B&&B.isSmsGateway&&B.isSmsGateway()); }catch(e){}
       if(_gwOn){ _gwSmsForward(); setInterval(_gwSmsForward, 10000); _gwSmsOutbound(); setInterval(_gwSmsOutbound, 12000); } }catch(e){}
  // C27 21.7. — jednorazovy diagnosticky check-in pri startu appky: rekne
  // serveru KTERA verze JS bezi + stav SMS brany + pocet SMS v logu. Cte se z
  // public.phone_checkin_dbg. Az doladime SMS branu, tohle se odstrani.
  try{
    var _gw=false,_sln=-1;
    try{ _gw=!!(B&&B.isSmsGateway&&B.isSmsGateway()); }catch(e){}
    try{ if(B&&typeof B.getSmsLog==="function"){ var _sl=B.getSmsLog(''); var _pp=_sl?JSON.parse(_sl):null; _sln=(_pp&&_pp.sms)?_pp.sms.length:0; } }catch(e){}
    // dve cesty se ruznymi markery: 'chk-api' (nativni authedFetch) vs 'chk-raw' (WebView fetch)
    try{ api('POST','/api/v1/erp/app/phone-checkin',{v:'chk-api',native:!!native,gw:_gw,sl:_sln}); }catch(e){}
    try{ fetch('/api/v1/erp/app/phone-checkin',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify({v:'chk-raw',native:!!native,gw:_gw,sl:_sln})}); }catch(e){}
  }catch(e){}
    try{ _urgentPoll(); setInterval(_urgentPoll, 20000); }catch(e){}  // urgentní notifikace
  setTimeout(function(){ refreshUpdate(); renderNav(); }, 800);
  // Deep-link (Kristý/Claude-24 29.6.): …/mobile#ocr otevře rovnou OČR obrazovku.
  // Segment za lomítkem (#ocr/1) zatím ignorujeme — naviguje na obrazovku dle 1. části.
  try{
    var _dl=(location.hash||"").replace(/^#/,"").trim();
    if(_dl){ var _dseg=_dl.split("/")[0]; setTimeout(function(){ try{ go(_dseg); }catch(e){} }, 950); }
  }catch(e){}

  // Marti 5.7.: počet dokumentů čekajících na můj podpis → badge (Podpisy smluv / Aplikace / Domů) + karta na Domů.
  function signPendLoad(){
    api("GET","/api/v1/erp/app/sign/pending-count","").then(function(j){
      var n=(j&&j.ok)?(j.count||0):0;
      if(n!==_signPend){ _signPend=n; try{renderNav();}catch(e){}
        var top=stack[stack.length-1];
        if((curTab==="home"&&stack.length===1)||top==="apps"){ try{ render(); }catch(e){} }
      }
    }).catch(function(){});
  }
  // Živé načítání úkolů — ať se nová notifikace objeví v appce sama (Marti 6.6.2026).
  function pollNotifs(){
    try{ signPendLoad(); }catch(e){}   // počet dokumentů k podpisu
    try{ vyRefreshLive(); }catch(e){}   // živý refresh statusů konzole přes události
    // Marti 14.6.: badge Úkoly = plány ke schválení + schválené nepromítnuté korekce
    // (jen schvalovatelé, jinak 403→0).
    api("GET","/api/v1/erp/app/plan/approvals/users","").then(function(j){
      var n=(j&&j.ok)?(j.total||0):0;
      api("GET","/api/v1/erp/app/plan/approvals/unapplied","").then(function(u){
        var un=(u&&u.ok)?(u.count||0):0; var tot=n+un;
        if(tot!==_planApprovalCount){ _planApprovalCount=tot; renderNav(); }
      }).catch(function(){ if(n!==_planApprovalCount){ _planApprovalCount=n; renderNav(); } });
    }).catch(function(){});
    api("GET","/api/v1/erp/app/mobile/commands/pending","").then(function(j){
      if(j)markOk();
      var cmds=(j&&j.commands)||[]; var n=cmds.length; var changed=(n!==notifCount);
      notifCount=n; renderNav();
      // Obnov seznam jen na hlavní obrazovce nebo na záložce Úkoly (ne když je
      // uživatel zanořený v detailu) — žádné vyškubnutí z rozečtené zprávy.
      if(changed){
        var top=stack[stack.length-1];
        if((curTab==="home"&&stack.length===1)||top==="notifs"){ try{ render(); }catch(e){} }
      }
    }).catch(function(){});
  }
  setInterval(pollNotifs, 6000);
  try{ setTimeout(signPendLoad, 700); }catch(e){}   // Marti 5.7.: badge podpisů hned po startu
  setInterval(function(){ updateLive(); showDialCard(); }, 1000);
  // Při návratu do popředí (otevření z notifikace/launcheru) obnov hned.
  document.addEventListener("visibilitychange", function(){ if(!document.hidden){ refreshUpdate(); pollNotifs(); } });
  window.addEventListener("focus", function(){ refreshUpdate(); pollNotifs(); });

  // Auto-zachycení čísla telefonu ze SIM (Marti 6.6.) — ať se v párování číslo
  // ukáže samo, bez ručního kroku. Uloží jen když SIM číslo lze přečíst a změnilo se.
  function autoCapturePhone(){
    try{
      if(!(B&&typeof B.simNumber==="function"&&typeof B.deviceId==="function")) return;
      var sn=(B.simNumber()||"").trim();
      if(!sn || sn.replace(/[^0-9]/g,"").length<6) return;
      var last=""; try{last=localStorage.getItem("stg_saved_phone")||"";}catch(e){}
      if(sn===last) return;
      api("POST","/api/v1/erp/app/phone-set",{phone_number:sn,device_id:B.deviceId()}).then(function(j){
        if(j&&j.ok){ try{localStorage.setItem("stg_saved_phone",sn);}catch(e){} }
      }).catch(function(){});
    }catch(e){}
  }
  setTimeout(autoCapturePhone, 1500);

  // ── Nová verze → lišta nahoře, klik = HARD reload (Marti 7.6.) ──────────
  // Marti 7.6. večer fix „detail Not Found": reload AŽ když /mobile odpoví 200.
  // Hned po deployi se primární API restartuje (~5 s) a Caddy spadne na
  // secondary (starší snapshot bez /mobile) → 404 bílá obrazovka. Sondujeme.
  var _verLoaded=null;
  function _verHardReload(){
    var done=false, started=false;
    var bar=document.getElementById("verBar");
    function probe(tries){
      if(done) return;
      if(bar) bar.textContent="⏳ Obnovuji… (čekám na server)";
      fetch("/mobile",{cache:"no-store",credentials:"same-origin"}).then(function(r){
        if(r&&r.ok){ if(!done){ done=true; try{location.reload();}catch(e){location.href="/mobile";} } }
        else if(tries<10){ setTimeout(function(){probe(tries+1);},2000); }
        else if(!done){ done=true; try{location.reload();}catch(e){} }
      }).catch(function(){
        if(tries<10){ setTimeout(function(){probe(tries+1);},2000); }
        else if(!done){ done=true; try{location.reload();}catch(e){} }
      });
    }
    function go(){ if(started)return; started=true; probe(0); }
    try{
      var ps=[];
      if(window.caches&&caches.keys) ps.push(caches.keys().then(function(ks){ return Promise.all(ks.map(function(k){ return caches.delete(k); })); }));
      if(navigator.serviceWorker&&navigator.serviceWorker.getRegistrations) ps.push(navigator.serviceWorker.getRegistrations().then(function(rs){ return Promise.all(rs.map(function(r){ return r.update(); })); }));
      Promise.all(ps).then(go,go); setTimeout(go,2500);
    }catch(e){ go(); }
  }
  function _verTick(){
    try{
      fetch("/api/v1/erp/app-version",{cache:"no-store",credentials:"same-origin"})
        .then(function(r){ return r.ok?r.json():null; })
        .then(function(j){
          var v=j&&j.version; if(!v||v==="unknown")return;
          if(_verLoaded===null){ _verLoaded=v; return; }
          if(v!==_verLoaded && !document.getElementById("verBar")){
            var b=el('<div id="verBar" style="position:fixed;top:74px;left:10px;right:10px;z-index:90;background:#3a2f12;border:1px solid #6e5326;border-radius:10px;box-shadow:0 6px 18px rgba(0,0,0,.4);color:#f0d98a;padding:11px 14px;font-size:13.5px;text-align:center;cursor:pointer;">🔄 Nová verze STRATEGIE — klepni pro obnovení</div>');
            b.addEventListener("click",_verHardReload); document.body.appendChild(b);
          }
        }).catch(function(){});
    }catch(e){}
  }
  setInterval(_verTick, 30000); setTimeout(_verTick, 1200);
})();
