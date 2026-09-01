# V Opravach dochazky jen Prace, Cesta a Pauza - absence patri vyhradne do Spravy

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# V Opravách jen Práce, Cesta a Pauza — absence patří výhradně do Správy docházky

**Peťa, 1. 9. 2026.** Nasazeno týž den, bez deploye (obojí žije v databázi).

## Pravidlo

**Dovolená, sick day, lékař, neplacené volno, nemoc, OČR, mateřská, náhradní volno,
volna 70/80/90 a další nepřítomnosti se zadávají VÝHRADNĚ ve Správě docházky.**
V Opravách docházky zůstávají jen **Práce, Cesta a Pauza**. Home office tam nepatří
také — je to jen činnost, ne druh záznamu.

Tím se ruší dřívější pravidlo Peti z 21. 7. 2026 („omylem píchnutá práce se musí dát
přepsat na dovolenou nebo lékaře"), které bylo v komentáři u `TYPES` v okně Oprav.

## Proč — Opravy nekontrolují nárok

Ověřeno čtením zdrojů v `g2007.python` 1. 9. 2026. `att_fix_entry` i `att_fix_add`
volají z kontrol **jen `att_sd_kontrola`** (tvar sick daye, celé hodiny nebo půlden).
**NEVOLAJÍ** `att_limit_kontrola` (nepřečerpat nárok) ani `att_absence_hpd_kontrola`
(celý nebo půl dne podle úvazku). Přes tlačítko „Opravit" tedy šlo zadat absenci
komukoli, i s nárokem vyčerpaným do poslední hodiny.

**Doložený případ.** Dušan Havlát 5. 8. 2026 v 11.27 přepsal přes Opravy svoji vlastní
**přestávku 07.16–08.37 na sick day** (`att_entry` 9984131, 1,00 h). Ten se pak čtyři
týdny přehazoval mezi 1 a 8 hodinami — šest verzí, poslední 31. 8. 2026 ve 12.26.

## Co se změnilo (obojí ověřeno otiskem md5 po zápisu)

| Kde | Co | Stav po |
|---|---|---|
| `g2007.python` `att_fix_entry` | `_ATT_FIX_TYPES` zkrácen na `("work","commute","break")` | verze 8, md5 `a9df5436d790aee772372a161e9fcba3`, 23979 znaků |
| `g2007.python` `att_fix_add` | totéž | verze 7, md5 `92b64c370fccc6968e37d169337ab4b2`, 16850 znaků |
| `g2007.soubor` `apps/api/static_db/dochazka-opravy.html` | nabídka druhů filtruje přes nový `OPRAVY_TYPY` | verze 71, md5 `864bb942688f09940f1f3c0f11ba84bc`, 123231 znaků |

Z `_ATT_FIX_TYPES` vypadlo i `overhead` (Režie). V nabídce okna nikdy nebyla (filtrovala
se od 21. 7.), na serveru zůstávala. Peťa 1. 9. 2026 — „režie by nikde být neměla",
řeší se samostatně.

**Starý typ záznamu zůstává v roletce vidět.** Stejný vzor, jaký od 21. 7. platil pro
Režii — když záznam už nějaký nepovolený typ má, v nabídce se ponechá, jinak by se při
opravě časů potichu přepsal na Práci. `TYPES` proto zůstává úplný, mění se jen filtr
v `mkTyp`.

## Gotcha — artefakt se zapisuje na disk hned

`@@G2007SOUBOR` s typem `artefakt` zapíše obsah **rovnou i do `apps/api/static_db/`**
(`router.py`, větev `_typ3 == "artefakt"`). Žádný `@@G2007PUBLISH`, žádný restart,
žádný deploy — změna je živá okamžitě. U typu `zdroj` to neplatí, tam se publikuje.

## Co tím NENÍ vyřešeno

1. **Správa docházky přepisuje hodiny na celý den.** `/app/dochazka-abs/save`
   (`dochazka_absence_sprava.py` r. 1030) — když formulář pošle prázdné pole
   „Hodin za den", server dosadí denní fond z úvazku, tedy 8 h, a přepíše tím
   hodnotu, která v záznamu byla. U NOVÉ absence je to záměr z 18. 8. 2026,
   u ÚPRAVY je to chyba. **Tohle vyrobilo obě osmičky u Havláta**, ne člověk.
   Oprava má být — při úpravě brát prázdné pole jako „nech, co tam je".
2. **Nárok se při úpravě denního záznamu ve Správě nekontroluje.** `_narok_check`
   se volá jen u zakládání nové absence a u úpravy žádosti; větev B (úprava denních
   záznamů) ho nemá.
3. **Už existující absenční řádky** jde v Opravách pořád otevřít a upravit jim časy
   (typ se nezmění). Jestli se má i to zavřít, je otevřená otázka.

Souvisí: [[doc-dochazka-absence-hodiny-z-uvazku-vsechny-typy]] · [[doc-dochazka-sprava-dochazky-zadost-vs-den-a-fajfka]]

