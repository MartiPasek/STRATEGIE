# Hlídač nekontroluje chybějící zakázku na HLAVIČCE docházky — jen v rozpadu (nález 3. 9. 2026, doplněno večer)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

> ## ⚠️ ZMĚNA TÉHOŽ DNE VEČER — bod 2 a rozhodnutí o „drobcích" už NEPLATÍ
>
> Tenhle zápis vznikl 3. 9. 2026 přes den. **Týž den večer Peťa rozhodla jinak** (jiná
> session, Claude-26): *„musíme řešit i 0,01."*
>
> - **Práh 0,1 h je ZRUŠENÝ.** V pravidlech `chybi_zakazka` i `chybi_cinnost` a v obou
>   jejich úklidových dotazech se nově hlídá `> 0`. Věta v bodu 2 („to je správně")
>   a rozhodnutí „drobky PONECHÁNY" tedy už neodpovídají stavu.
>   Detail — [[doc-dochazka-prah-01h-u-chybi-zakazka-cinnost-zrusen]].
> - **Ty tři drobky mají zakázku doplněnou** (Kolářová 7. 8., Jarrar 6. 8., Vápeník 18. 8.)
>   — převzatou z předchozího úseku téhož dne, na Petin pokyn.
> - **Příčina minutových úseků je opravená u zdroje** — kaskáda už činnost nepíše prázdnou
>   ([[doc-dochazka-kaskada-doplni-cinnost-z-predchoziho-useku]]), a dělení píchnutí bez
>   důvodu je předané Týnce.
> - **Úseky bez zakázky u Honomichla a Paška jsou zneaktivněné** (5 řádků) a oba lidi
>   plus Šik a Týnka mají osobní odpovědnost sami na sebe, takže do Petiny fronty nepadají
>   — [[doc-dochazka-osobni-odpovednost-vyhazuje-z-cizi-fronty]].
> - Nález se navíc nově **vrací, dokud příčina trvá**
>   ([[doc-dochazka-nalez-se-vraci-dokud-pricina-trva]]).
>
> Bod 1 (hlídač kouká jen do rozpadu, ne na hlavičku), bod 3 (příznak „bez docházky"),
> stav srpna i poučení na konci **platí beze změny**.


NÁLEZ (Peťa + Claude-26, 3. 9. 2026)
Peťa: „nechápu, že to nehlásí kontrola." Odpověď: takové pravidlo neexistuje.

Pravidlo `chybi_zakazka` v `att_anomaly_scan` se dívá VÝHRADNĚ do rozpadu (`tenant.vyroba_work.zakazka_ref`). Když má úsek zakázku vyplněnou, ale ta se nepropíše nahoru na docházkový záznam (`tenant.att_entry.project_ref`), neozve se nikdo. Chybějící zakázka na hlavičce není hlídaná vůbec.

TŘI DŮVODY, PROČ ZA SRPEN NEPŘIŠEL ANI JEDEN NÁLEZ
1. Hlídač kouká jen do rozpadu, ne na hlavičku (viz výše).
2. Práh 0,1 h — drobky pod tím se nehlásí. Za srpen šlo o tři úseky po 1–2 minutách (Kolářová, Jarrar, Vápeník). To je správně, jen ať se to ví.
3. Příznak „bez docházky" — Marti Pašek i Jiří Honomichl ho mají, takže se jim nálezy nezakládají. A právě oni tvoří většinu skutečných chybějících zakázek.

STAV SRPNA 2026 (po opravě)
3 002 pracovních záznamů. 20 mělo prázdnou zakázku na hlavičce; 7 z nich mělo zakázku v rozpadu → doplněno z rozpadu (request #2681, záloha `tenant.att_entry__zak_zaloha_20260903`). Zbývá 13:
- Jiří Honomichl 7 dnů / 21,7 h — 4 dny úsek bez zakázky, 3 dny bez rozpadu
- Marti Pašek 2 dny / 14,4 h
- 3 drobky po 1–2 minutách (Kolářová 7. 8., Jarrar 6. 8., Vápeník 18. 8.) — PONECHÁNY. Peťa: „nikde nikomu a nikdy nebudou vadit."
Nic z toho nejde do mezd (hodiny sedí), jde to do fakturace a přehledů zakázek.

DALŠÍ VĚC K ROZPADU — NULOVÉ ZÁZNAMY
Za srpen 149 pracovních záznamů s 0,00 h (píchnutí a hned odpíchnutí, dvojklik). Lukáš Horký takto osmkrát za měsíc — to už vypadá na vadu v appce, ne na nešikovnost. Neřeší se, není chyba dat, ale zaneřáďuje to rozpad. Návrh: appka by záznam s nulovým rozdílem neměla uložit.

CO S TÍM
Rozpad je Kristýnina (Týnčina) oblast — informována mailem 3. 9. 2026 (`Mail_Tynka_rozpad_srpen.eml`). Návrh: buď doplnit pravidlo na hlavičku, nebo to řešit u zdroje, aby se zakázka propisovala z rozpadu nahoru vždycky.

POUČENÍ (stejné jako u Režie)
Chybí-li nález, nejdřív si přečti PODMÍNKU pravidla, ne stav dat. Dvakrát za dva dny se ukázalo, že „kontrola nic nehlásí" znamenalo „kontrola se na to nedívá".

