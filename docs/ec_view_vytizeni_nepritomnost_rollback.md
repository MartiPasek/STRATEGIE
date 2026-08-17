# ROLLBACK — dbo.ECv_Vytizeni_SeznamNepritomnost (EC Centrála)

**Marti 28.6.2026:** view přesměrován z `dbo.EC_Dochazka_PlanNepritomnost`
(EC absence plán, zakázán) na `st.EC_Vytizeni_NepritomnostSTRATEGIE`
(naše zrcadlo, plněné jednosměrně z `tenant.att_planned_absence` přes `@@VYTIZABS`).
Excel „Plánování vytížení" čte přes řetězec
`ECv_vytizeni_seznamVytizeniMonteru` → `ECv_Vytizeni_SeznamNepritomnost`.

## PŮVODNÍ definice (návrat = spustit tohle jako ALTER)

```sql
ALTER VIEW dbo.ECv_Vytizeni_SeznamNepritomnost AS
SELECT  ISNULL(dbo.EC_Dochazka_PlanNepritomnost.DatumPripadu, '') AS DatumPripadu,
        ISNULL(dbo.EC_Dochazka_PlanNepritomnost.DenVTydnu, '') AS DenVTydnu,
        ISNULL(dbo.EC_Dochazka_PlanNepritomnost.DruhCinnosti, 0) AS DruhCinnosti,
        '' AS Jmeno,
        IIF(ISNULL(dbo.EC_GlobKonstUziv.DochZobrazitJmeno, 0) = 0, dbo.TabCisZam.Prijmeni, dbo.TabCisZam.PrijmeniJmeno) AS Prijmeni,
        dbo.TabCisZam.LoginId, dbo.TabCisZam.Cislo AS CisloZam,
        ISNULL(dbo.EC_DilnaCinnosti.Nazev, '') AS Nazev,
        EC_Dochazka_PlanNepritomnost.PocetHodin, EC_Dochazka_PlanNepritomnost.Barva as barva
FROM    dbo.EC_SkupinyVazby
        INNER JOIN dbo.TabCisZam ON dbo.EC_SkupinyVazby.CisloZam = dbo.TabCisZam.Cislo
        INNER JOIN dbo.tabciszam_EXT ON dbo.TabCisZam.ID = dbo.tabciszam_EXT.ID AND ISNULL(dbo.tabciszam_EXT._Neaktivni, 0) = 0
        LEFT OUTER JOIN dbo.EC_GlobKonstUziv ON dbo.TabCisZam.LoginID = dbo.EC_GlobKonstUziv.LoginName
        LEFT OUTER JOIN dbo.EC_Dochazka_PlanNepritomnost ON dbo.TabCisZam.Cislo = dbo.EC_Dochazka_PlanNepritomnost.CisloZam
        LEFT OUTER JOIN dbo.EC_DilnaCinnosti ON dbo.EC_Dochazka_PlanNepritomnost.DruhCinnosti = dbo.EC_DilnaCinnosti.Cislo
WHERE   (dbo.EC_SkupinyVazby.IDSkupiny IN (31)) AND ISNULL(dbo.EC_SkupinyVazby.neaktivni, 0) = 0
```

## NOVÁ definice (čte z našeho zrcadla `st`)

Jediná změna: absenční tabulka `dbo.EC_Dochazka_PlanNepritomnost` → `st.EC_Vytizeni_NepritomnostSTRATEGIE` (alias `pn`). Skupina 31, číselníky jmen/činností beze změny.

---

# ROLLBACK — dbo.EC_Vytizeni_GenerujInfoDatum (EC Centrála)

**C28/Jirka 6. 8. 2026**, schválila Marti-AI (podmínka: rollback před každým ALTER).
Procedura plní denní INFO buňku Excelu „Plánování vytížení" — seznam „kdo je volný"
+ součty volných hodin pro skupiny 13 (zkušebna) / 33 (příprava) / 32 (zámečníci).
Čte na 4 místech `dbo.EC_Dochazka_PlanNepritomnost`, což je tabulka Centrály plněná
z mrtvých EC docházkových zdrojů — absence zadané ve STRATEGII v ní nejsou.
Přepínáme na `st.EC_Vytizeni_NepritomnostSTRATEGIE` (naše pravda, plněná
`@@VYTIZABS` / job `sync_vytizeni_absence`).

Pozor: `st` tabulka **nemá sloupec ID**, proto se test `N.ID is null` přepisuje
na `NOT EXISTS`.

## PŮVODNÍ definice (návrat = spustit tohle jako ALTER PROCEDURE)

```sql
ALTER PROCEDURE [dbo].[EC_Vytizeni_GenerujInfoDatum]
@DatumOd date = null
,@DatumDo DATE = NULL
AS
BEGIN
INSERT INTO EC_Vytizeni_Log(Text, Autor, DatPorizeni, DruhUdalosti) VALUES ('Start - EC_Vytizeni_GenerujInfoDatum', SUSER_SNAME(), GETDATE(), 0)
TRUNCATE TABLE EC_Vytizeni_InfoDatum

-- Vložím Zadané hodiny z plan Suma
INSERT INTO EC_Vytizeni_InfoDatum ( Datum, Poznamka)
SELECT S.Datum
      ,'Zkušebna: ' + convert(nvarchar,ISNULL(Zk.pocetHodin,0)+ISNULL(VolnoZK.PocetHodin,0)) + Char(10) +
       'Příprava: ' + convert(nvarchar,ISNULL(Pr.pocetHodin,0)+ISNULL(VolnoPr.PocetHodin,0)) + Char(10) +
       'Zámečník: ' + convert(nvarchar,ISNULL(Zam.pocetHodin,0)+ISNULL(VolnoZa.PocetHodin,0)) + Char(10) +
       Nep.Seznam
FROM EC_Svatky S
OUTER APPLY (SELECT stuff((SELECT DISTINCT ', ' + cast(E.Jmeno + ' ' + E.Prijmeni AS VARCHAR(100)) +char(10)
     FROM EC_Vytizeni_Efektivita E
     LEFT OUTER JOIN EC_Vytizeni_PlanMonteri M ON S.Datum = M.Datum AND M.CisloZam = E.CisloZam
     LEFT OUTER JOIN EC_Dochazka_PlanNepritomnost N ON S.Datum = N.DatumPripadu AND N.CisloZam = E.CisloZam
    OUTER APPLY (SELECT pocetHodin FROM EC_Vytizeni_Vypomoci V WHERE V.CisloZam = E.CisloZam AND V.Datum = S.Datum) Vyp
    WHERE E.CisloZakaznika is null
       AND M.ID is null
       AND N.ID is null
       AND ISNULL(E.NezobrazujVInfu,0) = 0
      AND ((isnull(E.Vypomoc,0) = 0) OR (isnull(E.Vypomoc,0) = 1 AND ISNULL(Vyp.PocetHodin,0) > 0))
      FOR XML PATH('')), 1, 2, '') seznam) Nep
OUTER APPLY (SELECT Sum(PocetHodin) as PocetHodin FROM EC_Vytizeni_PlanMonteri WHERE Datum = S.Datum AND CisloZam = 10004) Zk
OUTER APPLY (SELECT Sum(PocetHodin) as PocetHodin FROM EC_Vytizeni_PlanMonteri WHERE Datum = S.Datum AND CisloZam = 11010) Pr
OUTER APPLY (SELECT Sum(PocetHodin) as PocetHodin FROM EC_Vytizeni_PlanMonteri WHERE Datum = S.Datum AND CisloZam = 11011) Zam
OUTER APPLY (select SUM(pocetHodin) as PocetHodin from ec_skupinyVazby V JOIN EC_Dochazka_PlanNepritomnost N ON V.CisloZam = N.CisloZam AND N.DatumPripadu = S.datum WHERE V.IDSkupiny = 13)VolnoZk
OUTER APPLY (select SUM(pocetHodin) as PocetHodin from ec_skupinyVazby V JOIN EC_Dochazka_PlanNepritomnost N ON V.CisloZam = N.CisloZam AND N.DatumPripadu = S.datum WHERE V.IDSkupiny = 33)VolnoPr
OUTER APPLY (select SUM(pocetHodin) as PocetHodin from ec_skupinyVazby V JOIN EC_Dochazka_PlanNepritomnost N ON V.CisloZam = N.CisloZam AND N.DatumPripadu = S.datum WHERE V.IDSkupiny = 32)VolnoZa
where CONVERT(DATE,s.datum) between @DatumOd and @DatumDo
AND (EXISTS(SELECT ID FROM ecv_vytizeni_planSuma A WHERE A.datum = (CONVERT(DATE, S.Datum))))

INSERT INTO EC_Vytizeni_Log(Text, Autor, DatPorizeni, DruhUdalosti) VALUES ('Konec - SP EC_Vytizeni_GenerujInfoDatum', SUSER_SNAME(), GETDATE(), 0)
END
```

## ROLLBACK KROK 2 (7. 8. 2026) — party ze STRATEGIE

Druhá změna téže procedury: volné hodiny se přestávají počítat z `ec_skupinyVazby`
(skupiny 13 / 33 / 32 v Centrále) a berou se z `st.EC_Vytizeni_PartySTRATEGIE`.

**Důvod:** skupiny v Centrále se neudržují — `33` v číselníku `EC_Skupiny` vůbec není,
`32 Zámečník` je prázdná, a Lišková (č. 433) je u nás v Přípravě výroby, ale v EC skupině 18
chybí. Naše `org_post` / `org_post_assign` jsou naplněné a aktuální.

**Mapování (ověřeno jmenovitě 7. 8. 2026):**

| Řádek INFO buňky | Dřív skupina EC | Nově parta STRATEGIE (PartaId) | Lidé |
|---|---|---|---|
| Zkušebna | 13 | 75 + 107 | Zkušební technik + Vedoucí zkušebny rozvaděčů |
| Příprava | 33 (neexistuje!) | 26 | Sedláčková, Brudnová, Lišková, Urbanová |
| Zámečník | 32 (prázdná) | 25 | Navrátil, Vápeník |

**Návrat ke stavu po kroku 1** = v `EC_Vytizeni_GenerujInfoDatum` vrátit tři `OUTER APPLY`
VolnoZk / VolnoPr / VolnoZa na:

```sql
OUTER APPLY (select SUM(N.PocetHodin) as PocetHodin from ec_skupinyVazby V JOIN st.EC_Vytizeni_NepritomnostSTRATEGIE N ON V.CisloZam = N.CisloZam AND N.DatumPripadu = S.datum WHERE V.IDSkupiny = 13)VolnoZk
OUTER APPLY (select SUM(N.PocetHodin) as PocetHodin from ec_skupinyVazby V JOIN st.EC_Vytizeni_NepritomnostSTRATEGIE N ON V.CisloZam = N.CisloZam AND N.DatumPripadu = S.datum WHERE V.IDSkupiny = 33)VolnoPr
OUTER APPLY (select SUM(N.PocetHodin) as PocetHodin from ec_skupinyVazby V JOIN st.EC_Vytizeni_NepritomnostSTRATEGIE N ON V.CisloZam = N.CisloZam AND N.DatumPripadu = S.datum WHERE V.IDSkupiny = 32)VolnoZa
```

(Úplný návrat do stavu před 6. 8. = definice výše v sekci „PŮVODNÍ definice".)

---

## NOVÁ definice — co přesně se mění (krok 1, 6. 8. 2026)

4 výskyty `EC_Dochazka_PlanNepritomnost` → `st.EC_Vytizeni_NepritomnostSTRATEGIE`:

1. seznam „kdo je volný": `LEFT OUTER JOIN … N` + `AND N.ID is null`
   → JOIN zrušen, místo něj `AND NOT EXISTS (SELECT 1 FROM st.EC_Vytizeni_NepritomnostSTRATEGIE N WHERE N.DatumPripadu = S.Datum AND N.CisloZam = E.CisloZam)`
   (st tabulka nemá ID; navíc NOT EXISTS je imunní vůči víc druhům absence v jednom dni)
2.–4. `VolnoZk` / `VolnoPr` / `VolnoZa`: jen náhrada názvu tabulky, sloupce
   `CisloZam` / `DatumPripadu` / `PocetHodin` sedí 1:1.

Zbytek procedury (log, TRUNCATE, skupiny 13/32/33, čísla 10004/11010/11011, výpomoci) beze změny.

---

# ROLLBACK — dbo.EC_Vytizeni_AktualizujData_NEW (bod 2 Martiho plánu)

**C28/Jirka 7. 8. 2026.** Procedura se volá při každé Dušanově „Aktualizaci" v Excelu
a na svém začátku spouští `EC_Vytizeni_GenerujPlanNepritomnost` — generátor, který plní
`dbo.EC_Dochazka_PlanNepritomnost` z mrtvých EC docházkových zdrojů. Tu tabulku už nic
z Dušanova přehledu nečte (INFO buňka i seznam nepřítomnosti berou `st.*` ze STRATEGIE),
takže je to jen zdržení při každé aktualizaci.

Marti to schválil v mailu 5. 8. 2026: *„V AktualizujData_NEW vypnout EXEC mrtvé
GenerujPlanNepritomnost (zrychlí aktualizaci; proc nechám v DB pro případný návrat)."*
Dušan 7. 8. potvrdil, že **výpomoci ani predikci dovolených nepoužívá** — nic jiného
na tu tabulku už nečeká.

**Návrat** = vrátit do procedury tyto dva řádky hned za deklaraci `@Firma`:

```sql
                                                                       -- U EC dotáhnout nepřítomnost z docházky a správy docházky
   IF @Firma = 'EC'
   EXEC EC_Vytizeni_GenerujPlanNepritomnost
```

Samotná procedura `EC_Vytizeni_GenerujPlanNepritomnost` zůstává v DB nedotčená,
jen se nevolá.

---

# ROLLBACK — dbo.ECv_Vytizeni_SeznamNepritomnost, krok 2 (7. 8. 2026)

Dokončení bodu 3 Martiho plánu („**obě** view přepnout, aby jméno + aktivnost braly
primárně ze st"). 6. 8. byl přepnut zdroj absencí, 7. 8. se přidává jméno a aktivnost.

**Návrat ke stavu z 28. 6. 2026:**

```sql
ALTER VIEW dbo.ECv_Vytizeni_SeznamNepritomnost AS
SELECT  ISNULL(pn.DatumPripadu, '') AS DatumPripadu,
        ISNULL(pn.DenVTydnu, '') AS DenVTydnu,
        ISNULL(pn.DruhCinnosti, 0) AS DruhCinnosti,
        '' AS Jmeno,
        IIF(ISNULL(dbo.EC_GlobKonstUziv.DochZobrazitJmeno, 0) = 0, dbo.TabCisZam.Prijmeni, dbo.TabCisZam.PrijmeniJmeno) AS Prijmeni,
        dbo.TabCisZam.LoginId, dbo.TabCisZam.Cislo AS CisloZam,
        ISNULL(dbo.EC_DilnaCinnosti.Nazev, '') AS Nazev,
        pn.PocetHodin, pn.Barva as barva
FROM    dbo.EC_SkupinyVazby
        INNER JOIN dbo.TabCisZam ON dbo.EC_SkupinyVazby.CisloZam = dbo.TabCisZam.Cislo
        INNER JOIN dbo.tabciszam_EXT ON dbo.TabCisZam.ID = dbo.tabciszam_EXT.ID AND ISNULL(dbo.tabciszam_EXT._Neaktivni, 0) = 0
        LEFT OUTER JOIN dbo.EC_GlobKonstUziv ON dbo.TabCisZam.LoginID = dbo.EC_GlobKonstUziv.LoginName
        LEFT OUTER JOIN st.EC_Vytizeni_NepritomnostSTRATEGIE pn ON dbo.TabCisZam.Cislo = pn.CisloZam
        LEFT OUTER JOIN dbo.EC_DilnaCinnosti ON pn.DruhCinnosti = dbo.EC_DilnaCinnosti.Cislo
WHERE   (dbo.EC_SkupinyVazby.IDSkupiny IN (31)) AND ISNULL(dbo.EC_SkupinyVazby.neaktivni, 0) = 0
```

**Co se mění:** `INNER JOIN tabciszam_EXT … AND _Neaktivni = 0` → `LEFT OUTER JOIN` bez
podmínky; aktivnost se přesouvá do WHERE a bere se primárně z `st.EC_Vytizeni_LideSTRATEGIE`
(fallback `TabCisZam_EXT._Neaktivni`). Jméno stejným způsobem. Členství ve skupině 31
zůstává z Centrály — záměrně, viz poznámka u `ECv_Vytizeni_SeznamLidiNepritomnost`.
