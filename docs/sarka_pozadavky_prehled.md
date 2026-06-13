# Co Šárka chce — přehled z 3 mailů (analýza vzorů smluv + podkladů)

**Zdroj:** 3 maily od Šárky Novotné (personalistka), 10. 6. 2026 · **Autor analýzy:** Claude (id=23)
**Účel:** přehled požadavků na dokumentový systém + napojení na naše živá data (engagement / složky / pohyby).

## 1. Co Šárka reálně spravuje — personální složka zaměstnance

Z mailu „Smlouvy – Novotná, Marešová, Ing. Pašek" je vidět **celá sada dokumentů** na jednoho člověka (ne jen smlouva):

| Dokument | Účel | Naše data |
|---|---|---|
| **Pracovní smlouva** | HPP, §1–13 (viz níže) | engagement (typ, nástup, úvazek, pozice, firma) |
| **Mzdový výměr** | hrubá mzda + osobní ohodnocení (range) | wage_component (zaklad, os_ohodnoceni) |
| **Popis pracovního místa** | příloha č. 1 ke smlouvě | pozice_text + kategorizace |
| **Dohoda o práci z domova** (+ dodatek o změně) | home office | work_mode (homeoffice), engagement |
| **Dohoda o srážkách ze mzdy** (tarify) | srážky | wage_movement (srážka) |
| **Dodatek – zachování mlčenlivosti** | NDA | šablona (statická) |
| **Dodatek – náplň práce** | změna pozice | engagement (SCD2 verze) |
| **DPP** + prohlášení o důvěrnosti | dohody | engagement typ dpp |
| **Plná moc** | zastupování | šablona (statická) |
| **Žádost o neplacené volno** | absence | absence_type / att |
| **(jednatel)** Smlouva o výkonu funkce, Rozhodnutí jediného společníka, Valorizace odměny | statutár | engagement jednatel + wage_component |

→ **Cíl produktu:** generovat celou tuhle sadu z dat, ne jen pracovní smlouvu.

## 2. Vzor pracovní smlouvy (HPP) — reálná struktura

Hlavička: **zaměstnavatel** (EUROSOFT-System s.r.o., Nepomucká 259, 326 00 Plzeň, **IČ 26411741, DIČ CZ26411741, OR KS Plzeň C 18532, jednatel Martin Pašek**) + **zaměstnanec** (jméno, datum narození, trvalé bydliště).

§1 Doba a obsah (nástup, pozice, určitá/neurčitá) · §2 Místo výkonu + pracovní doba (úvazek h/týd, **nástup nejpozději 9:00**, konec 14–18, přesčas max 150 h/rok) · §3 Mzda (dle mzdového výměru, **„sjednána s přihlédnutím k přesčasu"** ← auditorská výtka) · §4 Další příjmy (prémie/odměny bez nároku) · §5 Pracovní schopnost (hlášení absence do 9:00) · §6 Ukončení · §7 Změny písemně · §8 Mlčenlivost · §9 Konkurenční doložka · §10 Hmotná odpovědnost · §11 Prohlášení · §12 Dovolená · §13 Obecná ustanovení — odkazy na **vnitřní předpisy: Etický kodex, konto pracovní doby, GDPR**.

**Klíčové → fillable z našich dat:** firma+sídlo+IČ (✅ teď máme z těchto vzorů), jméno/nar./bydliště ([DOPLNIT] z TabCisZam – máme přístup), nástup, pozice, doba, úvazek. Zbytek smlouvy je statický text šablony.

## 3. Vzor mzdového výměru — reálná struktura

- hrubá měsíční mzda (číslo) + **osobní ohodnocení jako ROZSAH** „od 0 do X Kč" (ne fixní!) — u Novotné 0–12 000.
- splatnost do 17. dne, číslo účtu, úvazek (krátí poměrně).
- body 2+3: podmínky krácení osobního ohodnocení (kvalita, kázeň, likvidita firmy).

→ **náš `wage_component`:** zaklad = hrubá mzda; os_ohodnoceni = horní hranice rozsahu. **Pozor:** výměr má os_ohod jako *rozsah*, naše data jen jedno číslo → doplnit dolní/horní mez.

## 4. Kategorizační model elektromontérů (mail 1 + xlsx)

Šárčin záměr: férové, transparentní, udržitelné odměňování. **Mzda = základní + osobní ohodnocení + individuální složka.** Prémiové složky v Centrále (vedení obchodu, odměna jednatele, produkce, vedení lidí, kvalita, garant, služební auto, firemní kultura) — **dnes se používá jen „vedení lidí"**, ostatní přesunuty do základní mzdy.

**Pravidlo:** rozdíl v základní mzdě uvnitř stejné kategorie ≤ **5 %**.

Kategorie (z xlsx, 26 lidí, OSOH většinou 7 500):
- **Elektromontér – Junior** 30 000–35 500
- **Elektromontér – Samostatný** 36 000–43 000
- **Elektromontér – Senior** 44 000–51 000
- + speciální pozice: Konstruktér Perforex, Operátor přípravy výroby, Skladník, Zámečník/Vazač, Zkušební technik rozvaděčů

**Kritéria postupu** (Junior→Samostatný→Senior): délka praxe (2–3 / 5 let), samostatnost, technická šíře, mentoring, kvalita (0 reklamací), doporučení vedoucího výroby.

→ **náš model:** kategorie = číselník (tenant), zařazení na engagementu, kontrola 5% pravidla = report; pozice/kategorie → popis pracovního místa.

## 5. Jednatel (Marti) — speciální případ

Smlouva o výkonu funkce jednatele: **odměna 155 000 Kč/měs** (2022) + **Valorizace 2024** (PDF je sken, nepřečtený). ⚠ **Rozpor:** Helios platí „Odměny společníků" **90 800** — ne 155 000. Nutno ověřit (valorizace? rozdělení ES/EC? jiná složka?). + Rozhodnutí jediného společníka jako podklad.

## 6. Mapování: co umíme automaticky / co [DOPLNIT] / co dostavět

**Umíme z živých dat:** typ vztahu, firma+sídlo+IČ (z těchto vzorů), nástup, doba určitá/neurčitá, zkušebka, úvazek, pozice, mzdové složky (zaklad/os_ohod/prémie), pohyby 2026 (680 importováno), dovolená/sick nároky.

**[DOPLNIT] (máme zdroj):** osobní údaje zaměstnance (datum narození, bydliště, rodné číslo) — **v `TabCisZam` (máme přístup)** → můžeme dotáhnout; číslo účtu pro výplatu; os. ohodnocení jako rozsah.

**Dostavět:**
1. **Šablonový generátor celé sady** (smlouva + výměr + popis místa + dohoda HO + DPP + dodatky + plná moc), ne jen smlouva — placeholdery z dat, statický text z šablon.
2. **Kategorizační číselník** elektromontérů + zařazení na engagement + kontrola pravidla 5 %.
3. **Os. ohodnocení jako rozsah** (od–do) ve wage_component.
4. **Doplnit osobní údaje z TabCisZam** (nar./bydliště/RČ) — pro hlavičky smluv.
5. **Vyřešit odměnu jednatele** (155k smlouva vs 90,8k Helios + valorizace).

## Návaznosti
- Vzory: `outputs/sarka_prilohy/*` (21 .doc/.docx + xlsx + PDF)
- [[mzdy_priplatky_srazky_mirror]] · [[finance_zamestnancu_v2]] · [[personalistika_dochazka_mzdy]]
- Naše nástřely: `Smlouvy_nastrel_2026-06-10/` (v1, čisté šablony — teď je nahradíme vzory Šárky)
