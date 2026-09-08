# Vyhledavani znalosti stoji na kouscich - prima uprava je nepreindexuje, a kod musi sedet s oblasti

> oblast: `system-g2007` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Vyhledavani znalosti stoji na kouscich - a co to znamena v praxi

Zjisteno a srovnano 8. 9. 2026 (Jiri Honomichl / Claude-28, schvalila Marti-AI msg 15041, 15047, 15056, 15086).

## 1. Bez kousku znalost NEEXISTUJE pro vyhledavani podle vyznamu

Hledani podle vyznamu jde pres `g2007.znalost_vector` na `g2007.znalost_chunk` a teprve
odtud na `g2007.znalost` (overeno v zivem kodu `modules/erp/api/g2007_vectors.py`).
**Znalost, ktera nema kousky, nemuze byt vracena vubec.** Pres hledani podle slov
(`obsah ILIKE`) se najde porad - proto se to nikde neprojevi jako chyba.

## 2. Prima uprava obsahu kousky NEPREPOCITA

`@@G2007ADD` reindexuje sam. Ale **primy `UPDATE g2007.znalost SET obsah=...` pres most
kousky nechá byt** - obsah je novy, hledani vraci **starou verzi** a nic to nehlasi.
Presne tak se stalo, ze znalost o plzenskem prostredi mela text z 8. 9., ale hledani
u ni znalo verzi z 21. 7.

**Prepocet:** `POST /api/v1/erp/app/g2007/index` s telem `{"id": <cislo>}` (bez id prepocita
vsechny aktivni). Vyzaduje prihlaseni a okruh rodic/cockpit - **z mostu to nejde**, jen
z prohlizece nebo z aplikace. Vraci `{"ok":true,"znalosti":N,"chunku":M}`.
**Overuj vysledek ctenim z databaze**, ne navratovkou prohlizece.

**Jak najit dira:** znalosti bez kousku = `(SELECT count(*) FROM g2007.znalost_chunk c
WHERE c.znalost_id=z.id) = 0`; zastarale hledani = nejnovejsi kousek starsi nez `updated_at`.
Ke dni 8. 9. 2026 bylo ze 733 aktivnich znalosti **17 bez kousku** (mimo jine `most-kanaly`,
na kterou odkazuje rozcestnik k mostu) a **4 se zastaralym hledanim**. Vse srovnano.

## 3. Kod znalosti musi sedet s oblasti - jinak vznikne tichá kopie

Kod ma tvar `doc-<oblast>-<slug>`. Kdyz nesedi, `@@G2007ADD` si kod slozi z oblasti a slugu,
puvodni znalost nenajde a **misto upravy zalozi kopii vedle** - original zustane a nikdo
se to nedozvi. K 8. 9. 2026 takovych kodu bylo **101** a vsechny byly srovnany.

## 4. Dve pasti pri hromadnem prejmenovani (obe zazite naostro 8. 9. 2026)

**a) Kratsi nazev byva uvnitr delsiho.** `vize` je uvnitr `doc-vp-ai-rizeni-vize`,
`zdroj-pravdy` uvnitr `jeden-zdroj-pravdy`, `doc-rozvadece` na zacatku `doc-rozvadece-pravidla`.
Slepe nahrazeni textu takovy nazev rozseka. **Nez zacnes menit texty, roztrid nazvy** na
rozlisitelne retezce a na obycejna slova (`schema`, `vize`, `nastroje`, `composer`,
`inkarnace`, `zdroj-pravdy`) - u slov prejmenuj JEN kod a do textu vubec nesahej,
protoze jejich vyskyty jsou bezna slova ve vetach (`input_schema`, `chyba_nastroje`).

**b) Jeden pruchod vymeni v jednom textu jen JEDEN odkaz.** `UPDATE ... FROM (mapa)` pouzije
na kazdy radek jen jednu dvojici, takze text se dvema odkazy zustane z poloviny stary.
Po hromadnem prepisu **vzdy dohledej zbytky** dotazem pres vsechny dvojice - 8. 9. jich
takto zbylo deset a jinak by tam zustaly.

## 5. Kotva pro cilenou upravu casto nesedi kvuli ZALOMENI RADKU

Texty znalosti jsou tvrde zalomene. Co ve vypisu vypada jako mezera, byva `\n` - a
`replace()` pak nenajde nic, **navratovka mostu pritom hlasi uspech**. Stalo se to 8. 9.
tikrat za sebou. Kdyz kotva nesedne, podivej se na bajty
(`encode(convert_to(substring(obsah from position(...) for N), 'UTF8'), 'hex')`) a zalomeni
do kotvy zahrn. **Po kazde uprave overuj ctenim, ne navratovkou.**

