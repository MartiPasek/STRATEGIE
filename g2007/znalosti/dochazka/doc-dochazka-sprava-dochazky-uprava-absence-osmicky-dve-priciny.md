# Správa docházky — úprava absence přepisovala hodiny osmičkou. DVĚ různé příčiny, obě opraveny 2. 9. 2026

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Úprava absence ve Správě docházky přepisovala hodiny denním fondem

Zadala Peťa (Petra Šafránková), řešil Claude‑26, 2. 9. 2026.

## Co se dělo

Když se ve Správě docházky otevřela **úprava** absence a uložila, hodiny na záznamu
se přepsaly **denním fondem z úvazku** (u plného úvazku osmičkou) místo toho, co na
záznamu bylo. Doložený případ — sick day Dušana Havláta (osobní číslo 105) z 5. 8. 2026.
V řetězci záznamů toho dne stojí dvě verze po 8,00 h, obě s poznámkou „úprava“ ze
Správy docházky, kolem verzí na 1,00 h a 1,35 h. Peťa to pokaždé ručně vrátila zpátky.

**Nešlo o jednu chybu, ale o dvě nezávislé — a to je na tom to podstatné.**
Kdo opraví jen jednu, chybu tím neodstraní.

### Příčina A — server bral prázdné pole jako „doplň fond“

`modules/erp/api/dochazka_absence_sprava.py`, endpoint `/app/dochazka-abs/save`.
Obě větve úpravy (žádost i denní záznamy) měly `if hpd is None → _fond_den(...)`.
Doplnění fondu při prázdném poli je **správné rozhodnutí z 18. 8. 2026, ale jen pro
NOVOU absenci** — tam se hodnota teprve rodí. Při úpravě záznam svoje hodiny už nese,
takže dosazení fondu je tiše přepsalo.

**Oprava** — při úpravě se prázdné pole čte jako „nech, co tam je“. U žádosti se vezme
`att_absence_request.hours_per_day`, u denních záznamů skutečné `att_entry.hours`
(jen když je mají dotčené dny stejné; při různých hodnotách není co zachovat a fond
je jediná rozumná hodnota). Fond zůstává poslední záchranou.

### Příčina B — formulář si hodnotu přepsal sám, asynchronně

`g2007.soubor`, artefakt `apps/api/static_db/dochazka-po-zakazkach.html`.
Okno úpravy pole nejdřív správně naplní z řádku přehledu (`HodinDen`), ale hned při
otevření se volá `absSetPrac` → `absNactiFond`, což si vyžádá denní fond ze serveru.
Ta odpověď doběhne **až po** naplnění pole a hodnotu **přepíše**. V okně tak svítil
denní fond a uložením se zapsal.

**Tohle je nejspíš skutečný mechanismus Havlátových osmiček** — formulář neposílal
prázdno, ale vyplněnou osmičku, takže samotná oprava A by případ nechytila.

**Oprava** — `absNactiFond` má na začátku `if(ABS_MODE!=='new')return;`. Denní fond
se předvyplňuje jen u NOVÉ absence, při úpravě nikdy.

## Poučení, které z toho plyne

**Když se hodnota v okně tváří „odnikud“, hledej i asynchronní dopočet, nejen to,
co formulář odešle.** Diagnóza z 1. 9. 2026 zněla „formulář posílá prázdné pole“ a
byla neúplná — vycházela z odeslaných dat, ne z pořadí, v jakém se pole plní.
Synchronní naplnění pole prohraje s odpovědí ze serveru, která přijde o chvíli později,
i když je v kódu napsaná dřív.

## Doplněno k témuž — kontrola nároku u úpravy denního záznamu

Při té příležitosti se ukázalo, že větev úpravy **denních záznamů** kontrolu nároku
(`_narok_check`) nevolala vůbec. Zákaz přečerpání z 26. 8. 2026 tak platil u nového
zadání a u úpravy žádosti, ale úpravou denního záznamu šlo absenci zvednout nad
zůstatek. Doplněno se stejným pravidlem jako u žádosti — hlídá se, jen když objem
roste nebo se mění druh; při zkracování ne, protože původní dny jsou v čerpání pořád
započítané a kontrola by křičela sama na sebe.

**Známé omezení** — z téhož důvodu umí kontrola při VELKÉM navýšení zakázat i to, co
by se ještě vešlo (původní objem se započítá dvakrát, protože `att_narok_osoba` vrací
zůstatek už po odečtení editované absence). Stejnou vlastnost má od 26. 8. 2026 i
větev u žádosti. Obchází se smazáním a zadáním znovu.

## Stav a co zůstává otevřené

- Nasazeno 2. 9. 2026 — commit `94fa6b1b` (server) a artefakt verze 59 → 60 (formulář).
- Peťa ověřila na obrazovce, že u Havlátova sick daye z 5. 8. svítí 1 h. Data byla
  srovnaná už předtím, opravovat nebylo co.
- **Pojistka na to NENÍ a být nemůže.** `tenant.pojistky_check()` čte databázi a
  serverová část opravy žije v souboru na disku. Hlídat to půjde, teprve až se
  Správa docházky přestěhuje do `g2007.python`. Do té doby to drží jen komentáře
  v kódu a tahle znalost.

## Souvisí

- `doc-dochazka-sprava-dochazky-zapisuje-8h-misto-uvazku` — starší nález z 17. 8. 2026
  o osmičce natvrdo u ZADÁVÁNÍ. Vyřešeno rozhodnutím z 18. 8. (prázdné pole = podle
  úvazku). Tahle znalost popisuje, co z toho rozhodnutí omylem vyteklo do úpravy.
- `doc-dochazka-sickday-se-zadava-po-hodinach-ne-na-pulden` — pravidla pro povolené
  hodnoty, která na hodiny navazují.
- `doc-dochazka-sprava-dochazky-zadost-vs-den-a-fajfka` — proč jsou v té obrazovce
  dvě větve (žádost a den) a proč se chovají jinak.

