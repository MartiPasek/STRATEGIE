# Podminky (narok D/DN/SD i ostatni) jdou nove editovat primo v karte zamestnance v ERP (17.8.2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


> ⚠️ **DOPLNĚNO 19. 8. 2026 (Claude-28, schválila Marti-AI). Obsah pod tímto rámečkem jsem needitoval.**
> Od 19. 8. 2026 večer **`tenant.staff_cond` už není tabulka, ale POHLED.** Osobní hodnoty podmínek
> fyzicky žijí ve smlouvě (`tenant.engagement`, sloupce `pod_*` + `pod_meta`) a verzují se s ní.
> Skupinové a systémové výchozí hodnoty se **20. 8. 2026 přejmenovaly na `tenant.podminky_vychozi`**
> (dřív `staff_cond_zaklad`) a slouží už jen jako číselník výchozích hodnot — osobní řádky tam nepatří.
> **Doplněno 20. 8. 2026 (Claude-28, schválila Marti-AI):** od kroku 3a má každý člověk všechny hodnoty
> zapsané u sebe ve smlouvě, takže pohled `staff_cond` vrací **jen osobní řádky**, a spouštěč
> `trg_staff_cond_default_dovolena` na `att_employee` byl **ZRUŠEN** — nahradil ho `engagement_pod_defaults`
> na smlouvě.
> **Čtení i zápis přes `tenant.staff_cond` funguje dál úplně stejně** — ověřeno porovnáním otisků
> před a po (294 řádků i 1248 vyřešených hodnot bez rozdílu), takže **text níže platí dál**;
> změnilo se jen to, kde data fyzicky leží. Kdo bude sahat na strukturu nebo na spouštěče,
> ať si nejdřív přečte znalost **`doc-dochazka-podminky-slouceny-se-smlouvou`**.

---


# Editace Podminek v karte zamestnance v ERP

**Zadal Jirka 17. 8. 2026, schvalila Marti-AI.** Zapsal Claude-28.

## Co bylo predtim
Narok na dovolenou, dovolenou navic a sick days (a vsechny ostatni podminky z `tenant.staff_cond`)
sel menit **jen v mobilni appce**: HR -> Podminky -> Jednotlivci -> clovek
(fragment `48_hr_podminky_me.js`, endpoint `POST /app/hr/conditions/save`).

V ERP to neslo nikde:
- karta zamestnance, sekce Podminky (`karta_zamestnance.html`, funkce `podmUdaje`) = jen tabulka bez policek,
- prehled "Podminky zamestnancu" ma v hlavicce primo napsano "Jen ke cteni".

Tim zustal nedodelany bod 1 z rozhodnuti o naroku D/DN/SD (varianta a = editace primo v karte).

## Co se zmenilo
`podmUdaje` prepsana na dvojici `renderPodm(edit)` + `podmSave()` (commity `5516be08`, `565de50d`).
Vzor je stejny jako u ostatnich sekci karty: odkaz **"Upravit"** prepne radky na policka,
pak **"Ulozit" / "Zrusit"**.

- Prazdne policko = hodnota se dedi ze skupiny nebo ze systemu. Vyplnene = osobni vyjimka.
- Uklada se **jen to, co se opravdu zmenilo**, kazda podminka zvlast (endpoint bere jednu).
- Vysledek jde do stavoveho radku nad tabulkou, **ne do `alert()`** - at je videt, co proslo a co ne.
- Editovatelnych je 15 z 16 podminek. **"Dovolena celkem (pocita se)" policko vubec nedostane** -
  je to pocitadlo, soucet drzi databazovy trigger a endpoint rucni zapis do `dovolena_dni` odmita.
- Marti-AI rozhodla **editovat vsechny podminky, ne jen D/DN/SD** ("jednotny vzor s mobilem,
  zadne specialni pripady").
- Marti-AI zaroven rozhodla `karta_zamestnance.html` pri teto prilezitosti **NEmigrovat** do
  `g2007.soubor` (2245 radku, vetsi zasah nez sama uprava; migrace ma byt samostatny ukol).

## Prava a audit - nic noveho se nepridavalo
Cteni i zapis hlida **stejna funkce `_hr_can_manage`** (rodic NEBO clen skupiny HR),
takze kdo sekci vubec uvidi, ten smi i zapsat; ostatni dostanou 403 a sekce ukaze zamek.
K 17. 8. 2026 je to 8 lidi: Marti (1), Kristyna (11), Sarka Novotna (13), Petra Safrankova (18),
Jiri Honomichl (20), Petra Fajmonova (107), Marta Safarikova (108), Tomas Hrbek (109).
Audit `staff_cond.changed_by` + `changed_at` zapisuje endpoint sam.

## Poznamka u radku (`note`) - VYRESENO 17. 8. 2026
`/app/hr/conditions/save` je napsany jako **DELETE + INSERT** a `note` bere z tela pozadavku,
takze kdo ji neposle, ten ji smaze. Prave u naroku D/DN/SD je v poznamce zapsane, odkud
hodnota pochazi (napr. "rozpad dnesni celkove dovolene, hodnota ze stare tabulky
engagement_entitlement se zamerne neprenasela") - prvni editace HR by ty vety tise zahodila.

Marti-AI rozhodla poznamku **zachovat**. Reseni je cele na strane karty, `router.py` se nemenil:
`podmSave()` vezme stavajici `note` z uz stazeneho `own` a **posle ji zpatky beze zmeny**.
Pri MAZANI hodnoty (prazdne policko) se `note` zamerne NEposila - endpoint pak radek smaze
a vrati se dedeni; s poznamkou by po sobe nechal prazdny radek navic.
Endpoint poznamku orezava na 300 znaku; nejdelsi poznamka v `staff_cond` ma 141 znaku,
delsi nez 300 nema zadna, takze orez nehrozi.

**Mobil zustal jak byl** (rozhodnuti Marti-AI) - tam se poznamky nezobrazuji a nikdo s nimi
nepracuje, takze editace z appky poznamku porad smaze.

## Overeno naziva na ostrych datech (karta Jiriho Honomichla, user 20)
1. Osobni vyjimka `absence_nahlasit_do` = 09:45 -> v DB radek s `changed_by=20` a casem zapisu
   -> policko vyprazdneno -> radek smazan, hodnota zpet na systemovych 09:00.
2. Zachovani poznamky: `stravenka_kc` (hodnota 0, poznamka "sync Centrála 23.7.") zmenena
   na 0.0 a zpet na 0 -> **poznamka prezila obe zmeny**.
3. Po testech ma user 20 presne tech samych 4 radku se stejnymi hodnotami i poznamkami.
   **Jedina zbyla stopa:** u `stravenka_kc` je ted `changed_by=20` a dnesni `changed_at`
   misto puvodnich `13` / 23. 7. 2026. Hodnota ani poznamka se nezmenily; audit se
   prepisovat zpetne nebude, protoze zapis se opravdu stal.
Syntaxe JS overena pres `node --check` pred obema nasazenimi.

