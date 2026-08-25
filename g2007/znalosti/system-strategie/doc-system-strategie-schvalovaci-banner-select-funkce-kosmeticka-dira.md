# Schvalovaci banner obejde SELECT volajici zapisujici funkci - ale zapis se rollbackne (overeno 25.8.2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Schvalovaci banner obejde `SELECT zapisujici_funkce()` — zapis se ale neulozi

Nahlasila **Kristyna Ksirova (pres Claude-24) 21. 8. 2026** v mailu o dochazce a rozpadu. Overil naostro **Claude-28 25. 8. 2026** na zadani Jirky Honomichla, test schvalila **Marti-AI (msg 13697)**.

## Zaver napred

**Je to kosmeticka dira, ne skutecna.** Banner opravdu nevyskoci, ale **zapis se neulozi** — transakce se vrati zpet.

## Co presne plati (prvni polovina nalezu — POTVRZENO)

Most rozhoduje o tom, jestli je dotaz cteni nebo zapis, **ciste textove podle prvniho slova**:

```
_is_read = bool(re.match(r"\s*(SELECT|WITH|EXPLAIN|SHOW)\b", _s_chk, re.I))
if not _is_read:
    ... zaklada se pending request do fw.claude_write_request (banner) ...
```
(`modules/erp/api/router.py`, obsluha `/diag-sql`.)

Druha vrstva `query_raw` (`modules/strategie_pg/application/service.py`) ma stejne textovy whitelist `SELECT/WITH/EXPLAIN/SHOW` + seznam zakazanych slov (`DELETE/UPDATE/INSERT/DROP`).

**Ani jedna z techto kontrol nevidi dovnitr volane funkce.** `SELECT nazev_funkce()` tedy projde jako neskodne cteni, i kdyz ta funkce uvnitr zapisuje, a **schvalovaci banner nevyskoci**.

## Co NEPLATI (druha polovina — VYVRACENO testem)

Zapis se **neprovede**. Ctecí cesta jde pres `query_raw` -> `get_session()`, a ta na konci dela **jen `session.close()` bez `commit()`**. Engine je zalozen `create_engine(url, ...)` **bez** `isolation_level="AUTOCOMMIT"` a `sessionmaker(bind=_engine)` je vychozi. Transakce se proto **rollbackne**.

## Jak se to overilo (naostro, ne z kodu)

1. Zalozena testovaci tabulka `fw.test_c28_20260825_banner` + funkce `fw.test_c28_20260825_zapis()`, ktera vlozi jeden radek. (Pres schvalovaci banner — ten u `CREATE` vyskocil spravne.)
2. Posláno `SELECT fw.test_c28_20260825_zapis()`. Most vratil **`STATUS: OK`**, funkce ohlasila *"funkce probehla a zapsala radek"*, **zadny banner nevyskocil**.
3. Z **nove relace** precten obsah tabulky: **0 radku**.
4. Uklizeno (tabulka i funkce zrusena).

**Izolace to nebyla** — druhy dotaz bezel az po skonceni prvniho, ve vlastni relaci. Kdyby se transakce potvrdila, radek by byl videt. Na tuhle zamenu vyslovne upozornovala Marti-AI a byla proto oddelena.

## Poctiva vyhrada — co test NEPOKRYVA

Rollback chrani jen **bezny zapis do tabulky**. Funkce s vedlejsim efektem **mimo transakci** by prosla i tak:

- `nextval()` — sekvence nejsou transakcni, posun **prezije rollback**
- volani ven (`dblink`, HTTP, zapis do souboru)
- procedura s vlastnim `COMMIT` uvnitr

Tohle **netestovano** a netvrdi se o tom nic. Kdo bude na tuhle vrstvu spolehat u neceho citliveho, ma to overit zvlast.

## Praktický dopad

- **Neni to bezpecnostni prusvih**, ktery by se musel resit hned.
- **Je to ale slepe misto v tom, na co se banner spoleha**: kontrola je textova, ne semanticka. Kdyby se ctecí cesta kdykoli v budoucnu zmenila tak, ze commituje (napr. kvuli necemu jinemu), dira se stane skutecnou **a nikde to nezahlasi chybu**.
- Kristy to popsala presne: *"U nas to bylo neskodne, protoze volana funkce byla zamcena, ale je to dira v tom, na co se banner spoleha."*

Souvisi: [[doc-system-strategie-bridge-most-lanes-ops]]

