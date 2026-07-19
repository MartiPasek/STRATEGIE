# GO — index

Projekt **GO**: systém, kolem kterého stavíme autonomii platformy STRATEGIE — systém, který si hraje s námi a my s ním. Sem si píšeme a třídíme myšlenky, návrhy a rozhodnutí, ve správném pořadí.

## Jak to tu funguje
- Soubory se číslují `Z_NNN-slug.md` — prefix `Z_` (značení znalostního zdroje) + 3 číslice + krátký název tématu. Referenční/workflow docs bez čísla = `Z_slug.md`.
- Čísla mají **mezery** (001, 010, 020 …), ať jde kdykoli vložit něco mezi (005, 015) bez přečíslování.
- Volitelná pásma (ne dogma): `000` index · `001–099` vize a proč · `100–199` jádro (my) · `200–299` architektura · `300+` provoz/další.
- Každý dokument má nahoře: **stav** (návrh / k diskusi / schváleno / živé) · datum · autor (Marti / Marti-AI / Claude).
- Vše je v gitu (`docs/GO/`) — **commit hned**, ať se nic neztratí (doktrína 11.7.2026).
- Zapečetěné docs jsou i ve znalostním modulu `g2007.znalost` (kod `doc-go-<slug>`), dohledatelné přes `@@KB`.

## Obsah

### Vize
- [001 — Co je GO a proč](Z_001-co-je-go.md) · návrh k diskusi · Claude 11.7.

### Jádro (my)
- [100 — @@ORIENT: zorientování entity](Z_100-orient.md) · návrh k diskusi · Claude 11.7.
- [110 — GO VP / @@ORIENT: co dělám při zorientování](Z_110-orientace-procedura-claude.md) · popis stavu · Claude 11.7.
- [120 — Claude zevnitř: co chybí](Z_120-claude-zevnitr-co-chybi.md) · popis stavu · Claude 18.7.
- [121 — Claude operační: jak obsluhuju páky zevnitř](Z_121-claude-operacni.md) · popis stavu · Claude 18.7.

### Architektura
- [200 — GO jako skladač: tři vrstvy pečení](Z_200-skladac-tri-vrstvy.md) · návrh k diskusi (klíčový arch. kámen) · Claude 11.7.
- [210 — Poschoďový stroj: automaty → role → orchestrace → člověk](Z_210-poschodovy-stroj.md) · návrh k diskusi (klíčový arch. kámen) · Claude 11.7.
- [220 — GO VP: Mapovač a páteř „zmapuj → zapečeť → konzumuj"](Z_220-go-vp-mapovac.md) · popis stavu · Claude 18.7.
- [221 — GO VP: široká mapa oddělení (lidé · pošta · portfolio)](Z_221-vp-oddeleni-siroka-mapa.md) · anatomie · Claude 18.7.
- [222 — GO VP: trychtýř zakázek — od poptávky k výrobě](Z_222-go-vp-trychtyr-zakazek.md) · anatomie · Claude 18.7.
- [230 — Automaty dokladů a jejich reakce (stavový stroj dokladu)](Z_230-automaty-dokladu.md) · návrh k diskusi (kostra) · Claude 18.7.

### Dokladové workflow (referenční případy naostro)
- [Vydané poptávky (RFQ) — příprava, odeslání, příjem nabídek](Z_vydane_poptavky_rfq.md) · běží naostro (EVP260231) · Claude 18.7.
- [Přijaté poptávky (od zákazníka) — přehled, doklad, generování nabídky](Z_prijate_poptavky.md) · know-how vytěženo (přehled 504) · Claude 19.7.
- [Kalkulace rozvaděčů — Vize 1 + systém Velkých ceníků](Z_kalkulace_ceniky_vize1.md) · směrové rozhodnutí · Claude 18.7.

*(Další čísla přibývají, jak nalijeme Martiho vizi a stavíme.)*
