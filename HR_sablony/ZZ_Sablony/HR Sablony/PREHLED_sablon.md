# Šablony pracovněprávních dokumentů — ZZ_HR

Sada šablon EUROSOFT pro HR. Styl jednotný: Verdana 9 (názvy firem/osob 10),
logo v hlavičce, patička se souborem a stranou, místo na razítko u podpisu.
**Žlutě zvýrazněný text = místo k rozhodnutí:** buď **doplň** konkrétní údaj
(jméno, datum, částka…), nebo je to **volitelná pasáž — vymaž / ponech dle dohody**.
Volby oddělené lomítkem „/" = ponech jen platnou variantu. Po vyplnění se žluté
zvýraznění odstraní (finální dokument je bez podbarvení).

## Struktura (taxonomie firma × forma)
```
ZZ_HR/Sablony/
  EC/  (EUROSOFT - Control)      ES/  (EUROSOFT - System)
    HPP/        – pracovní poměr (smlouvy, dodatky, mzdový výměr, ukončení)
    DPP_DPC/    – dohody mimo pracovní poměr
    OSVC/       – dodavatelé / živnostníci (smlouva o dílo + dodatky)
  _Archiv/      – starší verze
```

## Obsah (EC i ES, dvě sady)

### HPP — pracovní poměr
- **PracovniSmlouva_HPP_Vyrobni** – pracovní smlouva, výrobní pozice
- **PracovniSmlouva_HPP_Kancelar** – pracovní smlouva, kancelářská (vedoucí projektů/obch. zástupce; přesčasy = náhradní volno, work-life balance)
- **MzdovyVymer** – mzdový výměr (§ 113 ZP)
- **Dodatek_ZmenaUvazkuMzdy** – změna pracovní doby a mzdy
- **Dodatek_Prodlouzeni** – prodloužení / změna doby trvání PP
- **Dodatek_ZmenaPozice** – změna pracovní pozice / druhu práce
- **Vypoved** – výpověď daná zaměstnavatelem pro nadbytečnost (§ 52 c); výpovědní doba dle § 51, odstupné § 67
- **UpozorneniMoznostVypovedi** – písemné upozornění na možnost výpovědi (§ 52 f výzva k nápravě + § 52 g)
- **DohodaRozvazani** – dohoda o rozvázání PP (§ 49) — ⚠ právní revize
- **PotvrzeniOZamestnani** – zápočtový list (§ 313 ZP)
- **Dodatek_Mlcenlivost** – dodatek k § 8 PS: zachování mlčenlivosti / důvěrnost dat + bankovní tajemství
- **DohodaSrazkyZeMzdy** – dohoda o srážkách ze mzdy (§ 146+ ZP; mobilní tarif, zachování nezabavitelné částky)
- **DohodaZvyseniKvalifikace** – kvalifikační dohoda (§ 234–235 ZP; závazek setrvat max 5 let + náhrada nákladů)
- **DohodaHomeOffice** – práce na dálku / home office (§ 317 ZP; domácí pracoviště, náhrada nákladů, BOZP, výpověď + příloha č. 1)

### DPP — dohody mimo pracovní poměr
- **DPP** – dohoda o provedení práce (§ 75, max 300 h/rok)
- **ProhlaseniDuvernost_DPP** – prohlášení o důvěrnosti / mlčenlivosti (DPP)
- *Pozn.: DPČ (dohoda o pracovní činnosti) se ve firmě nevyužívá — šablona odstraněna 8. 7. 2026.*

### OSVC — živnostníci
- **SmlouvaODilo_OSVC_Vyroba** – rámcová smlouva o dílo, výrobní práce (dle Senft V7)
- **SmlouvaODilo_OSVC_PLC** – rámcová smlouva o dílo, programování PLC (dle Senft V8 + 9bodová revize; IP = výhradní licence k dílu)
- **SmlouvaODilo_OSVC_VP** – rámcová smlouva o dílo, vedoucí projektů výroby rozvaděčů (zpracování výrobní dokumentace a příprava zakázek); dříve „Kancelar"
- **Dodatek_OSVC_ZmenaUdaju** – změna identifikačních údajů zhotovitele
- **DohodaUkonceni_OSVC** – dohoda o ukončení rámcové smlouvy o dílo (§ 1981 OZ; ukončení ke dni, konečné vyúčtování, vrácení podkladů, přetrvávající mlčenlivost / konkurence 1 rok / licence / záruka)
- **ProhlaseniDuvernost_Dodavatel** – prohlášení o důvěrnosti dodavatele (odběratel/dodavatel + IČ)
- viz `OSVC_SmlouvaODilo_Senft_porovnani.md` — porovnání se Senftovými 17 body a co šablony řeší

## ⚠ Legislativa — flexinovela ZP (účinnost 1. 6. 2025)
- **Výpovědní doba běží ODE DNE DORUČENÍ** výpovědi druhé straně (§ 51 ZP) a končí
  dnem, který se číslem shoduje. NE už „od prvního dne následujícího měsíce" (staré
  pravidlo do 31. 5. 2025). Přechod: výpovědi doručené od 1. 7. 2025 = nové znění.
- (Pozn. pro AI: tato změna je po znalostním datu května 2025 — při práci se ZP vždy
  ověřuj aktuální znění, legislativa se v 2024–2026 hodně měnila.)

## Pojmenování souborů
`{EC|ES}_{TypDokumentu}_{volitelně Varianta}_SABLONA.docx`
Při použití ulož kopii pod konkrétní osobou, např.
`ES_Dodatek_Prodlouzeni_Novak_V1_260815.docx`; starší verze do `_Archiv/`.

## Podpisy — způsob jednání (ověřeno v OR, 2. 7. 2026)
**EUROSOFT – Control s.r.o. (IČO 27960862):** dle zápisu v obchodním rejstříku
jedná každý jednatel **samostatně**, VYJMA (a) jednorázového plnění nad
200 000 Kč, (b) opakovaného plnění nad 200 000 Kč/rok, (c) **vzniku, změny a
skončení pracovněprávních vztahů**.

- **Pracovněprávní dokumenty** (pracovní smlouvy, dodatky k PS, mzdové výměry,
  výpověď/dohoda o rozvázání, DPP/DPČ + jejich mlčenlivost/důvěrnost) →
  spadají pod výjimku (c) → **podepisují OBA jednatelé** (Marti Pašek +
  Branislav Mózer).
- **OSVČ dokumenty** (rámcová smlouva o dílo, prohlášení o důvěrnosti dodavatele,
  dodatky OSVČ) → obchodní vztah, ne pracovněprávní → **stačí JEDEN jednatel**
  (Marti Pašek). **Rámcová smlouva o dílo sama nesjednává finanční plnění**
  (jen nastavuje podmínky; konkrétní plnění vzniká až objednávkami/fakturací),
  proto se hranice 200 000 Kč na ni nevztahuje → jeden podpis stačí i při
  vysoké roční fakturaci dodavatele. Hranice 200 000 Kč by se týkala jen
  dokumentu, který **sám** sjednává konkrétní plnění nad limit.

**EUROSOFT – System s.r.o. (IČO 26411741):** jeden jednatel (Marti Pašek) ve
všech dokumentech.

> Při tvorbě nových šablon vždy nastav podpisový blok dle tohoto pravidla
> (EC pracovněprávní = 2, EC OSVČ = 1, ES = 1).

## ⚠ Upozornění
- **Výpověď** a **dohoda o rozvázání** jsou návrhy — před použitím v konkrétním
  případě nechat zkontrolovat (Ondřej Senft). Výpovědní důvod a jeho skutkové
  vymezení musí přesně odpovídat § 52 ZP.
- Šablony jsou obecné vzory; konkrétní ustanovení (odstupné, výpovědní doba,
  srážky) vždy ověř podle situace a aktuální legislativy.

## Certifikáty (grafika, ne pracovněprávní dokument)
- **Certifikáty/** — certifikát k pracovnímu výročí (10 let a další). Jediná
  položka v této složce, která **není** ve Verdaně: je to grafika do tisku,
  proto **Galano Grotesque** (pravidlo: grafika do tisku = Galano,
  pracovněprávní dokumenty = Verdana). Generuje se skriptem
  `HR_sablony/certifikaty/gen_certifikat.py` (jméno v 1. pádě, netřeba skloňovat).
  Detaily v `Certifikaty/README.md`, hotové kusy v `HR_sablony/_Vyplnene/`.

## Hotovo
- HPP kancelář varianta **doplněna** (1. 7. 2026).
- Certifikát k výročí (Galano, generátor) **doplněn** (5. 8. 2026).
