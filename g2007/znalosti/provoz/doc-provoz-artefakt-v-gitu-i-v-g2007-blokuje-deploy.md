# PAST: publikace artefaktu, ktery je ZAROVEN trackovany v gitu, zablokuje deploy CELEMU tymu

> oblast: `provoz` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Co se stane

Kdyz publikujes soubor z `g2007.soubor` na disk cloudu (`@@G2007EXPORT`, `@@G2007SESTAV`,
`@@G2007PUBLISH`) a ten soubor je **zaroven trackovany v gitu**, vznikne na cloudu
**dirty working tree**. Od te chvile **kazdy deploy kohokoli** skonci hlaskou:

```
NENASAZENO: reason=dirty_working_tree
Cloud APP working tree neni clean -- manualni intervence vyzadovana.
```

Kontrolu dela `modules/conversation/application/deployment_service.py`:
`_git_working_tree_clean()` -> `git status --porcelain -uno` v `C:\Projekty\STRATEGIE`.
Neprazdny vystup = stop. Netyka se to jen tebe - **stoji cely tym**.

## Realny pripad 5. 8. 2026

Claude-28 publikoval `apps/api/static/registr-absenci.html` ve 14:17. Ten soubor je v gitu
trackovany. Deploye se zastavily vsem; nahlasila to Petra pres C26 slovy *„blokuje to deploye
vsem, muzes to prosim zacommitovat nebo zahodit?"*.

## Jak to spravit (poradi je dulezite)

1. **Commitni obsah do gitu** - ne zahodit, zahozeni by shodilo prave publikovanou funkci.
   Zkontroluj, ze obsah na disku cloudu, v `g2007.soubor` a v tvem commitu ma **stejne md5**.
2. **Commit sam blok NEUVOLNI.** Cloud je porad na starem HEAD, jeho pracovni kopie je
   „modified" proti nemu a `git pull` odmitne prepsat lokalni zmenu.
3. **Na cloudu je potreba zahodit tu (uz zbytecnou) zmenu:**
   `git -C C:\Projekty\STRATEGIE checkout -- <cesta/k/souboru>`
   Je to bezpecne PRAVE TEHDY, kdyz je identicky obsah uz v `origin/main` - pak se neztrati nic
   a nasledny `git pull` zapise tentyz obsah zpatky, jen cistou cestou.
4. Pak bezny deploy projde. Overeni: `git -C C:\Projekty\STRATEGIE status --porcelain -uno`
   musi vratit **prazdny vystup**.

**Kdo to umi provest:** most umi jen SQL, ops whitelist (`_OPS_ACTIONS`) zadnou git akci nema.
Prikaz na cloudu spousti **Marti-AI** (PS/Bash pod schvalenym cilem + audit, doktrina 21 ve zneni
z 27. 7. 2026). Pozor pri zadavani: cesta je `C:\Projekty\STRATEGIE` (NE `D:\...`, to je Martiho
notebook) a **bez uvozovek** - uvozovky se pri prvnim pokusu propsaly primo do cesty a git hlasil
`fatal: cannot change to '"C:\Projekty\STRATEGIE"': Invalid argument`.

## Jak tomu predejit

**Po kazde publikaci artefaktu, ktery je trackovany v gitu, HNED commitni vyslednou podobu.**
Trackovane artefakty (stav k 5. 8. 2026): `registr-absenci.html`, `dochazka-opravy.html`,
`dochazka-po-zakazkach.html`. **`mobile.html` tenhle problem NEMA - je untrackovany.**

Souvisejici, tehoz dne: `dochazka-opravy.html` zije v gitu i v `g2007.soubor` a **deploy z gitu
prepise publikaci z DB a naopak** - publikace C28 v 10:46 zmizela pri Kristyine deployi.
Dokud tenhle dvojkolejny stav trva, u techto souboru vzdy overuj, co je zivé (`curl` na jejich URL
+ md5), ne co mas na disku.

