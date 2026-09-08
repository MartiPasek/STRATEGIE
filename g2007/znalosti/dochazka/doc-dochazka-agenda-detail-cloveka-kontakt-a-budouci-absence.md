# Mobil, agenda (Firma → Agenda → dlaždice): tři filtry, řádek člověka a jeho detail (8. 9. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Mobil — obrazovka agendy: filtry, seznam lidí a detail člověka

**Zadal Jirka Honomichl 8. 9. 2026, schválila Marti-AI (msg 15050, 15065, 15092, 15101).**
Týká se **jen režimu agendy** (`mode='group'`, tj. Firma → Agenda → dlaždice).
Konzole **Výroba spouštěná z Aplikací** (`mode='vyroba'`) zůstala beze změny — má dál
celý stavový panel i spodní sekci (Zakázky, Odvozy, Příprava).

## 1. Pravý panel = tři filtry místo stavového žebříčku

Původní panel (Tým / mimo plán / Chybím / Makám / Relaxuji / Informuji / Potřebuji / Čekám /
Už jedu / Finišuji) je v agendě nahrazen třemi:

| filtr | koho ukáže |
|---|---|
| **Všichni** | výchozí po otevření agendy |
| **Pracující** | stav `makam`, `cekam` nebo `pauza` (je ve směně, pauza se počítá jako práce) |
| **Nepracující** | zbytek — `jedu`, `pryc`, `byl`, prázdno |

**Kdo má příznak „Bez docházky" (`tenant.engagement.pod_bez_dochazky`), je VŽDY mezi
Pracujícími** — docházku nevede, takže o něm docházka nic neřekne. Rozhodl Jirka.
K 8. 9. 2026 se to týká pěti lidí v agendách.

**Výchozí filtr se vynucuje.** Do 8. 9. se dědil naposledy použitý filtr (typicky „Makám"),
takže se agenda otevřela prázdná s hláškou „Nikdo zrovna nemaká", i když měla 35 členů.
Teď se při otevření agendy pohled vždy přepne na `vsichni`.

## 2. Řádek člověka

- vlevo **Příjmení Jméno** (⭐ vedoucí, 🎖 zástupce); kolečko s písmenem je pryč,
- pod jménem **stav**: `Pracuji` · `Pauza` · `dnes mám <absence>` · `Nepracuji`,
- vpravo **osobní číslo** (`tenant.att_employee.cislo_zam`).

**Živý stav má přednost před absencí** — kdo právě pracuje, má „Pracuji", i když má dnes
třeba dvě hodiny lékaře. Rozhodl Jirka.

**Každý typ absence se pojmenuje svým jménem** (dovolenou, sick day, lékaře, nemoc, OČR,
mateřskou, náhradní volno, neplacené volno, volno 70/80/90 %, nepřítomnost OSVČ).
Skloňování drží mapa `VY_ABS` v dílku `51_skupiny_sdileny.js`; když typ v mapě není,
použije se název z číselníku `tenant.att_entry_type`.

**Řazení: vedoucí → zástupce → zbytek podle české abecedy** (příjmení, jméno).
Platí i pro dlaždici **Všichni**, která se do 8. 9. řadila podle skóre výkonnosti — jedna
dlaždice s jiným chováním by byla tichá výjimka. Řadí databáze, viz
[[doc-system-strategie-ceske-razeni-nedelej-prevod-diakritiky]].

## 3. Detail po klepnutí na člověka

- **firemní e-mail**, nebo text „nemá firemní email",
- **pracovní telefon**, nebo text „nemá uvedené pracovní tel. číslo",
- **Nahlášené budoucí absence** (typ a datum), nebo „žádné nahlášené budoucí absence".

**Tlačítko „Zobrazit dnešek" bylo z detailu odstraněno** (Jirka 8. 9. 2026, Marti-AI msg 15101).
⚠️ Bylo to **jediné místo v celém obsahu mobilu, které volalo `openPersDnesek`** — funkce
i obrazovka `persDnesek` v kódu zůstávají, ale z agendy na ně už nevede cesta. Je to **záměr,
ne opomenutí**; úklid osiřelé obrazovky Jirka zatím nezadal.

## 4. Zdroje dat — tytéž jako v ERP

| údaj | zdroj |
|---|---|
| firemní e-mail | `tenant.user_self_data.company_email` (v osobní kartě „Firemní e-mail") |
| pracovní telefon | `tenant.user_self_data.company_phone` („Firemní telefon") |
| budoucí absence | `tenant.att_absence_request`, `stav='approved'` a `COALESCE(datum_do,datum_od) >= CURRENT_DATE` — totéž, co bere ERP na adrese `/app/hr/person-absence` |
| dnešní stav a absence | `tenant.att_entry` + `tenant.att_entry_type` pro dnešní den |

**Jiné pracovní telefonní číslo v databázi neexistuje.** „Firemní telefon" a „Pracovní mobil"
jsou dvě jména téže kolonky — ověřeno prohledáním všech sloupců na email/telefon/mobil.
Proto se u člověka bez vyplněného čísla píše rovnou „nemá uvedené pracovní tel. číslo".

⛔ **Osobní e-mail a osobní telefon se do mobilu neposílají vůbec** — nejsou ani v datech,
která aplikace dostane. Rozhodl Jirka Honomichl 8. 9. 2026.
Pozor, ERP to dělá jinak, viz [[doc-system-strategie-erp-pracovni-kontakt-padne-na-osobni]].

## 5. Kde to žije

- obsluha seznamu: `g2007.python` kód **`app_skupina_lidi`** (v jádře je jen tenká spojka),
- vzhled: dílky **`51_skupiny_sdileny.js`** (filtry, text stavu) a **`52_vyroba.js`**
  (kreslení panelu, řádku a detailu) v `g2007.soubor`.

## 6. Co zvážit do budoucna

Marti-AI (msg 15092) upozornila, že **budoucí absence kolegů včetně druhu vidí každý
zaměstnanec**. K 8. 9. 2026 je to neškodné — z 36 budoucích schválených absencí je 35 dovolená
a jednou home office, nic zdravotního. Kdyby si někdo dopředu nahlásil lékaře nebo nemoc,
bude to vidět celé firmě. Jirka o tom ví, zatím se nechává tak.

