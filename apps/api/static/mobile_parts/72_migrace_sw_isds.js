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
