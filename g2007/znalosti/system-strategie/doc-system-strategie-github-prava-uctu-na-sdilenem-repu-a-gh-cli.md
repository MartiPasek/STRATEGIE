# Kdo smi zapisovat do MartiPasek/STRATEGIE - a proc gh CLI se slucovanim PR nepomuze (24.8.2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Prava uctu na sdilenem repu a k cemu je (a neni) gh CLI

Zapsal Claude-28 na rozhodnuti **Jirky Honomichla**, **24.8.2026**. Vsechna cisla nize jsou
zmerena ten den, ne prevzata. Doplnuje `doc-system-strategie-nasazeni-obsahu-pr-pres-most-kdyz-nejde-sloucit`,
ktera popisuje, **jak** se obsah PR dostane do `main`, kdyz to tlacitkem nejde. Tahle znalost rika,
**proc to nejde a kdy to prestat zkouset**.

## Zmerene prava (24.8.2026)

| ucet | kde se pouziva | prava na `MartiPasek/STRATEGIE` |
|---|---|---|
| `eurosoft-strategie` | Jirkuv Windows stroj (gh CLI) | `pull=true`, **`push=false`**, `admin=false` |
| `GHubGeorge` | Jirkuv Mac | jen `pull` (viz kapitola 8 znalosti o iOS buildu) |
| `MartiPasek` | Marti | spravce |

Zjisteni: `gh api repos/MartiPasek/STRATEGIE --jq '.permissions'`.

**Dusledek:** ani jeden ucet, ktery ma tym bezne po ruce, **nesmi PR spojit s hlavni vetvi**.
GitHub proto u PR tlacitko vubec nezobrazi - ukaze jen zelene "no conflicts with base branch".
**Neni to konflikt obsahu, je to otazka prav** (rozliseni: `mergeable_state` je `clean`).

## Co z toho plyne prakticky

- **Neinstaluj a neprihlasuj gh v nadeji, ze pak PR spojis.** Nespojis. Prava nedava nastroj
  ani token, ale ucet. 24.8.2026 se tahle cesta prosla cela az do konce a skoncila na `push=false`.
- **Funkcni cesta je most** - postup a **tri povinne kontroly** ma
  `doc-system-strategie-nasazeni-obsahu-pr-pres-most-kdyz-nejde-sloucit`.
  Precedens: PR 2, 4, 5 a nove i **PR 7** (obsah v `main` jako commit `24e85a73`, iOS 1.85).
- **PR pak zavira a vetev na forku maze jeho autor.** Pod ulozenym pristupem, ktery patri
  konkretnimu cloveku (Marti), se **cizi PR nezaviraji ani nekomentuji** - to uz je vystupovani
  za nej. Push zmeny je v poradku, autorstvi commitu se nastavuje zvlast.
- Kdyz je opravdu potreba spojeni na GitHubu, **musi to udelat Marti** (jediny se spravcovskym pravem).

## gh CLI na Jirkove Windows stroji (stav 24.8.2026)

Nainstalovano pres `winget install --id GitHub.cli`, verze **2.98.0**, cesta
`C:\Program Files\GitHub CLI\gh.exe` (**neni v PATH** - volej plnou cestou).
Prihlasen ucet `eurosoft-strategie`, token v keyring, rozsahy `gist`, `read:org`, `repo`.

**K cemu JE dobre** (cteni, bez sahani na klice v nastaveni projektu): `gh api repos/.../pulls/7`,
`.../pulls/7/files` (rozsah zmen), `gh api "repos/<fork>/STRATEGIE/contents/<cesta>?ref=<sha>"`
pro stazeni souboru **ze spicky PR** a `gh api repos/.../compare/main...<fork>:<repo>:<vetev>`
pro spolecny zaklad. Obsah ber v **base64** a zapisuj binarne - `Out-File -Encoding utf8`
ve Windows PowerShellu prida **BOM** a soubor uz neni bajtove shodny s predlohou.

**K cemu NENI:** spojeni PR (viz vyse).

## Gotcha: prihlaseni gh spustene pres `!` bezi na pozadi a kod NENI videt

`gh auth login` je interaktivni. Kdyz ho clovek spusti z Claude Code pres `!`, prikaz se po
dvou minutach presune **na pozadi** a jednorazovy kod se vypise **jen do souboru s vystupem ulohy**
(`...\tasks\<id>.output`), takze na obrazovce **neni nic** a vypada to, ze se nic nedeje.
**Reseni:** precist kod z toho souboru, otevrit `https://github.com/login/device`, kod vlozit,
potvrdit opravneni. Prihlaseni pak dobehne s navratovym kodem 0 a `gh auth status` uz ukazuje ucet.
Kod plati radove minuty; po vyprseni se prihlaseni spousti znovu.

