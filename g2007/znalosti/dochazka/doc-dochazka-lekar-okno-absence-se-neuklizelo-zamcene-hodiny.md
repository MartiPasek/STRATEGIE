# Lekar ve Sprave dochazky - okno se neuklidilo po sobe, casy z minula zamkly hodiny a Dopocitat se zacyklilo

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Lékař — okno „Nová absence" se neuklízelo po sobě, hodiny zůstaly zamčené

**Peťa + C26, 1. 9. 2026. Opraveno a ověřeno naostro.**

## Příznak

Ve Správě docházky nešlo u druhu **Lékař** zadat hodiny — pole bylo zamčené a drželo 8.
Tlačítko „Dopočítat z docházky" nešlo použít, protože chce hodiny napřed.

Peťa: *„lékař má fungovat a fungoval ještě předevčírem."* Měla pravdu — kód se nezměnil.

## Příčina

Okno „Nová absence" je v celé stránce **jedno jediné** a `absOpen()` po sobě neuklízel
**pole s časy** `abs_od_cas` / `abs_do_cas`. Čistil druh, data, hodiny, poznámku i důvod,
ale ne časy a ne hlášku od „Dopočítat".

Řetěz byl tenhle:

1. První použití po načtení stránky — pole prázdná, **všechno funguje**.
2. Uživatel zadá Lékaře, dá Dopočítat, vyplní se třeba 06.00–14.00, okno se zavře.
3. Druhé otevření — druh se resetuje na prázdno, ale **časy tam pořád jsou**.
4. `absCasyHodiny()` z nich spočítá 8 h a pole hodin **ZAMKNE** (`readOnly=true`),
   což je správné pravidlo Peti z 12. 8. 2026 („musí to sedět se sumou od–do").
5. „Dopočítat" ale odmítá běžet bez hodin. **Patová situace.**

Přepnutí druhu na Lékaře nepomůže — `absCasyToggle()` časy čistí jen při přepnutí
**Z** lékaře na jiný druh, ne při přepnutí **NA** lékaře.

Proto to vypadalo jako náhoda. Fungovalo to vždy napoprvé (Peťa to tak testovala
u Krónera) a přestalo napodruhé bez načtení stránky.

## Oprava

V `absOpen()` se **při každém otevření, v obou režimech**, vynulují `abs_od_cas`,
`abs_do_cas`, hláška `abs_dopocti_info`, odemkne se pole hodin a blok s časy se
zobrazí/schová podle vybraného druhu.

U režimu úpravy je to navíc **pojistka proti přenosu cizích časů** — dosud mohl na
záznam propadnout čas z předchozího záznamu, na kterém bylo okno otevřené předtím.

`g2007.soubor`, `apps/api/static_db/dochazka-po-zakazkach.html`, verze 55,
md5 `704e2d338036566163fb76c6edee4fbc`. Peťa ověřila naostro — jde to.

## ⚠️ Gotcha — dvě session psaly do téhož souboru během 9 vteřin

Verze 55 (tahle oprava, 12.23.28) a verze 56 (jiná session Peti, „odfajfkování bez
potvrzování", 12.23.37) šly za sebou **s odstupem devíti vteřin**. Nic se neztratilo,
ověřeno čtením — ve verzi 56 je obojí. Ale bylo to o vlásek.

**Poučení:** `@@G2007SOUBOR` nemá pojistku na otisk (na rozdíl od cíleného UPDATE
s `AND md5(obsah)=…`). Kdo píše do sdíleného souboru, ať:

- před zápisem přečte otisk a hned potom zapíše (co nejkratší okno),
- po zápisu **ověří čtením**, že jeho změna v ŽIVÉ verzi je — ne podle návratovky
  a ne podle verze, kterou zapsal (může být mezitím přepsaná),
- a hlásí se přes `@@WORK` / `@@WHO`, ať je vidět, kdo v čem dělá.

Peťa jede běžně tři okna naráz, takže tohle není výjimka, ale provozní stav.

Souvisí: [[doc-dochazka-absence-bez-casu-krome-lekare]]

