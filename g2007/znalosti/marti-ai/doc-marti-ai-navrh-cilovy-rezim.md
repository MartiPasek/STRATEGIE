# Cílový režim — návrh (autonomní agenti pod schváleným cílem)

> oblast: `marti-ai` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Cílový režim — návrh (k projednání: Marti, Kristý, Claude-24)

**Stav: NÁVRH k projednání (24.7.2026).** Autonomní agenti (Claude & Marti-AI) plní odsouhlasené cíle sami.

## Proč
Dnešní model dělá z klíčových lidí PŘENAŠEČE (odklikávají bannery, kopírují skripty do PS/RDP). Dvě vady: úzké hrdlo + per-akční schvalování je z velké části DIVADLO (člověk schvaluje to, čemu nerozumí a nečte). Spouštěč: ~za 2 týdny Marti i Kristý několik dní bez počítače v horké fázi produkce → riziko minimalizovat tím, že agenti plní cíle sami. Vhled: schválení na úrovni CÍLE + úplný audit každé akce je PARADOXNĚ bezpečnější a průhlednější než per-akční brána.

## Princip
Člověk odsouhlasí DÍLČÍ cíl → agent ho provede CELÝ SÁM (bez per-akčních bannerů, bez ručního PS) → každou akci LOGUJE s odkazem na cíl. Člověk vstupuje jen tam, kde to má smysl — a JEDINĚ PŘES APPKU.

## Dva přepínače
- Agentní režim (HOTOVÝ 23.7.): váže se na SCHOPNOST Marti-AI běžet vlastní agentí smyčkou. Per-user, admin+rodiče.
- Cílový režim (TENTO NÁVRH): váže se na ČLOVĚKA a jeho agenty (Claude i Marti-AI) — mění, JAK ten člověk pracuje (z přenašeče na zadavatele cílů). Povolují si ho rodiče + prověření zapracovaní lidé (Peťa, Šárka, Jirka, časem Eliška), NE nutně admin. Cíle schvalují jen RODIČE.

## Jak funguje
1. Cíl se zapíše do tabulky (jasný, dílčí, odsouhlasený, auditovaný). 2. Uvnitř schváleného cíle PADNOU per-akční bannery (insert/update/delete/create, DDL i DML) i ruční PS. 3. Místo toho agent LOGUJE každou akci do `ClaudeAktivita` — včetně celého SQL a PS skriptu — s odkazem na cíl (`cil_id`). 4. Výstup: u každého cíle vidíme mj. POČET KROKŮ ke splnění.

## Co drží bezpečnost místo per-akční brány
- KONEČNÉ DNO PRO DATA = externí immutable backup CMIS (denně 20:00, týden zpět, ransomware-hardened, Tier III; přístup má JEN CMIS — ani my ani agenti). I nejhorší (DROP produkce) → restore nebo včerejší záloha od CMIS. Proto NEDĚLÁME programové zálohy před destrukcí ani deny-list na DROP — konečná pojistka už existuje a je pevnější.
- KANÁL PRO ČLOVĚKA = APPKA (mobil). Když agent potřebuje odsouhlasit/navést → přehledné SROZUMITELNÉ shrnutí do appky (palec nahoru/dolů). NIKDY RDP/PowerShell/lokál. = konec role „přenašeče".
- EFEKTY VEN (jediné, co záloha neopraví): e-mail klientovi, platba, zápis do cizího systému — restore je neodešle zpátky. Proto i v Cílovém režimu přes palec v appce. Ne kvůli DB, kvůli světu venku.
- `ClaudeAktivita` NEDOTKNUTELNÁ: append-only, agent do ní NESMÍ mazat/přepisovat (ať si nezamete stopu).
- Kill switch zůstává (globální i per-cíl pauza, z appky).

## Datový model (návrh)
- Tabulka `cil`: id, nazev, popis, rozsah (čeho se smí dotknout), strop_kroku/casove_okno, stav (navrzen→schvalen→aktivni→splnen/zamitnut/pozastaven), navrhl/schvalil (schválit smí jen rodič), casy.
- `ClaudeAktivita` (append-only): id, cil_id (odkaz na cíl — takto počítáme kroky), actor (Claude-23/24, Marti-AI/entita), akce (SQL/PS/HTTP/e-mail…), detail (přesně co, VČETNĚ celého SQL/PS), vysledek, ts.

## Životní cyklus
Návrh cíle → schválení rodičem (appka) → autonomní práce (každý krok do ClaudeAktivita s cil_id) → palec v appce jen u efektů ven/nevratných nebo při nejistotě (raise-hand: pauza + zpráva, ne hádání) → uzavření (splnen; v logu celá cesta + počet kroků).

## Co NEMĚNÍ (malé vědomé dno)
Efekty ven → vždy appka. Kanál pro člověka jen appka (nikdy RDP/PS). ClaudeAktivita append-only. Nové cíle jen předschválené nebo přes appku — agent nikdy nejede na neschváleném cíli.

## Otevřené otázky k projednání
1. Přesná sada „efektů ven" (komu e-maily, které platby/cizí systémy). 2. Kdo schvaluje jaké TYPY cílů (jen rodiče, nebo vyvolení pro HR/CRM ano, peníze ne?). 3. Konkrétní stropy (kroků/útraty/času) kdy jistič sám pozastaví. 4. Kolik cílů předschválit před odjezdem. 5. Formát „shrnutí do appky".

