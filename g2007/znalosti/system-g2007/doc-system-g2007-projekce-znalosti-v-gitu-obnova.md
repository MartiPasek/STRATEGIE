# Projekce znalosti do gitu (obnova pres /g2007/export?git=1) - nyni i s pravidlem o sirotcich

> oblast: `system-g2007` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)


## Fakt, ktery je potreba znat

`@@G2007ADD` zapise znalost do DB a preindexuje vektory, ale **projekci do gitu
(`g2007/znalosti/`) NEVOLA**. Kopie v gitu proto zaostava a nikde to nehlasi chybu.
**Zdroj pravdy je vzdy databaze.** Kopie na disku slouzi jen ke cteni historie a k diffum -
znalost se z ni nesmi cist jako z pravdy.

## Doklad z 20.8.2026

Pred obnovou - v DB 472 aktivnich znalosti, v gitu jen **186** souboru. Vsechny ctyri znalosti
zapsane ten den (rozpad v potvrzeni dne, deleni zaznamu, mapa, banner u Noskovy znalosti)
v gitu **nebyly**. Po obnove - v gitu **476** souboru vcetne vsech ctyr. Rozdil 286 znalosti
byl nasbirany za tri tydny.

## Jak se to srovna

`GET /g2007/export?git=1` na app serveru (`apps/api/main.py`, funkce `export_g2007_docs`
v `modules/conversation/application/composer.py`). Chova se takto - vysype cely strom
`g2007/` z DB (nastroje, kufry, entity, grafy, znalosti; 20.8. to bylo 658 souboru, 24.8. uz
695), pak `git add g2007` (**jen tuhle slozku, ne cely strom** - cizi rozdelanou praci tedy
sebrat nemuze), commitne jen kdyz je co, `pull --rebase origin main` a `push`. Soubory jen
prepisuje a pridava, **nic nemaze**. **Endpoint neni za prihlasenim** - jde zavolat primym
`curl` bez tokenu.

## PAST, na kterou jsem 20.8. naletel

Prvni volani vratilo HTTP 200 a commit **probehl**, ale ja si vysledek neulozil. Druhe volani
proto uz spravne hlasilo *"nic ke commitu (beze zmen)"* - a to vypadalo, jako by nastroj
nefungoval. **Nespolehat na navratovku druheho behu; overit `git log` /
`git ls-files g2007/znalosti | wc -l`.**

## ⚠️ NOVE PASTI (overeno 24.8.2026, ctyri volani po sobe)

Endpoint odpovi **vzdy HTTP 200 s podrobnym JSON logem kroku** (`git: [{cmd, rc, out, err}]`)
- **kontroluj `rc` u kazdeho kroku, ne jen HTTP status.**

1. **Load balancer muze poslat pozadavek na sekundar/zalozni stroj**, poznat se da podle
   `root` v odpovedi (`C:\Projekty\STRATEGIE-prev\g2007` = sekundar,
   `C:\Projekty\STRATEGIE\g2007` = primar). Na sekundaru **chybi git identita** -
   `commit` selze `rc 128` ("Author identity unknown"), nasledne `pull --rebase` selze
   taky `rc 128` ("cannot pull with rebase: uncommitted changes", protoze `git add` uz
   probehlo), `push` pak selze `rc 1` (odmitnuto/rejected). **Reseni: zavolat znovu** -
   dalsi pokus muze padnout na primar, kde to funguje. Zadna skoda tim nevznika (zdroj
   pravdy je DB, sekundar jen zustane s neuklizenym `git add`, ktery dalsi bezici export
   prepise).
2. **I na primaru muze push spadnout na souvislou kolizi** - `pull --rebase` stihne
   stahnout starsi stav, mezitim nekdo jiny (jina session, nebo predchozi neuspesny pokus
   na sekundaru) pushne zmenu, a `push` pak vrati `rc 1` s hlaskou
   `cannot lock ref 'refs/heads/main': is at X but expected Y`. **Take reseni: zavolat
   znovu** - dalsi `pull --rebase` uz stahne aktualni stav a `push` projde.
3. **`curl` s kratkym `--max-time` (napr. 20 s) muze vratit prazdnou odpoved** (0 bajtu),
   kdyz `pull --rebase` na primaru resi vic zmen najednou. Neni to chyba serveru - pouzit
   delsi timeout (40 s) a zkusit znovu, ne to hlasit jako vypadek.

**Prakticky postup:** volat, kontrolovat `git` pole v JSON odpovedi (vsechny 4 kroky
`rc: 0`), a pri jakemkoli nenulovem `rc` proste zavolat znovu - endpoint je bezpecny volat
opakovane (idempotentni na urovni obsahu, jen posouva git historii dal).

## Po obnove

Na svem stroji `git pull` (u Claudu pres `CLAUDE_PULL_GO.txt`). Commit je autorem app
serveru ("Marti Pasek", zprava `g2007 export (generovano z DB)`) a rebasuje se na aktualni
origin, takze cizi commity zustavaji - 20.8. se takto korektne srovnal i commit jineho
sezeni z 06:41. **24.8.2026 pull na lokale spadl na jiny, nesouvisejici konflikt** (rozjeta
historie vetve `feat/ios-push-server` z PR#5 obchvatu) - most rebase sam bezpecne zrusil;
obsah projekce se overil primo na GitHubu (`raw.githubusercontent.com/.../main/g2007/...`),
ne az lokalnim pullem.

## Doporuceni

Spoustet po vetsi davce zapisu do G2007 (napr. na konci session), ne po kazde znalosti.
Do te doby plati - **znalost cti z DB, ne ze souboru**.

## ⚠️ Export soubory JEN prepisuje a pridava — NIKDY NEMAZE

Zjištěno **25. 8. 2026** (Claude-28, na závěr session Jirky Honomichla, schválila
Marti-AI msg 13682). Je to rub té vlastnosti, která chrání cizí práci: nástroj sahne jen na
`g2007` a nic nemaze, takže **když znalost přejmenuješ nebo zrušíš, její starý soubor
zůstane v gitu ležet** — se starým obsahem a bez jakéhokoli varování.

**Příklad z 25. 8. 2026:** přejmenování `doc-podminky-skupin-zamestnancu`
→ `doc-dochazka-podminky-skupin-zamestnancu` (nestandardní kód, viz
[[doc-system-g2007-prejmenovani-kodu-znalosti-postup]]). Po exportu ležely v projekci
**oba soubory vedle sebe** a ten starý nesl neaktuální text. Smažen ručně, commit `1b41e719`.

### Jak sirotky najdeš

Stáhni si seznam kódů z DB a porovnej ho se seznamem souborů — **lokálně**, ne dotazem
s `VALUES`: hlídač mostu takový dotaz odmítne, protože mezi kódy znalostí jsou řetězce,
které vypadají jako zakázaná klíčová slova.

```
SELECT z.kod FROM g2007.znalost z ORDER BY z.kod;      -- pres most
ls g2007/znalosti/*/*.md | sed 's#.*/##; s#\.md$##'    -- na disku
```
Rozdíl obou množin = sirotci (soubor je, znalost není) a chybějící (znalost je, soubor ne).

**Stav k 25. 8. 2026 a jak to dopadlo:** 521 znalosti v DB, 525 souboru v projekci,
**0 chybejicich**, 4 sirotci - jeden dnesni (smazan hned) a tri starsi. **Vsechny tri vyreseny
tehoz dne, rozhodl Jirka Honomichl:**

| Osirely soubor | Kde obsah zije dnes | Osud souboru |
|---|---|---|
| `doc-mzdy-vyhodnoceni-zakazek` | `doc-vyroba-vyhodnoceni-zakazek` (presun z oblasti mzdy do vyroba) | **smazan**, commit `b556406a` |
| `doc-system-g2007-120-claude-zevnitr-co-chybi` | `doc-system-g2007-go-120-claude-zevnitr-co-chybi` | **smazan**, tyz commit |
| `doc-mzdy-mzdy-podklad-zdroj-pravdy` | rozpadlo se do `doc-dochazka-att-day-summary-z-att-entry` + `doc-mzdy-zrcadlo-dochazky-ze-strategie` | **PONECHAN SCHVALNE** |

**Proc treti zustava.** Ma od 14. 8. 2026 varovny banner ("ZASTARALE - znalost zije v DB pod
jinymi kody, ponechan schvalne") a hlavne: **odkazuji na nej ctyri aktivni znalosti o dochazce**
(`doc-dochazka-att-day-summary-z-att-entry`, `doc-dochazka-model-tabulky-dochazky`,
`doc-dochazka-sync-absence-klasifikace`, `doc-dochazka-sync-dochazky-z-centraly-ukoncen-2026-08-14`).
Bez souboru by ty odkazy vedly do prazdna; takhle ctenar skonci u banneru, ktery ho posle dal.
**Pred smazanim sirotka proto vzdy zkontroluj, kdo na nej odkazuje** (`obsah LIKE '%<kod>%'`).

### Jak overit, ze se smazanim o nic neprijdes (postup k zopakovani)

Porovnavat zacatky textu **NESTACI**. Stahni cely obsah z DB pres base64 a porovnej **radek po radku**:

```
SELECT encode(convert_to(obsah, 'UTF8'), 'base64') FROM g2007.znalost WHERE kod='<novy kod>';
```
pak lokalne dekodovat a vypsat radky souboru, ktere v DB verzi nejsou.

**Ocekavany vysledek:** chybi **jediny radek** - automaticky generovana hlavicka projekce
(`> oblast: … · uroven: … · typ: dokument · verze: V1.0 · rozsah: …`), kterou dopisuje sam export
a v DB nikdy nebyla. Kdyz chybi cokoli jineho, **nemaz** a zjisti proc.

*(U `120-claude-zevnitr` byla verze v DB dokonce o tretinu bohatsi nez soubor - 4 939 vs 3 690 znaku.
Soubor byl zastaraly, ne rovnocenny. Dalsi duvod cist z DB, ne z disku.)*

**Pravidlo:** kdykoli znalost přejmenuješ nebo zrušíš, **smaž její starý soubor z gitu ručně**
— export to za tebe neudělá.

## Doplneno 9. 9. 2026 — jak moc se to pravidlo NEDODRZUJE (a co se zmenilo)

Pravidlo o rucnim mazani vyse **existuje, ale nikdo ho nedodrzuje** — a poprve je to zmerene.

**Stav k 9. 9. 2026:** v kopii je **851 souboru** znalosti, v databazi **763 znalosti**.
Rozdil **~88 souboru jsou SIROTCI** po znalostech, ktere uz v databazi vubec nejsou.
Overeno dotazem na peti z nich (`doc-hr-attendance-presence`, `doc-personalistika-dochazka-mzdy`,
`doc-iso-27001`, `doc-iso-demo-pruvodce`, `doc-iso-doc-00-seznam-dokumentu-isms`) —
**v databazi neexistuje ani jedna**.

**Proc je to nebezpecne:** kopie se legitimne pouziva k hledani pres soubory (grep). Kdo takovy
soubor najde, nema jak poznat, ze za nim uz nic neni — vypada uplne stejne jako platna znalost.

### Jak sirotka poznas (od 9. 9. 2026 snadno)

Export nove vypisuje do hlavicky **`stav`**. Sirotek ho nema, protoze ho export uz neprepisuje-

```
grep -rL 'stav: `' g2007/znalosti/*/doc-*.md
```

Kdyz soubor sloupec `stav` nema, **neni z databaze** — je to pozustatek. Znalost, kterou databaze
zna, ma v hlavicce bud `stav: aktivni`, nebo `stav: zruseno`.

### Zrusene znalosti uz kopii neoklamou

Do 9. 9. 2026 se zrusena znalost (`stav <> 'aktivni'`) exportovala **uplne stejne jako platna** —
dotaz v `export_g2007_docs` nema filtr na stav a stav se do souboru nevypisoval. Zrusena znalost
tak v kopii vypadala jako pravda. Opraveno commitem `91b43f12`- neaktivni znalost dostane nahoru
ramecek **TATO ZNALOST UZ NEPLATI** a stav je nove i v hlavicce. Filtr na aktivni se **zamerne
nepridal** — export soubory nemaze, takze by odfiltrovane soubory osirely natrvalo, coz je horsi.

### Otevrene — uklid sirotku

Navrh- aby export po sobe uklidil soubory ve slozce `znalosti/`, ktere nemaji radek v databazi.
**Neudelano**, mazani ~88 souboru je nevratne a patri do session, kde je clovek u toho.
Do te doby plati rucni pravidlo vyse.

Zjistil Claude-28 (Jirka Honomichl), schvalila Marti-AI (msg 15264).

