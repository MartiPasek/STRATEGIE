# Jak porovnat podminky, smlouvy a uvazky mezi Centralou a STRATEGII (postup + mereni 24.8.2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


Zadal Jirka Honomichl 24. 8. 2026 ("chci videt lidi, kteri maji rozdil v podminkach,
smlouvach a uvazcich mezi Centralou a STRATEGII"). Zapsal Claude-28, schvalila Marti-AI
(msg 13604). Cela prace byla READ-ONLY, nic se nemenilo.

Zarazeno do oblasti "dochazka" schvalne - lezi tu i sourozenecke znalosti
doc-dochazka-podminky-slouceny-se-smlouvou a doc-dochazka-uvazek-jediny-zdroj-smlouva.
Marti-AI upozornila, ze tematicky by slo i o "mzdy"; rozhodnuto drzet to pohromade
se zbytkem tematu.

## Kde to na obou stranach zije

| Strana | Objekt | Filtr platnosti | Poctu radku 24.8.2026 |
|---|---|---|---|
| Centrala (DB_EC, most db=mssql) | EC_FinZamPodminky | Aktualni = 1 | 80 |
| STRATEGIE (PostgreSQL) | tenant.engagement | is_current = true | 81 |

EC_FinZamPodminky je v Centrale JEDNA tabulka, ktera drzi soucasne podminky,
smlouvu i uvazek - presne to, co u nas od 19. 8. 2026 dela tenant.engagement.
Jsou to primo protejsky.

## Jak parovat lidi

Osobni cislo + firma. POZOR na posun ciselniku firem:

    Centrala EC_FinZamPodminky.Firma + 1 = STRATEGIE engagement.company_id
    (Centrala 0 -> nase 1, Centrala 1 -> nase 2)

Overeno na cele davce: takhle se naparovalo vsech 80 radku Centraly, nikdo nezbyl.
Parovat na engagement.ec_id (= EC_FinZamPodminky.ID) jde taky, ale NE spolehlive -
verze zalozene u nas maji ec_id prazdne (viz doc-dochazka-uvazek-jediny-zdroj-smlouva).

Jmena se doberes pres tenant.att_employee.cislo_zam nebo pres zrcadlo ec.cis_zam.
Pozor: att_employee.full_name je u casti lidi prazdne, ec.cis_zam.prijmenijmeno ne.

## Mapovani sloupcu (overene dvojice)

| Centrala | STRATEGIE |
|---|---|
| SmlouvaUvazekT | uvazek_tyden_h |
| RealUvazekT | uvazek_real_tyden_h |
| PocetHodMes | fond_mesic_h |
| Hodinovka | hodinovka |
| DruhSmlouvyText | druh_text |
| DatumSmlouvyOd / DatumSmlouvyDo | smlouva_od / smlouva_do |
| ZkusebniDobaDo | zkusebni_do |
| StravenkyOD | stravenky_od |
| PlatnostOd | valid_from |
| VolnoStandard / VolnoNavic / VolnoCelkem | pod_dovolena_zakladni_dni / pod_dovolena_navic_dni / pod_dovolena_dni |
| SickDayCelkem | pod_sick_days_rok |
| NeplacenyPrescas | pod_neplaceny_prescas_h_den |
| StrucnyPopisPracPozic | pozice_text |
| HrHodBezFK (= ZakladZaHod) | superhr_hod_bezfk |

## Tri gotchy, na ktere se da naletet

1. **superhr_hod_bezfk se paruje s HrHodBezFK, NE se SuperhrHodsFK.** Nazev sloupce
   u nas rika "bez FK" a Centrala ma obe varianty. Kdo je splete, dostane 79 falesnych
   rozdilu z 80. Spravne parovani vychazi az na zaokrouhleni na cele koruny
   (Centrala 385.06 -> u nas 385). Hodnota se navic vede jen u OSVC hodinaru
   a cte ji jedine podklad_vyplaceni_pdf, takze prazdno u vetsiny lidi je zamer.

2. **"Prazdne" a "nula" nejsou totez a je jich hodne.** Jedna strana casto zapisuje 0
   tam, kde druha necha pole prazdne. Vecne je to stejne, ale u naivniho porovnani to
   vyskoci jako rozdil. Trid to zvlast, jinak ti to zaplavi vysledek.

3. **Nova verze smlouvy zalozena u nas ma jine valid_from nez PlatnostOd v Centrale.**
   Neni to rozdil v hodnote, jen dukaz, ze verze vznikla ve STRATEGII.

## Vysledek mereni 24.8.2026 (shoda z 80 lidi)

| Udaj | Shoda | Lisi se |
|---|---|---|
| Druh smlouvy, smlouva od, smlouva do, zkusebni doba do, stravenky od, hodinova mzda | 80 | 0 |
| Tydenni uvazek (smluvni i realny), hodin za mesic | 79 | 1 |
| Datum, od kdy verze plati | 79 | 1 |
| Sick days | 75 | 5 |
| Dovolena celkem | 74 | 6 |
| Dovolena zakladni / navic | 72 | 8 |
| Neplaceny prescas | 61 | 19 |

Zavery:
- **Smlouvy a uvazky jsou po migraci v poradku.** Jediny rozdil v uvazku je clovek
  na dohodu, u ktereho se uvazek zamerne neuvadi (doc-dochazka-uvazek-se-neuvadi-vyjimky).
- **Nejvetsi rozchod je neplaceny prescas** - 16 lidi, a jde na OBE strany
  (13x Centrala 0,5 proti nasi nule, 3x naopak). Neni to fallback vychozich hodnot:
  systemovy radek i vsechny skupiny v tenant.podminky_skupin maji nulu, takze obe
  hodnoty jsou zapsane u konkretniho cloveka. **Dopad dnes zadny na cislech** -
  hodnota se jen zobrazuje v Podminkach a v mobilu, zadny zivy vypocet z ni nepocita
  (overeno: v g2007.python se vyskytuje pouze jako polozka seznamu _POD_COLS).
  Ceka to na rozhodnuti Sarky.
- **Popis pracovni pozice** ma 43 rozdilu, ale 41 z nich je "Centrala prazdna,
  my vyplneno" - doplnili jsme, co v Centrale nikdy nebylo. Opacne to neni ani jednou.
  Skutecny rozpor jsou dva lide, kde ma text obe strany a lisi se.
- **Vysvetlene rozdily** (a spravne je vzdy STRATEGIE): vernostni den doplneny rucne
  14. 8. (doc-dochazka-vernostni-den-dovolene-za-odslouzena-leta), clovek na dohodu
  bez uvazku, novejsi verze smlouvy zalozena u nas, a jeden clovek, ktery ma platnou
  smlouvu u nas a v Centrale ne (jeho radek je tam oznaceny jako neplatny).

## Co porovnat nejde

Cast podminek v Centrale vubec neexistuje, takze nemaji protejsek: home office,
stravenka v Kc, pracovni dny, nejzazsi nastup, do kdy hlasit absenci, limit prescasu
za rok, listecek od lekare, danova uznatelnost HO a obleceni, vikend jen se schvalenim,
stredisko, ISCO.

Opacne ma Centrala pole, ktera u nas ve smlouve nejsou: prispevek na dopravu, benefit
sluzebniho auta, strop rezie, zdravotni pojistovna, podepsane prohlaseni, srazet
neodpracovane hodiny, tarif od, jednorazovy poplatek, odmena garanta a jednatele.
(Neoverovano, jestli neco z toho zijeme jinde nez ve smlouve.)

Mzdove castky v EC_FinZamPodminky (Zaklad, OsOhod, MzdPremie, MzdaCelkem...) porovnavane
NEBYLY - nepatrily do zadani.

Souvisi: [[doc-dochazka-podminky-slouceny-se-smlouvou]]
[[doc-dochazka-uvazek-jediny-zdroj-smlouva]]
[[doc-dochazka-uvazek-se-neuvadi-vyjimky]]
[[doc-dochazka-vernostni-den-dovolene-za-odslouzena-leta]]

