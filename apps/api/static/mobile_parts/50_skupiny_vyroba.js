  function moje_podminky(){
    app.innerHTML=topbar("📋 Moje podmínky", true);
    var box=el('<div class="panel"></div>'); app.appendChild(box); box.innerHTML='<div class="hint">Načítám…</div>';
    api("GET","/api/v1/erp/app/my-conditions","").then(function(j){
      box.innerHTML="";
      if(!j||!j.ok){ box.appendChild(el('<div class="hint">Nelze načíst.</div>')); return; }
      box.appendChild(el('<div class="hint" style="margin-bottom:10px;line-height:1.5;">Tvoje skupina: <b style="color:#e8eefc;">'+esc(j.skupina||"—")+'</b>. Tohle jsou podmínky, co aktuálně platí pro tebe — ze skupiny a případné osobní výjimky.</div>'));
      (j.podminky||[]).forEach(function(p){
        var sc={"osobní":"#fbbf24","skupina":"#60a5fa","systém":"#9aa"}[p.src]||"#9aa";
        box.appendChild(el('<div style="display:flex;align-items:center;gap:10px;padding:10px 4px;border-bottom:1px solid #1b2742;"><div style="flex:1;min-width:0;">'+esc(p.label)+(p.unit?(' <span class="hint">('+esc(p.unit)+')</span>'):'')+'</div><div style="font-weight:700;font-size:16px;">'+esc(p.value)+'</div><span style="font-size:10px;color:'+sc+';min-width:42px;text-align:right;">'+esc(p.src)+'</span></div>'));
      });
      if(!(j.podminky||[]).length) box.appendChild(el('<div class="hint">Zatím nic nastaveného.</div>'));
      box.appendChild(el('<div style="height:60px;"></div>'));
    });
  }
  function kdekdo(){
    app.innerHTML=topbar("👀 Kdo kde", true);
    // skupiny: key, label, barva, ikona
    var GRP=[["prace","V práci","#34d399","👷"],["homeoffice","Home office","#60a5fa","🏠"],
             ["vacation","Na dovolené","#fbbf24","🏝️"],["sick","Nemocní","#f87171","🤒"],
             ["medical","U lékaře","#f59e0b","🩺"],["family_care","OČR","#a78bfa","👶"],
             ["unpaid","Volno","#9aa","🚫"],["nic","Nezadáno","#667","—"]];
    var cur=new Date(); var _kk={f:"vse",data:[]};
    var bar=el('<div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;"></div>');
    var prev=el('<button class="ghost" style="padding:8px 12px;">‹</button>');
    var lbl=el('<div style="flex:1;text-align:center;font-weight:700;"></div>');
    var next=el('<button class="ghost" style="padding:8px 12px;">›</button>');
    bar.appendChild(prev); bar.appendChild(lbl); bar.appendChild(next);
    app.appendChild(bar);
    // STANDARD TEMPLATE: levý orámovaný přehled + pravá 72px lišta ikon
    var pane=el('<div style="display:flex;gap:10px;height:calc(64vh - 86px);align-items:stretch;">'
      +'<div style="flex:1;min-width:0;overflow-y:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none;border:1px solid var(--bord);border-radius:12px;background:rgba(255,255,255,0.02);padding:2px 8px;"><ul id="kkList" style="padding:0;list-style:none;margin:0;"></ul></div>'
      +'<div id="kkRail" style="width:72px;flex:none;overflow-y:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none;display:flex;flex-direction:column;gap:7px;padding:0;"></div></div>');
    app.appendChild(pane);
    function iso(d){ return d.getFullYear()+"-"+("0"+(d.getMonth()+1)).slice(-2)+"-"+("0"+d.getDate()).slice(-2); }
    function czlbl(d){ var dny=["neděle","pondělí","úterý","středa","čtvrtek","pátek","sobota"];
      var t=new Date(); t.setHours(0,0,0,0); var x=new Date(d); x.setHours(0,0,0,0);
      var diff=Math.round((x-t)/86400000); var suf=diff===0?" (dnes)":diff===-1?" (včera)":diff===1?" (zítra)":"";
      return dny[d.getDay()]+" "+d.getDate()+"."+(d.getMonth()+1)+"."+suf; }
    function gMeta(k){ for(var i=0;i<GRP.length;i++) if(GRP[i][0]===k) return GRP[i]; return ["nic","—","#667","—"]; }
    function cnt(k){ return k==="vse"?_kk.data.length:_kk.data.filter(function(p){return p.kind===k;}).length; }
    function railBtn(icon,label,key,color){
      var on=(_kk.f===key); var c=cnt(key);
      var amb=(key!=="prace"&&key!=="vse");
      var bdg=(c>0)?'<span style="position:absolute;top:4px;right:6px;min-width:17px;height:17px;line-height:15px;border-radius:9px;border:1px solid rgba(0,0,0,.25);background:'+(amb?"var(--amber)":"var(--green)")+';color:#241a02;font-size:10px;font-weight:700;padding:0 3px;box-sizing:border-box;text-align:center;">'+c+'</span>':'';
      var b=el('<button style="position:relative;width:100%;box-sizing:border-box;margin:0;padding:11px 2px;font-size:10.5px;line-height:1.15;display:flex;flex-direction:column;align-items:center;gap:4px;border:1px solid '+(on?"var(--green)":"var(--bord)")+';background:'+(on?"var(--green)":"rgba(255,255,255,0.02)")+';color:'+(on?"#04150e":"var(--mut)")+';border-radius:13px;cursor:pointer;"><span style="font-size:26px;line-height:1;">'+icon+'</span>'+label+bdg+'</button>');
      b.addEventListener("click",function(){ _kk.f=key; render(); });
      return b;
    }
    function render(){
      var rail=document.getElementById("kkRail"); var ul=document.getElementById("kkList");
      if(!rail||!ul) return;
      rail.innerHTML=""; rail.appendChild(railBtn("📋","Vše","vse"));
      GRP.forEach(function(g){ if(cnt(g[0])>0) rail.appendChild(railBtn(g[3],g[1],g[0],g[2])); });
      ul.innerHTML="";
      function liPerson(p){ var g=gMeta(p.kind);
        return el('<li style="border:none;padding:7px 4px;border-bottom:1px solid #1b2742;display:flex;align-items:center;gap:8px;"><span style="font-size:16px;">'+g[3]+'</span><span style="flex:1;">'+esc(p.jmeno)+'</span><span class="hint" style="color:'+g[2]+';">'+esc(p.label)+'</span></li>'); }
      if(_kk.f==="vse"){
        var any=false;
        GRP.forEach(function(g){ var arr=_kk.data.filter(function(p){return p.kind===g[0];}); if(!arr.length) return; any=true;
          ul.appendChild(el('<li style="border:none;padding:9px 2px 3px;font-weight:700;color:'+g[2]+';">'+g[3]+' '+esc(g[1])+' · '+arr.length+'</li>'));
          arr.forEach(function(p){ ul.appendChild(liPerson(p)); }); });
        if(!any) ul.appendChild(el('<li style="border:none;color:var(--mut);">Žádná data pro tento den.</li>'));
      } else {
        var arr=_kk.data.filter(function(p){return p.kind===_kk.f;});
        if(!arr.length) ul.appendChild(el('<li style="border:none;color:var(--mut);">Nikdo.</li>'));
        else arr.forEach(function(p){ ul.appendChild(liPerson(p)); });
      }
    }
    function load(){
      lbl.textContent=czlbl(cur);
      var ul=document.getElementById("kkList"); if(ul) ul.innerHTML='<li style="border:none;color:var(--mut);">Načítám…</li>';
      api("GET","/api/v1/erp/app/attendance/whereabouts?den="+iso(cur),"").then(function(j){
        _kk.data=(j&&j.ok&&j.lide)||[]; render();
      });
    }
    prev.addEventListener("click",function(){ cur.setDate(cur.getDate()-1); load(); });
    next.addEventListener("click",function(){ cur.setDate(cur.getDate()+1); load(); });
    load();
  }
  function absence(){
    app.innerHTML=topbar("🗓️ Absence", true);
    var TYPY=[["vacation","Dovolená"],["homeoffice","Home office"],["medical","Lékař"],["family_care","OČR"],["sick","Nemoc (PN)"],["unpaid","Neplacené volno"]];
    var TL={vacation:"Dovolená",homeoffice:"Home office",medical:"Lékař",family_care:"OČR",sick:"Nemoc (PN)",unpaid:"Neplacené volno"};
    var stavChip={pending:["čeká","#60a5fa"],approved:["schváleno","#34d399"],rejected:["zamítnuto","#f87171"],info:["info","#fbbf24"],cancelled:["zrušeno","#9aa4b2"]};
    function chip(t,c){ return '<span style="background:'+c+';color:#04150e;border-radius:8px;padding:2px 7px;font-size:11px;font-weight:700;">'+esc(t)+'</span>'; }
    function cz(d){ var p=(d||"").split("-"); return p.length===3?(p[2]+"."+p[1]+"."):d; }
    var t=new Date(); var today=t.getFullYear()+"-"+("0"+(t.getMonth()+1)).slice(-2)+"-"+("0"+t.getDate()).slice(-2);
    // ── Nová žádost ──
    var nf=el('<div style="border:1px solid #2b3a5c;border-radius:12px;padding:12px;margin-bottom:14px;"></div>');
    var w=el('<div></div>');
    function selOpts(opts){ return opts.map(function(o){ return '<option value="'+o[0]+'">'+esc(o[1])+'</option>'; }).join(''); }
    w.innerHTML='<div style="font-weight:700;margin-bottom:6px;">Nová žádost</div>'
      +'<label class="hint" style="display:block;margin:4px 0 2px;">Typ</label>'
      +'<select id="abTyp" style="width:100%;padding:9px;border-radius:9px;border:1px solid #2b3a5c;background:#0a1226;color:#e8eefc;">'+selOpts(TYPY)+'</select>'
      +'<div style="display:flex;gap:8px;"><div style="flex:1;"><label class="hint" style="display:block;margin:6px 0 2px;">Od</label><input id="abOd" type="date" value="'+today+'" style="width:100%;box-sizing:border-box;padding:9px;border-radius:9px;border:1px solid #2b3a5c;background:#0a1226;color:#e8eefc;"></div>'
      +'<div style="flex:1;"><label class="hint" style="display:block;margin:6px 0 2px;">Do</label><input id="abDo" type="date" value="'+today+'" style="width:100%;box-sizing:border-box;padding:9px;border-radius:9px;border:1px solid #2b3a5c;background:#0a1226;color:#e8eefc;"></div></div>'
      +'<label class="hint" style="display:block;margin:6px 0 2px;">Hodin/den</label><input id="abH" type="number" step="0.5" value="8" style="width:100%;box-sizing:border-box;padding:9px;border-radius:9px;border:1px solid #2b3a5c;background:#0a1226;color:#e8eefc;">'
      +'<input id="abNote" type="text" placeholder="Poznámka pro vedoucího (volitelné)" style="width:100%;box-sizing:border-box;padding:9px;border-radius:9px;border:1px solid #2b3a5c;background:#0a1226;color:#e8eefc;margin-top:8px;">';
    nf.appendChild(w);
    var sb=el('<button class="green full" style="margin-top:10px;">Odeslat vedoucímu</button>');
    var sst=el('<div class="hint" style="margin-top:6px;"></div>');
    sb.addEventListener("click",function(){
      sb.disabled=true; sst.textContent="Odesílám…";
      api("POST","/api/v1/erp/app/attendance/absence/request",{typ:w.querySelector('#abTyp').value,
        od:w.querySelector('#abOd').value, do:w.querySelector('#abDo').value,
        hours_per_day:parseFloat(w.querySelector('#abH').value)||8, note:w.querySelector('#abNote').value}).then(function(r){
          sb.disabled=false; sst.textContent=(r&&r.ok)?"✅ Odesláno vedoucímu":("✗ "+((r&&r.error)||"chyba"));
          if(r&&r.ok){ w.querySelector('#abNote').value=""; loadMine(); }
        });
    });
    nf.appendChild(sb); nf.appendChild(sst);
    app.appendChild(nf);
    // ── Ke schválení (vedoucí) ──
    var inbox=el('<div style="margin-bottom:14px;"></div>'); app.appendChild(inbox);
    function loadInbox(){
      api("GET","/api/v1/erp/app/attendance/absence/inbox","").then(function(j){
        inbox.innerHTML="";
        if(!j||!j.ok||!j.zadosti||!j.zadosti.length) return;
        inbox.appendChild(el('<div style="font-weight:700;margin-bottom:6px;">📥 Ke schválení ('+j.zadosti.length+')</div>'));
        j.zadosti.forEach(function(z){
          var row=el('<div style="border:1px solid #2b3a5c;border-radius:12px;padding:11px;margin-bottom:9px;"></div>');
          row.appendChild(el('<div><b>'+esc(z.zadatel)+'</b> — '+esc(z.typ_label)+' '+cz(z.od)+(z.od!==z.do?("–"+cz(z.do)):"")+' <span class="hint">('+z.hpd+' h/den)</span>'+(z.note?('<br><span class="hint">„'+esc(z.note)+'“</span>'):'')+'</div>'));
          var btns=el('<div style="display:flex;flex-direction:column;gap:6px;margin-top:8px;"></div>');
          (j.statusy||[]).forEach(function(stx){
            var b=el('<button class="ghost" style="text-align:left;padding:8px 10px;font-size:13px;">„'+esc(stx)+'“</button>');
            b.addEventListener("click",function(){
              b.disabled=true;
              api("POST","/api/v1/erp/app/attendance/absence/decide",{req_id:z.id,status_text:stx}).then(function(r){
                if(r&&r.ok){ loadInbox(); loadMine(); } else { b.disabled=false; alert("Chyba: "+((r&&r.error)||"?")); }
              });
            });
            btns.appendChild(b);
          });
          row.appendChild(btns); inbox.appendChild(row);
        });
      });
    }
    // ── Moje žádosti ──
    app.appendChild(el('<div style="font-weight:700;margin-bottom:6px;">Moje žádosti</div>'));
    var mine=el('<div></div>'); app.appendChild(mine);
    function loadMine(){
      api("GET","/api/v1/erp/app/attendance/absence/mine","").then(function(j){
        mine.innerHTML="";
        if(!j||!j.ok){ mine.appendChild(el('<div class="hint">Nelze načíst.</div>')); return; }
        if(!j.zadosti.length){ mine.appendChild(el('<div class="hint">Zatím žádné žádosti.</div>')); return; }
        j.zadosti.forEach(function(z){
          var sc=stavChip[z.stav]||["?","#888"];
          var row=el('<div style="border-bottom:1px solid #1b2742;padding:9px 4px;"><div style="display:flex;align-items:center;gap:8px;"><div style="flex:1;">'+esc(z.typ_label)+' '+cz(z.od)+(z.od!==z.do?("–"+cz(z.do)):"")+'</div>'+chip(sc[0],sc[1])+'</div>'+(z.status_text?('<div class="hint" style="margin-top:3px;">Vedoucí: „'+esc(z.status_text)+'“</div>'):'')+'</div>');
          if(z.stav==='pending'){
            var zr=el('<button class="ghost" style="margin-top:6px;padding:6px 10px;font-size:13px;color:#f87171;border-color:#5a2b2b;">✕ Zrušit</button>');
            zr.addEventListener("click",function(){
              if(!confirm("Zrušit žádost: "+z.typ_label+" "+cz(z.od)+(z.od!==z.do?("–"+cz(z.do)):"")+"?")) return;
              zr.disabled=true; zr.textContent="…";
              api("POST","/api/v1/erp/app/attendance/absence/cancel",{id:z.id}).then(function(r){
                if(r&&r.ok){ loadMine(); } else { zr.disabled=false; zr.textContent="✕ Zrušit"; alert("Nepodařilo se zrušit: "+((r&&r.error)||"?")); }
              }).catch(function(){ zr.disabled=false; zr.textContent="✕ Zrušit"; });
            });
            row.appendChild(zr);
          }
          mine.appendChild(row);
        });
      });
    }
    loadInbox(); loadMine();
  }
  function hr_import(){
    app.innerHTML=topbar("📥 Import docházky z EUROSOFTu", true);
    app.appendChild(el('<div class="hint" style="margin-bottom:10px;line-height:1.5;">Natáhne reálná data z EUROSOFTu (EC_Dochazka_SumaDen) 1:1 — odpracováno (montáž/režie), dovolená, nemoc, lékař, OČR. Přesčas se neimportuje zvlášť (konto si ho dopočítá). Idempotentní (lze pustit vícekrát). Dny s živým píchnutím ve STRATEGII se nepřepíšou.</div>'));
    function dinp(lbl,val){ var w=el('<div style="margin-bottom:8px;"><label class="hint" style="display:block;margin-bottom:3px;">'+lbl+'</label><input type="date" value="'+val+'" style="width:100%;box-sizing:border-box;padding:9px;border-radius:9px;border:1px solid #2b3a5c;background:#0a1226;color:#e8eefc;"></div>'); return w; }
    var t=new Date(); var today=t.getFullYear()+"-"+("0"+(t.getMonth()+1)).slice(-2)+"-"+("0"+t.getDate()).slice(-2);
    var wOd=dinp("Od","2026-01-01"), wDo=dinp("Do",today);
    app.appendChild(wOd); app.appendChild(wDo);
    var btn=el('<button class="green full" style="margin-top:6px;">📥 Spustit import</button>');
    var st=el('<div class="hint" style="margin-top:10px;line-height:1.7;"></div>');
    btn.addEventListener("click",function(){
      if(!confirm("Spustit import docházky z EUROSOFTu za zvolené období?")) return;
      btn.disabled=true; st.innerHTML="Importuji… (může chvíli trvat)";
      api("POST","/api/v1/erp/app/hr/import-dochazka",{od:wOd.querySelector('input').value, do:wDo.querySelector('input').value}).then(function(r){
        btn.disabled=false;
        if(!r||!r.ok){ st.innerHTML='<span style="color:#f87171;">✗ '+esc((r&&r.error)||"chyba")+'</span>'; return; }
        var pt=r.po_typech||{}; var pts=Object.keys(pt).map(function(k){ return k+': '+pt[k]; }).join(' · ');
        st.innerHTML='<span style="color:#34d399;">✅ Hotovo ('+esc(r.obdobi)+')</span><br>'
          +'EC řádků: <b>'+r.ec_radku+'</b> · vloženo záznamů: <b>'+r.vlozeno+'</b><br>'
          +'přeskočeno (živé píchnutí): '+r.preskoceno_zive+'<br>'
          +(pts?('po typech: '+esc(pts)+'<br>'):'')
          +((r.bez_napojeni&&r.bez_napojeni.length)?('<span style="color:#f59e0b;">bez napojení na osobu (CisloZam): '+esc(r.bez_napojeni.join(', '))+'</span>'):'');
      });
    });
    app.appendChild(btn); app.appendChild(st);
  }
  function hr_konto(){
    app.innerHTML=topbar("🏦 Uzávěrka konta", true);
    function chip(t,c){ return '<span style="background:'+c+';color:#04150e;border-radius:8px;padding:2px 7px;font-size:11px;font-weight:700;">'+esc(t)+'</span>'; }
    function nf(v){ return (Math.round((v||0)*100)/100).toString().replace('.',','); }
    function kc(v){ return new Intl.NumberFormat('cs-CZ').format(Math.round(v||0))+' Kč'; }
    // default = minulý měsíc (uzávěrka uzavřeného období)
    var now=new Date(); var d=new Date(now.getFullYear(),now.getMonth()-1,1);
    var curObd=d.getFullYear()+"-"+("0"+(d.getMonth()+1)).slice(-2);
    var mi=el('<input type="month" value="'+curObd+'" style="width:100%;box-sizing:border-box;padding:10px;border-radius:10px;border:1px solid #2b3a5c;background:#0a1226;color:#e8eefc;font-size:15px;margin-bottom:8px;">');
    app.appendChild(mi);
    app.appendChild(el('<div class="hint" style="margin-bottom:8px;line-height:1.5;">Jen lidé s aktivním kontem. Zůstatek = převod z minulé uzávěrky. Rozhodni do prémie / do přesčasu / převést.</div>'));
    var summ=el('<div style="margin-bottom:8px;"></div>'); app.appendChild(summ);
    var _kt={f:"vse",data:[]};
    var pane=el('<div style="display:flex;gap:10px;height:calc(54vh - 86px);align-items:stretch;">'
      +'<div style="flex:1;min-width:0;overflow-y:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none;border:1px solid var(--bord);border-radius:12px;background:rgba(255,255,255,0.02);padding:2px 8px;"><ul id="ktList" style="padding:0;list-style:none;margin:0;"></ul></div>'
      +'<div id="ktRail" style="width:72px;flex:none;overflow-y:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none;display:flex;flex-direction:column;gap:7px;padding:0;"></div></div>');
    app.appendChild(pane);
    function _ktDone(p){ return !!(p.settlement&&p.settlement.decided); }
    function _ktPass(p,k){ k=k||_kt.f; if(k==="vse")return true; return k==="done"?_ktDone(p):!_ktDone(p); }
    function _ktRailBtn(icon,label,key){
      var on=(_kt.f===key); var c=(key==="vse")?_kt.data.length:_kt.data.filter(function(p){return _ktPass(p,key);}).length;
      var amb=(key==="wait");
      var bdg=(c>0)?'<span style="position:absolute;top:4px;right:6px;min-width:17px;height:17px;line-height:15px;border-radius:9px;border:1px solid rgba(0,0,0,.25);background:'+(amb?"var(--amber)":"var(--green)")+';color:#241a02;font-size:10px;font-weight:700;padding:0 3px;box-sizing:border-box;text-align:center;">'+c+'</span>':'';
      var b=el('<button style="position:relative;width:100%;box-sizing:border-box;margin:0;padding:11px 2px;font-size:10.5px;line-height:1.15;display:flex;flex-direction:column;align-items:center;gap:4px;border:1px solid '+(on?"var(--green)":"var(--bord)")+';background:'+(on?"var(--green)":"rgba(255,255,255,0.02)")+';color:'+(on?"#04150e":"var(--mut)")+';border-radius:13px;cursor:pointer;"><span style="font-size:24px;line-height:1;">'+icon+'</span>'+label+bdg+'</button>');
      b.addEventListener("click",function(){ _kt.f=key; render(); });
      return b;
    }
    function panel(box,p){
      var w=el('<div></div>');
      var s=(p.settlement||{});
      var c=(p.comp||{});
      var nabehlo=(p.settlement && s.nabehlo!=null)?s.nabehlo:(c.nabehlo!=null?c.nabehlo:0);
      var sazba=(s.do_premie_h>0?Math.round(s.premie_kc/s.do_premie_h):(c.sazba||0));
      function numf(label,val,step){ return '<label class="hint" style="display:block;margin:6px 0 2px;">'+label+'</label><input type="number" step="'+(step||"0.5")+'" value="'+(val||0)+'" style="width:100%;box-sizing:border-box;padding:9px;border-radius:9px;border:1px solid #2b3a5c;background:#0a1226;color:#e8eefc;">'; }
      var breakdown='';
      if(p.comp){
        breakdown='<div style="margin:2px 0 8px;padding:10px;border-radius:10px;background:#0a1226;line-height:1.6;font-size:13px;">'
          +'<div style="font-weight:700;margin-bottom:4px;">📊 Výpočet z docházky</div>'
          +'Fond: <b>'+nf(c.fond)+' h</b> · Odpracováno: <b>'+nf(c.worked)+' h</b> · Placená absence: <b>'+nf(c.abs_paid)+' h</b><br>'
          +'Přesčas nad polštář: <b style="color:#34d399;">+'+nf(c.prescas)+' h</b><br>'
          +'Manko: '+nf(c.manko)+' h, po loajalitě ('+nf(c.loaj)+' h): <b style="color:#f59e0b;">−'+nf(c.manko_loaj)+' h</b><br>'
          +'<span style="color:#9fb;">⇒ Naběhlo (návrh): <b>'+nf(c.nabehlo)+' h</b></span> <span class="hint">— můžeš přepsat níže</span>'
          +'</div>';
      }
      w.innerHTML='<div class="hint" style="margin:2px 0 6px;">Zůstatek z minula: <b style="color:#e8eefc;">'+nf(p.konto_pred)+' h</b> · příplatek '+nf(p.priplatek_pct)+' %</div>'
        +breakdown
        +numf("Naběhlo za období (h)",nabehlo)
        +numf("Hodinová sazba (Kč/h, pro výpočet)",sazba,"1")
        +numf("Proplatit do prémie (h)",s.do_premie_h)
        +numf("Proplatit do přesčasu (h)",s.do_prescas_h);
      var nums=w.querySelectorAll("input[type=number]");
      var calc=el('<div style="margin-top:10px;padding:10px;border-radius:10px;background:#0a1226;line-height:1.7;"></div>');
      var note=el('<input type="text" placeholder="Poznámka (volitelné)" value="'+esc(s.note||"")+'" style="width:100%;box-sizing:border-box;padding:9px;border-radius:9px;border:1px solid #2b3a5c;background:#0a1226;color:#e8eefc;margin-top:8px;">');
      function recalc(){
        var nb=parseFloat(nums[0].value)||0, sz=parseFloat(nums[1].value)||0, dp=parseFloat(nums[2].value)||0, dpr=parseFloat(nums[3].value)||0;
        var pk=Math.round(dp*sz), prk=Math.round(dpr*sz*(1+p.priplatek_pct/100));
        var prev=Math.round((p.konto_pred+nb-dp-dpr)*100)/100;
        var over=(dp+dpr> p.konto_pred+nb+0.001);
        calc.innerHTML='Do prémie: <b>'+nf(dp)+' h</b> = '+kc(pk)+'<br>'
          +'Do přesčasu: <b>'+nf(dpr)+' h</b> +'+nf(p.priplatek_pct)+'% = '+kc(prk)+'<br>'
          +'<span style="'+(over?"color:#f87171;":"")+'">Převedeno do dalšího měsíce: <b>'+nf(prev)+' h</b></span>'
          +(over?'<br><span style="color:#f87171;">⚠ Proplácíš víc, než je v kontu</span>':'');
        return {over:over};
      }
      nums.forEach(function(n){ n.addEventListener("input",recalc); });
      note.addEventListener("focus",function(){});
      var volLbl={premie:'do prémie',do_premie:'do prémie',prescas:'do přesčasu',prevest:'převést',na_vyber:'převést'}[p.volba]||'převést';
      var qf=el('<button class="ghost full" style="margin-top:8px;border-color:#34d399;color:#9fb;">⚡ Dle režimu člověka ('+volLbl+')</button>');
      qf.addEventListener("click",function(){
        var avail=Math.round((p.konto_pred+(parseFloat(nums[0].value)||0))*100)/100;
        if(avail<0) avail=0;
        var v=p.volba||'';
        if(v.indexOf('premie')>=0){ nums[2].value=avail; nums[3].value=0; }
        else if(v.indexOf('prescas')>=0){ nums[2].value=0; nums[3].value=avail; }
        else { nums[2].value=0; nums[3].value=0; }
        recalc();
      });
      var btn=el('<button class="green full" style="margin-top:10px;">💾 Uložit rozhodnutí</button>');
      var st=el('<div class="hint" style="margin-top:6px;"></div>');
      btn.addEventListener("click",function(){
        if(recalc().over){ st.textContent="✗ Proplácíš víc, než je v kontu."; return; }
        btn.disabled=true; st.textContent="Ukládám…";
        api("POST","/api/v1/erp/app/hr/konto/save",{employee_id:p.employee_id,obdobi:mi.value,
          nabehlo:parseFloat(nums[0].value)||0, hodinova_sazba:parseFloat(nums[1].value)||0,
          do_premie_h:parseFloat(nums[2].value)||0, do_prescas_h:parseFloat(nums[3].value)||0,
          note:note.value}).then(function(r){
            btn.disabled=false; st.textContent=(r&&r.ok)?"✅ Uloženo":("✗ "+((r&&r.error)||"chyba")); if(r&&r.ok) setTimeout(load,600);
          });
      });
      w.appendChild(calc); w.appendChild(qf); w.appendChild(note); w.appendChild(btn); w.appendChild(st); box.appendChild(w); recalc();
    }
    function render(){
      var rail=document.getElementById("ktRail"), ul=document.getElementById("ktList");
      if(!rail||!ul) return;
      var sZust=0,sNab=0,nDone=0;
      _kt.data.forEach(function(p){ sZust+=(p.konto_pred||0); sNab+=((p.comp&&p.comp.nabehlo)||0); if(_ktDone(p))nDone++; });
      summ.innerHTML='<div style="padding:9px 11px;border-radius:10px;background:#0a1226;font-size:13px;line-height:1.6;"><b>'+_kt.data.length+'</b> lidí s kontem · rozhodnuto <b>'+nDone+'</b>/'+_kt.data.length+'<br>Σ zůstatek <b>'+nf(sZust)+' h</b> · Σ naběhlo (návrh) <b>'+nf(sNab)+' h</b></div>';
      rail.innerHTML="";
      [["📋","Vše","vse"],["⏳","Čeká","wait"],["✅","Hotovo","done"]].forEach(function(it){ rail.appendChild(_ktRailBtn(it[0],it[1],it[2])); });
      ul.innerHTML="";
      var arr=_kt.data.filter(function(p){return _ktPass(p);});
      if(!arr.length){ ul.appendChild(el('<li style="border:none;color:var(--mut);">Nikdo.</li>')); return; }
      arr.forEach(function(p){
        var firmaLbl=(p.tenant_id===14?'INTERSOFT':'EUROSOFT'); var done=_ktDone(p);
        var li=el('<li class="ct" style="border:none;border-bottom:1px solid #1b2742;padding:0;"></li>');
        var head=el('<div style="display:flex;align-items:center;gap:10px;cursor:pointer;padding:9px 4px;"></div>');
        head.appendChild(el('<div style="flex:1;min-width:0;"><div style="font-weight:600;">'+esc(p.jmeno)+' <span class="hint">· '+firmaLbl+'</span></div><div style="margin-top:4px;display:flex;gap:5px;flex-wrap:wrap;">'+chip('zůstatek '+nf(p.konto_pred)+' h','#fbbf24')+(done?chip('rozhodnuto','#34d399'):chip('čeká','#60a5fa'))+'</div></div>'));
        head.appendChild(el('<div class="chev" style="color:#5a6;">&#8250;</div>'));
        var ed=el('<div class="ctexp" style="display:none;padding:0 4px 10px;"></div>');
        head.addEventListener("click",function(){
          var open=li.classList.toggle("open"); ed.style.display=open?"block":"none";
          if(open && ed.dataset.built!=='1'){ panel(ed,p); ed.dataset.built='1'; }
          _railSync("ktRail","ktList");
        });
        li.appendChild(head); li.appendChild(ed); ul.appendChild(li);
      });
      _railSync("ktRail","ktList");
    }
    function load(){
      var ul=document.getElementById("ktList"); if(ul) ul.innerHTML='<li style="border:none;color:var(--mut);">Načítám…</li>'; summ.innerHTML="";
      api("GET","/api/v1/erp/app/hr/konto?obdobi="+encodeURIComponent(mi.value),"").then(function(j){
        if(!j||!j.ok){ if(ul) ul.innerHTML='<li style="border:none;color:var(--mut);">'+esc((j&&j.error==="forbidden")?"Nemáš přístup (jen HR / vedení).":"Nelze načíst.")+'</li>'; return; }
        if(!j.lide.length){ _kt.data=[]; if(ul) ul.innerHTML='<li style="border:none;color:var(--mut);">Nikdo s aktivním kontem. Konto zapneš v „Režimy docházky".</li>'; return; }
        _kt.data=j.lide; render();
      });
    }
    mi.addEventListener("change",load);
    load();
  }
  function hr_person(){
    var uid=window._hrUid;
    app.innerHTML=topbar(window._hrName||"Karta", true);
    var box=el('<div></div>'); app.appendChild(box); box.innerHTML='<div class="hint">Načítám…</div>';
    var edit=false, inputs={};
    function render(j){
      box.innerHTML="";
      if(!j||!j.ok){ box.appendChild(el('<div class="hint">'+esc((j&&j.error==="forbidden")?"Nemáš přístup.":"Nelze načíst.")+'</div>')); return; }
      var eb=el('<button style="width:100%;padding:10px;border:0;border-radius:10px;margin-bottom:10px;background:'+(edit?"#26304a":"#2563eb")+';color:#fff;font-weight:700;">'+(edit?"Zrušit úpravy":"✏️ Upravit")+'</button>');
      eb.onclick=function(){ edit=!edit; render(j); }; box.appendChild(eb);
      var ab=el('<button style="width:100%;padding:10px;border:0;border-radius:10px;margin-bottom:10px;background:#0e7490;color:#fff;font-weight:700;">✉️ Poslat aktivační e-mail (pozvánku)</button>');
      ab.onclick=function(){
        ab.disabled=true; var orig=ab.textContent; ab.textContent="Posílám…";
        api("POST","/api/v1/erp/app/hr/send-activation",{user_id:uid}).then(function(r){
          if(r&&r.ok){ alert("Hotovo — aktivační e-mail odeslán na: "+(r.to_email||"?")); }
          else { alert("Nepodařilo se odeslat: "+((r&&(r.message||r.error))||"?")); }
          ab.disabled=false; ab.textContent=orig;
        });
      };
      box.appendChild(ab);
      // Pracovní vztah (konfigurovatelné, měnitelné, auditované)
      if(j.vztah && j.vztah_typy){
        var vc=_card("🧾 Pracovní vztah","");
        var cur=j.vztah.relation||"zamestnanec";
        var sel=el('<select style="width:100%;padding:10px;border-radius:10px;border:1px solid #2a3550;background:#0e1530;color:#e8eef9;font-size:15px;"></select>');
        j.vztah_typy.forEach(function(t){ var o=el('<option value="'+t.key+'"'+(t.key===cur?' selected':'')+'>'+esc(t.label)+'</option>'); sel.appendChild(o); });
        vc.appendChild(sel);
        var note=el('<input placeholder="IČO / poznámka (volitelné)" value="'+esc(j.vztah.ico||j.vztah.note||"")+'" style="width:100%;margin-top:8px;padding:9px;border-radius:10px;border:1px solid #2a3550;background:#0e1530;color:#e8eef9;font-size:14px;">');
        vc.appendChild(note);
        var st=el('<div class="hint" style="margin-top:6px;">OSVČ/Dohoda = bez výplatnice (kontrola mezd je nehlásí jako chybějící).</div>'); vc.appendChild(st);
        sel.onchange=function(){
          st.textContent="Ukládám…";
          api("POST","/api/v1/erp/app/hr/person/work-relation",{uid:uid,relation:sel.value,ico:note.value}).then(function(r){
            st.textContent=(r&&r.ok)?"✓ Uloženo":("Chyba: "+((r&&r.error)||"?")); });
        };
        note.onblur=function(){ if(sel.value!=="zamestnanec"){ sel.onchange(); } };
        box.appendChild(vc);
      }
      inputs={};
      (j.sections||[]).forEach(function(sec){
        var c=_card(sec.label,"");
        sec.items.forEach(function(it){
          if(edit){ var w=_fld(it.label,(it.type==="date"?_czDate(it.value):it.value),it.type==="date"?"DD.MM.RRRR":""); inputs[it.key]={inp:w._inp,date:(it.type==="date")}; c.appendChild(w); }
          else { c.appendChild(el('<div style="padding:5px 0;"><span class="hint">'+esc(it.label)+': </span>'+(it.value?esc(it.type==="date"?_czDate(it.value):it.value):'<span class="hint">—</span>')+'</div>')); }
        });
        box.appendChild(c);
      });
      if(j.deti && j.deti.length){
        var dc=_card("👨‍👩‍👧 Děti","");
        j.deti.forEach(function(d){ dc.appendChild(el('<div style="padding:5px 0;">'+esc(d.child_name||"")+(d.relief_order?(" · "+d.relief_order+". dítě"):"")+(d.birth_date?(" · "+esc(_czDate(d.birth_date))):"")+'</div>')); });
        box.appendChild(dc);
      }
      if(edit){
        var sv=el('<button style="width:100%;padding:13px;border:0;border-radius:12px;background:#16a34a;color:#fff;font-weight:700;">💾 Uložit změny</button>');
        sv.onclick=function(){ var vals={}; Object.keys(inputs).forEach(function(k){ var v=inputs[k].inp.value; if(inputs[k].date)v=_isoDate(v); vals[k]=v; });
          api("POST","/api/v1/erp/app/hr/person/save",{uid:uid,values:vals}).then(function(r){ if(r&&r.ok){ edit=false; load(); } else alert("Chyba: "+((r&&r.error)||"?")); }); };
        box.appendChild(sv);
      }
      box.appendChild(el('<div style="height:80px;"></div>'));
    }
    function load(){ api("GET","/api/v1/erp/app/hr/person?uid="+uid,"").then(render); }
    load();
  }
  function sms_stav(){
    app.innerHTML=topbar("📨 Stav SMS", true);
    var box=el('<div></div>'); app.appendChild(box); box.innerHTML='<div class="hint">Načítám + ověřuji stav u brány…</div>';
    api("GET","/api/v1/erp/app/sms/recent","").then(function(j){
      box.innerHTML="";
      if(!j||!j.ok){ box.appendChild(el('<div class="hint">'+esc((j&&j.error==="forbidden")?"Jen pro rodiče.":"Nelze načíst.")+'</div>')); return; }
      if(j.reconcile){ var rc=j.reconcile; box.appendChild(el('<div class="hint" style="margin-bottom:8px;">'+(rc.ok?("Ověřeno u brány: zkontrolováno "+(rc.checked||0)+", aktualizováno "+(rc.updated||0)+(rc.failed?(", ⚠ selhalo "+rc.failed):"")):("Bránu nešlo ověřit: "+esc(rc.error||"?")))+'</div>')); }
      (j.sms||[]).forEach(function(m){
        var col={Delivered:"#5ee0b7",Sent:"#9fd",Failed:"#f88",Accepted:"#fc8",Pending:"#fc8"}[m.gate_state]||"#9fb2d4";
        var r=el('<div style="padding:9px 0;border-bottom:1px solid #1b2742;"></div>');
        r.innerHTML='<div style="display:flex;justify-content:space-between;gap:8px;"><b>'+esc(m.purpose)+'</b> <span style="color:'+col+';font-weight:700;">'+esc(m.gate_state)+'</span></div><div class="hint">'+esc(m.tel)+' · '+esc(m.vznik)+' · DB:'+esc(m.status)+(m.err?(' · '+esc(m.err)):'')+'</div>';
        box.appendChild(r);
      });
      if(!(j.sms||[]).length) box.appendChild(el('<div class="hint">Žádné nedávné SMS.</div>'));
      var rb=el('<button style="width:100%;margin-top:12px;padding:11px;border:0;border-radius:10px;background:#2563eb;color:#fff;font-weight:700;">🔄 Obnovit</button>'); rb.onclick=function(){ sms_stav(); }; box.appendChild(rb);
    });
  }
  function dev_stav(){
    app.innerHTML=topbar("📱 Stav aplikací", true);
    var box=el('<div></div>'); app.appendChild(box); box.innerHTML='<div class="hint">Načítám…</div>';
    api("GET","/api/v1/erp/app/devices","").then(function(j){
      box.innerHTML="";
      if(!j||!j.ok){ box.appendChild(el('<div class="hint">'+esc((j&&j.error==="forbidden")?"Jen pro rodiče.":"Nelze načíst.")+'</div>')); return; }
      var on=(j.zarizeni||[]).filter(function(d){return d.online;}).length;
      box.appendChild(el('<div class="hint" style="margin-bottom:8px;">'+on+' online z '+(j.zarizeni||[]).length+' · nejnovější verze kód '+j.latest_vc+'. Online = pinglo za 5 min.</div>'));
      (j.zarizeni||[]).forEach(function(d){
        var col=d.online?"#5ee0b7":"#f88";
        var stav=d.online?"online":(d.min_ago<1440?(d.min_ago+" min zpět"):(Math.floor(d.min_ago/1440)+" dní zpět"));
        var r=el('<div style="padding:9px 0;border-bottom:1px solid #1b2742;"></div>');
        r.innerHTML='<div style="display:flex;justify-content:space-between;gap:8px;"><b>'+esc(d.jmeno)+'</b><span style="color:'+col+';font-weight:700;">'+(d.online?"● online":"○ "+esc(stav))+'</span></div>'
          +'<div class="hint">'+esc(d.zarizeni)+' · v'+esc(d.verze)+(d.outdated?' ⚠ starší APK':'')+' · '+esc(d.naposledy)+(d.service?'':' · ⚠ služba vyp.')+'</div>';
        box.appendChild(r);
      });
      if(!(j.zarizeni||[]).length) box.appendChild(el('<div class="hint">Žádná zařízení.</div>'));
      var rb=el('<button style="width:100%;margin-top:12px;padding:11px;border:0;border-radius:10px;background:#2563eb;color:#fff;font-weight:700;">🔄 Obnovit</button>'); rb.onclick=function(){ dev_stav(); }; box.appendChild(rb);
    });
  }
  // --- generátor dokumentů: vyber šablonu + osobu → PDF (živá data) ---
  function doc_gen(){
    app.innerHTML=topbar("📄 Generovat dokument", true);
    var box=el('<div></div>'); app.appendChild(box); box.innerHTML='<div class="hint">Načítám…</div>';
    var tpls=[], picked=null;
    api("GET","/api/v1/erp/app/doc/templates","").then(function(j){
      if(!j||!j.ok){ box.innerHTML='<div class="hint">'+esc((j&&j.error==="forbidden")?"Generování dokumentů je jen pro HR / vedení.":"Nelze načíst šablony.")+'</div>'; return; }
      tpls=j.sablony||[]; paint();
    });
    function paint(){
      box.innerHTML="";
      var c1=_card("1) Vyber dokument","");
      if(!tpls.length) c1.appendChild(el('<div class="hint">Zatím žádná šablona.</div>'));
      tpls.forEach(function(t){
        var sel=(picked&&picked.id===t.id);
        var b=el('<button style="display:block;width:100%;text-align:left;margin:4px 0;padding:11px 12px;border-radius:10px;border:1px solid '+(sel?"#2563eb":"#2b3a5c")+';background:'+(sel?"#16223f":"#0f1830")+';color:#e8eefc;font-size:14px;">'+(sel?"✓ ":"")+esc(t.nazev)+(t.kategorie?(' <span style="color:#88a;">· '+esc(t.kategorie)+'</span>'):'')+'</button>');
        b.onclick=function(){ picked=t; paint(); };
        c1.appendChild(b);
      });
      box.appendChild(c1);
      if(picked){
        var c2=_card("2) Vyber osobu","Dokument se vyplní jejími živými daty.");
        var srch=el('<input type="text" placeholder="Hledat jméno…" style="width:100%;box-sizing:border-box;padding:10px 12px;border-radius:9px;border:1px solid #2b3a5c;background:#0a1226;color:#e8eefc;font-size:15px;margin-bottom:8px;">');
        c2.appendChild(srch);
        var list=el('<div></div>'); c2.appendChild(list); box.appendChild(c2);
        function loadP(q){
          list.innerHTML='<div class="hint">Načítám…</div>';
          api("GET","/api/v1/erp/app/doc/people"+(q?("?q="+encodeURIComponent(q)):""),"").then(function(j){
            list.innerHTML="";
            if(!j||!j.ok){ list.appendChild(el('<div class="hint">Nelze načíst.</div>')); return; }
            (j.lide||[]).slice(0,60).forEach(function(p){
              var r=el('<div style="display:flex;align-items:center;gap:8px;padding:9px 2px;border-bottom:1px solid #1b2742;"></div>');
              r.appendChild(el('<div style="flex:1;min-width:0;"><b>'+esc(p.jmeno)+'</b>'+(p.firma?' <span class="hint">'+esc(p.firma)+'</span>':'')+'</div>'));
              var bOpen=el('<button class="ghost" style="margin:0;padding:7px 11px;font-size:16px;" title="Otevřít PDF">📄</button>');
              bOpen.onclick=function(){ gen(picked, p, r); };
              var bPc=el('<button class="ghost" style="margin:0;padding:7px 11px;font-size:16px;color:#7fb0ff;border-color:#2b4a7a;" title="Tisk na počítači">💻</button>');
              bPc.onclick=function(){ openOnPc("/doc-print?template_id="+picked.id+"&engagement_id="+encodeURIComponent(p.engagement_id)+"&label="+encodeURIComponent(picked.nazev+" · "+p.jmeno), picked.nazev+" · "+p.jmeno); };
              var bEC=el('<button class="ghost" style="margin:0;padding:7px 11px;font-size:16px;color:#5ee0b7;border-color:#2a6b5a;" title="Uložit na EUROSOFT server">📤</button>');
              bEC.onclick=function(){ genEC(picked, p, bEC); };
              r.appendChild(bOpen); r.appendChild(bPc); r.appendChild(bEC);
              list.appendChild(r);
            });
            if(!(j.lide||[]).length) list.appendChild(el('<div class="hint">Nikdo nenalezen.</div>'));
          });
        }
        var _t3=null; srch.addEventListener("input",function(){ clearTimeout(_t3); _t3=setTimeout(function(){ loadP(srch.value.trim()); },250); });
        loadP("");
      }
    }
    function gen(t, p, rowEl){
      var orig=rowEl.innerHTML; rowEl.innerHTML='<div style="flex:1;">'+esc(p.jmeno)+'</div><div class="hint">generuji…</div>';
      api("POST","/api/v1/erp/app/doc/render",{template_id:t.id, engagement_id:p.engagement_id}).then(function(r){
        rowEl.innerHTML=orig;
        if(r&&r.ok){ openApp(r.url); }
        else alert("Chyba: "+((r&&(r.note||r.error))||"nepodařilo se vygenerovat"));
      });
    }
    function genEC(t, p, btn){
      btn.disabled=true; var o=btn.textContent; btn.textContent="⏳";
      api("POST","/api/v1/erp/app/doc/to-eurosoft",{template_id:t.id, engagement_id:p.engagement_id}).then(function(r){
        btn.disabled=false; btn.textContent=o;
        if(r&&r.ok){ alert("✅ Uloženo na EUROSOFT server:\n"+(r.fname||r.path||"")); }
        else alert("Chyba: "+((r&&(r.note||r.error))||"nepodařilo se uložit na EUROSOFT"));
      });
    }
  }
  // --- mzdy: Helios (EC) × STRATEGIE × delta ---
  function wage_cmp(){
    app.innerHTML=topbar("💰 Mzdy: Helios × STRATEGIE", true);
    var _wc={f:"vse",radky:[]};
    var info=el('<div style="margin-bottom:8px;"></div>'); app.appendChild(info);
    var pane=el('<div style="display:flex;gap:10px;height:calc(56vh - 86px);align-items:stretch;">'
      +'<div style="flex:1;min-width:0;overflow-y:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none;border:1px solid var(--bord);border-radius:12px;background:rgba(255,255,255,0.02);padding:2px 8px;"><div id="wcList"></div></div>'
      +'<div id="wcRail" style="width:72px;flex:none;overflow-y:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none;display:flex;flex-direction:column;gap:7px;padding:0;"></div></div>');
    app.appendChild(pane);
    function _wcDiff(p){ return p.stav!=="OK"; }
    function _wcRailBtn(icon,label,key){
      var on=(_wc.f===key); var c=(key==="vse")?_wc.radky.length:_wc.radky.filter(_wcDiff).length;
      var amb=(key==="diff");
      var bdg=(c>0)?'<span style="position:absolute;top:4px;right:6px;min-width:17px;height:17px;line-height:15px;border-radius:9px;border:1px solid rgba(0,0,0,.25);background:'+(amb?"#f88":"var(--green)")+';color:#241a02;font-size:10px;font-weight:700;padding:0 3px;box-sizing:border-box;text-align:center;">'+c+'</span>':'';
      var b=el('<button style="position:relative;width:100%;box-sizing:border-box;margin:0;padding:11px 2px;font-size:10.5px;line-height:1.15;display:flex;flex-direction:column;align-items:center;gap:4px;border:1px solid '+(on?"var(--green)":"var(--bord)")+';background:'+(on?"var(--green)":"rgba(255,255,255,0.02)")+';color:'+(on?"#04150e":"var(--mut)")+';border-radius:13px;cursor:pointer;"><span style="font-size:24px;line-height:1;">'+icon+'</span>'+label+bdg+'</button>');
      b.addEventListener("click",function(){ _wc.f=key; render(); });
      return b;
    }
    function render(){
      var rail=document.getElementById("wcRail"), lst=document.getElementById("wcList");
      if(!rail||!lst) return;
      rail.innerHTML=""; rail.appendChild(_wcRailBtn("📋","Vše","vse"));
      if(_wc.radky.filter(_wcDiff).length) rail.appendChild(_wcRailBtn("⚠","Rozdíly","diff"));
      lst.innerHTML='<div style="display:flex;gap:8px;padding:4px 2px;font-size:11px;color:#88a;border-bottom:1px solid #2b3a5c;position:sticky;top:0;background:#0b1020;"><div style="flex:1;">složka</div><div style="width:62px;text-align:right;">ZDROJ</div><div style="width:62px;text-align:right;">CÍL</div><div style="width:56px;text-align:right;">Δ</div></div>';
      var arr=_wc.radky.filter(function(p){ return _wc.f==="vse"||_wcDiff(p); });
      if(!arr.length){ lst.appendChild(el('<div class="hint" style="padding:8px 2px;">'+(_wc.radky.length?"Žádné rozdíly 🎉":"Žádná data — klikni Aktualizovat.")+'</div>')); return; }
      var lastName=null;
      arr.forEach(function(p){
        if(p.jmeno!==lastName){ lst.appendChild(el('<div style="margin-top:9px;font-weight:700;color:#cdd;font-size:13px;">'+esc(p.jmeno)+' <span class="hint">· '+esc(p.firma)+' · č.'+esc(p.cislo)+'</span></div>')); lastName=p.jmeno; }
        var col={"OK":"#5ee0b7","ROZDIL":"#f88","jen EC":"#fc8","jen STRATEGIE":"#fc8"}[p.stav]||"#9fb2d4";
        lst.appendChild(el('<div style="display:flex;gap:8px;padding:4px 2px;border-bottom:1px solid #1b2742;font-size:12.5px;"><div style="flex:1;">'+esc(p.slozka)+'</div><div style="width:62px;text-align:right;color:#9fb2d4;">'+(p.zdroj||0).toLocaleString("cs")+'</div><div style="width:62px;text-align:right;">'+(p.cil||0).toLocaleString("cs")+'</div><div style="width:56px;text-align:right;color:'+col+';font-weight:700;">'+(p.delta>0?"+":"")+(p.delta||0).toLocaleString("cs")+'</div></div>'));
      });
    }
    function load(){
      info.innerHTML='<div class="hint">Načítám…</div>';
      api("GET","/api/v1/erp/app/wage-compare","").then(function(j){
        if(!j||!j.ok){ info.innerHTML='<div class="hint">'+esc((j&&j.error==="forbidden")?"Jen HR / vedení.":"Nelze načíst.")+'</div>'; return; }
        _wc.radky=j.radky||[];
        info.innerHTML="";
        info.appendChild(el('<div class="hint" style="margin-bottom:6px;">Snapshot EC: '+esc(j.asof||"—")+' · '+j.celkem+' složek · <b style="color:'+(j.rozdilu?"#f88":"#5ee0b7")+'">'+j.rozdilu+' rozdílů</b></div>'));
        var sync=el('<button style="width:100%;padding:10px;border:0;border-radius:10px;background:#26304a;color:#cfe;">🔄 Aktualizovat z EUROSOFTu</button>');
        sync.onclick=function(){ sync.disabled=true; sync.textContent="Stahuji z EC…"; api("POST","/api/v1/erp/app/wage-compare/sync",{}).then(function(r){ if(r&&r.ok){ load(); } else { sync.disabled=false; alert("Chyba: "+((r&&(r.error))||"?")); } }); };
        info.appendChild(sync);
        render();
      });
    }
    load();
  }
  function openSoon(label){ window._soonLabel=label||""; go("soon"); }
  function soon(){
    var lab=window._soonLabel||"";
    app.innerHTML=topbar(lab||"Připravujeme", true);
    var p=el('<div class="panel"></div>');
    p.appendChild(el('<div class="big">🚧 '+esc(lab)+'</div>'));
    p.appendChild(el('<div class="hint" style="margin-top:8px;line-height:1.6;">Připravujeme — tahle agenda se brzy objeví. Řekni Marti, co tu má být, a napojíme ji.</div>'));
    app.appendChild(p);
  }
  // ───── SKUPINY (třídění lidí do skupin, ve stylu Výroby; parent-only). Marti 9.6. ─────
  var _skView=null, _skGroups=[], _skMembers=null;
  function skupiny(){
    app.innerHTML=topbar("👥 Skupiny", true, true);
    var _tb=app.querySelector('.topbar'); if(_tb) _tb.style.paddingTop="12px";
    var wrap=el('<div style="display:flex;gap:8px;height:calc(100vh - 165px);padding:4px 2px 0;"></div>');
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
    var wrap=el('<div style="display:flex;gap:10px;height:calc(100vh - 150px);align-items:stretch;"></div>');
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
