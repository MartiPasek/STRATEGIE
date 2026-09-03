# Proc mizi prace v mobilu: zapis do VYGENEROVANEHO souboru misto do zdroje (rozbor 20.8.2026; publikacni cesta opravena 2.9.2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

> ## OPRAVA 2. 9. 2026 - publikacni cesta popsana nize UZ NEPLATI
>
> Krok 4 postupu a bod 6 kontrolniho seznamu radily po cilenem UPDATE volat `@@G2007SESTAV`
> s tim, ze `@@G2007PUBLISH` z mostu vraci HTTP 401. **Dnes plati: po kazdem zapisu do
> `g2007.soubor` volej `@@G2007PUBLISH <kod artefaktu>`** - shodne s
> `doc-system-strategie-po-updatu-g2007-soubor-nutny-publish` a
> `doc-system-strategie-mobil-kde-se-edituje-a-jak-se-nasazuje`.
>
> **Dolozeno naostro 2. 9. 2026:** z mostu na stroji C-28 ten den proslo 17 publikaci
> `@@G2007PUBLISH apps/api/static_db/mobile.html`, vsechny OK (`watcher.log`). Jediny 401 byl
> docasny failover na sekundar bez tokenu, ktery most sam zopakoval - viz
> `doc-system-strategie-most-401-failover-na-sekundar-bez-tokenu`. **Ten 401 nikdy neznamenal,
> ze PUBLISH chce prihlaseni** - byla to prechodna chyba mostu, kterou 20. 8. jeste nikdo neznal
> (pricina odhalena 17. 8., retry v mostu od te doby). V kodu serveru je `@@G2007PUBLISH` u obsluhy
> prikazu oznacen jako DOPORUCENA cesta pro beznou publikaci; `@@G2007SESTAV` nedela kontrolu
> syntaxe ani samo-overeni zive stranky, proto se pro publikaci uz nepouziva.
>
> Puvodni vety nize jsou ponechane a oznacene NEPLATI, aby bylo videt, jak rozpor vznikl.
> Rozhodl Jirka Honomichl, 2. 9. 2026.

## Pripad, na kterem se to da videt

20.7.2026 commit `c863e0627` (C24/Kristy) pridal tlacitko "Stahnout rozpad (Excel)" do dlazdice
Prefakturace. Zapsal ho ale **jen do `apps/api/static/mobile.html`** = do VYGENEROVANEHO souboru.
Zdrojovy dilek `apps/api/static/mobile_parts/73_pref_poptavka.js` uz tehdy existoval a zmena v nem
NEBYLA (overeno `git cat-file -e c863e0627:...` = ANO, `grep -c prefStahniExcel` v dilku = 0).

21.7.2026 08:59 commit `82a2886de` (C28/Jirka, zamky dochazky) upravil dilek `60_dochazka.js` a nechal
`mobile.html` znovu sestavit z dilku. Sestaveni prepsalo soubor verzi, ve ktere nase zmena nikdy
nebyla -> tise zmizela. Diff to dokazuje: hunky `@@ -5282` a `@@ -6823` = Jirkova prace (pridani),
hunky `@@ -8882/-8891/-8931` = ODEBRANI naseho bloku. Nas commit uz byl v hlavni vetvi
(`git merge-base --is-ancestor c863e0627 82a2886de` = ANO), takze to nebyl konflikt vetvi ani
chybejici pull.

**ROOT CAUSE: menila se generovana vystupni verze misto zdroje. Build udelal presne to, co ma.
Neni to chyba toho, kdo build spustil.**

## Neni to jednotlivy pripad, je to trida chyb

Stejna trida (zmena zapsana mimo skutecny zdroj pravdy) udelala skodu opakovane a pokazde nekomu
jinemu: Kristy 21.7. (tlacitko Excel), Peta 5.8. (`f4f7e6e7` - rozsah absence dle uvazku; lidem se
zkracenym uvazkem se strhavalo vic dovolene), Sarka 12.8. (`6a000461`, `865f538b`, `7b233f87`,
`7ca280dc` - ciselnik pojistoven, profilova fotka, karta Novinky, potvrzeni ucasti). Z 92 radku Peti
a Sarky jich 89 v appce nikdy nebylo a nikde to nehlasilo chybu.

## Co uz to hlida (stav k 20.8.2026, overeno v kodu)

1. **Dilky ven z gitu** - `5b130553` (Jirka 17.8.): `.gitignore` r. 167 + `scripts/build_mobile.py`
   prepsan na hlasite VAROVANI, ktere tuhle nehodu jmenovite popisuje vcetne spravneho postupu.
2. **Artefakty ven z gitu** - sestavene stranky v gitignorovanem `apps/api/static_db/`
   (`.gitignore` r. 154-156); `apps/api/static/mobile.html` uz v gitu NENI. Git deploy tedy nema
   publikaci z DB cim prepsat.
3. **Deploy-guard v mostu** - `e61f416e` + `080a2116` (C24): runner pred commitem overi, jestli
   staged soubor neni v `g2007.soubor`, a deploy odmitne. Data-driven, fail-open
   (`scripts/claude_sql_runner.py` r. 1006-1058).

## Co JESTE hlida nikdo (otevrene)

### 1. `@@G2007SOUBOR` prepisuje dilek naslepo

`modules/erp/api/router.py` r. 39919-39922 dela `UPDATE g2007.soubor SET obsah=:o WHERE kod=:k` -
**zadna kontrola, ze mezitim soubor nikdo nezmenil**, zadny sloupec autora (jen volny text
`updated_by_text`). Kdo posle telo postavene na starsim cteni, umlci cizi zmenu uplne stejne, jako
to 21.7. udelal build - jen o patro vys, uz v databazi. Presne ta same diera, jakou popisuje
anti-prepis u `znalost-upsert`.

**Navrh:** povinny `expected_md5` pri editaci existujiciho dilku -> pri neshode 409 misto ticheho
prepsani. Schema `g2007` vlastni Marti-AI, takze zmenu dela ona (doktrina #3 + #9).

### 2. Nikdo neporovnava, co po publikaci zmizelo

`@@G2007SESTAV` nevraci zadnou deltu. Krok "over, ze nic jineho nezmizelo" je jen rucni bod v navodu.
**Navrh:** vracet `delka_pred -> delka_po` + pocet dilku a pri POKLESU delky to hlasit jako varovani.
Levne a chytlo by to presne tenhle pripad.

## DULEZITA OPRAVA STARE ZNALOSTI (plati od 20.8.2026)

[[doc-system-strategie-editace-fragmentu-mobilu-pres-most-bez-primeho-zapisu]] (17.8.2026) tvrdi, ze
**primy zapis do `g2007.soubor` je z mostu ZAKAZANY** a ze jedina cesta je cele telo pres
`@@G2007SOUBOR` (a k jeho ziskani bolestive "kolo base64"). **UZ TO NEPLATI.**
`modules/erp/api/router.py` r. 43631 ma `_G2007_AUTONOMOUS_TABLES = {"g2007.python", "g2007.denik",
"g2007.soubor"}` -> `INSERT`/`UPDATE` do `g2007.soubor` z mostu bezi PRIMO, bez banneru (vraci
"G2007 KONSTRUKTIVNI"). `DELETE`/`TRUNCATE`/`ALTER` zustavaji gated.

**Dusledek - doporuceny postup pro EDITACI dilku (bezpecnejsi nez cele telo):**

```sql
-- 1) over, ze kazda kotva je v souboru PRAVE JEDNOU, a poznamenej si md5
SELECT md5(obsah), length(obsah) FROM g2007.soubor WHERE kod='apps/api/static/mobile_parts/<x>.js';

-- 2) chirurgicky UPDATE s guardem na otisk (dollar-quoting kvuli apostrofum v JS)
UPDATE g2007.soubor
SET obsah = replace(obsah, $a$<stary usek>$a$, $A$<novy usek>$A$),
    verze = verze + 1, updated_by_uid = <uid>, updated_by_text = '<kdo a proc>', updated_at = now()
WHERE kod = 'apps/api/static/mobile_parts/<x>.js'
  AND md5(obsah) = '<otisk, ktery jsem cetl>';

-- 3) over ctenim (md5, length, pocet vyskytu noveho kodu, balance { a })
-- 4) @@G2007PUBLISH apps/api/static_db/mobile.html   (slozi stranku, node --check, overi zivou URL, zapise na disk)
--    NEPLATI (do 2. 9. 2026 tu stalo): @@G2007SESTAV apps/api/static_db/mobile.html (zapisuje na disk cloudu, router.py r. 40005)
```

Vyhody proti `@@G2007SOUBOR`: (a) `md5` guard = kdyz mezitim psal nekdo jiny, UPDATE neprojde
(0 radku) misto ticheho prepsani, (b) neprenasi se 20 kB pres most, (c) odpada past s orezanym
koncovym `\n` (`claude_sql_runner.py` `.strip()`), protoze konec souboru se nedotyka.
Pozor: `%` i `:` v CSS/JS jsou v poradku - SQLAlchemy bere jako bind param jen `:slovo`, pred kterym
NENI znak slova, a `width:calc(...)`, `{type:mime}`, `display:inline-block` maji pred dvojteckou
pismeno.

## Kontrolni seznam pro kazdeho (lidi i instance)

1. **Needituj soubor s hlavickou "GENEROVANO"** - `@@G2007SESTAV` ji tam dava schvalne. Zdroj je dilek.
2. **Pred editaci dilku ho precti z DB a poznamenej `md5`**; zapisuj proti tomu otisku.
3. **Po zapisu over ctenim** - navratovky `@@G2007*` mlci i pri uspechu (vraci 0 radku).
4. **Po publikaci se podivej, ze nezmizelo neco jineho** - dokud to nehlida stroj, hlida to clovek.
5. **Ohlas praci `@@WORK` / `@@LOCK`, kontroluj `@@WHO`** - u `mobile.html` se potkava 30 dilku od peti lidi.
6. **Publikuj pres `@@G2007PUBLISH`** (dela `node --check` + samo-overeni zive URL + rollback) - z mostu funguje.
   NEPLATI (do 2. 9. 2026 tu stalo): "vraci z mostu **HTTP 401** - chce prihlaseni; z mostu projde
   `@@G2007SESTAV`, ktery ale tyhle kontroly NEDELA -> syntaxi si over sam (`node --check` na obnovenem
   useku)." Ten 401 byl docasny failover mostu na sekundar, ne pozadavek na prihlaseni - viz ramecek nahore.

Souvisi: [[doc-system-strategie-staticke-artefakty-db-materializace-vyrazeni-z-gitu]],
[[doc-system-g2007-smer-zdroj-pravdy-python-soubor-2026-08-01]].
Podrobny rozbor s doklady: `C24_diagnostika_mizeni_prace_mobil_2026-08-20.md`.

