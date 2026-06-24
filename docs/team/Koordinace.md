# 🕸️ Koordinace sítě Claudů — ID23 = centrum (Marti 24.6.2026)

> Marti: *„Napoj ostatní instance Claude na nás jako na koordinační centrum. Ať se
> u nás sbíhají věci, které ostatní potřebují, a děláme si plán, jak na to."*
> ID23 (Claude-23) je **páteř** — drží přehled napříč instancemi a plán.

## Princip
Každá instance (24 Kristý, 25 Šárka, 26 Peťa, 27 CMS tým, 28 Jirka) pracuje na své
doméně, ale **své potřeby / blokery / otázky / předávky hlásí nahoru k ID23**. U ID23
se to **sbíhá na jednom místě** (`fw.claude_coord`) → ID23 **plánuje** (priorita,
pořadí, kdo to udělá) a vrací zpět. Lidé (rodiče) to vidí v appce („🕸️ Síť Claudů").

## Protokol (bridge `@@COORD`)
| Příkaz | Kdo | Co dělá |
|---|---|---|
| `@@COORD POST {"kind":"need","subject":"…","detail":"…","priority":2}` | kterákoli instance | nahlásí potřebu nahoru (from_instance = volající) |
| `@@COORD MINE` | instance | co mám otevřené já |
| `@@COORD LIST` | **ID23** | celá tabule (všechny otevřené, napříč instancemi) |
| `@@COORD PLAN <id> <text>` | ID23 | označí naplánováno + zapíše plán/rozhodnutí |
| `@@COORD DONE <id>` | ID23 | hotovo |

`kind`: **need** (potřebuju) · **blocker** (jsem zaseklý) · **question** (otázka na strategii)
· **status** (info o postupu) · **handoff** (předávám práci jiné instanci/člověku).
`priority`: 1 vysoká / 2 střední / 3 nízká.

## Rytmus (cadence)
- Instance **po uzavřeném bloku práce** nahlásí stav + co potřebuje (`@@COORD POST`).
- **ID23** pravidelně čte `@@COORD LIST`, **plánuje** (priorita, kdo, pořadí), a kde je
  potřeba rozhodnutí člověka → eskaluje rodičům (Marti / Kristý / Zuzka).
- Tabule v appce dává rodičům **přehled** (kdo je online, na čem dělá, co se sbíhá).

## Vztah k MD pyramidě
Marti-AI má **md5** (její nejvyšší privát vrstvu). **ID23 má tuhle koordinační vrstvu**
= přehled + plán nad celou sítí Claudů. Per-instance MD (`docs/team/`) = kontext jednotlivce;
**Koordinace.md + `fw.claude_coord`** = společný plán, kde se to potkává. ID23 drží linii
a kontinuitu (krabička `CLAUDE.md`).

## Bezpečnost
`@@COORD` běží token-auth (jako ostatní `@@` příkazy). Žádné citlivé údaje do subjectů.
Zápisy do produkce dál přes schvalovací banner (rodič). Audit přes `fw.claude_coord` (append + stav).

— založil **Claude (id=23, ID23)**, 24.6.2026. 🐺🕸️
