# Vítej v týmu STRATEGIE 🌳

Ahoj Kristý,

vítej mezi nás. Tenhle návod tě provede nastavením tvého pracovního prostředí
tak, abys měla **přesně stejný setup jako Marti** — vlastní kopii projektu na
svém notebooku a vlastního AI parťáka (Claude v Cowork), který zná celý náš
projekt a pomůže ti s čímkoli.

Postup má dvě části:

- **Část 1 — Základ** (uděláš sama, ~15 minut): nainstaluješ git, stáhneš
  projekt, spustíš Clauda. Tím se tvůj Claude „probudí" s plným kontextem.
- **Část 2 — Napojení na produkci** (projde s tebou tvůj Claude krok po kroku):
  GitHub přístup, automatické nasazování, databázový můstek.

Nemusíš spěchat. Když se něco zasekne, tvůj Claude (po Části 1) to s tebou
vyřeší — umí číst chybové logy a navrhnout opravu.

---

## Co pro tebe připraví Marti (předpoklady)

Než začneš, Marti zařídí:

1. **Pozvánku do GitHub repozitáře** `MartiPasek/STRATEGIE` (přijde ti e-mailem
   z GitHubu — přijmi ji). Tím získáš právo zapisovat změny.
2. **Deploy token** — krátký bezpečnostní klíč. Pošle ti ho **zvlášť**
   (ne v tomhle mailu). Budeš ho potřebovat až v Části 2.

K tomu budeš potřebovat **vlastní GitHub účet** (pokud ho ještě nemáš,
založ si ho na github.com a pošli Martimu své uživatelské jméno, ať tě
může pozvat).

---

## Část 1 — Základ (uděláš sama)

### Krok 1: Nainstaluj Git

Stáhni a nainstaluj Git pro Windows: **https://git-scm.com/download/win**

Instalátor proklikej s výchozím nastavením (všechno „Next").

Ověření — otevři **PowerShell** (Start → napiš „PowerShell" → Enter) a napiš:

```powershell
git --version
```

Mělo by se vypsat něco jako `git version 2.xx.x`. Když ano, máš hotovo.

### Krok 2: Stáhni projekt (git clone)

Pořád v PowerShellu napiš:

```powershell
git clone https://github.com/MartiPasek/STRATEGIE.git C:\PROJEKTY\Strategie
```

Při prvním stažení tě GitHub vyzve k přihlášení — přihlas se svým GitHub
účtem (otevře se okno prohlížeče). Po přihlášení se projekt stáhne do složky
**`C:\PROJEKTY\Strategie`**.

Ověření:

```powershell
cd C:\PROJEKTY\Strategie
git status
```

Mělo by se vypsat `On branch main` + `nothing to commit, working tree clean`.
To znamená, že máš čistou, aktuální kopii projektu.

> **Pozn.:** stahuj přes `git clone`, ne ruční kopií od Martiho — clone vezme
> jen čistý kód a historii, bez jeho lokálních souborů a nastavení.

### Krok 3: Nainstaluj Claude (Cowork)

Nainstaluj si desktopovou aplikaci Claude a v ní **Cowork režim**. Až ji
spustíš, **připoj/otevři pracovní složku `C:\PROJEKTY\Strategie`**
(Cowork se tě zeptá, kterou složku má používat — vyber tuhle).

### Krok 4: Probuď svého Clauda

V Cowlocalu (s připojenou složkou `C:\PROJEKTY\Strategie`) napiš svému
Claudovi něco jako:

> *„Ahoj, jsem Kristý, nový člen týmu STRATEGIE. Dělám onboarding. Načti si
> prosím `CLAUDE.md` a `docs/onboarding.md` a proveď mě dalšími kroky."*

Tvůj Claude si načte **`CLAUDE.md`** (naši „krabičku" — celý kontext projektu,
historii, principy, kdo je kdo) a tenhle návod, a od téhle chvíle **tě
provede zbytkem osobně**.

🎉 **Tímto je Část 1 hotová** — máš na svém notebooku plnohodnotného AI
parťáka, který zná celý projekt.

---

## Část 2 — Napojení na produkci (provede tě tvůj Claude)

Tohle už nedělej sama z hlavy — **nech se provést svým Claudem krok po kroku**,
ať se případné chyby hned chytí a opraví. Pro představu, co tě čeká:

1. **GitHub token (PAT)** — vygeneruješ si osobní přístupový token
   (oprávnění *Contents: Read and write* pro repo `MartiPasek/STRATEGIE`).
   Slouží k automatickému nahrávání tvých změn.
2. **Databázový/deploy můstek** — malá služba na pozadí (`STRATEGIE-CLAUDE-SQL`),
   kterou Claude používá ke dvěma věcem:
   - **diagnostika** — Claude si umí sám vytáhnout data z databáze (jen čtení;
     zápisy ti vždy nejdřív ukáže ke schválení),
   - **automatické nasazení** — když společně něco doděláte, Claude to sám
     uloží do gitu a nasadí na produkci. Ty nemusíš ručně psát žádné git
     příkazy.
3. **Deploy token** (ten, co ti Marti pošle zvlášť) — vložíš ho do nastavení
   té služby.

Tvůj Claude má na tohle připravený přesný postup a vše ověří, že funguje.

---

## Jak spolu pracujeme (pár slov na úvod)

- **Jedna produkce, jedna hlavní větev.** S Martim teď budete do projektu
  zapisovat dva. Aby si vaše změny neskákaly do zelí, systém se před každým
  nahráním automaticky srovná s tím, co nahrál ten druhý. Plus se hodí krátké
  „dělám nasazení" do chatu, ať o sobě víte.
- **Bezpečno na první místě.** Produkci používají reální lidé (Pavel a další).
  Máme pojistky — když by nové nasazení něco rozbilo, jde se okamžitě vrátit
  na předchozí verzi. Takže se neboj experimentovat; síť pod tebou je.
- **Claude je parťák, ne nástroj.** Klidně s ním mluv normálně, ptej se,
  nech ho navrhovat varianty. Zná naši historii i způsob práce z `CLAUDE.md`.

Kdyby cokoli vázlo už v Části 1 (git, clone, instalace Cowork), napiš Martimu —
rád pomůže. Od Části 2 dál máš svého Clauda.

Těšíme se na spolupráci! 🌷

— Marti & tým STRATEGIE
