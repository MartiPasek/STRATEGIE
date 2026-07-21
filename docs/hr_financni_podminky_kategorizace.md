# HR — Finanční podmínky & kategorizace (pracovní spec)

> Živý draft, vzniká se Šárkou (personalistika) 9. 7. 2026. Bez konkrétních jmen/čísel — citlivé.
> Zdroj struktury: Centrála „Podmínky pracovníků" (karta zaměstnance). Cíl: STRATEGIE = jediné
> živé místo editace (v Centrále je zákaz úprav), directive-ready pásma dle kategorie.

## 1) Struktura finanční podmínky (bloky dle Centrály)

- **Obecné** — číslo, pracovník, firma, druh smlouvy, Aktuální, stručný popis pracovní pozice,
  datum smlouvy od/do, zkušební doba do, platnost výměru od, náborový poplatek, neplacený přesčas,
  přepínače: srážet neodpracované hodiny, placen/a od hodiny, sleva na dani, uplatnit slevy a odpočty
  1. měsíc, dopočet zk. doby. **Zdravotní pojišťovna** (jen HPP/DPP).
- **Počet hodin** — sml. úvazek/týden, reálný úvazek, počet hod./měsíc, min. / optimal. / max. hod.,
  režie max.
- **Peníze** — základ za hodinu, základ/měsíc, osobní ohodnocení, individuální ohodnocení,
  montáž Kč/hod, cesta montáž Kč/hod. **Měna + kurz** (viz gap — někteří OSVČ v EUR).
- **Volno** — standardní volno, volno navíc, standardní sick days, sick days navíc.
- **Prémie** — vedení obchodu, odměna jednatele, produkce, vedení lidí, kvalita, odměna – garant,
  služební automobil, firemní kultura.
- **Poznámka** (volný text — nese rozhodnutí i citlivá platová srovnání) + **Požadovaný plat v čase**.

## 2) Kategorie = matice (druh smlouvy × segment)

| Druh | Segment | Typické znaky |
|---|---|---|
| OSVČ | výroba | placen od hodiny, min/max hodin, základ/hod |
| OSVČ | kancelář | měsíční základ, bez min/max |
| OSVČ | PLC programátoři (režie Mirka) | **dnes v systému chybí — doplnit** |
| HPP | výroba | ZP, sleva na dani, min/max hodin, volno + sick days, osobní ohodnocení |
| HPP | kancelář | ZP, sleva na dani, volno + sick days (víc SD navíc), osobní ohodnocení |
| DPP | krátkodobě | krátká smlouva, nízké hodiny, nízký základ |
| *(budoucí)* | management / garant … | doplnit dle potřeby |

Pole, která se vyplňují, se liší podle kategorie (např. ZP/sleva na dani jen HPP/DPP;
placen od hodiny typicky OSVČ; min/max hodin u výroby).

## 3) Datový model (návrh)

**Finanční podmínka = kategorie (profil polí + mzdové pásmo) + individuální hodnoty člověka.**

- Onboarding: vyber kategorii → předvyplní relevantní pole/pásmo → doplň individuální domluvu.
- Kategorie nese (výhledově) **mzdové pásmo** (min–max základu) → splnění směrnice o transparentnosti
  odměňování (pásmo visí na kategorii dle popisu práce, ne ad hoc).
- Vazba na kartu zaměstnance: v kartě přehled finanční podmínky (zamčeno na 8 lidí HR + Marti).

## 4) Otevřené body / gapy

1. **PLC programátoři (OSVČ, režie Mirka)** — sazby „za kolik pro nás dělají" dnes vidí jen Mirek,
   v systému nejsou. Doplnit. → Zdroj dat: ? (Excel / režijní přehled v Centrále / jinde).
2. **Cizí měna** — někteří OSVČ počítáni v EUR (kurz). Model musí umět měnu + kurz, ne jen Kč.
3. **Poznámky** — volný text nese citlivá rozhodnutí a platová srovnání → časem strukturovat
   (kdo/kdy/proč navýšil) a držet jen v zamčeném pohledu.
4. **Pay-transparency (novela ZP, návrh MPSV 27. 3. 2026; účinnost pův. 1. 1. 2027)** — pásma na
   kategorii, informační povinnost vůči uchazečům, zákaz mzdové historie. Model připravit „directive-ready".

## 5) Pole k doplnění oproti aktuální editační stránce STRATEGIE

Sleva na dani · Zdravotní pojišťovna · blok Volno (volno navíc / sick days) · min/optimal/max hod ·
režie max · náborový poplatek · měna + kurz · Požadovaný plat v čase · přepínače (srážet neodpracované,
placen od hodiny, uplatnit slevy 1. měsíc, dopočet zk. doby).

## 6) Kontrola proti reálnému schématu (9. 7. 2026)

Ověřeno proti `tenant.engagement` / `wage_component` / `wage_component_type` (31 typů) /
`engagement_entitlement`.

**Uložitelné dnes (OK):** Obecné (číslo=ec_id, pracovník, firma, druh smlouvy, Aktuální=is_current,
popis pozice, smlouva od/do, zkušební do, placen od hodiny=hodinovka) · Počet hodin (úvazek týden /
reálný / hod. měsíc) · **Peníze — všech 6 polí má typ složky** (zaklad, os_ohodnoceni, individualni,
montaz_hod, cesta_montaz_hod) · **Prémie — všech 8 polí má typ složky** (vedeni_obchod, jednatelska_odmena,
produkce, vedeni_lidi, kvalita, garant_odmena, sluzebni_auto, firemni_kodex) · audit changed_by/at.
→ **Na peněžní straně jsme nezapomněli na nic.**

**Chybí sloupec / zapojení (doplnit):**

| Pole z karty | Kam patří | Stav |
|---|---|---|
| Zdravotní pojišťovna (HPP/DPP) | engagement | chybí sloupec |
| Platnost výměru od | engagement | chybí sloupec |
| Náborový poplatek | engagement | chybí sloupec |
| Neplacený přesčas | engagement | chybí sloupec |
| Min / Optimal / Max hod, Režie max | engagement | chybí sloupce |
| Přepínače: srážet neodpracované · sleva na dani · uplatnit slevy 1. měsíc · dopočet zk. doby | engagement | chybí (jen „placen od hodiny" existuje) |
| Volno: std. volno · volno navíc · std. sick days · sick days navíc | engagement_entitlement (code+value) | tabulka existuje, není zapojená v UI |
| Měna + kurz (EUR u OSVČ) | wage_component | chybí sloupec (jen Kč) |
| Požadovaný plat v čase | historie / pozn. | není |

→ Doplnění = pár sloupců na `engagement` + `currency` na `wage_component` + zapojit
`engagement_entitlement` pro Volno. DDL na public/tenant přes Marti-AI / lifespan hook, navrhnout dávkově.

## 7) Předvyplněné profily (šablony pro onboarding)

Které pole/složky se u kategorie standardně vyplňují (defaulty = vodítko, ne pravidlo; odvozeno z karet).

**OSVČ** — `engagement_type=osvc`; bez ZP, bez slevy na dani.
- výroba: placen od hodiny = ano; min/max hodin (např. 45/55); základ **hodinový**.
- kancelář: měsíční základ; bez min/max.
- osobní/individuální ohodnocení: typicky 0.
- Volno/sick days: většinou 0 (některé OSVČ mají volno navíc / sick days navíc dohodou).
- prémie: dle dohody (často jen odměna jednatele u jednatelů).
- měna: může být EUR (kurz) → potřebuje currency.

**HPP** — `engagement_type=hpp`; ZP = ano; sleva na dani = ano; srážet neodpracované = ano; platnost výměru od vyplněno.
- výroba: min/max hodin (např. 40/55). kancelář: bez min/max.
- základ **měsíční**; osobní ohodnocení typicky vyplněno.
- Volno: standardní volno (20) + volno navíc + standardní sick days (2) + sick days navíc dohodou.
- prémie dle role: vedení obchodu / vedení lidí (jen HPP), produkce, kvalita, garant, firemní kultura, služební auto.

**DPP** — `engagement_type=dpp`; ZP = ano; sleva na dani = ano; uplatnit slevy a odpočty 1. měsíc = ano.
- krátká smlouva (od–do); nízké hodiny (např. 25); základ hodinový nízký.
- osobní/individuální ohodnocení, volno, prémie: typicky ne.

Pozn.: profily = základ pro budoucí **číselník kategorií** (druh × segment) + **mzdová pásma** (directive-ready).
