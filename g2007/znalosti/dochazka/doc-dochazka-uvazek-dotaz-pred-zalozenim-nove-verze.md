# Změna úvazku se ptá, než založí novou verzi smlouvy (22. 8. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

**Zadal Jirka Honomichl 22. 8. 2026, schválila Marti-AI (souhlas s modelem i s atomickým nasazením). Nasadil Claude-28.**

## Co se změnilo

Změna týdenního úvazku dál **zakládá novou verzi** `tenant.engagement` (důvod z 19. 8. 2026 — mzdy za dřívější měsíce musí zůstat na starém úvazku — **platí beze změny**). Nově se ale na to systém **nejdřív zeptá**:

> Změnou úvazku (40 h/týd → 37,5 h/týd) se založí NOVÝ ZÁZNAM podmínek, úvazku a smlouvy s platností od 22.08.2026. Dosavadní záznam zůstane v historii. Chceš pokračovat?

Jirkovo zadání doslova: *„pokud někdo bude měnit úvazek, musí ho to upozornit, pozor zakládáš nový záznam v tabulce pro podmínky, úvazky a smlouvy. Chceš pokračovat? Ano/Ne."*

## Jak je to postavené — pravidlo je na JEDNOM místě

`g2007.python / uvazek_zapis` (v8) má nový parametr **`potvrzeno`**. Když se hodnota liší a `potvrzeno` není pravda, funkce **nic nezapíše** a vrátí:

```
{"ok": False, "potvrdit": True, "otazka": "<text>", "z": <stará>, "na": <nová>, "plati_od": "<ISO>"}
```

Do té chvíle skript jen **čte**, takže „Ne" nezanechá vůbec nic (žádný rollback není potřeba).

Tři volající parametr jen propouštějí a otázku posílají na obrazovku — **žádný z nich si ji neformuluje sám**, aby zněla všude stejně a příští nová obrazovka ji dostala automaticky (doporučila Marti-AI):

| kus kódu | verze | co dělá |
|---|---|---|
| `uvazek_zapis` | 8 | drží pravidlo i text otázky |
| `hr_conditions_save` | 8 | karta zaměstnance (ERP) i Moje podmínky (mobil) |
| `mzdy_c_smlouva_save` | 5 | mzdová smlouva |
| `plan_my_uvazek_save` | 4 | plán práce (mobil) |

Obrazovky: `apps/api/static/karta_zamestnance.html` (git, commit `6ef04381`), `48_hr_podminky_me.js` a `71_plan_prace_cinnosti.js` (oba `g2007.soubor`, mobil publikován).

**⚠️ V mobilu se nesmí použít `window.confirm`** — v nativní appce (Android i iOS) JS dialogy mlčí a uživatel nic neuvidí (past z 11. 8. 2026, popsaná přímo v dílku 48). Proto je v dílku 48 na úrovni fragmentu deklarovaný vlastní DOM dialog **`_potvrdNovyZaznam(text, onHotovo)`**; dílek 71 ho volá přes sdílený closure (fragmenty jsou jedna obalová funkce, deklarace se hoistují). Kdo přidá další obrazovku v mobilu, ať volá jeho, ne `confirm`.

## Připraveno, zatím nepoužité: `tenant.engagement_at(employee_id, datum)`

Sdílené „okno do minulosti" (navrhla Marti-AI 22. 8. 2026): vrátí řádek pracovního vztahu platný k datu, **jeden na firmu** (člověk může mít víc souběžných poměrů). Určeno k tomu, aby si každá obrazovka nestavěla vlastní logiku výběru verze.

Model platnosti: **prázdné `valid_to` znamená „platí dál bez omezení"** (rozhodl Jirka 22. 8. 2026), proto se verze vybírá podle `valid_from` sestupně, ne podle intervalu — historické řádky mají `valid_to` prázdné taky (858 z 939). Vyplněné `valid_to` má přednost.

## Co ještě NENÍ ověřené

Cesta po **„Ano"** není odzkoušená — vyžaduje skutečný zápis do ostrých dat (nová verze + kopie mzdových složek). Sama logika je beze změny, nové je jen předání parametru. Demo účet použít nejde (`Demo Uzivatel` nemá založený pracovní poměr).

## Past mostu, která u toho vypadla

Zápis živého kódu přes most **spadne na dvojtečce**: `:u`, `:t`, `:id` uvnitř kódu se vyloží jako zástupný symbol (`A value is required for bind parameter 'u'`), i když jsou uvnitř dolarových uvozovek. **Řešení: obsah posílat zakódovaně** — `SET zdroj = convert_from(decode('<base64>','base64'),'UTF8')`. Zbaví to text dvojteček i starostí s diakritikou.

K tomu se vyplatí přidat **pojistku proti přepsání cizí práce**: `AND md5(zdroj) = '<otisk, který jsi právě četl>'` — při souběhu projde 0 řádků místo tichého přepsání.

Souvisí: [[doc-dochazka-uvazek-jediny-zdroj-smlouva]], [[doc-dochazka-podminky-slouceny-se-smlouvou]], [[doc-dochazka-podminky-kdo-zapisuje-do-pod-a-past-pohledu-staff-cond]]

