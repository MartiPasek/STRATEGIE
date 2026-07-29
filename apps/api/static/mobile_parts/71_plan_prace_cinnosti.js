  function plan(){
    var AP=window._planApprove||null; window._planApprove=null;   // režim schvalovatele (cizí plán)
    var WEEKONLY=(window._planInit==="thisweek");                 // jen tento týden (z dlaždice Týden)
    app.innerHTML=topbar(AP?("🗓️ "+esc(AP.name)):(WEEKONLY?("📅 Týden "+_isoWeek(new Date())):"🗓️ Plán"), true);
    var _ptb=app.querySelector('.topbar'); if(_ptb)_ptb.style.paddingTop="12px";
    function nf(v){ return (Math.round((v||0)*100)/100).toString().replace('.',','); }
    function czd(iso){ var p=(iso||"").split("-"); return p.length===3?(p[2]+"."+p[1]+"."):iso; }
    var wrap=el('<div style="display:flex;gap:10px;height:calc(100vh - 67px - var(--navh, 65px));align-items:stretch;"></div>');
    var left=el('<div style="flex:1;min-width:0;overflow-y:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none;padding-bottom:100px;"></div>');
    var right=el('<div style="width:88px;flex:none;display:flex;flex-direction:column;gap:8px;overflow-y:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none;padding-bottom:100px;"></div>');
    wrap.appendChild(left); wrap.appendChild(right); app.appendChild(wrap);
    // Marti 14.6. večer: v Týdnu navigace týdnů ↑ (předchozí) / ↓ (další) na vrchu lišty.
    if(WEEKONLY){
      var bUp=el('<button class="ghost" style="padding:12px 4px;text-align:center;border-color:#3a5a8c;color:#9cf;font-weight:700;font-size:13px;line-height:1.25;">⬆️<br>Předch.<br>týden</button>');
      bUp.addEventListener("click",function(){ try{ window._planWeekShift && window._planWeekShift(-1); }catch(e){} });
      right.appendChild(bUp);
      var bDn=el('<button class="ghost" style="padding:12px 4px;text-align:center;border-color:#3a5a8c;color:#9cf;font-weight:700;font-size:13px;line-height:1.25;">⬇️<br>Další<br>týden</button>');
      bDn.addEventListener("click",function(){ try{ window._planWeekShift && window._planWeekShift(1); }catch(e){} });
      right.appendChild(bDn);
    }
    // Marti 14.6. večer: pořadí lišty shora dolů — Můj plán, Moje podmínky,
    // Koho čekáme, Plán skupiny, [admin:] Skupiny výjimky, Firma plán, Firma výjimky, ČR 40h.
    var bMy=el('<button class="ghost" style="padding:12px 4px;text-align:center;border-color:#3a6b4c;color:#9ce0b0;font-weight:700;font-size:12px;line-height:1.25;">👤<br>Můj<br>plán</button>');
    bMy.addEventListener("click",function(){ renderPlan(false,'mydefault'); });
    var bUv=el('<button class="ghost" style="padding:12px 4px;text-align:center;border-color:#6b4a2a;color:#e6b97a;font-weight:700;font-size:12px;line-height:1.25;">📋<br>Moje<br>podmínky</button>');
    bUv.addEventListener("click",function(){ renderPodminky(); });
    var bDay=el('<button class="ghost" style="padding:12px 4px;text-align:center;border-color:#2a6b3a;color:#8fe0a0;font-weight:700;font-size:12px;line-height:1.25;">📊<br>Koho<br>čekáme</button>');
    bDay.addEventListener("click",function(){ renderDay(); });
    var bGrp=el('<button class="ghost" style="padding:12px 4px;text-align:center;border-color:#2a5a6b;color:#7fc8e0;font-weight:700;font-size:12px;line-height:1.25;">👥<br>Plán<br>skupiny</button>');
    bGrp.addEventListener("click",function(){ renderGroupPlan(); });
    var bFirma=el('<button class="ghost" style="padding:12px 4px;text-align:center;border-color:#2a6b5a;color:#7fe0c8;font-weight:700;font-size:12px;line-height:1.25;">🏭<br>Firma<br>plán</button>');
    bFirma.addEventListener("click",function(){ renderPlan(true); });
    var bScope=el('<button class="ghost" style="padding:12px 4px;text-align:center;border-color:#5a3a6b;color:#c9a6e6;font-weight:700;font-size:12px;line-height:1.25;">👥<br>Skupiny<br>výjimky</button>');
    bScope.addEventListener("click",function(){ renderExc('scope'); });
    var bExc=el('<button class="ghost" style="padding:12px 4px;text-align:center;border-color:#6b5a2a;color:#e6c86a;font-weight:700;font-size:12px;line-height:1.25;">🏢<br>Firma<br>výjimky</button>');
    bExc.addEventListener("click",function(){ renderExc('firma'); });
    var bGen=el('<button class="ghost" style="padding:12px 4px;text-align:center;border-color:#3a5a8c;color:#9cf;font-weight:700;font-size:13px;line-height:1.25;">📋<br>ČR<br>40 h</button>');
    bGen.addEventListener("click",function(){
      if(!confirm("Vygenerovat základní roční plán 40 h/týden (Po–Pá podle státních svátků)?")) return;
      bGen.disabled=true;
      api("POST","/api/v1/erp/app/plan/generate-base",{uvazek:40}).then(function(r){
        bGen.disabled=false;
        if(r&&r.ok){ renderPlan(); } else alert("Chyba: "+((r&&r.error)||"?"));
      });
    });
    // pořadí appendů = shora dolů
    right.appendChild(bMy);
    (function(){
      api("GET","/api/v1/erp/app/plan/requests?from="+_locDate(-365)+"&to="+_locDate(365),"").then(function(rq){
        var n=(((rq&&rq.items)||[]).filter(function(r){ return r&&r.status==='pending'; })).length;
        if(n>0){ bMy.style.position="relative"; bMy.appendChild(el('<span style="position:absolute;top:-5px;right:-5px;background:#f59e0b;color:#fff;font-size:10px;min-width:16px;height:16px;line-height:16px;border-radius:8px;padding:0 4px;text-align:center;font-weight:700;">'+(n>99?"99+":n)+'</span>')); }
      }).catch(function(){});
    })();
    right.appendChild(bUv);
    right.appendChild(bDay);
    right.appendChild(bGrp);
    if(!WEEKONLY){
      right.appendChild(bScope);
      right.appendChild(bFirma);
      right.appendChild(bExc);
      right.appendChild(el('<div class="hint" style="text-align:center;font-size:10px;line-height:1.3;margin-top:4px;">Vyrobit<br>základ</div>'));
      right.appendChild(bGen);
    }
    function czd2(iso){ var p=(iso||"").split("-"); return p.length===3?(p[2]+"."+p[1]+"."+p[0]):iso; }
    function renderPlan(eff, src){
      left.innerHTML='<div class="hint">Načítám…</div>';
      var _url= eff ? "/api/v1/erp/app/plan/firma"
              : (src==='mydefault') ? ("/api/v1/erp/app/plan/my-default"+(AP?("?user_id="+AP.user_id):""))
              : "/api/v1/erp/app/plan/mine?weeks=10";
      api("GET",_url,"").then(function(j){
        left.innerHTML="";
        if(!j||!j.ok){ left.appendChild(el('<div class="hint">Nelze načíst.</div>')); return; }
        if(!j.has_plan){ left.appendChild(el('<div class="hint" style="line-height:1.7;">Zatím nemáš žádný plán.<br>Vpravo klikni <b>📋 40 h</b> a vyrobí se ti základní roční plán podle státních svátků (Po–Pá, víkendy a svátky volno).</div>')); return; }
        if(src==='mydefault'){ renderWeeks(left, j, src); }
        else { renderMonths(left, j, eff, src, null); }
      });
    }
    // Marti 14.6.: Můj plán = TÝDENNÍ pohled — týdny aktivně oddělené, baseline plánu.
    // (Základ pro budoucí „Můj plán ke schválení" — kalendářní vkládání návrhů.)
    function renderWeeks(box, j, src){
      var fromD=(j.plan[0]&&j.plan[0].date)||_locDate(0);
      var toD=(j.plan[j.plan.length-1]&&j.plan[j.plan.length-1].date)||_locDate(0);
      var todayIso=_locDate(0);
      var iS="box-sizing:border-box;width:100%;padding:9px;border-radius:9px;border:1px solid #2b3a5c;background:#0a1226;color:#e8eefc;margin:2px 0;font-size:14px;";
      var ST={view:'list', wk:null, byDate:{}, weeks:{}, order:[], nowKey:null, weekKey:null, pend:0, listScroll:0};
      function stCol(s){ return s==='approved'?'#34d399':(s==='rejected'?'#f87171':'#fbbf24'); }
      function stIc(s){ return s==='approved'?'✓':(s==='rejected'?'✕':'⏳'); }
      function kLabel(r){
        if(r.kind==='off') return '🏝️ volno';
        if(r.kind==='meeting') return '🤝 '+(r.title||'porada/jednání')+(r.start?(' '+r.start+(r.end?('–'+r.end):'')):'');
        if(r.kind==='event') return '📌 '+(r.title||'akce')+(r.start?(' '+r.start):'');
        // hodiny: stejný formát jako plán — „od 10:00 · 8 h" (vlevo zůstane jen status ⏳)
        return (r.start?('od '+r.start+' · '):'')+(r.hours!=null?_hhmm(r.hours):'jiné hodiny');
      }
      function wkPend(ds){ var n=0; ds.forEach(function(d){ (ST.byDate[d.date]||[]).forEach(function(r){ if(r.status==='pending')n++; }); }); return n; }
      // Bod 3: root = jen seznam týdnů (klik = celý týden). Editace dnů až v týdnu.
      function showList(doScroll){
        ST.view='list'; ST.wk=null; box.innerHTML="";
        if(right)right.style.display=AP?'none':'flex';  // schvalovatel: bez admin lišty (flex, ne '' — jinak ztratí sloupec)
        var gt=0; j.plan.forEach(function(d){ gt+=d.hours; });
        var yr=(j.plan[0]&&j.plan[0].date||"").slice(0,4);
        box.appendChild(el('<div style="margin-bottom:4px;"><b>👤 '+(AP?esc(AP.name):'Můj plán')+' '+yr+'</b> <span class="hint">· úvazek '+(j.uvazek||"?")+' h/týd. · '+nf(gt)+' h</span></div>'));
        box.appendChild(el('<div class="hint" style="margin-bottom:10px;line-height:1.5;">'+(AP?'Klepni na týden — uvidíš návrhy a můžeš je schválit/zamítnout.':'Klepni na týden — otevře se celý. Tam přidáš návrhy ke schválení.')+(ST.pend?(' <b style="color:var(--amber);">· '+ST.pend+' čeká</b>'):'')+'</div>'));
        var curCard=null, todayEl=null, cardByKey={}, firstPendCard=null;
        var _keys = WEEKONLY ? (ST.weekKey ? [ST.weekKey] : ST.order.slice(0,1)) : ST.order;
        _keys.forEach(function(k){
          var ds=ST.weeks[k], sum=0, wd=0; ds.forEach(function(d){ sum+=d.hours; if(d.hours>0)wd++; });
          var lastD=ds[ds.length-1].date, isPast=(lastD<todayIso), isCur=(k===ST.nowKey);
          var pc=wkPend(ds);
          var card=el('<div style="border:1px solid '+(isCur?'#4f8ef7':'#2b3a5c')+';border-radius:12px;margin-bottom:10px;overflow:hidden;cursor:pointer;'+(isPast?'opacity:.5;':'')+'"></div>');
          var _hl,_hr;
          if(WEEKONLY){ _hl='Plán · '+ds[0].iso_week+'. týden'; _hr='<b style="font-size:16px;color:#cfe0ff;">'+_hhmm(sum)+'</b>'; }
          else { _hl='Týden '+ds[0].iso_week+(isCur?' · tento týden':''); _hr='<span class="hint">'+wd+' dní · '+_hhmm(sum)+'</span>'; }
          card.appendChild(el('<div style="padding:11px 12px;background:'+(isCur?'#11203a':(isPast?'#0c1018':'#0e1830'))+';display:flex;justify-content:space-between;align-items:center;'+(isCur?'border-left:3px solid #4f8ef7;':'')+'"><span style="font-weight:700;">'+_hl+'</span><span style="display:flex;align-items:center;gap:8px;">'+_hr+(pc?('<span style="color:var(--amber);font-size:12px;font-weight:700;">'+pc+'⏳</span>'):'')+'<span style="color:var(--mut);">›</span></span></div>'));
          var body=el('<div style="padding:4px 10px 8px;"></div>');
          ds.forEach(function(d){
            var dwork=(d.hours>0);
            var dcol=dwork?"#34d399":(d.day_type==="holiday"?"#fbbf24":(d.day_type==="exoff"?"#e6a93a":"#5b6b88"));
            var dToday=(d.date===todayIso); var dPast=(d.date<todayIso);
            var dReqs=ST.byDate[d.date]||[];
            // korekce typu hodiny/volno NAHRAZUJE plán → přeškrtnout původní hodnotu
            var hasRepl=dReqs.some(function(r){ return (r.kind==='hours'||r.kind==='off') && r.status!=='rejected'; });
            var rs="display:flex;justify-content:space-between;align-items:center;padding:5px 4px;font-size:13px;border-bottom:1px solid rgba(255,255,255,.05);"+(dToday?"background:rgba(79,142,247,.14);border-radius:6px;":"")+(dPast?"opacity:.45;":"");
            var rightCell;
            if(dwork){
              var _strk=hasRepl?'text-decoration:line-through;opacity:.55;':'';
              rightCell='<span style="display:inline-flex;align-items:baseline;gap:10px;'+_strk+'"><span style="color:#8fb4e8;font-size:12px;min-width:56px;text-align:right;">'+(d.start?'od '+d.start:'')+'</span><span style="color:#34d399;font-weight:700;min-width:46px;text-align:right;">'+_hhmm(d.hours)+'</span></span>';
            } else {
              var _lbl2=(d.day_type==="holiday")?"svátek":((d.day_type==="weekend")?"víkend":((d.day_type==="exoff")?((d.exc_scope==='osobní'?'👤 osobní':(d.exc_scope==='skupina'?'👥 skupinové':'🏢 celofiremní'))+' volno'):"volno"));
              rightCell='<span style="color:'+dcol+';font-weight:600;'+(hasRepl?'text-decoration:line-through;opacity:.55;':'')+'">'+_lbl2+'</span>';
            }
            var row=el('<div style="'+rs+'"><span'+(dToday?' style="font-weight:700;"':'')+'>'+(dToday?'▶ ':'')+d.weekday+' '+czd(d.date)+'</span>'+rightCell+'</div>');
            body.appendChild(row);
            if(dToday) todayEl=row;
            dReqs.forEach(function(r){
              // korekce vpravo zarovnaná, pod původní hodnotou
              body.appendChild(el('<div style="text-align:right;margin:1px 4px 5px;font-size:12px;color:'+stCol(r.status)+';">'+stIc(r.status)+' '+esc(kLabel(r))+'</div>'));
            });
          });
          card.appendChild(body);
          card.addEventListener("click",function(){ showWeek(k); });
          box.appendChild(card);
          cardByKey[k]=card;
          if(isCur) curCard=card;
          if(pc>0 && !firstPendCard) firstPendCard=card;   // první týden s čekajícím návrhem
        });
        // Nascrolovat na DNEŠEK jen při PRVNÍM otevření (ne při návratu z týdne).
        // Schvalovatel: nascrolluj na první týden, kde něco čeká na schválení.
        var target=(AP&&firstPendCard)?firstPendCard:(todayEl||curCard);
        if(doScroll && target){ setTimeout(function(){ try{ target.scrollIntoView({behavior:"smooth",block:"center"}); }catch(e){} },40); }
        else if(ST.openWk && cardByKey[ST.openWk]){ setTimeout(function(){ try{ cardByKey[ST.openWk].scrollIntoView({block:"start"}); }catch(e){} },30); }
        if(WEEKONLY){ _realityCard(box, ST.weeks[ST.weekKey]||ST.weeks[ST.nowKey]||[]); }
      }
      function _hhmm(h){ h=Math.max(0, Math.round((h||0)*60)); return Math.floor(h/60)+":"+("0"+(h%60)).slice(-2); }
      function _realityCard(box, days){
        if(!days.length) return;
        var fromD2=days[0].date, toD2=days[days.length-1].date;
        var card=el('<div style="border:1px solid #2b3a5c;border-radius:12px;margin-bottom:10px;overflow:hidden;"></div>');
        card.appendChild(el('<div style="padding:11px 12px;background:#0e1830;display:flex;justify-content:space-between;align-items:center;"><span style="font-weight:700;">Realita</span><b id="realSum" style="font-size:16px;color:#cfe0ff;">…</b></div>'));
        var body=el('<div style="padding:4px 10px 8px;"></div>');
        body.appendChild(el('<div class="hint" style="padding:6px 2px;">Načítám…</div>'));
        card.appendChild(body); box.appendChild(card);
        api("GET","/api/v1/erp/app/attendance/real?from="+fromD2+"&to="+toD2,"").then(function(j){
          body.innerHTML="";
          var by={}; ((j&&j.days)||[]).forEach(function(r){ by[r.d]=r; });
          var tot=0;
          days.forEach(function(d){
            var rr=by[d.date]; var w=(rr&&rr.worked)?parseFloat(rr.worked):0; tot+=w;
            var dToday=(d.date===todayIso), dPast=(d.date<todayIso);
            var rs="display:flex;justify-content:space-between;align-items:center;padding:5px 4px;font-size:13px;border-bottom:1px solid rgba(255,255,255,.05);"+(dToday?"background:rgba(79,142,247,.14);border-radius:6px;":"")+((dPast&&!w)?"opacity:.45;":"");
            var rightCell;
            if(w>0){
              rightCell='<span style="display:inline-flex;align-items:baseline;gap:10px;"><span style="color:#8fb4e8;font-size:12px;min-width:56px;text-align:right;">'+(rr&&rr.zac?'od '+rr.zac:'')+'</span><span style="color:#34d399;font-weight:700;min-width:46px;text-align:right;">'+_hhmm(w)+'</span></span>';
            } else { rightCell='<span style="color:#5b6b88;font-weight:600;">—</span>'; }
            body.appendChild(el('<div style="'+rs+'"><span'+(dToday?' style="font-weight:700;"':'')+'>'+(dToday?'▶ ':'')+d.weekday+' '+czd(d.date)+'</span>'+rightCell+'</div>'));
          });
          var sm=document.getElementById("realSum"); if(sm)sm.textContent=_hhmm(tot);
        }).catch(function(){ body.innerHTML='<div class="hint" style="padding:6px 2px;">Nepodařilo se načíst realitu.</div>'; });
      }
      function openForm(d, host){
        var ex=host.querySelector('.reqform'); if(ex){ ex.remove(); return; }
        var f=el('<div class="reqform" style="margin:2px 0 8px 12px;padding:9px;border:1px solid #3a4d6b;border-radius:10px;background:rgba(79,142,247,.06);"></div>');
        f.appendChild(el('<div class="hint" style="margin-bottom:7px;">Návrh na <b>'+d.weekday+' '+czd(d.date)+'</b>:</div>'));
        var cur={kind:'hours'};
        var kindRow=el('<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px;"></div>');
        var fields=el('<div></div>'); var elH,elS,elE,elT,elN;
        function buildFields(){
          fields.innerHTML="";
          if(cur.kind==='hours'){
            fields.appendChild(el('<label class="hint">Kolik hodin</label>'));
            elH=el('<input type="number" min="0" max="24" step="0.5" value="'+(d.hours||8)+'" style="'+iS+'">'); fields.appendChild(elH);
            fields.appendChild(el('<label class="hint">Příchod od (volitelně)</label>'));
            elS=el('<input type="time" value="'+(d.start||"")+'" style="'+iS+'">'); fields.appendChild(elS);
          } else if(cur.kind==='off'){
            fields.appendChild(el('<div class="hint" style="padding:4px 0;">Navrhuješ na tento den volno.</div>'));
          } else if(cur.kind==='meeting'){
            fields.appendChild(el('<label class="hint">Název (porada / jednání)</label>'));
            elT=el('<input placeholder="např. Porada výroby" style="'+iS+'">'); fields.appendChild(elT);
            fields.appendChild(el('<label class="hint">Od – do</label>'));
            var tr=el('<div style="display:flex;gap:6px;"></div>');
            elS=el('<input type="time" style="'+iS+'flex:1;">'); elE=el('<input type="time" style="'+iS+'flex:1;">');
            tr.appendChild(elS); tr.appendChild(elE); fields.appendChild(tr);
          }
          elN=el('<input placeholder="Poznámka (volitelně)" style="'+iS+'">'); fields.appendChild(elN);
        }
        function mkChip(lbl,kk){ var b=el('<button class="ghost" style="padding:6px 10px;font-size:12px;">'+lbl+'</button>');
          b.addEventListener("click",function(){ f.dataset.dirty='1'; cur.kind=kk; [].forEach.call(kindRow.children,function(c){c.style.borderColor='';c.style.color='';}); b.style.borderColor='var(--blue)'; b.style.color='var(--blue)'; buildFields(); }); return b; }
        kindRow.appendChild(mkChip('⏱ Jiné hodiny','hours'));
        kindRow.appendChild(mkChip('🏝️ Volno','off'));
        kindRow.appendChild(mkChip('🤝 Porada/jednání','meeting'));
        f.appendChild(kindRow);
        kindRow.children[0].style.borderColor='var(--blue)'; kindRow.children[0].style.color='var(--blue)'; buildFields();
        f.appendChild(fields);
        var sb=el('<button class="green full" style="margin-top:8px;">Odeslat ke schválení →</button>');
        sb.addEventListener("click",function(){ sb.disabled=true;
          var pl={date:d.date, kind:cur.kind, note:(elN&&elN.value)||""};
          if(cur.kind==='hours'){ pl.hours=(elH&&elH.value)||""; pl.start=(elS&&elS.value)||""; }
          else if(cur.kind==='meeting'){ pl.title=(elT&&elT.value)||"Porada/jednání"; pl.start=(elS&&elS.value)||""; pl.end=(elE&&elE.value)||""; }
          api("POST","/api/v1/erp/app/plan/request",pl).then(function(r){ if(r&&r.ok){ load(); } else { sb.disabled=false; alert("Chyba: "+((r&&r.error)||"?")); } });
        });
        f.appendChild(sb);
        f.addEventListener('input',function(){ f.dataset.dirty='1'; });
        host.appendChild(f);
        try{ f.scrollIntoView({behavior:"smooth",block:"center"}); }catch(e){}
      }
      function showWeek(k){
        ST.openWk=k;   // zapamatuj otevřený týden → po návratu na něj odscrolujeme
        ST.view='week'; ST.wk=k; var ds=ST.weeks[k]; if(!ds){ showList(); return; }
        box.innerHTML="";
        if(right)right.style.display='none';  // #2: detail týdne na celou šířku
        var bk=el('<button id="planWeekBack" class="ghost full" style="margin-bottom:10px;">'+(WEEKONLY?'‹ Zpět':'‹ Zpět na týdny')+'</button>'); bk.addEventListener("click",function(){ planBackStep(); }); box.appendChild(bk);
        var sum=0,wd=0; ds.forEach(function(d){ sum+=d.hours; if(d.hours>0)wd++; });
        box.appendChild(el('<div style="margin-bottom:8px;"><b>Týden '+ds[0].iso_week+'</b> <span class="hint">· '+wd+' dní · '+_hhmm(sum)+' · '+czd(ds[0].date)+'–'+czd(ds[ds.length-1].date)+'</span></div>'));
        box.appendChild(el('<div class="hint" style="margin-bottom:8px;">'+(AP?'Návrhy dne schválíš ✓ nebo zamítneš ✕ u příslušného řádku.':'Klepni na den a přidej návrh (jiné hodiny / volno / porada–jednání).')+'</div>'));
        ds.forEach(function(d){
          var work=(d.hours>0);
          var col=work?"#34d399":(d.day_type==="holiday"?"#fbbf24":"#5b6b88");
          var tag=work?((d.start?('od '+d.start+' · '):'')+_hhmm(d.hours)):(d.day_type==="holiday"?"svátek":(d.day_type==="weekend"?"víkend":"volno"));
          var dPast=(d.date<todayIso), dToday=(d.date===todayIso);
          var dReqs=ST.byDate[d.date]||[];
          var hasRepl=dReqs.some(function(r){ return (r.kind==='hours'||r.kind==='off') && r.status!=='rejected'; });
          var dayWrap=el('<div></div>');
          var rs="display:flex;justify-content:space-between;align-items:center;padding:9px 6px;font-size:14px;border-bottom:1px solid rgba(255,255,255,.06);cursor:pointer;"+(dToday?"background:rgba(79,142,247,.14);border-radius:8px;":"")+(dPast?"opacity:.5;":"");
          var tagSt="color:"+col+";font-weight:600;"+(hasRepl?"text-decoration:line-through;opacity:.55;":"");
          var plusHtml=AP?'':'<span style="display:inline-flex;align-items:center;justify-content:center;width:24px;height:24px;border-radius:50%;background:rgba(79,142,247,.18);color:#4f8ef7;font-size:17px;font-weight:700;line-height:1;flex:none;">+</span>';
          var row=el('<div style="'+rs+(AP?'cursor:default;':'')+'"><span'+(dToday?' style="font-weight:700;"':'')+'>'+(dToday?'▶ ':'')+d.weekday+' '+czd(d.date)+'</span><span style="display:flex;align-items:center;gap:8px;"><span style="'+tagSt+'">'+tag+'</span>'+plusHtml+'</span></div>');
          if(!AP){ row.addEventListener("click",function(){ openForm(d, dayWrap); }); }
          dayWrap.appendChild(row);
          (ST.byDate[d.date]||[]).forEach(function(r){
            var chip=el('<div style="display:flex;justify-content:space-between;align-items:center;gap:6px;margin:3px 6px 6px 14px;font-size:12.5px;"><span style="color:'+stCol(r.status)+';">'+stIc(r.status)+' '+esc(kLabel(r))+(r.note?(' — '+esc(r.note)):'')+(r.status==='rejected'&&r.decided_note?(' ('+esc(r.decided_note)+')'):'')+'</span></div>');
            if(AP){
              if(r.status==='pending'){
                var bw=el('<div style="display:flex;gap:6px;flex:none;"></div>');
                var ya=el('<button style="display:inline-flex;align-items:center;justify-content:center;width:26px;height:26px;border-radius:50%;background:rgba(52,211,153,.18);color:#34d399;border:0;font-size:14px;line-height:1;cursor:pointer;" title="Schválit">✓</button>');
                var na=el('<button style="display:inline-flex;align-items:center;justify-content:center;width:26px;height:26px;border-radius:50%;background:rgba(248,113,113,.16);color:#f87171;border:0;font-size:13px;line-height:1;cursor:pointer;" title="Zamítnout">✕</button>');
                ya.addEventListener("click",function(e){ e.stopPropagation(); ya.disabled=true; na.disabled=true; apDecideCal(r.id,"approved",null); });
                na.addEventListener("click",function(e){ e.stopPropagation(); apRejectDialog(r, function(note){ apDecideCal(r.id,"rejected",note); }); });
                bw.appendChild(ya); bw.appendChild(na); chip.appendChild(bw);
              }
            } else if(r.status==='pending'){
              var db=el('<button style="display:inline-flex;align-items:center;justify-content:center;width:24px;height:24px;border-radius:50%;background:rgba(248,113,113,.16);color:#f87171;border:0;font-size:13px;line-height:1;cursor:pointer;flex:none;" title="Smazat">✕</button>'); db.addEventListener("click",function(e){ e.stopPropagation(); if(!confirm("Chceš tento záznam opravdu smazat?")) return; db.disabled=true; api("POST","/api/v1/erp/app/plan/request/"+r.id+"/delete","").then(function(){ load(); }); }); chip.appendChild(db);
            }
            dayWrap.appendChild(chip);
          });
          box.appendChild(dayWrap);
        });
      }
      function apDecideCal(id, decision, note){
        api("POST","/api/v1/erp/app/plan/decide",{id:id,decision:decision,note:note||""}).then(function(x){
          if(x&&x.ok){ load(); } else alert("Chyba: "+((x&&x.error)||"?")); });
      }
      function load(){
        box.innerHTML='<div class="hint">Načítám…</div>';
        var _ru=AP?("/api/v1/erp/app/plan/approvals/user/"+AP.user_id+"?all=1"):("/api/v1/erp/app/plan/requests?from="+fromD+"&to="+toD);
        api("GET",_ru,"").then(function(rq){
          var reqs=(rq&&rq.ok&&rq.items)||[];
          ST.byDate={}; reqs.forEach(function(r){ (ST.byDate[r.d]=ST.byDate[r.d]||[]).push(r); });
          ST.pend=reqs.filter(function(r){return r.status==='pending';}).length;
          ST.weeks={}; ST.order=[]; ST.nowKey=null;
          j.plan.forEach(function(d){ var k=d.date.slice(0,4)+"-W"+("0"+d.iso_week).slice(-2); if(!ST.weeks[k]){ST.weeks[k]=[];ST.order.push(k);} ST.weeks[k].push(d); });
          ST.order.forEach(function(k){ if(ST.weeks[k].some(function(d){return d.date===todayIso;})) ST.nowKey=k; });
          if(WEEKONLY){
            // plnou sadu týdnů NECHÁVÁME (kvůli navigaci ↑/↓), zobrazíme jen weekKey
            if(!ST.weekKey || ST.order.indexOf(ST.weekKey)<0) ST.weekKey = ST.nowKey || ST.order[0];
            showList(true);
          }
          else if(ST.view==='week' && ST.weeks[ST.wk]) showWeek(ST.wk); else showList(true);
        });
      }
      // Bod 4: Zpět o jeden krok — z týdne zpět na seznam (ne rovnou pryč).
      function planBackStep(){
        // #1: rozdělaný návrh? Zpět nejdřív zavře formulář — když je změněný, zeptá se na uložení.
        var f=box.querySelector('.reqform');
        if(f){
          if(f.dataset.dirty==='1'){ planAskSave(f); return true; }
          f.remove(); return true;
        }
        if(document.getElementById('planWeekBack')){ showList(false); return true; }
        return false;
      }
      function planAskSave(f){
        var ov=el('<div class="appmodal" style="position:fixed;inset:0;z-index:99999;background:rgba(3,7,16,.66);display:flex;align-items:center;justify-content:center;padding:24px;"></div>');
        var card=el('<div style="background:#161c2b;border:1px solid rgba(255,255,255,.12);border-radius:16px;padding:22px 20px;max-width:320px;width:100%;box-shadow:0 16px 50px rgba(0,0,0,.55);"></div>');
        card.appendChild(el('<div style="font-size:16px;font-weight:600;color:#e8eefc;text-align:center;margin-bottom:18px;">Mám uložit změny?</div>'));
        var rowb=el('<div style="display:flex;gap:10px;"></div>');
        var yes=el('<button class="green" style="flex:1;margin:0;">Ano</button>');
        var no=el('<button class="ghost" style="flex:1;margin:0;">Ne</button>');
        yes.addEventListener("click",function(){ ov.remove(); var sb=f.querySelector('.green.full'); if(sb){ sb.click(); } });
        no.addEventListener("click",function(){ ov.remove(); f.remove(); });
        rowb.appendChild(yes); rowb.appendChild(no); card.appendChild(rowb);
        ov.appendChild(card); document.body.appendChild(ov);
      }
      window._planAnyOpen=planBackStep;
      // Marti 14.6. večer: navigace týdnů v Týdnu (↑/↓ z pravé lišty). -1 = předchozí, +1 = další.
      window._planWeekShift=function(delta){
        if(!ST.order.length) return;
        var i=ST.order.indexOf(ST.weekKey); if(i<0)i=0;
        var ni=Math.min(ST.order.length-1, Math.max(0, i+delta));
        if(ni===i) return;
        ST.weekKey=ST.order[ni];
        showList(false);
        try{ left.scrollTop=0; }catch(e){}
      };
      load();
    }
    function renderMonths(box, j, eff, src, titleOverride){
      var yr=(j.plan[0]&&j.plan[0].date||"").slice(0,4);
      var effH=function(d){ return (eff&&d.exc_hours!==null&&d.exc_hours!==undefined)?d.exc_hours:d.hours; };
      var effT=function(d){ return (eff&&d.exc_hours!==null&&d.exc_hours!==undefined)?(d.exc_hours>0?'exception':'exoff'):d.day_type; };
      var gt=0; j.plan.forEach(function(d){ gt+=effH(d); });
      var _ttl=titleOverride||(eff?('🏭 Firma plán '+yr):(src==='mydefault'?('👤 Můj výchozí plán '+yr):('ČR plán '+yr)));
      var _sub=eff?'po výjimkách':('úvazek '+(j.uvazek||"?")+' h/týd.');
      box.appendChild(el('<div style="margin-bottom:8px;"><b>'+_ttl+'</b> <span class="hint">· '+_sub+' · '+nf(gt)+' h</span></div>'));
      var MN=["Leden","Únor","Březen","Duben","Květen","Červen","Červenec","Srpen","Září","Říjen","Listopad","Prosinec"];
      var nowM=(new Date()).getFullYear()+"-"+("0"+((new Date()).getMonth()+1)).slice(-2);
      var _todayIso=_locDate(0);  // Marti 14.6.: odlišit minulost / současnost / budoucnost
      var months={}, order=[];
      j.plan.forEach(function(d){ var m=d.date.slice(0,7); if(!months[m]){ months[m]=[]; order.push(m);} months[m].push(d); });
      var entries=[];
      function closeAll(){ entries.forEach(function(e){ e.body.style.display="none"; e.arr.innerHTML=e.summary+' ▸'; }); }
      order.forEach(function(m){
        var days=months[m], sum=0, wd=0, hol=0;
        days.forEach(function(d){ var h=effH(d), tp=effT(d); sum+=h; if(tp==="work"||tp==="exception") wd++; else if(tp==="holiday") hol++; });
        function svL(n){ return n+' '+(n===1?'svátek':(n>=2&&n<=4?'svátky':'svátků')); }
        var summary=wd+' prac. dní · '+nf(sum)+' h';
        var mi=parseInt(m.slice(5,7),10)-1;
        var _isPastM=(m<nowM), _isCurM=(m===nowM);
        var card=el('<div style="border:1px solid '+(_isCurM?'#4f8ef7':'#2b3a5c')+';border-radius:12px;margin-bottom:8px;overflow:hidden;'+(_isPastM?'opacity:.5;':'')+'"></div>');
        var head=el('<div style="padding:10px 12px;cursor:pointer;background:'+(_isCurM?'#11203a':(_isPastM?'#0c1018':'#0e1830'))+';scroll-margin-top:38px;'+(_isCurM?'border-left:3px solid #4f8ef7;':'')+'"></div>');
        var top=el('<div style="display:flex;justify-content:space-between;align-items:center;"></div>');
        top.appendChild(el('<span style="font-weight:700;">'+MN[mi]+'</span>'));
        var arr=el('<span class="hint" style="font-size:12px;">'+summary+' ▸</span>');
        top.appendChild(arr); head.appendChild(top);
        head.appendChild(el('<div class="hint" style="font-size:11px;margin-top:2px;opacity:.75;">'+(hol>0?svL(hol):'bez svátků')+'</div>'));
        var body=el('<div style="padding:4px 12px 8px;display:none;"></div>');
        var lastW=null;
        days.forEach(function(d){
          if(d.iso_week!==lastW){ lastW=d.iso_week; body.appendChild(el('<div class="hint" style="font-size:10px;margin:6px 0 1px;opacity:.65;">Týden '+d.iso_week+'</div>')); }
          var h=effH(d), tp=effT(d);
          var col=(tp==="work")?"#34d399":(tp==="holiday"?"#fbbf24":(tp==="exception"?"#e6a93a":(tp==="exoff"?"#e6a93a":"#5b6b88")));
          var tag;
          if(tp==="exception"){ var ic=(d.exc_scope==='osobní'?'👤':(d.exc_scope==='skupina'?'👥':'🏢')); tag=ic+' '+nf(h)+' h'; }
          else if(tp==="exoff"){ var ic2=(d.exc_scope==='osobní'?'👤 osobní':(d.exc_scope==='skupina'?'👥 skupinové':'🏢 celofiremní')); tag=ic2+' volno'; }
          else if(tp==="work"){ tag=(d.start?('od '+d.start+' · '):'')+nf(h)+" h"; }
          else if(tp==="holiday"){ tag="svátek"; }
          else { tag=(d.day_type==="weekend"?"víkend":"volno"); }
          var _dPast=(d.date<_todayIso), _dToday=(d.date===_todayIso);
          var _rs="display:flex;justify-content:space-between;padding:3px 0;font-size:13px;"+(_dToday?"background:rgba(79,142,247,.14);border-radius:6px;padding:4px 6px;margin:2px -6px;":"")+(_dPast?"opacity:.4;":"");
          body.appendChild(el('<div style="'+_rs+'"><span'+(_dToday?' style="font-weight:700;"':'')+'>'+(_dToday?'▶ ':'')+d.weekday+' '+czd(d.date)+'</span><span style="color:'+col+';font-weight:600;">'+tag+'</span></div>'));
        });
        var entry={body:body, arr:arr, summary:summary, m:m};
        head.addEventListener("click",function(){ var willOpen=(body.style.display==="none"); closeAll(); if(willOpen){ body.style.display="block"; arr.innerHTML=summary+' ▾'; setTimeout(function(){ try{ head.scrollIntoView({behavior:'smooth',block:'start'}); }catch(e){} },10); } });
        entries.push(entry);
        card.appendChild(head); card.appendChild(body); box.appendChild(card);
      });
      var cur=entries.filter(function(e){return e.m===nowM;})[0]||entries[0];
      if(cur){ cur.body.style.display="block"; cur.arr.innerHTML=cur.summary+' ▾'; }
    }
    function renderGroupPlan(){
      left.innerHTML='<div class="hint">Načítám skupiny…</div>';
      api("GET","/api/v1/erp/app/plan/exception-targets","").then(function(t){
        left.innerHTML='';
        var groups=(t&&t.ok&&t.groups)||[];
        if(!groups.length){ left.appendChild(el('<div class="hint">Nelze načíst skupiny (jen rodiče/HR).</div>')); return; }
        var bar=el('<div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;"></div>');
        bar.appendChild(el('<span class="hint" style="flex:none;">👥 Skupina:</span>'));
        var sel=el('<select style="flex:1;box-sizing:border-box;padding:9px;border-radius:9px;border:1px solid #2b3a5c;background:#0a1226;color:#e8eefc;font-weight:700;">'+groups.map(function(g){return '<option value="'+g.id+'">'+esc(g.name)+'</option>';}).join('')+'</select>');
        bar.appendChild(sel); left.appendChild(bar);
        var box=el('<div></div>'); left.appendChild(box);
        function load(){
          var gid=sel.value;
          box.innerHTML='<div class="hint">Načítám…</div>';
          api("GET","/api/v1/erp/app/plan/group?group_id="+encodeURIComponent(gid),"").then(function(j){
            box.innerHTML='';
            if(!j||!j.ok){ box.appendChild(el('<div class="hint">'+esc((j&&j.error)||"Nelze načíst")+'</div>')); return; }
            var yr=(j.plan[0]&&j.plan[0].date||"").slice(0,4);
            renderMonths(box, j, true, 'group', '👥 '+(j.group_name||'')+' '+yr);
          });
        }
        sel.addEventListener("change",load); load();
      });
    }
    function renderDay(){
      left.innerHTML='';
      var t=new Date(); var st={d:t.getFullYear()+"-"+("0"+(t.getMonth()+1)).slice(-2)+"-"+("0"+t.getDate()).slice(-2)};
      var bar=el('<div style="display:flex;align-items:center;gap:6px;margin-bottom:8px;"></div>');
      var prev=el('<button class="ghost" style="padding:6px 10px;flex:none;">◀</button>');
      var din=el('<input type="date" value="'+st.d+'" style="flex:1;box-sizing:border-box;padding:8px;border-radius:9px;border:1px solid #2b3a5c;background:#0a1226;color:#e8eefc;">');
      var next=el('<button class="ghost" style="padding:6px 10px;flex:none;">▶</button>');
      bar.appendChild(prev); bar.appendChild(din); bar.appendChild(next); left.appendChild(bar);
      var regen=el('<button class="ghost full" style="margin-bottom:8px;border-color:#2a6b5a;color:#7fe0c8;">↻ Přegenerovat plán (dnes → +120 dní)</button>');
      regen.addEventListener("click",function(){ if(!confirm("Vygenerovat složený plán pro všechny na 120 dní dopředu?")) return; regen.disabled=true; var ot=regen.textContent; regen.textContent="Generuji…"; api("POST","/api/v1/erp/app/plan/generate-effective",{}).then(function(r){ regen.disabled=false; regen.textContent=ot; if(r&&r.ok){ alert("Hotovo: "+r.rows+" řádků, "+r.people+" lidí, do "+(r.do||"?")); load(); } else alert("Chyba: "+((r&&r.error)||"?")); }); });
      left.appendChild(regen);
      var box=el('<div></div>'); left.appendChild(box);
      function czdW(iso){ var p=(iso||"").split("-"); if(p.length!==3) return iso; var dd=new Date(iso); var wn=["Ne","Po","Út","St","Čt","Pá","So"][dd.getDay()]; return wn+" "+p[2]+"."+p[1]+"."; }
      function shift(n){ var dd=new Date(st.d); dd.setDate(dd.getDate()+n); st.d=dd.getFullYear()+"-"+("0"+(dd.getMonth()+1)).slice(-2)+"-"+("0"+dd.getDate()).slice(-2); din.value=st.d; load(); }
      prev.addEventListener("click",function(){ shift(-1); });
      next.addEventListener("click",function(){ shift(1); });
      din.addEventListener("change",function(){ st.d=din.value; load(); });
      function load(){
        box.innerHTML='<div class="hint">Načítám…</div>';
        api("GET","/api/v1/erp/app/plan/day?date="+encodeURIComponent(st.d),"").then(function(j){
          box.innerHTML='';
          if(!j||!j.ok){ box.appendChild(el('<div class="hint">'+esc((j&&j.error)||"Nelze načíst")+'</div>')); return; }
          box.appendChild(el('<div style="margin-bottom:8px;"><b>'+czdW(st.d)+'</b> <span class="hint">· čekáme '+j.total_people+' lidí · '+nf(j.total_hours)+' h</span></div>'));
          if(!j.generated){ box.appendChild(el('<div class="hint" style="line-height:1.6;">Pro tento den není plán vygenerovaný.<br>Klikni nahoře <b>↻ Přegenerovat plán</b>.</div>')); return; }
          j.groups.forEach(function(g){
            var card=el('<div style="border:1px solid #2b3a5c;border-radius:12px;margin-bottom:8px;overflow:hidden;"></div>');
            card.appendChild(el('<div style="display:flex;justify-content:space-between;padding:8px 12px;background:#0e1830;font-weight:700;"><span>'+esc(g.group_name)+'</span><span class="hint">'+g.count+' lidí · '+nf(g.sum_hours)+' h</span></div>'));
            var body=el('<div style="padding:4px 12px 8px;"></div>');
            g.people.forEach(function(p){
              var work=(p.hours>0);
              var col=work?"#34d399":"#5b6b88";
              var sic=p.scope_src==='osobni'?' 👤':(p.scope_src==='skupina'?' 👥':(p.scope_src==='firma'?' 🏢':''));
              var rt=work?((p.start?(p.start+' · '):'')+nf(p.hours)+' h'+sic):(p.day_type==='holiday'?'svátek':(p.day_type==='weekend'?'víkend':'volno'));
              body.appendChild(el('<div style="display:flex;justify-content:space-between;padding:3px 0;font-size:13px;"><span>'+esc(p.name)+'</span><span style="color:'+col+';font-weight:600;">'+rt+'</span></div>'));
            });
            card.appendChild(body); box.appendChild(card);
          });
          box.appendChild(el('<div style="text-align:right;font-weight:700;margin-top:6px;border-top:1px solid #2b3a5c;padding-top:8px;">Celkem: '+j.total_people+' lidí · '+nf(j.total_hours)+' h</div>'));
        });
      }
      load();
    }
    function renderUvazek(){
      left.innerHTML='<div class="hint">Načítám…</div>';
      api("GET","/api/v1/erp/app/plan/my-uvazek","").then(function(j){
        left.innerHTML='';
        if(!j||!j.ok){ left.appendChild(el('<div class="hint">'+esc((j&&j.error)||"Nelze načíst")+'</div>')); return; }
        left.appendChild(el('<div style="margin-bottom:8px;"><b>📐 Můj úvazek</b> <span class="hint">· '+(j.can_edit?'lze upravit':'jen k náhledu')+'</span></div>'));
        var iS="box-sizing:border-box;padding:10px;border-radius:9px;border:1px solid #2b3a5c;background:#0a1226;color:#e8eefc;";
        left.appendChild(el('<label class="hint" style="display:block;margin:2px 0;">Týdenní úvazek (h)</label>'));
        var uin=el('<input type="number" min="1" max="80" step="0.5" value="'+j.uvazek+'" '+(j.can_edit?'':'disabled')+' style="width:100%;'+iS+'margin-bottom:10px;">');
        left.appendChild(uin);
        left.appendChild(el('<div class="hint" style="margin-bottom:2px;">Týdenní vzorec (které dny a kolik hodin)</div>'));
        var dayEls=[];
        j.days.forEach(function(d){
          var row=el('<div style="border-bottom:1px solid #1b2742;padding:8px 2px;"></div>');
          var top=el('<div style="display:flex;align-items:center;gap:8px;"></div>');
          var cb=el('<input type="checkbox" '+(d.works?'checked':'')+' '+(j.can_edit?'':'disabled')+' style="width:18px;height:18px;flex:none;">');
          top.appendChild(cb);
          top.appendChild(el('<div style="flex:1;">'+d.label+'</div>'));
          var hin=el('<input type="number" min="0" max="24" step="0.5" value="'+d.hours+'" '+(j.can_edit?'':'disabled')+' style="width:64px;'+iS+'text-align:right;padding:8px 6px;">');
          top.appendChild(hin); top.appendChild(el('<span class="hint" style="flex:none;">h</span>'));
          row.appendChild(top);
          var sub=el('<div style="display:flex;align-items:center;gap:8px;margin-top:6px;padding-left:26px;"></div>');
          sub.appendChild(el('<span class="hint" style="flex:none;">příchod od</span>'));
          var tin=el('<input type="time" value="'+(d.start||"")+'" '+(j.can_edit?'':'disabled')+' style="flex:1;'+iS+'padding:8px 6px;">');
          sub.appendChild(tin);
          row.appendChild(sub);
          dayEls.push({weekday:d.weekday, cb:cb, hin:hin, tin:tin});
          var sync=function(){ var on=cb.checked; sub.style.display=on?'flex':'none'; if(j.can_edit){ hin.disabled=!on; tin.disabled=!on; if(!on){ hin.value="0"; tin.value=""; } else if(parseFloat(hin.value)===0){ hin.value=String(j.per_day||8); } } };
          cb.addEventListener("change",sync); sync();
          left.appendChild(row);
        });
        if(j.can_edit){
          var rb=el('<button class="ghost full" style="margin-top:10px;">↻ Rozpočítat úvazek do zaškrtnutých dnů</button>');
          rb.addEventListener("click",function(){ var uvz=parseFloat(uin.value)||0; var wc=dayEls.filter(function(x){return x.cb.checked;}).length||1; var pd=Math.round((uvz/wc)*100)/100; dayEls.forEach(function(x){ x.hin.value=x.cb.checked?pd:0; }); });
          left.appendChild(rb);
          var sb=el('<button class="green full" style="margin-top:8px;">Uložit úvazek</button>');
          var sst=el('<div class="hint" style="margin-top:6px;"></div>');
          sb.addEventListener("click",function(){
            var uvz=parseFloat(uin.value)||0;
            var days=dayEls.map(function(x){ return {weekday:x.weekday, works:x.cb.checked, hours:parseFloat(x.hin.value)||0, start:(x.tin.value||"")}; });
            sb.disabled=true; sst.textContent="Ukládám…";
            api("POST","/api/v1/erp/app/plan/my-uvazek/save",{uvazek:uvz, days:days}).then(function(r){
              sb.disabled=false; sst.textContent=(r&&r.ok)?"✅ Uloženo — 👤 Můj plán se přepočítá":("✗ "+((r&&r.error)||"chyba"));
            });
          });
          left.appendChild(sb); left.appendChild(sst);
        }
      });
    }
    // Marti 14.6.: „Moje podmínky" — RO, celoobrazovkový hezký přehled (pravá lišta se schová).
    function renderPodminky(){
      function hhmm(h){ h=Math.max(0,Math.round((h||0)*60)); return Math.floor(h/60)+":"+("0"+(h%60)).slice(-2); }
      if(right)right.style.display='none';
      function exitPod(){ if(right)right.style.display=AP?'none':'flex'; window._planAnyOpen=null; renderPlan(false,'mydefault'); }
      window._planAnyOpen=function(){ exitPod(); return true; };
      left.innerHTML='<div class="hint">Načítám…</div>';
      api("GET","/api/v1/erp/app/plan/my-uvazek","").then(function(j){
        left.innerHTML='';
        var bk=el('<button id="podBack" class="ghost full" style="margin-bottom:10px;">‹ Zpět</button>'); bk.addEventListener("click",exitPod); left.appendChild(bk);
        if(!j||!j.ok){ left.appendChild(el('<div class="hint">'+esc((j&&j.error)||"Nelze načíst")+'</div>')); return; }
        left.appendChild(el('<div style="margin-bottom:10px;"><b style="font-size:17px;">📋 Moje podmínky</b></div>'));
        var card=el('<div style="border:1px solid #2b3a5c;border-radius:12px;margin-bottom:10px;overflow:hidden;"></div>');
        card.appendChild(el('<div style="padding:11px 12px;background:#0e1830;display:flex;justify-content:space-between;align-items:center;"><span style="font-weight:700;">Týdenní úvazek</span><b style="font-size:16px;color:#cfe0ff;">'+(j.uvazek||"?")+' h</b></div>'));
        var body=el('<div style="padding:4px 10px 8px;"></div>');
        (j.days||[]).forEach(function(d){
          var work=d.works && d.hours>0;
          var rs="display:flex;justify-content:space-between;align-items:center;padding:7px 4px;font-size:14px;border-bottom:1px solid rgba(255,255,255,.05);";
          var rightCell;
          if(work){ rightCell='<span style="display:inline-flex;align-items:baseline;gap:10px;"><span style="color:#8fb4e8;font-size:12px;min-width:56px;text-align:right;">'+(d.start?'od '+d.start:'')+'</span><span style="color:#34d399;font-weight:700;min-width:46px;text-align:right;">'+hhmm(d.hours)+'</span></span>'; }
          else { rightCell='<span style="color:#5b6b88;font-weight:600;">volno</span>'; }
          body.appendChild(el('<div style="'+rs+'"><span>'+esc(d.label||"")+'</span>'+rightCell+'</div>'));
        });
        card.appendChild(body); left.appendChild(card);
        // Samostatná sekce: další sjednané podmínky (staff_cond, resolved) — pod základními.
        var ch=el('<div style="border:1px solid #2b3a5c;border-radius:12px;margin-bottom:10px;overflow:hidden;"></div>');
        ch.appendChild(el('<div style="padding:11px 12px;background:#0e1830;font-weight:700;">Sjednané podmínky</div>'));
        var cb=el('<div style="padding:4px 10px 8px;"></div>');
        cb.appendChild(el('<div class="hint" style="padding:6px 2px;">Načítám…</div>'));
        ch.appendChild(cb); left.appendChild(ch);
        api("GET","/api/v1/erp/app/my-conditions","").then(function(c){
          cb.innerHTML='';
          var items=((c&&c.ok&&c.podminky)||[]).filter(function(p){ return p.code!=='uvazek_h_tyden'; });
          if(!items.length){ cb.appendChild(el('<div class="hint" style="padding:6px 2px;">Žádné další sjednané podmínky.</div>')); return; }
          var srcMap={user:'osobní',group:'skupina',system:'firma'};
          items.forEach(function(p){
            var rs="display:flex;justify-content:space-between;align-items:center;gap:10px;padding:7px 4px;font-size:14px;border-bottom:1px solid rgba(255,255,255,.05);";
            cb.appendChild(el('<div style="'+rs+'"><span style="flex:1;min-width:0;">'+esc(p.label)+'</span><span style="display:inline-flex;align-items:baseline;gap:8px;flex:none;"><b style="color:#cfe0ff;">'+esc(String(p.value))+(p.unit?(' '+esc(p.unit)):'')+'</b><span class="hint" style="font-size:11px;">'+(srcMap[p.src]||p.src||'')+'</span></span></div>'));
          });
        }).catch(function(){ cb.innerHTML='<div class="hint" style="padding:6px 2px;">Nepodařilo se načíst.</div>'; });
        left.appendChild(el('<div class="hint" style="line-height:1.5;padding:2px 4px;">Tvé sjednané podmínky (úvazek, rozvrh a další). Jen k náhledu — změnu řeší nadřízený / HR.</div>'));
      });
    }
    function renderExc(mode){
      mode=mode||'firma';
      left.innerHTML='';
      var hd=el('<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;"></div>');
      hd.appendChild(el('<b>'+(mode==='scope'?'👥 Skupiny výjimky':'🏢 Firemní výjimky')+'</b>'));
      var addB=el('<button class="ghost" style="padding:6px 12px;border-color:#3a7a4c;color:#7fe0a0;font-weight:700;">+ Přidat</button>');
      addB.addEventListener("click",function(){ excDialog(null, mode); });
      hd.appendChild(addB); left.appendChild(hd);
      left.appendChild(el('<div class="hint" style="line-height:1.6;margin-bottom:8px;">'+(mode==='scope'?'Volno / zkrácený den / přesčas jen pro <b>skupinu</b> (např. Výroba — omezení při nedostatku práce nebo nařízené přesčasy). Přebíjí firemní výjimku. Edituje jen vedení / personalistika.':'Firemní den pro <b>celou firmu</b>. <b>0 h</b> = volno, jinak počet odpracovaných hodin (i pracovní víkend).')+' Plán (vrstva 1) zůstává nedotčený.</div>'));
      var box=el('<div></div>'); left.appendChild(box);
      box.innerHTML='<div class="hint">Načítám…</div>';
      Promise.all([api("GET","/api/v1/erp/app/plan/exceptions",""),api("GET","/api/v1/erp/app/plan/scope-exceptions","")]).then(function(res){
        var jc=res[0], js=res[1]; box.innerHTML='';
        if(jc&&jc.ok===false&&jc.error){ box.appendChild(el('<div class="hint">'+esc(jc.error)+'</div>')); return; }
        var items=[];
        if(mode!=='scope' && jc&&jc.ok&&jc.exceptions){ jc.exceptions.forEach(function(e){ items.push({kind:'firma',date:e.date,hours:e.hours,reason:e.reason,scope_name:'Celá firma',icon:'🏢'}); }); }
        if(mode==='scope' && js&&js.ok&&js.items){ js.items.filter(function(e){ return e.scope_type==='group'; }).forEach(function(e){ items.push({kind:'scope',id:e.id,scope_type:e.scope_type,scope_id:e.scope_id,date:e.date,hours:e.hours,reason:e.reason,scope_name:e.scope_name,icon:'👥'}); }); }
        if(!items.length){ box.appendChild(el('<div class="hint">Zatím žádné výjimky.</div>')); return; }
        items.sort(function(a,b){ return a.date<b.date?-1:(a.date>b.date?1:0); });
        items.forEach(function(e){
          var row=el('<div style="display:flex;align-items:center;gap:8px;border-bottom:1px solid #1b2742;padding:9px 4px;"></div>');
          var lbl=(e.hours===0?"volno":(nf(e.hours)+" h"));
          row.appendChild(el('<div style="flex:1;"><b>'+czd2(e.date)+'</b> · <span style="color:#e6a93a;font-weight:600;">'+lbl+'</span> <span class="hint">'+e.icon+' '+esc(e.scope_name)+'</span>'+(e.reason?('<br><span class="hint">'+esc(e.reason)+'</span>'):'')+'</div>'));
          var edit=el('<button class="ghost" style="padding:6px 12px;border-color:#3a5a8c;color:#9cf;">Upravit</button>');
          edit.addEventListener("click",function(){ excDialog(e, mode); });
          row.appendChild(edit); box.appendChild(row);
        });
      });
    }
    function excDialog(ex, mode){
      var isEdit=!!ex;
      var _reMode=isEdit?(ex.kind==='firma'?'firma':'scope'):(mode||'firma');  // po uložení/smazání se vrať do stejné sekce
      var t=new Date(); var today=t.getFullYear()+"-"+("0"+(t.getMonth()+1)).slice(-2)+"-"+("0"+t.getDate()).slice(-2);
      var inS="width:100%;box-sizing:border-box;padding:10px;border-radius:9px;border:1px solid #2b3a5c;background:#0a1226;color:#e8eefc;";
      var ov=el('<div style="position:fixed;inset:0;z-index:300;background:rgba(2,6,14,.72);display:flex;align-items:center;justify-content:center;padding:20px;"></div>');
      var bx=el('<div style="background:#0e1830;border:1px solid #2b3a5c;border-radius:14px;padding:16px;width:100%;max-width:340px;"></div>');
      bx.appendChild(el('<div style="font-weight:700;margin-bottom:10px;">'+(isEdit?'Upravit výjimku':'Nová výjimka')+'</div>'));
      var scopeType=isEdit?(ex.kind==='firma'?'firma':ex.scope_type):(mode==='scope'?'group':'firma');
      var targets=null, tgtSel=null;
      var scopeBox=el('<div style="margin-bottom:6px;"></div>'); bx.appendChild(scopeBox);
      var tgtBox=el('<div></div>'); bx.appendChild(tgtBox);
      function buildTgt(){
        tgtBox.innerHTML=''; tgtSel=null;
        if(isEdit||scopeType==='firma') return;
        var arr=scopeType==='group'?((targets&&targets.groups)||[]):((targets&&targets.people)||[]);
        var opts=arr.map(function(o){ var id=(scopeType==='group'?o.id:o.user_id); return '<option value="'+id+'">'+esc(o.name)+'</option>'; }).join('');
        tgtBox.appendChild(el('<label class="hint" style="display:block;margin:4px 0 2px;">'+(scopeType==='group'?'Skupina':'Osoba')+'</label>'));
        tgtSel=el('<select style="'+inS+'">'+opts+'</select>'); tgtBox.appendChild(tgtSel);
      }
      function ensureTargets(cb){ if(targets){ cb(); return; } api("GET","/api/v1/erp/app/plan/exception-targets","").then(function(j){ targets=(j&&j.ok)?j:{groups:[],people:[]}; cb(); }); }
      if(isEdit){
        scopeBox.appendChild(el('<div class="hint">Rozsah: <b>'+(ex.kind==='firma'?'Celá firma':((ex.scope_type==='group'?'Skupina — ':'Jednotlivec — ')+esc(ex.scope_name)))+'</b></div>'));
      } else if(mode==='scope'){
        scopeType='group';
        scopeBox.appendChild(el('<div class="hint">Rozsah: <b>Skupina</b></div>'));
        ensureTargets(buildTgt);
      } else {
        scopeBox.appendChild(el('<div class="hint">Rozsah: <b>Celá firma</b></div>'));
      }
      bx.appendChild(el('<label class="hint" style="display:block;margin:6px 0 2px;">Datum</label>'));
      var dI=el('<input type="date" value="'+(isEdit?ex.date:today)+'" '+(isEdit?'disabled':'')+' style="'+inS+(isEdit?'opacity:.6;':'')+'">'); bx.appendChild(dI);
      bx.appendChild(el('<label class="hint" style="display:block;margin:8px 0 2px;">Hodiny (0 = volno · jinak počet odpracovaných hodin, i pracovní víkend)</label>'));
      var hI=el('<input type="number" min="0" max="12" step="0.5" value="'+(isEdit?ex.hours:0)+'" style="'+inS+'">'); bx.appendChild(hI);
      var rI=el('<input type="text" placeholder="Důvod (volitelné)" style="'+inS+'margin-top:8px;">'); bx.appendChild(rI);
      if(isEdit) rI.value=ex.reason||"";
      var bs=el('<div style="display:flex;gap:8px;margin-top:12px;"></div>');
      var cancel=el('<button class="ghost" style="flex:1;">Zavřít</button>');
      var save=el('<button class="green" style="flex:1;">Uložit</button>');
      cancel.addEventListener("click",function(){ ov.remove(); });
      save.addEventListener("click",function(){
        var hrs=parseFloat(hI.value)||0, reason=rI.value; save.disabled=true;
        var done=function(r){ if(r&&r.ok){ ov.remove(); renderExc(_reMode); } else { save.disabled=false; alert("Chyba: "+((r&&r.error)||"?")); } };
        if(isEdit){
          if(ex.kind==='firma') api("POST","/api/v1/erp/app/plan/exceptions",{date:ex.date,hours:hrs,reason:reason}).then(done);
          else api("POST","/api/v1/erp/app/plan/scope-exceptions",{scope_type:ex.scope_type,scope_id:ex.scope_id,date:ex.date,hours:hrs,reason:reason}).then(done);
        } else if(scopeType==='firma'){
          api("POST","/api/v1/erp/app/plan/exceptions",{date:dI.value,hours:hrs,reason:reason}).then(done);
        } else {
          if(!tgtSel||!tgtSel.value){ save.disabled=false; alert("Vyber "+(scopeType==='group'?'skupinu':'osobu')+"."); return; }
          api("POST","/api/v1/erp/app/plan/scope-exceptions",{scope_type:scopeType,scope_id:parseInt(tgtSel.value,10),date:dI.value,hours:hrs,reason:reason}).then(done);
        }
      });
      bs.appendChild(cancel); bs.appendChild(save); bx.appendChild(bs);
      if(isEdit){
        var del=el('<button class="ghost full" style="margin-top:8px;color:#f87171;border-color:#5a2b2b;">🗑 Smazat výjimku</button>');
        del.addEventListener("click",function(){
          if(!confirm("Smazat výjimku "+czd2(ex.date)+"?")) return; del.disabled=true;
          var done=function(r){ if(r&&r.ok){ ov.remove(); renderExc(_reMode); } else { del.disabled=false; alert("Chyba: "+((r&&r.error)||"?")); } };
          if(ex.kind==='firma') api("POST","/api/v1/erp/app/plan/exceptions/delete",{date:ex.date}).then(done);
          else api("POST","/api/v1/erp/app/plan/scope-exceptions/delete",{id:ex.id}).then(done);
        });
        bx.appendChild(del);
      }
      ov.appendChild(bx); document.body.appendChild(ov);
      ov.addEventListener("click",function(ev){ if(ev.target===ov) ov.remove(); });
    }
    // Marti 14.6.: vstupní pohled z regionu docházky (Můj úvazek / Můj plán).
    if(AP){ renderPlan(false,'mydefault'); }
    else if(WEEKONLY){ window._planInit=null; renderPlan(false,'mydefault'); }
    else if(window._planInit==="uvazek"){ window._planInit=null; renderUvazek(); }
    else if(window._planInit==="myplan"){ window._planInit=null; renderPlan(false,'mydefault'); try{ setTimeout(function(){ if(right&&bMy) right.scrollTop=Math.max(0, bMy.offsetTop-4); },80); }catch(e){} }
    else renderPlan();
  }
  function plan_vyjimky(){
    app.innerHTML=topbar("🏢 Firemní výjimky", true);
    function nf(v){ return (Math.round((v||0)*100)/100).toString().replace('.',','); }
    function czd(iso){ var p=(iso||"").split("-"); return p.length===3?(p[2]+"."+p[1]+"."+p[0]):iso; }
    app.appendChild(el('<div class="hint" style="line-height:1.6;margin-bottom:10px;">Globální firemní volno / zkrácený den na konkrétní datum. <b>0 h</b> = celé volno, <b>1–8 h</b> = zkrácený den. Nepřepisuje plán — skládá se s ním.</div>'));
    var t=new Date(); var today=t.getFullYear()+"-"+("0"+(t.getMonth()+1)).slice(-2)+"-"+("0"+t.getDate()).slice(-2);
    var inS="width:100%;box-sizing:border-box;padding:9px;border-radius:9px;border:1px solid #2b3a5c;background:#0a1226;color:#e8eefc;";
    var f=el('<div style="border:1px solid #2b3a5c;border-radius:12px;padding:12px;margin-bottom:14px;"></div>');
    f.innerHTML='<div style="font-weight:700;margin-bottom:6px;">Nová výjimka</div>'
      +'<label class="hint" style="display:block;margin:4px 0 2px;">Datum</label><input id="exD" type="date" value="'+today+'" style="'+inS+'">'
      +'<label class="hint" style="display:block;margin:6px 0 2px;">Hodiny (0 = volno, 1–8 zkráceno)</label><input id="exH" type="number" min="0" max="8" step="0.5" value="0" style="'+inS+'">'
      +'<input id="exR" type="text" placeholder="Důvod (např. celozávodní dovolená)" style="'+inS+'margin-top:8px;">';
    var sb=el('<button class="green full" style="margin-top:10px;">Uložit výjimku</button>');
    var sst=el('<div class="hint" style="margin-top:6px;"></div>');
    sb.addEventListener("click",function(){
      sb.disabled=true; sst.textContent="Ukládám…";
      api("POST","/api/v1/erp/app/plan/exceptions",{date:f.querySelector('#exD').value, hours:parseFloat(f.querySelector('#exH').value)||0, reason:f.querySelector('#exR').value}).then(function(r){
        sb.disabled=false; sst.textContent=(r&&r.ok)?"✅ Uloženo":("✗ "+((r&&r.error)||"chyba"));
        if(r&&r.ok){ f.querySelector('#exR').value=""; load(); }
      });
    });
    f.appendChild(sb); f.appendChild(sst); app.appendChild(f);
    var list=el('<div></div>'); app.appendChild(list);
    function load(){
      list.innerHTML='<div class="hint">Načítám…</div>';
      api("GET","/api/v1/erp/app/plan/exceptions","").then(function(j){
        list.innerHTML="";
        if(!j||!j.ok){ list.appendChild(el('<div class="hint">'+esc((j&&j.error)||"Nelze načíst")+'</div>')); return; }
        if(!j.exceptions.length){ list.appendChild(el('<div class="hint">Zatím žádné výjimky.</div>')); return; }
        list.appendChild(el('<div style="font-weight:700;margin-bottom:6px;">Zadané výjimky</div>'));
        j.exceptions.forEach(function(e){
          var row=el('<div style="display:flex;align-items:center;gap:8px;border-bottom:1px solid #1b2742;padding:9px 4px;"></div>');
          var lbl=(e.hours===0?"volno":(nf(e.hours)+" h"));
          row.appendChild(el('<div style="flex:1;"><b>'+czd(e.date)+'</b> · <span style="color:#e6a93a;font-weight:600;">'+lbl+'</span>'+(e.reason?('<br><span class="hint">'+esc(e.reason)+'</span>'):'')+'</div>'));
          var del=el('<button class="ghost" style="padding:6px 10px;color:#f87171;border-color:#5a2b2b;">Smazat</button>');
          del.addEventListener("click",function(){ if(!confirm("Smazat výjimku "+czd(e.date)+"?")) return; api("POST","/api/v1/erp/app/plan/exceptions/delete",{date:e.date}).then(function(r){ if(r&&r.ok) load(); else alert("Chyba: "+((r&&r.error)||"?")); }); });
          row.appendChild(del); list.appendChild(row);
        });
      });
    }
    load();
  }
  function master_cinnosti(){
    app.innerHTML=topbar("🛠 Master číselník", true);
    var K=window._cinKind||"standard";
    var tg2=el('<div style="display:flex;gap:6px;margin:2px 0 10px;"></div>');
    [["standard","🧾 Běžné zakázky"],["rezie","🧰 Režie"]].forEach(function(t){
      var b=el('<button style="flex:1;padding:9px 4px;border-radius:11px;font-size:13px;font-weight:600;border:1px solid '+(K===t[0]?"#4f8ef7":"var(--bord)")+';background:'+(K===t[0]?"rgba(79,142,247,.14)":"rgba(255,255,255,.03)")+';color:'+(K===t[0]?"var(--tx)":"var(--mut)")+';">'+t[1]+'</button>');
      b.addEventListener("click",function(){ window._cinKind=t[0]; master_cinnosti(); });
      tg2.appendChild(b);
    });
    app.appendChild(tg2);
    app.appendChild(el('<div class="hint" style="line-height:1.6;margin-bottom:10px;">'+(K==="rezie"?"Seznam <b>režijních</b> činností (zakázka Režie).":"Výchozí seznam činností (pro běžné zakázky).")+' Přidej, přejmenuj, změň pořadí, skryj. Pracovníci si z něj dělají vlastní seznam.</div>'));
    var addb=el('<button class="green full" style="margin-bottom:10px;">+ Přidat činnost</button>');
    addb.addEventListener("click",function(){ var n=prompt("Název nové činnosti:"); if(!n||!n.trim())return; api("POST","/api/v1/erp/app/vyroba/cinnost-master/save",{name:n.trim(),kind:K}).then(function(r){ if(r&&r.ok) load(); else alert("Chyba: "+((r&&r.error)||"?")); }); });
    app.appendChild(addb);
    var box=el('<div></div>'); app.appendChild(box);
    app.appendChild(el('<div style="height:120px;"></div>'));
    var _all=[];
    function saveOrder(){ api("POST","/api/v1/erp/app/vyroba/cinnost-master/order",{order:_all.map(function(c){return c.id;})}).then(function(){}); }
    function render(){
      box.innerHTML='';
      _all.forEach(function(c,idx){
        var row=el('<div style="display:flex;align-items:center;gap:6px;border-bottom:1px solid #1b2742;padding:8px 4px;'+(c.active?'':'opacity:.5;')+'"></div>');
        var up=el('<button class="ghost" style="padding:4px 9px;flex:none;" '+(idx===0?'disabled':'')+'>▲</button>');
        var dn=el('<button class="ghost" style="padding:4px 9px;flex:none;" '+(idx===_all.length-1?'disabled':'')+'>▼</button>');
        up.addEventListener("click",function(){ if(idx===0)return; var t=_all[idx-1]; _all[idx-1]=_all[idx]; _all[idx]=t; render(); saveOrder(); });
        dn.addEventListener("click",function(){ if(idx===_all.length-1)return; var t=_all[idx+1]; _all[idx+1]=_all[idx]; _all[idx]=t; render(); saveOrder(); });
        row.appendChild(up); row.appendChild(dn);
        var ib=el('<button class="ghost" style="padding:4px 8px;flex:none;font-size:18px;line-height:1;" title="Změnit ikonu">'+(c.icon||"🔧")+'</button>');
        ib.addEventListener("click",function(){ var ic=prompt("Ikona (emoji) pro „"+c.name+"\":", c.icon||""); if(ic===null)return; ic=(ic||"").trim(); if(!ic||ic===c.icon)return; api("POST","/api/v1/erp/app/vyroba/cinnost-master/save",{id:c.id,icon:ic}).then(function(r){ if(r&&r.ok) load(); else alert("Chyba"); }); });
        row.appendChild(ib);
        var nm=el('<div style="flex:1;font-weight:600;cursor:pointer;">'+esc(c.name)+(c.active?'':' <span class="hint">(skryto)</span>')+'</div>');
        nm.addEventListener("click",function(){ var n=prompt("Název činnosti:",c.name); if(!n||!n.trim()||n.trim()===c.name)return; api("POST","/api/v1/erp/app/vyroba/cinnost-master/save",{id:c.id,name:n.trim()}).then(function(r){ if(r&&r.ok) load(); else alert("Chyba"); }); });
        row.appendChild(nm);
        var tg=el('<button class="ghost" style="padding:6px 10px;flex:none;">'+(c.active?'🚫':'👁')+'</button>');
        tg.addEventListener("click",function(){ api("POST","/api/v1/erp/app/vyroba/cinnost-master/save",{id:c.id,active:!c.active}).then(function(r){ if(r&&r.ok) load(); else alert("Chyba"); }); });
        row.appendChild(tg); box.appendChild(row);
      });
    }
    function load(){ box.innerHTML='<div class="hint">Načítám…</div>'; api("GET","/api/v1/erp/app/vyroba/cinnost-master?kind="+K,"").then(function(j){ box.innerHTML=''; if(!j||!j.ok){ box.appendChild(el('<div class="hint">'+esc((j&&j.error)||"Jen pro vedoucí/HR.")+'</div>')); return; } _all=j.cinnosti||[]; render(); }); }
    load();
  }
  function moje_cinnosti(){
    app.innerHTML=topbar("🧰 Moje činnosti", true);
    var K=window._cinKind||"standard";
    var tg3=el('<div style="display:flex;gap:6px;margin:2px 0 10px;"></div>');
    [["standard","🧾 Běžné zakázky"],["rezie","🧰 Režie"]].forEach(function(t){
      var b=el('<button style="flex:1;padding:9px 4px;border-radius:11px;font-size:13px;font-weight:600;border:1px solid '+(K===t[0]?"#4f8ef7":"var(--bord)")+';background:'+(K===t[0]?"rgba(79,142,247,.14)":"rgba(255,255,255,.03)")+';color:'+(K===t[0]?"var(--tx)":"var(--mut)")+';">'+t[1]+'</button>');
      b.addEventListener("click",function(){ window._cinKind=t[0]; moje_cinnosti(); });
      tg3.appendChild(b);
    });
    app.appendChild(tg3);
    // Marti 14.6.: vybrané činnosti složené jako ikony rovnou nahoře (náhled plochy).
    var _topGrid=el('<div class="appgrid" style="margin-bottom:12px;"></div>'); app.appendChild(_topGrid);
    app.appendChild(el('<div class="hint" style="line-height:1.6;margin-bottom:10px;">Vyber, které činnosti chceš mít ve svém seznamu a v jakém pořadí. Výchozí = všechny. ▲▼ pořadí · ✕ odebrat · + přidat zpět.</div>'));
    var mb=el('<button class="ghost full" style="margin-top:16px;border-color:#6b4a2a;color:#e6b97a;">🛠 Master číselník (správa)</button>');
    mb.addEventListener("click",function(){ go("master_cinnosti"); });
    var box=el('<div></div>'); app.appendChild(box);
    app.appendChild(mb);
    app.appendChild(el('<div style="height:120px;"></div>'));
    var _mine=[];
    function saveOrder(){ api("POST","/api/v1/erp/app/vyroba/my-cinnosti/order",{order:_mine.map(function(c){return c.id;})}).then(function(){}); }
    function renderMine(ml){
      ml.innerHTML='';
      if(!_mine.length){ ml.appendChild(el('<div class="hint">Prázdný seznam — přidej činnosti níže.</div>')); return; }
      _mine.forEach(function(c,idx){
        var row=el('<div style="display:flex;align-items:center;gap:6px;border-bottom:1px solid #1b2742;padding:8px 4px;"></div>');
        var up=el('<button class="ghost" style="padding:4px 9px;flex:none;" '+(idx===0?'disabled':'')+'>▲</button>');
        var dn=el('<button class="ghost" style="padding:4px 9px;flex:none;" '+(idx===_mine.length-1?'disabled':'')+'>▼</button>');
        up.addEventListener("click",function(){ if(idx===0)return; var t=_mine[idx-1]; _mine[idx-1]=_mine[idx]; _mine[idx]=t; renderMine(ml); saveOrder(); });
        dn.addEventListener("click",function(){ if(idx===_mine.length-1)return; var t=_mine[idx+1]; _mine[idx+1]=_mine[idx]; _mine[idx]=t; renderMine(ml); saveOrder(); });
        row.appendChild(up); row.appendChild(dn);
        row.appendChild(el('<div style="flex:1;font-weight:600;"><span style="margin-right:6px;">'+(c.icon||"🔧")+'</span>'+esc(c.name)+'</div>'));
        var rm=el('<button class="ghost" style="padding:6px 10px;flex:none;color:#f87171;border-color:#5a2b2b;">✕</button>');
        rm.addEventListener("click",function(){ api("POST","/api/v1/erp/app/vyroba/my-cinnosti/toggle",{cinnost_id:c.id,in_list:false}).then(function(r){ if(r&&r.ok) load(); else alert("Chyba: "+((r&&r.error)||"?")); }); });
        row.appendChild(rm); ml.appendChild(row);
      });
    }
    function load(){
      box.innerHTML='<div class="hint">Načítám…</div>';
      api("GET","/api/v1/erp/app/vyroba/my-cinnosti?kind="+K,"").then(function(j){
        box.innerHTML='';
        if(!j||!j.ok){ box.appendChild(el('<div class="hint">Nelze načíst.</div>')); return; }
        _mine=(j.cinnosti||[]).filter(function(c){return !c.hidden;});
        var avail=(j.cinnosti||[]).filter(function(c){return c.hidden;});
        // náhled plochy nahoře — vybrané činnosti jako ikony
        if(_topGrid){ _topGrid.innerHTML=''; _mine.forEach(function(c){ _topGrid.appendChild(appCell(c.icon||"🔧",c.name,0,function(){})); }); }
        box.appendChild(el('<div style="font-weight:700;margin-bottom:6px;">Můj seznam ('+_mine.length+')</div>'));
        var ml=el('<div></div>'); box.appendChild(ml); renderMine(ml);
        box.appendChild(el('<div style="font-weight:700;margin:14px 0 6px;">Přidat ze seznamu</div>'));
        if(!avail.length){ box.appendChild(el('<div class="hint">Máš všechny činnosti ve svém seznamu.</div>')); }
        avail.forEach(function(c){
          var row=el('<div style="display:flex;align-items:center;gap:8px;border-bottom:1px solid #1b2742;padding:9px 4px;"></div>');
          row.appendChild(el('<div style="flex:1;color:#8696b8;"><span style="margin-right:6px;">'+(c.icon||"🔧")+'</span>'+esc(c.name)+'</div>'));
          var add=el('<button class="ghost" style="padding:6px 12px;flex:none;border-color:#3a7a4c;color:#7fe0a0;">+ Přidat</button>');
          add.addEventListener("click",function(){ api("POST","/api/v1/erp/app/vyroba/my-cinnosti/toggle",{cinnost_id:c.id,in_list:true}).then(function(r){ if(r&&r.ok) load(); else alert("Chyba: "+((r&&r.error)||"?")); }); });
          row.appendChild(add); box.appendChild(row);
        });
      });
    }
    load();
  }
  // Marti 14.6.: „Na čem dělám" — osa přiřazení práce (zakázka+činnost) MIMO jádro docházky.
  function prace(){
    app.innerHTML=topbar("🧾 Na čem dělám", true);
    var box=el('<div style="padding-bottom:100px;"></div>'); app.appendChild(box);
    box.innerHTML='<div class="hint">Načítám…</div>';
    var _cur=null,_atwork=false,_mine=[];
    function _err(r){ alert((r&&(r.msg||r.error))||"Nepodařilo se."); }
    function setCin(ci){ api("POST","/api/v1/erp/app/work/set-cinnost",{cinnost_id:ci}).then(function(r){ if(r&&r.ok) load(); else _err(r); }); }
    function setZak(cislo,nazev){ api("POST","/api/v1/erp/app/work/set-zakazka",{project_ref:cislo,project_nazev:nazev}).then(function(r){ if(r&&r.ok) load(); else _err(r); }); }
    function setRezie(){ api("POST","/api/v1/erp/app/work/set-rezie",{}).then(function(r){ if(r&&r.ok) load(); else _err(r); }); }
    function zakPicker(host){
      host.innerHTML="";
      host.appendChild(el('<div class="hint" style="margin:4px 0 2px;">Najdi zakázku (číslo / název):</div>'));
      var si=el('<input placeholder="🔍 číslo nebo název…" autocomplete="off">');
      var res=el('<div style="margin-top:6px;"></div>'); var tmr=null;
      function zl(){ var q=(si.value||"").trim(); api("GET","/api/v1/erp/app/zakazky"+(q?("?q="+encodeURIComponent(q)):""),"").then(function(j){ res.innerHTML=""; ((j&&j.zakazky)||[]).slice(0,12).forEach(function(z){ var zb=el('<button class="ghost full" style="margin-top:6px;font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;text-align:left;">'+((z.typ==="REZIE")?"🧰 ":"🧾 ")+esc(z.cislo)+' — '+esc(z.nazev||"")+'</button>'); zb.addEventListener("click",function(){ setZak(z.cislo,z.nazev||""); }); res.appendChild(zb); }); }); }
      si.addEventListener("input",function(){ clearTimeout(tmr); tmr=setTimeout(zl,300); });
      host.appendChild(si); host.appendChild(res); zl();
    }
    function render(){
      box.innerHTML="";
      if(!_atwork){
        box.appendChild(el('<div style="background:var(--bg);border:1px solid var(--bord);border-radius:12px;padding:16px;text-align:center;line-height:1.6;"><div style="font-size:32px;">😴</div><div style="font-weight:700;margin-top:6px;">Nejsi přihlášený v práci</div><div class="hint" style="margin-top:4px;">Nejdřív se přihlas do práce v docházce — pak si tu vybereš zakázku a činnost.</div></div>'));
        return;
      }
      var a=_cur||{};
      var zText=a.is_rezie?"🧰 Režie (bez zakázky)":(a.project_ref?("🧾 "+esc(a.project_ref)+(a.project_nazev?(" — "+esc(a.project_nazev)):"")):"— žádná zakázka —");
      var cText=a.cinnost_name?("🔧 "+esc(a.cinnost_name)):"— žádná činnost —";
      var head=el('<div style="background:var(--bg);border:1px solid var(--green);border-radius:12px;padding:14px;margin-bottom:12px;"></div>');
      head.appendChild(el('<div class="hint" style="font-size:11px;letter-spacing:.5px;">PRÁVĚ DĚLÁM'+(a.since?(' · od '+esc(a.since)):'')+'</div>'));
      head.appendChild(el('<div style="font-size:16px;font-weight:700;margin-top:4px;">'+zText+'</div>'));
      head.appendChild(el('<div style="font-size:15px;margin-top:2px;color:#cdd8ea;">'+cText+'</div>'));
      box.appendChild(head);
      box.appendChild(el('<div style="font-weight:700;margin:6px 2px 6px;">Zakázka</div>'));
      var zwrap=el('<div></div>');
      var zbtn=el('<button class="green full" style="margin-bottom:6px;">🧾 Změnit zakázku</button>');
      zbtn.addEventListener("click",function(){ zakPicker(zwrap); });
      var rbtn=el('<button class="ghost full" style="margin-bottom:10px;border-color:#6b5a2a;color:#e6c86a;">🧰 Režie (bez zakázky)</button>');
      rbtn.addEventListener("click",setRezie);
      box.appendChild(zbtn); box.appendChild(rbtn); box.appendChild(zwrap);
      box.appendChild(el('<div style="font-weight:700;margin:6px 2px 6px;">Činnost</div>'));
      if(!_mine.length){ box.appendChild(el('<div class="hint" style="margin-bottom:10px;">Nemáš vybrané činnosti. Přidej si je v <b>🧰 Moje činnosti</b>.</div>')); }
      var cg=el('<div class="appgrid"></div>');
      _mine.forEach(function(c){ var on=(_cur&&_cur.cinnost_id===c.id); var cell=appCell("🔧",c.name,0,function(){ setCin(c.id); }); if(on){ cell.style.outline="2px solid var(--green)"; cell.style.borderColor="var(--green)"; } cg.appendChild(cell); });
      box.appendChild(cg);
      box.appendChild(el('<div style="font-weight:700;margin:14px 2px 6px;">Dnešní úseky</div>'));
      var tl=el('<div></div>'); box.appendChild(tl);
      api("GET","/api/v1/erp/app/work/today","").then(function(j){ tl.innerHTML=""; var segs=(j&&j.segments)||[]; if(!segs.length){ tl.innerHTML='<div class="hint">Zatím žádné úseky.</div>'; return; } segs.forEach(function(sg){ var z=sg.is_rezie?"Režie":(sg.project_ref?(esc(sg.project_ref)+(sg.project_nazev?(" — "+esc(sg.project_nazev)):"")):"—"); var c=sg.cinnost_name?(" · 🔧 "+esc(sg.cinnost_name)):""; tl.appendChild(el('<div style="border-bottom:1px solid #1b2742;padding:7px 2px;font-size:13px;"><span style="color:#8fb4e8;">'+esc(sg.od)+'–'+esc(sg.do_||"…")+'</span> · '+z+c+' <span class="hint">('+fmtHM(sg.hod)+')</span></div>')); }); });
    }
    function load(){
      box.innerHTML='<div class="hint">Načítám…</div>';
      Promise.all([
        api("GET","/api/v1/erp/app/work/current",""),
        api("GET","/api/v1/erp/app/vyroba/my-cinnosti","")
      ]).then(function(rs){
        var w=rs[0]||{},m=rs[1]||{};
        _atwork=!!w.at_work; _cur=w.alloc||null;
        _mine=((m&&m.cinnosti)||[]).filter(function(c){return !c.hidden;});
        render();
      }).catch(function(){ box.innerHTML='<div class="hint">Nelze načíst.</div>'; });
    }
    load();
  }
  // Marti 14.6.: sekce „Zakázky a činnosti" — pod nadpisem, nad „Potřebuji ti něco říct".
  // Předvýběr funguje vždy; ▶️ Makat zapne docházku z předvýběru; za běhu = změna úseku.
  window._buildWorkSwitch=function(host){
    var ws=el('<div style="margin:4px 0 0;padding:10px;border:1px solid #2a3a4d;border-radius:12px;background:rgba(127,200,224,.05);"></div>');
    var lbl=el('<div class="hint" style="font-size:11px;letter-spacing:.5px;margin-bottom:8px;">ZAKÁZKY A ČINNOSTI</div>'); ws.appendChild(lbl);
    var row=el('<div style="display:flex;gap:8px;"></div>'); ws.appendChild(row);
    var makWrap=el('<div></div>'); ws.appendChild(makWrap);
    host.appendChild(ws);
    function ensureCinPulseCss(){ if(document.getElementById("cinPulseCss"))return; var st=document.createElement("style"); st.id="cinPulseCss"; st.textContent="@keyframes cinpulse{0%,100%{box-shadow:0 0 0 0 rgba(245,158,11,.7);transform:scale(1)}50%{box-shadow:0 0 0 8px rgba(245,158,11,0);transform:scale(1.05)}} .cin-pulse{animation:cinpulse 1.05s ease-in-out infinite;border-color:#f59e0b!important;background:rgba(245,158,11,.14)!important;color:#f4c97a!important;}"; document.head.appendChild(st); }
    function tile(icon,top,sub,onclick,pulse){
      var t=el('<button class="ghost" style="flex:1;min-width:0;display:flex;flex-direction:column;align-items:center;gap:3px;padding:12px 8px;text-align:center;"></button>');
      t.appendChild(el('<div style="font-size:26px;line-height:1;">'+icon+'</div>'));
      t.appendChild(el('<div style="font-size:9.5px;letter-spacing:.5px;color:#8696b8;text-transform:uppercase;">'+esc(top)+'</div>'));
      t.appendChild(el('<div style="font-size:13px;font-weight:700;line-height:1.25;word-break:break-word;">'+esc(sub)+'</div>'));
      if(pulse){ ensureCinPulseCss(); t.classList.add("cin-pulse"); }
      t.addEventListener("click",onclick); return t;
    }
    api("GET","/api/v1/erp/app/work/state","").then(function(j){
      var aw=!!(j&&j.at_work);
      var src=(aw?(j&&j.working_alloc):(j&&j.pref))||(j&&j.pref)||{};
      var zIcon=src.is_rezie?"🧰":"🧾";
      var zSub=src.is_rezie?"Režie":(src.project_ref?(src.project_ref+(src.project_nazev?(" — "+src.project_nazev):"")):"Vyber zakázku");
      var cIcon=src.cinnost_name?(src.cinnost_icon||"🔧"):"🔧";
      var cSub=src.cinnost_name||"Vyber činnost";
      lbl.innerHTML=aw?'<span style="color:var(--green);font-weight:700;">🟢 MAKÁŠ — klikni a změň</span>':'ZAKÁZKY A ČINNOSTI — předvýběr, pak ▶️ Makat';
      row.innerHTML="";
      row.appendChild(tile(zIcon,"Zakázka",zSub,function(){ go("prace_zak"); }, !src.is_rezie && !src.project_ref));
      row.appendChild(tile(cIcon,"Činnost",cSub,function(){ go("prace_cin"); }, !src.cinnost_name));
      makWrap.innerHTML="";
      if(!aw){ var mb=el('<button class="green full" style="margin-top:8px;font-weight:700;">▶️ Makat</button>'); mb.addEventListener("click",function(){ if(window._praceStart) window._praceStart(); }); makWrap.appendChild(mb); }
    }).catch(function(){});
  };
  // Marti 14.6.: „Makat" — zapni docházku + zakázkový systém z předvýběru.
  window._praceStart=function(){
    api("POST","/api/v1/erp/app/attendance/checkin",{kind:"work",switch:true}).then(function(r){
      if(r&&r.need_confirm&&r.need_confirm.length){ alert("Nejdřív si prosím potvrď předchozí docházku (v sekci docházky)."); }
      if(typeof dochLoad==="function") dochLoad();
    }).catch(function(){});
  };
  // Picker zakázky — aktuální/předvybraná nahoře, ostatní (záloha) k výběru dole.
  function prace_zak(){
    app.innerHTML=topbar("🧾 Vyber zakázku", true);
    var box=el('<div style="padding-bottom:100px;"></div>'); app.appendChild(box);
    box.innerHTML='<div class="hint">Načítám…</div>';
    function pick(cislo,nazev){ api("POST","/api/v1/erp/app/work/set-zakazka",{project_ref:cislo,project_nazev:nazev}).then(function(r){ if(r&&r.ok) back(); else alert((r&&(r.msg||r.error))||"Nepodařilo se."); }); }
    function rezie(){ api("POST","/api/v1/erp/app/work/set-rezie",{}).then(function(r){ if(r&&r.ok) back(); else alert((r&&(r.msg||r.error))||"Nepodařilo se."); }); }
    api("GET","/api/v1/erp/app/work/state","").then(function(j){
      box.innerHTML="";
      var cur=((j&&j.at_work&&j.working_alloc)||(j&&j.pref))||{};
      var curTxt=cur.is_rezie?"🧰 Režie (bez zakázky)":(cur.project_ref?("🧾 "+esc(cur.project_ref)+(cur.project_nazev?(" — "+esc(cur.project_nazev)):"")):"— zatím nevybráno —");
      box.appendChild(el('<div style="background:var(--bg);border:1px solid var(--green);border-radius:12px;padding:12px;margin-bottom:10px;"><div class="hint" style="font-size:11px;letter-spacing:.5px;">AKTUÁLNÍ</div><div style="font-weight:700;font-size:15px;margin-top:3px;">'+curTxt+'</div></div>'));
      var rb=el('<button class="ghost full" style="margin-bottom:10px;border-color:#6b5a2a;color:#e6c86a;">🧰 Režie (bez zakázky)</button>'); rb.addEventListener("click",rezie); box.appendChild(rb);
      box.appendChild(el('<div style="font-weight:700;margin:4px 2px 6px;">V záloze — vyber jinou</div>'));
      var si=el('<input placeholder="🔍 číslo nebo název…" autocomplete="off">'); box.appendChild(si);
      var res=el('<div style="margin-top:6px;"></div>'); box.appendChild(res); var tmr=null;
      function zl(){ var q=(si.value||"").trim(); api("GET","/api/v1/erp/app/zakazky"+(q?("?q="+encodeURIComponent(q)):""),"").then(function(jz){ res.innerHTML=""; ((jz&&jz.zakazky)||[]).slice(0,20).forEach(function(z){ var zb=el('<button class="ghost full" style="margin-top:6px;font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;text-align:left;">'+((z.typ==="REZIE")?"🧰 ":"🧾 ")+esc(z.cislo)+' — '+esc(z.nazev||"")+'</button>'); zb.addEventListener("click",function(){ pick(z.cislo,z.nazev||""); }); res.appendChild(zb); }); }); }
      si.addEventListener("input",function(){ clearTimeout(tmr); tmr=setTimeout(zl,300); }); zl();
    });
  }
  // Picker činnosti — aktuální/předvybraná nahoře, dlaždice k výběru.
  function prace_cin(){
    app.innerHTML=topbar("🔧 Vyber činnost", true);
    var box=el('<div style="padding-bottom:100px;"></div>'); app.appendChild(box);
    box.innerHTML='<div class="hint">Načítám…</div>';
    function pick(ci){ api("POST","/api/v1/erp/app/work/set-cinnost",{cinnost_id:ci}).then(function(r){ if(r&&r.ok) back(); else alert((r&&(r.msg||r.error))||"Nepodařilo se."); }); }
    api("GET","/api/v1/erp/app/work/state","").then(function(st){
      st=st||{};
      var cur=((st.at_work&&st.working_alloc)||st.pref)||{};
      var rez=!!cur.is_rezie || (cur.kind==="overhead") || (cur.project_type==="REZIE")
        || (typeof _isRezieRef==="function" && _isRezieRef(cur.project_ref));
      window._cinKind=rez?"rezie":"standard";
      api("GET","/api/v1/erp/app/vyroba/my-cinnosti?kind="+(rez?"rezie":"standard"),"").then(function(m){
        box.innerHTML="";
        var mine=((m&&m.cinnosti)||[]).filter(function(c){return !c.hidden;});
        box.appendChild(el('<div style="background:var(--bg);border:1px solid '+(rez?"#e6c86a":"var(--green)")+';border-radius:12px;padding:12px;margin-bottom:10px;"><div class="hint" style="font-size:11px;letter-spacing:.5px;">'+(rez?"ČINNOST NA REŽII":"AKTUÁLNÍ ČINNOST")+'</div><div style="font-weight:700;font-size:15px;margin-top:3px;">'+(cur.cinnost_name?((cur.cinnost_icon||"🔧")+" "+esc(cur.cinnost_name)):"— zatím nevybráno —")+'</div></div>'));
        if(!mine.length){ box.appendChild(el('<div class="hint" style="margin-bottom:8px;">Nemáš vybrané '+(rez?"režijní ":"")+'činnosti — přidej je tlačítkem níže.</div>')); }
        var cg=el('<div class="appgrid"></div>');
        mine.forEach(function(c){ var on=(cur.cinnost_id===c.id); var cell=appCell(c.icon||"🔧",c.name,0,function(){ pick(c.id); }); if(on){ cell.style.outline="2px solid var(--green)"; cell.style.borderColor="var(--green)"; } cg.appendChild(cell); });
        box.appendChild(cg);
        var mb=el('<button class="ghost full" style="margin-top:12px;border-color:#6b4a2a;color:#e6b97a;">🧰 Upravit seznam '+(rez?"režijních ":"")+'činností</button>'); mb.addEventListener("click",function(){ go("moje_cinnosti"); }); box.appendChild(mb);
      });
    });
  }
  // Marti 15.6.: Web jako obrazovka UVNITŘ appky (iframe), ať hardwarové Zpět
  // vrátí do Aplikací a neukončuje celou appku.
