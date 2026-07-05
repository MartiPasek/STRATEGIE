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

  function plan(){
    var AP=window._planApprove||null; window._planApprove=null;   // režim schvalovatele (cizí plán)
    var WEEKONLY=(window._planInit==="thisweek");                 // jen tento týden (z dlaždice Týden)
    app.innerHTML=topbar(AP?("🗓️ "+esc(AP.name)):(WEEKONLY?("📅 Týden "+_isoWeek(new Date())):"🗓️ Plán"), true);
    var _ptb=app.querySelector('.topbar'); if(_ptb)_ptb.style.paddingTop="12px";
    function nf(v){ return (Math.round((v||0)*100)/100).toString().replace('.',','); }
    function czd(iso){ var p=(iso||"").split("-"); return p.length===3?(p[2]+"."+p[1]+"."):iso; }
    var wrap=el('<div style="display:flex;gap:10px;height:calc(100vh - 132px);align-items:stretch;"></div>');
    var left=el('<div style="flex:1;min-width:0;overflow-y:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none;padding-bottom:100px;"></div>');
    var right=el('<div style="width:88px;flex:none;display:flex;flex-direction:column;gap:8px;overflow-y:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none;padding-bottom:100px;"></div>');
    wrap.appendChild(left); wrap.appendChild(right); app.appendChild(wrap);
    // Marti 14.6. večer: v Týdnu navigace týdnů ↑ (předchozí) / ↓ (další) na vrchu lišty.
    if(WEEKONLY){
      var bUp=el('<button class="ghost" style="padding:12px 4px;text-align:center;border-color:#3a5a8c;color:#9cf;font-weight:700;font-size:13px;line-height:1.25;">⬆️<br>Předch.<br>týden</button>');
      bUp.addEventListener("click",function(){ try{ window._planWeekShift && window._planWeekShift(-1); }catch(e){} });
      right.appendChild(bUp);
      var bDn=el('<button class="ghost" style="padding:12px 4px;text-align:center;border-color:#3a5a8c;color:#9cf;font-weight:700;font-size:13px;line-height:1.25;">⬇️<br>Další<br>týden</button>');
      bDn.addEventListener("click",function(){ try{ window._planWeekShift && window._planWeekShift(1); }catch(e){} });
      right.appendChild(bDn);
    }
    // Marti 14.6. večer: pořadí lišty shora dolů — Můj plán, Moje podmínky,
    // Koho čekáme, Plán skupiny, [admin:] Skupiny výjimky, Firma plán, Firma výjimky, ČR 40h.
    var bMy=el('<button class="ghost" style="padding:12px 4px;text-align:center;border-color:#3a6b4c;color:#9ce0b0;font-weight:700;font-size:12px;line-height:1.25;">👤<br>Můj<br>plán</button>');
    bMy.addEventListener("click",function(){ renderPlan(false,'mydefault'); });
    var bUv=el('<button class="ghost" style="padding:12px 4px;text-align:center;border-color:#6b4a2a;color:#e6b97a;font-weight:700;font-size:12px;line-height:1.25;">📋<br>Moje<br>podmínky</button>');
    bUv.addEventListener("click",function(){ renderPodminky(); });
    var bDay=el('<button class="ghost" style="padding:12px 4px;text-align:center;border-color:#2a6b3a;color:#8fe0a0;font-weight:700;font-size:12px;line-height:1.25;">📊<br>Koho<br>čekáme</button>');
    bDay.addEventListener("click",function(){ renderDay(); });
    var bGrp=el('<button class="ghost" style="padding:12px 4px;text-align:center;border-color:#2a5a6b;color:#7fc8e0;font-weight:700;font-size:12px;line-height:1.25;">👥<br>Plán<br>skupiny</button>');
    bGrp.addEventListener("click",function(){ renderGroupPlan(); });
    var bFirma=el('<button class="ghost" style="padding:12px 4px;text-align:center;border-color:#2a6b5a;color:#7fe0c8;font-weight:700;font-size:12px;line-height:1.25;">🏭<br>Firma<br>plán</button>');
    bFirma.addEventListener("click",function(){ renderPlan(true); });
    var bScope=el('<button class="ghost" style="padding:12px 4px;text-align:center;border-color:#5a3a6b;color:#c9a6e6;font-weight:700;font-size:12px;line-height:1.25;">👥<br>Skupiny<br>výjimky</button>');
    bScope.addEventListener("click",function(){ renderExc('scope'); });
    var bExc=el('<button class="ghost" style="padding:12px 4px;text-align:center;border-color:#6b5a2a;color:#e6c86a;font-weight:700;font-size:12px;line-height:1.25;">🏢<br>Firma<br>výjimky</button>');
    bExc.addEventListener("click",function(){ renderExc('firma'); });
    var bGen=el('<button class="ghost" style="padding:12px 4px;text-align:center;border-color:#3a5a8c;color:#9cf;font-weight:700;font-size:13px;line-height:1.25;">📋<br>ČR<br>40 h</button>');
    bGen.addEventListener("click",function(){
      if(!confirm("Vygenerovat základní roční plán 40 h/týden (Po–Pá podle státních svátků)?")) return;
      bGen.disabled=true;
      api("POST","/api/v1/erp/app/plan/generate-base",{uvazek:40}).then(function(r){
        bGen.disabled=false;
        if(r&&r.ok){ renderPlan(); } else alert("Chyba: "+((r&&r.error)||"?"));
      });
    });
    // pořadí appendů = shora dolů
    right.appendChild(bMy);
    (function(){
      api("GET","/api/v1/erp/app/plan/requests?from="+_locDate(-365)+"&to="+_locDate(365),"").then(function(rq){
        var n=(((rq&&rq.items)||[]).filter(function(r){ return r&&r.status==='pending'; })).length;
        if(n>0){ bMy.style.position="relative"; bMy.appendChild(el('<span style="position:absolute;top:-5px;right:-5px;background:#f59e0b;color:#fff;font-size:10px;min-width:16px;height:16px;line-height:16px;border-radius:8px;padding:0 4px;text-align:center;font-weight:700;">'+(n>99?"99+":n)+'</span>')); }
      }).catch(function(){});
    })();
    right.appendChild(bUv);
    right.appendChild(bDay);
    right.appendChild(bGrp);
    if(!WEEKONLY){
      right.appendChild(bScope);
      right.appendChild(bFirma);
      right.appendChild(bExc);
      right.appendChild(el('<div class="hint" style="text-align:center;font-size:10px;line-height:1.3;margin-top:4px;">Vyrobit<br>základ</div>'));
      right.appendChild(bGen);
    }
    function czd2(iso){ var p=(iso||"").split("-"); return p.length===3?(p[2]+"."+p[1]+"."+p[0]):iso; }
    function renderPlan(eff, src){
      left.innerHTML='<div class="hint">Načítám…</div>';
      var _url= eff ? "/api/v1/erp/app/plan/firma"
              : (src==='mydefault') ? ("/api/v1/erp/app/plan/my-default"+(AP?("?user_id="+AP.user_id):""))
              : "/api/v1/erp/app/plan/mine?weeks=10";
      api("GET",_url,"").then(function(j){
        left.innerHTML="";
        if(!j||!j.ok){ left.appendChild(el('<div class="hint">Nelze načíst.</div>')); return; }
        if(!j.has_plan){ left.appendChild(el('<div class="hint" style="line-height:1.7;">Zatím nemáš žádný plán.<br>Vpravo klikni <b>📋 40 h</b> a vyrobí se ti základní roční plán podle státních svátků (Po–Pá, víkendy a svátky volno).</div>')); return; }
        if(src==='mydefault'){ renderWeeks(left, j, src); }
        else { renderMonths(left, j, eff, src, null); }
      });
    }
    // Marti 14.6.: Můj plán = TÝDENNÍ pohled — týdny aktivně oddělené, baseline plánu.
    // (Základ pro budoucí „Můj plán ke schválení" — kalendářní vkládání návrhů.)
    function renderWeeks(box, j, src){
      var fromD=(j.plan[0]&&j.plan[0].date)||_locDate(0);
      var toD=(j.plan[j.plan.length-1]&&j.plan[j.plan.length-1].date)||_locDate(0);
      var todayIso=_locDate(0);
      var iS="box-sizing:border-box;width:100%;padding:9px;border-radius:9px;border:1px solid #2b3a5c;background:#0a1226;color:#e8eefc;margin:2px 0;font-size:14px;";
      var ST={view:'list', wk:null, byDate:{}, weeks:{}, order:[], nowKey:null, weekKey:null, pend:0, listScroll:0};
      function stCol(s){ return s==='approved'?'#34d399':(s==='rejected'?'#f87171':'#fbbf24'); }
      function stIc(s){ return s==='approved'?'✓':(s==='rejected'?'✕':'⏳'); }
      function kLabel(r){
        if(r.kind==='off') return '🏝️ volno';
        if(r.kind==='meeting') return '🤝 '+(r.title||'porada/jednání')+(r.start?(' '+r.start+(r.end?('–'+r.end):'')):'');
        if(r.kind==='event') return '📌 '+(r.title||'akce')+(r.start?(' '+r.start):'');
        // hodiny: stejný formát jako plán — „od 10:00 · 8 h" (vlevo zůstane jen status ⏳)
        return (r.start?('od '+r.start+' · '):'')+(r.hours!=null?_hhmm(r.hours):'jiné hodiny');
      }
      function wkPend(ds){ var n=0; ds.forEach(function(d){ (ST.byDate[d.date]||[]).forEach(function(r){ if(r.status==='pending')n++; }); }); return n; }
      // Bod 3: root = jen seznam týdnů (klik = celý týden). Editace dnů až v týdnu.
      function showList(doScroll){
        ST.view='list'; ST.wk=null; box.innerHTML="";
        if(right)right.style.display=AP?'none':'flex';  // schvalovatel: bez admin lišty (flex, ne '' — jinak ztratí sloupec)
        var gt=0; j.plan.forEach(function(d){ gt+=d.hours; });
        var yr=(j.plan[0]&&j.plan[0].date||"").slice(0,4);
        box.appendChild(el('<div style="margin-bottom:4px;"><b>👤 '+(AP?esc(AP.name):'Můj plán')+' '+yr+'</b> <span class="hint">· úvazek '+(j.uvazek||"?")+' h/týd. · '+nf(gt)+' h</span></div>'));
        box.appendChild(el('<div class="hint" style="margin-bottom:10px;line-height:1.5;">'+(AP?'Klepni na týden — uvidíš návrhy a můžeš je schválit/zamítnout.':'Klepni na týden — otevře se celý. Tam přidáš návrhy ke schválení.')+(ST.pend?(' <b style="color:var(--amber);">· '+ST.pend+' čeká</b>'):'')+'</div>'));
        var curCard=null, todayEl=null, cardByKey={}, firstPendCard=null;
        var _keys = WEEKONLY ? (ST.weekKey ? [ST.weekKey] : ST.order.slice(0,1)) : ST.order;
        _keys.forEach(function(k){
          var ds=ST.weeks[k], sum=0, wd=0; ds.forEach(function(d){ sum+=d.hours; if(d.hours>0)wd++; });
          var lastD=ds[ds.length-1].date, isPast=(lastD<todayIso), isCur=(k===ST.nowKey);
          var pc=wkPend(ds);
          var card=el('<div style="border:1px solid '+(isCur?'#4f8ef7':'#2b3a5c')+';border-radius:12px;margin-bottom:10px;overflow:hidden;cursor:pointer;'+(isPast?'opacity:.5;':'')+'"></div>');
          var _hl,_hr;
          if(WEEKONLY){ _hl='Plán · '+ds[0].iso_week+'. týden'; _hr='<b style="font-size:16px;color:#cfe0ff;">'+_hhmm(sum)+'</b>'; }
          else { _hl='Týden '+ds[0].iso_week+(isCur?' · tento týden':''); _hr='<span class="hint">'+wd+' dní · '+_hhmm(sum)+'</span>'; }
          card.appendChild(el('<div style="padding:11px 12px;background:'+(isCur?'#11203a':(isPast?'#0c1018':'#0e1830'))+';display:flex;justify-content:space-between;align-items:center;'+(isCur?'border-left:3px solid #4f8ef7;':'')+'"><span style="font-weight:700;">'+_hl+'</span><span style="display:flex;align-items:center;gap:8px;">'+_hr+(pc?('<span style="color:var(--amber);font-size:12px;font-weight:700;">'+pc+'⏳</span>'):'')+'<span style="color:var(--mut);">›</span></span></div>'));
          var body=el('<div style="padding:4px 10px 8px;"></div>');
          ds.forEach(function(d){
            var dwork=(d.hours>0);
            var dcol=dwork?"#34d399":(d.day_type==="holiday"?"#fbbf24":(d.day_type==="exoff"?"#e6a93a":"#5b6b88"));
            var dToday=(d.date===todayIso); var dPast=(d.date<todayIso);
            var dReqs=ST.byDate[d.date]||[];
            // korekce typu hodiny/volno NAHRAZUJE plán → přeškrtnout původní hodnotu
            var hasRepl=dReqs.some(function(r){ return (r.kind==='hours'||r.kind==='off') && r.status!=='rejected'; });
            var rs="display:flex;justify-content:space-between;align-items:center;padding:5px 4px;font-size:13px;border-bottom:1px solid rgba(255,255,255,.05);"+(dToday?"background:rgba(79,142,247,.14);border-radius:6px;":"")+(dPast?"opacity:.45;":"");
            var rightCell;
            if(dwork){
              var _strk=hasRepl?'text-decoration:line-through;opacity:.55;':'';
              rightCell='<span style="display:inline-flex;align-items:baseline;gap:10px;'+_strk+'"><span style="color:#8fb4e8;font-size:12px;min-width:56px;text-align:right;">'+(d.start?'od '+d.start:'')+'</span><span style="color:#34d399;font-weight:700;min-width:46px;text-align:right;">'+_hhmm(d.hours)+'</span></span>';
            } else {
              var _lbl2=(d.day_type==="holiday")?"svátek":((d.day_type==="weekend")?"víkend":((d.day_type==="exoff")?((d.exc_scope==='osobní'?'👤 osobní':(d.exc_scope==='skupina'?'👥 skupinové':'🏢 celofiremní'))+' volno'):"volno"));
              rightCell='<span style="color:'+dcol+';font-weight:600;'+(hasRepl?'text-decoration:line-through;opacity:.55;':'')+'">'+_lbl2+'</span>';
            }
            var row=el('<div style="'+rs+'"><span'+(dToday?' style="font-weight:700;"':'')+'>'+(dToday?'▶ ':'')+d.weekday+' '+czd(d.date)+'</span>'+rightCell+'</div>');
            body.appendChild(row);
            if(dToday) todayEl=row;
            dReqs.forEach(function(r){
              // korekce vpravo zarovnaná, pod původní hodnotou
              body.appendChild(el('<div style="text-align:right;margin:1px 4px 5px;font-size:12px;color:'+stCol(r.status)+';">'+stIc(r.status)+' '+esc(kLabel(r))+'</div>'));
            });
          });
          card.appendChild(body);
          card.addEventListener("click",function(){ showWeek(k); });
          box.appendChild(card);
          cardByKey[k]=card;
          if(isCur) curCard=card;
          if(pc>0 && !firstPendCard) firstPendCard=card;   // první týden s čekajícím návrhem
        });
        // Nascrolovat na DNEŠEK jen při PRVNÍM otevření (ne při návratu z týdne).
        // Schvalovatel: nascrolluj na první týden, kde něco čeká na schválení.
        var target=(AP&&firstPendCard)?firstPendCard:(todayEl||curCard);
        if(doScroll && target){ setTimeout(function(){ try{ target.scrollIntoView({behavior:"smooth",block:"center"}); }catch(e){} },40); }
        else if(ST.openWk && cardByKey[ST.openWk]){ setTimeout(function(){ try{ cardByKey[ST.openWk].scrollIntoView({block:"start"}); }catch(e){} },30); }
        if(WEEKONLY){ _realityCard(box, ST.weeks[ST.weekKey]||ST.weeks[ST.nowKey]||[]); }
      }
      function _hhmm(h){ h=Math.max(0, Math.round((h||0)*60)); return Math.floor(h/60)+":"+("0"+(h%60)).slice(-2); }
      function _realityCard(box, days){
        if(!days.length) return;
        var fromD2=days[0].date, toD2=days[days.length-1].date;
        var card=el('<div style="border:1px solid #2b3a5c;border-radius:12px;margin-bottom:10px;overflow:hidden;"></div>');
        card.appendChild(el('<div style="padding:11px 12px;background:#0e1830;display:flex;justify-content:space-between;align-items:center;"><span style="font-weight:700;">Realita</span><b id="realSum" style="font-size:16px;color:#cfe0ff;">…</b></div>'));
        var body=el('<div style="padding:4px 10px 8px;"></div>');
        body.appendChild(el('<div class="hint" style="padding:6px 2px;">Načítám…</div>'));
        card.appendChild(body); box.appendChild(card);
        api("GET","/api/v1/erp/app/attendance/real?from="+fromD2+"&to="+toD2,"").then(function(j){
          body.innerHTML="";
          var by={}; ((j&&j.days)||[]).forEach(function(r){ by[r.d]=r; });
          var tot=0;
          days.forEach(function(d){
            var rr=by[d.date]; var w=(rr&&rr.worked)?parseFloat(rr.worked):0; tot+=w;
            var dToday=(d.date===todayIso), dPast=(d.date<todayIso);
            var rs="display:flex;justify-content:space-between;align-items:center;padding:5px 4px;font-size:13px;border-bottom:1px solid rgba(255,255,255,.05);"+(dToday?"background:rgba(79,142,247,.14);border-radius:6px;":"")+((dPast&&!w)?"opacity:.45;":"");
            var rightCell;
            if(w>0){
              rightCell='<span style="display:inline-flex;align-items:baseline;gap:10px;"><span style="color:#8fb4e8;font-size:12px;min-width:56px;text-align:right;">'+(rr&&rr.zac?'od '+rr.zac:'')+'</span><span style="color:#34d399;font-weight:700;min-width:46px;text-align:right;">'+_hhmm(w)+'</span></span>';
            } else { rightCell='<span style="color:#5b6b88;font-weight:600;">—</span>'; }
            body.appendChild(el('<div style="'+rs+'"><span'+(dToday?' style="font-weight:700;"':'')+'>'+(dToday?'▶ ':'')+d.weekday+' '+czd(d.date)+'</span>'+rightCell+'</div>'));
          });
          var sm=document.getElementById("realSum"); if(sm)sm.textContent=_hhmm(tot);
        }).catch(function(){ body.innerHTML='<div class="hint" style="padding:6px 2px;">Nepodařilo se načíst realitu.</div>'; });
      }
      function openForm(d, host){
        var ex=host.querySelector('.reqform'); if(ex){ ex.remove(); return; }
        var f=el('<div class="reqform" style="margin:2px 0 8px 12px;padding:9px;border:1px solid #3a4d6b;border-radius:10px;background:rgba(79,142,247,.06);"></div>');
        f.appendChild(el('<div class="hint" style="margin-bottom:7px;">Návrh na <b>'+d.weekday+' '+czd(d.date)+'</b>:</div>'));
        var cur={kind:'hours'};
        var kindRow=el('<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px;"></div>');
        var fields=el('<div></div>'); var elH,elS,elE,elT,elN;
        function buildFields(){
          fields.innerHTML="";
          if(cur.kind==='hours'){
            fields.appendChild(el('<label class="hint">Kolik hodin</label>'));
            elH=el('<input type="number" min="0" max="24" step="0.5" value="'+(d.hours||8)+'" style="'+iS+'">'); fields.appendChild(elH);
            fields.appendChild(el('<label class="hint">Příchod od (volitelně)</label>'));
            elS=el('<input type="time" value="'+(d.start||"")+'" style="'+iS+'">'); fields.appendChild(elS);
          } else if(cur.kind==='off'){
            fields.appendChild(el('<div class="hint" style="padding:4px 0;">Navrhuješ na tento den volno.</div>'));
          } else if(cur.kind==='meeting'){
            fields.appendChild(el('<label class="hint">Název (porada / jednání)</label>'));
            elT=el('<input placeholder="např. Porada výroby" style="'+iS+'">'); fields.appendChild(elT);
            fields.appendChild(el('<label class="hint">Od – do</label>'));
            var tr=el('<div style="display:flex;gap:6px;"></div>');
            elS=el('<input type="time" style="'+iS+'flex:1;">'); elE=el('<input type="time" style="'+iS+'flex:1;">');
            tr.appendChild(elS); tr.appendChild(elE); fields.appendChild(tr);
          }
          elN=el('<input placeholder="Poznámka (volitelně)" style="'+iS+'">'); fields.appendChild(elN);
        }
        function mkChip(lbl,kk){ var b=el('<button class="ghost" style="padding:6px 10px;font-size:12px;">'+lbl+'</button>');
          b.addEventListener("click",function(){ f.dataset.dirty='1'; cur.kind=kk; [].forEach.call(kindRow.children,function(c){c.style.borderColor='';c.style.color='';}); b.style.borderColor='var(--blue)'; b.style.color='var(--blue)'; buildFields(); }); return b; }
        kindRow.appendChild(mkChip('⏱ Jiné hodiny','hours'));
        kindRow.appendChild(mkChip('🏝️ Volno','off'));
        kindRow.appendChild(mkChip('🤝 Porada/jednání','meeting'));
        f.appendChild(kindRow);
        kindRow.children[0].style.borderColor='var(--blue)'; kindRow.children[0].style.color='var(--blue)'; buildFields();
        f.appendChild(fields);
        var sb=el('<button class="green full" style="margin-top:8px;">Odeslat ke schválení →</button>');
        sb.addEventListener("click",function(){ sb.disabled=true;
          var pl={date:d.date, kind:cur.kind, note:(elN&&elN.value)||""};
          if(cur.kind==='hours'){ pl.hours=(elH&&elH.value)||""; pl.start=(elS&&elS.value)||""; }
          else if(cur.kind==='meeting'){ pl.title=(elT&&elT.value)||"Porada/jednání"; pl.start=(elS&&elS.value)||""; pl.end=(elE&&elE.value)||""; }
          api("POST","/api/v1/erp/app/plan/request",pl).then(function(r){ if(r&&r.ok){ load(); } else { sb.disabled=false; alert("Chyba: "+((r&&r.error)||"?")); } });
        });
        f.appendChild(sb);
        f.addEventListener('input',function(){ f.dataset.dirty='1'; });
        host.appendChild(f);
        try{ f.scrollIntoView({behavior:"smooth",block:"center"}); }catch(e){}
      }
      function showWeek(k){
        ST.openWk=k;   // zapamatuj otevřený týden → po návratu na něj odscrolujeme
        ST.view='week'; ST.wk=k; var ds=ST.weeks[k]; if(!ds){ showList(); return; }
        box.innerHTML="";
        if(right)right.style.display='none';  // #2: detail týdne na celou šířku
        var bk=el('<button id="planWeekBack" class="ghost full" style="margin-bottom:10px;">'+(WEEKONLY?'‹ Zpět':'‹ Zpět na týdny')+'</button>'); bk.addEventListener("click",function(){ planBackStep(); }); box.appendChild(bk);
        var sum=0,wd=0; ds.forEach(function(d){ sum+=d.hours; if(d.hours>0)wd++; });
        box.appendChild(el('<div style="margin-bottom:8px;"><b>Týden '+ds[0].iso_week+'</b> <span class="hint">· '+wd+' dní · '+_hhmm(sum)+' · '+czd(ds[0].date)+'–'+czd(ds[ds.length-1].date)+'</span></div>'));
        box.appendChild(el('<div class="hint" style="margin-bottom:8px;">'+(AP?'Návrhy dne schválíš ✓ nebo zamítneš ✕ u příslušného řádku.':'Klepni na den a přidej návrh (jiné hodiny / volno / porada–jednání).')+'</div>'));
        ds.forEach(function(d){
          var work=(d.hours>0);
          var col=work?"#34d399":(d.day_type==="holiday"?"#fbbf24":"#5b6b88");
          var tag=work?((d.start?('od '+d.start+' · '):'')+_hhmm(d.hours)):(d.day_type==="holiday"?"svátek":(d.day_type==="weekend"?"víkend":"volno"));
          var dPast=(d.date<todayIso), dToday=(d.date===todayIso);
          var dReqs=ST.byDate[d.date]||[];
          var hasRepl=dReqs.some(function(r){ return (r.kind==='hours'||r.kind==='off') && r.status!=='rejected'; });
          var dayWrap=el('<div></div>');
          var rs="display:flex;justify-content:space-between;align-items:center;padding:9px 6px;font-size:14px;border-bottom:1px solid rgba(255,255,255,.06);cursor:pointer;"+(dToday?"background:rgba(79,142,247,.14);border-radius:8px;":"")+(dPast?"opacity:.5;":"");
          var tagSt="color:"+col+";font-weight:600;"+(hasRepl?"text-decoration:line-through;opacity:.55;":"");
          var plusHtml=AP?'':'<span style="display:inline-flex;align-items:center;justify-content:center;width:24px;height:24px;border-radius:50%;background:rgba(79,142,247,.18);color:#4f8ef7;font-size:17px;font-weight:700;line-height:1;flex:none;">+</span>';
          var row=el('<div style="'+rs+(AP?'cursor:default;':'')+'"><span'+(dToday?' style="font-weight:700;"':'')+'>'+(dToday?'▶ ':'')+d.weekday+' '+czd(d.date)+'</span><span style="display:flex;align-items:center;gap:8px;"><span style="'+tagSt+'">'+tag+'</span>'+plusHtml+'</span></div>');
          if(!AP){ row.addEventListener("click",function(){ openForm(d, dayWrap); }); }
          dayWrap.appendChild(row);
          (ST.byDate[d.date]||[]).forEach(function(r){
            var chip=el('<div style="display:flex;justify-content:space-between;align-items:center;gap:6px;margin:3px 6px 6px 14px;font-size:12.5px;"><span style="color:'+stCol(r.status)+';">'+stIc(r.status)+' '+esc(kLabel(r))+(r.note?(' — '+esc(r.note)):'')+(r.status==='rejected'&&r.decided_note?(' ('+esc(r.decided_note)+')'):'')+'</span></div>');
            if(AP){
              if(r.status==='pending'){
                var bw=el('<div style="display:flex;gap:6px;flex:none;"></div>');
                var ya=el('<button style="display:inline-flex;align-items:center;justify-content:center;width:26px;height:26px;border-radius:50%;background:rgba(52,211,153,.18);color:#34d399;border:0;font-size:14px;line-height:1;cursor:pointer;" title="Schválit">✓</button>');
                var na=el('<button style="display:inline-flex;align-items:center;justify-content:center;width:26px;height:26px;border-radius:50%;background:rgba(248,113,113,.16);color:#f87171;border:0;font-size:13px;line-height:1;cursor:pointer;" title="Zamítnout">✕</button>');
                ya.addEventListener("click",function(e){ e.stopPropagation(); ya.disabled=true; na.disabled=true; apDecideCal(r.id,"approved",null); });
                na.addEventListener("click",function(e){ e.stopPropagation(); apRejectDialog(r, function(note){ apDecideCal(r.id,"rejected",note); }); });
                bw.appendChild(ya); bw.appendChild(na); chip.appendChild(bw);
              }
            } else if(r.status==='pending'){
              var db=el('<button style="display:inline-flex;align-items:center;justify-content:center;width:24px;height:24px;border-radius:50%;background:rgba(248,113,113,.16);color:#f87171;border:0;font-size:13px;line-height:1;cursor:pointer;flex:none;" title="Smazat">✕</button>'); db.addEventListener("click",function(e){ e.stopPropagation(); if(!confirm("Chceš tento záznam opravdu smazat?")) return; db.disabled=true; api("POST","/api/v1/erp/app/plan/request/"+r.id+"/delete","").then(function(){ load(); }); }); chip.appendChild(db);
            }
            dayWrap.appendChild(chip);
          });
          box.appendChild(dayWrap);
        });
      }
      function apDecideCal(id, decision, note){
        api("POST","/api/v1/erp/app/plan/decide",{id:id,decision:decision,note:note||""}).then(function(x){
          if(x&&x.ok){ load(); } else alert("Chyba: "+((x&&x.error)||"?")); });
      }
      function load(){
        box.innerHTML='<div class="hint">Načítám…</div>';
        var _ru=AP?("/api/v1/erp/app/plan/approvals/user/"+AP.user_id+"?all=1"):("/api/v1/erp/app/plan/requests?from="+fromD+"&to="+toD);
        api("GET",_ru,"").then(function(rq){
          var reqs=(rq&&rq.ok&&rq.items)||[];
          ST.byDate={}; reqs.forEach(function(r){ (ST.byDate[r.d]=ST.byDate[r.d]||[]).push(r); });
          ST.pend=reqs.filter(function(r){return r.status==='pending';}).length;
          ST.weeks={}; ST.order=[]; ST.nowKey=null;
          j.plan.forEach(function(d){ var k=d.date.slice(0,4)+"-W"+("0"+d.iso_week).slice(-2); if(!ST.weeks[k]){ST.weeks[k]=[];ST.order.push(k);} ST.weeks[k].push(d); });
          ST.order.forEach(function(k){ if(ST.weeks[k].some(function(d){return d.date===todayIso;})) ST.nowKey=k; });
          if(WEEKONLY){
            // plnou sadu týdnů NECHÁVÁME (kvůli navigaci ↑/↓), zobrazíme jen weekKey
            if(!ST.weekKey || ST.order.indexOf(ST.weekKey)<0) ST.weekKey = ST.nowKey || ST.order[0];
            showList(true);
          }
          else if(ST.view==='week' && ST.weeks[ST.wk]) showWeek(ST.wk); else showList(true);
        });
      }
      // Bod 4: Zpět o jeden krok — z týdne zpět na seznam (ne rovnou pryč).
      function planBackStep(){
        // #1: rozdělaný návrh? Zpět nejdřív zavře formulář — když je změněný, zeptá se na uložení.
        var f=box.querySelector('.reqform');
        if(f){
          if(f.dataset.dirty==='1'){ planAskSave(f); return true; }
          f.remove(); return true;
        }
        if(document.getElementById('planWeekBack')){ showList(false); return true; }
        return false;
      }
      function planAskSave(f){
        var ov=el('<div class="appmodal" style="position:fixed;inset:0;z-index:99999;background:rgba(3,7,16,.66);display:flex;align-items:center;justify-content:center;padding:24px;"></div>');
        var card=el('<div style="background:#161c2b;border:1px solid rgba(255,255,255,.12);border-radius:16px;padding:22px 20px;max-width:320px;width:100%;box-shadow:0 16px 50px rgba(0,0,0,.55);"></div>');
        card.appendChild(el('<div style="font-size:16px;font-weight:600;color:#e8eefc;text-align:center;margin-bottom:18px;">Mám uložit změny?</div>'));
        var rowb=el('<div style="display:flex;gap:10px;"></div>');
        var yes=el('<button class="green" style="flex:1;margin:0;">Ano</button>');
        var no=el('<button class="ghost" style="flex:1;margin:0;">Ne</button>');
        yes.addEventListener("click",function(){ ov.remove(); var sb=f.querySelector('.green.full'); if(sb){ sb.click(); } });
        no.addEventListener("click",function(){ ov.remove(); f.remove(); });
        rowb.appendChild(yes); rowb.appendChild(no); card.appendChild(rowb);
        ov.appendChild(card); document.body.appendChild(ov);
      }
      window._planAnyOpen=planBackStep;
      // Marti 14.6. večer: navigace týdnů v Týdnu (↑/↓ z pravé lišty). -1 = předchozí, +1 = další.
      window._planWeekShift=function(delta){
        if(!ST.order.length) return;
        var i=ST.order.indexOf(ST.weekKey); if(i<0)i=0;
        var ni=Math.min(ST.order.length-1, Math.max(0, i+delta));
        if(ni===i) return;
        ST.weekKey=ST.order[ni];
        showList(false);
        try{ left.scrollTop=0; }catch(e){}
      };
      load();
    }
    function renderMonths(box, j, eff, src, titleOverride){
      var yr=(j.plan[0]&&j.plan[0].date||"").slice(0,4);
      var effH=function(d){ return (eff&&d.exc_hours!==null&&d.exc_hours!==undefined)?d.exc_hours:d.hours; };
      var effT=function(d){ return (eff&&d.exc_hours!==null&&d.exc_hours!==undefined)?(d.exc_hours>0?'exception':'exoff'):d.day_type; };
      var gt=0; j.plan.forEach(function(d){ gt+=effH(d); });
      var _ttl=titleOverride||(eff?('🏭 Firma plán '+yr):(src==='mydefault'?('👤 Můj výchozí plán '+yr):('ČR plán '+yr)));
      var _sub=eff?'po výjimkách':('úvazek '+(j.uvazek||"?")+' h/týd.');
      box.appendChild(el('<div style="margin-bottom:8px;"><b>'+_ttl+'</b> <span class="hint">· '+_sub+' · '+nf(gt)+' h</span></div>'));
      var MN=["Leden","Únor","Březen","Duben","Květen","Červen","Červenec","Srpen","Září","Říjen","Listopad","Prosinec"];
      var nowM=(new Date()).getFullYear()+"-"+("0"+((new Date()).getMonth()+1)).slice(-2);
      var _todayIso=_locDate(0);  // Marti 14.6.: odlišit minulost / současnost / budoucnost
      var months={}, order=[];
      j.plan.forEach(function(d){ var m=d.date.slice(0,7); if(!months[m]){ months[m]=[]; order.push(m);} months[m].push(d); });
      var entries=[];
      function closeAll(){ entries.forEach(function(e){ e.body.style.display="none"; e.arr.innerHTML=e.summary+' ▸'; }); }
      order.forEach(function(m){
        var days=months[m], sum=0, wd=0, hol=0;
        days.forEach(function(d){ var h=effH(d), tp=effT(d); sum+=h; if(tp==="work"||tp==="exception") wd++; else if(tp==="holiday") hol++; });
        function svL(n){ return n+' '+(n===1?'svátek':(n>=2&&n<=4?'svátky':'svátků')); }
        var summary=wd+' prac. dní · '+nf(sum)+' h';
        var mi=parseInt(m.slice(5,7),10)-1;
        var _isPastM=(m<nowM), _isCurM=(m===nowM);
        var card=el('<div style="border:1px solid '+(_isCurM?'#4f8ef7':'#2b3a5c')+';border-radius:12px;margin-bottom:8px;overflow:hidden;'+(_isPastM?'opacity:.5;':'')+'"></div>');
        var head=el('<div style="padding:10px 12px;cursor:pointer;background:'+(_isCurM?'#11203a':(_isPastM?'#0c1018':'#0e1830'))+';scroll-margin-top:38px;'+(_isCurM?'border-left:3px solid #4f8ef7;':'')+'"></div>');
        var top=el('<div style="display:flex;justify-content:space-between;align-items:center;"></div>');
        top.appendChild(el('<span style="font-weight:700;">'+MN[mi]+'</span>'));
        var arr=el('<span class="hint" style="font-size:12px;">'+summary+' ▸</span>');
        top.appendChild(arr); head.appendChild(top);
        head.appendChild(el('<div class="hint" style="font-size:11px;margin-top:2px;opacity:.75;">'+(hol>0?svL(hol):'bez svátků')+'</div>'));
        var body=el('<div style="padding:4px 12px 8px;display:none;"></div>');
        var lastW=null;
        days.forEach(function(d){
          if(d.iso_week!==lastW){ lastW=d.iso_week; body.appendChild(el('<div class="hint" style="font-size:10px;margin:6px 0 1px;opacity:.65;">Týden '+d.iso_week+'</div>')); }
          var h=effH(d), tp=effT(d);
          var col=(tp==="work")?"#34d399":(tp==="holiday"?"#fbbf24":(tp==="exception"?"#e6a93a":(tp==="exoff"?"#e6a93a":"#5b6b88")));
          var tag;
          if(tp==="exception"){ var ic=(d.exc_scope==='osobní'?'👤':(d.exc_scope==='skupina'?'👥':'🏢')); tag=ic+' '+nf(h)+' h'; }
          else if(tp==="exoff"){ var ic2=(d.exc_scope==='osobní'?'👤 osobní':(d.exc_scope==='skupina'?'👥 skupinové':'🏢 celofiremní')); tag=ic2+' volno'; }
          else if(tp==="work"){ tag=(d.start?('od '+d.start+' · '):'')+nf(h)+" h"; }
          else if(tp==="holiday"){ tag="svátek"; }
          else { tag=(d.day_type==="weekend"?"víkend":"volno"); }
          var _dPast=(d.date<_todayIso), _dToday=(d.date===_todayIso);
          var _rs="display:flex;justify-content:space-between;padding:3px 0;font-size:13px;"+(_dToday?"background:rgba(79,142,247,.14);border-radius:6px;padding:4px 6px;margin:2px -6px;":"")+(_dPast?"opacity:.4;":"");
          body.appendChild(el('<div style="'+_rs+'"><span'+(_dToday?' style="font-weight:700;"':'')+'>'+(_dToday?'▶ ':'')+d.weekday+' '+czd(d.date)+'</span><span style="color:'+col+';font-weight:600;">'+tag+'</span></div>'));
        });
        var entry={body:body, arr:arr, summary:summary, m:m};
        head.addEventListener("click",function(){ var willOpen=(body.style.display==="none"); closeAll(); if(willOpen){ body.style.display="block"; arr.innerHTML=summary+' ▾'; setTimeout(function(){ try{ head.scrollIntoView({behavior:'smooth',block:'start'}); }catch(e){} },10); } });
        entries.push(entry);
        card.appendChild(head); card.appendChild(body); box.appendChild(card);
      });
      var cur=entries.filter(function(e){return e.m===nowM;})[0]||entries[0];
      if(cur){ cur.body.style.display="block"; cur.arr.innerHTML=cur.summary+' ▾'; }
    }
    function renderGroupPlan(){
      left.innerHTML='<div class="hint">Načítám skupiny…</div>';
      api("GET","/api/v1/erp/app/plan/exception-targets","").then(function(t){
        left.innerHTML='';
        var groups=(t&&t.ok&&t.groups)||[];
        if(!groups.length){ left.appendChild(el('<div class="hint">Nelze načíst skupiny (jen rodiče/HR).</div>')); return; }
        var bar=el('<div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;"></div>');
        bar.appendChild(el('<span class="hint" style="flex:none;">👥 Skupina:</span>'));
        var sel=el('<select style="flex:1;box-sizing:border-box;padding:9px;border-radius:9px;border:1px solid #2b3a5c;background:#0a1226;color:#e8eefc;font-weight:700;">'+groups.map(function(g){return '<option value="'+g.id+'">'+esc(g.name)+'</option>';}).join('')+'</select>');
        bar.appendChild(sel); left.appendChild(bar);
        var box=el('<div></div>'); left.appendChild(box);
        function load(){
          var gid=sel.value;
          box.innerHTML='<div class="hint">Načítám…</div>';
          api("GET","/api/v1/erp/app/plan/group?group_id="+encodeURIComponent(gid),"").then(function(j){
            box.innerHTML='';
            if(!j||!j.ok){ box.appendChild(el('<div class="hint">'+esc((j&&j.error)||"Nelze načíst")+'</div>')); return; }
            var yr=(j.plan[0]&&j.plan[0].date||"").slice(0,4);
            renderMonths(box, j, true, 'group', '👥 '+(j.group_name||'')+' '+yr);
          });
        }
        sel.addEventListener("change",load); load();
      });
    }
    function renderDay(){
      left.innerHTML='';
      var t=new Date(); var st={d:t.getFullYear()+"-"+("0"+(t.getMonth()+1)).slice(-2)+"-"+("0"+t.getDate()).slice(-2)};
      var bar=el('<div style="display:flex;align-items:center;gap:6px;margin-bottom:8px;"></div>');
      var prev=el('<button class="ghost" style="padding:6px 10px;flex:none;">◀</button>');
      var din=el('<input type="date" value="'+st.d+'" style="flex:1;box-sizing:border-box;padding:8px;border-radius:9px;border:1px solid #2b3a5c;background:#0a1226;color:#e8eefc;">');
      var next=el('<button class="ghost" style="padding:6px 10px;flex:none;">▶</button>');
      bar.appendChild(prev); bar.appendChild(din); bar.appendChild(next); left.appendChild(bar);
      var regen=el('<button class="ghost full" style="margin-bottom:8px;border-color:#2a6b5a;color:#7fe0c8;">↻ Přegenerovat plán (dnes → +120 dní)</button>');
      regen.addEventListener("click",function(){ if(!confirm("Vygenerovat složený plán pro všechny na 120 dní dopředu?")) return; regen.disabled=true; var ot=regen.textContent; regen.textContent="Generuji…"; api("POST","/api/v1/erp/app/plan/generate-effective",{}).then(function(r){ regen.disabled=false; regen.textContent=ot; if(r&&r.ok){ alert("Hotovo: "+r.rows+" řádků, "+r.people+" lidí, do "+(r.do||"?")); load(); } else alert("Chyba: "+((r&&r.error)||"?")); }); });
      left.appendChild(regen);
      var box=el('<div></div>'); left.appendChild(box);
      function czdW(iso){ var p=(iso||"").split("-"); if(p.length!==3) return iso; var dd=new Date(iso); var wn=["Ne","Po","Út","St","Čt","Pá","So"][dd.getDay()]; return wn+" "+p[2]+"."+p[1]+"."; }
      function shift(n){ var dd=new Date(st.d); dd.setDate(dd.getDate()+n); st.d=dd.getFullYear()+"-"+("0"+(dd.getMonth()+1)).slice(-2)+"-"+("0"+dd.getDate()).slice(-2); din.value=st.d; load(); }
      prev.addEventListener("click",function(){ shift(-1); });
      next.addEventListener("click",function(){ shift(1); });
      din.addEventListener("change",function(){ st.d=din.value; load(); });
      function load(){
        box.innerHTML='<div class="hint">Načítám…</div>';
        api("GET","/api/v1/erp/app/plan/day?date="+encodeURIComponent(st.d),"").then(function(j){
          box.innerHTML='';
          if(!j||!j.ok){ box.appendChild(el('<div class="hint">'+esc((j&&j.error)||"Nelze načíst")+'</div>')); return; }
          box.appendChild(el('<div style="margin-bottom:8px;"><b>'+czdW(st.d)+'</b> <span class="hint">· čekáme '+j.total_people+' lidí · '+nf(j.total_hours)+' h</span></div>'));
          if(!j.generated){ box.appendChild(el('<div class="hint" style="line-height:1.6;">Pro tento den není plán vygenerovaný.<br>Klikni nahoře <b>↻ Přegenerovat plán</b>.</div>')); return; }
          j.groups.forEach(function(g){
            var card=el('<div style="border:1px solid #2b3a5c;border-radius:12px;margin-bottom:8px;overflow:hidden;"></div>');
            card.appendChild(el('<div style="display:flex;justify-content:space-between;padding:8px 12px;background:#0e1830;font-weight:700;"><span>'+esc(g.group_name)+'</span><span class="hint">'+g.count+' lidí · '+nf(g.sum_hours)+' h</span></div>'));
            var body=el('<div style="padding:4px 12px 8px;"></div>');
            g.people.forEach(function(p){
              var work=(p.hours>0);
              var col=work?"#34d399":"#5b6b88";
              var sic=p.scope_src==='osobni'?' 👤':(p.scope_src==='skupina'?' 👥':(p.scope_src==='firma'?' 🏢':''));
              var rt=work?((p.start?(p.start+' · '):'')+nf(p.hours)+' h'+sic):(p.day_type==='holiday'?'svátek':(p.day_type==='weekend'?'víkend':'volno'));
              body.appendChild(el('<div style="display:flex;justify-content:space-between;padding:3px 0;font-size:13px;"><span>'+esc(p.name)+'</span><span style="color:'+col+';font-weight:600;">'+rt+'</span></div>'));
            });
            card.appendChild(body); box.appendChild(card);
          });
          box.appendChild(el('<div style="text-align:right;font-weight:700;margin-top:6px;border-top:1px solid #2b3a5c;padding-top:8px;">Celkem: '+j.total_people+' lidí · '+nf(j.total_hours)+' h</div>'));
        });
      }
      load();
    }
    function renderUvazek(){
      left.innerHTML='<div class="hint">Načítám…</div>';
      api("GET","/api/v1/erp/app/plan/my-uvazek","").then(function(j){
        left.innerHTML='';
        if(!j||!j.ok){ left.appendChild(el('<div class="hint">'+esc((j&&j.error)||"Nelze načíst")+'</div>')); return; }
        left.appendChild(el('<div style="margin-bottom:8px;"><b>📐 Můj úvazek</b> <span class="hint">· '+(j.can_edit?'lze upravit':'jen k náhledu')+'</span></div>'));
        var iS="box-sizing:border-box;padding:10px;border-radius:9px;border:1px solid #2b3a5c;background:#0a1226;color:#e8eefc;";
        left.appendChild(el('<label class="hint" style="display:block;margin:2px 0;">Týdenní úvazek (h)</label>'));
        var uin=el('<input type="number" min="1" max="80" step="0.5" value="'+j.uvazek+'" '+(j.can_edit?'':'disabled')+' style="width:100%;'+iS+'margin-bottom:10px;">');
        left.appendChild(uin);
        left.appendChild(el('<div class="hint" style="margin-bottom:2px;">Týdenní vzorec (které dny a kolik hodin)</div>'));
        var dayEls=[];
        j.days.forEach(function(d){
          var row=el('<div style="border-bottom:1px solid #1b2742;padding:8px 2px;"></div>');
          var top=el('<div style="display:flex;align-items:center;gap:8px;"></div>');
          var cb=el('<input type="checkbox" '+(d.works?'checked':'')+' '+(j.can_edit?'':'disabled')+' style="width:18px;height:18px;flex:none;">');
          top.appendChild(cb);
          top.appendChild(el('<div style="flex:1;">'+d.label+'</div>'));
          var hin=el('<input type="number" min="0" max="24" step="0.5" value="'+d.hours+'" '+(j.can_edit?'':'disabled')+' style="width:64px;'+iS+'text-align:right;padding:8px 6px;">');
          top.appendChild(hin); top.appendChild(el('<span class="hint" style="flex:none;">h</span>'));
          row.appendChild(top);
          var sub=el('<div style="display:flex;align-items:center;gap:8px;margin-top:6px;padding-left:26px;"></div>');
          sub.appendChild(el('<span class="hint" style="flex:none;">příchod od</span>'));
          var tin=el('<input type="time" value="'+(d.start||"")+'" '+(j.can_edit?'':'disabled')+' style="flex:1;'+iS+'padding:8px 6px;">');
          sub.appendChild(tin);
          row.appendChild(sub);
          dayEls.push({weekday:d.weekday, cb:cb, hin:hin, tin:tin});
          var sync=function(){ var on=cb.checked; sub.style.display=on?'flex':'none'; if(j.can_edit){ hin.disabled=!on; tin.disabled=!on; if(!on){ hin.value="0"; tin.value=""; } else if(parseFloat(hin.value)===0){ hin.value=String(j.per_day||8); } } };
          cb.addEventListener("change",sync); sync();
          left.appendChild(row);
        });
        if(j.can_edit){
          var rb=el('<button class="ghost full" style="margin-top:10px;">↻ Rozpočítat úvazek do zaškrtnutých dnů</button>');
          rb.addEventListener("click",function(){ var uvz=parseFloat(uin.value)||0; var wc=dayEls.filter(function(x){return x.cb.checked;}).length||1; var pd=Math.round((uvz/wc)*100)/100; dayEls.forEach(function(x){ x.hin.value=x.cb.checked?pd:0; }); });
          left.appendChild(rb);
          var sb=el('<button class="green full" style="margin-top:8px;">Uložit úvazek</button>');
          var sst=el('<div class="hint" style="margin-top:6px;"></div>');
          sb.addEventListener("click",function(){
            var uvz=parseFloat(uin.value)||0;
            var days=dayEls.map(function(x){ return {weekday:x.weekday, works:x.cb.checked, hours:parseFloat(x.hin.value)||0, start:(x.tin.value||"")}; });
            sb.disabled=true; sst.textContent="Ukládám…";
            api("POST","/api/v1/erp/app/plan/my-uvazek/save",{uvazek:uvz, days:days}).then(function(r){
              sb.disabled=false; sst.textContent=(r&&r.ok)?"✅ Uloženo — 👤 Můj plán se přepočítá":("✗ "+((r&&r.error)||"chyba"));
            });
          });
          left.appendChild(sb); left.appendChild(sst);
        }
      });
    }
    // Marti 14.6.: „Moje podmínky" — RO, celoobrazovkový hezký přehled (pravá lišta se schová).
    function renderPodminky(){
      function hhmm(h){ h=Math.max(0,Math.round((h||0)*60)); return Math.floor(h/60)+":"+("0"+(h%60)).slice(-2); }
      if(right)right.style.display='none';
      function exitPod(){ if(right)right.style.display=AP?'none':'flex'; window._planAnyOpen=null; renderPlan(false,'mydefault'); }
      window._planAnyOpen=function(){ exitPod(); return true; };
      left.innerHTML='<div class="hint">Načítám…</div>';
      api("GET","/api/v1/erp/app/plan/my-uvazek","").then(function(j){
        left.innerHTML='';
        var bk=el('<button id="podBack" class="ghost full" style="margin-bottom:10px;">‹ Zpět</button>'); bk.addEventListener("click",exitPod); left.appendChild(bk);
        if(!j||!j.ok){ left.appendChild(el('<div class="hint">'+esc((j&&j.error)||"Nelze načíst")+'</div>')); return; }
        left.appendChild(el('<div style="margin-bottom:10px;"><b style="font-size:17px;">📋 Moje podmínky</b></div>'));
        var card=el('<div style="border:1px solid #2b3a5c;border-radius:12px;margin-bottom:10px;overflow:hidden;"></div>');
        card.appendChild(el('<div style="padding:11px 12px;background:#0e1830;display:flex;justify-content:space-between;align-items:center;"><span style="font-weight:700;">Týdenní úvazek</span><b style="font-size:16px;color:#cfe0ff;">'+(j.uvazek||"?")+' h</b></div>'));
        var body=el('<div style="padding:4px 10px 8px;"></div>');
        (j.days||[]).forEach(function(d){
          var work=d.works && d.hours>0;
          var rs="display:flex;justify-content:space-between;align-items:center;padding:7px 4px;font-size:14px;border-bottom:1px solid rgba(255,255,255,.05);";
          var rightCell;
          if(work){ rightCell='<span style="display:inline-flex;align-items:baseline;gap:10px;"><span style="color:#8fb4e8;font-size:12px;min-width:56px;text-align:right;">'+(d.start?'od '+d.start:'')+'</span><span style="color:#34d399;font-weight:700;min-width:46px;text-align:right;">'+hhmm(d.hours)+'</span></span>'; }
          else { rightCell='<span style="color:#5b6b88;font-weight:600;">volno</span>'; }
          body.appendChild(el('<div style="'+rs+'"><span>'+esc(d.label||"")+'</span>'+rightCell+'</div>'));
        });
        card.appendChild(body); left.appendChild(card);
        // Samostatná sekce: další sjednané podmínky (staff_cond, resolved) — pod základními.
        var ch=el('<div style="border:1px solid #2b3a5c;border-radius:12px;margin-bottom:10px;overflow:hidden;"></div>');
        ch.appendChild(el('<div style="padding:11px 12px;background:#0e1830;font-weight:700;">Sjednané podmínky</div>'));
        var cb=el('<div style="padding:4px 10px 8px;"></div>');
        cb.appendChild(el('<div class="hint" style="padding:6px 2px;">Načítám…</div>'));
        ch.appendChild(cb); left.appendChild(ch);
        api("GET","/api/v1/erp/app/my-conditions","").then(function(c){
          cb.innerHTML='';
          var items=((c&&c.ok&&c.podminky)||[]).filter(function(p){ return p.code!=='uvazek_h_tyden'; });
          if(!items.length){ cb.appendChild(el('<div class="hint" style="padding:6px 2px;">Žádné další sjednané podmínky.</div>')); return; }
          var srcMap={user:'osobní',group:'skupina',system:'firma'};
          items.forEach(function(p){
            var rs="display:flex;justify-content:space-between;align-items:center;gap:10px;padding:7px 4px;font-size:14px;border-bottom:1px solid rgba(255,255,255,.05);";
            cb.appendChild(el('<div style="'+rs+'"><span style="flex:1;min-width:0;">'+esc(p.label)+'</span><span style="display:inline-flex;align-items:baseline;gap:8px;flex:none;"><b style="color:#cfe0ff;">'+esc(String(p.value))+(p.unit?(' '+esc(p.unit)):'')+'</b><span class="hint" style="font-size:11px;">'+(srcMap[p.src]||p.src||'')+'</span></span></div>'));
          });
        }).catch(function(){ cb.innerHTML='<div class="hint" style="padding:6px 2px;">Nepodařilo se načíst.</div>'; });
        left.appendChild(el('<div class="hint" style="line-height:1.5;padding:2px 4px;">Tvé sjednané podmínky (úvazek, rozvrh a další). Jen k náhledu — změnu řeší nadřízený / HR.</div>'));
      });
    }
    function renderExc(mode){
      mode=mode||'firma';
      left.innerHTML='';
      var hd=el('<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;"></div>');
      hd.appendChild(el('<b>'+(mode==='scope'?'👥 Skupiny výjimky':'🏢 Firemní výjimky')+'</b>'));
      var addB=el('<button class="ghost" style="padding:6px 12px;border-color:#3a7a4c;color:#7fe0a0;font-weight:700;">+ Přidat</button>');
      addB.addEventListener("click",function(){ excDialog(null, mode); });
      hd.appendChild(addB); left.appendChild(hd);
      left.appendChild(el('<div class="hint" style="line-height:1.6;margin-bottom:8px;">'+(mode==='scope'?'Volno / zkrácený den / přesčas jen pro <b>skupinu</b> (např. Výroba — omezení při nedostatku práce nebo nařízené přesčasy). Přebíjí firemní výjimku. Edituje jen vedení / personalistika.':'Firemní den pro <b>celou firmu</b>. <b>0 h</b> = volno, jinak počet odpracovaných hodin (i pracovní víkend).')+' Plán (vrstva 1) zůstává nedotčený.</div>'));
      var box=el('<div></div>'); left.appendChild(box);
      box.innerHTML='<div class="hint">Načítám…</div>';
      Promise.all([api("GET","/api/v1/erp/app/plan/exceptions",""),api("GET","/api/v1/erp/app/plan/scope-exceptions","")]).then(function(res){
        var jc=res[0], js=res[1]; box.innerHTML='';
        if(jc&&jc.ok===false&&jc.error){ box.appendChild(el('<div class="hint">'+esc(jc.error)+'</div>')); return; }
        var items=[];
        if(mode!=='scope' && jc&&jc.ok&&jc.exceptions){ jc.exceptions.forEach(function(e){ items.push({kind:'firma',date:e.date,hours:e.hours,reason:e.reason,scope_name:'Celá firma',icon:'🏢'}); }); }
        if(mode==='scope' && js&&js.ok&&js.items){ js.items.filter(function(e){ return e.scope_type==='group'; }).forEach(function(e){ items.push({kind:'scope',id:e.id,scope_type:e.scope_type,scope_id:e.scope_id,date:e.date,hours:e.hours,reason:e.reason,scope_name:e.scope_name,icon:'👥'}); }); }
        if(!items.length){ box.appendChild(el('<div class="hint">Zatím žádné výjimky.</div>')); return; }
        items.sort(function(a,b){ return a.date<b.date?-1:(a.date>b.date?1:0); });
        items.forEach(function(e){
          var row=el('<div style="display:flex;align-items:center;gap:8px;border-bottom:1px solid #1b2742;padding:9px 4px;"></div>');
          var lbl=(e.hours===0?"volno":(nf(e.hours)+" h"));
          row.appendChild(el('<div style="flex:1;"><b>'+czd2(e.date)+'</b> · <span style="color:#e6a93a;font-weight:600;">'+lbl+'</span> <span class="hint">'+e.icon+' '+esc(e.scope_name)+'</span>'+(e.reason?('<br><span class="hint">'+esc(e.reason)+'</span>'):'')+'</div>'));
          var edit=el('<button class="ghost" style="padding:6px 12px;border-color:#3a5a8c;color:#9cf;">Upravit</button>');
          edit.addEventListener("click",function(){ excDialog(e, mode); });
          row.appendChild(edit); box.appendChild(row);
        });
      });
    }
    function excDialog(ex, mode){
      var isEdit=!!ex;
      var _reMode=isEdit?(ex.kind==='firma'?'firma':'scope'):(mode||'firma');  // po uložení/smazání se vrať do stejné sekce
      var t=new Date(); var today=t.getFullYear()+"-"+("0"+(t.getMonth()+1)).slice(-2)+"-"+("0"+t.getDate()).slice(-2);
      var inS="width:100%;box-sizing:border-box;padding:10px;border-radius:9px;border:1px solid #2b3a5c;background:#0a1226;color:#e8eefc;";
      var ov=el('<div style="position:fixed;inset:0;z-index:300;background:rgba(2,6,14,.72);display:flex;align-items:center;justify-content:center;padding:20px;"></div>');
      var bx=el('<div style="background:#0e1830;border:1px solid #2b3a5c;border-radius:14px;padding:16px;width:100%;max-width:340px;"></div>');
      bx.appendChild(el('<div style="font-weight:700;margin-bottom:10px;">'+(isEdit?'Upravit výjimku':'Nová výjimka')+'</div>'));
      var scopeType=isEdit?(ex.kind==='firma'?'firma':ex.scope_type):(mode==='scope'?'group':'firma');
      var targets=null, tgtSel=null;
      var scopeBox=el('<div style="margin-bottom:6px;"></div>'); bx.appendChild(scopeBox);
      var tgtBox=el('<div></div>'); bx.appendChild(tgtBox);
      function buildTgt(){
        tgtBox.innerHTML=''; tgtSel=null;
        if(isEdit||scopeType==='firma') return;
        var arr=scopeType==='group'?((targets&&targets.groups)||[]):((targets&&targets.people)||[]);
        var opts=arr.map(function(o){ var id=(scopeType==='group'?o.id:o.user_id); return '<option value="'+id+'">'+esc(o.name)+'</option>'; }).join('');
        tgtBox.appendChild(el('<label class="hint" style="display:block;margin:4px 0 2px;">'+(scopeType==='group'?'Skupina':'Osoba')+'</label>'));
        tgtSel=el('<select style="'+inS+'">'+opts+'</select>'); tgtBox.appendChild(tgtSel);
      }
      function ensureTargets(cb){ if(targets){ cb(); return; } api("GET","/api/v1/erp/app/plan/exception-targets","").then(function(j){ targets=(j&&j.ok)?j:{groups:[],people:[]}; cb(); }); }
      if(isEdit){
        scopeBox.appendChild(el('<div class="hint">Rozsah: <b>'+(ex.kind==='firma'?'Celá firma':((ex.scope_type==='group'?'Skupina — ':'Jednotlivec — ')+esc(ex.scope_name)))+'</b></div>'));
      } else if(mode==='scope'){
        scopeType='group';
        scopeBox.appendChild(el('<div class="hint">Rozsah: <b>Skupina</b></div>'));
        ensureTargets(buildTgt);
      } else {
        scopeBox.appendChild(el('<div class="hint">Rozsah: <b>Celá firma</b></div>'));
      }
      bx.appendChild(el('<label class="hint" style="display:block;margin:6px 0 2px;">Datum</label>'));
      var dI=el('<input type="date" value="'+(isEdit?ex.date:today)+'" '+(isEdit?'disabled':'')+' style="'+inS+(isEdit?'opacity:.6;':'')+'">'); bx.appendChild(dI);
      bx.appendChild(el('<label class="hint" style="display:block;margin:8px 0 2px;">Hodiny (0 = volno · jinak počet odpracovaných hodin, i pracovní víkend)</label>'));
      var hI=el('<input type="number" min="0" max="12" step="0.5" value="'+(isEdit?ex.hours:0)+'" style="'+inS+'">'); bx.appendChild(hI);
      var rI=el('<input type="text" placeholder="Důvod (volitelné)" style="'+inS+'margin-top:8px;">'); bx.appendChild(rI);
      if(isEdit) rI.value=ex.reason||"";
      var bs=el('<div style="display:flex;gap:8px;margin-top:12px;"></div>');
      var cancel=el('<button class="ghost" style="flex:1;">Zavřít</button>');
      var save=el('<button class="green" style="flex:1;">Uložit</button>');
      cancel.addEventListener("click",function(){ ov.remove(); });
      save.addEventListener("click",function(){
        var hrs=parseFloat(hI.value)||0, reason=rI.value; save.disabled=true;
        var done=function(r){ if(r&&r.ok){ ov.remove(); renderExc(_reMode); } else { save.disabled=false; alert("Chyba: "+((r&&r.error)||"?")); } };
        if(isEdit){
          if(ex.kind==='firma') api("POST","/api/v1/erp/app/plan/exceptions",{date:ex.date,hours:hrs,reason:reason}).then(done);
          else api("POST","/api/v1/erp/app/plan/scope-exceptions",{scope_type:ex.scope_type,scope_id:ex.scope_id,date:ex.date,hours:hrs,reason:reason}).then(done);
        } else if(scopeType==='firma'){
          api("POST","/api/v1/erp/app/plan/exceptions",{date:dI.value,hours:hrs,reason:reason}).then(done);
        } else {
          if(!tgtSel||!tgtSel.value){ save.disabled=false; alert("Vyber "+(scopeType==='group'?'skupinu':'osobu')+"."); return; }
          api("POST","/api/v1/erp/app/plan/scope-exceptions",{scope_type:scopeType,scope_id:parseInt(tgtSel.value,10),date:dI.value,hours:hrs,reason:reason}).then(done);
        }
      });
      bs.appendChild(cancel); bs.appendChild(save); bx.appendChild(bs);
      if(isEdit){
        var del=el('<button class="ghost full" style="margin-top:8px;color:#f87171;border-color:#5a2b2b;">🗑 Smazat výjimku</button>');
        del.addEventListener("click",function(){
          if(!confirm("Smazat výjimku "+czd2(ex.date)+"?")) return; del.disabled=true;
          var done=function(r){ if(r&&r.ok){ ov.remove(); renderExc(_reMode); } else { del.disabled=false; alert("Chyba: "+((r&&r.error)||"?")); } };
          if(ex.kind==='firma') api("POST","/api/v1/erp/app/plan/exceptions/delete",{date:ex.date}).then(done);
          else api("POST","/api/v1/erp/app/plan/scope-exceptions/delete",{id:ex.id}).then(done);
        });
        bx.appendChild(del);
      }
      ov.appendChild(bx); document.body.appendChild(ov);
      ov.addEventListener("click",function(ev){ if(ev.target===ov) ov.remove(); });
    }
    // Marti 14.6.: vstupní pohled z regionu docházky (Můj úvazek / Můj plán).
    if(AP){ renderPlan(false,'mydefault'); }
    else if(WEEKONLY){ window._planInit=null; renderPlan(false,'mydefault'); }
    else if(window._planInit==="uvazek"){ window._planInit=null; renderUvazek(); }
    else if(window._planInit==="myplan"){ window._planInit=null; renderPlan(false,'mydefault'); try{ setTimeout(function(){ if(right&&bMy) right.scrollTop=Math.max(0, bMy.offsetTop-4); },80); }catch(e){} }
    else renderPlan();
  }
  function plan_vyjimky(){
    app.innerHTML=topbar("🏢 Firemní výjimky", true);
    function nf(v){ return (Math.round((v||0)*100)/100).toString().replace('.',','); }
    function czd(iso){ var p=(iso||"").split("-"); return p.length===3?(p[2]+"."+p[1]+"."+p[0]):iso; }
    app.appendChild(el('<div class="hint" style="line-height:1.6;margin-bottom:10px;">Globální firemní volno / zkrácený den na konkrétní datum. <b>0 h</b> = celé volno, <b>1–8 h</b> = zkrácený den. Nepřepisuje plán — skládá se s ním.</div>'));
    var t=new Date(); var today=t.getFullYear()+"-"+("0"+(t.getMonth()+1)).slice(-2)+"-"+("0"+t.getDate()).slice(-2);
    var inS="width:100%;box-sizing:border-box;padding:9px;border-radius:9px;border:1px solid #2b3a5c;background:#0a1226;color:#e8eefc;";
    var f=el('<div style="border:1px solid #2b3a5c;border-radius:12px;padding:12px;margin-bottom:14px;"></div>');
    f.innerHTML='<div style="font-weight:700;margin-bottom:6px;">Nová výjimka</div>'
      +'<label class="hint" style="display:block;margin:4px 0 2px;">Datum</label><input id="exD" type="date" value="'+today+'" style="'+inS+'">'
      +'<label class="hint" style="display:block;margin:6px 0 2px;">Hodiny (0 = volno, 1–8 zkráceno)</label><input id="exH" type="number" min="0" max="8" step="0.5" value="0" style="'+inS+'">'
      +'<input id="exR" type="text" placeholder="Důvod (např. celozávodní dovolená)" style="'+inS+'margin-top:8px;">';
    var sb=el('<button class="green full" style="margin-top:10px;">Uložit výjimku</button>');
    var sst=el('<div class="hint" style="margin-top:6px;"></div>');
    sb.addEventListener("click",function(){
      sb.disabled=true; sst.textContent="Ukládám…";
      api("POST","/api/v1/erp/app/plan/exceptions",{date:f.querySelector('#exD').value, hours:parseFloat(f.querySelector('#exH').value)||0, reason:f.querySelector('#exR').value}).then(function(r){
        sb.disabled=false; sst.textContent=(r&&r.ok)?"✅ Uloženo":("✗ "+((r&&r.error)||"chyba"));
        if(r&&r.ok){ f.querySelector('#exR').value=""; load(); }
      });
    });
    f.appendChild(sb); f.appendChild(sst); app.appendChild(f);
    var list=el('<div></div>'); app.appendChild(list);
    function load(){
      list.innerHTML='<div class="hint">Načítám…</div>';
      api("GET","/api/v1/erp/app/plan/exceptions","").then(function(j){
        list.innerHTML="";
        if(!j||!j.ok){ list.appendChild(el('<div class="hint">'+esc((j&&j.error)||"Nelze načíst")+'</div>')); return; }
        if(!j.exceptions.length){ list.appendChild(el('<div class="hint">Zatím žádné výjimky.</div>')); return; }
        list.appendChild(el('<div style="font-weight:700;margin-bottom:6px;">Zadané výjimky</div>'));
        j.exceptions.forEach(function(e){
          var row=el('<div style="display:flex;align-items:center;gap:8px;border-bottom:1px solid #1b2742;padding:9px 4px;"></div>');
          var lbl=(e.hours===0?"volno":(nf(e.hours)+" h"));
          row.appendChild(el('<div style="flex:1;"><b>'+czd(e.date)+'</b> · <span style="color:#e6a93a;font-weight:600;">'+lbl+'</span>'+(e.reason?('<br><span class="hint">'+esc(e.reason)+'</span>'):'')+'</div>'));
          var del=el('<button class="ghost" style="padding:6px 10px;color:#f87171;border-color:#5a2b2b;">Smazat</button>');
          del.addEventListener("click",function(){ if(!confirm("Smazat výjimku "+czd(e.date)+"?")) return; api("POST","/api/v1/erp/app/plan/exceptions/delete",{date:e.date}).then(function(r){ if(r&&r.ok) load(); else alert("Chyba: "+((r&&r.error)||"?")); }); });
          row.appendChild(del); list.appendChild(row);
        });
      });
    }
    load();
  }
  function master_cinnosti(){
    app.innerHTML=topbar("🛠 Master číselník", true);
    var K=window._cinKind||"standard";
    var tg2=el('<div style="display:flex;gap:6px;margin:2px 0 10px;"></div>');
    [["standard","🧾 Běžné zakázky"],["rezie","🧰 Režie"]].forEach(function(t){
      var b=el('<button style="flex:1;padding:9px 4px;border-radius:11px;font-size:13px;font-weight:600;border:1px solid '+(K===t[0]?"#4f8ef7":"var(--bord)")+';background:'+(K===t[0]?"rgba(79,142,247,.14)":"rgba(255,255,255,.03)")+';color:'+(K===t[0]?"var(--tx)":"var(--mut)")+';">'+t[1]+'</button>');
      b.addEventListener("click",function(){ window._cinKind=t[0]; master_cinnosti(); });
      tg2.appendChild(b);
    });
    app.appendChild(tg2);
    app.appendChild(el('<div class="hint" style="line-height:1.6;margin-bottom:10px;">'+(K==="rezie"?"Seznam <b>režijních</b> činností (zakázka Režie).":"Výchozí seznam činností (pro běžné zakázky).")+' Přidej, přejmenuj, změň pořadí, skryj. Pracovníci si z něj dělají vlastní seznam.</div>'));
    var addb=el('<button class="green full" style="margin-bottom:10px;">+ Přidat činnost</button>');
    addb.addEventListener("click",function(){ var n=prompt("Název nové činnosti:"); if(!n||!n.trim())return; api("POST","/api/v1/erp/app/vyroba/cinnost-master/save",{name:n.trim(),kind:K}).then(function(r){ if(r&&r.ok) load(); else alert("Chyba: "+((r&&r.error)||"?")); }); });
    app.appendChild(addb);
    var box=el('<div></div>'); app.appendChild(box);
    app.appendChild(el('<div style="height:120px;"></div>'));
    var _all=[];
    function saveOrder(){ api("POST","/api/v1/erp/app/vyroba/cinnost-master/order",{order:_all.map(function(c){return c.id;})}).then(function(){}); }
    function render(){
      box.innerHTML='';
      _all.forEach(function(c,idx){
        var row=el('<div style="display:flex;align-items:center;gap:6px;border-bottom:1px solid #1b2742;padding:8px 4px;'+(c.active?'':'opacity:.5;')+'"></div>');
        var up=el('<button class="ghost" style="padding:4px 9px;flex:none;" '+(idx===0?'disabled':'')+'>▲</button>');
        var dn=el('<button class="ghost" style="padding:4px 9px;flex:none;" '+(idx===_all.length-1?'disabled':'')+'>▼</button>');
        up.addEventListener("click",function(){ if(idx===0)return; var t=_all[idx-1]; _all[idx-1]=_all[idx]; _all[idx]=t; render(); saveOrder(); });
        dn.addEventListener("click",function(){ if(idx===_all.length-1)return; var t=_all[idx+1]; _all[idx+1]=_all[idx]; _all[idx]=t; render(); saveOrder(); });
        row.appendChild(up); row.appendChild(dn);
        var ib=el('<button class="ghost" style="padding:4px 8px;flex:none;font-size:18px;line-height:1;" title="Změnit ikonu">'+(c.icon||"🔧")+'</button>');
        ib.addEventListener("click",function(){ var ic=prompt("Ikona (emoji) pro „"+c.name+"\":", c.icon||""); if(ic===null)return; ic=(ic||"").trim(); if(!ic||ic===c.icon)return; api("POST","/api/v1/erp/app/vyroba/cinnost-master/save",{id:c.id,icon:ic}).then(function(r){ if(r&&r.ok) load(); else alert("Chyba"); }); });
        row.appendChild(ib);
        var nm=el('<div style="flex:1;font-weight:600;cursor:pointer;">'+esc(c.name)+(c.active?'':' <span class="hint">(skryto)</span>')+'</div>');
        nm.addEventListener("click",function(){ var n=prompt("Název činnosti:",c.name); if(!n||!n.trim()||n.trim()===c.name)return; api("POST","/api/v1/erp/app/vyroba/cinnost-master/save",{id:c.id,name:n.trim()}).then(function(r){ if(r&&r.ok) load(); else alert("Chyba"); }); });
        row.appendChild(nm);
        var tg=el('<button class="ghost" style="padding:6px 10px;flex:none;">'+(c.active?'🚫':'👁')+'</button>');
        tg.addEventListener("click",function(){ api("POST","/api/v1/erp/app/vyroba/cinnost-master/save",{id:c.id,active:!c.active}).then(function(r){ if(r&&r.ok) load(); else alert("Chyba"); }); });
        row.appendChild(tg); box.appendChild(row);
      });
    }
    function load(){ box.innerHTML='<div class="hint">Načítám…</div>'; api("GET","/api/v1/erp/app/vyroba/cinnost-master?kind="+K,"").then(function(j){ box.innerHTML=''; if(!j||!j.ok){ box.appendChild(el('<div class="hint">'+esc((j&&j.error)||"Jen pro vedoucí/HR.")+'</div>')); return; } _all=j.cinnosti||[]; render(); }); }
    load();
  }
  function moje_cinnosti(){
    app.innerHTML=topbar("🧰 Moje činnosti", true);
    var K=window._cinKind||"standard";
    var tg3=el('<div style="display:flex;gap:6px;margin:2px 0 10px;"></div>');
    [["standard","🧾 Běžné zakázky"],["rezie","🧰 Režie"]].forEach(function(t){
      var b=el('<button style="flex:1;padding:9px 4px;border-radius:11px;font-size:13px;font-weight:600;border:1px solid '+(K===t[0]?"#4f8ef7":"var(--bord)")+';background:'+(K===t[0]?"rgba(79,142,247,.14)":"rgba(255,255,255,.03)")+';color:'+(K===t[0]?"var(--tx)":"var(--mut)")+';">'+t[1]+'</button>');
      b.addEventListener("click",function(){ window._cinKind=t[0]; moje_cinnosti(); });
      tg3.appendChild(b);
    });
    app.appendChild(tg3);
    // Marti 14.6.: vybrané činnosti složené jako ikony rovnou nahoře (náhled plochy).
    var _topGrid=el('<div class="appgrid" style="margin-bottom:12px;"></div>'); app.appendChild(_topGrid);
    app.appendChild(el('<div class="hint" style="line-height:1.6;margin-bottom:10px;">Vyber, které činnosti chceš mít ve svém seznamu a v jakém pořadí. Výchozí = všechny. ▲▼ pořadí · ✕ odebrat · + přidat zpět.</div>'));
    var mb=el('<button class="ghost full" style="margin-top:16px;border-color:#6b4a2a;color:#e6b97a;">🛠 Master číselník (správa)</button>');
    mb.addEventListener("click",function(){ go("master_cinnosti"); });
    var box=el('<div></div>'); app.appendChild(box);
    app.appendChild(mb);
    app.appendChild(el('<div style="height:120px;"></div>'));
    var _mine=[];
    function saveOrder(){ api("POST","/api/v1/erp/app/vyroba/my-cinnosti/order",{order:_mine.map(function(c){return c.id;})}).then(function(){}); }
    function renderMine(ml){
      ml.innerHTML='';
      if(!_mine.length){ ml.appendChild(el('<div class="hint">Prázdný seznam — přidej činnosti níže.</div>')); return; }
      _mine.forEach(function(c,idx){
        var row=el('<div style="display:flex;align-items:center;gap:6px;border-bottom:1px solid #1b2742;padding:8px 4px;"></div>');
        var up=el('<button class="ghost" style="padding:4px 9px;flex:none;" '+(idx===0?'disabled':'')+'>▲</button>');
        var dn=el('<button class="ghost" style="padding:4px 9px;flex:none;" '+(idx===_mine.length-1?'disabled':'')+'>▼</button>');
        up.addEventListener("click",function(){ if(idx===0)return; var t=_mine[idx-1]; _mine[idx-1]=_mine[idx]; _mine[idx]=t; renderMine(ml); saveOrder(); });
        dn.addEventListener("click",function(){ if(idx===_mine.length-1)return; var t=_mine[idx+1]; _mine[idx+1]=_mine[idx]; _mine[idx]=t; renderMine(ml); saveOrder(); });
        row.appendChild(up); row.appendChild(dn);
        row.appendChild(el('<div style="flex:1;font-weight:600;"><span style="margin-right:6px;">'+(c.icon||"🔧")+'</span>'+esc(c.name)+'</div>'));
        var rm=el('<button class="ghost" style="padding:6px 10px;flex:none;color:#f87171;border-color:#5a2b2b;">✕</button>');
        rm.addEventListener("click",function(){ api("POST","/api/v1/erp/app/vyroba/my-cinnosti/toggle",{cinnost_id:c.id,in_list:false}).then(function(r){ if(r&&r.ok) load(); else alert("Chyba: "+((r&&r.error)||"?")); }); });
        row.appendChild(rm); ml.appendChild(row);
      });
    }
    function load(){
      box.innerHTML='<div class="hint">Načítám…</div>';
      api("GET","/api/v1/erp/app/vyroba/my-cinnosti?kind="+K,"").then(function(j){
        box.innerHTML='';
        if(!j||!j.ok){ box.appendChild(el('<div class="hint">Nelze načíst.</div>')); return; }
        _mine=(j.cinnosti||[]).filter(function(c){return !c.hidden;});
        var avail=(j.cinnosti||[]).filter(function(c){return c.hidden;});
        // náhled plochy nahoře — vybrané činnosti jako ikony
        if(_topGrid){ _topGrid.innerHTML=''; _mine.forEach(function(c){ _topGrid.appendChild(appCell(c.icon||"🔧",c.name,0,function(){})); }); }
        box.appendChild(el('<div style="font-weight:700;margin-bottom:6px;">Můj seznam ('+_mine.length+')</div>'));
        var ml=el('<div></div>'); box.appendChild(ml); renderMine(ml);
        box.appendChild(el('<div style="font-weight:700;margin:14px 0 6px;">Přidat ze seznamu</div>'));
        if(!avail.length){ box.appendChild(el('<div class="hint">Máš všechny činnosti ve svém seznamu.</div>')); }
        avail.forEach(function(c){
          var row=el('<div style="display:flex;align-items:center;gap:8px;border-bottom:1px solid #1b2742;padding:9px 4px;"></div>');
          row.appendChild(el('<div style="flex:1;color:#8696b8;"><span style="margin-right:6px;">'+(c.icon||"🔧")+'</span>'+esc(c.name)+'</div>'));
          var add=el('<button class="ghost" style="padding:6px 12px;flex:none;border-color:#3a7a4c;color:#7fe0a0;">+ Přidat</button>');
          add.addEventListener("click",function(){ api("POST","/api/v1/erp/app/vyroba/my-cinnosti/toggle",{cinnost_id:c.id,in_list:true}).then(function(r){ if(r&&r.ok) load(); else alert("Chyba: "+((r&&r.error)||"?")); }); });
          row.appendChild(add); box.appendChild(row);
        });
      });
    }
    load();
  }
  // Marti 14.6.: „Na čem dělám" — osa přiřazení práce (zakázka+činnost) MIMO jádro docházky.
  function prace(){
    app.innerHTML=topbar("🧾 Na čem dělám", true);
    var box=el('<div style="padding-bottom:100px;"></div>'); app.appendChild(box);
    box.innerHTML='<div class="hint">Načítám…</div>';
    var _cur=null,_atwork=false,_mine=[];
    function _err(r){ alert((r&&(r.msg||r.error))||"Nepodařilo se."); }
    function setCin(ci){ api("POST","/api/v1/erp/app/work/set-cinnost",{cinnost_id:ci}).then(function(r){ if(r&&r.ok) load(); else _err(r); }); }
    function setZak(cislo,nazev){ api("POST","/api/v1/erp/app/work/set-zakazka",{project_ref:cislo,project_nazev:nazev}).then(function(r){ if(r&&r.ok) load(); else _err(r); }); }
    function setRezie(){ api("POST","/api/v1/erp/app/work/set-rezie",{}).then(function(r){ if(r&&r.ok) load(); else _err(r); }); }
    function zakPicker(host){
      host.innerHTML="";
      host.appendChild(el('<div class="hint" style="margin:4px 0 2px;">Najdi zakázku (číslo / název):</div>'));
      var si=el('<input placeholder="🔍 číslo nebo název…" autocomplete="off">');
      var res=el('<div style="margin-top:6px;"></div>'); var tmr=null;
      function zl(){ var q=(si.value||"").trim(); api("GET","/api/v1/erp/app/zakazky"+(q?("?q="+encodeURIComponent(q)):""),"").then(function(j){ res.innerHTML=""; ((j&&j.zakazky)||[]).slice(0,12).forEach(function(z){ var zb=el('<button class="ghost full" style="margin-top:6px;font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;text-align:left;">'+((z.typ==="REZIE")?"🧰 ":"🧾 ")+esc(z.cislo)+' — '+esc(z.nazev||"")+'</button>'); zb.addEventListener("click",function(){ setZak(z.cislo,z.nazev||""); }); res.appendChild(zb); }); }); }
      si.addEventListener("input",function(){ clearTimeout(tmr); tmr=setTimeout(zl,300); });
      host.appendChild(si); host.appendChild(res); zl();
    }
    function render(){
      box.innerHTML="";
      if(!_atwork){
        box.appendChild(el('<div style="background:var(--bg);border:1px solid var(--bord);border-radius:12px;padding:16px;text-align:center;line-height:1.6;"><div style="font-size:32px;">😴</div><div style="font-weight:700;margin-top:6px;">Nejsi přihlášený v práci</div><div class="hint" style="margin-top:4px;">Nejdřív se přihlas do práce v docházce — pak si tu vybereš zakázku a činnost.</div></div>'));
        return;
      }
      var a=_cur||{};
      var zText=a.is_rezie?"🧰 Režie (bez zakázky)":(a.project_ref?("🧾 "+esc(a.project_ref)+(a.project_nazev?(" — "+esc(a.project_nazev)):"")):"— žádná zakázka —");
      var cText=a.cinnost_name?("🔧 "+esc(a.cinnost_name)):"— žádná činnost —";
      var head=el('<div style="background:var(--bg);border:1px solid var(--green);border-radius:12px;padding:14px;margin-bottom:12px;"></div>');
      head.appendChild(el('<div class="hint" style="font-size:11px;letter-spacing:.5px;">PRÁVĚ DĚLÁM'+(a.since?(' · od '+esc(a.since)):'')+'</div>'));
      head.appendChild(el('<div style="font-size:16px;font-weight:700;margin-top:4px;">'+zText+'</div>'));
      head.appendChild(el('<div style="font-size:15px;margin-top:2px;color:#cdd8ea;">'+cText+'</div>'));
      box.appendChild(head);
      box.appendChild(el('<div style="font-weight:700;margin:6px 2px 6px;">Zakázka</div>'));
      var zwrap=el('<div></div>');
      var zbtn=el('<button class="green full" style="margin-bottom:6px;">🧾 Změnit zakázku</button>');
      zbtn.addEventListener("click",function(){ zakPicker(zwrap); });
      var rbtn=el('<button class="ghost full" style="margin-bottom:10px;border-color:#6b5a2a;color:#e6c86a;">🧰 Režie (bez zakázky)</button>');
      rbtn.addEventListener("click",setRezie);
      box.appendChild(zbtn); box.appendChild(rbtn); box.appendChild(zwrap);
      box.appendChild(el('<div style="font-weight:700;margin:6px 2px 6px;">Činnost</div>'));
      if(!_mine.length){ box.appendChild(el('<div class="hint" style="margin-bottom:10px;">Nemáš vybrané činnosti. Přidej si je v <b>🧰 Moje činnosti</b>.</div>')); }
      var cg=el('<div class="appgrid"></div>');
      _mine.forEach(function(c){ var on=(_cur&&_cur.cinnost_id===c.id); var cell=appCell("🔧",c.name,0,function(){ setCin(c.id); }); if(on){ cell.style.outline="2px solid var(--green)"; cell.style.borderColor="var(--green)"; } cg.appendChild(cell); });
      box.appendChild(cg);
      box.appendChild(el('<div style="font-weight:700;margin:14px 2px 6px;">Dnešní úseky</div>'));
      var tl=el('<div></div>'); box.appendChild(tl);
      api("GET","/api/v1/erp/app/work/today","").then(function(j){ tl.innerHTML=""; var segs=(j&&j.segments)||[]; if(!segs.length){ tl.innerHTML='<div class="hint">Zatím žádné úseky.</div>'; return; } segs.forEach(function(sg){ var z=sg.is_rezie?"Režie":(sg.project_ref?(esc(sg.project_ref)+(sg.project_nazev?(" — "+esc(sg.project_nazev)):"")):"—"); var c=sg.cinnost_name?(" · 🔧 "+esc(sg.cinnost_name)):""; tl.appendChild(el('<div style="border-bottom:1px solid #1b2742;padding:7px 2px;font-size:13px;"><span style="color:#8fb4e8;">'+esc(sg.od)+'–'+esc(sg.do_||"…")+'</span> · '+z+c+' <span class="hint">('+fmtHM(sg.hod)+')</span></div>')); }); });
    }
    function load(){
      box.innerHTML='<div class="hint">Načítám…</div>';
      Promise.all([
        api("GET","/api/v1/erp/app/work/current",""),
        api("GET","/api/v1/erp/app/vyroba/my-cinnosti","")
      ]).then(function(rs){
        var w=rs[0]||{},m=rs[1]||{};
        _atwork=!!w.at_work; _cur=w.alloc||null;
        _mine=((m&&m.cinnosti)||[]).filter(function(c){return !c.hidden;});
        render();
      }).catch(function(){ box.innerHTML='<div class="hint">Nelze načíst.</div>'; });
    }
    load();
  }
  // Marti 14.6.: sekce „Zakázky a činnosti" — pod nadpisem, nad „Potřebuji ti něco říct".
  // Předvýběr funguje vždy; ▶️ Makat zapne docházku z předvýběru; za běhu = změna úseku.
  window._buildWorkSwitch=function(host){
    var ws=el('<div style="margin:4px 0 0;padding:10px;border:1px solid #2a3a4d;border-radius:12px;background:rgba(127,200,224,.05);"></div>');
    var lbl=el('<div class="hint" style="font-size:11px;letter-spacing:.5px;margin-bottom:8px;">ZAKÁZKY A ČINNOSTI</div>'); ws.appendChild(lbl);
    var row=el('<div style="display:flex;gap:8px;"></div>'); ws.appendChild(row);
    var makWrap=el('<div></div>'); ws.appendChild(makWrap);
    host.appendChild(ws);
    function ensureCinPulseCss(){ if(document.getElementById("cinPulseCss"))return; var st=document.createElement("style"); st.id="cinPulseCss"; st.textContent="@keyframes cinpulse{0%,100%{box-shadow:0 0 0 0 rgba(245,158,11,.7);transform:scale(1)}50%{box-shadow:0 0 0 8px rgba(245,158,11,0);transform:scale(1.05)}} .cin-pulse{animation:cinpulse 1.05s ease-in-out infinite;border-color:#f59e0b!important;background:rgba(245,158,11,.14)!important;color:#f4c97a!important;}"; document.head.appendChild(st); }
    function tile(icon,top,sub,onclick,pulse){
      var t=el('<button class="ghost" style="flex:1;min-width:0;display:flex;flex-direction:column;align-items:center;gap:3px;padding:12px 8px;text-align:center;"></button>');
      t.appendChild(el('<div style="font-size:26px;line-height:1;">'+icon+'</div>'));
      t.appendChild(el('<div style="font-size:9.5px;letter-spacing:.5px;color:#8696b8;text-transform:uppercase;">'+esc(top)+'</div>'));
      t.appendChild(el('<div style="font-size:13px;font-weight:700;line-height:1.25;word-break:break-word;">'+esc(sub)+'</div>'));
      if(pulse){ ensureCinPulseCss(); t.classList.add("cin-pulse"); }
      t.addEventListener("click",onclick); return t;
    }
    api("GET","/api/v1/erp/app/work/state","").then(function(j){
      var aw=!!(j&&j.at_work);
      var src=(aw?(j&&j.working_alloc):(j&&j.pref))||(j&&j.pref)||{};
      var zIcon=src.is_rezie?"🧰":"🧾";
      var zSub=src.is_rezie?"Režie":(src.project_ref?(src.project_ref+(src.project_nazev?(" — "+src.project_nazev):"")):"Vyber zakázku");
      var cIcon=src.cinnost_name?(src.cinnost_icon||"🔧"):"🔧";
      var cSub=src.cinnost_name||"Vyber činnost";
      lbl.innerHTML=aw?'<span style="color:var(--green);font-weight:700;">🟢 MAKÁŠ — klikni a změň</span>':'ZAKÁZKY A ČINNOSTI — předvýběr, pak ▶️ Makat';
      row.innerHTML="";
      row.appendChild(tile(zIcon,"Zakázka",zSub,function(){ go("prace_zak"); }, !src.is_rezie && !src.project_ref));
      row.appendChild(tile(cIcon,"Činnost",cSub,function(){ go("prace_cin"); }, !src.cinnost_name));
      makWrap.innerHTML="";
      if(!aw){ var mb=el('<button class="green full" style="margin-top:8px;font-weight:700;">▶️ Makat</button>'); mb.addEventListener("click",function(){ if(window._praceStart) window._praceStart(); }); makWrap.appendChild(mb); }
    }).catch(function(){});
  };
  // Marti 14.6.: „Makat" — zapni docházku + zakázkový systém z předvýběru.
  window._praceStart=function(){
    api("POST","/api/v1/erp/app/attendance/checkin",{kind:"work",switch:true}).then(function(r){
      if(r&&r.need_confirm&&r.need_confirm.length){ alert("Nejdřív si prosím potvrď předchozí docházku (v sekci docházky)."); }
      if(typeof dochLoad==="function") dochLoad();
    }).catch(function(){});
  };
  // Picker zakázky — aktuální/předvybraná nahoře, ostatní (záloha) k výběru dole.
  function prace_zak(){
    app.innerHTML=topbar("🧾 Vyber zakázku", true);
    var box=el('<div style="padding-bottom:100px;"></div>'); app.appendChild(box);
    box.innerHTML='<div class="hint">Načítám…</div>';
    function pick(cislo,nazev){ api("POST","/api/v1/erp/app/work/set-zakazka",{project_ref:cislo,project_nazev:nazev}).then(function(r){ if(r&&r.ok) back(); else alert((r&&(r.msg||r.error))||"Nepodařilo se."); }); }
    function rezie(){ api("POST","/api/v1/erp/app/work/set-rezie",{}).then(function(r){ if(r&&r.ok) back(); else alert((r&&(r.msg||r.error))||"Nepodařilo se."); }); }
    api("GET","/api/v1/erp/app/work/state","").then(function(j){
      box.innerHTML="";
      var cur=((j&&j.at_work&&j.working_alloc)||(j&&j.pref))||{};
      var curTxt=cur.is_rezie?"🧰 Režie (bez zakázky)":(cur.project_ref?("🧾 "+esc(cur.project_ref)+(cur.project_nazev?(" — "+esc(cur.project_nazev)):"")):"— zatím nevybráno —");
      box.appendChild(el('<div style="background:var(--bg);border:1px solid var(--green);border-radius:12px;padding:12px;margin-bottom:10px;"><div class="hint" style="font-size:11px;letter-spacing:.5px;">AKTUÁLNÍ</div><div style="font-weight:700;font-size:15px;margin-top:3px;">'+curTxt+'</div></div>'));
      var rb=el('<button class="ghost full" style="margin-bottom:10px;border-color:#6b5a2a;color:#e6c86a;">🧰 Režie (bez zakázky)</button>'); rb.addEventListener("click",rezie); box.appendChild(rb);
      box.appendChild(el('<div style="font-weight:700;margin:4px 2px 6px;">V záloze — vyber jinou</div>'));
      var si=el('<input placeholder="🔍 číslo nebo název…" autocomplete="off">'); box.appendChild(si);
      var res=el('<div style="margin-top:6px;"></div>'); box.appendChild(res); var tmr=null;
      function zl(){ var q=(si.value||"").trim(); api("GET","/api/v1/erp/app/zakazky"+(q?("?q="+encodeURIComponent(q)):""),"").then(function(jz){ res.innerHTML=""; ((jz&&jz.zakazky)||[]).slice(0,20).forEach(function(z){ var zb=el('<button class="ghost full" style="margin-top:6px;font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;text-align:left;">'+((z.typ==="REZIE")?"🧰 ":"🧾 ")+esc(z.cislo)+' — '+esc(z.nazev||"")+'</button>'); zb.addEventListener("click",function(){ pick(z.cislo,z.nazev||""); }); res.appendChild(zb); }); }); }
      si.addEventListener("input",function(){ clearTimeout(tmr); tmr=setTimeout(zl,300); }); zl();
    });
  }
  // Picker činnosti — aktuální/předvybraná nahoře, dlaždice k výběru.
  function prace_cin(){
    app.innerHTML=topbar("🔧 Vyber činnost", true);
    var box=el('<div style="padding-bottom:100px;"></div>'); app.appendChild(box);
    box.innerHTML='<div class="hint">Načítám…</div>';
    function pick(ci){ api("POST","/api/v1/erp/app/work/set-cinnost",{cinnost_id:ci}).then(function(r){ if(r&&r.ok) back(); else alert((r&&(r.msg||r.error))||"Nepodařilo se."); }); }
    api("GET","/api/v1/erp/app/work/state","").then(function(st){
      st=st||{};
      var cur=((st.at_work&&st.working_alloc)||st.pref)||{};
      var rez=!!cur.is_rezie || (cur.kind==="overhead") || (cur.project_type==="REZIE")
        || (typeof _isRezieRef==="function" && _isRezieRef(cur.project_ref));
      window._cinKind=rez?"rezie":"standard";
      api("GET","/api/v1/erp/app/vyroba/my-cinnosti?kind="+(rez?"rezie":"standard"),"").then(function(m){
        box.innerHTML="";
        var mine=((m&&m.cinnosti)||[]).filter(function(c){return !c.hidden;});
        box.appendChild(el('<div style="background:var(--bg);border:1px solid '+(rez?"#e6c86a":"var(--green)")+';border-radius:12px;padding:12px;margin-bottom:10px;"><div class="hint" style="font-size:11px;letter-spacing:.5px;">'+(rez?"ČINNOST NA REŽII":"AKTUÁLNÍ ČINNOST")+'</div><div style="font-weight:700;font-size:15px;margin-top:3px;">'+(cur.cinnost_name?((cur.cinnost_icon||"🔧")+" "+esc(cur.cinnost_name)):"— zatím nevybráno —")+'</div></div>'));
        if(!mine.length){ box.appendChild(el('<div class="hint" style="margin-bottom:8px;">Nemáš vybrané '+(rez?"režijní ":"")+'činnosti — přidej je tlačítkem níže.</div>')); }
        var cg=el('<div class="appgrid"></div>');
        mine.forEach(function(c){ var on=(cur.cinnost_id===c.id); var cell=appCell(c.icon||"🔧",c.name,0,function(){ pick(c.id); }); if(on){ cell.style.outline="2px solid var(--green)"; cell.style.borderColor="var(--green)"; } cg.appendChild(cell); });
        box.appendChild(cg);
        var mb=el('<button class="ghost full" style="margin-top:12px;border-color:#6b4a2a;color:#e6b97a;">🧰 Upravit seznam '+(rez?"režijních ":"")+'činností</button>'); mb.addEventListener("click",function(){ go("moje_cinnosti"); }); box.appendChild(mb);
      });
    });
  }
  // Marti 15.6.: Web jako obrazovka UVNITŘ appky (iframe), ať hardwarové Zpět
  // vrátí do Aplikací a neukončuje celou appku.
  function webview(){
    app.innerHTML=topbar("🌐 Web ekosystému", true);
    app.appendChild(el('<iframe src="/web" style="display:block;width:100%;height:calc(100vh - 56px);border:0;background:var(--bg);"></iframe>'));
  }
  function web_stats(){
    app.innerHTML=topbar("📈 Návštěvnost webu", true);
    var box=el('<div style="padding-bottom:100px;"></div>'); app.appendChild(box); box.innerHTML='<div class="hint">Načítám…</div>';
    api("GET","/api/v1/erp/app/web-stats?days=30","").then(function(j){
      box.innerHTML='';
      if(!j||!j.ok){ box.appendChild(el('<div class="hint">'+esc((j&&j.error)||"Jen rodiče/HR.")+'</div>')); return; }
      function card(t,vis,ppl){ return '<div style="flex:1;min-width:70px;border:1px solid #2b3a5c;border-radius:12px;padding:10px 6px;text-align:center;"><div class="hint" style="font-size:11px;margin-bottom:2px;">'+t+'</div><div style="font-size:22px;font-weight:800;">'+vis+'</div><div class="hint" style="font-size:10px;">návštěv</div><div style="font-size:14px;font-weight:700;color:#7fc8e0;margin-top:4px;">'+ppl+'</div><div class="hint" style="font-size:10px;">lidí</div></div>'; }
      box.appendChild(el('<div class="hint" style="font-size:11px;margin-bottom:6px;">Návštěva = otevření stránky · Lidí = různé otisky (přibližně, nepřesné u mobilních sítí)</div>'));
      var kpi=el('<div style="display:flex;gap:6px;margin-bottom:12px;flex-wrap:wrap;"></div>'); kpi.innerHTML=card("Dnes",j.today,j.today_unique)+card("Včera",j.yday,j.yday_unique)+card("7 dní",j.d7,j.d7_unique)+card("30 dní",j.d30,j.d30_unique); box.appendChild(kpi);
      if(j.by_day&&j.by_day.length){
        var mx=Math.max.apply(null,j.by_day.map(function(d){return d.v;}))||1;
        box.appendChild(el('<div class="hint" style="margin-bottom:4px;">Návštěvy po dnech</div>'));
        var ch=el('<div style="display:flex;align-items:flex-end;gap:2px;height:90px;border-bottom:1px solid #2b3a5c;margin-bottom:12px;"></div>');
        j.by_day.forEach(function(d){ var h=Math.round(d.v/mx*84)+2; ch.appendChild(el('<div title="'+d.d+': '+d.v+' ('+d.u+' uniq)" style="flex:1;min-width:3px;height:'+h+'px;background:linear-gradient(180deg,#7fc8e0,#2a6b8a);border-radius:2px 2px 0 0;"></div>')); });
        box.appendChild(ch);
      }
      function sect(title,rows,key){ if(!rows||!rows.length)return; box.appendChild(el('<div style="font-weight:700;margin:10px 0 4px;">'+title+'</div>')); rows.forEach(function(r){ box.appendChild(el('<div style="display:flex;justify-content:space-between;gap:8px;border-bottom:1px solid #1b2742;padding:6px 2px;font-size:13px;"><span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">'+esc(String(r[key]||"—"))+'</span><span style="font-weight:700;color:#7fc8e0;flex:none;">'+r.v+'</span></div>')); }); }
      sect("Nejčtenější stránky",j.pages,"path");
      sect("Jazyky",j.langs,"lang");
      sect("Odkud přišli",j.refs,"ref");
    });
  }
  /* MIGRACE hub (Marti 18.6.2026): řídicí panel hybridní fáze — co kdy spustit
     + kdy naposledy běželo. Pro rodiče + Jirku. Nad ops frameworkem. */
  function migrace(){
    app.innerHTML=topbar("🔀 Migrace", true);
    app.appendChild(el('<div class="muted" style="margin:8px 6px;line-height:1.5">Hybridní fáze — starý a nový systém běží souběžně (červen → ~půlka července). Přehledně co kdy spustit a kdy to naposledy proběhlo.</div>'));
    var g=el('<div class="appgrid"></div>');
    g.appendChild(appCell("🗓️","Docházka",0,function(){go("migrace_dochazka");}));
    g.appendChild(appCell("💰","Mzdy",0,function(){go("migrace_mzdy");}));
    app.appendChild(g);
  }
  function migrace_dochazka(){ migraceDomain("dochazka","🗓️ Migrace — Docházka"); }
  function migrace_mzdy(){ migraceDomain("mzdy","💰 Migrace — Mzdy"); }
  function migraceDomain(domain,title){
    app.innerHTML=topbar(title, true);
    if(domain==="mzdy"){
      var pb=el('<button style="margin:8px 6px;background:linear-gradient(135deg,#5b8def,#7c5cff);color:#fff;border:0;border-radius:11px;padding:12px 16px;font-size:14px;font-weight:700;width:calc(100% - 12px)">📊 Přehled mzdových podkladů (osoba × měsíc)</button>');
      pb.onclick=function(){ openInApp("/payroll"); };
      app.appendChild(pb);
    }
    var wrap=el('<div id="migWrap" class="muted" style="padding:8px 6px">Načítám…</div>');
    app.appendChild(wrap);
    api("GET","/api/v1/erp/app/migrace/steps?domain="+domain,"").then(function(j){
      if(!j||!j.ok){ wrap.innerHTML=(j&&j.error==="forbidden")?"Tento přehled je pro rodiče a Jirku.":"Chyba načtení."; return; }
      wrap.innerHTML="";
      (j.steps||[]).forEach(function(st,i){
        var last=st.last;
        var col=last?(last.status==="done"?"#34d399":(last.status==="error"?"#ff8a8a":"#fbbf24")):"#9fb0c2";
        var lastHtml=last
          ?('<div style="font-size:12px;margin-top:6px;color:'+col+'">Naposledy: '+esc(last.ts||"")+' · '+esc(last.status||"")+(last.by?(' · '+esc(last.by)):"")+(last.result?('<br><span style="color:#9fb0c2">'+esc(last.result)+'</span>'):"")+'</div>')
          :'<div style="font-size:12px;margin-top:6px;color:#9fb0c2">Zatím nespuštěno.</div>';
        var card=el('<div style="margin:8px 6px;padding:12px;background:rgba(255,255,255,.03);border:1px solid var(--bord);border-radius:12px">'
          +'<div style="font-weight:700">'+(i+1)+'. '+esc(st.label)+'</div>'
          +'<div style="font-size:12.5px;color:#9fb0c2;margin-top:4px;line-height:1.45">'+esc(st.when)+'</div>'
          +lastHtml
          +'<div style="margin-top:10px"><button class="mig-run" data-k="'+esc(st.key)+'" style="background:#10b981;color:#04150e;border:0;border-radius:10px;padding:10px 16px;font-size:14px;font-weight:700">▶ Spustit</button>'
          +'<span class="mig-msg" style="margin-left:10px;font-size:13px"></span></div></div>');
        wrap.appendChild(card);
      });
      wrap.querySelectorAll(".mig-run").forEach(function(b){
        b.onclick=function(){
          var k=b.getAttribute("data-k"); var msg=b.parentElement.querySelector(".mig-msg");
          b.disabled=true; msg.style.color="#9fb0c2"; msg.textContent="Spouštím… (může chvíli trvat)";
          api("POST","/api/v1/erp/app/ops/run",{action_key:k}).then(function(r){
            if(r&&r.ok){ msg.style.color="#34d399"; msg.textContent="Hotovo. "+(r.result||""); setTimeout(function(){go(domain==="dochazka"?"migrace_dochazka":"migrace_mzdy");},1000); }
            else { msg.style.color="#ff8a8a"; msg.textContent="Chyba: "+((r&&(r.error||r.detail))||"?"); b.disabled=false; }
          }).catch(function(){ msg.style.color="#ff8a8a"; msg.textContent="Chyba spojení."; b.disabled=false; });
        };
      });
    });
  }
  // ── SW ZAKÁZKY — divize automatizace/PLC (Marti 19.6.2026, pro Zuzku) ──
  var _SW_STAVLBL={poptavka:"Poptávka",nabidka:"Nabídka",objednavka:"Objednávka",realizace:"Realizace",fakturovano:"Fakturováno",zaplaceno:"Zaplaceno"};
  var _SW_STAVCOL={poptavka:"#9fb0c2",nabidka:"#5b8def",objednavka:"#7c5cff",realizace:"#fbbf24",fakturovano:"#34d399",zaplaceno:"#10b981"};
  function swH(n){ try{ return (Math.round((+n||0)*10)/10).toLocaleString('cs-CZ')+" h"; }catch(e){ return (n||0)+" h"; } }
  function sw_zakazky(){
    app.innerHTML=topbar("🤖 SW zakázky — automatizace", true);
    app.appendChild(el('<div class="muted" style="margin:8px 6px;line-height:1.5">Přehled SW zakázek divize automatizace — zákazník, řešitel, hodiny, dílčí faktury, kolik zbývá odpracovat a zaplatit. Klikni na zakázku pro detail a faktury.</div>'));
    app.appendChild(el('<div id="swBox" style="margin:4px 6px"></div>'));
    if(window._swRes){ swLoad(); }
    else { api("GET","/api/v1/erp/app/sw/resitele","").then(function(j){ window._swRes=(j&&j.resitele)||[]; swLoad(); }); }
  }
  function swLoad(){
    var box=document.getElementById("swBox"); if(!box)return;
    box.innerHTML='<div class="hint" style="padding:12px">Načítám…</div>';
    api("GET","/api/v1/erp/app/sw/list","").then(function(j){
      if(!j||!j.ok){ box.innerHTML='<div class="hint" style="color:#ff8a8a;padding:10px">'+esc((j&&(j.error||j.detail))||"Chyba")+'</div>'; return; }
      window._swStavy=j.stavy||Object.keys(_SW_STAVLBL);
      var zk=j.zakazky||[];
      var f=window._swFilter||"";
      var zbH=0, zbZ=0;
      zk.forEach(function(z){ zbH+=(+z.zbyva_hodin||0); zbZ+=(+z.zbyva_zaplatit||0); });
      var h='<div style="display:flex;gap:8px;flex-wrap:wrap;margin:4px 0 8px">'
        +'<div style="flex:1;min-width:120px;background:rgba(255,255,255,.03);border:1px solid var(--bord);border-radius:10px;padding:8px"><div class="hint">Zakázek</div><div style="font-weight:800;font-size:17px">'+zk.length+'</div></div>'
        +'<div style="flex:1;min-width:120px;background:rgba(255,255,255,.03);border:1px solid var(--bord);border-radius:10px;padding:8px"><div class="hint">Zbývá odpracovat</div><div style="font-weight:800;font-size:17px;color:#fbbf24">'+swH(zbH)+'</div></div>'
        +'<div style="flex:1;min-width:120px;background:rgba(255,255,255,.03);border:1px solid var(--bord);border-radius:10px;padding:8px"><div class="hint">Zbývá zaplatit</div><div style="font-weight:800;font-size:15px;color:#34d399">'+prefKc(zbZ)+'</div></div>'
        +'</div>';
      h+='<input id="swSearch" placeholder="Hledat (číslo, zákazník, řešitel)…" value="'+esc(f)+'" style="margin:0 0 8px">';
      h+='<button id="swAdd" class="green full" style="margin:0 0 10px;width:100%">➕ Nová zakázka</button>';
      var fl=f.toLowerCase();
      var shown=zk.filter(function(z){ if(!fl)return true; return ((z.cislo_sw||"")+" "+(z.zakaznik||"")+" "+(z.resitel||"")+" "+(z.nazev||"")).toLowerCase().indexOf(fl)>=0; });
      shown.forEach(function(z){
        var col=_SW_STAVCOL[z.stav]||"#9fb0c2", lbl=_SW_STAVLBL[z.stav]||z.stav;
        h+='<div class="sw-card" data-id="'+z.id+'" style="margin:7px 0;padding:11px;background:rgba(255,255,255,.03);border:1px solid var(--bord);border-radius:12px;cursor:pointer">'
          +'<div style="display:flex;justify-content:space-between;gap:8px"><div style="font-weight:700"><span style="font-size:10.5px;color:#7c5cff;border:1px solid #7c5cff55;border-radius:6px;padding:0 5px;margin-right:5px">'+esc(z.typ||"SW")+'</span>'+esc(z.cislo_sw||"(bez čísla)")+' · '+esc(z.zakaznik||"")+'</div>'
          +'<span style="flex:none;font-size:11.5px;padding:2px 8px;border-radius:10px;background:'+col+'22;color:'+col+';border:1px solid '+col+'">'+esc(lbl)+'</span></div>'
          +'<div style="font-size:12.5px;color:#9fb0c2;margin-top:3px">'+esc(z.resitel||"—")+(z.nazev?(' · '+esc(z.nazev)):'')+'</div>'
          +'<div style="font-size:12.5px;margin-top:5px;display:flex;gap:12px;flex-wrap:wrap">'
          +'<span>obj. '+swH(z.objednano_hodin)+'</span><span style="color:#fbbf24">zbývá '+swH(z.zbyva_hodin)+'</span>'
          +'<span>'+prefKc(z.celkova_suma)+'</span><span style="color:#34d399">zbývá zaplatit '+prefKc(z.zbyva_zaplatit)+'</span></div></div>';
      });
      if(!shown.length) h+='<div class="hint" style="padding:10px">Žádná zakázka. Přidej první přes ➕.</div>';
      box.innerHTML=h;
      var si=document.getElementById("swSearch");
      si.addEventListener("input",function(){ window._swFilter=si.value; var p=si.selectionStart; swLoad(); setTimeout(function(){ var n=document.getElementById("swSearch"); if(n){n.focus(); try{n.setSelectionRange(p,p);}catch(e){}} },0); });
      document.getElementById("swAdd").addEventListener("click",function(){ swForm(null); });
      box.querySelectorAll(".sw-card").forEach(function(c){ c.addEventListener("click",function(){ swDetail(c.getAttribute("data-id")); }); });
    });
  }
  function _swSel(id,val){ var o='<option value="">— řešitel —</option>'; (window._swRes||[]).forEach(function(r){ o+='<option value="'+r.id+'"'+(String(r.id)===String(val)?' selected':'')+'>'+esc(r.jmeno||("#"+r.id))+'</option>'; }); return '<select id="'+id+'" style="margin:0">'+o+'</select>'; }
  function _swStavSel(id,val){ var o=''; (window._swStavy||Object.keys(_SW_STAVLBL)).forEach(function(s){ o+='<option value="'+s+'"'+(s===val?' selected':'')+'>'+(_SW_STAVLBL[s]||s)+'</option>'; }); return '<select id="'+id+'" style="margin:0">'+o+'</select>'; }
  function swForm(z){
    z=z||{};
    var ov=el('<div style="position:fixed;inset:0;z-index:300;background:rgba(4,10,18,.98);overflow:auto;padding:20px;display:flex;flex-direction:column;gap:8px"></div>');
    ov.appendChild(el('<div style="font-weight:800;font-size:18px">'+(z.id?'Upravit zakázku':'Nová SW zakázka')+' 🤖</div>'));
    function fld(lbl,inner){ var w=el('<label style="font-size:12px;color:#9fb0c2">'+lbl+'</label>'); w.appendChild(el('<div style="margin-top:2px">'+inner+'</div>')); return w; }
    function inp(id,val,ph,type){ return '<input id="'+id+'" '+(type?('type="'+type+'" '):'')+'placeholder="'+(ph||"")+'" value="'+esc(val==null?"":String(val))+'" style="margin:0">'; }
    ov.appendChild(fld("Typ zakázky", '<select id="swTyp" style="margin:0"><option value="SW"'+((z.typ||"SW")==="SW"?" selected":"")+'>SW (automatizace)</option><option value="VR"'+(z.typ==="VR"?" selected":"")+'>VR (výroba rozvaděčů)</option></select>'));
    ov.appendChild(fld("Číslo zakázky", inp("swCislo",z.cislo_sw,"SW8041 / VR…")));
    ov.appendChild(fld("Zákazník", inp("swZak",z.zakaznik,"Tesla / BMW…")));
    ov.appendChild(fld("PO zákazníka", inp("swPo",z.zakaznik_po,"5101270890")));
    ov.appendChild(fld("Název / popis", inp("swNazev",z.nazev,"")));
    ov.appendChild(fld("Řešitel", _swSel("swResitel",z.resitel_user_id)));
    ov.appendChild(fld("Objednáno hodin", inp("swObjH",z.objednano_hodin,"0","number")));
    ov.appendChild(fld("Hodinovka zákazník / SW", '<div style="display:flex;gap:8px">'+inp("swHodZak",z.hodinovka_zakaznik,"zákazník","number")+inp("swHodSw",z.hodinovka_sw,"sw","number")+'</div>'));
    ov.appendChild(fld("Celková suma (Kč)", inp("swSuma",z.celkova_suma,"0","number")));
    ov.appendChild(fld("Stav", _swStavSel("swStav",z.stav||"poptavka")));
    ov.appendChild(fld("Rok", inp("swRok",z.rok||2026,"2026","number")));
    ov.appendChild(fld("Poznámka", inp("swPozn",z.poznamka,"")));
    var st=el('<div class="hint" style="min-height:15px"></div>'); ov.appendChild(st);
    var save=el('<button class="green full" style="margin:0">Uložit</button>');
    var cl=el('<button class="ghost full" style="margin:0">Zavřít</button>');
    cl.addEventListener("click",function(){ ov.remove(); });
    function V(id){ var e=document.getElementById(id); return e?e.value:""; }
    save.addEventListener("click",function(){
      var body={id:z.id||null, typ:V("swTyp"), cislo_sw:V("swCislo"), zakaznik:V("swZak"), zakaznik_po:V("swPo"),
        nazev:V("swNazev"), resitel_user_id:V("swResitel"), objednano_hodin:V("swObjH"),
        hodinovka_zakaznik:V("swHodZak"), hodinovka_sw:V("swHodSw"), celkova_suma:V("swSuma"),
        stav:V("swStav"), rok:V("swRok"), poznamka:V("swPozn")};
      save.disabled=true; st.textContent="Ukládám…";
      api("POST","/api/v1/erp/app/sw/save",body).then(function(r){
        if(r&&r.ok){ ov.remove(); swLoad(); } else { save.disabled=false; st.textContent=((r&&(r.error||r.detail))||"Nepovedlo se."); }
      });
    });
    ov.appendChild(save); ov.appendChild(cl);
    app.appendChild(ov);
  }
  function swDetail(id){
    api("GET","/api/v1/erp/app/sw/detail?id="+id,"").then(function(j){
      if(!j||!j.ok){ try{_shotToast("Chyba detailu");}catch(e){} return; }
      var z=j.zakazka, fa=j.faktury||[];
      var ov=el('<div style="position:fixed;inset:0;z-index:300;background:rgba(4,10,18,.98);overflow:auto;padding:20px;display:flex;flex-direction:column;gap:8px"></div>');
      var col=_SW_STAVCOL[z.stav]||"#9fb0c2", lbl=_SW_STAVLBL[z.stav]||z.stav;
      ov.appendChild(el('<div style="display:flex;justify-content:space-between;gap:8px;align-items:center"><div style="font-weight:800;font-size:18px">'+esc(z.cislo_sw||"")+' · '+esc(z.zakaznik||"")+'</div><span style="flex:none;font-size:12px;padding:3px 9px;border-radius:10px;background:'+col+'22;color:'+col+';border:1px solid '+col+'">'+esc(lbl)+'</span></div>'));
      if(z.nazev) ov.appendChild(el('<div class="hint">'+esc(z.nazev)+'</div>'));
      var od=0,zp=0; fa.forEach(function(x){ od+=(+x.hodiny||0); if(x.zaplaceno) zp+=(+x.suma||0); });
      var oh=+z.objednano_hodin||0, cs=+z.celkova_suma||0;
      ov.appendChild(el('<div style="font-size:13px;margin-top:4px;line-height:1.7">Řešitel: <b>'+esc(z.resitel||"—")+'</b> · PO: '+esc(z.zakaznik_po||"—")
        +'<br>Hodiny: objednáno <b>'+swH(oh)+'</b> · odpracováno '+swH(od)+' · <span style="color:#fbbf24">zbývá '+swH(oh-od)+'</span>'
        +'<br>Suma: <b>'+prefKc(cs)+'</b> · zaplaceno '+prefKc(zp)+' · <span style="color:#34d399">zbývá '+prefKc(cs-zp)+'</span></div>'));
      var btns=el('<div style="display:flex;gap:7px;margin-top:8px"></div>');
      var bE=el('<button class="ghost" style="margin:0;padding:8px 12px">✏️ Upravit</button>');
      bE.addEventListener("click",function(){ ov.remove(); swForm(z); });
      var bD=el('<button class="ghost" style="margin:0;padding:8px 12px;color:#ff8a8a">🗑 Smazat</button>');
      bD.addEventListener("click",function(){ confirmDialog("Smazat zakázku",esc(z.cislo_sw||"")+" — opravdu?","🗑 Smazat",function(){ api("POST","/api/v1/erp/app/sw/delete",{id:z.id}).then(function(){ ov.remove(); swLoad(); }); }); });
      btns.appendChild(bE); btns.appendChild(bD); ov.appendChild(btns);
      ov.appendChild(el('<div style="font-weight:700;margin-top:12px">Faktury</div>'));
      var fl=el('<div></div>');
      fa.forEach(function(x){
        var row=el('<div style="display:flex;justify-content:space-between;gap:8px;border-bottom:1px solid #1b2742;padding:7px 2px;font-size:13px;cursor:pointer"><span>#'+(x.poradi||"")+' '+esc(x.cislo_faktury||"")+'<br><span class="hint">'+swH(x.hodiny)+' · '+(x.zaplaceno?('zaplaceno '+esc(x.zaplaceno)):'<span style="color:#fbbf24">nezaplaceno</span>')+'</span></span><b style="white-space:nowrap">'+prefKc(x.suma)+'</b></div>');
        row.addEventListener("click",function(){ swFaktForm(z.id,x,ov); }); fl.appendChild(row);
      });
      if(!fa.length) fl.appendChild(el('<div class="hint" style="padding:6px 2px">Zatím žádná faktura.</div>'));
      ov.appendChild(fl);
      var bF=el('<button class="green full" style="margin:8px 0 0">➕ Přidat fakturu</button>');
      bF.addEventListener("click",function(){ swFaktForm(z.id,null,ov); });
      ov.appendChild(bF);
      var cl=el('<button class="ghost full" style="margin:6px 0 0">Zavřít</button>'); cl.addEventListener("click",function(){ ov.remove(); });
      ov.appendChild(cl);
      app.appendChild(ov);
    });
  }
  function swFaktForm(zakId,x,parentOv){
    x=x||{};
    var ov=el('<div style="position:fixed;inset:0;z-index:320;background:rgba(4,10,18,.98);overflow:auto;padding:20px;display:flex;flex-direction:column;gap:8px"></div>');
    ov.appendChild(el('<div style="font-weight:800;font-size:17px">'+(x.id?'Upravit fakturu':'Nová faktura')+'</div>'));
    function inp(id,val,ph,type){ return '<input id="'+id+'" '+(type?('type="'+type+'" '):'')+'placeholder="'+(ph||"")+'" value="'+esc(val==null?"":String(val))+'" style="margin:0">'; }
    function fld(l,i){ var w=el('<label style="font-size:12px;color:#9fb0c2">'+l+'</label>'); w.appendChild(el('<div style="margin-top:2px">'+i+'</div>')); return w; }
    ov.appendChild(fld("Pořadí (1,2,3…)", inp("fkPor",x.poradi,"1","number")));
    ov.appendChild(fld("Hodiny", inp("fkHod",x.hodiny,"0","number")));
    ov.appendChild(fld("Číslo faktury", inp("fkCis",x.cislo_faktury,"626179")));
    ov.appendChild(fld("Suma (Kč)", inp("fkSum",x.suma,"0","number")));
    ov.appendChild(fld("Zaplaceno dne (prázdné = nezaplaceno)", inp("fkZap",x.zaplaceno,"DD.MM.RRRR")));
    var st=el('<div class="hint" style="min-height:15px"></div>'); ov.appendChild(st);
    var save=el('<button class="green full" style="margin:0">Uložit</button>');
    var del=x.id?el('<button class="ghost full" style="margin:0;color:#ff8a8a">🗑 Smazat fakturu</button>'):null;
    var cl=el('<button class="ghost full" style="margin:0">Zpět</button>');
    cl.addEventListener("click",function(){ ov.remove(); });
    function V(id){ var e=document.getElementById(id); return e?e.value:""; }
    function reopen(){ ov.remove(); if(parentOv)parentOv.remove(); swDetail(zakId); }
    save.addEventListener("click",function(){
      var body={id:x.id||null, zakazka_id:zakId, poradi:V("fkPor"), hodiny:V("fkHod"),
        cislo_faktury:V("fkCis"), suma:V("fkSum"), zaplaceno_at:V("fkZap")};
      save.disabled=true; st.textContent="Ukládám…";
      api("POST","/api/v1/erp/app/sw/faktura/save",body).then(function(r){ if(r&&r.ok){ reopen(); } else { save.disabled=false; st.textContent=((r&&(r.error||r.detail))||"Nepovedlo se."); } });
    });
    if(del) del.addEventListener("click",function(){ confirmDialog("Smazat fakturu","Opravdu smazat?","🗑 Smazat",function(){ api("POST","/api/v1/erp/app/sw/faktura/delete",{id:x.id}).then(reopen); }); });
    ov.appendChild(save); if(del)ov.appendChild(del); ov.appendChild(cl);
    app.appendChild(ov);
  }

  // ── DATOVÉ SCHRÁNKY / ISDS → eNeschopenka + OČR (Marti 19.6.2026) ─────
  function _isdsBanner(msg, kind){
    var COL={progress:["#1f6fd6","#2f86ef"], ok:["#15803d","#22c55e"], err:["#b91c1c","#ef4444"]};
    var c=COL[kind]||COL.progress;
    var bg=document.getElementById("isdsBannerBg");
    if(!bg){ bg=document.createElement("div"); bg.id="isdsBannerBg";
      bg.style.cssText="position:fixed;inset:0;z-index:1190;pointer-events:none;display:flex;align-items:center;justify-content:center;padding:24px;";
      document.body.appendChild(bg); }
    var t=document.getElementById("isdsBanner");
    if(!t){ t=document.createElement("div"); t.id="isdsBanner"; t.addEventListener("click",_isdsBannerHide); bg.appendChild(t); }
    t.style.cssText="pointer-events:auto;cursor:pointer;max-width:90vw;min-width:220px;text-align:center;color:#fff;font-size:23px;font-weight:800;line-height:1.35;padding:26px 28px;border-radius:18px;box-shadow:0 14px 44px rgba(0,0,0,.55);border:1px solid rgba(255,255,255,.25);background:linear-gradient(180deg,"+c[1]+","+c[0]+");";
    t.textContent=msg;
    bg.style.display="flex";
    if(_isdsBanner._t){ clearTimeout(_isdsBanner._t); _isdsBanner._t=null; }
    if(kind==="ok"||kind==="err"){ _isdsBanner._t=setTimeout(_isdsBannerHide, kind==="err"?5000:3500); }
  }
  function _isdsBannerHide(){ var bg=document.getElementById("isdsBannerBg"); if(bg)bg.style.display="none"; if(_isdsBanner._t){ clearTimeout(_isdsBanner._t); _isdsBanner._t=null; } }
  function buildAbsForm(box){
    var today=_locDate(0);
    var ist="width:100%;background:#0f1620;border:1px solid var(--bord);border-radius:8px;padding:11px;color:var(--tx);font-size:15px;margin-bottom:4px;";
    box.innerHTML='<label>Typ nepřítomnosti</label>'
      +'<select id="absType" style="'+ist+'"><option value="vacation">Dovolená</option>'
      +'<option value="homeoffice">🏠 Home office (hlášení dopředu)</option>'
      +'<option value="sick">Nemoc (PN)</option><option value="medical">Lékař</option>'
      +'<option value="family_care">OČR</option><option value="sickday">Sickday</option>'
      +'<option value="unpaid">Neplacené volno</option></select>'
      +'<label>Od</label><input type="date" id="absFrom" value="'+today+'" style="'+ist+'">'
      +'<label>Do (volitelně, jen pro celé dny)</label><input type="date" id="absTo" value="'+today+'" style="'+ist+'">'
      +'<label>Počet hodin (část dne — prázdné = celé dny po 8 h)</label><input type="number" step="0.5" min="0" id="absHours" placeholder="např. 1.5 (lékař)" style="'+ist+'">'
      +'<label>Poznámka (volitelné)</label><input id="absNote" placeholder="důvod…" style="'+ist+'">';
    var b=el('<button class="green full" style="margin-top:10px;">Odeslat ke schválení</button>');
    b.addEventListener("click",function(){
      var t=document.getElementById("absType").value, f=document.getElementById("absFrom").value,
          to=document.getElementById("absTo").value, n=document.getElementById("absNote").value,
          hv=(document.getElementById("absHours").value||"").trim();
      if(!f){ return; }
      var payload = hv ? {type_code:t,date_from:f,mode:"hours",hours:parseFloat(hv),note:n}
                       : {type_code:t,date_from:f,date_to:to,mode:"days",note:n};
      b.disabled=true; b.textContent="Odesílám…";
      api("POST","/api/v1/erp/app/attendance/absence",payload).then(function(j){
        if(j&&j.ok){ box.style.display="none"; box.innerHTML=""; dochListLoad(); alert("Nahlášeno ✓ ("+(j.created||0)+" pracovních dní)"); }
        else { b.disabled=false; b.textContent="Odeslat ke schválení"; alert("Nepodařilo se: "+((j&&j.error)||"")); }
      }).catch(function(){ b.disabled=false; b.textContent="Odeslat ke schválení"; });
    });
    box.appendChild(b);
  }
  function skupNazev(gid){ for(var i=0;i<_skup.length;i++){ if(_skup[i].id===gid) return (_skup[i].icon||"👥")+" "+_skup[i].name; } return "#"+gid; }

  function isds(){
    app.innerHTML=topbar("📨 Datové schránky (ISDS)", true);
    app.appendChild(el('<div class="muted" style="margin:8px 6px;line-height:1.5">Neschopenky a OČR z datových schránek firem — taženo automaticky. Jeden tenant může mít víc datovek (EC, ES, INTERSOFT…). Heslo se ukládá šifrovaně.</div>'));
    app.appendChild(el('<div id="isdsBox" style="margin:4px 6px"></div>'));
    isdsLoad();
  }
  function isdsLoad(){
    var box=document.getElementById("isdsBox"); if(!box)return;
    box.innerHTML='<div class="hint" style="padding:12px">Načítám…</div>';
    api("GET","/api/v1/erp/app/isds/accounts","").then(function(j){
      if(!j||!j.ok){ box.innerHTML='<div class="hint" style="color:#ff8a8a;padding:10px">'+esc((j&&(j.error||j.detail))||"Chyba")+'</div>'; return; }
      var h='';
      if(!j.vault_ready){ h+='<div style="margin:6px 0;padding:10px;border-radius:10px;background:rgba(251,191,36,.12);border:1px solid #fbbf24;color:#fde68a;font-size:13px">⚠️ Trezor není aktivní (STRATEGIE_VAULT_KEY). Hesla teď nepůjde uložit — doplň klíč do AppEnvironmentExtra a restartuj API.</div>'; }
      (j.accounts||[]).forEach(function(a){
        h+='<div style="margin:8px 0;padding:12px;background:rgba(255,255,255,.03);border:1px solid var(--bord);border-radius:12px">'
          +'<div style="font-weight:700">'+esc(a.company_label)+(a.active?'':' <span style="color:#ff8a8a;font-size:12px">(neaktivní)</span>')+'</div>'
          +'<div style="font-size:12.5px;color:#9fb0c2;margin-top:3px">📮 '+esc(a.box_id||"—")+' · login: '+esc(a.login_name||"—")+' · '+(a.has_pwd?'🔑 heslo uloženo':'<span style="color:#ff8a8a">bez hesla</span>')+(a.cssz_vs?(' · VS '+esc(a.cssz_vs)):'')+' · tenant '+esc(String(a.tenant_id))+'</div>'
          +(a.last_sync?('<div style="font-size:12px;color:#9fb0c2;margin-top:3px">Sync: '+esc(a.last_sync)+' · '+esc(a.last_sync_note||"")+'</div>'):'')
          +'<div style="margin-top:9px;display:flex;gap:7px;flex-wrap:wrap">'
          +'<button class="ghost isds-edit" data-id="'+a.id+'" style="margin:0;padding:7px 12px;font-size:13px">✏️ Upravit</button>'
          +'<button class="green isds-sync" data-id="'+a.id+'" style="margin:0;padding:7px 12px;font-size:13px">📥 Synchronizovat</button>'
          +'<button class="ghost isds-hist" data-id="'+a.id+'" style="margin:0;padding:7px 12px;font-size:13px">📜 Historie (rok)</button>'
          +'<button class="ghost isds-del" data-id="'+a.id+'" data-nm="'+esc(a.company_label)+'" style="margin:0;padding:7px 12px;font-size:13px;color:#ff8a8a">🗑</button>'
          +'</div></div>';
      });
      h+='<button id="isdsAdd" class="green full" style="margin:10px 0;width:100%">➕ Přidat datovku</button>';
      h+='<div id="isdsMsgs" style="margin-top:10px"></div>';
      box.innerHTML=h;
      box.querySelector("#isdsAdd").addEventListener("click",function(){ isdsForm(null); });
      box.querySelectorAll(".isds-edit").forEach(function(b){ b.addEventListener("click",function(){ var a=(j.accounts||[]).filter(function(x){return String(x.id)===b.getAttribute("data-id");})[0]; isdsForm(a); }); });
      box.querySelectorAll(".isds-sync").forEach(function(b){ b.addEventListener("click",function(){ isdsSync(b.getAttribute("data-id")); }); });
      box.querySelectorAll(".isds-hist").forEach(function(b){ b.addEventListener("click",function(){ isdsSync(b.getAttribute("data-id"),365); }); });
      box.querySelectorAll(".isds-del").forEach(function(b){ b.addEventListener("click",function(){ confirmDialog("Smazat datovku","Smazat "+b.getAttribute("data-nm")+" včetně stažených zpráv?","🗑 Smazat",function(){ api("POST","/api/v1/erp/app/isds/account/delete",{id:parseInt(b.getAttribute("data-id"),10)}).then(isdsLoad); }); }); });
      isdsLoadMsgs((j.accounts||[]).map(function(a){return a.company_label;}));
    });
  }
  function isdsLoadMsgs(accLabels){
    var box=document.getElementById("isdsMsgs"); if(!box)return;
    accLabels=accLabels||[];
    api("GET","/api/v1/erp/app/isds/messages","").then(function(j){
      var msgs=(j&&j.ok&&j.messages)?j.messages:[];
      if(!msgs.length && !accLabels.length){ box.innerHTML='<div class="hint" style="padding:6px 2px">Zatím žádné stažené zprávy.</div>'; return; }
      var open=(window._isdsOpen=window._isdsOpen||{});         // pamatuje rozbalení firem (do zavření appky)
      var PAL=["#3b82f6","#22c55e","#f59e0b","#a855f7","#ec4899","#14b8a6","#ef4444"];
      function pad(n){ return (n<10?"0":"")+n; }
      function plnew(n){ return n===1?"1 nová":((n>=2&&n<=4)?(n+" nové"):(n+" nových")); }
      function typeInfo(m){
        var t=(m.msg_type||"").toLowerCase(), su=(m.subject||"").toLowerCase();
        if(t.indexOf("neschop")>=0) return {ic:"🤒",tag:"ČSSZ neschopenka"};
        if(t==="ocr"||su.indexOf("očr")>=0||su.indexOf("ošetř")>=0) return {ic:"👶",tag:"ČSSZ OČR"};
        if(su.indexOf("daňov")>=0||su.indexOf("doklad")>=0) return {ic:"🧾",tag:"Daňový doklad"};
        if(su.indexOf("podán")>=0||su.indexOf("protokol")>=0||su.indexOf("hlášení")>=0) return {ic:"📄",tag:"ePodání"};
        if(su.indexOf("registr")>=0) return {ic:"🏛️",tag:"Registr"};
        return {ic:"✉️",tag:""};
      }
      var now=new Date(), today=new Date(now.getFullYear(),now.getMonth(),now.getDate());
      function parseDelivered(s){
        s=(s||"").trim(); if(!s) return null;
        var sp=s.split(" "), dp=(sp[0]||"").split("."), tp=sp[1]||"";
        if(dp.length<3) return null;
        var dd=+dp[0], mm=+dp[1], yy=+dp[2];
        if(!yy) return null;
        var dt=new Date(yy,mm-1,dd);
        var diff=Math.round((today-dt)/86400000);
        var lbl=(diff===0)?"Dnes":((diff===1)?"Včera":(pad(dd)+". "+pad(mm)+". "+yy));
        return {time:tp.slice(0,5), dayLabel:lbl};
      }
      // seskupení po firmách — tlačítko vznikne pro KAŽDOU datovku (i s 0 zprávami),
      // v pořadí podle seznamu firem; případné ostatní se přidají na konec.
      var byco={};
      function _grp(key){ var g=byco[key]; if(!g){ g={key:key,msgs:[],nnew:0}; byco[key]=g; } return g; }
      accLabels.forEach(function(lbl){ _grp(lbl||"(bez názvu)"); });
      msgs.forEach(function(m){
        var g=_grp(m.company_label||"(bez názvu)");
        g.msgs.push(m);
        if(((m.status||"").toLowerCase())==="new") g.nnew++;
      });
      var groups=[], seen={};
      accLabels.forEach(function(lbl){ var k=lbl||"(bez názvu)"; if(!seen[k]){ seen[k]=1; groups.push(byco[k]); } });
      Object.keys(byco).forEach(function(k){ if(!seen[k]){ seen[k]=1; groups.push(byco[k]); } });
      var h='<div style="font-weight:700;margin:10px 2px 6px;font-size:15px">Stažené zprávy</div>';
      groups.forEach(function(g,gi){
        var col=PAL[gi%PAL.length];
        var isOpen=(g.key in open)?open[g.key]:false;        // výchozí: vše sbalené — ukážou se jen tlačítka firem
        h+='<div style="margin:9px 0;border:1px solid '+col+';border-radius:14px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.25)">';
        h+='<div class="isds-co-h" data-k="'+esc(g.key)+'" style="display:flex;align-items:center;gap:10px;cursor:pointer;padding:15px 14px;background:linear-gradient(180deg,rgba(255,255,255,.06),rgba(255,255,255,.02))">'
          +'<span style="width:12px;height:12px;border-radius:50%;background:'+col+';flex:0 0 auto"></span>'
          +'<span style="flex:1;font-weight:800;font-size:16px;color:'+col+'">'+esc(g.key)+'</span>'
          +(g.nnew>0?('<span style="background:'+col+';color:#04121e;font-weight:800;font-size:12px;padding:3px 9px;border-radius:11px;flex:0 0 auto">'+plnew(g.nnew)+'</span>'):'')
          +'<span style="color:#9fb0c2;font-size:12px;margin-left:4px;flex:0 0 auto">'+g.msgs.length+' celkem</span>'
          +'<span class="isds-co-arr" style="font-size:15px;color:#9fb0c2;width:16px;text-align:center;flex:0 0 auto">'+(isOpen?"▾":"▸")+'</span>'
          +'</div>';
        h+='<div class="isds-co-b" style="display:'+(isOpen?"block":"none")+'">';
        if(!g.msgs.length){ h+='<div class="hint" style="padding:9px 12px;color:#7e90a4;font-size:12px">Zatím žádné stažené zprávy.</div>'; }
        var lastDay="";
        g.msgs.forEach(function(m){
          var pd=parseDelivered(m.delivered), dayLabel=pd?pd.dayLabel:"Bez data";
          if(dayLabel!==lastDay){
            h+='<div style="padding:7px 12px 3px;color:#7e90a4;font-size:11px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;background:rgba(255,255,255,.015)">'+esc(dayLabel)+'</div>';
            lastDay=dayLabel;
          }
          var ti=typeInfo(m), unread=((m.status||"").toLowerCase())==="new";
          h+='<div style="display:flex;gap:9px;align-items:flex-start;padding:8px 12px;border-top:1px solid #141f33">'
            +'<span style="font-size:15px;line-height:1.25;flex:0 0 auto">'+ti.ic+'</span>'
            +'<span style="flex:1;min-width:0">'
              +'<span style="font-size:13px;'+(unread?"font-weight:700;color:#eaf2ff":"color:#c4d2e2")+';display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'+esc(m.subject||"(bez předmětu)")+'</span>'
              +'<span style="color:#8aa0b6;font-size:11px">'+(ti.tag?esc(ti.tag):esc(m.sender||""))+'</span>'
            +'</span>'
            +'<span style="text-align:right;flex:0 0 auto;white-space:nowrap;padding-top:1px">'
              +'<span style="color:#9fb0c2;font-size:11.5px">'+(pd?esc(pd.time):"—")+'</span>'
              +(unread?('<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:'+col+';margin-left:6px;vertical-align:middle"></span>'):'')
            +'</span>'
          +'</div>';
        });
        h+='</div></div>';
      });
      box.innerHTML=h;
      box.querySelectorAll(".isds-co-h").forEach(function(hd){
        hd.addEventListener("click",function(){
          var k=hd.getAttribute("data-k"), body=hd.nextElementSibling;
          var nowOpen=!(body&&body.style.display!=="none");
          if(body) body.style.display=nowOpen?"block":"none";
          var arr=hd.querySelector(".isds-co-arr"); if(arr) arr.textContent=nowOpen?"▾":"▸";
          if(k) window._isdsOpen[k]=nowOpen;
        });
      });
    });
  }
  function isdsForm(a){
    a=a||{};
    var ov=el('<div style="position:fixed;inset:0;z-index:300;background:rgba(4,10,18,.97);display:flex;flex-direction:column;justify-content:center;padding:22px;gap:9px;overflow:auto"></div>');
    ov.appendChild(el('<div style="font-weight:800;font-size:18px">'+(a.id?'Upravit datovku':'Nová datovka')+' 📮</div>'));
    function inp(ph,val,type){ return el('<input '+(type?('type="'+type+'" '):'')+'placeholder="'+ph+'" value="'+esc(val||"")+'" style="margin:0">'); }
    var co=inp("Firma (např. EUROSOFT-Control)",a.company_label);
    var bx=inp("ID datové schránky",a.box_id);
    var ln=inp("Přihlašovací jméno",a.login_name);
    var pw=inp(a.has_pwd?"Heslo (nech prázdné = beze změny)":"Heslo",null,"password");
    var vs=inp("VS u ČSSZ (nepovinné)",a.cssz_vs);
    var tn=inp("Tenant ID (default 2 = EUROSOFT)",a.tenant_id!=null?String(a.tenant_id):"2");
    var st=el('<div class="hint" style="min-height:15px"></div>');
    var save=el('<button class="green full" style="margin:0">Uložit</button>');
    var cl=el('<button class="ghost full" style="margin:0">Zavřít</button>');
    cl.addEventListener("click",function(){ ov.remove(); });
    save.addEventListener("click",function(){
      var body={id:a.id||null, company_label:co.value.trim(), box_id:bx.value.trim(),
        login_name:ln.value.trim(), cssz_vs:vs.value.trim(),
        tenant_id:parseInt(tn.value,10)||2, active:true};
      if(pw.value) body.password=pw.value;
      if(!body.company_label||!body.box_id){ st.textContent="Vyplň firmu i ID schránky."; return; }
      save.disabled=true; st.textContent="Ukládám…";
      api("POST","/api/v1/erp/app/isds/account/save",body).then(function(r){
        if(r&&r.ok){ ov.remove(); isdsLoad(); }
        else { save.disabled=false; st.textContent=((r&&(r.error||r.detail))||"Nepovedlo se."); }
      });
    });
    ov.appendChild(el('<div class="hint" style="line-height:1.5">Heslo se uloží šifrovaně. Jeden tenant může mít víc datovek — přidej je jako samostatné záznamy.</div>'));
    [co,bx,ln,pw,vs,tn,st,save,cl].forEach(function(e){ ov.appendChild(e); });
    app.appendChild(ov);
  }
  function isdsSync(id,days){
    _isdsBanner(days?("Stahuji historii "+days+" dní…"):"Synchronizuji datovku…","progress");
    var pl={account_id:parseInt(id,10)}; if(days){pl.days_back=days;}
    api("POST","/api/v1/erp/app/isds/sync",pl).then(function(r){
      if(r&&r.ok){ var hasErr=r.errors&&r.errors.length; try{_isdsBanner("Hotovo: "+r["new"]+" nových"+(hasErr?(" · chyba: "+r.errors[0]):""), hasErr?"err":"ok");}catch(e){} isdsLoad(); }
      else { try{_isdsBanner("Chyba: "+((r&&(r.error||r.detail))||"?"),"err");}catch(e){} }
    }).catch(function(){ try{_isdsBanner("Chyba spojení.","err");}catch(e){} });
  }

  // ── PŘEFAKTURACE ES → Control (Marti 19.6.2026) ──────────────────────
  function prefKc(n){ try{ return (Math.round((+n||0)*100)/100).toLocaleString('cs-CZ',{minimumFractionDigits:2,maximumFractionDigits:2})+' Kč'; }catch(e){ return (n||0)+' Kč'; } }
  function prefV(id){ var e=document.getElementById(id); return e?e.value:""; }
  function prefakturace(){
    app.innerHTML=topbar("🧾 Přefakturace ES → Control", true);
    window._pref=window._pref||{};
    app.appendChild(el('<div class="muted" style="margin:8px 6px;line-height:1.5">Rozpad služeb EUROSOFT‑System → Control za měsíc, a po schválení (Marti/Braňo) vystavení faktury. Výpočet i faktura = ověřené procedury Centrály. Marže 5 %, nájem dle dokladu.</div>'));
    var ctl=el('<div style="margin:8px 6px;display:flex;gap:10px;flex-wrap:wrap;align-items:flex-end;"></div>');
    ctl.appendChild(el('<label style="font-size:12px;color:#9fb0c2">Měsíc<br><input id="prefM" type="number" min="1" max="12" style="width:72px;margin:3px 0 0"></label>'));
    ctl.appendChild(el('<label style="font-size:12px;color:#9fb0c2">Rok<br><input id="prefR" type="number" min="2020" max="2100" style="width:92px;margin:3px 0 0"></label>'));
    ctl.appendChild(el('<label style="font-size:12px;color:#9fb0c2">Marže %<br><input id="prefMarze" type="number" min="0" max="100" step="0.5" style="width:84px;margin:3px 0 0"></label>'));
    app.appendChild(ctl);
    var bRoz=el('<button class="green full" style="margin:10px 6px 0;width:calc(100% - 12px)">📋 Zobrazit rozpad</button>');
    bRoz.addEventListener("click",prefRozpad);
    app.appendChild(bRoz);
    app.appendChild(el('<div id="prefPosl" class="hint" style="margin:8px 6px"></div>'));
    app.appendChild(el('<div id="prefOut" style="margin:4px 6px"></div>'));
    api("GET","/api/v1/erp/app/prefakturace/info","").then(function(j){
      var now=new Date();
      var dm=(j&&j.ok)?j.mesic:(now.getMonth()||12), dr=(j&&j.ok)?j.rok:now.getFullYear(), dz=(j&&j.ok)?j.marze:5;
      var mEl=document.getElementById("prefM"); if(mEl)mEl.value=dm;
      var rEl=document.getElementById("prefR"); if(rEl)rEl.value=dr;
      var zEl=document.getElementById("prefMarze"); if(zEl)zEl.value=(dz==null?5:dz);
      var po=document.getElementById("prefPosl");
      if(j&&!j.ok&&(j.error||j.detail)&&!j.posledni){ if(po)po.innerHTML='<span style="color:#ff8a8a">'+esc(j.error||j.detail)+'</span>'; return; }
      if(po&&j&&j.posledni&&j.posledni.length){ po.innerHTML='Naposledy vystaveno: '+j.posledni.slice(0,3).map(function(p){return '#'+esc(String(p.cislo))+' ('+esc(String(p.mesic))+'/'+esc(String(p.rok))+')';}).join(' · '); }
    });
  }
  function prefRozpad(){
    var out=document.getElementById("prefOut"); if(!out)return;
    var m=parseInt(prefV("prefM"),10), r=parseInt(prefV("prefR"),10), z=parseFloat(prefV("prefMarze"));
    if(!m||!r){ out.innerHTML='<div class="hint" style="color:#ff8a8a;padding:8px">Doplň měsíc a rok.</div>'; return; }
    out.innerHTML='<div class="hint" style="padding:14px">Počítám rozpad z účetnictví… chvíli to trvá.</div>';
    api("POST","/api/v1/erp/app/prefakturace/rozpad",{mesic:m,rok:r,marze:z}).then(function(j){
      if(!j||!j.ok){ out.innerHTML='<div class="hint" style="color:#ff8a8a;padding:10px">'+esc((j&&(j.error||j.detail))||"Nepovedlo se.")+'</div>'; return; }
      window._pref.last={mesic:m,rok:r,marze:z,prev:(j.jiz_existuje?String(j.jiz_existuje.cislo):null)};
      var h='';
      if(j.jiz_existuje){ h+='<div style="margin:6px 0;padding:10px;border-radius:10px;background:rgba(251,191,36,.12);border:1px solid #fbbf24;color:#fde68a;font-size:13px">⚠️ Za '+m+'/'+r+' už existuje faktura č. <b>'+esc(String(j.jiz_existuje.cislo))+'</b> ('+esc(j.jiz_existuje.dat||"")+'). Vystavením vznikne duplikát.</div>'; }
      if(j.najem!=null && j.najem_minule!=null && Math.abs(j.najem-j.najem_minule)>0.5){ h+='<div style="margin:6px 0;padding:10px;border-radius:10px;background:rgba(91,141,239,.12);border:1px solid #5b8def;color:#cfe0ff;font-size:13px">ℹ️ Nájem se liší od minula: '+prefKc(j.najem_minule)+' → <b>'+prefKc(j.najem)+'</b>. Zkontroluj.</div>'; }
      h+='<table style="width:100%;border-collapse:collapse;font-size:13px;margin-top:6px">';
      (j.lines||[]).forEach(function(l){ h+='<tr style="border-bottom:1px solid #1b2742"><td style="padding:6px 4px;vertical-align:top">'+esc(l.popis)+'</td><td style="padding:6px 4px;text-align:right;white-space:nowrap;font-weight:600">'+prefKc(l.castka)+'</td></tr>'; });
      h+='</table>';
      h+='<div style="margin-top:10px;font-size:13px;border-top:2px solid #2a3b5c;padding-top:8px">'
        +'<div style="display:flex;justify-content:space-between"><span>Základ</span><b>'+prefKc(j.zaklad)+'</b></div>'
        +'<div style="display:flex;justify-content:space-between;color:#9fb0c2"><span>DPH 21 %</span><span>'+prefKc(j.dph)+'</span></div>'
        +'<div style="display:flex;justify-content:space-between;font-size:15px;margin-top:4px"><span>Celkem</span><b style="color:#34d399">'+prefKc(j.celkem)+'</b></div></div>';
      h+='<button id="prefIssue" style="margin-top:14px;width:100%;background:'+(j.jiz_existuje?"#b4791f":"#10b981")+';color:#04150e;border:0;border-radius:11px;padding:13px;font-size:15px;font-weight:700">📤 '+(j.jiz_existuje?"Přesto vystavit (duplikát)":"Vystavit fakturu")+'</button>';
      h+='<div id="prefIssueMsg" class="hint" style="margin-top:8px;min-height:16px"></div>';
      out.innerHTML=h;
      document.getElementById("prefIssue").addEventListener("click",function(){ prefVystavit(!!j.jiz_existuje); });
    }).catch(function(){ out.innerHTML='<div class="hint" style="color:#ff8a8a;padding:10px">Chyba spojení.</div>'; });
  }
  function prefVystavit(force){
    var L=window._pref&&window._pref.last; if(!L)return;
    var msg=document.getElementById("prefIssueMsg"), btn=document.getElementById("prefIssue");
    confirmDialog("Vystavit fakturu","Vystavit přefakturaci za "+L.mesic+"/"+L.rok+"? Pošle se ke schválení (Marti/Braňo) a po potvrzení se vystaví daňový doklad v Centrále.","📤 Ano, ke schválení",function(){
      if(btn)btn.disabled=true; if(msg){msg.style.color="#9fb0c2";msg.textContent="Posílám ke schválení…";}
      api("POST","/api/v1/erp/app/prefakturace/vystavit",{mesic:L.mesic,rok:L.rok,marze:L.marze,force:!!force}).then(function(r){
        if(r&&r.ok){ if(msg){msg.style.color="#34d399";msg.innerHTML="✅ Čeká na schválení v banneru (Marti/Braňo). Po potvrzení se faktura vystaví — číslo se objeví zde.";} prefPoll(L.mesic,L.rok,L.prev,0); }
        else if(r&&r.duplicate){ if(msg){msg.style.color="#fbbf24";msg.textContent=(r.error||"Faktura už existuje.");} if(btn)btn.disabled=false; }
        else { if(msg){msg.style.color="#ff8a8a";msg.textContent="Chyba: "+((r&&(r.error||r.detail))||"?");} if(btn)btn.disabled=false; }
      }).catch(function(){ if(msg){msg.style.color="#ff8a8a";msg.textContent="Chyba spojení.";} if(btn)btn.disabled=false; });
    });
  }
  function prefPoll(m,r,prev,n){
    if(n>60)return; var msg=document.getElementById("prefIssueMsg"); if(!msg)return;
    api("GET","/api/v1/erp/app/prefakturace/stav?mesic="+m+"&rok="+r,"").then(function(j){
      var c=(j&&j.ok&&j.faktura)?String(j.faktura.cislo):null;
      if(c && c!==String(prev||"")){ msg.style.color="#34d399"; msg.innerHTML="✅ Vystaveno — faktura č. <b>"+esc(c)+"</b>"+(j.faktura.dat?(" ("+esc(j.faktura.dat)+")"):"")+"."; return; }
      setTimeout(function(){ prefPoll(m,r,prev,n+1); },5000);
    }).catch(function(){ setTimeout(function(){ prefPoll(m,r,prev,n+1); },6000); });
  }

  // ── Oběh zakázky: stupeň POPTÁVKA ──────────────────────────────────────
  var _POP_LBL={nova:"Nová",zpracovava:"Zpracovává se",nabidnuto:"Nabídnuto",vyhrana:"Vyhraná",zamitnuta:"Zamítnutá"};
  var _POP_COL={nova:"#9fb0c2",zpracovava:"#fbbf24",nabidnuto:"#5b8def",vyhrana:"#34d399",zamitnuta:"#ff8a8a"};
  function poptavka(){
    app.innerHTML=topbar("📥 Poptávky — oběh zakázky", true);
    app.appendChild(el('<div class="muted" style="margin:8px 6px;line-height:1.5">První stupeň oběhu zakázky: <b>poptávka → kalkulace → nabídka → objednávka → zakázka</b>. Eviduj příchozí poptávky (zákazník, popis, řešitel, stav). Klikni na poptávku pro úpravu.</div>'));
    app.appendChild(el('<div id="popBox" style="margin:4px 6px"></div>'));
    if(window._swRes){ popLoad(); }
    else { api("GET","/api/v1/erp/app/sw/resitele","").then(function(j){ window._swRes=(j&&j.resitele)||[]; popLoad(); }); }
  }
  function popLoad(){
    var box=document.getElementById("popBox"); if(!box)return;
    box.innerHTML='<div class="hint" style="padding:12px">Načítám…</div>';
    api("GET","/api/v1/erp/app/poptavka/list","").then(function(j){
      if(!j||!j.ok){ box.innerHTML='<div class="hint" style="color:#ff8a8a;padding:10px">'+esc((j&&(j.error||j.detail))||"Chyba")+'</div>'; return; }
      window._popStavy=j.stavy||Object.keys(_POP_LBL);
      var pp=j.poptavky||[];
      var f=window._popFilter||"";
      var open=pp.filter(function(p){ return p.stav!=="zamitnuta"&&p.stav!=="vyhrana"; }).length;
      var h='<div style="display:flex;gap:8px;flex-wrap:wrap;margin:4px 0 8px">'
        +'<div style="flex:1;min-width:110px;background:rgba(255,255,255,.03);border:1px solid var(--bord);border-radius:10px;padding:8px"><div class="hint">Poptávek</div><div style="font-weight:800;font-size:17px">'+pp.length+'</div></div>'
        +'<div style="flex:1;min-width:110px;background:rgba(255,255,255,.03);border:1px solid var(--bord);border-radius:10px;padding:8px"><div class="hint">Otevřených</div><div style="font-weight:800;font-size:17px;color:#fbbf24">'+open+'</div></div>'
        +'</div>';
      h+='<input id="popSearch" placeholder="Hledat (číslo, zákazník, řešitel)…" value="'+esc(f)+'" style="margin:0 0 8px">';
      h+='<button id="popAdd" class="green full" style="margin:0 0 10px;width:100%">➕ Nová poptávka</button>';
      var fl=f.toLowerCase();
      var shown=pp.filter(function(p){ if(!fl)return true; return ((p.cislo||"")+" "+(p.zakaznik||"")+" "+(p.resitel||"")+" "+(p.popis||"")).toLowerCase().indexOf(fl)>=0; });
      shown.forEach(function(p){
        var col=_POP_COL[p.stav]||"#9fb0c2", lbl=_POP_LBL[p.stav]||p.stav;
        h+='<div class="pop-card" data-id="'+p.id+'" style="margin:7px 0;padding:11px;background:rgba(255,255,255,.03);border:1px solid var(--bord);border-radius:12px;cursor:pointer">'
          +'<div style="display:flex;justify-content:space-between;gap:8px"><div style="font-weight:700"><span style="font-size:10.5px;color:#7c5cff;border:1px solid #7c5cff55;border-radius:6px;padding:0 5px;margin-right:5px">'+esc(p.typ||"SW")+'</span>'+esc(p.cislo||p.zakaznik||"(bez čísla)")+'</div>'
          +'<span style="flex:none;font-size:11.5px;padding:2px 8px;border-radius:10px;background:'+col+'22;color:'+col+';border:1px solid '+col+'">'+esc(lbl)+'</span></div>'
          +'<div style="font-size:12.5px;color:#9fb0c2;margin-top:3px">'+esc(p.zakaznik||"—")+(p.resitel?(' · '+esc(p.resitel)):'')+(p.datum?(' · '+esc(p.datum)):'')+'</div>'
          +(p.popis?('<div style="font-size:12.5px;margin-top:5px;color:#c8d2dc">'+esc(p.popis)+'</div>'):'')+'</div>';
      });
      if(!shown.length) h+='<div class="hint" style="padding:10px">Žádná poptávka. Přidej první přes ➕.</div>';
      box.innerHTML=h;
      var si=document.getElementById("popSearch");
      si.addEventListener("input",function(){ window._popFilter=si.value; var p=si.selectionStart; popLoad(); setTimeout(function(){ var n=document.getElementById("popSearch"); if(n){n.focus(); try{n.setSelectionRange(p,p);}catch(e){}} },0); });
      document.getElementById("popAdd").addEventListener("click",function(){ popForm(null); });
      box.querySelectorAll(".pop-card").forEach(function(c){ c.addEventListener("click",function(){ popForm({_id:c.getAttribute("data-id")}); }); });
    });
  }
  function _popResSel(id,val){ var o='<option value="">— řešitel —</option>'; (window._swRes||[]).forEach(function(r){ o+='<option value="'+r.id+'"'+(String(r.id)===String(val)?' selected':'')+'>'+esc(r.jmeno||("#"+r.id))+'</option>'; }); return '<select id="'+id+'" style="margin:0">'+o+'</select>'; }
  function _popStavSel(id,val){ var o=''; (window._popStavy||Object.keys(_POP_LBL)).forEach(function(s){ o+='<option value="'+s+'"'+(s===val?' selected':'')+'>'+(_POP_LBL[s]||s)+'</option>'; }); return '<select id="'+id+'" style="margin:0">'+o+'</select>'; }
  function popForm(z){
    z=z||{};
    function render(p){
      p=p||{};
      var ov=el('<div style="position:fixed;inset:0;z-index:300;background:rgba(4,10,18,.98);overflow:auto;padding:20px;display:flex;flex-direction:column;gap:8px"></div>');
      ov.appendChild(el('<div style="font-weight:800;font-size:18px">'+(p.id?'Upravit poptávku':'Nová poptávka')+' 📥</div>'));
      function fld(lbl,inner){ var w=el('<label style="font-size:12px;color:#9fb0c2">'+lbl+'</label>'); w.appendChild(el('<div style="margin-top:2px">'+inner+'</div>')); return w; }
      function inp(id,val,ph,type){ return '<input id="'+id+'" '+(type?('type="'+type+'" '):'')+'placeholder="'+(ph||"")+'" value="'+esc(val==null?"":String(val))+'" style="margin:0">'; }
      ov.appendChild(fld("Typ", '<select id="popTyp" style="margin:0"><option value="SW"'+((p.typ||"SW")==="SW"?" selected":"")+'>SW (automatizace)</option><option value="VR"'+(p.typ==="VR"?" selected":"")+'>VR (výroba rozvaděčů)</option></select>'));
      ov.appendChild(fld("Číslo poptávky", inp("popCislo",p.cislo,"P2026-001 (volitelné)")));
      ov.appendChild(fld("Zákazník", inp("popZak",p.zakaznik,"Tesla / BMW…")));
      ov.appendChild(fld("Kontakt (osoba / e-mail / tel.)", inp("popKont",p.kontakt,"")));
      ov.appendChild(fld("Popis poptávky", '<textarea id="popPopis" placeholder="Co zákazník poptává…" style="margin:0;min-height:70px">'+esc(p.popis||"")+'</textarea>'));
      ov.appendChild(fld("Zdroj", inp("popZdroj",p.zdroj,"web / doporučení / veletrh…")));
      ov.appendChild(fld("Datum přijetí", inp("popDatum",p.datum||"","DD.MM.RRRR")));
      ov.appendChild(fld("Řešitel", _popResSel("popResitel",p.resitel_user_id)));
      ov.appendChild(fld("Stav", _popStavSel("popStav",p.stav||"nova")));
      ov.appendChild(fld("Poznámka", inp("popPozn",p.poznamka,"")));
      var st=el('<div class="hint" style="min-height:15px"></div>'); ov.appendChild(st);
      var save=el('<button class="green full" style="margin:0">Uložit</button>');
      var cl=el('<button class="ghost full" style="margin:0">Zavřít</button>');
      cl.addEventListener("click",function(){ ov.remove(); });
      function V(id){ var e=document.getElementById(id); return e?e.value:""; }
      save.addEventListener("click",function(){
        var body={id:p.id||null, typ:V("popTyp"), cislo:V("popCislo"), zakaznik:V("popZak"), kontakt:V("popKont"),
          popis:V("popPopis"), zdroj:V("popZdroj"), datum_prijeti:V("popDatum"), resitel_user_id:V("popResitel"),
          stav:V("popStav"), poznamka:V("popPozn")};
        save.disabled=true; st.textContent="Ukládám…";
        api("POST","/api/v1/erp/app/poptavka/save",body).then(function(r){
          if(r&&r.ok){ ov.remove(); popLoad(); } else { save.disabled=false; st.textContent=((r&&(r.error||r.detail))||"Nepovedlo se."); }
        });
      });
      ov.appendChild(save);
      if(p.id){ var del=el('<button class="ghost full" style="margin:0;color:#ff8a8a">Smazat</button>');
        del.addEventListener("click",function(){ confirmDialog("Smazat poptávku?","Poptávka se skryje z přehledu.","Smazat",function(){ api("POST","/api/v1/erp/app/poptavka/delete",{id:p.id}).then(function(){ ov.remove(); popLoad(); }); }); });
        ov.appendChild(del); }
      ov.appendChild(cl);
      app.appendChild(ov);
    }
    if(z._id){ api("GET","/api/v1/erp/app/poptavka/detail?id="+z._id,"").then(function(j){ render((j&&j.poptavka)||{}); }); }
    else { render(z); }
  }

  var SCREENS={home:home,poptavka:poptavka,phone:phone,notifs:notifs,claudetasks:claudetasks,claudeDetail:claudeDetail,mytodo:mytodo,ecukoly:ecukoly,strtask:strtask,contacts:contacts,calllog:calllog,settings:settings,apps:apps,firma:firma,vyroba:vyroba,vyroba_hub:vyroba_hub,vedeni:vedeni,soon:soon,skupiny:skupiny,sdileny:sdileny,dochazka:dochazka,alluser:alluser,set_listen:set_listen,set_icons:set_icons,set_install:set_install,set_prefixes:set_prefixes,set_phone:set_phone,set_notifaccess:set_notifaccess,set_dev:set_dev,set_about:set_about,strategie_nastroje:strategie_nastroje,apid_restore:apid_restore,set_imp:set_imp,set_smsgw:set_smsgw,set_shot:set_shot,urgent:urgent,hr_hub:hr_hub,hr:hr,hr_interni:hr_interni,hr_firma:hr_firma,hr_skupiny:hr_skupiny,hr_nabor:hr_nabor,hr_naroz:hr_naroz,hr_novi:hr_novi,hr_nabor_list:hr_nabor_list,hr_nabor_detail:hr_nabor_detail,hr_cv_result:hr_cv_result,hr_soon:hr_soon,hr_me:hr_me,hr_people:hr_people,hr_rezimy:hr_rezimy,hr_att_source:hr_att_source,ocr:ocr,ocr_schval:ocr_schval,sick:sick,sick_schval:sick_schval,np_prehled:np_prehled,med:med,med_schval:med_schval,med_prehled:med_prehled,hr_konto:hr_konto,hr_import:hr_import,hr_podminky:hr_podminky,moje_podminky:moje_podminky,absence:absence,kdekdo:kdekdo,hr_person:hr_person,sms_stav:sms_stav,dev_stav:dev_stav,doc_gen:doc_gen,wage_cmp:wage_cmp,kara:kara,kara_new:kara_new,kara_detail:kara_detail,kara_motive:kara_motive,kara_ref:kara_ref,kara_quad:kara_quad,kara_board:kara_board,hr_inzeraty:hr_inzeraty,hr_inzerat_edit:hr_inzerat_edit,ops:ops,plan:plan,plan_vyjimky:plan_vyjimky,moje_cinnosti:moje_cinnosti,master_cinnosti:master_cinnosti,prace:prace,prace_zak:prace_zak,prace_cin:prace_cin,webview:webview,web_stats:web_stats,doch_dnesek:doch_dnesek,doch_historie:doch_historie,doch_zitrek:doch_zitrek,moje_finance:moje_finance,moje_zadosti:moje_zadosti,planapprovals:planapprovals,bk_rozvrh:bk_rozvrh,bk_tridy:bk_tridy,bk_ucitele:bk_ucitele,bk_class:bk_class,bk_teacher:bk_teacher,bk_ucebny:bk_ucebny,bk_room:bk_room,bk_uvazky:bk_uvazky,bk_skola:bk_skola,uceni:uceni,migrace:migrace,migrace_dochazka:migrace_dochazka,migrace_mzdy:migrace_mzdy,prefakturace:prefakturace,isds:isds,sw_zakazky:sw_zakazky,extview:extview,persDnesek:persDnesek,claude27:claude27,coord:coord,fronta:fronta};

  // Claude-27 týmová hra (Marti 24.6.2026): Zuzka (+Mirek) vidí frontu Clauda-27
  // a dá mu „Go", když stojí. Slyšitelné notifikace chodí přes mobile_command.
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
        var isStg=/STG-[A-Za-z]+-/.test(body);
        // ČSSZ eOČR SMS (přeposlaná zaměstnancem) — forwardni i ji, server ji
        // v store_inbound_sms rozpozná a založí OČR případ. Kristý/Claude-24 23.6.
        var isOcr=(lb.indexOf("eportal.cssz.cz")>=0 && lb.indexOf("identifik")>=0
                   && (lb.indexOf("osetrov")>=0 || lb.indexOf("ošetřov")>=0));
        if(!isStg && !isOcr) return;
        var num=s.number||s.address||"";
        var key="stgfwd_"+num+"_"+(s.date||s.when||"")+"_"+body.replace(/\s/g,"").slice(0,16);
        try{ if(localStorage.getItem(key)) return; }catch(e){}
        api("POST","/api/v1/erp/app/sms-inbound",{from:num,body:body}).then(function(r){
          if(r&&r.ok){ try{ localStorage.setItem(key,"1"); }catch(e){} }
        });
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
