# Zaloha pokryva POUZE databazi - 19 GB dokumentu a instalace peti sluzeb v ni nejsou (nalez 8. 9. 2026)

> oblast: `provoz` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Zaloha pokryva POUZE databazi - dokumenty a instalacni postupy v ni nejsou

Nalez z 8. 9. 2026 (Jiri Honomichl / Claude-28, schvalila Marti-AI msg 15098) pri uklidu
po oprave nocniho prenosu zaloh Praha - Plzen.

> ## OTEVRENY BOD, NE ZDOKUMENTOVANY ZAMER
> **Dokud neni zaloha dokumentu vyresena, plan obnovy pokryva POUZE databazi.**
> Neni to rozhodnuti - je to stav, o kterem vime a ktery ceka na rozhodnuti.
> Prvni bod nize navic **vyzaduje provereni Martim**.

## 1. Dokumenty (19 GB) lezi mimo zalohovany retez

`public.documents` ma **101 891 zaznamu**. Z toho **51 298 ma skutecne soubory
o objemu 19 GB** ve slozce `C:\Data\STRATEGIE\Dokumenty`.

**Ta slozka lezi na aplikacnim serveru 188.11**, ne na databazovem 188.12 - overeno
tim, ze `pg_stat_file` na databazovem serveru hlasi, ze neexistuje. Cely DR retez
(nocni dump na 188.12, push do Prahy, stazeni a obnova v Plzni) zalohuje **jen databazi**.
Zadny skript v repozitari tu slozku nezminuje.

**Riziko neni teoreticke.** **50 593 zaznamu zalozenych PRED 21. 8. 2026** ma dnes
velikost 0 a priznak `file_missing`. Vsechny mladsi zaznamy (od 21. 8.) soubory maji.
**Jestli slo o umyslny uklid nebo o ztratu, z databaze rozlisit nelze - potrebuje to
provereni Martim.**

Dokumenty ulozene **primo v databazi** (`tenant.employee_document`, `dodavatel_soubor`,
`hr_audit_soubor`, `org_tabule_soubor`) v zaloze **jsou** - je jich ale jen 24 a par MB.
Naopak `tenant.kb_smernice_soubor` (771 souboru, 962 MB) a `tenant.iso_document` (38)
drzi v databazi jen cestu, takze na tom jsou stejne jako `documents`.

## 2. Pet sluzeb nema instalacni postup

V repozitari je deset instalacnich skriptu, ale tyhle sluzby nemaji **zadny**:

- **STRATEGIE-API** (hlavni aplikace)
- **STRATEGIE-CADDY** (brana)
- **STRATEGIE-TASK-WORKER**
- **STRATEGIE-EMAIL-FETCHER**
- **STRATEGIE-RESTART-WATCHER**

Kdyby se aplikacni server stavel znovu, tyhle by se musely poskladat rucne z hlavy.
Skript maji naopak STRATEGIE-API-B (`install_strategie_api_b*.ps1`), STRATEGIE-CLAUDE-SQL
(`setup_claude_instance.ps1`), STRATEGIE-APID-WATCHER (`setup_apid_watcher_service.ps1`),
EUROSOFT-MCP (`install_eurosoft_mcp_on_ec_server2.ps1`), API-D (`setup_api_d.ps1`)
a most na cloudu (`install_claude_bridge_nssm.ps1`).

## 3. Past pri diagnostice - volba starsi verze vede na TESTOVACI data

Brana ma porad pravidla pro cookie `strategie_api_version=older_1` a `older_2`.
`older_1` posila na port **8004, kde dnes bezi APID testovaci prostredi nad `data_db_test`**;
`older_2` (8005) neodpovida a spadne na produkci.

**Bezneho uzivatele to neohrozi** - cookie ma platnost 24 hodin a aplikace starsi verze
vubec nenabizi (`is_active=false`), takze si ji nikdo neklikne. **Past je pri diagnostice**,
kdy si instance cookie nastavi rucne, aby se podivala na zalozni verzi - pak muze necekane
skoncit nad testovacimi daty a myslet si, ze cte produkci. **Vzdy si over `/api/v1/api-info`,
ktere hlasi `db` a `env`.** Zvazit zruseni obou pravidel v Caddy.

