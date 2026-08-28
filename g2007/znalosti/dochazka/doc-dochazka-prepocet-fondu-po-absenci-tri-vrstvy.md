# Přepočet doplnění do fondu po absenci - tři vrstvy a díra v žádostech z appky (27. 8. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


**Zadala Peťa, postavil Claude-26, 27. 8. 2026.** Vše ověřeno v živém kódu a datech.

## Co se stalo

Pojistka `absence-prepocita-doplneni-do-fondu` byla zelená a přitom nehlídala, co slibuje jménem.
Vychází z **už existujícího** dopočtu (join na `fond_doplneni`) a ptá se, jestli nevznikl dřív než
absence. Den, kde automat **nesáhl vůbec**, do ní nespadne - není co k čemu přiložit. A to je ten
horší případ. Kdo bude psát podobné pravidlo, ať vyjde ze dnů s absencí, ne z dopočtů.

Přes to se našla skutečná díra: **žádost o absenci z mobilní appky nespouštěla přepočet fondu.**
Den v docházce vzniká už PODÁNÍM žádosti (pravidlo Peti z 30. 7. 2026), ne až schválením, a
ZRUŠENÍM žádosti zase mizí - ani jedno přepočet nevolalo. Schválení přepočítávat nemusí, tam se
s docházkou nehýbe. Noční srovnání sahalo jen 4 dny zpět, takže starší den zůstal špatně natrvalo.

## Tři vrstvy (stav po 27. 8. 2026)

1. **Hned při zásahu** - cílený přepočet jednoho dne. Volají Opravy docházky (`att_fix_entry`,
   `att_fix_add`, `att_fix_void`, `att_fix_merge`, `att_fix_polozka`, `att_fix_move_day`),
   Správa docházky (`dochazka_abs_save` / `_new` / `_delete` přes `_prepocti_fond`), mobilní
   "tady budu jinde" (`att_absence`) a **nově podání i zrušení žádosti** (`att_absence_request`,
   `att_absence_cancel`).
2. **V noci** - `att_maybe_level_catchup` srovnává nově **celý otevřený měsíc** místo natvrdo
   4 dnů. Okno začíná prvním dnem prvního NEZAMČENÉHO měsíce podle `tenant.att_period_lock`,
   takže do uzavřených mezd nesáhne; když se okno nepodaří spočítat, zůstávají 4 dny.
   Automat je idempotentní (své řádky v okně smaže a vloží znovu), proto je širší okno bezpečné.
3. **Fronta k vyřízení** - nový nález `den_nesrovnany_na_fond` v `att_anomaly_scan`. Den s absencí,
   kde hodiny nesedí na denní fond a automat u něj nemá žádný svůj řádek.

## ⚠️ Nález, se kterým nejde nic udělat, do fronty NEPATŘÍ

Napoprvé jsme nález pustili na celou historii od června - spadlo 9 dnů (7 v červnu, 2 v červenci).
Jenže **ty už opravit nejde, prošly mzdou.** Peťa: takový nález nikomu nemá chodit ani do fronty.
Devět nálezů bylo smazáno a okno pravidla zúženo na **otevřené období** (stejný výpočet ze zámku
jako u nočního srovnání). Platí to obecně, i pro chystaný denní spouštěč pojistek.

Nález je navíc **jen do fronty, bez notifikace** - je to systémová nesrovnalost, člověk s ní nic
nezmůže, řeší ji editor oprav.

## Detaily, které se snadno zapomenou

- Fond dne se bere dohodnutým způsobem - úvazek ze smlouvy dělený dny v týdnu
  (pojistka `fond-z-uvazku-ne-z-centraly`). Hodiny dne ze sdíleného `att_den_hodiny`
  (mzdové + absence - nad fond, tedy vzorec FPD kanceláře). **Žádný nový vzorec se nepsal.**
- Lidi, kteří docházku nevedou, poznej z příznaku `engagement.plny_fond_bez_dochazky`
  (je na SMLOUVĚ, ne na `att_employee`), ne z natvrdo psaných osobních čísel.
- Zálohy původních skriptů leží v `g2007.python` pod kódy `att_absence_request__zaloha_20260827`,
  `att_absence_cancel__zaloha_20260827`, `att_maybe_level_catchup__zaloha_20260827`,
  `att_anomaly_scan__zaloha_20260827`.
- Pojistky k tomu: `zadost-z-appky-prepocita-fond`, `nocni-srovnani-cely-otevreny-mesic`,
  `nalez-den-nesrovnany-na-fond`.

## Gotcha mostu (NEOVĚŘENO, jen popis chování)

Zápis do `g2007.python` přes `replace()` opakovaně spadl s `KeyError` na název dolarové značky.
Nezáleželo na jménu značky. Prošlo to, až když blok neobsahoval komentáře uvozené křížkem a
uzavírací značka stála na vlastním řádku. **Příčina nedohledána** - kdo na to narazí, ať to
prosím dořeší a doplní sem.

