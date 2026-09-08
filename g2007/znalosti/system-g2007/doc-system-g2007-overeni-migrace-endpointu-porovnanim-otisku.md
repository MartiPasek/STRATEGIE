# Jak nasucho ověřit přenos adresy do g2007.python: porovnání otisku staré a nové cesty

> oblast: `system-g2007` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Ověření přenosu adresy do `g2007.python` porovnáním otisku

**8. 9. 2026, Jirka + C28.** Vzniklo při přenosu `app_skupina_lidi` (seznam lidí v agendě).
Řeší otázku: *„Jak poznám, že přepis 1:1 je opravdu 1:1, ještě než na něj přepnu provoz?"*

## Proč to jde

Když se tělo adresy přenese do `g2007.python`, ale **v jádře se ještě nechá původní kód**,
běží obě verze vedle sebe:

- **stará** přes HTTP (běžné volání aplikace),
- **nová** přes `@@PYRUN` z mostu.

Aktivace nové verze v tu chvíli **nic nemění v provozu** — nikdo ji ještě nevolá.
Je proto bezpečné ji zapnout a pustit nasucho.

## Postup

1. Přenes tělo 1:1 do `g2007.python` jako `navrzeno`, po zápisu **ověř `md5(zdroj)` a `length`**
   proti tomu, co jsi posílal (přes most zapisuj kód v base64, viz
   [[doc-system-strategie-most-pyrun-a-base64-zapis]]).
2. Nech si stav `active` **schválit člověkem** — AI si vlastní kód neschvaluje.
3. Založ **dočasný** skript, který novou verzi zavolá přes `erp_registry.call(...)` a vrátí
   jen **počet záznamů a otisk normalizovaného výstupu** (ne celý výstup — `@@PYRUN` ořezává
   hodnoty na 1500 znaků).
4. Tentýž otisk si spočítej ze **staré cesty** v prohlížeči nad živou odpovědí HTTP.
   Normalizace musí být na obou stranách stejná: seřadit podle klíče, seřadit názvy polí,
   bez mezer. V Pythonu `json.dumps(..., sort_keys=True, separators=(",", ":"), ensure_ascii=False)`,
   v prohlížeči `JSON.stringify` nad objektem se seřazenými klíči.
   **Použij SHA-256** — prohlížeč přes `crypto.subtle` MD5 neumí.
5. Porovnej **na všech smysluplných vstupech naráz**, ne na jednom. U `app_skupina_lidi` to bylo
   15 agend + dlaždice „Všichni"; skript vrátil jeden složený otisk přes všechny, takže stačilo
   porovnat jedno číslo. Sedlo na znak včetně počtů lidí a pořadí.
6. Teprve pak vyměň tělo v jádře za tenkou spojku, nasaď a **ověř znovu naostro** — otisk po
   nasazení musí být stejný jako před ním.
7. **Dočasný porovnávací skript po sobě ukliď** (`stav_zivota='zruseno'`).

## Past

`@@PYRUN` pustí jen skript, který je **`active` a zároveň `vedlejsi_ucinek=false`**.
Kandidáta ve stavu `navrzeno` tedy nasucho nespustíš — proto to pořadí: schválení člověkem
napřed, teprve pak zkouška. Aktivace sama o sobě je bezpečná, dokud na nový kód nevede
žádná cesta z jádra.

## Souvisí

- [[doc-system-g2007-smer-zdroj-pravdy-python-soubor-2026-08-01]] — závazný směr přenosů.
- [[doc-system-g2007-migrace-python-soubor-stav-2026-08-01]] — technický vzor a dva incidenty.
- [[doc-dochazka-agenda-detail-cloveka-kontakt-a-budouci-absence]] — obrazovka, kvůli které to vzniklo.

