# 🧩 Podpůrné procesy — kvalita, HR, finance, BOZP, IT (řada přístupnost AI)

> **Autor: Claude (ID23), 1. 7. 2026.** Deep-dive podpůrných domén z `MAPA_smernic.md` (vše mimo
> jádro výroby rozvaděčů). Orientace pro Claude + Marti-AI; hloubka se doplňuje čtením příloh přes
> `@@KB <dotaz> | 3`. Zdroj pravdy = oficiální směrnice v RAG.

## 02 — Kvalita a zkoušky (8+ směrnic)
- **Zkoušky rozvaděče dle EN 61439-2:** izolační zkouška (protokol), zkouška ochranného vodiče
  (protokol), **deník zkoušek / hlášení o chybách**, prohlášení o shodě + prohlášení výrobce.
  Odeslání měřicích/zkušebních protokolů je součást STANDARDu (výstup výroby).
- **Reklamace a neshody:** *„Veškeré reklamace, návrhy, neshody a připomínky musí být evidovány
  v IS Centrála v záložce Interní."* Samostatně **reklamace poškozených dílů na zakázkách**
  (u nás před odesláním i u zákazníka). → řízené zaznamenávání neshod.
- **Normy:** odkazy na ČSN (např. úprava písemností). Vazba na ISO 9001 (kvalita) — viz ISO cockpit.

## 03 — Personalistika a HR (24 směrnic)
Mzdy, **docházka** (přehled plánovaného volna), dovolená, nástup/výstup zaměstnance, pracovní poměr,
cestovní náhrady, stravné, odměňování. → napojení na STRATEGIE HR modul (att_*, mzdy cloud, benefity
OBL/HO), který jsme stavěli. Směrnice = pravidla; náš modul = exekuce a evidence.

## 04 — Finance, clo a DPH (39 směrnic) — silně exportní firma
- **Clo:** kódy osvobození zboží od dovozního cla (celní režim volného oběhu), celní prohlášení.
- **DPH v EU:** pravidla uplatňování DPH při obchodu a službách v EU (export do DE/US!) — zdroj BIC
  (poradce v oblasti cel a unie). Reverse-charge, intrakomunitární plnění.
- **Fakturace, ceny, pokladna.** → napojení na účetní engine STRATEGIE (deník, předkontace, banka).
- Postřeh: protože 80 %+ produkce jde na export (DE), **clo/DPH je netriviální doména** — směrnice
  drží pravidla, která se musí promítnout do fakturace a účtování.

## 05 — BOZP a PO (18 směrnic)
Bezpečnost práce, požární ochrana, první pomoc, OOPP (ochranné pomůcky), evidence úrazů, školení
BOZP/PO. Náročné na evidenci a periodická školení (vazba na doménu 09 Školení). → compliance jádro
vedle ISO/TISAX.

## 07 — Nákup a sklad (11 směrnic)
Objednávání materiálu (per kusovník), sklad, dodavatelé (Rittal, Siemens, Rockwell, Schrack, Phoenix,
Weidmüller, Legrand, Murr), zásoby, **kontrola a objednávání VKM materiálu** (spojovací materiál).
→ napojení na kalkulaci (SRDCE FIRMY) a dostupnost skladem (`ec_stav_skladu`).

## 11 — IT a bezpečnost (2+ ve výrobě, širší v „ostatní")
Software, data, GDPR, hesla, zálohování, **ISO 27001 / kybernetická bezpečnost** — vazba na
elektronický ISO cockpit (`/iso`, `docs/iso27001_*`). Řada IT směrnic je v koši „Ostatní" (nápovědy
k systémům) — k dotřídění.

## 06 Ekologie a odpady (3) · 08 Doprava a expedice (2) · 09 Školení a kvalifikace (6)
- **Ekologie:** nakládání s odpady, likvidace, životní prostředí (ISO 14001 vazba).
- **Doprava/expedice:** odvoz rozvaděčů, balení (UPS/přepravce), termíny (centrála – informace
  o termínech a dopravě).
- **Školení/kvalifikace:** kvalifikační zkoušky, oprávnění, periodická školení (BOZP/PO, jeřáb,
  VZV, elektro §…). Vazba na HR (evidence platnosti).

## 12 — Ostatní a administrativa (259) — frontier k dotřídění
102 formulářů (šablony) + 98 obecných směrnic + 60 nápověd (systémy) + 37 informací. **TODO:**
rozklíčovat na organizaci/řízení (jednací řády, směrnice o směrnicích), IT nápovědy, komunikaci,
a přeřadit do domén 1–11. To je poslední krok „úplného pořádku".

## Postřehy (živé)
- **Vše se sbíhá do IS Centrála** (reklamace, evidence) — legacy systém, který STRATEGIE nahrazuje.
  RAG směrnic + naše moduly = přechod od „pravidlo v dokumentu" k „pravidlo vykonané v systému".
- **Compliance trojice:** kvalita (ISO 9001) + BOZP/PO + IT (ISO 27001/TISAX) + ekologie (ISO 14001)
  — směrnice jsou důkazní základ pro audity (napojení na ISO cockpit).
- **Další krok indexování:** dotřídit koš „Ostatní 259", dočíst přílohy kvality (EN 61439-2 checklist
  jako samostatná AI směrnice `Kvalita_zkousky.md`) a HR/finance detail.

— Claude (ID23) 🧩📚
