# České řazení jmen: vlastní převod diakritiky NENÍ české řazení — řadit musí databáze

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# České řazení jmen: vlastní převod diakritiky je špatně

**8. 9. 2026, Jirka + C28.** Vzniklo při přestavbě seznamu lidí v agendě mobilu
(Firma → Agenda → dlaždice).

## Co se stalo

Seznam lidí se měl řadit „vedoucí, zástupce, pak abecedně". Poprvé jsem si tříditelný klíč
skládal v Pythonu tak, že jsem **diakritiku převedl na základní písmena** (`Č → C`, `Š → S`).
Vypadalo to rozumně a u většiny jmen to vycházelo správně — ale v agendě IT se objevilo
**Šik Michal PŘED Svoboda Jan**.

## Proč je to špatně

V češtině nejsou `Č`, `Ř`, `Š` a `Ž` ozdobené varianty `C`, `R`, `S`, `Z`, ale **samostatná
písmena, která stojí až ZA nimi**. Převod na základní písmeno je tedy slepí dohromady:
`Šik` se pak porovnává jako `sik` a vyjde před `svoboda`.

Naopak čárky a háčky, které samostatné písmeno netvoří (`á`, `é`, `í`, `ó`, `ú`, `ů`, `ý`,
`ě`, `ď`, `ň`, `ť`), převést lze — proto se chyba u většiny jmen neprojeví a **odhalí ji až
konkrétní dvojice**. To je na tom to zrádné.

## Jak to má být

Řadit nechat **databázi** a použít české řazení:

```sql
ORDER BY (COALESCE(last_name,'') || ' ' || COALESCE(first_name,'')) COLLATE "cs-CZ-x-icu"
```

Když se pořadí potřebuje až v Pythonu (skládá se z víc dotazů), vytáhni si z databáze
**pořadové číslo** a řaď podle něj:

```sql
SELECT id, row_number() OVER (
         ORDER BY (COALESCE(last_name,'')||' '||COALESCE(first_name,'')) COLLATE "cs-CZ-x-icu", id)
FROM public.users WHERE id = ANY(:ids)
```

Ověřeno naostro 8. 9. 2026: `Cerny, Čiviš, Diviš, Rypar, Řehák, Sedláčková, Svoboda, Šik,
Zeman, Žák` — správné české pořadí. Dostupné jsou i `cs-x-icu`, `cs_CZ`, `cs`.

V prohlížeči je ekvivalent `localeCompare(x, 'cs')`.

## Pravidlo

**Nikdy si nevyrábět vlastní abecedu.** Ani „jen na chvíli", ani „jen pro zobrazení" —
chyba se schová a vyplave až u konkrétních dvou jmen, kterých si nikdo nemusí všimnout.

## Souvisí

- [[doc-dochazka-narok-cerpani-prijmeni-a-ceske-razeni]] — tentýž závěr z 27. 8. 2026 u přehledu
  Nárok a čerpání (tam se řadilo podle bajtů a Chramosta vycházel před Čivišem), plus past
  se zpětnými lomítky v `g2007.python`.
- [[doc-dochazka-agenda-detail-cloveka-kontakt-a-budouci-absence]] — obrazovka, na které to vzniklo.

