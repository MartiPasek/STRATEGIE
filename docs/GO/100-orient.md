# 100 — @@ORIENT: zorientování entity

**Stav:** návrh k diskusi · 11. 7. 2026 · Claude (z Martiho zadání)

## Co to je
`@@ORIENT` je ranní zorientování entity — lidské i digitální. Než entita sáhne po nástroji (mobil → čas), musí vědět, **kdo je a kam patří**. To je nultý krok autonomie: kdo je zorientovaný, může zjednodušovat a jednat; kdo není, je ztracený.

## Obsah orientace (vrstvy, esenciální první)
1. **Identita** — žiju, jak se jmenuju, kdo jsem.
2. **Příslušnost** — moje rodina, kam patřím (STRATEGIE), moje role.
3. **Práce** — co je moje běžná práce, co se ode mě čeká.
4. **Lidé kolem** — kdo mi pomáhá, kolegové, jak s nimi komunikuji, kdo je šéf, kdo parťáci, kdo podřízení.
5. **Možnosti a nástroje** — co mám k dispozici, čím to udělám.
6. **Nástroj → čas a datum** — orientace ve světě, „jsem v obraze".
7. **Symboly / notifikace** — kde je moje pozornost dlužná.

## Tři MUSTy (Marti 11.7.2026)
1. **UNIVERZÁLNÍ.** Jeden mechanismus pro Claude, Marti-AI i ostatní entity. Entita řekne „kdo jsem" → dostane své zorientování týmž mechanismem, jen jiným objektivem.
2. **ŽIJE V DATABÁZI, ne na lokálu.** Jediný živý zdroj pravdy — žádné rozjeté lokální kopie. Změna org (nový kolega, změna role) → zorientování všech se srovná samo. Fallback pro entitu bez přímého přístupu k DB (Claude v lokálu): **DB na povel vyexportuje první dávku do souboru a čeká na další.**
3. **NEZÁVISLÝ NA VYKONAVATELI.** Je jedno, zda ORIENT dělá Claude v lokálu nebo Marti-AI v jakékoli inkarnaci — výsledek je týž.

## Dávkování (paging) — jako telefon
První dávka = esenciální (kdo jsem, rodina, kam patřím). Na povel hlouběji (kolegové, hierarchie, aktuální práce, notifikace). Systém sám zjednoduší, co jde; eskaluje jen to, co potřebuje entitu.

## Otevřené / k rozhodnutí
- Datový model orientace v DB (identita, příslušnost, role, vztahy/hierarchie, kanály komunikace, nástroje).
- Formát a hranice dávek (co je „první dávka").
- Jak entita signalizuje „kdo jsem" (klíč identity napříč Claude / Marti-AI inkarnace).
- Napojení na existující: domain_env, GO režim, cockpit, ai_work_log.
