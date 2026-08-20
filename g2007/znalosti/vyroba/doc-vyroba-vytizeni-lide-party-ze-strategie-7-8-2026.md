# Plan absenci pro Dusana: lide a party ze STRATEGIE do Centraly, dokonceni Martiho planu (7.8.2026)

> oblast: `vyroba` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Plan absenci pro Dusana - dokonceni (C28/Jirka, 7.8.2026)

Navazuje na `doc-vyroba-vytizeni-absence-zdroj-opraven-6-8-2026`. Tim je splnen cely
schvaleny plan Martiho z mailu 5.8.2026. Schvalila Marti-AI (rozsireny rozsah).
Gotchy mostu z teto prace: `doc-system-strategie-most-gotchy-zapis-kodu-7-8-2026`.

## CO PRIBYLO

**Dve nove tabulky v DB_EC**, plnene stejnym syncem `sync_absence_to_ec_vytizeni`:
- `st.EC_Vytizeni_LideSTRATEGIE` (CisloZam PK, Prijmeni, Jmeno, Aktivni, synced_at) - 234 lidi
- `st.EC_Vytizeni_PartySTRATEGIE` (CisloZam+PartaId PK, Parta, synced_at) - 256 vazeb,
  plnena z `tenant.org_post_assign` + `tenant.org_post`

Filtry pri plneni part: `x.aktivni`, `o.aktivni`, clenstvi `active/invited`,
`platnost_do IS NULL OR >= dnes`, cislo_zam ciselne.

**`EC_Vytizeni_GenerujInfoDatum` krok 2**: volne hodiny se pocitaji z nasich part misto
`ec_skupinyVazby`. Mapovani: Zkusebna = party **75+107**, Priprava = **26**, Zamecnik = **25**.

**`EC_Vytizeni_AktualizujData_NEW`**: zakomentovano volani `EC_Vytizeni_GenerujPlanNepritomnost`
(bod 2 planu). Procedura zustava v DB pro navrat. Rollback vseho:
`docs/ec_view_vytizeni_nepritomnost_rollback.md`.

## PROC PARTY ZE STRATEGIE (Jirkuv podnet, data mu dala za pravdu)

Skupiny v Centrale se neudrzuji:
- skupina **33**, kterou procedura cetla pro "Pripravu", **v ciselniku EC_Skupiny VUBEC NENI**
  (ID skacou 32 -> 35) -> radek "Priprava" v INFO bunce nikdy nic neukazal, od 11/2024
- skupina **32 Zamecnik** je **prazdna**
- **Liskova c.433** je u nas v parte PRIPRAVA VYROBY, ale v EC skupine 18 chybi

Po zmene (overeno na 31.12.2026): `Zkusebna: 24 | Priprava: 16 | Zamecnik: 8` - drive
u dvou z nich vzdy nuly.

**`org_post.ec_id` NENI vazba na EC_Skupiny** (org_post 25 ZAMECNIK ma ec_id 25, ale
EC_Skupiny 25 = "Personalni"; org_post 75 -> 79, 107 -> 189). Miri na org strukturu
Centraly, ne na skupiny. Mapovani part je proto rucni - viz tabulka vyse.

`org_post_assign` zvlada N:N (48 lidi je ve vice partach, max 20). Vazba na cloveka je
pres `employee_id` = karta, `att_employee.cislo_zam` uz JE cislo zamestnance EC.

## DUSAN ROZHODL (7.8.2026)

- **vypomoci NEPOUZIVA** -> `ECv_Vytizeni_Vypomoc` se neresila (44 radku, jeden clovek,
  posledni zapis 31.1.2025, nula budoucich)
- **predikci dovolenych NEPOUZIVA** -> neozivena (byla natvrdo leto 2025, rezerva 24 h/den,
  fiktivni zamestnanec c.12001)
Diky tomu slo vypnout mrtvy generator - nic uz na `EC_Dochazka_PlanNepritomnost` neceka.

