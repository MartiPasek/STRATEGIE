# Projekt: Finanční podmínky zaměstnanců — kontext a zadání

> Překlopení kontextu pro samostatný projekt (Šárka, 9. 7. 2026). Vlož jako instrukce/knowledge
> nového projektu „Finanční podmínky". Bez konkrétních jmen a čísel — téma je citlivé.

## Účel
Vést a upravovat **finanční podmínky zaměstnanců** (OSVČ / HPP / DPP) ve STRATEGII: editace
personalistkou, kategorizace dle popisu práce, přehled v kartě zaměstnance, podpora onboardingu
a příprava na novelu o transparentnosti odměňování.

## Kdo a přístup
- **Šárka** (personalistka) — vede a upravuje.
- **Citlivost = maximální.** Vidí/edituje jen **8 lidí**: skupina HR (Marti, Kristý, Petra Šafránková,
  Šárka) + rozšíření dohodou = celkem 8, včetně Marti Pašek. Nikdo jiný (ani ostatní rodiče/vedení).
- Zaměstnanec vidí jen sebe (mimo finanční podmínky).

## Zásadní pravidla (držet!)
1. **V Centrále je ZÁKAZ editace** → Centrála = zamrzlá historie, **STRATEGIE = jediné živé místo úprav**.
2. **Neduplikovat data** — finanční data jsou už migrovaná do STRATEGIE (finance v2), pracujeme nad nimi,
   nezakládáme druhou kopii.
3. **Audit vždy** — u každé změny se drží `kdo` a `kdy` (changed_by / changed_at).
4. **CI + grafika** = stejné jako ERP / Marti-AI (tmavé schéma).

## Kde to žije technicky (STRATEGIE)
- Editovatelná dlaždice **„💰 Finanční podmínky"** — ERP strom, uzel **181**, `core=hr.finance`,
  přístup restricted na 8 uid. Stránka `/finance-podminky` (iframe), i v mobilní appce.
- Backend: `modules/erp/api/router.py` — endpointy `/app/hr/finance/{lide,osoba,slozky-typy,
  slozka-save,slozka-smazat}`, gate `_finance_can_uid` (allowlist 8), audit `changed_by_text/at`.
- Data: `tenant.engagement` (poměry) + `tenant.wage_component` (mzdové složky, 31 typů) — migrace
  z EC_FinZamPodminky (finance v2). Stav: ~84 poměrů / ~2636 složek / ~77 lidí.
- Martiho read-only „Finance lidí" (uzel **105**, jen rodiče) — **čeká na Martiho rozhodnutí**, zda
  zrušit a nechat jen 181 (dotázán 9. 7. na mobil).

## Struktura finanční podmínky (bloky dle Centrály)
Obecné · Počet hodin · Peníze · Volno · Prémie · Poznámka · Požadovaný plat v čase.
**Detailní pole a rozdíly dle druhu smlouvy → `docs/hr_financni_podminky_kategorizace.md`.**

## Kategorizace (matice druh × segment)
OSVČ výroba · OSVČ kancelář · OSVČ PLC programátoři (režie Mirka) · HPP výroba · HPP kancelář ·
DPP krátkodobě · *(budoucí: management / garant …)*.
Model: **finanční podmínka = kategorie (profil polí + mzdové pásmo) + individuální hodnoty.**

## Hotové vs. otevřené
**Hotové:** editovatelná dlaždice (poměry read + mzdové složky edit/přidat/smazat), audit u složky,
seznam lidí, zámek na 8.

**Otevřené / gapy:**
1. **PLC programátoři (OSVČ, režie Mirka)** — sazby dnes vidí jen Mirek, v systému nejsou → doplnit
   (zdroj dat teprve zjistit: Excel / režie v Centrále / jinde).
2. **Cizí měna (EUR)** — někteří OSVČ počítáni v EUR + kurz → model musí umět měnu, ne jen Kč.
3. **Editace poměrů** (úvazek, smlouva, pozice) — teď jen čtení, doplnit editaci.
4. **Pole k doplnění**: sleva na dani, zdravotní pojišťovna, blok Volno, min/optimal/max hod, režie max,
   náborový poplatek, měna+kurz, Požadovaný plat v čase, přepínače.
5. **Poznámky** — volný text nese citlivá rozhodnutí a platová srovnání → strukturovat (kdo/kdy/proč).
6. **Kategorie + mzdová pásma** — navrhnout číselník kategorií a pásma (directive-ready).
7. **Karta zaměstnance** — přehled finanční podmínky přímo z karty.
8. **Onboarding** — „založ kartu → přiřaď kategorii → doplň domluvu".

## Novela o transparentnosti odměňování (kontext)
Návrh novely zákoníku práce (MPSV, 27. 3. 2026, „minimalistická transpozice"). Pův. účinnost většiny
od 1. 1. 2027, hlášení mzdových rozdílů od 1. 1. 2028. Dopady: pásma na kategorii dle popisu práce,
informační povinnost vůči uchazečům, zákaz vyžadovat mzdovou historii. (Věcný přehled, ne právní
stanovisko — právní finále na kompetentní osobě.)

## Pracovní styl
Šárka = personalistka, ne programátorka. Motivační, laskavý přístup. Změny nasazovat přes bridge,
citlivost hlídat. Detailní spec drž a aktualizuj v `docs/hr_financni_podminky_kategorizace.md`.
