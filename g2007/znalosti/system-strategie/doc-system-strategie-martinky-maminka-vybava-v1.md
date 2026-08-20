# Maminka v1: schvalena potreba -> Maminka upravi VYBAVU domeny -> ukol se sam dokonci (NASAZENO+OVERENO 3.8.2026 v noci)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Princip (Marti 2.8. vecer: "abych Mamince odsouhlasil potrebu nastroje pro danou Martinku a ta aby upravila patricne prompt")

Kdyz Martinka ohlasi potrebu typu chybi_nastroje/chybi_data, clovek ji v Agent Inboxu tlacitkem "Predat Mamince" SCHVALI (+ volitelny pokyn). Skript maminka_vybav pak spusti agentni beh MAMINKY (run_goal s maminka-identitou), ktera napise DOPLNEK VYBAVY domeny - obecne pouzitelny navod/pravidlo, ne jen fix jednoho ukolu. Doplnek se appenduje do g2007.tool_domain.vybava_prompt (novy sloupec, DDL #1662 + vybava_upraveno_at/vybava_upravil), potreba -> splnena, ukol -> zpet 'zadan' + event dispatch. Dispatcher v2 pri KAZDEM behu Martinky injektuje vybavu domeny do goal ("VYBAVA DOMENY od Maminky - zavazne navody a pravidla").

## Efekty ven - zavazne pravidlo v dispatch v2

Kazda Martinka ma v goal natvrdo: e-mail/SMS/platby/zapisy do cizich systemu NIKDY neprovadi sama - pripravi kompletni NAVRH do vysledku a oznaci [EFEKT_VEN: email]; odeslani schvali a provede clovek. Stejne pravidlo je zavazne i pro Maminku pri psani vybavy (bod 1 jejiho promptu). Konzistentni s doktrinou Eliska-pilot (navrh->schvaleni, nikdy sam neodeslat).

## Skripty a artefakty
- maminka_vybav(uid, potreba_id, pokyn) v1 (md5 0688e29d...): vraci {vyreseno, doplnek, znovu_ve_fronte} nebo {vyreseno:false, nejde} kdyz to vybavou nejde ([STAV: NEJDE co=...] - napr. potreba noveho kodu).
- martinka_dispatch v2 (md5 8c487b68...): JOIN tool_domain, vybava blok + pravidlo efektu ven + typ chybi_nastroje v POTREBA formatu; chybi_nastroje/chyba_nastroje -> stav ceka_na_cloveka (inbox).
- UI v2 (g2007.soubor verze 2): tlacitko "Predat Mamince" u kazde potreby (dialog s pokynem).

## OVERENO E2E (3.8.2026 00:30-00:35, ukol #5)
Ukol "cena po sleve VIP ZLATO" (pravidlo zamerne nikde v DB): Martinka spravne NEvymyslela, ohlasila chybi_data "interni slevove pravidlo VIP ZLATO - potrebuji od Maminky" -> Predat Mamince s pokynem (12 % bez DPH, floor, nekombinovat) -> Maminka za 27 s napsala strukturovane pravidlo vc. prikladu do vybavy domeny nabidky -> ukol sam re-run -> Martinka pravidlo pouzila: 10 000 - 1 200 = 8 800 Kc bez DPH -> ke_schvaleni. NAVIC overeno u ukolu #4: Martinka s rucemi (cil_ruce_enabled) si firemni sablonu nabidky NASLA SAMA v systemu (EC_CZ_nabidka_VR_V2_JV_240212.doc) a e-mail pripravila jen jako [EFEKT_VEN: email] navrh - samoobsluha funguje, Maminka je pro to, co v systemu neni.

## Gotchy/pozn.
1. Vybava se appenduje bez limitu - casem hlidat velikost (goal orezava na poslednich 4000 znaku vybavy), pri rustu zavest kompakci (Maminka sama zkonsoliduje).
2. Maminka bezi pod stejnym run_goal (rozpocty/kill switch plati); jeji identita je zatim jen goal-prompt, ne persona - pozdeji zvazit vlastni inkarnaci dle org-struktura-md1-md5.
3. tool_domain.vybava_prompt meni skript v app procesu (zadny bridge banner) - gate je lidsky klik "Predat Mamince" v UI. DELETE/ALTER dal jen pres banner.

