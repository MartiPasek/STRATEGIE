# MCP eurosoft_strategie_query_raw vraci JEN PRVNI result set — proc nefunguje cteni OUTPUT po EXEC

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# MCP vraci jen PRVNI result set (overeno 20. 8. 2026)

Claude-24 (Kristy). Stalo nas to dva dny testovani podkladu OSVC, at to nikoho nestoji znovu.

## Zmereno, ne odhadnuto

Pres SQL most (`db=mssql`, tedy tataz cesta jako `eurosoft_strategie_query_raw`) poslano:

```sql
SELECT 111 AS hodnota, 'PRVNI vysledek' AS popis;
SELECT 222 AS hodnota, 'DRUHY vysledek' AS popis;
```

Vratil se **jen prvni** (111). Druhy result set se zahodi.

## Dusledek

Bezny vzor „zavolej proceduru s OUTPUT parametrem a precti si ho zaverecnym SELECTem"
**nefunguje spolehlive**:

```sql
DECLARE @ident int;
EXEC EC_PrijemZbozi_InsertPolozky @IDDoklad=…, @Ident=@ident OUTPUT, …;
SELECT @ident AS ident;     -- ⚠ dorazi jen kdyz procedura sama nic nevybrala
```

`EC_PrijemZbozi_InsertPolozky` ma pres 500 radku a uvnitr vola dalsi procedury
(`EC_DotahniCenuZbozi`, `hp_ObehZbozi_PrepocetPolozek`, `EC_PrijemZbozi_PrepocitejDoklad`…),
z nichz nektera vrati vlastni result set. Nas `SELECT @ident` je pak druhy v poradi → ztraci se.
**Zapis pritom probehne spravne** — polozka i platba vzniknou. Jen si o tom neprecteme potvrzeni,
takze skript to vyhodnoti jako selhani a prerusi se uprostred (u nas: hlaska
„Polozka pro VR10609 se nezalozila (bez ID)", pritom byla v objednavce).

**Pozor, „funguje to" nic nedokazuje.** `EC_Ukolnik_ZalozAOdesliUkol` zadny vlastni vyber
nedela, takze u ni cteni OUTPUT fungovalo — ale je to nahoda konkretni procedury,
ne vlastnost rozhrani. Po prepnuti na `_Loc` (konci volanim `EC_Ukolnik_AktualizujKomplet`)
uz by to spolehlive nebylo.

## Reseni: ID zjistovat samostatnym dotazem

Vzor „max ID pred a po":

```python
pre  = _ec("SELECT ISNULL(MAX(ID),0) AS maxid FROM TabPohybyZbozi WHERE IDDoklad=%d" % id_obj)
_ec("SET NOCOUNT ON; DECLARE @ident int, …; EXEC …; UPDATE …; INSERT …;")   # bez SELECTu
post = _ec("SELECT TOP 1 ID AS id FROM TabPohybyZbozi WHERE IDDoklad=%d AND ID > %d "
           "AND CisloZakazky = %s ORDER BY ID DESC" % (id_obj, maxid, zakazka))
```

Uvnitr davky `@ident` funguje normalne (da se pouzit v navazujicich UPDATE/INSERT) —
problem je vylucne v PRENOSU ven.

## Kde je to opravene (20. 8. 2026)

- `podklad_osvc_helios_obj` (v4+) — ID polozky objednavky pres MAX(ID) v dokladu
- `podklad_ukol_send` (v7+) — ID ukolu pres MAX(ID) v `EC_Ukoly` daneho zadavatele;
  notifikace (`EC_Ukolnik_OdesliUkol`) se vola az potom, samostatne

Kontrola, jestli nekde nezustal rizikovy vzor:

```sql
SELECT kod FROM g2007.python WHERE zdroj ILIKE '%OUTPUT%' AND zdroj ILIKE '%EXEC%';
```

K 20. 8. 2026 vraci prave tyhle dva skripty a oba jsou osetrene.

