  function home(){
    app.innerHTML = "";
    var ls = listenState();
    var bg = el('<div class="homebg"></div>');
    bg.style.backgroundImage = "linear-gradient(rgba(14,15,17,.05), rgba(14,15,17,.86)), url('"+avatarUrl+"')";
    // Marti 8.6.: ověřovací karta NAD nadpisem — „STRATEGIE Mobil" je pinned dole.
    bg.innerHTML = '<div id="homeDialCard"></div><div id="urgentSent"></div><div id="homeNotifsWrap"></div>'
      + '<div id="homeVerify"></div>'
      + '<div style="display:flex;align-items:flex-start;justify-content:space-between;gap:10px;">'
      +   '<div class="h1" id="homeTitle" style="font-family:\'DM Sans\',\'Galano Grotesque\',\'Montserrat\',sans-serif;font-weight:800;letter-spacing:-0.5px;background:linear-gradient(135deg,#4f8ef7,#7c5cfc);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;">STRATEGIE Mobil</div>'
      +   '<div id="homeWho" style="text-align:right;margin-top:4px;flex-shrink:0;line-height:1.35;">'
      +     '<div id="homeWhoName" style="font-weight:700;font-size:16px;"></div>'
      +     '<div id="homeWhoLabel" style="color:var(--mut);font-size:12px;"></div>'
      +     '<div id="homeWhoPhone" style="color:var(--mut);font-size:12px;"></div>'
      +   '</div>'
      + '</div>'
      + '<div class="h2">'+(nativeApp?"Nativní appka":"Prohlížeč (PWA)")+(DEV?" · DEV":"")+'</div>'
      + '<div class="h3" id="homeLive"></div>';
    app.appendChild(bg);
    try{ _urgentSentRender(); }catch(e){}  // indikátor běžících urgentních požadavků
    // Marti 8.6. ráno: identifikace telefonu — jméno i label ZE SERVERU
    // (fw.mobile_device = oficiální tabulka zařízení). Na main screen se NEmění.
    // Neověřené číslo → pulzující karta „Ověř číslo" hned po spárování.
    (function(){
      var dev=""; try{ if(B&&typeof B.deviceId==="function") dev=B.deviceId()||""; }catch(e){}
      api("GET","/api/v1/erp/app/whoami"+(dev?("?device_id="+encodeURIComponent(dev)):""),"").then(function(w){
        var n=document.getElementById("homeWhoName"), lb=document.getElementById("homeWhoLabel"), ph=document.getElementById("homeWhoPhone");
        if(n&&w&&w.jmeno) n.textContent=w.jmeno;
        if(lb) lb.textContent=(w&&w.label)||"";
        if(ph) ph.textContent=(w&&w.phone_verified&&w.phone)?w.phone:"";
        if(dev && w && w.ok && !w.phone_verified) _phoneVerifyCard(dev);
        if(!(w && w.jmeno)){ var hv=document.getElementById("homeVerify"); if(hv) renderGuestWelcome(hv); }
      });
    })();
    updateLive();
    showDialCard();
    // Pozastavené párování → ťuknutí na titulek nabídne spuštění (potvrzení).
    var ttl=document.getElementById("homeTitle");
    if(ttl && canListen && listenState()===false){
      ttl.style.cursor="pointer";
      ttl.addEventListener("click",function(){
        confirmDialog("Párování pozastaveno","Spustit párování s ERP? Telefon začne přijímat vytáčení a úkoly.","▶️ Spustit párování",function(){
          try{ B.startListening(); }catch(e){}
          setTimeout(function(){ render(); },900);
        });
      });
    }
    loadHomeNotifs();
  }
  // Prohlídkový režim (Marti 9.6.2026): nepřihlášený host — vlídné uvítání,
  // spárování, a lead capture (PR funnel pro širokou veřejnost).
  function renderGuestWelcome(box){
    box.innerHTML="";
    var card=el('<div style="background:linear-gradient(135deg,rgba(79,142,247,.14),rgba(124,92,252,.14));border:1px solid #2a4d80;border-radius:14px;padding:14px;margin-bottom:12px;"></div>');
    card.appendChild(el('<div style="font-weight:800;font-size:17px;margin-bottom:4px;">STRATEGIE 🌳</div>'));
    card.appendChild(el('<div style="color:#cdd8e6;font-size:13.5px;line-height:1.55;margin-bottom:10px;">Podnikový systém pro firmy — docházka, lidé, výroba a dokumenty na jednom místě. Vyzkoušej si ukázku, nebo se přihlas, pokud STRATEGII tvoje firma používá.</div>'));
    var btns=el('<div style="display:flex;flex-direction:column;gap:8px;"></div>');
    var bDemo=el('<button class="green full" style="margin:0;">▶️ Vyzkoušet ukázku</button>');
    bDemo.addEventListener("click",function(){ location.href="/api/v1/auth/demo-login?next=/mobile"; });
    var bPwd=el('<button class="ghost full" style="margin:0;">🔑 Přihlásit heslem</button>');
    bPwd.addEventListener("click",openPasswordLogin);
    var bPair=el('<button class="ghost full" style="margin:0;">🔗 Přihlásit odkazem / spárovat telefon</button>');
    bPair.addEventListener("click",function(){ location.href="/api/v1/auth/sms-login?next=/mobile"; });
    var bLead=el('<button class="ghost full" style="margin:0;">💬 Mám zájem — ozvěte se mi</button>');
    bLead.addEventListener("click",openLeadForm);
    btns.appendChild(bDemo); btns.appendChild(bPwd); btns.appendChild(bPair); btns.appendChild(bLead); card.appendChild(btns);
    box.appendChild(card);
  }
  // Přihlášení e-mailem + heslem (záloha k magic-linku; iOS magic-link otevře
  // Safari, recenzent i běžný uživatel tak uvízne mimo appku). POST /auth/login
  // nastaví cookie session → reload do appky. Demo zůstává jako bezloginová cesta.
  function openPasswordLogin(){
    var ov=el('<div style="position:fixed;inset:0;background:rgba(4,10,18,.97);z-index:300;display:flex;flex-direction:column;justify-content:center;padding:24px;gap:10px;"></div>');
    ov.appendChild(el('<div style="font-weight:800;font-size:19px;">Přihlášení heslem 🔑</div>'));
    ov.appendChild(el('<div class="hint" style="line-height:1.55;">Zadej e-mail a heslo svého účtu STRATEGIE.</div>'));
    var em=el('<input type="email" inputmode="email" autocapitalize="off" autocomplete="username" placeholder="E-mail" style="margin:0;">');
    var pw=el('<input type="password" autocomplete="current-password" placeholder="Heslo" style="margin:0;">');
    var st=el('<div class="hint" style="min-height:16px;"></div>');
    var send=el('<button class="green full" style="margin:0;">Přihlásit se</button>');
    var cl=el('<button class="ghost full" style="margin:0;">Zavřít</button>');
    cl.addEventListener("click",function(){ ov.remove(); });
    function doLogin(){
      var e=(em.value||"").trim(), p=(pw.value||"");
      if(!e||!p){ st.textContent="Doplň prosím e-mail i heslo."; return; }
      send.disabled=true; st.textContent="Přihlašuji…";
      fetch("/api/v1/auth/login",{method:"POST",headers:{"Content-Type":"application/json"},
        body:JSON.stringify({email:e,password:p})})
        .then(function(r){ return r.json().then(function(b){ return {ok:r.ok,status:r.status,body:b}; }); })
        .then(function(r){
          if(r.ok){ st.textContent="Hotovo ✅"; location.href="/mobile"; return; }
          send.disabled=false;
          var d=r.body&&r.body.detail;
          var msg = (d&&typeof d==="object"&&d.message) ? d.message
                  : (typeof d==="string"?d:"Přihlášení se nezdařilo.");
          if(r.status===401) msg="Neplatný e-mail nebo heslo.";
          if(r.status===429) msg=(typeof d==="string"?d:"Příliš mnoho pokusů. Zkus to prosím za chvíli.");
          st.textContent=msg;
        })
        .catch(function(){ send.disabled=false; st.textContent="Nepovedlo se. Zkus to prosím znovu."; });
    }
    send.addEventListener("click",doLogin);
    pw.addEventListener("keydown",function(ev){ if(ev.key==="Enter") doLogin(); });
    ov.appendChild(em); ov.appendChild(pw); ov.appendChild(st); ov.appendChild(send); ov.appendChild(cl);
    app.appendChild(ov);
  }
  function openLeadForm(){
    var ov=el('<div style="position:fixed;inset:0;background:rgba(4,10,18,.97);z-index:300;display:flex;flex-direction:column;justify-content:center;padding:24px;gap:10px;"></div>');
    ov.appendChild(el('<div style="font-weight:800;font-size:19px;">Nech nám na sebe kontakt 💬</div>'));
    ov.appendChild(el('<div class="hint" style="line-height:1.55;">Zaujalo tě to? Napiš jméno a telefon nebo e‑mail — ozveme se ti. Odesláním souhlasíš, že tě smíme kontaktovat.</div>'));
    var nm=el('<input placeholder="Tvoje jméno" autocomplete="name" style="margin:0;">');
    var ct=el('<input placeholder="Telefon nebo e‑mail" autocomplete="tel" style="margin:0;">');
    var ms=el('<textarea rows="2" placeholder="Vzkaz (nepovinné)…" style="width:100%;background:#0f1620;border:1px solid var(--bord);border-radius:10px;padding:10px;color:var(--tx);font-family:inherit;font-size:14px;"></textarea>');
    var st=el('<div class="hint" style="min-height:16px;"></div>');
    var send=el('<button class="green full" style="margin:0;">Odeslat</button>');
    var cl=el('<button class="ghost full" style="margin:0;">Zavřít</button>');
    cl.addEventListener("click",function(){ ov.remove(); });
    send.addEventListener("click",function(){
      var c=(ct.value||"").trim();
      if(!c){ st.textContent="Doplň prosím telefon nebo e‑mail."; return; }
      send.disabled=true; st.textContent="Odesílám…";
      var dk=""; try{ if(B&&typeof B.deviceId==="function") dk=B.deviceId()||""; }catch(e){}
      fetch("/api/v1/erp/app/lead",{method:"POST",headers:{"Content-Type":"application/json"},
        body:JSON.stringify({channel:"interest",name:(nm.value||"").trim(),contact:c,message:(ms.value||"").trim(),device_key:dk})})
        .then(function(r){return r.json();}).then(function(r){
          if(r&&r.ok){ ov.innerHTML='<div style="text-align:center;margin:auto;"><div style="font-size:44px;">✅</div><div style="font-weight:800;font-size:18px;margin-top:8px;">Děkujeme!</div><div class="hint" style="margin-top:6px;">Ozveme se ti co nejdřív. 🌳</div></div>'; setTimeout(function(){ov.remove();},2400); }
          else { send.disabled=false; st.textContent=((r&&r.error)||"Nepovedlo se. Zkus to prosím znovu."); }
        }).catch(function(){ send.disabled=false; st.textContent="Nepovedlo se. Zkus to prosím znovu."; });
    });
    ov.appendChild(nm); ov.appendChild(ct); ov.appendChild(ms); ov.appendChild(st); ov.appendChild(send); ov.appendChild(cl);
    app.appendChild(ov);
  }
  function loadHomeNotifs(){
    var box=document.getElementById("homeNotifsWrap"); if(!box)return;
    var upd=null; try{ if(B&&typeof B.checkUpdate==="function"){ var t=B.checkUpdate(); if(t)upd=JSON.parse(t); } }catch(e){}
    _hasUpdate=!!(upd&&upd.has_update);
    api("GET","/api/v1/erp/app/mobile/commands/pending","").then(function(j){
      if(j)markOk();
      var cmds=(j&&j.commands)||[]; notifCount=cmds.length; renderNav();
      box.innerHTML="";
      if(upd&&upd.has_update){
        var ru=el('<div class="homenotif"><div class="ic">🆕</div><div style="flex:1;min-width:0;"><div style="font-weight:600;">Nová verze STRATEGIE</div><div style="color:var(--mut);font-size:12px;">'+esc(upd.latest_name||"")+' — klepni pro aktualizaci</div></div><div class="chev">&#8250;</div></div>');
        ru.addEventListener("click",function(){ curTab="settings"; stack=["settings","set_about"]; render(); }); box.appendChild(ru);
      }
      if(_signPend>0){
        var sc=el('<div class="homenotif" style="background:rgba(37,42,64,.92);border-color:#4b5a8a;"><div class="ic">✍️</div><div style="flex:1;min-width:0;"><div style="font-weight:600;">'+_signPend+' '+(_signPend===1?"dokument k podpisu":(_signPend>=2&&_signPend<=4?"dokumenty k podpisu":"dokumentů k podpisu"))+'</div><div style="color:var(--mut);font-size:12px;">Klepni pro podpisový modul</div></div><div class="chev">&#8250;</div></div>');
        sc.addEventListener("click",function(){ openInApp("/podpisy"); }); box.appendChild(sc);
      }
      cmds.forEach(function(c){
        var r=el('<div class="homenotif"><div class="ic">'+CLAUDE_SVG.replace('width="26" height="26"','width="22" height="22"')+'</div><div style="flex:1;min-width:0;"><div style="font-weight:600;">'+esc(c.title||"Claude")+'</div><div style="color:var(--mut);font-size:12px;">'+esc((c.message||"").slice(0,60))+'</div></div><div class="chev">&#8250;</div></div>');
        r.addEventListener("click",function(){ curTab="notifs"; stack=["notifs","claudetasks"]; render(); }); box.appendChild(r);
      });
      // žádné notifikace → wrap zůstane prázdný (neviditelný)
    });
  }

  // ───── TELEFON ─────
  function phone(){
    app.innerHTML = topbar("Telefon", false);
    var p=el('<div class="panel"></div>');
    if(canDial||DEV){
      p.appendChild(el('<label>Telefonní číslo</label>'));
      var inp=el('<input id="num" type="tel" inputmode="tel" placeholder="+420…" value="+420">'); p.appendChild(inp);
      var btn=el('<button class="green full">Vytočit</button>'); var info=el('<div class="devinfo" style="display:none;"></div>');
      btn.addEventListener("click",function(){ var n=(inp.value||"").trim(); if(!n)return;
        if(canDial){ doDial(n); if(DEV){info.textContent="✓ Most: dialNumber(\""+n+"\") → ACTION_DIAL.";info.style.display="block";} }
        else { info.textContent="DEV (bez mostu): dialNumber(\""+n+"\") → v appce spustí ACTION_DIAL. Nativní-only.";info.style.display="block"; } });
      p.appendChild(btn); p.appendChild(info);
    } else { p.appendChild(el('<div class="hint">Vytáčení je nativní funkce — funguje v appce STRATEGIE.</div>')); }
    var ls=listenState();
    p.appendChild(el('<div class="group">Další</div>'));
    var sl=el('<div class="list"></div>');
    sl.appendChild(row("🟢","Párování s ERP", ls==null?"(zjistí se v appce)":(ls?"aktivní":"pozastaveno"), function(){go("set_listen");}));
    sl.appendChild(row("🕓","Historie hovorů","Prefixy: "+getPrefixes(), function(){go("calllog");}));
    p.appendChild(sl); app.appendChild(p);
  }

  // ───── ÚKOLY / NOTIFIKACE ─────
  var _afterAct=false;
  function act(id,decision,li){
    _afterAct=true;
    // Optimisticky odeber kartu hned — ať OK reaguje i když síť/POST zlobí.
    try{ if(li&&li.parentNode){ li.parentNode.removeChild(li); } }catch(e){}
    if(notifCount>0){ notifCount--; renderNav(); }
    api("POST","/api/v1/erp/app/command/"+id+"/result",{decision:decision}).then(notifsLoad).catch(function(){});
  }
  function notifsLoad(){ var ul=document.getElementById("ntlist"); if(!ul)return;
    api("GET","/api/v1/erp/app/mobile/commands/pending","").then(function(j){
      var wasAct=_afterAct; _afterAct=false;
      if(!j){ ul.innerHTML='<li style="color:var(--mut);border:none;">Přihlas se (prohlížeč) nebo otevři v appce.</li>'; return; }
      var cmds=j.commands||[]; notifCount=cmds.length;
      if(!cmds.length){ if(wasAct){ renderNav(); selectTab("home"); return; } ul.innerHTML='<li style="color:var(--mut);border:none;">Žádné čekající úkoly ✓</li>'; return; }
      ul.innerHTML="";
      cmds.forEach(function(c){
        var li=el('<li></li>');
        var isDoch=(c.title||"").indexOf("Potvrď si docházku")>=0;
        var hint=isDoch?'<div style="color:var(--blue);font-size:12px;">klepni → otevřít docházku k potvrzení</div>'
                       :(c.message&&c.message.length>120?'<div style="color:var(--blue);font-size:12px;">klepni pro celé…</div>':'');
        var txt=el('<div style="cursor:pointer;"><div class="nt">'+esc(c.title||"Úkol")+'</div>'+(c.message?'<div class="nm" style="max-height:60px;overflow:hidden;">'+esc(c.message)+'</div>':'')+hint+'</div>');
        txt.addEventListener("click",function(){ if(isDoch){ go("dochazka"); } else { openClaudeDetail(c); } });
        var a=el('<div class="nactions" style="margin-top:8px;"></div>');
        function b(l,cl,d){var x=el('<button class="sm '+cl+'">'+l+'</button>'); x.addEventListener("click",function(e){e.stopPropagation();act(c.id,d,li);}); a.appendChild(x);}
        if(c.command_type==="claude_confirm"){b("Odmítnout","warn","reject");b("Povolit","green","accept");}
        else if(isDoch){
          var ob=el('<button class="sm green">🖊 Otevřít docházku →</button>');
          ob.addEventListener("click",function(e){e.stopPropagation();go("dochazka");}); a.appendChild(ob);
        }
        else {
          var rb=el('<button class="sm green">💬 Odpovědět</button>');
          rb.addEventListener("click",function(e){e.stopPropagation();replyMsg(c,li);}); a.appendChild(rb);
          b("OK","ghost","done");
        }
        li.appendChild(txt); li.appendChild(a); ul.appendChild(li); }); }); }
  function replyMsg(c,li){
    if(li.querySelector(".replywrap"))return;
    var wrap=el('<div class="replywrap" style="margin-top:8px;"></div>');
    var ta=el('<textarea placeholder="Tvoje odpověď Claudovi…" style="width:100%;min-height:64px;background:#141b29;color:#e8edf6;border:1px solid #2a3547;border-radius:8px;padding:8px;font-size:14px;box-sizing:border-box;"></textarea>');
    var sb=el('<button class="sm green" style="margin-top:6px;">Odeslat</button>');
    var st=el('<span style="margin-left:8px;color:var(--mut);font-size:12px;"></span>');
    wrap.appendChild(ta); wrap.appendChild(sb); wrap.appendChild(st);
    li.appendChild(wrap); try{ta.focus();}catch(e){}
    sb.addEventListener("click",function(ev){ ev.stopPropagation();
      var t=(ta.value||"").trim(); if(!t){ta.focus();return;}
      sb.disabled=true; st.textContent="Odesílám…";
      api("POST","/api/v1/erp/app/notif/reply",{id:c.id,text:t}).then(function(r){
        if(r&&r.ok){ st.textContent="✓ Odesláno Claudovi"; if(notifCount>0){notifCount--;renderNav();}
          setTimeout(function(){ try{li.parentNode.removeChild(li);}catch(e){} if(!document.querySelectorAll('#ntlist li').length){selectTab('home');} },600); }
        else { st.textContent="Chyba: "+((r&&r.error)||"?"); sb.disabled=false; }
      }).catch(function(){ st.textContent="Chyba sítě"; sb.disabled=false; });
    });
  }
  function notifs(){ // dashboard s dlaždicemi
    app.innerHTML=topbar("", false); var p=el('<div class="panel"></div>');
    var grid=el('<div class="dashgrid"></div>');
    var ct=el('<div class="tile" style="position:relative;"><div class="tile-ic">'+CLAUDE_SVG+'</div><div class="tile-tt">Claude</div><div class="tile-sub" id="claudeSub">…</div><span id="claudeBadge" style="display:none;position:absolute;top:8px;right:8px;background:#e0483d;color:#fff;border-radius:11px;min-width:22px;height:22px;line-height:22px;text-align:center;font-size:12px;font-weight:700;padding:0 6px;box-shadow:0 1px 4px rgba(0,0,0,.35);"></span></div>');
    ct.addEventListener("click",function(){go("claudetasks");}); grid.appendChild(ct);
    var tt=el('<div class="tile" style="position:relative;"><div class="tile-ic">📝</div><div class="tile-tt">Moje TODO</div><div class="tile-sub" id="todoSub">…</div></div>');
    tt.addEventListener("click",function(){go("strtask");}); grid.appendChild(tt);
    var ut=el('<div class="tile"><div class="tile-ic">📋</div><div class="tile-tt">Úkoly</div><div class="tile-sub">Z Centrály</div></div>');
    ut.addEventListener("click",function(){go("ecukoly");}); grid.appendChild(ut);
    var bt=el('<div class="tile"><div class="tile-ic">🎁</div><div class="tile-tt">Benefity</div><div class="tile-sub">Home office / oblečení</div></div>');
    bt.addEventListener("click",function(){ openApp("/benefity"); }); grid.appendChild(bt);
    // Schvalování návrhů plánu — viditelné jen pro schvalovatele (jinak 403 → skryto).
    var ap=el('<div class="tile" style="position:relative;display:none;"><div class="tile-ic">🗓️</div><div class="tile-tt">Schvalování</div><div class="tile-sub" id="apSub">…</div><span id="apBadge" style="display:none;position:absolute;top:8px;right:8px;background:#f59e0b;color:#fff;border-radius:11px;min-width:22px;height:22px;line-height:22px;text-align:center;font-size:12px;font-weight:700;padding:0 6px;box-shadow:0 1px 4px rgba(0,0,0,.35);"></span></div>');
    ap.addEventListener("click",function(){go("planapprovals");}); grid.appendChild(ap);
    api("GET","/api/v1/erp/app/plan/approvals/users","").then(function(j){
      if(!j||!j.ok){ _planApprovalCount=0; return; }
      ap.style.display="";
      var n=j.total||0;
      api("GET","/api/v1/erp/app/plan/approvals/unapplied","").then(function(u){
        var un=(u&&u.ok)?(u.count||0):0; var tot=n+un;
        _planApprovalCount=tot; renderNav();
        var sub=document.getElementById("apSub");
        if(sub)sub.textContent=tot?((n?n+" ke schválení":"")+(n&&un?" · ":"")+(un?un+" k promítnutí":"")):"Nic nečeká";
        var bd=document.getElementById("apBadge"); if(bd){ if(tot>0){ bd.textContent=tot>99?"99+":tot; bd.style.display="block"; } else bd.style.display="none"; }
      }).catch(function(){ _planApprovalCount=n; renderNav(); });
    }).catch(function(){});
    p.appendChild(grid); app.appendChild(p);
    api("GET","/api/v1/erp/app/mobile/commands/pending","").then(function(j){ notifCount=j&&j.commands?j.commands.length:0; var s=document.getElementById("claudeSub"); if(s)s.textContent=notifCount?(notifCount+" ke schválení / nové"):"Žádné nové"; var bd=document.getElementById("claudeBadge"); if(bd){ if(notifCount>0){ bd.textContent=notifCount>99?"99+":notifCount; bd.style.display="block"; } else bd.style.display="none"; } renderNav(); });
    (function(){ var s0=document.getElementById("todoSub"); var dr=false; try{dr=!!localStorage.getItem("stg_task_draft");}catch(e){} if(s0&&dr)s0.textContent="✏️ rozpracované…"; })();
    api("GET","/api/v1/erp/app/task?view=moje","").then(function(j){ var n=((j&&j.ukoly)||[]).length; var s=document.getElementById("todoSub"); var dr=false; try{dr=!!localStorage.getItem("stg_task_draft");}catch(e){} if(s)s.textContent=(dr?"✏️ rozpracované · ":"")+(n?(n+" k vyřízení"):"nic nového"); }); }
  // ───── Schvalování návrhů plánu (pro schvalovatele). Marti 14.6. ─────
  function apCzd(iso){ var p=(iso||"").split("-"); return p.length===3?(p[2]+"."+p[1]+"."+p[0]):iso; }
  function apKLabel(r){
    if(r.kind==='off') return '🏝️ volno';
    if(r.kind==='meeting') return '🤝 '+(r.title||'Porada/jednání')+(r.start?(' '+r.start):'')+(r.end?('–'+r.end):'');
    return (r.start?('od '+r.start+' · '):'')+((r.hours!=null)?(r.hours+' h'):'změna');
  }
  function planapprovals(){
    app.innerHTML=topbar("🗓️ Schvalování plánu", true, true);
    var _tb=app.querySelector('.topbar'); if(_tb)_tb.style.paddingTop="12px";
    var wrap=el('<div style="display:flex;gap:8px;height:calc(100vh - 165px);padding:4px 2px 0;"></div>');
    var left=el('<div id="apleft" style="flex:1;min-width:0;min-height:0;display:flex;flex-direction:column;overflow:hidden;"></div>');
    var rail=el('<div id="aprail" style="width:64px;flex:none;overflow-y:auto;display:flex;flex-direction:column;gap:5px;padding:1px;"></div>');
    rail.appendChild(el('<button style="margin:0;padding:6px 1px;font-size:10px;line-height:1.1;display:flex;flex-direction:column;align-items:center;gap:2px;border:1px solid var(--blue);background:var(--blue);color:#fff;border-radius:9px;cursor:default;"><span style="font-size:17px;">👥</span>Lidé</button>'));
    var rr=el('<button style="margin:0;padding:6px 1px;font-size:10px;line-height:1.1;display:flex;flex-direction:column;align-items:center;gap:2px;border:1px solid var(--bord);background:transparent;color:var(--mut);border-radius:9px;cursor:pointer;"><span style="font-size:17px;">🔄</span>Obnovit</button>');
    rr.addEventListener("click",function(){ apLoad(); });
    rail.appendChild(rr);
    wrap.appendChild(left); wrap.appendChild(rail); app.appendChild(wrap);
    apLoad();
  }
  function apLoad(){
    var L=document.getElementById("apleft"); if(!L)return;
    L.innerHTML='<div class="hint" style="padding:12px;">Načítám…</div>';
    api("GET","/api/v1/erp/app/plan/approvals/users","").then(function(j){
      L.innerHTML="";
      if(!j||!j.ok){ L.innerHTML='<div class="hint" style="padding:14px;">'+esc((j&&j.error==='forbidden')?"Nemáš oprávnění schvalovat.":((j&&j.error)||"Nepodařilo se načíst."))+'</div>'; return; }
      var users=j.users||[];
      _apUnappliedBar(L);   // pojistka: nepromítnuté schválené korekce
      var lw=el('<div style="flex:1;min-height:0;overflow-y:auto;-webkit-overflow-scrolling:touch;padding-bottom:24px;"></div>');
      if(!users.length){ lw.innerHTML='<div class="hint" style="padding:14px;line-height:1.6;">Nic nečeká na schválení. 👍</div>'; L.appendChild(lw); return; }
      var ul=el('<ul class="list" style="padding:0 6px;"></ul>');
      users.forEach(function(u){
        var li=el('<li class="ct" style="padding:0;border-bottom:none;cursor:pointer;"></li>');
        var head=el('<div class="cthead"><div class="cav" style="background:'+avColor(u.name||"?")+';">'+esc((u.name||"?").trim().charAt(0).toUpperCase())+'</div><div style="flex:1;min-width:0;"><div class="ctname">'+esc(u.name||("#"+u.user_id))+'</div><div class="ctnum">'+u.cnt+' ke schválení · klepni pro kalendář</div></div><span style="flex:none;background:#f59e0b;color:#fff;border-radius:11px;min-width:22px;height:22px;line-height:22px;text-align:center;font-size:12px;font-weight:700;padding:0 6px;">'+u.cnt+'</span></div>');
        head.addEventListener("click",function(){ window._planApprove={user_id:u.user_id, name:(u.name||("#"+u.user_id))}; go("plan"); });
        li.appendChild(head); ul.appendChild(li);
      });
      lw.appendChild(ul); L.appendChild(lw);
    }); }
  function _apUnappliedBar(L){
    api("GET","/api/v1/erp/app/plan/approvals/unapplied","").then(function(u){
      var old=document.getElementById("apUnapBar"); if(old)old.remove();
      if(!u||!u.ok) return; var c=u.count||0; if(c<=0) return;
      var host=document.getElementById("apleft"); if(!host) return;
      var bar=el('<div id="apUnapBar" style="background:rgba(245,158,11,.15);border:1px solid #b6791f;border-radius:12px;padding:10px 12px;margin:0 6px 10px;display:flex;align-items:center;gap:10px;"></div>');
      bar.appendChild(el('<div style="flex:1;font-size:13px;color:#f3c969;line-height:1.4;">⚠ '+c+' schválených korekcí čeká na promítnutí do plánu.</div>'));
      var b=el('<button class="green" style="margin:0;padding:8px 12px;font-size:13px;flex:none;">Promítnout</button>');
      b.addEventListener("click",function(){ b.disabled=true; b.textContent="Promítám…"; api("POST","/api/v1/erp/app/plan/approvals/reapply",{}).then(function(r){ if(r&&r.ok){ apLoad(); } else { b.disabled=false; b.textContent="Promítnout"; alert("Chyba: "+((r&&r.error)||"?")); } }); });
      bar.appendChild(b);
      host.insertBefore(bar, host.firstChild);
    }).catch(function(){});
  }
  function apFillUser(exp,u){
    exp.innerHTML='<div class="hint" style="padding:8px;">Načítám…</div>';
    api("GET","/api/v1/erp/app/plan/approvals/user/"+u.user_id,"").then(function(j){
      exp.innerHTML="";
      if(!j||!j.ok){ exp.innerHTML='<div class="hint" style="padding:8px;">Nepodařilo se načíst.</div>'; return; }
      var items=j.items||[];
      if(!items.length){ exp.innerHTML='<div class="hint" style="padding:8px;">Nic nečeká.</div>'; return; }
      items.forEach(function(r){
        var row=el('<div style="padding:9px 6px;border-top:1px solid var(--bord);"></div>');
        row.appendChild(el('<div style="font-size:14px;margin-bottom:6px;"><b>'+esc(apCzd(r.d))+'</b> · '+esc(apKLabel(r))+(r.note?(' <span class="hint">— '+esc(r.note)+'</span>'):'')+'</div>'));
        var br=el('<div style="display:flex;gap:8px;"></div>');
        var ya=el('<button class="green" style="flex:1;margin:0;padding:8px;">✅ Schválit</button>');
        var na=el('<button class="ghost" style="flex:1;margin:0;padding:8px;color:#f87171;border-color:#5a2b2b;">🚫 Zamítnout</button>');
        ya.addEventListener("click",function(){ ya.disabled=true; na.disabled=true; apDecide(r.id,"approved",null); });
        na.addEventListener("click",function(){ apRejectDialog(r); });
        br.appendChild(ya); br.appendChild(na); row.appendChild(br);
        exp.appendChild(row);
      });
    }); }
  function apDecide(id,decision,note){
    api("POST","/api/v1/erp/app/plan/decide",{id:id,decision:decision,note:note||""}).then(function(r){
      if(r&&r.ok){ apLoad(); } else alert("Chyba: "+((r&&r.error)||"?")); });
  }
  function apRejectDialog(r, onReject){
    var ov=el('<div class="appmodal" style="position:fixed;inset:0;z-index:99999;background:rgba(3,7,16,.66);display:flex;align-items:center;justify-content:center;padding:24px;"></div>');
    var card=el('<div style="background:#161c2b;border:1px solid rgba(255,255,255,.12);border-radius:16px;padding:20px;max-width:340px;width:100%;box-shadow:0 16px 50px rgba(0,0,0,.55);"></div>');
    card.appendChild(el('<div style="font-size:16px;font-weight:600;color:#e8eefc;margin-bottom:6px;">Zamítnout návrh</div>'));
    card.appendChild(el('<div class="hint" style="margin-bottom:10px;">'+esc(apCzd(r.d))+' · '+esc(apKLabel(r))+'</div>'));
    var ta=el('<textarea placeholder="Důvod (nepovinné)…" style="width:100%;min-height:64px;margin-bottom:14px;box-sizing:border-box;"></textarea>');
    card.appendChild(ta);
    var rowb=el('<div style="display:flex;gap:10px;"></div>');
    var no=el('<button class="ghost" style="flex:1;margin:0;">Zrušit</button>');
    var yes=el('<button class="green" style="flex:1;margin:0;background:#b3402f;">🚫 Zamítnout</button>');
    no.addEventListener("click",function(){ ov.remove(); });
    yes.addEventListener("click",function(){ ov.remove(); var nt=(ta.value||"").trim(); if(onReject){ onReject(nt); } else { apDecide(r.id,"rejected",nt); } });
    rowb.appendChild(no); rowb.appendChild(yes); card.appendChild(rowb);
    ov.appendChild(card); document.body.appendChild(ov);
  }
