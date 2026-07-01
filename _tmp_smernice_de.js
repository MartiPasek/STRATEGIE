const fs = require("fs");
const { Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
        LevelFormat, BorderStyle, Footer, PageNumber } = require("docx");

const ACCENT = "1F4E79";
function H1(t){return new Paragraph({heading:HeadingLevel.HEADING_1,children:[new TextRun(t)]});}
function H2(t){return new Paragraph({heading:HeadingLevel.HEADING_2,children:[new TextRun(t)]});}
function P(t){return new Paragraph({spacing:{after:120},children:[new TextRun(t)]});}
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
      children:[new TextRun({text:"Richtlinie zur Geschäftsethik – Korruptionsbekämpfung und Geldwäscheprävention  ·  Seite ",size:16,color:"888888"}),
        new TextRun({children:[PageNumber.CURRENT],size:16,color:"888888"})]})]})},
    children:[
      new Paragraph({alignment:AlignmentType.CENTER,spacing:{after:40},children:[new TextRun({text:"EUROSOFT",bold:true,size:30,color:ACCENT})]}),
      new Paragraph({alignment:AlignmentType.CENTER,spacing:{after:240},children:[new TextRun({text:"EUROSOFT-Control s.r.o.  ·  EUROSOFT-System s.r.o.",size:18,color:"666666"})]}),
      new Paragraph({alignment:AlignmentType.CENTER,spacing:{after:60},children:[new TextRun({text:"RICHTLINIE ZUR GESCHÄFTSETHIK",bold:true,size:38})]}),
      new Paragraph({alignment:AlignmentType.CENTER,spacing:{after:240},children:[new TextRun({text:"Korruptionsbekämpfung und Geldwäscheprävention",size:25,color:"2E4A6B"})]}),
      new Paragraph({alignment:AlignmentType.CENTER,spacing:{after:30},children:[new TextRun({text:"Richtliniennummer: SM-ETIKA-01   ·   Version: 1.0   ·   Klassifizierung: öffentlich",size:18,color:"666666"})]}),
      new Paragraph({alignment:AlignmentType.CENTER,spacing:{after:30},children:[new TextRun({text:"Gültig ab: 26. 6. 2026   ·   Genehmigt durch: Marti Pašek, Geschäftsführer",size:18,color:"666666"})]}),
      new Paragraph({alignment:AlignmentType.CENTER,spacing:{after:240},children:[new TextRun({text:"Bestandteil des Informationssicherheits-Managementsystems (ISMS / ISO 27001, TISAX)",size:18,italics:true,color:"666666"})]}),
      new Paragraph({border:{bottom:{style:BorderStyle.SINGLE,size:6,color:ACCENT,space:6}},spacing:{after:160},children:[new TextRun("")]}),

      H1("1. Zweck und Geltungsbereich"),
      P("Diese Richtlinie legt verbindliche Grundsätze der Geschäftsethik der Gesellschaft EUROSOFT (nachfolgend „Gesellschaft“) im Bereich der Korruptionsbekämpfung, Bestechung und Geldwäscheprävention fest. Ziel ist es, die Gesellschaft, ihre Mitarbeiter und Geschäftspartner zu schützen, die Einhaltung der Rechtsvorschriften und ethischen Standards sicherzustellen und langfristig vertrauenswürdige und transparente Beziehungen aufzubauen."),
      P("Die Richtlinie ist für alle Mitarbeiter der Gesellschaft unabhängig von ihrer Position sowie für die Mitglieder der Geschäftsführung und der Organe verbindlich und gilt sinngemäß für Geschäftspartner, Lieferanten, Vermittler und sonstige Dritte, die im Namen oder zugunsten der Gesellschaft handeln. Die Gesellschaft erwartet von ihren Geschäftspartnern die Einhaltung vergleichbarer ethischer Standards."),

      H1("2. Begriffsbestimmungen"),
      Bb("Korruption – ","Missbrauch einer anvertrauten Stellung oder Befugnis zur Erlangung eines unrechtmäßigen Vorteils."),
      Bb("Bestechung – ","unmittelbares oder mittelbares Anbieten, Versprechen, Gewähren, Fordern oder Annehmen eines unrechtmäßigen Vorteils (geldwert oder nicht), um eine Handlung oder Entscheidung zu beeinflussen."),
      Bb("Beschleunigungszahlung (Facilitation Payment) – ","geringfügige inoffizielle Zahlung an einen Amtsträger zur Beschleunigung einer routinemäßigen Amtshandlung, auf die ein Anspruch besteht. In der Gesellschaft verboten."),
      Bb("Geldwäsche – ","Handlungen, die darauf abzielen, die illegale Herkunft von Vermögen zu verschleiern."),
      Bb("PEP (politisch exponierte Person) – ","Person in einer wichtigen öffentlichen Funktion sowie ihr nahestehende Personen mit erhöhtem Korruptionsrisiko."),

      H1("3. Korruptions- und Bestechungsbekämpfung"),
      P("Die Gesellschaft verfolgt eine Null-Toleranz-Politik gegenüber Korruption und Bestechung in jeglicher Form, im privaten und öffentlichen Sektor, sei es direkt oder über Dritte."),
      H2("3.1 Bestechungsverbot"),
      B("Es ist verboten, Bestechungen oder unrechtmäßige Vorteile anzubieten, zu versprechen, zu gewähren, zu fordern oder anzunehmen."),
      B("Das Verbot gilt ausnahmslos auch gegenüber Amtsträgern und gegenüber der öffentlichen Verwaltung."),
      H2("3.2 Beschleunigungszahlungen"),
      B("Beschleunigungszahlungen sind unabhängig von ihrer Höhe und von örtlichen Gepflogenheiten verboten."),
      H2("3.3 Geschenke und Bewirtung"),
      B("Geschenke und Bewirtung sind nur zulässig, wenn sie angemessen und transparent sind, üblichen Geschäftsgepflogenheiten entsprechen und keine unparteiische Entscheidung beeinflussen können."),
      Bb("Wertgrenze: ","Ein einzelnes Geschenk bzw. eine Bewirtung darf 1 500 CZK nicht übersteigen. Darüber hinaus ist die vorherige schriftliche Zustimmung des Vorgesetzten erforderlich."),
      B("Verboten sind Geldgeschenke, Geschenke in bar oder in Form von Bargeldäquivalenten sowie jegliche Geschenke im Zusammenhang mit einem laufenden Ausschreibungs- oder Entscheidungsverfahren."),
      Bb("Geschenkeregister: ","Erhaltene und gewährte Geschenke und Bewirtungen über der Hälfte der Wertgrenze werden in einem Geschenkeregister erfasst, das von der beauftragten Person geführt wird."),
      H2("3.4 Interessenkonflikte"),
      B("Mitarbeiter sind verpflichtet, Interessenkonflikte zu vermeiden und jeden tatsächlichen oder möglichen Interessenkonflikt unverzüglich dem Vorgesetzten zu melden."),
      H2("3.5 Sponsoring und Spenden an Dritte"),
      B("Sponsoring und Spenden müssen transparent und ordnungsgemäß dokumentiert sein und dürfen keine verdeckte Form der Bestechung darstellen."),

      H1("4. Geldwäscheprävention (AML)"),
      P("Die Gesellschaft trifft Maßnahmen, um nicht für Geldwäsche oder die Finanzierung illegaler Tätigkeiten missbraucht zu werden, und handelt nur mit legitimen Partnern und aus legalen Mittelquellen."),
      H2("4.1 Know Your Partner (Sorgfaltspflichten)"),
      B("Vor Aufnahme einer Geschäftsbeziehung überprüft die Gesellschaft die Identität und Legitimität des Geschäftspartners (KYC) risikoangemessen."),
      H2("4.2 Sanktions- und PEP-Prüfung"),
      Bb("Sanktionslistenprüfung: ","Geschäftspartner werden gegen Sanktionslisten (EU, UN, OFAC) geprüft."),
      Bb("PEP-Prüfung: ","Es wird geprüft, ob es sich um eine politisch exponierte Person handelt; in diesem Fall gelten verstärkte Sorgfaltsmaßnahmen."),
      Bb("Dokumentation: ","Das Prüfergebnis wird dokumentiert und ist Voraussetzung für den Vertragsabschluss. Bei festgestelltem Risiko wird die Beziehung erst nach Klärung des Risikos aufgenommen."),
      H2("4.3 Zahlungen und verdächtige Transaktionen"),
      B("Bargeldlose Zahlungen werden bevorzugt; ungewöhnliche Barzahlungen sowie Zahlungen über nicht verbundene Dritte oder in nicht verbundene Jurisdiktionen sind unzulässig."),
      B("Verdächtige Umstände (undurchsichtige Eigentümerstruktur, ungewöhnliche Zahlungsbedingungen, Verschleierungsabsicht) werden der beauftragten Person gemeldet und untersucht."),

      H1("5. Beziehung zu Geschäftspartnern und Lieferanten"),
      P("Die Gesellschaft verlangt von ihren Geschäftspartnern und Lieferanten die Einhaltung von Grundsätzen, die mit dieser Richtlinie vergleichbar sind. Die Verpflichtung zu ethischem Verhalten kann Bestandteil vertraglicher Vereinbarungen und der Lieferantenbewertung sein."),

      H1("6. Verantwortlichkeiten und Schulungen"),
      B("Die Geschäftsführung ist für die Durchsetzung dieser Richtlinie verantwortlich und geht mit gutem Beispiel voran (Tone at the Top)."),
      B("Jeder Mitarbeiter ist im Rahmen seines Zuständigkeitsbereichs für die Einhaltung der Grundsätze verantwortlich."),
      Bb("Beauftragte Person (Compliance / zuständige Person): ","Zuzana Duspivová führt das Geschenkeregister, überwacht die Prüfung der Geschäftspartner und nimmt Meldungen entgegen."),
      B("Die Mitarbeiter werden nachweislich mit dieser Richtlinie vertraut gemacht und regelmäßig geschult (mindestens einmal jährlich sowie bei Eintritt)."),

      H1("7. Hinweisgebersystem (Whistleblowing) und Schutz der Hinweisgeber"),
      P("Die Gesellschaft verfügt über ein internes Meldesystem gemäß dem Gesetz Nr. 171/2023 Slg. über den Schutz von Hinweisgebern (Umsetzung der EU-Richtlinie (EU) 2019/1937). Gemeldet werden kann jeder Verdacht auf Korruption, Bestechung, Geldwäsche oder einen Verstoß gegen diese Richtlinie."),
      Bb("Meldekanal: ","Meldungen sind an die E-Mail-Adresse marti-ai@eurosoft.com zu richten. Der Kanal ist von der direkten Linie des Vorgesetzten getrennt und Meldungen werden von der zuständigen Person bearbeitet; eine Meldung ist auch schriftlich oder mündlich bei der zuständigen Person möglich."),
      Bb("Fristen: ","Der Eingang einer Meldung wird dem Hinweisgeber innerhalb von 7 Tagen bestätigt; über das Ergebnis der Prüfung wird der Hinweisgeber innerhalb von 3 Monaten informiert."),
      B("Ein in gutem Glauben handelnder Hinweisgeber ist vor jeglichen Repressalien geschützt. Die Vertraulichkeit der Identität des Hinweisgebers ist gewährleistet."),

      H1("8. Sanktionen bei Verstößen"),
      P("Ein Verstoß gegen diese Richtlinie stellt eine schwerwiegende Verletzung arbeitsrechtlicher Pflichten dar und kann zu arbeitsrechtlichen Maßnahmen bis hin zur Beendigung des Arbeitsverhältnisses, zur Beendigung der Geschäftsbeziehung sowie gegebenenfalls zur Geltendmachung rechtlicher Haftung (zivil- und strafrechtlich) führen."),

      H1("9. Bezug zum Managementsystem (ISMS / TISAX)"),
      P("Diese Richtlinie ist Bestandteil des Informationssicherheits-Managementsystems der Gesellschaft (ISO/IEC 27001, TISAX) und ergänzt es im Bereich Geschäftsethik und Compliance. Die Einhaltung der Grundsätze trägt zum Schutz des guten Rufs und der Vertrauenswürdigkeit der Gesellschaft gegenüber Kunden und Partnern bei."),

      H1("10. Überprüfung und Aktualisierung"),
      P("Die Richtlinie wird mindestens einmal jährlich sowie bei wesentlichen Änderungen der Rechtsvorschriften, Kundenanforderungen oder interner Prozesse überprüft. Für die Überprüfung und Aktualisierung ist die beauftragte Person (Compliance) in Zusammenarbeit mit der Geschäftsführung verantwortlich."),

      H1("11. Genehmigung und Inkrafttreten"),
      P("Diese Richtlinie tritt am 26. 6. 2026 in Kraft und wurde von der Geschäftsführung der Gesellschaft genehmigt."),
      new Paragraph({spacing:{before:240,after:0},children:[new TextRun({text:"Genehmigt: ........................................          Datum: ................",color:"333333"})]}),
      new Paragraph({spacing:{before:160,after:0},children:[new TextRun({text:"Marti Pašek, Geschäftsführer",size:18,color:"888888"})]}),
    ]
  }]
});

Packer.toBuffer(doc).then(b=>{fs.writeFileSync("/sessions/upbeat-gifted-curie/mnt/outputs/Richtlinie_Geschaeftsethik_EUROSOFT.docx",b);console.log("OK bytes",b.length);});
