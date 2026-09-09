PŘEDÁNÍ — Peťa + Claude-26, práce z 28. 8. 2026, sepsáno 31. 8. ráno

HOTOVO

1. Tlačítko „V pořádku" ve frontě Oprav odbaví jedním kliknutím, bez výběru druhu chyby.
   Nabídka REASONS jsou druhy chyb a nález, který je v pořádku, žádný z nich není.
   Do historie se ukládá „zkontrolováno — v pořádku". Nová funkce `okUI()`.
2. V detailu dne jde odbavit i ČERVENÝ nález, ne jen modrý. Podmínka změněna z `_ainfo`
   na `!_aok && !_maNeodhl`. Skryté zůstává jen tehdy, když na dni visí neodhlášený záznam.
   Soubor `apps/api/static_db/dochazka-opravy.html` v69 (žije v `g2007.soubor`, ne v gitu).
3. Nová podmínka v kartě zaměstnance: „Bez docházky – nevede ji a nekontroluje se"
   (`tenant.staff_cond_def` kód `bez_dochazky`, sloupec `tenant.engagement.pod_bez_dochazky`,
   pořadí 140 = poslední). V HTML karty se neměnilo nic, tabulka se kreslí z číselníku.
   Nastaveno u: Pašek 2 a 41, Mózer 47, Vlková 361, Senft 374, Šík 349, Honomichl 9030.
   Marešová 21 (Týnka) záměrně BEZ příznaku — docházku reálně vede.
4. Příznak nahradil seznam devíti osobních čísel natvrdo. Byl na čtyřech místech
   v `att_anomaly_scan` a opsaný jen u tří pravidel z devíti; teď je to JEDNA globální
   výjimka u zápisu nálezu, platná pro všechna pravidla. Měřeno: ze 101 kandidátů
   patřilo 61 lidem, které nikdo nekontroluje.
5. Zastavena noční smyčka. `att_automat_level_day` v noci maže své doplňovací záznamy,
   `att_prazdny_den_fond` je zakládá znovu a ke KAŽDÉMU nový nález + zprávu na mobil.
   Dedup je na `entry_id`, které je každou noc nové → ručně odbavené nálezy se vracely.
   Od 13. 8.: Šík 67 nálezů, Pašek 50; 30 z nich někdo ručně zavřel a stejně se vrátily.
   Marti dostával i 16 zpráv na mobil denně. Opraveno, 26 starých nálezů zavřeno.
6. Přehled „Hlídání FPD (HPP)" přejmenován na **Nesplněný FPD** (jako v Centrále).
   Sloupce jako v Centrále 1088 bez ID + Druh smlouvy. Vzhled srovnán podle standardu
   (hlavně hlavička BEZ velkých písmen, což standard zakazuje a přehled to měl od začátku).
7. Nesplněný FPD — pravidla výběru: HPP i OSVČ (DPP ne), bez příznaku „Bez docházky",
   osobní číslo pod 9000 (nad = externí OSVČ programátoři), aktivní a smlouva neskončila,
   ne mateřská, schodek nad 0,5 h. Pracovní dny se počítají od nástupu do odchodu.
   Purkar (501, chybí mu celý srpen) se do přehledu konečně dostal — schovával ho filtr
   `(mzdove + absence) > 0`, který má Kristýna v Centrále od 6. 11. 2023 zakomentovaný.
8. Nezávislý přepočet ke včerejšku dal 10 lidí proti 10, shoda v devíti. Duspivová byla
   navíc (práh 0,1 místo dokumentovaných 0,5 — srovnáno), Michelle Šafránková byla navíc
   v mé kontrole (mateřská, přehled ji vyřazuje správně).
9. G2007: `doc-dochazka-priznak-bez-dochazky-v-podminkach`, `doc-dochazka-nocni-smycka-
   nalezu-a-zprav-prazdny-den`, `doc-dochazka-odbaveni-v-poradku-bez-vyberu-druhu-chyby`,
   `doc-system-strategie-podminky-vychozi-je-pohled-zapis-nejde-precist`,
   `doc-dochazka-hlidani-fpd-kdo-se-kontroluje-a-proc`. CLAUDE.md doplněna a pak opravena.

⚠️ CHYBA, KTERÁ SE TÝŽ DEN VRÁTILA — ČTI, NEŽ NA TO SÁHNEŠ

Příznak „Bez docházky" se odpoledne omylem zapojil i do MZDOVÉHO přepočtu
(`att_day_summary_recompute`) a týž den se to vrátilo. Peťa: „vždyť se tak i jmenuje,
nemá to ovlivňovat nic jiného." Šárka Novotná to zachytila nezávisle a dala důvod:
u hodinově placených se ty dvě věci rozejdou — DPP placená za skutečně odpracované
hodiny (typicky Herejtová) by s plným fondem dostala zaplaceno i za neodpracované.

DĚLICÍ ČÁRA: „nekontroluje se" je o dohledu, „plný fond" je o mzdovém výpočtu.
- kontrolní místa (`att_anomaly_scan`, `att_prazdny_den_fond`, `dochazka_kontrola_data`)
  čtou `pod_bez_dochazky`,
- mzdový přepočet čte a MUSÍ číst dál `engagement.plny_fond_bez_dochazky`. Ten sloupec
  NENÍ mrtvý, nemazat.
Srpen byl mezitím přepočítaný podle chybné verze a 31. 8. srovnán zpět: Honomichl
255,6 h, Šík 120,0 h, plný fond generuje 5 smluv. Přepočet je idempotentní.

OTEVŘENÉ

* Čeká odpověď JIRKY: ve STRATEGII jsou dva přehledy „Nesplněný FPD" a počítají jinak.
  Jeho (`menu_node` 197, `core` 209 `vyroba.dusan_nesplneny_fpd`, od 23. 7.) je soukromý
  jen pro Dušana (user 41), ukazuje jeho podřízené, „má být" bere z plánu a absenci
  NEpočítá jako odpracováno. Náš (206 / 218) bere fond z úvazku a absenci započítává.
  Nejsou duplikáty, mazat nemá smysl — ale Dušan je v obou seznamech, takže jediný uvidí
  dvě stejně pojmenované položky s různými čísly. Mail odeslán 28. 8.
* Čeká odpověď ŠÁRKY: doporučila rozdělit příznak na DVĚ zaškrtávátka — druhé, „plný fond
  bez docházky", by mzdový příznak přitáhlo do karty, aby byl vidět. Zatím neuděláno.
  Minimální varianta, kterou nabídla: pojistka, aby „plný fond" nikdy nechytil poměr
  placený od hodiny — jde postavit na sloupci `engagement.hodinovka`, ne na seznamu jmen.
  Šárka si taky ještě projde data, jestli příznak dneska nemá někdo hodinově placený.
* Čeká odpověď ŠÁRKY: neplacený přesčas nesedí u tří lidí — Kubín 9003, Mareš 9005,
  Siřiště 9037 mají v Centrále 0,50 h/den a ve STRATEGII 0. U ostatních prověřených to
  sedí. Na Nesplněný FPD to vliv nemá, je to podmínka ve smlouvě. Mail odeslán 28. 8.
* NEROZHODNUTO: mají Honomichl a Šík dostávat plný fond? Mzdový příznak nemají, takže
  dnes ne. Peťa 28. 8. říkala, že doplňování fondu je u nich špatně — jenže to je otázka
  na mzdový příznak, ne na to zaškrtávátko. Rozhodnutí patří Šárce a Týnce.
* NEPOLOŽENO: Mareš 9005, Svoboda 9017, Pillár 9103 nemají v Přehledu dnů za srpen
  jediný řádek — jsou to OSVČ, kteří nepíchají (Mareš nikdy, Svoboda naposled 16. 6.,
  Pillár 2. 7.). Příznak jim záměrně NEDÁN, protože by jim začal vznikat plný fond
  168 h měsíčně z ničeho. Otázka „mají být vedení jako aktivní s úvazkem 40?" se z mailu
  Týnce vyškrtla, ať se nezdržuje. Zůstává otevřená.
* Z předávky z 27. 8. pořád visí: migrace `set-zakazka` a `set-rezie` z `router.py` do
  `g2007.python` (dokud jsou na disku, nejde na ně napsat pojistka); denní připomínka
  fronty chodí VŠEM ve skupině DOCHÁZKA - OPRAVY bez ohledu na působnost; mobilní appka
  má přestat volit skupinu činností a žádat si `kind=prace`.
* Schvalovací banner nevyskakuje. 28. 8. třikrát: requesty 2593, 2598 a 2606 hlásily
  timeout po 120 s a přitom se PROVEDLY. Ověřuj ve `fw.claude_write_request` podle id
  a hlavně čtením dat.

GOTCHY (nové, ověřené naostro)

* `tenant.podminky_vychozi` NENÍ tabulka, ale POHLED nad širokou `tenant.podminky_skupin`.
  Zápis přes něj vrátí „OK, 1 řádek dotčen", `status=done`, `error=NULL` — a řádek
  v databázi NENÍ. Sourozenec pasti, kterou G2007 popisuje u `staff_cond`. Poznáš to tak,
  že `information_schema.columns ... is_nullable='NO'` vrátí u pohledu nula řádků.
* `updated_by_text` v `g2007.soubor` se u některých cest zápisu NEAKTUALIZUJE. Posledních
  12 verzí `dochazka-opravy.html` včetně Jirkových neslo staré jméno. Podle toho pole
  NEPOZNÁŠ, kdo psal naposledy — ověřuj jinak (`@@WHO`, heartbeat, verze).
* Spouštěč na `g2007.python` zvedá `verze`, ale NESAHÁ na `updated_at`. Staré datum změny
  tedy neznamená, že se zápis neprovedl. Ověřuj přes `g2007.python_historie` (archivní
  řádek staré verze) nebo přes md5.
* `@@G2007SOUBOR` přidává koncové zalomení řádku, když chybí. Otisk se pak liší o jeden
  znak, obsah je jinak bajt po bajtu shodný. Počítej s tím při kontrole md5.
* Lane si neurči podle časů souborů — `@@WHO` ukáže i ZÁMKY. 28. 8. držel lane 1 druhé
  okno Claude-28, přestože jeho heartbeat hlásil lane 3.
* Bezpečný zápis do cizího souboru: přečti obsah jako base64, ověř md5, uprav lokálně,
  odešli přes `@@G2007SOUBOR` a znovu ověř md5. Bez toho hrozí přepsání cizí práce.
* Velký soubor nikdy nesestavuj v odpovědi — stáhni ho z mostu do souboru, uprav skriptem
  v bash a odešli. Do kontextu se nemusí dostat vůbec.
