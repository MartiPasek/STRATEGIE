# 🗺️ MAPA směrnic — absolutní přehled a pořádek (řada přístupnost AI)

> **Autor: Claude (ID23), 1. 7. 2026.** Master index celého firemního know-how (633 aktivních
> směrnic + 632 příloh s textem) — Martiho zadání: *„je to srdce firmy a zaslouží si to tvou
> velkou pozornost."* Řada **AI** = orientace pro Claude + Marti-AI. Hledej přes **`@@KB <dotaz> | 3`**.
> Detaily domén v samostatných `docs/*.md` (viz §5). Živé — doplňuje se, jak čtu dál.

## 1. Co je srdce firmy

EUROSOFT-Control + INTERSOFT-Automation (IAP) = **zakázková výroba rozváděčů** pro (převážně
německé) OEM. Srdce = **nasbírané výrobní know-how per zákazník** + firemní STANDARD + podpůrné
procesy (kvalita, HR, finance/clo, BOZP, IT, nákup, doprava). Vše je ve směrnicích — a teď v RAG.

## 2. Taxonomie — 633 aktivních směrnic ve 12 doménách

| # | Doména | Počet | Co obsahuje |
|---|---|---|---|
| 1 | **Výroba rozvaděčů** | **241** | jádro — per-zákazník recepty + STANDARD baseline (viz §3) |
| 12 | Ostatní / administrativa | 237 | 102 formulářů + 98 obecných směrnic + 60 nápověd + 37 informací (org, jednací řády, IT nápovědy) — k dalšímu třídění |
| 4 | Finance / clo / DPH | 35 | celní osvobození, DPH v EU, fakturace, ceny, pokladna |
| 3 | Personalistika / HR | 23 | mzdy, docházka, dovolená, nástup, pracovní poměr, cestovné, stravné |
| 2 | Kvalita / zkoušky | 19 | EN 61439-2, deník zkoušek, revize, reklamace, kontrola |
| 10 | Obchod / nabídky | 19 | poptávka, kalkulace, nabídka, zakázka (viz SRDCE FIRMY) |
| 11 | IT / bezpečnost | 19 | software, data, GDPR, ISO 27001, hesla, zálohování |
| 5 | BOZP / PO | 18 | bezpečnost práce, požární ochrana, první pomoc, OOPP |
| 7 | Nákup / sklad | 11 | objednávání, sklad, materiál, dodavatelé, VKM |
| 9 | Školení / kvalifikace | 6 | školení, kvalifikační zkoušky, oprávnění |
| 6 | Ekologie / odpady | 3 | odpady, likvidace, životní prostředí |
| 8 | Doprava / expedice | 2 | odvoz, balení, přeprava |

Typy napříč: Směrnice 379 · Formulář 133 · Nápověda 60 · Informace 43 · Školení 16 · Rozhodnutí 2.
Přístupnost: Veřejná 379 · Vedoucí 184 · Plná 60 · Interní 5 · Vedení 5 (+ řada AI = naše).

## 3. ❤️ Jádro — Výroba rozvaděčů (241 směrnic)

### 3a. Per-zákazník recepty (kolik témat má každý)

| Zákazník | Témat | | Zákazník | Témat |
|---|---|---|---|---|
| **JUNKER** | **50** | | STRIKO | 8 |
| STANDARD (baseline) | 42 | | AUTKOM | 8 |
| **KOHLBACH** | 24 | | ZF | 6 |
| ISIMAT | 20 | | ABSAUGWERK | 6 |
| FOUNDRY4 | 17 | | SIEMENS | 3 |
| SENCO | 10 | | MAGNAFLUX | 2 |
| DÜCKER | 9 | | RITTMEYER | 2 |
| MOLINS | 9 | | + menší (SMS, XELLA…) | 1 |
| INTERSOFT | 8 | | | |

➡️ **Model:** STANDARD = obecný firemní recept; každý zákazník = **odchylky/specifika** od STANDARDu.
JUNKER je nejdetailnější vztah (50 témat). Nová zakázka od známého zákazníka → jeho balík je návod.

### 3b. STANDARD — kanonický procesní checklist (výběr z 42 témat)

Mechanika skříně a desky: pospojení montážní desky · pospojení rozvaděče · měděná přípojnice ·
mosazná lišta pro PE/PEN/N · FLEXIBAR lamelová sběrnice · krytky soklů VX · obsluha hydraulického
prostřihovadla häwa. Přístroje: montáž hlavního vypínače Siemens · dutinky v jističích řady SIE ·
pojistkové odpojovače (hodnota proudu) · konektory osvětlení Rittal/Richter. Svorky/vodiče (VKM):
barevné značení žil vodičů · koncové krytky PE svorky · kryt přívodní svorkovnice · kontrola a
objednávání VKM materiálu · označení utažených kontaktů. Dveře: dveře rozvaděče – pravidla připojení.
Výstup: balení rozvaděče (UPS) · odeslání měřicích/zkušebních protokolů, prohlášení, dokumentace.

To jsou dimenze „receptu" — každý zákazník některé mění. Detail v `docs/Rozvadece.md` a `@@KB … | 3`.

## 4. Podpůrné domény (stručně — deep-dive v samostatných AI směrnicích)

- **Kvalita/zkoušky:** EN 61439-2 (izolační + ochranný vodič, protokoly), deník zkoušek / hlášení
  chyb, revize, reklamace, prohlášení o shodě.
- **Personalistika/HR:** mzdy, docházka, dovolená, nástup/výstup, cestovní náhrady, stravné.
- **Finance/clo/DPH:** kódy osvobození od cla, uplatňování DPH v EU (export!), fakturace, ceny, pokladna.
- **BOZP/PO:** bezpečnost práce, PO, první pomoc, OOPP, úrazy.
- **IT/bezpečnost:** software, data, GDPR, ISO 27001, hesla, zálohování (napojení na ISO cockpit).
- **Nákup/sklad:** objednávání, sklad, dodavatelé (Rittal/Siemens/Rockwell/Schrack/Phoenix), VKM.
- **Doprava/expedice, Ekologie/odpady, Školení/kvalifikace** — menší, ale kompletní.

## 5. Řada AI — znalostní mapa (co píšu jako orientaci)

| Dokument | Stav | Obsah |
|---|---|---|
| `MAPA_smernic.md` (tato) | ✅ | master index + taxonomie + jádro |
| `Rozvadece.md` | ✅ | výroba rozvaděčů — tok procesu + slovník + postřehy |
| `srdce_firmy_kalkulace_nabidky_analyza.md` | ✅ | kalkulace/nabídka (koeficient→VKM+hodiny), SRDCE FIRMY |
| `smernice_rag_navrh.md` | ✅ | jak RAG funguje (@@SMSYNC/@@SMFILES/@@KB/@@KBADD) |
| `Zakaznici.md` | ⏳ | recept per zákazník (JUNKER, KOHLBACH, ISIMAT, FOUNDRY4…) |
| `Kvalita_zkousky.md` | ⏳ | EN 61439-2 checklist, deník zkoušek, reklamace |
| `Personalistika.md` | ⏳ | HR procesy (mzdy/docházka/nástup…) |
| `Finance_clo_dph.md` | ⏳ | clo/DPH při exportu, fakturace |
| `BOZP_IT_ostatni.md` | ⏳ | BOZP/PO, IT/ISO 27001, nákup, doprava |

## 6. Jak s tím pracovat (Claude + Marti-AI)

- **`@@KB <dotaz> | 3`** — hledá napříč všemi popisy + přílohami + řadou AI.
- Nové poznatky → připiš do příslušného `docs/*.md` → `@@KBADD <key> | <nazev> | <popis>` (přegeneruje RAG řádek).
- **Postřeh:** taxonomie je základ „pořádku" — další krok je doplnit ke každé směrnici `kategorie`
  (doména) do `kb_smernice` a přidat UI dlaždici „📚 Znalostní báze" s filtrem po doménách.
- **Datová kvalita:** 632/702 příloh má čistý text (90 %). `~$*.doc` = Wordí zámky (filtrovat).

— Claude (ID23) 🗺️🔌📚
