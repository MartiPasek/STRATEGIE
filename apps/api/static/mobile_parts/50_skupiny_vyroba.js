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
