  function hr_people(){
    app.innerHTML=topbar("👥 Personální složky", true);
    var srch=el('<input type="text" placeholder="Hledat jméno…" style="width:100%;box-sizing:border-box;padding:11px 13px;border-radius:10px;border:1px solid #2b3a5c;background:#0a1226;color:#e8eefc;font-size:15px;margin-bottom:10px;">');
    app.appendChild(srch);
    var _hp={f:"vse",data:[]};
    var pane=el('<div style="display:flex;gap:10px;height:calc(62vh - 86px);align-items:stretch;">'
      +'<div style="flex:1;min-width:0;overflow-y:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none;border:1px solid var(--bord);border-radius:12px;background:rgba(255,255,255,0.02);padding:2px 8px;"><ul id="hpList" style="padding:0;list-style:none;margin:0;"></ul></div>'
      +'<div id="hpRail" style="width:72px;flex:none;overflow-y:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none;display:flex;flex-direction:column;gap:7px;padding:0;"></div></div>');
    app.appendChild(pane);
    function _hpLetter(p){ var c=((p.jmeno||"").trim().charAt(0)||"#").toUpperCase();
      return c.replace(/[ÁÄ]/,'A').replace(/[ČC]/,'C').replace(/[ĎD]/,'D').replace(/[ÉĚE]/,'E').replace(/Í/,'I').replace(/[ŇN]/,'N').replace(/[ÓÖ]/,'O').replace(/[ŘR]/,'R').replace(/[ŠS]/,'S').replace(/[ŤT]/,'T').replace(/[ÚŮÜU]/,'U').replace(/[ÝY]/,'Y').replace(/[ŽZ]/,'Z'); }
    function _hpPass(p,k){ k=k||_hp.f; if(k==="vse")return true; return _hpLetter(p)===k;
    }
    function _hpRailBtn(letter,key){
      var on=(_hp.f===key); var c=(key==="vse")?_hp.data.length:_hp.data.filter(function(p){return _hpPass(p,key);}).length;
      var bdg=(c>0&&key!=="vse")?'<span style="position:absolute;top:4px;right:6px;min-width:16px;height:16px;line-height:14px;border-radius:8px;background:var(--green);color:#241a02;font-size:9.5px;font-weight:700;padding:0 2px;box-sizing:border-box;text-align:center;">'+c+'</span>':'';
      var b=el('<button style="position:relative;width:100%;box-sizing:border-box;margin:0;padding:10px 2px;font-size:18px;font-weight:700;display:flex;align-items:center;justify-content:center;border:1px solid '+(on?"var(--green)":"var(--bord)")+';background:'+(on?"var(--green)":"rgba(255,255,255,0.02)")+';color:'+(on?"#04150e":"var(--mut)")+';border-radius:12px;cursor:pointer;">'+letter+bdg+'</button>');
      b.addEventListener("click",function(){ _hp.f=key; render(); });
      return b;
    }
    function render(){
      var rail=document.getElementById("hpRail"), ul=document.getElementById("hpList");
      if(!rail||!ul) return;
      rail.innerHTML=""; rail.appendChild(_hpRailBtn("∗","vse"));
      var letters={}; _hp.data.forEach(function(p){ letters[_hpLetter(p)]=1; });
      Object.keys(letters).sort().forEach(function(L){ rail.appendChild(_hpRailBtn(L,L)); });
      ul.innerHTML="";
      var arr=_hp.data.filter(function(p){return _hpPass(p);});
      if(!arr.length){ ul.appendChild(el('<li style="border:none;color:var(--mut);">Nikdo nenalezen.</li>')); return; }
      arr.forEach(function(p){
        var ini=((p.jmeno||"?").trim().charAt(0)||"?").toUpperCase();
        var li=el('<li style="border:none;display:flex;align-items:center;gap:12px;padding:9px 4px;border-bottom:1px solid #1b2742;cursor:pointer;"></li>');
        li.appendChild(el('<div style="width:38px;height:38px;border-radius:50%;background:'+avColor(p.jmeno)+';color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:16px;flex:0 0 auto;">'+esc(ini)+'</div>'));
        li.appendChild(el('<div style="flex:1;min-width:0;"><div style="font-weight:600;">'+esc(p.jmeno)+'</div>'+(p.mesto?'<div class="hint">'+esc(p.mesto)+'</div>':'')+'</div>'));
        li.appendChild(el('<div class="chev" style="color:#5a6;">&#8250;</div>'));
        li.addEventListener("click",function(){ window._hrUid=p.user_id; window._hrName=p.jmeno; go("hr_person"); });
        ul.appendChild(li);
      });
    }
    function load(q){
      var ul=document.getElementById("hpList"); if(ul) ul.innerHTML='<li style="border:none;color:var(--mut);">Načítám…</li>';
      api("GET","/api/v1/erp/app/hr/people"+(q?("?q="+encodeURIComponent(q)):""),"").then(function(j){
        if(!j||!j.ok){ if(ul) ul.innerHTML='<li style="border:none;color:var(--mut);">'+esc((j&&j.error==="forbidden")?"Nemáš přístup (jen HR / vedení).":"Nelze načíst.")+'</li>'; return; }
        _hp.data=j.lide||[]; _hp.f="vse"; render();
      });
    }
    var _td=null; srch.addEventListener("input",function(){ clearTimeout(_td); _td=setTimeout(function(){ load(srch.value.trim()); },250); });
    load("");
  }
  function hr_rezimy(){
    app.innerHTML=topbar("🧩 Režimy docházky", true);
    var srch=el('<input type="text" placeholder="Hledat jméno…" style="width:100%;box-sizing:border-box;padding:11px 13px;border-radius:10px;border:1px solid #2b3a5c;background:#0a1226;color:#e8eefc;font-size:15px;margin-bottom:10px;">');
    app.appendChild(srch);
    app.appendChild(el('<div class="hint" style="margin-bottom:8px;line-height:1.5;">Forma a režim jsou nezávislé. Píchají všichni; režim řeší jen odměnu/řízení. Člověk může mít víc záznamů (firmy/formy/tenanty).</div>'));
    var FORMY=[["HPP","HPP"],["DPP","DPP"],["OSVC","OSVČ"]];
    var REZIMY=[["hodinovy","Hodinový"],["volny","Volný"],["pausal","Paušál"]];
    var addBtn=el('<button class="ghost full" style="margin-bottom:10px;border-color:var(--blue);color:var(--blue);">➕ Přidat angažmá (další firma / forma / tenant)</button>');
    var addBox=el('<div style="display:none;border:1px solid var(--blue);border-radius:12px;padding:12px;margin-bottom:12px;"></div>');
    addBtn.addEventListener("click",function(){ if(addBox.style.display==='none'){ addBox.style.display='block'; buildAdd(addBox); } else { addBox.style.display='none'; } });
    app.appendChild(addBtn); app.appendChild(addBox);
    var _rz={f:"vse",data:[]};
    var pane=el('<div style="display:flex;gap:10px;height:calc(58vh - 86px);align-items:stretch;">'
      +'<div style="flex:1;min-width:0;overflow-y:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none;border:1px solid var(--bord);border-radius:12px;background:rgba(255,255,255,0.02);padding:2px 8px;"><ul id="rezList" style="padding:0;list-style:none;margin:0;"></ul></div>'
      +'<div id="rezRail" style="width:72px;flex:none;overflow-y:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none;display:flex;flex-direction:column;gap:7px;padding:0;"></div></div>');
    app.appendChild(pane);
    function _rzRailBtn(icon,label,key){
      var on=(_rz.f===key);
      var c=(key==="vse")?_rz.data.length:_rz.data.filter(function(p){ return _rzPass(p,key); }).length;
      var bdg=(c>0)?'<span style="position:absolute;top:4px;right:6px;min-width:17px;height:17px;line-height:15px;border-radius:9px;border:1px solid rgba(0,0,0,.25);background:var(--green);color:#241a02;font-size:10px;font-weight:700;padding:0 3px;box-sizing:border-box;text-align:center;">'+c+'</span>':'';
      var b=el('<button style="position:relative;width:100%;box-sizing:border-box;margin:0;padding:11px 2px;font-size:10.5px;line-height:1.15;display:flex;flex-direction:column;align-items:center;gap:4px;border:1px solid '+(on?"var(--green)":"var(--bord)")+';background:'+(on?"var(--green)":"rgba(255,255,255,0.02)")+';color:'+(on?"#04150e":"var(--mut)")+';border-radius:13px;cursor:pointer;"><span style="font-size:24px;line-height:1;">'+icon+'</span>'+label+bdg+'</button>');
      b.addEventListener("click",function(){ _rz.f=key; render(); });
      return b;
    }
    function _rzPass(p,k){ k=k||_rz.f;
      if(k==="vse")return true;
      if(k==="2"||k==="14")return String(p.tenant_id)===k;
      if(k==="konto")return !!p.konto_aktivni;
      return p.forma===k; }
    function buildAdd(box){
      box.innerHTML='<div class="hint">Načítám lidi…</div>';
      api("GET","/api/v1/erp/app/hr/people","").then(function(j){
        var ps=''; ((j&&j.lide)||[]).forEach(function(p){ ps+='<option value="'+p.user_id+'">'+esc(p.jmeno)+'</option>'; });
        var w=el('<div></div>');
        w.innerHTML='<label class="hint" style="display:block;margin:2px 0 2px;">Osoba</label>'
          +'<select style="width:100%;padding:9px;border-radius:9px;border:1px solid #2b3a5c;background:#0a1226;color:#e8eefc;">'+ps+'</select>'
          +sel("Firma / tenant",[["2","EUROSOFT"],["14","INTERSOFT"]],"2")
          +sel("Právní forma",FORMY,"OSVC")+sel("Mzdový režim",REZIMY,"hodinovy");
        var sa=w.querySelectorAll("select");
        var b=el('<button class="green full" style="margin-top:10px;">Vytvořit angažmá</button>');
        var st=el('<div class="hint" style="margin-top:6px;"></div>');
        b.addEventListener("click",function(){ b.disabled=true; st.textContent="Vytvářím…";
          api("POST","/api/v1/erp/app/hr/rezim/add",{user_id:parseInt(sa[0].value),tenant_id:parseInt(sa[1].value),
            forma:sa[2].value,mzdovy:sa[3].value}).then(function(r){
              b.disabled=false; st.textContent=(r&&r.ok)?"✅ Přidáno":("✗ "+((r&&r.error)||"chyba"));
              if(r&&r.ok){ setTimeout(function(){ addBox.style.display='none'; load(srch.value.trim()); },700); }
            }); });
        w.appendChild(b); w.appendChild(st); box.innerHTML=""; box.appendChild(w);
      });
    }
    var VOLBY=[["na_vyber","Na výběr"],["premie","Do prémie"],["prescas","Do přesčasu"],["prevest","Převést"]];
    function chip(t,c){ return '<span style="background:'+c+';color:#04150e;border-radius:8px;padding:2px 7px;font-size:11px;font-weight:700;">'+esc(t)+'</span>'; }
    function sel(label,opts,val){ var s='<label class="hint" style="display:block;margin:6px 0 2px;">'+label+'</label><select style="width:100%;padding:9px;border-radius:9px;border:1px solid #2b3a5c;background:#0a1226;color:#e8eefc;">';
      opts.forEach(function(o){ s+='<option value="'+o[0]+'"'+(o[0]===val?' selected':'')+'>'+esc(o[1])+'</option>'; }); return s+'</select>'; }
    function numf(label,val){ return '<label class="hint" style="display:block;margin:6px 0 2px;">'+label+'</label><input type="number" step="0.5" value="'+(val||0)+'" style="width:100%;box-sizing:border-box;padding:9px;border-radius:9px;border:1px solid #2b3a5c;background:#0a1226;color:#e8eefc;">'; }
    function buildEdit(box,p){
      var w=el('<div></div>');
      w.innerHTML=sel("Právní forma",FORMY,p.forma)+sel("Mzdový režim",REZIMY,p.mzdovy)
        +numf("Loajalita — manko do minusu (h/měs)",p.loajalita_minus_h)
        +numf("Přesčas-polštář neproplácený (h/den)",p.prescas_plus_h_den)
        +numf("Paušál (Kč/měs, jen režim paušál)",p.pausal_kc)
        +'<label class="hint" style="display:flex;align-items:center;gap:8px;margin:10px 0 2px;"><input type="checkbox" '+(p.konto_aktivni?'checked':'')+'> Konto přesčasů aktivní</label>'
        +sel("Default dispozice konta",VOLBY,p.konto_volba)
        +numf("Příplatek za přesčas (%)",p.prescas_priplatek_pct);
      var sels=w.querySelectorAll("select"), nums=w.querySelectorAll("input[type=number]"), chk=w.querySelector("input[type=checkbox]");
      var btn=el('<button class="green full" style="margin-top:10px;">Uložit</button>');
      var st=el('<div class="hint" style="margin-top:6px;"></div>');
      btn.addEventListener("click",function(){ btn.disabled=true; st.textContent="Ukládám…";
        api("POST","/api/v1/erp/app/hr/rezim/save",{emp_id:p.emp_id,
          forma:sels[0].value, mzdovy:sels[1].value, konto_volba:sels[2].value,
          loajalita_minus_h:parseFloat(nums[0].value)||0, prescas_plus_h_den:parseFloat(nums[1].value)||0,
          pausal_kc:parseFloat(nums[2].value)||0, prescas_priplatek_pct:parseFloat(nums[3].value)||0,
          konto_aktivni:chk.checked}).then(function(r){
            btn.disabled=false; st.textContent=(r&&r.ok)?"✅ Uloženo":("✗ "+((r&&r.error)||"chyba")); if(r&&r.ok) setTimeout(function(){ load(srch.value.trim()); },600);
          });
      });
      w.appendChild(btn); w.appendChild(st); box.appendChild(w);
    }
    function render(){
      var rail=document.getElementById("rezRail"), ul=document.getElementById("rezList");
      if(!rail||!ul) return;
      rail.innerHTML="";
      [["📋","Vše","vse"],["🟢","HPP","HPP"],["🟣","DPP","DPP"],["🟠","OSVČ","OSVC"],["🏢","EUR","2"],["🏬","INT","14"],["🏦","Konto","konto"]].forEach(function(it){
        if(it[2]==="vse"||_rz.data.filter(function(p){return _rzPass(p,it[2]);}).length>0) rail.appendChild(_rzRailBtn(it[0],it[1],it[2]));
      });
      ul.innerHTML="";
      var arr=_rz.data.filter(function(p){return _rzPass(p);});
      if(!arr.length){ ul.appendChild(el('<li style="border:none;color:var(--mut);">Nikdo.</li>')); return; }
      arr.forEach(function(p){
        var fc=(p.forma==='OSVC')?'#f59e0b':(p.forma==='DPP'?'#a78bfa':'#34d399');
        var rc=(p.mzdovy==='volny')?'#60a5fa':(p.mzdovy==='pausal'?'#a78bfa':'#34d399');
        var rez={hodinovy:'Hodinový',volny:'Volný',pausal:'Paušál'}[p.mzdovy]||p.mzdovy;
        var forma={HPP:'HPP',DPP:'DPP',OSVC:'OSVČ'}[p.forma]||p.forma;
        var firmaLbl=p.firma||(p.tenant_id===14?'INTERSOFT':(p.tenant_id===2?'EUROSOFT':''));
        var li=el('<li class="ct" style="border:none;border-bottom:1px solid #1b2742;padding:0;"></li>');
        var head=el('<div style="display:flex;align-items:center;gap:10px;cursor:pointer;padding:9px 4px;"></div>');
        head.appendChild(el('<div style="flex:1;min-width:0;"><div style="font-weight:600;">'+esc(p.jmeno)+(firmaLbl?(' <span class="hint">· '+esc(firmaLbl)+'</span>'):'')+'</div><div style="margin-top:4px;display:flex;gap:5px;flex-wrap:wrap;">'+chip(forma,fc)+chip(rez,rc)+(p.tenant_id===14?chip('INTERSOFT','#60a5fa'):'')+(p.konto_aktivni?chip('konto','#fbbf24'):'')+'</div></div>'));
        head.appendChild(el('<div class="chev" style="color:#5a6;">&#8250;</div>'));
        var ed=el('<div class="ctexp" style="display:none;padding:0 4px 10px;"></div>');
        head.addEventListener("click",function(){
          var open=li.classList.toggle("open"); ed.style.display=open?"block":"none";
          if(open && ed.dataset.built!=='1'){ buildEdit(ed,p); ed.dataset.built='1'; }
          _railSync("rezRail","rezList");
        });
        li.appendChild(head); li.appendChild(ed); ul.appendChild(li);
      });
      _railSync("rezRail","rezList");
    }
    function load(q){
      var ul=document.getElementById("rezList"); if(ul) ul.innerHTML='<li style="border:none;color:var(--mut);">Načítám…</li>';
      api("GET","/api/v1/erp/app/hr/rezimy"+(q?("?q="+encodeURIComponent(q)):""),"").then(function(j){
        if(!j||!j.ok){ if(ul) ul.innerHTML='<li style="border:none;color:var(--mut);">'+esc((j&&j.error==="forbidden")?"Nemáš přístup (jen HR / vedení).":"Nelze načíst.")+'</li>'; return; }
        _rz.data=j.lide||[]; render();
      });
    }
    var _td=null; srch.addEventListener("input",function(){ clearTimeout(_td); _td=setTimeout(function(){ load(srch.value.trim()); },250); });
    load("");
  }
