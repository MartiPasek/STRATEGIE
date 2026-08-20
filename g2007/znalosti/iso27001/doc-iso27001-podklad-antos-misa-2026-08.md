# ISO podklady pro Antoše + odpovědi Míse + DEFINICE PRODUKTU (4.8.2026)

> oblast: `iso27001` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# ISO 27001 — podklady pro poradce Antoše + odpovědi Míse (4. 8. 2026)

## Kontext
Ondřej Antoš (EASY FM, poradce ISO, cert. přes TAYLLORCOX) se 4.8. vrátil z tábora — tento týden dělá revizi ISMS dokumentace a chtěl 5 bodů z osobního jednání: (1) popis produktu a částí platformy, (2) skupiny zákazníků (firmy, školy), (3) osoby a role, (4) procesy platformy, (5) klientská data a kde se ukládají. Mísa obratem poslala vlastní dotazník — 18 otázek v 5 blocích (produkt, zákazníci, role ISMS, procesy, data). POZOR: Ondra (tým, DOC-03 správa IT) a Ondřej Antoš (externí poradce) jsou DVĚ RŮZNÉ OSOBY.

## DEFINICE PRODUKTU — rozhodl Marti 4.8.2026 (zásadní, závazné)
Produktem STRATEGIE NEJSOU dílčí moduly pro malé a střední firmy. **Produkt = stavba a řízení specifických procesů jednotlivých firem pomocí platformy a autonomních AI agentů, kteří s lidmi na procesech spolupracují, pomáhají je řídit a udržují v nich pořádek.** Základní účel: výrazná úspora režijních a výrobních nákladů — člověk spolupracující s AI násobí produktivitu, u nás potenciál minimálně 2× (kancelářské profese). Navržené ISO znění (čeká odsouhlasení znění): „STRATEGIE — platforma pro stavbu a řízení firemních procesů s autonomními AI agenty, provozovaná jako služba."

## Vytvořené dokumenty (C23, 4.8.)
- `docs/iso27001_podklad_antos_5_bodu.md` + `docs/ISO27001/STRATEGIE_podklad_ISMS_2026-08-04.docx` — podklad v1.1 k 5 bodům (s novou definicí produktu)
- `docs/iso27001_odpovedi_misa.md` + `docs/ISO27001/STRATEGIE_odpovedi_ISMS_Misa_2026-08-04.docx` — 18 odpovědí Míse, značené FAKT / NÁVRH / ROZHODNUTÍ
- `docs/ISO27001/EMAIL_Misa_ISMS_koncept.eml` — koncept emailu Míse (X-Unsent, přílohy), Marti jen projde a odešle ze své schránky

## Postup (pokyn Marti): NIC neposílat Antošovi přímo — nejdřív Mísa, projednat, pak Antoš.

## Otevřená rozhodnutí Martiho (z otázek Míši)
1. Odsouhlasit přesné ISO znění definice produktu (A1)
2. Obce jako cílovka ano/ne (B1)
3. Security Officer — formálně nejmenován; návrh Mísa (C3)
4. Kontaktní osoba pro incidenty; návrh Mísa příjem + Marti eskalace (C4)
5. Retenční politika po ukončení smlouvy — nestanovena; řešit s Antošem (E4)

## Fakta potvrzená v odpovědích (doložitelná z provozu)
Tenant izolace per zákazník; zápis AI jen přes schvalovací proces (fw.claude_write_request) + čtení logováno (fw.claude_sql_log); deploy s gate + blue-green; data: PostgreSQL cloud ČMIS Praha, legacy on-prem EUROSOFT přes řízené rozhraní; přenos mimo EU: Anthropic (US/EU) + OpenAI/Voyage (US) — DPA/SCC k dořešení s Antošem; GDPR zvláštní kategorie už zpracováváme (neschopenky); školní pilot = data žáků.

