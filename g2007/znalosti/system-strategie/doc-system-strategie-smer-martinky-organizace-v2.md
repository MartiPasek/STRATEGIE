# SMER (Marti 3.8.2026): Organizace Martinek v2 - Martinka vlastni svou oblast, Maminka prideluje dle schopnosti

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Zavazny smer od Marti Paska (3.8.2026 dopoledne, po zprovozneni motoru v1)

Motor orchestrace v1 (ukol -> beh -> nastroje -> potreby -> schvaleni; viz doc-system-strategie-martinky-orchestrace-v1-nasazeno a navazujici) je INFRASTRUKTURA. Tento dokument definuje ORGANIZACI nad ni - dva smery, ktere Marti zadal:

### Smer 1: MAMINKA PRIDELUJE PRACI PODLE SCHOPNOSTI
Maminka (Marti-AI v roli supervisora) ma mit PREHLED o tom, co ktera Martinka umi, a pridelovat praci ona - ne clovek dropdownem. K tomu:
- KATALOG SCHOPNOSTI: kazda Martinka (=domena v g2007.tool_domain) ma strukturovany PROFIL: co umim, jake typy ukolu mi patri, priklady, jake mam nastroje, kdo je muj clovek-vlastnik. (Dnes rozptylene: nazev + vybava_prompt + globalni tool whitelist.)
- NASTROJE PER DOMENA: tool-smycka dispatchera ma cist g2007.domain_nastroj (existuje, nevyuziva se) misto globalniho whitelistu kategorie martinky - kalkulacni Martinka ma kalkulacku, fakturacni ji nema.
- KROK PRIDELENI: ukol zadany BEZ domeny (od cloveka, z emailu, od automatu ktery nevi cimu) -> stav 'nezarazen' -> beh Maminky vybere Martinku dle katalogu; kdyz zadna neumi -> potreba/eskalace cloveku ("na tohle nemam Martinku - zalozime novou?").

### Smer 2: MARTINKA VLASTNI SVOU OBLAST (napojena na automaty)
Kazda Martinka je trvale ZODPOVEDNA za svou cast prace - nezije jen v okamziku behu ukolu:
- Domena ma SVUJ AUTOMAT (oci do oblasti: hlida poptavky/terminy/chyby/stav, stavi status_block - Pilir B #280).
- Kdyz automat najde praci nebo problem, ZAKLADA UKOL SVE MARTINCE (helper napr. automat_zaloz_ukol -> martinka_ukol_zaloz) - NE primo cloveku, NE Marti-AI. Eskalacni zebrik #280 to uz predvida (Stupen 2 = prislusna Martinka), ale napojeni na ukolovy system g2007.ukol zatim NEEXISTUJE - eskalace dnes tecou mimo ukoly.
- Zebrik pak: automat -> ukol Martince -> (nezvladne: potreba) -> Maminka -> clovek. Kazdy stupen resi co umi, vys jde jen zbytek (poschodovy stroj, doc-go-210).

### Cilovy obrazek
MARTINKA (=domena) trvale ma: PROFIL (co umim) | VYBAVU (know-how od Maminky) | NASTROJE (sve, per domena) | AUTOMAT (oci). Prace pritéka: od automatu + od Maminky + od lidi.
MAMINKA: rozdeluje nezarazene dle katalogu | rozviji vybavu (maminka_vybav) | hlida potreby (aktivni wake) a eskaluje.
MARTI/LIDE: vidi celek, schvaluji vysledky a nove schopnosti/nastroje (eskalacni pravidla doc-system-strategie-marti-ai-martinka-eskalacni-pravidla).

### Porad implementace (dohodnuto s Martim)
1. PROFIL Martinky: tool_domain.schopnosti + prepnuti tool-smycky na domain_nastroj (katalog = podminka vseho dalsiho).
2. MAMINKA-ROZDELOVACKA: stav 'nezarazen' + beh maminka_pridel dle katalogu.
3. AUTOMAT->UKOL: helper pro automaty + uprava zebriku (cast patri do vecerniho deploy okna 3.8.).
Prvni saada profilu: upresni Marti (kandidati: poptavky, nabidky, kalkulace_obecna, kalkulace_specificka, faktury).

_Zapsal C23 dle zadani Marti 3.8.2026. Navazuje: #280 (architektura), orchestrace-v1, maminka-vybava-v1, vlakna-chat-hitl-v1, aktivni-probuzeni-v1, tool-smycka-kalkulace-v1._

