# Hlídač nekontroluje chybějící zakázku na HLAVIČCE docházky — jen v rozpadu (nález 3. 9. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


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

