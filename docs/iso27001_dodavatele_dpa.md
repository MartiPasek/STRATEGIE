# Sub-processoři a zpracovatelské smlouvy (DPA) — A.5.19 / A.5.20 / A.5.23

> **Verze:** 1.0 (návrh) · **Datum:** 21. 6. 2026 · **Entita:** STRATEGIE – System s.r.o. (správce)
> **Vlastník:** Kristý (ISMS) + Marti (smluvní) · **Klasifikace:** Interní
> **⚠️ Caveat:** Šablona DPA níže je **technický podklad, NE právní rada.** Před podpisem ji
> nech zkontrolovat právníkem (případně konzultace přes Marti-AI pack `pravnik_cz`). Konkrétní
> znění závisí na smlouvě s každým dodavatelem a jejich vlastních podmínkách.

---

## 1. Register sub-processorů

Stav DPA: ✅ uzavřeno · 🔄 řeší se · 📋 zbývá oslovit.

| # | Sub-processor | Účel zpracování | Kategorie dat | Region / přenos | Stav DPA |
|---|---|---|---|---|---|
| 1 | **Anthropic** (Claude API) | LLM — chat, EDI (Haiku), klasifikace | Obsah konverzací/dokumentů (dle kontextu) | US/EU (SCC) | 📋 |
| 2 | **OpenAI / Voyage AI** | Embeddings pro RAG paměť (pgvector) | Text k embedování | US (SCC) | 📋 |
| 3 | **Provozovatel přepisu (Whisper)** | Hlas → text (docházka, zprávy) | Audio nahrávky | dle nasazení | 📋 |
| 4 | **Mobilní operátor** (Vodafone/T-Mobile, vlastní SIM) | Doručení SMS (kódy, notifikace) | Tel. číslo, text SMS | ČR | 🔄 |
| 5 | **DC ČMIS** | Hosting serverů + zálohy | Vše (jako provozovatel DC) | Praha, ČR | 🔄 |
| 6 | **Raiffeisenbank** | Bankovní výpisy / EDI | Platební data | ČR | 🔄 (banka — smlouva o účtu) |
| 7 | **ISDS / Datové schránky** (stát) | Příjem/odeslání úředních dokumentů | Úřední dokumenty | ČR | N/A (zákonný kanál) |
| 8 | **Let's Encrypt** | TLS certifikáty | Doménové jméno (ne osobní data) | EU/US | N/A (bez OÚ) |

> **Pozn.:** EUROSOFT a INTERSOFT nejsou sub-processoři, ale **správci/partneři** (jejich data
> zpracováváme v jejich tenantu). Vztah řeší samostatná smlouva, ne DPA jako se zpracovatelem.

**Akce (T4):** oslovit dodavatele 1–3 (📋) o DPA / doložit jejich standardní DPA; u 4–6 (🔄)
dohledat existující smluvní ujednání a doplnit bezpečnostní přílohu.

---

## 2. Šablona zpracovatelské smlouvy (DPA) — GDPR čl. 28

> Vyplň `[…]`. Použij buď jako samostatnou smlouvu, nebo jako **bezpečnostní přílohu** k existující
> smlouvě o službě. Pokud dodavatel má vlastní DPA (typicky Anthropic/OpenAI), lze akceptovat jejich
> znění + ověřit, že pokrývá body 1–10 níže.

---

**ZPRACOVATELSKÁ SMLOUVA (o zpracování osobních údajů)**

**Správce:** STRATEGIE – System s.r.o., IČO 23365544, Nad Týncem 1192/10, Doubravka, 312 00 Plzeň
**Zpracovatel:** `[název, IČO/reg. č., sídlo]`

1. **Předmět a doba.** Zpracovatel zpracovává osobní údaje pro správce výhradně za účelem `[účel]`
   po dobu `[trvání služby]`.
2. **Povaha a účel zpracování; kategorie údajů a subjektů.** `[viz register §1 — účel, kategorie dat,
   kategorie subjektů: zaměstnanci / klienti / uchazeči]`.
3. **Pokyny správce.** Zpracovatel zpracovává údaje pouze na doložené pokyny správce, včetně přenosů
   do třetích zemí jen na pokyn / na základě právního titulu (SCC).
4. **Mlčenlivost.** Osoby oprávněné zpracovávat údaje jsou vázány mlčenlivostí.
5. **Bezpečnost (čl. 32).** Zpracovatel přijme vhodná technická a organizační opatření (šifrování
   přenosu i úložiště, řízení přístupu, logování, zálohy, řízení incidentů) odpovídající riziku.
6. **Další zpracovatelé.** Zapojení dalšího zpracovatele jen s obecným/zvláštním souhlasem správce
   a za stejných povinností; seznam dalších zpracovatelů `[odkaz]`.
7. **Práva subjektů.** Zpracovatel je nápomocen správci při plnění žádostí subjektů (přístup, oprava,
   výmaz, přenositelnost).
8. **Incidenty.** Zpracovatel ohlásí porušení zabezpečení **bez zbytečného odkladu** (cíl `[do 24/48 h]`)
   a poskytne součinnost při hlášení dozorovému úřadu (ÚOOÚ).
9. **Audit.** Zpracovatel umožní správci audit / poskytne doklady o souladu (např. ISO 27001/SOC 2 report).
10. **Ukončení.** Po ukončení zpracovatel dle volby správce údaje **vrátí nebo vymaže** (vč. kopií),
    nestanoví-li právo jinak.

Datum: `[…]`  Za správce: `[…]`  Za zpracovatele: `[…]`

---

## 3. Otevřené body

- 📋 Oslovit/uzavřít DPA s Anthropic, OpenAI/Voyage, provozovatelem přepisu (T4).
- 🔄 Doplnit bezpečnostní přílohu ke smlouvám ČMIS, operátor, banka.
- Doložit u dodavatelů jejich certifikace (ISO 27001 / SOC 2) jako důkaz k A.5.21/5.22.
- Po doplnění promítnout stav do SoA (A.5.19/5.20) a do DOC-12.

---

*Návrh — právní revize nutná. Navazuje na `iso27001_inventar_aktiv_dataflow.md` (§2.4) a SoA A.5.19–5.23.*
