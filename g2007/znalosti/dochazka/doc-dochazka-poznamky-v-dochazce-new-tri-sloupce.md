# Poznámky v Docházce new: tři sloupce podle toho, kdo je psal (Peťa 7. 9. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)


# Poznámky v Docházce new — tři sloupce podle pisatele

**Rozhodla Peťa 7. 9. 2026.** Vzniklo z otázky „proč nevidím poznámku o převodu přesčasů".

## Co se změnilo

V přehledu „Docházka new" byly dřív dvě kolonky: `Poznamka` (míchanice) a `VedPoznamka`
(prázdná ve všech 19 376 záznamech — nikdy ji nikdo nevyplnil, není totiž kam).
Nově jsou tři, dělené podle toho, KDO text napsal — stejně jako to má Centrála
(`ZamPoznamka` / `VedPoznamka` / `Poznamka`):

| sloupec | co v něm je | odkud |
|---|---|---|
| **ZamPoznamka** | co napsal člověk z mobilu | text za značkou `✋ ROZPOR:` v `att_entry.note` |
| **VedPoznamka** | co udělal opravář — opravy, storna, doplnění | skutečné pole `vedouci_poznamka`, a když je prázdné, úseky s `🛠` z `note` |
| **Poznamka** | zbytek od automatu | `auto-odhlášení o půlnoci`, `nahrazeno opravou #…`, `krátká pauza` |

Vše **jen ke čtení.** Poznámky se mění v Opravách — Peťa 7. 9.: *„většinou vznikne
při opravě, a tedy v Opravách."* Drží to linii rozhodnutí z 31. 8. (zakládat a rušit
docházku jen v Opravách), viz doc-dochazka-dochazka-new-zakladani-a-mazani-jen-v-opravach.

## HLAVNÍ NÁLEZ: poznámka o opravě nebyla v přehledu vidět NIKDY

Ne kvůli pořadí sloupců — kvůli patru. Editor píše poznámku při opravě na **hlavičku**
(`att_entry.note`), ale Docházka new u dnů s rozpadem ukazuje **řádek rozpadu**
(`vyroba_work`), a tam je kolonka `poznamka` prázdná. Hlavičku přehled schválně vynechává,
aby se hodiny nepočítaly dvakrát. Text tak visel o patro výš a přes tuhle obrazovku
se k němu nikdo nedostal.

Doloženo: Urbanová 1. 8. 2026, zakázka VR10698 — `vyroba_work.poznamka` prázdná,
`att_entry.note` = „🛠 OPRAVA (Dušan Havlát): 9h z 31/7 (původně Práce 06:00–09:00)".
Šlo o převod 9 přesčasových hodin z 31. 7., který Dušan dělal ručně.

**Oprava:** větev W datasetu `dochazka.zakazky_vse_list` (id 177) dostala
`LEFT JOIN tenant.att_entry ae ON ae.id=w.att_entry_id` a poznámka se bere jako
`COALESCE(NULLIF(btrim(w.poznamka),''), ae.note, '')`. Vazba `att_entry_id` existovala,
jen ji ta kolonka nepoužívala. Nic se nepřepisuje, jen se doplnilo, odkud číst.

## Známé slabiny — vědět o nich, než se objeví za rok

1. **ZamPoznamka stojí na značce `✋ ROZPOR:`, kterou píše mobilní appka.**
   Kdyby někdo tu značku změnil, sloupec **beze slova zmlkne**. Je to přesně ten vzorec
   jako u němých hlídačů (doc-dochazka-neodhlaseni-pulnocni-uzavreni-rozpadu). Pořádné
   řešení je vlastní pole v databázi místo značky v textu — zatím na to není důvod.
2. **VedPoznamka ukazuje text, který vedoucí nenapsal.** Úseky s `🛠` generuje opravárenský
   engine při změně záznamu; nesou jméno editora a co udělal. Sedí tam významem, ne původem.
   Skutečné pole `vedouci_poznamka` má přednost, kdyby ho někdo začal plnit.
3. **Když si člověk do rozporu napíše lomítko**, věta se dělí podle ` / ` a kus se objeví
   i v systémové poznámce. Radši duplicita než uříznutá věta.

## Kde to žije

- dataset `fw.data_set` id **177**, kód `dochazka.zakazky_vse_list`
- stránka `g2007.soubor` kód `apps/api/static_db/dochazka-po-zakazkach.html`, pole `COLS_DEF`
- endpoint `/app/dochazka-zak-tab/data` posílá **všechny** sloupce datasetu bez seznamu
  povolených → nový sloupec projde sám. Dataset se čte při každém požadavku, žádný restart.

## Souvisí

- doc-dochazka-dochazka-new-zakladani-a-mazani-jen-v-opravach
- doc-dochazka-anomaly-ciselnik-druhu-chyb-chybi
- doc-dochazka-att-entry-vyroba-work-kaskada

