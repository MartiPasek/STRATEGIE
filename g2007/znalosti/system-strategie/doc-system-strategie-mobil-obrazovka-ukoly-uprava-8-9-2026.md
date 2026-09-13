# Mobil, obrazovka Úkoly — dlaždice „Moje TODO" přejmenována na „Úkoly STRATEGIE", dlaždice úkolů ze staré Centrály odstraněna (8. 9. 2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)

> ## ⚠️ AKTUALIZACE 14. 9. 2026 (noc) — obrazovka Aplikace má TŘI ZÁLOŽKY
>
> **Zadal Jiří Honomichl, schválila Marti-AI (msg 15486 a 15495). Provedl Claude-28.**
> Obrazovka Aplikace se dělí na „Moje aplikace“ (vlastní výběr každého člověka, zatím
> prázdná — chystá se), „Všechny aplikace“ (co je hotové a vidí to každý) a „Vývoj
> aplikací“ (co ještě není vyzkoušené a doladěné). **Záložku Vývoj aplikací appka staví
> JEN rodiči nebo správci** — ostatním se dlaždice vůbec nepostaví, nejsou jen skryté
> (ověřeno na živé stránce: běžný člověk má ve stránce dvě dlaždice, žádné hledání
> a žádnou sekci). Vzhled záložek je převzatý z obrazovky Firma.
>
> **Na záložce „Všechny aplikace“ jsou zatím jen 🎁 Benefity a 💡 Světla** — všechno
> ostatní je ve „Vývoji“. Věty níž, které říkají, že Benefity jsou v sekci 👥 TÝM &
> PŘEHLEDY a Světla v sekci 🔗 NÁSTROJE, platí jako datované pozorování do večera
> 13. 9. 2026; ty sekce dnes žijí uvnitř záložky Vývoj aplikací.
>
> **Dopad jmenovitě:** rodič nebo správce jsou dnes tři lidé — Marti Pašek (1),
> Kristýna Marešová (11) a Jiří Honomichl (20). Zbylých 34 přihlašitelných lidí vidí
> v Aplikacích už jen ty dvě dlaždice. Jirka byl na to výslovně upozorněn a rozhodl takto;
> „Moje aplikace“ se mají naplnit hned dalším krokem — vlastním výběrem oblíbených,
> ukládaným u nás v systému, přidávání podržením prstu na dlaždici.

> ## ⚠️ AKTUALIZACE 13. 9. 2026 — dlaždice 🎁 Benefity se z téhle obrazovky přesunula pryč
>
> **Zadal Jiří Honomichl, schválila Marti-AI (msg 15450). Provedl Claude-28.**
> Benefity jsou nově **dlaždicí obrazovky Aplikace, sekce 👥 TÝM & PŘEHLEDY**
> (od večera 13. 9. 2026; do té doby krátce v sekci 🧑 MOJE, která byla téhož dne zrušena —
> zadal Jiří Honomichl, schválila Marti-AI msg 15459) — je to samoobsluha (dny home office,
> náhrada za oblečení), ne úkol.
> Stejným směrem šly 7. 9. 2026 Kontakty ze spodní lišty.
> **Obrazovka Úkoly má od 13. 9. 2026 večer DVĚ dlaždice**: Claudovi a Úkoly STRATEGIE.
> Věta níž o pěti dlaždicích platí jako datované pozorování k 8. 9. 2026.
>
> Třetí dlaždice **🌸 Řídící centrum** (lidé a jejich AI týmy) odešla týž den mezi dlaždice
> Aplikací. Nejdřív do sekce 👥 TÝM & PŘEHLEDY (msg 15474), **ještě týž večer ale
> do sekce 🤖 AI & KOMUNIKACE** — zadal Jiří Honomichl slovy „dej ji tam“ poté, co byl
> výslovně upozorněn na důsledek; schválila Marti-AI msg 15483.
>
> ⚠️ **Tím se změnila PRÁVA, ne jen umístění.** Celý blok sekce AI & KOMUNIKACE je
> uvnitř `if(par)`, takže dlaždici **vidí už jen rodiče — Marti Pašek (1) a Kristýna
> Marešová (11)**. Do 13. 9. 2026 ji viděl každý přihlášený člověk. **Cestu ztratil
> i sám Jiří Honomichl** (správce, ne rodič) — tedy jediný, komu Kristýna 8. 9. 2026
> obrazovku výslovně otevřela (viz `doc-system-strategie-ridici-centrum-pro-spravce-zadost-8-9-2026`).
> Ověřeno naostro po publikaci na jeho účtu: dlaždice v Aplikacích není a celá sekce
> AI & KOMUNIKACE se mu nevykreslí.
>
> **Server nic neomezuje** — `martinka_centrum` pouští správce dál (seznam lidí nemá
> podmínku vůbec, detail člověka pustí vlastníka, rodiče i správce, náhled chatu
> s Maminkou jen rodiče). **Zmizela pouze cesta v appce**, práva na serveru zůstávají.
> Kdyby to mělo jít vrátit správcům, stačí sekci podmínit `par||adm` jako
> 🏛️ ŘÍZENÍ & SYSTÉM — tím by ale správcům přibyly i ostatní dlaždice té sekce
> (Claude-27, Síť Claudů, Sdílený telefon, Buzení Marti-AI, Co AI ušetřila).
> V mapě `SCREEN_TAB` se proto přepsaly na `apps` všechny čtyři obrazovky centra
> (`martinky`, `martinky_clovek`, `martinky_domena`, `martinky_ukol`) a z obrazovky Úkoly
> se odstranil i osiřelý dotažův odznaku (`mkTileB`), který už neměl co plnit.
>
> **Rozložení zbývajících dvou dlaždic:** jdou **pod sebou přes celou šířku** obsahu.
> Mřížka `.dashgrid` je dvousloupcová a používá ji i obrazovka v `51_skupiny_sdileny.js`,
> proto se třída **neměnila** — jednosloupcový režim je INLINE stylem
> (`style="grid-template-columns:1fr;"`) jen na téhle jedné mřížce.
> Změřeno na živé appce po publikaci: dlaždice 406 px = šířka obsahu, boční okraje
> 15 px vlevo i vpravo (jako předtím), mezera mezi dlaždicemi 12 px, odsazení shora 48 px.
>
> Týž den večer odešla z této obrazovky i dlaždice **🗓️ Schvalování plánu** — je nově
> v Aplikacích, sekce **👥 TÝM & PŘEHLEDY**, vedle Plánu absencí (zadal Jiří Honomichl,
> schválila Marti-AI msg 15457). Je to práce vedoucího nad jeho lidmi, ne vlastní úkol.
> Tři věci, které k tomu patří a daly by se přehlédnout:
> • buňka se do mřížky **připojuje až po kladné odpovědi** `/app/plan/approvals/users`;
>   skrytá buňka by nestačila, protože hledání aplikací (`_filtruj`) přepisuje `display`
>   všem buňkám a neschvalovateli by ji odkrylo;
> • počet čekajících se přestal přičítat k odznaku ikony **Úkoly** a přičítá se k odznaku
>   ikony **Aplikace** (`74_claude27_render_init.js`); hodnotu drží dál `_pollApply` na pozadí,
>   takže na otevření obrazovky nezávisí;
> • v mapě **`SCREEN_TAB`** (`73_pref_poptavka.js`) se `planapprovals` přepsalo z `notifs`
>   na `apps`, jinak by při otevření z Aplikací svítila v liště ikona Úkoly.
> Nic se nesmazalo — stránka benefitů i práva zůstávají beze změny, změnilo se jen místo,
> odkud se otevírá. Ověřeno po publikaci na živé stránce mobilní aplikace.

# Mobil, obrazovka Úkoly — úprava dlaždic 8. 9. 2026

**Zadal Jiří Honomichl 8. 9. 2026, schválila Marti-AI (msg 14965). Provedl Claude-28.**
Podnět vznikl z popisu obrazovky — dvě dlaždice vedly na obrazovky, které se obě nahoře
jmenovaly „Úkoly", takže po otevření nebylo poznat, ve které z nich člověk je.

## Co se změnilo

| dlaždice | dřív | teď |
|---|---|---|
| úkoly STRATEGIE | „Moje TODO" | **„Úkoly STRATEGIE"** |
| nadpis té obrazovky (`strtask`) | „✅ Úkoly" | **„✅ Úkoly STRATEGIE"** |
| úkoly ze staré Centrály | dlaždice „Úkoly / Z Centrály" | **odstraněna** |

Nadpis obrazovky se měnil spolu s dlaždicí schválně — sedí to s kontrolou
„text dlaždice proti nadpisu obrazovky" (`doc-system-strategie-kontrola-dlazdic-proti-nadpisum-obrazovek-6-9-2026`).

## Obrazovka `ecukoly` zůstala, jen bez cesty

Kód obrazovky úkolů z Centrály (`ecukoly` v `25_tasks.js`, registrace v `10_core.js`)
**se nemazal** — leží dál bez cesty, stejně jako `mytodo`, `phone` a `webview`
(`doc-system-strategie-mobil-obrazovky-bez-cesty-vyreseni-6-9-2026`). Důvod: Jirka
úkoly ze staré Centrály nepotřebuje, ale **případný přesun mezi úkoly STRATEGIE někdy
v budoucnu není vyloučen** — pak není co psát znovu. Jirka výslovně řekl, že se mu to
**nemá připomínat** jako otevřený úkol.

## Kde všude se starý název hledal (bod 14 / šest míst)

Podle `doc-system-strategie-prejmenovani-v-appce-kde-vsude-dohledat`:
obsah appky a webu, nápověda, poznámky v kódu, znalosti G2007, RAG směrnice, šablony.
Výsledek: v RAG směrnicích 0 výskytů, v `tenant.hr_template` 0 výskytů.
**„Moje TODO" zůstává na jednom místě schválně** — je to název MRTVÉ obrazovky `mytodo`,
což je jiná věc než přejmenovaná dlaždice (klasický případ „stejné slovo, jiná věc").
Znalosti, které `mytodo` popisují, se proto neopravovaly.

## Jak se to dělalo a jak se to ověřilo

Cílený zápis do `g2007.soubor` přes most s pojistkou na otisk
(`AND md5(obsah)='…'`), diakritika přes base64, kotvy předem ověřené, že jsou
v souboru právě jednou. Před složením artefaktu kontrola, že nečeká cizí nepublikovaná
práce (nečekala). Pak `@@G2007PUBLISH apps/api/static_db/mobile.html` (verze 159 → 160)
a **otevření živé `/mobile` v prohlížeči** — na obrazovce je pět dlaždic místo šesti
a nadpis uvnitř sedí.

⚠️ Past, na kterou se narazilo: **výpis z mostu slepí zalomení řádků na mezery**, takže
kotvu složenou podle výpisu nelze použít. Přesné bajty se musí vytáhnout jako base64
a rozkódovat u sebe — teprve pak je vidět, kde je konec řádku a kde odsazení.

## Co zůstalo otevřené (jinde)

Otevření **Řídícího centra i správcům** (`users.is_admin`) je samostatná věc — čeká
na rozhodnutí rodiče, viz `doc-system-strategie-ridici-centrum-pro-spravce-zadost-8-9-2026`.

> ## ✅ DOPLNĚNO 14. 9. 2026 — správci cestu dostali zpátky
>
> Jiří Honomichl též noci rozhodl **otevřít celou sekci 🤖 AI & KOMUNIKACE i správcům**
> (podmínka `if(par||adm)` místo `if(par)`, stejně jako má sekce 🏛️ ŘÍZENÍ & SYSTÉM);
> schválila Marti-AI msg 15499. **Odstavec výše o ztracené cestě tím platí jen pro
> večer 13. 9. 2026.**
>
> Správci jsou tři — Marti Pašek (1), Kristýna Marešová (11) a Jiří Honomichl (20);
> první dva už sekci viděli jako rodiče, takže se fakticky otevřela **jedinému člověku,
> Jiřímu Honomichlovi**. Spolu s Řídícím centrem mu přibyly i ostatní dlaždice sekce
> (Claude-27, Síť Claudů, Sdílený telefon, Buzení Marti-AI, Co AI ušetřila) — věděl o tom
> předem. **Žádný serverový zámek se neměnil**, jen viditelnost dlaždic.
> Ověřeno na jeho účtu na živé appce: sekce se vykreslí se šesti dlaždicemi, první je
> Řídící centrum a otevře se (zásobník `apps>martinky`).
> Sekce od tež noci žije na záložce **Vývoj aplikací** (přestavba okna strategie-39).

