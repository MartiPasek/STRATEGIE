# Podmínky - úplný seznam zapisovatelů do engagement.pod_* a past pohledu staff_cond

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

**Claude-24 (Kristý), 20. 8. 2026. Vzniklo z obavy Šárky Novotné, že se jí ruční nastavení podmínek přepisuje zpět na výchozí hodnoty. Obava se NEPOTVRDILA, ale při dohledávání vypadly dvě věci, které stojí za zapsání.**

## Odpověď na otázku „přepíše mi něco ruční hodnotu?"

**Žádný import ani sync z Centrály se podmínek nedotýká.** Prověřeno vyčerpávajícím způsobem: `pg_trigger` na engagement / att_employee / podminky_vychozi / staff_group_member / staff_cond, všechny funkce v `pg_proc` (schémata tenant, public, g2007, fw) obsahující `pod_*`, všech 43 skriptů v `g2007.python` dotýkajících se těch tabulek, a grep na disku (`*.py`, `*.js`) — na disku **nula** zápisů.

Do `tenant.engagement.pod_*` zapisuje přesně **osm** cest *(sedm k 20. 8. 2026; osmá přibyla 24. 8. — viz poznámka pod tabulkou)*:

| Kdo | Kdy | Přepíše ruční hodnotu? |
|---|---|---|
| `g2007.python / hr_conditions_save` | ruční zápis z karty | to je sama personální |
| `tenant.staff_cond_view_write` | zápis přes pohled `staff_cond` | nic ho dnes nevolá |
| `tenant.engagement_pod_defaults` | BEFORE INSERT na engagement | **ne** — jen `COALESCE` do prázdných polí |
| `tenant.engagement_doplneni_pri_zarazeni` | AFTER INSERT na staff_group_member | **ne** — jen položky s příznakem `ceka_na_zarazeni` |
| `engagement_pod_soucet_dovolene` + `staff_cond_prepocet_dovolene` | při změně dovolené | ano, ale správně — `dovolena_dni` je počítadlo |
| **`g2007.python / att_vernost_dovolena`** | **1×/den po 7:00** | **mění** — viz níže |
| `g2007.python / uvazek_zapis` | změna úvazku | **ne** — novou verzi smlouvy nechá složit společným jádrem jako kopii všech sloupců podle `information_schema` |
| **`g2007.python / smlouva_nova_verze`** | **ruční tlačítko „Nová verze smlouvy" v kartě** | **ne** — tatáž kopie přes totéž jádro *(nové 24. 8. 2026)* |

> **Doplněno 24. 8. 2026 (Claude-28 / Jirka Honomichl, schválila Marti-AI msg 13561).**
> Kopírování celého řádku se z `uvazek_zapis` přestěhovalo do nového společného jádra
> **`engagement_nova_verze`**, které volají obě cesty zakládající novou verzi (změna úvazku
> i nové ruční tlačítko). **Na chování téhle tabulky to nic nemění** — kopie se pořád skládá
> ze všech sloupců podle `information_schema`, takže ruční hodnoty se nepřepíšou; ověřeno
> naostro porovnáním všech 49 sloupců, všech 16 podmínek se opsalo beze změny.
> Detail: [[doc-dochazka-smlouva-nova-verze-rucne]].

## Past č. 1 — věrnostní automat a PRÁZDNÁ hodnota

`att_vernost_dovolena` (denní smyčka, delegate `_hr_vernost_dovolena` v router.py ř. 13622 a 13955) přičítá při výročí 10/20/30 let **+1 den** k `pod_dovolena_navic_dni`. Nepřepisuje na výchozí hodnotu, přičítá k té, co tam je, a jednou za výročí (pojistka `tenant.vernost_dovolena_log`, `UNIQUE (tenant_id, user_id, roky_ve_firme)`).

**Ale když je `pod_dovolena_navic_dni` NULL, vezme si jako základ systémovou hodnotu (dnes 5) a zapíše 6.** Kdyby tam byla `0`, zapíše `1`.

→ **Při jakémkoli nulování podmínek psát `0`, nikdy nenechávat prázdno.** Dnes to nehrozí (prázdnou dovolenou navíc nemá nikdo), ožilo by to při hromadném vyprázdnění — což je přesně varianta, o které personální uvažuje pro OSVČ.

Tentýž skript se v komentáři na ř. 161–163 odkazuje na spouštěč `trg_staff_cond_default_dovolena`, který byl **20. 8. 2026 vědomě zrušen** (požadavek 2267, viz [[doc-dochazka-vychozi-podminky-spoustec-a-pevne-defaulty]]). Fallback větev, kterou komentář popisuje jako „nemělo by nastat", je tím pádem jediná pojistka — a sahá pro systémovou hodnotu. Při dalším zásahu do skriptu opravit.

## Past č. 2 — pohled `tenant.staff_cond` zapíše víc, než umí přečíst

- **Zápis** přes INSTEAD OF spouštěč: úroveň `user` → `engagement.pod_*`, úrovně `system`/`group` → `tenant.podminky_vychozi`.
- **Čtení**: `pg_get_viewdef` ukazuje jediný `SELECT` nad `tenant.engagement` — pohled **úroveň system ani group vůbec nevrací**.

Ověřeno: pohled vrací 1 115 řádků, z toho **0 systémových a 0 skupinových**, přitom v `podminky_vychozi` jich je 25.

Kdo přes pohled uloží skupinovou výchozí hodnotu, **zpátky ji neuvidí** — přesně dojem „nastavení se ztratilo". Živý kód pohled naštěstí nepoužívá (`hr_conditions`, `hr_conditions_people`, `hr_podminky_prehled`, `my_conditions` čtou přímo z `engagement` a `podminky_vychozi`; v `g2007.python` zbyly jen zmínky v komentářích). Je to tedy past pro budoucí kód a reporty, ne aktivní chyba.

**Doporučení:** buď pohled dorovnat `UNION`em s `podminky_vychozi`, nebo ho přejmenovat na `staff_cond_legacy`, ať je z názvu vidět, že to není zdroj pravdy.

## Navrhovaná pojistka do budoucna

Dnes se ruční hodnota pozná jen **nepřítomností** příznaku `ceka_na_zarazeni` v `pod_meta` — pojistka mlčením. Návrh: `hr_conditions_save` bude při zápisu z karty ukládat i `rucne: true`, a obě automatiky dostanou tvrdou podmínku „na klíč s `rucne=true` nesahej". Jeden řádek v zápisu, jedna podmínka v každé automatice. Neprojednáno, čeká na rozhodnutí.

Souvisí: [[doc-dochazka-vernostni-den-dovolene-za-odslouzena-leta]], [[doc-dochazka-podminky-slouceny-se-smlouvou]], [[doc-dochazka-podminky-vyber-skupiny-je-textove-min]].

