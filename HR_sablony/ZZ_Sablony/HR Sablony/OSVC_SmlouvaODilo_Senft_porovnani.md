# Rámcová smlouva o dílo (OSVČ) — revize dle Senfta + finální šablony

Porovnání Senftova komentáře (8 znaků švarcsystému) s nahranými verzemi
(**Výroba / elektromontér V7** 18. 11. 2025, **PLC programátor V8** 19. 11. 2025)
a co dělá **finální šablona**.

> Zkratky stavu: ✅ už ošetřeno · ⚠️ zbývá riziko · 🔧 finální šablona opraví

| # | Znak švarcsystému | Senftův doporučený směr | Výroba V7 | PLC V8 | Finální šablona |
|---|---|---|---|---|---|
| 1 | **Garance obratu + 30 dní „volna"** (Čl. IV/3) | Odstranit; úhrada vždy za konkrétní dílo | ✅ není | ✅ není | Ponechá pryč — Čl. IV jen „zajišťovat informace" |
| 2 | **Práce „podle příkazů"** (Čl. V/2) | „v souladu se schváleným zadáním a technickou specifikací; plná odpovědnost zhotovitele" | ✅ opraveno | ⚠️ **stále „příkazy"** | 🔧 sjednoceno na znění V7 (zadání + tech. specifikace + plná odpovědnost) — i v Čl. IX (záruka) |
| 3 | **Rozsah díla = rutinní výčet** (Čl. II/2,4) | Jen konkrétní finální výstupy (kód, dokumentace, výrobní operace) | ✅ konkrétní (výrobní operace) | ✅ konkrétní (SW kód + dokumentace) | Dílo dle varianty (Výroba/PLC/Kancelář). **Pozn.: „zaškolování zaměstnanců" (Čl. II/3, V/6) Senft označil jako rizikové** — necháno jako okrajové, ⚠️ k uvážení vypustit |
| 4 | **Work Report se Start/End time + docházka** (Čl. VII/5) | Platit za výsledek, ne za čas; WR jen pro výpočet ceny | ✅ není | ✅ není | Ponechá pryč — fakturace z nabídky / objednávky |
| 5 | **Vnitřní předpisy + firemní kultura** (Čl. V/7) | Jen BOZP + GDPR/mlčenlivost v nutném rozsahu; nevázán interními předpisy | ✅ čisté | ⚠️ částečně (zmiňuje vnitřní předpisy) | 🔧 sjednoceno na čisté znění V7 (BOZP + GDPR, nevázán interními předpisy) |
| 6 | **Konkurence 3 roky, nekompenzovaná** (Čl. V/5) | Max 1 rok po skončení, jen konkrétně určení zákazníci | ✅ 1 rok, strategičtí | ⚠️ **stále 3 roky** | 🔧 1 rok, jen písemně označení strategičtí zákazníci |
| 7 | **Vystupuje jako zástupce objednatele** (Čl. V/5) | Jedná vlastním jménem a na vlastní riziko; zastupování jen s písemným pověřením | ✅ vlastním jménem | ✅ vlastním jménem | Ponechá — vlastním jménem a na vlastní podnikatelské riziko |
| 8 | **Pojištění odpovědnosti za zhotovitele** (Čl. IV/2) | Odstranit; pojištění si platí zhotovitel sám | ✅ není | ✅ není | Ponechá pryč |

## Závěr
- **Výroba (V7)** je prakticky finální — splňuje všech 8 bodů. Šablona = jeho znění + house styl.
- **PLC (V8)** má **3 zbytkové švarc slabiny** (body 2, 5, 6) — finální šablona je opraví podle Senfta.
- **Kancelář** = nová varianta v témž duchu; liší se jen **vymezením díla** (Čl. II). **Pozor:** kancelářská/administrativní práce jako „dílo" je švarc-rizikovější (Senftův bod 3) → dílo musí být konkrétní výstup, ne rutinní agenda. **Vymezení díla pro kancelář nechat schválit Senftem.**

## Doporučení k doplnění (pro Senfta)
- **PLC — autorská/majetková práva ke kódu:** nahrané znění explicitní postoupení práv k vytvořenému programovému kódu na objednatele neobsahuje. U PLC programátora se hodí doplnit (s Ondřejem).
- **Zaškolování** (bod 3) — zvážit vypuštění, nebo ponechat jako vedlejší plnění.

## Varianty finální šablony (house styl, EC i ES)
- `SmlouvaODilo_OSVC_Vyroba_SABLONA` — výrobní operace (rozvaděče)
- `SmlouvaODilo_OSVC_PLC_SABLONA` — software kód + dokumentace (+ návrh IP klauzule k revizi)
- `SmlouvaODilo_OSVC_Kancelar_SABLONA` — kancelářské výstupy (vymezení díla k revizi Senftem)

---

## Dodatek — PLC‑specifický komentář Senfta (9 bodů) — zapracováno

PLC programátor dostal vlastní revizi. Body navíc proti obecné sadě a jak je řeší **PLC šablona**:

| # | Bod (PLC) | Řešení v PLC šabloně |
|---|---|---|
| 1 | „Příkazy" v Čl. V/2 i Čl. IX | 🔧 nahrazeno „zadání + technická specifikace, plná odpovědnost" (oba články) |
| 2 | Vnitřní předpisy / Etický kodex (Čl. V/7) | 🔧 jen BOZP + GDPR; „není vázán interními organizačními ani personálními předpisy" |
| 3 | Garance obratu + 30 dní volna (Čl. IV/3) | ✅ není |
| 4 | **Dílo = administrativa** (poptávka, fakturace, **školení**) | 🔧 dílo = jen SW kód + dokumentace; **zaškolování z PLC vypuštěno** (Čl. II i Čl. V) |
| 5 | Zástupce objednatele (Čl. V/5) | 🔧 „vlastním jménem, **nikoli jako zástupce**" |
| 6 | Konkurence 3 roky + pokuta 50 % | 🔧 **1 rok**, jen strategičtí; žádná 50% pokuta |
| 7 | **Subdodávky jen se souhlasem** (Čl. Va/11) | 🔧 PLC: subdodavatelé **bez souhlasu**, zhotovitel nese plnou odpovědnost |
| 8 | Pojištění za zhotovitele (Čl. IV/2) | ✅ není |
| 9 | **Návrat všech podkladů, zákaz kopií** (Čl. Va/5) | 🔧 PLC: právo **ponechat kopie pro záruku** + vlastní pracovní poznámky/nástroje bez obch. tajemství |

**Rozdíl variant:** Výroba a Kancelář drží znění elektromontéra V7 (subdodávky se souhlasem, standardní návrat podkladů, zaškolování ponecháno). PLC má relaxace dle své revize (bez souhlasu, ponechání kopií, bez zaškolování) + návrh IP klauzule.

## Pozn. ke staré generické šabloně
Původní `{EC|ES}_SmlouvaODilo_OSVC_SABLONA.docx` (slabá obecná verze) je **nahrazena** třemi variantami výše — je vhodné ji smazat (mount nedovolil automaticky).

---

## Dodatek — elektromontérský komentář Senfta (5 bodů) — stav

Potvrzení směru. **Výroba šablona (= čisté V7) už všech 5 bodů splňuje:**

| # | Bod (elektromontér) | Stav ve Výroba šabloně |
|---|---|---|
| 1 | „Příkazy" (Čl. V/2) | ✅ „zadání + technická specifikace, plná odpovědnost" |
| 2 | Vnitřní předpisy / Etický kodex / Firemní kultura (Čl. V/7) | ✅ jen BOZP + GDPR; „není vázán interními organizačními ani personálními předpisy" |
| 3 | Zástupce objednatele (Čl. V/5) | ✅ „vlastním jménem a na vlastní riziko, nikoli jako zástupce" |
| 4 | Garance obratu + 30 dní volna (Čl. IV/3) | ✅ není (odstraněno) — **ale viz otázka níže** |
| 5 | Konkurence 3 roky (Čl. V/5) | ✅ **1 rok**, jen strategičtí, přesunuto do čl. Va — **viz pozn. níže** |

### Dvě otevřené věci (rozhodnutí / vstup od vás)
- **Bod 4 — Senft se ptá: jaký byl důvod garance obratu + 30 dní volna?** Potřebuje to vědět, aby případně připravil měkčí náhradní formulaci (např. závazek objednatele „snažit se zajistit dostatek zakázek"). Teď je ustanovení úplně vypuštěné (jeho preferovaná varianta). → **Napiš Senftovi důvod, nebo potvrď, že zůstane vypuštěné.**
- **Bod 5 — Senft doporučuje, aby konkurenční doložka byla ideálně placená.** Teď je nekompenzovaná (1 rok, strategičtí). → **Rozhodnutí EUROSOFTu:** ponechat nekompenzovanou, nebo doplnit peněžité vyrovnání (pak doplním do čl. Va volitelnou klauzuli).
