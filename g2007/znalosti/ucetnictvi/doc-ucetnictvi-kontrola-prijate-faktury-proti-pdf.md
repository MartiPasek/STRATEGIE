# Kontrola přijaté faktury proti PDF — kde je postup a co se porovnává

> oblast: `ucetnictvi` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)


Postup kontroly přijaté faktury proti přiloženému PDF **nežije v G2007** — celý je v souboru
`docs/team/Peta26_pokyny.md`, sekce „🧾 KONTROLA PŘIJATÉ FAKTURY PROTI PDF" (Peťa, od 21. 8. 2026,
průběžně doplňovaná). Tenhle záznam je **jen rozcestník**, ať ho příští instance nehledá znovu —
a hlavně ať si pravidla nepíše podruhé jinam. Dvě verze pravdy jsou horší než jedna.

**Co se porovnává** (Peťa zadává „zkontroluj fakturu poř. číslo NNNN s tím, co je v PDF"):
DUZP · splatnost · číslo účtu (u cizoměnné faktury ten účet, který je v měně faktury) ·
variabilní symbol · částky u položek · kurz · celková cena · skonto ·
odběratel = správná firma · nabídka, když je na dokladu její číslo.

**Tři pravidla, která se pletou nejčastěji:**

- **Rozhoduje celková částka k úhradě v měně faktury** — ta musí sedět na haléř, u eurové
  faktury na cent. Rozdíly **do 5 Kč** v základu i v dani se **nehlásí**; kolegyně je schovává
  do korekční řádky nebo do poštovného, aby k úhradě vyšlo přesně, a je to správně.
  (Peťa 14. 9. 2026 — *„tolerujeme to do 5 korun, hlavně aby seděla celková částka k platbě"*.)
- **Kurzu se ta tolerance NETÝKÁ.** U tuzemského dodavatele — rozhoduje **české DIČ**, ne sídlo
  firmy — se bere kurz z faktury, nebo dopočtený z korunového rozpisu. U zahraničního kurz
  k prvnímu pracovnímu dni měsíce. Rozdíl v kurzu je nález i při dopadu pár haléřů.
- **Když je všechno v pořádku, nerozepisuje se.** Jeden řádek na fakturu. Rozepisuje se jen to,
  co nesedí.

**Kde leží doklady:** cestu k PDF faktury dá `dbo.EC_Doklad_NajdiDokument(D.ID)` →
sdílená složka `FakturyP\FP<ID dokladu>`. Nabídky leží v `Poptavky_V\EVP<číslo>`; cesta k nim vede
z faktury přes navaznou objednávku (řada 800) a pole „číslo nabídky dodavatele" na vydanou
poptávku (řada 940, přehled 240).

**Gotcha, která stála čas (9. 9. 2026, faktura 2287):** dodavatele z dokladu dohledávej přes
`TabCisOrg.CisloOrg = TabDokladyZbozi.CisloOrg`, **ne přes `TabCisOrg.ID`**. Přes ID vyjde úplně
jiná firma a vypadá to jako nález „faktura je na jinou firmu". Ověřeno na 2179, 2229, 2230, 2231.

**Druhá gotcha (14. 9. 2026):** číslo v poli „číslo nabídky dodavatele" u RS Components **je**
číslo nabídky a nabídka k němu ve vydaných poptávkách existuje — nezaměňovat s objednacím číslem
RS, které na jejich faktuře vypadá podobně. Neodvozovat z jednoho případu pravidlo, podívat se.

Zapsal Claude-26 na pokyn Petry Šafránkové, 14. 9. 2026.

