# Režie jako druh záznamu zrušena — historie překlopena na Práci (3. 9. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


ROZHODNUTÍ (Peťa, 3. 9. 2026)
Režie NENÍ druh záznamu. Model je: PRÁCE (zakázka Rezie / VR / PR / SW + činnost) — PAUZA — ABSENCE (na zakázce Rezie, druh dán činností). Kdekoli byl druh "Režie", má být "Práce".

PROČ TO NEBYLA KOSMETIKA
Dokud měl záznam druh Režie, server ho odmítl uložit v Opravách. Šárka ani nikdo jiný takový den neopravil. Tohle byl hlavní důvod k překlopení (Peťa), ne jen čistota číselníku.

CO BYLO ZMĚNĚNO — CELKEM 9 841 ZÁZNAMŮ tenant.att_entry (tenant 2), entry_type_id 2 (overhead) → 1 (work)
Krok 1 — platné záznamy, 5 849 (request #2679):
- A) 5 766 mělo zakázku → změněn jen druh
- B) 48 zakázku nemělo, ale mělo rozpad se zakázkou → zakázka vzata z úseku s nejvíc hodinami (u všech vyšla Rezie)
- C) 35 zakázku nemělo a rozpad nepomohl → dosazena Rezie
Krok 2 — škrtnuté (superseded) staré verze dnů, 3 992 (request #2680).
Po migraci: 0 záznamů s druhem Režie ve VŠECH stavech, 0 bez zakázky.
Rozpad (vyroba_work) se nemění — druh nenese, činnost sedí tam a zůstala.

PROČ I SUPERSEDED (Peťa rozhodla, argument dopsán při diskusi)
Kdyby se někdy nějaká oprava vracela zpět, škrtnutý záznam by ožil jako Režie a znovu by nešel uložit v Opravách. Ponechat v archivu druh, který systém neumí zpracovat, je odložený problém. Navíc Režie nikdy nepopisovala, co se stalo — ta práce byla vždy práce, jen špatně pojmenovaná. Nepřepisuje se historie, opravuje se překlep.

ZÁLOHY A NÁVRAT
tenant.att_entry__rezie_zaloha_20260903 (5 849 řádků, platné) a tenant.att_entry__rezie_zaloha_sup_20260903 (3 992 řádků, superseded). Obě mají id, entry_type_id, project_ref, ulozeno. Návrat = UPDATE att_entry ze zálohy podle id.
Skript: g2007.python kod=att_rezie_na_praci_migrace (umí dry_run; vedlejsi_ucinek=true, přes most se nespouští). Migrace nakonec proběhla jako SQL přes schvalovací banner.

CO SE PŘITOM ZJISTILO (opravy dřívějších tvrzení)
1. Leden–květen 2026 (4 234 záznamů) NEVZNIKLO ve STRATEGII postupně — naskočilo jedním importem z Centrály 31. 7. 2026. Sloupec source přenesl původní hodnotu (tablet/manual), takže to vypadalo jako průběžné píchání. Ověřuj created_at, ne source.
2. Vlastní, ve STRATEGII naklikaná Režie: 1 615 záznamů od 10. 6. 2026.
3. Záznamy bez zakázky (83) končí 20. 7. 2026 — tam byla Režie vypnuta v Opravách. Od té doby žádný nový nevznikl.
4. Celkový počet platných byl 5 849, ne 5 766 (to byla jen část se zakázkou). Číslo odhalil až dry run — dílčí počet se nesmí vydávat za celek.
5. 26 srpnových záznamů bez rozpadu není díra v kontrole: 22 z nich má 0,00 h (píchnutý příchod a hned odchod, není co rozpadat), zbytek patří Martimu, který má příznak "bez docházky". POZOR: Lukáš Horký si takto v srpnu píchnul nulu osmkrát — nevyřešeno, může být vada v appce.

SOUVISEJÍCÍ
Zdroje vzniku Režie byly uzavřeny dřív (g2007 doc-dochazka-rezie-neni-druh-zaznamu-je-zakazka): att_checkin, att_apply_work_selection, att_entry_project. Tablet a mobil Režii nabízely ještě po 21. 7., proto data pokračovala až do 3. 9.

