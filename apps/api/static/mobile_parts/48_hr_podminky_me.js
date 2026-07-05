  function hr_podminky(){
    app.innerHTML=topbar("📋 Podmínky skupin", true);
    var _pd={f:"system", groups:[]};
    function gLabel(key){ if(key==="system")return "Systém (výchozí pro všechny)"; if(key==="lide")return "Jednotlivci";
      var g=_pd.groups.filter(function(x){return String(x.code)===String(key);})[0]; return g?g.label:key; }
    var pane=el('<div style="display:flex;gap:10px;height:calc(64vh - 86px);align-items:stretch;">'
      +'<div id="pdC" style="flex:1;min-width:0;overflow-y:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none;border:1px solid var(--bord);border-radius:12px;background:rgba(255,255,255,0.02);padding:6px 10px;"><div class="hint">Načítám…</div></div>'
      +'<div id="pdRail" style="width:84px;flex:none;overflow-y:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none;display:flex;flex-direction:column;gap:6px;padding:0 0 86px;"></div></div>');
    app.appendChild(pane);
    var C=pane.querySelector("#pdC"), R=pane.querySelector("#pdRail");
    function railBtn(icon,label,key){
      var on=(_pd.f===key);
      var b=el('<button style="width:100%;box-sizing:border-box;margin:0;padding:9px 4px;font-size:10.5px;line-height:1.15;display:flex;flex-direction:column;align-items:center;gap:3px;border:1px solid '+(on?"var(--green)":"var(--bord)")+';background:'+(on?"var(--green)":"rgba(255,255,255,0.02)")+';color:'+(on?"#04150e":"var(--mut)")+';border-radius:12px;cursor:pointer;"><span style="font-size:20px;line-height:1;">'+icon+'</span>'+esc(label)+'</button>');
      b.addEventListener("click",function(){ _pd.f=key; render(); });
      return b;
    }
    function fieldEl(d,value){
      var v=(value==null?"":value);
      if(d.kind==="bool"){
        var s=el('<select style="width:120px;padding:7px;border-radius:8px;border:1px solid #2b3a5c;background:#0a1226;color:#e8eefc;"><option value="">— dědit —</option><option value="ANO">ANO</option><option value="NE">NE</option></select>');
        s.value=(v==="ANO"||v==="NE")?v:""; return s;
      }
      var i=el('<input type="text" value="'+esc(v)+'" '+(d.kind==="num"?'inputmode="decimal"':'')+' placeholder="'+(d.kind==="time"?"HH:MM":"— dědit —")+'" style="width:120px;box-sizing:border-box;padding:7px 9px;border-radius:8px;border:1px solid #2b3a5c;background:#0a1226;color:#e8eefc;text-align:right;">');
      return i;
    }
    function scopeView(key){
      C.innerHTML='<div class="hint">Načítám…</div>';
      var sk=(key==="system")?"system":"group", gc=(key==="system")?"":key;
      api("GET","/api/v1/erp/app/hr/conditions?scope_kind="+sk+(gc?("&group_code="+gc):""),"").then(function(j){
        C.innerHTML="";
        if(!j||!j.ok){ C.appendChild(el('<div class="hint">'+esc((j&&j.error==="forbidden")?"Jen HR / vedení.":"Nelze načíst.")+'</div>')); return; }
        C.appendChild(el('<div style="font-size:18px;font-weight:800;margin:2px 0 2px;">'+esc(gLabel(key))+'</div>'));
        C.appendChild(el('<div class="hint" style="margin-bottom:10px;">'+(sk==="system"?"Výchozí pro všechny. Skupina nebo jednotlivec to může přepsat.":"Hodnoty skupiny. Prázdné = zdědí ze systému. Členství se spravuje ve Skupinách.")+'</div>'));
        var st=el('<div class="hint" style="min-height:16px;margin-bottom:6px;"></div>'); C.appendChild(st);
        (j.defs||[]).forEach(function(d){
          var cur=(j.values&&j.values[d.code])?j.values[d.code].value:null;
          var row=el('<div style="display:flex;align-items:center;gap:10px;padding:7px 2px;border-bottom:1px solid #1b2742;"></div>');
          row.appendChild(el('<div style="flex:1;min-width:0;">'+esc(d.label)+(d.unit?(' <span class="hint">('+esc(d.unit)+')</span>'):'')+'</div>'));
          var f=fieldEl(d,cur); row.appendChild(f);
          function save(){ st.style.color="#9fb2d4"; st.textContent="Ukládám…";
            api("POST","/api/v1/erp/app/hr/conditions/save",{scope_kind:sk,group_code:gc,cond_code:d.code,value:f.value}).then(function(r){
              st.style.color=(r&&r.ok)?"#5ee0b7":"#f88"; st.textContent=(r&&r.ok)?("Uloženo: "+d.label+" ✓"):("✗ "+((r&&r.error)||"chyba")); });
          }
          f.addEventListener("change",save);
          C.appendChild(row);
        });
      });
    }
    function peopleView(){
      C.innerHTML='<input id="pdSrch" type="text" placeholder="Hledat jméno…" style="width:100%;box-sizing:border-box;padding:9px 11px;border-radius:9px;border:1px solid #2b3a5c;background:#0a1226;color:#e8eefc;margin-bottom:8px;"><div id="pdPpl"><div class="hint">Načítám…</div></div>';
      var srch=C.querySelector("#pdSrch"), box=C.querySelector("#pdPpl"), all=[], skupiny=[];
      function draw(q){
        box.innerHTML=""; var arr=all.filter(function(p){ return !q||(p.jmeno||"").toLowerCase().indexOf(q.toLowerCase())>=0; });
        if(!arr.length){ box.appendChild(el('<div class="hint">Nikdo.</div>')); return; }
        arr.forEach(function(p){
          var gl=p.cond_group||"— bez skupiny —";
          var li=el('<div class="ct" style="border-bottom:1px solid #1b2742;"></div>');
          var head=el('<div style="display:flex;align-items:center;gap:8px;cursor:pointer;padding:9px 2px;"></div>');
          head.appendChild(el('<div style="flex:1;min-width:0;"><div style="font-weight:600;">'+esc(p.jmeno)+'</div><div class="hint">'+esc(gl)+(p.vyjimka?' · <span style="color:#fbbf24;">vlastní výjimka</span>':'')+'</div></div>'));
          head.appendChild(el('<div class="chev" style="color:#5a6;">&#8250;</div>'));
          var ed=el('<div class="ctexp" style="display:none;padding:2px 2px 12px;"></div>');
          head.addEventListener("click",function(){ var op=li.classList.toggle("open"); ed.style.display=op?"block":"none"; if(op&&ed.dataset.b!=="1"){ personDetail(ed,p,skupiny); ed.dataset.b="1"; } });
          li.appendChild(head); li.appendChild(ed); box.appendChild(li);
        });
      }
      api("GET","/api/v1/erp/app/hr/conditions/people","").then(function(j){
        if(!j||!j.ok){ box.innerHTML='<div class="hint">'+esc((j&&j.error==="forbidden")?"Jen HR / vedení.":"Nelze načíst.")+'</div>'; return; }
        all=j.lide||[]; skupiny=j.skupiny||[]; draw("");
      });
      var td=null; srch.addEventListener("input",function(){ clearTimeout(td); td=setTimeout(function(){ draw(srch.value.trim()); },200); });
    }
    function personDetail(ed,p,skupiny){
      ed.innerHTML='<div class="hint">Načítám…</div>';
      api("GET","/api/v1/erp/app/hr/conditions?scope_kind=user&user_id="+p.user_id,"").then(function(j){
        ed.innerHTML="";
        if(!j||!j.ok){ ed.appendChild(el('<div class="hint">Nelze načíst.</div>')); return; }
        var glab=(skupiny.filter(function(g){return String(g.code)===String(j.group_code);})[0]||{}).label||(j.group_code?j.group_code:"— bez skupiny —");
        ed.appendChild(el('<div class="hint" style="margin-bottom:8px;">Podmínková skupina (dle členství): <b style="color:#9cf;">'+esc(glab)+'</b> <span class="hint">· mění se ve Skupinách</span></div>'));
        var st=el('<div class="hint" style="min-height:16px;margin:6px 0;"></div>'); ed.appendChild(st);
        (j.defs||[]).forEach(function(d){
          var rs=(j.resolved&&j.resolved[d.code])||{}; var own=(j.own&&j.own[d.code])?j.own[d.code].value:null;
          var row=el('<div style="display:flex;align-items:center;gap:8px;padding:6px 2px;border-bottom:1px solid #1b2742;"></div>');
          var srcCol={"osobní":"#fbbf24","skupina":"#60a5fa","systém":"#9aa"}[rs.src]||"#9aa";
          row.appendChild(el('<div style="flex:1;min-width:0;font-size:13px;">'+esc(d.label)+'<br><span class="hint">teď: <b style="color:'+srcCol+';">'+esc(rs.value==null?"—":rs.value)+'</b> ('+esc(rs.src||"—")+')</span></div>'));
          var f=fieldEl(d,own); row.appendChild(f);
          f.addEventListener("change",function(){ st.style.color="#9fb2d4"; st.textContent="Ukládám…";
            api("POST","/api/v1/erp/app/hr/conditions/save",{scope_kind:"user",user_id:p.user_id,cond_code:d.code,value:f.value}).then(function(r){
              st.style.color=(r&&r.ok)?"#5ee0b7":"#f88"; st.textContent=(r&&r.ok)?(d.label+": výjimka uložena ✓"):("✗ "+((r&&r.error)||"chyba"));
              if(r&&r.ok) setTimeout(function(){ ed.dataset.b=""; personDetail(ed,p,skupiny); },500);
            }); });
          ed.appendChild(row);
        });
        ed.appendChild(el('<div class="hint" style="margin-top:6px;">Prázdné pole = zdědí ze skupiny/systému. Vyplněné = osobní výjimka.</div>'));
        // 📅 Vzor týdne
        ed.appendChild(el('<div style="font-weight:700;margin:14px 0 2px;">📅 Vzor týdne</div>'));
        var schBox=el('<div></div>'); ed.appendChild(schBox); schBox.innerHTML='<div class="hint">Načítám…</div>';
        api("GET","/api/v1/erp/app/hr/schedule?user_id="+p.user_id,"").then(function(sj){
          schBox.innerHTML="";
          if(!sj||!sj.ok){ schBox.appendChild(el('<div class="hint">Nelze načíst.</div>')); return; }
          var info=el('<div class="hint" style="margin-bottom:4px;">Úvazek '+sj.uvazek+' h/týд · součet vzoru: <b id="schSum_'+p.user_id+'">'+sj.suma_h+'</b> h. Šedé dny = odvozeno z úvazku, dokud nenastavíš.</div>');
          schBox.appendChild(info);
          var sst=el('<div class="hint" style="min-height:14px;margin-bottom:4px;"></div>'); schBox.appendChild(sst);
          var states=[];
          function recalc(){ var sum=0; states.forEach(function(x){ if(x.chk.checked) sum+=(parseFloat(x.hin.value)||0); });
            var e=document.getElementById("schSum_"+p.user_id); if(e) e.textContent=Math.round(sum*100)/100; }
          sj.dny.forEach(function(d){
            var rowS=el('<div style="display:flex;align-items:center;gap:8px;padding:5px 2px;border-bottom:1px solid #1b2742;'+(d.explicit?'':'opacity:0.65;')+'"></div>');
            var chk=el('<input type="checkbox" '+(d.works?'checked':'')+' style="width:18px;height:18px;">');
            rowS.appendChild(chk);
            rowS.appendChild(el('<div style="width:72px;font-size:13px;">'+esc(d.label)+'</div>'));
            var hin=el('<input type="number" step="0.5" value="'+d.hours+'" style="width:56px;box-sizing:border-box;padding:6px;border-radius:8px;border:1px solid #2b3a5c;background:#0a1226;color:#e8eefc;text-align:right;">');
            rowS.appendChild(hin); rowS.appendChild(el('<span class="hint">h</span>'));
            var ein=el('<input type="text" placeholder="konec" value="'+(d.end_time||"")+'" inputmode="numeric" style="width:62px;box-sizing:border-box;padding:6px;border-radius:8px;border:1px solid #2b3a5c;background:#0a1226;color:#e8eefc;text-align:center;">');
            rowS.appendChild(ein);
            states.push({wd:d.weekday,chk:chk,hin:hin,ein:ein});
            function save(){ rowS.style.opacity="1"; sst.style.color="#9fb2d4"; sst.textContent="Ukládám…"; recalc();
              api("POST","/api/v1/erp/app/hr/schedule/save",{user_id:p.user_id,weekday:d.weekday,works:chk.checked,hours:parseFloat(hin.value)||0,end_time:ein.value.trim()}).then(function(r){
                sst.style.color=(r&&r.ok)?"#5ee0b7":"#f88"; sst.textContent=(r&&r.ok)?(d.label+" uloženo ✓"):("✗ "+((r&&r.error)||"chyba")); }); }
            chk.addEventListener("change",save); hin.addEventListener("change",save); ein.addEventListener("change",save);
            schBox.appendChild(rowS);
          });
          schBox.appendChild(el('<div class="hint" style="margin-top:6px;">Příklad: středa „konec 12:00" → zaškrtni St, hodiny 4, konec 12:00. Čtvrtek nedělá → odškrtni Čt.</div>'));
        });
      });
    }
    function render(){
      R.innerHTML="";
      R.appendChild(railBtn("⚙️","Systém","system"));
      _pd.groups.forEach(function(g){ R.appendChild(railBtn(g.icon||"👥",g.label,String(g.code))); });
      R.appendChild(railBtn("🧑","Jednotlivci","lide"));
      if(_pd.f==="lide") peopleView(); else scopeView(_pd.f);
    }
    C.innerHTML='<div class="hint">Načítám skupiny…</div>';
    api("GET","/api/v1/erp/app/hr/conditions/groups","").then(function(j){
      _pd.groups=(j&&j.ok&&j.skupiny)||[]; render();
    });
  }
  function _meIcon(lbl){ var s=(lbl||"").toLowerCase();
    if(/identi|jmén|jmen|osob/.test(s))return"🪪"; if(/osvč|osvc|ičo|ico|dič|dic|podnik/.test(s))return"🧾";
    if(/adres|bydli/.test(s))return"🏠"; if(/kontakt|e-?mail|telefon|nouz/.test(s))return"✉️";
    if(/výplat|vyplat|účet|ucet|banka|iban|pojišť|pojist/.test(s))return"🏦"; if(/doklad|rodné|op |pas|průkaz/.test(s))return"🔒";
    if(/pamě|pamet|poznám|poznam/.test(s))return"📝"; return"📄"; }
  function hr_me(){
    app.innerHTML=topbar("", true);
    var pane=el('<div style="position:relative;display:flex;gap:10px;height:calc(100vh - 168px);align-items:stretch;">'
      +'<div id="meContent" style="flex:1;min-width:0;overflow-y:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none;"><div class="hint">Načítám…</div></div>'
      +'<div id="meRail" style="width:86px;flex:none;overflow-y:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none;display:flex;flex-direction:column;gap:6px;padding:0;"></div></div>');
    app.appendChild(pane);
    var cont=pane.querySelector("#meContent"), rail=pane.querySelector("#meRail");
    var toggleBtn=el('<button style="position:absolute;top:6px;right:6px;z-index:5;display:none;padding:7px 11px;border-radius:10px;border:1px solid var(--bord);background:#1a2440;color:#cfe;font-size:13px;box-shadow:0 2px 8px rgba(0,0,0,.4);">📑 Sekce</button>');
    pane.appendChild(toggleBtn);
    function showRail(on){ rail.style.display=on?"":"none"; toggleBtn.style.display=on?"none":""; }
    // ťuknutí do seznamu → schovej lištu, plná šířka
    cont.addEventListener("click",function(){ if(rail.style.display!=="none") showRail(false); });
    toggleBtn.addEventListener("click",function(e){ e.stopPropagation(); showRail(true); });
    // Zpět: když je roztažené na celou šířku, nejdřív zúžit a vrátit lištu
    window._dochAnyOpen=function(){ if(!document.body.contains(pane)) return false;
      if(rail.style.display==="none"){ showRail(true); return true; } return false; };
    function scrollToId(id){ var t=document.getElementById(id); if(t) cont.scrollTop=Math.max(0, t.offsetTop - cont.offsetTop - 4); }
    var anchors=[], inputs={};
    function buildRail(){
      rail.innerHTML="";
      anchors.forEach(function(a){
        var b=el('<button style="width:100%;box-sizing:border-box;margin:0;padding:10px 6px;font-size:11.5px;line-height:1.2;text-align:center;word-break:break-word;border:1px solid var(--bord);background:rgba(255,255,255,0.02);color:#cdd;border-radius:11px;cursor:pointer;">'+(a.icon?('<span style="font-size:20px;display:block;line-height:1.1;margin-bottom:2px;">'+a.icon+'</span>'):'')+esc(a.label)+'</button>');
        b.addEventListener("click",function(e){ e.stopPropagation(); scrollToId(a.id); });
        rail.appendChild(b);
      });
    }
    api("GET","/api/v1/erp/app/self-data","").then(function(j){
      cont.innerHTML="";
      if(!j||!j.ok){ cont.innerHTML='<div class="hint">Nepodařilo se načíst ('+esc((j&&j.error)||"chyba")+').</div>'; return; }
      cont.appendChild(el('<div style="font-size:22px;font-weight:800;margin:2px 0 4px;">🪪 Moje osobní údaje</div>'));
      cont.appendChild(el('<div class="hint" style="line-height:1.55;margin-bottom:12px;">Tvoje údaje spravuješ ty sám — jsou <b>primárním zdrojem</b> pro smlouvu, výplatu a evidenci. Vpravo skoč rovnou na sekci; ťukni do seznamu a lišta se schová pro plnou šířku.</div>'));
      (j.sections||[]).forEach(function(sec,i){
        var sid="mesec_"+i; anchors.push({label:(sec.label||("Sekce "+(i+1))),id:sid});
        var card=el('<div id="'+sid+'" style="background:#0f1830;border:1px solid #22304f;border-radius:14px;padding:12px 14px;margin-bottom:12px;"></div>');
        card.appendChild(el('<div style="font-weight:700;font-size:16px;margin-bottom:2px;">'+esc(sec.label)+'</div>'));
        card.appendChild(el('<div class="hint" style="margin-bottom:10px;line-height:1.5;">'+esc(sec.why)+'</div>'));
        (sec.items||[]).forEach(function(it){
          var fld=el('<div style="margin-bottom:10px;"></div>');
          fld.innerHTML='<label style="display:block;font-size:13px;color:#9fb2d4;margin-bottom:3px;">'+esc(it.label)+(it.sensitive?' 🔒':'')+'</label>';
          var _sty='width:100%;box-sizing:border-box;padding:10px 12px;border-radius:10px;border:1px solid #2b3a5c;background:#0a1226;color:#e8eefc;font-size:15px;';
          var inp, isDate=(it.type==="date");
          if(it.type==="textarea"){ inp=el('<textarea rows="5" style="'+_sty+'resize:vertical;"></textarea>'); }
          else { inp=el('<input type="'+(it.type==="email"?"email":(it.type==="tel"?"tel":"text"))+'" style="'+_sty+'">'); if(isDate){ inp.placeholder="DD.MM.RRRR"; inp.inputMode="numeric"; } }
          inp.value = isDate ? _czDate(it.value) : (it.value||"");
          if(isDate) inp._isDate=true;
          if(it.key==="birth_number") inp._isRc=true;
          inputs[it.key]=inp; fld.appendChild(inp); card.appendChild(fld);
        });
        cont.appendChild(card);
      });
      if(j.updated_at){ cont.appendChild(el('<div class="hint" style="margin:-4px 0 8px;">Naposledy upraveno: '+esc(new Date(j.updated_at).toLocaleString("cs"))+'</div>')); }
      var st=el('<div class="hint" style="margin:4px 0 8px;min-height:18px;"></div>'); cont.appendChild(st);
      var btn=el('<button style="width:100%;padding:14px;border:0;border-radius:12px;background:#2563eb;color:#fff;font-size:16px;font-weight:700;margin-bottom:14px;">💾 Uložit moje údaje</button>');
      btn.addEventListener("click",function(){
        var vals={}, rcBad=false; Object.keys(inputs).forEach(function(k){ var v=inputs[k].value; if(inputs[k]._isDate) v=_isoDate(v); if(inputs[k]._isRc && (v||"").trim() && !_rcValid(v)) rcBad=true; vals[k]=v; });
        if(rcBad){ if(!confirm("Rodné číslo neprošlo kontrolou (modulo 11). Uložit přesto?"))return; }
        btn.disabled=true; st.style.color="#9fb2d4"; st.textContent="Ukládám…";
        api("POST","/api/v1/erp/app/self-data/save",{values:vals}).then(function(r){
          btn.disabled=false;
          if(r&&r.ok){ st.style.color="#5ee0b7"; st.textContent=(r.changed>0)?("Uloženo ✓ ("+r.changed+" změn)"):"Beze změn ✓"; }
          else { st.style.color="#f88"; st.textContent="Chyba: "+esc((r&&r.error)||"nepodařilo se uložit"); }
        });
      });
      cont.appendChild(btn);
      var cb=el('<div id="mesec_deti"></div>'); cont.appendChild(cb); _selfChildren(cb); anchors.push({icon:"👨‍👩‍👧",label:"Děti",id:"mesec_deti"});
      var vb=el('<div id="mesec_trezor" style="margin-top:6px;"></div>'); cont.appendChild(vb); _selfVault(vb); anchors.push({icon:"🔐",label:"Trezor",id:"mesec_trezor"});
      cont.appendChild(el('<div style="height:30px;"></div>'));
      buildRail();
    });
  }
  // --- karta: deti/blizke osoby ---
  function _card(title,hint){ var c=el('<div style="background:#0f1830;border:1px solid #22304f;border-radius:14px;padding:12px 14px;margin-bottom:12px;"></div>'); c.appendChild(el('<div style="font-weight:700;font-size:16px;margin-bottom:2px;">'+title+'</div>')); if(hint)c.appendChild(el('<div class="hint" style="margin-bottom:10px;line-height:1.5;">'+esc(hint)+'</div>')); return c; }
  function _fld(label,val,ph){ var w=el('<div style="margin-bottom:8px;"></div>'); w.innerHTML='<label style="display:block;font-size:12px;color:#9fb2d4;margin-bottom:3px;">'+esc(label)+'</label>'; var i=el('<input type="text" style="width:100%;box-sizing:border-box;padding:9px 11px;border-radius:9px;border:1px solid #2b3a5c;background:#0a1226;color:#e8eefc;font-size:15px;">'); i.value=val||""; if(ph)i.placeholder=ph; w.appendChild(i); w._inp=i; return w; }
  function _selfChildren(box){
    function render(j){
      box.innerHTML="";
      var card=_card("👨‍👩‍👧 Děti a blízké osoby","Rodná čísla dětí pro slevu na dani a kontakty na blízké. Soukromé — vidíš jen ty (a HR pro daňové).");
      box.appendChild(card);
      var deti=(j&&j.ok&&j.deti)?j.deti:[];
      if(!deti.length){ card.appendChild(el('<div class="hint" style="padding:8px 0;">Zatím nikdo. Přidej dítě nebo blízkou osobu.</div>')); }
      deti.forEach(function(d){
        var r=el('<div style="display:flex;align-items:center;gap:8px;padding:8px 0;border-top:1px solid #1b2742;"></div>');
        var t=(d.child_name||"(bez jména)")+(d.relation?(" · "+d.relation):"")+(d.relief_order?(" · "+d.relief_order+". dítě"):"");
        var sub=[_czDate(d.birth_date),d.birth_number].filter(Boolean).join(" · ");
        r.appendChild(el('<div style="flex:1;"><div style="font-weight:600;">'+esc(t)+'</div>'+(sub?'<div class="hint">'+esc(sub)+'</div>':'')+'</div>'));
        var e=el('<button style="background:#1d2a44;border:0;color:#cfe;border-radius:8px;padding:6px 9px;">✏️</button>'); e.onclick=function(){ form(d); }; r.appendChild(e);
        var x=el('<button style="background:#3a1d28;border:0;color:#f9b;border-radius:8px;padding:6px 9px;">🗑</button>'); x.onclick=function(){ if(confirm("Smazat "+(d.child_name||"záznam")+"?")) api("POST","/api/v1/erp/app/self-child/delete",{id:d.id}).then(load); }; r.appendChild(x);
        card.appendChild(r);
      });
      var add=el('<button style="width:100%;margin-top:8px;padding:10px;border:1px dashed #2b3a5c;border-radius:10px;background:transparent;color:#9fd;">➕ Přidat</button>'); add.onclick=function(){ form(null); }; card.appendChild(add);
    }
    function form(d){
      d=d||{}; box.innerHTML="";
      var f=_card(d.id?"Upravit":"➕ Přidat dítě / blízkou osobu",""); box.appendChild(f);
      var fn=_fld("Jméno",d.child_name), rel=_fld("Vztah (dítě / manželka / …)",d.relation),
          bd=_fld("Datum narození",_czDate(d.birth_date),"DD.MM.RRRR"), rc=_fld("Rodné číslo",d.birth_number),
          ord=_fld("Pořadí dítěte pro slevu (1/2/3)",d.relief_order), em=_fld("E-mail",d.email), ph=_fld("Telefon",d.phone);
      [fn,rel,bd,rc,ord,em,ph].forEach(function(w){f.appendChild(w);});
      var save=el('<button style="width:100%;padding:11px;border:0;border-radius:10px;background:#2563eb;color:#fff;font-weight:700;">💾 Uložit</button>');
      save.onclick=function(){
        var rcv=(rc._inp.value||"").trim();
        if(rcv && !_rcValid(rcv)){ if(!confirm("Rodné číslo neprošlo kontrolou (modulo 11). Uložit přesto?"))return; }
        api("POST","/api/v1/erp/app/self-child/save",{id:d.id,child_name:fn._inp.value,relation:rel._inp.value,birth_date:_isoDate(bd._inp.value),birth_number:rcv,relief_order:ord._inp.value,email:em._inp.value,phone:ph._inp.value}).then(function(r){ if(r&&r.ok)load(); else alert("Chyba: "+((r&&r.error)||"?")); });
      };
      f.appendChild(save);
      var back=el('<button style="width:100%;margin-top:6px;padding:9px;border:0;border-radius:10px;background:#26304a;color:#cdd;">Zpět</button>'); back.onclick=load; f.appendChild(back);
    }
    function load(){ api("GET","/api/v1/erp/app/self-child","").then(render); }
    load();
  }
  // --- karta: trezor hesel ---
  function _selfVault(box){
    function reveal(id,label){
      var pin=prompt("Zadej PIN pro zobrazení hesla:"); if(!pin)return;
      api("POST","/api/v1/erp/app/self-secret/reveal",{id:id,pin:pin}).then(function(x){
        if(x&&x.ok){ prompt("🔓 "+(x.label||label)+" (zkopíruj):", x.secret); }
        else alert("Chyba: "+((x&&(x.note||x.error))||"?"));
      });
    }
    function render(j){
      box.innerHTML="";
      var card=_card("🔐 Hesla a tokeny","Šifrované. Zobrazení jen po PINu + SMS kódu. Nikdo jiný (ani HR, ani vedení) je nevidí. Každé otevření ti přijde e-mailem.");
      box.appendChild(card);
      if(!j||!j.ok){ card.appendChild(el('<div class="hint">Nelze načíst.</div>')); return; }
      if(!j.vault_ready){ card.appendChild(el('<div class="hint" style="color:#fc8;">Trezor zatím není aktivní — čeká na bezpečnostní klíč na serveru.</div>')); return; }
      if(!j.has_pin){ card.appendChild(el('<div class="hint" style="color:#fc8;">Nejdřív si nastav PIN (Nastavení → PIN), pak půjde trezor odemykat.</div>')); }
      var pol=j.polozky||[];
      if(!pol.length){ card.appendChild(el('<div class="hint" style="padding:8px 0;">Trezor je prázdný. Ulož si první heslo.</div>')); }
      pol.forEach(function(p){
        var r=el('<div style="display:flex;align-items:center;gap:8px;padding:8px 0;border-top:1px solid #1b2742;"></div>');
        r.appendChild(el('<div style="flex:1;"><div style="font-weight:600;">'+esc(p.label)+'</div>'+(p.username?'<div class="hint">'+esc(p.username)+'</div>':'')+'</div>'));
        var v=el('<button style="background:#1d3a2a;border:0;color:#9f9;border-radius:8px;padding:6px 9px;">👁</button>'); v.onclick=function(){ reveal(p.id,p.label); }; r.appendChild(v);
        var e=el('<button style="background:#1d2a44;border:0;color:#cfe;border-radius:8px;padding:6px 9px;">✏️</button>'); e.onclick=function(){ form(p); }; r.appendChild(e);
        var x=el('<button style="background:#3a1d28;border:0;color:#f9b;border-radius:8px;padding:6px 9px;">🗑</button>'); x.onclick=function(){ if(confirm("Smazat „"+p.label+"\"?")) api("POST","/api/v1/erp/app/self-secret/delete",{id:p.id}).then(load); }; r.appendChild(x);
        card.appendChild(r);
      });
      var add=el('<button style="width:100%;margin-top:8px;padding:10px;border:1px dashed #2b3a5c;border-radius:10px;background:transparent;color:#9fd;">➕ Přidat heslo / token</button>'); add.onclick=function(){ form(null); }; card.appendChild(add);
    }
    function form(p){
      p=p||{}; box.innerHTML="";
      var f=_card(p.id?"Upravit položku":"➕ Nové heslo / token",""); box.appendChild(f);
      var lb=_fld("Název (např. Email, VPN, banka)",p.label), un=_fld("Uživatel / login",p.username),
          se=_fld("Heslo / token",""), ur=_fld("Web / poznámka kam",p.url);
      if(p.id) se._inp.placeholder="(nech prázdné = ponechat stávající)";
      [lb,un,se,ur].forEach(function(w){f.appendChild(w);});
      var save=el('<button style="width:100%;padding:11px;border:0;border-radius:10px;background:#2563eb;color:#fff;font-weight:700;">💾 Uložit zašifrovaně</button>');
      save.onclick=function(){ api("POST","/api/v1/erp/app/self-secret/save",{id:p.id,label:lb._inp.value,username:un._inp.value,secret:se._inp.value,url:ur._inp.value}).then(function(r){ if(r&&r.ok)load(); else alert("Chyba: "+((r&&(r.note||r.error))||"?")); }); };
      f.appendChild(save);
      var back=el('<button style="width:100%;margin-top:6px;padding:9px;border:0;border-radius:10px;background:#26304a;color:#cdd;">Zpět</button>'); back.onclick=load; f.appendChild(back);
    }
    function load(){ api("GET","/api/v1/erp/app/self-secret","").then(render); }
    load();
  }
  // --- HR: prehled lidi + karta (jen HR/rodice; citlive se nezobrazuji) ---
