# Přepočet denního souhrnu pro mzdy – zámek období a odstavené řádky

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Co se stalo (20. 8. 2026, C24 / Kristý)

Denní souhrn pro mzdy (`tenant.att_day_summary.cas_celkem`) přepisuje trigger
`att_entry_resummary` na `tenant.att_entry` → funkce `tenant._att_resummary_one`.
Ta měla dvě díry, obě nalezené při úklidu duplicit za červen 2026.

**1. Neměla filtr na `status`.** Sčítala i řádky označené `superseded`, tedy ty
vědomě odstavené (například staré `ec_real` a `ec_sumaden` z reimportu).

**2. Neznala zámek období.** `att_day_summary_recompute` má ruční FROZEN na
květen a červen 2026, ale tenhle trigger ho obcházel – nekoukal ani na
`tenant.att_period_lock`.

Důsledek – hodnota v mzdovém zrcadle **nebyla výsledkem vzorce, ale otiskem
posledního zápisu**. Jakýkoli dotek libovolného řádku `att_entry` v uzavřeném
měsíci ten den tiše přepočítal a přepsal. Změřený rozsah k 20. 8. 2026 –
kdyby vzorec přepočítal leden až červenec, **lišilo by se 7 262 dnů z 9 255**
(květen +4 697 h, červenec −2 202 h). Nevybuchlo to jen proto, že se
uzavřených měsíců nikdo nedotkl.

## Oprava

Ve `tenant._att_resummary_one` přibylo:

- `AND COALESCE(a.status,'') <> 'superseded'` v součtu hodin,
- na začátku `IF EXISTS (SELECT 1 FROM tenant.att_period_lock …) THEN RETURN`,
  tedy v zamčeném měsíci funkce nedělá vůbec nic.

Ověřeno chováním, ne jen čtením – ruční volání přepočtu na zamčený den
(Voříšek 12. 6.) nechalo hodnotu 8,42 beze změny.

Hlídá to pojistka **`dochazka-resummary-zamek-superseded`** v `tenant.pojistka`.

## Co z toho plyne pro další práci

- **Uzavřený měsíc se nikdy nemá hnout jako vedlejší efekt jiné operace.**
  Když je potřeba ho opravit, je to vědomý samostatný krok.
- Proto se po opravě **samy nesrovnají** dřívější chyby v uzavřených měsících.
  Příklad – Petra Šafránková ml. má 11., 12., 18. a 19. 6. 2026 zdvojený den
  (Centrála + naše píchnutí, například 16,07 h). Je OSVČ na paušálu, takže to
  nejsou peníze, ale číslo tam zůstane, dokud ho někdo vědomě nesrovná.

## Gotcha mostu (nález při ověřování)

**`SELECT nazev_funkce()` projde mostem jako čtení, i když funkce zapisuje.**
Schvalovací banner nevyskočí. Volání přepočtu přes SELECT proběhlo bez
schválení. V tomhle případě neškodné (funkce byla zamčená), ale je to díra
v tom, na co se banner spoléhá – zapsáno pro Péťu a Jirku.

