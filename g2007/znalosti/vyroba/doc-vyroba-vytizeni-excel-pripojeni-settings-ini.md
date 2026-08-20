# Dusanuv sesit Planovani vytizeni - jak se pripojuje k SQL a proc kopie hlasi nejsem pripojen (11.8.2026)

> oblast: `vyroba` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Priznak
Kopie sesitu Planovani vytizeni otevrena mimo puvodni slozku hlasi, ze neni pripojena k SQL, a nenacte data.

## Pricina (overeno dekompilaci VBA, modul basG, procedura FillDbConnection)
Sesit si pripojovaci udaje nenese v sobe, cte je ze souboru Settings.ini VEDLE SESITU (ThisWorkbook.Path & "\Settings.ini"). Kdyz tam soubor neni, zkusi slozku doplnku Intersoft.xlam, a kdyz ani ten neni otevreny, pouzije natvrdo zadrátovane ZALOZNI hodnoty.

## Tvar souboru
Sekce [DB], ctyri klice - DataSource, Catalog, UserID, Password.
Pro ostrou Centralu - DataSource = 192.168.30.11,1433 a Catalog = DB_EC. Overeno dotazem na spoj (server EC-SERVER2\SQLEXPRESS2017, MachineName EC-SERVER2, local_net_address 192.168.30.11, port 1433, DB_NAME DB_EC).
POZOR - zalozni hodnoty v kodu ukazuji na TESTOVACI databazi (192.168.99.15,1433 / TestVytizeni_V2). Bez spravneho ini tedy sesit muze tise zobrazovat testovaci data misto ostrych.
Heslo do souboru vyplnuje clovek, AI ho nezadava ani nezobrazuje.

## Druha vec, na kterou pozor
Radek ReadOnly = (InStr(ThisWorkbook.Path, "ZZAK_APS") = 0) je v teto verzi ZAKOMENTOVANY. Ochrana proti zapisu z kopie tedy NEPLATI - tlacitka Aktualizovat a Do planu zapisuji do OSTRE Centraly i z kopie na plose. Pri prohlizeni se nic nedeje, ale klikat se ma jen zamerne.

## Pripojeni
connStr = Provider=SQLOLEDB;Data Source=<DataSource>;Network Library=DBMSSOCN;Initial Catalog=<Catalog>;User ID=<UserID>;Password=<Password>
Sesit cte view dbo.ECv_Vytizeni_* a zapisuje pres procedury dbo.EC_Vytizeni_*. Zadne jine spojeni nema - proto vsechna data ze STRATEGIE musi byt fyzicky v DB_EC v nasich tabulkach st.*.

## Gotcha k hledani
Slozka s puvodnim sesitem (cesta obsahujici ZZAK_APS) NENI na sdilenych discich serveru 192.168.30.11 (proslo Data, Helios, install, Smernice, perforex, pdf2xl). Bude na jinem stroji nebo primo u Dusana. Nazev Settings.ini se navic pouziva i pro ERP Centrala, takze hledani podle nazvu souboru vraci nesouvisejici vysledky - hledej sesit, ne ini.

