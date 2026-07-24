  // ── Cílový režim — nativní obrazovka v appce (Kristý + C24, 24.7.2026) ──────
  // Proč nativní (ne iframe /cil): nativní appka se autentizuje Bearer tokenem,
  // ne cookie — vnořená stránka token nevidí → 401. Tady jedeme přes appkovou
  // api() (B.authedFetch/token na mobilu, cookie na webu) → funguje všude.
  // Data z /app/cil*. Registrace do SCREENS (definováno v 73_pref_poptavka.js).
  var _cilFiltr="", _cilId=0;
  var _CIL_STAV_L={navrzen:"Návrh",schvalen:"Schválen",aktivni:"Aktivní",splnen:"Splněn",zamitnut:"Zamítnut",pozastaven:"Pozastaven"};
  var _CIL_FILTRY=[["","Vše"],["navrzen","Čeká na schválení"],["aktivni","Aktivní"],["pozastaven","Pozastavené"],["splnen","Hotové"],["zamitnut","Zamítnuté"]];
  var _CIL_COL={navrzen:"#e8b13a",schvalen:"#4f9dff",aktivni:"#4f9dff",splnen:"#3fbf6b",zamitnut:"#ef6a6a",pozastaven:"#8ea3bd"};
  function _cilBadge(s){ var c=_CIL_COL[s]||"#8ea3bd"; return '<span style="flex:none;font-size:11px;font-weight:700;padding:3px 9px;border-radius:999px;background:'+c+'22;color:'+c+';text-transform:uppercase;letter-spacing:.3px;">'+esc(_CIL_STAV_L[s]||s)+'</span>'; }
  // Vlastní „← Zpět" — appka na Androidu skrývá spodní back lištu (systémové Zpět),
  // tak dáme viditelné tlačítko do obrazovky (funguje na všech platformách).
  function _cilBack(){ var b=el('<div style="color:var(--blue);font-size:15px;font-weight:600;padding:8px 4px 6px;cursor:pointer;">← Zpět</div>'); b.addEventListener("click",back); return b; }

  function cil(){
    app.innerHTML=topbar("🎯 Cíle", true);
    app.appendChild(_cilBack());
    var p=el('<div class="panel"></div>');
    var nb=el('<button class="green full" style="margin:0 0 10px;">＋ Nový cíl</button>');
    nb.addEventListener("click",function(){ go("cil_new"); });
    p.appendChild(nb);
    var chips=el('<div style="display:flex;gap:8px;overflow-x:auto;padding-bottom:8px;margin-bottom:8px;"></div>');
    _CIL_FILTRY.forEach(function(f){
      var on=(f[0]===_cilFiltr);
      var c=el('<div style="flex:none;padding:7px 13px;border-radius:999px;font-size:13px;cursor:pointer;border:1px solid var(--bord);background:'+(on?"var(--blue)":"transparent")+';color:'+(on?"#fff":"var(--mut)")+';">'+esc(f[1])+'</div>');
      c.addEventListener("click",function(){ _cilFiltr=f[0]; cil(); });
      chips.appendChild(c);
    });
    p.appendChild(chips);
    p.appendChild(el('<div class="list" id="cilList"><div class="hint">Načítám…</div></div>'));
    app.appendChild(p);
    var q=_cilFiltr?("?stav="+encodeURIComponent(_cilFiltr)):"";
    api("GET","/api/v1/erp/app/cil"+q,"").then(function(j){
      var box=document.getElementById("cilList"); if(!box)return; box.innerHTML="";
      if(!j||!j.ok){ box.appendChild(el('<div class="hint" style="color:#fc8;">'+esc((j&&j.error)||"Nepodařilo se načíst cíle.")+'</div>')); return; }
      var cile=j.cile||[];
      if(!cile.length){ box.appendChild(el('<div class="hint">Žádné cíle v tomto filtru.</div>')); return; }
      cile.forEach(function(c){
        var card=el('<div style="background:var(--surf);border:1px solid var(--bord);border-radius:12px;padding:13px;margin-bottom:9px;cursor:pointer;"></div>');
        card.innerHTML='<div style="display:flex;justify-content:space-between;gap:8px;align-items:center;"><span style="font-weight:600;">'+esc(c.nazev)+'</span>'+_cilBadge(c.stav)+'</div>'
          +'<div style="display:flex;justify-content:space-between;gap:8px;margin-top:4px;"><span style="color:var(--mut);font-size:12px;">#'+c.id+' · '+esc(c.navrhl_jmeno||("#"+c.navrhl_user_id))+' · '+esc(c.created||"")+'</span><span style="color:var(--mut);font-size:12px;">'+(c.kroku||0)+' kroků</span></div>'
          +(c.popis?'<div style="color:var(--mut);font-size:12.5px;margin-top:4px;">'+esc(c.popis)+'</div>':'');
        card.addEventListener("click",function(){ _cilId=c.id; go("cil_detail"); });
        box.appendChild(card);
      });
    }).catch(function(){ var box=document.getElementById("cilList"); if(box) box.innerHTML='<div class="hint" style="color:#fc8;">Chyba spojení.</div>'; });
  }

  function cil_detail(){
    app.innerHTML=topbar("🎯 Cíl", true);
    app.appendChild(_cilBack());
    var p=el('<div class="panel"><div class="hint">Načítám…</div></div>');
    app.appendChild(p);
    api("GET","/api/v1/erp/app/cil/"+_cilId,"").then(function(j){
      if(!j||!j.ok){ p.innerHTML='<div class="hint" style="color:#fc8;">'+esc((j&&j.error)||"Cíl nenalezen.")+'</div>'; return; }
      var c=j.cil, log=j.kroky_log||[];
      function fld(k,v){ return v?('<div style="margin:8px 0;"><div style="color:var(--mut);font-size:12px;">'+esc(k)+'</div><div>'+esc(v)+'</div></div>'):""; }
      var h='<div style="display:flex;justify-content:space-between;gap:8px;align-items:center;"><div style="font-weight:700;font-size:18px;">'+esc(c.nazev)+'</div>'+_cilBadge(c.stav)+'</div>';
      h+='<div style="color:var(--mut);font-size:12.5px;margin:4px 0 10px;">#'+c.id+' · navrhl '+esc(c.navrhl_jmeno||("#"+c.navrhl_user_id))+' · '+esc(c.created||"")+'</div>';
      h+=fld("Popis",c.popis)+fld("Rozsah (čeho se smí dotknout)",c.rozsah);
      h+='<div style="margin:8px 0;"><div style="color:var(--mut);font-size:12px;">Strop kroků</div><div>'+(c.strop_kroku!=null?c.strop_kroku:"—")+' · zatím '+(c.kroku||0)+' kroků</div></div>';
      if(c.okno_od||c.okno_do) h+=fld("Časové okno",(c.okno_od||"—")+" → "+(c.okno_do||"—"));
      if(c.schvalil_jmeno) h+=fld("Schválil",(c.schvalil_jmeno||"")+" · "+(c.schvaleno_at||""));
      if(c.uzavren_at) h+=fld("Uzavřeno",c.uzavren_at);
      p.innerHTML=h;
      var btns=el('<div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:12px;"></div>');
      function actBtn(label,color,dark,akce){
        var b=el('<button style="flex:1;min-width:120px;margin:0;border:0;border-radius:12px;padding:13px;font-size:15px;font-weight:700;color:'+(dark?"#20160a":"#fff")+';background:'+color+';">'+label+'</button>');
        b.addEventListener("click",function(){ b.disabled=true; api("POST","/api/v1/erp/app/cil/"+_cilId+"/"+akce,{}).then(function(r){ if(r&&r.ok){ cil_detail(); } else { b.disabled=false; alert((r&&r.error)||"Chyba přechodu."); } }).catch(function(){ b.disabled=false; alert("Chyba spojení."); }); });
        return b;
      }
      if(c.stav==="navrzen"){ btns.appendChild(actBtn("✅ Schválit","#3fbf6b",false,"schvalit")); btns.appendChild(actBtn("⛔ Zamítnout","#ef6a6a",false,"zamitnout")); }
      else if(c.stav==="aktivni"){ btns.appendChild(actBtn("⏸️ Pozastavit","#e8b13a",true,"pozastavit")); btns.appendChild(actBtn("🎯 Splnit","#3fbf6b",false,"splnit")); }
      else if(c.stav==="pozastaven"){ btns.appendChild(actBtn("▶️ Obnovit","#4f9dff",false,"obnovit")); }
      else { btns.appendChild(el('<div class="hint">Cíl je uzavřen — žádné další přechody.</div>')); }
      p.appendChild(btns);
      var lg=el('<div style="margin-top:14px;border-top:1px solid var(--bord);padding-top:10px;"></div>');
      lg.appendChild(el('<div style="color:var(--mut);font-size:12px;margin-bottom:6px;">Log akcí ('+log.length+')</div>'));
      if(!log.length) lg.appendChild(el('<div class="hint">Zatím žádné kroky.</div>'));
      log.forEach(function(l){ lg.appendChild(el('<div style="font-size:12.5px;color:var(--mut);padding:7px 0;border-bottom:1px dashed var(--bord);"><b style="color:var(--tx);">'+esc(l.actor)+'</b> · '+esc(l.akce)+' · '+esc(l.ts)+(l.detail?'<br>'+esc(l.detail):'')+(l.vysledek?'<br>→ '+esc(l.vysledek):'')+'</div>')); });
      p.appendChild(lg);
    }).catch(function(){ p.innerHTML='<div class="hint" style="color:#fc8;">Chyba spojení.</div>'; });
  }

  function cil_new(){
    app.innerHTML=topbar("＋ Nový cíl", true);
    app.appendChild(_cilBack());
    var p=el('<div class="panel"></div>');
    function fi(id,label,ph,ta){
      p.appendChild(el('<div style="color:var(--mut);font-size:12px;margin-top:10px;">'+esc(label)+'</div>'));
      p.appendChild(el(ta?('<textarea id="'+id+'" rows="3" style="width:100%;"></textarea>'):('<input id="'+id+'" style="width:100%;" placeholder="'+esc(ph)+'">')));
    }
    fi("cnNazev","Název *","Krátký název cíle",false);
    fi("cnPopis","Popis","",true);
    fi("cnRozsah","Rozsah (čeho se smí dotknout)","schémata/systémy",false);
    fi("cnStrop","Strop kroků","např. 10",false);
    var sb=el('<button class="green full" style="margin-top:14px;">Uložit návrh</button>');
    sb.addEventListener("click",function(){
      var nazev=(document.getElementById("cnNazev").value||"").trim();
      if(!nazev){ alert("Zadej název cíle."); return; }
      sb.disabled=true;
      api("POST","/api/v1/erp/app/cil",{nazev:nazev,popis:document.getElementById("cnPopis").value,rozsah:document.getElementById("cnRozsah").value,strop_kroku:document.getElementById("cnStrop").value}).then(function(r){
        if(r&&r.ok){ _cilId=r.id; go("cil_detail"); } else { sb.disabled=false; alert((r&&r.error)||"Chyba uložení."); }
      }).catch(function(){ sb.disabled=false; alert("Chyba spojení."); });
    });
    p.appendChild(sb);
    app.appendChild(p);
  }

  try{ SCREENS.cil=cil; SCREENS.cil_detail=cil_detail; SCREENS.cil_new=cil_new; }catch(e){}
