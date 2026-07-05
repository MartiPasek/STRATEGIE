<script>
(function () {
  var B = window.STRATEGIE || null;
  var deferredPrompt = null;
  window.addEventListener("beforeinstallprompt", function (e) { e.preventDefault(); deferredPrompt = e; });
  if ("serviceWorker" in navigator) { try { navigator.serviceWorker.register("/mobile-sw.js", { scope: "/mobile" }); } catch (e) {} }

  var canDial = !!(B && (typeof B.dialNumber === "function" || typeof B.dial === "function"));
  var canListen = !!(B && typeof B.listening === "function");
  var canFetch = !!(B && typeof B.authedFetch === "function");
  var canSms = !!(B && typeof B.sendSms === "function" && typeof B.deviceId === "function");
  // iOS companion (WKWebView) se hlásí markerem v user-agentu (ContentView.swift
  // applicationNameForUserAgent="STRATEGIE-iOS"). Kristý/Jirka 12.6.2026.
  var nativeIOS = /STRATEGIE-iOS/i.test(navigator.userAgent || "");
  var native = canDial || canListen || canFetch;   // Android bridge schopnosti (SIM/SMS/dial) — Android-only funkce
  var nativeApp = native || nativeIOS;              // jakákoli nativní appka (jen pro popisek/chip)
  var ver = (B && typeof B.version === "function") ? (function(){try{return B.version();}catch(e){return "";}})() : "";

  var params = new URLSearchParams(location.search);
  if (params.get("dev") === "1") { try { localStorage.setItem("stg_mobile_dev","1"); } catch(e){} }
  if (params.get("dev") === "0") { try { localStorage.removeItem("stg_mobile_dev"); } catch(e){} }
  var DEV = false; try { DEV = localStorage.getItem("stg_mobile_dev") === "1"; } catch(e){}

  var app = document.getElementById("app");
  var bnav = document.getElementById("bnav");
  var bnavx1 = document.getElementById("bnavx1");
  var bnavx2 = document.getElementById("bnavx2");
  var bnavback = document.getElementById("bnavback");
  var navwrap = document.getElementById("navwrap");
  var curTab = "home";
  var stack = ["home"];
  var notifCount = null;
  var _planApprovalCount = 0;   // Marti 14.6.: počet plánů čekajících na MÉ schválení (přičítá se do badge Úkoly)
  var _signPend = 0;   // Marti 5.7.: počet dokumentů čekajících na můj podpis (badge Podpisy smluv / Aplikace / Domů)
  var _hasUpdate = false;
  var _lastOk = 0;            // čas poslední úspěšné odezvy serveru (liveness)
  function markOk(){ _lastOk = Date.now(); }
  function refreshUpdate(){ try{ if(B&&typeof B.checkUpdate==="function"){ var t=B.checkUpdate(); var u=t?JSON.parse(t):null; _hasUpdate=!!(u&&u.has_update); } }catch(e){} }
  var avatarUrl = "/api/v1/erp/app/avatar";
  if (B && typeof B.avatarDataUrl === "function") { try { var d=B.avatarDataUrl(); if(d) avatarUrl=d; } catch(e){} }

  var CLAUDE_SVG='<svg width="26" height="26" viewBox="0 0 100 100"><g stroke="#d97757" stroke-width="8" stroke-linecap="round"><line x1="50" y1="50" x2="50" y2="8"/><line x1="50" y1="50" x2="71" y2="13.6"/><line x1="50" y1="50" x2="86.4" y2="29"/><line x1="50" y1="50" x2="92" y2="50"/><line x1="50" y1="50" x2="86.4" y2="71"/><line x1="50" y1="50" x2="71" y2="86.4"/><line x1="50" y1="50" x2="50" y2="92"/><line x1="50" y1="50" x2="29" y2="86.4"/><line x1="50" y1="50" x2="13.6" y2="71"/><line x1="50" y1="50" x2="8" y2="50"/><line x1="50" y1="50" x2="13.6" y2="29"/><line x1="50" y1="50" x2="29" y2="13.6"/></g></svg>';
  var PHONE_SVG='<svg width="22" height="22" viewBox="0 0 24 24" fill="#22c55e"><path d="M6.6 10.8c1.4 2.8 3.8 5.1 6.6 6.6l2.2-2.2c.3-.3.7-.4 1-.2 1.1.4 2.3.6 3.6.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1C10.6 21 3 13.4 3 4c0-.6.4-1 1-1h3.5c.6 0 1 .4 1 1 0 1.2.2 2.4.6 3.6.1.4 0 .8-.3 1.1l-2.2 2.1z"/></svg>';
  function esc(s){ return (s||"").replace(/[&<>"]/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;"}[c];}); }
  function el(html){ var d=document.createElement("div"); d.innerHTML=html.trim(); return d.firstChild; }
  function go(id){ stack.push(id); render(); }
  function back(){
    // Marti 14.6.: otevřený dialog (.appmodal) zavři jako první.
    try{ var _md=document.querySelectorAll('.appmodal'); if(_md.length){ _md[_md.length-1].remove(); return; } }catch(e){}
    // Marti 14.6.: v Plánu zpět o JEDEN krok — z otevřeného týdne zpět na seznam.
    try{ if(typeof window._planAnyOpen==="function" && window._planAnyOpen()) return; }catch(e){}
    // Marti 8.6.: nejdřív zavřít otevřený accordion (Výroba/kontakty), teprve pak odejít.
    try{ var _op=document.querySelector('#vylist li.ct.open'); if(_op){ _op.classList.remove('open'); var _x=_op.querySelector('.ctexp'); if(_x)_x.style.display='none'; return; } }catch(e){}
    // Marti 5.7.: dej šanci vnitřní stránce (extview iframe) zpracovat Zpět (zavřít vlastní overlay/detail) DŘÍV než opustíme modul.
    try{ if(stack[stack.length-1]==="extview"){ var _xf=document.getElementById("stgXvF"); if(_xf && _xf.contentWindow && typeof _xf.contentWindow.__onAppBack==="function" && _xf.contentWindow.__onAppBack()===true) return; } }catch(e){}
    // V appce otevřená stránka (extview): zpět o JEDEN krok v rámci appky (dokument → root ISO), ne ven.
    try{ if(stack[stack.length-1]==="extview" && _xvStack.length>1){ _xvStack.pop(); _xvSet(_xvStack[_xvStack.length-1]); render(); return; } }catch(e){}
    if(stack.length>1){ stack.pop(); render(); }
  }
  // iPhone nemá systémové tlačítko Zpět → swipe od levého okraje = Zpět.
  // Funguje v PWA (Přidat na plochu) i ve WKWebView. Na Androidu jako bonus gesto.
  (function(){
    var sx=0, sy=0, st=0, tracking=false;
    document.addEventListener("touchstart", function(e){
      if(!e.touches || e.touches.length!==1){ tracking=false; return; }
      var t=e.touches[0];
      if(t.clientX<=26){ tracking=true; sx=t.clientX; sy=t.clientY; st=Date.now(); }
      else tracking=false;
    }, {passive:true});
    document.addEventListener("touchend", function(e){
      if(!tracking) return; tracking=false;
      var t=e.changedTouches && e.changedTouches[0]; if(!t) return;
      var dx=t.clientX-sx, dy=Math.abs(t.clientY-sy), dt=Date.now()-st;
      if(dx>60 && dy<48 && dt<700){ try{ _tapFeedback(); }catch(_){ } back(); }
    }, {passive:true});
  })();
  function selectTab(t){ curTab=t; stack=[t]; render(); }
  // hardwarové zpět (nativní HybridActivity volá): vrať true když jsme šli o úroveň výš, false na home
  // Marti 7.6. večer: 1) zavřít otevřené věci · 2) vyjet nahoru · 3) o úroveň
  // výš / na home · 4) zeptat se, zda opravdu odejít (další Zpět = odchod).
  function showExitAsk(){
    if(document.getElementById("exitAsk")) return;
    var d=el('<div id="exitAsk" style="position:fixed;left:0;right:0;top:0;bottom:0;background:rgba(0,0,0,.55);z-index:999;display:flex;align-items:flex-end;justify-content:center;"></div>');
    var c=el('<div style="background:var(--surf);border:1px solid var(--bord);border-radius:16px 16px 0 0;padding:18px 16px calc(18px + env(safe-area-inset-bottom,0px));width:100%;max-width:520px;"></div>');
    c.appendChild(el('<div style="font-size:16px;font-weight:700;">Opravdu chceš odejít?</div>'));
    c.appendChild(el('<div class="hint" style="margin-top:4px;">Stiskni Zpět ještě jednou pro odchod.</div>'));
    var b=el('<button class="green full" style="margin-top:12px;">Zůstávám 🙂</button>');
    b.addEventListener("click",function(){ d.remove(); });
    d.addEventListener("click",function(ev){ if(ev.target===d) d.remove(); });
    c.appendChild(b); d.appendChild(c); document.body.appendChild(d);
  }
  window.__stgBack=function(){
    // Marti 11.6.: ochrana proti dvojímu Zpět (< 200 ms) + zvukové ťuknutí jako ostatní volby.
    var _nb=Date.now(); if(window._lastBackTs && (_nb-window._lastBackTs)<200) return true; window._lastBackTs=_nb;
    try{ _tapFeedback(); }catch(e){}
    // Kreslení snímku: systémové Zpět = stejné jako horní „↶ Zpět" (vrátí poslední
    // tah); když není co vracet, zavře overlay. Marti 11.6.
    var _sov=document.getElementById("shotOverlay");
    if(_sov){ if(typeof window._shotOverlayBack==="function") return window._shotOverlayBack();
      _sov.remove(); var _sfab=document.getElementById("shotFab"); if(_sfab)_sfab.style.display=""; return true; }
    // Marti 14.6.: otevřený dialog (.appmodal) zavři jako první.
    try{ var _md=document.querySelectorAll('.appmodal'); if(_md.length){ _md[_md.length-1].remove(); return true; } }catch(e){}
    // overlay odchodu už visí → druhý stisk Zpět = opravdu odejít
    // Marti 11.6.: detail jobu přes celou obrazovku → Zpět zavře jen jeho (o úroveň níž).
    var _jov=document.getElementById("jobOverlay");
    if(_jov){ _jov.remove(); return true; }
    var ov=document.getElementById("exitAsk");
    if(ov){ ov.remove(); return false; }
    // V kontaktech postupně: 1) odscrolluj nahoru, 2) smaž číslo ze zeleného pole,
    // 3) smaž filtr, teprve pak odejdi. Marti 6.6.2026.
    if(curTab==="contacts" && stack[stack.length-1]==="contacts"){
      var st=window.pageYOffset||document.documentElement.scrollTop||(document.body&&document.body.scrollTop)||0;
      if(st>10){ try{window.scrollTo({top:0,behavior:"smooth"});}catch(e){window.scrollTo(0,0);} return true; }
      if(_dialNum){ setDialNum(""); return true; }
      var sf=document.getElementById("ctsearch"); if(sf && sf.value && sf.value.length){ sf.value=""; try{renderContactsList();}catch(e){} return true; }
    }
    // 1) zavřít otevřené věci (menu rozhovoru, rozbalené sekce docházky, týden v plánu)
    try{ if(typeof window._dochAnyOpen==="function" && window._dochAnyOpen()) return true; }catch(e){}
    try{ if(typeof window._planAnyOpen==="function" && window._planAnyOpen()) return true; }catch(e){}
    // 2) vyjet nahoru
    var st2=window.pageYOffset||document.documentElement.scrollTop||(document.body&&document.body.scrollTop)||0;
    if(st2>40){ try{window.scrollTo({top:0,behavior:"smooth"});}catch(e){window.scrollTo(0,0);} return true; }
    // 3) o úroveň výš / na home
    if(stack.length>1){ back(); return true; }
    if(curTab!=="home"){ selectTab("home"); return true; }
    // 4) zeptat se
    showExitAsk();
    return true;
  };
  // Spuštění přes ikonu v launcheru → vždy hlavní obrazovka (volá nativní onNewIntent).
  window.__stgHome=function(){ try{ selectTab("home"); }catch(e){} return true; };

  // Marti 8.6. ráno: jemné potvrzení KAŽDÉHO tapu — krátká vibrace + tichý
  // blip (WebAudio, žádný soubor). Ať je jisté, že appka dotek zaznamenala.
  var _tapAC=null;
  function _tapFeedback(){
    try{ if(navigator.vibrate) navigator.vibrate(12); }catch(e){}
    try{
      _tapAC=_tapAC||new (window.AudioContext||window.webkitAudioContext)();
      if(_tapAC.state==="suspended") _tapAC.resume();
      // Marti 8.6.: jemněji — tišší, měkčí a kratší (sotva slyšitelný ťuk)
      var o=_tapAC.createOscillator(), g=_tapAC.createGain();
      o.type="sine"; o.frequency.value=620;
      g.gain.setValueAtTime(0.005,_tapAC.currentTime);
      g.gain.exponentialRampToValueAtTime(0.0004,_tapAC.currentTime+0.04);
      o.connect(g); g.connect(_tapAC.destination);
      o.start(); o.stop(_tapAC.currentTime+0.05);
    }catch(e){}
  }
  document.addEventListener("click",function(ev){
    try{
      var t=ev.target;
      var b=t&&t.closest?t.closest("button,.cthead,.appcell,.tile,.homenotif"):null;
      if(b&&!(b.disabled)) _tapFeedback();
    }catch(e){}
  },true);

  function api(method, path, body){
    // Marti 7.6. večer: během restartu API po deployi odpovídá starší secondary
    // 404 {"detail":"Not Found"} — přelož na lidskou hlášku místo ticha.
    function mk(t){
      var j=null; try{ j=t?JSON.parse(t):null; }catch(e){ return null; }
      if(j && j.detail==="Not Found") return {ok:false,error:"Server se právě aktualizuje — zkus to za pár vteřin."};
      return j;
    }
    if (canFetch){ try{ var t=B.authedFetch(method,path,body?JSON.stringify(body):""); return Promise.resolve(mk(t));}catch(e){return Promise.resolve(null);} }
    var o={method:method,credentials:"same-origin",headers:{}};
    if(body){o.headers["Content-Type"]="application/json";o.body=JSON.stringify(body);}
    return fetch(path,o).then(function(r){ return r.text().then(mk); }).catch(function(){return null;});
  }
  function bjson(fn, arg){ try{ if(B && typeof B[fn]==="function"){ var t=B[fn](arg); return t?JSON.parse(t):null; } }catch(e){} return null; }
  function doDial(n){ if(B&&typeof B.dialNumber==="function")B.dialNumber(n); else if(B&&typeof B.dial==="function")B.dial(n); }
  function listenState(){ if(!canListen)return null; try{return B.listening()==="1";}catch(e){return null;} }
  function getPrefixes(){ try{ return localStorage.getItem("stg_prefixes") || "STR,EC"; }catch(e){ return "STR,EC"; } }
  function fmtCall(c){ var t={1:"příchozí",2:"odchozí",3:"zmeškaný"}[c.type]||"hovor"; var d=new Date(c.date); var ds=d.toLocaleDateString("cs")+" "+d.toLocaleTimeString("cs",{hour:"2-digit",minute:"2-digit"}); return t+" · "+ds+(c.duration?(" · "+c.duration+" s"):""); }
  function getBadges(){ try{ if(B&&typeof B.appBadges==="function"){ var t=B.appBadges(); return t?JSON.parse(t):null; } }catch(e){} return null; }
  var PHONE_SVG_W=PHONE_SVG.replace(/#22c55e/g,'#ffffff');
  var WA_SVG='<svg width="30" height="30" viewBox="0 0 32 32"><path d="M16 3C9.4 3 4 8.4 4 15c0 2.1.5 4.1 1.5 5.8L4 29l8.4-2.2A12 12 0 1 0 16 3z" fill="#25D366"/><path d="M12.2 9.2c-.25 0-.65.1-1 .5-.35.4-1.3 1.25-1.3 3s1.35 3.5 1.5 3.75c.2.25 2.6 4.15 6.4 5.65 3.15 1.25 3.8 1 4.5.95.7-.05 2.2-.9 2.5-1.75.3-.85.3-1.6.2-1.75-.1-.15-.35-.25-.75-.45-.4-.2-2.2-1.1-2.55-1.2-.35-.15-.6-.2-.85.2-.25.4-.95 1.2-1.15 1.45-.2.25-.45.3-.85.1-.4-.2-1.7-.65-3.2-2-.9-.8-1.55-1.85-1.75-2.25-.2-.4 0-.6.2-.8.2-.2.4-.45.6-.7.2-.25.25-.4.4-.7.1-.25.05-.5-.05-.7-.1-.2-.85-2.1-1.2-2.85-.3-.7-.6-.65-.85-.65z" fill="#fff"/></svg>';
  function avColor(s){ var h=0; for(var i=0;i<(s||"").length;i++) h=(h*31+s.charCodeAt(i))%360; return "hsl("+h+",42%,55%)"; }
  function fmtName(name,pfxCsv){ var pl=(pfxCsv||"").split(",").map(function(x){return x.trim();}); for(var i=0;i<pl.length;i++){ if(pl[i] && (name||"").indexOf(pl[i])===0){ return '<span style="color:#5ee0b7;font-weight:700;">'+esc(pl[i])+'</span>'+esc(name.slice(pl[i].length)); } } return esc(name); }

  // datum: ISO (YYYY-MM-DD) <-> CZ (DD.MM.RRRR); RC modulo 11
  function _czDate(iso){ if(!iso)return ""; var m=/^(\d{4})-(\d{2})-(\d{2})/.exec(iso); return m?(m[3]+"."+m[2]+"."+m[1]):iso; }
  function _isoDate(cz){ cz=(cz||"").trim(); if(!cz)return ""; if(/^\d{4}-\d{2}-\d{2}/.test(cz))return cz; var m=/^(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{2,4})$/.exec(cz); if(!m)return cz; var y=m[3]; if(y.length===2)y=(parseInt(y,10)>30?"19":"20")+y; return y+"-"+("0"+m[2]).slice(-2)+"-"+("0"+m[1]).slice(-2); }
  function _rcValid(rc){ rc=(rc||"").replace(/[\s\/]/g,""); if(!/^\d{9,10}$/.test(rc))return false; if(rc.length===9)return true; return (parseInt(rc.slice(0,10),10)%11===0); }
  function modeChip(){ var c=nativeApp?"native":"web", t=nativeApp?"appka":"prohlížeč"; if(DEV){c="dev";t="DEV";} return '<span class="mode '+c+'">'+t+'</span>'; }
  function topbar(title, withBack, noChip){ var b='<div class="topbar">'; b+='<span class="title">'+esc(title)+'</span>'+(noChip?"":modeChip())+'</div>'; return b; }
  function row(ic, tt, sub, onclick, badge){ var bd=(badge&&badge>0)?'<div class="rbadge">'+(badge>99?"99+":badge)+'</div>':''; var r=el('<div class="row"><div class="ic">'+ic+'</div><div class="tx"><div class="tt">'+esc(tt)+'</div>'+(sub?'<div class="sub">'+esc(sub)+'</div>':'')+'</div>'+bd+'<div class="chev">&#8250;</div></div>'); r.addEventListener("click",onclick); return r; }

  // Znovupoužitelný potvrzovací dialog (využije i docházka). Marti 6.6.2026.
  function confirmDialog(title, msg, okLabel, onOk){
    var ov=el('<div style="position:fixed;inset:0;z-index:300;background:rgba(0,0,0,.62);display:flex;align-items:center;justify-content:center;padding:24px;"></div>');
    var card=el('<div style="background:#161b22;border:1px solid var(--bord);border-radius:14px;padding:20px;max-width:340px;width:100%;box-shadow:0 18px 50px rgba(0,0,0,.5);"></div>');
    card.innerHTML='<div style="font-size:17px;font-weight:700;margin-bottom:8px;">'+esc(title)+'</div>'
      +'<div style="color:#cdd6e2;font-size:14px;line-height:1.55;margin-bottom:18px;">'+esc(msg)+'</div>';
    var row=el('<div class="nactions"></div>');
    var no=el('<button class="ghost sm">Zrušit</button>'); no.addEventListener("click",function(){ try{ov.remove();}catch(e){} });
    var yes=el('<button class="green sm">'+esc(okLabel||"OK")+'</button>'); yes.addEventListener("click",function(){ try{ov.remove();}catch(e){} if(onOk)onOk(); });
    row.appendChild(no); row.appendChild(yes); card.appendChild(row); ov.appendChild(card);
    ov.addEventListener("click",function(e){ if(e.target===ov) ov.remove(); });
    document.body.appendChild(ov);
  }

  // Handoff mobil→PC: ťuk → potvrzovací kartička + zápis do fronty open-on-pc;
  // otevřená STRATEGIE na PC to vyzvedne pollerem a otevře v overlay. Marti 19.6.2026.
  function _opcCard(label){
    if(!document.getElementById("opcConfStyle")){
      var s=document.createElement("style"); s.id="opcConfStyle";
      s.textContent="@keyframes opcPop{from{opacity:0;transform:scale(.86) translateY(10px)}to{opacity:1;transform:none}}"
        +"@keyframes opcSpin{to{transform:rotate(360deg)}}";
      document.head.appendChild(s);
    }
    var old=document.getElementById("opcConfirm"); if(old)old.remove();
    var d=document.createElement("div"); d.id="opcConfirm";
    d.style.cssText="position:fixed;inset:0;z-index:99999;display:flex;align-items:center;justify-content:center;"
      +"background:rgba(6,10,16,.5);backdrop-filter:blur(1px)";
    d.innerHTML='<div style="background:#16202c;border:1px solid #2f3e50;border-radius:18px;padding:24px 28px;'
      +'text-align:center;min-width:230px;animation:opcPop .26s cubic-bezier(.2,.9,.2,1);box-shadow:0 18px 50px rgba(0,0,0,.5)">'
      +'<div id="opcIcon" style="width:62px;height:62px;margin:0 auto 12px;border-radius:50%;'
      +'background:rgba(79,142,247,.16);border:3px solid #4f8ef7;border-top-color:transparent;animation:opcSpin .8s linear infinite"></div>'
      +'<div id="opcTitle" style="font-weight:800;font-size:16px;color:#e8eef5">📲 → 💻 Posílám na počítač…</div>'
      +'<div style="color:#9fb0c4;font-size:13px;margin-top:4px">'+esc(label||"")+'</div></div>';
    document.body.appendChild(d);
    return d;
  }
  function _opcDone(d,ok){
    if(!d)return;
    var ic=d.querySelector("#opcIcon"), tt=d.querySelector("#opcTitle");
    if(ic){ ic.style.animation="none"; ic.style.borderColor=ok?"#34d399":"#ff8a8a";
      ic.style.background=(ok?"rgba(52,211,153,.16)":"rgba(255,138,138,.16)");
      ic.style.display="flex"; ic.style.alignItems="center"; ic.style.justifyContent="center";
      ic.style.fontSize="32px"; ic.textContent=ok?"✓":"✕"; }
    if(tt) tt.textContent=ok?"📲 → 💻 Otevřeno na počítači":"Nepodařilo se odeslat";
    setTimeout(function(){ try{d.remove();}catch(e){} }, ok?1600:2400);
  }
  function openOnPc(url,label){
    if(window._opcLast && (Date.now()-window._opcLast)<1500) return;  // debounce dvojklik
    window._opcLast=Date.now();
    var card=_opcCard(label);
    api("POST","/api/v1/erp/app/open-on-pc",{url:url,label:label}).then(function(j){
      _opcDone(card, !!(j&&j.ok));
      if(!(j&&j.ok)){ setTimeout(function(){ alert((j&&j.error)||"Otevři na PC STRATEGII a zkus znovu."); },300); }
    });
  }

  // Živý indikátor spojení s ERP (tep) — ukazuje, že párování žije a telefon odpovídá.
  function updateLive(){
    var e=document.getElementById("homeLive"); if(!e) return;
    var ls=listenState();
    if(ls===false){ e.innerHTML='🔴 Párování pozastaveno — ťukni na název pro spuštění'; return; }
    if(!_lastOk){ e.innerHTML='🟡 Připojuji se k ERP…'; return; }
    var s=Math.round((Date.now()-_lastOk)/1000);
    if(s<=15) e.innerHTML='🟢 Spojení s ERP <b>živé</b> · odezva před '+s+' s';
    else if(s<=60) e.innerHTML='🟡 Čekám na odezvu ('+s+' s)…';
    else e.innerHTML='🔴 Bez odezvy ('+s+' s) — zkontroluj párování';
  }

  // Karta „Zavolat z ERP" na hlavní obrazovce — když přijde vytočení (do ~2 min),
  // ukáže se i v appce (ne jen jako notifikace). Marti 6.6.2026.
  function showDialCard(){
    var box=document.getElementById("homeDialCard"); if(!box) return;
    var raw=""; try{ if(B&&typeof B.lastDial==="function") raw=B.lastDial()||""; }catch(e){}
    var d=null; try{ if(raw) d=JSON.parse(raw); }catch(e){}
    if(!d||!d.phone){ if(box.innerHTML)box.innerHTML=""; return; }
    if(box.getAttribute("data-ph")===d.phone) return; // už zobrazeno
    box.setAttribute("data-ph", d.phone);
    var who=esc(d.label||d.phone);
    box.innerHTML='<div class="homenotif" style="background:rgba(31,58,46,.94);border-color:#3a7a4a;">'
      +'<div class="ic">📞</div><div style="flex:1;min-width:0;"><div class="nt">Zavolat z ERP</div>'
      +'<div class="nm" style="margin:2px 0 0;">'+who+' · '+esc(d.phone)+'</div></div>'
      +'<button class="green sm" id="dialNowBtn">Vytočit</button></div>';
    var b=document.getElementById("dialNowBtn");
    if(b)b.addEventListener("click",function(){ doDial(d.phone); try{B.clearLastDial();}catch(e){} box.innerHTML=""; box.removeAttribute("data-ph"); });
  }

  // Marti 8.6.: ověření čísla telefonu odchozí SMS na naši SIM — nejsilnější
  // důkaz (caller-ID nelze ošidit). Karta visí, dokud zařízení nemá ověřeno.
  function _phoneVerifyCard(dev){
    var c=document.getElementById("homeVerify"); if(!c) return;
    c.innerHTML="";
    var card=el('<div class="doch-pulse" style="margin:10px 0;background:rgba(224,176,112,.10);border:1px solid #6e5326;border-radius:12px;padding:12px;"></div>');
    card.appendChild(el('<div style="font-weight:700;">📨 Ověř číslo tohoto telefonu</div>'));
    card.appendChild(el('<div class="hint" style="margin-top:4px;">Odešleš jednu předvyplněnou SMS na firemní číslo — tím se telefon oficiálně ověří. Nic nepíšeš, jen Odeslat.</div>'));
    var b=el('<button class="green full" style="margin-top:8px;">📨 Odeslat ověřovací SMS</button>');
    var st=el('<div class="hint" style="margin-top:6px;"></div>');
    b.addEventListener("click",function(){
      b.disabled=true; st.textContent="⏳ Připravuji…";
      api("POST","/api/v1/erp/app/phone-verify/start",{device_id:dev}).then(function(j){
        if(!(j&&j.ok)){ b.disabled=false; st.textContent="✗ "+((j&&j.error)||"Nepodařilo se."); return; }
        // Marti 8.6.: appka zkusí poslat SMS sama (B.sendSms), ALE novější
        // Androidy (Samsung S24) blokují SEND_SMS pro ne-výchozí SMS appku →
        // tiché selhání. Proto VŽDY otevřeme i Zprávy s předvyplněným textem
        // (Šárčin telefon) — uživatel jen klikne Odeslat. Funguje na 100 %.
        var sent=false;
        if(B && typeof B.sendSms==="function"){
          var r=""; try{ r=B.sendSms(j.send_to, j.body||j.token); }catch(e){ r="0"; }
          sent=(r==="1");
        }
        if(!sent){
          // Otevři Zprávy s předvyplněným tělem — spolehlivá cesta všude.
          openApp("sms:"+j.send_to+"?body="+encodeURIComponent(j.body||j.token));
        }
        st.textContent=sent?"📨 SMS odeslána — čekám na ověření…":"📨 V aplikaci Zprávy klikni Odeslat a vrať se — čekám…";
        var tries=0;
        var iv=setInterval(function(){
          if(!document.body.contains(card)){ clearInterval(iv); return; }
          if(++tries>45){ clearInterval(iv); b.disabled=false; st.textContent="⏳ SMS zatím nedorazila — zkus to znovu."; return; }
          api("GET","/api/v1/erp/app/phone-verify/status?token="+encodeURIComponent(j.token),"").then(function(r){
            if(r&&r.verified){
              clearInterval(iv);
              card.classList.remove("doch-pulse");
              card.innerHTML='<div style="font-weight:700;">✅ Číslo ověřeno: '+esc(r.phone_number||"")+'</div><div class="hint" style="margin-top:4px;">Telefon je oficiálně spárovaný.</div>';
            }
          });
        },4000);
      });
    });
    card.appendChild(b); card.appendChild(st);
    c.appendChild(card);
  }

  // ───── DOMŮ (pozadí = fotka Marti-AI) ─────
