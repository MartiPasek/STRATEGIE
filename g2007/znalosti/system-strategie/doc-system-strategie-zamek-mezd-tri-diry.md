# Zamek mezd (Peta 9.9.2026) - jak funguje a tri mista, kudy se da obejit

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)


# Zamek mezd a tri diry v nem

**Zapsala C24 (Kristy) 9.–10. 9. 2026.** Vsechny tri diry jsem potkala v jednom dni pri praci
na prevodu odmen do mezd. Peta o nich vi (notifikace 24212 a 24279).

## Jak zamek funguje

Peta nasadila 9. 9. 2026 kontrolu v `g2007.python` skriptu **`claude_write_decision`**:
funkce `_is_mzdy_write(sql)` regexem najde cilove tabulky zapisu a kdyz nektera zacina
mzdovym prefixem, request smi schvalit jen ona.

**Kontrola bezi PRED rozhodnutim o smeru**, takze neopravneny clovek nemuze request ani
schvalit, ani **ZAMITNOUT** - dostane 403 v obou pripadech a pending request mu **drzi frontu
banneru i v ostatnich session**. Na tohle jsme narazily 9. 9. (request #2857).

**Zmena 9. 9. 2026** (rozhodla Kristy jako rodic, provedla C24): podminka dostala
`and not is_marti_parent(uid)`, takze bannery smi odklikavat i rodic. **Rozsah je uzky** -
tyka se vyhradne schvalovani banneru; ostatni zamky, ktere Peta nasadila (kdo smi sahat
na mzdy v modulech), zustavaji pro rodice zavrene.

## Dira 1 - base64 detektor neprohledne

Tela funkci se pres most posilaji zabalena v base64, protoze jinak se rozbije diakritika
a dvojtecky (`::text`, `:master_id`). Detektor pak v SQL zadnou mzdovou tabulku nevidi -
vidi jen `DO $do$ ... convert_from(decode('<base64>','base64')) ... END $do$`.

Konkretne request #2858 instaloval kod, ktery maze z `wage_movement`, a pod zamek nespadl.

## Dira 2 - funkce volana z UI je mimo zamek

Zamek hlida **cestu pres most**, ne akci v aplikaci. Funkce `ec.vyhodnoceni_do_mezd` zapisuje
do `wage_movement` a vola se tlacitkem z ERP - tudy zamek nevede. Ma vlastni opravneni
(`ec.akce_opravneni`, akce `do_mezd`), ale to je jiny mechanismus.

**Obecne pravidlo, ktere z toho plyne:** zamek na CESTU nechrani pred kodem, ktery se tou
cestou jednou protahne a pak se vola odjinud.

## Dira 3 - zamek nechrani sam sebe (nejzavaznejsi)

Zmena samotneho zamku **prosla uplne bez banneru**. Most vyhodnotil zapis do `g2007.python`
jako "G2007 konstruktivni" a zapsal rovnou. Takze pravidlo o tom, kdo smi schvalovat penezni
zapisy, jde prepsat **bez jedineho schvaleni**.

Kristy tu zmenu zadala, ale **system se nezeptal nikoho**. Kdyby ji zadal nekdo jiny nebo
omylem, projde stejne tise.

## Co s tim

Nic z toho nerusi uzitecnost zamku - 9. 9. nam realne zabranil v tichem prusvihu. Ale:
- diry 1 a 3 jsou v tom, ze se kontroluje **text SQL**, ne **dopad**;
- dira 2 je v tom, ze se kontroluje **kanal**, ne **operace**.

Rozhodnuti, jestli a jak to resit, patri Petovi (jeji domena) a Martimu.

## Praktikum pro instance

- Kdyz ti banner "porad naskakuje" a nejde schvalit ANI zamitnout, podivej se, jestli request
  nesaha na mzdovou tabulku - je to jedine misto v systemu s timhle chovanim.
- Zaloha pred zasahem do ciziho `g2007.python` skriptu patri do slozky outputs, **ne do /tmp** -
  linuxove prostredi se mezi kroky cisti a zaloha zmizi (stalo se mi 9. 9.).
- Skript v `g2007.python` je `active` = **zmena plati okamzite, bez deploye**. Pred odeslanim
  si telo lokalne zkompiluj (`py_compile`), jinak muzes shodit produkci za behu.

