# Vyhodnoceni zakazek: tlacitka Sefmonter a Hodnotit spolecne (body 4+5, hotovo 6.8.2026)

> oblast: `vyroba` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Tlacitka Sefmonter a Slucovani zakazek

**Hotovo, nasazeno a overeno 6. 8. 2026** (C28/Jirka), commit `5624fd03`.
Posledni dva body ze sestice doladeni. Backend obou uz existoval a byl overeny,
chybelo **jen ovladani**.

## Kde a proc prave tam

Pridano do `apps/api/static/erp/components/ec_vyhodnoceni_actions.js` — do akcni listy
**v jadre** zakazky, za oddelovac. Tri nova tlacitka:

| tlacitko | co dela |
|---|---|
| 👷 **Sefmonter…** | nabidne lidi z teto zakazky a nastavi/odznaci vybraneho |
| 🔗 **Hodnotit spolecne…** | slouci tuto zakazku s dalsimi zadanymi |
| ✂️ **Zrusit slouceni** | vyclenit tuto zakazku ze skupiny |

**Puvodni zadani znelo "hromadny vyber radku na prehledu".** Prehled je ale grid,
ne `DesignFwForm`, takze se na nej tenhle soubor nevesi. Slucovani z jadra ma navic
prirozeny smysl: divam se na zakazku a rikam, ktere dalsi se k ni maji pripojit.
Kdyby to melo byt na prehledu s multi-selectem, je to samostatna prace na jinem miste.

## Proc zadani cisel a ne seznam

Zakazek je pres **5 600** - seznam k vyberu by byl nepouzitelny. Uzivatel proto napise
cisla dalsich zakazek; aktualni se pripoji automaticky. Backend si skupinu poresi sam.

## Sefmonter cte lidi ze STEJNEHO zdroje jako grid

`GET /api/v1/erp/data/ec.vyhodnoceni_jadro_osoba?master_id=<id>&kind=select-detail` -
seznam ve vyberu tedy vzdy odpovida tomu, co uzivatel vidi v gridu "Hodnoceni vse".

## Overeno naostro

- zdroj dat vraci spravne lidi vc. priznaku sefmontera a jejich ID
- `nastav_sefmontera` naostro na VR10704: vypnuti (Pechoucek -> nikdo) i zpetne
  zapnuti (-> Pechoucek) probehlo spravne, stav vracen do puvodniho
- vsechny tri `action_code` (`nastav_sefmontera`, `slouci`, `slouci_zrus`) overeny
  proti whitelistu v `vyhodnoceni_actions.py`

## POZOR: sefmonter se PREPINA, neprepisuje

`ec.nastav_sefmontera` dela `sefmonter = NOT sefmonter` u zadaneho radku a **ostatni
neodznaci**. Kdyz nekdo oznaci druheho cloveka, mohou vzniknout DVA sefmonteri a do
`zakazka_meta` se pak zapise jeden z nich nedeterministicky. Je to puvodni chovani
Centraly (1:1 port), ne novy problem - ale stoji za zvazeni, jestli to nema vybirat
jednoho. Proto je v okne napsano "Dalsim kliknutim na tehoz ho zase odznacis".

## Poznamka k pravidlu "kod jako data"

Soubor zustava v gitu. Kristyna Ksirova 6. 8. potvrdila, ze **ERP komponenty nejsou
v pasti dvou zdroju pravdy** - jsou jen v gitu, v `g2007.soubor` zadna neni, takze
editace v gitu je bezpecna a nikoho neblokuje. Skupinova migrace vsech ~45 komponent
je samostatne kategorialni rozhodnuti pro Martiho (viz
`doc-system-strategie-erp-komponenty-migrace-neni-stejny-vzor`).

