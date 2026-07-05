# F1 — Návrh finálního stromu ZZ_Marti-AI RO + triáž (Claude-27, 5. 7. 2026)

**Stav:** čeká na odsouhlasení Marti/Mísa. Připraveno po F0 inventuře (RO 1 736 souborů, RW 47, `public.documents` 2 046 / z toho 1 278 bez projektu → po dedupu **115 unikátních business dokumentů**).

## Navržený strom RO
```
ZZ_Marti-AI RO\
  BOZP_PO\              (JIŽ EXISTUJE — ponechat)
  Personalistika\       (sjednotit se stávající Personalistika_NEW)
  Prezentace_IT\        (JIŽ EXISTUJE — ponechat)
  ISO_TISAX\            (politiky DOC-xx, SoA, VDA ISA, dokumenty projektu 5)
  Ceniky\               (dodavatelské + vlastní ceníky; z RW)
  Smlouvy\              (rámcové, licenční, pronájem serveru ES<->ST, NDA)
  Obchod_CRM\           (nabídky, prezentace, limit listy, CRM standardy)
  Vyroba\               (kusovníky, PCN, nedokončená výroba, výrobní standardy)
  Ekonomika_Ucetnictvi\ (účetní osnova, podklady fakturace, přefakturace, ISDOC archiv)
  STRATEGIE_dokumentace\ (architektura, module registry, přehledy, Marti-AI popisy)
  _ARCHIV\              (staré verze, duplicity ke sloučení)
```

## Triáž 115 business dokumentů → cílové složky

**ISO_TISAX:** Business_Ethics_Directive_EUROSOFT + Richtlinie_Geschaeftsethik + Smernice_obchodni_etiky (3 jazykové verze), DOC-01_Rozsah_ISMS, Misa_vize_ISO_TISAX, TISAX_pravidelne_kontroly_v1.xlsx.

**Personalistika:** EC_Pracovni_smlouva_elektromonter/vedouci_projektu (+ verze v „Pracovně právní dokumenty"), Popisy_pracovnich_mist_EUROSOFT_v1, EC_Popis pracovního místa_elektromonter, Kategorizace_elektromonteru_v1 + Kategorizace_VP_v1, EC_FinPriplatkySrazkyDefinice_dokumentace, činnost logistika_10_2025, Narok D DN SD stav.

**Smlouvy:** Brokerage_contract_final_draft, koncept_Licenční smlouva s EC, Vypoved_licencni_smlouvy_Tool_Excel_INTERSOFT, Prohlaseni_o_duvernosti_dodavatele_V7, Prohlaseni_o_duvernosti_Zahradnik_Dusan, pronájmy (MP2015_F260xx_EC_Pronajem / 2026xxx_Pronajem xls).

**Obchod_CRM:** EUROSOFT - Control - Prezentace výběrového řízení.pptx, EUROSOFT_prezentace_navrh, Prezentace_digitalizace_VP_STRATEGIE, CRM kontakt / CRM_kontakt_upraveny, EUROSOFT - Control limit list (xlsx + xls).

**Ceniky:** Ceník měděných přípojnic DPL, Ceník zemnících pásků DPL, Ceník 2026-03 (+ 18 dodavatelských z RW).

**Vyroba:** *_KUSOVNIK_* (FLEX 4/7,5/15 kW), nove zalozene dily 9.-15.6., PCN_PBE240130, Nedokončená výroba 2024 (obě verze → nejnovější do Vyroba, starší _ARCHIV).

**Ekonomika_Ucetnictvi:** NAVRH_Cista_ucetni_osnova_2027, Podklady_pro_fakturaci_v1, Upominani_nezaplacenych_faktur (šablona), uspory_dani (nejnovější), Přefakturace ES_4_2026 + Rozpad_prefakturace_ES_5-2026, 121 000 EC_NV_2025, FPD_cerven_2026. ISDOC/ISDOCX faktury (~20) → `Ekonomika_Ucetnictvi\Faktury_ISDOC\` archiv.

**STRATEGIE_dokumentace:** centrala_erp_framework.md, module_registry.md, blueprint_forms_v1.xlsx, Marti-AI_co-umim/Co-umim (nejnovější), EUROSOFT_STRATEGIE_prehled_2026.pdf (z RW).

## VYŘAZENO z RO (šum / artefakty) — zůstává v DB/sandboxu
CLAUDE_SQL.sql, CLAUDE_GO.txt, ping.txt, test.txt, test_priloha.md, mobile.html, manifest.json, Intersoft.xlam, interní Claude/dev poznámky (_NASAZENI_banner_datovky, dopis_marti_ai_*, fix_import_*, google_play_jirka_navod, zadani_marti_ai_*, zprava_pro_Claude23), „Kopie -" duplicity, Souhrn_vikend, Rozvrh_AI_vysvetleni_Klarka (škola), ~500 inline obrázků z mailů, 25 generátorových .py skriptů.

## CITLIVÉ — do RO NEPATŘÍ (jen sandbox/trezor, řešit s Petrou/Mísou)
MZDY_EUROSOFT CONTROL/SYSTEM xlsm (mzdy jednotlivců), OČR Mudra + OCR_Nina_Marešová (péče o dítě = osobní), Finalni_smlouva_o_podilovem_spoluvlastnictvi_Safrankova (osobní), Trestni oznameni na neznameho pachatele (právní/citlivé), Přesčasy + Přesčasy_V2 (osobní odpracované — hraniční).

## Otázky k odsouhlasení (Marti/Mísa)
1. Sedí strom (11 složek výše)? Přejmenovat `Personalistika_NEW` → `Personalistika`?
2. ISDOC faktury: chceme je v RO archivu, nebo jen v účetním modulu (nepatří do „klíčových lidských dokumentů")?
3. Citlivé (mzdy/OČR/trestní oznámení) — potvrdit, že do RO NEjdou.

— Claude-27 (CMS), 5. 7. 2026
