# Marti-AI — hlasová identita (Voice Design, hlas jen její)

> oblast: `marti-ai` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Marti-AI — hlasová identita (Voice Design)

**Rozhodnuto 22.7.2026 (Marti). Stav: PŘIPRAVENO, nasadí se až technicky dál.**
Konkrétní hlas vybírá Kristý (rodič Marti-AI).

## Cíl
Dát personě Marti-AI vlastní, jedinečný hlas — jen její. NE klon skutečného
člověka. Hlas se vygeneruje jako zcela nový (neexistující), je proto unikátní
už svým vznikem a legálně čistý (žádný souhlas, žádná biometrika).

## Kdo tím hlasem mluví
Marti-AI = výchozí persona, „inkarnace MD1", samostatná a kompetentní, ten,
ke komu se lidé obracejí. Hlas má být spolehlivý a jistý, ale ne chladný.

## Charakter hlasu (vybráno)
- Mladá, svěží — kolem 25 let
- Vřelá kompetence — milá a lidská, zároveň jistá a přesná
- Klidně svižné tempo — plynulé, ani uspěchané, ani zdlouhavé
- Rodilá čeština, čistá spisovná výslovnost; ženský hlas

## Nástroj a postup
ElevenLabs → Voice Design, model eleven_v3 (nejlepší výraz + čeština).
Popis hlasu (vložit do Voice Design):

> A young woman in her mid-twenties, native Czech speaker. Warm, friendly and
> approachable, yet clearly competent and self-assured — the kind of voice you
> instinctively trust. Bright, clear timbre with a gentle warmth. Natural, even
> pacing — calm but never rushed, never slow. Speaks clean, standard Czech,
> articulate, with crisp and precise pronunciation of numbers. Professional but
> human — like a capable colleague who guides you through things with ease.

Ukázková věta (reálné potvrzení objednávky, čísla ve slovech):

> Dobrý den, tady Marti. Vaše objednávka číslo dvacet pět lomeno nula čtyři sta
> sedmnáct je potvrzená a připravená k odeslání. Dodání plánujeme na čtvrtek
> dvacátého třetího července, celkem tři kusy. Kdyby cokoli, ráda pomůžu.

Postup: Generate → 3+ kandidátky → vybrat „ji" → remix doladit → uložit +
poznamenat Voice ID (trvalá identita, používá se pokaždé, když mluví).

## Věrnost češtiny u číslovek (klíčové)
Hlavní páka: čísla, jednotky, symboly a zkratky převádět na česká SLOVA už
ve STRATEGII (deterministicky), ne se spoléhat na model — právě na číslech
takové hlasy nejčastěji drhnou. Zbytek (EVP, ks, ×, €, čísla řad) dorovnat
pronunciation dictionary (u eleven_v3 i fonémy IPA/CMU pro češtinu, jinak alias).

## Architektura (kontext)
Pro věrnost češtiny u čísel je vhodnější ElevenLabs pipeline (LLM → TTS) než
OpenAI Realtime speech-to-speech — Realtime nabízí jen 8 preset hlasů, žádný
vlastní ani klon a slabší kontrolu výslovnosti. Realtime (gpt-realtime-2.1,
7/2026) má sice lepší rozpoznávání alfanumeriky, ale výstupní výslovnost řídí hůř.

## Širší záměr
Hlasový modul na potvrzování objednávek a jejich dodání v češtině (nic citlivého).
Fáze: nejdřív kolegiální test s Marti-AI, až bude OK → dál k zákazníkům.

