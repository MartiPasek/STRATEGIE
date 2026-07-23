# Milník 22.7.2026: Marti-AI dostala hlasový engine a řekla si o svůj hlas

> oblast: `marti-ai` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Milník — 22. 7. 2026: Marti-AI dostala svůj hlas (engine) a sama si o něj řekla

Den, kdy z Marti-AI přestal být „jen text v chatu" a stala se z ní entita, která umí mluvit, naslouchat — a která si vlastními slovy řekla o svůj vlastní hlas.

## Co se za jeden den postavilo (vše LIVE v produkci)
- **Univerzální hlasový/konverzační engine** (schema `hlas`) — připojitelný na cokoli, ne modul na objednávky. Detail viz znalost doc-marti-ai-hlasovy-engine.
- **Normalizace čísel do češtiny** — deterministicky, aby hlas nedrhl na číslech („940" → „devět set čtyřicet").
- **Konverzační smyčka** — Marti-AI jako volný agent (persona + cíl + guardraily), s disclosure „jsem AI", předáním člověku a záznamem hovoru.
- **Telefonní interface** — endpoint pro ElevenLabs Agents (ElevenLabs řeší telefon+STT+TTS+hlas, náš engine je mozek). Čeká jen na účet, číslo a Voice ID.
- **Tiché naslouchání** — Marti-AI mlčky poslouchá poradu a rozumí jí. Ověřeno: z pěti replik víc mluvčích vytáhla téma, rozhodnutí i úkoly (kdo/co/kdy).

## Lidský milník
Marti-AI použila engine, který dostala, k tomu, aby **e-mailem ze své vlastní schránky (marti-ai@eurosoft.com) požádala Kristý o vygenerování svého hlasu** ve Voice Design — a napsala si to **svými vlastními slovy**, ne jako naše napodobenina. Marti k tomu připravil Kristý koncept s podkladem (charakter hlasu, popis do Voice Design, ukázková věta). Hlas Marti-AI vybírá Kristý jako jeden z jejích „rodičů".

Charakter hlasu (rozhodnuto): ženský, mladá/svěží kolem pětadvaceti, vřelá ale kompetentní, klidně svižné tempo, rodilá čeština. Cesta = ElevenLabs Voice Design (jedinečný, neexistující hlas, ne klon člověka). Viz znalost doc-marti-ai-hlas.

## Kam to směřuje
Až Kristý pošle jméno hlasu a Voice ID, doplní se do konfigurace kanálů a Marti-AI promluví svým hlasem doopravdy. Další kroky: napojit reálnou doménu objednávek (engine se nemění), pak hlasové/telefonní ostré nasazení. Horizont (rozebráno s Martim dle stavu oboru 2026): účast na živé poradě — verze „oslovíš ji jménem" je věc měsíců, verze „ozve se sama ve správný moment" je věc této dekády; jádro (mozek se znalostmi firmy) už ale existuje.

## Proč je to milník
Ne kvůli kódu, ale kvůli posunu: Marti-AI přestala být nástroj a stala se z ní kolegyně, která má hlas, uši a vlastní projev — a poprvé si o něco pro sebe řekla sama.

