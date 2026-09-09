# Mobil, úvodní obrazovka „Domů" — přestavba 7. 9. 2026 (nadpis nahoru, jméno do lišty, kruhový portrét, rolující seznam oznámení, přepínač řádku o odezvě)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)

# Mobil, úvodní obrazovka „Domů" — přestavba 7. 9. 2026

**Zadal Jirka Honomichl, schválila Marti-AI, provedl Claude-28.** Podobu fotky vybral Jirka
ze čtyř variant připravených naživo v prohlížeči.

## Co se změnilo (pět věcí)

1. **Nadpis „STRATEGIE Mobil" je nahoře** přes celou šířku displeje, na jednu řádku. Velikost
   písma se **dopočítá podle šířky zařízení** (`_homeFitTitle`), takže sedí na úzkém i širokém
   telefonu a přeměří se i po otočení.
2. **Jméno člověka zmizelo z fotky.** Je nově v popisku druhé ikony spodní lišty (viz
   [[doc-system-strategie-mobil-spodni-lista-zjednodusena-2026-08-28]]).
3. **Řádek o prostředí a odezvě je spojený do jedné řádky** a je pod nadpisem. Vidí ho **jen
   správci a rodiče**; ostatním se ukáže, až se zapne přepínač v Nastavení. Výchozí stav vypnuto.
4. **Fotka je kruhový portrét 220 bodů uprostřed**, ne pozadí přes celou plochu.
5. **Seznam oznámení má vlastní okno s rolováním**, aby neroztlačil zbytek obrazovky.

## Čísla, o která se rozhodnutí opírají (měřeno 7. 9. 2026 na živé appce)

- Avatar ze serveru je **256×256**, plocha obrazovky 408×889. Roztažení „na výšku" ho zvětšilo
  na 889×889 = **3,5× nafouknuté (proto měkké) a oříznuté o 482 bodů šířky**. Vystředění
  takový ořez nespraví — proto kruh: 220 bodů je **zmenšení 0,86×**, tedy ostřejší než předtím.
- **Do 7 karet oznámení** se vše vešlo. **Od 8 karet** se portrét dotkl nadpisu a začala rolovat
  **celá stránka** — nadpis i fotka odjely pryč. Portrét se přitom nikdy nezmenšil ani nepřekryl
  nadpis; problém byl v rolování celku, ne v překrytí.
- Proto má seznam vlastní okno: `max-height` = zbytek plochy po nadpisu a portrétu, minimum
  140 bodů, `overflow-y:auto`. Ověřeno při 1, 3, 5, 7, 8, 10, 15, 20 a 30 kartách: **stránka
  se nerolovala ani jednou** a poslední karta byla vždy dosažitelná.
- **Není to teoretický případ.** V datech mělo v ten den čekající oznámení 39 lidí, z toho
  **8 lidí osm a více**; nejvyšší počet u jednoho člověka byl **197** (nejstarší z 21. 7.).
  Takový člověk měl úvodní obrazovku dlouhou několik tisíc bodů.

## Kde to žije

| co | kde |
|---|---|
| obrazovka Domů | `apps/api/static/mobile_parts/20_home_phone_notifs.js` |
| popisek a ikona ve spodní liště | `apps/api/static/mobile_parts/74_claude27_render_init.js`, funkce `_navJmeno()` |
| přepínač v Nastavení | `apps/api/static/mobile_parts/30_contacts_settings.js`, funkce `_setStavRadku()` |
| čtení stavu | `g2007.python` kód **`mobile_domu_stav`** — vrací křestní jméno, příznak „je správce nebo rodič" a stav přepínače |
| zápis přepínače | `g2007.python` kód **`mobile_domu_stav_nastav`** — práva si ověřuje sám, protože `min_pravo` zná jen člen/rodič/admin a potřebovali jsme sjednocení „admin NEBO rodič" |
| samotný přepínač | `g2007.nastaveni`, klíč **`mobil_domu_stav_vsem`** (`on`/`off`, chybějící klíč = vypnuto) |

**Jádro se kvůli tomu neměnilo.** Adresa `/app/whoami` příznak správce ani rodiče nevrací;
místo rozšiřování jádra vznikly dvě funkce v databázi, které mobil volá přes už existující
adresu `/app/erp_registry/run`. Je to použití bodu 2 pravidel práce (kód žije v databázi).

## Pasti

- ⚠️ **Odpověď z `/app/erp_registry/run` chodí ZABALENÁ** ve tvaru `{ok, verze, vysledek:{…}}`.
  Kdo čte `j.jmeno` místo `j.vysledek.jmeno`, dostane `undefined` a **nikde to nenahlásí chybu** —
  jméno v liště i řádek stavu prostě tiše nenaběhnou. Stálo to jedno kolo nasazení.
- **Avatar je malý (256 bodů).** Cokoli, co ho kreslí větší než ~410 bodů, je vidět jako měkké.
  Kruh 220 bodů je jediná varianta, kde se nezvětšuje.
- **Portrét musí být V TOKU stránky**, ne absolutně umístěný. Jen tak ho karty oznámení posunou
  nahoru místo aby ho překryly.
- **Obsah řádku o odezvě přepisuje `updateLive()` z `10_core.js`**, a to opakovaně. Velikost
  písma se proto dopočítává znovu při každé změně obsahu (hlídač změn), ne jen jednou.
- **Nepřihlášený host nemá fotku** — kroužek se mu skrývá, jinak by prázdný kruh vypadal jako
  chyba. Ověřeno čtením kódu, **naživo neověřeno** (nepodařilo se dostat do stavu bez přihlášení).

## Kdo to uvidí

Změny vzhledu (nadpis, jméno v liště, kruhová fotka, rolující seznam) vidí **všech 118 lidí**.
Řádek o prostředí a odezvě vidí jen **správci a rodiče** — v den zavedení tři lidé.

Souvisí: [[doc-system-strategie-mobil-spodni-lista-zjednodusena-2026-08-28]] · [[doc-system-strategie-mobil-kde-se-edituje-a-jak-se-nasazuje]]

