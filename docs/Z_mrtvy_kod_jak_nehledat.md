# Mrtvý kód ve STRATEGII — proč grep lže a co NEMAZAT

**Autor:** Claude-28 (Jirka), 21. 7. 2026 · Podnět: „odstraň z projektu zbytečné nepoužívané věci"

> **TL;DR — v repu STRATEGIE se mrtvý kód NEDÁ hledat grepem po importech.**
> Klíčové části frameworku se načítají **dynamicky podle jména z databáze**.
> Statická analýza je označí jako nepoužité. **Nejsou.** Kontrola 21. 7. 2026
> neidentifikovala **ani jeden** soubor, který by šlo bezpečně smazat.

## 1. Past: `importlib` podle jména z DB

`modules/fw_components/__init__.py` (ř. ~38):

```python
module = importlib.import_module(f"modules.fw_components.{name}")
class_name = getattr(module, "CLASS_NAME")
return getattr(module, class_name)
```

`name` **přichází z databáze / registru komponent**, ne z kódu. Žádný `import`
na ty soubory v repu neexistuje a existovat nemá. `git grep` proto u celé řady
`modules/fw_components/*.py` vrátí nulu použití.

Totéž platí pro další dynamické cesty (`__import__("modules.erp.api.oz_mirror", …)`
v `router.py` u ops akcí) — modul se jmenuje **řetězcem v lambdě**, ne importem.

**Následek smazání:** aplikace se nerozbije při startu ani při syntax checku.
Rozbije se **až za běhu a jen tomu, kdo danou komponentu otevře.** Nejhorší
druh chyby — tichá, opožděná, uživatelsky viditelná.

## 2. Konkrétní soubory, které vypadají mrtvě a NEJSOU (stav 21. 7. 2026)

| Soubor | Zdá se | Skutečnost |
|---|---|---|
| `modules/fw_components/jadro_radek_form.py` | nikdo neimportuje | **manifest** načítaný dynamicky; **JS dvojče je živě načítáno** v ERP (`router.py` ~58582 `design_jadro_radek_form.js`) |
| `modules/fw_components/soudecek_core_form.py` | nikdo neimportuje | dtto (`design_soudecek_core_form.js`) |
| `modules/erp/api/teamio_replies.py` | nikdo neimportuje | popsáno v `docs/ARCHITEKTURA.md` + `docs/teamio_lmc_pozadavek.md` |
| `modules/erp/application/comp_inspector_service.py` | nikdo neimportuje | popsáno v `docs/erp_prehledy_overview.md` |

`modules/fw_components/` je **jednotná řada 9 manifestů** stejného tvaru
(`NAME`, `JS_PATH`, `BINDING`, `CLASS_NAME` + třída dědící `ComponentBase`).
Dva z nich mají v hlavičce *„Iterace B (later — extract router.py code)"* —
je to **rozdělaná architektura, ne odpad**. Smazáním by se navíc porušila
Martiho doktrína *„uniformita vítězí nad speciálními případy"* (Krok 13).

## 3. Co ještě NEMAZAT, i když to tak vypadá

- **`docs/Z_*.md`** (~60 souborů) — inbox znalostí pro G2007. Server po vstřebání
  soubor **sám smaže** commitem „g2007: uklid inbox …". Co tam zbylo, tedy
  **NENÍ vstřebané** → smazání = ztráta znalosti.
- **`docs/CLAUDE_ARCHIVE_*.md`, `CLAUDE_BACKUP_*.md`** — záměrný archiv krabičky
  (split 5. 6. 2026), na který se odkazuje z `CLAUDE.md`.
- **Atrapy tlačítek** ⏱/🧾/🗑 v Historii docházky (`_jobBtns`) — vypadají jako
  mrtvý kód (nic nevolají), ale nesou **nevyřízené rozhodnutí** položené Martimu
  („Ostrou funkci nawiruju, až schváliš", souvisí s R1 samoúpravami u Marti-AI).
  Jirka 21. 7. rozhodl **nechat**. Mrtvý kód ≠ nevyřízená otázka.

## 4. Jak tedy mrtvý kód hledat (když to bude opravdu potřeba)

1. **Nikdy jen grepem po jméně modulu.** Vždy ověř: (a) dynamické načítání
   (`importlib`, `__import__`, jméno v DB), (b) JS/HTML dvojče, (c) zmínku
   v `docs/` a v G2007.
2. **Statické soubory** (`apps/api/static/*.html|js`) — kontrola odkazů projde;
   k 21. 7. 2026 **0 osiřelých**.
3. **Registry v DB** je zdroj pravdy pro komponenty: `fw.hw_registry`
   (`name`, `py_path`, `js_path`, `is_active`, `is_deprecated`), `fw.comp_def`,
   `fw.core`. Než něco smažeš, hledej v nich — ne v kódu.
4. **`git log -1` na soubor** ukáže, jestli je to opuštěné, nebo čerstvě rozdělané.
5. Repo je **sdílené území 6 instancí** (23 Marti, 24 Kristý, 25 Šárka, 26 Peťa,
   28 Jirka + Marti-AI). Mazání bez pullu a bez ohlášení = přepsaná cizí práce.

## 5. Závěr kontroly 21. 7. 2026

**Nesmazáno nic.** Ne z opatrnosti pro opatrnost, ale protože se u žádného
kandidáta nepodařilo prokázat, že je nepoužitý — a u dvou se prokázal **opak**.
Úspora by byla ~600 řádků; riziko tichá produkční chyba. Nevyplatí se.
