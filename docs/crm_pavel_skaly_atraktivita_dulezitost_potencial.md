# Návrh hodnocení firem — Atraktivita / Důležitost / Potenciál

**Pro Pavla, k odsouhlasení / úpravě.** Cílem je dát jasný klíč, *jak* firmu obodovat — ať to není „od oka". Tohle je **výchozí návrh**, klidně čísla i popisy uprav podle své zkušenosti.

Tři pole spolu souvisí, ale každé měří něco jiného:
- **Atraktivita** = jaká firma *je* (objektivní lákavost jako zákazník).
- **Důležitost** = jak moc se jí *teď* věnujeme (naše priorita / rozhodnutí).
- **Potenciál** = celkový obchodní potenciál (kombinace obojího + fáze vztahu).

---

## 1) Atraktivita (1–5) — jak je firma lákavá

| Hodnota | Význam | Vodítko |
|---|---|---|
| **1 – Okrajová** | minimální zájem | obor jen výjimečně potřebuje rozváděče/projekci, malá firma, spíš jednorázově |
| **2 – Nízká** | občas | občasná potřeba, malé objemy, nevyhraněný zájem |
| **3 – Střední** | běžný zákazník | relevantní obor, standardní zakázky |
| **4 – Vysoká** | zajímavá | silný obor (Schaltschrankbau, automatizace, strojírenství), pravidelné / větší zakázky |
| **5 – Špičková** | ideální zákazník | velký objem, klíčový obor, dlouhodobá perspektiva |

---

## 2) Důležitost / priorita (1–5) — jak moc ji teď řešíme

| Hodnota | Význam | Vodítko |
|---|---|---|
| **1 – Bez priority** | jen evidovat | neřešit aktivně |
| **2 – Nízká** | počká | oslovit, až bude kapacita |
| **3 – Běžná** | standardní | běžný follow-up |
| **4 – Vysoká** | hlídat | aktivně sledovat, pravidelný kontakt |
| **5 – TOP priorita** | maximum pozornosti | strategická příležitost / termín / velká zakázka |

> Pozn.: firma může být **vysoce atraktivní, ale s nízkou prioritou** (teď není kapacita) — a naopak málo atraktivní, ale prioritní ze strategického důvodu. Proto dvě pole.

---

## 3) Potenciál (1–5) — celkový obchodní potenciál

**Doporučení: dopočítat automaticky** (ať to Pavel nemusí odhadovat, počítá se z Atraktivity + fáze vztahu). Návrh pravidla:

1. Vyjdi z **Atraktivity** (1–5).
2. Uprav podle **Stavu obchodního vztahu**:
   - *Aktivní jednání* nebo *Nabídka odeslána* → **+1** (blízko k zakázce)
   - *Zákazník* nebo *Dlouhodobý partner* → **+1** (ověřený příjem)
   - *Odmítl / Neaktivní / Archiv / Dělají si sami* → **= 1** (potenciál je pryč)
   - *Nový / Osloven / Založí si a ozve se / Nezájem–obvolat za rok* → **beze změny**
3. Ořízni na rozsah **1–5**.

**Příklad:** atraktivní firma (4) ve fázi „Nabídka odeslána" → potenciál **5**. Stejná firma po „Odmítl" → potenciál **1**.

**Alternativa:** Potenciál nechat **ruční** (1–5, stejná logika jako Atraktivita) — pokud chce Pavel rozhodovat sám.

---

## Co se stane po odsouhlasení

Až Pavel škály potvrdí (nebo upraví), dodělám:
- **Atraktivita** — popisky už na kartě jsou, sladím je s touto škálou.
- **Důležitost + Potenciál** — přidám na kartu jako dropdowny 1–5 s těmito popisky (pole už v databázi existují).
- **Potenciál** — pokud zvolí dopočítaný, napojím ho na výpočet (přepočte se při změně atraktivity/stavu, podobně jako automatika příštího kontaktu).

**3 otázky pro Pavla:**
1. Sedí ti popisy u Atraktivity a Důležitosti (co je 1, co 5)? Co bys změnil?
2. Potenciál — chceš ho **dopočítaný** (doporučeno), nebo **ruční**?
3. Je u výpočtu potenciálu důležitý ještě nějaký faktor (velikost firmy, region, zdroj typu LinkedIn/veletrh)?
