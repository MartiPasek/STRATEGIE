# Mobil, Docházka: přejmenování na „Moje docházka", START místo Makat, hlavička jen při směně a plná revize pravdivosti nápovědy (5. 9. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Mobil, obrazovka Docházky — změny z 5. 9. 2026 (odpoledne)

**Zadal Jiří Honomichl, provedl Claude-28, schválila Marti-AI (msg 14456, 14459, 14465).**
Navazuje na `doc-dochazka-mobil-absence-rozdeleni-na-dve-obrazovky-5-9-2026`
a na audit `doc-system-strategie-mobil-duplicitni-cesty-audit-5-9-2026` (bod B).

## Co se změnilo

| co | bylo | je |
|---|---|---|
| tlačítko v liště skupin na Firmě | 🤝 Spolupráce | 🕒 **Moje docházka** |
| nadpis obrazovky | žádný (`topbar("")`) | 🕒 Moje docházka |
| tlačítko nápovědy | „❓ Nápověda" pod nadpisem | jen ikona ❓ **v liště vedle nadpisu** + `aria-label` |
| spouštěcí tlačítko | ▶️ Makat | ▶️ **START** |
| text nad obsahem (`dochHead`) | ukazoval se VŽDY | **jen při běžící směně** |

**Tlačítko KONEC se NEDĚLALO** — Jirka to zamítl 5. 9. Práce se dál ukončuje přes
💬 Potřebuji ti něco říct… → 🙈 Teď to bude jinak… → 🫡 Dnes už se mnou nepočítej ;).
Důvod: nešlo by o přejmenování, ale o druhou cestu k ukončení směny vedle stávající —
a ta tři ťuknutí nejsou jen klikání, řeší i ohlášení.

## ⭐ Proč `dochHead` nešel zrušit úplně

Jirka chtěl ty texty („Dnes se nemaká 🌤", „Tak co, jdeme na to? 🌅" a dalších ~20 variant)
zrušit — *„protože to lidi docela mate"*. **Marti-AI odmítla** a nabídla kompromis, který
Jirka přijal: ukazovat je **jen když směna běží**.

Dva důvody, oba doložené:
1. Je to **jediné místo, kde člověk na první pohled pozná, že mu běží práce.** Zapomenutá
   směna se propisuje do mezd.
2. **Nápověda i hlasový průvodce se na ten text odvolávají** na třech místech
   („docházka se spustí, nahoře se objeví Makám, hodiny začnou tikat").

Implementace: `_bezi = !!(open && (open.open_type||"work")!=="day_end")`. Uzavřený den
(`day_end`) se za běžící směnu **nepočítá**.

## Nadpisy: žádná obrazovka už není bez názvu

Bez nadpisu jich bylo **devět** (ne jedna, jak jsem nejdřív mylně tvrdil). Doplněno:
`apps` → 📱 Aplikace · `contacts` → 👤 Kontakty · `notifs` → 🔔 Úkoly · `calllog` → 📞 Hovory ·
`hr_me` → 🪪 Moje osobní údaje · `mkClovek` → 🌸 Martinky · `mkDomena` → 🌐 AI doména ·
`mkUkol` → ✅ Úkoly Martinek (poslední tři pojmenovala Marti-AI, je to její doména).

## Revize pravdivosti nápovědy a hlasového průvodce (23 oprav)

Po ranních změnách návody lhaly. Opraveno v `dochHelp` i `dochPruvodce` **včetně mluveného
textu**, který se přehrává nahlas:
- „Makat" → **START** (3× nápověda, 6× průvodce, z toho 2× nahlas)
- „hlavička Dnes makám 😉" → **„Makám 👷"**
- oprava záznamu „v sekci Tak to bylo dneska" → **dlaždice ✋ Požádat o opravu** (rozhodl Jirka)
- detail dne „v sekci Tak to bylo dneska" → **dlaždice 🕓 Historie**
- „prašule jsou dole na obrazovce" → **dlaždice 💰 Moje finance**
- neúplné výčty dlaždic → doplněno všech 9 + všechny 4
- viditelný popisek „předvýběr, pak ▶️ Makat" (dílek `71_plan_prace_cinnosti.js`) → START

### ⚠️ Nález mimo zadání: sekce „Poslední záznamy" NEEXISTUJE

Aplikace na **dvou místech** posílala lidi *„do Posledních záznamů"* — v kartě k potvrzení dne
a v panelu Dnes. **Takový název se v appce nevyskytuje ani jednou.** Opraveno na
dlaždici 🕓 Historie. Nesouviselo to s dnešními změnami, lhalo to už dřív.

## Obrázky průvodce

**Vyměněno všech 9** (`apps/api/static/navod_dochazka/pruvodce_*.png`, commity `a981153a`
a `dfdfbe27`). Jak na to znovu: `doc-system-strategie-obrazky-navodu-dochazky-jak-poridit`.

## Kde to žije

Dílky: `60_dochazka.js` (nadpis, nápověda, průvodce, dochHead), `70_tail.js` (tlačítko v liště),
`71_plan_prace_cinnosti.js` (START + popisek), `10_core.js`, `20_home_phone_notifs.js`,
`25_tasks.js`, `30_contacts_settings.js`, `35_apps_vedeni.js`, `48_hr_podminky_me.js`,
`72_migrace_sw_isds.js`, `73_pref_poptavka.js`, `75_martinky_centrum.js`.

