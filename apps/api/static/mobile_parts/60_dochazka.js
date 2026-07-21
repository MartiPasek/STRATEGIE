  function dochHelp(openKey){
    var ov=el('<div class="appmodal" style="position:fixed;inset:0;background:rgba(4,10,18,.97);z-index:400;display:flex;flex-direction:column;padding:14px 14px 0;"></div>');
    var hd=el('<div style="display:flex;gap:8px;align-items:center;margin-bottom:8px;"><div style="flex:1;font-weight:800;font-size:18px;">❓ Nápověda — Docházka</div></div>');
    var cl=el('<button class="ghost" style="margin:0;width:44px;">✕</button>'); cl.addEventListener("click",function(){ ov.remove(); }); hd.appendChild(cl); ov.appendChild(hd);
    var sc=el('<div style="flex:1;overflow:auto;-webkit-overflow-scrolling:touch;padding-bottom:60px;"></div>'); ov.appendChild(sc);
    sc.appendChild(el('<div class="hint" style="margin-top:0;">Docházku najdeš dole: <b>🏢 Firma → 🤝 Spolupráce</b> (nebo dlaždice 🤝 Spolupráce v Aplikacích). Práci spustíš nahoře přes <b>▶️ Makat</b>, akce za chodu přes zelené <b>💬 Potřebuji ti něco říct…</b>, nepřítomnosti přes <b>🧭 Tady budu jinde</b>.</div>'));
    // Hlasový průvodce (Jirka 26.6.): video s mluveným výkladem krok za krokem.
    var _vg=el('<button class="full" style="margin:10px 0 2px;padding:13px;font-size:15px;font-weight:700;background:#2563eb;color:#fff;border:none;border-radius:12px;display:flex;align-items:center;justify-content:center;gap:8px;">▶️ Hlasový průvodce (video s výkladem)</button>');
    _vg.addEventListener("click",function(){ try{_tapFeedback();}catch(e){} ov.remove(); dochPruvodce(); });
    sc.appendChild(_vg);
    sc.appendChild(el('<div class="hint" style="margin-top:4px;text-align:center;">Mluvený průvodce krok za krokem — ťukni ▶ Přehrát.</div>'));
    // Tahák
    var tah=el('<div style="margin:12px 0;background:rgba(79,142,247,.07);border:1px solid #2a4d80;border-radius:12px;padding:10px 12px;"></div>');
    tah.appendChild(el('<div style="font-weight:700;margin-bottom:4px;">📋 Tahák — co když…?</div>'));
    [["Přijít do práce","vyber 🧾 Zakázku + 🔧 Činnost → ▶️ Makat (nebo 💬 → 🏢 Jsem v práci)"],["Z domova","💬 → 🏠 Nejsem v práci (home office)"],["Jsem na cestě","💬 → 🚗 Jedu do práce"],["Změnit zakázku/činnost","nahoře 🟢 MAKÁŠ — klikni a změň"],["Oběd / pauza","💬 → 🙈 → 🍃 Najíst / ☕ Pauza"],["Zpět z pauzy","✅ Jsem zpět — pokračuju"],["Jednání / pochůzka","💬 → 🙈 → 📅 jednání / 🚗 pochůzka"],["Konec dne","💬 → 🙈 → 🫡 Dnes už se mnou nepočítej"],["Dovolená / nemoc / lékař","🧭 Tady budu jinde → 🏠 Osobní důvody"],["Potvrdit den","jantarová karta → ✓ Potvrzuji (/ ✋ Rozpor)"],["Oprava záznamu","ťukni záznam → ⏱ Zkrátit konec / 🧾 Změnit zakázku"],["Už jsem den potvrdil a nesedí","✋ <b>Požádat o opravu</b> (Moje docházka) — jen tento měsíc"],["Dotaz / pomoc","💬 → 🙋 Mám dotaz na nadřízeného"]].forEach(function(r){ tah.appendChild(el('<div style="display:flex;gap:8px;padding:3px 0;border-top:1px solid rgba(255,255,255,.06);font-size:13.5px;"><div style="flex:0 0 42%;">'+r[0]+'</div><div style="flex:1;color:var(--mut);">'+r[1]+'</div></div>')); });
    sc.appendChild(tah);
    // Rozbalovací sekce (věrně dle uživatelského návodu)
    var items=[
     ["prichod","👷 Příchod — jak začít pracovat",
       "<b>Dva způsoby:</b><br><b>A)</b> Nahoře v sekci <b>Zakázky a činnosti</b> vyber <b>🧾 Zakázku</b> a <b>🔧 Činnost</b>, pak ťukni zelené <b>▶️ Makat</b>.<br><b>B)</b> Nebo <b>💬 Potřebuji ti něco říct…</b> → <b>🏢 Jsem v práci…</b><br>✓ Hlavička: <i>„Dnes makám 😉“</i> — hodiny tikají.<br><br>💡 Z domova: <b>💬 → 🏠 Nejsem v práci (home office)</b>.<br>💡 Teprve na cestě: <b>💬 → 🚗 Jedu do práce</b> → vyber, za jak dlouho dorazíš. Kolegové to vidí; hodiny se počítají až po příchodu."],
     ["zakcin","🧾 Zakázka a činnost",
       "Nahoře jsou dvě dlaždice — říkají, na čem pracuješ:<br><b>🧾 Zakázka</b> — vyber podle čísla nebo názvu, nebo <b>🧰 Režie</b> (práce bez konkrétní zakázky).<br><b>🔧 Činnost</b> — co děláš.<br><br>Když už makáš, je nahoře <b>🟢 MAKÁŠ — klikni a změň</b>: zakázku i činnost <b>přepneš kdykoli během dne</b> (třeba když začneš dělat na něčem jiném)."],
     ["pauza","🍽️ Pauza / oběd",
       "1. <b>💬 Potřebuji ti něco říct…</b><br>2. <b>🙈 Teď to bude jinak…</b><br>3. <b>🍃 Jdu se provětrat / najíst…</b> nebo <b>☕ Potřebuju krátkou pauzu…</b><br>Hlavička: <i>„Dávám si pauzu ☕“</i> — <b>hodiny NETIKAJÍ</b>.<br>Návrat: <b>✅ Jsem zpět — pokračuju</b>.<br><br>⚠️ Pauza = hodiny stojí! Po obědě se nezapomeň píchnout zpátky."],
     ["jednani","🤝 Jednání, pochůzka, dřív/později",
       "Během směny přes <b>💬 → 🙈 Teď to bude jinak…</b>:<br>📅 <b>Mám jednání…</b> · 🚗 <b>Mám služební pochůzku…</b> — zadáš čas „cca“ nebo „do“. <b>Hodiny TIKAJÍ DÁL</b> (není to pauza, jen info, kde jsi).<br>🌅 <b>Potřebuji přijít později…</b> · 🕔 <b>Potřebuji skončit dříve…</b> — nahlásíš dopředu."],
     ["odchod","🏠 Konec práce (odchod)",
       "1. <b>💬 Potřebuji ti něco říct…</b><br>2. <b>🙈 Teď to bude jinak…</b><br>3. <b>🫡 Dnes už se mnou nepočítej ;)</b><br>✓ Směna ukončena — uvidíš souhrn hodin.<br><br>💡 Zapomněl ses odhlásit? Systém tě o půlnoci odhlásí sám a upozorní tě. Raději se ale odhlas sám, je to přesnější."],
     ["potvrzeni","✅ Potvrzení docházky",
       "Po dni uvidíš <b>jantarovou (žlutou) kartu</b>: <i>„🖊 Včera · 7:26–16:26 · 7:52“</i>.<br>1. Zkontroluj údaje (detail v sekci „Tak to bylo dneska“).<br>2. Ťukni <b>✓ Potvrzuji svou docházku</b>.<br><br>⚠️ Dokud den nepotvrdíš, ráno se nepíchneš! Na potvrzení máš <b>14 dní</b>.<br>💡 Nesedí? Ťukni <b>✋ Rozpor</b> a napiš, co je špatně — dostane to nadřízený a pustí tě pracovat dál.<br><br>🆕 <b>Potvrdil jsi omylem a teprve pak zjistil, že to nesedí?</b> Nevadí — v sekci <b>Moje docházka</b> ťukni dlaždici <b>✋ Požádat o opravu</b>, vyber den (i starší) a napiš, co je špatně. Dostane to kontrola docházky a ozve se ti. Funguje i pro už potvrzený den."],
     ["oprava_zpetne","✋ Požádat o opravu (i po potvrzení dne)",
       "Když ti na už uzavřeném dni něco nesedí — <b>omylem jsi ho potvrdil</b>, chybí příchod nebo odchod, je špatný čas nebo zakázka:<br><br><b>Kudy na to (dvě cesty, obě stejné):</b><br><b>A)</b> Sekce <b>Moje docházka</b> → dlaždice <b>✋ Požádat o opravu</b> → vyber den <b>z aktuálního měsíce</b> → ťukni konkrétní záznam, nebo <b>✋ Nesedí mi celý den</b>.<br><b>B)</b> V <b>🕓 Historii</b> (nebo 📅 Dnešek) ťukni na záznam → v řadě ikonek vyber <b>✋</b>.<br><br>Pak jen napiš, co je špatně — můžeš si ťuknout hotový důvod (<i>omylem jsem potvrdil(a) den</i>, <i>chybí odchod</i>, …) a doplnit vlastní text.<br><br>✓ Žádost dostane <b>kontrola docházky</b> (Peťa, u výroby Dušan s Míšou), den se jim označí jako <b>✋ rozpor</b> a ozvou se ti. Nemusíš už za nimi chodit osobně.<br>💡 Sám si zpětně den nepřepisuješ — opravu udělá pověřená osoba, aby byla dohledatelná.<br><br>⏳ <b>Jen za aktuální měsíc!</b> Starší období už prošlo mzdami a nejde opravovat. Proto si docházku kontroluj průběžně — a když něco nesedí, řekni si hned. Za starší den se ozvi kontrole docházky osobně."],
     ["jinde","🧭 Tady budu jinde — dovolená, nemoc, lékař…",
       "Plánované nepřítomnosti hlásíš dlaždicí <b>🧭 Tady budu jinde</b> (sekce <b>Moje docházka</b>):<br><br><b>🏠 Osobní důvody:</b><br>🌴 <b>Že by dovolená?</b> (od–do)<br>👨‍👧 <b>Zase řeším rodinu</b> — OČR (od–do)<br>🤒 <b>Je mi fakt blbě</b> — sick day (dnes)<br>🤧 <b>Mám neschopenku do…</b> — nemoc<br>🩺 <b>Jedu k lékaři</b> (pak dorazím / dnes ne / hlásím dopředu)<br>🏡 <b>Potřebuju makat z domova</b> — home office<br>🕐 <b>Něco si zařizuji</b> — dorazím za…<br><br><b>💼 Služební důvody:</b><br>🚙 Jedu rovnou k zákazníkovi · 🎓 Jsem na školení · 📦 Služební pochůzka, pak dorazím · 📝 Ostatní (napíšeš důvod)<br><br>💡 Žádosti jdou ke schválení nadřízenému, přijde ti notifikace."],
     ["komunikace","🙋 Pomoc, zprávy a opravy",
       "<b>🙋 Mám dotaz na nadřízeného…</b> (v menu 💬) — napiš zprávu, dostane ji rovnou do mobilu.<br><b>💬 Píši přímo tobě, Marti…</b> — napíšeš asistentce Marti-AI.<br>Pro výrobu: <b>🛠 Zpráva vedoucímu výroby…</b> · <b>🏁 Budu brzy hotov…</b><br><br><b>✏️ Oprava záznamu:</b> v sekci „Tak to bylo dneska“ ťukni na záznam → <b>⏱ Zkrátit konec</b> nebo <b>🧾 Změnit zakázku</b>.<br><b>✋ Už potvrzený den (v tomto měsíci):</b> sekce <b>Moje docházka</b> → <b>✋ Požádat o opravu</b> (nebo v 🕓 Historii ťukni záznam → <b>✋</b>) — opraví to kontrola docházky."],
     ["prehledy","📊 Přehledy a moje údaje",
       "Sekce <b>Moje docházka</b>: 📅 <b>Dnešek</b> · 📅 <b>Týden</b> · 🔭 <b>Výhled</b> · 🕓 <b>Historie</b> · 📋 <b>Moje žádosti</b>.<br>Sekce <b>Podmínky &amp; finance</b>: 📋 Moje podmínky · 📐 <b>Můj úvazek</b> · 👤 Můj plán · 💰 <b>Moje finance</b> · 🗓️ Nepřítomnosti.<br><br>💰 <b>Moje odmakané prašule</b> (výplatní páska) je dole na obrazovce, <b>zamčená PINem</b>."],
     ["faq","❓ Časté otázky",
       "<b>Musím při příchodu vybírat zakázku?</b><br>Nemusíš — dej <b>🧰 Režie</b> (bez zakázky), nebo prostě <b>💬 → 🏢 Jsem v práci</b>. Zakázku i činnost změníš i během dne (🟢 MAKÁŠ).<br><br><b>Zapomněl jsem se ráno píchnout.</b><br>Píchni se, jak si vzpomeneš (zapíše se od aktuálního času). O opravu času pak požádej: <b>Moje docházka → ✋ Požádat o opravu</b>.<br><br><b>Omylem jsem potvrdil den — a teď vidím, že nesedí!</b><br>Klid, jde to napravit. <b>Moje docházka → ✋ Požádat o opravu</b> → vyber ten den → napiš, co je špatně (máš tam i hotový důvod „omylem jsem potvrdil(a) den“). Dostane to kontrola docházky a opraví to. Funguje i na už potvrzený den — ale <b>jen v rámci aktuálního měsíce</b> (starší už prošlo mzdami; tam se ozvi osobně).<br><br><b>Zapomněl jsem se odhlásit.</b><br>O půlnoci tě systém odhlásí sám — bude to ale víc hodin než realita. Raději se odhlas sám.<br><br><b>Nepustí mě píchnout!</b><br>Máš nepotvrzený den. Najdi jantarovou kartu → <b>✓ Potvrzuji</b> nebo <b>✋ Rozpor</b>.<br><br><b>Směna běží vs. pauza?</b><br>Běží = zelená hlavička, hodiny počítají. Pauza = oranžová, hodiny stojí. Jednání/pochůzka = hodiny běží dál.<br><br><b>Mám dotaz.</b><br>V menu 💬 ťukni <b>🙋 Mám dotaz na nadřízeného…</b>"]
    ];
    var openWrap=null;
    items.forEach(function(it){
      var open=(openKey&&openKey===it[0]);
      var wrap=el('<div style="border:1px solid var(--bord);border-radius:12px;margin-bottom:8px;overflow:hidden;"></div>');
      var h=el('<div style="padding:12px;font-weight:700;display:flex;justify-content:space-between;align-items:center;cursor:pointer;background:var(--surf);"><span>'+it[1]+'</span><span class="caret" style="color:var(--mut);">'+(open?'▾':'▸')+'</span></div>');
      var b=el('<div style="padding:0 12px 12px;font-size:14px;line-height:1.55;color:var(--tx);display:'+(open?'block':'none')+';">'+it[2]+'</div>');
      h.addEventListener("click",function(){ var o=b.style.display==="none"; b.style.display=o?'block':'none'; var c=h.querySelector('.caret'); if(c)c.textContent=o?'▾':'▸'; if(o){ try{wrap.scrollIntoView({behavior:'smooth',block:'nearest'});}catch(e){} } });
      wrap.appendChild(h); wrap.appendChild(b); sc.appendChild(wrap);
      if(open) openWrap=wrap;
    });
    sc.appendChild(el('<div class="hint" style="text-align:center;">Potřebuješ víc? Napiš nadřízenému přes 🙋 v menu, nebo HR.</div>'));
    app.appendChild(ov);
    if(openWrap){ try{ openWrap.scrollIntoView({behavior:'smooth',block:'center'}); }catch(e){} }
  }
  // ── Hlasový průvodce docházkou (Jirka 26.6.): nativní full-screen přehrávač ──
  // Profi přestavba: responsivní (obrázky se vždy vejdou), spolehlivá řeč:
  //  • text dělen na krátké úseky (<180 zn.) kvůli Android 15s/250zn. cutoffu (chunking,
  //    NE pause/resume — ten Android zruší),
  //  • řeč se VŽDY zruší při zavření/skrytí/hardware-back (MutationObserver + visibilitychange),
  //  • žádný globální swipe (skákání kapitol), jen jasná tlačítka.
  function dochPruvodce(){
    var synth = window.speechSynthesis;
    var IMG="/static/navod_dochazka/";
    var SL=[
      {t:"📱 Docházka v mobilu", img:"",
       cap:'<p style="font-size:17px;margin:0 0 8px;">Hlasový průvodce krok za krokem.</p><p class="hint" style="margin:0;">Ťukni dole <b style="color:#58a6ff">▶ Přehrát</b> a jen poslouchej a koukej — nebo procházej šipkami <b>◀ ▶</b> a čti si sám.</p>',
       v:"Vítejte v hlasovém průvodci docházkou ve STRATEGII. Projdeme spolu, jak v mobilu nahlásit příchod, práci na zakázce, pauzu, odchod, i dovolenou nebo lékaře. Stačí poslouchat a koukat. Pro další stránku ťukněte na šipku doprava."},
      {t:"🏢 Kde docházku najdeš", img:IMG+"pruvodce_firma.png",
       cap:'<div class="dp-step"><b>1.</b> Na spodní liště ťukni <b style="color:#58a6ff">🏢 Firma</b> (vpravo dole).</div><div class="dp-step"><b>2.</b> Ťukni <b style="color:#3fb950">🤝 Spolupráce</b>.</div><div class="dp-step dp-ok">✓ Jsi na obrazovce docházky. Najdeš ji i v <b>Aplikacích</b> jako dlaždici 🤝 Spolupráce.</div>',
       v:"Docházku najdete takto. Na spodní liště ťukněte úplně vpravo na Firma. Pak ťukněte na Spolupráce. A jste na obrazovce docházky. Stejnou obrazovku najdete i v Aplikacích jako dlaždici Spolupráce."},
      {t:"👀 Obrazovka docházky — kde co je", img:IMG+"pruvodce_prehled.png",
       cap:'<p class="hint" style="margin-top:0">Tohle je obrazovka docházky:</p><div class="dp-step">Nahoře <b>ZAKÁZKY A ČINNOSTI</b> — dlaždice <b style="color:#58a6ff">🧾 Zakázka</b> a <b>🔧 Činnost</b> + zelené <b style="color:#3fb950">▶️ Makat</b>.</div><div class="dp-step">Pod tím zelené <b style="color:#3fb950">💬 Potřebuji ti něco říct…</b> (skoro všechny akce).</div><div class="dp-step">Níž <b>Moje docházka</b>: Dnešek, Týden, Historie, <b>🧭 Tady budu jinde</b>.</div>',
       v:"Tohle je obrazovka docházky. Úplně nahoře je sekce Zakázky a činnosti se dvěma dlaždicemi, Zakázka a Činnost, a zeleným tlačítkem Makat. Pod tím je zelené tlačítko Potřebuji ti něco říct, kterým ovládáte skoro všechno. A níž je sekce Moje docházka s přehledy a s dlaždicí Tady budu jinde."},
      {t:"🧾 Příchod: vyber zakázku", img:IMG+"pruvodce_zakazka.png",
       cap:'<div class="dp-step"><b>1.</b> Ťukni dlaždici <b style="color:#58a6ff">🧾 Zakázka</b>.</div><div class="dp-step">Vyber zakázku podle <b>čísla nebo názvu</b> (hledání nahoře) — nebo <b>🧰 Režie</b> (práce bez konkrétní zakázky).</div>',
       v:"Začneme příchodem. Nejdřív vyberte, na čem budete pracovat. Ťukněte na dlaždici Zakázka. Otevře se seznam, kde zakázku najdete podle čísla nebo názvu. Pokud neděláte na konkrétní zakázce, zvolte nahoře Režie."},
      {t:"🔧 Příchod: vyber činnost a Makat", img:IMG+"pruvodce_cinnost.png",
       cap:'<div class="dp-step"><b>2.</b> Ťukni dlaždici <b style="color:#58a6ff">🔧 Činnost</b> a vyber, co děláš (Bez rozlišení činnosti, Porada, Úklid, Pracovní cesta…).</div><div class="dp-step dp-ok"><b>3.</b> Pak ťukni zelené <b style="color:#3fb950">▶️ Makat</b> — docházka se spustí, hlavička „Dnes makám 😉", hodiny tikají.</div>',
       v:"Pak ťukněte na dlaždici Činnost a vyberte, co budete dělat. Když máte vybranou zakázku i činnost, ťukněte na zelené tlačítko Makat. Docházka se spustí, hlavička se změní na Dnes makám a hodiny začnou tikat."},
      {t:"💬 Příchod jinak — přes menu", img:IMG+"pruvodce_menu.png",
       cap:'<p class="hint" style="margin-top:0">Rychlá alternativa — ťukni zelené <b style="color:#3fb950">💬 Potřebuji ti něco říct…</b>:</p><div class="dp-step">🏢 <b>Jsem v práci…</b> — běžný příchod</div><div class="dp-step">🏠 <b>Nejsem v práci… (home office)</b></div><div class="dp-step">🚗 <b>Jedu do práce…</b> — když jsi teprve na cestě (vybereš, za jak dlouho dorazíš)</div><div class="dp-step">🌅 Potřebuji přijít později… · 🕔 Potřebuji skončit dříve…</div>',
       v:"Příchod jde i rychleji, přes zelené tlačítko Potřebuji ti něco říct. Tam ťuknete Jsem v práci pro běžný příchod, nebo Nejsem v práci, home office, když děláte z domova. Když jste teprve na cestě, vyberte Jedu do práce a kolegové uvidí, že dorazíte. Najdete tu i volby Potřebuji přijít později a Potřebuji skončit dříve."},
      {t:"🍽️ Pauza / oběd", img:IMG+"pruvodce_jinak.png",
       cap:'<p class="hint" style="margin-top:0">Během směny ťukni zelené <b style="color:#3fb950">💬 Potřebuji ti něco říct…</b>, pak:</p><div class="dp-step"><b style="color:#d29922">🙈 Teď to bude jinak…</b> → ☕ Potřebuju krátkou pauzu · nebo 🍃 Jdu se provětrat / najíst</div><div class="dp-step dp-amber">⏸ Hodiny STOJÍ (pauza se nepočítá).</div><div class="dp-step dp-ok">Po pauze: ✅ Jsem zpět — pokračuju.</div>',
       v:"Když jdete na oběd nebo si dáte pauzu, ťukněte zelené Potřebuji ti něco říct, pak oranžové Teď to bude jinak, a vyberte Jdu se provětrat nebo najíst, případně Potřebuju krátkou pauzu. Hodiny se zastaví, pauza se nepočítá. Po pauze se vraťte tlačítkem Jsem zpět, pokračuju."},
      {t:"🤝 Jednání, pochůzka, dřív/později", img:IMG+"pruvodce_jinak.png",
       cap:'<p class="hint" style="margin-top:0">Také přes 💬 → <b style="color:#d29922">🙈 Teď to bude jinak…</b>:</p><div class="dp-step">📅 <b>Mám jednání…</b> · 🚗 <b>Mám služební pochůzku…</b> (zadáš čas) — <b>hodiny TIKAJÍ DÁL</b>, jen info, kde jsi.</div><div class="dp-step">🌅 <b>Potřebuji přijít později…</b> · 🕔 <b>Potřebuji skončit dříve…</b></div>',
       v:"Když máte během práce schůzku nebo pochůzku, ťukněte Potřebuji ti něco říct, Teď to bude jinak, a vyberte Mám jednání nebo Mám služební pochůzku. Zadáte, jak dlouho to potrvá. Pozor, tohle není pauza, hodiny běží dál. Je to jen informace pro kolegy, kde zrovna jste."},
      {t:"🏠 Konec práce — odchod", img:IMG+"pruvodce_odchod.png",
       cap:'<div class="dp-step"><b>1.</b> 💬 Potřebuji ti něco říct…</div><div class="dp-step"><b>2.</b> <b style="color:#d29922">🙈 Teď to bude jinak…</b></div><div class="dp-step dp-warn"><b>3.</b> 🫡 Dnes už se mnou nepočítej ;)</div><div class="dp-step dp-ok">✓ Směna ukončena — uvidíš souhrn hodin.</div><p class="hint">Zapomněl ses odhlásit? Systém tě o půlnoci odhlásí sám — ale raději se odhlas sám, je to přesnější.</p>',
       v:"Když končíte a jdete domů, ťukněte zelené Potřebuji ti něco říct, pak oranžové Teď to bude jinak, a nakonec Dnes už se mnou nepočítej. Směna se ukončí a uvidíte souhrn hodin. Když se zapomenete odhlásit, systém vás o půlnoci odhlásí sám a upozorní vás, ale raději se odhlašte sami, je to přesnější."},
      {t:"✅ Potvrzení docházky", img:IMG+"pruvodce_potvrzeni.png",
       cap:'<div class="dp-step dp-amber">🖊 Včera · 7:26–16:26 · 7:52 — zkontroluj a potvrď.</div><div class="dp-step dp-ok">✓ Potvrzuji svou docházku</div><div class="dp-step dp-warn">⚠️ Bez potvrzení se ráno nepíchneš! Nesedí? → ✋ Rozpor (napiš, co je špatně).</div><p class="hint">Na potvrzení máš 14 dní.</p>',
       v:"Po skončení dne, nebo další ráno, vás systém požádá o potvrzení. Uvidíte žlutou kartu s časem a počtem hodin. Zkontrolujte, jestli to sedí, a ťukněte Potvrzuji svou docházku. Důležité: dokud den nepotvrdíte, ráno se nepíchnete. Když něco nesedí, ťukněte Rozpor a napište, co je špatně. Dostane to nadřízený a vy můžete pracovat dál. Na potvrzení máte čtrnáct dní."},
      {t:"🧭 Dovolená, nemoc, lékař, OČR…", img:IMG+"pruvodce_jinde.png",
       cap:'<p class="hint" style="margin-top:0">Plánované nepřítomnosti hlásíš dlaždicí <b>🧭 Tady budu jinde</b> (sekce Moje docházka), pak <b>🏠 Osobní důvody</b>:</p><table class="dp"><tr><td>🌴</td><td><b>Že by dovolená?</b></td><td>od–do</td></tr><tr><td>👨‍👧</td><td><b>Zase řeším rodinu</b></td><td>OČR, od–do</td></tr><tr><td>🤒</td><td><b>Je mi fakt blbě</b></td><td>sick day (dnes)</td></tr><tr><td>🤧</td><td><b>Mám neschopenku do…</b></td><td>nemoc</td></tr><tr><td>🩺</td><td><b>Jedu k lékaři</b></td><td>pak dorazím / dnes ne</td></tr><tr><td>🏡</td><td><b>Makat z domova</b></td><td>home office</td></tr><tr><td>🕐</td><td><b>Něco si zařizuji</b></td><td>dorazím za…</td></tr></table><div class="dp-step">💼 <b>Služební důvody</b>: 🚙 k zákazníkovi · 🎓 školení · 📦 pochůzka. Vše jde ke schválení nadřízenému.</div>',
       v:"Dovolenou, lékaře nebo nemoc nahlásíte takhle. Na obrazovce docházky v sekci Moje docházka ťukněte na dlaždici Tady budu jinde. Pak vyberte Osobní důvody. Najdete tu Že by dovolená, Zase řeším rodinu pro ošetřovné, Je mi fakt blbě pro sick day, Mám neschopenku, Jedu k lékaři, Potřebuju makat z domova, a Něco si zařizuji. U dovolené, ošetřovného nebo home office zadáte datum od do. Je tu i volba Služební důvody, třeba školení nebo cesta k zákazníkovi. Každá žádost jde ke schválení nadřízenému a přijde vám notifikace."},
      {t:"🆘 Pomoc, opravy a přehledy", img:IMG+"pruvodce_menu.png",
       cap:'<div class="dp-step">🙋 <b>Mám dotaz na nadřízeného…</b> (v menu 💬) — napiš zprávu, dostane ji rovnou do mobilu.</div><div class="dp-step">✏️ <b>Ťukl jsi špatně?</b> V sekci „Tak to bylo dneska“ ťukni na záznam → <b>⏱ Zkrátit konec</b> nebo <b>🧾 Změnit zakázku</b>.</div><div class="dp-step">📊 Přehledy (sekce Moje docházka): 📅 Dnešek · Týden · 🕓 Historie · 📋 Moje žádosti · 📐 Můj úvazek · 💰 Moje finance (PIN).</div><div class="dp-step dp-ok" style="text-align:center">💬 zelené „Potřebuji ti něco říct" · 🙈 oranžové „Teď to bude jinak" · 🧭 „Tady budu jinde"</div>',
       v:"Na závěr pár užitečných věcí. Když si nevíte rady, v menu Potřebuji ti něco říct je tlačítko Mám dotaz na nadřízeného. Napíšete zprávu a dostane ji rovnou do mobilu. Když se spletete a chcete opravit záznam, ťukněte na něj v sekci Tak to bylo dneska a vyberte Zkrátit konec, nebo Změnit zakázku. A v sekci Moje docházka najdete přehledy: dnešek, týden, historii, svoje žádosti, úvazek i svoje finance, které jsou zamčené PINem. To je celé. Děkuji za pozornost a přeji hezký den."}
    ];
    var cur=0, voiceMode=false, queue=[], qi=0, nextT=null, mo=null, watchdog=null;
    var czVoice=null;
    function pickVoice(){ try{ var vs=synth?synth.getVoices():[]; czVoice=vs.filter(function(v){return v.lang==="cs-CZ";})[0] || vs.filter(function(v){return v.lang&&v.lang.indexOf("cs")===0;})[0] || null; }catch(e){} }
    if(synth){ pickVoice(); try{ synth.addEventListener("voiceschanged",pickVoice); }catch(e){} }
    // Dělení na krátké úseky (<180 zn.) — Android-safe (chunking, ne pause/resume).
    function chunk(t){
      var parts=(t.match(/[^.!?]+[.!?]*/g)||[t]).map(function(s){return s.trim();}).filter(Boolean), out=[];
      parts.forEach(function(s){
        if(s.length<=180){ out.push(s); return; }
        var buf=""; s.split(/,\s*/).forEach(function(c){
          if((buf+", "+c).length>180){ if(buf)out.push(buf); buf=c; } else buf=buf?buf+", "+c:c;
        });
        if(buf)out.push(buf);
      });
      return out;
    }
    // Overlay
    var ov=el('<div id="dpOverlay" class="appmodal"></div>');
    ov.style.cssText="position:fixed;inset:0;z-index:100000;background:#0b0e14;display:flex;flex-direction:column;padding-top:env(safe-area-inset-top,0px);";
    ov.appendChild(el('<style>#dpOverlay *{box-sizing:border-box}'
      +'#dpHd{display:flex;align-items:center;gap:8px;padding:10px 12px;border-bottom:1px solid #1d2733}'
      +'#dpHd .ttl{flex:1;font-weight:700;font-size:15px;color:#e6edf3}'
      +'#dpPill{display:none;align-items:center;gap:6px;background:rgba(37,99,235,.18);color:#7db0ff;border:1px solid #2f6feb;border-radius:20px;padding:3px 10px;font-size:12px}'
      +'#dpPill.on{display:inline-flex}'
      +'#dpPill .w{display:inline-block;width:3px;height:10px;background:#7db0ff;border-radius:2px;animation:dpw 1s infinite}'
      +'#dpProg{height:3px;background:#1d2733}#dpProg>div{height:100%;width:0;background:linear-gradient(90deg,#2f6feb,#7c3aed);transition:width .35s}'
      +'#dpStage{flex:1;overflow:auto;-webkit-overflow-scrolling:touch;padding:16px 16px 8px;display:flex;flex-direction:column;align-items:center;gap:12px}'
      +'#dpStage h2{font-size:20px;margin:0;text-align:center;color:#fff}'
      +'#dpStage img{max-width:100%;max-height:44vh;object-fit:contain;border-radius:14px;border:1px solid #25303f;display:block}'
      +'#dpStage .capw{width:100%;max-width:520px;color:#dbe3ee}'
      +'#dpStage .dp-step{background:#121822;border:1px solid #25303f;border-left:3px solid #2f6feb;border-radius:10px;padding:9px 12px;margin:8px 0;font-size:15px;line-height:1.5;text-align:left}'
      +'#dpStage .dp-ok{border-left-color:#16a34a;background:rgba(22,163,74,.08)}'
      +'#dpStage .dp-warn{border-left-color:#dc2626;background:rgba(220,38,38,.09)}'
      +'#dpStage .dp-amber{border-left-color:#d29922;background:rgba(210,153,34,.10)}'
      +'#dpStage table.dp{width:100%;border-collapse:collapse;font-size:14px}'
      +'#dpStage table.dp td{padding:7px 8px;border-bottom:1px solid #1b2430;text-align:left;vertical-align:top}'
      +'#dpStage table.dp td:first-child{width:1%;white-space:nowrap;font-size:1.3em}'
      +'#dpCtl{display:flex;align-items:center;gap:8px;padding:10px 12px calc(10px + env(safe-area-inset-bottom,0px));border-top:1px solid #1d2733}'
      +'#dpCtl button{border:1px solid #2a3340;background:#161d28;color:#e6edf3;border-radius:12px;padding:11px 14px;font-size:15px;font-weight:700;cursor:pointer}'
      +'#dpCtl button:disabled{opacity:.35}'
      +'#dpCtl .play{flex:1;background:#2563eb;border-color:#2563eb;color:#fff}'
      +'#dpCtl .num{min-width:42px;text-align:center;color:#8b949e;font-size:13px}'
      +'@keyframes dpw{0%,100%{transform:scaleY(.5)}50%{transform:scaleY(1)}}'
      +'</style>'));
    var hd=el('<div id="dpHd"><span class="ttl">🔊 Hlasový průvodce</span><span id="dpPill"><span class="w"></span>Čtu…</span></div>');
    var clo=el('<button style="border:1px solid #2a3340;background:#161d28;color:#e6edf3;border-radius:10px;width:40px;height:36px;font-size:16px;cursor:pointer;">✕</button>');
    clo.addEventListener("click",function(){ closeDp(); });
    hd.appendChild(clo); ov.appendChild(hd);
    var prog=el('<div id="dpProg"><div></div></div>'); ov.appendChild(prog);
    var stage=el('<div id="dpStage"></div>'); ov.appendChild(stage);
    var ctl=el('<div id="dpCtl"></div>');
    var bPrev=el('<button>◀</button>'), bPlay=el('<button class="play">▶ Přehrát</button>'), bNext=el('<button>▶</button>'), num=el('<span class="num">1/'+SL.length+'</span>');
    ctl.appendChild(bPrev); ctl.appendChild(num); ctl.appendChild(bPlay); ctl.appendChild(bNext); ov.appendChild(ctl);

    function pill(on){ var p=document.getElementById("dpPill"); if(p)p.classList.toggle("on",!!on); }
    function clearWd(){ if(watchdog){ clearTimeout(watchdog); watchdog=null; } }
    function stopSpeak(){ try{ if(synth)synth.cancel(); }catch(e){} if(nextT){clearTimeout(nextT);nextT=null;} clearWd(); pill(false); }
    function updUI(){
      num.textContent=(cur+1)+"/"+SL.length;
      prog.firstChild.style.width=(SL.length>1?(cur/(SL.length-1))*100:100)+"%";
      bPrev.disabled=cur===0; bNext.disabled=cur===SL.length-1;
      bPlay.textContent=voiceMode?"⏸ Pauza":"▶ Přehrát";
      bPlay.classList.toggle("playing",voiceMode);
    }
    function render(){
      stage.scrollTop=0; stage.innerHTML="";
      var s=SL[cur];
      stage.appendChild(el('<h2>'+s.t+'</h2>'));
      if(s.img){ var im=el('<img alt="">'); im.src=s.img; stage.appendChild(im); }
      var cw=el('<div class="capw"></div>'); cw.innerHTML=s.cap; stage.appendChild(cw);
      updUI();
    }
    function speakCur(){
      stopSpeak();
      if(!synth || !voiceMode) return;
      var t=SL[cur].v||"";
      if(!t){ scheduleNext(); return; }
      queue=chunk(t); qi=0; pill(true);
      // malé zpoždění po cancel() — jinak Chrome/Android občas zahodí hned navázaný speak()
      setTimeout(function(){ if(voiceMode && document.body.contains(ov)) speakChunk(); }, 160);
    }
    function speakChunk(){
      if(!voiceMode || !document.body.contains(ov)) return;
      if(qi>=queue.length){ pill(false); clearWd();
        if(cur<SL.length-1){ scheduleNext(); } else { voiceMode=false; updUI(); }
        return; }
      var txt=queue[qi], moved=false;
      function adv(){ if(moved)return; moved=true; clearWd(); qi++; speakChunk(); }
      var u=new SpeechSynthesisUtterance(txt);
      if(czVoice)u.voice=czVoice; u.lang="cs-CZ"; u.rate=.97; u.pitch=1;
      u.onend=adv; u.onerror=adv;
      // WATCHDOG: když speechSynthesis nevyšle onend (Android/Chrome to po pár větách občas
      // zahodí → auto-posun zamrzne), posuň se po odhadnuté době sám. Pojistka, ne primární cesta.
      clearWd(); watchdog=setTimeout(adv, Math.max(4000, txt.length*95) + 2500);
      try{ synth.speak(u); }catch(e){ adv(); }
    }
    function scheduleNext(){ if(nextT)clearTimeout(nextT); nextT=setTimeout(function(){ if(voiceMode && cur<SL.length-1) goTo(cur+1); },1100); }
    function goTo(n){ if(n<0||n>=SL.length)return; stopSpeak(); cur=n; render(); if(voiceMode) speakCur(); }
    bPrev.addEventListener("click",function(){ try{_tapFeedback();}catch(e){} goTo(cur-1); });
    bNext.addEventListener("click",function(){ try{_tapFeedback();}catch(e){} goTo(cur+1); });
    bPlay.addEventListener("click",function(){ try{_tapFeedback();}catch(e){}
      if(voiceMode){ voiceMode=false; stopSpeak(); updUI(); }
      else { voiceMode=true; updUI(); speakCur(); } });

    function cleanup(){ stopSpeak(); document.removeEventListener("visibilitychange",onVis); if(mo){mo.disconnect();mo=null;} }
    function closeDp(){ try{ ov.remove(); }catch(e){} /* MutationObserver dorovná cleanup */ }
    function onVis(){ if(document.hidden){ voiceMode=false; stopSpeak(); updUI(); } }
    document.addEventListener("visibilitychange",onVis);
    // Bezpečně zruš řeč při JAKÉMKOLI odebrání overlaye (✕ / hardware back přes .appmodal / render)
    mo=new MutationObserver(function(){ if(!document.body.contains(ov)) cleanup(); });
    try{ mo.observe(document.body,{childList:true}); }catch(e){}

    document.body.appendChild(ov);
    render();
  }
  function dochazka(){
    app.innerHTML=topbar("", false, true);  // Marti 7.6.: bez nadpisu a šipky; prázdná lišta drží odsazení
    var p=el('<div class="panel"></div>');
    // Marti 16.6.: docházka běží i v PWA (web) přes cookie auth — gate na nativní appku zrušen.
    // Marti 7.6. večer: „Dnes" logicky nahoru — obrazovka KONČÍ kartou
    // „Potřebuji ti něco říct…". Nadpis „Dnes makám 😉“ při běžící směně.
    // Nápověda (Jirka 26.6.): ❓ vpravo nahoře → kompletní návod docházky.
    var _hb=el('<div style="display:flex;justify-content:flex-end;margin:-6px 0 2px;"><button class="ghost" style="margin:0;width:auto;padding:6px 14px;font-size:13px;border-radius:18px;">❓ Nápověda</button></div>');
    _hb.querySelector("button").addEventListener("click",function(){ try{_tapFeedback();}catch(e){} dochHelp(); });
    p.appendChild(_hb);
    p.appendChild(el('<div id="dochHead" style="display:none;font-size:24px;font-weight:800;margin:6px 0 12px;">Dnes makám 😉</div>'));
    // Marti 14.6.: region nástrojů ve stylu sekce „Vedení" — JEN ikony v grupách
    // (BEZ rozbalovací hlavičky). Zobrazí se, KDYŽ ČLOVĚK NEMAKÁ. Časové sekce jsou
    // defaultně schované a odkrývají se až přes ikonu → pod ikonami zůstane jen
    // „Potřebuji ti něco říct".
    function _openSec(s){
      if(!s||!s.box) return;
      var li=s.box.parentNode; if(li) li.style.display="";   // řádek mohl být schovaný → odkrýt
      if(s.box.style.display==="none"){ var h=s.ttl&&s.ttl.parentNode; if(h)h.click(); }
      try{ s.box.scrollIntoView({behavior:"smooth",block:"center"}); }catch(e){}
    }
    var _toolsWrap=el('<div id="dochTools" style="display:none;margin:0 0 6px;"></div>');
    function _toolSec(t){ _toolsWrap.appendChild(el('<div style="margin:10px 6px 6px;font-size:12px;font-weight:700;letter-spacing:.5px;color:#7c8cdb;">'+t+'</div>')); }
    _toolSec("MOJE DOCHÁZKA");
    var _tg1=el('<div class="appgrid"></div>');
    _tg1.appendChild(appCell("📅","Dnešek",0,function(){ go("doch_dnesek"); }));
    var _wkNum=_isoWeek(new Date());
    var _tydCell=appCell("📅","Týden",0,function(){ window._planInit="thisweek"; go("plan"); });
    _tydCell.style.position="relative";
    _tydCell.appendChild(el('<span style="position:absolute;top:-4px;right:8px;background:#3a4d6b;color:#cfe0ff;border-radius:8px;min-width:18px;height:16px;line-height:16px;text-align:center;font-size:10px;font-weight:700;padding:0 4px;">'+_wkNum+'</span>'));
    _tg1.appendChild(_tydCell);
    var _vyhledCell=appCell("🔭","Výhled",0,function(){ window._planInit="myplan"; go("plan"); });
    _tg1.appendChild(_vyhledCell);
    (function _planPendingBadge(){
      var f=_locDate(-365), t=_locDate(365);
      api("GET","/api/v1/erp/app/plan/requests?from="+f+"&to="+t,"").then(function(rq){
        var n=(((rq&&rq.items)||[]).filter(function(r){ return r&&r.status==='pending'; })).length;
        var old=_vyhledCell.querySelector('.appbadge'); if(old) old.remove();
        if(n>0){ _vyhledCell.appendChild(el('<span class="appbadge" style="background:#f59e0b;">'+(n>99?"99+":n)+'</span>')); }
      }).catch(function(){});
    })();
    _tg1.appendChild(appCell("🕓","Historie",0,function(){ go("doch_historie"); }));
    _tg1.appendChild(appCell("📦","Po zakázkách",0,function(){ openInApp("/moje-dochazka"); }));
    _tg1.appendChild(appCell("📋","Moje žádosti",0,function(){ go("moje_zadosti"); }));
    // Jirka 21.7. (podnět Peťa): cesta k opravě i po potvrzení dne.
    _tg1.appendChild(appCell("✋","Požádat o opravu",0,function(){ go("doch_oprava_zadost"); }));
    _tg1.appendChild(appCell("🧭","Tady budu jinde",0,function(){
      var jb=document.getElementById("dochJindeBox"); if(!jb) return;
      if(jb.style.display!=="none"){ jb.style.display="none"; return; }
      jb.style.display="block";
      if(!jb._built && typeof window._dochJinde==="function"){ window._dochJinde(jb); jb._built=true; }
      try{ jb.scrollIntoView({behavior:"smooth",block:"center"}); }catch(e){}
    }));
    _toolsWrap.appendChild(_tg1);
    // Marti 14.6.: „Tady budu jinde" přesunuto z „Potřebuji ti něco říct" SEM (do docházky).
    var _jindeBox=el('<div id="dochJindeBox" style="display:none;margin:4px 4px 6px;padding:8px;border:1px solid #4a3a1a;border-radius:12px;background:rgba(251,191,36,.05);"></div>');
    _toolsWrap.appendChild(_jindeBox);
    // Marti 14.6.: sekce „Zakázky a činnosti" se renderuje NAHOŘE pod nadpisem
    // (v dochAction přes window._buildWorkSwitch) — tady už není.
    _toolSec("PODMÍNKY & FINANCE");
    var _tg2=el('<div class="appgrid"></div>');
    _tg2.appendChild(appCell("📋","Moje podmínky",0,function(){ go("moje_podminky"); }));
    _tg2.appendChild(appCell("📐","Můj úvazek",0,function(){ window._planInit="uvazek"; go("plan"); }));
    _tg2.appendChild(appCell("👤","Můj plán",0,function(){ window._planInit="myplan"; go("plan"); }));
    _tg2.appendChild(appCell("💰","Moje finance",0,function(){ go("moje_finance"); }));
    _tg2.appendChild(appCell("🗓️","Nepřítomnosti",0,function(){ go("absence"); }));
    _toolsWrap.appendChild(_tg2);
    // 🛠 Opravy docházky (Jirka 9.7.2026, zadal Marti): sekce JEN pro editory
    // (staff_group DOCHÁZKA - OPRAVY). Mimo _toolsWrap — editor ji vidí i když
    // sám zrovna maká. Badge = počet položek fronty K vyřešení.
    var _fixSec=el('<div id="dochFixSec" style="display:none;margin:2px 0 6px;"></div>');
    _fixSec.appendChild(el('<div style="margin:10px 6px 6px;font-size:12px;font-weight:700;letter-spacing:.5px;color:#7c8cdb;">SPRÁVA DOCHÁZKY</div>'));
    var _fixGrid=el('<div class="appgrid"></div>');
    var _fixCell=appCell("🛠","Opravy docházky",0,function(){ go("doch_opravy"); });
    _fixGrid.appendChild(_fixCell); _fixSec.appendChild(_fixGrid);
    (function _fixGate(){
      function show(n){ _fixSec.style.display="block"; var old=_fixCell.querySelector('.appbadge'); if(old)old.remove();
        if(n>0)_fixCell.appendChild(el('<span class="appbadge" style="background:#f59e0b;">'+(n>99?"99+":n)+'</span>')); }
      // Jirka 21.7.: dlaždici vidí editor (can_fix) I držitel zámku bez editorství
      // (can_lock — Šárka, rodiče). Lock-only nemá frontu → badge 0. Parita s ERP,
      // kde je gate can_fix||can_lock. Bez tohoto se Šárka/rodič na mobilu k zámku nedostal.
      if(window._canFixDoch===false&&window._canLockDoch===false) return;
      if(window._canFixDoch===true||window._canLockDoch===true){ show(window._canFixDoch?(window._fixQueueN||0):0); }
      api("GET","/api/v1/erp/app/attendance/fix/allowed","").then(function(j){
        window._canFixDoch=!!(j&&j.ok&&j.can_fix);
        window._canLockDoch=!!(j&&j.ok&&j.can_lock);
        if(!window._canFixDoch&&!window._canLockDoch){ _fixSec.style.display="none"; return; }
        show(window._canFixDoch?(window._fixQueueN||0):0);
        if(window._canFixDoch){
          api("GET","/api/v1/erp/app/attendance/fix/queue","").then(function(q){
            if(q&&q.ok){ window._fixQueueN=((q.anomalie||[]).length+(q.rozpory||[]).length); show(window._fixQueueN); }
          }).catch(function(){});
        }
      }).catch(function(){});
    })();
    // Marti 14.6.: pořadí obrazovky — nadpis → sekce Zakázky a činnosti (dochAction)
    // → „Potřebuji ti něco říct" (dochNow) → optická mezera → zbytek (region + sekce).
    p.appendChild(el('<div id="dochAction" style="margin-top:12px;"></div>'));
    p.appendChild(el('<div id="dochNow" class="doch-pulse" style="margin-top:12px;background:rgba(79,142,247,.07);border:1px solid #2a4d80;border-radius:14px;padding:14px;">Načítám…</div>'));
    p.appendChild(el('<div style="height:30px;"></div>'));  // optická mezera, ať to neruší
    p.appendChild(_toolsWrap);
    p.appendChild(_fixSec);  // 🛠 Opravy docházky — viditelné editorům vždy (i při běžící směně)
    var lc=el('<div style="margin-top:4px;"><ul id="dochSecs" style="list-style:none;padding:0;margin:0;"></ul></div>');
    var su=lc.querySelector("#dochSecs");
    // Marti 7.6. večer: lidské názvy sekcí — docházka mluví jako kolega.
    _dS={ today: collSec(su,"Dneska je den…", false),
          todayhist: collSec(su,"Tak to bylo dneska…", false),
          yest:  collSec(su,"Na včera si vzpomínám…", false),
          prev:  collSec(su,"To už si moc nepamatuju… (starší)", false),
          plan:  collSec(su,"Tak tady budu jinde…", false),
          paska: collSec(su,"Moje odmakané prašule… 💰", false, function(o){ paskaToggle(o); }) };
    _dS.todayhist.box.innerHTML='<div style="display:flex;gap:10px;height:46vh;align-items:stretch;"><div style="flex:1;min-width:0;overflow-y:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none;border:1px solid var(--bord);border-radius:12px;background:rgba(255,255,255,0.02);padding:2px 8px;"><ul id="dochToday2" style="padding:0;list-style:none;margin:0;"><li style="color:var(--mut);border:none;">Načítám…</li></ul></div><div id="dochTodayRail" style="width:72px;flex:none;overflow-y:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none;display:flex;flex-direction:column;gap:7px;padding:0;"></div></div>';
    _dS.today.box.innerHTML='<div id="dochSpanToday" style="font-size:13px;color:var(--mut);margin:2px 0 6px;display:none;"></div><div id="dochCard" style="padding:2px 0 4px;">Načítám…</div>';
    _dS.yest.box.innerHTML='<div id="dochSpanYest" style="font-size:13px;color:var(--mut);margin:2px 0 6px;display:none;"></div><div style="display:flex;gap:10px;height:42vh;align-items:stretch;"><div style="flex:1;min-width:0;overflow-y:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none;border:1px solid var(--bord);border-radius:12px;background:rgba(255,255,255,0.02);padding:2px 8px;"><ul id="dochYest2" style="padding:0;list-style:none;margin:0;"><li style="color:var(--mut);border:none;">Načítám…</li></ul></div><div id="dochYestRail" style="width:72px;flex:none;overflow-y:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none;display:flex;flex-direction:column;gap:7px;padding:0;"></div></div>';
    _dS.prev.box.innerHTML='<div style="display:flex;gap:10px;height:42vh;align-items:stretch;"><div style="flex:1;min-width:0;overflow-y:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none;border:1px solid var(--bord);border-radius:12px;background:rgba(255,255,255,0.02);padding:2px 8px;"><ul id="dochPrev2" style="padding:0;list-style:none;margin:0;"><li style="color:var(--mut);border:none;">Načítám…</li></ul></div><div id="dochPrevRail" style="width:72px;flex:none;overflow-y:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none;display:flex;flex-direction:column;gap:7px;padding:0;"></div></div>';
    _dS.plan.box.innerHTML='<div style="display:flex;gap:10px;height:42vh;align-items:stretch;"><div style="flex:1;min-width:0;overflow-y:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none;border:1px solid var(--bord);border-radius:12px;background:rgba(255,255,255,0.02);padding:2px 8px;"><ul id="dochPlan2" style="padding:0;list-style:none;margin:0;"><li style="color:var(--mut);border:none;">Načítám…</li></ul></div><div id="dochPlanRail" style="width:72px;flex:none;overflow-y:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none;display:flex;flex-direction:column;gap:7px;padding:0;"></div></div>';
    // Marti 7.6. večer: páska zamčená PINem + jen mimo směnu — souhrn v hlavičce
    // NIKDY neukazuje částku (🔒), obsah se načte až po odemčení při otevření.
    _dS.paska.box.innerHTML='<div id="paskaBox"><div class="hint">🔒 Páska je zamčená.</div></div>';
    // Marti 14.6.: časové sekce defaultně SCHOVANÉ — pod ikonami zůstane jen
    // „Potřebuji ti něco říct". Odkryjí se přes ikonu v regionu (Dnešek/Historie/…).
    // „Tak to bylo dneska“ (todayhist) skryté natrvalo (Marti: úplně schovat).
    try{ ["today","todayhist","yest","prev","plan","paska"].forEach(function(k){
      if(_dS[k]&&_dS[k].box&&_dS[k].box.parentNode) _dS[k].box.parentNode.style.display="none"; }); }catch(e){}
    // Marti 7.6. večer: pro tlačítko Zpět — zavření otevřeného menu/sekcí.
    window._dochAnyOpen=function(){
      if(!document.body.contains(su)){ window._dochMenuTs=0; return false; }  // jiná obrazovka
      // Marti 7.6. večer: Zpět zavírá i otevřený detail jobů schvalované docházky.
      var dbx=document.querySelector(".detbox");
      if(dbx){ dbx.remove(); return true; }
      if(window._dochMenuTs){ try{ if(window._dochCloseMenu) window._dochCloseMenu(); }catch(e){} window._dochMenuTs=0; return true; }
      // Marti 11.6.: rozkliknutý job „Tak to bylo dneska“ → Zpět zavře detail jobu
      // a zase ukáže pravou lištu (teprve další Zpět zavírá sekci).
      var _ojob=document.querySelector("#dochToday2 li.ct.open, #dochYest2 li.ct.open, #dochPrev2 li.ct.open, #dochPlan2 li.ct.open");
      if(_ojob){ var _oul=_ojob.parentNode; _ojob.classList.remove("open"); var _ojx=_ojob.querySelector(".ctexp"); if(_ojx)_ojx.style.display="none"; try{ var _lid=(_oul&&_oul.id)||"dochToday2"; _railSync(_lid.replace(/2$/,"")+"Rail",_lid); }catch(e){} return true; }
      var any=false;
      (su._secs||[]).forEach(function(sx){ if(sx.box && sx.box.style.display==="block"){ sx.close(); any=true; } });
      return any;
    };
    p.appendChild(lc);
    // Marti 14.6.: volná tlačítka „Požádat o absenci" + „Moje podmínky" přesunuta
    // do regionu „Moje docházka pod jednou střechou" nahoře (vše pod jednou střechou).
    // Marti 7.6. večer: okno odpovědi Marti-AI přímo v Docházce (nad rámečkem)
    // + karty dotazů pro nadřízeného (odpovídá rovnou z mobilu).
    p.appendChild(el('<div id="mmReply" style="display:none;margin-top:12px;background:rgba(79,142,247,.08);border:1px solid #2a4d80;border-radius:14px;padding:12px;"></div>'));
    p.appendChild(el('<div id="bossAsk"></div>'));
    // Marti 7.6. večer: konec obrazovky = zvýrazněný milý rámeček s rozhovorem.
    // Marti 7.6. večer: rámeček pulzuje NAPOŘÁD (líbí se mu to 😄) — při práci i mimo.
    p.appendChild(el('<div id="dochConfirm" style="margin-top:10px;"></div>'));
    p.appendChild(el('<div style="height:120px;"></div>'));  // rezerva pod patičku
    app.appendChild(p);
    _mmRender();  // čekající odpověď Marti-AI po překreslení zůstává vidět
    _bossAnswerCheck(); _bossPendingLoad();
    dochLoad();
  }
  function fmtHM(h){ var m=Math.round(Number(h||0)*60); var hh=Math.floor(m/60), mm=m%60; return hh+":"+(mm<10?"0":"")+mm; }
  function fmtDec(h){ return Number(h||0).toFixed(2).replace('.',','); }  // desetinné hodiny (5,90) — parita s ERP, Peťa 21.7.
  function dochLoad(){
    _dochViewUid=null;
    if(window._canManageVyroba===undefined){ window._canManageVyroba=false;
      api("GET","/api/v1/erp/app/vyroba/can-manage","").then(function(j){ window._canManageVyroba=!!(j&&j.ok&&j.can_manage); }); }
    api("GET","/api/v1/erp/app/attendance/status","").then(function(j){
      var cn=document.getElementById("dochNow"), c=document.getElementById("dochCard"); if(!cn||!c)return;
      if(!j||!j.ok){
        // Marti 11.6.: hláška je ťukací → nový pokus.
        cn.innerHTML='<div id="dochRetry" style="cursor:pointer;color:var(--amber);text-align:center;padding:6px 0;">⚠️ Nepodařilo se načíst. <b>Ťukni a zkusím to znovu.</b></div>';
        var _rt=document.getElementById("dochRetry"); if(_rt) _rt.addEventListener("click",function(){ try{_tapFeedback();}catch(e){} cn.textContent="Načítám…"; dochLoad(); });
        c.textContent="—"; return;
      }
      var open=j.open;
      // Marti 7.6. večer: při směně schovat vše kromě Dnes — „Další věci…" 😉
      if(_dS){
        ["yest","prev","plan","paska"].forEach(function(k){
          if(_dS[k]&&_dS[k].box.parentElement) _dS[k].box.parentElement.style.display=open?"none":"";
        });
      }
      // Marti 7.6. večer: žádný status text v kartě — puntík je v sekci Dnes,
      // karta je jen milý rámeček s „Potřebuji ti něco říct…".
      cn.innerHTML="";
      // Marti 7.6.: klik na Příchod/Odchod rozbalí volby v lidské řeči;
      // „Ostatní…" = podsekce, „Jsem na cestě" = výběr času dorazím za cca.
      var bw=el('<div></div>');
      // Marti 7.6. večer: menu se nesmí zavřít pod rukama — každý dotyk
      // resetuje minutový timeout (tick překreslí až po minutě nečinnosti).
      bw.addEventListener("click",function(){ if(window._dochMenuTs) window._dochMenuTs=Date.now(); },true);
      function btnEl(label, cls){ return el('<button class="'+cls+' full" style="margin-top:8px;font-size:15px;text-align:left;">'+label+'</button>'); }
      // Fáze 1 schvalování (Marti 7.6.): nepotvrzené dny — karty + záchytka při příchodu.
      function czDayLabel(iso){ try{ var d=new Date(iso+"T12:00:00"); return d.toLocaleDateString("cs",{weekday:"long",day:"numeric",month:"numeric"}); }catch(e){ return iso; } }
      function renderConfirmList(container, days, after){
        container.innerHTML="";
        if(!days||!days.length){ if(after)after(); return; }
        var left=days.length;
        days.forEach(function(d){
          // Marti 7.6. večer: karta se MUSÍ nabízet — pulzuje jako rámeček rozhovoru.
          var card=el('<div class="doch-pulse" style="background:rgba(224,176,112,.10);border:1px solid #6e5326;border-radius:12px;padding:12px;margin-bottom:8px;"></div>');
          card.appendChild(el('<div style="font-weight:600;font-size:14.5px;">🖊 '+esc(czDayLabel(d.day))+' · '+esc(d.od||'?')+'–'+esc(d.do||'…')+' · '+fmtHM(d.hodin)+' <span style="color:var(--mut);font-weight:400;">('+d.zaznamu+' zázn.)</span></div>'));
          card.appendChild(el('<div class="hint" style="margin-top:4px;">Zkontroluj si den (detail v Posledních záznamech) a potvrď ho.</div>'));
          // Kontextový tip (Jirka 26.6.): jak potvrdit / co je rozpor.
          var _ch=el('<div style="margin-top:2px;"><span style="color:var(--blue);font-size:12px;cursor:pointer;">ⓘ Jak potvrdit den / co je rozpor?</span></div>');
          _ch.querySelector("span").addEventListener("click",function(){ dochHelp("potvrzeni"); });
          card.appendChild(_ch);
          var b=el('<button class="green full" style="margin-top:8px;">✓ Potvrzuji svou docházku</button>');
          b.addEventListener("click",function(){
            b.disabled=true;
            api("POST","/api/v1/erp/app/attendance/confirm-day",{day:d.day}).then(function(j){
              if(j&&j.ok){ card.remove(); left--; if(left<=0){ if(after) after(); else dochLoad(); } }
              else { b.disabled=false; }
            }).catch(function(){ b.disabled=false; });
          });
          card.appendChild(b);
          // Marti 7.6. večer: detail jednotlivých jobů — redukce času self-service,
          // cokoliv jiného = poznámka na záznam → kontrola docházky.
          var det=el('<button class="ghost full" style="margin-top:6px;">🔍 Raději chci vidět detaily…</button>');
          det.addEventListener("click",function(){
            var ex=card.querySelector(".detbox");
            if(ex){ ex.remove(); return; }
            var db2=el('<div class="detbox" style="margin-top:8px;border-left:2px solid var(--bord);padding-left:8px;"></div>');
            db2.innerHTML='<div class="hint">Načítám…</div>';
            card.appendChild(db2);
            api("GET","/api/v1/erp/app/attendance/day-detail?day="+d.day,"").then(function(jd){
              db2.innerHTML="";
              var es=(jd&&jd.entries)||[];
              if(!es.length){ db2.innerHTML='<div class="hint">Žádné záznamy.</div>'; return; }
              es.forEach(function(e2){
                var row=el('<div style="background:var(--bg);border:1px solid var(--bord);border-radius:10px;padding:10px;margin-bottom:8px;"></div>');
                function hdrHtml(){ return esc((e2.zac||"?")+(e2.kon?(" – "+e2.kon):" – …"))+(e2.hours!=null?(' · '+fmtHM(e2.hours)):'')+(e2.project_ref?(' · 🧾 '+esc(e2.project_ref)):''); }
                var hd2=el('<div style="font-size:13.5px;font-weight:600;">'+hdrHtml()+'</div>');
                row.appendChild(hd2);
                if(e2.note) row.appendChild(el('<div class="hint" style="margin-top:2px;">'+esc(e2.note)+'</div>'));
                var ar=el('<div style="display:flex;gap:8px;margin-top:8px;flex-wrap:wrap;"></div>');
                var bt=el('<button class="ghost sm" style="border-color:var(--green);color:var(--green);">⏱ Zkrátit konec</button>');
                var bz=el('<button class="ghost sm" style="border-color:var(--blue);color:var(--blue);">🧾 Zakázka…</button>');
                var bx2=el('<button class="ghost sm" style="border-color:var(--amber);color:var(--amber);">✋ Nesedí…</button>');
                ar.appendChild(bt); ar.appendChild(bz); ar.appendChild(bx2); row.appendChild(ar);
                var fx=el('<div style="margin-top:6px;"></div>'); row.appendChild(fx);
                // Marti 7.6. večer: špatná zakázka = realita — změna přímo na jobu.
                bz.addEventListener("click",function(){
                  fx.innerHTML="";
                  fx.appendChild(el('<div class="hint" style="margin-bottom:4px;">Správná zakázka (teď: '+esc(e2.project_ref||"žádná")+'):</div>'));
                  var si2=el('<input placeholder="🔍 číslo nebo název…" autocomplete="off">');
                  var res2=el('<div style="margin-top:6px;"></div>');
                  var st4=el('<div class="hint" style="margin-top:4px;"></div>');
                  var tmr2=null;
                  function zload(){
                    var q=(si2.value||"").trim();
                    api("GET","/api/v1/erp/app/zakazky"+(q?("?q="+encodeURIComponent(q)):""),"").then(function(jz){
                      res2.innerHTML="";
                      ((jz&&jz.zakazky)||[]).forEach(function(z){
                        var zb2=el('<button class="ghost full" style="margin-top:6px;font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;text-align:left;">'+((z.typ==="REZIE")?"🧰 ":"🧾 ")+esc(z.cislo)+' — '+esc(z.nazev||"")+'</button>');
                        zb2.addEventListener("click",function(){
                          zb2.disabled=true; st4.textContent="⏳ Měním na "+z.cislo+"…";
                          api("POST","/api/v1/erp/app/attendance/entry-project",{id:e2.id,project_ref:z.cislo}).then(function(r){
                            // Marti 7.6. večer: detail nezavírat, ale seznam zakázek po výběru ano.
                            if(r&&r.ok){ e2.project_ref=z.cislo; hd2.innerHTML=hdrHtml(); try{si2.remove();res2.remove();}catch(e){} st4.textContent="✅ Zakázka změněna na "+z.cislo; }
                            else{ zb2.disabled=false; st4.textContent="✗ "+((r&&r.error)||"Nepodařilo se."); }
                          });
                        });
                        res2.appendChild(zb2);
                      });
                    });
                  }
                  si2.addEventListener("input",function(){ clearTimeout(tmr2); tmr2=setTimeout(zload,300); });
                  fx.appendChild(si2); fx.appendChild(res2); fx.appendChild(st4); zload();
                });
                bt.addEventListener("click",function(){
                  fx.innerHTML="";
                  if(!e2.kon){ fx.innerHTML='<div class="hint">Běžící záznam — nejdřív se odpíchni.</div>'; return; }
                  fx.appendChild(el('<div class="hint" style="margin-bottom:4px;">Nový konec (původně '+esc(e2.kon)+'):</div>'));
                  var ti=el('<input type="time" value="'+esc(e2.kon)+'" style="width:120px;">');
                  var ok2=el('<button class="green sm" style="margin-left:8px;">Uložit</button>');
                  var st2=el('<div class="hint" style="margin-top:4px;"></div>');
                  ok2.addEventListener("click",function(){
                    if(!ti.value){ st2.textContent="Vyber prosím čas."; return; }
                    // Marti 7.6. večer: potvrzení před zápisem.
                    fx.querySelectorAll(".trimconf").forEach(function(x){x.remove();});
                    var cw=el('<div class="trimconf" style="margin-top:6px;background:rgba(16,185,129,.10);border:1px solid var(--green);border-radius:8px;padding:10px;"></div>');
                    cw.appendChild(el('<div style="font-size:14px;">Opravdu zkrátit konec z <b>'+esc(e2.kon)+'</b> na <b>'+esc(ti.value)+'</b>?</div>'));
                    var br=el('<div style="display:flex;gap:8px;margin-top:8px;"></div>');
                    var ano=el('<button class="green sm" style="flex:1;">Ano, zkrátit</button>');
                    var ne=el('<button class="ghost sm">Ne</button>');
                    br.appendChild(ano); br.appendChild(ne); cw.appendChild(br); fx.appendChild(cw);
                    ne.addEventListener("click",function(){ cw.remove(); });
                    ano.addEventListener("click",function(){
                      ano.disabled=true; ne.disabled=true; st2.textContent="⏳ Ukládám…";
                      api("POST","/api/v1/erp/app/attendance/entry-trim",{id:e2.id,end:ti.value}).then(function(r){
                        if(r&&r.ok){ st2.textContent="✅ Zkráceno — přepočítávám den…"; setTimeout(dochLoad,700); }
                        else{ ano.disabled=false; ne.disabled=false; st2.textContent="✗ "+((r&&(r.error||JSON.stringify(r)))||"Bez odpovědi serveru."); }
                      });
                    });
                  });
                  fx.appendChild(ti); fx.appendChild(ok2); fx.appendChild(st2);
                });
                bx2.addEventListener("click",function(){
                  fx.innerHTML="";
                  var ta2=el('<textarea rows="2" placeholder="Co je na tomhle záznamu špatně?" style="width:100%;background:#0f1620;border:1px solid var(--bord);border-radius:8px;padding:10px;color:var(--tx);font-size:14px;font-family:inherit;"></textarea>');
                  var ok3=el('<button class="ghost full" style="margin-top:6px;border-color:var(--amber);color:var(--amber);">Odeslat kontrole docházky</button>');
                  var st3=el('<div class="hint" style="margin-top:4px;"></div>');
                  ok3.addEventListener("click",function(){
                    var n=(ta2.value||"").trim(); if(!n){ st3.textContent="Napiš prosím, co nesedí."; return; }
                    ok3.disabled=true;
                    api("POST","/api/v1/erp/app/attendance/entry-dispute",{id:e2.id,note:n}).then(function(r){
                      if(r&&r.ok){ fx.innerHTML='<div class="hint">✋ Nahlášeno — kontrola docházky se ozve.</div>'; setTimeout(dochLoad,1600); }
                      else{ ok3.disabled=false; st3.textContent="✗ "+((r&&r.error)||"Nepodařilo se."); }
                    });
                  });
                  fx.appendChild(ta2); fx.appendChild(ok3); fx.appendChild(st3);
                });
                db2.appendChild(row);
              });
              var zb=el('<button class="ghost full" style="margin-top:2px;">▲ Zpět</button>');
              zb.addEventListener("click",function(){ db2.remove(); });
              db2.appendChild(zb);
            });
          });
          card.appendChild(det);
          // Marti 7.6. večer: denní „Něco mi tu nesedí" zrušeno — rozpor se
          // hlásí na konkrétním jobu v detailech (a stejně odblokuje práci).
          container.appendChild(card);
        });
      }
      function act(ep, payload, b, after){
        b.disabled=true;
        api("POST","/api/v1/erp/app/attendance/"+ep,payload).then(function(j){
          if(j&&j.need_confirm&&j.need_confirm.length){
            bw.innerHTML="";
            bw.appendChild(el('<div class="hint" style="margin:4px 0 6px;">🖊 Nejdřív si potvrď předchozí docházku — pak tě hned píchnu:</div>'));
            var cc=el('<div></div>'); bw.appendChild(cc);
            renderConfirmList(cc, j.need_confirm, function(){
              api("POST","/api/v1/erp/app/attendance/"+ep,payload).then(function(){ if(after)after(); else dochLoad(); }).catch(function(){ dochLoad(); });
            });
            var z=el('<button class="ghost full" style="margin-top:6px;">Zrušit</button>');
            z.addEventListener("click",mainBtn); bw.appendChild(z);
            // Marti 7.6. večer: karty ke schválení hned na oči — scroll nahoru.
            setTimeout(function(){ try{ bw.scrollIntoView({behavior:"smooth",block:"start"}); }catch(e){} },60);
            return;
          }
          if(j&&j.ec_closed>0){ try{ alert("✅ Píchnuto v appce.\n\n⚠️ Ve starém systému (Centrála / tablet) jsme ti běžící píchnutí teď ukončili.\nOd teď se píchej JEN v této appce — ve starém systému už se nepřihlašuj."); }catch(e){} }
          if(after) after(); else dochLoad();
        }).catch(function(){ b.disabled=false; });
      }
      function mainBtn(){
        // Marti 7.6.: není to „odchod/příchod", je to změna činnosti — rozhovor.
        window._dochMenuTs=0;
        bw.innerHTML="";
        // Marti 10.6.: časované/přerušené statusy → Konec|Prodloužit do dochAction
        // (NAD pulzující rámeček), „Potřebuji ti něco říct" zůstává v rámečku sám.
        var actC=document.getElementById("dochAction"); if(actC) actC.innerHTML="";
        var _ann=(j.announced||""), tsKind=null, tsMode=null;
        if(open){
          if(/jedn[aá]n[ií]/i.test(_ann)){ tsKind="jednání"; tsMode="clear"; }
          else if(/poch[uů]z/i.test(_ann)){ tsKind="pochůzku"; tsMode="clear"; }
        } else {
          if(/pauz/i.test(_ann)){ tsKind="pauzu"; tsMode="resume"; }
          else if(/relaxuj|energii|naj[ií]st|ob[ěe]d/i.test(_ann)){ tsKind="přestávku"; tsMode="resume"; }
        }
        if(tsKind && actC){
          var _et=_parseEndTime(_ann);
          if(_et && _isPast(_et, _parseStartTime(_ann))) actC.appendChild(el('<div style="color:var(--amber);background:#241c0a;border:1px solid var(--amber);border-radius:10px;padding:10px 12px;margin-bottom:8px;font-size:14px;">⏰ Mělo skončit v '+_et+'. Skončilo už?</div>'));
          if(tsMode==="clear"){
            var rowB=el('<div style="display:flex;gap:8px;"></div>');
            var ke=el('<button class="green full" style="flex:1;margin:0;font-weight:700;background:var(--amber);color:#241a02;">✅ Konec</button>');
            ke.addEventListener("click",function(){ ke.disabled=true; api("POST","/api/v1/erp/app/attendance/clear-announce","").then(function(){ dochLoad(); }).catch(function(){ ke.disabled=false; }); });
            var pp=el('<div style="display:none;margin-top:8px;"></div>'); buildProlong(pp, tsKind);
            var pe=el('<button class="green full" style="flex:1;margin:0;font-weight:700;background:var(--blue);color:#fff;">⏱ Prodloužit</button>');
            pe.addEventListener("click",function(){ pp.style.display=(pp.style.display==="none")?"block":"none"; });
            rowB.appendChild(ke); rowB.appendChild(pe); actC.appendChild(rowB); actC.appendChild(pp);
          } else {
            var ke2=el('<button class="green full" style="margin:0;font-weight:700;background:var(--amber);color:#241a02;">✅ Konec '+(tsKind==="pauzu"?"pauzy":(tsKind==="přestávku"?"přestávky":tsKind))+' — jsem zpět</button>');
            ke2.addEventListener("click",function(){ ke2.disabled=true; act("checkin",{kind:"work"},ke2); });
            actC.appendChild(ke2);
          }
        }
        // Marti 14.6.: sekce „Zakázky a činnosti" pod nadpisem (vždy — i mimo práci),
        // ZVLÁŠŤ nad pulzujícím rámečkem „Potřebuji ti něco říct" (ten patří jen svému poli).
        if(actC && window._buildWorkSwitch){ window._buildWorkSwitch(actC); }
        // Marti 14.6.: on-shift volba „Jsem na zakázce" ÚPLNĚ SCHOVÁNA — patří do
        // sekce „Moje zakázky" (region). „Potřebuji ti něco říct" zůstává v rámečku sám.
        if(false && open && actC){
          var _zr=(open&&open.project_ref)||"";
          var _zic=(open&&open.project_type==="REZIE")?"🧾":"👷";  // delník s helmou / režijní papír
          expOpt(actC,_zic+" Jsem na zakázce…","green",zakBuild,function(b){ b.style.background="#3b5bdb"; b.style.color="#fff"; b.style.borderColor="#3b5bdb";
            b.style.display="flex"; b.style.justifyContent="space-between"; b.style.alignItems="center"; b.style.textAlign="left";
            b.innerHTML='<span>'+_zic+' Jsem na zakázce…</span>'+(_zr?('<span style="font-weight:700;white-space:nowrap;">'+esc(_zr)+'</span>'):''); });
        }
        // Marti 14.6.: NAD „Potřebuji ti něco říct" sekce rychlých stavů vedoucímu
        // výroby (Informuji/Makám/Potřebuji/Finišuji/Čekám) — dlaždice jako ve Vedení.
        // PARKOVÁNO (Marti 14.6.: „na rychlé stavy ještě nejsme ready") — kód zůstává,
        // jen se nezobrazuje. „Potřebuji ti něco říct" zůstává samo ve svém rámečku.
        if(false && open){
          bw.appendChild(el('<div style="margin:2px 6px 6px;font-size:12px;font-weight:700;letter-spacing:.5px;color:#7c8cdb;">RYCHLÝ STAV VEDOUCÍMU</div>'));
          var _sg=el('<div class="appgrid"></div>');
          var _fbPanel=function(build){ bw.innerHTML=""; var bk=el('<button class="ghost full" style="margin-bottom:8px;">‹ Zpět</button>'); bk.addEventListener("click",mainBtn); bw.appendChild(bk); var box=el('<div></div>'); bw.appendChild(box); build(box); try{ bw.scrollIntoView({behavior:"smooth",block:"start"}); }catch(e){} };
          var _fbQuick=function(pref,typ,okmsg){ return function(){ _fbPanel(function(box){ box.appendChild(el('<div class="hint" style="margin-bottom:6px;">Pošle se rovnou vedoucímu výroby.</div>')); var ta=el('<textarea rows="2" style="width:100%;background:#0f1620;border:1px solid #2a3a4d;border-radius:10px;padding:11px;color:var(--tx);font-size:15px;font-family:inherit;">'+pref+'</textarea>'); box.appendChild(ta); var sb=el('<button class="green full" style="margin-top:8px;">Odeslat →</button>'); sb.addEventListener("click",function(){ var t=(ta.value||"").trim(); if(!t){ ta.focus(); return; } sb.disabled=true; api("POST","/api/v1/erp/app/vyroba/zprava",{text:t,typ:typ}).then(function(r){ if(r&&r.ok){ box.innerHTML='<div class="hint" style="color:var(--green);padding:6px 0;">'+okmsg+'</div>'; setTimeout(mainBtn,1200); } else { sb.disabled=false; alert("Chyba: "+((r&&r.error)||"?")); } }); }); box.appendChild(sb); }); }; };
          _sg.appendChild(appCell("💡","Informuji",0,_fbQuick("","info","✅ Informace odeslána. Díky!")));
          _sg.appendChild(appCell("👷","Makám",0,_fbQuick("Makám 👷, vše OK","info","✅ Odesláno. Díky!")));
          _sg.appendChild(appCell("🙋","Potřebuji",0,_fbQuick("","pozadavek","✅ Požadavek odeslán vedoucímu.")));
          _sg.appendChild(appCell("🏁","Finišuji",0,function(){ _fbPanel(vyrobaFinishBuild); }));
          _sg.appendChild(appCell("🥱","Čekám",0,_fbQuick("Čekám na práci — mám volnou kapacitu 🥱","pozadavek","✅ Vedoucí ví, že čekáš.")));
          bw.appendChild(_sg);
        }
        // Marti 7.6. večer: zelené v obou stavech, bublina vpravo.
        var btn=el('<button class="green full" style="font-size:16px;display:flex;justify-content:space-between;align-items:center;text-align:left;"><span>Potřebuji ti něco říct…</span><span>💬</span></button>');
        btn.addEventListener("click",showOpts);
        bw.appendChild(btn);
        // Kontextový tip (Jirka 26.6.): rychlá nápověda k příchodu/odchodu.
        var _tip=el('<div style="text-align:right;margin-top:4px;"><span style="color:var(--mut);font-size:12px;cursor:pointer;">ⓘ Jak na příchod, pauzu, odchod?</span></div>');
        _tip.querySelector("span").addEventListener("click",function(){ dochHelp("prichod"); });
        bw.appendChild(_tip);
      }
      function addOpts(defs, cls){
        defs.forEach(function(o){
          var b=btnEl(o[0], cls);
          b.addEventListener("click",function(){ o[1](b); });
          bw.appendChild(b);
        });
      }
      // Marti 7.6. večer: rozbalování NA MÍSTĚ jako Kontakty — tlačítko + obsah
      // hned pod ním, v rámci jedné úrovně max jedno otevřené. Žádné přepínání
      // celých obrazovek, žádná tlačítka Zpět (zavře se ťuknutím na volbu znovu).
      function expOpt(parent, label, cls, build, style){
        var b=btnEl(label, cls);
        if(style) style(b);
        var box=el('<div style="display:none;margin:6px 0 4px 10px;border-left:2px solid var(--bord);padding-left:8px;"></div>');
        b.addEventListener("click",function(){
          var isOpen=box.style.display!=="none";
          (parent._exps||[]).forEach(function(x){ x.style.display="none"; });
          if(!isOpen){ box.innerHTML=""; box._exps=null; build(box, b); box.style.display="block"; }
        });
        parent.appendChild(b); parent.appendChild(box);
        parent._exps=parent._exps||[]; parent._exps.push(box);
        return b;
      }
      // Chips „za jak dlouho" do boxu → fn(min, btn); volitelný vlastní seznam
      function chipsIn(box, label, fn, list){
        box.appendChild(el('<div class="hint" style="margin:4px 0 2px;">'+label+'</div>'));
        var c=el('<div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:6px;"></div>');
        (list||[["15 min",15],["30 min",30],["45 min",45],["1 h",60],["1,5 h",90],["2 h",120]]).forEach(function(o){
          var b=el('<button class="ghost sm" style="border-color:var(--blue);color:var(--blue);">'+o[0]+'</button>');
          b.addEventListener("click",function(){ b.disabled=true; fn(o[1], b); });
          c.appendChild(b);
        });
        box.appendChild(c);
      }
      // Výběr data do boxu → fn("YYYY-MM-DD", btn)
      function datePickIn(box, label, fn){
        box.appendChild(el('<div class="hint" style="margin:4px 0 2px;">'+label+'</div>'));
        var d=el('<input type="date" value="'+_locDate(0)+'" style="margin-top:6px;">');
        box.appendChild(d);
        var ok=el('<button class="green full" style="margin-top:8px;">Potvrdit</button>');
        ok.addEventListener("click",function(){ if(d.value){ ok.disabled=true; fn(d.value, ok); } });
        box.appendChild(ok);
      }
      function czDate(iso){ var p=(iso||"").split("-"); return p.length===3?(Number(p[2])+". "+Number(p[1])+"."):iso; }
      // Výběr rozsahu dat od–do do boxu → fn(od, do, btn)
      function dateRangePickIn(box, label, fn){
        box.appendChild(el('<div class="hint" style="margin:4px 0 2px;">'+label+'</div>'));
        var today=_locDate(0);
        var d1=el('<input type="date" value="'+today+'" style="margin-top:6px;">');
        var d2=el('<input type="date" value="'+today+'" style="margin-top:6px;">');
        box.appendChild(el('<label>Od</label>')); box.appendChild(d1);
        box.appendChild(el('<label>Do</label>')); box.appendChild(d2);
        var ok=el('<button class="green full" style="margin-top:10px;">Potvrdit</button>');
        ok.addEventListener("click",function(){ if(d1.value&&d2.value){ ok.disabled=true; fn(d1.value, d2.value, ok); } });
        box.appendChild(ok);
      }
      // Výběr dne + času „do kdy zhruba" do boxu → fn(datum, čas, btn) — lékař
      function dateTimePickIn(box, label, fn){
        box.appendChild(el('<div class="hint" style="margin:4px 0 2px;">'+label+'</div>'));
        var today=_locDate(0);
        var d=el('<input type="date" value="'+today+'" style="margin-top:6px;">');
        var t=el('<input type="time" style="margin-top:6px;">');
        box.appendChild(el('<label>Den</label>')); box.appendChild(d);
        box.appendChild(el('<label>Do kdy zhruba</label>')); box.appendChild(t);
        var ok=el('<button class="green full" style="margin-top:10px;">Potvrdit</button>');
        ok.addEventListener("click",function(){ if(d.value){ ok.disabled=true; fn(d.value, t.value||"", ok); } });
        box.appendChild(ok);
      }
      // Přímá akce do containeru (helper pro inline menu)
      function dirBtn(parent, label, cls, h, style){
        var b=btnEl(label, cls);
        if(style) style(b);
        b.addEventListener("click",function(){ h(b); });
        parent.appendChild(b);
        return b;
      }
      // 💼 Služební důvody — obsah (Marti 7.6. večer: podmenu modré jako parent)
      function sluzebniBuild(box){
        dirBtn(box,"🚙 Jedu rovnou k zákazníkovi…","ghost",function(b){ act("checkin",{kind:"trip"},b); },_blueStyle);
        dirBtn(box,"🎓 Jsem na školení…","ghost",function(b){ act("checkin",{kind:"work"},b,function(){ presence({text:"Jsem na školení"},{disabled:false}); }); },_blueStyle);
        dirBtn(box,"📦 Služební pochůzka, pak dorazím…","ghost",function(b){ presence({text:"Na služební pochůzce, pak dorazím",add_since:true},b); },_blueStyle);
        expOpt(box,"📝 Ostatní — napíšu důvod…","ghost",function(bx){
          var ta=el('<textarea rows="2" placeholder="Napiš důvod… (např. jednání na úřadě)" style="width:100%;background:#0f1620;border:1px solid var(--bord);border-radius:8px;padding:11px;color:var(--tx);font-size:15px;font-family:inherit;margin-top:6px;"></textarea>');
          var t=el('<input type="time" style="margin-top:6px;">');
          bx.appendChild(ta);
          bx.appendChild(el('<label>Vrátím se zhruba v</label>')); bx.appendChild(t);
          var st=el('<div class="hint" style="margin-top:6px;"></div>'); bx.appendChild(st);
          var ok=el('<button class="green full" style="margin-top:8px;">Potvrdit</button>');
          ok.addEventListener("click",function(){
            var d=(ta.value||"").trim();
            if(!d){ st.textContent="Napiš prosím důvod."; return; }
            ok.disabled=true;
            presence({text:d.substring(0,120),add_since:true,until_txt:(t.value?("~"+t.value):"")},ok);
          });
          bx.appendChild(ok);
        },_blueStyle);
      }
      // 🏠 Osobní důvody — obsah (Marti 7.6. večer: HO a zařizování první se
      // zeleným rámečkem, OČR třetí, zbytek jantarově; dovolená na konci).
      var _greenStyle=function(b){ b.style.borderColor="var(--green)"; b.style.color="var(--green)"; };
      function osobniBuild(box){
        expOpt(box,"🏡 Potřebuju makat z domova…","ghost",function(bx){
          dateRangePickIn(bx,"Home office od – do:",function(od, dd, b){
            var today=_locDate(0);
            absence({type_code:"homeoffice",date_from:od,date_to:dd,mode:"days",note:"home office (přes mobil)"},function(){
              if(od<=today && dd>=today){ presence({text:"Jsem na home office",add_since:false,until_txt:czDate(dd)},b); }
              else absOk(bx,"Home office "+czDate(od)+" – "+czDate(dd));
            },b);
          });
        },_greenStyle);
        expOpt(box,"🕐 Něco si zařizuji…","ghost",function(bx){
          chipsIn(bx,"Dorazím zhruba za:",function(m,b){ presence({text:"Něco si zařizuji, dorazím",add_since:false,eta_min:m},b); });
        },_greenStyle);
        expOpt(box,"👨‍👧 Zase řeším rodinu… (OČR)","ghost",function(bx){
          dateRangePickIn(bx,"OČR od – do:",function(od, dd, b){
            var today=_locDate(0);
            absence({type_code:"family_care",date_from:od,date_to:dd,mode:"days",note:"OČR (přes mobil)"},function(){
              if(od<=today && dd>=today){ presence({text:"Pečuji o rodinu (OČR)",add_since:false,until_txt:czDate(dd)},b); }
              else absOk(bx,"OČR "+czDate(od)+" – "+czDate(dd));
            },b);
          });
        },_amberStyle);
        expOpt(box,"🤒 Je mi blbě… sick day","ghost",function(bx){
          dirBtn(bx,"🤒 Dnes je mi blbě","ghost",function(b){
            b.disabled=true; var today=_locDate(0);
            absence({type_code:"sickday",date_from:today,date_to:today,mode:"days",note:"přes mobil — je mi blbě"},function(){
              presence({text:"Je mi blbě — sick day, dnes nedorazím",add_since:false},b); },b);
          },_amberStyle);
          bx.appendChild(el('<div class="hint" style="margin-top:8px;">…nebo sick day na konkrétní dny (i zpětně):</div>'));
          dateRangePickIn(bx,"Sick day od – do:",function(od, dd, b){
            var today=_locDate(0);
            absence({type_code:"sickday",date_from:od,date_to:dd,mode:"days",note:"sick day (přes mobil)"},function(){
              if(od<=today && dd>=today){ presence({text:"Je mi blbě — sick day",add_since:false,until_txt:czDate(dd)},b); }
              else absOk(bx,"Sick day "+czDate(od)+" – "+czDate(dd));
            },b);
          });
        },_amberStyle);
        expOpt(box,"🤧 Mám neschopenku do…","ghost",function(bx){
          datePickIn(bx,"Neschopenka do:",function(d,b){
            var today=_locDate(0);
            absence({type_code:"sick",date_from:today,date_to:d,mode:"days",note:"neschopenka (přes mobil)"},function(){
              presence({text:"Neschopenka",add_since:false,until_txt:czDate(d)},b); },b); });
        },_amberStyle);
        expOpt(box,"🩺 Jedu k lékaři…","ghost",function(bx){
          // Marti 7.6. večer: rychlé volby teď + hlášení dopředu (dny i měsíce).
          dirBtn(bx,"🩺 Nebojte, pak dorazím…","ghost",function(b){ presence({text:"Jsem u lékaře, pak dorazím",add_since:true},b); },_amberStyle);
          dirBtn(bx,"🩺 Nevidím to dnes dobře…","ghost",function(b){ presence({text:"U lékaře, dnes už nedorazím",add_since:false},b); },_amberStyle);
          bx.appendChild(el('<div class="hint" style="margin-top:8px;">…nebo hlásím dopředu:</div>'));
          dateTimePickIn(bx,"Den a do kdy zhruba nebudu:",function(d, t, b){
            var today=_locDate(0);
            absence({type_code:"medical",date_from:d,date_to:d,mode:"days",note:"u lékaře"+(t?(" do ~"+t):"")},function(){
              if(d===today){ presence({text:"Jsem u lékaře",add_since:false,until_txt:(t?("~"+t):"")},b); }
              else absOk(bx,"Lékař "+czDate(d));
            },b);
          });
        },_amberStyle);
        expOpt(box,"🌴 Že by dovolená?… 😎","ghost",function(bx){
          dateRangePickIn(bx,"Dovolená od – do:",function(od, dd, b){
            var today=_locDate(0);
            absence({type_code:"vacation",date_from:od,date_to:dd,mode:"days",note:"přes mobil"},function(){
              if(od<=today && dd>=today){ presence({text:"Mám dovolenou",add_since:false,until_txt:czDate(dd)},b); }
              else absOk(bx,"Dovolená "+czDate(od)+" – "+czDate(dd));
            },b);
          });
        },_amberStyle);
      }
      // 🧭 Tady budu asi jinde… — obsah (osobní jantarové jako parent, služební modré)
      function jindeBuild(box){
        expOpt(box,"🏠 Osobní důvody…","ghost",osobniBuild,_amberStyle);
        expOpt(box,"💼 Služební důvody…","ghost",sluzebniBuild,_blueStyle);
      }
      // Marti 14.6.: zpřístupnit „Tady budu jinde" regionu docházky (dlaždice volá).
      window._dochJinde=jindeBuild;
      // Píchnutí na zakázku (Marti 7.6.): picker nad tenant.zakazka (⚙ sync_zakazky).
      function zakBuild(box){
        try{ window.scrollTo({top:0,behavior:"smooth"}); }catch(e){ try{window.scrollTo(0,0);}catch(_){} }  // Marti 11.6.: odscrolovat nahoru
        box.appendChild(el('<div class="hint" style="margin:4px 0 2px;">Najdi zakázku (číslo / název):</div>'));
        var si=el('<input placeholder="🔍 např. VR106… nebo název" autocomplete="off" style="margin-top:6px;">');
        var res=el('<div style="margin-top:8px;"></div>');
        var tmr=null;
        function load(){
          var q=(si.value||"").trim();
          api("GET","/api/v1/erp/app/zakazky"+(q?("?q="+encodeURIComponent(q)):""),"").then(function(j){
            res.innerHTML="";
            function mkBtn(z,planned){
              // Marti 7.6. večer: Režie je taky zakázka — píchá se jako režie.
              var rez=(z.typ==="REZIE");
              var lbl=(planned?"📋 ":(rez?"🧰 ":"🧾 "))+z.cislo+" — "+(z.nazev||"")
                + (planned&&z.hodin!=null?(" ("+z.hodin+"h)"):"");
              var b=btnEl(lbl,"green");
              b.style.fontSize="13px"; b.style.whiteSpace="nowrap"; b.style.overflow="hidden"; b.style.textOverflow="ellipsis";
              if(planned){ b.style.boxShadow="inset 3px 0 0 var(--blue)"; }
              b.addEventListener("click",function(){
                // Marti 18.6.: výběr zakázky v docházce nastaví i pracovní výběr,
                // aby seznam činností odpovídal (Režie → režijní činnosti).
                api("POST", rez?"/api/v1/erp/app/work/set-rezie":"/api/v1/erp/app/work/set-zakazka", rez?{}:{project_ref:z.cislo,project_nazev:z.nazev||""}).catch(function(){});
                act("checkin",{kind:(rez?"overhead":"work"),project_ref:z.cislo,switch:true},b);
              });
              return b;
            }
            // Marti 8.6.: ruční přiřazení od vedoucího výroby — úplně nahoře (📌 + pokyn).
            var assigned=(j&&j.assigned)||[];
            if(!q && assigned.length){
              res.appendChild(el('<div class="hint" style="margin:2px 0 4px;color:#f59e0b;">📌 Od vedoucího výroby:</div>'));
              assigned.forEach(function(z){
                var b=btnEl("📌 "+z.cislo+" — "+(z.nazev||""),"green");
                b.style.fontSize="13px"; b.style.whiteSpace="nowrap"; b.style.overflow="hidden"; b.style.textOverflow="ellipsis";
                b.style.boxShadow="inset 3px 0 0 #f59e0b";
                b.addEventListener("click",function(){ act("checkin",{kind:"work",project_ref:z.cislo,switch:true},b); });
                res.appendChild(b);
                if(z.pokyn||z.kdy_ozvat){
                  res.appendChild(el('<div class="hint" style="margin:2px 0 9px 8px;font-size:12px;color:#cbd5e1;white-space:normal;">'
                    +(z.pokyn?('📋 '+esc(z.pokyn)):'')
                    +(z.kdy_ozvat?((z.pokyn?'<br>':'')+'⏰ ozvi se: '+esc(z.kdy_ozvat)):'')+'</div>'));
                }
              });
            }
            // Marti 8.6.: „Dnes naplánováno" z plánu výroby — nahoře, jen bez hledání.
            var planned=(j&&j.planned)||[];
            if(!q && planned.length){
              res.appendChild(el('<div class="hint" style="margin:2px 0 2px;color:var(--blue);">📋 Dnes naplánováno (z plánu výroby):</div>'));
              planned.forEach(function(z){ res.appendChild(mkBtn(z,true)); });
              res.appendChild(el('<div class="hint" style="margin:12px 0 2px;">Ostatní zakázky:</div>'));
            }
            var list=(j&&j.zakazky)||[];
            if(!list.length && !planned.length){ res.innerHTML='<div class="hint">Nic nenalezeno — zkus jiný text, nebo nech zakázky synchronizovat (⚙).</div>'; return; }
            list.forEach(function(z){ res.appendChild(mkBtn(z,false)); });
          });
        }
        si.addEventListener("input",function(){ clearTimeout(tmr); tmr=setTimeout(load,300); });
        box.appendChild(si); box.appendChild(res);
        load();
      }
      // Přímá zpráva (Marti 7.6.): text i audio, odpověď hned + notifikace.
      // Marti 7.6. večer: zelený rámeček „Jsem tu, tak povídej…", 🚀 + 🎙, scroll nahoru.
      function martiMsgBuild(box){
        var ta=el('<textarea rows="3" placeholder="Jsem tu, tak povídej…" style="width:100%;background:#0f1620;border:1px solid var(--green);box-shadow:0 0 0 2px rgba(16,185,129,.18);border-radius:10px;padding:11px;color:var(--tx);font-size:15px;font-family:inherit;"></textarea>');
        var brow=el('<div style="display:flex;gap:8px;margin-top:8px;"></div>');
        var send=el('<button class="green" style="flex:1;font-size:18px;">🚀</button>');
        var rec=el('<button class="ghost" style="width:64px;font-size:18px;border-color:var(--blue);color:var(--blue);">🎙</button>');
        setTimeout(function(){ try{ box.scrollIntoView({behavior:"smooth",block:"start"}); }catch(e){} },60);
        var st=el('<div class="hint" style="margin-top:8px;"></div>');
        // Marti 7.6. večer: scrollovací okno odpovědi + polling — odpověď dorazí
        // PŘÍMO sem do menu, i když to trvá déle (notifikace je jen bonus).
        var reply=el('<div style="display:none;margin-top:10px;background:rgba(79,142,247,.08);border:1px solid #2a4d80;border-radius:10px;padding:12px;font-size:14px;line-height:1.5;white-space:pre-wrap;max-height:45vh;overflow-y:auto;"></div>');
        function busy(t){ st.textContent=t; }
        var mmAfter=0;
        function showReply(txt){
          send.disabled=false; rec.disabled=false;
          reply.style.display="block"; reply.textContent=txt; ta.value="";
          try{ reply.scrollIntoView({behavior:"smooth",block:"nearest"}); }catch(e){}
        }
        function doSend(payload){
          busy("💭 Tvoje Marti přemýšlí…"); send.disabled=true; rec.disabled=true;
          api("GET","/api/v1/erp/app/marti-message/last","").then(function(b0){ mmAfter=(b0&&b0.id)||0; });
          api("POST","/api/v1/erp/app/marti-message",payload).then(function(j){
            if(j&&j.ok){
              busy("✅ Odpovězeno");
              showReply((payload.audio_b64&&j.transcript?("🎙 Rozuměla jsem: „"+j.transcript+"“\n\n"):"")+(j.reply||""));
            } else if(j&&j.error){ send.disabled=false; rec.disabled=false; busy("✗ "+j.error); }
            else { busy("⏳ Trvá to déle — odpověď se ukáže tady v Docházce…"); _mmStartPoll(mmAfter); }
          }).catch(function(){ busy("⏳ Trvá to déle — odpověď se ukáže tady v Docházce…"); _mmStartPoll(mmAfter); });
        }
        send.addEventListener("click",function(){ var t=(ta.value||"").trim(); if(t) doSend({text:t}); });
        var recState=null;
        function fileFallback(){
          var fi=el('<input type="file" accept="audio/*" capture style="display:none;">');
          fi.addEventListener("change",function(){
            var f=fi.files&&fi.files[0]; if(!f)return;
            if(f.size>6*1024*1024){ busy("✗ Nahrávka je moc velká (max ~6 MB)."); return; }
            var fr=new FileReader();
            fr.onload=function(){ doSend({audio_b64:String(fr.result).split(",")[1],mime:f.type||"audio/m4a",filename:f.name||"audio"}); };
            fr.readAsDataURL(f);
          });
          box.appendChild(fi); fi.click();
        }
        rec.addEventListener("click",function(){
          if(recState){ try{recState.stop();}catch(e){} return; }
          if(navigator.mediaDevices&&navigator.mediaDevices.getUserMedia&&window.MediaRecorder){
            navigator.mediaDevices.getUserMedia({audio:true}).then(function(stream){
              window.__micStream=stream;
              var chunks=[]; var mr=new MediaRecorder(stream);
              mr.ondataavailable=function(e){ if(e.data&&e.data.size)chunks.push(e.data); };
              mr.onstop=function(){
                stream.getTracks().forEach(function(t){t.stop();}); window.__micStream=null;
                rec.textContent="🎙"; recState=null;
                var blob=new Blob(chunks,{type:mr.mimeType||"audio/webm"});
                if(blob.size>6*1024*1024){ busy("✗ Nahrávka je moc dlouhá."); return; }
                var fr=new FileReader();
                fr.onload=function(){ doSend({audio_b64:String(fr.result).split(",")[1],mime:blob.type,filename:"mobil-audio.webm"}); };
                fr.readAsDataURL(blob);
              };
              mr.start(); recState=mr;
              rec.textContent="⏹"; busy("🔴 Nahrávám… (klepni ⏹)");
            }).catch(function(){ if(B){ busy("🎙 Povol prosím mikrofon a klepni znovu."); } else { fileFallback(); } });
          } else if(B){ busy("🎙 Mikrofon tu není dostupný."); }
          else { fileFallback(); }
        });
        box.appendChild(ta);
        brow.appendChild(send); brow.appendChild(rec); box.appendChild(brow);
        box.appendChild(st); box.appendChild(reply);
      }
      function presence(payload, b){ b.disabled=true; api("POST","/api/v1/erp/app/attendance/announce",payload).then(function(){ dochLoad(); }).catch(function(){ b.disabled=false; }); }
      // Jirka 27.6.: robustní nahlášení nepřítomnosti. Na chybu re-enable tlačítka
      // + viditelná hláška (dřív tlačítko Potvrdit zůstalo šedé = „nešlo zmáčknout").
      function absence(payload, then, btn){
        return api("POST","/api/v1/erp/app/attendance/absence",payload).then(function(r){
          if(r&&r.ok===false){ throw new Error(r.error||"nepovedlo se"); }
          if(then) then(r);
        }).catch(function(e){
          if(btn){ btn.disabled=false;
            if(btn.parentNode){ btn.parentNode.appendChild(el('<div class="hint" style="color:#f87171;margin-top:6px;">Nepovedlo se uložit ('+esc((e&&e.message)||"zkus to znovu")+'). Zkus to prosím ještě jednou.</div>')); } }
        });
      }
      // Zelené potvrzení nahlášené (budoucí) nepřítomnosti do boxu — ať uživatel ví, že to prošlo.
      function absOk(box, txt){
        if(box){ box.innerHTML=''; box.appendChild(el('<div class="hint" style="color:var(--green);margin:8px 4px;font-size:14px;line-height:1.5;">✓ '+esc(txt)+'<br>Díky, nahlásil/a jsi to — čeká to na schválení.</div>')); }
      }
      var _blueStyle=function(b){ b.style.borderColor="var(--blue)"; b.style.color="var(--blue)"; };
      var _amberStyle=function(b){ b.style.borderColor="var(--amber)"; b.style.color="var(--amber)"; };
      // Marti 7.6. večer: ohlášení dřívějšího konce / pozdějšího příchodu —
      // dnes i dopředu (den + čas), status se ukáže ten den.
      function _denCasBuild(bx, otazkaCas, textFn){
        var today=_locDate(0);
        bx.appendChild(el('<div class="hint" style="margin-bottom:2px;">Který den?</div>'));
        var dI=el('<input type="date" value="'+today+'">');
        bx.appendChild(dI);
        bx.appendChild(el('<div class="hint" style="margin:6px 0 2px;">'+otazkaCas+'</div>'));
        var t=el('<input type="time">');
        var ok=el('<button class="green full" style="margin-top:8px;">Potvrdit</button>');
        ok.addEventListener("click",function(){
          if(!t.value||!dI.value) return;
          ok.disabled=true;
          var pref=(dI.value===today)?"Dnes":czDate(dI.value);
          presence({text:textFn(pref, t.value),add_since:false,day:dI.value},ok);
        });
        bx.appendChild(t); bx.appendChild(ok);
      }
      function driveBuild(bx){ _denCasBuild(bx,"V kolik budeš končit?",function(p,t){ return p+" končím dříve, asi v "+t; }); }
      function pozdejiBuild(bx){ _denCasBuild(bx,"V kolik dorazíš?",function(p,t){ return p+" přijdu později, dorazím asi v "+t; }); }
      // Marti 8.6.: zpětná vazba člověka → vedoucímu výroby (průběžně).
      function vyrobaFbBuild(box){
        box.appendChild(el('<div class="hint" style="margin:2px 0 4px;">Co se děje na zakázce? Jde rovnou vedoucímu výroby.</div>'));
        var ta=el('<textarea rows="3" placeholder="např. potřebuju díl · můžu vzít další · VR10660 hotová z půlky" style="width:100%;background:#0f1620;border:1px solid #2a3a4d;border-radius:10px;padding:11px;color:var(--tx);font-size:15px;font-family:inherit;"></textarea>');
        function snd(typ,btn){ var t=(ta.value||"").trim(); if(!t){ ta.focus(); return; } btn.disabled=true;
          api("POST","/api/v1/erp/app/vyroba/zprava",{text:t,typ:typ}).then(function(r){
            if(r&&r.ok){ box.innerHTML='<div class="hint" style="color:var(--green);padding:6px 0;">✅ Odesláno vedoucímu výroby. Díky!</div>'; }
            else { btn.disabled=false; alert("Chyba: "+((r&&r.error)||"?")); } }); }
        var b1=el('<button class="green full" style="margin-top:8px;">🙋 Něco potřebuju → poslat</button>');
        b1.addEventListener("click",function(){ snd("pozadavek",b1); });
        var b2=el('<button class="ghost full" style="margin-top:6px;">💡 Jen informuji → poslat</button>');
        b2.addEventListener("click",function(){ snd("info",b2); });
        box.appendChild(ta); box.appendChild(b1); box.appendChild(b2);
      }
      function vyrobaFinishBuild(box){
        box.appendChild(el('<div class="hint" style="margin:2px 0 4px;">Dej vedoucímu vědět, že budeš brzy hotov — ať ti připraví další práci. 🏁</div>'));
        var ta=el('<textarea rows="2" placeholder="Volitelně: na čem / co dál" style="width:100%;background:#0f1620;border:1px solid #2a3a4d;border-radius:10px;padding:11px;color:var(--tx);font-size:15px;font-family:inherit;margin-bottom:6px;"></textarea>');
        box.appendChild(ta);
        chipsIn(box,"Za jak dlouho asi budeš hotov?",function(min,b){ b.disabled=true;
          api("POST","/api/v1/erp/app/vyroba/finish",{eta_min:min,text:(ta.value||"").trim()}).then(function(r){
            if(r&&r.ok){ box.innerHTML='<div class="hint" style="color:var(--green);padding:6px 0;">🏁 Vedoucí ví, že finišuješ. Díky!</div>'; }
            else { b.disabled=false; alert("Chyba: "+((r&&r.error)||"?")); } }); });
      }
      // Marti 7.6. večer: vše se rozbaluje NA MÍSTĚ (jako Kontakty), žádné
      // přepínání obrazovek. Ťuknutí na volbu znovu = zavření.
      // Marti 10.6.: časovaný status (jednání/pochůzka) — čas přes ČIPY (žádné
      // kruhové hodiny), během statusu jen Konec+Prodloužit, po uplynutí dotaz.
      function _parseEndTime(s){ var m=(s||"").match(/do\s*(?:cca\s*|~)?(\d{1,2}:\d{2})/i); return m?m[1]:null; }
      function _parseStartTime(s){ var m=(s||"").match(/od\s*(\d{1,2}:\d{2})/i); return m?m[1]:null; }
      function _isPast(hhmm, startHHMM){
        var p=(hhmm||"").split(":"); if(p.length<2) return false;
        var now=new Date(), e=new Date(); e.setHours(parseInt(p[0],10),parseInt(p[1],10),0,0);
        if(startHHMM){ var sp=startHHMM.split(":"), sh=parseInt(sp[0],10), sm=parseInt(sp[1],10);
          if(parseInt(p[0],10)<sh || (parseInt(p[0],10)===sh && parseInt(p[1],10)<=sm)) e.setDate(e.getDate()+1); }
        else if(now - e > 2*3600*1000){ e.setDate(e.getDate()+1); }  // bez startu: konec >2h v minulosti = zítra (přes půlnoc)
        return now > e; }
      // Marti 10.6.: čas „do kolika" přes kompaktní rolovací KOLEČKA (HH : MM).
      // Hodiny jen DOPŘEDU od teď (minulý čas nejde), minuty po 5 ve smyčce.
      // Potvrzení hlídá, že čas je po aktuálním.
      function timeChips(box,label,onPick){
        if(label) box.appendChild(el('<div class="hint" style="margin-top:6px;">'+label+'</div>'));
        var ITEM=22, VIS=5, PAD=2*ITEM, H=ITEM*VIS;
        function wheel(values, def, loop){
          var len=values.length, REP=loop?7:1, MID=loop?3:0;
          var w=el('<div style="position:relative;flex:0 0 46px;height:'+H+'px;overflow-y:scroll;scroll-snap-type:y mandatory;-webkit-overflow-scrolling:touch;scrollbar-width:none;"></div>');
          var inner=el('<div></div>');
          inner.appendChild(el('<div style="height:'+PAD+'px;"></div>'));
          var rr,vv;
          for(rr=0;rr<REP;rr++){ for(vv=0;vv<len;vv++){ inner.appendChild(el('<div class="twi" style="height:'+ITEM+'px;line-height:'+ITEM+'px;text-align:center;scroll-snap-align:center;color:var(--mut);font-size:13px;transition:color .1s,font-size .1s,font-weight .1s;">'+("0"+values[vv]).slice(-2)+'</div>')); } }
          inner.appendChild(el('<div style="height:'+PAD+'px;"></div>'));
          w.appendChild(inner);
          w._values=values; w._idx=def;
          var its=inner.querySelectorAll('.twi');
          function hl(cur){ for(var k=0;k<its.length;k++){ var on=(k===cur); its[k].style.color=on?'var(--tx)':'var(--mut)'; its[k].style.fontWeight=on?'700':'400'; its[k].style.fontSize=on?'17px':'13px'; } }
          function upd(){ var cur=Math.round(w.scrollTop/ITEM);
            if(loop && (cur<len || cur>=(REP-1)*len)){ cur=((cur%len)+len)%len + MID*len; w.scrollTop=cur*ITEM; }
            if(!loop){ cur=Math.max(0,Math.min(len-1,cur)); }
            w._idx=loop?(((cur%len)+len)%len):cur; hl(cur); }
          w.addEventListener('scroll',function(){ clearTimeout(w._t); w._t=setTimeout(upd,60); });
          setTimeout(function(){ var s=loop?(MID*len+def):def; w.scrollTop=s*ITEM; hl(s); },20);
          return w;
        }
        var now=new Date(), nowH=now.getHours(), nowM=now.getMinutes();
        var hours=[],mins=[],h,m; for(h=0;h<24;h++)hours.push((nowH+h)%24); for(m=0;m<60;m+=5)mins.push(m);
        var dMin=Math.ceil((nowM+1)/5)*5, dHi=0; if(dMin>=60){ dMin=0; dHi=Math.min(1,hours.length-1); }
        var dMi=mins.indexOf(dMin); if(dMi<0)dMi=0;
        var row=el('<div style="display:flex;gap:0;align-items:center;justify-content:center;margin:6px auto 0;width:max-content;position:relative;"></div>');
        row.appendChild(el('<div style="position:absolute;left:0;right:0;top:'+PAD+'px;height:'+ITEM+'px;background:rgba(120,150,200,0.10);border-top:1px solid var(--bord);border-bottom:1px solid var(--bord);pointer-events:none;border-radius:6px;"></div>'));
        var wh=wheel(hours,dHi,false), wm=wheel(mins,dMi,true);
        row.appendChild(wh); row.appendChild(el('<div style="font-size:16px;font-weight:700;color:var(--tx);padding:0 1px;">:</div>')); row.appendChild(wm);
        box.appendChild(row);
        var warn=el('<div class="hint" style="color:var(--amber);margin-top:2px;"></div>'); box.appendChild(warn);
        var ok=el('<button class="green full" style="margin-top:6px;">Potvrdit čas</button>');
        ok.addEventListener("click",function(){ var hv=wh._values[wh._idx], mv=wm._values[wm._idx];
          var sel=new Date(); sel.setHours(hv,mv,0,0); if(sel<=new Date()) sel.setDate(sel.getDate()+1);
          ok.disabled=true; onPick(("0"+hv).slice(-2)+":"+("0"+mv).slice(-2),ok); });
        box.appendChild(ok);
      }
      function buildProlong(box, kind){
        var txt=(kind==="jednání")?"Mám jednání":"Na služební pochůzce";
        // Prodloužit RELATIVNĚ k stávajícímu konci (ne k teď). Když už uplynul, od teď.
        function plusMin(min){ var base=_parseEndTime(j.announced), d=new Date();
          if(base){ var p=base.split(":"); d.setHours(parseInt(p[0],10),parseInt(p[1],10),0,0); if(d<new Date()) d=new Date(); }
          d.setMinutes(d.getMinutes()+min);
          return ("0"+d.getHours()).slice(-2)+":"+("0"+d.getMinutes()).slice(-2); }
        chipsIn(box,"⏱ Prodloužit "+(kind==="jednání"?"jednání":"pochůzku")+" o:",function(m,b){ presence({text:txt,add_since:false,until_txt:"~"+plusMin(m)},b); },[["+30 min",30],["+60 min",60]]);
        timeChips(box,"…nebo do kolika:",function(t,b){ presence({text:txt,add_since:false,until_txt:"~"+t},b); });
      }
      function showOpts(){
        window._dochMenuTs=Date.now();
        bw.innerHTML=""; bw._exps=null;
        // Marti 7.6. večer: žádná červená — změna činnosti není poplach (ghost).
        // „Jsem na zakázce" (píchnutej ≠ pracuje), „nepočítej" až na konec.
        if(open && open.open_type!=='commute' && open.open_type!=='day_end'){
          // zakázka patří sem — přepnutí BĚHEM směny (switch)
          // (na cestě / „mám volno" → arrival větev níže: „Jsem v práci" je uzavře)
          // Marti 10.6.: víc místa v „makám" — těchto 7 voleb sbalit pod jeden obal.
          // („Tak tady budu jinde" = budoucnost, sem nepatří → jiný název.)
          expOpt(bw,"🙈 Teď to bude jinak…","ghost",function(bx){
            var bp=btnEl("☕ Potřebuju krátkou pauzu…","ghost"); bp.addEventListener("click",function(){ act("checkout",{reason:"krátká pauza",presence:"Jsem na krátké pauze"},bp); }); bx.appendChild(bp);
            expOpt(bx,"🍃 Jdu se provětrat / najíst…","ghost",function(b2){
              chipsIn(b2,"Na jak dlouho cca?",function(m,b){ act("checkout",{reason:"pauza — provětrání/jídlo",presence:"Relaxuji a odpočívám",presence_eta_min:m},b); });
            });
            expOpt(bx,"🕔 Potřebuji skončit dříve…","ghost",driveBuild);
            expOpt(bx,"🌅 Potřebuji přijít později…","ghost",pozdejiBuild);
            expOpt(bx,"📅 Mám jednání…","ghost",function(b2){
              chipsIn(b2,"Jednání potrvá cca:",function(m,b){ presence({text:"Mám jednání",add_since:false,eta_min:m},b); });
              timeChips(b2,"…nebo do kolika:",function(t,b){ presence({text:"Mám jednání",add_since:false,until_txt:"~"+t},b); });
            });
            expOpt(bx,"🚗 Mám služební pochůzku…","ghost",function(b2){
              chipsIn(b2,"Pochůzka potrvá cca:",function(m,b){ presence({text:"Na služební pochůzce",add_since:false,eta_min:m},b); });
              timeChips(b2,"…nebo do kolika:",function(t,b){ presence({text:"Na služební pochůzce",add_since:false,until_txt:"~"+t},b); });
              var nb=el('<button class="ghost full" style="margin-top:8px;">Zatím nevím — bez času</button>');
              nb.addEventListener("click",function(){ nb.disabled=true; presence({text:"Na služební pochůzce",add_since:true},nb); }); b2.appendChild(nb);
            });
            // Petra 25.6.2026: OSVČ — nahlášení nepřítomnosti (od–do), neplacené. Jen pro formu OSVČ.
            if(j.is_osvc){
              expOpt(bx,"🧾 Nepřítomnost OSVČ…","ghost",function(b2){
                dateRangePickIn(b2,"Nepřítomnost OSVČ od – do:",function(od,dd,b){
                  absence({type_code:"osvc_absence",date_from:od,date_to:dd,mode:"days",note:"nepřítomnost OSVČ (přes mobil)"},function(){
                    absOk(b2,"Nepřítomnost OSVČ "+czDate(od)+" – "+czDate(dd));
                  },b);
                });
              },_amberStyle);
            }
            var bn=btnEl("🫡 Dnes už se mnou nepočítej ;)","ghost"); bn.addEventListener("click",function(){ act("checkout",{reason:"",presence:"Dnes už se mnou nepočítej ;)",add_since:false},bn); }); bx.appendChild(bn);
          },_amberStyle);
          expOpt(bw,"🛠 Zpráva vedoucímu výroby…","ghost",vyrobaFbBuild,_blueStyle);
          expOpt(bw,"🏁 Budu brzy hotov…","ghost",vyrobaFinishBuild,_blueStyle);
          expOpt(bw,"💬 Píši přímo tobě, Marti…","ghost",martiMsgBuild,_blueStyle);
          expOpt(bw,"🙋 Mám dotaz na nadřízeného…","ghost",bossAskBuild,_blueStyle);
          if(window._canManageVyroba){
            var _vb=btnEl("🏭 Plánovač výroby (vedoucí)","green");
            _vb.addEventListener("click",function(){ go("vyroba"); });
            bw.appendChild(_vb);
          }
        } else {
          // „Už jedu" první · lékaři sem (Marti 7.6. večer) · „Jinde" před zprávou
          expOpt(bw,"🚗 Jedu do práce…","green",function(bx){
            // Marti 7.6. večer: + 5 minut = „už jsem skoro v práci"
            chipsIn(bx,"Dorazím za cca:",function(m,b){ act("checkin",{kind:"commute",eta_min:m},b); },
              [["5 min",5],["15 min",15],["30 min",30],["45 min",45],["1 h",60],["1,5 h",90],["2 h",120]]);
          });
          addOpts([
            ["🏢 Jsem v práci…",                 function(b){ act("checkin",{kind:"work"},b); }],
            ["🏠 Nejsem v práci… (home office)", function(b){ act("checkin",{kind:"homeoffice"},b); }]
          ],"green");
          expOpt(bw,"🌅 Potřebuji přijít později…","ghost",pozdejiBuild);
          expOpt(bw,"🕔 Potřebuji skončit dříve…","ghost",driveBuild);
          // Petra 25.6.2026: OSVČ nepřítomnost (od–do) — viditelná i MIMO směnu. Jen forma OSVČ.
          if(j.is_osvc){
            expOpt(bw,"🧾 Nepřítomnost OSVČ…","ghost",function(b2){
              dateRangePickIn(b2,"Nepřítomnost OSVČ od – do:",function(od,dd,b){
                absence({type_code:"osvc_absence",date_from:od,date_to:dd,mode:"days",note:"nepřítomnost OSVČ (přes mobil)"},function(){
                  absOk(b2,"Nepřítomnost OSVČ "+czDate(od)+" – "+czDate(dd));
                },b);
              });
            },_amberStyle);
          }
          // Marti 14.6.: „Tady budu asi jinde" přesunuto do regionu docházky (dlaždice).
          expOpt(bw,"💬 Píši přímo tobě, Marti…","ghost",martiMsgBuild,_blueStyle);
          expOpt(bw,"🙋 Mám dotaz na nadřízeného…","ghost",bossAskBuild,_blueStyle);
        }
        // Marti 7.6. večer: místo „Zrušit" šipka nahoru = zavřít.
        var z=el('<button class="ghost full" style="margin-top:8px;text-align:center;">▲</button>');
        z.addEventListener("click",mainBtn); bw.appendChild(z);
        // Marti 7.6. večer: po otevření rozhovoru odscrollovat nahoru k volbám.
        setTimeout(function(){ try{ bw.scrollIntoView({behavior:"smooth",block:"start"}); }catch(e){} },60);
      }
      window._dochCloseMenu=mainBtn;
      mainBtn(); cn.appendChild(bw);
      // nepotvrzené dny → karty pod „Právě probíhá"
      var cf=document.getElementById("dochConfirm");
      if(cf){ api("GET","/api/v1/erp/app/attendance/unconfirmed","").then(function(ju){
        renderConfirmList(cf, (ju&&ju.days)||[], function(){});
        // Marti 7.6. večer: při neschválené docházce karty rovnou na oči
        // (jen poprvé — tick uživatele nesmí vytrhávat ze čtení).
        if(((ju&&ju.days)||[]).length && !window._confScrolled){
          window._confScrolled=true;
          setTimeout(function(){ try{ cf.scrollIntoView({behavior:"smooth",block:"start"}); }catch(e){} },120);
        }
      }); }
      // Marti 7.6. večer: zabalený výchozí stav = JEN „Od: 7:26 — Rezie"
      // + odpracovaný čas vpravo. Mimo směnu stejný duch: jednoduše a přívětivě.
      var hrs=j.today_hours||0;
      // Marti 7.6. večer: nadpis + ikona podle statusu (schválený seznam).
      function dochTitle(){
        var a=(j.announced||"").toLowerCase();
        function has(s){ return a.indexOf(s)>=0; }
        var _et=_parseEndTime(j.announced), _es=_et?(" do "+_et):"";
        if(open){
          // Marti 12.6.: stav systémově podle typu běžícího jobu (jeden zdroj pravdy)
          var _ot=open.open_type||"work";
          if(_ot==='commute') return "Už jedu do práce 🚗";
          if(_ot==='break')   return "Dávám si pauzu ☕";
          if(_ot==='day_end') return "Mám volno 🏝️";
          if(has("jednání")) return "Mám jednání"+_es+" 🤝";
          if(has("školení")) return "Jsem na školení 🎓";
          if(has("pochůzce")||has("pochůzka")) return "Na pochůzce"+_es+" 📦";
          if(has("končím dříve")) return "Dnes končím dřív 🕔";
          // Marti 14.6.: nadpis je jen „Makám" — zakázka/činnost se řeší zvlášť v sekci.
          return "Makám 👷";
        }
        if(j.day_off) return "Mám volno 🏝️";
        if(a){
          if(has("krátké pauze")||has("krátká pauza")) return "Dávám si pauzu ☕";
          if(has("relaxuji")) return "Doplňuju energii 🍴";
          if(has("jedu do práce")) return "Už jedu! 🚗";
          if(has("přijdu později")) return "Dorazím později 🌅";
          if(has("lékař")||has("doktor")) return "Jsem u doktora 🩺";
          if(has("sick day")||has("je mi blbě")) return "Dneska marodím 🤒";
          if(has("neschopenka")) return "Marodím… 🤧";
          if(has("dovolen")) return "Mám dovolenou 🌴";
          if(has("očr")||has("rodinu")) return "Pečuju o rodinu 👨‍👧";
          if(has("pochůzce")||has("pochůzka")) return "Na pochůzce"+_es+" 📦";
          if(has("zařizuji")||has("zařizuju")) return "Něco si zařizuju 🕐";
          if(has("nepočítej")) return "Mám volno 🏝️";
          if(has("jednání")) return "Mám jednání"+_es+" 🤝";
          if(has("pauz")) return "Dávám si pauzu ☕";
        }
        if(hrs>0) return "Teď zrovna nemakám 😌";
        var wkd=(new Date().getDay()===0||new Date().getDay()===6);
        return wkd ? "Dnes se nemaká 🌤" : "Tak co, jdeme na to? 🌅";
      }
      var hd=document.getElementById("dochHead");
      if(hd){ hd.textContent=dochTitle(); hd.style.display=""; }
      // Marti 14.6.: region nástrojů „pod jednou střechou" — JEN když člověk nemaká
      // (žádný běžící pracovní job). Když maká, schovej (ať obrazovka neruší od práce).
      var _tools=document.getElementById("dochTools");
      if(_tools){ var _working=!!(open && (open.open_type==='work' || !open.open_type)); _tools.style.display=_working?"none":"block"; }
      var annHtml=(j.announced?('<div style="color:var(--amber);font-size:14px;margin-top:6px;">💬 '+esc(j.announced)+'</div>'):'');
      // Jedno číslo (odpracováno bez pauz) — v hlavičce; uvnitř jen detail/status.
      c.innerHTML=(open
          ? ((open.project_name?('<div style="font-size:13.5px;">Zakázka: <b>'+esc(open.project_name)+'</b></div>'):'')+annHtml)
          : (hrs>0 ? (annHtml||'<div class="hint">Detail dne najdeš v Posledních záznamech.</div>')
                   : ('<div class="hint">Dnes zatím nic. 😉</div>'+annHtml)));
      if(_dS&&_dS.today){
        var T=_dS.today;
        var hdr="font-size:14.5px;font-weight:500;flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;";
        // Marti 12.6.: píchají a vidí čas VŠICHNI (i volný/IT). Režim řeší odměnu/řízení
        // na backendu/u vedoucího, ne píchací UX. (Dřívější skrývání hodin u 'info' zrušeno.)
        var _info=false;
        function _setVal(txt,col,fs){
          if(_info){ T.val.textContent = open ? "🟢 k dispozici" : "mimo";
            T.val.style.color = open ? "var(--green)" : "var(--mut)"; T.val.style.fontSize="13px"; }
          else { T.val.textContent=txt; T.val.style.color=col; T.val.style.fontSize=fs; }
        }
        if(open){
          var ms=j.morning_start||open.started_at||"";
          T.ttl.innerHTML='Od: <b>'+(ms?esc(ms.substr(11,5)):"—")+'</b>'
            +(open.project_ref?(' &nbsp;—&nbsp; <b>'+esc(open.project_ref)+'</b>'):'');
          T.ttl.style.cssText=hdr;
          _setVal(fmtHM(hrs),"var(--green)","18px");
        } else if(hrs>0){
          T.ttl.innerHTML='Od: <b>'+(j.morning_start?esc(j.morning_start.substr(11,5)):"—")+'</b>'
            +(j.last_end?(' &nbsp;—&nbsp; do <b>'+esc(j.last_end.substr(11,5))+'</b>'):'');
          T.ttl.style.cssText=hdr;
          _setVal(fmtHM(hrs),"var(--green)","18px");
        } else {
          T.ttl.textContent="Dneska je den…"; T.ttl.style.cssText="font-size:15px;font-weight:600;";
          _setVal("—","var(--mut)","");
        }
      }
      dochDailyLoad(); dochListLoad();
      _bossAnswerCheck(); _bossPendingLoad();  // dotazy nadřízenému — refresh s 60s tickem
    }).catch(function(){ var c=document.getElementById("dochNow"); if(c)c.textContent="Chyba spojení."; });
    // živý přepočet běžící směny (jen dokud je obrazovka Docházka otevřená)
    if(window._dochTick) clearInterval(window._dochTick);
    window._dochTick=setInterval(function(){
      if(!document.getElementById("dochNow")){ clearInterval(window._dochTick); window._dochTick=null; return; }
      // Marti 7.6.: NIKDY nepřekreslovat, když člověk píše (rozporování, zpráva Marti…)
      var ae=document.activeElement;
      if(ae && (ae.tagName==="TEXTAREA" || ae.tagName==="INPUT")) return;
      // Marti 7.6. večer: otevřené menu rozhovoru nechat žít — zavřít až po
      // minutě od posledního dotyku.
      if(window._dochMenuTs && Date.now()-window._dochMenuTs<60000) return;
      dochLoad();
    },60000);
  }
  // Marti 11.6.: lokální datum (ne UTC) — jinak se kolem půlnoci „dnes/včera" rozjede.
  function _locDate(off){ var d=new Date(); if(off) d.setDate(d.getDate()+off); return d.getFullYear()+"-"+("0"+(d.getMonth()+1)).slice(-2)+"-"+("0"+d.getDate()).slice(-2); }
  function _dochDayRow(lbl, r){
    var w=Number(r.worked||0), a=Number(r.absence||0);
    var right='<b style="color:'+(w>0?'var(--green)':'var(--mut)')+';">'+fmtHM(w)+'</b>'+(a>0?(' <span style="color:var(--amber);">+ '+fmtHM(a)+' nepř.</span>'):'')+(r.active?' 🟢':'');
    return el('<li style="display:flex;justify-content:space-between;align-items:center;"><span class="nt">'+esc(lbl)+'</span><span class="nm" style="margin:0;">'+right+'</span></li>');
  }
  function dochDailyLoad(){
    api("GET","/api/v1/erp/app/attendance/daily?days=14","").then(function(j){
      var allRows=(j&&j.days)||[];
      var today=_locDate(0);
      var yest=_locDate(-1);
      // Včera — hlavička sekce (počet hodin); tělo plní dochListLoad job-templatem.
      var yrows=allRows.filter(function(r){return r.d===yest;});
      var yw=0, ya=0; yrows.forEach(function(r){ yw+=Number(r.worked||0); ya+=Number(r.absence||0); });
      if(_dS&&_dS.yest) _dS.yest.val.textContent=(yrows.length?fmtHM(yw)+(ya>0?(" + "+fmtHM(ya)+" nepř."):""):"—");
      var yu=document.getElementById("dochYest");
      if(yu){ if(!yrows.length){ yu.innerHTML='<li style="color:var(--mut);border:none;">Bez záznamu.</li>'; }
        else { yu.innerHTML=""; yrows.forEach(function(r){ yu.appendChild(_dochDayRow(r.d, r)); }); } }
      // Dřívější — hlavička sekce; tělo plní dochListLoad job-templatem.
      var prev=allRows.filter(function(r){return (r.d||"")<yest;});
      if(_dS&&_dS.prev) _dS.prev.val.textContent=(prev.length?czDays(prev.length):"");
      var ul=document.getElementById("dochDaily");
      if(ul){ if(!prev.length){ ul.innerHTML='<li style="color:var(--mut);border:none;">Zatím nic.</li>'; }
        else { ul.innerHTML=""; prev.forEach(function(r){ ul.appendChild(_dochDayRow(r.d, r)); }); } }
      // Plánovaná nepřítomnost — budoucnost (absence + ohlášení dopředu)
      var pu=document.getElementById("dochPlan2");
      if(pu){
        // Marti 11.6.: PLAN template (levý panel + lišta Vše/Absence/Ohlášení).
        var fut=allRows.filter(function(r){return (r.d||"")>today && (Number(r.absence||0)>0 || Number(r.worked||0)>0);}).sort(function(a,b){return a.d<b.d?-1:1;});
        api("GET","/api/v1/erp/app/attendance/announced-future","").then(function(ja){
          if(!document.getElementById("dochPlan2"))return;
          var ann=(ja&&ja.items)||[];
          if(_dS&&_dS.plan) _dS.plan.val.textContent="";
          var items=[];
          fut.forEach(function(r){ var a=Number(r.absence||0), w=Number(r.worked||0);
            items.push({kind:"absence", d:r.d, txt:(a>0?(fmtHM(a)+" nepřítomnost"):fmtHM(w))}); });
          ann.forEach(function(r){ items.push({kind:"ohlaseni", d:r.d, note:r.note||"", txt:"💬 "+(r.note||""), id:r.id}); });
          _renderPlanPanel("dochPlanRail","dochPlan2", items, _planSt);
        });
      }
    });
  }
  // Marti 11.6.: „Tak to bylo dneska“ — joby ve stylu Kontaktů (avatar+ikona,
  // accordion zvětšení, 3 tlačítka; 2. klik = detail přes celou obrazovku).
  function _jobIcon(e){ var s=((e.typ||'')+' '+(e.note||'')).toLowerCase();
    if(/home|domov/.test(s)) return '🏠';
    if(/konec dne|nepo[čc][íi]t/.test(s)) return '🏝️';
    if(/jedu do pr|na cest/.test(s)) return '🚗';
    if(/relax|energ|jídl|jidl|provětr|provetr|naj[íi]st|ob[ěe]d/.test(s)) return '🍴';
    if(/pauz|p[řr]est[aá]v/.test(s)) return '☕';
    if(/jedn[aá]n/.test(s)) return '🤝';
    if(/poch[uů]z/.test(s)) return '📦';
    if(/lékař|lekar|doktor/.test(s)) return '🩺';
    if(/školen|skolen/.test(s)) return '🎓';
    if(_jobZak(e)) return '👷';   // reálná zakázka = dělník s helmou
    return '🧾'; }               // produktivní bez zakázky = režie
  // ── ✋ Žádost o opravu už POTVRZENÉHO dne (Jirka 21.7.2026, podnět Peťa) ──
  // „Lidi omylem potvrdí docházku za předchozí den a pak za mnou chodí osobně."
  // Po potvrzení dne zmizí jantarová karta a s ní i jediné „✋ Nesedí…" — člověk
  // neměl jak se ozvat. Backend uměl obojí už dřív (entry-dispute / dispute-day,
  // oba fungují bez ohledu na potvrzení a routují editorům dle působnosti přes
  // _att_fix_editors_for_emp) — chyběla JEN cesta v appce. Bez časového omezení
  // (rozhodl Jirka 21.7.) — dozadu nic nezakazujeme, editor si den případně
  // odemkne. Trim/zakázku tu VĚDOMĚ nedrátujeme (R1 samoúpravy leží u Marti-AI).
  // Peťa 21.7.: o opravu lze žádat JEN za aktuální kalendářní měsíc (starší už
  // prošlo mzdou). Vynuceno i na serveru (/attendance/fix-request → 409).
  function _opravaMesicOd(){ var d=new Date(); return d.getFullYear()+"-"+("0"+(d.getMonth()+1)).slice(-2)+"-01"; }
  function _opravaDenPovolen(iso){ return String(iso||"") >= _opravaMesicOd(); }
  // Pozor: czDayLabel() je vnořená uvnitř dochLoad() — modulové funkce na ni nedosáhnou.
  function _czDayLabel(iso){ try{ var d=new Date(iso+"T12:00:00"); return d.toLocaleDateString("cs",{weekday:"long",day:"numeric",month:"numeric"}); }catch(e){ return iso; } }
  var _OPRAVA_DUVODY=["omylem jsem potvrdil(a) den","chybí příchod","chybí odchod",
                      "špatný čas","chybí přestávka / oběd","špatná zakázka"];
  // Popisek záznamu: záznamy bez časů (dovolená, nárok nad fond) by jinak
  // ukázaly „? – …" — u těch je smysluplný typ, ne prázdný rozsah.
  function _opravaLbl(e){
    if(!e) return "záznam";
    var t=(e.zac?(e.zac+(e.kon?(" – "+e.kon):" – …")):"");
    if(!t) return (e.typ||"záznam")+(e.hours!=null?(' · '+fmtHM(e.hours)):'');
    return t+(e.hours!=null?(' · '+fmtHM(e.hours)):'')
            +(e.project_ref?(' · 🧾 '+e.project_ref):'');
  }
  // Celoobrazovkový sheet — pro vstup z Historie/Dneška, kde je řádek uvnitř
  // úzkého scrollovacího railu (38vh) a formulář by se tam nevešel (ověřeno
  // Playwright 21.7.: oříznutá hlavička, Zrušit mimo displej).
  function _dochOpravaSheet(day, entryId, entryLabel){
    var ov=el('<div class="appmodal" style="position:fixed;inset:0;background:rgba(4,10,18,.97);z-index:400;display:flex;flex-direction:column;padding:14px 14px 0;"></div>');
    var hd=el('<div style="display:flex;gap:8px;align-items:center;margin-bottom:4px;"><div style="flex:1;font-weight:800;font-size:18px;">✋ Požádat o opravu</div></div>');
    var cl=el('<button class="ghost" style="margin:0;width:44px;">✕</button>');
    cl.addEventListener("click",function(){ ov.remove(); });
    hd.appendChild(cl); ov.appendChild(hd);
    var sc=el('<div style="flex:1;overflow:auto;-webkit-overflow-scrolling:touch;padding-bottom:60px;"></div>');
    ov.appendChild(sc);
    _dochOpravaBox(sc, day, entryId, entryLabel,
      function(){ ov.remove(); }, function(){ ov.remove(); });
    app.appendChild(ov);
  }
  function _dochOpravaBox(host, day, entryId, entryLabel, after, onCancel){
    host.innerHTML="";
    var w=el('<div style="background:rgba(224,176,112,.10);border:1px solid #6e5326;border-radius:12px;padding:12px;margin-top:6px;"></div>');
    w.appendChild(el('<div style="font-weight:700;font-size:14.5px;">✋ Žádost o opravu — '+esc(_czDayLabel(day))+'</div>'));
    w.appendChild(el('<div class="hint" style="margin-top:3px;">'
      +(entryId?('Záznam: <b>'+esc(entryLabel||"")+'</b>'):'Týká se <b>celého dne</b>.')
      +'<br>Napiš, co nesedí. Dostane to kontrola docházky a ozve se ti.</div>'));
    var ta=el('<textarea rows="3" placeholder="Co je na tom dni špatně?" style="width:100%;box-sizing:border-box;margin-top:8px;background:#0f1620;border:1px solid var(--bord);border-radius:8px;padding:10px;color:var(--tx);font-size:14px;font-family:inherit;"></textarea>');
    var chips=el('<div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:8px;"></div>');
    _OPRAVA_DUVODY.forEach(function(d){
      var c=el('<button class="ghost sm" style="font-size:12px;padding:5px 9px;">'+esc(d)+'</button>');
      c.addEventListener("click",function(){
        var v=(ta.value||"").trim();
        ta.value=(v?(v+", "):"")+d; ta.focus();
      });
      chips.appendChild(c);
    });
    var st=el('<div class="hint" style="margin-top:6px;"></div>');
    var ok=el('<button class="full" style="margin-top:8px;border-color:var(--amber);color:var(--amber);background:transparent;">✋ Odeslat kontrole docházky</button>');
    ok.addEventListener("click",function(){
      var n=(ta.value||"").trim();
      if(!n){ st.textContent="Napiš prosím, co nesedí."; return; }
      ok.disabled=true; st.textContent="⏳ Odesílám…";
      // Peťa 21.7.: jen aktuální kalendářní měsíc → vlastní endpoint fix-request
      // (dispute-day/entry-dispute zůstávají bez omezení pro potvrzovací kartu,
      // ta sahá 14 dní zpět a na přelomu měsíce by se člověk zasekl před píchnutím).
      var pl={day:day,note:n}; if(entryId) pl.id=entryId;
      api("POST","/api/v1/erp/app/attendance/fix-request",pl).then(function(r){
        if(r&&r.ok){
          host.innerHTML='<div style="background:rgba(224,176,112,.10);border:1px solid #6e5326;border-radius:12px;padding:12px;margin-top:6px;font-size:14px;">'
            +'✅ Odesláno. Kontrola docházky se ti ozve — den má teď <b>✋ rozpor</b> a je jim ve frontě.</div>';
          if(after) setTimeout(after,1400);
        } else { ok.disabled=false; st.textContent="✗ "+((r&&r.error)||"Nepodařilo se odeslat."); }
      }).catch(function(){ ok.disabled=false; st.textContent="✗ Nepodařilo se odeslat."; });
    });
    var zr=el('<button class="ghost full" style="margin-top:6px;">Zrušit</button>');
    zr.addEventListener("click",function(){ if(onCancel) onCancel(); else host.innerHTML=""; });
    w.appendChild(ta); w.appendChild(chips); w.appendChild(ok); w.appendChild(st); w.appendChild(zr);
    host.appendChild(w);
    try{ w.scrollIntoView({behavior:"smooth",block:"center"}); }catch(e){}
  }
  function _jobBtns(acts, hint, sz, fs0, e){
    function mk(bg,col,ic,fs,msg){ var b=el('<div class="cact" style="'+(sz?('width:'+sz+'px;height:'+sz+'px;border-radius:16px;'):'')+'background:'+bg+';color:'+col+';font-size:'+fs+';">'+ic+'</div>');
      b.addEventListener("click",function(ev){ ev.stopPropagation(); if(hint) hint.textContent=msg; }); return b; }
    var d=fs0||0;
    acts.appendChild(mk('#e0a44a','#241a02','⏱',(19+d)+'px','Návrh: Upravit konec — opravit čas konce (zapomenutý odchod). Ostrou funkci nawiruju, až schválíš.'));
    acts.appendChild(mk('#3b5bdb','#fff','🧾',(17+d)+'px','Návrh: Zakázka — přepnout tento záznam na jinou zakázku.'));
    acts.appendChild(mk('#ef4444','#fff','🗑',(18+d)+'px','Návrh: Smazat — odebrat tento záznam (s logem do att_audit).'));
    // Jirka 21.7.: jediné OSTRÉ tlačítko v řadě — žádost o opravu (i po potvrzení dne).
    // Ostatní tři zůstávají návrhem (R1 samoúpravy leží u Marti-AI/Martiho).
    if(e && e.d){
      var bf=el('<div class="cact" style="'+(sz?('width:'+sz+'px;height:'+sz+'px;border-radius:16px;'):'')+'background:#e0a44a;color:#241a02;font-size:'+(18+d)+'px;">✋</div>');
      bf.addEventListener("click",function(ev){
        ev.stopPropagation();
        if(!_opravaDenPovolen(e.d)){   // starší měsíc = uzavřeno mzdami (Peťa 21.7.)
          if(hint) hint.textContent="⏳ Za tenhle den už o opravu požádat nejde — jen za aktuální měsíc. Ozvi se prosím kontrole docházky osobně.";
          return; }
        if(hint) hint.textContent="";
        _dochOpravaSheet(e.d, e.id||0, _opravaLbl(e));
      });
      acts.appendChild(bf);
    }
  }
  function _jobOverlay(e){
    var ic=_jobIcon(e), timeR=(e.code==='day_end')?('Konec '+(e.zac||'')):((e.zac||'')+(e.kon?(' – '+e.kon):(e.is_active?' – …':'')));
    var ov=el('<div id="jobOverlay" style="position:fixed;inset:0;z-index:9000;background:#0c1118;overflow-y:auto;padding:16px 16px 48px;"></div>');
    var top=el('<div style="display:flex;justify-content:flex-end;"><button class="ghost" style="font-size:20px;width:44px;margin:0;">✕</button></div>');
    top.querySelector("button").addEventListener("click",function(){ ov.remove(); });
    ov.appendChild(top);
    ov.appendChild(el('<div style="display:flex;align-items:center;gap:14px;text-align:left;margin:4px 2px 16px;"><div class="cav" style="width:72px;height:72px;border-radius:20px;font-size:34px;flex:none;background:'+avColor(e.note||e.typ||"?")+';">'+ic+'</div><div style="min-width:0;"><div style="font-size:22px;font-weight:800;">'+esc(timeR||(e.typ||""))+'</div><div class="hint" style="margin-top:4px;">'+esc(e.typ||'')+(_jobZak(e)?(' · '+esc(e.project_ref)):(_jobRezie(e)?' · Režie':''))+'</div></div></div>'));
    var info=el('<div class="panel"></div>');
    info.appendChild(el('<div style="display:flex;justify-content:space-between;padding:6px 0;"><span class="hint">Datum</span><span>'+esc(e.d||"")+'</span></div>'));
    info.appendChild(el('<div style="display:flex;justify-content:space-between;padding:6px 0;"><span class="hint">Odpracováno</span><span>'+(e.hours!=null?fmtHM(e.hours):"—")+'</span></div>'));
    info.appendChild(el('<div style="display:flex;justify-content:space-between;padding:6px 0;"><span class="hint">Stav</span><span>'+esc(e.status||"")+'</span></div>'));
    if(e.note) info.appendChild(el('<div style="padding:6px 0;"><span class="hint">Poznámka</span><div style="margin-top:2px;">'+esc(e.note)+'</div></div>'));
    ov.appendChild(info);
    var actsBox=el('<div class="ctacts" style="justify-content:center;margin-top:20px;gap:18px;"></div>');
    var hint=el('<div class="hint" style="text-align:center;margin-top:14px;min-height:20px;"></div>');
    _jobBtns(actsBox, hint, 56, 5, e);
    ov.appendChild(actsBox); ov.appendChild(hint);
    document.body.appendChild(ov);
  }
  function _jobRow(e){
    var li=document.createElement("li"); li.className="ct"; li.style.padding="0"; li.style.borderBottom="none";
    var ic=_jobIcon(e), timeR=(e.code==='day_end')?('Konec '+(e.zac||'')):(((e.zac||'')+(e.kon?(' – '+e.kon):(e.is_active?' – …':'')))||(e.typ||''));
    // Marti 11.6.: „Práce" i stav (pending) skryté (typ je nespolehlivý — pauza má
    // taky entry type „Práce"). Režie ukáže „Režie", u relaxu žádná zakázka.
    var _sp=[];
    if(e.hours!=null) _sp.push(fmtHM(e.hours));  // Marti 11.6.: nejdřív čas
    // Marti 19.6.: DOCHÁZKA = jen přítomnost, BEZ zakázky/Režie (zakázka+činnost jsou v Zakázkovém pohledu).
    if(e.cat && e.cat!=='presence' && e.typ) _sp.push(esc(e.typ));  // Přestávka/Jedu do práce/Dovolená/Lékař…
    var sub=_sp.join(' · ');
    var _wbg=_jobMimo(e)?"#caa14a":"var(--green)";  // Marti 11.6.: práce zelená, mimo jantarová
    var head=el('<div class="cthead"><div class="cav" style="background:'+_wbg+';font-size:30px;line-height:1;">'+ic+'</div><div style="flex:1;min-width:0;"><div class="ctname">'+esc(timeR)+'</div><div class="ctnum">'+sub+'</div></div></div>');
    var exp=el('<div class="ctexp" style="display:none;"><div class="ctacts"></div><div class="hint" style="margin-top:8px;min-height:16px;"></div></div>');
    if(!_dochViewUid) _jobBtns(exp.querySelector(".ctacts"), exp.querySelector(".hint"), 0, 0, e);  // u cizí osoby read-only (bez akcí)
    head.addEventListener("click",function(){
      if(li.classList.contains("open")){ if(!_dochViewUid) _jobOverlay(e); return; }
      var ulx=li.parentNode;
      if(ulx&&ulx.querySelectorAll) ulx.querySelectorAll("li.ct").forEach(function(o){ o.classList.remove("open"); var x=o.querySelector(".ctexp"); if(x)x.style.display="none"; });
      exp.style.display="block"; li.classList.add("open"); li.scrollIntoView({block:"nearest",behavior:"smooth"});
      var lid=(ulx&&ulx.id)||"dochToday2"; _railSync(lid.replace(/2$/,"")+"Rail", lid);
    });
    li.appendChild(head); li.appendChild(exp); return li;
  }
  // Marti 11.6.: rozkliknutý job schová pravou lištu daného panelu (seznam přes celou šířku).
  function _railSync(railId,listId){
    var rail=document.getElementById(railId); if(!rail) return;
    var t2=document.getElementById(listId);
    rail.style.display=(t2&&t2.querySelector("li.ct.open"))?"none":"";
  }
  function _dochRailSync(){ _railSync("dochTodayRail","dochToday2"); }
  function _jobMimo(e){ var s=((e.typ||'')+' '+(e.note||'')).toLowerCase();
    if(/home|domov/.test(s)) return false;
    return /pauz|p[řr]est[aá]v|relax|energ|jídl|jidl|provětr|provetr|naj[íi]st|ob[ěe]d|jedn[aá]n|poch[uů]z|lékař|lekar|doktor|konec dne|nepo[čc][íi]t|jedu do pr|na cest/.test(s); }
  // Marti 12.6.: skupina Režie = produktivní práce BEZ píchnuté zakázky.
  // 'Rezie'/'Režie' jako project_ref = stará auto-stampovaná hodnota → bereme jako bez zakázky.
  function _isRezieRef(r){ r=(r||'').trim(); return !r || /^(rez|rež)ie$/i.test(r); }
  function _jobZak(e){ return !_jobMimo(e) && !_isRezieRef(e.project_ref); }
  function _jobRezie(e){ return !_jobMimo(e) && _isRezieRef(e.project_ref); }
  // Marti 19.6.: hodiny jobu — uzavřený má e.hours, BĚŽÍCÍ (bez konce) spočti z času příchodu do teď.
  function _jobHrs(e){
    if(e&&e.hours!=null) return Number(e.hours)||0;
    if(e&&e.is_active&&e.zac){ var p=(""+e.zac).split(":"); if(p.length>=2){
      var d=new Date(), st=new Date(d.getFullYear(),d.getMonth(),d.getDate(),(+p[0]||0),(+p[1]||0),0);
      var h=(d-st)/3600000; return h>0?h:0; } }
    return 0;
  }
  // Marti 12.6.: tři skupiny pro lištu — Speciální / Makám / Relax (podle kategorie typu).
  function _jobText(e){ return ((e.typ||'')+' '+(e.note||'')).toLowerCase(); }
  function _jobSpecial(e){ if(e.cat==='travel'||e.cat==='absence'||e.code==='day_end') return true;
    return /jedu do pr|na cest|lékař|lekar|doktor|dovolen|nemoc|neschopen|marod|sick|očr|ocr|mateřsk|matersk|otcovsk|konec dne|nepo[čc][íi]t|m[áa]m volno|jedn[aá]n|poch[uů]z/.test(_jobText(e)); }
  function _jobRelax2(e){ if(_jobSpecial(e)) return false; if(e.cat==='break') return true;
    return /pauz|p[řr]est[aá]v|relax|energ|jídl|jidl|provětr|provetr|naj[íi]st|ob[ěe]d/.test(_jobText(e)); }
  function _jobMakam(e){ return !_jobSpecial(e) && !_jobRelax2(e); }
  // Marti 11.6.: TEMPLATE „brand" dvoupanelu — lišta filtrů + joby + souhrn. Sdílený
  // pro „Tak to bylo dneska“, „Na včera si vzpomínám", „To už si nepamatuju".
  var _todaySt={f:"vse"}, _yestSt={f:"vse"}, _prevSt={f:"vse"};
  // Marti 19.6.: stejný „Dnešek" template lze zobrazit i pro jiného člověka (👁 v panelu skupin).
  // _dochViewUid != null → read-only pohled na docházku cizí osoby (bez akcí). Vlastní obrazovky ho resetují.
  var _dochViewUid=null, _dochViewName="";
  function _renderJobPanel(railId,listId,data,st){
    data=data||[];
    var rail=document.getElementById(railId);
    function _jobCnt(k){ if(k==="vse")return data.length;
      return data.filter(function(e){
        if(k==="makam")return _jobMakam(e);
        if(k==="spec")return _jobSpecial(e);
        if(k==="relax")return _jobRelax2(e);
        return false; }).length; }
    if(rail){ rail.innerHTML="";
      [["🌟","Speciální","spec"],["👷","Makám","makam"],["☕","Relax","relax"],["📋","Vše","vse"],["📊","Souhrn","souhrn"]].forEach(function(it){
        var on=(st.f===it[2]);
        var cnt=(it[2]==="souhrn")?0:_jobCnt(it[2]);
        var amb=(it[2]==="relax"||it[2]==="spec");  // makám zeleně, ostatní žlutě
        var bdg=(cnt>0)?'<span style="position:absolute;top:4px;right:6px;min-width:17px;height:17px;line-height:15px;border-radius:9px;border:1px solid rgba(0,0,0,.25);background:'+(amb?"var(--amber)":"var(--green)")+';color:#241a02;font-size:10px;font-weight:700;padding:0 3px;box-sizing:border-box;text-align:center;">'+cnt+'</span>':'';
        var b=el('<button style="position:relative;width:100%;box-sizing:border-box;margin:0;padding:11px 2px;font-size:10.5px;line-height:1.15;display:flex;flex-direction:column;align-items:center;gap:4px;border:1px solid '+(on?"var(--green)":"var(--bord)")+';background:'+(on?"var(--green)":"rgba(255,255,255,0.02)")+';color:'+(on?"#04150e":"var(--mut)")+';border-radius:13px;cursor:pointer;"><span style="font-size:27px;line-height:1;">'+it[0]+'</span>'+it[1]+bdg+'</button>');
        b.addEventListener("click",function(){ st.f=it[2]; _renderJobPanel(railId,listId,data,st); });
        rail.appendChild(b);
      });
    }
    _railSync(railId,listId);
    var t2=document.getElementById(listId); if(!t2) return;
    if(!data.length){ t2.innerHTML='<li style="color:var(--mut);border:none;">Nic tu není.</li>'; return; }
    if(st.f==="souhrn"){
      var msum=0, ssum=0, rsum=0;
      data.forEach(function(e){ var h=_jobHrs(e);
        if(_jobSpecial(e)) ssum+=h; else if(_jobRelax2(e)) rsum+=h; else msum+=h; });
      function _srow(lbl,val,col,strong){ return '<div style="display:flex;justify-content:space-between;padding:7px 2px;'+(strong?"border-bottom:1px solid var(--bord);margin-bottom:3px;":"")+'"><span'+(strong?' style="font-weight:700;color:#e8eef5;"':' class="hint"')+'>'+lbl+'</span><b style="color:'+col+';">'+fmtHM(val)+'</b></div>'; }
      t2.innerHTML='<li style="border:none;padding:0;"><div class="panel" style="margin:0;">'
        +_srow("Odmakáno", msum, "var(--green)", true)
        +_srow("👷 Makám", msum, "var(--green)", false)
        +_srow("🌟 Speciální", ssum, "var(--blue)", false)
        +_srow("☕ Relax", rsum, "var(--amber)", false)
        +'</div></li>';
      return;
    }
    var f=data.filter(function(e){
      if(st.f==="vse") return true;
      if(st.f==="makam") return _jobMakam(e);
      if(st.f==="spec") return _jobSpecial(e);
      if(st.f==="relax") return _jobRelax2(e);
      if(st.f==="zak") return _jobZak(e);
      if(st.f==="rezie") return _jobRezie(e);
      if(st.f==="mimo") return _jobMimo(e);
      return true; });
    if(!f.length){ t2.innerHTML='<li style="color:var(--mut);border:none;">Nic v této kategorii.</li>'; return; }
    t2.innerHTML=""; f.forEach(function(e){ t2.appendChild(_jobRow(e)); });
  }
  function _renderTodayPanel(todays){ _renderJobPanel("dochTodayRail","dochToday2",todays,_todaySt); }
  // Marti 11.6.: PLAN template — stejný systém (levý panel + pravá lišta + schovávání),
  // ale budoucí kategorie (Vše / 🏖 Absence / 💬 Ohlášení).
  var _planSt={f:"vse"};
  // Marti 11.6.: absenční/away kategorie do pravé lišty plánu (+ klasifikace dle textu).
  var _PLAN_CATS=[
    {k:"ho",   ic:"🏠", l:"Homeoffice",  rx:/home\s*office|homeoffice|\bho\b|z domova|domov/i},
    {k:"poch", ic:"📦", l:"Pochůzka",    rx:/poch[uů]z/i},
    {k:"dov",  ic:"🏖", l:"Dovolená",    rx:/dovolen/i},
    {k:"zar",  ic:"🧰", l:"Zařizuji",    rx:/zaři|zariz|vyřiz|vyriz|vyřid|vyrid/i},
    {k:"lek",  ic:"🩺", l:"Lékař",       rx:/lékař|lekar|doktor|kontrol/i},
    {k:"nem",  ic:"🤒", l:"Neschopenka", rx:/neschop|nemoc|sick/i},
    {k:"ocr",  ic:"👶", l:"OČR",         rx:/o[čc][řr]\b|ošetřov|osetrov/i},
    {k:"jed",  ic:"🤝", l:"Jednání",     rx:/jedn[aá]n/i},
    {k:"ohl",  ic:"💬", l:"Ohlášení",    rx:/dřív|driv|pozděj|pozdej|skonč|skonc|přijd|prijd/i},
    {k:"ost",  ic:"📌", l:"Ostatní",     rx:/.*/ }
  ];
  function _planCat(it){ var s=((it.note||"")+" "+(it.txt||"")).toLowerCase();
    for(var i=0;i<_PLAN_CATS.length;i++){ if(_PLAN_CATS[i].rx.test(s)) return _PLAN_CATS[i].k; }
    return ""; }
  function _planCatObj(k){ for(var i=0;i<_PLAN_CATS.length;i++){ if(_PLAN_CATS[i].k===k) return _PLAN_CATS[i]; } return null; }
  function _planRow(it){
    var li=document.createElement("li"); li.className="ct"; li.style.padding="0"; li.style.borderBottom="none";
    var _cc=_planCatObj(_planCat(it));
    var ic=_cc?_cc.ic:((it.kind==="absence")?"🏖":"💬"), bg=(it.kind==="ohlaseni")?"#4f8ef7":"#caa14a";
    var head=el('<div class="cthead"><div class="cav" style="background:'+bg+';font-size:26px;line-height:1;">'+ic+'</div><div style="flex:1;min-width:0;"><div class="ctname">'+esc(it.d||"")+'</div><div class="ctnum">'+esc(it.txt||it.note||"")+'</div></div></div>');
    var exp=el('<div class="ctexp" style="display:none;"></div>');
    if(it.kind==="ohlaseni" && it.id){
      var rw=el('<div style="display:flex;gap:8px;margin-top:6px;"></div>');
      var bd=el('<button class="green full" style="flex:1;margin:0;background:var(--amber);color:#241a02;">🗑 Smazat nahlášení</button>');
      bd.addEventListener("click",function(ev){ ev.stopPropagation(); if(!confirm("Smazat nahlášení „"+(it.note||"")+"\" ("+it.d+")?"))return; bd.disabled=true;
        api("POST","/api/v1/erp/app/attendance/announce-delete",{id:it.id}).then(function(j){ if(j&&j.ok){ dochLoad(); } else { bd.disabled=false; alert("Chyba: "+((j&&j.error)||"?")); } }); });
      rw.appendChild(bd); exp.appendChild(rw);
      exp.appendChild(el('<div class="hint" style="margin-top:8px;">Změnu nahlas nově přes 💬 Potřebuji ti něco říct → 🧭 Tady budu asi jinde.</div>'));
    } else {
      exp.appendChild(el('<div class="hint" style="margin-top:6px;">'+esc(it.txt||"")+'</div>'));
    }
    head.addEventListener("click",function(){
      var ulx=li.parentNode, wasOpen=li.classList.contains("open");
      if(ulx&&ulx.querySelectorAll) ulx.querySelectorAll("li.ct").forEach(function(o){ o.classList.remove("open"); var x=o.querySelector(".ctexp"); if(x)x.style.display="none"; });
      if(!wasOpen){ exp.style.display="block"; li.classList.add("open"); li.scrollIntoView({block:"nearest",behavior:"smooth"}); }
      var lid=(ulx&&ulx.id)||"dochPlan2"; _railSync(lid.replace(/2$/,"")+"Rail", lid);
    });
    li.appendChild(head); li.appendChild(exp); return li;
  }
  function _renderPlanPanel(railId,listId,items,st){
    items=items||[];
    var rail=document.getElementById(railId);
    if(rail){ rail.innerHTML="";
      [["📋","Vše","vse"]].concat(_PLAN_CATS.map(function(c){return [c.ic,c.l,c.k];})).forEach(function(it){
        var on=(st.f===it[2]);
        var cnt=(it[2]==="vse")?items.length:items.filter(function(x){return _planCat(x)===it[2];}).length;
        var bdg=(cnt>0)?'<span style="position:absolute;top:4px;right:6px;min-width:17px;height:17px;line-height:17px;border-radius:9px;background:var(--amber);color:#241a02;font-size:10px;font-weight:700;padding:0 3px;box-sizing:border-box;text-align:center;">'+cnt+'</span>':'';
        var b=el('<button style="position:relative;width:100%;box-sizing:border-box;margin:0;padding:11px 2px;font-size:10.5px;line-height:1.15;display:flex;flex-direction:column;align-items:center;gap:4px;border:1px solid '+(on?"var(--green)":"var(--bord)")+';background:'+(on?"var(--green)":"rgba(255,255,255,0.02)")+';color:'+(on?"#04150e":"var(--mut)")+';border-radius:13px;cursor:pointer;"><span style="font-size:27px;line-height:1;">'+it[0]+'</span>'+it[1]+bdg+'</button>');
        b.addEventListener("click",function(){ st.f=it[2]; _renderPlanPanel(railId,listId,items,st); });
        rail.appendChild(b);
      });
    }
    _railSync(railId,listId);
    var t2=document.getElementById(listId); if(!t2) return;
    var f=items.filter(function(it){ if(st.f==="vse")return true; return _planCat(it)===st.f; });
    if(!f.length){ t2.innerHTML='<li style="color:var(--mut);border:none;">Nic nahlášeného.</li>'; return; }
    t2.innerHTML=""; f.forEach(function(it){ t2.appendChild(_planRow(it)); });
  }
  function dochListLoad(){
    api("GET","/api/v1/erp/app/attendance/list?days=14"+(_dochViewUid?("&user_id="+encodeURIComponent(_dochViewUid)):""),"").then(function(j){
      var rows=(j&&j.entries)||[];
      window._dochEntries=rows; _dochSpans();
      var tdy=_locDate(0), yst=_locDate(-1);
      var t2=document.getElementById("dochToday2");
      if(t2){ var todays=rows.filter(function(e){ return (e.d||"")===tdy; });
        if(_dS&&_dS.todayhist) _dS.todayhist.val.textContent="";
        _renderTodayPanel(todays); }
      // Marti 11.6.: stejný template i pro včera a starší.
      if(document.getElementById("dochYest2")){
        _renderJobPanel("dochYestRail","dochYest2",rows.filter(function(e){ return (e.d||"")===yst; }),_yestSt); }
      if(document.getElementById("dochPrev2")){
        _renderJobPanel("dochPrevRail","dochPrev2",rows.filter(function(e){ return (e.d||"") && (e.d||"")<yst; }),_prevSt); }
    });
  }
  // Marti 14.6.: celoobrazovkové verze sekcí docházky (jako „Výhled"). Volají
  // stejné modulové loadery (dochListLoad/dochDailyLoad/paskaToggle), jen do
  // vlastního kontejneru s topbarem + Zpět.
  function _dochRail(listId,railId,h){
    return '<div style="display:flex;gap:10px;height:'+(h||"calc(100vh - 150px)")+';align-items:stretch;">'
      +'<div style="flex:1;min-width:0;overflow-y:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none;border:1px solid var(--bord);border-radius:12px;background:rgba(255,255,255,0.02);padding:2px 8px;">'
      +'<ul id="'+listId+'" style="padding:0;list-style:none;margin:0;"><li style="color:var(--mut);border:none;">Načítám…</li></ul></div>'
      +'<div id="'+railId+'" style="width:72px;flex:none;overflow-y:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none;display:flex;flex-direction:column;gap:7px;padding:0;"></div></div>';
  }
  function _dochTopPad(){ var _tb=app.querySelector('.topbar'); if(_tb)_tb.style.paddingTop="12px"; }
  function doch_dnesek(){ _dochViewUid=null; _dnesScreen("📅 Dnešek"); }
  function doch_historie(){ _dochViewUid=null; app.innerHTML=topbar("🕓 Historie docházky", true); _dochTopPad(); var p=el('<div class="panel"></div>'); app.appendChild(p);
    p.innerHTML='<div class="hint" style="margin:2px 0 6px;font-weight:600;">Včera</div>'+_dochRail("dochYest2","dochYestRail","38vh")
      +'<div class="hint" style="margin:14px 0 6px;font-weight:600;">Starší</div>'+_dochRail("dochPrev2","dochPrevRail","38vh");
    dochListLoad(); }
  // ✋ Samostatná obrazovka „Požádat o opravu" (Jirka 21.7.) — druhá cesta vedle
  // tlačítka v Historii. Bez časového omezení: nabídne posledních 14 dní a pro
  // starší je pole s datem.
  function doch_oprava_zadost(){
    _dochViewUid=null;
    app.innerHTML=topbar("✋ Požádat o opravu docházky", true); _dochTopPad();
    var p=el('<div class="panel"></div>'); app.appendChild(p);
    p.appendChild(el('<div class="hint" style="margin:2px 0 8px;">Vyber den, u kterého ti něco nesedí — třeba když jsi ho omylem potvrdil(a). '
      +'Žádost dostane kontrola docházky a ozve se ti. Potvrzený den to nevadí.<br>'
      +'⏳ <b>Jen za aktuální měsíc</b> — starší období je uzavřené mzdami. Když ti nesedí něco staršího, ozvi se kontrole docházky osobně.</div>'));
    var host=el('<div></div>');
    // volba dne — jen aktuální kalendářní měsíc (Peťa 21.7.)
    var _od=_opravaMesicOd(), _vcera=_locDate(-1);
    var dr=el('<div style="display:flex;gap:8px;align-items:center;margin-bottom:10px;"></div>');
    var di=el('<input type="date" min="'+_od+'" max="'+_locDate(0)+'" value="'+(_opravaDenPovolen(_vcera)?_vcera:_locDate(0))+'" style="flex:1;min-width:0;">');
    var db=el('<button class="ghost sm">Otevřít</button>');
    db.addEventListener("click",function(){
      if(!di.value) return;
      if(!_opravaDenPovolen(di.value)){
        host.innerHTML='<div class="hint" style="margin-top:10px;color:var(--amber);">⏳ Za tenhle den už žádat nejde — opravovat lze jen aktuální měsíc. Ozvi se prosím kontrole docházky osobně.</div>';
        return; }
      _opravaDen(host, di.value); });
    dr.appendChild(di); dr.appendChild(db); p.appendChild(dr);
    p.appendChild(el('<div class="hint" style="margin:2px 0 6px;font-weight:600;">Dny tohoto měsíce</div>'));
    var lst=el('<div></div>'); lst.innerHTML='<div class="hint">Načítám…</div>';
    p.appendChild(lst); p.appendChild(host);
    api("GET","/api/v1/erp/app/attendance/list?days=14","").then(function(j){
      lst.innerHTML="";
      var rows=(j&&j.entries)||[], dny={};
      rows.forEach(function(e2){
        if(!e2||!e2.d||e2.code==='day_end') return;
        if(!_opravaDenPovolen(e2.d)) return;   // starší měsíc = mimo (Peťa 21.7.)
        var g=dny[e2.d]||(dny[e2.d]={d:e2.d,od:null,do_:null,n:0});
        if(e2.zac&&(!g.od||e2.zac<g.od)) g.od=e2.zac;
        if(e2.kon&&(!g.do_||e2.kon>g.do_)) g.do_=e2.kon;
        g.n++;
      });
      var ks=Object.keys(dny).sort().reverse();
      if(!ks.length){ lst.appendChild(el('<div class="hint">V tomto měsíci tu zatím nic není — vyber datum výše.</div>')); return; }
      ks.forEach(function(k){
        var g=dny[k];
        // Hodiny tu VĚDOMĚ nesčítáme: „Nenároková práce (nad fond)" běží souběžně
        // se směnou, takže jakýkoli součet dvojitě počítá (20.7. dávalo 27:04).
        // Den se vybírá podle data — počet záznamů stačí, číslo bez záruky ne.
        var b=el('<button class="ghost full" style="margin-top:6px;text-align:left;font-size:13.5px;">'
          +esc(_czDayLabel(g.d))+' · '+esc(g.od||'?')+'–'+esc(g.do_||'…')
          +' <span style="color:var(--mut);font-weight:400;">('+g.n+' zázn.)</span></button>');
        b.addEventListener("click",function(){ _opravaDen(host, g.d); });
        lst.appendChild(b);
      });
    }).catch(function(){ lst.innerHTML='<div class="hint">Seznam se nepodařilo načíst — vyber datum výše.</div>'; });
  }
  // Detail vybraného dne (read-only) + volba „celý den" / konkrétní záznam.
  function _opravaDen(host, day){
    host.innerHTML='<div class="hint" style="margin-top:10px;">Načítám den…</div>';
    api("GET","/api/v1/erp/app/attendance/day-detail?day="+encodeURIComponent(day),"").then(function(jd){
      host.innerHTML="";
      var box=el('<div style="margin-top:10px;border-top:1px solid var(--bord);padding-top:10px;"></div>');
      box.appendChild(el('<div style="font-weight:700;font-size:15px;">'+esc(_czDayLabel(day))+'</div>'));
      var es=(jd&&jd.entries)||[];
      var form=el('<div></div>');
      if(!es.length){
        box.appendChild(el('<div class="hint" style="margin-top:4px;">V tento den nemáš žádné záznamy — napiš to do žádosti.</div>'));
      } else {
        box.appendChild(el('<div class="hint" style="margin-top:4px;">Čeho se to týká?</div>'));
        es.forEach(function(e2){
          var lbl=_opravaLbl(e2);
          var b=el('<button class="ghost full" style="margin-top:6px;text-align:left;font-size:13.5px;">'+esc(lbl)+'</button>');
          b.addEventListener("click",function(){ _dochOpravaBox(form, day, e2.id, lbl, null); });
          box.appendChild(b);
        });
      }
      var bd=el('<button class="ghost full" style="margin-top:8px;text-align:left;font-size:13.5px;border-color:var(--amber);color:var(--amber);">✋ Nesedí mi celý den…</button>');
      bd.addEventListener("click",function(){ _dochOpravaBox(form, day, 0, "", null); });
      box.appendChild(bd); box.appendChild(form);
      host.appendChild(box);
      try{ box.scrollIntoView({behavior:"smooth",block:"start"}); }catch(e){}
    }).catch(function(){ host.innerHTML='<div class="hint" style="margin-top:10px;">Den se nepodařilo načíst.</div>'; });
  }
  function doch_zitrek(){ _dochViewUid=null; app.innerHTML=topbar("🌅 Tady budu jinde", true); _dochTopPad(); var p=el('<div class="panel"></div>'); app.appendChild(p); p.innerHTML=_dochRail("dochPlan2","dochPlanRail"); dochDailyLoad(); }
  function moje_finance(){ app.innerHTML=topbar("💰 Moje finance", true); _dochTopPad(); var p=el('<div class="panel"></div>'); app.appendChild(p); p.innerHTML='<div id="paskaBox"><div class="hint">Načítám…</div></div>'; paskaToggle(true); }
  function moje_zadosti(){ app.innerHTML=topbar("📋 Moje hlášené / neschválené žádosti", true); _dochTopPad(); var p=el('<div class="panel"></div>'); app.appendChild(p);
    var box=el('<div></div>'); p.appendChild(box); box.innerHTML='<div class="hint">Načítám…</div>';
    api("GET","/api/v1/erp/app/attendance/announced-future","").then(function(j){
      box.innerHTML=""; var it=(j&&j.items)||[];
      if(!it.length){ box.appendChild(el('<div class="hint">Žádné nevyřízené žádosti. 👍</div>')); return; }
      it.forEach(function(r){ box.appendChild(el('<div style="display:flex;justify-content:space-between;align-items:center;gap:8px;border-bottom:1px solid var(--bord);padding:10px 2px;font-size:14px;"><span><b>'+esc(r.d||"")+'</b> — '+esc(r.note||"")+'</span></div>')); });
    });
  }
  // 💰 Výplatní páska (Marti 7.6.: „každej na ni má nárok") — jen vlastní data.
  // Marti 7.6. večer: ochrana — PIN + jen mimo směnu (aby si lidé v pracovní
  // době neukazovali, kolik kdo bere). PIN žije jen v paměti otevřené sekce.
  var _CZ_MES=["","leden","únor","březen","duben","květen","červen","červenec","srpen","září","říjen","listopad","prosinec"];
  var _paskaPin=null;
  function paskaToggle(open){
    var box=document.getElementById("paskaBox"); if(!box)return;
    if(open){ paskaLoad(0,0); return; }
    _paskaPin=null;  // zavření sekce = zámek, PIN znovu při dalším otevření
    box.innerHTML='<div class="hint">🔒 Páska je zamčená.</div>';
    if(_dS&&_dS.paska)_dS.paska.val.textContent="";
  }
  function _paskaMsg(html){
    var box=document.getElementById("paskaBox"); if(!box)return null;
    box.innerHTML=""; var w=el('<div style="padding:4px 0;"></div>'); box.appendChild(w); return w;
  }
  function _pinInput(){
    return el('<input type="password" inputmode="numeric" pattern="[0-9]*" maxlength="4" autocomplete="off" placeholder="• • • •" style="width:120px;text-align:center;font-size:20px;letter-spacing:6px;margin-top:6px;">');
  }
  function paskaPinSetup(){
    var w=_paskaMsg(); if(!w)return;
    w.appendChild(el('<div style="font-weight:700;">🔐 Nastav si PIN k pásce</div>'));
    w.appendChild(el('<div class="hint" style="margin:4px 0 2px;">Páska je jen tvoje. Zvol si 4místný PIN — budeš ho zadávat při každém otevření.</div>'));
    var i1=_pinInput(), i2=_pinInput(); i2.placeholder="znovu";
    var row=el('<div style="display:flex;gap:10px;align-items:center;"></div>'); row.appendChild(i1); row.appendChild(i2); w.appendChild(row);
    var st=el('<div class="hint" style="margin-top:6px;"></div>'); w.appendChild(st);
    var b=el('<button class="green full" style="margin-top:8px;">Nastavit PIN</button>'); w.appendChild(b);
    b.addEventListener("click",function(){
      var p1=(i1.value||"").trim(), p2=(i2.value||"").trim();
      if(!/^[0-9]{4}$/.test(p1)){ st.textContent="PIN jsou 4 číslice."; return; }
      if(p1!==p2){ st.textContent="PINy se neshodují."; return; }
      b.disabled=true; st.textContent="Ukládám…";
      api("POST","/api/v1/erp/app/pin/set",{pin:p1}).then(function(j){
        if(j&&j.ok){ _paskaPin=p1; paskaLoad(0,0); }
        else{ b.disabled=false; st.textContent=(j&&j.note)||"Nepodařilo se uložit."; }
      });
    });
  }
  function paskaPinEntry(j){
    var w=_paskaMsg(); if(!w)return;
    _paskaPin=null;
    w.appendChild(el('<div style="font-weight:700;">🔐 Zadej PIN k pásce</div>'));
    var st=el('<div class="hint" style="margin:4px 0 2px;"></div>'); w.appendChild(st);
    if(j&&j.error==="pin_wrong") st.textContent="PIN nesedí — zbývá pokusů: "+(j.left||0)+".";
    if(j&&j.error==="pin_locked"){ st.textContent="⏳ Příliš mnoho pokusů. Zkus to za "+(j.minutes||15)+" min."; return; }
    var i1=_pinInput(); w.appendChild(i1);
    var b=el('<button class="green full" style="margin-top:8px;">Odemknout</button>'); w.appendChild(b);
    function go(){ var p=(i1.value||"").trim(); if(!/^[0-9]{4}$/.test(p)){ st.textContent="PIN jsou 4 číslice."; return; } _paskaPin=p; paskaLoad(0,0); }
    b.addEventListener("click",go);
    i1.addEventListener("input",function(){ if(i1.value.length===4) go(); });
    var f=el('<button class="ghost full" style="margin-top:8px;font-size:13px;">Zapomněl/a jsem PIN…</button>'); w.appendChild(f);
    f.addEventListener("click",function(){
      f.disabled=true;
      api("POST","/api/v1/erp/app/pin/forgot",{}).then(function(r){
        if(!(r&&r.ok)){ f.disabled=false; st.textContent=(r&&(r.note||("✗ "+r.error)))||"SMS se nepodařilo poslat."; return; }
        var w2=_paskaMsg(); if(!w2)return;
        w2.appendChild(el('<div style="font-weight:700;">📨 Poslali jsme ti SMS kód</div>'));
        w2.appendChild(el('<div class="hint" style="margin:4px 0 2px;">Na číslo '+esc(r.phone||"")+'. Zadej kód a zvol nový PIN.</div>'));
        var ci=el('<input inputmode="numeric" pattern="[0-9]*" maxlength="6" autocomplete="off" placeholder="SMS kód" style="width:140px;text-align:center;font-size:18px;letter-spacing:4px;margin-top:6px;">');
        var n1=_pinInput(); n1.placeholder="nový PIN";
        w2.appendChild(ci); w2.appendChild(el('<div></div>')); w2.appendChild(n1);
        var st2=el('<div class="hint" style="margin-top:6px;"></div>'); w2.appendChild(st2);
        var b2=el('<button class="green full" style="margin-top:8px;">Nastavit nový PIN</button>'); w2.appendChild(b2);
        b2.addEventListener("click",function(){
          var c=(ci.value||"").trim(), p=(n1.value||"").trim();
          if(!/^[0-9]{6}$/.test(c)){ st2.textContent="Kód má 6 číslic."; return; }
          if(!/^[0-9]{4}$/.test(p)){ st2.textContent="PIN jsou 4 číslice."; return; }
          b2.disabled=true; st2.textContent="Ukládám…";
          api("POST","/api/v1/erp/app/pin/set",{code:c,pin:p}).then(function(x){
            if(x&&x.ok){ _paskaPin=p; paskaLoad(0,0); }
            else{ b2.disabled=false; st2.textContent=(x&&x.note)||"Nepodařilo se."; }
          });
        });
      });
    });
  }
  function paskaLoad(y,m){
    var box=document.getElementById("paskaBox"); if(!box)return;
    api("POST","/api/v1/erp/app/payslip",{y:y||0,m:m||0,pin:_paskaPin||""}).then(function(j){
      box=document.getElementById("paskaBox"); if(!box)return;
      if(j&&j.error==="on_shift"){
        box.innerHTML='<div class="hint">💼 Teď jsi v práci — páska počká. Otevřeš ji po odchodu nebo na pauze.</div>';
        return;
      }
      if(j&&j.error==="pin_not_set"){ paskaPinSetup(); return; }
      if(j&&(j.error==="pin_required"||j.error==="pin_wrong"||j.error==="pin_locked")){ paskaPinEntry(j); return; }
      if(!j||!j.ok){ box.innerHTML='<div class="hint">Pásku se nepodařilo načíst.</div>'; return; }
      if(!j.items||!j.items.length){ box.innerHTML='<div class="hint">'+esc(j.note||"Zatím žádné pásky.")+'</div>'; if(_dS&&_dS.paska)_dS.paska.val.textContent=""; return; }
      var ps=j.periods||[]; var idx=-1;
      for(var i2=0;i2<ps.length;i2++){ if(ps[i2].y===j.y&&ps[i2].m===j.m){ idx=i2; break; } }
      var hd=el('<div style="display:flex;align-items:center;gap:8px;margin:2px 0 8px;"></div>');
      var bPrev=el('<button class="ghost sm">◀</button>');
      var bNext=el('<button class="ghost sm">▶</button>');
      hd.appendChild(bPrev);
      hd.appendChild(el('<div style="flex:1;text-align:center;font-weight:700;">'+esc(_CZ_MES[j.m]||j.m)+' '+j.y+'</div>'));
      hd.appendChild(bNext);
      // periods jsou DESC: další v poli = starší
      bPrev.disabled = idx < 0 || idx >= ps.length-1;
      bNext.disabled = idx <= 0;
      bPrev.addEventListener("click",function(){ var p=ps[idx+1]; if(p) paskaLoad(p.y,p.m); });
      bNext.addEventListener("click",function(){ var p=ps[idx-1]; if(p) paskaLoad(p.y,p.m); });
      box.innerHTML=""; box.appendChild(hd);
      // Marti 7.6.: dvě firmy = DVĚ samostatné pásky, každá s plnou hlavičkou.
      var firmy={}; var poradi=[];
      j.items.forEach(function(it){
        var k=it.firma||"?";
        if(!firmy[k]){ firmy[k]={nazev:it.firma_nazev||k, items:[]}; poradi.push(k); }
        firmy[k].items.push(it);
      });
      var celkemVyplata=0;
      poradi.forEach(function(fk){
        var f=firmy[fk];
        var card=el('<div style="background:var(--bg);border:1px solid var(--bord);border-radius:12px;padding:12px;margin-bottom:10px;"></div>');
        card.appendChild(el('<div style="font-weight:700;font-size:14.5px;">🏢 '+esc(f.nazev)+'</div>'));
        card.appendChild(el('<div class="hint" style="margin:2px 0 8px;">Výplatní páska · '+esc(j.jmeno||"")+' · '+esc(_CZ_MES[j.m]||j.m)+' '+j.y+'</div>'));
        // Mzdový LIST k pásce (Marti 27.6.) — úvazek, fond PD, odpracováno, průměry, pojišťovna
        (function(){
          var lst=(j.list||[]).filter(function(x){ return (x.firma||"?")===fk; });
          if(!lst.length) return;
          var L=lst[0];
          function combo(dni,hod){ var a=[]; if(dni!=null)a.push(Math.round(dni*10)/10+" dní"); if(hod!=null)a.push(Math.round(hod*10)/10+" h"); return a.length?a.join(" · "):null; }
          function lrow(lbl,val){ return val==null?"":('<div style="display:flex;justify-content:space-between;gap:8px;padding:3px 0;border-bottom:1px solid var(--bord);"><span style="font-size:12.5px;color:var(--mut);">'+esc(lbl)+'</span><span style="font-size:12.5px;font-weight:600;">'+esc(val)+'</span></div>'); }
          var html=lrow("Týdenní úvazek", L.tydenni_uvazek!=null?(L.tydenni_uvazek+" h"):null)
            +lrow("Denní úvazek", L.denni_uvazek!=null?(Math.round(L.denni_uvazek*10)/10+" h"):null)
            +lrow("Fond prac. doby", combo(L.fond_dny,L.fond_hod))
            +lrow("Odpracováno", combo(L.odprac_dny,L.odprac_hod))
            +lrow("Přesčas", L.prescas_hod!=null?(Math.round(L.prescas_hod*10)/10+" h"):null)
            +lrow("Svátek", L.svatek_tarif_hod!=null?(Math.round(L.svatek_tarif_hod*10)/10+" h"):null)
            +lrow("Průměrný výdělek/h", L.prum_vydelek_hod!=null?(Math.round(L.prum_vydelek_hod*100)/100+" Kč"):null)
            +lrow("Základní mzda", L.zakladni_mzda!=null?(Math.round(L.zakladni_mzda).toLocaleString("cs")+" Kč"):null)
            +lrow("Zdrav. pojišťovna", L.zdrav_pojistovna);
          if(!html) return;
          var det=el('<details style="margin:0 0 10px;"></details>');
          det.appendChild(el('<summary style="cursor:pointer;font-size:13px;color:var(--mut);padding:4px 0;">📄 Mzdový list (úvazek, fond, odpracováno)</summary>'));
          var dbox=el('<div style="padding:4px 2px 2px;"></div>'); dbox.innerHTML=html;
          det.appendChild(dbox); card.appendChild(det);
        })();
        // Marti 7.6.: lidská struktura — 1) co firma poskytla (vč. odvodů firmy)
        // 2) FIRMA DALA CELKEM (superhrubá) 3) červené srážky (sleva na dani +)
        // 4) zelená Výplata na účet. Klasifikace dle názvu — doladí Šárka.
        var dal=[], firmaOdvody=[], srazky=[], vyp=[];
        f.items.forEach(function(it){
          var n=(it.nazev||"").toLowerCase();
          if(it.kc===0 && !it.hod && !it.dny) return;          // nulové technické řádky skrýt
          if(n.substring(0,7)==="výplata"){ vyp.push(it); return; }
          if(n.indexOf("firma")>=0){ firmaOdvody.push(it); return; }  // odvody firmy → dolů červeně (Marti: „to je teprve síla")
          if(it.hruba || n.indexOf("paušál")>=0 || n.indexOf("pausal")>=0
             || n.indexOf("stravenk")>=0 || n.indexOf("benefit")>=0 || n.indexOf("náhrad")>=0
             || (!it.kc && (it.hod||it.dny))){ dal.push(it); return; }
          srazky.push(it);
        });
        function radek(it, mode){  // mode: 'plus' | 'minus' | 'sleva'
          var kc="";
          if(it.kc!=null){
            var v=Math.round(it.kc).toLocaleString("cs")+" Kč";
            kc = (mode==="minus") ? ("− "+v) : ((mode==="sleva") ? ("+ "+v) : v);
          }
          var col = (mode==="minus") ? "var(--red)" : ((mode==="sleva") ? "var(--green)" : "var(--tx)");
          var sub=(it.hod?(it.hod+" h"):"")+(it.dny?((it.hod?" · ":"")+it.dny+" dní"):"");
          return el('<li style="display:flex;justify-content:space-between;align-items:center;gap:8px;">'
            +'<span class="nt" style="font-size:13.5px;'+(mode==="minus"?'color:var(--red);':'')+'">'+esc(it.nazev)+(sub?('<div class="sub" style="color:var(--mut);font-size:11.5px;">'+esc(sub)+'</div>'):'')+'</span>'
            +'<span class="nm" style="margin:0;white-space:nowrap;color:'+col+';">'+esc(kc)+'</span></li>');
        }
        var ul=el('<ul></ul>');
        var superhruba=0;
        dal.forEach(function(it){ superhruba+=(it.kc||0); ul.appendChild(radek(it,"plus")); });
        firmaOdvody.forEach(function(it){ superhruba+=(it.kc||0); });  // do CELKEM patří, zobrazí se dole červeně
        ul.appendChild(el('<li style="display:flex;justify-content:space-between;align-items:center;gap:8px;background:rgba(79,142,247,.08);border-radius:8px;padding:12px 8px;">'
          +'<span class="nt" style="font-weight:700;font-size:13.5px;">🏢 Firma dala celkem (superhrubá)</span>'
          +'<span class="nm" style="margin:0;white-space:nowrap;font-weight:700;">'+Math.round(superhruba).toLocaleString("cs")+' Kč</span></li>'));
        firmaOdvody.forEach(function(it){ ul.appendChild(radek(it,"minus")); });
        srazky.forEach(function(it){
          var n=(it.nazev||"").toLowerCase();
          ul.appendChild(radek(it, n.indexOf("sleva")>=0 ? "sleva" : "minus"));
        });
        var vyplata=0;
        vyp.forEach(function(it){
          vyplata+=(it.kc||0);
          ul.appendChild(el('<li style="display:flex;justify-content:space-between;align-items:center;gap:8px;background:rgba(16,185,129,.10);border-radius:8px;padding:13px 8px;">'
            +'<span class="nt" style="font-weight:700;font-size:14px;">💚 '+esc(it.nazev)+'</span>'
            +'<span class="nm" style="margin:0;white-space:nowrap;font-weight:700;color:var(--green);font-size:15px;">'+Math.round(it.kc||0).toLocaleString("cs")+' Kč</span></li>'));
        });
        card.appendChild(ul);
        box.appendChild(card);
        celkemVyplata+=vyplata;
      });
      box.appendChild(el('<div class="hint">Zdroj: mzdový systém Helios (oficiální zúčtování).</div>'));
      // Marti 7.6. večer: částka ani zámeček do hlavičky sekce NEPATŘÍ.
      if(_dS&&_dS.paska) _dS.paska.val.textContent="";
    });
  }
  // Rozsah práce „od prvního píchnutí do posledního odpíchnutí" (Marti 7.6.).
  function _dochSpans(){
    var es=window._dochEntries||[];
    var today=_locDate(0), yest=_locDate(-1);
    function mk(d,id){
      var e2=document.getElementById(id); if(!e2)return;
      var rows=es.filter(function(e){return e.d===d&&e.zac;});
      if(!rows.length){ e2.style.display="none"; return; }
      var zacs=rows.map(function(e){return e.zac;}).sort();
      var kons=rows.filter(function(e){return e.kon;}).map(function(e){return e.kon;}).sort();
      var act=rows.some(function(e){return e.is_active;});
      e2.style.display="";
      e2.innerHTML='Práce od <b style="color:var(--tx);">'+esc(zacs[0])+'</b>'
        +(act?' — <span style="color:var(--green);">běží</span>'
              :(kons.length?(' do <b style="color:var(--tx);">'+esc(kons[kons.length-1])+'</b>'):''));
    }
    mk(today,"dochSpanToday"); mk(yest,"dochSpanYest");
  }
  // ───── 🛠 OPRAVY DOCHÁZKY POVĚŘENÝMI (Jirka 9.7.2026, zadal Marti Pašek) ─────
  // Editoři = staff_group „DOCHÁZKA - OPRAVY" (backend /app/attendance/fix/*).
  // Oprava = supersede + nový záznam s povinným důvodem; dotčený dostane
  // notifikaci a může rozporovat. Lidé sami zpětně needitují.
  var _FIX_REASONS=["zapomenutý odchod","zapomenutý návrat z pauzy","zapomenutý příchod","zapomenutý oběd/pauza","mezera v docházce","chybný typ záznamu","omylem založený záznam"];
  var _FIX_TYPES=[["work","🧾 Práce"],["overhead","🧰 Režie"],["homeoffice","🏠 Home office"],["commute","🚗 Cesta"],["break","☕ Pauza"]];
  var _FIX_CINN=null;
  function _fixLoadCinn(cb){ if(_FIX_CINN){cb(_FIX_CINN);return;} api("GET","/api/v1/erp/app/attendance/fix/cinnosti","").then(function(j){ _FIX_CINN=(j&&j.cinnosti)||[]; cb(_FIX_CINN); }); }
  function _fixMkCombo(items,opts){
    opts=opts||{};
    var root=el('<div class="scb" style="'+(opts.style||'margin-top:6px;')+'"></div>');
    var inp=el('<input type="text" autocomplete="off" style="width:100%;" placeholder="'+esc(opts.ph||'Hledat…')+'">');
    var list=el('<div class="scb-list" style="display:none;"></div>');
    root.appendChild(inp);root.appendChild(list);
    var _items=(items||[]).slice(),_val='',_open=false,_hl=-1,_filt=[];
    function fold(s){s=String(s==null?'':s).toLowerCase();try{return s.normalize('NFD').replace(/[̀-ͯ]/g,'');}catch(e){return s;}}
    function labelOf(v){for(var i=0;i<_items.length;i++){if(String(_items[i].v)===String(v))return _items[i].t;}return (v?String(v):'');}
    function setVal(v,fire){_val=(v==null?'':v);inp.value=labelOf(_val);if(fire)root.dispatchEvent(new Event('change'));}
    Object.defineProperty(root,'value',{configurable:true,get:function(){return _val;},set:function(v){setVal(v,false);}});
    root._input=inp;
    root._setItems=function(arr){_items=(arr||[]).slice();if(_open)draw(inp.value);else inp.value=labelOf(_val);};
    function close(){list.style.display='none';_open=false;_hl=-1;}
    function draw(q){
      var f=fold(q);_filt=[];
      if(opts.empty)_filt.push({v:'',t:(opts.emptyText||'— nevybráno —'),none:true});
      for(var i=0;i<_items.length;i++){var it=_items[i];if(!f||fold(it.t+' '+it.v).indexOf(f)>=0)_filt.push(it);}
      list.innerHTML='';
      if(!_filt.length){list.appendChild(el('<div class="scb-it none">nic nenalezeno</div>'));return;}
      _filt.forEach(function(it,i){
        var d=el('<div class="scb-it'+(it.none?' none':'')+(i===_hl?' hl':'')+'">'+esc(it.t||'')+'</div>');
        d.addEventListener('mousedown',function(ev){ev.preventDefault();setVal(it.v,true);close();try{inp.blur();}catch(e){}});
        list.appendChild(d);
      });
    }
    function open(all){_open=true;list.style.display='block';draw(all?'':inp.value);}
    inp.addEventListener('focus',function(){_hl=-1;if(inp.select)try{inp.select();}catch(e){}open(true);});
    inp.addEventListener('input',function(){_hl=-1;open(false);});
    inp.addEventListener('blur',function(){setTimeout(function(){inp.value=labelOf(_val);close();},150);});
    inp.addEventListener('change',function(ev){ev.stopPropagation();});
    inp.addEventListener('keydown',function(ev){
      if(ev.key==='ArrowDown'){if(!_open){open(true);}else{_hl=Math.min(_filt.length-1,_hl+1);draw(inp.value);}ev.preventDefault();}
      else if(ev.key==='ArrowUp'){if(_open){_hl=Math.max(0,_hl-1);draw(inp.value);ev.preventDefault();}}
      else if(ev.key==='Enter'){if(_open){var p=_filt[_hl>=0?_hl:0];if(p){setVal(p.v,true);close();}ev.preventDefault();}}
      else if(ev.key==='Escape'){inp.value=labelOf(_val);close();}
    });
    if(opts.initial!=null&&opts.initial!=='')setVal(opts.initial,false);
    return root;
  }
  function _fixMkTyp(cur){return _fixMkCombo(_FIX_TYPES.map(function(t){return {v:t[0],t:t[1]};}),{ph:'🔍 typ…',initial:(cur||_FIX_TYPES[0][0])});}
  function _fixMkCin(cur){ var w=el('<div style="margin-top:6px;"></div>'); w.appendChild(el('<div class="hint" style="margin-bottom:2px;">🔧 Činnost (jen Práce/Režie, nepovinné):</div>')); var c=_fixMkCombo([],{ph:'🔍 činnost…',empty:true,emptyText:'— nevybráno —',style:'margin-top:0;'}); _fixLoadCinn(function(list){ c._setItems(list.map(function(x){return {v:x.id,t:(x.icon?x.icon+' ':'')+x.name};})); if(cur)c.value=cur; }); w.appendChild(c); w._sel=c; return w; }
  function _fixCinShow(w,typ){ w.style.display=(typ==="work"||typ==="overhead")?"":"none"; }
  var _FIX_ZAK=null;
  function _fixLoadZak(cb){ if(_FIX_ZAK){cb(_FIX_ZAK);return;} api("GET","/api/v1/erp/app/attendance/fix/zakazky","").then(function(j){ _FIX_ZAK=(j&&j.zakazky)||[]; cb(_FIX_ZAK); }); }
  function _fixMkZak(cur){ var c=_fixMkCombo([],{ph:'🔍 zakázka (číslo/název)…',empty:true,emptyText:'— zakázka (jen u práce) —'}); if(cur){ c._setItems([{v:cur,t:cur}]); c.value=cur; } _fixLoadZak(function(list){ var its=list.map(function(z){return {v:z.cislo,t:z.cislo+(z.nazev?(' — '+z.nazev):'')};}); var found=false; list.forEach(function(z){ if(cur&&z.cislo===cur)found=true; }); if(cur&&!found)its.unshift({v:cur,t:cur+' (mimo seznam)'}); c._setItems(its); if(cur)c.value=cur; }); return c; }
  function _fixReasonBox(){
    var w=el('<div style="margin-top:8px;"></div>');
    w.appendChild(el('<div class="hint" style="margin-bottom:4px;">Důvod (povinný):</div>'));
    var chips=el('<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:6px;"></div>');
    var ta=el('<input placeholder="…nebo napiš vlastní důvod" style="width:100%;">');
    _FIX_REASONS.forEach(function(r){
      var c=el('<button class="ghost sm" style="font-size:12px;">'+esc(r)+'</button>');
      c.addEventListener("click",function(){ ta.value=r; });
      chips.appendChild(c);
    });
    w.appendChild(chips); w.appendChild(ta); w._input=ta;
    return w;
  }
  function _fixConfirm(fx, txt, onYes){
    fx.querySelectorAll(".trimconf").forEach(function(x){x.remove();});
    var cw=el('<div class="trimconf" style="margin-top:6px;background:rgba(16,185,129,.10);border:1px solid var(--green);border-radius:8px;padding:10px;"></div>');
    cw.appendChild(el('<div style="font-size:14px;">'+txt+'</div>'));
    var br=el('<div style="display:flex;gap:8px;margin-top:8px;"></div>');
    var ano=el('<button class="green sm" style="flex:1;">Ano</button>');
    var ne=el('<button class="ghost sm">Ne</button>');
    br.appendChild(ano); br.appendChild(ne); cw.appendChild(br); fx.appendChild(cw); try{ cw.scrollIntoView({behavior:"smooth",block:"center"}); }catch(e){}
    ne.addEventListener("click",function(){ cw.remove(); });
    ano.addEventListener("click",function(){ ano.disabled=true; ne.disabled=true; onYes(cw); });
  }
  function doch_opravy(){
    app.innerHTML=topbar("🛠 Opravy docházky", true); _dochTopPad();
    var p=el('<div class="panel"></div>'); app.appendChild(p);
    var tabs=el('<div style="display:flex;gap:8px;margin:2px 0 10px;flex-wrap:wrap;"></div>');
    var box=el('<div></div>');
    p.appendChild(tabs); p.appendChild(box);
    p.appendChild(el('<div style="height:120px;"></div>'));  // rezerva pod spodní lištu (Jirka 10.7.)
    function tabBtn(lbl,fn){
      var b=el('<button class="ghost sm">'+lbl+'</button>');
      b.addEventListener("click",function(){
        tabs.querySelectorAll("button").forEach(function(x){ x.style.borderColor=""; x.style.color=""; });
        b.style.borderColor="var(--green)"; b.style.color="var(--green)"; fn();
      });
      tabs.appendChild(b); return b;
    }
    // Jirka 21.7.: taby dle práv (parita s ERP). Editor (can_fix) → fronta/lidé/
    // historie; držitel zámku (can_lock) → záložka Zámek. Lock-only (Šárka, rodič
    // bez editorství) vidí JEN Zámek. Práva z gate (window._canFixDoch/_canLockDoch).
    var _cf=(window._canFixDoch===true), _cl=(window._canLockDoch===true);
    var _first=null;
    if(_cf){
      var tq=tabBtn("📥 K vyřešení",function(){ _fixQueueLoad(box); });
      tabBtn("🔍 Najít člověka",function(){ _fixPeopleLoad(box); });
      tabBtn("📜 Historie oprav",function(){ _fixAuditLoad(box); });
      _first=tq;
    }
    if(_cl){
      var tl=tabBtn("🔒 Zámek období",function(){ _fixLockLoad(box); });
      if(!_first) _first=tl;
    }
    if(_first) _first.click();
    else box.innerHTML='<div class="hint">Nemáš oprávnění k opravám docházky.</div>';
  }
  function _fixLockLoad(box){
    box.innerHTML='<div class="hint">Načítám zámky…</div>';
    api("GET","/api/v1/erp/app/attendance/period-lock","").then(function(j){
      box.innerHTML="";
      if(!(j&&j.ok)){ box.innerHTML='<div class="hint">✗ '+esc((j&&j.error)||"chyba")+'</div>'; return; }
      box.appendChild(el('<div class="hint" style="margin-bottom:8px;">Uzamčený měsíc nelze opravovat (mzdy zpracovány) — ani držitelem zámku. Nejdřív odemknout, opravit a zase zamknout. Zamyká/odemyká Peťa, Šárka, Jirka a rodiče.</div>'));
      if(j.can_lock){
        var w=el('<div style="background:var(--bg);border:1px solid var(--bord);border-radius:10px;padding:10px;margin-bottom:10px;"></div>');
        var r1=el('<div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;"></div>');
        var mi=el('<input type="number" min="1" max="12" placeholder="měsíc" style="width:90px;">');
        var yi=el('<input type="number" min="2024" max="2100" value="'+(new Date().getFullYear())+'" style="width:100px;">');
        var bl=el('<button class="green sm">🔒 Zamknout</button>');
        var bu=el('<button class="ghost sm" style="border-color:var(--amber);color:var(--amber);">🔓 Odemknout</button>');
        r1.appendChild(mi);r1.appendChild(yi);r1.appendChild(bl);r1.appendChild(bu);w.appendChild(r1);
        var st=el('<div class="hint" style="margin-top:6px;"></div>');w.appendChild(st);
        function doLock(lock){
          var m=parseInt(mi.value||'0'),y=parseInt(yi.value||'0');
          if(!(m>=1&&m<=12&&y>=2024)){st.textContent='Zadej měsíc a rok.';return;}
          api("POST","/api/v1/erp/app/attendance/period-lock",{rok:y,mesic:m,lock:lock}).then(function(x){
            if(x&&x.ok)_fixLockLoad(box);else st.textContent='✗ '+((x&&x.error)||"chyba");
          });
        }
        bl.addEventListener("click",function(){doLock(true);});
        bu.addEventListener("click",function(){doLock(false);});
        box.appendChild(w);
      }
      (j.items||[]).forEach(function(r){
        box.appendChild(el('<div style="border-bottom:1px solid var(--bord);padding:8px 2px;font-size:13px;">🔒 <b>'+r.mesic+'/'+r.rok+'</b> <span class="hint">('+esc(r.kdo||"?")+', '+esc(r.od||"")+(r.note?(" — "+esc(r.note)):"")+')</span></div>'));
      });
    });
  }
  function _fixOpenDay(uid2,name,day){ window._fixCtx={uid:uid2,name:name||"",day:day}; go("doch_opravy_den"); }
  function _fixMarkDone(c){try{c.style.borderColor='var(--green)';c.style.background='rgba(16,185,129,.08)';var hd=c.firstChild;if(hd)hd.innerHTML+=' <span style="background:#123c26;color:#8fe0a0;font-size:10px;padding:1px 7px;border-radius:8px;font-weight:700;">✓ opraveno</span>';}catch(e){}}
  function _fixQuickDone(c,payload){payload.reason='opraveno v detailu dne';api("POST","/api/v1/erp/app/attendance/fix/resolve",payload).then(function(x){if(x&&x.ok){c.remove();}else{c._fx.innerHTML='<div class="hint">✗ '+esc((x&&x.error)||"Nepodařilo se.")+'</div>';}});}
  function _fixQueueLoad(box){
    box.innerHTML='<div class="hint">Načítám frontu…</div>';
    api("GET","/api/v1/erp/app/attendance/fix/queue","").then(function(j){
      box.innerHTML="";
      if(!(j&&j.ok)){ box.innerHTML='<div class="hint">✗ '+esc((j&&j.error)||"Nepodařilo se načíst.")+'</div>'; return; }
      var an=j.anomalie||[], rz=j.rozpory||[];
      window._fixQueueN=an.length+rz.length;
      if(!an.length&&!rz.length){ box.appendChild(el('<div class="hint">Všechno vyřešeno. 👍 Nic nečeká.</div>')); return; }
      function card(name,day,detail,extra){
        var c=el('<div style="background:var(--bg);border:1px solid var(--bord);border-radius:10px;padding:10px;margin-bottom:8px;"></div>');
        c.appendChild(el('<div style="font-size:13.5px;font-weight:700;">'+esc(name||"?")+' · '+esc(day||"")+'</div>'));
        c.appendChild(el('<div style="font-size:13px;margin-top:2px;">'+esc(detail||"")+(extra||"")+'</div>'));
        var ar=el('<div style="display:flex;gap:8px;margin-top:8px;flex-wrap:wrap;"></div>');
        c.appendChild(ar); c._ar=ar;
        var fx=el('<div style="margin-top:4px;"></div>'); c.appendChild(fx); c._fx=fx;
        return c;
      }
      if(rz.length) box.appendChild(el('<div class="hint" style="margin:2px 0 6px;font-weight:600;">✋ Rozporované dny</div>'));
      rz.forEach(function(r){
        var c=card(r.name,r.day,"„"+(r.note||"")+"“");
        if(r.opraveno){_fixMarkDone(c);var bh=el('<button class="green sm">✓ Hotovo — z fronty</button>');bh.addEventListener("click",function(){_fixQuickDone(c,{uid:r.user_id,day:r.day});});c._ar.appendChild(bh);}
        var bo=el('<button class="ghost sm" style="border-color:var(--green);color:var(--green);">🛠 Otevřít den</button>');
        bo.addEventListener("click",function(){ _fixOpenDay(r.user_id,r.name,r.day); });
        var bv=el('<button class="ghost sm" style="border-color:var(--green);color:var(--green);">✓ Vyřídit bez opravy</button>');
        bv.addEventListener("click",function(){
          c._fx.innerHTML=""; var rb=_fixReasonBox(); c._fx.appendChild(rb);
          var ok=el('<button class="green sm full" style="margin-top:6px;">Označit jako vyřízené</button>'); c._fx.appendChild(ok);
          ok.addEventListener("click",function(){
            api("POST","/api/v1/erp/app/attendance/fix/resolve",{uid:r.user_id,day:r.day,reason:(rb._input.value||"").trim()}).then(function(x){
              if(x&&x.ok){ c.remove(); } else { c._fx.innerHTML='<div class="hint">✗ '+esc((x&&x.error)||"Nepodařilo se.")+'</div>'; }
            });
          });
        });
        c._ar.appendChild(bo); c._ar.appendChild(bv);
        box.appendChild(c);
      });
      if(an.length) box.appendChild(el('<div class="hint" style="margin:8px 0 6px;font-weight:600;">⚠ Nesrovnalosti (automatická kontrola)</div>'));
      an.forEach(function(a){
        var extra=(a.rule==="zapomenuty_odchod"&&a.navrh_konec)?('<div class="hint" style="margin-top:2px;">💡 Poslední aktivita na zakázce: '+esc(a.navrh_konec)+'</div>'):"";
        var c=card(a.name,a.day,a.detail,extra);
        if(a.opraveno){_fixMarkDone(c);var bh=el('<button class="green sm">✓ Hotovo — z fronty</button>');bh.addEventListener("click",function(){_fixQuickDone(c,{anomaly_id:a.id});});c._ar.appendChild(bh);}
        var bo=el('<button class="ghost sm" style="border-color:var(--green);color:var(--green);">🛠 Otevřít den</button>');
        bo.addEventListener("click",function(){ _fixOpenDay(a.user_id,a.name,a.day); });
        var bv=el('<button class="ghost sm" style="border-color:var(--green);color:var(--green);">✓ V pořádku — vyřídit</button>');
        bv.addEventListener("click",function(){
          c._fx.innerHTML=""; var rb=_fixReasonBox(); c._fx.appendChild(rb);
          var ok=el('<button class="green sm full" style="margin-top:6px;">Označit jako v pořádku</button>'); c._fx.appendChild(ok);
          ok.addEventListener("click",function(){
            api("POST","/api/v1/erp/app/attendance/fix/resolve",{anomaly_id:a.id,reason:(rb._input.value||"").trim()}).then(function(x){
              if(x&&x.ok){ c.remove(); } else { c._fx.innerHTML='<div class="hint">✗ '+esc((x&&x.error)||"Nepodařilo se.")+'</div>'; }
            });
          });
        });
        c._ar.appendChild(bo); c._ar.appendChild(bv);
        box.appendChild(c);
      });
    });
  }
  function _fixPeopleLoad(box){
    box.innerHTML='<div class="hint">Načítám lidi…</div>';
    // Jirka 10.7. (rozhodl Marti): seznam JEN v působnosti editora (kancelář/výroba/vše).
    api("GET","/api/v1/erp/app/attendance/fix/lide","").then(function(j){
      box.innerHTML="";
      var lide=(j&&j.lide)||[];
      // Jirka 10.7.: pořadí volby je volné — den→člověk i člověk→den (den jde
      // přepnout i potom v detailu šipkami).
      box.appendChild(el('<div class="hint" style="margin-bottom:4px;">📅 Který den zobrazit (jde změnit i potom v detailu):</div>'));
      var dr=_fixDateRow(_locDate(0), null);
      var dt=dr.input;
      box.appendChild(dr.row);
      box.appendChild(el('<div class="hint" style="margin:10px 0 4px;">👤 Čí docházku otevřít:</div>'));
      var si=el('<input placeholder="🔍 hledat jméno…" autocomplete="off" style="width:100%;">');
      var res=el('<div style="margin-top:8px;"></div>');
      box.appendChild(si); box.appendChild(res);
      function rend(){
        var q=(si.value||"").trim().toLowerCase();
        res.innerHTML="";
        // Jirka 10.7.: BEZ oříznutí — musí být vidět všichni (67 lidí; slice(0,40) utínal M–Z).
        lide.filter(function(l){ return !q || (l.jmeno||"").toLowerCase().indexOf(q)>=0; }).forEach(function(l){
          var b=el('<button class="ghost full" style="margin-top:6px;text-align:left;">👤 '+esc(l.jmeno||"?")+'</button>');
          b.addEventListener("click",function(){ _fixOpenDay(l.user_id,l.jmeno,dt.value||_locDate(0)); });
          res.appendChild(b);
        });
        if(!res.childNodes.length) res.innerHTML='<div class="hint">Nikdo nenalezen.</div>';
      }
      si.addEventListener("input",rend); rend();
    });
  }
  function _fixAuditLoad(box){
    box.innerHTML='<div class="hint">Načítám historii…</div>';
    api("GET","/api/v1/erp/app/attendance/fix/audit","").then(function(j){
      box.innerHTML="";
      var it=(j&&j.items)||[];
      if(!it.length){ box.innerHTML='<div class="hint">Zatím žádné opravy.</div>'; return; }
      var ICO={fix:"✏️",add:"➕",void:"🗑",merge:"🔗",resolve:"✓",period_lock:"🔒",period_unlock:"🔓"};
      it.forEach(function(r){
        var c=el('<div style="border-bottom:1px solid var(--bord);padding:8px 2px;font-size:13px;"></div>');
        c.appendChild(el('<div><b>'+(ICO[r.action]||"·")+' '+esc(r.person||"")+'</b>'+(r.day?(' · '+esc(r.day)):'')+' <span class="hint">('+esc(r.actor||"?")+', '+esc(r.ts||"")+')</span></div>'));
        var d=[]; if(r.old)d.push("před: "+r.old); if(r.new)d.push("po: "+r.new); if(r.detail)d.push(r.detail);
        if(d.length) c.appendChild(el('<div class="hint" style="margin-top:2px;">'+esc(d.join(" · "))+'</div>'));
        box.appendChild(c);
      });
    });
  }
  // Jirka 10.7.: den se volí POHODLNĚ a v libovolném pořadí (den→člověk i
  // člověk→den) — šipky ◀/▶ + kalendář + název dne v týdnu.
  var _FIX_DNY=["neděle","pondělí","úterý","středa","čtvrtek","pátek","sobota"];
  function _fixDayLabel(v){
    try{ var d=new Date(v+"T12:00:00"); return _FIX_DNY[d.getDay()]+" "+d.getDate()+"."+(d.getMonth()+1)+"."; }
    catch(e){ return ""; }
  }
  function _fixDateRow(initial, onChange){
    var row=el('<div style="display:flex;gap:8px;align-items:flex-start;"></div>');
    var bp=el('<button class="ghost sm" style="width:46px;flex:none;font-size:16px;margin:0;">◀</button>');
    var mid=el('<div style="flex:1;min-width:0;"></div>');
    var inp=el('<input type="date" value="'+esc(initial)+'" style="width:100%;">');
    var lab=el('<div class="hint" style="text-align:center;margin-top:2px;">'+esc(_fixDayLabel(initial))+'</div>');
    mid.appendChild(inp); mid.appendChild(lab);
    var bn=el('<button class="ghost sm" style="width:46px;flex:none;font-size:16px;margin:0;">▶</button>');
    row.appendChild(bp); row.appendChild(mid); row.appendChild(bn);
    function pad2(n){ return (n<10?"0":"")+n; }
    function shift(days){
      try{ var d=new Date((inp.value||_locDate(0))+"T12:00:00"); d.setDate(d.getDate()+days);
           inp.value=d.getFullYear()+"-"+pad2(d.getMonth()+1)+"-"+pad2(d.getDate()); }catch(e){ return; }
      fire();
    }
    function fire(){ lab.textContent=_fixDayLabel(inp.value); if(onChange) onChange(inp.value); }
    bp.addEventListener("click",function(){ shift(-1); });
    bn.addEventListener("click",function(){ shift(1); });
    inp.addEventListener("change",fire);
    return {row: row, input: inp};
  }
  function doch_opravy_den(){
    var ctx=window._fixCtx||{};
    app.innerHTML=topbar("🛠 "+(ctx.name||"Oprava dne"), true); _dochTopPad();
    var p=el('<div class="panel"></div>'); app.appendChild(p);
    var dr=_fixDateRow(ctx.day||_locDate(0), function(v){ ctx.day=v; load(); });
    var dt=dr.input;
    p.appendChild(dr.row);
    var box=el('<div style="margin-top:8px;"></div>'); p.appendChild(box);
    p.appendChild(el('<div style="height:120px;"></div>'));  // rezerva pod spodní lištu (Jirka 10.7.)
    function load(){
      box.innerHTML='<div class="hint">Načítám den…</div>';
      api("GET","/api/v1/erp/app/attendance/fix/day?uid="+ctx.uid+"&day="+encodeURIComponent(dt.value||""),"").then(function(j){
        box.innerHTML="";
        if(!(j&&j.ok)){ box.innerHTML='<div class="hint">✗ '+esc((j&&j.error)||"Nepodařilo se načíst.")+'</div>'; return; }
        if(j.locked) box.appendChild(el('<div style="background:rgba(245,158,11,.12);border:1px solid var(--amber);border-radius:10px;padding:10px;margin-bottom:8px;font-size:13px;">'+(j.can_unlock?'🔒 Období je uzamčeno (mzdy zpracovány) — opravy nejsou možné. Ty ho smíš odemknout: odemkni, oprav a zase zamkni.':'🔒 Období je uzamčeno (mzdy zpracovány) — opravy nejsou možné. Odemknout smí Peťa/Šárka.')+'</div>'));
        // Jirka 12.7.: co člověk hlásí (✋ rozpor dne + rozpory na záznamech) = důležité, NAD tabulkou
        var hlasi=[];
        if(j.dispute&&j.dispute.disputed&&(j.dispute.note||"").trim())hlasi.push('<b>Den:</b> „'+esc(j.dispute.note)+'“');
        (j.entries||[]).forEach(function(e0){
          if(e0.status!=="superseded"&&(e0.note||"").indexOf("✋ ROZPOR")>=0)
            hlasi.push('<b>'+esc((e0.zac||"?")+"–"+(e0.kon||"…"))+':</b> '+esc(e0.note.replace(/.*?✋ ROZPOR:\s*/,"")));
        });
        if(hlasi.length)box.appendChild(el('<div style="background:rgba(245,158,11,.10);border:1px solid var(--amber);border-radius:10px;padding:10px 12px;margin-bottom:8px;font-size:13px;"><div style="font-weight:700;margin-bottom:4px;">✋ Co člověk hlásí</div>'+hlasi.join('<br>')+'</div>'));
        // ➕ doplnění chybějícího záznamu — z tlačítka i z řádku „mezera" (Dušan 12.7., předvyplněné časy)
        var addB=el('<button class="ghost full" style="margin-bottom:8px;border-color:var(--green);color:var(--green);">➕ Přidat záznam (zapomenutý příchod, mezera…)</button>');
        var addFx=el('<div style="margin-bottom:8px;"></div>');
        if(!j.locked){ box.appendChild(addB); box.appendChild(addFx); }
        function openAdd(prefZ,prefK){
          if(j.locked)return;
          addFx.innerHTML="";
          var w=el('<div style="background:var(--bg);border:1px solid var(--bord);border-radius:10px;padding:10px;"></div>');
          var sel=_fixMkTyp(null);
          var t1=el('<input type="time" value="'+esc(prefZ||"")+'" style="width:46%;">'), t2=el('<input type="time" value="'+esc(prefK||"")+'" style="width:46%;">');
          var tr=el('<div style="display:flex;gap:8%;margin-top:6px;"></div>'); tr.appendChild(t1); tr.appendChild(t2);
          var zk=_fixMkZak(null);
          var cinW=_fixMkCin(null); _fixCinShow(cinW,sel.value); sel.addEventListener("change",function(){ _fixCinShow(cinW,sel.value); });
          var rb=_fixReasonBox();
          var ok=el('<button class="green full" style="margin-top:8px;">Uložit nový záznam</button>');
          var st=el('<div class="errbar"></div>');
          w.appendChild(sel); w.appendChild(tr); w.appendChild(zk); w.appendChild(cinW); w.appendChild(rb); w.appendChild(st); w.appendChild(ok);
          addFx.appendChild(w);
          try{ addFx.scrollIntoView({behavior:"smooth",block:"center"}); }catch(e){}
          ok.addEventListener("click",function(){
            if(!t1.value||!t2.value){ st.textContent="Vyplň časy od–do."; return; }
            if(!(rb._input.value||"").trim()){ st.textContent="Důvod je povinný."; return; }
            _fixConfirm(addFx,"Přidat "+esc(sel.value)+" "+esc(t1.value)+"–"+esc(t2.value)+" pro <b>"+esc(ctx.name||"")+"</b> ("+esc(dt.value)+")?",function(cw){
              api("POST","/api/v1/erp/app/attendance/fix/add",{uid:ctx.uid,day:dt.value,type_code:sel.value,zac:t1.value,kon:t2.value,project_ref:(zk.value||"").trim()||null,cinnost_id:(cinW._sel.value?parseInt(cinW._sel.value,10):null),reason:rb._input.value.trim()}).then(function(r){
                if(r&&r.ok){ load(); } else { cw.remove(); st.textContent="✗ "+((r&&r.error)||"Nepodařilo se."); }
              });
            });
          });
        }
        addB.addEventListener("click",function(){ openAdd("",""); });
        var es=j.entries||[];
        if(!es.length){ box.appendChild(el('<div class="hint">Žádné záznamy v tomto dni.</div>')); return; }
        // Dušan 12.7.: den jako kompaktní tabulka — co záznam, to řádek; editace se rozbalí pod řádkem.
        var TH='font-size:10px;text-transform:uppercase;letter-spacing:.4px;color:var(--mut);text-align:left;padding:4px 4px;border-bottom:1px solid var(--bord);font-weight:600;';
        var TD='padding:8px 4px;border-bottom:1px solid var(--bord);vertical-align:middle;';
        var tbl=document.createElement('table'); tbl.style.cssText="width:100%;border-collapse:collapse;margin-top:2px;font-size:13px;";
        // POZOR: el() parsuje v kontextu <div>, který thead/tr/td zahazuje — tabulku stavíme přes DOM API.
        tbl.innerHTML='<thead><tr><th style="'+TH+'">Typ</th><th style="'+TH+'white-space:nowrap;">Od–Do</th><th style="'+TH+'text-align:right;">Hod</th><th style="'+TH+'text-align:right;">Akce</th></tr></thead>';
        var tb=document.createElement('tbody'); tbl.appendChild(tb);
        var poznBelow=[], maCentralu=false;
        // Peťa 21.7.: akumulace pro ∑ Součet dne (parita s ERP). Práce (přítomnost),
        // pauzy a „ostatní" (dovolená/lékař/doplnění do fondu…) zvlášť.
        var _PRES=['work','overhead','homeoffice','commute'];
        var ivPrace=[],ivPauzy=[],sumPauzyBezCasu=0,sumPauzyH=0,ostMap={},ostPor=[];
        function tdc(html,style){ var c=document.createElement('td'); if(style)c.style.cssText=style; c.innerHTML=html; return c; }
        function hmMin(x){ var p=String(x||"").split(":"); return (parseInt(p[0],10)||0)*60+(parseInt(p[1],10)||0); }
        var prevKon=null;  // konec předchozího (dřívějšího) viditelného záznamu — mezery vzestupně
        es.forEach(function(e2){
          var gone=(e2.status==="superseded");
          var isDE=(e2.code==="day_end");  // interní marker odchodu (verdikt Marti-AI 10.7., msg 10632)
          if(!gone&&!isDE&&e2.hours!=null){
            var _h=Number(e2.hours)||0, _iv=null;
            if(e2.zac&&e2.kon){ var _s=hmMin(e2.zac),_e=hmMin(e2.kon); if(_e<_s)_e+=1440; if(_e>_s)_iv={s:_s,e:_e}; }
            if(e2.code==='break'){ sumPauzyH+=_h; if(_iv)ivPauzy.push(_iv); else sumPauzyBezCasu+=_h; }
            else if(_PRES.indexOf(e2.code)>=0&&_iv)ivPrace.push(_iv);
            else{ var _lab=(e2.typ||'Ostatní'); if(ostMap[_lab]===undefined){ostMap[_lab]=0;ostPor.push(_lab);} ostMap[_lab]+=_h; }
          }
          if(!gone&&!isDE&&e2.zac&&prevKon&&(hmMin(e2.zac)-hmMin(prevKon))>=5&&!j.locked){
            var gz=prevKon, gk=e2.zac;
            var gr=document.createElement('tr');
            var g1=tdc('⋯ mezera '+esc(gz)+'–'+esc(gk)+' (bez záznamu)','border-bottom:1px dashed var(--bord);color:var(--mut);font-size:11.5px;padding:4px 6px;');
            g1.colSpan=3;
            var g2=tdc('','border-bottom:1px dashed var(--bord);text-align:right;padding:4px 6px;');
            var gb=el('<button class="ghost sm" style="padding:4px 9px;">➕</button>');
            gb.addEventListener("click",function(){ openAdd(gz,gk); });
            g2.appendChild(gb); gr.appendChild(g1); gr.appendChild(g2);
            tb.appendChild(gr);
          }
          var tr0=document.createElement('tr'); if(gone) tr0.style.opacity=".45";
          var badge="";
          if(gone) badge=' <span style="font-size:10.5px;color:var(--mut);">(storno)</span>';
          else if(e2.running&&!isDE) badge=' <span style="font-size:10.5px;color:var(--green);">● běží</span>';
          else if(e2.source_system){ badge=' <span style="font-size:10.5px;color:var(--amber);">🏛</span>'; maCentralu=true; }
          if(isDE&&!gone) badge+=' <span style="font-size:10.5px;color:var(--mut);">(uzávěrka dne)</span>';
          if(e2.source==="manual_fix") badge+=' <span style="font-size:10.5px;color:#7c8cdb;">🛠</span>';
          if(!gone&&e2.note&&e2.note.indexOf("✋ ROZPOR")<0) poznBelow.push('<b>'+esc((e2.zac||"?")+(isDE?'':("–"+(e2.kon||"…"))))+' '+(isDE?'🫡 Odchod':esc(e2.typ||""))+':</b> '+esc(e2.note));
          var tdT=tdc('',TD);
          tdT.appendChild(el('<div style="font-weight:600;">'+(isDE?'🫡 Odchod':esc(e2.typ||""))+badge+'</div>'));
          if(!isDE&&e2.project_ref) tdT.appendChild(el('<div style="font-size:11px;color:var(--mut);margin-top:1px;">🧾 '+esc(e2.project_ref)+'</div>'));
          if(!isDE&&e2.cin_name) tdT.appendChild(el('<div style="font-size:11px;color:var(--mut);margin-top:1px;">🔧 '+esc(e2.cin_name)+'</div>'));
          tr0.appendChild(tdT);
          tr0.appendChild(tdc(e2.zac?(esc(e2.zac)+(isDE?'':("–"+esc(e2.kon||"…")))):"—",TD+'white-space:nowrap;font-variant-numeric:tabular-nums;'));
          tr0.appendChild(tdc((!isDE&&e2.hours!=null)?fmtDec(e2.hours):"",TD+'text-align:right;font-variant-numeric:tabular-nums;'));
          var tdA=tdc('',TD+'text-align:right;white-space:nowrap;'); tr0.appendChild(tdA);
          tb.appendChild(tr0);
          if(!gone&&!isDE&&e2.kon) prevKon=e2.kon;
          if(!(e2.editable&&!e2.running&&e2.zac)){
            // proč tu nejsou tlačítka — ať je jasné, že to není chyba
            var duvod=gone?"storno":(e2.running&&!isDE)?"● běží":(e2.source_system?"🏛 v Centrále":(j.locked?"🔒":(!e2.zac?"—":"—")));
            tdA.innerHTML='<span style="font-size:11px;color:var(--mut);">'+duvod+'</span>';
          }
          if(e2.editable&&!e2.running&&e2.zac){
            var frow=document.createElement('tr'); frow.style.display="none";
            var fcell=tdc('','background:rgba(255,255,255,.03);border-bottom:1px solid var(--bord);padding:10px 8px;');
            fcell.colSpan=4;
            frow.appendChild(fcell); tb.appendChild(frow);
            var closeForm=function(){ frow.style.display="none"; tr0.style.background=""; fcell.innerHTML=""; };
            var openForm=function(titul){
              frow.style.display=""; tr0.style.background="rgba(79,142,247,.08)"; fcell.innerHTML="";
              var hd=el('<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;"><b style="font-size:12.5px;">'+titul+' — '+(isDE?'🫡 Odchod '+esc(e2.zac||"?"):esc((e2.typ||"")+" "+(e2.zac||"?")+"–"+(e2.kon||"…")))+'</b></div>');
              var bx=el('<button class="ghost sm" style="padding:2px 9px;">✕</button>');
              bx.addEventListener("click",closeForm); hd.appendChild(bx); fcell.appendChild(hd);
              var fx=el('<div></div>'); fcell.appendChild(fx); return fx;
            };
            var be=el('<button class="ghost sm" style="border-color:var(--green);color:var(--green);padding:7px 11px;">✏️</button>');
            var bs=el('<button class="ghost sm" style="border-color:var(--amber);color:var(--amber);padding:7px 11px;margin-left:6px;">🗑</button>');
            if(!isDE) tdA.appendChild(be);  // interní marker se needituje, jen stornuje
            tdA.appendChild(bs);
            be.addEventListener("click",function(){
              var fx=openForm("✏️ Oprava záznamu");
              var t1=el('<input type="time" value="'+esc(e2.zac||"")+'" style="width:46%;">');
              var t2=el('<input type="time" value="'+esc(e2.kon||"")+'" style="width:46%;">');
              var tr=el('<div style="display:flex;gap:8%;"></div>'); tr.appendChild(t1); tr.appendChild(t2);
              var sel=_fixMkTyp(e2.code);
              var zk=_fixMkZak(e2.project_ref||null);
              var cinW=_fixMkCin(e2.cin_id||null); _fixCinShow(cinW,sel.value); sel.addEventListener("change",function(){ _fixCinShow(cinW,sel.value); });
              var rb=_fixReasonBox();
              var ok=el('<button class="green full" style="margin-top:8px;">Uložit opravu</button>');
              var st=el('<div class="errbar"></div>');
              fx.appendChild(tr); fx.appendChild(sel); fx.appendChild(zk); fx.appendChild(cinW); fx.appendChild(rb); fx.appendChild(st); fx.appendChild(ok);
              ok.addEventListener("click",function(){
                if(!t1.value||!t2.value){ st.textContent="Vyplň oba časy."; return; }
                if(!(rb._input.value||"").trim()){ st.textContent="Důvod je povinný."; return; }
                _fixConfirm(fx,"Opravit záznam z <b>"+esc((e2.zac||"?")+"–"+(e2.kon||"…"))+"</b> na <b>"+esc(t1.value+"–"+t2.value)+((zk.value||"").trim()!==(e2.project_ref||"")?(" · 🧾 "+esc((zk.value||"").trim()||"bez zakázky")):"")+"</b>?",function(cw){
                  api("POST","/api/v1/erp/app/attendance/fix/entry",{id:e2.id,zac:t1.value,kon:t2.value,type_code:sel.value,project_ref:(zk.value||"").trim(),cinnost_id:(cinW._sel.value?parseInt(cinW._sel.value,10):null),reason:rb._input.value.trim()}).then(function(r){
                    if(r&&r.ok){ load(); } else { cw.remove(); st.textContent="✗ "+((r&&r.error)||"Nepodařilo se."); }
                  });
                });
              });
            });
            bs.addEventListener("click",function(){
              var fx=openForm("🗑 Storno záznamu");
              var rb=_fixReasonBox(); fx.appendChild(rb);
              var ok=el('<button class="ghost full" style="margin-top:6px;border-color:var(--amber);color:var(--amber);">Stornovat záznam</button>');
              var st=el('<div class="hint" style="margin-top:4px;"></div>');
              fx.appendChild(ok); fx.appendChild(st);
              ok.addEventListener("click",function(){
                if(!(rb._input.value||"").trim()){ st.textContent="Důvod je povinný."; return; }
                _fixConfirm(fx,"Opravdu stornovat záznam <b>"+esc((e2.zac||"?")+"–"+(e2.kon||"…"))+"</b>?",function(cw){
                  api("POST","/api/v1/erp/app/attendance/fix/void",{id:e2.id,reason:rb._input.value.trim()}).then(function(r){
                    if(!(r&&r.ok)){ cw.remove(); st.textContent="✗ "+((r&&r.error)||"Nepodařilo se."); return; }
                    // Jirka 10.7.: storno přerušení → když okolní záznamy navazují
                    // (stejný typ i zakázka), nabídni sešití do jednoho záznamu.
                    if(r.merge_offer&&r.merge_offer.a_id){
                      var mo=r.merge_offer;
                      cw.remove(); fx.innerHTML="";
                      var mw=el('<div class="trimconf" style="margin-top:6px;background:rgba(79,142,247,.10);border:1px solid var(--blue);border-radius:8px;padding:10px;"></div>');
                      mw.appendChild(el('<div style="font-size:14px;">Stornováno ✅ Okolní záznamy na sebe navazují (stejný typ i zakázka):<br><b>'+esc(mo.popis)+'</b><br>Sloučit do jednoho záznamu?</div>'));
                      var mbr=el('<div style="display:flex;gap:8px;margin-top:8px;"></div>');
                      var many=el('<button class="green sm" style="flex:1;">🔗 Sloučit</button>');
                      var mne=el('<button class="ghost sm">Nechat rozdělené</button>');
                      mbr.appendChild(many); mbr.appendChild(mne); mw.appendChild(mbr); fx.appendChild(mw);
                      mne.addEventListener("click",function(){ load(); });
                      many.addEventListener("click",function(){
                        many.disabled=true; mne.disabled=true;
                        api("POST","/api/v1/erp/app/attendance/fix/merge",{a_id:mo.a_id,b_id:mo.b_id,reason:"sloučení po stornu přerušení"}).then(function(m){
                          if(m&&m.ok){ load(); } else { mw.innerHTML='<div class="hint">✗ '+esc((m&&m.error)||"Sloučení se nepovedlo.")+'</div>'; setTimeout(load,1800); }
                        });
                      });
                      return;
                    }
                    load();
                  });
                });
              });
            });
          }
        });
        // Peťa 21.7.: Celkem přímo v tabulce ve sloupci Hod pod posledním řádkem (parita s ERP).
        (function(){
          var _mg0=ivPrace.slice().sort(function(a,b){return a.s-b.s;}),_m0=[];
          _mg0.forEach(function(v){var l=_m0[_m0.length-1];if(l&&v.s<=l.e){if(v.e>l.e)l.e=v.e;}else _m0.push({s:v.s,e:v.e});});
          var min0=0;_m0.forEach(function(v){min0+=v.e-v.s;});
          var vev0=0;ivPauzy.forEach(function(p){_m0.forEach(function(v){var o=Math.min(p.e,v.e)-Math.max(p.s,v.s);if(o>0)vev0+=o;});});
          var celk=min0/60-(vev0/60+sumPauzyBezCasu);
          ostPor.forEach(function(lab){celk+=ostMap[lab];});
          if(ivPrace.length||ostPor.length){
            var ctr=document.createElement('tr');
            ctr.appendChild(tdc('<b>Celkem</b>',TD));
            ctr.appendChild(tdc('<span style="font-size:11px;color:var(--mut);">bez přestávek</span>',TD+'white-space:nowrap;'));
            ctr.appendChild(tdc('<b>'+fmtDec(celk)+'</b>',TD+'text-align:right;font-variant-numeric:tabular-nums;'));
            ctr.appendChild(tdc('',TD));
            tb.appendChild(ctr);
          }
        })();
        box.appendChild(tbl);
        // Peťa 21.7.: ∑ SOUČET DNE pod tabulkou (parita s ERP) — jak se den skládá, ať jde
        // zkontrolovat, jestli doplnění do fondu sedí (odhalilo chybu s pauzami 21.7.).
        if(ivPrace.length||sumPauzyH||ostPor.length){
          var _mg=ivPrace.slice().sort(function(a,b){return a.s-b.s;}),_m=[];
          _mg.forEach(function(v){var last=_m[_m.length-1];if(last&&v.s<=last.e){if(v.e>last.e)last.e=v.e;}else _m.push({s:v.s,e:v.e});});
          var minPrace=0;_m.forEach(function(v){minPrace+=v.e-v.s;});
          var minPauzVev=0;
          ivPauzy.forEach(function(p){var uvnitr=0;_m.forEach(function(v){var o=Math.min(p.e,v.e)-Math.max(p.s,v.s);if(o>0)uvnitr+=o;});minPauzVev+=uvnitr;});
          var pauzOdecist=minPauzVev/60+sumPauzyBezCasu;
          var cisty=minPrace/60-pauzOdecist;
          var sb=el('<div style="margin-top:12px;"></div>');
          sb.appendChild(el('<div style="font-size:11px;font-weight:700;letter-spacing:.4px;color:var(--mut);text-transform:uppercase;">∑ Součet dne</div>'));
          var stb=document.createElement('table'); stb.style.cssText='width:100%;max-width:360px;border-collapse:collapse;margin-top:6px;font-size:13px;';
          var stbody=document.createElement('tbody'); stb.appendChild(stbody);
          function srow(label,val,bold){
            var r=document.createElement('tr');
            var c1=document.createElement('td'); c1.style.cssText='padding:5px 4px;border-bottom:1px solid var(--bord);'; c1.innerHTML=bold?('<b>'+label+'</b>'):label;
            var c2=document.createElement('td'); c2.style.cssText='padding:5px 4px;border-bottom:1px solid var(--bord);text-align:right;font-variant-numeric:tabular-nums;'; c2.innerHTML=bold?('<b>'+val+'</b>'):val;
            r.appendChild(c1); r.appendChild(c2); stbody.appendChild(r);
          }
          srow('Odpracováno (bez přestávek)',fmtDec(cisty),true);
          var celkem=cisty;
          ostPor.forEach(function(lab){celkem+=ostMap[lab];srow(esc(lab),fmtDec(ostMap[lab]));});
          srow('Celkem',fmtDec(celkem),true);
          if(sumPauzyH){
            srow('<span style="color:var(--mut);">Přestávky (mimo součet)</span>','<span style="color:var(--mut);">'+fmtDec(sumPauzyH)+'</span>');
            if(pauzOdecist)srow('<span style="color:var(--mut);">… z toho odečteno od práce</span>','<span style="color:var(--mut);">−'+fmtDec(pauzOdecist)+'</span>');
          }
          sb.appendChild(stb);
          sb.appendChild(el('<div class="hint" style="margin-top:4px;">Hodiny v desetinné soustavě (5,90 = 5 h 54 min). Stornované řádky se nepočítají. Přestávka se odečítá od práce jen když leží uvnitř pracovního záznamu.</div>'));
          box.appendChild(sb);
        }
        // Jirka 12.7.: systémové poznámky (stopy oprav, automaty…) POD tabulkou, ať je nahoře čistá
        if(maCentralu) box.appendChild(el('<div class="hint" style="margin-top:8px;">🏛 Záznamy z tabletu staré Centrály se opravují v Centrále (Dušan) — sem se přezrcadlí.</div>'));
        if(poznBelow.length){
          var pb=el('<div style="margin-top:10px;"></div>');
          pb.appendChild(el('<div style="font-size:11px;font-weight:700;letter-spacing:.4px;color:var(--mut);text-transform:uppercase;">🗒 Poznámky k záznamům</div>'));
          poznBelow.forEach(function(x){ pb.appendChild(el('<div class="hint" style="margin-top:3px;">'+x+'</div>')); });
          box.appendChild(pb);
        }
      });
    }
    load();
  }
  // ───── PŘIHLÁSIT JAKO (impersonace pro test docházky, Marti 7.6.) ─────

/* Claude-24 16.7.: styl pro searchable roletky (combobox) v mobilu */
(function(){try{if(document.getElementById('scbCss24'))return;var st=document.createElement('style');st.id='scbCss24';st.textContent='.scb-list{margin-top:4px;max-height:230px;overflow-y:auto;background:#0f1620;border:1px solid var(--bord);border-radius:8px;}.scb-it{padding:10px 12px;cursor:pointer;border-bottom:1px solid rgba(255,255,255,.06);font-size:14px;}.scb-it:last-child{border-bottom:0;}.scb-it.hl,.scb-it:active{background:rgba(79,142,247,.20);}.scb-it.none{color:var(--mut);}.errbar{margin:8px 0 2px;background:rgba(224,138,138,.16);border:1px solid var(--red);color:#f3c0c0;border-radius:8px;padding:10px 12px;font-size:14.5px;font-weight:600;line-height:1.35;}.errbar:empty{display:none;}';document.head.appendChild(st);}catch(e){}})();
