# Projekce znalostí do gitu (obnova přes /g2007/export?git=1) — nyní i s pastmi: sekundár bez git identity, souběžný push

> oblast: `system-g2007` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

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

