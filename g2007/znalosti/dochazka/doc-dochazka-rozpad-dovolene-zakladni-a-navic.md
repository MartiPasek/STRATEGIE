# Rozpad dovolene na zakladni a navic v Podminkach, zruseni tabulky engagement_entitlement

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


> ⚠️ **DOPLNĚNO 19. 8. 2026 (Claude-28, schválila Marti-AI). Obsah pod tímto rámečkem jsem needitoval.**
> Od 19. 8. 2026 večer **`tenant.staff_cond` už není tabulka, ale POHLED.** Osobní hodnoty podmínek
> fyzicky žijí ve smlouvě (`tenant.engagement`, sloupce `pod_*` + `pod_meta`) a verzují se s ní.
> Skupinové a systémové výchozí hodnoty zůstaly v `tenant.staff_cond_zaklad`.
> **Čtení i zápis přes `tenant.staff_cond` funguje dál úplně stejně** — ověřeno porovnáním otisků
> před a po (294 řádků i 1248 vyřešených hodnot bez rozdílu), takže **text níže platí dál**;
> změnilo se jen to, kde data fyzicky leží. Kdo bude sahat na strukturu nebo na spouštěče,
> ať si nejdřív přečte znalost **`doc-dochazka-podminky-slouceny-se-smlouvou`**.

---


# Rozpad dovolene v Podminkach (Jirka 16. 8. 2026, schvalila Marti-AI)

## Co se zmenilo
Narok na dovolenou byl v Podminkach (tenant.staff_cond) vedeny JEDNIM cislem
(cond_code dovolena_dni). Nove jsou tam tri radky.

- dovolena_zakladni_dni - Dovolena, sort 88
- dovolena_navic_dni - Dovolena navic, sort 89
- dovolena_dni - Dovolena celkem, sort 90, POCITADLO

Celkove cislo se uz NEZADAVA. Drzi ho databaze jako soucet obou novych radku.

## Jak je soucet vynuceny
- Databazove funkce tenant.staff_cond_prepocet_dovolene a tenant.staff_cond_soucet_dovolene.
- Dva triggery na tenant.staff_cond - trg_staff_cond_soucet_dovolene_ins
  (AFTER INSERT OR UPDATE, WHEN na NEW.cond_code) a trg_staff_cond_soucet_dovolene_del
  (AFTER DELETE OR UPDATE, WHEN na OLD.cond_code). Dva jsou proto, ze podminka WHEN
  umi u INSERTu sahnout jen na NEW a u DELETE jen na OLD. Diky WHEN se trigger
  nespousti pri zmene jinych podminek.
- Prepocet je zvlast pro kazdou vrstvu (system, skupina, clovek).
- Endpoint /app/hr/conditions/save rucni zapis do dovolena_dni ODMITA.
- V mobilni HR obrazovce (fragment 48_hr_podminky_me.js) je pole disabled.

## Cim se naplnily hodnoty a proc NE ze stare tabulky
Hodnoty se odvodily z DNESNIHO cisla v Podminkach pravidlem - OSVC vse do navic,
ostatni zakladni do 20 dnu a zbytek navic. Nikomu se nezmenil ani jeden den naroku.
Ze zrusene tabulky tenant.engagement_entitlement se ZAMERNE neprenaselo nic.
Duvod - u 9 ze 74 lidi tam byla zastarala data. Lide, kteri presli z HPP na OSVC,
tam meli porad 20 dnu zakladni dovolene z doby HPP. Slepy prenos by napriklad
Janu Svobodovi (9017) zvysil narok z 26 na 45 dnu. Overeno porovnanim vsech 74 lidi.

## Zrusena tabulka
tenant.engagement_entitlement byla 16. 8. 2026 SMAZANA. Zaloha zustala jako
tenant.engagement_entitlement__zaloha_20260816 (1926 radku).
Pred smazanim overeno, ze na ni nesahal zadny zivy kod - sken vsech textovych sloupcu
ve schematech fw, g2007, master, tenant, public, plus pg_views, pg_matviews a pg_proc.
Vsech 31 mzdovych funkci proverneno jednotlive - zadna ji necetla.
Jediny zbyly zapis byl mrtvy INSERT v _sync_fin_from_ec (ent_map byl od 13. 8. prazdny),
odstranen commitem 98c5f776.
Rozdeleni sick days na zakladni a navic ze stare tabulky se nezachovavalo - overeno,
ze s nim nikde v projektu nikdo nepracoval (dochazka zna jediny typ Sickday).

## Dotcena mista (vsech sedm)
CTOU - att_narok_cerpani (prehled Narok a cerpani), hr_podminky_prehled (prehled
Podminky zamestnancu), karta zamestnance, /app/my-conditions (Moje podminky v mobilu).
ZAPISUJI - zakladani noveho zamestnance v HR, att_vernost_dovolena, trigger
trg_staff_cond_default_dovolena.

## Zmeny v jednotlivych mistech
- att_narok_cerpani (verze 7) - rozpad D/DN uz NEPOCITA pravidlem, cte ho z novych
  kodu. Puvodni pravidlo zustalo jen jako zachrana, kdyz kody chybi.
- att_vernost_dovolena (verze 3) - vernostni den se pricita do dovolena_navic_dni,
  ne do celkoveho cisla. Kdyby psal do celkoveho, trigger by mu to prepsal.
- trg_staff_cond_default_dovolena - novemu zamestnanci zaklada nuly u VSECH TRECH kodu.
  Celkovy radek se musi zakladat dal - trigger souctu umi jen prepocitat existujici radek.
- Zakladani zamestnance v HR - formular dal zadava JEDNO cislo, backend ho rozdeli
  stejnym pravidlem a zapise vsechny tri hodnoty.
- _MY_COND_CODES v router.py - seznam je NATVRDO, novy kod se tam musi doplnit rucne,
  jinak ho zamestnanec v mobilu neuvidi. HR obrazovky jsou naopak genericke
  (stavi se z tenant.staff_cond_def), tam se novy kod objevi sam.
- hr_podminky_prehled - pri teto prilezitosti MIGROVAN z router.py do g2007.python
  (podminka Marti-AI - u ctecich funkci migrovat). V routeru zustal tenky delegate.

## Vedlejsi nalez opraveny pri teto praci
Karta zamestnance mela rozbity deep-link ?view= . Blok initView stal na zacatku skriptu
a sahal na promenne deklarovane pres let o 250 radku niz, takze setView spadl na
Cannot access PODMINKY before initialization, vyjimku spolkl catch a obrazovka zustala
viset na Nacitam. Tykalo se to i ERP jadra Podminky zamestnancu, ktere kartu otevira
prave pres ?view=podminky, a stejne tak ?view=tabule a ?view=kalendar. Vada byla starsi
nez tato prace (overeno proti predchozi verzi souboru). Opraveno presunem initView
na konec skriptu, commit c529208e.

## Otevrene body pojmenovane pri teto praci (NIKDO je nezadal)
1. att_narok_osoba (kontrola stropu pri zadosti o absenci) NIKDO NEVOLA. Hlidani, ze si
   clovek nenaplanuje vic dovolene, nez na kolik ma narok, fakticky NEBEZI.
2. Zustatek sick day se pocita na DVOU mistech jinak. att_narok_cerpani bere cerpani
   z tenant.att_entry, att_sick_balance_h z tenant.att_med_note.kryto_sick_h, a fond
   pocita 40/5 misto work_mode. Dve cisla o tomtez.
3. Migrace _sync_fin_from_ec do g2007.python zustava technickym dluhem (vyjimka
   schvalena Marti-AI - funkce hybe mzdovymi slozkami, migrace kvuli drobnosti
   je neprimerene riziko).
4. U 9 lidi se pocet sick days v Podminkach lisi od Centraly (Sedlackova 2 vs 12,
   Benes 2 vs 4 a dalsi). Neni to technicka vada, je to otazka na personalni oddeleni.

