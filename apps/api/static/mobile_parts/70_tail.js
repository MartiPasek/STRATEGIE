  function set_imp(){
    app.innerHTML=topbar("Přihlásit jako (test)", true);
    var p=el('<div class="panel"></div>');
    var st=el('<div class="hint" id="impSt" style="font-size:13.5px;">Zjišťuji stav…</div>'); p.appendChild(st);
    p.appendChild(el('<label>User ID, login, nebo z+ČísloZam (např. z370)</label>'));
    var inp=el('<input id="impUser" placeholder="např. 30 nebo z370" autocomplete="off">'); p.appendChild(inp);
    var go=el('<button class="green full">🎭 Přihlásit jako</button>');
    var bk=el('<button class="warn full" style="margin-top:8px;">Vrátit se k sobě</button>');
    function refresh(){
      api("GET","/api/v1/erp/app/impersonate/status","").then(function(j){
        var e=document.getElementById("impSt"); if(!e)return;
        if(!j||!j.ok){ e.textContent="Stav se nepodařilo načíst."; return; }
        if(j.active){ e.innerHTML='🎭 Právě jednáš jako <b>'+esc(j.active.target_name||String(j.active.target_id))+'</b> — Docházka ukazuje jeho data.'; }
        else if(!j.is_parent){ e.textContent="Tahle funkce je dostupná jen rodičům."; }
        else { e.textContent="Žádná aktivní impersonace — jednáš sám za sebe."; }
      });
    }
    go.addEventListener("click",function(){
      var q=(inp.value||"").trim(); if(!q)return; go.disabled=true;
      api("POST","/api/v1/erp/app/impersonate",{user:q}).then(function(j){
        go.disabled=false; var e=document.getElementById("impSt"); if(!e)return;
        if(j&&j.ok){ e.innerHTML='✅ Jednáš jako <b>'+esc(j.target_name||String(j.target_id))+'</b>. Otevři Docházku — uvidíš jeho data.'; inp.value=""; }
        else { e.textContent="✗ "+((j&&j.error)||"Nepodařilo se."); }
      });
    });
    bk.addEventListener("click",function(){
      bk.disabled=true;
      api("POST","/api/v1/erp/app/impersonate/stop",{}).then(function(){ bk.disabled=false; refresh(); });
    });
    p.appendChild(go); p.appendChild(bk);
    p.appendChild(el('<div class="hint">Pro testování docházky a práv. Vše se loguje do fw.impersonation_log (od–do, kdo, koho). Automaticky končí po 8 hodinách nebo tlačítkem výše.</div>'));
    app.appendChild(p); refresh();
  }
  // === Lišta skupin (Marti 10.6.2026): skupiny sdílí konzoli Výroby (_vyCtx mode=group) ===
  var _skupBarCache=null,_skupBarOn=false;
  function openSkup(gid,name,icon){ _vyCtx={mode:"group",gid:gid,name:name||"Skupina",icon:icon||"👥"}; _vyView="makam"; _vyPeople=[]; _vyData=null; _vyLidiSig=""; go("vyroba"); }
  function skupBtn(ic,lbl,fn,rel){
    var hi=(rel==="lead"||rel==="deputy");
    var fr=(ic||"").split("|");
    var iconHtml=(fr.length>1)
      ? '<span class="i anim-emoji" data-frames="'+fr.join("|")+'" data-fi="0" data-hold="3" style="display:inline-block;'+(fr[0]==="🚜"?"transform:scaleX(-1);":"")+'">'+fr[0]+'</span>'
      : '<span class="i">'+ic+'</span>';
    var b=el('<button class="tabbtn" style="flex:0 0 auto;min-width:60px;'+(hi?"color:var(--blue);":"")+'">'+iconHtml+esc(lbl)+'</button>');
    b.addEventListener("click",fn); return b;
  }
  var _animTimer=null;
  function _tickAnimIcons(){
    var els=document.querySelectorAll(".anim-emoji");
    Array.prototype.forEach.call(els,function(sp){
      var fr=(sp.getAttribute("data-frames")||"").split("|"); if(fr.length<2)return;
      var hold=parseInt(sp.getAttribute("data-hold")||"0",10);
      if(hold>1){ sp.setAttribute("data-hold",hold-1); return; }   // realita (1. snímek) drží dýl
      var i=(parseInt(sp.getAttribute("data-fi")||"0",10)+1)%fr.length;
      sp.setAttribute("data-fi",i); sp.textContent=fr[i];
      sp.style.display="inline-block"; sp.style.transform=(fr[i]==="🚜")?"scaleX(-1)":"";  // traktor doprava
      sp.setAttribute("data-hold", i===0?3:1);                    // 1. snímek 3× tak dlouho jako vize
    });
  }
  function startAnimIcons(){ if(_animTimer)return; _animTimer=setInterval(_tickAnimIcons,800); }
  function skupBar(){
    var bar=bnavx2;
    function paint(){
      bar.innerHTML="";
      var gs=(_skupBarCache&&_skupBarCache.groups)||[];
      bar.appendChild(skupBtn("🌐","Všichni",function(){ openSkup(0,"Všichni","🌐"); }));
      var rank={other:0,member:1,deputy:2,lead:3};
      gs.slice().sort(function(a,b){ return (rank[a.rel]||0)-(rank[b.rel]||0); }).forEach(function(g){
        bar.appendChild(skupBtn(g.icon,g.name,function(){ openSkup(g.id,g.name,g.icon); },g.rel));
      });
      bar.appendChild(skupBtn("🤝","Spolupráce",function(){ go("dochazka"); }));
      setTimeout(function(){ try{ bar.scrollLeft=bar.scrollWidth; }catch(e){} },0);
    }
    paint(); startAnimIcons();
    if(!_skupBarCache){ api("GET","/api/v1/erp/app/skupiny/bar","").then(function(j){ if(j&&j.ok){ _skupBarCache=j; if(curTab==="firma") paint(); } }); }
  }

  // === Všichni uživatelé STRATEGIE napříč tenanty (JEN RODIČE). Marti 10.6.2026 ===
  var _auTenant=0,_auData=null,_auMode="users",_auUnmatched=false;
  function alluser(){
    app.innerHTML=topbar("🌐 Uživatelé STRATEGIE", true, true);
    var wrap=el('<div style="height:calc(100vh - 150px);display:flex;flex-direction:column;padding:6px 8px 0;"></div>');
    var chips=el('<div style="display:flex;gap:6px;margin-bottom:8px;"></div>');
    function chip(lbl,m){ var b=el('<button class="ghost" style="flex:1;'+(_auMode===m?"background:var(--blue);color:#fff;border-color:var(--blue);":"")+'">'+lbl+'</button>'); b.addEventListener("click",function(){ _auMode=m; alluser(); }); return b; }
    chips.appendChild(chip("👥 Naši","users")); chips.appendChild(chip("📒 Helios (účetní)","helios"));
    wrap.appendChild(chips);
    if(_auMode==="users"){
      var sel=el('<select id="auTenant" style="width:100%;background:#0f1620;border:1px solid var(--bord);border-radius:10px;padding:10px;color:var(--tx);font-size:15px;margin-bottom:8px;"><option value="0">— Všechny tenanty —</option></select>');
      sel.addEventListener("change",function(){ _auTenant=parseInt(sel.value||"0",10); auLoad(); });
      wrap.appendChild(sel);
    } else {
      var f=el('<label style="display:flex;align-items:center;gap:8px;color:var(--mut);font-size:13px;margin-bottom:8px;"><input type="checkbox" id="auUnm"'+(_auUnmatched?" checked":"")+'> Jen nespárované</label>');
      f.querySelector("input").addEventListener("change",function(e){ _auUnmatched=e.target.checked; auLoadHelios(); });
      wrap.appendChild(f);
    }
    var lw=el('<div class="list" style="flex:1;overflow:auto;"><ul id="aulist"><li style="color:var(--mut);border:none;">Načítám…</li></ul></div>');
    wrap.appendChild(lw); app.appendChild(wrap);
    if(_auMode==="users") auLoad(); else auLoadHelios();
  }
  function auLoad(){ api("GET","/api/v1/erp/app/all-users?tenant="+_auTenant,"").then(function(j){ _auData=j; auRender(); }); }
  function auLoadHelios(){ api("GET","/api/v1/erp/app/helios-recon"+(_auUnmatched?"?filter=unmatched":""),"").then(function(j){ _auData=j; auRenderHelios(); }); }
  function auRenderHelios(){
    var ul=document.getElementById("aulist"); if(!ul)return;
    var j=_auData;
    if(!j||!j.ok){ ul.innerHTML='<li style="color:var(--mut);border:none;">'+(((j&&j.error)==="forbidden")?"🔒 Jen pro rodiče.":(((j&&j.error)==="mcp_unavailable")?"Helios (MCP) momentálně nedostupný.":"Nepodařilo se načíst."))+'</li>'; return; }
    var ppl=j.people||[], sm=j.summary||{};
    ul.innerHTML="";
    ul.appendChild(el('<li style="border:none;color:var(--mut);font-size:12.5px;padding:2px 4px 8px;">🔴 '+(sm.no_emp||0)+' nespárováno · 🟡 '+(sm.no_user||0)+' bez usera · 🟢 '+(sm.ok||0)+' OK</li>'));
    if(!ppl.length){ ul.appendChild(el('<li style="color:var(--mut);border:none;">Nikdo.</li>')); return; }
    var SM={no_emp:{e:"🔴",t:"nespárováno"},no_user:{e:"🟡",t:"bez usera"},ok:{e:"🟢",t:"OK"}};
    ppl.forEach(function(p){
      var st=SM[p.stav]||{e:"",t:""};
      ul.appendChild(el('<li style="display:flex;align-items:center;gap:10px;">'
        +'<span style="width:30px;height:30px;border-radius:50%;background:#1a2533;display:flex;align-items:center;justify-content:center;font-weight:700;flex:none;">'+vyInitial(p.jmeno||"?")+'</span>'
        +'<span style="min-width:0;flex:1;"><b style="display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">'+esc(p.jmeno||("#"+p.cislo))+'</b>'
        +'<span style="color:var(--mut);font-size:12px;">Helios '+esc(p.src)+' · č. '+esc(String(p.cislo))+(p.typ?(' · '+esc(p.typ)):'')+'</span></span>'
        +'<span style="font-size:12px;white-space:nowrap;flex:none;">'+st.e+' '+st.t+'</span></li>'));
    });
  }
  function auRender(){
    var ul=document.getElementById("aulist"); if(!ul)return;
    var j=_auData;
    if(!j||!j.ok){ ul.innerHTML='<li style="color:var(--mut);border:none;">'+(((j&&j.error)==="forbidden")?"🔒 Jen pro rodiče.":"Nepodařilo se načíst.")+'</li>'; return; }
    var sel=document.getElementById("auTenant");
    if(sel && sel.options.length<=1){ (j.tenants||[]).forEach(function(t){ var o=document.createElement("option"); o.value=t.id; o.textContent=t.name; sel.appendChild(o); }); sel.value=String(_auTenant); }
    var us=j.users||[];
    ul.innerHTML="";
    ul.appendChild(el('<li style="border:none;color:var(--mut);font-size:12.5px;padding:2px 4px 8px;">'+us.length+' uživatelů</li>'));
    if(!us.length){ ul.appendChild(el('<li style="color:var(--mut);border:none;">Nikdo.</li>')); return; }
    us.forEach(function(u){
      ul.appendChild(el('<li style="display:flex;align-items:center;gap:10px;">'
        +'<span style="width:30px;height:30px;border-radius:50%;background:#1a2533;display:flex;align-items:center;justify-content:center;font-weight:700;flex:none;">'+vyInitial(u.jmeno)+'</span>'
        +'<span style="min-width:0;flex:1;"><b style="display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">'+(u.parent?"👑 ":"")+esc(u.jmeno)+'</b>'
        +'<span style="color:var(--mut);font-size:12px;display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">'+esc(u.tenanty||"")+'</span></span>'
        +((u.status&&u.status!=="active")?'<span style="font-size:11px;color:#caa14a;flex:none;">'+esc(u.status)+'</span>':'')+'</li>'));
    });
  }

  // ===== Snímek obrazovky: zmrazit + nakreslit + odeslat Claudovi (Marti 11.6.2026) =====
  function _shotBtnOn(){ try{ return localStorage.getItem("stg_shot_btn")==="1"; }catch(e){ return false; } }
  function _shotSyncBtn(){
    var b=document.getElementById("shotFab"); var on=_shotBtnOn();
    if(on && !b){
      b=el('<button id="shotFab" aria-label="Snímek obrazovky" style="position:fixed;right:12px;top:50vh;z-index:1200;width:46px;height:46px;border-radius:50%;border:1px solid var(--bord);background:rgba(18,22,30,.78);color:#fff;font-size:21px;line-height:46px;text-align:center;box-shadow:0 4px 14px rgba(0,0,0,.45);touch-action:none;opacity:.92;">📷</button>');
      // Plovoucí = přetažitelné. Chytni a posuň kamkoliv; pozice se zapamatuje.
      var pos=null; try{ pos=JSON.parse(localStorage.getItem("stg_shot_pos")||"null"); }catch(e){}
      if(pos&&typeof pos.l==="number"){ b.style.left=pos.l+"px"; b.style.top=pos.t+"px"; b.style.right="auto"; }
      var dragging=false, moved=false, sx=0, sy=0, ox=0, oy=0;
      b.addEventListener("pointerdown",function(ev){ ev.preventDefault(); dragging=true; moved=false; var r=b.getBoundingClientRect(); sx=ev.clientX; sy=ev.clientY; ox=r.left; oy=r.top; try{b.setPointerCapture(ev.pointerId);}catch(e){} });
      b.addEventListener("pointermove",function(ev){ if(!dragging)return; var dx=ev.clientX-sx, dy=ev.clientY-sy; if(Math.abs(dx)+Math.abs(dy)>6)moved=true; var nl=Math.max(4,Math.min(window.innerWidth-50, ox+dx)); var nt=Math.max(36,Math.min(window.innerHeight-50, oy+dy)); b.style.left=nl+"px"; b.style.top=nt+"px"; b.style.right="auto"; });
      b.addEventListener("pointerup",function(ev){ if(!dragging)return; dragging=false; try{b.releasePointerCapture(ev.pointerId);}catch(e){}
        if(moved){ var r=b.getBoundingClientRect(); try{localStorage.setItem("stg_shot_pos",JSON.stringify({l:Math.round(r.left),t:Math.round(r.top)}));}catch(e){} }
        else { try{_tapFeedback();}catch(e){} openShot(); } });
      b.addEventListener("pointercancel",function(){ dragging=false; });
      document.body.appendChild(b);
    } else if(!on && b){ b.remove(); }
  }
  function _shotToast(msg){ var t=document.getElementById("shotToast"); if(!t){ t=el('<div id="shotToast" style="position:fixed;left:50%;top:18px;transform:translateX(-50%);z-index:1100;background:rgba(18,22,30,.96);border:1px solid var(--bord);color:#fff;padding:8px 14px;border-radius:20px;font-size:14px;box-shadow:0 4px 14px rgba(0,0,0,.45);"></div>'); document.body.appendChild(t); } t.textContent=msg; t.style.display="block"; }
  function _shotToastHide(){ var t=document.getElementById("shotToast"); if(t)t.style.display="none"; }
  var _h2cReady=null;
  function _loadH2C(){
    if(_h2cReady) return _h2cReady;
    _h2cReady=new Promise(function(res,rej){
      if(window.html2canvas){ res(window.html2canvas); return; }
      var s=document.createElement("script");
      s.src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js";
      s.onload=function(){ window.html2canvas?res(window.html2canvas):rej(new Error("html2canvas se nenačetl")); };
      s.onerror=function(){ rej(new Error("nelze stáhnout nástroj snímku (offline?)")); };
      document.head.appendChild(s);
    });
    return _h2cReady;
  }
  function openShot(){
    var fab=document.getElementById("shotFab"); if(fab)fab.style.display="none";
    _shotToast("📸 Zmrazuji obrazovku…");
    var sx=window.scrollX||0, sy=window.scrollY||0;
    _loadH2C().then(function(h2c){
      return h2c(document.body,{ x:sx, y:sy, width:document.documentElement.clientWidth, height:window.innerHeight,
        backgroundColor:"#0e1117", scale:Math.min(2,window.devicePixelRatio||1), useCORS:true, logging:false,
        ignoreElements:function(node){ return !!(node&&(node.id==="shotToast"||node.id==="shotFab")); } });
    }).then(function(canvas){ _shotToastHide(); _openAnnot(canvas); })
    .catch(function(e){ _shotToastHide(); if(fab)fab.style.display=""; _shotToast("⚠️ "+((e&&e.message)||e)); setTimeout(_shotToastHide,2600); });
  }
  function _openAnnot(baseCanvas){
    var W=baseCanvas.width, H=baseCanvas.height;
    var cv=document.createElement("canvas"); cv.width=W; cv.height=H;
    var ctx=cv.getContext("2d");
    var strokes=[], cur=null, drawing=false;
    var color="#ff3b30";
    var thin=Math.max(2,Math.round(W/220)), thick=Math.max(5,Math.round(W/80)), lw=thick;
    function redraw(){ ctx.clearRect(0,0,W,H); ctx.drawImage(baseCanvas,0,0); ctx.lineCap="round"; ctx.lineJoin="round";
      for(var i=0;i<strokes.length;i++){ var s=strokes[i]; ctx.strokeStyle=s.color; ctx.lineWidth=s.width; ctx.beginPath();
        for(var j=0;j<s.pts.length;j++){ var p=s.pts[j]; if(j===0)ctx.moveTo(p.x,p.y); else ctx.lineTo(p.x,p.y); }
        if(s.pts.length===1)ctx.lineTo(s.pts[0].x+0.2,s.pts[0].y+0.2); ctx.stroke(); } }
    redraw();
    var ov=el('<div id="shotOverlay" style="position:fixed;inset:0;z-index:1000;background:#0a0c10;display:flex;flex-direction:column;"></div>');
    var tb=el('<div style="display:flex;align-items:center;gap:6px;padding:8px 10px;background:#11151c;border-bottom:1px solid var(--bord);flex-wrap:wrap;"></div>');
    var colors=["#ff3b30","#ffcc00","#34c759","#0a84ff","#ffffff","#111111"];
    colors.forEach(function(c){ var sw=el('<button class="swt" style="width:30px;height:30px;border-radius:50%;border:2px solid '+(c===color?"#fff":"transparent")+';background:'+c+';padding:0;"></button>'); sw.dataset.c=c; sw.addEventListener("click",function(){ color=c; refreshSw(); }); tb.appendChild(sw); });
    function refreshSw(){ Array.prototype.forEach.call(tb.querySelectorAll(".swt"),function(x){ x.style.borderColor=(x.dataset.c===color)?"#fff":"transparent"; }); }
    var wbtn=el('<button class="ghost" style="padding:4px 10px;">✏️ silné</button>');
    wbtn.addEventListener("click",function(){ lw=(lw===thick)?thin:thick; wbtn.textContent=(lw===thick)?"✏️ silné":"✏️ tenké"; });
    var ub=el('<button class="ghost" style="padding:4px 10px;">↶ Zpět</button>'); ub.addEventListener("click",function(){ strokes.pop(); redraw(); });
    var clb=el('<button class="ghost" style="padding:4px 10px;">🗑</button>'); clb.addEventListener("click",function(){ strokes=[]; redraw(); });
    var xb=el('<button class="warn" style="padding:4px 12px;margin-left:auto;">✕</button>'); xb.addEventListener("click",closeOv);
    tb.appendChild(wbtn); tb.appendChild(ub); tb.appendChild(clb); tb.appendChild(xb);
    var wrap=el('<div style="flex:1;overflow:auto;display:flex;align-items:flex-start;justify-content:center;background:#000;"></div>');
    cv.style.width="100%"; cv.style.height="auto"; cv.style.display="block"; cv.style.touchAction="none";
    wrap.appendChild(cv);
    var bb=el('<div style="padding:8px 10px calc(10px + env(safe-area-inset-bottom,0px));background:#11151c;border-top:1px solid var(--bord);display:flex;gap:8px;align-items:center;"></div>');
    var note=el('<input placeholder="Popisek (nepovinné)…" style="flex:1;background:#0e1117;border:1px solid var(--bord);border-radius:10px;color:#fff;padding:9px 10px;font-size:14px;">');
    var send=el('<button class="green" style="padding:10px 14px;white-space:nowrap;">📤 Claudovi</button>');
    send.addEventListener("click",doSend);
    bb.appendChild(note); bb.appendChild(send);
    ov.appendChild(tb); ov.appendChild(wrap); ov.appendChild(bb); document.body.appendChild(ov);
    function pt(ev){ var r=cv.getBoundingClientRect(); var kx=cv.width/r.width, ky=cv.height/r.height;
      var cx=(ev.touches&&ev.touches[0])?ev.touches[0].clientX:ev.clientX, cy=(ev.touches&&ev.touches[0])?ev.touches[0].clientY:ev.clientY;
      return {x:(cx-r.left)*kx, y:(cy-r.top)*ky}; }
    cv.addEventListener("pointerdown",function(ev){ ev.preventDefault(); drawing=true; cur={color:color,width:lw,pts:[pt(ev)]}; strokes.push(cur); redraw(); try{cv.setPointerCapture(ev.pointerId);}catch(e){} });
    cv.addEventListener("pointermove",function(ev){ if(!drawing)return; ev.preventDefault(); cur.pts.push(pt(ev)); redraw(); });
    cv.addEventListener("pointerup",function(){ drawing=false; });
    cv.addEventListener("pointercancel",function(){ drawing=false; });
    function closeOv(){ ov.remove(); window._shotOverlayBack=null; var fab=document.getElementById("shotFab"); if(fab)fab.style.display=""; }
    // Systémové Zpět = vrátit poslední tah (jako horní „↶ Zpět"); prázdné → zavřít.
    window._shotOverlayBack=function(){ if(strokes.length){ strokes.pop(); redraw(); return true; } closeOv(); return true; };
    function doSend(){
      send.disabled=true; send.textContent="⏳ Posílám…";
      var data; try{ data=cv.toDataURL("image/png"); }catch(e){ send.disabled=false; send.textContent="📤 Claudovi"; _shotToast("⚠️ Snímek nelze uložit (CORS)"); setTimeout(_shotToastHide,2200); return; }
      api("POST","/api/v1/erp/app/screenshot",{img_b64:data, note:(note.value||"").trim(), target:"claude"}).then(function(j){
        if(j&&j.ok){ closeOv(); _shotToast("✅ Odesláno Claudovi"); setTimeout(_shotToastHide,1800); }
        else { send.disabled=false; send.textContent="📤 Claudovi"; _shotToast("⚠️ "+((j&&j.error)||"nepodařilo se odeslat")); setTimeout(_shotToastHide,2600); }
      }).catch(function(){ send.disabled=false; send.textContent="📤 Claudovi"; _shotToast("⚠️ Nepodařilo se odeslat"); setTimeout(_shotToastHide,2600); });
    }
    refreshSw();
  }
  function set_shot(){ app.innerHTML=topbar("Snímek obrazovky", true); var p=el('<div class="panel"></div>');
    var on=_shotBtnOn();
    p.appendChild(el('<div class="hint" style="margin-bottom:8px;">Zmrazí aktuální obrazovku, můžeš do ní <b>nakreslit</b> (kroužky, šipky) a <b>odeslat Claudovi</b>. Hodí se, když chceš rychle ukázat, co je na obrazovce.</div>'));
    var t=el('<button class="'+(on?"ghost":"green")+' full" style="font-size:16px;">'+(on?"✅ Plovoucí 📷 zapnuté — klepni pro vypnutí":"📷 Zapnout plovoucí tlačítko snímku")+'</button>');
    t.addEventListener("click",function(){ on=!on; try{localStorage.setItem("stg_shot_btn",on?"1":"0");}catch(e){} _shotSyncBtn();
      t.className=(on?"ghost":"green")+" full"; t.style.fontSize="16px";
      t.textContent=on?"✅ Plovoucí 📷 zapnuté — klepni pro vypnutí":"📷 Zapnout plovoucí tlačítko snímku"; });
    p.appendChild(t);
    var tryb=el('<button class="ghost full" style="margin-top:10px;">📸 Vyzkoušet teď</button>');
    tryb.addEventListener("click",function(){ openShot(); });
    p.appendChild(tryb);
    p.appendChild(el('<div class="hint" style="margin-top:10px;">Plovoucí 📷 se ukáže vpravo dole na každé obrazovce. Po stisku obrazovku zmrazí — pak kresli prstem, vyber barvu a klepni „Claudovi".</div>'));
    app.appendChild(p); }

  // ===== Urgentní notifikace „nutně tě potřebuju" (Marti 11.6.2026) =====
  var _urgentAC=null, _urgentSentCount=0, _urgentInCount=0;
  function _homeNotifSum(){ return (notifCount||0)+(_urgentSentCount||0)+(_urgentInCount||0)+(_signPend||0); }
  function _urgentRing(){
    try{ if(navigator.vibrate) navigator.vibrate([220,120,220,120,320]); }catch(e){}
    try{
      _urgentAC=_urgentAC||new (window.AudioContext||window.webkitAudioContext)();
      if(_urgentAC.state==="suspended") _urgentAC.resume();
      var t0=_urgentAC.currentTime;
      [0,0.26,0.52].forEach(function(off){
        var o=_urgentAC.createOscillator(), g=_urgentAC.createGain();
        o.type="square"; o.frequency.value=880;
        g.gain.setValueAtTime(0.0001,t0+off);
        g.gain.exponentialRampToValueAtTime(0.13,t0+off+0.03);
        g.gain.exponentialRampToValueAtTime(0.0001,t0+off+0.19);
        o.connect(g); g.connect(_urgentAC.destination);
        o.start(t0+off); o.stop(t0+off+0.21);
      });
    }catch(e){}
  }
  function _urgentOverlay(it){
    if(document.getElementById("urgentOverlay")) return;
    var ov=el('<div id="urgentOverlay" style="position:fixed;inset:0;z-index:2000;background:rgba(120,12,12,.96);display:flex;flex-direction:column;align-items:center;justify-content:center;padding:24px;text-align:center;color:#fff;"></div>');
    ov.appendChild(el('<div style="font-size:54px;margin-bottom:4px;">🆘</div>'));
    ov.appendChild(el('<div style="font-size:22px;font-weight:800;">'+esc(it.od||"Někdo")+' tě nutně potřebuje</div>'));
    ov.appendChild(el('<div style="font-size:13px;opacity:.8;margin:2px 0 14px;">'+esc(it.cas||"")+'</div>'));
    if(it.message) ov.appendChild(el('<div style="font-size:17px;background:rgba(255,255,255,.12);border-radius:14px;padding:14px 16px;max-width:480px;width:100%;box-sizing:border-box;margin-bottom:16px;">'+esc(it.message)+'</div>'));
    var rin=el('<input placeholder="Rychlá odpověď (nepovinné)…" style="width:100%;max-width:480px;box-sizing:border-box;background:rgba(0,0,0,.25);border:1px solid rgba(255,255,255,.4);border-radius:12px;color:#fff;padding:12px 14px;font-size:15px;margin-bottom:14px;">');
    ov.appendChild(rin);
    var b=el('<button style="width:100%;max-width:480px;box-sizing:border-box;background:#fff;color:#7a0a0a;border:0;border-radius:14px;padding:16px;font-size:18px;font-weight:800;cursor:pointer;">✋ Reaguji</button>');
    b.addEventListener("click",function(){ b.disabled=true; b.textContent="…";
      api("POST","/api/v1/erp/app/urgent/ack",{id:it.id, reply:(rin.value||"").trim()}).then(function(j){
        ov.remove(); if(!(j&&j.ok)){ try{_shotToast("⚠️ "+((j&&j.error)||"chyba"));setTimeout(_shotToastHide,2000);}catch(e){} } }); });
    ov.appendChild(b); document.body.appendChild(ov);
  }
  function _urgentPoll(){
    api("GET","/api/v1/erp/app/urgent/inbox","").then(function(j){
      var items=(j&&j.items)||[];
      _urgentInCount=items.length;
      if(items.length){ _urgentOverlay(items[0]); _urgentRing(); }
      try{ renderNav(); }catch(e){}
    }).catch(function(){});
    _urgentSentRender();
  }
  // Indikátor na hlavní obrazovce: moje urgentní požadavky, které ještě běží.
  function _urgentSentRender(){
    var box=document.getElementById("urgentSent"); if(!box) return;
    api("GET","/api/v1/erp/app/urgent/sent","").then(function(j){
      var items=(j&&j.items)||[]; box.innerHTML=""; _urgentSentCount=items.length; try{ renderNav(); }catch(e){}
      items.forEach(function(it){
        var c=el('<div class="doch-pulse" style="background:rgba(120,12,12,.22);border:1px solid #a33;border-radius:14px;padding:12px 14px;margin-bottom:10px;display:flex;align-items:center;gap:10px;"></div>');
        c.appendChild(el('<div style="font-size:22px;">🆘</div>'));
        c.appendChild(el('<div style="flex:1;min-width:0;"><div style="font-weight:700;font-size:15px;">Běží: <b>'+esc(it.komu)+'</b></div><div style="color:var(--mut);font-size:12px;">od '+esc(it.cas||"")+' · čeká na reakci, ťuká mu</div></div>'));
        var x=el('<button style="flex:none;background:transparent;border:1px solid #a33;color:#ff9b9b;border-radius:10px;padding:8px 10px;font-size:13px;cursor:pointer;">Zrušit</button>');
        x.addEventListener("click",function(){ x.disabled=true; api("POST","/api/v1/erp/app/urgent/cancel",{id:it.id}).then(function(){ _urgentSentRender(); }); });
        c.appendChild(x); box.appendChild(c);
      });
    }).catch(function(){});
  }
  function urgent(){ app.innerHTML=topbar("🆘 Nutně sehnat", true); var p=el('<div class="panel"></div>');
    p.appendChild(el('<div class="hint" style="margin-bottom:8px;">Pošle urgentní upozornění, které se dotyčnému opakovaně připomíná (ťuká), dokud nezareaguje. Pak ti přijde potvrzení.</div>'));
    p.appendChild(el('<label>Zpráva (nepovinné)</label>'));
    var msg=el('<textarea placeholder="Co potřebuješ?" style="width:100%;box-sizing:border-box;min-height:64px;background:#0e1117;border:1px solid var(--bord);border-radius:12px;color:#fff;padding:10px;font-size:15px;"></textarea>');
    p.appendChild(msg);
    p.appendChild(el('<label style="margin-top:12px;display:block;">Komu (klepni)</label>'));
    var list=el('<div class="list"></div>'); list.appendChild(el('<div class="hint">Načítám lidi…</div>')); p.appendChild(list);
    api("GET","/api/v1/erp/app/urgent/people","").then(function(j){
      list.innerHTML=""; var ppl=(j&&j.lide)||[];
      if(!ppl.length){ list.appendChild(el('<div class="hint">Nikdo k dispozici.</div>')); return; }
      ppl.forEach(function(u){
        var b=el('<button class="ghost full" style="text-align:left;margin-bottom:6px;font-size:15px;">🆘 '+esc(u.jmeno)+'</button>');
        b.addEventListener("click",function(){ b.disabled=true; b.textContent="Posílám…";
          api("POST","/api/v1/erp/app/urgent/send",{to_user_id:u.user_id, message:(msg.value||"").trim()}).then(function(r){
            if(r&&r.ok){ b.textContent="✅ Odesláno: "+u.jmeno; try{_shotToast("🆘 Odesláno — bude ťukat, dokud nezareaguje");setTimeout(_shotToastHide,2200);}catch(e){} setTimeout(function(){back();},1000); }
            else { b.disabled=false; b.textContent="🆘 "+u.jmeno; alert("Chyba: "+((r&&r.error)||"?")); } }); });
        list.appendChild(b);
      });
    });
    app.appendChild(p);
  }

