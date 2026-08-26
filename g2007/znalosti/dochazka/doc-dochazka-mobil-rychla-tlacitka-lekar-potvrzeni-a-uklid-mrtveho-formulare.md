# Rychlá tlačítka u lékaře dostala potvrzení + úklid mrtvého formuláře absencí (26. 8. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Rychlá tlačítka u lékaře + úklid mrtvého formuláře

**26. 8. 2026, druhá vlna.** Navazuje na [[doc-dochazka-mobil-nemoc-ocr-lekar-dve-zpravy-a-chybne-hlasky]] — po první opravě se Jirka zeptal, jestli se tytéž vady netýkají i jiných míst. Zadal Jiří Honomichl, schválila Marti-AI (msg 13850), provedl Claude-28.

## Kde všude jde absence z mobilu zadat (mapa, ověřeno 26. 8. 2026)

| místo | dílek | stav |
|---|---|---|
| Docházka → „Tady budu jinde" | `60_dochazka.js` | opraveno první vlnou |
| rychlá tlačítka u lékaře | `60_dochazka.js` | **opraveno touto vlnou** |
| Žádost o nepřítomnost (Skupiny) | `50_skupiny_vyroba.js` | v pořádku, neměněno |
| Žádost o nepřítomnost (Plán práce) | `71_plan_prace_cinnosti.js` | v pořádku, neměněno |
| formulář „Typ nepřítomnosti" | `72_migrace_sw_isds.js` | **smazán, byl mrtvý** |

Oba formuláře žádostí jsou **tentýž kód** a po odeslání píší „✅ Odesláno vedoucímu" — to je pravdivé i pro nemoc, OČR a lékaře, takže se tam neměnilo nic.

## Nález 1 — rychlá tlačítka u lékaře nedávala žádnou odezvu

Tlačítka **„🩺 Nebojte, pak dorazím…"** a **„🩺 Nevidím to dnes dobře…"** volají `presence()` samostatně, mimo `absence()`, takže do první vlny oprav nespadla.

Ověřeno naostro 26. 8. ve 20-09 a 20-10 — na obě server vrací `ok=true, info_only=true, typ=medical`, zprávu vedoucímu pošle a do docházky nezapíše nic (ověřeno čtením `att_entry`, nula řádků).

**Server přitom hotovou větu pro člověka posílá** — v poli `note` zní „Nahlásil jsem to vedoucímu. Do docházky se nic nezapisuje." — ale `presence()` ji zahazovala. Dělala jen `b.disabled=true` a `dochLoad()`; protože se do docházky nic nezapsalo, překreslení nemělo co ukázat a **člověk po klepnutí neviděl vůbec nic**.

**Oprava** (`60_dochazka.js` v19 → v20) — `presence()` při odpovědi s `info_only` zobrazí zeleně větu z pole `note`, s náhradním textem, kdyby nedorazila. **Tlačítko schválně zůstává vypnuté** (upozornila Marti-AI) — zpráva odešla a druhý klep by poslal druhou. Když `info_only` nepřijde, chování je jako dřív, takže home office, sick day a ostatní ohlášení se nezměnila (ověřeno spuštěním obou větví).

## Nález 2 — mrtvý formulář absencí, smazán

V `72_migrace_sw_isds.js` byla funkce `buildAbsForm(box)` — celý formulář „Typ nepřítomnosti" (Dovolená / Home office / Nemoc / Lékař / OČR / Sickday / Neplacené) posílající POST na `/attendance/absence`. Měla tři obdoby vad z první vlny — tlačítko „Odeslat ke schválení", hlášku „Nahlášeno ✓ (0 pracovních dní)" (u těchto typů vždy nula) a chybovou větev bez jakékoli zprávy.

**Nikdo se k ní nedostal.** Ověřeno v celém složeném `mobile.html` — jméno `AbsForm` tam bylo **právě jednou**, tedy jen definice; prvky `absType`, `absFrom`, `absHours`, `absNote` měly po dvou výskytech, oba uvnitř té jedné funkce; dynamické volání přes `window[...]` v mobilu neexistuje vůbec (nula výskytů).

Jirka rozhodl uklidit místo opravovat. Funkce smazána (`72_migrace_sw_isds.js` v2 → v4), na jejím místě zůstala poznámka, proč tam není a kde zadávání absencí žije.

## ⚠️ PAST, KTERÁ SE PŘITOM CHYTILA — komentář bez zlomu řádku spolkne další funkci

Náhradní text končil komentářem `//` **bez závěrečného zlomu řádku**. Vzniklo tím

`… Nezakládat sem znovu.function skupNazev(gid){ … }`

na jednom řádku — takže **celá další funkce `skupNazev` se stala součástí komentáře** a přestala existovat. Kód se přitom přeložil bez chyby a hlídač publikace by to nezachytil.

Chytilo se to jedině **kontrolou rozdílu před publikací**, kterou si vyžádala Marti-AI. Do živé aplikace se to nedostalo; opraveno doplněním zlomu řádku (v3 → v4) a znovu ověřeno na živé stránce.

**Pravidlo z toho:** když náhradní text končí komentářem `//`, **musí končit zlomem řádku** — jinak pohltí to, co za ním následuje. A protože se text často sestavuje přes `printf '%s' "$(cat …)"`, které koncový zlom **ořízne**, je potřeba ho doplnit výslovně. Obecněji platí to, co říká bod 9 pravidel práce — *„jde to přeložit" nic nedokazuje*; u mazání a náhrad bloků kontroluj rozdíl a výpis toho, co zmizelo, **před** nasazením.

## Jak to bylo ověřeno

Dvě ostré zkoušky obou tlačítek na živé aplikaci (zkušební zprávy smazané, úklid ověřen čtením), kontrola `att_entry` (nula řádků), rozdíl délky obou dílků proti stavu před zápisem, kontrola že ze smazaného bloku zmizela **jediná** definice funkce (`buildAbsForm`, ověřeno na vyříznutém textu), a po publikaci (`mobile.html` v68 → v70) čtení živé stránky — `skupNazev` je zpět na vlastním řádku, mrtvá funkce pryč, nové potvrzení na místě, tři potvrzení absencí z první vlny beze změny. Konzole prohlížeče bez chyb.

## Dopad

Rychlá tlačítka u lékaře se týkají všech 79 aktivních zaměstnanců; za 120 dní lékaře z mobilu hlásilo 5 lidí (Zuzana Duspivová 4x, Lukáš Horký, Erika Sedláčková, Jan Peřina, Pavel Zeman). Smazaný formulář se netýkal **nikoho** — nedal se otevřít.

