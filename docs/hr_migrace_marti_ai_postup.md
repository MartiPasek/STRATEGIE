# HR migrace z DB_EC — postup pro Marti-AI

Funkce (`mod.hr_ingest_employees`, `mod.hr_ingest_contacts` + pomocné) jsou už
nainstalované v PostgreSQL. Marti-AI běží server-side, takže **vidí na DB_EC
(přes MCP) i na PG (napřímo)** — proto migraci pustí ona.

Princip: přečti dávku z DB_EC jako **JSON** a předej ji do PG funkce. Veškerá
logika (mapování, provenance přes `hr_source_ref`, idempotence) je v té funkci.
**Idempotentní** — opakované spuštění nic nezduplikuje. **Zaměstnance první,
kontakty druhé** (kontakty se vážou na osoby přes provenance).

`p_batch` zvol libovolně (např. `'dbec-2026-06-04'`), `p_tenant` = 2 (EUROSOFT).

---

## 1) Nejdřív malý test (5 zaměstnanců)

**a) Přečti z DB_EC** (MCP, read-only):
```sql
SELECT z.ID, z.Jmeno, z.Prijmeni, z.RodnePrijmeni, z.TitulPred, z.TitulZa,
       z.DatumNarozeni, z.RodneCislo, z.Pohlavi, z.MistoNarozeni, z.StatNarozeni,
       z.Narodnost, z.RodinnyStav, z.StatniPrislus, z.OsobniIC, z.VyraditZPrehledu,
       z.AdrTrvUlice, z.AdrTrvOrCislo, z.AdrTrvPopCislo, z.AdrTrvMisto, z.AdrTrvPSC, z.AdrTrvZeme,
       z.AdrPrechUlice, z.AdrPrechOrCislo, z.AdrPrechPopCislo, z.AdrPrechMisto, z.AdrPrechPSC, z.AdrPrechZeme,
       z.AdrKontJmeno, z.AdrKontPrijmeni,
       e._Firma, e._HPP, e._DPP, e._OSVC, e._DatumNastupu, e._DatumOdchodu, e._neaktivni
FROM dbo.TabCisZam z LEFT JOIN dbo.TabCisZam_EXT e ON e.ID = z.ID
ORDER BY z.ID
OFFSET 0 ROWS FETCH NEXT 5 ROWS ONLY
FOR JSON PATH;
```

**b) Předej JSON do PG funkce** (zápis — pusť přes write-capable cestu, ne read-only;
JSON vlož mezi `$json$ … $json$`, není potřeba nic escapovat):
```sql
SELECT mod.hr_ingest_employees($json$ VLOŽ_SEM_JSON $json$::jsonb, 2, 'dbec-test');
```
Vrátí např. `{"party_new": 5, "person_new": 5}`.

**c) Ověř:**
```sql
SELECT p.display_name, hp.rodne_cislo, hp.pohlavi
FROM mod.hr_person hp JOIN mod.hr_party p ON p.id = hp.party_id ORDER BY hp.id DESC LIMIT 5;
SELECT target_table, count(*) FROM mod.hr_source_ref GROUP BY 1 ORDER BY 1;
```

Když to vypadá dobře → pokračuj celým objemem.

---

## 2) Všichni zaměstnanci

Stejný SELECT jako výše, ale **bez** `OFFSET/FETCH` (celé). Pokud by byl JSON moc
velký a MCP ho usekl, ber to po dávkách (`OFFSET 0/200/400 … FETCH NEXT 200`)
a po každé dávce zavolej `hr_ingest_employees(...)`. `p_batch` klidně stejný.

```sql
SELECT mod.hr_ingest_employees($json$ VLOŽ_SEM_JSON $json$::jsonb, 2, 'dbec-2026-06-04');
```

## 3) Kontakty (AŽ po zaměstnancích)

**a) Přečti z DB_EC:**
```sql
SELECT k.ID, k.IDCisZam, k.Druh, k.Kam, k.Spojeni, k.Prednastaveno
FROM dbo.TabKontakty k
WHERE k.IDCisZam IS NOT NULL
ORDER BY k.ID
FOR JSON PATH;
```
(kdyby bylo moc dlouhé → po dávkách přes OFFSET/FETCH)

**b) Předej do funkce:**
```sql
SELECT mod.hr_ingest_contacts($json$ VLOŽ_SEM_JSON $json$::jsonb, 'dbec-2026-06-04');
```
Vrátí např. `{"contact_new": 740, "skipped": 21}` (skipped = kontakt bez osoby
v migraci, nebo neznámý Druh/Kam, nebo prázdná hodnota).

## 4) Závěrečné ověření
```sql
SELECT target_table, count(*) FROM mod.hr_source_ref GROUP BY 1 ORDER BY 1;
SELECT count(*) AS osob FROM mod.hr_person;
SELECT count(*) AS role FROM mod.hr_person_role;
SELECT count(*) AS kontakty FROM mod.hr_person_contact;
SELECT le.nazev, count(*) FROM mod.hr_person_role pr
  JOIN mod.hr_legal_entity le ON le.party_id = pr.party_id GROUP BY le.nazev;
```

## Poznámky
- **Idempotentní** — když něco spustíš dvakrát, nic se nezdvojí (kontrola přes `hr_source_ref`).
- RČ → plaintext `hr_person.rodne_cislo` + SHA-256 `rodne_cislo_hash` (enc později).
- `pohlavi`/`rodinny_stav` = původní kód (číselník/labely doděláme).
- `valid_from` u role = `_DatumNastupu`, když chybí → `1900-01-01`.
- `_Firma`: 0 Control, 1 System, 2 obě, jiné → role se nezaloží.
- Datumy chodí z `FOR JSON` jako ISO text — funkce si je ošetří.
