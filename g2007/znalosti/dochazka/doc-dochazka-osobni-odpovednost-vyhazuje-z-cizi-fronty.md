# Osobní odpovědnost za docházku vyhazuje člověka z cizí fronty oprav (Peťa 3.9.2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Osobní odpovědnost za docházku vyhazuje člověka z cizí fronty oprav

> oblast: `dochazka` · zadala Peťa 3. 9. 2026, nasadil Claude-26

## Proč
Kristýna Marešová (Týnka) padala Petě do fronty „K vyřešení", protože podle stromu
skupin patří do kanceláří. Peťa si ji tam ale neřeší — Týnka se kontroluje sama —
takže ji **potvrzovala bez vyřízení a tím vznikaly chyby** (3. 9. 2026 takhle zavřela
nález „rozpad bez zakázky" u dne, který zakázku pořád neměl). Peťa: *„nechci ji mít
ani ve frontě, pak ji právě potvrzuji bez vyřízení a vznikají tím chyby."*

## Jak to je teď
Tabulka **`tenant.att_odpovednost`** (agenda `dochazka`, edituje se v kartě zaměstnance
→ dlaždice **Odpovědnost**) řídila od 24. 7. 2026 (Šárka) jen **notifikace**
(`att_fix_editors_for_emp` — osobní výjimka má přednost před stromem). **Fronta ji
nečetla**, takže notifikace chodily jinam než karta ve frontě.

Od 3. 9. 2026 ji čte i **`att_fix_queue` (v10)**: nová funkce `_sql_odpovednost_jinde()`
skládá `EXISTS` nad `att_odpovednost` a přidává se jako `AND NOT …` do dotazu na
anomálie i na rozpory. Kdo má aktivní osobní odpovědnost na **někoho jiného než
přihlášeného editora**, ve frontě toho editora se neobjeví.

Nastaveno pro Týnku (záznam #39, `user_id`=11 → `odpovedny_user_id`=11). Ověřeno:
pro Peťu (uid 18) se skryje, pro Týnku (uid 11) ne. Skryjí se dvě docházkové karty —
41 (aktivní) a 188 (neaktivní), obě její.

## ⚠️ Co tím NENÍ vyřešeno
**Týnka žádnou frontu neuvidí.** Není členkou skupiny DOCHÁZKA - OPRAVY, má jen
rodičovský přístup, a rodičům se fronta záměrně neplní (pravidlo z 18. 8. 2026).
Dostane **notifikaci** a den si otevře z ní. Kdyby ji měla vidět i ve frontě, musela
by být členkou skupiny — a působnost umí dnes jen `vse`/`vyroba`/`kancelar`, tedy
by viděla celou kancelář.

Obecně platí: **kdo má osobní odpovědnost nastavenou na needitora, vypadne z front
úplně.** Je to záměr (odpovědnost je silnější než strom), ale je dobré o tom vědět.

## Komu je to nastaveno (stav 3. 9. 2026 večer)

| Člověk | Odpovídá | Proč |
|---|---|---|
| Kristýna Marešová (Týnka) | sama sobě | kontroluje se sama, Peťa ji zavírala bez vyřízení |
| Jiří Honomichl | sám sobě | „bez docházky" — nekontroluje se |
| Marti Pašek | sám sobě | „bez docházky" — nekontroluje se |
| Michal Šik | sám sobě | „bez docházky" — nekontroluje se |

Poslední tři doplněny týž den večer. Peťa: *„do fronty mi padat nemají."* Nálezy se jim
kvůli příznaku „Bez docházky" stejně nezakládají — osobní odpovědnost navíc odkloní
i **rozpory**, které lidi hlásí sami a na které se ten příznak nevztahuje.

Mění se to v kartě člověka → dlaždice **Odpovědnost**, bez zásahu do kódu.

## Souvisí
[[doc-dochazka-prekryv-casu-blokuje-zezelenani-a-odbaveni-z-fronty]] — druhá pojistka
proti „odkliknuto, ale neopraveno" z téhož dne ·
[[doc-dochazka-nalez-se-vraci-dokud-pricina-trva]] — ta vracená pravidla lidi
s příznakem „Bez docházky" schválně přeskakují, ať se jim nic nevrací ·
[[doc-dochazka-priznak-bez-dochazky-v-podminkach]] — kde ten příznak žije.

