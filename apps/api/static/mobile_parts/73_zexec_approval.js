  // ── Žlutý banner — schvalování rizikových příkazů serveru (#3) ─────────────
  // Roadmapa doc-marti-ai-produkce-roadmap #3. Cowork instance B, 27.7.2026.
  // Nativní obrazovka (Bearer token / cookie přes appkovou api()) — NE iframe.
  // Rodič vidí KONKRÉTNÍ 🟡 příkaz + důvod + palec. Po ✅ se příkaz spustí přes
  // eurosoft_exec a výsledek se ukáže. Jeden banner = jeden příkaz, ~15 min expirace.
  // Registrace do SCREENS (definováno v 73_pref_poptavka.js). Data z /app/exec_approval*.
  var _eaTok=0;
  function _eaBack(){ var b=el('<div style="color:var(--blue);font-size:15px;font-weight:600;padding:8px 4px 6px;cursor:pointer;">← Zpět</div>'); b.addEventListener("click",back); return b; }
  function _eaTime(s){ s=Math.max(0,s|0); var m=Math.floor(s/60); return m>0?(m+" min "+(s%60)+" s"):(s+" s"); }

  function exec_approval(){
    var myTok=++_eaTok;
    app.innerHTML=topbar("🟡 Ke schválení", true);
    app.appendChild(_eaBack());
    var p=el('<div class="panel"></div>');
    var rb=el('<button class="full" style="margin:0 0 10px;background:var(--surf);border:1px solid var(--bord);color:var(--tx);">🔄 Obnovit</button>');
    rb.addEventListener("click",function(){ if(myTok===_eaTok) exec_approval(); });
    p.appendChild(rb);
    p.appendChild(el('<div class="hint" style="margin-bottom:8px;">Rizikové (🟡) příkazy serveru čekají na tvůj palec. Jeden banner = jeden konkrétní příkaz, po ~15 min propadne. Schválit = příkaz se hned spustí a zaudituje.</div>'));
    p.appendChild(el('<div class="list" id="eaList"><div class="hint">Načítám…</div></div>'));
    app.appendChild(p);
    api("GET","/api/v1/erp/app/exec_approval","").then(function(j){
      if(myTok!==_eaTok) return;
      var box=document.getElementById("eaList"); if(!box)return; box.innerHTML="";
      if(!j||!j.ok){ box.appendChild(el('<div class="hint" style="color:#fc8;">'+esc((j&&j.error)||"Nepodařilo se načíst žádosti.")+'</div>')); return; }
      var z=j.zadosti||[];
      if(!z.length){ box.appendChild(el('<div class="hint">Žádné čekající žádosti. 🎉</div>')); return; }
      z.forEach(function(a){ box.appendChild(_eaCard(a,myTok)); });
    }).catch(function(){ if(myTok!==_eaTok) return; var box=document.getElementById("eaList"); if(box) box.innerHTML='<div class="hint" style="color:#fc8;">Chyba spojení.</div>'; });
  }

  function _eaCard(a,myTok){
    var YEL="#e8b13a";
    var card=el('<div style="background:'+YEL+'14;border:1px solid '+YEL+'66;border-left:4px solid '+YEL+';border-radius:12px;padding:13px;margin-bottom:10px;"></div>');
    var head='<div style="display:flex;justify-content:space-between;gap:8px;align-items:center;margin-bottom:6px;">'
      +'<span style="font-size:11px;font-weight:700;padding:3px 9px;border-radius:999px;background:'+YEL+'26;color:'+YEL+';text-transform:uppercase;letter-spacing:.3px;">🟡 '+esc(a.tier||"yellow")+'</span>'
      +'<span style="color:var(--mut);font-size:12px;">vyprší za '+_eaTime(a.expires_in_s)+'</span></div>';
    head+='<div style="color:var(--mut);font-size:12px;margin-bottom:2px;">Důvod: '+esc(a.hint||"—")+'</div>';
    head+='<div style="color:var(--mut);font-size:12px;margin-bottom:6px;">Žádá: '+esc(a.requested_by||"Marti-AI")+' · #'+a.id+' · '+esc(a.created||"")+'</div>';
    head+='<div style="font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12.5px;background:#0d1117;color:#e6edf3;border:1px solid var(--bord);border-radius:8px;padding:9px 10px;white-space:pre-wrap;word-break:break-all;">'+esc(a.cmd||"")+'</div>';
    head+='<div style="color:var(--mut);font-size:11px;margin-top:3px;">shell: '+esc(a.shell||"powershell")+'</div>';
    card.innerHTML=head;
    var out=el('<div style="margin-top:8px;"></div>'); card.appendChild(out);
    var btns=el('<div style="display:flex;gap:8px;margin-top:10px;"></div>');
    var bYes=el('<button style="flex:1;margin:0;border:0;border-radius:12px;padding:13px;font-size:15px;font-weight:700;color:#fff;background:#3fbf6b;">✅ Schválit a spustit</button>');
    var bNo=el('<button style="flex:1;margin:0;border:0;border-radius:12px;padding:13px;font-size:15px;font-weight:700;color:#fff;background:#ef6a6a;">⛔ Zamítnout</button>');
    var _armed=false;
    bYes.addEventListener("click",function(){
      // Dvojklik místo native confirm() — ten je v nativní appce (webview) nespolehlivý.
      if(!_armed){ _armed=true; bYes.textContent="⚠️ Klepni znovu = spustit"; bYes.style.background="#d98a1f";
        out.innerHTML='<div class="hint" style="color:'+YEL+';">Potvrď spuštění dalším klepnutím (nebo Obnovit pro zrušení).</div>';
        setTimeout(function(){ if(_armed && myTok===_eaTok){ _armed=false; bYes.textContent="✅ Schválit a spustit"; bYes.style.background="#3fbf6b"; out.innerHTML=""; } },5000);
        return; }
      _armed=false; bYes.textContent="✅ Schválit a spustit"; bYes.style.background="#3fbf6b";
      bYes.disabled=true; bNo.disabled=true; out.innerHTML='<div class="hint">Spouštím…</div>';
      api("POST","/api/v1/erp/app/exec_approval/"+a.id+"/schvalit",{}).then(function(r){
        if(myTok!==_eaTok) return;
        if(r&&(r.status==="executed")){
          var okc=r.ok?"#3fbf6b":"#ef6a6a";
          out.innerHTML='<div style="font-size:12.5px;color:'+okc+';font-weight:700;margin-bottom:4px;">'+(r.ok?"✅ Provedeno":"⚠️ Skončilo chybou")+' (rc='+(r.rc==null?"?":r.rc)+')</div>'
            +(r.out?'<div style="font-family:ui-monospace,monospace;font-size:12px;background:#0d1117;color:#e6edf3;border-radius:8px;padding:8px;white-space:pre-wrap;word-break:break-all;max-height:220px;overflow:auto;">'+esc(r.out)+'</div>':'')
            +(r.err?'<div style="font-family:ui-monospace,monospace;font-size:12px;color:#fc8;margin-top:4px;white-space:pre-wrap;word-break:break-all;">'+esc(r.err)+'</div>':'');
        } else {
          bNo.disabled=false;
          out.innerHTML='<div class="hint" style="color:#fc8;">'+esc((r&&r.error)||"Nepodařilo se schválit.")+'</div>';
          if(r&&r.error&&/vyprš/.test(r.error)){ setTimeout(function(){ if(myTok===_eaTok) exec_approval(); },1200); }
        }
      }).catch(function(){ if(myTok!==_eaTok) return; bYes.disabled=false; bNo.disabled=false; out.innerHTML='<div class="hint" style="color:#fc8;">Chyba spojení.</div>'; });
    });
    bNo.addEventListener("click",function(){
      bYes.disabled=true; bNo.disabled=true;
      api("POST","/api/v1/erp/app/exec_approval/"+a.id+"/zamitnout",{}).then(function(r){
        if(myTok!==_eaTok) return;
        if(r&&r.ok){ card.style.opacity=".5"; out.innerHTML='<div class="hint">⛔ Zamítnuto.</div>'; }
        else { bYes.disabled=false; bNo.disabled=false; out.innerHTML='<div class="hint" style="color:#fc8;">'+esc((r&&r.error)||"Nepodařilo se zamítnout.")+'</div>'; }
      }).catch(function(){ if(myTok!==_eaTok) return; bYes.disabled=false; bNo.disabled=false; out.innerHTML='<div class="hint" style="color:#fc8;">Chyba spojení.</div>'; });
    });
    btns.appendChild(bYes); btns.appendChild(bNo); card.appendChild(btns);
    return card;
  }

  try{ SCREENS.exec_approval=exec_approval; }catch(e){}
