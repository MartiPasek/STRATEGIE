  function mytodo(){
    app.innerHTML=topbar("📝 Moje TODO", true);
    var p=el('<div class="panel"></div>');
    var arow=el('<div style="display:flex;gap:8px;margin-bottom:10px;"></div>');
    var inp=el('<input id="todoInp" placeholder="Nový úkol…" autocomplete="off" style="flex:1;">');
    var add=el('<button class="green" style="width:54px;font-size:22px;margin:0;">＋</button>');
    function doAdd(){ var t=(inp.value||"").trim(); if(!t)return; add.disabled=true; api("POST","/api/v1/erp/app/todo",{text:t}).then(function(r){ add.disabled=false; if(r&&r.ok){ inp.value=""; try{inp.focus();}catch(e){} todoLoad(); } else alert("Chyba: "+((r&&r.error)||"?")); }); }
    add.addEventListener("click",doAdd);
    inp.addEventListener("keydown",function(e){ if(e.key==="Enter") doAdd(); });
    arow.appendChild(inp); arow.appendChild(add); p.appendChild(arow);
    p.appendChild(el('<div class="list"><ul id="todoList"><li style="color:var(--mut);border:none;">Načítám…</li></ul></div>'));
    app.appendChild(p); todoLoad();
  }
  function todoLoad(){
    api("GET","/api/v1/erp/app/todo","").then(function(j){
      var ul=document.getElementById("todoList"); if(!ul)return; ul.innerHTML="";
      var items=(j&&j.todo)||[];
      if(!items.length){ ul.appendChild(el('<li style="color:var(--mut);border:none;">Zatím nic. Přidej si úkol nahoře. ✍️</li>')); return; }
      items.forEach(function(t){
        var li=el('<li style="display:flex;align-items:center;gap:10px;padding:11px 4px;"></li>');
        var chk=el('<div style="width:26px;height:26px;flex:none;border-radius:7px;border:2px solid '+(t.done?"var(--green)":"var(--mut)")+';background:'+(t.done?"var(--green)":"transparent")+';color:#04150e;text-align:center;line-height:23px;font-size:16px;cursor:pointer;">'+(t.done?"✓":"")+'</div>');
        chk.addEventListener("click",function(){ api("POST","/api/v1/erp/app/todo/"+t.id+"/toggle",{}).then(function(){ todoLoad(); }); });
        var txt=el('<div style="flex:1;min-width:0;white-space:normal;word-break:break-word;'+(t.done?"text-decoration:line-through;color:var(--mut);":"")+'">'+esc(t.text)+'</div>');
        var del=el('<button class="ghost" style="width:40px;margin:0;color:#e06a5a;flex:none;">✕</button>');
        del.addEventListener("click",function(){ if(confirm("Smazat úkol?")) api("POST","/api/v1/erp/app/todo/"+t.id+"/delete",{}).then(function(){ todoLoad(); }); });
        li.appendChild(chk); li.appendChild(txt); li.appendChild(del); ul.appendChild(li);
      });
    }); }
  // ───── ÚKOLY z Centrály (EC_Ukoly, read-only v1). Marti 9.6. ─────
  var _ecView="resitel";
  var EC_VIEWS=[
    {k:"resitel",  ic:"🛠", l:"Řešitel"},
    {k:"zadavatel",ic:"📤", l:"Zadané"},
    {k:"kopie",    ic:"📑", l:"Kopie"},
    {k:"urgentni", ic:"⏰", l:"Urgent"},
    {k:"splnene",  ic:"✅", l:"Splněné"}
  ];
  function ecukoly(){
    app.innerHTML=topbar("📋 Úkoly", true, true);
    var _tb=app.querySelector('.topbar'); if(_tb)_tb.style.paddingTop="12px";
    var wrap=el('<div style="display:flex;gap:8px;height:calc(100vh - 100px - var(--navh, 65px));padding:4px 2px 0;"></div>');
    var left=el('<div id="ecleft" style="flex:1;min-width:0;min-height:0;display:flex;flex-direction:column;overflow:hidden;"></div>');
    var rail=el('<div id="ecrail" style="width:64px;flex:none;overflow-y:auto;display:flex;flex-direction:column;gap:5px;padding:1px;"></div>');
    EC_VIEWS.forEach(function(v){ rail.appendChild(ecBtn(v)); });
    wrap.appendChild(left); wrap.appendChild(rail); app.appendChild(wrap);
    ecLoad();
  }
  function ecBtn(v){
    var on=(_ecView===v.k);
    var b=el('<button data-k="'+v.k+'" style="margin:0;padding:6px 1px;font-size:10px;line-height:1.1;display:flex;flex-direction:column;align-items:center;gap:2px;border:1px solid '+(on?"var(--blue)":"var(--bord)")+';background:'+(on?"var(--blue)":"transparent")+';color:'+(on?"#fff":"var(--mut)")+';border-radius:9px;cursor:pointer;"><span style="font-size:17px;">'+v.ic+'</span>'+esc(v.l)+'</button>');
    b.addEventListener("click",function(){ _ecView=v.k; ecPaintRail(); ecLoad(); });
    return b;
  }
  function ecPaintRail(){ var r=document.getElementById("ecrail"); if(!r)return;
    Array.prototype.forEach.call(r.querySelectorAll("button[data-k]"),function(b){ var on=b.getAttribute("data-k")===_ecView;
      b.style.background=on?"var(--blue)":"transparent"; b.style.color=on?"#fff":"var(--mut)"; b.style.borderColor=on?"var(--blue)":"var(--bord)"; }); }
  function ecLoad(){
    var L=document.getElementById("ecleft"); if(!L)return;
    L.innerHTML='<div class="hint" style="padding:12px;">Načítám z Centrály…</div>';
    api("GET","/api/v1/erp/app/ec-ukoly?view="+_ecView,"").then(function(j){
      L.innerHTML="";
      if(!j||!j.ok){ L.innerHTML='<div class="hint" style="padding:14px;">'+esc((j&&j.error)||"Nepodařilo se načíst.")+'</div>'; return; }
      if(j.note==="no_ec_number"){ L.innerHTML='<div class="hint" style="padding:14px;line-height:1.6;">Nemáš přiřazené EC číslo v Centrále.</div>'; return; }
      var items=j.ukoly||[];
      var lw=el('<div style="flex:1;min-height:0;overflow-y:auto;-webkit-overflow-scrolling:touch;padding-bottom:24px;"></div>');
      if(!items.length){ lw.innerHTML='<div class="hint" style="padding:14px;">Žádné úkoly. 👍</div>'; L.appendChild(lw); return; }
      var ul=el('<ul class="list" style="padding:0 6px;"></ul>');
      items.forEach(function(t){
        var li=el('<li class="ct" style="padding:0;border-bottom:none;"></li>');
        var sub=(t.zadavatel?('👤 '+esc(t.zadavatel)):'')+(t.termin?(' · 📅 '+esc(t.termin)):'')+(t.zak?(' · '+esc(t.zak)):'')+((t.hp!=null&&t.hp!=="")?(' · '+t.hp+'%'):'');
        var col=t.pozde?'#e06a5a':'var(--tx)';
        var head=el('<div class="cthead"><div class="cav" style="background:'+avColor(t.predmet||"?")+';font-size:15px;">'+(t.pozde?'⏰':'📋')+'</div><div style="flex:1;min-width:0;"><div class="ctname" style="color:'+col+';">'+esc(t.predmet||"(bez názvu)")+'</div><div class="ctnum">'+sub+'</div></div></div>');
        var exp=el('<div class="ctexp" style="display:none;"></div>');
        head.addEventListener("click",function(){ vyAcc(ul,li,exp); if(li.classList.contains("open")) ecFillDetail(exp,t); });
        li.appendChild(head); li.appendChild(exp); ul.appendChild(li);
      });
      lw.appendChild(ul); L.appendChild(lw);
    }); }
  function ecFillDetail(exp,t){
    exp.innerHTML='<div class="hint" style="padding:8px;">Načítám detail…</div>';
    api("GET","/api/v1/erp/app/ec-ukoly/"+t.id+"/detail","").then(function(j){
      exp.innerHTML="";
      if(!j||!j.ok){ exp.innerHTML='<div class="hint" style="padding:8px;">Detail se nenačetl.</div>'; return; }
      var u=j.ukol||{};
      if(u.popis){ exp.appendChild(el('<div style="padding:8px 6px;white-space:pre-wrap;word-break:break-word;font-size:14px;line-height:1.55;">'+esc(u.popis)+'</div>')); }
      exp.appendChild(el('<div class="hint" style="padding:2px 6px;">Stav: '+esc(u.stav||"")+((u.hp!=null&&u.hp!=="")?(' · '+u.hp+'%'):'')+(u.termin?(' · termín '+esc(u.termin)):'')+'</div>'));
      var pz=j.poznamky||[];
      if(pz.length){
        exp.appendChild(el('<div style="padding:8px 6px 2px;font-weight:700;font-size:13px;color:#ffd9a8;">💬 Poznámky</div>'));
        pz.forEach(function(p){ exp.appendChild(el('<div style="padding:4px 6px;border-top:1px solid var(--bord);font-size:13px;white-space:pre-wrap;word-break:break-word;"><b style="color:#9fb0c2;">'+esc(p.autor||"")+'</b> <span class="hint">'+esc(p.kdy||"")+'</span><br>'+esc(p.text||"")+'</div>')); });
      }
      exp.appendChild(el('<div class="hint" style="padding:8px 6px;">Akce (Přidat poznámku, Dát splněno) přidám v dalším kroku.</div>'));
    }); }
  // ───── Nativní úkoly STRATEGIE (tenant.task, lidi i AI). Marti 9.6. ─────
  var _stView="moje";
  var ST_VIEWS=[{k:"moje",ic:"🛠",l:"Moje"},{k:"zadane",ic:"📤",l:"Zadané"},{k:"urgentni",ic:"⏰",l:"Urgent"},{k:"splnene",ic:"✅",l:"Hotové"}];
  function strtask(){
    app.innerHTML=topbar("✅ Úkoly", true, true);
    var _tb=app.querySelector('.topbar'); if(_tb)_tb.style.paddingTop="12px";
    var wrap=el('<div style="display:flex;gap:8px;height:calc(100vh - 100px - var(--navh, 65px));padding:4px 2px 0;"></div>');
    var left=el('<div id="stleft" style="flex:1;min-width:0;min-height:0;display:flex;flex-direction:column;overflow:hidden;"></div>');
    var rail=el('<div id="strail" style="width:64px;flex:none;overflow-y:auto;display:flex;flex-direction:column;gap:5px;padding:1px;"></div>');
    ST_VIEWS.forEach(function(v){ rail.appendChild(stBtn(v)); });
    rail.appendChild(el('<div style="flex:1 1 auto;min-height:6px;"></div>'));
    var add=el('<button style="margin:0;padding:8px 1px;font-size:11px;line-height:1.1;display:flex;flex-direction:column;align-items:center;gap:2px;border:1px dashed var(--green);background:transparent;color:var(--green);border-radius:9px;cursor:pointer;"><span style="font-size:18px;">➕</span>Nový</button>');
    add.addEventListener("click",stNew); rail.appendChild(add);
    wrap.appendChild(left); wrap.appendChild(rail); app.appendChild(wrap);
    stLoad();
  }
  function stBtn(v){
    var on=(_stView===v.k);
    var b=el('<button data-k="'+v.k+'" style="margin:0;padding:6px 1px;font-size:10px;line-height:1.1;display:flex;flex-direction:column;align-items:center;gap:2px;border:1px solid '+(on?"var(--green)":"var(--bord)")+';background:'+(on?"var(--green)":"transparent")+';color:'+(on?"#04150e":"var(--mut)")+';border-radius:9px;cursor:pointer;"><span style="font-size:17px;">'+v.ic+'</span>'+esc(v.l)+'</button>');
    b.addEventListener("click",function(){ _stView=v.k; stPaintRail(); stLoad(); });
    return b;
  }
  function stPaintRail(){ var r=document.getElementById("strail"); if(!r)return;
    Array.prototype.forEach.call(r.querySelectorAll("button[data-k]"),function(b){ var on=b.getAttribute("data-k")===_stView;
      b.style.background=on?"var(--green)":"transparent"; b.style.color=on?"#04150e":"var(--mut)"; b.style.borderColor=on?"var(--green)":"var(--bord)"; }); }
  function stEnsureParentChip(){
    var r=document.getElementById("strail"); if(!r) return;
    if(r.querySelector('button[data-k="marti_ai"]')) return;
    var b=stBtn({k:"marti_ai",ic:"🤖",l:"Marti-AI"});
    var spacer=r.querySelector("div"); if(spacer) r.insertBefore(b,spacer); else r.appendChild(b);
  }
  function stDraftRow(){
    var dr=""; try{ dr=localStorage.getItem("stg_task_draft")||""; }catch(e){}
    if(!dr || _stView!=="moje") return null;
    var title=esc((dr.split("\n")[0]||"").slice(0,80));
    var li=el('<li class="ct" style="padding:0;border-bottom:none;"><div class="cthead"><div class="cav" style="background:#e0a44a;font-size:15px;">✏️</div><div style="flex:1;min-width:0;"><div class="ctname" style="color:#ffd9a8;">'+title+'</div><div class="ctnum">rozpracované — pokračovat</div></div></div></li>');
    li.addEventListener("click",stNew);
    return li;
  }
  function stLoad(){
    var L=document.getElementById("stleft"); if(!L)return;
    L.innerHTML='<div class="hint" style="padding:12px;">Načítám…</div>';
    api("GET","/api/v1/erp/app/task?view="+_stView,"").then(function(j){
      L.innerHTML="";
      if(!j||!j.ok){ L.innerHTML='<div class="hint" style="padding:14px;">'+esc((j&&j.error)||"Nepodařilo se načíst.")+'</div>'; return; }
      var items=j.ukoly||[];
      if(j.is_parent) stEnsureParentChip();
      var lw=el('<div style="flex:1;min-height:0;overflow-y:auto;-webkit-overflow-scrolling:touch;padding-bottom:24px;"></div>');
      var ul=el('<ul class="list" style="padding:0 6px;"></ul>');
      var drow=stDraftRow(); if(drow) ul.appendChild(drow);
      if(!items.length && !drow){ lw.innerHTML='<div class="hint" style="padding:14px;line-height:1.6;">Žádné úkoly.<br>Přidej přes <b>➕ Nový</b> vpravo dole.</div>'; L.appendChild(lw); return; }
      items.forEach(function(t){
        var li=el('<li class="ct" style="padding:0;border-bottom:none;"></li>');
        var sub=(t.stav_txt?('• '+esc(t.stav_txt)):'')+(t.termin?(' · 📅 '+esc(t.termin)):'')+(t.zak?(' · '+esc(t.zak)):'')+((t.zadavatel&&_stView!=="zadane")?(' · 👤 '+esc(t.zadavatel)):'');
        var col=t.pozde?'#e06a5a':'var(--tx)';
        var ic=t.pozde?'⏰':(t.priorita>=2?'🔴':'🗒');
        var head=el('<div class="cthead"><div class="cav" style="background:'+avColor(t.predmet||"?")+';font-size:15px;">'+ic+'</div><div style="flex:1;min-width:0;"><div class="ctname" style="color:'+col+';">'+esc(t.predmet||"")+'</div><div class="ctnum">'+sub+'</div></div></div>');
        var exp=el('<div class="ctexp" style="display:none;"></div>');
        head.addEventListener("click",function(){ vyAcc(ul,li,exp); if(li.classList.contains("open")) stDetail(exp,t); });
        li.appendChild(head); li.appendChild(exp); ul.appendChild(li);
      });
      lw.appendChild(ul); L.appendChild(lw);
    }); }
  function stDetail(exp,t){
    exp.innerHTML='<div class="hint" style="padding:8px;">Načítám…</div>';
    api("GET","/api/v1/erp/app/task/"+t.id,"").then(function(j){
      exp.innerHTML="";
      if(!j||!j.ok){ exp.innerHTML='<div class="hint" style="padding:8px;">Nenačteno.</div>'; return; }
      var u=j.ukol||{};
      if(u.popis){ exp.appendChild(el('<div style="padding:8px 6px;white-space:pre-wrap;word-break:break-word;font-size:14px;line-height:1.55;">'+esc(u.popis)+'</div>')); }
      exp.appendChild(el('<div class="hint" style="padding:2px 6px;">👤 '+esc(u.zadavatel||"")+(u.termin?(' · 📅 '+esc(u.termin)):'')+(u.zak?(' · '+esc(u.zak)):'')+'</div>'));
      var rr=j.resitele||[];
      if(rr.length){ exp.appendChild(el('<div class="hint" style="padding:4px 6px;">Řešitelé: '+rr.map(function(x){return esc(x.jmeno)+' ('+esc(x.stav_txt)+')';}).join(', ')+'</div>')); }
      var arow=el('<div style="display:flex;gap:6px;flex-wrap:wrap;padding:8px 6px;"></div>');
      var ms=j.muj_stav;
      function sb(lbl,st,cl){ var b=el('<button class="'+(cl||"ghost")+'" style="margin:0;">'+lbl+'</button>'); b.addEventListener("click",function(){ stSetStav(t.id,st); }); arow.appendChild(b); }
      if(ms!=null){ if(ms<2) sb("▶ Zahájit",2,"ghost"); if(ms<3) sb("✅ Hotovo",3,"green"); if(ms===3) sb("📣 Reportováno",4,"ghost"); }
      if(j.jsem_zadavatel) sb("🔒 Uzavřít",5,"ghost");
      if(arow.children.length) exp.appendChild(arow);
      exp.appendChild(el('<div style="padding:8px 6px 2px;font-weight:700;font-size:13px;color:#ffd9a8;">💬 Vlákno</div>'));
      var thread=el('<div style="display:flex;flex-direction:column;gap:6px;padding:6px;"></div>');
      var pz=(j.poznamky||[]).slice().reverse();
      if(!pz.length){ thread.appendChild(el('<div class="hint" style="text-align:center;padding:6px;">Zatím žádná zpráva. Napiš první.</div>')); }
      pz.forEach(function(p){
        var mine=(p.autor_id===j.me), ai=(p.autor_id===2);
        var bg=mine?'#13412f':(ai?'#3a2418':'#1b2738'), bd=mine?'#1f6b4d':(ai?'#d97757':'#2a3a4d');
        var row=el('<div style="display:flex;flex-direction:column;max-width:82%;align-self:'+(mine?'flex-end':'flex-start')+';"></div>');
        if(!mine){ row.appendChild(el('<div class="hint" style="margin:0 0 1px 6px;font-size:11px;">'+(ai?'🤖 ':'')+esc(p.autor||"")+'</div>')); }
        row.appendChild(el('<div style="background:'+bg+';border:1px solid '+bd+';border-radius:12px;padding:7px 10px;font-size:13.5px;line-height:1.5;white-space:pre-wrap;word-break:break-word;color:var(--tx);">'+esc(p.text||"")+'</div>'));
        row.appendChild(el('<div class="hint" style="font-size:10px;margin:1px 6px 0;align-self:'+(mine?'flex-end':'flex-start')+';">'+esc(p.kdy||"")+'</div>'));
        thread.appendChild(row);
      });
      exp.appendChild(thread);
      var prow=el('<div style="display:flex;gap:6px;padding:8px 6px;"></div>');
      var pin=el('<input placeholder="Napsat zprávu…" autocomplete="off" style="flex:1;">');
      var pb=el('<button class="green" style="width:48px;margin:0;font-size:18px;">➕</button>');
      function addp(){ var v=(pin.value||"").trim(); if(!v)return; pb.disabled=true; api("POST","/api/v1/erp/app/task/"+t.id+"/poznamka",{obsah:v}).then(function(r){ pb.disabled=false; if(r&&r.ok){ pin.value=""; stDetail(exp,t); } else alert("Chyba: "+((r&&r.error)||"?")); }); }
      pb.addEventListener("click",addp); pin.addEventListener("keydown",function(e){ if(e.key==="Enter")addp(); });
      prow.appendChild(pin); prow.appendChild(pb); exp.appendChild(prow);
    }); }
  function stSetStav(tid,stav){ api("POST","/api/v1/erp/app/task/"+tid+"/stav",{stav:stav}).then(function(r){ if(r&&r.ok){ stLoad(); } else alert("Chyba: "+((r&&r.error)||"?")); }); }
  function stNew(){
    var ov=el('<div style="position:fixed;inset:0;background:rgba(4,10,18,.96);z-index:200;display:flex;flex-direction:column;padding:16px;overflow:auto;"></div>');
    var hd=el('<div style="display:flex;gap:8px;align-items:center;margin-bottom:10px;"><div style="flex:1;font-weight:700;font-size:17px;">➕ Nový úkol</div></div>');
    var cl=el('<button class="ghost" style="margin:0;width:44px;">✕</button>'); cl.addEventListener("click",function(){ ov.remove(); }); hd.appendChild(cl); ov.appendChild(hd);
    var txt=el('<textarea rows="4" placeholder="Napiš úkol, vzkaz nebo poznámku…" style="width:100%;background:#0f1620;border:1px solid var(--green);box-shadow:0 0 0 2px rgba(16,185,129,.15);border-radius:10px;padding:12px;color:var(--tx);font-size:15px;font-family:inherit;margin-bottom:10px;"></textarea>'); ov.appendChild(txt);
    // Marti 9.6.: koncept — rozepsaný text se průběžně ukládá (přežije zavření i zpět).
    try{ var _dr=localStorage.getItem("stg_task_draft"); if(_dr) txt.value=_dr; }catch(e){}
    txt.addEventListener("input",function(){ try{ if(txt.value.trim()) localStorage.setItem("stg_task_draft",txt.value); else localStorage.removeItem("stg_task_draft"); }catch(e){} });
    ov.appendChild(el('<div class="hint" style="margin-bottom:2px;">Termín splnění</div>'));
    var ter=el('<input type="date" style="margin-bottom:8px;">'); ov.appendChild(ter);
    ov.appendChild(el('<div class="hint" style="margin-bottom:4px;">Priorita</div>'));
    var prio={v:0}; var prow=el('<div style="display:flex;gap:6px;margin-bottom:12px;"></div>');
    [["Nízká",0],["Střední",1],["Vysoká",2]].forEach(function(p){ var b=el('<button class="ghost" style="flex:1;margin:0;">'+p[0]+'</button>'); b.addEventListener("click",function(){ prio.v=p[1]; Array.prototype.forEach.call(prow.children,function(x){x.style.outline="";}); b.style.outline="2px solid var(--green)"; }); if(p[1]===0)b.style.outline="2px solid var(--green)"; prow.appendChild(b); }); ov.appendChild(prow);
    ov.appendChild(el('<div class="hint" style="margin-bottom:4px;">Komu (prázdné = sobě). Lze i AI 🤖</div>'));
    var rchips=el('<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px;"></div>'); ov.appendChild(rchips);
    var resit={ids:[],names:{}};
    function paintChips(){ rchips.innerHTML="";
      if(!resit.ids.length){ rchips.appendChild(el('<span class="hint">→ pro sebe</span>')); }
      resit.ids.forEach(function(id){ var c=el('<span style="background:#1b2738;border:1px solid #2a3a4d;border-radius:14px;padding:5px 10px;font-size:13px;display:inline-flex;align-items:center;gap:6px;">'+esc(resit.names[id]||("#"+id))+' <b data-x style="cursor:pointer;color:#e06a5a;">✕</b></span>'); c.querySelector("[data-x]").addEventListener("click",function(){ resit.ids=resit.ids.filter(function(x){return x!==id;}); paintChips(); }); rchips.appendChild(c); });
      var add=el('<span style="background:transparent;border:1px dashed var(--blue);color:var(--blue);border-radius:14px;padding:5px 10px;font-size:13px;cursor:pointer;">+ Přiřadit</span>'); add.addEventListener("click",openPick); rchips.appendChild(add);
    }
    function openPick(){
      var pv=el('<div style="position:fixed;inset:0;background:rgba(4,10,18,.97);z-index:210;display:flex;flex-direction:column;padding:14px;"></div>');
      var h=el('<div style="display:flex;gap:8px;align-items:center;margin-bottom:8px;"><div style="flex:1;font-weight:700;font-size:16px;">Přiřadit řešitele</div></div>');
      var x=el('<button class="ghost" style="margin:0;width:44px;">✕</button>'); x.addEventListener("click",function(){pv.remove();}); h.appendChild(x); pv.appendChild(h);
      var srch=el('<input placeholder="🔍 Hledat…" autocomplete="off" style="margin-bottom:8px;">'); pv.appendChild(srch);
      var lw=el('<div style="flex:1;overflow:auto;"><ul class="list" id="tpick"><li class="hint" style="border:none;">Načítám…</li></ul></div>'); pv.appendChild(lw);
      var done=el('<button class="green full" style="margin-top:8px;">Hotovo</button>'); done.addEventListener("click",function(){ pv.remove(); }); pv.appendChild(done);
      app.appendChild(pv);
      var all=[];
      function rp(){ var f=deacc((srch.value||"").trim()); var ul=document.getElementById("tpick"); if(!ul)return; ul.innerHTML="";
        all.filter(function(p){return !f||deacc(p.jmeno).indexOf(f)>=0;}).forEach(function(p){
          var has=resit.ids.indexOf(p.user_id)>=0;
          var li=el('<li class="ct" style="padding:8px 6px;display:flex;align-items:center;gap:8px;cursor:pointer;"><div class="cav" style="background:'+(p.agent?"#d97757":avColor(p.jmeno||"?"))+';">'+(p.agent?"🤖":vyInitial(p.jmeno||"?"))+'</div><div style="flex:1;">'+esc(p.jmeno||"")+(p.agent?' <span class="hint">(AI)</span>':'')+'</div><div>'+(has?'<span style="color:var(--green);">✓</span>':'<span style="color:var(--blue);font-size:20px;">＋</span>')+'</div></li>');
          li.addEventListener("click",function(){ if(has){ resit.ids=resit.ids.filter(function(x){return x!==p.user_id;}); } else { resit.ids.push(p.user_id); resit.names[p.user_id]=p.jmeno; } rp(); paintChips(); });
          ul.appendChild(li);
        });
      }
      srch.addEventListener("input",rp);
      api("GET","/api/v1/erp/app/task-lide","").then(function(j){ all=(j&&j.lide)||[]; all.sort(function(a,b){return ((b.agent?1:0)-(a.agent?1:0))||((a.jmeno||"")<(b.jmeno||"")?-1:1);}); rp(); });
    }
    paintChips();
    var sub=el('<button class="green full">Vytvořit</button>');
    sub.addEventListener("click",function(){ var pv=(txt.value||"").trim(); if(!pv){ try{txt.focus();}catch(e){} return; } sub.disabled=true;
      var payload={text:pv,termin:(ter.value||""),priorita:prio.v};
      if(resit.ids.length) payload.resitele=resit.ids;
      api("POST","/api/v1/erp/app/task",payload).then(function(r){ if(r&&r.ok){ try{localStorage.removeItem("stg_task_draft");}catch(e){} ov.remove(); _stView=resit.ids.length?"zadane":"moje"; stPaintRail(); stLoad(); } else { sub.disabled=false; alert("Chyba: "+((r&&r.error)||"?")); } }); });
    ov.appendChild(sub); app.appendChild(ov);
    try{txt.focus();}catch(e){}
  }
  function claudetasks(){ app.innerHTML=topbar("Claude", true); var p=el('<div class="panel"></div>');
    p.appendChild(el('<div class="list" style="padding:0 14px;"><ul id="ntlist"><li style="color:var(--mut);border:none;">Načítám…</li></ul></div>'));
    var r=el('<button class="ghost full">Obnovit</button>'); r.addEventListener("click",notifsLoad); p.appendChild(r); app.appendChild(p); notifsLoad(); }

  var _detailCmd=null;
  function openClaudeDetail(c){ _detailCmd=c; go("claudeDetail"); }
  function detailAct(c,decision){
    api("POST","/api/v1/erp/app/command/"+c.id+"/result",{decision:decision}).then(function(){
      api("GET","/api/v1/erp/app/mobile/commands/pending","").then(function(j){
        var cmds=(j&&j.commands)||[]; notifCount=cmds.length; renderNav();
        if(!cmds.length){ selectTab("home"); } else { curTab="notifs"; stack=["notifs","claudetasks"]; render(); }
      });
    });
  }
  function claudeDetail(){
    var c=_detailCmd||{};
    app.innerHTML=topbar("Claude", true);
    var p=el('<div class="panel"></div>');
    p.appendChild(el('<div style="font-weight:700;font-size:17px;margin-bottom:10px;">'+esc(c.title||"Claude")+'</div>'));
    p.appendChild(el('<div style="color:#d4dde8;font-size:14px;line-height:1.65;white-space:pre-wrap;word-break:break-word;max-height:72vh;overflow-y:auto;-webkit-overflow-scrolling:touch;">'+esc(c.message||"")+'</div>'));
    var a=el('<div class="nactions" style="margin-top:20px;"></div>');
    function b(l,cl,d){var x=el('<button class="'+cl+'">'+l+'</button>'); x.addEventListener("click",function(){ detailAct(c,d); }); a.appendChild(x);}
    if(c.command_type==="claude_confirm"){ b("Odmítnout","warn","reject"); b("Povolit","green","accept"); } else { b("OK","ghost","done"); }
    p.appendChild(a); app.appendChild(p);
  }

  // ───── KONTAKTY ─────
  var _contacts=null;
  // Sloučení duplikátů kontaktů podle normalizovaného čísla (777 666 555 == 777666555).
  function _normNum(n){ return (n||"").replace(/[^0-9]/g,""); }
  function dedupContacts(arr){
    var seen={}, out=[];
    (arr||[]).forEach(function(c){
      var k=_normNum(c.number);
      if(!k){ out.push(c); return; }
      if(seen[k]!==undefined){ var i=seen[k]; if(c.photo && !out[i].photo) out[i]=c; return; }
      seen[k]=out.length; out.push(c);
    });
    return out;
  }
  // Hledání bez diakritiky (Marti 7.6.): á=a, ě/é=e … jako nativní hledání.
  function deacc(s){ try{ return (s||"").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g,""); }catch(e){ return (s||"").toLowerCase(); } }
  function renderContactsList(){ var ul=document.getElementById("ctlist"); if(!ul)return; var j=_contacts;
    if(j&&j.need){ ul.innerHTML='<li style="border:none;"><div style="color:var(--mut);margin-bottom:8px;">Appka potřebuje přístup ke kontaktům.</div><button class="green sm" id="ctperm">Povolit přístup</button></li>'; var pb=document.getElementById("ctperm"); if(pb)pb.addEventListener("click",function(){bjson("getContacts",getPrefixes());setTimeout(loadContacts,700);}); return; }
    var all=dedupContacts((j&&j.contacts)||[]); var sf=document.getElementById("ctsearch"); var f=deacc(((sf&&sf.value)||"").trim()); var nf=f.replace(/\s/g,"");
    var list=all.filter(function(c){ if(!f)return true; return deacc(c.name).indexOf(f)>=0 || (c.number||"").replace(/\s/g,"").indexOf(nf)>=0; });
    if(!list.length){ ul.innerHTML='<li style="color:var(--mut);border:none;">'+(f?"Nic nenalezeno.":("Žádné kontakty s prefixem "+esc(getPrefixes())+"."))+'</li>'; return; }
    var pfx=getPrefixes(); ul.innerHTML="";
    list.forEach(function(c){
      var li=document.createElement("li"); li.className="ct"; li.style.padding="0"; li.style.borderBottom="none";
      var av = c.photo ? ('<div class="cav"><img src="'+c.photo+'"></div>')
        : ('<div class="cav" style="background:'+avColor(c.name||"?")+'">'+esc(((c.name||"?").replace(/[^A-Za-zÀ-ž]/g,"").charAt(0)||"?").toUpperCase())+'</div>');
      var head=el('<div class="cthead">'+av+'<div style="flex:1;min-width:0;"><div class="ctname">'+fmtName(c.name||"",pfx)+'</div><div class="ctnum">'+esc(c.number||"")+'</div></div></div>');
      var exp=el('<div class="ctexp" style="display:none;"><div class="ctacts"></div></div>');
      var acts=exp.querySelector(".ctacts");
      var bCall=el('<div class="cact call">'+PHONE_SVG_W+'</div>'); bCall.addEventListener("click",function(e){e.stopPropagation();doDial(c.number);});
      var bSms=el('<div class="cact sms" style="color:#fff;font-size:20px;">💬</div>'); bSms.addEventListener("click",function(e){e.stopPropagation();openApp("sms:"+(c.number||"").replace(/\s/g,""));});
      var bWa=el('<div class="cact" style="background:#25D366;">'+WA_SVG+'</div>');
      bWa.addEventListener("click",function(e){ e.stopPropagation(); var num=(c.number||"").replace(/[^0-9]/g,""); if(B&&typeof B.openExternal==="function") B.openExternal("https://wa.me/"+num); else openApp("https://wa.me/"+num); });
      acts.appendChild(bCall); acts.appendChild(bSms); acts.appendChild(bWa);
      head.addEventListener("click",function(){
        // Druhý klik na již otevřený kontakt → nativní detail (přes celý displej), nezmenšovat.
        if(li.classList.contains("open")){
          if(B&&typeof B.openContact==="function") B.openContact(c.number||"");
          return;
        }
        // Accordion: zavři všechny ostatní, otevři jen tenhle.
        ul.querySelectorAll("li.ct").forEach(function(o){ o.classList.remove("open"); var x=o.querySelector(".ctexp"); if(x)x.style.display="none"; });
        exp.style.display="block"; li.classList.add("open"); li.scrollIntoView({block:"nearest",behavior:"smooth"});
        setDialNum(c.number||"");  // vybraný kontakt → jeho číslo do zeleného pole
      });
      li.appendChild(head); li.appendChild(exp); ul.appendChild(li);
    }); }
  var _allContacts=false; try{ _allContacts=localStorage.getItem("stg_all_contacts")==="1"; }catch(e){}
  function loadContacts(){ _contacts=bjson("getContacts", _allContacts?"*":getPrefixes()); renderContactsList(); }
  var _dialNum="";
  function setDialNum(n){ _dialNum=(n||"").trim(); var e=document.getElementById("ctdialtxt"); if(!e)return;
    if(_dialNum){ e.textContent=_dialNum; e.style.color="var(--tx)"; } else { e.textContent="Vytáčení…"; e.style.color="var(--mut)"; } }
