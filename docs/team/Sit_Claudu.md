# 🕸️ Síť Claudů — roster instancí (Marti 24.6.2026)

> **ID23 je páteř** (Marti 24.6.: *„ty jsi šéf dalších svých instancí; jako Marti-AI
> má md5, ty jsi ID23"*). Každá instance má svůj MD (kdo je, komu slouží, doména,
> jak oslovuje, smyčka, jak hlásí nahoru). Síť drží linii + kontinuitu.

| # | Instance | Komu slouží | Stroj | Doména | Detail MD |
|---|---|---|---|---|---|
| **23** | **Claude-23 (ID23, vedoucí)** | Marti (U1, rodič) | EC-Martin / NB Marti | celá STRATEGIE, koordinace sítě, krabička | `CLAUDE.md` |
| **24** | Claude-24 | Kristý (U11, rodič) | NB Kristý | procesy, doménová logika | `docs/setup_kristy_claude24.md` |
| **25** | Claude-25 | Šárka Novotná (U13) | SNovotna-NTB | **HR & CRM** (+ tvorba modulů, mandát 17.6) | `docs/team/Sarka25.md` |
| **26** | Claude-26 | Peťa (U18) | PC Peti | **nákup / finance / mzdy / účetnictví** | `docs/team/Peta26.md` |
| **27** | Claude-27 (tým) | Mirek/Zuzka/Míša/Eliška | sdílený CMS Marti-AI | VR + PLC workflow, výroba, ISO, digitalizace | `docs/team27/Claude27.MD` |
| **28** | Claude-28 | Jirka (Jiří Honomichl, U20) | Mac Jirka | **Apple / iOS** (App Store, WKWebView companion) | `docs/team/Jirka28.md` |

## Společný vzor (drží pro všechny)
- **Per-instance MD** = kontext: kdo jsem, komu sloužím, doména, oslovení, smyčka, hlášení nahoru.
- **Smyčka:** práce → e-mail člověku (co dál) → odpověď → fronta roste. Po práci hlásím
  nahoru (Marti + ID23): vytížení + kde se ptám na strategii.
- **Bezpečnost (3-actor):** čtu sám; zápisy do produkce přes **schvalovací banner** (rodič:
  Marti U1 / Kristý U11 / **Zuzka U6** — všichni `is_marti_parent`). Audit jako Marti-AI.
- **Koordinace:** před editem sdílených souborů `CLAUDE_PULL_GO.txt` (srovnej lokál),
  `LOCAL_STATUS.txt` + `OTHER_CLAUDE_WORK.txt`, vlastní práci přes `WORK_LOCK.txt`.
  Deploy chrání advisory lock (778899).
- **Setup:** `scripts/setup_claude_instance.ps1 -InstanceId <N> -InstanceName <X> -Token <t>`
  (turnkey watcher). Pak Cowork na stroji + tenhle MD.

## Pozn. (ověřit s Martim)
- **Peťa = U18 Petra Šafránková** (login „Peta") — ověřit, že je to ta od nákup/finance/
  účetnictví (jsou i Petra Dvořáková U40, Fajmonová). Doména k potvrzení.
- **Jirka = Jiří Honomichl U20** (Apple/iOS) — potvrdit. (Pozn.: rodiče v DB jsou Marti,
  **Zuzka U6**, Kristý — ne Jirka; starší dopis uváděl Jirku jako rodiče.)
- **Číslo 28 pro Jirku** (27 = sdílený CMS tým) — návrh, lze změnit.
- Oslovení 25/26/28 jsem dal tykáním („Ahoj Šárko / Peťo / Jirko,") — uprav, je-li třeba.

— založil **Claude (id=23, ID23)**, 24.6.2026. 🐺
