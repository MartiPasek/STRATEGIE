# Nástřely smluv + mzdových výměrů — souhrn pro Šárku

**Vygenerováno:** 10. 6. 2026 z živé evidence STRATEGIE (personalistika v2, 79 aktuálních vztahů).
**Stav:** první nástřel k doplnění a kontrole. **Vše červené `[DOPLNIT]` je nutné doplnit ručně.**

## Co je ve složce

- `00_Prehled_pripravenosti.xlsx` — jeden řádek na člověka: typ, firma, nástup, úvazek, mzda/odměna celkem, dovolená, sick days a sloupec **„K doplnění"**.
- `01_HPP_pracovni_smlouvy/` — **48** pracovních smluv (HPP), každá s mzdovým výměrem v § VIII.
- `02_DPP_dohody/` — **2** dohody o provedení práce.
- `03_OSVC_ramcove_smlouvy/` — **29** rámcových smluv o spolupráci (OSVČ).

Soubor = `<id>_<jméno>.docx`. Kde jméno chybí: `<id>_BEZ_JMENA_c<číslo>.docx`.

## Co je z evidence vyplněno automaticky

Typ vztahu (HPP/DPP/OSVČ), firma (EUROSOFT-Control / EUROSOFT-System), den nástupu, doba určitá/neurčitá, zkušební doba (kde je), týdenní úvazek, výměra dovolené (zákonná + dodatková), sick days, a **mzdový výměr s reálnými složkami** (základní mzda, osobní ohodnocení, prémie, vedení lidí, individuální odměna, odměna jednatele) včetně součtu hrubé mzdy.

## Co je nutné doplnit ručně (`[DOPLNIT]` v dokumentech)

Tyto údaje **v naší evidenci nejsou** (jsou v Heliosu / na kartách):
- **Identifikace firmy:** IČO, sídlo, zápis v OR, jednatel — pro EC i ES (stačí doplnit 1× a rozkopírovat).
- **Osobní údaje:** datum narození, bydliště, rodné číslo (HPP) / IČO + sídlo (OSVČ).
- **Místo výkonu práce** (HPP).
- **Druh práce / pozice** — vyplněno jen u 3 lidí; u ostatních doplnit.
- **Rozvržení pracovní doby / povinný nástup** — pracovní režim zatím není navázán per osoba.

## Nálezy kvality dat (doporučuji projít)

1. **16 vztahů nemá jméno** v evidenci (hlavně OSVČ s čísly 9xxx + č. 374, 13, 47, 27, 361). Nástřely jsou označené `BEZ_JMENA`. → doplnit jména.
2. **Marti Pašek (č. 2 ES i č. 41 EC)** má **0 mzdových složek** — jeho mzda nebyla v původním „bastlu". Smlouvy se vygenerovaly bez výměru.
3. **Podezřelá odměna u 8 OSVČ:** stejná hodnota `129 221 Kč` (a dále 207 380 / 166 979 / 137 836 / 108 010). Vypadá jako artefakt migrace — ověřit skutečné odměny.
4. **„Odměna jednatele 1 000 Kč"** je navázaná na řadu řadových zaměstnanců — ověřit, zda je to záměr, nebo defaultní hodnota z migrace.
5. **Dovolená/sick u OSVČ** vedená jako smluvní benefit — u živnostníků právně neobvyklé, označeno k potvrzení.
6. **Pozor na záměnu:** „Martin Pašek" č. 29 je **jiný člověk** než Marti Pašek (č. 2/41).

## Doporučený další krok

Doplnit firemní hlavičky (IČO/sídlo/jednatel) a osobní/pozicní pole; pak lze ze stejného generátoru vytvořit finální verze. Ideálně navázat pracovní režim (nástup/přesčas) na lidi, ať se doplní i rozvržení pracovní doby automaticky.
