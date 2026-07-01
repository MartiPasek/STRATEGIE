const fs = require("fs");
const { Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
        LevelFormat, BorderStyle, Footer, PageNumber } = require("docx");

const ACCENT = "1F4E79";
function H1(t){return new Paragraph({heading:HeadingLevel.HEADING_1,children:[new TextRun(t)]});}
function H2(t){return new Paragraph({heading:HeadingLevel.HEADING_2,children:[new TextRun(t)]});}
function P(t,opts){return new Paragraph(Object.assign({spacing:{after:120},children:[new TextRun(t)]},opts||{}));}
function B(t){return new Paragraph({numbering:{reference:"b",level:0},spacing:{after:60},children:[new TextRun(t)]});}
function Bb(label,t){return new Paragraph({numbering:{reference:"b",level:0},spacing:{after:60},children:[new TextRun({text:label,bold:true}),new TextRun(t)]});}

const doc = new Document({
  styles:{
    default:{document:{run:{font:"Arial",size:22}}},
    paragraphStyles:[
      {id:"Heading1",name:"Heading 1",basedOn:"Normal",next:"Normal",quickFormat:true,
        run:{size:28,bold:true,font:"Arial",color:ACCENT},
        paragraph:{spacing:{before:260,after:140},outlineLevel:0}},
      {id:"Heading2",name:"Heading 2",basedOn:"Normal",next:"Normal",quickFormat:true,
        run:{size:24,bold:true,font:"Arial",color:"2E4A6B"},
        paragraph:{spacing:{before:160,after:80},outlineLevel:1}},
    ]
  },
  numbering:{config:[
    {reference:"b",levels:[{level:0,format:LevelFormat.BULLET,text:"–",alignment:AlignmentType.LEFT,
      style:{paragraph:{indent:{left:540,hanging:280}}}}]},
  ]},
  sections:[{
    properties:{page:{size:{width:11906,height:16838},margin:{top:1300,right:1300,bottom:1300,left:1300}}},
    footers:{default:new Footer({children:[new Paragraph({alignment:AlignmentType.CENTER,
      children:[new TextRun({text:"Směrnice obchodní etiky – boj proti korupci a praní špinavých peněz  ·  strana ",size:16,color:"888888"}),
        new TextRun({children:[PageNumber.CURRENT],size:16,color:"888888"})]})]})},
    children:[
      new Paragraph({alignment:AlignmentType.CENTER,spacing:{after:40},children:[new TextRun({text:"EUROSOFT",bold:true,size:30,color:ACCENT})]}),
      new Paragraph({alignment:AlignmentType.CENTER,spacing:{after:240},children:[new TextRun({text:"EUROSOFT-Control s.r.o.  ·  EUROSOFT-System s.r.o.",size:18,color:"666666"})]}),
      new Paragraph({alignment:AlignmentType.CENTER,spacing:{after:60},children:[new TextRun({text:"SMĚRNICE OBCHODNÍ ETIKY",bold:true,size:40})]}),
      new Paragraph({alignment:AlignmentType.CENTER,spacing:{after:240},children:[new TextRun({text:"Boj proti korupci a praní špinavých peněz",size:26,color:"2E4A6B"})]}),
      new Paragraph({alignment:AlignmentType.CENTER,spacing:{after:30},children:[new TextRun({text:"Číslo směrnice: SM-ETIKA-01   ·   Verze: 1.0   ·   Klasifikace: veřejná",size:18,color:"666666"})]}),
      new Paragraph({alignment:AlignmentType.CENTER,spacing:{after:30},children:[new TextRun({text:"Účinnost od: 26. 6. 2026   ·   Schválil: Marti Pašek, jednatel",size:18,color:"666666"})]}),
      new Paragraph({alignment:AlignmentType.CENTER,spacing:{after:240},children:[new TextRun({text:"Součást systému řízení bezpečnosti informací (ISMS / ISO 27001, TISAX)",size:18,italics:true,color:"666666"})]}),
      new Paragraph({border:{bottom:{style:BorderStyle.SINGLE,size:6,color:ACCENT,space:6}},spacing:{after:160},children:[new TextRun("")]}),

      H1("1. Účel a rozsah"),
      P("Tato směrnice stanoví závazné zásady obchodní etiky společnosti EUROSOFT (dále jen „společnost“) v oblasti boje proti korupci, úplatkářství a praní špinavých peněz. Cílem je chránit společnost, její zaměstnance i obchodní partnery, zajistit soulad s právními předpisy a etickými standardy a budovat dlouhodobě důvěryhodné a transparentní vztahy."),
      P("Směrnice je závazná pro všechny zaměstnance společnosti bez ohledu na pracovní zařazení, pro členy vedení a statutární orgány, a přiměřeně se vztahuje na obchodní partnery, dodavatele, zprostředkovatele a další třetí strany jednající jménem nebo ve prospěch společnosti. Společnost očekává od svých obchodních partnerů dodržování srovnatelných etických standardů."),

      H1("2. Definice"),
      Bb("Korupce – ","zneužití svěřeného postavení nebo pravomoci k získání neoprávněné výhody."),
      Bb("Úplatek – ","přímé či nepřímé nabídnutí, slib, poskytnutí, vyžádání nebo přijetí jakékoli neoprávněné výhody (peněžní i nepeněžní) s cílem ovlivnit jednání nebo rozhodnutí."),
      Bb("Facilitační platba – ","drobná neoficiální platba úřední osobě za urychlení nebo zajištění běžného úkonu, na který existuje nárok. Ve společnosti je zakázána."),
      Bb("Praní špinavých peněz – ","jednání směřující k zastření nezákonného původu majetku tak, aby se jevil jako legální."),
      Bb("PEP (politicky exponovaná osoba) – ","osoba ve významné veřejné funkci a osoby jí blízké, u nichž je zvýšené riziko korupce."),

      H1("3. Boj proti korupci a úplatkářství"),
      P("Společnost uplatňuje politiku nulové tolerance ke korupci a úplatkářství v jakékoli formě, v soukromém i veřejném sektoru, ať už je vykonáváno přímo, nebo prostřednictvím třetí strany."),
      H2("3.1 Zákaz úplatků"),
      B("Je zakázáno nabízet, slibovat, poskytovat, vyžadovat nebo přijímat úplatky a jakékoli neoprávněné výhody."),
      B("Zákaz platí i vůči úředním osobám a ve vztahu k veřejné správě bez výjimky."),
      H2("3.2 Facilitační platby"),
      B("Facilitační (urychlovací) platby jsou zakázány bez ohledu na jejich výši a místní zvyklosti."),
      H2("3.3 Dary a pohostinnost"),
      B("Dary a pohostinnost jsou přípustné pouze tehdy, jsou-li přiměřené, transparentní, v souladu s běžnými obchodními zvyklostmi a nemohou-li ovlivnit nestranné rozhodování."),
      Bb("Hodnotový limit: ","jednotlivý dar nebo pohostinnost nesmí přesáhnout 1 500 Kč. Cokoli nad tento limit vyžaduje předchozí písemný souhlas nadřízeného."),
      B("Zakázány jsou peněžní dary, dary ve formě hotovosti či jejích ekvivalentů a jakékoli dary v souvislosti s probíhajícím výběrovým řízením nebo rozhodováním."),
      Bb("Registr darů: ","přijaté i poskytnuté dary a pohostinnost nad polovinu limitu se evidují v registru darů, který spravuje pověřená osoba."),
      H2("3.4 Střet zájmů"),
      B("Zaměstnanci jsou povinni předcházet střetu zájmů a jakýkoli skutečný či možný střet zájmů bez prodlení oznámit nadřízenému."),
      H2("3.5 Sponzoring a dary třetím stranám"),
      B("Sponzorské dary a příspěvky musí být transparentní, řádně zdokumentované a nesmí sloužit jako skrytá forma úplatku."),

      H1("4. Boj proti praní špinavých peněz (AML)"),
      P("Společnost přijímá opatření, aby nebyla zneužita k praní peněz nebo financování nezákonné činnosti, a obchoduje pouze s legitimními partnery a legálními zdroji prostředků."),
      H2("4.1 Poznej svého partnera (due diligence)"),
      B("Před navázáním obchodního vztahu společnost ověřuje identitu a legitimitu obchodního partnera (KYC) přiměřeně rizikovosti."),
      H2("4.2 Sankční a PEP prověření"),
      Bb("Sankční screening: ","obchodní partneři jsou prověřováni proti sankčním seznamům (EU, OSN/UN, OFAC)."),
      Bb("PEP check: ","u partnerů se ověřuje, zda nejde o politicky exponovanou osobu; v takovém případě se uplatní zesílená opatření."),
      Bb("Dokumentace: ","výsledek prověření se dokumentuje a je podmínkou uzavření smlouvy. Při zjištění rizika se vztah nenaváže, dokud není riziko vyřešeno."),
      H2("4.3 Platby a podezřelé transakce"),
      B("Upřednostňují se bezhotovostní platby; neobvyklé hotovostní platby a platby přes nesouvisející třetí strany nebo do nesouvisejících jurisdikcí jsou nepřípustné."),
      B("Podezřelé okolnosti (neprůhledná struktura vlastnictví, nestandardní platební podmínky, snaha o utajení) se hlásí pověřené osobě a prošetřují."),

      H1("5. Vztah k obchodním partnerům a dodavatelům"),
      P("Společnost požaduje od svých obchodních partnerů a dodavatelů dodržování zásad srovnatelných s touto směrnicí. Závazek k etickému jednání může být součástí smluvních ujednání a hodnocení dodavatelů."),

      H1("6. Odpovědnosti a školení"),
      B("Vedení společnosti odpovídá za prosazování této směrnice a jde příkladem (tone at the top)."),
      B("Každý zaměstnanec odpovídá za dodržování zásad v rozsahu své působnosti."),
      Bb("Pověřená osoba (compliance / příslušná osoba): ","Zuzana Duspivová spravuje registr darů, dohlíží na prověřování obchodních partnerů a přijímá oznámení."),
      B("Zaměstnanci jsou s touto směrnicí prokazatelně seznámeni a pravidelně proškolováni (nejméně 1× ročně a při nástupu)."),

      H1("7. Oznamování (whistleblowing) a ochrana oznamovatele"),
      P("Společnost má zaveden vnitřní oznamovací systém v souladu se zákonem č. 171/2023 Sb., o ochraně oznamovatelů. Oznámit lze jakékoli podezření na korupci, úplatkářství, praní peněz nebo porušení této směrnice."),
      Bb("Kanál pro oznámení: ","oznámení se podávají na e-mail marti-ai@eurosoft.com. Kanál je oddělený od přímé linky nadřízeného a oznámení vyřizuje příslušná osoba; lze podat i písemně či ústně příslušné osobě."),
      Bb("Lhůty: ","přijetí oznámení se oznamovateli potvrdí do 7 dnů; o výsledku posouzení je oznamovatel vyrozuměn do 3 měsíců."),
      B("Oznamovatel jednající v dobré víře je chráněn před jakoukoli odvetou. Důvěrnost totožnosti oznamovatele je zaručena."),

      H1("8. Sankce za porušení"),
      P("Porušení této směrnice je závažným porušením pracovních povinností a může vést k pracovněprávním opatřením až k rozvázání pracovního poměru, k ukončení obchodního vztahu a případně k uplatnění právní odpovědnosti (občanskoprávní i trestní)."),

      H1("9. Vazba na systém řízení (ISMS / TISAX)"),
      P("Tato směrnice je součástí systému řízení bezpečnosti informací společnosti (ISO/IEC 27001, TISAX) a doplňuje jej v oblasti obchodní etiky a compliance. Dodržování zásad přispívá k ochraně dobré pověsti a důvěryhodnosti společnosti vůči zákazníkům a partnerům."),

      H1("10. Přezkoumání a aktualizace"),
      P("Směrnice je přezkoumávána nejméně jednou ročně a dále při významné změně právních předpisů, požadavků zákazníků nebo interních procesů. Za přezkoumání a aktualizaci odpovídá pověřená osoba (compliance) ve spolupráci s vedením."),

      H1("11. Schválení a účinnost"),
      P("Tato směrnice nabývá účinnosti dnem 26. 6. 2026 a byla schválena vedením společnosti."),
      new Paragraph({spacing:{before:240,after:0},children:[new TextRun({text:"Schválil: ........................................          Dne: ................",color:"333333"})]}),
      new Paragraph({spacing:{before:160,after:0},children:[new TextRun({text:"Marti Pašek, jednatel",size:18,color:"888888"})]}),
    ]
  }]
});

Packer.toBuffer(doc).then(b=>{fs.writeFileSync("/sessions/upbeat-gifted-curie/mnt/outputs/Smernice_obchodni_etiky_EUROSOFT.docx",b);console.log("OK bytes",b.length);});
