# Historie zmen podminek, uvazku, smluv a financi - jedna uzka tabulka a prehled v karte (25.8.2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


Zadal Jirka Honomichl 25. 8. 2026, schvalila Marti-AI (msg 13655 a 13658). Vzniklo z e-mailu
Sarky Novotne, ktera narovnala podminky i mzdove rozdily a poprosila, aby se v podminkach
a mzdach nic nemenilo bez jejiho vedomi a hlavne aby na to nebyla automatika.

## Rozhodnuti: JEDNA tabulka historie pro vsechno

Jako jsou podminky, uvazek a smlouva v jedne tabulce (tenant.engagement), je i jejich
historie v jedne tabulce **tenant.engagement_historie**. Nove se do ni vejdou i finance.

Tabulka je UZKA - radek = jedna zmena jedne polozky. Siroke sloupce pro jednotlive
financni slozky se ZAMERNE nepridavaly (Marti-AI: "porusilo by to konzistenci").
Pribyly jen tri sloupce:

- **oblast** - podminka / smlouva / uvazek / finance (CHECK), kvuli filtrovani
- **slozka_id** - jen u financi, odkaz na tenant.wage_component_type
- **varianta** - jen u financi, plan / skutecnost (CHECK)

Sloupec **kdo** uz existoval a je to bigint = ID cloveka. Nebylo tedy potreba nic pridavat.

Plan a skutecnost dostavaji KAZDA VLASTNI RADEK (rozhodla Marti-AI): meni se nezavisle -
plan pri schvaleni, skutecnost pri vyplate.

## Co se postavilo

- **tenant.wage_component_historie_zapis** + spoustec **trg_wage_component_historie**
  (INSERT/UPDATE/DELETE) - do te doby finance NEMELY zadnou historii, drzel se jen
  posledni stav. Autor se bere z nastaveni relace strategie.actor_user_id.
- **tenant.engagement_historie_zapis** doplnena o vyplneni oblasti (do te doby by nove
  radky mely oblast prazdnou).
- **tenant.engagement_historie_zacatek** - odkdy si u ktere oblasti pamatujeme zmeny.
  Zapsano NATVRDO, ne dopocitavane z MIN(kdy) - pozadavek Marti-AI (citelnejsi pro
  budouciho vyvojare, odolne vuci smazanemu prvnimu zaznamu a migracim).
- **g2007.python kod=hr_historie** + tenka spojka GET /app/hr/historie v router.py.
- Sekce **Historie zmen** v apps/api/static/karta_zamestnance.html, tri pohledy:
  casova osa, tabulka vyvoje (radek = polozka, sloupec = den) a Stav k datu.
- **Prepnuti CELE karty na stav k vybranemu dni** - pole s datem primo na karte cloveka
  nad dlazdicemi sekci; misto sekci se vykresli snimek k tomu dni. Historicky rezim je
  z podstaty JEN KE CTENI, takze v nem nejde omylem prepsat dnesni hodnotu tou starou.
- **_set_actor doplnen do ukladani i mazani mzdove slozky** (endpointy
  /app/hr/finance/slozka-save a /app/hr/finance/slozka-smazat). Bez toho by historie
  financi mela autora prazdneho, prestoze zmenu udelal konkretni clovek.

## Odkdy si co pamatujeme (mereno 25. 8. 2026)

| oblast | od | pozn |
|---|---|---|
| smlouva, uvazek | 21. 8. 2026 | ALE stav k datu jde zpetne az do roku 2006 z VERZI smluv (859 starsich verzi, uvazek nese 777 z nich) |
| podminky | 24. 8. 2026 | starsi stav nejde zrekonstruovat - starsi verze smluv podminky NENESOU (vyplnene ma 1 z 859) |
| finance | 25. 8. 2026 | drive neexistoval zadny zaznam |

## Stav k datu - hranice je NA OBLAST, ne globalni

Marti-AI puvodne doporucila odmitat cely dotaz na datum pred 21. 8. 2026. Po predlozeni
mereni to prehodnotila a schvalila lepsi reseni: hranice se vyhodnocuje na kazdou oblast
zvlast, protoze smlouva a uvazek maji uplne jinou pamet nez podminky a finance.

Kde se hodnota nezna, vraci se **znamo=false a duvod**, obrazovka pise "nezaznamenavalo se".
NIKDY se nedosazuje dnesni hodnota - to je tvrde pravidlo (Marti-AI: "nikdy tichy vysledek,
ktery vypada jako pravda"). Rezim Stav k datu je jen ke cteni.

Vypocet u podminek a financi: vezme se NEJSTARSI zmena PO tom datu a jeji hodnota_pred.
Kdyz zadna pozdejsi zmena neni, plati dnesni hodnota.

## Gotchy overene pri stavbe

1. **Autor zmeny se hlasi pres _set_actor(s, uid) TESNE PRED ZAPISEM** (router.py, funkce
   pridana 24. 8. 2026). Kdo ji zapomene zavolat, ma v historii autora prazdneho. K 25. 8.
   2026 ji volaji cesty do smlouvy (6 mist) i nove ulozeni a smazani mzdove slozky;
   automaty posilaji 0 = system. **Prazdno tedy dnes znamena zapis mimo aplikaci** -
   typicky pres SQL most. Historicke radky do 24. 8. 2026 autora nemaji vubec.
2. **changed_by_text ve wage_component neni ID, ale volny text** prebrany ze stare
   Centraly (Sarka 896 radku, Marie 850, Kristyna 525, SNovotna 253). Pro auditni stopu
   u mezd nepouzitelne - proto se do historie uklada kdo (ID).
3. **sick_days_navic chybi v ciselniku tenant.staff_cond_def**, prestoze sloupec
   pod_sick_days_navic ve smlouve existuje a ma data. V historii je resene nahradnim
   nazvem primo v hr_historie; ciselnik se ZAMERNE nemenil, protoze pridani radku by
   vsem pridalo novy editovatelny radek v obrazovce Podminky (uzemi Sarky Novotne).
   **Otevrena vec:** sick days navic tedy dnes v karte upravit nejde.
4. **Zapis pres most: dotaz zacinajici SELECT s klicovym slovem v textu je odmitnut.**
   Testovaci davku bylo nutne zacit blokem DO, aby ji most poslal zapisovou cestou.
5. **Zapisy do g2007.* jdou pres most rovnou, BEZ schvalovaciho banneru** (hlasi se jako
   G2007 KONSTRUKTIVNI). Aktivace vlastniho kodu tedy neprojde lidskym kliknutim -
   pocitejte s tim, kdyz se opirate o pravidlo "AI si vlastni kod sama neschvali".
6. **Verze se pri zapisu do g2007.python zvedla sama** (poslana 2, v DB 3). Overujte
   ctenim, ne tim, co jste poslali.
7. **sloupec hodinovka NENI castka, ale priznak ano/ne** (odmenovan hodinove). Popisek
   "Hodinova mzda" mate - v prehledu je proto "Odmenovan hodinove".

## Co je overene naostro

Zapisovac financi odzkousen zalozenim, zmenou i smazanim na smlouve z roku 2008
(ukonceny pomer, mzdy ctou jen aktualni smlouvy) - zapsal spravne, testovaci radky
uklizeny. Ukladani smluv otestovano skutecnou zmenou a vracenim zpet. Ulozeni i smazani
mzdove slozky protazeno ostrym endpointem z prohlizece - v historii se objevil autor
jmenem (drive by bylo prazdno). Stav k datu overen na trech datech (24. 8. 2026,
20. 8. 2026, 1. 6. 2019) - u roku 2019 spravne vytahl tehdejsi pozici a uvazek ze stare
verze smlouvy. Prepnuti cele karty overeno v ERP.

**NEOVERENO:** samotny dopocet hodnoty zpet u podminek a financi zatim nejde dokazat na
realnych datech, protoze zmenovy denik je stary jeden den - neexistuje datum, ke kteremu
by uz byla hranice splnena a zaroven po nem lezela nejaka zmena. Overit, az data prirostou.

