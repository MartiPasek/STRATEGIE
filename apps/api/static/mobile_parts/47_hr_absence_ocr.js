  function ocr(){
    app.innerHTML=topbar("🧑‍⚕️ Ošetřovné (OČR) · v2", true);
    // Auth gate (Kristý 29.6.): nepřihlášený host nesmí skončit u prázdného
    // formuláře bez cesty k loginu. whoami → jméno = přihlášen; jinak login karta.
    var _ocrLoad=el('<div class="hint" style="margin:12px 6px;">Ověřuji přihlášení…</div>'); app.appendChild(_ocrLoad);
    var _dev=""; try{ if(B&&typeof B.deviceId==="function") _dev=B.deviceId()||""; }catch(e){}
    api("GET","/api/v1/erp/app/whoami"+(_dev?("?device_id="+encodeURIComponent(_dev)):""),"").then(function(w){
      try{ _ocrLoad.remove(); }catch(e){}
      if(!(w && w.jmeno)){ _ocrLoginGate(); return; }
      _ocrListBody();
    });
  }
  function _ocrLoginGate(){
    var box=el('<div style="padding:14px 8px;"></div>');
    box.appendChild(el('<div style="font-weight:800;font-size:17px;margin-bottom:6px;">🔒 Nejdřív se přihlas</div>'));
    box.appendChild(el('<div class="hint" style="line-height:1.6;margin-bottom:14px;">Pro práci s ošetřovným se přihlas jako zaměstnanec. Tvůj OČR případ se založil přeposláním SMS od ČSSZ — po přihlášení ho tu uvidíš předvyplněný.</div>'));
    var bPwd=el('<button style="'+_OCR_BTN+'">🔑 Přihlásit e-mailem a heslem</button>');
    bPwd.addEventListener("click",function(){ try{ openPasswordLogin(); }catch(e){ location.href="/api/v1/auth/sms-login?next="+encodeURIComponent("/mobile?screen=ocr"); } });
    box.appendChild(bPwd);
    var bPair=el('<button class="ghost full" style="margin-top:8px;">🔗 Přihlásit odkazem (SMS)</button>');
    bPair.addEventListener("click",function(){ location.href="/api/v1/auth/sms-login?next="+encodeURIComponent("/mobile?screen=ocr"); });
    box.appendChild(bPair);
    app.appendChild(box);
  }
  function _ocrListBody(){
    app.appendChild(el('<div class="hint" style="margin:8px 6px;line-height:1.6;">Když ti přijde SMS od ČSSZ s identifikátorem ošetřování, založ tu OČR. Po skončení doplníš datum do a počet dní — vedoucí/HR to schválí. (Brzy se dokumenty z ČSSZ potáhnou samy.)</div>'));
    var nb=el('<button style="'+_OCR_BTN+'">➕ Nové ošetřovné</button>'); nb.addEventListener("click",function(){ ocrForm(); }); app.appendChild(nb);
    var box=el('<div class="list" style="margin-top:10px;"><div class="hint">Načítám…</div></div>'); app.appendChild(box);
    api("GET","/api/v1/erp/app/ocr/mine","").then(function(j){
      box.innerHTML="";
      if(!j||!j.ok){ box.innerHTML='<div class="hint">Nepodařilo se načíst.</div>'; return; }
      var cs=j.cases||[];
      if(!cs.length){ box.innerHTML='<div class="hint">Zatím žádné OČR.</div>'; return; }
      cs.forEach(function(c){
        var lbl={novy:"probíhá",ukonceno:"ke schválení",schvaleno:"schváleno"}[c.stav]||c.stav;
        var rw=el('<div style="padding:10px 6px;border-bottom:1px solid var(--bord);cursor:pointer;"></div>');
        rw.appendChild(el('<div style="font-weight:600;display:flex;justify-content:space-between;align-items:center;gap:8px;"><span>'+esc(c.osoba||"")+(c.vztah?(' · '+esc(c.vztah)):'')+'</span><span style="color:#9fd0ff;font-size:20px;line-height:1;">›</span></div>'));
        rw.appendChild(el('<div class="hint">'+_czDate(c.od)+(c.do?(' – '+_czDate(c.do)):'')+(c.dny?(' · '+c.dny+' dní'):'')+' · '+esc(lbl)+(c.company?(' · '+esc(c.company)):'')+'</div>'));
        rw.addEventListener("click",function(){ ocrVyplnit(c.id); });
        var fb=el('<button style="margin-top:6px;margin-right:6px;padding:8px 12px;border-radius:10px;border:1px solid #2b3a5c;background:rgba(159,208,255,.08);color:#9fd0ff;font-weight:700;cursor:pointer;">📋 Vyplnit formulář</button>');
        fb.addEventListener("click",function(e){ try{e.stopPropagation();}catch(_){} ocrVyplnit(c.id); }); rw.appendChild(fb);
        if(c.stav==="novy"){
          var eb=el('<button style="margin-top:6px;padding:8px 12px;border-radius:10px;border:1px solid var(--bord);background:rgba(255,255,255,.04);color:var(--tx);font-weight:700;cursor:pointer;">Ukončit a poslat ke schválení</button>');
          eb.addEventListener("click",function(e){ try{e.stopPropagation();}catch(_){} ocrEndForm(c); }); rw.appendChild(eb);
        }
        box.appendChild(rw);
      });
    });
  }
  function _ocrFld(parent,label,ph,hintTxt){
    var wr=el('<div></div>'); wr.appendChild(el('<div style="font-size:13px;color:#cdd6e2;margin-bottom:4px;">'+esc(label)+'</div>'));
    var i=el('<input type="text" placeholder="'+esc(ph||"")+'" style="width:100%;box-sizing:border-box;padding:10px;border-radius:10px;border:1px solid #2b3a5c;background:#0a1226;color:#e8eefc;">');
    wr.appendChild(i); if(hintTxt) wr.appendChild(el('<div class="hint" style="margin-top:3px;">'+esc(hintTxt)+'</div>')); parent.appendChild(wr); return i;
  }
  function ocrForm(){
    app.innerHTML=topbar("➕ Nové ošetřovné", true);
    var w=el('<div style="padding:6px;display:flex;flex-direction:column;gap:12px;"></div>'); app.appendChild(w);
    var fId=_ocrFld(w,"Identifikátor ČSSZ (ze SMS)","např. 10251643250619001N","Najdeš ve zprávě od ČSSZ s odkazem na eportal.cssz.cz.");
    var fOs=_ocrFld(w,"Ošetřovaná osoba (jméno)","Jméno a příjmení");
    var fRc=_ocrFld(w,"Rodné číslo ošetřované osoby","RRMMDD/XXXX");
    var fVz=_ocrFld(w,"Vztah","dítě / rodič / …");
    var fOd=_ocrFld(w,"Datum od","DD.MM.RRRR");
    var st=el('<div class="hint" style="min-height:16px;"></div>'); w.appendChild(st);
    var sv=el('<button style="'+_OCR_BTN+'">Založit OČR</button>'); w.appendChild(sv);
    var cx=el('<button class="ghost sm" style="margin-top:4px;">Zrušit</button>'); cx.addEventListener("click",function(){ ocr(); }); w.appendChild(cx);
    sv.addEventListener("click",function(){
      var osoba=(fOs.value||"").trim(); if(!osoba){ st.style.color="#ff8b8b"; st.textContent="Vyplň ošetřovanou osobu."; return; }
      var od=_isoDate(fOd.value); if(!/^\d{4}-\d{2}-\d{2}/.test(od)){ st.style.color="#ff8b8b"; st.textContent="Datum od ve formátu DD.MM.RRRR."; return; }
      var rc=(fRc.value||"").trim(); if(rc && !_rcValid(rc)){ st.style.color="#ff8b8b"; st.textContent="RČ nevypadá platně."; return; }
      sv.disabled=true; st.style.color="#9fb2d4"; st.textContent="Ukládám…";
      api("POST","/api/v1/erp/app/ocr/start",{identifikator:(fId.value||"").trim(),osoba_jmeno:osoba,osoba_rc:rc,osoba_vztah:(fVz.value||"").trim(),od:od}).then(function(r){
        if(r&&r.ok){ ocr(); } else { sv.disabled=false; st.style.color="#ff8b8b"; st.textContent="Chyba: "+((r&&r.error)||"?"); }
      });
    });
  }
  function ocrEndForm(c){
    app.innerHTML=topbar("Ukončit OČR", true);
    var w=el('<div style="padding:6px;display:flex;flex-direction:column;gap:12px;"></div>'); app.appendChild(w);
    w.appendChild(el('<div class="hint" style="line-height:1.6;">Péče o: <b>'+esc(c.osoba||"")+'</b>, od '+_czDate(c.od)+'. Doplň datum konce a počet dní, kdy ses staral(a).</div>'));
    var fDo=_ocrFld(w,"Datum do","DD.MM.RRRR");
    var fDny=_ocrFld(w,"Počet dní ošetřování","např. 6");
    var st=el('<div class="hint" style="min-height:16px;"></div>'); w.appendChild(st);
    var sv=el('<button style="'+_OCR_BTN+'">Poslat ke schválení</button>'); w.appendChild(sv);
    var cx=el('<button class="ghost sm" style="margin-top:4px;">Zrušit</button>'); cx.addEventListener("click",function(){ ocr(); }); w.appendChild(cx);
    sv.addEventListener("click",function(){
      var dd=_isoDate(fDo.value); if(!/^\d{4}-\d{2}-\d{2}/.test(dd)){ st.style.color="#ff8b8b"; st.textContent="Datum do ve formátu DD.MM.RRRR."; return; }
      var dny=parseInt((fDny.value||"0").replace(/\D/g,""),10)||0;
      sv.disabled=true; st.style.color="#9fb2d4"; st.textContent="Odesílám…";
      api("POST","/api/v1/erp/app/ocr/end",{id:c.id,"do":dd,dny:dny}).then(function(r){
        if(r&&r.ok){ ocr(); } else { sv.disabled=false; st.style.color="#ff8b8b"; st.textContent="Chyba: "+((r&&r.error)||"?"); }
      });
    });
  }
  // ── OČR formulář (ČSSZ §109) — předvyplněný, ukládá do att_ocr_form ──────
  function _ocrSec(title){ return el('<div style="margin-top:14px;font-weight:800;color:#9fd0ff;border-bottom:1px solid #24324f;padding-bottom:4px;">'+esc(title)+'</div>'); }
  function _ocrArea(parent,label,ph,val){
    var wr=el('<div></div>'); wr.appendChild(el('<div style="font-size:13px;color:#cdd6e2;margin-bottom:4px;">'+esc(label)+'</div>'));
    var t=el('<textarea rows="3" placeholder="'+esc(ph||"")+'" style="width:100%;box-sizing:border-box;padding:10px;border-radius:10px;border:1px solid #2b3a5c;background:#0a1226;color:#e8eefc;"></textarea>');
    t.value=val||""; wr.appendChild(t); parent.appendChild(wr); return t;
  }
  function _ocrRadio(parent,label,opts,val){
    var grp="ocrR"+Math.floor(Math.random()*1e9);  // společný name → vzájemně se vylučují
    var wr=el('<div></div>'); wr.appendChild(el('<div style="font-size:13px;color:#cdd6e2;margin-bottom:4px;">'+esc(label)+'</div>'));
    var box=el('<div style="display:flex;flex-direction:column;gap:4px;"></div>'); var cur={v:val};
    opts.forEach(function(o){
      var row=el('<label style="display:flex;align-items:center;gap:8px;font-size:14px;color:#e8eefc;cursor:pointer;"></label>');
      var r=el('<input type="radio" name="'+grp+'" style="accent-color:#34d399;width:16px;height:16px;">'); if(o.v===val)r.checked=true;
      r.addEventListener("change",function(){ cur.v=o.v; });
      row.appendChild(r); row.appendChild(el('<span>'+esc(o.t)+'</span>')); box.appendChild(row);
    });
    wr.appendChild(box); parent.appendChild(wr); return { get:function(){ return cur.v; } };
  }
  function _ocrYesNo(parent,label,val){ return _ocrRadio(parent,label,[{v:"ano",t:"Ano"},{v:"ne",t:"Ne"}],(val==="ano"?"ano":"ne")); }
  function _apiForm(path, fd){
    return fetch(path,{method:"POST",credentials:"same-origin",body:fd}).then(function(r){ return r.text(); }).then(function(t){ try{ return t?JSON.parse(t):null; }catch(e){ return null; } }).catch(function(){ return null; });
  }
  function _rcToBirth(rc){
    rc=(rc||"").replace(/[\s\/]/g,""); if(!/^\d{9,10}$/.test(rc)) return "";
    var yy=parseInt(rc.slice(0,2),10), mm=parseInt(rc.slice(2,4),10), dd=parseInt(rc.slice(4,6),10);
    if(mm>70)mm-=70; else if(mm>50)mm-=50; else if(mm>20)mm-=20;
    var full=(rc.length===10)?((yy<54?2000:1900)+yy):(1900+yy);
    if(full>(new Date().getFullYear()))full-=100;
    if(mm<1||mm>12||dd<1||dd>31)return "";
    return full+"-"+("0"+mm).slice(-2)+"-"+("0"+dd).slice(-2);
  }
  function _ocrLoadFiles(box, caseId, canDel){
    box.innerHTML='<div class="hint">Načítám přílohy…</div>';
    api("GET","/api/v1/erp/app/ocr/files?case="+caseId,"").then(function(j){
      box.innerHTML="";
      if(!j||!j.ok){ box.appendChild(el('<div class="hint">Přílohy se nepodařilo načíst.</div>')); return; }
      var fs=j.files||[];
      if(!fs.length){ box.appendChild(el('<div class="hint">Zatím žádné přílohy.</div>')); return; }
      fs.forEach(function(f){
        var r=el('<div style="display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid #1c2740;"></div>');
        var icon=(f.kind==="excel")?"📊":"📄";
        r.appendChild(el('<div style="flex:1;font-size:14px;"><a href="/api/v1/erp/app/ocr/file-view?fid='+f.id+'" target="_blank" rel="noopener" style="color:#9fd0ff;text-decoration:none;">'+icon+' '+esc(f.filename||("dokument "+f.document_id))+'</a> <span class="hint">'+esc(f.created||"")+'</span></div>'));
        if(canDel){
          var x=el('<button style="background:#3a1d28;border:0;color:#f9b;border-radius:8px;padding:5px 9px;cursor:pointer;">🗑</button>');
          x.addEventListener("click",function(){ if(!confirm("Smazat přílohu?"))return; api("POST","/api/v1/erp/app/ocr/file/delete",{id:f.id}).then(function(rr){ if(rr&&rr.ok)_ocrLoadFiles(box,caseId,canDel); else alert("Chyba: "+((rr&&rr.error)||"?")); }); });
          r.appendChild(x);
        }
        box.appendChild(r);
      });
    });
  }
  function ocrVyplnit(caseId){
    app.innerHTML=topbar("📋 Formulář ošetřovného", true);
    var w=el('<div style="padding:6px;display:flex;flex-direction:column;gap:10px;"></div>'); app.appendChild(w);
    w.appendChild(el('<div class="hint">Načítám…</div>'));
    api("GET","/api/v1/erp/app/ocr/form?case="+caseId,"").then(function(j){
      w.innerHTML="";
      if(!j||!j.ok){ w.appendChild(el('<div class="hint">'+esc((j&&j.error)||"Nepodařilo se načíst.")+'</div>')); var bk=el('<button class="ghost sm">Zpět</button>'); bk.addEventListener("click",function(){ocr();}); w.appendChild(bk); return; }
      var d=j.data||{}; var canMng=!!j.can_manage;
      w.appendChild(el('<div class="hint" style="line-height:1.6;">Formulář ČSSZ „Oznámení zaměstnavateli o potřebě ošetřování" (§109). Předvyplnili jsme, co víme — doplň zbytek a ulož. Rodné číslo jde jen do formuláře, nikdy ne SMS.</div>'));
      function _ocrLinkBtn(url,label){ return el('<div style="margin:2px 0 4px;padding:8px 10px;border-radius:10px;background:rgba(159,208,255,.08);border:1px solid #2b3a5c;"><a href="'+esc(url)+'" target="_blank" rel="noopener" style="color:#9fd0ff;font-weight:700;font-size:14px;text-decoration:none;">'+esc(label)+'</a></div>'); }
      var _ocrLnk=j.cssz_link||j.cssz_link_konec; if(_ocrLnk){ w.appendChild(_ocrLinkBtn(_ocrLnk,"📄 Stáhnout doklad z ČSSZ ePortálu")); }
      w.appendChild(_ocrSec("Zaměstnanec"));
      var fZj=_ocrFld(w,"Jméno",""); fZj.value=d.zam_jmeno||"";
      var fZp=_ocrFld(w,"Příjmení",""); fZp.value=d.zam_prijmeni||"";
      var fZr=_ocrFld(w,"Rodné číslo zaměstnance","RRMMDD/XXXX"); fZr.value=d.zam_rc||"";
      w.appendChild(_ocrSec("Ošetřovaná osoba"));
      var fOj=_ocrFld(w,"Jméno a příjmení",""); fOj.value=d.os_jmeno||"";
      var fOr=_ocrFld(w,"Rodné číslo ošetřované osoby","RRMMDD/XXXX"); fOr.value=d.os_rc||"";
      var fOv=_ocrFld(w,"Vztah k zaměstnanci","dítě / rodič / manžel…"); fOv.value=d.os_vztah||"";
      var sc=el('<button class="ghost sm" style="margin-top:2px;">👨‍👩‍👧 Uložit dítě do karty</button>');
      sc.addEventListener("click",function(){
        var nm=(fOj.value||"").trim(), rc=(fOr.value||"").trim(), rel=(fOv.value||"").trim();
        if(!nm){ alert("Vyplň jméno ošetřované osoby."); return; }
        if(rc && !_rcValid(rc)){ alert("RČ nevypadá platně."); return; }
        sc.disabled=true; sc.textContent="Ukládám…";
        api("POST","/api/v1/erp/app/self-child/save",{child_name:nm,birth_number:rc,relation:rel||"dítě",birth_date:_rcToBirth(rc)}).then(function(r){
          sc.disabled=false;
          if(r&&r.ok){ sc.textContent="✓ Uloženo do karty"; } else { sc.textContent="👨‍👩‍👧 Uložit dítě do karty"; alert("Chyba: "+((r&&r.error)||"?")); }
        });
      }); w.appendChild(sc);
      w.appendChild(_ocrSec("Rozhodnutí a období"));
      var fCr=_ocrFld(w,"Číslo rozhodnutí / identifikátor ČSSZ",""); fCr.value=d.cislo_rozhodnuti||"";
      var fDod=_ocrFld(w,"Datum od","DD.MM.RRRR"); fDod.value=_czDate(d.datum_od)||"";
      var fDdo=_ocrFld(w,"Datum do","DD.MM.RRRR"); fDdo.value=_czDate(d.datum_do)||"";
      var duvod=_ocrRadio(w,"Důvod ošetřování",[
        {v:"osetrovani_nemocne",t:"Ošetřování nemocného člena domácnosti"},
        {v:"karantena_dite",t:"Dítě v karanténě / izolaci"},
        {v:"zarizeni_uzavreno",t:"Uzavření školy / dětského zařízení"},
        {v:"osoba_onemocnela",t:"Onemocněla osoba, která jinak o dítě pečuje"}
      ], d.duvod||"osetrovani_nemocne");
      w.appendChild(_ocrSec("Podmínky nároku"));
      var spol=_ocrYesNo(w,"Žije ošetřovaná osoba s vámi ve společné domácnosti?", d.spolecna_domacnost||"ano");
      var osam=_ocrYesNo(w,"Jste osamělý/á zaměstnanec/kyně?", d.osamely_zamestnanec||"ne");
      var jina=_ocrYesNo(w,"Je v domácnosti jiná osoba, která může pečovat (pobírá PPM / rodičovský příspěvek)?", d.jina_osoba_ppm||"ne");
      var jinaNem=_ocrYesNo(w,"…a tato osoba onemocněla / nemůže pečovat?", d.jina_osoba_onemocnela||"ne");
      var ppm=_ocrYesNo(w,"Pobíráte vy peněžitou pomoc v mateřství (PPM)?", d.pobira_ppm||"ne");
      w.appendChild(_ocrSec("Žádost a poskytování péče"));
      var obd=_ocrRadio(w,"Žádám o ošetřovné za",[
        {v:"cela_doba",t:"Celou dobu ošetřování"},
        {v:"v_dnech",t:"Jen vybrané dny (od–do)"}
      ], d.obdobi_zadosti||"cela_doba");
      var fObOd=_ocrFld(w,"— období od (jen u vybraných dnů)","DD.MM.RRRR"); fObOd.value=_czDate(d.obdobi_od)||"";
      var fObDo=_ocrFld(w,"— období do","DD.MM.RRRR"); fObDo.value=_czDate(d.obdobi_do)||"";
      var posk=_ocrRadio(w,"Ošetřování jsem poskytoval(a)",[
        {v:"cela_doba",t:"Po celou dobu"},
        {v:"v_dnech",t:"Jen ve vybrané dny (od–do)"}
      ], d.osetrovani_poskytl||"cela_doba");
      var fPoOd=_ocrFld(w,"— poskytl od","DD.MM.RRRR"); fPoOd.value=_czDate(d.poskytl_od)||"";
      var fPoDo=_ocrFld(w,"— poskytl do","DD.MM.RRRR"); fPoDo.value=_czDate(d.poskytl_do)||"";
      w.appendChild(_ocrSec("Doplňující"));
      var area=_ocrArea(w,"Sdělení zaměstnance (nepovinné)","Cokoli pro účetní / úřad…", d.sdeleni||"");
      var fKont=_ocrFld(w,"Kontakt — telefon / e-mail (nepovinné)",""); fKont.value=d.kontakt||"";
      w.appendChild(_ocrSec("Přílohy (PDF / sken z ČSSZ)"));
      var filesBox=el('<div></div>'); w.appendChild(filesBox); _ocrLoadFiles(filesBox, caseId, canMng);
      var upBtn=el('<button class="ghost sm" style="margin-top:6px;">⬆️ Nahrát přílohu (PDF / foto)</button>');
      upBtn.addEventListener("click",function(){
        var fi=el('<input type="file" accept="application/pdf,image/*" style="display:none;">'); document.body.appendChild(fi);
        fi.addEventListener("change",function(){
          var f=fi.files&&fi.files[0]; if(!f){ try{fi.remove();}catch(e){} return; }
          if(f.size>25*1024*1024){ alert("Soubor je moc velký (max 25 MB)."); try{fi.remove();}catch(e){} return; }
          var fr=new FileReader();
          fr.onload=function(){
            var b64=String(fr.result).split(",")[1]||"";
            var fn=f.name||"priloha.pdf";
            upBtn.disabled=true; upBtn.textContent="Nahrávám…";
            api("POST","/api/v1/erp/app/ocr/file",{case:caseId,kind:"priloha",filename:fn,file_b64:b64}).then(function(r){
              upBtn.disabled=false; upBtn.textContent="⬆️ Nahrát přílohu (PDF / foto)";
              try{fi.remove();}catch(e){}
              _ocrLoadFiles(filesBox, caseId, canMng);
              if(!(r&&r.ok)){ alert("Chyba: "+((r&&r.error)||"nahrání selhalo")); }
            });
          };
          fr.readAsDataURL(f);
        });
        fi.click();
      }); if(canMng) w.appendChild(upBtn);
      var st=el('<div class="hint" style="min-height:16px;margin-top:8px;"></div>'); w.appendChild(st);
      function collect(){
        return {
          zam_jmeno:(fZj.value||"").trim(), zam_prijmeni:(fZp.value||"").trim(), zam_rc:(fZr.value||"").trim(),
          os_jmeno:(fOj.value||"").trim(), os_rc:(fOr.value||"").trim(), os_vztah:(fOv.value||"").trim(),
          cislo_rozhodnuti:(fCr.value||"").trim(), datum_od:_isoDate(fDod.value), datum_do:_isoDate(fDdo.value),
          duvod:duvod.get(), spolecna_domacnost:spol.get(), osamely_zamestnanec:osam.get(),
          jina_osoba_ppm:jina.get(), jina_osoba_onemocnela:jinaNem.get(), pobira_ppm:ppm.get(),
          obdobi_zadosti:obd.get(), obdobi_od:_isoDate(fObOd.value), obdobi_do:_isoDate(fObDo.value),
          osetrovani_poskytl:posk.get(), poskytl_od:_isoDate(fPoOd.value), poskytl_do:_isoDate(fPoDo.value),
          sdeleni:(area.value||"").trim(), kontakt:(fKont.value||"").trim()
        };
      }
      function doSave(stav){
        if(fOr.value && !_rcValid(fOr.value)){ st.style.color="#ff8b8b"; st.textContent="RČ ošetřované osoby nevypadá platně."; return; }
        st.style.color="#9fb2d4"; st.textContent="Ukládám…";
        api("POST","/api/v1/erp/app/ocr/form/save",{case:caseId,data:collect(),stav:stav}).then(function(r){
          if(r&&r.ok){ st.style.color="#5ee0b7"; st.textContent=(stav==="kompletni"?"✓ Uloženo jako kompletní":"✓ Uloženo"); }
          else { st.style.color="#ff8b8b"; st.textContent="Chyba: "+((r&&r.error)||"?"); }
        });
      }
      var sv=el('<button style="'+_OCR_BTN+'">💾 Uložit formulář</button>'); sv.addEventListener("click",function(){ doSave("rozpracovany"); }); w.appendChild(sv);
      var done=el('<button style="margin-top:6px;padding:11px;border-radius:12px;border:1px solid #34d399;background:rgba(52,211,153,.15);color:#5ee0b7;font-weight:800;width:100%;cursor:pointer;">✓ Označit jako kompletní</button>'); done.addEventListener("click",function(){ doSave("kompletni"); }); if(canMng) w.appendChild(done);
      var gx=el('<button style="margin-top:6px;padding:11px;border-radius:12px;border:1px solid #6aa9ff;background:rgba(106,169,255,.12);color:#9fd0ff;font-weight:800;width:100%;cursor:pointer;">📊 Vygenerovat ČSSZ Excel</button>');
      gx.addEventListener("click",function(){
        if(fOr.value && !_rcValid(fOr.value)){ st.style.color="#ff8b8b"; st.textContent="RČ ošetřované osoby nevypadá platně."; return; }
        gx.disabled=true; st.style.color="#9fb2d4"; st.textContent="Ukládám a generuji Excel…";
        api("POST","/api/v1/erp/app/ocr/form/save",{case:caseId,data:collect(),stav:"kompletni"}).then(function(r){
          if(!r||!r.ok){ gx.disabled=false; st.style.color="#ff8b8b"; st.textContent="Uložení selhalo: "+((r&&r.error)||"?"); return; }
          api("POST","/api/v1/erp/app/ocr/excel",{case:caseId}).then(function(e){
            gx.disabled=false;
            _ocrLoadFiles(filesBox, caseId, canMng);
            if(e&&e.ok){ st.style.color="#5ee0b7"; st.textContent="✓ Excel vygenerován: "+esc(e.filename||""); }
            else { st.style.color="#ff8b8b"; st.textContent="Generování selhalo: "+((e&&e.error)||"?"); }
          });
        });
      }); if(canMng) w.appendChild(gx);
      var mb=el('<button style="margin-top:6px;padding:11px;border-radius:12px;border:1px solid #f0b35e;background:rgba(240,179,94,.12);color:#f6c98a;font-weight:800;width:100%;cursor:pointer;">📧 Odeslat účetní</button>');
      mb.addEventListener("click",function(){
        if(!confirm("Odeslat formulář a přílohy e-mailem účetní (Petra Fajmonová, fajmonova@martia2000.cz), kopie Péťa (p.safrankova@eurosoft.com)?\n\nExcel se před odesláním vygeneruje z aktuálních dat."))return;
        mb.disabled=true; st.style.color="#9fb2d4"; st.textContent="Ukládám, generuji a odesílám…";
        api("POST","/api/v1/erp/app/ocr/form/save",{case:caseId,data:collect(),stav:"kompletni"}).then(function(r){
          if(!r||!r.ok){ mb.disabled=false; st.style.color="#ff8b8b"; st.textContent="Uložení selhalo: "+((r&&r.error)||"?"); return; }
          api("POST","/api/v1/erp/app/ocr/excel",{case:caseId}).then(function(e){
            if(!e||!e.ok){ mb.disabled=false; st.style.color="#ff8b8b"; st.textContent="Excel selhal: "+((e&&e.error)||"?"); return; }
            api("POST","/api/v1/erp/app/ocr/mail",{case:caseId}).then(function(m){
              mb.disabled=false;
              if(m&&m.ok){ st.style.color="#5ee0b7"; st.textContent="✓ Odesláno účetní ("+(m.attachments||0)+" příloh), kopie Péťa."; _ocrLoadFiles(filesBox, caseId, canMng); }
              else if(m&&m.error==="forbidden"){ st.style.color="#ff8b8b"; st.textContent="Odeslání může spustit jen HR/účetní."; }
              else { st.style.color="#ff8b8b"; st.textContent="Odeslání selhalo: "+((m&&m.error)||"?"); }
            });
          });
        });
      }); if(canMng) w.appendChild(mb);
      var cx=el('<button class="ghost sm" style="margin-top:4px;">Zpět na seznam OČR</button>'); cx.addEventListener("click",function(){ ocr(); }); w.appendChild(cx);
    });
  }
  function ocr_schval(){
    app.innerHTML=topbar("🧑‍⚕️ OČR — schvalování", true);
    var box=el('<div class="list"><div class="hint">Načítám…</div></div>'); app.appendChild(box);
    api("GET","/api/v1/erp/app/ocr/inbox","").then(function(j){
      box.innerHTML="";
      if(!j||!j.ok){ box.innerHTML='<div class="hint">'+((j&&j.error==="forbidden")?"🔒 Jen rodiče a HR.":"Nepodařilo se načíst.")+'</div>'; return; }
      var cs=j.cases||[];
      if(!cs.length){ box.innerHTML='<div class="hint">Nic ke schválení.</div>'; return; }
      cs.forEach(function(c){
        var rw=el('<div style="padding:10px 6px;border-bottom:1px solid var(--bord);"></div>');
        rw.appendChild(el('<div style="font-weight:600;">'+esc(c.zamestnanec||"")+'</div>'));
        rw.appendChild(el('<div class="hint">péče o: '+esc(c.osoba||"")+(c.vztah?(' ('+esc(c.vztah)+')'):'')+' · '+_czDate(c.od)+(c.do?(' – '+_czDate(c.do)):'')+(c.dny?(' · '+c.dny+' dní'):'')+(c.company?(' · '+esc(c.company)):'')+(c.identifikator?(' · id '+esc(c.identifikator)):'')+'</div>'));
        var _cl=c.link||c.link_konec; if(_cl){ rw.appendChild(el('<div style="margin-top:4px;"><a href="'+esc(_cl)+'" target="_blank" rel="noopener" style="color:#9fd0ff;font-size:13px;font-weight:600;">📄 Stáhnout doklad z ČSSZ ePortálu</a></div>')); }
        if(c.stav==="ukonceno"){
          var b=el('<button style="margin-top:6px;padding:8px 14px;border-radius:10px;border:1px solid #34d399;background:rgba(52,211,153,.15);color:#5ee0b7;font-weight:700;cursor:pointer;">✓ Schválit</button>');
          b.addEventListener("click",function(){ if(!confirm("Schválit OČR pro "+(c.zamestnanec||"")+"?"))return; b.disabled=true; b.textContent="…"; api("POST","/api/v1/erp/app/ocr/approve",{id:c.id}).then(function(r){ if(r&&r.ok){ ocr_schval(); } else { b.disabled=false; b.textContent="✓ Schválit"; alert("Chyba: "+((r&&r.error)||"?")); } }); });
          rw.appendChild(b);
        } else { rw.appendChild(el('<div class="hint" style="margin-top:4px;">probíhá (čeká na ukončení zaměstnancem)</div>')); }
        box.appendChild(rw);
      });
    });
  }
  // ── eNeschopenka (nemocenská) — Fáze 1 (mirror OČR) ────────────────────
  function sick(){
    app.innerHTML=topbar("🤒 Nemocenská", true);
    app.appendChild(el('<div class="hint" style="margin:8px 6px;line-height:1.6;">Nahlas nemoc (eNeschopenku). Pokud máš číslo rozhodnutí o DPN, zadej ho — jinak stačí datum od. Po uzdravení doplníš konec, vedoucí/HR schválí. (Brzy budeme údaje z ČSSZ tahat automaticky.)</div>'));
    var nb=el('<button style="'+_OCR_BTN+'">➕ Nahlásit nemoc</button>'); nb.addEventListener("click",function(){ sickForm(); }); app.appendChild(nb);
    var box=el('<div class="list" style="margin-top:10px;"><div class="hint">Načítám…</div></div>'); app.appendChild(box);
    api("GET","/api/v1/erp/app/sick/mine","").then(function(j){
      box.innerHTML="";
      if(!j||!j.ok){ box.innerHTML='<div class="hint">Nepodařilo se načíst.</div>'; return; }
      var cs=j.cases||[];
      if(!cs.length){ box.innerHTML='<div class="hint">Zatím žádná nemocenská.</div>'; return; }
      cs.forEach(function(c){
        var lbl={novy:"probíhá",trva:"probíhá",ukonceno:"ke schválení",schvaleno:"schváleno"}[c.stav]||c.stav;
        var konec=c.do?(" – "+_czDate(c.do)):(c.predpoklad_do?(" – předpoklad "+_czDate(c.predpoklad_do)):"");
        var rw=el('<div style="padding:10px 6px;border-bottom:1px solid var(--bord);"></div>');
        rw.appendChild(el('<div style="font-weight:600;">Nemocenská'+(c.cislo_dpn?(' · DPN '+esc(c.cislo_dpn)):'')+'</div>'));
        rw.appendChild(el('<div class="hint">'+_czDate(c.od)+konec+' · '+esc(lbl)+(c.company?(' · '+esc(c.company)):'')+'</div>'));
        if(c.stav==="novy"||c.stav==="trva"){
          var eb=el('<button style="margin-top:6px;padding:8px 12px;border-radius:10px;border:1px solid var(--bord);background:rgba(255,255,255,.04);color:var(--tx);font-weight:700;cursor:pointer;">Ukončit a poslat ke schválení</button>');
          eb.addEventListener("click",function(){ sickEndForm(c); }); rw.appendChild(eb);
        }
        box.appendChild(rw);
      });
    });
  }
  function sickForm(){
    app.innerHTML=topbar("➕ Nahlásit nemoc", true);
    var w=el('<div style="padding:6px;display:flex;flex-direction:column;gap:12px;"></div>'); app.appendChild(w);
    var fC=_ocrFld(w,"Číslo rozhodnutí o DPN (pokud máš)","nepovinné","Z eNeschopenky / od ČSSZ. Nemáš-li, nech prázdné.");
    var fOd=_ocrFld(w,"Nemocný od","DD.MM.RRRR");
    var fPd=_ocrFld(w,"Předpokládaný konec (pokud víš)","DD.MM.RRRR — nepovinné");
    var st=el('<div class="hint" style="min-height:16px;"></div>'); w.appendChild(st);
    var sv=el('<button style="'+_OCR_BTN+'">Nahlásit</button>'); w.appendChild(sv);
    var cx=el('<button class="ghost sm" style="margin-top:4px;">Zrušit</button>'); cx.addEventListener("click",function(){ sick(); }); w.appendChild(cx);
    sv.addEventListener("click",function(){
      var od=_isoDate(fOd.value); if(!/^\d{4}-\d{2}-\d{2}/.test(od)){ st.style.color="#ff8b8b"; st.textContent="Datum od ve formátu DD.MM.RRRR."; return; }
      var pd=(fPd.value||"").trim()?_isoDate(fPd.value):""; if(pd && !/^\d{4}-\d{2}-\d{2}/.test(pd)){ st.style.color="#ff8b8b"; st.textContent="Předpokládaný konec ve formátu DD.MM.RRRR."; return; }
      sv.disabled=true; st.style.color="#9fb2d4"; st.textContent="Odesílám…";
      api("POST","/api/v1/erp/app/sick/start",{cislo_dpn:(fC.value||"").trim(),od:od,predpoklad_do:pd}).then(function(r){
        if(r&&r.ok){ sick(); } else { sv.disabled=false; st.style.color="#ff8b8b"; st.textContent="Chyba: "+((r&&r.error)||"?"); }
      });
    });
  }
  function sickEndForm(c){
    app.innerHTML=topbar("Ukončit nemocenskou", true);
    var w=el('<div style="padding:6px;display:flex;flex-direction:column;gap:12px;"></div>'); app.appendChild(w);
    w.appendChild(el('<div class="hint" style="line-height:1.6;">Nemocný od '+_czDate(c.od)+'. Doplň datum konce nemocenské.</div>'));
    var fDo=_ocrFld(w,"Datum do","DD.MM.RRRR");
    var st=el('<div class="hint" style="min-height:16px;"></div>'); w.appendChild(st);
    var sv=el('<button style="'+_OCR_BTN+'">Poslat ke schválení</button>'); w.appendChild(sv);
    var cx=el('<button class="ghost sm" style="margin-top:4px;">Zrušit</button>'); cx.addEventListener("click",function(){ sick(); }); w.appendChild(cx);
    sv.addEventListener("click",function(){
      var dd=_isoDate(fDo.value); if(!/^\d{4}-\d{2}-\d{2}/.test(dd)){ st.style.color="#ff8b8b"; st.textContent="Datum do ve formátu DD.MM.RRRR."; return; }
      sv.disabled=true; st.style.color="#9fb2d4"; st.textContent="Odesílám…";
      api("POST","/api/v1/erp/app/sick/end",{id:c.id,"do":dd}).then(function(r){
        if(r&&r.ok){ sick(); } else { sv.disabled=false; st.style.color="#ff8b8b"; st.textContent="Chyba: "+((r&&r.error)||"?"); }
      });
    });
  }
  function sick_schval(){
    app.innerHTML=topbar("🤒 Nemocenská — schvalování", true);
    var box=el('<div class="list"><div class="hint">Načítám…</div></div>'); app.appendChild(box);
    api("GET","/api/v1/erp/app/sick/inbox","").then(function(j){
      box.innerHTML="";
      if(!j||!j.ok){ box.innerHTML='<div class="hint">'+((j&&j.error==="forbidden")?"🔒 Jen rodiče a HR.":"Nepodařilo se načíst.")+'</div>'; return; }
      var cs=j.cases||[];
      if(!cs.length){ box.innerHTML='<div class="hint">Nic ke schválení.</div>'; return; }
      cs.forEach(function(c){
        var rw=el('<div style="padding:10px 6px;border-bottom:1px solid var(--bord);"></div>');
        rw.appendChild(el('<div style="font-weight:600;">'+esc(c.zamestnanec||"")+'</div>'));
        var konec=c.do?(" – "+_czDate(c.do)):(c.predpoklad_do?(" – předpoklad "+_czDate(c.predpoklad_do)):"");
        rw.appendChild(el('<div class="hint">nemoc '+_czDate(c.od)+konec+(c.company?(' · '+esc(c.company)):'')+(c.cislo_dpn?(' · DPN '+esc(c.cislo_dpn)):'')+'</div>'));
        if(c.stav==="ukonceno"){
          var b=el('<button style="margin-top:6px;padding:8px 14px;border-radius:10px;border:1px solid #34d399;background:rgba(52,211,153,.15);color:#5ee0b7;font-weight:700;cursor:pointer;">✓ Schválit</button>');
          b.addEventListener("click",function(){ if(!confirm("Schválit nemocenskou pro "+(c.zamestnanec||"")+"?"))return; b.disabled=true; b.textContent="…"; api("POST","/api/v1/erp/app/sick/approve",{id:c.id}).then(function(r){ if(r&&r.ok){ sick_schval(); } else { b.disabled=false; b.textContent="✓ Schválit"; alert("Chyba: "+((r&&r.error)||"?")); } }); });
          rw.appendChild(b);
        } else { rw.appendChild(el('<div class="hint" style="margin-top:4px;">probíhá (čeká na ukončení)</div>')); }
        box.appendChild(rw);
      });
    });
  }
  function np_prehled(){
    app.innerHTML=topbar("📋 Nemoc a OČR — přehled", true);
    var bar=el('<div style="display:flex;gap:8px;margin:8px 6px;"></div>');
    var _act=true;
    var bAll=el('<button style="flex:1;padding:8px;border-radius:10px;cursor:pointer;"></button>');
    var bAct=el('<button style="flex:1;padding:8px;border-radius:10px;cursor:pointer;"></button>');
    bar.appendChild(bAct); bar.appendChild(bAll); app.appendChild(bar);
    var box=el('<div class="list"><div class="hint">Načítám…</div></div>'); app.appendChild(box);
    function paint(){
      bAct.style.cssText="flex:1;padding:8px;border-radius:10px;cursor:pointer;border:1px solid "+(_act?"var(--green)":"var(--bord)")+";background:"+(_act?"var(--green)":"rgba(255,255,255,.03)")+";color:"+(_act?"#04150e":"var(--mut)")+";font-weight:700;";
      bAll.style.cssText="flex:1;padding:8px;border-radius:10px;cursor:pointer;border:1px solid "+(!_act?"var(--green)":"var(--bord)")+";background:"+(!_act?"var(--green)":"rgba(255,255,255,.03)")+";color:"+(!_act?"#04150e":"var(--mut)")+";font-weight:700;";
      bAct.textContent="Probíhající"; bAll.textContent="Vše (i historie)";
    }
    function load(){
      paint(); box.innerHTML='<div class="hint">Načítám…</div>';
      api("GET","/api/v1/erp/app/hr/np-overview"+(_act?"?active=1":""),"").then(function(j){
        box.innerHTML="";
        if(!j||!j.ok){ box.innerHTML='<div class="hint">'+((j&&j.error==="forbidden")?"🔒 Jen rodiče a HR.":"Nepodařilo se načíst.")+'</div>'; return; }
        var it=j.items||[];
        if(!it.length){ box.innerHTML='<div class="hint">'+(_act?"Nikdo právě teď.":"Žádné záznamy.")+'</div>'; return; }
        var lblS={novy:"probíhá",trva:"probíhá",ukonceno:"ke schválení",schvaleno:"schváleno"};
        it.forEach(function(c){
          var ic=(c.kind==="ocr")?"🧑‍⚕️":"🤒"; var kindTxt=(c.kind==="ocr")?("OČR"+(c.osoba?(" · "+c.osoba):"")):"Nemocenská";
          var rw=el('<div style="display:flex;gap:10px;padding:9px 6px;border-bottom:1px solid var(--bord);"></div>');
          rw.appendChild(el('<div style="font-size:20px;">'+ic+'</div>'));
          rw.appendChild(el('<div style="flex:1;min-width:0;"><div style="font-weight:600;">'+esc(c.zamestnanec||"")+'</div><div class="hint">'+esc(kindTxt)+' · '+_czDate(c.od)+(c.do?(" – "+_czDate(c.do)):"")+(c.company?(" · "+esc(c.company)):"")+' · '+esc(lblS[c.stav]||c.stav)+'</div></div>'));
          box.appendChild(rw);
        });
      });
    }
    bAct.addEventListener("click",function(){ _act=true; load(); });
    bAll.addEventListener("click",function(){ _act=false; load(); });
    load();
  }
  // ── Lísteček od lékaře ─────────────────────────────────────────────────
  var _MED_TYP={vyset:"Vyšetření / ošetření",prevent:"Preventivní prohlídka",doprovod:"Doprovod"};
  function _krytiTxt(k){ return {sick_day:"sick day",listecek:"lísteček",kombinace:"sick day + lísteček"}[k]||k; }
  function med(){
    app.innerHTML=topbar("🩺 Lísteček od lékaře", true);
    var info=el('<div class="hint" style="margin:8px 6px;line-height:1.6;">Po návštěvě lékaře vyfoť lísteček a vyplň čas. Nejdřív se čerpá sick day (po hodinách), po jeho vyčerpání proplácíme lísteček do limitu.</div>');
    app.appendChild(info);
    var balBox=el('<div class="hint" style="margin:0 6px 6px;">Načítám zůstatek…</div>'); app.appendChild(balBox);
    var nb=el('<button style="'+_OCR_BTN+'">➕ Nová návštěva u lékaře</button>'); nb.addEventListener("click",function(){ medForm(); }); app.appendChild(nb);
    var box=el('<div class="list" style="margin-top:10px;"><div class="hint">Načítám…</div></div>'); app.appendChild(box);
    api("GET","/api/v1/erp/app/med/mine","").then(function(j){
      box.innerHTML="";
      if(!j||!j.ok){ box.innerHTML='<div class="hint">Nepodařilo se načíst.</div>'; return; }
      if(j.balance){ balBox.innerHTML='Zůstatek sick day: <b>'+j.balance.remaining_h+' h</b> (z '+j.balance.entitlement_h+' h/rok) · lísteček do <b>'+(j.limit_h||4)+' h</b>'; }
      var cs=j.cases||[];
      if(!cs.length){ box.innerHTML='<div class="hint">Zatím žádné lístečky.</div>'; return; }
      cs.forEach(function(c){
        var lbl={nahlaseno:"ke schválení",schvaleno:"schváleno",zamitnuto:"zamítnuto"}[c.stav]||c.stav;
        var rw=el('<div style="padding:10px 6px;border-bottom:1px solid var(--bord);"></div>');
        rw.appendChild(el('<div style="font-weight:600;">'+_czDate(c.datum)+(c.doba_h?(' · '+c.doba_h+' h'):'')+' · '+esc(_MED_TYP[c.typ]||c.typ)+'</div>'));
        rw.appendChild(el('<div class="hint">krytí: '+esc(_krytiTxt(c.kryti))+' · sick '+c.kryto_sick_h+' h · proplaceno '+c.proplaceno_listecek_h+' h'+(c.neplaceno_h?(' · neplac. '+c.neplaceno_h+' h'):'')+' · '+esc(lbl)+'</div>'));
        if(c.has_foto){ var a=el('<div style="margin-top:4px;"><a href="/api/v1/erp/app/med/photo/'+c.id+'" target="_blank" style="color:#5ee0b7;font-size:13px;">📷 zobrazit foto</a></div>'); rw.appendChild(a); }
        box.appendChild(rw);
      });
    });
  }
  function medForm(){
    app.innerHTML=topbar("➕ Návštěva u lékaře", true);
    var w=el('<div style="padding:6px;display:flex;flex-direction:column;gap:12px;"></div>'); app.appendChild(w);
    var fDat=_ocrFld(w,"Datum návštěvy","DD.MM.RRRR");
    var wr2=el('<div style="display:flex;gap:10px;"></div>');
    var c1=el('<div style="flex:1;"></div>'), c2=el('<div style="flex:1;"></div>'); wr2.appendChild(c1); wr2.appendChild(c2); w.appendChild(wr2);
    var fOd=_ocrFld(c1,"Čas od (odchod)","HH:MM");
    var fDo=_ocrFld(c2,"Čas do (návrat)","HH:MM");
    var tw=el('<div></div>'); tw.appendChild(el('<div style="font-size:13px;color:#cdd6e2;margin-bottom:4px;">Typ návštěvy</div>'));
    var sel=el('<select style="width:100%;box-sizing:border-box;padding:10px;border-radius:10px;border:1px solid #2b3a5c;background:#0a1226;color:#e8eefc;"><option value="vyset">Vyšetření / ošetření</option><option value="prevent">Preventivní prohlídka</option><option value="doprovod">Doprovod (rodinný příslušník)</option></select>');
    tw.appendChild(sel); w.appendChild(tw);
    var fOsoba=_ocrFld(w,"Doprovázená osoba (jen u doprovodu)","jméno");
    var fVz=_ocrFld(w,"Vztah (jen u doprovodu)","dítě / rodič / …");
    var fZar=_ocrFld(w,"Zdravotnické zařízení / lékař","nepovinné");
    // foto
    var _foto=null;
    var fw=el('<div></div>'); fw.appendChild(el('<div style="font-size:13px;color:#cdd6e2;margin-bottom:4px;">Foto lístečku</div>'));
    var cam=el('<button style="width:100%;box-sizing:border-box;padding:11px;border-radius:10px;border:1px dashed #3a4c70;background:rgba(255,255,255,.03);color:var(--tx);font-weight:700;cursor:pointer;">📷 Vyfotit lísteček</button>');
    var thumb=el('<img style="display:none;max-width:100%;margin-top:8px;border-radius:10px;border:1px solid var(--bord);">');
    cam.addEventListener("click",function(){
      var fi=el('<input type="file" accept="image/*" capture="environment" style="display:none;">'); document.body.appendChild(fi);
      fi.addEventListener("change",function(){ var f=fi.files&&fi.files[0]; if(!f){fi.remove();return;} var fr=new FileReader(); fr.onload=function(){ _foto=fr.result; thumb.src=_foto; thumb.style.display="block"; cam.textContent="📷 Přefotit lísteček"; try{fi.remove();}catch(e){} }; fr.readAsDataURL(f); });
      fi.click();
    });
    fw.appendChild(cam); fw.appendChild(thumb); w.appendChild(fw);
    var st=el('<div class="hint" style="min-height:16px;"></div>'); w.appendChild(st);
    var sv=el('<button style="'+_OCR_BTN+'">Odeslat ke schválení</button>'); w.appendChild(sv);
    var cx=el('<button class="ghost sm" style="margin-top:4px;">Zrušit</button>'); cx.addEventListener("click",function(){ med(); }); w.appendChild(cx);
    sv.addEventListener("click",function(){
      var d=_isoDate(fDat.value); if(!/^\d{4}-\d{2}-\d{2}/.test(d)){ st.style.color="#ff8b8b"; st.textContent="Datum ve formátu DD.MM.RRRR."; return; }
      if(!_foto){ st.style.color="#ff8b8b"; st.textContent="Vyfoť prosím lísteček."; return; }
      sv.disabled=true; st.style.color="#9fb2d4"; st.textContent="Odesílám…";
      api("POST","/api/v1/erp/app/med/start",{datum:d,cas_od:(fOd.value||"").trim(),cas_do:(fDo.value||"").trim(),typ:sel.value,osoba_jmeno:(fOsoba.value||"").trim(),osoba_vztah:(fVz.value||"").trim(),zarizeni:(fZar.value||"").trim(),foto:_foto}).then(function(r){
        if(r&&r.ok){ med(); } else { sv.disabled=false; st.style.color="#ff8b8b"; st.textContent="Chyba: "+((r&&r.error)||"?"); }
      });
    });
  }
  function med_schval(){
    app.innerHTML=topbar("🩺 Lístečky — schvalování", true);
    var box=el('<div class="list"><div class="hint">Načítám…</div></div>'); app.appendChild(box);
    api("GET","/api/v1/erp/app/med/inbox","").then(function(j){
      box.innerHTML="";
      if(!j||!j.ok){ box.innerHTML='<div class="hint">'+((j&&j.error==="forbidden")?"🔒 Jen rodiče a HR.":"Nepodařilo se načíst.")+'</div>'; return; }
      var cs=j.cases||[];
      if(!cs.length){ box.innerHTML='<div class="hint">Nic ke schválení.</div>'; return; }
      cs.forEach(function(c){
        var rw=el('<div style="padding:10px 6px;border-bottom:1px solid var(--bord);"></div>');
        rw.appendChild(el('<div style="font-weight:600;">'+esc(c.zamestnanec||"")+' · '+_czDate(c.datum)+(c.doba_h?(' · '+c.doba_h+' h'):'')+'</div>'));
        rw.appendChild(el('<div class="hint">'+esc(_MED_TYP[c.typ]||c.typ)+(c.zarizeni?(' · '+esc(c.zarizeni)):'')+(c.company?(' · '+esc(c.company)):'')+'<br>krytí: '+esc(_krytiTxt(c.kryti))+' · sick '+c.kryto_sick_h+' h · proplaceno '+c.proplaceno_listecek_h+' h (limit '+c.limit_h+')'+(c.neplaceno_h?(' · neplac. '+c.neplaceno_h+' h'):'')+'</div>'));
        if(c.has_foto){ rw.appendChild(el('<div style="margin-top:4px;"><a href="/api/v1/erp/app/med/photo/'+c.id+'" target="_blank" style="color:#5ee0b7;font-size:13px;">📷 zobrazit foto</a></div>')); }
        var b=el('<button style="margin-top:6px;padding:8px 14px;border-radius:10px;border:1px solid #34d399;background:rgba(52,211,153,.15);color:#5ee0b7;font-weight:700;cursor:pointer;">✓ Schválit</button>');
        b.addEventListener("click",function(){ if(!confirm("Schválit lísteček pro "+(c.zamestnanec||"")+"?"))return; b.disabled=true; b.textContent="…"; api("POST","/api/v1/erp/app/med/approve",{id:c.id}).then(function(r){ if(r&&r.ok){ med_schval(); } else { b.disabled=false; b.textContent="✓ Schválit"; alert("Chyba: "+((r&&r.error)||"?")); } }); });
        rw.appendChild(b);
        box.appendChild(rw);
      });
    });
  }
  function med_prehled(){
    app.innerHTML=topbar("🩺 Lékař — přehled", true);
    var sum=el('<div class="hint" style="margin:8px 6px;"></div>'); app.appendChild(sum);
    var box=el('<div class="list"><div class="hint">Načítám…</div></div>'); app.appendChild(box);
    api("GET","/api/v1/erp/app/hr/med-overview","").then(function(j){
      box.innerHTML="";
      if(!j||!j.ok){ box.innerHTML='<div class="hint">'+((j&&j.error==="forbidden")?"🔒 Jen rodiče a HR.":"Nepodařilo se načíst.")+'</div>'; return; }
      var it=j.items||[]; if(!it.length){ box.innerHTML='<div class="hint">Žádné lístečky.</div>'; return; }
      var tProp=0,tDoba=0; it.forEach(function(c){ tProp+=c.proplaceno_listecek_h||0; tDoba+=c.doba_h||0; });
      sum.innerHTML='Celkem '+it.length+' návštěv · doba '+(Math.round(tDoba*10)/10)+' h · proplaceno lístečkem '+(Math.round(tProp*10)/10)+' h';
      it.forEach(function(c){
        var lbl={nahlaseno:"ke schválení",schvaleno:"schváleno",zamitnuto:"zamítnuto"}[c.stav]||c.stav;
        var rw=el('<div style="padding:9px 6px;border-bottom:1px solid var(--bord);"></div>');
        rw.appendChild(el('<div style="font-weight:600;">'+esc(c.zamestnanec||"")+' · '+_czDate(c.datum)+'</div>'));
        rw.appendChild(el('<div class="hint">'+(c.doba_h||0)+' h · '+esc(_krytiTxt(c.kryti))+' · proplaceno '+c.proplaceno_listecek_h+' h'+(c.company?(' · '+esc(c.company)):'')+' · '+esc(lbl)+(c.has_foto?' · 📷':'')+'</div>'));
        box.appendChild(rw);
      });
    });
  }
