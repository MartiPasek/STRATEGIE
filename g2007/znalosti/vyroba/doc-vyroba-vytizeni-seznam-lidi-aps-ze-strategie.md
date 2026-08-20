# Seznam lidi pro planovani vyroby (APS) uz pochazi ze STRATEGIE, ne ze skupiny 31 Centraly (DOKONCENO 11.8.2026)

> oblast: `vyroba` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Zadani (Jirka 10.8.2026, upresneno 11.8.2026)
Seznam lidi planovanych ve vytizeni vyroby (APS, Dusanuv Excel) ma prestat pochazet ze skupiny 31 Centraly a ma vznikat z nasi HR evidence funkci. Jen aktivni lide.
Upresneni Jirky 11.8. - "nechci, aby se ze STRATEGIE neco menilo v Centrale a Excel aby koukal zase do Centraly, chci aby bral seznam ze STRATEGIE stejne jako absence".
Schvalila Marti-AI (msg 12460, 12481 varianta A, 12496, 12499).

## Jak to funguje (overeno rozborem VBA sesitu v162)
Sesit ma JEDINE pripojeni SQLOLEDB na EC server a cte vyhradne view dbo.ECv_Vytizeni_*. Do PostgreSQL nedosahne, jinam nez do te jedne databaze se nepodiva. Nase data proto lezi v NASICH vlastnich tabulkach st.* v DB_EC a view jsou namirena na ne. Do dat Centraly se nezapisuje nic. Stejny princip uz drive u absenci.

## Stav - HOTOVO A OVERENO
1. tenant.org_post.je_vytizeni zapnuty u sesti funkci - 28 ELEKTROMONTER, 25 ZAMECNIK, 26 PRIPRAVA VYROBY, 29 VYPOMOC VE VYROBE, 122 KONSTRUKTER PERFOREX, 27 SEFMONTER.
2. Prenos posila priznak do st.EC_Vytizeni_PartySTRATEGIE.JeVytizeni.
3. ECv_Vytizeni_SeznamLidiNepritomnost prepnut na st.EC_Vytizeni_LideSTRATEGIE (Aktivni=1) + EXISTS na PartySTRATEGIE (JeVytizeni=1). Vysledek 34 lidi vcetne Havlata.
4. ECv_Vytizeni_SeznamNepritomnost prepnut stejne. Havlatovi se nove ukazuje 6 dnu absence v pristich 30 dnech (driv nula) - tim mizi stary rozpor, kdy byl videt v seznamu, ale bez dovolenych.
5. EC_Vytizeni_GenerujEfektivity - temp #Zam prepsan (25939 -> 7292 znaku). Generator spusten naostro, lidi v planu 37 -> 38, radku 978 -> 1037, cely prirustek je Havlat (59 radku), nikdo neubyl.
6. Zalohy vsech definic v st.EC_Vytizeni_RollbackDefinice, pred zmenou overena binarni shoda s aktualnim stavem.

## NALEZ, KTERY ZMENIL NAVRH - zastupne polozky se nesmi smazat
Ve skupine 31 nejsou jen lide. 11005 Skupina Zkusebna (669 radku v planu), 11010 Skupina Priprava vyroby (1934 radku) a 12001 Predikce dovolenych maji radek v EC_Vytizeni_Efektivita a jsou VYHRADNE ve skupine 31. Zaverecny DELETE v generatoru maze vse, co neni v #Zam - prosta nahrada by je smazala i s naplanovanymi hodinami.
Pravidlo, ktere to resi - clovek se bere ze STRATEGIE, polozka, kterou nase evidence lidi VUBEC NEZNA, zustava z Centraly. Overeno, ze takovych je presne pet a vsechny jsou neosobni (5000 Dilna, 11002 Skupina Dilna, 11005, 11010, 12001). Vsech 35 odeslych ze skupiny 31 nase evidence zna s Aktivni=0, takze se nevraceji. Skupina 30 (vypomoc) zustava cela beze zmeny.

## Obrazovka pro spravu priznaku (11.8.2026)
Puvodne schvalena nova stranka v g2007.soubor byla ZAMITNUTA po zjisteni, ze obe Organizacni struktury v ERP jsou ramcove gridy nad fw.data_set (system_new.hr_org_struktura_list id 81, vyroba.dusan_org_struktura_list id 140), ne stary hardcode. Nova stranka by vytvorila druhe misto se stejnymi daty.
Jirka rozhodl, ze to je vec vedouciho vyroby, ne personalistky - proto na Dusanove vyrobnim gridu. Hotovo -
- sloupec PlanVytizeni_APS v gridu (alias nad p.je_vytizeni, zobrazuje se jako zaskrtavatko),
- edit jadro vyroba.dusan_org_post_edit (core 227) - pole Funkce (readonly), zaskrtavatko Planuje se ve vytizeni (APS) a vnoreny grid Lide v teto funkci,
- data_source vyroba.dusan_org_post_lide se select-detail operaci,
- prava resi viditelnost uzlu (fw.menu_node.visibility_user_ids), Dusanova vetev Vyroba uz je takto scoped. Jirkuv navrh, Marti-AI ho posoudila jako spravny.
Technicke pasti pri stavbe - viz system-strategie / fw-gotchy-edit-jadro-a-vnoreny-grid.

## Ulozeni vyzadovalo zmenu schematu
Ramec pri ulozeni pres formular pise i updated_by_id a updated_by_text. tenant.org_post je nemela, ulozeni koncilo HTTP 500 (fw.diag_log 331765). Marti-AI schvalila jejich pridani (msg 12499) - neni to vyjimka, je to konvence ramce. Overeno zapisem tam i zpet, audit se plni.

## Jen aktivni lide (Jirka 11.8.)
Grid i vnoreny seznam filtruji pres public.user_tenants.membership_status IN (active, invited), tedy STEJNYM pravidlem jako prenos. Tim jsou obe mista konzistentni. Dopad - ELEKTROMONTER 31 -> 29, VAZAC 21 -> 20, ZAMECNIK 4 -> 2, SEFMONTER 1 -> 0 (zastupny zaznam).

## NALEZY mimo zadani - NEOPRAVOVAT bez Martiho
1. V EC_Vytizeni_GenerujEfektivity se priznak Vypomoc nastavuje podle skupiny 24 (Vedouci), puvodni zakomentovana verze pouzivala post 29 Vypomoc ve vyrobe. Preklep z 3.10.2023.
2. Navic je ten vypocet MAX(IIF(S.ID = 24,1,0)) uvnitr WHERE IDSkupiny IN (30,31), takze nikdy nemuze vyjit - priznak je vzdy 0, fakticky mrtvy.
Jirka 11.8. rozhodl nechat oboji beze zmeny.

## Kde overit
tenant.org_post (je_vytizeni) · st.EC_Vytizeni_PartySTRATEGIE (JeVytizeni) · st.EC_Vytizeni_LideSTRATEGIE (Aktivni) · prehled 7630 skupina 31 (stary zdroj) · EC_Vytizeni_Efektivita · g2007.python kod sync_absence_to_ec_vytizeni · fw.mirror_job klic sync_vytizeni_absence (180 min) · st.EC_Vytizeni_RollbackDefinice · predavka na plose Jirky ve slozce Plan absenci.

