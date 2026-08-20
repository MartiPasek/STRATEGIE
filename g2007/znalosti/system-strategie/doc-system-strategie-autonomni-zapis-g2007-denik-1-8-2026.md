# Doktrina "konstruktivni operace autonomne" rozsirena o g2007.denik (1.8.2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

Marti 21.7.2026 zavedl doktrinu pro @@G2007ADD: "konstruktivni operace musi jet autonomne,
updaty taky; jen mazani se schvaluje." Marti 31.7.2026 ji rozsiril na INSERT/UPDATE do
g2007.python jako celek (cil: migrace router.py -> g2007.python, Cesta B).

Marti 1.8.2026 vyslovne potvrdil rozsireni te same doktriny na novou tabulku g2007.denik
(provozni denik vsech Claude instanci + MartiAI - kdo, na jakem vlaknu, kdo to spustil, co
resi, co vyresil, ktere soubory/g2007 kody se toho tykaji, pripadny git commit sha). Duvod:
denik ma smysl jen pokud je zapis plynuly a bez treni - kdyby kazdy INSERT cekal na banner,
byl by denik deravy prave tam, kde ma byt nejspolehlivejsi (napr. zapisy MartiAI/watcheru
mimo Martiho pozornost).

Obecny cil, ktereho se to tyka: bezpecna autonomie zalozena na vratnych, auditovatelnych
zapisech. g2007.python a g2007.denik jsou obe operacni metadata, ktera si system pise sam
o sobe (kod jako data / kdo-co-kdy dela) - nejde o business-kriticka data (mzdy, fakturace,
docházka zamestnancu), a kazdy zapis je dohledatelny (verze/archiv u g2007.python, radek
s timestampem u g2007.denik). Destruktivni nebo strukturalni operace (DELETE, TRUNCATE,
ALTER, DROP) na obou tabulkach zustavaji VZDY gated pres banner - to se timto nemeni.

Implementace: modules/erp/api/router.py, funkce diag_sql(), blok "G2007 KONSTRUKTIVNI
TABULKY" - _G2007_AUTONOMOUS_TABLES nyni obsahuje {"g2007.python", "g2007.denik"} misto
puvodniho singularniho _PY_TABLE = "g2007.python". Zmena je hotova a commitnuta lokalne
(git), ale CEKA NA DEPLOY - git push na GitHub aktualne selhava (HTTP 403 od proxy na
Martiho stroji), takze zatim bezi jen puvodni chovani (jen g2007.python autonomne,
g2007.denik zatim jeste pres banner). Az push pujde, nasadi se spolu s pripravovanou
dlazdici "Denik" ve Firma -> Vedeni (admin-gated prehled g2007.denik s rozklikavanim).

