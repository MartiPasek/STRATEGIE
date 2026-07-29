  function vyroba_hub(){
    app.innerHTML=topbar("🏭 Výroba — pracovní plocha", true);
    app.appendChild(el('<div class="hint" style="margin:6px 6px 2px;line-height:1.6;">Tvoje pracovní plocha, Míšo — celá výroba na jednom místě. Bloky: plánování a vytížení, operativa výroby, lidé a docházka. S Claudem‑27 si ji můžeš upravovat.</div>'));
    function s(t){ app.appendChild(el('<div style="margin:14px 6px 6px;font-size:12px;font-weight:700;letter-spacing:.5px;color:#7c8cdb;">'+t+'</div>')); }
    s("PLÁNOVÁNÍ & VYTÍŽENÍ");
    var g1=el('<div class="appgrid"></div>');
    g1.appendChild(appCell("📊","FLOW — časová osa",0,function(){openInApp("/flow");}));
    g1.appendChild(appCell("📈","Vytížení",0,function(){openInApp("/vytizeni");}));
    app.appendChild(g1);
    s("OPERATIVA VÝROBY");
    var g2=el('<div class="appgrid"></div>');
    g2.appendChild(appCell("👷","Výroba — konzole",0,function(){openVyroba("makam");}));
    g2.appendChild(appCell("🧾","Zakázky",0,function(){openVyroba("zakazky");}));
    g2.appendChild(appCell("👔","VP",0,function(){openVyroba("vp");}));
    g2.appendChild(appCell("🧪","Zkušebna",0,function(){openVyroba("zkusebna");}));
    g2.appendChild(appCell("🔧","Příprava",0,function(){openVyroba("priprava");}));
    g2.appendChild(appCell("🚚","Odvozy",0,function(){openVyroba("odvozy");}));
    g2.appendChild(appCell("🛒","Nákup materiálu",0,function(){openVyroba("nakup");}));
    g2.appendChild(appCell("📷","Fotky",0,function(){openInApp("/foto");}));
    app.appendChild(g2);
    s("LIDÉ & DOCHÁZKA");
    var g3=el('<div class="appgrid"></div>');
    g3.appendChild(appCell("👀","Kdo kde dnes",0,function(){go("kdekdo");}));
    g3.appendChild(appCell("🏖️","Plán absencí",0,function(){openInApp("/absence-plan");}));
    app.appendChild(g3);
  }
  function vyroba(){
    if(window._vyInitView){ _vyView=window._vyInitView; window._vyInitView=null; }
    app.innerHTML=topbar(_vyIsGroup()?(((_vyCtx.icon||"👥").split("|")[0])+" "+(_vyCtx.name||"Skupina")):"🏭 Výroba", true, true);
    var _tb=app.querySelector('.topbar'); if(_tb) _tb.style.paddingTop="12px";
    var wrap=el('<div style="display:flex;gap:8px;height:calc(100vh - 165px);padding:4px 2px 0;"></div>');
    var left=el('<div style="flex:1;min-width:0;display:flex;flex-direction:column;"></div>');
    var s=el('<input id="vysearch" placeholder="🔍 Hledat…" autocomplete="off" style="border:1px solid var(--blue);background:#0d1828;box-shadow:0 0 0 2px rgba(79,142,247,.18);font-weight:600;margin-bottom:8px;">');
    s.addEventListener("input",vyRender);
    var lw=el('<div class="list vy-list" style="flex:1;overflow:auto;padding:0 6px;"><ul id="vylist"><li style="color:var(--mut);border:none;">Načítám…</li></ul></div>');
    left.appendChild(s); left.appendChild(lw);
    var rail=el('<div id="vyrail" style="width:64px;flex:none;overflow-y:auto;display:flex;flex-direction:column;gap:5px;padding:1px;"></div>');
    if(_vyIsGroup()){ rail.appendChild(vyBtn({k:"tym",ic:"👥",l:"Tým"})); }
    VY_TOP.forEach(function(v){ rail.appendChild(vyBtn(v)); });
    rail.appendChild(el('<div style="flex:1 1 auto;min-height:10px;"></div>'));
    if(!_vyIsGroup()){ VY_BOT.forEach(function(v){ rail.appendChild(vyBtn(v)); }); }
    wrap.appendChild(left); wrap.appendChild(rail); app.appendChild(wrap);
    vyPaintRail(); vyLoad(); vyCounts();
  }
  function vyPaintRail(){ var r=document.getElementById("vyrail"); if(!r)return;
    Array.prototype.forEach.call(r.querySelectorAll("button[data-k]"),function(b){ var on=b.getAttribute("data-k")===_vyView;
      b.style.background=on?"var(--green)":"transparent"; b.style.color=on?"#04150e":"var(--mut)";
      b.style.borderColor=on?"var(--green)":"var(--bord)"; b.style.fontWeight=on?"700":"400"; });
  }
  function vyBezPrace(lidi){ return (lidi||[]).filter(function(pp){ return !(pp.prirazeni&&pp.prirazeni.length) && !((pp.plan||[]).some(function(o){ return !o.hidden; })); }); }
  function vySetBadge(k,n){ var r=document.getElementById("vyrail"); if(!r)return;
    var btn=r.querySelector('button[data-k="'+k+'"]'); if(!btn)return;
    var bg=btn.querySelector('[data-badge]'); if(bg){ bg.textContent=n; bg.style.display=n>0?"block":"none";
      bg.classList.toggle("gr", k==="makam"||k==="relaxuji"||k==="tym");
      bg.classList.toggle("pulse", (k==="potrebuji"||k==="cekam") && n>0); }
    if(btn.getAttribute("data-onlyif")==="1"){ btn.style.display=n>0?"flex":"none"; }
  }
  function vyCounts(){
    function fromLidi(){
      vySetBadge("makam", _vyPeople.filter(function(p){return p.stav==="makam";}).length);
      vySetBadge("relaxuji", _vyPeople.filter(function(p){return p.stav==="pauza";}).length);
      vySetBadge("chybi", _vyPeople.filter(function(p){return p.stav==="chybi";}).length);
      vySetBadge("jedu", _vyPeople.filter(function(p){return p.stav==="jedu";}).length);
      vySetBadge("cekam", _vyPeople.filter(function(p){return p.stav==="cekam";}).length);
      vySetBadge("mimo_plan", _vyPeople.filter(function(p){return p.stav==="mimo_plan";}).length);
      vySetBadge("tym", _vyPeople.length);
    }
    if(_vyIsGroup()){
      if(_vyPeople.length){ fromLidi(); }
      else { api("GET","/api/v1/erp/app/skupina/lidi?gid="+_vyCtx.gid,"").then(function(j){ if(j&&j.ok)_vyPeople=j.lidi||[]; fromLidi(); }); }
      vySetBadge("potrebuji",0); vySetBadge("informuji",0); vySetBadge("finisuji",0);
      return;
    }
    if(_vyPeople.length){ fromLidi(); }
    else { api("GET","/api/v1/erp/app/vyroba/lidi","").then(function(j){ if(j&&j.ok)_vyPeople=j.lidi||[]; fromLidi(); }); }
    api("GET","/api/v1/erp/app/vyroba/zpravy","").then(function(j){ var z=(j&&j.zpravy)||[];
      vySetBadge("potrebuji", z.filter(function(m){return (m.typ||"pozadavek")==="pozadavek";}).length);
      vySetBadge("informuji", z.filter(function(m){return m.typ==="info";}).length); });
    api("GET","/api/v1/erp/app/vyroba/zakazky-lide","").then(function(j){ vySetBadge("zakazky", ((j&&j.zakazky)||[]).length); });
    api("GET","/api/v1/erp/app/vyroba/odvozy","").then(function(j){ vySetBadge("odvozy", ((j&&j.odvozy)||[]).length); });
  }
  function vyLoad(){
    var ul=document.getElementById("vylist"); if(ul)ul.innerHTML='<li style="color:var(--mut);border:none;">Načítám…</li>';
    var v=_vyView;
    if(!VY_READY[v]){ _vyData={ok:true,todo:true}; vyRender(); return; }
    if(_vyIsGroup()){
      if(v==="potrebuji"||v==="informuji"||v==="finisuji"){ _vyData={ok:true,zpravy:[]}; vyRender(); return; }
      api("GET","/api/v1/erp/app/skupina/lidi?gid="+_vyCtx.gid,"").then(function(j){ if(j&&j.ok)_vyPeople=j.lidi||[]; _vyLidiSig=_vySig(_vyPeople); _vyData=j; vyRender(); vyCounts(); });
      return;
    }
    if(v==="zakazky"){
      if(!_vyPeople.length) api("GET","/api/v1/erp/app/vyroba/lidi","").then(function(jp){ if(jp&&jp.ok)_vyPeople=jp.lidi||[]; });
      api("GET","/api/v1/erp/app/vyroba/zakazky-lide","").then(function(j){ _vyData=j; vyRender(); });
    } else if(v==="odvozy"){
      api("GET","/api/v1/erp/app/vyroba/odvozy","").then(function(j){ _vyData=j; vyRender(); });
    } else if(v==="potrebuji"||v==="informuji"||v==="finisuji"){
      api("GET","/api/v1/erp/app/vyroba/zpravy","").then(function(j){ _vyData=j; vyRender(); });
    } else {
      api("GET","/api/v1/erp/app/vyroba/lidi","").then(function(j){ if(j&&j.ok)_vyPeople=j.lidi||[]; _vyLidiSig=_vySig(_vyPeople); _vyData=j; vyRender(); vyCounts(); });
    }
  }
  // Živý refresh konzole (Výroba i skupiny) — voláno z existujících událostí
  // (foreground/focus + heartbeat pollNotifs). Re-render jen při změně statusů.
  function vyRefreshLive(){
    if(stack[stack.length-1]!=="vyroba") return;
    if(["zakazky","odvozy","potrebuji","informuji","finisuji"].indexOf(_vyView)>=0) return;
    var url=_vyIsGroup()?("/api/v1/erp/app/skupina/lidi?gid="+_vyCtx.gid):"/api/v1/erp/app/vyroba/lidi";
    api("GET",url,"").then(function(j){
      if(!j||!j.ok) return;
      var sig=_vySig(j.lidi);
      if(sig===_vyLidiSig) return;          // beze změny → neruš
      _vyLidiSig=sig; _vyPeople=j.lidi||[]; _vyData=j; vyRender(); vyCounts();
    }).catch(function(){});
  }
  function vyRender(){
    var ul=document.getElementById("vylist"); if(!ul)return;
    var f=deacc(((document.getElementById("vysearch")||{}).value||"").trim()), j=_vyData;
    if(j&&j.todo){ ul.innerHTML='<li style="color:var(--mut);border:none;line-height:1.5;">Sekce <b>'+esc(_vyView)+'</b> zatím čeká na zadání — řekni mi, co tu má být a napojím ji.</li>'; return; }
    if(!j||!j.ok){ ul.innerHTML='<li style="color:var(--mut);border:none;">'+((j&&j.error)==="forbidden"?"Jen pro vedoucího výroby a jeho zástupce.":"Nepodařilo se načíst.")+'</li>'; return; }
    ul.innerHTML="";
    if(_vyView==="zakazky"){
      var zak=(j.zakazky||[]).filter(function(x){ return !f||deacc(x.cislo+" "+(x.nazev||"")).indexOf(f)>=0; });
      if(!zak.length){ ul.innerHTML='<li style="color:var(--mut);border:none;">Nic.</li>'; return; }
      zak.forEach(function(z){ ul.appendChild(vyZakLi(z)); });
    } else if(_vyView==="odvozy"){
      var odv=(j.odvozy||[]).filter(function(o){ return !f||deacc((o.cislo||"")+" "+(o.nazev||"")+" "+(o.adresa||"")).indexOf(f)>=0; });
      if(!odv.length){ ul.innerHTML='<li style="color:var(--mut);border:none;">Žádné odvozy. Spusť ⚙ sync odvozů.</li>'; return; }
      odv.forEach(function(o){ ul.appendChild(vyOdvozLi(o)); });
    } else if(_vyView==="potrebuji"||_vyView==="informuji"||_vyView==="finisuji"){
      var want=(_vyView==="informuji"?"info":(_vyView==="finisuji"?"finish":"pozadavek"));
      var zpr=(j.zpravy||[]).filter(function(m){ return (m.typ||"pozadavek")===want && (!f||deacc((m.jmeno||"")+" "+(m.text||"")).indexOf(f)>=0); });
      if(!zpr.length){ ul.innerHTML='<li style="color:var(--mut);border:none;">'+({potrebuji:"Nikdo nic nepotřebuje. 👍",informuji:"Žádné informace.",finisuji:"Nikdo zatím nefinišuje."}[_vyView])+'</li>'; return; }
      zpr.forEach(function(m){ ul.appendChild(vyZpravaLi(m)); });
    } else {
      var lidi=(j.lidi||[]);
      var STMAP={makam:"makam",relaxuji:"pauza",chybi:"chybi",jedu:"jedu",mimo_plan:"mimo_plan"};
      if(_vyView==="cekam"){ lidi=lidi.filter(function(pp){ return pp.stav==="cekam"; }); }
      else if(STMAP[_vyView]){ lidi=lidi.filter(function(pp){ return pp.stav===STMAP[_vyView]; }); }
      lidi=lidi.filter(function(x){ return !f||deacc(x.jmeno).indexOf(f)>=0; });
      if(!lidi.length){
        var em={cekam:"Nikdo nečeká na práci. 👍",mimo_plan:"Dnes nikdo mimo plán.",makam:"Nikdo zrovna nemaká.",relaxuji:"Nikdo není na pauze.",chybi:"Nikdo nechybí. 👍",jedu:"Nikdo není na cestě."};
        ul.innerHTML='<li style="color:var(--mut);border:none;">'+(em[_vyView]||"Nikdo.")+'</li>'; return;
      }
      lidi.forEach(function(pp){ ul.appendChild(vyPersonLi(pp)); });
    }
  }
  function vyAcc(ul,li,exp){
    if(li.classList.contains("open")){ li.classList.remove("open"); exp.style.display="none"; return; }
    ul.querySelectorAll("li.ct").forEach(function(o){ o.classList.remove("open"); var x=o.querySelector(".ctexp"); if(x)x.style.display="none"; });
    exp.style.display="block"; li.classList.add("open"); li.scrollIntoView({block:"nearest",behavior:"smooth"});
  }
  function vyInitial(nm){ return esc(((nm||"?").replace(/[^A-Za-zÀ-ž]/g,"").charAt(0)||"?").toUpperCase()); }
  function vyOverlay(uid,cislo,patch){ var b={user_id:uid,cislo_zakazky:cislo}; for(var k in patch)b[k]=patch[k];
    api("POST","/api/v1/erp/app/vyroba/plan-overlay",b).then(function(r){ if(r&&r.ok) vyLoad(); }); }
  function vyResolve(id){ api("POST","/api/v1/erp/app/vyroba/zprava/"+id+"/resolve",{}).then(function(r){ if(r&&r.ok){ vyLoad(); vyCounts(); } }); }
  // Marti 8.6.: diktování do pole přes nativní záznamník (file-capture) → Whisper.
  // Marti 8.6.: diktování ve Výrobě 1:1 jako velký Marti chat — PODRŽ a mluv,
  // pusť = přepis. Pointer capture (drží i když ujede prst) + detekce formátu
  // (webm/opus) + requestData flush před stop (jinak Chrome zapíše jen header).
  function _micRelease(){ try{ if(window.__micStream){ window.__micStream.getTracks().forEach(function(t){t.stop();}); window.__micStream=null; } }catch(e){} }
  function _micMime(){ var c=["audio/webm;codecs=opus","audio/webm","audio/ogg;codecs=opus","audio/mp4"]; if(typeof MediaRecorder==="undefined")return ""; for(var i=0;i<c.length;i++){ if(MediaRecorder.isTypeSupported&&MediaRecorder.isTypeSupported(c[i]))return c[i]; } return ""; }
  function _micExt(m){ if(!m)return "webm"; if(m.indexOf("audio/mp4")===0)return "m4a"; if(m.indexOf("audio/ogg")===0)return "ogg"; return "webm"; }
  function vyMic(ta, st){
    var btn=el('<button class="ghost" style="width:64px;font-size:19px;border-color:var(--blue);color:var(--blue);margin:0;flex:none;touch-action:none;-webkit-user-select:none;user-select:none;" title="Podrž a mluv">🎙</button>');
    var state="idle";  // idle | starting | recording
    var mr=null, chunks=[], pid=null;
    function reset(){ state="idle"; btn.textContent="🎙"; btn.style.background=""; }
    function doTranscribe(blob){
      if(blob.size<300){ if(st)st.textContent="✗ Moc krátké — podrž 🎙 a mluv."; return; }
      if(st)st.textContent="💭 Přepisuji…"; btn.disabled=true;
      var fr=new FileReader();
      fr.onload=function(){
        api("POST","/api/v1/erp/app/transcribe",{audio_b64:String(fr.result).split(",")[1],mime:blob.type,filename:"mobil-audio."+_micExt(blob.type)}).then(function(r){
          btn.disabled=false;
          if(r&&r.ok&&r.text){ ta.value=(ta.value?(ta.value.trim()+" "):"")+r.text; if(st)st.textContent="✅ Přepsáno"; try{ta.focus();}catch(e){} }
          else { if(st)st.textContent="✗ "+((r&&r.error)||"nepřepsáno"); }
        });
      };
      fr.readAsDataURL(blob);
    }
    function stopRec(){
      if(state==="starting"){ state="aborting"; return; }   // pustil během getUserMedia
      if(state!=="recording"||!mr){ return; }
      reset();
      try{ if(mr.state==="recording") mr.requestData(); }catch(e){}
      try{ mr.stop(); }catch(e){ _micRelease(); }
    }
    function startRec(){
      if(state!=="idle") return;
      if(!(navigator.mediaDevices&&navigator.mediaDevices.getUserMedia&&window.MediaRecorder)){ if(st)st.textContent="🎙 Mikrofon tu není dostupný."; return; }
      state="starting"; _micRelease(); btn.textContent="⏺"; btn.style.background="rgba(79,142,247,.18)"; if(st)st.textContent="🎙 …";
      navigator.mediaDevices.getUserMedia({audio:true}).then(function(s){
        window.__micStream=s;
        if(state==="aborting"){ _micRelease(); reset(); if(st)st.textContent=""; return; }
        var mime=_micMime(); var opts=mime?{mimeType:mime}:{};
        try{ mr=new MediaRecorder(s,opts); }catch(e){ try{ mr=new MediaRecorder(s); }catch(e2){ _micRelease(); reset(); if(st)st.textContent="🎙 Záznam nejde."; return; } }
        chunks=[];
        mr.ondataavailable=function(e){ if(e.data&&e.data.size)chunks.push(e.data); };
        mr.onstop=function(){ var raw=(mr&&mr.mimeType)||mime||"audio/webm"; var m=raw.split(";")[0].trim()||"audio/webm"; var blob=new Blob(chunks,{type:m}); _micRelease(); mr=null; doTranscribe(blob); };
        mr.start(); state="recording"; btn.textContent="⏺"; if(st)st.textContent="🔴 Mluv… (pusť pro přepis)";
      }).catch(function(err){ _micRelease(); reset(); if(st)st.textContent="🎙 Mikrofon ["+((err&&(err.name||err.message))||"?")+"] — podrž znovu."; });
    }
    btn.addEventListener("pointerdown",function(ev){ ev.preventDefault(); pid=ev.pointerId; try{btn.setPointerCapture(pid);}catch(e){} startRec(); });
    btn.addEventListener("pointerup",function(ev){ ev.preventDefault(); try{btn.releasePointerCapture(pid);}catch(e){} stopRec(); });
    btn.addEventListener("pointercancel",function(){ stopRec(); });
    return btn;
  }
  function vyOdvozLi(o){
    var ul=document.getElementById("vylist");
    var li=document.createElement("li"); li.className="ct"; li.style.padding="0"; li.style.borderBottom="none";
    if(o.minulost) li.style.opacity="0.55";
    var sub=(o.nazev||"")+(o.pozn_count?(" · 💬 "+o.pozn_count):"");
    var head=el('<div class="cthead"><div class="cav" style="background:'+avColor(o.cislo||"?")+';font-size:16px;">🚚</div><div style="flex:1;min-width:0;"><div class="ctname">'+esc(o.datum||"")+' · '+esc(o.cislo||"")+'</div><div class="ctnum">'+esc(sub)+'</div></div></div>');
    var exp=el('<div class="ctexp" style="display:none;"></div>');
    head.addEventListener("click",function(){ vyAcc(ul,li,exp); if(li.classList.contains("open")) vyFillOdvoz(exp,o); });
    li.appendChild(head); li.appendChild(exp); return li;
  }
  function vyFillOdvoz(exp,o){
    exp.innerHTML="";
    if(o.adresa) exp.appendChild(el('<div style="padding:4px;font-size:14px;white-space:normal;">📍 '+esc(o.adresa)+'</div>'));
    if(o.poznamka) exp.appendChild(el('<div class="hint" style="margin:2px 4px;white-space:normal;">📝 '+esc(o.poznamka)+'</div>'));
    var rwrap=el('<div style="margin:4px 0;"></div>'); exp.appendChild(rwrap);
    api("GET","/api/v1/erp/app/vyroba/odvoz-pozn?ext_id="+o.ext_id,"").then(function(j){
      ((j&&j.pozn)||[]).forEach(function(p){
        rwrap.appendChild(el('<div style="padding:5px 4px;border-top:1px solid var(--bord);font-size:13px;white-space:normal;"><b style="color:#ffd9a8;">'+(p.oddeleni?esc(p.oddeleni):"💬")+'</b> '+esc(p.text||"")+' <span class="hint">· '+esc(p.kdo||"")+' '+esc(p.kdy||"")+'</span></div>'));
      });
    });
    var sel={d:null};
    var brow=el('<div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:8px;"></div>');
    ["Nákup","VP","Zkušebna","Výroba"].forEach(function(d){
      var b=el('<button class="ghost" style="padding:6px 11px;font-size:13px;margin:0;">'+d+'</button>');
      b.addEventListener("click",function(){ sel.d=(sel.d===d?null:d);
        Array.prototype.forEach.call(brow.children,function(x){ x.style.outline=""; x.style.color="var(--mut)"; });
        if(sel.d){ b.style.outline="2px solid var(--green)"; b.style.color="var(--tx)"; } });
      brow.appendChild(b);
    });
    exp.appendChild(brow);
    var ta=el('<textarea rows="2" placeholder="Reakce / poznámka k odvozu… (nebo nadiktuj 🎙)" style="background:#0f1620;border:1px solid #2a3a4d;border-radius:10px;padding:10px;color:var(--tx);font-size:14px;font-family:inherit;flex:1;"></textarea>');
    var st=el('<div class="hint" style="margin-top:4px;"></div>');
    var trow=el('<div style="display:flex;gap:6px;align-items:stretch;margin-top:8px;"></div>');
    trow.appendChild(ta); trow.appendChild(vyMic(ta,st));
    var send=el('<button class="green full" style="margin-top:6px;">💬 Odeslat reakci</button>');
    send.addEventListener("click",function(){ var t=(ta.value||"").trim(); if(!t&&!sel.d){ ta.focus(); return; } send.disabled=true;
      api("POST","/api/v1/erp/app/vyroba/odvoz-pozn",{odvoz_ext_id:o.ext_id,cislo_zakazky:o.cislo,oddeleni:sel.d,text:t}).then(function(r){ if(r&&r.ok){ vyLoad(); vyCounts(); } else { send.disabled=false; alert("Chyba: "+((r&&r.error)||"?")); } }); });
    exp.appendChild(trow); exp.appendChild(st); exp.appendChild(send);
  }
  function vyZpravaLi(m){
    var ul=document.getElementById("vylist");
    var li=document.createElement("li"); li.className="ct"; li.style.padding="0"; li.style.borderBottom="none";
    var ic=(_vyView==="informuji"?"💡":(_vyView==="finisuji"?"🏁":"🙋"));
    var sub=(m.kdy||"")+(m.eta_min?(" · za ~"+m.eta_min+" min"):"")+(m.cislo?(" · "+m.cislo):"");
    var head=el('<div class="cthead"><div class="cav" style="background:'+avColor(m.jmeno||"?")+'">'+vyInitial(m.jmeno||"?")+'</div><div style="flex:1;min-width:0;"><div class="ctname">'+ic+' '+esc(m.jmeno||"")+'</div><div class="ctnum">'+esc(sub)+'</div></div></div>');
    var exp=el('<div class="ctexp" style="display:none;"></div>');
    head.addEventListener("click",function(){ vyAcc(ul,li,exp); if(li.classList.contains("open")) vyFillZprava(exp,m); });
    li.appendChild(head); li.appendChild(exp); return li;
  }
  function vyFillZprava(exp,m){
    exp.innerHTML="";
    exp.appendChild(el('<div style="padding:6px 4px 10px;white-space:normal;font-size:15px;">'+esc(m.text||"")+'</div>'));
    if(_vyView==="potrebuji"){
      var ta=el('<textarea rows="6" placeholder="Napiš odpověď…" style="width:100%;min-height:40vh;background:#0f1620;border:1px solid var(--green);border-radius:10px;padding:11px;color:var(--tx);font-size:15px;font-family:inherit;"></textarea>');
      var send=el('<button class="green full" style="margin-top:8px;">🚀 Odeslat odpověď</button>');
      send.addEventListener("click",function(){ var t=(ta.value||"").trim(); if(!t){ta.focus();return;} send.disabled=true;
        api("POST","/api/v1/erp/app/vyroba/odpoved",{user_id:m.user_id,text:t,zprava_id:m.id}).then(function(r){ if(r&&r.ok){ vyLoad(); vyCounts(); } else { send.disabled=false; alert("Chyba: "+((r&&r.error)||"?")); } }); });
      var done=el('<button class="ghost full" style="margin-top:6px;">✅ Vyřešeno (bez odpovědi)</button>');
      done.addEventListener("click",function(){ vyResolve(m.id); });
      var st=el('<div class="hint" style="margin-top:4px;"></div>');
      var mrow=el('<div style="display:flex;gap:8px;align-items:center;margin-top:6px;"></div>');
      mrow.appendChild(vyMic(ta,st)); mrow.appendChild(el('<span class="hint">…nebo to nadiktuj</span>'));
      exp.appendChild(ta); exp.appendChild(mrow); exp.appendChild(st); exp.appendChild(send); exp.appendChild(done);
    } else if(_vyView==="informuji"){
      var ok=el('<button class="green full" style="margin-top:4px;">✅ Potvrdit (přečteno)</button>');
      ok.addEventListener("click",function(){ vyResolve(m.id); });
      var td=el('<button class="ghost full" style="margin-top:6px;">📝 Zapsat do TODO</button>');
      td.addEventListener("click",function(){ var t=prompt("Úkol do TODO:", m.text||""); if(t){ api("POST","/api/v1/erp/app/vyroba/todo",{text:t,ref_zakazka:(m.cislo||null)}).then(function(r){ if(r&&r.ok) vyResolve(m.id); }); } });
      exp.appendChild(ok); exp.appendChild(td);
    } else {
      var ok2=el('<button class="green full" style="margin-top:4px;">✅ Beru na vědomí</button>');
      ok2.addEventListener("click",function(){ vyResolve(m.id); });
      exp.appendChild(ok2);
    }
  }
  function vyPersonLi(pp){
    var ul=document.getElementById("vylist");
    var li=document.createElement("li"); li.className="ct"; li.style.padding="0"; li.style.borderBottom="none";
    var nm=pp.jmeno||"?";
    var cnt=((pp.plan||[]).filter(function(o){return !o.hidden;}).length)+((pp.prirazeni||[]).length);
    var sub=cnt+' zakázek';
    if(_vyIsGroup()){
      var GSM={makam:"🟢 maká",pauza:"☕ pauza",jedu:"🚗 na cestě",chybi:"🫥 nepřihlášen",pryc:"🌙 pryč",byl:"✓ byl",cekam:"🥱 bez zakázky",mimo_plan:"🌴 mimo plán"};
      sub=GSM[pp.stav]||"—";
      if(pp.stav==="makam"&&pp.stav_zak) sub='🧾 '+esc(pp.stav_zak);
      else if((pp.stav==="pauza"||pp.stav==="jedu")&&pp.stav_pozn) sub=(GSM[pp.stav]||"").split(" ")[0]+' '+esc(pp.stav_pozn);
    }
    else if(_vyView==="makam"){ sub=pp.stav_zak?('🧾 '+esc(pp.stav_zak)):'🟢 maká'; }
    else if(_vyView==="relaxuji"){ sub='☕ '+esc(pp.stav_pozn||'pauza'); }
    else if(_vyView==="jedu"){ sub='🚗 '+esc(pp.stav_pozn||'na cestě'); }
    else if(_vyView==="chybi"){ sub='🫥 '+(pp.stav_pozn?esc(pp.stav_pozn):'nepřihlášen'); }
    var nmDisp=esc(nm);
    if(_vyIsGroup()){ if(pp.role==="lead") nmDisp="⭐ "+nmDisp; else if(pp.role==="deputy") nmDisp="🎖 "+nmDisp; }
    if(pp.ec_old) nmDisp+=' <span title="Píchnutý ve starém systému (Centrála)" style="color:#f0a93b;">🕰️</span>';  // Marti 19.6.
    var head=el('<div class="cthead"><div class="cav" style="background:'+avColor(nm)+'">'+vyInitial(nm)+'</div><div style="flex:1;min-width:0;"><div class="ctname">'+nmDisp+'</div><div class="ctnum">'+sub+'</div></div></div>');
    var exp=el('<div class="ctexp" style="display:none;"></div>');
    head.addEventListener("click",function(){ vyAcc(ul,li,exp); if(li.classList.contains("open")) vyFillPerson(exp,pp); });
    li.appendChild(head); li.appendChild(exp); return li;
  }
  function vyFillPerson(exp,pp){
    exp.innerHTML="";
    if(_vyIsGroup()){
      // Marti 19.6.: poznámka (důvod pauzy/cesty) ANO; druhé číslo zakázky pryč → ikonka oka = „Dnešek" osoby.
      var _note=pp.stav_pozn||"";
      if(_note) exp.appendChild(el('<div style="padding:8px 4px;color:var(--mut);">📝 '+esc(_note)+'</div>'));
      var _eye=el('<button class="ghost full" style="margin:6px 0 2px;display:flex;align-items:center;justify-content:center;gap:8px;"><span style="font-size:19px;">👁</span> Zobrazit dnešek</button>');
      _eye.addEventListener("click",function(){ openPersDnesek(pp.user_id, pp.jmeno||""); });
      exp.appendChild(_eye);
      return;
    }
    (pp.plan||[]).forEach(function(o){
      var row=el('<div style="padding:8px 4px;border-top:1px solid var(--bord);"></div>');
      row.appendChild(el('<div style="font-weight:600;color:'+(o.done?'#6b7a8a':'#cfe3ff')+';'+(o.done?'text-decoration:line-through;':'')+'">📋 '+esc(o.cislo)+(o.nazev?(' — '+esc(o.nazev)):'')+(o.hidden?' · 🙈 skryté':'')+(o.hod!=null?(' · '+o.hod+'h'):'')+'</div>'));
      if(o.poznamka) row.appendChild(el('<div class="hint" style="margin:2px 0;">📝 '+esc(o.poznamka)+'</div>'));
      var br=el('<div style="display:flex;gap:6px;margin-top:5px;flex-wrap:wrap;"></div>');
      var bD=el('<button class="ghost" style="padding:4px 9px;font-size:12px;margin:0;">'+(o.done?'↩ vrátit':'✅ hotovo')+'</button>');
      bD.addEventListener("click",function(){ vyOverlay(pp.user_id,o.cislo,{done:!o.done}); });
      var bH=el('<button class="ghost" style="padding:4px 9px;font-size:12px;margin:0;">'+(o.hidden?'👁 zobrazit':'🙈 skrýt')+'</button>');
      bH.addEventListener("click",function(){ vyOverlay(pp.user_id,o.cislo,{hidden:!o.hidden}); });
      var bN=el('<button class="ghost" style="padding:4px 9px;font-size:12px;margin:0;">📝 poznámka</button>');
      bN.addEventListener("click",function(){ var t=prompt("Poznámka k "+o.cislo+":",o.poznamka||""); if(t!=null) vyOverlay(pp.user_id,o.cislo,{poznamka:t}); });
      br.appendChild(bD); br.appendChild(bH); br.appendChild(bN); row.appendChild(br); exp.appendChild(row);
    });
    (pp.prirazeni||[]).forEach(function(a){
      var row=el('<div style="padding:8px 4px;border-top:1px solid var(--bord);"></div>');
      row.appendChild(el('<div style="font-weight:600;color:#ffd9a8;">📌 '+esc(a.cislo)+(a.nazev?(' — '+esc(a.nazev)):'')+'</div>'));
      if(a.pokyn) row.appendChild(el('<div class="hint" style="margin:2px 0;">📋 '+esc(a.pokyn)+'</div>'));
      if(a.kdy_ozvat) row.appendChild(el('<div class="hint" style="margin:1px 0;color:#f59e0b;">⏰ '+esc(a.kdy_ozvat)+'</div>'));
      var bx=el('<button class="ghost" style="padding:4px 9px;font-size:12px;margin-top:4px;color:#ef4444;border-color:#ef4444;">✕ zrušit</button>');
      bx.addEventListener("click",function(){ api("POST","/api/v1/erp/app/vyroba/prirazeni/"+a.id+"/zrusit",{}).then(function(r){ if(r&&r.ok) vyLoad(); }); });
      row.appendChild(bx); exp.appendChild(row);
    });
    var add=el('<button class="green full" style="margin-top:8px;">➕ Přidat zakázku</button>'), wrap=el('<div></div>');
    add.addEventListener("click",function(){ if(wrap.firstChild){wrap.innerHTML="";return;} wrap.appendChild(vyOrderBox(pp)); });
    exp.appendChild(add); exp.appendChild(wrap);
  }
  function vyOrderBox(pp){
    var box=el('<div style="margin-top:8px;padding:10px;background:#0f1620;border:1px solid var(--bord);border-radius:10px;"></div>');
    box.appendChild(el('<div class="hint">Najdi zakázku:</div>'));
    var si=el('<input placeholder="🔍 VR106… / název">'), res=el('<div style="margin-top:6px;"></div>'), chosen={c:null};
    var pokyn=el('<textarea rows="2" placeholder="Pokyn — co dělat" style="margin-top:6px;"></textarea>');
    var ozvat=el('<input placeholder="Kdy se ozvat (volitelné)" style="margin-top:6px;">');
    var go=el('<button class="green full" style="margin-top:8px;">Přiřadit + odeslat</button>'); go.disabled=true; go.style.opacity=".5";
    function load(){ var q=(si.value||"").trim();
      api("GET","/api/v1/erp/app/zakazky"+(q?("?q="+encodeURIComponent(q)):""),"").then(function(j){ res.innerHTML="";
        ((j&&j.zakazky)||[]).slice(0,10).forEach(function(z){
          var b=el('<button class="ghost full" style="text-align:left;font-size:13px;margin-top:5px;">'+(z.typ==="REZIE"?"🧰 ":"🧾 ")+esc(z.cislo)+" — "+esc(z.nazev||"")+'</button>');
          b.addEventListener("click",function(){ chosen.c=z.cislo; Array.prototype.forEach.call(res.children,function(x){x.style.outline="";}); b.style.outline="2px solid var(--green)"; go.disabled=false; go.style.opacity="1"; });
          res.appendChild(b);
        });
      });
    }
    var tmr=null; si.addEventListener("input",function(){clearTimeout(tmr);tmr=setTimeout(load,300);});
    go.addEventListener("click",function(){ if(!chosen.c)return; go.disabled=true;
      api("POST","/api/v1/erp/app/vyroba/prirazeni",{user_id:pp.user_id,cislo_zakazky:chosen.c,pokyn:(pokyn.value||"").trim(),kdy_ozvat:(ozvat.value||"").trim()}).then(function(r){ if(r&&r.ok){ vyLoad(); } else { go.disabled=false; alert("Chyba: "+((r&&r.error)||"?")); } });
    });
    var _pst=el('<div class="hint" style="margin-top:3px;"></div>');
    var _prow=el('<div style="display:flex;gap:6px;align-items:stretch;margin-top:6px;"></div>');
    pokyn.style.marginTop="0"; pokyn.style.flex="1"; _prow.appendChild(pokyn); _prow.appendChild(vyMic(pokyn,_pst));
    box.appendChild(si);box.appendChild(res);box.appendChild(_prow);box.appendChild(_pst);box.appendChild(ozvat);box.appendChild(go); load(); return box;
  }
  function vyZakLi(z){
    var ul=document.getElementById("vylist");
    var li=document.createElement("li"); li.className="ct"; li.style.padding="0"; li.style.borderBottom="none";
    var head=el('<div class="cthead"><div class="cav" style="background:'+avColor(z.cislo)+';font-size:16px;">🧾</div><div style="flex:1;min-width:0;"><div class="ctname">'+esc(z.cislo)+'</div><div class="ctnum">'+esc(z.nazev||"")+' · '+(z.pocet||0)+' lidí</div></div></div>');
    var exp=el('<div class="ctexp" style="display:none;"></div>');
    head.addEventListener("click",function(){ vyAcc(ul,li,exp); if(li.classList.contains("open")) vyFillZak(exp,z); });
    li.appendChild(head); li.appendChild(exp); return li;
  }
  function vyFillZak(exp,z){
    exp.innerHTML="";
    (z.lide||[]).forEach(function(l){
      var row=el('<div style="display:flex;align-items:center;gap:8px;padding:7px 4px;border-top:1px solid var(--bord);"></div>');
      var manual=(l.source==="manual");
      row.appendChild(el('<div style="flex:1;min-width:0;">'+(manual?"📌 ":"📋 ")+esc(l.jmeno)+(l.done?' · ✅':'')+'</div>'));
      var b=el('<button class="ghost" style="padding:4px 9px;font-size:12px;margin:0;color:#ef4444;border-color:#ef4444;">✕ odebrat</button>');
      b.addEventListener("click",function(){
        if(manual){ api("POST","/api/v1/erp/app/vyroba/prirazeni/"+l.prirazeni_id+"/zrusit",{}).then(function(r){ if(r&&r.ok) vyLoad(); }); }
        else { vyOverlay(l.user_id,z.cislo,{hidden:true}); }
      });
      row.appendChild(b); exp.appendChild(row);
    });
    var add=el('<button class="green full" style="margin-top:8px;">➕ Přidat člověka</button>'), wrap=el('<div></div>');
    add.addEventListener("click",function(){ if(wrap.firstChild){wrap.innerHTML="";return;} wrap.appendChild(vyPersonBox(z)); });
    exp.appendChild(add); exp.appendChild(wrap);
  }
  function vyPersonBox(z){
    var box=el('<div style="margin-top:8px;padding:10px;background:#0f1620;border:1px solid var(--bord);border-radius:10px;"></div>');
    box.appendChild(el('<div class="hint">Přiřadit člověka na '+esc(z.cislo)+':</div>'));
    var si=el('<input placeholder="🔍 jméno">'), res=el('<div style="margin-top:6px;"></div>');
    function load(){ var q=deacc((si.value||"").trim()); res.innerHTML="";
      _vyPeople.filter(function(pp){return !q||deacc(pp.jmeno).indexOf(q)>=0;}).slice(0,12).forEach(function(pp){
        var b=el('<button class="ghost full" style="text-align:left;font-size:13px;margin-top:5px;">👤 '+esc(pp.jmeno)+'</button>');
        b.addEventListener("click",function(){ b.disabled=true;
          api("POST","/api/v1/erp/app/vyroba/prirazeni",{user_id:pp.user_id,cislo_zakazky:z.cislo}).then(function(r){ if(r&&r.ok) vyLoad(); else { b.disabled=false; alert("Chyba: "+((r&&r.error)||"?")); } });
        });
        res.appendChild(b);
      });
    }
    si.addEventListener("input",load); box.appendChild(si); box.appendChild(res); load(); return box;
  }
  // ───── DOCHÁZKA (check-in/out + přehled) ─────
  // Rozbalovací sekce jako Kontakty (Marti 7.6.): samostatné bubliny s mezerou,
  // VŽDY otevřená max jedna (ostatní se zavřou) — accordion jako kontakty.
  function collSec(ulEl, title, defOpen, onToggle){
    var li=document.createElement("li");
    li.style.cssText="background:var(--surf);border:1px solid var(--bord);border-radius:12px;margin:0 0 10px;padding:0 8px;list-style:none;";
    var head=el('<div class="cthead" style="padding:13px 8px;"><span style="font-size:15px;font-weight:600;flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;"></span><span class="cgv" style="color:var(--tx);font-weight:700;white-space:nowrap;"></span><span class="cgch" style="margin-left:6px;color:var(--mut);font-size:12px;">▼</span></div>');
    head.firstChild.textContent=title;
    var box=el('<div style="display:none;padding:0 8px 12px;"></div>');
    function close(){ box.style.display="none"; head.querySelector(".cgch").textContent="▼"; li.style.borderColor="var(--bord)"; li.style.background="var(--surf)"; if(onToggle)onToggle(false); }
    function setOpen(o){
      if(o){ (ulEl._secs||[]).forEach(function(s){ if(s.box!==box) s.close(); }); }
      box.style.display=o?"block":"none"; head.querySelector(".cgch").textContent=o?"▲":"▼";
      li.style.borderColor=o?"#2a4d80":"var(--bord)"; li.style.background=o?"rgba(79,142,247,.07)":"var(--surf)";
      if(onToggle)onToggle(o);
    }
    head.addEventListener("click",function(){ setOpen(box.style.display==="none"); });
    li.appendChild(head); li.appendChild(box); ulEl.appendChild(li);
    ulEl._secs=ulEl._secs||[]; ulEl._secs.push({box:box, close:close});
    if(defOpen) setOpen(true);
    return {box:box, val:head.querySelector(".cgv"), ttl:head.firstChild};
  }
  function czDays(n){ return n===1?"1 den":(n>=2&&n<=4?(n+" dny"):(n+" dní")); }
  var _dS=null;
  // Marti 7.6. večer: odpověď Marti-AI se zobrazí PŘÍMO v Docházce — globální
  // okno #mmReply přežije překreslení menu i 60s tick. Polling je nezávislý na DOM.
  var _mmPollIv=null, _mmReplyTxt=null, _mmReplyTitle="💬 Tvoje Marti odpovídá", _mmOnClose=null;
  function _mmRender(){
    var d=document.getElementById("mmReply"); if(!d) return;
    if(!_mmReplyTxt){ d.style.display="none"; return; }
    d.innerHTML="";
    var head=el('<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;"><b style="flex:1;"></b><button class="ghost sm">✕</button></div>');
    head.querySelector("b").textContent=_mmReplyTitle;
    head.querySelector("button").addEventListener("click",function(){
      var f=_mmOnClose; _mmReplyTxt=null; _mmOnClose=null; _mmRender(); if(f)f();
    });
    var body=el('<div style="white-space:pre-wrap;font-size:14px;line-height:1.5;max-height:45vh;overflow-y:auto;"></div>');
    body.textContent=_mmReplyTxt;
    d.appendChild(head); d.appendChild(body);
    d.style.display="block";
    try{ d.scrollIntoView({behavior:"smooth",block:"nearest"}); }catch(e){}
  }
  function _mmShow(title, txt, onClose){ _mmReplyTitle=title; _mmReplyTxt=txt; _mmOnClose=onClose||null; _mmRender(); }
  function _mmStartPoll(afterId){
    if(_mmPollIv) clearInterval(_mmPollIv);
    var tries=0;
    _mmPollIv=setInterval(function(){
      if(++tries>36){ clearInterval(_mmPollIv); _mmPollIv=null; return; }
      api("GET","/api/v1/erp/app/marti-message/last?after="+(afterId||0),"").then(function(r){
        if(r&&r.id&&r.reply){
          clearInterval(_mmPollIv); _mmPollIv=null;
          _mmShow("💬 Tvoje Marti odpovídá", r.reply);
        }
      });
    },5000);
  }
  // 🙋 Dotaz nadřízenému (Marti 7.6. večer — v1 jednoduše: padá Martimu na mobil)
  function _bossAnswerCheck(){
    api("GET","/api/v1/erp/app/ask-boss/my-answer","").then(function(r){
      if(r&&r.id&&r.answer){
        _mmShow("🙋 "+(r.boss||"Nadřízený")+" odpovídá",
          (r.question?("❓ "+r.question+"\n\n"):"")+r.answer,
          function(){ api("POST","/api/v1/erp/app/ask-boss/seen",{id:r.id}); });
      }
    });
  }
  function _bossPendingLoad(){
    var d=document.getElementById("bossAsk"); if(!d) return;
    api("GET","/api/v1/erp/app/ask-boss/pending","").then(function(j){
      d=document.getElementById("bossAsk"); if(!d) return;
      d.innerHTML="";
      ((j&&j.items)||[]).forEach(function(q){
        var card=el('<div style="background:rgba(79,142,247,.10);border:1px solid #2a4d80;border-radius:12px;padding:12px;margin-top:10px;"></div>');
        card.appendChild(el('<div style="font-weight:600;font-size:14.5px;">🙋 '+esc(q.jmeno)+' · '+esc(q.cas||"")+'</div>'));
        var qt=el('<div style="margin-top:4px;font-size:14px;white-space:pre-wrap;"></div>'); qt.textContent=q.question; card.appendChild(qt);
        var ta=el('<textarea rows="2" placeholder="Odpověz mu…" style="width:100%;margin-top:8px;background:#0f1620;border:1px solid var(--green);border-radius:8px;padding:10px;color:var(--tx);font-size:14px;font-family:inherit;"></textarea>');
        var ok=el('<button class="green full" style="margin-top:6px;font-size:17px;">🚀</button>');
        var st=el('<div class="hint" style="margin-top:4px;"></div>');
        ok.addEventListener("click",function(){
          var a=(ta.value||"").trim(); if(!a){ st.textContent="Napiš odpověď."; return; }
          ok.disabled=true;
          api("POST","/api/v1/erp/app/ask-boss/answer",{id:q.id,answer:a}).then(function(r){
            if(r&&r.ok){ card.remove(); }
            else { ok.disabled=false; st.textContent="✗ "+((r&&r.error)||"Nepodařilo se."); }
          });
        });
        card.appendChild(ta); card.appendChild(ok); card.appendChild(st);
        d.appendChild(card);
      });
    });
  }
  function bossAskBuild(box){
    var ta=el('<textarea rows="2" placeholder="Na co se chceš zeptat?" style="width:100%;background:#0f1620;border:1px solid var(--blue);box-shadow:0 0 0 2px rgba(79,142,247,.18);border-radius:10px;padding:11px;color:var(--tx);font-size:15px;font-family:inherit;"></textarea>');
    var ok=el('<button class="green full" style="margin-top:8px;font-size:17px;">🚀</button>');
    var st=el('<div class="hint" style="margin-top:6px;"></div>');
    ok.addEventListener("click",function(){
      var q=(ta.value||"").trim(); if(!q){ st.textContent="Napiš dotaz."; return; }
      ok.disabled=true;
      api("POST","/api/v1/erp/app/ask-boss",{question:q}).then(function(j){
        if(j&&j.ok){ ta.value=""; ok.disabled=false; st.textContent="✅ Odesláno — odpověď se ukáže tady v Docházce."; }
        else { ok.disabled=false; st.textContent="✗ "+((j&&j.error)||"Nepodařilo se."); }
      });
    });
    box.appendChild(ta); box.appendChild(ok); box.appendChild(st);
    setTimeout(function(){ try{ box.scrollIntoView({behavior:"smooth",block:"start"}); }catch(e){} },60);
  }
  // Nápověda pro docházku (Jirka 26.6.2026) — adaptace docs/NAVOD_DOCHAZKA_UZIVATELE.html.
  // ❓ z hlavičky Spolupráce + kontextové ⓘ tipy (openKey auto-rozbalí sekci).
