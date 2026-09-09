# Zaloha pokryva POUZE databazi - 19 GB dokumentu a instalace peti sluzeb v ni nejsou (nalez 8. 9. 2026)

> oblast: `provoz` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)

# Zaloha pokryva POUZE databazi - dokumenty a instalacni postupy v ni nejsou

Nalez z 8. 9. 2026 (Jiri Honomichl / Claude-28) pri uklidu po oprave nocniho prenosu zaloh Praha - Plzen.

> ## OTEVRENY BOD, NE ZDOKUMENTOVANY ZAMER
> **Dokud neni zaloha dokumentu vyresena, plan obnovy pokryva POUZE databazi.**
> Neni to rozhodnuti - je to stav, o kterem vime a ktery ceka na rozhodnuti.
> ⛔ **Veta "Prvni bod nize navic vyzaduje provereni Martim" UZ NEPLATI (opraveno 9. 9. 2026).**
> Duvod chybejicich souboru je znamy - viz bod 1.

## 1. Dokumenty (19 GB) lezi mimo zalohovany retez

`public.documents` ma **101 891 zaznamu**. Z toho **51 299 ma skutecne soubory o objemu 19 GB** ve slozce `C:\Data\STRATEGIE\Dokumenty`.

**Ta slozka lezi na aplikacnim serveru 188.11**, ne na databazovem 188.12 - overeno tim, ze `pg_stat_file` na databazovem serveru hlasi, ze neexistuje. Cely DR retez (nocni dump na 188.12, push do Prahy, stazeni a obnova v Plzni) zalohuje **jen databazi**. Zadny skript v repozitari tu slozku nezminuje.

**50 593 zaznamu zalozenych PRED 21. 8. 2026** ma dnes velikost 0 a priznak `file_missing`. Vsechny mladsi zaznamy (od 21. 8.) soubory maji.

### Proc ty soubory chybi - ZODPOVEZENO (opraveno 9. 9. 2026)

⛔ **NEPLATI puvodni veta:** *"Jestli slo o umyslny uklid nebo o ztratu, z databaze rozlisit nelze - potrebuje to provereni Martim."*

**Byl to umyslny uklid.** Odpoved byla znama uz **6. 9. 2026** ve znalosti `doc-system-strategie-prilohy-z-posty-filtr-a-chybejici-soubory`: **Marti Pasek starsi prilohy kolem 21. 8. 2026 smazal SAM kvuli nedostatku mista.** Rez je podle poradi zaznamu (vse pod id 122892), overeno na kus - v databazi 51 084 zaznamu od id 122892 a ve slozce presne 51 084 souboru.

**Jak chyba vznikla:** nalez z 8. 9. vznikl bez porovnani s existujicimi znalostmi. Odpoved uz dva dny lezela zapsana a stacilo se na ni dotazat pres obsah vsech platnych znalosti. Proto se do teto znalosti dostal otevreny bod, ktery otevreny nebyl, a cekalo se na cloveka zbytecne.

### Co v tech 19 GB doopravdy je (zmereno 9. 9. 2026)

Jsou to **prilohy z firemni posty**. Objem je z drtive vetsiny opakovani tehoz souboru:

| skupina | souboru | na disku | **ruzny obsah** |
|---|---|---|---|
| obrazky (loga z paticek) | 39 509 | 5 708 MB | **169 MB** |
| dokumenty (pdf, office) | 11 790 | 13 GB | **662 MB** |
| **celkem** | **51 299** | **19 GB** | **831 MB** |

Tech 51 299 souboru ma jen **1 326 ruznych obsahu**. `image001.png` je ulozen 3 795x, jedna prezentace 3 777x - jeden mail na sto lidi se ulozi stokrat.

⚠️ **Vyhrada:** "ruzny obsah" je pocitany podle dvojice nazev + velikost, **ne podle otisku souboru**. U podpisovych obrazku a hromadne posty je to spolehlive, ale neni to dukaz do posledniho souboru. **Presny otisk se merit neplanuje** - pro rozhodnuti o zaloze staci rad velikosti.

### Zalohovat, ale deduplikovane a az na spravnou linku

Zalohovat se ma **skutecny obsah (831 MB), ne syrovych 19 GB**. Nejdriv je ale nutne overit, ze nocni prenos objem navic vubec unese: 9. 9. 2026 nedojela ani samotna databaze (3 921 MB) - stahovani drzelo **~200 kB/s** a spadlo na vsechny tri pokusy. Pridavat gigabajty na linku, ktera neuveze soucasny objem, nema smysl. Viz `doc-system-strategie-dr-prenos-praha-plzen-pricina-a-oprava-2026-09-08`.

### Co je naopak v poradku

Dokumenty ulozene **primo v databazi** (`tenant.employee_document`, `dodavatel_soubor`, `hr_audit_soubor`, `org_tabule_soubor`) v zaloze **jsou**. Naopak `tenant.kb_smernice_soubor` (771 souboru, 962 MB) a `tenant.iso_document` (38) drzi v databazi jen cestu.

Na slozce `Dokumenty` **nestoji zadna funkce systemu** - overeno 9. 9. 2026 na vazbach: `mod.hr_document` 0 vazeb, `tenant.contract_sign` 7 (a ty na tyto dokumenty neukazuji), `tenant.att_ocr_file` 3. Riziko tedy neni "prijdeme o system", ale "prijdeme o postu, kterou zpetne nedohledame".

## 2. Pet sluzeb nemelo instalacni postup - DOPLNENO 9. 9. 2026

> **VYRESENO** (Jirka Honomichl). Skripty jsou v `scripts/install/` (commit `cdbdb56c`),
> nastaveni je **opsane ze skutecne bezicich sluzeb** na 188.11 (cteno z registru,
> ne vymyslene). Jsou **opakovatelne** - kdyz sluzba existuje, jen srovnaji nastaveni.
> **Tajemstvi v nich NEJSOU** a nesmi byt - predavaji se parametrem `-Promenne`;
> pri vynechani zustanou uz nastavene promenne beze zmeny. Rozcestnik ve stejne slozce
> v `README.md`. Puvodni stav popsany nize UZ NEPLATI.

V repozitari je deset instalacnich skriptu, ale tyhle sluzby nemaji **zadny**:

- **STRATEGIE-API** (hlavni aplikace)
- **STRATEGIE-CADDY** (brana)
- **STRATEGIE-TASK-WORKER**
- **STRATEGIE-EMAIL-FETCHER**
- **STRATEGIE-RESTART-WATCHER**

Kdyby se aplikacni server stavel znovu, tyhle by se musely poskladat rucne z hlavy. Skript maji naopak STRATEGIE-API-B (`install_strategie_api_b*.ps1`), STRATEGIE-CLAUDE-SQL (`setup_claude_instance.ps1`), STRATEGIE-APID-WATCHER (`setup_apid_watcher_service.ps1`), EUROSOFT-MCP (`install_eurosoft_mcp_on_ec_server2.ps1`), API-D (`setup_api_d.ps1`) a most na cloudu (`install_claude_bridge_nssm.ps1`).

## 3. Past pri diagnostice - volba starsi verze vede na TESTOVACI data

Brana ma porad pravidla pro cookie `strategie_api_version=older_1` a `older_2`. `older_1` posila na port **8004, kde dnes bezi APID testovaci prostredi nad `data_db_test`**; `older_2` (8005) neodpovida a spadne na produkci.

**Bezneho uzivatele to neohrozi** - cookie ma platnost 24 hodin a aplikace starsi verze vubec nenabizi (`is_active=false`), takze si ji nikdo neklikne. **Past je pri diagnostice**, kdy si instance cookie nastavi rucne, aby se podivala na zalozni verzi - pak muze necekane skoncit nad testovacimi daty a myslet si, ze cte produkci. **Vzdy si over `/api/v1/api-info`, ktere hlasi `db` a `env`.** Zvazit zruseni obou pravidel v Caddy.

