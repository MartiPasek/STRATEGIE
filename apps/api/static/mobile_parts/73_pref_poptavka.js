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

  var SCREENS={home:home,poptavka:poptavka,phone:phone,notifs:notifs,claudetasks:claudetasks,claudeDetail:claudeDetail,mytodo:mytodo,ecukoly:ecukoly,strtask:strtask,contacts:contacts,calllog:calllog,settings:settings,apps:apps,firma:firma,vyroba:vyroba,vyroba_hub:vyroba_hub,vedeni:vedeni,soon:soon,skupiny:skupiny,sdileny:sdileny,dochazka:dochazka,alluser:alluser,set_listen:set_listen,set_icons:set_icons,set_install:set_install,set_prefixes:set_prefixes,set_phone:set_phone,set_notifaccess:set_notifaccess,set_dev:set_dev,set_about:set_about,strategie_nastroje:strategie_nastroje,apid_restore:apid_restore,set_imp:set_imp,set_smsgw:set_smsgw,set_shot:set_shot,urgent:urgent,hr_hub:hr_hub,hr:hr,hr_interni:hr_interni,hr_firma:hr_firma,hr_skupiny:hr_skupiny,hr_nabor:hr_nabor,hr_naroz:hr_naroz,hr_novi:hr_novi,hr_nabor_list:hr_nabor_list,hr_nabor_detail:hr_nabor_detail,hr_cv_result:hr_cv_result,hr_soon:hr_soon,hr_me:hr_me,hr_people:hr_people,hr_rezimy:hr_rezimy,hr_att_source:hr_att_source,ocr:ocr,ocr_schval:ocr_schval,sick:sick,sick_schval:sick_schval,np_prehled:np_prehled,med:med,med_schval:med_schval,med_prehled:med_prehled,hr_konto:hr_konto,hr_import:hr_import,hr_podminky:hr_podminky,moje_podminky:moje_podminky,absence:absence,kdekdo:kdekdo,hr_person:hr_person,sms_stav:sms_stav,dev_stav:dev_stav,doc_gen:doc_gen,wage_cmp:wage_cmp,kara:kara,kara_new:kara_new,kara_detail:kara_detail,kara_motive:kara_motive,kara_ref:kara_ref,kara_quad:kara_quad,kara_board:kara_board,hr_inzeraty:hr_inzeraty,hr_inzerat_edit:hr_inzerat_edit,ops:ops,plan:plan,plan_vyjimky:plan_vyjimky,moje_cinnosti:moje_cinnosti,master_cinnosti:master_cinnosti,prace:prace,prace_zak:prace_zak,prace_cin:prace_cin,webview:webview,web_stats:web_stats,doch_dnesek:doch_dnesek,doch_historie:doch_historie,doch_zitrek:doch_zitrek,doch_opravy:doch_opravy,doch_opravy_den:doch_opravy_den,moje_finance:moje_finance,moje_zadosti:moje_zadosti,planapprovals:planapprovals,bk_rozvrh:bk_rozvrh,bk_tridy:bk_tridy,bk_ucitele:bk_ucitele,bk_class:bk_class,bk_teacher:bk_teacher,bk_ucebny:bk_ucebny,bk_room:bk_room,bk_uvazky:bk_uvazky,bk_skola:bk_skola,uceni:uceni,migrace:migrace,migrace_dochazka:migrace_dochazka,migrace_mzdy:migrace_mzdy,prefakturace:prefakturace,isds:isds,sw_zakazky:sw_zakazky,extview:extview,persDnesek:persDnesek,claude27:claude27,coord:coord,fronta:fronta};

  // Claude-27 týmová hra (Marti 24.6.2026): Zuzka (+Mirek) vidí frontu Clauda-27
  // a dá mu „Go", když stojí. Slyšitelné notifikace chodí přes mobile_command.
