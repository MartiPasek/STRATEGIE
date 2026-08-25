# Zálohovací tabulka může vlastnit sekvenci živé tabulky — CASCADE pak rozbije provoz (25. 8. 2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Zálohovací tabulka může vlastnit sekvenci ŽIVÉ tabulky — `CASCADE` pak rozbije provoz

> Zjistil Claude-28 při rušení zálohovacích tabulek **25. 8. 2026** na zadání
> **Jirky Honomichla**, schválila **Marti-AI** (msg 13661, 13664).
> Navazuje na [[doc-dochazka-podminky-slouceny-se-smlouvou]].

## Co se stalo

Rušení šesti zálohovacích tabulek podmínek spadlo na `DependentObjectsStillExist`:

```
cannot drop table tenant.podminky_vychozi__zaloha_20260821 because other objects depend on it
DETAIL: default value for column id of table tenant.podminky_osobni
        depends on sequence tenant.staff_cond_id_seq
```

Záloha vznikla jako kopie tabulky, která sekvenci vlastnila — a **vlastnictví sekvence
šlo se zálohou**, zatímco `DEFAULT` na ni zůstal i v tabulce ŽIVÉ. `DROP … CASCADE` by
sekvenci smazal a **první zápis do `tenant.podminky_osobni` by spadl**. Ta tabulka měla
v tu chvíli 0 řádků, takže by se to projevilo **až u prvního člověka bez platné smlouvy** —
tichý časovaný problém, ne okamžitá chyba.

⚠️ **Transakce se celá vrátila zpět, nic se nesmazalo.** To je na tom to jediné dobré:
`DROP TABLE` bez `CASCADE` je bezpečný — **selže hlasitě místo aby něco tiše odnesl**.

## Proč to standardní kontrola nenajde

Před rušením tabulky se běžně kontroluje: pojistky (`tenant.pojistka.kontrola`), živý kód
(`g2007.python.zdroj`), obsah webu a mobilu (`g2007.soubor`), závislé pohledy
(`information_schema.view_table_usage`) a cizí klíče. **Sekvence do žádné z nich nespadá.**
Všech pět kontrol vrátilo nulu a tabulka přesto smazat nešla.

## Kontrola, kterou je potřeba doplnit

```sql
SELECT s.relname AS sekvence, t.relname AS vlastni_ji, a.attname AS sloupec
FROM pg_class s
JOIN pg_namespace ns ON ns.oid = s.relnamespace AND ns.nspname = 'tenant'
LEFT JOIN pg_depend d ON d.objid = s.oid AND d.deptype = 'a'
LEFT JOIN pg_class t ON t.oid = d.refobjid
LEFT JOIN pg_attribute a ON a.attrelid = d.refobjid AND a.attnum = d.refobjsubid
WHERE s.relkind = 'S';
```

a k tomu, kdo sekvenci používá ve výchozí hodnotě sloupce — přes `pg_attrdef`
a `pg_get_expr(ad.adbin, ad.adrelid)`.

## Postup opravy (schválila Marti-AI, msg 13664)

1. `ALTER SEQUENCE tenant.staff_cond_id_seq OWNED BY tenant.podminky_osobni.id;`
   — přepojí vlastnictví na tabulku, která sekvenci doopravdy používá
2. `ALTER SEQUENCE tenant.staff_cond_id_seq RENAME TO podminky_osobni_id_seq;`
   — nepovinné, ale čisté: starý název u cizí tabulky vypadá jako nedokončená migrace
3. teprve pak `DROP TABLE … ` **bez `CASCADE`**

✅ **Ověřeno 25. 8. 2026:** přejmenování se do `DEFAULT` sloupce **propsalo samo** —
PostgreSQL si v `nextval('…'::regclass)` drží OID, ne text názvu. Třetí krok
(`ALTER TABLE … SET DEFAULT`), kterého se Marti-AI obávala, nebyl potřeba.
Po zrušení ověřeno čtením: šest zálohovacích tabulek pryč, `podminky_osobni` stojí,
její počítadlo běží pod novým názvem, 81 platných smluv a 1 119 řádků podmínek beze změny.

## Pravidlo

**Před zrušením jakékoli tabulky (a u zálohovacích kopií dvojnásob) kontroluj i sekvence.**
A `CASCADE` nepoužívej jako způsob, jak se dostat přes chybu — ta chyba je informace,
ne překážka. Vlastnictví se dá přepojit, data se smazat nedají zpátky.

Souvisí: [[doc-dochazka-podminky-slouceny-se-smlouvou]]
[[doc-system-strategie-podminky-vychozi-na-sirku-a-historie-zmen]]

