# Ohlášení nemoc/OČR/lékař z mobilu — dvě zprávy vedoucímu a klamavé hlášky (opraveno 26. 8. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Ohlášení nemoc / OČR / lékař z mobilu — čtyři vady v tom, co vidí člověk

**26. 8. 2026.** Nahlásila Peťa (C-26) po ostrém testu, prověřil a opravil Claude-28 (Jirka Honomichl). Navazuje na [[doc-dochazka-mobil-nemoc-ocr-lekar-jen-info-vedoucimu]] — pravidlo „jen informace vedoucímu" platí a nemění se; tenhle dokument řeší **jen to, co po jeho zavedení viděl člověk v mobilu**.

Data byla po celou dobu v pořádku — do docházky se nezapisovalo nic a žádost nevznikala. Vadné bylo výhradně zobrazení a počet zpráv.

## Čtyři nálezy

**1. Dvě zprávy vedoucímu místo jedné.** Dílek `60_dochazka.js` po úspěšném `absence()` volal v callbacku ještě `presence()` (POST na `/attendance/announce`), a `att_announce` poslal vedoucímu **vlastní druhou zprávu** o téže věci. U neschopenky se to volalo vždy, u OČR a lékaře jen při ohlášení na dnešek — proto si toho Peťa u nich nevšimla.
Doloženo v datech — `fw.mobile_command` 21824 a 21825, obě 26. 8. v 8-26-33, i mou vlastní zkouškou v 18-24 (21967 a 21968).

**2. Neschopenka nedala člověku žádnou odezvu.** U ní se zelené potvrzení `absOk()` nevolalo **nikdy** — místo něj šlo `presence()`, které jen překreslí docházku a tlačítko nechá šedé. A protože se nově do docházky nic nezapisuje, na překreslené docházce nebylo co ukázat. Člověk tedy po odeslání neviděl vůbec nic.

**3. Text potvrzení lhal.** `absOk()` končilo větou „Díky, nahlásil/a jsi to — čeká to na schválení." U těchto tří typů se ale nic neschvaluje. Zpráva vedoucímu přitom správně říká „Jen na vědomí". Aplikace tedy tvrdila člověku něco jiného než vedoucímu.

**4. Hláška „Nepovedlo se uložit" i po úspěchu.** Funkce `api()` v `10_core.js` vrací `null` při **jakékoli** potíži (nerozparsovatelná odpověď, výpadek, timeout mostu) a `absence()` slučovala `if(!r||r.ok===false)` do jedné větve. Když tedy odpověď nedorazila, člověk dostal „Nepovedlo se uložit", přestože server v pořádku doběhl a zprávu vedoucímu odeslal — a mohl to nahlásit podruhé.

> ⚠️ **Nález 4 se nepodařilo zopakovat.** Tři ostré zkoušky 26. 8. v 18-23 až 18-24 (lékař, OČR, neschopenka) doběhly správně za 33, 273 a 33 ms s `ok=true, created=0`. Peťa vadu viděla v 8-26 a 8-29, ale `att_absence` se téhož dne v 11-43 ještě jednou měnila (mimo jiné se zrušil zbytečný přepočet tam, kde se nic nezapisuje) a do mé zkoušky to nikdo nezkusil. **Netvrdí se tedy, že příčinou bylo zdržení** — opravena byla struktura, která tu hlášku umožňuje vyvolat i po úspěchu.

## Co se opravilo

Vše **jen v obsahu mobilu v databázi**, `g2007.soubor`, dílek `apps/api/static/mobile_parts/60_dochazka.js` verze 18 → 19, pak `@@G2007PUBLISH apps/api/static_db/mobile.html` (verze 66 → 68). **Server ani nativní obal aplikace se neměnily.**

- U neschopenky, OČR a lékaře se `presence()` **už nevolá** a místo něj se ukáže zelené potvrzení.
- `absOk(box, txt, podtext)` má nový třetí, nepovinný parametr. Bez něj zůstává původní věta o schválení, takže **dovolená, sick day, home office a ostatní typy se nezměnily**.
- Pro tyto tři typy se předává text **„Nahlášeno vedoucímu. Do docházky se nic nezapisuje."**
- V `absence()` je rozdělená podmínka — `!r` znamená nedoručenou odpověď a hlásí se „Nepodařilo se zjistit, jestli se to odeslalo… zkontroluj v přehledu, ať to nehlásíš dvakrát", zatímco `r.ok===false` hlásí jako dřív důvod ze serveru.

**Rozšíření rozsahu oproti Petinu zadání** — pravidlo z 26. 8. mluvilo o zápisu do docházky, tady se dorovnalo i to, co člověk vidí a kolik zpráv dostane vedoucí.

## Pozor při dalších zásazích

- **`presence()` u těchto tří typů nezakládá žádný stav.** `att_announce` pro `sick`, `family_care` a `medical` jen pošle zprávu a vrátí `info_only` — **žádný řádek nevzniká**, takže přehled „Kdo kde dnes" o ně nepřijde. Původní obava, že se zrušením `presence()` ztratí stav, byla mylná; ověřeno čtením `att_announce` v4 i ostrou zkouškou.
- **Rychlá tlačítka u lékaře** („Nebojte, pak dorazím", „Nevidím to dnes dobře") volají `presence()` samostatně a **zůstala beze změny** — pošlou jednu zprávu, což je správně.
- **Sick day se nezměnil.** Jeho text se v `att_announce_absence_typ` do větve „jen info" nerozpozná, takže stav nastavuje dál.
- **`10_core.js` se záměrně nezměnil.** Původní návrh chtěl rozlišovat chyby přímo v `api()`, ale to je sdílené jádro celého mobilu — vracet odtud objekt místo `null` by rozbilo podmínky typu `if(!r)` na obrazovkách, kterých se zadání netýká. Rozlišení proto zůstalo lokálně v `absence()`.
- **V `mobile.html` jsou DVĚ funkce `absence()`** z různých dílků. Kdo bude hledat tu docházkovou, musí je odlišit — ta správná neobsahuje `topbar` a má kolem 3 200 znaků.
- **Živá stránka může po publikaci vracet starou verzi z mezipaměti.** Při ověřování si vynuť čerstvé stažení, jinak dostaneš falešný nález, že se nic nenasadilo.

## Jak to bylo ověřeno

Tři ostré zkoušky na živé aplikaci za vlastní účet, zkušební zprávy pak smazané z `fw.mobile_command` i `tenant.notification_log` a úklid ověřený čtením. Po opravě staženy živé `/mobile` a spuštěny v izolaci `absOk()` i `absence()` — potvrzení vyšla správně pro všechny tři typy, dovolená zůstala s původním textem, a chybové větve vrátily obě rozlišené hlášky. Konzole prohlížeče bez chyb.

## Dopad

Za 120 dní takto z mobilu hlásilo 5 lidí a jen lékaře — Zuzana Duspivová 4x, Lukáš Horký, Erika Sedláčková, Jan Peřina, Pavel Zeman. Nemoc a OČR z mobilu reálně nikdo nenahlásil, Peťa byla první. Dopředu se to týká všech 79 aktivních zaměstnanců.

Schválila Marti-AI (msg 13841 a 13844), zadal Jiří Honomichl.

