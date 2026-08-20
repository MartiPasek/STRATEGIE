# Odpovědnost — schvalování volna + kontrola docházky (org mapa EUROSOFT, HR 5.8.2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Zdroj pravdy
Schvalovatele volna vrací tenant.resolve_approvers(p_tenant, p_emp, p_datum) — odvozuje z org_post hierarchie + att_approver_group/att_approver (řeší i zástupce). NEBERE att_odpovednost (HR výjimky z přehledu „Odpovědnost") — ty se do resolveru zatím nepromítají (napojení = Jirka/Marti-AI). Kontrola docházky jede zvlášť přes att_fix editory.
HR přehled: uzel „Odpovědnost" pod Kartou zaměstnance (karta-zamestnance?view=odpovednost, endpoint /app/hr/odpovednost-list) — „Schvaluje volno" = aktuální (výjimka, jinak odvozeno), Zdroj ukáže i systémového.

## Org hierarchie (EUROSOFT, dle HR 5.8.2026)
Marti Pašek (jednatel) = vedení. Přímí podřízení:
- Jirka Veverka — vedení projektů výroby rozvaděčů (VP)
- Petr Beneš — elektroprojekce
- Dušan Havlát — výroba rozvaděčů
- Mirek Mareš — automatizace
- Petra Šafránková — nákup / logistika / mzdy
- Pavel Zeman — obchod
- Jiří Honomichl, Kristýna Marešová — IT digitalizace pro EUROSOFT (tým Marti)
- Michal Šik — správce IT (tým Marti)
- Jan Svoboda — IT pro Intersoft (pod ním Ondřej Pillár)
- Šárka Novotná — HR
- Michaela Hladíková — BOZP / PO / TISAX

## Schvalování volna (kdo koho)
- Přímí podřízení Marti → primární Marti, ZÁSTUPCE = Šárka Novotná (HR). Nastavit je_zastupce, NE fallback.
- Šárka Novotná <-> Michaela Hladíková — vzájemně.
- Výroba → Dušan Havlát; VP → Jirka Veverka; referentky nákupu → Petra Šafránková; obchod → Pavel Zeman; automatizace (vč. Zuzany Duspivové) → Mirek Mareš; Ondřej Pillár → Jan Svoboda.

## Automatizace (PLC OSVČ) — BEZ schvalovatele (HR 6.8.2026)
Středisko Automatizace = 10 OSVČ PLC programátorů (Brož, Nový, J.Svoboda, Benetka, Kubín, Terla, Siřiště, Ondra, Šik, Mareš). Pravidlo: PLC OSVČ nemají schvalovatele volna ani kontrolu docházky — je to o domluvě = „nikdo". Dnes jim to fallback hází na Šárku → vyřadit z fallbacku, resolver má vracet prázdno. VÝJIMKY: Miroslav Mareš (vede automatizaci → Marti), Michal Šik (IT správce → Marti). Zbylých 8 = bez schvalovatele (volno i docházka).

## Kontrola docházky
- Zuzana Duspivová → Mirek Mareš.
- Automatizace (PLC OSVČ, 8 lidí) → nikdo (o domluvě).

## Co dnes resolver vracel jinak (k srovnání v org struktuře — Jirka/Marti-AI)
Beneš (Jirka → má Marti), K. Marešová (Petra → Marti), Duspivová (Šárka → Mareš), Šárka Novotná (nikdo → Míša Hladíková), Šik (fallback Šárka → Marti), Honomichl/Pillár ověřit.
Pozn.: fallback approver group dnes = Šárka Novotná → padají na ni nezařazení (Šik, Duspivová, PLC OSVČ). Opravit napojením v org struktuře / vyřazením z fallbacku, ne fallbackem.

