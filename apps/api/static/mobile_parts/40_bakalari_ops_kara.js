  function bk_rozvrh(){
    app.innerHTML=topbar("🗓️ Rozvrh Nerudovka", true);
    app.appendChild(el('<div class="hint" style="margin:8px 6px;line-height:1.6;">Živá data ze školního systému Bakaláři — budovy Nerudovka i Aťásy. Náhled rozvrhu po třídách a učitelích.</div>'));
    var yr=el('<div id="bkYr" style="margin:0 6px 8px;display:flex;gap:6px;flex-wrap:wrap;align-items:center;"></div>');
    app.appendChild(yr);
    api("GET","/api/v1/erp/app/bakalari/versions","").then(function(j){
      if(!j||!j.ok||!(j.items&&j.items.length)){ return; }
      if(!window._bkPO){ window._bkPO=j.aktualni_po; }
      yr.innerHTML='<span style="font-size:12px;color:var(--mut);">Školní rok:</span>';
      j.items.forEach(function(v){
        var on=(v.po===window._bkPO);
        var b=el('<button style="padding:6px 12px;border-radius:999px;border:1px solid '+(on?'#4f8ef7':'var(--bord)')+';background:'+(on?'rgba(79,142,247,.18)':'rgba(255,255,255,.03)')+';color:var(--tx);font-weight:'+(on?'700':'500')+';cursor:pointer;font-size:13px;">'+esc(v.skolrok)+'</button>');
        b.addEventListener("click",function(){ window._bkPO=v.po; go("bk_rozvrh"); });
        yr.appendChild(b);
      });
    });
    var dash=el('<div id="bkDash" class="hint" style="margin:0 6px 10px;">Načítám…</div>');
    app.appendChild(dash);
    var l=el('<div class="list"></div>');
    l.appendChild(row("🏫","Třídy","Rozvrh po třídách — mřížka celého týdne",function(){ go("bk_tridy"); }));
    l.appendChild(row("👩‍🏫","Učitelé","Osobní rozvrh každého učitele",function(){ go("bk_ucitele"); }));
    l.appendChild(row("🚪","Obsazení učeben","Co se kdy učí v které učebně (Nerudovka / Aťásy)",function(){ go("bk_ucebny"); }));
    l.appendChild(row("📋","Úvazky","Co který učitel učí — předměty, třídy, hodiny",function(){ go("bk_uvazky"); }));
    l.appendChild(row("📊","Přehled školy","Žáci, naplněnost tříd, využití učeben — efektivita provozu",function(){ go("bk_skola"); }));
    l.appendChild(row("🗓️","Varianty rozvrhu","Rozvrh 2026/27 (A/B/C), třídy i učitelé — přes celou obrazovku",function(){ openApp("/rozvrh-verze"); }));
    l.appendChild(row("📅","Přehled po ročnících","Všechny třídy oboru (GD, MI…) vedle sebe — otevře se přes celou obrazovku",function(){ openApp("/rozvrh-prehled"); }));
    l.appendChild(row("🛠️","Chat s Claudem","Napiš, co u rozvrhu potřebuješ — Claude si to přečte a odpoví ti sem",function(){ openApp("/claude-chat"); }));
    app.appendChild(l);
    api("GET",_bkUrl("/api/v1/erp/app/bakalari/overview"),"").then(function(j){
      if(!j||!j.ok){ dash.textContent=(j&&j.error==="forbidden")?"🔒 Vidí jen rodiče.":"Nepodařilo se načíst."; return; }
      if(j.empty){ dash.textContent="Zrcadlo se právě plní daty…"; return; }
      function kc(v,lb){ return '<div style="flex:1;min-width:64px;background:rgba(255,255,255,.03);border:1px solid var(--bord);border-radius:12px;padding:9px 4px;text-align:center;"><div style="font-size:20px;font-weight:800;">'+v+'</div><div style="font-size:10px;color:var(--mut);">'+lb+'</div></div>'; }
      var bud=(j.budovy||[]).map(function(b){ return '🏫 '+esc(b.nazev)+' · '+b.mistnosti+' učeben'; }).join(' &nbsp;·&nbsp; ');
      dash.innerHTML='<div style="display:flex;gap:6px;flex-wrap:wrap;">'+kc(j.trid,"tříd")+kc(j.ucitelu,"učitelů")+kc(j.predmetu,"předmětů")+kc(j.mistnosti,"místností")+'</div>'+(bud?'<div style="margin-top:6px;font-size:11.5px;color:var(--mut);">'+bud+'</div>':'');
    });
  }
  function bk_tridy(){
    app.innerHTML=topbar("🏫 Třídy", true);
    var box=el('<div class="list"><div class="hint">Načítám…</div></div>'); app.appendChild(box);
    api("GET",_bkUrl("/api/v1/erp/app/bakalari/classes"),"").then(function(j){
      box.innerHTML="";
      if(!j||!j.ok||!(j.items&&j.items.length)){ box.appendChild(el('<div class="hint">Žádné třídy.</div>')); return; }
      j.items.forEach(function(c){
        var sub=(c.zaku?(c.zaku+" žáků"):"")+(c.tridni?((c.zaku?" · ":"")+"tř. uč. "+c.tridni):"");
        box.appendChild(row("🏫",(c.zkratka||c.nazev||c.kod),sub,function(){ window._bkTrid=c.kod; window._bkTridLbl=(c.zkratka||c.nazev||c.kod); go("bk_class"); }));
      });
    });
  }
  function bk_ucitele(){
    app.innerHTML=topbar("👩‍🏫 Učitelé", true);
    var box=el('<div class="list"><div class="hint">Načítám…</div></div>'); app.appendChild(box);
    api("GET",_bkUrl("/api/v1/erp/app/bakalari/teachers"),"").then(function(j){
      box.innerHTML="";
      if(!j||!j.ok||!(j.items&&j.items.length)){ box.appendChild(el('<div class="hint">Žádní učitelé.</div>')); return; }
      j.items.forEach(function(u){
        var nm=((u.prijmeni||"")+" "+(u.jmeno||"")).trim()||u.zkratka||u.kod;
        var sub=(u.zkratka?u.zkratka:"")+(u.hodin?((u.zkratka?" · ":"")+u.hodin+" h/týd"):"")+(u.aprobace?(" · "+u.aprobace):"");
        box.appendChild(row("👩‍🏫",nm,sub,function(){ window._bkUcit=u.kod; window._bkUcitLbl=nm; go("bk_teacher"); }));
      });
    });
  }
  function _bkGridHtml(j, mode){
    var mh=j.max_hod||0; if(mh<1) return '<div class="hint" style="margin:6px;">Pro tuto verzi nejsou hodiny umístěné.</div>';
    var dny=[1,2,3,4,5], dn={1:"Po",2:"Út",3:"St",4:"Čt",5:"Pá"};
    var map={}; (j.cells||[]).forEach(function(c){ var k=c.den+"_"+c.hod; (map[k]=map[k]||[]).push(c); });
    var pal=["#4f8ef7","#34d399","#a78bfa","#f59e0b","#ef4444","#06b6d4","#ec4899","#84cc16","#f97316","#14b8a6"];
    function colOf(s){ var h=0; s=s||""; for(var i=0;i<s.length;i++)h=(h*31+s.charCodeAt(i))%pal.length; return pal[h]; }
    var _z=window._bkZoom||1.2; var _fs=(11*_z).toFixed(1); var _mw=Math.round(58*_z);
    var h='<div style="overflow-x:auto;-webkit-overflow-scrolling:touch;padding:0 6px 20px;"><table style="border-collapse:collapse;width:100%;min-width:'+Math.round(340*_z)+'px;font-size:'+_fs+'px;">';
    h+='<tr><th style="width:20px;"></th>';
    dny.forEach(function(d){ h+='<th style="padding:4px;color:var(--mut);font-weight:700;">'+dn[d]+'</th>'; });
    h+='</tr>';
    var OFF=4, minH=99;
    (j.cells||[]).forEach(function(c){ if(c.hod<minH)minH=c.hod; });
    if(minH>mh) minH=1;
    for(var hod=minH;hod<=mh;hod++){
      h+='<tr><td style="text-align:center;color:var(--mut);font-weight:700;border-top:1px solid var(--bord);">'+(hod-OFF)+'</td>';
      dny.forEach(function(d){
        var arr=map[d+"_"+hod]||[];
        var inner=arr.map(function(c){
          var top, bot;
          if(mode==='class'){ top=c.pred||""; bot=(c.ucit||"")+(c.mist?(" · "+c.mist):""); }
          else if(mode==='room'){ top=c.trid||""; bot=(c.pred||"")+(c.ucit?(" · "+c.ucit):""); }
          else { top=c.trid||c.pred||""; bot=(c.pred||"")+(c.mist?(" · "+c.mist):""); }
          var col=colOf(c.pred||top);
          var sk=(mode==='class'&&c.skup)?(' <span style="opacity:.7;">'+esc(c.skup)+'</span>'):'';
          return '<div style="background:'+col+'22;border-left:3px solid '+col+';border-radius:4px;padding:2px 3px;margin:1px 0;line-height:1.25;"><b>'+esc(top)+'</b>'+sk+'<br><span style="opacity:.8;font-size:'+(9.5*_z).toFixed(1)+'px;">'+esc(bot)+'</span></div>';
        }).join("");
        h+='<td style="vertical-align:top;border-top:1px solid var(--bord);padding:1px;min-width:'+_mw+'px;">'+inner+'</td>';
      });
      h+='</tr>';
    }
    h+='</table></div>';
    return h;
  }
  function _bkRenderGrid(box, headerHtml, j, mode){
    if(window._bkZoom==null){ var z=parseFloat(localStorage.getItem('bkZoom')); window._bkZoom=(z&&z>=0.8&&z<=3)?z:1.2; }
    var bar='<div style="display:flex;align-items:center;gap:8px;margin:6px;">'+
      '<div class="hint" style="flex:1;margin:0;">'+(headerHtml||"")+'</div>'+
      '<button id="bkZm" style="width:36px;height:34px;border-radius:8px;border:1px solid var(--bord);background:rgba(255,255,255,.05);color:var(--tx);font-size:15px;font-weight:700;">A−</button>'+
      '<button id="bkZp" style="width:36px;height:34px;border-radius:8px;border:1px solid var(--bord);background:rgba(255,255,255,.05);color:var(--tx);font-size:18px;font-weight:700;">A+</button>'+
      '</div>';
    box.innerHTML=bar+_bkGridHtml(j,mode);
    function setZ(d){ window._bkZoom=Math.min(3,Math.max(0.8,(window._bkZoom||1.2)+d)); try{localStorage.setItem('bkZoom',window._bkZoom);}catch(e){} _bkRenderGrid(box,headerHtml,j,mode); }
    var bm=document.getElementById('bkZm'), bp=document.getElementById('bkZp');
    if(bm) bm.addEventListener('click',function(){ setZ(-0.2); });
    if(bp) bp.addEventListener('click',function(){ setZ(0.2); });
  }
  function bk_class(){
    app.innerHTML=topbar("🏫 "+(window._bkTridLbl||"Třída"), true);
    var box=el('<div><div class="hint" style="margin:6px;">Načítám rozvrh…</div></div>'); app.appendChild(box);
    api("GET",_bkUrl("/api/v1/erp/app/bakalari/class-grid?trid="+encodeURIComponent(window._bkTrid||"")),"").then(function(j){
      if(!j||!j.ok){ box.innerHTML='<div class="hint" style="margin:6px;">'+esc((j&&j.error)||"Chyba")+'</div>'; return; }
      _bkRenderGrid(box, esc(j.nazev||"")+' · verze rozvrhu '+esc(j.plat_od||""), j, 'class');
    });
  }
  function bk_teacher(){
    app.innerHTML=topbar("👩‍🏫 "+(window._bkUcitLbl||"Učitel"), true);
    var box=el('<div><div class="hint" style="margin:6px;">Načítám rozvrh…</div></div>'); app.appendChild(box);
    api("GET",_bkUrl("/api/v1/erp/app/bakalari/teacher-grid?ucit="+encodeURIComponent(window._bkUcit||"")),"").then(function(j){
      if(!j||!j.ok){ box.innerHTML='<div class="hint" style="margin:6px;">'+esc((j&&j.error)||"Chyba")+'</div>'; return; }
      _bkRenderGrid(box, esc(j.jmeno||"")+' · verze rozvrhu '+esc(j.plat_od||""), j, 'teacher');
    });
  }
  function bk_ucebny(){
    app.innerHTML=topbar("🚪 Obsazení učeben", true);
    var box=el('<div class="list"><div class="hint">Načítám…</div></div>'); app.appendChild(box);
    api("GET",_bkUrl("/api/v1/erp/app/bakalari/rooms"),"").then(function(j){
      box.innerHTML="";
      if(!j||!j.ok||!(j.items&&j.items.length)){ box.appendChild(el('<div class="hint">Žádné učebny.</div>')); return; }
      var curB=null;
      j.items.forEach(function(m){
        if(m.budova!==curB){ curB=m.budova; box.appendChild(el('<div style="margin:12px 8px 4px;font-size:12px;font-weight:700;color:#7c8cdb;">🏫 '+esc(curB||"—")+'</div>')); }
        var sub=(m.nazev||"")+(m.kapacita?(" · "+m.kapacita+" míst"):"")+(m.hodin?(" · "+m.hodin+" h/týd"):"");
        box.appendChild(row("🚪",(m.zkratka||m.kod),sub,function(){ window._bkMist=m.kod; window._bkMistLbl=(m.zkratka||m.kod)+(m.budova?(" · "+m.budova):""); go("bk_room"); }));
      });
    });
  }
  function bk_room(){
    app.innerHTML=topbar("🚪 "+(window._bkMistLbl||"Učebna"), true);
    var box=el('<div><div class="hint" style="margin:6px;">Načítám obsazení…</div></div>'); app.appendChild(box);
    api("GET",_bkUrl("/api/v1/erp/app/bakalari/room-grid?mist="+encodeURIComponent(window._bkMist||"")),"").then(function(j){
      if(!j||!j.ok){ box.innerHTML='<div class="hint" style="margin:6px;">'+esc((j&&j.error)||"Chyba")+'</div>'; return; }
      _bkRenderGrid(box, esc(j.nazev||"")+' · '+esc(j.budova||"")+' · verze '+esc(j.plat_od||""), j, 'room');
    });
  }
  var _bkUvazPo="";
  function bk_uvazky(){
    app.innerHTML=topbar("📋 Úvazky", true);
    app.appendChild(el('<div class="hint" style="margin:8px 6px;line-height:1.5;">Co který učitel učí — předměty, třídy a počet hodin týdně.</div>'));
    var bar=el('<div style="display:flex;gap:6px;flex-wrap:wrap;margin:0 6px 6px;"></div>'); app.appendChild(bar);
    var box=el('<div class="list"><div class="hint">Načítám…</div></div>'); app.appendChild(box);
    function load(po){
      box.innerHTML='<div class="hint">Načítám…</div>';
      var u=_bkUrl("/api/v1/erp/app/bakalari/loads"); if(po) u+=(u.indexOf("?")>=0?"&":"?")+"po="+encodeURIComponent(po);
      api("GET",u,"").then(function(j){
        box.innerHTML="";
        if(!j||!j.ok||!(j.items&&j.items.length)){ box.appendChild(el('<div class="hint">'+((j&&j.error==="forbidden")?"🔒 Vidí jen rodiče.":"Žádné úvazky.")+'</div>')); return; }
        _bkUvazPo=j.plat_od||po||"";
        // přepínač školních roků
        bar.innerHTML="";
        if((j.roky||[]).length>1){
          j.roky.forEach(function(r){
            var on=(r.po===_bkUvazPo);
            var b=el('<button style="border:1px solid '+(on?'var(--accent)':'var(--bord)')+';background:'+(on?'var(--accent)':'transparent')+';color:'+(on?'#06101f':'var(--tx)')+';border-radius:9px;padding:5px 12px;font-size:13px;font-weight:700;">'+esc(r.skolrok)+'</button>');
            b.onclick=function(){ load(r.po); };
            bar.appendChild(b);
          });
        }
        j.items.forEach(function(t){
          var card=el('<div style="background:rgba(255,255,255,.03);border:1px solid var(--bord);border-radius:12px;padding:10px 12px;margin:6px;"></div>');
          var head='<div style="display:flex;justify-content:space-between;gap:8px;align-items:baseline;margin-bottom:4px;"><b style="font-size:15px;">'+esc(t.jmeno)+'</b><span style="color:var(--green);font-weight:800;">'+t.total+' h/týd</span></div>';
          var lines=(t.items||[]).map(function(it){ return '<div style="display:flex;justify-content:space-between;gap:8px;font-size:13px;padding:2px 0;border-top:1px solid #1b2742;"><span style="flex:1;">'+esc(it.pred_nazev||it.pred)+(it.tridy?(' <span style="color:var(--mut);">'+esc(it.tridy)+'</span>'):'')+'</span><b>'+it.hodin+'</b></div>'; }).join("");
          card.innerHTML=head+lines;
          box.appendChild(card);
        });
      });
    }
    load(_bkUvazPo);
  }
  function bk_skola(){
    app.innerHTML=topbar("📊 Přehled školy", true);
    var box=el('<div style="padding-bottom:80px;"><div class="hint" style="margin:6px;">Načítám…</div></div>'); app.appendChild(box);
    api("GET",_bkUrl("/api/v1/erp/app/bakalari/skola"),"").then(function(j){
      if(!j||!j.ok){ box.innerHTML='<div class="hint" style="margin:6px;">'+esc((j&&j.error==="forbidden")?"🔒 Vidí jen vedení.":((j&&j.error)||"Chyba"))+'</div>'; return; }
      function kc(v,lb,col){ return '<div style="flex:1;min-width:92px;background:rgba(255,255,255,.03);border:1px solid var(--bord);border-radius:14px;padding:12px 8px;text-align:center;"><div style="font-size:25px;font-weight:800;color:'+(col||'var(--tx)')+';">'+v+'</div><div style="font-size:11px;color:var(--mut);margin-top:2px;">'+lb+'</div></div>'; }
      var html='<div class="hint" style="margin:6px;">Školní rok '+esc(j.skolrok||"")+' · provozní efektivita (živá data školy)</div>';
      html+='<div style="display:flex;gap:8px;flex-wrap:wrap;margin:0 6px;">'+kc(j.zaku,"žáků","#60a5fa")+kc(j.trid,"tříd")+kc(j.naplnenost_prum,"prům. ve třídě","var(--green)")+'</div>';
      html+='<div style="display:flex;gap:8px;flex-wrap:wrap;margin:8px 6px;">'+kc(j.ucitelu,"učitelů")+kc(j.uceben_vyuk+"/"+j.uceben,"vyučov. učeben")+kc(j.vyuziti_pct+"%","využití učeben","#a78bfa")+'</div>';
      html+='<div class="hint" style="margin:12px 6px 4px;font-weight:700;color:var(--tx);">Naplněnost tříd <span style="color:var(--mut);font-weight:400;">(min '+j.naplnenost_min+' · max '+j.naplnenost_max+')</span></div>';
      var mx=j.naplnenost_max||34;
      html+='<div style="margin:0 6px;">'+(j.tridy||[]).map(function(t){
        var w=Math.round(100*t.zaku/mx);
        return '<div style="display:flex;align-items:center;gap:8px;margin:3px 0;font-size:13px;"><span style="width:46px;font-weight:700;">'+esc(t.zkratka)+'</span><span style="flex:1;background:rgba(255,255,255,.05);border-radius:6px;height:16px;position:relative;overflow:hidden;"><span style="position:absolute;left:0;top:0;bottom:0;width:'+w+'%;background:linear-gradient(90deg,#4f8ef7,#34d399);"></span></span><b style="width:26px;text-align:right;">'+t.zaku+'</b></div>';
      }).join("")+'</div>';
      html+='<div class="hint" style="margin:14px 6px;line-height:1.5;font-size:11.5px;">Kapacita učeben celkem '+j.kapacita+' míst · '+j.hodin_tydne+' vyučovacích hodin týdně. Plné třídy a vysoké využití učeben = škola hospodaří s lidmi i prostorem efektivně. Brzy přibude ekonomika (rozpočet × čerpání × normativ na žáka).</div>';
      box.innerHTML=html;
    });
  }
  // Ops akce — provozní akce + historie spuštění s datumy (jen rodiče). Marti 13.6.
  function ops(){
    app.innerHTML=topbar("⚙️ Ops akce", true);
    app.appendChild(el('<div class="hint" style="margin:6px;line-height:1.5;">Provozní akce systému — co se dá spustit a kdy se to naposledy spouštělo. Spouští jen rodiče, vše se loguje (audit).</div>'));
    var lab={};
    function fmt(iso){ if(!iso) return ""; var d=new Date(iso); if(isNaN(d.getTime())) return String(iso).slice(0,16).replace("T"," "); return ("0"+d.getDate()).slice(-2)+"."+("0"+(d.getMonth()+1)).slice(-2)+". "+("0"+d.getHours()).slice(-2)+":"+("0"+d.getMinutes()).slice(-2); }
    function stMeta(st){ st=(st||"").toLowerCase(); if(st==="done"||st==="ok"||st==="finished") return {e:"✅",c:"#34d399"}; if(st==="error"||st==="failed"||st==="fail") return {e:"❌",c:"#f87171"}; if(st==="pending"||st==="ack") return {e:"⏳",c:"#fbbf24"}; return {e:"•",c:"var(--mut)"}; }
    app.appendChild(el('<div style="margin:14px 6px 6px;font-size:12px;font-weight:700;letter-spacing:.5px;color:#7c8cdb;">🕒 HISTORIE SPUŠTĚNÍ</div>'));
    var hist=el('<div class="list"><div class="hint">Načítám…</div></div>'); app.appendChild(hist);
    app.appendChild(el('<div style="margin:16px 6px 6px;font-size:12px;font-weight:700;letter-spacing:.5px;color:#7c8cdb;">▶️ SPUSTIT AKCI</div>'));
    var acts=el('<div class="list"><div class="hint">Načítám…</div></div>'); app.appendChild(acts);
    function loadLog(){
      api("GET","/api/v1/erp/app/ops/log","").then(function(j){
        hist.innerHTML="";
        if(!j||!j.ok){ hist.innerHTML='<div class="hint">'+((j&&j.error)?esc(j.error):"Vidí jen rodiče.")+'</div>'; return; }
        if(!j.log.length){ hist.innerHTML='<div class="hint">Zatím nic nespuštěno.</div>'; return; }
        j.log.forEach(function(r){
          var m=stMeta(r.status); var nm=lab[r.action_key]||r.action_key;
          var sub=fmt(r.created_at)+(r.requested_by_name?(" · "+r.requested_by_name):"")+(r.finished_at?(" · hotovo "+fmt(r.finished_at)):"")+(r.status?(" · "+r.status):"");
          var resu=(r.result?('<div style="font-size:11px;color:var(--mut);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">'+esc(String(r.result).slice(0,140))+'</div>'):'');
          hist.appendChild(el('<div style="display:flex;gap:9px;padding:9px 6px;border-bottom:1px solid var(--bord);"><span style="font-size:17px;">'+m.e+'</span><div style="flex:1;min-width:0;"><div style="font-size:14px;font-weight:600;">'+esc(nm)+'</div><div style="font-size:11.5px;color:'+m.c+';">'+esc(sub)+'</div>'+resu+'</div></div>'));
        });
      });
    }
    api("GET","/api/v1/erp/app/ops/actions","").then(function(j){
      acts.innerHTML="";
      if(!j||!j.ok){ acts.innerHTML='<div class="hint">Vidí jen rodiče.</div>'; loadLog(); return; }
      (j.actions||[]).forEach(function(a){ lab[a.action_key]=a.label; });
      (j.actions||[]).forEach(function(a){
        acts.appendChild(row("⚙️",a.label,"cíl: "+a.target,function(){
          if(!confirm("Spustit:\n"+a.label+"?")) return;
          api("POST","/api/v1/erp/app/ops/run",{action_key:a.action_key}).then(function(r){ alert(r&&r.ok?"Spuštěno ✓ (sleduj historii)":("Chyba: "+((r&&r.error)||"?"))); loadLog(); });
        }));
      });
      loadLog();
    });
  }

  // ─── Kára: produktivita člověka (motor + lopata + znalosti × výstup). Gated server-side. ───
  var KTRAITS=[["A","Stabilita"],["B","Pozitivnost"],["C","Klid"],["D","Jistota"],["E","Aktivita"],["F","Tah na bránu"],["G","Zodpovědnost"],["H","Správný odhad"],["I","Empatie"],["J","Komunikace"]];
  function _kZoneBg(z){ if(z==='striped') return 'repeating-linear-gradient(90deg,#f59e0b 0 7px,rgba(255,255,255,.25) 7px 11px)'; return z==='orange'?'#f59e0b':z==='gray'?'#9aa0aa':'#2a55c8'; }
  function _utest(traits,nl,nh){
    nl=(nl==null?-19:nl); nh=(nh==null?32:nh);
    var pct=function(v){ return ((Math.max(-100,Math.min(100,v))+100)/200*100); };
    var rows=traits.map(function(t){
      var has=(t.value!=null);
      return '<div style="display:flex;align-items:center;gap:8px;margin:5px 0;">'
        +'<div style="width:118px;flex:none;font-size:12px;line-height:1.15;"><b>'+esc(t.code)+' '+esc(t.label)+'</b><div style="color:var(--mut);font-size:10px;">'+esc(t.sublabel||"")+'</div></div>'
        +'<div style="flex:1;position:relative;height:22px;background:rgba(255,255,255,.05);border:1px solid var(--bord);border-radius:5px;overflow:hidden;">'
        +'<div style="position:absolute;top:0;bottom:0;left:'+pct(nl)+'%;width:1px;background:rgba(255,255,255,.28);"></div>'
        +'<div style="position:absolute;top:0;bottom:0;left:'+pct(nh)+'%;width:1px;background:rgba(255,255,255,.28);"></div>'
        +(has?'<div style="position:absolute;top:2px;bottom:2px;left:2px;width:calc('+pct(t.value)+'% - 4px);min-width:3px;background:'+_kZoneBg(t.zone)+';border-radius:4px;"></div>':'')
        +'</div>'
        +'<div style="width:34px;flex:none;text-align:right;font-weight:800;font-size:13px;">'+(has?t.value:'—')+'</div></div>';
    }).join("");
    return '<div style="margin:6px 0;"><div style="display:flex;font-size:10px;color:var(--mut);padding-left:126px;"><span style="flex:1;">−100</span><span>0</span><span style="flex:1;text-align:right;">+100</span></div>'+rows+'</div>';
  }
  function kara(){
    app.innerHTML=topbar("📊 Produktivita lidí", true);
    app.appendChild(el('<div class="hint" style="margin:6px;line-height:1.55;">Podklad pro rozvoj, ne ortel. <b>Motor</b> (co táhne) + <b>lopata</b> (osobnostní profil) + znalosti × <b>reálný výstup</b>. Vidí jen licencovaní a rodiče.</div>'));
    var add=el('<button style="margin:6px;padding:11px 16px;border:0;border-radius:12px;background:linear-gradient(110deg,#34d399,#2dd4bf);color:#04150e;font-weight:700;cursor:pointer;">+ Nové vyhodnocení</button>');
    add.addEventListener("click",function(){ go("kara_new"); });
    app.appendChild(add);
    var bd=el('<button style="margin:6px;padding:11px 16px;border:0;border-radius:12px;background:linear-gradient(110deg,#a78bfa,#7c5cff);color:#0c0820;font-weight:700;cursor:pointer;">📊 Žebříček (−100…+100)</button>');
    bd.addEventListener("click",function(){ go("kara_board"); });
    app.appendChild(bd);
    var box=el('<div class="list"><div class="hint">Načítám…</div></div>'); app.appendChild(box);
    api("GET","/api/v1/erp/app/kara/list","").then(function(j){
      box.innerHTML="";
      if(!j||!j.ok){ box.innerHTML='<div class="hint">'+((j&&j.error==="forbidden")?"🔒 Produktivitu vidí jen licencovaní konzultanti a rodiče.":"Nepodařilo se načíst.")+'</div>'; return; }
      if(!j.items.length){ box.innerHTML='<div class="hint">Zatím žádné vyhodnocení. Přidej první přes „+ Nové vyhodnocení".</div>'; return; }
      j.items.forEach(function(it){
        var sub=(it.test_type||"")+(it.project?(" · "+it.project):"")+(it.datum?(" · "+it.datum):"")+(it.kvadrant&&it.disclosed?(" · "+it.kvadrant):"");
        box.appendChild(row("📊",it.jmeno,sub,function(){ window._kAid=it.id; go("kara_detail"); }));
      });
    });
  }
  function _kPanel(title,html){ return '<div style="background:rgba(255,255,255,.03);border:1px solid var(--bord);border-radius:12px;padding:12px;margin:8px 6px;"><div style="font-weight:800;margin-bottom:6px;">'+title+'</div>'+html+'</div>'; }
  function kara_detail(){
    var aid=window._kAid;
    app.innerHTML=topbar("📊 Profil produktivity", true);
    var wrap=el('<div><div class="hint" style="margin:6px;">Načítám…</div></div>'); app.appendChild(wrap);
    api("GET","/api/v1/erp/app/kara/detail?aid="+aid,"").then(function(j){
      if(!j||!j.ok){ wrap.innerHTML='<div class="hint" style="margin:6px;">'+((j&&j.error==="forbidden")?"🔒 Nemáš přístup.":"Nepodařilo se načíst.")+'</div>'; return; }
      var h='<div style="margin:8px 6px;"><div style="font-size:20px;font-weight:800;">'+esc(j.jmeno)+'</div>'
        +'<div style="color:var(--mut);font-size:13px;">'+esc(j.test_type||"")+(j.project?(" · "+esc(j.project)):"")+(j.datum?(" · "+esc(j.datum)):"")+(j.perf_code?(" · kód "+esc(j.perf_code)):"")+'</div></div>';
      // Lopata = U-TEST graf
      h+=_kPanel("🛠 Lopata — osobnostní profil (EXEC-U-TEST)", _utest(j.traits,j.norm_low,j.norm_high));
      // Motor
      if(j.motive){ var m=j.motive;
        h+=_kPanel("🔋 Motor — co člověka pohání (nejdůležitější)",
          (m.strength!=null?('<div style="margin-bottom:4px;">Síla motoru: <b>'+m.strength+'</b>/100</div>'):'')
          +(m.drivers?('<div><span style="color:var(--mut);">Pohání ho:</span> '+esc(m.drivers)+'</div>'):'')
          +(m.enjoys?('<div><span style="color:var(--mut);">Baví ho:</span> '+esc(m.enjoys)+'</div>'):'')
          +(m.wants?('<div><span style="color:var(--mut);">Chce:</span> '+esc(m.wants)+'</div>'):'')
          +(m.align?('<div style="margin-top:4px;font-style:italic;">'+esc(m.align)+'</div>'):''));
      } else { h+=_kPanel("🔋 Motor","<div class=\"hint\">Zatím nezadáno. Motor je nejdůležitější faktor.</div>"); }
      // Provozni prehled (vystup)
      var ov='';
      if(j.output&&j.output.length){ ov=j.output.map(function(o){ return '<div>'+(o.quantity!=null?('<b>'+o.quantity+'</b> '+esc(o.unit||"")):'')+' '+esc(o.metric||"")+(o.od?(' · '+o.od+(o.do?("–"+o.do):"")):"")+'</div>'; }).join(""); }
      else ov='<div class="hint">Naše statistika zatím nenaběhla — výchozí číslo dají reference níže.</div>';
      h+=_kPanel("📈 Provozní přehled — reálný výstup (množství)", ov);
      // Reference (baseline)
      var rf='';
      if(j.references&&j.references.length){ rf=j.references.map(function(r){ return '<div style="border-top:1px solid var(--bord);padding:5px 0;"><b>'+esc(r.company||"?")+'</b>'+(r.role?(" · "+esc(r.role)):"")+(r.datum?(" · "+r.datum):"")+'<div style="font-size:12px;">'+(r.productivity!=null?('produktivita <b>'+r.productivity+'</b>'):'')+(r.hardworking!=null?(' · pracovitost '+r.hardworking+'/100'):'')+(r.rehire===true?' · vzal by znovu ✓':(r.rehire===false?' · znovu ne ✗':''))+'</div>'+(r.summary?('<div style="font-size:12px;color:var(--mut);">'+esc(r.summary)+'</div>'):'')+'</div>'; }).join(""); }
      else rf='<div class="hint">Žádná reference. U nového uchazeče volej ≥2 bývalé zaměstnavatele (Performia praxe).</div>';
      h+=_kPanel("📞 Ověření referencemi — výchozí číslo", rf);
      // Kvadrant
      h+=_kPanel("🧭 Zařazení (konzultant)", (j.kvadrant?('<div style="font-size:16px;font-weight:800;">'+esc(j.kvadrant)+'</div>'+(j.rationale?('<div style="font-size:12px;color:var(--mut);">'+esc(j.rationale)+'</div>'):'')+'<div style="font-size:11px;color:var(--mut);margin-top:3px;">'+(j.disclosed?"Sděleno hodnocenému":"Nesděleno hodnocenému")+'</div>'):'<div class="hint">Nezařazeno. Zařazení dělá konzultant ručně, ne algoritmus.</div>'));
      if(j.report_path) h+='<div style="margin:8px 6px;"><a href="'+esc(j.report_path)+'" target="_blank" style="color:#2dd4bf;font-weight:700;">📄 Otevřít originální report</a></div>';
      // akce
      h+='<div style="margin:8px 6px;display:flex;gap:8px;flex-wrap:wrap;">'
        +'<button id="kbMot" style="padding:9px 13px;border:1px solid var(--bord);border-radius:10px;background:rgba(255,255,255,.04);color:var(--tx);cursor:pointer;">+ Motor</button>'
        +'<button id="kbRef" style="padding:9px 13px;border:1px solid var(--bord);border-radius:10px;background:rgba(255,255,255,.04);color:var(--tx);cursor:pointer;">+ Reference</button>'
        +'<button id="kbQuad" style="padding:9px 13px;border:1px solid var(--bord);border-radius:10px;background:rgba(255,255,255,.04);color:var(--tx);cursor:pointer;">Zařadit</button></div>';
      h+='<div style="height:70px;"></div>';
      wrap.innerHTML=h;
      window._kSubj={kind:j.subject_kind,id:j.subject_id};
      var b1=document.getElementById("kbMot"); if(b1) b1.addEventListener("click",function(){ go("kara_motive"); });
      var b2=document.getElementById("kbRef"); if(b2) b2.addEventListener("click",function(){ go("kara_ref"); });
      var b3=document.getElementById("kbQuad"); if(b3) b3.addEventListener("click",function(){ go("kara_quad"); });
    });
  }
  function _kFld(label,id,ph,type){ return '<div style="margin:6px 0;"><div style="font-size:12px;color:var(--mut);margin-bottom:2px;">'+label+'</div><input id="'+id+'" type="'+(type||"text")+'" placeholder="'+(ph||"")+'" style="width:100%;box-sizing:border-box;padding:9px;border-radius:9px;border:1px solid var(--bord);background:rgba(255,255,255,.04);color:var(--tx);"></div>'; }
  function _kVal(id){ var e=document.getElementById(id); return e?e.value:""; }
  function kara_new(){
    app.innerHTML=topbar("+ Nové vyhodnocení", true);
    var c=el('<div style="margin:6px;"></div>');
    var zopt='<option value="blue">modrá</option><option value="orange">oranžová</option><option value="striped">oranžová šraf.</option><option value="gray">šedá</option>';
    var h='<div style="font-size:12px;color:var(--mut);margin-bottom:2px;">Subjekt</div>'
      +'<select id="kSk" style="width:100%;padding:9px;border-radius:9px;border:1px solid var(--bord);background:rgba(255,255,255,.04);color:var(--tx);"><option value="user">zaměstnanec (user id)</option><option value="candidate">uchazeč (candidate id)</option></select>';
    h+=_kFld("ID subjektu","kSid","např. 41","number");
    h+=_kFld("Projekt","kProj","Coffee break s jednatelem 2026");
    h+=_kFld("Kód Performia","kCode","KFF871C12FJ");
    h+=_kFld("Datum vyhodnocení","kDate","","date");
    h+='<label style="display:flex;gap:7px;align-items:center;margin:6px 0;font-size:13px;"><input type="checkbox" id="kConsent"> Souhlas zaměstnance s uložením (GDPR)</label>';
    h+='<div style="font-weight:800;margin:10px 0 4px;">Hodnoty A–J (−100…+100) + zóna</div>';
    KTRAITS.forEach(function(t){
      h+='<div style="display:flex;gap:7px;align-items:center;margin:3px 0;"><div style="width:120px;font-size:12px;"><b>'+t[0]+'</b> '+t[1]+'</div>'
        +'<input id="kv_'+t[0]+'" type="number" min="-100" max="100" style="width:70px;padding:7px;border-radius:8px;border:1px solid var(--bord);background:rgba(255,255,255,.04);color:var(--tx);">'
        +'<select id="kz_'+t[0]+'" style="flex:1;padding:7px;border-radius:8px;border:1px solid var(--bord);background:rgba(255,255,255,.04);color:var(--tx);">'+zopt+'</select></div>';
    });
    h+='<button id="kSave" style="margin:12px 0;padding:11px 18px;border:0;border-radius:12px;background:linear-gradient(110deg,#34d399,#2dd4bf);color:#04150e;font-weight:700;cursor:pointer;">Uložit profil</button>';
    h+='<div id="kMsg" class="hint"></div>';
    c.innerHTML=h; app.appendChild(c);
    document.getElementById("kSave").addEventListener("click",function(){
      var vals=KTRAITS.map(function(t){ var v=_kVal("kv_"+t[0]); return v===""?null:{trait:t[0],value:parseInt(v,10),zone:_kVal("kz_"+t[0])}; }).filter(function(x){return x;});
      var sid=parseInt(_kVal("kSid"),10);
      if(!sid){ document.getElementById("kMsg").textContent="Zadej ID subjektu."; return; }
      var payload={subject_kind:_kVal("kSk"),subject_id:sid,project:_kVal("kProj"),perf_code:_kVal("kCode"),assessed_on:(_kVal("kDate")||null),consent_given:document.getElementById("kConsent").checked,values:vals};
      api("POST","/api/v1/erp/app/kara/create",payload).then(function(r){
        if(r&&r.ok){ window._kAid=r.id; go("kara_detail"); } else { document.getElementById("kMsg").textContent="Chyba: "+((r&&r.error)||"?"); }
      });
    });
  }
  function kara_motive(){
    app.innerHTML=topbar("🔋 Motor", true);
    var c=el('<div style="margin:6px;"></div>');
    var h='<div class="hint" style="margin-bottom:6px;">Motor je nejdůležitější — co člověka pohání, baví, co chce.</div>';
    h+=_kFld("Co ho pohání (drivers)","mDr");
    h+=_kFld("Co ho baví (enjoys)","mEn");
    h+=_kFld("Co chce (wants)","mWa");
    h+=_kFld("Síla motoru 0–100","mSt","","number");
    h+=_kFld("Jak ladí s rolí / lopatou","mAl");
    h+='<button id="mSave" style="margin:10px 0;padding:11px 18px;border:0;border-radius:12px;background:linear-gradient(110deg,#34d399,#2dd4bf);color:#04150e;font-weight:700;cursor:pointer;">Uložit motor</button><div id="mMsg" class="hint"></div>';
    c.innerHTML=h; app.appendChild(c);
    document.getElementById("mSave").addEventListener("click",function(){
      var sj=window._kSubj||{};
      api("POST","/api/v1/erp/app/kara/motive",{subject_kind:sj.kind,subject_id:sj.id,drivers:_kVal("mDr"),enjoys:_kVal("mEn"),wants:_kVal("mWa"),strength:_kVal("mSt"),alignment_note:_kVal("mAl")}).then(function(r){
        if(r&&r.ok){ go("kara_detail"); } else document.getElementById("mMsg").textContent="Chyba: "+((r&&r.error)||"?");
      });
    });
  }
  function kara_ref(){
    app.innerHTML=topbar("📞 Reference", true);
    var c=el('<div style="margin:6px;"></div>');
    var h='<div class="hint" style="margin-bottom:6px;">Telefonát na bývalého zaměstnavatele (Šárka). U nového uchazeče ≥2 reference = výchozí číslo.</div>';
    h+=_kFld("Firma","rCo"); h+=_kFld("Pozice / vztah","rRole"); h+=_kFld("Kontakt","rContact");
    h+=_kFld("Produktivita (otevřené číslo)","rProd","","number");
    h+=_kFld("Pracovitost 0–100","rHard","","number");
    h+=_kFld("Shrnutí rozhovoru","rSum");
    h+='<label style="display:flex;gap:7px;align-items:center;margin:6px 0;font-size:13px;"><input type="checkbox" id="rRehire"> Vzal by znovu</label>';
    h+='<button id="rSave" style="margin:10px 0;padding:11px 18px;border:0;border-radius:12px;background:linear-gradient(110deg,#34d399,#2dd4bf);color:#04150e;font-weight:700;cursor:pointer;">Uložit referenci</button><div id="rMsg" class="hint"></div>';
    c.innerHTML=h; app.appendChild(c);
    document.getElementById("rSave").addEventListener("click",function(){
      var sj=window._kSubj||{};
      api("POST","/api/v1/erp/app/kara/reference",{subject_kind:sj.kind,subject_id:sj.id,referee_company:_kVal("rCo"),referee_role:_kVal("rRole"),referee_contact:_kVal("rContact"),productivity:_kVal("rProd"),hardworking:_kVal("rHard"),summary:_kVal("rSum"),reached:true,would_rehire:document.getElementById("rRehire").checked}).then(function(r){
        if(r&&r.ok){ go("kara_detail"); } else document.getElementById("rMsg").textContent="Chyba: "+((r&&r.error)||"?");
      });
    });
  }
  function kara_quad(){
    app.innerHTML=topbar("🧭 Zařazení", true);
    var c=el('<div style="margin:6px;"></div>');
    var h='<div class="hint" style="margin-bottom:6px;">Zařazení dělá konzultant ručně se zdůvodněním (ne algoritmus). Sdělení hodnocenému je metodická volba.</div>';
    h+='<div style="font-size:12px;color:var(--mut);">Kvadrant</div><select id="qCode" style="width:100%;padding:9px;border-radius:9px;border:1px solid var(--bord);background:rgba(255,255,255,.04);color:var(--tx);"><option value="tahoun">Tahoun</option><option value="efektivni">Efektivní</option><option value="rozvoj">Rozvoj</option><option value="prostor">Prostor pro změnu</option></select>';
    h+=_kFld("Zdůvodnění","qR");
    h+='<label style="display:flex;gap:7px;align-items:center;margin:6px 0;font-size:13px;"><input type="checkbox" id="qDisc"> Sdělit hodnocenému</label>';
    h+='<button id="qSave" style="margin:10px 0;padding:11px 18px;border:0;border-radius:12px;background:linear-gradient(110deg,#34d399,#2dd4bf);color:#04150e;font-weight:700;cursor:pointer;">Uložit zařazení</button><div id="qMsg" class="hint"></div>';
    c.innerHTML=h; app.appendChild(c);
    document.getElementById("qSave").addEventListener("click",function(){
      api("POST","/api/v1/erp/app/kara/quadrant",{aid:window._kAid,quadrant_code:_kVal("qCode"),rationale:_kVal("qR"),disclosed:document.getElementById("qDisc").checked}).then(function(r){
        if(r&&r.ok){ go("kara_detail"); } else document.getElementById("qMsg").textContent="Chyba: "+((r&&r.error)||"?");
      });
    });
  }
  // Overdrive popup: nad +100 % se dá přetáhnout do 500 % (✈️ Letadlo) a nad 500 % (🚀 Raketa)
  function karaOverdrive(cur, cb){
    var val=Math.max(100,Math.min(1000,cur||100));
    function emo(v){ return v>500?"🚀":(v>200?"✈️":"🐎"); }
    function lab(v){ return v>500?"Raketa — nad 500 %!":(v>200?"Letadlo (200–500 %)":"Zlatý tahoun (100–200 %)"); }
    var ov=document.createElement("div");
    ov.style.cssText="position:fixed;inset:0;z-index:200;background:rgba(2,4,10,.82);display:flex;align-items:center;justify-content:center;padding:18px;";
    var card=document.createElement("div");
    card.style.cssText="width:100%;max-width:380px;background:#0e1730;border:1px solid #2a55c8;border-radius:18px;padding:22px;text-align:center;";
    card.innerHTML='<div style="font-size:12px;color:#8ea0c4;font-weight:700;letter-spacing:1px;text-transform:uppercase;">Overdrive nad 100 %</div>'
      +'<div id="ovEmo" style="font-size:64px;line-height:1.1;margin:8px 0;">'+emo(val)+'</div>'
      +'<div id="ovLab" style="font-weight:800;font-size:18px;margin-bottom:4px;">'+lab(val)+'</div>'
      +'<div id="ovNum" style="font-size:30px;font-weight:900;color:#7dd3fc;">'+val+' %</div>'
      +'<input id="ovRange" type="range" min="100" max="1000" step="10" value="'+val+'" style="width:100%;margin:16px 0;accent-color:#7c5cff;">'
      +'<div style="display:flex;justify-content:space-between;font-size:11px;color:#8ea0c4;"><span>100 %</span><span>500 %</span><span>1000 %</span></div>'
      +'<div style="display:flex;gap:8px;margin-top:16px;"><button id="ovCancel" style="flex:1;padding:11px;border:1px solid #2a55c8;border-radius:11px;background:transparent;color:#e8eefc;cursor:pointer;">Zrušit</button>'
      +'<button id="ovOk" style="flex:1;padding:11px;border:0;border-radius:11px;background:linear-gradient(110deg,#7dd3fc,#7c5cff);color:#0c0820;font-weight:800;cursor:pointer;">Nastavit</button></div>';
    ov.appendChild(card); document.body.appendChild(ov);
    var rng=card.querySelector("#ovRange");
    rng.addEventListener("input",function(){ var v=parseInt(rng.value,10); card.querySelector("#ovEmo").textContent=emo(v); card.querySelector("#ovLab").textContent=lab(v); card.querySelector("#ovNum").textContent=v+" %"; });
    card.querySelector("#ovCancel").addEventListener("click",function(){ document.body.removeChild(ov); });
    card.querySelector("#ovOk").addEventListener("click",function(){ var v=parseInt(rng.value,10); document.body.removeChild(ov); if(cb)cb(v); });
  }
  // Kára naživo: žebříček lidí na škále −100…+100 → 4 pásma (+ overdrive nad 100 %)
  function _kbEmo(v){ if(v==null)return"·"; if(v>500)return"🚀"; if(v>100)return"✈️"; if(v>=50)return"💪"; if(v>=0)return"✅"; if(v>=-49)return"🌱"; return"🧭"; }
  function _kbCol(v){ if(v==null)return"#667"; if(v>500)return"#f0abfc"; if(v>100)return"#7dd3fc"; if(v>=50)return"#34d399"; if(v>=0)return"#60a5fa"; if(v>=-49)return"#fbbf24"; return"#f87171"; }
  function _kbLab(v){ if(v==null)return"Nezařazeno"; if(v>500)return"Raketa"; if(v>100)return"Letadlo"; if(v>=50)return"Tahoun"; if(v>=0)return"Efektivní"; if(v>=-49)return"Rozvoj"; return"Prostor pro změnu"; }
  function karaSet(uid,name,cur,after){
    var val=(cur==null?0:cur);
    var ov=document.createElement("div");
    ov.style.cssText="position:fixed;inset:0;z-index:200;background:rgba(2,4,10,.82);display:flex;align-items:center;justify-content:center;padding:18px;";
    var card=document.createElement("div");
    card.style.cssText="width:100%;max-width:380px;background:#0e1730;border:1px solid #2a55c8;border-radius:18px;padding:22px;text-align:center;";
    card.innerHTML='<div style="font-size:14px;color:#cdd6e2;font-weight:700;">'+esc(name)+'</div>'
      +'<div id="ksEmo" style="font-size:60px;line-height:1.1;margin:6px 0;">'+_kbEmo(val)+'</div>'
      +'<div id="ksLab" style="font-weight:800;font-size:18px;">'+_kbLab(val)+'</div>'
      +'<div id="ksNum" style="font-size:30px;font-weight:900;margin-top:2px;color:'+_kbCol(val)+';">'+val+' %</div>'
      +'<input id="ksRng" type="range" min="-100" max="1000" step="5" value="'+val+'" style="width:100%;margin:16px 0;accent-color:#7c5cff;">'
      +'<div style="display:flex;justify-content:space-between;font-size:10px;color:#8ea0c4;"><span>−100</span><span>0</span><span>100</span><span>500</span><span>1000</span></div>'
      +'<div style="display:flex;gap:8px;margin-top:16px;"><button id="ksC" style="flex:1;padding:11px;border:1px solid #2a55c8;border-radius:11px;background:transparent;color:#e8eefc;cursor:pointer;">Zrušit</button>'
      +'<button id="ksO" style="flex:1;padding:11px;border:0;border-radius:11px;background:linear-gradient(110deg,#a78bfa,#7c5cff);color:#0c0820;font-weight:800;cursor:pointer;">Uložit</button></div>';
    ov.appendChild(card); document.body.appendChild(ov);
    var rng=card.querySelector("#ksRng");
    rng.addEventListener("input",function(){ var v=parseInt(rng.value,10); card.querySelector("#ksEmo").textContent=_kbEmo(v); card.querySelector("#ksLab").textContent=_kbLab(v); var n=card.querySelector("#ksNum"); n.textContent=v+" %"; n.style.color=_kbCol(v); });
    card.querySelector("#ksC").addEventListener("click",function(){ document.body.removeChild(ov); });
    card.querySelector("#ksO").addEventListener("click",function(){ var v=parseInt(rng.value,10); api("POST","/api/v1/erp/app/kara/score",{subject_kind:"user",subject_id:uid,value:v}).then(function(r){ document.body.removeChild(ov); if(r&&r.ok&&after)after(); }); });
  }
  function kara_board(){
    app.innerHTML=topbar("📊 Produktivita lidí", true);
    app.appendChild(el('<div class="hint" style="margin:6px;line-height:1.5;">Individuální ukazatel u každého člověka: −100…+100 (a výš — ✈️ Letadlo nad 100 %, 🚀 Raketa nad 500 %). Ťukni na člověka a nastav.</div>'));
    var sb=el('<input placeholder="Hledat člověka…" style="width:calc(100% - 12px);margin:6px;padding:10px;border-radius:10px;border:1px solid var(--bord);background:rgba(255,255,255,.04);color:var(--tx);box-sizing:border-box;">');
    app.appendChild(sb);
    var box=el('<div class="list"><div class="hint">Načítám…</div></div>'); app.appendChild(box);
    function load(){
      var q=(sb.value||"").trim();
      api("GET","/api/v1/erp/app/kara/people"+(q?("?q="+encodeURIComponent(q)):""),"").then(function(j){
        box.innerHTML="";
        if(!j||!j.ok){ box.innerHTML='<div class="hint">'+((j&&j.error==="forbidden")?"🔒 Vidí jen licencovaní a rodiče.":"Nepodařilo se načíst.")+'</div>'; return; }
        if(!j.items.length){ box.innerHTML='<div class="hint">Nikdo nenalezen.</div>'; return; }
        j.items.forEach(function(p){
          var v=p.value, has=(v!=null);
          var w=has?((Math.max(-100,Math.min(100,v))+100)/200*100):0;
          var row=el('<div style="display:flex;align-items:center;gap:10px;padding:9px 6px;border-bottom:1px solid var(--bord);cursor:pointer;"><div style="font-size:20px;width:26px;text-align:center;">'+_kbEmo(v)+'</div><div style="flex:1;min-width:0;"><div style="font-size:14px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">'+esc(p.jmeno)+'</div><div style="position:relative;height:7px;background:rgba(255,255,255,.06);border-radius:4px;margin-top:4px;"><div style="position:absolute;left:50%;top:0;bottom:0;width:1px;background:rgba(255,255,255,.2);"></div>'+(has?'<div style="position:absolute;left:1px;top:1px;bottom:1px;width:calc('+w+'% - 2px);background:'+_kbCol(v)+';border-radius:3px;"></div>':'')+'</div></div><div style="width:54px;text-align:right;font-weight:800;color:'+_kbCol(v)+';">'+(has?(v+" %"):"—")+'</div></div>');
          row.addEventListener("click",function(){ karaSet(p.user_id,p.jmeno,v,load); });
          box.appendChild(row);
        });
      });
    }
    var _qt=null; sb.addEventListener("input",function(){ clearTimeout(_qt); _qt=setTimeout(load,250); });
    load();
  }
  // Marti 11.6.: HR rozcestník — self-service osobních údajů (každý) + správa
  // skupiny HR / přístupů k personálním složkám (rodiče).
  // Marti 13.6.: HR shora dolů — dva světy personalistiky: INTERNÍ (naši lidé:
  // firma → skupiny → jednotlivci → režim/podmínky/docházka) a EXTERNÍ (nábor).
  function _hrSec(t){ return el('<div style="margin:15px 6px 6px;font-size:12px;font-weight:700;letter-spacing:.5px;color:#7c8cdb;">'+esc(t)+'</div>'); }
  function hrSoon(t,d){ window._soonT=t; window._soonD=d||""; go("hr_soon"); }
  function hr_soon(){
    app.innerHTML=topbar(window._soonT||"Připravujeme", true);
    var p=el('<div class="panel" style="margin:10px;"></div>');
    p.innerHTML='<div style="font-size:18px;font-weight:800;margin-bottom:6px;">🚧 '+esc(window._soonT||"")+'</div>'
      +'<div class="hint" style="line-height:1.6;">'+esc(window._soonD||"Tato část je v přípravě — kostra hotová, obsah doplníme.")+'</div>';
    app.appendChild(p);
  }
  // 👥 HR hub pro Šárku (Marti 23.6.2026) — vzor sekce Vedení: nadpisy skupin + ikonky.
  // Šárčina sekce, s Claudem-25 si ji upravuje. Server-side ACL _hr_can_manage (rodiče + HR skupina).
