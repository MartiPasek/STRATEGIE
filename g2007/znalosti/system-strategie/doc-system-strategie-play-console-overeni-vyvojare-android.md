# Google Play - overeni vyvojare pro Android (registrace balicku a podpisovych klicu, 10.8.2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Proc to je

Google od 30.9.2026 vyzaduje, aby byly vsechny aplikace zaregistrovane v ramci
"Overeni vyvojare softwaru pro Android". Neregistrovane aplikace na Google Play
budou celosvetove odstraneny. Neregistrovane aplikace z jinych zucastnenych obchodu
nepujde instalovat na certifikovana zarizeni ve vybranych zemich - vynuceni zacina
30.9.2026 v Brazilii, Indonesii, Singapuru a Thajsku, globalne az v roce 2027.
Sideload primo z naseho serveru tim zatim dotcen neni.

## Nas stav (overeno 10.8.2026 v Play Console)

Ucet vyvojare - "Marti Pasek", typ Organizace, ID 7788767915610025159,
vlastnik m.pasek@eurosoft.com, organizace EUROSOFT - System s.r.o.,
web www.eurosoft.com overeny, kontaktni mail i telefon overene.
Administratorsky pristup ma i Jirka (j.honomichl@eurosoft.com).

Aplikace - jedina, STRATEGIE, balicek `cz.strategie.mobile`, produkce.
Ma dve distribucni varianty se stejnym balickem - flavor `play` (AAB na Google Play,
bez SMS opravneni) a flavor `internal` (sideload APK se SMS branou, stahuje se
z `/api/v1/erp/app/mobile/download`).

Registrovane klice u balicku (obe polozky stav Overeno)
- `3E:7C:1B:E0:1B:E6:5A:AD:7D:26:6C:4C:F4:9B:CA:99:81:B7:F3:F8:0F:73:67:3C:33:A9:3E:12:7C:F0:5E:93`
  = podpisovy klic Google Play (Play App Signing), zaregistroval Google automaticky 9.6.2026
- `CC:AC:10:F2:70:0F:0B:57:4F:9F:E8:24:0C:56:24:B3:5A:2B:80:1B:C2:47:BC:7B:FA:AC:07:F8:DE:60:5B:84`
  = nas upload/release klic `APP\Mobile\strategie-release.jks`, alias `strategie`,
  CN=Marti Pasek, platnost do 20.10.2053. Timto klicem je podepsany sideload APK
  distribuovany mimo Play. Doplnil C28/Jirka 10.8.2026, nejdriv "Probiha kontrola",
  po chvili "Overeno".

## Jak se to dela (kdyby pribyl dalsi klic nebo balicek)

Play Console -> leve menu "Overeni vyvojare softwaru pro Android".
Zalozka "Nazvy balicku" - seznam balicku a poctu klicu, tlacitko
"Zaregistrovat nazev balicku" pro appky distribuovane mimo Play.
Klik na radek -> "Sprava klicu balicku" -> "Pridat klic" -> vlozi se
POUZE otisk SHA-256 certifikatu (zadne nahravani APK). Zalozka "Identita"
prebira jmeno a adresu z uctu vyvojare, nic se tam nevyplnuje zvlast.

Otisk naseho klice se ziska takto (JDK 17 je na stroji Jirky v Eclipse Adoptium)
`keytool -list -v -keystore APP\Mobile\strategie-release.jks -alias strategie`,
u hotoveho balicku `apksigner verify --print-certs <soubor.apk>`.

## Na co si dat pozor

Kdyby se release keystore ztratil nebo se menil, zmeni se i otisk a novy klic
se musi v Play Console doregistrovat - jinak sideload APK po plnem vynuceni
neprojde. Keystore i heslo k nemu jsou jen lokalne (gitignored), NEPATRI do gitu.

