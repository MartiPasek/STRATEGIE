# Integrovaný tok: e-mail → poptávka → kalkulace → nabídka (implementační plán)

> oblast: `system-strategie` · úroveň:  · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Integrovaný tok poptávky → kalkulace → nabídka (C23, 31.7.2026)

Zadání Martiho (30.7.): vzít doménu poptávek/kalkulací/nabídek šířeji naráz, protože se přirozeně propojují — včetně hlídání a analýzy příchozích e-mailů a tvorby nabídek podle standardu. Tento dokument shrnuje co už NAOSTRO ŽIJE (ověřeno 31.7. přímo v DB/kódu) a navrhuje, jak to propojit.

## 1. Co už žije (ověřeno 31.7., ne z paměti — přímo dotazem)

- **`@@PP` engine** (`modules/erp/api/prijata_poptavka.py`, dispatch `modules/erp/api/router.py:44711`) — TEST paralelní engine nad přijatými poptávkami (DB_EC řada 900). GEN/FILL/SHOW/REPLY(koncept)/KALK/MSG/DIR/COPYDOCS/SMAZ. Naostro odzkoušeno: EP26309 → EN263470 + EK263470 (ponecháno jako učební artefakt). Vše prefixem TEST, e-maily jen koncepty — bezpečné.
- **Kalkulační engine** (`modules/erp/api/kalkulace_engine.py`): `@@KALKSYNC/@@KALKINFO/@@KALKCALC/@@KALKSTD` (obecný), `@@KALKABSV1` (zákaznický ABSAUGWERK, validováno na 0,8 %), `@@KALKPRICE` (cena dílu z poslední nákupky+ceníku). Doktrína: finální cenu/marži validuje ELIŠKA, ne AI.
- **`@@VYPOPT`** (vydané poptávky dodavatelům, řada 940) — 798 přijatých nabídek dodavatelů v `tenant.vypopt_nabidka`. Zatím NENÍ zapojeno jako zdroj do `@@KALKPRICE` (další krok, už dřív identifikováno, dosud neuděláno).
- **E-mailový mirror** (`tenant.mail_message`, `modules/erp/api/mail_mirror.py`): pro Elišku (user 34) ŽIVÝ a ČERSTVÝ — poslední mail 30.7. 16:44, sync 30.7. 22:35. (Poznámka: starší paměťový zápis "zamrzlé od 5.7." je ZASTARALÝ, mezitím to někdo opravil/běží dál — dobrá zpráva, není to blocker.)
- **`tenant.vp_poptavka`** — tabulka EXISTUJE, má přesně schéma pro AI triage e-mailů do poptávek: `source_email_id`, `smer`, `jistota` (confidence skóre), `shrnuti` (AI summary), `prideleno_user_id/by/at` (audit přiřazení), `zakazka_ref`. **0 řádků — schéma je připravené, ale nikdy nebyl napsán kód, který by ji plnil.** Toto je přesně "Fáze 2 (governance Marti-AI): AI triáž, poptávky→VP" zmíněná dřív jako nepostavená.
- **`tenant.poptavka`** — jednodušší obecná tabulka (cislo/zakaznik/typ/stav/resitel_user_id/zdroj), taky 0 řádků. Zdvojení s `vp_poptavka` — nutno rozhodnout, která je kanonická (viz otevřené otázky).
- **`g2007.eskalace_log`** — potvrzeno: STÁLE NEEXISTUJE. Chybí durable audit trail eskalací automatů/Haiku.
- **Doménová architektura Martinek** (g2007.tool_domain/domain_nastroj, g2007.automat, permission_tier) — HOTOVO a nasazeno (viz `doc-system-strategie-domeny-automaty-implementace-plan`), zatím inertní (0 konverzací s active_domain), čeká na první doménový automat.

## 2. Navržený integrovaný tok

```
[příchozí e-mail, tenant.mail_message]
        ↓  (nový: automat/Haiku triage — L0/L1 z eskalačního žebříčku)
[AI klasifikace: je to poptávka? jaká jistota? → tenant.vp_poptavka]
        ↓  jistota vysoká + jasný zákazník/díl
[návrh: @@PP GEN → přijatá poptávka EP… v Centrále]
        ↓
[kalkulace: @@KALKPRICE / @@KALKABSV1 (+ @@VYPOPT jako 4. cenový zdroj — dodělat hook)]
        ↓
[nabídka podle standardu (šablona EN262940-styl) — návrh, TEST prefix, koncept]
        ↓
[Eliška: kontrola + finální cena/marže (její doména, ne AI) → schválení → odeslání]
```

Toto je zároveň PRVNÍ přirozený "doménový automat" pro doménu `poptavky` (Pilíř B z architektury Martinek) — status_block by hlásil: kolik nových e-mailů čeká na triage, kolik poptávek čeká na kalkulaci, kolik nabídek čeká na Eliščino schválení.

## 3. Kroky (v pořadí, žádný nekóduje bez schválení Martiho)

1. **Rozhodnout `vp_poptavka` vs `poptavka`** (otevřená otázka Martimu — navrhuji `vp_poptavka`, má bohatší schéma přesně pro AI triage).
2. **Napsat AI triage krok** (Haiku, L1 eskalačního žebříčku): čte nové řádky `tenant.mail_message` (WHERE slozka='dorucene' AND created_at > last_run), klasifikuje poptávka/ne-poptávka + jistota + shrnutí → INSERT do `vp_poptavka`. Nízká jistota → nechá nepřiřazené, čeká na člověka (Eliška/Regele).
3. **Propojit vysokou jistotu → `@@PP GEN`** (návrh, ne auto-send) — vytvoří TEST poptávku v Centrále, přiřadí `zakazka_ref` zpět do `vp_poptavka`.
4. **Dodělat `@@VYPOPT` jako 4. cenový zdroj** do `@@KALKPRICE` (bylo už dřív navrženo, teď to zapadá do celého toku).
5. **Šablona nabídky podle standardu** — najít/potvrdit u Martiho, kde žije aktuální EN262940-styl šablona (Word/Centrála/jinde), a napojit `@@PP REPLY`/nabídkový krok na ni.
6. **`g2007.eskalace_log`** — postavit před/souběžně s krokem 2, protože AI triage bude první reálný provoz Haiku eskalací s dopadem na byznys (chybná klasifikace = ztracená poptávka).
7. **První doménový automat `poptavky`** v `g2007.automat` (rozšíření o `domain_kod`/`status_block`, Step 4 z `doc-system-strategie-domeny-automaty-implementace-plan`) — zastřeší kroky 2-3 jako pravidelný běh + status_block do promptu.

## 4. Otevřené otázky pro Martiho

- `vp_poptavka` vs `poptavka` — sloučit/zvolit kanonickou?
- Šablona nabídky "podle standardu" — kde přesně žije aktuální vzor (EN262940 zmíněné dřív)?
- AI triage e-mailů: má být čistě návrh čekající na Elišku/Regele, nebo smí `@@PP GEN` spouštět sama (v TEST režimu) bez potvrzení člověka? (Doktrína dosud: AI navrhuje, člověk potvrzuje — navrhuji tohle zachovat i tady.)

Navazuje na: `doc-system-strategie-domeny-automaty-implementace-plan` (#281), `doc-go-prijate_poptavky`, `doc-go-vydane_poptavky_rfq`.


