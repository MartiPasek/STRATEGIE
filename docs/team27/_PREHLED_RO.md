# 📁 ZZ_Marti-AI RO — Přehled klíčových dokumentů

**Aktualizováno:** 5. 7. 2026 (Claude-27). Tato složka je pro lidi **jen ke čtení** (zapisuje Marti-AI / Claude). Klíčové firemní dokumenty jsou uspořádané po doménách níže.

## Struktura

**BOZP_PO/** — bezpečnost práce a požární ochrana (~1 736 souborů). Podsložky: `BOZP/` (bezpečnost práce), `PO/` (požární ochrana), `_ARCHIV_PO/` + `_ARCHIV_RW/` (starší verze), `_TEST/`.

**Prezentace_IT/** — IT prezentace (beze změny).

**ISO_TISAX/** — ISMS politiky a TISAX (6): směrnice obchodní etiky (CZ/DE/EN), DOC-01 Rozsah ISMS, vize ISO/TISAX (Mísa), pravidelné kontroly.

**Personalistika/** — HR (7): pracovní smlouvy (elektromontér, vedoucí projektu), popisy pracovních míst, kategorizace elektromontérů a VP, definice příplatků/srážek, činnost logistika.

**Smlouvy/** — smlouvy (5): brokerage contract, licenční smlouva s EC (koncept), výpověď licence Tool Excel INTERSOFT, prohlášení o důvěrnosti (dodavatel V7, Zahradník Dušan).

**Obchod_CRM/** — obchod (5): prezentace výběrového řízení, návrh prezentace EUROSOFT, prezentace digitalizace VP, CRM kontakt, limit list.

**Vyroba/** — výroba (5): kusovníky FLEX 4/7,5/15 kW, nově založené díly, nedokončená výroba 2024.

**Ekonomika_Ucetnictvi/** — ekonomika (7): návrh čisté účetní osnovy 2027, podklady pro fakturaci, upomínání nezaplacených faktur (šablona), úspory daní (nové sazby), přefakturace ES 4+5/2026, nedokončená výroba EC_NV 2025.

**Ceniky/** — 20 ceníků: dodavatelské (Eaton, Finder, Harting, LAPP, MBS, Murr, PhoenixContact, Pilz, Rittal, Rockwell, Schneider, Siemens, SOCOMEC, WAGO, Weidmüller, Woehner + převodní tabulka) + vlastní (měděné přípojnice DPL, zemnící pásky DPL, Ceník 2026-03).

**STRATEGIE_dokumentace/** — dokumentace platformy (4): centrala ERP framework, module registry, Marti-AI co umím, EUROSOFT×STRATEGIE přehled 2026.

## Poznámky
- Celkem nově uspořádáno **59 klíčových business dokumentů** (5. 7. 2026) z DB STRATEGIE, které dosud nebyly přehledně v RO.
- Prázdná složka `Personalistika_NEW` (jen kostra bez souborů) sloučena do `Personalistika` a odstraněna (5. 7. 2026).
- **Nezařazeno záměrně** (šum): ~500 inline obrázků z mailů, generátorové .py skripty, dočasné/testovací soubory, duplicity.
- **Citlivé — do RO NEPATŘÍ** (jen sandbox/trezor): mzdy jednotlivců, OČR, trestní oznámení, osobní spoluvlastnictví. Řeší se s Petrou/Mísou.
- **TODO (blokováno na nástroj ID23):** sémantické zaindexování fyzických RO souborů do RAG + doembedování 33 TISAX dokumentů.
- **Úklid DB (připraveno pro ID23):** v `public.documents` je 571 duplicit + 10 `~$` temp souborů (~149 MB) — hotový skript `docs/team27/cleanup_documents_manifest_2026-07-05.md`.
