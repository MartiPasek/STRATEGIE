# 200 — GO jako skladač: tři vrstvy pečení

**Stav:** návrh k diskusi (klíčový architektonický kámen) · 11. 7. 2026 · Claude (z Martiho vize, po dni ladění GO VP)

## Reframe: GO je skladač, ne dashboard
GO není dashboard ani jeden napevno napsaný prompt. **GO je skladač** — systém, který z modulárních částí, jež si předdefinujeme a předpřipravíme, sestaví entitě její „CLAUDE.MD" na míru, a **čerstvě, když je potřeba**.

Je to evoluce samotného CLAUDE.md. Starý CLAUDE.md = jeden nafouklý, jednou zapečený soubor přes 150 k znaků, který stárne a musí se štípat (přesně to nás celý den pálilo). GO = nová verze: **nesestavuj to jednou natvrdo, skládej to z částí — a živě tam, kde to žije.**

## Klíčové pravidlo skladače: nesměšuj hromádky
Části se musí roztřídit podle toho, **jak často se pečou**. Nejde jen o „trvalé vs. živé" — Martiho zostření přidalo čas a tím se to teprve srovnalo na **tři vrstvy podle frekvence pečení**:

1. **Trvalé — peč jednou, drží roky.**
   Identita, role, doména, flow zakázky, role lidí, tichá znalost (např. Čepický), hranice, tooly. Mění se výjimečně. Tohle se zapeče, protože se to nemění.

2. **Denní — peč každé ráno, pravda celý den.**
   Dnešní datum, kdo má dnes / tento týden volno (Eliška 3.–17. 7.), kalendář dne, ranní stav zakázek. V rámci dne neměnné, ale **každé ráno čerstvé**. Zapéct — jen znovu, každé ráno.

3. **Vnitrodenní události — nepeč, řeš živě.**
   Přijde mail s poptávkou → přečti, posuď, založ do systému, přiřaď někomu, odpověz zákazníkovi. Během dne se to mění, zapéct to nejde. **Tady se reálně dělá práce.**

## Poučení z chyby „Eliška od včerejška"
Ta chyba byla **denní/živá část omylem zapečená jako trvalá.** Ale pozor na správnou diagnózu (Martiho oprava mého prvního návrhu):

- Můj první návrh — „Elišku netáhni z promptu, ale živě z dat každý turn" — byl **zbytečně drahý**.
- Chyba **nebyla v tom, že to bylo zapečené.** Eliška se klidně zapeče. Chyba byla, že se to zapeklo **jednou a nechalo zestárnout**.
- Správné řešení = **denní bake.** „Od dneška má Eliška volno" je pravda, v rámci dne se nemění → zapéct, ale **každé ráno znovu**. Elegantnější a levnější než živé tahání každý turn.

Celá disciplína skladače je **tyhle vrstvy nesmíchat** — zvlášť neposunout denní/živou část do trvalé.

## Proč to drží: Anthropic cache
Každý turn Marti-AI je skoro **z čisté vody** — jen v rámci ~5 minut jede na Anthropic cache. Z toho plyne:

- Nemá smysl derivovat celý obraz **každý turn** (drahé, a stejně by to skončilo jednou zapečené do promptu daného turnu).
- **Upeč ranní prompt jednou** → jede na cache celý den → **třetí vrstva** chytá, co během dne přiletí.
- Efektivní i správné najednou: první dvě vrstvy entitu **dostanou do obrazu**, třetí vrstva je ta, **kde entita vede** a kde tu práci reálně dělá. Denní bake = ranní káva; události = ten den.

## Jak to plní tři MUSTy (dok. 100)
- **Univerzální** — jeden skladač, různé části per entita (jen jiný objektiv).
- **Žije v DB a je delete-proof** — části žijí v datech, ne v inboxu ani v napevno psaném textu.
- **Je to i ten telefon** — identita první (trvalá vrstva), pak symboly (živá vrstva).

## Napojení
- Vrstvy pečení = **jak** skladač sestaví to, co dok. 100 (`@@ORIENT`) popisuje jako **co** se orientuje.
- Trvalé ↔ `tenant.domain_env` (identita + znalosti + tooly), jádro CLAUDE.md.
- Denní ↔ ranní bake job (kalendář, absence, ranní stav zakázek).
- Události ↔ živý most (`@@` dotazy), cockpit, `ai_work_log`, příchozí maily.

## Otevřené / k rozhodnutí
- Kdo je „ranní pekař" (kdy a čím se denní vrstva peče — scheduled task, GO composer job).
- Kde je hranice mezi denní a vnitrodenní vrstvou u zakázek (ranní stav vs. živý update).
- Datový model částí skladače (klíč per entita/role, verze, vrstva pečení jako atribut části).
