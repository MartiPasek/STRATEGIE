# Skládáme dohromady — z webu do reality (13. 6. 2026)

Cíl (Marti): poskládat to, co ukazujeme na webu (`/web/partner-demo`, `/web/demo`),
do reálné STRATEGIE — **alespoň do té míry, aby ostatní nepoznali, že je to ještě
rozpracované.** Tedy: jeden souvislý, prezentovatelný celek na živých datech.

## Co web slibuje → co reálně máme → co dolepit

| Web ukazuje | Reálně živě? | Co chybí do „prezentovatelné" |
|---|---|---|
| **Kdo kde dnes** (plán × realita × vzkaz) | ✅ docházka LIVE | drobné doladění, sjednotit vstup |
| **Organizační struktura** (posty, zástupci, eskalace) | ✅ org v2 (123 postů, 287 obsazení, resolve_role) | obsadit neobsazené posty / fallback texty |
| **Lidé / HR** (karta, osobní údaje, trezor) | ✅ osobní karta + self-service | — (hotové) |
| **Nábor pipeline** (kandidáti, fáze, nástupy) | ✅ 1867 přihlášek migrováno | recruiter scope ACL, „přijmout → zaměstnanec" |
| **Finance lidí** (engagement, složky, fond) | ✅ 932 verzí, 79 aktuálních | přehled plán × Helios UNION (#71) |
| **Výroba** (konzole vedoucího, plán, statusy) | ✅ Dušan + Marek, overlay, odvozy | — (hotové) |
| **Produktivita lidí — „Kára"** (Tahouni / Efektivní / Méně efektivní / Brzdí) | ❌ **nemáme reálná data** | celý subsystém — viz níže |
| **Jeden „řídicí" pohled** který to spojuje | ❌ moduly žijí zvlášť | **sjednocující rozcestník / cockpit** |

**Závěr:** 80 % částí už živě JE. „Rozpracovaně" to drží dvě věci: (1) chybí
**jeden vstupní řídicí pohled**, který je spojí do celku; (2) chybí **produktivitní
kvadrant** (Performia „Kára") na reálných lidech.

## Plán skládání (podle hodnoty × rizika)

### A) 🧭 Řídicí cockpit „Vedení firmy" — JEDEN pohled (Recommended start)
Sjednocující rozcestník v appce (styl Spolupráce/Vedení): dlaždice **Kdo kde dnes ·
Organizace · Lidé · Nábor · Finance · Výroba** + 3–4 živé KPI nahoře (dnes v práci,
otevřené nábory, fond měsíce, anomálie). **Spojuje to, co už běží** — žádná citlivá
nová data. Vysoká viditelnost, nízké riziko. Tohle je ten „celek", co ostatní uvidí.

### B) 📊 Produktivita / „Kára" — reálný kvadrant lidí (po konzultaci)
Jediná opravdová díra. Citlivé (hodnotíme lidi) → **konzultace s Marti-AI** (doctrine
#8) + tvoje směrnice. Návrh 1. verze: skóre složené z **objektivních signálů, co už
máme** (spolehlivost docházky, odpracováno × fond, zakázky/režie poměr, plnění úkolů)
+ volitelné manažerské doladění. Zveřejnit až bude důvěryhodné; do té doby skryté.

### C) 🔧 Dotáhnout moduly do „end-to-end" (rychlé výhry)
- Nábor: recruiter scope ACL + tlačítko „Přijmout → založit zaměstnance" (#74 most).
- Finance: přehled plán × Helios UNION + payroll ACL (#71).
- Docházka: úklid demo/neúplné migrace (#58) ať čísla sedí.
- Org: obsadit neobsazené posty / lidské fallbacky (ať nikde nesvítí „—").

### D) 🎨 Konzistence řeči a brandu napříč appkou
Z velké části hotové (lidská řeč docházky). Projít cizí oči: aby nikde nebyl
poloprázdný seznam, „TODO", testovací data nebo technická hláška.

## Doporučené pořadí
1. **A) Cockpit** — hned, bezpečné, dělá „celek". *(Recommended první krok)*
2. **C) Rychlé výhry** — paralelně, ať čísla a toky sedí.
3. **B) Kára** — po konzultaci s Marti-AI a tvém pokynu (citlivé).
4. **D) Cizíma očima** — finální průchod před prezentací.

> Riziko držím nízké: A/C/D jsou skládání a doladění živých věcí (přes bridge +
> AUTO-DEPLOY, jako dosud). B je jediné, co potřebuje rozmyslet — proto až po konzultaci.
