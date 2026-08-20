# Konec session: co presne zkontrolovat, aby se pri soubehu instanci nic neztratilo (overeno 17.8.2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

## Proc

Na projektu pracuje soucasne vic Claude instanci a lidi. **Neutralni navratovka ani "deploy OK"
nestaci** - prace muze tise viset na tri ruznych mistech najednou. 17. 8. 2026 se pri zaverecne
kontrole naslo, ze **necommitnuta dokumentace Jirky visela 11 dni** (`docs/ec_view_vytizeni_nepritomnost_rollback.md`,
159 radku, dopsana 6. 8.). Pri kazdem `git pull` pres most se jen odlozila (`autostash`) a zase
vratila - navenek to vypada nevinne, ale staci jeden konflikt pri rebase a je pryc.

## Kontrolni seznam na konec session (vsech pet, ne jen git)

**1. Git - lokal vs. origin**
```
git status -sb | first line     -- "## main...origin/main" BEZ cisel = srovnano
git status --porcelain          -- prazdne = nic neceka
```
Kdyz neco visi, **podivej se ci to je** (`git diff`, podpis v souboru) a **zeptej se autora**,
nemaz to a necommituj naslepo. Cizi rozdelana prace muze byt zamerne rozdelana.

**2. g2007.soubor - nepublikovane fragmenty**
```
SELECT kod, updated_by_text FROM g2007.soubor
WHERE typ='zdroj' AND kod LIKE 'apps/api/static/mobile_parts/%'
  AND updated_at > (SELECT updated_at FROM g2007.soubor
                    WHERE kod='apps/api/static_db/mobile.html' AND typ='artefakt');
```
⚠️ **Cesta artefaktu musi byt spravna** (`static_db/`, ne `static/`). Se starou cestou vrati
poddotaz NULL, porovnani je NULL a dotaz tise vrati 0 radku = **falesne "cisto"**. Overit, ze
artefakt v poddotazu vubec existuje.

**3. g2007.python - prezily moje zmeny?**
Nestaci `updated_by_text = 'ja'` - **jina session mohla tutez funkci upravit po tobe** a tvoje
jmeno prepsat. 17. 8. se to stalo u `att_absence_request`: md5 nesedelo, autor byl jiny, ale
`strpos(zdroj,'req_id') > 0` ukazalo, ze zmena tam **je** - druha session ji korektne zachovala.
**Proto se neptej "je tam muj otisk", ale "jsou tam moje konkretni casti"** - vyjmenuj si klicove
retezce a over kazdy zvlast.

**4. Pojistky** - `SELECT * FROM tenant.pojistky_check()` a **porovnat pocet proti zacatku session**.
Novy nalez = neco se rozbilo dnes. Rozlisuj `ZTRACENO` (vlastnost zmizela) od `CHYBA KONTROLY`
(pojistka se ani nespusti = nehlida vubec).

**5. Zprava lidem** - co ceka na jejich rozhodnuti, at to nezustane jen v chatu.

## Gotcha: sdilene kanaly mostu

`CLAUDE_NOTIFY.txt`, `CLAUDE_DEPLOY.txt` a pull/build **nejsou per-lane** - jina session ti je
prepise pod rukama. 17. 8. byl `CLAUDE_NOTIFY.txt` prepsan cizi zpravou behem par vterin.
**Odeslani notifikace proto over ctenim** (`SELECT ... FROM fw.mobile_command WHERE target_user_id=...
AND created_at > now() - interval '30 minutes'`), ne tim, ze jsi soubor zapsal.
Lane ma **jen samotny SQL dotaz** (`CLAUDE<N>_SQL.sql`).

## Gotcha: deploy vysledek muze patrit nekomu jinemu
`CLAUDE_DEPLOY_OUT.txt` je take spolecny. Po zapisu `_GO` **cekej na zmenu casove znacky**, ne na
pritomnost "DEPLOY: OK" - jinak si prectes vysledek cizi session (17. 8. se to stalo, commit
`2487f94f` patril jine praci).

