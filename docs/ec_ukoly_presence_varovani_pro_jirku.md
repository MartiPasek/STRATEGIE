# EC_Ukoly — varování „adresát není v práci" (zadání pro Jirku)

**Datum:** 19. 6. 2026 · **Od:** Marti / STRATEGIE · **Pro:** Jirka (Centrála 1 / Delphi)
**Priorita:** střední — blokuje hladký přechod lidí na novou docházku (hybridní fáze)

---

## Co potřebujeme (jedna věta)
Při zadávání úkolu v Centrále (EC_Ukoly) **odstranit / zneškodnit varování zadavateli, že
adresát „není v práci"** — případně ho omezit tak, aby nevyskakovalo zbytečně (např. když je
člověk jen na pauze).

## Proč
Spustili jsme novou docházku ve STRATEGII (mobilní appka). Cíl hybridní fáze: **appka = zdroj
pravdy**, lidé se mají píchat **jen v ní** a starý systém postupně opustit.

Problém, který to blokuje: když se někdo píchne v appce, my mu v Centrále **uzavřeme otevřenou
směnu** v `EC_Dochazka` (aby nebyly dvě docházky). Jenže Centrála při **zadání úkolu** kontroluje
přítomnost právě podle otevřené směny v `EC_Dochazka` — a když otevřená není, **zadavateli
vyskočí varování, že adresát není v práci**.

Důsledek: lidé (např. tester Pavel Voříšek) se **schválně píchají do starého systému jen proto**,
aby u nich to varování nevyskakovalo a chodily jim úkoly „v pořádku". Tím se nám maří přechod na
novou docházku.

Navíc je to varování nepřesné i samo o sobě — vyskočí, i když je člověk **jen na pauze / obědě**,
což zadavatele zbytečně mate.

## Co jsme zjistili (technicky)
- Přítomnost „v práci / není v práci" se v Centrále odvozuje **z `EC_Dochazka`** (otevřená směna,
  `PraceAktivni = 1` pro dnešek). Samostatný příznak přítomnosti na `TabCisZam`/`TabCisZam_EXT`
  jsme nenašli.
- V proceduře `EC_Ukolnik_EditujUkol` (zakládání/editace úkolu) **kontrola `PraceAktivni` není** —
  takže to varování je nejspíš buď v **Delphi klientovi** (messagebox nad presence dotazem), nebo
  v jiné proceduře/funkci, kterou klient při zadání úkolu volá. Přesné místo zná nejlíp EUROSOFT.

## Návrh řešení (vyber, co je nejčistší — Jirkova volba)
1. **Varování úplně vypnout** při zadání úkolu (nejjednodušší, Marti preferuje).
2. **Nechat jen jako informaci, ne blokující** — ať to nikoho nezdržuje (žádné „opravdu pokračovat?").
3. **Rozšířit definici „v práci"** — brát jako přítomného i toho, kdo má pro dnešek **naplánovanou
   docházku** / je jen na pauze, ne jen toho s živou otevřenou směnou. (Tím by varování zmizelo
   u lidí, co reálně pracují přes appku.)

Stačí kterákoliv z variant; pro nás je hlavní, aby **zadání úkolu fungovalo bez ohledu na to, že
člověk není píchnutý ve staré `EC_Dochazka`**.

## Co bychom uvítali zpět
- Kde přesně to varování je (Delphi klient × procedura/funkce) — ať to máme zmapované.
- Po úpravě krátké potvrzení, ať to otestujeme s testery.

## Souvislost / výhled
Dlouhodobě EC_Ukoly nahradí **nativní systém úkolů ve STRATEGII** (přítomnost = appka, řešitel =
člověk i AI agent). Tahle úprava je **mezikrok pro hybridní fázi**, ať lidé můžou hned přejít na
novou docházku, aniž by je starý systém „nutil" se píchat kvůli úkolům.

---
*Pozn.: STRATEGIE má od 19. 6. povolený auditovaný zápis (INSERT/UPDATE) do `DB_EC` přes MCP,
takže pokud bude potřeba součinnost na straně dat, umíme ji dodat.*
