# Vyhodnoceni zakazek - do ktere firmy odmena patri (pravidlo overene 8.9.2026)

> oblast: `vyroba` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Do ktere firmy odmena patri

**Zapsala C24 (Kristy) 8. 9. 2026.** Vse nize je overene ctenim z produkcni DB, ne odhad.
Navazuje na doktrinu #24 (jeden clovek = vic pracovnich zaznamu) a na
[[doc-vyroba-vyhodnoceni-penize-z-nasich-tabulek]].

## Otazka

`tenant.wage_movement.engagement_id` je pracovni POMER, ne clovek. Odmena z vyhodnoceni
zakazky musi spadnout do spravne firmy. Import z Centraly firmu zna, protoze ji nese zdroj.
Nase cesta ji zna take - jen se na to musi spravne zeptat.

## Retez (plati)

`ec.zakazky_finance_zam.cislo_zam` -> `tenant.att_employee.cislo_zam` -> karta ->
`tenant.engagement.employee_id` -> engagement platny k datu -> `company_id` a `engagement.id`.

Firmu nese **`tenant.engagement.company_id`**. Firmy jsou dve - 1 a 2.
Ani `att_employee`, ani `zakazky_finance_zam` zadny sloupec s firmou nemaji.

## Pravidlo vyberu pomeru

Engagement s nejnovejsim `valid_from` mensim nebo rovnym datu,
`ORDER BY valid_from DESC, is_current DESC, id DESC LIMIT 1`.
Je to **totez pravidlo, jake uz v produkci pouziva trigger `att_entry_fill_firma_user`** -
nezavadi se nova cesta, pouziva se existujici vzor.

## Overeni (rozhodujici test)

Na 47 radcich `wage_movement` za 7/2026 (typ 67, `import_src='EC_PRIPL'`), ktere pritekly
z Centraly, dalo pravidlo **47 ze 47 shodu - vcetne konkretniho `engagement_id`**, ne jen firmy.
Rozpad sedi na firma 1 = 9 radku / 2 990 Kc a firma 2 = 38 radku / 8 880 Kc.
**20 ze 47 radku patri lidem, kteri maji engagementy ve dvou firmach**, takze diskriminujici
pripady jsou v testu obsazene - neni to shoda nahod.

## Parovani je jednoznacne

Karet s ciselnym `cislo_zam` je 236, z toho **zadne cislo neni pouzite na vic kartach**
a **zadny radek `zakazky_finance_zam` se nenapari na vic nez jednu kartu**.
2 592 z 23 479 historickych radku se nenapari na zadnou kartu (stari lide) - do mezd ale
nejdou, historie je uzamcena.

## Na co si dat pozor

- **`valid_to` je NULL u vsech verzi `engagement`.** Platnost stoji VYHRADNE na `valid_from`,
  takze chybna nebo prekryvajici se verze by tise vyhrala. Test na prekryv obdobi proto
  nic nedokazuje - degeneruje, protoze vsechno prekryva vsechno.
- **41 karet ma engagementy ve dvou firmach**, ale lidi s vic nez jednim AKTIVNIM pomerem
  (`is_current`) je **nula**. Dve firmy maji tedy za sebou v case, ne soubezne.
- **Dusledek pro koeficient superhrube**: blok `g_typ` v `ec.vyhodnoceni_uzavrit` urcuje
  `engagement_type = 'hpp'` pres `is_current` s `LIMIT 1`. Dnes to nekouse prave proto, ze
  soubezne aktivni pomery nikdo nema. Jakmile nekdo druhy soubezny pomer dostane, stane se
  z koeficientu 1,4 los - a to je rozdil 40 % na vyplacene castce.
  **Zajisteno je to daty, ne konstrukci.**

