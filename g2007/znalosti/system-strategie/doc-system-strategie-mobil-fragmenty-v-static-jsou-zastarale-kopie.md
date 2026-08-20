# Fragmenty mobilu v apps/api/static/mobile_parts jsou ZASTARALE kopie - ziva verze je v g2007.soubor (17.8.2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Kopie fragmentu mobilu na disku lze cist, ale nesmi se jim verit

> **VYRESENO 17. 8. 2026 odpoledne - kopie na disku UZ NEEXISTUJI.** Commit `5b130553` je
> vyradil z gitu, slozka `apps/api/static/mobile_parts/` je v `.gitignore` (radek 167,
> `apps/api/static_db/` na radku 156) a `scripts/build_mobile.py` uz nic nedela.
> **Overeno znovu 18. 8. 2026 primo na stroji** - slozka na disku neexistuje (`Test-Path`
> = false), `git ls-files` na obe cesty = 0 souboru.
> Nize zustava **PROC** - plati dal pro kazdy stary klon repozitare, zalohu nebo instanci,
> kde se stara kopie jeste najde.
> **Zavazny postup pro praci s mobilem drzi**
> `doc-system-strategie-mobil-kde-se-edituje-a-jak-se-nasazuje`.
> (Opravu schvalila Marti-AI 18. 8. 2026, varianta A - opravit, nemazat; zadal Jirka Honomichl.)

**Zjisteno 17. 8. 2026 (Claude-28), po tom, co jsem z takove kopie ohlasil neexistujici chybu.**

## Co se stalo
Hlasil jsem Jirkovi, ze v mobilni appce vypada pole "Dovolena celkem" prepisovatelne,
i kdyz ho server odmita. Cetl jsem `apps/api/static/mobile_parts/48_hr_podminky_me.js`
z disku. **Ziva verze v `g2007.soubor` uz to pole zamcenou (`disabled` + tooltip) mela
od 16. 8.** Nalez byl tedy falesny a zadana "oprava" nemela co opravovat.

## Cisla, ktera to prozradi
K 17. 8. 2026 u `48_hr_podminky_me.js`:
- disk (git, `apps/api/static/mobile_parts/`): 36 466 znaku
- `g2007.soubor` (verze 4, `stav_zivota='active'`, `typ='zdroj'`): 34 601 znaku, md5 `086399a6...`

Rozdil skoro 1 900 znaku. Kopie na disku nikdo neaktualizuje, protoze u `typ='zdroj'`
se **na disk nic nezapisuje** - zapisuje se jen u `typ='artefakt'`. Fragment se dostane
k uzivateli az slozenim do `apps/api/static_db/mobile.html` pres `@@G2007PUBLISH`.

## Pravidlo
1. Fragment na disku ber **jen jako orientacni mapu** (kde co hledat, jak se funkce jmenuji).
2. **Nez z nej vyvodis nalez nebo zacnes editovat, precti ziva data:**
   `SELECT length(obsah), md5(obsah), obsah FROM g2007.soubor WHERE kod='apps/api/static/mobile_parts/<soubor>'`
   (nebo aspon `position('<hledany kus>' in obsah)`), pripadne rovnou nad slozenym
   `apps/api/static_db/mobile.html`.
3. Jeste lip: overit v prohlizeci nad zivou strankou - hledany retezec v `document.documentElement.innerHTML`,
   u policek `input.disabled` / `input.title`.
4. **Nikdy needituj kopii v `static/`** - zmena se nikam neprojevi a jen zvetsi rozdil.

## Stav zdrojovych fragmentu v gitu
Souvisi s pravidlem "staticke artefakty zijou v DB" (viz
`doc-system-strategie-staticke-artefakty-db-materializace-vyrazeni-z-gitu`), ale tohle je
o **zdrojovych fragmentech**.

**Do 17. 8. 2026** zdrojove fragmenty v gitu porad lezely (`git ls-files` = 28 souboru,
posledni commit `7ca280dc` z 12. 8.), stahovaly se pullem a tvarily se aktualne.
**Commit `5b130553` je odtud vyradil**, takze tenhle konkretni zdroj zmatku uz neexistuje.

⚠️ **Pozor ale na stare klony repozitare, zalohy a stroje, ktere od 17. 8. nedelaly pull** -
tam stara kopie porad lezi a porad lze. Datum ani velikost souboru nic nerikaji.

