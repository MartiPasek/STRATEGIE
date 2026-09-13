# Grid ERP - tecka v aliasu sloupce = prazdna bunka (AG Grid dot notation)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)


**Priznak.** Sloupec v gridu ma spravnou hlavicku, ale vsechny bunky jsou prazdne - pritom data v databazi jsou. Sousedni sloupce se zobrazuji normalne. Typicky se to jevi jako "nesynchronizovana data" nebo "nesedi to s jadrem", ale s daty to nesouvisi vubec.

**Root cause (overeno v kodu 10.9.2026, C24).** `apps/api/static/erp/datagrid.js`, funkce `buildAutoColumnDefs` (r. 535-545) stavi sloupce jako `field = presny alias ze SQL` a `headerName = tentyz alias`. AG Grid ale bere **tecku ve field jako cestu do vnoreneho objektu** - alias `Efekt. %` znamena pro AG Grid `radek["Efekt"][" %"]`, coz je undefined, tedy prazdna bunka. Vypnout to jde volbou `suppressFieldDotNotation` v gridOptions - ta se ale v celem repu nenastavuje nikde (grep = 0 vyskytu) a `valueGetter` se nepouziva taky nikde.

**Dusledek.** Prazdny zustane KAZDY sloupec, jehoz alias obsahuje tecku. Ne jen ten, na kterem si toho nekdo vsimne - je to plosne pres cele ERP.

**Zazito.** Modul Vyhodnoceni zakazek, grid "Hodnoceni vse" (dataset `ec.vyhodnoceni_jadro_osoba`): prazdne byly `Os. c.` a `Efekt. %` (a byla by i `Sefm.`), zatimco `Pracovnik`, `Hodin` a `Premie` - bez tecky - se zobrazovaly spravne. V datech pritom efektivita byla (14 035 radku ma 100). Kristy to hlasila jako "efektivita v gridu nesedi s jadrem, synchronizujeme s Centralou?".

**Reseni.** Doporucene = jednoradkove `suppressFieldDotNotation = true` v gridOptions v `datagrid.js` - opravi to plosne. Pozor, `datagrid.js` je sdilene jadro celeho ERP (270 KB) a sahaji do nej i dalsi instance, takze nasazovat po dohode, ne potichu. Zaplata na jednom miste = prejmenovat aliasy v datasetu tak, aby v nich nebyla tecka; opravi jeden grid a chyba zustane vsude jinde.

**Jak to poznat priste.** Kdyz nekdo hlasi prazdny sloupec v gridu, nejdriv se podivej, jestli ma alias tecku. Neztracej cas hledanim chyby v datech ani v synchronizaci zrcadel.

