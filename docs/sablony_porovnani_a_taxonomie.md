# Pracovní smlouva — porovnání verzí + finální šablona + taxonomie ukládání
Pro Šárku, 25. 6. 2026. Marti odsouhlasil směr.

## Verze (všechny mám, přečteny)
- **Auditorská (21. 4. 2026)** — `EC_…_SN_260421` — verze po auditu, „syrovější".
- **Právníkova „Návrh finální" (1. 6. 2026)** — Ondřej Senft — revize auditorské verze.
- **V8 (16. 6. 2026)** — nejnovější, z ní jsem stavěl současné šablony (= právníkovo znění + udělané volby).

Vývoj: **auditor 21.4 → právník 1.6 (revize) → V8 16.6 (zešablonování s volbami).**

## ⚠️ KLÍČOVÉ ZJIŠTĚNÍ — přesčasy: tvůj instinkt byl správný
Mezi auditorskou (21.4) a právníkovou (1.6) verzí se **přesčasy reálně změnily**:

- **Auditorská 21.4** měla **konkrétní ujednání**: §2.5 *„Práce přesčas se sjednává do rozsahu
  maximálně **150 hodin za kalendářní rok**."* + §3 Mzda *„Mzda je sjednána již **s přihlédnutím
  k případné práci přesčas**."* → tj. přesčas do 150 h/rok je **zahrnut ve mzdě** (výhodné pro
  zaměstnavatele, právně přípustné dle §114 ZP, když je správně sepsáno).
- **Právník 1.6 to VYPUSTIL** a nahradil obecným zněním dle zákoníku práce: *„Za práci přesčas
  náleží zaměstnanci mzda a **příplatek**, případně náhradní volno…"* → tj. **zákonný režim**
  (přesčas se proplácí navíc s příplatkem), bez 150h ujednání a bez „mzda zahrnuje přesčasy".

**To je věcný (právní i obchodní) rozdíl** — právník to nejspíš vypustil záměrně (právní opatrnost).
Není to na mně, abych to potichu vrátil. **Rozhodnutí patří k Ondřejovi Senftovi / Marti‑AI / vedení:**
chcete „150 h + mzda s přihlédnutím k přesčasům" (auditor, výhodnější pro firmu), nebo zákonný
příplatkový režim (právník)? V8/současná šablona má teď **právníkovu (příplatkovou) variantu.**

## Co naopak právník vylepšil (doporučuju ponechat)
- **Přidal § 14** „Samostatná informace o obsahu pracovního poměru" — od novely ZP 2023 **povinné**
  (auditorská verze ho neměla).
- **Zmodernizoval terminologii**: „porušení pracovní **kázně**" → „porušení pracovních **povinností**"
  (auditor používal starý pojem); zmírnil místy tvrdé formulace.
- Do nadpisu doplnil *„uzavřená **podle zákona č. 262/2006 Sb.**"*.
→ V těchto bodech je **právníkova verze lepší a je v V8 zachovaná.**

## Porovnání proměnných částí: právník 1.6 → V8 16.6 (zešablonování)
| Místo | Právník 1.6 | V8 16.6 (současná šablona) | Doporučení |
|---|---|---|---|
| §1.1 pozice | „elektromontér" (jedna) | seznam: operátor / elektromontér junior / … (volba) | **V8** — pokryje všechny výrobní pozice |
| §1.2 doba | + věta „konkrétní varianta se před podpisem ponechá…" | bez té věty | **doplnit větu z 1.6** (užitečný návod) |
| §2.1 místo | plná adresa Nepomucká 259 | jen „Plzeň" | **Plzeň** (tvé rozhodnutí) |
| §2.2 úvazek | 40 h | 30/35/40/XX (volba) | **V8** |
| §5.2 telefon nadřízeného | 773 738 **586** | 773 738 **580** | ⚠️ **OVĚŘIT správné číslo** |

## Finální šablona
**Základ = V8 (16.6)** — je nejnovější, obsahuje právníkovo právní znění + udělané volby/doplňovačky.
Už jsem z ní vytvořil finální šablony (obě firmy, výrobní pozice), které máš:
- `EUROSOFT-Control_pracovni_smlouva_vyrobni_pozice.docx`
- `EUROSOFT-System_pracovni_smlouva_vyrobni_pozice.docx`

**K dotažení do úplného finále (3 drobnosti):**
1. Doplnit větu z §1.2 (právník): „Konkrétní varianta se v šabloně před podpisem ponechá pouze
   v rozsahu odpovídajícím sjednanému pracovnímu poměru."
2. Ověřit telefon v §5.2 (586 vs 580).
3. (Volitelně) porovnat i s auditorskou 21.4 — až ji znovu nahraješ.

## Doporučená taxonomie ukládání šablon
Tři osy: **firma × forma vztahu × typ dokumentu** (+ varianta pozice, kde dává smysl).

### Osy
- **Firma:** `EC` (EUROSOFT‑Control) · `ES` (EUROSOFT‑System)
- **Forma vztahu:** `HPP` (pracovní smlouva) · `DPP` (dohoda o provedení práce) ·
  `DPC` (dohoda o pracovní činnosti) · `OSVC` (smlouva o dílo / rámcová — fakturace, ne mzda)
- **Typ dokumentu:** pracovní smlouva · dodatek (prodloužení / změna mzdy / změna pozice) ·
  mzdový výměr · dohoda (DPP/DPČ) · smlouva o dílo (OSVČ) · potvrzení o zaměstnání ·
  výpověď / ukončení · …
- **Varianta:** `Vyrobni` / `Kancelar` (jen u smluv, kde se liší).

### Co dává smysl (ne všechny kombinace)
- **HPP** → pracovní smlouva (výrobní/kancelář) + mzdový výměr + dodatky. (EC i ES)
- **DPP / DPČ** → dohoda o provedení práce / o pracovní činnosti (NE „smlouva", NE mzdový výměr).
- **OSVČ** → smlouva o dílo / rámcová smlouva (fakturace, NE mzda). (EC i ES)

### Konvence názvu (navazuje na vaši stávající)
`{EC|ES}_{TypDokumentu}_{Forma}_{Varianta}_V{n}_{Iniciály}_{RRMMDD}.docx`
Příklady:
- `EC_PracovniSmlouva_HPP_Vyrobni_V9_SN_260625.docx`
- `ES_PracovniSmlouva_HPP_Kancelar_V1_SN_260625.docx`
- `EC_Dodatek_Prodlouzeni_V2_SN_260625.docx`
- `ES_DPP_V1_SN_260625.docx`
- `EC_SmlouvaODilo_OSVC_V1_SN_260625.docx`

### Struktura složek v ZZ_HR
```
ZZ_HR/Sablony/
  EC/
    HPP/        (pracovní smlouvy, mzdové výměry, dodatky)
    DPP_DPC/    (dohody)
    OSVC/       (smlouvy o dílo / rámcové)
  ES/
    HPP/  DPP_DPC/  OSVC/
  _Archiv/      (předchozí verze – V1…V8)
```
Aktuální verze v dané složce, starší do `_Archiv/`. „Current" = nejvyšší V{n}.

### Doporučení (kam směřovat)
- **Krátkodobě:** ZZ_HR + tahle konvence názvů (jasné, dohledatelné, verzované číslem V{n}).
- **Dlouhodobě:** šablony v systému (`tenant.doc_template`, SCD2 verzování `is_current`), generování
  per firma automaticky — tj. **jedna šablona = obě firmy** (EC/ES se dosadí z dat), méně souborů
  na údržbu. Tam směřuje editor šablon (Krok B HR sekce).

## Body k probrání (Ondřej Senft / Marti‑AI / vedení)
1. **🔴 PŘESČASY — hlavní rozhodnutí:** zákonný příplatkový režim (právník, teď v šabloně) vs.
   „150 h/rok zahrnuto ve mzdě" (auditor, výhodnější pro firmu). Doporučuju **nechat na Ondřeji
   Senftovi** — vypustil to nejspíš z právního důvodu. Po jeho stanovisku zapracuju.
2. Telefon §5.2 (586 vs 580) — které je správné.
3. Vrátit právníkovu větu v §1.2 (návod k variantě) — ano/ne.
4. Taxonomie: souhlas s osami firma × forma × typ a s konvencí názvu?
5. OSVČ: „smlouva o dílo" vs „rámcová smlouva" — co používáte (kvůli šabloně).

## Stanovisko Marti‑AI (konzultováno přes most 25. 6. 2026)
**Přiklání se k variantě B (zákonný/příplatkový režim — Ondřejova verze).** Argumenty:
- Varianta A je legální, ale **asymetrická** — zaměstnanec odpracuje až 150 h přesčas a nedostane nic navíc.
- **Výrobní pozice je fyzicky náročná** — 150 h/rok ≈ skoro 4 týdny práce navíc; paušál bez příplatku je pro elektromontéra obzvlášť tvrdý.
- **Dlouhodobá důvěra a nižší fluktuace** > krátkodobá úspora; A nese reputační riziko.
- **Navrhuje střední cestu:** smluvní přesčas do **nižšího limitu (např. 50–80 h/rok)** zahrnutý ve mzdě,
  nad limit zákonný příplatek — „ani čistá A, ani čistá B", férovější k lidem a firmě dává předvídatelné náklady. Ondřej to umí zformulovat.
- Finální slovo nechává na **Ondřejovi a Marti**.

## ROZHODNUTO — politika přesčasů (Marti + Šárka, 25. 6. 2026)
Marti potvrdil, že **finální slovo má Marti‑AI** → platí **varianta B (zákonný režim)**.
Upřesnění od Šárky (zapracovat do šablon):
- **Výroba:** přesčas se proplácí **dle ZP** (mzda + příplatek, příp. náhradní volno) → výrobní šablona je OK.
- **Kancelář:** přesčasy nechceme a **neproplácíme**; pokud nastanou, zaměstnanec si je **vybere náhradním volnem**
  (v kancelářské šabloně §2.5 formulovat náhradní volno jako sjednaný způsob vypořádání).
- **150 h/rok** = zákonný strop, jen **informativně** (NE „zahrnuto ve mzdě").
- **Dobrovolná práce navíc** (víkendy kvůli výdělku) = **prémie za loajalitu** (§4 Další příjmy), NE přesčas.
- Cíl: **nedráždit auditory** — čistý zákonný režim je auditorsky bezpečný.

## ROZHODNUTO — zkušební doba (Šárka, 25. 6. 2026)
- **Standard = 4 měsíce** (legální dle **novely ZP od 6/2025**, která limit zvýšila na 4 měsíce).
- Důvody: víc času poznat zaměstnance + sladěno se **stravenkovým paušálem** (nárok až po 4 měsících).
- Pole je editovatelné → při individuální domluvě lze změnit (Martiho „možnost volby" tím pokryta).
