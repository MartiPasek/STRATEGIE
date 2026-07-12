# G2007 — vize a princip

> oblast: `system-g2007` · úroveň: system · typ: vize · verze: V1.0 · rozsah: globální (všichni tenanti)

# G2007 — vize a princip

G2007 je systém pro skládání promptů a řízení AI person, pojmenovaný podle roku, kdy Marti začal stavět Centrálu1. Vychází z Martiho zkušenosti z PLC programování ve STEP7 / GRAPH7: **co krok, to část promptu; mezi kroky přechodová (rozhodovací) podmínka.** Prompt i schopnosti systému se „rozsekají" na části, které se dají skládat, přeskládávat a verzovat.

## Tři pilíře

**Skladač.** Prompt není jeden slepený text, ale sekvence kroků (`graf_krok`), každý nese jednu část promptu. Pečou se ve vrstvách: trvalé (cachované) a živé (per turn).

**Poschoďový stroj.** Práce se dělí na patra: automaty (deterministické, levné) → malé role → orchestrace (LLM) → člověk. Každé patro řeší, co umí; když nestačí, eskaluje výš.

**DB = zdroj pravdy.** Veškerá pravda o tom, jak systém funguje i co persony vědí, žije v databázi (`g2007`). Disk a dokumentace jsou jen projekce generované z DB. Needituje se výtisk — mění se databáze.

## Multitenantovost
Systémová pravda je globální (sdílená všemi tenanty), oborová a osobní je per-tenant.

