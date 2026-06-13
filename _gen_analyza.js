const fs = require('fs');
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType, LevelFormat,
  TableOfContents, PageBreak, PageNumber, Header, Footer } = require('docx');

const BL = "1F3A5F", ACC = "2E75B6", HDR = "D5E8F0", ZEBRA = "F2F6FA";
const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: border, bottom: border, left: border, right: border };

function P(text, opts={}) { return new Paragraph({ children:[new TextRun({ text, ...opts })], spacing:{after:120}, ...(opts.p||{}) }); }
function H1(t){ return new Paragraph({ heading:HeadingLevel.HEADING_1, children:[new TextRun(t)] }); }
function H2(t){ return new Paragraph({ heading:HeadingLevel.HEADING_2, children:[new TextRun(t)] }); }
function bullet(t){ return new Paragraph({ numbering:{reference:"b",level:0}, children:[new TextRun(t)], spacing:{after:60} }); }
function bsub(t){ return new Paragraph({ numbering:{reference:"b",level:1}, children:[new TextRun(t)], spacing:{after:40} }); }

function table(head, rows, widths){
  const tot = widths.reduce((a,b)=>a+b,0);
  const mk = (txt, w, isH, i)=> new TableCell({ borders, width:{size:w,type:WidthType.DXA},
    shading:{fill: isH?HDR:(i%2?ZEBRA:"FFFFFF"), type:ShadingType.CLEAR},
    margins:{top:60,bottom:60,left:110,right:110},
    children:(''+txt).split('\n').map(line=> new Paragraph({children:[new TextRun({text:line,bold:!!isH,size:18,color:isH?BL:"222222"})]})) });
  const hr = new TableRow({ tableHeader:true, children: head.map((h,i)=>mk(h,widths[i],true,0)) });
  const dr = rows.map((r,ri)=> new TableRow({ children: r.map((c,i)=>mk(c,widths[i],false,ri)) }));
  return new Table({ width:{size:tot,type:WidthType.DXA}, columnWidths:widths, rows:[hr,...dr] });
}

const children = [];

// Titulka
children.push(new Paragraph({ spacing:{before:1200,after:0}, children:[new TextRun({text:"STRATEGIE", bold:true, size:56, color:BL})] }));
children.push(new Paragraph({ spacing:{after:400}, children:[new TextRun({text:"Analýza nástroje", size:28, color:ACC})] }));
children.push(new Paragraph({ spacing:{after:120}, children:[new TextRun({text:"Plánování vytížení montérů (v162.xlsm)", bold:true, size:40, color:"222222"})] }));
children.push(new Paragraph({ spacing:{after:600}, children:[new TextRun({text:"Kompletní technická analýza pro přenos do platformy STRATEGIE", size:24, color:"555555", italics:true})] }));
children.push(new Paragraph({ children:[new TextRun({text:"Zpracoval: Claude (id=23)  ·  8. 6. 2026  ·  EUROSOFT-System / STRATEGIE", size:20, color:"777777"})] }));
children.push(new Paragraph({ children:[new TextRun({text:"Zdroj: Plánování vytížení v162.xlsm (1,8 MB, .xlsm s VBA)", size:20, color:"777777"})] }));
children.push(new Paragraph({ children:[new PageBreak()] }));

// TOC
children.push(new Paragraph({ children:[new TextRun({text:"Obsah", bold:true, size:32, color:BL})], spacing:{after:200} }));
children.push(new TableOfContents("Obsah", { hyperlink:true, headingStyleRange:"1-2" }));
children.push(new Paragraph({ children:[new PageBreak()] }));

// 1. Shrnutí
children.push(H1("1. Manažerské shrnutí"));
children.push(P("Soubor „Plánování vytížení v162.xlsm\" je rozsáhlý provozní nástroj pro plánování práce montérů, řízení vytížení dílny, odvozů a nepřítomností. Není to běžná tabulka — je to plnohodnotná klientská aplikace postavená nad Excelem, s vlastním ribbonem (panelem tlačítek), cca 65 moduly kódu VBA (~14 000 řádků) a živým napojením na databázi Centrály 1 (MSSQL)."));
children.push(P("Excel zde funguje jen jako zobrazovací a ovládací vrstva. Veškerá data se čtou z databázových pohledů (views) a každá změna (přidání montéra na zakázku, nastavení odvozu, poznámka) se zapisuje voláním uložené procedury. Listy v sešitu jsou jen lokální vyrovnávací paměť (cache) — proto je většina z nich skrytá.", {}));
children.push(P("Pro STRATEGIE to znamená velmi dobrou zprávu: databázová logika (pohledy + procedury) je už hotová a oddělená od Excelu. Migrace = nahradit excelovou UI/VBA vrstvu webovým modulem STRATEGIE, který volá tytéž views a procedury. Datová vrstva se nemusí psát znovu.", { bold:false }));

children.push(H2("Klíčová čísla"));
children.push(table(
  ["Ukazatel","Hodnota"],
  [
   ["Listů v sešitu","15 datových + 2 grafové (3 viditelné, ostatní skryté/cache)"],
   ["Modulů VBA","65 modulů, ~14 000 řádků kódu"],
   ["Procedur / funkcí VBA","787"],
   ["Tlačítek na ribbonu (akcí)","30 (APS_*)"],
   ["DB pohledy pro čtení (ECv_)","20+ views"],
   ["DB procedury pro zápis (EC_)","31 procedur"],
   ["Databáze","MSSQL — Centrála 1 (DB_EC), přes SQLOLEDB"],
  ],
  [3400, 5960]
));

// 2. Architektura
children.push(H1("2. Architektura"));
children.push(P("Nástroj je třívrstvý, i když to na první pohled vypadá jako jeden soubor:"));
children.push(bullet("Prezentační vrstva — listy Excelu (Zakázky_Plán, Vytížení montérů, Přehled odvozů) + ribbon s tlačítky. Tady uživatel vidí plán a klikáním ho mění."));
children.push(bullet("Logická vrstva — VBA kód (65 modulů). Řídí načtení/uložení dat, přepočty vytížení a kapacit, barvení buněk, kalendář, dialogy (formuláře) pro přidání montéra, poznámky, události."));
children.push(bullet("Datová vrstva — MSSQL databáze Centrály 1. Čtení přes pohledy ECv_Vytizeni_*, zápis přes procedury EC_Vytizeni_*."));
children.push(P("Připojení k databázi: Provider=SQLOLEDB; Network Library=DBMSSOCN (TCP/IP); Data Source a Initial Catalog se skládají dynamicky z nastavení. Jde tedy o stejnou databázi, na kterou už STRATEGIE čte přes EUROSOFT-MCP.", {italics:false}));

children.push(H2("Důležité: oddělení čtení a zápisu"));
children.push(P("Pohledy ECv_ jsou pouze ke čtení (read-only views). Žádný zápis přes ně neprobíhá. Veškeré změny dat jdou výhradně přes uložené procedury EC_Vytizeni_* (bez „v\"). Tohle je čistý, bezpečný vzor a pro STRATEGIE ideální — modul bude číst z views a zapisovat voláním procedur, přesně jak to dnes dělá Excel.", { bold:false }));

// 3. Listy
children.push(H1("3. Přehled listů sešitu"));
children.push(P("Většina listů je skrytá — slouží jako lokální cache dat stažených z databáze. Viditelné jsou jen tři pracovní plochy a nápověda."));
children.push(table(
  ["List","Stav","Rozměr","Účel"],
  [
   ["Zakázky_Plán","viditelný","219×240","Hlavní plánovací plocha — zakázky × časová osa, hodiny, barvy, odvozy"],
   ["Vytížení montérů","viditelný","237×263","Matice montér × dny — vytížení, počítané přepočtem"],
   ["Přehled odvozů","viditelný","1526×6","Odvozy po kalendářních týdnech (KW)"],
   ["HELP","viditelný","100×16","Nápověda, legenda barev, typy odvozů a nepřítomností"],
   ["Plán montéři","skrytý","1135×10","Cache: přiřazení montér → zakázka → den → hodiny"],
   ["Nepřítomnost","skrytý","4042×13","Cache: dovolené, nemoci (datum, zaměstnanec, hodiny)"],
   ["Výpomoc","skrytý","1996×9","Cache: výpomoc mezi pracovišti"],
   ["Události","skrytý","864×17","Cache: odvozy/události (čas, dopravce, místo určení)"],
   ["Plán vyhled","skrytý","10724×4","Cache: výhledové plánování"],
   ["Poznamky","skrytý","5314×12","Cache: poznámky k termínům a zakázkám"],
   ["Počty / Ost / Akce / List1","skrytý","—","Pomocné: agregace, parametry, číselníky"],
  ],
  [1900, 1050, 1050, 5360]
));

// 4. Datovy model
children.push(H1("4. Datový model (databáze)"));
children.push(H2("4.1 Pohledy pro čtení (ECv_Vytizeni_*) — read-only"));
children.push(table(
  ["Pohled (view)","Co vrací"],
  [
   ["ECv_Vytizeni_Zakazky","Zakázky k plánování (číslo, kód, název, zákazník, hodiny ZL/zapsané/reálné, termíny)"],
   ["ECv_Vytizeni_PlanMonteri","Přiřazení montérů na zakázky (montér, datum, hodiny)"],
   ["ECv_Vytizeni_SeznamNepritomnost / SeznamLidiNepritomnost","Nepřítomnosti (dovolená, nemoc) po zaměstnancích"],
   ["ECv_Vytizeni_Vypomoc","Výpomoc mezi pracovišti"],
   ["ECv_Vytizení_Odvozy / ECv_Vytizeni_Udalosti","Odvozy a události (čas, dopravce, místo, objednávka)"],
   ["ECv_Vytizeni_Poznamka","Poznámky k termínům a zakázkám"],
   ["ECv_Vytizeni_kapacitaDilny","Kapacita dílny (dostupné hodiny)"],
   ["ECv_Vytizeni_PlanSuma / PlanVyhled","Souhrny plánu a výhled"],
   ["ECv_Vytizeni_Efektivita / Statistika*","Statistiky, efektivita, skryté hodiny"],
   ["ECv_Vytizeni_Nastaveni / InfoDatum / TypyUdalosti / DynamickeAkce","Parametry, číselníky, dynamické akce"],
  ],
  [4100, 5260]
));
children.push(H2("4.2 Procedury pro zápis (EC_Vytizeni_*) — 31 procedur"));
children.push(P("Každá uživatelská akce v Excelu volá jednu z těchto procedur. Pro STRATEGIE jsou to hotové „API\" zápisu:"));
children.push(table(
  ["Procedura","Akce"],
  [
   ["EC_Vytizeni_PridejMontera / VlozPlanMonter","Přidat montéra na zakázku/den"],
   ["EC_Vytizeni_PlanMonteri","Uložit plán montérů"],
   ["EC_Vytizeni_NastavOdvoz / NastavPredodvoz / NastavPredodvozKKO / NastavKKO","Nastavit typy odvozů"],
   ["EC_Vytizeni_NastavPrejimku / NastavZkousky / NastavSklad / NastavDoposilaniMaterialu","Stavy zakázky (přejímka, zkoušky, sklad…)"],
   ["EC_Vytizeni_NastavSefmontera / NastavParametryZakazky / NastavPraniZakaznika","Parametry zakázky, šéfmontér, přání zákazníka"],
   ["EC_Vytizeni_PridejUdalost / NastavUdalost / SmazUdalost / ZmenaOdvozu","Události a odvozy"],
   ["EC_Vytizeni_VlozPoznamkuPlan / VlozPoznamkuZakazka / VlozPoznamkuPlanMonter","Poznámky"],
   ["EC_Vytizeni_VlozPlanSuma / VlozHlavickuStatistiky / VlozPolozkuStatistiky","Souhrny a statistiky"],
   ["EC_Vytizeni_SmazPlanZakazky / SmazPlanVyhled / SkryjZakazku / ProvedAkci","Mazání, skrytí, dynamické akce"],
   ["EC_Vytizeni_AktualizujData_NEW / GenerujMonteryMimoObdobi","Hromadná aktualizace a generování"],
  ],
  [4500, 4860]
));

// 5. Funkce
children.push(H1("5. Funkce nástroje (ribbon)"));
children.push(P("Panel tlačítek (ribbon) nabízí 30 akcí. Tvoří funkční specifikaci budoucího modulu STRATEGIE:"));
children.push(H2("Plánování"));
children.push(bullet("Aktualizovat — znovu načte data z databáze (sdílený režim, více uživatelů najednou)."));
children.push(bullet("Uložit plán / Uložit výhledy — zapíše provedené změny do databáze."));
children.push(bullet("Přidat montéra / Smazat montéra / Do plánu — obsazení zakázky lidmi."));
children.push(bullet("Výpočet vytížení — přepočítá matici vytížení montérů a kapacitu dílny."));
children.push(bullet("Zobrazit plán na den / Jdi na dnešek / Jdi na začátek — navigace v časové ose."));
children.push(H2("Odvozy a stavy zakázky"));
children.push(bullet("Nastavit odvoz / Předodvoz / Odvoz KKO / Předodvoz KKO / Zrušit odvoz."));
children.push(bullet("Přejímka / Zkoušky / Sklad / Doposílání materiálu / Přání zákazníka — stavy zakázky."));
children.push(bullet("Generuj přehled odvozů — sestava odvozů po týdnech."));
children.push(H2("Ostatní"));
children.push(bullet("Vložit poznámku (k plánu i k zakázce), Akce (dynamické akce), Počty dle zákazníka, Skryj zakázku, Archive, Zpět na zakázku."));

// 6. VBA
children.push(H1("6. Kód VBA (logická vrstva)"));
children.push(P("65 modulů, nejdůležitější:"));
children.push(table(
  ["Modul","Řádků","Co řeší"],
  [
   ["basRozplanovani","1171","Hlavní rozplánovací logika"],
   ["frmAktualizace","1077","Dialog a průběh aktualizace dat"],
   ["bas_Zak","878","Práce se zakázkami"],
   ["basOdvozy / basPrehledOdvozu","901","Odvozy a jejich přehled"],
   ["basRibbon","571","Panel tlačítek (akce)"],
   ["basDb / clsDb","373","Připojení k databázi, čtení/zápis"],
   ["basVytizeniMonteru / basVytizeni / basKapacity","435","Přepočet vytížení a kapacit"],
   ["basNepritomnost / basVypomoc","348","Nepřítomnosti a výpomoc"],
   ["bazPoznamky / basPoznamkykTerminum","249","Poznámky"],
   ["basUdalosti / basAkce","743","Události a dynamické akce"],
  ],
  [3300, 1060, 5000]
));
children.push(P("Pozn.: Tato logika (přepočty kapacit, barvení, kalendář) je jediná část, kterou bude potřeba při migraci přepsat do STRATEGIE — datová vrstva (views + procedury) zůstává.", {italics:true}));

// 7. Doporuceni
children.push(H1("7. Doporučení pro přenos do STRATEGIE"));
children.push(P("Migrace je výhodná a nízkoriziková, protože databázová vrstva je hotová a oddělená."));
children.push(H2("Navržený postup"));
children.push(new Paragraph({ numbering:{reference:"n",level:0}, children:[new TextRun("Datová vrstva beze změny — STRATEGIE bude číst z pohledů ECv_Vytizeni_* a zapisovat přes procedury EC_Vytizeni_*, stejně jako dnes Excel. Napojení je přes EUROSOFT-MCP (už existuje).")], spacing:{after:80} }));
children.push(new Paragraph({ numbering:{reference:"n",level:0}, children:[new TextRun("Modul „Vytížení / Plánování\" v ERP — hlavní plocha jako webový grid (zakázky × časová osa) a matice vytížení montérů, s barvami a stavy. Reuse existující generátor jader/přehledů.")], spacing:{after:80} }));
children.push(new Paragraph({ numbering:{reference:"n",level:0}, children:[new TextRun("Akce jako tlačítka — 30 ribbon akcí se mapuje 1:1 na akce v ERP (přidej montéra, nastav odvoz, poznámka…), každá volá příslušnou proceduru EC_.")], spacing:{after:80} }));
children.push(new Paragraph({ numbering:{reference:"n",level:0}, children:[new TextRun("Přepočty (vytížení, kapacita dílny) — přenést z VBA do backendu (Python) nebo, pokud už je počítá SQL, použít pohledy PlanSuma / kapacitaDilny / Efektivita.")], spacing:{after:80} }));
children.push(new Paragraph({ numbering:{reference:"n",level:0}, children:[new TextRun("Sdílený provoz a živá data — STRATEGIE řeší nativně (víc uživatelů, auto-refresh gridu), odpadá excelové „Aktualizovat\" a „pro čtení\".")], spacing:{after:80} }));
children.push(new Paragraph({ numbering:{reference:"n",level:0}, children:[new TextRun("Propojení s docházkou — plán montérů (kdo/kdy/kolik hodin) lze provázat s modulem Spolupráce/Docházka (reálně odpracováno vs. plán).")], spacing:{after:80} }));

children.push(H2("Co je potřeba doplnit / ověřit"));
children.push(bullet("Přesné definice pohledů ECv_ a parametry procedur EC_ (sloupce, vstupy) — vytáhnout z MSSQL (máme přístup přes bridge/MCP)."));
children.push(bullet("Logika barvení a stavů (legenda v listu HELP) — přenést do STRATEGIE jako pravidla zobrazení."));
children.push(bullet("Číselníky: typy odvozů (KKO, rozvaděče, přejímka, instalace, doposílání, na sklad), typy nepřítomnosti (dovolená, nemoc, náhradní volno), typy událostí."));
children.push(bullet("Parametry kapacit (named ranges rn_Kapacita, rn_Kap1/2, rn_KalkZaplKoef, rn_PrumerVyp) — přenést jako konfiguraci."));

children.push(H2("Závěr"));
children.push(P("Tento Excel je ve skutečnosti zralá aplikace s čistě oddělenou databázovou vrstvou. Pro STRATEGIE je to ideální kandidát na migraci: přebíráme hotové views a procedury, nahrazujeme jen excelovou UI/VBA webovým modulem. Výsledkem bude plánování vytížení přímo v STRATEGII — sdílené, živé, provázané s docházkou a bez závislosti na Excelu.", { bold:false }));

const doc = new Document({
  creator: "Claude (id=23) — STRATEGIE",
  title: "Analýza: Plánování vytížení montérů (v162.xlsm)",
  styles: {
    default: { document: { run: { font:"Arial", size:21, color:"222222" } } },
    paragraphStyles: [
      { id:"Heading1", name:"Heading 1", basedOn:"Normal", next:"Normal", quickFormat:true,
        run:{ size:30, bold:true, color:BL, font:"Arial" }, paragraph:{ spacing:{before:300,after:160}, outlineLevel:0 } },
      { id:"Heading2", name:"Heading 2", basedOn:"Normal", next:"Normal", quickFormat:true,
        run:{ size:25, bold:true, color:ACC, font:"Arial" }, paragraph:{ spacing:{before:200,after:120}, outlineLevel:1 } },
    ]
  },
  numbering: { config: [
    { reference:"b", levels:[
      { level:0, format:LevelFormat.BULLET, text:"•", alignment:AlignmentType.LEFT, style:{paragraph:{indent:{left:540,hanging:300}}} },
      { level:1, format:LevelFormat.BULLET, text:"–", alignment:AlignmentType.LEFT, style:{paragraph:{indent:{left:1080,hanging:300}}} },
    ]},
    { reference:"n", levels:[
      { level:0, format:LevelFormat.DECIMAL, text:"%1.", alignment:AlignmentType.LEFT, style:{paragraph:{indent:{left:540,hanging:300}}} },
    ]},
  ]},
  sections: [{
    properties: { page: { size:{width:11906,height:16838}, margin:{top:1200,right:1100,bottom:1200,left:1100} } },
    footers: { default: new Footer({ children:[ new Paragraph({
      border:{ top:{style:BorderStyle.SINGLE,size:4,color:ACC,space:6} },
      tabStops:[{type:"right",position:9700}],
      children:[ new TextRun({text:"STRATEGIE · Analýza Plánování vytížení montérů", size:16, color:"888888"}),
        new TextRun({text:"\tStrana ", size:16, color:"888888"}),
        new TextRun({children:[PageNumber.CURRENT], size:16, color:"888888"}) ] }) ] }) },
    children
  }]
});

Packer.toBuffer(doc).then(buf=>{ fs.writeFileSync("/sessions/nifty-laughing-mccarthy/mnt/STRATEGIE/Analyza_Planovani_vytizeni_monteru.docx", buf); console.log("OK", buf.length, "B"); });
