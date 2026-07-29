  function skupiny(){
    app.innerHTML=topbar("👥 Skupiny", true, true);
    var _tb=app.querySelector('.topbar'); if(_tb) _tb.style.paddingTop="12px";
    var wrap=el('<div style="display:flex;gap:8px;height:calc(100vh - 100px - var(--navh, 65px));padding:4px 2px 0;"></div>');
    var left=el('<div id="skleft" style="flex:1;min-width:0;min-height:0;display:flex;flex-direction:column;overflow:hidden;"></div>');
    var rail=el('<div id="skrail" style="width:64px;flex:none;overflow-y:auto;display:flex;flex-direction:column;gap:5px;padding:1px;"></div>');
    wrap.appendChild(left); wrap.appendChild(rail); app.appendChild(wrap);
    skLoadGroups();
  }
  function skBtn(g){
    var on=(_skView===g.id);
    var b=el('<button data-g="'+g.id+'" style="position:relative;margin:0;padding:6px 1px;font-size:10px;line-height:1.1;display:flex;flex-direction:column;align-items:center;gap:2px;border:1px solid '+(on?"var(--green)":"var(--bord)")+';background:'+(on?"var(--green)":"transparent")+';color:'+(on?"#04150e":"var(--mut)")+';border-radius:9px;cursor:pointer;"><span style="font-size:18px;">'+esc(g.icon||"👥")+'</span>'+esc(g.name)+(g.count?'<span class="vybadge" style="display:block;background:var(--blue);color:#fff;">'+g.count+'</span>':'')+'</button>');
    b.addEventListener("click",function(){ _skView=g.id; skLoadMembers(); skPaintRail(); });
    return b;
  }
  function skPaintRail(){
    var r=document.getElementById("skrail"); if(!r)return; r.innerHTML="";
    _skGroups.forEach(function(g){ r.appendChild(skBtn(g)); });
    r.appendChild(el('<div style="flex:1 1 auto;min-height:8px;"></div>'));
    var add=el('<button style="margin:0;padding:8px 1px;font-size:11px;line-height:1.1;display:flex;flex-direction:column;align-items:center;gap:2px;border:1px dashed var(--blue);background:transparent;color:var(--blue);border-radius:9px;cursor:pointer;"><span style="font-size:18px;">➕</span>Nová</button>');
    add.addEventListener("click",skNewGroup); r.appendChild(add);
  }
  function skLoadGroups(){
    api("GET","/api/v1/erp/app/skupiny","").then(function(j){
      var L=document.getElementById("skleft");
      if(!j||!j.ok){ if(L)L.innerHTML='<div class="hint" style="padding:14px;">'+((j&&j.error)==="forbidden"?"Skupiny spravují jen rodiče.":"Nepodařilo se načíst.")+'</div>'; return; }
      _skGroups=j.skupiny||[]; skPaintRail();
      if(window._skFocusName){ var _fg=_skGroups.filter(function(g){return (g.name||'')===window._skFocusName;})[0]; if(_fg)_skView=_fg.id; window._skFocusName=null; }
      if(_skView && !_skGroups.some(function(g){return g.id===_skView;})) _skView=null;
      if(!_skView && _skGroups.length) _skView=_skGroups[0].id;
      if(_skView){ skPaintRail(); skLoadMembers(); } else skRenderEmpty();
    });
  }
  function skRenderEmpty(){ var L=document.getElementById("skleft"); if(L)L.innerHTML='<div class="hint" style="padding:18px 12px;line-height:1.7;">Zatím žádná skupina.<br>Přidej první přes <b>➕ Nová</b> vpravo dole.</div>'; }
  function skLoadMembers(){
    var L=document.getElementById("skleft"); if(!L)return;
    L.innerHTML='<div class="hint" style="padding:12px;">Načítám…</div>';
    api("GET","/api/v1/erp/app/skupiny/"+_skView+"/lidi","").then(function(j){ _skMembers=j; skRenderMembers(); });
  }
  function skRenderMembers(){
    var L=document.getElementById("skleft"); if(!L)return;
    var g=_skGroups.filter(function(x){return x.id===_skView;})[0]||{}, j=_skMembers||{};
    L.innerHTML="";
    var head=el('<div style="flex:none;display:flex;align-items:center;gap:8px;padding:4px 6px 10px;border-bottom:1px solid var(--bord);"></div>');
    head.appendChild(el('<div style="font-size:20px;">'+esc(g.icon||"👥")+'</div>'));
    head.appendChild(el('<div style="flex:1;min-width:0;font-weight:700;font-size:16px;">'+esc(g.name||"")+'</div>'));
    var gear=el('<button class="ghost" style="margin:0;width:40px;">⚙</button>'); gear.addEventListener("click",function(){ skEditGroup(g); }); head.appendChild(gear);
    L.appendChild(head);
    var addp=el('<button class="green" style="flex:none;margin:8px 6px;">➕ Přidat lidi</button>'); addp.addEventListener("click",function(){ skPickPeople(g); }); L.appendChild(addp);
    var lw=el('<div style="flex:1;min-height:0;overflow-y:auto;-webkit-overflow-scrolling:touch;padding-bottom:24px;"></div>');
    var ul=el('<ul class="list" style="padding:0 6px;"></ul>');
    var cl=(j.clenove||[]);
    if(!cl.length){ ul.appendChild(el('<li style="color:var(--mut);border:none;">Zatím tu nikdo není. Přidej lidi ➕.</li>')); }
    cl.forEach(function(m){
      var li=el('<li class="ct" style="padding:0;border-bottom:none;"></li>');
      var bd=skBand(m.score||0);
      var role=(m.is_leader?' ⭐':(m.is_deputy?' 🎖':''));
      var sc=(m.score>0?"+":"")+(m.score||0);
      var h2=el('<div class="cthead"><div class="cav" style="background:'+avColor(m.jmeno||"?")+'">'+vyInitial(m.jmeno||"?")+'</div>'
        +'<div style="flex:1;min-width:0;"><div class="ctname">'+esc(m.jmeno||"")+role+'</div>'
        +'<div class="ctnum" style="color:'+bd.color+';">'+bd.emoji+' '+esc(bd.label)+'</div></div>'
        +'<div style="font-weight:800;font-size:17px;color:'+bd.color+';min-width:44px;text-align:right;">'+sc+'</div></div>');
      var exp=el('<div class="ctexp" style="display:none;"></div>');
      h2.addEventListener("click",function(){ vyAcc(ul,li,exp); if(li.classList.contains("open")) skFillMember(exp,g,m); });
      li.appendChild(h2); li.appendChild(exp); ul.appendChild(li);
    });
    lw.appendChild(ul); L.appendChild(lw);
  }
  function skBand(sc){
    sc=sc||0;
    if(sc>500)  return {emoji:"🚀", label:"Raketa", color:"#f0abfc"};
    if(sc>200)  return {emoji:"✈️", label:"Letadlo", color:"#7dd3fc"};
    if(sc>100)  return {emoji:"🐎", label:"Zlatý tahoun", color:"#FFD700"};
    if(sc>=51)  return {emoji:"🐎", label:"Tahoun", color:"#10b981"};
    if(sc>=1)   return {emoji:"✅", label:"Efektivní", color:"#4f8ef7"};
    if(sc>=-50) return {emoji:"🐢", label:"Méně efektivní", color:"#e0a44a"};
    return {emoji:"🪨", label:"Ti ostatní", color:"#e06a5a"};
  }
  function skScore(gid,uid,score){ api("POST","/api/v1/erp/app/skupiny/"+gid+"/clen/skore",{user_id:uid,score:score}).then(function(j){ if(j&&j.ok){ skLoadMembers(); } else alert("Chyba: "+((j&&j.error)||"?")); }); }
  function skFillMember(exp,g,m){
    exp.innerHTML="";
    // Performia „Kára" skóre −100..+100 (tahoun ⇄ ti ostatní)
    var bd0=skBand(m.score||0);
    var sw=el('<div style="padding:10px 6px 4px;"></div>');
    sw.appendChild(el('<div style="display:flex;justify-content:space-between;font-size:12px;color:var(--mut);margin-bottom:4px;"><span>🪨 −100</span><span>Kára</span><span>+100 🐎 → ✈️🚀</span></div>'));
    var val=el('<div style="text-align:center;font-weight:800;font-size:21px;color:'+bd0.color+';margin-bottom:4px;">'+(m.score>0?"+":"")+(m.score||0)+' · '+bd0.emoji+' '+esc(bd0.label)+'</div>');
    var rng=el('<input type="range" min="-100" max="100" step="1" value="'+(Math.min(100,(m.score||0)))+'" style="width:100%;accent-color:'+bd0.color+';">');
    function skSetVal(nv){ m.score=nv; var b=skBand(nv); val.innerHTML=(nv>0?"+":"")+nv+' · '+b.emoji+' '+esc(b.label); val.style.color=b.color; rng.style.accentColor=b.color; rng.value=Math.min(100,nv); }
    rng.addEventListener("input",function(){ var v=parseInt(rng.value,10)||0; var b=skBand(v); val.innerHTML=(v>0?"+":"")+v+' · '+b.emoji+' '+esc(b.label); val.style.color=b.color; rng.style.accentColor=b.color; });
    rng.addEventListener("change",function(){ var v=parseInt(rng.value,10)||0; if(v>=100){ karaOverdrive((m.score&&m.score>100?m.score:100),function(nv){ skSetVal(nv); skScore(g.id,m.user_id,nv); }); } else { skSetVal(v); skScore(g.id,m.user_id,v); } });
    sw.appendChild(val); sw.appendChild(rng);
    var ovb=el('<button class="ghost" style="margin:6px 0 0;width:100%;color:#7dd3fc;border-color:#7dd3fc;">🚀 Přetáhnout přes 100 % (✈️ Letadlo / 🚀 Raketa)</button>');
    ovb.addEventListener("click",function(){ karaOverdrive((m.score&&m.score>100?m.score:100),function(nv){ skSetVal(nv); skScore(g.id,m.user_id,nv); }); });
    sw.appendChild(ovb); exp.appendChild(sw);
    var row=el('<div style="display:flex;gap:6px;flex-wrap:wrap;padding:8px 4px;"></div>');
    var bL=el('<button class="ghost" style="margin:0;">⭐ Vedoucí</button>'); bL.addEventListener("click",function(){ skUpdate(g.id,{leader_user_id:m.user_id}); });
    var bD=el('<button class="ghost" style="margin:0;">🎖 Zástupce</button>'); bD.addEventListener("click",function(){ skUpdate(g.id,{deputy_user_id:m.user_id}); });
    var bR=el('<button class="warn" style="margin:0;">✕ Odebrat</button>'); bR.addEventListener("click",function(){ if(confirm("Odebrat "+(m.jmeno||"")+" ze skupiny?")) skMember(g.id,m.user_id,"remove"); });
    row.appendChild(bL); row.appendChild(bD); row.appendChild(bR); exp.appendChild(row);
  }
  function skNewGroup(){
    var name=prompt("Název nové skupiny (např. Vedení, IT):"); if(!name) return;
    var icon=prompt("Ikona (emoji, nepovinné):","👥")||"👥";
    api("POST","/api/v1/erp/app/skupiny/create",{name:name,icon:icon}).then(function(j){ if(j&&j.ok){ _skView=j.id; skLoadGroups(); } else alert("Chyba: "+((j&&j.error)||"?")); });
  }
  function skEditGroup(g){
    var name=prompt("Název skupiny:",g.name||""); if(name===null) return;
    var icon=prompt("Ikona (emoji):",g.icon||"👥"); if(icon===null) icon=g.icon||"👥";
    var arch=confirm("OK = uložit změny.\nZrušit ↓ pak potvrď archivaci skupiny.");
    if(!arch){ if(confirm("Archivovat skupinu „"+(g.name||"")+"\"? (lidé zůstanou, skupina zmizí)")){ api("POST","/api/v1/erp/app/skupiny/"+g.id+"/archive",{}).then(function(j){ if(j&&j.ok){ _skView=null; skLoadGroups(); } else alert("Chyba: "+((j&&j.error)||"?")); }); } return; }
    api("POST","/api/v1/erp/app/skupiny/"+g.id+"/update",{name:name,icon:icon||"👥"}).then(function(j){ if(j&&j.ok){ skLoadGroups(); } else alert("Chyba: "+((j&&j.error)||"?")); });
  }
  function skUpdate(gid,patch){ api("POST","/api/v1/erp/app/skupiny/"+gid+"/update",patch).then(function(j){ if(j&&j.ok){ skLoadMembers(); skLoadGroups(); } else alert("Chyba: "+((j&&j.error)||"?")); }); }
  function skMember(gid,uid,action){ api("POST","/api/v1/erp/app/skupiny/"+gid+"/clen",{user_id:uid,action:action}).then(function(j){ if(j&&j.ok){ skLoadMembers(); skLoadGroups(); } else alert("Chyba: "+((j&&j.error)||"?")); }); }
  function skPickPeople(g){
    var ov=el('<div style="position:fixed;inset:0;background:rgba(4,10,18,.94);z-index:200;display:flex;flex-direction:column;padding:14px;"></div>');
    var hd=el('<div style="display:flex;gap:8px;align-items:center;margin-bottom:8px;"></div>');
    hd.appendChild(el('<div style="flex:1;font-weight:700;font-size:16px;">➕ Přidat do: '+esc(g.name||"")+'</div>'));
    var cl=el('<button class="ghost" style="margin:0;width:44px;">✕</button>'); cl.addEventListener("click",function(){ ov.remove(); }); hd.appendChild(cl);
    ov.appendChild(hd);
    var srch=el('<input placeholder="🔍 Hledat člověka…" style="margin-bottom:8px;">'); ov.appendChild(srch);
    var lw=el('<div style="flex:1;overflow:auto;"><ul class="list" id="skpicklist"><li class="hint" style="border:none;">Načítám…</li></ul></div>'); ov.appendChild(lw);
    app.appendChild(ov);
    var all=[], inGrp={}; (_skMembers&&_skMembers.clenove||[]).forEach(function(m){ inGrp[m.user_id]=1; });
    function paint(){
      var f=deacc((srch.value||"").trim()); var ul=document.getElementById("skpicklist"); if(!ul)return; ul.innerHTML="";
      var shown=all.filter(function(p){ return !f||deacc(p.jmeno).indexOf(f)>=0; });
      if(!shown.length){ ul.appendChild(el('<li class="hint" style="border:none;">Nikdo.</li>')); return; }
      shown.forEach(function(p){
        var has=inGrp[p.user_id];
        var li=el('<li class="ct" style="padding:8px 6px;display:flex;align-items:center;gap:8px;cursor:pointer;"><div class="cav" style="background:'+avColor(p.jmeno||"?")+'">'+vyInitial(p.jmeno||"?")+'</div><div style="flex:1;">'+esc(p.jmeno||"")+'</div><div>'+(has?'<span style="color:var(--green);">✓</span>':'<span style="color:var(--blue);font-size:20px;">＋</span>')+'</div></li>');
        li.addEventListener("click",function(){ if(inGrp[p.user_id]){ skMember(g.id,p.user_id,"remove"); delete inGrp[p.user_id]; } else { skMember(g.id,p.user_id,"add"); inGrp[p.user_id]=1; } paint(); });
        ul.appendChild(li);
      });
    }
    srch.addEventListener("input",paint);
    api("GET","/api/v1/erp/app/skupiny/vsichni-lide","").then(function(j){ all=(j&&j.lide)||[]; paint(); });
  }
  // ───── Sdílený telefon (až 4 useři, přepínač + PIN). Marti 9.6. ─────
  function devKey(){ var k=""; try{k=localStorage.getItem("stg_device_key")||"";}catch(e){} if(!k){ k="dev-"+Math.random().toString(36).slice(2,10)+Date.now().toString(36); try{localStorage.setItem("stg_device_key",k);}catch(e){} } return k; }
  function sdileny(){
    app.innerHTML=topbar("👥 Sdílený telefon", true);
    var p=el('<div class="panel"></div>');
    p.appendChild(el('<div class="hint" style="margin-bottom:8px;line-height:1.6;">Kdo telefon drží? Klepni na sebe a zadej PIN. Citlivá data (mzda) si vyžádají PIN zvlášť.</div>'));
    // Název telefonu (sjednou) → stabilní device_key (např. „marti-ai").
    var curn=""; try{curn=localStorage.getItem("stg_device_key")||"";}catch(e){}
    var nrow=el('<div style="display:flex;gap:6px;align-items:center;margin-bottom:10px;"></div>');
    var nin=el('<input placeholder="Název telefonu (např. marti-ai)" value="'+esc(curn)+'" style="flex:1;font-size:13px;">');
    var nb=el('<button class="ghost" style="margin:0;width:64px;font-size:13px;">Uložit</button>');
    nb.addEventListener("click",function(){ var v=(nin.value||"").trim().slice(0,40); if(!v)return; try{localStorage.setItem("stg_device_key",v);}catch(e){} sdLoad(); });
    nrow.appendChild(nin); nrow.appendChild(nb); p.appendChild(nrow);
    p.appendChild(el('<div class="dashgrid" id="sdgrid"></div>'));
    var add=el('<button class="green full" style="margin-top:12px;">➕ Přidat sebe na tento telefon</button>'); add.addEventListener("click",sdJoin); p.appendChild(add);
    var adm=el('<button class="ghost full" style="margin-top:8px;">👨‍👩‍👧 Přidat lidi (rodič)</button>'); adm.addEventListener("click",sdAddPeople); p.appendChild(adm);
    var pinb=el('<button class="ghost full" style="margin-top:8px;">🔐 Nastavit / změnit můj PIN</button>'); pinb.addEventListener("click",sdSetPin); p.appendChild(pinb);
    var unb=el('<button class="ghost full" style="margin-top:14px;color:#f87171;border-color:#5a2b2b;">🚫 Zrušit sdílení tohoto telefonu</button>'); unb.addEventListener("click",sdUnshare); p.appendChild(unb);
    app.appendChild(p); sdLoad();
  }
  function sdUnshare(){
    if(!confirm("Zrušit sdílení tohoto telefonu? Odeberou se z něj všichni a telefon bude zase osobní (bez PIN zámku při otevření).")) return;
    var dk=devKey();
    api("GET","/api/v1/erp/app/shared/users?dk="+encodeURIComponent(dk),"").then(function(j){
      var us=(j&&j.users)||[];
      function fin(){ try{localStorage.removeItem("stg_device_key");}catch(e){} alert("✓ Sdílení zrušeno. Telefon je zase osobní."); try{location.reload();}catch(e){ go("apps"); } }
      var i=0;
      function next(){ if(i>=us.length){ fin(); return; } api("POST","/api/v1/erp/app/shared/remove",{device_key:dk,user_id:us[i].user_id}).then(function(){ i++; next(); }); }
      if(!us.length){ fin(); } else next();
    });
  }
  function sdAddPeople(){
    var ov=el('<div style="position:fixed;inset:0;background:rgba(4,10,18,.97);z-index:210;display:flex;flex-direction:column;padding:14px;"></div>');
    var h=el('<div style="display:flex;gap:8px;align-items:center;margin-bottom:8px;"><div style="flex:1;font-weight:700;font-size:16px;">Přidat lidi na telefon</div></div>');
    var x=el('<button class="ghost" style="margin:0;width:44px;">✕</button>'); x.addEventListener("click",function(){ov.remove(); sdLoad();}); h.appendChild(x); ov.appendChild(h);
    var srch=el('<input placeholder="🔍 Hledat…" autocomplete="off" style="margin-bottom:8px;">'); ov.appendChild(srch);
    var lw=el('<div style="flex:1;overflow:auto;"><ul class="list" id="sapick"><li class="hint" style="border:none;">Načítám…</li></ul></div>'); ov.appendChild(lw);
    app.appendChild(ov);
    var all=[], added={};
    function rp(){ var f=deacc((srch.value||"").trim()); var ul=document.getElementById("sapick"); if(!ul)return; ul.innerHTML="";
      all.filter(function(pp){return !f||deacc(pp.jmeno).indexOf(f)>=0;}).forEach(function(pp){
        var has=added[pp.user_id];
        var li=el('<li class="ct" style="padding:8px 6px;display:flex;align-items:center;gap:8px;cursor:pointer;"><div class="cav" style="background:'+(pp.agent?"#d97757":avColor(pp.jmeno||"?"))+';">'+(pp.agent?"🤖":vyInitial(pp.jmeno||"?"))+'</div><div style="flex:1;">'+esc(pp.jmeno||"")+'</div><div>'+(has?'<span style="color:var(--green);">✓</span>':'<span style="color:var(--blue);font-size:20px;">＋</span>')+'</div></li>');
        li.addEventListener("click",function(){ if(has)return; api("POST","/api/v1/erp/app/shared/assign",{device_key:devKey(),user_id:pp.user_id}).then(function(r){ if(r&&r.ok){ added[pp.user_id]=1; rp(); } else alert("Chyba: "+((r&&r.error)||"?")); }); });
        ul.appendChild(li);
      });
    }
    srch.addEventListener("input",rp);
    api("GET","/api/v1/erp/app/task-lide","").then(function(j){ all=(j&&j.lide)||[]; rp(); });
  }
  function sdPinSms(u){
    var ov=el('<div style="position:fixed;inset:0;background:rgba(4,10,18,.97);z-index:200;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px;padding:24px;"></div>');
    ov.appendChild(el('<div style="font-size:17px;font-weight:700;text-align:center;">🔐 Nastavit PIN pro<br>'+esc(u.jmeno||"")+'</div>'));
    var st=el('<div class="hint" style="text-align:center;max-width:300px;min-height:18px;line-height:1.5;">Pošlu SMS kód na ověřený mobil tohoto člověka. Po přečtení zadá kód a svůj nový PIN tady.</div>'); ov.appendChild(st);
    var send=el('<button class="green full" style="max-width:260px;">📨 Poslat SMS kód</button>');
    var sendEmail=el('<button class="ghost full" style="max-width:260px;">✉️ Poslat kód e-mailem</button>');
    var codeIn=el('<input type="tel" inputmode="numeric" maxlength="6" placeholder="ověřovací kód (SMS/e-mail)" style="width:200px;text-align:center;font-size:20px;letter-spacing:6px;display:none;">');
    var pinIn=el('<input type="tel" inputmode="numeric" maxlength="4" placeholder="nový PIN ••••" style="width:170px;text-align:center;font-size:22px;letter-spacing:8px;display:none;">');
    var setb=el('<button class="green full" style="max-width:260px;display:none;">Uložit PIN</button>');
    var numLine=el('<div class="hint" style="text-align:center;max-width:300px;min-height:16px;">📱 Číslo pro ověření: načítám…</div>');
    var editBtn=el('<button class="ghost" style="max-width:260px;font-size:13px;">✏️ Zobrazit / změnit číslo</button>');
    function loadPhone(){ api("GET","/api/v1/erp/app/shared/get-phone?user_id="+u.user_id,"").then(function(r){ if(r&&r.ok&&r.phone){ numLine.textContent="📱 Číslo pro ověření: "+r.phone; phoneIn.value=r.phone; } else { numLine.textContent="📱 Číslo pro ověření: — není nastaveno"; phoneIn.value=""; } }).catch(function(){ numLine.textContent="📱 Číslo pro ověření: (nenačteno)"; }); }
    editBtn.addEventListener("click",function(){ var show=(phoneWrap.style.display!=="flex"); phoneWrap.style.display=(show?"flex":"none"); if(show){ try{phoneIn.focus();}catch(e){} } });
    var phoneWrap=el('<div style="display:none;flex-direction:column;align-items:center;gap:8px;width:100%;max-width:260px;"></div>');
    var phoneIn=el('<input type="tel" inputmode="tel" autocomplete="off" placeholder="📱 Telefonní číslo" style="width:230px;text-align:center;font-size:18px;">');
    var savePhone=el('<button class="green full" style="max-width:260px;">Uložit číslo a pokračovat</button>');
    phoneWrap.appendChild(phoneIn); phoneWrap.appendChild(savePhone);
    savePhone.addEventListener("click",function(){ var pn=(phoneIn.value||"").trim(); if(pn.replace(/[^0-9]/g,"").length<6){ st.textContent="Zadej platné telefonní číslo."; return; } savePhone.disabled=true; st.textContent="Ukládám číslo…"; api("POST","/api/v1/erp/app/shared/set-phone",{user_id:u.user_id,phone_number:pn}).then(function(r){ if(r&&r.ok){ phoneWrap.style.display="none"; loadPhone(); send.style.display="block"; send.disabled=false; st.textContent="✓ Číslo uloženo."; } else { savePhone.disabled=false; st.textContent="Chyba: "+((r&&r.error)||"?")+(r&&r.note?(" — "+r.note):""); } }); });
    send.addEventListener("click",function(){ send.disabled=true; st.textContent="Posílám SMS…"; api("POST","/api/v1/erp/app/shared/pin-send",{user_id:u.user_id}).then(function(r){ if(r&&r.ok){ st.textContent="✓ SMS odeslána na "+(r.phone||"mobil")+". Zadej kód + nový PIN."; send.style.display="none"; sendEmail.style.display="none"; codeIn.style.display="block"; pinIn.style.display="block"; setb.style.display="block"; try{codeIn.focus();}catch(e){} } else if(r&&r.error==="no_phone"){ send.style.display="none"; phoneWrap.style.display="flex"; st.textContent="Tenhle člověk nemá uložené číslo. Zadej ho, nebo pošli kód e-mailem."; try{phoneIn.focus();}catch(e){} } else { send.disabled=false; st.textContent="Chyba: "+((r&&r.error)||"?")+(r&&r.note?(" — "+r.note):""); } }); });
    sendEmail.addEventListener("click",function(){ sendEmail.disabled=true; st.textContent="Posílám e-mail…"; api("POST","/api/v1/erp/app/shared/pin-send-email",{user_id:u.user_id}).then(function(r){ if(r&&r.ok){ st.textContent="✓ Kód poslán na "+(r.email||"e-mail")+". Zadej kód + nový PIN."; send.style.display="none"; sendEmail.style.display="none"; codeIn.style.display="block"; pinIn.style.display="block"; setb.style.display="block"; try{codeIn.focus();}catch(e){} } else { sendEmail.disabled=false; st.textContent="Chyba: "+((r&&r.error)||"?")+(r&&r.note?(" — "+r.note):""); } }); });
    setb.addEventListener("click",function(){ var cd=(codeIn.value||"").trim(); var pv=(pinIn.value||"").trim(); if(cd.length<4||!(pv.length===4&&/^[0-9]+$/.test(pv))){ st.textContent="Zadej kód z SMS a 4místný PIN."; return; } setb.disabled=true; st.textContent="Ukládám…"; api("POST","/api/v1/erp/app/shared/pin-set",{user_id:u.user_id,code:cd,pin:pv}).then(function(r){ if(r&&r.ok){ st.textContent="✓ PIN nastaven!"; setTimeout(function(){ ov.remove(); sdLoad(); },700); } else { setb.disabled=false; st.textContent="Chyba: "+((r&&r.error)||"?")+(r&&r.note?(" — "+r.note):""); } }); });
    ov.appendChild(numLine); ov.appendChild(editBtn); ov.appendChild(send); ov.appendChild(sendEmail); ov.appendChild(phoneWrap); ov.appendChild(codeIn); ov.appendChild(pinIn); ov.appendChild(setb);
    var cl=el('<button class="ghost" style="max-width:260px;">Zpět</button>'); cl.addEventListener("click",function(){ov.remove();}); ov.appendChild(cl);
    app.appendChild(ov); loadPhone();
  }
  function sdLoad(){
    var g=document.getElementById("sdgrid"); if(!g)return; g.innerHTML='<div class="hint">Načítám…</div>';
    api("GET","/api/v1/erp/app/shared/users?dk="+encodeURIComponent(devKey()),"").then(function(j){
      g.innerHTML="";
      if(!j||!j.ok){ g.innerHTML='<div class="hint">'+esc((j&&j.error)||"Nenačteno.")+'</div>'; return; }
      var us=j.users||[];
      if(!us.length){ g.innerHTML='<div class="hint" style="line-height:1.6;">Zatím nikdo. Dej <b>➕ Přidat sebe</b>, ať jsi na tomhle telefonu jako první.</div>'; return; }
      us.forEach(function(u){
        var t=el('<div class="tile" style="position:relative;'+(u.current?"outline:2px solid var(--green);":"")+'"><div class="tile-ic"><div class="cav" style="width:46px;height:46px;line-height:46px;font-size:20px;margin:0 auto;background:'+avColor(u.jmeno||"?")+';">'+vyInitial(u.jmeno||"?")+'</div></div><div class="tile-tt">'+esc((u.jmeno||"").split(" ")[0])+'</div><div class="tile-sub">'+(u.current?"právě ty ✓":(u.has_pin?"klepni → PIN":"nemá PIN"))+'</div></div>');
        t.addEventListener("click",function(){ if(u.current) return; if(!u.has_pin){ sdPinSms(u); return; } sdSwitch(u); });
        var rmx=el('<button class="ghost" style="position:absolute;top:2px;right:2px;padding:1px 7px;font-size:12px;color:#f87171;border-color:#5a2b2b;background:#1a0f12;z-index:2;">✕</button>');
        rmx.addEventListener("click",function(ev){ ev.stopPropagation(); if(!confirm("Odebrat "+(u.jmeno||"")+" z tohoto telefonu?")) return; api("POST","/api/v1/erp/app/shared/remove",{device_key:devKey(),user_id:u.user_id}).then(function(r){ if(r&&r.ok) sdLoad(); else alert("Chyba: "+((r&&r.error)||"?")); }); });
        t.appendChild(rmx);
        g.appendChild(t);
      });
    });
  }
  function sdSwitch(u){
    var ov=el('<div style="position:fixed;inset:0;background:rgba(4,10,18,.97);z-index:200;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:14px;padding:24px;"></div>');
    ov.appendChild(el('<div class="cav" style="width:64px;height:64px;line-height:64px;font-size:26px;background:'+avColor(u.jmeno||"?")+';">'+vyInitial(u.jmeno||"?")+'</div>'));
    ov.appendChild(el('<div style="font-size:18px;font-weight:700;">'+esc(u.jmeno||"")+'</div>'));
    ov.appendChild(el('<div class="hint">Zadej PIN</div>'));
    var inp=el('<input type="tel" inputmode="numeric" maxlength="4" placeholder="••••" style="width:150px;text-align:center;font-size:26px;letter-spacing:10px;">'); ov.appendChild(inp);
    var st=el('<div class="hint" style="min-height:18px;"></div>'); ov.appendChild(st);
    var go2=el('<button class="green full" style="max-width:240px;">Přepnout</button>');
    function doSw(){ var pv=(inp.value||"").trim(); if(pv.length<4){ try{inp.focus();}catch(e){} return; } go2.disabled=true; st.textContent="Přepínám…";
      api("POST","/api/v1/erp/app/shared/switch",{device_key:devKey(),user_id:u.user_id,pin:pv}).then(function(r){
        if(r&&r.ok){ st.textContent="✓ Přihlášen/a jako "+(u.jmeno||""); setTimeout(function(){ try{location.reload();}catch(e){} },500); }
        else { go2.disabled=false; var e=(r&&r.error)||"?"; st.textContent=(e==="pin_wrong"?("Špatný PIN — zbývá "+(r.left||0)):(e==="pin_locked"?("Zamčeno na "+(r.minutes||15)+" min"):(e==="pin_not_set"?"Tento user nemá PIN":e))); inp.value=""; try{inp.focus();}catch(_){} }
      }); }
    go2.addEventListener("click",doSw); inp.addEventListener("keydown",function(e){ if(e.key==="Enter")doSw(); });
    ov.appendChild(go2);
    var cl=el('<button class="ghost" style="max-width:240px;">Zpět</button>'); cl.addEventListener("click",function(){ov.remove();}); ov.appendChild(cl);
    app.appendChild(ov); try{inp.focus();}catch(e){}
  }
  function sdJoin(){ api("POST","/api/v1/erp/app/shared/join",{device_key:devKey()}).then(function(r){ if(r&&r.ok){ sdLoad(); } else alert("Chyba: "+((r&&r.error)||"?")); }); }
  function sdSetPin(){
    var ov=el('<div style="position:fixed;inset:0;background:rgba(4,10,18,.97);z-index:200;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:14px;padding:24px;"></div>');
    ov.appendChild(el('<div style="font-size:17px;font-weight:700;">🔐 Nastav svůj 4místný PIN</div>'));
    ov.appendChild(el('<div class="hint" style="text-align:center;max-width:280px;line-height:1.6;">Tímhle PINem se pak přepneš na sebe na sdíleném telefonu.</div>'));
    var inp=el('<input type="tel" inputmode="numeric" maxlength="4" placeholder="••••" style="width:150px;text-align:center;font-size:26px;letter-spacing:10px;">'); ov.appendChild(inp);
    var st=el('<div class="hint" style="min-height:18px;"></div>'); ov.appendChild(st);
    var go2=el('<button class="green full" style="max-width:240px;">Uložit PIN</button>');
    go2.addEventListener("click",function(){ var pv=(inp.value||"").trim(); if(!(pv.length===4&&/^[0-9]+$/.test(pv))){ st.textContent="PIN jsou 4 číslice."; return; } go2.disabled=true;
      api("POST","/api/v1/erp/app/pin/set",{pin:pv}).then(function(r){ if(r&&r.ok){ st.textContent="✓ PIN uložen"; setTimeout(function(){ ov.remove(); sdLoad(); },500); } else { go2.disabled=false; st.textContent="Chyba: "+((r&&r.error)||"?")+(r&&r.note?(" — "+r.note):""); } }); });
    ov.appendChild(go2);
    var cl=el('<button class="ghost" style="max-width:240px;">Zpět</button>'); cl.addEventListener("click",function(){ov.remove();}); ov.appendChild(cl);
    app.appendChild(ov); try{inp.focus();}catch(e){}
  }
  function set_notifaccess(){ app.innerHTML=topbar("Přístup k oznámením", true); var p=el('<div class="panel"></div>');
    if(!(B&&typeof B.openNotifAccess==="function")){ p.appendChild(el('<div class="hint">Tato funkce je v appce STRATEGIE.</div>')); app.appendChild(p); return; }
    var bd=getBadges()||{};
    p.appendChild(el('<div class="big">Stav: <b>'+(bd.access?"povoleno ✓":"nepovoleno")+'</b></div>'));
    var b=el('<button class="green full">Otevřít nastavení přístupu</button>'); b.addEventListener("click",function(){B.openNotifAccess();}); p.appendChild(b);
    p.appendChild(el('<div class="hint">Umožní spočítat nová oznámení (WhatsApp, SMS) a zobrazit číslo na ikoně Aplikace. Appka oznámení nečte — jen je počítá.</div>')); app.appendChild(p); }
  // ── TELEFONNÍ ČÍSLO (přečteno ze SIM přes appku + potvrzení → uložení, bez SMS) ──
  function set_phone(){
    app.innerHTML=topbar("Telefonní číslo", true);
    var p=el('<div class="panel"></div>');
    p.appendChild(el('<div class="hint">Číslo tohoto telefonu uložíme ke spárovanému zařízení (pro zobrazení jména u hovorů). Appka ho zkusí přečíst ze SIM — můžeš ho upravit.</div>'));
    var pre=""; try{ if(B&&typeof B.simNumber==="function") pre=B.simNumber()||""; }catch(e){}
    var inp=el('<input id="phNum" inputmode="tel" placeholder="+420 777 123 456" value="'+esc(pre)+'" style="margin-top:6px">'); p.appendChild(inp);
    var status=el('<div class="hint" id="phStatus" style="margin-top:8px"></div>');
    if(!pre) status.textContent="SIM číslo se nepodařilo přečíst — zadej ho ručně.";
    var btn=el('<button class="green full">Uložit číslo</button>');
    btn.addEventListener("click",function(){
      var v=(inp.value||"").trim();
      if(v.replace(/[^0-9]/g,"").length<6){ status.textContent="Zadej platné číslo."; return; }
      btn.disabled=true; status.textContent="Ukládám…";
      var dev=""; try{ dev=B.deviceId(); }catch(e){}
      api("POST","/api/v1/erp/app/phone-set",{phone_number:v,device_id:dev}).then(function(j){
        if(j&&j.ok){ status.innerHTML="✓ Uloženo: <b>"+esc(j.phone_number||v)+"</b>"; btn.disabled=false; btn.textContent="Uložit změnu"; }
        else { status.textContent="Uložení selhalo."; btn.disabled=false; }
      }).catch(function(){ status.textContent="Chyba spojení."; btn.disabled=false; });
    });
    p.appendChild(btn); p.appendChild(status); app.appendChild(p);
  }

  // ───── FIRMA (celá plocha s jemným firemním pozadím, bez spodní lišty) ─────
  function firma(){
    app.innerHTML="";
    var sec=el('<div style="margin:-14px -14px -96px;min-height:100vh;padding:22px 20px calc(96px + env(safe-area-inset-bottom,0));background:linear-gradient(165deg,#0c1622,#13243a 55%,#0b1420);display:flex;flex-direction:column;"></div>');
    // Marti 7.6. večer: hlavička posunutá do půlky obrazovky.
    sec.appendChild(el('<div style="font-size:27px;font-weight:800;margin-top:50vh;">🏢 Firma</div>'));
    sec.appendChild(el('<div style="color:#cdd6e2;margin-top:10px;font-size:14px;line-height:1.6;max-width:420px;">Firemní rozcestník — připravujeme. Tady budou firemní agendy, přehledy a nástroje.</div>'));
    app.appendChild(sec);
  }
  // ───── VÝROBA (icon-rail: živé nahoře, neživé dole). Marti 8.6. ─────
  var _vyView="makam", _vyPeople=[], _vyData=null, _vyZakMode="list";
  // Marti 10.6.2026: stejná konzole pro Výrobu i skupiny. mode 'vyroba' | 'group'.
  var _vyCtx={mode:"vyroba",gid:0,name:"",icon:"🏭"};
  function _vyIsGroup(){ return _vyCtx.mode==="group"; }
  // Marti 10.6.: živý refresh statusů přes UDÁLOSTI (foreground/poll), ne nový
  // watchdog. Překreslí jen když se podpis stavů změní → žádné rušení bez změny.
  var _vyLidiSig="";
  function _vySig(lidi){ return JSON.stringify((lidi||[]).map(function(p){ return [p.user_id,p.stav,p.stav_pozn||"",p.stav_zak||""]; })); }
  var VY_TOP=[
    {k:"mimo_plan", ic:"🌴", l:""},
    {k:"chybi",     ic:"🫥", l:"Chybím"},
    {k:"makam",     ic:"👷", l:"Makám"},
    {k:"relaxuji",  ic:"☕", l:"Relaxuji"},
    {k:"informuji", ic:"💡", l:"Informuji"},
    {k:"potrebuji", ic:"🙋", l:"Potřebuji"},
    {k:"cekam",     ic:"🥱", l:"(Čekám…)", badge:true},
    {k:"jedu",      ic:"🚗", l:"Už jedu", onlyIf:true},
    {k:"finisuji",  ic:"🏁", l:"Finišuji"}
  ];
  var VY_BOT=[
    {k:"zakazky",   ic:"🧾", l:"Zakázky"},
    {k:"vp",        ic:"👔", l:"VP"},
    {k:"zkusebna",  ic:"🧪", l:"Zkušebna"},
    {k:"odvozy",    ic:"🚚", l:"Odvozy"},
    {k:"nakup",     ic:"🛒", l:"Nákup"},
    {k:"priprava",  ic:"🔧", l:"Příprava"}
  ];
  var VY_READY={tym:1,makam:1,relaxuji:1,potrebuji:1,informuji:1,finisuji:1,cekam:1,chybi:1,jedu:1,zakazky:1,odvozy:1,mimo_plan:1};
  function vyBtn(v){
    var b=el('<button data-k="'+v.k+'" style="position:relative;margin:0;padding:6px 1px;font-size:10px;line-height:1.1;display:flex;flex-direction:column;align-items:center;gap:2px;border:1px solid var(--bord);background:transparent;color:var(--mut);border-radius:9px;cursor:pointer;"><span style="font-size:18px;">'+v.ic+'</span>'+esc(v.l)+'<span class="vybadge" data-badge style="display:none;">0</span></button>');
    if(v.onlyIf) b.style.display="none";
    b.addEventListener("click",function(){
      _vyView=v.k; vyPaintRail(); vyLoad();
    });
    return b;
  }
  // Marti 9.6.: otevři Výrobu rovnou na konkrétním seznamu (z ikon v Aplikacích).
  function openVyroba(view){ _vyCtx={mode:"vyroba",gid:0,name:"",icon:"🏭"}; window._vyInitView=view||"makam"; go("vyroba"); }
  // ───── „Dnešek" — dva pohledy: 🗓 Docházkový (HR) + 🧾 Zakázkový (vedoucí výroby). Marti 19.6. ─────
  // Sdílené pro vlastní Dnešek i pro 👁 osoby z panelu skupin (přes _dochViewUid).
  function openPersDnesek(uid, jmeno){ window._persDnesek={uid:uid, jmeno:jmeno||""}; go("persDnesek"); }
  var _dnesView="doch", _dnesFilter="vse", _dnesTodays=[];   // pravý panel: Docházka (filtry) + Výroba (zakázky)
  function _dnesScreen(title){
    app.innerHTML=topbar(title, true, true); _dochTopPad();
    if(!window._dnesViewSet){ _dnesView=(window._canManageVyroba?"zak":"doch"); }
    var wrap=el('<div style="display:flex;gap:10px;height:calc(100vh - 85px - var(--navh, 65px));align-items:stretch;"></div>');
    wrap.appendChild(el('<div id="dnesLeft" style="flex:1;min-width:0;overflow-y:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none;border:1px solid var(--bord);border-radius:12px;background:rgba(255,255,255,0.02);padding:2px 8px;"></div>'));
    wrap.appendChild(el('<div id="dnesRail" style="width:78px;flex:none;overflow-y:auto;scrollbar-width:none;display:flex;flex-direction:column;gap:4px;padding:1px;"></div>'));
    app.appendChild(wrap);
    _dnesLoad();
  }
  function _dnesLoad(){
    var left=document.getElementById("dnesLeft"); if(left) left.innerHTML='<div class="hint" style="padding:12px;">Načítám…</div>';
    api("GET","/api/v1/erp/app/attendance/list?days=14"+(_dochViewUid?("&user_id="+encodeURIComponent(_dochViewUid)):""),"").then(function(j){
      var rows=(j&&j.entries)||[]; var tdy=_locDate(0);
      _dnesTodays=rows.filter(function(e){ return (e.d||"")===tdy; });
      // Marti 19.6.: skrýt nulové zbytky (trimnutá importovaná směna, např. 05:18–05:18, 0 h).
      _dnesTodays=_dnesTodays.filter(function(e){ return !(!e.is_active && (Number(e.hours||0)===0) && e.zac && e.kon && e.zac===e.kon); });
      // Marti 19.6.: chronologicky — ranní příchod nahoře, další joby dolů.
      _dnesTodays.sort(function(a,b){ var az=a.zac||"99:99", bz=b.zac||"99:99"; if(az!==bz) return az<bz?-1:1; return (a.id||0)-(b.id||0); });
      _dnesPaint();
    }).catch(function(){ var l=document.getElementById("dnesLeft"); if(l)l.innerHTML='<div class="hint" style="padding:12px;">Nepodařilo se načíst.</div>'; });
  }
  function _dnesRailHdr(t){ return el('<div style="font-size:9.5px;font-weight:800;color:#8aa0c4;text-transform:uppercase;letter-spacing:.04em;text-align:center;margin:7px 0 1px;">'+esc(t)+'</div>'); }
  function _dnesRailBtn(icon,label,active,fn){
    var b=el('<button style="width:100%;box-sizing:border-box;margin:0;padding:9px 2px;font-size:10px;line-height:1.1;display:flex;flex-direction:column;align-items:center;gap:3px;border:1px solid '+(active?"var(--green)":"var(--bord)")+';background:'+(active?"var(--green)":"rgba(255,255,255,0.02)")+';color:'+(active?"#04150e":"var(--mut)")+';border-radius:12px;cursor:pointer;"><span style="font-size:21px;line-height:1;">'+icon+'</span>'+esc(label)+'</button>');
    b.addEventListener("click",fn); return b;
  }
  function _dnesPaint(){
    var rail=document.getElementById("dnesRail"), left=document.getElementById("dnesLeft");
    if(rail){ rail.innerHTML="";
      rail.appendChild(_dnesRailHdr("Docházka"));
      [["📋","Vše","vse"],["🌟","Speciální","spec"],["👷","Makám","makam"],["☕","Relax","relax"],["📊","Souhrn","souhrn"]].forEach(function(it){
        rail.appendChild(_dnesRailBtn(it[0],it[1],(_dnesView==="doch"&&_dnesFilter===it[2]),function(){ _dnesView="doch"; _dnesFilter=it[2]; window._dnesViewSet=true; _dnesPaint(); }));
      });
      rail.appendChild(_dnesRailHdr("Výroba"));
      rail.appendChild(_dnesRailBtn("🧾","Zakázky",(_dnesView==="zak"),function(){ _dnesView="zak"; window._dnesViewSet=true; _dnesPaint(); }));
    }
    if(!left) return;
    if(_dnesView==="zak"){ _zakRender(left); return; }
    // Docházkový pohled: jen seznam (lištu staví naše skupinová lišta vpravo, ne _renderJobPanel)
    left.innerHTML='<ul id="dochToday2" style="padding:0;list-style:none;margin:0;"></ul>';
    _renderJobPanel("dnesNoRail","dochToday2",_dnesTodays,{f:_dnesFilter});
  }
  function _zakRender(box){
    box.innerHTML='<div class="hint" style="padding:12px;">Načítám…</div>';
    var q="/api/v1/erp/app/work/today"+(_dochViewUid?("?user_id="+encodeURIComponent(_dochViewUid)):"");
    api("GET",q,"").then(function(j){
      box.innerHTML="";
      var segs=(j&&j.segments)||[];
      // Marti 19.6.: skrýt parazitní úseky (uzavřené, skoro nulové < ~1 min) — vznikaly při přepnutí zakázky→činnost.
      segs=segs.filter(function(s){ return !(s.do_ && Number(s.hod||0)<0.02); });
      if(!segs.length){ box.appendChild(el('<div class="hint" style="padding:14px;">Dnes žádná práce na zakázce.</div>')); return; }
      var groups={}, order=[], total=0;
      segs.forEach(function(s){
        var key=s.is_rezie?"Režie":(s.project_ref||"—");
        if(!groups[key]){ groups[key]={nazev:(s.is_rezie?"":(s.project_nazev||"")), rows:[], h:0}; order.push(key); }
        groups[key].rows.push(s); groups[key].h+=Number(s.hod||0); total+=Number(s.hod||0);
      });
      box.appendChild(el('<div style="font-weight:800;font-size:16px;margin:2px 2px 12px;">⏱ Dnes na zakázkách: <span style="color:#3ecf8e;">'+fmtHM(total)+'</span></div>'));
      order.forEach(function(key){
        var g=groups[key];
        var card=el('<div style="border:1px solid var(--bord);border-radius:13px;margin-bottom:10px;overflow:hidden;"></div>');
        card.appendChild(el('<div style="display:flex;justify-content:space-between;align-items:center;padding:10px 12px;background:rgba(91,141,239,.08);"><div style="font-weight:700;min-width:0;">'+(key==="Režie"?"🧰 Režie":"🧾 "+esc(key))+(g.nazev?(' <span class="hint" style="font-weight:400;">'+esc(g.nazev)+'</span>'):'')+'</div><b style="color:#3ecf8e;white-space:nowrap;margin-left:8px;">'+fmtHM(g.h)+'</b></div>'));
        g.rows.forEach(function(s){
          var rng=(s.od||"?")+(s.do_?(" – "+s.do_):" – …");
          card.appendChild(el('<div style="display:flex;justify-content:space-between;gap:8px;padding:8px 12px;border-top:1px solid var(--bord);font-size:13px;"><div style="min-width:0;">'+(s.cinnost_name?("⚙ "+esc(s.cinnost_name)):'<span class="hint">bez rozlišení činnosti</span>')+' <span class="hint">· '+esc(rng)+'</span></div><span class="hint" style="white-space:nowrap;">'+(s.hod!=null?fmtHM(s.hod):"")+'</span></div>'));
        });
        box.appendChild(card);
      });
    }).catch(function(){ box.innerHTML='<div class="hint" style="padding:14px;">Nepodařilo se načíst.</div>'; });
  }
  function persDnesek(){
    var P=window._persDnesek||{};
    _dochViewUid=P.uid; _dochViewName=P.jmeno||"";
    _dnesScreen("📅 Dnešek — "+(P.jmeno||""));
  }
  // 🏭 Výroba hub pro Michaelu Hladíkovou (Marti 23.6.2026) — vzor sekce Vedení:
  // nadpisy bloků + ikonky. Její pracovní plocha pro výrobu. Plná práva (uid 16 v _VYROBA_MANAGERS).
