# Osobní mzdový kalendář v Heliosu — proč se změna úvazku neprojeví ve výpočtu mzdy

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Osobní mzdový kalendář — proč se změna úvazku „nechytne"

**Ověřeno 6. 8. 2026** (Peťa + Claude-26) na reálném případu, dohledáno v dokumentaci
Helios Inuvio na podnět Martiho Paška.

## Příznak

Zaměstnanci se změní úvazek (např. z 8 h na 7 h denně). Na mzdové kartě v Heliosu je
**všechno správně** — kalendář, denní i týdenní úvazek, základní mzda. Mzda se přegeneruje
a Helios přesto počítá **starý fond pracovní doby**. Základní plat vyjde vyšší, než má být,
protože se od většího fondu odečte stejná absence a zbyde poměrově víc odpracované doby.

## Příčina

Helios drží u každého zaměstnance **osobní mzdový kalendář** = kopii hlavního kalendáře,
která vznikne při prvním přiřazení. Z dokumentace Helios Inuvio (Mzdový kalendář - Mzdy CZ)

> „Pokud provedete úpravu v hlavním mzdovém kalendáři, změny se do osobních kalendářů
> nepromítnou automaticky, projeví se pouze u zaměstnanců, kterým kalendář NOVĚ PŘIŘADÍTE
> a vygeneruje se jim ten nový osobní kalendář."

> „Při synchronizaci probíhá kontrola, která zjišťuje, v kterých měsících existuje pro vybraného
> zaměstnance vypočtená mzda nebo zadané předzpracování. Pokud existuje mzda nebo předzpracování,
> tak pro takový měsíc synchronizace NEPROBÍHÁ."

Proto ani „Synchronizuj" na hlavním kalendáři nepomůže, dokud existuje spočítaná mzda.

## Řešení (ověřený postup)

1. **Smazat zaměstnanci vypočtenou mzdu.** Dokud existuje, Helios úpravy mzdových údajů
   nepustí — pole jsou šedá/needitovatelná.
2. Na mzdové kartě opravit kalendář a úvazek (Mzdové údaje → 2 Zařazení → Tarif a úvazek).
3. Zkontrolovat **Mzdy → Mzdové údaje → Osobní mzdový kalendář** — zaměstnanec tam musí mít
   AKTIVNÍ řádek s novým kalendářem a správným denním/týdenním úvazkem. Starší řádky
   (neaktivní, z předchozích let/úvazků) tam zůstávají jako historie — **NEMAZAT je.**
4. **Vygenerovat mzdu znovu.**

Kdyby aktivní osobní kalendář chyběl, jde založit přes Konstanty a číselníky → Mzdový kalendář
→ karta Akce → **Generuj osobní kalendáře** (vytvoří ho tomu, kdo ho nemá, existující nechá být).

## Jak to poznat ve výplatnici

U složky základní mzdy nesedí HODINY. Spočítej `fond − absence`; když vyjde jiné číslo než je
ve výplatnici, má zaměstnanec starý osobní kalendář. Dovolená se tím nemění (počítá se z průměru),
mění se základní mzda a poměrově krácené složky.

## Co NEDĚLAT

**Neposouvat kvůli tomu aktuální mzdové období** ve starém (opouštěném) Heliosu jen proto,
že jsou tam pole šedá. Posun období = nevratná uzávěrka předchozího měsíce a s tímhle problémem
nesouvisí. Šedá pole v needitovatelném období jsou důsledek toho, že se tam mzdy už nezpracovávají.

## Poznámka k naší docházce

Docházkový automat ve STRATEGII doplňuje do fondu **správně podle úvazku ve STRATEGII** —
při ověření seděl součet odpracováno + doplněno do fondu + absence přesně na správný fond.
Chyba byla výhradně na straně Heliosu. Takže rozejde-li se fond, hledej nejdřív osobní
kalendář v Heliosu, ne chybu v naší docházce.

