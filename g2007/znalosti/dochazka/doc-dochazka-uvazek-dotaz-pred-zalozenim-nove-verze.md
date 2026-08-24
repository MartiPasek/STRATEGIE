# Změna úvazku se ptá, než založí novou verzi smlouvy (22. 8. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

**Zadal Jirka Honomichl 22. 8. 2026, schválila Marti-AI (souhlas s modelem i s atomickým nasazením). Nasadil Claude-28.**

## Co se změnilo

Změna týdenního úvazku dál **zakládá novou verzi** `tenant.engagement` (důvod z 19. 8. 2026 — mzdy za dřívější měsíce musí zůstat na starém úvazku — **platí beze změny**). Nově se ale na to systém **nejdřív zeptá**:

> Změnou úvazku (40 h/týd → 37,5 h/týd) se založí NOVÝ ZÁZNAM podmínek, úvazku a smlouvy s platností od 22.08.2026. Dosavadní záznam zůstane v historii. Chceš pokračovat?

Jirkovo zadání doslova: *„pokud někdo bude měnit úvazek, musí ho to upozornit, pozor zakládáš nový záznam v tabulce pro podmínky, úvazky a smlouvy. Chceš pokračovat? Ano/Ne."*

## Jak je to postavené — pravidlo je na JEDNOM místě

`g2007.python / uvazek_zapis` (dnes v9, tehdy v8) má nový parametr **`potvrzeno`**. Když se hodnota liší a `potvrzeno` není pravda, funkce **nic nezapíše** a vrátí:

```
{"ok": False, "potvrdit": True, "otazka": "<text>", "z": <stará>, "na": <nová>, "plati_od": "<ISO>"}
```

Do té chvíle skript jen **čte**, takže „Ne" nezanechá vůbec nic (žádný rollback není potřeba).

Tři volající parametr jen propouštějí a otázku posílají na obrazovku — **žádný z nich si ji neformuluje sám**, aby zněla všude stejně a příští nová obrazovka ji dostala automaticky (doporučila Marti-AI):

| kus kódu | verze | co dělá |
|---|---|---|
| `uvazek_zapis` | 9 | drží pravidlo i text otázky |
| `hr_conditions_save` | 9 | karta zaměstnance (ERP) i Moje podmínky (mobil) |
| `mzdy_c_smlouva_save` | 5 | mzdová smlouva |
| `plan_my_uvazek_save` | 4 | plán práce (mobil) |

Obrazovky: `apps/api/static/karta_zamestnance.html` (git, commit `6ef04381`), `48_hr_podminky_me.js` a `71_plan_prace_cinnosti.js` (oba `g2007.soubor`, mobil publikován).

**⚠️ V mobilu se nesmí použít `window.confirm`** — v nativní appce (Android i iOS) JS dialogy mlčí a uživatel nic neuvidí (past z 11. 8. 2026, popsaná přímo v dílku 48). Proto je v dílku 48 na úrovni fragmentu deklarovaný vlastní DOM dialog **`_potvrdNovyZaznam(text, onHotovo)`**; dílek 71 ho volá přes sdílený closure (fragmenty jsou jedna obalová funkce, deklarace se hoistují). Kdo přidá další obrazovku v mobilu, ať volá jeho, ne `confirm`.

## Připraveno, zatím nepoužité: `tenant.engagement_at(employee_id, datum)`

Sdílené „okno do minulosti" (navrhla Marti-AI 22. 8. 2026): vrátí řádek pracovního vztahu platný k datu, **jeden na firmu** (člověk může mít víc souběžných poměrů). Určeno k tomu, aby si každá obrazovka nestavěla vlastní logiku výběru verze.

Model platnosti: **prázdné `valid_to` znamená „platí dál bez omezení"** (rozhodl Jirka 22. 8. 2026), proto se verze vybírá podle `valid_from` sestupně, ne podle intervalu — historické řádky mají `valid_to` prázdné taky (858 z 939). Vyplněné `valid_to` má přednost.

## ✅ Cesta po „Ano" JE ověřená (24. 8. 2026)

*(Do 24. 8. 2026 tu stálo „není odzkoušená — vyžaduje skutečný zápis do ostrých dat". Už neplatí.)*

Odzkoušeno naostro na Jirkovi (poměr 926) a hned beze zbytku uklizeno. Porovnáno **všech 49 sloupců** staré a nové verze — lišily se jen `id`, `valid_from`, `is_current`, `note`, `created_at` a `ec_id`; **všech 16 podmínek se opsalo beze změny**. Mzdové složky se zkopírovaly (1 ks) v původní výši, zprávy Petře a Šárce vznikly a byly smazané dřív, než se doručily.

Demo účet použít pořád nejde (`Demo Uzivatel` nemá založený pracovní poměr) — zkouší se na skutečném člověku a **uklízí se po sobě**: smazat novou verzi, její mzdové složky a řádky historie, vrátit staré verzi `is_current`, `changed_by_text` i původní `changed_at`, a smazat zprávy z `fw.mobile_command`, dokud jsou ve stavu „čeká".

## Past mostu, která u toho vypadla

Zápis živého kódu přes most **spadne na dvojtečce**: `:u`, `:t`, `:id` uvnitř kódu se vyloží jako zástupný symbol (`A value is required for bind parameter 'u'`), i když jsou uvnitř dolarových uvozovek. **Řešení: obsah posílat zakódovaně** — `SET zdroj = convert_from(decode('<base64>','base64'),'UTF8')`. Zbaví to text dvojteček i starostí s diakritikou.

K tomu se vyplatí přidat **pojistku proti přepsání cizí práce**: `AND md5(zdroj) = '<otisk, který jsi právě četl>'` — při souběhu projde 0 řádků místo tichého přepsání.

Souvisí: [[doc-dochazka-uvazek-jediny-zdroj-smlouva]], [[doc-dochazka-podminky-slouceny-se-smlouvou]], [[doc-dochazka-podminky-kdo-zapisuje-do-pod-a-past-pohledu-staff-cond]]

---

## DOPLNĚNO 24. 8. 2026 — kopírování se přesunulo do společného jádra

*(Zadal Jirka Honomichl, schválila Marti-AI msg 13561. Zapsáno sem, aby tahle znalost
neučila stav, který už neplatí — bod 14 Jirkových pravidel.)*

Přibylo **ruční tlačítko „Nová verze smlouvy"** v kartě zaměstnance, takže novou verzi
poměru umí založit i jiná cesta než změna úvazku. Aby kopírovací logika nebyla na dvou
místech, přestěhovala se z `uvazek_zapis` do nového společného jádra
**`engagement_nova_verze`**, které volají obě cesty.

| co | kde to žije dnes |
|---|---|
| kontrola „platí od", zmrazené měsíce, výběr při víc souběžných poměrech | `engagement_nova_verze` |
| kopie řádku 1:1, přepnutí staré verze, kopie mzdových složek | `engagement_nova_verze` |
| poznání „úvazek se nemění, nedělej nic", **znění potvrzovací otázky**, zpráva Petře a Šárce | `uvazek_zapis` (beze změny) |

⚠️ **Chování změny úvazku navenek je záměrně stejné jako ve v8** včetně pořadí hlášek:
„úvazek se nemění" se musí vyhodnotit DŘÍV než kontrola data. Proto jádro při zjišťování
datum jen označí příznakem (`datum_ok`) a nevynucuje ho — vynutí se až při skutečném zápisu.
Ověřeno naostro 24. 8. 2026: stejná hodnota → „nic se nemění"; jiná hodnota bez potvrzení →
doslova stejná otázka jako předtím.

⚠️ Od 24. 8. 2026 všechny tyhle cesty navíc zapisují do historie **autora** změny —
viz [[doc-system-strategie-historie-smluv-kdo-zmenu-udelal]].

Detail tlačítka: [[doc-dochazka-smlouva-nova-verze-rucne]]

