# describe_image

## MAPA
- **kód:** `describe_image`
- **kategorie:** běžné (CORE)
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Faze 12a multimedia: popis OBRAZKU (kind='image'), ktery user nahral. KRITICKE: Pouzij JEN pro IMAGE media. NEVOLEJ na AUDIO -- pro audio dostavas Whisper transcript automaticky v multimodal contextu, zadny tool nepotrebujes; pokud transcript jeste neni hotov, pockej a uzivateli rekni ze prepis dorazi za par sekund.

Pouzij kdyz user prilozil OBRAZEK a pta se 'co je na tom?', 'popis to', 'co vidis?', nebo kdyz potrebujes vlastni kontext k obrazku pro dalsi praci. Sonnet 4.6 podporuje vize nativne -- tool ti obrazek nacte z FS a posle zpet detailni popis. Vysledek se ulozi do media_files.description (alt text) -- priste uz nemusis volat znovu.

## PARAMETRY

- **`focus`** [string, volitelný]
  - Volitelne -- co konkretne user chce vedet? 'popis sceny', 'cti text', 'rozpoznej objekty', 'popis lidi', atd. Bez focus = obecny popis.
- **`media_id`** [integer, POVINNÝ]
  - ID media souboru (z media_files). User obvykle dava jako 'obrazek #5' nebo se vyber automaticky z attached media v aktualni zprave.

