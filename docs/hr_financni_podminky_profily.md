# Finanční podmínky — předvyplněné profily podle druhu (OSVČ / HPP / DPP)

> Claude-25 (za Šárku), 9. 7. 2026. Kontrola proti reálným printscreenům z projektu „HR přehled"
> (vzorky: OSVČ Voříšek/Saad/Benetka, HPP Diviš/Hladíková, DPP Řeháková) + hodnoty ze
> `podminky_skupin_zamestnancu.md`. Slouží jako **předvyplnění při zakládání karty** — vybereš druh,
> předvyplní se relevantní pole a defaulty, ty doladíš individuální domluvu. Bez konkrétních jmen a čísel.

## Kontrola úplnosti — na nic jsme nezapomněli ✅

Všechna pole z karet Centrály už model pokrývá:
- **Zdravotní pojišťovna** + **Sleva na dani** — na kartách jen HPP/DPP → v modelu `zdrav_pojistovna_code`, `sleva_na_dani` (Gap 3). ✅
- **Placen od hodiny** — OSVČ ano / HPP ne → `placen_od_hodiny` (Gap 3). ✅
- **Min / optimal / max hodin**, **režie max** — HPP výroba i OSVČ výroba → `hod_min/optimal/max`, `rezie_max` (Gap 3). ✅
- **Cizí měna + kurz** — Benetka 30 EUR/hod → `currency`, `fx_rate`, `fx_date` (Gap 2). ✅
- **Náborový poplatek**, **neplacený přesčas**, přepínače (srážet neodpracované, uplatnit slevy 1. měsíc, dopočet zk. doby), **platnost výměru od** → Gap 3. ✅
- Bloky Peníze / Prémie / Volno / Poznámka / Požadovaný plat v čase → složky, entitlements, poznámky, target salary. ✅

Jediná skutečná díra zůstává **OSVČ PLC (režie Mirka)** — sazby dnes vidí jen Mirek, v systému nejsou.
Není to chybějící pole, je to chybějící data → nejdřív zjistit zdroj (Excel / režie v Centrále).

---

## Matice: která pole se vyplňují podle druhu

Legenda: ✅ = vyplnit · — = nevyplňovat (nerelevantní) · ⚙ = dle domluvy

| Pole | OSVČ výroba | OSVČ kancelář | OSVČ PLC | HPP výroba | HPP kancelář | DPP krátkodobě |
|---|---|---|---|---|---|---|
| Zdravotní pojišťovna | — | — | — | ✅ | ✅ | ✅ |
| Sleva na dani | — | — | — | ✅ | ✅ | ⚙ |
| Placen od hodiny | ✅ ano | ⚙ | ✅ ano | ne | ne | ✅ ano |
| Základ | za hodinu | měsíční | za hodinu | měsíční | měsíční | za hodinu |
| Min / optimal / max hodin | ✅ | — | ⚙ | ✅ | — | — |
| Režie max | ⚙ | — | ✅ | — | — | — |
| Osobní ohodnocení | — | — | — | ✅ | ✅ | — |
| Volno + sick days | — | — | — | ✅ | ✅ (víc SD navíc) | — |
| Stravenkový paušál | — | — | — | ✅ | ✅ | — |
| Prémie | odměna jednatele | ⚙ | — | dle role | ⚙ | — |
| Náborový poplatek | ⚙ | ⚙ | ⚙ | ⚙ | ⚙ | — |
| Měna + kurz | ⚙ (i EUR) | ⚙ | ⚙ (i EUR) | CZK | CZK | CZK |
| Zkušební doba | — | — | — | ✅ 4 měs. | ✅ 4 měs. | — |

---

## Předvyplněné defaulty podle druhu

Hodnoty pocházejí z reálných podmínek (`podminky_skupin_zamestnancu.md`) a slouží jako **default kategorie**;
u konkrétního člověka se přepíšou individuální domluvou.

### OSVČ — výroba (vzor: Voříšek)
Dodavatelský vztah. Placen od hodiny, hodinový základ, min/optimal/max hodin dle domluvy, režie.
Bez ZP, slevy na dani, volna, stravenky, zkušebky. Prémie typicky nejsou (příp. montáž Kč/hod, cesta).
Měna CZK, u některých EUR + kurz.

### OSVČ — kancelář (vzor: Saad)
Jako OSVČ výroba, ale zpravidla **měsíční základ bez min/max hodin**.

### OSVČ — PLC programátoři (režie Mirka) — ⚠ data chybí
Hodinová sazba (možná EUR + kurz), režie max. **Zdroj sazeb zatím jen u Mirka** — před založením
zjistit, kde data jsou (Excel / režijní přehled v Centrále). Do té doby profil připraven, hodnoty prázdné.

### HPP — výroba (vzor: Diviš)
- Zdravotní pojišťovna ✅ · Sleva na dani ✅ · placen od hodiny NE · **měsíční základ**.
- Min/max hodin ✅ (např. 40/55) · osobní ohodnocení ✅.
- Dovolená **25 dní** (20 zákl. + 5 dodatková; +1 po 10/15/20 letech) · sick days **2/rok** (nevyčerpané proplaceny 70 %).
- Stravenkový paušál **82 Kč / odpracovaná směna** (nenáleží: sick day, OČR, PN, neodpracovaná směna).
- Limit přesčasů **150 h/rok** · víkend jen po schválení · nástup nejpozději **07:00**.
- Zkušební doba **4 měsíce** (výjimka 3) · fond **174 h/měs**.

### HPP — kancelář (vzor: Hladíková)
Jako HPP výroba, ale:
- **bez min/max hodin**, **víc sick days navíc** (individuálně, viz výjimky) · nástup nejpozději **09:00**.
- Home office možný (skupina kanceláře: HO ~48 h/měs, daňová úspora HO ano) · neplacený přesčas 0,5 h/den.

### DPP — krátkodobě (vzor: Řeháková)
Krátká smlouva, nízké hodiny, hodinový/nízký základ. ZP dle limitu DPP · bez volna/sick days/stravenky ·
bez zkušebky. Placen od hodiny.

---

## Navázání na model

Tyhle profily = obsah `tenant.engagement_category.field_profile` (jsonb: která pole vyplnit) + `wage_band`
(pásma) + defaulty entitlements. Individuální hodnoty jdou do `engagement` / `wage_component` /
`engagement_entitlement` a přepíšou default kategorie (3vrstvý princip: systém → kategorie → jednotlivec).
Detail modelu: `hr_financni_podminky_datovy_model.md`.

## Otevřené
1. **OSVČ PLC** — kde jsou Mirkova data o sazbách?
2. Potvrdit finální seznam kategorií (management / garant / brigádník DPČ hned, nebo později?).
3. Mzdové pásmo — jen na základ, nebo i další složky?
4. Stravenkový nárok = vždy konec ZD, nebo se domlouvá zvlášť?
