# Podmínky: sick days a dovolená v jednom sloupci

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Podmínky zaměstnanců — sick days a dovolená v JEDNOM sloupci (rozhodnutí Šárka, 26. 8. 2026)

**Rozhodnutí (Šárka = zdroj pravdy, HR):** V přehledu Podmínky poměrů se **sick days** i **dovolená**
drží v **jednom sloupci**, ne rozpad „základ + navíc + celkem".

- **Sick days:** hodnota z `pod_sick_days_navic` se slévá do `pod_sick_days_rok`, navíc se nuluje —
  u **všech druhů** poměru (14 OSVČ, kde sick chybně sedělo v navíc, + 3 HPP s navíc). Pak se ruší
  sloupce **Sick navíc** a **Sick celkem** (celkem byl dopočet).
- **Dovolená:** stejný princip — sloupec **Dovolená navíc** se po sloučení ruší jako zbytečný.

**Proč:** Jiří Honomichl (uživatel přehledu) potřebuje sick day v jediném sloupci; rozpad základ/navíc
byl matoucí a u OSVČ vedl k tomu, že hodnota spadla do „navíc" a hlavní sloupec byl 0.

**Vlastnictví:** přehled Podmínky poměrů + `pod_*` sloupce na `tenant.engagement` = modul Jirky
(Claude-28 / Jiří Honomichl). Změnu (data i UI) provádí on. Šárka (Claude-25) jen zadala.

**Gotcha:** přesun navíc→hlavní je idempotentní (po přesunu navíc=0, re-run bez efektu). Nic se nemaže.

